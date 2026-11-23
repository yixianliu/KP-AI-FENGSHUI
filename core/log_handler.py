"""
统一日志 Handler
================
把「系统日志」接入本地 SQLite 数据库的 system_logs 表。所有模块的
logger.info/warning/error 在写本地文件的同时，也会结构化写入 system_logs。

落库为**异步批量**：调用线程只做「取字段 + 入队」（微秒级），由独立后台线程
按批攒够 ``batch_size`` 条或超过 ``flush_interval`` 秒（先到先写）一次性提交，
避免 GUI / worker 线程被 SQLite 写入拖慢，也减少并发写导致的 database is locked。

用法（在 main_window / 各业务模块启动处）：
    from core.log_handler import setup_app_logging
    setup_app_logging()   # 接入 DatabaseManager 本地库单例

之后任意模块：
    import logging
    logger = logging.getLogger(__name__)
    logger.info("xxx")   # 自动落文件 + 队列 → system_logs
"""
import atexit
import logging
import logging.handlers
import queue
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

from core.path_utils import get_logs_dir

# NOTE: sys.path 统一在 main.py 入口处注入，此处不再重复 inject

# 顶层模块 logger：兼容历史代码 `from core.log_handler import logger`
# （UI 子模块早期曾这样写，迁移后保留符号避免外部 import 失败）
logger = logging.getLogger(__name__)

# 默认攒批参数：100 条 / 1 秒，二者先到先写
DEFAULT_BATCH_SIZE = 100
DEFAULT_FLUSH_INTERVAL = 1.0
# DB 未就绪期间的内存缓冲上限（超出部分降级写文件，避免无限占用内存）
DEFAULT_MAX_BACKLOG = 2000
# 落库队列上限（写库线程被锁拖住时，队列不得无限增长；满则丢最旧并计数告警）
DEFAULT_MAX_QUEUE_SIZE = 5000
# close() 等待消费线程收尾的默认时限（超时后强制把剩余队列降级写文件）
DEFAULT_CLOSE_TIMEOUT = 5.0


class _BackendNotReady(Exception):
    """存储后端尚未完成初始化（不是写入失败，日志暂存内存等待重试）。"""


class _FlushRequest:
    """flush 同步标记：消费线程处理到该标记时把未满批次立即落库并唤醒等待方。"""

    __slots__ = ('event',)

    def __init__(self, event: threading.Event):
        self.event = event


