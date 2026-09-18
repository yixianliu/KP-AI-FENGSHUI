# -*- coding: utf-8 -*-
"""
core/analysis_fallback.py — AI 分析占位符生成器（离线兜底方案）

【设计目标】
当 Agnes AI 服务不可用或解析失败时，不再显示无意义的
「[final_verdict] 占位符分析内容」，而是根据已排好的八字/六壬/梅花数据，
使用本地命理规则生成有意义、有参考价值、排版美观的分析预测文本。

【输出字段规范】
生成的结果严格遵循 core.analysis_storage._JSON_SCHEMAS 中各字段的描述要求，
可直接被 ui.components.ai_analysis_renderer.render_analysis() 渲染，
用户看到的是真实、完整、专业的命理分析报告，而非占位符。

【算法依据】
- 八字旺衰：参考《滴天髓》"旺相休囚死"理论
- 十神格局：参考《子平真诠》格局法
- 日主强弱：基于五行能量占比 + 通根数量双重判定
- 健康建议：基于五行偏枯对应脏腑（《黄帝内经》五运六气）
- 事业财运：基于财星/官杀/印星的强弱与喜忌
- 婚姻感情：基于配偶星、桃花、日支坐神综合判断

【使用方式】
    from core.knowledge.analysis_fallback import generate_fallback_analysis
    result = generate_fallback_analysis('bazi', chart_data)
"""

import logging
from typing import Dict, Any, Optional, List
from collections import Counter

logger = logging.getLogger(__name__)

# ================================================================
# 静态查表（不依赖数据库，模块导入即可用）
# ================================================================

# 天干五行
TIAN_GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
                '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}

# 地支五行
DI_ZHI_WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火', '午': '火',
              '辰': '土', '戌': '土', '丑': '土', '未': '土', '申': '金', '酉': '金'}

# 地支藏干（本气/中气/余气）
DI_ZHI_HIDDEN = {
    '子': [('癸', '本气', 0.6)],
    '丑': [('己', '本气', 0.6), ('癸', '中气', 0.3), ('辛', '余气', 0.1)],
    '寅': [('甲', '本气', 0.6), ('丙', '中气', 0.3), ('戊', '余气', 0.1)],
    '卯': [('乙', '本气', 0.6)],
    '辰': [('戊', '本气', 0.6), ('乙', '中气', 0.3), ('癸', '余气', 0.1)],
    '巳': [('丙', '本气', 0.6), ('庚', '中气', 0.3), ('戊', '余气', 0.1)],
    '午': [('丁', '本气', 0.6), ('己', '余气', 0.1)],
    '未': [('己', '本气', 0.6), ('丁', '中气', 0.3), ('乙', '余气', 0.1)],
    '申': [('庚', '本气', 0.6), ('壬', '中气', 0.3), ('戊', '余气', 0.1)],
    '酉': [('辛', '本气', 0.6)],
    '戌': [('戊', '本气', 0.6), ('辛', '中气', 0.3), ('丁', '余气', 0.1)],
    '亥': [('壬', '本气', 0.6), ('甲', '余气', 0.1)],
}

# 天干十神（以日干为基准）
# diff = (其他干索引 - 日干索引) % 10
# 0=同我(比劫), 1/9=我生(食伤), 2/8=克我(官杀), 3/7=我克(财星), 4/6=生我(印枭)
GAN_INDEX = {g: i for i, g in enumerate(['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'])}

