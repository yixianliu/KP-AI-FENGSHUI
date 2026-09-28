#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主程序入口 - KP-AI-FENGSHUI 风水排盘系统
"""

import os
import sys
import traceback
from pathlib import Path

_project_root = Path(__file__).resolve().parent
_project_str = str(_project_root)
if _project_str not in sys.path:
    sys.path.insert(0, _project_str)

# AI 依赖目录（langchain / chromadb / sentence-transformers 等）
# 这些包通过 pip --target 安装到 Lib/site-packages/ai_extra，
# 在此处加入 sys.path 以便程序运行时能找到。
_ai_extra_dir = _project_root / 'Lib' / 'site-packages' / 'ai_extra'
if _ai_extra_dir.is_dir():
    _ai_extra_str = str(_ai_extra_dir)
    if _ai_extra_str not in sys.path:
        sys.path.append(_ai_extra_str)

# UI 依赖目录（PySide6 / shiboken6 等）
# 用户全局 site-packages 中的 PySide6 可能只剩 .pyi 存根而缺失原生 .pyd，
# 因此把本项目自带的 ui_extra 插入到 sys.path 最前，优先命中完整版本。
_ui_extra_dir = _project_root / 'Lib' / 'site-packages' / 'ui_extra'
_ui_extra_str = str(_ui_extra_dir) if _ui_extra_dir.is_dir() else ''


def _fix_pyside6_resolution():
    """确保 PySide6.QtWidgets 可导入（不修改任何磁盘文件，仅调整本进程 sys.path）。

    背景：全局 site-packages 里的 PySide6 安装可能只剩 .pyi 存根，缺
    QtWidgets.pyd / Qt6Widgets.dll，导致 `from PySide6.QtWidgets import ...`
    报 ModuleNotFoundError。修复策略：把项目内置的 ui_extra 提到 sys.path
    最前，同时暂时屏蔽其它路径上残缺的 PySide6，再重新 import。
    """
    try:
        import PySide6.QtWidgets  # noqa: F401 快速探测，已可用则直接返回
        return True
    except ImportError:
        pass

    if not _ui_extra_str or not (_project_root / 'Lib' / 'site-packages' / 'ui_extra' / 'PySide6').is_dir():
        return False

    # 清理已加载的残缺模块，避免缓存污染
    for _name in list(sys.modules):
        if _name == 'PySide6' or _name.startswith('PySide6.') or _name == 'shiboken6' or _name.startswith('shiboken6.'):
            del sys.modules[_name]

    # 项目依赖置最前，其余路径中若已含残缺 PySide6 的目录则暂时移出
    if _ui_extra_str in sys.path:
        sys.path.remove(_ui_extra_str)
    sys.path.insert(0, _ui_extra_str)
    _shadowed = []
    for _p in list(sys.path):
        try:
            _pd = Path(_p) / 'PySide6'
            if _pd.is_dir() and str(_pd) != str((_project_root / 'Lib' / 'site-packages' / 'ui_extra' / 'PySide6')):
                sys.path.remove(_p)
                _shadowed.append(_p)
        except (TypeError, OSError):
            continue

    try:
        import PySide6.QtWidgets  # noqa: F401
        return True
    except ImportError:
        # 恢复原状，交由后续诊断处理
        for _p in _shadowed:
            sys.path.append(_p)
        return False


# frozen 环境处理
if getattr(sys, 'frozen', False):
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass and str(meipass) not in sys.path:
        sys.path.insert(0, str(meipass))

# 关键修复：在导入任何 Qt 模块之前，强制指定 Qt 平台插件目录
# 无论打包环境还是源码运行，都需要设置此环境变量，否则 Qt 无法创建窗口
def _set_qt_platform_plugin_path():
    """定位并设置 Qt 平台插件目录（qwindows.dll 所在目录）。

    搜索顺序：
    1. 打包环境：_MEIPASS/platforms/
    2. 项目内置 pyside6_packages/PySide6/plugins/platforms/
    3. 项目内置 Lib/site-packages/ui_extra/PySide6/plugins/platforms/
    4. PySide6 包目录下的 plugins/platforms/
    """
    candidates = []
    # 1. 打包环境
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            candidates.append(os.path.join(meipass, 'platforms'))
        candidates.append(os.path.join(os.path.dirname(sys.executable), 'platforms'))
    # 2. 项目内置 pyside6_packages
    builtin_plugins = _project_root / 'pyside6_packages' / 'PySide6' / 'plugins' / 'platforms'
    if builtin_plugins.is_dir():
        candidates.append(str(builtin_plugins))
    builtin_plugins2 = _project_root / 'pyside6_packages' / 'plugins' / 'platforms'
    if builtin_plugins2.is_dir():
        candidates.append(str(builtin_plugins2))
    # 3. ui_extra
    ui_extra_plugins = _project_root / 'Lib' / 'site-packages' / 'ui_extra' / 'PySide6' / 'plugins' / 'platforms'
    if ui_extra_plugins.is_dir():
        candidates.append(str(ui_extra_plugins))
    # 4. PySide6 包目录
    try:
        import PySide6
        pyside6_dir = os.path.dirname(PySide6.__file__)
        candidates.append(os.path.join(pyside6_dir, 'plugins', 'platforms'))
    except ImportError:
        pass

    for plugin_dir in candidates:
        if os.path.isdir(plugin_dir):
            qwindows = os.path.join(plugin_dir, 'qwindows.dll')
            if os.path.isfile(qwindows):
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_dir
                print(f"[DLL] Qt 平台插件已设置: {plugin_dir}", file=sys.stderr)
                return
    print("[DLL] 警告：未找到 Qt 平台插件（qwindows.dll）", file=sys.stderr)


_set_qt_platform_plugin_path()

from core.dll_diagnostic import fix_dll_loading_order
fix_dll_loading_order()

# 必须在 DLL 搜索路径注入之后执行：PySide6.QtWidgets 加载需要 ICU 等 Qt 依赖
_fix_pyside6_resolution()

from core.path_utils import get_resource_path, get_logs_dir
from core.secure_log import install_log_scrubber, scrub

install_log_scrubber()

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6 import QtCore

_log_dir = get_logs_dir()
_log_dir.mkdir(parents=True, exist_ok=True)
_log_path = _log_dir / 'runtime_error.log'


def excepthook(exc_type, exc_value, exc_tb):
    text = (
        f"Unhandled exception: {exc_type.__name__}\n"
        f"Message: {exc_value}\n"
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


def _early_diagnose(exc):
    try:
        text = (
            "[启动诊断] 应用启动失败（早期异常)\n"
            f"异常类型: {type(exc).__name__}\n"
            f"异常信息: {exc}\n"
            "Traceback:\n"
            + ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        )
        safe_text = scrub(text)
        with open(str(_log_path), 'w', encoding='utf-8') as f:
            f.write(safe_text)
        print(safe_text, file=sys.stderr)
    except OSError:
        pass


try:
    from ui.main_window import MainWindow
except Exception as e:
    _early_diagnose(e)
    print(f"Failed to import MainWindow: {scrub(str(e))}", file=sys.stderr)
    print(f"See {_log_path} for details", file=sys.stderr)
    sys.exit(1)


def _show_crash_dialog(exc):
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            '启动失败',
            f'应用启动时发生致命错误：\n\n{exc}\n\n详细堆栈已写入 logs/runtime_error.log'
        )
    except Exception:
        pass


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')

        try:
            icon_path = get_resource_path('favicon.ico')
            if icon_path.exists():
                app.setWindowIcon(QIcon(str(icon_path)))
        except Exception as icon_exc:
            pass

        try:
            window = MainWindow()
        except Exception as win_exc:
            _early_diagnose(win_exc)
            print(f"[启动] 主窗口创建失败：{scrub(str(win_exc))}", file=sys.stderr)
            _show_crash_dialog(win_exc)
            sys.exit(1)

        window.show()
        try:
            window.raise_()
            window.activateWindow()
        except Exception:
            pass
        sys.exit(app.exec())
    except Exception as e:
        excepthook(type(e), e, e.__traceback__)
        sys.exit(1)