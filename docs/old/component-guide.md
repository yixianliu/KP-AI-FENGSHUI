# 组件使用指南（Component Guide）

> 项目：KP-AI-FENGSHUI 风水排盘专业工具（PySide6 6.9.2，新中式玄中易设计系统 v6.1）
> 组件源：`ui/components/*.py`（22 个文件）
> 配套文档：`docs/design-tokens.md`（设计令牌体系：颜色 / 字号 / 间距 / 圆角 / 动效 / 阴影）

组件统一引用 `Colors` / `Fonts` / `Spacing` / `Shadows` / `EASING_*` / `DURATION_*` 令牌，禁止裸色值、裸字号、裸间距。新增组件请优先复用既有组件，避免自造轮子。

## 组件速查

| 组件 | 文件 | 基类 | 用途 |
| --- | --- | --- | --- |
| `TLabel` | `typography.py` | 工厂 | 统一 QLabel 工厂（7 级字号 + 4 级灰阶） |
| `ListItem` | `list_item.py` | `QFrame` | 统一列表项（图标 + 主标题 + 副标题 + 右值/徽章） |
| `Badge` | `badge.py` | `QLabel` | 语义色小标签（吉 / 凶 / 中 / 吉星 / 凶星） |
| `DataCard` | `data_card.py` | `QFrame` | 数值卡片（指标 + 数值 + 单位 + 可选徽章） |
| `CollapsibleCard` | `collapsible_card.py` | `QFrame` | 可折叠结果卡片（强调色条 + 图标 + 标题 + 内容） |
| `EmptyState` | `states.py` | `QWidget` | 空数据引导 |
| `LoadingState` | `states.py` | `QWidget` | 加载中（旋转太极 + 主文案 + 轮播提示） |
| `ErrorState` | `states.py` | `QWidget` | 错误 / 异常 + 重试按钮 |
| `IconButton` | `icon_button.py` | `QPushButton` | 图标按钮（QIcon + 固定尺寸 + tooltip + accessibleName） |
| `icons.icon()` | `icons.py` | 函数 | 统一 SVG 图标加载器（QIcon 缓存） |
| `Timeline` | `timeline.py` | `QWidget` | 大运流年时间轴（节点展开 / 筛选 / 键盘导航） |
| `ExportDialog` | `export_dialog.py` | `QDialog` | 导出对话框（格式 / 章节 / 文件名） |


## 文字标签（TLabel）

`ui/components/typography.py` —— 取代全 UI 层散落的 QLabel 硬编码字号 / 颜色，所有标签经 `TLabel` 工厂产出，强制 7 级 Font Scale + 4 级文字灰阶。

**规范**：
- 禁止直接 `QLabel(...).setStyleSheet('font-size: ...px')` 硬编码。
- 一律走 `TLabel.hero/h1/h2/h3/body/caption/micro/value`。
- 配套 `FONT_SCALE_QSS` 注入 objectName 选择器（`#t-hero` ~ `#t-value`），供全局集中样式管理，组件内不写死字号。

**级别规格**：

| 方法 | 字号 | 字族 | 字重 | 颜色 |
| --- | --- | --- | --- | --- |
| `TLabel.hero()` | 28px | TITLE（楷体） | BOLD | `TEXT` |
| `TLabel.h1()` | 20px | TITLE | SEMIBOLD | `TEXT` |
| `TLabel.h2()` | 17px | TITLE | SEMIBOLD | `TEXT` |
| `TLabel.h3()` | 15px | BODY（雅黑） | MEDIUM | `TEXT` |
| `TLabel.body()` | 13px | BODY | REGULAR | `TEXT2` |
| `TLabel.caption()` | 12px | BODY | REGULAR | `TEXT3` |
| `TLabel.micro()` | 11px | BODY | REGULAR | `TEXT4` |
| `TLabel.value()` | 13px | MONO（等宽） | SEMIBOLD | `BRAND` |

**用法**：

