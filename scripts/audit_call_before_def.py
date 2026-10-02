# -*- coding: utf-8 -*-
"""AST 审计：嵌套函数的「调用早于定义」缺陷（ratchet）
================================================================
背景（真实事故）：`ui/components/ai_analysis_renderer.py` 的 `render_analysis`
内，嵌套函数 `_render_blocks` 被定义在函数**末尾**，却在更早的章节循环里被调用
→ `UnboundLocalError`；又因 `container` 直到函数末尾才挂载，导致整份 AI 解读
**静默渲染为空白**。而唯一的相关测试用 `try/except` 吞掉异常 → 假绿，长期未被发现。

本脚本遍历顶层函数（含方法），若某个**嵌套函数**（def 位于该函数体内的内联执行流）
在被定义之前就被内联调用，即判为缺陷。

判定要点：
- 只统计「内联执行流」中的调用——即**不**深入其它嵌套函数的函数体
  （那些体在后来才执行，属合法前向引用）。
- 但会深入 if/for/while/with/try 等复合语句体（它们立即执行）。
- 以行号比较：内联调用行 < 嵌套 def 行  → 命中。

用法：`python scripts/audit_call_before_def.py`
退出码：0=无缺陷；1=存在缺陷。
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCAN_DIRS = ('ui', 'core', 'service', 'scripts', 'tests')


def _collect_inline_calls(fn_node: ast.AST) -> dict:
    """收集 fn_node 内「会立即执行」语句中的调用名 → 最早出现的行号。

    不深入嵌套函数/Lambda 的函数体（其体延后执行，前向引用合法）。
    """
    calls: dict = {}

    def rec(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 装饰器与默认参数会在 def 语句处立即求值 → 需扫描
                for dec in getattr(child, 'decorator_list', None) or []:
                    rec(dec)
                rec(child.args)
                continue  # 跳过函数体
            if isinstance(child, ast.Lambda):
                rec(child.args)
                continue
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                calls.setdefault(child.func.id, child.func.lineno)
            rec(child)

    rec(fn_node)
    return calls


def _collect_nested_defs(fn_node: ast.AST) -> dict:
    """收集 fn_node 内联流中的嵌套函数定义 → {name: lineno}（不深入更深层）。"""
    defs: dict = {}

    def rec(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defs.setdefault(child.name, child.lineno)
                continue  # 不深入更深层嵌套
            rec(child)

    rec(fn_node)
    return defs


def _audit_tree(tree: ast.AST, rel: str) -> list:
    """返回该模块内的缺陷列表 [(rel, func_name, nested_name, call_line, def_line)]。"""
    findings = []

    def visit(fn):
        inline_calls = _collect_inline_calls(fn)
        nested_defs = _collect_nested_defs(fn)
        for name, def_line in nested_defs.items():
            call_line = inline_calls.get(name)
            if call_line is not None and call_line < def_line:
                findings.append((rel, fn.name, name, call_line, def_line))
        # 继续深入查找更深层的函数（如方法内的方法）
        for child in ast.iter_child_nodes(fn):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit(child)

    for top in ast.walk(tree):
        if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 只从顶层定义进入，避免重复
            pass
    for top in tree.body if hasattr(tree, 'body') else []:
        if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if isinstance(top, ast.ClassDef):
                for m in top.body:
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        visit(m)
            else:
                visit(top)
    return findings


def main() -> int:
    all_findings = []
    scanned = 0
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        for py in sorted(base.rglob('*.py')):
            rel = py.relative_to(ROOT).as_posix()
            if '__pycache__' in rel or '/build/' in rel:
                continue
            try:
                # utf-8-sig：兼容带 BOM 的源文件（否则 ast.parse 报 U+FEFF）
                src = py.read_text(encoding='utf-8-sig', errors='replace')
                tree = ast.parse(src)
            except SyntaxError as e:
                print(f"[WARN] 语法错误，跳过 {rel}: {e}")
                continue
            scanned += 1
            all_findings.extend(_audit_tree(tree, rel))

    print('=' * 64)
    if all_findings:
        for rel, fn, name, call_line, def_line in all_findings:
            print(f"[FAIL] {rel}: {fn}() 内联调用 '{name}' 于第 {call_line} 行，"
                  f"但定义在第 {def_line} 行 → UnboundLocalError 风险")
    else:
        print("未发现「调用早于定义」的嵌套函数缺陷 ✅")
    print(f"audit_call_before_def: 扫描 {scanned} 个 .py，发现 {len(all_findings)} 处缺陷")
    print('=' * 64)
    return 1 if all_findings else 0


if __name__ == '__main__':
    sys.exit(main())
