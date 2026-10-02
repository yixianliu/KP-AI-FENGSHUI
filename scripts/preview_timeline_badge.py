# -*- coding: utf-8 -*-
"""大运流年时间轴 Badge 视觉预览生成器（设计签核用，非断言门禁）
================================================================
用途：把 `ui/components/timeline.py::fortune_timeline_widget` 的真实渲染结果
落成一张 PNG，供人工核对 M4-T4 落地的「关系徽章」（吉/慎/平）在三档语义色下的
观感与自动前景色对比。与 `verify_timeline_badge.py`（35 项文本断言）互补：
后者断言「值对不对」，本脚本呈现「看起来对不对」。

用法（必须用 venv 的 PySide6，且离屏）：
    QT_QPA_PLATFORM=offscreen ./venv/Scripts/python.exe scripts/preview_timeline_badge.py
产物：build/screenshots/timeline_badge_preview.png

关键坑（已在 skill 记录）：离屏 QPA 的字体库为空（QFontDatabase.families() == 0），
不显式注入系统 CJK 字体时所有中文渲染为豆腐块。见 `_install_cjk_font`。
"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                               QFrame, QScrollArea)
from PySide6.QtGui import QFont, QFontDatabase

from ui.styles import Colors, Fonts, Spacing
from ui.components.timeline import fortune_timeline_widget

# 系统 CJK 字体候选（按优先级）；离屏字体库为空时必须手动注入
_CJK_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\msyh.ttc",    # 微软雅黑
    r"C:\Windows\Fonts\simhei.ttf",  # 黑体
    r"C:\Windows\Fonts\simsun.ttc",  # 宋体
)


def _install_cjk_font(app):
    """离屏 QPA 字体库为空 → 注入系统 CJK 字体并设为应用字体，避免豆腐块。

    Returns:
        str: 实际生效的字体族名（无可用字体时回退 'Microsoft YaHei'）。
    """
    family = "Microsoft YaHei"
    for path in _CJK_FONT_CANDIDATES:
        if not os.path.exists(path):
            continue
        fid = QFontDatabase.addApplicationFont(path)
        names = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
        if names:
            family = names[0]
            print(f"[font] loaded {path} -> {names[:2]}")
            break
    else:
        print("[font] WARN 未找到系统 CJK 字体，中文可能渲染为豆腐块")
    app.setFont(QFont(family, 10))  # 对齐 ui/main_window.py
    return family


def _preview_data():
    """构造覆盖三档关系徽章 + 当前大运高亮的大运样本。"""
    def period(no, ganzhi, sa, ea, sy, ey, gan_rel, zhi_rel, gan_wx, zhi_wx, txt):
        return {
            'period': no, 'ganzhi': ganzhi, 'start_age': sa, 'end_age': ea,
            'start_year': sy, 'end_year': ey, 'analysis': txt,
            'detailed_analysis': {
                'gan': ganzhi[0], 'gan_wx': gan_wx,
                'zhi': ganzhi[1], 'zhi_wx': zhi_wx,
                'gan_relation': gan_rel, 'zhi_relation': zhi_rel,
                '十神': '正官', '纳音': '杨柳木',
            },
        }
    periods = [
        # 生我 → Badge success（绿）
        period(1, '壬午', 4, 13, 1994, 2003, '生我', '生我', '水', '火', '早年得长辈提携，学业顺遂。'),
        # 克我 → Badge warning（琥珀）
        period(2, '癸未', 14, 23, 2004, 2013, '克我', '克我', '水', '土', '压力较重，需防小人是非。'),
        # 我生/我克 → Badge info（蓝）
        period(3, '甲申', 24, 33, 2014, 2023, '我生', '我克', '木', '金', '泄秀输出，宜主动作为。'),
        # 生我 → success；且 2024-2033 命中当前年 → 金色描边 + 📍当前大运
        period(4, '乙酉', 34, 43, 2024, 2033, '生我', '平', '木', '金', '印星护身，宜稳中求进。'),
        # 克我 → warning（克我 优先级高于 生我）
        period(5, '丙戌', 44, 53, 2034, 2043, '克我', '生我', '火', '土', '火土交争，注意健康与破财。'),
    ]
    return {
        'dayun': {'qiyun_text': '4岁3个月起运', 'direction': '顺', 'periods': periods},
        'liunian': {'years': [{'year': 2026, 'ganzhi': '丙午', 'analysis': '流年顺遂'}]},
    }


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    _install_cjk_font(app)

    data = _preview_data()
    timeline = fortune_timeline_widget(data['dayun'], data['liunian'], Colors.LIUJIN)

    # 外层容器显式给 BG 底色（timeline 自身 transparent），grab 才有实底
    outer = QWidget()
    outer.setStyleSheet(f"background:{Colors.BG};")
    outer.setFixedWidth(940)
    ol = QVBoxLayout(outer)
    ol.setContentsMargins(Spacing.S6, Spacing.S6, Spacing.S6, Spacing.S6)
    ol.setSpacing(Spacing.S4)

    head = QLabel('大运流年时间轴 · Badge 语义色预览（M4-T4）')
    head.setStyleSheet(
        f"color:{Colors.LIUJIN}; font-size:{Fonts.FS_H2}px; "
        f"font-weight:{Fonts.W_BOLD}; font-family:{Fonts.BODY};")
    ol.addWidget(head)

    card = QFrame()
    card.setStyleSheet(
        f"QFrame {{ background:{Colors.CARD}; border:1px solid {Colors.BORDER}; "
        f"border-radius:{Spacing.RADIUS}; }}")
    cl = QVBoxLayout(card)
    cl.setContentsMargins(Spacing.S5, Spacing.S5, Spacing.S5, Spacing.S5)
    cl.setSpacing(Spacing.S3)
    cl.addWidget(timeline)
    ol.addWidget(card)
    ol.addStretch()

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(outer)
    scroll.setStyleSheet(f"QScrollArea {{ background:{Colors.BG}; border:none; }}")
    scroll.resize(980, 1150)
    scroll.show()

    for _ in range(4):          # 离屏需多次 processEvents 几何才生效
        app.processEvents()

    shot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'build', 'screenshots')
    os.makedirs(shot_dir, exist_ok=True)
    out = os.path.join(shot_dir, 'timeline_badge_preview.png')

    # 抓 outer（有实底）：透明控件直接 grab 会得 alpha=0 黑伪影
    outer.resize(940, max(outer.sizeHint().height(), 400))
    for _ in range(3):
        app.processEvents()
    img = outer.grab().toImage()
    ok = img.save(out)
    print(f"saved={ok} path={out} size={img.width()}x{img.height()}")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
