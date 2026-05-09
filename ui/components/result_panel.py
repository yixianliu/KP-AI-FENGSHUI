from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QFrame, QGridLayout, QTabWidget,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QApplication, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ResultPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(15, 15, 15, 15)

        self.create_header()
        self.create_tabs()

        self.setLayout(self.layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #FFF8E7;
            }
            QTabWidget::pane {
                border: 1px solid #E8D5B5;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #F5E6D3;
                color: #5D4037;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #5D4037;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #EBD9C4;
            }
            QLabel {
                color: #333333;
            }
            QFrame {
                background-color: white;
                border: 1px solid #E8D5B5;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #5D4037;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4A3428;
            }
        """)

    def create_header(self):
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #4A3728;
                border: none;
                border-radius: 8px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel('命盘分析结果')
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #D4AF37;
        """)
        title_label.setFont(QFont('SimHei', 16, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.copy_btn = QPushButton('复制结果')
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        header_layout.addWidget(self.copy_btn)

        self.layout.addWidget(header_frame)

    def create_tabs(self):
        self.tab_widget = QTabWidget()

        self.bazi_tab = self.create_bazi_tab()
        self.wuxing_tab = self.create_wuxing_tab()
        self.shishen_tab = self.create_shishen_tab()
        self.geju_tab = self.create_geju_tab()

        self.tab_widget.addTab(self.bazi_tab, '四柱八字')
        self.tab_widget.addTab(self.wuxing_tab, '五行分析')
        self.tab_widget.addTab(self.shishen_tab, '十神分析')
        self.tab_widget.addTab(self.geju_tab, '命局格局')

        self.layout.addWidget(self.tab_widget)

    def create_bazi_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)

        self.bazi_grid = QGridLayout()
        self.bazi_grid.setSpacing(20)

        pillars = ['年柱', '月柱', '日柱', '时柱']
        for i, pillar in enumerate(pillars):
            label = QLabel(pillar)
            label.setStyleSheet("""
                font-size: 13px;
                color: #8B7355;
                font-weight: bold;
            """)
            label.setAlignment(Qt.AlignCenter)
            self.bazi_grid.addWidget(label, 0, i)

            ganzhi = QLabel('--')
            ganzhi.setStyleSheet("""
                font-size: 26px;
                font-weight: bold;
                color: #5D4037;
                font-family: 'SimHei';
            """)
            ganzhi.setAlignment(Qt.AlignCenter)
            self.bazi_grid.addWidget(ganzhi, 1, i)

            decoration = QFrame()
            decoration.setFixedHeight(3)
            decoration.setStyleSheet("background-color: #D4AF37; border-radius: 2px;")
            self.bazi_grid.addWidget(decoration, 2, i)

        content_layout.addLayout(self.bazi_grid)

        self.date_label = QLabel('')
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("""
            font-size: 12px;
            color: #666666;
            padding-top: 10px;
        """)
        content_layout.addWidget(self.date_label)

        layout.addWidget(content_frame)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_wuxing_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)

        self.wuxing_grid = QGridLayout()
        self.wuxing_grid.setSpacing(15)

        elements = ['木', '火', '土', '金', '水']
        colors = {
            '木': '#228B22',
            '火': '#DC143C',
            '土': '#D2691E',
            '金': '#708090',
            '水': '#1E90FF'
        }

        for i, element in enumerate(elements):
            label = QLabel(element)
            label.setStyleSheet(f"""
                font-size: 20px;
                font-weight: bold;
                color: {colors[element]};
            """)
            label.setAlignment(Qt.AlignCenter)
            self.wuxing_grid.addWidget(label, 0, i)

            count = QLabel('--')
            count.setStyleSheet("""
                font-size: 16px;
                color: #5D4037;
                font-weight: bold;
            """)
            count.setAlignment(Qt.AlignCenter)
            self.wuxing_grid.addWidget(count, 1, i)

            bar_container = QFrame()
            bar_container.setStyleSheet("""
                QFrame {
                    background-color: #F5E6D3;
                    border-radius: 8px;
                }
            """)
            bar_layout = QHBoxLayout(bar_container)
            bar_layout.setContentsMargins(3, 3, 3, 3)

            bar = QFrame()
            bar.setFixedHeight(16)
            bar.setStyleSheet(f"background-color: {colors[element]}; border-radius: 6px;")
            bar.setMaximumWidth(0)
            bar_layout.addWidget(bar)

            self.wuxing_grid.addWidget(bar_container, 2, i)

            percentage = QLabel('--')
            percentage.setStyleSheet("font-size: 11px; color: #666666;")
            percentage.setAlignment(Qt.AlignCenter)
            self.wuxing_grid.addWidget(percentage, 3, i)

        content_layout.addLayout(self.wuxing_grid)

        self.wuxing_summary = QLabel('')
        self.wuxing_summary.setAlignment(Qt.AlignCenter)
        self.wuxing_summary.setStyleSheet("""
            font-size: 14px;
            color: #5D4037;
            font-weight: bold;
            padding-top: 15px;
            margin-top: 10px;
            border-top: 1px dashed #D4AF37;
        """)
        content_layout.addWidget(self.wuxing_summary)

        layout.addWidget(content_frame)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_shishen_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)

        self.shishen_table = QTableWidget(4, 5)
        self.shishen_table.setHorizontalHeaderLabels(['柱位', '天干', '十神', '地支', '藏干十神'])
        self.shishen_table.verticalHeader().setVisible(False)
        self.shishen_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.shishen_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.shishen_table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #F5E6D3;
            }
            QHeaderView::section {
                background-color: #5D4037;
                color: white;
                font-weight: bold;
                padding: 8px;
                text-align: center;
                border: none;
            }
        """)

        for i in range(4):
            for j in range(5):
                item = QTableWidgetItem('--')
                item.setTextAlignment(Qt.AlignCenter)
                self.shishen_table.setItem(i, j, item)

        content_layout.addWidget(self.shishen_table)

        self.shishen_summary = QLabel('')
        self.shishen_summary.setStyleSheet("""
            font-size: 13px;
            color: #5D4037;
            padding-top: 10px;
            border-top: 1px dashed #D4AF37;
        """)
        content_layout.addWidget(self.shishen_summary)

        layout.addWidget(content_frame)

        widget.setLayout(layout)
        return widget

    def create_geju_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)

        self.geju_content = QLabel('请输入信息并点击排盘按钮')
        self.geju_content.setStyleSheet("""
            font-size: 14px;
            color: #333333;
            line-height: 1.8;
        """)
        self.geju_content.setWordWrap(True)

        geju_frame = QFrame()
        geju_frame.setStyleSheet("""
            QFrame {
                background-color: #F5E6D3;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        geju_layout = QVBoxLayout(geju_frame)
        geju_layout.addWidget(self.geju_content)

        content_layout.addWidget(geju_frame)

        layout.addWidget(content_frame)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def get_wuxing_color(self, element):
        colors = {
            '木': '#228B22',
            '火': '#DC143C',
            '土': '#D2691E',
            '金': '#708090',
            '水': '#1E90FF'
        }
        return colors.get(element, '#333333')

    def update_bazi(self, data):
        pillars = ['年柱', '月柱', '日柱', '时柱']
        values = [data['year'], data['month'], data['day'], data['hour']]

        for i, value in enumerate(values):
            label = self.bazi_grid.itemAtPosition(1, i).widget()
            label.setText(value)

        self.date_label.setText(f"公历: {data['solar_date']} | 农历: {data['lunar_date']}")

    def update_wuxing(self, data):
        elements = ['木', '火', '土', '金', '水']

        for i, element in enumerate(elements):
            count_label = self.wuxing_grid.itemAtPosition(1, i).widget()
            count_label.setText(f"{data[element]['count']:.1f}")

            bar_container = self.wuxing_grid.itemAtPosition(2, i).widget()
            bar = bar_container.layout().itemAt(0).widget()
            bar.setMaximumWidth(int(data[element]['percentage'] * 2.5))

            percentage_label = self.wuxing_grid.itemAtPosition(3, i).widget()
            percentage_label.setText(f"{data[element]['percentage']}%")

        self.wuxing_summary.setText(f"五行分析: {data['summary']}")

    def update_shishen(self, data):
        for i, detail in enumerate(data['details']):
            self.shishen_table.item(i, 0).setText(detail['pillar'])
            self.shishen_table.item(i, 1).setText(detail['gan'])
            self.shishen_table.item(i, 2).setText(detail['gan_shishen'])
            self.shishen_table.item(i, 3).setText(detail['zhi'])
            self.shishen_table.item(i, 4).setText(' '.join(detail['zhi_shishens']))

        summary_text = f"日主: {data['rizhu']} ({data['rizhu_wuxing']}) | "
        summary_text += ', '.join([f"{k}: {v}个" for k, v in data['summary'].items()])
        self.shishen_summary.setText(summary_text)

    def update_geju(self, bazhi, wuxing, shishen):
        rizhu = bazhi['rizhu']
        summary = []

        if wuxing['summary']:
            summary.append(wuxing['summary'])

        shishen_list = list(shishen['summary'].keys())
        if '正官' in shishen_list or '七杀' in shishen_list:
            summary.append('官杀混杂' if ('正官' in shishen_list and '七杀' in shishen_list) else '官杀得位')

        if '正印' in shishen_list or '偏印' in shishen_list:
            summary.append('印星护身')

        if not summary:
            summary.append('格局平和')

        geju_text = '；'.join(summary)
        self.geju_content.setText(f"日主为{rizhu}，{geju_text}")

    def copy_to_clipboard(self):
        text = self.get_summary_text()
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, '复制成功', '结果已复制到剪贴板')

    def get_summary_text(self):
        lines = []
        lines.append("【四柱八字】")
        pillars = ['年柱', '月柱', '日柱', '时柱']
        for i in range(4):
            value = self.bazi_grid.itemAtPosition(1, i).widget().text()
            lines.append(f"  {pillars[i]}: {value}")

        lines.append(f"\n{self.date_label.text()}")

        lines.append("\n【五行分布】")
        elements = ['木', '火', '土', '金', '水']
        for i, element in enumerate(elements):
            count = self.wuxing_grid.itemAtPosition(1, i).widget().text()
            pct = self.wuxing_grid.itemAtPosition(3, i).widget().text()
            lines.append(f"  {element}: {count}个 ({pct})")

        if self.wuxing_summary.text():
            lines.append(f"\n{self.wuxing_summary.text()}")

        lines.append("\n【十神分析】")
        for i in range(4):
            row_data = [self.shishen_table.item(i, j).text() for j in range(5)]
            lines.append(f"  {' | '.join(row_data)}")

        if self.shishen_summary.text():
            lines.append(f"\n{self.shishen_summary.text()}")

        lines.append("\n【命局格局】")
        lines.append(f"  {self.geju_content.text()}")

        return '\n'.join(lines)

    def clear(self):
        self.geju_content.setText('请输入信息并点击排盘按钮')
        self.date_label.setText('')
        self.wuxing_summary.setText('')
        self.shishen_summary.setText('')

        for i in range(4):
            label = self.bazi_grid.itemAtPosition(1, i).widget()
            label.setText('--')

        elements = ['木', '火', '土', '金', '水']
        for i, element in enumerate(elements):
            count_label = self.wuxing_grid.itemAtPosition(1, i).widget()
            count_label.setText('--')

            bar_container = self.wuxing_grid.itemAtPosition(2, i).widget()
            bar = bar_container.layout().itemAt(0).widget()
            bar.setMaximumWidth(0)

            percentage_label = self.wuxing_grid.itemAtPosition(3, i).widget()
            percentage_label.setText('--')

        for i in range(4):
            for j in range(5):
                self.shishen_table.item(i, j).setText('--')
