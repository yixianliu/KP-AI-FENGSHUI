# KP-AI-FENGSHUI 界面 UI 升级方案

> 输出目标：本文件为**可直接解析执行的实施规格**。所有改造项均给出「涉及文件 + 行号/函数锚点 + 具体改动 + 验收标准」，AI 或开发者可按 §6 执行顺序逐条落地，无需二次澄清。
>
> 基线版本：v5.0.6（`core/app_version.py` 为唯一权威源）· 基线代码树：`ui/` 19,461 行 / `ui/main_window.py` 1,811 行
> 技术栈：PySide6 6.9.2 + Python 3.13（venv 3.13.5）· 桌面端深色国风主题
> 执行环境约定：所有命令在仓库根目录执行，UI 相关一律用 `./venv/Scripts/python.exe`，离屏加 `QT_QPA_PLATFORM=offscreen`

---

## 目录

1. [现状分析](#1-现状分析)
2. [问题清单](#2-问题清单)
3. [改进目标与度量](#3-改进目标与度量)
4. [设计基线（改造前必须先确立）](#4-设计基线改造前必须先确立)
5. [改造项（按模块拆分）](#5-改造项按模块拆分)
6. [实施优先级与执行顺序](#6-实施优先级与执行顺序)
7. [风险与回滚](#7-风险与回滚)
8. [附录：验收命令清单](#8-附录验收命令清单)

---

## 1. 现状分析

### 1.1 界面架构

#### 1.1.1 页面结构（单窗口 + 双栈同步路由）

```
MainWindow (QMainWindow)                     ui/main_window.py:51
├── 顶部导航栏 QFrame (固定 54px)             _create_navbar()  :504
│   ├── Logo 区（☯ + 「风水排盘」）
│   ├── 竖分隔线
│   ├── 导航按钮组 nav_btns（4 个 QPushButton，checkable）
│   ├── stretch
│   ├── ⚙ 设置按钮 → SettingsDialog
│   └── i  关于按钮 → AboutDialog
├── QSplitter(Qt.Horizontal)                  _init_ui()        :442
│   ├── [0] left_stack  QStackedWidget        min 360 / max 460
│   │   ├── 0 InputPanel          八字输入      ui/components/input_panel.py
│   │   ├── 1 MeihuaInputPanel    梅花输入
│   │   ├── 2 LiurenInputPanel    六壬输入
│   │   └── 3 XuanKongInputPanel  玄空输入
│   └── [1] right_stack QStackedWidget        min 460
│       ├── 0 ResultPanel          八字结果    1,907 行
│       ├── 1 MeihuaResultPanel    梅花结果    1,411 行
│       ├── 2 LiurenResultPanel    六壬结果    1,225 行
│       └── 3 XuanKongResultPanel  玄空结果      354 行
└── QStatusBar + 常驻版本标签                  :479-500
```

#### 1.1.2 路由机制

- 路由表 `NAV`（`ui/main_window.py:40`）：`bazi / meihua / liuren / xuan_kong`，每项 `{id, name, icon}`。
- 切换入口 `_switch(pid)`（`:681`）：硬编码索引映射 `idx = {'bazi':0,'meihua':1,'liuren':2,'xuan_kong':3}`，**同步**设置 `left_stack` / `right_stack` 的 `currentIndex`，按钮 `setChecked`，然后 `_fade_in_page()` 做 300ms 淡入。
- ⚠️ 现状缺陷：路由表与索引映射是**两处独立硬编码**（`NAV` 列表 + `idx` 字典），新增板块需改 3 处；`_restore_ui_settings()`（`:375`）的合法模块白名单只写了 `('bazi','meihua','liuren')`，**漏了 `xuan_kong`**，玄空板块的「记住上次板块」功能实际失效。

#### 1.1.3 组件层级

| 层 | 文件 | 职责 |
|---|---|---|
| 设计令牌 | `ui/styles.py`（1,153 行） | `Colors` / `Fonts` / `Spacing` / `Shadows` / `Stylesheets` / `apply_shadow()` |
| 排版工厂 | `ui/components/typography.py` | `TLabel.hero/h1/h2/h3/body/caption/micro/value` + `FONT_SCALE_QSS` |
| 容器组件 | `ui/components/collapsible_card.py`（2,569 行） | `CollapsibleCard` / `ResponsiveFlow` / `LoadingPanel` / `TaijiSpinner` |
| 内容块 | 同上 | `ai_section_header` / `ai_section_nav` / `hero_conclusion_block` / `conclusion_block` / `suggestion_block` / `rich_list_block` / `probability_stats_widget` / `disclaimer_card` / `highlight_label` / `risk_aware_label` |
| 状态组件 | `ui/components/states.py` | `EmptyState` / `LoadingState` / `ErrorState` |
| 展示组件 | `badge.py` / `data_card.py` / `list_item.py` / `icon_button.py` / `icons.py`（24 SVG） | 徽章 / 数值卡 / 列表项 / 图标按钮 / 图标 |
| AI 渲染 | `ui/components/ai_analysis_renderer.py`（449 行） | `render_analysis(pan_type, payload, target_layout)` —— 三面板共用 |
| 线程 | `ai_analysis_worker.py` / `bazi_calculation_worker.py` | AI 请求 / 排盘计算 |
| 对话框 | `about_dialog.py`(834) / `settings_dialog.py`(424) / `export_dialog.py`(534) | 关于 / AI 配置 / 导出 |
| 导出 | `ui/export/{base,csv,excel,pdf}_exporter.py` | CSV / Excel / PDF |

#### 1.1.4 状态管理

| 状态 | 存放位置 | 持久化 |
|---|---|---|
| 当前板块 `_current_module()` | `MainWindow` 运行时 | ✅ DB `ui_settings.current_module`（⚠️ 缺 xuan_kong） |
| 窗口几何 / 分栏比例 | `MainWindow` | ✅ DB `ui_settings`（`_save_ui_settings` `:341`，关窗非阻塞） |
| 排盘结果 | 面板实例 `self._current_result` | ❌ 不持久化 |
| AI 结果 | 面板实例 `self._data` | ✅ `core/knowledge/analysis_storage.py` |
| AI 配置 | `core/ai_config.py` | ✅ 订阅-通知（`_on_ai_config_changed` `:251`，热生效） |
| Worker 生命周期 | `self._workers`（`_register_worker` / `_cleanup_worker` / `_shutdown_workers`） | ❌ |
| 操作日志 | `self._session_id` + `_log_op()` | ✅ `system_logs` |
| 卡片折叠态 | 各 `CollapsibleCard` 实例 | ❌ 每次重渲染复位 |

**结论**：状态管理是「实例字段 + DB 少量持久化」，无集中 store。UI 升级**不重构状态模型**，仅在需要时补充字段（见 §5-M3-3 折叠态记忆）。

---

### 1.2 界面 UI/UX 现状

#### 1.2.1 视觉风格与配色

- **深色国风水墨**：`BG #1a1a2e`（深靛蓝）/ `CARD #21213a` / `TEXT #F5F1E8`（暖白）；品牌古金 `BRAND #c9a227`、朱红 `ACCENT #8b0000`。
- 语义色：`SUCCESS #5DAF74` / `WARNING #D8A94E` / `DANGER #C45545` / `INFO #7FB3C8`；五行五色 `WOOD/FIRE/EARTH/METAL/WATER` 已做深底可读性提亮。
- 另存**两套浅色子主题**：`PAPER_*`（导出对话框，模拟纸质报告）+ `PDF_*`（打印输出），属有意设计。
- ⚠️ 存在**浅色孤岛**：`hero_conclusion_block()`（`collapsible_card.py:2351`）背景用 `Colors.HIGHLIGHT_WARM_SOFT #FFF9E8` + `LIUJIN_GLOW`，文字用 `Colors.TEXT_INV #12121f`。它是深色结果流中唯一的高亮浅色块，与全局深色语言冲突，且字号 16px / 14px / **13.5px** 全部越出 Font Scale（7 级为 28/20/17/15/13/12/11）。

#### 1.2.2 间距与栅格

- 令牌 `Spacing.S0~S8 = 0/4/8/12/16/20/24/32/48`；`Fonts.FS_*` 7 级。
- ⚠️ **同一层级 padding 三套并存**：

| 位置 | 内容区边距 | 卡片间距 |
|---|---|---|
| `result_panel.py:84` | `(24, 20, 24, 20)` | `Spacing.S4`=16 |
| `meihua_result_panel.py:89/172` | 外框 20（`CARD_PADDING`），内容区 `(0,0,0,0)` | `Spacing.S4` |
| `liuren_result_panel.py:240/318` | 同上 | `Spacing.S4` |
| `about_dialog.py:85` | `(28, 24, 28, 24)` 裸数字 | `Spacing.S4` |

→ 切换板块时右侧内容**左右留白会跳变**（24px ↔ 0px），是本次升级必须消除的 P0 问题。

- ⚠️ `about_dialog.py:85` / `:114`(header 160px) / `:190`(24,16,24,16) 等处为**裸数字**，违反项目「间距必须走 `Spacing` 令牌」的不变量。
- ⚠️ 无栅格概念：`ResponsiveFlow`（`collapsible_card.py:511`）是唯一的响应式容器，按 `min_item_width` 自动算列数，但**调用点参数各不相同**（`min_item_width` 从 72 到 300，`spacing` 6/8/12/14），同一 UI 内网格节奏不统一。

#### 1.2.3 交互流程与反馈

| 流程 | 现状 | 问题 |
|---|---|---|
| 排盘 | 输入面板 submit → `MainWindow._on_*` → `_do_*` → `display_result()` | 结果面板顶部按钮（刷新/复制/导出/智能分析）初始 `setVisible(False)`，完成后才显示，**首屏无操作入口** |
| AI 分析 | 排盘完成 → `_trigger_*_auto_ai` → worker → `_on_*_ai_finished` → `display_ai_result()` | 进度仅靠 `status_lbl` 文本；加载态用 `TaijiSpinner` + 轮播提示 |
| 章节跳转 | `ai_section_nav()` 胶囊组（章节 ≥3 才显示）→ `register_anchor_scroller` → `_scroll_to_anchor_id` | 目录条**随内容滚动消失**，长报告回到顶部才能再导航 |
| 折叠 | `CollapsibleCard` 点击标题栏折叠，高度过渡动画 | 折叠态不记忆；`result_panel` 有「全部折叠」开关 `_toggle_collapse_all()`（`:179`） |
| 反馈 | 卡片 hover 双轨（QSS 背景渐变 + `enter/leaveEvent` 切阴影）、按钮点击微缩放、板块切换淡入、错误 `QMessageBox` | 反馈体系已较完整，但**键盘焦点环覆盖不全**（P17 只覆盖按钮类） |
| 导出 | 结果面板「导出」→ `ExportDialog`（章节勾选）→ CSV/Excel/PDF | 与本次排版升级解耦，不改 |

---

### 1.3 完整功能列表

| 编号 | 功能 | 入口 | 实现位置 |
|---|---|---|---|
| F1 | 八字排盘（四柱 / 五行 / 十神 / 神煞 / 地支关系 / 命局类型 / 运程） | 左栏 InputPanel | `core/bazi/*`、`result_panel.py` |
| F2 | 梅花易数起卦与解卦 | MeihuaInputPanel | `core/divination/meihua.py`、`meihua_result_panel.py` |
| F3 | 大六壬起课（天地盘 / 四课三传 / 天将神煞） | LiurenInputPanel | `core/divination/liuren.py`、`liuren_result_panel.py` |
| F4 | 玄空飞星（九宫飞星盘 / 山向 / 流年） | XuanKongInputPanel | `core/fengshui/xuan_kong.py`、`xuan_kong_result_panel.py` |
| F5 | 真太阳时校正 | 输入面板「真太阳时」区 | `core/calendar_utils.py SolarTimeCalculator` |
| F6 | 地点经纬度解析 + 地点库 | 输入面板地点输入 | `core/location_db.py` |
| F7 | 农历/公历互转 | — | `core/lunar_converter.py` |
| F8 | 龙虎山大师兄 AI 解读（三板块，自动触发 + 手动） | 结果面板「⚡智能分析」 | `ai_analysis_worker.py` + `ai_analysis_renderer.py` |
| F9 | AI 结果缓存 | 自动 | `core/ai_cache.py` |
| F10 | AI 模型配置（端点/密钥/模型/超时）热生效 | ⚙ 设置 | `settings_dialog.py` + `core/ai_config.py` |
| F11 | 导出 CSV / Excel / PDF（带章节勾选） | 结果面板「导出」 | `ui/export/*` + `export_dialog.py` |
| F12 | 排盘历史/记录落库 | 自动 | `_save_pan_record()` `:782` + `core/database_manager.py` |
| F13 | 界面配置持久化（几何/分栏/板块） | 自动 | `_save_ui_settings()` |
| F14 | 操作日志 + 会话追踪 | 自动 | `core/log_handler.py`、`_log_op()` |
| F15 | AI 指标图表 | AI 解读区 | `ai_metrics_chart.py`（matplotlib，真 DPI + resize 防抖） |
| F16 | 概率统计模块（含解读说明） | AI 解读区 | `probability_stats_widget()` |
| F17 | 关于 / 联系我 / 支付二维码 | ⓘ 关于 | `about_dialog.py` |
| F18 | 大运流年时间轴 | 八字结果 | `timeline.py` |
| F19 | 空 / 加载 / 错误三态 | 结果面板 | `states.py`（⚠️ 面板仍有自造实现未替换） |
| F20 | 设备标识 / 安全日志 / 构建安全检查 | 后台 | `core/device_identity.py`、`secure_log.py`、`scripts/verify_build_security.py` |

---

### 1.4 资产与打包现状（二维码改造的关键前提）

| 事实 | 证据 | 影响 |
|---|---|---|
| 二维码图片实际位置 | `images/link_qrcode/{qq.png 747×737, wx.png 1085×919}`、`images/pay_qrcode/{ali-pay.png 876×869, wx-pay.png 792×782}` | 资源已就位 |
| 代码读取路径 | `about_dialog.py:26` `QRCODE_DIR = Path(r'D:\PythonProject\qrcode')` | ❌ **硬编码绝对路径且目录不存在** → 支付二维码 100% 走失败分支，界面显示「未找到 wx-pay.png / ali-pay.png」 |
| 打包资源清单 | `KP-AI-FENGSHUI.spec:8` `datas=[('database','database'),('data','data'),(platforms),(icudtl.dat),('assets','assets')]` | ❌ **`images/` 未进 datas** → 即便修好路径，打包后仍丢失 |
| 资源定位工具 | `core/path_utils.py::get_resource_path(relative)` ✅ 已支持 `_MEIPASS` | 应改用它替代裸 `Path` |
| 「添加好友」二维码 | 代码中**无任何引用** | ❌ 待新增 |

---

## 2. 问题清单

> 严重度：**P0** 阻断 / 明显视觉错误，须本轮修复；**P1** 体验与一致性；**P2** 增强。

| ID | 严重度 | 问题 | 位置 |
|---|---|---|---|
| Q01 | P0 | 支付二维码路径硬编码到不存在的 `D:\PythonProject\qrcode`，功能实质失效 | `about_dialog.py:26,345` |
| Q02 | P0 | `images/` 未进 PyInstaller `datas`，打包后所有二维码丢失 | `KP-AI-FENGSHUI.spec:8` |
| Q03 | P0 | 右侧结果区三面板内容边距不一致（24px vs 0px），切板块时留白跳变 | `result_panel.py:84` vs `meihua:172`/`liuren:318` |
| Q04 | P0 | 「添加我好友」二维码缺失（微信 / QQ 图已备好但无入口） | `about_dialog.py` |
| Q05 | P1 | `hero_conclusion_block` 浅色纸底 + 深字，深色主题中的视觉孤岛；字号 16/14/13.5px 越出 Font Scale | `collapsible_card.py:2351,2456,2465` |
| Q06 | P1 | 关于对话框大量裸数字间距（`28,24,28,24` / `160` / `24,16,24,16`），违反间距令牌不变量 | `about_dialog.py:85,114,190,225` |
| Q07 | P1 | 关于对话框单列固定 480×520，二维码 `FIXED_SIZE=140` 硬尺寸，窄窗口下两栏挤压、无降级 | `about_dialog.py:50,771` |
| Q08 | P1 | 章节目录条（TOC）随内容滚出视野，长报告导航成本高 | `collapsible_card.py:790` |
| Q09 | P1 | 长文本段落无最大行宽约束；`line-height` 值散落（1.7 / 1.8 / 1.9 / `170%`），行高不统一 | `result_panel.py:1736,1784`；`collapsible_card.py:1649,2456` |
| Q10 | P1 | 无代码块渲染路径：AI 若返回含 ```` ``` ```` / 缩进 / 键值行的内容，会被当普通段落或逐字符列表渲染 | `ai_analysis_renderer.py::_as_text/_as_list` |
| Q11 | P1 | 列表项（`rich_list_block` / `_list`）条目间距仅 `S2=8`，条目多时视觉黏连；序号 `min-width:22px` 在长列表（>99 条）会挤字 | `collapsible_card.py:2517,2544`；`result_panel.py:1728` |
| Q12 | P1 | 无响应式断点：`setMinimumSize(1100,700)` 一刀切；左栏 min 360 在 <900px 窗口挤占右侧 | `main_window.py:63` |
| Q13 | P1 | 路由索引硬编码两处；`_restore_ui_settings` 白名单漏 `xuan_kong` | `main_window.py:691,404` |
| Q14 | P1 | 结果面板顶部操作按钮初始隐藏，首屏无可操作入口 | `result_panel.py:129,137,146,152` |
| Q15 | P1 | `SIDEBAR_WIDTH = 168` 为死常量（仅被 e2e 脚本断言引用），真实导航是顶部栏 | `main_window.py:48` |
| Q16 | P2 | 卡片折叠态不记忆，重渲染后复位 | `collapsible_card.py` |
| Q17 | P2 | `states.py` 的空/错误组件未被三结果面板全面替换（面板仍有 `_empty()` / `_show_error()` 自造实现） | `result_panel.py:187,1686` |
| Q18 | P2 | 关于对话框无「版本/环境」信息分区（Git commit 只以小字拼在版权行） | `about_dialog.py:354` |
| Q19 | P2 | 二维码无加载失败的可操作兜底（仅静态文字「未找到 xxx.png」） | `about_dialog.py:816` |

---

## 3. 改进目标与度量

### 3.1 目标

1. **统一**：全 UI 一套栅格、一套间距、一套字号层级；消除跨面板留白跳变。
2. **参考主流 AI 对话/工具类产品的左右分栏**：左＝输入与控制（收敛、稳定宽度、操作区贴底），右＝结果流（sticky 头部工具条 + 常驻目录导航 + 分区内容 + 高密度但不拥挤的正文排版）。
3. **可读**：右侧结果区建立「分区 → 卡片 → 标题 → 正文/列表/代码块」四级信息架构，长文本、列表、代码块各有明确呈现规格。
4. **可信**：关于板块重组成「项目 / 联系 / 好友 / 支持 / 版本」五个语义分区，二维码可加载、可缩放、可兜底。
5. **可适配**：≥1100 标准 / ≥1440 宽屏 / 900–1099 紧凑 / <900 单栏 四档断点；高 DPI（≥1.5）间距与字号整体放大。

### 3.2 量化指标

| 指标 | 现状 | 目标 | 度量方式 |
|---|---|---|---|
| 内容区左右边距一致性 | 24 / 0 / 0 / — | **全部 = `Spacing.S6`=24**（紧凑档 S5=20） | 离屏遍历 4 面板 `contentsMargins()` |
| 裸数字间距 | about_dialog 4 处 + 其余 | **0**（`audit_style_tokens.py` 新增检查项） | `scripts/audit_style_tokens.py` |
| Font Scale 越界字号 | 16/14/13.5px ≥3 处 | **0** | 新增 `scripts/audit_font_scale.py` |
| 二维码加载成功率 | 0%（路径错） | **100%**（源码 + 打包） | 离屏断言 `QPixmapLabel.pixmap().isNull()==False` |
| 长文本行宽 | 撑满（可达 900px+） | **正文最大 720px**，超出居中 | 离屏测 `QLabel.width()` |
| 冷启动 | 1163.5ms | **≤ 2000ms（不劣化）** | `scripts/measure_performance.py` |
| UI 渲染 | <200ms | **≤ 200ms** | 同上 |
| 内存（增量） | 归因增长 ~97MB | **ΔRSS ≤ 115MB（相对自身基线）** | 同上 |
| 回归 | 662 passed / 1 skipped | **不降低** | `pytest tests/` |
| 对比度 | — | **正文 ≥4.5:1（WCAG AA）** | `scripts/audit_contrast.py` |

---

## 4. 设计基线（改造前必须先确立）

### 4.1 栅格体系

以 **8px 为基准网格**，4px 为半格（沿用既有 `Spacing.S0~S8`）：

| 令牌 | 值 | 用途 |
|---|---|---|
| `S1`=4 | 图标↔文字、徽章内距 | 最紧 |
| `S2`=8 | 卡片内边距（紧）/ 条目间距 | |
| `S3`=12 | 控件间距 / 表单行距 | |
| `S4`=16 | **卡片间距（默认）** | |
| `S5`=20 | 卡片内边距（默认）/ 紧凑档页面边距 | |
| `S6`=24 | **页面内容区边距（默认）** | |
| `S7`=32 | 分区（Section）之间 | |
| `S8`=48 | 大分区 / 空状态上下留白 | |

**内容栅格**：右侧结果区正文列**最大宽度 720px**（≈ 45 个汉字 ×2 行宽经验值上限），超过则容器内居中；卡片区最大宽度 1080px。左侧表单列固定 360–460px。

### 4.2 间距规范（三档密度）

| 档位 | 页面边距 | 卡片间距 | 卡片内距 | 正文行高 |
|---|---|---|---|---|
| 紧凑（窗口 <1100 或高 DPI 小屏） | `S5`=20 | `S3`=12 | `S4`=16 | 1.6 |
| 标准（1100–1439） | `S6`=24 | `S4`=16 | `S5`=20 | 1.7 |
| 宽屏（≥1440） | `S7`=32 | `S4`=16 | `S5`=20 | 1.75 |

> Qt `QLabel` 的 QSS `line-height` 支持百分比/倍数；统一由新令牌 `Spacing.LINE_HEIGHT_BODY = 1.7` 提供，禁止再写裸 `1.7/1.8/1.9/170%`。

### 4.3 视觉层级（四级）

| 层级 | 字号 | 字重 | 颜色 | 用途 |
|---|---|---|---|---|
| L1 页面标题 | `FS_H1`=20 | `W_SEMIBOLD` | `TEXT` | 面板顶部「排盘结果」 |
| L2 分区标题 | `FS_H2`=17 | `W_SEMIBOLD` | `TEXT` | AI 区大标题、关于板块分区 |
| L3 卡片标题 | `FS_H3`=15 | `W_MEDIUM` | `TEXT` | `CollapsibleCard` 标题 |
| L4 正文 | `FS_BODY`=13 | `W_REGULAR` | `TEXT2` | 段落 / 列表项 |
| L5 辅助 | `FS_CAPTION`=12 | `W_REGULAR` | `TEXT3` | 说明 / 提示 |
| L6 元信息 | `FS_MICRO`=11 | `W_REGULAR` | `TEXT4` | 时间戳 / 版本 / 版权 |

**禁止**出现 14 / 16 / 13.5px。分隔靠**字号 + 字重 + 灰阶**三要素，不靠加边框。

### 4.4 响应式断点

| 断点 | 窗口宽度 | 布局策略 |
|---|---|---|
| `XS` | < 900 | **单栏**：splitter 切 `Qt.Vertical`（输入在上、结果在下）；左栏最小宽度降至 320 |
| `S` | 900–1099 | 双栏；左 320 / 右自适应；页面边距 `S5`；`ResponsiveFlow` 强制 1 列 |
| `M` | 1100–1439 | 双栏；左 360 / 右自适应；页面边距 `S6`（**当前默认**） |
| `L` | ≥ 1440 | 双栏；左 420（上限 460）；页面边距 `S7`；右侧内容最大宽度 1080 居中 |
| DPI | ≥ 1.5 | 所有 `Spacing` ×1.25、`FS` ×1.125（取整到偶数），走 `Spacing.scale()` / `Fonts.scale()` |

> 「移动端」在本桌面应用语境下 = **窄窗口 + 高 DPI + 触控**（平板/二合一设备）。不做独立移动端 UI，但须保证 `XS` 档可用：最小控件高度 ≥36px（现 `Spacing.CONTROL_H`=36 已满足），触控目标 ≥40px。

---

## 5. 改造项（按模块拆分）

---

### M1 · 设计令牌与排版基线

#### M1-1 扩展 `Spacing`：栅格、密度档、行高

- **目标**：为全局排版提供唯一间距/行高/密度真相源。
- **涉及文件**：`ui/styles.py`（`class Spacing`，约 :350-410）
- **改动**：
  1. 在 `Spacing` 内新增（**不改动既有 S0~S8 值**）：

```python
    # ===== 栅格与密度档（UI 升级 M1） =====
    GRID_UNIT = 8                 # 基准网格
    COL_MAX_TEXT = 720            # 正文列最大宽度（px）
    COL_MAX_CARD = 1080           # 卡片区最大宽度（px）

    # 密度档：(页面边距, 卡片间距, 卡片内距, 正文行高)
    DENSITY = {
        'compact': (20, 12, 16, 1.6),
        'normal':  (24, 16, 20, 1.7),
        'spacious':(32, 16, 20, 1.75),
    }
    LINE_HEIGHT_BODY = 1.7        # 正文统一行高（取代散落的 1.7/1.8/1.9/170%）
    LINE_HEIGHT_TITLE = 1.3

    # 响应式断点（窗口宽度 px）
    BP_XS = 900
    BP_S = 1100
    BP_L = 1440

    @staticmethod
    def density_for(width: int, dpi: float = 1.0) -> tuple:
        """按窗口宽度返回密度档元组；dpi>=1.5 时整体降为 compact 并放大字号由调用方处理。"""
        if width < Spacing.BP_S or dpi >= 1.5:
            return Spacing.DENSITY['compact']
        if width < Spacing.BP_L:
            return Spacing.DENSITY['normal']
        return Spacing.DENSITY['spacious']

    @staticmethod
    def scale(v: int, factor: float) -> int:
        """DPI 缩放：8px 网格对齐（结果取整到 4 的倍数）。"""
        return int(round(v * factor / 4.0)) * 4
```

  2. `Fonts` 新增 `FS_SCALE_FACTOR = 1.0`（由 `MainWindow._init_fonts()` 按 `devicePixelRatio` 写入：≥1.5 → 1.125），并加：

```python
    @staticmethod
    def px(size: int) -> int:
        """按 DPI 缩放因子返回实际 px（偶数对齐）。"""
        return int(round(size * Fonts.FS_SCALE_FACTOR / 2.0)) * 2
```

- **验收**：
  - `./venv/Scripts/python.exe -c "from ui.styles import Spacing; print(Spacing.density_for(1000), Spacing.density_for(1280), Spacing.density_for(1600))"` 输出 `(20,12,16,1.6) (24,16,20,1.7) (32,16,20,1.75)`。
  - `pytest tests/` 不降低（662 passed / 1 skipped）。

#### M1-2 新增字号审计脚本（Font Scale 门禁）

- **目标**：杜绝 14 / 16 / 13.5px 等越界字号再次出现。
- **涉及文件**：新建 `scripts/audit_font_scale.py`
- **改动**：扫描 `ui/**/*.py` 与 QSS 字符串中的 `font-size:\s*([0-9.]+)px`，白名单 = `{11,12,13,15,17,20,28}` + 已知豁免（`ui/export/pdf_exporter.py` 打印专用、脚本内 `40px/36px` 空状态图标）。命中非白名单 → 打印 `文件:行` 并 `sys.exit(1)`。
- **验收**：`./venv/Scripts/python.exe scripts/audit_font_scale.py` 在**改造完成后**退出码 0；改造前允许失败（先记录基线）。

#### M1-3 `TLabel` 补 `paragraph` / `code` 两个级别

- **目标**：长文本与代码块有统一排版出口。
- **涉及文件**：`ui/components/typography.py`
- **改动**：
  1. `_T_NAMES` 增加 `'para': 't-para'`、`'code': 't-code'`；`_SPECS` 增加：

```python
    'para':    (Fonts.FS_BODY,    Fonts.BODY,  Fonts.W_REGULAR,   Colors.TEXT2,
                {'line-height': Spacing.LINE_HEIGHT_BODY}),
    'code':    (Fonts.FS_CAPTION, Fonts.MONO,  Fonts.W_REGULAR,   Colors.TEXT2,
                {'line-height': Spacing.LINE_HEIGHT_BODY}),
```
  2. `TLabel.paragraph(text)` / `TLabel.code(text)` 两个静态方法（返回已设 `setWordWrap(True)` 的 QLabel；`code` 额外 `setTextInteractionFlags(Qt.TextSelectableByMouse)`）。
- **验收**：离屏构造 `TLabel.paragraph('测')`，断言 `objectName()=='t-para'` 且 `wordWrap()==True`。

---

### M2 · 主窗口骨架与响应式

#### M2-1 路由表单一真相源（修 Q13）

- **目标**：消除两处硬编码索引、修复玄空板块不被记忆。
- **涉及文件**：`ui/main_window.py:40`（`NAV`）、`:681`（`_switch`）、`:404`（`_restore_ui_settings`）、`:644/655`（`_build_left/_build_right`）
- **改动**：
  1. `NAV` 每项增加 `'index'` 字段（0..3），或直接新增模块级：

```python
NAV_INDEX = {item['id']: i for i, item in enumerate(NAV)}   # 放在 NAV 定义之后
VALID_MODULES = tuple(item['id'] for item in NAV)           # ('bazi','meihua','liuren','xuan_kong')
```
  2. `_switch()` 内 `idx = {...}` 替换为 `idx = NAV_INDEX`；`idx.get(pid, 0)` 保持不变。
  3. `_restore_ui_settings()` 的 `if mod in ('bazi','meihua','liuren'):` → `if mod in VALID_MODULES:`；末尾 `if mod != 'bazi'` → `if mod != NAV[0]['id']`。
- **验收**：
  - `grep -n "'bazi', 'meihua', 'liuren'" ui/main_window.py` 无结果。
  - 离屏：`_switch('xuan_kong')` 后 `left_stack.currentIndex()==3 and right_stack.currentIndex()==3`。

#### M2-2 响应式断点与 splitter 策略（修 Q12）

- **目标**：实现 §4.4 四档断点 + 高 DPI 缩放。
- **涉及文件**：`ui/main_window.py:48`（`SIDEBAR_WIDTH`）、`:63`（最小尺寸）、`:430-476`（`_init_ui`）、`:666`（`_apply_splitter_ratio`）
- **改动**：
  1. **删除** `SIDEBAR_WIDTH = 168`（Q15 死常量），同步修改 `scripts/verify_offscreen_gui_e2e.py:70,75` 改为断言 `NAV_INDEX` 与断点常量。
  2. `setMinimumSize(1100, 700)` → `setMinimumSize(900, 640)`，允许 `XS` 档。
  3. 新增方法：

```python
    def _current_density(self) -> tuple:
        """返回当前 (页面边距, 卡片间距, 卡片内距, 行高)。"""
        from PySide6.QtGui import QGuiApplication
        dpi = 1.0
        try:
            scr = QGuiApplication.primaryScreen()
            if scr:
                dpi = float(scr.devicePixelRatio() or 1.0)
        except Exception:
            pass
        return Spacing.density_for(self.width(), dpi)

    def _apply_responsive(self):
        """按断点设置 splitter 方向/尺寸与左栏宽度，并发 density_changed 信号。"""
        w = self.width()
        if w < Spacing.BP_XS:
            self.splitter.setOrientation(Qt.Vertical)
            self.left_stack.setMinimumWidth(320)
            self.left_stack.setMaximumWidth(16777215)   # 纵向模式解除上限
            self.right_stack.setMinimumWidth(320)
        else:
            self.splitter.setOrientation(Qt.Horizontal)
            self.left_stack.setMinimumWidth(360)
            self.left_stack.setMaximumWidth(460)
            self.right_stack.setMinimumWidth(460)
        self._apply_splitter_ratio()
        self.density_changed.emit(self._current_density())
```
  4. 新增信号 `density_changed = Signal(tuple)`；在 `__init__` 中 `QTimer.singleShot(0, self._apply_responsive)` 替代原 `QTimer.singleShot(0, self._apply_splitter_ratio)`。
  5. 重写 `resizeEvent`：宽度跨越断点时调用 `_apply_responsive()`（用 `self._last_bp` 缓存断点做短路，避免每次 resize 都重排）。
  6. `_apply_splitter_ratio()` 中比例常数提为 `SPLIT_LEFT_RATIO = 0.34`，纵向模式时按 0.4 分配高度。
- **验收**：
  - 离屏：`mw.resize(860,700); mw._apply_responsive()` → `mw.splitter.orientation()==Qt.Vertical`。
  - `mw.resize(1280,800)` → `orientation()==Qt.Horizontal` 且 `splitter.sizes()[0]` 在 [360,460]。
  - `scripts/verify_offscreen_gui_e2e.py` 12 项仍全 PASS（需同步改断言）。

#### M2-3 导航按钮视觉层级与键盘可达性

- **目标**：导航对齐 §4.3 层级（L5 字号 13px 现已是 `SZ_BODY`，保持不变），补齐焦点环。
- **涉及文件**：`ui/main_window.py:571-589`（nav 按钮 QSS）、`:602`、`:624`
- **改动**：三处 `QPushButton` QSS 各追加：

```css
QPushButton:focus { border: 2px solid {Colors.BRAND}; }
QPushButton:disabled { color: {Colors.TEXT4}; }
```
  （注意：`QSS 不支持 :not()`，且 `:disabled` 必须写在 `:hover`/`:checked` **之后**——见记忆中的 Qt QSS 陷阱。）
- **验收**：`scripts/verify_keyboard_focus.py` 13 项全 PASS 且新增「导航按钮聚焦有 2px 品牌色边框」断言。

---

### M3 · 右侧结果显示区：内容排版与信息架构

> 参考主流 AI 对话/工具产品的右栏范式：**Sticky 头部工具条 → 常驻目录导航 → 分区内容流 → 区块卡片 → 正文**。

#### M3-1 内容区边距与间距统一（修 Q03）

- **目标**：四面板右侧内容区边距完全一致，随密度档变化。
- **涉及文件**：
  - `ui/components/result_panel.py:84`（`self.clay.setContentsMargins(24,20,24,20)`）
  - `ui/components/meihua_result_panel.py:88-89, 171-173`
  - `ui/components/liuren_result_panel.py:239-240, 317-319`
  - `ui/components/xuan_kong_result_panel.py:203, 231, 242`
- **改动**：
  1. 在 `ui/styles.py` 新增模块级函数：

```python
def content_margins(density: tuple) -> tuple:
    """按密度档返回内容区 QLayout 边距 (l,t,r,b)。"""
    pad, _gap, _inner, _lh = density
    return (pad, pad, pad, pad)
```

```python
def apply_density(layout, density: tuple) -> None:
    """统一设置内容布局的边距与间距（唯一入口）。"""
    pad, gap, _inner, _lh = density
    layout.setContentsMargins(pad, pad, pad, pad)
    layout.setSpacing(gap)
```
  2. 四面板内容布局改为：

```python
from ui.styles import apply_density, DEFAULT_DENSITY
DEFAULT_DENSITY = Spacing.DENSITY['normal']
...
apply_density(self.clay, DEFAULT_DENSITY)              # result_panel
apply_density(self.content_layout, DEFAULT_DENSITY)    # meihua / liuren
apply_density(self.detail_layout, DEFAULT_DENSITY)     # xuan_kong
```
  3. **删除** meihua/liuren 外层 `main_layout` 的 `CARD_PADDING`（20px）边距，改为 `(0,0,0,0)` —— 只由 `apply_density` 一处控制，避免双层 padding 叠加。
  4. 四面板各实现 `on_density_changed(density)` 槽，由 `MainWindow.density_changed` 信号连接，内部 `apply_density(...)` 并 `layout.invalidate()`。
- **验收**：
  - 新增 `scripts/verify_panel_margin.py`：离屏构造 4 个结果面板，断言 `layout.contentsMargins() == (24,24,24,24)` 且 `layout.spacing() == 16`（标准档），四者**完全一致**。
  - 切板块后重测，值不变（无跳变）。
- **落地状态**（2026-09-29）：
  - **口径决议**：采用「根布局归 0 + 内容布局承载密度内边距」形态（与 bazi 既有形态一致）。bazi=`clay`、meihua/liuren=`content_layout` 均改为 `apply_density(DEFAULT_DENSITY)` → **(24,24,24,24)/16**；header 内边距沿用 Qt 默认 9px（与 bazi 同）。
  - **xuan_kong 暂不纳入**：其九宫格 `grid_canvas` 直挂根布局，改根归 0 会令九宫格贴边，需单独设计（待后续）。
  - **运行时回归断言**已落在 `scripts/verify_panel_layout.py`（检查项「M3-1 内容区边距统一」），`verify_panel_margin.py` 保持为源码裸数字扫描器。
  - 已知隐患：bazi/meihua/liuren 的 header 内边距为 Qt 默认 **9px**（非 8-4 网格令牌），如后续要求网格严格化需显式令牌化（含 bazi）。

#### M3-2 Sticky 头部工具条 + 常驻目录（修 Q08、Q14）

- **目标**：头部操作区常驻可见；章节目录不随内容滚走。
- **涉及文件**：`ui/components/result_panel.py:62-100`（`init_ui`）、`:102-178`（`_header`）、`ui/components/collapsible_card.py:790`（`ai_section_nav`）
- **改动**：
  1. 把 `_header_widget` 从 `self.clay`（可滚动内容区）**移出**到 `main` 布局，置于 `self.scroll` 之上：

```python
        main.addWidget(self._header_widget)      # 常驻，不随滚动
        main.addWidget(self.scroll, 1)
```
     （原 `self.clay.addWidget(self._header_widget)` 删除；注意 `_clear_content()` 中「从索引 1 开始删除」的逻辑需改为「删除全部」，见下方风险提示。）
  2. 头部按钮初始态改为：刷新 / 复制 / 导出 **常驻可见**（`setVisible(True)`），仅 `cancel_btn` 与 `smart_analyze_btn` 保持条件显隐；禁用态用 `setEnabled(False)` 而非隐藏（避免布局跳动）。
  3. `ai_section_nav()` 生成的目录条：在 `render_analysis()`（`ai_analysis_renderer.py:337`）中由「插入 root 布局」改为「插入一个 `QFrame`（objectName=`ai_toc_bar`），并置于 `ai_analysis_container` 的第 0 位」，同时把该 widget 引用注册到面板的 `self._toc_bar`，由面板在滚动时切换 `setVisible` 与「悬浮吸顶」样式（背景 `Colors.CARD` + `border-bottom` + 阴影）。
  4. 目录条长度 > 可视宽度时改为 `QScrollArea`（`horizontalScrollBarPolicy=Qt.ScrollBarAlwaysOff`，`setFixedHeight(44)`）。
- **验收**：
  - 离屏：`result_panel` 的 `main.itemAt(0).widget() is result_panel._header_widget` 为 True（头部在滚动区外）。
  - 滚动到内容底部后，`_header_widget.isVisible()` 与 `y()==0` 恒真。
  - 目录条 `objectName()=='ai_toc_bar'` 且滚动 2000px 后仍 `isVisible()`。

#### M3-3 分区（Section）与视觉层级（修 Q05 字号部分）

- **目标**：建立「分区 → 卡片 → 标题 → 内容」四级结构，统一行高。
- **涉及文件**：`ui/components/ai_analysis_renderer.py:241-257`（hero 区）、`ui/components/collapsible_card.py:600`（`ai_section_header`）、`:1945`（`ai_section_card_header`）
- **改动**：
  1. `ai_section_header()`：分区大标题改用 `TLabel.h1`（20px，`FS_H1`）或降级为 `TLabel.h2`（17px，**不得用 16px**）；副标题 `TLabel.caption`；时间戳 `TLabel.micro`。分区之间用 `Spacing.S7`=32 分隔（现 `root.setSpacing(Spacing.S4)` 在 `render_analysis():239` → 分区级改为 S7，卡片级保持 S4）。
  2. 所有 `line-height` 裸值（1.7/1.8/1.9/`170%`）替换为 `Spacing.LINE_HEIGHT_BODY`：
     - `result_panel.py:1736`（`1.7`）、`:1784`（`1.8`）
     - `collapsible_card.py:1649`（`1.8`）、`:2456`/`:2465`（`1.9`）
     - `about_dialog.py:214`（`170%`）
  3. `hero_conclusion_block()` 字号整改（修 Q05）：
     - 标题 `16px` → `Fonts.FS_H3`(15)；首段 `14px` → `Fonts.FS_BODY`(13) + `W_MEDIUM`；后续段 `13.5px` → `Fonts.FS_BODY`(13)。
     - **背景整改**（消除浅色孤岛）：背景由 `#FFF9E8` 渐变改为深色卡片语言 —— `qlineargradient(stop:0 {Colors.CARD_HOVER}, stop:1 {Colors.CARD})` + `border: 1.5px solid {Colors.LIUJIN_LIGHT}` + 左/右侧 3px 金色装饰线保留；文字 `Colors.TEXT_INV` → `Colors.TEXT`；副标题 `Colors.TEXT3`。
- **验收**：
  - `scripts/audit_font_scale.py` 退出码 0。
  - 离屏采样 hero 块背景众数 ≈ `Colors.CARD/CARD_HOVER`（非 `#FFF9E8`），正文文字色 = `Colors.TEXT`，对比度 ≥4.5:1（`scripts/audit_contrast.py`）。

#### M3-4 长文本、列表、代码块的呈现规格（修 Q09、Q10、Q11）

- **目标**：三类内容各有明确排版契约，长文可读、列表不黏连、代码块等宽可选中。
- **涉及文件**：`ui/components/collapsible_card.py`（`conclusion_block` :1611、`rich_list_block` :2487、`hero_conclusion_block` :2351）、`ui/components/result_panel.py`（`_list` :1714、`_paragraph` :1773）、`ui/components/ai_analysis_renderer.py`（`_as_text` :118 / `_as_list` :141）
- **改动**：

  **(a) 长文本**
  1. 新增 `ui/components/collapsible_card.py::paragraph_block(text, max_width=Spacing.COL_MAX_TEXT) -> QWidget`：
     - 按 `\n` 切段，每段一个 `TLabel.paragraph`；
     - 容器 `QVBoxLayout`，`setSpacing(Spacing.S3)`=12（段间距 > 行距，形成段落感）；
     - 用 `QHBoxLayout` 包一层并左右 `addStretch`，配合 `setMaximumWidth(max_width)` 实现**超宽居中**（用 `setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)` + 外层 `setAlignment(Qt.AlignHCenter)`）。
  2. `conclusion_block()` / `hero_conclusion_block()` 正文改调 `paragraph_block()`，删除内联 `line-height`。

  **(b) 列表**
  3. `rich_list_block()`：条目间距 `Spacing.S2`(8) → `Spacing.S3`(12)；序号宽度 `min-width:22px` → `min-width:26px`（容纳三位数）；序号字体 `Fonts.MONO`、`FS_CAPTION`；条目 >50 条时，仅渲染前 50 条 + 一个「展开剩余 N 条」`QPushButton`（点击后补齐），防止 UI 爆炸（现 `_as_list` 上限 200 条）。
  4. `result_panel._list()`：序号 badge 尺寸 20→24，字号 11→`FS_MICRO`，`min-width` 同步；行距改 `Spacing.LINE_HEIGHT_BODY`。
  5. 新增**有序/无序语义区分**：`rich_list_block(items, ordered=True/False)`，`ordered=False` 时用 `•` 圆点替代序号（用于并列的「建议」「提示」类）。调用点：`suggestion_block` 传 `ordered=True`，`folklore_tips` 传 `ordered=False`。

  **(c) 代码块**
  6. `ai_analysis_renderer.py` 新增：

```python
_CODE_FENCE_RE = re.compile(r'```[a-zA-Z0-9]*\n(.*?)```', re.S)

def _split_blocks(text: str) -> list:
    """把文本切成 [('p', 段落文本) | ('code', 代码文本)] 序列。

    识别 ``` 围栏；围栏外的文本按 \n 分段。无围栏时返回单段 ('p', text)。
    """
```
  7. 新增 `ui/components/collapsible_card.py::code_block(text, language='') -> QWidget`：
     - `QFrame`，背景 `Colors.BG_DARK`、`border: 1px solid Colors.BORDER`、`border-radius: Spacing.RADIUS_SM`、内距 `Spacing.S3`；
     - 内容 `TLabel.code(text)`（等宽 `Fonts.MONO`），`setTextInteractionFlags(Qt.TextSelectableByMouse)`，`setWordWrap(False)` 并外层包 `QScrollArea`（横向滚动条按需）；
     - 顶部一行 `language` 标签 + 「复制」`QPushButton`（写入剪贴板，`QApplication.clipboard()`），高度 24px，`FS_MICRO`。
  8. `render_analysis()` 的 `conclusion` / `conclusion_hero` / `list` 三种 mode 渲染前先过 `_split_blocks()`：命中 `code` 片段时插入 `code_block()`，其余走 `paragraph_block()` / `rich_list_block()`。
- **验收**：
  - 离屏喂入含 ```` ```python\nprint(1)\n``` ```` 的 payload，断言结果树中存在 `objectName()=='code_block'` 的 `QFrame`，且其 `findChild(QLabel,'t-code')` 非 None、`font()` 为等宽族。
  - 列表 60 条时渲染条目数为 50，点击「展开剩余」后为 60。
  - 文本宽度 1200px 时，正文 QLabel 的 `maximumWidth()==720`（或实际渲染宽度 ≤720）。

#### M3-5 折叠态记忆（修 Q16，P2）

- **目标**：用户折叠的卡片在重渲染后保持折叠。
- **涉及文件**：`ui/components/collapsible_card.py`（`CollapsibleCard`）、`ui/components/result_panel.py`（`_clear_content` :1574）
- **改动**：`CollapsibleCard` 增加 `persist_key: str = ''` 参数；类级字典 `_COLLAPSE_STATE: dict[str, bool]`（模块级，进程内有效）；`toggle()` 时写入，`__init__` 时读取覆盖 `collapsed`。`display_ai_result()` 生成卡片的调用点传入 `persist_key=f'{pan_type}:{key}'`。
- **验收**：离屏折叠某卡片 → 重新 `display_ai_result()` → 该卡片 `is_collapsed()==True`。

#### M3-6 三态组件替换（修 Q17，P2）

- **目标**：统一空/加载/错误视觉。
- **涉及文件**：`ui/components/result_panel.py:187`（`_empty`）、`:1686`（`_show_error`）、`meihua_result_panel.py`、`liuren_result_panel.py` 同名实现
- **改动**：内部实现改为委托 `ui/components/states.py` 的 `EmptyState` / `ErrorState`，保留对外方法签名（避免破坏 662 项测试）。`ErrorState.retry` 信号连到 `MainWindow._on_*_ai_analyze`。
- **验收**：`pytest tests/ui/` 全通过；离屏断言空状态树中存在 `EmptyState` 实例。

---

### M4 · 「关于」板块：内容组织与排版调优 + 二维码

#### M4-1 二维码资源定位修复（修 Q01、Q02）

- **目标**：源码与打包两种模式都能正确读到 4 张二维码。
- **涉及文件**：`ui/components/about_dialog.py:26`（`QRCODE_DIR`）、`:344-350`（`_qr_item` 内路径拼接）、`KP-AI-FENGSHUI.spec:8`
- **改动**：
  1. 删除 `QRCODE_DIR = Path(r'D:\PythonProject\qrcode')`，替换为：

```python
from core.path_utils import get_resource_path
...
    # 二维码资源（相对仓库根目录；打包后由 _MEIPASS 提供，见 core.path_utils）
    QR_FRIEND_DIR = 'images/link_qrcode'   # 添加好友：wx.png / qq.png
    QR_PAY_DIR    = 'images/pay_qrcode'    # 支付打赏：wx-pay.png / ali-pay.png
```
  2. 新增解析函数：

```python
    @classmethod
    def _resolve_qr(cls, sub_dir: str, filename: str):
        """按 打包(_MEIPASS) → 资源根 → 可执行文件同级 顺序解析二维码路径。

        Returns:
            (Path | None, str)：路径与失败原因（成功时原因为 ''）。
        """
        rel = f'{sub_dir}/{filename}'
        try:
            p = get_resource_path(rel)
            if p and p.exists():
                return p, ''
        except Exception:
            pass
        # 打包回退：exe 同级 images/
        try:
            from core.path_utils import get_app_dir
            p2 = get_app_dir() / sub_dir / filename
            if p2.exists():
                return p2, ''
        except Exception:
            pass
        return None, f'未找到 {filename}'
```
  3. `_qr_item()` 的路径拼接改为调用 `_resolve_qr(self.QR_PAY_DIR|self.QR_FRIEND_DIR, filename)`，并**优先从文件加载失败原因构造降级文案**（见 M4-4）。
  4. **打包**：`KP-AI-FENGSHUI.spec` 的 `datas` 增加 `('images', 'images')`；如 `scripts/build_release.py` 中有拷贝白名单，同步加入 `images/`。
- **验收**：
  - `./venv/Scripts/python.exe -c "from ui.components.about_dialog import AboutDialog as A; print(A._resolve_qr(A.QR_PAY_DIR,'wx-pay.png')[0])"` 打印出存在的绝对路径。
  - 离屏构造 `AboutDialog`，4 个 `QPixmapLabel` 的 `pixmap().isNull()` **全为 False**。
  - 打包后（`dist/` 内）`images/pay_qrcode/wx-pay.png` 与 `images/link_qrcode/wx.png` 均存在。

#### M4-2 「添加我好友」分区（修 Q04）

- **目标**：新增微信 / QQ 好友二维码展示区。
- **涉及文件**：`ui/components/about_dialog.py`（`_build_ui` :71、`_contacts_section` :221 之后新增）
- **改动**：
  1. 新增方法 `_friend_section() -> QFrame`，结构与 `_qrcode_section()` 一致，但：
     - 标题：`添加我好友`（`TLabel.h3` 居中，色 `Colors.QINGHUA_DARK`）；
     - 双栏：`_qr_item('微信好友', 'wx.png', Colors.SUCCESS, sub_dir=QR_FRIEND_DIR)`、`_qr_item('QQ 好友', 'qq.png', Colors.QINGHUA, sub_dir=QR_FRIEND_DIR)`；
     - 提示文案：`扫码添加好友，交流命理与使用问题 · 好友申请请备注「排盘」`（`TLabel.micro`，`Colors.TEXT3`，居中）。
  2. `_qr_item(self, label, filename, accent, sub_dir)` 增加 `sub_dir` 参数（默认 `QR_PAY_DIR` 保持向后兼容）。
  3. 在 `_build_ui()` 中的**插入顺序**（自上而下）：

```
Header（渐变 + 头像）
├─ 关于本项目        （intro_card）
├─ 联系我            （contacts：QQ / 手机）
├─ 添加我好友        （friend：微信 / QQ）   ← 新增
├─ 支持我们          （qrcode：微信支付 / 支付宝）
└─ 版权 + 版本信息   （footer）
```
     卡片入场动画的 `_cards` 列表与 `_STAGGER_DELAY`（80ms）基数按新顺序递增，**新增一张卡片后总时长增加 80ms（可接受，≤500ms）**。
  4. 支付区提示文案微调为：`扫码支持本项目开发 · 金额随意，感谢认可 🙏`。
- **验收**：离屏 `AboutDialog` 的卡片数为 4（介绍/联系/好友/支付）；好友区两个 `QPixmapLabel` 均成功加载（M4-1 验收项覆盖）。

#### M4-3 二维码展示尺寸、文案与响应式（修 Q07）

- **目标**：二维码清晰可扫、不挤压、随窗口缩放。
- **涉及文件**：`ui/components/about_dialog.py:771`（`QPixmapLabel.FIXED_SIZE`）、`:308-352`（`_qr_item`）、`:764-835`（`QPixmapLabel`）
- **改动**：
  1. **尺寸规格**（三档，随对话框宽度自适应）：

| 档 | 对话框宽度 | 二维码显示框 | 列数 |
|---|---|---|---|
| 紧凑 | < 520 | 132 × 132 | 2（保持并排，不换行） |
| 标准 | 520–679 | 160 × 160 | 2 |
| 宽屏 | ≥ 680 | 180 × 180 | 2 |

  2. `QPixmapLabel`：
     - `FIXED_SIZE = 140` → 实例属性 `self._size`（构造参数 `size: int = 160`）；
     - `setSize(size)` 方法：`setMinimumSize/setMaximumSize(size, size)` 并重新 `scaled()` 已缓存的 `self._raw_pixmap`（**必须保存原始 QPixmap**，否则反复缩放会累积失真）；
     - **白底留白（quiet zone）**：二维码外围加 `8px` 白色 `QFrame` 容器（`background: #FFFFFF; border-radius: 8px;`），保证扫码成功率 —— 深色主题下直接贴深色底会显著降低识别率；
     - 加载成功时 `setStyleSheet("")` 保留，但**不再清空白底容器样式**（容器与图片标签分离）。
  3. 缩放算法：`pixmap.scaled(QSize(size, size), Qt.KeepAspectRatio, Qt.SmoothTransformation)`（**注意**：不能传 `0, 0`，PySide6 6.9.2 会 TypeError）。原图非正方（如 1085×919），`KeepAspectRatio` 后居中，四周留白由白底容器吸收。
  4. `AboutDialog` 新增 `resizeEvent` / 或 `showEvent` 内按 `self.width()` 计算档位并调用各 `QPixmapLabel.setSize()`；`setMinimumSize(480, 520)` → `setMinimumSize(460, 560)`（容纳新增卡片，仍允许滚动：body 用 `QScrollArea` 包裹，见下）。
  5. body 内容区改包 `QScrollArea`（`widgetResizable=True`、`frameShape=NoFrame`、样式 `Stylesheets.SCROLL`），避免新增卡片后在小屏被裁切。
- **验收**：
  - 离屏 `dlg.resize(500,700)` → 二维码 label `minimumWidth()==132`；`dlg.resize(700,700)` → `==180`。
  - 采样二维码外框容器像素为纯白 `#FFFFFF`（`toImage().pixelColor()`）。
  - 对话内容全部可见（滚动区 `verticalScrollBar().maximum() >= 0` 且无控件 `height()==0`）。

#### M4-4 加载失败的兜底（修 Q19）

- **目标**：图片缺失时不出现「空洞 + 英文文件名」，给出可操作提示。
- **涉及文件**：`ui/components/about_dialog.py:816`（`setError`）、`:345-350`
- **改动**：
  1. `setError(text)` 的占位改为结构化降级：
     - 图标行：渠道专属 Unicode 占位（`微信 → 💬`、`QQ → 🐧`、`支付宝 → 🅰`），`font-size: 28px`，色 `self._accent`；
     - 主文案：`{渠道名}二维码暂未加载`（`FS_CAPTION`，`Colors.TEXT2`）；
     - 副文案：`请通过下方「{渠道}」联系方式添加`（`FS_MICRO`，`Colors.TEXT3`）—— 复用 `_contacts_section` 已有的 QQ 号 `1153602036` 与手机号 `19258585274`；
     - 保留 `2px dashed {accent}88` 边框与 `Spacing.RADIUS_SM` 圆角（现有设计保留）。
  2. `_resolve_qr()` 返回失败原因时写入 `self._logger.warning(...)`（若有 logger）便于排查，不弹窗（弹窗会阻塞且离屏测试 hang）。
  3. **显式文件名不再暴露给用户**：`未找到\nwx-pay.png` 这类文案全部移除。
- **验收**：临时把 `images/` 目录改名后离屏打开对话框 → 4 个占位区均显示中文降级文案、**无 `.png` 字样**、无异常抛出、对话框正常关闭。

#### M4-5 关于板块内容组织与间距令牌化（修 Q06、Q18）

- **目标**：五个语义分区 + 全部间距走 `Spacing` 令牌 + 版本信息独立成区。
- **涉及文件**：`ui/components/about_dialog.py:71-108`（`_build_ui`）、`:85`、`:114`、`:190`、`:225`、`:272`、`:354`（`_footer_text`）
- **改动**：
  1. 所有裸数字边距改为令牌：

| 现（行） | 现值 | 改为 |
|---|---|---|
| `:85` body_layout | `(28,24,28,24)` | `(Spacing.S6, Spacing.S5, Spacing.S6, Spacing.S5)` = (24,20,24,20) |
| `:114` header | `setFixedHeight(160)` | `setFixedHeight(Spacing.S8 * 2 + Spacing.S4)` = 112，或保留 160 但提为常量 `HEADER_H = 160` |
| `:190/:225/:272` card inner | `(24,16,24,16)` | `(Spacing.S6, Spacing.S4, Spacing.S6, Spacing.S4)` = (24,16,24,16) |
| `:135/:140/:175` addSpacing | `S7/S4/S6` | **删除**，改用 `clayout.setContentsMargins(Spacing.S6,0,Spacing.S6,0)` + `setAlignment(Qt.AlignCenter)`（消除手工撑居中的 hack） |

  2. 分区标题统一走 `TLabel.h3`（替代 4 处重复的 QSS 字符串），正文走 `TLabel.paragraph`，提示走 `TLabel.micro`。
  3. 新增 `_version_section()`（Q18）：把 `_footer_text()` 拆成两块——
     - 「版本信息」小卡：`版本号 v5.0.6` / `构建 (git short hash)` / `运行环境 Python 3.13 · PySide6 6.9.2`，三行 `TLabel.micro`，等宽显示版本号；
     - 「版权与声明」：底部居中小字（`_footer_text` 保留）。
  4. 分区顺序最终为：**关于本项目 → 联系我 → 添加我好友 → 支持我们 → 版本信息 → 版权声明**。
- **验收**：
  - `scripts/audit_style_tokens.py` 中 `about_dialog.py` 裸数字间距为 0（现有豁免仅保留 `#12B7F5` 品牌色）。
  - 离屏遍历对话框所有 `QLayout`，断言 `spacing()` ∈ `{0,4,8,12,16,20,24,32,48}`（无 -1 / 6）。
  - `scripts/verify_offscreen_gui_e2e.py` 全 PASS。

---

### M5 · 验证与门禁

#### M5-1 新增/更新验证脚本

| 脚本 | 作用 | 断言数 |
|---|---|---|
| `scripts/verify_panel_margin.py` | 四面板内容区边距/间距一致 | ≥4 |
| `scripts/verify_about_qrcode.py` | 4 张二维码加载成功 + 白底 + 尺寸三档 + 降级文案 | ≥12 |
| `scripts/verify_responsive_breakpoint.py` | XS/S/M/L 四档 splitter 方向与左栏宽度；高 DPI 密度降级 | ≥6 |
| `scripts/audit_font_scale.py` | 字号白名单门禁 | ≥1（退出码） |
| `scripts/verify_content_blocks.py` | 段落/列表/代码块三类呈现（行宽、段距、序号、等宽） | ≥8 |
| `scripts/audit_style_tokens.py` | 增量：间距裸数字 + `about_dialog` 归零 | 基线 609 → 覆盖新增项 |

- **验收**：全部脚本 `exit 0`；`pytest tests/` 仍为 662 passed / 1 skipped 或更高。

#### M5-2 性能与回归门禁

- **改动**：`scripts/measure_performance.py` 增加「关于对话框打开耗时」一项（阈值 ≤ 300ms，4 张 PNG 同步加载不得阻塞）。
- **演进**（2026-09-29）：内存判定从「绝对 RSS ≤ 150MB」改为「**增量 ΔRSS ≤ 115MB**」，根除同代码因 OS 基线 RSS 波动（44→60MB）导致 12↔9 PASS 的 flaky 现象；新增 `_record_memory()` 函数，`measure_memory(app, win, baseline_mb)` 接受基线参数。
- **当前状态**：12 项全 PASS；冷启动 ~1.5s、渲染 ~100ms、内存增量 ~97MB；`main_window` 覆盖率 74%、`result_panel` 73%。
- **验收**：`scripts/measure_performance.py` 12 项全部 PASS；`pytest tests/ui/` ≥ 316 passed（含新增覆盖测试）。

---

## 6. 实施优先级与执行顺序

### 优先级定义

| 级别 | 含义 |
|---|---|
| **P0-必做** | 功能失效或明显视觉错误，本轮必须完成 |
| **P1-应做** | 一致性 / 可读性，本轮完成 |
| **P2-可做** | 增强，时间允许再做 |

### 执行顺序（含依赖关系）

```
阶段 1（地基，无 UI 可见变化）
  M1-1  Spacing/Fonts 令牌扩展                 ├─ 被 M2/M3/M4 全部依赖
  M1-3  TLabel 增 paragraph/code               ├─ 被 M3-4 依赖
  M1-2  audit_font_scale.py（先跑出基线）       └─ 记录基线，最后再跑一次归零

阶段 2（修复失效功能 —— 最高 ROI）
  M4-1  二维码路径修复 + spec 加 images        ├─ 依赖 M1-1（无强依赖，可并行）
  M4-2  添加我好友分区                         ├─ 依赖 M4-1
  M4-3  二维码尺寸/白底/响应式                 ├─ 依赖 M4-2
  M4-4  加载失败兜底                           ├─ 依赖 M4-3
  → 阶段 2 完成即可交付「关于板块」成果

阶段 3（骨架响应式）
  M2-1  路由单一真相源 + xuan_kong 修复        ├─ 独立
  M2-2  断点 / splitter / 密度信号             ├─ 依赖 M1-1
  M2-3  导航焦点环                             └─ 独立

阶段 4（右侧结果区 —— 工作量最大的一块）
  M3-1  四面板边距统一 + 密度联动               ├─ 依赖 M1-1、M2-2
  M3-2  Sticky 头部 + 常驻目录                 ├─ 依赖 M3-1
  M3-3  分区层级 + 行高 + hero 整改            ├─ 依赖 M1-1、M1-3
  M3-4  长文本 / 列表 / 代码块规格              ├─ 依赖 M1-3、M3-3

阶段 5（增强）
  M3-5  折叠态记忆（P2）                       ├─ 依赖 M3-4
  M3-6  三态组件替换（P2）                     └─ 依赖 M3-4
  M4-5  关于板块令牌化 + 版本信息区（P1）      └─ 依赖 M1-1

阶段 6（门禁）
  M5-1  新增/更新验证脚本                      ├─ 依赖全部
  M5-2  性能与回归门禁                         └─ 依赖全部
```

### 建议分批交付

| 批次 | 内容 | 可独立验收 |
|---|---|---|
| 批次 A | M1-1、M1-2、M1-3、M4-1、M4-2、M4-3、M4-4 | ✅ 关于板块完整可用 |
| 批次 B | M2-1、M2-2、M2-3 | ✅ 响应式与路由 |
| 批次 C | M3-1、M3-2 | ✅ right panel 骨架 |
| 批次 D | M3-3、M3-4 | ✅ 内容排版 |
| 批次 E | M3-5、M3-6、M4-5、M5-1、M5-2 | ✅ 收口 |

> 每批次结束必须跑：`pytest tests/` + `scripts/verify_offscreen_gui_e2e.py` + `scripts/measure_performance.py`，任一失败不得进入下一批。

---

## 7. 风险与回滚

| 风险 | 触发点 | 防控 |
|---|---|---|
| **Sticky 头部移动破坏 `_clear_content()` 的「索引 1 起删」约定** | M3-2 | `self.clay` 不再含 header，必须把 `_clear_content()` 改为 `while self.clay.count(): takeAt(0)...`；同步检查 `result_panel.py:1586` 与 `meihua/liuren` 同名方法 |
| **删除 `SIDEBAR_WIDTH` 打断 e2e 断言** | M2-2 | 同批修改 `scripts/verify_offscreen_gui_e2e.py:70,75` |
| **双层 padding 叠加**（meihua/liuren 外框 20 + 内容区 24） | M3-1 | 外框必须置 0，只允许 `apply_density` 一处设置 |
| **QR 图非正方**（1085×919 等） | M4-3 | 必须 `KeepAspectRatio` + 白底容器吸收留白；禁止 `IgnoreAspectRatio` |
| **PyInstaller `images/` 未打包** | M4-1 | 改 spec 后必须重跑 `scripts/build_release.py` 并验证 `dist/` 内文件存在 |
| **QSS `:disabled` 顺序 / `:not()` 失效** | M2-3 | `:disabled` 写在 `:hover`/`:checked` 之后；禁用 `:not()` |
| **`setGraphicsEffect` 悬空指针** | 涉及阴影的改动 | 一律用 `ui/styles.py::apply_shadow(spec, eff)` 改参数，禁止换实例 |
| **AI 返回内容结构变化** | M3-4 | `_split_blocks()` 必须容错：围栏不匹配时整体按段落处理，绝不抛异常 |
| **冷启动劣化** | 全部 | 每批次跑 `measure_performance.py`；新增组件一律惰性 import |
| **回滚** | 任一阶段 | 每批次一个独立 commit；`git revert` 单批次即可，无跨批次耦合（M1 令牌为纯新增，删除不影响既有值） |

---

## 8. 附录：验收命令清单

```bash
# 环境
cd /d/PythonProject/KP-AI-FENGSHUI
PY=./venv/Scripts/python.exe

# 1) 全量回归（基线：662 passed / 1 skipped）
QT_QPA_PLATFORM=offscreen $PY -m pytest tests/ -q

# 2) 离屏 e2e 门禁
QT_QPA_PLATFORM=offscreen $PY scripts/verify_offscreen_gui_e2e.py

# 3) 性能门禁（冷启动 ≤2000ms / 渲染 ≤200ms / 内存增量 ΔRSS ≤115MB，免疫 OS 基线漂移）
$PY scripts/measure_performance.py

# 4) 设计令牌审计（间距裸数字）
$PY scripts/audit_style_tokens.py

# 5) 字号门禁（本轮新增）
$PY scripts/audit_font_scale.py

# 6) 对比度（WCAG AA ≥4.5:1）
$PY scripts/audit_contrast.py

# 7) 本轮新增验证
QT_QPA_PLATFORM=offscreen $PY scripts/verify_panel_margin.py
QT_QPA_PLATFORM=offscreen $PY scripts/verify_about_qrcode.py
QT_QPA_PLATFORM=offscreen $PY scripts/verify_responsive_breakpoint.py
QT_QPA_PLATFORM=offscreen $PY scripts/verify_content_blocks.py

# 8) 打包（验证 images/ 已进 dist）
$PY scripts/build_release.py
ls dist/KP-AI-FENGSHUI/_internal/images/link_qrcode/ 2>/dev/null || ls dist/*/images/link_qrcode/
$PY scripts/verify_build_security.py
```

**冒烟手测清单（人工，离屏脚本无法覆盖）**

1. 关于对话框：4 张二维码（微信好友 / QQ 好友 / 微信支付 / 支付宝）均清晰可扫（用手机实扫验证）。
2. 拖动窗口宽度跨越 900 / 1100 / 1440，右侧留白与卡片列数平滑切换，无控件重叠或空白断裂。
3. 高 DPI（150% 缩放）下字号与间距放大后无截断。
4. 八字板块 AI 解读：滚动到中部时顶部工具条仍可见、目录条仍悬浮可见，点击目录跳转正确。
5. 结果区切到梅花 / 大六壬 / 玄空，左右留白与八字板块**完全一致**（无跳变）。
6. 断开网络触发 AI 失败：错误态走统一 `ErrorState`，「重试」按钮可用，无模态卡死。
