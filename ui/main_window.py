"""
风水排盘专业工具 v5.0 - 精美国风主窗口
QSplitter左右分栏35%/65% · 暖米底色 · 圆角卡片 · 三色点缀 · 微动画
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QFrame, QApplication, QStatusBar,
                               QPushButton, QStackedWidget, QSplitter, QScrollArea,
                               QMessageBox, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor
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
from core.redis_manager import get_redis_manager, RedisManager, RedisConnectionError, RedisOperationError
from datetime import datetime
import traceback
import uuid

NAV = [
    {'id': 'bazi', 'name': '八字排盘', 'icon': '☯'},
    {'id': 'meihua', 'name': '梅花易数', 'icon': '⚊'},
    {'id': 'terms', 'name': '术语词典', 'icon': '📖'},
    {'id': 'charts', 'name': '图表分析', 'icon': '📊'},
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.module_hint = None
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
        self._init_redis_polling()
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
        # 初始化Redis管理器
        try:
            self.redis_manager = get_redis_manager()
            if self.redis_manager.test_connection():
                print("Redis连接成功")
            else:
                print("Redis连接失败")
        except Exception as e:
            print(f"Redis初始化失败: {e}")
            self.redis_manager = None

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
            QSplitter::handle:hover {{
                background-color: {Colors.QINGHUA_LIGHT};
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
        sb.showMessage('风水排盘专业工具 v5.0 · 精美国风 · AI自动分析')
        self.setStatusBar(sb)

    def _create_navbar(self, parent):
        bar = QFrame()
        bar.setFixedHeight(60)
        bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFFFFF, stop:1 {Colors.GRADIENT_NAV_END});
                border-bottom: 1px solid {Colors.DIVIDER};
            }}
        """)
        # 导航栏阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setOffset(0, 1)
        shadow.setColor(QColor(0, 0, 0, 30))
        bar.setGraphicsEffect(shadow)

        h = QHBoxLayout(bar)
        h.setContentsMargins(24, 0, 20, 0)
        h.setSpacing(0)

        # Logo区
        logo_container = QFrame()
        logo_container.setStyleSheet("background: transparent; border: none;")
        logo_hl = QHBoxLayout(logo_container)
        logo_hl.setContentsMargins(0, 0, 0, 0)
        logo_hl.setSpacing(4)

        logo = QLabel('☯')
        logo.setStyleSheet(f"font-size: 20px; color: {Colors.LIUJIN};")

        title = QLabel('风水排盘')
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
            letter-spacing: 1px;
        """)

        logo_hl.addWidget(logo)
        logo_hl.addWidget(title)
        h.addWidget(logo_container)
        h.addSpacing(36)

        # 导航按钮组
        nav_container = QFrame()
        nav_container.setStyleSheet(f"""
            background: {Colors.HOVER};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS};
            padding: 3px;
        """)
        nav_hl = QHBoxLayout(nav_container)
        nav_hl.setContentsMargins(3, 3, 3, 3)
        nav_hl.setSpacing(2)

        self.nav_btns = {}
        for item in NAV:
            btn = QPushButton(item['icon'] + '  ' + item['name'])
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Colors.TEXT2};
                    border: none;
                    border-radius: 8px;
                    font-size: {Fonts.SZ_SMALL};
                    font-family: {Fonts.BODY};
                    padding: 5px 16px;
                }}
                QPushButton:hover {{
                    color: {Colors.TEXT};
                    background: {Colors.CARD};
                }}
                QPushButton:checked {{
                    color: {Colors.TEXT_INV};
                    background: {Colors.QINGHUA};
                    font-weight: {Fonts.W_MEDIUM};
                }}
            """)
            self.nav_btns[item['id']] = btn
            nav_hl.addWidget(btn)
            btn.clicked.connect(lambda _, pid=item['id']: self._switch(pid))

        h.addWidget(nav_container)
        h.addStretch()

        # 用户登录/用户名按钮
        self.user_btn = QPushButton('👤 登录')
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
                background: {Colors.QINGHUA_GLOW};
                color: {Colors.QINGHUA_DARK};
            }}
        """)
        self.user_btn.clicked.connect(self._on_user_btn_clicked)
        h.addWidget(self.user_btn)

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

        if self.module_hint is not None:
            self.module_hint.setText(names.get(pid, ''))
        else:
            print("Label is None")

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
        self.user_btn.setText(f'👤 {username}')
        self.user_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.QINGHUA_GLOW};
                color: {Colors.QINGHUA};
                border: 1px solid {Colors.QINGHUA_LIGHT};
                border-radius: {Spacing.RADIUS_SM};
                font-size: {Fonts.SZ_SMALL};
                font-family: {Fonts.BODY};
                padding: 4px 16px;
            }}
            QPushButton:hover {{
                background: rgba(74, 122, 144, 0.18);
                color: {Colors.QINGHUA_DARK};
            }}
        """)
        self.statusBar().showMessage(f'欢迎回来，{username}')

    def _logout(self):
        """退出登录"""
        self.current_user_id = None
        self.current_username = None
        self.user_btn.setText('👤 登录')
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
                background: {Colors.QINGHUA_GLOW};
                color: {Colors.QINGHUA_DARK};
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
            task_id = str(uuid.uuid4())
            self._save_bazi_input_to_redis(task_id, data)
            self.bazi_result.show_loading()
            QTimer.singleShot(80, lambda: self._do_bazi(data, task_id))
        except Exception as e:
            self.statusBar().showMessage(f'参数错误: {e}')
            traceback.print_exc()

    def _save_bazi_input_to_redis(self, task_id: str, data: dict):
        """将八字排盘输入数据保存到Redis"""
        if not self.redis_manager:
            return
        try:
            self.redis_manager.set_task_input('bazi', task_id, data)
            self.redis_manager.set_task_status('bazi', task_id, 'pending')
            print(f"八字排盘数据已存入Redis: bazi:input:{task_id}")
        except (RedisConnectionError, RedisOperationError) as e:
            print(f"Redis存储失败: {e}")
            self.statusBar().showMessage(f'数据缓存失败: {e}')

    def _do_bazi(self, data, task_id=None):
        try:
            y, m, d, hh, mm = data['year'], data['month'], data['day'], data['hour'], data['minute']
            longitude = data['longitude']
            is_lunar = data['is_lunar']
            gender = data.get('gender', '男')

            if is_lunar:
                sol = self.lunar_conv.lunar_to_solar(y, m, d)
                if not sol: return
                y, m, d = sol

            dt = datetime(y, m, d, hh, mm)
            sdt = self.solar_calc.get_solar_time(dt, longitude)

            bazi = self.bazi_calc.calculate(y, m, d, hh, mm, longitude, is_lunar=False)
            li = self.lunar_conv.solar_to_lunar(y, m, d)

            wx = self.bazi_calc.get_wuxing(bazi)
            ss = self.bazi_calc.get_shishen(bazi)
            ml = self.bazi_calc.get_mingli(bazi)
            # 新增：大运与十二长生（图表与深度分析依赖）
            try:
                dayun = self.bazi_calc.get_dayun(bazi, gender, y)
            except Exception as e:
                print(f"大运计算失败: {e}")
                dayun = {'periods': [], 'direction': '顺行'}
            try:
                shier_shen_raw = self.bazi_calc.get_shier_shen(bazi)
                # 转换格式：{pillar: {name, ...}}，供图表组件使用
                shier_shen = {}
                for item in shier_shen_raw.get('shier_shen', []):
                    shier_shen[item['pillar']] = {
                        'name': item.get('shier_shen', ''),
                        'description': item.get('description', ''),
                        'ganzhi': item.get('ganzhi', ''),
                    }
            except Exception as e:
                print(f"十二长生计算失败: {e}")
                shier_shen = {}

            wuxing_summary = {}
            for k in ('木', '火', '土', '金', '水'):
                v = wx.get(k, {})
                if isinstance(v, int):
                    wuxing_summary[k] = v
                else:
                    wuxing_summary[k] = round(v.get('score', 0), 2)

            result = {
                'basic_info': {
                    'pan_type': '八字排盘',
                    'solar_date': f'{y}年{m}月{d}日',
                    'lunar_date': f'{li[0]}年{li[1]}月{li[2]}日' if li else bazi.get('lunar_date', '-'),
                    'hour': f'{sdt.hour:02d}:{sdt.minute:02d}',
                    'location': data['city'],
                    'gender': gender,
                    'solar_time': bazi.get('solar_time', ''),
                    'original_time': bazi.get('original_time', ''),
                    'longitude': longitude,
                },
                'bazi': {
                    'year_pillar': bazi['year_pillar'],
                    'month_pillar': bazi['month_pillar'],
                    'day_pillar': bazi['day_pillar'],
                    'hour_pillar': bazi['hour_pillar'],
                    'rizhu': bazi.get('rizhu', ''),
                    'month_zhi': bazi.get('month_zhi', ''),
                },
                'wuxing': wuxing_summary,
                'wuxing_detail': wx,
                'shishen': ss,
                'mingli': ml,
                'dayun': dayun,
                'shier_shen': shier_shen,
                'analysis': self._analysis(ml, ss),
            }
            self.bazi_result.display_result(result)
            self.statusBar().showMessage(
                f'排盘完成 · {data["city"]} {y}年{m}月{d}日 · 图表数据已就绪，可切换至「图表分析」查看'
            )

            # 关键修复：把排盘数据同步到图表组件，确保图表分析视图能正常渲染
            try:
                self._sync_chart_data(wx, ss, dayun, shier_shen)
            except Exception as chart_err:
                print(f"图表数据同步失败: {chart_err}")
                traceback.print_exc()

            self._save_pan_record(data, result, '八字排盘')

            # ★ v5.0: 排盘完成后自动触发AI分析
            QTimer.singleShot(300, self._trigger_bazi_auto_ai)
        except Exception as e:
            self.statusBar().showMessage(f'计算错误: {e}')
            traceback.print_exc()

    def _trigger_bazi_auto_ai(self):
        """排盘完成后自动触发AI深度分析"""
        try:
            input_data = self.bazi_input.get_data()
            chart_data = self.bazi_result.get_chart_data_for_ai()

            if not chart_data or not chart_data.get('bazi', {}).get('year'):
                print("自动AI分析跳过: 排盘数据不完整")
                return

            # 更新状态提示
            self.statusBar().showMessage('排盘完成 · 正在自动进行AI深度分析…')

            task_id = str(uuid.uuid4())
            self._save_bazi_input_to_redis(task_id, input_data)

            self._bazi_ai_worker = AiAnalysisWorker('bazi', input_data, chart_data, task_id)
            self._bazi_ai_worker.progress_updated.connect(self._on_bazi_ai_progress)
            self._bazi_ai_worker.analysis_finished.connect(self._on_bazi_ai_finished)
            self._bazi_ai_worker.analysis_failed.connect(self._on_bazi_ai_failed)
            self._bazi_ai_worker.start()
        except Exception as e:
            print(f"自动AI分析启动失败: {e}")
            traceback.print_exc()

    def _sync_chart_data(self, wx, ss, dayun, shier_shen):
        """同步排盘数据到图表组件

        关键修复：将五行/十神/大运/十二长生数据按 chart_widget 期望的格式
        整理后传入，确保「图表分析」视图能正常显示各类图表。
        """
        # 1) 五行数据：chart_widget 透传给 chart_gen，
        #    chart_gen 期望 {wx: {count, percentage}}，与 get_wuxing 返回兼容
        chart_wuxing = {}
        if isinstance(wx, dict):
            for k in ('木', '火', '土', '金', '水'):
                v = wx.get(k, {})
                if isinstance(v, dict):
                    chart_wuxing[k] = {
                        'count': v.get('count', 0),
                        'percentage': v.get('percentage', 0),
                    }
                else:
                    chart_wuxing[k] = {'count': v or 0, 'percentage': 0}

        # 2) 十神数据：chart_gen 期望 summary 字段（与 get_shishen 返回一致）
        chart_shishen = ss if isinstance(ss, dict) else {'summary': {}}

        # 3) 大运数据：chart_gen 期望 periods 字段（与 get_dayun 返回一致）
        chart_dayun = dayun if isinstance(dayun, dict) else {'periods': []}

        # 4) 十二长生：chart_gen 期望 {柱位: {name, ...}}，已在 _do_bazi 中转换
        chart_changsheng = shier_shen if isinstance(shier_shen, dict) else {}

        self.chart_widget.set_data(
            wuxing=chart_wuxing,
            shishen=chart_shishen,
            dayun=chart_dayun,
            changsheng=chart_changsheng,
        )
        # 缓存最近一次图表数据，便于切回图表视图时自动恢复
        self._last_chart_data = {
            'wuxing': chart_wuxing,
            'shishen': chart_shishen,
            'dayun': chart_dayun,
            'changsheng': chart_changsheng,
        }

    def _analysis(self, ml, ss):
        a = []
        sh_summary = ss.get('summary', {})
        sh_weight_summary = ss.get('weight_summary', {})
        sh_total_weights = ss.get('total_weights', {})

        if sh_summary:
            if sh_summary.get('正官', 0) > 0 or sh_summary.get('七杀', 0) > 0:
                a.append({'type': '中', 'text': '官杀透干，事业心强，注意工作压力'})
            if sh_summary.get('正财', 0) > 0 or sh_summary.get('偏财', 0) > 0:
                a.append({'type': '吉', 'text': '财星显现，财运较好'})
            if sh_summary.get('正印', 0) > 0 or sh_summary.get('偏印', 0) > 0:
                a.append({'type': '吉', 'text': '印星护身，贵人相助'})
            if sh_summary.get('食神', 0) > 0 or sh_summary.get('伤官', 0) > 0:
                a.append({'type': '中', 'text': '食伤泄秀，才华出众'})

        if sh_total_weights:
            total = sh_total_weights.get('total', 0)
            if total > 0:
                for category, label in [('印星', '生扶'), ('食伤', '泄秀'), ('官杀', '克制'), ('财星', '耗身'), ('比劫', '帮身')]:
                    weight = sh_total_weights.get(category, 0)
                    if weight / total >= 0.3:
                        a.append({'type': '吉', 'text': f'{category}偏旺，{label}有力'})

        sn = ml.get('shensha', {}) if isinstance(ml, dict) else {}
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
            task_id = str(uuid.uuid4())
            self._save_meihua_input_to_redis(task_id, data)
            self.meihua_result.show_loading()
            QTimer.singleShot(80, lambda: self._do_meihua(data, task_id))
        except Exception as e:
            self.statusBar().showMessage(f'参数错误: {e}')
            traceback.print_exc()

    def _save_meihua_input_to_redis(self, task_id: str, data: dict):
        """将梅花易数起卦数据保存到Redis"""
        if not self.redis_manager:
            return
        try:
            self.redis_manager.set_task_input('meihua', task_id, data)
            self.redis_manager.set_task_status('meihua', task_id, 'pending')
            print(f"梅花易数数据已存入Redis: meihua:input:{task_id}")
        except (RedisConnectionError, RedisOperationError) as e:
            print(f"Redis存储失败: {e}")
            self.statusBar().showMessage(f'数据缓存失败: {e}')

    def _do_meihua(self, data, task_id=None):
        try:
            method, q = data['method'], data.get('question', '')
            now = datetime.now()
            hr = None
            if method == 'time':
                hr = self.meihua_calc.time_divination(now.year, now.month, now.day, now.hour, q)
            elif method == 'number':
                hr = self.meihua_calc.number_divination([data.get('num1', 3), data.get('num2', 5)], q)
            elif method == 'direction':
                hr = self.meihua_calc.direction_divination(data.get('direction', '南方'), q)
            elif method == 'text':
                hr = self.meihua_calc.text_divination(data.get('text', '梅花'), q)
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

            # ★ v5.0: 起卦完成后自动触发AI解读
            QTimer.singleShot(300, self._trigger_meihua_auto_ai)
        except Exception as e:
            self.statusBar().showMessage(f'起卦错误: {e}')
            traceback.print_exc()

    def _trigger_meihua_auto_ai(self):
        """起卦完成后自动触发AI深度解读"""
        try:
            input_data = self.meihua_input.get_data()
            hexagram_data = self.meihua_result.get_hexagram_data_for_ai()

            if not hexagram_data or not hexagram_data.get('base', {}).get('name'):
                print("自动AI解读跳过: 卦象数据不完整")
                return

            # 更新状态提示
            self.statusBar().showMessage('起卦完成 · 正在自动进行AI深度解读…')

            task_id = str(uuid.uuid4())
            self._save_meihua_input_to_redis(task_id, input_data)

            self._meihua_ai_worker = AiAnalysisWorker('meihua', input_data, hexagram_data, task_id)
            self._meihua_ai_worker.progress_updated.connect(self._on_meihua_ai_progress)
            self._meihua_ai_worker.analysis_finished.connect(self._on_meihua_ai_finished)
            self._meihua_ai_worker.analysis_failed.connect(self._on_meihua_ai_failed)
            self._meihua_ai_worker.start()
        except Exception as e:
            print(f"自动AI解读启动失败: {e}")
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

            task_id = str(uuid.uuid4())
            self._save_bazi_input_to_redis(task_id, input_data)

            self._bazi_ai_worker = AiAnalysisWorker('bazi', input_data, chart_data, task_id)
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
                f'消耗Token: {token_usage} · 耗时: {elapsed:.1f}秒 · 结果已同步至Redis'
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

            task_id = str(uuid.uuid4())
            self._save_meihua_input_to_redis(task_id, input_data)

            self._meihua_ai_worker = AiAnalysisWorker('meihua', input_data, hexagram_data, task_id)
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
                f'消耗Token: {token_usage} · 耗时: {elapsed:.1f}秒 · 结果已同步至Redis'
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

    # ===== Redis轮询机制 =====

    def _init_redis_polling(self):
        """初始化Redis轮询定时器"""
        self._bazi_polling_timer = QTimer(self)
        self._bazi_polling_timer.setInterval(1000)
        self._bazi_polling_timer.timeout.connect(self._poll_bazi_result)
        self._bazi_polling_task_id = None
        self._bazi_polling_retry_count = 0
        self._bazi_polling_max_retries = 30

        self._meihua_polling_timer = QTimer(self)
        self._meihua_polling_timer.setInterval(1000)
        self._meihua_polling_timer.timeout.connect(self._poll_meihua_result)
        self._meihua_polling_task_id = None
        self._meihua_polling_retry_count = 0
        self._meihua_polling_max_retries = 30

    def _start_bazi_polling(self, task_id: str):
        """开始八字分析结果轮询"""
        self._bazi_polling_task_id = task_id
        self._bazi_polling_retry_count = 0
        self._bazi_polling_timer.start()
        print(f"开始轮询八字分析结果: {task_id}")

    def _start_meihua_polling(self, task_id: str):
        """开始梅花易数分析结果轮询"""
        self._meihua_polling_task_id = task_id
        self._meihua_polling_retry_count = 0
        self._meihua_polling_timer.start()
        print(f"开始轮询梅花易数分析结果: {task_id}")

    def _stop_bazi_polling(self):
        """停止八字分析结果轮询"""
        self._bazi_polling_timer.stop()
        self._bazi_polling_task_id = None
        self._bazi_polling_retry_count = 0

    def _stop_meihua_polling(self):
        """停止梅花易数分析结果轮询"""
        self._meihua_polling_timer.stop()
        self._meihua_polling_task_id = None
        self._meihua_polling_retry_count = 0

    def _poll_bazi_result(self):
        """轮询八字分析结果"""
        if not self._bazi_polling_task_id or not self.redis_manager:
            self._stop_bazi_polling()
            return

        self._bazi_polling_retry_count += 1

        try:
            status = self.redis_manager.get_task_status('bazi', self._bazi_polling_task_id)
            result = self.redis_manager.get_task_result('bazi', self._bazi_polling_task_id)

            if status == 'completed' and result:
                self._stop_bazi_polling()
                self._handle_bazi_redis_result(result)
                return

            if status == 'failed' and result:
                self._stop_bazi_polling()
                self._handle_bazi_redis_error(result)
                return

            if self._bazi_polling_retry_count >= self._bazi_polling_max_retries:
                self._stop_bazi_polling()
                self.statusBar().showMessage('八字分析超时，请重试')
                QMessageBox.warning(self, '超时', 'AI分析超时，请重试')
                return

            self.statusBar().showMessage(
                f'AI分析进行中... ({self._bazi_polling_retry_count}/{self._bazi_polling_max_retries})'
            )

        except (RedisConnectionError, RedisOperationError) as e:
            self._stop_bazi_polling()
            self.statusBar().showMessage(f'Redis连接错误: {e}')
        except Exception as e:
            self._stop_bazi_polling()
            self.statusBar().showMessage(f'轮询错误: {e}')

    def _poll_meihua_result(self):
        """轮询梅花易数分析结果"""
        if not self._meihua_polling_task_id or not self.redis_manager:
            self._stop_meihua_polling()
            return

        self._meihua_polling_retry_count += 1

        try:
            status = self.redis_manager.get_task_status('meihua', self._meihua_polling_task_id)
            result = self.redis_manager.get_task_result('meihua', self._meihua_polling_task_id)

            if status == 'completed' and result:
                self._stop_meihua_polling()
                self._handle_meihua_redis_result(result)
                return

            if status == 'failed' and result:
                self._stop_meihua_polling()
                self._handle_meihua_redis_error(result)
                return

            if self._meihua_polling_retry_count >= self._meihua_polling_max_retries:
                self._stop_meihua_polling()
                self.statusBar().showMessage('梅花易数解读超时，请重试')
                QMessageBox.warning(self, '超时', 'AI解读超时，请重试')
                return

            self.statusBar().showMessage(
                f'AI解读进行中... ({self._meihua_polling_retry_count}/{self._meihua_polling_max_retries})'
            )

        except (RedisConnectionError, RedisOperationError) as e:
            self._stop_meihua_polling()
            self.statusBar().showMessage(f'Redis连接错误: {e}')
        except Exception as e:
            self._stop_meihua_polling()
            self.statusBar().showMessage(f'轮询错误: {e}')

    def _handle_bazi_redis_result(self, result: dict):
        """处理从Redis获取的八字分析结果"""
        try:
            ai_analysis = result.get('ai_analysis', {})
            self.bazi_result.display_ai_result(ai_analysis)

            token_usage = result.get('token_usage', 0)
            report_id = result.get('report_id', 0)
            self.statusBar().showMessage(
                f'AI分析完成 · 报告ID: {report_id} · '
                f'消耗Token: {token_usage}'
            )
        except Exception as e:
            self.statusBar().showMessage(f'显示AI分析结果失败: {e}')
            traceback.print_exc()

    def _handle_bazi_redis_error(self, result: dict):
        """处理从Redis获取的八字分析错误"""
        error_type = result.get('error_type', 'unknown')
        error_message = result.get('error_message', '未知错误')

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
            'redis_error': 'Redis连接错误',
            'timeout': '分析超时',
        }
        title = error_titles.get(error_type, '分析失败')

        msg_lines = error_message.split('\n')
        short_msg = msg_lines[0] if msg_lines else error_message

        QMessageBox.warning(self, title, short_msg)

    def _handle_meihua_redis_result(self, result: dict):
        """处理从Redis获取的梅花易数分析结果"""
        try:
            ai_analysis = result.get('ai_analysis', {})
            self.meihua_result.display_ai_analysis_result(ai_analysis)

            token_usage = result.get('token_usage', 0)
            report_id = result.get('report_id', 0)
            self.statusBar().showMessage(
                f'AI解读完成 · 报告ID: {report_id} · '
                f'消耗Token: {token_usage}'
            )
        except Exception as e:
            self.statusBar().showMessage(f'显示AI解读结果失败: {e}')
            traceback.print_exc()

    def _handle_meihua_redis_error(self, result: dict):
        """处理从Redis获取的梅花易数分析错误"""
        error_type = result.get('error_type', 'unknown')
        error_message = result.get('error_message', '未知错误')

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
            'redis_error': 'Redis连接错误',
            'timeout': '解读超时',
        }
        title = error_titles.get(error_type, '解读失败')

        msg_lines = error_message.split('\n')
        short_msg = msg_lines[0] if msg_lines else error_message

        QMessageBox.warning(self, title, short_msg)
