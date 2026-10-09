# -*- coding: utf-8 -*-
"""scripts/verify_build_security.py — 产物级密钥残留校验（发布门禁）
用法: python scripts/verify_build_security.py [dist_dir]
退出: 0=无残留可发布; 1=发现残留禁止发布; 2=参数/目录错误
"""
from __future__ import annotations
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIST = ROOT / "dist" / "风水排盘专业工具"

PATTERNS: list[tuple[str, bytes]] = [
    ("openai_style_key", rb"sk-[A-Za-z0-9]{20,}"),
    ("openrouter_key", rb"sk-or-v1-[A-Za-z0-9]{20,}"),
    ("bearer_token", rb"Bearer\s+[A-Za-z0-9_\-]{24,}"),
    ("api_key_assign", rb"api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"),
    ("endpoint_host", rb"agnes-ai\.cn"),
    ("embedded_module", rb"_embedded_config"),
]
TEXT_EXT = {".md", ".txt", ".log"}
SAMPLE_LIMIT = 8 * 1024 * 1024


def _read_bytes_for_scan(p: Path) -> bytes:
    size = p.stat().st_size
    if size <= SAMPLE_LIMIT * 2:
        return p.read_bytes()
    with p.open("rb") as f:
        head = f.read(SAMPLE_LIMIT)
        f.seek(-SAMPLE_LIMIT, 2)
        tail = f.read(SAMPLE_LIMIT)
    return head + tail


def scan(dist: Path) -> list[tuple[str, str, int]]:
    hits: list[tuple[str, str, int]] = []
    if not dist.is_dir():
        return hits
    for p in dist.rglob("*"):
        if not p.is_file() or p.suffix.lower() in TEXT_EXT:
            continue
        try:
            blob = _read_bytes_for_scan(p)
        except OSError:
            continue
        for name, pat in PATTERNS:
            n = len(re.findall(pat, blob))
            if n:
                hits.append((str(p.relative_to(dist)), name, n))
    return hits


def main() -> int:
    dist = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DIST
    if not dist.exists():
        print("[错误] 分发目录不存在：%s" % dist)
        return 2
    hits = scan(dist)
    total = sum(1 for p in dist.rglob("*") if p.is_file())
    print("[校验] 目录：%s" % dist)
    print("[校验] 文件总数：%d" % total)
    if not hits:
        print("[通过] 产物零密钥残留，可发布。")
        return 0
    print("[失败] 发现 %d 处疑似残留：" % len(hits))
    for fname, rule, n in hits[:50]:
        print("  - %s  [%s x%d]" % (fname, rule, n))
    return 1


if __name__ == "__main__":
    sys.exit(main())
