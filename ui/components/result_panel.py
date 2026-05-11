from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QPushButton, QScrollArea, QHeaderView)
from PyQt5.QtCore import Qt
from ui.styles import Stylesheets, Colors, Fonts, Spacing

class ResultCard(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()
    
    def init_ui(self):
        self.setStyleSheet(Stylesheets.CARD)
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet(Stylesheets.COLLAPSE_HEADER)
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(int(Spacing.CARD_PADDING.replace('px', '')), 12, int(Spacing.CARD_PADDING.replace('px', '')), 12)
        self.header_layout.setSpacing(10)
        
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet(Stylesheets.CARD_TITLE)
        
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        
        self.main_layout.addWidget(self.header_frame)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(int(Spacing.CARD_PADDING.replace('px', '')), int(Spacing.CARD_PADDING.replace('px', '')), int(Spacing.CARD_PADDING.replace('px', '')), int(Spacing.CARD_PADDING.replace('px', '')))
        self.content_layout.setSpacing(14)
        
        self.main_layout.addWidget(self.content_widget)
        
        self.setLayout(self.main_layout)
    
    def set_content(self, widget):
        self.content_layout.addWidget(widget)

class BasicInfoCard(ResultCard):
    def __init__(self, parent=None):
        super().__init__('命主基础信息', parent)
        self.init_content()
    
    def init_content(self):
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(24)
        content_layout.addStretch()
        
        left_layout = QVBoxLayout()
        left_layout.setSpacing(6)
        
        self.gender_label = QLabel('')
        self.gender_label.setStyleSheet(Stylesheets.LABEL_KEY)
        
        self.solar_date_label = QLabel('')
        self.solar_date_label.setStyleSheet(Stylesheets.LABEL_SMALL)
        
        left_layout.addWidget(self.gender_label)
        left_layout.addWidget(self.solar_date_label)
        
        right_layout = QVBoxLayout()
        right_layout.setSpacing(6)
        
        self.lunar_date_label = QLabel('')
        self.lunar_date_label.setStyleSheet(Stylesheets.LABEL_SMALL)
        
        self.solar_time_label = QLabel('')
        self.solar_time_label.setStyleSheet(Stylesheets.LABEL_SMALL)
        
        right_layout.addWidget(self.lunar_date_label)
        right_layout.addWidget(self.solar_time_label)
        
        content_layout.addLayout(left_layout)
        content_layout.addLayout(right_layout)
        content_layout.addStretch()
        
        self.set_content(content_widget)
        
        self._set_initial_state()
    
    def _set_initial_state(self):
        self.gender_label.setText('请输入信息进行排盘')
        self.solar_date_label.setText('公历：')
        self.lunar_date_label.setText('农历：')
        self.solar_time_label.setText('真太阳时：未校正')
    
    def update_info(self, bazhi_data, input_data):
        if not input_data or not bazhi_data:
            self._set_initial_state()
            return
        
        gender_text = '乾造（男）' if input_data.get('gender', '') == '男' else '坤造（女）'
        self.gender_label.setText(gender_text)
        self.solar_date_label.setText(f'公历：{bazhi_data.get("solar_date", "")}')
        self.lunar_date_label.setText(f'农历：{bazhi_data.get("lunar_date", "")}')
        self.solar_time_label.setText(f'真太阳时：{bazhi_data.get("solar_time", "未校正")}')

class BaziCard(ResultCard):
    def __init__(self, parent=None):
        super().__init__('四柱核心排盘', parent)
        self.init_content()
    
    def init_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        
        pillars_grid = QGridLayout()
        pillars_grid.setSpacing(10)
        
        self.pillar_widgets = []
        pillar_names = ['年柱', '月柱', '日柱', '时柱']
        
        for i, name in enumerate(pillar_names):
            is_rizhu = (i == 2)
            pillar_frame = QFrame()
            pillar_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {'rgba(42, 74, 63, 0.08)' if is_rizhu else '{Colors.BACKGROUND}'};
                    border-radius: {Spacing.CONTROL_RADIUS};
                    padding: 14px 12px;
                    border: 1px solid {Colors.BORDER};
                }}
            """)
            pillar_layout = QVBoxLayout(pillar_frame)
            pillar_layout.setSpacing(8)
            pillar_layout.setAlignment(Qt.AlignCenter)
            
            name_label = QLabel(name)
            name_label.setStyleSheet(Stylesheets.LABEL_SMALL)
            name_label.setAlignment(Qt.AlignCenter)
            
            ganzhi_label = QLabel('--')
            ganzhi_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_KEY};
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.TEXT_PRIMARY};
                font-family: {Fonts.FAMILY_CN};
            """)
            ganzhi_label.setAlignment(Qt.AlignCenter)
            
            shishen_label = QLabel('--')
            shishen_label.setStyleSheet(Stylesheets.LABEL_ACCENT)
            shishen_label.setAlignment(Qt.AlignCenter)
            
            canggan_label = QLabel('--')
            canggan_label.setStyleSheet(Stylesheets.LABEL_SMALL)
            canggan_label.setAlignment(Qt.AlignCenter)
            
            wuxing_label = QLabel('--')
            wuxing_label.setStyleSheet(Stylesheets.LABEL_SMALL)
            wuxing_label.setAlignment(Qt.AlignCenter)
            
            pillar_layout.addWidget(name_label)
            pillar_layout.addWidget(ganzhi_label)
            pillar_layout.addWidget(shishen_label)
            pillar_layout.addWidget(canggan_label)
            pillar_layout.addWidget(wuxing_label)
            
            pillars_grid.addWidget(pillar_frame, 0, i)
            self.pillar_widgets.append((ganzhi_label, shishen_label, canggan_label, wuxing_label))
        
        content_layout.addLayout(pillars_grid)
        
        rizhu_hint = QLabel('注：日柱为日主，代表命主本人')
        rizhu_hint.setStyleSheet(Stylesheets.LABEL_SMALL)
        rizhu_hint.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(rizhu_hint)
        
        self.set_content(content_widget)
    
    def update_bazi(self, bazhi_data, shishen_data):
        if not bazhi_data:
            for widgets in self.pillar_widgets:
                for widget in widgets:
                    widget.setText('--')
            return
        
        pillars = [bazhi_data.get('year', '--'), bazhi_data.get('month', '--'), 
                   bazhi_data.get('day', '--'), bazhi_data.get('hour', '--')]
        
        for i, pillar in enumerate(pillars):
            ganzhi_label, shishen_label, canggan_label, wuxing_label = self.pillar_widgets[i]
            ganzhi_label.setText(pillar)
            
            if shishen_data and 'details' in shishen_data and i < len(shishen_data['details']):
                detail = shishen_data['details'][i]
                shishen_label.setText(detail.get('gan_shishen', '--'))
                canggan_label.setText('藏干：' + ' '.join(detail.get('zhi_shishens', [])))
                
                gan = pillar[0] if len(pillar) > 0 else ''
                zhi = pillar[1] if len(pillar) > 1 else ''
                wuxing_map = {
                    '甲': '木', '乙': '木', '丙': '火', '丁': '火',
                    '戊': '土', '己': '土', '庚': '金', '辛': '金',
                    '壬': '水', '癸': '水',
                    '子': '水', '丑': '土', '寅': '木', '卯': '木',
                    '辰': '土', '巳': '火', '午': '火', '未': '土',
                    '申': '金', '酉': '金', '戌': '土', '亥': '水'
                }
                gan_wuxing = wuxing_map.get(gan, '')
                zhi_wuxing = wuxing_map.get(zhi, '')
                wuxing_label.setText(f'五行：{gan_wuxing} + {zhi_wuxing}')
            else:
                shishen_label.setText('--')
                canggan_label.setText('--')
                wuxing_label.setText('--')

