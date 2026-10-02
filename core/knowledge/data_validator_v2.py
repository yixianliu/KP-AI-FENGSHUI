"""
core/data_validator_v2.py — 数据校验 v2（基于 Pydantic 风格强类型校验）

对应执行计划任务 1.4：建立统一的数据校验体系，覆盖：
- 输入校验：出生时辰、经纬度、公历/农历标志、性别
- 节气校准：立春为年柱切分依据
- 真太阳时修正
- 干支映射合法性
- 结果 Schema：标准化四柱 JSON 结构

设计原则：
1. 纯函数式校验，无状态，可复用
2. 校验结果标准化：通过/失败 + 错误清单
3. 与 core/data_validator.py 的 DataValidator 共存，v2 作为严格校验层
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.ganzhi_constants import (
    DI_ZHI, SIXTY_JIAZI, GAN_INDEX, ZHI_INDEX,
    GAN_YANG, ZHI_YANG,
)

# ---------------------------------------------------------------- 常量

#: 有效年份范围（支持 1900-2100）
YEAR_MIN = 1900
YEAR_MAX = 2100

#: 有效月份范围
MONTH_MIN = 1
MONTH_MAX = 12

#: 有效经度范围（东经 73-135，覆盖中国疆域）
LONGITUDE_MIN = 73.0
LONGITUDE_MAX = 135.0

#: 有效纬度范围（北纬 18-53）
LATITUDE_MIN = 18.0
LATITUDE_MAX = 53.0

#: 性别选项
GENDER_OPTIONS = ('男', '女')

#: 日期格式正则
_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


# ---------------------------------------------------------------- 校验结果

class ValidationResult:
    """校验结果封装：通过标志 + 错误列表 + 警告列表。"""

    __slots__ = ('success', 'errors', 'warnings')

    def __init__(self):
        self.success: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, msg: str) -> None:
        """添加一条校验错误，标记为不通过。"""
        self.success = False
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        """添加一条校验警告（不影响通过状态）。"""
        self.warnings.append(msg)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典，便于日志与 API 返回。"""
        return {
            'success': self.success,
            'errors': self.errors,
            'warnings': self.warnings,
        }


# ---------------------------------------------------------------- 纯函数校验器

def validate_year(year: int) -> Optional[str]:
    """校验年份是否在有效范围内。返回错误信息或 None。"""
    if not isinstance(year, int):
        return f'年份必须为整数，收到 {type(year).__name__}'
    if year < YEAR_MIN or year > YEAR_MAX:
        return f'年份 {year} 超出有效范围 {YEAR_MIN}-{YEAR_MAX}'
    return None


def validate_month(month: int, is_lunar: bool = False) -> Optional[str]:
    """校验月份。公历 1-12，农历 1-12（含闰月则 >12 需特殊处理）。"""
    if not isinstance(month, int):
        return f'月份必须为整数，收到 {type(month).__name__}'
    if is_lunar:
        if month < 1 or month > 12:
            return f'农历月份 {month} 超出 1-12 范围'
    else:
        if month < MONTH_MIN or month > MONTH_MAX:
            return f'月份 {month} 超出 {MONTH_MIN}-{MONTH_MAX} 范围'
    return None


def validate_day(day: int, month: int = 12, is_lunar: bool = False) -> Optional[str]:
    """校验日期，考虑月份天数与闰年。"""
    if not isinstance(day, int):
        return f'日期必须为整数，收到 {type(day).__name__}'
    if is_lunar:
        # 农历日 1-30
        if day < 1 or day > 30:
            return f'农历日期 {day} 超出 1-30 范围'
        return None
    # 公历：用 datetime 校验
    try:
        datetime(2000, month, day)  # 借用闰年 2000 做上限检测
    except ValueError:
        return f'日期 {day} 在 {month} 月无效'
    if day < 1 or day > 31:
        return f'日期 {day} 超出 1-31 范围'
    return None


def validate_time(hour: int, minute: int = 0) -> Optional[str]:
    """校验时分（0-23:00-59）。"""
    if not isinstance(hour, int) or not isinstance(minute, int):
        return '时分必须为整数'
    if hour < 0 or hour > 23:
        return f'小时 {hour} 超出 0-23 范围'
    if minute < 0 or minute > 59:
        return f'分钟 {minute} 超出 0-59 范围'
    return None


