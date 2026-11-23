# -*- coding: utf-8 -*-
"""
api/ai_throttle.py — AI 调用的并发限速 + 熔断保护（无第三方依赖）

【定位】
对 agnes_client.chat_completion 进行「调用前」的限速与熔断保护，避免：
  1. 突发并发把上游 API 打挂（被服务端 429）；
  2. 上游持续故障时，客户端无限重试浪费 token 与延迟；
  3. 极端情况下给上游造成「雪崩压力」。

【设计】
  1. 令牌桶限速：capacity=QPS 上限，refill_rate=QPS；
     每次 chat_completion 前必须先取到令牌，否则短暂等待。
  2. 熔断器（三态）：
     - CLOSED：正常通过；
     - OPEN：连续 N 次失败后熔断 M 秒，期间所有请求快速失败；
     - HALF_OPEN：熔断期满后放 1 个试探请求；成功 -> CLOSED；失败 -> OPEN。
  3. 状态均线程安全（threading.Lock），适合多线程/多 worker。

【与重试的关系】
  本模块只决定「这次调用能不能发出去」。
  上游真正的「重试 + 退避 + 抖动」仍在 agnes_client.chat_completion 内部，
  本模块与重试完全解耦，避免相互放大等待时间。

【可关闭】
  通过 enable(False) 可整体关闭（灰度上线时用），关闭后所有调用立即放行。
"""
from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


# ================================================================
# 异常
# ================================================================
class ThrottleBlockedError(Exception):
    """熔断器开启或令牌桶取不到时抛出的快速失败异常。"""

    def __init__(self, message: str, retry_after: float = 0.0):
        super().__init__(message)
        self.retry_after = retry_after


# ================================================================
# 令牌桶
# ================================================================
class TokenBucket:
    """简单令牌桶：按 refill_rate 持续补充令牌，上限 capacity。

    取令牌时若库存不足，按 max_wait 上限短暂等待；超时仍未取到则抛
    ThrottleBlockedError，让调用方决定如何降级。
    """

    def __init__(self, capacity: float, refill_rate: float):
        """
        Args:
            capacity:    桶容量（最大瞬时并发许可数）。
            refill_rate: 每秒补充令牌数（长期平均 QPS）。
        """
        self._capacity = float(capacity)
        self._refill_rate = float(refill_rate)
        self._tokens = float(capacity)
        self._last_ts = time.time()
        self._lock = threading.Lock()

    def acquire(self, max_wait: float = 5.0) -> bool:
        """尝试取 1 个令牌；返回 True/False，不抛异常（更友好）。"""
        deadline = time.time() + max(0.0, max_wait)
        while True:
            with self._lock:
                now = time.time()
                elapsed = max(0.0, now - self._last_ts)
                if elapsed > 0 and self._refill_rate > 0:
                    self._tokens = min(
                        self._capacity,
                        self._tokens + elapsed * self._refill_rate,
                    )
                    self._last_ts = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True
                # 估算下次有令牌的等待时间
                if self._refill_rate <= 0:
                    return False
                needed = 1.0 - self._tokens
                wait = needed / self._refill_rate
            if now + wait > deadline:
                return False
            time.sleep(min(wait, 0.05))


