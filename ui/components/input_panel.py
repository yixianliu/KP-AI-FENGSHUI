from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QComboBox, QPushButton, QFrame, QCheckBox, QSizePolicy,
                             QGraphicsOpacityEffect, QSpacerItem)
from PySide6.QtCore import QDate, QTime, Qt, QEvent, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QEnterEvent, QMouseEvent
from ui.styles import Stylesheets, Colors, Fonts, Spacing

HOUR_NAMES = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时',
              '午时', '未时', '申时', '酉时', '戌时', '亥时']
HOUR_RANGES = [(23, 1), (1, 3), (3, 5), (5, 7), (7, 9), (9, 11),
               (11, 13), (13, 15), (15, 17), (17, 19), (19, 21), (21, 23)]

CITIES = [
    ('北京', (116.4074, 39.9042)),
    ('上海', (121.4737, 31.2304)),
    ('广州', (113.2644, 23.1291)),
    ('深圳', (114.0579, 22.5431)),
    ('杭州', (120.1552, 30.2875)),
    ('南京', (118.7969, 32.0603)),
    ('成都', (104.0668, 30.5728)),
    ('武汉', (114.3055, 30.5928)),
    ('西安', (108.948, 34.2631)),
    ('重庆', (106.5516, 29.563)),
    ('天津', (117.2008, 39.0842)),
    ('苏州', (120.6293, 31.3251)),
    ('郑州', (113.6243, 34.7466)),
    ('长沙', (112.9388, 28.228)),
    ('青岛', (120.3316, 36.0671)),
    ('沈阳', (123.4328, 41.8045)),
    ('大连', (121.6147, 38.914)),
    ('宁波', (121.5429, 29.8753)),
    ('无锡', (120.3199, 31.573)),
    ('佛山', (113.1064, 23.0208)),
]


class InputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_validation()
        self.installEventFilter(self)

    def init_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.CARD_RADIUS};
            }}
        """)

        main_layout = QVBoxLayout()
        card_padding = int(Spacing.CARD_PADDING.replace('px', ''))
        module_gap = int(Spacing.MODULE_GAP.replace('px', ''))
        main_layout.setContentsMargins(card_padding, card_padding, card_padding, card_padding)
        main_layout.setSpacing(module_gap)

        # ===== 标题区域 =====
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        title_layout.setAlignment(Qt.AlignCenter)

        title_icon = QLabel('☯')
        title_icon.setStyleSheet(f"font-size: 22px; color: {Colors.ACCENT};")

        title_label = QLabel('八字排盘')
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_TITLE};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)

        subtitle_label = QLabel('专业精准排盘')
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet(Stylesheets.HEADER_SUBTITLE)

        main_layout.addLayout(title_layout)
        main_layout.addWidget(subtitle_label)

        # 分隔线
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT};")
        main_layout.addWidget(separator)

        # ===== 表单区域 =====
        form_layout = QVBoxLayout()
        form_layout.setSpacing(14)

        # 姓名输入 - 带图标
        name_section = self._create_section_card('👤', '命主姓名', self._create_name_content())
        form_layout.addWidget(name_section)

        # 性别选择
        gender_section = self._create_section_card('⚥', '性别', self._create_gender_content())
        form_layout.addWidget(gender_section)

        # 历法选择
        calendar_section = self._create_section_card('📅', '历法', self._create_calendar_content())
        form_layout.addWidget(calendar_section)

        # 出生日期
        date_section = self._create_section_card('🎂', '出生日期', self._create_date_content())
        form_layout.addWidget(date_section)

        # 出生时辰
        hour_section = self._create_section_card('⏰', '出生时辰', self._create_hour_content())
        form_layout.addWidget(hour_section)

        # 出生地点
        location_section = self._create_section_card('📍', '出生地点', self._create_location_content())
        form_layout.addWidget(location_section)

        # 高级设置
        advanced_section = self._create_advanced_section()
        form_layout.addWidget(advanced_section)

        main_layout.addLayout(form_layout)

        # ===== 验证提示 =====
        self.validation_hint = QLabel('')
        self.validation_hint.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.WARNING};
            font-family: {Fonts.FAMILY_CN};
            padding: 8px 12px;
            background-color: rgba(156, 68, 68, 0.06);
            border-radius: {Spacing.CONTROL_RADIUS};
            border-left: 3px solid {Colors.WARNING};
        """)
        self.validation_hint.setVisible(False)
        self.validation_hint.setWordWrap(True)
        main_layout.addWidget(self.validation_hint)

        # ===== 按钮区域 =====
        button_layout = QHBoxLayout()
        button_layout.setSpacing(14)
        button_layout.setAlignment(Qt.AlignCenter)

        self.reset_btn = QPushButton('🔄 重置清空')
        self.reset_btn.setStyleSheet(self._secondary_btn_style())
        self.reset_btn.setCursor(Qt.PointingHandCursor)

        self.submit_btn = QPushButton('✨ 精准排盘')
        self.submit_btn.setStyleSheet(self._primary_btn_style())
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setEnabled(False)

        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.submit_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    # ===== 样式生成方法 =====
    def _section_card_style(self):
        return f"""
            QFrame {{
                background-color: {Colors.BACKGROUND};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CONTROL_RADIUS};
            }}
        """

    def _input_style(self):
        return f"""
            QLineEdit {{
                background-color: {Colors.CARD};
                border: 2px solid {Colors.BORDER};
                border-radius: {Spacing.CONTROL_RADIUS};
                font-size: {Fonts.SIZE_BODY};
                font-family: {Fonts.FAMILY_CN};
                padding: 8px 12px;
                min-height: 36px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 2px solid {Colors.ACCENT};
            }}
            QLineEdit::placeholder {{
                color: {Colors.TEXT_TERTIARY};
                font-style: italic;
            }}
        """

    def _combo_style(self):
        return f"""
            QComboBox {{
                background-color: {Colors.CARD};
                border: 2px solid {Colors.BORDER};
                border-radius: {Spacing.CONTROL_RADIUS};
                font-size: {Fonts.SIZE_BODY};
                font-family: {Fonts.FAMILY_CN};
                padding: 6px 10px;
                min-height: 36px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QComboBox:focus, QComboBox:on {{
                border: 2px solid {Colors.ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 28px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {Colors.ACCENT};
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

    def _toggle_style(self):
        return f"""
            QPushButton {{
                background-color: {Colors.CARD};
                color: {Colors.TEXT_SECONDARY};
                border: 2px solid {Colors.BORDER};
                border-radius: {Spacing.CONTROL_RADIUS};
                font-size: {Fonts.SIZE_BODY};
                font-weight: {Fonts.WEIGHT_NORMAL};
                font-family: {Fonts.FAMILY_CN};
                padding: 7px 16px;
                min-width: 80px;
                min-height: 34px;
            }}
            QPushButton:hover {{
                border-color: {Colors.ACCENT};
                color: {Colors.ACCENT};
                background-color: rgba(42, 74, 63, 0.04);
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

    def _primary_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: {Spacing.CARD_RADIUS};
                font-size: 15px;
                font-weight: {Fonts.WEIGHT_BOLD};
                font-family: {Fonts.FAMILY_CN};
                padding: 10px 28px;
                min-height: 42px;
                min-width: 130px;
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

    def _secondary_btn_style(self):
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BUTTON_SECONDARY_BORDER};
                border-radius: {Spacing.CARD_RADIUS};
                font-size: {Fonts.SIZE_BODY};
                font-weight: {Fonts.WEIGHT_NORMAL};
                font-family: {Fonts.FAMILY_CN};
                padding: 8px 20px;
                min-height: 42px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                border-color: {Colors.ACCENT};
                color: {Colors.ACCENT};
                background-color: rgba(42, 74, 63, 0.04);
            }}
            QPushButton:pressed {{
                background-color: rgba(42, 74, 63, 0.08);
            }}
        """

    def _label_style(self):
        return f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """

    def _hint_style(self):
        return f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
            padding-left: 2px;
        """

    # ===== 分组卡片构建器 =====
    def _create_section_card(self, icon, title, content_widget):
        """创建一个带图标标题的分组卡片"""
        card = QFrame()
        card.setStyleSheet(self._section_card_style())

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # 标题行：图标 + 文字
        header = QHBoxLayout()
        header.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 16px;")

        title_label = QLabel(title)
        title_label.setStyleSheet(self._label_style())

        header.addWidget(icon_label)
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)
        layout.addWidget(content_widget)

        return card

    # ===== 各字段内容构建 =====
    def _create_name_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.name_lineedit = QLineEdit()
        self.name_lineedit.setStyleSheet(self._input_style())
        self.name_lineedit.setPlaceholderText('请输入命主姓名')
        self.name_lineedit.setMinimumHeight(36)
        self.name_lineedit.textChanged.connect(self._on_name_changed)

        layout.addWidget(self.name_lineedit)
        return widget

    def _create_gender_content(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.male_btn = QPushButton('乾造（男）')
        self.male_btn.setStyleSheet(self._toggle_style())
        self.male_btn.setCheckable(True)
        self.male_btn.setChecked(True)
        self.male_btn.setCursor(Qt.PointingHandCursor)

        self.female_btn = QPushButton('坤造（女）')
        self.female_btn.setStyleSheet(self._toggle_style())
        self.female_btn.setCheckable(True)
        self.female_btn.setCursor(Qt.PointingHandCursor)

        layout.addWidget(self.male_btn)
        layout.addWidget(self.female_btn)
        layout.addStretch()

        return widget

    def _create_calendar_content(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.solar_btn = QPushButton('公历')
        self.solar_btn.setStyleSheet(self._toggle_style())
        self.solar_btn.setCheckable(True)
        self.solar_btn.setChecked(True)
        self.solar_btn.setCursor(Qt.PointingHandCursor)

        self.lunar_btn = QPushButton('农历')
        self.lunar_btn.setStyleSheet(self._toggle_style())
        self.lunar_btn.setCheckable(True)
        self.lunar_btn.setCursor(Qt.PointingHandCursor)

        layout.addWidget(self.solar_btn)
        layout.addWidget(self.lunar_btn)
        layout.addStretch()

        return widget

    def _create_date_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        date_row = QHBoxLayout()
        date_row.setSpacing(8)

        self.year_combo = QComboBox()
        self.year_combo.setStyleSheet(self._combo_style())
        self.year_combo.setMinimumWidth(100)
        current_year = QDate.currentDate().year()
        for year in range(1900, current_year + 1):
            self.year_combo.addItem(f'{year}年', year)
        self.year_combo.setCurrentIndex(self.year_combo.count() - 1)

        self.month_combo = QComboBox()
        self.month_combo.setStyleSheet(self._combo_style())
        self.month_combo.setMinimumWidth(70)
        for month in range(1, 13):
            self.month_combo.addItem(f'{month}月', month)
        self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)

        self.day_combo = QComboBox()
        self.day_combo.setStyleSheet(self._combo_style())
        self.day_combo.setMinimumWidth(70)
        self._update_day_combo()
        self.day_combo.setCurrentIndex(QDate.currentDate().day() - 1)

        date_row.addWidget(self.year_combo)
        date_row.addWidget(self.month_combo)
        date_row.addWidget(self.day_combo)
        date_row.addStretch()

        hint_label = QLabel('选择日期后将自动匹配节气')
        hint_label.setStyleSheet(self._hint_style())

        layout.addLayout(date_row)
        layout.addWidget(hint_label)

        return widget

    def _create_hour_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        hour_row = QHBoxLayout()
        hour_row.setSpacing(8)

        self.hour_combo = QComboBox()
        self.hour_combo.setStyleSheet(self._combo_style())
        self.hour_combo.setMinimumWidth(140)
        self.hour_combo.setMaximumWidth(180)

        for i, name in enumerate(HOUR_NAMES):
            start, end = HOUR_RANGES[i]
            if start == 23:
                time_range = "23:00-00:59"
            else:
                time_range = f"{start:02d}:00-{end:02d}:59"
            self.hour_combo.addItem(f"{name} ({time_range})", i)

        self.time_edit = QLineEdit()
        self.time_edit.setStyleSheet(self._input_style())
        self.time_edit.setPlaceholderText('时:分')
        self.time_edit.setMaximumWidth(85)
        self.time_edit.setText('12:00')
        self.time_edit.textChanged.connect(self._on_time_changed)

        hour_row.addWidget(self.hour_combo)
        hour_row.addWidget(self.time_edit)
        hour_row.addStretch()

        # 早晚子时行
        zi_row = QHBoxLayout()
        zi_row.setSpacing(8)

        zi_label = QLabel('早晚子时')
        zi_label.setStyleSheet(Stylesheets.LABEL_SMALL)

        self.early_zi_switch = QCheckBox()
        self.early_zi_switch.setStyleSheet(Stylesheets.TOGGLE_SWITCH)
        self.early_zi_switch.setChecked(False)

        zi_desc = QLabel('启用早子时')
        zi_desc.setStyleSheet(Stylesheets.LABEL_SMALL)

        zi_row.addWidget(zi_label)
        zi_row.addWidget(self.early_zi_switch)
        zi_row.addWidget(zi_desc)
        zi_row.addStretch()

        layout.addLayout(hour_row)
        layout.addLayout(zi_row)

        return widget

    def _create_location_content(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.city_combo = QComboBox()
        self.city_combo.setStyleSheet(self._combo_style())
        self.city_combo.setMinimumWidth(140)
        for city, coords in CITIES:
            self.city_combo.addItem(city, coords)

        self.lat_label = QLabel('')
        self.lat_label.setStyleSheet(self._hint_style())
        self.lat_label.setMaximumWidth(150)

        layout.addWidget(self.city_combo)
        layout.addWidget(self.lat_label)
        layout.addStretch()

        self._update_coords_label()

        return widget

    def _create_advanced_section(self):
        """高级设置 - 可折叠卡片"""
        card = QFrame()
        card.setStyleSheet(self._section_card_style())

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 头部（可点击折叠）
        header = QFrame()
        header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: {Spacing.CONTROL_RADIUS};
            }}
            QFrame:hover {{
                background-color: rgba(42, 74, 63, 0.03);
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(8)

        header_icon = QLabel('⚙️')
        header_icon.setStyleSheet("font-size: 16px;")

        header_title = QLabel('高级设置')
        header_title.setStyleSheet(self._label_style())

        self.advanced_arrow = QLabel('▼')
        self.advanced_arrow.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; font-size: 12px;")

        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(self.advanced_arrow)

        # 内容区域（默认折叠）
        self.advanced_content = QWidget()
        self.advanced_content.setVisible(False)
        content_layout = QVBoxLayout(self.advanced_content)
        content_layout.setContentsMargins(14, 0, 14, 14)
        content_layout.setSpacing(10)

        # 真太阳时校正
        solar_time_row = self._create_combo_row('真太阳时校正', ['自动', '启用', '禁用'])
        content_layout.addLayout(solar_time_row)

        # 起运计算规则
        age_rule_row = self._create_combo_row('起运计算规则', ['虚岁', '周岁'])
        content_layout.addLayout(age_rule_row)

        # 闰月处理方式
        leap_rule_row = self._create_combo_row('闰月处理方式', ['归前', '归后', '独立'])
        content_layout.addLayout(leap_rule_row)

        layout.addWidget(header)
        layout.addWidget(self.advanced_content)

        # 点击头部切换折叠
        header.mousePressEvent = lambda e: self._toggle_advanced()

        return card

    def _create_combo_row(self, label_text, items):
        """创建标签+下拉框的行"""
        row = QHBoxLayout()
        row.setSpacing(10)

        label = QLabel(label_text)
        label.setStyleSheet(Stylesheets.LABEL_BODY)
        label.setMinimumWidth(90)

        combo = QComboBox()
        combo.setStyleSheet(self._combo_style())
        combo.setMinimumWidth(130)
        combo.addItems(items)

        # 保存引用
        if label_text == '真太阳时校正':
            self.solar_time_combo = combo
        elif label_text == '起运计算规则':
            self.age_rule_combo = combo
        elif label_text == '闰月处理方式':
            self.leap_rule_combo = combo

        row.addWidget(label)
        row.addWidget(combo)
        row.addStretch()

        return row

    # ===== 数据更新方法 =====
    def _update_day_combo(self):
        year = self.year_combo.currentData() if self.year_combo else QDate.currentDate().year()
        month = self.month_combo.currentData() if self.month_combo else QDate.currentDate().month()

        days_in_month = self._get_days_in_month(year, month)
        current_day = self.day_combo.currentData()

        self.day_combo.clear()
        for day in range(1, days_in_month + 1):
            self.day_combo.addItem(f'{day}日', day)

        if current_day and current_day <= days_in_month:
            self.day_combo.setCurrentIndex(current_day - 1)
        else:
            self.day_combo.setCurrentIndex(min(self.day_combo.count() - 1, 0))

    def _update_coords_label(self):
        coords = self.city_combo.currentData()
        if coords:
            lat, lng = coords
            self.lat_label.setText(f'坐标: {lat:.4f}, {lng:.4f}')
        else:
            self.lat_label.setText('')

    def _get_days_in_month(self, year, month):
        if month in [4, 6, 9, 11]:
            return 30
        elif month == 2:
            if self._is_leap_year(year):
                return 29
            else:
                return 28
        else:
            return 31

    def _is_leap_year(self, year):
        if year % 4 != 0:
            return False
        elif year % 100 != 0:
            return True
        elif year % 400 != 0:
            return False
        else:
            return True

    # ===== 事件与验证 =====
    def setup_validation(self):
        self.city_combo.currentIndexChanged.connect(self._update_coords_label)
        self.submit_btn.clicked.connect(self.on_submit_clicked)
        self.reset_btn.clicked.connect(self.clear)
        self.male_btn.clicked.connect(lambda: self._on_gender_toggle(True))
        self.female_btn.clicked.connect(lambda: self._on_gender_toggle(False))
        self.solar_btn.clicked.connect(lambda: self._on_calendar_toggle(True))
        self.lunar_btn.clicked.connect(lambda: self._on_calendar_toggle(False))
        self.year_combo.currentIndexChanged.connect(self._update_day_combo)
        self.month_combo.currentIndexChanged.connect(self._update_day_combo)
        self.hour_combo.currentIndexChanged.connect(self._update_time_from_hour)

    def _on_name_changed(self, text):
        self.validate_input()

    def _on_time_changed(self, text):
        self.validate_input()

    def _toggle_advanced(self):
        is_visible = not self.advanced_content.isVisible()
        self.advanced_content.setVisible(is_visible)
        self.advanced_arrow.setText('▲' if is_visible else '▼')

    def _on_gender_toggle(self, is_male):
        self.male_btn.setChecked(is_male)
        self.female_btn.setChecked(not is_male)

    def _on_calendar_toggle(self, is_solar):
        self.solar_btn.setChecked(is_solar)
        self.lunar_btn.setChecked(not is_solar)

    def _update_time_from_hour(self):
        hour_index = self.hour_combo.currentData()
        start, end = HOUR_RANGES[hour_index]
        if start == 23:
            self.time_edit.setText('23:00')
        else:
            self.time_edit.setText(f"{start:02d}:00")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusOut:
            if obj == self.name_lineedit:
                self.validate_input()
        return super().eventFilter(obj, event)

    def validate_input(self):
        name = self.name_lineedit.text().strip()
        time_text = self.time_edit.text().strip()

        if not name:
            self.validation_hint.setText('请输入姓名')
            self.validation_hint.setVisible(True)
            self.submit_btn.setEnabled(False)
            return False

        if len(name) > 20:
            self.validation_hint.setText('姓名不能超过20个字符')
            self.validation_hint.setVisible(True)
            self.submit_btn.setEnabled(False)
            return False

        if not time_text:
            self.validation_hint.setText('请输入出生时间')
            self.validation_hint.setVisible(True)
            self.submit_btn.setEnabled(False)
            return False

        try:
            hh, mm = map(int, time_text.split(':'))
            if hh < 0 or hh > 23 or mm < 0 or mm > 59:
                self.validation_hint.setText('时间格式错误，请输入有效的时分（00:00-23:59）')
                self.validation_hint.setVisible(True)
                self.submit_btn.setEnabled(False)
                return False
        except:
            self.validation_hint.setText('时间格式错误，请使用 时:分 格式')
            self.validation_hint.setVisible(True)
            self.submit_btn.setEnabled(False)
            return False

        self.validation_hint.setVisible(False)
        self.submit_btn.setEnabled(True)
        return True

    def on_submit_clicked(self):
        if not self.validate_input():
            pass

    def get_data(self):
        hour_index = self.hour_combo.currentData()

        try:
            hh, mm = map(int, self.time_edit.text().split(':'))
        except:
            hh, mm = 12, 0

        city, coords = CITIES[self.city_combo.currentIndex()]

        return {
            'name': self.name_lineedit.text().strip(),
            'gender': '男' if self.male_btn.isChecked() else '女',
            'is_lunar': self.lunar_btn.isChecked(),
            'year': self.year_combo.currentData(),
            'month': self.month_combo.currentData(),
            'day': self.day_combo.currentData(),
            'hour': hh,
            'minute': mm,
            'hour_index': hour_index,
            'is_early_zi': self.early_zi_switch.isChecked(),
            'city': city,
            'latitude': coords[0],
            'longitude': coords[1],
            'solar_time_mode': self.solar_time_combo.currentText(),
            'age_type': '虚岁' if self.age_rule_combo.currentText() == '虚岁' else 'real',
            'leap_rule': self.leap_rule_combo.currentText()
        }

    def clear(self):
        current_year = QDate.currentDate().year()
        current_month = QDate.currentDate().month()
        current_day = QDate.currentDate().day()

        self.name_lineedit.clear()
        self.male_btn.setChecked(True)
        self.female_btn.setChecked(False)
        self.solar_btn.setChecked(True)
        self.lunar_btn.setChecked(False)
        self.year_combo.setCurrentIndex(self.year_combo.count() - 1)
        self.month_combo.setCurrentIndex(current_month - 1)
        self._update_day_combo()
        self.day_combo.setCurrentIndex(current_day - 1)
        self.time_edit.setText('12:00')
        self.hour_combo.setCurrentIndex(self.get_hour_index(QTime.currentTime().hour()))
        self.early_zi_switch.setChecked(False)
        self.city_combo.setCurrentIndex(0)
        self._update_coords_label()
        self.solar_time_combo.setCurrentIndex(0)
        self.age_rule_combo.setCurrentIndex(0)
        self.leap_rule_combo.setCurrentIndex(0)
        self.advanced_content.setVisible(False)
        self.advanced_arrow.setText('▼')
        self.validation_hint.setVisible(False)
        self.submit_btn.setEnabled(False)

    def get_hour_index(self, hour):
        for i, (start, end) in enumerate(HOUR_RANGES):
            if start == 23:
                if hour >= 23 or hour < end:
                    return i
            elif start <= hour < end:
                return i
        return 0
