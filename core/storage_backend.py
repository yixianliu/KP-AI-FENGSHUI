"""
统一存储后端抽象层
====================
负责「非命理类」数据的持久化：界面配置(ui_settings)、操作记录(operation_logs)、
系统日志(system_logs)。命理排盘与 AI 解读结果(pan_records / analysis_reports)
维持既有 MySQL 存储，不纳入本抽象层。

支持四种后端，运行时可热切换：
  - mysql : 复用 config.ini [database] 段，自建 pymysql 连接
  - redis : 复用 RedisManager 单例
  - csv   : CSV 文件（每类一个 csv）
  - text  : 文本文件（每记录一行 / 单文件追加）

设计要点
--------
- StorageBackend 为抽象基类，四种后端统一接口。
- StorageManager 为单例工厂，管理「当前激活后端」，提供热切换与参数校验。
- 后端切换只影响后续写入；正在运行的 AI worker 使用 Redis 队列 + DatabaseManager 直接写库，
  不经过本层，因此切换不会中断进行中的任务。
"""
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging
import os
import sys
import configparser
import threading

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

VALID_BACKENDS = ('mysql', 'redis', 'csv', 'text')


# ==================== 异常 ====================
class StorageBackendError(Exception):
    """存储后端异常基类"""
    pass


class StorageConfigError(StorageBackendError):
    """配置/参数错误"""
    pass


class StorageConnectionError(StorageBackendError):
    """后端连接失败"""
    pass


# ==================== 抽象基类 ====================
class StorageBackend(ABC):
    """统一存储后端抽象基类（非命理类数据）"""

    #: 后端类型标识，子类覆盖
    backend_type: str = 'abstract'

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params = params or {}
        self._lock = threading.Lock()

    @abstractmethod
    def test_connection(self) -> bool:
        """测试后端可用性，供切换前校验。"""
        ...

    @abstractmethod
    def save_ui_settings(self, settings: Dict[str, Any]) -> bool:
        """保存界面配置（窗口尺寸/分栏比例/主题/最近板块等）。"""
        ...

    @abstractmethod
    def load_ui_settings(self) -> Dict[str, Any]:
        """读取界面配置，未配置返回空 dict。"""
        ...

    @abstractmethod
    def save_operation_log(self, op_type: str, op_object: str = '',
                               user_id: Any = None, session: str = None,
                               detail: str = None) -> bool:
        """记录一条操作记录。"""
        ...

    @abstractmethod
    def save_system_log(self, level: str, message: str,
                            module: str = None, data: Any = None) -> bool:
        """记录一条系统日志。"""
        ...

    @abstractmethod
    def load_operation_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """读取最近操作记录（供历史/审计）。"""
        ...

    def close(self):
        """释放后端资源（可选覆盖）。"""
        pass


