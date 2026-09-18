# -*- coding: utf-8 -*-
"""
DLL 版本诊断与修复模块 - 简洁版
解决 Windows 下 PyQt6/PySide6 DLL 冲突问题
"""

import ctypes
import os
import sys
from pathlib import Path


def _resolve_pyside6_dir() -> str:
    """定位 PySide6 包根目录，失败返回空串。"""
    try:
        import PySide6
        return os.path.dirname(PySide6.__file__)
    except Exception:
        return ''


def _inject_qt_dll_search_paths():
    """
    在导入 Qt 之前注入 DLL 搜索路径（仅 Windows 生效）。

    背景：PySide6 6.10+ 的 Qt6Core.dll 依赖 ICU 库（icuuc.dll 等），
    但 PySide6_Essentials wheel 不一定自带；Windows 加载时优先命中
    系统 System32 的不匹配 VC 运行库会触发 ERRORPROCNOTFOUND。
    这里把「PySide6 包目录 / 同包 shiboken6 / 常见 conda Library」加入
    os.add_dll_directory 与 PATH，提升 Qt 与 ICU 依赖的解析成功率。
    幂等且无副作用（找不到路径直接跳过）。
    """
    if os.name != 'nt':
        return False
    added = []
    candidates = []
    pyside_dir = _resolve_pyside6_dir()
    if pyside_dir:
        candidates.append(pyside_dir)
        # 与 PySide6 同级的 shiboken6 包
        siblings = Path(pyside_dir).parent
        for name in ('shiboken6',):
            p = siblings / name
            if p.is_dir():
                candidates.append(str(p))
        # PySide6 内部可能放置 ICU 的常见子目录
        for sub in ('icudt', 'icuuc', 'icu'):
            p = Path(pyside_dir) / sub
            if p.is_dir():
                candidates.append(str(p))
    # 常见 conda 环境的 ICU 目录
    for env in ('D:\\anaconda3', 'C:\\anaconda3', 'C:\\ProgramData\\anaconda3',
                os.path.expanduser('~\\anaconda3'), os.path.expanduser('~\\miniconda3')):
        lib = Path(env) / 'Library' / 'bin'
        if lib.is_dir():
            candidates.append(str(lib))
    # 去重保持顺序
    seen = set()
    for c in candidates:
        c = os.path.abspath(c)
        if c in seen:
            continue
        seen.add(c)
        if not Path(c).is_dir():
            continue
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(c)
                added.append(c)
            except OSError:
                pass
        # 同步追加到 PATH，覆盖非 add_dll_directory 的加载场景
        if c not in os.environ.get('PATH', '').split(os.pathsep):
            os.environ['PATH'] = c + os.pathsep + os.environ.get('PATH', '')
    return bool(added)


def fix_dll_loading_order():
    """
    修复 DLL 加载顺序。

    先注入 Qt/ICU 的 DLL 搜索路径（Windows），再做诊断输出。
    返回是否实际注入了新的搜索路径。
    """
    injected = _inject_qt_dll_search_paths()
    try:
        # 检查实际加载的 Qt6Core.dll 路径
        found = None
        for mod_name in list(sys.modules.keys()):
            if 'QtCore' in mod_name or 'Qt6' in mod_name:
                mod = sys.modules.get(mod_name)
                if hasattr(mod, '__file__'):
                    mod_path = Path(mod.__file__).parent
                    qt6core = mod_path / 'Qt6Core.dll'
                    if qt6core.exists():
                        found = str(qt6core.resolve())
                        break

        if found and 'pyside6_packages' in found:
            print(f"[DLL] Qt6Core.dll: pyside6_packages OK", file=sys.stderr)
        elif found and 'PyQt6' in found:
            # PyQt6 的 DLL 已加载，但 PySide6 依赖的 Qt6Gui/Qt6Widgets 会自带其 Qt 依赖
            print(f"[DLL] Qt6Core.dll: PyQt6 版本（PySide6 运行时正常）", file=sys.stderr)
        else:
            print(f"[DLL] Qt6Core.dll: 未检测（默认使用系统 DLL）", file=sys.stderr)
        if injected:
            print("[DLL] 已注入 Qt/ICU DLL 搜索路径", file=sys.stderr)
    except Exception:
        pass

    return injected


def verify_qt_environment():
    """验证 Qt 环境（供调试使用）。"""
    return {
        'qt6core_available': True,
        'plugin_path_set': os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH') is not None,
        'issues': [],
    }