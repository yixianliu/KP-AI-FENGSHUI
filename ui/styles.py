"""
风水排盘专业工具 - 精美国风设计系统 v5.0.3
三色点缀：朱砂红·青花蓝·鎏金黄 | 暖米底色 | 圆角卡片 | 柔和阴影 | 微动画
"""


class Colors:
    """全局色彩体系"""

    # ========== 底色系 - 暖米色调 ==========
    BG = '#F7F4EE'
    BG_DARK = '#EDE8DF'
    CARD = '#FFFFFF'
    HOVER = '#F2EEE6'
    CARD_HOVER = '#FAF8F4'
    CARD_SELECTED = '#F0EDE4'

    # ========== 三色点缀 - 国风主题 ==========
    # 朱砂红（主操作）
    ZHUSHA = '#C45545'
    ZHUSHA_LIGHT = '#E8B0A0'
    ZHUSHA_DARK = '#9B3528'
    ZHUSHA_GLOW = 'rgba(196, 85, 69, 0.12)'

    # 青花蓝（导航/选中）
    QINGHUA = '#4A7A90'
    QINGHUA_LIGHT = '#A0C4D4'
    QINGHUA_DARK = '#3A5A6A'
    QINGHUA_GLOW = 'rgba(74, 122, 144, 0.10)'

    # 鎏金黄（高亮/强调）
    LIUJIN = '#B88A30'
    LIUJIN_LIGHT = '#E0D0A0'
    LIUJIN_DARK = '#8B6520'
    LIUJIN_GLOW = 'rgba(184, 138, 48, 0.10)'

    # ========== 文字色彩 ==========
    TEXT = '#1C1A16'
    TEXT2 = '#5C5650'
    TEXT3 = '#8C8680'
    TEXT4 = '#B0AAA4'
    TEXT_INV = '#FFFFFF'

    # ========== 边框与分割 ==========
    BORDER = '#E6E0D8'
    BORDER2 = '#D4CCC0'
    DIVIDER = '#ECE6DC'
    DIVIDER_LIGHT = '#F2EDE4'

    # ========== 状态色彩 ==========
    SUCCESS = '#4A8A5E'
    SUCCESS_LIGHT = '#D4EDDA'
    WARNING = '#C49030'
    WARNING_LIGHT = '#FFF3CD'
    DANGER = '#C45545'
    DANGER_LIGHT = '#F8D7DA'
    INFO = '#4A7A90'
    INFO_LIGHT = '#D1ECF1'

    # ========== 渐变 ==========
    GRADIENT_WARM = '#F7F4EE'
    GRADIENT_COOL = '#EEF2F6'
    GRADIENT_NAV_START = '#FFFFFF'
    GRADIENT_NAV_END = '#FAF8F4'

    # ========== 阴影（用于 QGraphicsDropShadowEffect） ==========
    SHADOW_SM = 'rgba(0,0,0,0.04)'
    SHADOW_MD = 'rgba(0,0,0,0.06)'
    SHADOW_LG = 'rgba(0,0,0,0.10)'

    # ========== 五行色彩 ==========
    WOOD = '#5A8F6E'
    WOOD_LIGHT = '#A0D0B0'
    WOOD_DARK = '#3A6F4E'
    FIRE = '#C45C48'
    FIRE_LIGHT = '#E8A898'
    FIRE_DARK = '#9B3C2A'
    EARTH = '#8B7355'
    EARTH_LIGHT = '#B8A080'
    EARTH_DARK = '#6B5338'
    METAL = '#B8B0A0'
    METAL_LIGHT = '#D8D0C0'
    METAL_DARK = '#8B8070'
    WATER = '#5B8FA8'
    WATER_LIGHT = '#A0C8D8'
    WATER_DARK = '#3B6F88'

    # ========== 旧版兼容别名 ==========
    BACKGROUND = BG
    PRIMARY = QINGHUA
    PRIMARY_LIGHT = QINGHUA_LIGHT
    PRIMARY_DARK = QINGHUA_DARK
    ACCENT = ZHUSHA
    ACCENT_LIGHT = ZHUSHA_LIGHT
    ACCENT_DARK = ZHUSHA_DARK
    HIGHLIGHT = LIUJIN
    HIGHLIGHT_LIGHT = LIUJIN_LIGHT
    HIGHLIGHT_DARK = LIUJIN_DARK
    HIGHLIGHT_GLOW = LIUJIN_GLOW
    TEXT_PRIMARY = TEXT
    TEXT_SECONDARY = TEXT2
    TEXT_TERTIARY = TEXT3
    TEXT_INVERSE = TEXT_INV
    BORDER_LIGHT = DIVIDER
    HOVER_BG = HOVER
    INPUT_BG = CARD
    PARCHMENT = BG
    PARCHMENT_LIGHT = BG
    PARCHMENT_DARK = '#E3D5BC'
    BRONZE = '#6B6B4D'
    BRONZE_LIGHT = '#8A8A68'
    BRONZE_DARK = '#4A4A30'
    WATERMARK = 'rgba(0,0,0,0.02)'


