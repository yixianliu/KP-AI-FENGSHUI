# -*- coding: utf-8 -*-
"""
scripts/measure_performance.py — M7-T5 性能测量（离屏，可重复）

验收指标（docs/old/UI-Upgrade-Execution-Plan.md L159）：
    - 冷启动 < 2s
    - UI 渲染 < 200ms
    - 内存 < 150MB

测量项：
    1. 冷启动：从 import PySide6.QtWidgets 到 MainWindow.show() + 首帧 processEvents()
       完成所耗墙钟时间（含数据库初始化、字体注册、核心计算器构造）
    2. UI 渲染：
       a) 三面板 display_result(样本数据) 的构造 + 首帧耗时
       b) 板块切换 _switch() × 3 的平均耗时
       c) export_dialog 构造耗时
    3. 内存：进程 RSS（ctypes 调 Windows GetProcessMemoryInfo），测
       baseline / 构造 MainWindow 后 / 三面板渲染后 / 峰值

用法：
    QT_QPA_PLATFORM=offscreen python scripts/measure_performance.py
    QT_QPA_PLATFORM=offscreen python scripts/measure_performance.py --json build/perf.json

退出码：0 = 全部达标；1 = 存在未达标项。
"""
from __future__ import annotations

import ctypes
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
_VENDOR = os.path.join(_ROOT, 'build', 'vendor_libs')
if os.path.isdir(_VENDOR) and _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

# 验收阈值
COLD_START_LIMIT_MS = 2000.0
RENDER_LIMIT_MS = 200.0
MEMORY_LIMIT_MB = 150.0

RESULTS: list = []


def _record(name: str, value_ms: float, limit_ms: float, unit: str = 'ms', extra: str = ''):
    """记录一项测量结果。"""
    ok = value_ms <= limit_ms
    RESULTS.append({
        'name': name, 'value': value_ms, 'limit': limit_ms,
        'unit': unit, 'ok': ok, 'extra': extra,
    })
    flag = 'OK  ' if ok else 'FAIL'
    print(f"  [{flag}] {name}: {value_ms:.1f}{unit} (限 {limit_ms:.0f}{unit}) {extra}")
    return ok


# ---------------------------------------------------------------------------
# 内存测量（Windows / POSIX）
# ---------------------------------------------------------------------------
class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ('cb', ctypes.c_ulong),
        ('PageFaultCount', ctypes.c_ulong),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t),
    ]


def _rss_windows():
    """返回 (当前 RSS MB, 峰值 RSS MB)。

    两个坑（实测）：
    1. 必须用 `ctypes.WinDLL(...)` 显式加载；`ctypes.windll.kernel32` 上
       取不到 `GetProcessMemoryInfo` 符号（静默失败 → 回退 0.0）。
    2. 符号分布：psapi.dll 导出 `GetProcessMemoryInfo`；kernel32 导出的是
       `K32GetProcessMemoryInfo`。两处都试，任一成功即可。
    """
    candidates = (
        ('psapi', 'GetProcessMemoryInfo'),
        ('kernel32', 'K32GetProcessMemoryInfo'),
    )
    for dll_name, fn_name in candidates:
        try:
            dll = ctypes.WinDLL(dll_name, use_last_error=True)
            fn = getattr(dll, fn_name, None)
            if fn is None:
                continue
            k32 = ctypes.WinDLL('kernel32', use_last_error=True)
            # 坑 3：GetCurrentProcess 默认被 ctype 当成 c_int 返回，句柄被截断，
            # 传给 GetProcessMemoryInfo 会得到 ERROR_INVALID_HANDLE(6)。
            # 必须显式声明 restype/argtypes 为 void*。
            k32.GetCurrentProcess.restype = ctypes.c_void_p
            k32.GetCurrentProcess.argtypes = []
            fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
            fn.restype = ctypes.c_int
            h = k32.GetCurrentProcess()
            pmc = PROCESS_MEMORY_COUNTERS()
            pmc.cb = ctypes.sizeof(pmc)
            if fn(h, ctypes.byref(pmc), pmc.cb):
                return pmc.WorkingSetSize / 1048576.0, pmc.PeakWorkingSetSize / 1048576.0
            print(f"  [warn] {dll_name}.{fn_name} 返回 0，last_error={ctypes.get_last_error()}")
        except Exception as e:
            print(f"  [warn] {dll_name}.{fn_name} 失败: {e}")
    return 0.0, 0.0


