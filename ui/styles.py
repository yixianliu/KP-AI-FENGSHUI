class Colors:
    PRIMARY = '#6B4423'
    PRIMARY_LIGHT = '#8B5A2B'
    PRIMARY_DARK = '#4A2E17'
    
    ACCENT = '#D4AF37'
    ACCENT_LIGHT = '#E8C850'
    ACCENT_DARK = '#B89600'
    
    BACKGROUND = '#FAF8F5'
    BACKGROUND_LIGHT = '#FFFFFF'
    BACKGROUND_SOFT = '#F5F2ED'
    
    TEXT_PRIMARY = '#2D2D2D'
    TEXT_SECONDARY = '#5A5A5A'
    TEXT_TERTIARY = '#8A8A8A'
    
    BORDER = '#E0D8D0'
    BORDER_LIGHT = '#F0EBE5'
    
    SUCCESS = '#2E7D32'
    WARNING = '#E65100'
    ERROR = '#C62828'
    INFO = '#1565C0'
    
    WOOD = '#2E7D32'
    FIRE = '#C62828'
    EARTH = '#E65100'
    METAL = '#546E7A'
    WATER = '#1565C0'

class Fonts:
    FAMILY = 'Microsoft YaHei'
    FAMILY_BOLD = 'SimHei'
    
    SIZE_TITLE = '18px'
    SIZE_SUBTITLE = '15px'
    SIZE_CARD_TITLE = '14px'
    SIZE_BODY = '13px'
    SIZE_SMALL = '12px'
    
    WEIGHT_NORMAL = 'Normal'
    WEIGHT_MEDIUM = '500'
    WEIGHT_BOLD = 'Bold'

class Spacing:
    CARD_GAP = '16px'
    CARD_PADDING = '20px'
    CONTENT_PADDING = '24px'
    SECTION_GAP = '12px'
    ELEMENT_GAP = '8px'
    BUTTON_MIN_HEIGHT = '40px'
    BUTTON_MIN_WIDTH = '120px'
    LINE_HEIGHT = '1.6'

class Animation:
    DURATION_SHORT = 200
    DURATION_NORMAL = 300
    DURATION_LONG = 500

