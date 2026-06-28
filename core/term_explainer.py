"""
专业术语解释系统
提供命理术语的查询、分类浏览、关联推荐等功能
数据来源：MySQL数据库
"""
import json
from core.database_manager import DatabaseManager
from core.knowledge_base import KnowledgeBase


def _get_db():
    return DatabaseManager()


def _load_all_terms_from_db():
    """从数据库加载所有术语"""
    db = _get_db()
    result = {}
    
    # 神煞术语
    for name, info in db.get_shensha_terms().items():
        result[name] = {
            'category': info.get('category', ''),
            'type': info.get('term_type', ''),
            'brief': info.get('brief', ''),
            'description': info.get('description', ''),
            'check_method': info.get('check_method', ''),
            'influence': json.loads(info['influence']) if isinstance(info.get('influence'), str) else info.get('influence', []),
            'related_terms': json.loads(info['related_terms']) if isinstance(info.get('related_terms'), str) else info.get('related_terms', [])
        }
    
    # 干支关系术语
    for name, info in db.get_ganzhi_relation_terms().items():
        result[name] = {
            'category': info.get('category', ''),
            'type': info.get('term_type', ''),
            'brief': info.get('brief', ''),
            'description': info.get('description', ''),
            'details': json.loads(info['details']) if isinstance(info.get('details'), str) else info.get('details', []),
            'influence': json.loads(info['influence']) if isinstance(info.get('influence'), str) else info.get('influence', []),
            'related_terms': json.loads(info['related_terms']) if isinstance(info.get('related_terms'), str) else info.get('related_terms', [])
        }
    
    # 命理基础术语
    for name, info in db.get_foundation_terms().items():
        result[name] = {
            'category': info.get('category', ''),
            'type': info.get('term_type', ''),
            'brief': info.get('brief', ''),
            'description': info.get('description', ''),
            'details': json.loads(info['details']) if isinstance(info.get('details'), str) else info.get('details', []),
            'influence': json.loads(info['influence']) if isinstance(info.get('influence'), str) else info.get('influence', []),
            'related_terms': json.loads(info['related_terms']) if isinstance(info.get('related_terms'), str) else info.get('related_terms', [])
        }
    
    # 梅花易数术语
    for name, info in db.get_meihua_terms().items():
        result[name] = {
            'category': info.get('category', ''),
            'type': info.get('term_type', ''),
            'brief': info.get('brief', ''),
            'description': info.get('description', ''),
            'details': json.loads(info['details']) if isinstance(info.get('details'), str) else info.get('details', []),
            'influence': json.loads(info['influence']) if isinstance(info.get('influence'), str) else info.get('influence', []),
            'related_terms': json.loads(info['related_terms']) if isinstance(info.get('related_terms'), str) else info.get('related_terms', [])
        }
    
    return result


class _LazyAllTerms:
    def __init__(self):
        self._data = None
    
    def _load(self):
        if self._data is None:
            self._data = _load_all_terms_from_db()
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
    
    def update(self, *args, **kwargs):
        return self._load().update(*args, **kwargs)


# 兼容旧代码
SHENSHA_TERMS = {}
GANZHI_RELATION_TERMS = {}
FOUNDATION_TERMS = {}
MEIHUA_TERMS = {}

ALL_TERMS = _LazyAllTerms()


def _get_default_categories():
    """从数据库动态生成术语分类，降级使用默认值"""
    db = _get_db()
    categories = [{'key': 'all', 'name': '全部术语', 'description': '所有专业术语'}]
    
    # 从数据库术语表收集分类
    all_terms_data = _load_all_terms_from_db()
    seen_categories = set()
    for term_name, info in all_terms_data.items():
        cat = info.get('category', '')
        if cat and cat not in seen_categories:
            seen_categories.add(cat)
            categories.append({
                'key': cat,
                'name': cat,
                'description': f'{cat}相关术语'
            })
    
    # 也加入知识库中的分类
    db_kb = KnowledgeBase()
    for cat_name in db_kb.get_all_categories():
        if cat_name not in seen_categories:
            seen_categories.add(cat_name)
            categories.append({
                'key': cat_name,
                'name': cat_name,
                'description': f'{cat_name}相关知识'
            })
    
    return categories


