# -*- coding: utf-8 -*-
"""
scripts/verify_chart_responsive.py — P12/P13 图表响应式与状态验证

P12 痛点：窗口 resize 时 FigureCanvasQTAgg 无响应式重绘 → DPI 抖动。
关键区分点：`set_size_inches(forward=True)` 只改 Figure 尺寸，**不会触发重绘**。
仅校验 `figure.get_size_inches()` 变化无法证明修复——必须验证
**canvas 实际渲染位图尺寸 == figure 尺寸**（即 draw 已真正执行）。

验证项：
  R1  真 DPI：_dpi 来自系统 physicalDotsPerInch，非硬编码 100
  R2  响应式：3 个不同控件尺寸下，figure 英寸数与像素宽均跟随变化
  R3  **重绘真实发生**：canvas renderer 位图尺寸 == figure 像素尺寸（防抖后）
  R4  无抖动：连续快速 resize 后位图尺寸与最终目标一致（防抖合并有效）
  E1  P13 空数据 → EmptyState 页（index 1）
  E2  P13 有数据  → 图表页（index 0）+ tooltip 高亮线句柄已注册
  E3  P13 加载失败 → ErrorState 页（index 2）+ 页序稳定
  S1  截图落盘 build/screenshots/chart.png

用法：
    QT_QPA_PLATFORM=offscreen python scripts/verify_chart_responsive.py
退出码：0 全通过；1 有失败；2 缺 matplotlib（跳过）。
环境：需带 PySide6 的解释器（venv）。matplotlib 从 build/vendor_libs 加载。
"""
import os
import sys
import traceback
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

VENDOR = ROOT / 'build' / 'vendor_libs'
if VENDOR.is_dir():
    sys.path.insert(0, str(VENDOR))

OUT_DIR = ROOT / 'build' / 'screenshots'

_results = []


def check(name, fn):
    """执行单项检查，记录通过/失败。"""
    try:
        fn()
        _results.append((name, True, ''))
        print(f"  [OK]   {name}")
    except Exception as e:  # noqa: BLE001
        _results.append((name, False, f"{type(e).__name__}: {e}"))
        print(f"  [FAIL] {name} -> {type(e).__name__}: {e}")
        traceback.print_exc(limit=4)


def _settle(app, ms=300):
    """等待防抖定时器与 draw_idle 完成。"""
    from PySide6.QtTest import QTest
    QTest.qWait(ms)
    app.processEvents()


