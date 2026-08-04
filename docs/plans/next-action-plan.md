# 风水排盘专业工具 — 下一步开发行动计划（2026-07-27）

> 依据实际代码库核实结果制定。所有定位均附 `文件:行号`。
> 范围：八字 / 梅花易数 / 大六壬 / 综合建议 / 导出 / 用户体系 / 测试 / 打包。

---

## 一、项目当前状态

### 已完成（可交付）
- 三层 GUI：导航 `八字排盘 / 梅花易数 / 大六壬 / 综合建议 / 历史记录`（`ui/main_window.py` NAV）。
- 八字引擎真实可用：`core/bazi_calculator.py` + `wuxing / shishen / mingli / yunshi / geju_analyzer`（geju_analyzer 635 行，无桩）。
- 三术数 AI 分析已调优：`analysis_pipeline.py` 提示词重写 + 梅花注入知识库 + max_tokens=4096；八字补数据（`result_panel.get_chart_data_for_ai`）。
- 综合建议已接通：`comprehensive_panel.py` → `main_window._on_zonghe_generate` → `ai_analysis_worker(comprehensive)` → `analysis_pipeline.run_comprehensive_analysis`（数据链经核对正确）。
- 存储统一为本地 SQLite（37 表 + 参考表），bcrypt 用户体系可用。
- AI 容错：全局异常钩子（`main.py`）、各方法 `_on_*_ai_failed`、类型兜转（`agnes_client._validate_json_result`）。
- 打包可用：`build_release.spec` + managed Python 3.13.12，已出含全部改动的 exe。

### 待办 / 缺口（已核实）
| 区域 | 位置 | 问题 |
|---|---|---|
| 大六壬·三传 | `core/liuren.py:244-284` | 中末传对所有 9 门用同一 `tian_pan` 链，伏吟/返吟/昴星/八专/别责 中末传错误 |
| 大六壬·神煞 | `core/liuren.py:311-323` | 仅 驿马 + 三传文本，缺 空亡/六合/旺相休囚死 等 |
| 大六壬·月将 | `core/liuren.py:104-106` | 按公历月近似，未按月将（太阳过中气） |
| 八字·十二长生 | `core/_baazi_compat.py:76-77` | `analyze_shier_shen` 直接 `return {}`（桩），测试被掩盖 |
| 综合建议·落库 | `ui/main_window.py:1336-1348` | `_on_zonghe_finished` 无 `save_pan_record`，历史查不到 |
| 综合建议·导出 | `ui/export/base_exporter.py:11-21` | 章节仅八字形状，无 zonghe 章节；综合结果导出为空 |
| 梅花/六壬·导出 | `ui/components/result_panel.py:1000-1019` | ExportDialog 仅八字面板触发，梅花/六壬/综合无入口 |
| 测试覆盖 | `tests/test_all.py` | 仅数据层/基础计算；liuren、analysis_pipeline、导出器 零覆盖 |
| 知识库种子 | `database/schema_sqlite.sql` | `meihua_knowledge` 种子未入 schema，删库重建即丢失 |
| 用户体系 | `ui/components/login_dialog.py:217,470` | DB 不可用时模拟登录可绕过；登录非强制、不跨重启 |
| 文档 | `docs/` | 无维护中 roadmap / known-issues；archive 草稿陈旧 |

---

## 二、当前阶段关键任务与优先级

- **P0（正确性闭环，先做）**：测试地基 + 综合建议落库/导出 —— 用户直接可见价值且风险最低。
- **P1（专业度硬伤）**：大六壬三传/神煞/月将修正 + 八字十二长生实现 —— 决定"专业工具"可信度。
- **P2（完善治理）**：梅花/六壬/综合导出可达 + 用户体系加固 + 文档/种子固化。

---

## 三、未完成核心功能 · 具体推进方案

### A. 大六壬正确性（P1-1）
- **三传**：在 `_build_sanchuan` 中按 `gate` 分支构造中末传，移除 `liuren.py:244-246` 的通用链：
  - 贼克/比用：中传取初传地盘本位、末传取中传地盘本位（现行初传可取）。
  - 涉害：依"涉害深浅"取孟/仲/季位，非天盘链。
  - 伏吟：中传取初传之刑，末传取中传之刑（寅巳申三刑等）。
  - 返吟：初传支上、中传支阴/干上、末传干上。
  - 昴星：阳日初传酉→中传支上→末传干上；阴日反之。
  - 八专：三传皆干上神。
  - 别责：初传干上，中末传取干合/支合。
