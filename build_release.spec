# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python313.dll', '.'),
    ],
    datas=[
        ('config.ini', '.'),
        ('config.ini.example', '.'),
        ('favicon.ico', '.'),
        ('database', 'database'),
    ],
    hiddenimports=[
        'lunarcalendar',
        'pymysql',
        'redis',
        'bcrypt',
        'openpyxl',
        'reportlab',
        'reportlab.graphics',
        'reportlab.lib.colors',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PIL', 'notebook', 'jinja2'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
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
    icon='favicon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='风水排盘专业工具',
)
