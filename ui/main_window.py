"""
风水排盘专业工具 v4.0 - 极简轻量国风主窗口
QSplitter左右分栏35%/65% · 纯白底色 · 圆角卡片 · 三色点缀
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QFrame, QApplication, QStatusBar,
                             QPushButton, QStackedWidget, QSplitter, QScrollArea,
                             QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from ui.components.input_panel import InputPanel
from ui.components.result_panel import ResultPanel
from ui.components.meihua_input import MeihuaInputPanel
from ui.components.meihua_result_panel import MeihuaResultPanel
from ui.components.term_dictionary_panel import TermDictionaryPanel
from ui.components.chart_widget import ChartWidget
from ui.components.login_dialog import LoginDialog, RegisterDialog
from ui.components.ai_analysis_worker import AiAnalysisWorker
from core.bazi_calculator import BaziCalculator
from core.lunar_converter import LunarConverter
from core.solar_time import SolarTimeCalculator
from core.location_db import LocationDB
from core.meihua import MeiHuaCalculator
from core.hexagram_analyzer import HexagramAnalyzer
from core.database_manager import DatabaseManager
from datetime import datetime
import traceback

NAV = [
    {'id': 'bazi', 'name': '八字排盘', 'icon': '☯'},
    {'id': 'meihua', 'name': '梅花易数', 'icon': '⚊'},
    {'id': 'terms', 'name': '术语词典', 'icon': '📖'},
    {'id': 'charts', 'name': '图表分析', 'icon': '📊'},
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('风水排盘专业工具')
        self.setMinimumSize(1100, 700)
        self.resize(1400, 900)
        self.setStyleSheet(Stylesheets.MAIN)

        # 用户状态
        self.current_user_id = None
        self.current_username = None
        self.db_manager = None

        self._init_fonts()
        self._init_core()
        self._init_ui()
        self._connect_signals()
        self._switch('bazi')

    def _init_fonts(self):
        QApplication.setFont(QFont("Microsoft YaHei", 10))
        QApplication.instance().setStyleSheet(Stylesheets.TOOLTIP)

    def _init_core(self):
        self.bazi_calc = BaziCalculator()
        self.lunar_conv = LunarConverter()
        self.solar_calc = SolarTimeCalculator()
        self.location_db = LocationDB()
        self.meihua_calc = MeiHuaCalculator()
        self.hexagram_analyzer = HexagramAnalyzer()
        # 初始化数据库管理器
        try:
            self.db_manager = DatabaseManager()
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            self.db_manager = None

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ===== 顶部导航栏 =====
        self._create_navbar(root)

        # ===== 内容区：QSplitter左右分栏 =====
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {Colors.DIVIDER};
                width: 1px;
            }}
        """)
        self.splitter.setHandleWidth(1)
        self.splitter.setStretchFactor(0, 35)
        self.splitter.setStretchFactor(1, 65)

        # 左侧
        self.left_stack = QStackedWidget()
        self.left_stack.setStyleSheet("background: transparent;")
        self._build_left()
        self.splitter.addWidget(self.left_stack)

        # 右侧
        self.right_stack = QStackedWidget()
        self.right_stack.setStyleSheet("background: transparent;")
        self._build_right()
        self.splitter.addWidget(self.right_stack)

        root.addWidget(self.splitter, 1)

        # 状态栏
        sb = QStatusBar()
        sb.setStyleSheet(Stylesheets.STATUS)
        sb.showMessage('风水排盘专业工具 v4.0')
        self.setStatusBar(sb)

    def _create_navbar(self, parent):
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border-bottom: 1px solid {Colors.DIVIDER};
            }}
        """)
        h = QHBoxLayout(bar)
        h.setContentsMargins(20, 0, 20, 0)

        # Logo
        logo = QLabel('☯')
        logo.setStyleSheet(f"font-size: 16px; color: {Colors.LIUJIN};")

        title = QLabel('风水排盘')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_TITLE};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
        """)

        h.addWidget(logo)
        h.addWidget(title)
        h.addSpacing(30)

        # 导航按钮
        self.nav_btns = {}
        for item in NAV:
            btn = QPushButton(item['icon'] + '  ' + item['name'])
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Colors.TEXT3};
                    border: 1px solid transparent;
                    border-radius: {Spacing.RADIUS_SM};
                    font-size: {Fonts.SZ_SMALL};
                    font-family: {Fonts.BODY};
                    padding: 5px 16px;
                }}
                QPushButton:hover {{
                    color: {Colors.TEXT2};
                    background: {Colors.HOVER};
                }}
                QPushButton:checked {{
                    color: {Colors.QINGHUA};
                    background: rgba(91, 143, 168, 0.08);
                    border-color: {Colors.QINGHUA_LIGHT};
                }}
            """)
            self.nav_btns[item['id']] = btn
            h.addWidget(btn)
            btn.clicked.connect(lambda _, pid=item['id']: self._switch(pid))

        h.addStretch()

        # 用户登录/用户名按钮
        self.user_btn = QPushButton('登录')
        self.user_btn.setCursor(Qt.PointingHandCursor)
        self.user_btn.setFixedHeight(32)
        self.user_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.QINGHUA};
                border: 1px solid {Colors.QINGHUA_LIGHT};
                border-radius: {Spacing.RADIUS_SM};
                font-size: {Fonts.SZ_SMALL};
                font-family: {Fonts.BODY};
                padding: 4px 16px;
            }}
            QPushButton:hover {{
                background: rgba(91, 143, 168, 0.08);
                color: {Colors.QINGHUA};
            }}
        """)
        self.user_btn.clicked.connect(self._on_user_btn_clicked)
        h.addWidget(self.user_btn)

        # 右侧模块标签
        self.module_hint = QLabel('八字排盘')
        self.module_hint.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            color: {Colors.TEXT3};
            font-family: {Fonts.BODY};
        """)
        h.addWidget(self.module_hint)

        parent.addWidget(bar)

    def _build_left(self):
        self.bazi_input = InputPanel()
        self.left_stack.addWidget(self.bazi_input)
        self.meihua_input = MeihuaInputPanel()
        self.left_stack.addWidget(self.meihua_input)
        self.terms_panel = TermDictionaryPanel()
        self.left_stack.addWidget(self.terms_panel)
        # 图表占位
        w = QWidget()
        l = QLabel('图表分析参数', w)
        l.setStyleSheet(f"color:{Colors.TEXT3}; font-size:16px;")
        l.setAlignment(Qt.AlignCenter)
        self.left_stack.addWidget(w)

    def _build_right(self):
        self.bazi_result = ResultPanel()
        self.right_stack.addWidget(self.bazi_result)
        self.meihua_result = MeihuaResultPanel()
        self.right_stack.addWidget(self.meihua_result)
        # 术语
        tw = QWidget()
        tl = QVBoxLayout(tw)
        tl.setContentsMargins(40, 40, 40, 40)
        tl.addWidget(QLabel('← 请从左侧选择术语分类'))
        self.right_stack.addWidget(tw)
        # 图表
        self.chart_widget = ChartWidget()
        self.right_stack.addWidget(self.chart_widget)

    def _switch(self, pid):
        for k, b in self.nav_btns.items():
            b.setChecked(k == pid)
        idx = {'bazi': 0, 'meihua': 1, 'terms': 2, 'charts': 3}
        names = {'bazi': '八字排盘', 'meihua': '梅花易数', 'terms': '术语词典', 'charts': '图表分析'}
        self.left_stack.setCurrentIndex(idx.get(pid, 0))
        self.right_stack.setCurrentIndex(idx.get(pid, 0))
        self.module_hint.setText(names.get(pid, ''))

    def _connect_signals(self):
        self.bazi_input.submit_btn.clicked.connect(self._on_bazi)
        self.bazi_input.reset_btn.clicked.connect(self._on_bazi_reset)
        self.bazi_result.refresh_btn.clicked.connect(self._on_bazi)
        self.bazi_result.ai_analyze_btn.clicked.connect(self._on_bazi_ai_analyze)
        self.meihua_input.submit_btn.clicked.connect(self._on_meihua)
        self.meihua_input.reset_btn.clicked.connect(self._on_meihua_reset)
        self.meihua_result.ai_analyze_btn.clicked.connect(self._on_meihua_ai_analyze)

    # ===== 用户登录相关 =====

    def _on_user_btn_clicked(self):
        """处理用户按钮点击事件"""
        if self.current_user_id is not None:
            # 已登录，显示退出确认
            reply = QMessageBox.question(
                self, '确认退出', f'当前用户: {self.current_username}\n是否退出登录？',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._logout()
        else:
            # 未登录，显示登录对话框
            self._show_login_dialog()

    def _show_login_dialog(self):
        """显示登录对话框"""
        dialog = LoginDialog(db_manager=self.db_manager, parent=self)
        dialog.user_logged_in.connect(self._on_user_logged_in)
        dialog.switch_to_register.connect(lambda: self._show_register_dialog(dialog))
        dialog.exec()

    def _show_register_dialog(self, close_dialog=None):
        """显示注册对话框"""
        if close_dialog:
            close_dialog.close()
        dialog = RegisterDialog(db_manager=self.db_manager, parent=self)
        dialog.user_registered.connect(self._on_user_logged_in)
        dialog.switch_to_login.connect(lambda: self._show_login_dialog())
        dialog.exec()

    def _on_user_logged_in(self, user_id: int, username: str):
        """用户登录成功回调"""
        self.current_user_id = user_id
        self.current_username = username
        self.user_btn.setText(username)
        self.user_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(91, 143, 168, 0.08);
                color: {Colors.QINGHUA};
                border: 1px solid {Colors.QINGHUA_LIGHT};
                border-radius: {Spacing.RADIUS_SM};
                font-size: {Fonts.SZ_SMALL};
                font-family: {Fonts.BODY};
                padding: 4px 16px;
            }}
            QPushButton:hover {{
                background: rgba(91, 143, 168, 0.15);
                color: {Colors.QINGHUA};
            }}
        """)
        self.statusBar().showMessage(f'欢迎回来，{username}')

    def _logout(self):
        """退出登录"""
        self.current_user_id = None
        self.current_username = None
        self.user_btn.setText('登录')
        self.user_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.QINGHUA};
                border: 1px solid {Colors.QINGHUA_LIGHT};
                border-radius: {Spacing.RADIUS_SM};
                font-size: {Fonts.SZ_SMALL};
                font-family: {Fonts.BODY};
                padding: 4px 16px;
            }}
            QPushButton:hover {{
                background: rgba(91, 143, 168, 0.08);
                color: {Colors.QINGHUA};
            }}
        """)
        self.statusBar().showMessage('已退出登录')

    def _save_pan_record(self, data: dict, result: dict, pan_type: str):
        """保存排盘记录到数据库"""
        if not self.db_manager or self.current_user_id is None:
            return

        try:
            birth_date = f"{data.get('year', '')}-{data.get('month', ''):02d}-{data.get('day', ''):02d}"
            birth_time = f"{data.get('hour', 0):02d}:{data.get('minute', 0):02d}"

            record_id = self.db_manager.save_pan_record(
                user_id=self.current_user_id,
                name=data.get('name', '未命名'),
                gender=data.get('gender', ''),
                birth_date=birth_date,
                birth_time=birth_time,
                city=data.get('city', ''),
                pan_type=pan_type,
                result=result
            )

            if record_id:
                self.statusBar().showMessage(f'排盘完成 · 已保存到数据库 · 记录ID: {record_id}')
            else:
                self.statusBar().showMessage('排盘完成 · 保存到数据库失败')
        except Exception as e:
            print(f"保存排盘记录失败: {e}")
            self.statusBar().showMessage('排盘完成 · 保存到数据库失败')

    # ===== 八字 =====
    def _on_bazi(self):
        try:
            data = self.bazi_input.get_data()
            self.bazi_result.show_loading()
            QTimer.singleShot(80, lambda: self._do_bazi(data))
        except Exception as e:
            self.statusBar().showMessage(f'参数错误: {e}')

    def _do_bazi(self, data):
        try:
            y, m, d, hh, mm = data['year'], data['month'], data['day'], data['hour'], data['minute']
            if data['is_lunar']:
                sol = self.lunar_conv.lunar_to_solar(y, m, d)
                if not sol: return
                y, m, d = sol
            dt = datetime(y, m, d, hh, mm)
            sdt = self.solar_calc.get_solar_time(dt, data['longitude'])
            bazi = self.bazi_calc.calculate(y, m, d, sdt.hour)
            li = self.lunar_conv.solar_to_lunar(y, m, d)
            wx = self.bazi_calc.get_wuxing(bazi)
            ss = self.bazi_calc.get_shishen(bazi)
            ml = self.bazi_calc.get_mingli(bazi)
            result = {
                'basic_info': {
                    'pan_type': '八字排盘', 'solar_date': f'{y}年{m}月{d}日',
                    'lunar_date': f'{li[0]}年{li[1]}月{li[2]}日' if li else '-',
                    'hour': f'{sdt.hour:02d}:{sdt.minute:02d}',
                    'location': data['city'], 'gender': data['gender'],
                },
                'bazi': {
                    'year_pillar': bazi['year_pillar'], 'month_pillar': bazi['month_pillar'],
                    'day_pillar': bazi['day_pillar'], 'hour_pillar': bazi['hour_pillar'],
                },
                'wuxing': {k: v if isinstance(v, int) else v.get('count', 0) for k, v in wx.items() if k in ('木','火','土','金','水')},
                'analysis': self._analysis(ml, ss),
            }
            self.bazi_result.display_result(result)
            self.statusBar().showMessage(f'排盘完成 · {data["city"]} {y}年{m}月{d}日')

            # 保存到数据库
            self._save_pan_record(data, result, '八字排盘')
        except Exception as e:
            self.statusBar().showMessage(f'计算错误: {e}')
            traceback.print_exc()

    def _analysis(self, ml, ss):
        a = []
        sh = ss.get('summary', {})
        if '正官' in sh or '七杀' in sh: a.append({'type': '中', 'text': '官杀透干，事业心强，注意工作压力'})
        if '正财' in sh or '偏财' in sh: a.append({'type': '吉', 'text': '财星显现，财运较好'})
        if '正印' in sh or '偏印' in sh: a.append({'type': '吉', 'text': '印星护身，贵人相助'})
        if '食神' in sh or '伤官' in sh: a.append({'type': '中', 'text': '食伤泄秀，才华出众'})
        sn = ml.get('shensha', {})
        for k, key in [('positive', '吉'), ('negative', '凶')]:
            items = sn.get(k, [])
            if items:
                ns = '、'.join(s['name'] for s in items[:3])
                a.append({'type': key, 'text': f'命带{ns}'})
        if not a:
            a = [{'type': '吉', 'text': '日主得令，宜积极进取'}, {'type': '中', 'text': '财星透干，理财宜谨慎'}, {'type': '凶', 'text': '官杀混杂，注意身心'}]
        return a

    def _on_bazi_reset(self):
        self.bazi_input.clear()
        self.bazi_result.clear()

    # ===== 梅花 =====
    def _on_meihua(self):
        try:
            data = self.meihua_input.get_data()
            self.meihua_result.show_loading()
            QTimer.singleShot(80, lambda: self._do_meihua(data))
        except Exception as e:
            self.statusBar().showMessage(f'参数错误: {e}')

    def _do_meihua(self, data):
        try:
            method, q = data['method'], data.get('question', '')
            now = datetime.now()
            hr = None
            if method == 'time': hr = self.meihua_calc.time_divination(now.year, now.month, now.day, now.hour, q)
            elif method == 'number': hr = self.meihua_calc.number_divination([data.get('num1', 3), data.get('num2', 5)], q)
            elif method == 'direction': hr = self.meihua_calc.direction_divination(data.get('direction', '南方'), q)
            elif method == 'text': hr = self.meihua_calc.text_divination(data.get('text', '梅花'), q)
            if not hr: return
            all_hex = self.meihua_calc.generate_all_hexagrams(hr)
            analysis = self.hexagram_analyzer.analyze_divination(hr, all_hex)
            base = analysis.get('base', {})
            result = {
                'basic_info': {'method': method, 'question': q, 'time': now.strftime('%Y年%m月%d日 %H:%M'), 'moving_yao': ''},
                'overall': {'level': analysis.get('overall_judgment', '平'), 'overall': base.get('description', '')},
                'ben_gua': base, 'hu_gua': analysis.get('hu', {}), 'bian_gua': analysis.get('bian', {}),
                'cuo_gua': analysis.get('cuo', {}), 'zong_gua': analysis.get('zong', {}),
                'yao_list': base.get('yao_ci', []), 'suggestions': analysis.get('suggestions', []),
            }
            self.meihua_result.display_result(result)
            self.statusBar().showMessage('梅花易数起卦完成')

            # 保存到数据库（梅花易数也支持保存）
            self._save_pan_record(data, result, '梅花易数')
        except Exception as e:
            self.statusBar().showMessage(f'起卦错误: {e}')
            traceback.print_exc()

    def _on_meihua_reset(self):
        self.meihua_input.clear()
        self.meihua_result.clear()

    # ===== AI分析 =====

    def _on_bazi_ai_analyze(self):
        """八字AI分析按钮点击处理"""
        try:
            input_data = self.bazi_input.get_data()
            chart_data = self.bazi_result.get_chart_data_for_ai()

            if not chart_data or not chart_data.get('bazi', {}).get('year'):
                QMessageBox.warning(self, '提示', '请先进行排盘，再使用AI分析功能')
                return

            self.bazi_result.show_ai_loading('AI正在深入分析八字命理…')
            self.statusBar().showMessage('AI分析进行中，请稍候…')

            self._bazi_ai_worker = AiAnalysisWorker('bazi', input_data, chart_data)
            self._bazi_ai_worker.progress_updated.connect(self._on_bazi_ai_progress)
            self._bazi_ai_worker.analysis_finished.connect(self._on_bazi_ai_finished)
            self._bazi_ai_worker.analysis_failed.connect(self._on_bazi_ai_failed)
            self._bazi_ai_worker.start()

        except Exception as e:
            self.statusBar().showMessage(f'AI分析启动失败: {e}')
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'AI分析启动失败: {e}')

    def _on_bazi_ai_progress(self, stage: str, message: str):
        """八字AI分析进度更新"""
        status_messages = {
            'validating': '正在验证输入数据…',
            'initializing': '正在初始化AI分析引擎…',
            'analyzing': 'AI正在深度分析八字命理…',
            'completed': '分析完成！'
        }
        status = status_messages.get(stage, message)
        self.statusBar().showMessage(status)

    def _on_bazi_ai_finished(self, result: dict):
        """八字AI分析完成"""
        try:
            ai_analysis = result.get('ai_analysis', {})
            self.bazi_result.display_ai_result(ai_analysis)

            token_usage = result.get('token_usage', 0)
            report_id = result.get('report_id', 0)
            elapsed = result.get('elapsed_seconds', 0)
            self.statusBar().showMessage(
                f'AI分析完成 · 报告ID: {report_id} · '
                f'消耗Token: {token_usage} · 耗时: {elapsed:.1f}秒'
            )
        except Exception as e:
            self.statusBar().showMessage(f'显示AI分析结果失败: {e}')
            traceback.print_exc()

    def _on_bazi_ai_failed(self, error_type: str, error_message: str):
        """八字AI分析失败"""
        self.bazi_result.display_result(getattr(self.bazi_result, '_current_result', {}))
        self.bazi_result.ai_analyze_btn.setVisible(True)
        self.bazi_result.ai_analyze_btn.setEnabled(True)
        self.statusBar().showMessage(f'AI分析失败: {error_type}')

        error_titles = {
            'validation_error': '数据验证失败',
            'ai_timeout': 'AI请求超时',
            'ai_request_error': 'AI请求失败',
            'ai_response_error': 'AI响应解析失败',
            'db_connection_error': '数据库连接异常',
            'db_query_error': '数据库操作异常',
        }
        title = error_titles.get(error_type, '分析失败')

        msg_lines = error_message.split('\n')
        short_msg = msg_lines[0] if msg_lines else error_message

        QMessageBox.warning(self, title, short_msg)

    def _on_meihua_ai_analyze(self):
        """梅花易数AI分析按钮点击处理"""
        try:
            input_data = self.meihua_input.get_data()
            hexagram_data = self.meihua_result.get_hexagram_data_for_ai()

            if not hexagram_data or not hexagram_data.get('base', {}).get('name'):
                QMessageBox.warning(self, '提示', '请先起卦，再使用AI解读功能')
                return

            self.meihua_result.show_ai_loading('AI正在解读卦象玄机…')
            self.statusBar().showMessage('AI解读进行中，请稍候…')

            self._meihua_ai_worker = AiAnalysisWorker('meihua', input_data, hexagram_data)
            self._meihua_ai_worker.progress_updated.connect(self._on_meihua_ai_progress)
            self._meihua_ai_worker.analysis_finished.connect(self._on_meihua_ai_finished)
            self._meihua_ai_worker.analysis_failed.connect(self._on_meihua_ai_failed)
            self._meihua_ai_worker.start()

        except Exception as e:
            self.statusBar().showMessage(f'AI解读启动失败: {e}')
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'AI解读启动失败: {e}')

    def _on_meihua_ai_progress(self, stage: str, message: str):
        """梅花易数AI分析进度更新"""
        status_messages = {
            'validating': '正在验证输入数据…',
            'initializing': '正在初始化AI分析引擎…',
            'analyzing': 'AI正在解读卦象玄机…',
            'completed': '解读完成！'
        }
        status = status_messages.get(stage, message)
        self.statusBar().showMessage(status)

    def _on_meihua_ai_finished(self, result: dict):
        """梅花易数AI分析完成"""
        try:
            ai_analysis = result.get('ai_analysis', {})
            self.meihua_result.display_ai_analysis_result(ai_analysis)

            token_usage = result.get('token_usage', 0)
            report_id = result.get('report_id', 0)
            elapsed = result.get('elapsed_seconds', 0)
            self.statusBar().showMessage(
                f'AI解读完成 · 报告ID: {report_id} · '
                f'消耗Token: {token_usage} · 耗时: {elapsed:.1f}秒'
            )
        except Exception as e:
            self.statusBar().showMessage(f'显示AI解读结果失败: {e}')
            traceback.print_exc()

    def _on_meihua_ai_failed(self, error_type: str, error_message: str):
        """梅花易数AI分析失败"""
        self.meihua_result.display_result(getattr(self.meihua_result, '_current_result', {}))
        self.meihua_result.ai_analyze_btn.setVisible(True)
        self.meihua_result.ai_analyze_btn.setEnabled(True)
        self.statusBar().showMessage(f'AI解读失败: {error_type}')

        error_titles = {
            'validation_error': '数据验证失败',
            'ai_timeout': 'AI请求超时',
            'ai_request_error': 'AI请求失败',
            'ai_response_error': 'AI响应解析失败',
            'db_connection_error': '数据库连接异常',
            'db_query_error': '数据库操作异常',
        }
        title = error_titles.get(error_type, '解读失败')

        msg_lines = error_message.split('\n')
        short_msg = msg_lines[0] if msg_lines else error_message

        QMessageBox.warning(self, title, short_msg)
