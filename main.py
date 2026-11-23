#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主程序入口 - KP-AI-FENGSHUI 风水排盘系统
"""

import os
import sys
import subprocess
import traceback
from datetime import datetime
from pathlib import Path

_project_root = Path(__file__).resolve().parent
_project_str = str(_project_root)
if _project_str not in sys.path:
    sys.path.insert(0, _project_str)


def _ensure_venv_interpreter():
    """在导入任何 Qt 之前，确保程序运行在项目自带 venv 的 Python 解释器上。

    背景：项目 venv 锁定了完整可用的 PySide6 6.9.2（含全部原生依赖），
    但用户常用全局 Anaconda 环境（如 PythonWeb313）启动。该环境的 PySide6
    是 6.10+ 残缺版，且即便把 venv 的 Qt 库指给 Anaconda 解释器，其进程在
    加载 qwindows.dll 平台插件时也会 fail-fast 崩溃（0xC0000409 / -1073740791，
    已通过多次隔离实验证实，与 dll_diagnostic 的注入无关）。

    因此：当前解释器不是 venv 且 venv 存在时，用 venv 的 python.exe 重新
    启动本脚本（子进程 exec），保证 Qt 始终运行在能正常加载它的进程里。
    若 venv 不可用或已处于 venv 内，则继续当前流程。
    """
    try:
        venv_py = _project_root / 'venv' / 'Scripts' / 'python.exe'
        if not venv_py.is_file():
            return  # 无 venv，交由后续 PySide6 候选探测兜底
        cur = Path(sys.executable).resolve()
        venv_exe = venv_py.resolve()
        if cur == venv_exe:
            return  # 已在 venv 内，无需重启
        # 仅当 venv 内确实装了我们锁定的 PySide6 时才自举，避免空 venv 死循环
        venv_site = _project_root / 'venv' / 'Lib' / 'site-packages'
        if not (venv_site / 'PySide6' / 'QtCore.pyd').is_file():
            return
        if getattr(sys, 'frozen', False):
            return  # 打包环境不执行自举
        env = dict(os.environ)
        env['PYTHONPATH'] = ''
        # 用 venv 解释器重新执行本脚本，子进程替换当前进程，Qt 在干净进程加载
        cmd = [str(venv_exe), str(_project_root / 'main.py')] + sys.argv[1:]
        print(f"[venv] 切换到项目虚拟环境重启: {venv_exe}", file=sys.stderr)
        code = subprocess.call(cmd, env=env)
        sys.exit(code)
    except Exception as _exc:  # 自举失败不阻塞主流程
        print(f"[venv] 自动切换失败，继续当前流程: {_exc}", file=sys.stderr)


_ensure_venv_interpreter()


# AI 依赖目录（langchain / chromadb / sentence-transformers 等）
# 这些包通过 pip --target 安装到 Lib/site-packages/ai_extra，
# 在此处加入 sys.path 以便程序运行时能找到。
_ai_extra_dir = _project_root / 'Lib' / 'site-packages' / 'ai_extra'
if _ai_extra_dir.is_dir():
    _ai_extra_str = str(_ai_extra_dir)
    if _ai_extra_str not in sys.path:
        sys.path.append(_ai_extra_str)

# UI 依赖目录（PySide6 / shiboken6 等）
# 全局 site-packages 中的 PySide6 可能只剩 .pyi 存根（缺原生 .pyd），也可能是 6.10+
# 版本（其 Qt6Core.dll 硬依赖 icuuc.dll 而 wheel 不自带，必然加载失败）。
# 因此这里不盲信任何单一目录，改为逐个候选做「真实导入」探测，选第一个能用的安装。
_ui_extra_dir = _project_root / 'Lib' / 'site-packages' / 'ui_extra'
_ui_extra_str = str(_ui_extra_dir) if _ui_extra_dir.is_dir() else ''

# 已选定的 site-packages 根目录（内部同时含 PySide6 与同版本 shiboken6），空串表示未选定
_pyside6_root = ''
# 探测失败的候选（残缺或缺依赖），启动失败时用于给出可读的中文指引
_pyside6_rejected = []


def _purge_pyside_modules():
    """清理已加载的 PySide6 / shiboken6 模块，避免上一个残缺安装的缓存污染后续探测。"""
    for _name in list(sys.modules):
        if (_name == 'PySide6' or _name.startswith('PySide6.')
                or _name == 'shiboken6' or _name.startswith('shiboken6.')):
            del sys.modules[_name]


def _pyside6_candidates():
    """收集所有可能可用的 PySide6 安装根目录（越前越优先）。

    判定标准：<root>/PySide6 内必须存在原生 QtCore.pyd；
    只有 .pyi 存根的目录属于半装/损坏的安装，直接排除，不参与探测。
    项目自带 venv（锁定 PySide6 6.9.2，完整验证可用）拥有最高优先级，
    避免被全局环境里 6.10+ 的残缺安装（Qt6Core.dll 硬依赖 icuuc.dll 而
    wheel 不自带）遮蔽；venv 一旦损坏会自然回退到后续候选。
    """
    candidates = []
    seen = set()

    def _add(p):
        if not p:
            return
        try:
            _pkg = Path(p) / 'PySide6'
        except (TypeError, OSError):
            return
        if not (_pkg / 'QtCore.pyd').is_file():
            return
        _key = os.path.abspath(p)
        if _key in seen:
            return
        seen.add(_key)
        candidates.append(p)

    # 0. 项目自带 venv（最高优先级：锁定且完整，优先于任何全局安装）
    _venv_site = _project_root / 'venv' / 'Lib' / 'site-packages'
    _add(str(_venv_site))
    # 1. sys.path 中所有含完整 PySide6 的目录（按顺序，越前越优先）
    for _p in list(sys.path):
        if not _p:
            continue
        _add(_p)
    # 2. 项目内置 ui_extra / pyside6_packages 兜底
    for _p in (_ui_extra_str, str(_project_root / 'pyside6_packages')):
        _add(_p)
    return candidates


def _try_pyside6_root(root):
    """把 root 置到 sys.path 首位、屏蔽其它含 PySide6 的路径，再做一次真实导入验证。

    真实导入会真正加载 QtCore.pyd / Qt6Core.dll / shiboken6.abi3.dll，
    因此能同时发现「只有存根文件」与「PySide6 与 shiboken6 版本错配」两类问题。
    失败时完整回滚 sys.path，不影响后续候选探测。
    """
    original = list(sys.path)
    _purge_pyside_modules()
    sys.path.insert(0, root)
    for _p in list(sys.path):
        if _p == root or not _p:
            continue
        try:
            if (Path(_p) / 'PySide6').is_dir():
                sys.path.remove(_p)
        except (TypeError, OSError):
            continue
    try:
        import PySide6.QtWidgets  # noqa: F401 真实加载原生 DLL
        from PySide6 import QtCore  # noqa: F401
        return True
    except (ImportError, OSError) as _exc:
        _pyside6_rejected.append((root, str(_exc)))
        _purge_pyside_modules()
        sys.path[:] = original
        return False


def _fix_pyside6_resolution():
    """选定一个真正可用的 PySide6 安装（不修改任何磁盘文件，仅调整本进程 sys.path）。

    返回是否成功；成功时同时记录选中目录到 _pyside6_root，供 Qt 平台插件定位使用。
    """
    global _pyside6_root
    for _root in _pyside6_candidates():
        if _try_pyside6_root(_root):
            _pyside6_root = _root
            return True
    # 所有候选都失败：尽力探测一次当前解释器原始状态，便于指引里说明真实原因
    try:
        import PySide6.QtWidgets  # noqa: F401
        _pyside6_root = str(Path(sys.modules['PySide6'].__file__).resolve().parent.parent)
        return True
    except (ImportError, OSError) as _exc:
        _pyside6_rejected.append((sys.executable, str(_exc)))
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
    0. 已选定 PySide6 安装自带的 plugins/platforms/（必须最先，插件版本须与运行时一致）
    1. 打包环境：_MEIPASS/platforms/
    2. 项目内置 pyside6_packages/PySide6/plugins/platforms/
    3. 项目内置 Lib/site-packages/ui_extra/PySide6/plugins/platforms/
    4. PySide6 包目录下的 plugins/platforms/
    """
    candidates = []
    # 0. 优先使用与运行时同版本的插件（跨版本插件会被 Qt 判定为不兼容而拒绝加载）
    if _pyside6_root:
        matched_plugins = os.path.join(_pyside6_root, 'PySide6', 'plugins', 'platforms')
        if os.path.isfile(os.path.join(matched_plugins, 'qwindows.dll')):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = matched_plugins
            print(f"[DLL] Qt 平台插件已设置: {matched_plugins}", file=sys.stderr)
            return
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


