"""
分析报告存储模块
负责将 智能 分析报告存储到本地嵌入式 SQLite 数据库（data/fengshui.db）。
连接与首次建库统一委托 core.sqlite_db，无需另架 MySQL 服务。
"""
import json
import logging
import sqlite3
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from core import sqlite_db
from core.ai_cache import get_cached_result, save_to_cache, compute_input_hash, compute_question_hash, make_cache_key
from core.data_integration import DataIntegrator
from api.agnes_client import get_agnes_client, AgnesRequestError, AgnesTimeoutError, AgnesResponseError, AgnesQuotaError


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
    负责管理数据库连接，存储和查询 智能 分析报告
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
            ai_analysis: 智能分析结果
            status: 状态
            error_message: 错误信息
            ai_model: 使用的智能分析
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
                year_val = input_data.get('year', '')
                month_val = int(input_data.get('month', 0) or 0)
                day_val = int(input_data.get('day', 0) or 0)
                birth_date = (
                    f"{year_val}-"
                    f"{month_val:02d}-"
                    f"{day_val:02d}"
                )
            if 'hour' in input_data and 'minute' in input_data:
                hour_val = int(input_data.get('hour', 0) or 0)
                minute_val = int(input_data.get('minute', 0) or 0)
                birth_time = (
                    f"{hour_val:02d}:"
                    f"{minute_val:02d}"
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
            ai_analysis: 智能分析结果
            ai_model: 智能分析名称
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


# ================================================================
# AI 分析入口方法（替代旧 analysis_pipeline）
# ================================================================

# 各分析类型要求模型返回的 JSON 字段（必须与下方 _parse_ai_response 的
# required_fields 完全对应，否则解析端会补默认值导致界面字段缺失）
_JSON_SCHEMAS = {
    'bazi': {
        'final_verdict': '整体格局与日主强弱的综合判断：结合日主强弱、五行旺衰、十神格局、大运走势给出全面的总体定论（格局定性、吉凶趋势、关键建议），内容详实、结合具体干支与十神、避免套话，不少于300字',
        'key_points': '重点提示：提炼 3-5 条最关键、最值得命主注意的结论（如重大吉凶、关键大运节点、核心用神喜忌、最需规避的风险），每条为一段独立短句，用于高亮标注',
        'personality': '性格特征分析：结合日主、十神组合与五行偏枯，刻画具体性格优缺点，不少于150字',
        'career': '事业与财运分析及建议：结合官杀/财星/印星与喜用神，给出行业取向、发展节奏与具体建议，不少于200字',
        'relationships': '感情与婚姻分析及建议：结合配偶星、桃花与日支，给出婚恋趋势与相处建议，不少于180字',
        'health': '健康分析及建议：结合五行偏枯、刑冲与神煞，指出易弱脏腑与养护建议（仅作养生参考，非医疗诊断），不少于150字',
    'four_pillars_detail': '四柱天干地支的逐项解释：逐柱说明干支组合、十神含义、旺衰喜忌与吉凶细节，不少于250字',
        'scenario_advice': '针对用户提问场景（事业、婚姻、健康等）的逐项具体建议，可分行列举，不少于200字',
        'historical_cases': '历史案例或统计参考，含概率/比例信息，佐证上述判断，不少于120字',
        'probability_stats': '概率/置信度统计：用「维度名称：百分比数值%」格式逐条给出（如「事业财运：82%」「感情婚姻：65%」「健康状况：70%」「整体吉凶：75%」），每条独立、直观对比各维度强弱，便于可视化展示；百分比为基于命理数据的相对估算',
        'disclaimer': '免责声明：说明命理分析仅供参考、不构成决策或医疗依据',
    },
    'meihua': {
        'final_verdict': '总体断语：综合本卦/互卦/变卦、体用生克、动爻与应期，给出全面的总体判断（格局定性、吉凶趋势、关键时机、核心建议），内容详实、结合具体卦象、避免套话，不少于300字',
        'key_points': '重点提示：提炼 3-5 条最关键、最值得问者注意的结论（如吉凶关键、最佳时机、核心行动、最需规避之事），每条为一段独立短句，用于高亮标注',
        'analysis': '卦象分析：结合卦名、卦辞、上下卦与体用关系，给出整体吉凶与事态趋势，不少于200字',
    'hexagram_interpretations': '每条爻辞的解释与吉凶：结合动爻与变卦，逐项说明各爻含义与对所占之事的影响，不少于200字',
    'scenario_advice': '针对用户提问场景（事业、婚姻、健康等）的具体建议，可分行列举，不少于200字',
    'historical_cases': '历史案例或统计参考，含概率/比例信息，佐证卦象判断，不少于120字',
    'probability_stats': '针对所占之事的吉凶概率或置信度统计，给出相对比例',
        'advice': '行动建议：结合体用生克与变卦趋势，给出 3-5 条具体、可执行的行动指引；每条以「【高】」「【中】」「【低】」开头标注优先级，接着明确写清「应该做什么」「避免什么」「最佳时机」，每条独立成段，避免笼统套话',
        'disclaimer': '免责声明：说明卦象分析仅供参考、不构成决策依据',
    },
    'liuren': {
        'final_verdict': '总体断语：综合四课、三传、天将与神煞，给出全面的总体判断（课体定性、吉凶趋势、关键时机、核心建议），内容详实、结合具体课体、避免套话，不少于300字',
        'key_points': '重点提示：提炼 3-5 条最关键、最值得问者注意的结论（如课体吉凶关键、最佳应期、核心行动、最需规避之象），每条为一段独立短句，用于高亮标注',
        'analysis': '课体分析：结合四课生克、三传发用、天将与神煞，逐项解析课体含义与事态脉络，不少于250字',
        'scenario_advice': '针对用户提问场景（事业、婚姻、健康等）的具体建议，可分行列举，不少于200字',
        'historical_cases': '历史案例或统计参考，含概率/比例信息，佐证六壬判断，不少于120字',
        'probability_stats': '针对所占之事的吉凶概率或置信度统计，给出相对比例',
        'timing': '应期与时机分析：结合三传与天将，指出事情发端与应验时机，不少于150字',
        'disclaimer': '免责声明：说明六壬分析仅供参考、不构成决策依据',
    },
}


def _json_schema_instruction(pan_type: str) -> str:
    """
    构造要求模型以 JSON 输出的指令，追加到用户提示词末尾。

    模型默认会对「请分析」类请求返回自然语言散文，而解析端期望结构化 JSON，
    二者不一致会导致 JSON 解析失败、退回原始文本（界面字段缺失）。
    此处显式约束输出格式，字段与 _parse_ai_response 的 required_fields 对齐。
    """
    schema = _JSON_SCHEMAS.get(pan_type, _JSON_SCHEMAS['bazi'])
    fields = ",\n".join(f'  "{k}": "{v}"' for k, v in schema.items())
    return (
        "\n\n【输出格式要求】\n"
        "你必须且只能输出一个 JSON 对象，不要输出任何解释性文字，不要使用 markdown 代码块，"
        "不要添加任何前缀或后缀。各字段 value 的类型要求如下：\n"
        "  - final_verdict / disclaimer / key_points：字符串（key_points 各要点以换行 '\\n' 分隔）；\n"
        "  - 其余分析类字段（personality / career / relationships / health / four_pillars_detail / "
        "scenario_advice / analysis / hexagram_interpretations / advice / timing / "
        "historical_cases / probability_stats）：均为「字符串数组」，每条为一段独立、具体的分析内容，"
        "数组元素不少于 3 条，内容要详细、专业、避免空泛套话。\n"
        "JSON 字段如下：\n"
        "{\n" + fields + "\n}"
    )


def run_bazi_analysis(input_data: Dict[str, Any], chart_data: Dict[str, Any] = None, task_id: str = None) -> Dict[str, Any]:
    """
    执行八字AI分析

    Args:
        input_data: 输入数据（姓名、性别、出生时间等）
        chart_data: 排盘数据（四柱、五行、十神等）
        task_id: 任务ID

    Returns:
        包含 success, ai_analysis, token_usage, elapsed_seconds 等字段的结果字典
    """
    return _run_ai_analysis('bazi', input_data, chart_data, task_id)


def run_meihua_analysis(input_data: Dict[str, Any], chart_data: Dict[str, Any] = None, task_id: str = None) -> Dict[str, Any]:
    """
    执行梅花易数AI分析

    Args:
        input_data: 输入数据（问题、起卦方式等）
        chart_data: 卦象数据（本卦、变卦、动爻等）
        task_id: 任务ID

    Returns:
        包含 success, ai_analysis, token_usage, elapsed_seconds 等字段的结果字典
    """
    return _run_ai_analysis('meihua', input_data, chart_data, task_id)


def run_liuren_analysis(input_data: Dict[str, Any], chart_data: Dict[str, Any] = None, task_id: str = None) -> Dict[str, Any]:
    """
    执行大六壬AI分析

    Args:
        input_data: 输入数据（占问事项、时间等）
        chart_data: 排盘数据（四课、三传、天将等）
        task_id: 任务ID

    Returns:
        包含 success, ai_analysis, token_usage, elapsed_seconds 等字段的结果字典
    """
    return _run_ai_analysis('liuren', input_data, chart_data, task_id)


def _run_ai_analysis(pan_type: str, input_data: Dict[str, Any], chart_data: Dict[str, Any], task_id: str = None) -> Dict[str, Any]:
    """
    统一的AI分析入口方法

    Args:
        pan_type: 分析类型 ('bazi'/'meihua'/'liuren')
        input_data: 输入数据
        chart_data: 排盘/卦象数据
        task_id: 任务ID

    Returns:
        包含 success, ai_analysis, token_usage, elapsed_seconds 等字段的结果字典
    """
    from core.ai_config import is_ai_configured

    start_time = time.time()
    logger.info(f"[AI分析] 开始 {pan_type} 分析，task_id={task_id}")

    # 检查缓存（无论AI是否配置，先查缓存）
    cached = get_cached_result(pan_type, input_data, question=None)
    if cached is not None:
        logger.info(f"[AI分析] 缓存命中 {pan_type}，跳过API调用")
        elapsed = time.time() - start_time
        return {
            'success': True,
            'ai_analysis': cached,
            'from_cache': True,
            'token_usage': 0,
            'elapsed_seconds': round(elapsed, 2)
        }

    # 检查AI配置
    if not is_ai_configured():
        logger.warning(f"[AI分析] AI未配置，无法执行 {pan_type} 分析")
        return {
            'success': False,
            'error_type': 'ai_not_configured',
            'error_message': '龙虎山大师兄功能当前不可用，请在「设置」中配置AI模型',
            'token_usage': 0,
            'elapsed_seconds': 0
        }

    # 构建数据整合
    try:
        integrator = DataIntegrator()
        integrator.collect_raw_data(input_data, chart_data)
        integrator.clean_and_unify()
        prompt = integrator.build_comprehensive_prompt(pan_type)
        # 追加结构化 JSON 输出约束，避免模型返回散文导致解析失败
        prompt = prompt + _json_schema_instruction(pan_type)
    except Exception as e:
        logger.error(f"[AI分析] 构建提示词失败: {e}")
        return {
            'success': False,
            'error_type': 'prompt_build_error',
            'error_message': f'构建提示词失败: {str(e)}',
            'token_usage': 0,
            'elapsed_seconds': 0
        }

    # 调用AI
    try:
        client = get_agnes_client()
        messages = [
            {'role': 'system', 'content': '你是龙虎山大师兄，一位精通中国传统命理学（八字、梅花易数、大六壬）的专家。请基于用户提供的命理数据进行专业、深入、详尽的分析：各项结论要结合具体干支/卦象/课体数据展开，避免任何空泛套话；分析类字段需分多条列举、每条独立且具体；并务必提炼关键结论用于重点提示。语言专业、可读、有条理。'},
            {'role': 'user', 'content': prompt}
        ]

        result = client.chat_completion(messages)
        content = result.get('content', '')

        # 解析AI返回结果
        ai_analysis = _parse_ai_response(content, pan_type)

        # 保存缓存
        try:
            save_to_cache(pan_type, input_data, question=None, ai_result=ai_analysis)
        except Exception as e:
            logger.warning(f"[AI分析] 保存缓存失败（不影响结果）: {e}")

        elapsed = time.time() - start_time
        token_usage = result.get('usage', {}).get('total_tokens', 0)

        logger.info(f"[AI分析] {pan_type} 分析完成，耗时: {elapsed:.2f}秒，Token: {token_usage}")

        return {
            'success': True,
            'ai_analysis': ai_analysis,
            'from_cache': False,
            'token_usage': token_usage,
            'elapsed_seconds': round(elapsed, 2)
        }

    except AgnesTimeoutError as e:
        elapsed = time.time() - start_time
        logger.error(f"[AI分析] 超时: {e}")
        return {
            'success': False,
            'error_type': 'ai_timeout',
            'error_message': f'龙虎山大师兄请求超时: {str(e)}',
            'token_usage': 0,
            'elapsed_seconds': round(elapsed, 2)
        }
    except AgnesRequestError as e:
        elapsed = time.time() - start_time
        logger.error(f"[AI分析] 请求失败: {e}")
        return {
            'success': False,
            'error_type': 'ai_request_error',
            'error_message': f'龙虎山大师兄请求失败: {str(e)}',
            'token_usage': 0,
            'elapsed_seconds': round(elapsed, 2)
        }
    except AgnesQuotaError as e:
        elapsed = time.time() - start_time
        logger.error(f"[AI分析] 配额不足: {e}")
        return {
            'success': False,
            'error_type': 'ai_quota_error',
            'error_message': f'龙虎山大师兄配额不足: {str(e)}',
            'token_usage': 0,
            'elapsed_seconds': round(elapsed, 2)
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[AI分析] 未知错误: {e}", exc_info=True)
        return {
            'success': False,
            'error_type': 'unknown_error',
            'error_message': f'分析失败: {str(e)}',
            'token_usage': 0,
            'elapsed_seconds': round(elapsed, 2)
        }


def _parse_ai_response(content: str, pan_type: str) -> Dict[str, Any]:
    """
    解析AI返回的JSON结果

    Args:
        content: AI返回的文本内容
        pan_type: 分析类型

    Returns:
        解析后的字典结果
    """
    from api.agnes_client import AgnesClient

    try:
        cleaned = AgnesClient._clean_json_response(content)
        if not cleaned:
            return {'summary': content[:500], 'analysis': '解析失败'}

        result = json.loads(cleaned)

        # 验证必需字段：扩展为完整 schema，确保所有非字符串字段都被
        # _validate_json_result 归一化为列表（除 final_verdict/disclaimer 保持字符串），
        # 否则 UI 收到字符串后会逐字符渲染（一个字一行）。
        required_fields = [
            'final_verdict', 'key_points', 'personality', 'career', 'relationships', 'health',
            'four_pillars_detail', 'scenario_advice', 'historical_cases',
            'probability_stats', 'disclaimer',
        ]
        if pan_type == 'meihua':
            required_fields = [
                'final_verdict', 'key_points', 'analysis', 'hexagram_interpretations',
                'scenario_advice', 'historical_cases', 'probability_stats',
                'advice', 'disclaimer',
            ]
        elif pan_type == 'liuren':
            required_fields = [
                'final_verdict', 'key_points', 'analysis', 'scenario_advice',
                'historical_cases', 'probability_stats', 'timing', 'disclaimer',
            ]

        result = AgnesClient._validate_json_result(result, required_fields)
        return result

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"[AI分析] JSON解析失败，使用原始文本: {e}")
        return {
            'summary': content[:500],
            'analysis': content,
            'final_verdict': '需结合实际情况分析',
            'disclaimer': '分析仅供参考'
        }
