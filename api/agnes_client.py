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

import random
import re
import time
import json
import logging

from typing import Dict, List, Optional, Any
from api.ai_throttle import AIThrottle, ThrottleBlockedError
from api.ai_metrics import CallEvent
# 日志/异常脱敏兜底：不依赖 logger 过滤器，失败路径显式打码
from core.secure_log import scrub

logger = logging.getLogger(__name__)


# ================================================================
# JSON 清洗 / 解析加固（与 _clean_json_response 互补，覆盖多轮提取）
# ================================================================
# 兼顾历史签名：上层仍通过 _clean_json_response 调用，这里只追加新逻辑
_JSON_FENCE_RE = re.compile(r'```(?:json|JSON)?\s*\n?(.*?)\n?```', re.DOTALL)
_JSON_FIRST_BRACE = re.compile(r'\{')


def _try_extract_balanced_json(text: str) -> Optional[str]:
    """在文本中寻找「第一个 '{' 之后到与之匹配的 '}' 之间的平衡 JSON 子串」。

    相比 rfind('}') 的「最右花括号」策略，本方法能正确处理模型返回中
    嵌套对象之外的散落文本（如解释、代码围栏未闭合）。找不到平衡括号
    时返回 None。
    """
    start = _JSON_FIRST_BRACE.search(text)
    if not start:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start.start(), len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start.start():i + 1]
    return None


def _deep_clean_json(content: str) -> str:
    """多层清洗：去代码围栏 -> 去 Gemini/LLM 思考标签 -> 取平衡 JSON 子串 -> 去除尾部逗号等常见坏 JSON。

    旧 _clean_json_response 使用 rfind('}')，在模型输出夹杂解释文字时
    极易「越界」吃掉后面的段落。本方法作为增强版被新代码使用，旧接口
    行为保持不变（兼容性）。

    新增：剔除 Gemini 风格的思考标签 <think>...</think> 等，避免这些标签污染 JSON 解析。
    """
    if not content:
        return ''
    text = content.strip()
    # 1) 去代码围栏（兼容 ```json / ```JSON / ```）
    fence_match = _JSON_FENCE_RE.search(text)
    if fence_match:
        text = fence_match.group(1).strip()
    # 1.5) 去 LLM 思考标签：<think>...</think>、[thinking]...</thinking> 等 Gemini 风格标签
    # 使用非贪婪匹配并跨行清理
    think_re = re.compile(r'(?i)<think>.*?</think>', re.DOTALL)
    text = think_re.sub('', text)
    think_re2 = re.compile(r'(?i)\[thinking\].*?\[/thinking\]', re.DOTALL)
    text = think_re2.sub('', text)
    # 2) 提取平衡 JSON 子串
    balanced = _try_extract_balanced_json(text)
    if balanced is not None:
        text = balanced
    # 3) 修正常见「JSON 不合法」瑕疵（仅限不影响语义的清理）
    #    - 末尾多余逗号：,]} 前的一个或多个逗号
    text = re.sub(r',(\s*[\]\}])', r'\1', text)
    #    - 行内注释 // ... 与 /* ... */（极少数模型会插入）
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r'(?m)^\s*//.*$', '', text)
    return text.strip()


def _retry_backoff(attempt: int, base: float, cap: float) -> float:
    """指数退避 + 完整抖动（Full Jitter）。

    AWS 推荐使用「Full Jitter」：sleep = random(0, min(cap, base * 2^attempt))
    比起「等长退避」能让大量客户端错峰回退，避免雷鸣群效应。
    """
    expo = base * (2 ** max(0, attempt))
    upper = min(cap, expo)
    if upper <= 0:
        return 0.0
    return random.uniform(0.0, upper)


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


