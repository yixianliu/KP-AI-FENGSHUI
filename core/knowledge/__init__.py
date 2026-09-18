"""core/knowledge — 命理知识库与分析管道包。

本包聚合了知识库、分析存储与数据校验模块：
  - knowledge_base : 命理知识库（结构化存储八字命理与梅花易数专业知识）
  - rag_knowledge : RAG 知识库（BM25 + 向量检索）
  - analysis_storage : 分析存储（排盘记录落库与 AI 分析管道）
  - analysis_fallback : 分析降级（AI 不可用时的兜底解读）
  - data_integration : 数据整合（收集、清洗、统一分析数据）
  - data_validator / data_validator_v2 : 输入数据校验
"""