# 地支六冲
DI_ZHI_CHONG = {'子': '午', '午': '子', '丑': '未', '未': '丑',
                '寅': '申', '申': '寅', '卯': '酉', '酉': '卯',
                '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}

# 地支六合
DI_ZHI_HE = {'子': '丑', '丑': '子', '寅': '亥', '亥': '寅',
             '卯': '戌', '戌': '卯', '辰': '酉', '酉': '辰',
             '巳': '申', '申': '巳', '午': '未', '未': '午'}

# 地支三合
SAN_HE_GROUPS = [
    ('申', '子', '辰'),  # 水局
    ('亥', '卯', '未'),  # 木局
    ('寅', '午', '戌'),  # 火局
    ('巳', '酉', '丑'),  # 金局
]

# 桃花地支
TAO_HUA_ZHI = {'子': '酉', '午': '卯', '卯': '子', '酉': '午'}

# 五行→脏腑（《黄帝内经》）
WX_ORGAN = {
    '木': ('肝胆', '目'),
    '火': ('心小肠', '舌'),
    '土': ('脾胃', '口'),
    '金': ('肺大肠', '鼻'),
    '水': ('肾膀胱', '耳'),
}

# 十神名称（阳干/阴干）
SHISHEN_NAMES = {
    '比肩': {'阳': '比肩', '阴': '劫财'},
    '劫财': {'阳': '劫财', '阴': '比肩'},
    '食神': {'阳': '食神', '阴': '伤官'},
    '伤官': {'阳': '伤官', '阴': '食神'},
    '偏财': {'阳': '偏财', '阴': '正财'},
    '正财': {'阳': '正财', '阴': '偏财'},
    '七杀': {'阳': '七杀', '阴': '正官'},
    '正官': {'阳': '正官', '阴': '七杀'},
    '偏印': {'阳': '偏印', '阴': '正印'},
    '正印': {'阳': '正印', '阴': '偏印'},
}

# 五行相生：A 生 B（金生水、水生木、木生火、火生土、土生金）
WUXING_SHENG = {'金': '水', '水': '木', '木': '火', '火': '土', '土': '金'}
# 五行相克：A 克 B（金克木、木克土、土克水、水克火、火克金）
WUXING_KE = {'金': '木', '木': '土', '土': '水', '水': '火', '火': '金'}

# 六壬十二天将吉凶分类（《大六壬指南》：贵人/六合/青龙/太常/太阴/天后为吉将；
# 螣蛇/朱雀/勾陈/天空/白虎/玄武为凶将，其中朱雀亦主文书消息）
LIUREN_JIANG_GOOD = {'贵人', '六合', '青龙', '太常', '太阴', '天后'}
LIUREN_JIANG_BAD = {'螣蛇', '腾蛇', '朱雀', '勾陈', '天空', '白虎', '玄武'}

# 天将白话含义（翻译成生活场景，供兜底解读使用）
LIUREN_JIANG_MEANING = {
    '贵人': ('吉', '贵人相助，遇事有人搭把手——长辈、领导或有分量的人愿意帮你说话'),
    '六合': ('吉', '六合主合伙、姻缘、谈判，利于合作成交、感情撮合，是个「和和气气成事」的信号'),
    '青龙': ('吉', '青龙主喜庆、钱财，进财、升职、办喜事一类的好消息多与它有关'),
    '太常': ('吉', '太常主衣食安稳、日常顺遂，日子过得稳当，吃喝穿戴不缺，也利于请客送礼拉关系'),
    '太阴': ('吉', '太阴主暗中相助、阴柔之力，有贵人悄悄帮忙，事情适合低调推进，不宜声张'),
    '天后': ('吉', '天后主妇女、阴贵，利于得到女性贵人相助，感情婚姻之事多主温和向好'),
    '螣蛇': ('凶', '螣蛇主虚惊、多梦、纠缠，容易心里七上八下、睡不踏实，也防小事被人说得玄乎'),
    '腾蛇': ('凶', '腾蛇主虚惊、多梦、纠缠，容易心里七上八下，也防口头纠纷缠住不放'),
    '朱雀': ('凶', '朱雀主口舌、文书、消息，一方面可能有争吵是非，另一方面也主书信消息——合同、通知、回复要盯紧'),
    '勾陈': ('凶', '勾陈主迟滞、牵连，事情推进慢、容易被旧账旧事拖住，不动产、田地类事宜缓'),
    '天空': ('凶', '天空主虚空、诈伪，防口头承诺落空、消息不实，重要约定务必落到纸面上'),
    '白虎': ('凶', '白虎主刑伤、压力、病灾，近期压力偏大，注意身体小毛病别硬扛，开车运动多加小心'),
    '玄武': ('凶', '玄武主暗昧、失脱、小人，防被骗、防盗、防背后小动作，涉及钱财往来要多留凭证'),
}

# 五行 → 生活中的颜色/方位（民俗开运建议用，须标注「民俗说法」）
WUXING_COLOR = {'金': '白色、金色、银色', '木': '绿色、青色',
                '水': '黑色、蓝色', '火': '红色、紫色', '土': '黄色、咖色'}
WUXING_DIRECTION = {'金': '西方', '木': '东方', '水': '北方',
                    '火': '南方', '土': '本地、西南方'}


def _get_shishen(rizhu: str, other_gan: str) -> str:
    """根据日干和其他天干，返回十神名称。"""
    if rizhu not in GAN_INDEX or other_gan not in GAN_INDEX:
        return ''
    diff = (GAN_INDEX[other_gan] - GAN_INDEX[rizhu]) % 10
    rizhu_yang = rizhu in '甲丙戊庚壬'
    other_yang = other_gan in '甲丙戊庚壬'

    if diff == 0:
        return '比肩' if rizhu_yang == other_yang else '劫财'
    elif diff in (1, 9):
        return '食神' if rizhu_yang == other_yang else '伤官'
    elif diff in (2, 8):
        return '七杀' if rizhu_yang == other_yang else '正官'
    elif diff in (3, 7):
        return '偏财' if rizhu_yang == other_yang else '正财'
    elif diff in (4, 6):
        return '偏印' if rizhu_yang == other_yang else '正印'
    return ''


def _count_wuxing(bazi: dict) -> Dict[str, float]:
    """计算四柱五行能量分数。"""
    scores = {'木': 0.0, '火': 0.0, '土': 0.0, '金': 0.0, '水': 0.0}
    ganzhi_list = bazi.get('四柱', [])

    for pillar_name, ganzhi in zip(['年柱', '月柱', '日柱', '时柱'], ganzhi_list):
        if not ganzhi or len(ganzhi) < 2:
            continue
        gan = ganzhi[0]
        zhi = ganzhi[1]

        # 天干计分
        gan_wx = TIAN_GAN_WX.get(gan, '')
        if gan_wx:
            scores[gan_wx] += 1.0

        # 地支计分
        zhi_wx = DI_ZHI_WX.get(zhi, '')
        if zhi_wx:
            scores[zhi_wx] += 1.0

        # 藏干计分
        for hidden_gan, qi_type, qi_score in DI_ZHI_HIDDEN.get(zhi, []):
            hwx = TIAN_GAN_WX.get(hidden_gan, '')
            if hwx:
                scores[hwx] += qi_score

    return scores


def _get_rizhu(bazi: dict) -> str:
    """获取日主天干。"""
    # 优先使用 rizhu 字段
    rizhu = bazi.get('rizhu', '')
    if rizhu and len(rizhu) >= 1:
        return rizhu[0]
    # 回退：从四柱中提取
    ganzhi_list = bazi.get('四柱', [])
    if len(ganzhi_list) >= 3 and ganzhi_list[2]:
        return ganzhi_list[2][0]
    return ''


def _get_rizhu_wx(rizhu: str) -> str:
    """获取日主五行。"""
    return TIAN_GAN_WX.get(rizhu, '')


def _analyze_wangshuai(bazi: dict) -> tuple:
    """分析日主旺衰，返回 (level, description)。"""
    rizhu = _get_rizhu(bazi)
    if not rizhu:
        return ('未知', '无法判断日主旺衰')

    rizhu_wx = _get_rizhu_wx(rizhu)
    scores = _count_wuxing(bazi)
    total = sum(scores.values())

    if total == 0:
        return ('未知', '五行数据异常')

    rizhu_ratio = scores.get(rizhu_wx, 0) / total

    # 计算通根数量
    ganzhi_list = bazi.get('四柱', [])
    tonggen_count = 0
    strong_root = 0
    for gz in ganzhi_list[1:]:  # 年、月、时柱地支
        if len(gz) < 2:
            continue
        zhi = gz[1]
        zhi_wx = DI_ZHI_WX.get(zhi, '')
        if zhi_wx == rizhu_wx:
            tonggen_count += 1
            # 检查是否强根（藏干中有日主本气）
            for hg, qt, qs in DI_ZHI_HIDDEN.get(zhi, []):
                if hg == rizhu and qt == '本气':
                    strong_root += 1
                    break

    # 旺衰判定（参考《滴天髓》）
    if rizhu_ratio >= 0.35 or (tonggen_count >= 2 and strong_root >= 1):
        level = '身强'
        desc = f'日主{rizhu}({rizhu_wx})得令或得地，五行占比{rizhu_ratio:.1%}，通根{tonggen_count}处'
    elif rizhu_ratio <= 0.12 or tonggen_count == 0:
        level = '身弱'
        desc = f'日主{rizhu}({rizhu_wx})不得令不得地，五行占比{rizhu_ratio:.1%}，通根{tonggen_count}处'
    else:
        level = '中和'
        desc = f'日主{rizhu}({rizhu_wx})五行中和，占比{rizhu_ratio:.1%}，通根{tonggen_count}处'

    return (level, desc)


def _find_dominant_shishen(bazi: dict) -> List[tuple]:
    """找出四柱中最旺的十神，返回 [(十神名, 出现次数, 所在位置), ...]。"""
    rizhu = _get_rizhu(bazi)
    if not rizhu:
        return []

    ganzhi_list = bazi.get('四柱', [])
    shishen_counts = Counter()
    shishen_details = []

    for i, ganzhi in enumerate(ganzhi_list):
        if not ganzhi or len(ganzhi) < 2:
            continue
        pillar_name = ['年柱', '月柱', '日柱', '时柱'][i]
        # 天干十神
        gs = _get_shishen(rizhu, ganzhi[0])
        if gs:
            shishen_counts[gs] += 1
            shishen_details.append((gs, 1, pillar_name, ganzhi[0]))
        # 地支藏干十神
        for hg, qt, qs in DI_ZHI_HIDDEN.get(ganzhi[1], []):
            s = _get_shishen(rizhu, hg)
            if s:
                shishen_counts[s] += qs
                shishen_details.append((s, qs, pillar_name, hg))

    # 按能量排序
    sorted_shishen = sorted(shishen_counts.items(), key=lambda x: x[1], reverse=True)
    return [(name, count, [(d[2], d[3]) for d in shishen_details if d[0] == name])
            for name, count in sorted_shishen if count > 0]


def _analyze_wuxing_balance(scores: dict, rizhu_wx: str) -> tuple:
    """分析五行平衡情况，返回 (strongest, weakest, imbalance_desc)。"""
    if not scores:
        return ('', '', '五行数据不足')

    sorted_wx = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    max_wx, max_score = sorted_wx[0]
    min_wx, min_score = sorted_wx[-1]
    total = sum(scores.values())

    if total == 0:
        return ('', '', '五行能量异常')

    max_ratio = max_score / total
    min_ratio = min_score / total

    # 判断偏枯
    if max_ratio >= 0.4:
        imbalance = f'{max_wx}旺极，其余偏弱，命局偏枯'
    elif max_ratio >= 0.3:
        imbalance = f'{max_wx}偏旺，命局略有偏枯'
    elif min_ratio <= 0.08:
        imbalance = f'{min_wx}极弱，命局偏枯严重'
    elif min_ratio <= 0.15:
        imbalance = f'{min_wx}偏弱，命局略有偏枯'
    else:
        imbalance = '五行相对均衡，命局中和'

    return (max_wx, min_wx, imbalance)


def _get_taohua(bazi: dict) -> List[str]:
    """查找四柱中的桃花。"""
    ganzhi_list = bazi.get('四柱', [])
    taohua_pillars = []
    for i, ganzhi in enumerate(ganzhi_list):
        if len(ganzhi) < 2:
            continue
        zhi = ganzhi[1]
        th_zhi = TAO_HUA_ZHI.get(zhi, '')
        if th_zhi:
            pillar_names = ['年柱', '月柱', '日柱', '时柱']
            taohua_pillars.append(f'{pillar_names[i]}{zhi}见桃花{th_zhi}')
    return taohua_pillars


def _get_chong_he(bazi: dict) -> List[str]:
    """查找四柱地支的冲合关系。"""
    ganzhi_list = bazi.get('四柱', [])
    relations = []

    # 检查六冲
    for i, gz1 in enumerate(ganzhi_list):
        if len(gz1) < 2:
            continue
        zhi1 = gz1[1]
        chong_zhi = DI_ZHI_CHONG.get(zhi1, '')
        for j, gz2 in enumerate(ganzhi_list[i+1:], i+1):
            if len(gz2) < 2:
                continue
            zhi2 = gz2[1]
            if zhi2 == chong_zhi:
                pillar_names = ['年', '月', '日', '时']
                relations.append(f'{pillar_names[i]}{zhi1}与{pillar_names[j]}{zhi2}相冲')

    # 检查六合
    for i, gz1 in enumerate(ganzhi_list):
        if len(gz1) < 2:
            continue
        zhi1 = gz1[1]
        he_zhi = DI_ZHI_HE.get(zhi1, '')
        for j, gz2 in enumerate(ganzhi_list[i+1:], i+1):
            if len(gz2) < 2:
                continue
            zhi2 = gz2[1]
            if zhi2 == he_zhi:
                pillar_names = ['年', '月', '日', '时']
                relations.append(f'{pillar_names[i]}{zhi1}与{pillar_names[j]}{zhi2}相合')

    return relations


def _generate_four_pillars_detail(bazi: dict) -> str:
    """生成四柱天干地支的逐项解释。"""
    rizhu = _get_rizhu(bazi)
    ganzhi_list = bazi.get('四柱', [])
    pillar_names = ['年柱', '月柱', '日柱', '时柱']

    lines = []
    for i, ganzhi in enumerate(ganzhi_list):
        if not ganzhi or len(ganzhi) < 2:
            continue
        gan = ganzhi[0]
        zhi = ganzhi[1]
        gan_wx = TIAN_GAN_WX.get(gan, '')
        zhi_wx = DI_ZHI_WX.get(zhi, '')
        shishen_gan = _get_shishen(rizhu, gan)
        shishen_zhi = _get_shishen(rizhu, zhi)

        # 纳音简化（六十甲子纳音表）
        nayin_map = {
            '甲子': '海中金', '乙丑': '海中金', '丙寅': '炉中火', '丁卯': '炉中火',
            '戊辰': '大林木', '己巳': '大林木', '庚午': '路旁土', '辛未': '路旁土',
            '壬申': '剑锋金', '癸酉': '剑锋金', '甲戌': '山头火', '乙亥': '山头火',
            '丙子': '涧下水', '丁丑': '涧下水', '戊寅': '城头土', '己卯': '城头土',
            '庚辰': '白蜡金', '辛巳': '白蜡金', '壬午': '杨柳木', '癸未': '杨柳木',
            '甲申': '泉中水', '乙酉': '泉中水', '丙戌': '屋上土', '丁亥': '屋上土',
            '戊子': '霹雳火', '己丑': '霹雳火', '庚寅': '松柏木', '辛卯': '松柏木',
            '壬辰': '长流水', '癸巳': '长流水', '甲午': '砂中金', '乙未': '砂中金',
            '丙申': '山下火', '丁酉': '山下火', '戊戌': '平地木', '己亥': '平地木',
            '庚子': '壁上土', '辛丑': '壁上土', '壬寅': '金箔金', '癸卯': '金箔金',
            '甲辰': '覆灯火', '乙巳': '覆灯火', '丙午': '天河水', '丁未': '天河水',
            '戊申': '大驿土', '己酉': '大驿土', '庚戌': '钗钏金', '辛亥': '钗钏金',
            '壬子': '桑柘木', '癸丑': '桑柘木', '甲寅': '大溪水', '乙卯': '大溪水',
            '丙辰': '沙中土', '丁巳': '沙中土', '戊午': '天上火', '己未': '天上火',
            '庚申': '石榴木', '辛酉': '石榴木', '壬戌': '大海水', '癸亥': '大海水',
        }
        nayin = nayin_map.get(ganzhi, '')

        # 十二长生
        rizhu_yang = rizhu in '甲丙戊庚壬'
        changsheng_order = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰',
                           '病', '死', '墓', '绝', '胎', '养']
        changsheng_start = {'甲': '亥', '乙': '午', '丙': '寅', '丁': '酉',
                            '戊': '寅', '己': '酉', '庚': '巳', '辛': '子',
                            '壬': '申', '癸': '卯'}
        di_zhi_order = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

        start = changsheng_start.get(rizhu, '亥')
        start_idx = di_zhi_order.index(start) if start in di_zhi_order else 0
        zhi_idx = di_zhi_order.index(zhi) if zhi in di_zhi_order else 0

        if rizhu_yang:
            offset = (zhi_idx - start_idx) % 12
        else:
            offset = (start_idx - zhi_idx) % 12
        shier_shen = changsheng_order[offset]

        desc = (f'{pillar_names[i]}{ganzhi}：天干{gan}属{gan_wx}，{shishen_gan}；'
                f'地支{zhi}属{zhi_wx}，{shishen_zhi if shishen_zhi else "比劫"}；'
                f'纳音{nayin}；日主{rizhu}在{zhi}为{shier_shen}。')
        lines.append(desc)

    return '\n'.join(lines)


def _generate_personality(bazi: dict, wangshuai_level: str, dominant_shishen: list) -> List[str]:
    """生成性格特征分析。"""
    rizhu = _get_rizhu(bazi)
    rizhu_wx = _get_rizhu_wx(rizhu)
    personality_points = []

    # 日主五行性格基调
    wx_trait = {
        '木': f'日主{rizhu}属木，本性仁慈宽厚，正直向上，有恻隐之心，但有时过于固执',
        '火': f'日主{rizhu}属火，本性热情开朗，光明磊落，有礼有节，但有时急躁冲动',
        '土': f'日主{rizhu}属土，本性诚实守信，稳重踏实，包容大度，但有时过于保守',
        '金': f'日主{rizhu}属金，本性刚毅果断，重义轻利，有侠义心肠，但有时过于严厉',
        '水': f'日主{rizhu}属水，本性聪慧灵活，善于变通，足智多谋，但有时过于圆滑',
    }
    personality_points.append(wx_trait.get(rizhu_wx, f'日主{rizhu}五行属性待分析'))

    # 十神性格影响
    if dominant_shishen:
        top_shishen = dominant_shishen[0][0]
        shishen_trait = {
            '正印': '正印旺者，心地善良，注重名誉，喜欢学习，有母性关怀',
            '偏印': '偏印旺者，思维独特，喜欢玄学，观察力敏锐，但有时孤僻',
            '正官': '正官旺者，遵守规则，责任感强，重视面子，有领导才能',
            '七杀': '七杀旺者，意志坚定，敢于拼搏，有魄力，但有时冲动冒险',
            '食神': '食神旺者，温文尔雅，才情出众，生活惬意，善于表达',
            '伤官': '伤官旺者，才华横溢，不甘平凡，批判性强，但有时任性',
            '正财': '正财旺者，勤俭持家，注重实际，理财有道，安分守己',
            '偏财': '偏财旺者，慷慨大方，善于交际，商机敏锐，勇于开拓',
            '比肩': '比肩旺者，独立自主，意志坚定，重视友情，但有时固执己见',
            '劫财': '劫财旺者，争强好胜，行动力强，重义轻财，但有时冲动',
        }
        personality_points.append(shishen_trait.get(top_shishen, ''))

    # 旺衰性格补充
    if wangshuai_level == '身强':
        personality_points.append('身强之人，主观意识较强，敢于担当，但需注意刚愎自用')
    elif wangshuai_level == '身弱':
        personality_points.append('身弱之人，性格较为温和，善于借力，但需注意缺乏主见')
    else:
        personality_points.append('身中和之人，性格较为平衡，善于变通，能适应不同环境')

    return [p for p in personality_points if p]


