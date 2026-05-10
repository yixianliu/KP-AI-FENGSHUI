from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QRadioButton,
                             QDateEdit, QComboBox, QPushButton,
                             QButtonGroup, QFrame, QGridLayout,
                             QToolTip, QMessageBox)
from PyQt5.QtCore import QDate, QTime, Qt, QEvent
from ui.styles import Stylesheets, Colors, Fonts

HOUR_NAMES = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时',
              '午时', '未时', '申时', '酉时', '戌时', '亥时']

HOUR_RANGES = [(23, 1), (1, 3), (3, 5), (5, 7), (7, 9), (9, 11),
               (11, 13), (13, 15), (15, 17), (17, 19), (19, 21), (21, 23)]

class InputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_validation()

    def init_ui(self):
        self.setStyleSheet(Stylesheets.CARD)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        title_label = QLabel('八字排盘')
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_TITLE};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_BOLD};
            margin-bottom: 10px;
        """)
        main_layout.addWidget(title_label)

        form_layout = QGridLayout()
        form_layout.setSpacing(10)
        form_layout.setVerticalSpacing(12)

        row = 0

        name_label = QLabel('姓名:')
        name_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_BOLD};
        """)
        self.name_lineedit = QLineEdit()
        self.name_lineedit.setPlaceholderText('请输入姓名')
        self.name_lineedit.setStyleSheet(Stylesheets.LINE_EDIT)
        self.name_lineedit.textChanged.connect(self.on_input_changed)

        form_layout.addWidget(name_label, row, 0)
        form_layout.addWidget(self.name_lineedit, row, 1, 1, 3)

        row += 1

        gender_label = QLabel('性别:')
        gender_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_BOLD};
        """)

        self.gender_group = QButtonGroup()
        self.male_radio = QRadioButton('男')
        self.female_radio = QRadioButton('女')
        self.male_radio.setChecked(True)
        self.male_radio.setStyleSheet(Stylesheets.RADIO_BUTTON)
        self.female_radio.setStyleSheet(Stylesheets.RADIO_BUTTON)

        gender_layout = QHBoxLayout()
        gender_layout.setSpacing(20)
        gender_layout.addWidget(self.male_radio)
        gender_layout.addWidget(self.female_radio)

        calendar_label = QLabel('历法:')
        calendar_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_BOLD};
        """)

        self.calendar_group = QButtonGroup()
        self.solar_radio = QRadioButton('公历')
        self.lunar_radio = QRadioButton('农历')
        self.solar_radio.setChecked(True)
        self.solar_radio.setStyleSheet(Stylesheets.RADIO_BUTTON)
        self.lunar_radio.setStyleSheet(Stylesheets.RADIO_BUTTON)

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
        date_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_BOLD};
        """)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet(Stylesheets.DATE_EDIT)

        hour_label = QLabel('时辰:')
        hour_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_BOLD};
        """)

        self.hour_combo = QComboBox()
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

        self.hour_combo.setStyleSheet(Stylesheets.COMBO_BOX)

        form_layout.addWidget(date_label, row, 0)
        form_layout.addWidget(self.date_edit, row, 1)
        form_layout.addWidget(hour_label, row, 2)
        form_layout.addWidget(self.hour_combo, row, 3)

        main_layout.addLayout(form_layout)

        self.validation_hint = QLabel('')
        self.validation_hint.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.ERROR};
            font-family: {Fonts.FAMILY};
            padding: 8px;
            background-color: rgba(220, 20, 60, 0.05);
            border-radius: 4px;
            margin-top: 5px;
        """)
        self.validation_hint.setVisible(False)
        main_layout.addWidget(self.validation_hint)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.submit_btn = QPushButton('开始排盘')
        self.submit_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        self.submit_btn.setEnabled(False)

        button_layout.addWidget(self.submit_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def setup_validation(self):
        self.name_lineedit.installEventFilter(self)
        self.submit_btn.clicked.connect(self.on_submit_clicked)

    def eventFilter(self, obj, event):
        if obj == self.name_lineedit and event.type() == QEvent.FocusOut:
            self.validate_input()
        return super().eventFilter(obj, event)

    def on_input_changed(self, text):
        self.validate_input()

    def validate_input(self):
        name = self.name_lineedit.text().strip()

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

        self.validation_hint.setVisible(False)
        self.submit_btn.setEnabled(True)
        return True

    def on_submit_clicked(self):
        if not self.validate_input():
            QMessageBox.warning(self, '输入验证', '请填写完整信息')

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
        self.validation_hint.setVisible(False)
        self.submit_btn.setEnabled(False)