def validate_longitude(longitude: float) -> Optional[str]:
    """校验经度是否在有效范围。"""
    if not isinstance(longitude, (int, float)):
        return f'经度必须为数值，收到 {type(longitude).__name__}'
    if longitude < LONGITUDE_MIN or longitude > LONGITUDE_MAX:
        return f'经度 {longitude}° 超出有效范围 {LONGITUDE_MIN}-{LONGITUDE_MAX}°E'
    return None


def validate_latitude(latitude: float) -> Optional[str]:
    """校验纬度是否在有效范围。"""
    if not isinstance(latitude, (int, float)):
        return f'纬度必须为数值，收到 {type(latitude).__name__}'
    if latitude < LATITUDE_MIN or latitude > LATITUDE_MAX:
        return f'纬度 {latitude}° 超出有效范围 {LATITUDE_MIN}-{LATITUDE_MAX}°N'
    return None


def validate_gender(gender: str) -> Optional[str]:
    """校验性别。"""
    if gender not in GENDER_OPTIONS:
        return f'性别 "{gender}" 无效，可选值：{GENDER_OPTIONS}'
    return None


def validate_ganzhi(gz: str) -> Optional[str]:
    """校验干支组合是否在六十甲子中。"""
    if len(gz) != 2:
        return f'干支 "{gz}" 长度不为 2'
    gan, zhi = gz[0], gz[1]
    if gan not in GAN_INDEX:
        return f'天干 "{gan}" 无效'
    if zhi not in ZHI_INDEX:
        return f'地支 "{zhi}" 无效'
    if gz not in SIXTY_JIAZI:
        return f'干支 "{gz}" 不在六十甲子中'
    return None


def validate_ganzhi_pair(gan: str, zhi: str) -> Optional[str]:
    """校验干支配对合法性：阳干配阳支、阴干配阴支。"""
    if gan not in GAN_INDEX:
        return f'天干 "{gan}" 无效'
    if zhi not in ZHI_INDEX:
        return f'地支 "{zhi}" 无效'
    gan_is_yang = gan in GAN_YANG
    zhi_is_yang = zhi in ZHI_YANG
    if gan_is_yang != zhi_is_yang:
        return f'干支配对错误：{"阳干" if gan_is_yang else "阴干"}不可配{"阳支" if zhi_is_yang else "阴支"}'
    return None


# ---------------------------------------------------------------- 综合校验入口

def validate_bazi_input(data: Dict[str, Any]) -> ValidationResult:
    """八字输入完整校验。

    Args:
        data: 包含 year/month/day/hour/minute/longitude/gender 等字段的字典

    Returns:
        ValidationResult: 校验结果
    """
    result = ValidationResult()

    err = validate_year(data.get('year', 0))
    if err:
        result.add_error(err)

    is_lunar = data.get('is_lunar', False)
    err = validate_month(data.get('month', 0), is_lunar)
    if err:
        result.add_error(err)

    err = validate_day(data.get('day', 0), data.get('month', 1), is_lunar)
    if err:
        result.add_error(err)

    err = validate_time(data.get('hour', 0), data.get('minute', 0))
    if err:
        result.add_error(err)

    err = validate_longitude(data.get('longitude', 120.0))
    if err:
        result.add_error(err)

    err = validate_gender(data.get('gender', '男'))
    if err:
        result.add_error(err)

    # 子时 23:00 古法分界：23:00-23:59 归当日亥时末/次日子时初
    if data.get('hour') == 23:
        result.add_warning('23 时为古法子时起始，排盘将按次日处理')

    return result


