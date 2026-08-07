# -*- coding: utf-8 -*-
"""
core/device_identity.py — 设备指纹与设备令牌本地管理

背景：客户端不再持有上游 AI 密钥，改为持有一枚「设备令牌」向中转服务鉴权。
     该令牌一机一份、服务端可单独吊销、可单独限额，
     即使被本机用户读取，损失范围也仅限于这一台设备的调用配额。

设计要点：
  1. 设备指纹由机器特征哈希得到，不含任何明文个人信息；
  2. 令牌与生成它的指纹一起存盘。换机器（例如整目录拷贝到别的电脑）时
     指纹对不上，客户端会自动重新注册，不会共用同一令牌；
  3. 令牌文件在 POSIX 上设为 0600；Windows 依赖用户目录本身的 ACL。
"""
from __future__ import annotations

import getpass
import hashlib
import json
import logging
import os
import platform
import uuid
from pathlib import Path
from typing import Optional

from core.path_utils import get_data_dir

logger = logging.getLogger(__name__)

_TOKEN_FILENAME = 'device.json'


def _token_path() -> Path:
    """返回设备令牌文件路径（数据目录下的 device.json）。"""
    return get_data_dir() / _TOKEN_FILENAME


def get_device_fingerprint() -> str:
    """
    生成稳定的设备指纹（64 位十六进制截断为 32 字符）。

    取材于主机名、登录用户名、网卡地址三者的哈希。
    这些原始值不会被存储或上送，只上送最终哈希，因此不泄露个人信息。
    """
    parts = []
    try:
        parts.append(platform.node() or '')
    except Exception:
        parts.append('')
    try:
        parts.append(getpass.getuser() or '')
    except Exception:
        parts.append('')
    try:
        parts.append(str(uuid.getnode()))
    except Exception:
        parts.append('')

    raw = '|'.join(parts) or 'fallback-device'
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    return digest[:32]


def load_device_token() -> Optional[str]:
    """
    读取本机已保存的设备令牌。

    仅当存储的指纹与当前机器指纹一致时才返回；否则视为无效（换机场景），
    由调用方触发重新注册。
    """
    path = _token_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        logger.debug('[device] 令牌文件损坏，将重新注册')
        return None

    if not isinstance(data, dict):
        return None

    token = data.get('token')
    fingerprint = data.get('fingerprint')
    if not token or not isinstance(token, str):
        return None
    if fingerprint != get_device_fingerprint():
        logger.info('[device] 设备指纹变化，将重新注册')
        return None
    return token


def save_device_token(token: str) -> bool:
    """保存设备令牌。写入失败不抛异常，仅返回 False（下次启动会重新注册）。"""
    path = _token_path()
    payload = {
        'token': token,
        'fingerprint': get_device_fingerprint(),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False), encoding='utf-8'
        )
        _harden_permissions(path)
        return True
    except OSError as e:
        logger.warning('[device] 令牌保存失败：%s', e)
        return False


def clear_device_token() -> None:
    """清除本机令牌（令牌失效或被吊销时调用，促使下次重新注册）。"""
    try:
        p = _token_path()
        if p.exists():
            p.unlink()
    except OSError:
        pass


def _harden_permissions(path: Path) -> None:
    """POSIX 下收紧为仅属主可读写；Windows 无对应简单机制，跳过。"""
    if os.name == 'posix':
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
