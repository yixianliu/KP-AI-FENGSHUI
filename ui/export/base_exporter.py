"""
导出基类
定义导出器的统一接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

# ==================== 导出章节定义 ====================
# 统一的章节清单（顺序即导出顺序）。key 为章节标识，label 为显示名。
# 'yunshi' 为虚拟章节，对应 data 中的 dayun + liunian 两个键。
CHAPTERS: List[tuple] = [
    ('basic_info', '基本信息'),
    ('bazi_types', '命局类型'),
    ('bazi', '四柱八字'),
    ('wuxing', '五行分析'),
    ('shishen', '十神分析'),
    ('yunshi', '大运流年'),
    ('yuncheng', '运程总结'),
    ('analysis', '吉凶批注'),
    ('ai_analysis', 'universal.ai.SECTION_TITLE'),
    ('meihua', '梅花易数'),
    ('liuren', '大六壬起课'),
    ('zonghe', '综合建议'),
]

# 四柱在两种上游路径下的键名：旧结构集中在 data['bazi'] 子字典，
# Service 路径（bazi_service）则直接摊平在顶层，两路都要能取到。
PILLAR_FIELDS: List[str] = ['year_pillar', 'month_pillar',
                            'day_pillar', 'hour_pillar']

# 四柱字段 -> 中文标签。Excel/CSV 的通用键值区块是直接把 dict 的 key 当标签
# 输出的，不映射的话导出件里会出现 year_pillar 这类英文字段名。
PILLAR_LABELS: Dict[str, str] = {
    'year_pillar': '年柱',
    'month_pillar': '月柱',
    'day_pillar': '日柱',
    'hour_pillar': '时柱',
}

# 章节标识 -> 实际数据键（在 result data 字典中）
# 'bazi' / 'wuxing' 各带一个回退键：Service 路径不用 data['bazi'] 而是顶层
# 四柱字段，五行也不用 data['wuxing'] 而是 wuxing_detail。若只写主键，
# filter_export_data 会把真实数据整章过滤掉（导出件缺「四柱八字」「五行分析」）。
CHAPTER_KEYS: Dict[str, List[str]] = {
    'basic_info': ['basic_info'],
    'bazi_types': ['bazi_types'],
    'bazi': ['bazi'] + PILLAR_FIELDS,
    'wuxing': ['wuxing', 'wuxing_detail'],
    'shishen': ['shishen'],
    'yunshi': ['dayun', 'liunian'],
    'yuncheng': ['yuncheng'],
    'analysis': ['analysis'],
    'ai_analysis': ['ai_analysis'],
    'meihua': ['meihua_data', 'meihua_ai'],
    'liuren': ['liuren_data', 'liuren_ai'],
    'zonghe': ['zonghe'],
}

# 兼容旧导出字段：mingli（神煞）未纳入统一章节，按需保留
_LEGACY_KEYS = ['mingli']


def filter_export_data(data: Dict[str, Any], selected: List[str]) -> Dict[str, Any]:
    """
    仅保留 selected 章节对应的数据键，返回新字典（不修改原 data）。

    Args:
        data: 完整的排盘结果字典
        selected: 选中的章节标识列表（见 CHAPTERS 的 key）
    Returns:
        过滤后的字典；若 selected 为空，返回空字典。
    """
    keep: set = set(_LEGACY_KEYS)  # 神煞等附加信息始终保留
    for ch in (selected or []):
        keep.update(CHAPTER_KEYS.get(ch, [ch]))
    return {k: v for k, v in data.items() if k in keep}


def has_chapter(data: Dict[str, Any], key: str) -> bool:
    """
    判断某章节是否有可渲染的数据。
    - 字典类章节：非空字典
    - 列表类章节（analysis）：非空列表
    - 大运流年（yunshi）：dayun.periods 或 liunian.years 任一非空
    - 四柱（bazi）：extract_pillars 结果非空
    - 五行（wuxing）：extract_wuxing 结果非空
    """
    if key == 'yunshi':
        dayun = data.get('dayun') or {}
        liunian = data.get('liunian') or {}
        periods = dayun.get('periods') if isinstance(dayun, dict) else []
        years = liunian.get('years') if isinstance(liunian, dict) else []
        return bool(periods or years)
    if key == 'bazi':
        return bool(extract_pillars(data))
    if key == 'wuxing':
        return bool(extract_wuxing(data))
    val = data.get(key)
    if val is None:
        return False
    if isinstance(val, (list, tuple, dict, str)):
        return len(val) > 0
    return True


def extract_pillars(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    取四柱干支，兼容两种上游结构。

    旧结构：data['bazi'] = {'year_pillar': '庚午', ...}
    Service 结构：四柱直接摊平在 data 顶层（year_pillar / month_pillar /
    day_pillar / hour_pillar）。两种都返回同构的 dict，导出器无需分支。

    Args:
        data: 排盘结果字典

    Returns:
        dict: {year_pillar, month_pillar, day_pillar, hour_pillar}，
        只含有值的键；两路都取不到时返回空 dict
    """
    bz = data.get('bazi') or {}
    if not isinstance(bz, dict):
        bz = {}
    out = {k: bz.get(k) for k in PILLAR_FIELDS if bz.get(k)}
    if out:
        return out
    return {k: data.get(k) for k in PILLAR_FIELDS if data.get(k)}