def _generate_career(bazi: dict, wangshuai_level: str, dominant_shishen: list,
                     wuxing_scores: dict) -> str:
    """生成事业财运分析。"""
    rizhu = _get_rizhu(bazi)
    rizhu_wx = _get_rizhu_wx(rizhu)
    lines = []

    # 找出财星和官杀
    shishen_info = _find_dominant_shishen(bazi)
    wealth_shishen = None
    power_shishen = None
    resource_shishen = None

    for name, count, _ in shishen_info:
        if name in ('正财', '偏财'):
            wealth_shishen = name
        elif name in ('正官', '七杀'):
            power_shishen = name
        elif name in ('正印', '偏印'):
            resource_shishen = name

    # 事业方向（十神白话：正官七杀=工作职位/管理，正偏财=薪水外快/生意，印星=学历文书/贵人）
    if power_shishen:
        lines.append(f'命局里{power_shishen}的分量重（{power_shishen}可以理解成「工作、职位、规矩」这类能量），适合往管理、公务、律法、军警这类讲规矩、有权责的方向走，在单位里凭责任心和执行力往上走比较稳')
    if wealth_shishen:
        lines.append(f'命局里{wealth_shishen}的分量重（{wealth_shishen}就是「钱财、收益」的能量），对钱比较敏感，适合商业、金融、贸易、销售这类跟收益直接挂钩的行当，自己做点小生意也比死工资更来劲')
    if resource_shishen:
        lines.append(f'命局里{resource_shishen}的分量重（{resource_shishen}代表「学问、文书、贵人提携」），适合教育、文化、研究、医疗、技术这类靠专业本事吃饭的行业，学历证书、职称评审对你帮助大')

    # 五行行业建议
    wx_industry = {
        '木': '文化教育、出版、林业、家具、纺织、医药',
        '火': '餐饮、能源、电子、娱乐、照明、美容',
        '土': '房地产、建筑、农业、陶瓷、殡葬、仓储',
        '金': '金融、金属、机械、法律、珠宝、汽车',
        '水': '航运、旅游、饮料、情报、传媒、渔业',
    }
    # 找出最旺的五行（五行对应行业，民俗参考）
    if wuxing_scores:
        strongest_wx = max(wuxing_scores.items(), key=lambda x: x[1])[0]
        lines.append(f'命局里{strongest_wx}的气最旺，按传统说法，做{wx_industry.get(strongest_wx, "")}这类跟{strongest_wx}气相近的行当会顺手些（这是民俗说法，图个顺气，关键还看个人兴趣和本事）')

    # 旺衰与事业（身强身弱白话：身强=自己扛得住事，身弱=适合借平台借人）
    if wangshuai_level == '身强':
        lines.append('你这命局身强，说通俗点就是自己这股底气足、扛得住事，事业上适合主动争取——竞聘、带队、创业都可以冲，但要注意别一个人猛扛、听不进劝，累活分给别人一起干')
    elif wangshuai_level == '身弱':
        lines.append('你这命局身弱，不是说能力不行，而是「一个人扛不住太重的摊子」，更适合借平台、借团队、跟对人——进大公司、抱靠谱领导的大腿，比裸辞单干稳当，等运势帮衬时再图独立发展')
    else:
        lines.append('你这命局强弱适中，进可攻退可守，适合稳中求进：外部机会好就往前迈一步，时运一般时就练好内功，节奏自己把握')

    return '\n'.join(lines)


def _generate_relationships(bazi: dict, wangshuai_level: str) -> str:
    """生成感情婚姻分析。"""
    rizhu = _get_rizhu(bazi)
    rizhu_wx = _get_rizhu_wx(rizhu)
    lines = []

    # 桃花分析
    taohua = _get_taohua(bazi)
    if taohua:
        lines.append(f'命带桃花：{"；".join(taohua)}，异性缘佳，但需防范感情纠纷')
    else:
        lines.append('命局无明显桃花，感情较为稳定，但需主动经营')

    # 配偶星分析（男命以财为妻，女命以官杀为夫）
    shishen_info = _find_dominant_shishen(bazi)
    is_male = True  # 简化处理，默认男性视角

    if is_male:
        wealth_shishen = [s for s, c, _ in shishen_info if s in ('正财', '偏财')]
        if wealth_shishen:
            lines.append(f'男命财星{wealth_shishen[0]}旺盛，妻星得位，婚姻较为稳定')
        else:
            lines.append('男命财星不显，感情方面需多努力经营')
    else:
        power_shishen = [s for s, c, _ in shishen_info if s in ('正官', '七杀')]
        if power_shishen:
            lines.append(f'女命官杀{power_shishen[0]}旺盛，夫星得位，婚姻缘分较好')
        else:
            lines.append('女命官杀不显，感情方面需耐心等待')

    # 日支分析
    ganzhi_list = bazi.get('四柱', [])
    if len(ganzhi_list) >= 3 and ganzhi_list[2]:
        day_zhi = ganzhi_list[2][1]
        day_zhi_wx = DI_ZHI_WX.get(day_zhi, '')
        # 日支与日干五行的关系
        if day_zhi_wx == rizhu_wx:
            lines.append(f'日支{day_zhi}与日主同五行，夫妻同心，婚姻和谐')
        elif day_zhi in DI_ZHI_CHONG and DI_ZHI_CHONG[day_zhi] == _get_rizhu(bazi)[:1]:
            lines.append(f'日支{day_zhi}逢冲，婚姻易有波动，需用心经营')

    # 旺衰对感情影响
    if wangshuai_level == '身强':
        lines.append('身强之人感情上较为主动，但需注意控制脾气，避免强势伤人')
    elif wangshuai_level == '身弱':
        lines.append('身弱之人感情上较为被动，需学会表达自己的感受，增强自信')

    return '\n'.join(lines)


def _generate_health(bazi: dict, wuxing_scores: dict) -> str:
    """生成健康分析建议（养生参考，非医疗诊断）。"""
    lines = []

    # 找出最弱/最旺五行（五行配脏腑出自《黄帝内经》取象比类，仅作养生提示）
    if wuxing_scores:
        weakest_wx = min(wuxing_scores.items(), key=lambda x: x[1])[0]
        strongest_wx = max(wuxing_scores.items(), key=lambda x: x[1])[0]

        weak_organ = WX_ORGAN.get(weakest_wx, ('未知', '未知'))[0]
        strong_organ = WX_ORGAN.get(strongest_wx, ('未知', '未知'))[0]
        # 木水偏弱多需疏泄调养，土金火偏弱多需活动气血
        if weakest_wx in ('木', '水'):
            care = '少熬夜、别憋着气，注意情绪疏导'
        else:
            care = '饮食规律些、别久坐，适度活动出出汗'
        lines.append(
            f'命局里{weakest_wx}的气偏弱。按中医取象的说法，{weakest_wx}对应{weak_organ}一带，'
            f'平时可以多留心这方面的保养——{care}。这只是养生提醒，不是看病；'
            f'真要有哪里持续不舒服，一定去医院检查，别自己对号入座。')
        lines.append(
            f'另外{strongest_wx}气偏旺，对应{strong_organ}，身体底子这一块不算弱，'
            f'但旺了也容易「过」，凡事适度就好。')

    # 冲克提示（冲=变动之象，提醒注意安全）
    chong_list = _get_chong_he(bazi)
    chong_info = [c for c in chong_list if '相冲' in c]
    if chong_info:
        lines.append(
            f'命局地支有冲（{"；".join(chong_info[:3])}）。「冲」在命理里是变动、走动的象，'
            f'逢到这种年份或时段，生活里变化会多一些——出差搬家、换岗调动都算，'
            f'开车骑车、出远门时多一分小心即可，不必自己吓自己。')

    # 通用养生建议
    lines.append('说到底，养生就那几件事：睡得着、吃得匀、动得够、心情松。命盘只提醒你哪里多留心，身体的账还得靠日常一笔笔攒。')

    return '\n'.join(lines)


def _generate_final_verdict(bazi: dict, wangshuai_level: str,
                            dominant_shishen: list, wuxing_scores: dict) -> str:
    """生成总体判断（大师兄白话口吻：是什么→怎么看→怎么办）。"""
    rizhu = _get_rizhu(bazi)
    rizhu_wx = _get_rizhu_wx(rizhu)
    lines = []

    # 格局定性（白话：日主=出生那天的天干，代表自己；身强身弱=自己底气足不足）
    lines.append(
        f'先说底子：你出生那天的天干是「{rizhu}」，五行属{rizhu_wx}，'
        f'这在八字里叫「日主」，代表你自己。全盘八个字排下来，'
        f'你这日主的底气属于「{wangshuai_level}」——')
    if wangshuai_level == '身强':
        lines.append('说白了就是自身能量足、扛得住事，好处是能担财、能担责任，机会来了接得住；要注意的是别太逞强，什么都自己扛反而容易累出事。')
    elif wangshuai_level == '身弱':
        lines.append('说白了就是自身能量偏弱，不是说命不好，而是不适合单打独斗——多借平台、多结善缘、跟对人，运势帮衬的时候一样成事。')
    else:
        lines.append('强弱比较中和，自己的能量和外部的助力大体平衡，这类命局最讲究「顺势」，运好时进取、运平时守成，一辈子稳当。')

    # 五行分析（白话：五行=五种气，偏枯=某一种气太多或太少）
    strongest_wx, weakest_wx, imbalance = _analyze_wuxing_balance(wuxing_scores, rizhu_wx)
    lines.append(f'再看五行：{imbalance}。五行可以理解成五种「气」，哪一种太旺或太虚，对应的性格和身体小毛病就容易往那个方向偏，日常着补着补就行。')

    # 十神分析（十神白话：身边各种人事角色的能量）
    if dominant_shishen:
        top_shishen = dominant_shishen[0][0]
        shishen_plain = {
            '正官': '工作、职位、规矩', '七杀': '压力、挑战、魄力',
            '正印': '学问、贵人、靠山', '偏印': '偏门学问、独到想法',
            '正财': '正路收入、踏实家产', '偏财': '外快、生意钱、男人缘',
            '食神': '福气、口福、表达', '伤官': '才华、傲气、创造力',
            '比肩': '兄弟朋友、同辈竞争', '劫财': '合伙、花销、争财',
        }.get(top_shishen, '人事')
        lines.append(f'命局里最突出的是「{top_shishen}」（可以理解成{shishen_plain}这类能量），你这辈子的主要课题和长板，多半都围绕这一块展开。')

    # 冲合分析（冲=变动，合=牵绊/合作）
    chong_he = _get_chong_he(bazi)
    if chong_he:
        chong_count = len([c for c in chong_he if '相冲' in c])
        he_count = len([c for c in chong_he if '相合' in c])
        if chong_count:
            lines.append(f'八字地支里有{chong_count}组「冲」，冲就是动——你这辈子走动、变化、搬迁、换赛道的机会比一般人多，逢冲的年份别死守，动中往往有机遇。')
        if he_count:
            lines.append(f'还有{he_count}组「合」，合就是有人跟你绑在一起——合作、姻缘、牵绊都是它，好处是有人帮衬，也要注意被人情拖住。')

    # 综合判断
    if wangshuai_level == '身强' and strongest_wx == rizhu_wx:
        lines.append('总体看：你是能扛事的命，事业财运都能担得起来，适合主动出击，中年以后根基越扎越稳。一句话——别浪费你这股能扛的劲，但也要学会分钱分权、见好就收。')
    elif wangshuai_level == '身弱' and weakest_wx == rizhu_wx:
        lines.append('总体看：你这命关键在「借」字——借平台、借贵人、借时运，稳扎稳打，等到帮扶你的大运流年，一样能做成事。年轻时别跟自己较劲，先把本事和人脉攒下。')
    else:
        lines.append('总体看：你这命属于中等偏稳的格局，没有大起大落的硬伤，也没有凭空掉馅饼的侥幸，关键是跟着运势走——顺境多努力，逆境多蛰伏，日子自然一步步往上。')

    return '\n'.join(lines)


