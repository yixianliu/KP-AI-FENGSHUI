# -*- coding: utf-8 -*-
"""
core/ai_cache.py — AI 分析调用本地缓存层（P2-4）

目的：
- 同盘 + 同问题命中本地 SQLite 缓存，避免重复调用 API（节省 token + 加速响应）。
- 缓存键 = (pan_type, input_hash, question_hash)，三者一致视为同一请求。
- 失效策略：默认永不失效（命理分析结论稳定）；提供 `clear_old()` LRU 清理接口（按 hit_count）。

设计要点：
- 缓存层对 analysis_pipeline 透明：run_* 入口先查缓存，未命中走 API 后写缓存。
- 表 schema 嵌入 schema_sqlite.sql；首次运行由 ensure_initialized() 自动建表（无需种子）。
- 运行时自愈：`ensure_cache_table()` 会在 ai_cache 表缺失的旧主库上自动建表（按 DB 路径追踪，测试切换临时库也安全）。
- 缓存写入与命中均记录日志；hit_count > 1 时附加 "[AI 缓存] 命中第 N 次" 标记。
"""
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional

from core import sqlite_db
from core.sqlite_db import get_connection

logger = logging.getLogger(__name__)

# 缓存表 DDL（与 schema_sqlite.sql 中 ai_cache 定义保持一致，用于运行时自愈建表）
_CACHE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS ai_cache (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    pan_type      TEXT    NOT NULL,
    input_hash    TEXT    NOT NULL,
    question_hash TEXT    NOT NULL,
    ai_json       TEXT    NOT NULL,
    hit_count     INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    last_used_at  TEXT    NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    UNIQUE (pan_type, input_hash, question_hash)
)
'''

# 已建表锁：按 DB 路径追踪，避免每条缓存操作都跑一次建表检测，
# 同时支持测试/运行时切换 _DB_PATH 后仍能自愈新库。
_TABLE_READY_PATH = None


def ensure_cache_table() -> None:
    """幂等确保 ai_cache 表存在（用于真实主库早于 schema 固化时自愈）。

    按当前 sqlite_db._DB_PATH 追踪是否已建表；路径变化（测试切换临时库）时
    自动重新建表，避免全局标志导致新库漏建。
    显式调用 sqlite_db.ensure_initialized() 且已是含 ai_cache 的新库则不会进入此分支。
    """
    global _TABLE_READY_PATH
    current_path = getattr(sqlite_db, '_DB_PATH', None)
    if _TABLE_READY_PATH == current_path:
        return
    con = get_connection()
    try:
        con.execute(_CACHE_TABLE_SQL)
        con.commit()
        _TABLE_READY_PATH = current_path
    finally:
        con.close()


# 参与 input_hash 计算的输入字段（与排盘计算相关的核心字段）
_BAZI_KEY_FIELDS = ('name', 'gender', 'year', 'month', 'day', 'hour', 'minute', 'longitude', 'is_lunar')
_MEIHUA_KEY_FIELDS = ('method', 'year', 'month', 'day', 'hour', 'minute', 'question', 'numbers', 'text')
_LIUREN_KEY_FIELDS = ('method', 'year', 'month', 'day', 'hour', 'minute', 'question')
_COMPREHENSIVE_KEY_FIELDS = ('question', 'bazi', 'meihua', 'liuren')

_PAN_TYPE_FIELDS = {
    'bazi': _BAZI_KEY_FIELDS,
    'meihua': _MEIHUA_KEY_FIELDS,
    'liuren': _LIUREN_KEY_FIELDS,
    'comprehensive': _COMPREHENSIVE_KEY_FIELDS,
}


def _normalize(obj: Any) -> Any:
    """递归规范化：dict 按 key 排序、tuple 转 list、None 保持 None。"""
    if isinstance(obj, dict):
        return {k: _normalize(obj[k]) for k in sorted(obj.keys()) if obj[k] is not None}
    if isinstance(obj, (list, tuple)):
        return [_normalize(x) for x in obj]
    return obj


def compute_input_hash(pan_type: str, input_data: Dict[str, Any]) -> str:
    """计算 (pan_type, input_data) 的稳定哈希（SHA256 前 32 字符）。

    仅纳入该 pan_type 的核心字段，避免 UI 临时字段（如 question）污染 hash。
    """
    fields = _PAN_TYPE_FIELDS.get(pan_type, ())
    picked = {k: input_data.get(k) for k in fields if k in input_data}
    normalized = _normalize(picked)
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()[:32]


def compute_question_hash(question: Any) -> str:
    """计算问题的稳定哈希（用户问事不同则不命中缓存）。"""
    q = (question or '').strip() if isinstance(question, str) else str(question or '')
    return hashlib.sha256(q.encode('utf-8')).hexdigest()[:32]


def make_cache_key(pan_type: str, input_data: Dict[str, Any], question: Any = None) -> tuple:
    """构造缓存主键 (pan_type, input_hash, question_hash)。"""
    return (
        pan_type,
        compute_input_hash(pan_type, input_data),
        compute_question_hash(question),
    )


def get_cached_result(pan_type: str, input_data: Dict[str, Any], question: Any = None) -> Optional[Dict[str, Any]]:
    """查询缓存：命中返回 dict；未命中返回 None。

    副作用：命中时原子更新 last_used_at 与 hit_count。
    """
    ensure_cache_table()
    key = make_cache_key(pan_type, input_data, question)
    con = get_connection()
    try:
        row = con.execute(
            'SELECT ai_json, hit_count FROM ai_cache '
            'WHERE pan_type=? AND input_hash=? AND question_hash=?',
            key
        ).fetchone()
        if row is None:
            logger.debug(f'[AI 缓存] 未命中 pan_type={pan_type} input_hash={key[1][:8]}...')
            return None
        ai_json = row['ai_json']
        hit_count = row['hit_count'] or 0
        try:
            ai = json.loads(ai_json) if isinstance(ai_json, str) else ai_json
        except (json.JSONDecodeError, TypeError):
            logger.warning(f'[AI 缓存] 命中但 JSON 解析失败（pan_type={pan_type}），按未命中处理')
            return None

        # 原子更新 hit_count
        try:
            con.execute(
                'UPDATE ai_cache SET hit_count=?, last_used_at=CURRENT_TIMESTAMP '
                'WHERE pan_type=? AND input_hash=? AND question_hash=?',
                (hit_count + 1, *key)
            )
            con.commit()
        except Exception as e:
            logger.warning(f'[AI 缓存] 更新 hit_count 失败（忽略）: {e}')

        logger.info(f'[AI 缓存] 命中 pan_type={pan_type} input_hash={key[1][:8]}... '
                    f'hit_count={hit_count + 1}')
        # 在返回结果上附加 _cache_hit 标记，便于上层 UI 渲染「缓存命中第 N 次」
        if isinstance(ai, dict):
            ai['_cache_hit_count'] = hit_count + 1
        return ai
    finally:
        con.close()


def save_to_cache(pan_type: str, input_data: Dict[str, Any], question: Any,
                  ai_result: Dict[str, Any]) -> bool:
    """写入缓存：成功 True，失败 False。

    只缓存非空结果；写失败仅记日志不抛异常（避免缓存错误影响正常流程）。
    """
    if not ai_result or not isinstance(ai_result, dict):
        return False
    ensure_cache_table()
    key = make_cache_key(pan_type, input_data, question)
    # 不缓存带 _cache_hit_count 标记的二次结果（避免污染）
    ai_json = json.dumps(ai_result, ensure_ascii=False)
    con = get_connection()
    try:
        # UPSERT: 已存在则更新 ai_json 与 last_used_at，保留 hit_count；不存在则 INSERT
        con.execute(
            'INSERT INTO ai_cache '
            '  (pan_type, input_hash, question_hash, ai_json, hit_count, created_at, last_used_at) '
            'VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) '
            'ON CONFLICT(pan_type, input_hash, question_hash) DO UPDATE '
            '  SET ai_json=excluded.ai_json, last_used_at=CURRENT_TIMESTAMP',
            (key[0], key[1], key[2], ai_json)
        )
        con.commit()
        logger.info(f'[AI 缓存] 写入 pan_type={pan_type} input_hash={key[1][:8]}... '
                    f'question_len={len(question) if isinstance(question, str) else 0}')
        return True
    except Exception as e:
        logger.warning(f'[AI 缓存] 写入失败（忽略）: {e}')
        return False
    finally:
        con.close()


def get_cache_stats() -> Dict[str, Any]:
    """返回缓存统计：总条数、按 pan_type 分组、最近命中时间、节省调用次数。"""
    ensure_cache_table()
    con = get_connection()
    try:
        total_row = con.execute('SELECT COUNT(*) AS c, COALESCE(SUM(hit_count), 0) AS h '
                                'FROM ai_cache').fetchone()
        total = total_row['c']
        total_hits = total_row['h']
        by_type_rows = con.execute(
            'SELECT pan_type, COUNT(*) AS c, COALESCE(SUM(hit_count), 0) AS h, '
            '       MAX(last_used_at) AS last_used '
            'FROM ai_cache GROUP BY pan_type ORDER BY pan_type'
        ).fetchall()
        return {
            'total_entries': total,
            'total_hits': total_hits,
            'total_calls_saved': total_hits,  # 每次 hit_count +1 代表节省 1 次 API 调用
            'by_type': [dict(r) for r in by_type_rows],
        }
    finally:
        con.close()


def clear_old(min_hit_count_to_keep: int = 1) -> int:
    """清理 hit_count < min_hit_to_keep 的缓存条目，返回清理条数。"""
    ensure_cache_table()
    con = get_connection()
    try:
        cur = con.execute('DELETE FROM ai_cache WHERE hit_count < ?', (min_hit_count_to_keep,))
        deleted = cur.rowcount
        con.commit()
        logger.info(f'[AI 缓存] 清理 hit_count<{min_hit_count_to_keep} 的 {deleted} 条缓存')
        return deleted
    finally:
        con.close()


def clear_all() -> int:
    """清空全部缓存。返回清理条数。"""
    ensure_cache_table()
    con = get_connection()
    try:
        cur = con.execute('DELETE FROM ai_cache')
        deleted = cur.rowcount
        con.commit()
        logger.info(f'[AI 缓存] 清空全部 {deleted} 条缓存')
        return deleted
    finally:
        con.close()
