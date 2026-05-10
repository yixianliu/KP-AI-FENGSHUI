from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QFrame, QGridLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QApplication,
                             QScrollArea, QSizePolicy, QProxyStyle)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class ResultCard(QFrame):
    def __init__(self, title, icon, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.is_expanded = True
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E8D5B5;
                border-radius: 10px;
            }
        """)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: #5D4037;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(15, 10, 10, 10)

        self.expand_btn = QPushButton('▼')
        self.expand_btn.setFixedSize(24, 24)
        self.expand_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #D4AF37;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #FFF8E7;
            }
        """)
        self.expand_btn.clicked.connect(self.toggle_expand)

        self.icon_label = QLabel(self.icon)
        self.icon_label.setStyleSheet("font-size: 16px;")

        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #D4AF37;
        """)

        self.header_layout.addWidget(self.expand_btn)
        self.header_layout.addWidget(self.icon_label)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()

        self.copy_btn = QPushButton('复制')
        self.copy_btn.setFixedSize(50, 24)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #D4AF37;
                color: #5D4037;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B89600;
            }
        """)
        self.copy_btn.clicked.connect(self.on_copy)
        self.header_layout.addWidget(self.copy_btn)

        self.main_layout.addWidget(self.header_frame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 15, 15, 15)

        self.main_layout.addWidget(self.content_widget)

        self.setLayout(self.main_layout)

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        self.expand_btn.setText('▶' if not self.is_expanded else '▼')

    def on_copy(self):
        text = self.get_copy_text()
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, '复制成功', f'{self.title}已复制到剪贴板')

    def get_copy_text(self):
        return ""

    def set_content(self, widget):
        self.content_layout.addWidget(widget)

class ResultPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(15)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #F5E6D3;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #D4AF37;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #B89600;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(15)

        self.bazi_card = ResultCard('四柱八字', '🔮')
        self.wuxing_card = ResultCard('五行分布', '⚗️')
        self.shishen_card = ResultCard('十神分析', '📊')
        self.geju_card = ResultCard('命局格局', '🏆')

        self.init_bazi_content()
        self.init_wuxing_content()
        self.init_shishen_content()
        self.init_geju_content()

        self.scroll_layout.addWidget(self.bazi_card)
        self.scroll_layout.addWidget(self.wuxing_card)
        self.scroll_layout.addWidget(self.shishen_card)
        self.scroll_layout.addWidget(self.geju_card)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)

        self.layout.addWidget(self.scroll_area)

        self.setLayout(self.layout)

        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)

    def init_bazi_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

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
                font-size: 28px;
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

        self.bazi_card.set_content(content_widget)

    def init_wuxing_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

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
                font-size: 22px;
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

        self.wuxing_card.set_content(content_widget)

    def init_shishen_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        self.shishen_table = QTableWidget(4, 5)
        self.shishen_table.setHorizontalHeaderLabels(['柱位', '天干', '十神', '地支', '藏干十神'])
        self.shishen_table.verticalHeader().setVisible(False)
        self.shishen_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.shishen_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.shishen_table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 13px;
                background-color: transparent;
            }
            QTableWidget::item {
                padding: 10px;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #F5E6D3;
            }
            QHeaderView::section {
                background-color: #5D4037;
                color: white;
                font-weight: bold;
                padding: 10px;
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

        self.shishen_card.set_content(content_widget)

    def init_geju_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

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

        self.geju_card.set_content(content_widget)

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