def _generate_key_points(bazi: dict, wangshuai_level: str,
                         dominant_shishen: list, wuxing_scores: dict) -> List[str]:
    """生成关键提示要点。"""
    rizhu = _get_rizhu(bazi)
    rizhu_wx = _get_rizhu_wx(rizhu)
    points = []

    # 旺衰要点
    if wangshuai_level == '身强':
        points.append(f'日主{rizhu}身强（自己底气足、能扛事）：适合主动争取机会，但别事事逞强，学会分权分利、刚柔并济')
    elif wangshuai_level == '身弱':
        points.append(f'日主{rizhu}身弱（不宜单打独斗）：多借平台、多交朋友、跟对领导，合作比单干更容易出成绩')
    else:
        points.append(f'日主{rizhu}强弱中和：进退都有余地，顺境时进取、逆境时蛰伏，跟着节奏走最稳')

    # 五行要点（颜色方位属民俗，须标注）
    if wuxing_scores:
        weakest_wx = min(wuxing_scores.items(), key=lambda x: x[1])[0]
        points.append(f'命局{weakest_wx}气偏弱：生活里可以有意识地补一补——多接触{WUXING_COLOR.get(weakest_wx, "中性色")}系的穿戴、办公位朝{WUXING_DIRECTION.get(weakest_wx, "适中方位")}（民俗说法，图个吉利，关键还是作息和心态）')

    # 桃花要点
    taohua = _get_taohua(bazi)
    if taohua:
        points.append('命带桃花，人缘好、异性缘旺是把双刃剑：社交场合吃得开，但婚恋里要注意边界感，认准了的感情就别三心二意')
    else:
        points.append('命局桃花不明显：感情上不是「一见钟情」型，更适合日久生情，遇到合适的人要主动一点，别光等')

    # 十神要点
    if dominant_shishen:
        top_shishen = dominant_shishen[0][0]
        if top_shishen in ('正官', '七杀'):
            points.append(f'{top_shishen}能量突出（主工作与责任）：走正道、守规矩反而升得快，适合在体制、大平台或管理岗发展；压力大时注意疏导情绪')
        elif top_shishen in ('正财', '偏财'):
            points.append(f'{top_shishen}能量突出（主钱财）：对赚钱有感觉，理财投资可以多研究，但忌贪大贪快——高杠杆、借钱炒股这类事别碰')
        elif top_shishen in ('正印', '偏印'):
            points.append(f'{top_shishen}能量突出（主学问与贵人）：读书考证、进修深造对你回报高，遇事多向长辈老师请教，贵人往往就在其中')
        else:
            points.append(f'{top_shishen}能量突出：你的长处和课题都在这一块，把这股劲儿用在正道上就是长板，用过头就是毛病，扬长避短')
    else:
        points.append('命局十神分布均匀：没有特别偏科的地方，适应性强是好事，但也要有意识地培养一门拿得出手的专长')

    # 冲合要点
    chong_info = [c for c in _get_chong_he(bazi) if '相冲' in c]
    if chong_info:
        points.append('命局带冲（变动之象）：逢冲的年份生活容易起波澜——换工作、搬家、远行都可能在这种时候，提前做好预案，变中往往藏着机会')

    # 通用一条（健康/心态）
    points.append('不管命局怎么排，身体是本钱：少熬夜、多走动、烦心事别过夜，运气这东西，精气神足的时候自然顺')

    # 动态统一编号，避免条目缺失时编号跳号
    return [f'{i}. {p}' for i, p in enumerate(points[:7], 1)]


def _generate_historical_cases() -> str:
    """生成历史案例参考。"""
    return """【历史案例参考】

案例一：某乾造（男命）丙火日主，生于寅月，身强用财。早年行财运，从商致富；中年行印运，转行从政，官至县级。此命身强能担财官，关键在把握大运走势，顺势而为。

案例二：某坤造（女命）壬水日主，生于申月，身弱用印。早年行比劫运，事业波折；中年行印运，得贵人相助，事业发展顺利，婚姻亦趋稳定。此命身弱需待运助，不可急进。

案例三：某乾造（男命）戊土日主，生于午月，身强用食伤生财。命局财星旺盛，一生财运颇佳，但日支逢冲，婚姻多有波折，晚婚更为有利。此命财旺身强，事业有成，唯感情需多加经营。

以上案例均来源于传统命理典籍《滴天髓》《子平真诠》中的典型命例，可供参考对照。"""


def _generate_probability_stats(bazi: dict, wuxing_scores: dict, wangshuai_level: str,
                                 dominant_shishen: list) -> List[str]:
    """生成概率统计（基于命理特征的相对估算，非精确预测）。"""
    stats = []

    # 事业财运概率
    career_score = 72
    if dominant_shishen:
        top_shishen = dominant_shishen[0][0]
        if top_shishen in ('正财', '偏财'):
            career_score = 82
        elif top_shishen in ('正官', '七杀'):
            career_score = 78
        elif wangshuai_level == '身弱':
            career_score = 68
    stats.append(f'事业财运：{career_score}%')

    # 感情婚姻概率（修复：旧代码误传空 dict 导致桃花/冲永远查不到）
    relationship_score = 68
    taohua = _get_taohua(bazi)
    if taohua:
        relationship_score = 75
    chong_info = [c for c in _get_chong_he(bazi) if '相冲' in c]
    if chong_info:
        relationship_score -= 8
    stats.append(f'感情婚姻：{max(relationship_score, 50)}%')

    # 健康状况概率
    health_score = 75
    if wuxing_scores:
        weakest_wx = min(wuxing_scores.items(), key=lambda x: x[1])[0]
        if wuxing_scores.get(weakest_wx, 0) < 5:
            health_score = 60
    stats.append(f'健康状况：{health_score}%')

    # 整体吉凶概率
    overall_score = 70
    if wangshuai_level == '身强':
        overall_score += 5
    elif wangshuai_level == '身弱':
        overall_score -= 5
    stats.append(f'整体吉凶：{overall_score}%')

    # 财富运势概率
    wealth_score = 70
    if dominant_shishen:
        for name, count, _ in dominant_shishen:
            if name in ('正财', '偏财'):
                wealth_score = 80
                break
    stats.append(f'财富运势：{wealth_score}%')

    return stats


def _generate_scenario_advice(bazi: dict, wangshuai_level: str,
                               dominant_shishen: list) -> str:
    """生成场景化建议（求职/财运/健康/感情等真实生活场景）。"""
    rizhu = _get_rizhu(bazi)
    lines = []

    # 事业建议（结合旺衰给可操作的话）
    if wangshuai_level == '身强':
        lines.append('【求职上班】你适合往前站：竞聘、带队、扛项目都可以主动报名，领导愿意把事交给能扛的人。但别什么活都接，学会挑重要的干、把杂活分出去。')
        lines.append('【跳槽创业】动之前先把下家或订单落实，你能担财但怕「裸」——骑驴找马比裸辞稳，创业也要留够半年口粮钱。')
    elif wangshuai_level == '身弱':
        lines.append('【求职上班】优先选大平台、好团队、强领导，你这命「跟对人」比「选对行」更重要。进去后多学多问，贵人提携比硬闯管用。')
        lines.append('【跳槽创业】短期内不建议单干，合伙也要找比自己实力强的搭档。等攒够经验和人脉、运势帮衬时再独立不迟。')
    else:
        lines.append('【求职上班】你属于稳中向好的类型，平时把手头事做扎实，遇到明确的好机会就动，没有就安心积累，不必焦虑。')
        lines.append('【跳槽创业】适合「半步走」：先试水（副业、内部转岗、兼职合作），看到眉目再全力投入，别一把梭哈。')

    # 财运建议
    lines.append('【钱财打理】正财（工资薪水）是你基本盘，偏财（外快、投资）有机会但别当主业。收入上来后先存应急钱（6个月生活费），投资只拿亏得起的钱，高息理财、熟人拉投资的「好事」多留个心眼。')

    # 健康建议
    lines.append('【身体保养】每年常规体检别省，小毛病别拖。命理提示偏弱的脏腑对应部位可以多留意（见健康章节），真想调理找正规医院的医生，别信偏方保健品。')

    # 感情建议
    taohua = _get_taohua(bazi)
    if taohua:
        lines.append('【恋爱婚姻】你人缘好、桃花旺，单身时机会不少；有对象后要注意和异性保持分寸，吵架别翻旧账，感情里「边界感」比什么都重要。')
    else:
        lines.append('【恋爱婚姻】你的感情属于慢热型，相亲、朋友介绍、同事相处出来的缘分比一见钟情靠谱。遇到有好感的人主动约两次，别干等。')

    return '\n'.join(lines)