class _StreamedResponse:
    """stream=True 路径的轻量响应快照。

    流式读取完成后原始 ``requests.Response`` 会被 ``close()`` 归还连接池，
    因此把外部调用需要的 ``.status_code`` / ``.text`` / ``.json()`` 固化到本对象，
    避免上层继续持有已关闭的响应。
    """

    def __init__(self, raw, body: bytes):
        self.status_code = raw.status_code
        self._body = body
        self.text = body.decode('utf-8', errors='replace')

    def json(self):
        """解析响应体 JSON（等价于 ``requests.Response.json()``）。"""
        return json.loads(self.text)


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
            AgnesNotConfiguredError: 尚未配置 AI 模型，或配置档校验未通过。
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
                '尚未配置 AI 模型。请打开「设置 → 文化研究算法配置」，'
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
        self.retry_delay: float = profile.retry_delay
        self.temperature: float = profile.temperature
        self.max_tokens: int = profile.max_tokens
        self.send_no_think: bool = profile.send_no_think
        self.verify_ssl: bool = verify_ssl if verify_ssl is not None else profile.verify_ssl
        self._config_version = -1

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

    def _calculate_prompt_chars(self, messages: List[Dict[str, str]]) -> int:
        """计算请求体大小（埋点用，估算 token 成本）。"""
        try:
            return sum(len(str(m.get('content', ''))) for m in messages)
        except Exception:
            return 0

    def _build_payload(self, messages: List[Dict[str, str]], temperature: Optional[float], max_tokens: Optional[int]) -> Dict[str, Any]:
        """构建请求payload。"""
        payload: Dict[str, Any] = {
            'model': self.model,
            'messages': messages,
            'temperature': self.temperature if temperature is None else temperature,
            'max_tokens': self.max_tokens if max_tokens is None else max_tokens,
            # 【请勿删除】显式声明非流式：OpenAI 兼容协议中 stream 未显式给出时，
            # 部分服务端会按默认行为返回 SSE 分片（data: {...} / [DONE]）。而本客户端
            # 是「整包读完后一次性 json.loads」，一旦上游真的返回 SSE，解析必然失败。
            # 显式传 False 可让上游稳定返回单个 JSON 对象，与本客户端的解析方式匹配。
            'stream': False,
        }
        if self.send_no_think:
            # 关闭思考模式以显著降低首响延迟（部分服务商支持）
            # 【关键性能修复，请勿删除】部分模型服务端默认开启 thinking，会先吐出
            # 一大段推理过程再给正文，实测单次分析响应从 20+ 秒降到约 1 秒。
            # 该键是 OpenAI 兼容协议的扩展字段，不认识它的服务端会直接忽略，
            # 因此保留没有兼容性代价；一旦删掉，性能会立刻退回到 20 秒级。
            payload['chat_template_kwargs'] = {'enable_thinking': False}
        return payload

    def _build_headers(self) -> Dict[str, str]:
        """构建请求headers。"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = self.api_key
        return headers

    def _handle_throttle_enter(self, throttle: 'AIThrottle', call_event: 'CallEvent', call_start: float) -> None:
        """处理限速进入，若被限速则快速失败并记录指标。"""
        try:
            throttle.enter()
        except ThrottleBlockedError:
            # 限速 / 熔断快速失败：直接记录并上抛，不再发请请求
            call_event.latency_ms = (time.time() - call_start) * 1000.0
            call_event.attempts = 0
            call_event.error_type = 'throttle'
            from api.ai_metrics import record_call
            record_call(call_event)
            raise

    # ------------------------------------------------------------
    # 核心调用
    # ------------------------------------------------------------
    def chat_completion(
            self,
            messages: List[Dict[str, str]],
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            *,
            pan_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        发起对话补全（OpenAI 兼容协议）。

        temperature / max_tokens 不传时使用配置档中的值。
        pan_type 仅用于指标埋点（区分排盘类型），不影响请求行为。

        Returns:
            dict: {"content": str, "usage": dict}

        Raises:
            AgnesRequestError: HTTP 非 200 或网络请求异常
            AgnesTimeoutError: 请求超时（重试耗尽后）
            AgnesResponseError: 响应结构解析失败
            AgnesQuotaError:    配额用尽
            api.ai_throttle.ThrottleBlockedError: 限速/熔断快速失败
        """
        # 初始化
        requests = self._requests()
        prompt_chars = self._calculate_prompt_chars(messages)
        payload = self._build_payload(messages, temperature, max_tokens)
        headers = self._build_headers()
        
        # 限速和指标设置
        from api.ai_throttle import AIThrottle, ThrottleBlockedError
        throttle = AIThrottle.instance()
        
        from api.ai_metrics import CallEvent
        call_event = CallEvent(
            ts=time.time(),
            pan_type=pan_type or '',
            model=self.model,
            success=False,
            status_code=None,
            attempts=0,
            latency_ms=0.0,
            first_byte_ms=None,
            prompt_chars=prompt_chars,
            completion_chars=0,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            cache_hit=False,
            parse_stage='fallback',
        )

        last_err: Optional[Exception] = None
        call_start = time.time()
        
        # 处理限速进入
        self._handle_throttle_enter(throttle, call_event, call_start)
        
        # 主重试循环
        try:
            for attempt in range(self.max_retries + 1):
                call_event.attempts = attempt + 1
                try:
                    logger.debug('[AI] 第 %d 次请求上游', attempt + 1)
                    # 首字节延迟：用 stream=True 取得首字节后再读完整 body
                    req_start = time.time()
                    # 【P1-05】TypeError 只包住 post() 本身：仅当 requests 不接受
                    # stream 参数时才走非流式兜底。此前 TypeError 覆盖了「请求已发出
                    # + 读取 body」整块，读取阶段抛出的 TypeError 会被误判为
                    # 「不支持 stream」而重新发一次请求（极端情况重复计费），
                    # 同时第一次的连接也不会被关闭。
                    stream_resp = None
                    try:
                        stream_resp = requests.post(
                            self.api_url,
                            headers=headers,
                            json=payload,
                            timeout=self.timeout,
                            verify=self.verify_ssl,
                            stream=True,
                        )
                    except TypeError:
                        stream_resp = None

                    if stream_resp is not None:
                        # 主路径：所有退出分支（含 429/401/403/非 200）都必须 close()，
                        # 否则连接不会归还连接池。
                        try:
                            self._raise_for_status(stream_resp)
                            # 读取完整响应体（chunked 传输下不可用 iter_content(1) 试探首字节，
                            # 否则会破坏后续分块读取，导致 body 丢失）
                            # 首字节耗时埋点：在「第一个非空 chunk 产出」处打点，而不是用请求开始
                            # 时间近似（旧写法恒为 0，指标失真）。该值仅用于观测，不参与控制流。
                            first_byte_ts: Optional[float] = None
                            _chunks = []
                            try:
                                for _chunk in stream_resp.iter_content(chunk_size=4096):
                                    if _chunk and first_byte_ts is None:
                                        first_byte_ts = time.time()
                                    _chunks.append(_chunk)
                                body_bytes = b''.join(_chunks)
                            except Exception as e:
                                raise AgnesRequestError(f'读取响应体时发生错误: {e}') from e
                            if not body_bytes or not body_bytes.strip():
                                raise AgnesResponseError('响应体为空，无法解析 JSON')
                            # 构造轻量响应快照，随后即可关闭原始响应（body 已读完）
                            resp = _StreamedResponse(stream_resp, body_bytes)
                            # first_byte_ts 为空说明一个 chunk 都没拿到（正常不会发生，
                            # 上面已判空），此时保持 None，不虚构数值。
                            if first_byte_ts is not None:
                                call_event.first_byte_ms = (first_byte_ts - req_start) * 1000.0
                        finally:
                            stream_resp.close()
                    else:
                        # 兜底：requests 不支持 stream 参数时的非流式请求
                        raw_resp = requests.post(
                            self.api_url,
                            headers=headers,
                            json=payload,
                            timeout=self.timeout,
                            verify=self.verify_ssl,
                        )
                        try:
                            self._raise_for_status(raw_resp)
                            # 非流式路径下 post() 返回即代表响应头已到达，
                            # 用「响应头到达时刻」作为首字节耗时的近似值（仅埋点用途）。
                            call_event.first_byte_ms = (time.time() - req_start) * 1000.0
                            # 非流式 body 已完整读取（stream=False），固化快照后再关闭
                            resp = _StreamedResponse(raw_resp, raw_resp.content)
                        finally:
                            raw_resp.close()

                    # 【关键】两条请求路径（stream=True 主路径 / 不支持 stream 的兜底路径）
                    # 在此汇合：统一解析响应体、记录成功埋点并返回。
                    # 历史缺陷：本段曾被错误缩进到 except TypeError 分支内，导致主路径
                    # 拿到 200 响应后既不解析也不返回，只能白跑到重试耗尽并抛「未知错误」。
                    call_event.status_code = resp.status_code

                    # 防御性检查：响应体为空时提前报错，避免 json.loads('') 抛出空值错误
                    try:
                        resp_content = resp.text
                    except Exception:
                        resp_content = ''
                    if not resp_content or not resp_content.strip():
                        raise AgnesResponseError('响应体为空，无法解析 JSON')
                    try:
                        data = resp.json()
                    except ValueError as e:
                        raise AgnesResponseError(f'响应不是合法 JSON: {e}') from e

                    content = self._extract_content(data)
                    usage = data.get('usage', {}) if isinstance(data, dict) else {}

                    # 记录成功
                    call_event.success = True
                    call_event.latency_ms = (time.time() - call_start) * 1000.0
                    call_event.completion_chars = len(content or '')
                    call_event.prompt_tokens = int(usage.get('prompt_tokens', 0) or 0)
                    call_event.completion_tokens = int(usage.get('completion_tokens', 0) or 0)
                    call_event.total_tokens = int(usage.get('total_tokens', 0) or 0)
                    call_event.parse_stage = 'ok'
                    # 成功埋点：记录耗时、重试次数，便于性能监控
                    logger.info(
                        '[AI] 请求成功 model=%s endpoint=%s 耗时=%.0fms attempts=%d tokens=%d',
                        self.model, self.api_url, call_event.latency_ms, call_event.attempts,
                        call_event.total_tokens
                    )
                    throttle.exit(success=True)
                    from api.ai_metrics import record_call
                    record_call(call_event)
                    return {'content': content, 'usage': usage}

                except (AgnesResponseError, AgnesQuotaError):
                    # 业务错误，重试无意义
                    raise
                except AgnesRequestError as e:
                    if attempt < self.max_retries and _is_transient_status(e.status_code):
                        delay = _retry_backoff(attempt, base=float(self.retry_delay), cap=60.0)
                        last_err = e
                        logger.warning(
                            '[AI] HTTP %s 瞬时错误（第 %d 次），%.2f 秒后重试，当前耗时=%.0fms',
                            e.status_code, attempt + 1, delay,
                            (time.time() - call_start) * 1000.0
                        )
                        time.sleep(delay)
                        continue
                    raise
                except (requests.exceptions.Timeout,) as e:
                    last_err = e
                    logger.warning('[AI] 请求超时（第 %d 次），当前耗时=%.0fms', attempt + 1, (time.time() - call_start) * 1000.0)
                    if attempt < self.max_retries:
                        delay = _retry_backoff(attempt, base=float(self.retry_delay), cap=60.0)
                        time.sleep(delay)
                        continue
                    raise AgnesTimeoutError('请求超时，请检查网络后重试') from e
                except (requests.exceptions.RequestException,) as e:
                    last_err = e
                    logger.warning('[AI] 请求异常（第 %d 次），当前耗时=%.0fms', attempt + 1, (time.time() - call_start) * 1000.0)
                    if attempt < self.max_retries:
                        delay = _retry_backoff(attempt, base=float(self.retry_delay), cap=60.0)
                        time.sleep(delay)
                        continue
                    raise AgnesRequestError('无法连接 AI 服务，请检查网络与端点地址') from e

            # 重试耗尽
            raise AgnesRequestError(f'未知错误: {last_err}')
        except BaseException as e:
            # 失败路径：通知熔断器 + 写入指标 + 记录详细错误日志（含堆栈）
            call_event.success = False
            call_event.latency_ms = (time.time() - call_start) * 1000.0
            call_event.completion_chars = 0
            call_event.parse_stage = 'fallback'
            # 【诊断关键】统一在失败出口记录一次结构化错误日志，包含：
            #   端点、模型、耗时、HTTP 状态码、错误类型、异常堆栈。
            # 之前只有零散的 logger.warning，导致"AI 无法使用"在日志中完全无法定位。
            # 使用 logger.error 而非 warning，确保在默认 INFO 级别的日志中可见。
            err_type = 'unknown'
            if isinstance(e, AgnesTimeoutError):
                err_type = 'timeout'
            elif isinstance(e, AgnesQuotaError):
                err_type = 'quota'
            elif isinstance(e, AgnesRequestError):
                err_type = 'request'
            elif isinstance(e, AgnesResponseError):
                err_type = 'response'
            call_event.error_type = err_type
            logger.error(
                '[AI] 调用失败 type=%s status=%s model=%s endpoint=%s 耗时=%.0fms '
                'attempts=%d err=%s',
                err_type, call_event.status_code, self.model, self.api_url,
                call_event.latency_ms, call_event.attempts, scrub(str(e)),
                exc_info=err_type == 'unknown',  # 未知错误保留完整堆栈便于排查
            )
            if isinstance(e, AgnesTimeoutError):
                throttle.exit(success=False)
                raise
            elif isinstance(e, AgnesQuotaError):
                throttle.exit(success=False)
                raise
            elif isinstance(e, AgnesRequestError):
                throttle.exit(success=False)
                raise
            elif isinstance(e, AgnesResponseError):
                # 响应体为空 / JSON 解析失败：属于上游响应异常，直接上抛
                # 避免被错误地包装为"未知错误"，方便调用方识别真实原因
                throttle.exit(success=False)
                raise
            else:
                throttle.exit(success=False)
                raise AgnesRequestError(f'未知错误: {e}') from e


    def _raise_for_status(self, resp) -> None:
        """按 HTTP 状态码抛对应业务异常（本方法不负责关闭 resp）。

        Args:
            resp: requests 响应对象（或等价替身），需具备 ``status_code`` /
                ``json()``；调用方在 finally 中负责 ``close()``。
        """
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

    def _detail(self, resp, default_msg: str) -> str:
        """提取上游错误详情（优先使用 JSON body 中的 message 字段）。

        兼容两种常见错误结构：
          1) OpenAI 标准：{"error": {"message": "..."}}
          2) 部分服务商扁平结构：{"message": "..."}
        仅当对应 message 为「非空值」时才采用，避免嵌套空串把上层默认文案
        覆盖成空字符串；两种结构都取不到（或解析失败）才回退 default_msg。
        """
        try:
            data = resp.json()
            if isinstance(data, dict):
                nested = data.get('error')
                if isinstance(nested, dict):
                    nested_msg = nested.get('message')
                    if nested_msg:
                        return str(nested_msg)
                flat_msg = data.get('message')
                if flat_msg:
                    return str(flat_msg)
        except Exception:
            pass
        return default_msg

    def _extract_content(self, data: Dict[str, Any]) -> str:
        """从上游响应中提取模型返回的文本内容。
        支持 OpenAI 兼容格式以及部分服务商的自定义字段。
        """
        if not isinstance(data, dict):
            return ''
        # OpenAI 兼容格式
        if 'choices' in data and isinstance(data['choices'], list):
            for choice in data['choices']:
                if isinstance(choice, dict) and 'message' in choice:
                    message = choice['message']
                    if isinstance(message, dict) and 'content' in message:
                        return message['content'] or ''
        # 某些服务商直接返回文本
        if 'content' in data:
            return data['content'] or ''
        # 兜底：返回空字符串
        return ''

    @staticmethod
    def parse_json_response(content: str) -> Optional[Dict[str, Any]]:
        """安全地从模型响应中提取 JSON 对象。
        使用 _deep_clean_json 进行多层清洗，然后尝试解析。
        如果解析失败，返回 None 而不是抛异常。
        """
        cleaned = _deep_clean_json(content)
        if not cleaned:
            return None
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _clean_json_response(content: str) -> str:
        """向后兼容的 JSON 清洗方法，委托给 _deep_clean_json。
        历史代码通过 AgnesClient._clean_json_response 调用。
        """
        return _deep_clean_json(content or '')


# ================================================================
# 工厂函数（保持向后兼容）
# ================================================================
_client_cache: Optional[AgnesClient] = None
_client_cache_version: int = 0


def invalidate_client() -> None:
    """清除客户端单例缓存，强制下次 get_agnes_client() 重建实例。

    主要用于测试环境清理全局状态，生产环境一般不需要调用。
    """
    global _client_cache, _client_cache_version
    _client_cache = None
    _client_cache_version = 0


def get_agnes_client() -> AgnesClient:
    """获取当前生效的 AgnesClient 实例（单例模式）。

    配置版本号未变时复用同一实例，避免重复建连。
    """
    from core.ai_config import get_config_manager
    global _client_cache, _client_cache_version
    manager = get_config_manager()
    current_version = manager.version
    if _client_cache is not None and _client_cache_version == current_version:
        return _client_cache
    _client_cache = AgnesClient(profile=manager.get_active())
    _client_cache_version = current_version
    return _client_cache


# 兼容历史别名
load_relay_config = load_ai_config
load_agnes_config = load_ai_config