"""
audit_complexity.py — 静态分析门禁（radon Cyclomatic Complexity）

与 audit_pyflakes 并列的第二类静态分析维度：门禁/测试全绿只证「被测路径」
正确，pyflakes 只抓运行期 NameError 风险，但「能跑通且短小」≠「设计合理」。
radon CC（圈复杂度）把「难以维护的巨型函数」量化：CC 越高，路径越多，
单测覆盖成本指数级上升，且几乎一定藏 bug。

设计要点：
- 用受管 Python 环境（`binaries/python/envs/default`）的 radon，避免污染项目 venv
- 扫 ui/core/service/api/ai；tests/ 与 tools/manual/ 不进（前者自解释方法名，后者手稿）
- 硬阈值：D=21 起（即 D/E/F 三级合并）。基线 = 当前 D/F 数量（天花板式），
  仅在「新增 D/F 级方法」时 RC=1，**不**对「清理 / 拆分后 D/F 减少」误报。
- 0 项守卫：扫到 0 项即 RC=1（门禁空转）
- 汇总行形如 `汇总: N 项 ...（基线 X）`，便于 gate_sweep 的 N/M 正则解析

历史基线：radon CC 首次跑出 D/F = 7（详见 docs/UI_UPGRADE_PLAN.md §15.19）
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 受管 Python 环境的 radon（与 audit_pyflakes 用同一个环境；项目 venv 无 linter）
RADON_PY = (
    r"C:/Users/Administrator/.workbuddy/binaries/python/"
    r"envs/default/Scripts/python.exe"
)

SCAN_DIRS = ['ui', 'core', 'service', 'api', 'ai']

# 硬阈值：rank in {'D', 'E', 'F'}（CC ≥ 21）。A/B/C 仅统计不阻断。
HIGH_COMPLEXITY_RANKS = {'D', 'E', 'F'}

# 基线 = 当前 D/F 数量（天花板式；可通过清理/拆分降低，但绝不因 R1C2 误报）
# 2026-10-01 第 8 轮十九续首次扫全项目：F=6, E=4, D=14 → 总 24
BASELINE_TOTAL = 24


def run_radon() -> subprocess.CompletedProcess:
    """在受管环境跑 radon cc -j（JSON 输出），捕获完整 stdout。"""
    env = os.environ.copy()
    env.setdefault('QT_QPA_PLATFORM', 'offscreen')
    return subprocess.run(
        [RADON_PY, '-m', 'radon', 'cc', '-s', '-j', *SCAN_DIRS],
        cwd=str(ROOT), env=env,
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        timeout=180,
    )


def collect_high_complexity() -> list[dict]:
    """解析 radon JSON 输出，返回所有 rank ∈ {D, E, F} 的方法/函数清单。

    radon JSON 结构：`{file: [{type, name, rank, complexity, lineno, classname?}, ...]}`。
    """
    r = run_radon()
    try:
        data = json.loads(r.stdout or '{}')
    except json.JSONDecodeError as e:
        print(f'audit_complexity: radon 输出无法解析为 JSON（{e}）')
        print('--- 原始输出（前 20 行）---')
        for ln in (r.stdout or '').splitlines()[:20]:
            print(f'    {ln}')
        return []

    out: list[dict] = []
    parse_errors: list[tuple[str, str]] = []
    for fpath, items in data.items():
        # radon 解析失败的文件（如 BOM 让 ast 报错）会返回 dict 而非 list
        if isinstance(items, dict):
            if 'error' in items:
                parse_errors.append((fpath, items['error']))
            continue
        for it in items:
            if it.get('rank') in HIGH_COMPLEXITY_RANKS:
                out.append({
                    'file': fpath,
                    'name': it.get('name', ''),
                    'classname': it.get('classname', ''),
                    'rank': it['rank'],
                    'cc': it['complexity'],
                    'lineno': it['lineno'],
                    'type': it.get('type', 'function'),
                })
    out.sort(key=lambda x: (x['rank'] != 'F', x['rank'] != 'E', -x['cc']))
    return out, parse_errors


def main() -> int:
    print('=== radon 圈复杂度静态分析门禁 ===')
    print(f'扫描目录: {", ".join(SCAN_DIRS)}')
    print(f'Radon: {RADON_PY}')
    print(f'硬阈值: rank ∈ {sorted(HIGH_COMPLEXITY_RANKS)}（CC ≥ 21）')
    print(f'基线 D+F 数量: {BASELINE_TOTAL}')
    print('-' * 64)

    items, parse_errors = collect_high_complexity()
    total = len(items)

    # 0 项守卫：vacuous gate —— 扫描器若崩（环境错、目录空），必须立即 RC=1
    if total == 0:
        if parse_errors:
            # 所有文件都被 BOM 卡住 → radon 全军覆没，仍视为空转
            print(f'audit_complexity: D/F 数量为 0，但 {len(parse_errors)} 个文件解析失败 —— 门禁空转 ❌')
            return 1
        print('audit_complexity: 扫描到 0 项 D/F 级方法 —— 门禁空转 ❌')
        print('（检查 radon 是否安装、扫描目录是否正确）')
        return 1

    # 分类统计
    by_rank: dict[str, int] = {}
    for it in items:
        by_rank[it['rank']] = by_rank.get(it['rank'], 0) + 1

    print(f'总项: {total}')
    for rank in ('D', 'E', 'F'):
        print(f'  rank={rank}: {by_rank.get(rank, 0)}')

    # 打印明细（按 rank 降序 + CC 降序）
    print('-' * 64)
    print('[!] D/F 级方法清单:')
    for it in items:
        loc = f"{it['file']}:{it['lineno']}"
        qualname = (f"{it['classname']}.{it['name']}" if it.get('classname')
                    else it['name'])
        print(f'    {it["rank"]} CC={it["cc"]:>2}  {loc:<48}  {qualname}')

    if parse_errors:
        print('-' * 64)
        print(f'[!] {len(parse_errors)} 个文件 radon 解析失败（BOM 等）——'
              f'其 CC 数据全部丢失:')
        for fpath, err in parse_errors:
            print(f'    {fpath}: {err[:80]}')
        print('（建议清理为 utf-8-sig → utf-8；这些文件此前 audit_docstrings 同样无法解析）')

    # 汇总行（gate_sweep N/M 正则可解析）
    print('=' * 64)
    rc_zero = int(total <= BASELINE_TOTAL)
    total_checks = 1  # 一个硬检查（D/F 数量是否在基线下）
    print(f'汇总: {rc_zero}/{total_checks} 项硬检查通过 '
          f'（D+F 总 {total}，基线 {BASELINE_TOTAL}，'
          f'增量 {total - BASELINE_TOTAL:+d}）')

    if total > BASELINE_TOTAL:
        print(f'audit_complexity: D/F 级方法数 {total} 超过基线 {BASELINE_TOTAL} ❌')
        print('（请拆分巨型方法；radon 阈值参考：A≤5/B≤10/C≤20/D≤30/E≤40/F≤50）')
        return 1
    print('audit_complexity: D/F 数量 ≤ 基线，复杂度巡检通过 ✅')
    return 0


if __name__ == '__main__':
    sys.exit(main())