from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QFrame, QSplitter, QApplication, QStatusBar)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFontDatabase, QFont
from ui.styles import Stylesheets, Colors, Fonts
from ui.components.input_panel import InputPanel
from ui.components.result_panel import ResultPanel
from core.bazi_calculator import BaziCalculator
from core.lunar_converter import LunarConverter
from core.solar_time import SolarTimeCalculator
from core.location_db import LocationDB
from datetime import datetime
import traceback


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('风水排盘专业工具')
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self.setStyleSheet(Stylesheets.MAIN_WINDOW)

        # 加载中文字体
        self._load_chinese_fonts()

        # 初始化核心组件
        self.bazi_calc = BaziCalculator()
        self.lunar_conv = LunarConverter()
        self.solar_calc = SolarTimeCalculator()
        self.location_db = LocationDB()

        # 初始化UI
        self.init_ui()
        self.connect_signals()

    def _load_chinese_fonts(self):
        """加载中文字体"""
        app_font = QFont("Microsoft YaHei", 10)
        app_font.setStyleStrategy(QFont.PreferAntialias)
        QApplication.setFont(app_font)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 可调整的分栏布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {Colors.BORDER_LIGHT};
            }}
            QSplitter::handle:hover {{
                background-color: {Colors.HIGHLIGHT};
            }}
        """)

        # 左侧输入面板
        self.input_panel = InputPanel()
        self.input_panel.setMinimumWidth(380)
        self.input_panel.setMaximumWidth(520)

        # 右侧结果面板
        self.result_panel = ResultPanel()
        self.result_panel.setMinimumWidth(500)

        splitter.addWidget(self.input_panel)
        splitter.addWidget(self.result_panel)

        # 初始比例 35:65
        total_width = self.width()
        left_width = int(total_width * 0.35)
        splitter.setSizes([left_width, total_width - left_width])

        main_layout.addWidget(splitter)

        # 状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(Stylesheets.STATUS_BAR)
        self.status_bar.showMessage('风水排盘专业工具 v1.0 | 新中式极简国风设计')
        self.setStatusBar(self.status_bar)

    def connect_signals(self):
        self.input_panel.submit_btn.clicked.connect(self.on_calculate)
        self.input_panel.reset_btn.clicked.connect(self.on_reset)
        self.result_panel.refresh_btn.clicked.connect(self.on_calculate)

    def on_calculate(self):
        try:
            data = self.input_panel.get_data()
            self.result_panel.show_loading()
            self.status_bar.showMessage('正在计算排盘...')
            QTimer.singleShot(100, lambda: self._do_calculate(data))
        except Exception as e:
            self.status_bar.showMessage(f'错误: {str(e)}')
            traceback.print_exc()

    def _do_calculate(self, data):
        try:
            year = data['year']
            month = data['month']
            day = data['day']
            hour = data['hour']
            minute = data['minute']
            is_lunar = data['is_lunar']
            city = data['city']
            longitude = data['longitude']
            gender = data['gender']
            pan_type = data.get('pan_type', 'bazi')

            # 农历转公历
            if is_lunar:
                solar_date = self.lunar_conv.lunar_to_solar(year, month, day)
                if solar_date is None:
                    self.status_bar.showMessage('农历日期转换失败')
                    return
                year, month, day = solar_date

            # 计算真太阳时
            dt = datetime(year, month, day, hour, minute)
            solar_dt = self.solar_calc.get_solar_time(dt, longitude)

            # 计算八字
            bazi = self.bazi_calc.calculate(year, month, day, solar_dt.hour)

            # 获取农历信息
            lunar_info = self.lunar_conv.solar_to_lunar(year, month, day)

            # 计算五行
            wuxing = self.bazi_calc.get_wuxing(bazi)

            # 计算十神
            shishen = self.bazi_calc.get_shishen(bazi)

            # 计算大运
            dayun = self.bazi_calc.get_dayun(bazi, gender, year)

            # 计算流年
            liunian = self.bazi_calc.get_liunian(bazi)

            # 计算命理综合分析
            mingli = self.bazi_calc.get_mingli(bazi)

            # 构建结果数据
            result_data = {
                'basic_info': {
                    'pan_type': self._get_pan_type_name(pan_type),
                    'solar_date': f'{year}年{month}月{day}日',
                    'lunar_date': f'{lunar_info[0]}年{lunar_info[1]}月{lunar_info[2]}日' if lunar_info else '-',
                    'hour': f'{solar_dt.hour:02d}:{solar_dt.minute:02d}',
                    'location': city,
                    'gender': gender,
                },
                'bazi': {
                    'year_pillar': bazi['year_pillar'],
                    'month_pillar': bazi['month_pillar'],
                    'day_pillar': bazi['day_pillar'],
                    'hour_pillar': bazi['hour_pillar'],
                },
                'wuxing': {
                    '金': wuxing.get('金', {}).get('count', 0),
                    '木': wuxing.get('木', {}).get('count', 0),
                    '水': wuxing.get('水', {}).get('count', 0),
                    '火': wuxing.get('火', {}).get('count', 0),
                    '土': wuxing.get('土', {}).get('count', 0),
                },
                'analysis': self._build_analysis(mingli, shishen),
            }

            # 显示结果
            self.result_panel.display_result(result_data)
            self.status_bar.showMessage(
                f'排盘完成 | {city} | {gender} | {year}年{month}月{day}日 '
                f'{solar_dt.hour:02d}:{solar_dt.minute:02d}'
            )

        except Exception as e:
            self.status_bar.showMessage(f'计算错误: {str(e)}')
            traceback.print_exc()

    def _build_analysis(self, mingli, shishen):
        """根据命理分析结果构建吉凶批注"""
        analysis = []
        rizhu = shishen.get('rizhu', '')

        # 基于十神分布生成分析
        summary = shishen.get('summary', {})
        if summary:
            if '正官' in summary or '七杀' in summary:
                analysis.append({'type': '中', 'text': f'官杀透干，事业心强，但需注意工作压力与小人'})
            if '正财' in summary or '偏财' in summary:
                analysis.append({'type': '吉', 'text': f'财星显现，财运较好，理财需谨慎，不宜冒险投资'})
            if '正印' in summary or '偏印' in summary:
                analysis.append({'type': '吉', 'text': f'印星护身，学业运佳，利于深造进修，贵人相助'})
            if '食神' in summary or '伤官' in summary:
                analysis.append({'type': '中', 'text': f'食伤泄秀，才华出众，利于创意表达，但需防口舌是非'})

        # 基于神煞生成分析
        shensha = mingli.get('shensha', {})
        positive = shensha.get('positive', [])
        negative = shensha.get('negative', [])
        if positive:
            names = '、'.join(s['name'] for s in positive[:3])
            analysis.append({'type': '吉', 'text': f'命带吉神：{names}，逢凶化吉，一生多贵人相助'})
        if negative:
            names = '、'.join(s['name'] for s in negative[:3])
            analysis.append({'type': '凶', 'text': f'命带凶煞：{names}，需注意防范，趋吉避凶'})

        # 基于干支关系生成分析
        ganzhi_relations = mingli.get('ganzhi_relations', {})
        zhi_relations = ganzhi_relations.get('zhi_relations', [])
        for rel in zhi_relations:
            if '冲' in rel:
                analysis.append({'type': '凶', 'text': f'四柱中有{rel}，主动荡变化，需注意人际关系'})
                break

        # 保证至少有分析内容
        if not analysis:
            analysis.append({'type': '吉', 'text': f'日主{rizhu}得令，身强有力，事业运势旺盛，宜积极进取'})
            analysis.append({'type': '中', 'text': f'财星透干，正财偏财皆有，理财需谨慎，不宜冒险投资'})
            analysis.append({'type': '凶', 'text': f'官杀混杂，工作压力较大，注意调节身心，防小人暗算'})
            analysis.append({'type': '吉', 'text': f'印星护身，学业运佳，利于深造进修，贵人相助'})

        return analysis

    def _get_pan_type_name(self, pan_type):
        names = {
            'bazi': '八字排盘',
            'ziwei': '紫微排盘',
            'qimen': '奇门遁甲',
            'liuyao': '六爻',
            'fengshui': '风水宅盘',
        }
        return names.get(pan_type, pan_type)

    def on_reset(self):
        self.input_panel.clear()
        self.result_panel.clear()
        self.status_bar.showMessage('参数已重置')
