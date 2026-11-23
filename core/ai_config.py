# -*- coding: utf-8 -*-
"""
core/ai_config.py — AI 模型配置中央管理器（全局唯一权威源）

【定位】
本模块是全程序 AI 相关参数的唯一出处。任何模块（api 客户端、分析流程、UI）
都必须经由此处取数，禁止再从 config.ini / .env / 内置常量各自读取，
以避免「多份配置各说各话」。

【管理的参数】
  - 模型类型（provider，如 OpenAI 兼容 / Agnes / DeepSeek / Ollama 本地…）
  - API 端点（api_url）
  - 认证信息（api_key + auth_scheme）
  - 模型名称（model）
  - 请求参数（timeout / max_retries / retry_delay / temperature / max_tokens）

【多配置档】
  支持保存多个「配置档（Profile）」并一键切换，便于在不同模型间对比切换。

【热更新】
  1. 版本号：任何写操作都会自增 `version`。使用方（如 AI 客户端单例）
     只需比对版本号即可判断「配置是否已变」，变了就重建，无需重启程序。
  2. 订阅回调：`subscribe(cb)` 注册监听者，保存后同步回调，供 UI 即时刷新。
  3. 外部改动感知：`version` 读取时会做节流的 mtime 检查，
     若配置文件被其他进程/手工编辑过，会自动重新载入。

【密钥落盘策略】
  当前默认使用 Windows DPAPI 加密（CryptProtectData / CryptUnprotectData，
  CRYPTPROTECT_UI_FORBIDDEN，密文与「当前 Windows 设备 + 用户账户」绑定）：
  配置文件被拷到别的机器或别的账户下都无法还原，属于真正的加密而非混淆。
  落盘形式为 `enc:v2:<base64(DPAPI blob)>`。
  历史版本使用「设备指纹派生密钥 + XOR + base64」混淆，落盘形式 `enc:v1:...`；
  为保证老用户平滑升级，读取时按 v2 → v1 的顺序尝试解密，
  旧格式一旦解密成功即自动以 DPAPI 重写（幂等，只迁移一次）。
  非 Windows 平台无 DPAPI 能力时，读写自动退回 v1 混淆格式（功能可用但强度较低）。

【发布产物约定】
  本程序仅接入一个固定的官方后端「文化研究算法 AI（Agnes AI）」，
  其端点与模型名作为公开的、非机密的产品常量写在本模块
  （OFFICIAL_AGNES_ENDPOINT / OFFICIAL_AGNES_MODEL）。
  真正需要保密、且由用户填写的只有 API 密钥：
  密钥经 GUI 填写后落盘加密（Windows DPAPI），不随 exe 明文分发。
  安全边界：exe 不得包含任何密钥；官方公开后端信息允许随包分发。
"""
from __future__ import annotations

import base64
import copy
import ctypes
import hashlib
import json
import logging
import os
import sys
import threading
import time
import uuid
from dataclasses import dataclass, asdict, field, fields as dataclass_fields
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

CONFIG_FILENAME = 'ai_config.json'
SCHEMA_VERSION = 1

# 落盘密钥的标记前缀：v1 = 旧版设备指纹 + XOR 混淆；v2 = Windows DPAPI 加密
_ENC_PREFIX = 'enc:v1:'
_ENC_PREFIX_DPAPI = 'enc:v2:'
# 识别「看起来是密文但版本号不认识」的情形，用于区分「文件损坏」与「格式升级不兼容」
_ENC_MARKER = 'enc:'
# 混淆用静态盐（非机密，仅让明文→密文映射不平凡）
_STATIC_SALT = b'KP-AI-FENGSHUI::ai_config::v1'

# 解密结果原因码（供日志与 UI 精确区分失效原因）
KEY_REASON_OK = 'ok'                            # DPAPI 解密成功
KEY_REASON_EMPTY = 'empty'                      # 未落盘（空串）
KEY_REASON_PLAINTEXT = 'plaintext'              # 无标记明文（外部手工导入）
KEY_REASON_LEGACY_OK = 'legacy_ok'              # 旧版 XOR 混淆解密成功（可迁移）
KEY_REASON_DPAPI_FAILED = 'dpapi_failed'        # DPAPI 解密失败（设备/账户变更）
KEY_REASON_LEGACY_FAILED = 'legacy_failed'      # 旧版混淆解密失败（指纹变更）
KEY_REASON_CORRUPTED = 'corrupted'              # 密文本身损坏（base64 无法解码）
KEY_REASON_UNKNOWN_FORMAT = 'unknown_format'    # 密文标记不认识（格式不兼容）

# 原因码 → 可读说明（写日志 / 透给 UI）
_KEY_REASON_TEXT: Dict[str, str] = {
    KEY_REASON_DPAPI_FAILED: 'DPAPI 解密失败（密文与 Windows 设备/账户绑定，可能来自其他设备或账户已变更）',
    KEY_REASON_LEGACY_FAILED: '旧版混淆解密失败（设备指纹变更或密文被改动）',
    KEY_REASON_CORRUPTED: '密钥数据已损坏（base64 解码失败）',
    KEY_REASON_UNKNOWN_FORMAT: '密钥格式无法识别（未知的加密版本标记）',
}


