# -*- coding: utf-8 -*-
"""校验 Badge 前景色修复 + P07 卡片 hover 反馈。

断言清单：
  A1  Badge 6 种语义色的文字/背景 WCAG 对比度 ≥ 4.5:1
      （Badge 文字 FS_MICRO 11px 属 WCAG 小字，须达 AA 正文标准；大字 3:1 不够）
  A2  Badge 渲染后存在与背景显著差异的像素——证明文字真的被画出来，
      而非「前景色==背景色」导致同色隐藏（原 bug 的判据）
  A3  P07 QSS hover 静态：QFrame:hover 必须同时含 background 与 border-color
      （原实现只有 border-color，1px 边框变色在深色底几乎不可见）
  A4  P07 运行时：enter 切换为 CARD_HOVER 阴影、leave 还原，
      幂等短路（状态未变不改参数），以及 hover 前后渲染像素确实变化
      （Qt QSS 不支持 box-shadow，阴影只能在事件里用 QGraphicsDropShadowEffect 切）
  A5  P29 概率统计行 hover 阴影真切换：参数真的变（ROW → ROW_HOVER → ROW），
      且复用同一 effect 实例（不踩 Qt 换装删旧 effect 的悬空指针）

PDF 调色板校验（PDF_* 令牌值零变化 + PDF 生成冒烟）已拆到
scripts/verify_pdf_palette.py——它不依赖 PySide6，两个 python 环境都能跑。

离屏采样方法学（勿改）：grab().toImage() + 位运算取 RGB。
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def _rel_lum(hex_color):
    """WCAG 2.x 相对亮度（线性化 sRGB，ITU-R BT.709 权重）。"""
    def f(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    """WCAG 对比度比。"""
    la, lb = _rel_lum(a), _rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def rgb(px):
    return ((px >> 16) & 0xFF, (px >> 8) & 0xFF, px & 0xFF)


def main():
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
    from PySide6.QtCore import QEvent, QPoint, QPointF
    from PySide6.QtGui import QEnterEvent
    from ui.styles import Colors
    import ui.components.badge as badge_mod
    from ui.components.badge import Badge, _BADGE_COLORS
    import ui.components.collapsible_card as cc_mod
    from ui.components.collapsible_card import CollapsibleCard

    app = QApplication([])

    # ── A1 Badge 前景色对比度 ───────────────────────────────────
    fg_of = {
        'success': Colors.TEXT_INV, 'danger': Colors.TEXT,
        'warning': Colors.TEXT_INV, 'info': Colors.TEXT_INV,
        'brand': Colors.TEXT_INV, 'accent': Colors.TEXT,
    }
    for sem in ('success', 'danger', 'warning', 'info', 'brand', 'accent'):
        bg = _BADGE_COLORS[sem]
        fg = badge_mod._contrast_fg(bg)
        ratio = contrast(fg, bg)
        check(f'A1 Badge[{sem}] 对比度', ratio >= 4.5,
              f'{bg} on {fg} = {ratio:.2f}:1')
        # 同时校验「推导出的前景色」与「人工预期」一致，防止阈值漂移
        check(f'A1 Badge[{sem}] 前景色推导', fg == fg_of[sem], f'{fg} vs {fg_of[sem]}')

    # ── A2 Badge 文字真的被画出来（同色隐藏的判据）──────────────
    for sem in ('success', 'danger', 'warning', 'info', 'brand', 'accent'):
        b = Badge('吉', semantic=sem)
        b.adjustSize()
        b.setFixedWidth(max(b.sizeHint().width(), 44))
        b.setFixedHeight(24)
        b.show()
        app.processEvents()
        img = b.grab().toImage()
        bg = _BADGE_COLORS[sem]
        br, bgg, bb = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
        diff = 0
        for y in range(img.height()):
            for x in range(img.width()):
                r, g, bl = rgb(img.pixel(x, y))
                if (abs(r - br) + abs(g - bgg) + abs(bl - bb)) > 60:
                    diff += 1
        check(f'A2 Badge[{sem}] 文字像素可见', diff >= 30,
              f'{diff} 个与背景差异显著的像素')

    # ── A3 P07 QSS hover 静态 ──────────────────────────────────
    card = CollapsibleCard('测试卡片', icon='☯')
    qss = card.styleSheet()
    hover = re.search(r'QFrame:hover\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', qss)
    has_bg = bool(re.search(r'background\s*:', qss[qss.find('QFrame:hover'):], re.I))
    has_border = bool(re.search(r'border-color\s*:', qss[qss.find('QFrame:hover'):], re.I))
    check('A3 P07 hover 含 background', has_bg,
          '' if has_bg else '缺失 → 原实现只改 1px 边框，深色底上几乎不可见')
    check('A3 P07 hover 含 border-color', has_border, '')
    check('A3 P07 hover 块已解析', hover is not None, 'QFrame:hover 规则存在')

    # ── A4 P07 运行时阴影切换 ──────────────────────────────────
    # 事件构造的两个坑（PySide6 6.9 实测）：
    # ① QWidget::enterEvent 的参数是 QEnterEvent*，传裸 QEvent 抛 TypeError，
    #    故 Enter 必须构造真实 QEnterEvent(localPos, scenePos, globalPos)；
    # ② QLeaveEvent 未被 PySide6 导出（ImportError），但 leaveEvent 参数是普通
    #    QEvent*，故用 QEvent(Type.HoverLeave) 即可。
    # 每次调用都新建事件对象——QEvent 是一次性消费的。
    def enter_shadow():
        """直接触发 enterEvent（测阴影切换逻辑）。"""
        card.enterEvent(QEnterEvent(QPoint(5, 5), QPointF(5, 5), QPoint(5, 5)))
        app.processEvents()

    def leave_shadow():
        """直接触发 leaveEvent（测阴影还原逻辑）。"""
        card.leaveEvent(QEvent(QEvent.Type.HoverLeave))
        app.processEvents()

    def eff_sig():
        """当前阴影参数签名：(模糊半径, 偏移x, 偏移y, 主色hex, alpha)。

        不能用对象身份比较——setGraphicsEffect() 换入新 effect 时 Qt 会删除旧
        effect，卡片每次即时构造新实例，旧引用已悬空。
        """
        e = card.graphicsEffect()
        if e is None:
            return None
        c = e.color()
        return (e.blurRadius(), e.offset().x(), e.offset().y(),
                c.name().upper(), round(c.alphaF(), 2))

    card.show()
    app.processEvents()
    # offscreen 下 show() 后鼠标位置可能落在控件上触发自动 hover，
    # 故断言初始态前先显式归位，消除环境差异。
    leave_shadow()
    exp_base = (12.0, 0.0, 4.0, '#000000', 0.35)
    exp_hover = (16.0, 0.0, 6.0, '#C9A227', 0.25)
    s_base = eff_sig()
    check('A4 P07 初始为基础阴影', s_base == exp_base,
          f'实际 {s_base}，期望 {exp_base}')
    enter_shadow()
    s_hover = eff_sig()
    check('A4 P07 enter 切为 hover 阴影', s_hover == exp_hover,
          f'实际 {s_hover}，期望 {exp_hover}')
    leave_shadow()
    check('A4 P07 leave 还原基础阴影', eff_sig() == exp_base,
          f'实际 {eff_sig()}')
    # 幂等性：状态未变时不得重复 setGraphicsEffect（否则每次都新建 effect）
    before_id = id(card.graphicsEffect())
    leave_shadow()
    check('A4 P07 状态未变时不重建 effect', id(card.graphicsEffect()) == before_id,
          '幂等短路生效')

    # 渲染层验证：hover 前/后 grab 的像素分布必须变化（背景渐变 + 阴影）。
    # 这是「hover 反馈真的可见」的最终判据——QSS/事件都对但渲染无变化 = 无效。
    # 用全新卡片避免 hover 伪状态残留；阴影画在控件几何之外，直接 grab() 卡片
    # 会被裁掉，故嵌进带边距的父容器后抓父。
    card2 = CollapsibleCard('渲染验证卡片', icon='☯')
    card2.setMaximumHeight(220)
    pad = QWidget()
    _lay = QVBoxLayout(pad)
    _lay.setContentsMargins(60, 60, 60, 60)
    _lay.addWidget(card2)
    pad.resize(560, 340)
    pad.show()
    app.processEvents()
    before = pad.grab().toImage()
    app.sendEvent(card2, QEnterEvent(QPoint(5, 5), QPointF(5, 5), QPoint(5, 5)))
    app.processEvents()
    after = pad.grab().toImage()
    changed = 0
    for y in range(0, min(before.height(), after.height()), 2):
        for x in range(0, min(before.width(), after.width()), 2):
            if rgb(before.pixel(x, y)) != rgb(after.pixel(x, y)):
                changed += 1
    check('A4 P07 hover 后渲染确实变化', changed > 50,
          f'{changed} 个采样点变化（背景渐变 + 阴影）')

    # ── A5 P29 prob-row hover 阴影真切换 ────────────────────────
    # P29 根因：原实现是「两个 effect + setEnabled 切换」，而只有装在 widget 上
    # 的那个生效——对未安装的 highlight 调 setEnabled(True) 无渲染效果，实际表现是
    # 「hover 时阴影消失」而非「切换为强调阴影」（静默失效多年）。
    # 修复后改同一实例的参数，故断言重点放在：参数真的变 + 实例不换（无悬空指针）。
    from PySide6.QtWidgets import QFrame
    from ui.styles import Shadows
    import ui.components.collapsible_card as cc2
    stats_w = cc2.probability_stats_widget(['事业：82%', '财运：70%', '健康：90%'])
    stats_w.show()
    app.processEvents()
    rows = [f for f in stats_w.findChildren(QFrame) if f.objectName().startswith('prob-row-')]
    check('A5 P29 概率统计行已渲染', len(rows) >= 1, f'{len(rows)} 行')

    exp_row = (float(Shadows.ROW['radius']), float(Shadows.ROW['offset'][1]),
               Shadows.ROW['hex'].upper(), int(round(Shadows.ROW['alpha'] * 255)))
    exp_row_hover = (float(Shadows.ROW_HOVER['radius']), float(Shadows.ROW_HOVER['offset'][1]),
                     Shadows.ROW_HOVER['hex'].upper(),
                     int(round(Shadows.ROW_HOVER['alpha'] * 255)))

    def row_sig(f):
        """prob-row 阴影签名：(模糊半径, 偏移y, 主色hex, alpha 0~255)。"""
        e = f.graphicsEffect()
        if e is None:
            return None
        c = e.color()
        return (e.blurRadius(), e.offset().y(), c.name().upper(), c.alpha())

    for i, row in enumerate(rows):
        base = row_sig(row)
        check(f'A5 P29 第{i + 1}行初始为 ROW 阴影', base == exp_row,
              f'实际 {base}，期望 {exp_row}')
        eff_id = id(row.graphicsEffect())
        app.sendEvent(row, QEnterEvent(QPoint(5, 5), QPointF(5, 5), QPoint(5, 5)))
        app.processEvents()
        check(f'A5 P29 第{i + 1}行 hover 切为 ROW_HOVER', row_sig(row) == exp_row_hover,
              f'实际 {row_sig(row)}，期望 {exp_row_hover}')
        check(f'A5 P29 第{i + 1}行 hover 未换 effect 实例',
              id(row.graphicsEffect()) == eff_id,
              '同一实例改参数 → 不踩 Qt 删旧 effect 的悬空指针')
        app.sendEvent(row, QEvent(QEvent.Type.Leave))
        app.processEvents()
        check(f'A5 P29 第{i + 1}行 leave 还原 ROW', row_sig(row) == exp_row,
              f'实际 {row_sig(row)}')

    # ── A6 PDF 调色板已拆到独立脚本 ─────────────────────────────
    # PDF_* 令牌值校验与 PDF 生成冒烟不依赖 PySide6，拆到
    # verify_pdf_palette.py：venv（无 reportlab）与 anaconda（无 PySide6）
    # 各自都能跑到属于自己的那部分。
    print("\n[PROMPT] PDF 调色板校验请用 scripts/verify_pdf_palette.py（两个 python 环境均可）")

    # ── 汇总 ────────────────────────────────────────────────────
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{'=' * 62}")
    print(f"verify_badge_p07: {len(RESULTS) - len(failed)}/{len(RESULTS)} 通过")
    if failed:
        for name, _, detail in failed:
            print(f"  ✗ {name} — {detail}")
        return 1
    print("Badge 前景色 / P07 hover / P29 prob-row 阴影全部通过 ✅")
    return 0


if __name__ == '__main__':
    sys.exit(main())