```python
from ui.components.typography import TLabel

# 每个方法返回已配置 objectName + 内联样式的 QLabel，可直接 addWidget
lay.addWidget(TLabel.hero("风水排盘"))
lay.addWidget(TLabel.body("正文内容…"))
lay.addWidget(TLabel.value("92.5"))
# 通用工厂
lay.addWidget(TLabel.of("辅助说明", level="caption"))
```


## 列表项（ListItem）

`ui/components/list_item.py` —— 统一「列表项」视觉语言：图标（可选）+ 主标题 + 副标题 + 右侧数值/状态徽章。
支持状态：default / hover / active / disabled。

**构造签名**：

```python
ListItem(icon='', title='', subtitle='', value='', badge_color=None, parent=None)
# icon:       左侧图标字符（emoji / 卦符 / SVG 名占位），空串不显示
# title:      主标题（FS_H3 15px SEMIBOLD）
# subtitle:   副标题（FS_CAPTION 12px TEXT3），可空
# value:      右侧数值/状态（FS_BODY 13px MONO），可空
# badge_color: value 颜色，None 取 Colors.BRAND
```

**状态**：`QFrame` 按 `property("state")` 区分四态，`STATES = ('default','hover','active','disabled')`。

| 状态 | 背景 | 边框 | 说明 |
| --- | --- | --- | --- |
| `default` | transparent | transparent | 默认 |
| `hover` | `HOVER` | `BORDER` | 鼠标进入 |
| `active` | `CARD_HOVER` | `BORDER` + 左侧 3px `BRAND` | 选中 / 高亮 |
| `disabled` | transparent | transparent + `TEXT4` 字 | 禁用 |

**API**：
- `item.clicked`：`Signal()`，左键点击发出。
- `set_state(state)`：切换状态（default/hover/active/disabled），触发重绘。
- `enterEvent` / `leaveEvent`：自动切 hover / 还原进入前基础态。

**用法**：

```python
item = ListItem(title='甲子', subtitle='大运', value='1990-1999', icon='☘')
item.clicked.connect(on_click)
item.set_state('active')
item.set_state('disabled')   # 同时 setEnabled(False) + 子 label 压 TEXT4
```

### 坑（子 QWidget 透明背景）

每个子 QLabel **必须**带 `background: transparent`——Qt 的实测坑：子 QLabel 若不显式声明透明背景，会盖住父 QFrame 的 QSS 背景，导致 `LIST_ITEM_QSS` 的四态背景**全部静默失效**（整份 QSS 等于没写）。
`_register()` 已统一自动补 `background: transparent;`，无需手动处理。

### 坑（QSS 动态属性）

Qt 的 dynamic property 变更后必须 `unpolish()` + `polish()` 配合 `style().unpolish/polish`，否则 QSS 的 `[state=...]` 选择器不会即时生效。`set_state` 已封装。

## 状态徽章（Badge）

`ui/components/badge.py` —— 语义色小标签（吉 / 凶 / 中 / 吉星 / 凶星 等）。
统一视觉语言：药丸圆角 + 语义色背景 + 自动前景色对比（WCAG AA 小字 ≥4.5:1）。

**构造签名**：

```python
Badge(text, semantic='info', parent=None)
# text:     徽章文字
# semantic: 语义色键，取值 success/danger/warning/info/brand/accent，默认 'info'
```

**语义色映射**（`_BADGE_COLORS`）：

| semantic | 背景 | 自动前景色 |
| --- | --- | --- |
| `success` | `SEMANTIC_SUCCESS` #5DAF74 | `TEXT_INV`（lum=0.63>0.5） |
| `danger` | `DANGER_DARK` #A03E32 | `TEXT`（lum=0.42<0.5） |
| `warning` | `SEMANTIC_WARNING` #D8A94E | `TEXT_INV`（lum=0.73>0.5） |
| `info` | `SEMANTIC_INFO` #7FB3C8 | `TEXT_INV`（lum=0.71>0.5） |
| `brand` | `BRAND` #c9a227 | `TEXT_INV`（lum=0.61>0.5） |
| `accent` | `ACCENT` #8b0000 | `TEXT`（lum=0.12<0.5） |

