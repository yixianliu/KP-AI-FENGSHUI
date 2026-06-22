"""
分析报告存储模块
负责从config.ini读取数据库配置，将AI分析报告存储到MySQL数据库
"""
import configparser
import json
import logging
import pymysql
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)


class AnalysisStorageError(Exception):
    """分析存储异常基类"""
    pass


class DatabaseConnectionError(AnalysisStorageError):
    """数据库连接异常"""
    pass


class DatabaseQueryError(AnalysisStorageError):
    """数据库查询异常"""
    pass


class AnalysisStorage:
    """
    分析报告存储器
    负责管理数据库连接，存储和查询AI分析报告
    """

    def __init__(self, config_path: str = None):
        """
        初始化分析存储器

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
        self._ensure_database()
        self._ensure_tables()
        logger.info(f"[分析存储] 初始化完成，数据库: {self.db_config['database']}")

    def _load_db_config(self) -> Dict[str, str]:
        """
        从config.ini读取MySQL数据库配置

        Returns:
            数据库配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置段缺失
        """
        parser = configparser.ConfigParser()
        if not self.config_path.exists():
            logger.error(f"[分析存储] 未找到数据库配置文件: {self.config_path}")
            raise FileNotFoundError(f"未找到数据库配置文件: {self.config_path}")

        parser.read(self.config_path, encoding='utf-8')
        if 'database' not in parser:
            logger.error("[分析存储] config.ini 缺少 [database] 配置段")
            raise ValueError("config.ini 缺少 [database] 配置段")

        section = parser['database']
        config = {
            'host': section.get('host', '127.0.0.1'),
            'port': section.getint('port', 3306),
            'user': section.get('user', 'root'),
            'password': section.get('password', ''),
            'database': section.get('database', 'ai_fengshui'),
            'charset': section.get('charset', 'utf8mb4')
        }

        logger.info(f"[分析存储] 数据库配置加载成功: host={config['host']}, "
                    f"database={config['database']}")
        return config

    def _get_connection(self, include_database: bool = True, autocommit: bool = False):
        """
        获取数据库连接

        Args:
            include_database: 是否包含数据库名
            autocommit: 是否自动提交

        Returns:
            pymysql连接对象

        Raises:
            DatabaseConnectionError: 连接失败
        """
        try:
            connect_args = {
                'host': self.db_config['host'],
                'port': self.db_config['port'],
                'user': self.db_config['user'],
                'password': self.db_config['password'],
                'charset': self.db_config['charset'],
                'autocommit': autocommit,
                'cursorclass': pymysql.cursors.DictCursor
            }
            if include_database:
                connect_args['database'] = self.db_config['database']
            return pymysql.connect(**connect_args)
        except pymysql.MySQLError as e:
            logger.error(f"[分析存储] 数据库连接失败: {e}")
            raise DatabaseConnectionError(f"数据库连接失败: {e}") from e

    def _ensure_database(self):
        """确保数据库存在"""
        try:
            with self._get_connection(include_database=False, autocommit=True) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"CREATE DATABASE IF NOT EXISTS `{self.db_config['database']}` "
                        f"CHARACTER SET {self.db_config['charset']}"
                    )
            logger.info(f"[分析存储] 数据库已就绪: {self.db_config['database']}")
        except DatabaseConnectionError:
            raise
        except Exception as e:
            logger.error(f"[分析存储] 创建数据库失败: {e}")
            raise DatabaseQueryError(f"创建数据库失败: {e}") from e

    def _ensure_tables(self):
        """确保所需数据表存在"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    self._create_analysis_reports_table(cursor)
                    self._create_analysis_logs_table(cursor)
                conn.commit()
            logger.info("[分析存储] 数据表已就绪")
        except DatabaseConnectionError:
            raise
        except Exception as e:
            logger.error(f"[分析存储] 创建数据表失败: {e}")
            raise DatabaseQueryError(f"创建数据表失败: {e}") from e

    def _create_analysis_reports_table(self, cursor):
        """创建分析报告表"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_reports (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '报告ID',
                report_type VARCHAR(50) NOT NULL COMMENT '报告类型：bazi/meihua',
                name VARCHAR(100) COMMENT '姓名/标识',
                gender VARCHAR(10) COMMENT '性别',
                birth_date VARCHAR(20) COMMENT '出生日期',
                birth_time VARCHAR(20) COMMENT '出生时间',
                city VARCHAR(100) COMMENT '城市',
                question TEXT COMMENT '所问之事（梅花易数）',
                input_data JSON COMMENT '原始输入数据（JSON格式）',
                chart_data JSON COMMENT '排盘数据（JSON格式）',
                ai_analysis JSON COMMENT 'AI分析结果（JSON格式）',
                status VARCHAR(20) DEFAULT 'completed' COMMENT '状态：pending/completed/failed',
                error_message TEXT COMMENT '错误信息',
                ai_model VARCHAR(100) COMMENT '使用的AI模型',
                token_usage INT DEFAULT 0 COMMENT '消耗token数',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_report_type (report_type),
                INDEX idx_status (status),
                INDEX idx_created_at (created_at),
                INDEX idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI分析报告表'
        """)

    def _create_analysis_logs_table(self, cursor):
        """创建分析日志表"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_logs (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
                report_id BIGINT COMMENT '关联报告ID',
                log_level VARCHAR(20) NOT NULL COMMENT '日志级别：INFO/WARNING/ERROR',
                log_message TEXT NOT NULL COMMENT '日志内容',
                log_data JSON COMMENT '附加数据（JSON格式）',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX idx_report_id (report_id),
                INDEX idx_log_level (log_level),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分析日志表'
        """)

    def save_analysis_report(
        self,
        report_type: str,
        input_data: Dict[str, Any],
        chart_data: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        status: str = 'completed',
        error_message: str = None,
        ai_model: str = None,
        token_usage: int = 0
    ) -> int:
        """
        保存分析报告

        Args:
            report_type: 报告类型 ('bazi' 或 'meihua')
            input_data: 原始输入数据
            chart_data: 排盘数据
            ai_analysis: AI分析结果
            status: 状态
            error_message: 错误信息
            ai_model: 使用的AI模型
            token_usage: 消耗的token数

        Returns:
            新创建的报告ID

        Raises:
            DatabaseQueryError: 保存失败
        """
        try:
            name = input_data.get('name', '')
            gender = input_data.get('gender', '')

            birth_date = ''
            birth_time = ''
            if 'year' in input_data and 'month' in input_data and 'day' in input_data:
                birth_date = (
                    f"{input_data.get('year', '')}-"
                    f"{input_data.get('month', 0):02d}-"
                    f"{input_data.get('day', 0):02d}"
                )
            if 'hour' in input_data and 'minute' in input_data:
                birth_time = (
                    f"{input_data.get('hour', 0):02d}:"
                    f"{input_data.get('minute', 0):02d}"
                )

            city = input_data.get('city', '')
            question = input_data.get('question', '')

            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO analysis_reports
                        (report_type, name, gender, birth_date, birth_time, city, question,
                         input_data, chart_data, ai_analysis, status, error_message,
                         ai_model, token_usage)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            report_type,
                            name,
                            gender,
                            birth_date,
                            birth_time,
                            city,
                            question,
                            json.dumps(input_data, ensure_ascii=False),
                            json.dumps(chart_data, ensure_ascii=False),
                            json.dumps(ai_analysis, ensure_ascii=False),
                            status,
                            error_message,
                            ai_model,
                            token_usage
                        )
                    )
                    report_id = cursor.lastrowid
                conn.commit()

            logger.info(f"[分析存储] 分析报告保存成功，ID: {report_id}, 类型: {report_type}")
            return report_id

        except DatabaseConnectionError:
            raise
        except Exception as e:
            logger.error(f"[分析存储] 保存分析报告失败: {e}")
            raise DatabaseQueryError(f"保存分析报告失败: {e}") from e

    def create_pending_report(
        self,
        report_type: str,
        input_data: Dict[str, Any]
    ) -> int:
        """
        创建待处理报告记录

        Args:
            report_type: 报告类型
            input_data: 输入数据

        Returns:
            报告ID
        """
        return self.save_analysis_report(
            report_type=report_type,
            input_data=input_data,
            chart_data={},
            ai_analysis={},
            status='pending'
        )

    def update_report_status(
        self,
        report_id: int,
        status: str,
        error_message: str = None
    ) -> bool:
        """
        更新报告状态

        Args:
            report_id: 报告ID
            status: 新状态
            error_message: 错误信息（可选）

        Returns:
            是否更新成功
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    if error_message:
                        cursor.execute(
                            "UPDATE analysis_reports SET status = %s, error_message = %s WHERE id = %s",
                            (status, error_message, report_id)
                        )
                    else:
                        cursor.execute(
                            "UPDATE analysis_reports SET status = %s WHERE id = %s",
                            (status, report_id)
                        )
                    affected = cursor.rowcount
                conn.commit()

            logger.info(f"[分析存储] 报告状态更新: ID={report_id}, status={status}")
            return affected > 0

        except Exception as e:
            logger.error(f"[分析存储] 更新报告状态失败: {e}")
            raise DatabaseQueryError(f"更新报告状态失败: {e}") from e

    def update_report_result(
        self,
        report_id: int,
        chart_data: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        ai_model: str = None,
        token_usage: int = 0
    ) -> bool:
        """
        更新报告结果数据

        Args:
            report_id: 报告ID
            chart_data: 排盘数据
            ai_analysis: AI分析结果
            ai_model: AI模型名称
            token_usage: token使用量

        Returns:
            是否更新成功
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE analysis_reports
                        SET chart_data = %s, ai_analysis = %s, status = 'completed',
                            ai_model = %s, token_usage = %s
                        WHERE id = %s
                        """,
                        (
                            json.dumps(chart_data, ensure_ascii=False),
                            json.dumps(ai_analysis, ensure_ascii=False),
                            ai_model,
                            token_usage,
                            report_id
                        )
                    )
                    affected = cursor.rowcount
                conn.commit()

            logger.info(f"[分析存储] 报告结果更新成功: ID={report_id}")
            return affected > 0

        except Exception as e:
            logger.error(f"[分析存储] 更新报告结果失败: {e}")
            raise DatabaseQueryError(f"更新报告结果失败: {e}") from e

    def add_log(
        self,
        report_id: int,
        log_level: str,
        log_message: str,
        log_data: Dict[str, Any] = None
    ) -> int:
        """
        添加分析日志

        Args:
            report_id: 关联报告ID
            log_level: 日志级别 (INFO/WARNING/ERROR)
            log_message: 日志内容
            log_data: 附加数据

        Returns:
            日志ID
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO analysis_logs
                        (report_id, log_level, log_message, log_data)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            report_id,
                            log_level,
                            log_message,
                            json.dumps(log_data, ensure_ascii=False) if log_data else None
                        )
                    )
                    log_id = cursor.lastrowid
                conn.commit()

            return log_id

        except Exception as e:
            logger.warning(f"[分析存储] 添加日志失败: {e}")
            return 0

    def get_report_by_id(self, report_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取报告

        Args:
            report_id: 报告ID

        Returns:
            报告字典，不存在返回None
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM analysis_reports WHERE id = %s",
                        (report_id,)
                    )
                    report = cursor.fetchone()

            if report:
                for field in ['input_data', 'chart_data', 'ai_analysis']:
                    if report.get(field):
                        try:
                            report[field] = json.loads(report[field])
                        except (json.JSONDecodeError, TypeError):
                            report[field] = {}

            return report

        except Exception as e:
            logger.error(f"[分析存储] 获取报告失败: {e}")
            raise DatabaseQueryError(f"获取报告失败: {e}") from e

    def get_reports_by_type(
        self,
        report_type: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        按类型获取报告列表

        Args:
            report_type: 报告类型
            limit: 数量限制
            offset: 偏移量

        Returns:
            报告列表
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, report_type, name, gender, birth_date, birth_time,
                               city, status, ai_model, token_usage, created_at
                        FROM analysis_reports
                        WHERE report_type = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                        """,
                        (report_type, limit, offset)
                    )
                    reports = cursor.fetchall()

            return reports

        except Exception as e:
            logger.error(f"[分析存储] 获取报告列表失败: {e}")
            raise DatabaseQueryError(f"获取报告列表失败: {e}") from e

    def get_report_count(self, report_type: str = None) -> int:
        """
        获取报告数量

        Args:
            report_type: 报告类型，None表示全部

        Returns:
            报告数量
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    if report_type:
                        cursor.execute(
                            "SELECT COUNT(*) as cnt FROM analysis_reports WHERE report_type = %s",
                            (report_type,)
                        )
                    else:
                        cursor.execute("SELECT COUNT(*) as cnt FROM analysis_reports")
                    result = cursor.fetchone()

            return result['cnt'] if result else 0

        except Exception as e:
            logger.error(f"[分析存储] 获取报告数量失败: {e}")
            raise DatabaseQueryError(f"获取报告数量失败: {e}") from e

    def test_connection(self) -> bool:
        """
        测试数据库连接

        Returns:
            连接是否成功
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result is not None
        except Exception as e:
            logger.error(f"[分析存储] 数据库连接测试失败: {e}")
            return False


_default_storage = None


def get_analysis_storage(config_path: str = None) -> AnalysisStorage:
    """
    获取默认的分析存储器实例（单例模式）

    Args:
        config_path: 配置文件路径

    Returns:
        AnalysisStorage实例
    """
    global _default_storage
    if _default_storage is None or config_path:
        _default_storage = AnalysisStorage(config_path)
    return _default_storage