class WuxingCard(ResultCard):
    def __init__(self, parent=None):
        super().__init__('五行格局分析', parent)
        self.init_content()
    
    def init_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        
        wuxing_grid = QGridLayout()
        wuxing_grid.setSpacing(10)
        
        elements = ['木', '火', '土', '金', '水']
        self.wuxing_widgets = []
        
        for i, element in enumerate(elements):
            element_frame = QFrame()
            element_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND};
                    border-radius: {Spacing.CONTROL_RADIUS};
                    padding: 12px;
                    border: 1px solid {Colors.BORDER};
                }}
            """)
            element_layout = QVBoxLayout(element_frame)
            element_layout.setSpacing(6)
            element_layout.setAlignment(Qt.AlignCenter)
            
            name_label = QLabel(element)
            name_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_KEY};
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.TEXT_PRIMARY};
                font-family: {Fonts.FAMILY_CN};
            """)
            name_label.setAlignment(Qt.AlignCenter)
            
            count_label = QLabel('--')
            count_label.setStyleSheet(Stylesheets.LABEL_BODY)
            count_label.setAlignment(Qt.AlignCenter)
            
            percent_label = QLabel('--')
            percent_label.setStyleSheet(Stylesheets.LABEL_SMALL)
            percent_label.setAlignment(Qt.AlignCenter)
            
            element_layout.addWidget(name_label)
            element_layout.addWidget(count_label)
            element_layout.addWidget(percent_label)
            
            wuxing_grid.addWidget(element_frame, 0, i)
            self.wuxing_widgets.append((count_label, percent_label))
        
        content_layout.addLayout(wuxing_grid)
        
        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 14px;
                border: 1px solid {Colors.BORDER};
            }}
        """)
        summary_layout = QVBoxLayout(summary_frame)
        
        self.wuxing_summary = QLabel('')
        self.wuxing_summary.setStyleSheet(Stylesheets.LABEL_BODY)
        self.wuxing_summary.setWordWrap(True)
        summary_layout.addWidget(self.wuxing_summary)
        
        content_layout.addWidget(summary_frame)
        
        self.set_content(content_widget)
        
        self._set_initial_state()
    
    def _set_initial_state(self):
        self.wuxing_summary.setText('请输入信息进行排盘，五行分析结果将在此显示')
    
    def update_wuxing(self, wuxing_data):
        if not wuxing_data:
            for count_label, percent_label in self.wuxing_widgets:
                count_label.setText('--')
                percent_label.setText('--')
            self._set_initial_state()
            return
        
        elements = ['木', '火', '土', '金', '水']
        
        for i, element in enumerate(elements):
            count_label, percent_label = self.wuxing_widgets[i]
            count_label.setText(f'{wuxing_data.get(element, {}).get("count", 0):.1f}')
            percent_label.setText(f'{wuxing_data.get(element, {}).get("percentage", 0)}%')
        
        summary_text = ''
        if 'summary' in wuxing_data:
            summary_text += wuxing_data['summary'] + '\n\n'
        if 'rizhu_wuxing' in wuxing_data:
            summary_text += f'日主五行：{wuxing_data["rizhu_wuxing"]}\n'
        if 'strength' in wuxing_data:
            summary_text += f'日主强弱：{wuxing_data["strength"]}\n'
        if 'ying_shen' in wuxing_data and wuxing_data['ying_shen']:
            summary_text += f'<span style="color: {Colors.ACCENT}; font-weight: bold;">喜用神：{wuxing_data["ying_shen"]}</span>\n'
        if 'ji_shen' in wuxing_data and wuxing_data['ji_shen']:
            summary_text += f'<span style="color: {Colors.WARNING}; font-weight: bold;">忌神：{wuxing_data["ji_shen"]}</span>'
        
        self.wuxing_summary.setText(summary_text)

class FortuneCard(ResultCard):
    def __init__(self, parent=None):
        super().__init__('大运流年', parent)
        self.init_content()
    
    def init_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(14)
        
        self.fortune_table = QTableWidget(0, 5)
        self.fortune_table.setHorizontalHeaderLabels(['大运', '年龄', '干支', '十神', '运势简述'])
        self.fortune_table.verticalHeader().setVisible(False)
        self.fortune_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.fortune_table.setStyleSheet(Stylesheets.TABLE_WIDGET)
        self.fortune_table.setAlternatingRowColors(False)
        self.fortune_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        
        header = self.fortune_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.resizeSection(0, 55)
        header.resizeSection(1, 70)
        header.resizeSection(2, 70)
        header.resizeSection(3, 70)
        
        self.fortune_table.setMinimumHeight(200)
        
        content_layout.addWidget(self.fortune_table)
        
        initial_hint = QLabel('请输入信息进行排盘，大运流年信息将在此显示')
        initial_hint.setStyleSheet(Stylesheets.LABEL_SMALL)
        initial_hint.setAlignment(Qt.AlignCenter)
        self.initial_hint = initial_hint
        
        content_layout.addWidget(initial_hint)
        
        self.set_content(content_widget)
    
    def update_fortune(self, major_fortune_data):
        self.fortune_table.setRowCount(0)
        
        if not major_fortune_data or 'periods' not in major_fortune_data:
            self.initial_hint.setVisible(True)
            return
        
        self.initial_hint.setVisible(False)
        
        for i, period in enumerate(major_fortune_data['periods'][:8]):
            self.fortune_table.insertRow(i)
            
            item0 = QTableWidgetItem(f'第{period.get("period", "")}步')
            item0.setTextAlignment(Qt.AlignCenter)
            self.fortune_table.setItem(i, 0, item0)
            
            item1 = QTableWidgetItem(f'{period.get("start_age", "")}-{period.get("end_age", "")}岁')
            item1.setTextAlignment(Qt.AlignCenter)
            self.fortune_table.setItem(i, 1, item1)
            
            item2 = QTableWidgetItem(period.get('ganzhi', ''))
            item2.setTextAlignment(Qt.AlignCenter)
            self.fortune_table.setItem(i, 2, item2)
            
            item3 = QTableWidgetItem(period.get('shishen', ''))
            item3.setTextAlignment(Qt.AlignCenter)
            self.fortune_table.setItem(i, 3, item3)
            
            item4 = QTableWidgetItem(period.get('description', ''))
            item4.setTextAlignment(Qt.AlignLeft)
            item4.setToolTip(period.get('description', ''))
            self.fortune_table.setItem(i, 4, item4)

class AIAnalysisCard(ResultCard):
    def __init__(self, parent=None):
        super().__init__('AI智能解析', parent)
        self.init_content()
    
    def init_content(self):
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(14)
        
        sections = [
            ('性格特质', 'personality'),
            ('事业财运', 'career'),
            ('婚姻感情', 'marriage'),
            ('健康注意', 'health'),
            ('综合建议', 'suggestions')
        ]
        
        self.section_labels = {}
        
        for title, key in sections:
            section_frame = QFrame()
            section_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND};
                    border-radius: {Spacing.CONTROL_RADIUS};
                    padding: 12px;
                    border: 1px solid {Colors.BORDER};
                }}
            """)
            section_layout = QVBoxLayout(section_frame)
            section_layout.setSpacing(6)
            
            title_label = QLabel(title)
            title_label.setStyleSheet(Stylesheets.CARD_TITLE_ACCENT)
            
            content_label = QLabel('')
            content_label.setStyleSheet(Stylesheets.LABEL_BODY)
            content_label.setWordWrap(True)
            content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            
            section_layout.addWidget(title_label)
            section_layout.addWidget(content_label)
            
            self.section_labels[key] = content_label
            content_layout.addWidget(section_frame)
        
        self.set_content(content_widget)
        
        self._set_initial_state()
    
    def _set_initial_state(self):
        for key in self.section_labels:
            self.section_labels[key].setText('请输入信息进行排盘')
    
    def update_analysis(self, ai_data):
        if not ai_data:
            self._set_initial_state()
            return
        
        self.section_labels['personality'].setText(self._format_content(ai_data.get('personality', [])))
        self.section_labels['career'].setText(self._format_content(ai_data.get('career', [])))
        self.section_labels['marriage'].setText(self._format_content(ai_data.get('marriage', [])))
        self.section_labels['health'].setText(self._format_content(ai_data.get('health', [])))
        self.section_labels['suggestions'].setText(self._format_content(ai_data.get('suggestions', [])))
    
    def _format_content(self, content_list):
        if isinstance(content_list, list):
            if len(content_list) == 0:
                return '暂无内容'
            return '\n'.join([f'• {item}' for item in content_list])
        elif isinstance(content_list, str):
            return content_list
        else:
            return '暂无内容'

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
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        module_gap = int(Spacing.MODULE_GAP.replace('px', ''))
        self.scroll_layout.setContentsMargins(module_gap, module_gap, module_gap, module_gap)
        self.scroll_layout.setSpacing(module_gap)
        
        self.basic_info_card = BasicInfoCard()
        self.scroll_layout.addWidget(self.basic_info_card)
        
        self.bazi_card = BaziCard()
        self.scroll_layout.addWidget(self.bazi_card)
        
        self.wuxing_card = WuxingCard()
        self.scroll_layout.addWidget(self.wuxing_card)
        
        self.fortune_card = FortuneCard()
        self.scroll_layout.addWidget(self.fortune_card)
        
        self.ai_analysis_card = AIAnalysisCard()
        self.scroll_layout.addWidget(self.ai_analysis_card)
        
        self.scroll_layout.addStretch(1)
        
        self.scroll_area.setWidget(self.scroll_content)
        
        self.layout.addWidget(self.scroll_area)
        
        self.setLayout(self.layout)
    
    def update_basic_info(self, bazhi_data, input_data):
        self.basic_info_card.update_info(bazhi_data, input_data)
    
    def update_bazi(self, bazhi_data, shishen_data):
        self.bazi_card.update_bazi(bazhi_data, shishen_data)
    
    def update_wuxing(self, wuxing_data):
        self.wuxing_card.update_wuxing(wuxing_data)
    
    def update_fortune(self, fortune_data):
        self.fortune_card.update_fortune(fortune_data)
    
    def update_ai_analysis(self, ai_data):
        self.ai_analysis_card.update_analysis(ai_data)
    
    def clear(self):
        self.basic_info_card.update_info({}, {})
        self.bazi_card.update_bazi({}, {})
        self.wuxing_card.update_wuxing({})
        self.fortune_card.update_fortune({})
        self.ai_analysis_card.update_analysis({})