class AsyncStorageLogHandler(logging.handlers.QueueHandler):
    """异步批量落库 Handler：``emit`` 只入队，后台线程攒批写 ``system_logs``。

    设计要点：
    - 调用线程（GUI / worker）绝不触碰 SQLite，``emit`` 仅做字段提取 + ``put_nowait``。
    - 后台消费线程按「批大小 / 刷新间隔」先到先写，单连接 executemany 单次提交。
    - 递归保护：消费线程自身写库期间产生的日志直接丢弃，不会再次入队形成自激。
    - 不丢日志：DB 未就绪时暂存内存（超上限降级写文件）；写库失败整批降级写
      独立文件并输出 stderr 痕迹；``flush()`` / ``close()`` 会排空队列。
    """

    _STOP = object()

    def __init__(self, level=logging.WARNING,
                 batch_size: int = DEFAULT_BATCH_SIZE,
                 flush_interval: float = DEFAULT_FLUSH_INTERVAL,
                 max_backlog: int = DEFAULT_MAX_BACKLOG,
                 max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE,
                 fallback_file: str | Path | None = None):
        """构造异步 Handler。

        Args:
            level: 入队门槛，低于该级别的日志不入队（控制写入量）。
            batch_size: 单批最多条数，达到即写。
            flush_interval: 单批最长等待秒数，超时即写。
            max_backlog: DB 未就绪时的内存暂存上限，超出部分降级写文件。
            max_queue_size: 落库队列上限；消费线程被拖住时满则丢弃最旧记录
                （丢弃条数见 ``dropped_count``），避免内存无界增长。
            fallback_file: 降级文件路径，默认 logs/system_logs_fallback_<日期>.log。
        """
        self._records: "queue.Queue" = queue.Queue(
            maxsize=max(1, int(max_queue_size)))
        super().__init__(self._records)
        self.setLevel(level)
        self.batch_size = max(1, int(batch_size))
        self.flush_interval = max(0.01, float(flush_interval))
        self.max_backlog = max(1, int(max_backlog))
        self._local = threading.local()  # 递归 guard：标记「当前线程正在写库」
        self._backlog: list = []  # DB 未就绪期间的暂存
        self._fallback_lock = threading.Lock()
        self._stopped = False
        self._failed_batches = 0
        self._last_error = None
        self._written = 0
        # 队列溢出计数（丢最旧），供指标/告警读取
        self._dropped = 0
        self._drop_lock = threading.Lock()
        # close() 等待消费线程的时限；超时后把剩余队列降级写文件（测试可调小）
        self.close_timeout = DEFAULT_CLOSE_TIMEOUT
        if fallback_file is None:
            fallback_file = get_logs_dir() / (
                f'system_logs_fallback_{datetime.now().strftime("%Y%m%d")}.log')
        self.fallback_file = Path(fallback_file)
        self._worker = threading.Thread(
            target=self._run, name='kp-system-log-writer', daemon=True)
        self._worker.start()

    # ------------------------------------------------------------------ 入队侧
    def emit(self, record: logging.LogRecord):
        """仅做字段提取并入队，保持调用线程零 DB 开销。

        递归保护：消费线程写库时若产生日志，直接跳过；本模块自身日志也跳过。
        字段提取阶段不修改原 record（文件 / 控制台 Handler 仍可正常格式化）。
        """
        if getattr(self._local, 'writing', False):
            return
        if record.name == __name__:
            return
        try:
            payload = self.prepare(record)
            self.enqueue(payload)
        except Exception:
            # 入队失败不应影响业务线程
            self.handleError(record)

    @property
    def dropped_count(self) -> int:
        """队列溢出时被丢弃的最旧日志条数（供指标 / 告警读取）。"""
        return self._dropped

    def enqueue(self, record):
        """入队（队列满时丢弃最旧一条并计数，绝不阻塞调用线程）。

        覆盖 ``QueueHandler.enqueue``：无界队列在消费线程被
        ``database is locked`` 拖住时会无限增长，必须设上限并丢弃最旧记录。
        """
        try:
            self._records.put_nowait(record)
            return
        except queue.Full:
            pass
        # 满队列：丢弃最旧一条腾位，再放入当前记录
        try:
            self._records.get_nowait()
        except queue.Empty:
            pass
        with self._drop_lock:
            self._dropped += 1
            dropped = self._dropped
        try:
            self._records.put_nowait(record)
        except queue.Full:
            # 极端并发下腾位后又满：当前记录也只能丢弃（同样计数）
            with self._drop_lock:
                self._dropped += 1
                dropped = self._dropped
        if dropped == 1 or dropped % 100 == 0:
            # 控制日志频率：首次丢弃与每满 100 条提示一次。
            # 本模块 logger 的记录会被 emit 的递归 guard 跳过，不会再次入队。
            logger.warning('[日志] 落库队列已满，丢弃最旧日志（累计 %d 条）', dropped)

    def _enqueue_control(self, item) -> bool:
        """放入控制标记（_FlushRequest / _STOP）；队列满时丢弃最旧业务记录腾位。

        Returns:
            bool: True 表示已成功放入队列。
        """
        for _ in range(4):
            try:
                self._records.put_nowait(item)
                return True
            except queue.Full:
                try:
                    self._records.get_nowait()
                    with self._drop_lock:
                        self._dropped += 1
                except queue.Empty:
                    return False
        return False

    def prepare(self, record: logging.LogRecord) -> dict:
        """把 LogRecord 提炼为落库所需的最小字典（不修改原 record）。"""
        data = {
            'pathname': record.pathname,
            'lineno': record.lineno,
            'funcName': record.funcName,
        }
        if record.exc_info:
            data['exc_text'] = ''.join(traceback.format_exception(*record.exc_info))
        return {
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.name,
            'data': data,
        }

    # ------------------------------------------------------------------ 消费侧
    def _run(self):
        """后台消费循环：攒批写入，sentinel 退出前排空。"""
        batch: list = []
        deadline = time.monotonic() + self.flush_interval
        try:
            while True:
                timeout = max(0.0, deadline - time.monotonic())
                try:
                    item = self._records.get(timeout=timeout)
                except queue.Empty:
                    if batch:
                        self._flush(batch)
                        batch = []
                    deadline = time.monotonic() + self.flush_interval
                    continue
                if item is self._STOP:
                    break
                if isinstance(item, _FlushRequest):
                    if batch:
                        self._flush(batch)
                        batch = []
                    item.event.set()
                    deadline = time.monotonic() + self.flush_interval
                    continue
                batch.append(item)
                if len(batch) >= self.batch_size:
                    self._flush(batch)
                    batch = []
                    deadline = time.monotonic() + self.flush_interval
        finally:
            if batch:
                self._flush(batch)
            self._drain_after_stop()

    def _drain_after_stop(self):
        """退出前兜底：把 sentinel 之后可能残留的条目也写掉，并唤醒等待中的 flush。"""
        leftovers: list = []
        while True:
            try:
                item = self._records.get_nowait()
            except queue.Empty:
                break
            if item is self._STOP:
                continue
            if isinstance(item, _FlushRequest):
                item.event.set()
                continue
            leftovers.append(item)
        if leftovers:
            self._flush(leftovers)

    def _write_batch(self, rows: list) -> bool:
        """把一批日志交给 DatabaseManager 批量写入（单连接 + 单次提交）。

        Raises:
            _BackendNotReady: DB 管理器尚未完成初始化，调用方转入内存暂存。
        """
        from core.database_manager import peek_db_manager
        mgr = peek_db_manager()
        if mgr is None:
            raise _BackendNotReady()
        return bool(mgr.save_system_logs_batch(rows))

    def _flush(self, batch: list):
        """落库一批日志；后端未就绪暂存内存，失败则整批降级写文件。"""
        if not batch:
            return
        self._local.writing = True  # 递归 guard：写库期间的日志不再入队
        try:
            pending = self._backlog + batch if self._backlog else batch
            self._backlog = []
            try:
                ok = self._write_batch(pending)
            except _BackendNotReady:
                if len(pending) > self.max_backlog:
                    overflow = pending[:-self.max_backlog]
                    pending = pending[-self.max_backlog:]
                    self._degrade_to_file(overflow, '后端未就绪且内存缓冲已满')
                self._backlog = pending
                return
            except Exception as e:
                self._degrade_to_file(pending, e)
                return
            if not ok:
                self._degrade_to_file(pending, 'save_system_logs_batch 返回 False')
            else:
                self._written += len(pending)
        finally:
            self._local.writing = False

    def _degrade_to_file(self, rows: list, reason):
        """写库失败的降级路径：整批追加到独立文件，并在 stderr 留痕，不静默丢弃。"""
        self._failed_batches += 1
        self._last_error = str(reason)
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.fallback_file.parent.mkdir(parents=True, exist_ok=True)
            with self._fallback_lock:
                with open(self.fallback_file, 'a', encoding='utf-8') as f:
                    for r in rows:
                        f.write(f"{ts} [{r.get('level')}] {r.get('module')} - "
                                f"{r.get('message')}\n")
                    f.write(f"# 批量落库失败（{len(rows)} 条）：{reason}\n")
        except Exception:
            pass
        try:
            sys.stderr.write(
                f"[system_logs] 批量落库失败（{len(rows)} 条）：{reason}；"
                f"已降级写入 {self.fallback_file}\n")
        except Exception:
            pass

    # ------------------------------------------------------------------ 生命周期
    def flush(self):
        """阻塞等待队列中已有日志全部落库（仅在进程退出 / 关闭窗口时调用）。"""
        if getattr(self, '_stopped', False) or not self._worker.is_alive():
            return
        if threading.current_thread() is self._worker:
            return
        event = threading.Event()
        if not self._enqueue_control(_FlushRequest(event)):
            return
        event.wait(timeout=max(5.0, self.flush_interval * 3))

    def _degrade_remaining_queue(self):
        """close 超时兜底：把队列中剩余记录整批降级写文件，避免静默丢失。"""
        leftovers: list = []
        stop_seen = False
        while True:
            try:
                item = self._records.get_nowait()
            except queue.Empty:
                break
            if item is self._STOP:
                stop_seen = True
                continue
            if isinstance(item, _FlushRequest):
                item.event.set()
                continue
            leftovers.append(item)
        if stop_seen:
            # 保留停止标记：消费线程解除阻塞后仍需靠它退出，否则会空转
            try:
                self._records.put_nowait(self._STOP)
            except queue.Full:
                pass
        if leftovers:
            self._degrade_to_file(leftovers, '关闭超时，消费线程未在时限内排空队列')

    def close(self):
        """停止消费线程并排空剩余队列（logging.shutdown / atexit 自动调用）。

        消费线程若因 ``database is locked`` 等长时间阻塞，join 超时后把队列中
        剩余记录强制降级写文件，绝不放任其静默丢失。
        """
        if not getattr(self, '_stopped', False):
            self._stopped = True
            self._enqueue_control(self._STOP)
            is_self = threading.current_thread() is self._worker
            if not is_self and self._worker.is_alive():
                self._worker.join(timeout=self.close_timeout)
                if self._worker.is_alive():
                    self._degrade_remaining_queue()
        super().close()


