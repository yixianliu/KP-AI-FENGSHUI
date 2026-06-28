"""
命理知识库 - 结构化存储八字命理和梅花易数的专业知识
支持术语查询、知识检索、分类浏览等功能
为AI分析提供结构化知识支撑
数据来源：MySQL数据库
"""
import json
from core.database_manager import DatabaseManager
from core.wuxing import TIAN_GAN_WUXING, DI_ZHI_WUXING
from core.hexagram_analyzer import BAGUA, HEXAGRAMS


def _get_db():
    return DatabaseManager()


def _load_wuxing_knowledge():
    """从数据库加载五行知识"""
    db = _get_db()
    rows = db.get_wuxing_knowledge()
    result = {}
    for name, info in rows.items():
        result[name] = {
            'nature': info.get('nature', ''),
            'characteristics': json.loads(info['characteristics']) if isinstance(info.get('characteristics'), str) else info.get('characteristics', []),
            'direction': info.get('direction', ''),
            'season': info.get('season', ''),
            'color': info.get('color', ''),
            'organ': json.loads(info['organs']) if isinstance(info.get('organs'), str) else info.get('organs', []),
            'taste': info.get('taste', ''),
            'number': info.get('luck_number', 0),
            'positive_traits': json.loads(info['positive_traits']) if isinstance(info.get('positive_traits'), str) else info.get('positive_traits', []),
            'negative_traits': json.loads(info['negative_traits']) if isinstance(info.get('negative_traits'), str) else info.get('negative_traits', []),
            'career': json.loads(info['careers']) if isinstance(info.get('careers'), str) else info.get('careers', []),
            'health_advice': info.get('health_advice', ''),
            'description': info.get('description', '')
        }
    return result


def _load_wuxing_relations():
    """从数据库加载五行关系"""
    db = _get_db()
    rows = db.get_wuxing_relations()
    return rows


def _load_shishen_knowledge():
    """从数据库加载十神知识"""
    db = _get_db()
    rows = db.get_shishen_knowledge()
    result = {}
    for name, info in rows.items():
        result[name] = {
            'type': info.get('shishen_type', ''),
            'yinyang': info.get('yinyang', ''),
            'description': info.get('description', ''),
            'meaning': info.get('meaning', ''),
            'positive': json.loads(info['positive']) if isinstance(info.get('positive'), str) else info.get('positive', []),
            'negative': json.loads(info['negative']) if isinstance(info.get('negative'), str) else info.get('negative', []),
            'career': info.get('career', ''),
            'wealth': info.get('wealth', ''),
            'love': info.get('love', '')
        }
    return result


def _load_tiangan_dizhi_knowledge():
    """从数据库加载天干地支知识"""
    db = _get_db()
    tian_gan_rows = db.get_tian_gan_all()
    di_zhi_rows = db.get_di_zhi_all()
    di_zhi_hidden = db.get_di_zhi_hidden_gan_simple()
    
    tiangan = {}
    for row in tian_gan_rows:
        gan = row['gan']
        tiangan[gan] = {
            'wuxing': ('阳' if row.get('yinyang') == '阳' else '阴') + row.get('wuxing', ''),
            'direction': row.get('direction', ''),
            'season': row.get('season', ''),
            'meaning': row.get('meaning', ''),
            'organ': row.get('organ', ''),
            'body': row.get('body', '')
        }
    
    dizhi = {}
    for row in di_zhi_rows:
        zhi = row['zhi']
        dizhi[zhi] = {
            'wuxing': ('阳' if row.get('yinyang') == '阳' else '阴') + row.get('wuxing', ''),
            'direction': row.get('direction', ''),
            'season': row.get('season', ''),
            'month': row.get('lunar_month', ''),
            'hour': row.get('hour_range', ''),
            'meaning': row.get('meaning', ''),
            'organ': row.get('organ', ''),
            'hidden_stems': di_zhi_hidden.get(zhi, [])
        }
    
    return {'tiangan': tiangan, 'dizhi': dizhi}


def _load_shier_changsheng():
    """从数据库加载十二长生知识"""
    db = _get_db()
    rows = db.get_shier_changsheng()
    result = {}
    for name, info in rows.items():
        result[name] = {
            'stage': info.get('stage', 0),
            'meaning': info.get('meaning', ''),
            'characteristics': json.loads(info['characteristics']) if isinstance(info.get('characteristics'), str) else info.get('characteristics', []),
            'influence': info.get('influence', '')
        }
    return result


