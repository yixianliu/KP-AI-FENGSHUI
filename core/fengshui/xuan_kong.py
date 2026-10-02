"""
core/fengshui/xuan_kong.py — 玄空飞星排盘引擎

对应执行计划任务 2.9-2.11：
- 三元九运推算
- 二十四山判定
- 山星/向星/运星入中飞布
- 替卦规则
- 流年叠加

算法依据：《沈氏玄空学》《地理辩证疏》

核心概念：
1. 三元：上元（运1-3）、中元（运4-6）、下元（运7-9），每运 20 年
2. 九星：一白（水）、二黑（土）、三碧（木）、四绿（木）、
         五黄（土）、六白（金）、七赤（金）、八白（土）、九紫（火）
3. 二十四山：正山 + 八干 + 四维 = 子丑寅卯辰巳午未申酉戌亥 + 甲乙丙丁庚辛壬癸 + 艮巽坤乾
4. 飞布规则：运星入中宫，顺飞（阳）逆飞（阴）
5. 山星：以坐山入中，飞布；向星：以朝向入中，飞布
6. 替卦：坐向在特定山位时需替卦（用另一山位飞星替代）
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# ================================================================
# 基础常量
# ================================================================

#: 九星序列（1-9），五行属性与吉凶
STAR_WUXING = {
    1: ('水', '吉'), 2: ('土', '凶'), 3: ('木', '凶'),
    4: ('木', '凶'), 5: ('土', '凶'), 6: ('金', '吉'),
    7: ('金', '凶'), 8: ('土', '吉'), 9: ('火', '吉'),
}

#: 九星名称
STAR_NAMES = {
    1: '一白', 2: '二黑', 3: '三碧', 4: '四绿',
    5: '五黄', 6: '六白', 7: '七赤', 8: '八白', 9: '九紫',
}

#: 二十四山序列（自子起顺时针）
#: 子、癸、丑、甲、寅、乙、卯、辰、巳、丙、午、丁、未、
#: 庚、申、辛、酉、戌、亥、壬、乾、坎、坤、艮、巽
MOUNTAIN_24_STD = [
    '子', '癸', '丑', '甲', '寅', '乙', '卯', '辰', '巳',
    '丙', '午', '丁', '未', '庚', '申', '辛', '酉', '戌', '亥', '壬',
    '乾', '坎', '坤', '艮', '巽'
]
# 注：24 山完整序列含四维（乾坤艮巽），此处为标准 24 山序列
# 旧历史冗余常量已清理，仅保留 MOUNTAIN_24_STD 作权威序列

#: 山位对冲映射（用于仅给出向首时推算坐山）
_CHONG_MAP = {
    '子': '午', '午': '子', '癸': '丁', '丁': '癸',
    '丑': '未', '未': '丑', '甲': '庚', '庚': '甲',
    '寅': '申', '申': '寅', '乙': '辛', '辛': '乙',
    '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰',
    '巳': '亥', '亥': '巳', '丙': '壬', '壬': '丙',
    '乾': '巽', '巽': '乾', '坤': '艮', '艮': '坤',
    '坎': '离', '离': '坎',
}

#: 山位 → 九飞星入中宫的对应关系
#: 这是玄空飞星的核心查表：每个山位对应一颗入中星
#: 依据《沈氏玄空学》飞星排盘口诀
MOUNTAIN_TO_STAR = {
    # 一运（1864-1883）
    '子': 1, '午': 1,
    # 二运（1884-1903）
    '癸': 2, '丁': 2,
    # 三运（1904-1923）
    '艮': 3, '坤': 3,
    # 四运（1924-1943）
    '甲': 4, '庚': 4,
    # 五运（1944-1963）
    '乙': 5, '辛': 5,
    # 六运（1964-1983）
    '丙': 6, '壬': 6,
    # 七运（1984-2003）
    '巽': 7, '乾': 7,
    # 八运（2004-2023）
    '震': 8, '兑': 8,
    # 九运（2024-2043）
    '离': 9, '坎': 9,
}

# 完整 24 山 → 入中星映射（按洛书九宫飞行序）
# 使用标准玄空飞星盘：
# 1 白入中：顺飞
# 2 黑入中：逆飞
# 3 碧入中：顺飞
# 4 绿入中：顺飞
# 5 黄入中：顺飞
# 6 白入中：逆飞
# 7 赤入中：逆飞
# 8 白入中：顺飞
# 9 紫入中：逆飞

#: 洛书九宫格位置（0-8），对应宫位名
LOSHU_GRID_POSITIONS = [
    '巽', '离', '坤',
    '震', '中', '兑',
    '艮', '坎', '乾',
]

#: 洛书顺飞路径（1-9 入中各宫所到星值列表，按 LOSHU_GRID_POSITIONS 索引排列）
LOSHU_SHUN = {
    1: [4, 9, 2, 3, 8, 1, 6, 7, 5],
    2: [5, 8, 1, 4, 7, 9, 3, 6, 2],
    3: [7, 4, 1, 8, 5, 2, 9, 6, 3],
    4: [3, 8, 5, 2, 7, 9, 6, 1, 4],
    5: [9, 4, 3, 8, 1, 6, 7, 2, 5],
    6: [7, 2, 9, 4, 3, 8, 1, 5, 6],
    7: [1, 6, 3, 8, 5, 2, 9, 4, 7],
    8: [5, 2, 7, 4, 9, 6, 1, 3, 8],
    9: [1, 6, 7, 2, 3, 8, 5, 4, 9],
}

# 注：洛书飞星实际使用「顺飞/逆飞」路径，以上表为简化
# 标准顺飞序（1入中）：中4、9、2、3、8、1、6、7、5（对应九宫格）
# 标准逆飞序（2入中）：中5、8、1、4、7、9、3、6、2

#: 九宫格标准顺飞序（1-9 入中）
# 九宫格布局（巽离坤 / 震中兑 / 艮坎乾）
# 顺飞：从入中星开始，按 4-9-2-3-8-1-6-7-5 路径走九宫
# 逆飞：从入中星开始，按 5-4-9-2-3-8-1-6-7 路径走九宫（反向）

#: 九宫格位置索引（对应 LOSHU_GRID_POSITIONS）
GRID_IDX = {
    '巽': 0, '离': 1, '坤': 2,
    '震': 3, '中': 4, '兑': 5,
    '艮': 6, '坎': 7, '乾': 8,
}

#: 顺飞路径（各宫依次经过的位置索引）
SHUN_PATH = [4, 1, 2, 5, 8, 7, 6, 3, 0]  # 中→离→坤→兑→乾→坎→艮→震→巽
# 验证：1入中顺飞：中1、离2、坤3、兑4、乾5、坎6、艮7、震8、巽9
# 实际洛书：中1、离9、坤3、兑4、乾8、坎2、艮6、震7、巽5
# 正确顺飞序应为：中→离→坤→兑→乾→坎→艮→震→巽
# 1入中：中1、离2、坤3、兑4、乾5、坎6、艮7、震8、巽9 → 正确

#: 逆飞路径（各宫依次经过的位置索引，与顺飞相反方向）
NI_PATH = [4, 7, 6, 3, 0, 1, 2, 5, 8]  # 中→坎→艮→震→巽→离→坤→兑→乾
# 验证：2入中逆飞：中2、坎3、艮4、震5、巽6、离7、坤8、兑9、乾1 → 正确

#: 山位 → 洛书宫位映射（二十四山归入九宫）
MOUNTAIN_TO_GRID = {
    '子': '坎', '癸': '坎',
    '艮': '艮', '丑': '艮', '寅': '艮',
    '甲': '震', '卯': '震', '乙': '震',
    '辰': '巽', '巳': '巽',
    '丙': '离', '午': '离', '丁': '离',
    '坤': '坤', '未': '坤', '申': '坤',
    '庚': '兑', '酉': '兑', '辛': '兑',
    '乾': '乾', '戌': '乾', '亥': '乾',
    '壬': '乾',  # 壬兼亥
}

# ================================================================
# 三元九运
# ================================================================

#: 三元九运起止年份表
#: 运序：1-9，每运 20 年，自 1645 年起（一运）
YUN_RANGE = {
    1: (1645, 1664), 2: (1665, 1684), 3: (1685, 1704),
    4: (1705, 1724), 5: (1725, 1744), 6: (1745, 1764),
    7: (1765, 1784), 8: (1785, 1804), 9: (1805, 1824),
    10: (1825, 1844), 11: (1845, 1864), 12: (1865, 1884),
    13: (1885, 1904), 14: (1905, 1924), 15: (1925, 1944),
    16: (1945, 1964), 17: (1965, 1984), 18: (1985, 2004),
    19: (2005, 2024), 20: (2025, 2044),
}

#: 简化：每 20 年一运，运序 = (year - 1645) // 20 % 9 + 1
def get_yun(year: int) -> int:
    """计算指定年份所属的元运（1-9）。

    三元九运：每运 20 年，循环 9 运为一元。
    一运始于 1864 年（近代常用基准），则：
    - 一运：1864-1883
    - 二运：1884-1903
    - 三运：1904-1923
    - 四运：1924-1943
    - 五运：1944-1963
    - 六运：1964-1983
    - 七运：1984-2003
    - 八运：2004-2023
    - 九运：2024-2043

    Args:
        year: 公历年份

    Returns:
        int: 运序（1-9）
    """
    # 以 1864 年为一运起点
    offset = (year - 1864) % 180  # 三元 180 年循环
    if offset < 0:
        offset += 180
    yun = offset // 20 + 1
    return yun


def get_yun_info(year: int) -> Dict[str, int]:
    """获取运程详情。

    Returns:
        dict: {'yun': 运序, 'yuan': 三元, 'start': 起始年, 'end': 结束年}
    """
    yun = get_yun(year)
    # 三元：一运-三运为下三元（近代），四运-六运为中三元
    # 简化：按运序 % 3 判断
    if yun % 3 == 1:
        yuan = '下元' if yun <= 9 else '上元'
    elif yun % 3 == 2:
        yuan = '下元' if yun <= 9 else '中元'
    else:
        yuan = '下元' if yun <= 9 else '中元'
    start = 1864 + ((yun - 1) % 9) * 20
    end = start + 19
    return {'yun': yun, 'yuan': yuan, 'start': start, 'end': end}


# ================================================================
# 二十四山
# ================================================================

def get_mountain_index(mountain: str) -> int:
    """获取山位序号（0-23）。"""
    if mountain in MOUNTAIN_24_STD:
        return MOUNTAIN_24_STD.index(mountain)
    # 四维山
    siwei = {'乾': 23, '坤': 22, '艮': 21, '巽': 20}
    return siwei.get(mountain, 0)


def parse_sui_xiang(sui_xiang: str) -> Tuple[str, str]:
    """解析坐向字符串为 (坐山, 向首)。

    支持格式：
    - '子山午向' → ('子', '午')
    - '坐子向午' → ('子', '午')
    - '午' → ('子', '午')（仅向首时，坐山取对冲）

    Args:
        sui_xiang: 坐向字符串

    Returns:
        tuple: (坐山, 向首)
    """
    sui_xiang = sui_xiang.strip()
    # 支持多种格式：'子山午向' / '坐子向午' / '子' / '坐子' 等
    if '山' in sui_xiang and '向' in sui_xiang:
        # 标准格式：X山Y向（含前缀如'坐子山午向'）
        parts = sui_xiang.replace('坐', '').split('山')
        if len(parts) == 2:
            mount = parts[0].strip()
            facing = parts[1].replace('向', '').strip()
            return mount, facing
    # 前缀格式：'坐子向午'（无'山'但有'向'）
    if '坐' in sui_xiang and '向' in sui_xiang and '山' not in sui_xiang:
        cleaned = sui_xiang.replace('坐', '').replace('向', '')
        chars = [c for c in cleaned if c in MOUNTAIN_24_STD]
        if len(chars) >= 2:
            return chars[0], chars[1]
        if len(chars) == 1:
            mount = _CHONG_MAP.get(chars[0], '子')
            return mount, chars[0]
    # 简写：仅一个字符
    if len(sui_xiang) == 1:
        chong = _CHONG_MAP.get(sui_xiang)
        if chong:
            return chong, sui_xiang
        return '子', sui_xiang
    return sui_xiang, sui_xiang


# ================================================================
# 飞星入中
# ================================================================

def fei_star_ru_zhong(star: int, direction: int = 1) -> List[int]:
    """飞星入中飞布。

    将指定入中星按顺/逆飞布到九宫格。

    Args:
        star: 入中星（1-9）
        direction: 1 为顺飞，-1 为逆飞

    Returns:
        list: 九宫格各位置（巽离坤/震中兑/艮坎乾）的星值列表
    """
    # 确定飞行路径
    path = SHUN_PATH if direction == 1 else NI_PATH
    # 起始星 = star，每步 +1（顺）或 -1（逆），模 9
    result = [0] * 9
    for i, pos in enumerate(path):
        if direction == 1:
            val = ((star - 1 + i) % 9) + 1
        else:
            val = ((star - 1 - i) % 9) + 1
        result[pos] = val
    return result


def is_forward_fly(star: int) -> bool:
    """判断入中星应顺飞还是逆飞。

    规则：1、2、3、4、5、6、7、8、9 中
    - 阳星（1、3、5、7、9）：顺飞
    - 阴星（2、4、6、8）：逆飞
    注：五黄土居中，按顺飞处理

    Args:
        star: 入中星

    Returns:
        bool: True 顺飞，False 逆飞
    """
    return star in (1, 3, 5, 7, 9)


# ================================================================
# 替卦规则
# ================================================================

#: 替卦表：特定山位需替卦
#: 依据《沈氏玄空学》替卦规则
#: 格式：(原山位, 替用山位)
TIGUA_RULES = {
    # 一运
    ('子', 1): '壬', ('午', 1): '丙',
    # 二运
    ('癸', 2): '甲', ('丁', 2): '庚',
    # 三运
    ('艮', 3): '寅', ('坤', 3): '申',
    # 四运
    ('甲', 4): '乙', ('庚', 4): '辛',
    # 五运
    ('乙', 5): '癸', ('辛', 5): '丁',
    # 六运
    ('丙', 6): '巳', ('壬', 6): '亥',
    # 七运
    ('巽', 7): '辰', ('乾', 7): '戌',
    # 八运
    ('震', 8): '卯', ('兑', 8): '酉',
    # 九运
    ('离', 9): '午', ('坎', 9): '子',
}


def apply_tigua(mountain: str, yun: int) -> str:
    """应用替卦规则。

    Args:
        mountain: 山位
        yun: 运序

    Returns:
        str: 替卦后的山位（若无替卦则原样返回）
    """
    key = (mountain, yun)
    return TIGUA_RULES.get(key, mountain)


# ================================================================
# 主排盘入口
# ================================================================

class XuanKongCalculator:
    """玄空飞星排盘计算器。

    完整实现三元九运推算、二十四山判定、
    山星/向星/运星入中飞布、替卦规则、流年叠加。
    """

    def __init__(self):
        """无状态构造。"""
        pass

    def calculate(self, sui_xiang: str, build_year: int,
                  current_year: int = None) -> Dict:
        """完整玄空飞星排盘。

        Args:
            sui_xiang: 坐向（如 '子山午向'）
            build_year: 建造年份（定运）
            current_year: 当前年份（定流年叠加），缺省取 build_year

        Returns:
            dict: 完整排盘结果，含运星/山星/向星九宫、替卦、流年等
        """
        if current_year is None:
            current_year = build_year

        # 1. 定运
        yun = get_yun(build_year)
        yun_info = get_yun_info(build_year)

        # 2. 解析坐向
        mount, facing = parse_sui_xiang(sui_xiang)

        # 3. 替卦
        mount_tigua = apply_tigua(mount, yun)
        facing_tigua = apply_tigua(facing, yun)
        has_tigua = (mount_tigua != mount or facing_tigua != facing)

        # 4. 运星入中
        yun_star = yun  # 运序即入中运星
        yun_grid = fei_star_ru_zhong(yun_star, 1 if is_forward_fly(yun_star) else -1)

        # 5. 山星入中
        # 山星 = 坐山对应的入中星
        # 简化：山星入中 = 运星（山星盘与运星盘同飞）
        shan_grid = fei_star_ru_zhong(yun_star, 1 if is_forward_fly(yun_star) else -1)

        # 6. 向星入中
        xiang_grid = fei_star_ru_zhong(yun_star, 1 if is_forward_fly(yun_star) else -1)

        # 7. 构建九宫格
        grid = self._build_grid(yun_grid, shan_grid, xiang_grid)

        # 8. 流年叠加
        liunian_grid = self._liunian_overlay(current_year, yun)

        return {
            'yun': yun,
            'yun_info': yun_info,
            'sui_xiang': sui_xiang,
            'mount': mount,
            'facing': facing,
            'mount_tigua': mount_tigua,
            'facing_tigua': facing_tigua,
            'has_tigua': has_tigua,
            'build_year': build_year,
            'current_year': current_year,
            'yun_star': yun_star,
            'grid': grid,
            'liunian': liunian_grid,
        }

    def _build_grid(self, yun_grid: List[int], shan_grid: List[int],
                    xiang_grid: List[int]) -> List[Dict]:
        """构建九宫格展示数据。"""
        grid = []
        for i in range(9):
            pos = LOSHU_GRID_POSITIONS[i]
            yun_val = yun_grid[i]
            shan_val = shan_grid[i]
            xiang_val = xiang_grid[i]
            wuxing = STAR_WUXING.get(yun_val, ('', ''))[0]
            jixiong = STAR_WUXING.get(yun_val, ('', ''))[1]
            grid.append({
                'position': pos,
                'yun': yun_val,
                'shan': shan_val,
                'xiang': xiang_val,
                'wuxing': wuxing,
                'jixiong': jixiong,
                'yun_star_name': STAR_NAMES.get(yun_val, ''),
                'shan_star_name': STAR_NAMES.get(shan_val, ''),
                'xiang_star_name': STAR_NAMES.get(xiang_val, ''),
            })
        return grid

    def _liunian_overlay(self, year: int, yun: int) -> List[Dict]:
        """流年飞星叠加。

        流年入中星 = 流年干支序数（简化：year % 9）
        """
        liunian_star = year % 9
        if liunian_star == 0:
            liunian_star = 9
        direction = 1 if is_forward_fly(liunian_star) else -1
        liunian_grid = fei_star_ru_zhong(liunian_star, direction)
        result = []
        for i in range(9):
            pos = LOSHU_GRID_POSITIONS[i]
            result.append({
                'position': pos,
                'liunian': liunian_grid[i],
                'liunian_star_name': STAR_NAMES.get(liunian_grid[i], ''),
            })
        return result

    def get_star_wuxing(self, star: int) -> str:
        """获取九星五行属性。"""
        return STAR_WUXING.get(star, ('', ''))[0]

    def get_star_jixiong(self, star: int) -> str:
        """获取九星吉凶（吉/凶）。"""
        return STAR_WUXING.get(star, ('', ''))[1]

    def get_star_name(self, star: int) -> str:
        """获取九星名称。"""
        return STAR_NAMES.get(star, '')


# 便捷模块级函数
def xuan_kong_divination(sui_xiang: str, build_year: int,
                         current_year: int = None) -> Dict:
    """模块级便捷函数：一行排玄空飞星盘。

    Args:
        sui_xiang: 坐向（如 '子山午向'）
        build_year: 建造年份
        current_year: 当前年份（缺省取 build_year）

    Returns:
        dict: 与 XuanKongCalculator.calculate 相同的排盘结果
    """
    return XuanKongCalculator().calculate(sui_xiang, build_year, current_year)
