# -*- coding: utf-8 -*-
"""
scripts/verify_keyboard_focus.py — 键盘焦点与可访问性验证（P17）

背景
----
项目原有 3 处焦点环声明用了 `outline`，但 Qt QSS **不支持** outline 属性
（见 scripts/probe_qss_outline.py 的决定性实测：贴边金色像素 0 vs border 624），
因此键盘 Tab 到任何按钮都**没有任何视觉反馈**，违反 WCAG 2.4.7「焦点可见」。

检查项
------
V1  静态：styles.py 每个 QPushButton 样式块都必须含 :focus 规则
V2  静态：全 UI 目录无有效的 `outline:` 属性声明（Qt 静默忽略，写了等于没写）
V3  动态：项目实际 FOCUS_BORDER 在真实聚焦态下渲染出古金像素（决定性验证）
V4  动态：Tab 键可遍历输入控件，且焦点在控件间真实移动
V5  可访问性：IconButton 等图标按钮 100% 具备 accessibleName
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent, QImage
from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / 'ui'

BRAND_R, BRAND_G, BRAND_B = 0xC9, 0xA2, 0x27
TOL = 40
PASS, FAIL = [], []


def _rgb(px: int) -> tuple[int, int, int]:
    return (px >> 16) & 0xFF, (px >> 8) & 0xFF, px & 0xFF


def golden_pixels(img: QImage, band: int = 4) -> int:
    """统计贴边环形带内的古金像素（避开中心文字）。"""
    w, h = img.width(), img.height()
    n = 0
    for y in range(h):
        for x in range(w):
            if not (x < band or y < band or x >= w - band or y >= h - band):
                continue
            p = img.pixel(x, y)
            if (p >> 24) & 0xFF < 200:
                continue
            r, g, b = _rgb(p)
            if abs(r - BRAND_R) <= TOL and abs(g - BRAND_G) <= TOL \
                    and abs(b - BRAND_B) <= TOL:
                n += 1
    return n


def check(name: str, ok: bool, detail: str = '') -> None:
    (PASS if ok else FAIL).append(name)
    mark = 'OK  ' if ok else 'FAIL'
    print(f'  [{mark}] {name}' + (f'  · {detail}' if detail else ''))


def check_focus_block(name: str, qss: str, app: QApplication) -> None:
    """把 QSS 套到按钮上，真实聚焦/失焦各渲染一次，断言焦点态出现古金环。"""
    btn = QPushButton('测试')
    btn.setStyleSheet(qss)
    btn.setFixedSize(140, 44)
    btn.setFocusPolicy(Qt.StrongFocus)
    btn.show()
    app.processEvents()
    btn.setFocus()
    app.processEvents()
    focused = golden_pixels(btn.grab().toImage())
    btn.clearFocus()
    app.processEvents()
    blurred = golden_pixels(btn.grab().toImage())
    btn.deleteLater()
    check(name, focused > 50 and focused > blurred,
          f'聚焦态 {focused} 金色像素 vs 失焦态 {blurred}')


def v1_focus_rule_coverage() -> None:
    """V1：styles.py 每个含 QPushButton 的样式块都必须声明 :focus。"""
    src = (ROOT / 'ui' / 'styles.py').read_text(encoding='utf-8')
    # 按三引号切块，逐块检查
    blocks = re.findall(r'"""(.*?)"""', src, flags=re.S)
    targets = [b for b in blocks if 'QPushButton' in b]
    missing = [i for i, b in enumerate(targets) if ':focus' not in b]
    check('V1 QPushButton 块 100% 声明 :focus',
          bool(targets) and not missing,
          f'{len(targets)} 个按钮块，缺焦点态 {len(missing)} 个')


def v2_no_outline_attr() -> None:
    """V2：全 UI 无无效 QSS 语法（Qt 会静默忽略，写了等于没写）。

    ① `outline:` 属性 —— Qt QSS 不支持，焦点环必须用 border
    ② `:not(` 复合伪状态 —— Qt QSS 不支持，`:focus:not(:disabled)` 整条规则失效
    """
    outline_hits, not_hits = [], []
    for f in sorted(UI_DIR.rglob('*.py')):
        for i, line in enumerate(
                f.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
            s = line.lstrip()
            if s.startswith('#') or s.startswith('/*'):
                continue  # 注释行（含说明性提及 outline）
            if re.match(r'outline\s*:', s):
                outline_hits.append(f'{f.relative_to(ROOT)}:{i}')
            if ':not(' in line:
                not_hits.append(f'{f.relative_to(ROOT)}:{i}')
    check('V2.1 无 outline 属性声明', not outline_hits,
          f'残留 {len(outline_hits)} 处: {outline_hits[:3]}')
    check('V2.2 无 :not() 复合伪状态', not not_hits,
          f'残留 {len(not_hits)} 处: {not_hits[:3]}')


def v3_focus_ring_renders() -> None:
    """V3：项目真实焦点声明在聚焦态渲染出古金环（决定性验证）。"""
    from ui.styles import FOCUS_BORDER, Colors
    check('V3.0 FOCUS_BORDER 令牌存在', 'solid' in FOCUS_BORDER and Colors.BRAND in FOCUS_BORDER,
          FOCUS_BORDER)
    qss_primary = f"""
        QPushButton {{
            background-color: {Colors.ZHUSHA};
            color: {Colors.TEXT_INV};
            border: none;
            padding: 10px 28px;
            min-height: 40px;
        }}
        QPushButton:focus {{
            border: {FOCUS_BORDER};
        }}
    """
    check_focus_block('V3.1 主按钮焦点环真实渲染', qss_primary,
                      app())
    qss_input = f"""
        QLineEdit {{
            background: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            padding: 6px 12px;
        }}
        QLineEdit:focus {{
            border: {FOCUS_BORDER};
        }}
    """
    edit = QLineEdit()
    edit.setStyleSheet(qss_input)
    edit.setFixedSize(200, 36)
    edit.show()
    app().processEvents()
    edit.setFocus()
    app().processEvents()
    fn = golden_pixels(edit.grab().toImage())
    edit.clearFocus()
    app().processEvents()
    bn = golden_pixels(edit.grab().toImage())
    edit.deleteLater()
    check('V3.2 输入框焦点环真实渲染', fn > 50 and fn > bn,
          f'聚焦态 {fn} vs 失焦态 {bn}')


def v4_tab_traversal() -> None:
    """V4：Tab 键可遍历控件，焦点真实移动且逐个可见。"""
    from PySide6.QtWidgets import QVBoxLayout, QWidget
    from ui.styles import Stylesheets
    form = QWidget()
    lay = QVBoxLayout(form)
    b1 = QPushButton('主操作'); b1.setStyleSheet(Stylesheets.BTN_PRIMARY)
    ed = QLineEdit(); ed.setStyleSheet(Stylesheets.INPUT)
    b2 = QPushButton('次操作'); b2.setStyleSheet(Stylesheets.BTN_SECONDARY)
    lay.addWidget(b1); lay.addWidget(ed); lay.addWidget(b2)
    form.setTabOrder(b1, ed)
    form.setTabOrder(ed, b2)
    form.setFixedSize(280, 200)
    form.show()
    a = app()
    a.processEvents()

    b1.setFocus()
    a.processEvents()
    seq = [b1]
    # 走焦点链遍历（等价于连按两次 Tab）：焦点应依次到输入框 → 次按钮
    for _ in range(2):
        form.focusNextChild()
        a.processEvents()
        seq.append(form.focusWidget())
    ok_moves = all(s is not None for s in seq) and len({id(s) for s in seq}) == 3
    check('V4.1 Tab 焦点链逐个移动', ok_moves,
          f'3 个不同焦点目标: {[type(s).__name__ for s in seq]}')
    check('V4.2 Tab 顺序符合 setTabOrder 声明',
          isinstance(seq[1], QLineEdit) and isinstance(seq[2], QPushButton),
          f'主按钮 → {type(seq[1]).__name__} → {type(seq[2]).__name__}')
    # 焦点链确实存在 next 链接（否则 Tab 无任何作用）
    check('V4.3 焦点链存在 nextInFocusChain 链接',
          b1.nextInFocusChain() is not None,
          '主按钮有后继焦点目标')

    for w, tag in ((b1, '主按钮'), (ed, '输入框'), (b2, '次按钮')):
        w.setFocus(); a.processEvents()
        n = golden_pixels(w.grab().toImage())
        check(f'V4.4 键盘聚焦「{tag}」有可见反馈', n > 50, f'{n} 金色像素')
    for w in (b1, ed, b2):
        w.deleteLater()


def v5_accessible_names() -> None:
    """V5：图标按钮具备无障碍名称（屏幕阅读器可读）。"""
    from ui.components.icon_button import IconButton
    cases = [
        ('robot', '龙虎山大师兄解读', None),
        ('copy', None, '复制排盘结果'),
        ('collapse-all', None, None),  # 三缺时回落默认
    ]
    missing = []
    for icon_name, tooltip, accessible in cases:
        btn = IconButton(icon_name=icon_name, tooltip=tooltip or '',
                         accessible=accessible)
        name = btn.accessibleName()
        if not name:
            missing.append(icon_name)
        btn.deleteLater()
    check('V5 IconButton 无障碍名称 100% 覆盖', not missing,
          f'{len(cases)} 例，缺失 {missing}' if missing else f'{len(cases)} 例全部具备')


def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def main() -> int:
    print('=== 键盘焦点与可访问性验证（P17） ===')
    QApplication(sys.argv)  # 提前建立 app
    v1_focus_rule_coverage()
    v2_no_outline_attr()
    v3_focus_ring_renders()
    v4_tab_traversal()
    v5_accessible_names()
    total = len(PASS) + len(FAIL)
    print(f'------------------------------------------------------------')
    print(f'verify_keyboard_focus: {len(PASS)}/{total} 通过'
          + (' ✅' if not FAIL else f' ❌ 失败项: {FAIL}'))
    return 0 if not FAIL else 1


if __name__ == '__main__':
    sys.exit(main())
