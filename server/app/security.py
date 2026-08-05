# -*- coding: utf-8 -*-
"""
server/app/security.py — 令牌生成/校验与日志脱敏

设计要点：
  1. 设备令牌明文只在「注册响应」中出现一次，服务端仅存 SHA-256 摘要。
     即使数据库整库泄露，攻击者也拿不到可用令牌。
  2. 所有密钥比较使用 secrets.compare_digest，避免计时侧信道。
  3. SecretScrubbingFilter 挂到 root logger，对 sk-/Bearer/token 等模式做兜底打码，
     防止任何一处 logger.exception 意外把密钥写进日志。
"""
from __future__ import annotations

import hashlib
import logging
import re
import secrets
from typing import Iterable

# ------------------------------------------------------------------
# 令牌
# ------------------------------------------------------------------
_TOKEN_BYTES = 32


def new_device_token() -> str:
    """生成高熵设备令牌（URL 安全，约 43 字符）。"""
    return secrets.token_urlsafe(_TOKEN_BYTES)


def hash_token(token: str) -> str:
    """对令牌做 SHA-256 摘要，用于落库比对。"""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def token_matches_any(candidate: str, allowed: Iterable[str]) -> bool:
    """常量时间比对候选密钥是否命中允许列表，避免计时攻击。"""
    hit = False
    for item in allowed:
        # 不短路：始终遍历完整列表，保持耗时稳定
        if secrets.compare_digest(candidate, item):
            hit = True
    return hit


def constant_time_eq(a: str, b: str) -> bool:
    """常量时间字符串比较。"""
    return secrets.compare_digest(a, b)


# ------------------------------------------------------------------
# 日志脱敏
# ------------------------------------------------------------------
_SECRET_PATTERNS = [
    # OpenAI 风格密钥 sk-xxxxx
    re.compile(r'sk-[A-Za-z0-9_\-]{8,}'),
    # Authorization: Bearer xxxxx
    re.compile(r'(?i)(bearer\s+)[A-Za-z0-9_\-\.=]{8,}'),
    # 通用 token/key/secret 赋值形式
    re.compile(r'(?i)\b(api[_-]?key|access[_-]?token|secret|password)'
               r'(["\']?\s*[:=]\s*["\']?)([^\s"\',;}]{6,})'),
]

_MASK = '***REDACTED***'


def scrub(text: str) -> str:
    """对任意文本做敏感信息打码。"""
    if not text:
        return text
    out = text
    out = _SECRET_PATTERNS[0].sub(_MASK, out)
    out = _SECRET_PATTERNS[1].sub(lambda m: m.group(1) + _MASK, out)
    out = _SECRET_PATTERNS[2].sub(lambda m: m.group(1) + m.group(2) + _MASK, out)
    return out


class SecretScrubbingFilter(logging.Filter):
    """日志过滤器：对 msg 与 args 做敏感信息打码后再输出。"""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = scrub(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {
                        k: scrub(v) if isinstance(v, str) else v
                        for k, v in record.args.items()
                    }
                else:
                    record.args = tuple(
                        scrub(a) if isinstance(a, str) else a
                        for a in record.args
                    )
        except Exception:
            # 脱敏本身绝不能阻断日志
            pass
        return True


def install_log_scrubber() -> None:
    """把脱敏过滤器挂到 root logger 及所有已存在的 handler 上。"""
    scrubber = SecretScrubbingFilter()
    root = logging.getLogger()
    root.addFilter(scrubber)
    for handler in root.handlers:
        handler.addFilter(scrubber)
    # uvicorn 自带的 logger 也要覆盖
    for name in ('uvicorn', 'uvicorn.error', 'uvicorn.access', 'httpx'):
        lg = logging.getLogger(name)
        lg.addFilter(scrubber)
        for handler in lg.handlers:
            handler.addFilter(scrubber)