class Fonts:
    """字体体系"""

    # 衬线字体（标题/装饰）
    TITLE = '"Noto Serif CJK SC", "Source Han Serif SC", SimSun, STSong, serif'
    # 无衬线字体（正文/UI）
    BODY = '"Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif'
    # 等宽字体（数据/数值）
    MONO = '"Cascadia Code", "Consolas", "SF Mono", Monaco, monospace'

    # 字号
    SZ_HERO = '20px'
    SZ_TITLE = '17px'
    SZ_SECTION = '15px'
    SZ_BODY = '13px'
    SZ_SMALL = '12px'
    SZ_MICRO = '11px'

    # 字重
    W_LIGHT = '300'
    W_NORMAL = 'Normal'
    W_MEDIUM = '500'
    W_BOLD = '600'

    # 旧版兼容
    FAMILY_CN = BODY
    FAMILY_KAI = TITLE
    FAMILY_SONG = TITLE
    FAMILY_SERIF = TITLE
    FAMILY_EN = MONO
    SIZE_TITLE = SZ_TITLE
    SIZE_SECTION = SZ_SECTION
    SIZE_KEY = '24px'
    SIZE_BODY = SZ_BODY
    SIZE_SMALL = SZ_SMALL
    SIZE_MICRO = SZ_MICRO
    WEIGHT_NORMAL = W_NORMAL
    WEIGHT_BOLD = W_BOLD


class Spacing:
    """间距与圆角体系"""

    RADIUS = '10px'
    RADIUS_SM = '6px'
    RADIUS_LG = '14px'
    RADIUS_XL = '18px'
    PAD = '20px'
    PAD_LG = '28px'
    GAP = '14px'
    GAP_SM = '8px'

    # 旧版兼容
    CARD_RADIUS = RADIUS
    CONTROL_RADIUS = RADIUS_SM
    CARD_PADDING = PAD
    MODULE_GAP = GAP
    LINE_HEIGHT = '1.6'
    LETTER_SPACING = '0.5px'
    CONTROL_VERTICAL_GAP = '12px'
    BUTTON_MIN_HEIGHT = '40px'
    BUTTON_MIN_WIDTH = '100px'


