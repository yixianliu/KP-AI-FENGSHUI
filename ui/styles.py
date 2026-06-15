"""
风水排盘专业工具 - 新中式极简国风设计系统
配色方案：藏青、朱砂红、鎏金浅黄、米白、墨黑
"""


class Colors:
    # 主色调 - 藏青
    PRIMARY = '#2C3E5C'
    PRIMARY_LIGHT = '#3D5A80'
    PRIMARY_DARK = '#1A2536'

    # 点缀色 - 朱砂红
    ACCENT = '#C45C48'
    ACCENT_LIGHT = '#D97B6A'
    ACCENT_DARK = '#9E3D2B'

    # 高光色 - 鎏金
    HIGHLIGHT = '#D4A843'
    HIGHLIGHT_LIGHT = '#E8C876'
    HIGHLIGHT_GLOW = 'rgba(212, 168, 67, 0.15)'

    # 中性色
    BACKGROUND = '#F5F0E8'
    CARD = '#FAF7F2'
    INPUT_BG = '#FFFFFF'
    HOVER_BG = '#EDE8DE'

    # 文字色
    TEXT_PRIMARY = '#1A1A1A'
    TEXT_SECONDARY = '#4A4A4A'
    TEXT_TERTIARY = '#8A8A8A'
    TEXT_INVERSE = '#F5F0E8'

    # 边框与分割线
    BORDER = '#D9D3C7'
    BORDER_LIGHT = '#E8E2D6'
    DIVIDER = 'rgba(44, 62, 92, 0.1)'

    # 状态色
    SUCCESS = '#5A8F6E'
    WARNING = '#C49548'
    DANGER = '#C45C48'
    INFO = '#5A7A9E'


class Fonts:
    FAMILY_CN = 'Microsoft YaHei, PingFang SC, Hiragino Sans GB, Noto Sans CJK SC, WenQuanYi Micro Hei, sans-serif'
    FAMILY_SERIF = 'SimSun, STSong, Noto Serif CJK SC, Source Han Serif CN, serif'
    FAMILY_EN = 'Consolas, Monaco, monospace'
    SIZE_TITLE = '20px'
    SIZE_SECTION = '15px'
    SIZE_KEY = '18px'
    SIZE_BODY = '13px'
    SIZE_SMALL = '11px'
    WEIGHT_NORMAL = 'Normal'
    WEIGHT_BOLD = 'Bold'


class Spacing:
    CARD_RADIUS = '12px'
    CONTROL_RADIUS = '8px'
    CARD_PADDING = '20px'
    MODULE_GAP = '16px'
    LINE_HEIGHT = '1.6'
    LETTER_SPACING = '0.5px'
    CONTROL_VERTICAL_GAP = '12px'
    BUTTON_MIN_HEIGHT = '42px'
    BUTTON_MIN_WIDTH = '100px'


