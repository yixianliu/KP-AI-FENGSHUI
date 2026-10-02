#!/usr/bin/env python
"""
KP-AI-FENGSHUI 单文件绿色便携版构建脚本
目标：生成单个 .exe 可执行文件，无需安装，输出至 dist/ 目录
兼容 Windows 7 / 10 / 11，绿色运行
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT       = Path(__file__).resolve().parent   # D:\PythonProject\KP-AI-FENGSHUI
PY         = sys.executable
DIST_DIR   = ROOT / "dist"
BUILD_DIR  = ROOT / "_build_single"
SPEC_FILE  = BUILD_DIR / "build.spec"

PYSIDE6_PKG = ROOT / "pyside6_packages"
ANACONDA3    = Path(r"D:\anaconda3")
USER_PYTHON  = Path(r"F:\AppData\Roaming\Python\Python313")


def run(cmd, **kw):
    print("[CMD] " + " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, **kw)


def ensure_dirs():
    if DIST_DIR.exists():
        shutil.rmtree(str(DIST_DIR))
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[目录] dist 已就绪: {DIST_DIR}")
    if BUILD_DIR.exists():
        shutil.rmtree(str(BUILD_DIR))
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


def collect_binaries() -> list:
    """收集二进制 DLL/pyd，返回 (src_path_str, dest_dir) 列表。"""
    binaries = []
    pkg = PYSIDE6_PKG

    def add(path: Path):
        if path.exists():
            binaries.append((str(path), "."))

    vc_ssl = [
        "msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll",
        "msvcp140_codecvt_ids.dll", "msvcp140_atomic_wait.dll",
        "vcruntime140.dll", "vcruntime140_1.dll",
        "vcruntime140_threads.dll", "vccorlib140.dll", "concrt140.dll",
        "libssl-3-x64.dll", "libcrypto-3-x64.dll", "_ssl.pyd",
        "python3.dll",
    ]
    for name in vc_ssl:
        add(pkg / name)

    for p in sorted(pkg.glob("icu*.dll")):
        add(p)
    for p in sorted(pkg.glob("*_conda.dll")):
        add(p)

    pyside6_pydir = pkg / "PySide6"
    if pyside6_pydir.exists():
        for p in sorted(pyside6_pydir.glob("Qt6*.dll")):
            add(p)
        for n in ["pyside6.abi3.dll", "pyside6qml.abi3.dll"]:
            add(pyside6_pydir / n)

    shiboken6_dir = pkg / "shiboken6"
    if shiboken6_dir.exists():
        for n in ["Shiboken.pyd", "shiboken6.abi3.dll"]:
            add(shiboken6_dir / n)

    platforms_dir = pkg / "plugins" / "platforms"
    if platforms_dir.exists():
        for p in sorted(platforms_dir.glob("*.dll")):
            add(p)

    return binaries


def collect_datas() -> list:
    """收集静态资源，返回 (src_path_str, dest_dir) 列表。"""
    datas = []

    def add(src: Path, dest: str):
        if src.exists():
            datas.append((str(src), dest))

    add(ROOT / "assets" / "favicon.ico", ".")
    add(ROOT / "database", "database")
    add(ROOT / "data", "data")

    # certifi cacert.pem
    certifi_path = None
    for cand in [
        ANACONDA3 / "Lib" / "site-packages" / "certifi" / "cacert.pem",
        USER_PYTHON / "Lib" / "site-packages" / "certifi" / "cacert.pem",
    ]:
        if cand.exists():
            certifi_path = str(cand)
            break
    if certifi_path:
        datas.append((certifi_path, "certifi"))

    # PySide6 插件（除 platforms 外）
    plugins_src = PYSIDE6_PKG / "plugins"
    if plugins_src.exists():
        for p in plugins_src.rglob("*"):
            if p.is_file() and "platforms" not in str(p).lower() and p.name not in {"qwindows.dll"}:
                rel = str(p.relative_to(plugins_src))
                datas.append((str(p), f"PySide6/plugins/{rel}"))

    # PySide6 Python 包本体 - 确保核心模块被包含
    pyside6_src = PYSIDE6_PKG / "PySide6"
    if pyside6_src.exists():
        init_py = pyside6_src / "__init__.py"
        if init_py.exists():
            datas.append((str(init_py), "PySide6"))
        for p in sorted(pyside6_src.rglob("*.pyd")):
            datas.append((str(p), "PySide6"))

    # shiboken6 包本体
    shiboken6_src = PYSIDE6_PKG / "shiboken6"
    if shiboken6_src.exists():
        for p in sorted(shiboken6_src.rglob("*")):
            if p.is_file() and not p.name.endswith(('.pyi', '.lib', '.h')) and '__pycache__' not in str(p):
                rel = str(p.relative_to(shiboken6_src)).replace(os.sep, '/')
                datas.append((str(p), f"shiboken6/{os.path.dirname(rel)}"))

    # **关键：明确收集 platforms 目录**
    platforms_src = PYSIDE6_PKG / "plugins" / "platforms"
    if platforms_src.exists():
        for p in platforms_src.rglob("*"):
            if p.is_file():
                rel = str(p.relative_to(platforms_src))
                datas.append((str(p), f"PySide6/plugins/platforms/{rel}"))

    return datas


def _escape_for_py(s: str) -> str:
    """将路径转义为 Python 字符串字面量（保留反斜杠，使用 r'' 形式）。"""
    s_escaped = s.replace('\\', '\\\\')
    if "'" in s_escaped and '"' not in s_escaped:
        return f'"{s_escaped}"'
    return f"r'{s_escaped}'"


def generate_spec(binaries: list, datas: list) -> Path:
    """生成 PyInstaller spec 文件（直接写入 Python 字面量，避免转义问题）。"""
    hidden = [
        'core.path_utils', 'core.secure_log', 'core.device_identity',
        'core.sqlite_db', 'core.log_handler', 'core.knowledge.analysis_storage',
        'core.ai_cache', 'core.database_manager', 'core.bazi.bazi_calculator',
        'core.bazi.bazi_types', 'core.calendar_utils', 'core.ganzhi_constants',
        'core.knowledge.data_validator', 'core.knowledge.data_integration', 'core.bazi.geju_analyzer',
        'core.divination.hexagram_analyzer', 'core.divination.hexagram_data', 'core.knowledge.knowledge_base',
        'core.divination.liuren', 'core.location_db', 'core.lunar_converter',
        'core.divination.meihua', 'core.bazi.mingli', 'core.bazi.shishen', 'core.bazi.wuxing',
        'core.bazi.yuncheng', 'core.bazi.yunshi', 'core.bazi._baazi_compat',
        'ui.main_window', 'ui.styles',
        'ui.components.settings_dialog', 'ui.components.about_dialog',
        'ui.components.input_panel', 'ui.components.result_panel',
        'ui.components.meihua_input', 'ui.components.meihua_result_panel',
        'ui.components.liuren_input', 'ui.components.liuren_result_panel',
        'ui.components.ai_analysis_worker', 'ui.components.collapsible_card',
        'ui.components.export_dialog',
        'ui.export.base_exporter', 'ui.export.csv_exporter',
        'ui.export.excel_exporter', 'ui.export.pdf_exporter',
        'core.app_version', 'api.agnes_client', 'core.ai_config',
        'core.local_settings', 'lunarcalendar', 'bcrypt',
        'openpyxl', 'reportlab', 'reportlab.graphics', 'reportlab.lib.colors',
        '_ssl', 'ssl', 'certifi', 'certifi.core', 'urllib3.util.ssl_',
    ]

    runtime_hooks = [
        str(ROOT / "scripts" / "pyi_rth_ssl.py"),
        str(ROOT / "scripts" / "pyi_rth_pyside6_qt6.py"),
        str(ROOT / "scripts" / "pyi_rth_dll_fix.py"),
    ]

    pathex = [
        str(ANACONDA3 / "Lib" / "site-packages"),
        str(USER_PYTHON / "site-packages"),
        str(ROOT),
        str(ROOT / "scripts"),
        str(PYSIDE6_PKG),
    ]

    # 构建 binaries 行
    bin_lines = []
    for bpath, bdest in binaries:
        bin_lines.append(f"        ({_escape_for_py(bpath)}, {_escape_for_py(bdest)}),")
    binaries_block = "\n".join(bin_lines)

    # 构建 datas 行
    datas_lines = []
    for dpath, ddest in datas:
        datas_lines.append(f"        ({_escape_for_py(dpath)}, {_escape_for_py(ddest)}),")
    datas_block = "\n".join(datas_lines)

    # hiddenimports
    hidden_lines = "\n".join(f"        '{h}'," for h in hidden)

    # runtime_hooks
    hooks_lines = "\n".join(f"        {_escape_for_py(h)},\n" for h in runtime_hooks)

    # pathex
    pathex_lines = "\n".join(f"        {_escape_for_py(p)},\n" for p in pathex)

    ver_file = ROOT / "version_info.txt"
    icon_path = str(ROOT / "assets" / "favicon.ico")
    ver_arg  = f"    version={_escape_for_py(str(ver_file))},\n    " if ver_file.exists() else ""

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""KP-AI-FENGSHUI 单文件绿色便携版 - 自动生成"""
import os

