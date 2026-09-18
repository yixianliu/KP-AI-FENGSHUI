"""core/bazi — 八字四柱算法包（排盘计算 + 分析器 + 兼容层）。

本包聚合了八字系统的全部计算与分析模块：
  - bazi_calculator : 八字计算总入口（聚合 5 个分析器）
  - wuxing / shishen / mingli : 五行 / 十神 / 命理分析器
  - geju_analyzer / yunshi / yuncheng : 格局 / 大运流年 / 运程分析
  - bazi_types / bazi_batch : 命局类型词表 / 批量计算
  - _baazi_compat : 旧 core.baazi 兼容层
  - pillar : 四柱纯函数（五虎遁 / 五鼠遁）
"""

from core.bazi.pillar import (
    TG,
    DZ,
    JIAZI,
    YANG_GAN,
    WU_HU_DUN,
    WU_SHU_DUN,
    calc_year_pillar,
    calc_month_pillar,
    calc_day_pillar,
    calc_hour_pillar,
    hour_zhi_from_hour,
    find_li_chun,
    get_lunar_year,
    get_month_zhi,
    calculate_pillars,
    PillarEngine,
)

__all__ = [
    'TG', 'DZ', 'JIAZI', 'YANG_GAN',
    'WU_HU_DUN', 'WU_SHU_DUN',
    'calc_year_pillar', 'calc_month_pillar',
    'calc_day_pillar', 'calc_hour_pillar',
    'hour_zhi_from_hour', 'find_li_chun',
    'get_lunar_year', 'get_month_zhi',
    'calculate_pillars', 'PillarEngine',
]