# 先选定可真正加载的 PySide6 安装（排除只有存根的残缺安装与版本错配），
# 再做 DLL 搜索路径注入与平台插件定位，保证三者都指向同一份可用运行时。
_fix_pyside6_resolution()

from core.dll_diagnostic import fix_dll_loading_order
fix_dll_loading_order()

_set_qt_platform_plugin_path()

from core.path_utils import get_resource_path, get_logs_dir
from core.secure_log import install_log_scrubber, scrub

install_log_scrubber()

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
    # 【P2-08】追加写：早退诊断不得覆盖上一次的崩溃现场，用时间戳分隔多次崩溃
    try:
        with open(str(_log_path), 'a', encoding='utf-8') as f:
            f.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} =====\n")
            f.write(safe_text)
            f.write('\n')
    except OSError:
        pass
    # windowed 打包下 sys.stderr 可能为 None，显式判空避免 hook 内再抛异常
    if sys.stderr is not None:
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
        # 同上：追加写 + 时间戳分隔，保留历史崩溃现场
        with open(str(_log_path), 'a', encoding='utf-8') as f:
            f.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} =====\n")
            f.write(safe_text)
            f.write('\n')
        if sys.stderr is not None:
            print(safe_text, file=sys.stderr)
    except OSError:
        pass


