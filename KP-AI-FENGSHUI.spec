# -*- mode: python ; coding: utf-8 -*-
"""风水排盘专业工具 - 便携版打包配置 (自动生成)"""
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

_project_root = r'D:\PythonProject\KP-AI-FENGSHUI'
_spec_dir = r'D:\PythonProject\KP-AI-FENGSHUI\scripts'
_pyside6_path = r'D:\PythonProject\KP-AI-FENGSHUI\pyside6_packages\PySide6'

# 收集 PySide6 自带的 plugins（platforms / styles / imageformats 等）
_pyside6_plugins = collect_data_files('PySide6', subdir='plugins')

a = Analysis(
    [r'D:\PythonProject\KP-AI-FENGSHUI\main.py'],
    pathex=[_project_root, _spec_dir],
    binaries=[
        # Visual C++ 运行时 (来自 PySide6 安装目录)
        (r'D:\PythonProject\KP-AI-FENGSHUI\pyside6_packages\PySide6\msvcp140.dll', '.'),
        (r'D:\PythonProject\KP-AI-FENGSHUI\pyside6_packages\PySide6\msvcp140_1.dll', '.'),
        (r'D:\PythonProject\KP-AI-FENGSHUI\pyside6_packages\PySide6\msvcp140_2.dll', '.'),
        (r'D:\PythonProject\KP-AI-FENGSHUI\pyside6_packages\PySide6\msvcp140_codecvt_ids.dll', '.'),
        (r'D:\PythonProject\KP-AI-FENGSHUI\pyside6_packages\PySide6\vcruntime140.dll', '.'),
        (r'D:\PythonProject\KP-AI-FENGSHUI\pyside6_packages\PySide6\vcruntime140_1.dll', '.'),
        (r'D:\PythonProject\KP-AI-FENGSHUI\pyside6_packages\PySide6\concrt140.dll', '.'),
        (r'D:\PythonProject\KP-AI-FENGSHUI\pyside6_packages\PySide6\vccorlib140.dll', '.'),
        # SSL 模块 (解决 HTTPS 连接问题)
        (r'D:\anaconda3\DLLs\_ssl.pyd', '.'),
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
        (r'D:\PythonProject\KP-AI-FENGSHUI\assets\favicon.ico', '.'),
        # 数据库 schema
        (r'D:\PythonProject\KP-AI-FENGSHUI\database', 'database'),
        # 用户数据
        (r'D:\PythonProject\KP-AI-FENGSHUI\data', 'data'),
        # CA 证书 bundle
        (r'D:\anaconda3\Lib\site-packages\certifi\cacert.pem', 'certifi'),
        # PySide6 plugins（platforms / styles / imageformats 等），合并到 _MEIPASS/plugins/
        *_pyside6_plugins,
    ],
    hiddenimports=[
        # 核心模块
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
        'ui.components.timeline',
        # 统一 AI 分析渲染入口（三面板延迟 import render_analysis，PyInstaller 静态分析追不到）
        'ui.components.ai_analysis_renderer',
        # 导出层 AI 章节标题常量（export_dialog 与三个导出器显式 import）
        'ui.export.ai_titles',
        'ui.export.base_exporter',
        'ui.export.csv_exporter',
        'ui.export.excel_exporter',
        'ui.export.pdf_exporter',
        # Service 层（main_window.py 函数内延迟 import BaziService）
        'service.bazi_service',
        # AI 分析降级回退（analysis_storage.py 全部为函数内 try import）
        'core.knowledge.analysis_fallback',
        # 版本号单一权威源（GUI 与 EXE 版本资源均从此读取）
        'core.app_version',
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
    runtime_hooks=[r'D:\PythonProject\KP-AI-FENGSHUI\scripts\pyi_rth_ssl.py'],
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
    # 版本资源：由 build_release.py 依据 app_version.py 自动生成，
    # 使 EXE 文件属性中的版本号与程序/界面版本完全一致。
    version=os.path.join(_project_root, 'version_info.txt'),
    icon=os.path.join(_spec_dir, '..', 'assets', 'favicon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='风水排盘专业工具',
)
