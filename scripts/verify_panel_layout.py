# -*- coding: utf-8 -*-
"""
scripts/verify_panel_layout.py — 四结果面板布局与间距体系验证（P05/P06）

P05/P06 痛点：四面板 setSpacing 硬编码混用（2/4/5/6/8/10/12/14/16/18），
同类列表项跨面板视觉不齐。重构为 Spacing.S* 令牌后须验证两件事：

  1. **体系合规**：运行时遍历每个面板 widget 树的全部 QLayout，
     spacing() 值必须落在 8-4 体系 {0,4,8,12,16,20,24,32,48}
     （-1 = 未显式设置、交给样式表，合法）
  2. **布局未崩坏**：四面板均可离屏构造，sizeHint 合理，截图落盘可肉眼复核

类名采用运行时探测（模块内 QWidget 子类且以 Panel 结尾），避免硬编码漂移。

用法：
    QT_QPA_PLATFORM=offscreen python scripts/verify_panel_layout.py
退出码：0 全通过；1 有失败。
"""
import inspect
import importlib
import os
import sys
import traceback
from collections import Counter
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

VENDOR = ROOT / 'build' / 'vendor_libs'
if VENDOR.is_dir():
    sys.path.insert(0, str(VENDOR))

OUT_DIR = ROOT / 'build' / 'screenshots'

# 8-4 基准体系（Spacing.S0 ~ S8）
GRID = {0, 4, 8, 12, 16, 20, 24, 32, 48}
UNSET = {-1}  # QLayout 默认值：未显式设置，由样式表决定

PANELS = [
    ('bazi', 'ui.components.result_panel'),
    ('meihua', 'ui.components.meihua_result_panel'),
    ('liuren', 'ui.components.liuren_result_panel'),
    ('xuan_kong', 'ui.components.xuan_kong_result_panel'),
]

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


def _find_panel_cls(module, qt_widget_cls):
    """探测模块内的面板类（QWidget 子类且类名以 Panel 结尾）。"""
    for _, obj in vars(module).items():
        if inspect.isclass(obj) and issubclass(obj, qt_widget_cls) \
                and obj.__name__.endswith('Panel'):
            return obj
    return None


def main():
    from PySide6.QtWidgets import QApplication, QWidget, QLayout

    app = QApplication.instance() or QApplication(sys.argv)
    print("=== 四结果面板布局与间距体系验证 ===")

    built = {}

    def build_all():
        for key, mod_name in PANELS:
            mod = importlib.import_module(mod_name)
            cls = _find_panel_cls(mod, QWidget)
            assert cls is not None, f"{mod_name} 未找到 *Panel 类"
            w = cls()
            w.resize(900, 700)
            w.show()
            app.processEvents()
            built[key] = (cls.__name__, w)

    check('四面板离屏构造', build_all)

    def collect(w):
        """收集 widget 树内所有布局的 spacing 值分布，并附带来源链便于定位。

        Returns:
            (值 -> 计数, [(值, 来源描述), ...])
        """
        c = Counter()
        details = []
        for lay in w.findChildren(QLayout):
            v = lay.spacing()
            c[v] += 1
            chain = []
            node = lay.parent()
            for _ in range(4):
                if node is None:
                    break
                chain.append(type(node).__name__)
                node = node.parent()
            details.append((v, f"{type(lay).__name__} @ {' → '.join(chain)}"))
        return c, details

    dist = {}

    def grid_compliance():
        for key, (cls, w) in built.items():
            d, details = collect(w)
            dist[key] = d
            bad = {v: n for v, n in d.items() if v not in GRID and v not in UNSET}
            print(f"       · {key:<9} {cls:<24} 布局数={sum(d.values()):>3} "
                  f"值分布={dict(sorted(d.items()))}")
            for v, src in details:
                if v in bad:
                    print(f"           ⚠ 越界 spacing={v} 来源：{src}")
            assert not bad, f"{key} 存在非 8-4 体系间距 {bad}"

    check('间距全部落在 8-4 体系（S0~S8）', grid_compliance)

    def sizehint():
        for key, (cls, w) in built.items():
            sh = w.sizeHint()
            assert sh.width() > 200 and sh.height() > 100, \
                f"{key} sizeHint 异常 {sh.width()}x{sh.height()}（布局崩坏）"
            print(f"       · {key:<9} sizeHint={sh.width()}x{sh.height()}")

    check('sizeHint 合理（布局未崩坏）', sizehint)

    # M3-1：内容区边距统一。bazi/meihua/liuren 的内容布局须同为 (24,24,24,24)/16。
    # xuan_kong 结构特殊（九宫格直挂根布局 + 内层 detail），按用户决议暂不纳入统一口径。
    CONTENT_ATTR = {'bazi': 'clay', 'meihua': 'content_layout', 'liuren': 'content_layout'}
    TARGET_MARGINS = (24, 24, 24, 24)
    TARGET_SPACING = 16

    def content_margins():
        for key, attr in CONTENT_ATTR.items():
            _cls, w = built[key]
            lay = getattr(w, attr, None)
            assert lay is not None, f"{key} 缺少内容布局 `{attr}`"
            m = lay.contentsMargins()
            vals = (m.left(), m.top(), m.right(), m.bottom())
            assert vals == TARGET_MARGINS, f"{key} 内容区边距 {vals} != {TARGET_MARGINS}"
            assert lay.spacing() == TARGET_SPACING, \
                f"{key} 内容区间距 {lay.spacing()} != {TARGET_SPACING}"
            print(f"       · {key:<9} {attr:<16} margins={vals} spacing={lay.spacing()}")

    check('M3-1 内容区边距统一 (24,24,24,24)/16（bazi/meihua/liuren）', content_margins)

    def shots():
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for key, (cls, w) in built.items():
            p = OUT_DIR / f'panel_{key}.png'
            assert w.grab().save(str(p)), f"截图失败：{p}"
            print(f"       · {p.relative_to(ROOT)}")

    check('四面板截图落盘', shots)

    # ---------- 汇总 ----------
    total = len(_results)
    passed = sum(1 for _, ok, _ in _results if ok)
    print('-' * 60)
    if passed == total:
        print(f"verify_panel_layout: {passed}/{total} 全通过 ✅")
        print(f"截图目录：{OUT_DIR.relative_to(ROOT)}")
        return 0
    print(f"verify_panel_layout: {passed}/{total} 通过，{total - passed} 失败 ❌")
    for name, ok, err in _results:
        if not ok:
            print(f"  - {name}: {err}")
    return 1


if __name__ == '__main__':
    sys.exit(main())
