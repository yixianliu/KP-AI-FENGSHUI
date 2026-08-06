"""
数据验证模块
负责验证输入数据的完整性、格式正确性和业务规则约束
"""
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """数据验证异常基类"""
    pass


class DataValidator:
    """
    数据验证器
    提供多种数据验证方法，确保输入数据完整、格式正确
    """

    TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    GAN_ZHI_PAIRS = [
        '甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉',
        '甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未',
        '甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳',
        '甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯',
        '甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑',
        '甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥'
    ]

    GENDER_OPTIONS = ['男', '女']
    PAN_TYPES = ['八字', '梅花易数']

    def __init__(self):
        """初始化数据验证器"""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def reset(self):
        """重置验证状态"""
        self.errors = []
        self.warnings = []

    def add_error(self, field: str, message: str):
        """
        添加错误信息

        Args:
            field: 字段名
            message: 错误信息
        """
        error_msg = f"[错误] {field}: {message}"
        self.errors.append(error_msg)
        logger.error(error_msg)

    def add_warning(self, field: str, message: str):
        """
        添加警告信息

        Args:
            field: 字段名
            message: 警告信息
        """
        warning_msg = f"[警告] {field}: {message}"
        self.warnings.append(warning_msg)
        logger.warning(warning_msg)

    def validate_required(self, data: Dict[str, Any], field: str, field_name: str = None) -> bool:
        """
        验证必填字段

        Args:
            data: 数据字典
            field: 字段名
            field_name: 字段显示名称

        Returns:
            是否通过验证
        """
        display_name = field_name or field
        if field not in data:
            self.add_error(display_name, "字段缺失")
            return False
        value = data[field]
        if value is None:
            self.add_error(display_name, "值不能为None")
            return False
        if isinstance(value, str) and value.strip() == '':
            self.add_error(display_name, "值不能为空字符串")
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            self.add_error(display_name, "值不能为空")
            return False
        return True

    def validate_string_length(
        self,
        value: str,
        field_name: str,
        min_len: int = 0,
        max_len: int = None
    ) -> bool:
        """
        验证字符串长度

        Args:
            value: 字符串值
            field_name: 字段显示名称
            min_len: 最小长度
            max_len: 最大长度

        Returns:
            是否通过验证
        """
        if value is None:
            return True
        length = len(str(value))
        if length < min_len:
            self.add_error(field_name, f"长度不能少于{min_len}个字符")
            return False
        if max_len is not None and length > max_len:
            self.add_error(field_name, f"长度不能超过{max_len}个字符")
            return False
        return True

    def validate_integer(
        self,
        value: Any,
        field_name: str,
        min_val: int = None,
        max_val: int = None
    ) -> Tuple[bool, Optional[int]]:
        """
        验证整数

        Args:
            value: 值
            field_name: 字段名称
            min_val: 最小值
            max_val: 最大值

        Returns:
            (是否通过, 转换后的整数值)
        """
        try:
            int_val = int(value)
        except (ValueError, TypeError):
            self.add_error(field_name, "必须是整数")
            return False, None

        if min_val is not None and int_val < min_val:
            self.add_error(field_name, f"不能小于{min_val}")
            return False, int_val

        if max_val is not None and int_val > max_val:
            self.add_error(field_name, f"不能大于{max_val}")
            return False, int_val

        return True, int_val

    def validate_date(self, year: int, month: int, day: int, field_name: str = "日期") -> bool:
        """
        验证日期合法性

        Args:
            year: 年份
            month: 月份
            day: 日期
            field_name: 字段名称

        Returns:
            是否合法
        """
        try:
            datetime(year, month, day)
            return True
        except ValueError as e:
            self.add_error(field_name, f"日期不合法: {year}-{month:02d}-{day:02d}, {e}")
            return False

    def validate_time(self, hour: int, minute: int, field_name: str = "时间") -> bool:
        """
        验证时间合法性

        Args:
            hour: 小时
            minute: 分钟
            field_name: 字段名称

        Returns:
            是否合法
        """
        if hour < 0 or hour > 23:
            self.add_error(field_name, f"小时必须在0-23之间，当前值: {hour}")
            return False
        if minute < 0 or minute > 59:
            self.add_error(field_name, f"分钟必须在0-59之间，当前值: {minute}")
            return False
        return True

    def validate_gender(self, gender: str, field_name: str = "性别") -> bool:
        """
        验证性别

        Args:
            gender: 性别值
            field_name: 字段名称

        Returns:
            是否合法
        """
        if gender not in self.GENDER_OPTIONS:
            self.add_error(field_name, f"必须是{'/'.join(self.GENDER_OPTIONS)}之一，当前值: {gender}")
            return False
        return True

    def validate_pan_type(self, pan_type: str, field_name: str = "排盘类型") -> bool:
        """
        验证排盘类型

        Args:
            pan_type: 排盘类型
            field_name: 字段名称

        Returns:
            是否合法
        """
        if pan_type not in self.PAN_TYPES:
            self.add_error(field_name, f"必须是{'/'.join(self.PAN_TYPES)}之一，当前值: {pan_type}")
            return False
        return True

    def validate_ganzhi(self, ganzhi: str, field_name: str = "干支") -> bool:
        """
        验证干支组合合法性

        Args:
            ganzhi: 干支字符串
            field_name: 字段名称

        Returns:
            是否合法
        """
        if len(ganzhi) != 2:
            self.add_error(field_name, f"干支必须是2个字符，当前长度: {len(ganzhi)}")
            return False

        gan = ganzhi[0]
        zhi = ganzhi[1]

        if gan not in self.TIAN_GAN:
            self.add_error(field_name, f"天干'{gan}'不合法，必须是{'/'.join(self.TIAN_GAN)}之一")
            return False

        if zhi not in self.DI_ZHI:
            self.add_error(field_name, f"地支'{zhi}'不合法，必须是{'/'.join(self.DI_ZHI)}之一")
            return False

        if ganzhi not in self.GAN_ZHI_PAIRS:
            self.add_warning(field_name, f"干支组合'{ganzhi}'不是标准的60甲子组合")

        return True

    def validate_bazi_input(self, input_data: Dict[str, Any]) -> bool:
        """
        验证八字输入数据

        Args:
            input_data: 输入数据字典，需包含 name, gender, year, month, day, hour, minute, city

        Returns:
            是否验证通过
        """
        self.reset()
        logger.info("[数据验证] 开始验证八字输入数据")

        self.validate_required(input_data, 'name', '姓名')
        self.validate_required(input_data, 'gender', '性别')
        self.validate_required(input_data, 'year', '年份')
        self.validate_required(input_data, 'month', '月份')
        self.validate_required(input_data, 'day', '日期')
        self.validate_required(input_data, 'hour', '小时')
        self.validate_required(input_data, 'minute', '分钟')

        if 'name' in input_data and input_data['name']:
            self.validate_string_length(input_data['name'], '姓名', max_len=100)

        if 'gender' in input_data and input_data['gender']:
            self.validate_gender(input_data['gender'])

        year_valid, year_val = self.validate_integer(input_data.get('year'), '年份', min_val=1900, max_val=2100)
        month_valid, month_val = self.validate_integer(input_data.get('month'), '月份', min_val=1, max_val=12)
        day_valid, day_val = self.validate_integer(input_data.get('day'), '日期', min_val=1, max_val=31)

        if year_valid and month_valid and day_valid:
            self.validate_date(year_val, month_val, day_val, '出生日期')

        hour_valid, hour_val = self.validate_integer(input_data.get('hour'), '小时', min_val=0, max_val=23)
        minute_valid, minute_val = self.validate_integer(input_data.get('minute'), '分钟', min_val=0, max_val=59)

        if hour_valid and minute_valid:
            self.validate_time(hour_val, minute_val, '出生时间')

        loc = input_data.get('location') or input_data.get('city')
        if loc:
            self.validate_string_length(loc, '出生地', max_len=100)

        passed = len(self.errors) == 0
        if passed:
            logger.info("[数据验证] 八字输入数据验证通过")
        else:
            logger.error(f"[数据验证] 八字输入数据验证失败，共{len(self.errors)}个错误")

        return passed

    def validate_meihua_input(self, input_data: Dict[str, Any]) -> bool:
        """
        验证梅花易数输入数据

        Args:
            input_data: 输入数据字典

        Returns:
            是否验证通过
        """
        self.reset()
        logger.info("[数据验证] 开始验证梅花易数输入数据")

        method = input_data.get('method', '')
        if not method:
            self.add_error('起卦方式', '起卦方式不能为空')
            return False

        if method == 'time':
            self.validate_required(input_data, 'year', '年份')
            self.validate_required(input_data, 'month', '月份')
            self.validate_required(input_data, 'day', '日期')
            self.validate_required(input_data, 'hour', '小时')

            year_valid, year_val = self.validate_integer(input_data.get('year'), '年份', min_val=1900, max_val=2100)
            month_valid, month_val = self.validate_integer(input_data.get('month'), '月份', min_val=1, max_val=12)
            day_valid, day_val = self.validate_integer(input_data.get('day'), '日期', min_val=1, max_val=31)
            hour_valid, hour_val = self.validate_integer(input_data.get('hour'), '小时', min_val=0, max_val=23)

            if year_valid and month_valid and day_valid:
                self.validate_date(year_val, month_val, day_val, '起卦日期')

        elif method == 'number':
            self.validate_required(input_data, 'upper_num', '上卦数字')
            self.validate_required(input_data, 'lower_num', '下卦数字')
            self.validate_integer(input_data.get('upper_num'), '上卦数字', min_val=1)
            self.validate_integer(input_data.get('lower_num'), '下卦数字', min_val=1)

        elif method == 'text':
            self.validate_required(input_data, 'text', '测字文本')
            if input_data.get('text'):
                self.validate_string_length(input_data['text'], '测字文本', min_len=1, max_len=100)

        elif method == 'direction':
            self.validate_required(input_data, 'direction', '方位')
            direction = input_data.get('direction', '')
            valid_directions = ['正北方', '东北方', '正东方', '东南方',
                               '正南方', '西南方', '正西方', '西北方']
            if direction and direction not in valid_directions:
                self.add_error('方位', f"不支持的方位: {direction}")

        elif method == 'copper_coin':
            self.validate_required(input_data, 'six_lines', '六爻')
            six_lines = input_data.get('six_lines', [])
            if isinstance(six_lines, list):
                if len(six_lines) != 6:
                    self.add_error('六爻', f"六爻数量应为6，实际为{len(six_lines)}")
                else:
                    valid_yao = {'少阳', '老阴', '少阴', '老阳'}
                    for i, y in enumerate(six_lines, 1):
                        if y not in valid_yao:
                            self.add_error('六爻', f"第{i}爻取值无效: {y}")

        elif method == 'stroke':
            self.validate_required(input_data, 'char', '汉字')
            if input_data.get('char'):
                self.validate_string_length(input_data['char'], '汉字', min_len=1, max_len=4)
            self.validate_required(input_data, 'stroke_count', '笔画数')
            self.validate_integer(input_data.get('stroke_count'), '笔画数', min_val=1, max_val=81)

        else:
            self.add_error('起卦方式', f"不支持的起卦方式: {method}")

        if 'question' in input_data and input_data['question']:
            self.validate_string_length(input_data['question'], '所问之事', max_len=500)

        passed = len(self.errors) == 0
        if passed:
            logger.info("[数据验证] 梅花易数输入数据验证通过")
        else:
            logger.error(f"[数据验证] 梅花易数输入数据验证失败，共{len(self.errors)}个错误")

        return passed

    def validate_liuren_input(self, input_data: Dict[str, Any]) -> bool:
        """
        验证大六壬起课输入数据。

        Args:
            input_data: 输入数据字典

        Returns:
            是否验证通过
        """
        self.reset()
        logger.info("[数据验证] 开始验证大六壬输入数据")

        from core.liuren import GATE_METHODS
        ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

        method = input_data.get('method', '')
        if not method:
            self.add_error('起课方式', '起课方式不能为空')
            return False

        if method not in GATE_METHODS:
            self.add_error('起课方式', f"不支持的起课方式: {method}")
        else:
            self.validate_required(input_data, 'year', '年份')
            self.validate_required(input_data, 'month', '月份')
            self.validate_required(input_data, 'day', '日期')
            self.validate_required(input_data, 'hour', '小时')

            year_valid, year_val = self.validate_integer(
                input_data.get('year'), '年份', min_val=1900, max_val=2100)
            month_valid, month_val = self.validate_integer(
                input_data.get('month'), '月份', min_val=1, max_val=12)
            day_valid, day_val = self.validate_integer(
                input_data.get('day'), '日期', min_val=1, max_val=31)
            hour_valid, hour_val = self.validate_integer(
                input_data.get('hour'), '小时', min_val=0, max_val=23)

            if year_valid and month_valid and day_valid:
                self.validate_date(year_val, month_val, day_val, '起课日期')

            zhan_shi = input_data.get('zhan_shi')
            if zhan_shi and zhan_shi not in ZHI:
                self.add_error('占时', f"不支持的占时地支: {zhan_shi}")

        if 'question' in input_data and input_data['question']:
            self.validate_string_length(input_data['question'], '所问之事', max_len=500)

        passed = len(self.errors) == 0
        if passed:
            logger.info("[数据验证] 大六壬输入数据验证通过")
        else:
            logger.error(f"[数据验证] 大六壬输入数据验证失败，共{len(self.errors)}个错误")

        return passed

    def validate_bazi_result(self, bazi_data: Dict[str, Any]) -> bool:
        """
        验证八字排盘结果数据完整性

        Args:
            bazi_data: 八字排盘结果数据

        Returns:
            是否验证通过
        """
        self.reset()
        logger.info("[数据验证] 开始验证八字排盘结果数据")

        required_fields = ['year', 'month', 'day', 'hour', 'rizhu']
        for field in required_fields:
            self.validate_required(bazi_data, field, f"八字.{field}")

        for pillar in ['year', 'month', 'day', 'hour']:
            if pillar in bazi_data and bazi_data[pillar]:
                self.validate_ganzhi(bazi_data[pillar], f"八字.{pillar}柱")

        if 'wuxing' in bazi_data:
            wuxing = bazi_data['wuxing']
            for wx in ['木', '火', '土', '金', '水']:
                if wx in wuxing:
                    wx_data = wuxing[wx]
                    if isinstance(wx_data, dict):
                        if 'count' in wx_data:
                            self.validate_integer(wx_data['count'], f"五行.{wx}.数量", min_val=0)

        passed = len(self.errors) == 0
        if passed:
            logger.info("[数据验证] 八字排盘结果数据验证通过")
        else:
            logger.error(f"[数据验证] 八字排盘结果验证失败，共{len(self.errors)}个错误")

        return passed

    def validate_ai_analysis_result(
        self,
        analysis_data: Dict[str, Any],
        analysis_type: str = 'bazi'
    ) -> bool:
        """
        验证AI分析结果数据完整性

        Args:
            analysis_data: AI分析结果数据
            analysis_type: 分析类型 ('bazi' 或 'meihua')

        Returns:
            是否验证通过
        """
        self.reset()
        logger.info(f"[数据验证] 开始验证AI分析结果（{analysis_type}）")

        if analysis_type == 'bazi':
            required_fields = ['personality', 'career', 'marriage', 'health', 'suggestions',
                               'pattern_analysis', 'wuxing_balance', 'shishen_analysis',
                               'improvement_plan']
        elif analysis_type == 'meihua':
            required_fields = ['gua_overview', 'situation_analysis', 'good_omens',
                              'bad_omens', 'action_advice', 'final_verdict']
        elif analysis_type == 'liuren':
            required_fields = ['ke_overview', 'si_ke_analysis', 'san_chuan_analysis',
                              'tian_jiang_analysis', 'final_verdict']
        else:
            self.add_error('分析类型', f"不支持的分析类型: {analysis_type}")
            return False

        for field in required_fields:
            if field not in analysis_data:
                self.add_error(f'AI结果.{field}', '字段缺失')
            else:
                value = analysis_data[field]
                if field == 'final_verdict':
                    if not isinstance(value, str) or not value.strip():
                        self.add_warning(f'AI结果.{field}', '内容为空')
                else:
                    if not isinstance(value, list):
                        self.add_error(f'AI结果.{field}', '格式错误，应为数组')
                    elif len(value) == 0:
                        self.add_warning(f'AI结果.{field}', '内容为空数组')

        passed = len(self.errors) == 0
        if passed:
            logger.info("[数据验证] AI分析结果验证通过")
        else:
            logger.error(f"[数据验证] AI分析结果验证失败，共{len(self.errors)}个错误")

        return passed

    def get_errors(self) -> List[str]:
        """获取所有错误信息"""
        return self.errors.copy()

    def get_warnings(self) -> List[str]:
        """获取所有警告信息"""
        return self.warnings.copy()

    def get_validation_report(self) -> Dict[str, Any]:
        """
        获取验证报告

        Returns:
            验证报告字典
        """
        return {
            'passed': len(self.errors) == 0,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.get_errors(),
            'warnings': self.get_warnings()
        }


_default_validator = None


def get_data_validator() -> DataValidator:
    """
    获取默认的数据验证器实例（单例模式）

    Returns:
        DataValidator实例
    """
    global _default_validator
    if _default_validator is None:
        _default_validator = DataValidator()
    return _default_validator