class Stylesheets:
    MAIN_WINDOW = f"""
        QMainWindow {{
            background-color: {Colors.BACKGROUND};
        }}
    """

    LEFT_PANEL = f"""
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.CARD}, stop:1 {Colors.BACKGROUND});
            border-right: 1px solid {Colors.BORDER_LIGHT};
        }}
    """

    CARD = f"""
        QFrame {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: {Spacing.CARD_RADIUS};
        }}
    """

    SECTION_CARD = f"""
        QFrame {{
            background-color: {Colors.INPUT_BG};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: {Spacing.CONTROL_RADIUS};
        }}
    """

    BUTTON_PRIMARY = f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {Colors.ACCENT}, stop:1 {Colors.ACCENT_DARK});
            color: {Colors.TEXT_INVERSE};
            border: none;
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: 15px;
            font-weight: {Fonts.WEIGHT_BOLD};
            font-family: {Fonts.FAMILY_CN};
            padding: 10px 28px;
            min-height: {Spacing.BUTTON_MIN_HEIGHT};
            min-width: {Spacing.BUTTON_MIN_WIDTH};
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {Colors.ACCENT_LIGHT}, stop:1 {Colors.ACCENT});
        }}
        QPushButton:pressed {{
            background: {Colors.ACCENT_DARK};
        }}
        QPushButton:disabled {{
            background: {Colors.BORDER};
            color: {Colors.TEXT_TERTIARY};
        }}
    """

    BUTTON_SECONDARY = f"""
        QPushButton {{
            background-color: {Colors.HOVER_BG};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_NORMAL};
            font-family: {Fonts.FAMILY_CN};
            padding: 10px 20px;
            min-height: {Spacing.BUTTON_MIN_HEIGHT};
            min-width: {Spacing.BUTTON_MIN_WIDTH};
        }}
        QPushButton:hover {{
            background-color: {Colors.ACCENT_LIGHT};
            color: white;
            border-color: {Colors.ACCENT_LIGHT};
        }}
        QPushButton:pressed {{
            background-color: {Colors.ACCENT};
        }}
    """

    BUTTON_SWITCH = f"""
        QPushButton {{
            background-color: {Colors.BACKGROUND};
            color: {Colors.TEXT_SECONDARY};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_NORMAL};
            font-family: {Fonts.FAMILY_CN};
            padding: 6px 12px;
            min-width: 80px;
        }}
        QPushButton:hover {{
            border-color: {Colors.HIGHLIGHT};
            color: {Colors.HIGHLIGHT};
        }}
        QPushButton:checked {{
            background-color: {Colors.PRIMARY};
            color: white;
            border-color: {Colors.PRIMARY};
        }}
        QPushButton:checked:hover {{
            background-color: {Colors.PRIMARY_LIGHT};
        }}
    """

    BUTTON_HOUR = f"""
        QPushButton {{
            background-color: {Colors.INPUT_BG};
            color: {Colors.TEXT_SECONDARY};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: 12px;
            font-family: {Fonts.FAMILY_CN};
            padding: 6px 4px;
            min-width: 50px;
        }}
        QPushButton:hover {{
            border-color: {Colors.HIGHLIGHT};
            color: {Colors.HIGHLIGHT};
        }}
        QPushButton:checked {{
            background-color: {Colors.ACCENT};
            color: white;
            border-color: {Colors.ACCENT};
        }}
    """

    LINE_EDIT = f"""
        QLineEdit {{
            background-color: {Colors.INPUT_BG};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY_CN};
            padding: 8px 12px;
            min-height: 36px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QLineEdit:focus {{
            border: 2px solid {Colors.HIGHLIGHT};
            padding: 7px 11px;
        }}
        QLineEdit::placeholder {{
            color: {Colors.TEXT_TERTIARY};
        }}
    """

    COMBO_BOX = f"""
        QComboBox {{
            background-color: {Colors.INPUT_BG};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY_CN};
            padding: 6px 10px;
            min-height: 36px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QComboBox:focus {{
            border: 2px solid {Colors.HIGHLIGHT};
            padding: 5px 9px;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 26px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid {Colors.PRIMARY};
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            background-color: {Colors.INPUT_BG};
            selection-background-color: {Colors.PRIMARY};
            selection-color: white;
            padding: 4px;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY_CN};
        }}
    """

    DATE_EDIT = f"""
        QDateEdit {{
            background-color: {Colors.INPUT_BG};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY_EN};
            padding: 6px 10px;
            min-height: 36px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QDateEdit:focus {{
            border: 2px solid {Colors.HIGHLIGHT};
            padding: 5px 9px;
        }}
        QDateEdit::drop-down {{
            border: none;
            width: 26px;
        }}
        QDateEdit::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid {Colors.PRIMARY};
        }}
    """

    SCROLL_AREA = f"""
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background-color: transparent;
            width: 6px;
            border-radius: 3px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {Colors.BORDER};
            border-radius: 3px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {Colors.HIGHLIGHT};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """

    STATUS_BAR = f"""
        QStatusBar {{
            background-color: {Colors.CARD};
            color: {Colors.TEXT_SECONDARY};
            border-top: 1px solid {Colors.BORDER_LIGHT};
            font-size: {Fonts.SIZE_SMALL};
            font-family: {Fonts.FAMILY_CN};
        }}
    """

    TOGGLE_SWITCH = f"""
        QCheckBox {{
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 44px;
            height: 24px;
            border-radius: 12px;
            background-color: {Colors.BORDER};
        }}
        QCheckBox::indicator:checked {{
            background-color: {Colors.ACCENT};
        }}
        QCheckBox::indicator:unchecked::handle {{
            width: 18px;
            height: 18px;
            border-radius: 9px;
            background-color: white;
            margin: 3px;
        }}
        QCheckBox::indicator:checked::handle {{
            width: 18px;
            height: 18px;
            border-radius: 9px;
            background-color: white;
            margin-left: 23px;
            margin-top: 3px;
        }}
    """

    GOLD_DIVIDER = f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 transparent, stop:0.3 {Colors.HIGHLIGHT},
            stop:0.5 {Colors.HIGHLIGHT_LIGHT}, stop:0.7 {Colors.HIGHLIGHT},
            stop:1 transparent);
        height: 2px;
        border-radius: 1px;
    """

    PAN_TYPE_CARD = f"""
        QPushButton {{
            background-color: {Colors.INPUT_BG};
            color: {Colors.TEXT_SECONDARY};
            border: 2px solid {Colors.BORDER};
            border-radius: {Spacing.CARD_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            font-family: {Fonts.FAMILY_CN};
            padding: 16px;
        }}
        QPushButton:hover {{
            border-color: {Colors.HIGHLIGHT};
            color: {Colors.HIGHLIGHT};
        }}
        QPushButton:checked {{
            background-color: {Colors.ACCENT};
            color: white;
            border-color: {Colors.HIGHLIGHT};
            border: 2px solid {Colors.HIGHLIGHT};
        }}
    """

    GENDER_CARD = f"""
        QPushButton {{
            background-color: {Colors.INPUT_BG};
            color: {Colors.TEXT_SECONDARY};
            border: 2px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY_CN};
            padding: 12px;
        }}
        QPushButton:hover {{
            border-color: {Colors.HIGHLIGHT};
        }}
        QPushButton:checked {{
            border-color: {Colors.ACCENT};
            background-color: rgba(196, 92, 72, 0.08);
        }}
    """

    TEXT_EDIT = f"""
        QTextEdit {{
            background-color: {Colors.INPUT_BG};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY_CN};
            padding: 8px 12px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QTextEdit:focus {{
            border: 2px solid {Colors.HIGHLIGHT};
            padding: 7px 11px;
        }}
    """
