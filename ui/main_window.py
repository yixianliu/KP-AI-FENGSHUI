from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QLabel, QSplitter)
from PyQt5.QtCore import Qt
from ui.components.input_panel import InputPanel
from ui.components.result_panel import ResultPanel
from core.baazi import BaZiCalculator
from core.wuxing import WuXingAnalyzer
from core.shishen import ShiShenAnalyzer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_analyzers()
    
    def init_ui(self):
        self.setWindowTitle('八字排盘')
        self.setGeometry(100, 100, 900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        header = QLabel('八字排盘')
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #5D4037;
            padding: 15px;
            text-align: center;
        """)
        main_layout.addWidget(header)
        
        splitter = QSplitter(Qt.Horizontal)
        
        self.input_panel = InputPanel()
        self.input_panel.submit_btn.clicked.connect(self.on_calculate)
        splitter.addWidget(self.input_panel)
        self.input_panel.setFixedWidth(300)
        
        self.result_panel = ResultPanel()
        splitter.addWidget(self.result_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5E6D3;
            }
            QSplitter::handle {
                background-color: #D4AF37;
                width: 2px;
            }
        """)
    
    def init_analyzers(self):
        self.baazi_calculator = BaZiCalculator()
        self.wuxing_analyzer = WuXingAnalyzer()
        self.shishen_analyzer = ShiShenAnalyzer()
    
    def on_calculate(self):
        data = self.input_panel.get_data()
        
        try:
            bazhi = self.baazi_calculator.calculate(
                data['year'],
                data['month'],
                data['day'],
                data['hour'],
                data['is_lunar']
            )
            
            wuxing_result = self.wuxing_analyzer.analyze(bazhi)
            shishen_result = self.shishen_analyzer.analyze(bazhi)
            
            self.result_panel.update_bazi(bazhi)
            self.result_panel.update_wuxing(wuxing_result)
            self.result_panel.update_shishen(shishen_result)
            self.result_panel.update_geju(bazhi, wuxing_result, shishen_result)
            
        except Exception as e:
            print(f"计算错误: {e}")
            self.result_panel.clear()