# -*- coding: utf-8 -*-
"""
scripts/verify_icons_svg.py — SVG 图标渲染真实性验证

背景：QPixmap 直接加载 SVG 时 currentColor 渲染为纯黑（深色底完全不可见），
仅检查 isNull() 会误判「加载成功」。本脚本强制做**像素采样**，确认图标：
  1) 文件存在且可被 icons.icon() 渲染为非空 pixmap；
  2) 采样像素存在「非黑、非透明」的着色笔画（证明 currentColor 着色生效）；
  3) 侧边栏 6 个功能按钮已 SVG 化（无 Unicode 前缀 + 图标可渲染 + 采样非黑）。

用法：
    python scripts/verify_icons_svg.py
退出码：0 = 全通过；1 = 存在失败项。
"""
import os
import sys
import traceback

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 图标主色（与 icons._DEFAULT_ICON_COLOR 一致），容差 ±60 以覆盖抗锯齿边缘
_TARGET = (0xF5, 0xF1, 0xE8)
_TOLERANCE = 60

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
        traceback.print_exc(limit=3)


def _sample(pix, target=None, tol=None):
    """遍历 pixmap 像素，返回 (着色像素数, 黑色像素数, 非透明像素数)。

    Args:
        pix:    待采样 QPixmap。
        target: 目标色 (R,G,B) 三元组，默认取 Colors.TEXT 解析值。
        tol:    色相容差（覆盖抗锯齿边缘），默认 60。
    """
    from PySide6.QtGui import QImage
    target = target or _TARGET
    tol = tol if tol is not None else _TOLERANCE
    img = pix.toImage()
    colored = black = opaque = 0
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            if c.alpha() == 0:
                continue
            opaque += 1
            r, g, b = c.red(), c.green(), c.blue()
            if r < 40 and g < 40 and b < 40:
                black += 1
            if abs(r - target[0]) <= tol and abs(g - target[1]) <= tol \
                    and abs(b - target[2]) <= tol:
                colored += 1
    return colored, black, opaque


def _first_opaque_color(pix):
    """返回 alpha 最大的像素颜色（避开抗锯齿边缘的半透明混合像素）。"""
    img = pix.toImage()
    best = None
    best_a = -1
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            if c.alpha() > best_a:
                best_a = c.alpha()
                best = c
    return best


def verify_all_icons(app):
    """全部 SVG 图标：非空 + 有真实着色笔画（排除纯黑 / 纯透明）。"""
    from pathlib import Path
    from ui.components.icons import icon, has_icon
    from ui.styles import Colors

    global _TARGET
    text_rgb = (int(Colors.TEXT[1:3], 16), int(Colors.TEXT[3:5], 16),
                int(Colors.TEXT[5:7], 16))
    _TARGET = text_rgb  # 图标默认色必须跟随设计令牌，避免双源漂移

    root = Path(__file__).resolve().parent.parent / 'assets' / 'icons'
    names = sorted(p.stem for p in root.glob('*.svg'))
    assert names, f"未找到任何 SVG 图标：{root}"

    bad = []
    for name in names:
        assert has_icon(name), f"{name}.svg 未通过 has_icon"
        ic = icon(name, size=24)
        pix = ic.pixmap(24, 24)
        if pix.isNull():
            bad.append(f"{name}: pixmap 为空")
            continue
        colored, black, opaque = _sample(pix)
        if opaque == 0:
            bad.append(f"{name}: 全透明（未渲染任何笔画）")
        elif black == opaque:
            bad.append(f"{name}: 全部 {opaque} 个像素为黑色（currentColor 未着色）")
        elif colored == 0:
            bad.append(f"{name}: 无目标色像素（着色异常，black={black}/{opaque}）")
        else:
            print(f"       · {name:<14} 着色像素 {colored:>4}/{opaque} 黑色 {black}")
    assert not bad, "图标渲染异常：\n" + "\n".join(bad)


def verify_cache_colorization(app):
    """显式着色必须生效（不同色值产出不同像素）。"""
    from ui.components.icons import icon
    a = icon('copy', 24, '#F5F1E8').pixmap(24, 24)
    b = icon('copy', 24, '#C9A227').pixmap(24, 24)
    assert not a.isNull() and not b.isNull()
    gold = (0xC9, 0xA2, 0x27)
    ca, _, _ = _sample(a, _TARGET)
    cb, _, _ = _sample(b, gold)
    assert ca > 0, "浅色图标无着色像素"
    assert cb > 0, "金色图标无着色像素（缓存串色或着色失效）"

    # 缓存必须按 color 区分：取首个不透明像素比对实际色值
    ga = _first_opaque_color(a)
    gb = _first_opaque_color(b)
    assert ga is not None and gb is not None, "着色图标无实心像素"
    # alpha 最大者即抗锯齿前的纯色笔画
    assert gb.alpha() > 200 and ga.alpha() > 200, \
        f"实心像素 alpha 偏低 ga={ga.alpha()} gb={gb.alpha()}"
    assert ga != gb, "两种色值产出同一像素（缓存未按 color 区分）"
    assert abs(ga.red() - _TARGET[0]) <= _TOLERANCE, f"浅色采样偏离 {ga.red()}"
    assert abs(gb.red() - gold[0]) <= _TOLERANCE, f"金色采样偏离 {gb.red()}"


def verify_sidebar(app):
    """侧边栏 6 个功能按钮：纯文字 + SVG 图标 + 采样非黑。"""
    from ui.main_window import MainWindow

    win = MainWindow()
    btns = {f'nav_{k}': v for k, v in win.nav_btns.items()}
    btns['settings_btn'] = win.settings_btn
    btns['about_btn'] = win.about_btn
    assert len(btns) == 6, f"侧边栏按钮数异常：{list(btns)}"

    bad = []
    for key, btn in btns.items():
        text = btn.text()
        ic = btn.icon()
        if not ic:
            bad.append(f"{key}: 未设置图标")
            continue
        pix = ic.pixmap(20, 20)
        if pix.isNull():
            bad.append(f"{key}: 图标 pixmap 为空")
            continue
        colored, black, opaque = _sample(pix)
        if opaque == 0:
            bad.append(f"{key}: 图标全透明")
        if black == opaque:
            bad.append(f"{key}: 图标全黑（深色底不可见）")
        if colored == 0:
            bad.append(f"{key}: 图标无目标色像素")
        if text.strip() == '' or len(text) > 6:
            bad.append(f"{key}: 文本异常 {text!r}")
        print(f"       · {key:<14} text={text!r:<10} 着色 {colored:>4}/{opaque} 黑色 {black}")

    assert not bad, "侧边栏图标异常：\n" + "\n".join(bad)
    win.close()


def main():
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication(sys.argv)
    print("=== SVG 图标渲染真实性验证 ===")

    check('全部 SVG 图标着色渲染（像素采样）', lambda: verify_all_icons(None))
    check('显式着色生效（浅色 vs 金色）', lambda: verify_cache_colorization(None))
    check('侧边栏 6 按钮 SVG 化', lambda: verify_sidebar(None))

    total = len(_results)
    passed = sum(1 for _, ok, _ in _results if ok)
    print('-' * 52)
    if passed == total:
        print(f"verify_icons_svg: {passed}/{total} 全通过 ✅")
        return 0
    print(f"verify_icons_svg: {passed}/{total} 通过，{total - passed} 失败 ❌")
    return 1


if __name__ == '__main__':
    sys.exit(main())
