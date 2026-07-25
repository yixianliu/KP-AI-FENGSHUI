import sys
import os
import traceback
from pathlib import Path

# ================================================================
# 统一 sys.path：只在打包前或启动时注入一次
# ================================================================
_project_root = Path(__file__).resolve().parent
_project_str = str(_project_root)
if _project_str not in sys.path:
    sys.path.insert(0, _project_str)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

# ================================================================
# 全局异常钩子：把未处理的崩溃写入 runtime_error.log
# ================================================================
# 打包环境（PyInstaller）下写入 exe 同级目录，方便用户排查；
# 开发环境下写入源码目录。
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    _app_base = os.path.dirname(sys.executable)
else:
    _app_base = os.path.dirname(os.path.abspath(__file__))
_log_path = os.path.join(_app_base, 'runtime_error.log')


def excepthook(exc_type, exc_value, exc_tb):
    with open(_log_path, 'w', encoding='utf-8') as f:
        f.write(f"Unhandled exception: {exc_type.__name__}\n")
        f.write(f"Message: {exc_value}\n")
        f.write("Traceback:\n")
        f.write(''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))
    print(f"FATAL ERROR - see {_log_path}", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_tb)


sys.excepthook = excepthook

try:
    from ui.main_window import MainWindow
except Exception as e:
    with open(_log_path, 'w', encoding='utf-8') as f:
        f.write(f"Import FAILED: {e}\n")
        f.write("Traceback:\n")
        f.write(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
    print(f"Failed to import MainWindow: {e}", file=sys.stderr)
    print(f"See {_log_path} for details", file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # 设置应用程序图标（统一使用项目根目录下的 favicon.ico）
        icon_path = _project_root / 'favicon.ico'
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        excepthook(type(e), e, e.__traceback__)
        sys.exit(1)