> `danger` 刻意用 `DANGER_DARK`（#A03E32）而非 `SEMANTIC_DANGER`（#C45545）——
> 徽章文字仅 FS_MICRO 11px，属 WCAG 小字，需 ≥4.5:1。#C45545 配浅字仅 3.94:1 不达 AA；
> DANGER_DARK 配浅字 5.80:1 达标。

**API**：
- `set_text(text)`：更新徽章文字（保留样式）。

**用法**：

```python
Badge('吉', semantic='success')
Badge('凶', semantic='danger')
Badge('平', semantic='info')
```

### 坑（foreground 自动推导）

`_contrast_fg` 按 ITU-R BT.709 感知亮度（`0.2126R+0.7152G+0.0722B`）判断：亮底（>0.5）配深字 `TEXT_INV`，暗底配浅字 `TEXT`。原实现曾只在 brand/accent 用 `TEXT_INV`、其余语义色直接取背景色 c——文字与背景同色，对比度 1:1，**文字完全不可见**。已修正。

## 数值卡片（DataCard）

`ui/components/data_card.py` —— 展示「指标 + 数值 + 单位 + 可选徽章 + 可选迷你趋势」的紧凑数据卡片，供各结果面板的统计 / 指标区复用。

**构造签名**：

```python
DataCard(title='', value='', unit='', badge='', badge_semantic='info', color=None, parent=None)
# title:        指标名称（FS_CAPTION 12px TEXT3）
# value:        主数值（FS_HERO 28px MONO 金色）
# unit:         单位（小字，紧跟数值，底对齐）
# badge:        可选状态徽章文字（如 '优'/'警'）
# badge_semantic: 徽章语义色键（success/danger/warning/info/brand/accent）
# color:        数值强调色，None 取 Colors.BRAND
```

**hover**：背景渐变 `CARD_HOVER`→`HOVER` + 边框 `BRAND_LIGHT`。

**API**：
- `set_value(value, unit='')`：动态更新数值（基于 `objectName == 'dc_value'`）。

**用法**：

```python
DataCard(title='命中率', value='92.5', unit='%', badge='优', badge_semantic='success', parent=self)
```

## 可折叠卡片（CollapsibleCard）

`ui/components/collapsible_card.py` —— 结果显示卡片，支持折叠 / 展开（默认展开）。
三套右侧结果面板（八字 / 梅花易数 / 大六壬）统一复用此组件，保证视觉一致：左侧强调色条 + 图标 + 标题 + 内容区。

**配色约定**（视觉层次）：
- 排盘类卡片：青色条（`Colors.QINGHUA` = `BRAND`）
- AI 解读类卡片：鎏金色条（`Colors.LIUJIN` = `BRAND`）
强调色由调用方通过 `accent_color` 传入，便于语义化区分。

**构造签名**：

```python
CollapsibleCard(title, icon='', parent=None, accent_color=None, collapsed=False)
# title:        卡片标题
# icon:         标题左侧图标字符（emoji 或卦符），空串不显示
# accent_color: 左侧强调色条颜色；None 取 Colors.QINGHUA
# collapsed:    初始是否折叠，默认 False（展开）
```

**API**：
- `toggle()`：切换折叠 / 展开。
- `set_collapsed(collapsed, animated=True)`：设置折叠状态；`animated=False` 初次构建无动画。
- `is_collapsed() -> bool`：返回当前是否折叠。
- `set_content(widget)`：设置卡片内容（首次 / 更新均安全，自动加分割线）。
- `clicked`：标题栏点击信号（已绑定 `toggle`）。

**折叠动画**：`maximumHeight` 属性，`DURATION_NORMAL`(300ms) + `EASING_STANDARD`(InOutCubic)。▼/▶ 箭头指示。

### P07 卡片 hover 双轨（必须双轨联动）