class Stylesheets:
    MAIN_WINDOW = f"""
        QMainWindow {{
            background-color: {Colors.BACKGROUND};
        }}
    """
    
    HEADER = f"""
        QFrame {{
            background-color: {Colors.PRIMARY};
            border-bottom: 2px solid {Colors.ACCENT};
        }}
    """
    
    HEADER_TITLE = f"""
        font-size: {Fonts.SIZE_TITLE};
        font-weight: {Fonts.WEIGHT_BOLD};
        color: {Colors.ACCENT};
        font-family: {Fonts.FAMILY_BOLD};
    """
    
    CARD = f"""
        QFrame {{
            background-color: {Colors.BACKGROUND_LIGHT};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
        }}
    """
    
    CARD_HEADER = f"""
        QFrame {{
            background-color: {Colors.PRIMARY};
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            border-bottom: 1px solid {Colors.PRIMARY_DARK};
        }}
    """
    
    CARD_TITLE = f"""
        font-size: {Fonts.SIZE_CARD_TITLE};
        font-weight: {Fonts.WEIGHT_BOLD};
        color: {Colors.ACCENT};
        font-family: {Fonts.FAMILY_BOLD};
    """
    
    BUTTON_PRIMARY = f"""
        QPushButton {{
            background-color: {Colors.PRIMARY};
            color: white;
            border: none;
            border-radius: 8px;
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            font-family: {Fonts.FAMILY};
            padding: 10px 24px;
            min-height: {Spacing.BUTTON_MIN_HEIGHT};
            min-width: {Spacing.BUTTON_MIN_WIDTH};
        }}
        QPushButton:hover {{
            background-color: {Colors.PRIMARY_LIGHT};
        }}
        QPushButton:pressed {{
            background-color: {Colors.PRIMARY_DARK};
        }}
        QPushButton:disabled {{
            background-color: {Colors.BORDER};
            color: {Colors.TEXT_TERTIARY};
        }}
    """
    
    BUTTON_SECONDARY = f"""
        QPushButton {{
            background-color: {Colors.BACKGROUND_LIGHT};
            color: {Colors.PRIMARY};
            border: 2px solid {Colors.PRIMARY};
            border-radius: 8px;
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            font-family: {Fonts.FAMILY};
            padding: 10px 24px;
            min-height: {Spacing.BUTTON_MIN_HEIGHT};
            min-width: {Spacing.BUTTON_MIN_WIDTH};
        }}
        QPushButton:hover {{
            background-color: {Colors.BACKGROUND_SOFT};
        }}
    """
    
    BUTTON_SMALL = f"""
        QPushButton {{
            background-color: {Colors.ACCENT};
            color: {Colors.PRIMARY};
            border: none;
            border-radius: 4px;
            font-size: {Fonts.SIZE_SMALL};
            font-weight: {Fonts.WEIGHT_BOLD};
            font-family: {Fonts.FAMILY};
            padding: 6px 12px;
        }}
        QPushButton:hover {{
            background-color: {Colors.ACCENT_LIGHT};
        }}
    """
    
    LINE_EDIT = f"""
        QLineEdit {{
            background-color: {Colors.BACKGROUND_LIGHT};
            border: 2px solid {Colors.BORDER};
            border-radius: 6px;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
            padding: 10px 14px;
            min-height: 36px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QLineEdit:focus {{
            border-color: {Colors.PRIMARY};
            background-color: {Colors.BACKGROUND_SOFT};
        }}
        QLineEdit::placeholder {{
            color: {Colors.TEXT_TERTIARY};
        }}
    """
    
    COMBO_BOX = f"""
        QComboBox {{
            background-color: {Colors.BACKGROUND_LIGHT};
            border: 2px solid {Colors.BORDER};
            border-radius: 6px;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
            padding: 10px 14px;
            min-height: 36px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QComboBox:focus {{
            border-color: {Colors.PRIMARY};
            background-color: {Colors.BACKGROUND_SOFT};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {Colors.PRIMARY};
        }}
        QComboBox QAbstractItemView {{
            border: 2px solid {Colors.BORDER};
            border-radius: 6px;
            background-color: {Colors.BACKGROUND_LIGHT};
            selection-background-color: {Colors.PRIMARY};
            selection-color: white;
            padding: 4px;
        }}
    """
    
    DATE_EDIT = f"""
        QDateEdit {{
            background-color: {Colors.BACKGROUND_LIGHT};
            border: 2px solid {Colors.BORDER};
            border-radius: 6px;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
            padding: 10px 14px;
            min-height: 36px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QDateEdit:focus {{
            border-color: {Colors.PRIMARY};
            background-color: {Colors.BACKGROUND_SOFT};
        }}
        QDateEdit::drop-down {{
            border: none;
            width: 30px;
        }}
        QDateEdit::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {Colors.PRIMARY};
        }}
    """
    
    RADIO_BUTTON = f"""
        QRadioButton {{
            color: {Colors.TEXT_PRIMARY};
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
            spacing: 8px;
        }}
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {Colors.BORDER};
            border-radius: 9px;
            background-color: {Colors.BACKGROUND_LIGHT};
        }}
        QRadioButton::indicator:checked {{
            background-color: {Colors.PRIMARY};
            border-color: {Colors.PRIMARY};
        }}
        QRadioButton::indicator:hover {{
            border-color: {Colors.PRIMARY_LIGHT};
        }}
    """
    
    TABLE_WIDGET = f"""
        QTableWidget {{
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
            background-color: {Colors.BACKGROUND_LIGHT};
            gridline-color: {Colors.BORDER_LIGHT};
            alternate-background-color: {Colors.BACKGROUND_SOFT};
        }}
        QTableWidget::item {{
            padding: 10px 8px;
            text-align: center;
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
        }}
        QTableWidget::item:selected {{
            background-color: {Colors.BACKGROUND_SOFT};
            color: {Colors.TEXT_PRIMARY};
        }}
        QHeaderView::section {{
            background-color: {Colors.PRIMARY};
            color: white;
            font-weight: {Fonts.WEIGHT_BOLD};
            font-size: {Fonts.SIZE_SMALL};
            padding: 12px 8px;
            text-align: center;
            border: none;
            border-right: 1px solid {Colors.PRIMARY_DARK};
        }}
        QHeaderView::section:first {{
            border-top-left-radius: 8px;
        }}
        QHeaderView::section:last {{
            border-top-right-radius: 8px;
            border-right: none;
        }}
        QTableCornerButton::section {{
            background-color: {Colors.PRIMARY};
            border: none;
        }}
    """
    
    LIST_WIDGET = f"""
        QListWidget {{
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            background-color: {Colors.BACKGROUND_LIGHT};
            font-family: {Fonts.FAMILY};
        }}
        QListWidget::item {{
            padding: 12px 16px;
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_PRIMARY};
            border-bottom: 1px solid {Colors.BORDER_LIGHT};
        }}
        QListWidget::item:hover {{
            background-color: {Colors.BACKGROUND_SOFT};
        }}
        QListWidget::item:last {{
            border-bottom: none;
        }}
    """
    
    SCROLL_AREA = f"""
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background-color: {Colors.BORDER_LIGHT};
            width: 10px;
            border-radius: 5px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {Colors.PRIMARY};
            border-radius: 5px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {Colors.PRIMARY_LIGHT};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background-color: {Colors.BORDER_LIGHT};
            height: 10px;
            border-radius: 5px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {Colors.PRIMARY};
            border-radius: 5px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {Colors.PRIMARY_LIGHT};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """
    
    STATUS_BAR = f"""
        QStatusBar {{
            background-color: {Colors.BACKGROUND_SOFT};
            color: {Colors.PRIMARY};
            border-top: 1px solid {Colors.BORDER};
            font-size: {Fonts.SIZE_SMALL};
            font-family: {Fonts.FAMILY};
        }}
    """
    
    PROGRESS_BAR = f"""
        QProgressBar {{
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
            background-color: {Colors.BORDER_LIGHT};
            text-align: center;
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.TEXT_TERTIARY};
            height: 8px;
        }}
        QProgressBar::chunk {{
            background-color: {Colors.PRIMARY};
            border-radius: 3px;
        }}
    """
    
    MENU_BAR = f"""
        QMenuBar {{
            background-color: {Colors.PRIMARY};
            color: white;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
            border: none;
        }}
        QMenuBar::item {{
            padding: 6px 16px;
            border-radius: 4px;
        }}
        QMenuBar::item:selected {{
            background-color: {Colors.PRIMARY_LIGHT};
        }}
        QMenu {{
            background-color: {Colors.BACKGROUND_LIGHT};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
            padding: 4px;
        }}
        QMenu::item {{
            padding: 8px 24px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {Colors.BACKGROUND_SOFT};
        }}
    """
    
    TOOL_BAR = f"""
        QToolBar {{
            background-color: {Colors.PRIMARY_LIGHT};
            border: none;
            spacing: 6px;
            padding: 4px;
        }}
        QToolButton {{
            background-color: transparent;
            color: white;
            padding: 8px 14px;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
            border-radius: 4px;
        }}
        QToolButton:hover {{
            background-color: {Colors.PRIMARY};
        }}
    """