def _print_pyside6_guidance(err):
    """PySide6 原生库加载失败时，输出可读的中文指引（而不是甩一屏 traceback）。

    典型触发场景：用错了解释器（例如全局 Anaconda 环境里装的是 6.10+ 残缺/跨版本
    PySide6），此时项目内置依赖也不可用，需要明确告知用户应该怎样启动。
    """
    lines = [
        '=' * 72,
        '[启动失败] PySide6（Qt 界面组件）无法加载，界面无法创建。',
        f'当前解释器：{sys.executable}',
        f'Python 版本：{sys.version.split()[0]}',
        f'导入错误：{err}',
        '',
        '本项目要求 PySide6==6.9.2：6.10 及以上版本的 Qt6Core.dll 硬依赖 icuuc.dll，',
        '官方 wheel 不自带该库，在干净环境中必然报 “DLL load failed”。',
    ]
    if _pyside6_root:
        lines.append(f'已选用的 PySide6 安装：{_pyside6_root}')
    for _root, _reason in _pyside6_rejected:
        lines.append(f'已排除的安装：{_root}（{_reason}）')
    lines += [
        '',
        '推荐启动方式（项目自带环境，已锁定 PySide6 6.9.2）：',
        f'  "{_project_root / "venv" / "Scripts" / "python.exe"}" main.py',
        '  或直接双击项目根目录下的 start.bat',
        '',
        '若必须使用当前解释器，请先安装锁定版本：',
        f'  "{sys.executable}" -m pip install "PySide6==6.9.2" "shiboken6==6.9.2"',
        '提示：若用户目录下残留只有 .pyi 没有 .pyd 的残缺 PySide6/shiboken6，',
        '      请先删除该目录再安装，否则会继续被残缺安装遮蔽。',
        '=' * 72,
    ]
    if sys.stderr is not None:
        print('\n'.join(lines), file=sys.stderr)


# Qt 原生库导入放在这里统一兜底：失败时仍写入 logs/runtime_error.log（追加 + 时间戳），
# 再给出中文指引，避免用户只看到一条无从下手的 DLL load failed。
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon
    from PySide6 import QtCore
except (ImportError, OSError) as _qt_import_err:
    _early_diagnose(_qt_import_err)
    _print_pyside6_guidance(_qt_import_err)
    sys.exit(2)


try:
    from ui.main_window import MainWindow
except Exception as e:
    _early_diagnose(e)
    if sys.stderr is not None:
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
            icon_path = get_resource_path('assets/favicon.ico')
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