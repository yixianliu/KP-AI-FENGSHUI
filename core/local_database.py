import configparser
import json
from datetime import datetime
from pathlib import Path

import pymysql


class LocalAnalysisDatabase:
    def __init__(self, db_path=None):
        project_root = Path(__file__).resolve().parent.parent
        self.project_root = project_root
        self.config_path = project_root / 'config.ini'
        self.db_config = self._load_db_config()
        self.db_path = db_path or self._build_connection_label()
        self._initialize_database()

    def _load_db_config(self):
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

    def _build_connection_label(self):
        return (
            f"mysql://{self.db_config['host']}/"
            f"{self.db_config['database']}"
        )

    def _connect(self, include_database=True, autocommit=False):
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

    def _initialize_database(self):
        with self._connect(include_database=False, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.db_config['database']}` "
                    f"CHARACTER SET {self.db_config['charset']}"
                )

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_records (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        name VARCHAR(100) NOT NULL,
                        gender VARCHAR(20),
                        birth_date VARCHAR(20),
                        birth_time VARCHAR(20),
                        city VARCHAR(100),
                        professional_chart_json LONGTEXT NOT NULL,
                        ai_analysis_json LONGTEXT NOT NULL,
                        input_json LONGTEXT NOT NULL,
                        created_at DATETIME NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
            connection.commit()

    def save_analysis(self, input_data, professional_chart, ai_analysis):
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        birth_date = (
            f"{input_data.get('year', '')}-"
            f"{input_data.get('month', ''):02d}-"
            f"{input_data.get('day', ''):02d}"
        )
        birth_time = (
            f"{input_data.get('hour', 0):02d}:"
            f"{input_data.get('minute', 0):02d}"
        )

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO analysis_records (
                        name,
                        gender,
                        birth_date,
                        birth_time,
                        city,
                        professional_chart_json,
                        ai_analysis_json,
                        input_json,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        input_data.get('name', '未命名'),
                        input_data.get('gender', ''),
                        birth_date,
                        birth_time,
                        input_data.get('city', ''),
                        json.dumps(professional_chart, ensure_ascii=False),
                        json.dumps(ai_analysis, ensure_ascii=False),
                        json.dumps(input_data, ensure_ascii=False),
                        created_at,
                    )
                )
                record_id = cursor.lastrowid
            connection.commit()

        return {
            'record_id': record_id,
            'created_at': created_at,
            'db_path': str(self.db_path)
        }
