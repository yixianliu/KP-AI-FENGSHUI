from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QRadioButton,
                             QDateEdit, QComboBox, QPushButton,
                             QButtonGroup, QFrame, QGridLayout, QSpacerItem)
from PyQt5.QtCore import QDate, QTime, Qt, QSize

HOUR_NAMES = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时',
              '午时', '未时', '申时', '酉时', '戌时', '亥时']

HOUR_RANGES = [(23, 1), (1, 3), (3, 5), (5, 7), (7, 9), (9, 11),
               (11, 13), (13, 15), (15, 17), (17, 19), (19, 21), (21, 23)]

class InputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #E8D5B5;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(12)

        title_layout = QHBoxLayout()
        title_icon = QLabel('📋')
        title_icon.setStyleSheet("font-size: 18px;")
        title_label = QLabel('基本信息')
        title_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            color: #5D4037;
        """)
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)

        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        form_layout.setVerticalSpacing(12)

        row = 0

        name_label = QLabel('姓名:')
        name_label.setStyleSheet("color: #5D4037; font-weight: bold;")
        self.name_lineedit = QLineEdit()
        self.name_lineedit.setPlaceholderText('请输入您的姓名')
        self.name_lineedit.setFixedHeight(38)
        self.name_lineedit.setMinimumWidth(150)
        form_layout.addWidget(name_label, row, 0)
        form_layout.addWidget(self.name_lineedit, row, 1, 1, 2)

        row += 1
        gender_label = QLabel('性别:')
        gender_label.setStyleSheet("color: #5D4037; font-weight: bold;")

        self.gender_group = QButtonGroup()
        self.male_radio = QRadioButton('男')
        self.female_radio = QRadioButton('女')
        self.male_radio.setChecked(True)
        self.male_radio.setStyleSheet("""
            QRadioButton {
                color: #333333;
                font-size: 13px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #D4AF37;
                border-radius: 8px;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                background-color: #D4AF37;
            }
        """)
        self.female_radio.setStyleSheet(self.male_radio.styleSheet())

        self.gender_group.addButton(self.male_radio)
        self.gender_group.addButton(self.female_radio)

        gender_layout = QHBoxLayout()
        gender_layout.setSpacing(20)
        gender_layout.addWidget(self.male_radio)
        gender_layout.addWidget(self.female_radio)

        calendar_label = QLabel('历法:')
        calendar_label.setStyleSheet("color: #5D4037; font-weight: bold;")

        self.calendar_group = QButtonGroup()
        self.solar_radio = QRadioButton('公历')
        self.lunar_radio = QRadioButton('农历')
        self.solar_radio.setChecked(True)
        self.solar_radio.setStyleSheet(self.male_radio.styleSheet())
        self.lunar_radio.setStyleSheet(self.male_radio.styleSheet())

        self.calendar_group.addButton(self.solar_radio)
        self.calendar_group.addButton(self.lunar_radio)

        calendar_layout = QHBoxLayout()
        calendar_layout.setSpacing(20)
        calendar_layout.addWidget(self.solar_radio)
        calendar_layout.addWidget(self.lunar_radio)

        form_layout.addWidget(gender_label, row, 0)
        form_layout.addLayout(gender_layout, row, 1)
        form_layout.addWidget(calendar_label, row, 2)
        form_layout.addLayout(calendar_layout, row, 3)

        row += 1
        date_label = QLabel('日期:')
        date_label.setStyleSheet("color: #5D4037; font-weight: bold;")

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedHeight(38)
        self.date_edit.setMinimumWidth(130)
        self.date_edit.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 2px solid #D4AF37;
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
            }
            QDateEdit:focus {
                border-color: #5D4037;
            }
        """)

        hour_label = QLabel('时辰:')
        hour_label.setStyleSheet("color: #5D4037; font-weight: bold;")

        self.hour_combo = QComboBox()
        self.hour_combo.setFixedHeight(38)
        self.hour_combo.setMinimumWidth(180)
        for i, name in enumerate(HOUR_NAMES):
            start, end = HOUR_RANGES[i]
            if start == 23:
                time_range = "23:00-00:59"
            else:
                time_range = f"{start:02d}:00-{end:02d}:59"
            self.hour_combo.addItem(f"{name} ({time_range})", i)

        today_hour = QTime.currentTime().hour()
        default_idx = self.get_hour_index(today_hour)
        self.hour_combo.setCurrentIndex(default_idx)

        self.hour_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 2px solid #D4AF37;
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #5D4037;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #D4AF37;
                margin-right: 5px;
            }
        """)

        form_layout.addWidget(date_label, row, 0)
        form_layout.addWidget(self.date_edit, row, 1)
        form_layout.addWidget(hour_label, row, 2)
        form_layout.addWidget(self.hour_combo, row, 3)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.quick_btn = QPushButton('⚡ 快速排盘')
        self.quick_btn.setFixedHeight(40)
        self.quick_btn.setMinimumWidth(130)
        self.quick_btn.clicked.connect(self.on_quick_input)
        self.quick_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5E6D3;
                color: #5D4037;
                border: 2px solid #D4AF37;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #EBD9C4;
            }
            QPushButton:pressed {
                background-color: #D4AF37;
                color: white;
            }
        """)

        self.submit_btn = QPushButton('✨ 开始排盘')
        self.submit_btn.setFixedHeight(40)
        self.submit_btn.setMinimumWidth(130)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5D4037, stop:1 #3D2A20);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6B4423, stop:1 #4A3428);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3D2A20, stop:1 #2D1F18);
            }
        """)

        button_layout.addWidget(self.quick_btn)
        button_layout.addWidget(self.submit_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def on_quick_input(self):
        from PyQt5.QtCore import QDate, QTime
        current_date = QDate.currentDate()
        self.date_edit.setDate(current_date)
        current_hour = QTime.currentTime().hour()
        self.hour_combo.setCurrentIndex(self.get_hour_index(current_hour))

    def get_hour_index(self, hour):
        for i, (start, end) in enumerate(HOUR_RANGES):
            if start == 23:
                if hour >= 23 or hour < end:
                    return i
            elif start <= hour < end:
                return i
        return 0

    def get_data(self):
        hour_index = self.hour_combo.currentData()
        hour = HOUR_RANGES[hour_index][0]
        if hour == 23:
            hour = 0

        return {
            'name': self.name_lineedit.text().strip(),
            'gender': '男' if self.male_radio.isChecked() else '女',
            'is_lunar': self.lunar_radio.isChecked(),
            'year': self.date_edit.date().year(),
            'month': self.date_edit.date().month(),
            'day': self.date_edit.date().day(),
            'hour': hour
        }

    def clear(self):
        self.name_lineedit.clear()
        self.male_radio.setChecked(True)
        self.solar_radio.setChecked(True)
        self.date_edit.setDate(QDate.currentDate())
        self.hour_combo.setCurrentIndex(self.get_hour_index(QTime.currentTime().hour()))