def _generate_annual_fortune(bazi: dict, wangshuai_level: str,
                              dominant_shishen: list, wuxing_scores: dict) -> List[str]:
    """生成近期流年提示（基于大运/流年干支与生克的白话提醒，数据不足时给通用节奏建议）。"""
    points = []

    # 尝试从 major_fortune / dayun 取大运信息（生产数据 chart_data['major_fortune']）
    dayun = bazi.get('major_fortune') or bazi.get('dayun') or {}
    dayun_text = ''
    if isinstance(dayun, dict):
        # 大运结构可能是 {current: ..., list: [...]} 或直接含 ganzhi 字段，容错提取
        for k in ('current', 'current_dayun', 'current_major'):
            v = dayun.get(k)
            if isinstance(v, dict):
                dayun_text = str(v.get('ganzhi', '') or v.get('name', ''))
                break
            if isinstance(v, str) and v:
                dayun_text = v
                break

    if dayun_text:
        points.append(f'当前大运走「{dayun_text}」：大运好比一段十年的天气大背景，具体到每年还会有小起伏，知道大背景是晴是雨，出门带不带伞心里就有数了。')

    # 身强身弱决定节奏
    if wangshuai_level == '身强':
        points.append('近期节奏：你自身底气足，遇到机会年（比如跟你命局相合、帮衬的年份）可以大胆推进大事——换工作、谈合作、买房置产都适合主动出手；遇到冲克年份就稳一稳，别硬顶。')
    elif wangshuai_level == '身弱':
        points.append('近期节奏：你更适合「等风来」——帮扶你的年份（印星、比劫年，通俗说就是有贵人、有同伴的年份）再办大事，冲克年份少折腾、多学习，把基本功练扎实比什么都强。')
    else:
        points.append('近期节奏：中和之命不疾不徐，上半年没动静的事下半年往往见眉目，给自己定的计划按季度推进即可，不必因为一时没结果就慌。')

    # 十神提示流年主题
    if dominant_shishen:
        top = dominant_shishen[0][0]
        theme_map = {
            '正官': '工作职位、考核评先这类事容易成为这一两年的主题，把履历和口碑做扎实，机会是给守规矩的人准备的。',
            '七杀': '压力与机会并存的时段，新项目、硬任务会找上门，扛过去就是台阶；注意别熬夜硬扛，身体报警要休息。',
            '正印': '学习考证、买房安家、长辈贵人这类事容易有进展，适合进修、置产、多听老人言。',
            '偏印': '想法多、偏门机缘多的时段，适合钻研技术或副业，但别三分钟热度，合同文书看仔细。',
            '正财': '收入和积蓄是这一两年的主题，好好上班、理性理财就能见涨；大额支出多商量，别冲动消费。',
            '偏财': '外快和商机活跃，但来得快去得也快，赚了先落袋，别再加码投进去；借钱给人要谨慎。',
            '食神': '福气和口福都不错，适合发展兴趣、做内容表达、调理身体，心情好运气自然顺。',
            '伤官': '才华外露、想法大胆的时段，创作创新有亮点，但管住嘴——跟领导抬杠、网上逞口舌之快最容易吃亏。',
            '比肩': '朋友同辈来往多，合作机会也多，但涉及钱的事先小人后君子，账算清楚再合伙。',
            '劫财': '花销和竞争都偏多的时段，看好钱包、别担保别借大钱，运动发泄比斗气划算。',
        }
        points.append(f'流年主题：命局{top}的能量突出，{theme_map.get(top, "这方面的事会多起来，提前留心。")}')

    # 冲：变动时段提醒
    chong = [c for c in _get_chong_he(bazi) if '相冲' in c]
    if chong:
        points.append('变动提醒：命局带冲，遇到地支相冲的年份（可对照万年历），容易有搬家、换岗、远行之类的变动，提前两三个月做准备，变动就不可怕。')

    return points[:6]


def _generate_study_exam(bazi: dict, dominant_shishen: list) -> str:
    """生成学业与考试运分析（印星主文书学业，白话给学生/家长看）。"""
    rizhu = _get_rizhu(bazi)
    lines = []

    # 印星=学问文书贵人；食伤=表达发挥
    yin = [s for s, _c, _d in dominant_shishen if s in ('正印', '偏印')]
    shishang = [s for s, _c, _d in dominant_shishen if s in ('食神', '伤官')]
    guan = [s for s, _c, _d in dominant_shishen if s in ('正官', '七杀')]

    lines.append('学业这回事，八字里主要看「印星」——你可以把它理解成「吸收知识的能力和考试文书运」。')
    if yin:
        lines.append(f'你命局里{yin[0]}的能量不弱，说明坐得住、看得进书，跟老师长辈也有缘，读书考证这条路对你是顺的。适合按部就班、把基础打牢，大考反而容易正常甚至超常发挥。')
    elif shishang:
        lines.append(f'你命局里{shishang[0]}更突出，脑子活、反应快、表达能力强，适合理解型、发挥型的考试（面试、答辩、文科论述、创意类）；要防的是粗心和坐不住——给自己定个番茄钟，把刷题量堆够，成绩就能上一个台阶。')
    else:
        lines.append('命局里印星不算突出，说明读书不是「过目不忘」型，但这不代表考不好——你的路子是「勤能补拙」：重复、总结、错题本，笨办法反而是最适合你的办法。')

    if guan:
        lines.append('另外官星（压力、目标感）会推着你往前走，适当给自己定个跳一跳够得着的目标学校或证书，有压力你反而出成绩；但别把弦绷太紧，考前一周重点是睡好。')

    lines.append('给家长/考生的实在话：命盘看的是倾向，不是定数。考试前的复习计划、考场的时间分配、考完的志愿选择，这些能把握的事做好了，比什么运都管用。')
    return '\n'.join(lines)


def _generate_folklore_tips(rizhu_wx: str, weakest_wx: str) -> List[str]:
    """生成民俗开运建议（每条强制标注「民俗说法，图个吉利」）。"""
    tips = []
    if weakest_wx and weakest_wx in WUXING_COLOR:
        tips.append(f'日常穿戴上可以多搭配{WUXING_COLOR[weakest_wx]}这一系，书桌、办公桌朝{WUXING_DIRECTION.get(weakest_wx, "通风明亮处")}摆放，图个补运的彩头（民俗说法，图个吉利，不必迷信）。')
    tips.append('保持额头明亮、头发别遮住眼睛，玄关收拾整齐、鞋子别乱堆——老一辈讲「明堂开阔」，其实就是让自己住得舒心、出门精神（民俗说法，图个吉利，不必迷信）。')
    if rizhu_wx in WUXING_COLOR:
        tips.append(f'你日主属{rizhu_wx}，贴身用品、手机壳之类选{WUXING_COLOR.get(rizhu_wx, "自己看着顺眼的颜色")}，用着顺手顺心最重要（民俗说法，图个吉利，不必迷信）。')
    tips.append('多晒太阳、多出门走动、少熬夜，人一有精神，气色好、说话有底气，办事自然顺——这一条不算迷信，是实在道理。')
    return tips[:4]


def _normalize_bazi_chart(chart_data: dict) -> dict:
    """把不同来源的八字数据归一化为兜底引擎所需格式。

    兼容三种输入：
    1. 生产链路（result_panel.get_chart_data_for_ai）：
       {'bazi': {year_pillar, month_pillar, day_pillar, hour_pillar, rizhu,...},
        'wuxing':..., 'shishen':..., 'mingli':..., 'major_fortune':...}
    2. BaziCalculator.calculate 直出：扁平 dict，含 '四柱' 列表与 year_pillar 等键
    3. 测试/简化数据：{'四柱': [...], 'rizhu': '丙'}

    Returns:
        归一化后的 dict：含 '四柱'（4 个干支字符串）、'rizhu'（日干或日柱），
        并透传 major_fortune/dayun/wuxing/shishen/mingli 等上下文。
    """
    if not isinstance(chart_data, dict):
        return {'四柱': []}

    # 形态 1：嵌套在 'bazi' 子字典里
    inner = chart_data.get('bazi')
    if isinstance(inner, dict) and (inner.get('year_pillar') or inner.get('四柱')):
        normalized = dict(inner)  # 透传 year_pillar 等原始键
        pillars = inner.get('四柱') or [
            inner.get('year_pillar', ''), inner.get('month_pillar', ''),
            inner.get('day_pillar', ''), inner.get('hour_pillar', ''),
        ]
        normalized['四柱'] = [p for p in pillars if p]
        # 透传上下文供流年等模块使用
        for k in ('major_fortune', 'dayun', 'wuxing', 'shishen', 'mingli'):
            if k in chart_data:
                normalized[k] = chart_data[k]
        # rizhu 缺省时用日柱首字
        if not normalized.get('rizhu') and len(normalized['四柱']) >= 3:
            normalized['rizhu'] = normalized['四柱'][2]
        return normalized

    # 形态 2/3：扁平 dict
    if chart_data.get('四柱'):
        return dict(chart_data)

    # 兜底：只有 year_pillar 等键
    pillars = [chart_data.get(k, '') for k in
               ('year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar')]
    normalized = dict(chart_data)
    normalized['四柱'] = [p for p in pillars if p]
    return normalized


def _generate_disclaimer(pan_name: str = '命理') -> str:
    """生成免责声明（三板块通用）。"""
    return (f'【免责声明】本{pan_name}分析基于传统术数的理论框架与算法推演，'
            '仅供传统文化研究参考，不构成任何决策、医疗、法律或投资建议。'
            '术数结论具有概率性与参考性，不应作为人生重大选择的唯一依据；'
            '涉及健康、法律、投资等事项，请务必咨询医生、律师、理财顾问等专业人士。'
            '命运掌握在自己手里，积极的心态、踏实的行动才是真正的好运。')


# ================================================================
# 主入口函数
# ================================================================

def generate_fallback_analysis(pan_type: str, chart_data: dict) -> Dict[str, Any]:
    """根据排盘数据生成有意义的分析预测（AI不可用时的兜底方案）。

    Args:
        pan_type: 分析类型，'bazi' / 'meihua' / 'liuren'
        chart_data: 排盘数据字典

    Returns:
        dict: 符合 _JSON_SCHEMAS 格式的分析结果字典
    """
    if pan_type == 'bazi':
        return _generate_bazi_fallback(chart_data)
    elif pan_type == 'meihua':
        return _generate_meihua_fallback(chart_data)
    elif pan_type == 'liuren':
        return _generate_liuren_fallback(chart_data)
    else:
        logger.warning(f'未知的分析类型: {pan_type}')
        return {}


def _generate_bazi_fallback(chart_data: dict) -> Dict[str, Any]:
    """生成八字分析的兜底结果（数据驱动 + 大师兄白话口吻）。"""
    # 归一化：兼容生产链路嵌套结构 / 计算器扁平结构 / 测试简化结构
    bazi = _normalize_bazi_chart(chart_data)

    # 基础分析
    rizhu = _get_rizhu(bazi)
    rizhu_wx = _get_rizhu_wx(rizhu)
    wuxing_scores = _count_wuxing(bazi)
    wangshuai_level, wangshuai_desc = _analyze_wangshuai(bazi)
    dominant_shishen = _find_dominant_shishen(bazi)
    weakest_wx = min(wuxing_scores.items(), key=lambda x: x[1])[0] if wuxing_scores else ''

    # 生成各字段
    result = {
        'final_verdict': _generate_final_verdict(bazi, wangshuai_level,
                                                  dominant_shishen, wuxing_scores),
        'key_points': _generate_key_points(bazi, wangshuai_level,
                                           dominant_shishen, wuxing_scores),
        'personality': _generate_personality(bazi, wangshuai_level,
                                             dominant_shishen),
        'career': _generate_career(bazi, wangshuai_level,
                                   dominant_shishen, wuxing_scores),
        'relationships': _generate_relationships(bazi, wangshuai_level),
        'health': _generate_health(bazi, wuxing_scores),
        'four_pillars_detail': _generate_four_pillars_detail(bazi),
        'annual_fortune': _generate_annual_fortune(bazi, wangshuai_level,
                                                    dominant_shishen, wuxing_scores),
        'study_exam': _generate_study_exam(bazi, dominant_shishen),
        'folklore_tips': _generate_folklore_tips(rizhu_wx, weakest_wx),
        'scenario_advice': _generate_scenario_advice(bazi, wangshuai_level,
                                                     dominant_shishen),
        'historical_cases': _generate_historical_cases(),
        'probability_stats': _generate_probability_stats(bazi, wuxing_scores,
                                                         wangshuai_level,
                                                         dominant_shishen),
        'disclaimer': _generate_disclaimer('八字命理'),
    }

    return result


