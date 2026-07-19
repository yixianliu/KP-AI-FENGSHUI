"""
AGNES AI 模型客户端模块
基于 agnes-2.0-flash API（apihub.agnes-ai.com）封装 AI 分析调用接口
接口调试脚本见 scripts/agnes_test_client.py：
    POST https://apihub.agnes-ai.com/v1/chat/completions
    Headers:
        Content-Type: application/json
        Authorization: Bearer <api_key>
    Body:
        {
            "model": "agnes-2.0-flash",
            "messages": [ {"role": "system", "content": ...}, {"role": "user", "content": ...} ]
        }
返回值为 OpenAI 兼容的 chat/completions 结构：
    {
        "choices": [ {"message": {"role": "assistant", "content": "..."}} ],
        "usage": {...}
    }
"""

import threading
import json
import time
import logging
import configparser
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# ================================================================
# 异常定义
# ================================================================
class AgnesClientError(Exception):
    """AGNES 客户端基础异常"""
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


def _is_transient_status(status_code: Optional[int]) -> bool:
    """
    判定 HTTP 状态码是否为「可重试的瞬时错误」。

    包括：
      - 429 限流（Too Many Requests）
      - 500 服务器内部错误
      - 502 网关错误
      - 503 服务不可用（如 system memory overloaded 过载）
      - 504 网关超时
    其余（如 4xx 客户端错误）不可重试。
    """
    if status_code is None:
        return False
    return status_code in (429, 500, 502, 503, 504)


# ================================================================
# 配置加载
# ================================================================
def load_agnes_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    从 config.ini 读取 [agnes] 段配置（不再兼容已废弃的 [ernie]/百度千帆配置）。

    Returns:
        dict，包含 api_url / api_key / model / max_retries / retry_delay / timeout
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / 'config.ini'
    else:
        config_path = Path(config_path)

    parser = configparser.ConfigParser()
    parser.read(str(config_path), encoding='utf-8')

    section = 'agnes'

    def _get(key: str, default: str) -> str:
        if parser.has_section(section) and parser.has_option(section, key):
            return parser.get(section, key)
        return default

    return {
        'api_url': _get('api_url', 'https://apihub.agnes-ai.com/v1/chat/completions'),
        'api_key': _get('api_key', ''),
        'model': _get('model', 'agnes-2.0-flash'),
        'max_retries': int(_get('max_retries', '3')),
        'retry_delay': int(_get('retry_delay', '3')),
        'timeout': int(_get('timeout', '120')),
    }


