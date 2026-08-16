# -*- mode: python ; coding: utf-8 -*-
"""风水排盘专业工具 - 便携版打包配置"""
import os

block_cipher = None

_project_root = 'D:/PythonProject/KP-AI-FENGSHUI'
_managed_python = 'C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12'

a = Analysis(
    ['main.py'],
    pathex=[_project_root],
    binaries=[
        # Visual C++ 运行时 (来自 managed Python PySide6)
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/Lib/site-packages/PySide6/msvcp140.dll', '.'),
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/Lib/site-packages/PySide6/msvcp140_1.dll', '.'),
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/Lib/site-packages/PySide6/msvcp140_2.dll', '.'),
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/Lib/site-packages/PySide6/msvcp140_codecvt_ids.dll', '.'),
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/Lib/site-packages/PySide6/vcruntime140.dll', '.'),
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/Lib/site-packages/PySide6/vcruntime140_1.dll', '.'),
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/Lib/site-packages/PySide6/concrt140.dll', '.'),
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/Lib/site-packages/PySide6/vccorlib140.dll', '.'),
        # SSL 模块 (解决 HTTPS 连接问题)
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/DLLs/_ssl.pyd', '.'),
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/DLLs/libssl-3-x64.dll', '.'),
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/DLLs/libcrypto-3-x64.dll', '.'),
    ],
    datas=[
        # ================= AI 凭据安全约定 =================
        # 产物中【不包含任何 AI 原始信息】：无端点、无密钥、无模型名。
        # 运行参数全部由用户在 GUI「设置 → 龙虎山大师兄配置」中填写，
        # 保存到用户本机的 ai_config.json（设备指纹混淆），与安装包无关。
        #
        # 构建前必须执行： python scripts/purge_ai_secrets.py
        # 构建后必须执行： python scripts/verify_build_security.py
        #
        # 因此这里不打包 config.ini / config.ini.example / _embedded_config.py。
        ('favicon.ico', '.'),
        # 数据库 schema
        ('database', 'database'),
        # 用户数据
        ('data', 'data'),
        # CA 证书 bundle
        ('C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/Lib/site-packages/certifi/cacert.pem', 'certifi'),
    ],
    hiddenimports=[
        # 核心模块
        'core.path_utils',
        'core.secure_log',
        'core.device_identity',
        'core.sqlite_db',
        'core.log_handler',
        'core.analysis_storage',
        'core.ai_cache',
        'core.database_manager',
        'core.bazi_calculator',
        'core.bazi_types',
        'core.calendar_utils',
        'core.ganzhi_constants',
        'core.data_validator',
        'core.data_integration',
        'core.geju_analyzer',
        'core.hexagram_analyzer',
        'core.hexagram_data',
        'core.knowledge_base',
        'core.liuren',
        'core.location_db',
        'core.lunar_converter',
        'core.meihua',
        'core.mingli',
        'core.shishen',
        'core.wuxing',
        'core.yuncheng',
        'core.yunshi',
        'core._baazi_compat',
        # UI 模块
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
        # API 模块
        'api.agnes_client',
        # AI 配置中央管理器（模型类型/端点/认证/请求参数的唯一权威源）
        'core.ai_config',
        # 本地用户设置（兼容层，转发到 core.ai_config）
        'core.local_settings',
        # 第三方依赖
        'lunarcalendar',
        'bcrypt',
        'openpyxl',
        'reportlab',
        'reportlab.graphics',
        'reportlab.lib.colors',
        # SSL 模块 (解决 HTTPS 连接问题)
        '_ssl', 'ssl', 'certifi', 'certifi.core',
        'urllib3.util.ssl_',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_ssl.py'],
    # 'server' 为历史中转服务端代码，持有上游密钥，严禁打进客户端；
    # 'core._embedded_config' 为已废弃的密钥烧录模块，即便有人重新生成也不得入包。
    excludes=['PyQt5', 'PyQt6', 'PIL', 'notebook', 'jinja2', 'tkinter', 'python313',
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
    icon=os.path.join(_project_root, 'favicon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='风水排盘专业工具',
)
