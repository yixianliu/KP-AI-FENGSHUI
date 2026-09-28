# KP-AI-FENGSHUI UI 升级 · 实施推进计划

> 版本：v1.0
> 编制日期：2026-09-24
> 依据文档：[UI-Upgrade-Implementation-Plan.md](./UI-Upgrade-Implementation-Plan.md) v1.0
> 定位：将「升级方案」转化为**可执行、可验收、可回滚**的项目推进蓝图
> 总工期：**10 个工作日**（不含最终 code review 与 QA 缓冲 1 天，实际落地周期 11 天）

---

## 目录（TOC）

1. [推进原则与目标](#1-推进原则与目标)
2. [团队角色与责任分配（RACI）](#2-团队角色与责任分配raci)
3. [任务分解结构（WBS）](#3-任务分解结构wbs)
4. [里程碑与时间节点甘特](#4-里程碑与时间节点甘特)
5. [资源需求](#5-资源需求)
6. [设计规范一致性保障机制](#6-设计规范一致性保障机制)
7. [阶段性测试与验收机制](#7-阶段性测试与验收机制)
8. [用户反馈闭环与调整策略](#8-用户反馈闭环与调整策略)
9. [风险登记册与应对](#9-风险登记册与应对)
10. [交付物清单](#10-交付物清单)
11. [启动前 Checklist（T-2 准备日）](#11-启动前-checklistt-2-准备日)

---

## 1. 推进原则与目标

### 1.1 三条铁律

1. **不越界**：`core/` 计算层零改动；AI 解读、数据库、算法一律不动。
2. **不降级**：每一阶段合并后必须通过该阶段的 Gate 验收，验收不通过则**禁止进入下一阶段**（除紧急修复）。
3. **可回滚**：每阶段独立 PR，独立可 `git revert`；`styles.py` 每次改版留版本注释，允许 24 小时回退窗口。

### 1.2 阶段验收总目标（对齐实施计划 7.1~7.7）

| 维度 | 硬指标 |
|------|--------|
| 设计令牌合规率 | `scripts/audit_style_tokens.py` 硬编码命中率 0（除 `styles.py`） |
| 视觉还原 | 三主色使用率 ≥ 95%，字号严格 7 级，间距 8-4 基准 |
| 交互一致 | 按钮 6 态、输入 4 态、ListItem 4 态全通过 |
| 可访问性 | 全文对比度 ≥ 4.5:1（大字 ≥ 3:1），焦点可见 |
| 性能 | 冷启动 < 2s，UI 渲染 < 200ms，内存 < 150MB |
| 回归 | 四大板块 + 弹窗 + 导出 + 缩放 10 项场景全通过 |
| UI 层测试覆盖 | `pytest tests/ui/` ≥ 60% |

---

## 2. 团队角色与责任分配（RACI）

> 本项目为单主力 + 支持型结构。为便于协作与未来扩展，仍按角色（非具体人）划分职责。
> 角色代号：**P**=PM/项目负责，**D**=设计负责，**U**=UI 实现（前端），**A**=算法/测试负责，**U0**=最终用户代表。

| 角色 | 主要职责 | 参与阶段 |
|------|---------|---------|
| **P**（项目负责） | 排期、Gate 决策、跨阶段协调、验收签收 | M0 ~ M7 全程 |
| **D**（设计负责） | 设计令牌冻结、图标源确认、色板/字号/间距终版、设计走查 | M1、M5、M7 |
| **U**（UI 实现） | 全部代码改造、组件新增、样式迁移 | M1 ~ M6 |
| **A**（算法/测试负责） | 回归用例编写、脚本校验（token/对比度）、覆盖率把关 | M1、M6、M7 |
| **U0**（最终用户代表） | 灰度试用、反馈闭环 | M6 之后、M7 全程 |

### RACI 责任矩阵（列 = 任务，行 = 角色）

| 角色 \ 任务 | T1 令牌 | T2 图表 | T3 排版 | T4 列表 | T5 视觉 | T6 动效 | T7 收口 |
|------------|--------|--------|--------|--------|--------|--------|--------|
| P | A | C | C | C | C | C | **A/R** |
| D | **R/A** | C | **A** | C | **R/A** | C | **A** |
| U | **R** | **R** | **R** | **R** | **R** | **R** | C |
| A | **R**（脚本） | C | C | C | C | C | **R**（回归） |
| U0 | I | I | I | I | I | C | **C**（试用） |

图例：**R**=负责执行，**A**=最终负责/签收，**C**=咨询，**I**=知会。

---

## 3. 任务分解结构（WBS）

按 7 个里程碑（M1~M7）拆解为 38 个可跟踪子任务，任务 ID 形如 `M3-T2`。

### M1 · 设计令牌冻结（1 天）

| ID | 任务 | 责任人 | 依赖 | 产出 |
|----|------|--------|------|------|
| M1-T1 | 收敛 `Colors` 同义命名（`QINGHUA/LIUJIN/YU/SHANHU` → 别名映射） | U | - | `ui/styles.py` Colors 类 |
| M1-T2 | 8-4 间距基准重构 `Spacing` | U | M1-T1 | `Spacing.S0~S8 / GAP*/PAD*` |
| M1-T3 | Font Scale 强化 `Fonts`（含 W_REGULAR~W_BOLD） | U | - | `Fonts.FS_* / SZ_*` |
| M1-T4 | 新增 `scripts/audit_style_tokens.py`（硬编码扫描） | A | M1-T1~T3 | 脚本 + 首次扫描报告 |
| M1-T5 | 新增 `scripts/audit_contrast.py`（WCAG 对比度） | A | - | 脚本 + 色板对比度报告 |
| M1-T6 | 图标资产批量下载（`scripts/download_icons.py` + 25 个 SVG） | U | - | `assets/icons/*.svg` |
| M1-T7 | 设计令牌冻结评审（D 签收） | D | M1-T1~T6 | `styles.py` v6.1 tag |

### M2 · 图表交互化（1.5 天，可与 M3 并行）

| ID | 任务 | 责任人 | 依赖 | 产出 |
|----|------|--------|------|------|
| M2-T1 | `_apply_theme()` 主题映射函数 | U | M1-T7 | `ai_metrics_chart.py` |
| M2-T2 | `resizeEvent` 响应式重绘 + `set_size_inches(forward=True)` | U | M2-T1 | 同上 |
| M2-T3 | 悬停 tooltip + 数据点高亮 | U | M2-T2 | 同上 |
| M2-T4 | 空数据 `EmptyState` 替换 `generate_demo_data` 伪造 | U | M4-T1 | 同上 |
| M2-T5 | `TaijiSpinner` 加载覆盖层 | U | - | 同上 |
| M2-T6 | 图表 DPI 抖动回归（125% / 150% / 200%） | A | M2-T2 | 截图对比 |

### M3 · 排版规范化（2 天，可与 M2 并行）

| ID | 任务 | 责任人 | 依赖 | 产出 |
|----|------|--------|------|------|
| M3-T1 | 新增 `ui/components/typography.py`（`TLabel` 工厂） | U | M1-T7 | 新文件 |
| M3-T2 | `styles.py` 追加 `_qss_font_scale()` | U | M3-T1 | QSS `QLabel#t-*` |
| M3-T3 | 全 UI `QLabel` 硬编码替换为 `TLabel` | U | M3-T1 | 全 UI 层 |
| M3-T4 | 全 UI `setContentsMargins/setSpacing` 走 `Spacing` 常量 | U | M1-T2 | 全 UI 层 |
| M3-T5 | `collapsible_card.py` 标题字体绑定 Font Scale | U | M3-T1 | 微调 |
| M3-T6 | 排版一致性走查（键盘/焦点/行高） | D | M3-T3~T5 | 走查记录 |

### M4 · 列表与状态组件（2 天）

| ID | 任务 | 责任人 | 依赖 | 产出 |
|----|------|--------|------|------|
| M4-T1 | 新增 `ui/components/states.py`（`EmptyState / LoadingState / ErrorState`） | U | M1-T7 | 新文件 |
| M4-T2 | 新增 `ui/components/list_item.py` + `LIST_ITEM` QSS | U | M1-T7 | 新文件 |
| M4-T3 | 新增 `ui/components/badge.py` | U | M1-T7 | 新文件 |
| M4-T4 | `result_panel.py` 大运/流年列表替换为 `ListItem+Badge` | U | M4-T2/T3 | 中等改造 |
| M4-T5 | `liuren_result_panel.py` 十二天将列表改造 | U | M4-T2 | 中等改造 |
| M4-T6 | `xuan_kong_result_panel.py` `_CELL_COLORS` 走 `Colors` + 宫位列表化 | U | M4-T2 | 中等改造 |
| M4-T7 | `meihua_result_panel.py` 卦象图标 SVG 化 | U | M4-T2, M1-T6 | 中等改造 |
| M4-T8 | 列表一致性走查 | D | M4-T4~T7 | 走查记录 |

### M5 · 视觉一致性（2 天）

| ID | 任务 | 责任人 | 依赖 | 产出 |
|----|------|--------|------|------|
| M5-T1 | 新增 `ui/components/icons.py`（`icon(name,size)`） | U | M1-T6 | 新文件 |
| M5-T2 | 侧边栏 4 图标 Unicode → SVG | U | M5-T1 | `main_window.py` |
| M5-T3 | 结果面板工具栏 emoji → SVG | U | M5-T1 | 4 个 result panel |
| M5-T4 | `styles.py` 补 `ButtonStates`（6 态）+ 输入控件 4 态 | U | M1-T7 | `styles.py` |
| M5-T5 | 新增 `ui/components/icon_button.py` | U | M5-T1, M5-T4 | 新文件 |
| M5-T6 | 新增 `ui/components/data_card.py` | U | M1-T7 | 新文件 |
| M5-T7 | 3 个弹窗套用 `DIALOG` QSS | U | M1-T7 | settings/export/about_dialog |
| M5-T8 | 视觉一致性走查（D 签收） | D | M5-T2~T7 | 走查记录 |

### M6 · 动效与 AI 流式（1 天）

| ID | 任务 | 责任人 | 依赖 | 产出 |
|----|------|--------|------|------|
| M6-T1 | 新增 `ui/animation.py`（缓动 + 时长常量） | U | M1-T7 | 新文件 |
| M6-T2 | `CollapsibleCard` 折叠动画 300ms `IN_OUT_CUBIC` | U | M6-T1 | 微调 |
| M6-T3 | `ListItem` / 卡片 hover 阴影动画 | U | M6-T1 | 微调 |
| M6-T4 | AI 输出流式追加动画（`QGraphicsOpacityEffect`） | U | M6-T1 | `ai_analysis_renderer.py` |
| M6-T5 | 板块切换淡入淡出（`QStackedWidget`） | U | M6-T1 | `main_window.py` |
| M6-T6 | 时间轴节点 hover 增强 | U | M6-T1 | `timeline.py` |

### M7 · 收口与验收（0.5 天）

| ID | 任务 | 责任人 | 依赖 | 产出 |
|----|------|--------|------|------|
| M7-T1 | 对比度校验（`audit_contrast.py` 通过） | A | M1-T5 | 通过报告 |
| M7-T2 | ARIA / `setAccessibleName` 补齐 | U | - | 全 UI 层 |
| M7-T3 | 回归测试 10 场景跑通 | A | M2~M6 | `tests/ui/` |
| M7-T4 | UI 覆盖率 ≥ 60% | A | M7-T3 | `pytest --cov` 报告 |
| M7-T5 | 冷启动 < 2s、UI 渲染 < 200ms、内存 < 150MB | A | M2~M6 | 性能报告 |
| M7-T6 | `docs/design-tokens.md` + `docs/component-guide.md` | D | M1~M6 | 两份文档 |
| M7-T7 | README UI 章节更新 | U | - | `README.md` |
| M7-T8 | 最终交付签收（P + D + U0） | P | M7-T1~T7 | 签收单 |

---

## 4. 里程碑与时间节点甘特

以 **T+1 为启动日**（默认 2026-09-25，周五），按工作日排期，跳周末。

| 里程碑 | 名称 | 日期 | 工期 | 前置 | Gate |
|--------|------|------|------|------|------|
| **M0** | 启动准备（T-2 ~ T-1） | 2026-09-23 ~ 09-24 | 0.5d | - | 环境就绪 |
| **M1** | 令牌冻结 | 2026-09-25 | 1d | M0 | Gate-1 令牌签收 |
| **M2 ∥ M3** | 图表 + 排版（并行） | 09-28 ~ 09-30 | 1.5d + 2d 并行 | M1 | Gate-2 |
| **M4** | 列表 & 状态组件 | 10-09 ~ 10-10 | 2d | M3 | Gate-3 |
| **M5** | 视觉一致性 | 10-12 ~ 10-13 | 2d | M4 | Gate-4 |
| **M6** | 动效与流式 | 10-14 | 1d | M5 | Gate-5 |
| **M7** | 收口与交付 | 10-15 | 0.5d + 0.5d 缓冲 | M6 | Gate-6 签收 |

> 注：本排期跳过 2026-10-01 ~ 10-08 国庆假期；如遇不可抗力，M4/M5 顺序可互换（列表先做则图表空态延后）。

### 关键路径

```
M0 → M1 → M3 → M4 → M5 → M6 → M7
           ↖ M2 ↗（M2 与 M3 并行，M2 结束即接入 M4-T4 空态）
```

- **关键路径**：M1 → M3 → M4 → M5 → M6 → M7（共 8.5 工作日）
- **缓冲**：M2 完成后可提前插入 M3 走查，节省 0.5 天；M7 预留 0.5 天缓冲

---

## 5. 资源需求

### 5.1 人力资源

| 角色 | 投入人天 | 备注 |
|------|--------|------|
| UI 实现（U） | 10 人日 | 主力，全程 |
| 设计（D） | 1.5 人日 | M1 / M5 / M7 走查 |
| 测试（A） | 2 人日 | M1 脚本 + M7 回归 |
| 项目（P） | 0.5 人日 | Gate 决策 + 交付 |
| 用户（U0） | 0.5 人日 | M7 灰度试用 |
| **合计** | **14.5 人日** | 10 工作日并行 |

### 5.2 环境与工具

| 类别 | 需求 | 状态 |
|------|------|------|
| Python | 3.10 ~ 3.12 | 已具备 |
| PySide6 | 6.9 ~ 6.11 | 已具备 |
| Matplotlib | 3.7 ~ 3.9 | 已具备 |
| IDE | VSCode + Pylance | 已具备 |
| 网络 | 图标下载（一次性，25 SVG） | 需外网 30 分钟 |
| 授权 | Apache 2.0 / MIT 图标源（Tabler） | 无需付费 |
| CI | 本地 `pytest + ruff + mypy` | 已具备 |
| 版本管理 | Git + 独立分支 `feat/ui-upgrade-v1` | 需新建 |

### 5.3 依赖新增

- **运行时零新增**（不引入新包）
- **开发时可选新增**：`iconify-api-client`（仅图标下载用，可写一次性脚本替代）

---

## 6. 设计规范一致性保障机制

### 6.1 三层防护

```
Layer 1（作者侧）  ：Pylance 类型提示 + `scripts/audit_style_tokens.py` pre-commit
Layer 2（阶段侧）  ：每阶段 Gate 走查 + 截图基线（screenshots/baseline/）
Layer 3（合并侧）  ：CI 强制跑 `audit_style_tokens.py` + `audit_contrast.py`，不通过则阻塞
```

### 6.2 设计决策日志（ADR）

每次涉及全局设计决策（色板改动、字号调整、组件 API 变更），写入 `docs/adr/NNN-<title>.md`：

- 背景 / 决策 / 后果 / 回滚方式
- 示例：`001-color-token-consolidation.md`、`002-spacing-8-4.md`

### 6.3 组件变更约束

- **新增组件**（`ListItem / Badge / EmptyState / TLabel ...`）必须先写 `docs/component-guide.md` 章节，再写实现代码。
- **修改既有组件 API**（如 `CollapsibleCard`）必须走兼容期：新增 API 用 v2 方法，v1 方法标记 deprecated 但保留。
- **样式散落红线**：任何 UI 文件出现 `#xxxxxx` / `\d+px` / `setContentsMargins(数字)` 直接 pre-commit 拒绝。

### 6.4 响应式适配矩阵

| 尺寸断点 | 断点值 | 布局策略 |
|----------|--------|---------|
| XS | 1280×800 | 侧边栏 168px 固定 + 主区最小 620px |
| SM | 1440×900 | 主区内容居中，左右留白 ≥ 24px |
| MD | 1920×1080 | 主区最大宽度 1600px，居中留白 |
| LG | 2560×1440 | 主区最大宽度 1800px，字号不变 |
| 4K | 3840×2160 | Qt High-DPI aware，字号自动缩放，不硬放大 |
| DPI | 100/125/150/200% | Matplotlib 走 `forward=True`；SVG 图标无损 |

**校验方法**：每阶段截图回归（`scripts/screenshot_regression.py`，M7 落地）。

---

## 7. 阶段性测试与验收机制

### 7.1 三道 Gate 模型

每阶段结束执行 **Gate-Checklist**（下），未全部勾选则禁止进入下一阶段。

| Gate | 触发时点 | 验收人 | Checklist 数量 |
|------|---------|--------|---------------|
| Gate-1 | M1 结束 | D + P | 令牌类 8 项 |
| Gate-2 | M2+M3 结束 | D + U | 图表 + 排版 10 项 |
| Gate-3 | M4 结束 | D + U | 列表组件 8 项 |
| Gate-4 | M5 结束 | D + U | 视觉一致性 12 项 |
| Gate-5 | M6 结束 | U | 动效 6 项 |
| Gate-6 | M7 结束 | P + D + U0 | 最终 20 项 |

### 7.2 Gate-6 最终验收 Checklist（节选，完整版对齐实施计划 7.1~7.7）

**视觉（4 项）**
- [ ] `audit_style_tokens.py` 硬编码命中率 0（除 `styles.py`）
- [ ] 三主色使用率 ≥ 95%
- [ ] 字号 7 级，无散点
- [ ] 弹窗三区分明，标题/正文/底部一致

**交互（4 项）**
- [ ] 按钮 6 态、输入 4 态、ListItem 4 态全通过
- [ ] 图表 hover tooltip + 移出消失
- [ ] 折叠动画 300ms IN_OUT_CUBIC
- [ ] Tab 键盘流符合视觉顺序

**响应式（3 项）**
- [ ] 1280×800 / 1920×1080 / 3840×2160 均不溢出/不拉伸
- [ ] DPI 125/150/200% 无 Matplotlib 抖动
- [ ] 窗口缩放至最小 1100×700 不裁切

**性能（3 项）**
- [ ] 冷启动 < 2s
- [ ] 排盘 → 渲染 < 200ms
- [ ] 30 分钟长跑 `tracemalloc` 无增长，空闲内存 < 150MB

**可访问性（2 项）**
- [ ] 全部文本对比度 ≥ 4.5:1（大字 ≥ 3:1）
- [ ] 图标按钮 100% 具备 `accessibleName` / `tooltip`

**回归（4 项）**
- [ ] 四大板块全链路（八字 / 梅花 / 六壬 / 玄空）
- [ ] 设置 / 导出 / 关于弹窗
- [ ] CSV / Excel / PDF 导出
- [ ] `pytest tests/ui/` 覆盖率 ≥ 60%

### 7.3 分层测试策略

| 层 | 工具 | 触发时机 | 责任 |
|----|------|---------|------|
| 静态 | `ruff + mypy` | 每次提交 | U |
| 静态 | `audit_style_tokens.py` | pre-commit + CI | A |
| 静态 | `audit_contrast.py` | CI | A |
| 单元 | `pytest tests/ui/` | 每阶段 Gate | A |
| 集成 | 手工回归 10 场景 | M7 | A + U |
| 视觉 | `screenshot_regression.py` | 每阶段 Gate | A |
| 性能 | `tracemalloc` + 冷启动计时 | M7 | A |
| 用户 | U0 试用 30 分钟 | M7 缓冲日 | U0 |

---

## 8. 用户反馈闭环与调整策略

### 8.1 反馈渠道

| 渠道 | 形式 | 触发时机 | 责任人 |
|------|------|---------|--------|
| 内部走查 | D 每阶段末走查记录 | 每 Gate | D |
| U0 灰度 | 灰度分支试用 30 分钟 | M7 缓冲日 | U0 |
| 缺陷单 | `docs/ui-defect-log.md` | 全程 | U |
| 视觉争议 | ADR 决策日志 | 出现分歧时 | P + D |

### 8.2 缺陷分级与响应

| 等级 | 定义 | 响应时限 | 处理方式 |
|------|------|---------|---------|
| **P0 阻断** | 崩溃、数据错误、无法交互 | 立即 | 打断当前阶段，4 小时内修复 |
| **P1 高** | 视觉明显不一致、性能严重退化 | 当天 | 当阶段内修复 |
| **P2 中** | 轻微不一致、边缘场景 | 当日评估 | 本阶段末或转入 M7 |
| **P3 低** | 优化建议、微体验 | 记录不阻塞 | 归入 v1.1 backlog |

### 8.3 调整机制

- **允许微调**：色板偏移 ±10%、间距 ±4px、字号 ±1px（不违背字体级别）
- **需评审**：新增/移除组件、组件 API 变更、字体族变化
- **需重启阶段**：令牌层错误导致大面积回归（触发 M1 复盘）
- **拒绝变更**：涉及 `core/` 算法、AI 解读逻辑（超出本 UI 升级范围）

### 8.4 反馈日志模板（`docs/ui-defect-log.md`）

```
## DEF-YYYYMMDD-NN | 标题
- 发现时间：YYYY-MM-DD HH:MM
- 发现阶段：M? / Gate-?
- 严重度：P0 / P1 / P2 / P3
- 复现路径：...
- 期望表现 vs 实际表现：...
- 截图：screenshots/defects/def-*.png
- 处理方式：修复 / 归入 backlog / 拒绝
- 关闭条件：...
```

---

## 9. 风险登记册与应对

| ID | 风险 | 概率 | 影响 | 早期信号 | 应对 |
|----|------|------|------|---------|------|
| R1 | 图标版权/合规 | 低 | 中 | 下载源异常 | 只用 Apache 2.0 / MIT，`assets/icons/LICENSE.md` 记录来源 |
| R2 | 楷体跨平台 | 中 | 低 | Linux 截图异常 | `Noto Serif CJK SC` 回退写入 `Fonts.TITLE` |
| R3 | QSS `:focus-visible` 兼容 | 低 | 低 | Qt < 5.15 环境 | 项目锁 PySide6 ≥ 6.9，无兼容风险 |
| R4 | Matplotlib DPI 抖动 | 中 | 中 | 125/150% DPI 截图模糊 | `forward=True` + `tight_layout` + 测试 3 档 DPI |
| R5 | 大范围重构回归 | 中 | 高 | M3/M4 面板崩溃 | 每阶段独立 PR，可 `git revert --no-edit <merge-commit>` |
| R6 | `styles.py` 单点故障 | 低 | 高 | 令牌改动引起全 UI 变化 | 令牌改动必须走 D 签收 + 全 UI 回归 |
| R7 | 假期/人力中断 | 中 | 中 | 国庆 8 天 | 排期已避开；U 缺席启用 A 接手脚本任务 |
| R8 | U0 反馈延期 | 低 | 低 | M7 缓冲期未启动试用 | 内部自评替代，U0 试用移至 v1.1 |

---

## 10. 交付物清单

### 10.1 代码交付

- `ui/styles.py` v6.1（令牌冻结）
- `ui/animation.py`（新增）
- `ui/components/typography.py / list_item.py / badge.py / states.py / icon_button.py / data_card.py / icons.py`（7 个新增组件）
- `ui/components/ai_metrics_chart.py`（重写）
- `ui/components/*_input.py` × 4、`*_result_panel.py` × 4、弹窗 × 3（改造）
- `ui/main_window.py`、`collapsible_card.py`、`timeline.py`、`ai_analysis_renderer.py`（微调）
- `assets/icons/*.svg`（25 个）
- `scripts/audit_style_tokens.py / audit_contrast.py / download_icons.py / screenshot_regression.py`（新增）
- `tests/ui/`（补齐覆盖 ≥ 60%）

### 10.2 文档交付

- `docs/UI-Upgrade-Implementation-Plan.md` → 更新为 v1.1（回填最终决策）
- `docs/UI-Upgrade-Execution-Plan.md`（本文档，v1.0）
- `docs/design-tokens.md`（新增）
- `docs/component-guide.md`（新增）
- `docs/adr/`（新增，≥ 3 篇 ADR）
- `docs/ui-defect-log.md`（新增，缺陷闭环记录）
- `README.md` UI 章节更新

### 10.3 版本与分支

- 分支：`feat/ui-upgrade-v1`
- 版本：项目版本 `vX.Y.Z` → `vX.(Y+1).0-rc.1`（M7 结束） → `vX.(Y+1).0`（U0 试用签收后）
- Tag：每 Gate 打 `ui-upgrade/m<n>` tag

---

## 11. 启动前 Checklist（T-2 准备日）

**P 主导**

- [ ] 建立 `feat/ui-upgrade-v1` 分支，从 `main` 切出
- [ ] 确认 `main` 分支 CI 绿（`pytest` 全通过）
- [ ] 建立 `docs/adr/`、`docs/ui-defect-log.md`、`screenshots/baseline/` 目录
- [ ] 通知全部参与角色（P/D/U/A/U0）
- [ ] 建立每日站会（15 分钟，M1~M6 期间）
- [ ] 定义 Gate 验收表（`docs/gates.md`，Gate-1 ~ Gate-6）
- [ ] 备份当前 UI 截图作为基线（`screenshots/baseline/`）
- [ ] 冻结 `core/` 变更窗口（M1~M7 期间除紧急 bug 外禁止改动 core 层）

**U 主导**

- [ ] 环境自查：Python 版本、PySide6、Matplotlib 符合矩阵
- [ ] 下载图标测试一次（验证网络与授权）
- [ ] 阅读本实施推进计划 + UI 升级方案

**A 主导**

- [ ] 编写 `audit_style_tokens.py`、`audit_contrast.py` 骨架
- [ ] 记录基线性能数据（冷启动 / 内存 / 渲染耗时）
- [ ] 定义 10 项回归用例脚本

---

## 附：执行摘要（一页速览）

| 阶段 | 日期 | 关键动作 | Gate |
|------|------|---------|------|
| M0 | T-2 ~ T-1 | 环境/分支/基线 | 启动就绪 |
| M1 | D1 | 令牌冻结 + 图标 + 审计脚本 | Gate-1 令牌签收 |
| M2∥M3 | D2~D4 | 图表交互 + 排版落地（并行） | Gate-2 |
| M4 | D5~D6 | 列表 & 状态组件 | Gate-3 |
| M5 | D7~D8 | 图标/按钮/弹窗视觉一致 | Gate-4 |
| M6 | D9 | 动效 & AI 流式 | Gate-5 |
| M7 | D10~D11 | 回归、A11y、文档、签收 | Gate-6 交付 |

**核心承诺**：10 工作日并行 + 1 天缓冲；每阶段独立可回滚；设计令牌一次冻结、全项目跟随；U0 试用签收即 v1.0 发布。

---

**免责声明**：本文档为 UI/UX 层面推进计划，不涉及算法、AI 解读、数据存储等功能性变更。所有涉及命理学、风水学的展示内容仅供文化研究参考，不构成决策依据。涉及健康、法律、投资等重大事项，请咨询相关专业人士。
