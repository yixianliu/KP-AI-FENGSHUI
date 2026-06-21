"""
数据库管理模块 - 封装所有数据库操作
支持MySQL配置读取、用户管理、排盘记录管理
"""
import configparser
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

import pymysql


class DatabaseManager:
    """数据库管理器 - 封装所有数据库操作"""

    def __init__(self, config_path: str = None):
        """
        初始化数据库管理器

        Args:
            config_path: 配置文件路径，默认使用项目根目录的config.ini
        """
        if config_path is None:
            project_root = Path(__file__).resolve().parent.parent
            config_path = project_root / 'config.ini'
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self.db_config = self._load_db_config()
        self._init_database()

    def _load_db_config(self) -> Dict[str, str]:
        """从config.ini读取MySQL配置"""
        parser = configparser.ConfigParser()
        if not self.config_path.exists():
            raise FileNotFoundError(f"未找到数据库配置文件: {self.config_path}")

        parser.read(self.config_path, encoding='utf-8')
        if 'database' not in parser:
            raise ValueError("config.ini 缺少 [database] 配置段")

        section = parser['database']
        return {
            'host': section.get('host', '127.0.0.1'),
            'user': section.get('user', 'root'),
            'password': section.get('password', ''),
            'database': section.get('database', 'ai_fengshui'),
            'charset': section.get('charset', 'utf8mb4')
        }

    def _connect(self, include_database: bool = True, autocommit: bool = False):
        """建立数据库连接"""
        connect_args = {
            'host': self.db_config['host'],
            'user': self.db_config['user'],
            'password': self.db_config['password'],
            'charset': self.db_config['charset'],
            'autocommit': autocommit
        }
        if include_database:
            connect_args['database'] = self.db_config['database']
        return pymysql.connect(**connect_args)

    def _init_database(self):
        """初始化数据库和表结构"""
        # 创建数据库（如果不存在）
        with self._connect(include_database=False, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.db_config['database']}` "
                    f"CHARACTER SET {self.db_config['charset']}"
                )

        # 创建用户表
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        username VARCHAR(50) NOT NULL UNIQUE,
                        password_hash VARCHAR(64) NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_username (username)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)

            # 创建排盘记录表
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pan_records (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        user_id INT NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        gender VARCHAR(10),
                        birth_date VARCHAR(20),
                        birth_time VARCHAR(20),
                        city VARCHAR(100),
                        pan_type VARCHAR(50),
                        result_json LONGTEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_user_id (user_id),
                        INDEX idx_created_at (created_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
            connection.commit()

    # ==================== 用户管理 ====================

    def create_user(self, username: str, password_hash: str) -> Optional[int]:
        """
        创建新用户

        Args:
            username: 用户名
            password_hash: 密码哈希值

        Returns:
            新用户ID，失败返回None
        """
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                        (username, password_hash)
                    )
                    user_id = cursor.lastrowid
                connection.commit()
                return user_id
        except pymysql.IntegrityError:
            # 用户名已存在
            return None
        except Exception as e:
            print(f"创建用户失败: {e}")
            return None

    def verify_user(self, username: str, password_hash: str) -> Optional[Dict[str, Any]]:
        """
        验证用户登录

        Args:
            username: 用户名
            password_hash: 密码哈希值

        Returns:
            用户信息字典，验证失败返回None
        """
        try:
            with self._connect() as connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT id, username, created_at FROM users WHERE username = %s AND password_hash = %s",
                        (username, password_hash)
                    )
                    return cursor.fetchone()
        except Exception as e:
            print(f"验证用户失败: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名查询用户

        Args:
            username: 用户名

        Returns:
            用户信息字典，不存在返回None
        """
        try:
            with self._connect() as connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT id, username, created_at FROM users WHERE username = %s",
                        (username,)
                    )
                    return cursor.fetchone()
        except Exception as e:
            print(f"查询用户失败: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据用户ID查询用户

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典，不存在返回None
        """
        try:
            with self._connect() as connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT id, username, created_at FROM users WHERE id = %s",
                        (user_id,)
                    )
                    return cursor.fetchone()
        except Exception as e:
            print(f"查询用户失败: {e}")
            return None

    # ==================== 排盘记录管理 ====================

    def save_pan_record(self, user_id: int, name: str, gender: str,
                        birth_date: str, birth_time: str, city: str,
                        pan_type: str, result: Dict[str, Any]) -> Optional[int]:
        """
        保存排盘记录

        Args:
            user_id: 用户ID
            name: 姓名
            gender: 性别
            birth_date: 出生日期
            birth_time: 出生时间
            city: 城市
            pan_type: 排盘类型
            result: 排盘结果字典

        Returns:
            记录ID，失败返回None
        """
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO pan_records
                        (user_id, name, gender, birth_date, birth_time, city, pan_type, result_json)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            user_id, name, gender, birth_date, birth_time,
                            city, pan_type, json.dumps(result, ensure_ascii=False)
                        )
                    )
                    record_id = cursor.lastrowid
                connection.commit()
                return record_id
        except Exception as e:
            print(f"保存排盘记录失败: {e}")
            return None

    def get_user_records(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取用户的排盘记录列表

        Args:
            user_id: 用户ID
            limit: 返回记录数量上限

        Returns:
            排盘记录列表
        """
        try:
            with self._connect() as connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        """
                        SELECT id, name, gender, birth_date, birth_time,
                               city, pan_type, result_json, created_at
                        FROM pan_records
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (user_id, limit)
                    )
                    records = cursor.fetchall()
                    # 解析JSON字段
                    for record in records:
                        try:
                            record['result'] = json.loads(record['result_json'])
                        except (json.JSONDecodeError, KeyError):
                            record['result'] = {}
                        del record['result_json']
                    return records
        except Exception as e:
            print(f"获取排盘记录失败: {e}")
            return []

    def get_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单条排盘记录

        Args:
            record_id: 记录ID

        Returns:
            排盘记录字典，不存在返回None
        """
        try:
            with self._connect() as connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        """
                        SELECT id, user_id, name, gender, birth_date, birth_time,
                               city, pan_type, result_json, created_at
                        FROM pan_records
                        WHERE id = %s
                        """,
                        (record_id,)
                    )
                    record = cursor.fetchone()
                    if record:
                        try:
                            record['result'] = json.loads(record['result_json'])
                        except (json.JSONDecodeError, KeyError):
                            record['result'] = {}
                        del record['result_json']
                    return record
        except Exception as e:
            print(f"获取排盘记录失败: {e}")
            return None

    def delete_record(self, record_id: int, user_id: int) -> bool:
        """
        删除排盘记录

        Args:
            record_id: 记录ID
            user_id: 用户ID（用于权限验证）

        Returns:
            是否删除成功
        """
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM pan_records WHERE id = %s AND user_id = %s",
                        (record_id, user_id)
                    )
                    affected = cursor.rowcount
                connection.commit()
                return affected > 0
        except Exception as e:
            print(f"删除排盘记录失败: {e}")
            return False

    def init_database(self):
        """
        重新初始化数据库（公开接口）
        用于外部调用确保数据库和表已创建
        """
        self._init_database()
