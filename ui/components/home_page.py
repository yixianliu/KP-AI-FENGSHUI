from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QComboBox, QPushButton, QLineEdit,
                             QRadioButton, QButtonGroup, QSpacerItem,
                             QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from ui.styles import Stylesheets, Colors, Fonts
from utils.calendar import solar_to_lunar, lunar_to_solar
from utils.solar_time import (CITIES, get_city_data, calculate_true_solar_time,
                            get_solar_term_info, get_correction_display)

HOUR_NAMES = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时', 
              '午时', '未时', '申时', '酉时', '戌时', '亥时']
HOUR_RANGES = [(23, 1), (1, 3), (3, 5), (5, 7), (7, 9), (9, 11),
               (11, 13), (13, 15), (15, 17), (17, 19), (19, 21), (21, 23)]


class HomePage(QWidget):
    start_panpan = pyqtSignal(dict)
    back_to_home = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_lunar = False
        self.is_early_zi = False
        self.solar_time_mode = 'auto'
        self.current_city = '北京'
        self.init_ui()
        self.connect_signals()
        self._update_solar_term_info()
        self._update_solar_time_correction()
    
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
        
        header_frame = self._create_header_section()
        main_layout.addWidget(header_frame)
        
        form_frame = self._create_form_section()
        main_layout.addWidget(form_frame)
        
        self.setLayout(main_layout)
    
    def _create_header_section(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)
        
        title_label = QLabel('八字排盘 · 专业精准排盘')
        title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY_BOLD};
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        subtitle_label = QLabel('传统命理 · 精准排盘 · AI分析')
        subtitle_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SUBTITLE};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY};
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        
        frame.setLayout(layout)
        return frame
    
    def _create_form_section(self):
        frame = QFrame()
        frame.setStyleSheet(Stylesheets.CARD)
        frame.setMinimumWidth(600)
        frame.setMaximumWidth(700)
        
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet(Stylesheets.SCROLL_AREA)
        scroll_area.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(28, 28, 28, 28)
        scroll_layout.setSpacing(20)
        
        gender_section = self._create_gender_section()
        scroll_layout.addLayout(gender_section)
        
        calendar_section = self._create_calendar_section()
        scroll_layout.addLayout(calendar_section)
        
        date_section = self._create_date_section()
        scroll_layout.addLayout(date_section)
        
        term_hint_section = self._create_term_hint_section()
        scroll_layout.addLayout(term_hint_section)
        
        hour_section = self._create_hour_section()
        scroll_layout.addLayout(hour_section)
        
        city_section = self._create_city_section()
        scroll_layout.addLayout(city_section)
        
        advanced_section = self._create_advanced_section()
        scroll_layout.addWidget(advanced_section)
        
        scroll_area.setWidget(scroll_content)
        
        main_layout = QVBoxLayout(frame)
        main_layout.addWidget(scroll_area)
        
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
        
        self.save_btn = QPushButton('保存命例')
        self.save_btn.setStyleSheet(Stylesheets.BUTTON_SMALL)
        self.save_btn.setMinimumWidth(100)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
        
        return frame
    
    def _create_gender_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        label = QLabel('性别')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_MEDIUM};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY};
        """)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        
        self.male_btn = QPushButton('乾造（男）')
        self.male_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.male_btn.setCheckable(True)
        self.male_btn.setChecked(True)
        
        self.female_btn = QPushButton('坤造（女）')
        self.female_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.female_btn.setCheckable(True)
        
        button_layout.addWidget(self.male_btn)
        button_layout.addWidget(self.female_btn)
        button_layout.addStretch()
        
        layout.addWidget(label)
        layout.addLayout(button_layout)
        
        return layout
    
    def _create_calendar_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        label = QLabel('历法')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_MEDIUM};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY};
        """)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        
        self.solar_btn = QPushButton('公历')
        self.solar_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.solar_btn.setCheckable(True)
        self.solar_btn.setChecked(True)
        
        self.lunar_btn = QPushButton('农历')
        self.lunar_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.lunar_btn.setCheckable(True)
        
        button_layout.addWidget(self.solar_btn)
        button_layout.addWidget(self.lunar_btn)
        button_layout.addStretch()
        
        layout.addWidget(label)
        layout.addLayout(button_layout)
        
        return layout
    
    def _create_date_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        label = QLabel('出生日期')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_MEDIUM};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY};
        """)
        
        date_layout = QHBoxLayout()
        date_layout.setSpacing(12)
        
        self.year_combo = QComboBox()
        self.year_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.year_combo.setMinimumWidth(130)
        current_year = QDate.currentDate().year()
        for year in range(1900, 2024):
            self.year_combo.addItem(f'{year}年', year)
        self.year_combo.setCurrentIndex(self.year_combo.count() - 11)
        
        self.month_combo = QComboBox()
        self.month_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.month_combo.setMinimumWidth(90)
        for month in range(1, 13):
            self.month_combo.addItem(f'{month}月', month)
        self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)
        
        self.day_combo = QComboBox()
        self.day_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.day_combo.setMinimumWidth(90)
        self._update_day_combo()
        self.day_combo.setCurrentIndex(QDate.currentDate().day() - 1)
        
        date_layout.addWidget(self.year_combo)
        date_layout.addWidget(self.month_combo)
        date_layout.addWidget(self.day_combo)
        date_layout.addStretch()
        
        layout.addWidget(label)
        layout.addLayout(date_layout)
        
        return layout
    
    def _create_term_hint_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        label = QLabel('节气提示')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            font-weight: {Fonts.WEIGHT_MEDIUM};
            color: {Colors.ACCENT};
            font-family: {Fonts.FAMILY};
        """)
        
        self.term_hint = QLabel('')
        self.term_hint.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY};
            padding: 12px 14px;
            background-color: {Colors.BACKGROUND_SOFT};
            border-radius: 6px;
            border: 1px solid {Colors.BORDER};
        """)
        self.term_hint.setWordWrap(True)
        
        layout.addWidget(label)
        layout.addWidget(self.term_hint)
        
        return layout
    
    def _create_hour_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        label = QLabel('出生时辰')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_MEDIUM};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY};
        """)
        
        hour_layout = QHBoxLayout()
        hour_layout.setSpacing(12)
        
        self.hour_combo = QComboBox()
        self.hour_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.hour_combo.setMinimumWidth(180)
        for i, name in enumerate(HOUR_NAMES):
            start, end = HOUR_RANGES[i]
            if start == 23:
                time_range = "23:00-00:59"
            else:
                time_range = f"{start:02d}:00-{end:02d}:59"
            self.hour_combo.addItem(f"{name} ({time_range})", i)
        
        self.time_edit = QLineEdit()
        self.time_edit.setStyleSheet(Stylesheets.LINE_EDIT)
        self.time_edit.setPlaceholderText('时:分')
        self.time_edit.setMaximumWidth(100)
        self.time_edit.setText('12:00')
        
        hour_layout.addWidget(self.hour_combo)
        hour_layout.addWidget(self.time_edit)
        hour_layout.addStretch()
        
        zi_layout = QHBoxLayout()
        zi_layout.setSpacing(16)
        
        self.normal_zi_btn = QPushButton('标准时辰')
        self.normal_zi_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.normal_zi_btn.setCheckable(True)
        self.normal_zi_btn.setChecked(True)
        
        self.early_zi_btn = QPushButton('早晚子时')
        self.early_zi_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.early_zi_btn.setCheckable(True)
        
        zi_layout.addWidget(self.normal_zi_btn)
        zi_layout.addWidget(self.early_zi_btn)
        zi_layout.addStretch()
        
        layout.addWidget(label)
        layout.addLayout(hour_layout)
        layout.addLayout(zi_layout)
        
        return layout
    
    def _create_city_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        label = QLabel('出生地')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_MEDIUM};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY};
        """)
        
        city_layout = QHBoxLayout()
        city_layout.setSpacing(12)
        
        self.city_combo = QComboBox()
        self.city_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.city_combo.setMinimumWidth(200)
        for city in sorted(CITIES.keys()):
            self.city_combo.addItem(city)
        self.city_combo.setCurrentText('北京')
        
        self.correction_label = QLabel('真太阳时校正：±0分')
        self.correction_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.ACCENT};
            font-family: {Fonts.FAMILY};
            padding: 10px 14px;
            background-color: rgba(139, 125, 107, 0.1);
            border-radius: 6px;
        """)
        
        city_layout.addWidget(self.city_combo)
        city_layout.addWidget(self.correction_label)
        
        layout.addWidget(label)
        layout.addLayout(city_layout)
        
        return layout
    
    def _create_advanced_section(self):
        frame = QFrame()
        frame.setStyleSheet(Stylesheets.COLLAPSE_PANEL)
        
        self.advanced_expanded = False
        
        header_frame = QFrame()
        header_frame.setStyleSheet(Stylesheets.COLLAPSE_HEADER)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        self.advanced_toggle = QPushButton('▼ 高级设置')
        self.advanced_toggle.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: {Fonts.SIZE_BODY};
                font-weight: {Fonts.WEIGHT_MEDIUM};
                color: {Colors.TEXT_PRIMARY};
                font-family: {Fonts.FAMILY};
                text-align: left;
            }}
        """)
        
        header_layout.addWidget(self.advanced_toggle)
        
        self.advanced_content = QFrame()
        content_layout = QVBoxLayout(self.advanced_content)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(16)
        
        solar_time_layout = self._create_solar_time_setting()
        content_layout.addLayout(solar_time_layout)
        
        age_layout = self._create_age_setting()
        content_layout.addLayout(age_layout)
        
        leap_layout = self._create_leap_setting()
        content_layout.addLayout(leap_layout)
        
        renyuan_layout = self._create_renyuan_setting()
        content_layout.addLayout(renyuan_layout)
        
        self.advanced_content.setVisible(False)
        
        main_layout = QVBoxLayout(frame)
        main_layout.addWidget(header_frame)
        main_layout.addWidget(self.advanced_content)
        
        return frame
    
    def _create_solar_time_setting(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        label = QLabel('真太阳时')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            font-weight: {Fonts.WEIGHT_MEDIUM};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY};
        """)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.solar_auto_btn = QPushButton('自动校正')
        self.solar_auto_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.solar_auto_btn.setCheckable(True)
        self.solar_auto_btn.setChecked(True)
        
        self.solar_manual_btn = QPushButton('手动经度')
        self.solar_manual_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.solar_manual_btn.setCheckable(True)
        
        self.solar_off_btn = QPushButton('关闭')
        self.solar_off_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.solar_off_btn.setCheckable(True)
        
        button_layout.addWidget(self.solar_auto_btn)
        button_layout.addWidget(self.solar_manual_btn)
        button_layout.addWidget(self.solar_off_btn)
        button_layout.addStretch()
        
        layout.addWidget(label)
        layout.addLayout(button_layout)
        
        return layout
    
    def _create_age_setting(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        label = QLabel('起运岁数')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            font-weight: {Fonts.WEIGHT_MEDIUM};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY};
        """)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.age_real_btn = QPushButton('实岁')
        self.age_real_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.age_real_btn.setCheckable(True)
        self.age_real_btn.setChecked(True)
        
        self.age_virtual_btn = QPushButton('虚岁')
        self.age_virtual_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.age_virtual_btn.setCheckable(True)
        
        button_layout.addWidget(self.age_real_btn)
        button_layout.addWidget(self.age_virtual_btn)
        button_layout.addStretch()
        
        layout.addWidget(label)
        layout.addLayout(button_layout)
        
        return layout
    
    def _create_leap_setting(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        label = QLabel('闰月规则')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            font-weight: {Fonts.WEIGHT_MEDIUM};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY};
        """)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.leap_prev_btn = QPushButton('按上月')
        self.leap_prev_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.leap_prev_btn.setCheckable(True)
        self.leap_prev_btn.setChecked(True)
        
        self.leap_next_btn = QPushButton('按下月')
        self.leap_next_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.leap_next_btn.setCheckable(True)
        
        button_layout.addWidget(self.leap_prev_btn)
        button_layout.addWidget(self.leap_next_btn)
        button_layout.addStretch()
        
        layout.addWidget(label)
        layout.addLayout(button_layout)
        
        return layout
    
    def _create_renyuan_setting(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        label = QLabel('人元司令')
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            font-weight: {Fonts.WEIGHT_MEDIUM};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY};
        """)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.renyuan_std_btn = QPushButton('标准')
        self.renyuan_std_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.renyuan_std_btn.setCheckable(True)
        self.renyuan_std_btn.setChecked(True)
        
        self.renyuan_blind_btn = QPushButton('盲派')
        self.renyuan_blind_btn.setStyleSheet(Stylesheets.SWITCH_BUTTON)
        self.renyuan_blind_btn.setCheckable(True)
        
        button_layout.addWidget(self.renyuan_std_btn)
        button_layout.addWidget(self.renyuan_blind_btn)
        button_layout.addStretch()
        
        layout.addWidget(label)
        layout.addLayout(button_layout)
        
        return layout
    
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
    
    def _update_solar_term_info(self):
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        day = self.day_combo.currentData()
        
        term_info = get_solar_term_info(year, month, day)
        
        hour_text = self.time_edit.text()
        try:
            hh, mm = map(int, hour_text.split(':'))
            hours_after_term = ((day - 1) * 24 + hh + mm / 60) / 24
            hours_after_term = round(hours_after_term, 1)
        except:
            hours_after_term = 0
        
        hint_text = f"出生于{term_info['current_term']}后{hours_after_term}天，月令：{term_info['monthly_term']}月（节气为准）"
        self.term_hint.setText(hint_text)
    
    def _update_solar_time_correction(self):
        city_name = self.city_combo.currentText()
        city_data = get_city_data(city_name)
        
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        day = self.day_combo.currentData()
        
        try:
            hh, mm = map(int, self.time_edit.text().split(':'))
        except:
            hh, mm = 12, 0
        
        result = calculate_true_solar_time(year, month, day, hh, mm, 
                                          city_data['longitude'], 
                                          city_data['timezone'])
        
        correction = get_correction_display(result['correction'])
        self.correction_label.setText(f"真太阳时校正：{correction}")
    
    def _update_time_from_hour_combo(self):
        hour_index = self.hour_combo.currentData()
        start, end = HOUR_RANGES[hour_index]
        if start == 23:
            self.time_edit.setText('23:00')
        else:
            self.time_edit.setText(f"{start:02d}:00")
    
    def _update_hour_combo_from_time(self):
        try:
            hh, mm = map(int, self.time_edit.text().split(':'))
            adjusted_hh = hh if hh < 24 else 0
            
            for i, (start, end) in enumerate(HOUR_RANGES):
                if start == 23:
                    if adjusted_hh >= 23 or adjusted_hh < end:
                        self.hour_combo.setCurrentIndex(i)
                        break
                elif start <= adjusted_hh < end:
                    self.hour_combo.setCurrentIndex(i)
                    break
        except:
            pass
    
    def _convert_calendar(self, to_lunar):
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        day = self.day_combo.currentData()
        
        if to_lunar:
            lunar_data = solar_to_lunar(year, month, day)
            if lunar_data:
                self.year_combo.setCurrentIndex(lunar_data['year'] - 1900)
                self.month_combo.setCurrentIndex(lunar_data['month'] - 1)
                self.day_combo.setCurrentIndex(lunar_data['day'] - 1)
        else:
            solar_data = lunar_to_solar(year, month, day)
            if solar_data:
                self.year_combo.setCurrentIndex(solar_data['year'] - 1900)
                self.month_combo.setCurrentIndex(solar_data['month'] - 1)
                self.day_combo.setCurrentIndex(solar_data['day'] - 1)
    
    def connect_signals(self):
        self.male_btn.clicked.connect(lambda: self._on_gender_toggle(True))
        self.female_btn.clicked.connect(lambda: self._on_gender_toggle(False))
        
        self.solar_btn.clicked.connect(lambda: self._on_calendar_toggle(True))
        self.lunar_btn.clicked.connect(lambda: self._on_calendar_toggle(False))
        
        self.year_combo.currentIndexChanged.connect(self._on_date_changed)
        self.month_combo.currentIndexChanged.connect(self._on_date_changed)
        self.day_combo.currentIndexChanged.connect(self._on_date_changed)
        
        self.hour_combo.currentIndexChanged.connect(self._update_time_from_hour_combo)
        self.time_edit.textChanged.connect(self._update_hour_combo_from_time)
        
        self.normal_zi_btn.clicked.connect(lambda: self._on_zi_toggle(False))
        self.early_zi_btn.clicked.connect(lambda: self._on_zi_toggle(True))
        
        self.city_combo.currentTextChanged.connect(self._on_city_changed)
        
        self.advanced_toggle.clicked.connect(self._toggle_advanced)
        
        self.solar_auto_btn.clicked.connect(lambda: self._on_solar_time_mode('auto'))
        self.solar_manual_btn.clicked.connect(lambda: self._on_solar_time_mode('manual'))
        self.solar_off_btn.clicked.connect(lambda: self._on_solar_time_mode('off'))
        
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        self.save_btn.clicked.connect(self._on_save_clicked)
    
    def _on_gender_toggle(self, is_male):
        self.male_btn.setChecked(is_male)
        self.female_btn.setChecked(not is_male)
    
    def _on_calendar_toggle(self, is_solar):
        self.solar_btn.setChecked(is_solar)
        self.lunar_btn.setChecked(not is_solar)
        
        if is_solar != self.is_lunar:
            self._convert_calendar(not is_solar)
            self.is_lunar = not is_solar
    
    def _on_date_changed(self):
        self._update_day_combo()
        self._update_solar_term_info()
        self._update_solar_time_correction()
    
    def _on_zi_toggle(self, is_early):
        self.normal_zi_btn.setChecked(not is_early)
        self.early_zi_btn.setChecked(is_early)
        self.is_early_zi = is_early
    
    def _on_city_changed(self, city_name):
        self.current_city = city_name
        self._update_solar_time_correction()
    
    def _toggle_advanced(self):
        self.advanced_expanded = not self.advanced_expanded
        if self.advanced_expanded:
            self.advanced_toggle.setText('▲ 高级设置')
            self.advanced_content.setVisible(True)
        else:
            self.advanced_toggle.setText('▼ 高级设置')
            self.advanced_content.setVisible(False)
    
    def _on_solar_time_mode(self, mode):
        self.solar_time_mode = mode
        self.solar_auto_btn.setChecked(mode == 'auto')
        self.solar_manual_btn.setChecked(mode == 'manual')
        self.solar_off_btn.setChecked(mode == 'off')
        
        if mode == 'off':
            self.correction_label.setText('真太阳时校正：已关闭')
        else:
            self._update_solar_time_correction()
    
    def _on_start_clicked(self):
        if self.validate_input():
            data = self.get_data()
            self.start_panpan.emit(data)
    
    def _on_reset_clicked(self):
        self.reset()
    
    def _on_save_clicked(self):
        pass
    
    def validate_input(self):
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        day = self.day_combo.currentData()
        
        if year < 1900 or year > 2023:
            return False
        
        if month < 1 or month > 12:
            return False
        
        days_in_month = self._get_days_in_month(year, month)
        if day < 1 or day > days_in_month:
            return False
        
        time_text = self.time_edit.text()
        try:
            hh, mm = map(int, time_text.split(':'))
            if hh < 0 or hh > 24 or mm < 0 or mm > 59:
                return False
        except:
            return False
        
        return True
    
    def get_data(self):
        hour_index = self.hour_combo.currentData()
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        day = self.day_combo.currentData()
        
        try:
            hh, mm = map(int, self.time_edit.text().split(':'))
        except:
            hh, mm = 12, 0
        
        city_data = get_city_data(self.current_city)
        solar_time_result = calculate_true_solar_time(year, month, day, hh, mm,
                                                     city_data['longitude'],
                                                     city_data['timezone'])
        
        return {
            'name': '',
            'year': year,
            'month': month,
            'day': day,
            'hour': hh,
            'minute': mm,
            'hour_index': hour_index,
            'gender': '男' if self.male_btn.isChecked() else '女',
            'is_lunar': self.is_lunar,
            'city': self.current_city,
            'longitude': city_data['longitude'],
            'latitude': city_data['latitude'],
            'solar_time_correction': solar_time_result['correction'],
            'is_early_zi': self.is_early_zi,
            'solar_time_mode': self.solar_time_mode,
            'age_type': 'real' if self.age_real_btn.isChecked() else 'virtual',
            'leap_rule': 'prev' if self.leap_prev_btn.isChecked() else 'next',
            'renyuan_rule': 'std' if self.renyuan_std_btn.isChecked() else 'blind'
        }
    
    def reset(self):
        current_year = QDate.currentDate().year()
        current_month = QDate.currentDate().month()
        current_day = QDate.currentDate().day()
        
        self.male_btn.setChecked(True)
        self.female_btn.setChecked(False)
        
        self.solar_btn.setChecked(True)
        self.lunar_btn.setChecked(False)
        self.is_lunar = False
        
        self.year_combo.setCurrentIndex(current_year - 1900)
        self.month_combo.setCurrentIndex(current_month - 1)
        self._update_day_combo()
        self.day_combo.setCurrentIndex(current_day - 1)
        
        self.time_edit.setText('12:00')
        self.hour_combo.setCurrentIndex(5)
        
        self.normal_zi_btn.setChecked(True)
        self.early_zi_btn.setChecked(False)
        self.is_early_zi = False
        
        self.city_combo.setCurrentText('北京')
        self.current_city = '北京'
        
        self.solar_auto_btn.setChecked(True)
        self.solar_manual_btn.setChecked(False)
        self.solar_off_btn.setChecked(False)
        self.solar_time_mode = 'auto'
        
        self.age_real_btn.setChecked(True)
        self.age_virtual_btn.setChecked(False)
        
        self.leap_prev_btn.setChecked(True)
        self.leap_next_btn.setChecked(False)
        
        self.renyuan_std_btn.setChecked(True)
        self.renyuan_blind_btn.setChecked(False)
        
        self.advanced_expanded = False
        self.advanced_toggle.setText('▼ 高级设置')
        self.advanced_content.setVisible(False)
        
        self._update_solar_term_info()
        self._update_solar_time_correction()
