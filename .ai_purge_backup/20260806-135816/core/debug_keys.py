# -*- coding: utf-8 -*-
"""
core/debug_keys.py — 本地命令行调试用密钥源（仅开发机，绝不进入发布产物）

【用途】
参考 D:\\PythonProject\\api 目录下的实现风格：把本地调试用的 AI 模型密钥直接
放在源码级常量里，方便 `python main.py` 命令行调试时免去 GUI 填密钥。
调试模式下，core.ai_config 会把本文件作为「兜底配置」自动注入并使用（保留密钥）。

【打包安全】
打包生成 EXE 前，scripts/purge_ai_secrets.py 会自动把下方 DEBUG_AGNES_API_KEY
清空为 ""（并备份原文件），因此密钥绝不会随安装包分发。
即便忘了清理，产物级校验 scripts/verify_build_security.py 也会在打包后扫描到
残留并拒绝发布。请勿把真实密钥提交到版本库。

【优先级】
调试密钥仅在「源码运行（非冻结）」且「用户尚未在 GUI 配置」时生效；
一旦用户在 GUI 填写了密钥，GUI 配置优先，本文件被忽略。
"""
from __future__ import annotations

import os

# ↓↓↓ 仅本地调试填写，留空则忽略（由 GUI 配置 / 运行时环境变量接管）↓↓↓
DEBUG_AGNES_API_KEY = "sk-REALKEY-abcdefghij0123456789"   # 调试用密钥，仅你的开发机填写（例如 sk- 开头的一串）
DEBUG_AGNES_API_URL = "https://api.agnes-ai.cn/v1/chat/completions"
DEBUG_AGNES_MODEL = "agnes-2.5-flash"
# ↑↑↑ ↑↑↑

# 环境变量名（可选）：命令行 `set KP_AGNES_API_KEY=...` 即可，无需改本文件
_ENV_KEY = "KP_AGNES_API_KEY"

# 官方固定后端（公开、非机密），作为调试默认值兜底
_OFFICIAL_ENDPOINT = "https://api.agnes-ai.cn/v1/chat/completions"
_OFFICIAL_MODEL = "agnes-2.5-flash"


def get_debug_keys() -> "dict | None":
    """返回调试密钥三元组；无可用密钥时返回 None。

    优先级：环境变量 KP_AGNES_API_KEY > 本文件常量 DEBUG_AGNES_API_KEY。
    """
    key = (os.environ.get(_ENV_KEY) or DEBUG_AGNES_API_KEY or "").strip()
    if not key:
        return None
    url = (DEBUG_AGNES_API_URL or _OFFICIAL_ENDPOINT).strip()
    model = (DEBUG_AGNES_MODEL or _OFFICIAL_MODEL).strip()
    return {
        "api_key": key,
        "api_url": url,
        "model": model,
    }
