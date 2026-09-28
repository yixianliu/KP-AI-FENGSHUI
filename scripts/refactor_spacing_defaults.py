#!/usr/bin/env python3
"""
把「创建布局但未显式 setSpacing」的位置补上 Spacing.S2，使间距体系闭合。

背景（P05/P06 收尾）
--------------------
QHBoxLayout()/QVBoxLayout()/QGridLayout() 创建后不显式设置 spacing 时，
Qt 会取样式默认值（常见为 6），落在 8-4 体系（0/4/8/12/16/20/24/32/48）之外。
此前审计只覆盖「setSpacing(裸数字)」的显式硬编码，遗漏了这种隐式继承。
补 S2(8) 是对默认 6 的最近体系值，视觉扰动 ≤2px。

幂等：仅对「变量后续从未出现 .setSpacing(」的位置插入，重跑不重复插入。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

UI_DIR = Path(__file__).resolve().parent.parent / 'ui'

LAYOUT_PAT = re.compile(
    r'^([ \t]*)([A-Za-z_]\w*)\s*=\s*(?:QHBoxLayout|QVBoxLayout|QGridLayout)\s*\('
)

# 插入的注释，说明为什么是 S2
INSERT_COMMENT = '  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）'


def _has_spacing_call(text: str, var: str) -> bool:
    """变量在文本后续是否出现过 .setSpacing( 调用。"""
    return bool(re.search(rf'\b{re.escape(var)}\.setSpacing\(', text))


def ensure_spacing_import(source: str) -> str:
    """若文件从 ui.styles 导入但未引入 Spacing，则补入。"""
    if 'Spacing' in source:
        return source
    # from ...styles import (...)  多行形式
    m = re.search(r'from\s+ui\.styles\s+import\s*\(', source)
    if m:
        start = m.end() - 1
        end = source.find(')', start)
        if end != -1 and 'Spacing' not in source[start:end]:
            block = source[start:end]
            # 追加到块末（保留缩进风格）
            new_block = block.rstrip() + ', Spacing)'
            return source[:start] + new_block + source[end + 1:]
    # from ...styles import X, Y, Z  单行形式
    m = re.search(r'from\s+ui\.styles\s+import\s+([^\n(]+)', source)
    if m:
        names = m.group(1)
        if 'Spacing' not in names:
            return source[:m.end()] + f', Spacing{source[m.end():]}'
    return source


def fix_file(path: Path, dry_run: bool, verbose: bool) -> int:
    src = path.read_text(encoding='utf-8')
    lines = src.splitlines()
    out: list[str] = []
    n = 0

    for line in lines:
        m = LAYOUT_PAT.match(line)
        if m and not _has_spacing_call(src, m.group(2)):
            out.append(line)
            out.append(f'{m.group(1)}{m.group(2)}.setSpacing(Spacing.S2)'
                       + INSERT_COMMENT)
            n += 1
        else:
            out.append(line)

    if n == 0:
        return 0

    new_src = ensure_spacing_import('\n'.join(out) + ('\n' if src.endswith('\n') else ''))
    if not dry_run:
        path.write_text(new_src, encoding='utf-8')
    if verbose:
        print(f'{path}: +{n} 处补 Spacing.S2')
    return n


def main() -> int:
    ap = argparse.ArgumentParser(
        description='为未显式 setSpacing 的布局补 Spacing.S2，闭合 8-4 间距体系。')
    ap.add_argument('--dry-run', action='store_true', help='仅报告，不写盘')
    ap.add_argument('--verbose', '-v', action='store_true', help='逐文件打印')
    ap.add_argument('files', nargs='*', help='显式文件列表；默认扫描 ui/ 全部 py')
    args = ap.parse_args()

    if args.files:
        targets = [Path(f) for f in args.files]
    else:
        targets = sorted(UI_DIR.rglob('*.py'))

    total = 0
    for t in targets:
        if t.exists() and t.suffix == '.py':
            total += fix_file(t, args.dry_run, args.verbose)

    verb = '待写入' if args.dry_run else '已写入'
    print(f'{verb}: {total} 处布局补齐显式 spacing')
    return 0


if __name__ == '__main__':
    sys.exit(main())