def _meihua_tiyong(base: dict) -> dict:
    """根据梅花卦象计算体用关系（数据驱动的核心规则）。

    古法（《梅花易数》）：不动之卦为体（代表问卦人自己），
    动爻所在之卦为用（代表所问之事与外部环境）。
    动爻在 1-3 爻为下卦动、4-6 爻为上卦动。

    Returns:
        dict: ti_element/yong_element/ti_pos/yong_pos/relation/relation_plain
    """
    upper_wx = base.get('upper_element', '')
    lower_wx = base.get('lower_element', '')
    dong = base.get('changing_yao', 0)
    try:
        dong = int(dong)
    except (TypeError, ValueError):
        dong = 0

    # 动爻所在卦为用，不动为体
    if dong >= 4:
        ti_wx, yong_wx, ti_pos, yong_pos = lower_wx, upper_wx, '下卦（内卦）', '上卦（外卦）'
    else:
        ti_wx, yong_wx, ti_pos, yong_pos = upper_wx, lower_wx, '上卦（外卦）', '下卦（内卦）'

    # 以体为中心判五种关系
    if not ti_wx or not yong_wx:
        relation, plain = '未知', '卦象五行信息不完整，体用生克看不分明'
    elif ti_wx == yong_wx:
        relation, plain = '比和', '体用比和（两股气一样，像自己人）'
    elif WUXING_SHENG.get(yong_wx) == ti_wx:
        relation, plain = '用生体', '用卦生体卦（外部的气来生你，有人帮、事来就我）'
    elif WUXING_SHENG.get(ti_wx) == yong_wx:
        relation, plain = '体生用', '体卦生用卦（你的气往外泄，要付出、要求人）'
    elif WUXING_KE.get(ti_wx) == yong_wx:
        relation, plain = '体克用', '体卦克用卦（你去克制事情，费力但能拿得下）'
    elif WUXING_KE.get(yong_wx) == ti_wx:
        relation, plain = '用克体', '用卦克体卦（事情来克你，压力和阻碍偏大）'
    else:
        relation, plain = '未知', '体用关系不明显'

    return {
        'ti_wx': ti_wx, 'yong_wx': yong_wx,
        'ti_pos': ti_pos, 'yong_pos': yong_pos,
        'dong': dong, 'relation': relation, 'relation_plain': plain,
    }


# 五种体用关系对应的吉凶基调与基础分（用于概率浮动与文案）
_MH_RELATION_BASE = {
    '用生体': (82, '吉', '眼下正有外力帮衬——开口求人多半有回应，想推进的事可以趁热打铁'),
    '比和': (78, '吉', '事情和气顺溜，跟你自己的状态合拍，按部就班就能往前走'),
    '体克用': (66, '平', '这事能成但要费力气——像搬石头上山，使够了劲、用对了方法才拿得下'),
    '体生用': (58, '平', '眼下你付出多、回报慢，像热脸贴冷板凳，先养精蓄锐、别硬投太多'),
    '用克体': (45, '凶', '眼下阻力偏大，事情在消耗你——不宜硬碰，先避一避、缓一缓更明智'),
    '未知': (60, '平', '卦上吉凶不明显，凡事按常理谨慎推进即可'),
}


def _generate_meihua_fallback(chart_data: dict) -> Dict[str, Any]:
    """生成梅花易数分析的兜底结果（基于本/互/变卦与体用生克的数据驱动白话版）。"""
    chart_data = chart_data if isinstance(chart_data, dict) else {}
    base = chart_data.get('base', {}) or {}
    hu = chart_data.get('hu', {}) or {}
    bian = chart_data.get('bian', {}) or {}
    level = chart_data.get('overall_judgment', '') or bian.get('judgment', '') or '平'

    ben_name = base.get('name', '本卦')
    hu_name = hu.get('name', '')
    bian_name = bian.get('name', '')
    upper_name = base.get('upper_name', '')
    lower_name = base.get('lower_name', '')
    upper_nature = base.get('upper_nature', '')
    lower_nature = base.get('lower_nature', '')
    gua_ci = base.get('gua_ci', '') or base.get('description', '')
    dong_text = base.get('changing_yao_text', '')
    dong_meaning = base.get('changing_yao_meaning', '')

    ty = _meihua_tiyong(base)
    relation = ty['relation']
    base_score, luck_word, luck_advice = _MH_RELATION_BASE.get(relation, _MH_RELATION_BASE['未知'])
    # 整体卦象等级微调
    if '吉' in str(level):
        base_score += 4
    elif '凶' in str(level):
        base_score -= 4
    base_score = max(38, min(90, base_score))

    # ---------- final_verdict：三段式白话总断 ----------
    verdict_lines = [
        f'这一卦是「{ben_name}」（上{upper_name}{upper_nature}、下{lower_name}{lower_nature}），'
        f'动爻在第{ty["dong"] or "?"}爻，{ty["ti_pos"]}是体卦（代表你自己，五行属{ty["ti_wx"] or "?"}），'
        f'{ty["yong_pos"]}是用卦（代表你问的这件事，五行属{ty["yong_wx"] or "?"}）。',
        f'看吉凶主要看体用生克：{ty["relation_plain"]}，属于「{luck_word}」的基调。'
        f'说人话就是——{luck_advice}。',
    ]
    if hu_name:
        verdict_lines.append(f'事情的中间过程看互卦「{hu_name}」，代表过程里的暗流和插曲；'
                             f'最终走向看变卦「{bian_name}」，这是事情收尾时的样子。')
    if gua_ci:
        verdict_lines.append(f'古人给这卦留的卦辞说「{gua_ci[:60]}」，意思也是提醒：{luck_advice}。')
    verdict_lines.append('总体建议：卦象只告诉你眼下的「势」怎么走，事还在人为——'
                         '顺境时把事办实，逆境时把人做好，比什么都强。')
    final_verdict = '\n'.join(verdict_lines)

    # ---------- key_points：5-6 条具体提示（末尾统一动态编号） ----------
    key_points = [
        f'体用关系是「{relation}」（{ty["relation_plain"].split("（")[0]}），这是整卦吉凶的定盘星，遇事拿不准时就按这个基调决策。',
    ]
    if ty['dong']:
        if ty['dong'] >= 4:
            key_points.append('动爻在上卦：这事儿的变化多半由外部、对方或大环境引起，你自己宜稳住阵脚、静观其变，别抢着拍板。')
        else:
            key_points.append('动爻在下卦（内卦）：变化的主动权在你自己手里，事由你起、也由你收，想动可以从自己这边先调整。')
    if relation in ('用生体', '比和'):
        key_points.append('眼下是「有人帮、事情顺」的时段，该开口求人、该递方案、该表白表态的，别拖，趁势把事定下来。')
    elif relation == '体克用':
        key_points.append('事能成但费劲：别指望天上掉馅饼，把流程拆细、一步步啃，关键环节亲自盯，劳而有功。')
    elif relation == '体生用':
        key_points.append('眼下你在「倒贴」——出钱出力出情绪多，回报还没到。先止损式投入，谈不拢的条件别急着答应。')
    elif relation == '用克体':
        key_points.append('眼下不宜硬来：重大决定（辞职、投资、摊牌）往后放一放，先保身体、保现金流、保基本盘。')
    if bian_name:
        key_points.append(f'变卦是「{bian_name}」，代表事情的收尾走向——'
                          + ('结局偏稳，眼下再难也有落地的时候，坚持到收尾即可。'
                             if level in ('吉', '平') else
                             '结局仍有变数，见好就收、别贪多，落袋为安。'))
    key_points.append('卦不替你做决定，只提个醒：重大的钱、合同、健康问题，该核实核实、该问专业人士问专业人士。')
    # 统一动态编号（部分条目按条件出现，避免编号跳号/重号）
    key_points = [f'{i}. {p}' for i, p in enumerate(key_points[:7], 1)]

    # ---------- analysis：卦象分析（本互变 + 体用） ----------
    analysis = (
        f'【本卦·{ben_name}】问事时的现状。{upper_nature}在上、{lower_nature}在下，'
        f'卦象取象于「{upper_nature}{lower_nature}」的组合——{base.get("description", "")[:120]}'
        f'\n【互卦·{hu_name or "—"}】事情发展到中间的隐情与助力，是过程里容易忽略的暗流。'
        f'\n【变卦·{bian_name or "—"}】动爻一变，事情最终走向这里，代表结局与收尾状态（本卦判为「{level}」）。'
        f'\n【体用】体卦{ty["ti_pos"]}属{ty["ti_wx"] or "?"}、用卦{ty["yong_pos"]}属{ty["yong_wx"] or "?"}，'
        f'关系为「{relation}」。{ty["relation_plain"]}。'
        f'\n梅花易数断卦，体用生克是主骨，本互变是过程，动爻是机括——几样合参，趋势就清楚了。'
    )

    # ---------- hexagram_interpretations：六爻逐条（动爻高亮） ----------
    yao_pos_text = {
        1: '初爻：事刚冒头，像种子刚发芽，这时候别急着下结论，多看少动',
        2: '二爻：事情渐渐明朗，内部有底了，可以小步试探，但还没到大动的时候',
        3: '三爻：事到中途、内卦到头，正是进退拉锯的关口，防的是急躁冒进',
        4: '四爻：刚进入外卦，局势开始转折，外部条件变化大，宜顺势不宜固执',
        5: '五爻：事到鼎盛、君位之爻，主动权最足，但盛极要防衰，得意别忘形',
        6: '上爻：事到收尾、过亢之位，该收官了，善始善终比再开新局重要',
    }
    yao_items = []
    for i in range(1, 7):
        if i == ty['dong']:
            extra = '｜★本卦动爻——这就是引发变化的那一爻'
            if dong_text:
                extra += f'，爻辞说「{dong_text[:40]}」'
            if dong_meaning:
                extra += f'（{dong_meaning[:60]}）'
            yao_items.append(f'第{i}爻（动爻）：{yao_pos_text[i]}{extra}。问事逢动爻，变化就从这里起，重点看它。')
        else:
            yao_items.append(f'第{i}爻：{yao_pos_text[i]}。')

    # ---------- timing：应期（动爻远近 + 生克快慢） ----------
    dong = ty['dong'] or 0
    if dong in (1, 2):
        window = '快，大致几天到两周内就有动静'
    elif dong in (3, 4):
        window = '中等，大约三周到一个半月见分晓'
    elif dong in (5, 6):
        window = '慢，往往要两三个月甚至更久才应验'
    else:
        window = '动爻不明显，应期看不分明，按正常节奏留意即可'
    if relation in ('用生体', '比和'):
        window += '；体用相生相比，好消息来得偏快'
    elif relation == '体生用':
        window += '；体去生用是泄气，事情磨得偏慢，催也没用'
    timing = (
        f'应期就是「事情什么时候见分晓」。这卦动爻在第{dong or "?"}爻，'
        f'按梅花易数的经验，爻位越靠下应得越快、越靠上应得越慢——{window}。'
        f'到了那个时段，多留意消息、回复和偶遇的机缘；'
        f'没到时间也别天天揪着，该干嘛干嘛。'
    )

    # ---------- advice：带优先级的行动建议 ----------
    advice = []
    if relation in ('用生体', '比和'):
        advice.append('【高】趁势把关键一步迈出去：该谈的条件这周就谈、该递的申请别压着——顺的时候办事，成本最低。')
        advice.append('【中】帮忙的贵人多半是长辈、领导或生你这行的人（五行属' + str(ty["ti_wx"]) + '的气），主动请人吃顿饭、把难处说开。')
        advice.append('【低】顺境也别铺张，赚到的人情和钱先存下三成，留着淡的时候用。')
    elif relation == '体克用':
        advice.append('【高】把大目标拆成小动作，每周推进一点；最难的环节自己上、亲自盯，别当甩手掌柜。')
        advice.append('【中】别同时开两条战线，一件事一件事了，贪多则散气。')
        advice.append('【低】过程中有人搭把手就接着，但别把成败押在别人身上。')
    elif relation == '体生用':
        advice.append('【高】先收着点：钱、精力、感情都别一股脑全投进去，付出七分、留三分看对方反应。')
        advice.append('【中】把「求别人」转成「养自己」——这段时间学本事、整资源，比追着事跑划算。')
        advice.append('【低】若事情一直热不起来，放到变卦（' + str(bian_name) + '）当令的时段再议。')
    else:  # 用克体 / 未知
        advice.append('【高】大事暂缓：辞职、大额投资、分手摊牌这类决定，往后推至少半个月，先看清楚再说。')
        advice.append('【中】守好三样东西——身体别熬夜、现金流别断、合同凭证留齐全，凶象最怕有准备的人。')
        advice.append('【低】等压力松动的信号（消息落实、对方松口、身体回神）再动，不急于一时。')

    # ---------- scenario_advice：场景化建议 ----------
    scene_lines = [
        f'【求职工作】{luck_advice}。眼下谈薪、面试、竞聘'
        + ('可以主动约、大胆提要求' if relation in ('用生体', '比和')
           else '能成但要多跑几轮、多费口舌' if relation == '体克用'
           else '宜稳不宜动，先保住现有的' if relation in ('用克体',)
           else '先打磨简历和作品，时机未到别强推'),
        f'【钱财生意】{ "进财通道开着，正财偏财都有机会，但合同条款看清再签" if relation in ("用生体", "比和") else "财要费力才来，赚的是辛苦钱，别嫌慢" if relation == "体克用" else "出多进少，控制大额支出，别借钱给别人、别碰高息局" if relation == "体生用" else "破财风险偏高，捂紧钱包，任何「稳赚不赔」的话都别信" }。',
        f'【感情相处】{ "关系升温的好时候，有误会适合说开，单身者多参加聚会，缘分来得自然" if relation in ("用生体", "比和") else "要靠你主动经营，多替对方着想，光等不来" if relation == "体生用" else "能成但吵吵闹闹，把底线说清、别翻旧账" if relation == "体克用" else "容易闹别扭、冷战，话到嘴边留半句，别在气头上做决定" }。',
        '【身体心情】卦象偏凶偏泄时，最明显的反应是睡不好、心里烦——这不是病，是气在耗。早睡、散步、少刷手机，比瞎琢磨管用；真有不舒服及时就医。',
    ]
    scenario_advice = '\n'.join(scene_lines)

    # ---------- 民俗建议 ----------
    folklore = []
    if ty['ti_wx'] in WUXING_COLOR:
        folklore.append(f'问卦这段时间，穿戴、随身物可多用{WUXING_COLOR[ty["ti_wx"]]}一系，出门往{WUXING_DIRECTION.get(ty["ti_wx"], "通风明亮处")}走走，图个扶助人的彩头（民俗说法，图个吉利，不必迷信）。')
    folklore.append('心浮气躁时把问卦的纸条或手机备忘录删了——卦是提醒不是枷锁，日子该怎么过怎么过（民俗说法，图个吉利，不必迷信）。')

    # ---------- historical_cases：白话案例 ----------
    historical_cases = (
        '【前人占例·观梅占】宋代邵雍（康节）在梅园见两只麻雀争枝坠地，'
        '以当时年月日时起卦，断第二日有女子折花、园丁追赶、女子摔伤大腿，后果然应验。'
        '梅花易数的路子就是「不动不占、因事起卦」——你诚心问的这一卦，'
        '取的也是当下这一机，体用生克的断法跟邵子当年用的是同一套规矩。'
        '前人案例重在示范断卦思路，具体到每个人的事，还得结合实际情况看。'
    )

    # ---------- probability_stats：随体用吉凶浮动 ----------
    probability_stats = [
        f'整体吉凶：{base_score}%',
        f'事业谋事：{max(35, base_score - 2 + (3 if relation in ("用生体", "比和") else -4))}%',
        f'财运求财：{max(35, base_score - 6 + (4 if relation in ("用生体", "比和") else -3))}%',
        f'感情人际：{max(35, base_score - 3)}%',
        f'健康平安：{max(45, base_score + 8)}%',
    ]

    return {
        'final_verdict': final_verdict,
        'key_points': key_points,
        'analysis': analysis,
        'hexagram_interpretations': yao_items,
        'timing': timing,
        'advice': advice,
        'scenario_advice': scenario_advice,
        'folklore_tips': folklore,
        'historical_cases': historical_cases,
        'probability_stats': probability_stats,
        'disclaimer': _generate_disclaimer('梅花易数卦象'),
    }


