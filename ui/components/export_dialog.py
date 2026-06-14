from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QCheckBox, QPushButton,
                             QGroupBox, QLineEdit, QButtonGroup, QRadioButton,
                             QFileDialog, QMessageBox)
from PySide6.QtCore import Signal, Qt

class ExportDialog(QDialog):
    export_signal = Signal(str)

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('导出排盘结果')
        self.setFixedSize(450, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFF8E7;
            }
            QLabel {
                color: #333333;
                font-size: 13px;
            }
            QGroupBox {
                font-weight: bold;
                color: #5D4037;
                border: 1px solid #D4AF37;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
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
            QCheckBox {
                color: #333333;
                font-size: 13px;
                padding: 3px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #D4AF37;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #5D4037;
                border-color: #5D4037;
            }
            QRadioButton {
                color: #333333;
                font-size: 13px;
                padding: 3px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #D4AF37;
                border-radius: 9px;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                background-color: #5D4037;
                border-color: #5D4037;
            }
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #D4AF37;
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #5D4037;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5D4037, stop:1 #3D2A20);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
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

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel('导出排盘结果')
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #5D4037;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        format_group = QGroupBox('导出格式')
        format_layout = QVBoxLayout()

        format_options_layout = QHBoxLayout()
        self.csv_radio = QRadioButton('CSV (兼容性强)')
        self.csv_radio.setChecked(True)
        self.excel_radio = QRadioButton('Excel (推荐)')
        self.pdf_radio = QRadioButton('PDF (报告格式)')

        format_options_layout.addWidget(self.csv_radio)
        format_options_layout.addWidget(self.excel_radio)
        format_options_layout.addWidget(self.pdf_radio)
        format_layout.addLayout(format_options_layout)

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        content_group = QGroupBox('导出内容')
        content_layout = QVBoxLayout()

        self.basic_check = QCheckBox('基本信息')
        self.basic_check.setChecked(True)
        self.basic_check.setEnabled(False)

        self.bazi_check = QCheckBox('四柱八字')
        self.bazi_check.setChecked(True)
        self.bazi_check.setEnabled(False)

        self.wuxing_check = QCheckBox('五行分布')
        self.wuxing_check.setChecked(True)
        self.wuxing_check.setEnabled(False)

        self.shishen_check = QCheckBox('十神分析')
        self.shishen_check.setChecked(True)
        self.shishen_check.setEnabled(False)

        self.geju_check = QCheckBox('命局格局')
        self.geju_check.setChecked(True)
        self.geju_check.setEnabled(False)

        content_layout.addWidget(self.basic_check)
        content_layout.addWidget(self.bazi_check)
        content_layout.addWidget(self.wuxing_check)
        content_layout.addWidget(self.shishen_check)
        content_layout.addWidget(self.geju_check)

        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        filename_group = QGroupBox('文件名')
        filename_layout = QHBoxLayout()

        filename_layout.addWidget(QLabel('前缀:'))

        self.filename_edit = QLineEdit()
        self.filename_edit.setText(f"八字排盘_{self.data['input']['name']}")
        filename_layout.addWidget(self.filename_edit)

        filename_group.setLayout(filename_layout)
        layout.addWidget(filename_group)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.export_btn = QPushButton('导出')
        self.export_btn.clicked.connect(self.on_export)
        button_layout.addWidget(self.export_btn)

        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def on_export(self):
        if self.csv_radio.isChecked():
            format_type = 'csv'
            file_filter = 'CSV Files (*.csv)'
            default_ext = '.csv'
        elif self.excel_radio.isChecked():
            format_type = 'excel'
            file_filter = 'Excel Files (*.xlsx)'
            default_ext = '.xlsx'
        else:
            format_type = 'pdf'
            file_filter = 'PDF Files (*.pdf)'
            default_ext = '.pdf'

        filename = self.filename_edit.text().strip()
        if not filename:
            filename = f"八字排盘_{self.data['input']['name']}"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            '导出文件',
            filename + default_ext,
            file_filter
        )

        if file_path:
            self.export_signal.emit(format_type)
            self.accept()

    def get_selected_format(self):
        if self.csv_radio.isChecked():
            return 'csv'
        elif self.excel_radio.isChecked():
            return 'excel'
        else:
            return 'pdf'