# ==================== MySQL 后端 ====================
class MysqlStorageBackend(StorageBackend):
    """MySQL 后端：复用 config.ini [database] 段自建连接，管理三张新表。"""
    backend_type = 'mysql'

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.db_config = self._load_db_config()
        self._conn = None
        self._ensure_tables()

    def _load_db_config(self) -> Dict[str, Any]:
        parser = configparser.ConfigParser()
        cfg = self.params or {}
        # 优先用传入参数，其次 config.ini [database]
        host = cfg.get('host') or self._ini_get('database', 'host', '127.0.0.1')
        port = int(cfg.get('port') or self._ini_get('database', 'port', '3306'))
        user = cfg.get('user') or self._ini_get('database', 'user', 'root')
        password = cfg.get('password', self._ini_get('database', 'password', ''))
        database = cfg.get('database') or self._ini_get('database', 'database', 'ai_fengshui')
        charset = cfg.get('charset') or self._ini_get('database', 'charset', 'utf8mb4')
        return {'host': host, 'port': port, 'user': user,
                'password': password, 'database': database, 'charset': charset}

    @staticmethod
    def _ini_get(section, key, default):
        p = project_root / 'config.ini'
        if not p.exists():
            return default
        parser = configparser.ConfigParser()
        parser.read(p, encoding='utf-8')
        if section in parser and key in parser[section]:
            return parser[section][key]
        return default

    def _connect(self, include_database: bool = True):
        import pymysql
        args = dict(host=self.db_config['host'], port=self.db_config['port'],
                    user=self.db_config['user'], password=self.db_config['password'],
                    charset=self.db_config['charset'], autocommit=True,
                    cursorclass=pymysql.cursors.DictCursor)
        if include_database:
            args['database'] = self.db_config['database']
        return pymysql.connect(**args)

    def _ensure_tables(self):
        try:
            with self._connect(include_database=False) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"CREATE DATABASE IF NOT EXISTS `{self.db_config['database']}` "
                        f"CHARACTER SET {self.db_config['charset']}"
                    )
            with self._connect() as conn:
                with conn.cursor() as cur:
                    self._create_ui_settings(cur)
                    self._create_operation_logs(cur)
                    self._create_system_logs(cur)
                conn.commit()
        except Exception as e:
            logger.warning(f"[存储-MySQL] 建表失败（可能无数据库）：{e}")

    def _create_ui_settings(self, cur):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ui_settings (
                id INT PRIMARY KEY AUTO_INCREMENT,
                setting_key VARCHAR(64) NOT NULL,
                setting_value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_key (setting_key)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='界面配置'
        """)

    def _create_operation_logs(self, cur):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS operation_logs (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                user_id VARCHAR(64),
                op_type VARCHAR(32) NOT NULL,
                op_object VARCHAR(128),
                detail TEXT,
                session VARCHAR(64),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_op_type (op_type),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作记录'
        """)

    def _create_system_logs(self, cur):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                log_level VARCHAR(16) NOT NULL,
                module VARCHAR(64),
                log_message TEXT,
                log_data JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_level (log_level),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统日志'
        """)

    def test_connection(self) -> bool:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"[存储-MySQL] 连接测试失败: {e}")
            return False

    def save_ui_settings(self, settings: Dict[str, Any]) -> bool:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    for k, v in settings.items():
                        val = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
                        cur.execute(
                            "INSERT INTO ui_settings (setting_key, setting_value) VALUES (%s, %s) "
                            "ON DUPLICATE KEY UPDATE setting_value = %s, updated_at = CURRENT_TIMESTAMP",
                            (k, val, val)
                        )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"[存储-MySQL] 保存界面配置失败: {e}")
            return False

    def load_ui_settings(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT setting_key, setting_value FROM ui_settings")
                    for row in cur.fetchall():
                        k, v = row['setting_key'], row['setting_value']
                        try:
                            out[k] = json.loads(v)
                        except (json.JSONDecodeError, TypeError):
                            out[k] = v
        except Exception as e:
            logger.warning(f"[存储-MySQL] 读取界面配置失败: {e}")
        return out

    def save_operation_log(self, op_type: str, op_object: str = '',
                            user_id: Any = None, session: str = None,
                            detail: str = None) -> bool:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO operation_logs (user_id, op_type, op_object, detail, session) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (str(user_id) if user_id is not None else None,
                         op_type, op_object, detail, session)
                    )
                conn.commit()
            return True
        except Exception as e:
            logger.warning(f"[存储-MySQL] 操作记录失败: {e}")
            return False

    def save_system_log(self, level: str, message: str,
                        module: str = None, data: Any = None) -> bool:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO system_logs (log_level, module, log_message, log_data) "
                        "VALUES (%s, %s, %s, %s)",
                        (level, module, message,
                         json.dumps(data, ensure_ascii=False) if data is not None else None)
                    )
                conn.commit()
            return True
        except Exception as e:
            logger.warning(f"[存储-MySQL] 系统日志失败: {e}")
            return False

    def load_operation_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM operation_logs ORDER BY created_at DESC LIMIT %s",
                        (limit,)
                    )
                    return list(cur.fetchall())
        except Exception as e:
            logger.warning(f"[存储-MySQL] 读取操作记录失败: {e}")
            return []


# ==================== Redis 后端 ====================
class RedisStorageBackend(StorageBackend):
    """Redis 后端：复用 RedisManager 单例。"""
    backend_type = 'redis'

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self._mgr = None
        try:
            from core.redis_manager import get_redis_manager
            self._mgr = get_redis_manager()
        except Exception as e:
            logger.warning(f"[存储-Redis] 管理器初始化失败: {e}")

    @staticmethod
    def _ini_get(section, key, default):
        p = project_root / 'config.ini'
        if not p.exists():
            return default
        parser = configparser.ConfigParser()
        parser.read(p, encoding='utf-8')
        if section in parser and key in parser[section]:
            return parser[section][key]
        return default

    def _available(self) -> bool:
        return self._mgr is not None and self._mgr.is_connected()

    def test_connection(self) -> bool:
        if self._mgr is None:
            return False
        return self._mgr.test_connection()

    def _key(self, name: str) -> str:
        prefix = (self.params or {}).get('key_prefix') or 'kp_fengshui:storage'
        return f"{prefix}:{name}"

    def save_ui_settings(self, settings: Dict[str, Any]) -> bool:
        if not self._available():
            return False
        try:
            self._mgr.set(self._key('ui_settings'), settings)
            return True
        except Exception as e:
            logger.error(f"[存储-Redis] 保存界面配置失败: {e}")
            return False

    def load_ui_settings(self) -> Dict[str, Any]:
        if not self._available():
            return {}
        try:
            v = self._mgr.get(self._key('ui_settings'))
            return v if isinstance(v, dict) else {}
        except Exception as e:
            logger.warning(f"[存储-Redis] 读取界面配置失败: {e}")
            return {}

    def save_operation_log(self, op_type: str, op_object: str = '',
                            user_id: Any = None, session: str = None,
                            detail: str = None) -> bool:
        if not self._available():
            return False
        try:
            rec = {'user_id': str(user_id) if user_id is not None else None,
                    'op_type': op_type, 'op_object': op_object,
                    'detail': detail, 'session': session,
                    'created_at': datetime.now().isoformat(timespec='seconds')}
            self._mgr.get_client().rpush(self._key('operation_logs'), json.dumps(rec, ensure_ascii=False))
            return True
        except Exception as e:
            logger.warning(f"[存储-Redis] 操作记录失败: {e}")
            return False

    def save_system_log(self, level: str, message: str,
                        module: str = None, data: Any = None) -> bool:
        if not self._available():
            return False
        try:
            rec = {'level': level, 'module': module, 'message': message,
                    'data': data, 'created_at': datetime.now().isoformat(timespec='seconds')}
            self._mgr.get_client().rpush(self._key('system_logs'), json.dumps(rec, ensure_ascii=False))
            return True
        except Exception as e:
            logger.warning(f"[存储-Redis] 系统日志失败: {e}")
            return False

    def load_operation_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self._available():
            return []
        try:
            raw = self._mgr.get_client().lrange(self._key('operation_logs'), -limit, -1)
            return [json.loads(r) for r in raw if r]
        except Exception as e:
            logger.warning(f"[存储-Redis] 读取操作记录失败: {e}")
            return []


# ==================== CSV 文件后端 ====================
class CsvFileStorageBackend(StorageBackend):
    """CSV 文件后端：每类一个 csv 文件。"""
    backend_type = 'csv'

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.dir = Path((self.params or {}).get('dir') or 'storage/csv')
        self.encoding = (self.params or {}).get('encoding') or 'utf-8'
        self._ensure_dir()

    def _ensure_dir(self):
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"[存储-CSV] 目录创建失败: {e}")

    def _path(self, name: str) -> Path:
        return self.dir / f"{name}.csv"

    def test_connection(self) -> bool:
        return os.access(str(self.dir), os.W_OK) or self._ensure_dir() is None

    def save_ui_settings(self, settings: Dict[str, Any]) -> bool:
        import csv
        try:
            fp = self._path('ui_settings')
            with open(fp, 'w', encoding=self.encoding, newline='') as f:
                w = csv.writer(f)
                w.writerow(['setting_key', 'setting_value'])
                for k, v in settings.items():
                    val = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
                    w.writerow([k, val])
            return True
        except Exception as e:
            logger.error(f"[存储-CSV] 保存界面配置失败: {e}")
            return False

    def load_ui_settings(self) -> Dict[str, Any]:
        import csv
        out: Dict[str, Any] = {}
        fp = self._path('ui_settings')
        if not fp.exists():
            return out
        try:
            with open(fp, 'r', encoding=self.encoding, newline='') as f:
                for row in csv.reader(f):
                    if len(row) >= 2 and row[0] != 'setting_key':
                        k, v = row[0], row[1]
                        try:
                            out[k] = json.loads(v)
                        except (json.JSONDecodeError, TypeError):
                            out[k] = v
        except Exception as e:
            logger.warning(f"[存储-CSV] 读取界面配置失败: {e}")
        return out

    def save_operation_log(self, op_type: str, op_object: str = '',
                            user_id: Any = None, session: str = None,
                            detail: str = None) -> bool:
        import csv
        try:
            fp = self._path('operation_logs')
            write_header = not fp.exists()
            with open(fp, 'a', encoding=self.encoding, newline='') as f:
                w = csv.writer(f)
                if write_header:
                    w.writerow(['created_at', 'user_id', 'op_type', 'op_object', 'detail', 'session'])
                w.writerow([datetime.now().isoformat(timespec='seconds'),
                            str(user_id) if user_id is not None else '',
                            op_type, op_object, detail or '', session or ''])
            return True
        except Exception as e:
            logger.error(f"[存储-CSV] 操作记录失败: {e}")
            return False

    def save_system_log(self, level: str, message: str,
                        module: str = None, data: Any = None) -> bool:
        import csv
        try:
            fp = self._path('system_logs')
            write_header = not fp.exists()
            with open(fp, 'a', encoding=self.encoding, newline='') as f:
                w = csv.writer(f)
                if write_header:
                    w.writerow(['created_at', 'level', 'module', 'message', 'data'])
                w.writerow([datetime.now().isoformat(timespec='seconds'),
                            level, module or '', message,
                            json.dumps(data, ensure_ascii=False) if data is not None else ''])
            return True
        except Exception as e:
            logger.error(f"[存储-CSV] 系统日志失败: {e}")
            return False

    def load_operation_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        import csv
        fp = self._path('operation_logs')
        if not fp.exists():
            return []
        try:
            rows = []
            with open(fp, 'r', encoding=self.encoding, newline='') as f:
                for i, row in enumerate(csv.reader(f)):
                    if i == 0:
                        continue
                    rows.append({'created_at': row[0] if len(row) > 0 else '',
                                 'op_type': row[2] if len(row) > 2 else '',
                                 'op_object': row[3] if len(row) > 3 else ''})
            return rows[-limit:]
        except Exception as e:
            logger.warning(f"[存储-CSV] 读取操作记录失败: {e}")
            return []


# ==================== 文本文件后端 ====================
class TextFileStorageBackend(StorageBackend):
    """文本文件后端：每记录一行 / 单文件追加。"""
    backend_type = 'text'

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.dir = Path((self.params or {}).get('dir') or 'storage/text')
        self.ext = (self.params or {}).get('ext') or '.txt'
        self.mode = (self.params or {}).get('mode') or 'append'  # append | per_record
        self.encoding = (self.params or {}).get('encoding') or 'utf-8'
        self._ensure_dir()

    def _ensure_dir(self):
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"[存储-Text] 目录创建失败: {e}")

    def _path(self, name: str) -> Path:
        return self.dir / f"{name}{self.ext}"

    def test_connection(self) -> bool:
        return os.access(str(self.dir), os.W_OK) or self._ensure_dir() is None

    def save_ui_settings(self, settings: Dict[str, Any]) -> bool:
        try:
            fp = self._path('ui_settings')
            with open(fp, 'w', encoding=self.encoding) as f:
                if self.ext in ('.json', '.md'):
                    json.dump(settings, f, ensure_ascii=False, indent=2)
                else:
                    for k, v in settings.items():
                        f.write(f"{k} = {json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v}\n")
            return True
        except Exception as e:
            logger.error(f"[存储-Text] 保存界面配置失败: {e}")
            return False

    def load_ui_settings(self) -> Dict[str, Any]:
        import re
        out: Dict[str, Any] = {}
        fp = self._path('ui_settings')
        if not fp.exists():
            return out
        try:
            with open(fp, 'r', encoding=self.encoding) as f:
                content = f.read()
            if self.ext in ('.json', '.md'):
                return json.loads(content)
            for line in content.splitlines():
                m = re.match(r'^(\S+)\s*=\s*(.*)$', line)
                if m:
                    k, v = m.group(1), m.group(2).strip()
                    try:
                        out[k] = json.loads(v)
                    except (json.JSONDecodeError, TypeError):
                        out[k] = v
        except Exception as e:
            logger.warning(f"[存储-Text] 读取界面配置失败: {e}")
        return out

    def save_operation_log(self, op_type: str, op_object: str = '',
                            user_id: Any = None, session: str = None,
                            detail: str = None) -> bool:
        try:
            fp = self._path('operation_logs')
            with open(fp, 'a', encoding=self.encoding) as f:
                ts = datetime.now().isoformat(timespec='seconds')
                f.write(f"[{ts}] user={user_id} op={op_type} object={op_object}")
                if detail:
                    f.write(f" detail={detail}")
                if session:
                    f.write(f" session={session}")
                f.write("\n")
            return True
        except Exception as e:
            logger.error(f"[存储-Text] 操作记录失败: {e}")
            return False

    def save_system_log(self, level: str, message: str,
                        module: str = None, data: Any = None) -> bool:
        try:
            fp = self._path('system_logs')
            with open(fp, 'a', encoding=self.encoding) as f:
                ts = datetime.now().isoformat(timespec='seconds')
                f.write(f"[{ts}][{level}][{module or 'app'}] {message}")
                if data is not None:
                    f.write(f" {json.dumps(data, ensure_ascii=False)}")
                f.write("\n")
            return True
        except Exception as e:
            logger.error(f"[存储-Text] 系统日志失败: {e}")
            return False

    def load_operation_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        fp = self._path('operation_logs')
        if not fp.exists():
            return []
        try:
            with open(fp, 'r', encoding=self.encoding) as f:
                lines = f.read().splitlines()
            return [{'raw': ln} for ln in lines[-limit:]]
        except Exception as e:
            logger.warning(f"[存储-Text] 读取操作记录失败: {e}")
            return []


# ==================== 后端工厂 ====================
_BACKEND_CLASSES = {
    'mysql': MysqlStorageBackend,
    'redis': RedisStorageBackend,
    'csv': CsvFileStorageBackend,
    'text': TextFileStorageBackend,
}


def create_backend(backend_type: str, params: Optional[Dict[str, Any]] = None) -> StorageBackend:
    """按类型创建后端实例（不校验连接，校验请用 test_connection）。"""
    if backend_type not in VALID_BACKENDS:
        raise StorageConfigError(f"不支持的存储后端: {backend_type}")
    cls = _BACKEND_CLASSES[backend_type]
    return cls(params or {})


def backend_default_params(backend_type: str) -> Dict[str, Any]:
    """返回某后端的默认参数（供设置界面预填）。"""
    if backend_type == 'mysql':
        return {'host': '127.0.0.1', 'port': 3306, 'user': 'root',
                'password': '', 'database': 'ai_fengshui', 'charset': 'utf8mb4'}
    if backend_type == 'redis':
        return {'host': '127.0.0.1', 'port': 6379, 'db': 0,
                'password': '', 'key_prefix': 'kp_fengshui:storage'}
    if backend_type == 'csv':
        return {'dir': 'storage/csv', 'encoding': 'utf-8'}
    if backend_type == 'text':
        return {'dir': 'storage/text', 'ext': '.txt', 'mode': 'append', 'encoding': 'utf-8'}
    return {}


# ==================== 存储管理器（单例 + 热切换） ====================
class StorageManager:
    """管理当前激活存储后端，支持运行时热切换与参数校验。"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else (project_root / 'config.ini')
        self._current: Optional[StorageBackend] = None
        self._current_type: Optional[str] = None
        self._lock = threading.Lock()
        self._init_from_config()

    def _read_config(self) -> Dict[str, Any]:
        """读取 config.ini [storage] 段决定初始后端。"""
        out = {'backend': 'mysql'}
        if self.config_path.exists():
            parser = configparser.ConfigParser()
            parser.read(self.config_path, encoding='utf-8')
            if 'storage' in parser:
                sec = parser['storage']
                out['backend'] = sec.get('backend', 'mysql')
        if out['backend'] not in VALID_BACKENDS:
            out['backend'] = 'mysql'
        return out

    def _init_from_config(self):
        cfg = self._read_config()
        btype = cfg['backend']
        try:
            backend = create_backend(btype)
            # 连接不可用时不阻断启动，仅告警
            if not backend.test_connection():
                logger.warning(f"[存储管理] 初始后端「{btype}」连接不可用，将降级运行（写入可能失败）")
            self._current = backend
            self._current_type = btype
        except Exception as e:
            logger.error(f"[存储管理] 初始后端「{btype}」创建失败: {e}")
            # 兜底：内存 csv 后端
            self._current = CsvFileStorageBackend({'dir': 'storage/csv'})
            self._current_type = 'csv'

    @property
    def backend_type(self) -> Optional[str]:
        return self._current_type

    def get_backend(self) -> StorageBackend:
        return self._current

    def test_backend(self, backend_type: str, params: Dict[str, Any]) -> bool:
        """校验某后端（创建并探活），不切换。"""
        try:
            backend = create_backend(backend_type, params)
            return backend.test_connection()
        except Exception as e:
            logger.error(f"[存储管理] 后端校验失败: {e}")
            return False

    def switch_backend(self, backend_type: str, params: Optional[Dict[str, Any]] = None,
                         write_config: bool = True) -> bool:
        """热切换到新后端。成功返回 True；失败回滚到旧后端并抛异常。"""
        if backend_type not in VALID_BACKENDS:
            raise StorageConfigError(f"不支持的存储后端: {backend_type}")
        new_backend = create_backend(backend_type, params)
        if not new_backend.test_connection():
            raise StorageConnectionError(f"后端「{backend_type}」连接校验未通过")
        with self._lock:
            old = self._current
            self._current = new_backend
            self._current_type = backend_type
            if old is not None and old is not new_backend:
                try:
                    old.close()
                except Exception:
                    pass
        if write_config:
            self._write_config(backend_type, params)
        logger.info(f"[存储管理] 已热切换存储后端至「{backend_type}」")
        return True

    def _write_config(self, backend_type: str, params: Optional[Dict[str, Any]]):
        """把后端类型与参数写回 config.ini。"""
        try:
            parser = configparser.ConfigParser()
            if self.config_path.exists():
                parser.read(self.config_path, encoding='utf-8')
            if 'storage' not in parser:
                parser.add_section('storage')
            parser['storage']['backend'] = backend_type
            # 把后端专属参数也写回对应段，便于其他模块复用
            target = {'mysql': 'database', 'redis': 'redis', 'csv': 'csv', 'text': 'text'}.get(backend_type)
            if target and params:
                if target not in parser:
                    parser.add_section(target)
                for k, v in params.items():
                    if k in ('host', 'port', 'user', 'password', 'database', 'charset',
                              'db', 'key_prefix', 'dir', 'encoding', 'ext', 'mode'):
                        parser[target][k] = str(v)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                parser.write(f)
        except Exception as e:
            logger.warning(f"[存储管理] 写回 config.ini 失败: {e}")

    # ---- 委托方法（统一入口）----
    def save_ui_settings(self, settings: Dict[str, Any]) -> bool:
        return self._current.save_ui_settings(settings)

    def load_ui_settings(self) -> Dict[str, Any]:
        return self._current.load_ui_settings()

    def save_operation_log(self, *args, **kwargs) -> bool:
        return self._current.save_operation_log(*args, **kwargs)

    def save_system_log(self, *args, **kwargs) -> bool:
        return self._current.save_system_log(*args, **kwargs)

    def load_operation_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._current.load_operation_logs(limit)


_manager_instance = None
_manager_lock = threading.Lock()


def get_storage_manager(config_path: Optional[str] = None) -> StorageManager:
    """获取 StorageManager 单例。"""
    global _manager_instance
    if _manager_instance is None:
        with _manager_lock:
            if _manager_instance is None:
                _manager_instance = StorageManager(config_path)
    return _manager_instance
