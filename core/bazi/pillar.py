"""
core/bazi/pillar.py — 八字四柱纯函数引擎

本模块提供完整的四柱排盘纯函数接口，内部委托给已验证的
calendar_utils.BaZiCalendar 实现，确保计算准确性。

公开接口：
  - calculate_pillars(...)  : 主排盘入口（纯函数，推荐）
  - PillarEngine            : 类封装（向后兼容）
  - calc_year/month/day/hour_pillar  : 各柱独立计算函数
  - hour_zhi_from_hour       : 小时→地支时支
  - find_li_chun             : 查找立春时刻
  - get_lunar_year           : 根据立春确定农历年
  - get_month_zhi            : 根据节气确定月建
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - 仅供字符串注解解析，运行期不求值
    import datetime

# 延迟导入，避免循环依赖
def _get_calendar():
    """懒加载 BaZiCalendar，首次调用时触发数据库初始化。"""
    from core.calendar_utils import BaZiCalendar
    return BaZiCalendar()


# ---------------------------------------------------------------- 常量（与 ganzhi_constants 对齐）

#: 十天干
TG = ('甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸')
#: 十二地支
DZ = ('子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥')
#: 六十甲子
JIAZI = tuple(TG[i % 10] + DZ[i % 12] for i in range(60))
#: 阳干集合
YANG_GAN = frozenset(('甲', '丙', '戊', '庚', '壬'))

#: 五虎遁：年干 → 寅月月干
#: 依据《渊海子平·论十干生月取例》
WU_HU_DUN: dict[str, tuple[str, ...]] = {
    '甲': ('丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁'),
    '乙': ('戊', '己', '庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己'),
    '丙': ('庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛'),
    '丁': ('壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'),
    '戊': ('甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '甲', '乙'),
    '己': ('丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁'),
    '庚': ('戊', '己', '庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己'),
    '辛': ('庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛'),
    '壬': ('壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'),
    '癸': ('甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '甲', '乙'),
}

#: 五鼠遁：日干 → 子时（23:00-01:00）时干
#: 依据《珞琭子赋》
WU_SHU_DUN: dict[str, tuple[str, ...]] = {
    '甲': ('甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '甲', '乙'),
    '乙': ('丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁'),
    '丙': ('戊', '己', '庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己'),
    '丁': ('庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛'),
    '戊': ('壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'),
    '己': ('甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '甲', '乙'),
    '庚': ('丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁'),
    '辛': ('戊', '己', '庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己'),
    '壬': ('庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛'),
    '癸': ('壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'),
}


# ---------------------------------------------------------------- 纯函数：各柱独立计算

def calc_year_pillar(year: int) -> str:
    """计算年干支（六十甲子序号）。

    依据《三命通会》：年柱以立春为界，公元4年为甲子年起点。
    公式：idx = (year - 4) mod 60

    Args:
        year: 公历年份（立春后的年份即为该年干支，立春前为上年）

    Returns:
        str: 年干支，如 '甲子'
    """
    idx = (year - 4) % 60
    return JIAZI[idx]


def calc_month_pillar(year_gan: str, month_zhi: str) -> str:
    """五虎遁年起月法计算月干支。

    依据《渊海子平·论十干生月取例》：
    丙辛之年戊寅首，丁壬庚寅居上头，
    戊癸何方发，甲寅之上好追求，
    甲己何处求，丙寅之上莫相误，乙庚之岁戊寅初。

    WU_HU_DUN 索引对应月建地支顺序：寅(0)、卯(1)、辰(2)、巳(3)、
    午(4)、未(5)、申(6)、酉(7)、戌(8)、亥(9)、子(10)、丑(11)。

    Args:
        year_gan: 年干（单个天干字符）
        month_zhi: 月支（寅/卯/辰/巳/午/未/申/酉/戌/亥/子/丑）

    Returns:
        str: 月干支，如 '丙寅'
    """
    if month_zhi not in DZ:
        raise ValueError(f"非法月支: {month_zhi}")
    rules = WU_HU_DUN.get(year_gan)
    if rules is None:
        raise ValueError(f"非法年干: {year_gan}")
    # WU_HU_DUN 索引从寅月(0)开始，DZ 索引从子月(0)开始
    # 转换：寅月(DZ index 2) → WU_HU_DUN index 0
    month_idx = (DZ.index(month_zhi) - 2) % 12
    month_gan = rules[month_idx]
    return month_gan + month_zhi


def calc_day_pillar(year: int, month: int, day: int) -> str:
    """基于儒略日精确计算日干支。

    算法来源（参照 calendar_utils.GanZhiCalculator.get_day_ganzhi）：
    1. 计算公历日期的儒略日(JD)
    2. 基准日 2000-01-01 JD=2451544.5，对应干支戊午(序号54)
    3. 真实历法相对代码基准存在 -6 个干支位的固定偏移

    验证锚点：
      - 2000-01-01 = 戊午（序号54）
      - 1949-10-01 = 甲子（序号0）
      - 2026-07-09 = 甲申（序号20）

    Args:
        year: 公历年
        month: 公历月
        day: 公历日

    Returns:
        str: 日干支，如 '甲子'
    """
    import math
    y, m = year, month
    if m <= 2:
        y -= 1
        m += 12
    A = math.floor(y / 100)
    B = 2 - A + math.floor(A / 4)
    jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + day + B - 1524.5

    base_jd = 2451544.5
    delta = jd - base_jd
    # -6 偏移修正（详见函数注释）
    idx = (int((delta % 60 + 60) % 60) - 6) % 60
    return JIAZI[idx]


def calc_hour_pillar(day_gan: str, hour_zhi: str) -> str:
    """五鼠遁日起时法计算时干支。

    依据《珞琭子赋》：
    甲己还加甲，乙庚丙作初，
    丙辛从戊起，丁壬庚子居，
    戊癸何方发，壬子是真途。

    子时从23:00开始（古法子时分界），每个时辰2小时。

    WU_SHU_DUN 索引对应地支顺序：子(0)、丑(1)、寅(2)、…、亥(11)。

    Args:
        day_gan: 日干（单个天干字符）
        hour_zhi: 时支（子/丑/寅/卯/辰/巳/午/未/申/酉/戌/亥）

    Returns:
        str: 时干支，如 '甲子'
    """
    if hour_zhi not in DZ:
        raise ValueError(f"非法时支: {hour_zhi}")
    rules = WU_SHU_DUN.get(day_gan)
    if rules is None:
        raise ValueError(f"非法日干: {day_gan}")
    hour_idx = DZ.index(hour_zhi)
    hour_gan = rules[hour_idx]
    return hour_gan + hour_zhi


def hour_zhi_from_hour(hour: int) -> str:
    """将小时数转换为地支时支（古法子时从23:00起算）。

    古法子时从23:00开始，23:00-01:59为子时，02:00-03:59为丑时，以此类推。
    子时跨日：23:00-23:59 和 00:00-01:59 均归子时。

    Args:
        hour: 0-23 的小时数

    Returns:
        str: 时支，如 '子'
    """
    return DZ[(hour + 1) // 2 % 12]


# ---------------------------------------------------------------- 辅助函数

def find_li_chun(year: int) -> 'datetime.datetime':
    """近似计算指定年份立春日辰（二分查找黄经315°）。

    立春对应太阳黄经315°，使用天文近似算法二分查找精确时刻。
    误差控制在±30分钟内，满足排盘需求。

    Args:
        year: 公历年份

    Returns:
        datetime: 立春时刻
    """
    from core.calendar_utils import JieQiCalculator
    return JieQiCalculator.calculate_jieqi(year, 0)  # 立春是第0个节气


def get_lunar_year(solar_dt: 'datetime.datetime') -> int:
    """根据立春判断农历年份。

    立春前一年为上一个农历年，立春后为新年。

    Args:
        solar_dt: 公历日期时间

    Returns:
        int: 农历年份
    """
    li_chun = find_li_chun(solar_dt.year)
    if solar_dt < li_chun:
        return solar_dt.year - 1
    return solar_dt.year


def get_month_zhi(solar_dt: 'datetime.datetime') -> str:
    """根据节气确定月建地支。

    寅月始于立春(0°)，卯月始于惊蛰(345°)，……，丑月始于小寒(285°)。
    月建以「节」为界，非「气」。

    Args:
        solar_dt: 公历日期时间

    Returns:
        str: 月支，如 '寅'
    """
    from core.calendar_utils import JieQiCalculator
    jieqi = JieQiCalculator()
    return jieqi.get_solar_term_month(solar_dt) or '寅'


# ---------------------------------------------------------------- 主入口

def calculate_pillars(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    longitude: float = 120.0,
) -> dict:
    """完整四柱排盘主入口（纯函数）。

    委托给已验证的 calendar_utils.BaZiCalendar 实现，确保准确性。

    Args:
        year: 公历年
        month: 公历月
        day: 公历日
        hour: 公历小时
        minute: 公历分钟
        longitude: 经度，用于真太阳时修正（默认东经120°）

    Returns:
        dict: 含 'year', 'month', 'day', 'hour' 四柱，
              以及 'lunar_year', 'month_zhi', 'hour_zhi', 'rizhu' 等字段
    """
    cal = _get_calendar()
    return cal.calculate_bazi(year, month, day, hour, minute, longitude)


# ---------------------------------------------------------------- 类封装（向后兼容）

class PillarEngine:
    """四柱排盘引擎（类封装，保留向后兼容）。

    推荐使用纯函数 :func:`calculate_pillars` 以获得更好的测试性与批处理能力。
    """

    def calculate(self, year: int, month: int, day: int, hour: int,
                  minute: int = 0, longitude: float = 120.0) -> dict:
        """计算四柱。

        Args:
            year: 公历年
            month: 公历月
            day: 公历日
            hour: 公历小时
            minute: 公历分钟
            longitude: 经度（默认东经120°）

        Returns:
            dict: 四柱结果
        """
        return calculate_pillars(year, month, day, hour, minute, longitude)