def key_reason_text(reason: str) -> str:
    """把解密原因码翻译为可读中文说明（未知原因码原样返回）。"""
    return _KEY_REASON_TEXT.get(reason, reason or '未知原因')

# 调试兜底日志只打印一次，避免 get_active 高频调用时刷屏
_debug_fallback_logged = False
# 外部文件改动检测的节流间隔（秒），避免高频 stat
_MTIME_CHECK_INTERVAL = 2.0


# ================================================================
# 官方固定后端（公开、非机密）：程序仅接入此一个模型
# GUI 仅索取 API 密钥，端点与模型名固定，不向用户暴露任何选择项
# ================================================================
OFFICIAL_AGNES_ENDPOINT = 'https://api.agnes-ai.cn/v1/chat/completions'
OFFICIAL_AGNES_MODEL = 'agnes-2.5-flash'
OFFICIAL_PROVIDER_KEY = 'agnes'


# ================================================================
# 供应商预设：当前仅保留官方「文化研究算法 AI」一个模型
# （公开端点 / 模型名已固化为上方产品常量，GUI 不暴露多模型选择）
# ================================================================
@dataclass(frozen=True)
class ProviderPreset:
    """供应商预设模板。api_url 仅为该服务的公开文档地址，不含凭据。"""
    key: str
    label: str
    api_url: str
    models: tuple
    auth_scheme: str = 'bearer'      # bearer: 自动加 "Bearer " 前缀；raw: 原样发送
    send_no_think: bool = False      # 是否附带 chat_template_kwargs 关闭思考模式
    needs_key: bool = True           # 本地模型（如 Ollama）可不填密钥


PROVIDER_PRESETS: Dict[str, ProviderPreset] = {
    OFFICIAL_PROVIDER_KEY: ProviderPreset(
        key=OFFICIAL_PROVIDER_KEY,
        label='文化研究算法 AI',
        api_url=OFFICIAL_AGNES_ENDPOINT,
        models=(OFFICIAL_AGNES_MODEL,),
        auth_scheme='bearer',
        send_no_think=True,      # agnes-2.5-flash 关闭思考模式可显著提速
        needs_key=True,
    ),
}

DEFAULT_PROVIDER = OFFICIAL_PROVIDER_KEY


