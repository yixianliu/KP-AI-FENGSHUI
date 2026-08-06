import sys
import traceback
from pathlib import Path

# ================================================================
# 统一 sys.path：只在打包前或启动时注入一次
# ================================================================
_project_root = Path(__file__).resolve().parent
_project_str = str(_project_root)
if _project_str not in sys.path:
    sys.path.insert(0, _project_str)

# 统一路径工具（必须在 import core.* 之前注入 sys.path）
from core.path_utils import get_resource_path, get_logs_dir

# 日志脱敏：尽可能早地挂载，确保后续任何日志/崩溃信息都不会写出凭据
from core.secure_log import install_log_scrubber, scrub

install_log_scrubber()

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

# ================================================================
# 全局异常钩子：把未处理的崩溃写入 runtime_error.log
#
# 注意：崩溃堆栈是凭据泄露的高危出口（异常消息里可能带上请求头、令牌等），
#      因此写盘与打印前一律先经 scrub() 脱敏。
# ================================================================
_log_dir = get_logs_dir()
_log_dir.mkdir(parents=True, exist_ok=True)
_log_path = _log_dir / 'runtime_error.log'


def excepthook(exc_type, exc_value, exc_tb):
    text = (
        f"Unhandled exception: {exc_type.__name__}\n"
        f"Message: {exc_value}\n"
        "Traceback:\n"
        + ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    )
    safe_text = scrub(text)
    try:
        with open(str(_log_path), 'w', encoding='utf-8') as f:
            f.write(safe_text)
    except OSError:
        pass
    print(f"FATAL ERROR - see {_log_path}", file=sys.stderr)
    print(safe_text, file=sys.stderr)


sys.excepthook = excepthook

try:
    from ui.main_window import MainWindow
except Exception as e:
    _msg = scrub(
        f"Import FAILED: {e}\nTraceback:\n"
        + ''.join(traceback.format_exception(type(e), e, e.__traceback__))
    )
    try:
        with open(str(_log_path), 'w', encoding='utf-8') as f:
            f.write(_msg)
    except OSError:
        pass
    print(f"Failed to import MainWindow: {scrub(str(e))}", file=sys.stderr)
    print(f"See {_log_path} for details", file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')

        # 设置应用程序图标（统一使用资源目录下的 favicon.ico）
        icon_path = get_resource_path('favicon.ico')
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))

        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        excepthook(type(e), e, e.__traceback__)
        sys.exit(1)
