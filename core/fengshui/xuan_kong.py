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

#: 二十四山序列（自正北「子」起顺时针，每山 15°）
#: 子、癸、丑、艮、寅、甲、卯、乙、辰、巽、巳、丙、
#: 午、丁、未、坤、申、庚、酉、辛、戌、乾、亥、壬
#: 注：四维为乾、坤、艮、巽；「坎」「离」是卦名（坎=子宫、离=午宫），不属于二十四山
MOUNTAIN_24_STD = [
    '子', '癸', '丑', '艮', '寅', '甲', '卯', '乙', '辰', '巽',
    '巳', '丙', '午', '丁', '未', '坤', '申', '庚', '酉', '辛',
    '戌', '乾', '亥', '壬',
]
MOUNTAIN_SET = frozenset(MOUNTAIN_24_STD)

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

#: 洛书九宫格位置（0-8），对应宫位名
LOSHU_GRID_POSITIONS = [
    '巽', '离', '坤',
    '震', '中', '兑',
    '艮', '坎', '乾',
]

#: 九宫格位置索引（对应 LOSHU_GRID_POSITIONS）
GRID_IDX = {
    '巽': 0, '离': 1, '坤': 2,
    '震': 3, '中': 4, '兑': 5,
    '艮': 6, '坎': 7, '乾': 8,
}

#: 洛书九宫飞星「顺飞」路径（各宫依次经过的位置索引）
#: 以洛书数序 5→6→7→8→9→1→2→3→4 飞布，即：中→乾→兑→艮→离→坎→坤→震→巽
#: 依据《沈氏玄空学》：五星入中，六白到乾、七赤到兑、八白到艮、九紫到离、
#: 一白到坎、二黑到坤、三碧到震、四绿到巽。
#: 校验：一白入中顺飞 → 巽9 离5 坤7 / 震8 中1 兑3 / 艮4 坎6 乾2（即元旦盘加五之盘）
SHUN_PATH = [4, 8, 5, 6, 1, 7, 2, 3, 0]

#: 逆飞 = 沿同一条顺飞路径逐宫「递减」一星（不是把路径反向）
#: 注：若把路径反向再递减，9 个宫位会退化为与顺飞完全相同，故不采用反向路径。

#: 山位 → 洛书宫位映射（二十四山归入九宫，每宫三山：地元、天元、人元）
MOUNTAIN_TO_GRID = {
    '子': '坎', '癸': '坎', '壬': '坎',      # 坎宫三山：壬（地元）、子（天元）、癸（人元）
    '艮': '艮', '丑': '艮', '寅': '艮',      # 艮宫：丑、艮、寅
    '甲': '震', '卯': '震', '乙': '震',      # 震宫：甲、卯、乙
    '巽': '巽', '辰': '巽', '巳': '巽',      # 巽宫：辰、巽、巳
    '丙': '离', '午': '离', '丁': '离',      # 离宫：丙、午、丁
    '坤': '坤', '未': '坤', '申': '坤',      # 坤宫：未、坤、申
    '庚': '兑', '酉': '兑', '辛': '兑',      # 兑宫：庚、酉、辛
    '乾': '乾', '戌': '乾', '亥': '乾',      # 乾宫：戌、乾、亥
}

#: 二十四山三元龙与阴阳（山星/向星顺逆的唯一依据）
#: 依据《沈氏玄空学》：天元龙（父母卦）随本卦阴阳，地元龙（逆子卦）随本卦阴阳，
#: 人元龙（顺子卦）反本卦阴阳；洛书奇偶为阳（一三五七九）、偶为阴（二四六八）。
#: - 天元龙 8 山：子、午、卯、酉（四正，阳）；乾、坤、艮、巽（四维，阴）
#: - 地元龙 8 山：甲、庚、丙、壬（阳）；辰、戌、丑、未（阴）
#: - 人元龙 8 山：寅、申、巳、亥（阳）；乙、辛、丁、癸（阴）
#: 格式：山 → (元龙, 阴阳)；阳顺飞、阴逆飞
SANYUAN_LONG = {
    '子': ('天元龙', '阳'), '癸': ('人元龙', '阴'),
    '丑': ('地元龙', '阴'), '艮': ('天元龙', '阴'),
    '寅': ('人元龙', '阳'), '甲': ('地元龙', '阳'),
    '卯': ('天元龙', '阳'), '乙': ('人元龙', '阴'),
    '辰': ('地元龙', '阴'), '巽': ('天元龙', '阴'),
    '巳': ('人元龙', '阳'), '丙': ('地元龙', '阳'),
    '午': ('天元龙', '阳'), '丁': ('人元龙', '阴'),
    '未': ('地元龙', '阴'), '坤': ('天元龙', '阴'),
    '申': ('人元龙', '阳'), '庚': ('地元龙', '阳'),
    '酉': ('天元龙', '阳'), '辛': ('人元龙', '阴'),
    '戌': ('地元龙', '阴'), '乾': ('天元龙', '阴'),
    '亥': ('人元龙', '阳'), '壬': ('地元龙', '阳'),
}

