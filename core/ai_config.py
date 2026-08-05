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

【密钥落盘策略】（诚实声明）
  api_key 落盘时使用「设备指纹派生密钥 + XOR + base64」混淆，
  配置文件被拷到另一台机器无法还原。但这属于**提高门槛**而非真正的加密：
  在本机上，任何能运行本程序代码的人都可以还原它。请勿绑定高价值账户。

【发布产物约定】
  本模块不含任何默认端点 / 默认密钥 / 默认模型名。
  打包后的 exe 中不存在任何 AI 原始信息，全部由用户在 GUI 中填写。
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, asdict, field, fields as dataclass_fields
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

CONFIG_FILENAME = 'ai_config.json'
SCHEMA_VERSION = 1

# 落盘密钥的标记前缀，便于识别与未来算法升级
_ENC_PREFIX = 'enc:v1:'
# 混淆用静态盐（非机密，仅让明文→密文映射不平凡）
_STATIC_SALT = b'KP-AI-FENGSHUI::ai_config::v1'
# 外部文件改动检测的节流间隔（秒），避免高频 stat
_MTIME_CHECK_INTERVAL = 2.0


# ================================================================
# 供应商预设：仅提供「填写模板」，不含任何真实凭据
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
    # 通用档：不预置任何端点与模型名，完全由用户填写。
    # 这是默认项 —— 程序本体对「用哪家模型」不做任何预设。
    'openai_compatible': ProviderPreset(
        key='openai_compatible',
        label='OpenAI 兼容接口（通用）',
        api_url='',
        models=(),
        auth_scheme='bearer',
    ),
    'openai': ProviderPreset(
        key='openai',
        label='OpenAI',
        api_url='https://api.openai.com/v1/chat/completions',
        models=('gpt-4o-mini', 'gpt-4o', 'gpt-4.1-mini'),
        auth_scheme='bearer',
    ),
    'deepseek': ProviderPreset(
        key='deepseek',
        label='DeepSeek',
        api_url='https://api.deepseek.com/chat/completions',
        models=('deepseek-chat', 'deepseek-reasoner'),
        auth_scheme='bearer',
    ),
    'moonshot': ProviderPreset(
        key='moonshot',
        label='Moonshot 月之暗面',
        api_url='https://api.moonshot.cn/v1/chat/completions',
        models=('moonshot-v1-8k', 'moonshot-v1-32k'),
        auth_scheme='bearer',
    ),
    'dashscope': ProviderPreset(
        key='dashscope',
        label='阿里云百炼（通义千问）',
        api_url='https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
        models=('qwen-plus', 'qwen-turbo', 'qwen-max'),
        auth_scheme='bearer',
    ),
    'zhipu': ProviderPreset(
        key='zhipu',
        label='智谱 GLM',
        api_url='https://open.bigmodel.cn/api/paas/v4/chat/completions',
        models=('glm-4-flash', 'glm-4-plus'),
        auth_scheme='bearer',
    ),
    'ollama': ProviderPreset(
        key='ollama',
        label='Ollama 本地模型',
        api_url='http://localhost:11434/v1/chat/completions',
        models=('qwen2.5:7b', 'llama3.1:8b'),
        auth_scheme='raw',
        needs_key=False,
    ),
    'custom': ProviderPreset(
        key='custom',
        label='自定义',
        api_url='',
        models=(),
        auth_scheme='bearer',
    ),
}

DEFAULT_PROVIDER = 'openai_compatible'


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
    max_tokens: int = 2048
    send_no_think: bool = False
    verify_ssl: bool = True

    # ---------- 校验 ----------
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
        data = asdict(self)
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
        for key, spec in valid.items():
            if key not in data:
                continue
            raw = data[key]
            try:
                if spec.type in ('int', int):
                    kwargs[key] = int(raw)
                elif spec.type in ('float', float):
                    kwargs[key] = float(raw)
                elif spec.type in ('bool', bool):
                    kwargs[key] = bool(raw)
                else:
                    kwargs[key] = str(raw) if raw is not None else ''
            except (TypeError, ValueError):
                continue
        return cls(**kwargs)


# ================================================================
# 密钥落盘混淆（设备绑定）
# ================================================================
def _device_key() -> bytes:
    """派生设备绑定的混淆密钥。取不到设备指纹时回退静态盐。"""
    try:
        from core.device_identity import get_device_fingerprint
        fp = get_device_fingerprint().encode('utf-8')
    except Exception:
        fp = b'no-device-fingerprint'
    return hashlib.sha256(_STATIC_SALT + fp).digest()


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt_key(plain: str) -> str:
    """把明文密钥混淆为落盘形式。空值原样返回。"""
    if not plain:
        return ''
    blob = _xor(plain.encode('utf-8'), _device_key())
    return _ENC_PREFIX + base64.b64encode(blob).decode('ascii')


