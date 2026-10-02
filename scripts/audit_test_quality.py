# -*- coding: utf-8 -*-
"""audit_test_quality.py — 测试用例「假绿」模式审计（ratchet）

背景
----
2026-09-29 定位到一个严重缺陷：`ai_analysis_renderer.render_analysis` 因嵌套函数
「调用早于定义」抛 `UnboundLocalError`，导致三面板 AI 解读整份渲染为空白。
该缺陷能长期潜伏，**根因是唯一相关测试把断言包在 `try/except` 里只 print**——
静默 except 测试等于没有测试。

本脚本用 AST 扫描 `tests/`，把「写成了测试、但永远不可能失败」的代码揪出来：

1. DEFECT `return-non-none`
   `test_*` 函数体内 `return <非 None>`。pytest **完全忽略测试函数返回值**，
   因此 `return True/False` 表达的是「断言意图」，但实际零校验。

2. DEFECT `silent-except`
   `test_*` 函数体内的 `except`（裸 except 或 `except Exception`），其处理体
   既无 `raise` 也无 `assert`/`pytest.fail` —— 捕获异常后仅 print/pass，
   测试恒绿。这正是上面那个缺陷的藏身之处。

3. DEFECT `assert-in-try`
   `assert` 写在 `try/except Exception` 内部 —— `AssertionError` **也是** Exception，
   于是断言失败被自己的 except 吞掉，测试照旧通过。

4. WARN `vacuous-test`
   `test_*` 函数体内完全没有断言（`assert` / `pytest.raises|warns|fail`）。
   纯构造型 smoke 测试可能合法，故仅告警不 gate；如需保留请在 def 行尾加注释
   `# audit-test-quality: allow`。

用法
----
    ./venv/Scripts/python.exe scripts/audit_test_quality.py [--root tests] [--strict]

`--strict` 时 WARN 也计入失败。默认仅 DEFECT 决定退出码。
"""
from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ALLOW_MARK = 'audit-test-quality: allow'

# 断言判定：这些调用等价于「会失败」
_ASSERT_CALL_ATTRS = {'raises', 'warns', 'fail', 'xfail'}


def _is_assert_call(fn: ast.AST) -> bool:
    """调用是否属于断言族：pytest.raises / self.assertEqual / assertEqual 等。"""
    if isinstance(fn, ast.Attribute):
        return fn.attr in _ASSERT_CALL_ATTRS or fn.attr.startswith('assert')
    if isinstance(fn, ast.Name):
        return fn.id.startswith('assert')
    return False


@dataclass
class Finding:
    """一条审计结论。"""

    kind: str          # return-non-none | silent-except | vacuous-test
    path: Path
    lineno: int
    func: str

    @property
    def level(self) -> str:
        """vacuous-test 仅为告警，其余为缺陷。"""
        return 'WARN' if self.kind == 'vacuous-test' else 'DEFECT'


def _iter_test_funcs(tree: ast.AST):
    """产出模块级 / 类内的 `test_*` 函数（跳过被嵌套包裹的私有实现）。"""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith('test_'):
                yield node


def _walk_without_nested_funcs(node: ast.AST):
    """遍历节点，但不下钻到嵌套函数/lambda 体内部。

    嵌套函数体不属于被测函数自身的断言证据；若一个测试把校验委托给同模块
    辅助函数，应视为该辅助函数的责任，而不是在这里误判为「无断言」。
    """
    stack = list(ast.iter_child_nodes(node))
    while stack:
        cur = stack.pop()
        yield cur
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        stack.extend(ast.iter_child_nodes(cur))


def _handler_is_silent(handler: ast.ExceptHandler) -> bool:
    """except 处理体是否「静默」：既未把失败抛出，也未把失败记录下来。

    非静默（可见失败）的证据：
        - `raise`（含重抛）/ `assert`
        - `pytest.fail` / `pytest.xfail`
        - 收集证据的调用：`.append(...)` / `.extend(...)` / `.add(...)`
          （例如把「读不了的文件」记进 offenders，最终由断言暴露）
        - 以 error/critical/exception 级别记录
    仍然算静默：`pass` / `print(...)` / logger.warning / logger.info
    """
    for node in ast.walk(handler):
        if isinstance(node, (ast.Raise, ast.Assert)):
            return False
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute):
                if fn.attr in ('append', 'extend', 'add', 'fail', 'xfail'):
                    return False
                if fn.attr in ('error', 'critical', 'exception'):
                    return False
    return True


