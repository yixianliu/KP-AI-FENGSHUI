class Colors:
    BACKGROUND = '#F9F7F3'
    CARD = '#FFFFFF'
    TEXT_PRIMARY = '#1A1A1A'
    TEXT_SECONDARY = '#333333'
    TEXT_TERTIARY = '#8A8A8A'
    ACCENT = '#2A4A3F'
    ACCENT_LIGHT = '#3A6A5F'
    ACCENT_DARK = '#1A3A2F'
    WARNING = '#9C4444'
    BORDER = '#E0E0E0'
    BORDER_LIGHT = '#F0F0F0'
    BUTTON_SECONDARY_BORDER = '#B8B8B8'


class Fonts:
    FAMILY_CN = 'Source Han Sans SC, Microsoft YaHei, sans-serif'
    FAMILY_EN = 'Consolas, Monaco, monospace'
    SIZE_TITLE = '19px'
    SIZE_SECTION = '16px'
    SIZE_KEY = '18px'
    SIZE_BODY = '13px'
    SIZE_SMALL = '11px'
    WEIGHT_NORMAL = 'Normal'
    WEIGHT_BOLD = 'Bold'


class Spacing:
    CARD_RADIUS = '8px'
    CONTROL_RADIUS = '6px'
    CARD_PADDING = '20px'
    MODULE_GAP = '14px'
    LINE_HEIGHT = '1.6'
    LETTER_SPACING = '0.5px'
    CONTROL_VERTICAL_GAP = '10px'
    BUTTON_MIN_HEIGHT = '34px'
    BUTTON_MIN_WIDTH = '85px'


class Animation:
    DURATION_SHORT = 200
    DURATION_NORMAL = 300


