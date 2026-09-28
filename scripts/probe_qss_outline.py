# -*- coding: utf-8 -*-
"""
scripts/probe_qss_outline.py — 决定性测试：Qt QSS 是否支持 `outline` 属性

背景（P17）
----------
项目内焦点环用了 `outline: 2px solid {BRAND}`：
  - ui/components/icon_button.py:91
  - ui/styles.py:663（QComboBox::drop-down 的 `outline: none`）
  - ui/styles.py:947（DIALOG 块 :focus-visible）
若 Qt 不支持 outline，这些焦点环从未生效——键盘 Tab 无视觉反馈。

方法：用**无条件**样式（不依赖 :focus 伪状态，offscreen 下伪状态不稳定），
用 `btn.grab()` 取位图，在**贴边环形带**内采样古金色 (#c9a227) 像素。
  - border  有效 → 贴边出现金色（对照组，验证采样方法本身正确）
  - outline 有效 → 贴边出现金色
  - 阴性对照    → 贴边不应出现金色
"""
from __future__ import annotations

import sys

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QPushButton

# 古金 #c9a227 及其容差（抗锯齿边缘）
BRAND_R, BRAND_G, BRAND_B = 0xC9, 0xA2, 0x27
TOL = 40


def _rgb(px: int) -> tuple[int, int, int]:
    """QRgb → (r, g, b)，按位提取（避免 QColor 构造歧义）。"""
    return (px >> 16) & 0xFF, (px >> 8) & 0xFF, px & 0xFF


CASES = {
    # 对照组：验证「贴边采样」方法本身能检出金色边框
    'border':    'QPushButton { border: 2px solid #c9a227; background: #21213a; }',
    # 待验证：Qt QSS 是否支持 outline
    'outline':   'QPushButton { outline: 2px solid #c9a227; background: #21213a; }',
    # 阴性对照：明确不放金边框
    'none':      'QPushButton { border: 2px solid #33335A; background: #21213a; }',
}


def golden_pixels_near_edge(img: QImage, band: int = 4) -> int:
    """统计贴边环形带内的古金像素数。"""
    w, h = img.width(), img.height()
    count = 0
    for y in range(h):
        for x in range(w):
            # 只取贴边环带，避开按钮中心文字
            if not (x < band or y < band or x >= w - band or y >= h - band):
                continue
            a = (img.pixel(x, y) >> 24) & 0xFF
            if a < 200:
                continue
            r, g, b = _rgb(img.pixel(x, y))
            if abs(r - BRAND_R) <= TOL and abs(g - BRAND_G) <= TOL \
                    and abs(b - BRAND_B) <= TOL:
                count += 1
    return count


def grab(btn: QPushButton, side: int = 80) -> QImage:
    btn.setFixedSize(side, side)
    btn.show()
    return btn.grab().toImage()


def main() -> int:
    app = QApplication.instance() or QApplication([])
    print('=== QSS outline 属性有效性测试 ===')
    results = {}
    for name, qss in CASES.items():
        btn = QPushButton('OK')
        btn.setStyleSheet(qss)
        app.processEvents()
        img = grab(btn)
        n = golden_pixels_near_edge(img)
        results[name] = n
        flag = '检出焦点环' if n > 50 else ('未检出' if n == 0 else '少量/边缘')
        print(f'  {name:8s} 贴边古金像素 = {n:5d}  <- {flag}')

    print('\n=== 结论 ===')
    if results['border'] <= 50:
        print('⚠ 对照组 border 也未检出——采样方法失效，测试不可信')
        return 1
    if results['outline'] > 50:
        print('outline 属性【有效】：Qt 支持，焦点环真实渲染')
    else:
        print('outline 属性【无效】：Qt QSS 静默忽略该属性，焦点环从未生效')
        print('→ 修复方向：焦点环必须用 border 实现')
    return 0


if __name__ == '__main__':
    sys.exit(main())