# ================================================================
# 客户端
# ================================================================
class AgnesClient:
    """
    AGNES AI 模型客户端
    封装对 apihub.agnes-ai.com 的 chat/completions 调用，
    对外提供稳定的 chat/completions 调用契约，便于上层直接消费。
    """

    def __init__(self, config_path: Optional[str] = None, verify_ssl: bool = True):
        """
        Args:
            config_path: 配置文件路径，默认读取项目根目录 config.ini
            verify_ssl: 是否校验 SSL 证书，默认 True
        """
        config = load_agnes_config(config_path)
        self.api_url: str = config['api_url']
        self.api_key: str = config['api_key']
        self.model: str = config['model']
        self.max_retries: int = config['max_retries']
        self.retry_delay: int = config['retry_delay']
        self.timeout: int = config['timeout']
        self.verify_ssl: bool = verify_ssl

        if not self.api_url:
            raise AgnesClientError("API地址未配置，请在 config.ini 的 [agnes] 段配置 api_url")
        if not self.api_key:
            raise AgnesClientError("API密钥未配置，请在 config.ini 的 [agnes] 段配置 api_key")

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
        调用 AGNES chat/completions 接口，进行多轮对话补全。

        Args:
            messages: 消息列表，例如
                [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
            temperature: 采样温度（OpenAI 兼容参数）
            max_tokens: 最大生成 token 数（OpenAI 兼容参数）

        Returns:
            dict: {"content": str, "usage": dict}
                返回结构遵循 OpenAI 兼容的 chat/completions 格式，便于上层直接消费。

        Raises:
            AgnesRequestError: HTTP 非 200 或网络请求异常
            AgnesTimeoutError: 请求超时（重试耗尽后）
            AgnesResponseError: 响应结构解析失败
        """
        # 惰性导入：未安装 requests/urllib3 时，仅本方法在调用时报错，
        # 不影响整个模块（及依赖它的 analysis_pipeline / main_window）的导入与启动。
        try:
            import requests
            import urllib3
            from urllib3.exceptions import InsecureRequestWarning
            urllib3.disable_warnings(InsecureRequestWarning)
        except ImportError as e:
            raise AgnesClientError(
                f"缺少依赖 {e.name}，请先安装：pip install requests urllib3"
            ) from e

        headers = {
            'Content-Type': 'application/json',
            'Authorization': self.api_key,
        }
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }

        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    "[AGNES] 第 %d 次请求 %s model=%s",
                    attempt + 1, self.api_url, self.model
                )
                resp = requests.request(
                    'POST',
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                )

                if resp.status_code != 200:
                    raise AgnesRequestError(
                        f"HTTP {resp.status_code}: {resp.text[:500]}",
                        status_code=resp.status_code,
                    )

                try:
                    data = resp.json()
                except ValueError as e:
                    raise AgnesResponseError(f"响应不是合法 JSON: {e}") from e

                content = self._extract_content(data)
                usage = data.get('usage', {}) if isinstance(data, dict) else {}
                return {'content': content, 'usage': usage}

            except AgnesResponseError:
                # 响应解析失败属业务错误，不重试
                raise
            except AgnesRequestError as e:
                # 5xx / 429 等瞬时错误（如服务过载 system memory overloaded）可重试；
                # 其余 4xx 属客户端错误，直接上抛。
                if attempt < self.max_retries and _is_transient_status(e.status_code):
                    delay = self.retry_delay * (2 ** attempt)
                    last_err = e
                    logger.warning(
                        "[AGNES] HTTP %s 瞬时错误（第 %d 次），%d 秒后重试：%s",
                        e.status_code, attempt + 1, delay, e,
                    )
                    time.sleep(delay)
                    continue
                raise
            except requests.exceptions.Timeout as e:
                last_err = e
                logger.warning("[AGNES] 请求超时（第 %d 次），%s", attempt + 1, e)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise AgnesTimeoutError(f"请求超时: {e}") from e
            except requests.exceptions.RequestException as e:
                last_err = e
                logger.warning("[AGNES] 请求异常（第 %d 次），%s", attempt + 1, e)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise AgnesRequestError(f"请求失败: {e}") from e

        # 理论上不会到达这里
        raise AgnesRequestError(f"未知错误: {last_err}")

    # ------------------------------------------------------------
    # 响应内容提取
    # ------------------------------------------------------------
    @staticmethod
    def _extract_content(data: Any) -> str:
        """
        从 OpenAI 兼容的响应中提取助手回复文本。

        兼容结构：
            {"choices": [{"message": {"content": "..."}}]}
        以及简化的 {"content": "..."} 结构。
        """
        if isinstance(data, dict) and 'choices' in data:
            choices = data.get('choices') or []
            if choices and isinstance(choices[0], dict):
                message = choices[0].get('message', {}) or {}
                return message.get('content', '') or ''
        if isinstance(data, dict) and 'content' in data:
            return data.get('content') or ''
        raise AgnesResponseError(f"响应中未找到 content 字段: {str(data)[:300]}")

    # ------------------------------------------------------------
    # 响应清洗 / 校验（与历史实现契约保持一致）
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
        校验并补全 AI 返回的 JSON 结果，保证 required_fields 均存在，
        缺失字段以空列表（或 final_verdict 以空字符串）兜底。
        """
        if not isinstance(analysis, dict):
            analysis = {}
        for field in required_fields:
            if field not in analysis or analysis[field] is None:
                analysis[field] = '' if field == 'final_verdict' else []
        return analysis


# ================================================================
# 全局单例（线程安全）
# ================================================================
_default_client: Optional[AgnesClient] = None
_singleton_lock = threading.Lock()


def get_agnes_client() -> AgnesClient:
    """获取（惰性创建）AGNES 客户端单例，线程安全。"""
    global _default_client
    if _default_client is None:
        with _singleton_lock:
            # 双重检查：防止两个线程同时进入 if 块
            if _default_client is None:
                _default_client = AgnesClient()
    return _default_client