def _load_meihua_knowledge():
    """从数据库加载梅花易数知识"""
    db = _get_db()
    return db.get_meihua_knowledge()


# 惰性加载模块级变量
class _LazyLoader:
    def __init__(self, loader):
        self._loader = loader
        self._data = None

    def _load(self):
        if self._data is None:
            self._data = self._loader()
        return self._data

    def __getitem__(self, key):
        return self._load()[key]

    def get(self, key, default=None):
        return self._load().get(key, default)

    def items(self):
        return self._load().items()

    def keys(self):
        return self._load().keys()

    def values(self):
        return self._load().values()

    def __iter__(self):
        return iter(self._load())

    def __len__(self):
        return len(self._load())

    def __contains__(self, key):
        return key in self._load()


WUXING_KNOWLEDGE = _LazyLoader(_load_wuxing_knowledge)
WUXING_RELATIONS = _LazyLoader(_load_wuxing_relations)
SHISHEN_KNOWLEDGE = _LazyLoader(_load_shishen_knowledge)
TIANGAN_DIZHI_KNOWLEDGE = _LazyLoader(_load_tiangan_dizhi_knowledge)
SHIER_CHANGSHENG_KNOWLEDGE = _LazyLoader(_load_shier_changsheng)
MEIHUA_KNOWLEDGE = _LazyLoader(_load_meihua_knowledge)


def _build_term_index():
    """构建术语索引，支持快速查询"""
    terms = {}

    for wx, info in WUXING_KNOWLEDGE.items():
        terms[wx] = {
            'category': '五行',
            'name': wx,
            'description': info['description'],
            'details': info
        }

    for shishen, info in SHISHEN_KNOWLEDGE.items():
        terms[shishen] = {
            'category': '十神',
            'name': shishen,
            'description': info['description'],
            'details': info
        }

    for tiangan, info in TIANGAN_DIZHI_KNOWLEDGE['tiangan'].items():
        terms[tiangan] = {
            'category': '天干',
            'name': tiangan,
            'description': info['meaning'],
            'details': info
        }

    for dizhi, info in TIANGAN_DIZHI_KNOWLEDGE['dizhi'].items():
        terms[dizhi] = {
            'category': '地支',
            'name': dizhi,
            'description': info['meaning'],
            'details': info
        }

    for shen, info in SHIER_CHANGSHENG_KNOWLEDGE.items():
        terms[shen] = {
            'category': '十二长生',
            'name': shen,
            'description': info['meaning'],
            'details': info
        }

    for bagua_num, info in BAGUA.items():
        terms[info['name']] = {
            'category': '八卦',
            'name': info['name'],
            'description': info['description'],
            'details': info
        }

    return terms


class _LazyTermIndex:
    def __init__(self):
        self._data = None

    def _load(self):
        if self._data is None:
            self._data = _build_term_index()
        return self._data

    def __getitem__(self, key):
        return self._load()[key]

    def get(self, key, default=None):
        return self._load().get(key, default)

    def items(self):
        return self._load().items()

    def keys(self):
        return self._load().keys()

    def values(self):
        return self._load().values()

    def __iter__(self):
        return iter(self._load())

    def __len__(self):
        return len(self._load())

    def __contains__(self, key):
        return key in self._load()


TERM_INDEX = _LazyTermIndex()


