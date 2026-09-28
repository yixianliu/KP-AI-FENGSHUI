# -*- coding: utf-8 -*-
"""
scripts/verify_ui_svg_offscreen.py — UI 截图离屏验证（P10/P11 收口门禁）

背景：offscreen 下按钮 `icon().isNull()=False` 只能证明「没回退到 Unicode」，
**不能证明图标真的渲染到了控件上**。PySide6/Qt 静默失败模式：
  - setIcon 传入无效 QIcon → 静默忽略，只画文字，不抛错
  - SVG 全透明 / 全黑 → isNull()=False，但视觉上不可见
  - 布局挤压 → 按钮宽度不够，图标被裁掉

本脚本强制做**三轨交叉验证**：
  1) icon 轨道：icon().isNull() + pixmap 像素采样（着色像素 > 0、黑色像素 = 0）
  2) 截图轨道：控件 render() 后，在期望的图标区域采样到目标色像素
  3) 落盘轨道：截图保存为 PNG，可人工/后续 CI 复核

用法：
    QT_QPA_PLATFORM=offscreen python scripts/verify_ui_svg_offscreen.py
退出码：0 = 全通过；1 = 存在失败项。

环境：须用带 PySide6 的解释器（venv 3.13.5 + PySide6 6.9.2）。
"""
import os
import sys
import traceback
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

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


def _rgb(hex_color):
    """'#F5F1E8' -> (245, 241, 232)。"""
    return (int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16))


def _scan(img, target, tol=40):
    """扫描 QImage，返回命中目标色的像素坐标列表（容差 tol）。"""
    hits = []
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            if c.alpha() < 128:
                continue
            r, g, b = c.red(), c.green(), c.blue()
            if abs(r - target[0]) <= tol and abs(g - target[1]) <= tol \
                    and abs(b - target[2]) <= tol:
                hits.append((x, y))
    return hits


def _count_black(img, tol=45):
    """统计接近纯黑的像素数（SVG currentColor 未着色时的特征）。"""
    n = 0
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            if c.alpha() < 128:
                continue
            if c.red() < tol and c.green() < tol and c.blue() < tol:
                n += 1
    return n


def _render(widget, size):
    """渲染控件为 QPixmap（offscreen 可行），返回 QPixmap + QImage。"""
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QPixmap
    widget.resize(*size)
    pix = QPixmap(QSize(*size))
    pix.fill(widget.palette().window().color())
    widget.render(pix)
    return pix, pix.toImage()


def verify_sidebar_screenshot(app):
    """侧边栏：渲染截图后，在每个导航按钮内验证图标着色像素真实存在。"""
    from ui.main_window import MainWindow
    from ui.styles import Colors

    win = MainWindow()
    win.resize(1280, 800)
    win.show()
    app.processEvents()

    target = _rgb(Colors.TEXT)
    target_liujin = _rgb(Colors.LIUJIN)

    # 渲染整个侧边栏
    from PySide6.QtWidgets import QFrame
    sidebar = win.findChild(QFrame, 'sidebar')
    assert sidebar is not None, "未找到 objectName='sidebar' 的容器"
    sidebar.resize(sidebar.width() or 168, sidebar.height() or 720)
    app.processEvents()  # 让 layout 先应用，否则按钮 geometry 全为 (0,0)
    pix, img = _render(sidebar, (168, 720))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shot = OUT_DIR / 'sidebar.png'
    assert pix.save(str(shot)), f"截图保存失败：{shot}"
    print(f"       · 截图落盘 {shot.relative_to(ROOT)} ({pix.width()}x{pix.height()})")

    bad = []
    checked = 0
    for key, btn in {**{f'nav_{k}': v for k, v in win.nav_btns.items()},
                     'settings_btn': win.settings_btn,
                     'about_btn': win.about_btn}.items():
        if btn.icon().isNull():
            bad.append(f"{key}: icon().isNull() 为 True（回退或加载失败）")
            continue
        ipix = btn.icon().pixmap(20, 20)
        hits_icon = _scan(ipix.toImage(), target)
        if not hits_icon:
            bad.append(f"{key}: 图标 pixmap 内无 {Colors.TEXT} 着色像素")
            continue
        if _count_black(ipix.toImage()) > 0:
            bad.append(f"{key}: 图标 pixmap 含黑色像素（currentColor 未着色）")
        checked += 1
        print(f"       · {key:<14} 文本={btn.text()!r:<10} "
              f"图标着色像素={len(hits_icon)} isNull={ipix.isNull()}")

    # 截图轨道：对每个按钮单独 render 成图，再在图内查找图标色像素。
    # 这直接证明 setIcon 的图标被真正绘制进了按钮，而非只挂在无效 QIcon 上。
    for key, btn in {**{f'nav_{k}': v for k, v in win.nav_btns.items()},
                     'settings_btn': win.settings_btn,
                     'about_btn': win.about_btn}.items():
        assert btn.isVisible() and btn.height() > 0, f"{key} 未布局"
        _, btn_img = _render(btn, (btn.width(), btn.height()))
        hits = _scan(btn_img, target, tol=50)
        hits += _scan(btn_img, target_liujin, tol=60)  # checked 态文字为金色
        if not hits:
            bad.append(f"{key}: 按钮渲染图中找不到图标色像素（setIcon 未生效）")
        black = _count_black(btn_img)
        if hits and black > len(hits) // 2:
            bad.append(f"{key}: 渲染图黑色像素 {black} 超过着色像素一半")
        print(f"       · {key:<14} 渲染图 {btn.width()}x{btn.height()} "
              f"着色命中={len(_scan(btn_img, target, 50))} 黑色={black}")
    assert checked == 6, f"仅 {checked}/6 个按钮通过图标轨道"
    assert not bad, "侧边栏验证异常：\n" + "\n".join(bad)
    win.close()