# ================================================================
# 熔断器
# ================================================================
class CircuitBreaker:
    """三态熔断器：CLOSED / OPEN / HALF_OPEN。

    状态机：
      CLOSED --(连续失败 >= failure_threshold)--> OPEN
      OPEN   --(经过 open_seconds)-------------> HALF_OPEN
      HALF_OPEN --(下一次调用成功)-------------> CLOSED
      HALF_OPEN --(下一次调用失败)-------------> OPEN（重新计时）
    """

    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

    def __init__(
            self,
            failure_threshold: int = 5,
            open_seconds: float = 30.0,
            half_open_max_probes: int = 1,
    ):
        """
        Args:
            failure_threshold:    CLOSED 状态下连续失败 N 次触发熔断。
            open_seconds:         OPEN 状态持续秒数。
            half_open_max_probes: HALF_OPEN 状态下允许放行的试探请求数。
        """
        self._failure_threshold = max(1, int(failure_threshold))
        self._open_seconds = max(1.0, float(open_seconds))
        self._half_open_max = max(1, int(half_open_max_probes))
        self._state = self.CLOSED
        self._fail_streak = 0
        self._opened_at: float = 0.0
        self._probes_in_flight = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        """当前状态（线程安全；OPEN 满期会自动转为 HALF_OPEN）。"""
        with self._lock:
            self._maybe_recover_locked()
            return self._state

    def _maybe_recover_locked(self) -> None:
        """OPEN 满期自动转入 HALF_OPEN（调用方须持锁）。"""
        if self._state == self.OPEN and (time.time() - self._opened_at) >= self._open_seconds:
            self._state = self.HALF_OPEN
            self._probes_in_flight = 0
            logger.info('[熔断] OPEN -> HALF_OPEN，放行试探请求')
            try:
                from core.sqlite_db import log_circuit_breaker_event
                log_circuit_breaker_event(self._state, self._fail_streak, 0)
            except Exception:
                pass

    def allow(self) -> bool:
        """是否允许本次调用通过。"""
        with self._lock:
            self._maybe_recover_locked()
            if self._state == self.CLOSED:
                return True
            if self._state == self.HALF_OPEN:
                if self._probes_in_flight < self._half_open_max:
                    self._probes_in_flight += 1
                    return True
                return False
            # OPEN：直接拒绝，记录快速失败日志
            logger.warning('[熔断] OPEN 状态，请求被快速拒绝，retry_after≈%.0fs', max(0.0, self._open_seconds - (time.time() - self._opened_at)))
            return False

    def on_success(self) -> None:
        """通知一次成功（调用后必须调用）。"""
        with self._lock:
            if self._state == self.HALF_OPEN:
                self._state = self.CLOSED
                self._fail_streak = 0
                self._probes_in_flight = 0
                logger.info('[熔断] HALF_OPEN -> CLOSED，恢复正常')
                try:
                    from core.sqlite_db import log_circuit_breaker_event
                    log_circuit_breaker_event(self._state, 0, 0)
                except Exception:
                    pass
            else:
                self._fail_streak = 0

    def on_failure(self) -> None:
        """通知一次失败（调用后必须调用）。"""
        with self._lock:
            if self._state == self.HALF_OPEN:
                self._state = self.OPEN
                self._opened_at = time.time()
                self._probes_in_flight = 0
                logger.warning('[熔断] HALF_OPEN -> OPEN，重新计时')
                try:
                    from core.sqlite_db import log_circuit_breaker_event
                    log_circuit_breaker_event(self._state, self._fail_streak, 1)
                except Exception:
                    pass
                return
            self._fail_streak += 1
            if self._state == self.CLOSED and self._fail_streak >= self._failure_threshold:
                self._state = self.OPEN
                self._opened_at = time.time()
                logger.warning(
                    '[熔断] CLOSED -> OPEN（连续失败 %d 次，熔断 %d 秒）',
                    self._fail_streak, int(self._open_seconds),
                )
                try:
                    from core.sqlite_db import log_circuit_breaker_event
                    log_circuit_breaker_event(self._state, self._fail_streak, 1)
                except Exception:
                    pass

    def reset(self) -> None:
        """强制回到 CLOSED（管理 / 测试用）。"""
        with self._lock:
            self._state = self.CLOSED
            self._fail_streak = 0
            self._probes_in_flight = 0
            self._opened_at = 0.0
            try:
                from core.sqlite_db import log_circuit_breaker_event
                log_circuit_breaker_event(self._state, 0, 0)
            except Exception:
                pass


# ================================================================
# 限速 + 熔断 协调器（单例）
# ================================================================
@dataclass
class ThrottleConfig:
    """限速 + 熔断参数（热重载用）。"""
    enabled: bool = True
    qps_capacity: float = 4.0      # 桶容量（瞬时并发许可）
    qps_refill: float = 2.0        # 每秒补充令牌数（长期 QPS）
    acquire_max_wait: float = 5.0  # 取令牌最长等待秒数
    failure_threshold: int = 5     # 连续失败多少次触发熔断
    open_seconds: float = 30.0     # 熔断持续秒数


