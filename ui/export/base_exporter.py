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
    ('ai_analysis', '龙虎山大师兄智能分析'),
    ('meihua', '梅花易数'),
    ('liuren', '大六壬起课'),
    ('zonghe', '综合建议'),
]

# 章节标识 -> 实际数据键（在 result data 字典中）
CHAPTER_KEYS: Dict[str, List[str]] = {
    'basic_info': ['basic_info'],
    'bazi_types': ['bazi_types'],
    'bazi': ['bazi'],
    'wuxing': ['wuxing'],
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
    """
    if key == 'yunshi':
        dayun = data.get('dayun') or {}
        liunian = data.get('liunian') or {}
        periods = dayun.get('periods') if isinstance(dayun, dict) else []
        years = liunian.get('years') if isinstance(liunian, dict) else []
        return bool(periods or years)
    val = data.get(key)
    if val is None:
        return False
    if isinstance(val, (list, tuple, dict, str)):
        return len(val) > 0
    return True


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