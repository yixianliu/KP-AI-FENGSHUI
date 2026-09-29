"""
风水排盘专业工具 - 精美国风主窗口
QSplitter左右分栏 · 暖米底色 · 圆角卡片 · 三色点缀 · 微动画
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QFrame, QApplication, QStatusBar,
                               QPushButton, QStackedWidget, QSplitter,
                               QMessageBox, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal
from PySide6.QtGui import QFont, QIcon
from ui.styles import Stylesheets, Colors, Fonts, Spacing, FOCUS_BORDER
from core.path_utils import get_resource_path
from core.app_version import get_version_label, APP_NAME
from ui.components.input_panel import InputPanel
from ui.components.result_panel import ResultPanel
from ui.components.meihua_input import MeihuaInputPanel
from ui.components.meihua_result_panel import MeihuaResultPanel
from ui.components.liuren_input import LiurenInputPanel
from ui.components.liuren_result_panel import LiurenResultPanel
from ui.components.xuan_kong_input import XuanKongInputPanel
from ui.components.xuan_kong_result_panel import XuanKongResultPanel
from ui.components.settings_dialog import SettingsDialog
from ui.components.about_dialog import AboutDialog
from ui.components.ai_analysis_worker import AiAnalysisWorker
from core.bazi.bazi_calculator import BaziCalculator
from core.lunar_converter import LunarConverter
from core.calendar_utils import SolarTimeCalculator
from core.location_db import LocationDB
from core.divination.meihua import MeiHuaCalculator
from core.divination.hexagram_analyzer import HexagramAnalyzer
from core.divination.liuren import LiuRenCalculator
from core.fengshui.xuan_kong import XuanKongCalculator, xuan_kong_divination
from core.log_handler import setup_app_logging
from datetime import datetime
import traceback
import logging
import uuid
import sys

NAV = [
    {'id': 'bazi', 'name': '八字排盘', 'icon': '☯'},
    {'id': 'meihua', 'name': '梅花易数', 'icon': '⚊'},
    {'id': 'liuren', 'name': '大六壬', 'icon': '☵'},
    {'id': 'xuan_kong', 'name': '玄空飞星', 'icon': '⛰'},
]

# M2-1：路由单一真相源（修 Q13）。由 NAV 顺序派生，消除 _switch / _restore_ui_settings
# 两处硬编码索引；新增板块只需在 NAV 追加一项，索引自动同步。
NAV_INDEX = {item['id']: i for i, item in enumerate(NAV)}
VALID_MODULES = tuple(NAV_INDEX.keys())  # ('bazi', 'meihua', 'liuren', 'xuan_kong')

# 注：原 `SIDEBAR_WIDTH = 168`（Q15 死常量）已删除——真实导航是顶部栏，
# 该常量仅被 e2e 脚本断言引用，无任何布局依赖。


class MainWindow(QMainWindow):
    """应用主窗口：承载八字 / 梅花易数 / 大六壬三大板块。

    采用三层架构的 UI 层（PySide6）：通过 QSplitter 左右分栏（输入面板 + 结果面板），
    顶部胶囊式导航切换板块，并调度 core 业务层完成排盘与龙虎山大师兄（AI）分析。
    负责 worker 线程生命周期、界面配置持久化与操作日志记录。
    """
    # M2-2：密度档变化信号（tuple: (页面边距, 卡片间距, 卡片内距, 行高)），
    # 四结果面板订阅 on_density_changed 槽统一刷新边距（M3-1 连接）。
    density_changed = Signal(tuple)
    # M2-2：左栏占比常量（标准双栏约 34%），纵向模式按 0.4 分配高度。
    SPLIT_LEFT_RATIO = 0.34

    def __init__(self):
        """初始化主窗口：设置窗口元数据、日志、会话标识，并依次完成字体、core、UI、信号绑定与配置还原。"""
        super().__init__()
        self.module_hint = None
        self.setWindowTitle('风水排盘专业工具')
        # M2-2（Q12）：最小尺寸由 1100×700 下调，允许窄窗口。
        # 假设（文档矛盾）：计划写 setMinimumSize(900,640) 且 BP_XS=900（XS 为 <900），
        # 但 QWidget.resize 受 minimumWidth 钳制，min=900 时窗口永远 >=900，XS 单栏档
        # 不可达（与计划「允许 XS 档」的意图相悖，且验收用例 resize(860)→Vertical 无法满足）。
        # 故取 800 使 XS(<900) 可达，同时仍 >= 常见上网本有效宽度。
        self.setMinimumSize(800, 560)
        self.resize(1400, 900)
        self._last_bp = None  # 断点缓存（resizeEvent 短路用，M2-2）
        self.setStyleSheet(Stylesheets.MAIN)
        
        # 设置窗口图标（统一使用资源目录下的 favicon.ico）
        icon_path = get_resource_path('favicon.ico')
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # DB 由 _init_core → _init_db_async 在后台线程打开；这里仅初始化占位属性
        self._db_manager = None
        self._db_manager_ready = False

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

    def showEvent(self, event):
        super().showEvent(event)

    def _init_fonts(self):
        """设置全局默认字体（微软雅黑）与工具提示样式表。"""
        QApplication.setFont(QFont("Microsoft YaHei", 10))
        # 追加工具提示样式而不是替换整个样式表
        current_style = QApplication.instance().styleSheet()
        QApplication.instance().setStyleSheet(current_style + Stylesheets.TOOLTIP)

    def _init_core(self):
        """初始化 core 业务层与数据库，并准备 AI 状态管理。

        排盘计算器（八字/农历/真太阳时/地点/梅花/六壬）与 BaziService 改为惰性
        构造（见下方 @property，首次 _do_* 用户操作时才实例化），避免冷启动一次性
        阻塞约 600+ ms。DatabaseManager 由后台线程异步打开（见 _init_db_async），
        避免约 1s 的冷 SQLite 读阻塞首帧；_restore_ui_settings 就绪前按默认布局，
        就绪后自动重试。
        初始化 AI worker 登记表、最近记录 ID，并探测 AI 可用性、刷新按钮状态、
        订阅配置热更新。
        """
        # 持有所有正在运行的 AI worker 引用，避免被 GC 销毁
        # （QThread: Destroyed while thread is still running）
        self._active_workers = []
        # 计算器与 Service 改为惰性构造（见下方 @property），避免冷启动阻塞
        self._bazi_calc = None
        self._lunar_conv = None
        self._solar_calc = None
        self._location_db = None
        self._meihua_calc = None
        self._hexagram_analyzer = None
        self._liuren_calc = None
        self._bazi_service = None
        # DatabaseManager 由后台线程异步打开（见 _init_db_async）
        self._db_manager = None
        self._db_manager_ready = False
        self._init_db_async()
        # 最近一次排盘记录 ID（供 AI 回调更新 ai_json）
        self._last_bazi_record_id = None
        self._last_meihua_record_id = None
        self._last_liuren_record_id = None
        # 最近一次八字输入（含出生日期/地点）
        self._last_bazi_input = None
        # 最近一次大六壬完整排盘结果（供 AI 解读使用）
        self._last_liuren_hr = None
        # ===== R4: AI 降级检测 + 配置热更新订阅 =====
        self._ai_available = self._check_ai_availability()
        self._update_ai_buttons_state()
        self._subscribe_ai_config()

    # ===== 惰性计算器 / Service（冷启动优化：首次 _do_* 用户操作时才构造） =====
    @property
    def bazi_calc(self):
        if self._bazi_calc is None:
            self._bazi_calc = BaziCalculator()
        return self._bazi_calc

    @property
    def lunar_conv(self):
        if self._lunar_conv is None:
            self._lunar_conv = LunarConverter()
        return self._lunar_conv

    @property
    def solar_calc(self):
        if self._solar_calc is None:
            self._solar_calc = SolarTimeCalculator()
        return self._solar_calc

    @property
    def location_db(self):
        if self._location_db is None:
            self._location_db = LocationDB()
        return self._location_db

    @property
    def meihua_calc(self):
        if self._meihua_calc is None:
            self._meihua_calc = MeiHuaCalculator()
        return self._meihua_calc

    @property
    def hexagram_analyzer(self):
        if self._hexagram_analyzer is None:
            self._hexagram_analyzer = HexagramAnalyzer()
        return self._hexagram_analyzer

    @property
    def liuren_calc(self):
        if self._liuren_calc is None:
            self._liuren_calc = LiuRenCalculator()
        return self._liuren_calc

    @property
    def bazi_service(self):
        if self._bazi_service is None:
            try:
                from service.bazi_service import BaziService
                self._bazi_service = BaziService()
            except Exception:
                self._bazi_service = None
        return self._bazi_service

    # ===== DatabaseManager 惰性 + 后台线程异步打开（避免约 1s 冷读阻塞首帧） =====
    @property
    def db_manager(self):
        """DatabaseManager 惰性 + 异步就绪。

        后台线程打开 SQLite（冷读约 1s）期间，同步访问仅做有界等待——
        用户操作通常远晚于后台线程完成，几乎零阻塞；等待失败（初始化失败）则返回 None。
        """
        if self._db_manager is None and not self._db_manager_ready:
            import time as _t
            _deadline = _t.time() + 5.0
            while not self._db_manager_ready and _t.time() < _deadline:
                _t.sleep(0.01)
        return self._db_manager

    def _init_db_async(self):
        """后台线程打开 SQLite，避免冷启动阻塞；完成后置 _db_manager。

        SQLite 连接本身线程安全；DatabaseManager 单例在构造期注册，重复访问幂等。
        """
        import threading

        def _open():
            try:
                from core.database_manager import DatabaseManager
                dm = DatabaseManager()
            except Exception as e:  # noqa: BLE001
                dm = None
                try:
                    self._logger.warning(f"[DB] 后台初始化失败：{e}")
                except Exception:
                    pass
            self._db_manager = dm
            self._db_manager_ready = True

        threading.Thread(target=_open, daemon=True).start()

    def _check_ai_availability(self) -> bool:
        """探测 AI 模型配置是否完整可用（唯一来源：core.ai_config）。"""
        try:
            from core.ai_config import is_ai_configured
            return is_ai_configured()
        except Exception:
            return False

    def _subscribe_ai_config(self):
        """订阅配置变更，用户在设置中改完即时刷新界面，无需重启。"""
        try:
            from core.ai_config import subscribe
            self._ai_config_unsubscribe = subscribe(self._on_ai_config_changed)
        except Exception as e:
            self._logger.warning(f"[设置] AI 配置订阅失败：{e}")
            self._ai_config_unsubscribe = None

    def _on_ai_config_changed(self, version: int):
        """配置热更新回调：重新探测可用性并刷新按钮状态。"""
        try:
            self._ai_available = self._check_ai_availability()
            self._update_ai_buttons_state()
            self._logger.info(f"[设置] AI 配置已更新（v{version}），界面状态已刷新")
        except Exception as e:
            self._logger.warning(f"[设置] AI 配置热更新处理失败：{e}")

    def _update_ai_buttons_state(self):
        """根据 AI 可用性更新各结果面板上的 AI 分析按钮状态。"""
        if self._ai_available:
            msg = ''
        else:
            msg = '龙虎山大师兄功能当前不可用，请在「设置」中配置 AI 模型'

        for attr in ('bazi_result', 'meihua_result', 'liuren_result'):
            panel = getattr(self, attr, None)
            if panel is None:
                continue
            btn = getattr(panel, 'smart_analyze_btn', None)
            if btn is not None and not self._ai_available:
                # 仅在不可用时强制隐藏；可用时交由面板自身的展示逻辑控制
                btn.setVisible(False)
            setter = getattr(panel, 'set_ai_status_message', None)
            if callable(setter):
                try:
                    setter(msg)
                except Exception:
                    pass

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
        # 安全退出：停止所有 AI worker 并保存界面设置
        self._shutdown_workers()
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
        """把窗口几何、分栏比例、当前板块写入当前激活后端（尽力而为，关窗时不阻塞）。

        DB 仍处后台冷读时（未就绪）直接跳过，避免关窗被 5s 等待拖慢；正常路径
        （DB 已就绪）行为不变。
        """
        try:
            # 关窗路径：不阻塞等待后台 DB，未就绪则跳过保存
            if not self._db_manager_ready:
                return False
            mgr = self._db_manager
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
        """启动时还原上次的界面配置。DB 后台线程未就绪时按默认布局并稍后重试一次。

        还原失败（初始化失败）静默忽略。
        """
        try:
            # DB 可能仍在后台冷读（约 1s），此时按默认布局，稍后重试一次
            if not self._db_manager_ready:
                QTimer.singleShot(150, self._restore_ui_settings)
                return
            mgr = self._db_manager
            if mgr is None:
                return  # 初始化失败，静默忽略
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
            # M2-1（Q13）：白名单改为 VALID_MODULES，修复玄空飞星不被记忆
            if mod in VALID_MODULES:
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
                user_id=0,
                session=self._session_id,
                detail=detail,
            )
            return bool(ok)
        except Exception as e:
            self._logger.warning(f"[操作记录] 写入失败：{e}")
            return False

    def _init_ui(self):
        """构建主窗口整体布局：顶部导航栏 + QSplitter 左右分栏（输入栈/结果栈）+ 状态栏。"""
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(Spacing.S0)

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
        # 延迟到窗口几何可用时，按断点初始化 splitter + 发密度信号（M2-2）
        QTimer.singleShot(0, self._apply_responsive)

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
        sb.showMessage('八字排盘 · 梅花易数 · 大六壬 · 龙虎山大师兄自动分析')
        self.setStatusBar(sb)

        # 常驻版本标签（状态栏右侧，清晰可见）：版本号源自 app_version 单一权威源，
        # 与程序实际版本完全一致，打包后随版本更新自动同步。
        self._version_label = QLabel(get_version_label())
        self._version_label.setObjectName('StatusBarVersion')
        self._version_label.setStyleSheet(f"""
            QLabel#StatusBarVersion {{
                color: {Colors.QINGHUA};
                font-size: 11px;
                font-family: 'Courier New', 'Consolas', monospace;
                font-weight: {Fonts.W_MEDIUM};
                padding: 2px 12px;
                border-left: 1px solid {Colors.BORDER};
                background: {Colors.HOVER};
            }}
        """)
        self._version_label.setToolTip(f'{APP_NAME} {get_version_label()} · 绿色便携版')
        sb.addPermanentWidget(self._version_label)

        self.module_hint = None  # 预留：当前模块提示

    def _create_navbar(self, parent):
        """创建顶部导航栏：浅色国风简约风格。

        白色底色 + 金色点缀，底部细线分割，导航按钮以「图标+文字」横向排列，
        选中态青花蓝填充，悬停态金色文字，整体干净清爽不突兀。

        Args:
            parent: 承载导航栏的父布局（根垂直布局）
        """
        bar = QFrame()
        bar.setFixedHeight(54)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border-bottom: 1px solid {Colors.DIVIDER};
            }}
        """)

        h = QHBoxLayout(bar)
        h.setContentsMargins(Spacing.S5, Spacing.S0, Spacing.S4, Spacing.S0)
        h.setSpacing(Spacing.S0)

        # Logo区：鎏金太极图标 + 宋体标题
        logo_container = QFrame()
        logo_container.setStyleSheet("background: #1a1a2e; border: none;")
        logo_hl = QHBoxLayout(logo_container)
        logo_hl.setContentsMargins(0, 0, 0, 0)
        logo_hl.setSpacing(Spacing.S2)

        logo_icon = QLabel('☯')
        logo_icon.setStyleSheet(f"font-size: 20px; color: {Colors.LIUJIN};")

        logo_title = QLabel('风水排盘')
        logo_title.setStyleSheet(f"""
            font-size: 15px;
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
            letter-spacing: 2px;
        """)

        logo_hl.addWidget(logo_icon)
        logo_hl.addWidget(logo_title)
        h.addWidget(logo_container)
        h.addSpacing(Spacing.S6)

        # 分隔竖线（淡金色）
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(24)
        sep.setStyleSheet(f"background-color: {Colors.LIUJIN_LIGHT};")
        h.addWidget(sep)
        h.addSpacing(Spacing.S4)

        # 导航按钮组：无边框胶囊，简洁横向排列
        nav_container = QFrame()
        nav_container.setStyleSheet("background: transparent; border: none;")
        nav_hl = QHBoxLayout(nav_container)
        nav_hl.setContentsMargins(0, 0, 0, 0)
        nav_hl.setSpacing(Spacing.S0)

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
                    border-radius: {Spacing.RADIUS};
                    font-size: 13px;
                    font-family: {Fonts.BODY};
                    padding: 0 16px;
                }}
                QPushButton:hover {{
                    color: {Colors.LIUJIN};
                    background: {Colors.LIUJIN_GLOW};
                }}
                QPushButton:checked {{
                    color: {Colors.TEXT_INV};
                    background: {Colors.QINGHUA};
                }}
                QPushButton:focus {{
                    border: {FOCUS_BORDER};
                }}
            """)
            self.nav_btns[item['id']] = btn
            nav_hl.addWidget(btn)
            btn.clicked.connect(lambda _, pid=item['id']: self._switch(pid))

        h.addWidget(nav_container)
        h.addStretch()

        # 设置按钮（简洁图标，无描边）
        self.settings_btn = QPushButton('⚙')
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setToolTip('设置 · AI模型配置')
        self.settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.TEXT3};
                border: none;
                border-radius: {Spacing.RADIUS_SM};
                font-size: 13px;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {Colors.QINGHUA};
                background: {Colors.QINGHUA_GLOW};
            }}
            QPushButton:focus {{
                border: {FOCUS_BORDER};
            }}
        """)
        self.settings_btn.clicked.connect(self._show_settings_dialog)
        h.addWidget(self.settings_btn)

        # 关于按钮（简洁图标，无描边）
        self.about_btn = QPushButton('i')
        self.about_btn.setCursor(Qt.PointingHandCursor)
        self.about_btn.setFixedSize(30, 30)
        self.about_btn.setToolTip('关于 / 联系我')
        self.about_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.TEXT3};
                border: none;
                border-radius: {Spacing.RADIUS_SM};
                font-size: 13px;
                font-weight: {Fonts.W_BOLD};
                padding: 0;
            }}
            QPushButton:hover {{
                color: {Colors.QINGHUA};
                background: {Colors.QINGHUA_GLOW};
            }}
            QPushButton:focus {{
                border: {FOCUS_BORDER};
            }}
        """)
        self.about_btn.clicked.connect(self._show_about_dialog)
        h.addWidget(self.about_btn)

        parent.addWidget(bar)

    def _build_left(self):
        """构建左侧输入面板栈：依次加入八字/梅花/六壬/玄空飞星四个输入面板。"""
        self.bazi_input = InputPanel()
        self.left_stack.addWidget(self.bazi_input)
        self.meihua_input = MeihuaInputPanel()
        self.left_stack.addWidget(self.meihua_input)
        self.liuren_input = LiurenInputPanel()
        self.left_stack.addWidget(self.liuren_input)
        self.xuan_kong_input = XuanKongInputPanel()
        self.left_stack.addWidget(self.xuan_kong_input)

    def _build_right(self):
        """构建右侧结果面板栈：依次加入八字/梅花/六壬/玄空飞星四个结果面板。"""
        self.bazi_result = ResultPanel()
        self.right_stack.addWidget(self.bazi_result)
        self.meihua_result = MeihuaResultPanel()
        self.right_stack.addWidget(self.meihua_result)
        self.liuren_result = LiurenResultPanel()
        self.right_stack.addWidget(self.liuren_result)
        self.xuan_kong_result = XuanKongResultPanel()
        self.right_stack.addWidget(self.xuan_kong_result)

    def _current_density(self) -> tuple:
        """返回当前密度档 (页面边距, 卡片间距, 卡片内距, 行高)（M2-2）。

        供四结果面板的 `on_density_changed(density)` 槽消费。DPI 取自主屏
        devicePixelRatio；无屏（离屏）时回落 1.0。
        """
        from PySide6.QtGui import QGuiApplication
        dpi = 1.0
        try:
            scr = QGuiApplication.primaryScreen()
            if scr is not None:
                dpi = scr.devicePixelRatio()
        except Exception:
            pass
        return Spacing.density_for(self.width(), dpi)

    def _apply_responsive(self):
        """按 §4.4 四档断点设置 splitter 方向/尺寸与左栏宽度，并发密度信号（M2-2）。

        - XS (<900)：单栏纵向，左栏 min 320、解除上限，右栏 min 320。
        - S  (900–1099)：紧凑双栏，左栏 320~460。
        - M/L(≥1100)：标准/宽屏双栏，左栏 360~460（宽屏保持上限 460）。
        每次调用均 emit density_changed，供结果面板同步边距。
        """
        w = self.width()
        if w <= 0:
            w = 1400
        if w < Spacing.BP_XS:                       # XS：单栏（纵向）
            self.splitter.setOrientation(Qt.Vertical)
            self.left_stack.setMinimumWidth(320)
            self.left_stack.setMaximumWidth(16777215)   # 纵向模式解除上限
            self.right_stack.setMinimumWidth(320)
            left = int(max(w, 640) * 0.4)
            self.splitter.setSizes([left, max(w - left, 320)])
        elif w < Spacing.BP_S:                       # S：紧凑双栏
            self.splitter.setOrientation(Qt.Horizontal)
            self.left_stack.setMinimumWidth(320)
            self.left_stack.setMaximumWidth(460)
            self.right_stack.setMinimumWidth(320)
            left = int(w * self.SPLIT_LEFT_RATIO)
            self.splitter.setSizes([left, w - left])
        else:                                        # M/L：标准 / 宽屏双栏
            self.splitter.setOrientation(Qt.Horizontal)
            self.left_stack.setMinimumWidth(360)
            self.left_stack.setMaximumWidth(460)
            self.right_stack.setMinimumWidth(460)
            left = int(w * self.SPLIT_LEFT_RATIO)
            self.splitter.setSizes([left, w - left])
        self.density_changed.emit(self._current_density())

    def _apply_splitter_ratio(self):
        """历史兼容别名：委托 _apply_responsive（M2-2 重命名）。

        窗口缩放时由 QSplitter 依据 stretch 因子自适应维持比例；
        左侧触及上限（大屏）后右侧继续填满剩余空间，实现自适应。
        """
        self._apply_responsive()

    def resizeEvent(self, event):
        """窗口缩放跨越断点时重排（M2-2）。

        用 `self._last_bp` 缓存断点名做短路：仅在 XS/S/M/L 之间切换才调用
        `_apply_responsive()`，避免每次像素级 resize 都触发 splitter 重排与信号发射。
        """
        super().resizeEvent(event)
        w = self.width()
        bp = ('XS' if w < Spacing.BP_XS
              else 'S' if w < Spacing.BP_S
              else 'M' if w < Spacing.BP_L
              else 'L')
        if bp != self._last_bp:
            self._last_bp = bp
            self._apply_responsive()

    def _switch(self, pid):
        """切换当前激活板块。

        Args:
            pid: 板块 id，取值 'bazi'/'meihua'/'liuren'/'xuan_kong'

        同步高亮导航按钮，切换左右堆叠控件的当前页，并记录切换操作。
        """
        for k, b in self.nav_btns.items():
            b.setChecked(k == pid)
        # M2-1：索引单一真相源（NAV_INDEX），不再硬编码 dict
        idx = NAV_INDEX.get(pid, 0)
        self.left_stack.setCurrentIndex(idx)
        self.right_stack.setCurrentIndex(idx)
        # 板块切换微动画：对新激活页做 300ms 淡入（M7-T3/T4）
        self._fade_in_page(self.left_stack.currentWidget())
        self._fade_in_page(self.right_stack.currentWidget())
        self._log_op('switch_module', pid)

    def _fade_in_page(self, widget):
        """板块切换时对新激活页做透明度过渡（M7-T3/T4 微动画）。

        - widget 为 None 时静默返回（调用方传 currentWidget() 可能为空）。
        - 使用 QGraphicsOpacityEffect 做 0→1 的 300ms 淡入（EASING_OUT，DURATION_NORMAL），
          动画结束后移除 effect，避免残留影响后续渲染。
        - 幂等：同一 widget 的在途动画会被 stop，不会叠加。

        Args:
            widget: 目标 QWidget（板块输入/结果页）；None 时不处理。
        """
        if widget is None:
            return
        try:
            from ui.animation import DURATION_NORMAL, EASING_OUT
            # 同一 widget 的在途动画先停，避免叠加
            prev = getattr(widget, '_page_fade_anim', None)
            if prev is not None:
                try:
                    prev.stop()
                except RuntimeError:
                    pass
            eff = widget.graphicsEffect()
            op = QGraphicsOpacityEffect(widget) if eff is None else eff
            op.setOpacity(0.0)
            anim = QPropertyAnimation(op, b'opacity', self)
            anim.setDuration(DURATION_NORMAL)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(EASING_OUT)
            widget._page_fade_anim = anim
            widget._page_fade_eff = op
            # 动画完成或中途中止后清理 effect，避免残留
            def _cleanup():
                try:
                    widget.setGraphicsEffect(None)
                except RuntimeError:
                    pass
            anim.finished.connect(_cleanup)
            anim.start()
        except Exception:
            # 动画异常不影响切换本身（页面已 setCurrentIndex）
            pass

    def _connect_signals(self):
        """绑定各输入面板与结果面板的信号到对应槽函数（提交/重置/AI分析等）。"""
        self.bazi_input.submit_btn.clicked.connect(self._on_bazi)
        self.bazi_input.reset_btn.clicked.connect(self._on_bazi_reset)
        self.bazi_result.refresh_btn.clicked.connect(self._on_bazi)
        self.bazi_result.smart_analyze_btn.clicked.connect(self._on_bazi_ai_analyze)
        self.meihua_input.submit_btn.clicked.connect(self._on_meihua)
        self.meihua_input.reset_btn.clicked.connect(self._on_meihua_reset)
        self.meihua_result.smart_analyze_btn.clicked.connect(self._on_meihua_ai_analyze)
        self.liuren_input.submit_btn.clicked.connect(self._on_liuren)
        self.liuren_input.reset_btn.clicked.connect(self._on_liuren_reset)
        self.liuren_result.smart_analyze_btn.clicked.connect(self._on_liuren_ai_analyze)
        self.xuan_kong_input.submit_btn.clicked.connect(self._on_xuan_kong)
        self.xuan_kong_input.reset_btn.clicked.connect(self._on_xuan_kong_reset)
        self.xuan_kong_result.refresh_btn.clicked.connect(self._on_xuan_kong)

    def _show_settings_dialog(self):
        """打开 AI 模型配置对话框（保存后热生效，无需重启）。"""
        try:
            dlg = SettingsDialog(self)
            dlg.exec()
            # 兜底刷新：即便订阅回调因异常未触发，关闭对话框后也同步一次状态
            self._ai_available = self._check_ai_availability()
            self._update_ai_buttons_state()
            if self._ai_available:
                self.statusBar().showMessage('AI 模型配置已生效', 4000)
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
        if not self.db_manager:
            return None

        try:
            def _to_int(v, default=0):
                """安全转为 int：缺值/非数字（如空串或字符串）回落默认值。"""
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return default

            y, mo, d = (_to_int(data.get('year')),
                        _to_int(data.get('month')),
                        _to_int(data.get('day')))
            # 无真实生辰信息（如梅花/六壬）时留空，避免写入 "0000-00-00" 垃圾值
            birth_date = f"{y:04d}-{mo:02d}-{d:02d}" if (y or mo or d) else ''
            birth_time = f"{_to_int(data.get('hour')):02d}:{_to_int(data.get('minute', 0)):02d}"

            record_id = self.db_manager.save_pan_record(
                user_id=0,
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
        """八字『开始排盘』按钮槽：先弹出关于对话框，再执行排盘。"""
        self._show_about_dialog()
        try:
            data = self.bazi_input.get_data()
            task_id = str(uuid.uuid4())
            self.bazi_result.show_loading()
            QTimer.singleShot(80, lambda: self._do_bazi(data, task_id))
        except Exception as e:
            self.statusBar().showMessage(f'参数错误: {e}')
            traceback.print_exc()

    def _do_bazi(self, data, task_id=None):
        """执行八字排盘核心流程（由 _on_bazi 经定时器延迟调用）。

        Args:
            data: 输入面板数据（年/月/日/时/经纬度/农历标志/性别等）
            task_id: 本次排盘任务标识（预留，用于日志与并发追踪）

        流程：解析出生地经纬度 → 农历转公历（如需要）→ 计算真太阳时 →
        调用 core 完成四柱/五行/十神/命理/大运流年/命局类型/运程总结 →
        保存记录 → 展示结果 → 自动触发龙虎山大师兄（AI）分析。
        """
        try:
            # 优先走 Service 层：业务编排（校验/计算/综合建议/落库/事件）
            if getattr(self, 'bazi_service', None):
                try:
                    service_result = self.bazi_service.calculate(
                        year=int(data.get('year', 0)),
                        month=int(data.get('month', 1)),
                        day=int(data.get('day', 1)),
                        hour=int(data.get('hour', 0)),
                        minute=int(data.get('minute', 0)),
                        longitude=float(data.get('longitude', 120.0)),
                        gender=data.get('gender', '男'),
                        save=True,
                        name=data.get('name', '')
                    )
                    self._last_bazi_record_id = service_result.get('record_id')
                    # 补充 UI 专属字段：basic_info、lunar_date、hour、location 等
                    y = service_result.get('basic_info', {}).get('year', int(data.get('year', 0)))
                    m = service_result.get('basic_info', {}).get('month', int(data.get('month', 1)))
                    d = service_result.get('basic_info', {}).get('day', int(data.get('day', 1)))
                    try:
                        dt = datetime(y, m, d, int(data.get('hour', 0)), int(data.get('minute', 0)))
                        sdt = self.solar_calc.get_true_solar_time(dt, float(data.get('longitude', 120.0)))
                        hour_str = f"{sdt.hour:02d}:{sdt.minute:02d}"
                    except Exception:
                        hour_str = f"{data.get('hour', 0):02d}:{data.get('minute', 0):02d}"
                    li = self.lunar_conv.solar_to_lunar(y, m, d)
                    basic = service_result.get('basic_info', {})
                    basic.update({
                        'solar_date': f"{y}年{m}月{d}日",
                        'lunar_date': f"{li[0]}年{li[1]}月{li[2]}日" if li else basic.get('lunar_date', '-'),
                        'hour': hour_str,
                        'location': data.get('location') or '-',
                        'longitude': float(data.get('longitude', 120.0)),
                        'latitude': float(data.get('latitude', 30.0)),
                    })
                    service_result['basic_info'] = basic
                    self.bazi_result.display_result(service_result)
                    self.statusBar().showMessage('八字排盘完成 · Service层综合建议生成')
                    QTimer.singleShot(300, self._trigger_bazi_auto_ai)
                    return
                except Exception as e:
                    self._logger.warning(f"[Service] BaziService 计算失败，回退 core 流程: {e}")

            # 回退：原始 core 流程（兼容）
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
                from core.bazi.yunshi import YunShiCalculator
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
                from core.bazi.yuncheng import YunChengAnalyzer
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

            # ★ 显示排盘结果（关键修复：之前遗漏了此调用导致"无内容显示"）
            self.bazi_result.display_result(result)
            self.statusBar().showMessage(f'八字排盘完成 · 准备启动龙虎山大师兄分析…')

            # ★ v5.0: 排盘完成后自动触发AI分析
            QTimer.singleShot(300, self._trigger_bazi_auto_ai)
        except Exception as e:
            self.statusBar().showMessage(f'计算错误: {e}')
            traceback.print_exc()

    def _trigger_bazi_auto_ai(self):
        """排盘完成后自动触发AI深度分析"""
        try:
            # 修复：AI 未配置时跳过自动解读，避免发起注定失败的网络请求造成白屏
            if not getattr(self, '_ai_available', False):
                self._logger.debug("[AI] 自动AI分析跳过: AI 未配置")
                return
            input_data = self.bazi_input.get_data()
            chart_data = self.bazi_result.get_chart_data_for_ai()

            if not chart_data or not chart_data.get('bazi', {}).get('year_pillar'):
                self._logger.debug("[AI] 自动AI分析跳过: 排盘数据不完整")
                return

            # 更新状态提示
            self.statusBar().showMessage('排盘完成 · 正在自动进行龙虎山大师兄深度分析…')

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
        """根据十神汇总与命理神煞生成吉凶批注列表（规则引擎，离线可跑）。

        Args:
            ml: 命理数据（含神煞 shensha）
            ss: 十神数据（含 summary 与 total_weights）

        Returns:
            批注条目列表，每条形如 {'type': '吉'/'中'/'凶', 'text': '...'}
        """
        a = []
        sh_summary = ss.get('summary', {})
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
            cleaned = AgnesClient._clean_json_response(content)
            import json
            obj = json.loads(cleaned)
            lon = float(obj['longitude'])
            lat = float(obj['latitude'])
            print(f"出生地「{text}」龙虎山大师兄解析：({lon}, {lat})")
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
        from core.bazi.bazi_types import get_bazi_types_payload

        strength = ''
        geju_type = ''
        geju_name = ''
        geju_desc = ''
        rizhu_wx = wx.get('rizhu_wx', '') if isinstance(wx, dict) else ''

        try:
            from core.bazi.geju_analyzer import GeJuAnalyzer
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

        from core.bazi.bazi_types import get_yongshen
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
        """八字『重置』按钮槽：清空输入面板与结果面板。"""
        self.bazi_input.clear()
        self.bazi_result.clear()

    # ===== 梅花 =====
    def _on_meihua(self):
        """梅花易数『起卦』按钮槽：先弹出关于对话框，再执行起卦。"""
        self._show_about_dialog()
        try:
            data = self.meihua_input.get_data()
            task_id = str(uuid.uuid4())
            self.meihua_result.show_loading()
            QTimer.singleShot(80, lambda: self._do_meihua(data, task_id))
        except Exception as e:
            self.statusBar().showMessage(f'参数错误: {e}')
            self._logger.warning(f"[梅花] 起卦参数校验失败: {e}")


    def _do_meihua(self, data, task_id=None):
        """执行梅花易数起卦流程（由 _on_meihua 经定时器延迟调用）。

        Args:
            data: 输入面板数据（起卦方式 method、问题、各方式对应参数）
            task_id: 本次起卦任务标识（预留）

        按 method 分发到对应起卦算法，生成本/互/变/错/综卦并交由 HexagramAnalyzer 分析，
        展示结果、保存记录、记录操作，最后自动触发龙虎山大师兄（AI）解读。
        """
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
                # 检查是否为 None（0 时是有效值，不能用 all() 判断）
                if any(v is None for v in (year, month, day, hour)):
                    raise ValueError("时间起卦需要完整的年月日时")
                hr = self.meihua_calc.time_divination(year, month, day, hour, q)
            else:
                raise ValueError(f"未知起卦方式: {method}")

            if not hr:
                return

            all_hex = self.meihua_calc.generate_all_hexagrams(hr)
            analysis = self.hexagram_analyzer.analyze_divination(hr, all_hex)
            base_raw = analysis.get('base', {})
            hu_raw = analysis.get('hu', {})
            bian_raw = analysis.get('bian', {})
            cuo_raw = analysis.get('cuo', {})
            zong_raw = analysis.get('zong', {})

            def _enrich_hexagram_info(raw):
                if not raw:
                    return {}
                enriched = raw.copy()
                upper_num = raw.get('upper_num')
                lower_num = raw.get('lower_num')
                upper_info = self.hexagram_analyzer.bagua.get(upper_num, {}) if upper_num is not None else {}
                lower_info = self.hexagram_analyzer.bagua.get(lower_num, {}) if lower_num is not None else {}
                enriched['symbol'] = upper_info.get('symbol', '') + lower_info.get('symbol', '')
                enriched['explanation'] = raw.get('description', '')
                enriched['upper_gua'] = upper_info.get('name', '')
                enriched['lower_gua'] = lower_info.get('name', '')
                return enriched

            ben_gua = _enrich_hexagram_info(base_raw)
            hu_gua = _enrich_hexagram_info(hu_raw)
            bian_gua = _enrich_hexagram_info(bian_raw)
            cuo_gua = _enrich_hexagram_info(cuo_raw)
            zong_gua = _enrich_hexagram_info(zong_raw)

            # Build yao list with moving flag
            yao_list_raw = base_raw.get('yao_ci', [])
            changing_yao = base_raw.get('changing_yao', 0)
            yao_list = []
            for idx, yao in enumerate(yao_list_raw, start=1):
                yao_list.append({
                    'name': yao.get('yao', ''),
                    'text': yao.get('text', ''),
                    'explanation': yao.get('meaning', ''),
                    'is_moving': (idx == changing_yao)
                })

            result = {
                'basic_info': {
                    'method': hr.get('method', ''),
                    'question': q,
                    'time': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
                    'moving_yao': str(changing_yao) if changing_yao else ''
                },
                'overall': {
                    'level': analysis.get('overall_judgment', '平'),
                    'overall': base_raw.get('description', '')
                },
                'ben_gua': ben_gua,
                'hu_gua': hu_gua,
                'bian_gua': bian_gua,
                'cuo_gua': cuo_gua,
                'zong_gua': zong_gua,
                'yao_list': yao_list,
                'suggestions': analysis.get('suggestions', []),
                'divination_extra': hr,
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
            # 修复：AI 未配置时跳过自动解读，避免发起注定失败的网络请求造成白屏
            if not getattr(self, '_ai_available', False):
                self._logger.debug("[AI] 自动AI解读跳过: AI 未配置")
                return
            input_data = self.meihua_input.get_data()
            hexagram_data = self.meihua_result.get_hexagram_data_for_ai()

            if not hexagram_data or not hexagram_data.get('base', {}).get('name'):
                self._logger.debug("[AI] 自动AI解读跳过: 卦象数据不完整")
                return

            # 更新状态提示
            self.statusBar().showMessage('起卦完成 · 正在自动进行龙虎山大师兄深度解读…')

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
        """梅花易数『重置』按钮槽：清空输入面板与结果面板。"""
        self.meihua_input.clear()
        self.meihua_result.clear()

    # ===== 大六壬 =====
    def _on_liuren(self):
        """大六壬『起课』按钮槽：先弹出关于对话框，再执行起课。"""
        self._show_about_dialog()
        try:
            data = self.liuren_input.get_data()
            task_id = str(uuid.uuid4())
            # 若已有有效排盘结果则直接复用，避免 show_loading 清空已渲染内容导致白屏
            if not getattr(self.liuren_result, '_current_result', None):
                self.liuren_result.show_loading()
            QTimer.singleShot(80, lambda: self._do_liuren(data, task_id))
        except Exception as e:
            self.statusBar().showMessage(f'参数错误: {e}')
            traceback.print_exc()


    def _do_liuren(self, data, task_id=None):
        """执行大六壬起课流程（由 _on_liuren 经定时器延迟调用）。

        Args:
            data: 输入面板数据（起课方式 method、年月日时、问题、占事等）
            task_id: 本次起课任务标识（预留）

        调用 LiuRenCalculator 起课，展示结果、保存记录、记录操作，
        最后自动触发龙虎山大师兄（AI）解读。
        """
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
                self.liuren_result.clear()
                return
            self.liuren_result.display_result(hr)
            self.statusBar().showMessage('大六壬起课完成')
            record_id = self._save_pan_record(data, hr, '大六壬')
            if record_id:
                self.statusBar().showMessage(f'大六壬起课完成 · 记录ID: {record_id}')
            self._log_op('liuren_divination', method, f"question={q}" if q else f"method={method}")
            # 保存完整排盘结果供 AI 解读使用
            self._last_liuren_hr = hr
            QTimer.singleShot(300, self._trigger_liuren_auto_ai)
        except Exception as e:
            # 异常时恢复 empty_state，防止布局处于空状态导致白屏
            self.liuren_result.clear()
            self.statusBar().showMessage(f'起课错误: {e}')
            traceback.print_exc()

    def _trigger_liuren_auto_ai(self):
        """起课后自动触发AI深度解读"""
        try:
            # 修复：AI 未配置时跳过自动解读，避免发起注定失败的网络请求造成白屏
            if not getattr(self, '_ai_available', False):
                self._logger.debug("[AI] 自动AI解读跳过: AI 未配置")
                return
            input_data = self.liuren_input.get_data()
            # 优先使用完整排盘结果（含天地盘/四课/三传/天将/神煞），避免 AI 因数据不全返回空结果导致白屏
            chart_data = getattr(self, '_last_liuren_hr', None) or self.liuren_result._current_result
            if not chart_data:
                self._logger.warning("[AI] 自动AI解读跳过: 无可用排盘数据")
                return

            if not chart_data.get('san_chuan'):
                self._logger.debug("[AI] 自动AI解读跳过: 起课数据不完整")
                return

            self.statusBar().showMessage('起课完成 · 正在自动进行龙虎山大师兄深度解读…')

            task_id = str(uuid.uuid4())

            self._liuren_ai_worker = AiAnalysisWorker('liuren', input_data, chart_data, task_id)
            self._liuren_ai_worker.progress_updated.connect(self._on_liuren_ai_progress)
            self._liuren_ai_worker.analysis_finished.connect(self._on_liuren_ai_finished)
            self._liuren_ai_worker.analysis_failed.connect(self._on_liuren_ai_failed)
            self._register_worker(self._liuren_ai_worker)
            self._liuren_ai_worker.start()
        except Exception as e:
            self._logger.error("[六壬] 自动AI解读启动失败: %s", e, exc_info=True)

    def _on_liuren_reset(self):
        """大六壬『重置』按钮槽：清空输入面板与结果面板。"""
        self.liuren_input.clear()
        self.liuren_result.clear()

    # ===== 玄空飞星 =====

    def _on_xuan_kong(self):
        """玄空飞星『起盘』按钮槽：执行排盘流程。"""
        try:
            data = self.xuan_kong_input.get_data()
            self.xuan_kong_result.show_loading() if hasattr(self.xuan_kong_result, 'show_loading') else None
            QTimer.singleShot(50, lambda: self._do_xuan_kong(data))
        except Exception as e:
            self.statusBar().showMessage(f'参数错误: {e}')
            traceback.print_exc()

    def _do_xuan_kong(self, data, task_id=None):
        """执行玄空飞星排盘流程。

        Args:
            data: 输入面板数据（坐向、建造年份、当前年份）
        """
        try:
            sui_xiang = data['sui_xiang']
            build_year = data['build_year']
            current_year = data.get('current_year', build_year)
            calc = XuanKongCalculator()
            result = calc.calculate(sui_xiang=sui_xiang, build_year=build_year, current_year=current_year)
            self.xuan_kong_result.display_result(result)
            self.statusBar().showMessage(f"玄空飞星排盘完成 · 坐向{sui_xiang} · 运序{result.get('yun', '-')}")
            record_id = self._save_pan_record(data, result, '玄空飞星')
            if record_id:
                self.statusBar().showMessage(f"玄空飞星排盘完成 · 记录ID: {record_id}")
            self._log_op('xuan_kong_divination', sui_xiang, f"build_year={build_year}")
        except Exception as e:
            self._logger.error("[玄空] 排盘失败: %s", e, exc_info=True)
            self.statusBar().showMessage(f"玄空飞星排盘失败: {e}")
            self.xuan_kong_result.clear() if hasattr(self.xuan_kong_result, 'clear') else None

    def _on_xuan_kong_reset(self):
        """玄空飞星『重置』按钮槽：清空输入面板与结果面板。"""
        self.xuan_kong_input.clear()
        self.xuan_kong_result.clear()

    def _on_liuren_ai_analyze(self):
        """大六壬AI分析按钮点击处理"""
        try:
            input_data = self.liuren_input.get_data()
            liuren_data = self.liuren_result.get_liuren_data_for_ai()

            if not liuren_data or not liuren_data.get('san_chuan'):
                QMessageBox.warning(self, '提示', '请先起课，再使用龙虎山大师兄解读功能')
                return

            self.liuren_result.show_ai_loading('龙虎山大师兄正在解读六壬玄机…')
            self.statusBar().showMessage('龙虎山大师兄解读进行中，请稍候…')

            task_id = str(uuid.uuid4())

            self._liuren_ai_worker = AiAnalysisWorker('liuren', input_data, liuren_data, task_id)
            self._liuren_ai_worker.progress_updated.connect(self._on_liuren_ai_progress)
            self._liuren_ai_worker.analysis_finished.connect(self._on_liuren_ai_finished)
            self._liuren_ai_worker.analysis_failed.connect(self._on_liuren_ai_failed)
            self._register_worker(self._liuren_ai_worker)
            self._liuren_ai_worker.start()
        except Exception as e:
            self.statusBar().showMessage(f'龙虎山大师兄解读启动失败: {e}')
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'龙虎山大师兄解读启动失败: {e}')

    def _on_liuren_ai_progress(self, stage: str, message: str):
        """大六壬AI分析进度更新"""
        status_messages = {
            'validating': '正在验证输入数据…',
            'initializing': '正在初始化龙虎山大师兄分析引擎…',
            'analyzing': '龙虎山大师兄正在解读六壬玄机…',
            'completed': '分析完成！'
        }
        status = status_messages.get(stage, message)
        self.statusBar().showMessage(status)

    def _on_liuren_ai_finished(self, result: dict):
        """大六壬AI分析完成"""
        try:
            # 检查分析是否成功
            if not result.get('success', False):
                error_type = result.get('error_type', 'unknown')
                error_msg = result.get('error_message', '未知错误')
                self._on_liuren_ai_failed(error_type, error_msg)
                return

            ai_analysis = result.get('ai_analysis', {})
            self.liuren_result.display_ai_analysis_result(ai_analysis)
            # 缓存 AI 结论供大六壬面板导出复用（键名与面板内部 _current_智能 保持一致）
            try:
                self.liuren_result._current_智能 = dict(ai_analysis or {})
            except Exception:
                pass

            token_usage = result.get('token_usage', 0)
            report_id = result.get('report_id', 0)
            elapsed = result.get('elapsed_seconds', 0)

            # 更新数据库：将 AI 分析结果写入 pan_records.ai_json
            if self.db_manager and hasattr(self, '_last_liuren_record_id'):
                try:
                    last_id = self._last_liuren_record_id
                    if last_id:
                        self.db_manager.update_pan_ai_result(last_id, ai_analysis)
                except Exception as e:
                    self._logger.warning(f"[AI] 更新六壬AI分析结果到数据库失败: {e}")

            self.statusBar().showMessage(
                f'龙虎山大师兄解读完成 · 报告ID: {report_id} · '
                f'消耗Token: {token_usage} · 耗时: {elapsed:.1f}秒'
            )
        except Exception as e:
            self.statusBar().showMessage(f'显示龙虎山大师兄分析结果失败: {e}')
            traceback.print_exc()

    def _on_liuren_ai_failed(self, error_type: str, error_message: str):
        """大六壬AI分析失败"""
        # AI 失败不覆盖已渲染的排盘结果，只恢复按钮可点击状态
        self.liuren_result.smart_analyze_btn.setVisible(True)
        self.liuren_result.smart_analyze_btn.setEnabled(True)
        self.statusBar().showMessage(f'龙虎山大师兄解读失败: {error_type}')

        error_titles = {
            'validation_error': '数据验证失败',
            'ai_timeout': '龙虎山大师兄请求超时',
            'ai_request_error': '龙虎山大师兄请求失败',
            'ai_response_error': '龙虎山大师兄响应解析失败',
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
            self._last_bazi_input = input_data
            chart_data = self.bazi_result.get_chart_data_for_ai()

            if not chart_data or not chart_data.get('bazi', {}).get('year_pillar'):
                QMessageBox.warning(self, '提示', '请先进行排盘，再使用龙虎山大师兄分析功能')
                return

            self.bazi_result.show_ai_loading('龙虎山大师兄正在深入分析八字命理…')
            self.statusBar().showMessage('龙虎山大师兄分析进行中，请稍候…')

            task_id = str(uuid.uuid4())

            self._bazi_ai_worker = AiAnalysisWorker('bazi', input_data, chart_data, task_id)
            self._bazi_ai_worker.progress_updated.connect(self._on_bazi_ai_progress)
            self._bazi_ai_worker.analysis_finished.connect(self._on_bazi_ai_finished)
            self._bazi_ai_worker.analysis_failed.connect(self._on_bazi_ai_failed)
            self._register_worker(self._bazi_ai_worker)
            self._bazi_ai_worker.start()

        except Exception as e:
            self.statusBar().showMessage(f'龙虎山大师兄分析启动失败: {e}')
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'龙虎山大师兄分析启动失败: {e}')

    def _on_bazi_ai_progress(self, stage: str, message: str):
        """八字AI分析进度更新"""
        status_messages = {
            'validating': '正在验证输入数据…',
            'initializing': '正在初始化龙虎山大师兄分析引擎…',
            'analyzing': '龙虎山大师兄正在深度分析八字命理…',
            'completed': '分析完成！'
        }
        status = status_messages.get(stage, message)
        self.statusBar().showMessage(status)

    def _on_bazi_ai_finished(self, result: dict):
        """八字AI分析完成"""
        try:
            # 检查分析是否成功
            if not result.get('success', False):
                error_type = result.get('error_type', 'unknown')
                error_msg = result.get('error_message', '未知错误')
                self._on_bazi_ai_failed(error_type, error_msg)
                return

            ai_analysis = result.get('ai_analysis', {})
            self.bazi_result.display_ai_result(ai_analysis)

            token_usage = result.get('token_usage', 0)
            report_id = result.get('report_id', 0)
            elapsed = result.get('elapsed_seconds', 0)

            # 更新数据库：将 AI 分析结果写入 pan_records.ai_json
            if self.db_manager and hasattr(self, '_last_bazi_record_id'):
                try:
                    last_id = self._last_bazi_record_id
                    if last_id:
                        self.db_manager.update_pan_ai_result(last_id, ai_analysis)
                except Exception as e:
                    self._logger.warning(f"[AI] 更新八字AI分析结果到数据库失败: {e}")

            self.statusBar().showMessage(
                f'龙虎山大师兄分析完成 · 报告ID: {report_id} · '
                f'消耗Token: {token_usage} · 耗时: {elapsed:.1f}秒'
            )
        except Exception as e:
            self.statusBar().showMessage(f'显示龙虎山大师兄分析结果失败: {e}')
            traceback.print_exc()

    def _on_bazi_ai_failed(self, error_type: str, error_message: str):
        """八字AI分析失败"""
        self.bazi_result.display_result(getattr(self.bazi_result, '_current_result', {}))
        self.bazi_result.smart_analyze_btn.setVisible(True)
        self.bazi_result.smart_analyze_btn.setEnabled(True)
        self.statusBar().showMessage(f'龙虎山大师兄分析失败: {error_type}')

        error_titles = {
            'validation_error': '数据验证失败',
            'ai_timeout': '龙虎山大师兄请求超时',
            'ai_request_error': '龙虎山大师兄请求失败',
            'ai_response_error': '龙虎山大师兄响应解析失败',
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
                QMessageBox.warning(self, '提示', '请先起卦，再使用龙虎山大师兄解读功能')
                return

            self.meihua_result.show_ai_loading('龙虎山大师兄正在解读卦象玄机…')
            self.statusBar().showMessage('龙虎山大师兄解读进行中，请稍候…')

            task_id = str(uuid.uuid4())

            self._meihua_ai_worker = AiAnalysisWorker('meihua', input_data, hexagram_data, task_id)
            self._meihua_ai_worker.progress_updated.connect(self._on_meihua_ai_progress)
            self._meihua_ai_worker.analysis_finished.connect(self._on_meihua_ai_finished)
            self._meihua_ai_worker.analysis_failed.connect(self._on_meihua_ai_failed)
            self._register_worker(self._meihua_ai_worker)
            self._meihua_ai_worker.start()

        except Exception as e:
            self.statusBar().showMessage(f'龙虎山大师兄解读启动失败: {e}')
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'龙虎山大师兄解读启动失败: {e}')

    def _on_meihua_ai_progress(self, stage: str, message: str):
        """梅花易数AI分析进度更新"""
        status_messages = {
            'validating': '正在验证输入数据…',
            'initializing': '正在初始化龙虎山大师兄分析引擎…',
            'analyzing': '龙虎山大师兄正在解读卦象玄机…',
            'completed': '解读完成！'
        }
        status = status_messages.get(stage, message)
        self.statusBar().showMessage(status)

    def _on_meihua_ai_finished(self, result: dict):
        """梅花易数AI分析完成"""
        try:
            # 检查分析是否成功
            if not result.get('success', False):
                error_type = result.get('error_type', 'unknown')
                error_msg = result.get('error_message', '未知错误')
                self._on_meihua_ai_failed(error_type, error_msg)
                return

            ai_analysis = result.get('ai_analysis', {})
            self.meihua_result.display_ai_analysis_result(ai_analysis)

            token_usage = result.get('token_usage', 0)
            report_id = result.get('report_id', 0)
            elapsed = result.get('elapsed_seconds', 0)

            # 更新数据库：将 AI 分析结果写入 pan_records.ai_json
            if self.db_manager and hasattr(self, '_last_meihua_record_id'):
                try:
                    last_id = self._last_meihua_record_id
                    if last_id:
                        self.db_manager.update_pan_ai_result(last_id, ai_analysis)
                except Exception as e:
                    self._logger.warning(f"[AI] 更新梅花AI分析结果到数据库失败: {e}")

            self.statusBar().showMessage(
                f'龙虎山大师兄解读完成 · 报告ID: {report_id} · '
                f'消耗Token: {token_usage} · 耗时: {elapsed:.1f}秒'
            )
        except Exception as e:
            self.statusBar().showMessage(f'显示龙虎山大师兄解读结果失败: {e}')
            traceback.print_exc()

    def _on_meihua_ai_failed(self, error_type: str, error_message: str):
        """梅花易数AI分析失败"""
        self.meihua_result.display_result(getattr(self.meihua_result, '_current_result', {}))
        self.meihua_result.smart_analyze_btn.setVisible(True)
        self.meihua_result.smart_analyze_btn.setEnabled(True)
        self.statusBar().showMessage(f'龙虎山大师兄解读失败: {error_type}')

        error_titles = {
            'validation_error': '数据验证失败',
            'ai_timeout': '龙虎山大师兄请求超时',
            'ai_request_error': '龙虎山大师兄请求失败',
            'ai_response_error': '龙虎山大师兄响应解析失败',
            'db_connection_error': '数据库连接异常',
            'db_query_error': '数据库操作异常',
        }
        title = error_titles.get(error_type, '解读失败')

        msg_lines = error_message.split('\n')
        short_msg = msg_lines[0] if msg_lines else error_message

        QMessageBox.warning(self, title, short_msg)

