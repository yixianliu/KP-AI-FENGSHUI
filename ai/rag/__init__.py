# ai/rag 子包初始化

"""
ai.rag — RAG 知识库与向量检索模块

功能：
  - ChromaDB 本地向量库管理
  - bge-small-zh 文本向量化
  - BM25 + 向量混合检索
  - 古籍知识片段管理

使用示例：
    from ai.rag.knowledge_base import RAGKnowledgeBase
    kb = RAGKnowledgeBase()
    results = kb.search("八字身强身弱如何判断", top_k=5)
"""

from ai.rag.knowledge_base import RAGKnowledgeBase
from ai.rag.chunker import chunk_text, load_corpus_from_dir
from ai.rag.retriever import HybridRetriever

__all__ = [
    'RAGKnowledgeBase',
    'chunk_text',
    'load_corpus_from_dir',
    'HybridRetriever',
]
