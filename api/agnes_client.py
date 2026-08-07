"""
AI 客户端模块（配置全部来自 core.ai_config 中央管理器）

【架构说明】
本客户端**不再持有任何内置端点 / 密钥 / 模型名**。
运行所需的全部参数（模型类型、API 端点、认证信息、请求参数）
统一由 `core.ai_config.AIConfigManager` 提供，用户在 GUI「设置」中填写。

演进历史：
  1. 早期：密钥写死在 config.ini，随 exe 分发（已废弃，泄露风险）
  2. 中期：中转服务持有密钥（依赖服务器，已废弃）
  3. 现在：零内置凭据 + 用户自填配置（打包产物中不含任何 AI 原始信息）

【热更新】
`get_agnes_client()` 会比对配置版本号，用户在 GUI 改完配置点保存后，
下一次调用即自动使用新配置重建客户端，无需重启程序。

【对外契约保持不变】（上层 core.analysis_pipeline / ui.main_window 无需改动）
    AgnesClient / get_agnes_client / load_ai_config
    AgnesClientError / AgnesRequestError / AgnesTimeoutError / AgnesResponseError / AgnesQuotaError
    AgnesClient.chat_completion(messages, temperature, max_tokens) -> {'content': str, 'usage': dict}
    AgnesClient._clean_json_response / _validate_json_result
"""
from __future__ import annotations

import threading
import time
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# ================================================================
# 异常定义（保持原有层次，上层 except 逻辑不受影响）
# ================================================================
class AgnesClientError(Exception):
    """客户端基础异常"""
    pass


