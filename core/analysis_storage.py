"""
分析报告存储模块
负责将 AI 分析报告存储到本地嵌入式 SQLite 数据库（data/fengshui.db）。
连接与首次建库统一委托 core.sqlite_db，无需另架 MySQL 服务。
"""
import json
import logging
import sqlite3
from typing import Dict, Any, List, Optional

from core import sqlite_db


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
    分析报告存储器（SQLite 版）
    负责管理数据库连接，存储和查询 AI 分析报告
    """

    def __init__(self, config_path: str = None):
        """
        初始化分析存储器

        Args:
            config_path: 兼容旧签名保留，当前实现忽略（DB 路径由 core.sqlite_db 统一解析）。
        """
        self.config_path = config_path
        sqlite_db.ensure_initialized()
        self._ensure_tables()
        logger.info(f"[分析存储] 初始化完成，数据库: {sqlite_db.get_db_path()}")

    def _get_connection(self, include_database: bool = True, autocommit: bool = False):
        """
        获取本地 SQLite 连接（row_factory=Row；`with` 结束自动提交并 close）。

        Returns:
            sqlite3 连接对象

        Raises:
            DatabaseConnectionError: 连接失败
        """
        try:
            return sqlite_db.get_connection()
        except sqlite3.Error as e:
            logger.error(f"[分析存储] 数据库连接失败: {e}")
            raise DatabaseConnectionError(f"数据库连接失败: {e}") from e

    def _ensure_tables(self):
        """确保所需数据表存在（analysis_reports / analysis_logs）。"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
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
        """创建分析报告表（SQLite 方言）。"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                name TEXT,
                gender TEXT,
                birth_date TEXT,
                birth_time TEXT,
                city TEXT,
                question TEXT,
                input_data TEXT,
                chart_data TEXT,
                ai_analysis TEXT,
                status TEXT DEFAULT 'completed',
                error_message TEXT,
                ai_model TEXT,
                token_usage INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _create_analysis_logs_table(self, cursor):
        """创建分析日志表（SQLite 方言）。"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER,
                log_level TEXT NOT NULL,
                log_message TEXT NOT NULL,
                log_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
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

            city = input_data.get('location') or input_data.get('city', '')
            question = input_data.get('question', '')

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO analysis_reports
                    (report_type, name, gender, birth_date, birth_time, city, question,
                     input_data, chart_data, ai_analysis, status, error_message,
                     ai_model, token_usage)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                cursor = conn.cursor()
                if error_message:
                    cursor.execute(
                        "UPDATE analysis_reports SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (status, error_message, report_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE analysis_reports SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
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
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE analysis_reports
                    SET chart_data = ?, ai_analysis = ?, status = 'completed',
                        ai_model = ?, token_usage = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
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
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO analysis_logs
                    (report_id, log_level, log_message, log_data)
                    VALUES (?, ?, ?, ?)
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
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM analysis_reports WHERE id = ?",
                    (report_id,)
                )
                report = cursor.fetchone()

            if report:
                report = dict(report)
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
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, report_type, name, gender, birth_date, birth_time,
                           city, status, ai_model, token_usage, created_at
                    FROM analysis_reports
                    WHERE report_type = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (report_type, limit, offset)
                )
                reports = [dict(r) for r in cursor.fetchall()]

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
                cursor = conn.cursor()
                if report_type:
                    cursor.execute(
                        "SELECT COUNT(*) as cnt FROM analysis_reports WHERE report_type = ?",
                        (report_type,)
                    )
                else:
                    cursor.execute("SELECT COUNT(*) as cnt FROM analysis_reports")
                result = cursor.fetchone()
                cnt = result['cnt'] if result else 0

            return cnt

        except Exception as e:
            logger.error(f"[分析存储] 获取报告数量失败: {e}")
            raise DatabaseQueryError(f"获取报告数量失败: {e}") from e

    def get_recent_reports(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近的分析报告

        Args:
            limit: 返回数量限制

        Returns:
            报告列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, report_type as type, name, gender, birth_date, birth_time,
                           city, status, ai_model, token_usage, created_at,
                           input_data, chart_data, ai_analysis
                    FROM analysis_reports
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,)
                )
                reports = [dict(r) for r in cursor.fetchall()]

            for report in reports:
                for field in ['input_data', 'chart_data', 'ai_analysis']:
                    if report.get(field):
                        try:
                            report[field] = json.loads(report[field])
                        except (json.JSONDecodeError, TypeError):
                            report[field] = {}

            return reports

        except Exception as e:
            logger.error(f"[分析存储] 获取最近报告失败: {e}")
            raise DatabaseQueryError(f"获取报告失败: {e}") from e

    def test_connection(self) -> bool:
        """
        测试数据库连接

        Returns:
            连接是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
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
