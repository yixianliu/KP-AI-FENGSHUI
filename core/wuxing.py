"""
五行量化分析模块 - 完善五行能量计算体系
数据来源：MySQL数据库

修复内容：
1. 细化藏干能量分值：本气0.6、中气0.3、余气0.1（原为统一0.5）
2. 增加月令扶抑权重：根据月令调整五行能量
3. 增加通根强弱判定规则
4. 完善五行均衡分析逻辑
"""

from core.database_manager import DatabaseManager

# 懒加载数据库数据
_db = None
_TIAN_GAN_WUXING = None
_DI_ZHI_WUXING = None
_DI_ZHI_HIDDEN_GAN = None
_DI_ZHI_HIDDEN_GAN_DETAIL = None
_YUE_LING_WEIGHT = None


def _ensure_db():
    """确保数据库连接并加载数据"""
    global _db, _TIAN_GAN_WUXING, _DI_ZHI_WUXING
    global _DI_ZHI_HIDDEN_GAN, _DI_ZHI_HIDDEN_GAN_DETAIL, _YUE_LING_WEIGHT
    if _db is None:
        _db = DatabaseManager()
        _TIAN_GAN_WUXING = _db.get_tian_gan_wuxing()
        _DI_ZHI_WUXING = _db.get_di_zhi_wuxing()
        _DI_ZHI_HIDDEN_GAN_DETAIL = _db.get_di_zhi_hidden_gan()
        _DI_ZHI_HIDDEN_GAN = _db.get_di_zhi_hidden_gan_simple()
        _YUE_LING_WEIGHT = _db.get_yue_ling_weight()


def get_tian_gan_wuxing():
    """获取天干五行映射"""
    _ensure_db()
    return _TIAN_GAN_WUXING


def get_di_zhi_wuxing():
    """获取地支五行映射"""
    _ensure_db()
    return _DI_ZHI_WUXING


def get_di_zhi_hidden_gan_detail():
    """获取地支藏干详细数据"""
    _ensure_db()
    return _DI_ZHI_HIDDEN_GAN_DETAIL


def get_yue_ling_weight():
    """获取月令权重"""
    _ensure_db()
    return _YUE_LING_WEIGHT


# 兼容旧代码的模块级变量（通过属性访问延迟加载）
class _LazyDict:
    """延迟加载字典"""
    def __init__(self, loader):
        self._loader = loader
        self._data = None
    
    def _load(self):
        if self._data is None:
            self._data = self._loader()
        return self._data
    
    def __getitem__(self, key):
        return self._load().__getitem__(key)
    
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


TIAN_GAN_WUXING = _LazyDict(lambda: (_ensure_db() or _TIAN_GAN_WUXING))
DI_ZHI_WUXING = _LazyDict(lambda: (_ensure_db() or _DI_ZHI_WUXING))
DI_ZHI_HIDDEN_GAN = _LazyDict(lambda: (_ensure_db() or _DI_ZHI_HIDDEN_GAN))
DI_ZHI_HIDDEN_GAN_DETAIL = _LazyDict(lambda: (_ensure_db() or _DI_ZHI_HIDDEN_GAN_DETAIL))
YUE_LING_WEIGHT = _LazyDict(lambda: (_ensure_db() or _YUE_LING_WEIGHT))


