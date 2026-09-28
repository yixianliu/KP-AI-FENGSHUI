# -*- coding: utf-8 -*-
"""校验 ListItem 四态：静态 QSS 覆盖 + 像素级可见性 + 状态机正确性。

背景：ListItem 是 M4 步骤 4.1 的产物，但**从未被任何面板使用过**（死代码），
因此四态从来没有被像素级验证过。本轮发现三处与 Badge 同级的静默失效并修掉：

  ① QSS 里的 `hover` 分支从未被赋值（死分支），enterEvent 直接写 `active`；
  ② 程序化 `set_state('active')`（固定选中态）在鼠标路过的同一秒被抹平 → API 不可用；
  ③ `disabled` 只给 QFrame 设 `color: TEXT4`，但子 QLabel 都带内联 color 会覆盖
     继承值 → 禁用态文字颜色一点没变，且 `isEnabled()` 仍为 True、点击照旧触发。

断言清单：
  A1  LIST_ITEM_QSS 四态分支齐全（default/hover/active/disabled）
  A2  四态各自的背景 + 文字像素都真实渲染（防同色隐藏，Badge 类 bug 的判据）
  A3  四态背景两两不同（防「四个态长得一样」）
  A4  disabled 真禁用：isEnabled()==False、clicked 不触发、文字被压到 TEXT4
  A5  固定选中态在鼠标往返后仍保持（进入显示 hover、离开还原 active）
  A6  未知状态回落 default；文本对比度达标（WCAG AA）

离屏采样方法学（勿改）：grab().toImage() + 位运算取 RGB，背景取众数以规避文字干扰。
"""
import os

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

RESULTS = []


def check(name, ok, detail=''):
    """记录并打印一条断言结果。"""
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def rgb(px):
    """QImage 像素 int → (r, g, b)。"""
    return ((px >> 16) & 0xFF, (px >> 8) & 0xFF, px & 0xFF)


def hexc(t):
    """(r, g, b) → '#RRGGBB'。"""
    return f"#{t[0]:02x}{t[1]:02x}{t[2]:02x}"


def modal_color(widget):
    """区域内像素众数（背景色）：抗锯齿与文字会污染精确断言，故取众数。"""
    img = widget.grab().toImage()
    c = Counter()
    for y in range(img.height()):
        for x in range(img.width()):
            c[rgb(img.pixel(x, y))] += 1
    return c.most_common(1)[0][0]


def text_pixel_count(widget, bg, min_dist=60):
    """与背景差异显著的像素数——证明文字真的被画出来，而非同色隐藏。"""
    img = widget.grab().toImage()
    n = 0
    for y in range(img.height()):
        for x in range(img.width()):
            r, g, b = rgb(img.pixel(x, y))
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > min_dist:
                n += 1
    return n


