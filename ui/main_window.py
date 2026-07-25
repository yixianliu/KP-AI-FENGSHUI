"""
风水排盘专业工具 v5.0 - 精美国风主窗口
QSplitter左右分栏28%/72% · 暖米底色 · 圆角卡片 · 三色点缀 · 微动画
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QFrame, QApplication, QStatusBar,
                               QPushButton, QStackedWidget, QSplitter, QScrollArea,
                               QMessageBox, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QIcon
from pathlib import Path
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from ui.components.input_panel import InputPanel
from ui.components.result_panel import ResultPanel
from ui.components.meihua_input import MeihuaInputPanel
from ui.components.meihua_result_panel import MeihuaResultPanel
from ui.components.liuren_input import LiurenInputPanel
from ui.components.liuren_result_panel import LiurenResultPanel
from ui.components.history_panel import HistoryFilterPanel, HistoryListPanel
from ui.components.login_dialog import LoginDialog, RegisterDialog
from ui.components.settings_dialog import SettingsDialog
from ui.components.about_dialog import AboutDialog
from ui.components.ai_analysis_worker import AiAnalysisWorker
from core.bazi_calculator import BaziCalculator
from core.lunar_converter import LunarConverter
from core.calendar_utils import SolarTimeCalculator
from core.location_db import LocationDB
from core.meihua import MeiHuaCalculator
from core.hexagram_analyzer import HexagramAnalyzer
from core.liuren import LiuRenCalculator
from core.database_manager import DatabaseManager
from core.log_handler import setup_app_logging
from datetime import datetime
import traceback
import logging
import uuid

NAV = [
    {'id': 'bazi', 'name': '八字排盘', 'icon': '☯'},
    {'id': 'meihua', 'name': '梅花易数', 'icon': '⚊'},
    {'id': 'liuren', 'name': '大六壬', 'icon': '☵'},
    {'id': 'history', 'name': '历史记录', 'icon': '📜'},
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.module_hint = None
        self.setWindowTitle('风水排盘专业工具')
        self.setMinimumSize(1100, 700)
        self.resize(1400, 900)
        self.setStyleSheet(Stylesheets.MAIN)
        
        # 设置窗口图标（统一使用项目根目录下的 favicon.ico）
        icon_path = Path(__file__).resolve().parent.parent / 'favicon.ico'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # 用户状态
        self.current_user_id = None
        self.current_username = None
        self.db_manager = None

        # 统一日志（本地文件 + 存储后端 system_logs）
        try:
            setup_app_logging()
        except Exception:
            traceback.print_exc()
        self._logger = logging.getLogger(__name__)

        # 本次运行会话标识，用于把同一会话的操作聚合
        self._session_id = str(uuid.uuid4())

        self._init_fonts()
        self._init_core()
        self._init_ui()
        self._connect_signals()
        # 还原上次的界面配置（窗口几何 + 分栏比例 + 最近板块）
        self._restore_ui_settings()
        self._switch('bazi')

    def _init_fonts(self):
        QApplication.setFont(QFont("Microsoft YaHei", 10))
        QApplication.instance().setStyleSheet(Stylesheets.TOOLTIP)

    def _init_core(self):
        # 持有所有正在运行的 AI worker 引用，避免被 GC 销毁
        # （QThread: Destroyed while thread is still running）
        self._active_workers = []
        self.bazi_calc = BaziCalculator()
        self.lunar_conv = LunarConverter()
        self.solar_calc = SolarTimeCalculator()
        self.location_db = LocationDB()
        self.meihua_calc = MeiHuaCalculator()
        self.hexagram_analyzer = HexagramAnalyzer()
        self.liuren_calc = LiuRenCalculator()
        # 初始化数据库管理器
        try:
            self.db_manager = DatabaseManager()
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            self.db_manager = None
        # 最近一次排盘记录 ID（供 AI 回调更新 ai_json）
        self._last_bazi_record_id = None
        self._last_meihua_record_id = None
        self._last_liuren_record_id = None
        # ===== R4: AI 降级检测 =====
        self._ai_available = self._check_ai_availability()
        self._update_ai_buttons_state()

    def _check_ai_availability(self) -> bool:
        """探测 config.ini 是否包含 [agnes] 配置段（AI 分析所需）。"""
        import configparser
        from pathlib import Path
        cfg = configparser.ConfigParser()
        project_root = Path(__file__).resolve().parent.parent
        config_path = project_root / 'config.ini'
        cfg.read(str(config_path), encoding='utf-8')
        return cfg.has_section('agnes')

    def _update_ai_buttons_state(self):
        """根据 AI 可用性更新结果面板上的 AI 分析按钮状态"""
        if not self._ai_available:
            msg = 'AI 功能当前不可用，请检查 config.ini 中的 [agnes] 配置'
            if hasattr(self, 'bazi_result'):
                self.bazi_result.ai_analyze_btn.setVisible(False)
                self.bazi_result.set_ai_status_message(msg)
            if hasattr(self, 'meihua_result'):
                self.meihua_result.ai_analyze_btn.setVisible(False)
                self.meihua_result.set_ai_status_message(msg)
            if hasattr(self, 'liuren_result'):
                self.liuren_result.ai_analyze_btn.setVisible(False)
                self.liuren_result.set_ai_status_message(msg)

    # ===== AI worker 线程生命周期管理 =====

    def _register_worker(self, worker):
        """登记一个 AI worker，持有其引用直到运行结束再释放。

        防止两类崩溃：
        1. 局部/被覆盖的 QThread 在运行中被 Python GC 销毁；
        2. 同一属性（如 _liuren_ai_worker）被自动触发与手动按钮先后覆盖。
        worker 自身的 finished 信号触发后从登记表移除并 deleteLater。
        """
        if worker is None:
            return
        self._active_workers.append(worker)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))

    def _cleanup_worker(self, worker):
        """worker 运行结束后从登记表移除并安排销毁。"""
        try:
            if worker in self._active_workers:
                self._active_workers.remove(worker)
            worker.deleteLater()
        except (RuntimeError, ValueError):
            pass

    def _shutdown_workers(self, timeout_ms: int = 3000):
        """停止并等待所有仍在运行的 AI worker，用于关窗时安全退出。"""
        workers = list(getattr(self, '_active_workers', []))
        self._active_workers.clear()
        for worker in workers:
            try:
                if worker is None:
                    continue
                if worker.isRunning():
                    if hasattr(worker, 'stop'):
                        worker.stop()
                    if not worker.wait(timeout_ms):
                        # AI 请求为阻塞调用无法中断，超时后强制终止以避免关窗卡死
                        worker.terminate()
                        worker.wait(1000)
                else:
                    worker.deleteLater()
            except RuntimeError:
                # 底层 C++ 对象已销毁，忽略
                pass

    def closeEvent(self, event):
        """关闭窗口前停止轮询定时器并安全终止所有 AI 线程。"""
        self._shutdown_workers()
        # 退出前持久化界面配置到当前激活存储后端
        self._save_ui_settings()
        super().closeEvent(event)

    # ===== 界面配置持久化（窗口几何 / 分栏 / 最近板块） =====
    def _current_module(self) -> str:
        """返回当前激活的板块 id。"""
        for pid, btn in getattr(self, 'nav_btns', {}).items():
            if btn.isChecked():
                return pid
        return 'bazi'

    def _save_ui_settings(self) -> bool:
        """把窗口几何、分栏比例、当前板块写入当前激活后端。"""
        try:
            mgr = self.db_manager
            if mgr is None:
                return False
            geo = self.geometry()
            sizes = self.splitter.sizes() if hasattr(self, 'splitter') else [0, 0]
            settings = {
                'window_x': geo.x(),
                'window_y': geo.y(),
                'window_w': geo.width(),
                'window_h': geo.height(),
                'splitter_left': sizes[0] if len(sizes) > 0 else 0,
                'splitter_right': sizes[1] if len(sizes) > 1 else 0,
                'current_module': self._current_module(),
            }
            ok = mgr.save_ui_settings(settings)
            if ok:
                self._logger.info("[界面配置] 已保存 UI 设置")
            else:
                self._logger.warning("[界面配置] UI 设置保存失败（后端不可用？）")
            return ok
        except Exception as e:
            self._logger.warning(f"[界面配置] 保存异常：{e}")
            return False

    def _restore_ui_settings(self):
        """启动时还原上次的界面配置。还原失败静默忽略。"""
        try:
            mgr = self.db_manager
            if mgr is None:
                return
            s = mgr.load_ui_settings()
            if not s:
                return
            w = int(s.get('window_w') or 0)
            h = int(s.get('window_h') or 0)
            x = int(s.get('window_x') or 0)
            y = int(s.get('window_y') or 0)
            if w > 0 and h > 0:
                self.resize(w, h)
                if x >= 0 and y >= 0:
                    self.move(x, y)
            left = int(s.get('splitter_left') or 0)
            right = int(s.get('splitter_right') or 0)
            if left > 0 and right > 0 and hasattr(self, 'splitter'):
                QTimer.singleShot(0, lambda: self.splitter.setSizes([left, right]))
            mod = s.get('current_module')
            if mod in ('bazi', 'meihua', 'liuren', 'history'):
                # _switch 已在 __init__ 末尾调用默认 'bazi'，如需切换覆盖之
                if mod != 'bazi':
                    self._switch(mod)
            self._logger.info("[界面配置] 已还原 UI 设置")
        except Exception as e:
            self._logger.warning(f"[界面配置] 还原异常：{e}")

    def _log_op(self, op_type: str, op_object: str = '', detail: str = None) -> bool:
        """记录一条操作记录到当前激活后端（失败静默降级，不阻断 UI）。"""
        try:
            mgr = self.db_manager
            if mgr is None:
                return False
            ok = mgr.save_operation_log(
                op_type=op_type,
                op_object=op_object,
                user_id=self.current_user_id,
                session=self._session_id,
                detail=detail,
            )
            return bool(ok)
        except Exception as e:
            self._logger.warning(f"[操作记录] 写入失败：{e}")
            return False

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
        # 拉伸因子决定窗口缩放时的自适应比例（左 34 : 右 66，约 34% / 66%）
        self.splitter.setStretchFactor(0, 34)
        self.splitter.setStretchFactor(1, 66)
        # 延迟到窗口几何可用时，按可用宽度初始化（尊重最小/最大约束）
        QTimer.singleShot(0, self._apply_splitter_ratio)

        # 左侧
        self.left_stack = QStackedWidget()
        self.left_stack.setStyleSheet("background: transparent;")
        # 左侧输入面板：稳定宽度区间，避免被压窄或在大屏上留白过大
        self.left_stack.setMinimumWidth(360)
        self.left_stack.setMaximumWidth(460)
        self._build_left()
        self.splitter.addWidget(self.left_stack)

        # 右侧
        self.right_stack = QStackedWidget()
        self.right_stack.setStyleSheet("background: transparent;")
        # 右侧结果面板：自适应填满，设最小宽度防止内容被截断
        self.right_stack.setMinimumWidth(460)
        self._build_right()
        self.splitter.addWidget(self.right_stack)

        root.addWidget(self.splitter, 1)

        # 状态栏
        sb = QStatusBar()
        sb.setStyleSheet(Stylesheets.STATUS)
        sb.showMessage('风水排盘专业工具 v5.0 · 精美国风 · AI自动分析')
        self.setStatusBar(sb)
        self.module_hint = None  # 预留：当前模块提示

    def _create_navbar(self, parent):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFFFFF, stop:1 {Colors.GRADIENT_NAV_END});
                border-bottom: none;
            }}
        """)

        h = QHBoxLayout(bar)
        h.setContentsMargins(20, 0, 16, 0)
        h.setSpacing(0)

        # Logo区
        logo_container = QFrame()
        logo_container.setStyleSheet("background: transparent; border: none;")
        logo_hl = QHBoxLayout(logo_container)
        logo_hl.setContentsMargins(0, 0, 0, 0)
        logo_hl.setSpacing(6)

        logo = QLabel('☯')
        logo.setStyleSheet(f"font-size: 22px; color: {Colors.LIUJIN};")

        title = QLabel('风水排盘')
        title.setStyleSheet(f"""
            font-size: 17px;
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
            letter-spacing: 2px;
        """)

        logo_hl.addWidget(logo)
        logo_hl.addWidget(title)
        h.addWidget(logo_container)
        h.addSpacing(28)

        # 导航按钮组 - 改为胶囊式切换
        nav_container = QFrame()
        nav_container.setStyleSheet(f"""
            background: {Colors.HOVER};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_LG};
            padding: 2px;
        """)
        nav_hl = QHBoxLayout(nav_container)
        nav_hl.setContentsMargins(4, 4, 4, 4)
        nav_hl.setSpacing(0)

        self.nav_btns = {}
        for item in NAV:
            btn = QPushButton(item['icon'] + ' ' + item['name'])
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Colors.TEXT2};
                    border: none;
                    border-radius: {Spacing.RADIUS};
                    font-size: {Fonts.SZ_BODY};
                    font-family: {Fonts.BODY};
                    padding: 4px 20px;
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

        # 用户登录按钮 - 简化
        self.user_btn = QPushButton('👤 登录')
        self.user_btn.setCursor(Qt.PointingHandCursor)
        self.user_btn.setFixedHeight(30)
        self.user_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.QINGHUA};
                border: 1px solid {Colors.QINGHUA_LIGHT};
                border-radius: {Spacing.RADIUS_SM};
                font-size: {Fonts.SZ_SMALL};
                font-family: {Fonts.BODY};
                padding: 3px 12px;
            }}
            QPushButton:hover {{
                background: {Colors.QINGHUA_GLOW};
            }}
        """)
        self.user_btn.clicked.connect(self._on_user_btn_clicked)
        h.addWidget(self.user_btn)

        # 设置按钮（存储后端切换 / 界面配置）
        self.settings_btn = QPushButton('⚙')
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setToolTip('设置 · AI 模型配置 + 存储方式切换')
        self.settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.QINGHUA};
                border: 1px solid {Colors.QINGHUA_LIGHT};
                border-radius: {Spacing.RADIUS_SM};
                font-size: 16px;
            }}
            QPushButton:hover {{
                background: {Colors.QINGHUA_GLOW};
            }}
        """)
        self.settings_btn.clicked.connect(self._show_settings_dialog)
        h.addWidget(self.settings_btn)

        # 关于按钮
        self.about_btn = QPushButton('\U0001F4CB')
        self.about_btn.setCursor(Qt.PointingHandCursor)
        self.about_btn.setFixedSize(30, 30)
        self.about_btn.setToolTip('关于 / 联系我')
        self.about_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.QINGHUA};
                border: 1px solid {Colors.QINGHUA_LIGHT};
                border-radius: {Spacing.RADIUS_SM};
                font-size: 16px;
            }}
            QPushButton:hover {{
                background: {Colors.QINGHUA_GLOW};
            }}
        """)
        self.about_btn.clicked.connect(self._show_about_dialog)
        h.addWidget(self.about_btn)

        parent.addWidget(bar)

    def _build_left(self):
        self.bazi_input = InputPanel()
        self.left_stack.addWidget(self.bazi_input)
        self.meihua_input = MeihuaInputPanel()
        self.left_stack.addWidget(self.meihua_input)
        self.liuren_input = LiurenInputPanel()
        self.left_stack.addWidget(self.liuren_input)
        self.history_left = HistoryFilterPanel()
        self.left_stack.addWidget(self.history_left)

    def _build_right(self):
        self.bazi_result = ResultPanel()
        self.right_stack.addWidget(self.bazi_result)
        self.meihua_result = MeihuaResultPanel()
        self.right_stack.addWidget(self.meihua_result)
        self.liuren_result = LiurenResultPanel()
        self.right_stack.addWidget(self.liuren_result)
        self.history_right = HistoryListPanel(self.db_manager, lambda: self.current_user_id)
        self.right_stack.addWidget(self.history_right)

    def _apply_splitter_ratio(self):
        """按约 34%/66% 初始化左右分栏尺寸，并尊重最小/最大宽度约束。

        窗口缩放时由 QSplitter 依据 stretch 因子自适应维持比例；
        左侧触及上限（大屏）后右侧继续填满剩余空间，实现自适应。
        """
        w = self.width()
        if w <= 0:
            w = 1400
        avail = max(w, self.left_stack.minimumWidth() + self.right_stack.minimumWidth())
        left_target = int(avail * 0.34)
        left = max(self.left_stack.minimumWidth(),
                   min(self.left_stack.maximumWidth(), left_target))
        self.splitter.setSizes([left, avail - left])

    def _switch(self, pid):
        for k, b in self.nav_btns.items():
            b.setChecked(k == pid)
        idx = {'bazi': 0, 'meihua': 1, 'liuren': 2, 'history': 3}
        self.left_stack.setCurrentIndex(idx.get(pid, 0))
        self.right_stack.setCurrentIndex(idx.get(pid, 0))
        if pid == 'history' and hasattr(self, 'history_right'):
            self.history_right.load()
        self._log_op('switch_module', pid)

    def _on_load_history_record(self, rec):
        """把历史记录载入到八字结果面板"""
        self._switch('bazi')
        result = rec.get('result', {}) or {}
        self.bazi_result.display_result(result)

    def _connect_signals(self):
        self.bazi_input.submit_btn.clicked.connect(self._on_bazi)
        self.bazi_input.reset_btn.clicked.connect(self._on_bazi_reset)
        self.bazi_result.refresh_btn.clicked.connect(self._on_bazi)
        self.bazi_result.ai_analyze_btn.clicked.connect(self._on_bazi_ai_analyze)
        self.meihua_input.submit_btn.clicked.connect(self._on_meihua)
        self.meihua_input.reset_btn.clicked.connect(self._on_meihua_reset)
        self.meihua_result.ai_analyze_btn.clicked.connect(self._on_meihua_ai_analyze)
        self.liuren_input.submit_btn.clicked.connect(self._on_liuren)
        self.liuren_input.reset_btn.clicked.connect(self._on_liuren_reset)
        self.liuren_result.ai_analyze_btn.clicked.connect(self._on_liuren_ai_analyze)
        # 历史记录面板联动
        self.history_left.filter_changed.connect(self.history_right.load)
        self.history_right.load_to_bazi.connect(self._on_load_history_record)

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
        self._log_op('login', username)
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
        self._log_op('logout', self.current_username or '')
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

    def _show_settings_dialog(self):
        """打开设置对话框（存储方式热切换）。"""
        try:
            dlg = SettingsDialog(self)
            dlg.exec()
        except Exception as e:
            self._logger.error(f"[设置] 打开设置对话框失败：{e}")
            traceback.print_exc()

    def _show_about_dialog(self):
        """打开关于对话框。"""
        try:
            dlg = AboutDialog(self)
            dlg.exec()
        except Exception as e:
            self._logger.error(f"[关于] 打开关于对话框失败：{e}")
            traceback.print_exc()

    def _save_pan_record(self, data: dict, result: dict, pan_type: str, ai_result: dict = None):
        """保存排盘记录到数据库。返回值: record_id 或 None"""
        if not self.db_manager or self.current_user_id is None:
            return None

        try:
            birth_date = f"{data.get('year', '')}-{data.get('month', ''):02d}-{data.get('day', ''):02d}"
            birth_time = f"{data.get('hour', 0):02d}:{data.get('minute', 0):02d}"

            record_id = self.db_manager.save_pan_record(
                user_id=self.current_user_id,
                name=data.get('name', '未命名'),
                gender=data.get('gender', ''),
                birth_date=birth_date,
                birth_time=birth_time,
                city=data.get('location') or data.get('city', ''),
                pan_type=pan_type,
                result=result,
                ai_analysis=ai_result
            )

            if record_id:
                # 记录当前模块的最后一条 record_id，供 AI 回调更新 ai_json
                if pan_type == '八字排盘':
                    self._last_bazi_record_id = record_id
                elif pan_type == '梅花易数':
                    self._last_meihua_record_id = record_id
                elif pan_type == '大六壬':
                    self._last_liuren_record_id = record_id
                self.statusBar().showMessage(f'排盘完成 · 已保存到数据库 · 记录ID: {record_id}')
            else:
                self.statusBar().showMessage('排盘完成 · 保存到数据库失败')
                self._logger.warning(f"[排盘] 保存记录失败，record_id={record_id}")
        except Exception as e:
            self._logger.error(f"[排盘] 保存排盘记录失败: {e}", exc_info=True)
            self.statusBar().showMessage('排盘完成 · 保存到数据库失败')
            return None

        return record_id

    # ===== 八字 =====
    def _on_bazi(self):
        try:
            data = self.bazi_input.get_data()
            task_id = str(uuid.uuid4())
            self.bazi_result.show_loading()
            QTimer.singleShot(80, lambda: self._do_bazi(data, task_id))
        except Exception as e:
            self.statusBar().showMessage(f'参数错误: {e}')
            traceback.print_exc()

    def _do_bazi(self, data, task_id=None):
        try:
            y, m, d, hh, mm = data['year'], data['month'], data['day'], data['hour'], data['minute']
            longitude = data['longitude']
            latitude = data.get('latitude', 30.0)
            is_lunar = data['is_lunar']
            gender = data.get('gender', '男')

            # 出生地解析：手动文本 -> 经纬度（本地库优先，其次 AI，兜底默认）
            loc_text = (data.get('location') or '').strip()
            if loc_text:
                longitude, latitude = self._resolve_location(loc_text, longitude, latitude)
                data['longitude'] = longitude
                data['latitude'] = latitude
                data['location'] = loc_text

            if is_lunar:
                sol = self.lunar_conv.lunar_to_solar(y, m, d)
                if not sol:
                    self.statusBar().showMessage('农历转换失败：日期无效')
                    QMessageBox.warning(self, '输入错误', '农历日期无效，请检查年月日是否正确。')
                    return
                y, m, d = sol

            dt = datetime(y, m, d, hh, mm)
            sdt = self.solar_calc.get_true_solar_time(dt, longitude)

            bazi = self.bazi_calc.calculate(y, m, d, hh, mm, longitude, is_lunar=False)
            li = self.lunar_conv.solar_to_lunar(y, m, d)

            wx = self.bazi_calc.get_wuxing(bazi)
            ss = self.bazi_calc.get_shishen(bazi)
            ml = self.bazi_calc.get_mingli(bazi)

            # 计算大运流年（使用YunShiCalculator）
            try:
                from core.yunshi import YunShiCalculator
                yunshi_calc = YunShiCalculator()
                dayun = yunshi_calc.calculate_major_fortune(bazi, gender, y, birth_dt=sdt)
                liunian = yunshi_calc.calculate_annual_fortune(bazi, start_year=datetime.now().year, years_count=10)
            except Exception as e:
                self._logger.warning(f"[八字] 大运流年计算失败: {e}")
                dayun = {'periods': [], 'direction': '顺行'}
                liunian = {'years': []}

            try:
                shier_shen_raw = self.bazi_calc.get_shier_shen(bazi)
                shier_shen = {}
                for item in shier_shen_raw.get('shier_shen', []):
                    shier_shen[item['pillar']] = {
                        'name': item.get('shier_shen', ''),
                        'description': item.get('description', ''),
                        'ganzhi': item.get('ganzhi', ''),
                    }
            except Exception as e:
                self._logger.warning(f"[八字] 十二长生计算失败: {e}")
                shier_shen = {}

            # ★ 类型字段：计算日主强弱 / 格局类型 / 五行旺衰类别（命局类型）
            bazi_types = self._compute_bazi_types(bazi, wx)

            # ★ 运程总结：事业 / 财运 / 健康 / 感情（规则引擎，离线可跑）
            try:
                from core.yuncheng import YunChengAnalyzer
                yuncheng = YunChengAnalyzer().analyze(bazi, wx, ss, bazi_types)
            except Exception as e:
                self._logger.warning(f"[八字] 运程总结生成失败: {e}")
                yuncheng = {}

            wuxing_summary = {}
            for k in ('木', '火', '土', '金', '水'):
                v = wx.get(k, {})
                if isinstance(v, int):
                    wuxing_summary[k] = v
                else:
                    wuxing_summary[k] = round(v.get('score', 0), 2)

            result = {
                'basic_info': {
                    'pan_type': bazi_types.get('pan_type', '八字四柱'),
                    'solar_date': f'{y}年{m}月{d}日',
                    'lunar_date': f'{li[0]}年{li[1]}月{li[2]}日' if li else bazi.get('lunar_date', '-'),
                    'hour': f'{sdt.hour:02d}:{sdt.minute:02d}',
                    'location': data.get('location') or '-',
                    'gender': gender,
                    'solar_time': bazi.get('solar_time', ''),
                    'original_time': bazi.get('original_time', ''),
                    'longitude': longitude,
                    'latitude': latitude,
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
                'liunian': liunian,
                'shier_shen': shier_shen,
                'analysis': self._analysis(ml, ss),
                'bazi_types': bazi_types,
                'yuncheng': yuncheng,
            }
            self._save_pan_record(data, result, '八字排盘')

            # 操作记录（写入当前激活存储后端，算命内容本身不进统一层）
            self._log_op('bazi_divination', data.get('name', '未命名'),
                         f"{data.get('year','')}-{data.get('month','')}-{data.get('day','')} {data.get('hour','')}:{data.get('minute','')} {data.get('location') or ''}".strip())

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
                self._logger.debug("[AI] 自动AI分析跳过: 排盘数据不完整")
                return

            # 更新状态提示
            self.statusBar().showMessage('排盘完成 · 正在自动进行AI深度分析…')

            task_id = str(uuid.uuid4())

            self._bazi_ai_worker = AiAnalysisWorker('bazi', input_data, chart_data, task_id)
            self._bazi_ai_worker.progress_updated.connect(self._on_bazi_ai_progress)
            self._bazi_ai_worker.analysis_finished.connect(self._on_bazi_ai_finished)
            self._bazi_ai_worker.analysis_failed.connect(self._on_bazi_ai_failed)
            self._register_worker(self._bazi_ai_worker)
            self._bazi_ai_worker.start()
        except Exception as e:
            self._logger.error("[八字] 自动AI分析启动失败: %s", e, exc_info=True)

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

    def _resolve_location(self, text, fallback_lon=120.0, fallback_lat=30.0):
        """将出生地文本解析为（经度, 纬度）。

        解析优先级：
        1) 本地城市库（core.location_db）子串匹配，离线、即时；
        2) 否则交给 AGNES AI 解析经纬度/时区；
        3) 均失败则回退默认（120.0, 30.0）。
        """
        # 1) 本地城市库优先
        try:
            from core.location_db import LocationDB
            db = LocationDB()
            hits = db.search_city(text)
            if not hits:
                short = text.rstrip('省市县区自治州盟')
                hits = db.search_city(short)
            if not hits:
                for c in db.get_all_cities():
                    if c and c in text:
                        hits = [c]
                        break
            if hits:
                lon, lat = db.get_coords(hits[0])
                self._logger.info(f"出生地「{text}」命中本地库：{hits[0]} ({lon}, {lat})")
                return float(lon), float(lat)
        except Exception as e:
            self._logger.debug(f"本地城市库解析失败（转 AI）：{e}")

        # 2) AI 地理解析（加超时保护）
        try:
            from api.agnes_client import get_agnes_client, AgnesClient
            client = get_agnes_client()
            prompt = (
                f"请解析出生地「{text}」的地理坐标，"
                f"仅返回一个 JSON 对象，不要任何解释："
                f'{{"longitude": 数值, "latitude": 数值, "timezone": "Asia/Shanghai"}}'
            )
            resp = client.chat_completion(
                [{'role': 'user', 'content': prompt}],
                temperature=0.0, max_tokens=256,
            )
            content = (resp or {}).get('content', '')
            from api.agnes_client import AgnesClient
            cleaned = AgnesClient._clean_json_response(content)
            import json
            obj = json.loads(cleaned)
            lon = float(obj['longitude'])
            lat = float(obj['latitude'])
            print(f"出生地「{text}」AI 解析：({lon}, {lat})")
            return lon, lat
        except Exception as e:
            self._logger.debug(f"AI 地理解析失败（用默认经度）：{e}")

        # 3) 兜底
        return float(fallback_lon), float(fallback_lat)

    def _compute_bazi_types(self, bazi, wx):
        """计算八字命局类型：日主强弱 / 格局类型 / 五行旺衰类别

        将分散在 GeJuAnalyzer、WuXingAnalyzer 中的类型判定汇聚为单一结构，
        并补全每种类型的含义与用途，使『类型』字段在排盘结果中具备参考价值。
        格局分析依赖数据库命理数据，失败仅跳过类型展示，不影响主排盘。
        """
        from core.bazi_types import get_bazi_types_payload

        strength = ''
        geju_type = ''
        geju_name = ''
        geju_desc = ''
        rizhu_wx = wx.get('rizhu_wx', '') if isinstance(wx, dict) else ''

        try:
            from core.geju_analyzer import GeJuAnalyzer
            analyzer = GeJuAnalyzer()
            geju = analyzer.analyze(bazi, wx, bazi.get('month_zhi'))
            wangshuai = geju.get('wangshuai', {}) or {}
            strength = wangshuai.get('level', '')
            geju_type = geju.get('geju_type', '')
            geju_name = geju.get('main_geju', '')
            geju_desc = geju.get('description', '')
        except Exception as e:
            self._logger.warning(f"[八字] 格局类型分析失败（已跳过）: {e}")
            traceback.print_exc()

        wuxing_summary = wx.get('summary', '') if isinstance(wx, dict) else ''

        from core.bazi_types import get_yongshen
        yongshen = get_yongshen(rizhu_wx, strength) if rizhu_wx else {}

        return get_bazi_types_payload(
            pan_type_code='bazi',
            strength=strength,
            geju_type=geju_type,
            geju_name=geju_name,
            geju_desc=geju_desc,
            wuxing_summary=wuxing_summary,
            rizhu_wx=rizhu_wx,
            yongshen=yongshen,
        )

    def _on_bazi_reset(self):
        self.bazi_input.clear()
        self.bazi_result.clear()

    # ===== 梅花 =====
    def _on_meihua(self):
        try:
            data = self.meihua_input.get_data()
            task_id = str(uuid.uuid4())
            self.meihua_result.show_loading()
            QTimer.singleShot(80, lambda: self._do_meihua(data, task_id))
        except Exception as e:
            self.statusBar().showMessage(f'参数错误: {e}')
            traceback.print_exc()


    def _do_meihua(self, data, task_id=None):
        try:
            method = data.get('method')
            if not method:
                raise ValueError("起卦方式未选择")

            q = data.get('question', '')

            # 按起卦方式分发到不同算法
            hr = None
            if method == 'stroke':
                char = data.get('char', '')
                if not char or len(char) != 1 or not ('\u4e00' <= char <= '\u9fff'):
                    raise ValueError(f"笔画起卦需输入单个汉字，当前: {char!r}")
                hr = self.meihua_calc.stroke_divination(char, q)
            elif method == 'number':
                numbers = data.get('numbers', [])
                if not isinstance(numbers, list) or len(numbers) < 2:
                    raw = data.get('num_input', '')
                    if raw:
                        try:
                            numbers = [int(n.strip()) for n in raw.split(',') if n.strip()]
                        except ValueError:
                            pass
                if not isinstance(numbers, list) or len(numbers) < 2:
                    raise ValueError("数字起卦需提供至少两个数字")
                hr = self.meihua_calc.number_divination(numbers, q)
            elif method == 'direction':
                direction = data.get('direction', '')
                if not direction:
                    raise ValueError("方位起卦需提供方位")
                hr = self.meihua_calc.direction_divination(direction, q)
            elif method == 'text':
                text = data.get('text', '')
                if not text:
                    raise ValueError("文字起卦需提供文字内容")
                hr = self.meihua_calc.text_divination(text, q)
            elif method == 'copper_coin':
                six_lines = data.get('six_lines', [])
                if not six_lines or len(six_lines) != 6:
                    raise ValueError("铜钱摇卦需提供完整的6爻")
                hr = self.meihua_calc.copper_coin_divination(six_lines, q)
            elif method == 'time':
                year = data.get('year')
                month = data.get('month')
                day = data.get('day')
                hour = data.get('hour')
                if not all([year, month, day, hour]):
                    raise ValueError("时间起卦需要完整的年月日时")
                hr = self.meihua_calc.time_divination(year, month, day, hour, q)
            else:
                raise ValueError(f"未知起卦方式: {method}")

            if not hr:
                return

            all_hex = self.meihua_calc.generate_all_hexagrams(hr)
            analysis = self.hexagram_analyzer.analyze_divination(hr, all_hex)
            base = analysis.get('base', {})
            result = {
                'basic_info': {'method': hr.get('method', ''), 'question': q, 'time': datetime.now().strftime('%Y年%m月%d日 %H:%M'), 'moving_yao': ''},
                'overall': {'level': analysis.get('overall_judgment', '平'), 'overall': base.get('description', '')},
                'ben_gua': base, 'hu_gua': analysis.get('hu', {}), 'bian_gua': analysis.get('bian', {}),
                'cuo_gua': analysis.get('cuo', {}), 'zong_gua': analysis.get('zong', {}),
                'yao_list': base.get('yao_ci', []), 'suggestions': analysis.get('suggestions', []),
                'divination_extra': hr,  # 保存完整起卦结果（含铜钱摇卦six_lines/笔画起卦char等），供AI分析使用
            }
            self.meihua_result.display_result(result)
            self.statusBar().showMessage('梅花易数起卦完成')

            # 保存到数据库（梅花易数也支持保存）
            record_id = self._save_pan_record(data, result, '梅花易数')
            if record_id:
                self.statusBar().showMessage(f'梅花易数起卦完成 · 记录ID: {record_id}')

            # 操作记录
            self._log_op('meihua_divination', method,
                         f"question={q}" if q else f"method={method}")

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
                self._logger.debug("[AI] 自动AI解读跳过: 卦象数据不完整")
                return

            # 更新状态提示
            self.statusBar().showMessage('起卦完成 · 正在自动进行AI深度解读…')

            task_id = str(uuid.uuid4())

            self._meihua_ai_worker = AiAnalysisWorker('meihua', input_data, hexagram_data, task_id)
            self._meihua_ai_worker.progress_updated.connect(self._on_meihua_ai_progress)
            self._meihua_ai_worker.analysis_finished.connect(self._on_meihua_ai_finished)
            self._meihua_ai_worker.analysis_failed.connect(self._on_meihua_ai_failed)
            self._register_worker(self._meihua_ai_worker)
            self._meihua_ai_worker.start()
        except Exception as e:
            self._logger.error("[梅花] 自动AI解读启动失败: %s", e, exc_info=True)

    def _on_meihua_reset(self):
        self.meihua_input.clear()
        self.meihua_result.clear()

    # ===== 大六壬 =====
    def _on_liuren(self):
        try:
            data = self.liuren_input.get_data()
            task_id = str(uuid.uuid4())
            self.liuren_result.show_loading()
            QTimer.singleShot(80, lambda: self._do_liuren(data, task_id))
        except Exception as e:
            self.statusBar().showMessage(f'参数错误: {e}')
            traceback.print_exc()


    def _do_liuren(self, data, task_id=None):
        try:
            method = data['method']
            q = data.get('question', '')
            hr = self.liuren_calc.calc(
                method=method,
                year=data.get('year'),
                month=data.get('month'),
                day=data.get('day'),
                hour=data.get('hour'),
                question=q,
                zhan_shi=data.get('zhan_shi'),
            )
            if not hr:
                return
            self.liuren_result.display_result(hr)
            self.statusBar().showMessage('大六壬起课完成')
            record_id = self._save_pan_record(data, hr, '大六壬')
            if record_id:
                self.statusBar().showMessage(f'大六壬起课完成 · 记录ID: {record_id}')
            self._log_op('liuren_divination', method, f"question={q}" if q else f"method={method}")
            QTimer.singleShot(300, self._trigger_liuren_auto_ai)
        except Exception as e:
            self.statusBar().showMessage(f'起课错误: {e}')
            traceback.print_exc()

    def _trigger_liuren_auto_ai(self):
        """起课后自动触发AI深度解读"""
        try:
            input_data = self.liuren_input.get_data()
            liuren_data = self.liuren_result.get_liuren_data_for_ai()

            if not liuren_data or not liuren_data.get('san_chuan'):
                self._logger.debug("[AI] 自动AI解读跳过: 起课数据不完整")
                return

            self.statusBar().showMessage('起课完成 · 正在自动进行AI深度解读…')

            task_id = str(uuid.uuid4())

            self._liuren_ai_worker = AiAnalysisWorker('liuren', input_data, liuren_data, task_id)
            self._liuren_ai_worker.progress_updated.connect(self._on_liuren_ai_progress)
            self._liuren_ai_worker.analysis_finished.connect(self._on_liuren_ai_finished)
            self._liuren_ai_worker.analysis_failed.connect(self._on_liuren_ai_failed)
            self._register_worker(self._liuren_ai_worker)
            self._liuren_ai_worker.start()
        except Exception as e:
            self._logger.error("[六壬] 自动AI解读启动失败: %s", e, exc_info=True)

    def _on_liuren_reset(self):
        self.liuren_input.clear()
        self.liuren_result.clear()

    def _on_liuren_ai_analyze(self):
        """大六壬AI分析按钮点击处理"""
        try:
            input_data = self.liuren_input.get_data()
            liuren_data = self.liuren_result.get_liuren_data_for_ai()

            if not liuren_data or not liuren_data.get('san_chuan'):
                QMessageBox.warning(self, '提示', '请先起课，再使用AI解读功能')
                return

            self.liuren_result.show_ai_loading('AI正在解读六壬玄机…')
            self.statusBar().showMessage('AI解读进行中，请稍候…')

            task_id = str(uuid.uuid4())

            self._liuren_ai_worker = AiAnalysisWorker('liuren', input_data, liuren_data, task_id)
            self._liuren_ai_worker.progress_updated.connect(self._on_liuren_ai_progress)
            self._liuren_ai_worker.analysis_finished.connect(self._on_liuren_ai_finished)
            self._liuren_ai_worker.analysis_failed.connect(self._on_liuren_ai_failed)
            self._register_worker(self._liuren_ai_worker)
            self._liuren_ai_worker.start()
        except Exception as e:
            self.statusBar().showMessage(f'AI解读启动失败: {e}')
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'AI解读启动失败: {e}')

    def _on_liuren_ai_progress(self, stage: str, message: str):
        """大六壬AI分析进度更新"""
        status_messages = {
            'validating': '正在验证输入数据…',
            'initializing': '正在初始化AI分析引擎…',
            'analyzing': 'AI正在解读六壬玄机…',
            'completed': '分析完成！'
        }
        status = status_messages.get(stage, message)
        self.statusBar().showMessage(status)

    def _on_liuren_ai_finished(self, result: dict):
        """大六壬AI分析完成"""
        try:
            ai_analysis = result.get('ai_analysis', {})
            self.liuren_result.display_ai_analysis_result(ai_analysis)

            token_usage = result.get('token_usage', 0)
            report_id = result.get('report_id', 0)
            elapsed = result.get('elapsed_seconds', 0)

            # 更新数据库：将 AI 分析结果写入 pan_records.ai_json
            if self.db_manager and self.current_user_id and hasattr(self, '_last_liuren_record_id'):
                try:
                    last_id = self._last_liuren_record_id
                    if last_id:
                        self.db_manager.update_pan_ai_result(last_id, ai_analysis)
                except Exception as e:
                    self._logger.warning(f"[AI] 更新六壬AI分析结果到数据库失败: {e}")

            self.statusBar().showMessage(
                f'AI解读完成 · 报告ID: {report_id} · '
                f'消耗Token: {token_usage} · 耗时: {elapsed:.1f}秒'
            )
        except Exception as e:
            self.statusBar().showMessage(f'显示AI分析结果失败: {e}')
            traceback.print_exc()

    def _on_liuren_ai_failed(self, error_type: str, error_message: str):
        """大六壬AI分析失败"""
        self.liuren_result.display_result(getattr(self.liuren_result, '_current_result', {}))
        self.liuren_result.ai_analyze_btn.setVisible(True)
        self.liuren_result.ai_analyze_btn.setEnabled(True)
        self.statusBar().showMessage(f'AI解读失败: {error_type}')

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

            self._bazi_ai_worker = AiAnalysisWorker('bazi', input_data, chart_data, task_id)
            self._bazi_ai_worker.progress_updated.connect(self._on_bazi_ai_progress)
            self._bazi_ai_worker.analysis_finished.connect(self._on_bazi_ai_finished)
            self._bazi_ai_worker.analysis_failed.connect(self._on_bazi_ai_failed)
            self._register_worker(self._bazi_ai_worker)
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

            # 更新数据库：将 AI 分析结果写入 pan_records.ai_json
            if self.db_manager and self.current_user_id and hasattr(self, '_last_bazi_record_id'):
                try:
                    last_id = self._last_bazi_record_id
                    if last_id:
                        self.db_manager.update_pan_ai_result(last_id, ai_analysis)
                except Exception as e:
                    self._logger.warning(f"[AI] 更新八字AI分析结果到数据库失败: {e}")

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

            task_id = str(uuid.uuid4())

            self._meihua_ai_worker = AiAnalysisWorker('meihua', input_data, hexagram_data, task_id)
            self._meihua_ai_worker.progress_updated.connect(self._on_meihua_ai_progress)
            self._meihua_ai_worker.analysis_finished.connect(self._on_meihua_ai_finished)
            self._meihua_ai_worker.analysis_failed.connect(self._on_meihua_ai_failed)
            self._register_worker(self._meihua_ai_worker)
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

            # 更新数据库：将 AI 分析结果写入 pan_records.ai_json
            if self.db_manager and self.current_user_id and hasattr(self, '_last_meihua_record_id'):
                try:
                    last_id = self._last_meihua_record_id
                    if last_id:
                        self.db_manager.update_pan_ai_result(last_id, ai_analysis)
                except Exception as e:
                    self._logger.warning(f"[AI] 更新梅花AI分析结果到数据库失败: {e}")

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

