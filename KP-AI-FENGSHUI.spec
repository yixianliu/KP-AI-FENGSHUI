# -*- mode: python ; coding: utf-8 -*-
"""Windows 绿色便携版 (onedir) — 以已验证基线增强。
产物: <ROOT>/dist/风水排盘专业工具/{风水排盘专业工具.exe, _internal/}
资源规则见 docs/packaging-plan.md §4。
"""
import os
from PyInstaller.utils.hooks import collect_data_files

ROOT = r'D:\PythonProject\KP-AI-FENGSHUI'
VPS  = r'D:\PythonProject\KP-AI-FENGSHUI\venv\Lib\site-packages\PySide6'
ANA  = r'D:\anaconda3'
VENV_CERTIFI = r'D:\PythonProject\KP-AI-FENGSHUI\venv\Lib\site-packages\certifi\cacert.pem'

# ---- VC 运行时（随包，免除目标机安装 VC Redist）----
_VC = ['msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll',
       'msvcp140_codecvt_ids.dll', 'vcruntime140.dll', 'vcruntime140_1.dll',
       'concrt140.dll', 'vccorlib140.dll']
vc_bins = [(os.path.join(VPS, n), '.') for n in _VC if os.path.isfile(os.path.join(VPS, n))]

# ---- SSL / OpenSSL（HTTPS 调 AI 必需；venv 不自带，取 anaconda）----
ssl_bins = [
    (os.path.join(ANA, 'DLLs', '_ssl.pyd'), '.'),
    (os.path.join(ANA, 'Library', 'bin', 'libssl-3-x64.dll'), '.'),
    (os.path.join(ANA, 'Library', 'bin', 'libcrypto-3-x64.dll'), '.'),
]
ssl_bins = [b for b in ssl_bins if os.path.isfile(b[0])]

# ---- PySide6 自带插件（platforms / imageformats / styles / tls / iconengines）----
_pyside6_plugins = collect_data_files('PySide6', subdir='plugins')

a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[
        os.path.join(ROOT, 'venv', 'Lib', 'site-packages'),
        ROOT,
        os.path.join(ROOT, 'scripts'),
    ],
    binaries=vc_bins + ssl_bins,
    datas=[
        # 程序图标：必须落在 _MEIPASS 根（main.py / main_window 用 get_resource_path('favicon.ico')）
        (os.path.join(ROOT, 'assets', 'favicon.ico'), '.'),
        # 运行时 SVG 图标集（icons.py 用 assets/icons/{name}.svg）
        (os.path.join(ROOT, 'assets'), 'assets'),
        # 关于页二维码 + 产品图（about_dialog 用 images/...）
        (os.path.join(ROOT, 'images'), 'images'),
        # 建库 schema（只读资源）
        (os.path.join(ROOT, 'database'), 'database'),
        # 可写种子数据（读种子→_MEIPASS/data；ST-08.5 另复制到 exe 同级）
        (os.path.join(ROOT, 'data'), 'data'),
        # CA 证书链
        (VENV_CERTIFI, 'certifi'),
        # Qt 国际化数据（Qt6Core 依赖）
        (os.path.join(VPS, 'resources', 'icudtl.dat'), '.'),
        # PySide6 插件集合
        *_pyside6_plugins,
    ],
    hiddenimports=[
        # 业务核心
        'core.path_utils', 'core.secure_log', 'core.device_identity',
        'core.sqlite_db', 'core.log_handler', 'core.database_manager',
        'core.ai_cache', 'core.app_version', 'core.ai_config', 'core.local_settings',
        'core.dll_diagnostic', 'core.bazi.bazi_calculator', 'core.bazi.bazi_types',
        'core.bazi._baazi_compat', 'core.bazi.geju_analyzer', 'core.bazi.mingli',
        'core.bazi.shishen', 'core.bazi.wuxing', 'core.bazi.yuncheng', 'core.bazi.yunshi',
        'core.calendar_utils', 'core.ganzhi_constants',
        'core.knowledge.data_validator', 'core.knowledge.data_integration',
        'core.knowledge.analysis_storage', 'core.knowledge.analysis_fallback',
        'core.knowledge.knowledge_base',
        'core.divination.hexagram_analyzer', 'core.divination.hexagram_data',
        'core.divination.liuren', 'core.divination.meihua',
        'core.location_db', 'core.lunar_converter',
        # UI
        'ui.main_window', 'ui.styles',
        'ui.components.settings_dialog', 'ui.components.about_dialog',
        'ui.components.input_panel', 'ui.components.result_panel',
        'ui.components.meihua_input', 'ui.components.meihua_result_panel',
        'ui.components.liuren_input', 'ui.components.liuren_result_panel',
        'ui.components.ai_analysis_worker', 'ui.components.ai_analysis_renderer',
        'ui.components.collapsible_card', 'ui.components.export_dialog',
        'ui.components.timeline',
        'ui.export.ai_titles', 'ui.export.base_exporter',
        'ui.export.csv_exporter', 'ui.export.excel_exporter', 'ui.export.pdf_exporter',
        # Service / API
        'service.bazi_service', 'api.agnes_client',
        # PySide6（含 SVG 渲染与 QML/Quick 依赖）
        'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        'PySide6.QtSvg', 'PySide6.QtQml', 'PySide6.QtQuick',
        # 第三方（业务必需）
        'lunarcalendar', 'bcrypt', 'openpyxl', 'reportlab', 'reportlab.graphics',
        'reportlab.lib.colors', 'requests', 'urllib3', 'certifi',
        'numpy', 'matplotlib', 'matplotlib.backends.backend_qtagg',
        # SSL
        '_ssl', 'ssl', 'certifi', 'certifi.core', 'urllib3.util.ssl_',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[
        os.path.join(ROOT, 'scripts', 'pyi_rth_ssl.py'),
        os.path.join(ROOT, 'scripts', 'pyi_rth_pyside6_qt6.py'),
    ],
    excludes=[
        'PyQt5', 'PyQt6', 'PIL', 'notebook', 'jinja2', 'tkinter', 'python313',
        # 持有上游密钥 / 废弃烧录，严禁入包
        'server', 'server.app', 'core._embedded_config',
        # 可选 RAG（函数内 try-import，缺失不影响主流程）
        'chromadb', 'sentence_transformers', 'rank_bm25', 'langchain',
        # 未使用 / 超大 Qt 模块裁剪（省 ~150–220MB）
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineQuick',
        'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.Qt3DInput', 'PySide6.Qt3DLogic',
        'PySide6.Qt3DExtras', 'PySide6.Qt3DAnimation', 'PySide6.Qt3DQuick',
        'PySide6.QtCharts', 'PySide6.QtChartsQml',
        'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
        'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtPositioning',
        'PySide6.QtSerialPort', 'PySide6.QtSql', 'PySide6.QtTest',
        'PySide6.QtDesigner', 'PySide6.QtLocation',
    ],
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
    icon=os.path.join(ROOT, 'assets', 'favicon.ico'),
)

# onedir：exe + _internal，绿色便携
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='风水排盘专业工具',
)