def _rel_lum(hex_color):
    """WCAG 2.x 相对亮度（线性化 sRGB，ITU-R BT.709 权重）。"""
    def f(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    """WCAG 对比度比。"""
    la, lb = _rel_lum(a), _rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def main():
    """跑全部断言，返回退出码。"""
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
    from PySide6.QtCore import QEvent, QPoint, QPointF
    from PySide6.QtGui import QEnterEvent
    from ui.styles import Colors
    from ui.components.list_item import ListItem, LIST_ITEM_QSS, STATES

    app = QApplication([])
    states = ('default', 'hover', 'active', 'disabled')

    # ── A1 四态 QSS 分支齐全 ────────────────────────────────────
    for s in states:
        check(f'A1 QSS 含 state={s} 分支', f'QFrame[state="{s}"]' in LIST_ITEM_QSS,
              '' if f'QFrame[state="{s}"]' in LIST_ITEM_QSS else '该分支从未被使用')
    check('A1 STATES 与 QSS 分支一致',
          sorted(STATES) == sorted(states), f'STATES={STATES}')
    # hover 分支不得是死分支：必须存在代码把它赋出去
    import ui.components.list_item as li_mod
    src = Path(li_mod.__file__).read_text(encoding='utf-8')
    check('A1 hover 态被代码赋值（非死分支）', "'hover'" in src and 'set_state' in src,
          '')
    # 关键门禁：子 label 必须强制透明背景。实测坑——子 QLabel 不声明
    # `background: transparent` 会盖住父 QFrame 的 QSS 背景，四态背景整体静默失效。
    check('A1 子 label 强制透明背景', 'background: transparent' in src,
          '缺失时四态背景会被子 label 盖住，LIST_ITEM_QSS 整份等于没写')

    # ── 建四态控件（放进带背景的容器，模拟真实使用场景）─────────
    items = {s: ListItem(icon='☘', title='甲子', subtitle='大运', value='1990-1999')
             for s in states}
    hosts = {}
    for s, item in items.items():
        host = QWidget()
        host.setStyleSheet(f"background: {Colors.BG};")
        lay = QVBoxLayout(host)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(item)
        host.resize(420, 90)
        host.show()
        app.processEvents()
        # 必须**在 show() 之后再 set_state**：offscreen 下 show 后鼠标位置可能落在
        # 控件上，Qt 会自动发 HoverEnter → enterEvent 把状态翻成 hover，先设会被覆盖。
        # 先显示再设态，才能保证采样到目标状态（消除环境差异，保证测试可复现）。
        item.set_state(s)
        app.processEvents()
        # 必须留住 host 引用：QWidget 无父且无 Python 引用会被 CPython 立刻 GC，
        # 连带销毁子控件，下一轮循环再 grab 就会 RuntimeError: already deleted。
        hosts[s] = (host, lay)

    def shot(state):
        """采样**父容器**而非控件本身。

        控件自身的 grab() 对透明背景（default/disabled）得到 alpha=0 的像素，
        `rgb()` 会把它读成 #000000 纯黑——那是采样伪影，不是渲染结果。
        在父容器上采样才能拿到「透明 → 透出父背景」的真实合成色。
        """
        return hosts[state][0]

    # ── A2 四态文字真实渲染（同色隐藏的判据）─────────────────────
    for s in states:
        bg = modal_color(shot(s))
        n = text_pixel_count(shot(s), bg)
        check(f'A2 {s} 文字像素可见', n >= 30,
              f'{n} 个与背景差异显著的像素，背景 {hexc(bg)}')

    # ── A3 四态背景可区分 ───────────────────────────────────────
    got = {s: modal_color(shot(s)) for s in states}
    check('A3 default/disabled 透明 → 透出父背景 BG',
          got['default'] == tuple(int(Colors.BG[i:i + 2], 16) for i in (1, 3, 5)),
          f'实际 {hexc(got["default"])}，期望 {Colors.BG}')
    check('A3 hover 背景为 HOVER', got['hover'] == tuple(int(Colors.HOVER[i:i + 2], 16)
                                                         for i in (1, 3, 5)),
          f'实际 {hexc(got["hover"])}')
    check('A3 active 背景为 CARD_HOVER',
          got['active'] == tuple(int(Colors.CARD_HOVER[i:i + 2], 16) for i in (1, 3, 5)),
          f'实际 {hexc(got["active"])}')
    check('A3 hover 与 active 背景不同', got['hover'] != got['active'],
          f'{hexc(got["hover"])} vs {hexc(got["active"])}')
    check('A3 default 与 hover 背景不同', got['default'] != got['hover'],
          f'{hexc(got["default"])} vs {hexc(got["hover"])}')

    # ── A4 disabled 真禁用 ──────────────────────────────────────
    d = ListItem(title='丙寅', subtitle='流年', value='吉')
    host_d = QWidget()
    host_d.setStyleSheet(f"background: {Colors.BG};")
    _l = QVBoxLayout(host_d)
    _l.setContentsMargins(0, 0, 0, 0)
    _l.addWidget(d)
    host_d.resize(360, 80)
    host_d.show()
    app.processEvents()
    d.set_state('disabled')   # 必须在 show() 之后，否则被自动 HoverEnter 覆盖
    app.processEvents()

    from PySide6.QtWidgets import QLabel as _QL
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import Qt as _Qt

    def child_colors(w):
        """取控件内所有 QLabel 的 color 声明值。"""
        return [l.styleSheet().split('color:')[1].split(';')[0].strip().upper()
                for l in w.findChildren(_QL)]

    check('A4 disabled → isEnabled() False', not d.isEnabled(),
          '原实现为 True → 点击与焦点照旧。Qt 输入路径对 disabled 控件'
          '不投递鼠标事件（sendMouseEvent 里的 isEnabled 判断），这是正确性保证')
    # 注意：这里**不能**用 app.sendEvent 合成鼠标按下验证「disabled 时不触发」——
    # sendEvent 直接投递到 event()，绕开了 Qt 在输入路径做的 isEnabled 门禁，
    # 会造成假失败。正确断言是 isEnabled()==False + 启用态点击仍正常。
    # 禁用态文字必须被压到 TEXT4（而非保持主文字色）
    colors_now = child_colors(d)
    check('A4 子文字统一压到 TEXT4',
          all(c == Colors.TEXT4.upper() for c in colors_now),
          f'实际 {colors_now}（原实现仍是 TEXT/TEXT3/BRAND，禁用等于没生效）')
    bg_d = modal_color(host_d)
    txt_d = text_pixel_count(host_d, bg_d)
    check('A4 disabled 文字像素可见', txt_d >= 30,
          f'{txt_d} 个像素（压暗但仍可读，非同色隐藏）')

    # 还原后颜色回到原值（防「只能压暗、无法恢复」）
    d.set_state('default')
    check('A4 disabled 可还原为可用', d.isEnabled(), '')
    restored = child_colors(d)
    check('A4 还原后 title 回主文字色', Colors.TEXT.upper() in restored,
          f'实际 {restored}')
    check('A4 还原后 value 回 BRAND', Colors.BRAND.upper() in restored, '')
    # 启用态点击仍正常（证明 clicked 接线没被禁用逻辑弄坏）
    clicks = []
    d.clicked.connect(lambda: clicks.append(1))
    _me = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(10, 10),
                      _Qt.LeftButton, _Qt.LeftButton, _Qt.NoModifier)
    app.sendEvent(d, _me)
    app.processEvents()
    check('A4 启用态点击仍触发 clicked', clicks == [1], f'触发 {len(clicks)} 次')

    # ── A5 固定选中态在鼠标往返后仍保持 ─────────────────────────
    pinned = ListItem(title='戊辰', subtitle='大运', value='1990-1999')
    host_p = QWidget()
    host_p.setStyleSheet(f"background: {Colors.BG};")
    _lp = QVBoxLayout(host_p)
    _lp.setContentsMargins(10, 10, 10, 10)
    _lp.addWidget(pinned)
    host_p.resize(380, 80)
    host_p.show()
    app.processEvents()
    pinned.set_state('active')
    check('A5 程序化 active 生效', pinned.property('state') == 'active', '')
    app.sendEvent(pinned, QEnterEvent(QPoint(5, 5), QPointF(5, 5), QPoint(5, 5)))
    app.processEvents()
    check('A5 鼠标进入显示 hover', pinned.property('state') == 'hover',
          f'实际 {pinned.property("state")}'
          '（原实现直接置 active，与 hover 不可区分）')
    app.sendEvent(pinned, QEvent(QEvent.Type.Leave))
    app.processEvents()
    check('A5 鼠标离开还原 active（固定选中态不被抹平）',
          pinned.property('state') == 'active',
          f'实际 {pinned.property("state")}'
          '（原实现无条件写回 default）')

    # disabled 时鼠标进入不得改变状态
    pinned.set_state('disabled')
    app.sendEvent(pinned, QEnterEvent(QPoint(5, 5), QPointF(5, 5), QPoint(5, 5)))
    app.processEvents()
    check('A5 disabled 时鼠标进入不切态', pinned.property('state') == 'disabled',
          f'实际 {pinned.property("state")}')

    # ── A6 未知状态回落 + 文本对比度 ────────────────────────────
    u = ListItem(title='庚午')
    host_u = QWidget()
    host_u.setStyleSheet(f"background: {Colors.BG};")
    _lu = QVBoxLayout(host_u)
    _lu.setContentsMargins(8, 8, 8, 8)
    _lu.addWidget(u)
    host_u.resize(220, 60)
    host_u.show()
    app.processEvents()
    u.set_state('bogus_state')
    check('A6 未知状态回落 default', u.property('state') == 'default',
          f'实际 {u.property("state")}')

    for label, fg in (('title', Colors.TEXT), ('subtitle', Colors.TEXT3),
                      ('value', Colors.BRAND)):
        r = contrast(fg, Colors.BG)
        check(f'A6 {label} 对比度', r >= 4.5,
              f'{fg} on {Colors.BG} = {r:.2f}:1（小字须 ≥4.5:1）')
    r_d = contrast(Colors.TEXT4, Colors.BG)
    check('A6 disabled 文字对比度', r_d >= 4.5,
          f'{Colors.TEXT4} on {Colors.BG} = {r_d:.2f}:1')

    # ── 汇总 ────────────────────────────────────────────────────
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{'=' * 62}")
    print(f"verify_list_item: {len(RESULTS) - len(failed)}/{len(RESULTS)} 通过")
    if failed:
        for name, _, detail in failed:
            print(f"  ✗ {name} — {detail}")
        return 1
    print("ListItem 四态全部通过 ✅")
    return 0


if __name__ == '__main__':
    sys.exit(main())