class KnowledgeBase:
    """命理知识库 - 提供结构化的命理知识查询和检索"""
    
    def __init__(self):
        self.wuxing = WUXING_KNOWLEDGE
        self.shishen = SHISHEN_KNOWLEDGE
        self.tiangan_dizhi = TIANGAN_DIZHI_KNOWLEDGE
        self.shier_changsheng = SHIER_CHANGSHENG_KNOWLEDGE
        self.wuxing_relations = WUXING_RELATIONS
        self.meihua = MEIHUA_KNOWLEDGE
        self.bagua = BAGUA
        self.hexagrams = HEXAGRAMS
        self.term_index = TERM_INDEX
    
    def search_term(self, keyword):
        """
        搜索术语，支持模糊匹配
        返回匹配的术语列表
        """
        results = []
        keyword = keyword.strip()
        
        if not keyword:
            return results
        
        if keyword in self.term_index:
            results.append(self.term_index[keyword])
            return results
        
        for term, info in self.term_index.items():
            if keyword in term or keyword in info['description']:
                results.append(info)
        
        return results
    
    def get_category_terms(self, category):
        """
        获取指定分类的所有术语
        分类：五行、十神、天干、地支、十二长生、八卦
        """
        results = []
        for term, info in self.term_index.items():
            if info['category'] == category:
                results.append(info)
        return results
    
    def get_wuxing_info(self, wuxing_name):
        """获取五行详细信息"""
        return self.wuxing.get(wuxing_name, {})
    
    def get_shishen_info(self, shishen_name):
        """获取十神详细信息"""
        return self.shishen.get(shishen_name, {})
    
    def get_shier_changsheng_info(self, shen_name):
        """获取十二长生详细信息"""
        return self.shier_changsheng.get(shen_name, {})
    
    def get_bagua_info(self, num_or_name):
        """获取八卦信息，支持按数字或名称查询"""
        if isinstance(num_or_name, int):
            return self.bagua.get(num_or_name, {})
        else:
            for num, info in self.bagua.items():
                if info['name'] == num_or_name:
                    info_copy = info.copy()
                    info_copy['num'] = num
                    return info_copy
            return {}
    
    def get_hexagram_info(self, upper_num, lower_num):
        """获取64卦信息"""
        key = (upper_num, lower_num)
        return self.hexagrams.get(key, {})
    
    def get_meihua_knowledge(self, section=None):
        """获取梅花易数相关知识"""
        if section:
            return self.meihua.get(section, {})
        return self.meihua
    
    def build_bazi_knowledge_context(self, bazi_data):
        """
        构建八字分析的知识上下文
        为AI分析提供结构化的命理知识背景
        """
        context_parts = []
        context_parts.append("=== 命理知识库 ===")
        
        rizhu = bazi_data.get('rizhu', '')
        if rizhu:
            rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
            wx_info = self.get_wuxing_info(rizhu_wx)
            if wx_info:
                context_parts.append(f"\n【日主五行：{rizhu_wx}】")
                context_parts.append(f"特性：{wx_info.get('description', '')}")
                context_parts.append(f"正面特质：{', '.join(wx_info.get('positive_traits', []))}")
                context_parts.append(f"负面特质：{', '.join(wx_info.get('negative_traits', []))}")
                context_parts.append(f"适合职业：{wx_info.get('career', '')}")
                context_parts.append(f"健康建议：{wx_info.get('health_advice', '')}")
        
        wuxing_result = bazi_data.get('wuxing', {})
        if wuxing_result:
            context_parts.append(f"\n【五行生克关系】")
            context_parts.append(f"相生：{WUXING_RELATIONS['sheng']['description']}")
            context_parts.append(f"相克：{WUXING_RELATIONS['ke']['description']}")
        
        return '\n'.join(context_parts)
    
    def build_meihua_knowledge_context(self, hexagram_data):
        """
        构建梅花易数分析的知识上下文
        为AI分析提供结构化的卦象知识背景
        """
        context_parts = []
        context_parts.append("=== 梅花易数知识库 ===")
        
        base_info = hexagram_data.get('base', {})
        base_name = base_info.get('name', '')
        if base_name:
            context_parts.append(f"\n【本卦：{base_name}】")
            context_parts.append(f"卦辞：{base_info.get('gua_ci', '')}")
            context_parts.append(f"释义：{base_info.get('description', '')}")
            
            changing_yao = base_info.get('changing_yao', 0)
            if changing_yao:
                context_parts.append(f"动爻：第{changing_yao}爻 - {base_info.get('changing_yao_name', '')}")
                context_parts.append(f"爻辞：{base_info.get('changing_yao_text', '')}")
                context_parts.append(f"释义：{base_info.get('changing_yao_meaning', '')}")
        
        bian_info = hexagram_data.get('bian', {})
        bian_name = bian_info.get('name', '')
        if bian_name:
            context_parts.append(f"\n【变卦：{bian_name}】")
            context_parts.append(f"释义：{bian_info.get('description', '')}")
        
        context_parts.append(f"\n【解卦原则】")
        for rule in MEIHUA_KNOWLEDGE['interpretation']['basic_rules']:
            context_parts.append(f"- {rule}")
        
        return '\n'.join(context_parts)
    
    def get_all_categories(self):
        """获取所有术语分类"""
        categories = set()
        for info in self.term_index.values():
            categories.add(info['category'])
        return sorted(list(categories))