卡片 hover 反馈 = **背景渐变 + 边框变色**（QSS 管）+ **阴影变化**（`enterEvent` 切 `Shadows.CARD_HOVER`，QGraphicsDropShadowEffect 改参数）。

- **QSS 必须同时含 `background:` 与 `border-color:`**——原实现仅改 border-color，1px 边框在深色卡片底上几乎不可见，反馈严重不足。
- **阴影无法用 QSS**（Qt 不支持 box-shadow），须嵌 60px 边距父容器后抓父，`enter/leaveEvent` 切阴影。
- **`_apply_card_hover` 幂等短路**：单实例 `make_shadow(Shadows.CARD)`，hover 时 `apply_shadow(Shadows.CARD_HOVER, eff)` 改参数（`setColor`/`setOffset`/`setBlurRadius` 触发 `changed()`），**不产生新对象**，避开 `setGraphicsEffect(new)` 删旧 effect 的悬空指针坑。

**用法**：

```python
card = CollapsibleCard('八字命局', icon='☯', accent_color=Colors.QINGHUA)
card.set_content(我的结果 widget)
card.toggle()
card.set_collapsed(True, animated=False)
```


## 状态组件（EmptyState / LoadingState / ErrorState）

`ui/components/states.py` —— 替代各面板「自造轮子」的加载 / 空 / 错误实现，提供统一视觉语言的三个状态组件，供四结果面板与图表复用。

**规范**（对齐实施计划 4.2 / 步骤 2.4）：
- `EmptyState`：空数据引导（图标 + 标题 + 提示），禁止伪造数据
- `LoadingState`：加载中（复用 CollapsibleCard.LoadingPanel + 主文案 + 轮播提示）
- `ErrorState`：错误 / 异常（图标 + 标题 + 描述 + 重试按钮，retry 信号）

### EmptyState（空数据引导）

```python
EmptyState(title='暂无数据', hint='', icon='○', color=Colors.TEXT3, parent=None)
# 工厂：EmptyState.empty(title, hint, icon, parent)
```
图标 40px、标题 FS_H3 15px MEDIUM TEXT2、提示 FS_CAPTION 12px TEXT3（自动换行），垂直居中。

### LoadingState（加载中）

```python
LoadingState(message='正在加载…', sub='', color=Colors.LIUJIN, hints=None, parent=None)
# 工厂：LoadingState.of(message, color, hints, parent)
```
内部复用 `CollapsibleCard.LoadingPanel`（旋转太极 + 主文案 + 副标题 + 轮播提示语），保证与面板加载态视觉一致。`hints` 传轮播提示语列表。

### ErrorState（错误 / 异常）

```python
ErrorState(title='出错了', message='', retry_hint='重试', show_retry=True, color=Colors.DANGER, parent=None)
# 工厂：ErrorState.of(title, message, retry_hint, show_retry, parent)
```
- 图标 36px、标题 FS_H3 15px SEMIBOLD、描述 FS_CAPTION 12px TEXT2（自动换行）
- `retry = Signal()`：重试按钮点击发出，由调用方绑定重试逻辑
- `set_retry_enabled(enabled)`：启用 / 禁用重试按钮

## 图标按钮（IconButton）

`ui/components/icon_button.py` —— 统一图标按钮，替代侧边栏 / 工具栏裸 QPushButton。
图标经 `icons.icon()` 加载，支持 6 态（默认 / 悬停 / 按下 / 选中 / 禁用 / 焦点），强制 20×20（或 24×24）图标尺寸与 accessibleName（可访问性）。

```python
IconButton(icon_name='robot', tooltip='龙虎山大师兄解读', accessible='AI 深度解读',
           size=20, checkable=False, text='', parent=None)
# icon_name:  图标名（icons.icon 的 name）
# tooltip:    鼠标悬停提示
# accessible: 无障碍名称（默认取 tooltip）
# size:       图标尺寸档位（16/20/24/32/48），默认 20
# checkable:  是否可选中（导航类按钮 True）
# text:       可选文本（图标 + 文字同显）
```
**坑**：`:focus` 用 border 不用 outline（Qt QSS 不支持 outline，实测被静默忽略）；不能写 `:focus:not(:disabled)`（Qt QSS 不支持 `:not()`，整条规则失效）。

