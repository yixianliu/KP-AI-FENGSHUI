"""
统一日志 Handler
================
把「系统日志」接入本地 SQLite 数据库的 system_logs 表。所有模块的
logger.info/warning/error 在写本地文件的同时，也会结构化写入 system_logs。

用法（在 main_window / 各业务模块启动处）：
    from core.log_handler import setup_app_logging
    setup_app_logging()   # 接入 DatabaseManager 本地库单例

之后任意模块：
    import logging
    logger = logging.getLogger(__name__)
    logger.info("xxx")   # 自动落文件 + system_logs
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

# NOTE: sys.path 统一在 main.py 入口处注入，此处不再重复 inject


class StorageLogHandler(logging.Handler):
    """将日志记录写入本地 SQLite 数据库的 system_logs 表。"""

    def __init__(self, level=logging.WARNING):
        super().__init__(level)
        self._failed = False

    def emit(self, record: logging.LogRecord):
        if self._failed:
            return
        try:
            from core.database_manager import get_db_manager
            mgr = get_db_manager()
            if mgr is None:
                return
            # 避免把本 handler 自己的错误再写回后端造成递归
            if record.name == __name__:
                return
            data = {
                'pathname': record.pathname,
                'lineno': record.lineno,
                'funcName': record.funcName,
            }
            if record.exc_info:
                import traceback
                data['exc_text'] = ''.join(traceback.format_exception(*record.exc_info))
            mgr.save_system_log(
                level=record.levelname,
                message=record.getMessage(),
                module=record.name,
                data=data,
            )
        except Exception:
            # 后端不可用时静默降级，不阻断业务日志
            self._failed = True


def _resolve_default_log_dir() -> Path:
    """解析默认日志目录。

    - 打包环境（PyInstaller）：写到 exe 同级 logs/，用户易找到
    - 开发环境：写到项目根 logs/（core/ 的上一级）
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys.executable).resolve().parent / 'logs'
    return Path(__file__).resolve().parent.parent / 'logs'


def setup_app_logging(log_dir=None, console_level=logging.WARNING,
                     storage_level=logging.WARNING,
                     file_level=logging.INFO):
    """配置全局日志：本地文件 + 存储后端（system_logs）。

    Args:
        log_dir: 本地日志目录，默认 logs/
        console_level: 控制台输出级别
        storage_level: 写入存储后端的级别
        file_level: 本地文件级别
    """
    if log_dir is None:
        log_dir = _resolve_default_log_dir()
    log_dir = Path(log_dir)
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

    # 1) 本地文件（按模块/日期分文件在各自模块 setup_logger 中处理；
    #    此处统一给一个全局文件兜底，避免无 handler 时丢失
    global_file = log_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.FileHandler(global_file, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # 2) 控制台
    console = logging.StreamHandler()
    console.setLevel(console_level)
    console.setFormatter(fmt)
    root.addHandler(console)

    # 3) 存储后端（system_logs）
    storage_handler = StorageLogHandler(level=storage_level)
    storage_handler.setFormatter(fmt)
    root.addHandler(storage_handler)

    root._kp_logging_inited = True
    logging.getLogger(__name__).info("[日志] 全局日志已接入：本地文件 + 存储后端(system_logs)")
    return root