def decrypt_key(stored: str) -> str:
    """还原落盘密钥。非本机生成 / 损坏时返回空串（触发重新配置）。"""
    if not stored:
        return ''
    if not stored.startswith(_ENC_PREFIX):
        # 兼容用户手工写入的明文（导入外部配置的场景）
        return stored
    try:
        blob = base64.b64decode(stored[len(_ENC_PREFIX):])
        return _xor(blob, _device_key()).decode('utf-8')
    except Exception:
        logger.warning('[AI配置] 密钥无法还原（可能来自其他设备），请重新填写')
        return ''


# ================================================================
# 中央管理器
# ================================================================
class AIConfigManager:
    """AI 配置中央管理器（进程内单例，线程安全）。"""

    _instance: Optional['AIConfigManager'] = None
    _instance_lock = threading.Lock()

    def __init__(self, path: Optional[Path] = None):
        self._lock = threading.RLock()
        self._path: Optional[Path] = Path(path) if path else None
        self._profiles: List[AIProfile] = []
        self._active_id: str = ''
        self._version: int = 0
        self._subscribers: List[Callable[[int], None]] = []
        self._file_mtime: float = -1.0
        self._last_stat_at: float = 0.0
        self._loaded = False

    # ---------- 单例 ----------
    @classmethod
    def instance(cls) -> 'AIConfigManager':
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
            path = self.path()
            try:
                if path.exists():
                    data = json.loads(path.read_text(encoding='utf-8'))
                    self._apply_raw(data)
                    self._file_mtime = path.stat().st_mtime
            except (OSError, ValueError) as e:
                logger.warning('[AI配置] 读取失败，将以空配置启动：%s', e)
            self._loaded = True

    def _apply_raw(self, data: Any) -> None:
        """把原始 JSON 结构应用到内存（已持锁）。"""
        if not isinstance(data, dict):
            return
        raw_profiles = data.get('profiles')
        if not isinstance(raw_profiles, list):
            return
        loaded: List[AIProfile] = []
        for item in raw_profiles:
            if not isinstance(item, dict):
                continue
            item = dict(item)
            # 落盘字段 api_key_enc → 内存字段 api_key
            enc = item.pop('api_key_enc', '')
            profile = AIProfile.from_dict(item)
            profile.api_key = decrypt_key(enc) if enc else item.get('api_key', '')
            loaded.append(profile)
        self._profiles = loaded
        active = data.get('active')
        if isinstance(active, str) and any(p.id == active for p in loaded):
            self._active_id = active
        elif loaded:
            self._active_id = loaded[0].id

    def save(self) -> bool:
        """原子写盘并触发热更新通知。"""
        with self._lock:
            path = self.path()
            payload = {
                'schema': SCHEMA_VERSION,
                'active': self._active_id,
                'profiles': [],
            }
            for p in self._profiles:
                item = asdict(p)
                item.pop('api_key', None)
                item['api_key_enc'] = encrypt_key(p.api_key)
                payload['profiles'].append(item)

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
            except OSError as e:
                logger.error('[AI配置] 写入失败：%s', e)
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
            with self._lock:
                if callback in self._subscribers:
                    self._subscribers.remove(callback)

        return unsubscribe

    def _notify(self, version: int) -> None:
        with self._lock:
            subs = list(self._subscribers)
        for cb in subs:
            try:
                cb(version)
            except Exception as e:
                logger.warning('[AI配置] 订阅者回调异常：%s', e)

    # ---------- 查询 ----------
    def list_profiles(self) -> List[AIProfile]:
        self.load()
        with self._lock:
            return [copy.deepcopy(p) for p in self._profiles]

    def get_active(self) -> Optional[AIProfile]:
        """返回当前生效的配置档副本；未配置时返回 None。"""
        self.load()
        with self._lock:
            for p in self._profiles:
                if p.id == self._active_id:
                    return copy.deepcopy(p)
            return copy.deepcopy(self._profiles[0]) if self._profiles else None

    def get_profile(self, profile_id: str) -> Optional[AIProfile]:
        self.load()
        with self._lock:
            for p in self._profiles:
                if p.id == profile_id:
                    return copy.deepcopy(p)
            return None

    @property
    def active_id(self) -> str:
        self.load()
        with self._lock:
            return self._active_id

    def is_configured(self) -> bool:
        """AI 功能是否可用（存在一个字段完整的生效配置）。"""
        profile = self.get_active()
        return bool(profile and profile.is_usable())

    def status_text(self) -> str:
        """供 UI 展示的一句话状态。"""
        profile = self.get_active()
        if profile is None:
            return '尚未配置 AI 模型，请在「设置」中填写 API 端点与密钥'
        err = profile.validate()
        if err:
            return f'当前配置不完整：{err}'
        return f'已就绪：{profile.name}（{profile.model}）'

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
    return get_config_manager().get_active()


def is_ai_configured() -> bool:
    return get_config_manager().is_configured()


def config_version() -> int:
    return get_config_manager().version


def subscribe(callback: Callable[[int], None]) -> Callable[[], None]:
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