# ================================================================
# 配置档数据模型
# ================================================================
@dataclass
class AIProfile:
    """单个 AI 模型配置档。所有字段均可在 GUI 中编辑。"""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = '默认配置'
    provider: str = DEFAULT_PROVIDER
    api_url: str = ''
    api_key: str = ''                 # 内存中为明文，落盘时混淆
    model: str = ''
    auth_scheme: str = 'bearer'
    timeout: int = 120
    max_retries: int = 2
    retry_delay: int = 5
    temperature: float = 0.7
    max_tokens: int = 4096
    send_no_think: bool = False
    verify_ssl: bool = True
    # 内部标记：当前 api_key 是否曾经落盘过（用于区分「未填写」与「失效」）
    # init=False：不进入构造参数；repr/compare=False：不出现在 repr 与 == 比较中
    _key_was_stored: bool = field(default=False, init=False, repr=False, compare=False)
    # 内部标记：上次解密失败的原因码（KEY_REASON_*），供 UI 精确提示
    _key_error_reason: str = field(default='', init=False, repr=False, compare=False)

    # ---------- 校验 ----------
    def key_status(self) -> str:
        """返回 api_key 的状态码，供 UI 精确区分不同失效原因。

        Returns:
            'ok'         : 密钥有效且可用
            'empty'      : 密钥从未填写（用户尚未输入）
            'corrupted'  : 密钥曾落盘但当前无法还原（跨设备迁移 / 指纹变更 / 文件损坏）
            'not_needed' : 当前 provider 无需密钥
        """
        preset = PROVIDER_PRESETS.get(self.provider)
        if preset is not None and not preset.needs_key:
            return 'not_needed'
        if not self.api_key.strip():
            return 'corrupted' if self._key_was_stored else 'empty'
        return 'ok'

    def key_error_text(self) -> str:
        """返回密钥失效的可读原因（无失效时返回空串），供 UI 提示使用。"""
        if self.api_key.strip() or not self._key_was_stored:
            return ''
        reason = self._key_error_reason or KEY_REASON_DPAPI_FAILED
        return key_reason_text(reason)

    def validate(self) -> Optional[str]:
        """返回错误信息；通过校验返回 None。"""
        if not self.name.strip():
            return '配置名称不能为空'
        if not self.api_url.strip():
            return 'API 端点不能为空'
        if not self.api_url.startswith(('http://', 'https://')):
            return 'API 端点必须以 http:// 或 https:// 开头'
        if not self.model.strip():
            return '模型名称不能为空'
        preset = PROVIDER_PRESETS.get(self.provider)
        if (preset is None or preset.needs_key) and not self.api_key.strip():
            # 区分「从未填写」与「密钥已损坏无法还原」，方便用户对症下药
            if self._key_was_stored:
                return f'认证密钥已失效（{self.key_error_text()}），请重新填写'
            return '认证密钥不能为空'
        if not (1 <= self.timeout <= 3600):
            return '请求超时须在 1~3600 秒之间'
        if not (0 <= self.max_retries <= 10):
            return '最大重试次数须在 0~10 之间'
        if not (0 <= self.retry_delay <= 60):
            return '重试间隔须在 0~60 秒之间'
        if not (0.0 <= self.temperature <= 2.0):
            return '温度须在 0.0~2.0 之间'
        if not (16 <= self.max_tokens <= 32768):
            return '最大输出 token 须在 16~32768 之间'
        return None

    def is_usable(self) -> bool:
        """是否具备发起请求的最小条件。"""
        return self.validate() is None

    # ---------- 认证头 ----------
    def auth_header(self) -> str:
        """构造 Authorization 头的值。"""
        key = self.api_key.strip()
        if not key:
            return ''
        if self.auth_scheme == 'raw':
            return key
        # bearer：已带前缀则不重复添加
        if key.lower().startswith('bearer '):
            return key
        return f'Bearer {key}'

    # ---------- 展示 ----------
    def masked_key(self) -> str:
        """用于 UI / 日志展示的脱敏密钥。"""
        key = self.api_key.strip()
        if not key:
            return '（未配置）'
        body = key[7:].strip() if key.lower().startswith('bearer ') else key
        if len(body) <= 8:
            return '*' * len(body)
        return f'{body[:4]}{"*" * 8}{body[-4:]}'

    def summary(self) -> Dict[str, str]:
        """安全摘要（不含明文密钥），可安全写日志。"""
        preset = PROVIDER_PRESETS.get(self.provider)
        return {
            'name': self.name,
            'provider': preset.label if preset else self.provider,
            'api_url': self.api_url,
            'model': self.model,
            'api_key': self.masked_key(),
        }

    def clone(self, new_name: Optional[str] = None) -> 'AIProfile':
        """深拷贝出一个新配置档，并分配新的随机 id（可选重命名）。

        Args:
            new_name: 新配置档名称；为 None 时沿用原名。

        Returns:
            AIProfile: 字段相同但 id 不同、可独立编辑的新配置档。
        """
        data = asdict(self)
        data.pop('_key_was_stored', None)  # 内部标记不随 clone 传播
        data.pop('_key_error_reason', None)
        data['id'] = uuid.uuid4().hex[:12]
        if new_name:
            data['name'] = new_name
        return AIProfile(**data)

    # ---------- 序列化 ----------
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIProfile':
        """宽容解析：忽略未知字段，缺失字段回落默认值，类型错误不致命。"""
        valid = {f.name: f for f in dataclass_fields(cls)}
        kwargs: Dict[str, Any] = {}
        init_kwargs: Dict[str, Any] = {}
        for key, spec in valid.items():
            if key not in data:
                continue
            raw = data[key]
            try:
                if spec.type in ('int', int):
                    val: Any = int(raw)
                elif spec.type in ('float', float):
                    val = float(raw)
                elif spec.type in ('bool', bool):
                    val = bool(raw)
                else:
                    val = str(raw) if raw is not None else ''
            except (TypeError, ValueError):
                continue
            if spec.init:
                init_kwargs[key] = val
            else:
                # init=False 的字段不参与构造，单独保存供赋值
                kwargs[key] = val
        instance = cls(**init_kwargs)
        for k, v in kwargs.items():
            setattr(instance, k, v)
        return instance


# ================================================================
# 密钥落盘加密：Windows DPAPI（主）+ 旧版 XOR 混淆（兼容/降级）
# ================================================================
# ---- DPAPI 的 ctypes 绑定（不引入任何第三方依赖）----
_CRYPTPROTECT_UI_FORBIDDEN = 0x1
_DPAPI_DESCRIPTION = 'KP-AI-FENGSHUI AI api key'


class _DATA_BLOB(ctypes.Structure):
    """Win32 DATA_BLOB 结构体（CryptProtectData 的入参/出参载体）。"""
    _fields_ = [
        ('cbData', ctypes.c_ulong),
        ('pbData', ctypes.POINTER(ctypes.c_char)),
    ]


# DPAPI 可用性探测结果缓存（None 表示尚未探测）
_dpapi_state: Optional[bool] = None


def dpapi_available() -> bool:
    """当前环境是否具备 Windows DPAPI 能力（结果缓存，避免反复探测）。

    Returns:
        bool: Windows 且 crypt32 暴露所需两个 API 时返回 True。
    """
    global _dpapi_state
    if _dpapi_state is not None:
        return _dpapi_state
    ok = False
    if os.name == 'nt':
        try:
            crypt32 = ctypes.WinDLL('crypt32', use_last_error=True)
            ok = bool(
                hasattr(crypt32, 'CryptProtectData')
                and hasattr(crypt32, 'CryptUnprotectData')
            )
        except (OSError, AttributeError):
            ok = False
    _dpapi_state = ok
    return ok