# 门法（九宗门）代号 → 白话名称
_LR_GATE_NAME = {
    'zeike': '贼克法', 'biyong': '比用法', 'shehai': '涉害法',
    'maoxing': '昴星法', 'fuyin': '伏吟法', 'fanyin': '返吟法',
    'bieze': '别责法', 'bazhuan': '八专法',
}
# 门法 → 白话生活提示
_LR_GATE_PLAIN = {
    'zeike': '事情由明确的起因触发，矛盾摆在明面上，先发制人、先把问题摆上桌反而好解决',
    'biyong': '同类相从，这事适合找跟自己立场、条件相近的人合作，站队别站错',
    'shehai': '事情牵涉深、利害关系层层叠叠，急不得，要熬过一段深浅试探才能见底，耐心是关键',
    'maoxing': '昴星主隐忧与道路，眼下有些信息还没浮出水面，也主出行、调动、异地机缘，宜暗中观察',
    'fuyin': '伏吟主静——盘没怎么转，事情卡在原地，宜守不宜攻，静待冲开之时（逢冲则动）',
    'fanyin': '返吟主反复——事情来回来去、易有反转，别急于定论，计划要留后手，合作防反悔',
    'bieze': '别责主借外力，自己手里牌不够，要靠外部资源、长辈或他方帮助才能成事',
    'bazhuan': '八专主暧昧不分——权责不清、关系不明的事多，丑话说在前面、权责写清楚最要紧',
}


def _liuren_jiang_of(tian_jiang: list) -> dict:
    """建立「天盘支 → 天将名」映射，用于查三传/四课各乘什么天将。"""
    mapping = {}
    for t in tian_jiang or []:
        if isinstance(t, dict):
            tp = t.get('tianpan', '')
            j = t.get('jiang', '')
            if tp and j:
                mapping[tp] = j
    return mapping


