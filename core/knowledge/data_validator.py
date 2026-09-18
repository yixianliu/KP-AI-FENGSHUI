"""
数据验证模块
负责验证输入数据的完整性、格式正确性和业务规则约束
"""
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# 干支静态常量统一从权威源导入，避免各模块重复硬编导致索引错位。
# 加下划线前缀是为了与下方 DataValidator 的同名类属性区分开。
from core.ganzhi_constants import (
    TIAN_GAN as _TIAN_GAN,
    DI_ZHI as _DI_ZHI,
    SIXTY_JIAZI as _SIXTY_JIAZI,
)
from core.knowledge.analysis_storage import _JSON_SCHEMAS


logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """数据验证异常基类"""
    pass


class DataValidator:
    """
    数据验证器
    提供多种数据验证方法，确保输入数据完整、格式正确
    """

    # 以下三张表引用 core.ganzhi_constants 的唯一定义（保留类属性形式，
    # 是为了不破坏 DataValidator.TIAN_GAN 这类既有外部调用写法）
    TIAN_GAN = _TIAN_GAN
    DI_ZHI = _DI_ZHI
    GAN_ZHI_PAIRS = _SIXTY_JIAZI

    #: 允许的性别取值
    GENDER_OPTIONS = ['男', '女']
    #: 允许的排盘类型
    PAN_TYPES = ['八字', '梅花易数', '大六壬']

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

        # 延迟导入：liuren 模块较重，且仅本方法需要
        from core.divination.liuren import GATE_METHODS
        ZHI = _DI_ZHI  # 复用权威地支表，不再局部硬编

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

    def validate_meihua_result(self, meihua_data: Dict[str, Any]) -> bool:
        """
        验证梅花易数排盘结果数据完整性

        Args:
            meihua_data: 梅花易数排盘结果数据

        Returns:
            是否验证通过
        """
        self.reset()
        logger.info("[数据验证] 开始验证梅花易数排盘结果数据")

        # 基础字段（基础起卦结果包含的字段）
        required_fields = ['method', 'question', 'upper_num', 'lower_num', 'changing_yao', 'base_hex',
                           'base_upper_yangs', 'base_lower_yangs']
        for field in required_fields:
            self.validate_required(meihua_data, field, f"梅花.{field}")

        # 上下卦数值范围验证
        if 'upper_num' in meihua_data:
            self.validate_integer(meihua_data['upper_num'], '梅花.上卦数', min_val=1, max_val=8)
        if 'lower_num' in meihua_data:
            self.validate_integer(meihua_data['lower_num'], '梅花.下卦数', min_val=1, max_val=8)
        if 'changing_yao' in meihua_data:
            self.validate_integer(meihua_data['changing_yao'], '梅花.动爻', min_val=1, max_val=6)

        # base_hex 结构验证（基础起卦返回的简要结构）
        if 'base_hex' in meihua_data and isinstance(meihua_data['base_hex'], dict):
            base_hex = meihua_data['base_hex']
            hex_fields = ['upper', 'lower', 'full']
            for hf in hex_fields:
                if hf not in base_hex:
                    self.add_error(f"梅花.base_hex.{hf}", '字段缺失')

        # base_upper_yangs / base_lower_yangs 验证
        for key in ['base_upper_yangs', 'base_lower_yangs']:
            if key in meihua_data and isinstance(meihua_data[key], list):
                yangs = meihua_data[key]
                if len(yangs) != 3:
                    self.add_error(f'梅花.{key}', f'应含3爻，实际为{len(yangs)}')
                else:
                    for i, yao in enumerate(yangs, 1):
                        if isinstance(yao, dict):
                            if 'type' not in yao or yao['type'] not in ['老阳', '少阴', '少阳', '老阴']:
                                self.add_error(f'梅花.{key}[{i}]', f"爻类型无效: {yao.get('type')}")
                            if 'symbol' not in yao:
                                self.add_error(f'梅花.{key}[{i}]', '缺少symbol字段')

        # 生成的所有卦象验证（generate_all_hexagrams 产出的结构）
        if 'all_hexagrams' in meihua_data and isinstance(meihua_data['all_hexagrams'], dict):
            all_hex = meihua_data['all_hexagrams']
            for hex_key in ['base', 'hu', 'bian', 'cuo', 'zong']:
                if hex_key in all_hex:
                    hex_data = all_hex[hex_key]
                    if isinstance(hex_data, dict):
                        # base 有 upper_num/lower_num，其他只有 upper_yangs/lower_yangs
                        if hex_key == 'base':
                            required_hex = ['upper_num', 'lower_num', 'upper_yangs', 'lower_yangs']
                        else:
                            required_hex = ['upper_yangs', 'lower_yangs']
                        for rh in required_hex:
                            if rh not in hex_data:
                                self.add_error(f"梅花.all_hexagrams.{hex_key}.{rh}", '字段缺失')
                        # 验证爻数组
                        for yao_key in ['upper_yangs', 'lower_yangs']:
                            if yao_key in hex_data and isinstance(hex_data[yao_key], list):
                                yangs = hex_data[yao_key]
                                if len(yangs) != 3:
                                    self.add_error(f'梅花.all_hexagrams.{hex_key}.{yao_key}', f'应含3爻，实际为{len(yangs)}')

        # 方法特定字段验证
        method = meihua_data.get('method', '')
        if method == '笔画起卦':
            self.validate_required(meihua_data, 'char', '梅花.汉字')
            self.validate_required(meihua_data, 'stroke_count', '梅花.笔画数')
        elif method == '铜钱摇卦':
            self.validate_required(meihua_data, 'six_lines', '梅花.六爻')
            if 'six_lines' in meihua_data:
                lines = meihua_data['six_lines']
                if isinstance(lines, list):
                    if len(lines) != 6:
                        self.add_error('梅花.六爻', f"爻数应为6，实际为{len(lines)}")
                    else:
                        valid_yao = {'老阳', '少阴', '少阳', '老阴'}
                        for i, y in enumerate(lines, 1):
                            if y not in valid_yao:
                                self.add_error('梅花.六爻', f"第{i}爻取值无效: {y}")

        passed = len(self.errors) == 0
        if passed:
            logger.info("[数据验证] 梅花易数排盘结果数据验证通过")
        else:
            logger.error(f"[数据验证] 梅花易数排盘结果验证失败，共{len(self.errors)}个错误")

        return passed

    def validate_liuren_result(self, liuren_data: Dict[str, Any]) -> bool:
        """
        验证大六壬排盘结果数据完整性

        Args:
            liuren_data: 大六壬排盘结果数据

        Returns:
            是否验证通过
        """
        self.reset()
        logger.info("[数据验证] 开始验证大六壬排盘结果数据")

        # 基础字段
        required_fields = ['method', 'method_name', 'question', 'time', 'ri_gan', 'ri_zhi',
                           'yue_jiang', 'zhan_shi', 'is_day', 'di_pan', 'tian_pan',
                           'si_ke', 'san_chuan', 'tian_jiang', 'shen_sha']
        for field in required_fields:
            self.validate_required(liuren_data, field, f"六壬.{field}")

        # 日干支验证
        if 'ri_gan' in liuren_data:
            if liuren_data['ri_gan'] not in self.TIAN_GAN:
                self.add_error('六壬.ri_gan', f"日干'{liuren_data['ri_gan']}'不合法")
        if 'ri_zhi' in liuren_data:
            if liuren_data['ri_zhi'] not in self.DI_ZHI:
                self.add_error('六壬.ri_zhi', f"日支'{liuren_data['ri_zhi']}'不合法")

        # 月将验证
        if 'yue_jiang' in liuren_data:
            if liuren_data['yue_jiang'] not in self.DI_ZHI:
                self.add_error('六壬.yue_jiang', f"月将'{liuren_data['yue_jiang']}'不合法")

        # 占时验证
        if 'zhan_shi' in liuren_data:
            if liuren_data['zhan_shi'] not in self.DI_ZHI:
                self.add_error('六壬.zhan_shi', f"占时'{liuren_data['zhan_shi']}'不合法")

        # 地盘验证（应为12地支）
        if 'di_pan' in liuren_data and isinstance(liuren_data['di_pan'], list):
            if len(liuren_data['di_pan']) != 12:
                self.add_error('六壬.di_pan', f"地盘应含12地支，实际为{len(liuren_data['di_pan'])}")
            else:
                for i, z in enumerate(liuren_data['di_pan']):
                    if z not in self.DI_ZHI:
                        self.add_error('六壬.di_pan', f"第{i+1}位地支'{z}'不合法")

        # 天盘验证（字典，键为地盘支，值为天盘支）
        if 'tian_pan' in liuren_data and isinstance(liuren_data['tian_pan'], dict):
            if len(liuren_data['tian_pan']) != 12:
                self.add_error('六壬.tian_pan', f"天盘应含12项，实际为{len(liuren_data['tian_pan'])}")
            for dz, tp in liuren_data['tian_pan'].items():
                if dz not in self.DI_ZHI:
                    self.add_error('六壬.tian_pan', f"地盘键'{dz}'不合法")
                if tp not in self.DI_ZHI:
                    self.add_error('六壬.tian_pan', f"天盘值'{tp}'不合法")

        # 四课验证
        if 'si_ke' in liuren_data and isinstance(liuren_data['si_ke'], dict):
            si_ke = liuren_data['si_ke']
            for ke_name in ['gan_shang', 'gan_yin', 'zhi_shang', 'zhi_yin']:
                if ke_name in si_ke and isinstance(si_ke[ke_name], dict):
                    ke = si_ke[ke_name]
                    if 'dizhi' in ke and ke['dizhi'] not in self.DI_ZHI:
                        self.add_error(f'六壬.si_ke.{ke_name}.dizhi', f"地支'{ke['dizhi']}'不合法")
                    if 'tianpan' in ke and ke['tianpan'] not in self.DI_ZHI:
                        self.add_error(f'六壬.si_ke.{ke_name}.tianpan', f"天盘支'{ke['tianpan']}'不合法")

        # 三传验证
        if 'san_chuan' in liuren_data and isinstance(liuren_data['san_chuan'], dict):
            san_chuan = liuren_data['san_chuan']
            for trans in ['chu', 'zhong', 'mo', 'gate']:
                self.validate_required(san_chuan, trans, f"六壬.san_chuan.{trans}")
            if 'chu' in san_chuan and san_chuan['chu'] not in self.DI_ZHI:
                self.add_error('六壬.san_chuan.chu', f"初传'{san_chuan['chu']}'不合法")
            if 'zhong' in san_chuan and san_chuan['zhong'] not in self.DI_ZHI + self.TIAN_GAN:
                self.add_error('六壬.san_chuan.zhong', f"中传'{san_chuan['zhong']}'不合法")
            if 'mo' in san_chuan and san_chuan['mo'] not in self.DI_ZHI + self.TIAN_GAN:
                self.add_error('六壬.san_chuan.mo', f"末传'{san_chuan['mo']}'不合法")

        # 十二天将验证
        if 'tian_jiang' in liuren_data and isinstance(liuren_data['tian_jiang'], list):
            if len(liuren_data['tian_jiang']) != 12:
                self.add_error('六壬.tian_jiang', f"十二天将应含12项，实际为{len(liuren_data['tian_jiang'])}")
            else:
                valid_jiang = ['贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙',
                               '天空', '白虎', '太常', '玄武', '太阴', '天后']
                for i, tj in enumerate(liuren_data['tian_jiang']):
                    if isinstance(tj, dict):
                        if 'jiang' in tj and tj['jiang'] not in valid_jiang:
                            self.add_error('六壬.tian_jiang', f"第{i+1}位天将'{tj['jiang']}'不合法")
                        if 'pos' in tj and tj['pos'] not in self.DI_ZHI:
                            self.add_error('六壬.tian_jiang', f"第{i+1}位地支'{tj['pos']}'不合法")

        # 神煞验证
        if 'shen_sha' in liuren_data and isinstance(liuren_data['shen_sha'], dict):
            shen_sha = liuren_data['shen_sha']
            expected_sha = ['驿马', '三传', '空亡', '六合', '六害', '天马', '旺相休囚死']
            for sa in expected_sha:
                if sa not in shen_sha:
                    self.add_warning(f'六壬.shen_sha.{sa}', '字段缺失')

        passed = len(self.errors) == 0
        if passed:
            logger.info("[数据验证] 大六壬排盘结果数据验证通过")
        else:
            logger.error(f"[数据验证] 大六壬排盘结果验证失败，共{len(self.errors)}个错误")

        return passed

    def validate_ai_analysis_result(
        self,
        analysis_data: Dict[str, Any],
        analysis_type: str = 'bazi'
    ) -> bool:
        """
        验证智能分析结果数据完整性

        Args:
            analysis_data: 智能分析结果数据
            analysis_type: 分析类型 ('bazi' 或 'meihua')

        Returns:
            是否验证通过
        """
        self.reset()
        logger.info(f"[数据验证] 开始验证智能分析结果（{analysis_type}）")

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
            logger.info("[数据验证] 智能分析结果验证通过")
        else:
            logger.error(f"[数据验证] 智能分析结果验证失败，共{len(self.errors)}个错误")

        return passed

    def _validate_analysis_schema(self, analysis_data: Dict[str, Any], pan_type: str) -> bool:
        """
        Validate AI analysis result against the JSON schema for the given pan_type.
        
        Args:
            analysis_data: The AI analysis result dictionary.
            pan_type: One of 'bazi', 'meihua', 'liuren'.
            
        Returns:
            True if validation passes, False otherwise.
        """
        self.reset()
        logger.info(f"[数据验证] 开始验证 {pan_type} AI分析结果结构")
        
        if not isinstance(analysis_data, dict):
            self.add_error('AI结果', '输入数据必须是字典')
            return False
        
        schema = _JSON_SCHEMAS.get(pan_type)
        if not schema:
            self.add_error('AI结果', f'不支持的分析类型: {pan_type}')
            return False
        
        # Check for deprecated fields
        deprecated_fields = ['marriage', 'pattern_analysis', 'suggestions']
        for field in deprecated_fields:
            if field in analysis_data:
                self.add_warning(f'AI结果.{field}', '该字段已被废弃，请移除')
        
        # Validate each field in schema
        for field, description in schema.items():
            if field not in analysis_data:
                self.add_error(f'AI结果.{field}', '必需字段缺失')
                continue
            
            value = analysis_data[field]
            
            # Determine expected type
            if field in ('final_verdict', 'disclaimer', 'key_points'):
                # String fields
                if not isinstance(value, str):
                    self.add_error(f'AI结果.{field}', f'期望字符串类型，得到 {type(value).__name__}')
                elif field == 'key_points' and value.strip() == '':
                    self.add_warning(f'AI结果.{field}', '内容为空')
                # For final_verdict and disclaimer, we could check non-empty but not required
            else:
                # Array of strings fields, expecting at least 3 items
                if not isinstance(value, list):
                    self.add_error(f'AI结果.{field}', f'期望字符串数组类型，得到 {type(value).__name__}')
                else:
                    # Check each element is string
                    for i, item in enumerate(value):
                        if not isinstance(item, str):
                            self.add_error(f'AI结果.{field}[{i}]', f'期望字符串，得到 {type(item).__name__}')
                    # Check minimum length
                    if len(value) < 3:
                        self.add_warning(f'AI结果.{field}', f'数组长度应不少于3，实际为{len(value)}')
        
        passed = len(self.errors) == 0
        if passed:
            logger.info(f"[数据验证] {pan_type} AI分析结果验证通过")
        else:
            logger.error(f"[数据验证] {pan_type} AI分析结果验证失败，共{len(self.errors)}个错误")
        
        return passed

    def validate_bazi_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """
        Validate Bazi AI analysis result against the JSON schema.
        
        Args:
            analysis_data: The AI analysis result dictionary.
            
        Returns:
            True if validation passes, False otherwise.
        """
        return self._validate_analysis_schema(analysis_data, 'bazi')

    def validate_meihua_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """
        Validate Mei Hua AI analysis result against the JSON schema.
        
        Args:
            analysis_data: The AI analysis result dictionary.
            
        Returns:
            True if validation passes, False otherwise.
        """
        return self._validate_analysis_schema(analysis_data, 'meihua')

    def validate_liuren_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """
        Validate Liu Ren AI analysis result against the JSON schema.
        
        Args:
            analysis_data: The AI analysis result dictionary.
            
        Returns:
            True if validation passes, False otherwise.
        """
        return self._validate_analysis_schema(analysis_data, 'liuren')

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