def _dpapi_call(data: bytes, protect: bool) -> bytes:
    """调用 DPAPI 对字节流加密或解密。

    Args:
        data: 待处理的字节流（加密时为明文，解密时为 DPAPI 密文）。
        protect: True 走 CryptProtectData，False 走 CryptUnprotectData。

    Returns:
        bytes: 转换后的字节流。

    Raises:
        OSError: 平台不支持 DPAPI 或 Win32 调用失败（解密失败通常意味着
                 密文来自其他设备/账户，或密文被篡改）。
    """
    if not dpapi_available():
        raise OSError('当前平台不支持 Windows DPAPI')

    crypt32 = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    # 显式声明签名，避免 64 位下指针被截断
    crypt32.CryptProtectData.restype = ctypes.c_int
    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DATA_BLOB), ctypes.c_wchar_p,
        ctypes.POINTER(_DATA_BLOB), ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_ulong, ctypes.POINTER(_DATA_BLOB),
    ]
    crypt32.CryptUnprotectData.restype = ctypes.c_int
    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DATA_BLOB), ctypes.POINTER(ctypes.c_wchar_p),
        ctypes.POINTER(_DATA_BLOB), ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_ulong, ctypes.POINTER(_DATA_BLOB),
    ]
    kernel32.LocalFree.restype = ctypes.c_void_p
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]

    raw = ctypes.create_string_buffer(data, len(data))
    blob_in = _DATA_BLOB(
        len(data),
        ctypes.cast(raw, ctypes.POINTER(ctypes.c_char)),
    )
    blob_out = _DATA_BLOB()

    if protect:
        ok = crypt32.CryptProtectData(
            ctypes.byref(blob_in), _DPAPI_DESCRIPTION,
            None, None, None, _CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(blob_out),
        )
    else:
        ok = crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None,
            None, None, None, _CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(blob_out),
        )
    if not ok:
        raise OSError(f'DPAPI 调用失败（Win32 error={ctypes.get_last_error()}）')

    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        # CryptProtectData / CryptUnprotectData 分配的缓冲区必须由调用方释放
        kernel32.LocalFree(ctypes.cast(blob_out.pbData, ctypes.c_void_p))


def _device_key() -> bytes:
    """派生设备绑定的旧版混淆密钥。取不到设备指纹时回退静态盐。"""
    try:
        from core.device_identity import get_device_fingerprint
        fp = get_device_fingerprint().encode('utf-8')
    except Exception:
        fp = b'no-device-fingerprint'
    return hashlib.sha256(_STATIC_SALT + fp).digest()


def _xor(data: bytes, key: bytes) -> bytes:
    """对字节流做循环密钥 XOR（旧版混淆，仅用于兼容历史密文）。

    Args:
        data: 待变换的明文/密文字节。
        key: 派生出的混淆密钥字节。

    Returns:
        bytes: 逐字节与 key 循环异或后的结果（XOR 可逆，再算一次即还原）。
    """
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _legacy_encrypt_key(plain: str) -> str:
    """按旧版算法（设备指纹 + XOR + base64）生成 `enc:v1:` 密文。

    仅用于兼容性与迁移测试；正常写盘不会再用此路径。
    """
    if not plain:
        return ''
    blob = _xor(plain.encode('utf-8'), _device_key())
    return _ENC_PREFIX + base64.b64encode(blob).decode('ascii')


def encrypt_key(plain: str) -> str:
    """把明文密钥加密为落盘形式（Windows 下为 DPAPI 密文）。

    空值原样返回。DPAPI 不可用（非 Windows）或调用失败时，
    退回旧版 `enc:v1:` 混淆，保证功能可用（日志会明确记录降级原因）。

    Args:
        plain: 明文 API 密钥。

    Returns:
        str: `enc:v2:`（DPAPI）或 `enc:v1:`（旧版混淆）密文。
    """
    if not plain:
        return ''
    if dpapi_available():
        try:
            blob = _dpapi_call(plain.encode('utf-8'), protect=True)
            return _ENC_PREFIX_DPAPI + base64.b64encode(blob).decode('ascii')
        except Exception as e:
            logger.error('[AI配置] DPAPI 加密失败，已降级为旧版混淆格式：%s', e)
    return _legacy_encrypt_key(plain)


