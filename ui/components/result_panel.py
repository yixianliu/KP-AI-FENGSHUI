from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QFrame, QGridLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QApplication,
                             QScrollArea, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer
from ui.styles import Stylesheets, Colors, Fonts

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
        self.header_layout.setContentsMargins(12, 8, 12, 8)

        self.expand_btn = QPushButton('▼')
        self.expand_btn.setFixedSize(22, 22)
        self.expand_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.ACCENT};
                border: none;
                font-size: 12px;
            }}
        """)
        self.expand_btn.clicked.connect(self.toggle_expand)

        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet(Stylesheets.CARD_TITLE)

        self.header_layout.addWidget(self.expand_btn)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()

        self.main_layout.addWidget(self.header_frame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 12, 12, 12)

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
        self.scroll_layout.setSpacing(12)

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
        content_layout.setSpacing(10)

        self.bazi_grid = QGridLayout()
        self.bazi_grid.setSpacing(12)

        pillars = ['年柱', '月柱', '日柱', '时柱']
        for i, pillar in enumerate(pillars):
            label = QLabel(pillar)
            label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_SMALL};
                color: {Colors.TEXT_SECONDARY};
                font-weight: {Fonts.WEIGHT_BOLD};
            """)
            label.setAlignment(Qt.AlignCenter)
            self.bazi_grid.addWidget(label, 0, i)

            ganzhi = QLabel('--')
            ganzhi.setStyleSheet(f"""
                font-size: 22px;
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.PRIMARY};
                font-family: {Fonts.FAMILY_BOLD};
            """)
            ganzhi.setAlignment(Qt.AlignCenter)
            self.bazi_grid.addWidget(ganzhi, 1, i)

        content_layout.addLayout(self.bazi_grid)

        self.date_label = QLabel('')
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.TEXT_SECONDARY};
        """)
        content_layout.addWidget(self.date_label)

        self.bazi_card.set_content(content_widget)

    def init_wuxing_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)

        self.wuxing_grid = QGridLayout()
        self.wuxing_grid.setSpacing(10)

        elements = ['木', '火', '土', '金', '水']
        colors = {'木': '#228B22', '火': '#DC143C', '土': '#D2691E', '金': '#708090', '水': '#1E90FF'}

        for i, element in enumerate(elements):
            label = QLabel(element)
            label.setStyleSheet(f"""
                font-size: 16px;
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {colors[element]};
            """)
            label.setAlignment(Qt.AlignCenter)
            self.wuxing_grid.addWidget(label, 0, i)

            count = QLabel('--')
            count.setStyleSheet(f"""
                font-size: 12px;
                color: {Colors.PRIMARY};
                font-weight: {Fonts.WEIGHT_BOLD};
            """)
            count.setAlignment(Qt.AlignCenter)
            self.wuxing_grid.addWidget(count, 1, i)

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
            bar.setFixedHeight(10)
            bar.setStyleSheet(f"background-color: {colors[element]}; border-radius: 3px;")
            bar.setMaximumWidth(0)
            bar_layout.addWidget(bar)

            self.wuxing_grid.addWidget(bar_container, 2, i)

            percentage = QLabel('--')
            percentage.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_SECONDARY};")
            percentage.setAlignment(Qt.AlignCenter)
            self.wuxing_grid.addWidget(percentage, 3, i)

        content_layout.addLayout(self.wuxing_grid)

        self.wuxing_summary = QLabel('')
        self.wuxing_summary.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.PRIMARY};
            font-weight: {Fonts.WEIGHT_BOLD};
            text-align: center;
            padding-top: 5px;
            border-top: 1px dashed {Colors.BORDER};
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
        self.shishen_table.setStyleSheet(Stylesheets.TABLE_WIDGET)

        for i in range(4):
            for j in range(5):
                item = QTableWidgetItem('--')
                item.setTextAlignment(Qt.AlignCenter)
                self.shishen_table.setItem(i, j, item)

        content_layout.addWidget(self.shishen_table)

        self.shishen_summary = QLabel('')
        self.shishen_summary.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.PRIMARY};
            padding-top: 8px;
            border-top: 1px dashed {Colors.BORDER};
        """)
        content_layout.addWidget(self.shishen_summary)

        self.shishen_card.set_content(content_widget)

    def init_geju_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        self.geju_content = QLabel('请输入信息并点击排盘按钮')
        self.geju_content.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_PRIMARY};
            line-height: 1.5;
        """)
        self.geju_content.setWordWrap(True)

        geju_frame = QFrame()
        geju_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BORDER_LIGHT};
                border-radius: 4px;
                padding: 10px;
            }}
        """)
        geju_layout = QVBoxLayout(geju_frame)
        geju_layout.addWidget(self.geju_content)

        content_layout.addWidget(geju_frame)

        self.geju_card.set_content(content_widget)

    def init_major_fortune_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        self.major_fortune_list = QListWidget()
        self.major_fortune_list.setStyleSheet(Stylesheets.LIST_WIDGET)

        content_layout.addWidget(self.major_fortune_list)
        self.major_fortune_card.set_content(content_widget)

    def init_annual_fortune_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        self.annual_fortune_list = QListWidget()
        self.annual_fortune_list.setStyleSheet(Stylesheets.LIST_WIDGET)

        content_layout.addWidget(self.annual_fortune_list)
        self.annual_fortune_card.set_content(content_widget)

    def init_monthly_fortune_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        self.monthly_fortune_grid = QGridLayout()
        self.monthly_fortune_grid.setSpacing(8)

        for i in range(3):
            for j in range(4):
                month_frame = QFrame()
                month_frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {Colors.BORDER_LIGHT};
                        border-radius: 4px;
                        padding: 8px;
                    }}
                """)
                month_layout = QVBoxLayout(month_frame)

                month_label = QLabel('--')
                month_label.setStyleSheet(f"""
                    font-size: {Fonts.SIZE_BODY};
                    font-weight: {Fonts.WEIGHT_BOLD};
                    color: {Colors.PRIMARY};
                """)
                month_label.setAlignment(Qt.AlignCenter)

                ganzhi_label = QLabel('--')
                ganzhi_label.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_SECONDARY};")
                ganzhi_label.setAlignment(Qt.AlignCenter)

                month_layout.addWidget(month_label)
                month_layout.addWidget(ganzhi_label)
                self.monthly_fortune_grid.addWidget(month_frame, i, j)

        content_layout.addLayout(self.monthly_fortune_grid)
        self.monthly_fortune_card.set_content(content_widget)

    def init_mingli_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)

        self.mingli_tabs = QFrame()
        self.mingli_tabs.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BORDER_LIGHT};
                border-radius: 4px;
                padding: 10px;
            }}
        """)
        self.mingli_layout = QVBoxLayout(self.mingli_tabs)
        self.mingli_layout.setSpacing(8)

        self.hidden_stems_label = QLabel('')
        self.hidden_stems_label.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY};")
        self.hidden_stems_label.setWordWrap(True)
        self.mingli_layout.addWidget(self.hidden_stems_label)

        self.nayin_label = QLabel('')
        self.nayin_label.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY};")
        self.nayin_label.setWordWrap(True)
        self.mingli_layout.addWidget(self.nayin_label)

        self.shensha_label = QLabel('')
        self.shensha_label.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY};")
        self.shensha_label.setWordWrap(True)
        self.mingli_layout.addWidget(self.shensha_label)

        self.main_stars_label = QLabel('')
        self.main_stars_label.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY};")
        self.main_stars_label.setWordWrap(True)
        self.mingli_layout.addWidget(self.main_stars_label)

        self.self_seat_label = QLabel('')
        self.self_seat_label.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY};")
        self.self_seat_label.setWordWrap(True)
        self.mingli_layout.addWidget(self.self_seat_label)

        self.kongwang_label = QLabel('')
        self.kongwang_label.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY};")
        self.kongwang_label.setWordWrap(True)
        self.mingli_layout.addWidget(self.kongwang_label)

        content_layout.addWidget(self.mingli_tabs)
        self.mingli_card.set_content(content_widget)

    def init_ai_analysis_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)

        sections = ['overview', 'personality', 'life_trends', 'opportunities', 'challenges', 'compatibility', 'recommendations']
        labels = ['综合概述', '性格特征', '人生趋势', '机遇分析', '挑战提示', '五行匹配', '实用建议']

        self.ai_sections = {}

        for key, label in zip(sections, labels):
            section_frame = QFrame()
            section_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BORDER_LIGHT};
                    border-radius: 4px;
                    padding: 10px;
                }}
            """)
            section_layout = QVBoxLayout(section_frame)

            title_label = QLabel(label)
            title_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_CARD_TITLE};
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.PRIMARY};
                margin-bottom: 5px;
            """)

            content_label = QLabel('--')
            content_label.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY}; line-height: 1.5;")
            content_label.setWordWrap(True)

            section_layout.addWidget(title_label)
            section_layout.addWidget(content_label)

            self.ai_sections[key] = content_label
            content_layout.addWidget(section_frame)

        self.ai_analysis_card.set_content(content_widget)

    def update_bazi(self, data):
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
            bar.setMaximumWidth(int(data[element]['percentage'] * 1.5))

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

    def update_major_fortune(self, data):
        self.major_fortune_list.clear()
        for period in data['periods'][:6]:
            text = f"第{period['period']}步大运: {period['ganzhi']} "
            text += f"({period['start_age']}-{period['end_age']}岁, {period['start_year']}-{period['end_year']}年)"
            item = QListWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.major_fortune_list.addItem(item)

    def update_annual_fortune(self, data):
        self.annual_fortune_list.clear()
        for year in data['years']:
            text = f"{year['year']}年 {year['ganzhi']} | 小运: {year['minor_fortune']}"
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
        self.hidden_stems_label.setText(f"藏干分析:\n{hidden_text}" if hidden_text else "藏干分析: 无")

        nayin_text = '\n'.join([f"{v['pillar']}: {v['nayin']}({v['element']})" for v in nayin.values()])
        self.nayin_label.setText(f"纳音五行:\n{nayin_text}")

        positive = [f"{s['name']}({s['location']})" for s in shensha['positive']]
        negative = [f"{s['name']}({s['location']})" for s in shensha['negative']]
        shensha_text = f"吉神: {', '.join(positive) if positive else '无'}\n"
        shensha_text += f"凶煞: {', '.join(negative) if negative else '无'}"
        self.shensha_label.setText(f"神煞:\n{shensha_text}")

        stars_text = '\n'.join([f"{s['name']}: {s['characteristics']}" for s in main_stars['stars']])
        self.main_stars_label.setText(f"主星:\n{stars_text}" if stars_text else "主星: 无")

        self.self_seat_label.setText(f"自坐分析: {self_seat['description']}")
        self.kongwang_label.setText(f"空亡: {kongwang['description']}")

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

        self.major_fortune_list.clear()
        self.annual_fortune_list.clear()

        self.hidden_stems_label.setText('')
        self.nayin_label.setText('')
        self.shensha_label.setText('')
        self.main_stars_label.setText('')
        self.self_seat_label.setText('')
        self.kongwang_label.setText('')

        for key in self.ai_sections:
            self.ai_sections[key].setText('--')