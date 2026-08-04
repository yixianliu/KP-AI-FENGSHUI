"""
数据分析主流程模块
整合数据验证、AI模型调用、结果存储的完整流程
包含完善的错误处理和日志记录机制
"""
import os
import sys
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from core.path_utils import get_app_dir, get_config_path, get_resource_path, get_logs_dir

from api.agnes_client import (
    AgnesClient, AgnesClientError, AgnesRequestError,
    AgnesTimeoutError, AgnesResponseError
)
from core.data_validator import DataValidator, DataValidationError
from core.analysis_storage import (
    AnalysisStorage, AnalysisStorageError,
    DatabaseConnectionError, DatabaseQueryError
)
from core.data_integration import DataIntegrator
from core.knowledge_base import KnowledgeBase
from core.ai_cache import (
    get_cached_result, save_to_cache,
    get_cache_stats, clear_all as ai_cache_clear_all,
)


def setup_logger(log_dir: str = None, log_level: int = logging.INFO) -> logging.Logger:
    """
    设置日志系统

    Args:
        log_dir: 日志目录（忽略，统一使用 path_utils.get_logs_dir()）
        log_level: 日志级别

    Returns:
        配置好的logger
    """
    log_dir = get_logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger('analysis_pipeline')
    logger.setLevel(log_level)

    if logger.handlers:
        return logger

    log_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    log_file = log_dir / f'analysis_pipeline_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()


class AnalysisPipelineError(Exception):
    """分析流程异常基类"""
    pass


