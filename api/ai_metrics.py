# -*- coding: utf-8 -*-
"""
api/ai_metrics.py — AI 调用层轻量指标采集器（无第三方依赖）

【定位】
仅服务于「LLM 调用层调优」的可观测性需求。
记录每次 chat_completion / 缓存命中 / 解析降级的关键指标：
  - 延迟（首响 / 总耗时）
  - HTTP 状态、重试次数、最终成败
  - 缓存命中 / 写入
  - Token 用量（上游 usage）
  - JSON 解析阶段（成功 / 清洗次数 / 失败降级）

【设计原则】
  1. 进程内环形缓冲 + 累计统计，零依赖、可热重置、单例线程安全；
  2. 不修改任何业务路径，仅做「旁路记录」，不影响请求行为；
  3. 提供导出接口，UI / 调试工具可直接拉取用于 A/B 对比与报告生成；
  4. 内存常驻上限可控（默认保留最近 500 条事件 + 累计计数），避免长跑膨胀。

【不做什么】
  - 不替代 logging；只采集结构化指标，文本日志仍走 core.log_handler；
  - 不做远程上报；如需外发请调用方自行处理；
  - 不参与请求决策；限速/熔断是 api/ai_throttle.py 的职责。
"""
from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import dataclass, asdict
from typing import Any, Deque, Dict, List, Optional


# ================================================================
# 数据结构
# ================================================================
@dataclass
class CallEvent:
    """单次 AI 调用的完整事件。

    字段命名与下游报告列名一一对应，避免后续再映射。
    """
    ts: float                       # unix 时间戳（秒，浮点）
    pan_type: str                   # bazi / meihua / xuan_kong
    model: str                      # 上游模型名
    success: bool                   # 是否最终成功（拿到可解析的 JSON）
    status_code: Optional[int]      # HTTP 状态码；None 表示连接级失败
    attempts: int                   # 实际重试次数（含首次 = 1）
    latency_ms: float               # 总耗时（毫秒）
    first_byte_ms: Optional[float]  # 首字节延迟（毫秒，None 表示无法测量）
    prompt_chars: int               # 输入提示词字符数
    completion_chars: int           # 返回内容字符数
    prompt_tokens: int              # usage.prompt_tokens
    completion_tokens: int          # usage.completion_tokens
    total_tokens: int               # usage.total_tokens
    cache_hit: bool                 # 是否命中本地缓存
    parse_stage: str                # ok / cleaned / fallback
    error_type: str = ''            # 失败时的错误类型（timeout / request / quota / parse / None）


@dataclass
class CacheEvent:
    """单次缓存读写事件。"""
    ts: float
    pan_type: str
    op: str          # hit / miss / write / write_fail
    input_hash: str
    question_hash: str


