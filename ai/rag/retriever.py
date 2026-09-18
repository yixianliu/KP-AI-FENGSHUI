# -*- coding: utf-8 -*-
"""
ai/rag/retriever.py — BM25 + 向量混合检索器

检索策略：
  1. BM25 关键词检索（轻量、快速）
  2. 向量相似度检索（语义匹配，可选）
  3. 重排序：BM25 得分 * 0.4 + 向量得分 * 0.6

依赖：
  - rank-bm25：BM25 实现（必选）
  - sentence-transformers + chromadb：向量检索（可选，首次使用需下载嵌入模型）

设计说明：
  嵌入函数采用「懒加载」策略：
    - __init__ 阶段不实际下载模型（避免首次启动卡顿 / 离线报错）
    - 调用 embed 前检查 HF 缓存；无缓存则自动降级为纯 BM25 模式
"""
from __future__ import annotations

import json
import logging
import math
import os
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.utils import embedding_functions
    _HAS_CHROMA = True
except ImportError:
    _HAS_CHROMA = False
    chromadb = None
    embedding_functions = None

try:
    from rank_bm25 import BM25Okapi
    _HAS_BM25 = True
except ImportError:
    _HAS_BM25 = False

#: 嵌入模型名称（bge-small-zh 体积小，约 100MB）
_EMBEDDING_MODEL = "BAAI/bge-small-zh"

# 中文分词（简单按字切分，避免依赖 jieba）
def _tokenize_zh(text: str) -> list[str]:
    """中文字符级分词"""
    return list(text)


def _hf_model_cached(model_name: str) -> bool:
    """检查 HuggingFace 模型是否已在本地缓存中（避免触发网络下载）。

    检查顺序：
      1. 用户自定义缓存目录（HF_HOME / HUGGINGFACE_HUB_CACHE）
      2. 默认缓存目录 ~/.cache/huggingface/hub

    命中标准：缓存目录中存在 models--<org>--<name> 子目录。
    """
    safe_name = model_name.replace('/', '--')
    candidates = []
    for env_var in ('HF_HOME', 'HUGGINGFACE_HUB_CACHE'):
        val = os.environ.get(env_var)
        if val:
            candidates.append(os.path.join(val, 'hub', f'models--{safe_name}'))
    default_cache = os.path.expanduser('~/.cache/huggingface/hub')
    candidates.append(os.path.join(default_cache, f'models--{safe_name}'))
    return any(os.path.isdir(c) for c in candidates)


class _LazySentenceTransformerFn:
    """懒加载嵌入函数包装器。

    在首次调用 __call__ 时才真正加载 SentenceTransformer 模型；
    若模型未缓存且离线则抛出异常，由调用方降级处理。
    """

    def __init__(self, model_name: str = _EMBEDDING_MODEL):
        self._model_name = model_name
        self._model = None
        self._loaded = False
        self._load_failed = False

    def _ensure_loaded(self):
        if self._loaded or self._load_failed:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._loaded = True
        except Exception as e:
            logger.warning(f'[RAG] 嵌入模型加载失败（将降级为纯 BM25）：{e}')
            self._load_failed = True

    def __call__(self, input: list[str]) -> list[list[float]]:
        self._ensure_loaded()
        if self._model is None:
            raise RuntimeError('嵌入模型不可用，无法进行向量检索')
        return self._model.encode(input, normalize_embeddings=True).tolist()

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self(input)


