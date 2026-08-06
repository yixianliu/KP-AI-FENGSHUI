# -*- coding: utf-8 -*-
"""
core/sqlite_db.py — 本地嵌入式 SQLite 数据库统一连接层。

职责:
- 解析数据库文件路径 data/fengshui.db（源码运行 / PyInstaller 打包均兼容）。
- 首次运行时若数据库不存在，则从 database/schema_sqlite.sql 建库（schema + 命理参考数据）。
- 提供 get_connection()（row_factory=dict 工厂，兼容 .get()）作为所有存储模块的共享连接源。

设计说明:
- 打包 (frozen) 时，schema 文件为只读资源（位于 sys._MEIPASS），数据库文件写入
  可写目录（exe 同级 data/，若不可写则回退到用户目录 ~/.kp-fengshui/data）。
- 源码运行时，数据库与 schema 均位于项目根目录 database/ 与 data/ 下。
- 建库采用「临时文件 + 原子替换」，避免中途失败留下损坏的半成品库。
"""
import os
import sys
import sqlite3
import logging
import threading

from core.path_utils import get_resource_path, get_data_dir

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_DB_PATH = None
_SCHEMA_PATH = None
_INITIALIZED = False


def _resource_root():
    """只读资源根目录：打包后为解包临时目录，源码为项目根目录。"""
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _is_writable(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        test = os.path.join(path, '.write_test')
        with open(test, 'w') as f:
            f.write('ok')
        os.remove(test)
        return True
    except OSError:
        return False


def _data_dir() -> str:
    """可写数据目录，与 core.path_utils.get_data_dir() 保持一致。"""
    return str(get_data_dir())


def get_db_path() -> str:
    global _DB_PATH
    if _DB_PATH is None:
        _DB_PATH = os.path.join(_data_dir(), 'fengshui.db')
    return _DB_PATH


def get_schema_path() -> str:
    global _SCHEMA_PATH
    if _SCHEMA_PATH is None:
        # 优先使用可写目录下的 schema（若有），否则从资源目录读取
        resource_schema = get_resource_path('database/schema_sqlite.sql')
        _SCHEMA_PATH = str(resource_schema)
    return _SCHEMA_PATH


def _build_database(db_path: str, schema_path: str):
    """从 schema_sqlite.sql 构建数据库（原子写入）。"""
    if not os.path.exists(schema_path):
        raise FileNotFoundError('SQLite schema 文件不存在: %s' % schema_path)

    tmp_path = db_path + '.tmp'
    if os.path.exists(tmp_path):
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    con = sqlite3.connect(tmp_path)
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            con.executescript(f.read())
        con.commit()
    finally:
        con.close()

    os.replace(tmp_path, db_path)
    logger.info('已从 %s 构建 SQLite 数据库: %s', schema_path, db_path)


def ensure_initialized():
    """确保数据库存在；首次运行时建库。线程安全。"""
    global _INITIALIZED
    if _INITIALIZED:
        return
    with _LOCK:
        if _INITIALIZED:
            return
        db_path = get_db_path()
        if not os.path.exists(db_path):
            _build_database(db_path, get_schema_path())
        _INITIALIZED = True


def _dict_factory(cursor, row):
    """将 SQLite 行转为 dict——兼容 dict.get(key, default) 调用,
    行为对齐迁移前的 MySQL DictCursor（字典式行），避免 'sqlite3.Row' object
    has no attribute 'get' 这类错误。"""
    return dict(zip((col[0] for col in cursor.description), row))


def get_connection() -> sqlite3.Connection:
    """获取一个 SQLite 连接（每次调用返回新连接，调用方负责 close）。

    - row_factory=dict 工厂：支持按列名访问以及 .get(key, default) 取值，
      与迁移前 MySQL 字典式行行为一致。
    - check_same_thread=False：允许在 Qt 工作线程中使用。
    - WAL 模式提升读写并发。
    """
    ensure_initialized()
    con = sqlite3.connect(get_db_path(), timeout=30, check_same_thread=False,
                          factory=_Connection)
    con.row_factory = _dict_factory
    try:
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('PRAGMA foreign_keys=OFF')
    except sqlite3.Error:
        pass
    return con


def row_to_dict(row):
    """sqlite3.Row → dict（None 安全）。"""
    return dict(row) if row is not None else None


class _Connection(sqlite3.Connection):
    """sqlite3.Connection 子类：`with conn:` 结束后在提交/回滚之余自动 close，避免连接泄漏。"""

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            self.close()
