"""
core/astronomy — 天文计算子包

提供真太阳时、均时差、节气时刻等天文相关纯函数计算。
所有函数无状态、纯函数式，便于单元测试与向量化批量计算。

算法依据：
- 均时差公式：基于 Meeus《天文算法》第25章近似公式
- 真太阳时 = 平太阳时 + 均时差
- 平太阳时 = 标准时区时间 + 经度修正（每度4分钟）
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta

__all__ = [
    'calculate_true_solar_time',
    'equation_of_time',
    'longitude_time_correction',
    'solar_hour_to_zhi',
    'find_jieqi_approx',
]

# ---------------------------------------------------------------- 常量

#: 标准时间经度（北京时间东八区）
STANDARD_LONGITUDE = 120.0

#: 每度经度对应的时间差（分钟）
MINUTES_PER_DEGREE = 4.0


# ---------------------------------------------------------------- 均时差计算

def equation_of_time(day_of_year: int) -> float:
    """计算均时差（单位：分钟）。

    均时差是真太阳时与平太阳时之间的差值，由地球公转轨道偏心率和
    黄赤交角共同导致。使用 Meeus 近似公式。

    公式来源：Jean Meeus, "Astronomical Algorithms", 2nd Ed.,
    Chapter 25 — Equation of Time.

    Args:
        day_of_year: 一年中的第几天 (1-366)

    Returns:
        float: 均时差（分钟），正值表示真太阳时快于平太阳时
    """
    b = 2.0 * math.pi * (day_of_year - 81) / 364.0
    return (
        9.87 * math.sin(2.0 * b)
        - 7.53 * math.cos(b)
        - 1.5 * math.sin(b)
    )


def longitude_time_correction(longitude: float) -> float:
    """计算经度修正时间（单位：分钟）。

    标准经度以东经120°为基准，每偏离1°产生4分钟时间差。

    Args:
        longitude: 地理经度（东经为正，西经为负）

    Returns:
        float: 经度修正时间（分钟），正值表示当地平太阳时晚于标准时
    """
    return (longitude - STANDARD_LONGITUDE) * MINUTES_PER_DEGREE


def calculate_true_solar_time(
    solar_dt: datetime,
    longitude: float = STANDARD_LONGITUDE,
) -> datetime:
    """计算真太阳时。

    计算流程：
    1. 平太阳时 = 标准时区时间 + 经度修正
    2. 均时差 = f(年积日)
    3. 真太阳时 = 平太阳时 + 均时差

    Args:
        solar_dt: 标准时区时间（datetime对象）
        longitude: 地理经度，默认东经120°

    Returns:
        datetime: 真太阳时
    """
    lon_corr = longitude_time_correction(longitude)
    mean_solar = solar_dt + timedelta(minutes=lon_corr)
    eq_time = equation_of_time(mean_solar.timetuple().tm_yday)
    return mean_solar + timedelta(minutes=eq_time)


def solar_hour_to_zhi(solar_hour: float) -> str:
    """将真太阳时的小时数转换为地支时支。

    古法子时从23:00开始，23:00-00:59为子时，01:00-02:59为丑时，以此类推。
    晚子时（23:00-00:00）按当日排盘但时柱用次日日干。

    Args:
        solar_hour: 真太阳时的小时数（可带小数，如 12.5 表示12:30）

    Returns:
        str: 地支时支，如 '午'
    """
    ZHI = ('子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥')
    # 23:00起算，每个时辰2小时；子时跨日（23:00-01:59），故偏移+2
    return ZHI[int((solar_hour + 1)) // 2 % 12]


# ---------------------------------------------------------------- 节气近似计算

def _sun_longitude(jd: float) -> float:
    """计算给定儒略日的太阳黄经（度）。

    使用简化天文算法，精度约±0.01°，满足排盘需求。

    Args:
        jd: 儒略日

    Returns:
        float: 太阳黄经（0-360°）
    """
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + 36000.76983 * T + 0.0003032 * T ** 2) % 360
    M = (357.52911 + 35999.05029 * T - 0.0001537 * T ** 2) % 360
    C = (
        (1.914602 - 0.004817 * T - 0.000014 * T ** 2) * math.sin(math.radians(M))
        + (0.019993 - 0.000101 * T) * math.sin(math.radians(2 * M))
        + 0.000289 * math.sin(math.radians(3 * M))
    )
    return (L0 + C) % 360


def _jd_to_datetime(jd: float) -> datetime:
    """将儒略日转换为 datetime。"""
    jd += 0.5
    z = int(jd)
    f = jd - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - int(alpha / 4)
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = b - d - int(30.6001 * e)
    month = e - 1 if e < 14 else e - 13
    yr = c - 4716 if month > 2 else c - 4715
    hours = int(f * 24)
    minutes = int((f * 24 - hours) * 60)
    return datetime(yr, month, day, hours, minutes)


def find_jieqi_approx(
    year: int,
    target_angle: float,
    center_day: int = 35,
    half_range: int = 30,
) -> datetime:
    """二分查找指定黄经角度对应的时刻。

    用于节气时刻近似计算。例如立春对应黄经315°。

    Args:
        year: 公历年份
        target_angle: 目标太阳黄经（度）
        center_day: 估算中心日（当年第几天，默认35≈2月4日）
        half_range: 搜索半宽（天），默认30天

    Returns:
        datetime: 近似时刻
    """
    from datetime import date as _date
    base_jd = _julian_day_from_date(year, 1, 1) + center_day - 1

    jd_start = base_jd - half_range
    jd_end = base_jd + half_range

    for _ in range(50):
        jd_mid = (jd_start + jd_end) / 2
        angle = _sun_longitude(jd_mid)
        diff = (angle - target_angle + 180) % 360 - 180
        if abs(diff) < 0.001:
            break
        if diff > 0:
            jd_end = jd_mid
        else:
            jd_start = jd_mid

    return _jd_to_datetime(jd_mid)


def _julian_day_from_date(year: int, month: int, day: int) -> float:
    """计算公历日期对应的儒略日。"""
    y, m = year, month
    if m <= 2:
        y -= 1
        m += 12
    A = math.floor(y / 100)
    B = 2 - A + math.floor(A / 4)
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + day + B - 1524.5
