"""
八字「类型」分类体系 - 单一权威词表
为八字排盘提供统一、清晰、可参考的类型分类：
  - 排盘类型 (pan_type)   ：本程序支持的排盘种类
  - 日主强弱 (strength)    ：身强 / 身弱 / 中和
  - 格局类型 (geju_type)  ：专旺格 / 从格 / 扶抑格 / 中和格
  - 五行旺衰类别 (wuxing) ：旺极 / 偏旺 / 均衡 / 偏弱 / 极弱

每个类型均提供「含义」与「用途」，确保类型字段在排盘结果中具备实际参考价值。
所有展示层（输入面板 / 结果面板 / 主流程）均从此模块取数，避免词表不一致。
"""
from typing import Dict, Any, List, Optional

# ===================== 排盘类型 =====================
# 代码 <-> 显示名 的唯一映射。本程序实际支持的排盘类型。
PAN_TYPE_NAME: Dict[str, str] = {
    'bazi': '八字四柱',
    'meihua': '梅花易数',
}
PAN_TYPE_DESC: Dict[str, str] = {
    'bazi': '以出生年、月、日、时的天干地支四柱推断命局，本程序八字排盘主类型',
    'meihua': '以时间、数字或测字起卦，依体用生克解读所问之事',
}


def get_pan_type_name(code: str) -> str:
    """排盘类型代码 -> 中文显示名（缺省回退『八字四柱』）"""
    return PAN_TYPE_NAME.get(code, '八字四柱')


# ===================== 日主强弱 =====================
STRENGTH_INFO: Dict[str, Dict[str, str]] = {
    '身强': {
        'meaning': '日主五行能量充沛，得月令、得地或得生扶',
        'purpose': '宜克、泄、耗以平衡，喜财、官、食伤',
    },
    '身弱': {
        'meaning': '日主五行能量不足，失令、失地又少生扶',
        'purpose': '宜生、扶以助身，喜印星、比劫',
    },
    '中和': {
        'meaning': '日主五行能量均衡，不偏不倚',
        'purpose': '格局清正，喜忌随大运流年而转',
    },
}


def get_strength_info(level: str) -> Dict[str, str]:
    return STRENGTH_INFO.get(level, {'meaning': '', 'purpose': ''})


# ===================== 格局类型 =====================
GEJU_INFO: Dict[str, Dict[str, str]] = {
    '专旺格': {
        'meaning': '某一五行极旺，日主顺从旺气而专',
        'purpose': '顺势而为，忌克泄逆其旺势',
        'subs': '曲直格(木) / 炎上格(火) / 稼穑格(土) / 从革格(金) / 润下格(水)',
    },
    '从格': {
        'meaning': '日主极弱无根，弃命从旺神',
        'purpose': '顺从旺神，忌生扶帮身',
        'subs': '从财格 / 从官杀格 / 从儿格 / 从势格',
    },
    '扶抑格': {
        'meaning': '日主有根有气，需扶抑以求平衡',
        'purpose': '身强用克泄耗，身弱用生扶',
        'subs': '身强用财格 / 杀印相生格 / 食神吐秀格 / 身弱用印格',
    },
    '中和格': {
        'meaning': '五行均衡、格局清正',
        'purpose': '财官印得位，多主富贵双全',
        'subs': '财官双美格 / 印绶生贵格',
    },
}


def get_geju_info(geju_type: str) -> Dict[str, str]:
    return GEJU_INFO.get(geju_type, {'meaning': '', 'purpose': '', 'subs': ''})


# ===================== 五行旺衰类别 =====================
# 由五行能量摘要（如『火偏旺，水极弱』）解析出每个类别的含义
WUXING_CATEGORY_INFO: Dict[str, str] = {
    '旺极': '某五行能量过盛，需克制疏导，过犹不及',
    '偏旺': '某五行能量偏强，宜适当泄耗以归中和',
    '均衡': '五行能量分布均匀，格局清和',
    '偏弱': '某五行能量不足，宜补益生扶',
    '极弱': '某五行能量枯竭，需大力生扶或顺势而从',
}

# 类别 -> 优先级（用于排序展示：先旺后弱）
_WUXING_CATEGORY_ORDER = ['旺极', '偏旺', '均衡', '偏弱', '极弱']


def get_wuxing_category_info(summary: str) -> List[Dict[str, str]]:
    """从五行摘要文本中提取命中的旺衰类别及其含义。

    Args:
        summary: 如 '火偏旺，水极弱' 或 '五行均衡'
    Returns:
        [{'label': '偏旺', 'element': '火', 'meaning': '...'}, ...]
    """
    if not summary:
        return []
    results: List[Dict[str, str]] = []
    for cat in _WUXING_CATEGORY_ORDER:
        if cat in summary:
            # 提取该类别前的五行（如『火偏旺』-> 火）
            idx = summary.find(cat)
            element = ''
            for ch in summary[max(0, idx - 2):idx]:
                if ch in ('木', '火', '土', '金', '水'):
                    element = ch
                    break
            results.append({
                'label': cat,
                'element': element,
                'meaning': WUXING_CATEGORY_INFO.get(cat, ''),
            })
    return results


