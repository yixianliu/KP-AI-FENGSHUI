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

# frozen 环境处理
if getattr(sys, 'frozen', False):
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass and str(meipass) not in sys.path:
        sys.path.insert(0, str(meipass))

# 关键修复：在导入任何 Qt 模块之前，强制指定 Qt 平台插件目录
if getattr(sys, 'frozen', False):
    # 打包环境中，平台插件位于 _MEIPASS/platforms/
    plugin_dir = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)), 'platforms')
    if os.path.isdir(plugin_dir):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_dir

from core.dll_diagnostic import fix_dll_loading_order
fix_dll_loading_order()

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