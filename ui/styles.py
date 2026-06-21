"""
风水排盘专业工具 - 极简轻量国风设计系统 v4.0
三色点缀：朱砂红·青花蓝·鎏金黄 | 底色纯白/浅米灰 | 圆角卡片 | 柔和阴影
"""
from PySide6.QtGui import QColor


class Colors:
    # 底色
    BG = '#F7F6F3'
    BG_WHITE = '#FFFFFF'
    CARD = '#FFFFFF'
    HOVER = '#F0EFEC'

    # 三色点缀
    ZHUSHA = '#C45C48'
    ZHUSHA_LIGHT = '#E8A090'
    ZHUSHA_DARK = '#9E3D2B'
    QINGHUA = '#5B8FA8'
    QINGHUA_LIGHT = '#A8C8D8'
    LIUJIN = '#C49A3C'
    LIUJIN_LIGHT = '#E8D5A0'

    # 文字
    TEXT = '#1A1A1A'
    TEXT2 = '#666666'
    TEXT3 = '#999999'
    TEXT_INV = '#FFFFFF'

    # 边框
    BORDER = '#E5E3DE'
    BORDER2 = '#D0CEC8'
    DIVIDER = '#E8E6E1'

    # 状态
    SUCCESS = '#5A8F6E'
    WARNING = '#C49548'
    DANGER = '#C45C48'

    # 阴影
    SHADOW = 'rgba(0,0,0,0.06)'
    SHADOW_HOVER = 'rgba(0,0,0,0.10)'

    # ==================== 旧版兼容别名 ====================
    BACKGROUND = BG
    PRIMARY = QINGHUA
    PRIMARY_LIGHT = QINGHUA_LIGHT
    PRIMARY_DARK = '#3A6A7A'
    ACCENT = ZHUSHA
    ACCENT_LIGHT = ZHUSHA_LIGHT
    ACCENT_DARK = ZHUSHA_DARK
    HIGHLIGHT = LIUJIN
    HIGHLIGHT_LIGHT = LIUJIN_LIGHT
    HIGHLIGHT_DARK = '#A67D28'
    HIGHLIGHT_GLOW = 'rgba(196,154,60,0.10)'
    TEXT_PRIMARY = TEXT
    TEXT_SECONDARY = TEXT2
    TEXT_TERTIARY = TEXT3
    TEXT_INVERSE = TEXT_INV
    BORDER_LIGHT = DIVIDER
    HOVER_BG = HOVER
    INPUT_BG = CARD
    INFO = QINGHUA
    WOOD = '#6B4E3A'
    WOOD_LIGHT = '#8B6B55'
    WOOD_DARK = '#4A3427'
    PARCHMENT = BG
    PARCHMENT_LIGHT = BG
    PARCHMENT_DARK = '#E3D5BC'
    BRONZE = '#6B6B4D'
    BRONZE_LIGHT = '#8A8A68'
    BRONZE_DARK = '#4A4A30'
    WATERMARK = 'rgba(0,0,0,0.02)'


