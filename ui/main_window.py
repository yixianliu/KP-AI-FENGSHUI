"""
传统文化研究工具 - 精美国风主窗口
QSplitter左右分栏 · 暖米底色 · 圆角卡片 · 三色点缀 · 微动画
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QFrame, QApplication, QStatusBar,
                               QPushButton, QStackedWidget, QSplitter,
                               QMessageBox, QGraphicsOpacityEffect)
from PySide6.QtCore import (Qt, QTimer, QPropertyAnimation, Signal,
                            QAbstractAnimation, QDate)
from PySide6.QtGui import QFont, QIcon
from ui.styles import Stylesheets, Colors, Fonts, Spacing, FOCUS_BORDER
from core.path_utils import get_resource_path
from core.app_version import get_version_label, APP_NAME
from ui.components.input_panel import InputPanel
from ui.components.result_panel import ResultPanel
from ui.components.meihua_input import MeihuaInputPanel, METHODS as MEIHUA_METHODS
from ui.components.meihua_result_panel import MeihuaResultPanel
from ui.components.xuan_kong_input import XuanKongInputPanel
from ui.components.xuan_kong_result_panel import XuanKongResultPanel
from ui.components.settings_dialog import SettingsDialog
from ui.components.about_dialog import AboutDialog
from ui.components.ai_analysis_worker import AiAnalysisWorker
from ui.components.history_panel import HistoryPanel
# 注：core.bazi.bazi_calculator 与 core.lunar_converter 改为**惰性导入**
# （见下方 bazi_calc / lunar_conv property）。二者 import 时会经
# core.bazi._baazi_compat._ensure() **同步加载日历数据库**（实测 ~1.5s），
# 是冷启动耗时的首因。延迟到首次八字排盘再付这笔成本，启动不再受影响。
from core.calendar_utils import SolarTimeCalculator
from core.location_db import LocationDB
from core.divination.meihua import MeiHuaCalculator
from core.divination.hexagram_analyzer import HexagramAnalyzer
from core.fengshui.xuan_kong import XuanKongCalculator
from core.log_handler import setup_app_logging
from ui.thread_shutdown import shutdown_threads
from datetime import datetime
import traceback
import logging
import queue
import threading
import uuid

NAV = [
    {'id': 'bazi', 'name': '八字排盘', 'icon': '☯'},
    {'id': 'meihua', 'name': '梅花易数', 'icon': '⚊'},
    {'id': 'xuan_kong', 'name': '玄空飞星', 'icon': '⛰'},
    # 历史记录放在末位：不打乱既有一~三页的 NAV_INDEX 语义
    {'id': 'history', 'name': '历史记录', 'icon': '☲'},
]

# M2-1：路由单一真相源（修 Q13）。由 NAV 顺序派生，消除 _switch / _restore_ui_settings
# 两处硬编码索引；新增板块只需在 NAV 追加一项，索引自动同步。
NAV_INDEX = {item['id']: i for i, item in enumerate(NAV)}
VALID_MODULES = tuple(NAV_INDEX.keys())  # ('bazi', 'meihua', 'xuan_kong', 'history')

# 注：原 `SIDEBAR_WIDTH = 168`（Q15 死常量）已删除——真实导航是顶部栏，
# 该常量仅被 e2e 脚本断言引用，无任何布局依赖。

# ===== 操作日志异步投递 =====
# _log_op 曾直接在 GUI 线程执行「新开连接 + PRAGMA + INSERT + commit」，
# 写锁冲突时切换板块可卡 30s。现改为 GUI 线程只入队，由单个后台线程串行写库；
# 与 system_logs 的 AsyncStorageLogHandler 分开（两者目标表不同）。
_OP_LOG_QUEUE = queue.Queue(maxsize=500)
_OP_LOG_WORKER = None
_OP_LOG_LOCK = threading.Lock()


def _op_log_worker_loop():
    """后台消费操作日志队列：逐条写入 operation_logs，失败仅记录不重试。"""
    logger = logging.getLogger(__name__)
    while True:
        item = _OP_LOG_QUEUE.get()
        if item is None:
            break
        manager, kwargs = item
        try:
            manager.save_operation_log(**kwargs)
        except Exception as e:  # noqa: BLE001 - 后台写入失败不得影响 UI
            logger.warning('[操作记录] 后台写入失败：%s', e)


def _ensure_op_log_worker():
    """惰性启动操作日志消费线程（daemon，不阻塞解释器退出）。"""
    global _OP_LOG_WORKER
    if _OP_LOG_WORKER is not None and _OP_LOG_WORKER.is_alive():
        return
    with _OP_LOG_LOCK:
        if _OP_LOG_WORKER is not None and _OP_LOG_WORKER.is_alive():
            return
        _OP_LOG_WORKER = threading.Thread(
            target=_op_log_worker_loop, daemon=True, name='kp-op-log')
        _OP_LOG_WORKER.start()


def _enqueue_op_log(manager, kwargs) -> bool:
    """把一次操作日志投递到后台队列；队列满时丢弃并返回 False。"""
    try:
        _ensure_op_log_worker()
        _OP_LOG_QUEUE.put_nowait((manager, kwargs))
        return True
    except queue.Full:
        logging.getLogger(__name__).warning('[操作记录] 队列已满，丢弃一条日志')
        return False


class MainWindow(QMainWindow):
    """应用主窗口：承载八字 / 梅花易数 / 玄空飞星三大板块。

    采用三层架构的 UI 层（PySide6）：通过 QSplitter 左右分栏（输入面板 + 结果面板），
    顶部胶囊式导航切换板块，并调度 core 业务层完成排盘与文化研究算法（AI）分析。
    负责 worker 线程生命周期、界面配置持久化与操作日志记录。
    """
    # M2-2：密度档变化信号（tuple: (页面边距, 卡片间距, 卡片内距, 行高)），
    # 四结果面板订阅 on_density_changed 槽统一刷新边距（M3-1 连接）。
    density_changed = Signal(tuple)
    # 数据库后台初始化完成信号：True=就绪，False=初始化失败（进入降级模式）
    db_ready_changed = Signal(bool)
    # M2-2 / M7：左栏占比常量（标准双栏 35%），纵向模式按 0.4 分配高度。
    # 原 0.34 + left_stack.setMaximumWidth(460) 在 1440 宽下把左栏压到 31.97%，
    # 故比例改 0.35，并解除 460 硬上限，让 35/65 真正生效（1440 下 504/936）。
    SPLIT_LEFT_RATIO = 0.35
    # 关窗收尾参数：先协作取消并等待 3s；仍未结束则隐藏窗口等待，30s 后兜底退出
    AI_SHUTDOWN_TIMEOUT_MS = 3000
    AI_SHUTDOWN_GRACE_MS = 30000

    def __init__(self):
        """初始化主窗口：设置窗口元数据、日志、会话标识，并依次完成字体、core、UI、信号绑定与配置还原。"""
        super().__init__()
        self.module_hint = None
        self.setWindowTitle('传统文化研究工具')
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

        排盘计算器（八字/农历/真太阳时/地点/梅花）与 BaziService 改为惰性
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
        # 排盘/起卦后台线程（八字、梅花）：键为板块名，值为 PanTaskWorker/BaziCalculationWorker
        # 未放到 _active_workers 是因为它们的生命周期信号是「业务完成」而非「线程结束」，
        # 需单独成表才能既防止 GC、又在关窗时统一 requestInterruption + wait
        self._pan_workers = {}
        # 计算期间被禁用的主按钮原始文案（完成后复原，避免「计算中…」残留）
        self._calc_btn_texts = {}
        # 超时仍未结束、已从父对象摘除的历史查询/导出/连通测试线程
        self._deferred_threads = []
        # 当前打开的设置对话框（模态期间主窗口无法关闭，仅作为统一收尾入口）
        self._settings_dialog = None
        # 计算器与 Service 改为惰性构造（见下方 @property），避免冷启动阻塞
        self._bazi_calc = None
        self._lunar_conv = None
        self._solar_calc = None
        self._location_db = None
        self._meihua_calc = None
        self._hexagram_analyzer = None
        self._bazi_service = None
        # DatabaseManager 由后台线程异步打开（见 _init_db_async）
        self._db_manager = None
        self._db_manager_ready = False
        # 关窗收尾状态：一旦进入延迟关闭流程，重复 closeEvent 一律忽略
        self._shutdown_requested = False
        self._shutdown_force_allowed = False
        self._shutdown_grace_timer = None
        # 先连接就绪信号，再启动后台线程；显式排队连接，确保回调在 UI 线程执行
        self.db_ready_changed.connect(self._on_db_ready, Qt.QueuedConnection)
        self._init_db_async()
        # 最近一次排盘记录 ID 及其所在表（供 AI 回调写回正确的表）
        # 八字 Service 路径写 analysis_records；梅花及八字回退路径写 pan_records
        self._last_bazi_record_id = None
        self._last_meihua_record_id = None
        self._last_xuan_kong_record_id = None
        self._last_bazi_record_table = None
        self._last_meihua_record_table = None
        self._last_xuan_kong_record_table = None
        # 最近一次八字输入（含出生日期/地点）
        self._last_bazi_input = None
        # 「重新分析」按钮引用与在途状态（跳过缓存重算的 UI 侧控制）
        self._reanalyze_btns = {}
        self._reanalyze_busy = set()
        # ===== R4: AI 降级检测 + 配置热更新订阅 =====
        self._ai_available = self._check_ai_availability()
        self._update_ai_buttons_state()
        self._subscribe_ai_config()

    # ===== 惰性计算器 / Service（冷启动优化：首次 _do_* 用户操作时才构造） =====
    @property
    def bazi_calc(self):
        if self._bazi_calc is None:
            # 冷启动优化：延迟导入 core.bazi.bazi_calculator。
            # 其 import 会触发 core.bazi._baazi_compat._ensure() → 同步加载日历 DB（~1.5s）。
            from core.bazi.bazi_calculator import BaziCalculator
            self._bazi_calc = BaziCalculator()
        return self._bazi_calc

    @property
    def lunar_conv(self):
        if self._lunar_conv is None:
            # 同上：core.lunar_converter 亦 import `_baazi_compat`，一并延迟。
            from core.lunar_converter import LunarConverter
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
        """返回已就绪的 DatabaseManager；后台初始化未完成时返回 None。

        绝不阻塞主线程：冷启动时 getter 立即返回 None，调用方按未就绪处理
        （写记录/日志失败走既有降级分支），就绪后由 db_ready_changed 信号
        触发界面恢复动作。调用方必须容忍 None。
        """
        return self._db_manager

    def _init_db_async(self):
        """后台线程打开 SQLite，避免冷启动阻塞；完成后置 _db_manager 并发出就绪信号。

        SQLite 连接本身线程安全；DatabaseManager 单例在构造期注册，重复访问幂等。
        就绪/失败均发 db_ready_changed(bool)，UI 线程据此恢复配置或提示降级。
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
            try:
                # 跨线程信号：Qt 自动排队到 UI 线程执行 _on_db_ready
                self.db_ready_changed.emit(dm is not None)
            except Exception:
                pass

        # 持有线程引用：关闭窗口时需 join 收尾，避免解释器退出阶段该线程仍执行
        # SQLite 初始化，与 finalize 竞争触发 0xC0000005 / 0xC0000374
        self._db_thread = threading.Thread(target=_open, daemon=True, name='kp-db-init')
        self._db_thread.start()

    def _on_db_ready(self, ok: bool):
        """数据库后台初始化完成回调：就绪则补做界面配置还原，失败则提示降级。"""
        try:
            if ok:
                sb = self.statusBar()
                if sb is not None:
                    sb.showMessage('本地数据库已就绪', 3000)
                # 启动时未就绪跳过的配置还原，此刻补做一次
                self._restore_ui_settings()
            else:
                sb = self.statusBar()
                if sb is not None:
                    sb.showMessage('本地数据库初始化失败：历史记录与 AI 回写不可用')
                self._logger.warning('[DB] 后台初始化失败，已进入降级模式')
        except Exception as e:
            self._logger.warning(f'[DB] 就绪回调处理异常：{e}')

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
            msg = '文化研究算法功能当前不可用，请在「设置」中配置 AI 模型'

        for attr in ('bazi_result', 'meihua_result'):
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

        # 「重新分析」入口同样受 AI 可用性约束：不可用时一律隐藏
        if not self._ai_available:
            for btn in getattr(self, '_reanalyze_btns', {}).values():
                btn.setVisible(False)
                btn.setEnabled(False)

    # ===== AI「重新分析」入口（跳过缓存） =====

    def _build_reanalyze_buttons(self):
        """在八字/梅花结果面板标题栏挂「重新分析」小按钮。

        两个面板的类各不相同（ResultPanel / MeihuaResultPanel），
        但都把「智能分析」按钮暴露为 smart_analyze_btn，故统一以它为锚点插入左侧，
        不抢占主按钮位置；样式复用 Stylesheets.BTN_SECONDARY（浅灰、6px 圆角），
        不新增颜色或改动分栏比例。
        """
        for kind, panel in (('bazi', self.bazi_result),
                            ('meihua', self.meihua_result)):
            btn = QPushButton('重新分析')
            btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip('跳过本地缓存，重新请求 AI 解读（会覆盖已有解读）')
            btn.setVisible(False)
            btn.setEnabled(False)
            btn.clicked.connect(
                lambda _checked=False, k=kind: self._start_reanalyze(k))
            hdr = self._panel_header_layout(panel)
            anchor = getattr(panel, 'smart_analyze_btn', None)
            if hdr is None:
                # 兜底：找不到标题栏时把按钮挂在面板本身（不可见，不影响布局）
                btn.setParent(panel)
            else:
                idx = hdr.indexOf(anchor) if anchor is not None else -1
                if idx >= 0:
                    hdr.insertWidget(idx, btn)
                else:
                    hdr.addWidget(btn)
            self._reanalyze_btns[kind] = btn

    @staticmethod
    def _panel_header_layout(panel):
        """取结果面板的标题栏布局：ResultPanel 走 _header_layout，
        其余面板标题栏是根布局的第 0 项子布局。"""
        hdr = getattr(panel, '_header_layout', None)
        if hdr is not None:
            return hdr
        root = panel.layout()
        if root is not None and root.count():
            item = root.itemAt(0)
            if item is not None:
                return item.layout()
        return None

    def _start_reanalyze(self, kind: str):
        """「重新分析」按钮槽：跳过缓存重跑对应板块的 AI 解读。"""
        if kind in getattr(self, '_reanalyze_busy', set()):
            return
        starters = {
            'bazi': self._on_bazi_ai_analyze,
            'meihua': self._on_meihua_ai_analyze,
        }
        starter = starters.get(kind)
        if starter is None:
            return
        starter(force_refresh=True)

    def _begin_ai_busy(self, kind: str):
        """AI 解读启动：禁用「重新分析」按钮，防止重复点击并发请求。"""
        busy = getattr(self, '_reanalyze_busy', None)
        if busy is None:
            return
        busy.add(kind)
        btn = self._reanalyze_btns.get(kind)
        if btn is not None:
            btn.setEnabled(False)

    def _end_ai_busy(self, kind: str, has_result: bool = True):
        """AI 解读结束：恢复按钮；有可复用结果且 AI 可用时才显示。"""
        busy = getattr(self, '_reanalyze_busy', None)
        if busy is None:
            return
        busy.discard(kind)
        btn = self._reanalyze_btns.get(kind)
        if btn is None:
            return
        btn.setVisible(bool(has_result) and bool(getattr(self, '_ai_available', False)))
        btn.setEnabled(True)

    def _hide_reanalyze(self, kind: str):
        """排盘开始/重置/记录被删：隐藏「重新分析」，避免对着失效结果重算。"""
        busy = getattr(self, '_reanalyze_busy', None)
        if busy is not None:
            busy.discard(kind)
        btn = self._reanalyze_btns.get(kind)
        if btn is not None:
            btn.setVisible(False)
            btn.setEnabled(False)

    # ===== AI worker 线程生命周期管理 =====

    def _register_worker(self, worker):
        """登记一个 AI worker，持有其引用直到运行结束再释放。

        防止两类崩溃：
        1. 局部/被覆盖的 QThread 在运行中被 Python GC 销毁；
        2. 同一属性（如 _meihua_ai_worker）被自动触发与手动按钮先后覆盖。
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

    def _shutdown_workers(self, timeout_ms: int = AI_SHUTDOWN_TIMEOUT_MS):
        """请求所有 AI worker 协作取消并等待收尾（绝不 terminate 强杀线程）。

        Returns:
            list: 超过 timeout_ms 仍未结束的 worker；空列表表示全部已安全收尾。
        """
        workers = list(getattr(self, '_active_workers', []))
        self._active_workers.clear()
        still_running = []
        for worker in workers:
            try:
                if worker is None:
                    continue
                if worker.isRunning():
                    # 协作式取消：只置标志，线程会自行走完当前原子操作（写库/写缓存）
                    canceller = getattr(worker, 'cancel', None) or getattr(worker, 'stop', None)
                    if callable(canceller):
                        canceller()
                    if not worker.wait(timeout_ms):
                        # 底层请求仍阻塞：继续持有引用，交给 closeEvent 的分层收尾处理
                        still_running.append(worker)
                        self._active_workers.append(worker)
                else:
                    worker.deleteLater()
            except RuntimeError:
                # 底层 C++ 对象已销毁，忽略
                pass
        if still_running:
            self._logger.warning(
                f"[退出] {len(still_running)} 个 AI 线程未在 {timeout_ms}ms 内结束，"
                f"进入「隐藏窗口等待收尾」层级（不使用 terminate）")
        return still_running

    def _shutdown_managed_threads(self, timeout_ms: int = None) -> list:
        """统一收尾历史查询 / 导出 / 设置连通测试三类线程（复用同一套机制）。

        这些线程此前不在 closeEvent 的收尾名单里，窗口销毁时仍在 run() 中，
        Qt 会打印 "QThread: Destroyed while thread is still running" 并崩溃。

        Args:
            timeout_ms: 单线程等待上限；None 用 AI_SHUTDOWN_TIMEOUT_MS。

        Returns:
            list: 超时仍未结束、已从父对象摘除并托管的线程。
        """
        if timeout_ms is None:
            timeout_ms = self.AI_SHUTDOWN_TIMEOUT_MS
        still_running = []
        panel = getattr(self, 'history_panel', None)
        fn = getattr(panel, 'shutdown_query', None)
        if callable(fn):
            still_running.extend(fn(timeout_ms))
        for attr in ('bazi_result', 'meihua_result', 'xuan_kong_result'):
            panel = getattr(self, attr, None)
            fn = getattr(panel, 'shutdown_exports', None)
            if callable(fn):
                still_running.extend(fn(timeout_ms))
        dialog = getattr(self, '_settings_dialog', None)
        fn = getattr(dialog, 'shutdown_test_worker', None)
        if callable(fn):
            still_running.extend(fn(timeout_ms))
        # 排盘/起卦后台线程：复用 ui/thread_shutdown.py 的统一收尾（协作取消 + wait）
        pan_workers = list(getattr(self, '_pan_workers', {}).values())
        getattr(self, '_pan_workers', {}).clear()
        if pan_workers:
            still_running.extend(shutdown_threads(pan_workers, timeout_ms))
        return still_running

    def _wait_db_init(self, timeout: float = 3.0):
        """等待后台 DB 初始化/种子校验线程收尾（绝不 terminate）。

        daemon 线程若在解释器退出阶段仍执行 SQLite 初始化，会与 finalize 竞争
        并触发 0xC0000005 / 0xC0000374。关窗前先 join；超时仅记 warning 后继续
        关窗，不阻塞用户。

        校验线程改为模块级统一收尾：DatabaseManager 已是进程内单例，
        不再存在「另一个实例的校验线程没人 join」的缺口。
        """
        th = getattr(self, '_db_thread', None)
        if th is not None and th.is_alive():
            th.join(timeout)
            if th.is_alive():
                try:
                    self._logger.warning(
                        f"[DB] 初始化线程未在 {timeout}s 内结束，继续关窗（不 terminate）")
                except Exception:
                    pass
        try:
            from core.database_manager import shutdown_db_background_tasks
            if not shutdown_db_background_tasks(timeout):
                self._logger.warning(
                    f"[DB] 种子校验线程未在 {timeout}s 内结束，继续关窗（不 terminate）")
        except Exception:
            pass

    def closeEvent(self, event):
        """关窗分层收尾：

        1) 协作取消 + wait(3s)，全部结束则正常关闭；
        2) 仍有线程阻塞（如已发出的 HTTP 请求）则隐藏窗口、忽略本次关闭，
           等 finished 信号后自动再关（用户无感知卡死）；
        3) 宽限期（30s）仍未结束则兜底放行关闭并留日志，全程不 terminate 线程。
        """
        # 先收尾后台 DB 初始化/校验线程，防止其存活到解释器退出阶段
        self._wait_db_init()
        if self._shutdown_force_allowed:
            self._save_ui_settings()
            super().closeEvent(event)
            return
        if self._shutdown_requested:
            # 延迟收尾期间重复触发的关闭请求（如再次 Alt+F4）直接忽略
            event.ignore()
            return

        still_running = self._shutdown_workers()
        # 历史查询 / 导出 / 设置连通测试线程：此前完全不在收尾名单里
        managed_running = self._shutdown_managed_threads()
        self._save_ui_settings()
        if not still_running and not managed_running:
            super().closeEvent(event)
            return

        # 层级 2：隐藏窗口，等待线程自然结束；不阻塞 GUI 事件循环
        self._shutdown_requested = True
        event.ignore()
        self.hide()
        self._deferred_threads = list(managed_running)
        for worker in still_running:
            try:
                worker.finished.connect(self._on_deferred_worker_finished)
            except Exception:
                pass
        for thread in managed_running:
            try:
                thread.finished.connect(self._on_deferred_worker_finished)
            except Exception:
                pass
        if self._shutdown_grace_timer is None:
            self._shutdown_grace_timer = QTimer(self)
            self._shutdown_grace_timer.setSingleShot(True)
            self._shutdown_grace_timer.timeout.connect(self._on_shutdown_grace_timeout)
        self._shutdown_grace_timer.start(self.AI_SHUTDOWN_GRACE_MS)

    def _on_deferred_worker_finished(self):
        """有 worker 结束：若全部收尾完成则真正关闭窗口。"""
        try:
            running = [w for w in list(self._active_workers) if w.isRunning()]
        except RuntimeError:
            running = []
        for thread in list(getattr(self, '_deferred_threads', [])):
            try:
                if thread.isRunning():
                    running.append(thread)
            except RuntimeError:
                continue
        if running:
            return
        self._finalize_deferred_close(forced=False)

    def _on_shutdown_grace_timeout(self):
        """层级 3 兜底：宽限期已到仍有线程未结束，放行关闭并留痕（不 terminate）。"""
        try:
            remaining = [w for w in list(self._active_workers) if w.isRunning()]
        except RuntimeError:
            remaining = []
        self._logger.warning(
            f"[退出] 宽限期 {self.AI_SHUTDOWN_GRACE_MS}ms 已到，仍有 "
            f"{len(remaining)} 个 AI 线程未结束，执行兜底退出（不 terminate 线程）")
        self._finalize_deferred_close(forced=True)

    def _finalize_deferred_close(self, forced: bool = False):
        """延迟关闭收尾：停表、保存设置，并以「允许强制关闭」状态再次 close()。"""
        if self._shutdown_grace_timer is not None:
            self._shutdown_grace_timer.stop()
        self._shutdown_requested = True
        self._shutdown_force_allowed = True
        if not forced:
            self._logger.info('[退出] AI 线程已全部收尾，完成延迟关闭')
        self._save_ui_settings()
        self.close()

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
            # DB 可能仍在后台冷读（约 1s），此时按默认布局并直接返回；
            # 就绪后由 db_ready_changed 信号回调 _on_db_ready 再触发本方法（不再轮询）
            if not self._db_manager_ready:
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
                total = left + right
                # M7：旧版本受 460 硬上限影响，存档比例约 32%；若历史配置偏离
                # 目标 35% 超过 2 个百分点，视为陈旧值，交由 _apply_responsive
                # 按 35/65 重算，避免旧配置把分栏缺陷带回来。
                if abs(left / total - self.SPLIT_LEFT_RATIO) <= 0.02:
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
        """记录一条操作记录（异步投递到后台队列，失败静默降级，不阻断 UI）。

        返回 True 表示已成功入队，False 表示当前无可用数据库或队列已满。
        真正的 SQLite 写入由后台 daemon 线程串行执行，GUI 线程不再触碰数据库。
        """
        try:
            mgr = self.db_manager
            if mgr is None:
                return False
            return _enqueue_op_log(mgr, {
                'op_type': op_type,
                'op_object': op_object,
                'user_id': 0,
                'session': self._session_id,
                'detail': detail,
            })
        except Exception as e:
            self._logger.warning(f"[操作记录] 投递失败：{e}")
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
        # 拉伸因子决定窗口缩放时的自适应比例（左 35 : 右 65）
        self.splitter.setStretchFactor(0, 35)
        self.splitter.setStretchFactor(1, 65)
        # 延迟到窗口几何可用时，按断点初始化 splitter + 发密度信号（M2-2）
        QTimer.singleShot(0, self._apply_responsive)

        # 左侧
        self.left_stack = QStackedWidget()
        self.left_stack.setStyleSheet("background: transparent;")
        # 左侧输入面板：只设下限，宽度由 SPLIT_LEFT_RATIO（35%）决定；
        # 不再设 460 硬上限，否则 1440 宽下比例失效（实测被压到 31.97%）
        self.left_stack.setMinimumWidth(360)
        self._build_left()
        self.splitter.addWidget(self.left_stack)

        # 右侧
        self.right_stack = QStackedWidget()
        self.right_stack.setStyleSheet("background: transparent;")
        # 右侧结果面板：自适应填满，设最小宽度防止内容被截断
        self.right_stack.setMinimumWidth(460)
        self._build_right()
        self.splitter.addWidget(self.right_stack)
        # AI 解读「重新分析（跳过缓存）」入口：挂在三个结果面板标题栏
        self._build_reanalyze_buttons()
        # 历史面板与主窗口接线：载入/删除交给主窗口处理；refresh_requested 不回接，
        # 否则面板刷新会再次触发自身刷新（自激）。
        self._wire_history_panel()

        root.addWidget(self.splitter, 1)

        # 状态栏
        sb = QStatusBar()
        sb.setStyleSheet(Stylesheets.STATUS)
        sb.showMessage('八字排盘 · 梅花易数 · 玄空飞星 · 文化研究算法自动分析')
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
        """构建左侧输入面板栈：依次加入八字/梅花/玄空飞星三个输入面板 + 历史记录。"""
        self.bazi_input = InputPanel()
        self.left_stack.addWidget(self.bazi_input)
        self.meihua_input = MeihuaInputPanel()
        self.left_stack.addWidget(self.meihua_input)
        self.xuan_kong_input = XuanKongInputPanel()
        self.left_stack.addWidget(self.xuan_kong_input)
        # 历史记录页：面板自带列表 + 详情预览，右侧不再重复渲染
        self.history_panel = HistoryPanel()
        self.left_stack.addWidget(self.history_panel)

    def _build_right(self):
        """构建右侧结果面板栈：依次加入八字/梅花/玄空飞星三个结果面板 + 历史提示页。"""
        self.bazi_result = ResultPanel()
        self.right_stack.addWidget(self.bazi_result)
        self.meihua_result = MeihuaResultPanel()
        self.right_stack.addWidget(self.meihua_result)
        self.xuan_kong_result = XuanKongResultPanel()
        self.right_stack.addWidget(self.xuan_kong_result)
        # 历史记录页的右侧说明页：详情已在左栏面板内展示，这里只给轻量提示
        self.right_stack.addWidget(self._build_history_hint_page())

    def _build_history_hint_page(self) -> QWidget:
        """构建历史记录模块的右侧说明页（轻量占位，不重复渲染详情）。"""
        page = QWidget()
        page.setStyleSheet(f"background-color: {Colors.BG};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(Spacing.S8, Spacing.S8, Spacing.S8, Spacing.S8)
        lay.setSpacing(Spacing.S3)

        title = QLabel('历史记录')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT}; font-family: {Fonts.TITLE};
        """)
        lay.addWidget(title)

        hint = QLabel(
            '左侧可按板块、日期与关键字筛选历史记录，选中单条即可预览参数与结论。\n'
            '「载入」只会把原始输入回填到对应板块（不会自动排盘），确认参数后请手动点提交。\n'
            '「删除」为二次确认后的硬删除，命中当前排盘记录时会同时清空右侧结果与 AI 面板。'
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"""
            font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2};
            font-family: {Fonts.BODY}; line-height: 1.6;
        """)
        lay.addWidget(hint)
        lay.addStretch()
        return page

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
        - S  (900–1099)：紧凑双栏，左栏 min 320，按 35% 分配。
        - M/L(≥1100)：标准/宽屏双栏，左栏 min 360，按 35% 分配（不再封顶 460）。
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
            self.left_stack.setMaximumWidth(16777215)   # 解除 460 硬上限
            self.right_stack.setMinimumWidth(320)
            left = int(w * self.SPLIT_LEFT_RATIO)
            self.splitter.setSizes([left, w - left])
        else:                                        # M/L：标准 / 宽屏双栏
            self.splitter.setOrientation(Qt.Horizontal)
            self.left_stack.setMinimumWidth(360)
            self.left_stack.setMaximumWidth(16777215)   # 解除 460 硬上限，让 35% 生效
            self.right_stack.setMinimumWidth(460)
            left = int(w * self.SPLIT_LEFT_RATIO)
            self.splitter.setSizes([left, w - left])
        self.density_changed.emit(self._current_density())

    def _apply_splitter_ratio(self):
        """历史兼容别名：委托 _apply_responsive（M2-2 重命名）。

        窗口缩放时由 QSplitter 依据 stretch 因子自适应维持比例；
        左栏不再封顶，始终按 35% 分配，避免大屏上比例漂移。
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
            pid: 板块 id，取值 'bazi'/'meihua'/'xuan_kong'/'history'

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
            # P2-11：只有 QGraphicsOpacityEffect 才有 setOpacity()。若复用
            # QGraphicsDropShadowEffect（投影）去调 setOpacity() 会抛 AttributeError，
            # 被外层 except 吞掉后淡入静默失效。因此这里必须判类型：非 opacity effect
            # 时新建一个透明度 effect，绝不把阴影对象当透明度对象用。
            if isinstance(eff, QGraphicsOpacityEffect):
                op = eff
                installed_by_us = False
            else:
                op = QGraphicsOpacityEffect(widget)
                widget.setGraphicsEffect(op)
                installed_by_us = True
            op.setOpacity(0.0)
            anim = QPropertyAnimation(op, b'opacity', self)
            anim.setDuration(DURATION_NORMAL)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(EASING_OUT)
            widget._page_fade_anim = anim
            widget._page_fade_eff = op

            def _cleanup():
                """动画终止后复原：自装 effect 则摘除，复用 effect 则把透明度还原。"""
                if installed_by_us:
                    try:
                        widget.setGraphicsEffect(None)
                    except RuntimeError:
                        pass
                else:
                    try:
                        op.setOpacity(1.0)
                    except RuntimeError:
                        pass

            def _on_state(state, _anim=anim, _widget=widget):
                """状态机兜底：`stop()` 不会发 finished，只靠 finished 会残留半透明页面。

                仅当本动画仍是该 widget 的当前动画时才清理，避免快速连续切换板块时，
                旧动画的 Stopped 信号误拆新动画刚装好的 effect。
                """
                if (state == QAbstractAnimation.Stopped
                        and getattr(_widget, '_page_fade_anim', None) is _anim):
                    _cleanup()

            anim.finished.connect(_cleanup)
            anim.stateChanged.connect(_on_state)
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
        self.xuan_kong_input.submit_btn.clicked.connect(self._on_xuan_kong)
        self.xuan_kong_input.reset_btn.clicked.connect(self._on_xuan_kong_reset)
        self.xuan_kong_result.refresh_btn.clicked.connect(self._on_xuan_kong)

    # ===== 历史记录面板接线 =====
    def _wire_history_panel(self):
        """接线历史面板：只接「载入 / 删除」意图。

        `refresh_requested` 刻意不连接：面板刷新本身就是由它发起，
        回接会形成「刷新→信号→刷新」的自激循环。
        """
        self.history_panel.load_requested.connect(self._on_history_load_requested)
        self.history_panel.delete_requested.connect(self._on_history_delete_requested)

    @staticmethod
    def _as_int(value, default=0):
        """安全转 int：缺值/非数字回落默认值（历史 payload 可能来自旧库）。"""
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_hhmm(text):
        """从含 `HH:MM` 的文本中取 (时, 分)；解析失败返回 None。"""
        import re
        m = re.search(r'(\d{1,2}):(\d{2})', str(text or ''))
        if not m:
            return None
        hh, mm = int(m.group(1)), int(m.group(2))
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return hh, mm
        return None

    @staticmethod
    def _payload_date_text(payload):
        """把 payload 的年月日拼成可读日期；不完整时回落到 time_str。"""
        try:
            return (f"{int(payload.get('year')):04d}-"
                    f"{int(payload.get('month')):02d}-"
                    f"{int(payload.get('day')):02d}")
        except (TypeError, ValueError):
            return str(payload.get('time_str') or '').strip()

    def _on_history_load_requested(self, pan_kind, record_id, payload):
        """历史面板「载入」槽：切板块 → 重置 → 回填原始输入，**不自动排盘**。

        Args:
            pan_kind: 'bazi' / 'meihua' / 'xuan_kong'
            record_id: 记录 ID（仅用于日志/提示，回填以 payload 为准）
            payload: 原始输入 dict（优先来自 input_json，旧库为反推结果）
        """
        loaders = {
            'bazi': (self._load_bazi_payload, '八字', '开始排盘'),
            'meihua': (self._load_meihua_payload, '梅花', '起卦'),
            'xuan_kong': (self._load_xuan_kong_payload, '玄空', '起盘'),
        }
        entry = loaders.get(pan_kind)
        if entry is None:
            self.statusBar().showMessage('未知的板块类型，无法载入该记录')
            return
        if not isinstance(payload, dict) or not payload:
            self.statusBar().showMessage('该记录缺少原始输入，无法一键载入')
            return
        loader, label, submit_hint = entry
        # 1) 先切到对应板块，让用户直接看到回填结果
        self._switch(pan_kind)
        # 2) 复用板块自身的重置逻辑，清掉上次输入、结果与 AI 面板
        self._reset_panel_for_kind(pan_kind)
        # 3) 仅回填控件；不触发提交，用户确认参数后自行点提交
        try:
            desc = loader(payload)
        except Exception as exc:  # noqa: BLE001 - 单条记录脏数据不应打断主流程
            self._logger.warning(f'[历史] {label}记录回填失败: {exc}')
            self.statusBar().showMessage(f'{label}记录回填失败：{exc}')
            return
        desc = (desc or '').strip()
        prefix = f'已载入 {desc} 的{label}记录' if desc else f'已载入该条{label}记录'
        self.statusBar().showMessage(f'{prefix}，确认参数后点「{submit_hint}」')

    def _reset_panel_for_kind(self, pan_kind):
        """按板块调用既有重置槽（同时清空结果面板与 AI 区域）。"""
        resets = {
            'bazi': self._on_bazi_reset,
            'meihua': self._on_meihua_reset,
            'xuan_kong': self._on_xuan_kong_reset,
        }
        resets[pan_kind]()

    def _load_bazi_payload(self, payload):
        """回填八字输入面板；返回用于状态提示的时间描述。"""
        p = self.bazi_input
        p.name_edit.setText(str(payload.get('name') or ''))
        is_lunar = bool(payload.get('is_lunar'))
        # 先切历法按钮与日期页，再写入具体日期
        p._cal(not is_lunar)
        y, m, d = (self._as_int(payload.get('year'), 0),
                   self._as_int(payload.get('month'), 1),
                   self._as_int(payload.get('day'), 1))
        if is_lunar:
            if y:
                p.lunar_picker.set_lunar(y, m, d, bool(payload.get('is_leap')))
                # 农历日期变化后同步真太阳时展示（_cal 早于本次赋值执行过一次）
                p._refresh_true_solar()
        elif y and 1 <= m <= 12 and 1 <= d <= 31:
            p.date_edit.setDate(QDate(y, m, d))
        # 性别
        p._gen(str(payload.get('gender') or '男') == '男')
        # 时分：优先取 hour/minute，缺失时按 hour_index 反算
        hour = self._as_int(payload.get('hour'), -1)
        if 0 <= hour <= 23:
            p.hour_spin.setValue(hour)
            p.minute_spin.setValue(max(0, min(59, self._as_int(
                payload.get('minute'), 0))))
        else:
            idx = self._as_int(payload.get('hour_index'), -1)
            if 0 <= idx <= 11:
                p.hour_combo.setCurrentIndex(idx)
        p.location_edit.setText(str(payload.get('location') or ''))
        # 经纬度回填：历史记录（input_json）中保存的坐标写回面板；
        # 旧记录无该字段时保留面板当前值，非法值抛 ValueError 由上层提示，绝不静默回落
        p.set_coordinates(payload.get('longitude'), payload.get('latitude'))
        p.notes_edit.setPlainText(str(payload.get('notes') or ''))
        p._sync_time_label()
        p._validate()
        return self._payload_date_text(payload)

    def _load_meihua_payload(self, payload):
        """回填梅花易数输入面板（含数字起卦取数、六爻、笔画等）。"""
        p = self.meihua_input
        method = str(payload.get('method') or 'time')
        idx = next((i for i, (key, _) in enumerate(MEIHUA_METHODS) if key == method), 0)
        p.method_btns[idx].setChecked(True)
        p._on_method(idx)
        p.question.setText(str(payload.get('question') or ''))
        cat = payload.get('question_category')
        if cat:
            i = p.question_category.findText(str(cat))
            if i >= 0:
                p.question_category.setCurrentIndex(i)

        if method == 'number':
            # 数字起卦：优先单个字段，缺失时回落到 numbers 数组
            nums = payload.get('numbers') or []
            n1 = payload.get('num1', payload.get('upper_num'))
            n2 = payload.get('num2', payload.get('lower_num'))
            if n1 is None and len(nums) > 0:
                n1 = nums[0]
            if n2 is None and len(nums) > 1:
                n2 = nums[1]
            if n1 is not None:
                p.num1.setValue(self._as_int(n1, 3))
            if n2 is not None:
                p.num2.setValue(self._as_int(n2, 5))
            if hasattr(p, 'num3'):
                n3 = payload.get('num3')
                if n3 is None and len(nums) > 2:
                    n3 = nums[2]
                if n3 is not None:
                    p.num3.setValue(self._as_int(n3, 7))
        elif method == 'direction':
            i = p.dir_combo.findText(str(payload.get('direction') or ''))
            if i >= 0:
                p.dir_combo.setCurrentIndex(i)
        elif method == 'text':
            p.text_edit.setText(str(payload.get('text') or ''))
            mode = str(payload.get('character_mode') or 'single')
            p.char_mode_combo.setCurrentIndex(1 if mode == 'multi' else 0)
        elif method == 'copper_coin':
            lines = payload.get('six_lines') or []
            for i, val in enumerate(lines[:6]):
                btns = (p.coin_radio_buttons[i]
                        if i < len(p.coin_radio_buttons) else [])
                for rb in btns:
                    if rb.text() == val:
                        rb.setChecked(True)
                        break
        elif method == 'stroke':
            p.stroke_char_edit.setText(str(payload.get('char') or ''))
            if payload.get('stroke_count') is not None:
                p.stroke_spin.setValue(
                    self._as_int(payload.get('stroke_count'), 12))

        # 时间起卦：还原历法、年月日与时分
        if method == 'time':
            if str(payload.get('calendar_type') or '公历') == '农历':
                y = self._as_int(payload.get('year'), 0)
                m = self._as_int(payload.get('month'), 1)
                d = self._as_int(payload.get('day'), 1)
                hh = self._as_int(payload.get('hour'), 0)
                parsed = self._parse_hhmm(payload.get('time_str'))
                mm = parsed[1] if parsed else 0
                # 先标记已初始化，避免切农历时被当前时间覆盖
                p._lunar_initialized = True
                p.cal_lunar.setChecked(True)
                p.time_stack.setCurrentIndex(1)
                if y:
                    p.lunar_picker.set_lunar(
                        y, m, d, bool(payload.get('is_leap')))
                p.lunar_hour_spin.setValue(hh)
                p.lunar_minute_spin.setValue(mm)
            else:
                p.cal_solar.setChecked(True)
                p.time_stack.setCurrentIndex(0)
                p.time_edit.setText(str(payload.get('time_str') or ''))

        return self._payload_date_text(payload)

    def _load_xuan_kong_payload(self, payload):
        """回填玄空飞星输入面板（坐向 + 建造年份 + 当前年份）。"""
        p = self.xuan_kong_input
        build = payload.get('build_year')
        current = payload.get('current_year')
        p.sui_xiang_edit.setText(str(payload.get('sui_xiang') or '子山午向'))
        p.build_year_edit.setText('' if build is None else str(build))
        p.current_year_edit.setText(
            str(current) if current is not None else
            ('' if build is None else str(build)))
        xiang = p.sui_xiang_edit.text().strip()
        year = p.build_year_edit.text().strip()
        return f'{xiang} · {year}年' if xiang and year else xiang

    def _on_history_delete_requested(self, entries):
        """历史面板「删除」槽：命中当前记录时清空记录态与 AI 面板。

        Args:
            entries: [{'source_table': 'pan_records'|'analysis_records', 'id': int}]
        """
        deleted = set()
        for item in entries or []:
            if isinstance(item, dict):
                table, rid = item.get('source_table'), item.get('id')
            elif isinstance(item, (tuple, list)) and len(item) == 2:
                table, rid = item
            else:
                continue
            try:
                deleted.add((str(table), int(rid)))
            except (TypeError, ValueError):
                continue
        if not deleted:
            self.statusBar().showMessage('历史记录已删除')
            return

        cleared = []
        for kind, label in (('bazi', '八字'), ('meihua', '梅花'),
                            ('xuan_kong', '玄空')):
            rid = getattr(self, f'_last_{kind}_record_id', None)
            table = getattr(self, f'_last_{kind}_record_table', None) or 'pan_records'
            if rid is None:
                continue
            try:
                hit = (table, int(rid)) in deleted
            except (TypeError, ValueError):
                hit = False
            if not hit:
                continue
            setattr(self, f'_last_{kind}_record_id', None)
            setattr(self, f'_last_{kind}_record_table', None)
            self._hide_reanalyze(kind)
            cleared.append(label)

        if not cleared:
            self.statusBar().showMessage('历史记录已删除')
            return
        # 记录已删而界面仍挂着上次结果会误导用户，故同步清空结果与 AI 区域
        if '八字' in cleared:
            self.bazi_result.clear()
            self._last_bazi_input = None
        if '梅花' in cleared:
            self.meihua_result.clear()
        if '玄空' in cleared:
            self.xuan_kong_result.clear()
        self.statusBar().showMessage(
            f'历史记录已删除 · 已清空当前{"/".join(cleared)}结果')

    def _show_settings_dialog(self):
        """打开 AI 模型配置对话框（保存后热生效，无需重启）。"""
        try:
            dlg = SettingsDialog(self)
            # 登记在途对话框：关窗统一收尾时能拿到它的连通测试线程
            self._settings_dialog = dlg
            try:
                dlg.exec()
            finally:
                self._settings_dialog = None
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

    def _save_pan_record(self, data: dict, result: dict, pan_type: str, ai_result: dict = None,
                         notify: bool = True):
        """保存排盘记录到数据库。返回值: record_id 或 None

        Args:
            notify: 是否在 GUI 线程侧更新状态栏 / AI 按钮状态。后台线程调用时必须
                传 False —— 状态栏属 UI 对象，只能在 GUI 线程操作；记录 ID 与所在表
                由调用方在回到 GUI 线程后再写入实例属性。
        """
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
            # 无真实生辰信息（如梅花）时留空，避免写入 "0000-00-00" 垃圾值
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
                ai_analysis=ai_result,
                # 完整原始输入随记录落库，历史面板「一键载入」优先使用它
                input_json=dict(data)
            )

            if record_id:
                # notify=False 时运行在后台线程：不得触碰控件/状态栏，只回传记录信息
                if not notify:
                    return record_id
                # 记录当前模块的最后一条 record_id 及其所在表（pan_records），供 AI 回调写回
                if pan_type == '八字排盘':
                    self._last_bazi_record_id = record_id
                    self._last_bazi_record_table = 'pan_records'
                elif pan_type == '梅花易数':
                    self._last_meihua_record_id = record_id
                    self._last_meihua_record_table = 'pan_records'
                elif pan_type == '玄空飞星':
                    # 玄空无 AI 链路，但需记住记录态，供历史删除联动清空右侧结果
                    self._last_xuan_kong_record_id = record_id
                    self._last_xuan_kong_record_table = 'pan_records'
                # 新一轮排盘结果已落库：允许「重新分析」（AI 不可用时保持隐藏）
                _kind = {'八字排盘': 'bazi', '梅花易数': 'meihua'}.get(pan_type)
                if _kind:
                    self._end_ai_busy(_kind, has_result=bool(getattr(self, '_ai_available', False)))
                self.statusBar().showMessage(f'排盘完成 · 已保存到数据库 · 记录ID: {record_id}')
            else:
                self._logger.warning(f"[排盘] 保存记录失败，record_id={record_id}")
                if notify:
                    self.statusBar().showMessage('排盘完成 · 保存到数据库失败')
        except Exception as e:
            self._logger.error(f"[排盘] 保存排盘记录失败: {e}", exc_info=True)
            if notify:
                self.statusBar().showMessage('排盘完成 · 保存到数据库失败')
            return None

        return record_id

    def _persist_ai_analysis(self, pan_kind: str, ai_analysis: dict) -> bool:
        """把 AI 解读写回对应板块的历史记录，失败时状态栏给出可见提示。

        两个板块（八字/梅花）统一走本方法：按落库时记录的「记录所在表」
        选择 analysis_records 或 pan_records，避免拿 A 表的 id 去更新 B 表
        （那会 rowcount=0 静默失败，甚至误伤同 id 的无关记录）。

        Args:
            pan_kind: 'bazi' / 'meihua'
            ai_analysis: AI 解读结果字典

        Returns:
            bool: True 表示已写入；False 表示未写入（无记录/记录不存在/异常）
        """
        label = {'bazi': '八字', 'meihua': '梅花'}.get(pan_kind, pan_kind)
        record_id = getattr(self, f'_last_{pan_kind}_record_id', None)
        table = getattr(self, f'_last_{pan_kind}_record_table', None)

        if not self.db_manager or not record_id or not table:
            self.statusBar().showMessage(
                f'{label}AI解读完成，但未找到对应历史记录，未写回数据库')
            self._logger.warning(
                f'[AI] {label}解读未写回：record_id={record_id}, table={table}')
            return False

        try:
            if table == 'analysis_records':
                ok = self.db_manager.update_analysis_ai(record_id, ai_analysis)
            else:
                ok = self.db_manager.update_pan_ai_result(record_id, ai_analysis)
        except Exception as e:
            ok = False
            self._logger.error(f'[AI] {label}解读写回异常: {e}', exc_info=True)

        if not ok:
            # 不能静默吞掉：状态栏明确告知用户「解读成功但没存进历史」
            self.statusBar().showMessage(
                f'{label}AI解读完成，但写回历史记录失败（记录ID {record_id}，表 {table}）')
            self._logger.warning(
                f'[AI] {label}解读写回失败：record_id={record_id}, table={table}')
        return ok

    # ===== 八字 =====
    def _on_bazi(self):
        """八字『开始排盘』按钮槽：GUI 线程只做轻量准备 + 启动后台线程。

        P1-01：原实现经 ``QTimer.singleShot(80)`` 后仍在 **GUI 线程**同步跑完整条
        计算链（首次加载 core 日历库 ~1.5s + 四柱/大运/落库 + 旧回退路径里的同步
        地理编码请求），点击后界面会出现数秒到数十秒的「未响应」。现在计算链整体
        下沉到 ``BaziCalculationWorker``，GUI 线程只保留：
            1) 读输入面板；
            2) 内置城市表解析出生地（纯内存查表，微秒级）；
            3) 置 loading / 禁用按钮 / 起线程。
        """
        try:
            data = self.bazi_input.get_data()
            task_id = str(uuid.uuid4())
            self._reap_pan_workers()
            existing = self._pan_workers.get('bazi')
            if existing is not None and existing.isRunning():
                # 防抖：按钮虽已禁用，仍拦住快捷键/脚本重复触发，避免双线程并发写库
                self.statusBar().showMessage('八字排盘正在进行中，请稍候…')
                return
            self._hide_reanalyze('bazi')
            self.bazi_result.show_loading()
            # 出生地文本解析：仅内置城市表，不联网、不调 AI，绝不阻塞事件循环
            data, location_note = self._prepare_bazi_location(data, apply_to_ui=True)
            self._begin_calc_busy('bazi', location_note or '正在后台排盘…')

            # 惰性导入：模块级导入会触发 core 日历库同步加载（~1.5s），冷启动会被拖慢
            from ui.components.bazi_calculation_worker import BaziCalculationWorker
            worker = BaziCalculationWorker(
                data, task=lambda w: self._compute_bazi_payload(data, w))
            worker.progress.connect(self._on_calc_progress)
            worker.finished.connect(self._on_bazi_task_finished)
            worker.failed.connect(self._on_bazi_task_failed)
            # 不在业务信号里立即 deleteLater：信号可能在 run() 返回前发出，
            # 此时销毁 QThread 会触发进程级崩溃。统一由 _reap_pan_workers()
            # 在确认 isRunning()==False 之后销毁。
            # 持有引用，避免局部变量被 GC（QThread: Destroyed while thread is running）
            self._pan_workers['bazi'] = worker
            worker.start()
        except Exception as e:
            self._end_calc_busy('bazi')
            self.statusBar().showMessage(f'参数错误: {e}')
            traceback.print_exc()
            # 排盘失败必须落到错误态：否则面板会永远停在 loading（转圈 + 按钮隐藏）
            self.bazi_result.show_error(f'排盘失败：{e}', retry=self._on_bazi)

    def _on_bazi_task_finished(self, payload):
        """后台八字计算成功回调（GUI 线程）：展示结果、恢复按钮、触发 AI。"""
        self._end_calc_busy('bazi')
        try:
            self._present_bazi_result(payload)
        except Exception as e:
            self._on_bazi_task_failed('present_error', str(e))
        self._reap_pan_workers('bazi')

    def _on_bazi_task_failed(self, error_type: str, message: str):
        """后台八字计算失败回调（GUI 线程）：给出可读错误，绝不静默。"""
        self._end_calc_busy('bazi')
        title = '输入错误' if error_type == 'validation_error' else '排盘失败'
        self._logger.warning(f'[八字] 后台计算失败({error_type}): {message}')
        self.statusBar().showMessage(f'{title}：{message}')
        self.bazi_result.show_error(f'{title}：{message}', retry=self._on_bazi)
        self._reap_pan_workers('bazi')

    def _do_bazi(self, data, task_id=None):
        """同步执行八字排盘（保留给直接调用/兼容旧行为）。

        GUI 按钮路径已改为 ``_on_bazi`` → 后台线程；本方法仍在当前线程同步执行
        整条链，仅供测试与不支持线程的调用方使用。

        Args:
            data: 输入面板数据（年/月/日/时/经纬度/农历标志/性别等）
            task_id: 本次排盘任务标识（预留，用于日志与并发追踪）
        """
        try:
            payload = self._compute_bazi_payload(data)
        except ValueError as e:
            # 农历由 core 层统一严格转换；转换失败直接报错，禁止按农历数字继续排盘
            self.statusBar().showMessage(f'农历转换失败：{e}')
            QMessageBox.warning(self, '输入错误', f'农历日期无效：{e}')
            self.bazi_result.show_error(f'排盘失败：{e}', retry=self._on_bazi)
            return
        except Exception as e:
            self.statusBar().showMessage(f'计算错误: {e}')
            traceback.print_exc()
            # 计算阶段异常同样要落错误态，避免面板卡在 loading
            self.bazi_result.show_error(f'排盘失败：{e}', retry=self._on_bazi)
            return
        self._present_bazi_result(payload)

    def _compute_bazi_payload(self, data, worker=None):
        """八字排盘纯计算（可在后台线程执行，不触碰任何 Qt 控件/状态栏）。

        Args:
            data: 输入面板数据（出生地解析会就地补全经纬度与 coords_source）
            worker: 可选后台线程对象，用于 emit 进度（同步调用时为 None）

        Returns:
            dict: ``{'result', 'record_id', 'record_table', 'source', 'location_note'}``

        Raises:
            ValueError: 农历日期非法，由调用方在 GUI 线程转成可读提示
        """
        def _progress(stage: str, message: str):
            if worker is not None:
                worker.progress.emit(stage, message)

        # 幂等：_on_bazi 已在 GUI 线程解析过时（coords_source='manual'）直接跳过
        data, location_note = self._prepare_bazi_location(data)

        try:
            # Service 主路径：业务编排（校验/计算/综合建议/落库/事件）
            if getattr(self, 'bazi_service', None):
                _progress('service', '正在调用 Service 层排盘…')
                try:
                    service_result = self.bazi_service.calculate(
                        year=int(data.get('year', 0)),
                        month=int(data.get('month', 1)),
                        day=int(data.get('day', 1)),
                        hour=int(data.get('hour', 0)),
                        minute=int(data.get('minute', 0)),
                        longitude=float(data.get('longitude', 120.0)),
                        latitude=float(data.get('latitude', 30.0)),
                        gender=data.get('gender', '男'),
                        save=True,
                        name=data.get('name', ''),
                        is_lunar=bool(data.get('is_lunar', False)),
                        is_leap=bool(data.get('is_leap', False)),
                        # 出生地文本必须透传：否则 analysis_records.city 落空串
                        location=data.get('location', ''),
                    )
                    record_id = service_result.get('record_id')
                    # Service 层落库到 analysis_records，AI 回写必须指向同一张表
                    record_table = 'analysis_records' if record_id else None
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
                    return {
                        'result': service_result,
                        'record_id': record_id,
                        'record_table': record_table,
                        'source': 'service',
                        'location_note': location_note,
                        'name': data.get('name', '未命名'),
                    }
                except Exception as e:
                    self._logger.warning(f"[Service] BaziService 计算失败，回退 core 流程: {e}")

            # 回退：原始 core 流程（兼容）
            _progress('core', '正在计算四柱与真太阳时…')
            y, m, d, hh, mm = data['year'], data['month'], data['day'], data['hour'], data['minute']
            longitude = data['longitude']
            latitude = data.get('latitude', 30.0)
            is_lunar = bool(data.get('is_lunar', False))
            is_leap = bool(data.get('is_leap', False))
            gender = data.get('gender', '男')

            # 出生地解析：手动文本 -> 经纬度（本地库优先，其次 AI，兜底默认）
            # 仅当坐标来源为 auto（沿用默认值或历史回填）时才允许文本覆盖；
            # 用户显式设定的经纬度永远优先，避免被静默替换成别的城市坐标
            loc_text = (data.get('location') or '').strip()
            if loc_text and data.get('coords_source', 'auto') == 'auto':
                longitude, latitude = self._resolve_location(loc_text, longitude, latitude)
                data['longitude'] = longitude
                data['latitude'] = latitude
                data['location'] = loc_text

            # 农历由 core 层统一严格转换；转换失败抛 ValueError，由 GUI 线程提示
            bazi = self.bazi_calc.calculate(
                y, m, d, hh, mm, longitude, is_lunar, is_leap, latitude)

            # 后续日期一律使用公历；公历输入时与原有逻辑完全一致
            try:
                sy, sm, sd = (int(x) for x in str(bazi.get('solar_date', '')).split('-')[:3])
            except Exception:
                sy, sm, sd = y, m, d
            y, m, d = sy, sm, sd

            dt = datetime(y, m, d, hh, mm)
            sdt = self.solar_calc.get_true_solar_time(dt, longitude)
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
                # 确保流年数据始终包含 years 字段，防止前端因空列表而不展示卡片
                if not liunian or not isinstance(liunian, dict):
                    liunian = {'years': []}
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
            _progress('types', '正在分析命局类型与运程…')
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
            _progress('save', '正在保存排盘记录…')
            # notify=False：本函数可能运行在后台线程，禁止触碰状态栏
            record_id = self._save_pan_record(data, result, '八字排盘', notify=False)
            return {
                'result': result,
                'record_id': record_id,
                'record_table': 'pan_records' if record_id else None,
                'source': 'core',
                'location_note': location_note,
                'name': data.get('name', '未命名'),
            }
        except ValueError:
            # 农历非法：原样抛出，交给 GUI 线程提示（不许静默按农历数字排盘）
            raise
        except Exception:
            # 其它异常原样抛出：worker 转 failed 信号，同步调用方兜底展示
            raise

    def _present_bazi_result(self, payload):
        """在 GUI 线程展示八字排盘结果（后台线程只回传纯数据）。

        Args:
            payload: ``_compute_bazi_payload`` 的返回值
        """
        result = payload['result']
        record_id = payload.get('record_id')
        # 记录态必须在 GUI 线程写入：AI 回写与历史删除联动都依赖它
        self._last_bazi_record_id = record_id
        self._last_bazi_record_table = payload.get('record_table') if record_id else None

        self.bazi_result.display_result(result)
        note = payload.get('location_note')
        if note:
            # 出生地解析结果必须让用户看得见，不能只写日志
            self.bazi_result.status_lbl.setText(f'✓ 排盘完成 · {note}')
        if record_id:
            self.statusBar().showMessage(f'八字排盘完成 · 记录ID: {record_id}')
        else:
            self.statusBar().showMessage('八字排盘完成 · 保存到数据库失败')

        # 操作记录（写入当前激活存储后端，算命内容本身不进统一层）
        info = result.get('basic_info', {})
        self._log_op(
            'bazi_divination',
            payload.get('name') or '未命名',
            f"{info.get('solar_date', '')} {info.get('hour', '')} {info.get('location', '')}".strip())

        # 新一轮结果可用：允许「重新分析」
        self._end_ai_busy('bazi', has_result=True)
        # ★ v5.0: 排盘完成后自动触发AI分析
        QTimer.singleShot(300, self._trigger_bazi_auto_ai)

    # ===== 出生地解析 / 计算中状态（两条缺陷共用） =====

    def _prepare_bazi_location(self, data: dict, apply_to_ui: bool = False):
        """在进入计算前统一解析出生地文本（P1-04），返回 ``(data, 提示文案)``。

        优先级规则（用户手填坐标永远最高）：
            1. ``coords_source`` 为 ``explicit``（用户改过经纬度）→ **不解析、不覆盖**；
            2. ``coords_source`` 为 ``manual``（本轮已按文本解析过）→ 跳过，保持幂等；
            3. 其余（``auto``，含历史回填与默认 120/30）→ 查内置城市表：
               - 命中：回填经纬度并置 ``coords_source='manual'``，提示「已按出生地…回填」；
               - 未命中：**不静默沿用默认值**，返回显式提示「无法解析出生地，将使用当前经纬度」。

        本方法只做内存查表（service/location_resolver），不联网、不调 AI，可在 GUI 线程调用。

        Args:
            data: 输入面板数据（就地补全 longitude/latitude/coords_source）
            apply_to_ui: 是否把解析结果回填到输入面板控件（仅 GUI 线程可置 True）

        Returns:
            tuple: ``(data, 提示文案或 None)``
        """
        from service.location_resolver import resolve_local

        source = data.get('coords_source', 'auto')
        text = (data.get('location') or '').strip()
        if source in ('explicit', 'manual') or not text:
            return data, None

        hit = resolve_local(text)
        if hit:
            name, lon, lat = hit
            data['longitude'] = lon
            data['latitude'] = lat
            if apply_to_ui:
                # GUI 主路径标记 manual：程序已按出生地文本回填，后续不再覆盖；
                # 非 GUI 调用（同步 _do_bazi/后台 calc）保留原 coords_source，
                # 由回退分支用同一个内置表幂等复算，结果完全一致。
                data['coords_source'] = 'manual'
                try:
                    self.bazi_input.set_coordinates(lon, lat)
                except Exception as e:
                    self._logger.debug(f'[出生地] 回填输入面板失败（不影响计算）: {e}')
            note = f'已按出生地「{name}」回填经度 {lon:.2f}°、纬度 {lat:.2f}°'
            self._logger.info(f'[出生地] 「{text}」→「{name}」({lon}, {lat})')
            return data, note

        lon = float(data.get('longitude', 120.0))
        lat = float(data.get('latitude', 30.0))
        note = f'无法解析出生地「{text}」，将使用当前经纬度 {lon:.2f}° / {lat:.2f}°'
        self._logger.warning(f'[出生地] {note}')
        return data, note

    def _begin_calc_busy(self, kind: str, message: str = ''):
        """排盘/起卦开始：禁用主按钮并提示进度，避免重复提交与「无反馈」体验。"""
        panel = {'bazi': getattr(self, 'bazi_input', None),
                 'meihua': getattr(self, 'meihua_input', None)}.get(kind)
        btn = getattr(panel, 'submit_btn', None)
        if btn is not None:
            self._calc_btn_texts.setdefault(kind, btn.text())
            btn.setEnabled(False)
            btn.setText('计算中…')
        if message:
            self.statusBar().showMessage(message)

    def _end_calc_busy(self, kind: str):
        """排盘/起卦结束：恢复主按钮文案与可用状态（失败路径也必须调用）。"""
        panel = {'bazi': getattr(self, 'bazi_input', None),
                 'meihua': getattr(self, 'meihua_input', None)}.get(kind)
        btn = getattr(panel, 'submit_btn', None)
        if btn is not None:
            btn.setText(self._calc_btn_texts.pop(kind, btn.text()))
            # 输入面板自带校验（姓名等必填项）：能校验就按校验结果恢复，否则直接放行
            validate = getattr(panel, '_validate', None)
            if callable(validate):
                validate()
            else:
                btn.setEnabled(True)

    def _on_calc_progress(self, stage: str, message: str):
        """后台排盘/起卦进度回调（GUI 线程）：状态栏可见进度。"""
        if message:
            self.statusBar().showMessage(f'{message}（{stage}）')

    def _reap_pan_workers(self, kind: str = None, attempt: int = 0):
        """回收已结束的排盘/起卦线程。

        必须等 ``isRunning()`` 为 False 才能 ``deleteLater()``：业务信号
        （finished/succeeded/failed）是在 run() 内部发出的，此时线程尚未退出，
        直接销毁 QThread 会触发进程级崩溃（0xC0000409）。``QThread::finished``
        也在 run() 返回后立即发出，但跨线程排队到 GUI 线程执行时，底层线程
        可能仍在收尾，因此这里对指定板块做短周期重试（最多 4s），确保「已停才删」。

        Args:
            kind: 指定板块；None 表示全量巡检一次且不重试（新任务开始前调用）。
            attempt: 内部重试计数，调用方无需传。
        """
        kinds = [kind] if kind else list(self._pan_workers)
        retry_needed = False
        for k in kinds:
            worker = self._pan_workers.get(k)
            if worker is None:
                continue
            try:
                running = worker.isRunning()
            except RuntimeError:
                # 底层对象已释放（已被 Qt 销毁），直接从表中移除
                self._pan_workers.pop(k, None)
                continue
            if not running:
                worker.deleteLater()
                self._pan_workers.pop(k, None)
            elif kind is not None and attempt < 40:
                retry_needed = True
        if retry_needed:
            QTimer.singleShot(100, lambda: self._reap_pan_workers(kind, attempt + 1))

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
            self.statusBar().showMessage('排盘完成 · 正在自动进行文化研究算法深度分析…')
            self._begin_ai_busy('bazi')

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
        """将出生地文本解析为（经度, 纬度），仅本地数据，绝不发起网络请求。

        P1-01：原实现本地库未命中时会同步调用 AI 地理编码（同步 HTTP + 重试
        sleep），在 GUI 线程执行会让界面「未响应」数十秒。现在只做本地解析：
            1) service/location_resolver 内置城市表（与输入面板下拉同一来源）；
            2) core.location_db 本地城市库；
            3) 均未命中返回回退坐标，由调用方显式提示用户（不静默）。
        """
        # 1) 内置城市表（唯一来源，纯内存查表）
        try:
            from service.location_resolver import resolve_local
            hit = resolve_local(text)
            if hit:
                name, lon, lat = hit
                self._logger.info(f"出生地「{text}」命中内置城市表：{name} ({lon}, {lat})")
                return float(lon), float(lat)
        except Exception as e:
            self._logger.debug(f"内置城市表解析失败（转本地库）: {e}")

        # 2) 本地城市库
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
            self._logger.debug(f"本地城市库解析失败: {e}")

        # 3) 兜底：不联网，交给调用方提示「无法解析出生地」
        self._logger.warning(
            f"出生地「{text}」无法解析，使用回退经纬度 ({fallback_lon}, {fallback_lat})")
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
        self._hide_reanalyze('bazi')
        self.bazi_input.clear()
        self.bazi_result.clear()

    # ===== 梅花 =====
    def _on_meihua(self):
        """梅花易数『起卦』按钮槽：校验输入后执行起卦（不再先弹关于对话框）。"""
        try:
            data = self.meihua_input.get_data()
            task_id = str(uuid.uuid4())
            self._reap_pan_workers()
            existing = self._pan_workers.get('meihua')
            if existing is not None and existing.isRunning():
                self.statusBar().showMessage('梅花起卦正在进行中，请稍候…')
                return
            self._hide_reanalyze('meihua')
            self.meihua_result.show_loading()
            # 起卦本身是毫秒级计算，但「落库写盘」与「AI 解读」必须离开 GUI 线程，
            # 见 _do_meihua 末尾的 PanTaskWorker；这里先给用户明确的计算中反馈
            self._begin_calc_busy('meihua', '正在起卦…')
            QTimer.singleShot(80, lambda: self._do_meihua(data, task_id))
        except Exception as e:
            self._end_calc_busy('meihua')
            self.statusBar().showMessage(f'参数错误: {e}')
            self._logger.warning(f"[梅花] 起卦参数校验失败: {e}")
            # 起卦失败必须落错误态：否则面板会永远停在 loading
            self.meihua_result.show_error(f'起卦失败：{e}', retry=self._on_meihua)


    def _do_meihua(self, data, task_id=None):
        """执行梅花易数起卦流程（由 _on_meihua 经定时器延迟调用）。

        Args:
            data: 输入面板数据（起卦方式 method、问题、各方式对应参数）
            task_id: 本次起卦任务标识（预留）

        按 method 分发到对应起卦算法，生成本/互/变/错/综卦并交由 HexagramAnalyzer 分析，
        展示结果、保存记录、记录操作，最后自动触发文化研究算法（AI）解读。
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
                # 农历输入先真实转换为公历，避免农历数字被直接当作公历参与起卦
                if data.get('calendar_type') == '农历':
                    solar = self.lunar_conv.lunar_to_solar(
                        year, month, day, bool(data.get('is_leap', False)))
                    if not solar:
                        raise ValueError("农历日期无效，请检查年月日是否正确")
                    original_date = f'{year}-{month}-{day}'
                    year, month, day = solar
                    data.update({'year': year, 'month': month, 'day': day,
                                 'calendar_type': '公历',
                                 'original_date': original_date,
                                 'original_calendar_type': '农历'})
                hr = self.meihua_calc.time_divination(year, month, day, hour, q)
            else:
                raise ValueError(f"未知起卦方式: {method}")

            if not hr:
                # 算法未返回卦象：必须恢复按钮，否则「计算中…」永久残留
                self._end_calc_busy('meihua')
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

            # 操作记录
            self._log_op('meihua_divination', method,
                         f"question={q}" if q else f"method={method}")

            # 保存到数据库（梅花易数也支持保存）：写库可能遇上 SQLite 写锁最长 30s，
            # 必须放到后台线程，完成后回 GUI 线程更新记录态并触发 AI 解读（P1-01）
            from ui.components.pan_task_worker import PanTaskWorker
            worker = PanTaskWorker(
                lambda w: self._save_pan_record(data, result, '梅花易数', notify=False),
                label='meihua_save')
            worker.succeeded.connect(self._on_meihua_save_finished)
            worker.failed.connect(self._on_meihua_save_failed)
            # 销毁交给 _reap_pan_workers（确认 isRunning()==False 后才 deleteLater）
            self._pan_workers['meihua'] = worker
            self._begin_calc_busy('meihua', '起卦完成 · 正在保存记录…')
            worker.start()
        except Exception as e:
            self._end_calc_busy('meihua')
            self.statusBar().showMessage(f'起卦错误: {e}')
            traceback.print_exc()
            # 起卦阶段异常同样要落错误态，避免面板卡在 loading
            self.meihua_result.show_error(f'起卦失败：{e}', retry=self._on_meihua)

    def _on_meihua_save_finished(self, record_id):
        """梅花落库成功回调（GUI 线程）：更新记录态、恢复按钮、触发 AI 解读。"""
        self._end_calc_busy('meihua')
        self._last_meihua_record_id = record_id
        self._last_meihua_record_table = 'pan_records' if record_id else None
        if record_id:
            self.statusBar().showMessage(f'梅花易数起卦完成 · 记录ID: {record_id}')
        else:
            self.statusBar().showMessage('梅花易数起卦完成 · 保存到数据库失败')
        self._end_ai_busy('meihua', has_result=True)
        # ★ v5.0: 起卦完成后自动触发AI解读（须等 record_id 落定，否则 AI 回写无目标）
        QTimer.singleShot(300, self._trigger_meihua_auto_ai)
        self._reap_pan_workers('meihua')

    def _on_meihua_save_failed(self, error_type: str, message: str):
        """梅花落库失败回调（GUI 线程）：显式提示，不静默。"""
        self._end_calc_busy('meihua')
        self._last_meihua_record_table = None
        self._logger.warning(f'[梅花] 后台落库失败({error_type}): {message}')
        self.statusBar().showMessage(f'梅花易数起卦完成 · 保存到数据库失败：{message}')
        self._end_ai_busy('meihua', has_result=True)
        QTimer.singleShot(300, self._trigger_meihua_auto_ai)
        self._reap_pan_workers('meihua')

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
            self.statusBar().showMessage('起卦完成 · 正在自动进行文化研究算法深度解读…')
            self._begin_ai_busy('meihua')

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
        self._hide_reanalyze('meihua')
        self.meihua_input.clear()
        self.meihua_result.clear()

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
            self.xuan_kong_result.show_error(f'排盘失败：{e}', retry=self._on_xuan_kong)

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
            # 少白屏：落统一错误态（含重试），而非静默 clear
            self.xuan_kong_result.show_error(f'排盘失败：{e}', retry=self._on_xuan_kong)

    def _on_xuan_kong_reset(self):
        """玄空飞星『重置』按钮槽：清空输入面板与结果面板。"""
        self.xuan_kong_input.clear()
        self.xuan_kong_result.clear()

    # ===== AI分析 =====

    def _on_bazi_ai_analyze(self, force_refresh: bool = False):
        """八字AI分析按钮点击处理。

        Args:
            force_refresh: True 时跳过 AI 结果缓存强制重新分析（「重新分析」入口使用）
        """
        try:
            input_data = self.bazi_input.get_data()
            self._last_bazi_input = input_data
            chart_data = self.bazi_result.get_chart_data_for_ai()

            if not chart_data or not chart_data.get('bazi', {}).get('year_pillar'):
                QMessageBox.warning(self, '提示', '请先进行排盘，再使用文化研究算法分析功能')
                return

            self.bazi_result.show_ai_loading('文化研究算法正在深入分析八字命理…')
            self.statusBar().showMessage('文化研究算法分析进行中，请稍候…')
            self._begin_ai_busy('bazi')

            task_id = str(uuid.uuid4())

            self._bazi_ai_worker = AiAnalysisWorker('bazi', input_data, chart_data, task_id)
            # 保持 4 位置参数构造契约（测试替身可能不接受额外关键字），
            # 与 AiAnalysisManager.start_analysis 的既有做法一致
            if force_refresh:
                self._bazi_ai_worker.force_refresh = True
            self._bazi_ai_worker.progress_updated.connect(self._on_bazi_ai_progress)
            self._bazi_ai_worker.analysis_finished.connect(self._on_bazi_ai_finished)
            self._bazi_ai_worker.analysis_failed.connect(self._on_bazi_ai_failed)
            self._register_worker(self._bazi_ai_worker)
            self._bazi_ai_worker.start()

        except Exception as e:
            self.statusBar().showMessage(f'文化研究算法分析启动失败: {e}')
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'文化研究算法分析启动失败: {e}')

    def _on_bazi_ai_progress(self, stage: str, message: str):
        """八字AI分析进度更新"""
        status_messages = {
            'validating': '正在验证输入数据…',
            'initializing': '正在初始化文化研究算法分析引擎…',
            'analyzing': '文化研究算法正在深度分析八字命理…',
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
            self._end_ai_busy('bazi')
            self.bazi_result.display_ai_result(ai_analysis)

            token_usage = result.get('token_usage', 0)
            report_id = result.get('report_id', 0)
            elapsed = result.get('elapsed_seconds', 0)

            # 更新数据库：按落库时记录的表写回 AI 解读（失败会状态栏提示）
            self._persist_ai_analysis('bazi', ai_analysis)

            self.statusBar().showMessage(
                f'文化研究算法分析完成 · 报告ID: {report_id} · '
                f'消耗Token: {token_usage} · 耗时: {elapsed:.1f}秒'
            )
        except Exception as e:
            self.statusBar().showMessage(f'显示文化研究算法分析结果失败: {e}')
            traceback.print_exc()

    def _on_bazi_ai_failed(self, error_type: str, error_message: str):
        """八字AI分析失败"""
        self._end_ai_busy('bazi')
        self.bazi_result.display_result(getattr(self.bazi_result, '_current_result', {}))
        self.bazi_result.smart_analyze_btn.setVisible(True)
        self.bazi_result.smart_analyze_btn.setEnabled(True)
        self.statusBar().showMessage(f'文化研究算法分析失败: {error_type}')

        error_titles = {
            'validation_error': '数据验证失败',
            'ai_timeout': '文化研究算法请求超时',
            'ai_request_error': '文化研究算法请求失败',
            'ai_response_error': '文化研究算法响应解析失败',
            'db_connection_error': '数据库连接异常',
            'db_query_error': '数据库操作异常',
        }
        title = error_titles.get(error_type, '分析失败')

        msg_lines = error_message.split('\n')
        short_msg = msg_lines[0] if msg_lines else error_message

        QMessageBox.warning(self, title, short_msg)

    def _on_meihua_ai_analyze(self, force_refresh: bool = False):
        """梅花易数AI分析按钮点击处理。

        Args:
            force_refresh: True 时跳过 AI 结果缓存强制重新解读（「重新分析」入口使用）
        """
        try:
            input_data = self.meihua_input.get_data()
            hexagram_data = self.meihua_result.get_hexagram_data_for_ai()

            if not hexagram_data or not hexagram_data.get('base', {}).get('name'):
                QMessageBox.warning(self, '提示', '请先起卦，再使用文化研究算法解读功能')
                return

            self.meihua_result.show_ai_loading('文化研究算法正在解读卦象玄机…')
            self.statusBar().showMessage('文化研究算法解读进行中，请稍候…')
            self._begin_ai_busy('meihua')

            task_id = str(uuid.uuid4())

            self._meihua_ai_worker = AiAnalysisWorker('meihua', input_data, hexagram_data, task_id)
            if force_refresh:
                self._meihua_ai_worker.force_refresh = True
            self._meihua_ai_worker.progress_updated.connect(self._on_meihua_ai_progress)
            self._meihua_ai_worker.analysis_finished.connect(self._on_meihua_ai_finished)
            self._meihua_ai_worker.analysis_failed.connect(self._on_meihua_ai_failed)
            self._register_worker(self._meihua_ai_worker)
            self._meihua_ai_worker.start()

        except Exception as e:
            self.statusBar().showMessage(f'文化研究算法解读启动失败: {e}')
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'文化研究算法解读启动失败: {e}')

    def _on_meihua_ai_progress(self, stage: str, message: str):
        """梅花易数AI分析进度更新"""
        status_messages = {
            'validating': '正在验证输入数据…',
            'initializing': '正在初始化文化研究算法分析引擎…',
            'analyzing': '文化研究算法正在解读卦象玄机…',
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
            self._end_ai_busy('meihua')
            self.meihua_result.display_ai_analysis_result(ai_analysis)

            token_usage = result.get('token_usage', 0)
            report_id = result.get('report_id', 0)
            elapsed = result.get('elapsed_seconds', 0)

            # 更新数据库：按落库时记录的表写回 AI 解读（失败会状态栏提示）
            self._persist_ai_analysis('meihua', ai_analysis)

            self.statusBar().showMessage(
                f'文化研究算法解读完成 · 报告ID: {report_id} · '
                f'消耗Token: {token_usage} · 耗时: {elapsed:.1f}秒'
            )
        except Exception as e:
            self.statusBar().showMessage(f'显示文化研究算法解读结果失败: {e}')
            traceback.print_exc()

    def _on_meihua_ai_failed(self, error_type: str, error_message: str):
        """梅花易数AI分析失败"""
        self._end_ai_busy('meihua')
        self.meihua_result.display_result(getattr(self.meihua_result, '_current_result', {}))
        self.meihua_result.smart_analyze_btn.setVisible(True)
        self.meihua_result.smart_analyze_btn.setEnabled(True)
        self.statusBar().showMessage(f'文化研究算法解读失败: {error_type}')

        error_titles = {
            'validation_error': '数据验证失败',
            'ai_timeout': '文化研究算法请求超时',
            'ai_request_error': '文化研究算法请求失败',
            'ai_response_error': '文化研究算法响应解析失败',
            'db_connection_error': '数据库连接异常',
            'db_query_error': '数据库操作异常',
        }
        title = error_titles.get(error_type, '解读失败')

        msg_lines = error_message.split('\n')
        short_msg = msg_lines[0] if msg_lines else error_message

        QMessageBox.warning(self, title, short_msg)