class AgnesRequestError(AgnesClientError):
    """请求发送或接口返回错误（网络层 / HTTP 非 200）"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        """
        Args:
            message:     面向用户的错误描述，须避免携带密钥等敏感信息。
            status_code: HTTP 状态码；None 表示压根没拿到响应（如连接失败）。
                         重试策略依赖此字段判定是否为瞬时错误，见 _is_transient_status。
        """
        super().__init__(message)
        self.status_code = status_code


class AgnesTimeoutError(AgnesClientError):
    """请求超时"""
    pass


class AgnesResponseError(AgnesClientError):
    """响应解析失败（非预期返回结构）"""
    pass


class AgnesQuotaError(AgnesClientError):
    """配额用尽（不可重试）"""
    pass


class AgnesNotConfiguredError(AgnesClientError):
    """尚未配置 AI 模型（首次运行的正常状态，非故障）"""
    pass


def _is_transient_status(status_code: Optional[int]) -> bool:
    """判定 HTTP 状态码是否为「可重试的瞬时错误」（429 不算，表示配额用尽）。"""
    if status_code is None:
        return False
    return status_code in (500, 502, 503, 504)


# ================================================================
# 配置读取：唯一来源为 core.ai_config
# ================================================================
def load_ai_config() -> Dict[str, Any]:
    """
    读取当前生效的 AI 配置（扁平字典，历史调用方兼容）。

    未配置时返回各字段为空的字典而非抛异常，交由调用方降级处理。
    返回值中的 api_key 为可直接用于 Authorization 头的完整值。
    """
    from core.ai_config import get_config_manager
    return get_config_manager().as_legacy_dict()


# 兼容历史别名（旧代码 / 测试曾以 load_relay_config / load_agnes_config 引用）
load_relay_config = load_ai_config
load_agnes_config = load_ai_config


# ================================================================
# 客户端
# ================================================================
class AgnesClient:
    """
    AI 客户端。所有参数来自中央配置管理器的「当前生效配置档」。

    Args:
        profile:     可选，直接指定配置档（GUI 中「保存前测试连接」用）。
                     不传则取中央管理器的生效配置。
        verify_ssl:  可选，覆盖配置档中的 SSL 校验开关。
        config_path: 历史兼容参数，已废弃（配置由中央管理器托管，忽略）。
    """

    def __init__(
            self,
            config_path: Optional[str] = None,
            verify_ssl: Optional[bool] = None,
            profile: Optional[Any] = None,
    ):
        """
        从配置档解出本次会话要用的端点、凭据与请求参数。

        Args:
            config_path: 历史兼容参数，已废弃且被忽略（配置改由中央管理器托管）。
            verify_ssl:  覆盖配置档中的 SSL 校验开关；None 表示沿用配置档取值。
            profile:     直接指定配置档，供 GUI「保存前测试连接」使用；
                         None 则向中央管理器索取当前生效配置。

        Raises:
            AgnesNotConfiguredError: 尚未配置任何 AI 模型，或配置档校验未通过。
        """
        from core.ai_config import get_config_manager

        manager = get_config_manager()
        if profile is None:
            profile = manager.get_active()
            self._config_version = manager.version
        else:
            self._config_version = -1  # 显式传入的临时配置，不参与版本比对

        if profile is None:
            raise AgnesNotConfiguredError(
                '尚未配置 AI 模型。请打开「设置 → 龙虎山大师兄配置」，'
                '填写 API 密钥后保存。'
            )

        err = profile.validate()
        if err:
            raise AgnesNotConfiguredError(f'AI 配置不完整：{err}')

        self.profile = profile
        self.api_url: str = profile.api_url.strip()
        self.api_key: str = profile.auth_header()
        self.model: str = profile.model.strip()
        self.timeout: int = profile.timeout
        self.max_retries: int = profile.max_retries
        self.retry_delay: int = profile.retry_delay
        self.temperature: float = profile.temperature
        self.max_tokens: int = profile.max_tokens
        self.send_no_think: bool = profile.send_no_think
        self.verify_ssl: bool = (
            profile.verify_ssl if verify_ssl is None else bool(verify_ssl)
        )

        if self.api_url.startswith('http://') and 'localhost' not in self.api_url \
                and '127.0.0.1' not in self.api_url:
            logger.warning('[AI] 使用明文 HTTP 访问远程服务，存在被窃听风险')

    # ------------------------------------------------------------
    # 依赖惰性导入
    # ------------------------------------------------------------
    @staticmethod
    def _requests():
        """
        惰性导入 requests，并静音自签名证书的 InsecureRequestWarning。

        之所以不在模块顶部导入：纯排盘场景（不调用 AI）无需网络依赖，
        延迟到真正发请求时再导入可缩短冷启动，也让缺依赖的报错带上安装指引。

        Returns:
            module: requests 模块对象。

        Raises:
            AgnesClientError: requests 或 urllib3 未安装。
        """
        try:
            import requests
            import urllib3
            from urllib3.exceptions import InsecureRequestWarning
            urllib3.disable_warnings(InsecureRequestWarning)
            return requests
        except ImportError as e:
            raise AgnesClientError(
                f"缺少依赖 {e.name}，请先安装：pip install requests urllib3"
            ) from e

    # ------------------------------------------------------------
    # 核心调用
    # ------------------------------------------------------------
    def chat_completion(
            self,
            messages: List[Dict[str, str]],
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        发起对话补全（OpenAI 兼容协议）。

        temperature / max_tokens 不传时使用配置档中的值。

        Returns:
            dict: {"content": str, "usage": dict}

        Raises:
            AgnesRequestError: HTTP 非 200 或网络请求异常
            AgnesTimeoutError: 请求超时（重试耗尽后）
            AgnesResponseError: 响应结构解析失败
            AgnesQuotaError:    配额用尽
        """
        requests = self._requests()
        payload: Dict[str, Any] = {
            'model': self.model,
            'messages': messages,
            'temperature': self.temperature if temperature is None else temperature,
            'max_tokens': self.max_tokens if max_tokens is None else max_tokens,
        }
        if self.send_no_think:
            # 关闭思考模式以显著降低首响延迟（部分服务商支持）
            # 【关键性能修复，请勿删除】部分模型服务端默认开启 thinking，会先吐出
            # 一大段推理过程再给正文，实测单次分析响应从 20+ 秒降到约 1 秒。
            # 该键是 OpenAI 兼容协议的扩展字段，不认识它的服务端会直接忽略，
            # 因此保留没有兼容性代价；一旦删掉，性能会立刻退回到 20 秒级。
            payload['chat_template_kwargs'] = {'enable_thinking': False}

        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = self.api_key

        last_err: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug('[AI] 第 %d 次请求上游', attempt + 1)
                resp = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                )

                if resp.status_code == 429:
                    raise AgnesQuotaError(self._detail(resp, '使用次数已达上限'))

                if resp.status_code in (401, 403):
                    raise AgnesRequestError(
                        self._detail(resp, '认证失败，请在「设置」中检查 API 密钥'),
                        status_code=resp.status_code,
                    )

                if resp.status_code != 200:
                    raise AgnesRequestError(
                        self._detail(resp, f'服务返回 HTTP {resp.status_code}'),
                        status_code=resp.status_code,
                    )

                try:
                    data = resp.json()
                except ValueError as e:
                    raise AgnesResponseError(f'响应不是合法 JSON: {e}') from e

                content = self._extract_content(data)
                usage = data.get('usage', {}) if isinstance(data, dict) else {}
                return {'content': content, 'usage': usage}

            except (AgnesResponseError, AgnesQuotaError):
                # 业务错误，重试无意义
                raise
            except AgnesRequestError as e:
                if attempt < self.max_retries and _is_transient_status(e.status_code):
                    delay = self.retry_delay * (2 ** attempt)
                    last_err = e
                    logger.warning(
                        '[AI] HTTP %s 瞬时错误（第 %d 次），%d 秒后重试',
                        e.status_code, attempt + 1, delay,
                    )
                    time.sleep(delay)
                    continue
                raise
            except requests.exceptions.Timeout as e:
                last_err = e
                logger.warning('[AI] 请求超时（第 %d 次）', attempt + 1)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise AgnesTimeoutError('请求超时，请检查网络后重试') from e
            except requests.exceptions.RequestException as e:
                last_err = e
                logger.warning('[AI] 请求异常（第 %d 次）', attempt + 1)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise AgnesRequestError('无法连接 AI 服务，请检查网络与端点地址') from e

        raise AgnesRequestError(f'未知错误: {last_err}')

    # ------------------------------------------------------------
    # 响应处理
    # ------------------------------------------------------------
    @staticmethod
    def _detail(resp, fallback: str) -> str:
        """提取上游返回的错误描述（确保不含敏感信息）。"""
        try:
            data = resp.json()
            detail = data.get('detail')
            if isinstance(detail, str) and detail:
                return detail
            error = data.get('error')
            if isinstance(error, dict) and isinstance(error.get('message'), str):
                return error['message']
            if isinstance(error, str) and error:
                return error
        except Exception:
            pass
        return fallback

    @staticmethod
    def _extract_content(data: Any) -> str:
        """从 OpenAI 兼容响应中提取回复文本。"""
        if isinstance(data, dict) and 'choices' in data:
            choices = data.get('choices') or []
            if choices and isinstance(choices[0], dict):
                message = choices[0].get('message', {}) or {}
                return message.get('content', '') or ''
        if isinstance(data, dict) and 'content' in data:
            return data.get('content') or ''
        raise AgnesResponseError('响应中未找到 content 字段')

    # ------------------------------------------------------------
    # JSON 清洗 / 校验（逻辑与旧版完全一致，上层依赖不变）
    # ------------------------------------------------------------
    @staticmethod
    def _clean_json_response(content: str) -> str:
        """
        清洗模型返回的 JSON 文本：
        - 去除 ```json ... ``` 代码围栏
        - 截取首个 '{' 到最后一个 '}' 之间的内容
        """
        if not content:
            return ''
        text = content.strip()

        if text.startswith('```'):
            lines = text.splitlines()
            if lines and lines[0].strip().startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines).strip()

        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]
        return text

    @staticmethod
    def _validate_json_result(analysis: Any, required_fields: List[str]) -> Dict[str, Any]:
        """
        校验并补全 AI 返回的 JSON 结果，保证 required_fields 均存在且类型正确：
        - 数组类字段（非 final_verdict）必须为「字符串列表」；
          缺失/None -> 空列表；字符串 -> 包成单元素列表；字典 -> 取值列表；其他 -> 字符串化后包列表。
        - final_verdict 必须为字符串；列表 -> 换行拼接；其他 -> 字符串化。
        """
        if not isinstance(analysis, dict):
            analysis = {}
        string_fields = {'final_verdict', 'disclaimer'}
        for field in required_fields:
            value = analysis.get(field)
            if field in string_fields:
                if value is None or value == '':
                    analysis[field] = ''
                elif isinstance(value, list):
                    analysis[field] = '\n'.join(str(x) for x in value if x)
                elif not isinstance(value, str):
                    analysis[field] = str(value)
            else:
                if value is None:
                    analysis[field] = []
                elif isinstance(value, list):
                    analysis[field] = [str(x) for x in value if x is not None]
                elif isinstance(value, str):
                    analysis[field] = [value] if value.strip() else []
                elif isinstance(value, dict):
                    analysis[field] = [str(v) for v in value.values() if v is not None]
                else:
                    analysis[field] = [str(value)]
        return analysis


# ================================================================
# 全局单例（线程安全 + 配置热更新感知）
# ================================================================
_default_client: Optional[AgnesClient] = None
_singleton_lock = threading.Lock()


def get_agnes_client() -> AgnesClient:
    """
    获取客户端单例（线程安全）。

    热更新：若中央配置版本号已变化（用户在 GUI 改了配置），
    此处会自动丢弃旧实例并按新配置重建，无需重启程序。
    """
    global _default_client

    from core.ai_config import get_config_manager
    current_version = get_config_manager().version

    client = _default_client
    if client is not None and client._config_version == current_version:
        return client

    with _singleton_lock:
        client = _default_client
        if client is not None and client._config_version == current_version:
            return client
        _default_client = AgnesClient()
        if client is not None:
            logger.info('[AI] 配置已更新，客户端已按新配置重建')
        return _default_client


def invalidate_client() -> None:
    """强制丢弃客户端单例（配置保存后可显式调用，通常无需手动触发）。"""
    global _default_client
    with _singleton_lock:
        _default_client = None
