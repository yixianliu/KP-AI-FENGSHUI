# -*- coding: utf-8 -*-
"""
core/local_settings.py — 本地请求参数读写（兼容层）

【已废弃，仅作兼容】
超时 / 重试等参数现已并入 `core.ai_config` 的配置档，
与模型类型、端点、认证信息一起集中管理，避免多份配置各说各话。

本模块保留只是为了不破坏历史调用方，内部一律转发到中央管理器。
新代码请直接使用 `core.ai_config.get_config_manager()`。
"""
from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)

# 可调参数规范：键 -> 默认值（均为非负整数，非机密）
DEFAULTS: Dict[str, int] = {
    'timeout': 120,
    'max_retries': 2,
    'retry_delay': 5,
}


def load_tunables() -> Dict[str, int]:
    """读取当前生效配置档中的请求参数；无配置时回退默认值。"""
    try:
        from core.ai_config import get_config_manager
        profile = get_config_manager().get_active()
        if profile is not None:
            return {
                'timeout': profile.timeout,
                'max_retries': profile.max_retries,
                'retry_delay': profile.retry_delay,
            }
    except Exception as e:
        logger.debug('[设置] 读取中央配置失败，使用默认值: %s', e)
    return dict(DEFAULTS)


def save_tunables(params: Dict[str, int]) -> bool:
    """把请求参数写回当前生效的配置档。无配置档时返回 False。"""
    try:
        from core.ai_config import get_config_manager
        manager = get_config_manager()
        profile = manager.get_active()
        if profile is None:
            logger.warning('[设置] 尚无 AI 配置档，请求参数无处保存')
            return False
        for key in DEFAULTS:
            if key in params:
                setattr(profile, key, int(params[key]))
        return manager.upsert_profile(profile)
    except Exception as e:
        logger.error('[设置] 请求参数写入失败: %s', e)
        return False