def get_bazi_types_payload(
    pan_type_code: str = 'bazi',
    strength: str = '',
    geju_type: str = '',
    geju_name: str = '',
    geju_desc: str = '',
    wuxing_summary: str = '',
    rizhu_wx: str = '',
    yongshen: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """组装一份完整的「命局类型」数据，供结果面板统一渲染。

    将所有零散的类型字段汇聚为单一结构，并自动补全含义/用途，
    保证类型字段在结果中始终具备参考价值。
    """
    return {
        'pan_type': get_pan_type_name(pan_type_code),
        'strength': strength,
        'strength_info': get_strength_info(strength),
        'geju_type': geju_type,
        'geju_name': geju_name,
        'geju_info': get_geju_info(geju_type),
        'geju_desc': geju_desc,
        'wuxing_summary': wuxing_summary,
        'wuxing_categories': get_wuxing_category_info(wuxing_summary),
        'rizhu_wx': rizhu_wx,
        'yongshen': yongshen or {},
    }


# ===================== 用神 / 喜神 / 忌神 =====================
# 由『日主五行 + 日主强弱』推导。命理核心：身弱喜生扶、身强喜克泄耗。
_WUXING_GENERATES = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}  # 我生
_WUXING_GENERATED_BY = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}  # 生我
_WUXING_OVERCOMES = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}  # 我克
_WUXING_OVERCOMED_BY = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}  # 克我

_REL_NAME = {
    '同我': '比劫', '生我': '印星', '我生': '食伤',
    '我克': '财星', '克我': '官杀',
}


def _relation(dayan: str, other: str) -> str:
    if dayan == other:
        return '同我'
    if _WUXING_GENERATED_BY.get(dayan) == other:
        return '生我'
    if _WUXING_GENERATES.get(dayan) == other:
        return '我生'
    if _WUXING_OVERCOMES.get(dayan) == other:
        return '我克'
    if _WUXING_OVERCOMED_BY.get(dayan) == other:
        return '克我'
    return ''


def get_yongshen(rizhu_wx: str, strength: str) -> Dict[str, Any]:
    """由日主五行与强弱推导用神 / 喜神 / 忌神。

    Args:
        rizhu_wx: 日主五行（木/火/土/金/水）
        strength:  日主强弱（身强/身弱/中和）

    Returns:
        {
          'rizhu_wx','strength',
          'yongshen': 用神五行, 'yongshen_name': 用神十神名,
          'xishen': [喜神五行...], 'xishen_names': [喜神十神名...],
          'jishen': [忌神五行...], 'jishen_names': [...],
          'meaning','purpose','all': [每五行的关系...],
        }
    """
    if not rizhu_wx:
        return {}
    rels = []
    for el in ('木', '火', '土', '金', '水'):
        rel = _relation(rizhu_wx, el)
        if rel:
            rels.append({'element': el, 'relation': rel, 'name': _REL_NAME[rel]})

    if strength == '身弱':
        xi = [r for r in rels if r['relation'] in ('生我', '同我')]
        ji = [r for r in rels if r['relation'] in ('我生', '我克', '克我')]
        yong = next((r for r in rels if r['relation'] == '生我'), None) or \
               next((r for r in rels if r['relation'] == '同我'), None)
        meaning = '日主偏弱，宜生扶帮身'
        purpose = '用神取印星、比劫以助身；忌食伤、财星、官杀耗克'
    elif strength == '身强':
        xi = [r for r in rels if r['relation'] in ('克我', '我生', '我克')]
        ji = [r for r in rels if r['relation'] in ('生我', '同我')]
        yong = next((r for r in rels if r['relation'] == '我克'), None) or \
               next((r for r in rels if r['relation'] == '克我'), None)
        meaning = '日主偏强，宜克泄耗'
        purpose = '用神取财星、官杀、食伤以制衡；忌印星、比劫助身'
    else:  # 中和
        xi = rels
        ji = []
        yong = None
        meaning = '日主中和，不偏不倚'
        purpose = '喜忌随大运流年而转，宜顺势而为'

    return {
        'rizhu_wx': rizhu_wx,
        'strength': strength,
        'yongshen': yong['element'] if yong else '',
        'yongshen_name': yong['name'] if yong else '',
        'xishen': [r['element'] for r in xi],
        'xishen_names': [r['name'] for r in xi],
        'jishen': [r['element'] for r in ji],
        'jishen_names': [r['name'] for r in ji],
        'meaning': meaning,
        'purpose': purpose,
        'all': rels,
    }
