# -*- coding: utf-8 -*-
"""
梅花易数 P0 静默错算修复 —— 实测对照脚本。

本脚本刻意不复用被测实现来生成「期望值」：
  * 先天八卦的三爻位图、64 卦上下卦组合名称表，均以教科书常量在本脚本内独立声明；
  * 互卦/变卦/错卦/综卦的推导，按古法规则在原始六爻位图上独立计算。
被测代码只负责给出「修复后结果」，两者逐一比对。

运行：
    .\\venv\\Scripts\\python.exe scripts\\verify_meihua_p0.py

退出码：0 = 全部用例通过；1 = 存在不符。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# =============================================================================
# 一、独立的古法基准（教科书常量，不依赖被测代码）
# =============================================================================
#: 先天八卦数（通行《梅花易数》先天卦序）→ 三爻位图，初→上
SHAPE = {
    1: ('阳', '阳', '阳'),  # 乾 ☰
    2: ('阳', '阳', '阴'),  # 兑 ☱
    3: ('阳', '阴', '阳'),  # 离 ☲
    4: ('阳', '阴', '阴'),  # 震 ☳
    5: ('阴', '阳', '阳'),  # 巽 ☴
    6: ('阴', '阳', '阴'),  # 坎 ☵
    7: ('阴', '阴', '阳'),  # 艮 ☶
    8: ('阴', '阴', '阴'),  # 坤 ☷
}
NUM = {shape: num for num, shape in SHAPE.items()}

#: 八卦卦符
SYMBOL = {1: '☰', 2: '☱', 3: '☲', 4: '☳', 5: '☴', 6: '☵', 7: '☶', 8: '☷'}

#: 64 卦名，键为 (上卦先天数, 下卦先天数)，按文王六十四卦通行名
NAME = {
    (1, 1): '乾为天', (1, 2): '天泽履', (1, 3): '天火同人', (1, 4): '天雷无妄',
    (1, 5): '天风姤', (1, 6): '天水讼', (1, 7): '天山遁', (1, 8): '天地否',
    (2, 1): '泽天夬', (2, 2): '兑为泽', (2, 3): '泽火革', (2, 4): '泽雷随',
    (2, 5): '泽风大过', (2, 6): '泽水困', (2, 7): '泽山咸', (2, 8): '泽地萃',
    (3, 1): '火天大有', (3, 2): '火泽睽', (3, 3): '离为火', (3, 4): '火雷噬嗑',
    (3, 5): '火风鼎', (3, 6): '火水未济', (3, 7): '火山旅', (3, 8): '火地晋',
    (4, 1): '雷天大壮', (4, 2): '雷泽归妹', (4, 3): '雷火丰', (4, 4): '震为雷',
    (4, 5): '雷风恒', (4, 6): '雷水解', (4, 7): '雷山小过', (4, 8): '雷地豫',
    (5, 1): '风天小畜', (5, 2): '风泽中孚', (5, 3): '风火家人', (5, 4): '风雷益',
    (5, 5): '巽为风', (5, 6): '风水涣', (5, 7): '风山渐', (5, 8): '风地观',
    (6, 1): '水天需', (6, 2): '水泽节', (6, 3): '水火既济', (6, 4): '水雷屯',
    (6, 5): '水风井', (6, 6): '坎为水', (6, 7): '水山蹇', (6, 8): '水地比',
    (7, 1): '山天大畜', (7, 2): '山泽损', (7, 3): '山火贲', (7, 4): '山雷颐',
    (7, 5): '山风蛊', (7, 6): '山水蒙', (7, 7): '艮为山', (7, 8): '山地剥',
    (8, 1): '地天泰', (8, 2): '地泽临', (8, 3): '地火明夷', (8, 4): '地雷复',
    (8, 5): '地风升', (8, 6): '地水师', (8, 7): '地山谦', (8, 8): '坤为地',
}

#: 康熙笔画（与项目 data/fengshui.db 的 stroke_count 表一致，脚本内先独立声明）
STROKES = {'乾': 11, '水': 4, '坤': 8}


def invert(pattern):
    """阴阳反转。"""
    return tuple('阴' if yao == '阳' else '阳' for yao in pattern)


def expected_hexagrams(pattern6, changing_positions):
    """按古法在原始六爻位图上独立推导五卦的 (上卦数, 下卦数)。"""
    lower_p, upper_p = pattern6[0:3], pattern6[3:6]
    base = (NUM[upper_p], NUM[lower_p])

    # 互卦：下互二三四，上互三四五
    hu = (NUM[pattern6[2:5]], NUM[pattern6[1:4]])

    # 变卦：按变爻位置翻转
    changed = [
        invert((yao,))[0] if (i + 1) in changing_positions else yao
        for i, yao in enumerate(pattern6)
    ]
    bian = (NUM[tuple(changed[3:6])], NUM[tuple(changed[0:3])])

    # 错卦：六爻全反
    cuo = (NUM[invert(upper_p)], NUM[invert(lower_p)])

    # 综卦：整卦颠倒
    reversed6 = pattern6[::-1]
    zong = (NUM[reversed6[3:6]], NUM[reversed6[0:3]])
    return {'base': base, 'hu': hu, 'bian': bian, 'cuo': cuo, 'zong': zong}


def render(key):
    """把 (上卦数, 下卦数) 渲染成「符+卦名」。"""
    upper, lower = key
    return f'{SYMBOL[upper]}{SYMBOL[lower]} {NAME[key]}'


# =============================================================================
# 二、用例（输入 → 独立期望）
# =============================================================================
def case_number(numbers):
    """数字起卦：按公开接口语义（1/2/3 个数）算期望。"""
    if len(numbers) == 1:
        upper = numbers[0] % 8
        lower = (numbers[0] // 10) % 8
        changing = numbers[0] % 6
    elif len(numbers) == 2:
        upper = numbers[0] % 8
        lower = numbers[1] % 8
        changing = (numbers[0] + numbers[1]) % 6
    else:
        upper = numbers[0] % 8
        lower = numbers[1] % 8
        changing = numbers[2] % 6
    upper = upper or 8
    lower = lower or 8
    changing = changing or 6
    pattern = SHAPE[lower] + SHAPE[upper]
    return pattern, [changing], numbers


def case_coin(lines):
    """铜钱起卦：爻型直接决定阴阳位图。三背=老阳、二背=少阳、一背=少阴、零背=老阴。"""
    yin_yang = {'老阳': '阳', '少阳': '阳', '少阴': '阴', '老阴': '阴'}
    pattern = tuple(yin_yang[t] for t in lines)
    positions = [i + 1 for i, t in enumerate(lines) if t in ('老阳', '老阴')] or [6]
    return pattern, positions, None


def case_text(text):
    """文字起卦：上卦=总笔画%8，下卦=(总笔画+字数)%8，动爻=(总笔画*字数)%6。"""
    strokes = sum(STROKES[char] for char in text)
    count = len(text)
    upper = strokes % 8 or 8
    lower = (strokes + count) % 8 or 8
    changing = (strokes * count) % 6 or 6
    pattern = SHAPE[lower] + SHAPE[upper]
    return pattern, [changing], text


#: 修复前结果实测值（取自 git HEAD 旧版代码，见报告「证据」一节）
LEGACY = {
    '数字 [3, 3]': {'base': '离为火', 'hu': '乾为天', 'bian': '水天需', 'cuo': '坤为地', 'zong': '乾为天'},
    '数字 [1, 1]': {'base': '乾为天', 'hu': '乾为天', 'bian': '天火同人', 'cuo': '坤为地', 'zong': '乾为天'},
    '数字 [1, 2, 3]': {'base': '天水讼', 'hu': '水风井', 'bian': '乾为天', 'cuo': '地山谦', 'zong': '风天小畜'},
    '数字 [5, 7]': {'base': '风山渐', 'hu': '天火同人', 'bian': '天火同人', 'cuo': '山泽损', 'zong': '火风鼎'},
    '铜钱 六少阳': {'base': '兑为泽', 'hu': '坤为地', 'bian': '山地剥', 'cuo': '乾为天', 'zong': '坤为地'},
    '铜钱 六老阳': {'base': '乾为天', 'hu': '乾为天', 'bian': '坤为地', 'cuo': '坤为地', 'zong': '乾为天'},
    '铜钱 混合': {'base': '泽风大过', 'hu': '兑为泽', 'bian': '天泽履', 'cuo': '雷火丰', 'zong': '泽水困'},
    '文字 乾': {'base': '水火既济', 'hu': '乾为天', 'bian': '水火既济', 'cuo': '山地剥', 'zong': '天风姤'},
    '文字 水': {'base': '水火既济', 'hu': '乾为天', 'bian': '水火既济', 'cuo': '山地剥', 'zong': '天风姤'},
    '文字 乾坤': {'base': '雷泽归妹', 'hu': '天火同人', 'bian': '乾为天', 'cuo': '地泽临', 'zong': '火天大有'},
}

ORDER = ('base', 'hu', 'bian', 'cuo', 'zong')
LABEL = {'base': '本卦', 'hu': '互卦', 'bian': '变卦', 'cuo': '错卦', 'zong': '综卦'}


def build_cases():
    cases = []
    for nums in ([3, 3], [1, 1], [1, 2, 3], [5, 7]):
        label = f'数字 {nums}'
        pattern, positions, _ = case_number(nums)
        cases.append((label, 'number', nums, pattern, positions))
    for label, lines in (
        ('六少阳', ['少阳'] * 6),
        ('六老阳', ['老阳'] * 6),
        ('混合', ['少阳', '少阴', '少阳', '老阳', '少阴', '少阳']),
    ):
        pattern, positions, _ = case_coin(lines)
        cases.append((f'铜钱 {label}', 'coin', lines, pattern, positions))
    for text in ('乾', '水', '乾坤'):
        pattern, positions, _ = case_text(text)
        cases.append((f'文字 {text}', 'text', text, pattern, positions))
    return cases


# =============================================================================
# 三、跑被测实现并与期望比对
# =============================================================================
def main():
    from core.divination.meihua import MeiHuaCalculator
    from core.divination.hexagram_analyzer import HexagramAnalyzer
    from core.database_manager import get_db_manager

    calc = MeiHuaCalculator()
    analyzer = HexagramAnalyzer()

    def run(kind, data):
        if kind == 'number':
            dr = calc.number_divination(list(data), '对照')
        elif kind == 'coin':
            dr = calc.copper_coin_divination(list(data), '对照')
        else:
            dr = calc.text_divination(data, '对照')
        allh = calc.generate_all_hexagrams(dr)
        result = analyzer.analyze_divination(dr, allh)
        got = {k: result[k]['name'] for k in ORDER}
        return dr, got, result

    print('=' * 132)
    print('梅花易数 P0 修复实测对照（修复前 = git HEAD 旧版实测；期望 = 脚本内独立古法基准）')
    print('=' * 132)
    failures = 0
    for label, kind, data, pattern, positions in build_cases():
        expected = expected_hexagrams(pattern, positions)
        dr, got, _ = run(kind, data)
        print(f'\n【{label}】 六爻(初→上)={"".join(pattern)}  上={dr["upper_num"]} 下={dr["lower_num"]}  动爻={positions}')
        for key in ORDER:
            legacy = LEGACY[label][key]
            now = got[key]
            want = render(expected[key])
            ok = now == NAME[expected[key]]
            failures += 0 if ok else 1
            flag = 'OK ' if ok else 'FAIL'
            print(f'  {LABEL[key]}  修复前: {legacy:<6} | 修复后: {now:<6} | 古法正确: {want}  [{flag}]')

    # 64 卦名称表核对（含 hexagram_64 表的兑/坎编号错位）
    print('\n' + '-' * 132)
    print('64 卦名称表核对：把 hexagram_64 表的 upper_num/lower_num 换算成先天数后逐一比对')
    table_num = {1: 1, 2: 6, 3: 3, 4: 4, 5: 5, 6: 2, 7: 7, 8: 8}  # 表内 2=坎、6=兑，与先天数相反
    rows = get_db_manager().get_hexagram_64()
    bad = []
    for (upper_t, lower_t), info in rows.items():
        key = (table_num.get(upper_t, upper_t), table_num.get(lower_t, lower_t))
        if NAME.get(key) != info.get('name'):
            bad.append((key, info.get('name'), NAME.get(key)))
    print(f'  hexagram_64 共 {len(rows)} 条；换算后与教科书名称不符 {len(bad)} 条')
    for item in bad:
        print(f'    不符: {item}')

    print('\n' + '=' * 132)
    if failures or bad:
        print(f'结论：失败 {failures} 项，名称表不符 {len(bad)} 条')
        return 1
    print('结论：全部用例通过；64 卦名称表换算后与教科书完全一致')
    return 0


if __name__ == '__main__':
    sys.exit(main())
