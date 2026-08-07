# -*- coding: utf-8 -*-
"""
core/secure_log.py — 客户端日志与异常脱敏

作用：作为「兜底防线」，确保任何凭据都不会因为一句随手写的
      logger.exception / print / 崩溃堆栈而落进日志文件。

即便当前架构下客户端已不再持有上游 API 密钥，设备令牌仍属敏感凭据，
且未来若有人在客户端引入新的凭据，本模块可自动覆盖，无需逐处改代码。

用法（在程序入口调用一次即可）：
    from core.secure_log import install_log_scrubber
    install_log_scrubber()
"""
from __future__ import annotations

import logging
import re

MASK = '***REDACTED***'

# 覆盖常见凭据形态。宁可多打码，也不能漏。
_PATTERNS = [
    # OpenAI 风格密钥
    (re.compile(r'sk-[A-Za-z0-9_\-]{8,}'), lambda m: MASK),
    # Authorization: Bearer xxx
    (re.compile(r'(?i)(bearer\s+)[A-Za-z0-9_\-\.=]{8,}'), lambda m: m.group(1) + MASK),
    # key/token/secret/password 赋值形态
    (re.compile(r'(?i)\b(api[_-]?key|app[_-]?key|device[_-]?token|access[_-]?token'
                r'|admin[_-]?token|secret|password)(["\']?\s*[:=]\s*["\']?)([^\s"\',;}]{6,})'),
     lambda m: m.group(1) + m.group(2) + MASK),
    # 长串 URL-safe 令牌（设备令牌为 token_urlsafe(32)，约 43 字符）
    (re.compile(r'\b[A-Za-z0-9_\-]{40,}\b'), lambda m: MASK),
]


def scrub(text: str) -> str:
    """对任意文本做敏感信息打码。非字符串原样返回。"""
    if not isinstance(text, str) or not text:
        return text
    out = text
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    return out


class SecretScrubbingFilter(logging.Filter):
    """日志过滤器：对消息、参数、异常文本统一打码。"""

    def filter(self, record: logging.LogRecord) -> bool:
        """对日志记录的消息、格式化参数、异常文本统一脱敏；脱敏异常也不阻断日志。

        返回 True 表示放行该记录（脱敏只是就地改写消息内容，不丢弃日志）。
        """
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
            # 脱敏失败绝不能阻断日志写入
            pass
        return True


_installed = False


def install_log_scrubber() -> None:
    """把脱敏过滤器挂到 root logger 及其所有 handler（幂等）。"""
    global _installed
    if _installed:
        return

    scrubber = SecretScrubbingFilter()
    root = logging.getLogger()
    root.addFilter(scrubber)
    for handler in root.handlers:
        handler.addFilter(scrubber)

    # 已经创建过的具名 logger 也补挂一遍
    manager = logging.Logger.manager
    for name in list(manager.loggerDict.keys()):
        obj = manager.loggerDict.get(name)
        if isinstance(obj, logging.Logger):
            obj.addFilter(scrubber)
            for handler in obj.handlers:
                handler.addFilter(scrubber)

    _installed = True


def attach_to_logger(logger: logging.Logger) -> None:
    """给指定 logger 及其 handler 单独挂载脱敏过滤器。

    用于在 install_log_scrubber() 之后才创建的 logger / handler。
    """
    scrubber = SecretScrubbingFilter()
    logger.addFilter(scrubber)
    for handler in logger.handlers:
        handler.addFilter(scrubber)