class AnalysisPipeline:
    """
    数据分析主流程
    整合数据验证、AI分析、结果存储的完整流程
    """

    def __init__(
            self,
            config_path: str = None,
            log_level: int = logging.INFO
    ):
        """
        初始化分析流程

        Args:
            config_path: 配置文件路径
            log_level: 日志级别
        """
        global logger
        logger = setup_logger(log_level=log_level)

        logger.info("=" * 60)
        logger.info("[分析流程] 初始化数据分析流程")
        logger.info("=" * 60)

        # ===== AI 降级探测 =====
        self.ai_enabled = True
        self._ai_disabled_reasons = []

        # 探测 config.ini 关键配置段
        if config_path is None:
            config_path = str(get_config_path())
        else:
            config_path = str(Path(config_path))

        import configparser
        cfg = configparser.ConfigParser()
        cfg.read(config_path, encoding='utf-8')

        # 注：本地 SQLite 存储（AnalysisStorage）始终可用，无需外部服务。
        # AI 是否启用仅取决于 [agnes] 配置段。
        if not cfg.has_section('agnes'):
            self.ai_enabled = False
            self._ai_disabled_reasons.append('[agnes]')

        if self._ai_disabled_reasons:
            logger.warning(f"[分析流程] AI 已禁用，缺失配置段: {', '.join(self._ai_disabled_reasons)}")
        else:
            logger.info("[分析流程] 配置完整性检测通过")

        try:
            self.validator = DataValidator()
            self.storage = AnalysisStorage(config_path) if self.ai_enabled else None
            self.agnes_client = AgnesClient(verify_ssl=False) if self.ai_enabled else None
            logger.info("[分析流程] 所有模块初始化完成")
        except Exception as e:
            logger.error(f"[分析流程] 初始化失败: {e}")
            logger.error(traceback.format_exc())
            if not self.ai_enabled:
                logger.warning("[分析流程] 已处于降级模式，不抛出异常")
            else:
                raise AnalysisPipelineError(f"分析流程初始化失败: {e}") from e

    # ==================== 八字分析流程 ====================

    def run_bazi_analysis(
            self,
            input_data: Dict[str, Any],
            chart_data: Dict[str, Any] = None,
            task_id: str = None
    ) -> Dict[str, Any]:
        """
        执行八字AI分析完整流程

        Args:
            input_data: 输入数据字典
            chart_data: 预计算的排盘数据（可选）
            task_id: 任务ID（用于日志关联，可选）

        Returns:
            分析结果字典，包含 report_id, ai_analysis 等
        """
        report_id = None
        start_time = datetime.now()

        try:
            # 缓存命中直接返回（P2-4：避免重复 API 调用）
            cached = get_cached_result('bazi', input_data, None)
            if cached:
                logger.info(f"[八字分析] 缓存命中（hit_count={cached.get('_cache_hit_count', 1)}），跳过 API 调用")
                return {
                    'success': True,
                    'report_id': None,
                    'ai_analysis': cached,
                    'chart_data': chart_data or {},
                    'token_usage': 0,
                    'elapsed_seconds': (datetime.now() - start_time).total_seconds(),
                    'from_cache': True,
                }

            logger.info("[八字分析] ========== 开始八字AI分析流程 ==========")
            logger.info(f"[八字分析] 输入数据: 姓名={input_data.get('name', '未知')}, "
                        f"性别={input_data.get('gender', '未知')}, task_id={task_id}")

            if not self.validator.validate_bazi_input(input_data):
                errors = self.validator.get_errors()
                error_msg = f"输入数据验证失败: {'; '.join(errors)}"
                logger.error(f"[八字分析] {error_msg}")
                raise DataValidationError(error_msg)

            report_id = self.storage.create_pending_report('bazi', input_data)
            logger.info(f"[八字分析] 创建待处理报告，ID: {report_id}")

            self.storage.add_log(report_id, 'INFO', '八字分析流程开始', {
                'input_data': {k: v for k, v in input_data.items() if k != 'name' or True}
            })

            if chart_data is None:
                logger.info("[八字分析] 排盘数据未提供，使用空数据")
                chart_data = {}
            else:
                self.storage.add_log(report_id, 'INFO', '排盘数据已准备')

            ai_result = self._call_agnes_for_bazi(input_data, chart_data)

            token_usage = ai_result.get('usage', {}).get('total_tokens', 0)
            ai_analysis = ai_result.get('analysis', {})

            self.storage.add_log(report_id, 'INFO', 'AI分析完成', {
                'token_usage': token_usage,
                'analysis_fields': list(ai_analysis.keys())
            })

            if not self.validator.validate_ai_analysis_result(ai_analysis, 'bazi'):
                warnings = self.validator.get_warnings()
                if warnings:
                    logger.warning(f"[八字分析] AI结果有警告: {'; '.join(warnings)}")
                    self.storage.add_log(report_id, 'WARNING', 'AI结果验证有警告', {
                        'warnings': warnings
                    })

            self.storage.update_report_result(
                report_id=report_id,
                chart_data=chart_data,
                ai_analysis=ai_analysis,
                ai_model=self.agnes_client.model,
                token_usage=token_usage
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[八字分析] 流程完成，耗时: {elapsed:.2f}秒，报告ID: {report_id}")
            logger.info("[八字分析] ========================================")

            # 写入 AI 缓存（P2-4：同盘 + 同问题命中本地 DB，避免重复 API 调用）
            try:
                save_to_cache('bazi', input_data, None, ai_analysis)
            except Exception as e:
                logger.debug(f"[八字分析] 写入缓存失败（忽略）: {e}")

            return {
                'success': True,
                'report_id': report_id,
                'ai_analysis': ai_analysis,
                'chart_data': chart_data,
                'token_usage': token_usage,
                'elapsed_seconds': elapsed
            }

        except DataValidationError as e:
            error_msg = str(e)
            logger.error(f"[八字分析] 数据验证错误: {error_msg}")
            if report_id:
                self.storage.update_report_status(report_id, 'failed', error_msg)
                self.storage.add_log(report_id, 'ERROR', '数据验证失败', {'error': error_msg})
            return self._build_error_result(report_id, 'validation_error', error_msg, start_time)

        except AgnesTimeoutError as e:
            error_msg = f"AI模型请求超时: {e}"
            logger.error(f"[八字分析] {error_msg}")
            if report_id:
                self.storage.update_report_status(report_id, 'failed', error_msg)
                self.storage.add_log(report_id, 'ERROR', 'AI请求超时', {'error': str(e)})
            return self._build_error_result(report_id, 'ai_timeout', error_msg, start_time)

        except AgnesRequestError as e:
            error_msg = f"AI模型请求失败: {e}"
            logger.error(f"[八字分析] {error_msg}")
            if report_id:
                self.storage.update_report_status(report_id, 'failed', error_msg)
                self.storage.add_log(report_id, 'ERROR', 'AI请求失败', {'error': str(e)})
            return self._build_error_result(report_id, 'ai_request_error', error_msg, start_time)

        except AgnesResponseError as e:
            error_msg = f"AI响应解析失败: {e}"
            logger.error(f"[八字分析] {error_msg}")
            if report_id:
                self.storage.update_report_status(report_id, 'failed', error_msg)
                self.storage.add_log(report_id, 'ERROR', 'AI响应解析失败', {'error': str(e)})
            return self._build_error_result(report_id, 'ai_response_error', error_msg, start_time)

        except DatabaseConnectionError as e:
            error_msg = f"数据库连接异常: {e}"
            logger.error(f"[八字分析] {error_msg}")
            logger.error(traceback.format_exc())
            return self._build_error_result(report_id, 'db_connection_error', error_msg, start_time)

        except DatabaseQueryError as e:
            error_msg = f"数据库操作异常: {e}"
            logger.error(f"[八字分析] {error_msg}")
            if report_id:
                self.storage.add_log(report_id, 'ERROR', '数据库操作失败', {'error': str(e)})
            return self._build_error_result(report_id, 'db_query_error', error_msg, start_time)

        except Exception as e:
            error_msg = f"未知错误: {e}"
            logger.error(f"[八字分析] {error_msg}")
            logger.error(traceback.format_exc())
            if report_id:
                try:
                    self.storage.update_report_status(report_id, 'failed', error_msg)
                    self.storage.add_log(report_id, 'ERROR', '未知错误', {
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    })
                except Exception:
                    pass
            return self._build_error_result(report_id, 'unknown_error', error_msg, start_time)

    def _call_agnes_for_bazi(
            self,
            input_data: Dict[str, Any],
            chart_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用AGNES模型进行八字分析

        Args:
            input_data: 输入数据
            chart_data: 排盘数据

        Returns:
            包含 analysis 和 usage 的结果字典
        """
        logger.info("[八字分析] 构建AI分析请求...")

        integrator = DataIntegrator()
        knowledge_base = KnowledgeBase()

        integrator.collect_raw_data(input_data, chart_data)
        integrator.collect_processed_data(
            wuxing_result=chart_data.get('wuxing', {}),
            shishen_result=chart_data.get('shishen', {}),
            mingli_result=chart_data.get('mingli', {}),
            major_fortune=chart_data.get('major_fortune', {})
        )
        integrator.collect_historical_records(self.storage, limit=3)
        integrator.collect_knowledge_context(knowledge_base, 'bazi')
        integrator.clean_and_unify()
        integrator.build_relationships()

        prompt = integrator.build_comprehensive_prompt('bazi')

        system_prompt = (
            "你是一位德高望重的命理宗师，精研子平八字、阴阳五行、十神生克、十二长生、神煞、纳音、格局与用神喜忌之学，断语严谨、有理有据。\n"
            "你将收到一份【已经程序精确排盘】的八字数据，包含四柱干支、五行分值与强弱、十神分布与权重、吉神凶煞、纳音、空亡、大运走势等。请基于这些数据做专业、深入、可落地的分析，严禁凭空臆造。\n"
            "\n"
            "分析铁律：\n"
            "1. 所有结论必须严格依据所提供的数据推导，并明确点出依据（如『日主甲木生于寅月得令』『财星透干而旺』『七杀攻身』等），不可泛泛而谈；\n"
            "2. 必须判定【日主强弱】（身强/身弱/中和）与【用神、喜神、忌神】，这是全文分析的枢纽；\n"
            "3. 五行分析要指出最旺与最弱之五行、对日主的助益或耗泄，并说明补救方向；\n"
            "4. 十神分析要结合具体十神（正官/七杀/正财/偏财/正印/偏印/食神/伤官/比肩/劫财）及其旺衰，说明对性格、事业、婚姻、健康的影响；\n"
            "5. 大运分析要说明起运年龄、各步大运干支对命局是喜是忌、关键运势窗口；\n"
            "6. 用词审慎，多用『多』『易』『相对』『宜』等，避免绝对化与恐吓式表述；\n"
            "7. 每条分析都要给出命理依据，避免空话套话。\n"
            "\n"
            "输出格式要求：严格用JSON格式输出，不要包含任何额外的解释或说明文字，也不要使用 Markdown 代码块。\n"
            "JSON必须包含以下字段（数组类字段 5-8 条，每条 80-150 字，须含具体命理依据与可操作建议）：\n"
            "- personality（性格特质）\n"
            "- career（事业财运）\n"
            "- marriage（婚姻感情）\n"
            "- health（健康注意）\n"
            "- suggestions（综合建议：针对命局喜忌，给出事业、情感、健康、修身方面的统揽性建议）\n"
            "- pattern_analysis（格局与用神分析：含日主强弱、格局类型、用神喜忌、成败关键）\n"
            "- wuxing_balance（五行平衡分析：最旺/最弱五行、对日主影响、补救方向）\n"
            "- shishen_analysis（十神分析：主导十神及其对人生各领域的影响）\n"
            "- improvement_plan（改善方案：4-6条，按五行补救/方位颜色/人际修身/风水布局/时机选择分类，具体可操作）\n"
            "请务必深入、专业、精准，让内容对命主真正有用。"
        )

        required_fields = ['personality', 'career', 'marriage', 'health', 'suggestions',
                           'pattern_analysis', 'wuxing_balance', 'shishen_analysis',
                           'improvement_plan']

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        logger.info("[八字分析] 调用AGNES AI模型进行分析...")
        result = self.agnes_client.chat_completion(messages, temperature=0.25, max_tokens=2048)

        content = result.get('content', '')
        usage = result.get('usage', {})

        cleaned_content = self.agnes_client._clean_json_response(content)

        import json
        try:
            analysis = json.loads(cleaned_content)
            analysis = self.agnes_client._validate_json_result(analysis, required_fields)
        except json.JSONDecodeError:
            logger.warning("[八字分析] JSON解析失败，尝试文本解析")
            analysis = self._parse_text_to_bazi_fields(cleaned_content, required_fields)

        logger.info(f"[八字分析] AI分析完成，生成字段: {list(analysis.keys())}")

        return {
            'analysis': analysis,
            'usage': usage
        }

    def _build_bazi_prompt(
            self,
            input_data: Dict[str, Any],
            chart_data: Dict[str, Any]
    ) -> str:
        """
        构建八字分析提示词

        Args:
            input_data: 输入数据
            chart_data: 排盘数据

        Returns:
            提示词字符串
        """
        parts = []

        name = input_data.get('name', '未命名')
        gender = input_data.get('gender', '未知')
        parts.append(f"命主信息：姓名{name}，性别{gender}")

        if 'year' in input_data and 'month' in input_data and 'day' in input_data:
            birth_date = (
                f"{input_data['year']}-{input_data['month']:02d}-{input_data['day']:02d}"
            )
            birth_time = f"{input_data.get('hour', 0):02d}:{input_data.get('minute', 0):02d}"
            parts.append(f"出生时间：公历{birth_date} {birth_time}")

        loc = input_data.get('location') or input_data.get('city')
        if loc:
            parts.append(f"出生地：{loc}")

        if chart_data:
            bazi = chart_data.get('bazi', chart_data)
            if isinstance(bazi, dict):
                if 'year' in bazi and 'month' in bazi and 'day' in bazi and 'hour' in bazi:
                    parts.append(
                        f"八字四柱：年柱{bazi['year']} 月柱{bazi['month']} "
                        f"日柱{bazi['day']} 时柱{bazi['hour']}"
                    )
                if 'rizhu' in bazi:
                    parts.append(f"日主：{bazi['rizhu']}")

            wuxing = chart_data.get('wuxing', {})
            if wuxing:
                wx_summary = wuxing.get('summary', '')
                if wx_summary:
                    parts.append(f"五行分析：{wx_summary}")
                for wx in ['木', '火', '土', '金', '水']:
                    wx_data = wuxing.get(wx, {})
                    if isinstance(wx_data, dict):
                        count = wx_data.get('count', 0)
                        percentage = wx_data.get('percentage', 0)
                        if count > 0:
                            parts.append(f"  {wx}：{count:.1f} ({percentage}%)")

            shishen = chart_data.get('shishen', {})
            if shishen and shishen.get('summary'):
                shishen_list = [f"{k}{v}个" for k, v in shishen['summary'].items()]
                parts.append(f"十神分布：{'、'.join(shishen_list)}")

        return '\n'.join(parts)

    def _parse_text_to_bazi_fields(self, content: str, required_fields: List[str]) -> Dict[str, Any]:
        """
        解析非JSON格式的八字分析文本

        Args:
            content: 文本内容
            required_fields: 必填字段

        Returns:
            解析后的字典
        """
        section_keywords = {
            'personality': ['性格', '人格', '特质', '个性'],
            'career': ['事业', '财运', '工作', '职业', '生意'],
            'marriage': ['婚姻', '感情', '爱情', '姻缘', '婚恋'],
            'health': ['健康', '身体', '疾病', '养生'],
            'suggestions': ['建议', '忠告', '提示', '注意事项'],
            'pattern_analysis': ['格局', '格', '局'],
            'wuxing_balance': ['五行', '平衡', '生克'],
            'shishen_analysis': ['十神', '用神', '忌神'],
            'improvement_plan': ['改善', '补救', '调理', '化解', '趋吉避凶']
        }

        result = {}
        for field in required_fields:
            result[field] = []

        current_field = None

        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue

            matched = False
            for field, keywords in section_keywords.items():
                if field in required_fields:
                    for kw in keywords:
                        if kw in line and len(line) < 40:
                            current_field = field
                            matched = True
                            break
                if matched:
                    break

            if matched:
                continue

            if current_field and current_field in required_fields:
                if line[0] in ['•', '·', '-', '●', '★', '◆', '1.', '2.', '3.', '4.', '5.', '（', '(']:
                    result[current_field].append(line.lstrip('•·-●★◆1234567890.（() '))
                elif len(line) > 10:
                    result[current_field].append(line)

        for field in required_fields:
            if not result[field]:
                result[field] = ['AI分析结果格式异常，需人工解读']

        return result

    # ==================== 梅花易数分析流程 ====================

    def run_meihua_analysis(
            self,
            input_data: Dict[str, Any],
            hexagram_data: Dict[str, Any] = None,
            task_id: str = None
    ) -> Dict[str, Any]:
        """
        执行梅花易数AI分析完整流程

        Args:
            input_data: 输入数据字典
            hexagram_data: 预计算的卦象数据（可选）
            task_id: 任务ID（用于日志关联，可选）

        Returns:
            分析结果字典
        """
        report_id = None
        start_time = datetime.now()

        try:
            # 缓存命中直接返回（P2-4：避免重复 API 调用）
            cached = get_cached_result('meihua', input_data, input_data.get('question', ''))
            if cached:
                logger.info(f"[梅花易数] 缓存命中（hit_count={cached.get('_cache_hit_count', 1)}），跳过 API 调用")
                return {
                    'success': True,
                    'report_id': None,
                    'ai_analysis': cached,
                    'hexagram_data': hexagram_data or {},
                    'token_usage': 0,
                    'elapsed_seconds': (datetime.now() - start_time).total_seconds(),
                    'from_cache': True,
                }

            logger.info("[梅花易数] ======== 开始梅花易数AI分析流程 ========")
            logger.info(f"[梅花易数] 所问之事: {input_data.get('question', '未指定')}, task_id={task_id}")

            if not self.validator.validate_meihua_input(input_data):
                errors = self.validator.get_errors()
                error_msg = f"输入数据验证失败: {'; '.join(errors)}"
                logger.error(f"[梅花易数] {error_msg}")
                raise DataValidationError(error_msg)

            report_id = self.storage.create_pending_report('meihua', input_data)
            logger.info(f"[梅花易数] 创建待处理报告，ID: {report_id}")

            self.storage.add_log(report_id, 'INFO', '梅花易数分析流程开始', {
                'method': input_data.get('method', 'unknown'),
                'question': input_data.get('question', '')
            })

            if hexagram_data is None:
                hexagram_data = {}

            ai_result = self._call_agnes_for_meihua(input_data, hexagram_data)

            token_usage = ai_result.get('usage', {}).get('total_tokens', 0)
            ai_analysis = ai_result.get('analysis', {})

            self.storage.add_log(report_id, 'INFO', 'AI分析完成', {
                'token_usage': token_usage,
                'analysis_fields': list(ai_analysis.keys())
            })

            if not self.validator.validate_ai_analysis_result(ai_analysis, 'meihua'):
                warnings = self.validator.get_warnings()
                if warnings:
                    logger.warning(f"[梅花易数] AI结果有警告: {'; '.join(warnings)}")
                    self.storage.add_log(report_id, 'WARNING', 'AI结果验证有警告', {
                        'warnings': warnings
                    })

            self.storage.update_report_result(
                report_id=report_id,
                chart_data=hexagram_data,
                ai_analysis=ai_analysis,
                ai_model=self.agnes_client.model,
                token_usage=token_usage
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[梅花易数] 流程完成，耗时: {elapsed:.2f}秒，报告ID: {report_id}")
            logger.info("[梅花易数] ======================================")

            # 写入 AI 缓存（P2-4：缓存键含 question 字段，不同问题不命中）
            try:
                save_to_cache('meihua', input_data, input_data.get('question', ''), ai_analysis)
            except Exception as e:
                logger.debug(f"[梅花易数] 写入缓存失败（忽略）: {e}")

            return {
                'success': True,
                'report_id': report_id,
                'ai_analysis': ai_analysis,
                'hexagram_data': hexagram_data,
                'token_usage': token_usage,
                'elapsed_seconds': elapsed
            }

        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            logger.error(f"[梅花易数] {error_msg}")
            logger.error(traceback.format_exc())
            if report_id:
                try:
                    self.storage.update_report_status(report_id, 'failed', error_msg)
                    self.storage.add_log(report_id, 'ERROR', '分析失败', {
                        'error_type': type(e).__name__,
                        'error': str(e)
                    })
                except Exception:
                    pass
            return self._build_error_result(report_id, type(e).__name__, error_msg, start_time)

    def _call_agnes_for_meihua(
            self,
            input_data: Dict[str, Any],
            hexagram_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用AGNES模型进行梅花易数分析

        Args:
            input_data: 输入数据
            hexagram_data: 卦象数据

        Returns:
            包含 analysis 和 usage 的结果字典
        """
        logger.info("[梅花易数] 构建AI分析请求...")

        prompt = self._build_meihua_prompt(input_data, hexagram_data)

        # 注入梅花易数知识库上下文（卦辞/爻辞/解卦原则），让解读有据可依
        try:
            kb = KnowledgeBase()
            meihua_kb = kb.build_meihua_knowledge_context(hexagram_data)
            if meihua_kb:
                prompt += (
                    "\n\n" + "=" * 70 +
                    "\n【梅花易数知识库参考】\n" + "=" * 70 +
                    "\n" + meihua_kb
                )
        except Exception as e:
            logger.warning(f"[梅花易数] 知识库上下文注入失败（忽略继续）: {e}")

        system_prompt = (
            "你是一位精研邵雍梅花易数的占卜宗师，深谙先天后天六十四卦卦辞爻辞、体用生克、互变错综、卦气旺衰与先天数理。\n"
            "你将收到一份已经程序起出的卦象（本卦、互卦、变卦、动爻、卦辞爻辞、体用五行生克、综合吉凶）。请据此做专业、深入、针对『所问之事』的解读，严禁套话。\n"
            "\n"
            "分析铁律：\n"
            "1. 必须结合具体卦象：点出本卦之义、动爻爻辞、体用（上卦为某、下卦为某，体卦为某、用卦为某）及其生克关系；\n"
            "2. 互卦、变卦必须纳入推演：说明事情的发展趋势与最终归宿；\n"
            "3. 要区分『体』为我方、『用』为所问之事/对方，据此判断事之成否、快慢、损益；\n"
            "4. 针对『所问之事』给出明确判断（吉/凶/平、成/不成、宜动/宜静），并说明关键时机与注意事项；\n"
            "5. 用词审慎，避免绝对化；给出现实中可操作的趋吉避凶建议；\n"
            "6. 严禁脱离卦象空谈，每条分析都要引用具体卦名、爻位或体用生克作为依据。\n"
            "\n"
            "输出格式要求：严格用JSON格式输出，不要包含任何额外的解释或说明文字，也不要使用 Markdown 代码块。\n"
            "JSON必须包含以下字段（数组类字段 5-8 条，每条 80-150 字，须引卦象依据并给可操作建议）：\n"
            "- gua_overview（卦象概述：本卦之义、体用、所占之事总象）\n"
            "- situation_analysis（事态分析：当前形势、用神旺衰、成事之机）\n"
            "- good_omens（吉兆机遇：有利因素、宜把握之时机）\n"
            "- bad_omens（凶兆隐患：不利因素、须防范之风险）\n"
            "- action_advice（行动建议：宜/忌、动/静、方位、时机、具体做法）\n"
            "- final_verdict（总结判断：对所问之事的总体定论与一句话建议）\n"
            "\n"
            "【严格格式示例】你必须严格输出如下结构的纯 JSON，且数组字段必须是 JSON 数组（方括号、多个字符串元素），"
            "绝不能把数组字段写成单个字符串或对象：\n"
            "{\n"
            "  'gua_overview': ['本卦水火既济，事已成之象……', '体卦为坎水、用卦为离火，体克用……'],\n"
            "  'situation_analysis': ['当前形势……', '用神旺衰……'],\n"
            "  'good_omens': ['有利因素一……', '有利因素二……'],\n"
            "  'bad_omens': ['风险隐患一……'],\n"
            "  'action_advice': ['宜……忌……'],\n"
            "  'final_verdict': '一句话定论……'\n"
            "}\n"
            "请深入、专业、精准，让求测者得到真正有用的指引。"
        )

        required_fields = [
            'gua_overview', 'situation_analysis', 'good_omens',
            'bad_omens', 'action_advice', 'final_verdict'
        ]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        logger.info("[梅花易数] 调用AGNES AI模型进行分析...")
        result = self.agnes_client.chat_completion(messages, temperature=0.4, max_tokens=2048)

        content = result.get('content', '')
        usage = result.get('usage', {})

        cleaned_content = self.agnes_client._clean_json_response(content)

        import json
        try:
            analysis = json.loads(cleaned_content)
            analysis = self.agnes_client._validate_json_result(analysis, required_fields)
        except json.JSONDecodeError:
            logger.warning("[梅花易数] JSON解析失败，尝试文本解析")
            analysis = self._parse_text_to_meihua_fields(cleaned_content, required_fields)

        logger.info(f"[梅花易数] AI分析完成，生成字段: {list(analysis.keys())}")

        return {
            'analysis': analysis,
            'usage': usage
        }

    def _build_meihua_prompt(
            self,
            input_data: Dict[str, Any],
            hexagram_data: Dict[str, Any]
    ) -> str:
        """
        构建梅花易数分析提示词

        Args:
            input_data: 输入数据
            hexagram_data: 卦象数据

        Returns:
            提示词字符串
        """
        parts = []

        question = input_data.get('question', '')
        if question:
            parts.append(f"所问之事：{question}")

        method = input_data.get('method', '')
        if method:
            method_names = {
                'time': '时间起卦',
                'number': '数字起卦',
                'direction': '方位起卦',
                'text': '测字起卦',
                'copper_coin': '铜钱摇卦',
                'stroke': '笔画起卦'
            }
            parts.append(f"起卦方式：{method_names.get(method, method)}")

        base = hexagram_data.get('base', hexagram_data.get('hexagram', {}))
        if base:
            parts.append(f"\n本卦：{base.get('name', base.get('gua_name', '未知卦'))}")
            if 'upper_name' in base and 'lower_name' in base:
                parts.append(f"  上卦：{base['upper_name']}({base.get('upper_nature', '')})")
                parts.append(f"  下卦：{base['lower_name']}({base.get('lower_nature', '')})")
            if 'gua_ci' in base:
                parts.append(f"  卦辞：{base['gua_ci']}")
            if 'description' in base:
                parts.append(f"  卦义：{base['description']}")

            changing_yao = base.get('changing_yao', 0)
            if changing_yao:
                parts.append(f"  动爻：第{changing_yao}爻")
                if 'changing_yao_text' in base:
                    parts.append(f"  爻辞：{base['changing_yao_text']}")

        hu = hexagram_data.get('hu', {})
        if hu and hu.get('name'):
            parts.append(f"\n互卦：{hu['name']}")
            if hu.get('description'):
                parts.append(f"  卦义：{hu['description']}")

        bian = hexagram_data.get('bian', {})
        if bian and bian.get('name'):
            parts.append(f"\n变卦：{bian['name']}")
            if bian.get('description'):
                parts.append(f"  卦义：{bian['description']}")
            if bian.get('judgment'):
                parts.append(f"  判断：{bian['judgment']}")

        overall = hexagram_data.get('overall_judgment', '')
        if overall:
            parts.append(f"\n综合吉凶判断：{overall}")

        return '\n'.join(parts)

    # ========== 大六壬 ==========
    def run_liuren_analysis(
            self,
            input_data: Dict[str, Any],
            liuren_data: Dict[str, Any] = None,
            task_id: str = None
    ) -> Dict[str, Any]:
        """
        执行大六壬AI分析完整流程（镜像 run_meihua_analysis）。
        """
        report_id = None
        start_time = datetime.now()

        try:
            # 缓存命中直接返回（P2-4：避免重复 API 调用）
            cached = get_cached_result('liuren', input_data, input_data.get('question', ''))
            if cached:
                logger.info(f"[大六壬] 缓存命中（hit_count={cached.get('_cache_hit_count', 1)}），跳过 API 调用")
                return {
                    'success': True,
                    'report_id': None,
                    'ai_analysis': cached,
                    'liuren_data': liuren_data or {},
                    'token_usage': 0,
                    'elapsed_seconds': (datetime.now() - start_time).total_seconds(),
                    'from_cache': True,
                }

            logger.info("[大六壬] ======== 开始大六壬AI分析流程 ========")
            logger.info(f"[大六壬] 所问之事: {input_data.get('question', '未指定')}, task_id={task_id}")

            if not self.validator.validate_liuren_input(input_data):
                errors = self.validator.get_errors()
                error_msg = f"输入数据验证失败: {'; '.join(errors)}"
                logger.error(f"[大六壬] {error_msg}")
                raise DataValidationError(error_msg)

            report_id = self.storage.create_pending_report('liuren', input_data)
            logger.info(f"[大六壬] 创建待处理报告，ID: {report_id}")

            self.storage.add_log(report_id, 'INFO', '大六壬分析流程开始', {
                'method': input_data.get('method', 'unknown'),
                'question': input_data.get('question', '')
            })

            if liuren_data is None:
                liuren_data = {}

            ai_result = self._call_agnes_for_liuren(input_data, liuren_data)

            token_usage = ai_result.get('usage', {}).get('total_tokens', 0)
            ai_analysis = ai_result.get('analysis', {})

            self.storage.add_log(report_id, 'INFO', 'AI分析完成', {
                'token_usage': token_usage,
                'analysis_fields': list(ai_analysis.keys())
            })

            if not self.validator.validate_ai_analysis_result(ai_analysis, 'liuren'):
                warnings = self.validator.get_warnings()
                if warnings:
                    logger.warning(f"[大六壬] AI结果有警告: {'; '.join(warnings)}")
                    self.storage.add_log(report_id, 'WARNING', 'AI结果验证有警告', {
                        'warnings': warnings
                    })

            self.storage.update_report_result(
                report_id=report_id,
                chart_data=liuren_data,
                ai_analysis=ai_analysis,
                ai_model=self.agnes_client.model,
                token_usage=token_usage
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[大六壬] 流程完成，耗时: {elapsed:.2f}秒，报告ID: {report_id}")
            logger.info("[大六壬] ======================================")

            # 写入 AI 缓存（P2-4：缓存键含 question 字段，不同问题不命中）
            try:
                save_to_cache('liuren', input_data, input_data.get('question', ''), ai_analysis)
            except Exception as e:
                logger.debug(f"[大六壬] 写入缓存失败（忽略）: {e}")

            return {
                'success': True,
                'report_id': report_id,
                'ai_analysis': ai_analysis,
                'liuren_data': liuren_data,
                'token_usage': token_usage,
                'elapsed_seconds': elapsed
            }

        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            logger.error(f"[大六壬] {error_msg}")
            logger.error(traceback.format_exc())
            if report_id:
                try:
                    self.storage.update_report_status(report_id, 'failed', error_msg)
                    self.storage.add_log(report_id, 'ERROR', '分析失败', {
                        'error_type': type(e).__name__,
                        'error': str(e)
                    })
                except Exception:
                    pass
            return self._build_error_result(report_id, type(e).__name__, error_msg, start_time)

    def _call_agnes_for_liuren(
            self,
            input_data: Dict[str, Any],
            liuren_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用AGNES模型进行大六壬分析。
        """
        logger.info("[大六壬] 构建AI分析请求...")

        prompt = self._build_liuren_prompt(input_data, liuren_data)

        system_prompt = (
            "你是一位精研大六壬（六壬神课）的术数宗师，深明天地盘、四课、三传、十二天将、神煞格局与九宗门取用之法，断课如神、理象合一。\n"
            "你将收到一份已经程序起出的六壬课体（日干支、月将、占时、天盘、四课、三传、十二天将、神煞）。请据此做专业、深入、针对『所问之事』的占断，严禁套话。\n"
            "\n"
            "分析铁律：\n"
            "1. 必须以『日干（或类神）为彼我之分』：日干为求测者/我方，支辰为所占之事/对方/环境；\n"
            "2. 四课论『明暗、远近、亲疏』：第一课干上神、第二课干阴、第三课支上、第四课支阴，逐一讲明生克与类象；\n"
            "3. 三传论『初、中、末』之事之始、中、终：说明进退连茹、比用、遥克等取传之理与事之发展；\n"
            "4. 天将论『阴阳、善恶』：贵人、螣蛇、朱雀等十二将之属性与所乘之神，判断吉凶之由；\n"
            "5. 神煞论『生克之外的特殊信号』：如驿马、天马、德合、墓绝等，指出关键影响；\n"
            "6. 针对『所问之事』给出明确判断（成/不成、速/迟、吉/凶）与可操作的趋避建议；\n"
            "7. 用词审慎，避免绝对化；每条分析都要引用具体课传、天将或神煞作为依据。\n"
            "\n"
            "输出格式要求：严格用JSON格式输出，不要包含任何额外的解释或说明文字，也不要使用 Markdown 代码块。\n"
            "JSON必须包含以下字段（数组类字段 5-8 条，每条 80-150 字，须引课体依据并给可操作建议）：\n"
            "- ke_overview（课体总览：课名、占类、整体气象与吉凶基调）\n"
            "- si_ke_analysis（四课精解：干支四课生克与类象，彼我态势）\n"
            "- san_chuan_analysis（三传推演：初传发端、中传过程、末传归宿，事之始终）\n"
            "- tian_jiang_analysis（天将神煞：十二将所乘之神、关键神煞之吉凶含义）\n"
            "- final_verdict（总结判断与建议：对所问之事的总体定论、一句断语与趋避要点）\n"
            "请深入、专业、精准，让占者得到真正有用的指引。"
        )

        required_fields = [
            'ke_overview', 'si_ke_analysis', 'san_chuan_analysis',
            'tian_jiang_analysis', 'final_verdict'
        ]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        logger.info("[大六壬] 调用AGNES AI模型进行分析...")
        result = self.agnes_client.chat_completion(
            messages, temperature=0.4, max_tokens=2048)

        content = result.get('content', '')
        usage = result.get('usage', {})

        cleaned_content = self.agnes_client._clean_json_response(content)

        import json
        try:
            analysis = json.loads(cleaned_content)
            analysis = self.agnes_client._validate_json_result(analysis, required_fields)
        except json.JSONDecodeError:
            logger.warning("[大六壬] JSON解析失败，尝试文本解析")
            analysis = self._parse_text_to_liuren_fields(cleaned_content, required_fields)

        logger.info(f"[大六壬] AI分析完成，生成字段: {list(analysis.keys())}")

        return {
            'analysis': analysis,
            'usage': usage
        }

    def _build_liuren_prompt(
            self,
            input_data: Dict[str, Any],
            liuren_data: Dict[str, Any]
    ) -> str:
        """
        构建大六壬分析提示词。
        """
        parts = []

        question = liuren_data.get('question', input_data.get('question', ''))
        if question:
            parts.append(f"所问之事：{question}")

        method_name = liuren_data.get('method_name', '')
        if method_name:
            parts.append(f"起课方式（取用法）：{method_name}")

        time = liuren_data.get('time', '')
        if time:
            parts.append(f"占问时间：{time}")

        ri_gan = liuren_data.get('ri_gan', '')
        ri_zhi = liuren_data.get('ri_zhi', '')
        ri_gan_wx = liuren_data.get('ri_gan_wx', '')
        if ri_gan and ri_zhi:
            parts.append(f"日干支：{ri_gan}{ri_zhi}（日干五行：{ri_gan_wx}）")

        yue_jiang = liuren_data.get('yue_jiang', '')
        if yue_jiang:
            parts.append(f"月将：{yue_jiang}")

        zhan_shi = liuren_data.get('zhan_shi', '')
        if zhan_shi:
            parts.append(f"占时：{zhan_shi}")

        tian_pan = liuren_data.get('tian_pan', {})
        if tian_pan:
            tp_pairs = '，'.join(f"{k}上见{v}" for k, v in tian_pan.items())
            parts.append(f"天盘（月将加占时）：{tp_pairs}")

        si_ke = liuren_data.get('si_ke', {})
        if si_ke:
            parts.append(
                f"四课：第一课干上 {si_ke.get('gan_shang','')}；"
                f"第二课干阴 {si_ke.get('gan_yin','')}；"
                f"第三课支上 {si_ke.get('zhi_shang','')}；"
                f"第四课支阴 {si_ke.get('zhi_yin','')}"
            )

        san_chuan = liuren_data.get('san_chuan', {})
        if san_chuan:
            parts.append(
                f"三传：初传 {san_chuan.get('chu','')} → "
                f"中传 {san_chuan.get('zhong','')} → "
                f"末传 {san_chuan.get('mo','')}（取用法：{san_chuan.get('gate','')}）"
            )

        tian_jiang = liuren_data.get('tian_jiang', [])
        if tian_jiang:
            tj = '，'.join(tian_jiang)
            parts.append(f"十二天将：{tj}")

        shen_sha = liuren_data.get('shen_sha', {})
        if shen_sha:
            ss = '；'.join(f"{k}：{v}" for k, v in shen_sha.items())
            parts.append(f"神煞：{ss}")

        parts.append("请综合四课生克、三传进退、天将阴阳、神煞吉凶，针对所问之事做专业解读。")
        return '\n'.join(parts)

    def _parse_text_to_liuren_fields(self, content: str, required_fields: List[str]) -> Dict[str, Any]:
        """
        解析非JSON格式的大六壬分析文本。
        """
        section_keywords = {
            'ke_overview': ['课体总览', '课体', '总览', '概况'],
            'si_ke_analysis': ['四课', '四课精解', '课义'],
            'san_chuan_analysis': ['三传', '三传推演', '传变'],
            'tian_jiang_analysis': ['天将', '神煞', '将神'],
            'final_verdict': ['总结', '结论', '判断', '建议']
        }

        result = {}
        for field in required_fields:
            keywords = section_keywords.get(field, [])
            found = []
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if any(kw in line for kw in keywords):
                    found.append(line)
            if found:
                result[field] = found[:5]
            else:
                result[field] = [content[:200]] if field != 'final_verdict' else content[:200]

        if 'final_verdict' not in result or not result.get('final_verdict'):
            result['final_verdict'] = content[:200]
        return result

    def _parse_text_to_meihua_fields(self, content: str, required_fields: List[str]) -> Dict[str, Any]:
        """
        解析非JSON格式的梅花易数分析文本

        Args:
            content: 文本内容
            required_fields: 必填字段

        Returns:
            解析后的字典
        """
        section_keywords = {
            'gua_overview': ['卦象概述', '卦象解读', '卦义', '卦意'],
            'situation_analysis': ['事态分析', '现状分析', '情况分析', '形势'],
            'good_omens': ['吉兆', '机遇', '好运', '有利', '吉'],
            'bad_omens': ['凶兆', '隐患', '风险', '不利', '凶'],
            'action_advice': ['行动建议', '建议', '怎么做', '如何', '对策'],
            'final_verdict': ['总结', '结论', '判断', '最终']
        }

        result = {}
        for field in required_fields:
            result[field] = [] if field != 'final_verdict' else ''

        current_field = None

        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue

            matched = False
            for field, keywords in section_keywords.items():
                if field in required_fields:
                    for kw in keywords:
                        if kw in line and len(line) < 30:
                            current_field = field
                            matched = True
                            break
                if matched:
                    break

            if matched:
                continue

            if current_field and current_field in required_fields:
                if current_field == 'final_verdict':
                    if not result[current_field]:
                        result[current_field] = line
                else:
                    if line[0] in ['•', '·', '-', '●', '★', '◆', '1.', '2.', '3.', '4.', '5.', '（', '(']:
                        result[current_field].append(line.lstrip('•·-●★◆1234567890.（() '))
                    elif len(line) > 10:
                        result[current_field].append(line)

        if 'final_verdict' in required_fields and not result.get('final_verdict'):
            result['final_verdict'] = '需结合实际情况综合判断'

        return result

    # ========== 综合建议（融合 八字 + 梅花易数 + 大六壬） ==========
    def run_comprehensive_analysis(
            self,
            parts: Dict[str, Any],
            meta: Dict[str, Any] = None,
            task_id: str = None
    ) -> Dict[str, Any]:
        """
        融合三种术数结论，生成统筹的【综合建议】。

        Args:
            parts: {'bazi': <八字AI分析>, 'meihua': <梅花AI分析>, 'liuren': <六壬AI分析>}
            meta:  补充信息（姓名/性别/所问之事/各方课体摘要）
            task_id: 任务ID（可选）

        Returns:
            {'success': bool, 'ai_analysis': dict, ...}
        """
        start_time = datetime.now()
        try:
            logger.info("[综合建议] ======== 开始融合三方结论、生成综合建议 ========")
            if not parts or not any(parts.get(k) for k in ('bazi', 'meihua', 'liuren')):
                raise AnalysisPipelineError("缺少可用的术数分析结论，无法生成综合建议")

            # 缓存命中直接返回（P2-4：缓存键 = question + 三方 AI 摘要哈希，避免重复综合）
            cache_input = {
                'question': (meta or {}).get('question', ''),
                'bazi': self._digest_for_cache(parts.get('bazi')),
                'meihua': self._digest_for_cache(parts.get('meihua')),
                'liuren': self._digest_for_cache(parts.get('liuren')),
            }
            cached = get_cached_result('comprehensive', cache_input,
                                       (meta or {}).get('question', ''))
            if cached:
                logger.info(f"[综合建议] 缓存命中（hit_count={cached.get('_cache_hit_count', 1)}），跳过 API 调用")
                return {
                    'success': True,
                    'ai_analysis': cached,
                    'token_usage': 0,
                    'elapsed_seconds': (datetime.now() - start_time).total_seconds(),
                    'from_cache': True,
                }

            ai_result = self._call_agnes_for_comprehensive(parts, meta or {})
            ai_analysis = ai_result.get('analysis', {})
            token_usage = ai_result.get('usage', {}).get('total_tokens', 0)

            # 写入缓存（仅综合的 ai_analysis，键含 question）
            try:
                save_to_cache('comprehensive', cache_input,
                              (meta or {}).get('question', ''), ai_analysis)
            except Exception as e:
                logger.debug(f"[综合建议] 写入缓存失败（忽略）: {e}")

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[综合建议] 完成，耗时: {elapsed:.2f}秒")
            return {
                'success': True,
                'ai_analysis': ai_analysis,
                'token_usage': token_usage,
                'elapsed_seconds': elapsed,
            }
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            logger.error(f"[综合建议] 失败: {error_msg}")
            logger.error(traceback.format_exc())
            return self._build_error_result(None, type(e).__name__, error_msg, start_time)

    @staticmethod
    def _digest_for_cache(obj: Any) -> str:
        """生成对象摘要（用于综合缓存键）：若为 dict 则取 final_verdict 与关键字段，否则取 str。"""
        if not obj:
            return ''
        if isinstance(obj, dict):
            keys = ('final_verdict', 'synthesis', 'personality')
            parts = [str(obj.get(k, ''))[:80] for k in keys if obj.get(k)]
            return ' | '.join(parts) if parts else str(sorted(obj.keys()))[:80]
        return str(obj)[:80]

    def _call_agnes_for_comprehensive(
            self,
            parts: Dict[str, Any],
            meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用 AGNES 生成融合综合建议。"""
        logger.info("[综合建议] 构建融合分析请求...")

        prompt = self._build_comprehensive_prompt(parts, meta)

        system_prompt = (
            "你是一位贯通八字命理、梅花易数、大六壬三家之学的宗师级顾问（龙虎山大师兄）。\n"
            "用户就同一人生课题，分别用八字（定命局根基）、梅花易数（测当下所问之事的机缘）、大六壬（断具体所问之事的时空吉凶）三种术数进行了推算。\n"
            "现在你将三份结论汇总，给出一份统筹、精准、可落地的【综合建议】。\n"
            "\n"
            "综合建议铁律：\n"
            "1. 先逐家概述三方结论要点（不重复全文，提炼关键判断与定论）；\n"
            "2. 做【矛盾与印证】校验：指出三家一致之处（互为印证、可信度高）与分歧之处（说明可能原因，如尺度不同、所问侧重不同），并给出调和口径；\n"
            "3. 给出【综合定论】：对用户当前最关心的课题，形成一段权威结论；\n"
            "4. 给出【统一趋吉避凶方案】：整合三家可操作建议，去重、排序、落地，覆盖事业/情感/健康/修身/时机五个维度，每条 80-150 字且具体可操作；\n"
            "5. 指出【关键时机与禁忌】：什么时间窗口有利、什么情形宜避；\n"
            "6. 语气审慎专业，避免绝对化与恐吓；文末加一句负责任的免责说明（命理咨询仅供参考，重大决策须理性判断）。\n"
            "\n"
            "输出格式要求：严格用JSON格式输出，不要包含任何额外的解释或说明文字，也不要使用 Markdown 代码块。\n"
            "JSON必须包含以下字段（数组类字段 4-6 条，每条 80-150 字）：\n"
            "- tri_method_overview（三方概览：八字/梅花/六壬 各自的核心结论要点）\n"
            "- consistency_check（矛盾与印证：一致与分歧及调和）\n"
            "- synthesis（综合定论：对用户课题的统筹结论）\n"
            "- unified_plan（统一趋吉避凶方案：整合后的可执行建议）\n"
            "- key_timing（关键时机与禁忌）\n"
            "- disclaimer（免责说明，字符串）\n"
            "请务必深入、专业、精准，让内容对用户真正有用。"
        )

        required_fields = [
            'tri_method_overview', 'consistency_check', 'synthesis',
            'unified_plan', 'key_timing', 'disclaimer'
        ]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        logger.info("[综合建议] 调用AGNES AI模型...")
        result = self.agnes_client.chat_completion(
            messages, temperature=0.4, max_tokens=2048)

        content = result.get('content', '')
        usage = result.get('usage', {})

        cleaned_content = self.agnes_client._clean_json_response(content)

        try:
            analysis = json.loads(cleaned_content)
            analysis = self.agnes_client._validate_json_result(analysis, required_fields)
        except json.JSONDecodeError:
            logger.warning("[综合建议] JSON解析失败，尝试文本解析")
            analysis = self._parse_text_to_comprehensive_fields(cleaned_content, required_fields)

        logger.info(f"[综合建议] 生成字段: {list(analysis.keys())}")
        return {'analysis': analysis, 'usage': usage}

    def _build_comprehensive_prompt(self, parts: Dict[str, Any], meta: Dict[str, Any]) -> str:
        """汇总三方结论，拼装给模型的融合提示词。"""
        lines = []
        meta = meta or {}

        lines.append("【求测者信息】")
        lines.append(f"姓名：{meta.get('name', '')}　性别：{meta.get('gender', '')}")
        if meta.get('question'):
            lines.append(f"所关心 / 所问之事：{meta.get('question')}")
        if meta.get('bazi_summary'):
            lines.append(f"八字四柱：{meta.get('bazi_summary')}")
        if meta.get('meihua_summary'):
            lines.append(f"梅花卦象：{meta.get('meihua_summary')}")
        if meta.get('liuren_summary'):
            lines.append(f"六壬课体：{meta.get('liuren_summary')}")

        bazi = parts.get('bazi') or {}
        if bazi:
            lines.append("\n【八字分析结论】")
            for k in ['personality', 'career', 'marriage', 'health',
                      'pattern_analysis', 'wuxing_balance', 'shishen_analysis',
                      'improvement_plan', 'suggestions']:
                v = bazi.get(k)
                if v:
                    lines.append(f"- {k}: " + (json.dumps(v, ensure_ascii=False)
                                               if isinstance(v, list) else str(v)))

        meihua = parts.get('meihua') or {}
        if meihua:
            lines.append("\n【梅花易数分析结论】")
            for k in ['gua_overview', 'situation_analysis', 'good_omens',
                      'bad_omens', 'action_advice', 'final_verdict']:
                v = meihua.get(k)
                if v:
                    lines.append(f"- {k}: " + (json.dumps(v, ensure_ascii=False)
                                               if isinstance(v, list) else str(v)))

        liuren = parts.get('liuren') or {}
        if liuren:
            lines.append("\n【大六壬分析结论】")
            for k in ['ke_overview', 'si_ke_analysis', 'san_chuan_analysis',
                      'tian_jiang_analysis', 'final_verdict']:
                v = liuren.get(k)
                if v:
                    lines.append(f"- {k}: " + (json.dumps(v, ensure_ascii=False)
                                               if isinstance(v, list) else str(v)))

        lines.append("\n请综合以上三方结论，给出统筹、精准、可落地的【综合建议】。")
        return '\n'.join(lines)

    def _parse_text_to_comprehensive_fields(self, content: str, required_fields: List[str]) -> Dict[str, Any]:
        """解析非JSON格式的综合建议文本。"""
        section_keywords = {
            'tri_method_overview': ['三方概览', '概览', '概述'],
            'consistency_check': ['矛盾', '印证', '一致', '分歧'],
            'synthesis': ['综合定论', '定论', '结论'],
            'unified_plan': ['统一方案', '趋吉避凶', '改善', '方案'],
            'key_timing': ['时机', '禁忌', '关键'],
            'disclaimer': ['免责', '声明', '参考'],
        }
        result = {}
        for field in required_fields:
            if field == 'disclaimer':
                result[field] = ''
                continue
            result[field] = []
        current_field = None
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            matched = False
            for field, keywords in section_keywords.items():
                if field in required_fields and field != 'disclaimer':
                    for kw in keywords:
                        if kw in line and len(line) < 30:
                            current_field = field
                            matched = True
                            break
                if matched:
                    break
            if matched:
                continue
            if current_field and current_field in result:
                if line and line[0] in ['•', '·', '-', '●', '★', '◆', '1.', '2.', '3.', '4.', '5.', '（', '(']:
                    result[current_field].append(line.lstrip('•·-●★◆1234567890.（() '))
                elif len(line) > 10:
                    result[current_field].append(line)
        for field in required_fields:
            if field == 'disclaimer':
                if not result[field]:
                    result[field] = '命理咨询仅供参考，重大决策须结合现实理性判断。'
            elif not result[field]:
                result[field] = ['内容解析异常，请重新生成综合建议。']
        return result

    # ==================== 通用方法 ====================

    def _build_error_result(
            self,
            report_id: Optional[int],
            error_type: str,
            error_message: str,
            start_time: datetime
    ) -> Dict[str, Any]:
        """
        构建错误结果

        Args:
            report_id: 报告ID
            error_type: 错误类型
            error_message: 错误信息
            start_time: 开始时间

        Returns:
            错误结果字典
        """
        elapsed = (datetime.now() - start_time).total_seconds()
        return {
            'success': False,
            'report_id': report_id,
            'error_type': error_type,
            'error_message': error_message,
            'elapsed_seconds': elapsed
        }

    def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        """
        获取分析报告

        Args:
            report_id: 报告ID

        Returns:
            报告字典
        """
        return self.storage.get_report_by_id(report_id)

    def test_database_connection(self) -> bool:
        """
        测试数据库连接

        Returns:
            是否连接成功
        """
        return self.storage.test_connection()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        try:
            total = self.storage.get_report_count()
            bazi_count = self.storage.get_report_count('bazi')
            meihua_count = self.storage.get_report_count('meihua')

            return {
                'total_reports': total,
                'bazi_reports': bazi_count,
                'meihua_reports': meihua_count,
                'database_ok': self.storage.test_connection()
            }
        except Exception as e:
            logger.error(f"[分析流程] 获取统计信息失败: {e}")
            return {'error': str(e)}


_pipeline_instance = None


def get_analysis_pipeline(config_path: str = None) -> AnalysisPipeline:
    """
    获取默认的分析流程实例（单例模式）

    Args:
        config_path: 配置文件路径

    Returns:
        AnalysisPipeline实例
    """
    global _pipeline_instance
    if _pipeline_instance is None or config_path:
        _pipeline_instance = AnalysisPipeline(config_path)
    return _pipeline_instance
