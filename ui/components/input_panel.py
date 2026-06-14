from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QComboBox, QPushButton, QFrame, QCheckBox, QSizePolicy)
from PyQt5.QtCore import QDate, QTime, Qt, QEvent
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
        self.setStyleSheet(Stylesheets.CARD)

        main_layout = QVBoxLayout()
        card_padding = int(Spacing.CARD_PADDING.replace('px', ''))
        module_gap = int(Spacing.MODULE_GAP.replace('px', ''))
        main_layout.setContentsMargins(card_padding, card_padding, card_padding, card_padding)
        main_layout.setSpacing(module_gap)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(6)

        title_label = QLabel('八字排盘 · 专业精准排盘')
        title_label.setStyleSheet(Stylesheets.CARD_TITLE)
        title_label.setAlignment(Qt.AlignCenter)

        title_layout.addWidget(title_label)
        main_layout.addLayout(title_layout)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(module_gap)

        gender_section = self._create_gender_section()
        form_layout.addLayout(gender_section)

        name_section = self._create_name_section()
        form_layout.addLayout(name_section)

        calendar_section = self._create_calendar_section()
        form_layout.addLayout(calendar_section)

        date_section = self._create_date_section()
        form_layout.addLayout(date_section)

        hour_section = self._create_hour_section()
        form_layout.addLayout(hour_section)

        location_section = self._create_location_section()
        form_layout.addLayout(location_section)

        advanced_section = self._create_advanced_section()
        form_layout.addLayout(advanced_section)

        main_layout.addLayout(form_layout)

        self.validation_hint = QLabel('')
        self.validation_hint.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.WARNING};
            font-family: {Fonts.FAMILY_CN};
            padding: 8px 12px;
            background-color: rgba(156, 68, 68, 0.06);
            border-radius: {Spacing.CONTROL_RADIUS};
        """)
        self.validation_hint.setVisible(False)
        self.validation_hint.setWordWrap(True)
        main_layout.addWidget(self.validation_hint)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(14)
        button_layout.setAlignment(Qt.AlignCenter)

        self.reset_btn = QPushButton('重置清空')
        self.reset_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)
        self.reset_btn.setMinimumWidth(100)

        self.submit_btn = QPushButton('精准排盘')
        self.submit_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        self.submit_btn.setMinimumWidth(120)
        self.submit_btn.setEnabled(False)

        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.submit_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _create_gender_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(int(Spacing.CONTROL_VERTICAL_GAP.replace('px', '')))

        label = QLabel('性别')
        label.setStyleSheet(Stylesheets.LABEL_BODY)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.male_btn = QPushButton('乾造（男）')
        self.male_btn.setStyleSheet(Stylesheets.BUTTON_TOGGLE)
        self.male_btn.setCheckable(True)
        self.male_btn.setChecked(True)

        self.female_btn = QPushButton('坤造（女）')
        self.female_btn.setStyleSheet(Stylesheets.BUTTON_TOGGLE)
        self.female_btn.setCheckable(True)

        button_layout.addWidget(self.male_btn)
        button_layout.addWidget(self.female_btn)
        button_layout.addStretch()

        layout.addWidget(label)
        layout.addLayout(button_layout)

        return layout

    def _create_name_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(int(Spacing.CONTROL_VERTICAL_GAP.replace('px', '')))

        label = QLabel('姓名')
        label.setStyleSheet(Stylesheets.LABEL_BODY)

        self.name_lineedit = QLineEdit()
        self.name_lineedit.setStyleSheet(Stylesheets.LINE_EDIT)
        self.name_lineedit.setPlaceholderText('请输入姓名')
        self.name_lineedit.setMinimumHeight(32)
        self.name_lineedit.textChanged.connect(self._on_name_changed)

        layout.addWidget(label)
        layout.addWidget(self.name_lineedit)

        return layout

    def _create_calendar_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(int(Spacing.CONTROL_VERTICAL_GAP.replace('px', '')))

        label = QLabel('历法')
        label.setStyleSheet(Stylesheets.LABEL_BODY)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.solar_btn = QPushButton('公历')
        self.solar_btn.setStyleSheet(Stylesheets.BUTTON_TOGGLE)
        self.solar_btn.setCheckable(True)
        self.solar_btn.setChecked(True)

        self.lunar_btn = QPushButton('农历')
        self.lunar_btn.setStyleSheet(Stylesheets.BUTTON_TOGGLE)
        self.lunar_btn.setCheckable(True)

        button_layout.addWidget(self.solar_btn)
        button_layout.addWidget(self.lunar_btn)
        button_layout.addStretch()

        layout.addWidget(label)
        layout.addLayout(button_layout)

        return layout

    def _create_date_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(int(Spacing.CONTROL_VERTICAL_GAP.replace('px', '')))

        label = QLabel('出生日期')
        label.setStyleSheet(Stylesheets.LABEL_BODY)

        date_layout = QHBoxLayout()
        date_layout.setSpacing(8)

        self.year_combo = QComboBox()
        self.year_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.year_combo.setMinimumWidth(110)
        current_year = QDate.currentDate().year()
        for year in range(1900, current_year + 1):
            self.year_combo.addItem(f'{year}年', year)
        self.year_combo.setCurrentIndex(self.year_combo.count() - 1)

        self.month_combo = QComboBox()
        self.month_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.month_combo.setMinimumWidth(75)
        for month in range(1, 13):
            self.month_combo.addItem(f'{month}月', month)
        self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)

        self.day_combo = QComboBox()
        self.day_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.day_combo.setMinimumWidth(75)
        self._update_day_combo()
        self.day_combo.setCurrentIndex(QDate.currentDate().day() - 1)

        date_layout.addWidget(self.year_combo)
        date_layout.addWidget(self.month_combo)
        date_layout.addWidget(self.day_combo)
        date_layout.addStretch()

        hint_label = QLabel('提示：选择日期后将自动匹配节气')
        hint_label.setStyleSheet(Stylesheets.LABEL_SMALL)

        layout.addWidget(label)
        layout.addLayout(date_layout)
        layout.addWidget(hint_label)

        return layout

    def _create_hour_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(int(Spacing.CONTROL_VERTICAL_GAP.replace('px', '')))

        label = QLabel('出生时辰')
        label.setStyleSheet(Stylesheets.LABEL_BODY)

        hour_layout = QHBoxLayout()
        hour_layout.setSpacing(8)

        self.hour_combo = QComboBox()
        self.hour_combo.setStyleSheet(Stylesheets.COMBO_BOX)
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
        self.time_edit.setStyleSheet(Stylesheets.LINE_EDIT)
        self.time_edit.setPlaceholderText('时:分')
        self.time_edit.setMaximumWidth(85)
        self.time_edit.setText('12:00')
        self.time_edit.textChanged.connect(self._on_time_changed)

        hour_layout.addWidget(self.hour_combo)
        hour_layout.addWidget(self.time_edit)
        hour_layout.addStretch()

        zi_switch_layout = QHBoxLayout()
        zi_switch_layout.setSpacing(8)

        zi_label = QLabel('早晚子时')
        zi_label.setStyleSheet(Stylesheets.LABEL_SMALL)

        self.early_zi_switch = QCheckBox()
        self.early_zi_switch.setStyleSheet(Stylesheets.TOGGLE_SWITCH)
        self.early_zi_switch.setChecked(False)

        zi_desc = QLabel('启用早子时')
        zi_desc.setStyleSheet(Stylesheets.LABEL_SMALL)

        zi_switch_layout.addWidget(zi_label)
        zi_switch_layout.addWidget(self.early_zi_switch)
        zi_switch_layout.addWidget(zi_desc)
        zi_switch_layout.addStretch()

        layout.addWidget(label)
        layout.addLayout(hour_layout)
        layout.addLayout(zi_switch_layout)

        return layout

    def _create_location_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(int(Spacing.CONTROL_VERTICAL_GAP.replace('px', '')))

        label = QLabel('出生地点')
        label.setStyleSheet(Stylesheets.LABEL_BODY)

        location_layout = QHBoxLayout()
        location_layout.setSpacing(8)

        self.city_combo = QComboBox()
        self.city_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.city_combo.setMinimumWidth(160)
        for city, coords in CITIES:
            self.city_combo.addItem(city, coords)

        self.lat_label = QLabel('')
        self.lat_label.setStyleSheet(Stylesheets.LABEL_SMALL)
        self.lat_label.setMaximumWidth(150)

        location_layout.addWidget(self.city_combo)
        location_layout.addWidget(self.lat_label)
        location_layout.addStretch()

        self._update_coords_label()

        layout.addWidget(label)
        layout.addLayout(location_layout)

        return layout

    def _create_advanced_section(self):
        layout = QVBoxLayout()
        layout.setSpacing(0)

        self.advanced_frame = QFrame()
        self.advanced_frame.setStyleSheet(Stylesheets.CARD_NO_SHADOW)

        advanced_header = QFrame()
        advanced_header.setStyleSheet(Stylesheets.COLLAPSE_HEADER)
        header_layout = QHBoxLayout(advanced_header)
        header_layout.setContentsMargins(14, 10, 14, 10)

        self.advanced_toggle = QPushButton('▼ 高级设置')
        self.advanced_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: none;
                font-size: {Fonts.SIZE_BODY};
                font-family: {Fonts.FAMILY_CN};
                padding: 0;
                text-align: left;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT};
            }}
        """)
        self.advanced_toggle.setCursor(Qt.PointingHandCursor)

        header_layout.addWidget(self.advanced_toggle)
        header_layout.addStretch()

        self.advanced_content = QWidget()
        self.advanced_content.setVisible(False)
        advanced_content_layout = QVBoxLayout(self.advanced_content)
        advanced_content_layout.setContentsMargins(14, 12, 14, 12)
        advanced_content_layout.setSpacing(int(Spacing.MODULE_GAP.replace('px', '')))

        solar_time_layout = QHBoxLayout()
        solar_time_layout.setSpacing(8)

        solar_time_label = QLabel('真太阳时校正')
        solar_time_label.setStyleSheet(Stylesheets.LABEL_BODY)
        solar_time_label.setMinimumWidth(90)

        self.solar_time_combo = QComboBox()
        self.solar_time_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.solar_time_combo.setMinimumWidth(130)
        self.solar_time_combo.addItems(['自动', '启用', '禁用'])

        solar_time_layout.addWidget(solar_time_label)
        solar_time_layout.addWidget(self.solar_time_combo)
        solar_time_layout.addStretch()

        age_rule_layout = QHBoxLayout()
        age_rule_layout.setSpacing(8)

        age_rule_label = QLabel('起运计算规则')
        age_rule_label.setStyleSheet(Stylesheets.LABEL_BODY)
        age_rule_label.setMinimumWidth(90)

        self.age_rule_combo = QComboBox()
        self.age_rule_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.age_rule_combo.setMinimumWidth(130)
        self.age_rule_combo.addItems(['虚岁', '周岁'])

        age_rule_layout.addWidget(age_rule_label)
        age_rule_layout.addWidget(self.age_rule_combo)
        age_rule_layout.addStretch()

        leap_rule_layout = QHBoxLayout()
        leap_rule_layout.setSpacing(8)

        leap_rule_label = QLabel('闰月处理方式')
        leap_rule_label.setStyleSheet(Stylesheets.LABEL_BODY)
        leap_rule_label.setMinimumWidth(90)

        self.leap_rule_combo = QComboBox()
        self.leap_rule_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.leap_rule_combo.setMinimumWidth(130)
        self.leap_rule_combo.addItems(['归前', '归后', '独立'])

        leap_rule_layout.addWidget(leap_rule_label)
        leap_rule_layout.addWidget(self.leap_rule_combo)
        leap_rule_layout.addStretch()

        advanced_content_layout.addLayout(solar_time_layout)
        advanced_content_layout.addLayout(age_rule_layout)
        advanced_content_layout.addLayout(leap_rule_layout)

        advanced_main_layout = QVBoxLayout(self.advanced_frame)
        advanced_main_layout.setContentsMargins(0, 0, 0, 0)
        advanced_main_layout.addWidget(advanced_header)
        advanced_main_layout.addWidget(self.advanced_content)

        layout.addWidget(self.advanced_frame)

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

    def setup_validation(self):
        self.city_combo.currentIndexChanged.connect(self._update_coords_label)
        self.advanced_toggle.clicked.connect(self._toggle_advanced)
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
        self.advanced_toggle.setText('▲ 高级设置' if is_visible else '▼ 高级设置')

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

    def _update_hour_from_time(self):
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

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusOut:
            if obj == self.name_lineedit:
                self.validate_input()
        return super().eventFilter(obj, event)

    def validate_input(self):
        name = self.name_lineedit.text().strip()
        time_text = self.time_edit.text().strip()

        if not name:
            self.validation_hint.setText('✘ 请输入姓名')
            self.validation_hint.setVisible(True)
            self.submit_btn.setEnabled(False)
            return False

        if len(name) > 20:
            self.validation_hint.setText('✘ 姓名不能超过20个字符')
            self.validation_hint.setVisible(True)
            self.submit_btn.setEnabled(False)
            return False

        if not time_text:
            self.validation_hint.setText('✘ 请输入出生时间')
            self.validation_hint.setVisible(True)
            self.submit_btn.setEnabled(False)
            return False

        try:
            hh, mm = map(int, time_text.split(':'))
            if hh < 0 or hh > 23 or mm < 0 or mm > 59:
                self.validation_hint.setText('✘ 时间格式错误，请输入有效的时分（00:00-23:59）')
                self.validation_hint.setVisible(True)
                self.submit_btn.setEnabled(False)
                return False
        except:
            self.validation_hint.setText('✘ 时间格式错误，请使用 时:分 格式')
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
        self.advanced_toggle.setText('▼ 高级设置')
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