#: 立向分界（罗盘口径，0° 为正北「子」山中心，每山 15°）
#: 正向（下卦）= 距山中线 ≤4.5°（每山中间 9°）；兼向（替卦）= 4.5°~7.5°（左右各 3°）；
#: 超过 7.5° 即压在两山交界（出卦/骑线），不予排盘。
MOUNTAIN_ARC = 15.0
XIA_GUA_HALF_WIDTH = 4.5
JIAN_XIANG_HALF_WIDTH = 7.5

#: 本模块明确未实现/简化的口径，随排盘结果一起返回，供界面与报告标注
LIMITATIONS = [
    '五运五黄入中未实现「前十年寄坤、后十年寄艮」之分，五运一律按中宫五黄顺飞',
    '兼向替卦（TIGUA_RULES）数据不完整且未经验证，不参与排盘；兼向请求直接报错',
    '出卦/骑线（距山中线 >7.5°）不支持，按报错处理',
    '非标准多字串坐向（如「坐北朝南」）沿用历史兜底，山向星不重排',
]

# ================================================================
# 三元九运
# ================================================================

#: 三元九运运程唯一的权威口径见 get_yun / get_yun_info：
#: 一运起于 1864 年，每运 20 年，九运一轮回，三元（上/中/下）各 60 年。


def _validate_year(year, field: str = '年份') -> int:
    """校验年份入参：必须为整数且落在 1-9999 的合理区间。

    Args:
        year: 待校验年份
        field: 字段名（用于错误信息）

    Returns:
        int: 校验通过的年份

    Raises:
        ValueError: 非整数或越界
    """
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError(f'{field}必须为整数，收到 {year!r}')
    if not (1 <= year <= 9999):
        raise ValueError(f'{field}超出合理范围 1-9999，收到 {year}')
    return year


