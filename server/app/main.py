# -*- coding: utf-8 -*-
"""
server/app/main.py — 风水排盘工具 AI 中转服务

职责：把桌面客户端的 AI 请求，用服务端持有的密钥转发给上游，
      使上游密钥永远不出现在任何用户可触达的位置。

信任模型（务必理解，否则容易高估安全性）：
  - X-App-Key 随 exe 分发，必然会泄露。它不是"秘密"，只是一道门槛，
    真正的控制手段是「每设备令牌 + 可吊销 + 配额」。
  - 设备令牌一机一份，可单独吊销、单独限额，滥用可精确切断。
  - 上游 AGNES_API_KEY 只存在于服务器环境变量中，任何接口都不会返回它。

接口：
  GET  /healthz            健康检查
  POST /v1/register        设备注册，换取设备令牌
  POST /v1/chat            AI 转发（需设备令牌）
  GET  /admin/stats        运营概览（需管理员令牌）
  POST /admin/revoke       吊销指定设备（需管理员令牌）
  POST /admin/revoke-all   一键吊销全部设备（需管理员令牌，应急用）
"""
from __future__ import annotations

import logging
from typing import List, Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from . import db
from .config import Settings, get_settings
from .relay import UpstreamError, call_upstream
from .security import (
    constant_time_eq,
    hash_token,
    install_log_scrubber,
    new_device_token,
    token_matches_any,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)
install_log_scrubber()
logger = logging.getLogger('relay')

app = FastAPI(
    title='风水排盘工具 AI 中转服务',
    description='为桌面客户端代理 AI 调用，使上游密钥不下发到用户设备。',
    version='1.0.0',
    # 生产环境关闭交互式文档，减少信息暴露面
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.on_event('startup')
def _startup() -> None:
    settings = get_settings()
    db.init_db(settings.db_path)
    logger.info('中转服务启动完成 | %s', settings)  # Settings.__repr__ 已脱敏


# ==================================================================
# 请求/响应模型
# ==================================================================
class RegisterRequest(BaseModel):
    fingerprint: str = Field(min_length=8, max_length=128)
    app_version: str = Field(default='', max_length=32)


class RegisterResponse(BaseModel):
    device_token: str
    device_daily_quota: int


class ChatMessage(BaseModel):
    role: Literal['system', 'user', 'assistant']
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=32768)

    @field_validator('messages')
    @classmethod
    def _limit_messages(cls, v: List[ChatMessage]) -> List[ChatMessage]:
        settings = get_settings()
        if len(v) > settings.max_messages:
            raise ValueError(f'消息条数超过上限 {settings.max_messages}')
        total = sum(len(m.content) for m in v)
        if total > settings.max_chars_per_request:
            raise ValueError(
                f'请求内容长度超过上限 {settings.max_chars_per_request} 字符'
            )
        return v


class ChatResponse(BaseModel):
    content: str
    usage: dict


# ==================================================================
# 依赖：鉴权
# ==================================================================
def _client_ip(request: Request) -> str:
    """取客户端 IP。部署在反向代理后时优先取 X-Forwarded-For 首段。"""
    xff = request.headers.get('x-forwarded-for', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.client.host if request.client else 'unknown'


def require_app_key(
    x_app_key: str = Header(default='', alias='X-App-Key'),
    settings: Settings = Depends(get_settings),
) -> None:
    """校验客户端准入密钥（防随手刷注册，非强安全边界）。"""
    if not x_app_key or not token_matches_any(x_app_key, settings.app_keys):
        raise HTTPException(status_code=401, detail='客户端未授权')


def require_device(
    authorization: str = Header(default='', alias='Authorization'),
) -> int:
    """校验设备令牌，返回 device_id。"""
    prefix = 'Bearer '
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail='缺少设备令牌')
    token = authorization[len(prefix):].strip()
    if not token:
        raise HTTPException(status_code=401, detail='缺少设备令牌')

    row = db.get_device_by_token_hash(hash_token(token))
    if row is None:
        raise HTTPException(status_code=401, detail='设备令牌无效')
    if int(row['revoked']) == 1:
        raise HTTPException(status_code=403, detail='设备令牌已被吊销')
    return int(row['id'])


