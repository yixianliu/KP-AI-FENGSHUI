from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QFrame, QSplitter, QApplication, QStatusBar,
                             QPushButton, QStackedWidget)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFontDatabase, QFont, QIcon
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from ui.components.input_panel import InputPanel
from ui.components.result_panel import ResultPanel
from ui.components.meihua_input import MeihuaInputPanel
from ui.components.meihua_result_panel import MeihuaResultPanel
from ui.components.term_dictionary_panel import TermDictionaryPanel
from ui.components.chart_widget import ChartWidget
from core.bazi_calculator import BaziCalculator
from core.lunar_converter import LunarConverter
from core.solar_time import SolarTimeCalculator
from core.location_db import LocationDB
from core.meihua import MeiHuaCalculator
from core.hexagram_analyzer import HexagramAnalyzer
from datetime import datetime
import traceback


# 导航菜单项配置
NAV_MENU = [
    {'id': 'bazi', 'name': '八字排盘', 'icon': '☯', 'desc': '专业八字命理排盘'},
    {'id': 'meihua', 'name': '梅花易数', 'icon': '🔮', 'desc': '梅花易数起卦解卦'},
    {'id': 'terms', 'name': '术语词典', 'icon': '📖', 'desc': '专业术语查询'},
    {'id': 'charts', 'name': '图表分析', 'icon': '📊', 'desc': '数据可视化图表'},
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('风水排盘专业工具')
        self.setMinimumSize(1300, 850)
        self.resize(1500, 950)
        self.setStyleSheet(Stylesheets.MAIN_WINDOW)

        self._load_chinese_fonts()
        self._init_core_components()
        self.init_ui()
        self._connect_signals()
        self._switch_page('bazi')

    def _load_chinese_fonts(self):
        """加载中文字体"""
        app_font = QFont("Microsoft YaHei", 10)
        app_font.setStyleStrategy(QFont.PreferAntialias)
        QApplication.setFont(app_font)

    def _init_core_components(self):
        """初始化核心计算组件"""
        self.bazi_calc = BaziCalculator()
        self.lunar_conv = LunarConverter()
        self.solar_calc = SolarTimeCalculator()
        self.location_db = LocationDB()
        self.meihua_calc = MeiHuaCalculator()
        self.hexagram_analyzer = HexagramAnalyzer()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航栏
        self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        # 右侧内容区域
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {Colors.BACKGROUND};
            }}
        """)

        # 创建各模块页面
        self._create_bazi_page()
        self._create_meihua_page()
        self._create_terms_page()
        self._create_charts_page()

        main_layout.addWidget(self.content_stack, 1)

        # 状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(Stylesheets.STATUS_BAR)
        self.status_bar.showMessage('风水排盘专业工具 v2.0 | 新中式极简国风设计')
        self.setStatusBar(self.status_bar)

    def _create_sidebar(self):
        """创建左侧导航栏"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.PRIMARY_DARK}, stop:1 {Colors.PRIMARY});
                border: none;
            }}
        """)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo区域
        logo_widget = QWidget()
        logo_widget.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
            }}
        """)
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(20, 30, 20, 24)
        logo_layout.setSpacing(8)

        logo_icon = QLabel('☯')
        logo_icon.setStyleSheet(f"""
            font-size: 42px;
            color: {Colors.HIGHLIGHT};
        """)
        logo_icon.setAlignment(Qt.AlignCenter)

        logo_title = QLabel('风水排盘')
        logo_title.setStyleSheet(f"""
            font-size: 22px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.HIGHLIGHT_LIGHT};
            font-family: {Fonts.FAMILY_SERIF};
            letter-spacing: 4px;
        """)
        logo_title.setAlignment(Qt.AlignCenter)

        logo_subtitle = QLabel('专业命理工具')
        logo_subtitle.setStyleSheet(f"""
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
            font-family: {Fonts.FAMILY_CN};
            letter-spacing: 2px;
        """)
        logo_subtitle.setAlignment(Qt.AlignCenter)

        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_title)
        logo_layout.addWidget(logo_subtitle)
        sidebar_layout.addWidget(logo_widget)

        # 分割线
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: rgba(255, 255, 255, 0.1);")
        divider.setContentsMargins(20, 0, 20, 0)
        sidebar_layout.addWidget(divider)

        # 导航菜单
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(6)

        self.nav_buttons = {}
        for item in NAV_MENU:
            btn = self._create_nav_button(item)
            self.nav_buttons[item['id']] = btn
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        sidebar_layout.addWidget(nav_widget, 1)

        # 底部版本信息
        footer_widget = QWidget()
        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setContentsMargins(16, 16, 16, 20)
        footer_layout.setSpacing(4)

        version_label = QLabel('v2.0.0')
        version_label.setStyleSheet(f"""
            font-size: 11px;
            color: rgba(255, 255, 255, 0.3);
            font-family: {Fonts.FAMILY_EN};
        """)
        version_label.setAlignment(Qt.AlignCenter)

        footer_layout.addWidget(version_label)
        sidebar_layout.addWidget(footer_widget)

    def _create_nav_button(self, item):
        """创建导航按钮"""
        btn = QPushButton()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setCheckable(True)
        btn.setProperty('nav_id', item['id'])

        btn_layout = QVBoxLayout(btn)
        btn_layout.setContentsMargins(12, 12, 12, 12)
        btn_layout.setSpacing(4)
        btn_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel(item['icon'])
        icon_label.setStyleSheet("font-size: 24px;")
        icon_label.setAlignment(Qt.AlignCenter)

        name_label = QLabel(item['name'])
        name_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: {Fonts.WEIGHT_BOLD};
            font-family: {Fonts.FAMILY_CN};
        """)
        name_label.setAlignment(Qt.AlignCenter)

        desc_label = QLabel(item['desc'])
        desc_label.setStyleSheet(f"""
            font-size: 11px;
            font-family: {Fonts.FAMILY_CN};
        """)
        desc_label.setAlignment(Qt.AlignCenter)

        btn_layout.addWidget(icon_label)
        btn_layout.addWidget(name_label)
        btn_layout.addWidget(desc_label)

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 10px;
                color: rgba(255, 255, 255, 0.6);
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.9);
            }}
            QPushButton:checked {{
                background-color: {Colors.ACCENT};
                color: white;
            }}
            QPushButton:checked QLabel {{
                color: white;
            }}
        """)

        btn.clicked.connect(lambda: self._switch_page(item['id']))
        return btn

    def _switch_page(self, page_id):
        """切换页面"""
        for nav_id, btn in self.nav_buttons.items():
            btn.setChecked(nav_id == page_id)

        page_map = {
            'bazi': self.bazi_page,
            'meihua': self.meihua_page,
            'terms': self.terms_page,
            'charts': self.charts_page,
        }

        if page_id in page_map:
            index = self.content_stack.indexOf(page_map[page_id])
            if index >= 0:
                self.content_stack.setCurrentIndex(index)

        page_names = {
            'bazi': '八字排盘',
            'meihua': '梅花易数',
            'terms': '术语词典',
            'charts': '图表分析',
        }
        self.status_bar.showMessage(f'风水排盘专业工具 v2.0 | 当前模块：{page_names.get(page_id, "")}')

    def _create_bazi_page(self):
        """创建八字排盘页面"""
        self.bazi_page = QWidget()
        page_layout = QHBoxLayout(self.bazi_page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

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

        self.bazi_input_panel = InputPanel()
        self.bazi_input_panel.setMinimumWidth(380)
        self.bazi_input_panel.setMaximumWidth(520)

        self.bazi_result_panel = ResultPanel()
        self.bazi_result_panel.setMinimumWidth(500)

        splitter.addWidget(self.bazi_input_panel)
        splitter.addWidget(self.bazi_result_panel)
        splitter.setSizes([420, 900])

        page_layout.addWidget(splitter)
        self.content_stack.addWidget(self.bazi_page)

    def _create_meihua_page(self):
        """创建梅花易数页面"""
        self.meihua_page = QWidget()
        page_layout = QHBoxLayout(self.meihua_page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

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

        self.meihua_input_panel = MeihuaInputPanel()
        self.meihua_input_panel.setMinimumWidth(380)
        self.meihua_input_panel.setMaximumWidth(520)

        self.meihua_result_panel = MeihuaResultPanel()
        self.meihua_result_panel.setMinimumWidth(500)

        splitter.addWidget(self.meihua_input_panel)
        splitter.addWidget(self.meihua_result_panel)
        splitter.setSizes([420, 900])

        page_layout.addWidget(splitter)
        self.content_stack.addWidget(self.meihua_page)

    def _create_terms_page(self):
        """创建术语词典页面"""
        self.terms_page = TermDictionaryPanel()
        self.content_stack.addWidget(self.terms_page)

    def _create_charts_page(self):
        """创建图表分析页面"""
        self.charts_page = QWidget()
        page_layout = QVBoxLayout(self.charts_page)
        card_padding = int(Spacing.CARD_PADDING.replace('px', ''))
        page_layout.setContentsMargins(card_padding, card_padding, card_padding, card_padding)
        page_layout.setSpacing(16)

        # 顶部提示
        hint_card = QFrame()
        hint_card.setStyleSheet(Stylesheets.SECTION_CARD)
        hint_layout = QVBoxLayout(hint_card)
        hint_layout.setContentsMargins(16, 14, 16, 14)

        hint_title = QLabel('📊 数据可视化图表')
        hint_title.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SECTION};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        hint_desc = QLabel('在八字排盘完成后，可在此查看五行、十神、大运等数据的可视化图表分析')
        hint_desc.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        hint_layout.addWidget(hint_title)
        hint_layout.addWidget(hint_desc)
        page_layout.addWidget(hint_card)

        # 图表组件
        self.chart_widget = ChartWidget()
        page_layout.addWidget(self.chart_widget, 1)

        self.content_stack.addWidget(self.charts_page)

    def _connect_signals(self):
        """连接信号"""
        # 八字排盘
        self.bazi_input_panel.submit_btn.clicked.connect(self._on_bazi_calculate)
        self.bazi_input_panel.reset_btn.clicked.connect(self._on_bazi_reset)
        self.bazi_result_panel.refresh_btn.clicked.connect(self._on_bazi_calculate)

        # 梅花易数
        self.meihua_input_panel.submit_btn.clicked.connect(self._on_meihua_calculate)
        self.meihua_input_panel.reset_btn.clicked.connect(self._on_meihua_reset)
        self.meihua_result_panel.ai_analyze_btn.clicked.connect(self._on_meihua_ai_analyze)

    # ==================== 八字排盘相关方法 ====================

    def _on_bazi_calculate(self):
        try:
            data = self.bazi_input_panel.get_data()
            self.bazi_result_panel.show_loading()
            self.status_bar.showMessage('正在计算八字排盘...')
            QTimer.singleShot(100, lambda: self._do_bazi_calculate(data))
        except Exception as e:
            self.status_bar.showMessage(f'错误: {str(e)}')
            traceback.print_exc()

    def _do_bazi_calculate(self, data):
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

            if is_lunar:
                solar_date = self.lunar_conv.lunar_to_solar(year, month, day)
                if solar_date is None:
                    self.status_bar.showMessage('农历日期转换失败')
                    return
                year, month, day = solar_date

            dt = datetime(year, month, day, hour, minute)
            solar_dt = self.solar_calc.get_solar_time(dt, longitude)

            bazi = self.bazi_calc.calculate(year, month, day, solar_dt.hour)
            lunar_info = self.lunar_conv.solar_to_lunar(year, month, day)
            wuxing = self.bazi_calc.get_wuxing(bazi)
            shishen = self.bazi_calc.get_shishen(bazi)
            dayun = self.bazi_calc.get_dayun(bazi, gender, year)
            liunian = self.bazi_calc.get_liunian(bazi)
            mingli = self.bazi_calc.get_mingli(bazi)
            shier_shen = self.bazi_calc.get_shier_shen(bazi)

            # 保存图表数据（过滤掉非字典值的summary等字段）
            self._current_wuxing_data = {
                k: v.get('count', 0)
                for k, v in wuxing.items()
                if isinstance(v, dict) and 'count' in v
            }
            self._current_shishen_data = shishen
            self._current_dayun_data = dayun
            self._current_changsheng_data = shier_shen

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
                'wuxing': self._current_wuxing_data,
                'analysis': self._build_bazi_analysis(mingli, shishen),
            }

            self.bazi_result_panel.display_result(result_data)

            # 更新图表数据
            self.chart_widget.set_data(
                wuxing=self._current_wuxing_data,
                shishen=self._current_shishen_data,
                dayun=self._current_dayun_data,
                changsheng=self._current_changsheng_data,
            )

            self.status_bar.showMessage(
                f'八字排盘完成 | {city} | {gender} | {year}年{month}月{day}日 '
                f'{solar_dt.hour:02d}:{solar_dt.minute:02d}'
            )

        except Exception as e:
            self.status_bar.showMessage(f'计算错误: {str(e)}')
            traceback.print_exc()

    def _build_bazi_analysis(self, mingli, shishen):
        """构建八字吉凶批注"""
        analysis = []
        rizhu = shishen.get('rizhu', '')

        summary = shishen.get('summary', {})
        if summary:
            if '正官' in summary or '七杀' in summary:
                analysis.append({'type': '中', 'text': '官杀透干，事业心强，但需注意工作压力与小人'})
            if '正财' in summary or '偏财' in summary:
                analysis.append({'type': '吉', 'text': '财星显现，财运较好，理财需谨慎，不宜冒险投资'})
            if '正印' in summary or '偏印' in summary:
                analysis.append({'type': '吉', 'text': '印星护身，学业运佳，利于深造进修，贵人相助'})
            if '食神' in summary or '伤官' in summary:
                analysis.append({'type': '中', 'text': '食伤泄秀，才华出众，利于创意表达，但需防口舌是非'})

        shensha = mingli.get('shensha', {})
        positive = shensha.get('positive', [])
        negative = shensha.get('negative', [])
        if positive:
            names = '、'.join(s['name'] for s in positive[:3])
            analysis.append({'type': '吉', 'text': f'命带吉神：{names}，逢凶化吉，一生多贵人相助'})
        if negative:
            names = '、'.join(s['name'] for s in negative[:3])
            analysis.append({'type': '凶', 'text': f'命带凶煞：{names}，需注意防范，趋吉避凶'})

        ganzhi_relations = mingli.get('ganzhi_relations', {})
        zhi_relations = ganzhi_relations.get('zhi_relations', [])
        for rel in zhi_relations:
            if '冲' in rel:
                analysis.append({'type': '凶', 'text': f'四柱中有{rel}，主动荡变化，需注意人际关系'})
                break

        if not analysis:
            analysis.append({'type': '吉', 'text': f'日主{rizhu}得令，身强有力，事业运势旺盛，宜积极进取'})
            analysis.append({'type': '中', 'text': '财星透干，正财偏财皆有，理财需谨慎，不宜冒险投资'})
            analysis.append({'type': '凶', 'text': '官杀混杂，工作压力较大，注意调节身心，防小人暗算'})
            analysis.append({'type': '吉', 'text': '印星护身，学业运佳，利于深造进修，贵人相助'})

        return analysis

    def _on_bazi_reset(self):
        self.bazi_input_panel.clear()
        self.bazi_result_panel.clear()
        self.status_bar.showMessage('八字排盘参数已重置')

    # ==================== 梅花易数相关方法 ====================

    def _on_meihua_calculate(self):
        try:
            data = self.meihua_input_panel.get_data()
            self.meihua_result_panel.show_loading()
            self.status_bar.showMessage('正在起卦分析...')
            QTimer.singleShot(100, lambda: self._do_meihua_calculate(data))
        except Exception as e:
            self.status_bar.showMessage(f'错误: {str(e)}')
            traceback.print_exc()

    def _do_meihua_calculate(self, data):
        try:
            method = data['method']
            question = data.get('question', '')

            # 起卦
            hex_result = None
            if method == 'time':
                now = datetime.now()
                hex_result = self.meihua_calc.time_divination(
                    now.year, now.month, now.day, now.hour, question
                )
            elif method == 'number':
                num1 = data.get('num1', 3)
                num2 = data.get('num2', 5)
                hex_result = self.meihua_calc.number_divination([num1, num2], question)
            elif method == 'direction':
                direction = data.get('direction', '南方')
                hex_result = self.meihua_calc.direction_divination(direction, question)
            elif method == 'text':
                text = data.get('text', '梅花易数')
                hex_result = self.meihua_calc.text_divination(text, question)

            if not hex_result:
                self.status_bar.showMessage('起卦失败')
                return

            # 生成所有卦象
            all_hexagrams = self.meihua_calc.generate_all_hexagrams(hex_result)

            # 卦象分析
            analysis = self.hexagram_analyzer.analyze_divination(hex_result, all_hexagrams)

            base_info = analysis.get('base', {})
            yao_list = base_info.get('yao_ci', [])
            moving_yao = base_info.get('changing_yao', 0)
            moving_yao_name = base_info.get('changing_yao_name', '')

            # 构建结果数据
            result_data = {
                'basic_info': {
                    'method': method,
                    'question': question,
                    'time': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
                    'moving_yao': moving_yao_name or (f'第{moving_yao}爻' if moving_yao else ''),
                },
                'overall': {
                    'level': analysis.get('overall_judgment', '平'),
                    'overall': base_info.get('description', ''),
                },
                'ben_gua': base_info,
                'hu_gua': analysis.get('hu', {}),
                'bian_gua': analysis.get('bian', {}),
                'cuo_gua': analysis.get('cuo', {}),
                'zong_gua': analysis.get('zong', {}),
                'yao_list': yao_list,
                'suggestions': analysis.get('suggestions', []),
            }

            self._current_meihua_result = analysis
            self.meihua_result_panel.display_result(result_data)
            self.status_bar.showMessage(
                f'梅花易数起卦完成 | {base_info.get("name", "")} '
                f'→ {analysis.get("bian", {}).get("name", "")}'
            )

        except Exception as e:
            self.status_bar.showMessage(f'起卦错误: {str(e)}')
            traceback.print_exc()

    def _on_meihua_reset(self):
        self.meihua_input_panel.clear()
        self.meihua_result_panel.clear()
        self.status_bar.showMessage('梅花易数参数已重置')

    def _on_meihua_ai_analyze(self):
        """梅花易数AI分析（预留接口）"""
        self.status_bar.showMessage('AI分析功能开发中...')

    def _get_pan_type_name(self, pan_type):
        names = {
            'bazi': '八字排盘',
            'ziwei': '紫微排盘',
            'qimen': '奇门遁甲',
            'liuyao': '六爻',
            'fengshui': '风水宅盘',
        }
        return names.get(pan_type, pan_type)
