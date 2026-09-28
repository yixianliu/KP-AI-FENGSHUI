# KP-AI-FENGSHUI UI 升级实施方案

> 编制日期：2026-09-22  
> 版本：v1.0  
> 目标：将 KP-AI-FENGSHUI 界面从"可用"升级为"专业级国风命理学工具"，对标时空八字、十三行八字、Jiewen、卦天等头部产品

---

## 目录

1. [现状分析](#1-现状分析)
2. [对标参考分析](#2-对标参考分析)
3. [升级总目标与原则](#3-升级总目标与原则)
4. [视觉规范升级](#4-视觉规范升级)
5. [导航栏改造](#5-导航栏改造)
6. [输入面板改造](#6-输入面板改造)
7. [结果面板改造](#7-结果面板改造)
8. [AI 解读区改造](#8-ai-解读区改造)
9. [玄空飞星九宫格升级](#9-玄空飞星九宫格升级)
10. [梅花易数结果面板升级](#10-梅花易数结果面板升级)
11. [大六壬结果面板升级](#11-大六壬结果面板升级)
12. [对话框组件升级](#12-对话框组件升级)
13. [导出系统升级](#13-导出系统升级)
14. [交互与动效规范](#14-交互与动效规范)
15. [实施步骤与优先级](#15-实施步骤与优先级)
16. [验收标准](#16-验收标准)

---

## 1. 现状分析

### 1.1 技术栈

| 项 | 内容 |
|---|------|
| GUI 框架 | PySide6 (Qt6)，版本 `>=6.9,<6.12` |
| 样式方案 | Qt Style Sheets（qss）+ 内联 styleSheet() |
| 主色体系 | 深靛蓝 `#1a1a2e` / 古金 `#c9a227` / 朱红 `#8b0000` |
| 字体体系 | 标题：KaiTi/SimSun；正文：Microsoft YaHei；数值：Cascadia Code |
| 布局结构 | QSplitter 左右分栏（左 34% 输入 / 右 66% 结果） |
| 导航方式 | 顶部水平 QPushButton 胶囊组（4个模块） |
| 结果容器 | QStackedWidget 左右各自管理4个模块页 |
| 卡片组件 | CollapsibleCard（QPropertyAnimation 折叠动画） |
| 加载动画 | TaijiSpinner（旋转太极 SVG QPainter） |

### 1.2 当前界面结构

```
MainWindow (1400×900, min 1100×700)
├── QFrame 导航栏 (NAVBAR)
│   ├── QLabel 图标 (☯)
│   ├── QLabel 标题 ("风水排盘专业工具")
│   ├── QPushButton × 4 (八字排盘 / 梅花易数 / 大六壬 / 玄空飞星)
│   └── QToolButton × 2 (设置 / 关于)
├── QSplitter (左右分栏)
│   ├── 左栏 QStackedWidget (34% 宽度)
│   │   ├── 八字输入面板 (InputPanel)
│   │   ├── 梅花输入面板 (MeihuaInputPanel)
│   │   ├── 大六壬输入面板 (LiurenInputPanel)
│   │   └── 玄空飞星输入面板 (XuanKongInputPanel)
│   └── 右栏 QStackedWidget (66% 宽度)
│       ├── 八字结果面板 (ResultPanel)
│       ├── 梅花结果面板 (MeihuaResultPanel)
│       ├── 大六壬结果面板 (LiurenResultPanel)
│       └── 玄空飞星结果面板 (XuanKongResultPanel)
└── QStatusBar (底部状态栏)
```

### 1.3 现存问题清单

| # | 问题描述 | 严重程度 |
|---|---------|---------|
| 1 | 顶部导航栏为普通 QPushButton 水平排列，视觉权重过高，未体现"玄中易"风格 | 中 |
| 2 | 左栏输入面板仅八字 InputPanel 做了精修，梅花/大六壬输入面板仍使用基础控件堆叠，风格不统一 | 高 |
| 3 | 结果面板的顶部工具栏按钮（刷新/复制/导出/收起全部）在窄屏下溢出，无溢出处理 | 中 |
| 4 | 玄空飞星九宫格 Canvas 区域仅占位，无实际 QPainter 绘制，显示"九宫飞星盘"文字 | 高 |
| 5 | AI 解读区渲染器 `ai_analysis_renderer.py` 对三段式结构支持良好，但视觉层次弱，"龙虎山大师兄"标题风格与其他区域不一致 | 中 |
| 6 | 八字结果面板的四柱色块固定 36px，未随窗口缩放自适应 | 中 |
| 7 | 设置对话框、导出对话框样式与主体不统一，缺少主题感 | 中 |
| 8 | 空状态页面（未排盘时）只有一个太极图标 + 文字，无引导性动效 | 低 |
| 9 | 无明/暗主题切换能力，深色底固定，无法适配用户偏好 | 中 |
| 10 | 各模块结果面板间缺乏统一的视觉语言（卡片阴影、分割线样式、间距系统性不一致） | 中 |
| 11 | 结果面板顶部标题行中 emoji 图标（🤖、📋、📤）在深色底上不够融合，风格不统一 | 低 |
| 12 | 无侧边历史记录面板，用户无法快速查看/对比之前的排盘结果 | 中 |

---

## 2. 对标参考分析

### 2.1 市场主流产品特征

| 产品 | 核心亮点 | 可借鉴点 |
|------|---------|---------|
| **时空八字** | 极简主义设计、深色底 + 金色强调、命盘一屏完整呈现 | 四柱紧凑展示、五行能量可视化进度条 |
| **十三行八字** | "刑冲会合"关系图可视化、iPad 双栏布局、流运面板底部滑出 | 关系图谱、流运时间轴底部面板、智能分类 |
| **Jiewen Bazi** | 2025年全面UI改版、古典与现代融合、多模块整合 | 信息密度控制、改版节奏（渐进式而非推倒重来） |
| **卦天软件** | 玄色主调 + 朱砂红强调、思源宋体古籍引文、PDF报告水印 | 深色体系配色方案、古籍引文排版、报告导出品质 |
| **马国峻八字排盘宝** | 纯净无广告、历史记录管理、多条件筛选 | 历史面板设计、案例收藏管理 |

### 2.2 行业 UI 趋势总结

1. **深色底 + 金色点缀** 成为命理工具标准审美（`#0F172A`/`#1a1a2e` 底 + `#c9a227` 强调）
2. **一屏完整呈现** 核心参数（四柱+五行+十神+大运），减少翻页
3. **关系可视化**（刑冲会合箭头图、飞星生克箭头）替代纯文字列表
4. **流运底部面板**（抽屉式）不遮挡主结果区
5. **历史面板侧边滑出**（Overlay 而非全屏切换）
6. **真太阳时校正显式标注**（原始时间 vs 校正时间双列对比）
7. **PDF/报告导出品质升级**（水印、二维码溯源、结构化章节）

---

## 3. 升级总目标与原则

### 3.1 总体目标

> 在保留现有功能架构（PySide6 + QSS + CollapsibleCard）不变的前提下，以**最小侵入方式**对界面进行系统性升级，重点解决：视觉一致性、信息密度、专业感、交互流畅度四个维度。

### 3.2 设计原则

1. **继承性**：现有 `styles.py` 色彩体系 (`INK/GOLD/ZHUSHA`)、`Fonts`、`Spacing` 常量全部保留，禁止推翻重写
2. **渐进式**：每次改造只涉及一个文件或一组相关文件，确保可独立测试
3. **零功能变更**：所有UI升级不改 core 层算法逻辑，不改 service 层业务编排
4. **兼容性**：支持 1100×700 ~ 1920×1080 常见分辨率自适应
5. **可控性**：AI 解读功能保持可选，不因UI升级改变AI调用链路

### 3.3 禁止事项

- 禁止将 PySide6 替换为 CustomTkinter 或 PyQt6（技术栈锁定）
- 禁止修改 `core/` 目录下任何算法代码
- 禁止引入新的第三方 UI 库
- 禁止更改 SQLite 数据库 Schema

---

## 4. 视觉规范升级

### 4.1 色彩体系扩展（更新 `styles.py`）

**新增辅助色彩**，丰富视觉层次：

```python
# 在 Colors 类中新增以下内容（插入位置：五行色彩之后）

# ========== 新中式扩展色彩 ==========
# 宣纸色（浅色区域/选中态背景）
XUANZHI = '#F5F0E6'
XUANZHI_LIGHT = '#FAF7F0'
XUANZHI_DARK = '#E8E0CC'

# 墨色（次级边框/次要文字）
MO = '#2C2C3A'
MO_LIGHT = '#3A3A50'
MO_DARK = '#1E1E2E'

# 玉色（吉星/正面信息）
YU = '#5DAF74'        # 即 SUCCESS，统一命名
YU_LIGHT = '#2A4A38'

# 珊瑚色（警示/特殊标记）
SHANHU = '#D8A94E'    # 即 WARNING，统一命名
SHANHU_LIGHT = '#4A3E20'

# 靛青（辅助强调色，替代部分 QINGHUA 使用场景）
DIANQING = '#7FB3C8'
DIANQING_LIGHT = '#1E3A4A'

# 水墨纹理透明度（用于背景装饰）
INK_WASH_LOW = 'rgba(201, 162, 39, 0.04)'
INK_WASH_MID = 'rgba(201, 162, 39, 0.08)'
```

### 4.2 阴影与层次感（更新 `styles.py`）

新增 QGraphicsDropShadowEffect 统一配置：

```python
# 卡片阴影（所有 CollapsibleCard 统一使用）
CARD_SHADOW = {
    'color': 'rgba(0, 0, 0, 0.35)',
    'offset': (0, 4),
    'radius': 12,
}
# 悬浮卡片阴影（鼠标悬停时增强）
CARD_SHADOW_HOVER = {
    'color': 'rgba(201, 162, 39, 0.25)',  # 金色发光
    'offset': (0, 6),
    'radius': 16,
}
# 导航栏阴影
NAVBAR_SHADOW = {
    'color': 'rgba(0, 0, 0, 0.5)',
    'offset': (0, 2),
    'radius': 4,
}
```

### 4.3 圆角与间距系统统一

| 层级 | 圆角 | 用途 |
|------|------|------|
| RADIUS_SM | `6px` | 输入框、按钮、标签 |
| RADIUS | `10px` | 卡片、分组容器 |
| RADIUS_LG | `14px` | 四柱色块、大卡片 |
| RADIUS_XL | `18px` | 九宫格外框、全屏弹窗 |

> **注**：当前 `Spacing` 类已定义这四个常量，只需统一引用，禁止再出现硬编码数值。

---

## 5. 导航栏改造

### 5.1 现状

当前导航栏为 4 个水平排列的 `QPushButton`，使用 `Stylesheets.NAVBAR_BUTTON`，选中态为纯金色背景，风格偏通用 Web 按钮。

### 5.2 改造方案

#### 任务 5.1：导航栏改为竖排侧边栏（推荐方案 A）

**设计理由**：
- 横向导航在 1100px 窄屏下 4 个按钮挤在一起，可读性差
- 竖排侧边栏是专业命理工具（文墨天机、时空八字）的通用布局
- 释放顶部空间给应用标题和品牌标识
- 左侧导航栏与左侧输入面板天然合并为统一"左栏"，视觉更紧凑

**改动范围**：`ui/main_window.py` + `ui/styles.py`

**具体实现**：

```
原布局：
┌─────────────────────────────────────────┐
│ [☯] 风水排盘专业工具    [八字][梅花][六壬][玄空] [⚙] [?] │
├──────────────┬──────────────────────────┤
│  输入面板    │     结果面板             │
│  (34%)      │      (66%)               │
└──────────────┴──────────────────────────┘

新布局：
┌────────┬────────────────────────────────┐
│ [☯]品牌 │                                │
│        │                                │
│ 八字排盘│         结果面板              │
│ 梅花易数│         (全高)                │
│ 大六壬  │                                │
│ 玄空飞星│                                │
│        │                                │
│ [⚙]设置 │                                │
│ [?]关于 │                                │
└────────┘────────────────────────────────┘
```

**侧边栏规范**（宽度固定 72px，紧凑型）：

```python
# styles.py 新增 NAV_SIDEBAR 样式
NAV_SIDEBAR = f"""
    QFrame {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {Colors.BG}, stop:1 {Colors.BG_DARK});
        border-right: 1px solid {Colors.DIVIDER};
    }}
"""
NAV_SIDEBAR_BUTTON = f"""
    QPushButton {{
        background: transparent;
        color: {Colors.TEXT3};
        border: none;
        border-radius: {Spacing.RADIUS};
        font-size: 12px;
        font-family: {Fonts.BODY};
        padding: 8px 0px;
        min-height: 44px;
        text-align: left;
        qproperty-icon-size: 20x20;
    }}
    QPushButton:hover {{
        color: {Colors.TEXT};
        background: {Colors.HOVER};
    }}
    QPushButton:checked {{
        color: {Colors.LIUJIN};
        background: {Colors.QINGHUA_GLOW};
        border-left: 3px solid {Colors.LIUJIN};
        padding-left: 9px;      /* 补偿左边框宽度 */
        font-weight: {Fonts.W_MEDIUM};
    }}
"""
NAV_SIDEBAR_ICON = f"""
    font-size: 20px;
    color: {Colors.LIUJIN};
"""
NAV_SIDEBAR_DIVIDER = f"background-color: {Colors.DIVIDER}; height: 1px;"
```

**main_window.py 改动要点**：

```python
def _init_ui(self):
    # 移除原 QSplitter 左右分栏
    # 改为：左侧 Sidebar + 右侧主内容区 QSplitter
    
    main_layout = QHBoxLayout(self)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)
    
    # 1. 左侧边栏 (72px)
    self.sidebar = QFrame()
    self.sidebar.setFixedWidth(72)
    self.sidebar.setStyleSheet(Stylesheets.NAV_SIDEBAR)
    sidebar_layout = QVBoxLayout(self.sidebar)
    sidebar_layout.setContentsMargins(0, 12, 0, 12)
    sidebar_layout.setSpacing(4)
    
    # 品牌 Logo 区
    logo_lbl = QLabel('☯')
    logo_lbl.setAlignment(Qt.AlignCenter)
    logo_lbl.setStyleSheet(Stylesheets.NAVBAR_ICON_BUTTON)
    logo_lbl.setFixedHeight(36)
    sidebar_layout.addWidget(logo_lbl)
    
    sidebar_layout.addStretch(1)  # 弹性空间
    
    # 导航按钮组
    for nav_item in NAV:
        btn = QPushButton(nav_item['icon'])
        btn.setToolTip(nav_item['name'])
        btn.setCheckable(True)
        btn.setStyleSheet(Stylesheets.NAV_SIDEBAR_BUTTON)
        btn.setFixedSize(72, 44)
        btn.setIconSize(QSize(24, 24))
        btn.setObjectName(nav_item['id'])
        btn.clicked.connect(lambda checked, nid=nav_item['id']: self._switch(nid))
        sidebar_layout.addWidget(btn)
    
    sidebar_layout.addStretch(1)  # 弹性空间
    
    # 底部工具按钮
    settings_btn = QPushButton('⚙')
    settings_btn.setToolTip('设置')
    settings_btn.setStyleSheet(Stylesheets.NAV_SIDEBAR_BUTTON)
    settings_btn.setFixedSize(72, 36)
    settings_btn.clicked.connect(self._on_settings)
    sidebar_layout.addWidget(settings_btn)
    
    about_btn = QPushButton('?')
    about_btn.setToolTip('关于')
    about_btn.setStyleSheet(Stylesheets.NAV_SIDEBAR_BUTTON)
    about_btn.setFixedSize(72, 36)
    about_btn.clicked.connect(self._on_about)
    sidebar_layout.addWidget(about_btn)
    
    main_layout.addWidget(self.sidebar)
    
    # 2. 右侧主内容区
    self.main_splitter = QSplitter(Qt.Horizontal)
    self.main_splitter.setChildrenCollapsible(False)
    
    # 原左栏输入面板 (28%，比原来 34% 稍窄，因为侧边栏已承担导航)
    self.input_stack = QStackedWidget()
    self._build_left()
    self.main_splitter.addWidget(self.input_stack)
    
    # 原右栏结果面板
    self.result_stack = QStackedWidget()
    self._build_right()
    self.main_splitter.addWidget(self.result_stack)
    
    self.main_splitter.setSizes([320, 1080])  # 默认比例
    main_layout.addWidget(self.main_splitter)
    
    self.setCentralWidget(self.main_splitter)
```

#### 备选方案 B：顶部导航优化（如果侧边栏改动量过大）

仅优化现有水平导航栏视觉风格：
- 导航按钮加 icon + text 上下排列（图标在上，文字在下）
- 选中态改为底部金色横线指示器（而非全背景填充）
- 添加导航栏底部阴影 `QGraphicsDropShadowEffect`
- 按钮间距扩大至 4px，字号缩小至 12px

> **推荐方案 A**，方案 B 作为降级方案保留在代码注释中。

### 5.3 验收标准

- [ ] 导航栏高度在 1100px 宽屏上不拥挤，4 个模块名称清晰可辨
- [ ] 侧边栏选中态有金色左边框指示器，视觉焦点明确
- [ ] 切换模块时，左右面板同步刷新，无闪烁
- [ ] 品牌 Logo 区与导航按钮区有适当弹性空间分布
- [ ] 设置/关于按钮固定在侧边栏底部

---

## 6. 输入面板改造

### 6.1 八字输入面板（`input_panel.py`）

#### 任务 6.1.1：表单分组重构

将当前线性表单重构为三个语义分组卡片，提升信息层次：

```
┌─────────────────────────────┐
│ ☯  基本信息                   │
│ 姓名：[___________]          │
│ 性别：[♂ 男] [♀ 女]          │
│ 历法：[公历] [农历]           │
│ 日期：[2026-09-22 ▼]         │
│ 时辰：[午时 (11:00~13:00) ▼]  │
│ 时间：[12:00]                │
├─────────────────────────────┤
│ ☯  地点与偏好                 │
│ 出生地：[_________________]   │
│ 流派：[子平真诠 ▼]            │
├─────────────────────────────┤
│ ☯  备注                       │
│ [_______________________]    │
│ [_______________________]    │
├─────────────────────────────┤
│ [开始排盘        ] [重置     ] │
└─────────────────────────────┘
```

**改动要点**：
- 使用 `CollapsibleCard` 包裹每组（默认展开）
- 每组卡片左侧使用 `accent_color=Colors.QINGHUA` 区分
- 分组标题使用 `Fonts.TITLE` 宋体
- 标签列宽从固定 42px 改为动态计算（最长标签"出生地"需 48px）

#### 任务 6.1.2：时辰选择优化

当前时辰下拉框显示 `"子时 (23:00~01:00)"` 长文本，在窄屏下换行。

**方案**：时分双输入控件替换单一下拉框：
- 时：下拉框（0-23）
- 分：数字输入框（0-59）
- 关联显示对应时辰名称（实时计算并显示）

```python
# 新增属性
self.hour_spin = QSpinBox()       # 时 0-23
self.minute_spin = QSpinBox()     # 分 0-59
self.hour_label = QLabel('午时 (11:00~13:00)')  # 实时映射
```

#### 任务 6.1.3：真太阳时信息显示

在输入面板底部添加"时间校准"区域（默认折叠），显示：
- 原始出生时间
- 经度时差修正
- 真太阳时结果

> 该区域由 `_build_true_solar_section()` 方法实现，通过 `true_solar_switch` 现有兼容字段驱动显示/隐藏。

### 6.2 梅花易数输入面板（`meihua_input.py`）

#### 任务 6.2.1：起卦方式选择器升级

当前使用按钮组切换 6 种方式，视觉扁平。

**升级方案**：
- 顶部改为横向 Tab 式选择器（`QTabWidget` 或自定义 `QFrame` 标签组）
- 每个 Tab 含图标 + 文字（如时间起卦 ⏰、铜钱摇卦 🪙）
- 选中 Tab 底部金色下划线指示器

#### 任务 6.2.2：方位罗盘可视化

当前方位罗盘仅 3×3 布局文字，升级为带图形化的罗盘：
- 使用 QPainter 绘制八卦方位罗盘（后天八卦方位）
- 8 个方位按钮围绕罗盘环形排列
- 点击方位后高亮选中格

### 6.3 大六壬输入面板（`liuren_input.py`）

#### 任务 6.3.1：九宗门选择器优化

将九宗门（干前三传/支前三传/比用/涉害/遥克/昴星/别责/八专/伏吟）改为分组单选卡片：

```
┌── 取法分类 ──────────────────────┐
│ [有支贼日] [有日贼支] [比用]      │
│ [涉害]   [遥克]   [昴星]         │
│ [别责]   [八专]   [伏吟]         │
└─────────────────────────────────┘
```

每组 3 个卡片按钮，选中态鎏金边框 + 浅金背景。

### 6.4 玄空飞星输入面板（`xuan_kong_input.py`）

#### 任务 6.4.1：坐向选择器可视化

当前坐向为下拉框，升级为：
- 24 山向环形选择器（QPainter 绘制圆形罗盘）
- 点击罗盘上的山向即选中
- 显示当前选中山的度数范围

---

## 7. 结果面板改造

### 7.1 通用结果面板升级（所有模块）

#### 任务 7.1.1：顶部工具栏响应式优化

当前工具栏按钮（刷新/复制/导出/收起全部）在窄屏下溢出。

**方案**：
- 工具栏改为可折叠：超过 3 个按钮时自动折叠为"⋯ 更多"下拉菜单
- 核心按钮（刷新、AI 分析）始终可见
- 按钮图标统一使用 Unicode 字符替代 emoji，确保跨平台一致性

```python
# 替换 emoji 为 Unicode 字符
# '🤖 重新分析' → '⚡ 智能分析'
# '📋 复制' → '⎘ 复制'
# '📤 导出' → '⤓ 导出'
# '✕ 取消' → '✗ 取消'
```

#### 任务 7.1.2：卡片间距与分隔线统一

当前卡片间距 16px，分隔线样式不一致。

**统一规范**：
- 卡片间距：`Spacing.GAP = 14px`
- 卡片内边距：`Spacing.PAD = 20px`
- 卡片间分隔线：仅在相邻卡片间显示，使用 `Colors.DIVIDER` 1px 横线
- 所有卡片统一添加 `QGraphicsDropShadowEffect`（参考 4.2 节）

### 7.2 八字结果面板（`result_panel.py`）

#### 任务 7.2.1：四柱展示升级

当前四柱为 4 个竖向色块，升级为**专业命盘格**：

```
┌─────────────────────────────────────────────────────┐
│           年柱          │           月柱             │
│    丙  (火)  申 (金)    │    丁  (火)  酉 (金)       │
│    赤  ······  白       │    赤  ······  白         │
│    天干·地支            │    天干·地支               │
│                                                     │
│  藏干：戊庚壬          │  藏干：辛                   │
│  十神：比肩            │  十神：劫财                 │
│  纳音：山下火          │  山下火                     │
│  空亡：辰巳            │  空亡：——                   │
├─────────────────────────────────────────────────────┤
│           日柱 ★      │           时柱             │
│    日主：戊 (土) ◉     │    戊  (土)  午 (火)       │
│    坐支：午 (帝旺)     │    赤  ······  朱           │
│                                                     │
│  藏干：丁己            │  藏干：丁                   │
│  十神：比肩            │  十神：比肩                 │
│  纳音：天上火          │  天上火                     │
│  空亡：寅卯            │  空亡：——                   │
└─────────────────────────────────────────────────────┘
```

**改动要点**：
- 日柱使用 `QFrame` 白色渐变背景 + 金色边框突出显示
- 天干地支色块尺寸改为响应式（根据可用宽度自适应，最小 32px，最大 48px）
- 藏干/十神/纳音/空亡用小标签行内展示（`tag_badge` 样式）
- 使用 `ResponsiveFlow(min_item_width=280, max_cols=2, min_cols=1)` 响应式两列布局

#### 任务 7.2.2：五行分析可视化升级

当前五行分析为彩色标签 + 百分比数字 + 进度条。

**升级方案**：增加横向条形能量图 + 五行相生关系图：

```
木 ████████████░░░░ 62.3%  [旺]
火 █████████████░░░ 71.5%  [旺]
土 ████████░░░░░░░░ 40.2%  [中和]
金 ███████░░░░░░░░░ 35.8%  [弱]
水 ██████░░░░░░░░░░ 28.4%  [弱]
```

每行右侧显示旺/中/弱标注（颜色对应：旺=朱红，中=古金，弱=靛蓝）。

#### 任务 7.2.3：神煞系统可视化

当前神煞为列表形式。升级为分类卡片组：

```
┌─ 吉神 ──────────────────────────┐
│ [天乙贵人] [文昌] [天德] [月德]  │
├─ 凶煞 ──────────────────────────┤
│ [驿马] [劫煞] [咸池]             │
└─────────────────────────────────┘
```

每个神煞为带颜色边框的小标签：吉神=绿色边框，凶煞=红色边框。

#### 任务 7.2.4：地支关系可视化

当前为文字列表（子午冲、丑未冲...）。升级为关系图：

```
    子 ───冲─── 午
    │           │
  六合        六害
    │           │
    丑 ───刑─── 戌
```

使用 QPainter 绘制地支关系图，冲/合/刑/害 用不同颜色箭头区分。

### 7.3 运程总结卡片升级

将四段运程（事业/财运/健康/感情）从文字卡片升级为：

```
┌─ 运程总览 ────────────────────────────────┐
│ 事业  ████████████░░░░  80% 吉     │
│ 财运  █████████░░░░░░░  65% 平     │
│ 健康  ████████░░░░░░░░░ 50% 注意   │
│ 感情  ███████████░░░░░  70% 吉     │
└──────────────────────────────────────────┘
```

每个维度带进度条 + 吉凶标签，下方附简短说明文字。

---

## 8. AI 解读区改造

### 8.1 现状

AI 解读区由 `ai_analysis_renderer.py` 统一渲染，`render_analysis()` 方法根据 `pan_type` 分发。当前存在以下问题：
- "龙虎山大师兄分析"标题风格与其他卡片不一致
- 三段式内容（格局总评/分项分析/建议与注意事项）视觉层次不够分明
- 免责声明与正文混排，不够醒目

### 8.2 改造方案

#### 任务 8.1：AI 解读区 Hero 标题升级

```
┌═══════════════════════════════════════════════════┐
│  ⚡  龙虎山大师兄 · 深度解读                        │
│  基于《子平真诠》《滴天髓》等古籍参校分析          │
└───────────────────────────────────────────────────┘
```

**实现**：在 `ai_analysis_renderer.py` 的 `conclusion_hero` 模式渲染中：
- 左侧金色竖条 + ⚡ 图标
- 副标题使用 `Fonts.SZ_SMALL` 灰色文字，显示参与分析的古籍名称
- 使用 `CollapsibleCard(accent_color=Colors.LIUJIN)` 包裹

#### 任务 8.2：三段式内容视觉分层

| 层级 | 视觉处理 | 颜色 |
|------|---------|------|
| 格局总评 | 大标题 + 摘要文字，加粗 | LIUJIN 鎏金 |
| 分项分析 | 子标题 + 内容，列表展示 | TEXT 白色 |
| 建议与注意事项 | 引用块样式（左侧金色竖线） | QINGHUA 古金 |

**实现**：在 `ai_analysis_renderer.py` 中为三种章节模式分别定义样式：

```python
# 格局总评 - 大字强调
SECTION_TITLE_STYLE = f"font-size: 15px; font-weight: {Fonts.W_BOLD}; color: {Colors.LIUJIN}; font-family: {Fonts.TITLE};"

# 分项分析 - 标准正文
SECTION_BODY_STYLE = f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; line-height: 1.7;"

# 建议块 - 引用样式
ADVICE_BLOCK_STYLE = f"""
    background: {Colors.QINGHUA_GLOW};
    border-left: 3px solid {Colors.QINGHUA};
    padding: 10px 14px;
    border-radius: 0 {Spacing.RADIUS_SM} {Spacing.RADIUS_SM} 0;
"""
```

#### 任务 8.3：免责声明醒目化

当前免责声明在文字末尾混排，升级为首段引用块样式，使用醒目的警告图标和颜色：

```
⚠  本解读仅供文化研究参考，不构成任何决策依据。
   涉及健康/法律/投资等重大事项，请咨询相关专业人士。
```

**实现**：在 `ai_analysis_renderer.py` 的 `disclaimer` 模式渲染中使用 `Colors.WARNING` 色 + 加粗边框卡片。

#### 任务 8.4：古籍引用标注

当 AI 输出包含古籍引用时（如"《子平真诠》云：……"），在文字中自动高亮标注：

```
  日主【戊土】生于酉月， 【《子平真诠》云："戊土固重，既中且正"】
  得令而旺，……
```

**实现**：在 `ai_analysis_renderer.py` 渲染前，用正则匹配 `《[^》]+》` 模式，为匹配文本添加特殊样式（斜体 + 古金色）。

---

## 9. 玄空飞星九宫格升级

### 9.1 现状

`xuan_kong_result_panel.py` 中九宫格 Canvas 区域当前仅占位，显示文字"九宫飞星盘"，无实际绘制。

### 9.2 改造方案

#### 任务 9.1：实现完整的 QPainter 九宫格绘制

绘制规范：
- 3×3 网格，中宫略大（洛书格局）
- 每宫展示：宫位名（如"巽"）、山星数、向星数、运星数
- 五行属性用背景色标（木=绿、火=红、土=黄、金=白、水=蓝）
- 吉星（一白/六白/八白）用朱红标注数字
- 凶星（二黑/三碧/五黄/七赤）用黑色标注数字
- 生克关系用箭头连线（可选项：鼠标悬停显示）

**核心绘制代码结构**：

```python
def _draw_flying_star_grid(self, painter: QPainter, result: dict):
    """绘制玄空飞星九宫格
    
    洛书九宫方位：
    巽(4)  离(9)  坤(2)
    震(3)  中(5)  兑(7)
    艮(8)  坎(1)  乾(6)
    """
    # 1. 绘制九宫外框
    # 2. 绘制每个宫位（含五行背景色）
    # 3. 绘制山星/向星/运星数字
    # 4. 绘制吉凶颜色标注
    # 5. 绘制生克关系箭头（可选）
```

#### 任务 9.2：宫位鼠标悬停交互

鼠标悬停在某个宫位时：
- 高亮该宫边框（金色）
- 弹出 ToolTip 显示该宫详细解读
- 联动右侧文字详情区滚动到对应位置

#### 任务 9.3：流年飞星叠加切换

添加年份切换按钮组（当前运 + 未来 9 年流年），点击切换显示对应年份的飞星叠加盘。

---

## 10. 梅花易数结果面板升级

### 10.1 任务 10.1：卦象演变流程图

当前卦象展示为静态卡片（本卦/互卦/变卦/错卦/综卦）。升级为流程图式布局：

```
  本卦          互卦          变卦
┌──────┐      ┌──────┐      ┌──────┐
│ ☲离  │ ──▶ │ ☷坤  │ ──▶ │ ☱兑  │
│ 离上离下│    │ 坤上坤下│    │ 兑上坤下│
└──────┘      └──────┘      └──────┘
                            │
                       动爻：▅▅  ▅▅  (六三)
```

使用箭头连接三个卦象，动爻位置用高亮标注。

### 10.2 任务 10.2：体用生克关系可视化

将体用生克关系从文字描述升级为图形：
- 体卦（主方）用金色边框
- 用卦（客方）用朱砂边框
- 中间显示生克关系箭头（相生=绿色↑，相克=红色↔）

---

## 11. 大六壬结果面板升级

### 11.1 任务 11.1：天地盘可视化

当前天地盘为 12 宫位响应式流布局。升级为圆形罗盘式绘制：
- 12 地支环形排列（子北/午南/卯东/酉西）
- 天盘地支覆盖在地盘之上，可看到重叠关系
- 四课三传用颜色高亮标注

### 11.2 任务 11.2：三传展示升级

当前三传为文字列表。升级为：
```
初传（发用）──▶ 中传（传干）──▶ 末传（归宅）
  [庚午]         [丙子]         [壬午]
   ▓▓▓           ░░░           ░░░
  鎏金高亮      古金标注       靛蓝标注
```

---

## 12. 对话框组件升级

### 12.1 设置对话框（`settings_dialog.py`）

**改造要点**：
- 使用 `CollapsibleCard` 包裹各设置分组（AI 配置/显示设置/数据管理）
- AI 密钥输入框改为密码模式（默认隐藏，点击眼睛图标显示）
- 连接测试按钮添加加载动画（TaijiSpinner）
- 密钥存储状态显示加密方式说明（设备绑定 XOR+Base64）

### 12.2 关于对话框（`about_dialog.py`）

**改造要点**：
- HaloAvatarWidget 呼吸动画速率从 3s 缩短为 2s，增强存在感
- WaveDivider 波浪颜色从默认改为 GLOW 透明度 0.15
- 版本信息增加 Git commit hash（调试版）
- 联系方式按钮增加图标（QQ/手机/邮箱）

### 12.3 导出对话框（`export_dialog.py`）

**改造要点**：
- 格式选择从单选按钮组改为图标卡片（CSV/Excel/PDF 三个大方块）
- 章节勾选改为分组折叠卡片（基础信息/命局分析/运程/AI解读）
- 文件预览区域增加格式说明文字（如"PDF 适合打印分享，Excel 适合数据分析"）

---

## 13. 导出系统升级

### 13.1 任务 13.1：PDF 报告模板升级

当前 PDF 使用 reportlab 两列表格，升级为正式报告格式：

```
封面：
  ┌─────────────────────────────┐
  │                             │
  │      ☯ 风水排盘专业工具      │
  │      KP-AI-FENGSHUI v5.0.6 │
  │                             │
  │   姓名：张三   性别：男      │
  │   公历：2026-09-22 12:00    │
  │   真太阳时：11:47           │
  │                             │
  │   八字：丙午 丁酉 戊午 戊午  │
  │                             │
  │   报告生成时间：2026-09-22   │
  │   仅供文化研究参考           │
  └─────────────────────────────┘

目录页：
  一、基本信息 ............ 1
  二、命局类型 ............ 2
  三、四柱详析 ............ 3
  四、五行分析 ............ 5
  ...
```

**改动**：`ui/export/pdf_exporter.py` — 重写 `generate_report()` 方法，增加封面页、目录页、分章节分页。

### 13.2 任务 13.2：Excel 报告升级

- A 列标签改为金色背景 + 白色文字
- B 列数值改为斑马纹（奇偶行不同底色）
- 吉凶批注行颜色按 type 着色（凶=朱红底，吉=绿底，中=橙底）
- 新增"五行分析"工作表，带条件格式色阶图

### 13.3 任务 13.3：CSV 导出补充

- 补充 UTF-8-SIG BOM（已实现，确认无误）
- 新增多工作表支持（八字/梅花/六壬分别导出到不同 sheet）

---

## 14. 交互与动效规范

### 14.1 页面切换动画

模块切换时（点击导航按钮），左右面板切换使用淡入淡出动画：

```python
def _switch(self, nav_id):
    # 隐藏当前面板，添加淡出动画
    current = self.input_stack.currentWidget()
    if current:
        opacity = QGraphicsOpacityEffect(current)
        current.setGraphicsEffect(opacity)
        anim = QPropertyAnimation(opacity, b"opacity")
        anim.setDuration(150)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.finished.connect(lambda: self.input_stack.setCurrentWidget(...))
        anim.start()
    # 新面板淡入
    ...
```

### 14.2 卡片入场动画

排盘完成后，结果卡片逐个淡入（50ms 延迟递增）：

```python
def _fade_in_cards(self, cards: List[CollapsibleCard]):
    for i, card in enumerate(cards):
        card.setStyleSheet(f"opacity: 0;")
        QTimer.singleShot(i * 50, lambda c=card: self._animate_opacity(c, 1.0))
```

### 14.3 按钮点击反馈

所有交互按钮添加点击微缩放动画（scale 0.95 → 1.0，时长 100ms）：

```python
def _click_feedback(self, btn: QPushButton):
    orig_scale = btn.scale
    btn.setScale(0.95)
    QTimer.singleShot(100, lambda: btn.setScale(orig_scale))
```

### 14.4 加载状态

AI 分析中显示 TaijiSpinner 旋转动画 + 轮播提示语：
- "正在参详命理..."
- "古籍引证中..."
- "五行推演中..."
- "格局分析中..."

轮播间隔 2 秒，3 个提示语循环。

---

## 15. 实施步骤与优先级

### 阶段一：视觉基础层（优先级 P0）

| 编号 | 任务 | 涉及文件 | 预估工作量 |
|------|------|---------|-----------|
| T1.1 | 扩展 `styles.py` 色彩与阴影体系 | `ui/styles.py` | 0.5h |
| T1.2 | 四柱展示响应式色块尺寸改造 | `ui/components/result_panel.py` | 2h |
| T1.3 | 卡片统一阴影效果注入 | `ui/components/collapsible_card.py` | 1h |
| T1.4 | 工具栏 emoji→Unicode 字符替换 | 所有 `*_result_panel.py` | 1h |

### 阶段二：导航与布局层（优先级 P1）

| 编号 | 任务 | 涉及文件 | 预估工作量 |
|------|------|---------|-----------|
| T2.1 | 顶部导航栏改为竖排侧边栏 | `ui/main_window.py` | 4h |
| T2.2 | 左右分栏比例自适应（1100px 以下切换布局） | `ui/main_window.py` | 2h |
| T2.3 | 页面切换淡入淡出动画 | `ui/main_window.py` | 1.5h |

### 阶段三：输入面板层（优先级 P1）

| 编号 | 任务 | 涉及文件 | 预估工作量 |
|------|------|---------|-----------|
| T3.1 | 八字输入面板分组卡片重构 | `ui/components/input_panel.py` | 2h |
| T3.2 | 时辰时分双输入控件 | `ui/components/input_panel.py` | 1h |
| T3.3 | 梅花易数 Tab 式起卦方式选择器 | `ui/components/meihua_input.py` | 2h |
| T3.4 | 大六壬九宗门卡片选择器 | `ui/components/liuren_input.py` | 1.5h |
| T3.5 | 玄空飞星 24 山向罗盘选择器 | `ui/components/xuan_kong_input.py` | 3h |

### 阶段四：结果面板层（优先级 P1）

| 编号 | 任务 | 涉及文件 | 预估工作量 |
|------|------|---------|-----------|
| T4.1 | 八字结果：四柱专业命盘格 | `ui/components/result_panel.py` | 4h |
| T4.2 | 八字结果：五行能量条形图 | `ui/components/result_panel.py` | 2h |
| T4.3 | 八字结果：神煞分类标签组 | `ui/components/result_panel.py` | 1.5h |
| T4.4 | 八字结果：地支关系图 | `ui/components/result_panel.py` | 3h |
| T4.5 | 八字结果：运程进度条可视化 | `ui/components/result_panel.py` | 1.5h |
| T4.6 | 玄空飞星：完整九宫格 QPainter 绘制 | `ui/components/xuan_kong_result_panel.py` | 4h |
| T4.7 | 梅花易数：卦象演变流程图 | `ui/components/meihua_result_panel.py` | 2.5h |
| T4.8 | 大六壬：天地盘罗盘绘制 | `ui/components/liuren_result_panel.py` | 3h |

### 阶段五：AI 解读层（优先级 P2）

| 编号 | 任务 | 涉及文件 | 预估工作量 |
|------|------|---------|-----------|
| T5.1 | AI 解读 Hero 标题升级 | `ui/components/ai_analysis_renderer.py` | 1h |
| T5.2 | 三段式内容视觉分层 | `ui/components/ai_analysis_renderer.py` | 1.5h |
| T5.3 | 免责声明醒目化 | `ui/components/ai_analysis_renderer.py` | 0.5h |
| T5.4 | 古籍引用自动高亮 | `ai/interpret_pipeline.py` | 1h |

### 阶段六：对话框与导出层（优先级 P2）

| 编号 | 任务 | 涉及文件 | 预估工作量 |
|------|------|---------|-----------|
| T6.1 | 设置对话框升级 | `ui/components/settings_dialog.py` | 2h |
| T6.2 | 关于对话框升级 | `ui/components/about_dialog.py` | 1h |
| T6.3 | 导出对话框升级 | `ui/components/export_dialog.py` | 1.5h |
| T6.4 | PDF 报告模板升级（封面+目录） | `ui/export/pdf_exporter.py` | 3h |
| T6.5 | Excel 报告升级（斑马纹+色阶） | `ui/export/excel_exporter.py` | 2h |

### 阶段七：动效与细节层（优先级 P3）

| 编号 | 任务 | 涉及文件 | 预估工作量 |
|------|------|---------|-----------|
| T7.1 | 页面切换淡入淡出动画 | `ui/main_window.py` | 1.5h |
| T7.2 | 卡片入场逐条淡入动画 | `ui/components/result_panel.py` | 1h |
| T7.3 | 按钮点击微缩放反馈 | `ui/styles.py` + 全局 | 1h |
| T7.4 | AI 加载状态轮播提示语 | `ui/components/collapsible_card.py` | 0.5h |
| T7.5 | 空状态页面引导动效 | `ui/components/result_panel.py` | 1h |

---

## 16. 验收标准

### 16.1 功能验收

| # | 检查项 | 通过标准 |
|---|-------|---------|
| F1 | 八字排盘核心功能 | 输入合法数据后，四柱、五行、十神、大运流年全部正确计算，与升级前一致 |
| F2 | 梅花易数起卦 | 6 种起卦方式均能正常生成卦象，与本升级前行为一致 |
| F3 | 大六壬起课 | 九宗门取法正确，天地盘/四课/三传完整输出 |
| F4 | 玄空飞星排盘 | 九宫格正确绘制，山星/向星/运星数据准确 |
| F5 | AI 解读功能 | AI 分析按钮正常触发，输出内容与升级前一致 |
| F6 | 导出功能 | PDF/Excel/CSV 导出正常，文件格式可用 |
| F7 | 设置功能 | AI 配置修改后热更新生效，无需重启 |
| F8 | 历史记录持久化 | 窗口几何/分栏比例/最近模块重启后自动还原 |

### 16.2 视觉验收

| # | 检查项 | 通过标准 |
|---|-------|---------|
| V1 | 色彩体系一致性 | 全界面仅使用 `styles.py` Colors 类定义的色值，无硬编码颜色 |
| V2 | 字体体系一致性 | 标题统一使用 KaiTi/SimSun，正文使用 Microsoft YaHei |
| V3 | 圆角一致性 | 所有容器使用 Spacing 类定义的 RADIUS_* 常量 |
| V4 | 导航清晰度 | 侧边栏选中态有明确金色指示器，4 个模块图标+文字清晰可辨 |
| V5 | 四柱突出显示 | 日柱使用金色边框+浅色背景，明显区别于其他三柱 |
| V6 | 五行颜色规范 | 木绿/火红/土黄/金白/水蓝五色统一，无偏离 |
| V7 | 吉凶颜色规范 | 吉星朱红、凶星黑色/靛蓝，无混乱 |
| V8 | 窄屏适配 | 窗口缩小至 1100×700 时，内容不溢出、不裁剪、可正常操作 |

### 16.3 性能验收

| # | 检查项 | 通过标准 |
|---|-------|---------|
| P1 | 启动时间 | 冷启动到界面完全渲染 ≤ 3 秒 |
| P2 | 排盘响应 | 单次八字排盘 UI 渲染 ≤ 500ms |
| P3 | AI 分析响应 | AI 分析首帧渲染（流式输出第一行）≤ 5 秒 |
| P4 | 内存占用 | 空闲态内存 ≤ 200MB，排盘完成 ≤ 300MB |
| P5 | 动画帧率 | 所有动画效果 ≥ 55fps（无掉帧卡顿） |

### 16.4 兼容性验收

| # | 检查项 | 通过标准 |
|---|-------|---------|
| C1 | Windows 10/11 | 在所有主流分辨率下正常运行 |
| C2 | Python 3.10+ | 依赖版本不降级 |
| C3 | PySide6 6.9-6.11 | 样式表语法兼容 |
| C4 | 打包产物 | PyInstaller 打包后界面正常渲染 |

---

## 附录 A：关键文件索引

| 文件路径 | 职责 | 本次升级涉及程度 |
|---------|------|---------------|
| `ui/main_window.py` | 主窗口布局/导航/信号绑定 | 高（导航改造+布局调整） |
| `ui/styles.py` | 全局样式/色彩/字体/间距常量 | 高（新增色彩+阴影+侧边栏样式） |
| `ui/components/input_panel.py` | 八字输入面板 | 中（分组重构+时分控件） |
| `ui/components/result_panel.py` | 八字结果面板 | 高（四柱升级+五行可视化+关系图） |
| `ui/components/collapsible_card.py` | 共享卡片组件 | 中（阴影注入+入场动画） |
| `ui/components/timeline.py` | 大运流年时间轴 | 低（微调样式） |
| `ui/components/meihua_input.py` | 梅花易数输入面板 | 中（Tab 选择器+罗盘） |
| `ui/components/meihua_result_panel.py` | 梅花易数结果面板 | 中（卦象流程图） |
| `ui/components/liuren_input.py` | 大六壬输入面板 | 中（九宗门卡片） |
| `ui/components/liuren_result_panel.py` | 大六壬结果面板 | 中（天地盘罗盘） |
| `ui/components/xuan_kong_input.py` | 玄空飞星输入面板 | 中（24山罗盘） |
| `ui/components/xuan_kong_result_panel.py` | 玄空飞星结果面板 | 高（九宫格绘制） |
| `ui/components/ai_analysis_renderer.py` | AI 解读渲染器 | 中（三段式视觉分层） |
| `ui/components/ai_analysis_worker.py` | AI 分析线程 | 低（无改动） |
| `ui/components/settings_dialog.py` | 设置对话框 | 中（密码模式+加载动画） |
| `ui/components/about_dialog.py` | 关于对话框 | 低（微动效优化） |
| `ui/components/export_dialog.py` | 导出对话框 | 中（图标卡片选择） |
| `ui/export/pdf_exporter.py` | PDF 导出 | 高（封面+目录页） |
| `ui/export/excel_exporter.py` | Excel 导出 | 中（斑马纹+色阶） |
| `ui/export/csv_exporter.py` | CSV 导出 | 低（确认无误） |
| `ai/interpret_pipeline.py` | AI 解读管道 | 低（古籍引用高亮） |
| `core/bazi/bazi_calculator.py` | 八字核心算法 | 无（禁止修改） |
| `core/divination/meihua.py` | 梅花易数算法 | 无（禁止修改） |
| `core/divination/liuren.py` | 大六壬算法 | 无（禁止修改） |
| `core/fengshui/xuan_kong.py` | 玄空飞星算法 | 无（禁止修改） |

---

## 附录 B：设计系统常量速查

### 色彩速查

```
深靛蓝 INK          #1a1a2e  — 主背景
深靛蓝 DARK         #12121f  — 次级背景
卡片 CARD           #21213a  — 卡片背景
悬停 HOVER          #262640  — 悬停背景
选中 SELECTED       #2c2c4e  — 选中背景
边框 BORDER         #33335A  — 卡片边框
分割线 DIVIDER      #2E2E4C  — 分割线

古金 QINGHUA        #c9a227  — 强调/选中/导航
古金 LIGHT          #e8d08a  — 悬停高亮
鎏金 LIUJIN         #c9a227  — AI解读/日柱高亮

朱红 ZHUSHA         #8b0000  — 主操作按钮/吉星
朱红 LIGHT          #C97A6A  — 悬停
朱红 GLOW           rgba(139,0,0,0.25)

文字 TEXT           #F5F1E8  — 主要文字
文字 TEXT2          #D8D3C8  — 次要文字
文字 TEXT3          #9C97A8  — 三级文字
文字 TEXT4          #6B6678  — 四级/禁用文字

五行 WOOD           #7CB48E  — 木
五行 FIRE           #E88870  — 火
五行 EARTH          #C0A878  — 土
五行 METAL          #B8B0A0  — 金
五行 WATER          #8AC8E8  — 水
```

### 字号速查

```
HERO     20px  — 大标题
TITLE    17px  — 章节标题
SECTION  15px  — 小组标题
BODY     13px  — 正文
SMALL    12px  — 辅助文字
MICRO    11px  — 标签/注释
```

---

> **免责声明**：本方案仅供文化研究与软件工程参考，不构成任何命理决策依据。所有UI升级变更需经过功能回归测试验证后上线。
