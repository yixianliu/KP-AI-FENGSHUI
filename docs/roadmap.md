# 风水排盘专业工具 · 项目路线图

> 最后更新：2026-07-28

## 一、已完成（P0 / P1 / P2 全部闭环）

### P0 · 正确性闭环
- **P0-1a 大六壬单元测试**（`tests/test_liuren.py`，18 项）：锁定干支换算、天地盘、四课、天将、神煞（驿马）稳定部分。
- **P0-1b 综合 / 导出器单元测试**（`tests/test_comprehensive_export.py`，14 项）：覆盖三导出器对八字、综合建议的可写性；同时暴露并修复 `disclaimer` 字符串字段未兜转问题。
- **P0-2a 综合建议落库**：`_on_zonghe_finished` 调 `save_pan_record(pan_type='综合建议', ...)`，`_last_bazi_input` 实例变量存档。
- **P0-2b 综合建议导出**：`base_exporter.CHAPTERS` 新增 `('zonghe','综合建议')` 章节，三导出器渲染 `tri_method_overview/consistency_check/synthesis/unified_plan/key_timing/disclaimer` 全字段。

### P1 · 专业度硬伤
- **P1-1a 大六壬三传修正**（`core/liuren.py`）：
  - 重写 `_build_sanchuan`，按 gate（zeike / biyong / shehai / fuyin / fanyin / maoxing / bazhuan / bieze）分支生成中末传。
  - 修复 `_forced_gate` 元组缺逗号崩溃。
  - 比用法改按地支阴阳奇偶而非五行同名判定。
- **P1-1b 大六壬神煞与月将**（`core/liuren.py`）：
  - `_build_shensha` 扩展为 7 类：驿马、六合、空亡（旬空）、六害、旺相休囚死、天马、三传摘要。
  - 月将改为基于"太阳黄经过中气"映射（含 `_solar_longitude` 工具函数）。
- **P1-2 八字十二长生**（`core/_baazi_compat.py`）：
  - 完整实现 `analyze_shier_shen`：阳干顺行、阴干逆行；返回 `{'shier_shen': [{pillar, ganzhi, shier_shen, description}, …]}`。
  - 测试从"非空 dict"弱断言升级为"4 项各含 4 字段且宫位 ∈ 12 长生"。

### P2 · 完善治理
- **P2-1 梅花 / 大六壬导出可达**：
  - `base_exporter.CHAPTERS` 新增 `('meihua','梅花易数')` 与 `('liuren','大六壬起课')`。
  - 三导出器新增 `_add_meihua_section` / `_build_meihua` 与对应六壬方法。
  - `MeihuaResultPanel` / `LiurenResultPanel` 加 📤 导出按钮，复用 `ExportDialog` 与 `filter_export_data`。
  - 新增 3 项导出测试覆盖 CSV / Excel 对两个章节。
- **P2-2 用户体系加固**（`ui/components/login_dialog.py`）：
  - DB 不可用时 `_on_login` / `_on_register` 改为明确报错（QMessageBox.critical），不再"模拟登录/注册"绕过。
- **P2-3 种子固化 + 文档**：
  - `database/schema_sqlite.sql` 末尾新增 `meihua_knowledge` 8 条 INSERT 种子（与 `_BUILTIN_MEIHUA_RULES` 同步）。
  - 新增 `tests/test_meihua_knowledge_seed.py`（4 项）锁定种子随 schema 自动恢复。

## 二、当前测试矩阵（57 项全绿）

| 模块 | 测试文件 | 用例数 |
|---|---|---|
| 八字基础 + 性能 + 安全 | `tests/test_all.py` | 11 |
| 梅花易数 + 数据校验 | `tests/test_all.py` | 5 |
| 大六壬（稳定部分） | `tests/test_liuren.py` | 11 |
| 大六壬（九宗门三传表征） | `tests/test_liuren.py` | 7 |
| 综合 + 导出器 | `tests/test_comprehensive_export.py` | 14 |
| meihua_knowledge 种子 | `tests/test_meihua_knowledge_seed.py` | 4 |

## 三、打包与部署

- **必须使用 managed Python 3.13.12**（`C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/`）。
- spec 文件：`build_release.spec`，已固化 VC++ 运行时 + python313.dll + PySide6 + shiboken6。
- 产物：`dist/风水排盘专业工具/风水排盘专业工具.exe` + `_internal/`。
- 验证法：`QT_QPA_PLATFORM=offscreen timeout 14s 风水排盘专业工具.exe`，EXIT=124 即存活。

## 四、后续待办（仅供参考，不在 P0/P1/P2 范围内）

- **大六壬九宗门表征测试扩展**：伏吟 / 返吟 / 别责等目前 7 项门法表征测试已绿，可继续为 12 神将课体增测试。
- **八字流时与日柱精确换算**：已用 `lunarcalendar`，可考虑引入 `cnlunar` / `pyephem` 增强精度。
- **用户跨重启会话保持**：当前主流程用 `_last_bazi/meihua/liuren_record_id` 缓存；可加 `QSettings` 持久化。
- **AI 缓存复用**：相同排盘 + 问题应可命中本地缓存，避免重复调用 API。
- **国际化**：项目目前无 locale 文件，后续若需多语言，可加入 `ui/i18n/`。

## 五、变更约定

- 任何对命理规则的修改，须先在 `tests/test_liuren.py` 或新增表征测试中固化预期值，再改实现。
- 任何对 AI 提示词或字段契约的修改，须同步 `core/analysis_pipeline.py` 与 `tests/test_comprehensive_export.py`。
- 任何对导出章节的修改，须同步 `ui/export/base_exporter.py` 与三导出器 + `tests/test_comprehensive_export.py`。