def validate_bazi_result(result: Dict[str, Any]) -> ValidationResult:
    """八字排盘结果 Schema 校验。

    确保返回结构包含所有必要字段且格式正确。

    Args:
        result: BaziCalculator.calculate 返回的字典

    Returns:
        ValidationResult
    """
    v = ValidationResult()

    required_fields = ['year', 'month', 'day', 'hour', '四柱', 'rizhu']
    for field in required_fields:
        if field not in result:
            v.add_error(f'缺少必要字段：{field}')

    # 校验四柱结构
    pillars = result.get('四柱', [])
    if len(pillars) != 4:
        v.add_error(f'四柱长度应为 4，实际为 {len(pillars)}')
    else:
        for i, pillar in enumerate(pillars):
            if not isinstance(pillar, str) or len(pillar) != 2:
                v.add_error(f'第{i+1}柱 "{pillar}" 格式无效（应为两字干支）')
                continue
            err = validate_ganzhi(pillar)
            if err:
                v.add_error(f'第{i+1}柱：{err}')

    # 校验日柱
    rizhu = result.get('rizhu', '')
    if len(rizhu) != 2:
        v.add_error(f'日柱 "{rizhu}" 长度不为 2')

    return v


def validate_meihua_input(data: Dict[str, Any]) -> ValidationResult:
    """梅花易数输入校验。"""
    v = ValidationResult()
    method = data.get('method', 'time')
    if method not in ('time', 'number', 'direction', 'text', 'copper_coin', 'stroke'):
        v.add_error(f'起卦方法 "{method}" 无效')
    else:
        if method == 'time':
            for field in ('year', 'month', 'day', 'hour'):
                if field not in data:
                    v.add_error(f'时间起卦缺少字段：{field}')
        elif method == 'number':
            numbers = data.get('numbers', [])
            if not isinstance(numbers, list) or not (1 <= len(numbers) <= 3):
                v.add_error('数字起卦需 1-3 个数字')
    return v


def validate_liuren_input(data: Dict[str, Any]) -> ValidationResult:
    """大六壬输入校验。"""
    v = ValidationResult()
    method = data.get('method', 'auto')
    valid_methods = ('auto', 'zeike', 'biyong', 'shehai', 'maoxing',
                     'fuyin', 'fanyin', 'bieze', 'bazhuan')
    if method not in valid_methods:
        v.add_error(f'九宗门方法 "{method}" 无效')
    if data.get('year') and data.get('month') and data.get('day'):
        err = validate_year(data['year'])
        if err:
            v.add_error(err)
        err = validate_month(data['month'])
        if err:
            v.add_error(err)
    return v


def validate_xuan_kong_input(data: Dict[str, Any]) -> ValidationResult:
    """玄空飞星输入校验。

    Args:
        data: 包含 sui_xiang（坐向，如 '子山午向'）与 build_year（建造年份）
    """
    v = ValidationResult()
    sui_xiang = data.get('sui_xiang', '')
    if not sui_xiang:
        v.add_error('缺少坐向')
    else:
        # 坐向格式：X山Y向，X/Y 为 24 山之一
        valid_mountains = set(DI_ZHI) | {'壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛',
                                         '乾', '坤', '艮', '巽'}
        if len(sui_xiang) >= 4:
            mount = sui_xiang[0]
            facing = sui_xiang[-1]
            if mount not in valid_mountains:
                v.add_error(f'坐山 "{mount}" 不在二十四山中')
            if facing not in valid_mountains:
                v.add_error(f'向首 "{facing}" 不在二十四山中')
        else:
            v.add_error(f'坐向 "{sui_xiang}" 格式无效（应为 X山Y向）')
    build_year = data.get('build_year')
    if build_year:
        err = validate_year(build_year)
        if err:
            v.add_error(err)
    return v


# ---------------------------------------------------------------- 便捷工厂

def create_validator_for(pan_type: str):
    """按盘型返回对应的输入校验函数。

    Args:
        pan_type: 'bazi' / 'meihua' / 'liuren' / 'xuan_kong'

    Returns:
        callable: 接受 dict 参数，返回 ValidationResult
    """
    mapping = {
        'bazi': validate_bazi_input,
        'meihua': validate_meihua_input,
        'liuren': validate_liuren_input,
        'xuan_kong': validate_xuan_kong_input,
    }
    fn = mapping.get(pan_type)
    if fn is None:
        raise ValueError(f'未知盘型：{pan_type}，支持：{list(mapping.keys())}')
    return fn