def decrypt_key_detailed(stored: str) -> tuple:
    """还原落盘密钥，同时返回可诊断的原因码。

    解密顺序：DPAPI（v2）→ 旧版 XOR（v1）；对 v1 也先试一次 DPAPI，
    以兼容「密文本身正确但版本标记被手工改动」的极端情况。

    Args:
        stored: 落盘字段 api_key_enc 的原始值。

    Returns:
        tuple[str, str]: (明文密钥, 原因码)。失败时明文为空串，原因码为
        KEY_REASON_* 之一，调用方据此写日志 / 透给 UI。
    """
    if not stored:
        return '', KEY_REASON_EMPTY

    # 无 `enc:` 标记：按历史行为视作外部导入的明文
    if not stored.startswith(_ENC_MARKER):
        return stored, KEY_REASON_PLAINTEXT

    known = stored.startswith(_ENC_PREFIX_DPAPI) or stored.startswith(_ENC_PREFIX)
    if not known:
        return '', KEY_REASON_UNKNOWN_FORMAT

    parts = stored.split(':', 2)
    payload = parts[2] if len(parts) >= 3 else ''
    try:
        blob = base64.b64decode(payload, validate=True)
    except Exception:
        return '', KEY_REASON_CORRUPTED

    # 1) 优先尝试 DPAPI：现代格式成功即返回
    if dpapi_available():
        try:
            return _dpapi_call(blob, protect=False).decode('utf-8'), KEY_REASON_OK
        except Exception:
            # v2 密文只能由 DPAPI 还原；失败即判定「设备/账户变更」，不再走 XOR
            if stored.startswith(_ENC_PREFIX_DPAPI):
                return '', KEY_REASON_DPAPI_FAILED
    elif stored.startswith(_ENC_PREFIX_DPAPI):
        # 平台无 DPAPI（如 CI 的 Linux 容器），无法还原 v2 密文
        return '', KEY_REASON_DPAPI_FAILED

    # 2) 回退旧版 XOR 混淆
    if stored.startswith(_ENC_PREFIX):
        try:
            return _xor(blob, _device_key()).decode('utf-8'), KEY_REASON_LEGACY_OK
        except Exception:
            return '', KEY_REASON_LEGACY_FAILED
    return '', KEY_REASON_UNKNOWN_FORMAT


def decrypt_key(stored: str) -> str:
    """还原落盘密钥。非本机生成 / 损坏时返回空串（触发重新配置）。

    【安全约束】空串本身不携带语义，调用方需自行判断「空是因为未落盘」还是
    「空是因为解密失败」；需要精确原因时改用 decrypt_key_detailed。
    """
    plain, reason = decrypt_key_detailed(stored)
    if not plain and reason not in (KEY_REASON_EMPTY, KEY_REASON_PLAINTEXT):
        logger.error('[AI配置] 密钥无法还原：%s。请重新填写 API 密钥。',
                     key_reason_text(reason))
    return plain