class Stylesheets:
    """全局样式表集合"""

    # ==================== 主窗口 ====================
    MAIN = f"""
        QMainWindow {{
            background-color: {Colors.BG};
        }}
        QWidget {{
            font-family: {Fonts.BODY};
        }}
    """

    # ==================== 卡片 ====================
    CARD = f"""
        QFrame {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS};
        }}
        QFrame:hover {{
            border-color: {Colors.BORDER2};
        }}
    """

    # ==================== 主按钮（朱砂红） ====================
    BTN_PRIMARY = f"""
        QPushButton {{
            background-color: {Colors.ZHUSHA};
            color: {Colors.TEXT_INV};
            border: none;
            border-radius: {Spacing.RADIUS_SM};
            font-size: 14px;
            font-weight: {Fonts.W_MEDIUM};
            font-family: {Fonts.BODY};
            padding: 10px 28px;
            min-height: 40px;
        }}
        QPushButton:hover {{
            background-color: {Colors.ZHUSHA_DARK};
        }}
        QPushButton:pressed {{
            background-color: {Colors.ZHUSHA_DARK};
        }}
        QPushButton:disabled {{
            background-color: {Colors.BORDER};
            color: {Colors.TEXT3};
        }}
    """

    # ==================== 次按钮 ====================
    BTN_SECONDARY = f"""
        QPushButton {{
            background-color: {Colors.CARD};
            color: {Colors.TEXT2};
            border: 1px solid {Colors.BORDER2};
            border-radius: {Spacing.RADIUS_SM};
            font-size: 13px;
            font-family: {Fonts.BODY};
            padding: 10px 22px;
            min-height: 40px;
        }}
        QPushButton:hover {{
            background-color: {Colors.CARD_HOVER};
            border-color: {Colors.QINGHUA_LIGHT};
            color: {Colors.QINGHUA};
        }}
        QPushButton:pressed {{
            background-color: {Colors.HOVER};
        }}
    """

    # ==================== 切换按钮 ====================
    BTN_SWITCH = f"""
        QPushButton {{
            background-color: {Colors.CARD};
            color: {Colors.TEXT2};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: 12px;
            font-family: {Fonts.BODY};
            padding: 6px 16px;
        }}
        QPushButton:hover {{
            border-color: {Colors.QINGHUA_LIGHT};
            color: {Colors.QINGHUA};
            background-color: {Colors.CARD_HOVER};
        }}
        QPushButton:checked {{
            background-color: {Colors.QINGHUA};
            color: {Colors.TEXT_INV};
            border-color: {Colors.QINGHUA};
            font-weight: {Fonts.W_MEDIUM};
        }}
    """

    # ==================== 输入框 ====================
    INPUT = f"""
        QLineEdit {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 8px 12px;
            min-height: 36px;
            color: {Colors.TEXT};
            selection-background-color: {Colors.QINGHUA};
            selection-color: white;
        }}
        QLineEdit:focus {{
            border: 1.5px solid {Colors.QINGHUA};
            background-color: {Colors.CARD_HOVER};
        }}
        QLineEdit:hover:!focus {{
            border-color: {Colors.BORDER2};
        }}
        QLineEdit::placeholder {{
            color: {Colors.TEXT3};
        }}
    """

    # ==================== 下拉框 ====================
    COMBO = f"""
        QComboBox {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 7px 28px 7px 12px;
            min-height: 36px;
            color: {Colors.TEXT};
        }}
        QComboBox:focus {{
            border: 1.5px solid {Colors.QINGHUA};
        }}
        QComboBox:hover:!focus {{
            border-color: {Colors.BORDER2};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
            subcontrol-origin: padding;
            subcontrol-position: right center;
            padding-right: 8px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {Colors.TEXT3};
        }}
        QComboBox::down-arrow:hover {{
            border-top-color: {Colors.QINGHUA};
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            background: {Colors.CARD};
            selection-background-color: {Colors.QINGHUA};
            selection-color: white;
            padding: 6px;
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            border-radius: 4px;
            min-height: 30px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {Colors.HOVER};
        }}
    """

    # ==================== 单选按钮 ====================
    RADIO = f"""
        QRadioButton {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 6px 14px;
            min-height: 32px;
            color: {Colors.TEXT};
        }}
        QRadioButton:hover {{
            border-color: {Colors.BORDER2};
            background-color: {Colors.CARD_HOVER};
        }}
        QRadioButton:checked {{
            border: 1.5px solid {Colors.QINGHUA};
            background-color: {Colors.QINGHUA_LIGHT};
            color: {Colors.QINGHUA};
            font-weight: {Fonts.W_BOLD};
        }}
        QRadioButton::indicator {{
            width: 14px;
            height: 14px;
            border-radius: 7px;
            border: 1.5px solid {Colors.BORDER2};
        }}
        QRadioButton::indicator:checked {{
            background-color: {Colors.QINGHUA};
            border-color: {Colors.QINGHUA};
        }}
    """

    # ==================== 日期选择 ====================
    DATE = f"""
        QDateEdit {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 7px 12px;
            min-height: 36px;
            color: {Colors.TEXT};
        }}
        QDateEdit:focus {{
            border: 1.5px solid {Colors.QINGHUA};
        }}
        QDateEdit:hover:!focus {{
            border-color: {Colors.BORDER2};
        }}
        QDateEdit::drop-down {{
            border: none;
            width: 22px;
        }}
        QDateEdit::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {Colors.TEXT3};
        }}
        QDateEdit QCalendarWidget {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS};
        }}
        QDateEdit QCalendarWidget QToolButton {{
            color: {Colors.TEXT};
            font-family: {Fonts.BODY};
            padding: 6px;
            border-radius: {Spacing.RADIUS_SM};
        }}
        QDateEdit QCalendarWidget QToolButton:hover {{
            background-color: {Colors.HOVER};
        }}
        QDateEdit QCalendarWidget QAbstractItemView:enabled {{
            color: {Colors.TEXT};
            selection-background-color: {Colors.QINGHUA};
            selection-color: white;
        }}
    """

    # ==================== 滚动条 ====================
    SCROLL = f"""
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            border-radius: 4px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {Colors.BORDER};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {Colors.BORDER2};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 8px;
            border-radius: 4px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal {{
            background: {Colors.BORDER};
            border-radius: 4px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {Colors.BORDER2};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
    """

    # ==================== 状态栏 ====================
    STATUS = f"""
        QStatusBar {{
            background: {Colors.CARD};
            color: {Colors.TEXT3};
            border-top: 1px solid {Colors.DIVIDER};
            font-size: {Fonts.SZ_SMALL};
            font-family: {Fonts.BODY};
            padding: 4px 16px;
            min-height: 30px;
        }}
        QStatusBar::item {{
            border: none;
        }}
    """

    # ==================== 提示框 ====================
    TOOLTIP = f"""
        QToolTip {{
            background: {Colors.CARD};
            color: {Colors.TEXT};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            padding: 10px 14px;
            font-size: {Fonts.SZ_SMALL};
            font-family: {Fonts.BODY};
        }}
    """

    # ==================== 多行文本 ====================
    TEXT_EDIT = f"""
        QTextEdit {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 8px 12px;
            color: {Colors.TEXT};
        }}
        QTextEdit:focus {{
            border: 1.5px solid {Colors.QINGHUA};
        }}
    """

    # ==================== 图标按钮 ====================
    BTN_ICON = f"""
        QPushButton {{
            background: transparent;
            color: {Colors.TEXT3};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_SMALL};
            font-family: {Fonts.BODY};
            padding: 6px 14px;
            min-height: 30px;
        }}
        QPushButton:hover {{
            background: {Colors.HOVER};
            color: {Colors.TEXT2};
            border-color: {Colors.BORDER2};
        }}
    """

    # ==================== 标签页/分组标题 ====================
    SECTION_HEADER = f"""
        QLabel {{
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT};
            font-family: {Fonts.BODY};
        }}
    """

    # ==================== 分割线 ====================
    DIVIDER_STYLE = f"background-color: {Colors.DIVIDER};"

    # ==================== 旧版兼容别名 ====================
    GOLD_DIVIDER = DIVIDER_STYLE
    SECTION_CARD = CARD
    LINE_EDIT = INPUT
    BUTTON_PRIMARY = BTN_PRIMARY
    BUTTON_SECONDARY = BTN_SECONDARY
    BUTTON_SWITCH = BTN_SWITCH
    COMBO_BOX = COMBO
    SCROLL_AREA = SCROLL
    SCROLL_BOOK = SCROLL
    LEFT_PANEL = f"background-color: {Colors.BG};"
    RIGHT_PANEL = f"background-color: {Colors.BG};"
    PARCHMENT_PANEL = f"background-color: {Colors.BG};"
    SEAL_BUTTON = BTN_PRIMARY
    WADANG_BUTTON = BTN_SECONDARY
    GUA_CARD = BTN_SWITCH
    SWITCH_BUTTON = BTN_SWITCH
    PARCHMENT_INPUT = INPUT
    SCROLL_COMBO = COMBO
    ANCIENT_DATE = DATE
    CLOUD_DIVIDER = DIVIDER_STYLE
    WOOD_FRAME = DIVIDER_STYLE
    MAIN_WINDOW = MAIN
    BOOK_PAGE = CARD
    PAN_TYPE_CARD = BTN_SWITCH
    GENDER_CARD = BTN_SWITCH
    BUTTON_HOUR = BTN_SWITCH
    TOGGLE_SWITCH = ""
    MEANDER_BORDER = ""
    WOOD_SEPARATOR = DIVIDER_STYLE
    INPUT_SEPARATOR = DIVIDER_STYLE
    LABEL_ANCIENT = f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};"
    FAMILY_CN = Fonts.BODY
    FAMILY_KAI = Fonts.TITLE
    FAMILY_SONG = Fonts.TITLE
    FAMILY_SERIF = Fonts.TITLE
    FAMILY_EN = Fonts.MONO
    SIZE_TITLE = Fonts.SZ_TITLE
    SIZE_SECTION = Fonts.SZ_SECTION
    SIZE_KEY = '24px'
    SIZE_BODY = Fonts.SZ_BODY
    SIZE_SMALL = Fonts.SZ_SMALL
    SIZE_MICRO = Fonts.SZ_MICRO
    WEIGHT_NORMAL = Fonts.W_NORMAL
    WEIGHT_BOLD = Fonts.W_BOLD
