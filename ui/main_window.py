import sys
import traceback
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QStackedWidget,
                             QFrame, QProgressBar, QMenuBar, QMenu,
                             QAction, QToolBar, QStatusBar, QMessageBox,
                             QShortcut, QFileDialog, QApplication)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QKeySequence
from ui.components.input_panel import InputPanel
from ui.components.result_panel import ResultPanel
from core.baazi import BaZiCalculator
from core.wuxing import WuXingAnalyzer
from core.shishen import ShiShenAnalyzer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_data = None
        self.init_ui()
        self.init_analyzers()
        self.init_shortcuts()

    def init_ui(self):
        self.setWindowTitle('八字排盘')
        self.setGeometry(100, 100, 1000, 800)
        self.setMinimumSize(800, 600)

        self.create_menu_bar()
        self.create_tool_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)

        header_frame = self.create_header()
        main_layout.addWidget(header_frame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)

        self.input_panel = InputPanel()
        self.input_panel.submit_btn.clicked.connect(self.on_calculate)

        self.result_panel = ResultPanel()

        self.content_layout.addWidget(self.input_panel)
        self.content_layout.addWidget(self.result_panel)

        main_layout.addWidget(self.content_widget)

        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #F5E6D3;
                color: #5D4037;
                border-top: 1px solid #D4AF37;
            }
        """)
        self.statusBar().showMessage('就绪')

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setMaximumHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #D4AF37;
                border-radius: 4px;
                background-color: #FFF8E7;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #D4AF37;
                border-radius: 3px;
            }
        """)
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5E6D3;
            }
        """)

    def create_header(self):
        header_frame = QFrame()
        header_frame.setFixedHeight(60)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #4A3728;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title_label = QLabel('八字排盘')
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #D4AF37;
        """)
        title_label.setFont(QFont('SimHei', 24, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.status_label = QLabel('就绪')
        self.status_label.setStyleSheet("""
            font-size: 13px;
            color: #FFF8E7;
        """)
        header_layout.addWidget(self.status_label)

        return header_frame

    def create_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #4A3728;
                color: #FFF8E7;
                padding: 5px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 15px;
            }
            QMenuBar::item:selected {
                background-color: #5D4037;
            }
            QMenu {
                background-color: #FFF8E7;
                color: #333333;
                border: 1px solid #D4AF37;
            }
            QMenu::item:selected {
                background-color: #F5E6D3;
            }
        """)

        file_menu = menubar.addMenu('文件')

        new_action = QAction('新建', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.on_new)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        export_menu = menubar.addMenu('导出')

        export_csv_action = QAction('导出为 CSV', self)
        export_csv_action.setShortcut('Ctrl+E')
        export_csv_action.triggered.connect(lambda: self.on_export('csv'))
        export_menu.addAction(export_csv_action)

        export_excel_action = QAction('导出为 Excel', self)
        export_excel_action.setShortcut('Ctrl+Shift+E')
        export_excel_action.triggered.connect(lambda: self.on_export('excel'))
        export_menu.addAction(export_excel_action)

        export_pdf_action = QAction('导出为 PDF', self)
        export_pdf_action.setShortcut('Ctrl+P')
        export_pdf_action.triggered.connect(lambda: self.on_export('pdf'))
        export_menu.addAction(export_pdf_action)

        help_menu = menubar.addMenu('帮助')

        about_action = QAction('关于', self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)

    def create_tool_bar(self):
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #5D4037;
                border: none;
                padding: 5px;
            }
            QToolButton {
                background-color: transparent;
                color: #FFF8E7;
                padding: 8px;
                border-radius: 5px;
            }
            QToolButton:hover {
                background-color: #6B4423;
            }
            QToolButton:pressed {
                background-color: #4A3428;
            }
        """)
        self.addToolBar(toolbar)

        new_action = QAction('新建', self)
        new_action.triggered.connect(self.on_new)
        toolbar.addAction(new_action)

        toolbar.addSeparator()

        export_action = QAction('导出', self)
        export_action.triggered.connect(self.on_show_export_dialog)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        quick_action = QAction('快速排盘', self)
        quick_action.triggered.connect(self.on_quick_calculate)
        toolbar.addAction(quick_action)

    def init_shortcuts(self):
        QShortcut(QKeySequence('Ctrl+Return'), self, self.on_calculate)
        QShortcut(QKeySequence('Ctrl+R'), self, self.on_quick_calculate)

    def init_analyzers(self):
        self.baazi_calculator = BaZiCalculator()
        self.wuxing_analyzer = WuXingAnalyzer()
        self.shishen_analyzer = ShiShenAnalyzer()

    def on_new(self):
        self.input_panel.clear()
        self.result_panel.clear()
        self.statusBar().showMessage('已新建')

    def on_quick_calculate(self):
        from PyQt5.QtCore import QDate, QTime
        current_date = QDate.currentDate()
        self.input_panel.date_edit.setDate(current_date)
        current_hour = QTime.currentTime().hour()
        self.input_panel.hour_combo.setCurrentIndex(self.input_panel.get_hour_index(current_hour))
        self.on_calculate()

    def on_calculate(self):
        self.statusBar().showMessage('正在排盘中...')
        self.progress_bar.show()
        self.progress_bar.setValue(10)
        QTimer.singleShot(50, self.perform_calculate)

    def perform_calculate(self):
        try:
            self.progress_bar.setValue(30)

            data = self.input_panel.get_data()

            if not data['name']:
                self.show_error("请输入姓名")
                return

            self.progress_bar.setValue(50)

            bazhi = self.baazi_calculator.calculate(
                data['year'],
                data['month'],
                data['day'],
                data['hour'],
                data['is_lunar']
            )

            wuxing_result = self.wuxing_analyzer.analyze(bazhi)
            shishen_result = self.shishen_analyzer.analyze(bazhi)

            self.progress_bar.setValue(70)

            self.result_panel.update_bazi(bazhi)
            self.result_panel.update_wuxing(wuxing_result)
            self.result_panel.update_shishen(shishen_result)
            self.result_panel.update_geju(bazhi, wuxing_result, shishen_result)

            self.current_data = {
                'input': data,
                'bazhi': bazhi,
                'wuxing': wuxing_result,
                'shishen': shishen_result
            }

            self.progress_bar.setValue(100)
            self.statusBar().showMessage(f"排盘完成 - {data['name']}")

            QTimer.singleShot(500, self.progress_bar.hide)

        except Exception as e:
            error_msg = f"排盘过程中发生错误:\n{str(e)}"
            self.log_error(error_msg)
            self.show_error(error_msg)
            self.statusBar().showMessage('排盘失败')
            self.progress_bar.hide()

    def on_export(self, format_type):
        if not self.current_data:
            self.show_error("请先进行排盘操作")
            return

        try:
            from ui.export import get_exporter
            exporter_class = get_exporter(format_type)
            exporter = exporter_class()

            file_filter = {
                'csv': 'CSV Files (*.csv)',
                'excel': 'Excel Files (*.xlsx)',
                'pdf': 'PDF Files (*.pdf)'
            }

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                f"导出为{format_type.upper()}",
                f"八字排盘_{self.current_data['input']['name']}",
                file_filter[format_type]
            )

            if file_path:
                exporter.export(self.current_data, file_path)
                self.statusBar().showMessage(f"导出成功: {file_path}")
                QMessageBox.information(self, '导出成功', f'文件已保存至:\n{file_path}')

        except ImportError as e:
            self.show_error(f"导出功能未安装所需依赖:\n{str(e)}\n\n请运行: pip install pandas openpyxl reportlab")
        except Exception as e:
            self.log_error(f"导出失败: {str(e)}")
            self.show_error(f"导出失败:\n{str(e)}")

    def on_show_export_dialog(self):
        if not self.current_data:
            self.show_error("请先进行排盘操作")
            return

        from ui.components.export_dialog import ExportDialog
        dialog = ExportDialog(self.current_data, self)
        dialog.export_signal.connect(self.on_export)
        dialog.exec_()

    def on_about(self):
        QMessageBox.about(self, '关于',
            '<div style="text-align: center;">'
            '<h2>八字排盘</h2>'
            '<p>版本 1.0</p>'
            '<p>传统命理 · 精准排盘</p>'
            '<p style="margin-top: 15px;">基于传统八字命理理论，'
            '提供四柱、五行、十神等综合分析。</p>'
            '</div>'
        )

    def show_error(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle('错误')
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #FFF8E7;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QPushButton {
                background-color: #5D4037;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4A3428;
            }
        """)
        msg_box.exec_()

    def log_error(self, message):
        with open('baazi_error.log', 'a', encoding='utf-8') as f:
            import datetime
            f.write(f"[{datetime.datetime.now()}] {message}\n")
            traceback.print_exc(file=f)