def _asserts_inside_try(func: ast.AST) -> list[int]:
    """返回「写在 try 块内、且该 try 有 Exception 级 handler」的 assert 行号。

    `AssertionError` 是 `Exception` 子类 → 断言失败会被自己的 except 吞掉，
    测试照旧通过。这是最隐蔽的一种假绿（本轮修掉 3 处）。
    """
    hits: list[int] = []
    for node in _walk_without_nested_funcs(func):
        if not isinstance(node, ast.Try):
            continue
        catches_assertion = any(
            h.type is None
            or (isinstance(h.type, ast.Name) and h.type.id in ('Exception', 'BaseException'))
            or isinstance(h.type, ast.Tuple)
            for h in node.handlers
        )
        if not catches_assertion:
            continue
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assert):
                hits.append(stmt.lineno)
    return hits


def _has_assertion(node: ast.AST) -> bool:
    """函数体内是否存在断言（含 pytest 风格的 raises/warns/fail/xfail）。"""
    for sub in _walk_without_nested_funcs(node):
        if isinstance(sub, ast.Assert):
            return True
        if isinstance(sub, ast.Call):
            if _is_assert_call(sub.func):
                return True
    return False


def _allowed(src_lines: list[str], func_lineno: int) -> bool:
    """def 行尾（含其上一行）是否带豁免标记。"""
    idx = func_lineno - 1
    if idx < 0 or idx >= len(src_lines):
        return False
    window = src_lines[max(0, idx - 1): idx + 1]
    return any(ALLOW_MARK in line for line in window)


def _audit_tree(tree: ast.AST, path: Path, src_lines: list[str]) -> list[Finding]:
    """对单个模块执行三类检查。"""
    findings: list[Finding] = []
    for func in _iter_test_funcs(tree):
        if _allowed(src_lines, func.lineno):
            continue

        # --- 1) return <非 None> ---
        for sub in _walk_without_nested_funcs(func):
            if isinstance(sub, ast.Return) and sub.value is not None:
                findings.append(Finding('return-non-none', path, sub.lineno, func.name))

        # --- 2) 静默 except ---
        for sub in _walk_without_nested_funcs(func):
            if isinstance(sub, ast.ExceptHandler) and _handler_is_silent(sub):
                findings.append(Finding('silent-except', path, sub.lineno, func.name))

        # --- 3) assert 写在 try/except Exception 内（断言被自己吞掉） ---
        for lineno in _asserts_inside_try(func):
            findings.append(Finding('assert-in-try', path, lineno, func.name))

        # --- 4) 无断言（告警） ---
        if not _has_assertion(func):
            findings.append(Finding('vacuous-test', path, func.lineno, func.name))

    return findings


def _iter_py_files(root: Path):
    """产出 root 下所有 .py（跳过 __pycache__）。"""
    for p in sorted(root.rglob('*.py')):
        if '__pycache__' in p.parts:
            continue
        yield p


def main(argv: list[str] | None = None) -> int:
    """入口：扫描并打印汇总，按缺陷数返回退出码。"""
    ap = argparse.ArgumentParser(description='测试假绿模式审计（ratchet）')
    ap.add_argument('--root', default='tests', help='待扫描目录，默认 tests')
    ap.add_argument('--strict', action='store_true', help='WARN 也视为失败')
    args = ap.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(f'[错误] 目录不存在：{root}')
        return 2

    all_findings: list[Finding] = []
    scanned = 0
    for path in _iter_py_files(root):
        scanned += 1
        try:
            # 7 个文件带 BOM，必须 utf-8-sig，否则 ast.parse 报 U+FEFF
            src = path.read_text(encoding='utf-8-sig')
            tree = ast.parse(src, filename=str(path))
        except SyntaxError as exc:  # 语法错误本身就是缺陷
            all_findings.append(Finding('syntax-error', path, exc.lineno or 0, '<module>'))
            continue
        all_findings.extend(_audit_tree(tree, path, src.splitlines()))

    defects = [f for f in all_findings if f.level == 'DEFECT']
    warns = [f for f in all_findings if f.level == 'WARN']

    print('=' * 64)
    print(f'扫描文件：{scanned} 个 .py（{root}）  缺陷 {len(defects)}  告警 {len(warns)}')
    print('=' * 64)

    for label, group in (('DEFECT', defects), ('WARN', warns)):
        if not group:
            continue
        print(f'\n[{label}]')
        for f in group:
            rel = f.path.relative_to(root.parent) if root.parent in f.path.parents else f.path
            print(f'  {rel}:{f.lineno}  {f.kind:<16} {f.func}()')

    if not defects and not (args.strict and warns):
        print('\n未发现「假绿」测试缺陷 ✅' if not warns
              else '\n未发现缺陷 ✅（告警见上，非门禁）')
        return 0

    if defects:
        print(f'\n发现 {len(defects)} 处假绿缺陷 ❌ —— 这些测试永远不可能失败')
        return 1
    print(f'\n[strict] 发现 {len(warns)} 处告警 ❌')
    return 1


if __name__ == '__main__':
    sys.exit(main())