class Stylesheets:
    MAIN_WINDOW = f"""
        QMainWindow {{
            background-color: {Colors.BACKGROUND};
        }}
    """

    HEADER = f"""
        QFrame {{
            background-color: {Colors.CARD};
            border-bottom: 1px solid {Colors.BORDER};
        }}
    """

    HEADER_TITLE = f"""
        font-size: {Fonts.SIZE_TITLE};
        font-weight: {Fonts.WEIGHT_BOLD};
        color: {Colors.TEXT_PRIMARY};
        font-family: {Fonts.FAMILY_CN};
    """

    HEADER_SUBTITLE = f"""
        font-size: {Fonts.SIZE_BODY};
        color: {Colors.TEXT_TERTIARY};
        font-family: {Fonts.FAMILY_CN};
    """

    CARD = f"""
        QFrame {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CARD_RADIUS};
        }}
    """

    CARD_NO_SHADOW = f"""
        QFrame {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CARD_RADIUS};
        }}
    """

    CARD_TITLE = f"""
        font-size: {Fonts.SIZE_SECTION};
        font-weight: {Fonts.WEIGHT_BOLD};
        color: {Colors.TEXT_PRIMARY};
        font-family: {Fonts.FAMILY_CN};
    """

    CARD_TITLE_ACCENT = f"""
        font-size: {Fonts.SIZE_SECTION};
        font-weight: {Fonts.WEIGHT_BOLD};
        color: {Colors.ACCENT};
        font-family: {Fonts.FAMILY_CN};
    """

    BUTTON_PRIMARY = f"""
        QPushButton {{
            background-color: {Colors.ACCENT};
            color: white;
            border: none;
            border-radius: {Spacing.CARD_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            font-family: {Fonts.FAMILY_CN};
            padding: 8px 24px;
            min-height: {Spacing.BUTTON_MIN_HEIGHT};
            min-width: {Spacing.BUTTON_MIN_WIDTH};
        }}
        QPushButton:hover {{
            background-color: {Colors.ACCENT_LIGHT};
        }}
        QPushButton:pressed {{
            background-color: {Colors.ACCENT_DARK};
        }}
        QPushButton:disabled {{
            background-color: {Colors.BORDER};
            color: {Colors.TEXT_TERTIARY};
        }}
    """

    BUTTON_SECONDARY = f"""
        QPushButton {{
            background-color: transparent;
            color: {Colors.TEXT_SECONDARY};
            border: 1px solid {Colors.BUTTON_SECONDARY_BORDER};
            border-radius: {Spacing.CARD_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_NORMAL};
            font-family: {Fonts.FAMILY_CN};
            padding: 8px 18px;
            min-height: {Spacing.BUTTON_MIN_HEIGHT};
            min-width: {Spacing.BUTTON_MIN_WIDTH};
        }}
        QPushButton:hover {{
            border-color: {Colors.ACCENT};
            color: {Colors.ACCENT};
        }}
        QPushButton:pressed {{
            background-color: rgba(42, 74, 63, 0.05);
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
            border-color: {Colors.ACCENT};
        }}
        QPushButton:checked {{
            background-color: {Colors.ACCENT};
            color: white;
            border-color: {Colors.ACCENT};
        }}
        QPushButton:checked:hover {{
            background-color: {Colors.ACCENT_LIGHT};
        }}
    """

    BUTTON_TOGGLE = f"""
        QPushButton {{
            background-color: {Colors.BACKGROUND};
            color: {Colors.TEXT_SECONDARY};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_NORMAL};
            font-family: {Fonts.FAMILY_CN};
            padding: 6px 16px;
            min-width: 85px;
        }}
        QPushButton:hover {{
            border-color: {Colors.ACCENT};
        }}
        QPushButton:checked {{
            background-color: {Colors.ACCENT};
            color: white;
            border-color: {Colors.ACCENT};
        }}
    """

    LINE_EDIT = f"""
        QLineEdit {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY_CN};
            padding: 6px 10px;
            min-height: 32px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QLineEdit:focus {{
            border: 2px solid {Colors.ACCENT};
            padding: 5px 9px;
        }}
        QLineEdit::placeholder {{
            color: {Colors.TEXT_TERTIARY};
        }}
    """

    COMBO_BOX = f"""
        QComboBox {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY_CN};
            padding: 6px 10px;
            min-height: 32px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QComboBox:focus {{
            border: 2px solid {Colors.ACCENT};
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
            border-top: 4px solid {Colors.ACCENT};
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            background-color: {Colors.CARD};
            selection-background-color: {Colors.ACCENT};
            selection-color: white;
            padding: 4px;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY_CN};
        }}
    """

    DATE_EDIT = f"""
        QDateEdit {{
            background-color: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY_EN};
            padding: 6px 10px;
            min-height: 32px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QDateEdit:focus {{
            border: 2px solid {Colors.ACCENT};
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
            border-top: 4px solid {Colors.ACCENT};
        }}
    """

    LABEL_BODY = f"""
        font-size: {Fonts.SIZE_BODY};
        color: {Colors.TEXT_SECONDARY};
        font-family: {Fonts.FAMILY_CN};
        line-height: {Spacing.LINE_HEIGHT};
        letter-spacing: {Spacing.LETTER_SPACING};
    """

    LABEL_SMALL = f"""
        font-size: {Fonts.SIZE_SMALL};
        color: {Colors.TEXT_TERTIARY};
        font-family: {Fonts.FAMILY_CN};
    """

    LABEL_KEY = f"""
        font-size: {Fonts.SIZE_KEY};
        font-weight: {Fonts.WEIGHT_BOLD};
        color: {Colors.TEXT_PRIMARY};
        font-family: {Fonts.FAMILY_CN};
    """

    LABEL_ACCENT = f"""
        font-size: {Fonts.SIZE_BODY};
        font-weight: {Fonts.WEIGHT_BOLD};
        color: {Colors.ACCENT};
        font-family: {Fonts.FAMILY_CN};
    """

    LABEL_WARNING = f"""
        font-size: {Fonts.SIZE_SMALL};
        color: {Colors.WARNING};
        font-family: {Fonts.FAMILY_CN};
    """

    TABLE_WIDGET = f"""
        QTableWidget {{
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CARD_RADIUS};
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY_CN};
            background-color: {Colors.CARD};
            gridline-color: {Colors.BORDER_LIGHT};
        }}
        QTableWidget::item {{
            padding: 8px 6px;
            text-align: center;
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
        }}
        QTableWidget::item:selected {{
            background-color: rgba(42, 74, 63, 0.08);
            color: {Colors.TEXT_PRIMARY};
        }}
        QHeaderView::section {{
            background-color: {Colors.ACCENT};
            color: white;
            font-weight: {Fonts.WEIGHT_BOLD};
            font-size: {Fonts.SIZE_SMALL};
            padding: 8px 6px;
            text-align: center;
            border: none;
            border-right: 1px solid {Colors.ACCENT_DARK};
        }}
        QHeaderView::section:first {{
            border-top-left-radius: {Spacing.CARD_RADIUS};
        }}
        QHeaderView::section:last {{
            border-top-right-radius: {Spacing.CARD_RADIUS};
            border-right: none;
        }}
        QTableCornerButton::section {{
            background-color: {Colors.ACCENT};
            border: none;
        }}
    """

    SCROLL_AREA = f"""
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background-color: {Colors.BORDER_LIGHT};
            width: 8px;
            border-radius: 4px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {Colors.BORDER};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {Colors.ACCENT};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background-color: {Colors.BORDER_LIGHT};
            height: 8px;
            border-radius: 4px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {Colors.BORDER};
            border-radius: 4px;
            min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {Colors.ACCENT};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """

    STATUS_BAR = f"""
        QStatusBar {{
            background-color: {Colors.CARD};
            color: {Colors.TEXT_SECONDARY};
            border-top: 1px solid {Colors.BORDER};
            font-size: {Fonts.SIZE_SMALL};
            font-family: {Fonts.FAMILY_CN};
        }}
    """

    PROGRESS_BAR = f"""
        QProgressBar {{
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.CONTROL_RADIUS};
            background-color: {Colors.BORDER_LIGHT};
            text-align: center;
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.TEXT_TERTIARY};
            height: 10px;
        }}
        QProgressBar::chunk {{
            background-color: {Colors.ACCENT};
            border-radius: 4px;
        }}
    """

    COLLAPSE_HEADER = f"""
        QFrame {{
            background-color: {Colors.BACKGROUND};
            border-bottom: 1px solid {Colors.BORDER};
        }}
    """

    TOGGLE_SWITCH = f"""
        QCheckBox {{
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 40px;
            height: 22px;
            border-radius: 11px;
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
            margin: 2px;
        }}
        QCheckBox::indicator:checked::handle {{
            width: 18px;
            height: 18px;
            border-radius: 9px;
            background-color: white;
            margin-left: 20px;
            margin-top: 2px;
        }}
    """
