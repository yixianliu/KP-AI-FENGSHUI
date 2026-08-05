"""
AGNES AI 客户端模块（中转版）

【架构变更说明】
本模块曾直接持有上游 API 密钥并调用 api.agnes-ai.cn。该做法存在无法修补的
安全缺陷：随 exe 分发的密钥可被抓包、内存扫描、解包反编译等方式取走，
代码混淆与反调试对前两者完全无效。

现改为：客户端 --(设备令牌)--> 自建中转服务 --(上游密钥)--> Agnes AI
        客户端不再持有任何上游密钥。

【对外契约保持不变】
    AgnesClient / get_agnes_client / load_agnes_config
    AgnesClientError / AgnesRequestError / AgnesTimeoutError / AgnesResponseError
    AgnesClient.chat_completion(messages, temperature, max_tokens)
        -> {'content': str, 'usage': dict}
    AgnesClient._clean_json_response / _validate_json_result
上层 core.analysis_pipeline、ui.main_window 无需改动。

【客户端持有的凭据】
    relay.app_key   —— 准入密钥，随 exe 分发，「必然会泄露」，仅作门槛用
    设备令牌         —— 一机一份，服务端可单独吊销与限额
两者泄露均不影响上游密钥安全，这正是本架构的意义。
"""

import threading
import json
import time
import logging
import configparser
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# 默认中转服务地址（发布前须改为你自己的域名，且必须是 HTTPS）
DEFAULT_RELAY_BASE_URL = 'https://relay.example.com'


# ================================================================
# 异常定义（保持原有层次，上层 except 逻辑不受影响）
# ================================================================
class AgnesClientError(Exception):
    """客户端基础异常"""
    pass


class AgnesRequestError(AgnesClientError):
    """请求发送或接口返回错误（网络层 / HTTP 非 200）"""
    def __init__(self, message: str, status_code: Optional[int] = None):
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


def _is_transient_status(status_code: Optional[int]) -> bool:
    """
    判定 HTTP 状态码是否为「可重试的瞬时错误」。

    注意 429 不在其中：中转服务用 429 表示配额用尽，重试无意义；
    上游繁忙已由中转服务映射为 503。
    """
    if status_code is None:
        return False
    return status_code in (500, 502, 503, 504)


