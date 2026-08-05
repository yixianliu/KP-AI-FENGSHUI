# -*- coding: utf-8 -*-
"""
scripts/verify_build_security.py — 打包产物密钥残留校验

用途：在发布前对 dist/ 做二进制级扫描，确认没有任何机密被打进客户端。
      这是「可验证的安全」，不依赖肉眼检查或主观判断。

发布约定：产物中【不含任何 AI 原始信息】—— 无端点、无密钥、无模型名。
        运行参数由用户在 GUI「设置」中自行填写，存于本机 ai_config.json。

校验逻辑：
  1. 若 server/.env 仍存在，读取其中的历史机密值（AGNES_API_KEY / ADMIN_TOKEN），
     断言它们【绝不出现】在任何产物文件中；
  2. 用通用正则扫描密钥形态、已知上游端点、内置模型名与已废弃的凭据模块名；
  3. 文件名级检查：config.ini / _embedded_config.py 等旧版凭据载体不得入包；
  4. APP_KEYS 属于历史上「设计上会随 exe 分发」的非机密，出现属正常，
     脚本会明确区分并给出提示，避免误报干扰判断；
  5. .exe / .zip 等二进制与压缩包均会被解开或按字节扫描。

用法：
    python scripts/verify_build_security.py
    python scripts/verify_build_security.py --dist dist --env server/.env

退出码：0 = 通过；1 = 发现机密残留；2 = 参数或环境错误
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

# 通用密钥形态 + AI 原始信息（端点 / 内置模型名 / 已废弃的凭据模块）
# 发布约定：产物中不得出现任何 AI 原始信息，用户自行在 GUI 填写。
_GENERIC_PATTERNS = [
    (re.compile(rb'sk-[A-Za-z0-9_\-]{16,}'), 'OpenAI 风格密钥 (sk-...)'),
    (re.compile(rb'Bearer\s+sk-'), '明文 Bearer 密钥'),
    (re.compile(rb'api\.agnes-ai\.cn'), '硬编码的上游端点'),
    (re.compile(rb'agnes-2\.5-(?:flash|pro)'), '硬编码的内置模型名'),
    (re.compile(rb'_embedded_config'), '已废弃的密钥烧录模块'),
]

# 这些文件名不得出现在产物中（旧版凭据载体）
_FORBIDDEN_FILENAMES = ('config.ini', '_embedded_config.py', '_embedded_config.pyc')

# 读取 .env 时，这些键属于机密，必须不出现在产物中
_SECRET_KEYS = ('AGNES_API_KEY', 'ADMIN_TOKEN')
# 这些键属于设计上会分发的非机密，出现在产物中属正常
_PUBLIC_KEYS = ('APP_KEYS',)

# 扫描时跳过的超大无关文件后缀（纯资源，不可能含密钥）
_SKIP_SUFFIXES = {'.qm', '.ttf', '.otf', '.png', '.jpg', '.jpeg', '.ico', '.svg'}

_CHUNK = 4 * 1024 * 1024


def parse_env(env_path: Path) -> Dict[str, str]:
    """极简 .env 解析，只取 KEY=VALUE。"""
    result: Dict[str, str] = {}
    if not env_path.exists():
        return result
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, val = line.partition('=')
        result[key.strip()] = val.strip()
    return result


def build_needles(env: Dict[str, str]) -> List[Tuple[bytes, str]]:
    """构造必须缺席的机密字节串列表。"""
    needles: List[Tuple[bytes, str]] = []
    for key in _SECRET_KEYS:
        raw = env.get(key, '').strip()
        if not raw:
            continue
        # AGNES_API_KEY 形如 "Bearer sk-xxx"，同时检查完整值与去前缀的令牌本体
        candidates = {raw}
        if raw.lower().startswith('bearer '):
            candidates.add(raw[7:].strip())
        for c in candidates:
            if len(c) >= 12:
                needles.append((c.encode('utf-8'), key))
    return needles


def iter_scan_targets(dist: Path):
    """产出 (显示名, 字节读取器) 。zip 会被解开逐条目扫描。"""
    for path in sorted(dist.rglob('*')):
        if not path.is_file():
            continue
        if path.suffix.lower() in _SKIP_SUFFIXES:
            continue
        rel = path.relative_to(dist)
        if path.suffix.lower() == '.zip':
            try:
                with zipfile.ZipFile(path) as zf:
                    for info in zf.infolist():
                        if info.is_dir() or info.file_size == 0:
                            continue
                        if Path(info.filename).suffix.lower() in _SKIP_SUFFIXES:
                            continue
                        try:
                            with zf.open(info) as fh:
                                yield f'{rel}::{info.filename}', fh.read()
                        except (RuntimeError, zipfile.BadZipFile, OSError):
                            continue
            except (zipfile.BadZipFile, OSError):
                yield f'{rel} (压缩包无法读取)', b''
            continue

        try:
            yield str(rel), path.read_bytes()
        except OSError:
            continue


def scan(dist: Path, env_path: Path) -> int:
    if not dist.exists():
        print(f'[错误] 产物目录不存在: {dist}')
        return 2

    env = parse_env(env_path)
    needles = build_needles(env)

    if not needles:
        print(f'[警告] 未能从 {env_path} 读到机密值，将仅执行通用模式扫描。')
    else:
        print(f'[信息] 已载入 {len(needles)} 条机密指纹用于比对（值不会被打印）')

    public_vals = {
        env.get(k, '').strip().encode('utf-8')
        for k in _PUBLIC_KEYS
        if env.get(k, '').strip()
    }

    # 文件名级检查：旧版凭据载体不得随产物分发
    forbidden_files = [
        str(p.relative_to(dist))
        for p in dist.rglob('*')
        if p.is_file() and p.name in _FORBIDDEN_FILENAMES
    ]

    secret_hits: List[str] = []
    generic_hits: List[str] = []
    public_hits: List[str] = []
    scanned = 0

    for name, data in iter_scan_targets(dist):
        if not data:
            continue
        scanned += 1

        for needle, key in needles:
            if needle in data:
                secret_hits.append(f'{name}  ←  {key}')

        for pattern, desc in _GENERIC_PATTERNS:
            m = pattern.search(data)
            if m:
                # 只显示前 8 字符，避免校验日志本身泄密
                snippet = m.group(0)[:8].decode('ascii', 'replace')
                generic_hits.append(f'{name}  ←  {desc}  (片段 {snippet}...)')

        for val in public_vals:
            if val in data:
                public_hits.append(name)

    print(f'[信息] 已扫描 {scanned} 个文件条目\n')

    ok = True

    if secret_hits:
        ok = False
        print('=' * 64)
        print('[失败] 产物中发现机密残留，禁止发布：')
        for h in secret_hits:
            print(f'   - {h}')
        print('=' * 64)

    if forbidden_files:
        ok = False
        print('[失败] 产物中出现旧版凭据载体文件，禁止发布：')
        for h in forbidden_files:
            print(f'   - {h}')
        print('   请先运行 scripts/purge_ai_secrets.py 后重新打包。')

    if generic_hits:
        ok = False
        print('[失败] 产物中发现 AI 原始信息残留（密钥 / 端点 / 内置模型名）：')
        for h in sorted(set(generic_hits)):
            print(f'   - {h}')

    if public_hits:
        uniq = sorted(set(public_hits))
        print(f'[正常] 客户端准入密钥出现在 {len(uniq)} 个条目中（设计如此，非机密）：')
        for h in uniq[:5]:
            print(f'   - {h}')
        if len(uniq) > 5:
            print(f'   ... 另有 {len(uniq) - 5} 项')
        print('       该密钥用于挡住随手刷接口的行为，泄露不影响上游密钥安全。\n')

    if ok:
        print('=' * 64)
        print('[通过] 产物中不含任何 AI 原始信息（端点 / 密钥 / 模型名），可以发布。')
        print('       用户首次运行需在「设置 → 龙虎山大师兄配置」中自行填写。')
        print('=' * 64)
        return 0
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description='打包产物密钥残留校验')
    parser.add_argument('--dist', default='dist', help='产物目录，默认 dist')
    parser.add_argument('--env', default='server/.env',
                        help='机密来源 .env，默认 server/.env')
    args = parser.parse_args()
    return scan(Path(args.dist), Path(args.env))


if __name__ == '__main__':
    sys.exit(main())
