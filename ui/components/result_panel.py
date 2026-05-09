from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QFrame, QGridLayout)
from PyQt5.QtCore import Qt

class ResultPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        self.bazi_widget = self.create_bazi_section()
        self.wuxing_widget = self.create_wuxing_section()
        self.shishen_widget = self.create_shishen_section()
        self格局_widget = self.create_geju_section()
        
        self.layout.addWidget(self.bazi_widget)
        self.layout.addWidget(self.wuxing_widget)
        self.layout.addWidget(self.shishen_widget)
        self.layout.addWidget(self格局_widget)
        
        self.setLayout(self.layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #FFF8E7;
                border-radius: 10px;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            .title_label {
                font-size: 16px;
                font-weight: bold;
                color: #5D4037;
            }
            .ganzhi_label {
                font-size: 24px;
                font-weight: bold;
                color: #5D4037;
            }
            .pillar_label {
                font-size: 14px;
                color: #8B7355;
            }
            QFrame {
                background-color: white;
                border: 1px solid #D4AF37;
                border-radius: 8px;
            }
        """)
    
    def create_bazi_section(self):
        widget = QFrame()
        layout = QVBoxLayout()
        
        title = QLabel('四柱八字')
        title.setObjectName('title_label')
        layout.addWidget(title)
        
        self.bazi_grid = QGridLayout()
        self.bazi_grid.setSpacing(10)
        
        pillars = ['年柱', '月柱', '日柱', '时柱']
        for i, pillar in enumerate(pillars):
            label = QLabel(pillar)
            label.setObjectName('pillar_label')
            self.bazi_grid.addWidget(label, 0, i)
            
            ganzhi = QLabel('--')
            ganzhi.setObjectName('ganzhi_label')
            ganzhi.setAlignment(Qt.AlignCenter)
            self.bazi_grid.addWidget(ganzhi, 1, i)
        
        layout.addLayout(self.bazi_grid)
        
        self.date_label = QLabel('')
        layout.addWidget(self.date_label)
        
        widget.setLayout(layout)
        return widget
    
    def create_wuxing_section(self):
        widget = QFrame()
        layout = QVBoxLayout()
        
        title = QLabel('五行分布')
        title.setObjectName('title_label')
        layout.addWidget(title)
        
        self.wuxing_grid = QGridLayout()
        self.wuxing_grid.setSpacing(15)
        
        elements = ['木', '火', '土', '金', '水']
        for i, element in enumerate(elements):
            label = QLabel(element)
            label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.get_wuxing_color(element)};")
            self.wuxing_grid.addWidget(label, 0, i)
            
            count = QLabel('--')
            count.setAlignment(Qt.AlignCenter)
            self.wuxing_grid.addWidget(count, 1, i)
            
            bar = QFrame()
            bar.setFixedHeight(20)
            bar.setStyleSheet(f"background-color: {self.get_wuxing_color(element)}; border-radius: 10px;")
            bar.setMaximumWidth(0)
            self.wuxing_grid.addWidget(bar, 2, i)
        
        self.wuxing_summary = QLabel('')
        layout.addWidget(self.wuxing_summary)
        
        layout.addLayout(self.wuxing_grid)
        widget.setLayout(layout)
        return widget
    
    def create_shishen_section(self):
        widget = QFrame()
        layout = QVBoxLayout()
        
        title = QLabel('十神分析')
        title.setObjectName('title_label')
        layout.addWidget(title)
        
        self.shishen_table = QGridLayout()
        self.shishen_table.setSpacing(10)
        
        headers = ['柱位', '天干', '十神', '地支', '藏干十神']
        for i, header in enumerate(headers):
            label = QLabel(header)
            label.setStyleSheet("font-weight: bold; color: #5D4037;")
            self.shishen_table.addWidget(label, 0, i)
        
        for i in range(4):
            for j in range(5):
                label = QLabel('--')
                self.shishen_table.addWidget(label, i+1, j)
        
        layout.addLayout(self.shishen_table)
        
        self.shishen_summary = QLabel('')
        layout.addWidget(self.shishen_summary)
        
        widget.setLayout(layout)
        return widget
    
    def create_geju_section(self):
        widget = QFrame()
        layout = QVBoxLayout()
        
        title = QLabel('命局格局')
        title.setObjectName('title_label')
        layout.addWidget(title)
        
        self.geju_content = QLabel('请输入信息并点击排盘按钮')
        self.geju_content.setWordWrap(True)
        layout.addWidget(self.geju_content)
        
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
            
            bar = self.wuxing_grid.itemAtPosition(2, i).widget()
            bar.setMaximumWidth(int(data[element]['percentage'] * 3))
            bar.setStyleSheet(f"background-color: {self.get_wuxing_color(element)}; border-radius: 10px;")
        
        self.wuxing_summary.setText(f"五行分析: {data['summary']}")
    
    def update_shishen(self, data):
        for i, detail in enumerate(data['details']):
            row = i + 1
            self.shishen_table.itemAtPosition(row, 0).widget().setText(detail['pillar'])
            self.shishen_table.itemAtPosition(row, 1).widget().setText(detail['gan'])
            self.shishen_table.itemAtPosition(row, 2).widget().setText(detail['gan_shishen'])
            self.shishen_table.itemAtPosition(row, 3).widget().setText(detail['zhi'])
            self.shishen_table.itemAtPosition(row, 4).widget().setText(' '.join(detail['zhi_shishens']))
        
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
        
        self.geju_content.setText('；'.join(summary))
    
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
            
            bar = self.wuxing_grid.itemAtPosition(2, i).widget()
            bar.setMaximumWidth(0)
        
        for i in range(4):
            for j in range(5):
                self.shishen_table.itemAtPosition(i+1, j).widget().setText('--')