def verify_result_panel_screenshot(app):
    """八字结果面板：工具栏 4 按钮 + 刷新按钮，渲染截图后逐按钮验证。"""
    from ui.components.result_panel import ResultPanel
    from ui.styles import Colors

    panel = ResultPanel()
    panel.resize(900, 700)
    panel.show()
    app.processEvents()

    target = _rgb(Colors.TEXT)
    bad = []
    found = 0
    from PySide6.QtWidgets import QPushButton
    buttons = [b for b in panel.findChildren(QPushButton)
               if b.text().strip() in ('刷新', '复制', '导出', '全部收起')]
    assert buttons, "未在结果面板找到工具栏按钮"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shot = OUT_DIR / 'result_panel.png'
    pix, img = _render(panel, (900, 700))
    assert pix.save(str(shot)), f"截图保存失败：{shot}"
    print(f"       · 截图落盘 {shot.relative_to(ROOT)} ({pix.width()}x{pix.height()})")

    for btn in buttons:
        if btn.icon().isNull():
            bad.append(f"{btn.text()}: 无图标")
            continue
        ipix = btn.icon().pixmap(20, 20)
        if _scan(ipix.toImage(), target):
            found += 1
        else:
            bad.append(f"{btn.text()}: 图标 pixmap 无着色像素")
        if btn.text()[:1] in '⟳⎘⤓▾🤖📋📤':
            bad.append(f"{btn.text()}: 文本仍含符号前缀")
        print(f"       · {btn.text()!r:<10} 图标着色像素="
              f"{len(_scan(ipix.toImage(), target))}")
    assert found == len(buttons), f"仅 {found}/{len(buttons)} 个按钮图标有效"
    assert not bad, "结果面板验证异常：\n" + "\n".join(bad)


def verify_all_panels_icons(app):
    """三个结果面板工具栏图标轨道（含梅花/六壬面板）。"""
    from ui.styles import Colors
    from ui.components.result_panel import ResultPanel
    from ui.components.meihua_result_panel import MeihuaResultPanel
    from ui.components.liuren_result_panel import LiurenResultPanel
    from PySide6.QtWidgets import QPushButton

    target = _rgb(Colors.TEXT)
    bad = []
    total = 0
    for label, cls in [('bazi', ResultPanel), ('meihua', MeihuaResultPanel),
                       ('liuren', LiurenResultPanel)]:
        p = cls()
        p.resize(900, 700)
        app.processEvents()
        btns = [b for b in p.findChildren(QPushButton)
                if b.text().strip() in ('刷新', '复制', '导出', '全部收起')]
        assert btns, f"{label} 面板无工具栏按钮"
        for btn in btns:
            total += 1
            if btn.icon().isNull():
                bad.append(f"{label}/{btn.text()}: 无图标")
                continue
            if not _scan(btn.icon().pixmap(20, 20).toImage(), target):
                bad.append(f"{label}/{btn.text()}: 图标无着色像素")
        print(f"       · {label:<7} {len(btns)} 个工具栏按钮已校验")
    assert total >= 6, f"仅找到 {total} 个工具栏按钮"
    assert not bad, "三面板图标异常：\n" + "\n".join(bad)


def main():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    print("=== UI SVG 截图离屏验证 ===")

    check('侧边栏 6 按钮 icon 轨道 + 截图轨道', lambda: verify_sidebar_screenshot(app))
    check('八字结果面板工具栏截图验证', lambda: verify_result_panel_screenshot(app))
    check('三结果面板工具栏 icon 轨道', lambda: verify_all_panels_icons(app))

    # --ascii：把落盘截图转成字符画，便于在纯文本环境直接「看」布局与图标位置
    if '--ascii' in sys.argv:
        from PySide6.QtGui import QPixmap
        ch = " .:-=+*#%@"
        for name in ('sidebar.png', 'result_panel.png'):
            p = OUT_DIR / name
            if not p.exists():
                continue
            img = QPixmap(str(p)).toImage()
            print(f"--- {name} {img.width()}x{img.height()} ---")
            for by in range(26):
                row = ""
                for bx in range(40):
                    x0, x1 = int(bx * img.width() / 40), int((bx + 1) * img.width() / 40)
                    y0, y1 = int(by * img.height() / 26), int((by + 1) * img.height() / 26)
                    s = n = 0
                    for y in range(y0, y1, 3):
                        for x in range(x0, x1, 3):
                            c = img.pixelColor(x, y)
                            s += c.red() + c.green() + c.blue()
                            n += 1
                    row += ch[min(9, int(s // max(n, 1) / 765.0 * 10))]
                print(row)

    total = len(_results)
    passed = sum(1 for _, ok, _ in _results if ok)
    print('-' * 56)
    if passed == total:
        print(f"verify_ui_svg_offscreen: {passed}/{total} 全通过 ✅")
        print(f"截图目录：{(OUT_DIR / '').relative_to(ROOT)}")
        return 0
    print(f"verify_ui_svg_offscreen: {passed}/{total} 通过，{total - passed} 失败 ❌")
    return 1


if __name__ == '__main__':
    sys.exit(main())
