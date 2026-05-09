from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QRadioButton, 
                             QDateEdit, QSpinBox, QPushButton,
                             QButtonGroup, QComboBox)
from PyQt5.QtCore import QDate, Qt

class InputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.name_edit = self.create_name_input()
        self.gender_group = self.create_gender_select()
        self.calendar_switch = self.create_calendar_switch()
        self.date_edit = self.create_date_input()
        self.hour_spin = self.create_hour_input()
        self.submit_btn = self.create_submit_button()
        
        layout.addWidget(QLabel('<span style="font-size: 16px; font-weight: bold; color: #5D4037;">基本信息</span>'))
        layout.addWidget(self.name_edit)
        layout.addWidget(self.gender_group)
        
        layout.addWidget(QLabel('<span style="font-size: 16px; font-weight: bold; color: #5D4037;">出生日期</span>'))
        layout.addWidget(self.calendar_switch)
        layout.addWidget(self.date_edit)
        
        layout.addWidget(QLabel('<span style="font-size: 16px; font-weight: bold; color: #5D4037;">出生时辰</span>'))
        layout.addWidget(self.hour_spin)
        
        layout.addStretch()
        layout.addWidget(self.submit_btn)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #FFF8E7;
                border-radius: 10px;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #D4AF37;
                border-radius: 5px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #5D4037;
                outline: none;
            }
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #D4AF37;
                border-radius: 5px;
                font-size: 14px;
                background-color: white;
            }
            QDateEdit:focus {
                border-color: #5D4037;
                outline: none;
            }
            QSpinBox {
                padding: 8px 12px;
                border: 1px solid #D4AF37;
                border-radius: 5px;
                font-size: 14px;
                background-color: white;
            }
            QSpinBox:focus {
                border-color: #5D4037;
                outline: none;
            }
            QRadioButton {
                color: #333333;
                font-size: 14px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton::indicator::checked {
                background-color: #D4AF37;
                border-color: #D4AF37;
            }
            QPushButton {
                background-color: #5D4037;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4A3428;
            }
            QPushButton:pressed {
                background-color: #3D2A20;
            }
        """)
    
    def create_name_input(self):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(QLabel('姓名:'))
        self.name_lineedit = QLineEdit()
        self.name_lineedit.setPlaceholderText('请输入姓名')
        layout.addWidget(self.name_lineedit)
        widget.setLayout(layout)
        return widget
    
    def create_gender_select(self):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(QLabel('性别:'))
        
        self.gender_group = QButtonGroup()
        self.male_radio = QRadioButton('男')
        self.female_radio = QRadioButton('女')
        self.male_radio.setChecked(True)
        
        self.gender_group.addButton(self.male_radio)
        self.gender_group.addButton(self.female_radio)
        
        layout.addWidget(self.male_radio)
        layout.addWidget(self.female_radio)
        widget.setLayout(layout)
        return widget
    
    def create_calendar_switch(self):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(QLabel('历法:'))
        
        self.calendar_group = QButtonGroup()
        self.solar_radio = QRadioButton('公历')
        self.lunar_radio = QRadioButton('农历')
        self.solar_radio.setChecked(True)
        
        self.calendar_group.addButton(self.solar_radio)
        self.calendar_group.addButton(self.lunar_radio)
        
        layout.addWidget(self.solar_radio)
        layout.addWidget(self.lunar_radio)
        widget.setLayout(layout)
        return widget
    
    def create_date_input(self):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(QLabel('日期:'))
        
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        self.date_edit.setCalendarPopup(True)
        
        layout.addWidget(self.date_edit)
        widget.setLayout(layout)
        return widget
    
    def create_hour_input(self):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(QLabel('时辰(24小时制):'))
        
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(12)
        
        layout.addWidget(self.hour_spin)
        layout.addWidget(QLabel('时'))
        widget.setLayout(layout)
        return widget
    
    def create_submit_button(self):
        self.submit_btn = QPushButton('开始排盘')
        return self.submit_btn
    
    def get_data(self):
        return {
            'name': self.name_lineedit.text(),
            'gender': '男' if self.male_radio.isChecked() else '女',
            'is_lunar': self.lunar_radio.isChecked(),
            'year': self.date_edit.date().year(),
            'month': self.date_edit.date().month(),
            'day': self.date_edit.date().day(),
            'hour': self.hour_spin.value()
        }