class TermExplainer:
    """
    专业术语解释器
    提供术语查询、分类浏览、关联推荐等功能
    """

    def __init__(self):
        self.kb = KnowledgeBase()
        self.terms = ALL_TERMS
        self.categories = _get_default_categories()
        self._build_search_index()

    def _build_search_index(self):
        """构建搜索索引，包含知识库术语"""
        self.search_index = {}
        
        # 加入扩展术语
        for term_name, info in self.terms.items():
            self.search_index[term_name] = {
                'name': term_name,
                'category': info.get('category', ''),
                'brief': info.get('brief', ''),
                'description': info.get('description', ''),
                'source': 'extended',
                'details': info
            }
        
        # 加入知识库术语
        kb_terms = self.kb.term_index
        for term_name, info in kb_terms.items():
            if term_name not in self.search_index:
                self.search_index[term_name] = {
                    'name': term_name,
                    'category': info.get('category', ''),
                    'brief': info.get('description', ''),
                    'description': info.get('description', ''),
                    'source': 'knowledge_base',
                    'details': info.get('details', {})
                }

    def search(self, keyword, category=None, limit=20):
        """
        搜索术语，支持模糊匹配
        
        Args:
            keyword: 搜索关键词
            category: 分类筛选（可选）
            limit: 返回结果数量限制
            
        Returns:
            匹配的术语列表
        """
        results = []
        keyword = keyword.strip()
        
        if not keyword:
            return results
        
        # 精确匹配优先
        if keyword in self.search_index:
            term = self.search_index[keyword]
            if not category or term['category'] == category:
                results.append(term)
        
        # 名称包含匹配
        for term_name, info in self.search_index.items():
            if term_name == keyword:
                continue
            if category and info['category'] != category:
                continue
            if keyword in term_name:
                results.append(info)
                if len(results) >= limit:
                    break
        
        # 描述包含匹配
        if len(results) < limit:
            for term_name, info in self.search_index.items():
                if category and info['category'] != category:
                    continue
                if keyword in info.get('brief', '') or keyword in info.get('description', ''):
                    if info not in results:
                        results.append(info)
                        if len(results) >= limit:
                            break
        
        return results[:limit]

    def get_term_detail(self, term_name):
        """
        获取术语详细信息
        
        Args:
            term_name: 术语名称
            
        Returns:
            术语详细信息字典
        """
        if term_name in self.search_index:
            term = self.search_index[term_name].copy()
            # 添加关联术语详情
            related = term.get('details', {}).get('related_terms', [])
            if related:
                related_details = []
                for rt in related:
                    if rt in self.search_index:
                        related_details.append({
                            'name': rt,
                            'category': self.search_index[rt]['category'],
                            'brief': self.search_index[rt]['brief']
                        })
                term['related_details'] = related_details
            return term
        return None

    def get_terms_by_category(self, category_key, limit=50):
        """
        按分类获取术语列表
        
        Args:
            category_key: 分类键名
            limit: 返回数量限制
            
        Returns:
            该分类下的术语列表
        """
        results = []
        
        if category_key == 'all':
            for term_name, info in self.search_index.items():
                results.append({
                    'name': term_name,
                    'category': info['category'],
                    'brief': info['brief']
                })
                if len(results) >= limit:
                    break
        else:
            for term_name, info in self.search_index.items():
                if info['category'] == category_key:
                    results.append({
                        'name': term_name,
                        'category': info['category'],
                        'brief': info['brief']
                    })
                    if len(results) >= limit:
                        break
        
        return results

    def get_all_categories(self):
        """获取所有术语分类"""
        return self.categories

    def get_hot_terms(self, limit=10):
        """
        获取热门/常用术语
        从数据库和知识库中动态获取核心术语
        
        Args:
            limit: 返回数量限制
            
        Returns:
            热门术语列表
        """
        # 从知识库获取核心概念作为热门术语
        hot_categories = ['五行', '十神', '天干', '地支', '十二长生', '八卦']
        results = []
        seen = set()
        
        for cat in hot_categories:
            kb_terms = self.kb.get_category_terms(cat)
            for term in kb_terms:
                name = term.get('name', '')
                if name and name not in seen:
                    seen.add(name)
                    results.append({
                        'name': name,
                        'category': term.get('category', cat),
                        'brief': term.get('description', '')
                    })
                    if len(results) >= limit:
                        return results
        
        # 补充扩展术语
        for term_name, info in self.search_index.items():
            if term_name not in seen:
                results.append({
                    'name': term_name,
                    'category': info.get('category', ''),
                    'brief': info.get('brief', '')
                })
                if len(results) >= limit:
                    break
        
        return results

    def get_related_terms(self, term_name, limit=5):
        """
        获取相关术语
        
        Args:
            term_name: 术语名称
            limit: 返回数量限制
            
        Returns:
            相关术语列表
        """
        term = self.get_term_detail(term_name)
        if not term:
            return []
        
        related = term.get('details', {}).get('related_terms', [])
        results = []
        
        for rt in related:
            if rt in self.search_index:
                results.append({
                    'name': rt,
                    'category': self.search_index[rt]['category'],
                    'brief': self.search_index[rt]['brief']
                })
                if len(results) >= limit:
                    break
        
        return results

    def get_term_count(self):
        """获取术语总数统计"""
        category_counts = {}
        for info in self.search_index.values():
            cat = info['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return {
            'total': len(self.search_index),
            'by_category': category_counts
        }