class Fonts:
    TITLE = 'Source Han Serif SC, SimSun, STSong, Noto Serif CJK SC, serif'
    BODY = 'Microsoft YaHei, PingFang SC, Noto Sans CJK SC, sans-serif'
    MONO = 'Consolas, Monaco, monospace'

    SZ_TITLE = '17px'
    SZ_SECTION = '14px'
    SZ_BODY = '13px'
    SZ_SMALL = '12px'
    SZ_MICRO = '11px'

    W_NORMAL = 'Normal'
    W_BOLD = 'Medium'

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
    RADIUS = '10px'
    RADIUS_SM = '6px'
    RADIUS_LG = '14px'
    PAD = '20px'
    GAP = '14px'

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
    MAIN = f"QMainWindow {{ background-color: {Colors.BG}; }}"

    CARD = f"""
        QFrame {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS};
        }}
    """

    BTN_PRIMARY = f"""
        QPushButton {{
            background-color: {Colors.ZHUSHA};
            color: {Colors.TEXT_INV};
            border: 1.5px solid {Colors.LIUJIN};
            border-radius: {Spacing.RADIUS_SM};
            font-size: 14px;
            font-weight: {Fonts.W_BOLD};
            font-family: {Fonts.BODY};
            padding: 10px 28px;
            min-height: 40px;
        }}
        QPushButton:hover {{
            background-color: {Colors.ZHUSHA_LIGHT};
            border-color: {Colors.LIUJIN};
        }}
        QPushButton:pressed {{ background-color: {Colors.ZHUSHA_DARK}; }}
        QPushButton:disabled {{
            background-color: {Colors.BORDER}; border-color: {Colors.BORDER};
            color: {Colors.TEXT3};
        }}
    """

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
            background-color: #FFF0EE;
            border-color: {Colors.ZHUSHA_LIGHT};
            color: {Colors.ZHUSHA};
        }}
        QPushButton:pressed {{ background-color: {Colors.HOVER}; }}
    """

    BTN_SWITCH = f"""
        QPushButton {{
            background-color: {Colors.CARD};
            color: {Colors.TEXT2};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: 12px;
            font-family: {Fonts.BODY};
            padding: 5px 14px;
        }}
        QPushButton:hover {{
            border-color: {Colors.QINGHUA_LIGHT};
            color: {Colors.QINGHUA};
        }}
        QPushButton:checked {{
            background-color: {Colors.QINGHUA};
            color: {Colors.TEXT_INV};
            border-color: {Colors.QINGHUA};
        }}
    """

    INPUT = f"""
        QLineEdit {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 7px 12px;
            min-height: 34px;
            color: {Colors.TEXT};
            selection-background-color: {Colors.QINGHUA};
            selection-color: white;
        }}
        QLineEdit:focus {{ border: 1.5px solid {Colors.QINGHUA}; }}
        QLineEdit:hover:!focus {{ border-color: {Colors.BORDER2}; }}
        QLineEdit::placeholder {{ color: {Colors.TEXT3}; }}
    """

    COMBO = f"""
        QComboBox {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 6px 12px;
            min-height: 34px;
            color: {Colors.TEXT};
        }}
        QComboBox:focus {{ border: 1.5px solid {Colors.QINGHUA}; }}
        QComboBox:hover:!focus {{ border-color: {Colors.BORDER2}; }}
        QComboBox::drop-down {{ border: none; width: 22px; subcontrol-origin: padding; }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {Colors.TEXT3};
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            background: {Colors.CARD};
            selection-background-color: {Colors.QINGHUA};
            selection-color: white;
            padding: 4px;
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 6px 10px; border-radius: 4px; min-height: 28px;
        }}
        QComboBox QAbstractItemView::item:hover {{ background-color: {Colors.HOVER}; }}
    """

    DATE = f"""
        QDateEdit {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_BODY};
            font-family: {Fonts.BODY};
            padding: 6px 12px;
            min-height: 34px;
            color: {Colors.TEXT};
        }}
        QDateEdit:focus {{ border: 1.5px solid {Colors.QINGHUA}; }}
        QDateEdit:hover:!focus {{ border-color: {Colors.BORDER2}; }}
        QDateEdit::drop-down {{ border: none; width: 22px; }}
        QDateEdit::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {Colors.TEXT3};
        }}
    """

    SCROLL = f"""
        QScrollArea {{ background: transparent; border: none; }}
        QScrollBar:vertical {{
            background: transparent; width: 6px; border-radius: 3px; margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {Colors.BORDER2}; border-radius: 3px; min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {Colors.TEXT3}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
    """

    STATUS = f"""
        QStatusBar {{
            background: {Colors.CARD}; color: {Colors.TEXT3};
            border-top: 1px solid {Colors.DIVIDER};
            font-size: {Fonts.SZ_SMALL}; font-family: {Fonts.BODY}; padding: 3px 10px;
        }}
    """

    TOOLTIP = f"""
        QToolTip {{
            background: {Colors.CARD}; color: {Colors.TEXT};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            padding: 8px 12px;
            font-size: {Fonts.SZ_SMALL}; font-family: {Fonts.BODY};
        }}
    """

    DIVIDER = f"background-color: {Colors.DIVIDER};"

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
        QTextEdit:focus {{ border: 1.5px solid {Colors.QINGHUA}; }}
    """

    BTN_ICON = f"""
        QPushButton {{
            background: transparent; color: {Colors.TEXT3};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            font-size: {Fonts.SZ_SMALL}; font-family: {Fonts.BODY};
            padding: 5px 12px; min-height: 30px;
        }}
        QPushButton:hover {{
            background: {Colors.HOVER}; color: {Colors.TEXT2};
            border-color: {Colors.BORDER2};
        }}
    """

    # ==================== 旧版兼容别名 ====================
    GOLD_DIVIDER = DIVIDER
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
    CLOUD_DIVIDER = DIVIDER
    WOOD_FRAME = DIVIDER
    MAIN_WINDOW = MAIN
    BOOK_PAGE = CARD
    PAN_TYPE_CARD = BTN_SWITCH
    GENDER_CARD = BTN_SWITCH
    BUTTON_HOUR = BTN_SWITCH
    TOGGLE_SWITCH = ""
    MEANDER_BORDER = ""
    WOOD_SEPARATOR = DIVIDER
    INPUT_SEPARATOR = DIVIDER
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
