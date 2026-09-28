# KP-AI-FENGSHUI UI 精细化打磨与一致性升级 · 实施方案

> 版本：v1.0
> 编制日期：2026-09-24
> 适用技术栈：PySide6 (Qt 6.9 ~ 6.11) + QSS + QPainter + Matplotlib(QtAgg)
> 参考基线：`docs/old/ui_upgrade_plan.md` v1.0（已归档）、`ui/styles.py` v6.0
> 目标：将现有"可用但不精致"的国风命理学工具升级为"专业级、可交付、可复用的设计系统"

---

## 目录（TOC）

1. [项目现状分析](#1-项目现状分析)
2. [升级目标设定](#2-升级目标设定)
3. [具体实施步骤](#3-具体实施步骤)
4. [技术规范](#4-技术规范)
5. [资源需求](#5-资源需求)
6. [开发排期与里程碑](#6-开发排期与里程碑)
7. [质量验收标准](#7-质量验收标准)
8. [附录：修改清单速查表](#8-附录修改清单速查表)

---

## 1. 项目现状分析

### 1.1 代码结构与 UI 架构总览

```
KP-AI-FENGSHUI/
├── core/                       # 计算核心（禁止修改）
├── service/                    # 业务编排
├── ui/
│   ├── main_window.py          # 主窗口 & 侧边栏导航
│   ├── styles.py               # 全局设计系统（Colors/Fonts/Spacing/Stylesheets/Shadows）
│   ├── components/             # UI 组件库
│   │   ├── input_panel.py      # 八字输入
│   │   ├── meihua_input.py     # 梅花输入
│   │   ├── liuren_input.py     # 大六壬输入
│   │   ├── xuan_kong_input.py  # 玄空输入
│   │   ├── result_panel.py     # 八字结果
│   │   ├── meihua_result_panel.py
│   │   ├── liuren_result_panel.py
│   │   ├── xuan_kong_result_panel.py
│   │   ├── collapsible_card.py # 通用折叠卡片 + TaijiSpinner + loading_panel
│   │   ├── ai_analysis_renderer.py
│   │   ├── ai_metrics_chart.py # Matplotlib 图表
│   │   ├── timeline.py         # 流运时间轴
│   │   ├── settings_dialog.py
│   │   ├── export_dialog.py
│   │   └── about_dialog.py
│   └── export/                 # CSV / Excel / PDF 导出
├── assets/                     # 图标、favicon
└── docs/
```

- **导航方式**：`main_window.py` 已改造为 **168px 竖排侧边栏 + QSplitter 左右分栏**（`SIDEBAR_WIDTH = 168`），四模块（八字 / 梅花 / 大六壬 / 玄空）通过 `QStackedWidget` 切换。
- **设计系统**：`ui/styles.py` v6.0 已定义 `Colors / Fonts / Spacing / Shadows / Stylesheets`，主色 `#1a1a2e`（深靛蓝）+ `#c9a227`（古金）+ `#8b0000`（朱红）。
- **图表**：仅 `ai_metrics_chart.py` 使用 Matplotlib + `QtAgg` 后端，双轴展示命中率与熔断次数。

### 1.2 现存痛点清单

| # | 分类 | 痛点描述 | 严重度 | 涉及文件 |
|---|------|---------|--------|----------|
| P01 | 图表 | `AIMetricsChart` 硬编码 `figsize=(8,6), dpi=100`，不随窗口缩放；无悬停 tooltip / hover 高亮 / 动画过渡 | 高 | `ui/components/ai_metrics_chart.py` |
| P02 | 图表 | 图表背景色 `#22223b` 与全局 `Colors.CARD = #21213a` 存在色差；未走 `Colors` 常量 | 中 | 同上 |
| P03 | 排版 | `Fonts` 已定义 6 级字号（20/17/15/13/12/11），但实际使用存在硬编码 `14px / 16px / 18px` 的散点 | 高 | 全 UI 层 |
| P04 | 排版 | `Spacing.LINE_HEIGHT = '1.6'` 仅定义未被强制使用；部分标签 `QLabel` 未设置行高 | 中 | 全 UI 层 |
| P05 | 排版 | 各输入面板 `setContentsMargins(24, 20, 24, 20)` / `setSpacing(16)` 各自手写，与 `Spacing.PAD/GAP` 常量脱钩 | 中 | `input_panel.py` 等 |
| P06 | 列表 | 四个结果面板（八字/梅花/六壬/玄空）均基于 `CollapsibleCard`，但内嵌列表项（如大运柱、流年、星宿）使用不同的 `QVBoxLayout` 间距（10/12/14/16 混用） | 高 | `result_panel.py`、`xuan_kong_result_panel.py` 等 |
| P07 | 交互 | 列表项无统一 hover 反馈；`CollapsibleCard` 卡片仅"边框变色"，无背景/阴影变化 | 中 | `collapsible_card.py` |
| P08 | 交互 | 按钮状态（默认/悬停/按下/禁用）在 4 类按钮（PRIMARY / SECONDARY / SWITCH / ICON）中不完全一致，缺失 `:checked`、`:pressed` 反馈差异 | 中 | `styles.py` |
| P09 | 视觉 | 色彩体系存在同义命名冗余：`QINGHUA`/`LIUJIN` 完全同值、`SUCCESS`/`YU` 同义、`WARNING`/`SHANHU` 同义，未做别名收敛 | 低 | `styles.py` |
| P10 | 图标 | 侧边栏图标使用 Unicode 字符（`☯ ⚊ ☵ ⛰`），无统一尺寸/线宽；`NAVBAR_ICON_BUTTON` 未强制图标 20×20 | 中 | `main_window.py` |
| P11 | 图标 | 结果面板头部混用 emoji（🤖📋📤⚙）与纯文本；深色底 emoji 显示质量差（Windows Segoe UI Emoji 渲染） | 中 | `result_panel.py` |
| P12 | 图表 | 无响应式重绘：窗口 resize 时 `FigureCanvasQTAgg` 无 `resizeEvent` 处理，导致 DPI 抖动 | 高 | `ai_metrics_chart.py` |
| P13 | 图表 | 无空数据引导（`generate_demo_data` 直接伪造数据展示，误导用户） | 中 | 同上 |
| P14 | 组件 | `QDialog`（设置 / 导出 / 关于）标题栏、关闭按钮样式与主体风格割裂 | 中 | `settings_dialog.py`、`export_dialog.py`、`about_dialog.py` |
| P15 | 组件 | 缺少统一 `EmptyState` / `LoadingState` / `ErrorState` 组件封装，各面板各自实现 | 中 | 四个结果面板 |
| P16 | 可访问性 | 颜色对比度未系统性校验（如 `TEXT3 #9C97A8` on `CARD #21213a` 约 4.6:1，接近 AA 边界） | 中 | 全 UI 层 |
| P17 | 可访问性 | 无 `QAccessible` 描述、无键盘焦点样式（`:focus` 除 INPUT/COMBO 外缺失） | 中 | 全 UI 层 |
| P18 | 动效 | `CollapsibleCard` 高度动画使用默认 `QEasingCurve.Linear`；按钮、卡片、AI 输出均无统一缓动 | 低 | `collapsible_card.py` |
| P19 | 导出 | 导出对话框（`export_dialog.py`）与主题割裂，缺少 `QDialog` 全局样式定义 | 中 | `export_dialog.py` |
| P20 | 一致性 | `xuan_kong_result_panel.py` 的 `_CELL_COLORS` / `_WUXING_COLORS` 硬编码色值，未从 `Colors` 常量派生，导致未来调色需双改 | 中 | `xuan_kong_result_panel.py` |

### 1.3 系统性根因

1. **样式散落**：`Colors`/`Fonts`/`Spacing` 常量体系已建立，但**引用不彻底**，存在硬编码色值、字号、间距。
2. **组件未复用**：`EmptyState` / `LoadingState` / `ErrorState` / `IconButton` / `DataCard` 等基础组件缺失，导致每个面板"自造轮子"。
3. **图表技术债**：Matplotlib 集成未做 DPI 自适应、主题映射、交互事件桥接。
4. **状态机不完整**：控件的 `default/hover/pressed/checked/disabled/focus` 六态未在 styles.py 中系统性定义。

---

## 2. 升级目标设定

### 2.1 视觉目标

| 维度 | 现状 | 目标 |
|------|------|------|
| 主色一致性 | ~70% 走常量 | 100% 走 `Colors`/`Fonts`/`Spacing` |
| 字号层级 | 6 级 + 硬编码散点 | 严格 6 级 Font Scale |
| 间距体系 | 混用 10/12/14/16 | 8-4 基准体系（4 / 8 / 12 / 16 / 20 / 24 / 32） |
| 图标体系 | Unicode + emoji 混用 | 单一图标源（QIcon + `assets/icons/*.svg`） |
| 交互反馈 | 边框变色为主 | 背景 + 阴影 + 边框 + 颜色 四通道联动 |
| 图表可读性 | 静态图、无交互 | 悬停 tooltip、动画过渡、响应式重绘 |
| 深色对比度 | 部分 AA 边界 | 全局 WCAG AA（正文 ≥ 4.5:1，大字 ≥ 3:1） |

### 2.2 体验目标

- **一致性**：进入任何板块（八字 / 梅花 / 六壬 / 玄空），第一眼看到"同一个 App"。
- **可预期**：鼠标 hover 一律有视觉响应；点击一律有 pressed 反馈；无效操作一律有 disabled 提示。
- **可学习**：所有控件状态映射符合"Material Design 3 + 新中式"混合语义。
- **可维护**：改一处色值 / 字号，全项目自动跟随。

### 2.3 非目标（本轮不做）

- 不引入新 GUI 框架（继续 PySide6，不换 CustomTkinter/PyQt6）。
- 不改造 core 层任何算法。
- 不做明/暗主题切换（保持深色单一主题）。
- 不做国际化（保持中文）。
- 不引入商业付费图标库（仅使用 MIT/Apache 授权或 Unicode）。

---

## 3. 具体实施步骤

按依赖顺序拆分为 **7 个阶段**，每阶段可独立合并、独立回滚。

### 阶段 1：设计令牌（Design Tokens）收敛 —— 基础层

**目标**：让 `styles.py` 成为唯一"真相源"，消除同义命名与硬编码。

#### 步骤 1.1 收敛同义色彩

在 `ui/styles.py` 中，将 `QINGHUA`、`LIUJIN`、`SUCCESS`、`YU`、`WARNING`、`SHANHU` 等重复定义合并：

```python
# ui/styles.py
class Colors:
    # ===== 主色 =====
    INK = '#1a1a2e'
    GOLD = '#c9a227'
    ZHUSHA = '#8b0000'

    # ===== 语义化色彩（唯一权威命名） =====
    BRAND = GOLD                     # 品牌金（导航、选中、强调）
    BRAND_LIGHT = '#e8d08a'
    BRAND_DARK = '#8f751c'
    BRAND_GLOW = 'rgba(201, 162, 39, 0.22)'

    ACCENT = ZHUSHA                  # 主操作朱红
    ACCENT_LIGHT = '#C97A6A'
    ACCENT_DARK = '#5E0000'
    ACCENT_GLOW = 'rgba(139, 0, 0, 0.25)'

    # ===== 语义色（成功/警告/危险/信息） =====
    SEMANTIC_SUCCESS = '#5DAF74'
    SEMANTIC_WARNING = '#D8A94E'
    SEMANTIC_DANGER = '#C45545'
    SEMANTIC_INFO = '#7FB3C8'

    # ===== 兼容别名（保留，逐步下线） =====
    QINGHUA = BRAND
    LIUJIN = BRAND
    YU = SEMANTIC_SUCCESS
    SHANHU = SEMANTIC_WARNING
    SUCCESS = SEMANTIC_SUCCESS
    WARNING = SEMANTIC_WARNING
    DANGER = SEMANTIC_DANGER
    INFO = SEMANTIC_INFO
```

#### 步骤 1.2 建立 8-4 间距基准

替换 `Spacing` 类：

```python
class Spacing:
    # 8-4 基准体系
    S0 = 0
    S1 = 4     # 图标-文字
    S2 = 8     # 内边距紧
    S3 = 12    # 控件间距
    S4 = 16    # 常规间距
    S5 = 20    # 卡片内边距
    S6 = 24    # 面板内边距
    S7 = 32    # 板块间距
    S8 = 48    # 大分区

    # 圆角（对齐 4 的倍数，符合触控友好）
    RADIUS_XS = 4
    RADIUS_SM = 6
    RADIUS = 10
    RADIUS_LG = 14
    RADIUS_XL = 18
    RADIUS_PILL = 999

    # 间距别名（QLayout spacing 使用）
    GAP_XS = S1
    GAP_SM = S2
    GAP = S4
    GAP_LG = S6
    GAP_XL = S7

    # 内边距别名
    PAD_SM = S2
    PAD = S5
    PAD_LG = S6
    PAD_XL = S7

    # 行高 / 字距
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT = 1.6
    LINE_HEIGHT_LOOSE = 1.75
    LETTER_SPACING = 0.5   # px

    # 控件最小尺寸
    CONTROL_H_SM = 28
    CONTROL_H = 36
    CONTROL_H_LG = 44
    BUTTON_H = 40
    BUTTON_W_MIN = 100
```

#### 步骤 1.3 Font Scale 强化

```python
class Fonts:
    # 字族
    TITLE = '"KaiTi", "SimSun", "STKaiti", "Noto Serif CJK SC", serif'
    BODY = '"Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif'
    MONO = '"Cascadia Code", "Consolas", "SF Mono", monospace'

    # 字号（px，Windows 逻辑像素；DPI 由 QApplication 自动处理）
    FS_HERO = 28     # 首页大标题（Hero 场景）
    FS_H1 = 20       # 主标题
    FS_H2 = 17       # 页内标题
    FS_H3 = 15       # 小标题 / 卡片标题
    FS_BODY = 13     # 正文
    FS_CAPTION = 12  # 辅助说明
    FS_MICRO = 11    # 极小字（时间戳、单位）

    # 兼容旧别名
    SZ_HERO = '28px'
    SZ_TITLE = '20px'
    SZ_SECTION = '15px'
    SZ_BODY = '13px'
    SZ_SMALL = '12px'
    SZ_MICRO = '11px'

    # 字重
    W_REGULAR = 400
    W_MEDIUM = 500
    W_SEMIBOLD = 600
    W_BOLD = 700
```

#### 步骤 1.4 全项目 grep 硬编码，替换为令牌

```powershell
# 检查脚本（放在 scripts/audit_style_tokens.py）
patterns = {
    'hardcoded_color':  r"#[0-9a-fA-F]{6}",
    'hardcoded_font_px': r'\b\d{1,2}px\b',
    'hardcoded_spacing': r'set(ContentsMargins|Spacing)\(\s*\d+\s*,',
}
```

**规则**：所有非 `styles.py` 内的硬编码必须替换为 `Colors.*` / `Fonts.*` / `Spacing.*`。

---

### 阶段 2：图表展示优化（`ai_metrics_chart.py`）

**目标**：让图表具备悬停提示、动画过渡、响应式重绘、主题映射。

#### 步骤 2.1 主题映射到 Matplotlib

```python
# ui/components/ai_metrics_chart.py
from ui.styles import Colors

def _apply_theme(fig, ax_list):
    """将 Colors 常量映射为 Matplotlib rcParams 与轴样式"""
    bg = Colors.BG          # #1a1a2e
    card = Colors.CARD      # #21213a
    text = Colors.TEXT      # #F5F1E8
    text2 = Colors.TEXT2
    text3 = Colors.TEXT3
    grid = Colors.DIVIDER   # #2E2E4C
    brand = Colors.BRAND    # #c9a227
    accent = Colors.ACCENT  # #8b0000

    fig.patch.set_facecolor(bg)
    for ax in ax_list:
        ax.set_facecolor(card)
        ax.tick_params(colors=text2, labelsize=10)
        ax.label.set_color(text)
        ax.grid(True, color=grid, alpha=0.5, linewidth=0.6)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(grid)
        ax.spines['bottom'].set_color(grid)
    return {'brand': brand, 'accent': accent, 'text': text, 'text2': text2}
```

#### 步骤 2.2 响应式重绘

```python
class AIMetricsChart(QWidget):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.figure is not None:
            w = max(320, self.width() - 24)
            h = max(200, int(w * 0.45))
            self.figure.set_size_inches(w / self._dpi, h / self._dpi, forward=True)
            self.figure.tight_layout()
```

#### 步骤 2.3 悬停 tooltip + 高亮

```python
from matplotlib.widgets import EventCallbackBasics

def _on_motion(self, event):
    """鼠标移入图元时显示 tooltip 并加粗该数据点。"""
    if event.inaxes not in (self.ax1, self.ax2):
        return
    for line in event.inaxes.lines:
        x, y = event.xdata, event.ydata
        nearest = min(line.get_xydata(), key=lambda p: (p[0] - x) ** 2)
        # 找到最近的数据点，绘制 highlight circle 并显示 annotation
```

#### 步骤 2.4 空数据引导（不再伪造）

替换 `generate_demo_data()`，改为展示 `EmptyState`：

```python
def _show_empty_state(self):
    for ax in (self.ax1, self.ax2):
        ax.clear()
        ax.text(0.5, 0.5, '暂无数据\n请在“设置”中启用 AI 指标采集',
                transform=ax.transAxes, ha='center', va='center',
                color=Colors.TEXT3, fontsize=Fonts.FS_BODY)
        ax.axis('off')
```

#### 步骤 2.5 加载动画

使用 `CollapsibleCard.TaijiSpinner`（已存在），在 `load_real_data()` 期间覆盖显示。

---

### 阶段 3：内容排版规范化

**目标**：强制使用 6 级 Font Scale + 8-4 间距体系，消除散点。

#### 步骤 3.1 建立 UI 语义类名（QSS 优先使用 objectName）

在 `styles.py` 中新增按 objectName 的样式：

```python
# ui/styles.py 追加
def _qss_font_scale(self):
    return f"""
        QLabel#t-hero  {{ font-family: {Fonts.TITLE}; font-size: {Fonts.FS_HERO}px; font-weight: {Fonts.W_BOLD}; color: {Colors.TEXT}; line-height: {Spacing.LINE_HEIGHT_TIGHT}; }}
        QLabel#t-h1    {{ font-family: {Fonts.TITLE}; font-size: {Fonts.FS_H1}px;  font-weight: {Fonts.W_SEMIBOLD}; color: {Colors.TEXT}; }}
        QLabel#t-h2    {{ font-family: {Fonts.TITLE}; font-size: {Fonts.FS_H2}px;  font-weight: {Fonts.W_SEMIBOLD}; color: {Colors.TEXT}; letter-spacing: {Spacing.LETTER_SPACING}px; }}
        QLabel#t-h3    {{ font-family: {Fonts.BODY}; font-size: {Fonts.FS_H3}px;   font-weight: {Fonts.W_MEDIUM}; color: {Colors.TEXT}; }}
        QLabel#t-body  {{ font-family: {Fonts.BODY}; font-size: {Fonts.FS_BODY}px;  color: {Colors.TEXT2}; line-height: {Spacing.LINE_HEIGHT}; }}
        QLabel#t-caption {{ font-family: {Fonts.BODY}; font-size: {Fonts.FS_CAPTION}px; color: {Colors.TEXT3}; }}
        QLabel#t-micro {{ font-family: {Fonts.BODY}; font-size: {Fonts.FS_MICRO}px; color: {Colors.TEXT4}; }}
        QLabel#t-value {{ font-family: {Fonts.MONO}; font-size: {Fonts.FS_BODY}px; color: {Colors.BRAND}; }}
    """
```

#### 步骤 3.2 引入 `LabelFactory`（禁止直接 `QLabel` 硬设样式）

```python
# ui/components/typography.py 新增
class TLabel:
    """统一的 QLabel 工厂，取代散落的 font-size/padding。"""
    @staticmethod
    def hero(text: str) -> QLabel: ...
    @staticmethod
    def h1(text: str) -> QLabel: ...
    @staticmethod
    def h2(text: str) -> QLabel: ...
    @staticmethod
    def h3(text: str) -> QLabel: ...
    @staticmethod
    def body(text: str) -> QLabel: ...
    @staticmethod
    def caption(text: str) -> QLabel: ...
    @staticmethod
    def micro(text: str) -> QLabel: ...
    @staticmethod
    def value(text: str) -> QLabel: ...  # 数值/等宽
```

#### 步骤 3.3 布局间距强制规范

```python
# 替换散落的 setContentsMargins / setSpacing
panel_lay.setContentsMargins(Spacing.PAD_LG, Spacing.PAD_LG, Spacing.PAD_LG, Spacing.PAD_LG)
panel_lay.setSpacing(Spacing.GAP)          # 卡片之间 16px
row_lay.setSpacing(Spacing.GAP_SM)         # 表单项之间 8px
```

#### 步骤 3.4 卡片内标题行统一

在 `collapsible_card.py` 中把标题字体、字重、颜色绑定到 Font Scale：

```python
title_lbl.setFont(QFont(Fonts.TITLE, 15, QFont.Weight.DemiBold))
title_lbl.setStyleSheet(f"color: {Colors.TEXT}; letter-spacing: 0.5px;")
```

---

### 阶段 4：内容列表样式统一

**目标**：所有"列表项"（大运柱、流年柱、星宿、六爻、章节项等）共享同一视觉语言。

#### 步骤 4.1 定义 `ListItem` 组件

```python
# ui/components/list_item.py 新增
class ListItem(QFrame):
    """统一列表项：图标 + 主标题 + 副标题 + 右侧数值/状态徽章。

    支持状态：default / hover / active / disabled。
    """
    clicked = Signal()

    def __init__(self, icon: str = '', title: str = '', subtitle: str = '',
                 value: str = '', badge_color: str = None, parent=None):
        super().__init__(parent)
        self.setProperty('state', 'default')
        self.setCursor(Qt.PointingHandCursor)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(Spacing.S3, Spacing.S2, Spacing.S3, Spacing.S2)
        lay.setSpacing(Spacing.S3)
        # 图标 24x24
        # 主标题 15px DemiBold  + 副标题 12px muted
        # 右侧 value 13px 金色 或 badge 圆角药丸
```

配套 QSS：

```python
LIST_ITEM = f"""
    QFrame[state="default"] {{ background: transparent; border: 1px solid transparent; border-radius: {Spacing.RADIUS_SM}px; }}
    QFrame[state="hover"]   {{ background: {Colors.HOVER}; border: 1px solid {Colors.BORDER}; }}
    QFrame[state="active"]  {{ background: {Colors.CARD_HOVER}; border-left: 3px solid {Colors.BRAND}; }}
    QFrame[state="disabled"]{{ background: transparent; color: {Colors.TEXT4}; }}
"""
```

#### 步骤 4.2 批量替换

| 原位置 | 现状 | 替换为 |
|--------|------|--------|
| `result_panel.py` 大运柱列表 | 手写 QHBoxLayout | `ListItem(title='甲子', subtitle='大运', value='1990-1999')` |
| `result_panel.py` 流年列表 | 同上 | `ListItem(icon='☘', title='甲子', value='吉')` |
| `xuan_kong_result_panel.py` 宫位详情 | 手写 QGridLayout | `ListItem` 竖排 |
| `liuren_result_panel.py` 十二天将 | 手写表格 | `ListItem` 网格 |
| `export_dialog.py` 章节复选框组 | `QCheckBox` 竖列 | 保留 `QCheckBox`，但换用统一 `checkbox-item` QSS |

#### 步骤 4.3 状态徽章（Badge）

```python
# ui/components/badge.py 新增
class Badge(QLabel):
    """状态徽章：吉 / 凶 / 中 / 吉星 / 凶星 等语义色小标签"""
    def __init__(self, text: str, semantic: str = 'info'):
        super().__init__()
        color_map = {'success': Colors.SEMANTIC_SUCCESS, 'danger': Colors.SEMANTIC_DANGER,
                     'warning': Colors.SEMANTIC_WARNING, 'info': Colors.SEMANTIC_INFO,
                     'brand': Colors.BRAND, 'accent': Colors.ACCENT}
        c = color_map[semantic]
        self.setText(f" {text} ")
        self.setStyleSheet(f"""
            color: {Colors.TEXT_INV if c in (Colors.ACCENT, Colors.BRAND) else c};
            background: {c};
            border-radius: {Spacing.RADIUS_PILL}px;
            padding: 2px 8px;
            font-size: {Fonts.FS_MICRO}px;
            font-weight: {Fonts.W_SEMIBOLD};
        """)
```

---

### 阶段 5：视觉元素一致性

#### 步骤 5.1 颜色系统（三色模型）

```
主色 (Primary)   = BRAND  #c9a227   导航选中、强调、图表主色
辅助色 (Secondary) = ACCENT #8b0000 主按钮、主操作、警报
中性色 (Neutral)  = BG / CARD / BORDER / TEXT*  9 级灰阶
语义色 (Semantic) = SUCCESS / WARNING / DANGER / INFO
领域色 (Domain)   = WOOD / FIRE / EARTH / METAL / WATER
```

**使用规则**（写入 `docs/design-tokens.md`）：

- `BRAND` 用于「导航 + 强调 + 图表主色」，禁止用作按钮背景。
- `ACCENT` 仅用于「一次交互一个页面最多 2 个主按钮」。
- `Semantic` 只用于「状态提示」，禁止装饰性使用。
- `Domain` 五行色仅出现在八字/玄空领域特定区域。

#### 步骤 5.2 图标体系

**规范**：

- **图标源**：统一放 `assets/icons/*.svg`（尺寸 24×24 viewBox）。
- **来源**：使用 `Iconify` 中的 `tabler-outline`（Apache 2.0）或 `phosphor-regular`（MIT），本地化保存。
- **尺寸**：`XS=16` / `SM=20` / `MD=24` / `LG=32` / `XL=48`，仅 5 档。
- **线宽**：`stroke-width = 1.75px`（Tabler 默认），全项目统一。
- **颜色**：默认 `Colors.TEXT2`，hover 变 `Colors.BRAND`，禁用 `Colors.TEXT4`。

**IconLoader 工具**：

```python
# ui/components/icons.py 新增
from PySide6.QtGui import QIcon

_ICON_CACHE = {}

def icon(name: str, size: int = 24, color: str = None) -> QIcon:
    """按名称加载 SVG 图标，缓存 QIcon。size 只支持 16/20/24/32/48。"""
    if size not in (16, 20, 24, 32, 48):
        raise ValueError(f"图标尺寸必须为 16/20/24/32/48，收到 {size}")
    from core.path_utils import get_resource_path
    path = get_resource_path(f"assets/icons/{name}.svg")
    if not path.exists():
        raise FileNotFoundError(f"图标不存在：{path}")
    return QIcon(str(path))
```

**迁移策略**：

| 位置 | 现状 | 目标 |
|------|------|------|
| 侧边栏 4 个模块 | Unicode `☯ ⚊ ☵ ⛰` | SVG（`bazi.svg / meihua.svg / liuren.svg / xuan-kong.svg`）|
| 结果面板顶部工具栏 | emoji `🤖 📋 📤` | SVG（`robot.svg / copy.svg / export.svg`）|
| 按钮前缀图标 | emoji | `QIcon` + `btn.setIconSize(QSize(20,20))` |

#### 步骤 5.3 组件样式统一

**按钮四态模型**（补全 `styles.py`）：

```python
# ui/styles.py
class ButtonStates:
    """统一按钮状态模型：default / hover / pressed / checked / disabled / focus"""
    @staticmethod
    def _base(bg, fg, border, radius=Spacing.RADIUS_SM, h=Spacing.BUTTON_H):
        return f"""
            QPushButton {{
                background: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: {radius}px;
                padding: 0 20px;
                min-height: {h}px;
                font-size: {Fonts.FS_BODY}px;
                font-family: {Fonts.BODY};
                font-weight: {Fonts.W_MEDIUM};
            }}
            QPushButton:hover:not(:disabled) {{
                background: {Colors.CARD_HOVER};
                border-color: {Colors.BRAND_LIGHT};
                color: {Colors.BRAND};
            }}
            QPushButton:pressed:not(:disabled) {{
                background: {Colors.BG_DARK};
                transform: translateY(1px);
            }}
            QPushButton:checked {{
                background: {Colors.BRAND};
                color: {Colors.TEXT_INV};
                border-color: {Colors.BRAND};
                font-weight: {Fonts.W_SEMIBOLD};
            }}
            QPushButton:disabled {{
                background: {Colors.BORDER};
                color: {Colors.TEXT4};
                border-color: {Colors.BORDER};
            }}
            QPushButton:focus-visible {{
                outline: 2px solid {Colors.BRAND};
                outline-offset: 2px;
            }}
        """

    PRIMARY   = _base(Colors.ACCENT, Colors.TEXT_INV, Colors.ACCENT_DARK)
    SECONDARY = _base(Colors.CARD, Colors.TEXT, Colors.BORDER2)
    GHOST     = _base('transparent', Colors.TEXT2, 'transparent')
    DANGER    = _base(Colors.SEMANTIC_DANGER, Colors.TEXT_INV, '#8B3A2E')
```

**输入框、下拉框、日期框、CheckBox、RadioButton 同理全部按此模型重写**，保证六态一致。

#### 步骤 5.4 弹窗统一

在 `styles.py` 增加全局 `QDialog` 样式：

```python
DIALOG = f"""
    QDialog {{ background: {Colors.BG}; }}
    QFrame#dialog-header {{
        background: {Colors.CARD};
        border-bottom: 1px solid {Colors.DIVIDER};
        border-radius: {Spacing.RADIUS_LG}px {Spacing.RADIUS_LG}px 0 0;
        padding: {Spacing.S5}px {Spacing.S6}px;
    }}
    QFrame#dialog-body {{
        padding: {Spacing.S6}px;
    }}
    QFrame#dialog-footer {{
        background: {Colors.CARD};
        border-top: 1px solid {Colors.DIVIDER};
        border-radius: 0 0 {Spacing.RADIUS_LG}px {Spacing.RADIUS_LG}px;
        padding: {Spacing.S4}px {Spacing.S6}px;
    }}
"""
```

`export_dialog.py` / `settings_dialog.py` / `about_dialog.py` 全部套此结构。

---

### 阶段 6：动效与微交互

**统一缓动参数**（写入 `styles.py` 或 `ui/animation.py`）：

```python
# ui/animation.py
from PySide6.QtCore import QEasingCurve
from PySide6.QtCore import Property

EASING_STANDARD = QEasingCurve.InOutCubic     # 0.4s 默认过渡
EASING_IN       = QEasingCurve.InCubic        # 消失
EASING_OUT      = QEasingCurve.OutCubic       # 出现

DURATION_INSTANT = 100    # 键盘反馈
DURATION_FAST    = 200    # hover 切换
DURATION_NORMAL  = 300    # 默认动画
DURATION_SLOW    = 500    # 卡片折叠
DURATION_SLOWER  = 800    # 页面切换
```

**应用场景**：

| 组件 | 属性 | 时长 | 缓动 |
|------|------|------|------|
| `CollapsibleCard` 高度 | `maximumHeight` | 300ms | IN_OUT_CUBIC |
| `ListItem` 背景色 | `background` | 100ms | LINEAR |
| 卡片阴影 hover | QGraphicsDropShadowEffect.color | 200ms | IN_CUBIC |
| AI 输出流式追加 | QGraphicsOpacityEffect.opacity | 100ms/行 | LINEAR |
| 结果面板板块切换 | QGraphicsOpacityEffect.opacity | 300ms | IN_OUT_CUBIC |

---

### 阶段 7：可访问性与国际化预留

**步骤 7.1 键盘焦点**：为所有可交互控件补齐 `:focus-visible` 样式（2px BRAND outline）。

**步骤 7.2 对比度**：用脚本校验 WCAG AA：

```python
# scripts/audit_contrast.py
def contrast_ratio(hex_a: str, hex_b: str) -> float:
    def lum(h):
        c = tuple(int(h[i:i+2], 16)/255 for i in (1,3,5))
        c = tuple(v/12.92 if v <= 0.03928 else ((v+0.055)/1.055)**2.4 for v in c)
        return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2]
    L1, L2 = lum(hex_a), lum(hex_b)
    hi, lo = max(L1,L2), min(L1,L2)
    return (hi+0.05)/(lo+0.05)

# 全 UI 色对必须 ≥ 4.5:1（正文）或 ≥ 3:1（大字）
```

**步骤 7.3 ARIA 描述**：为按钮、图标按钮加 `setAccessibleName` / `setAccessibleDescription`。

---

## 4. 技术规范

### 4.1 CSS/QSS 变量映射表

| Token | QSS 引用 | 用途 |
|-------|---------|------|
| `Colors.BG` | `background-color` | 主背景 |
| `Colors.CARD` | `background-color` | 卡片背景 |
| `Colors.BRAND` | `color`/`background`/`border-color` | 品牌色 |
| `Colors.ACCENT` | `background-color` | 主操作按钮 |
| `Colors.TEXT/TEXT2/TEXT3/TEXT4` | `color` | 4 级灰阶 |
| `Colors.BORDER/BORDER2` | `border` | 边框 |
| `Spacing.RADIUS_SM/RADIUS/RADIUS_LG` | `border-radius` | 圆角 |
| `Spacing.GAP/PAD*` | `padding/margin/spacing` | 间距 |
| `Fonts.FS_H1~FS_MICRO` | `font-size` | 字号 |

### 4.2 组件 API 规范

| 组件 | 位置 | 主要 API |
|------|------|---------|
| `CollapsibleCard` | `ui/components/collapsible_card.py` | `title, icon, accent_color, collapsed, toggle(), set_collapsed()`, `content_layout` |
| `ListItem` | `ui/components/list_item.py`（新增） | `icon, title, subtitle, value, state`, `clicked signal` |
| `Badge` | `ui/components/badge.py`（新增） | `text, semantic ∈ {success,warning,danger,info,brand,accent}` |
| `EmptyState` | `ui/components/states.py`（新增） | `icon, title, hint` |
| `LoadingState` | `ui/components/states.py` | `message, hint_list` |
| `ErrorState` | `ui/components/states.py` | `message, retry_hint, on_retry signal` |
| `TLabel` | `ui/components/typography.py`（新增） | 类方法 `hero/h1/h2/h3/body/caption/micro/value` |
| `IconButton` | `ui/components/icon_button.py`（新增） | `icon(name, size)`, `tooltip`, `state` |
| `DataCard` | `ui/components/data_card.py`（新增） | `title, value, unit, badge, spark` |

### 4.3 图标使用规范

- 目录：`assets/icons/{domain}/{name}.svg`，例如 `assets/icons/bazi/bazi.svg`
- 命名：小写短横线（kebab-case）
- 尺寸：仅 16 / 20 / 24 / 32 / 48
- 颜色：SVG 内 `fill="currentColor"` 或 `stroke="currentColor"`，由 QIcon 或 QSS 控制
- 加载：一律走 `ui/components/icons.py::icon(name, size)`

### 4.4 命名与代码规范

- Python：PEP 8，类名 `PascalCase`，方法/变量 `snake_case`
- QSS：selector 使用 `#objectName` 优先，属性选择器 `[state="hover"]` 用于状态
- 组件文件：`ui/components/{name}.py`，一个文件一个主组件
- 常量文件：`ui/styles.py` 保留，但新增 `ui/animation.py`、`ui/components/icons.py`

### 4.5 图表 API（Matplotlib）规范

- `FigureCanvasQTAgg` 必写 `resizeEvent` 调用 `set_size_inches(forward=True)`
- 所有颜色走 `_apply_theme()`，禁止硬编码 `#xxxxxx`
- 数据加载失败展示 `EmptyState`，禁止伪造数据
- 悬停交互使用 `event_data()` 桥接到 Qt `QToolTip`

---

## 5. 资源需求

### 5.1 字体

| 名称 | 用途 | 授权 | 来源 |
|------|------|------|------|
| KaiTi（楷体） | 主标题、板块名 | 系统内置 | Windows 自带 |
| SimSun（宋体） | 楷体回退 | 系统内置 | Windows 自带 |
| Microsoft YaHei | 正文 | 系统内置 | Windows 自带 |
| Cascadia Code | 等宽数值 | SIL OFL 1.1 | [github.com/microsoft/cascadia-code](https://github.com/microsoft/cascadia-code) |
| Noto Serif CJK SC | 非 Windows 回退 | SIL OFL 1.1 | [github.com/googlefonts/noto-cjk](https://github.com/googlefonts/noto-cjk) |
| Noto Sans CJK SC | 非 Windows 回退 | SIL OFL 1.1 | 同上 |

**注意**：楷体/宋体是 Windows 系统字体，跨平台需打包 Noto CJK 回退。

### 5.2 图标库

**推荐**：`Iconify` + `tabler-outline`（Apache 2.0），需要下载以下图标（25 个）：

| 分类 | 图标 |
|------|------|
| 模块导航 | `bazi.svg`（☯ 太极）、`meihua.svg`（梅花/花枝）、`liuren.svg`（天盘）、`xuan-kong.svg`（山脉） |
| 工具栏 | `robot.svg`、`copy.svg`、`export.svg`、`export-pdf.svg`、`export-excel.svg`、`collapse-all.svg` |
| 设置 | `settings.svg`、`info.svg`、`close.svg`、`check.svg` |
| 状态 | `success.svg`、`warning.svg`、`danger.svg`、`info.svg`、`loading.svg`（旋转太极） |
| 通用 | `arrow-down.svg`、`arrow-up.svg`、`arrow-left.svg`、`arrow-right.svg`、`chevron.svg`、`refresh.svg`、`search.svg` |

**下载脚本**（`scripts/download_icons.py`）：

```python
import requests, pathlib
TABLER = "https://api.iconify.design/tabler/{name}.svg"
NAMES = ["infinity", "blossom", "globe", "mountain", "bot", "copy", "download", "file-pdf", "file-spreadsheet", "layout-2", "settings", "info-circle", "circle-x", "circle-check", "circle-alert", "circle-info", "loader", "chevron-down", "chevron-up", "chevron-left", "chevron-right", "chevron", "refresh"]
out = pathlib.Path("assets/icons"); out.mkdir(parents=True, exist_ok=True)
for n in NAMES:
    r = requests.get(TABLER.format(name=n), timeout=10)
    r.raise_for_status()
    (out / f"{n}.svg").write_bytes(r.content)
```

### 5.3 第三方依赖

无新增运行时依赖，仅新增开发依赖：

| 包 | 用途 | 版本 |
|----|------|------|
| `iconify-api-client` | 图标下载（仅开发用） | latest |
| `Pillow` | 图标 SVG→PNG 转换（如需要） | 已在 requirements |
| `weasyprint` | PDF 导出主题化（可选） | 待评估 |

现有依赖保持不变：
- `PySide6>=6.9,<6.12`
- `matplotlib>=3.7,<3.10`
- `pandas`, `numpy`, `lunardate`, `chromadb`, `langchain`, `pydantic>=2`

### 5.4 开发工具

- VSCode + Python/Pylance
- Qt Designer（用于原型验证）
- Figma（可选，用于设计稿）
- `scripts/audit_style_tokens.py`（自查硬编码）
- `scripts/audit_contrast.py`（自查对比度）
- `scripts/screenshot_regression.py`（截图回归，可选）

---

## 6. 开发排期与里程碑

**总工期**：约 **10 个工作日**（不含 code review / QA 缓冲）。

| 阶段 | 内容 | 工时 | 产出 | 里程碑 |
|------|------|------|------|--------|
| M1 准备 | 图标下载 + 自查脚本 + Design Tokens 收敛 | 1d | `styles.py` v6.1、`icons/`、`audit_*.py` | 令牌冻结 |
| M2 图表 | `ai_metrics_chart.py` 主题化 + 响应式 + 悬停 | 1.5d | 新 `AIMetricsChart` | 图表可交互 |
| M3 排版 | `typography.py` + `QLabel` 全量替换 + Font Scale 落地 | 2d | 全 UI 字号合规 | 排版一致 |
| M4 列表 | `ListItem` / `Badge` / `states.py` 三组件 + 四面板改造 | 2d | 统一列表语言 | 列表一致 |
| M5 视觉 | 图标迁移 + 按钮六态 + 弹窗统一 | 2d | `ButtonStates` / `DIALOG` / 图标迁移 | 视觉一致 |
| M6 动效 | `animation.py` + 卡片折叠/切换/AI 流式动效 | 1d | 统一缓动 | 动效流畅 |
| M7 收口 | 对比度、A11y、文档、回归测试 | 0.5d | `audit_*.py` 通过 | 交付 |

**依赖顺序**：M1 → (M2 ∥ M3) → M4 → M5 → M6 → M7。M2 与 M3 可并行。

---

## 7. 质量验收标准

### 7.1 UI 还原度（Visual Fidelity）

- [ ] 主色 `#1a1a2e / #c9a227 / #8b0000` 三主色在项目内使用率 ≥ 95%（`scripts/audit_style_tokens.py` 通过）
- [ ] 字号严格 6 级：28 / 20 / 17 / 15 / 13 / 12 / 11，禁止其他字号出现
- [ ] 间距严格 8-4 基准（4/8/12/16/20/24/32/48），无奇数值
- [ ] 圆角仅使用 `4 / 6 / 10 / 14 / 18 / 999`
- [ ] 侧边栏 4 模块导航图标为 SVG，24×24，线宽 1.75px
- [ ] 结果面板顶部工具栏图标为 SVG，20×20
- [ ] 弹窗（设置/导出/关于）标题栏、正文、底部三区分明

### 7.2 交互一致性（Interaction Consistency）

- [ ] 全部 `QPushButton` 具备 6 态：`default / hover / pressed / checked / disabled / focus-visible`
- [ ] 全部 `QLineEdit / QComboBox / QDateEdit / QCheckBox / QRadioButton` 具备 `default / hover / focus / disabled` 4 态
- [ ] 全部 `ListItem` 具备 `default / hover / active / disabled` 4 态
- [ ] 全部折叠动画时长 300ms + `IN_OUT_CUBIC`
- [ ] 图表悬停显示 tooltip，鼠标移出自动消失
- [ ] 键盘 Tab 顺序符合视觉流（从上到下、从左到右）
- [ ] 所有可交互元素支持 `Enter` / `Space` 触发

### 7.3 浏览器/平台兼容性

| 环境 | 最低要求 |
|------|---------|
| Windows | 10 1903+ / 11 22H2+ |
| macOS | 12 Monterey+ |
| Linux | Ubuntu 22.04+ / Debian 12+ |
| 分辨率 | 1280×800 ~ 3840×2160 自适应 |
| DPI | 100% / 125% / 150% / 200%（Qt High-DPI aware） |
| Python | 3.10 ~ 3.12 |
| PySide6 | 6.9 ~ 6.11 |

### 7.4 性能

- [ ] 首次启动 < 2s（冷启动，含数据库初始化）
- [ ] 排盘计算完成 → UI 渲染 < 200ms
- [ ] 图表刷新（≤ 100 数据点）< 100ms
- [ ] 无内存泄漏（长跑 30 分钟，`tracemalloc` 无持续增长）
- [ ] 内存占用 < 150MB（空闲状态）

### 7.5 可访问性

- [ ] 全部文本对比度 ≥ 4.5:1（WCAG AA 正文）
- [ ] 大字（≥ 18px）对比度 ≥ 3:1
- [ ] 交互元素聚焦可见（`outline: 2px solid BRAND`）
- [ ] 图标按钮 100% 具备 `accessibleName` / `tooltip`
- [ ] 无纯装饰性 emoji 用作主要功能标识

### 7.6 回归测试清单

- [ ] 八字排盘全链路（输入 → 排盘 → 展示 → AI 分析 → 导出）
- [ ] 梅花易数全链路
- [ ] 大六壬全链路
- [ ] 玄空飞星全链路（含九宫格悬停）
- [ ] 设置对话框（AI 配置 / 通用设置 / 关于）
- [ ] 导出对话框（CSV / Excel / PDF 三格式）
- [ ] 窗口缩放至 1100×700 最小尺寸不溢出
- [ ] 窗口放大至 1920×1080 内容居中不拉伸
- [ ] 深色主题下无白闪（QToolTip / QDialog 弹出瞬间）
- [ ] `pytest tests/ui/` 覆盖率 ≥ 60%（UI 层可测部分）

### 7.7 文档交付

- [ ] 本方案文档更新为 v1.1（含最终决策记录）
- [ ] `docs/design-tokens.md`（新增）
- [ ] `docs/component-guide.md`（新增，`ListItem` / `Badge` / `DataCard` 使用示例）
- [ ] `README.md` UI 章节更新

---

## 8. 附录：修改清单速查表

| 文件 | 操作 | 关键改动 |
|------|------|---------|
| `ui/styles.py` | 重写 | 收敛同义色、8-4 间距、Font Scale、`ButtonStates`、`DIALOG` QSS |
| `ui/main_window.py` | 微调 | 侧边栏图标改 SVG、字体走 `TLabel.h1/h3` |
| `ui/components/typography.py` | 新增 | `TLabel` 工厂 |
| `ui/components/list_item.py` | 新增 | 统一列表项 |
| `ui/components/badge.py` | 新增 | 状态徽章 |
| `ui/components/states.py` | 新增 | `EmptyState` / `LoadingState` / `ErrorState` |
| `ui/components/icon_button.py` | 新增 | 图标按钮 |
| `ui/components/data_card.py` | 新增 | 数值卡片 |
| `ui/components/icons.py` | 新增 | `icon(name, size)` 加载器 |
| `ui/animation.py` | 新增 | 缓动常量 + 时长 |
| `ui/components/collapsible_card.py` | 微调 | 折叠动画 300ms IN_OUT_CUBIC、标题字体走 Font Scale |
| `ui/components/input_panel.py` | 微调 | 间距走 `Spacing.PAD_LG/GAP` |
| `ui/components/meihua_input.py` | 微调 | 同上 |
| `ui/components/liuren_input.py` | 微调 | 同上 |
| `ui/components/xuan_kong_input.py` | 微调 | 同上 |
| `ui/components/result_panel.py` | 中等 | 大运/流年列表替换为 `ListItem` + `Badge` |
| `ui/components/meihua_result_panel.py` | 中等 | 卦象展示图标 SVG 化 |
| `ui/components/liuren_result_panel.py` | 中等 | 十二天将使用 `ListItem` |
| `ui/components/xuan_kong_result_panel.py` | 中等 | `_CELL_COLORS` 从 `Colors` 派生；九宫悬停增强 |
| `ui/components/ai_metrics_chart.py` | 重写 | 主题映射 + 响应式 + 悬停 tooltip + EmptyState |
| `ui/components/ai_analysis_renderer.py` | 微调 | 流式动画走 `animation.py` |
| `ui/components/timeline.py` | 微调 | 时间轴节点 hover 增强 |
| `ui/components/settings_dialog.py` | 中等 | 套用 `DIALOG` QSS |
| `ui/components/export_dialog.py` | 中等 | 套用 `DIALOG` QSS + 章节列表用 `ListItem` |
| `ui/components/about_dialog.py` | 微调 | 套用 `DIALOG` QSS |
| `assets/icons/*.svg` | 新增 | 25 个 SVG 图标 |
| `scripts/audit_style_tokens.py` | 新增 | 硬编码自查 |
| `scripts/audit_contrast.py` | 新增 | 对比度自查 |
| `scripts/download_icons.py` | 新增 | 图标批量下载 |
| `docs/design-tokens.md` | 新增 | 设计令牌文档 |
| `docs/component-guide.md` | 新增 | 组件使用指南 |

---

## 附：风险与回滚

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 图标版权 | 低 | 中 | 只用 Apache 2.0 / MIT 授权源 |
| 楷体跨平台 | 中 | 低 | Noto Serif CJK SC 作为回退 |
| QSS `:focus-visible` 支持度 | 中 | 低 | Qt 5.15+ 支持，PySide6 6.x 完全支持 |
| Matplotlib DPI 抖动 | 中 | 低 | 使用 `forward=True` + `tight_layout()` |
| 大范围重构导致回归 | 中 | 高 | 每阶段独立 PR，独立可回滚 |

---

**免责声明**：本文档为 UI/UX 层面升级方案，不涉及算法、AI 解读、数据存储等功能性变更。所有涉及命理学、风水学的展示内容仅供文化研究参考，不构成决策依据。涉及健康、法律、投资等重大事项，请咨询相关专业人士。