class HybridRetriever:
    """BM25 + 向量混合检索器。

    用法：
        retriever = HybridRetriever(collection_name="fengshui_knowledge")
        retriever.add_documents(chunks)       # 批量添加
        results = retriever.search("八字身强身弱", top_k=5)
    """

    def __init__(self, persist_dir: str = None, collection_name: str = "fengshui_knowledge"):
        """
        Args:
            persist_dir: ChromaDB 持久化目录，不传则使用内存模式
            collection_name: 集合名称
        """
        self.collection_name = collection_name
        self._bm25: Optional[object] = None
        self._docs: list[str] = []
        self._meta: list[dict] = []
        self._chroma_client = None
        self._collection = None
        self._embedding_fn = None  # 延迟在 add_documents 中初始化

        if _HAS_CHROMA:
            # 注意：不能用局部 import chromadb，否则 Python 会把整个方法中的
            # chromadb 视为局部变量，未赋值前先访问会触发 UnboundLocalError。
            if persist_dir:
                self._chroma_client = chromadb.PersistentClient(path=persist_dir)
            else:
                self._chroma_client = chromadb.Client()

            # 仅当模型已缓存时才使用向量检索，否则自动降级为纯 BM25
            if _hf_model_cached(_EMBEDDING_MODEL):
                self._embedding_fn = _LazySentenceTransformerFn()
                logger.info('[RAG] 嵌入模型已缓存，启用向量检索模式')
            else:
                self._embedding_fn = None
                logger.info('[RAG] 嵌入模型未缓存，使用纯 BM25 降级模式'
                            f'（首次联网运行后将自动启用向量检索）')
        else:
            logger.info('[RAG] chromadb 未安装，使用纯 BM25 降级模式')

    def add_documents(self, chunks: list[dict]) -> int:
        """批量添加知识块。

        Args:
            chunks: chunker 输出的知识块列表

        Returns:
            int: 成功添加的数量
        """
        if not chunks:
            return 0

        texts = [c['text'] for c in chunks]
        metadatas = [{'source': c.get('source', ''), 'chunk_id': c.get('chunk_id', i)}
                     for i, c in enumerate(chunks)]

        # BM25 索引
        if _HAS_BM25:
            tokenized = [_tokenize_zh(t) for t in texts]
            self._bm25 = BM25Okapi(tokenized)
            self._docs = texts
            self._meta = metadatas

        # ChromaDB 向量索引
        if _HAS_CHROMA and self._embedding_fn is not None:
            try:
                ids = [f"chunk_{i}" for i in range(len(texts))]
                self._collection = self._chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    embedding_function=self._embedding_fn,
                    metadata={"hnsw:space": "cosine"}
                )
                # 检查是否已有数据
                existing = self._collection.count()
                if existing == 0:
                    self._collection.add(
                        documents=texts,
                        metadatas=metadatas,
                        ids=ids
                    )
            except Exception as e:
                print(f"[RAG] ChromaDB 添加失败: {e}")
                # 降级为纯 BM25
                self._bm25 = None

        return len(texts)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """混合检索。

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            list[dict]: 含 'text', 'score', 'source', 'chunk_id' 的结果列表
        """
        if not query or not query.strip():
            return []

        results: list[dict] = []

        # BM25 检索
        bm25_scores: list[float] = []
        if _HAS_BM25 and self._bm25 is not None and self._docs:
            query_tokens = _tokenize_zh(query)
            raw_scores = self._bm25.get_scores(query_tokens)
            # rank_bm25.get_scores 返回 numpy 数组，先转 Python list 避免
            # numpy 数组的布尔真值歧义（"truth value is ambiguous"）
            bm25_scores = list(raw_scores)
            # 归一化 BM25 分数（防止除零）
            max_bm25 = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1.0
            bm25_norm = [s / max_bm25 for s in bm25_scores]
        else:
            bm25_norm = [0.0] * len(self._docs)

        # 向量检索
        vector_scores: list[float] = []
        if _HAS_CHROMA and self._collection is not None and self._embedding_fn:
            try:
                query_embed = self._embedding_fn.embed_documents([query])
                result = self._collection.query(
                    query_embeddings=query_embed,
                    n_results=min(top_k * 2, self._collection.count()),
                    include=["distances", "metadatas", "documents"]
                )
                # 余弦距离转相似度
                distances = result.get("distances", [[]])[0]
                vector_scores = [1.0 - d for d in distances]  # 距离越小=越相似
                # 填充缺失的分数
                while len(vector_scores) < len(self._docs):
                    vector_scores.append(0.0)
            except Exception:
                vector_scores = [0.0] * len(self._docs)
        else:
            vector_scores = [0.0] * len(self._docs)

        # 综合打分：BM25 * 0.4 + 向量 * 0.6
        doc_count = max(len(self._docs), len(bm25_norm), len(vector_scores))
        for i in range(doc_count):
            bm25_s = bm25_norm[i] if i < len(bm25_norm) else 0.0
            vec_s = vector_scores[i] if i < len(vector_scores) else 0.0
            combined = bm25_s * 0.4 + vec_s * 0.6

            if combined <= 0:
                continue

            meta = self._meta[i] if i < len(self._meta) else {}
            text = self._docs[i] if i < len(self._docs) else ""

            results.append({
                'text': text,
                'score': round(combined, 4),
                'source': meta.get('source', ''),
                'chunk_id': meta.get('chunk_id', i),
            })

        # 按分数降序排序，取 top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def search_with_sources(self, query: str, top_k: int = 5) -> list[dict]:
        """增强版检索，返回出处信息。

        格式：
        {
            'text': '...',
            'score': 0.85,
            'source': '子平真诠',
            'chunk_id': 3,
            'citation': '《子平真诠·论格局》'
        }
        """
        results = self.search(query, top_k=top_k)
        for r in results:
            r.setdefault('citation', f"《{r.get('source', '古籍')}》")
        return results
