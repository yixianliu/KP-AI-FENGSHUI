# -*- coding: utf-8 -*-
"""
core/ganzhi_constants.py — 干支静态常量的唯一权威源

【为什么需要这个模块】
天干、地支是命理体系中恒定不变的基础序列。在重构前，这两张表被硬编在
data_validator、liuren、meihua、_baazi_compat、database_manager 以及多个 UI
组件里，共出现 8 次。任何一处笔误都会导致索引错位且极难排查。
本模块把它们收敛为单一定义，所有模块统一从此导入。

【与 calendar_utils 的分工】
- ``core.calendar_utils.TIAN_GAN / DI_ZHI``：从 SQLite 知识库懒加载，
  携带五行、阴阳、方位等**扩展属性**，初始值为 None，必须先 ``_lazy_init()``。
- 本模块：**纯静态字面量**，导入即可用、无数据库依赖，
  适合做索引计算、下拉框选项、参数校验等不需要扩展属性的场景。

两者的序列顺序保证完全一致，可安全互换索引。
"""
from __future__ import annotations

# ---------------------------------------------------------------- 基础序列

#: 十天干，索引 0-9，顺序固定不可调整（大量取模运算依赖该顺序）
TIAN_GAN: list[str] = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']

#: 十二地支，索引 0-11，顺序固定不可调整（时辰、生肖、月建均按此序推算）
DI_ZHI: list[str] = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

#: 阳干集合，用于十二长生顺行/逆行判定（阳干顺行、阴干逆行）
GAN_YANG: frozenset[str] = frozenset({'甲', '丙', '戊', '庚', '壬'})

#: 阳支集合，用于干支配对合法性校验（阳干只配阳支、阴干只配阴支）
ZHI_YANG: frozenset[str] = frozenset({'子', '寅', '辰', '午', '申', '戌'})

# ---------------------------------------------------------------- 索引映射

#: 天干 -> 序号，避免各处重复 ``TIAN_GAN.index(x)`` 的线性查找
GAN_INDEX: dict[str, int] = {gan: i for i, gan in enumerate(TIAN_GAN)}

#: 地支 -> 序号
ZHI_INDEX: dict[str, int] = {zhi: i for i, zhi in enumerate(DI_ZHI)}


def build_sixty_jiazi() -> list[str]:
    """生成六十甲子序列。

    规则：天干循环 10 位、地支循环 12 位，同步递进 60 步后回到「甲子」，
    因此第 i 组为 ``TIAN_GAN[i % 10] + DI_ZHI[i % 12]``。

    Returns:
        list[str]: 长度 60 的干支组合列表，首项「甲子」、末项「癸亥」。
    """
    return [TIAN_GAN[i % 10] + DI_ZHI[i % 12] for i in range(60)]


#: 六十甲子完整序列（模块导入时一次性生成，后续直接复用）
SIXTY_JIAZI: list[str] = build_sixty_jiazi()


def is_valid_gan(char: str) -> bool:
    """判断字符是否为合法天干。

    Args:
        char: 待校验的单字。

    Returns:
        bool: 属于十天干返回 True。
    """
    return char in GAN_INDEX


def is_valid_zhi(char: str) -> bool:
    """判断字符是否为合法地支。

    Args:
        char: 待校验的单字。

    Returns:
        bool: 属于十二地支返回 True。
    """
    return char in ZHI_INDEX


def is_valid_ganzhi(pillar: str) -> bool:
    """判断两字字符串是否为合法干支组合。

    合法条件有三：长度为 2、首字是天干、次字是地支。
    注意本函数不校验阴阳配对，如需严格校验请另行结合
    :data:`GAN_YANG` 与 :data:`ZHI_YANG`。

    Args:
        pillar: 形如「甲子」的两字干支。

    Returns:
        bool: 合法返回 True。
    """
    return len(pillar) == 2 and is_valid_gan(pillar[0]) and is_valid_zhi(pillar[1])