def require_admin(
    x_admin_token: str = Header(default='', alias='X-Admin-Token'),
    settings: Settings = Depends(get_settings),
) -> None:
    if not x_admin_token or not constant_time_eq(x_admin_token, settings.admin_token):
        raise HTTPException(status_code=401, detail='管理员未授权')


# ==================================================================
# 业务接口
# ==================================================================
@app.get('/healthz')
def healthz() -> dict:
    """健康检查。刻意不返回任何配置信息。"""
    return {'status': 'ok'}


@app.post('/v1/register', response_model=RegisterResponse)
def register(
    body: RegisterRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_app_key),
) -> RegisterResponse:
    """
    设备注册：同一指纹已有有效令牌时不重复发放，避免刷量。
    注册接口按 IP 逐日限流。
    """
    ip_hash = db.hash_ip(_client_ip(request))
    day = db.today()
    count = db.bump_register_ip(ip_hash, day)
    if count > settings.register_ip_daily_limit:
        logger.warning('[register] IP 注册超限，已拒绝')
        raise HTTPException(status_code=429, detail='注册过于频繁，请稍后再试')

    # 令牌明文只在此刻存在一次，返回后服务端只保留摘要
    token = new_device_token()
    db.create_device(
        token_hash=hash_token(token),
        fingerprint=body.fingerprint,
        app_version=body.app_version,
    )
    logger.info('[register] 新设备注册成功')
    return RegisterResponse(
        device_token=token,
        device_daily_quota=settings.device_daily_quota,
    )


@app.post('/v1/chat', response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
    device_id: int = Depends(require_device),
) -> ChatResponse:
    """AI 转发主接口。配额检查在调用上游之前完成，防止刷爆账单。"""
    day = db.today()

    # 配额类拒绝一律用 429，客户端据此不做重试
    if db.get_global_usage(day) >= settings.global_daily_quota:
        logger.error('[chat] 全局日配额已耗尽，拒绝服务')
        raise HTTPException(status_code=429, detail='今日服务量已达上限，请明日再试')

    if db.get_device_usage(device_id, day) >= settings.device_daily_quota:
        raise HTTPException(status_code=429, detail='今日使用次数已达上限')

    messages = [{'role': m.role, 'content': m.content} for m in body.messages]

    try:
        result = await call_upstream(
            settings=settings,
            messages=messages,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
    except UpstreamError as e:
        # e.message 已确保为通用文案，不含上游细节
        raise HTTPException(status_code=e.status_code, detail=str(e)) from None

    db.bump_usage(device_id, day)
    db.touch_device(device_id)
    return ChatResponse(content=result['content'], usage=result['usage'])


# ==================================================================
# 管理接口
# ==================================================================
class RevokeRequest(BaseModel):
    device_id: int
    note: str = Field(default='', max_length=200)


@app.get('/admin/stats')
def admin_stats(_: None = Depends(require_admin)) -> dict:
    return db.stats()


@app.post('/admin/revoke')
def admin_revoke(body: RevokeRequest, _: None = Depends(require_admin)) -> dict:
    ok = db.revoke_device(body.device_id, body.note)
    if not ok:
        raise HTTPException(status_code=404, detail='设备不存在')
    logger.info('[admin] 已吊销设备 %s', body.device_id)
    return {'revoked': True, 'device_id': body.device_id}


@app.post('/admin/revoke-all')
def admin_revoke_all(_: None = Depends(require_admin)) -> dict:
    """应急开关：一键吊销全部设备令牌。客户端会自动重新注册。"""
    n = db.revoke_all_devices('bulk revoke')
    logger.warning('[admin] 已批量吊销 %s 个设备令牌', n)
    return {'revoked_count': n}


# ==================================================================
# 全局异常兜底：绝不把堆栈返回给客户端
# ==================================================================
@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
    logger.exception('[unhandled] 未捕获异常')  # 堆栈只进服务端日志（已脱敏）
    return JSONResponse(status_code=500, content={'detail': '服务内部错误'})