def _resolve_default_log_dir() -> Path:
    """解析默认日志目录（统一使用 path_utils 工具）。"""
    return get_logs_dir()


def setup_app_logging(log_dir=None, console_level=logging.WARNING,
                     storage_level=logging.WARNING,
                     file_level=logging.INFO,
                     max_bytes=5 * 1024 * 1024,
                     backup_count=5,
                     storage_batch_size=DEFAULT_BATCH_SIZE,
                     storage_flush_interval=DEFAULT_FLUSH_INTERVAL):
    """配置全局日志：本地文件 + 控制台 + 异步批量存储后端（system_logs）。

    使用 RotatingFileHandler 实现日志切割，避免单文件无限增长淹没磁盘。
    屏显（控制台 / 文件）与落库走不同 Handler：前者同步直写，后者入队由后台线程
    攒批写 SQLite，因此落库慢或锁冲突不会阻塞调用线程，也不会影响屏显时效。

    Args:
        log_dir: 本地日志目录（忽略，统一使用 path_utils.get_logs_dir()）
        console_level: 控制台输出级别
        storage_level: 写入存储后端的级别
        file_level: 本地文件级别
        max_bytes: 单个日志文件最大字节数，默认 5MB
        backup_count: 保留的历史文件数量，默认 5
        storage_batch_size: 落库单批条数，默认 100
        storage_flush_interval: 落库单批最长等待秒数，默认 1.0
    """
    log_dir = get_logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    # 避免重复添加 handler（多次调用 setup 时）
    if getattr(root, '_kp_logging_inited', False):
        return root
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1) 本地文件：使用 RotatingFileHandler 实现切割
    from logging.handlers import RotatingFileHandler
    global_file = log_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = RotatingFileHandler(
        str(global_file), encoding='utf-8',
        maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # 2) 控制台
    console = logging.StreamHandler()
    console.setLevel(console_level)
    console.setFormatter(fmt)
    root.addHandler(console)

    # 3) 存储后端（system_logs）：入队 + 后台批量写库
    storage_handler = AsyncStorageLogHandler(
        level=storage_level,
        batch_size=storage_batch_size,
        flush_interval=storage_flush_interval,
    )
    storage_handler.setFormatter(fmt)
    root.addHandler(storage_handler)
    # 进程退出兜底：先排空队列再让 logging.shutdown 收尾（atexit 为后进先出）
    atexit.register(storage_handler.close)

    root._kp_logging_inited = True
    logging.getLogger(__name__).info("[日志] 全局日志已接入：本地文件 + 控制台 + 异步批量存储后端(system_logs)")
    return root
