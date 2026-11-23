# -*- mode: python ; coding: utf-8 -*-
"""风水排盘专业工具 - 便携版打包配置 (自动生成)"""
import os
import sys
import sysconfig
from importlib.util import find_spec
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# ---- 路径全部动态推导：换机器 / 换 venv / 换 conda 环境无需改 spec ----
# 项目根与 spec 目录均由本文件位置推导，不写死盘符与用户名。
# PyInstaller 6.22+ 的 spec 执行环境不再注入 __file__，需用 SPECPATH 兜底，
# 与根目录 KP-AI-FENGSHUI.spec 的既有做法保持一致。
# 注意：__file__ 指向 spec 文件本体，SPECPATH 指向 spec 所在目录，二者归一为
# _SPEC_DIR（spec 所在目录）后，项目根 = _SPEC_DIR.parent（spec 在 scripts/ 下）。
try:
    _SPEC_DIR = Path(__file__).resolve().parent
except NameError:  # PyInstaller 个别版本不注入 __file__，但会注入 SPECPATH
    _SPEC_DIR = Path(SPECPATH).resolve()  # noqa: F821
_ROOT = _SPEC_DIR.parent
_project_root = str(_ROOT)
_spec_dir = str(_SPEC_DIR)

# 当前解释器的 site-packages（跟随 venv / 系统 Python / conda）
_SITE = Path(sysconfig.get_paths()['purelib'])
if not _SITE.is_dir():  # 少数布局 purelib 不存在时回退 platlib
    _SITE = Path(sysconfig.get_paths()['platlib'])


def _locate_pkg(mod_name, fallback):
    """用 import 解析定位包/扩展目录；解析失败回退 fallback。"""
    try:
        spec = find_spec(mod_name)
        if spec and spec.origin:
            return Path(spec.origin).parent
    except (ImportError, ValueError):
        pass
    return Path(fallback)


# PySide6 优先取当前解释器的真实安装位置，其次回退仓库内 pyside6_packages
_pyside6_path = _locate_pkg('PySide6', _ROOT / 'pyside6_packages' / 'PySide6')
_certifi_dir = _locate_pkg('certifi', _SITE / 'certifi')

# 依赖目录探测顺序：PySide6 目录 → Python 根 → conda Library/bin → Python DLLs
_DEP_DIRS = [_pyside6_path, Path(sys.prefix), Path(sys.prefix) / 'Library' / 'bin',
             Path(sys.base_prefix), Path(sys.base_prefix) / 'DLLs',
             Path(sys.base_prefix) / 'Library' / 'bin']


def _pick(names):
    """按“候选文件名 × 候选目录”顺序定位二进制，缺失即跳过。"""
    out = []
    for name in names:
        for d in _DEP_DIRS:
            p = d / name
            if p.is_file():
                out.append((str(p), '.'))
                break
    return out


# Visual C++ 运行时（免除目标机安装 VC Redist）
_VC_BINS = _pick(['msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll',
                  'msvcp140_codecvt_ids.dll', 'msvcp140_atomic_wait.dll',
                  'vcruntime140.dll', 'vcruntime140_1.dll', 'vcruntime140_threads.dll',
                  'concrt140.dll', 'vccorlib140.dll'])

# SSL / OpenSSL（HTTPS 调 AI 必需）：collect_dynamic_libs 优先，逐目录兜底
_SSL_BINS = []
try:
    _SSL_BINS.extend(collect_dynamic_libs('ssl'))
except Exception:
    pass  # 无 ssl 包元数据的环境走下方兜底
_ssl_dir = _locate_pkg('_ssl', Path(sys.base_prefix) / 'DLLs')
_SSL_DIRS = [_ssl_dir, Path(sys.prefix) / 'DLLs', Path(sys.base_prefix) / 'DLLs',
             Path(sys.prefix) / 'Library' / 'bin', Path(sys.base_prefix) / 'Library' / 'bin']
for _n in ('_ssl.pyd', 'libssl-3-x64.dll', 'libcrypto-3-x64.dll',
           'libssl-3.dll', 'libcrypto-3.dll',
           'libssl-1_1-x64.dll', 'libcrypto-1_1-x64.dll'):
    for _d in _SSL_DIRS:
        _p = _d / _n
        if _p.is_file():
            _SSL_BINS.append((str(_p), '.'))
            break
# 去重（collect_dynamic_libs 与兜底可能命中同一文件）
_seen_ssl = set()
_SSL_UNIQ = []
for _src, _dst in _SSL_BINS:
    _key = (os.path.normcase(str(_src)), _dst)
    if _key in _seen_ssl:
        continue
    _seen_ssl.add(_key)
    _SSL_UNIQ.append((str(_src), _dst))

# 收集 PySide6 自带的 plugins（platforms / styles / imageformats 等）
_pyside6_plugins = collect_data_files('PySide6', subdir='plugins')

a = Analysis(
    [str(_ROOT / 'main.py')],
    pathex=[_project_root, _spec_dir, str(_SITE)],
    binaries=_VC_BINS + _SSL_UNIQ + [
        # ================= AI 凭据安全约定 =================
        # 产物中【不包含任何 AI 原始信息】：无端点、无密钥、无模型名。
        # 运行参数全部由用户在 GUI「设置 → 龙虎山大师兄配置」中填写，
        # 保存到用户本机的 ai_config.json（设备指纹混淆），与安装包无关。
        #
        # 构建前必须执行： python scripts/purge_ai_secrets.py
        # 构建后必须执行： python scripts/verify_build_security.py
        #
        # 因此这里不打包 config.ini / config.ini.example / _embedded_config.py。
    ],
    datas=[
        # 程序图标（main.py / main_window 用 get_resource_path('favicon.ico')）
        (str(_ROOT / 'assets' / 'favicon.ico'), '.'),
        # 数据库 schema
        (str(_ROOT / 'database'), 'database'),
        # 用户数据
        (str(_ROOT / 'data'), 'data'),
        # CA 证书 bundle（随解释器动态定位，换环境不再指向特定发行版安装目录）
        (str(_certifi_dir / 'cacert.pem'), 'certifi'),
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
        # AI 限速 / 指标（agnes_client / ai_cache 中既有顶层 import 也有函数内延迟 import，
        # 显式声明避免漏打）
        'api.ai_metrics',
        'api.ai_throttle',
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
    runtime_hooks=[str(_ROOT / 'scripts' / 'pyi_rth_ssl.py')],
    # 'server' 为历史中转服务端代码，持有上游密钥，严禁打进客户端；
    # 'core._embedded_config' 为已废弃的密钥烧录模块，即便有人重新生成也不得入包。
    excludes=['PyQt5', 'PyQt6', 'PIL', 'notebook', 'jinja2', 'tkinter', 'python313',
              'server', 'server.app', 'core._embedded_config'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure)

# onedir 标准写法：EXE 只装 bootloader + PYZ，二进制与数据统一由 COLLECT 落到
# _internal/。若 EXE 同时内嵌 a.binaries + a.datas 且未设 exclude_binaries=True，
# 会与 COLLECT 形成双份拷贝，产物接近翻倍（历史现象：dist 730MB / ZIP 410MB）。
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
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
    version=(str(_ROOT / 'version_info.txt') if (_ROOT / 'version_info.txt').is_file() else None),
    icon=str(_ROOT / 'assets' / 'favicon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='风水排盘专业工具',
)
