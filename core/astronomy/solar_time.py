"""
core/astronomy — 天文计算子包

提供真太阳时、均时差、节气时刻等天文相关纯函数计算。
所有函数无状态、纯函数式，便于单元测试与向量化批量计算。

算法依据：
- 均时差公式：基于 Meeus《天文算法》第25章近似公式
- 真太阳时 = 平太阳时 + 均时差
- 平太阳时 = 标准时区时间 + 经度修正（每度4分钟）
- 节气时刻：VSOP87D 截断序列求太阳地心视黄经，二分逼近目标黄经

【时间口径（重要，P0-2 修复）】
本模块对外一律使用两种明确口径，不再有第三种：
1. 儒略日 jd 一律为 **真实 UT 儒略日**（不是「北京时间当作 UT」的伪 JD）；
2. datetime 一律为 **北京时间（UTC+8）的 naive datetime**。
边界换算集中在本模块的 julian_day_from_beijing_parts / beijing_datetime_from_julian_day，
调用方只需按上述口径传参即可。
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from functools import lru_cache

__all__ = [
    'calculate_true_solar_time',
    'equation_of_time',
    'longitude_time_correction',
    'solar_hour_to_zhi',
    'find_jieqi_approx',
    'find_jieqi_julian_day',
    'apparent_sun_longitude',
    'julian_day_from_beijing',
    'julian_day_from_beijing_parts',
    'beijing_datetime_from_julian_day',
]

# ---------------------------------------------------------------- 常量

#: 标准时间经度（北京时间东八区）
STANDARD_LONGITUDE = 120.0

#: 每度经度对应的时间差（分钟）
MINUTES_PER_DEGREE = 4.0

#: 北京时间相对 UT 的偏移（小时）
BEIJING_OFFSET_HOURS = 8.0

#: 北京时间相对 UT 的偏移（天）
_BEIJING_OFFSET_DAYS = BEIJING_OFFSET_HOURS / 24.0

#: J2000.0 儒略日
_J2000 = 2451545.0


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
        solar_dt: 标准时区时间（北京时间 naive datetime）
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


# ---------------------------------------------------------------- 儒略日边界换算

def julian_day_from_beijing_parts(year: int, month: int, day: int, hour: float = 0.0) -> float:
    """北京时间（UTC+8）年月日时分 → 真实 UT 儒略日。

    这是全项目唯一的「北京时间 → JD」入口。旧实现直接把北京 0 点当作 UT，
    使节气交接时刻整体偏早 8 小时，本函数在构造阶段即减去 8 小时偏移。

    Args:
        year: 公历年
        month: 公历月
        day: 公历日
        hour: 北京时的小时数（可带小数，如 16.4486 表示 16:26:53）

    Returns:
        float: 真实 UT 儒略日
    """
    # 先把「日内小数天」和「日历 → JD」合并，再整体减去 8h；JD 连续，
    # 因此跨日（如北京 00:00 = 前一日 16:00 UT）会被自动落到前一天。
    day_fraction = day + hour / 24.0
    y, m = year, month
    if m <= 2:
        y -= 1
        m += 12
    a = math.floor(y / 100.0)
    b = 2 - a + math.floor(a / 4.0)
    return (
        math.floor(365.25 * (y + 4716))
        + math.floor(30.6001 * (m + 1))
        + day_fraction
        + b
        - 1524.5
        - _BEIJING_OFFSET_DAYS
    )


def julian_day_from_beijing(dt: datetime) -> float:
    """北京时间 naive datetime → 真实 UT 儒略日。"""
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + dt.microsecond / 3.6e9
    return julian_day_from_beijing_parts(dt.year, dt.month, dt.day, hour)


def beijing_datetime_from_julian_day(jd_ut: float) -> datetime:
    """真实 UT 儒略日 → 北京时间（UTC+8）naive datetime。

    与 julian_day_from_beijing_parts 互为逆运算：输出阶段补回 8 小时。
    精度到秒（毫秒级由浮点误差决定，不影响节气分钟级判定）。
    """
    jd = jd_ut + 0.5
    z = int(jd)
    f = jd - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - int(alpha / 4.0)
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)

    day = b - d - int(30.6001 * e)
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715

    ut = datetime(year, month, day) + timedelta(seconds=f * 86400.0)
    return ut + timedelta(hours=BEIJING_OFFSET_HOURS)


# ---------------------------------------------------------------- 太阳视黄经（VSOP87D 截断）

# 说明：
# 以下两张表由官方 VSOP87D.ear 按振幅阈值截断并四舍五入得到（L0 ≥ 1e-7、
# R0 ≥ 1e-6，其余阶次见各项前的注释），共 106 项。太阳地心视黄经误差
# ≈ 1~2″（≈ 40~50 秒时间），满足节气「±1 分钟」口径。
# 每项格式为 (A, B, C)，贡献 A·cos(B + C·τ)，单位：A/B 为弧度、C 为 1/千年。
_L_SERIES = (
    # T^0
    (
        (1.75347045673, 0.0, 0.0),
        (0.03341656456, 4.6692568042, 6283.07585),
        (0.00034894275, 4.6261024176, 12566.1517),
        (3.417571e-05, 2.8288657961, 3.523118),
        (3.497056e-05, 2.7441180097, 5753.384885),
        (3.135896e-05, 3.6276704176, 77713.771468),
        (2.676218e-05, 4.418083514, 7860.419392),
        (2.342687e-05, 6.1351623763, 3930.209696),
        (1.273166e-05, 2.0370965577, 529.690965),
        (1.324292e-05, 0.7424635635, 11506.76977),
        (1.199167e-05, 1.1096294432, 1577.343542),
        (8.57223e-06, 3.5084915696, 398.149003),
        (7.79786e-06, 1.1788265211, 5223.69392),
        (9.9025e-06, 5.2326812959, 5884.926847),
        (7.53141e-06, 2.5333905382, 5507.553239),
        (5.05264e-06, 4.5829256305, 18849.22755),
        (4.92379e-06, 4.2050663986, 775.522611),
        (2.84125e-06, 1.8986903419, 796.298007),
        (2.4281e-06, 0.3448114091, 5486.777843),
        (3.17087e-06, 5.8490195222, 11790.629089),
        (2.71039e-06, 0.3148860765, 10977.078805),
        (2.0616e-06, 4.8064660606, 2544.31442),
        (2.05385e-06, 1.8694781369, 5573.142801),
        (2.02261e-06, 2.4576779546, 6069.776755),
        (1.26184e-06, 1.0830263021, 20.775395),
        (1.55516e-06, 0.8330607381, 213.299095),
        (1.02851e-06, 0.6359984673, 4694.002955),
        (1.01724e-06, 4.2667982136, 7.113547),
        (9.9206e-07, 6.2099294026, 2146.165416),
        (1.32212e-06, 3.4111827556, 2942.463423),
        (8.5128e-07, 1.2987074302, 6275.962303),
        (7.4651e-07, 1.7550891616, 5088.62884),
        (1.01895e-06, 0.9756922182, 15720.838785),
        (8.4711e-07, 3.6708009302, 71430.695618),
        (7.3547e-07, 4.6792656548, 801.820931),
        (7.3874e-07, 3.5031944317, 3154.687085),
        (7.8756e-07, 3.0369831314, 12036.460735),
        (7.9637e-07, 1.807913307, 17260.154655),
        (8.5803e-07, 5.9832263126, 161000.685738),
        (5.6963e-07, 2.7843039804, 6286.598968),
        (6.1148e-07, 1.8183981102, 7084.896781),
        (6.9627e-07, 0.8329759697, 9437.762935),
        (5.6116e-07, 4.3869488078, 14143.495242),
        (6.2449e-07, 3.9776388059, 8827.39027),
        (5.1145e-07, 0.283068645, 5856.477659),
        (5.5577e-07, 3.4700600906, 6279.552732),
        (4.1036e-07, 5.368173514, 8429.241266),
        (5.1605e-07, 1.3328274698, 1748.016413),
        (5.1992e-07, 0.1891494583, 12139.553509),
        (4.9e-07, 0.4873506503, 1194.44701),
        (3.92e-07, 6.1683299502, 10447.38784),
        (3.5566e-07, 1.7759731469, 6812.766815),
        (3.677e-07, 6.0413385935, 10213.285546),
        (3.6596e-07, 2.5695523863, 1059.38193),
        (3.3291e-07, 0.5930949946, 17789.84562),
        (3.5954e-07, 1.708761119, 2352.866154),
        (4.0938e-07, 2.3985088171, 19651.048481),
        (3.0047e-07, 2.7397512393, 1349.86741),
        (3.0412e-07, 0.4429446414, 83996.847318),
        (2.3663e-07, 0.4847356776, 8031.092263),
        (2.3574e-07, 2.0652772005, 3340.612427),
        (2.4738e-07, 0.2148476214, 3.590429),
        (2.5352e-07, 3.164709534, 4690.479836),
        (2.282e-07, 5.2219788803, 4705.732308),
        (2.1419e-07, 1.4256373552, 16730.46369),
        (1.7481e-07, 4.5605290036, 135.06508),
        (1.9925e-07, 5.2220847127, 12168.002697),
        (2.03e-07, 0.3713379295, 283.859319),
        (1.6225e-07, 5.9883772256, 11769.853693),
        (1.9124e-07, 3.8221999695, 23581.258177),
        (1.8888e-07, 5.3862688097, 149854.400135),
        (1.7898e-07, 2.2149073565, 13367.972631),
        (1.2054e-07, 2.6222958835, 955.599742),
        (1.1287e-07, 0.1773932809, 4164.31199),
        (1.3971e-07, 4.4013814, 6681.224853),
        (1.3621e-07, 1.8893447141, 7632.94326),
        (1.2503e-07, 1.1305241221, 5.522924),
        (1.0498e-07, 5.3590951867, 1592.596014),
        (1.2003e-07, 1.003514567, 632.783739),
        (1.0827e-07, 0.3273452022, 103.092774),
        (1.0005e-07, 6.0291496328, 5746.271338),
        (1.0523e-07, 0.9387180551, 11926.254414),
    ),
    # T^1
    (
        (6283.31966747491, 0.0, 0.0),
        (0.00206058863, 2.6782345558, 6283.07585),
        (4.30343e-05, 2.6351265041, 12566.1517),
        (4.25264e-06, 1.5904698073, 3.523118),
    ),
    # T^2
    (
        (0.0005291887, 0.0, 0.0),
        (8.719837e-05, 1.0720966524, 6283.07585),
    ),
)

_R_SERIES = (
    # T^0
    (
        (1.00013988799, 0.0, 0.0),
        (0.01670699626, 3.0984635077, 6283.07585),
        (0.00013956023, 3.0552460962, 12566.1517),
        (3.08372e-05, 5.1984667438, 77713.771468),
        (1.628461e-05, 1.1738774901, 5753.384885),
        (1.575568e-05, 2.8468524582, 7860.419392),
        (9.24799e-06, 5.4529223408, 11506.76977),
        (5.42444e-06, 4.5640914978, 3930.209696),
        (4.7211e-06, 3.6610002215, 5884.926847),
        (3.2878e-06, 5.8998364648, 5223.69392),
        (3.45983e-06, 0.9636861769, 5507.553239),
        (3.06784e-06, 0.2986713951, 5573.142801),
        (1.74844e-06, 3.0119363653, 18849.22755),
        (2.43189e-06, 4.2734953615, 11790.629089),
        (2.11829e-06, 5.8471454031, 1577.343542),
        (1.85752e-06, 5.0219444718, 10977.078805),
        (1.09835e-06, 5.0551063629, 5486.777843),
    ),
    # T^1
    (
        (0.00103018608, 1.1074896959, 6283.07585),
    ),
)


def _series_sum(series, tau: float) -> float:
    """按 τ 的幂次累加截断 VSOP87 序列。"""
    total = 0.0
    power = 1.0
    for order in series:
        total += power * sum(a * math.cos(b + c * tau) for a, b, c in order)
        power *= tau
    return total


def _delta_t_seconds(year: int) -> float:
    """ΔT = TT − UT（秒），Espenak–Meeus 2005–2050 段多项式。"""
    t = year - 2000
    return 62.92 + 0.32217 * t + 0.005589 * t * t


def _nutation_dpsi(t: float) -> float:
    """章动 Δψ（度），Meeus 简化四项，精度约 0.5″。"""
    om = math.radians((125.04452 - 1934.136261 * t + 0.0020708 * t * t) % 360.0)
    ls = math.radians((280.4665 + 36000.7698 * t) % 360.0)
    lm = math.radians((218.3165 + 481267.8813 * t) % 360.0)
    return (
        -17.20 * math.sin(om)
        - 1.32 * math.sin(2.0 * ls)
        - 0.23 * math.sin(2.0 * lm)
        + 0.21 * math.sin(2.0 * om)
    ) / 3600.0


def apparent_sun_longitude(jd_ut: float) -> float:
    """给定真实 UT 儒略日，返回太阳地心视黄经（度，[0,360)）。

    计算链：VSOP87D 地球日心黄经 + 180° → FK5 修正 → 章动 Δψ →
    光行差 −20.489″/R。精度约 1~2″（时间上约 40~50 秒）。

    Args:
        jd_ut: 真实 UT 儒略日

    Returns:
        float: 太阳视黄经（度）
    """
    year = int((jd_ut - _J2000) / 365.25 + 2000.0)  # 仅用于 ΔT 估值，年份边界不影响结果
    jde = jd_ut + _delta_t_seconds(year) / 86400.0
    tau = (jde - _J2000) / 365250.0

    longitude = math.degrees(_series_sum(_L_SERIES, tau)) + 180.0 - 0.09033 / 3600.0
    radius = _series_sum(_R_SERIES, tau)
    longitude += _nutation_dpsi(tau * 10.0)
    longitude -= 20.489 / (3600.0 * radius)
    return longitude % 360.0


def _sun_longitude(jd: float) -> float:
    """兼容旧名：返回太阳地心视黄经（度）。"""
    return apparent_sun_longitude(jd)


def _angle_difference(target_angle: float, current_angle: float) -> float:
    """目标黄经与当前黄经之差，归一到 (−180°, 180°]。"""
    return (target_angle - current_angle + 180.0) % 360.0 - 180.0


@lru_cache(maxsize=2048)
def find_jieqi_julian_day(year: int, target_angle: float) -> float:
    """求指定年份内太阳视黄经达到 target_angle 的真实 UT 儒略日。

    先按日粗扫定位唯一交点（排除反日点 180° 处的假跳变），再二分到亚秒级。
    该函数是全项目节气时刻的唯一数值来源，calendar_utils 与 astronomy 均委托它，
    从根本上杜绝「两套节气结果互相打架」。

    Args:
        year: 公历年（取该年 1 月 1 日北京时起算 367 天窗口）
        target_angle: 目标太阳黄经（度）

    Returns:
        float: 真实 UT 儒略日

    Raises:
        ValueError: 窗口内未找到交点（数据异常）
    """
    start = julian_day_from_beijing_parts(year, 1, 1, 0.0)
    prev_diff = _angle_difference(target_angle, apparent_sun_longitude(start))
    prev_jd = start
    lo = hi = None
    for step in range(1, 368):
        jd = start + step
        cur_diff = _angle_difference(target_angle, apparent_sun_longitude(jd))
        # 真实交点：diff 由正转负且幅度很小；反日点跳变处 |diff|≈180，需排除
        if prev_diff > 0 >= cur_diff and prev_diff < 90:
            lo, hi = prev_jd, jd
            break
        prev_jd, prev_diff = jd, cur_diff

    if lo is None:
        raise ValueError(f'{year} 年未找到黄经 {target_angle}° 的交点')

    for _ in range(60):
        mid = (lo + hi) / 2.0
        if mid == lo or mid == hi:
            break
        if _angle_difference(target_angle, apparent_sun_longitude(mid)) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def find_jieqi_approx(
    year: int,
    target_angle: float,
    center_day: int = 35,
    half_range: int = 30,
) -> datetime:
    """查找指定黄经角度对应的节气时刻（北京时间）。

    历史上本函数用 center_day/half_range 做局部窗口二分；现在统一委托
    find_jieqi_julian_day 做全年精确搜索，两个参数仅为兼容旧调用保留。

    Args:
        year: 公历年份
        target_angle: 目标太阳黄经（度），如立春 315°
        center_day: 兼容保留，不再生效
        half_range: 兼容保留，不再生效

    Returns:
        datetime: 节气时刻（北京时间 naive datetime）
    """
    del center_day, half_range  # 明确标注：仅兼容签名，不参与计算
    return beijing_datetime_from_julian_day(find_jieqi_julian_day(year, target_angle))


def _jd_to_datetime(jd: float) -> datetime:
    """兼容旧名：真实 UT 儒略日 → 北京时间 datetime。"""
    return beijing_datetime_from_julian_day(jd)


def _julian_day_from_date(year: int, month: int, day: int) -> float:
    """兼容旧名：北京日期 0 点 → 真实 UT 儒略日。"""
    return julian_day_from_beijing_parts(year, month, day, 0.0)
