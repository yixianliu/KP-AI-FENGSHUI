"""
数据分析主流程模块
整合数据验证、AI模型调用、结果存储的完整流程
包含完善的错误处理和日志记录机制
"""
import os
import sys
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from api.ernie_client import (
    ErnieClient, ErnieClientError, ErnieRequestError,
    ErnieTimeoutError, ErnieResponseError
)
from core.data_validator import DataValidator, DataValidationError
from core.analysis_storage import (
    AnalysisStorage, AnalysisStorageError,
    DatabaseConnectionError, DatabaseQueryError
)
from core.data_integration import DataIntegrator
from core.knowledge_base import KnowledgeBase


def setup_logger(log_dir: str = None, log_level: int = logging.INFO) -> logging.Logger:
    """
    设置日志系统

    Args:
        log_dir: 日志目录，默认 logs/
        log_level: 日志级别

    Returns:
        配置好的logger
    """
    if log_dir is None:
        log_dir = project_root / 'logs'
    log_dir = Path(log_dir)
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

        try:
            self.validator = DataValidator()
            self.storage = AnalysisStorage(config_path)
            self.ernie_client = ErnieClient(verify_ssl=False)
            logger.info("[分析流程] 所有模块初始化成功")
        except Exception as e:
            logger.error(f"[分析流程] 初始化失败: {e}")
            logger.error(traceback.format_exc())
            raise AnalysisPipelineError(f"分析流程初始化失败: {e}") from e

    # ==================== 八字分析流程 ====================

    def run_bazi_analysis(
        self,
        input_data: Dict[str, Any],
        chart_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        执行八字AI分析完整流程

        Args:
            input_data: 输入数据字典
            chart_data: 预计算的排盘数据（可选）

        Returns:
            分析结果字典，包含 report_id, ai_analysis 等
        """
        report_id = None
        start_time = datetime.now()

        try:
            logger.info("[八字分析] ========== 开始八字AI分析流程 ==========")
            logger.info(f"[八字分析] 输入数据: 姓名={input_data.get('name', '未知')}, "
                        f"性别={input_data.get('gender', '未知')}")

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

            ai_result = self._call_ernie_for_bazi(input_data, chart_data)

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
                ai_model=self.ernie_client.model,
                token_usage=token_usage
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[八字分析] 流程完成，耗时: {elapsed:.2f}秒，报告ID: {report_id}")
            logger.info("[八字分析] ========================================")

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

        except ErnieTimeoutError as e:
            error_msg = f"AI模型请求超时: {e}"
            logger.error(f"[八字分析] {error_msg}")
            if report_id:
                self.storage.update_report_status(report_id, 'failed', error_msg)
                self.storage.add_log(report_id, 'ERROR', 'AI请求超时', {'error': str(e)})
            return self._build_error_result(report_id, 'ai_timeout', error_msg, start_time)

        except ErnieRequestError as e:
            error_msg = f"AI模型请求失败: {e}"
            logger.error(f"[八字分析] {error_msg}")
            if report_id:
                self.storage.update_report_status(report_id, 'failed', error_msg)
                self.storage.add_log(report_id, 'ERROR', 'AI请求失败', {'error': str(e)})
            return self._build_error_result(report_id, 'ai_request_error', error_msg, start_time)

        except ErnieResponseError as e:
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

    def _call_ernie_for_bazi(
        self,
        input_data: Dict[str, Any],
        chart_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用ERNIE模型进行八字分析

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
            "你是一位专业的命理大师，精通传统八字命理、阴阳五行、十神、十二长生、神煞、纳音、格局等专业知识。\n"
            "请基于用户提供的完整八字信息进行深入、细致、专业的分析。\n"
            "\n"
            "分析原则：\n"
            "1. 必须基于提供的八字数据进行分析，所有结论要有命理依据，不可凭空推断；\n"
            "2. 兼顾五行平衡、十神力量、月令影响、通根强弱等多角度综合分析；\n"
            "3. 使用'可能'、'较为'、'相对'等谨慎表述，避免绝对化结论；\n"
            "4. 分析要深入细致，涵盖性格、事业、婚姻、健康等多个维度；\n"
            "5. 考虑大运走势对命运的影响；\n"
            "6. 参考神煞、纳音、空亡等命理特征。\n"
            "\n"
            "输出格式要求：严格用JSON格式输出，不要包含任何额外的解释或说明文字。\n"
            "JSON必须包含以下字段：\n"
            "- personality（性格特质，字符串数组，5-8条，每条50-100字）\n"
            "- career（事业财运，字符串数组，5-8条，每条50-100字）\n"
            "- marriage（婚姻感情，字符串数组，5-8条，每条50-100字）\n"
            "- health（健康注意，字符串数组，5-8条，每条50-100字）\n"
            "- suggestions（综合建议，字符串数组，5-8条，每条50-100字）\n"
            "- pattern_analysis（格局分析，字符串数组，3-5条，每条50-100字）\n"
            "- wuxing_balance（五行平衡分析，字符串数组，3-5条，每条50-100字）\n"
            "- shishen_analysis（十神分析，字符串数组，3-5条，每条50-100字）\n"
            "\n"
            "请结合命理知识进行深度分析，不要泛泛而谈，每条分析要有具体的命理依据。"
        )

        required_fields = ['personality', 'career', 'marriage', 'health', 'suggestions',
                          'pattern_analysis', 'wuxing_balance', 'shishen_analysis']

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        logger.info("[八字分析] 调用ERNIE AI模型进行分析...")
        result = self.ernie_client.chat_completion(messages, temperature=0.3, max_tokens=4096)

        content = result.get('content', '')
        usage = result.get('usage', {})

        cleaned_content = self.ernie_client._clean_json_response(content)

        import json
        try:
            analysis = json.loads(cleaned_content)
            analysis = self.ernie_client._validate_json_result(analysis, required_fields)
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

        if 'city' in input_data and input_data['city']:
            parts.append(f"出生地：{input_data['city']}")

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
            'shishen_analysis': ['十神', '用神', '忌神']
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
        hexagram_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        执行梅花易数AI分析完整流程

        Args:
            input_data: 输入数据字典
            hexagram_data: 预计算的卦象数据（可选）

        Returns:
            分析结果字典
        """
        report_id = None
        start_time = datetime.now()

        try:
            logger.info("[梅花易数] ======== 开始梅花易数AI分析流程 ========")
            logger.info(f"[梅花易数] 所问之事: {input_data.get('question', '未指定')}")

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

            ai_result = self._call_ernie_for_meihua(input_data, hexagram_data)

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
                ai_model=self.ernie_client.model,
                token_usage=token_usage
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[梅花易数] 流程完成，耗时: {elapsed:.2f}秒，报告ID: {report_id}")
            logger.info("[梅花易数] ======================================")

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

    def _call_ernie_for_meihua(
        self,
        input_data: Dict[str, Any],
        hexagram_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用ERNIE模型进行梅花易数分析

        Args:
            input_data: 输入数据
            hexagram_data: 卦象数据

        Returns:
            包含 analysis 和 usage 的结果字典
        """
        logger.info("[梅花易数] 构建AI分析请求...")

        prompt = self._build_meihua_prompt(input_data, hexagram_data)

        system_prompt = (
            "你是一位精通梅花易数的专业占卜大师，深谙64卦卦辞爻辞、体用生克、互变错综等解卦之道。"
            "请基于用户提供的卦象信息进行专业深入的解读和分析。"
            "输出格式要求：严格用JSON格式输出，不要包含任何额外的解释或说明文字。"
            "JSON必须包含以下字段："
            "gua_overview（卦象概述，字符串数组，3-5条）、"
            "situation_analysis（事态分析，字符串数组，3-5条）、"
            "good_omens（吉兆机遇，字符串数组，3-5条）、"
            "bad_omens（凶兆隐患，字符串数组，3-5条）、"
            "action_advice（行动建议，字符串数组，3-5条）、"
            "final_verdict（总结判断，字符串）。"
            "请结合卦辞、爻辞、体用生克进行深度分析，针对所问之事给出具体实用的建议。"
        )

        required_fields = [
            'gua_overview', 'situation_analysis', 'good_omens',
            'bad_omens', 'action_advice', 'final_verdict'
        ]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        logger.info("[梅花易数] 调用ERNIE AI模型进行分析...")
        result = self.ernie_client.chat_completion(messages, temperature=0.5, max_tokens=2048)

        content = result.get('content', '')
        usage = result.get('usage', {})

        cleaned_content = self.ernie_client._clean_json_response(content)

        import json
        try:
            analysis = json.loads(cleaned_content)
            analysis = self.ernie_client._validate_json_result(analysis, required_fields)
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
                'text': '测字起卦'
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