class WuXingAnalyzer:
    """五行分析器
    
    修复内容：
    1. 藏干能量细化：本气0.6、中气0.3、余气0.1
    2. 增加月令扶抑权重
    3. 增加通根强弱判定
    4. 完善五行均衡分析
    """
    
    def __init__(self):
        _ensure_db()
        self.wuxing = ['木', '火', '土', '金', '水']
    
    def analyze(self, bazhi, month_zhi=None):
        """分析五行能量（含月令权重、藏干细化）
        
        修正：原算法藏干统一0.5分值，现在区分本气/中气/余气
        修正：原算法无月令权重，现在根据月令调整能量
        """
        ganzhi_list = bazhi['四柱']
        
        result = {wx: {'count': 0.0, 'score': 0.0, 'elements': [], 'sources': []} 
                 for wx in self.wuxing}
        
        lunar_month_zhi = month_zhi if month_zhi else bazhi.get('month_zhi', '')
        yue_ling_weight = _YUE_LING_WEIGHT.get(lunar_month_zhi, {})
        
        for pillar_name, ganzhi in zip(['年柱', '月柱', '日柱', '时柱'], ganzhi_list):
            if not ganzhi:
                continue
                
            gan = ganzhi[0]
            zhi = ganzhi[1]
            
            wx_gan = _TIAN_GAN_WUXING[gan]
            base_score = 1.0
            if lunar_month_zhi and wx_gan in yue_ling_weight:
                base_score *= yue_ling_weight[wx_gan]
            
            result[wx_gan]['count'] += 1
            result[wx_gan]['score'] += base_score
            result[wx_gan]['elements'].append(gan)
            result[wx_gan]['sources'].append(f'{pillar_name}天干{gan}')
            
            wx_zhi = _DI_ZHI_WUXING[zhi]
            base_score = 1.0
            if lunar_month_zhi and wx_zhi in yue_ling_weight:
                base_score *= yue_ling_weight[wx_zhi]
            
            result[wx_zhi]['count'] += 1
            result[wx_zhi]['score'] += base_score
            result[wx_zhi]['elements'].append(zhi)
            result[wx_zhi]['sources'].append(f'{pillar_name}地支{zhi}')
            
            hidden_gans = _DI_ZHI_HIDDEN_GAN_DETAIL.get(zhi, [])
            for hidden_gan, qi_type, qi_score in hidden_gans:
                wx_hidden = _TIAN_GAN_WUXING[hidden_gan]
                base_score = qi_score
                if lunar_month_zhi and wx_hidden in yue_ling_weight:
                    base_score *= yue_ling_weight[wx_hidden]
                
                result[wx_hidden]['count'] += qi_score
                result[wx_hidden]['score'] += base_score
                result[wx_hidden]['elements'].append(f'{zhi}藏{hidden_gan}')
                result[wx_hidden]['sources'].append(f'{pillar_name}{zhi}藏{hidden_gan}({qi_type})')
        
        total_score = sum(result[wx]['score'] for wx in self.wuxing)
        total_count = sum(result[wx]['count'] for wx in self.wuxing)
        
        rizhu = bazhi.get('rizhu', '')
        rizhu_wx = _TIAN_GAN_WUXING.get(rizhu, '')
        
        tonggen_info = self._analyze_tonggen(bazhi, rizhu)
        
        for wx in self.wuxing:
            result[wx]['percentage'] = round(
                result[wx]['score'] / total_score * 100 if total_score > 0 else 0, 1
            )
            result[wx]['count_percentage'] = round(
                result[wx]['count'] / total_count * 100 if total_count > 0 else 0, 1
            )
            result[wx]['is_rizhu'] = wx == rizhu_wx
        
        result['summary'] = self.get_summary(result, rizhu_wx)
        result['tonggen'] = tonggen_info
        result['yue_ling'] = lunar_month_zhi
        result['total_score'] = round(total_score, 2)
        result['total_count'] = round(total_count, 2)
        result['rizhu_wx'] = rizhu_wx
        
        return result
    
    def _analyze_tonggen(self, bazhi, rizhu):
        """分析日主通根情况（新增）"""
        rizhu_wx = _TIAN_GAN_WUXING.get(rizhu, '')
        
        tonggen_list = []
        strong_count = 0
        weak_count = 0
        
        for pillar_name, ganzhi in zip(['年柱', '月柱', '日柱', '时柱'], bazhi['四柱']):
            if not ganzhi:
                continue
                
            zhi = ganzhi[1]
            zhi_wx = _DI_ZHI_WUXING.get(zhi)
            
            if zhi_wx == rizhu_wx:
                hidden_gans = _DI_ZHI_HIDDEN_GAN_DETAIL.get(zhi, [])
                has_rizhu_in_hidden = any(hg[0] == rizhu for hg in hidden_gans)
                
                if has_rizhu_in_hidden:
                    tonggen_list.append({
                        'pillar': pillar_name,
                        'zhi': zhi,
                        'strength': '强根',
                        'reason': f'{zhi}中藏{rizhu}为本气'
                    })
                    strong_count += 1
                else:
                    tonggen_list.append({
                        'pillar': pillar_name,
                        'zhi': zhi,
                        'strength': '中气',
                        'reason': f'{zhi}五行与日主相同'
                    })
                    weak_count += 1
        
        total_tonggen = len(tonggen_list)
        
        return {
            'rizhu': rizhu,
            'rizhu_wx': rizhu_wx,
            'total': total_tonggen,
            'strong': strong_count,
            'weak': weak_count,
            'details': tonggen_list,
            'description': self._get_tonggen_description(total_tonggen, strong_count)
        }
    
    def _get_tonggen_description(self, total, strong):
        """生成通根描述"""
        if total == 0:
            return '日主无通根，身弱之象'
        elif total >= 3:
            return f'日主通根{total}处，{strong}处强根，身强无疑'
        elif total == 2:
            if strong >= 1:
                return f'日主通根{total}处，{strong}处强根，身较强'
            else:
                return f'日主通根{total}处，无强根，身偏弱'
        else:
            if strong >= 1:
                return f'日主通根{total}处强根，身偏强'
            else:
                return f'日主通根{total}处，根气不足，身偏弱'
    
    def get_summary(self, data, rizhu_wx):
        """生成五行分析摘要（完善版）"""
        sorted_wx = sorted(self.wuxing, key=lambda x: data[x]['score'], reverse=True)
        
        max_wx = sorted_wx[0]
        min_wx = sorted_wx[-1]
        
        max_score = data[max_wx]['score']
        min_score = data[min_wx]['score']
        total_score = data.get('total_score', 0)
        
        summary = []
        
        if total_score > 0:
            max_ratio = max_score / total_score
            min_ratio = min_score / total_score
            
            if max_ratio >= 0.4:
                summary.append(f"{max_wx}旺极")
            elif max_ratio >= 0.3:
                summary.append(f"{max_wx}偏旺")
            
            if min_ratio <= 0.08:
                summary.append(f"{min_wx}极弱")
            elif min_ratio <= 0.15:
                summary.append(f"{min_wx}偏弱")
            
            if rizhu_wx and data[rizhu_wx]['score'] >= total_score * 0.25:
                summary.append("日主偏强")
            elif rizhu_wx and data[rizhu_wx]['score'] <= total_score * 0.12:
                summary.append("日主偏弱")
        
        if not summary:
            summary.append("五行均衡")
        
        return '，'.join(summary)
    
    def analyze_wangshuai(self, bazhi, month_zhi=None):
        """判断日主旺衰（新增完整方法）"""
        wuxing_result = self.analyze(bazhi, month_zhi)
        
        rizhu_wx = wuxing_result.get('rizhu_wx', '')
        rizhu_score = wuxing_result.get(rizhu_wx, {}).get('score', 0)
        total_score = wuxing_result.get('total_score', 0)
        
        tonggen = wuxing_result.get('tonggen', {})
        tonggen_total = tonggen.get('total', 0)
        tonggen_strong = tonggen.get('strong', 0)
        
        rizhu_ratio = rizhu_score / total_score if total_score > 0 else 0
        
        wangshuai_level = ''
        description = ''
        
        if rizhu_ratio >= 0.3 or (tonggen_total >= 2 and tonggen_strong >= 1):
            wangshuai_level = '身强'
            description = f'日主{rizhu_wx}得令或得地，五行分值占比{rizhu_ratio:.1%}，通根{tonggen_total}处'
        elif rizhu_ratio <= 0.12 or tonggen_total == 0:
            wangshuai_level = '身弱'
            description = f'日主{rizhu_wx}不得令不得地，五行分值占比{rizhu_ratio:.1%}，通根{tonggen_total}处'
        else:
            wangshuai_level = '中和'
            description = f'日主{rizhu_wx}五行中和，分值占比{rizhu_ratio:.1%}'
        
        return {
            'level': wangshuai_level,
            'description': description,
            'rizhu_score': round(rizhu_score, 2),
            'total_score': total_score,
            'rizhu_ratio': round(rizhu_ratio, 3),
            'tonggen': tonggen
        }
