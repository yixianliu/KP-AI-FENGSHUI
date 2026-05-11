from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QFrame, QGridLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QApplication,
                             QScrollArea, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer
from ui.styles import Stylesheets, Colors, Fonts, Spacing

class ResultCard(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.is_expanded = True
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(Stylesheets.CARD)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.header_frame = QFrame()
        self.header_frame.setStyleSheet(Stylesheets.CARD_HEADER)
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(16, 14, 16, 14)
        self.header_layout.setSpacing(12)

        self.expand_btn = QPushButton('▼')
        self.expand_btn.setFixedSize(28, 28)
        self.expand_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.ACCENT};
                border: none;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_LIGHT};
            }}
        """)
        self.expand_btn.clicked.connect(self.toggle_expand)

        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_CARD_TITLE};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.ACCENT};
            font-family: {Fonts.FAMILY_BOLD};
        """)

        self.header_layout.addWidget(self.expand_btn)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()

        self.main_layout.addWidget(self.header_frame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(16)

        self.main_layout.addWidget(self.content_widget)

        self.setLayout(self.main_layout)

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        self.expand_btn.setText('▶' if not self.is_expanded else '▼')

    def set_content(self, widget):
        self.content_layout.addWidget(widget)

class ResultPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(Stylesheets.SCROLL_AREA)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(20)

        self.bazi_card = ResultCard('四柱八字')
        self.wuxing_card = ResultCard('五行分布')
        self.shishen_card = ResultCard('十神分析')
        self.geju_card = ResultCard('命局格局')

        self.major_fortune_card = ResultCard('大运分析')
        self.annual_fortune_card = ResultCard('流年运势')
        self.monthly_fortune_card = ResultCard('流月运势')

        self.mingli_card = ResultCard('命理元素')
        self.ai_analysis_card = ResultCard('AI综合分析')

        self.init_bazi_content()
        self.init_wuxing_content()
        self.init_shishen_content()
        self.init_geju_content()
        self.init_major_fortune_content()
        self.init_annual_fortune_content()
        self.init_monthly_fortune_content()
        self.init_mingli_content()
        self.init_ai_analysis_content()

        self.scroll_layout.addWidget(self.bazi_card)
        self.scroll_layout.addWidget(self.wuxing_card)
        self.scroll_layout.addWidget(self.shishen_card)
        self.scroll_layout.addWidget(self.geju_card)
        self.scroll_layout.addWidget(self.major_fortune_card)
        self.scroll_layout.addWidget(self.annual_fortune_card)
        self.scroll_layout.addWidget(self.monthly_fortune_card)
        self.scroll_layout.addWidget(self.mingli_card)
        self.scroll_layout.addWidget(self.ai_analysis_card)

        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)

        self.layout.addWidget(self.scroll_area)

        self.setLayout(self.layout)

    def init_bazi_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)

        self.bazi_grid = QGridLayout()
        self.bazi_grid.setSpacing(16)

        pillars = ['年柱', '月柱', '日柱', '时柱']
        for i, pillar in enumerate(pillars):
            pillar_frame = QFrame()
            pillar_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND_SOFT};
                    border-radius: 8px;
                    padding: 16px;
                }}
            """)
            pillar_layout = QVBoxLayout(pillar_frame)
            pillar_layout.setSpacing(12)

            label = QLabel(pillar)
            label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_SMALL};
                color: {Colors.TEXT_SECONDARY};
                font-weight: {Fonts.WEIGHT_BOLD};
                font-family: {Fonts.FAMILY_BOLD};
            """)
            label.setAlignment(Qt.AlignCenter)

            ganzhi = QLabel('--')
            ganzhi.setStyleSheet(f"""
                font-size: 26px;
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.PRIMARY};
                font-family: {Fonts.FAMILY_BOLD};
            """)
            ganzhi.setAlignment(Qt.AlignCenter)

            pillar_layout.addWidget(label)
            pillar_layout.addWidget(ganzhi)
            self.bazi_grid.addWidget(pillar_frame, 0, i)

        content_layout.addLayout(self.bazi_grid)

        date_frame = QFrame()
        date_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_SOFT};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        date_layout = QVBoxLayout(date_frame)

        self.date_label = QLabel('')
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_PRIMARY};
            font-weight: {Fonts.WEIGHT_MEDIUM};
            line-height: 1.6;
        """)
        date_layout.addWidget(self.date_label)

        content_layout.addWidget(date_frame)

        self.bazi_card.set_content(content_widget)

    def init_wuxing_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)

        self.wuxing_grid = QGridLayout()
        self.wuxing_grid.setSpacing(16)

        elements = ['木', '火', '土', '金', '水']
        colors = {
            '木': '#2E7D32',
            '火': '#C62828',
            '土': '#E65100',
            '金': '#546E7A',
            '水': '#1565C0'
        }

        for i, element in enumerate(elements):
            element_frame = QFrame()
            element_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND_SOFT};
                    border-radius: 8px;
                    padding: 16px;
                }}
            """)
            element_layout = QVBoxLayout(element_frame)
            element_layout.setSpacing(12)

            label = QLabel(element)
            label.setStyleSheet(f"""
                font-size: 18px;
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {colors[element]};
                font-family: {Fonts.FAMILY_BOLD};
            """)
            label.setAlignment(Qt.AlignCenter)

            count = QLabel('--')
            count.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_PRIMARY};
                font-weight: {Fonts.WEIGHT_BOLD};
            """)
            count.setAlignment(Qt.AlignCenter)

            bar_container = QFrame()
            bar_container.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BORDER_LIGHT};
                    border-radius: 4px;
                }}
            """)
            bar_layout = QHBoxLayout(bar_container)
            bar_layout.setContentsMargins(2, 2, 2, 2)

            bar = QFrame()
            bar.setFixedHeight(12)
            bar.setStyleSheet(f"background-color: {colors[element]}; border-radius: 3px;")
            bar.setMaximumWidth(0)
            bar_layout.addWidget(bar)

            percentage = QLabel('--')
            percentage.setStyleSheet(f"""
                font-size: {Fonts.SIZE_SMALL};
                color: {Colors.TEXT_SECONDARY};
                font-weight: {Fonts.WEIGHT_MEDIUM};
            """)
            percentage.setAlignment(Qt.AlignCenter)

            element_layout.addWidget(label)
            element_layout.addWidget(count)
            element_layout.addWidget(bar_container)
            element_layout.addWidget(percentage)

            self.wuxing_grid.addWidget(element_frame, 0, i)

        content_layout.addLayout(self.wuxing_grid)

        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_SOFT};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        summary_layout = QVBoxLayout(summary_frame)

        self.wuxing_summary = QLabel('')
        self.wuxing_summary.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_PRIMARY};
            font-weight: {Fonts.WEIGHT_MEDIUM};
            line-height: 1.6;
        """)
        self.wuxing_summary.setWordWrap(True)
        self.wuxing_summary.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.wuxing_summary)

        content_layout.addWidget(summary_frame)

        self.wuxing_card.set_content(content_widget)

    def init_shishen_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)

        self.shishen_table = QTableWidget(4, 5)
        self.shishen_table.setHorizontalHeaderLabels(['柱位', '天干', '十神', '地支', '藏干十神'])
        self.shishen_table.verticalHeader().setVisible(False)
        self.shishen_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.shishen_table.setStyleSheet(Stylesheets.TABLE_WIDGET)
        self.shishen_table.setAlternatingRowColors(True)
        self.shishen_table.horizontalHeader().setStretchLastSection(True)
        self.shishen_table.verticalHeader().setDefaultSectionSize(44)
        self.shishen_table.horizontalHeader().setSectionsClickable(False)

        for i in range(4):
            for j in range(5):
                item = QTableWidgetItem('--')
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                self.shishen_table.setItem(i, j, item)

        content_layout.addWidget(self.shishen_table)

        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_SOFT};
                border-radius: 8px;
                padding: 14px 16px;
            }}
        """)
        summary_layout = QVBoxLayout(summary_frame)

        self.shishen_summary = QLabel('')
        self.shishen_summary.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_PRIMARY};
            line-height: 1.6;
        """)
        self.shishen_summary.setWordWrap(True)
        summary_layout.addWidget(self.shishen_summary)

        content_layout.addWidget(summary_frame)

        self.shishen_card.set_content(content_widget)

    def init_geju_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)

        geju_frame = QFrame()
        geju_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_SOFT};
                border-radius: 8px;
                padding: 20px;
            }}
        """)
        geju_layout = QVBoxLayout(geju_frame)

        self.geju_content = QLabel('请输入信息并点击排盘按钮')
        self.geju_content.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_PRIMARY};
            line-height: 1.8;
        """)
        self.geju_content.setWordWrap(True)

        geju_layout.addWidget(self.geju_content)

        content_layout.addWidget(geju_frame)

        self.geju_card.set_content(content_widget)

    def init_major_fortune_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)

        self.major_fortune_list = QListWidget()
        self.major_fortune_list.setStyleSheet(Stylesheets.LIST_WIDGET)

        content_layout.addWidget(self.major_fortune_list)
        self.major_fortune_card.set_content(content_widget)

    def init_annual_fortune_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)

        self.annual_fortune_list = QListWidget()
        self.annual_fortune_list.setStyleSheet(Stylesheets.LIST_WIDGET)

        content_layout.addWidget(self.annual_fortune_list)
        self.annual_fortune_card.set_content(content_widget)

    def init_monthly_fortune_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)

        self.monthly_fortune_grid = QGridLayout()
        self.monthly_fortune_grid.setSpacing(12)

        for i in range(3):
            for j in range(4):
                month_frame = QFrame()
                month_frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {Colors.BACKGROUND_SOFT};
                        border-radius: 8px;
                        padding: 14px;
                    }}
                """)
                month_layout = QVBoxLayout(month_frame)
                month_layout.setSpacing(8)

                month_label = QLabel('--')
                month_label.setStyleSheet(f"""
                    font-size: {Fonts.SIZE_BODY};
                    font-weight: {Fonts.WEIGHT_BOLD};
                    color: {Colors.PRIMARY};
                """)
                month_label.setAlignment(Qt.AlignCenter)

                ganzhi_label = QLabel('--')
                ganzhi_label.setStyleSheet(f"""
                    font-size: {Fonts.SIZE_SMALL};
                    color: {Colors.TEXT_SECONDARY};
                    font-weight: {Fonts.WEIGHT_MEDIUM};
                """)
                ganzhi_label.setAlignment(Qt.AlignCenter)

                month_layout.addWidget(month_label)
                month_layout.addWidget(ganzhi_label)
                self.monthly_fortune_grid.addWidget(month_frame, i, j)

        content_layout.addLayout(self.monthly_fortune_grid)
        self.monthly_fortune_card.set_content(content_widget)

    def init_mingli_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)

        sections = [
            ('藏干分析', 'hidden_stems'),
            ('纳音五行', 'nayin'),
            ('神煞', 'shensha'),
            ('主星', 'main_stars'),
            ('自坐分析', 'self_seat'),
            ('空亡', 'kongwang')
        ]

        self.mingli_labels = {}

        for section_name, key in sections:
            outer_frame = QFrame()
            outer_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND_SOFT};
                    border-radius: 8px;
                    padding: 16px;
                }}
            """)
            outer_layout = QVBoxLayout(outer_frame)
            outer_layout.setSpacing(12)

            inner_frame = QFrame()
            inner_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND_LIGHT};
                    border-radius: 6px;
                    padding: 14px;
                }}
            """)
            inner_layout = QVBoxLayout(inner_frame)
            inner_layout.setSpacing(10)

            section_title = QLabel(section_name)
            section_title.setStyleSheet(f"""
                font-size: {Fonts.SIZE_CARD_TITLE};
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.PRIMARY};
                font-family: {Fonts.FAMILY_BOLD};
            """)

            content_label = QLabel('')
            content_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_PRIMARY};
                line-height: 1.6;
            """)
            content_label.setWordWrap(True)

            inner_layout.addWidget(section_title)
            inner_layout.addWidget(content_label)

            outer_layout.addWidget(inner_frame)

            self.mingli_labels[key] = content_label
            content_layout.addWidget(outer_frame)

        self.mingli_card.set_content(content_widget)

    def init_ai_analysis_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)

        section_keys = ['overview', 'personality', 'life_trends', 'opportunities', 'challenges', 'compatibility', 'recommendations']
        section_labels = ['📋 综合概述', '😊 性格特征', '📈 人生趋势', '✨ 机遇分析', '⚠️ 挑战提示', '🔗 五行匹配', '💡 实用建议']

        self.ai_sections = {}

        for key, label in zip(section_keys, section_labels):
            section_frame = QFrame()
            section_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND_SOFT};
                    border-radius: 8px;
                    padding: 18px;
                }}
            """)
            section_layout = QVBoxLayout(section_frame)
            section_layout.setSpacing(10)

            title_label = QLabel(label)
            title_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_CARD_TITLE};
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.PRIMARY};
                font-family: {Fonts.FAMILY_BOLD};
            """)

            content_label = QLabel('--')
            content_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_PRIMARY};
                line-height: 1.8;
            """)
            content_label.setWordWrap(True)

            section_layout.addWidget(title_label)
            section_layout.addWidget(content_label)

            self.ai_sections[key] = content_label
            content_layout.addWidget(section_frame)

        self.ai_analysis_card.set_content(content_widget)

    def update_bazi(self, data):
        values = [data['year'], data['month'], data['day'], data['hour']]
        for i, value in enumerate(values):
            pillar_frame = self.bazi_grid.itemAtPosition(0, i).widget()
            ganzhi_label = pillar_frame.layout().itemAt(1).widget()
            ganzhi_label.setText(value)
        self.date_label.setText(f"公历：{data['solar_date']}\n农历：{data['lunar_date']}")

    def update_wuxing(self, data):
        elements = ['木', '火', '土', '金', '水']
        for i, element in enumerate(elements):
            element_frame = self.wuxing_grid.itemAtPosition(0, i).widget()
            count_label = element_frame.layout().itemAt(1).widget()
            count_label.setText(f"{data[element]['count']:.1f}")

            bar_container = element_frame.layout().itemAt(2).widget()
            bar = bar_container.layout().itemAt(0).widget()
            bar.setMaximumWidth(int(data[element]['percentage'] * 2))

            percentage_label = element_frame.layout().itemAt(3).widget()
            percentage_label.setText(f"{data[element]['percentage']}%")

        self.wuxing_summary.setText(f"五行分析：{data['summary']}")

    def update_shishen(self, data):
        for i, detail in enumerate(data['details']):
            self.shishen_table.item(i, 0).setText(detail['pillar'])
            self.shishen_table.item(i, 1).setText(detail['gan'])
            self.shishen_table.item(i, 2).setText(detail['gan_shishen'])
            self.shishen_table.item(i, 3).setText(detail['zhi'])
            self.shishen_table.item(i, 4).setText(' '.join(detail['zhi_shishens']))

        summary_text = f"日主：{data['rizhu']} ({data['rizhu_wuxing']})"
        if data['summary']:
            summary_text += "\n" + '，'.join([f"{k}：{v}个" for k, v in data['summary'].items()])
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

        geju_text = '日主：' + rizhu + '\n\n' + '\n'.join(['• ' + s for s in summary])
        self.geju_content.setText(geju_text)

    def update_major_fortune(self, data):
        self.major_fortune_list.clear()
        for period in data['periods'][:6]:
            text = f"第{period['period']}步大运：{period['ganzhi']}  ({period['start_age']}-{period['end_age']}岁，{period['start_year']}-{period['end_year']}年)"
            item = QListWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.major_fortune_list.addItem(item)

    def update_annual_fortune(self, data):
        self.annual_fortune_list.clear()
        for year in data['years']:
            text = f"{year['year']}年 {year['ganzhi']}  |  小运：{year['minor_fortune']}"
            item = QListWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.annual_fortune_list.addItem(item)

    def update_monthly_fortune(self, data):
        months = data['months']
        for i, month in enumerate(months):
            row = i // 4
            col = i % 4
            month_frame = self.monthly_fortune_grid.itemAtPosition(row, col).widget()
            month_label = month_frame.layout().itemAt(0).widget()
            ganzhi_label = month_frame.layout().itemAt(1).widget()

            month_label.setText(f"{month['month_name']}")
            ganzhi_label.setText(f"{month['ganzhi']}")

    def update_mingli(self, hidden_stems, nayin, shensha, main_stars, self_seat, kongwang):
        hidden_text = '\n'.join([item['description'] for item in hidden_stems['hidden_stems']])
        self.mingli_labels['hidden_stems'].setText(hidden_text if hidden_text else '暂无信息')

        nayin_text = '\n'.join([f"{v['pillar']}：{v['nayin']}（{v['element']}）" for v in nayin.values()])
        self.mingli_labels['nayin'].setText(nayin_text)

        positive = [f"{s['name']}（{s['location']}）" for s in shensha['positive']]
        negative = [f"{s['name']}（{s['location']}）" for s in shensha['negative']]
        shensha_text = f"吉神：{', '.join(positive) if positive else '无'}\n\n凶煞：{', '.join(negative) if negative else '无'}"
        self.mingli_labels['shensha'].setText(shensha_text)

        stars_text = '\n\n'.join([f"{s['name']}：{s['characteristics']}" for s in main_stars['stars']])
        self.mingli_labels['main_stars'].setText(stars_text if stars_text else '暂无信息')

        self.mingli_labels['self_seat'].setText(self_seat['description'])
        self.mingli_labels['kongwang'].setText(kongwang['description'])

    def update_ai_analysis(self, data):
        self.ai_sections['overview'].setText(data['overview'])
        self.ai_sections['personality'].setText('• ' + '\n• '.join(data['personality']))
        self.ai_sections['life_trends'].setText(data['life_trends'])
        self.ai_sections['opportunities'].setText('• ' + '\n• '.join(data['opportunities']))
        self.ai_sections['challenges'].setText('• ' + '\n• '.join(data['challenges']))
        self.ai_sections['compatibility'].setText(data['compatibility'])
        self.ai_sections['recommendations'].setText('• ' + '\n• '.join(data['recommendations']))

    def clear(self):
        self.geju_content.setText('请输入信息并点击排盘按钮')
        self.date_label.setText('')
        self.wuxing_summary.setText('')
        self.shishen_summary.setText('')

        for i in range(4):
            pillar_frame = self.bazi_grid.itemAtPosition(0, i).widget()
            ganzhi_label = pillar_frame.layout().itemAt(1).widget()
            ganzhi_label.setText('--')

        elements = ['木', '火', '土', '金', '水']
        for i, element in enumerate(elements):
            element_frame = self.wuxing_grid.itemAtPosition(0, i).widget()
            count_label = element_frame.layout().itemAt(1).widget()
            count_label.setText('--')
            bar_container = element_frame.layout().itemAt(2).widget()
            bar = bar_container.layout().itemAt(0).widget()
            bar.setMaximumWidth(0)
            percentage_label = element_frame.layout().itemAt(3).widget()
            percentage_label.setText('--')

        for i in range(4):
            for j in range(5):
                self.shishen_table.item(i, j).setText('--')

        self.major_fortune_list.clear()
        self.annual_fortune_list.clear()

        for i in range(3):
            for j in range(4):
                month_frame = self.monthly_fortune_grid.itemAtPosition(i, j).widget()
                month_label = month_frame.layout().itemAt(0).widget()
                ganzhi_label = month_frame.layout().itemAt(1).widget()
                month_label.setText('--')
                ganzhi_label.setText('--')

        for key in self.mingli_labels:
            self.mingli_labels[key].setText('')

        for key in self.ai_sections:
            self.ai_sections[key].setText('--')