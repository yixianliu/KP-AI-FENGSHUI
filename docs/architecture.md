# 架构说明与模块依赖关系（KP-AI-FENGSHUI）

> 维护者文档。最近更新：2026-07-25（存储架构统一为本地 SQLite 后）。

## 1. 技术栈
- 语言：Python 3.13（打包使用 managed Python 3.13.12）
- GUI：PySide6（Qt6）
- 数据库：本地嵌入式 SQLite（`data/fengshui.db`，首次运行自动建库）
- AI 接口：Agnes AI（`api/agnes_client.py`，读 `config.ini [agnes]`）
- 依赖：`requirements.txt`（PySide6 / lunarcalendar / bcrypt / openpyxl / reportlab）

## 2. 分层结构
```
main.py  ── 程序入口（Qt 启动、全局异常钩子、窗口图标）
   │
ui/  ── 界面层（main_window 主控 + components/* 对话框 + export/* 导出）
   │
core/ ── 业务核心（计算 / 存储 / 流程 / 兼容）
   │
api/  ── 外部接口（agnes_client：AI 分析）
   │
database/schema_sqlite.sql ── 建库 Schema（37 表）
data/fengshui.db            ── 运行时数据库
```

## 3. 依赖关系（箭头 = 依赖于）
- `main.py` → `ui.main_window` → `ui.components.*` / `ui.export.*`
- UI 组件 → `core.analysis_pipeline` / `core.database_manager` / `core.analysis_storage` / `core.sqlite_db`
- `core.analysis_pipeline` → 排盘计算模块（`bazi_calculator` / `meihua` / `liuren` / `yuncheng` / `yunshi` / `geju_analyzer` / `shishen` / `wuxing` / `mingli`）
- 排盘计算模块 → 参考表读取（`core.database_manager` / `core.sqlite_db`）+ 历法（`calendar_utils` / `lunar_converter` / `_baazi_compat`）
- `core.database_manager` / `core.analysis_storage` → `core.sqlite_db` → `database/schema_sqlite.sql` → `data/fengshui.db`
- `api.agnes_client` → `config.ini [agnes]`

## 4. 关键约束（重构/迁移时务必遵守）
1. **存储唯一入口**：所有读写经 `core.sqlite_db.get_connection()`；行工厂为 dict（兼容 `row.get()`，对齐旧 MySQL DictCursor 行为）。禁止在业务代码中自建 `sqlite3.connect`。
2. **Schema 来源**：改表结构应改 `database/base.sql`（MySQL 源）后重跑 `scripts/convert_mysql_to_sqlite.py` 重新生成 `database/schema_sqlite.sql`，勿手改 schema 或 db。
3. **兼容垫片**：`core/_baazi_compat.py` 被 `bazi_calculator` / `lunar_converter` / `mingli` / `shishen` 引用，**不可删除**。
4. **AI 降级**：`config.ini` 缺失 `[agnes]` 段时，AI 分析优雅降级，不影响排盘主流程。
5. **打包唯一规格**：仅用 `build_release.spec` + managed Python 3.13.12（否则缺 `python313.dll` / `shiboken6` 不匹配）。产物：`dist/风水排盘专业工具/`。

## 5. Schema 生成链
```
database/base.sql  ──▶  scripts/convert_mysql_to_sqlite.py  ──▶  database/schema_sqlite.sql  ──▶  data/fengshui.db
```
图标链：`assets/app_icon.svg` ──▶ `favicon.ico` / `app_icon_512.png`（打包 datas 引用）。

## 6. 目录职责速查
| 目录 | 职责 |
|---|---|
| `core/` | 排盘计算、存储层、分析流水线、校验、知识库 |
| `ui/` | 主控窗口、输入/结果/历史/设置/登录/关于对话框、AI worker、CSV/Excel/PDF 导出 |
| `api/` | AI 外部接口 |
| `scripts/` | `convert_mysql_to_sqlite.py`（Schema 生成，重要）、`agnes_test_client.py`、`_smoke_analysis.py` |
| `tests/` | `test_all.py`（统一测试入口，15 用例） |
| `database/` | `base.sql`（MySQL 源）+ `schema_sqlite.sql`（SQLite 权威） |
| `data/` | `fengshui.db`（运行时，gitignore） |
| `assets/` | 图标矢量源 |
| `docs/` | 本文档 + 结构报告 + 历史方案归档 |