# ================================================================
# 配置加载
# ================================================================
def load_relay_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    从 config.ini 读取 [relay] 段配置。

    配置项均非机密：
        base_url  中转服务地址
        app_key   客户端准入密钥（会随 exe 泄露，仅作门槛）
        model     模型名，仅用于分析记录展示；真正生效的模型由服务端强制指定
    """
    if config_path is None:
        from core.path_utils import get_config_path
        config_path = get_config_path()
    else:
        config_path = Path(config_path)

    parser = configparser.ConfigParser()
    parser.read(str(config_path), encoding='utf-8')

    section = 'relay'

    def _get(key: str, default: str) -> str:
        if parser.has_section(section) and parser.has_option(section, key):
            return parser.get(section, key)
        return default

    def _get_int(key: str, default: str) -> int:
        try:
            return int(_get(key, default))
        except (TypeError, ValueError):
            return int(default)

    return {
        'base_url': _get('base_url', DEFAULT_RELAY_BASE_URL).rstrip('/'),
        'app_key': _get('app_key', ''),
        'model': _get('model', 'agnes-2.5-flash'),
        'max_retries': _get_int('max_retries', '2'),
        'retry_delay': _get_int('retry_delay', '5'),
        'timeout': _get_int('timeout', '120'),
    }


# 兼容别名：历史代码与测试仍以 load_agnes_config 名称引用
load_agnes_config = load_relay_config


# ================================================================
# 客户端
# ================================================================
class AgnesClient:
    """
    AI 客户端（经由自建中转服务）。

    对外行为与旧版一致；内部改为携带设备令牌访问中转服务，
    不再持有、不再传输任何上游 API 密钥。
    """

    def __init__(self, config_path: Optional[str] = None, verify_ssl: bool = True):
        """
        Args:
            config_path: 配置文件路径，默认读取应用目录 config.ini
            verify_ssl: 是否校验 SSL 证书，默认 True（生产环境请勿关闭）
        """
        config = load_relay_config(config_path)
        self.base_url: str = config['base_url']
        self.app_key: str = config['app_key']
        self.model: str = config['model']
        self.max_retries: int = config['max_retries']
        self.retry_delay: int = config['retry_delay']
        self.timeout: int = config['timeout']
        self.verify_ssl: bool = verify_ssl

        self._device_token: Optional[str] = None
        self._token_lock = threading.Lock()

        if not self.base_url:
            raise AgnesClientError(
                '中转服务地址未配置，请在 config.ini 的 [relay] 段配置 base_url'
            )
        if not self.app_key:
            raise AgnesClientError(
                '客户端准入密钥未配置，请在 config.ini 的 [relay] 段配置 app_key'
            )
        if self.base_url.startswith('http://'):
            # 明文 HTTP 会导致设备令牌在链路上裸奔
            logger.warning('[relay] 中转服务使用明文 HTTP，设备令牌存在被窃听风险')

    # ------------------------------------------------------------
    # 依赖惰性导入
    # ------------------------------------------------------------
    @staticmethod
    def _requests():
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
    # 设备注册与令牌
    # ------------------------------------------------------------
    def _register_device(self) -> str:
        """向中转服务注册本机，换取设备令牌。"""
        from core.device_identity import get_device_fingerprint, save_device_token

        requests = self._requests()
        url = f'{self.base_url}/v1/register'
        payload = {
            'fingerprint': get_device_fingerprint(),
            'app_version': '5.0',
        }
        try:
            resp = requests.post(
                url,
                headers={'Content-Type': 'application/json',
                         'X-App-Key': self.app_key},
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
        except Exception as e:
            raise AgnesRequestError(f'设备注册请求失败: {e}') from e

        if resp.status_code == 429:
            raise AgnesQuotaError('设备注册过于频繁，请稍后再试')
        if resp.status_code != 200:
            raise AgnesRequestError(
                f'设备注册失败（HTTP {resp.status_code}）',
                status_code=resp.status_code,
            )

        try:
            token = resp.json().get('device_token', '')
        except ValueError as e:
            raise AgnesResponseError('设备注册响应格式异常') from e

        if not token:
            raise AgnesResponseError('设备注册未返回令牌')

        save_device_token(token)
        logger.info('[relay] 设备注册成功')
        return token

    def _ensure_token(self, force_refresh: bool = False) -> str:
        """获取可用设备令牌：优先本地缓存，缺失或强制刷新时重新注册。"""
        from core.device_identity import load_device_token, clear_device_token

        with self._token_lock:
            if force_refresh:
                self._device_token = None
                clear_device_token()

            if self._device_token:
                return self._device_token

            token = load_device_token()
            if token:
                self._device_token = token
                return token

            token = self._register_device()
            self._device_token = token
            return token

    # ------------------------------------------------------------
    # 核心调用
    # ------------------------------------------------------------
    def chat_completion(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        经中转服务发起对话补全。

        Args / Returns / Raises 与旧版完全一致，上层无需改动。

        Returns:
            dict: {"content": str, "usage": dict}

        Raises:
            AgnesRequestError: HTTP 非 200 或网络请求异常
            AgnesTimeoutError: 请求超时（重试耗尽后）
            AgnesResponseError: 响应结构解析失败
            AgnesQuotaError:    配额用尽
        """
        requests = self._requests()
        url = f'{self.base_url}/v1/chat'
        payload = {
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }

        token = self._ensure_token()
        reauth_used = False
        last_err: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug('[relay] 第 %d 次请求中转服务', attempt + 1)
                resp = requests.post(
                    url,
                    headers={'Content-Type': 'application/json',
                             'Authorization': f'Bearer {token}'},
                    json=payload,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                )

                # 令牌失效或被吊销：清除后重新注册并重试一次
                if resp.status_code in (401, 403) and not reauth_used:
                    reauth_used = True
                    logger.info('[relay] 设备令牌失效，正在重新注册')
                    token = self._ensure_token(force_refresh=True)
                    continue

                if resp.status_code == 429:
                    raise AgnesQuotaError(self._detail(resp, '使用次数已达上限'))

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
                        '[relay] HTTP %s 瞬时错误（第 %d 次），%d 秒后重试',
                        e.status_code, attempt + 1, delay,
                    )
                    time.sleep(delay)
                    continue
                raise
            except requests.exceptions.Timeout as e:
                last_err = e
                logger.warning('[relay] 请求超时（第 %d 次）', attempt + 1)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise AgnesTimeoutError('请求超时，请检查网络后重试') from e
            except requests.exceptions.RequestException as e:
                last_err = e
                logger.warning('[relay] 请求异常（第 %d 次）', attempt + 1)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise AgnesRequestError('无法连接分析服务，请检查网络') from e

        raise AgnesRequestError(f'未知错误: {last_err}')

    # ------------------------------------------------------------
    # 响应处理
    # ------------------------------------------------------------
    @staticmethod
    def _detail(resp, fallback: str) -> str:
        """提取中转服务返回的 detail 文案（已由服务端确保不含敏感信息）。"""
        try:
            detail = resp.json().get('detail')
            if isinstance(detail, str) and detail:
                return detail
        except Exception:
            pass
        return fallback

    @staticmethod
    def _extract_content(data: Any) -> str:
        """
        从中转服务响应中提取回复文本。

        兼容 OpenAI 结构 {"choices":[{"message":{"content":...}}]}
        与中转服务的简化结构 {"content": "..."}。
        """
        if isinstance(data, dict) and 'content' in data:
            return data.get('content') or ''
        if isinstance(data, dict) and 'choices' in data:
            choices = data.get('choices') or []
            if choices and isinstance(choices[0], dict):
                message = choices[0].get('message', {}) or {}
                return message.get('content', '') or ''
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
        这样可兜住模型偶发返回字符串/字典而非数组的情况，避免下游校验与渲染失败。
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
# 全局单例（线程安全）
# ================================================================
_default_client: Optional[AgnesClient] = None
_singleton_lock = threading.Lock()


def get_agnes_client() -> AgnesClient:
    """获取（惰性创建）客户端单例，线程安全。"""
    global _default_client
    if _default_client is None:
        with _singleton_lock:
            if _default_client is None:
                _default_client = AgnesClient()
    return _default_client
