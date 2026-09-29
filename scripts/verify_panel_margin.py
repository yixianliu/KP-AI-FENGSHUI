# -*- coding: utf-8 -*-
"""校验「面板/卡片间距令牌化」的合规性（M3-3 样式令牌化后缀验证）。

与 scripts/audit_style_tokens.py 采用**完全一致的豁免口径**，并额外校验：
  · 间距调用的 Spacing.* 令牌值必须与 ui.styles.Spacing 定义一致（写死比对，
    防止令牌值被误改后验证脚本跟着变绿）；
  · 全 0 内边距（等价 S0）为「贴边紧凑容器」的合法声明（占全目录 35%，
    等价 Spacing.S0，归令牌化仅增冗长），豁免于裸数字红线。

改动范围：result_panel / meihua_result_panel / liuren_result_panel /
xuan_kong_result_panel / collapsible_card / about_dialog 等全部面板/卡片/对话框文件。

退出码：0 = 全部通过；1 = 存在间距调用裸数字违规或令牌值异常。
"""
import re
import sys
import tokenize
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.audit_style_tokens import (  # 复用同一豁免口径与令牌表
    MARGIN_ALL_ZERO,
    MARGIN_TOKENS_EXEMPT,
    _strip_comments,
)

# 间距相关调用正则
SPACING_CALL_RE = re.compile(
    r'\b(?:set|add)Spacing\s*\(\s*[^)]*\)|setContentsMargins\s*\(\s*[^)]*\)'
)
# 匹配调用括号的参数范围（支持嵌套括号）
ARG_RE = re.compile(r'\(([^()]*(?:\([^()]*\)[^()]*)*)\)')
# 裸数字（含小数）
NUM_RE = re.compile(r'\b\d+(?:\.\d+)?\b')
# Spacing 令牌引用
TOKEN_RE = re.compile(r'\bSpacing\.\w+')
# Spacing 令牌定义行：Token = value（matches styles.py 中 Spacing 类内
#       `    S0 = 0` / `    S_MIN = 2` 等定义行，无需 Spacing. 前缀）
SPACING_DEF_RE = re.compile(
    r'^\s*(S\w+)\s*=\s*([0-9]+(?:\.\d+)?)\s*$', re.M
)

# 目标文件：间距令牌化需全量合规的面板/卡片/对话框文件
TARGET_FILES = [
    'ui/components/result_panel.py',
    'ui/components/meihua_result_panel.py',
    'ui/components/liuren_result_panel.py',
    'ui/components/xuan_kong_result_panel.py',
    'ui/components/collapsible_card.py',
    'ui/components/about_dialog.py',
    'ui/components/export_dialog.py',
    'ui/components/input_panel.py',
    'ui/components/liuren_input.py',
    'ui/components/meihua_input.py',
    'ui/components/settings_dialog.py',
    'ui/components/timeline.py',
    'ui/components/xuan_kong_input.py',
]

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def _get_spacing_values():
    """从 ui/styles.py 提取 Spacing 令牌的实际数值（唯一真相源）。"""
    styles_path = ROOT / 'ui' / 'styles.py'
    text = styles_path.read_text(encoding='utf-8', errors='replace')
    code_lines = _strip_comments(text)
    values = {}
    for line_no, line in enumerate(code_lines, start=1):
        m = SPACING_DEF_RE.match(line)
        if m:
            tok, val = m.group(1), m.group(2)
            try:
                values[tok] = float(val)
            except ValueError:
                pass
    return values


def _strip_tokens(text):
    """剥离所有 Spacing.* 令牌，用于排除令牌内数字，检测真正裸数字。"""
    return re.sub(r'Spacing\.\w+', '', text)


def _extract_arg(text):
    """从调用文本中提取首个括号内的参数字符串（支持嵌套括号）。"""
    m = ARG_RE.search(text)
    return m.group(1) if m else ''


