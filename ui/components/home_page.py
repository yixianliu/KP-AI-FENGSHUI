from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QComboBox, QPushButton, QLineEdit,
                             QButtonGroup, QScrollArea)
from PySide6.QtCore import Qt, Signal, QDate
from ui.styles import Stylesheets, Colors, Fonts
from ui.components.input_panel import CITIES, HOUR_NAMES, HOUR_RANGES


class HomePage(QWidget):
    """首页输入面板 - 复用 input_panel 中已定义的常量"""

    start_panpan = Signal(dict)
    back_to_home = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_lunar = False
        self.is_early_zi = False
        self.current_city = '北京'
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.BACKGROUND};
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(32)
        main_layout.setAlignment(Qt.AlignCenter)

        # 标题
        title_label = QLabel('八字排盘 · 专业精准排盘')
        title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY_SERIF};
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        subtitle_label = QLabel('传统命理 · 精准排盘 · AI分析')
        subtitle_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)

        # 表单卡片
        form_frame = QFrame()
        form_frame.setStyleSheet(Stylesheets.CARD)
        form_frame.setMinimumWidth(600)
        form_frame.setMaximumWidth(700)

        scroll_area = QScrollArea()
        scroll_area.setStyleSheet(Stylesheets.SCROLL_AREA)
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(28, 28, 28, 28)
        scroll_layout.setSpacing(20)

        # 性别
        scroll_layout.addLayout(self._create_toggle_row('性别', ['乾造（男）', '坤造（女）'], 'gender'))
        # 历法
        scroll_layout.addLayout(self._create_toggle_row('历法', ['公历', '农历'], 'calendar'))
        # 出生日期
        scroll_layout.addLayout(self._create_date_section())
        # 出生时辰
        scroll_layout.addLayout(self._create_hour_section())
        # 出生地
        scroll_layout.addLayout(self._create_city_section())

        scroll_area.setWidget(scroll_content)

        form_main_layout = QVBoxLayout(form_frame)
        form_main_layout.addWidget(scroll_area)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        button_layout.setContentsMargins(28, 16, 28, 28)
        button_layout.setAlignment(Qt.AlignCenter)

        self.reset_btn = QPushButton('重置')
        self.reset_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)
        self.reset_btn.setMinimumWidth(100)

        self.start_btn = QPushButton('精准排盘')
        self.start_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        self.start_btn.setMinimumWidth(140)

        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.start_btn)

        form_main_layout.addLayout(button_layout)
        main_layout.addWidget(form_frame)
        self.setLayout(main_layout)

    def _create_toggle_row(self, label_text, items, group_name):
        """创建切换按钮行"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        label = QLabel(label_text)
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)

        group = QButtonGroup(self)
        group.setExclusive(True)

        btns = []
        for idx, item in enumerate(items):
            btn = QPushButton(item)
            btn.setStyleSheet(Stylesheets.BUTTON_SWITCH)
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            group.addButton(btn, idx)
            button_layout.addWidget(btn)
            btns.append(btn)

        button_layout.addStretch()

        # 保存引用
        if group_name == 'gender':
            self.male_btn, self.female_btn = btns
        elif group_name == 'calendar':
            self.solar_btn, self.lunar_btn = btns

        layout.addWidget(label)
        layout.addLayout(button_layout)
        return layout

    def _create_date_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        label = QLabel('出生日期')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        date_layout = QHBoxLayout()
        date_layout.setSpacing(12)

        self.date_edit = QLineEdit()
        self.date_edit.setStyleSheet(Stylesheets.LINE_EDIT)
        self.date_edit.setPlaceholderText('YYYY-MM-DD')
        self.date_edit.setMaximumWidth(200)
        today = QDate.currentDate()
        self.date_edit.setText(today.toString('yyyy-MM-dd'))

        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()

        layout.addWidget(label)
        layout.addLayout(date_layout)
        return layout

    def _create_hour_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        label = QLabel('出生时辰')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        hour_layout = QHBoxLayout()
        hour_layout.setSpacing(12)

        self.hour_combo = QComboBox()
        self.hour_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.hour_combo.setMinimumWidth(180)
        for i, name in enumerate(HOUR_NAMES):
            start, end = HOUR_RANGES[i]
            time_range = "23:00-00:59" if start == 23 else f"{start:02d}:00-{end:02d}:59"
            self.hour_combo.addItem(f"{name} ({time_range})", i)

        self.time_edit = QLineEdit()
        self.time_edit.setStyleSheet(Stylesheets.LINE_EDIT)
        self.time_edit.setPlaceholderText('时:分')
        self.time_edit.setMaximumWidth(100)
        self.time_edit.setText('12:00')

        hour_layout.addWidget(self.hour_combo)
        hour_layout.addWidget(self.time_edit)
        hour_layout.addStretch()

        layout.addWidget(label)
        layout.addLayout(hour_layout)
        return layout

    def _create_city_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        label = QLabel('出生地')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        city_layout = QHBoxLayout()
        city_layout.setSpacing(12)

        self.city_combo = QComboBox()
        self.city_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.city_combo.setMinimumWidth(200)
        for city, coords in CITIES:
            self.city_combo.addItem(city, coords)
        self.city_combo.setCurrentIndex(0)

        city_layout.addWidget(self.city_combo)
        city_layout.addStretch()

        layout.addWidget(label)
        layout.addLayout(city_layout)
        return layout

    def connect_signals(self):
        self.male_btn.clicked.connect(lambda: self._on_gender_toggle(True))
        self.female_btn.clicked.connect(lambda: self._on_gender_toggle(False))
        self.solar_btn.clicked.connect(lambda: self._on_calendar_toggle(True))
        self.lunar_btn.clicked.connect(lambda: self._on_calendar_toggle(False))
        self.hour_combo.currentIndexChanged.connect(self._update_time_from_hour)
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.reset_btn.clicked.connect(self.reset)

    def _on_gender_toggle(self, is_male):
        self.male_btn.setChecked(is_male)
        self.female_btn.setChecked(not is_male)

    def _on_calendar_toggle(self, is_solar):
        self.solar_btn.setChecked(is_solar)
        self.lunar_btn.setChecked(not is_solar)
        self.is_lunar = not is_solar

    def _update_time_from_hour(self):
        hour_index = self.hour_combo.currentData()
        if hour_index is None:
            return
        start, end = HOUR_RANGES[hour_index]
        self.time_edit.setText('23:00' if start == 23 else f"{start:02d}:00")

    def _on_start_clicked(self):
        if self.validate_input():
            self.start_panpan.emit(self.get_data())

    def validate_input(self):
        date_text = self.date_edit.text().strip()
        try:
            year, month, day = map(int, date_text.split('-'))
            if year < 1900 or year > 2100 or month < 1 or month > 12 or day < 1 or day > 31:
                return False
        except:
            return False

        time_text = self.time_edit.text().strip()
        try:
            hh, mm = map(int, time_text.split(':'))
            if hh < 0 or hh > 23 or mm < 0 or mm > 59:
                return False
        except:
            return False

        return True

    def get_data(self):
        date_text = self.date_edit.text().strip()
        try:
            year, month, day = map(int, date_text.split('-'))
        except:
            year, month, day = 2000, 1, 1

        try:
            hh, mm = map(int, self.time_edit.text().split(':'))
        except:
            hh, mm = 12, 0

        city, coords = CITIES[self.city_combo.currentIndex()]

        return {
            'name': '',
            'year': year,
            'month': month,
            'day': day,
            'hour': hh,
            'minute': mm,
            'hour_index': self.hour_combo.currentData() or 0,
            'gender': '男' if self.male_btn.isChecked() else '女',
            'is_lunar': self.is_lunar,
            'is_early_zi': self.is_early_zi,
            'city': city,
            'longitude': coords[0],
            'latitude': coords[1],
            'pan_type': 'bazi',
        }

    def reset(self):
        self.male_btn.setChecked(True)
        self.female_btn.setChecked(False)
        self.solar_btn.setChecked(True)
        self.lunar_btn.setChecked(False)
        self.is_lunar = False
        self.date_edit.setText(QDate.currentDate().toString('yyyy-MM-dd'))
        self.time_edit.setText('12:00')
        self.hour_combo.setCurrentIndex(0)
        self.city_combo.setCurrentIndex(0)
        self.current_city = '北京'