## 图标加载器（icons.icon）

`ui/components/icons.py` —— 全部图标统一走 `assets/icons/*.svg`，经 `icon(name, size)` 加载，QIcon 缓存，禁止各处裸构造 `QIcon(path)`。

**规范**：
- 目录：`assets/icons/{name}.svg`（kebab-case 小写短横线命名）
- 尺寸：仅 16 / 20 / 24 / 32 / 48 五档（其他值抛 `ValueError`）
- 路径：打包后走 `core.path_utils.get_resource_path`，源码走项目根
- 缺失：图标不存在时回退到内置 Unicode 字符 QIcon（不崩溃），并输出告警日志

```python
from ui.components.icons import icon as load_icon
qicon = load_icon('bazi', size=24, color=Colors.TEXT)
qicon = load_icon('export-pdf', size=32)
# 判断图标文件是否存在（走查 / 审计）
from ui.components.icons import has_icon
has_icon('bazi')  # -> True / False
```

### 坑（SVG currentColor 渲染为纯黑）

QPixmap 直接加载 SVG 时 `currentColor` 渲**纯黑**（深色底不可见），须走 `_load_svg_pixmap`：
- 先文本替换 `currentColor` → 目标色（默认 `#F5F1E8` = `Colors.TEXT`）
- 再 `QSvgRenderer` 渲染到 2x 画布（高分屏清晰），`Qt.KeepAspectRatio` + `Qt.SmoothTransformation`
- 缺 `QSvgRenderer` 时回退 `loadFromData` / 路径加载

**命名遮蔽**：四面板局部 `icon = QLabel(...)` 会遮蔽 import，一律 `from ui.components.icons import icon as load_icon`。

**验证**：`QIcon.isNull()=False` 会误判（空 QPixmap 也非 null），须 `QPixmap.toImage().pixelColor()` 采样，判色取 alpha 最大像素。

## 大运流年时间轴（Timeline）

`ui/components/timeline.py` —— 大运 / 流年时间轴组件，节点展开 / 流年筛选 / 键盘导航 / 悬浮增强。

**构造签名**（关键字段，详见源码）：大运节点列表 + 流年数据，节点可点击展开 / 收起详细分析；流年年份筛选输入框（支持范围 / 关键字）；当前大运期间高亮指示。

**配色约定**：
- 五行色：`WUXING_COLOR = {木: WOOD, 火: FIRE, 土: EARTH, 金: METAL, 水: WATER}`
- 关系吉凶徽章：`RELATION_STYLE`（三元组「标签, Badge 语义键, 图标」）

| 关系 | 标签 | Badge 语义 | 图标 |
| --- | --- | --- | --- |
| 克我 | 慎 | warning | ⚠ |
| 生我 / 比和 | 吉 | success | ✓ |
| 平 | 平 | info | ～ |

**交互**：
- 大运节点点击展开 / 收起（高度过渡动画，`DURATION_NORMAL` + `EASING_STANDARD`）
- 流年年份筛选输入框（支持范围 / 关键字）
- 当前大运期间高亮指示
- 键盘导航（上下键切换、回车展开）
- 悬浮态增强（阴影、放大、进度条动画，`DURATION_FAST` + `EASING_OUT`）
- 响应式布局适配窄宽度

**M4-T4 徽章标准化**：`_DayunRow` 关系徽章（吉 / 慎 / 平）改标准 `Badge`，`RELATION_STYLE` 由四元组改三元组（标签, 语义键, 图标）——有意视觉变更（浅底饱和字→饱和底自动对比字，圆角 `RADIUS_SM`→`RADIUS_PILL`），需用户视觉签核。


