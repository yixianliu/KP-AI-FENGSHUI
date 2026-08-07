"""
导出排盘结果对话框
提供 CSV / Excel / PDF 三种导出格式选择、可选导出章节（来自 ui.export.base_exporter.CHAPTERS）
以及导出文件名前缀；确认后通过 export_signal 抛出所选格式，交由主窗口驱动 ui/export/ 下的导出器。
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QCheckBox, QPushButton,
                             QGroupBox, QLineEdit, QRadioButton,
                             QMessageBox, QGridLayout)
from PySide6.QtCore import Signal, Qt

from ui.export.base_exporter import CHAPTERS


class ExportDialog(QDialog):
    """导出排盘结果对话框：选择格式 / 章节与文件名，确认后发出导出信号。"""
    export_signal = Signal(str)

    def __init__(self, data, parent=None):
        """初始化导出对话框。

        Args:
            data: 排盘结果数据（dict），用于推导默认文件名。
            parent: 父窗口（可选）。
        """
        super().__init__(parent)
        self.data = data
        self.init_ui()

    def init_ui(self):
        """构建导出对话框全部 UI：格式单选、章节勾选、文件名输入与操作按钮。"""
        self.setWindowTitle('导出排盘结果')
        self.setFixedSize(470, 520)
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
            QPushButton#ghost {
                background: transparent;
                color: #5D4037;
                border: 1px solid #D4AF37;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: normal;
            }
            QPushButton#ghost:hover {
                background: #F3E9CF;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel('导出排盘结果')
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #5D4037;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # ---------- 导出格式 ----------
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

        # ---------- 导出内容（可选章节） ----------
        content_group = QGroupBox('导出内容（勾选章节）')
        content_layout = QVBoxLayout()

        quick_row = QHBoxLayout()
        self.select_all_btn = QPushButton('全选')
        self.select_all_btn.setObjectName('ghost')
        self.select_all_btn.clicked.connect(lambda: self._set_all(True))
        self.select_none_btn = QPushButton('全不选')
        self.select_none_btn.setObjectName('ghost')
        self.select_none_btn.clicked.connect(lambda: self._set_all(False))
        quick_row.addStretch()
        quick_row.addWidget(self.select_all_btn)
        quick_row.addWidget(self.select_none_btn)
        content_layout.addLayout(quick_row)

        # 章节勾选（2 列网格），与 ui.export.base_exporter.CHAPTERS 对应
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)
        self._checks = {}
        for i, (key, label) in enumerate(CHAPTERS):
            cb = QCheckBox(label)
            cb.setChecked(True)
            grid.addWidget(cb, i // 2, i % 2)
            self._checks[key] = cb
        content_layout.addLayout(grid)

        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        # ---------- 文件名 ----------
        filename_group = QGroupBox('文件名')
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel('前缀:'))
        self.filename_edit = QLineEdit()
        _dft = self.data.get('basic_info', {}).get('solar_date') or '八字排盘'
        self.filename_edit.setText(f"八字排盘_{_dft}")
        filename_layout.addWidget(self.filename_edit)
        filename_group.setLayout(filename_layout)
        layout.addWidget(filename_group)

        # ---------- 按钮 ----------
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

    def _set_all(self, checked: bool):
        """由「全选/全不选」按钮触发：批量设置所有章节勾选框状态。"""
        for cb in self._checks.values():
            cb.setChecked(checked)

    def get_selected_chapters(self):
        """返回勾选的章节 key 列表"""
        return [key for key, cb in self._checks.items() if cb.isChecked()]

    def on_export(self):
        """由「导出」按钮 clicked 触发：确定格式、校验章节、发出 export_signal 并关闭。"""
        if self.csv_radio.isChecked():
            format_type = 'csv'
        elif self.excel_radio.isChecked():
            format_type = 'excel'
        else:
            format_type = 'pdf'

        if not self.get_selected_chapters():
            QMessageBox.warning(self, '请选择章节', '至少勾选一个导出章节。')
            return

        self.export_signal.emit(format_type)
        self.accept()

    def get_selected_format(self):
        """返回当前选中的导出格式字符串（'csv' / 'excel' / 'pdf'）。"""
        if self.csv_radio.isChecked():
            return 'csv'
        elif self.excel_radio.isChecked():
            return 'excel'
        else:
            return 'pdf'