def extract_wuxing(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    取五行分值，兼容两种上游结构。

    旧结构：data['wuxing'] = {'木': 12.5, ...}
    Service 结构：data['wuxing_detail'] = {'木': {'percentage': 8.0,
    'score': 0.24, ...}, ...}，且 data['wuxing'] 常为 None。回退时优先取
    percentage（已是百分数语义），缺失再退 score。

    Args:
        data: 排盘结果字典

    Returns:
        dict: {五行名: 分值}，取不到时返回空 dict
    """
    wx = data.get('wuxing') or {}
    if not isinstance(wx, dict):
        wx = {}
    if wx:
        return dict(wx)
    detail = data.get('wuxing_detail') or {}
    if not isinstance(detail, dict):
        return {}
    out: Dict[str, Any] = {}
    for name, info in detail.items():
        if isinstance(info, dict):
            val = info.get('percentage')
            if val is None:
                val = info.get('score')
            if val is not None:
                out[name] = val
        elif info is not None:
            out[name] = info
    return out


def normalize_shensha(shensha: Any) -> List[tuple]:
    """
    把神煞数据归一化为 [(名称, 释义), ...]，兼容三种上游形态。

    实际排盘结果里 mingli['shensha'] 是 {'positive': [...], 'negative': [...],
    'neutral': [...]} 的分组字典，直接迭代只会得到字符串键，再调 .get() 必然
    AttributeError: 'str' object has no attribute 'get'，导致整份导出失败
    （export 返回 False、文件不落盘）。这里统一摊平，同时兼容「列表套字典」
    与「纯字符串列表」两种历史形态。

    Args:
        shensha: 神煞原始数据（分组 dict / list of dict / list of str）

    Returns:
        list[tuple[str, str]]: 归一化后的 (名称, 释义) 列表
    """
    items: List[Any] = []
    if isinstance(shensha, dict):
        for _grp, members in shensha.items():
            if isinstance(members, (list, tuple)):
                items.extend(members)
            elif members:
                items.append(members)
    elif isinstance(shensha, (list, tuple)):
        items = list(shensha)

    out: List[tuple] = []
    for it in items:
        if isinstance(it, dict):
            name = str(it.get('name', '') or '')
            desc = str(it.get('description', '') or it.get('detailed', '') or '')
        else:
            name, desc = str(it), ''
        if name:
            out.append((name, desc))
    return out


class BaseExporter(ABC):
    """导出器基类"""

    @abstractmethod
    def export(self, data: Dict[str, Any], file_path: str) -> bool:
        """
        导出数据到文件

        Args:
            data: 导出数据字典
            file_path: 目标文件路径

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """
        获取文件扩展名

        Returns:
            文件扩展名（如 '.csv'、'.xlsx'）
        """
        pass