block_cipher = None
_project_root = r'{ROOT}'

a = Analysis(
    [{_escape_for_py(str(ROOT / "main.py"))}],
    pathex=[
{pathex_lines}    ],
    binaries=[
{binaries_block}    ],
    datas=[
{datas_block}    ],
    hiddenimports=[
{hidden_lines}    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[
{hooks_lines}    ],
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
    name='KP-AI-FENGSHUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    {ver_arg}icon={_escape_for_py(icon_path)}
)

# 单文件模式（--onefile），所有资源嵌入 exe，无额外文件夹
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='KP-AI-FENGSHUI',
    strip=False,
    upx=True,
    upx_exclude=[],
)
'''

    SPEC_FILE.write_text(spec_content, encoding="utf-8")
    print(f"[Spec] 已生成: {SPEC_FILE}")
    return SPEC_FILE


def main() -> int:
    print("=" * 64)
    print("KP-AI-FENGSHUI 单文件绿色便携版构建")
    print(f"  输出目录: {DIST_DIR}")
    print(f"  Python:   {PY}")
    print("=" * 64)

    print("\n[步骤 1/3] 准备目录...")
    ensure_dirs()

    print("\n[步骤 2/3] 生成 PyInstaller spec...")
    binaries = collect_binaries()
    datas    = collect_datas()
    print(f"  二进制文件: {len(binaries)} 个")
    print(f"  数据文件:   {len(datas)} 个")
    # generate_spec() 的副作用是写入 SPEC_FILE；返回值此处不需要。
    generate_spec(binaries, datas)

    print("\n[步骤 3/3] PyInstaller 打包中（耗时较长，请耐心等待）...")
    result = run(
        [PY, "-m", "PyInstaller", str(SPEC_FILE), "--noconfirm"],
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        print("[错误] PyInstaller 构建失败！")
        return result.returncode

    # 确认产物
    exe_dest = DIST_DIR / "KP-AI-FENGSHUI.exe"
    if not exe_dest.exists():
        for candidate in BUILD_DIR.rglob("*.exe"):
            if candidate.name == "KP-AI-FENGSHUI.exe":
                shutil.copy2(str(candidate), str(exe_dest))
                print(f"[完成] exe 已复制到: {exe_dest}")
                break
        else:
            print("[警告] 未找到生成的 exe，请检查构建日志")
            return 1

    print("\n" + "=" * 64)
    print("[成功] 单文件绿色便携版构建完成！")
    print(f"  文件: {exe_dest}")
    if exe_dest.exists():
        size_mb = exe_dest.stat().st_size / (1024 * 1024)
        print(f"  大小: {size_mb:.1f} MB")
    print("=" * 64)
    print("特性说明：")
    print("  - 单文件 exe，双击即可运行，无需安装 Python")
    print("  - 绿色便携，不写注册表，不留系统配置文件")
    print("  - 兼容 Windows 7 / 10 / 11")
    print("  - 所有依赖内置于 exe 中")
    print("  - 仅供文化研究参考，不构成决策依据")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())