"""
audit_pyflakes.py — 静态分析门禁（pyflakes）

第 8 轮确立的第三类探测器：门禁/测试全绿只证「被测路径」正确，
无法覆盖未被执行的代码 / 被 `except` 吞的异常 / 注解笔误。本脚本
把 pyflakes 形式化为可重复跑的硬门禁——**运行期 NameError 风险必须为 0**，
未用导入/f-string 未用本地只统计，不阻断日常改动。

设计要点：
- 用受管 Python 环境（`binaries/python/envs/default`）的 pyflakes 3.4.0，
  避免污染项目 venv
- 硬错误分类（RC=1）：`undefined name`（运行期 NameError 前兆）
- 信息性分类（仅统计）：`redefinition of unused`、`imported but unused`、
  `f-string is missing placeholders`、`assigned to but never used`
- 0 项守卫：扫到 0 项即 RC=1（门禁空转）
- 汇总行形如 `汇总: N 项 ...（基线 X）`，便于 gate_sweep 的 N/M 正则解析

历史基线：214 → 154 → 147 → 144 → **144**（2026-09-30 第 8 轮四续后）。
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 受管 Python 环境的 pyflakes（不污染项目 venv；项目 venv 无任何 linter）。
# 这是 2026-09-30 第 8 轮已确立的配置。
PYFLAKES_PY = (
    r"C:/Users/Administrator/.workbuddy/binaries/python/"
    r"envs/default/Scripts/python.exe"
)

# 扫哪些目录：覆盖全部产品代码 + 脚本；tests/ 与 tools/manual/ 不进硬门禁
# （前者由 pytest 覆盖，后者是手工调试脚本）。
SCAN_DIRS = ['ui', 'core', 'service', 'api', 'ai', 'scripts', 'tools']

# 硬错误分类（运行期风险）。regex 命中 → RC=1。
# 注：`redefinition of unused` 也属运行期风险（被前一步 finally 删掉留下的
# `entered` 类遗物标记），但已知的「有意惰性导入」雷区（`_lazy_init`）需白名单，
# 故此处只把 `undefined name` 当硬错误，redefinition 留为信息项 + 由人审。
HARD_ERROR_PATTERNS = [
    re.compile(r"\bundefined name\b"),
]

# 信息分类 regex（仅用于分类统计；不阻断）
INFO_PATTERNS = {
    'unused_import': re.compile(r"\bimported but unused\b"),
    'unused_local': re.compile(r"\bassigned to but never used\b"),
    'f_string': re.compile(r"\bf-string is missing placeholders\b"),
    'redefinition': re.compile(r"\bredefinition of unused\b"),
}

# 历史基线（2026-09-30 第 8 轮四续后）
BASELINE_TOTAL = 144


def run_pyflakes() -> subprocess.CompletedProcess:
    """在受管环境跑 pyflakes，捕获完整 stdout。"""
    env = os.environ.copy()
    env.setdefault('QT_QPA_PLATFORM', 'offscreen')
    return subprocess.run(
        [PYFLAKES_PY, '-m', 'pyflakes', *SCAN_DIRS],
        cwd=str(ROOT), env=env,
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        timeout=120,
    )


def classify(lines: list[str]) -> dict[str, list[str]]:
    """把 pyflakes 输出按四类信息分类。"""
    buckets = {k: [] for k in INFO_PATTERNS}
    buckets['hard_error'] = []
    for ln in lines:
        if any(rx.search(ln) for rx in HARD_ERROR_PATTERNS):
            buckets['hard_error'].append(ln)
        for k, rx in INFO_PATTERNS.items():
            if rx.search(ln):
                buckets[k].append(ln)
                break
    return buckets


def main() -> int:
    print('=== pyflakes 静态分析门禁 ===')
    print(f'扫描目录: {", ".join(SCAN_DIRS)}')
    print(f'Pyflakes: {PYFLAKES_PY}')
    print(f'基线总项: {BASELINE_TOTAL}')
    print('-' * 64)

    r = run_pyflakes()
    lines = [ln for ln in (r.stdout or '').splitlines() if ln.strip()]
    total = len(lines)

    # 0 项守卫：与「vacuous gate」同形态——若空反回
    if total == 0:
        print('audit_pyflakes: 扫描到 0 项 —— 门禁空转 ❌')
        print('（检查扫描目录是否正确；可能所有目录都被排除或 pyflakes 已卸载）')
        return 1

    buckets = classify(lines)

    # 打印分类明细
    print(f'总项: {total}')
    for k in ('hard_error', 'redefinition', 'unused_import',
              'f_string', 'unused_local'):
        print(f'  {k}: {len(buckets[k])}')

    # 硬错误样本（最多 10 条）
    if buckets['hard_error']:
        print('-' * 64)
        print(f'[!] {len(buckets["hard_error"])} 项运行期 NameError 风险（硬错误）:')
        for ln in buckets['hard_error'][:10]:
            print(f'    {ln}')
        if len(buckets['hard_error']) > 10:
            print(f'    ... 还有 {len(buckets["hard_error"]) - 10} 项')

    # 汇总行（gate_sweep N/M 正则可解析）
    print('=' * 64)
    rc_zero = int(not buckets['hard_error'])
    total_checks = 1  # 一个硬检查
    print(f'汇总: {rc_zero}/{total_checks} 项硬错误检查通过 '
          f'（总项 {total}，基线 {BASELINE_TOTAL}，'
          f'增量 {total - BASELINE_TOTAL:+d}）')

    if buckets['hard_error']:
        print(f'audit_pyflakes: {len(buckets["hard_error"])} 项硬错误（运行期 NameError 风险）❌')
        return 1
    print('audit_pyflakes: 无硬错误，pyflakes 形式化巡检通过 ✅')
    return 0


if __name__ == '__main__':
    sys.exit(main())