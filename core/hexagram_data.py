"""
64卦完整数据库 - 数据已迁移至MySQL数据库
所有卦象数据通过 DatabaseManager 查询
"""
from core.database_manager import DatabaseManager


def _get_db():
    """获取数据库管理器单例"""
    return DatabaseManager()


def get_hexagrams_full():
    """获取64卦完整数据 {hexagram_id: info_dict}"""
    db = _get_db()
    rows = db.get_hexagram_64()
    result = {}
    for key, info in rows.items():
        result[info['hexagram_id']] = {
            'name': info['name'],
            'upper': info['upper_num'],
            'lower': info['lower_num'],
            'wuxing': info['wuxing'],
            'description': info['description']
        }
    return result


def get_gan_yao_full():
    """获取64卦爻辞数据 {hexagram_id: yao_ci_info}"""
    db = _get_db()
    rows = db.get_hexagram_64()
    result = {}
    for key, info in rows.items():
        hex_id = info['hexagram_id']
        yao_list = db.get_hexagram_yao_ci(hex_id)
        yao_ci = []
        for yao in yao_list:
            yao_ci.append({
                'yao': yao['yao_name'],
                'text': yao['yao_text'],
                'meaning': yao['meaning']
            })
        result[hex_id] = {
            'name': info['name'],
            'description': info['description'],
            'judgment': info['judgment'],
            'gua_ci': info['gua_ci'],
            'yao_ci': yao_ci
        }
    return result


# 兼容旧代码的惰性加载
class _LazyHexagramsFull:
    """惰性加载64卦完整数据，首次访问时才查询数据库并缓存。"""
    def __init__(self):
        """初始化空缓存，数据在首次访问时由 _load 加载。"""
        self._data = None

    def _load(self):
        """调用 get_hexagrams_full 加载并缓存64卦基础数据，重复调用只加载一次。"""
        if self._data is None:
            self._data = get_hexagrams_full()
        return self._data

    def __getitem__(self, key):
        """按 hexagram_id 取下卦完整信息，触发懒加载。"""
        return self._load()[key]

    def __iter__(self):
        """遍历所有 hexagram_id 键。"""
        return iter(self._load())

    def __contains__(self, key):
        """判断某 hexagram_id 是否存在。"""
        return key in self._load()

    def items(self):
        """返回 (hexagram_id, 卦信息) 的视图。"""
        return self._load().items()

    def keys(self):
        """返回所有 hexagram_id 键的视图。"""
        return self._load().keys()

    def values(self):
        """返回所有卦信息值的视图。"""
        return self._load().values()

    def get(self, key, default=None):
        """兼容 dict.get：缺失键时返回 default。"""
        return self._load().get(key, default)


class _LazyGanYaoFull:
    """惰性加载64卦爻辞数据，首次访问时才查询数据库并缓存。"""
    def __init__(self):
        """初始化空缓存，数据在首次访问时由 _load 加载。"""
        self._data = None

    def _load(self):
        """调用 get_gan_yao_full 加载并缓存64卦卦辞/爻辞，重复调用只加载一次。"""
        if self._data is None:
            self._data = get_gan_yao_full()
        return self._data

    def __getitem__(self, key):
        """按 hexagram_id 取该卦的卦辞与六爻爻辞，触发懒加载。"""
        return self._load()[key]

    def __iter__(self):
        """遍历所有 hexagram_id 键。"""
        return iter(self._load())

    def __contains__(self, key):
        """判断某 hexagram_id 是否存在。"""
        return key in self._load()

    def items(self):
        """返回 (hexagram_id, 卦辞爻辞信息) 的视图。"""
        return self._load().items()

    def keys(self):
        """返回所有 hexagram_id 键的视图。"""
        return self._load().keys()

    def values(self):
        """返回所有卦辞爻辞信息值的视图。"""
        return self._load().values()

    def get(self, key, default=None):
        """兼容 dict.get：缺失键时返回 default。"""
        return self._load().get(key, default)


# 兼容旧代码的模块级变量
HEXAGRAMS_FULL = _LazyHexagramsFull()
GAN_YAO_FULL = _LazyGanYaoFull()
