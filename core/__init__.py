"""核心业务模块 - 八字排盘、起卦、命理分析、AI 分析管道。

Public API:
- AnalysisPipeline / DatabaseManager / AnalysisStorage 等在各显式子模块中导出
- 存储统一基于本地嵌入式 SQLite（core.sqlite_db，data/fengshui.db）
- 本包通过显式子模块导入，禁止依赖 ``from core import *``
"""