#: 每 20 年一运，运序 = (year - 1864) % 180 // 20 + 1
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

    Raises:
        ValueError: 年份非整数或越界
    """
    year = _validate_year(year, '建造年份')
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

    Raises:
        ValueError: 年份非整数或越界
    """
    year = _validate_year(year, '建造年份')
    yun = get_yun(year)
    # 三元归属：上元（一、二、三运）、中元（四、五、六运）、下元（七、八、九运）
    offset = (year - 1864) % 180
    if offset < 0:
        offset += 180
    yuan = ('上元', '中元', '下元')[offset // 60]
    # 起始年按该年在运内的实际偏移回推，避免跨 180 年周期时算错
    start = year - (offset % 20)
    end = start + 19
    return {'yun': yun, 'yuan': yuan, 'start': start, 'end': end}


# ================================================================
# 二十四山
# ================================================================

def get_mountain_index(mountain: str) -> int:
    """获取山位序号（0-23，自「子」起顺时针）。

    Raises:
        ValueError: 传入的非二十四山名
    """
    if mountain in MOUNTAIN_SET:
        return MOUNTAIN_24_STD.index(mountain)
    raise ValueError(f'「{mountain}」不是二十四山之一')


def _require_mountain(name: str, field: str) -> str:
    """校验单个山名是否属于二十四山。

    Raises:
        ValueError: 非法山名
    """
    if name not in MOUNTAIN_SET:
        raise ValueError(
            f'{field}「{name}」不是二十四山之一（合法值：{"".join(MOUNTAIN_24_STD)}）')
    return name


def _require_opposite(mount: str, facing: str) -> None:
    """校验坐山与向首是否互为 180° 对冲。

    Raises:
        ValueError: 坐向不成对
    """
    expect = _CHONG_MAP.get(mount)
    if expect != facing:
        raise ValueError(f'坐向不成对：{mount}山的对冲应为{expect}向，收到{facing}向')


def parse_sui_xiang(sui_xiang: str) -> Tuple[str, str]:
    """解析坐向字符串为 (坐山, 向首)。

    支持格式：
    - '子山午向' → ('子', '午')
    - '坐子向午' → ('子', '午')
    - '午' → ('子', '午')（仅向首时，坐山取对冲）
    - 其他非标准多字串沿用历史兜底（原样返回），以兼容旧调用方

    Args:
        sui_xiang: 坐向字符串

    Returns:
        tuple: (坐山, 向首)

    Raises:
        ValueError: 坐向为空/非字符串；显式「山向」格式中出现非二十四山名，
                    或坐山与向首不构成对冲
    """
    if not isinstance(sui_xiang, str):
        raise ValueError(f'坐向必须为字符串，收到 {sui_xiang!r}')
    s = sui_xiang.strip()
    if not s:
        raise ValueError('坐向不能为空')

    # 标准格式：X山Y向（含前缀如 '坐子山午向'）
    if '山' in s and '向' in s:
        parts = s.replace('坐', '').split('山')
        if len(parts) != 2:
            raise ValueError(f'坐向格式不合法：{sui_xiang!r}')
        mount = parts[0].strip()
        facing = parts[1].replace('向', '').strip()
        _require_mountain(mount, '坐山')
        _require_mountain(facing, '向首')
        _require_opposite(mount, facing)
        return mount, facing

    # 前缀格式：'坐子向午'（无「山」但有「向」）
    if '坐' in s and '向' in s:
        cleaned = s.replace('坐', '').replace('向', '')
        unknown = [c for c in cleaned if not c.isspace() and c not in MOUNTAIN_SET]
        if unknown:
            raise ValueError(f'坐向含非法山名：{"".join(unknown)}')
        chars = [c for c in cleaned if c in MOUNTAIN_SET]
        if len(chars) >= 2:
            _require_opposite(chars[0], chars[1])
            return chars[0], chars[1]
        if len(chars) == 1:
            return _CHONG_MAP[chars[0]], chars[0]
        raise ValueError(f'坐向格式不合法：{sui_xiang!r}')

    # 简写：仅一个字符（视为向首，坐山取对冲）
    if len(s) == 1:
        _require_mountain(s, '向首')
        return _CHONG_MAP[s], s

    # 非标准多字串：保留历史兜底行为，避免破坏既有调用方
    return s, s


# ================================================================
# 立向：下卦 / 兼向（替卦）
# ================================================================

def classify_xiang(mountain: str, degree) -> Dict:
    """按罗盘度数判定「下卦（正向）」还是「兼向（替卦）」。

    口径：每山占 15°，以山中线为基准
    - 距中线 ≤4.5°（本山中间 9°）→ 下卦
    - 4.5°~7.5°（左右各 3°）→ 兼向（需替卦）
    - >7.5° → 压两山交界（出卦/骑线），报错

    Args:
        mountain: 坐山（二十四山之一）
        degree: 罗盘度数（0° 为正北子山中心，顺时针）

    Returns:
        dict: {'method': '下卦'|'替卦', 'degree': 归一度数, 'offset': 距中线度数}

    Raises:
        ValueError: 山名非法、度数非数字/越界、或出卦骑线
    """
    _require_mountain(mountain, '坐山')
    if isinstance(degree, bool) or not isinstance(degree, (int, float)):
        raise ValueError(f'罗盘度数必须为数字，收到 {degree!r}')
    d = float(degree) % 360.0
    center = get_mountain_index(mountain) * MOUNTAIN_ARC
    diff = abs(d - center)
    diff = min(diff, 360.0 - diff)
    if diff > JIAN_XIANG_HALF_WIDTH:
        raise ValueError(
            f'度数 {d:.2f}° 距{mountain}山中线 {diff:.2f}°，超出 ±{JIAN_XIANG_HALF_WIDTH}°'
            '（出卦/骑线），请重新立向')
    return {
        'method': '下卦' if diff <= XIA_GUA_HALF_WIDTH else '替卦',
        'degree': d,
        'offset': round(diff, 2),
    }


# ================================================================
# 飞星入中
# ================================================================

def _validate_star(star, field: str = '星值') -> int:
    """校验九星入参：必须为 1-9 的整数。

    Raises:
        ValueError: 非整数、布尔值或越界
    """
    if isinstance(star, bool) or not isinstance(star, int) or not 1 <= star <= 9:
        raise ValueError(f'{field}必须为 1-9 的整数，收到 {star!r}')
    return star


def fei_star_ru_zhong(star: int, direction: int = 1) -> List[int]:
    """飞星入中飞布。

    将指定入中星沿洛书顺飞路径飞布到九宫格：
    - 顺飞：每进一宫，星值 +1（9 后回到 1）
    - 逆飞：每进一宫，星值 -1（1 后回到 9）

    Args:
        star: 入中星（1-9）
        direction: 1 为顺飞，-1 为逆飞

    Returns:
        list: 九宫格各位置（巽离坤/震中兑/艮坎乾）的星值列表

    Raises:
        ValueError: 入中星非 1-9 整数，或 direction 不是 1 / -1
    """
    star = _validate_star(star, '入中星')
    if direction not in (1, -1):
        raise ValueError(f'飞布方向只能为 1（顺飞）或 -1（逆飞），收到 {direction!r}')
    result = [0] * 9
    for i, pos in enumerate(SHUN_PATH):
        # 中宫为 star，其后每宫按 ±i 递增/递减，模 9 映射回 1-9
        result[pos] = ((star - 1 + direction * i) % 9) + 1
    return result


def is_forward_fly(star: int) -> bool:
    """判断山星/向星入中后应顺飞还是逆飞。

    规则（三元龙阴阳）：
    - 阳星（1、3、5、7、9）：顺飞
    - 阴星（2、4、6、8）：逆飞
    注：五黄土居中，按顺飞处理。
    运盘与流年盘不适用此规则，二者一律顺飞。

    Args:
        star: 入中星（1-9）

    Returns:
        bool: True 顺飞，False 逆飞

    Raises:
        ValueError: 星值非 1-9 整数
    """
    return _validate_star(star) in (1, 3, 5, 7, 9)


def get_liunian_ruzhong(year: int) -> int:
    """计算流年入中星（三元九运正统流年紫白法）。

    规则：上元甲子年（1864 年）一白入中；此后每过一年，入中星退一位
    （即 1→9→8→…→2 循环）。中元甲子年（1924）四绿入中、下元甲子年
    （1984）七赤入中，与此递推规则自洽。
    等价公式：入中星 = ((1864 - year) mod 9) + 1。

    Args:
        year: 公历年份

    Returns:
        int: 流年入中星（1-9）

    Raises:
        ValueError: 年份非整数或越界
    """
    year = _validate_year(year, '流年年份')
    return ((1864 - year) % 9) + 1


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
                  current_year: int = None, mount_degree=None) -> Dict:
        """完整玄空飞星排盘。

        山星/向星正统算法：
        1. 运盘（当运星入中，一律顺飞）先排出九宫运星；
        2. 山星入中星 = 运盘中「坐山所在宫」的运星；
           向星入中星 = 运盘中「向首所在宫」的运星；
        3. 山星顺逆取坐山三元龙阴阳，向星顺逆取向首三元龙阴阳（阳顺阴逆）。

        Args:
            sui_xiang: 坐向（如 '子山午向'）
            build_year: 建造年份（定运）
            current_year: 当前年份（定流年叠加），缺省取 build_year
            mount_degree: 坐山罗盘度数（可选）；给出时判定下卦/兼向，
                          兼向因替卦未实现而报错

        Returns:
            dict: 完整排盘结果，含运星/山星/向星九宫、格局、替卦、流年等

        Raises:
            ValueError: 年份非整数/越界；显式「山向」格式非法；
                        兼向替卦未实现；出卦/骑线
        """
        build_year = _validate_year(build_year, '建造年份')
        if current_year is None:
            current_year = build_year
        current_year = _validate_year(current_year, '当前年份')

        # 1. 定运
        yun = get_yun(build_year)
        yun_info = get_yun_info(build_year)

        # 2. 解析坐向
        mount, facing = parse_sui_xiang(sui_xiang)

        # 3. 立向判定：下卦 / 兼向
        if mount_degree is None:
            lifa = {'method': '下卦', 'degree': None, 'offset': 0.0}
        else:
            lifa = classify_xiang(mount, mount_degree)
            if lifa['method'] == '替卦':
                raise ValueError(
                    '兼向替卦排盘尚未实现：现有 TIGUA_RULES 数据不完整且未经验证，'
                    '拒绝以占位替卦出盘。请按正向（下卦）立向或等待替卦表补全。')

        # 4. 替卦（历史字段，仅按旧表命中标记，未参与排盘；见 LIMITATIONS）
        mount_tigua = apply_tigua(mount, yun)
        facing_tigua = apply_tigua(facing, yun)
        has_tigua = (mount_tigua != mount or facing_tigua != facing)

        # 5. 运星入中：当运星入中，一律顺飞（不按阴阳分顺逆）
        yun_star = yun  # 运序即入中运星
        yun_grid = fei_star_ru_zhong(yun_star, 1)

        # 6. 山星/向星：取运盘坐山宫/向首宫之星入中，按三元龙阴阳顺逆
        limitations = list(LIMITATIONS)
        if mount in MOUNTAIN_SET and facing in MOUNTAIN_SET:
            shan_ruzhong = yun_grid[GRID_IDX[MOUNTAIN_TO_GRID[mount]]]
            xiang_ruzhong = yun_grid[GRID_IDX[MOUNTAIN_TO_GRID[facing]]]
            shan_dir = 1 if SANYUAN_LONG[mount][1] == '阳' else -1
            xiang_dir = 1 if SANYUAN_LONG[facing][1] == '阳' else -1
            shan_grid = fei_star_ru_zhong(shan_ruzhong, shan_dir)
            xiang_grid = fei_star_ru_zhong(xiang_ruzhong, xiang_dir)
            pattern = self._classify_pattern(
                mount, facing, shan_grid, xiang_grid, yun_star)
        else:
            # 历史兜底：非标准坐向无法定宫，不做山向重排（不得静默冒充正统盘）
            shan_ruzhong = xiang_ruzhong = yun_star
            shan_dir = xiang_dir = 1
            shan_grid = list(yun_grid)
            xiang_grid = list(yun_grid)
            pattern = '未判定'
            limitations.append('坐向未能解析为二十四山，山星/向星未重排（结果不可作玄空判断）')

        # 7. 构建九宫格
        grid = self._build_grid(yun_grid, shan_grid, xiang_grid)

        # 8. 流年叠加
        liunian_grid = self._liunian_overlay(current_year)

        return {
            'yun': yun,
            'yun_info': yun_info,
            'sui_xiang': sui_xiang,
            'mount': mount,
            'facing': facing,
            'mount_tigua': mount_tigua,
            'facing_tigua': facing_tigua,
            'has_tigua': has_tigua,
            'lifa': lifa,
            'build_year': build_year,
            'current_year': current_year,
            'yun_star': yun_star,
            'shan_ruzhong': shan_ruzhong,
            'xiang_ruzhong': xiang_ruzhong,
            'shan_direction': shan_dir,
            'xiang_direction': xiang_dir,
            'pattern': pattern,
            'liunian_star': get_liunian_ruzhong(current_year),
            'grid': grid,
            'liunian': liunian_grid,
            'limitations': limitations,
        }

    def _classify_pattern(self, mount: str, facing: str, shan_grid: List[int],
                          xiang_grid: List[int], yun_star: int) -> str:
        """按当旺星（运星）落宫判定玄空格局。

        判定口径（通行飞星法）：
        - 双星会向：山星、向星当旺星同到向首宫
        - 双星会坐：山星、向星当旺星同到坐山宫
        - 旺山旺向（到山到向）：山星当旺到坐山、向星当旺到向首
        - 上山下水：山星当旺到向首、向星当旺到坐山
        - 其余为一般格局
        """
        idx_mount = GRID_IDX[MOUNTAIN_TO_GRID[mount]]
        idx_facing = GRID_IDX[MOUNTAIN_TO_GRID[facing]]
        shan_at_mount = shan_grid[idx_mount]
        xiang_at_mount = xiang_grid[idx_mount]
        shan_at_facing = shan_grid[idx_facing]
        xiang_at_facing = xiang_grid[idx_facing]
        if shan_at_facing == yun_star and xiang_at_facing == yun_star:
            return '双星会向'
        if shan_at_mount == yun_star and xiang_at_mount == yun_star:
            return '双星会坐'
        if shan_at_mount == yun_star and xiang_at_facing == yun_star:
            return '旺山旺向'
        if shan_at_facing == yun_star and xiang_at_mount == yun_star:
            return '上山下水'
        return '一般格局'

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

    def _liunian_overlay(self, year: int) -> List[Dict]:
        """流年飞星叠加。

        流年入中星按三元九运正统流年紫白法推算（见 get_liunian_ruzhong），
        入中后一律顺飞。

        Raises:
            ValueError: 年份非整数或越界
        """
        liunian_star = get_liunian_ruzhong(year)
        liunian_grid = fei_star_ru_zhong(liunian_star, 1)
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
