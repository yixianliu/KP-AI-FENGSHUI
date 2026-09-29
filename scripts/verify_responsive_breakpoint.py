# -*- coding: utf-8 -*-
"""验证「响应式断点」（M2 / §4.4 四档断点）合规。

校验点：
  1. 断点常量存在且取值正确：BP_XS=900 / BP_S=1100 / BP_L=1440；
  2. 断点严格递增：BP_XS < BP_S < BP_L；
  3. main_window.py 在响应式分支（_apply_responsive / resizeEvent）使用
     Spacing.BP_XS/BP_S/BP_L 令牌，未硬编码 900/1100/1440 裸数字；
  4. 断点分类契约：窗口宽度 → 档位( XS/S/M/L ) 边界行为正确；
  5. Spacing.density_for 按断点返回正确密度档（compact/normal/spacious）。

退出码：0 = 全部通过；1 = 存在断点定义或引用违规。
"""
import io
import re
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ui.styles import Spacing


def _strip_comments_and_strings(text: str) -> str:
    """用 tokenize 剥离注释与字符串字面量，返回「纯代码」文本。

    背景：断点文档写在 docstring（如 'XS (<900)：单栏'）中，若直接正则扫
    描会把 docstring 里的 <900 误判为硬编码裸数字。tokenize 同时 blank 掉
    COMMENT 与 STRING token，仅保留真正参与运算的标识符与数字。
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text  # 语法异常回退原文（宁漏报，不误剥）
    lines = text.splitlines()
    char_rows = [list(ln) for ln in lines]
    for tok in tokens:
        if tok.type not in (tokenize.COMMENT, tokenize.STRING):
            continue
        (srow, scol), (erow, ecol) = tok.start, tok.end  # 行 1-based / 列 0-based
        for r in range(srow, erow + 1):
            row = char_rows[r - 1]
            start = scol if r == srow else 0
            end = ecol if r == erow else len(row)
            for c in range(start, min(end, len(row))):
                row[c] = ' '
    return '\n'.join(''.join(row) for row in char_rows)


def _check(name, ok, detail=''):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def _classify(width):
    """复刻 main_window.resizeEvent 的断点分类（纯函数，仅依赖常量）。"""
    return ('XS' if width < Spacing.BP_XS
            else 'S' if width < Spacing.BP_S
            else 'M' if width < Spacing.BP_L
            else 'L')


def main():
    all_pass = True
    print("=" * 64)
    print("verify_responsive_breakpoint: 响应式断点合规校验（M2 / §4.4）")
    print("=" * 64)

    # 1. 常量取值正确
    print("\n[1] 断点常量取值校验")
    for attr, expect in (('BP_XS', 900), ('BP_S', 1100), ('BP_L', 1440)):
        val = getattr(Spacing, attr, None)
        ok = val == expect
        all_pass = _check(f"Spacing.{attr} == {expect}", ok, f"={val}") and all_pass

    # 2. 严格递增
    print("\n[2] 断点严格递增校验")
    ok_order = (Spacing.BP_XS < Spacing.BP_S < Spacing.BP_L)
    all_pass = _check(
        "BP_XS < BP_S < BP_L", ok_order,
        f"({Spacing.BP_XS} < {Spacing.BP_S} < {Spacing.BP_L})",
    ) and all_pass

    # 3. main_window.py 使用常量而非裸数字
    print("\n[3] main_window.py 引用断点令牌（无硬编码裸数字）")
    mw_src = (ROOT / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    uses_token = all(
        f'Spacing.{a}' in mw_src for a in ('BP_XS', 'BP_S', 'BP_L')
    )
    all_pass = _check(
        "main_window 使用 Spacing.BP_XS/BP_S/BP_L 令牌",
        uses_token,
        "响应式分支引用断点令牌" if uses_token else "存在未引用令牌的断点",
    ) and all_pass
    # 反向：在「纯代码」（已剥离注释与 docstring）中不得出现裸断点数字比较
    code_only = _strip_comments_and_strings(mw_src)
    bare_hits = re.findall(r'(<\s*900|<\s*1100|>=?\s*1440|<\s*1440)', code_only)
    ok_no_bare = not bare_hits
    all_pass = _check(
        "main_window 无硬编码断点裸数字（900/1100/1440）",
        ok_no_bare,
        "未出现裸数字比较" if ok_no_bare else f"命中裸数字: {bare_hits}",
    ) and all_pass

    # 4. 断点分类边界契约
    print("\n[4] 断点分类边界契约（XS/S/M/L）")
    cases = [
        (899, 'XS'), (900, 'S'), (1099, 'S'),
        (1100, 'M'), (1439, 'M'), (1440, 'L'), (2560, 'L'),
    ]
    ok_cls = True
    bad = []
    for w, expect in cases:
        got = _classify(w)
        if got != expect:
            ok_cls = False
            bad.append(f"{w}->{got}(期望{expect})")
    all_pass = _check(
        "窗口宽度→档位分类边界正确",
        ok_cls,
        "900/1100/1440 三档边界划分正确" if ok_cls else f"错误: {bad}",
    ) and all_pass

    # 5. density_for 按断点返回密度档
    print("\n[5] Spacing.density_for 密度档契约")
    d_compact = Spacing.density_for(800)        # < BP_S → compact
    d_normal = Spacing.density_for(1200)        # BP_S<=w<BP_L → normal
    d_spacious = Spacing.density_for(1600)      # >= BP_L → spacious
    ok_density = (
        d_compact == Spacing.DENSITY['compact']
        and d_normal == Spacing.DENSITY['normal']
        and d_spacious == Spacing.DENSITY['spacious']
    )
    all_pass = _check(
        "density_for: <900→compact, 1100→normal, 1440→spacious",
        ok_density,
        f"compact={d_compact[0]} normal={d_normal[0]} spacious={d_spacious[0]}",
    ) and all_pass

    print("\n" + "=" * 64)
    if all_pass:
        print("verify_responsive_breakpoint: 响应式断点全部合规 ✅")
        return 0
    print("verify_responsive_breakpoint: 响应式断点校验未通过 ❌")
    return 1


if __name__ == '__main__':
    sys.exit(main())
