from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QRadioButton,
                             QDateEdit, QComboBox, QPushButton,
                             QButtonGroup, QFrame, QGridLayout)
from PyQt5.QtCore import QDate, QTime, Qt

HOUR_NAMES = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时',
              '午时', '未时', '申时', '酉时', '戌时', '亥时']

HOUR_RANGES = [(23, 1), (1, 3), (3, 5), (5, 7), (7, 9), (9, 11),
               (11, 13), (13, 15), (15, 17), (17, 19), (19, 21), (21, 23)]

class InputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_frame = self.create_section_title('基本信息', '📋')
        layout.addWidget(title_frame)

        basic_card = self.create_basic_card()
        layout.addWidget(basic_card)

        title_frame2 = self.create_section_title('出生日期', '📅')
        layout.addWidget(title_frame2)

        date_card = self.create_date_card()
        layout.addWidget(date_card)

        title_frame3 = self.create_section_title('出生时辰', '⏰')
        layout.addWidget(title_frame3)

        hour_card = self.create_hour_card()
        layout.addWidget(hour_card)

        layout.addStretch()

        self.submit_btn = QPushButton('开始排盘')
        self.submit_btn.setFixedHeight(45)
        layout.addWidget(self.submit_btn)

        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #FFF8E7;
            }
            QLabel {
                color: #333333;
                font-size: 13px;
            }
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #D4AF37;
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
                font-family: 'Microsoft YaHei';
            }
            QLineEdit:focus {
                border-color: #5D4037;
                background-color: #FFFEF5;
            }
            QLineEdit::placeholder {
                color: #999999;
            }
            QDateEdit {
                padding: 8px 12px;
                border: 2px solid #D4AF37;
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
                font-family: 'Microsoft YaHei';
            }
            QDateEdit:focus {
                border-color: #5D4037;
                background-color: #FFFEF5;
            }
            QComboBox {
                padding: 8px 12px;
                border: 2px solid #D4AF37;
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
                font-family: 'Microsoft YaHei';
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
            QRadioButton {
                color: #333333;
                font-size: 13px;
                padding: 5px;
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
                border-color: #D4AF37;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5D4037, stop:1 #3D2A20);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
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

    def create_section_title(self, title, icon):
        frame = QWidget()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 5, 0, 5)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #5D4037;
        """)
        layout.addWidget(title_label)

        layout.addStretch()
        return frame

    def create_basic_card(self):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E8D5B5;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        layout = QGridLayout()
        layout.setSpacing(10)

        name_label = QLabel('姓名:')
        name_label.setFixedWidth(45)
        self.name_lineedit = QLineEdit()
        self.name_lineedit.setPlaceholderText('请输入您的姓名')
        self.name_lineedit.setFixedHeight(36)
        self.name_lineedit.textChanged.connect(self.on_name_changed)
        layout.addWidget(name_label, 0, 0)
        layout.addWidget(self.name_lineedit, 0, 1)

        gender_label = QLabel('性别:')
        gender_label.setFixedWidth(45)

        self.gender_group = QButtonGroup()
        self.male_radio = QRadioButton('男')
        self.female_radio = QRadioButton('女')
        self.male_radio.setChecked(True)

        self.gender_group.addButton(self.male_radio)
        self.gender_group.addButton(self.female_radio)

        gender_layout = QHBoxLayout()
        gender_layout.setSpacing(15)
        gender_layout.addWidget(self.male_radio)
        gender_layout.addWidget(self.female_radio)
        gender_layout.addStretch()

        layout.addWidget(gender_label, 1, 0)
        layout.addLayout(gender_layout, 1, 1)

        card.setLayout(layout)
        return card

    def create_date_card(self):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E8D5B5;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        layout = QGridLayout()
        layout.setSpacing(10)

        calendar_label = QLabel('历法:')
        calendar_label.setFixedWidth(45)

        self.calendar_group = QButtonGroup()
        self.solar_radio = QRadioButton('公历')
        self.lunar_radio = QRadioButton('农历')
        self.solar_radio.setChecked(True)

        self.calendar_group.addButton(self.solar_radio)
        self.calendar_group.addButton(self.lunar_radio)

        calendar_layout = QHBoxLayout()
        calendar_layout.setSpacing(15)
        calendar_layout.addWidget(self.solar_radio)
        calendar_layout.addWidget(self.lunar_radio)
        calendar_layout.addStretch()

        layout.addWidget(calendar_label, 0, 0)
        layout.addLayout(calendar_layout, 0, 1)

        date_label = QLabel('日期:')
        date_label.setFixedWidth(45)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedHeight(36)

        layout.addWidget(date_label, 1, 0)
        layout.addWidget(self.date_edit, 1, 1)

        card.setLayout(layout)
        return card

    def create_hour_card(self):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E8D5B5;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        layout = QHBoxLayout()
        layout.setSpacing(10)

        hour_label = QLabel('时辰:')
        hour_label.setFixedWidth(45)

        self.hour_combo = QComboBox()
        self.hour_combo.setFixedHeight(36)
        for i, name in enumerate(HOUR_NAMES):
            start, end = HOUR_RANGES[i]
            if start == 23:
                time_range = f"23:00-00:59"
            else:
                time_range = f"{start:02d}:00-{end:02d}:59"
            self.hour_combo.addItem(f"{name} ({time_range})", i)

        today_hour = QTime.currentTime().hour()
        default_idx = self.get_hour_index(today_hour)
        self.hour_combo.setCurrentIndex(default_idx)

        layout.addWidget(hour_label)
        layout.addWidget(self.hour_combo)
        layout.addStretch()

        card.setLayout(layout)
        return card

    def get_hour_index(self, hour):
        for i, (start, end) in enumerate(HOUR_RANGES):
            if start == 23:
                if hour >= 23 or hour < end:
                    return i
            elif start <= hour < end:
                return i
        return 0

    def on_name_changed(self, text):
        pass

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