def main():
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        print("=== 图表响应式验证 ===")
        print("  [SKIP] venv 无 matplotlib（build/vendor_libs 缺失），跳过 P12/P13 运行时验证")
        print("         安装：TEMP=build/piptmp pip install --no-cache-dir --target build/vendor_libs matplotlib")
        return 2

    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    print(f"=== P12/P13 图表响应式验证 (matplotlib {matplotlib.__version__}) ===")

    from ui.components.ai_metrics_chart import AIMetricsChart
    from ui.styles import Spacing

    chart = AIMetricsChart()
    chart.show()
    app.processEvents()

    # ---------- R1 真 DPI ----------
    def r1_dpi():
        dpi = chart._detect_dpi()
        screen = QApplication.primaryScreen()
        real = float(screen.physicalDotsPerInch())
        assert dpi == real, f"_dpi={dpi} 与系统物理 DPI {real} 不一致"
        assert chart._dpi == real, f"实例 _dpi={chart._dpi} 未使用系统 DPI {real}"
        print(f"       · 系统物理 DPI={real} → chart._dpi={chart._dpi}")

    check('R1 真 DPI（跟随系统 physicalDotsPerInch）', r1_dpi)

    # ---------- R2/R3 响应式 + 真实重绘 ----------
    def _px_size(c):
        """返回 (figure 像素宽, figure 像素高, renderer 位图宽, renderer 位图高)。"""
        fig = c.figure
        fw, fh = fig.get_size_inches()
        dpi = fig.dpi
        r = fig.canvas.get_renderer()
        rw, rh = r.get_canvas_width_height() if r is not None else (0, 0)
        return round(fw * dpi, 1), round(fh * dpi, 1), rw, rh

    sizes = [(900, 600), (520, 420), (1280, 760)]
    observed = []

    def r2_responsive():
        nonlocal observed
        observed = []
        for w, h in sizes:
            chart.resize(w, h)
            app.processEvents()
            _settle(app)
            px = _px_size(chart)
            observed.append((w, h, px))
            # figure 像素宽 = max(320, width - 2*Spacing.S6)，须随控件变化
            expect = max(320, w - Spacing.S6 * 2)
            assert px[0] == expect, f"控件宽 {w} → figure 像素宽 {px[0]}，期望 {expect}"
            # ±1px：set_size_inches 会先取整到像素再回算英寸，存在取整误差
            exp_h = round(expect * 0.45, 1)
            assert abs(px[1] - exp_h) <= 1.0, \
                f"figure 高 {px[1]} 不符合 0.45 宽高比（期望 {exp_h} ±1px 取整误差）"
            print(f"       · 控件 {w}x{h} → figure {px[0]}x{px[1]}px")
        widths = [o[2][0] for o in observed]
        assert len(set(widths)) == len(widths), \
            f"不同控件宽度下 figure 像素宽未变化：{widths}"

    check('R2 响应式（figure 尺寸随控件尺寸变化）', r2_responsive)

    def r3_repainted():
        """P12 核心：renderer 位图尺寸 == figure 尺寸，证明 draw 真实执行。"""
        assert observed, "无观测数据（R2 未产出），R3 无法验证"
        for w, h, px in observed:
            fw, fh, rw, rh = px
            assert rw == fw, \
                f"控件 {w}x{h}：renderer 位图宽 {rw} != figure 像素宽 {fw}（draw 未执行）"
            assert rh == fh, \
                f"控件 {w}x{h}：renderer 位图高 {rh} != figure 像素高 {fh}（draw 未执行）"
            print(f"       · 控件 {w}x{h}：位图 {rw}x{rh} == figure {fw}x{fh} ✅")

    check('R3 重绘真实发生（renderer 位图 == figure 尺寸）', r3_repainted)

    def r4_debounce():
        """防抖：连续快速 resize 后，最终位图与目标尺寸一致。"""
        import random
        random.seed(42)
        for _ in range(12):
            chart.resize(random.randint(480, 1100), random.randint(400, 700))
            app.processEvents()
        _settle(app, 400)
        w = chart.width()
        expect = max(320, w - Spacing.S6 * 2)
        fw, fh, rw, rh = _px_size(chart)
        assert fw == expect, f"防抖后 figure 像素宽 {fw} != 期望 {expect}"
        assert rw == fw, f"防抖后位图宽 {rw} != figure 宽 {fw}"
        print(f"       · 12 次随机 resize 后收敛：控件 {w} → figure/位图 {fw}x{fh}")

    check('R4 防抖合并（快速 resize 后位图收敛）', r4_debounce)

    # ---------- E1~E3 P13 状态 ----------
    from datetime import datetime, timedelta

    def e1_empty():
        chart.update_charts([], [])
        assert chart._stack.currentIndex() == 1, \
            f"空数据应切到 EmptyState(index 1)，实际 {chart._stack.currentIndex()}"
        print(f"       · 空数据 → stack index={chart._stack.currentIndex()} (EmptyState)")

    check('E1 空数据 → EmptyState', e1_empty)

    def e2_data():
        base = datetime(2026, 9, 1, 9, 0)
        cache = [(base + timedelta(hours=i), 40 + i * 4.5) for i in range(10)]
        circuit = [(base + timedelta(hours=i), (i % 3)) for i in range(10)]
        chart.update_charts(cache, circuit)
        assert chart._stack.currentIndex() == 0, \
            f"有数据应切到图表页(index 0)，实际 {chart._stack.currentIndex()}"
        assert len(chart._highlight) == 2, \
            f"两条曲线句柄应为 2，实际 {len(chart._highlight)}"
        assert chart._last_tooltip is None, "旧 tooltip 未清理"
        fw, fh, rw, rh = _px_size(chart)
        assert rw == fw, "重建后未重绘（位图尺寸未跟随）"
        print(f"       · 10+10 点 → index={chart._stack.currentIndex()}，"
              f"highlight={len(chart._highlight)}，位图 {rw}x{rh}")

    check('E2 有数据 → 图表页 + 高亮句柄 + 重建后重绘', e2_data)

    def e3_error():
        chart._show_error('指标加载失败：测试异常')
        assert chart._stack.currentIndex() == 2, \
            f"错误应切到 index 2，实际 {chart._stack.currentIndex()}"
        # 再次触发，页序须稳定（insertWidget 位置正确，不能追加到 index 3）
        chart._show_error('第二次异常')
        assert chart._stack.currentIndex() == 2
        assert chart._stack.count() == 3, \
            f"重复触发后页数应为 3，实际 {chart._stack.count()}（旧页未清理）"
        # retry 信号须可发
        from ui.components.states import ErrorState
        err = chart._error.findChild(ErrorState)
        assert err is not None and err._retry_btn is not None, "错误态缺少重试按钮"
        print(f"       · 异常 → index={chart._stack.currentIndex()}，页数={chart._stack.count()}")

    check('E3 加载失败 → ErrorState + 页序稳定 + 重试按钮', e3_error)

    # ---------- S1 截图落盘 ----------
    def s1_screenshot():
        chart._stack.setCurrentIndex(0)
        chart.resize(900, 600)
        app.processEvents()
        _settle(app)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / 'chart.png'
        assert chart.grab().save(str(path)), f"截图保存失败：{path}"
        print(f"       · 截图落盘 {path.relative_to(ROOT)}")

    check('S1 图表截图落盘', s1_screenshot)

    # ---------- 汇总 ----------
    total = len(_results)
    passed = sum(1 for _, ok, _ in _results if ok)
    print('-' * 58)
    if passed == total:
        print(f"verify_chart_responsive: {passed}/{total} 全通过 ✅")
        return 0
    print(f"verify_chart_responsive: {passed}/{total} 通过，{total - passed} 失败 ❌")
    for name, ok, err in _results:
        if not ok:
            print(f"  - {name}: {err}")
    return 1


if __name__ == '__main__':
    sys.exit(main())
