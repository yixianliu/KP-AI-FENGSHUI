# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('D:\\anaconda3\\Lib\\site-packages\\shiboken6\\shiboken6.abi3.dll', 'PySide6')],
    datas=[('config.ini', '.'), ('config.ini.example', '.'), ('favicon.ico', '.'), ('database', 'base')],
    hiddenimports=['lunarcalendar', 'lunarcalendar.converter', 'pymysql', 'redis', 'bcrypt', 'openpyxl', 'reportlab', 'reportlab.graphics', 'reportlab.lib.colors'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PIL', 'notebook', 'jinja2'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='风水排盘专业工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='风水排盘专业工具',
)