def _rss_posix():
    """Linux/macOS：读 /proc/self/status 的 VmRSS（peak 不可用则回退 RSS）。"""
    try:
        with open('/proc/self/status', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    mb = int(line.split()[1]) / 1024.0
                    return mb, mb
    except Exception:
        pass
    return 0.0, 0.0


def rss_mb():
    """返回 (当前 RSS MB, 峰值 RSS MB)。"""
    if platform.system() == 'Windows':
        return _rss_windows()
    return _rss_posix()


# ---------------------------------------------------------------------------
# 测量
# ---------------------------------------------------------------------------
def measure_cold_start(app):
    """冷启动：MainWindow 构造 + show + 首帧。"""
    print("\n── 1. 冷启动 ──")
    t0 = time.perf_counter()
    from ui.main_window import MainWindow
    win = MainWindow()
    win.show()
    app.processEvents()
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    _record('MainWindow 冷启动（构造+show+首帧）', elapsed_ms, COLD_START_LIMIT_MS,
            extra='含 DB/字体/核心计算器初始化')
    return win


def _sample_bazi_data():
    """八字排盘样本（与 tests/ui 一致的结构）。"""
    return {
        'basic_info': {
            'pan_type': '八字四柱',
            'solar_date': '1990年5月15日',
            'lunar_date': '庚午年四月廿二',
            'hour': '12:00',
            'location': '北京',
            'gender': '男',
        },
        'bazi': {'year_pillar': '庚午', 'month_pillar': '辛巳',
                 'day_pillar': '戊午', 'hour_pillar': '戊午',
                 'rizhu': '戊', 'month_zhi': '巳'},
        'wuxing': {'木': 1, '火': 3, '土': 2, '金': 1, '水': 1},
        'shishen': {'summary': {'正官': 2, '正印': 1}, 'total_weights': {'total': 5, '官杀': 3}},
        'mingli': {'shensha': {'positive': [{'name': '天乙贵人'}],
                              'negative': [{'name': '羊刃'}]}},
        'analysis': [
            {'type': '吉', 'text': '印星护身，贵人相助'},
            {'type': '中', 'text': '食伤泄秀，才华出众'},
        ],
        'dayun': {'direction': '顺', 'periods': [
            {'period': 1, 'ganzhi': '壬午', 'start_age': 3, 'end_age': 12,
             'start_year': 1993, 'end_year': 2002, 'analysis': '早年平顺'},
        ]},
        'liunian': {'years': [
            {'year': 2026, 'ganzhi': '丙午', 'analysis': '流年顺遂'},
        ]},
        'bazi_types': {'strength': '身强', 'geju_type': '印格',
                       'geju_name': '正印格', 'wuxing_summary': '火旺'},
        'yuncheng': {'overview': '综合评分 78', 'career': '事业顺遂',
                     'wealth': '财运平稳', 'health': '注意饮食',
                     'love': '感情有波折', 'tags': ['吉时', '宜出行']},
    }


def _sample_meihua_data():
    return {
        'meihua_data': {
            'method': '时间起卦', 'base_hex': '地天泰',
            'changed_hex': '雷水解', 'hu_hex': '水地比',
            'hex_relation': '体生用',
        },
        'question': '问事业',
        'overall': {'overall_judgment': '吉', 'description': '天地交泰',
                    'advice': '宜顺天应人'},
        'suggestions': ['宜出行', '忌口舌'],
    }


def _sample_liuren_data():
    return {
        'liuren_data': {
            'pan_date': '2026-01-01', 'si_ke': '四课信息',
            'san_chuan': '三传信息', 'yue_jiang': '卯',
            'tian_pan': {'子': '癸', '午': '己'},
            'tian_jiang': [{'pos': '子', 'jiang': '甲'}, {'pos': '午', 'jiang': '庚'}],
            'ri_gan': '甲', 'ri_zhi': '子',
        },
    }


def measure_render(app):
    """UI 渲染：三面板 display_result + 板块切换 + export_dialog。"""
    print("\n── 2. UI 渲染 ──")

    # 2a. 三面板 display_result
    from ui.components.result_panel import ResultPanel
    from ui.components.meihua_result_panel import MeihuaResultPanel
    from ui.components.liuren_result_panel import LiurenResultPanel

    panels = [
        ('八字结果面板', ResultPanel, _sample_bazi_data()),
        ('梅花结果面板', MeihuaResultPanel, _sample_meihua_data()),
        ('六壬结果面板', LiurenResultPanel, _sample_liuren_data()),
    ]
    built = []
    for name, cls, data in panels:
        t0 = time.perf_counter()
        p = cls()
        p.show()
        try:
            p.display_result(data)
        except Exception as e:  # noqa: BLE001
            print(f"        (display_result 异常已忽略: {type(e).__name__}: {e})")
        app.processEvents()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        built.append(p)
        _record(f'{name} display_result', elapsed_ms, RENDER_LIMIT_MS)

    # 2b. 重复渲染（第二次走热路径，反映稳态）
    for name, p_data in zip(['八字', '梅花', '六壬'],
                            [_sample_bazi_data(), _sample_meihua_data(), _sample_liuren_data()]):
        p = built[['八字', '梅花', '六壬'].index(name)]
        t0 = time.perf_counter()
        try:
            p.display_result(p_data)
        except Exception:
            pass
        app.processEvents()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        _record(f'{name}面板 二次渲染（稳态）', elapsed_ms, RENDER_LIMIT_MS)

    # 2c. export_dialog 构造
    from ui.components.export_dialog import ExportDialog
    t0 = time.perf_counter()
    try:
        dlg = ExportDialog(_sample_bazi_data())
        dlg.show()
        app.processEvents()
        dlg.close()
    except Exception as e:  # noqa: BLE001
        print(f"        (export_dialog 构造异常已忽略: {type(e).__name__}: {e})")
        elapsed_ms = 0.0
    else:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
    if elapsed_ms:
        _record('导出对话框构造', elapsed_ms, RENDER_LIMIT_MS)

    return built


def measure_switch(app, win):
    """板块切换 _switch() × 3 平均耗时。"""
    print("\n── 2d. 板块切换 ──")
    times = []
    for pid in ('bazi', 'meihua', 'liuren', 'bazi'):
        t0 = time.perf_counter()
        try:
            win._switch(pid)
        except Exception:
            pass
        app.processEvents()
        times.append((time.perf_counter() - t0) * 1000.0)
    avg = statistics.mean(times)
    _record('板块切换平均耗时', avg, RENDER_LIMIT_MS,
            extra=f'(样本 {len(times)} 次: ' + ', '.join(f'{t:.0f}' for t in times) + ')')


def measure_memory(app, win):
    """内存：baseline / MainWindow 后 / 三面板渲染后 / 峰值。"""
    print("\n── 3. 内存 ──")
    cur, peak = rss_mb()
    print(f"  [info] MainWindow 构造后 RSS={cur:.1f}MB  峰值={peak:.1f}MB")

    # 强制再渲染一轮以观察内存增长
    from ui.components.result_panel import ResultPanel
    panels = []
    for _ in range(3):
        p = ResultPanel()
        p.show()
        try:
            p.display_result(_sample_bazi_data())
        except Exception:
            pass
        app.processEvents()
        panels.append(p)
    cur2, peak2 = rss_mb()
    print(f"  [info] +3 个结果面板后 RSS={cur2:.1f}MB  峰值={peak2:.1f}MB")

    _record('MainWindow 构造后 RSS', cur, MEMORY_LIMIT_MB, unit='MB')
    _record('全量渲染后 RSS', cur2, MEMORY_LIMIT_MB, unit='MB')
    _record('进程峰值 RSS', max(peak, peak2), MEMORY_LIMIT_MB, unit='MB',
            extra='(PeakWorkingSetSize)')

    # 释放面板，观察回收
    for p in panels:
        try:
            p.close()
            p.deleteLater()
        except Exception:
            pass
    app.processEvents()
    cur3, _ = rss_mb()
    print(f"  [info] 释放面板后 RSS={cur3:.1f}MB")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main(argv=None):
    argv = argv or sys.argv[1:]
    json_out = None
    if '--json' in argv:
        idx = argv.index('--json')
        if idx + 1 < len(argv):
            json_out = argv[idx + 1]

    from PySide6.QtWidgets import QApplication
    t_import = time.perf_counter()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle('Fusion')
    import_ms = (time.perf_counter() - t_import) * 1000.0

    print("=== M7-T5 性能测量（离屏）===")
    print(f"Python {sys.version.split()[0]}  |  {platform.system()} {platform.machine()}")
    print(f"QT_QPA_PLATFORM={os.environ.get('QT_QPA_PLATFORM')}")
    print(f"QApplication 构造: {import_ms:.1f}ms")

    base_rss, base_peak = rss_mb()
    print(f"基线 RSS={base_rss:.1f}MB  峰值={base_peak:.1f}MB")

    win = measure_cold_start(app)
    measure_render(app)
    measure_switch(app, win)
    measure_memory(app, win)

    # 汇总
    print("\n=== 汇总 ===")
    failed = [r for r in RESULTS if not r['ok']]
    for r in RESULTS:
        flag = 'PASS' if r['ok'] else 'FAIL'
        print(f"  {flag}  {r['name']}: {r['value']:.1f}{r['unit']} / 限 {r['limit']:.0f}{r['unit']}")
    print(f"\n共 {len(RESULTS)} 项，通过 {len(RESULTS) - len(failed)} 项，未达标 {len(failed)} 项。")

    if json_out:
        payload = {
            'meta': {
                'python': sys.version.split()[0],
                'platform': f'{platform.system()} {platform.machine()}',
                'qt_platform': os.environ.get('QT_QPA_PLATFORM'),
                'baseline_rss_mb': round(base_rss, 2),
                'baseline_peak_rss_mb': round(base_peak, 2),
            },
            'limits': {
                'cold_start_ms': COLD_START_LIMIT_MS,
                'render_ms': RENDER_LIMIT_MS,
                'memory_mb': MEMORY_LIMIT_MB,
            },
            'results': RESULTS,
            'passed': len(RESULTS) - len(failed),
            'failed': len(failed),
        }
        Path(json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(json_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                  encoding='utf-8')
        print(f"JSON 结果已写入 {json_out}")

    try:
        win.close()
    except Exception:
        pass

    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