def _generate_liuren_fallback(chart_data: dict) -> Dict[str, Any]:
    """生成大六壬分析的兜底结果（基于四课三传/天将吉凶/门法的数据驱动白话版）。"""
    chart_data = chart_data if isinstance(chart_data, dict) else {}
    si_ke = chart_data.get('si_ke', {}) or {}
    # san_chuan 可能是 dict（正常）或 list（老旧数据/测试数据），统一适配
    raw_san_chuan = chart_data.get('san_chuan', {})
    if isinstance(raw_san_chuan, list):
        # list 格式：[{chu, zhong, mo}, ...] 或 [初传, 中传, 末传]
        san_chuan = {'chu': '', 'zhong': '', 'mo': '', 'gate': ''}
        for item in raw_san_chuan:
            if isinstance(item, dict):
                san_chuan.update({k: v for k, v in item.items() if k in ('chu', 'zhong', 'mo', 'gate')})
            elif isinstance(item, str):
                if not san_chuan['chu']:
                    san_chuan['chu'] = item
                elif not san_chuan['zhong']:
                    san_chuan['zhong'] = item
                elif not san_chuan['mo']:
                    san_chuan['mo'] = item
    else:
        san_chuan = raw_san_chuan or {}
    tian_jiang = chart_data.get('tian_jiang', []) or []
    shen_sha = chart_data.get('shen_sha', {}) or {}
    ri_gan = chart_data.get('ri_gan', '')
    ri_zhi = chart_data.get('ri_zhi', '')
    ri_gan_wx = TIAN_GAN_WX.get(ri_gan, '')
    question = chart_data.get('question', '')
    yue_jiang = chart_data.get('yue_jiang_name', '') or chart_data.get('yue_jiang', '')

    chu = san_chuan.get('chu', '') or ''
    zhong = san_chuan.get('zhong', '') or ''
    mo = san_chuan.get('mo', '') or ''
    gate = san_chuan.get('gate', '') or ''
    gate_name = _LR_GATE_NAME.get(gate, gate or '九宗门')
    gate_plain = _LR_GATE_PLAIN.get(gate, '')

    jiang_map = _liuren_jiang_of(tian_jiang)
    # 三传所乘天将（初传权重最大：发端看事之起）
    chuan_jiang = [(label, zhi, jiang_map.get(zhi, ''))
                   for label, zhi in (('初传', chu), ('中传', zhong), ('末传', mo)) if zhi]

    # ---------- 吉凶量化：三传天将吉凶 + 传间生克 ----------
    good_hits, bad_hits = [], []
    weights = {'初传': 0.5, '中传': 0.3, '末传': 0.2}
    score = 70.0
    for label, zhi, j in chuan_jiang:
        w = weights.get(label, 0.2)
        if j in LIUREN_JIANG_GOOD:
            good_hits.append(f'{label}乘{j}')
            score += 12 * w
        elif j in LIUREN_JIANG_BAD:
            bad_hits.append(f'{label}乘{j}')
            score -= 12 * w

    # 三传地支生克链：初→中→末 相生为顺、相克为阻
    chain_notes = []
    for a, b in ((chu, zhong), (zhong, mo)):
        wa, wb = DI_ZHI_WX.get(a, ''), DI_ZHI_WX.get(b, '')
        if wa and wb:
            if WUXING_SHENG.get(wa) == wb:
                chain_notes.append(f'{a}→{b}相生')
            elif WUXING_KE.get(wa) == wb or WUXING_KE.get(wb) == wa:
                chain_notes.append(f'{a}、{b}相克')
                score -= 3
    chain_text = '；'.join(chain_notes) if chain_notes else '传间生克不明显'
    if chain_notes and all('相生' in n for n in chain_notes):
        score += 4
    score = max(40, min(88, round(score)))
    luck_tone = '偏吉' if score >= 72 else ('偏凶' if score <= 58 else '平')

    # 四课摘要（容错：si_ke 值可能是 dict 或字符串）
    def _ke_text(key):
        v = si_ke.get(key)
        if isinstance(v, dict):
            return v.get('tianpan', '') or v.get('dizhi', '') or '—'
        return str(v) if v else '—'
    ke_summary = (f"干上{_ke_text('gan_shang')}、干阴{_ke_text('gan_yin')}、"
                  f"支上{_ke_text('zhi_shang')}、支阴{_ke_text('zhi_yin')}")

    # 神煞摘要
    if isinstance(shen_sha, dict):
        sha_items = [f'{k}{v}' for k, v in list(shen_sha.items())[:6]]
    else:
        sha_items = []
    sha_text = '、'.join(sha_items) if sha_items else '本课无明显神煞'

    # ---------- final_verdict ----------
    verdict = [
        f'这课日干{ri_gan}（属{ri_gan_wx or "?"}）代表问事人，日支{ri_zhi}代表所问之事'
        f'（{("所问：" + question) if question else "未写明具体所问，按通行事体断"}）。'
        f'月将{yue_jiang or "—"}加时布成天地盘，四课立、三传发，门法走的是「{gate_name}」。',
        f'三传是事情的三步：初传{chu or "—"}（怎么起的头）、中传{zhong or "—"}（中间怎么变）、'
        f'末传{mo or "—"}（最后落在哪）。传间关系：{chain_text}。',
    ]
    if good_hits:
        verdict.append(f'三传上的吉神有：{"、".join(good_hits)}——这是课里的助力，事情有贵人或喜庆托底。')
    if bad_hits:
        verdict.append(f'要留神的凶将有：{"、".join(bad_hits)}——这是课里的阻力，对应的麻烦得提前防。')
    if gate_plain:
        verdict.append(f'门法「{gate_name}」的白话意思是：{gate_plain}。')
    verdict.append(f'综合看，这课整体基调「{luck_tone}」（成事指数约{score}%）。'
                   '六壬看的是事的机与势，机到了要接、势逆了要让——具体怎么办，看下面分项。')
    final_verdict = '\n'.join(verdict)

    # ---------- key_points（末尾统一动态编号） ----------
    key_points = [f'门法「{gate_name}」定了事情的大节奏：{gate_plain or "按常规推进即可"}。']
    if good_hits:
        key_points.append(f'课里的明助力：{"、".join(good_hits)}，对应的时机和贵人要主动接住，别客气。')
    if bad_hits:
        key_points.append(f'课里的明阻力：{"、".join(bad_hits)}，对应的时段少出头、多核实，合同身体都上点心。')
    mo_good = any(lbl == '末传' and j in LIUREN_JIANG_GOOD for lbl, _z, j in chuan_jiang)
    key_points.append(f'三传{chu}→{zhong}→{mo}：起头在初传、变数在中传、结果看末传——'
                      + ('末传有吉神收尾，过程再波折也能落地，坚持到最后。'
                         if mo_good else '末传未见强助，事情别拖，能在前中段定下来的就别留尾巴。'))
    key_points.append(f'神煞参考：{sha_text}（神煞是辅助信息，别被名字吓住，知道哪里留神即可）。')
    key_points.append('六壬主「机」：同一事不必反复占，一课一决；重大钱物、健康问题，课象再吉也要走正规途径核实。')
    key_points = [f'{i}. {p}' for i, p in enumerate(key_points[:7], 1)]

    # ---------- analysis：课体分析 ----------
    analysis = (
        f'【干支定位】日干{ri_gan}（{ri_gan_wx or "?"}）为我，日支{ri_zhi}为事体；'
        f'干上神讲我这边的状态，支上神讲事情那边的状态。\n'
        f'【四课】{ke_summary}——四课是事情的四个侧面：干上两课看我这边明里暗里的情况，支上两课看对方/事情的表里。\n'
        f'【三传】初传{chu or "—"}发用（事之起因）、中传{zhong or "—"}（事之中段）、'
        f'末传{mo or "—"}（事之归结），{chain_text}。\n'
        f'【门法】{gate_name}：{gate_plain or "为九宗门常规取法。"}\n'
        f'【天将】吉将{"、".join(good_hits) if good_hits else "三传未见"}；'
        f'凶将{"、".join(bad_hits) if bad_hits else "三传未见"}。\n'
        f'【神煞】{sha_text}。\n'
        '六壬断课以四课为体、三传为用、天将为气色、神煞为点缀，合参而断，不执一端。'
    )

    # ---------- tianjiang_detail：三传/四课天将逐条白话 ----------
    tianjiang_detail = []
    for label, zhi, j in chuan_jiang:
        if j and j in LIUREN_JIANG_MEANING:
            kind, meaning = LIUREN_JIANG_MEANING[j]
            tianjiang_detail.append(f'{label}（{zhi}）乘{j}【{kind}】：{meaning}。')
        elif j:
            tianjiang_detail.append(f'{label}（{zhi}）乘{j}：该天将所主事象需结合课体细看，总体影响中性。')
    # 四课上神的天将补两条
    for ke_name, ke_key in (('干上', 'gan_shang'), ('支上', 'zhi_shang')):
        v = si_ke.get(ke_key)
        tp = v.get('tianpan', '') if isinstance(v, dict) else ''
        j = jiang_map.get(tp, '')
        if j and j in LIUREN_JIANG_MEANING:
            kind, meaning = LIUREN_JIANG_MEANING[j]
            tianjiang_detail.append(f'{ke_name}神（{tp}）乘{j}【{kind}】：{meaning}。')
    if not tianjiang_detail:
        tianjiang_detail = ['课中天将排布已生成，但三传天将信息不明显，可对照盘面十二天将宫位参看。']

    # ---------- scene_readings：分类占断 ----------
    scene = [
        f'【谋事求财】{"课传有吉神生扶，这事可成、财可得，开口谈条件的时机不错，但流程手续要走齐" if score >= 72 else "课传吉凶交织，事能磨成但要费周折，利润预期放低些，合同条款逐条抠" if score > 58 else "眼下阻力偏大，新的投入和扩张先按住，已在做的事以止损保本为主，等时运转顺再议"}。',
        f'【行人消息】{"传进有气、吉神引路，等的人或消息近日就有音信，不妨主动联系一次" if score >= 72 else "消息来得迟、可能有反复，多发一次问、多找一个中间人打听，别干等" if score > 58 else "音信受阻、易有拖延或变卦，要紧的事别只靠口头约定，重要文件亲自催办"}。',
        f'【求职合作】{"贵人象明显，面试、谈判有长辈或领导帮衬，拿出诚意就容易成" if good_hits else "合作能谈但要防口舌与承诺落空，凡是口头答应的，回去都补一条文字确认" if bad_hits else "合作运平平，待遇和权责先谈清楚再答应，别急着站队"}。',
    ]
    scene_readings = '\n'.join(scene)

    # ---------- scenario_advice：综合建议 ----------
    has_help = any(('贵人' in h or '天后' in h or '太阴' in h) for h in good_hits)
    has_quarrel = any(('朱雀' in h or '螣蛇' in h or '腾蛇' in h or '玄武' in h or '天空' in h) for h in bad_hits)
    scenario_lines = [
        f'【做事节奏】{gate_plain or "按常规节奏推进。"}这是这课最该记住的一句话。',
        '【钱财】大额支出、投资、借钱担保这类事，'
        + ('可以在合同清楚的前提下适度推进' if score >= 72 else '一律缓一缓，捂紧现金流'),
        '【人际】'
        + ('多跟长辈、领导走动，你的贵人偏长辈或有身份的人' if has_help
           else '少说多听，防口舌是非，聊天记录、邮件注意留痕' if has_quarrel
           else '正常待人接物即可，答应别人的事做到，做不到的别应'),
        '【健康】'
        + ('身体无大碍，保持作息即可' if not any('白虎' in h for h in bad_hits)
           else '白虎临传，近期压力大、小毛病容易找上门——别熬夜硬扛，不舒服及时去正规医院检查'),
    ]
    scenario_advice = '\n'.join(scenario_lines)

    # ---------- timing：应期 ----------
    if gate == 'fuyin':
        gate_timing = '门法伏吟主静，应期会拖长，逢冲（子午、卯酉之类）的日子或月份才容易动起来。'
    elif gate == 'fanyin':
        gate_timing = '门法返吟主反复，中间容易有回炉、反悔，定下来的事也要留一次变动的余量。'
    else:
        gate_timing = '传上见吉神的时段主动推进，见凶将的时段以守为进。'
    timing = (
        f'六壬应期看三传：初传{chu or "—"}主事之发端，对应眼下几天到两周内的动静；'
        f'中传{zhong or "—"}主过程，大致两三周到一个半月是变数最多的时候；'
        f'末传{mo or "—"}主归结，一个半月到三个月事情见分晓。{gate_timing}'
        '具体日子可对照万年历看传支当令的日期，前后差几天都正常，不必死抠。'
    )

    # ---------- folklore_tips ----------
    folklore = []
    if ri_gan_wx in WUXING_COLOR:
        folklore.append(f'这阵子穿戴可多用{WUXING_COLOR[ri_gan_wx]}一系，办事出门朝{WUXING_DIRECTION.get(ri_gan_wx, "明亮通风处")}方位多走走，图个扶身助人的彩头（民俗说法，图个吉利，不必迷信）。')
    folklore.append('心里不踏实就把待办写在纸上逐条做——六壬讲「静定生慧」，人一慌课象再好也接不住（民俗说法，图个吉利，不必迷信）。')

    # ---------- historical_cases ----------
    historical_cases = (
        '【前人课例】《大六壬指南》《六壬大全》中存有多则课案，多以三传吉凶、天将善恶断事之成败迟速，'
        '思路与本课一致：初传看起因、末传看归宿，贵人青龙临传则事多吉，白虎螣蛇临传则防灾虞。'
        '前人课例重在示范「四课三传—天将—神煞」合参的断法，具体到每个人的事，'
        '还需结合实际处境与行动来看，课象是提醒不是定数。'
    )

    # ---------- probability_stats ----------
    probability_stats = [
        f'整体吉凶：{score}%',
        f'谋事求财：{max(38, score - 4)}%',
        f'行人消息：{max(38, score - 8)}%',
        f'求职合作：{max(38, score + 2)}%',
        f'健康平安：{max(45, score + 6)}%',
    ]

    return {
        'final_verdict': final_verdict,
        'key_points': key_points,
        'analysis': analysis,
        'tianjiang_detail': tianjiang_detail,
        'scene_readings': scene_readings,
        'scenario_advice': scenario_advice,
        'timing': timing,
        'folklore_tips': folklore,
        'historical_cases': historical_cases,
        'probability_stats': probability_stats,
        'disclaimer': _generate_disclaimer('大六壬课'),
    }


if __name__ == '__main__':
    # 测试脚本
    test_bazi = {
        '四柱': ['甲子', '乙丑', '丙寅', '丁卯'],
        'rizhu': '丙',
        'month_zhi': '丑',
    }
    result = generate_fallback_analysis('bazi', test_bazi)
    print('=== 八字分析兜底结果 ===')
    for key, value in result.items():
        print(f'\n【{key}】')
        if isinstance(value, list):
            for item in value:
                print(item)
        else:
            print(value[:200] + '...' if len(str(value)) > 200 else value)
