# -*- coding: utf-8 -*-
"""
文档字符串审计脚本（开发辅助工具）。

用途：
    静态扫描项目内的 Python 源文件，统计模块 / 类 / 函数三级的中文
    docstring 覆盖情况，输出缺失清单，便于批量补齐注释。

用法：
    python scripts/audit_docstrings.py            # 扫描默认目录
    python scripts/audit_docstrings.py core ui    # 只扫描指定目录
"""

import ast
import sys
from pathlib import Path

# 项目根目录（本文件位于 scripts/ 下，故上溯一级）
ROOT = Path(__file__).resolve().parent.parent

# 默认扫描目录：核心业务层、界面层、接口层、脚本层、测试层
DEFAULT_TARGETS = ['core', 'ui', 'api', 'scripts', 'tests']


def audit_file(path: Path):
    """审计单个 Python 文件的 docstring 覆盖情况。

    Args:
        path: 待审计的 .py 文件路径。

    Returns:
        tuple: (缺失条目列表, 总定义数)。缺失条目形如
               ``('func', '行号', '名称')``。
    """
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except (SyntaxError, UnicodeDecodeError) as exc:
        return [('parse-error', 0, str(exc))], 0

    missing, total = [], 0

    # 模块级 docstring
    total += 1
    if not ast.get_docstring(tree):
        missing.append(('module', 1, path.name))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            total += 1
            if not ast.get_docstring(node):
                kind = 'class' if isinstance(node, ast.ClassDef) else 'func'
                missing.append((kind, node.lineno, node.name))

    return missing, total


def main() -> int:
    """入口函数：遍历目标目录并打印审计报告。"""
    targets = sys.argv[1:] or DEFAULT_TARGETS

    files = []
    for target in targets:
        base = ROOT / target
        if base.is_dir():
            files.extend(sorted(base.rglob('*.py')))
        elif base.is_file():
            files.append(base)

    grand_total = grand_missing = 0
    for file in files:
        if '__pycache__' in file.parts:
            continue
        missing, total = audit_file(file)
        grand_total += total
        grand_missing += len(missing)
        if missing:
            rel = file.relative_to(ROOT).as_posix()
            print(f'{rel}  缺失 {len(missing)}/{total}')
            for kind, lineno, name in missing[:60]:
                print(f'    L{lineno:<5} [{kind}] {name}')

    covered = grand_total - grand_missing
    rate = (covered / grand_total * 100) if grand_total else 100.0
    print(f'\n合计：{covered}/{grand_total} 已注释，覆盖率 {rate:.1f}%')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
