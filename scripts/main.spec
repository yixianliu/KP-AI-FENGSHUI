# -*- mode: python ; coding: utf-8 -*-

from importlib.util import find_spec
from pathlib import Path

# PySide6 platforms 插件按当前解释器动态定位（不写死盘符 / venv 路径）
_pyside6_platforms = str(Path(find_spec('PySide6').submodule_search_locations[0]) / 'plugins' / 'platforms')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/favicon.ico', '.'), ('database/schema_sqlite.sql', 'database'), (_pyside6_platforms, 'platforms')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
