class Colors:
    PRIMARY = '#5D4037'
    PRIMARY_LIGHT = '#6B4423'
    PRIMARY_DARK = '#3D2A20'
    
    ACCENT = '#D4AF37'
    ACCENT_LIGHT = '#E8C850'
    ACCENT_DARK = '#B89600'
    
    BACKGROUND = '#F5F5F0'
    BACKGROUND_LIGHT = '#FFFFFF'
    
    TEXT_PRIMARY = '#333333'
    TEXT_SECONDARY = '#666666'
    TEXT_TERTIARY = '#999999'
    
    BORDER = '#E0E0E0'
    BORDER_LIGHT = '#F0F0F0'
    
    SUCCESS = '#228B22'
    WARNING = '#D2691E'
    ERROR = '#DC143C'
    INFO = '#1E90FF'

class Fonts:
    FAMILY = 'Microsoft YaHei'
    FAMILY_BOLD = 'SimHei'
    
    SIZE_TITLE = '16px'
    SIZE_SUBTITLE = '14px'
    SIZE_CARD_TITLE = '13px'
    SIZE_BODY = '12px'
    SIZE_SMALL = '11px'
    
    WEIGHT_NORMAL = 'Normal'
    WEIGHT_BOLD = 'Bold'

class Spacing:
    CARD_GAP = '12px'
    CARD_PADDING = '12px'
    CONTENT_PADDING = '15px'
    BUTTON_MIN_HEIGHT = '36px'
    BUTTON_MIN_WIDTH = '100px'
    LINE_HEIGHT = '1.5'

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
            border-radius: 6px;
        }}
    """
    
    CARD_HEADER = f"""
        QFrame {{
            background-color: {Colors.PRIMARY};
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
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
            border-radius: 4px;
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            font-family: {Fonts.FAMILY};
            padding: 8px 16px;
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
            border: 1px solid {Colors.PRIMARY};
            border-radius: 4px;
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            font-family: {Fonts.FAMILY};
            padding: 8px 16px;
            min-height: {Spacing.BUTTON_MIN_HEIGHT};
            min-width: {Spacing.BUTTON_MIN_WIDTH};
        }}
        QPushButton:hover {{
            background-color: {Colors.BORDER_LIGHT};
        }}
    """
    
    BUTTON_SMALL = f"""
        QPushButton {{
            background-color: {Colors.ACCENT};
            color: {Colors.PRIMARY};
            border: none;
            border-radius: 3px;
            font-size: {Fonts.SIZE_SMALL};
            font-weight: {Fonts.WEIGHT_BOLD};
            font-family: {Fonts.FAMILY};
            padding: 4px 8px;
        }}
        QPushButton:hover {{
            background-color: {Colors.ACCENT_LIGHT};
        }}
    """
    
    LINE_EDIT = f"""
        QLineEdit {{
            background-color: {Colors.BACKGROUND_LIGHT};
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
            padding: 6px 10px;
            min-height: 32px;
        }}
        QLineEdit:focus {{
            border-color: {Colors.PRIMARY};
        }}
    """
    
    COMBO_BOX = f"""
        QComboBox {{
            background-color: {Colors.BACKGROUND_LIGHT};
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
            padding: 6px 10px;
            min-height: 32px;
        }}
        QComboBox:focus {{
            border-color: {Colors.PRIMARY};
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid {Colors.PRIMARY};
        }}
    """
    
    DATE_EDIT = f"""
        QDateEdit {{
            background-color: {Colors.BACKGROUND_LIGHT};
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
            padding: 6px 10px;
            min-height: 32px;
        }}
        QDateEdit:focus {{
            border-color: {Colors.PRIMARY};
        }}
    """
    
    RADIO_BUTTON = f"""
        QRadioButton {{
            color: {Colors.TEXT_PRIMARY};
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
        }}
        QRadioButton::indicator {{
            width: 14px;
            height: 14px;
            border: 1px solid {Colors.PRIMARY};
            border-radius: 7px;
            background-color: white;
        }}
        QRadioButton::indicator:checked {{
            background-color: {Colors.PRIMARY};
        }}
    """
    
    TABLE_WIDGET = f"""
        QTableWidget {{
            border: none;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
            background-color: transparent;
        }}
        QTableWidget::item {{
            padding: 6px;
            text-align: center;
        }}
        QTableWidget::item:selected {{
            background-color: {Colors.BORDER_LIGHT};
        }}
        QHeaderView::section {{
            background-color: {Colors.PRIMARY};
            color: white;
            font-weight: {Fonts.WEIGHT_BOLD};
            font-size: {Fonts.SIZE_SMALL};
            padding: 6px;
            text-align: center;
            border: none;
        }}
    """
    
    LIST_WIDGET = f"""
        QListWidget {{
            border: none;
            background-color: transparent;
            font-family: {Fonts.FAMILY};
        }}
        QListWidget::item {{
            padding: 8px;
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_PRIMARY};
        }}
        QListWidget::item:hover {{
            background-color: {Colors.BORDER_LIGHT};
        }}
    """
    
    SCROLL_AREA = f"""
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background-color: {Colors.BORDER_LIGHT};
            width: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {Colors.PRIMARY};
            border-radius: 3px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
    """
    
    STATUS_BAR = f"""
        QStatusBar {{
            background-color: {Colors.BORDER_LIGHT};
            color: {Colors.PRIMARY};
            border-top: 1px solid {Colors.BORDER};
            font-size: {Fonts.SIZE_SMALL};
            font-family: {Fonts.FAMILY};
        }}
    """
    
    PROGRESS_BAR = f"""
        QProgressBar {{
            border: 1px solid {Colors.BORDER};
            border-radius: 3px;
            background-color: {Colors.BORDER_LIGHT};
            text-align: center;
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.PRIMARY};
            height: 6px;
        }}
        QProgressBar::chunk {{
            background-color: {Colors.PRIMARY};
            border-radius: 2px;
        }}
    """
    
    MENU_BAR = f"""
        QMenuBar {{
            background-color: {Colors.PRIMARY};
            color: white;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
        }}
        QMenuBar::item {{
            padding: 4px 12px;
        }}
        QMenuBar::item:selected {{
            background-color: {Colors.PRIMARY_LIGHT};
        }}
        QMenu {{
            background-color: {Colors.BACKGROUND_LIGHT};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER};
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
        }}
        QMenu::item {{
            padding: 6px 20px;
        }}
        QMenu::item:selected {{
            background-color: {Colors.BORDER_LIGHT};
        }}
    """
    
    TOOL_BAR = f"""
        QToolBar {{
            background-color: {Colors.PRIMARY_LIGHT};
            border: none;
            spacing: 4px;
        }}
        QToolButton {{
            background-color: transparent;
            color: white;
            padding: 6px 10px;
            font-size: {Fonts.SIZE_BODY};
            font-family: {Fonts.FAMILY};
        }}
        QToolButton:hover {{
            background-color: {Colors.PRIMARY};
        }}
    """