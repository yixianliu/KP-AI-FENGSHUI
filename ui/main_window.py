import sys
import traceback
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QFrame, QProgressBar,
                             QStatusBar, QMessageBox, QShortcut, QFileDialog, 
                             QApplication, QPushButton)
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QKeySequence
from ui.components.input_panel import InputPanel
from ui.components.result_panel import ResultPanel
from core.baazi import BaZiCalculator
from core.wuxing import WuXingAnalyzer
from core.shishen import ShiShenAnalyzer
from core.yunshi import YunShiCalculator
from core.mingli import MingLiAnalyzer
from core.ai_analyzer import AIAnalyzer
from ui.styles import Stylesheets, Colors, Fonts, Spacing

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_data = None
        self.is_calculating = False
        self.init_ui()
        self.init_analyzers()
        self.init_shortcuts()

    def init_ui(self):
        self.setWindowTitle('八字排盘')
        self.setGeometry(100, 100, 1200, 900)
        self.setMinimumSize(1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)

        header_frame = self.create_header()
        main_layout.addWidget(header_frame)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(int(Spacing.MODULE_GAP.replace('px', '')), 
                                          int(Spacing.MODULE_GAP.replace('px', '')), 
                                          int(Spacing.MODULE_GAP.replace('px', '')), 
                                          int(Spacing.MODULE_GAP.replace('px', '')))
        content_layout.setSpacing(int(Spacing.MODULE_GAP.replace('px', '')))

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.input_panel = InputPanel()
        self.input_panel.submit_btn.clicked.connect(self.on_calculate)
        
        left_layout.addWidget(self.input_panel)
        left_layout.addStretch()

        content_layout.addWidget(left_container)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.result_panel = ResultPanel()
        right_layout.addWidget(self.result_panel)

        content_layout.addWidget(right_container)
        content_layout.setStretch(0, 1)
        content_layout.setStretch(1, 2)

        main_layout.addLayout(content_layout)

        self.statusBar().setStyleSheet(Stylesheets.STATUS_BAR)
        self.statusBar().showMessage('就绪')

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(280)
        self.progress_bar.setMaximumHeight(12)
        self.progress_bar.setStyleSheet(Stylesheets.PROGRESS_BAR)
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

        self.setStyleSheet(Stylesheets.MAIN_WINDOW)

        self.loading_overlay = self.create_loading_overlay()
    
    def create_header(self):
        header_frame = QFrame()
        header_frame.setFixedHeight(60)
        header_frame.setStyleSheet(Stylesheets.HEADER)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(int(Spacing.CARD_PADDING.replace('px', '')), 0, int(Spacing.CARD_PADDING.replace('px', '')), 0)

        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)

        title_label = QLabel('八字排盘')
        title_label.setStyleSheet(Stylesheets.HEADER_TITLE)

        subtitle_label = QLabel('专业精准排盘')
        subtitle_label.setStyleSheet(Stylesheets.HEADER_SUBTITLE)

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.addStretch()

        self.status_icon = QLabel('')
        self.status_icon.setStyleSheet(f"font-size: 16px; margin-right: 8px;")

        self.status_label = QLabel('就绪')
        self.status_label.setStyleSheet(Stylesheets.LABEL_BODY)

        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_label)

        header_layout.addLayout(title_layout)
        header_layout.addLayout(status_layout)

        return header_frame

    def create_loading_overlay(self):
        overlay = QFrame()
        overlay.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(249, 247, 243, 0.96);
            }}
        """)
        overlay.setGeometry(QRect(0, 0, self.width(), self.height()))
        overlay.hide()

        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setAlignment(Qt.AlignCenter)

        loading_container = QWidget()
        loading_container.setStyleSheet(Stylesheets.CARD)
        loading_layout = QVBoxLayout(loading_container)
        loading_layout.setContentsMargins(40, 40, 40, 40)
        loading_layout.setSpacing(20)

        loading_icon = QLabel('☯')
        loading_icon.setStyleSheet(f"font-size: 48px;")
        loading_icon.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(loading_icon)

        self.loading_text = QLabel('正在分析您的命理信息...')
        self.loading_text.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SECTION};
            color: {Colors.TEXT_PRIMARY};
            font-family: {Fonts.FAMILY_CN};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)
        self.loading_text.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(self.loading_text)

        self.loading_progress = QProgressBar()
        self.loading_progress.setFixedWidth(220)
        self.loading_progress.setStyleSheet(Stylesheets.PROGRESS_BAR)
        loading_layout.addWidget(self.loading_progress)

        overlay_layout.addWidget(loading_container)

        return overlay

    def init_shortcuts(self):
        QShortcut(QKeySequence('Ctrl+Return'), self, self.on_calculate)
        QShortcut(QKeySequence('Ctrl+R'), self, self.on_reset)

    def init_analyzers(self):
        self.baazi_calculator = BaZiCalculator()
        self.wuxing_analyzer = WuXingAnalyzer()
        self.shishen_analyzer = ShiShenAnalyzer()
        self.yunshi_calculator = YunShiCalculator()
        self.mingli_analyzer = MingLiAnalyzer()
        self.ai_analyzer = AIAnalyzer()

    def show_loading(self):
        self.loading_overlay.setGeometry(QRect(0, 0, self.width(), self.height()))
        self.loading_overlay.show()
        self.loading_progress.setValue(0)
        self.is_calculating = True
        self.statusBar().showMessage('正在排盘中...')

    def hide_loading(self):
        self.loading_overlay.hide()
        self.is_calculating = False

    def update_loading_progress(self, value, text):
        self.loading_progress.setValue(value)
        self.loading_text.setText(text)
        QApplication.processEvents()

    def on_reset(self):
        self.input_panel.clear()
        self.result_panel.clear()
        self.statusBar().showMessage('已重置')
        self.status_icon.setText('')

    def on_calculate(self):
        if self.is_calculating:
            return

        if not self.input_panel.validate_input():
            return

        self.show_loading()
        QTimer.singleShot(50, self.perform_calculate)

    def perform_calculate(self):
        try:
            self.update_loading_progress(10, '正在分析八字命盘...')

            data = self.input_panel.get_data()

            self.update_loading_progress(20, '正在计算四柱八字...')
            bazhi = self.baazi_calculator.calculate(
                data['year'],
                data['month'],
                data['day'],
                data['hour'],
                data['is_lunar']
            )

            self.update_loading_progress(35, '正在分析五行...')
            wuxing_result = self.wuxing_analyzer.analyze(bazhi)

            self.update_loading_progress(50, '正在分析十神...')
            shishen_result = self.shishen_analyzer.analyze(bazhi)

            self.update_loading_progress(60, '正在计算大运流年...')
            major_fortune = self.yunshi_calculator.calculate_major_fortune(
                bazhi, data['gender'], data['year']
            )

            self.update_loading_progress(75, '正在分析命理元素...')
            mingli_result = self.mingli_analyzer.analyze_all(bazhi)

            self.update_loading_progress(85, '正在生成AI分析...')
            ai_analysis = self.ai_analyzer.analyze(bazhi, wuxing_result, shishen_result, mingli_result)

            self.update_loading_progress(95, '正在渲染结果...')
            QTimer.singleShot(200, lambda: self.update_results(
                bazhi, wuxing_result, shishen_result,
                major_fortune, mingli_result, ai_analysis, data
            ))

        except Exception as e:
            error_msg = f"排盘过程中发生错误:\n{str(e)}"
            self.log_error(error_msg)
            self.show_error(error_msg)
            self.statusBar().showMessage('排盘失败')
            self.hide_loading()

    def update_results(self, bazhi, wuxing_result, shishen_result,
                      major_fortune, mingli_result, ai_analysis, input_data):
        self.result_panel.update_basic_info(bazhi, input_data)
        self.result_panel.update_bazi(bazhi, shishen_result)
        self.result_panel.update_wuxing(wuxing_result)
        self.result_panel.update_fortune(major_fortune)
        self.result_panel.update_ai_analysis(ai_analysis)

        self.current_data = {
            'input': input_data,
            'bazhi': bazhi,
            'wuxing': wuxing_result,
            'shishen': shishen_result,
            'major_fortune': major_fortune,
            'mingli': mingli_result,
            'ai_analysis': ai_analysis
        }

        self.statusBar().showMessage("排盘完成")
        self.status_icon.setText('✓')

        self.update_loading_progress(100, '完成')
        QTimer.singleShot(300, self.hide_loading)

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
                f"八字排盘",
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

    def on_about(self):
        QMessageBox.about(self, '关于',
            '<div style="text-align: center;">'
            '<h2>八字排盘</h2>'
            '<p>专业精准排盘 · AI智能分析</p>'
            '<p style="margin-top: 15px;">基于传统八字命理理论，'
            '提供四柱、五行、十神、大运等综合分析。</p>'
            '</div>'
        )

    def show_error(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle('错误')
        msg_box.setText(message)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {Colors.BACKGROUND};
            }}
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.SIZE_BODY};
            }}
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: {Spacing.CONTROL_RADIUS};
                font-size: {Fonts.SIZE_BODY};
                font-weight: {Fonts.WEIGHT_BOLD};
            }}
            QPushButton:hover {{
                background-color: {Colors.ACCENT_LIGHT};
            }}
        """)
        msg_box.exec_()

    def log_error(self, message):
        with open('baazi_error.log', 'a', encoding='utf-8') as f:
            import datetime
            f.write(f"[{datetime.datetime.now()}] {message}\n")
            traceback.print_exc(file=f)

    def resizeEvent(self, event):
        if self.loading_overlay:
            self.loading_overlay.setGeometry(QRect(0, 0, self.width(), self.height()))
        super().resizeEvent(event)
