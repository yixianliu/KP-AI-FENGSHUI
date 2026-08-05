# -*- coding: utf-8 -*-
"""
server/app/config.py — 中转服务配置

所有敏感配置一律从「环境变量」读取，绝不落盘、绝不写入代码、绝不下发客户端。
本模块是上游 AI 密钥在整个系统中唯一的入口点。

安全约定：
  1. AGNES_API_KEY 只允许被 relay.py 读取用于构造上游请求头；
  2. Settings.__repr__ / __str__ 已重写为脱敏输出，防止配置对象被打印进日志；
  3. 缺少必需环境变量时「启动即失败」，避免服务带着空密钥裸奔。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import FrozenSet


class ConfigError(RuntimeError):
    """配置缺失或非法（启动期抛出，服务不应继续运行）。"""


def _require(name: str) -> str:
    val = os.environ.get(name, '').strip()
    if not val:
        raise ConfigError(
            f"缺少必需的环境变量 {name}。"
            f"请参考 server/.env.example 配置后再启动服务。"
        )
    return val


def _optional(name: str, default: str) -> str:
    val = os.environ.get(name, '').strip()
    return val or default


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, '').strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as e:
        raise ConfigError(f"环境变量 {name} 必须是整数，当前值非法") from e


def _csv_env(name: str) -> FrozenSet[str]:
    raw = os.environ.get(name, '').strip()
    if not raw:
        return frozenset()
    return frozenset(x.strip() for x in raw.split(',') if x.strip())


@dataclass(frozen=True)
class Settings:
    """服务配置。含密字段一律不进入 repr。"""

    # ---------- 上游 AI（机密，永不下发） ----------
    agnes_api_url: str
    agnes_api_key: str = field(repr=False)
    agnes_model: str

    # ---------- 客户端准入 ----------
    app_keys: FrozenSet[str] = field(repr=False)
    admin_token: str = field(repr=False)

    # ---------- 存储 ----------
    db_path: str

    # ---------- 配额与限流 ----------
    device_daily_quota: int
    global_daily_quota: int
    register_ip_daily_limit: int

    # ---------- 上游请求约束（控制成本与滥用） ----------
    upstream_timeout: int
    max_messages: int
    max_chars_per_request: int
    max_tokens_cap: int

    def __repr__(self) -> str:  # pragma: no cover - 仅用于日志安全
        return (
            f"Settings(agnes_api_url={self.agnes_api_url!r}, "
            f"agnes_model={self.agnes_model!r}, "
            f"agnes_api_key='***REDACTED***', "
            f"app_keys='***REDACTED***', admin_token='***REDACTED***', "
            f"db_path={self.db_path!r}, "
            f"device_daily_quota={self.device_daily_quota}, "
            f"global_daily_quota={self.global_daily_quota})"
        )

    __str__ = __repr__


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """读取并缓存配置。任何必需项缺失都会在此抛出，服务启动失败。"""
    app_keys = _csv_env('APP_KEYS')
    if not app_keys:
        raise ConfigError(
            "缺少必需的环境变量 APP_KEYS（逗号分隔的客户端准入密钥列表）。"
        )

    return Settings(
        agnes_api_url=_optional(
            'AGNES_API_URL', 'https://api.agnes-ai.cn/v1/chat/completions'
        ),
        agnes_api_key=_require('AGNES_API_KEY'),
        agnes_model=_optional('AGNES_MODEL', 'agnes-2.5-flash'),
        app_keys=app_keys,
        admin_token=_require('ADMIN_TOKEN'),
        db_path=_optional('RELAY_DB_PATH', 'relay.db'),
        device_daily_quota=_int_env('DEVICE_DAILY_QUOTA', 100),
        global_daily_quota=_int_env('GLOBAL_DAILY_QUOTA', 20000),
        register_ip_daily_limit=_int_env('REGISTER_IP_DAILY_LIMIT', 20),
        upstream_timeout=_int_env('UPSTREAM_TIMEOUT', 120),
        max_messages=_int_env('MAX_MESSAGES', 12),
        max_chars_per_request=_int_env('MAX_CHARS_PER_REQUEST', 24000),
        max_tokens_cap=_int_env('MAX_TOKENS_CAP', 2048),
    )