- **神煞**：补 空亡（旬空）、六合（日干六合支）、旺相休囚死（月令）、天马、六害等，建静态表。
- **月将**：改为按太阳过中气映射（建 `节气→月将` 表，120 年精度足够），替换 `liuren.py:104-106`。

### B. 八字十二长生（P1-2）
- 实现 `_baazi_compat.analyze_shier_shen`：输入日干 + 各柱地支，按 12 长生宫位表（长生/沐浴/冠带/临官/帝旺/衰/病/死/墓/绝/胎/养）映射，阳顺阴逆。
- 将 `tests/test_all.py` 的 `test_get_shier_shen` 断言由 `isinstance(dict)` 改为校验含非空十二宫。

### C. 综合建议闭环（P0-2）
- **落库**：`_on_zonghe_finished` 调 `save_pan_record(record_type='zonghe', ai_analysis=ai_analysis)`；`database_manager` 若缺 `method/record_type` 列则补。
- **导出**：`base_exporter` 增 `('zonghe','综合建议')` 章节与对应键（`tri_method_overview/consistency_check/synthesis/unified_plan/key_timing/disclaimer`）；`comprehensive_result_panel` 加导出按钮复用 `ExportDialog`。

### D. 导出可达（P2-1）
- 扩展导出器支持 meihua/liuren/zonghe 数据形状（各自章节集）；在 `meihua_result_panel`/`liuren_result_panel` 加导出按钮。

---

## 四、阻塞与依赖 · 解决路径

- **大六壬领域知识**：无外部 API，依赖《大六壬大全》经典规则 + 静态表。风险=规则繁多易错 → 对策：**先写表征测试**（古籍/《壬归》已知课例锁定正确输出）再实现，避免回归。
- **综合建议数据契约**：zonghe result 字段已固化（`tri_method_overview…disclaimer`）。落库与导出共用此契约，先定契约再改两端，避免字段漂移。
- **用户体系**：是否强制登录是产品决策非技术阻塞 → 先保留可选，去除"DB 失败模拟登录绕过"（改为明确报错）。
- **运行环境**：`test_env/` 为 vendor 虚拟环境（4217 文件），**不作为运行环境**；测试用 managed Python 3.13.12 + 项目依赖。

---

## 五、下一步行动计划（执行顺序 + 预估工作量）

| 序 | 任务 | 描述 | 预估 | 前置 |
|---|---|---|---|---|
| 1 | P0-1a 大六壬单测 | `liuren.py` 排盘/三传/神煞单测 + 已知课例表征测试 | 0.5d | — |
| 2 | P0-1b 综合/导出单测 | `run_comprehensive_analysis` + 三导出器单测 | 0.5d | — |
| 3 | P0-2a 综合建议落库 | `main_window` + `database_manager` 加 zonghe 记录 | 0.5d | 契约§三C |
| 4 | P0-2b 综合建议导出 | `base_exporter` 加 zonghe 章节 + 面板按钮 | 0.5d | 3 |
| 5 | P1-1a 三传修正 | 九宗门中末传按门实现 | 1.5d | 1（测试先行） |
| 6 | P1-1b 神煞/月将 | 空亡/六合/旺衰 + 节气月将 | 1d | 5 |
| 7 | P1-2 十二长生 | 实现 `analyze_shier_shen` + 测试 | 0.5d | — |
| 8 | P2-1 梅花/六壬导出 | 扩展导出器 + 两面板按钮 | 1d | 4（复用框架） |
| 9 | P2-2 用户体系加固 | 去模拟登录绕过 + 可选登录明确化 | 0.5d | — |
| 10 | P2-3 文档/种子 | 建 `roadmap.md` + `meihua_knowledge` 种子入 schema/init | 0.5d | — |

**合计 ≈ 8 人日。**

### 推荐执行节奏
1. 先跑 **1–2** 建安全网（尤其大六壬表征测试，为步骤 5 护航）。
2. 做 **3–4** 闭环综合建议（用户直接可见价值：历史可查 + 可导出）。
3. 攻 **5–7** 专业度硬伤（大六壬 + 十二长生），全程靠 1/7 的测试防回归。
4. 收尾 **8–10** 完善导出可达面与工程治理。

### 验证门禁（每步必过）
- `python -m py_compile` 全量通过；`tests/test_all.py` 全过（步骤 1/2/7 新增测试须通过）。
- 大六壬修正后用步骤 1 的表征测试覆盖 9 宗门各一门例题。
- 综合建议落库后历史记录可检索；导出后文件可被 Excel/PDF 打开且非空。
- 改动完成后用 managed Python 3.13.12 按 `build_release.spec` 重新打包并无头启动验证。
