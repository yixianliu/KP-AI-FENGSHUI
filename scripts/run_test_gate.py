# -*- coding: utf-8 -*-
"""
scripts/run_test_gate.py — 逐文件独立子进程测试门禁

背景：全量 `pytest` 在同一进程里跑完 1000+ 个用例时，解释器退出阶段会偶发
进程级访问冲突（0xC0000005 / -1073741819）。已证实这不是某个坏文件，
而是同进程累积 7500+ 控件后的退出期析构问题（详见
docs/reports/report_exit_crash_p0p1p2.md）。

因此门禁改为「一个测试文件一个子进程」：
- 每个文件独立跑 `pytest <file> -q`；
- **判定必须看子进程退出码**（崩溃码同样是失败），不能只看输出里有没有 "passed"；
- 汇总每个文件的 passed / failed / exit code，任一非 0 则整轮失败。

用法：
    python scripts/run_test_gate.py              # 跑 1 轮
    python scripts/run_test_gate.py --rounds 3   # 连跑 3 轮
    python scripts/run_test_gate.py --files tests/ui/test_panels.py  # 仅指定文件
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# 单个文件最长允许 10 分钟（正常文件 1~100s，超时视为异常）
PER_FILE_TIMEOUT = 600
_RE_PASSED = re.compile(r'(\d+) passed')
_RE_FAILED = re.compile(r'(\d+) failed')
_RE_ERROR = re.compile(r'(\d+) error')
_RE_SKIPPED = re.compile(r'(\d+) skipped')


def collect_test_files() -> list[str]:
    """用 pytest 自身收集结果确定测试文件（尊重 pytest.ini 的 testpaths/命名规则）。"""
    proc = subprocess.run(
        [sys.executable, '-m', 'pytest', '--collect-only', '-q'],
        cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    files: set[str] = set()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if '::' in line and not line.startswith('='):
            files.add(line.split('::')[0])
    # 兜底：收集解析失败时按文件名约定扫描（排除 conftest）
    if not files:
        files = {str(p.relative_to(ROOT)).replace('\\', '/')
                 for p in ROOT.glob('tests/**/test_*.py')}
    return sorted(files)


def run_one(py: str, rel_file: str) -> dict:
    """跑单个测试文件，返回 {exit, passed, failed, error, skipped, sec, crash}."""
    env = dict(os.environ)
    env.setdefault('PYTHONFAULTHANDLER', '1')
    env.setdefault('QT_QPA_PLATFORM', 'offscreen')
    t0 = time.time()
    try:
        proc = subprocess.run(
            [py, '-m', 'pytest', rel_file, '-q'],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=PER_FILE_TIMEOUT, env=env,
        )
        out, code = (proc.stdout or '') + (proc.stderr or ''), proc.returncode
    except subprocess.TimeoutExpired:
        out, code = '', -999  # -999 自定义：超时
    sec = time.time() - t0
    m_p = _RE_PASSED.search(out)
    m_f = _RE_FAILED.search(out)
    m_e = _RE_ERROR.search(out)
    m_s = _RE_SKIPPED.search(out)
    return {
        'file': rel_file,
        'exit': code,
        'passed': int(m_p.group(1)) if m_p else 0,
        'failed': int(m_f.group(1)) if m_f else 0,
        'error': int(m_e.group(1)) if m_e else 0,
        'skipped': int(m_s.group(1)) if m_s else 0,
        'sec': sec,
        # 崩溃特征：退出码非 0 且输出里没有 pytest 汇总行
        'crash': code != 0 and not m_p and not m_f,
        'timeout': code == -999,
    }


def run_round(py: str, files: list[str], idx: int) -> dict:
    """跑一轮（全部文件各起一个子进程），打印明细并返回汇总。"""
    print(f'\n=== ROUND {idx} ===  files={len(files)}')
    rows = []
    t0 = time.time()
    for i, f in enumerate(files, 1):
        r = run_one(py, f)
        rows.append(r)
        flag = 'OK  ' if (r['exit'] == 0 and r['failed'] == 0) else 'FAIL'
        extra = ''
        if r['timeout']:
            extra = ' TIMEOUT'
        elif r['crash']:
            extra = ' CRASH(no-summary)'
        print(f'[{i:02d}/{len(files)}] {flag} exit={r["exit"]:<12} '
              f'passed={r["passed"]:<4} failed={r["failed"]:<3} err={r["error"]:<2} '
              f'{r["sec"]:7.1f}s  {f}{extra}')
        sys.stdout.flush()
    total_sec = time.time() - t0
    bad = [r for r in rows if r['exit'] != 0 or r['failed'] > 0 or r['error'] > 0]
    total_passed = sum(r['passed'] for r in rows)
    print(f'--- ROUND {idx} SUMMARY: files={len(rows)} ok={len(rows) - len(bad)} '
          f'bad={len(bad)} passed={total_passed} '
          f'failed={sum(r["failed"] for r in rows)} '
          f'total={total_sec:.1f}s')
    if bad:
        print(f'--- ROUND {idx} NON-ZERO EXIT ({len(bad)}):')
        for r in bad:
            kind = 'TIMEOUT' if r['timeout'] else ('CRASH' if r['crash'] else 'FAILED')
            print(f'    {kind} exit={r["exit"]} failed={r["failed"]} '
                  f'err={r["error"]} {r["file"]}')
    return {'round': idx, 'total': len(rows), 'bad': len(bad),
            'passed': total_passed, 'sec': total_sec, 'bad_rows': bad}


def main() -> int:
    ap = argparse.ArgumentParser(description='逐文件独立子进程测试门禁')
    ap.add_argument('--rounds', type=int, default=1, help='连跑轮数（默认 1）')
    ap.add_argument('--files', nargs='*', help='只跑指定文件（相对项目根路径）')
    args = ap.parse_args()

    py = sys.executable
    files = args.files if args.files else collect_test_files()
    print(f'[gate] python={py}')
    print(f'[gate] files={len(files)} rounds={args.rounds}')

    results = [run_round(py, files, i) for i in range(1, args.rounds + 1)]

    print('\n=== GATE SUMMARY ===')
    ok = True
    for r in results:
        status = 'PASS' if r['bad'] == 0 else 'FAIL'
        print(f'round {r["round"]}: {status} files={r["total"]} bad={r["bad"]} '
              f'passed={r["passed"]} total={r["sec"]:.1f}s')
        if r['bad']:
            ok = False
    print(f'[gate] RESULT: {"PASS" if ok else "FAIL"}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
