"""
core/bazi_batch.py — 八字批量排盘引擎（NumPy 向量化）

设计目标：
- 支持批量排盘（10 万条 < 2 秒）
- 核心算法纯函数化，便于单元测试
- 输入输出均为 NumPy ndarray，减少 Python 循环开销

算法依据：
- 年柱：(year - 4) % 60 → YEAR_GANZHI[idx]，立春为界（简化版）
- 月柱：五虎遁（根据年干推月干）
- 日柱：儒略日算法 + -6 偏移修正（对齐真实历法）
- 时柱：五鼠遁（根据日干推时干）
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

# 延迟导入，避免模块加载时 TIAN_GAN 等常量尚未初始化
# _lazy_init 在函数体内惰性调用（第 28 行），模块级不预加载。


def _get_maps():
    """获取干支映射表（懒加载，首次调用时自动初始化数据库）。"""
    from core.calendar_utils import _lazy_init
    _lazy_init()
    # 注意：必须在 _lazy_init() 之后导入，否则得到的是 None
    from core.calendar_utils import TIAN_GAN, DI_ZHI, YEAR_GANZHI, MONTH_GAN_RULES
    return TIAN_GAN, DI_ZHI, YEAR_GANZHI, MONTH_GAN_RULES


# ================================================================
# 年柱（向量化）
# ================================================================

def batch_year_ganzhi(years: np.ndarray) -> np.ndarray:
    """批量计算年干支（纯公式，无循环）。

    Args:
        years: shape (N,) 的 int ndarray，公历年份

    Returns:
        shape (N,) 的 str ndarray，干支字符串
    """
    _, _, YEAR_GANZHI, _ = _get_maps()
    idx = ((years.astype(int) - 4) % 60 + 60) % 60
    return np.array([YEAR_GANZHI[i] for i in idx])


# ================================================================
# 月柱（向量化）
# ================================================================

def batch_month_ganzhi(year_gans: np.ndarray, month_zhis: np.ndarray) -> np.ndarray:
    """批量计算月干支（五虎遁）。

    Args:
        year_gans: shape (N,) 的 str ndarray，年干
        month_zhis: shape (N,) 的 str ndarray，月支（寅=0, ..., 丑=11）

    Returns:
        shape (N,) 的 str ndarray，月柱干支
    """
    TIAN_GAN, DI_ZHI, _, MONTH_GAN_RULES = _get_maps()
    result = np.empty(len(year_gans), dtype=object)
    # 按年干分组处理，减少内层循环
    for key, gan_list in MONTH_GAN_RULES.items():
        mask = np.isin(year_gans, list(key))
        if not np.any(mask):
            continue
        month_zhi_idx = np.array([DI_ZHI.index(z) for z in month_zhis[mask]])
        # 转换：月支索引（子=0）→ 五虎遁起始（寅=0）
        gan_idx = (month_zhi_idx - 2) % 12
        # 逐个计算（月干依赖年干，无法完全向量化）
        for i, idx in enumerate(np.where(mask)[0]):
            result[idx] = gan_list[gan_idx[i]] + month_zhis[idx]
    return result


# ================================================================
# 日柱（向量化）
# ================================================================

def batch_day_ganzhi(
    years: np.ndarray,
    months: np.ndarray,
    days: np.ndarray,
) -> np.ndarray:
    """批量计算日干支（儒略日算法，向量化）。

    算法：JD = floor(365.25*(Y+4716)) + floor(30.6001*(M+1)) + D + B - 1524.5
          idx = (JD - 2451544.5 - 6) % 60
    """
    _, _, YEAR_GANZHI, _ = _get_maps()
    y = years.astype(float).copy()
    m = months.astype(float).copy()
    d = days.astype(float).copy()

    # 1月和2月当作上一年的13/14月
    adjust = m <= 2
    y[adjust] -= 1
    m[adjust] += 12

    a = np.floor(y / 100).astype(float)
    b = 2.0 - a + np.floor(a / 4.0)

    jd = (
        np.floor(365.25 * (y + 4716))
        + np.floor(30.6001 * (m + 1))
        + d
        + b
        - 1524.5
    )

    base_jd = 2451544.5
    delta = jd - base_jd
    # 对 60 取模（处理负数）
    raw_idx = ((delta % 60 + 60) % 60).astype(int)
    idx = (raw_idx - 6) % 60

    return np.array([YEAR_GANZHI[i] for i in idx])


# ================================================================
# 时柱（向量化）
# ================================================================

# 五鼠遁：日干 → 时干起点表
# 甲己→甲子起，乙庚→丙子起，丙辛→戊子起，丁壬→庚子起，戊癸→壬子起
_SHISHU_DUN: Dict[str, int] = {
    '甲': 0, '己': 0,
    '乙': 2, '庚': 2,
    '丙': 4, '辛': 4,
    '丁': 6, '壬': 6,
    '戊': 8, '癸': 8,
}


def batch_hour_ganzhi(day_gans: np.ndarray, hour_zhis: np.ndarray) -> np.ndarray:
    """批量计算时干支（五鼠遁）。

    Args:
        day_gans: shape (N,) 的 str ndarray，日干
        hour_zhis: shape (N,) 的 str ndarray，时支（子=0, ..., 亥=11）

    Returns:
        shape (N,) 的 str ndarray，时柱干支
    """
    TIAN_GAN, DI_ZHI, _, _ = _get_maps()
    hour_zhi_idx = np.array([DI_ZHI.index(z) for z in hour_zhis])
    # 时干起点（根据日干）
    start_gan = np.array([_SHISHU_DUN.get(g, 0) for g in day_gans])
    # 时干 = (start_gan + hour_zhi_idx) % 10
    result_gan_idx = (start_gan + hour_zhi_idx) % 10
    result = np.empty(len(day_gans), dtype=object)
    for i in range(len(result)):
        result[i] = TIAN_GAN[result_gan_idx[i]] + hour_zhis[i]
    return result


# ================================================================
# 综合批量排盘
# ================================================================

def batch_bazi_calculate(
    years: np.ndarray,
    months: np.ndarray,
    days: np.ndarray,
    hours: np.ndarray,
    month_zhis: Optional[np.ndarray] = None,
    hour_zhis: Optional[np.ndarray] = None,
) -> List[Dict[str, str]]:
    """批量八字排盘，返回列表。

    Args:
        years: shape (N,) int，公历年
        months: shape (N,) int，公历月
        days: shape (N,) int，公历日
        hours: shape (N,) int，小时（0-23）
        month_zhis: 可选，shape (N,) str，月支（如不传则自动从 hours 推算）
        hour_zhis: 可选，shape (N,) str，时支（如不传则自动从 hours 推算）

    Returns:
        长度 N 的字典列表，每项含 year_pillar / month_pillar / day_pillar / hour_pillar
    """
    n = len(years)
    if month_zhis is None:
        month_zhis = np.array([''] * n, dtype=object)
    if hour_zhis is None:
        hour_zhis = np.array([''] * n, dtype=object)

    # 推算月支（基于月份）
    MONTH_ZHI_MAP = {1: '寅', 2: '卯', 3: '辰', 4: '巳', 5: '午', 6: '未',
                     7: '申', 8: '酉', 9: '戌', 10: '亥', 11: '子', 12: '丑'}
    if np.all(month_zhis == ''):
        month_zhis = np.array([MONTH_ZHI_MAP.get(int(m), '寅') for m in months])

    # 推算时支（基于小时）
    HOUR_ZHI_MAP = {0: '子', 1: '子', 2: '丑', 3: '丑', 4: '寅', 5: '寅',
                    6: '卯', 7: '卯', 8: '辰', 9: '辰', 10: '巳', 11: '巳',
                    12: '午', 13: '午', 14: '未', 15: '未', 16: '申', 17: '申',
                    18: '酉', 19: '酉', 20: '戌', 21: '戌', 22: '亥', 23: '亥'}
    if np.all(hour_zhis == ''):
        hour_zhis = np.array([HOUR_ZHI_MAP.get(int(h), '子') for h in hours])

    # 批量计算四柱
    year_pillars = batch_year_ganzhi(years)
    day_pillars = batch_day_ganzhi(years, months, days)
    month_pillars = batch_month_ganzhi(
        np.array([g[:1] for g in year_pillars]), month_zhis
    )
    hour_pillars = batch_hour_ganzhi(
        np.array([g[:1] for g in day_pillars]), hour_zhis
    )

    # 组合结果
    results = []
    for i in range(n):
        results.append({
            'year_pillar': year_pillars[i],
            'month_pillar': month_pillars[i],
            'day_pillar': day_pillars[i],
            'hour_pillar': hour_pillars[i],
        })
    return results


# ================================================================
# 性能基准
# ================================================================

def benchmark_batch_calculate(n: int = 10000) -> Dict:
    """性能基准测试。

    Args:
        n: 排盘数量

    Returns:
        {'elapsed_seconds': float, 'n': int, 'per_record_ms': float}
    """
    import time
    years = np.random.randint(1900, 2100, size=n)
    months = np.random.randint(1, 13, size=n)
    days = np.random.randint(1, 29, size=n)
    hours = np.random.randint(0, 24, size=n)

    t0 = time.perf_counter()
    results = batch_bazi_calculate(years, months, days, hours)
    elapsed = time.perf_counter() - t0

    return {
        'elapsed_seconds': round(elapsed, 4),
        'n': n,
        'per_record_ms': round(elapsed / n * 1000, 4),
        'results_sample': results[:3],
    }


if __name__ == '__main__':
    # 快速性能测试
    for n in [100, 1000, 10000, 100000]:
        bench = benchmark_batch_calculate(n)
        print(f"n={bench['n']:>6}: {bench['elapsed_seconds']:.4f}s  "
              f"({bench['per_record_ms']:.4f}ms/条)")