# ================================================================
# 指标采集器（单例）
# ================================================================
class AIMetricsCollector:
    """进程内 AI 调用指标采集器（线程安全）。"""

    _instance: Optional['AIMetricsCollector'] = None
    _instance_lock = threading.Lock()

    def __init__(self, max_events: int = 500):
        """初始化采集器。

        Args:
            max_events: 内存中保留的最近事件数；超出会自动弹出最旧事件。
        """
        self._lock = threading.RLock()
        self._max_events = max(50, int(max_events))
        self._call_events: Deque[CallEvent] = deque(maxlen=self._max_events)
        self._cache_events: Deque[CacheEvent] = deque(maxlen=self._max_events)
        # 累计计数器（不随 max_events 截断）
        self._counters: Dict[str, int] = {
            'calls_total': 0,
            'calls_success': 0,
            'calls_failed': 0,
            'cache_hits': 0,
            'cache_miss': 0,
            'cache_writes': 0,
            'cache_write_fail': 0,
            'parse_fallback': 0,
            'retries_total': 0,
        }
        self._started_at = time.time()

    # ---------- 单例 ----------
    @classmethod
    def instance(cls) -> 'AIMetricsCollector':
        """获取全局采集器实例（双重检查锁单例）。"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = AIMetricsCollector()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """仅供测试：丢弃单例与全部指标。"""
        with cls._instance_lock:
            cls._instance = None

    # ---------- 记录入口 ----------
    def record_call(self, event: CallEvent) -> None:
        """记录一次完整 AI 调用事件。"""
        with self._lock:
            self._call_events.append(event)
            self._counters['calls_total'] += 1
            if event.cache_hit:
                # 缓存命中不计入「API 调用成功」，仅计入缓存命中
                self._counters['cache_hits'] += 1
            else:
                if event.success:
                    self._counters['calls_success'] += 1
                else:
                    self._counters['calls_failed'] += 1
                self._counters['retries_total'] += max(0, event.attempts - 1)
            if event.parse_stage == 'fallback':
                self._counters['parse_fallback'] += 1

    def record_cache(self, event: CacheEvent) -> None:
        """记录一次缓存事件。"""
        with self._lock:
            self._cache_events.append(event)
            if event.op == 'hit':
                self._counters['cache_hits'] += 1
            elif event.op == 'miss':
                self._counters['cache_miss'] += 1
            elif event.op == 'write':
                self._counters['cache_writes'] += 1
            elif event.op == 'write_fail':
                self._counters['cache_write_fail'] += 1

    # ---------- 聚合统计 ----------
    def _percentile(self, values: List[float], p: float) -> float:
        """计算分位数（线性插值，p ∈ [0, 100]）。"""
        if not values:
            return 0.0
        sorted_v = sorted(values)
        if len(sorted_v) == 1:
            return float(sorted_v[0])
        rank = (p / 100.0) * (len(sorted_v) - 1)
        lo = int(math.floor(rank))
        hi = int(math.ceil(rank))
        if lo == hi:
            return float(sorted_v[lo])
        frac = rank - lo
        return float(sorted_v[lo] + (sorted_v[hi] - sorted_v[lo]) * frac)

    def summary(self) -> Dict[str, Any]:
        """汇总当前所有指标，返回可序列化的字典。

        返回结构包含：
          - overall：累计计数与运行时长
          - latency_ms：API 调用（非缓存）的延迟分位
          - by_pan_type：按排盘类型分组的关键指标
          - parse：JSON 解析阶段分布
          - last_calls：最近 20 条事件（按时间倒序）
        """
        with self._lock:
            calls = list(self._call_events)
            caches = list(self._cache_events)
            counters = dict(self._counters)
            uptime = max(0.001, time.time() - self._started_at)

        # 仅统计「真实 API 调用」（cache_hit=False）的延迟
        api_latencies: List[float] = []
        first_byte: List[float] = []
        total_tokens_list: List[int] = []
        retries_list: List[int] = []
        for c in calls:
            if c.cache_hit:
                continue
            api_latencies.append(c.latency_ms)
            if c.first_byte_ms is not None:
                first_byte.append(c.first_byte_ms)
            total_tokens_list.append(c.total_tokens)
            retries_list.append(c.attempts)

        # 按 pan_type 分组
        by_pan: Dict[str, Dict[str, Any]] = {}
        for c in calls:
            if c.cache_hit:
                continue
            slot = by_pan.setdefault(c.pan_type or 'unknown', {
                'count': 0, 'success': 0, 'failed': 0,
                'latencies_ms': [], 'tokens': 0, 'retries': 0,
            })
            slot['count'] += 1
            if c.success:
                slot['success'] += 1
            else:
                slot['failed'] += 1
            slot['latencies_ms'].append(c.latency_ms)
            slot['tokens'] += c.total_tokens
            slot['retries'] += max(0, c.attempts - 1)

        # 解析阶段分布
        parse_dist: Dict[str, int] = {'ok': 0, 'cleaned': 0, 'fallback': 0}
        for c in calls:
            if c.cache_hit:
                continue
            key = c.parse_stage if c.parse_stage in parse_dist else 'fallback'
            parse_dist[key] += 1

        # 错误类型分布
        error_dist: Dict[str, int] = {}
        for c in calls:
            if c.cache_hit or c.success:
                continue
            if c.error_type:
                error_dist[c.error_type] = error_dist.get(c.error_type, 0) + 1

        # 最近事件（按时间倒序，限制 20 条）
        recent = sorted(calls, key=lambda x: x.ts, reverse=True)[:20]
        recent_dicts: List[Dict[str, Any]] = []
        for c in recent:
            d = asdict(c)
            d['ts_iso'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(c.ts))
            recent_dicts.append(d)

        return {
            'overall': {
                **counters,
                'uptime_seconds': round(uptime, 1),
                'qps_real_api': round(
                    counters['calls_success'] + counters['calls_failed']
                ) / uptime if uptime > 0 else 0.0,
            },
            'latency_ms': {
                'samples': len(api_latencies),
                'p50': round(self._percentile(api_latencies, 50), 1),
                'p90': round(self._percentile(api_latencies, 90), 1),
                'p99': round(self._percentile(api_latencies, 99), 1),
                'avg': round(sum(api_latencies) / len(api_latencies), 1) if api_latencies else 0.0,
                'max': round(max(api_latencies), 1) if api_latencies else 0.0,
                'first_byte_p50': round(self._percentile(first_byte, 50), 1),
                'first_byte_p90': round(self._percentile(first_byte, 90), 1),
            },
            'tokens': {
                'samples': len(total_tokens_list),
                'total': sum(total_tokens_list),
                'avg_per_call': round(
                    sum(total_tokens_list) / len(total_tokens_list), 1
                ) if total_tokens_list else 0.0,
            },
            'retries': {
                'samples': len(retries_list),
                'avg': round(
                    sum(retries_list) / len(retries_list), 2
                ) if retries_list else 0.0,
                'max': max(retries_list) if retries_list else 0,
            },
            'by_pan_type': {
                k: {
                    'count': v['count'],
                    'success': v['success'],
                    'failed': v['failed'],
                    'success_rate': round(v['success'] / v['count'], 4) if v['count'] else 0.0,
                    'avg_latency_ms': round(
                        sum(v['latencies_ms']) / len(v['latencies_ms']), 1
                    ) if v['latencies_ms'] else 0.0,
                    'p90_latency_ms': round(self._percentile(v['latencies_ms'], 90), 1),
                    'tokens': v['tokens'],
                    'retries': v['retries'],
                }
                for k, v in by_pan.items()
            },
            'parse_distribution': parse_dist,
            'error_distribution': error_dist,
            'recent_events': recent_dicts,
            'cache_recent': [asdict(c) for c in list(caches)[-10:]],
        }

    def reset(self) -> None:
        """清空全部指标（保留单例）。"""
        with self._lock:
            self._call_events.clear()
            self._cache_events.clear()
            for k in self._counters:
                self._counters[k] = 0
            self._started_at = time.time()


# ================================================================
# 便捷函数
# ================================================================
def get_metrics() -> AIMetricsCollector:
    """获取全局指标采集器实例。"""
    return AIMetricsCollector.instance()


def record_call(event: CallEvent) -> None:
    """记录一次 AI 调用事件（便捷入口）。"""
    AIMetricsCollector.instance().record_call(event)


def record_cache(event: CacheEvent) -> None:
    """记录一次缓存事件（便捷入口）。"""
    AIMetricsCollector.instance().record_cache(event)
