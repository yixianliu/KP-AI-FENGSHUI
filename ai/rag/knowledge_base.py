# -*- coding: utf-8 -*-
"""
ai/rag/knowledge_base.py — RAG 知识库管理类

封装 ChromaDB + BM25 混合检索，提供标准化的知识查询接口。
古籍来源：《沈氏玄空学》《地理辩证疏》《子平真诠》《滴天髓》
"""
from __future__ import annotations

from ai.rag.retriever import HybridRetriever
from ai.rag.chunker import chunk_text


class RAGKnowledgeBase:
    """RAG 知识库主类。

    用法：
        kb = RAGKnowledgeBase(persist_dir="./ai/rag/chroma_db")
        kb.load_from_text("《子平真诠》相关内容...")
        results = kb.search("什么是用神", top_k=5)
    """

    # 内置默认语料（公有领域古籍摘要）
    DEFAULT_CORPUS = {
        "子平真诠": """
            何谓用神：八字用神，专求月令。以日干配月令之神，
            如甲木生寅月，甲木得禄，是谓身旺。身旺宜克泄，身弱宜生扶。
            用神之胜负：月令本气为用，余气为次。用神有力者为胜，
            无用神或用神受损者为败。格局成败，全系于用神。
        """,
        "滴天髓": """
            五行旺衰：春木旺、夏火旺、秋金旺、冬水旺、四季土旺。
            得令者旺，失令者衰。旺者宜泄不宜克，衰者宜生不宜克。
            调候为急：冬金需火炼，夏木需水润。调候得宜，格局方成。
        """,
        "沈氏玄空学": """
            玄空飞星：洛书九星，一白坎、二黑坤、三碧震、四绿巽、
            五黄中央、六白乾、七赤兑、八白艮、九紫离。
            运星入中，顺逆飞布。山星管人丁，向星管财禄。
            当运者旺，退运者衰。七星打劫，城门诀法，皆须细推。
        """,
        "地理辩证疏": """
            龙穴砂水：龙为山脉之祖，穴为气聚之所，砂为护持之山，
            水为血脉之流。龙真穴的，砂环水抱，方为上格。
            来龙去脉，须辨真假。真龙曲折盘旋，假龙直硬无情。
        """,
        "穷通宝鉴": """
            调候用神：甲木生于正月，寒气未除，先用丙火，后取庚金。
            乙木生于正月，阳气初升，先用丙火，次取癸水。
            丙火生于正月，余寒犹厉，专用壬水，次取庚金。
            各月调候，各有专司，不可误用。
        """,
    }

    def __init__(self, persist_dir: str = None):
        """
        Args:
            persist_dir: ChromaDB 持久化目录，不传则使用内存模式
        """
        self._retriever = HybridRetriever(persist_dir=persist_dir)
        self._loaded = False

    def load_builtin_corpus(self) -> int:
        """加载内置默认语料（来自公有领域古籍）。

        Returns:
            int: 加载的知识块数量
        """
        if self._loaded:
            return 0

        all_chunks: list[dict] = []
        for source, text in self.DEFAULT_CORPUS.items():
            # 短文本使用更小的 min_len 以确保能切分出块
            chunks = chunk_text(text, min_len=50, max_len=500, overlap=20)
            for c in chunks:
                c['source'] = source
            all_chunks.extend(chunks)

        count = self._retriever.add_documents(all_chunks)
        self._loaded = True
        return count

    def load_from_text(self, text: str, source: str = "custom") -> int:
        """从任意文本加载知识块。

        Args:
            text: 古籍文本内容
            source: 来源标识

        Returns:
            int: 加载的知识块数量
        """
        chunks = chunk_text(text)
        for c in chunks:
            c['source'] = source
        return self._retriever.add_documents(chunks)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """检索相关知识块。

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            list[dict]: 含 text, score, source, citation 的结果列表
        """
        if not self._loaded:
            self.load_builtin_corpus()

        return self._retriever.search_with_sources(query, top_k=top_k)

    def search_raw(self, query: str, top_k: int = 5) -> list[dict]:
        """原始检索（不含 citation 字段）。

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            list[dict]: 含 text, score, source, chunk_id 的结果列表
        """
        if not self._loaded:
            self.load_builtin_corpus()

        return self._retriever.search(query, top_k=top_k)
