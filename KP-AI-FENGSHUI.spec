# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('database', 'database'), ('data', 'data'), ('D:\\PythonProject\\KP-AI-FENGSHUI/pyside6_packages/PySide6/plugins/platforms', 'platforms'), ('D:\\PythonProject\\KP-AI-FENGSHUI/pyside6_packages/PySide6/resources/icudtl.dat', '.'), ('assets', 'assets'), ('images', 'images')],  # M4-1.4：二维码资源目录进打包产物
    hiddenimports=['core.bazi.bazi_calculator', 'core.bazi.bazi_types', 'core.ganzhi_constants', 'core.ai_config', 'core.database_manager', 'core.ai_cache', 'core.ai_metrics', 'core.ai_throttle', 'core.path_utils', 'core.secure_log', 'core.bazi.shishen', 'core.bazi.wuxing', 'core.divination.liuren', 'core.bazi.mingli', 'core.divination.meihua', 'core.divination.hexagram_analyzer', 'core.bazi.geju_analyzer', 'core.calendar_utils', 'core.lunar_converter', 'core.local_settings', 'core.location_db', 'core.log_handler', 'core.knowledge.data_integration', 'core.knowledge.data_validator', 'core.knowledge.data_validator_v2', 'core.debug_keys', 'core.device_identity', 'core.dll_diagnostic', 'core.bazi._baazi_compat', 'core.divination.hexagram_data', 'core.bazi.yuncheng', 'core.bazi.yunshi', 'core.knowledge.analysis_fallback', 'core.knowledge.analysis_storage', 'core.app_version', 'core.knowledge.rag_knowledge', 'core.bazi.bazi_batch', 'core.fengshui', 'core.fengshui.xuan_kong', 'service', 'service.bazi_service', 'api.agnes_client', 'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'PySide6.QtQml', 'PySide6.QtQuick', 'lunarcalendar', 'requests', 'urllib3', 'certifi', 'openpyxl', 'reportlab'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    name='KP-AI-FENGSHUI',
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
    icon=['D:\\PythonProject\\KP-AI-FENGSHUI\\assets\\favicon.ico'],
)
