# PyInstaller runtime hook to fix DLL search order
# 解决 UCNV_TO_U_CALLBACK_SUBSTITUTE 缺失问题
# 通过设置添加 DLL 目录到 Windows DLL 搜索链中

import os
import sys
from pathlib import Path

# 确保 pyside6_packages 中的 Qt6Core.dll 被优先加载
# 这可以防止系统/临时目录中的旧版 DLL 优先被加载

_project_root = Path(__file__).resolve().parent.parent
_packages_path = _project_root / 'pyside6_packages'

if str(_packages_path) not in sys.path:
    sys.path.insert(0, str(_packages_path))

# 添加 pyside6_packages 根目录（ICU DLL 所在）到 DLL 搜索路径
# Windows will search this directory before system32 etc.
_dll_search_path = _packages_path

if _dll_search_path.exists():
    # 使用 add_dll_directory (Python 3.8+ Windows)
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(str(_dll_search_path.resolve()))
            print(f"[DLL钩子] 已添加 DLL 搜索目录: {_dll_search_path}")
        except Exception:
            pass

    # 备选方案：设置环境变量
    env_path = os.environ.get('PATH', '')
    if str(_dll_search_path) not in env_path:
        os.environ['PATH'] = str(_dll_search_path) + os.pathsep + env_path
        print(f"[DLL钩子] 已预置 PATH: {_dll_search_path}")
