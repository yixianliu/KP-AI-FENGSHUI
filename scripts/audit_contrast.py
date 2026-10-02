# -*- coding: utf-8 -*-
"""
scripts/audit_contrast.py — WCAG 对比度审计（M1-T5 / M7-T1）

计算 Colors 色板各文本/背景色对的对比度，校验是否满足 WCAG AA：
  - 正文（< 18px）  ≥ 4.5:1
  - 大字（≥ 18px）  ≥ 3:1

用法：
    python scripts/audit_contrast.py
退出码：0 = 全部达标；1 = 存在不达标色对 / 色对表为空（门禁空转）。

空转守卫（2026-09-29 第 7 轮补）：原逻辑「fail == 0 即通过」，若 PAIRS 被误清空
则循环不执行、fail 恒 0 也判绿。现显式打印「已校验 N 个色对」并在 N == 0 时判红。
"""
import sys

# 引入项目 Colors 单一真相源
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
from ui.styles import Colors  # noqa: E402


def _rel_luminance(hex_color: str) -> float:
    """按 WCAG 2.x 相对亮度公式计算。支持 #RRGGBB。"""
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    c = tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    c = tuple(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c)
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    """两色对比度（WCAG 公式）。"""
    l1, l2 = _rel_luminance(hex_a), _rel_luminance(hex_b)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


# 文本/背景色对（对齐实施计划 7.5 可访问性验收）
# 每项：(前景, 背景, 是否大字)
PAIRS = [
    (Colors.TEXT,   Colors.CARD,  False),  # 正文主色 on 卡片
    (Colors.TEXT2,  Colors.CARD,  False),  # 二级灰阶 on 卡片
    (Colors.TEXT3,  Colors.CARD,  False),  # 三级灰阶 on 卡片
    (Colors.TEXT4,  Colors.CARD,  False),  # 四级灰阶 on 卡片
    (Colors.TEXT,   Colors.BG,    False),  # 主色 on 背景
    (Colors.BRAND,  Colors.CARD,  False),  # 品牌金 on 卡片（大字场景）
    (Colors.BRAND,  Colors.BG,    False),  # 品牌金 on 背景
    (Colors.TEXT_INV, Colors.BRAND, True), # 反白 on 品牌金（checked 态）
    (Colors.TEXT,   Colors.ACCENT, True),  # 浅字 on 朱红（主按钮，M7 修正原深字 1.85:1）
    (Colors.TEXT,   Colors.DANGER_DARK, False),  # 浅字 on 危险暗红（危险按钮）
]


def main():
    print("=== WCAG AA 对比度审计 ===")
    print(f"{'前景':>10} {'背景':>10}  对比度   要求   结果")
    print('-' * 52)
    fail = 0
    for fg, bg, big in PAIRS:
        ratio = contrast_ratio(fg, bg)
        need = 3.0 if big else 4.5
        ok = ratio >= need
        mark = '✅' if ok else '❌'
        if not ok:
            fail += 1
        print(f"{fg:>10} {bg:>10}  {ratio:5.2f}:1  {need:.1f}:1  {mark}")
    print('-' * 52)
    total = len(PAIRS)
    passed = total - fail
    print(f"汇总: {passed}/{total} 项通过（WCAG AA 色对）")
    # 空转守卫：色对表为空时 fail 必然为 0，若照旧判绿就是「一项没查也算过」。
    if total == 0:
        print("audit_contrast: 色对表 PAIRS 为空 —— 门禁空转 ❌")
        return 1
    if fail == 0:
        print(f"audit_contrast: 全部 {total} 个色对达标 WCAG AA ✅")
        return 0
    print(f"audit_contrast: {fail} 个色对不达标 ⚠️（见上）")
    return 1


if __name__ == '__main__':
    sys.exit(main())