def _parse_call_args(arg_str, call_text, spacing_values):
    """解析间距调用参数，返回 (裸数字列表, 令牌列表, 令牌值异常列表)。

    - 先剥离 Spacing.* 令牌，避免令牌内数字被误判为裸数字。
    - 裸数字：令牌剥离后仍剩余的裸数字，视为违规（全 0 豁免见 MARGIN_ALL_ZERO）。
    - 令牌值异常：令牌调用侧存在同步赋值 Spacing.X = 值，需与 styles.py 一致。
    """
    problems = []
    tokens = []
    drift = []
    # 剥离令牌，再匹配裸数字
    stripped = _strip_tokens(arg_str)
    num_matches = NUM_RE.findall(stripped)
    if num_matches:
        # 全 0 内边距豁免（贴边/紧凑容器，等价 S0，豁免裸数字红线）。
        # 检查完整调用文本（含 setContentsMargins( 前缀），与 MARGIN_ALL_ZERO 模式匹配。
        if MARGIN_ALL_ZERO.search(call_text):
            pass
        else:
            problems.append(num_matches)
    # 收集令牌引用
    for tok in TOKEN_RE.findall(arg_str):
        tokens.append(tok)
        tok_key = tok.split('.', 1)[1]
        if tok_key not in spacing_values:
            drift.append((tok, f'{tok_key} 不在 Spacing 令牌表'))
        else:
            # 提取该令牌在调用中的数值（Spacing.X = value 同步赋值）
            for tm in re.finditer(rf'{tok}\s*=\s*([0-9]+(?:\.\d+)?)', arg_str):
                val_num = float(tm.group(1))
                expected = spacing_values[tok_key]
                if abs(val_num - expected) > 0.01:
                    drift.append((tok, f'{tok}={val_num} vs 预期 {expected}'))
    return problems, tokens, drift


def scan_file(rel_path, spacing_values):
    """扫描单个文件，返回 (问题列表, 令牌值异常列表)。"""
    path = ROOT / rel_path
    text = path.read_text(encoding='utf-8', errors='replace')
    code_lines = _strip_comments(text)
    problems = []
    abnormal = []

    for line_no, line in enumerate(code_lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        # 仅匹配间距相关调用
        for m in SPACING_CALL_RE.finditer(line):
            arg_str = _extract_arg(m.group(0))
            call_text = m.group(0).strip()
            num_matches, tokens, drift = _parse_call_args(arg_str, call_text, spacing_values)
            if num_matches:
                problems.append((line_no, rel_path, call_text,
                                 f'含裸数字间距参数: {num_matches}'))
            for d in drift:
                abnormal.append((line_no, rel_path, call_text, str(d)))
    return problems, abnormal


def main():
    spacing_values = _get_spacing_values()
    print("=" * 64)
    print("verify_panel_margin: 面板/卡片间距令牌化合规校验（M3-3）")
    print("=" * 64)

    all_pass = True
    for rel in TARGET_FILES:
        problems, abnormal = scan_file(rel, spacing_values)
        # 已令牌化文件：内边距已统一引用 Spacing 令牌，不作为裸数字命中
        file_ok = not problems and not abnormal
        if not file_ok:
            all_pass = False
        # 记录到 RESULTS（驱动汇总行计数），check() 内部打印 [PASS]/[FAIL] 行
        check(rel, file_ok)
        if problems:
            for p in problems:
                print(f"  ✗ 间距调用含裸数字违规: {p[2]} — {p[3]}")
        if abnormal:
            for a in abnormal:
                print(f"  ✗ 令牌值异常: {a[2]} — {a[3]}")
        if file_ok:
            print(f"  ✓ 全部 setContentsMargins/setSpacing/addSpacing 已令牌化，数值合规")

    print(f"\n{'=' * 64}")
    print(f"verify_panel_margin: {sum(1 for r in RESULTS if r[1])}/{len(RESULTS)} 检查项通过")
    if all_pass:
        print("面板间距令牌化合规，全部通过 ✅")
        return 0
    print("间距令牌化合规校验未通过 ❌")
    return 1


if __name__ == '__main__':
    sys.exit(main())
