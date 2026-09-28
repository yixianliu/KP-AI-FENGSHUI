# -*- coding: utf-8 -*-
"""
scripts/verify_timeline_badge.py — 大运关系徽章标准化验证

M4-T4 适配部分的验证：timeline._DayunRow 的趋势徽章已从手搓 QLabel
改为标准 ui.components.badge.Badge 组件。

断言：
- A1 RELATION_STYLE 语义键全部是 Badge 支持的合法语义色
- A2 _relation_to_level 四种关系映射到正确的 (标签, 语义, 图标)
- A3 _DayunRow 渲染出的趋势徽章是 Badge 实例（且每行恰好一个）
- A4 三种关系（克我/生我/平）渲染出可区分的徽章背景色
- A5 fortune_timeline_widget 完整渲染冒烟（含起运行 + 大运行 + 流年网格）
- A6 徽章文字对比度（Badge._contrast_fg 推导，防语义色阈值漂移）

用法：QT_QPA_PLATFORM=offscreen ./venv/Scripts/python.exe scripts/verify_timeline_badge.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication, QLabel, QWidget, QFrame, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QColor
from collections import Counter

PASSED = 0
FAILED = 0


def check(name, cond, detail=''):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f'  [PASS] {name}')
    else:
        FAILED += 1
        print(f'  [FAIL] {name} — {detail}')


def hex_of(qcolor):
    return '#%02x%02x%02x' % (qcolor.red(), qcolor.green(), qcolor.blue())


def dominant_rgb(img):
    """取图像中众数 RGB（规避文字/抗锯齿干扰）。"""
    c = Counter()
    for y in range(img.height()):
        for x in range(img.width()):
            p = img.pixelColor(x, y)
            c[(p.red(), p.green(), p.blue())] += 1
    return c.most_common(1)[0][0]


def contrast_ratio(hex1, hex2):
    """WCAG 对比度。"""
    def lum(h):
        r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
        def lin(v):
            v /= 255.0
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    l1, l2 = lum(hex1), lum(hex2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    # ---------- A1：RELATION_STYLE 语义键合法性 ----------
    from ui.components.timeline import RELATION_STYLE, _relation_to_level, _DayunRow, fortune_timeline_widget
    from ui.components.badge import _BADGE_COLORS, Badge, _contrast_fg
    from ui.styles import Colors

    print('\n[A1] RELATION_STYLE 语义键合法性')
    for rel, (label, semantic, icon) in RELATION_STYLE.items():
        check(f'{rel} → semantic={semantic!r} 是合法 Badge 语义',
              semantic in _BADGE_COLORS, f'合法键={list(_BADGE_COLORS)}')
        check(f'{rel} → 标签 {label!r} 非空', bool(label))
        check(f'{rel} → 图标 {icon!r} 非空', bool(icon))

    # ---------- A2：_relation_to_level 映射 ----------
    print('\n[A2] _relation_to_level 关系归一')
    cases = [
        (None, None, '平', 'info', '～'),
        ('平', '平', '平', 'info', '～'),
        ('生我', '比和', '吉', 'success', '✓'),
        ('比和', '生我', '吉', 'success', '✓'),
        ('生我', None, '吉', 'success', '✓'),
        ('克我', '生我', '慎', 'warning', '⚠'),  # 克我优先（生克并存取凶）
        ('克我', None, '慎', 'warning', '⚠'),
        (None, '克我', '慎', 'warning', '⚠'),
    ]
    for gan, zhi, exp_label, exp_sem, exp_icon in cases:
        got = _relation_to_level(gan, zhi)
        check(f'({gan!r},{zhi!r}) → {got[0]}/{got[1]}/{got[2]}',
              got == (exp_label, exp_sem, exp_icon),
              f'期望=({exp_label},{exp_sem},{exp_icon})')

    # ---------- A3：_DayunRow 渲染出 Badge 实例 ----------
    print('\n[A3] _DayunRow 趋势徽章是 Badge 实例')
    rows = []
    fixtures = [
        ('克我', {'period': '第1步', 'ganzhi': '甲子', 'start_age': 10, 'end_age': 19,
                  'start_year': 2025, 'end_year': 2034, 'analysis': '忌行险地，宜守旧业。',
                  'detailed_analysis': {'gan': '甲', 'gan_wx': '木', 'zhi': '子', 'zhi_wx': '水',
                                        'gan_relation': '克我', 'zhi_relation': '生我'}}),
        ('生我', {'period': '第2步', 'ganzhi': '乙丑', 'start_age': 20, 'end_age': 29,
                  'start_year': 2035, 'end_year': 2044, 'analysis': '贵人相助，谋事易成。',
                  'detailed_analysis': {'gan': '乙', 'gan_wx': '木', 'zhi': '丑', 'zhi_wx': '土',
                                        'gan_relation': '生我', 'zhi_relation': '比和'}}),
        ('平', {'period': '第3步', 'ganzhi': '丙寅', 'start_age': 30, 'end_age': 39,
                'start_year': 2045, 'end_year': 2054, 'analysis': '运势平稳，宜守成。',
                'detailed_analysis': {'gan': '丙', 'gan_wx': '火', 'zhi': '寅', 'zhi_wx': '木',
                                      'gan_relation': '平', 'zhi_relation': '平'}}),
    ]
    for key, period in fixtures:
        r = _DayunRow(period, Colors.LIUJIN, is_last=True)
        r.show()
        app.processEvents()
        badges = [w for w in r.findChildren(Badge)]
        check(f'{key} 行含 Badge 实例（{len(badges)} 个）', len(badges) == 1,
              f'实际 {len(badges)} 个')
        if badges:
            b = badges[0]
            rows.append((key, b))
    check('3 行全部渲染成功', len(rows) == 3)

    # ---------- A4：三种关系徽章背景色可区分 ----------
    print('\n[A4] 三种关系徽章背景色可区分')
    # 注意：不能把 A3 里 row 的 Badge 搬进新容器——addWidget 会 reparent，
    # 原父链（card→row）会被级联销毁，触发 C++ 悬空指针。改为独立构造 Badge
    # 做采样：A3 已证明 row 内确有 Badge 实例，此处只需验证语义键→背景色的映射。
    bgs = {}
    for key in ('克我', '生我', '平'):
        sem = RELATION_STYLE[key][1]
        host = QWidget()
        host.setStyleSheet(f"background:{Colors.CARD};")
        hl = QHBoxLayout(host)
        hl.setContentsMargins(0, 0, 0, 0)
        b = Badge(f'{RELATION_STYLE[key][2]} {RELATION_STYLE[key][0]}',
                  semantic=sem)
        hl.addWidget(b)
        host.show()
        app.processEvents()
        host.setFixedHeight(host.sizeHint().height())
        app.processEvents()
        img = host.grab().toImage()
        bgs[key] = dominant_rgb(img)
        check(f'{key}（{sem}）徽章背景采样成功 '
              f'{img.width()}×{img.height()}={hex_of(QColor(*bgs[key]))}',
              img.width() > 20 and img.height() > 10)
    distinct = set(bgs.values())
    check(f'3 种关系背景互不相同（{len(distinct)} 种）', len(distinct) == 3,
          f'采样={bgs}')

    # ---------- A5：完整时间轴冒烟 ----------
    print('\n[A5] fortune_timeline_widget 完整渲染')
    dayun = {
        'direction': '顺行',
        'qiyun_text': '3 岁 8 个月起运',
        'periods': [p for _, p in fixtures],
    }
    liunian = {
        'years': [
            {'year': 2025, 'ganzhi': '乙巳', 'analysis': '火旺之年，宜进取。',
             'detailed_analysis': {'gan': '乙', 'gan_wx': '木', 'zhi': '巳', 'zhi_wx': '火',
                                   'gan_relation': '生我', 'zhi_relation': '克我'}},
            {'year': 2026, 'ganzhi': '丙午', 'analysis': '火土相生，稳中求进。',
             'detailed_analysis': {'gan': '丙', 'gan_wx': '火', 'zhi': '午', 'zhi_wx': '火',
                                   'gan_relation': '克我', 'zhi_relation': '克我'}},
        ]
    }
    try:
        w = fortune_timeline_widget(dayun, liunian, Colors.LIUJIN)
        w.show()
        app.processEvents()
        check('时间轴构造无异常', w is not None and w.isVisible())
        badge_count = len(w.findChildren(Badge))
        check(f'完整时间轴含 Badge（{badge_count} 个）', badge_count >= 3,
              f'期望 ≥3（3 个大运行各一个），实际 {badge_count}')
        # 空数据回退
        empty = fortune_timeline_widget({}, {}, Colors.LIUJIN)
        check('空数据回退为提示标签', isinstance(empty, QLabel))
    except Exception as e:
        import traceback
        check('时间轴渲染冒烟', False, f'{e}\n{traceback.format_exc()}')

    # ---------- A6：徽章文字对比度（WCAG AA 小字 ≥4.5:1） ----------
    print('\n[A6] Badge 文字对比度（WCAG AA 小字）')
    # 遍历 RELATION_STYLE 实际用到的语义键，验证其背景/前景对比度达标
    used_semantics = {rel: spec[1] for rel, spec in RELATION_STYLE.items()}
    for rel, sem_key in used_semantics.items():
        bg = _BADGE_COLORS[sem_key]
        fg = _contrast_fg(bg)
        ratio = contrast_ratio(bg, fg)
        check(f'{rel} → {sem_key} {bg} → fg={fg} 对比 {ratio:.2f}:1 ≥4.5:1',
              ratio >= 4.5, f'{ratio:.2f}:1')

    print('\n' + '=' * 60)
    print(f'verify_timeline_badge: {PASSED}/{PASSED + FAILED} 通过')
    if FAILED:
        print('存在失败项 ❌')
        return 1
    print('时间轴徽章标准化全部通过 ✅')
    return 0


if __name__ == '__main__':
    sys.exit(main())
