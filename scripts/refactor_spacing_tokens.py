# -*- coding: utf-8 -*-
"""
scripts/refactor_spacing_tokens.py — 批量把 setSpacing/addSpacing 硬编码归位到 8-4 令牌

P05/P06 痛点：UI 层间距散落硬编码（2/3/4/5/6/10/14/18/28 等），
非 8-4 值导致同类列表项跨面板视觉不齐。本脚本按「就近取体系值」规则机械替换，
保持功能不变（单处差值 ≤2px，唯一例外 28→S7 差 4px）。

映射规则（8-4 基准 Spacing.S0~S8 = 0/4/8/12/16/20/24/32/48）：

    0           → S0   (0)
    1,2,3,4,5   → S1   (4)
    6,7,8       → S2   (8)
    9,10,11,12,13 → S3 (12)
    14,15,16,17,18 → S4 (16)
    19,20,21    → S5   (20)
    22,23,24,25,26,27 → S6 (24)
    28,29,30,31,32 → S7 (32)   ← 28→32 差 4px，唯一超出 2px 的例外
    48          → S8   (48)

超出规则表的值保持原样并打印告警（避免误伤特殊布局）。

幂等性：已用 Spacing.S* 的调用不会被再次匹配（正则仅匹配裸数字）。

用法：
    python scripts/refactor_spacing_tokens.py             # 全 ui/ 目录（除 styles.py）
    python scripts/refactor_spacing_tokens.py --dry-run   # 只统计不写入
    python scripts/refactor_spacing_tokens.py --verbose   # 打印每处明细
    python scripts/refactor_spacing_tokens.py ui/components/a.py ui/components/b.py
退出码：0 正常。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / 'ui'

# styles.py 是设计令牌「单一真相源」，豁免
EXEMPT = {str(UI_DIR / 'styles.py')}

# 裸像素值 → Spacing 令牌（就近取 8-4 体系值）
MAPPING = {
    '0': 'Spacing.S0',
    '1': 'Spacing.S1', '2': 'Spacing.S1', '3': 'Spacing.S1',
    '4': 'Spacing.S1', '5': 'Spacing.S1',
    '6': 'Spacing.S2', '7': 'Spacing.S2', '8': 'Spacing.S2',
    '9': 'Spacing.S3', '10': 'Spacing.S3', '11': 'Spacing.S3',
    '12': 'Spacing.S3', '13': 'Spacing.S3',
    '14': 'Spacing.S4', '15': 'Spacing.S4', '16': 'Spacing.S4',
    '17': 'Spacing.S4', '18': 'Spacing.S4',
    '19': 'Spacing.S5', '20': 'Spacing.S5', '21': 'Spacing.S5',
    '22': 'Spacing.S6', '23': 'Spacing.S6', '24': 'Spacing.S6',
    '25': 'Spacing.S6', '26': 'Spacing.S6', '27': 'Spacing.S6',
    '28': 'Spacing.S7', '29': 'Spacing.S7', '30': 'Spacing.S7',
    '31': 'Spacing.S7', '32': 'Spacing.S7',
    '48': 'Spacing.S8', '50': 'Spacing.S8',
}

PATTERN = re.compile(r'\b(?:set|add)Spacing\(\s*(\d+)\s*\)')


def default_targets():
    """默认扫描全 ui/ 目录的 .py，排除设计令牌真相源。"""
    return sorted(p for p in UI_DIR.rglob('*.py') if str(p) not in EXEMPT)


def refactor(text: str):
    """替换文本中的 setSpacing/addSpacing 硬编码。

    Returns:
        (新文本, 变更列表 [(原值, 令牌或None), ...])，None 表示未覆盖保持原样。
    """
    changes = []

    def _sub(m):
        val = m.group(1)
        token = MAPPING.get(val)
        changes.append((val, token))
        return m.group(0) if token is None else f'{m.group(0).split("(")[0]}({token})'

    return PATTERN.sub(_sub, text), changes


def main(argv):
    dry = '--dry-run' in argv
    verbose = '--verbose' in argv
    args = [a for a in argv if not a.startswith('--')]
    targets = [Path(a) for a in args] if args else default_targets()

    total = 0
    unmapped = {}
    written = 0
    for p in targets:
        if not p.exists():
            print(f'[MISS] {p}')
            continue
        text = p.read_text(encoding='utf-8')
        new_text, changes = refactor(text)
        bad = sorted({v for v, t in changes if t is None}, key=int)
        for v in bad:
            unmapped[v] = unmapped.get(v, 0) + 1
        if changes:
            rel = p.relative_to(ROOT)
            print(f'{rel}: {len(changes)} 处'
                  + (f'  ⚠ 未覆盖 {bad}' if bad else ''))
            if verbose:
                for val, tok in changes:
                    print(f'    {val:>3} → {tok or val}')
        if not dry and new_text != text:
            p.write_text(new_text, encoding='utf-8')
            written += 1
        total += len(changes)

    print('-' * 56)
    mode = 'dry-run（未写入）' if dry else f'已写入 {written} 个文件'
    print(f'共 {total} 处，{mode}'
          + (f'；超出规则表的值 {unmapped}' if unmapped else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
