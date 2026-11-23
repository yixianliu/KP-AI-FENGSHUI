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
# 正在执行初始化的线程 ident：仅用于识别同线程递归（见 ensure_initialized）
_INIT_OWNER = None


def _resource_root():
    """只读资源根目录：打包后为解包临时目录，源码为项目根目录。"""
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 熔断历史日志表
_BREAKER_HISTORY_TABLE = '''
CREATE TABLE IF NOT EXISTS circuit_breaker_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    state TEXT NOT NULL,
    failure_count INTEGER NOT NULL DEFAULT 0,
    open_count INTEGER NOT NULL DEFAULT 0
)
'''


def _is_writable(path: str) -> bool:
    """判断指定目录是否可写：尝试建目录并写入/删除临时文件。异常一律视为不可写。"""
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
    """返回数据库文件路径（data/fengshui.db），结果带缓存（模块级 _DB_PATH）。"""
    global _DB_PATH
    if _DB_PATH is None:
        _DB_PATH = os.path.join(_data_dir(), 'fengshui.db')
    return _DB_PATH


def get_schema_path() -> str:
    """返回建库用的 schema_sqlite.sql 路径，结果带缓存（模块级 _SCHEMA_PATH）。"""
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
        # journal_mode=WAL 是数据库级持久属性，写入 DB 头后长期有效。
        # 只在这里设置一次：每个连接重复执行该 PRAGMA 会多一次锁尝试，
        # 失败还会被静默吞掉（见 get_connection 的说明）。
        con.execute('PRAGMA journal_mode=WAL')
        with open(schema_path, 'r', encoding='utf-8') as f:
            con.executescript(f.read())
        con.commit()
    finally:
        con.close()

    os.replace(tmp_path, db_path)
    logger.info('已从 %s 构建 SQLite 数据库: %s', schema_path, db_path)


def _ensure_breaker_history_table():
    """确保熔断历史表存在"""
    con = get_connection()
    try:
        con.execute(_BREAKER_HISTORY_TABLE)
        con.commit()
    finally:
        con.close()


def _ensure_pan_records_input_json():
    """幂等迁移：为老库的 pan_records 补 input_json 列（允许 NULL）。

    新建库由 schema_sqlite.sql 直接带列；老库通过 PRAGMA table_info 检查后
    ALTER TABLE 添加，不做整表重建，已有记录保持原样（payload 走回退分支）。
    """
    con = get_connection()
    try:
        columns = {row['name'] for row in
                   con.execute('PRAGMA table_info(pan_records)').fetchall()}
        if 'input_json' not in columns:
            con.execute('ALTER TABLE pan_records ADD COLUMN input_json TEXT')
            con.commit()
            logger.info('已为 pan_records 补充 input_json 列')
    except Exception as exc:  # noqa: BLE001 - 迁移失败不应阻断启动
        logger.warning('pan_records.input_json 迁移失败（将沿用回退 payload）：%s', exc)
    finally:
        con.close()

def ensure_initialized():
    """确保数据库已建成（表 + 初始数据可用）；首次运行时建库。线程安全。

    「标志可见 = 表已可用」：``_INITIALIZED`` 只在 schema 建库、熔断历史表补建、
    pan_records 迁移**全部完成之后**才置 True。旧实现提前置位，导致其它线程
    在本线程建表尚未完成时就能拿到连接，撞上 ``no such table``（测试表现为
    ``no such table: shishen_map``，产品路径同样会中招）。

    并发安全性（不死锁）：
    - ``_LOCK`` 只在本函数获取，持有期间只做本地文件/SQLite 建表，不申请其它锁，
      因而不存在「持锁等别人、别人又要这把锁」的环；
    - 同线程递归（``_ensure_breaker_history_table`` → ``get_connection`` →
      再次进入本函数）由 ``_INIT_OWNER`` 识别后直接放行，不会二次抢锁；
    - 其它线程在 ``_LOCK`` 上等待初始化完成，随后命中 ``_INITIALIZED`` 快路径返回，
      即「等完成」而不是「拿到半成品」。
    """
    global _INITIALIZED, _INIT_OWNER
    if _INITIALIZED:
        return
    me = threading.get_ident()
    if _INIT_OWNER == me:  # 同线程递归：初始化尚未结束，直接放行
        return
    with _LOCK:
        if _INITIALIZED:  # 等锁期间已被别的线程完成
            return
        _INIT_OWNER = me
        try:
            db_path = get_db_path()
            if not os.path.exists(db_path):
                _build_database(db_path, get_schema_path())
            _ensure_breaker_history_table()
            _ensure_pan_records_input_json()
            # 建库/迁移全部成功后才置位：其它线程此时看到的库一定是可用的
            _INITIALIZED = True
        finally:
            _INIT_OWNER = None


def _dict_factory(cursor, row):
    """将 SQLite 行转为 dict——兼容 dict.get(key, default) 调用,
    行为对齐迁移前的 MySQL DictCursor（字典式行），避免 'sqlite3.Row' object
    has no attribute 'get' 这类错误。"""
    return dict(zip((col[0] for col in cursor.description), row))


def log_circuit_breaker_event(state: str, failure_count: int = 0, open_count: int = 0):
    """记录熔断器状态变化到数据库历史表"""
    import time
    con = get_connection()
    try:
        con.execute(
            'INSERT INTO circuit_breaker_history (ts, state, failure_count, open_count) VALUES (?, ?, ?, ?)',
            (time.strftime('%Y-%m-%d %H:%M:%S'), state, failure_count, open_count)
        )
        con.commit()
    finally:
        con.close()

def get_circuit_breaker_history(limit: int = 48):
    """获取最近熔断历史"""
    con = get_connection()
    try:
        rows = con.execute(
            'SELECT ts, state, failure_count, open_count FROM circuit_breaker_history ORDER BY id DESC LIMIT ?',
            (limit,)
        ).fetchall()
        history = list(reversed(rows))
        return history
    finally:
        con.close()

def get_connection() -> sqlite3.Connection:
    """获取一个 SQLite 连接（每次调用返回新连接，调用方负责 close）。

    - row_factory=dict 工厂：支持按列名访问以及 .get(key, default) 取值，
      与迁移前 MySQL 字典式行行为一致。
    - check_same_thread=False：允许在 Qt 工作线程中使用。
    - journal_mode=WAL 是数据库级持久属性，仅在 _build_database 建库时设置一次；
      每个连接重复 PRAGMA journal_mode 会多一次锁尝试且失败被静默吞掉（P2-07）。
      连接级只设置 busy_timeout / synchronous。
    """
    ensure_initialized()
    con = sqlite3.connect(get_db_path(), timeout=30, check_same_thread=False,
                          factory=_Connection)
    con.row_factory = _dict_factory
    try:
        # busy_timeout 与 connect(timeout=30) 等价，显式声明避免依赖默认值；
        # synchronous=NORMAL 是 WAL 模式下的推荐档位（连接级属性，必须每连接设置）。
        con.execute('PRAGMA busy_timeout=30000')
        con.execute('PRAGMA synchronous=NORMAL')
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
        """退出 with 块时先提交/回滚（父类处理），再无条件 close，避免连接泄漏。

        清理逻辑置于 finally，因此即便上下文内抛异常也照常关闭连接；
        本方法不吞异常，异常会继续向上传播。
        """
        try:
            super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            self.close()
