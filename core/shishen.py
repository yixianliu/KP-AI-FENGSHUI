"""
十神分析模块 - 完善十神权重计算

修复内容：
1. 增加藏干十神能量权重（基于本气/中气/余气）
2. 完善十神力量分析
3. 增加十神综合评分
"""

from core.wuxing import TIAN_GAN_WUXING, DI_ZHI_HIDDEN_GAN_DETAIL
from core.calendar_utils import TIAN_GAN
from core.database_manager import DatabaseManager


def _get_db():
    return DatabaseManager()


# 模块级变量，首次使用时加载
_SHISHEN_DETAIL = None
_SHISHEN_WUXING_MAP = None


def _lazy_init():
    global _SHISHEN_DETAIL, _SHISHEN_WUXING_MAP
    if _SHISHEN_DETAIL is None:
        db = _get_db()
        shishen_map_rows = db.get_shishen_map()
        _SHISHEN_DETAIL = {}
        for shishen_type, row in shishen_map_rows.items():
            _SHISHEN_DETAIL[shishen_type] = {
                '阳': row.get('yang_name', ''),
                '阴': row.get('yin_name', '')
            }
        _SHISHEN_WUXING_MAP = db.get_shishen_wuxing_map()


# 保留旧模块级变量名称兼容性（内容已清空，实际通过 _lazy_init() 加载）
SHISHEN_MAP = {}
SHISHEN_DETAIL = None
SHISHEN_WUXING_MAP = None


class ShiShenAnalyzer:
    """十神分析器
    
    修复内容：
    1. 增加藏干十神能量权重计算
    2. 完善十神力量分析
    3. 增加十神综合评分
    """
    
    def __init__(self):
        _lazy_init()
        self.tian_gan_map = {tg: i for i, tg in enumerate(TIAN_GAN)}
    
    def get_shishen_type(self, rizhu, other):
        """获取十神类型（生我/我生/克我/我克/同我）"""
        rizhu_idx = self.tian_gan_map[rizhu]
        other_idx = self.tian_gan_map[other]
        
        diff = (other_idx - rizhu_idx) % 10
        
        if diff == 0:
            return '同我'
        elif diff in (1, 9):
            return '我生'
        elif diff in (2, 8):
            return '克我'
        elif diff in (3, 7):
            return '我克'
        elif diff in (4, 6):
            return '生我'
        else:
            return None
    
    def get_shishen_name(self, rizhu, other):
        """获取十神名称（正印/偏印/食神/伤官/正官/七杀/正财/偏财/比肩/劫财）"""
        shishen_type = self.get_shishen_type(rizhu, other)
        if not shishen_type:
            return ''
        
        other_yang = self.tian_gan_map[other] % 2 == 0
        
        if shishen_type in ['我生', '克我']:
            is_yang = other_yang
        else:
            is_yang = not other_yang
        
        return _SHISHEN_DETAIL[shishen_type]['阳' if is_yang else '阴']
    
    def analyze(self, bazhi):
        """分析十神分布（含权重计算）
        
        修正：原算法仅统计数量，现在增加能量权重
        """
        rizhu = bazhi['rizhu']
        pillars = ['年柱', '月柱', '日柱', '时柱']
        ganzhi_list = bazhi['四柱']
        
        result = {
            'rizhu': rizhu,
            'rizhu_wuxing': TIAN_GAN_WUXING.get(rizhu, ''),
            'details': [],
            'summary': {},
            'weight_summary': {},
            'total_weights': {},
            'analysis': ''
        }
        
        shishen_weights = {
            '正印': 0.0, '偏印': 0.0,
            '食神': 0.0, '伤官': 0.0,
            '正官': 0.0, '七杀': 0.0,
            '正财': 0.0, '偏财': 0.0,
            '比肩': 0.0, '劫财': 0.0
        }
        
        for pillar, ganzhi in zip(pillars, ganzhi_list):
            gan = ganzhi[0]
            zhi = ganzhi[1]
            
            shishen_gan = self.get_shishen_name(rizhu, gan)
            if shishen_gan in shishen_weights:
                shishen_weights[shishen_gan] += 1.0
            
            zhi_shishens = []
            hidden_gans = DI_ZHI_HIDDEN_GAN_DETAIL.get(zhi, [])
            for hidden_gan, qi_type, qi_score in hidden_gans:
                shishen = self.get_shishen_name(rizhu, hidden_gan)
                if shishen in shishen_weights:
                    shishen_weights[shishen] += qi_score
                zhi_shishens.append(f"{hidden_gan}({shishen},{qi_score})")
            
            result['details'].append({
                'pillar': pillar,
                'ganzhi': ganzhi,
                'gan': gan,
                'gan_shishen': shishen_gan,
                'gan_weight': 1.0,
                'zhi': zhi,
                'zhi_shishens': zhi_shishens,
                'hidden_weights': [(hg[0], self.get_shishen_name(rizhu, hg[0]), hg[2]) 
                                  for hg in hidden_gans]
            })
        
        self._generate_summary(result, shishen_weights)
        result['analysis'] = self._generate_analysis(result)
        
        return result
    
    def _generate_summary(self, result, shishen_weights):
        """生成十神统计摘要"""
        shishen_counts = {}
        for detail in result['details']:
            shishen = detail['gan_shishen']
            shishen_counts[shishen] = shishen_counts.get(shishen, 0) + 1
        
        result['summary'] = shishen_counts
        result['weight_summary'] = {k: round(v, 2) for k, v in shishen_weights.items() if v > 0}
        
        total_weight = sum(shishen_weights.values())
        result['total_weights'] = {
            '印星': round(shishen_weights['正印'] + shishen_weights['偏印'], 2),
            '食伤': round(shishen_weights['食神'] + shishen_weights['伤官'], 2),
            '官杀': round(shishen_weights['正官'] + shishen_weights['七杀'], 2),
            '财星': round(shishen_weights['正财'] + shishen_weights['偏财'], 2),
            '比劫': round(shishen_weights['比肩'] + shishen_weights['劫财'], 2),
            'total': round(total_weight, 2)
        }
    
    def _generate_analysis(self, result):
        """生成十神分析结论"""
        parts = []
        total_weights = result['total_weights']
        total = total_weights.get('total', 0)
        
        if total > 0:
            for category, weight in [('印星', '生扶'), ('食伤', '泄秀'), 
                                     ('官杀', '克制'), ('财星', '耗身'), ('比劫', '帮身')]:
                w = total_weights[category]
                if w / total >= 0.3:
                    parts.append(f"{category}偏旺，{weight}有力")
                elif w / total <= 0.1:
                    parts.append(f"{category}偏弱，{weight}不足")
        
        if not parts:
            parts.append("十神分布均衡")
        
        return '；'.join(parts)