class AIThrottle:
    """进程内限速 + 熔断协调器（线程安全单例）。"""

    _instance: Optional['AIThrottle'] = None
    _instance_lock = threading.Lock()

    def __init__(self, config: Optional[ThrottleConfig] = None):
        self._lock = threading.RLock()
        self._config = config or ThrottleConfig()
        self._bucket = TokenBucket(
            capacity=self._config.qps_capacity,
            refill_rate=self._config.qps_refill,
        )
        self._breaker = CircuitBreaker(
            failure_threshold=self._config.failure_threshold,
            open_seconds=self._config.open_seconds,
        )
        self._enabled = bool(self._config.enabled)

    @classmethod
    def instance(cls) -> 'AIThrottle':
        """获取全局单例（双重检查锁）。"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = AIThrottle()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """仅供测试：丢弃单例。"""
        with cls._instance_lock:
            cls._instance = None

    # ---------- 配置 ----------
    def configure(self, config: ThrottleConfig) -> None:
        """整体重配（热重载）。"""
        with self._lock:
            self._config = config
            self._enabled = bool(config.enabled)
            self._bucket = TokenBucket(
                capacity=config.qps_capacity,
                refill_rate=config.qps_refill,
            )
            self._breaker = CircuitBreaker(
                failure_threshold=config.failure_threshold,
                open_seconds=config.open_seconds,
            )

    @property
    def enabled(self) -> bool:
        """限速 + 熔断是否启用（可被运行时关闭）。"""
        with self._lock:
            return self._enabled

    def enable(self, flag: bool) -> None:
        """开启 / 关闭限速熔断（关闭后调用立即放行，不做限速也不计失败）。"""
        with self._lock:
            self._enabled = bool(flag)

    def status(self) -> dict:
        """返回当前状态（用于指标展示与调试面板）。"""
        with self._lock:
            return {
                'enabled': self._enabled,
                'breaker_state': self._breaker.state,
                'config': {
                    'qps_capacity': self._config.qps_capacity,
                    'qps_refill': self._config.qps_refill,
                    'acquire_max_wait': self._config.acquire_max_wait,
                    'failure_threshold': self._config.failure_threshold,
                    'open_seconds': self._config.open_seconds,
                },
            }

    # ---------- 准入 ----------
    def enter(self) -> None:
        """进入临界区（取令牌 + 熔断放行）；任一拒绝即抛 ThrottleBlockedError。

        【P2-13】不在持有全局 ``_lock`` 时等待令牌：令牌桶在库存不足时会 sleep
        最长 acquire_max_wait（默认 5s），旧实现把该 sleep 夹在 ``with self._lock``
        内，导致其它线程连进入都要排队，整体被串行化。现改为「锁内只做快照，
        等待在锁外进行」，令牌桶自身仍有独立锁保护其状态。

        Raises:
            ThrottleBlockedError: 熔断开启 / 令牌桶等待超时
        """
        with self._lock:
            if not self._enabled:
                return
            # 锁内只取快照，不在此处等待；configure() 中途换组件也不会混用
            cfg = self._config
            breaker = self._breaker
            bucket = self._bucket
        if not breaker.allow():
            # 熔断告警日志
            state = breaker.state
            if state == breaker.OPEN:
                remaining = max(0.0, cfg.open_seconds - (time.time() - breaker._opened_at))
                logger.warning('[熔断告警] 请求被熔断器快速失败，当前状态=%s，剩余熔断时间≈%.0fs', state, remaining)
            else:
                logger.warning('[熔断告警] 请求被熔断器快速失败，当前状态=%s', state)
            raise ThrottleBlockedError(
                f'熔断器处于 {state} 状态，请求被快速失败',
                retry_after=cfg.open_seconds,
            )
        if not bucket.acquire(cfg.acquire_max_wait):
            logger.warning('[限速告警] 令牌桶等待超时，当前 QPS 配置 capacity=%s refill=%s', cfg.qps_capacity, cfg.qps_refill)
            raise ThrottleBlockedError(
                '请求过于频繁，令牌桶等待超时',
                retry_after=1.0 / max(cfg.qps_refill, 0.01),
            )

    def exit(self, success: bool) -> None:
        """退出临界区，通知熔断器成功 / 失败。

        仅在 enabled=True 且本次调用真正进入过（breaker.allow 返回 True）时
        才有意义；为简化调用方，对所有调用统一调用本方法即可。
        """
        with self._lock:
            if not self._enabled:
                return
            if success:
                self._breaker.on_success()
            else:
                self._breaker.on_failure()


# ================================================================
# 上下文管理器（推荐使用方式）
# ================================================================
@contextmanager
def guarded_call():
    """限速 + 熔断保护的 with 上下文。

    用法：
        with guarded_call():
            resp = client.chat_completion(messages)
    失败时（已成功进入但上游报错）必须调用 exit(success=False)，因此本上下文
    只能在「成功路径」下简化使用；失败路径请改用 try/except 显式调用 exit。

    为简单起见，本上下文管理器约定：
        - yield 内部正常返回 -> 视为成功；
        - yield 内部抛任何异常 -> 视为失败；
        - 上下文管理器内部不再 throw（异常向上抛给业务层处理）。
    """
    throttle = AIThrottle.instance()
    throttle.enter()
    try:
        yield
    except BaseException:
        throttle.exit(success=False)
        raise
    else:
        throttle.exit(success=True)
