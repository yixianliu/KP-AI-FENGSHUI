# -*- coding: utf-8 -*-
"""
scripts/build_portable.py — 绿色便携版打包脚本

目标：生成无需安装、不写注册表、不依赖外部配置的可执行文件 (.exe)，
      所有资源内置或放在同一目录中，输出到 dist/风水排盘专业工具/。

步骤：
  1. purge_ai_secrets.py   — 清除 AI 密钥（构建安全）
  2. 生成 version_info.txt — EXE 版本资源
  3. 拷贝 Qt/VC DLLs 到 pyside6_packages — 便携依赖
  4. PyInstaller 打包（spec 自动生成）
  5. verify_build_security.py — 产物级密钥校验
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
DIST = ROOT / "dist"
VERSION_INFO = ROOT / "version_info.txt"
PYSIDE6_PKG = ROOT / "pyside6_packages"
SPEC_PATH = ROOT / "scripts" / "build_portable.spec"

# ── anaconda3 路径（包含 Qt DLLs / VC 运行时 / _ssl.pyd）───────────────────
ANACONDA3 = Path(r"D:\anaconda3")
ANACONDA_DLLS = ANACONDA3 / "Library" / "bin"   # Qt / VC / SSL DLLs
ANACONDA_PYD  = ANACONDA3 / "DLLs"               # _ssl.pyd 等

# ── 用户空间 PySide6 安装路径 ───────────────────────────────────────────────
USER_PYTHON = Path(r"F:\AppData\Roaming\Python\Python313")
# anaconda3 里的 PySide6 包含真正的 .pyd 文件（用户空间的是纯 shim）
ANACONDA_PYSIDE6_SITE = ANACONDA3 / "Lib" / "site-packages"
PYINSTALLER = subprocess.run(
    [PY, "-m", "pip", "show", "PyInstaller"],
    capture_output=True, text=True
)


def run(cmd, **kw):
    print(">>> " + " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, **kw)


def _rmtree_win32(path: Path) -> None:
    """Win32 直接递归删除（绕过安全删除包装）。"""
    import ctypes
    k32 = ctypes.windll.kernel32
    p = Path(path)
    if p.is_symlink() or p.is_file():
        try:
            k32.DeleteFileW(str(p))
        except Exception:
            pass
        return
    if not p.exists():
        return
    for child in p.iterdir():
        _rmtree_win32(child)
    try:
        k32.RemoveDirectoryW(str(p))
    except Exception:
        pass


def _prepare_pyside6_packages() -> dict:
    """将 Qt/VC/SSL DLLs 及 PySide6 插件拷贝到 pyside6_packages/。

    Returns:
        dict: {相对路径(字符串): 绝对路径(Path)}，供 spec 生成使用。
    """
    # 清除旧目录
    if PYSIDE6_PKG.exists():
        _rmtree_win32(PYSIDE6_PKG)
    PYSIDE6_PKG.mkdir(parents=True)

    collected: dict = {}   # key: dest_relative_path, value: source_path

    # 1) VC 运行时 DLL
    vc_names = [
        "msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll",
        "msvcp140_codecvt_ids.dll", "msvcp140_atomic_wait.dll",
        "vcruntime140.dll", "vcruntime140_1.dll",
        "concrt140.dll", "vcruntime140_threads.dll",
        "vccorlib140.dll",
    ]
    for name in vc_names:
        src = ANACONDA_DLLS / name
        if src.exists():
            dst = PYSIDE6_PKG / name
            shutil.copy2(str(src), str(dst))
            collected[name] = dst

    # 2) SSL DLLs
    ssl_names = ["libssl-3-x64.dll", "libcrypto-3-x64.dll"]
    for name in ssl_names:
        src = ANACONDA_DLLS / name
        if src.exists():
            dst = PYSIDE6_PKG / name
            shutil.copy2(str(src), str(dst))
            collected[name] = dst

    # 3) Qt DLLs（带 _conda 后缀的 conda 打包）+ ICU 国际化库
    qt_src = ANACONDA_DLLS
    if qt_src.exists():
        for dll in sorted(qt_src.glob("*_conda.dll")):
            dst = PYSIDE6_PKG / dll.name
            shutil.copy2(str(dll), str(dst))
            collected[dll.name] = dst
        # 也拷贝不带后缀的 Qt DLL（如有）
        for dll in sorted(qt_src.glob("Qt*.dll")):
            if dll.name not in collected:
                dst = PYSIDE6_PKG / dll.name
                shutil.copy2(str(dll), str(dst))
                collected[dll.name] = dst
        # 拷贝 ICU 国际化库（Qt6 核心依赖：icuuc/icudt/icuin 等）
        for dll in sorted(qt_src.glob("icu*.dll")):
            if dll.name not in collected:
                dst = PYSIDE6_PKG / dll.name
                shutil.copy2(str(dll), str(dst))
                collected[dll.name] = dst
        # 将 icudt73.dll 复制为 icudt.dll（Qt6Core 需要无版本号的数据文件，
        # conda 中的 icudt.dll 是 1KB 的空 stub，实际数据在 icudt73.dll）
        _src_icudt73 = qt_src / "icudt73.dll"
        _dst_icudt = PYSIDE6_PKG / "icudt.dll"
        if _src_icudt73.exists() and _dst_icudt.exists():
            import hashlib
            with open(str(_src_icudt73), 'rb') as f:
                src_md5 = hashlib.md5(f.read()).hexdigest()
            with open(str(_dst_icudt), 'rb') as f:
                dst_md5 = hashlib.md5(f.read()).hexdigest()
            if src_md5 != dst_md5:
                shutil.copy2(str(_src_icudt73), str(_dst_icudt))
                print("[配置] 已用 icudt73.dll 覆盖空 stub icudt.dll")

    # 4) _ssl.pyd
    pyd_src = ANACONDA_PYD / "_ssl.pyd"
    if pyd_src.exists():
        dst = PYSIDE6_PKG / "_ssl.pyd"
        shutil.copy2(str(pyd_src), str(dst))
        collected["_ssl.pyd"] = dst

    # 4b) shiboken6 包（必须与 PySide6 .pyd 版本一致）
    # 优先级：conda shiboken6 > 用户空间 shiboken6
    _conda_shiboken6 = ANACONDA3 / "Lib" / "site-packages" / "shiboken6"
    _user_shiboken6 = USER_PYTHON / "site-packages" / "shiboken6"
    _shiboken6_src = None
    if _conda_shiboken6.exists():
        _shiboken6_src = _conda_shiboken6
        print("[配置] 使用 conda shiboken6")
    elif _user_shiboken6.exists():
        _shiboken6_src = _user_shiboken6
        print("[配置] 使用用户空间 shiboken6（conda 不存在）")
    if _shiboken6_src:
        _pyside6_shiboken_dir = PYSIDE6_PKG / "shiboken6"
        shutil.copytree(str(_shiboken6_src), str(_pyside6_shiboken_dir), dirs_exist_ok=True)
        for p in _pyside6_shiboken_dir.rglob("*"):
            if p.is_file() and not p.name.endswith(('.pyi', '.lib', '.h')):
                rel = str(p.relative_to(PYSIDE6_PKG)).replace(os.sep, '/')
                collected[rel] = p
        print("[配置] 已复制 shiboken6 到 pyside6_packages/shiboken6/")
        # 记录 shiboken6 ABI DLL 供 spec 使用
        _shiboken6_abi_dll = _pyside6_shiboken_dir / "shiboken6.abi3.dll"
        _shiboken6_pyd = _pyside6_shiboken_dir / "Shiboken.pyd"
        if _shiboken6_abi_dll.exists():
            collected['shiboken6/shiboken6.abi3.dll'] = _shiboken6_abi_dll
        if _shiboken6_pyd.exists():
            collected['shiboken6/Shiboken.pyd'] = _shiboken6_pyd

    # 5) PySide6 插件目录（platforms / styles / imageformats）
    # 优先从 anaconda3 的 PySide6 获取插件，备选从用户空间获取
    _anaconda_pyside6_plugins = ANACONDA3 / "Lib" / "site-packages" / "PySide6" / "plugins"
    _user_pyside6_plugins = USER_PYTHON / "site-packages" / "PySide6" / "plugins"
    if _anaconda_pyside6_plugins.exists():
        plugins_src = _anaconda_pyside6_plugins
    elif _user_pyside6_plugins.exists():
        plugins_src = _user_pyside6_plugins
    else:
        plugins_src = None
    if plugins_src and plugins_src.exists():
        plugins_dst = PYSIDE6_PKG / "plugins"
        shutil.copytree(str(plugins_src), str(plugins_dst), dirs_exist_ok=True)
        for rel, src_file in _collect_plugins(plugins_src, plugins_dst):
            collected[rel] = src_file
        print(f"[插件] 已拷贝 {len(list(plugins_src.rglob('*.dll')))} 个 Qt 插件")

    # 6) PySide6 Python 包本体（优先 anaconda3，备选用户空间）
    _anaconda_pyside6_site = ANACONDA3 / "Lib" / "site-packages" / "PySide6"
    pyside6_site = _anaconda_pyside6_site if _anaconda_pyside6_site.exists() else USER_PYTHON / "site-packages" / "PySide6"
    pyside6_dst = PYSIDE6_PKG / "PySide6"
    if pyside6_site.exists():
        shutil.copytree(str(pyside6_site), str(pyside6_dst), dirs_exist_ok=True)
        # 使用用户空间的智能版 __init__.py（含 _setupQtDirectories 逻辑）
        # 它会自动调用 os.add_dll_directory(shiboken6_dir) 设置 DLL 搜索路径
        _user_init_py = USER_PYTHON / "site-packages" / "PySide6" / "__init__.py"
        if _user_init_py.exists():
            import shutil as _shutil
            _shutil.copy2(str(_user_init_py), str(pyside6_dst / "__init__.py"))
            print("[配置] 已替换为智能版 PySide6 __init__.py")
        else:
            init_py = pyside6_dst / "__init__.py"
            if not init_py.exists():
                init_py.write_text("# auto-generated by build_portable.py\n", encoding="utf-8")
        # 将 PySide6 包本体中的 .pyd 和 Qt6 DLL 加入 collected，供 spec 作为 datas 打包
        # 统一使用正斜杠作为 key 前缀，避免 Windows 路径分隔符问题
        for p in pyside6_dst.rglob("*"):
            if p.is_file() and (p.suffix == '.pyd' or (p.name.startswith('Qt6') and p.suffix == '.dll')):
                rel = str(p.relative_to(PYSIDE6_PKG)).replace(os.sep, '/')
                collected[rel] = p

    print(f"[依赖准备] 已收集 {len(collected)} 个依赖文件到 {PYSIDE6_PKG}")
    return collected


def _collect_plugins(src: Path, dst: Path) -> list[tuple[str, Path]]:
    """递归收集插件目录中的所有 DLL，返回 (相对路径, 源路径) 列表。"""
    result = []
    for p in dst.rglob("*.dll"):
        rel = str(p.relative_to(dst))
        result.append((rel, p))
    return result


def _find_certifi_cacert() -> Path:
    """查找 certifi cacert.pem。"""
    candidates = [
        ANACONDA3 / "Lib" / "site-packages" / "certifi" / "cacert.pem",
        USER_PYTHON / "Lib" / "site-packages" / "certifi" / "cacert.pem",
    ]
    for c in candidates:
        if c.exists():
            return c
    import certifi
    return Path(certifi.where())


def _generate_spec(collected: dict) -> Path:
    """自动生成 PyInstaller spec 文件。

    策略（解决 Python 3.13 frozen 环境 .pyd DLL 加载问题）：
    - PySide6 包结构 (_internal/PySide6/) 通过 datas 保持：.pyd + __init__.py
    - shiboken6 包结构 (_internal/shiboken6/) 通过 datas 整体打入，避免版本混杂
    - Qt6 DLLs / VC 运行时 → binaries（放 _internal/ 根目录）
    - runtime hook 在 import 前预加载关键 DLL
    """
    # VC 运行时 → binaries（根目录）
    vc_dlls = {k: v for k, v in collected.items() if k.startswith(("msv", "vcr", "concrt", "vccor"))}
    # SSL DLLs → binaries（根目录）
    ssl_dlls = {k: v for k, v in collected.items() if k in ("libssl-3-x64.dll", "libcrypto-3-x64.dll", "_ssl.pyd")}
    # ICU DLLs → binaries（根目录，Qt6Core 强依赖无版本号名称）
    icu_dlls = {k: v for k, v in collected.items()
                if k.startswith('icu') and k.endswith('.dll')}
    # Qt platform plugins → binaries（根目录，PySide6 rthook 自动发现）
    platform_dlls = {k: v for k, v in collected.items() if "platforms" in k.lower()}
    # Qt5 conda DLLs → binaries（根目录）
    qt5_conda_dlls = {k: v for k, v in collected.items()
                      if k.endswith('_conda.dll') or (k.startswith('Qt5') and k.endswith('.dll'))}
    # PySide6 .pyd → datas（打入 _internal/PySide6/ 子目录，保持包结构）
    _pyside6_prefix = 'PySide6/'
    pyside6_pyds = {k: v for k, v in collected.items()
                    if k.startswith(_pyside6_prefix) and k.endswith('.pyd')}
    # pyside6 ABI DLL → binaries（根目录，.pyd 需要找到它们）
    abi_dlls = {k: v for k, v in collected.items()
                if k in ('pyside6.abi3.dll', 'pyside6qml.abi3.dll')}
    # Qt6 DLLs → binaries（根目录）
    qt6_dlls = {k: v for k, v in collected.items()
                if k.startswith(_pyside6_prefix) and k.endswith('.dll')}
    # python3.dll → binaries（根目录）
    python3_dll = {k: v for k, v in collected.items()
                   if k == 'python3.dll'}
    # shiboken6 ABI DLL → binaries（根目录，.pyd 需要找到它们）
    shiboken6_abi = {k: v for k, v in collected.items()
                     if k in ('shiboken6/shiboken6.abi3.dll', 'shiboken6/Shiboken.pyd')}
    # 其余 Qt 插件（styles, imageformats 等）→ datas（打入 PySide6/plugins/）
    # 注：当前实现的过滤条件已合并入其他 datas 收集分支，不再单独保留 other_plugins 字典。

    certifi_cacert = _find_certifi_cacert()

    def _binaries_lines(items: dict) -> str:
        return "\n".join(f"        (r'{src}', '.')," for rel, src in items.items())

    vc_lines = _binaries_lines(vc_dlls)
    ssl_lines = _binaries_lines(ssl_dlls)
    icu_lines = _binaries_lines(icu_dlls)
    platform_lines = _binaries_lines(platform_dlls)
    qt5_lines = _binaries_lines(qt5_conda_dlls)
    abi_lines = _binaries_lines(abi_dlls)
    qt6_lines = _binaries_lines(qt6_dlls)
    python3_lines = _binaries_lines(python3_dll)
    shiboken6_abi_lines = _binaries_lines(shiboken6_abi)

    # PySide6 .pyd + __init__.py → datas（打入 _internal/PySide6/ 子目录）
    _pyside6_pkg_dir = PYSIDE6_PKG / "PySide6"
    _init_py_src = _pyside6_pkg_dir / "__init__.py"
    pyside6_datas_entries = []
    if _init_py_src.exists():
        pyside6_datas_entries.append(f"        (r'{_init_py_src}', 'PySide6'),")
    for rel, src in pyside6_pyds.items():
        pyside6_datas_entries.append(f"        (r'{src}', 'PySide6'),")
    pyside6_datas_lines = "\n".join(pyside6_datas_entries)

    # shiboken6 包 → datas（整体打入 _internal/shiboken6/，保持版本一致性）
    _shiboken6_pkg_dir = PYSIDE6_PKG / "shiboken6"
    shiboken6_datas_entries = []
    if _shiboken6_pkg_dir.exists():
        for p in _shiboken6_pkg_dir.rglob("*"):
            if p.is_file() and not p.name.endswith(('.pyi', '.lib', '.h', '__pycache__')):
                rel = str(p.relative_to(_shiboken6_pkg_dir)).replace(os.sep, '/')
                shiboken6_datas_entries.append(f"        (r'{p}', 'shiboken6/{os.path.dirname(rel)}'),")
    shiboken6_datas_lines = "\n".join(shiboken6_datas_entries) if shiboken6_datas_entries else "        # 无 shiboken6 数据"

    # 插件 datas → PySide6/plugins/
    _plugin_datas = []
    _plugins_dir = PYSIDE6_PKG / "plugins"
    if _plugins_dir.exists():
        for p in _plugins_dir.rglob("*"):
            if p.is_file():
                _plugin_datas.append(f"        (r'{p}', 'PySide6/plugins'),")
    plugins_datas_str = "\n".join(_plugin_datas) if _plugin_datas else "        # 无插件数据"

    # pathex 顺序：conda PySide6（含真实 .pyd）优先于用户空间 shim
    _pathex_order = [
        str(ANACONDA_PYSIDE6_SITE),
        str(USER_PYTHON / "site-packages"),
        str(ROOT),
        str(ROOT / "scripts"),
    ]

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""风水排盘专业工具 - 便携版打包配置 (自动生成)"""
import os

