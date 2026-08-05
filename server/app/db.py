# -*- coding: utf-8 -*-
"""
server/app/db.py — 中转服务的设备与配额存储（SQLite）

与桌面端保持一致的技术选型：本地嵌入式 SQLite，无需额外数据库服务。

表结构：
  devices           设备注册表（只存令牌摘要，不存明文）
  usage_daily       单设备逐日调用计数
  global_daily      全局逐日调用计数（保护上游账单）
  register_ip_daily 注册接口按 IP 逐日计数（防批量刷注册）

隐私约定：IP 只存 SHA-256 摘要，不留明文。
"""
from __future__ import annotations

import hashlib
import sqlite3
import threading
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional, Iterator

_SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS devices (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash   TEXT    NOT NULL UNIQUE,
    fingerprint  TEXT    NOT NULL,
    app_version  TEXT    NOT NULL DEFAULT '',
    created_at   TEXT    NOT NULL,
    last_seen_at TEXT    NOT NULL DEFAULT '',
    revoked      INTEGER NOT NULL DEFAULT 0,
    note         TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_devices_fingerprint ON devices(fingerprint);

CREATE TABLE IF NOT EXISTS usage_daily (
    device_id INTEGER NOT NULL,
    day       TEXT    NOT NULL,
    count     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (device_id, day)
);

CREATE TABLE IF NOT EXISTS global_daily (
    day   TEXT    PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS register_ip_daily (
    ip_hash TEXT    NOT NULL,
    day     TEXT    NOT NULL,
    count   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (ip_hash, day)
);
"""

_lock = threading.RLock()
_conn: Optional[sqlite3.Connection] = None
_db_path: Optional[str] = None


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def today() -> str:
    return date.today().isoformat()


def hash_ip(ip: str) -> str:
    """IP 仅以摘要形式留存，避免存储可回溯的个人信息。"""
    return hashlib.sha256((ip or 'unknown').encode('utf-8')).hexdigest()


def init_db(db_path: str) -> None:
    """初始化连接与表结构（进程内单连接 + 全局锁，够用且简单）。"""
    global _conn, _db_path
    with _lock:
        if _conn is not None and _db_path == db_path:
            return
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(db_path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(_SCHEMA)
        _conn.commit()
        _db_path = db_path


@contextmanager
def _cursor() -> Iterator[sqlite3.Cursor]:
    if _conn is None:
        raise RuntimeError('数据库未初始化，请先调用 init_db()')
    with _lock:
        cur = _conn.cursor()
        try:
            yield cur
            _conn.commit()
        except Exception:
            _conn.rollback()
            raise
        finally:
            cur.close()


# ------------------------------------------------------------------
# 设备
# ------------------------------------------------------------------
def create_device(token_hash: str, fingerprint: str, app_version: str) -> int:
    with _cursor() as cur:
        cur.execute(
            'INSERT INTO devices (token_hash, fingerprint, app_version, created_at, last_seen_at) '
            'VALUES (?, ?, ?, ?, ?)',
            (token_hash, fingerprint, app_version, _utcnow(), _utcnow()),
        )
        return int(cur.lastrowid)


def get_device_by_token_hash(token_hash: str) -> Optional[sqlite3.Row]:
    with _cursor() as cur:
        cur.execute(
            'SELECT id, revoked, fingerprint FROM devices WHERE token_hash = ?',
            (token_hash,),
        )
        return cur.fetchone()


def touch_device(device_id: int) -> None:
    with _cursor() as cur:
        cur.execute(
            'UPDATE devices SET last_seen_at = ? WHERE id = ?',
            (_utcnow(), device_id),
        )


def revoke_device(device_id: int, note: str = '') -> bool:
    with _cursor() as cur:
        cur.execute(
            'UPDATE devices SET revoked = 1, note = ? WHERE id = ?',
            (note, device_id),
        )
        return cur.rowcount > 0


def revoke_all_devices(note: str = '') -> int:
    """一键吊销全部设备令牌（应急开关）。"""
    with _cursor() as cur:
        cur.execute(
            'UPDATE devices SET revoked = 1, note = ? WHERE revoked = 0',
            (note,),
        )
        return cur.rowcount


def count_registered_devices(fingerprint: str) -> int:
    with _cursor() as cur:
        cur.execute(
            'SELECT COUNT(*) AS c FROM devices WHERE fingerprint = ? AND revoked = 0',
            (fingerprint,),
        )
        row = cur.fetchone()
        return int(row['c']) if row else 0


def find_active_device_by_fingerprint(fingerprint: str) -> Optional[sqlite3.Row]:
    with _cursor() as cur:
        cur.execute(
            'SELECT id FROM devices WHERE fingerprint = ? AND revoked = 0 '
            'ORDER BY id DESC LIMIT 1',
            (fingerprint,),
        )
        return cur.fetchone()


# ------------------------------------------------------------------
# 配额
# ------------------------------------------------------------------
def get_device_usage(device_id: int, day: str) -> int:
    with _cursor() as cur:
        cur.execute(
            'SELECT count FROM usage_daily WHERE device_id = ? AND day = ?',
            (device_id, day),
        )
        row = cur.fetchone()
        return int(row['count']) if row else 0


def get_global_usage(day: str) -> int:
    with _cursor() as cur:
        cur.execute('SELECT count FROM global_daily WHERE day = ?', (day,))
        row = cur.fetchone()
        return int(row['count']) if row else 0


def bump_usage(device_id: int, day: str) -> None:
    """设备计数与全局计数一起自增（同一事务，保证一致）。"""
    with _cursor() as cur:
        cur.execute(
            'INSERT INTO usage_daily (device_id, day, count) VALUES (?, ?, 1) '
            'ON CONFLICT(device_id, day) DO UPDATE SET count = count + 1',
            (device_id, day),
        )
        cur.execute(
            'INSERT INTO global_daily (day, count) VALUES (?, 1) '
            'ON CONFLICT(day) DO UPDATE SET count = count + 1',
            (day,),
        )


def bump_register_ip(ip_hash: str, day: str) -> int:
    with _cursor() as cur:
        cur.execute(
            'INSERT INTO register_ip_daily (ip_hash, day, count) VALUES (?, ?, 1) '
            'ON CONFLICT(ip_hash, day) DO UPDATE SET count = count + 1',
            (ip_hash, day),
        )
        cur.execute(
            'SELECT count FROM register_ip_daily WHERE ip_hash = ? AND day = ?',
            (ip_hash, day),
        )
        row = cur.fetchone()
        return int(row['count']) if row else 0


def stats() -> dict:
    """运营概览（管理接口用，不含任何敏感信息）。"""
    d = today()
    with _cursor() as cur:
        cur.execute('SELECT COUNT(*) AS c FROM devices')
        total = int(cur.fetchone()['c'])
        cur.execute('SELECT COUNT(*) AS c FROM devices WHERE revoked = 1')
        revoked = int(cur.fetchone()['c'])
    return {
        'devices_total': total,
        'devices_revoked': revoked,
        'devices_active': total - revoked,
        'global_usage_today': get_global_usage(d),
        'day': d,
    }
