# -*- mode: python ; coding: utf-8 -*-
"""Windows 绿色便携版 (onedir) — 以已验证基线增强。

产物: <ROOT>/dist/风水排盘专业工具/{风水排盘专业工具.exe, _internal/}
资源规则见 docs/packaging-plan.md §4。

路径解析原则（换机器/换 Python 环境无需改 spec）：
  1. ROOT 由 spec 自身位置推导（不写死盘符）；
  2. site-packages 由 sysconfig 推导（跟随当前解释器/虚拟环境）；
  3. SSL / VC 运行库用 importlib 定位 + collect_dynamic_libs 收集，附带
     官方安装包 / conda 布局兜底；
  4. 所有 datas 条目先校验源文件存在，缺失即跳过，避免换机器后构建报错。
"""
import os
import sys
import sysconfig
from importlib.util import find_spec
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# ---- 项目根目录 ----
try:
    ROOT = Path(__file__).resolve().parent
except NameError:  # PyInstaller 个别版本不注入 __file__，但会注入 SPECPATH
    ROOT = Path(SPECPATH).resolve()  # noqa: F821

# ---- 当前解释器的 site-packages（跟随 venv / 系统 Python / conda）----
SITE = Path(sysconfig.get_paths()['purelib'])
if not SITE.is_dir():  # 兜底：少数布局 purelib 不存在时用 platlib
    SITE = Path(sysconfig.get_paths()['platlib'])


def _module_dir(mod_name, fallback):
    """用 import 解析定位某个包/扩展所在目录；解析失败回退到 fallback。"""
    try:
        spec = find_spec(mod_name)
        if spec and spec.origin:
            return Path(spec.origin).parent
    except (ImportError, ValueError):
        pass
    return Path(fallback)


PY_SIDE = _module_dir('PySide6', SITE / 'PySide6')
CERTIFI_DIR = _module_dir('certifi', SITE / 'certifi')

# ---- VC 运行时（随包，免除目标机安装 VC Redist）----
_VC = ['msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll',
       'msvcp140_codecvt_ids.dll', 'vcruntime140.dll', 'vcruntime140_1.dll',
       'concrt140.dll', 'vccorlib140.dll']
# 运行库可能位于 PySide6 目录 / Python 安装根 / conda Library\bin，逐处探测
_VC_DIRS = [PY_SIDE, Path(sys.prefix), Path(sys.prefix) / 'Library' / 'bin',
            Path(sys.base_prefix), Path(sys.base_prefix) / 'DLLs']
vc_bins = []
for _name in _VC:
    for _d in _VC_DIRS:
        _p = _d / _name
        if _p.is_file():
            vc_bins.append((str(_p), '.'))
            break


def _ssl_binaries():
    """定位 _ssl 扩展与 OpenSSL DLL（HTTPS 调 AI 必需），不依赖写死路径。

    说明：collect_dynamic_libs('ssl') 对非包模块通常返回空，真正的 DLL 位于
    （a）_ssl 扩展所在目录，（b）Windows 官方安装包的 DLLs 目录，
    （c）conda 布局的 Library/bin。三种命名（libssl-3-x64 / libssl-3 / libssl-1_1）均探测。
    """
    found = []
    try:
        found.extend(collect_dynamic_libs('ssl'))
    except Exception:
        pass  # 极少数环境无 ssl 包元数据，走下方兜底

    ssl_dir = _module_dir('_ssl', Path(sys.base_prefix) / 'DLLs')
    _SSL_DIRS = [
        ssl_dir,
        Path(sys.prefix) / 'DLLs',
        Path(sys.base_prefix) / 'DLLs',
        Path(sys.prefix) / 'Library' / 'bin',
        Path(sys.base_prefix) / 'Library' / 'bin',
    ]
    _SSL_NAMES = [
        '_ssl.pyd',
        'libssl-3-x64.dll', 'libcrypto-3-x64.dll',   # conda 布局
        'libssl-3.dll', 'libcrypto-3.dll',           # python.org 布局
        'libssl-1_1-x64.dll', 'libcrypto-1_1-x64.dll',  # 旧环境兜底
    ]
    for _name in _SSL_NAMES:
        for _d in _SSL_DIRS:
            _p = _d / _name
            if _p.is_file():
                found.append((str(_p), '.'))
                break

    seen, uniq = set(), []
    for src, dest in found:
        key = (os.path.normcase(str(src)), dest)
        if key in seen or not os.path.isfile(str(src)):
            continue
        seen.add(key)
        uniq.append((str(src), dest))
    return uniq


ssl_bins = _ssl_binaries()

# ---- PySide6 自带插件（platforms / imageformats / styles / tls / iconengines）----
_pyside6_plugins = collect_data_files('PySide6', subdir='plugins')


# 运行期用户数据绝不可入包：*.db 是用户本机历史记录（含隐私），data/cache 是
# 本机缓存。目录拷贝默认会整目录吸入，故逐文件展开并过滤。
_EXCLUDE_DB_SUFFIX = ('.db', '.db-wal', '.db-shm', '.db-journal', '.tmp')
_EXCLUDE_DIRS = {'__pycache__', 'cache'}