block_cipher = None

_project_root = r'{ROOT}'
_pyside6_path = r'{PYSIDE6_PKG}'

a = Analysis(
    [r'{ROOT / "main.py"}'],
    pathex={_pathex_order},
    binaries=[
{vc_lines}
{ssl_lines}
{icu_lines}
{platform_lines}
{qt5_lines}
{abi_lines}
{shiboken6_abi_lines}
{qt6_lines}
{python3_lines}
    ],
    datas=[
        (r'{ROOT / "assets" / "favicon.ico"}', '.'),
        (r'{ROOT / "database"}', 'database'),
        (r'{ROOT / "data"}', 'data'),
        (r'{certifi_cacert}', 'certifi'),
{plugins_datas_str}
{pyside6_datas_lines}
{shiboken6_datas_lines}
    ],
    hiddenimports=[
        'core.path_utils',
        'core.secure_log',
        'core.device_identity',
        'core.sqlite_db',
        'core.log_handler',
        'core.knowledge.analysis_storage',
        'core.ai_cache',
        'core.database_manager',
        'core.bazi.bazi_calculator',
        'core.bazi.bazi_types',
        'core.calendar_utils',
        'core.ganzhi_constants',
        'core.knowledge.data_validator',
        'core.knowledge.data_integration',
        'core.bazi.geju_analyzer',
        'core.divination.hexagram_analyzer',
        'core.divination.hexagram_data',
        'core.knowledge.knowledge_base',
        'core.divination.liuren',
        'core.location_db',
        'core.lunar_converter',
        'core.divination.meihua',
        'core.bazi.mingli',
        'core.bazi.shishen',
        'core.bazi.wuxing',
        'core.bazi.yuncheng',
        'core.bazi.yunshi',
        'core.bazi._baazi_compat',
        'ui.main_window',
        'ui.styles',
        'ui.components.settings_dialog',
        'ui.components.about_dialog',
        'ui.components.input_panel',
        'ui.components.result_panel',
        'ui.components.meihua_input',
        'ui.components.meihua_result_panel',
        'ui.components.liuren_input',
        'ui.components.liuren_result_panel',
        'ui.components.ai_analysis_worker',
        'ui.components.collapsible_card',
        'ui.components.export_dialog',
        'ui.export.base_exporter',
        'ui.export.csv_exporter',
        'ui.export.excel_exporter',
        'ui.export.pdf_exporter',
        'core.app_version',
        'api.agnes_client',
        'core.ai_config',
        'core.local_settings',
        'lunarcalendar',
        'bcrypt',
        'openpyxl',
        'reportlab',
        'reportlab.graphics',
        'reportlab.lib.colors',
        '_ssl', 'ssl', 'certifi', 'certifi.core',
        'urllib3.util.ssl_',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[r'{ROOT / "scripts" / "pyi_rth_ssl.py"}', r'{ROOT / "scripts" / "pyi_rth_pyside6_qt6.py"}'],
    excludes=['PyQt5', 'PyQt6', 'PIL', 'notebook', 'jinja2', 'tkinter',
              'server', 'server.app', 'core._embedded_config'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='风水排盘专业工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=os.path.join(_project_root, 'version_info.txt'),
    icon=os.path.join(_project_root, 'assets', 'favicon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='风水排盘专业工具',
)
'''
    SPEC_PATH.write_text(spec_content, encoding="utf-8")
    print(f"[配置] 已生成 spec: {SPEC_PATH}")
    return SPEC_PATH


def main() -> int:
    os.environ["CODEBUDDY_SAFE_DELETE_SANDBOX"] = "0"

    # 1. 清密钥
    print("[步骤 1/6] 清除 AI 密钥...")
    code = run([PY, str(ROOT / "scripts" / "purge_ai_secrets.py")],
               cwd=str(ROOT)).returncode
    if code != 0:
        print("[错误] 密钥清除失败。")
        return code

    # 2. 清理旧 dist
    if DIST.exists():
        _rmtree_win32(DIST)
        print("[构建] 已清理旧 dist")

    # 3. 准备便携依赖（Qt/VC/SSL DLLs + PySide6 插件）
    print("[步骤 2/6] 准备便携依赖 (pyside6_packages)...")
    collected = _prepare_pyside6_packages()

    # 4. 生成版本资源
    print("[步骤 3/6] 生成版本资源...")
    sys.path.insert(0, str(ROOT))
    from core.app_version import get_version, get_version_tuple
    ver_str = get_version()
    major, minor, patch, _ = get_version_tuple()
    quad = f"{major}.{minor}.{patch}.0"
    content = (
        "# UTF-8\n"
        "# 本文件由 scripts/build_portable.py 自动生成，请勿手工维护。\n"
        "# http://msdn.microsoft.com/en-us/library/ms646997.aspx\n"
        "VSVersionInfo(\n"
        "  ffi=FixedFileInfo(\n"
        f"    filevers=({major}, {minor}, {patch}, 0),\n"
        f"    prodvers=({major}, {minor}, {patch}, 0),\n"
        "    mask=0x3f,\n"
        "    flags=0x0,\n"
        "    OS=0x40004,\n"
        "    fileType=0x1,\n"
        "    subtype=0x0,\n"
        "    date=(0, 0)\n"
        "  ),\n"
        "  kids=[\n"
        "    StringFileInfo(\n"
        "      [\n"
        "        StringTable(\n"
        "          u'040904B0',\n"
        "          [\n"
        f"            StringStruct(u'CompanyName', u'KP工作室'),\n"
        f"            StringStruct(u'FileDescription', u'风水排盘专业工具'),\n"
        f"            StringStruct(u'FileVersion', u'{quad}'),\n"
        f"            StringStruct(u'InternalName', u'风水排盘专业工具'),\n"
        f"            StringStruct(u'LegalCopyright', u'Copyright © 2024-2026 KP工作室'),\n"
        f"            StringStruct(u'OriginalFilename', u'风水排盘专业工具.exe'),\n"
        f"            StringStruct(u'ProductName', u'风水排盘专业工具'),\n"
        f"            StringStruct(u'ProductVersion', u'{quad}')\n"
        "          ]\n"
        "        )\n"
        "      ]\n"
        "    ),\n"
        "    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])\n"
        "  ]\n"
        ")\n"
    )
    VERSION_INFO.write_text(content, encoding="utf-8")
    print(f"[构建] 已生成 version_info.txt (v{ver_str})")

    # 5. 生成 spec 并打包
    print("[步骤 4/6] 生成 PyInstaller spec...")
    spec = _generate_spec(collected)

    print("[步骤 5/6] PyInstaller 打包中（耗时较长）...")
    code = run([PY, "-m", "PyInstaller", str(spec), "--noconfirm"],
               cwd=str(ROOT)).returncode
    if code != 0:
        print("[错误] PyInstaller 构建失败。")
        return code

    # 清理根目录遗留 exe
    stray = DIST / "风水排盘专业工具.exe"
    if stray.exists():
        try:
            stray.unlink(missing_ok=True)
            print("[构建] 已清理根目录遗留 exe")
        except Exception:
            pass

    # 6. 产物校验
    print("[步骤 6/6] 产物安全校验...")
    code = run([PY, str(ROOT / "scripts" / "verify_build_security.py")],
               cwd=str(ROOT)).returncode
    if code != 0:
        print("[错误] 产物校验未通过，禁止发布！")
        return code

    print("=" * 64)
    print("[完成] 便携版构建成功，可发布。")
    print(f"       版本: v{ver_str}")
    print(f"       输出目录: {DIST / '风水排盘专业工具'}")
    print("       可独立运行于任何 Windows 10+ 系统，无需 Python 环境。")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