# ================================================================
# 中央管理器
# ================================================================
class AIConfigManager:
    """AI 配置中央管理器（进程内单例，线程安全）。"""

    _instance: Optional['AIConfigManager'] = None
    _instance_lock = threading.Lock()

    def __init__(self, path: Optional[Path] = None):
        """初始化中央配置管理器。

        Args:
            path: 配置文件路径；为 None 时首次访问再按应用目录解析默认值。
        """
        self._lock = threading.RLock()
        self._path: Optional[Path] = Path(path) if path else None
        self._profiles: List[AIProfile] = []
        self._active_id: str = ''
        self._version: int = 0
        self._subscribers: List[Callable[[int], None]] = []
        self._file_mtime: float = -1.0
        self._last_stat_at: float = 0.0
        self._loaded = False
        # 待迁移的旧版混淆密钥数量（>0 表示本次载入需要一次性迁移为 DPAPI）
        self._pending_migration: int = 0

    # ---------- 单例 ----------
    @classmethod
    def instance(cls) -> 'AIConfigManager':
        """获取进程内唯一实例（双重检查锁的单例）。

        使用方都应经此入口而不是自行 new，以保证全程序共享同一份配置与版本号。

        Returns:
            AIConfigManager: 全局唯一的配置管理器实例。
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """仅供测试使用：丢弃单例。"""
        with cls._instance_lock:
            cls._instance = None

    # ---------- 路径 ----------
    def path(self) -> Path:
        """返回配置文件路径；首次调用时按应用目录惰性解析默认路径。

        Returns:
            Path: `ai_config.json` 的完整路径。
        """
        if self._path is None:
            from core.path_utils import get_app_dir
            self._path = get_app_dir() / CONFIG_FILENAME
        return self._path

    def set_path(self, path: Path) -> None:
        """重设配置文件路径（测试 / 迁移用），并强制重载。"""
        with self._lock:
            self._path = Path(path)
            self._loaded = False
            self._file_mtime = -1.0
            self._last_stat_at = 0.0
            self.load(force=True)

    # ---------- 载入 / 保存 ----------
    def load(self, force: bool = False) -> None:
        """从磁盘载入配置。文件缺失或损坏时以空配置启动（不抛异常）。"""
        with self._lock:
            if self._loaded and not force:
                return
            self._profiles = []
            self._active_id = ''
            self._pending_migration = 0
            path = self.path()
            try:
                if path.exists():
                    data = json.loads(path.read_text(encoding='utf-8'))
                    self._apply_raw(data)
                    self._file_mtime = path.stat().st_mtime
                    # 旧版混淆密文 → DPAPI 平滑迁移（幂等，只发生一次）
                    self._migrate_legacy_keys()
            except (OSError, ValueError) as e:
                logger.warning('[AI配置] 读取失败，将以空配置启动：%s', e)
            self._loaded = True

    def _apply_raw(self, data: Any) -> None:
        """把原始 JSON 结构应用到内存（已持锁）。

        解密采用「DPAPI 优先、旧版 XOR 回退」策略，并记录失败原因，
        统计可迁移的旧格式档位数量（供 load 中的一次性迁移使用）。
        """
        if not isinstance(data, dict):
            return
        raw_profiles = data.get('profiles')
        if not isinstance(raw_profiles, list):
            return
        loaded: List[AIProfile] = []
        legacy_count = 0
        for item in raw_profiles:
            if not isinstance(item, dict):
                continue
            item = dict(item)
            # 落盘字段 api_key_enc → 内存字段 api_key
            enc = item.pop('api_key_enc', '')
            profile = AIProfile.from_dict(item)
            if enc:
                plain, reason = decrypt_key_detailed(enc)
                profile.api_key = plain
                profile._key_was_stored = True
                if reason == KEY_REASON_LEGACY_OK:
                    legacy_count += 1
                elif reason not in (KEY_REASON_OK, KEY_REASON_PLAINTEXT):
                    profile._key_error_reason = reason
                    logger.error('[AI配置] 配置档「%s」的密钥无法还原：%s',
                                 profile.name, key_reason_text(reason))
            else:
                profile.api_key = item.get('api_key', '')
            loaded.append(profile)
        self._profiles = loaded
        # 仅当所有落盘密钥都已成功解密时才迁移，避免把无法还原的密文写丢
        has_failure = any(p._key_error_reason for p in loaded)
        self._pending_migration = 0 if has_failure else legacy_count
        active = data.get('active')
        if isinstance(active, str) and any(p.id == active for p in loaded):
            self._active_id = active
        elif loaded:
            self._active_id = loaded[0].id

    def _serialize_payload(self) -> Dict[str, Any]:
        """构造落盘 JSON 结构（不写盘、不改版本号）。"""
        payload: Dict[str, Any] = {
            'schema': SCHEMA_VERSION,
            'active': self._active_id,
            'profiles': [],
        }
        for p in self._profiles:
            item = asdict(p)
            item.pop('api_key', None)
            item.pop('_key_was_stored', None)      # 内部状态不落盘
            item.pop('_key_error_reason', None)    # 内部状态不落盘
            item['api_key_enc'] = encrypt_key(p.api_key)
            payload['profiles'].append(item)
        return payload

    def _write_payload(self, payload: Dict[str, Any]) -> bool:
        """原子写盘（不含版本号自增与订阅通知）。"""
        path = self.path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix('.json.tmp')
            tmp.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding='utf-8',
            )
            os.replace(tmp, path)
            _harden_permissions(path)
            self._file_mtime = path.stat().st_mtime
            return True
        except OSError as e:
            logger.error('[AI配置] 写入失败：%s', e)
            return False

    def _migrate_legacy_keys(self) -> None:
        """把旧版 `enc:v1:` 混淆密文一次性重写为 DPAPI 密文（幂等）。

        迁移成功后文件内全部为 `enc:v2:`，下次载入不会再触发本流程；
        平台无 DPAPI 能力时保持旧格式不动，仅记录日志。
        """
        if not self._pending_migration:
            return
        if not dpapi_available():
            logger.info('[AI配置] 当前平台无 DPAPI 能力，%d 个旧版密钥保持原混淆格式',
                        self._pending_migration)
            self._pending_migration = 0
            return
        count = self._pending_migration
        if self._write_payload(self._serialize_payload()):
            logger.info('[AI配置] 已将 %d 个旧版混淆密钥迁移为 DPAPI 加密（仅此一次）', count)
        self._pending_migration = 0

    def save(self) -> bool:
        """原子写盘并触发热更新通知。"""
        with self._lock:
            if not self._write_payload(self._serialize_payload()):
                return False
            self._version += 1
            version = self._version

        # 通知放在锁外，避免订阅者回调里再次读配置造成死锁
        self._notify(version)
        return True

    # ---------- 热更新 ----------
    @property
    def version(self) -> int:
        """配置版本号。读取时顺带做节流的外部改动检测。"""
        self._reload_if_file_changed()
        with self._lock:
            return self._version

    def _reload_if_file_changed(self) -> None:
        """检测配置文件是否被外部修改，是则重载并自增版本。"""
        now = time.time()
        with self._lock:
            if not self._loaded:
                self.load()
                return
            if now - self._last_stat_at < _MTIME_CHECK_INTERVAL:
                return
            self._last_stat_at = now
            path = self.path()
            try:
                mtime = path.stat().st_mtime if path.exists() else -1.0
            except OSError:
                return
            if mtime == self._file_mtime:
                return
            logger.info('[AI配置] 检测到配置文件变化，已重新载入')
            self.load(force=True)
            self._version += 1
            version = self._version
        self._notify(version)

    def subscribe(self, callback: Callable[[int], None]) -> Callable[[], None]:
        """注册配置变更监听者，返回取消订阅的函数。"""
        with self._lock:
            self._subscribers.append(callback)

        def unsubscribe() -> None:
            """取消订阅：把原 callback 从监听列表中移除（幂等，重复调用安全）。"""
            with self._lock:
                if callback in self._subscribers:
                    self._subscribers.remove(callback)

        return unsubscribe

    def _notify(self, version: int) -> None:
        """依次调用所有订阅者回调（已复制列表，避免回调内修改订阅表时出错）。

        Args:
            version: 触发本次通知的配置版本号，作为回调参数传给订阅者。
        """
        with self._lock:
            subs = list(self._subscribers)
        for cb in subs:
            try:
                cb(version)
            except Exception as e:
                logger.warning('[AI配置] 订阅者回调异常：%s', e)

    # ---------- 查询 ----------
    def list_profiles(self) -> List[AIProfile]:
        """返回全部配置档的深拷贝列表（先确保已从磁盘载入最新内容）。

        Returns:
            List[AIProfile]: 所有配置档的副本，调用方修改不会污染内存状态。
        """
        self.load()
        with self._lock:
            return [copy.deepcopy(p) for p in self._profiles]

    def get_active(self) -> Optional[AIProfile]:
        """返回当前生效的配置档副本；未配置时返回 None。

        调试兜底：源码运行（非冻结）且用户尚未在 GUI 配置时，
        自动返回 core.debug_keys 中的本地密钥作为生效配置，
        便于 `python main.py` 命令行调试无需先走 GUI。
        该兜底为内存态、不落盘，绝不进入打包产物。
        """
        self.load()
        with self._lock:
            # 候选档：当前生效档优先，否则取全部档
            candidates = [p for p in self._profiles if p.id == self._active_id] or self._profiles
        # 优先返回「字段完整、可发起请求」的档（GUI 已配好且含有效密钥）。
        # 仅当不存在任何可用档时，才在调试模式（非冻结）下注入本地调试密钥。
        # 这样即便磁盘残留一个「空密钥 / 不完整」的档，也不会阻塞调试兜底；
        # 冻结（EXE）运行时兜底返回 None，保持产物零密钥。
        for p in candidates:
            if p.is_usable():
                return copy.deepcopy(p)
        return self._debug_fallback_profile()

    def get_active_version(self) -> int:
        """返回当前生效配置档的版本号（用于客户端单例比对是否需要重建）。

        Returns:
            当前配置版本号，未加载时返回 0。
        """
        self.load()
        with self._lock:
            return self._version

    def _debug_fallback_profile(self) -> Optional[AIProfile]:
        """调试模式兜底：从 core.debug_keys 读取本地密钥（内存态、不落盘）。"""
        # 打包产物（PyInstaller 冻结）运行时直接忽略，且 core.debug_keys 不会被打进 exe
        if getattr(sys, 'frozen', False):
            return None
        try:
            from core.debug_keys import get_debug_keys
            data = get_debug_keys()
        except Exception:
            return None
        if not data:
            return None
        profile = make_default_profile()
        profile.name = '调试密钥（自动注入）'
        profile.api_key = data['api_key']
        profile.api_url = data['api_url']
        profile.model = data['model']
        global _debug_fallback_logged
        if not _debug_fallback_logged:
            _debug_fallback_logged = True
            logger.info('[AI配置] 调试模式：已注入本地调试密钥（来自 core.debug_keys）')
        return profile

    def get_profile(self, profile_id: str) -> Optional[AIProfile]:
        """按 id 查找并返回配置档的深拷贝；不存在时返回 None。

        Args:
            profile_id: 目标配置档的 id。

        Returns:
            Optional[AIProfile]: 命中的配置档副本，或 None。
        """
        self.load()
        with self._lock:
            for p in self._profiles:
                if p.id == profile_id:
                    return copy.deepcopy(p)
            return None

    @property
    def active_id(self) -> str:
        """当前生效配置档的 id（先确保已载入最新内容）。

        Returns:
            str: 生效配置档 id；尚未配置时为空串。
        """
        self.load()
        with self._lock:
            return self._active_id

    def is_configured(self) -> bool:
        """AI 功能是否可用（存在一个字段完整的生效配置）。"""
        profile = self.get_active()
        return bool(profile and profile.is_usable())

    def status_text(self) -> str:
        """供 UI 展示的一句话状态（密钥失效时透出可读原因）。"""
        profile = self.get_active()
        if profile is None:
            # 密钥全部无法还原时 get_active 返回 None，这里补一句可读原因
            issue = self._first_key_issue()
            if issue:
                return f'当前配置的认证密钥不可用：{issue}'
            return '尚未配置 AI 模型，请在「设置」中填写 API 密钥'
        err = profile.validate()
        if err:
            return f'当前配置不完整：{err}'
        return f'已就绪：{profile.name}（{profile.model}）'

    def _first_key_issue(self) -> str:
        """返回第一个密钥失效配置档的可读原因（无失效时返回空串）。"""
        with self._lock:
            for p in self._profiles:
                text = p.key_error_text()
                if text:
                    return text
        return ''

    # ---------- 写操作（均会触发热更新） ----------
    def upsert_profile(self, profile: AIProfile, make_active: bool = False) -> bool:
        """新增或覆盖一个配置档。"""
        self.load()
        with self._lock:
            replaced = False
            for i, p in enumerate(self._profiles):
                if p.id == profile.id:
                    self._profiles[i] = copy.deepcopy(profile)
                    replaced = True
                    break
            if not replaced:
                self._profiles.append(copy.deepcopy(profile))
            if make_active or not self._active_id:
                self._active_id = profile.id
        return self.save()

    def delete_profile(self, profile_id: str) -> bool:
        """删除指定配置档；若它正被设为生效档，则自动改指第一个剩余档。

        Args:
            profile_id: 待删除配置档的 id。

        Returns:
            bool: 成功删除返回 True；id 不存在（无改动）返回 False。
        """
        self.load()
        with self._lock:
            before = len(self._profiles)
            self._profiles = [p for p in self._profiles if p.id != profile_id]
            if len(self._profiles) == before:
                return False
            if self._active_id == profile_id:
                self._active_id = self._profiles[0].id if self._profiles else ''
        return self.save()

    def set_active(self, profile_id: str) -> bool:
        """把指定配置档设为当前生效档（落盘并触发热更新）。

        Args:
            profile_id: 目标配置档的 id。

        Returns:
            bool: 设置成功（id 存在）返回 True；id 不存在返回 False。
        """
        self.load()
        with self._lock:
            if not any(p.id == profile_id for p in self._profiles):
                return False
            if self._active_id == profile_id:
                return True
            self._active_id = profile_id
        return self.save()

    def replace_all(self, profiles: List[AIProfile], active_id: str = '') -> bool:
        """
        用给定集合整体替换现有配置，单次原子写盘、单次版本自增。

        供 GUI「保存并应用」使用：一次提交所有配置档的编辑结果，
        避免逐档保存造成多次磁盘写入与多次热更新通知。
        """
        self.load()
        with self._lock:
            self._profiles = [copy.deepcopy(p) for p in profiles]
            if active_id and any(p.id == active_id for p in self._profiles):
                self._active_id = active_id
            elif self._profiles:
                if not any(p.id == self._active_id for p in self._profiles):
                    self._active_id = self._profiles[0].id
            else:
                self._active_id = ''
        return self.save()

    def clear_all(self) -> bool:
        """清空全部配置（用于「注销/重置」场景）。"""
        self.load()
        with self._lock:
            self._profiles = []
            self._active_id = ''
        return self.save()

    # ---------- 兼容接口：给旧调用方的扁平字典 ----------
    def as_legacy_dict(self) -> Dict[str, Any]:
        """
        返回历史调用方期望的扁平配置字典。

        未配置时各字段为空串 / 默认值，由调用方自行降级，不抛异常。
        """
        p = self.get_active()
        if p is None:
            return {
                'api_url': '', 'api_key': '', 'model': '',
                'timeout': 120, 'max_retries': 2, 'retry_delay': 5,
                'temperature': 0.7, 'max_tokens': 2048,
                'auth_scheme': 'bearer', 'send_no_think': False,
                'verify_ssl': True, 'provider': DEFAULT_PROVIDER,
            }
        return {
            'api_url': p.api_url,
            'api_key': p.auth_header(),
            'model': p.model,
            'timeout': p.timeout,
            'max_retries': p.max_retries,
            'retry_delay': p.retry_delay,
            'temperature': p.temperature,
            'max_tokens': p.max_tokens,
            'auth_scheme': p.auth_scheme,
            'send_no_think': p.send_no_think,
            'verify_ssl': p.verify_ssl,
            'provider': p.provider,
        }


def _harden_permissions(path: Path) -> None:
    """POSIX 下收紧为仅属主可读写；Windows 依赖用户目录 ACL。"""
    if os.name == 'posix':
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


# ================================================================
# 模块级便捷函数（推荐的统一入口）
# ================================================================
def get_config_manager() -> AIConfigManager:
    """获取全局 AI 配置管理器。"""
    return AIConfigManager.instance()


def get_active_profile() -> Optional[AIProfile]:
    """便捷入口：返回当前生效配置档，未配置时返回 None。"""
    return get_config_manager().get_active()


def is_ai_configured() -> bool:
    """便捷入口：判断 AI 功能是否已具备可用配置。"""
    return get_config_manager().is_configured()


def config_version() -> int:
    """便捷入口：返回当前配置版本号（读取时可能触发外部改动重载）。"""
    return get_config_manager().version


def subscribe(callback: Callable[[int], None]) -> Callable[[], None]:
    """便捷入口：注册配置变更监听者，返回取消订阅的函数。

    Args:
        callback: 接收版本号 (int) 的回调。

    Returns:
        Callable[[], None]: 用于取消订阅的函数。
    """
    return get_config_manager().subscribe(callback)


def make_default_profile(provider: str = DEFAULT_PROVIDER) -> AIProfile:
    """按供应商预设生成一个待填写的新配置档（不含任何凭据）。"""
    preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS[DEFAULT_PROVIDER])
    return AIProfile(
        name=preset.label,
        provider=preset.key,
        api_url=preset.api_url,
        api_key='',
        model=preset.models[0] if preset.models else '',
        auth_scheme=preset.auth_scheme,
        send_no_think=preset.send_no_think,
    )
