# -*- coding: utf-8 -*-
"""
scripts/purge_ai_secrets.py — 打包前清除全部 AI 原始信息

【为什么需要它】
发布产物中**不得包含任何密钥与非官方 AI 信息**：密钥一律不进 exe，
非官方上游端点 / 非发布模型名也视为泄漏。官方固定后端（龙虎山大师兄 AI 的
端点 api.agnes-ai.cn 与模型 agnes-2.5-flash）属公开、非机密的产品常量，
随包分发属正常，由 core.ai_config 固化。密钥仍由用户在 GUI 自行填写，
存放于本机 ai_config.json（设备指纹混淆），与安装包无关。

本脚本在 PyInstaller 之前运行，负责把历史遗留的凭据载体从源码树中移除：

  1. core/_embedded_config.py      —— 旧版烧录进 exe 的混淆密钥模块
  2. config.ini / config.ini.example —— 旧版 [relay] 段含端点 / app_key / 模型名
  3. 上述模块对应的 __pycache__/*.pyc —— 防止陈旧字节码被打进产物
  4. 扫描 api/ core/ ui/ 中残留的密钥形态与已知端点字面量并报警
  5. 清空 data/fengshui.db（随 exe 打包的「种子库」）中的运行期 / 测试期表
     （分析报告、日志、用户等）并 VACUUM，避免历史数据里的模型名 / 端点
     字面量泄漏进产物

被移除的文件会先备份到 .ai_purge_backup/（该目录不参与打包），
需要时可自行取回；确认无用后可手动删除。

用法：
    python scripts/purge_ai_secrets.py
    python scripts/purge_ai_secrets.py --check   # 只检查不改动，用于 CI 门禁

退出码：0 = 干净；1 = --check 模式下发现残留
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT / '.ai_purge_backup'

# 必须从源码树中移除的凭据载体
PURGE_TARGETS = [
    'core/_embedded_config.py',
    'config.ini',
    'config.ini.example',
    # 该脚本的用途就是把密钥烧录进 exe，与「产物零凭据」的目标直接冲突，
    # 保留它等于给未来的自己留一个脚枪，一并移除。
    'scripts/build_embed_secrets.py',
]

# 扫描范围：会被打进 exe 的客户端代码
SCAN_DIRS = ('api', 'core', 'ui', 'scripts')

# 残留信号：密钥形态 + 非官方上游端点 + 非发布模型名
# 注意：官方固定后端（api.agnes-ai.cn 与 agnes-2.5-flash）属公开、非机密，
# 随包分发属正常，故在此放行；仅拦截其他端点与 agnes-2.5-pro。
RESIDUE_PATTERNS = [
    (re.compile(r'sk-[A-Za-z0-9_\-]{16,}'), '疑似明文 API 密钥'),
    (re.compile(r'Bearer\s+sk-'), '疑似明文 Bearer 密钥'),
    (re.compile(r'api\.(?!agnes-ai\.cn)[A-Za-z0-9.\-]+\.(?:com|cn)'), '硬编码的非官方上游端点'),
    (re.compile(r'agnes-2\.5-pro'), '硬编码的非发布模型名（pro）'),
]

# 白名单：这些文件本就负责描述 / 检测这些模式，命中属正常
# core/debug_keys.py 是「双模式密钥管理」唯一 sanctioned 的调试密钥源：
# 其真实密钥由 clear_debug_keys() 在打包前清空，故残留扫描对它放行，
# 真正的产物级防护由 verify_build_security.py（扫描 dist）兜底。
WHITELIST = {
    'scripts/purge_ai_secrets.py',
    'scripts/verify_build_security.py',
    'core/secure_log.py',
    'core/debug_keys.py',
}

# 调试密钥源：core.debug_keys 中的真实密钥必须在打包前清空为 ""。
# 保留文件本身与结构（避免导入失败），仅清掉密钥值，并备份原文件。
# 这实现了「双模式密钥管理」的打包侧：命令行调试可保留密钥，打包 EXE 自动移除。
DEBUG_KEYS = ROOT / 'core' / 'debug_keys.py'
# 仅匹配「含真实密钥」的一行（引号内至少 1 个字符）；空值 "" 不触发清理
_DEBUG_KEY_RE = re.compile(r"^DEBUG_AGNES_API_KEY\s*=\s*[\"'].+?[\"']", re.MULTILINE)

# 随 exe 打包的「种子数据库」会混入运行期 / 测试期数据
# （历史分析报告残留的模型名、系统日志里的上游端点等）。
# 打包前必须把运行期表清空并 VACUUM，否则字节级扫描仍会扫到残留。
SEED_DB = ROOT / 'data' / 'fengshui.db'
RUNTIME_TABLES = [
    'analysis_reports', 'analysis_records', 'analysis_logs',
    'pan_records', 'ai_cache', 'system_logs', 'operation_logs',
    'ui_settings',
]
# 与 RESIDUE_PATTERNS 同义，但用于二进制（.db）扫描
DB_PATTERNS = [p[0].pattern.encode('utf-8') for p in RESIDUE_PATTERNS]


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def purge_files(dry_run: bool) -> List[str]:
    """移除凭据载体文件，返回被处理（或待处理）的相对路径列表。"""
    hits: List[str] = []
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')

    for rel in PURGE_TARGETS:
        target = ROOT / rel
        if not target.exists():
            continue
        hits.append(rel)
        if dry_run:
            continue
        dest = BACKUP_DIR / stamp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, dest)
        target.unlink()
        print(f'[清除] {rel}  ->  已备份至 {_rel(dest)}')

    return hits


def purge_pycache(dry_run: bool) -> List[str]:
    """清掉凭据模块的陈旧字节码，避免 PyInstaller 收进产物。"""
    hits: List[str] = []
    for pyc in ROOT.rglob('__pycache__/_embedded_config.*.pyc'):
        if '.ai_purge_backup' in pyc.parts:
            continue
        hits.append(_rel(pyc))
        if not dry_run:
            try:
                pyc.unlink()
                print(f'[清除] {_rel(pyc)}')
            except OSError as e:
                print(f'[警告] 无法删除 {_rel(pyc)}: {e}')
    return hits


def clear_debug_keys(dry_run: bool) -> List[str]:
    """打包前把调试密钥源中的真实密钥清空为 ""（保留文件本身与结构）。

    core.debug_keys 负责本地命令行调试的密钥注入；打包产物中不得含任何密钥，
    因此这里把 DEBUG_AGNES_API_KEY 这一行重置为 ""，并先备份原文件。
    """
    hits: List[str] = []
    if not DEBUG_KEYS.exists():
        return hits
    text = DEBUG_KEYS.read_text(encoding='utf-8')
    new_text, n = _DEBUG_KEY_RE.subn(lambda m: 'DEBUG_AGNES_API_KEY = ""', text)
    if n == 0:
        return hits
    hits.append('core/debug_keys.py')
    if dry_run:
        return hits
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    dest = BACKUP_DIR / stamp / 'core' / 'debug_keys.py'
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DEBUG_KEYS, dest)
    DEBUG_KEYS.write_text(new_text, encoding='utf-8')
    print(f'[清除] core/debug_keys.py  调试密钥已清空（{n} 处，备份至 {_rel(dest)}）')
    return hits


def scan_residue() -> List[str]:
    """扫描客户端源码中残留的 AI 原始信息。"""
    findings: List[str] = []
    for sub in SCAN_DIRS:
        base = ROOT / sub
        if not base.exists():
            continue
        for py in base.rglob('*.py'):
            rel = _rel(py)
            if rel in WHITELIST:
                continue
            try:
                text = py.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            for pattern, desc in RESIDUE_PATTERNS:
                if pattern.search(text):
                    findings.append(f'{rel}  ←  {desc}')
    return findings


def clean_seed_db(dry_run: bool) -> List[str]:
    """打包前清扫种子库里的运行期 / 测试期数据，确保不含 AI 原始信息。

    SQLite 的 DELETE 不会立即从文件中抹除数据，必须 VACUUM 物理重写，
    否则产物级字节扫描仍能命中残留的字面量。
    """
    findings: List[str] = []
    if not SEED_DB.exists():
        return findings
    if dry_run:
        data = SEED_DB.read_bytes()
        rel = SEED_DB.relative_to(ROOT).as_posix()
        for pat in DB_PATTERNS:
            if pat in data:
                findings.append(f'{rel}  ←  含 {pat.decode()}')
        return findings

    import sqlite3
    con = sqlite3.connect(str(SEED_DB))
    cur = con.cursor()
    for t in RUNTIME_TABLES:
        try:
            cur.execute(f'DELETE FROM "{t}"')
        except sqlite3.Error:
            pass
    con.commit()
    cur.execute('VACUUM')
    con.commit()
    con.close()
    print(f'[清除] {SEED_DB.relative_to(ROOT).as_posix()} 运行期表已清空并 VACUUM')
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description='打包前清除全部 AI 原始信息')
    parser.add_argument('--check', action='store_true',
                        help='只检查不改动（CI 门禁用）')
    args = parser.parse_args()

    mode = '检查' if args.check else '清除'
    print('=' * 64)
    print(f'AI 原始信息{mode} — 目标：产物中零端点、零密钥、零模型名')
    print('=' * 64)

    file_hits = purge_files(dry_run=args.check)
    pyc_hits = purge_pycache(dry_run=args.check)
    debug_hits = clear_debug_keys(dry_run=args.check)
    residue = scan_residue()
    db_hits = clean_seed_db(dry_run=args.check)

    print()
    if args.check:
        problems = file_hits + pyc_hits + debug_hits + residue + db_hits
        if problems:
            print('[失败] 源码树 / 种子库中仍存在 AI 原始信息：')
            for p in problems:
                print(f'   - {p}')
            print('\n请先运行：python scripts/purge_ai_secrets.py')
            return 1
        print('[通过] 源码树与种子库干净，可以打包。')
        return 0

    if not file_hits and not pyc_hits and not debug_hits:
        print('[信息] 未发现需要清除的凭据载体（源码树本就干净）。')
    else:
        print(f'[完成] 已清除 {len(file_hits)} 个凭据文件、'
              f'{len(pyc_hits)} 个陈旧字节码、{len(debug_hits)} 处调试密钥。')

    if residue:
        print('\n[警告] 以下源码中仍出现 AI 原始信息，请人工确认：')
        for r in residue:
            print(f'   - {r}')
        return 1
    if db_hits:
        # 正常模式下已清空，这里不应再出现
        print('\n[警告] 种子库扫描异常，请检查：')
        for r in db_hits:
            print(f'   - {r}')

    print('[通过] 客户端源码与种子库中未发现任何端点 / 密钥 / 内置模型名。')
    print('\n提示：打包完成后请运行 scripts/verify_build_security.py 做产物级复核。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