def _tree(src_root, dest_prefix):
    """把 src_root 逐文件展开为 (源文件, 目标目录) 列表，并过滤用户运行期数据。"""
    out = []
    src_root = str(src_root)
    if not os.path.isdir(src_root):
        return out
    for dirpath, dirnames, filenames in os.walk(src_root):
        dirnames[:] = [d for d in dirnames if d not in _EXCLUDE_DIRS]
        rel = os.path.relpath(dirpath, src_root)
        dest = dest_prefix if rel == '.' else os.path.join(dest_prefix, rel).replace(os.sep, '/')
        for fn in filenames:
            if fn.lower().endswith(_EXCLUDE_DB_SUFFIX) or fn.endswith('.pyc'):
                continue
            out.append((os.path.join(dirpath, fn), dest))
    return out


def _datas():
    """按存在性过滤 datas 条目，换机器缺资源时只跳过而不中断构建。"""
    items = [
        # 程序图标：必须落在 _MEIPASS 根（main.py / main_window 用 get_resource_path('favicon.ico')）
        (ROOT / 'assets' / 'favicon.ico', '.'),
        # 运行时 SVG 图标集（icons.py 用 assets/icons/{name}.svg）
        (ROOT / 'assets', 'assets'),
        # 关于页二维码 + 产品图（about_dialog 用 images/...）
        (ROOT / 'images', 'images'),
        # CA 证书链
        (CERTIFI_DIR / 'cacert.pem', 'certifi'),
        # Qt 国际化数据（Qt6Core 依赖）
        (PY_SIDE / 'resources' / 'icudtl.dat', '.'),
    ]
    # 建库 schema（只读资源，core/sqlite_db.py 运行时建库依赖）：必须随包，
    # 否则干净机器首次运行建库即失败（历史「干净检出不起来」根因）。
    items.extend(_tree(ROOT / 'database', 'database'))
    # 可写种子数据（unihan 笔画 JSON）：同样逐文件过滤，剔除 *.db 与 data/cache
    items.extend(_tree(ROOT / 'data', 'data'))
    items.extend(_pyside6_plugins)
    out = []
    for src, dest in items:
        _s = str(src)
        if os.path.isdir(_s) or os.path.isfile(_s):
            out.append((_s, dest))
    return out


a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(SITE), str(ROOT), str(ROOT / 'scripts')],
    binaries=vc_bins + ssl_bins,
    datas=_datas(),
    hiddenimports=[
        # 业务核心
        'core.path_utils', 'core.secure_log', 'core.device_identity',
        'core.sqlite_db', 'core.log_handler', 'core.database_manager',
        'core.ai_cache', 'core.app_version', 'core.ai_config', 'core.local_settings',
        'core.dll_diagnostic', 'core.bazi.bazi_calculator', 'core.bazi.bazi_types',
        'core.bazi._baazi_compat', 'core.bazi.geju_analyzer', 'core.bazi.mingli',
        'core.bazi.shishen', 'core.bazi.wuxing', 'core.bazi.yuncheng', 'core.bazi.yunshi',
        'core.calendar_utils', 'core.ganzhi_constants',
        'core.astronomy.solar_time', 'core.bazi.pillar', 'core.bazi.bazi_batch',
        'core.knowledge.data_validator', 'core.knowledge.data_integration',
        'core.knowledge.analysis_storage', 'core.knowledge.analysis_fallback',
        'core.knowledge.knowledge_base',
        'core.divination.hexagram_analyzer', 'core.divination.hexagram_data',
        'core.divination.meihua',
        'core.location_db', 'core.lunar_converter',
        # UI
        'ui.main_window', 'ui.styles',
        'ui.components.settings_dialog', 'ui.components.about_dialog',
        'ui.components.input_panel', 'ui.components.result_panel',
        'ui.components.meihua_input', 'ui.components.meihua_result_panel',
        'ui.components.ai_analysis_worker', 'ui.components.ai_analysis_renderer',
        'ui.components.collapsible_card', 'ui.components.export_dialog',
        'ui.components.timeline', 'ui.components.history_panel',
        'ui.components.bazi_calculation_worker', 'ui.components.pan_task_worker',
        'ui.components.export_worker', 'ui.components.xuan_kong_input',
        'ui.components.xuan_kong_result_panel', 'ui.components.meihua_result_panel',
        'ui.export.ai_titles', 'ui.export.base_exporter',
        'ui.export.csv_exporter', 'ui.export.excel_exporter', 'ui.export.pdf_exporter',
        # Service / API（ai_metrics / ai_throttle 为 agnes_client 顶层依赖，
        # 部分调用点走函数内延迟 import，显式声明避免漏打）
        'service.bazi_service', 'service.location_resolver', 'api.agnes_client',
        'api.ai_metrics', 'api.ai_throttle',
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
        str(ROOT / 'scripts' / 'pyi_rth_ssl.py'),
        str(ROOT / 'scripts' / 'pyi_rth_pyside6_qt6.py'),
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

# onedir 标准写法：EXE 只装 bootloader + PYZ，二进制与数据统一由 COLLECT 落到
# _internal/。若 EXE 同时内嵌 a.binaries+a.datas（且未设 exclude_binaries=True），
# 会与 COLLECT 形成双份拷贝，体积接近翻倍（历史现象：dist 730MB / ZIP 410MB）。
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
    icon=str(ROOT / 'assets' / 'favicon.ico'),
    # 版本资源：此前遗漏该参数，exe 属性里没有产品名/版本号
    version=str(ROOT / 'version_info.txt') if (ROOT / 'version_info.txt').is_file() else None,
)

# onedir：exe + _internal，绿色便携
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='风水排盘专业工具',
)
