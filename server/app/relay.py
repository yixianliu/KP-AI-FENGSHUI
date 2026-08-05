# -*- coding: utf-8 -*-
"""
server/app/relay.py — 上游 Agnes AI 转发

这是全系统唯一持有并使用上游 API 密钥的模块。

安全约定（逐条对应一种真实泄露途径）：
  1. 密钥只在本函数内组装进请求头，不写日志、不进异常、不入返回值；
  2. 上游响应体绝不原样透传给客户端 —— 上游报错信息可能回显密钥片段、
     内部地址或账号信息，一律映射为通用错误码后再返回；
  3. 模型名由服务端强制指定，客户端无权选择，防止被诱导调用高价模型；
  4. max_tokens 在服务端二次封顶，防止单次请求刷爆账单；
  5. 任何异常在向上抛出前都经过 scrub() 脱敏。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import httpx

from .config import Settings
from .security import scrub

logger = logging.getLogger(__name__)


class UpstreamError(Exception):
    """上游调用失败。message 为「可安全返回给客户端」的通用描述。"""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


# 上游状态码 -> (返回给客户端的状态码, 通用文案)
# 注意：不暴露上游身份、不暴露具体原因细节
_STATUS_MAP: Dict[int, Tuple[int, str]] = {
    400: (502, 'AI 服务拒绝了本次请求'),
    401: (503, 'AI 服务暂不可用，请稍后重试'),   # 密钥问题属服务端故障，不告知客户端真因
    403: (503, 'AI 服务暂不可用，请稍后重试'),
    404: (502, 'AI 服务接口异常'),
    # 上游限流映射为 503 而非 429：429 在本服务中专表「配额用尽」，
    # 客户端据此决定不重试；上游繁忙则属可重试的瞬时错误。
    429: (503, 'AI 服务繁忙，请稍后重试'),
    500: (502, 'AI 服务内部错误'),
    502: (502, 'AI 服务网关异常'),
    503: (503, 'AI 服务过载，请稍后重试'),
    504: (504, 'AI 服务响应超时'),
}


async def call_upstream(
    settings: Settings,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> Dict[str, Any]:
    """
    调用上游 Agnes AI 并返回「已清洗」的结果。

    Returns:
        {'content': str, 'usage': dict}

    Raises:
        UpstreamError: 任何上游异常，message 已确保不含敏感信息
    """
    # 服务端强制约束：模型固定、token 封顶
    capped_tokens = max(1, min(int(max_tokens), settings.max_tokens_cap))

    headers = {
        'Content-Type': 'application/json',
        # 唯一一处使用密钥的地方
        'Authorization': settings.agnes_api_key,
    }
    payload = {
        'model': settings.agnes_model,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': capped_tokens,
        'chat_template_kwargs': {'enable_thinking': False},
    }

    try:
        async with httpx.AsyncClient(timeout=settings.upstream_timeout) as client:
            resp = await client.post(
                settings.agnes_api_url, headers=headers, json=payload
            )
    except httpx.TimeoutException:
        logger.warning('[relay] 上游请求超时')
        raise UpstreamError('AI 服务响应超时，请稍后重试', 504) from None
    except httpx.HTTPError as e:
        # 注意：异常文本可能含 URL，做一次脱敏后再记录；不回传给客户端
        logger.warning('[relay] 上游网络异常: %s', scrub(str(e)))
        raise UpstreamError('AI 服务连接失败，请稍后重试', 502) from None

    if resp.status_code != 200:
        client_status, client_msg = _STATUS_MAP.get(
            resp.status_code, (502, 'AI 服务调用失败')
        )
        # 上游原文只进服务端日志（且脱敏），绝不返回客户端
        logger.warning(
            '[relay] 上游 HTTP %s: %s',
            resp.status_code, scrub(resp.text[:500]),
        )
        raise UpstreamError(client_msg, client_status)

    try:
        data = resp.json()
    except ValueError:
        logger.warning('[relay] 上游返回非法 JSON')
        raise UpstreamError('AI 服务返回格式异常', 502) from None

    content = _extract_content(data)
    if content is None:
        logger.warning('[relay] 上游响应缺少 content 字段')
        raise UpstreamError('AI 服务返回内容为空', 502)

    usage = data.get('usage', {}) if isinstance(data, dict) else {}
    if not isinstance(usage, dict):
        usage = {}

    # 只回传业务必需的两个字段，杜绝上游元数据（含账号、组织、限额等）外泄
    return {
        'content': content,
        'usage': {
            'prompt_tokens': int(usage.get('prompt_tokens', 0) or 0),
            'completion_tokens': int(usage.get('completion_tokens', 0) or 0),
            'total_tokens': int(usage.get('total_tokens', 0) or 0),
        },
    }


def _extract_content(data: Any) -> str | None:
    """从 OpenAI 兼容响应中提取回复文本，失败返回 None。"""
    if isinstance(data, dict):
        choices = data.get('choices')
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get('message') or {}
                if isinstance(message, dict):
                    content = message.get('content')
                    if isinstance(content, str):
                        return content
        content = data.get('content')
        if isinstance(content, str):
            return content
    return None