## 导出对话框（ExportDialog）

`ui/components/export_dialog.py` —— 导出排盘结果对话框：选择格式 / 章节与文件名，确认后发出导出信号。

**设计意图**：浅色国风主题（宣纸 - 墨褐 - 古金），模拟纸质报告，与深色主界面形成「编辑态 / 成品态」对比。**有意设计**（勿改为深色）；改视觉请改 `Colors.PAPER_*` 令牌值。

```python
ExportDialog(data, parent=None)
# data: 排盘结果数据（dict），用于推导默认文件名
# export_signal = Signal(str)：确认后发出（值 = 选中格式 csv/excel/pdf）
```

**章节**：模块级 `CHAPTERS`（基础信息 / 命局分析 / 运程 / AI 解读等），分组折叠卡片（`_ChapterGroup`）含章节勾选框，支持「全选 / 全不选」。

**格式卡片**：`_FormatCard(icon, title, desc, parent=None)` —— 图标 + 标题 + 说明，可勾选互斥；替代原 `QRadioButton`，保留 `setChecked` / `isChecked` 语义，使 `on_export` / `get_selected_format` 既有调用零变更。

**浅色主题令牌**（`Colors.PAPER_*` / `INK_PAPER_*` / `GOLD_PAPER_*`，详见 design-tokens.md）：宣纸底 `PAPER`、墨褐主色 `INK_PAPER`、古金描边 `GOLD_PAPER`。

## 通用约定（跨组件）

- **QLayout 显式 `setSpacing`**：每个 `QLayout` 创建后须显式 `setSpacing(Spacing.S*)`，不设继承 Qt 默认 6（非 8-4 体系）。
- **子 QWidget 透明背景**：在深色 `QFrame` 父容器内放 `QLabel` 等子控件，必须 `background: transparent`，否则盖住父 QSS 背景。
- **QSS 三条静默失效陷阱**：① 不支持 `outline`（焦点环用 `border`）；② 不支持 `:not()` 复合伪状态；③ 子 QWidget 未声明 `background: transparent` 会盖住父 QFrame QSS 背景。
- **QGraphicsDropShadowEffect 单实例**：hover 切换只改参数（`apply_shadow`），不新建 effect。
- **品牌化**：用户可见「AI」一律写作「龙虎山大师兄」。
- **组件引用令牌**：新组件一律 `from ui.styles import Colors, Fonts, Spacing`，动效 `from ui.animation import EASING_*, DURATION_*`，禁止裸值。

## 组件验收脚本（离屏采样）

| 脚本 | 说明 |
| --- | --- |
| `verify_badge_p07.py`（39） | Badge 前景色 + 四态 QSS + PDF_* 视觉验证 |
| `verify_list_item.py`（32） | ListItem 四态 QSS + 子 label 透明背景 |
| `verify_timeline_badge.py`（35） | Timeline 关系徽章标准化（M4-T4） |
| `verify_export_dialog_theme.py` | 导出对话框浅色主题 |
| `verify_offscreen_gui_e2e.py`（12） | 构建门禁 e2e |
| `verify_icons_svg.py`（3） | 图标 SVG 采样验证 |

采样方法：`:focus`/`:hover` 可激活（`setFocus()` / `sendEvent(QEnterEvent)` + `processEvents()`）；透明控件直接 `grab()` 得 `alpha=0`→`#000000` 伪影，须在父容器采样；背景取众数；阴影须嵌 60px 边距父容器后抓父。

## 迁移备注（有意设计，勿改）

- **M4-T4 徽章视觉变更**：`_DayunRow` 关系徽章由「浅底饱和字 + `RADIUS_SM`」改「饱和底自动对比字 + `RADIUS_PILL`」，已落地，**需用户视觉签核**。
- **export_dialog 浅色国风 / about_dialog 无边距沉浸 header**：保留视觉意图 ≠ 允许裸色值，已归位 `Colors` 令牌组（`PAPER_*` / `PDF_*` / 领域色）。

