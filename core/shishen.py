from core.baazi import TIAN_GAN

SHISHEN_MAP = {
    '生我': '印星',
    '我生': '食伤',
    '克我': '官杀',
    '我克': '财星',
    '同我': '比劫'
}

SHISHEN_DETAIL = {
    '生我': {'阳': '偏印', '阴': '正印'},
    '我生': {'阳': '伤官', '阴': '食神'},
    '克我': {'阳': '七杀', '阴': '正官'},
    '我克': {'阳': '偏财', '阴': '正财'},
    '同我': {'阳': '比肩', '阴': '劫财'}
}

class ShiShenAnalyzer:
    def __init__(self):
        self.tian_gan_map = {tg: i for i, tg in enumerate(TIAN_GAN)}
    
    def get_shishen_type(self, rizhu, other):
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
        shishen_type = self.get_shishen_type(rizhu, other)
        if not shishen_type:
            return ''
        
        rizhu_yang = self.tian_gan_map[rizhu] % 2 == 0
        other_yang = self.tian_gan_map[other] % 2 == 0
        
        if shishen_type in ['我生', '克我']:
            is_yang = other_yang
        else:
            is_yang = not other_yang
        
        return SHISHEN_DETAIL[shishen_type]['阳' if is_yang else '阴']
    
    def analyze(self, bazhi):
        rizhu = bazhi['rizhu']
        pillars = ['年柱', '月柱', '日柱', '时柱']
        ganzhi_list = bazhi['四柱']
        
        result = {
            'rizhu': rizhu,
            'rizhu_wuxing': self.get_wuxing(rizhu),
            'details': [],
            'summary': {}
        }
        
        for pillar, ganzhi in zip(pillars, ganzhi_list):
            gan = ganzhi[0]
            zhi = ganzhi[1]
            
            shishen_gan = self.get_shishen_name(rizhu, gan)
            
            zhi_shishens = []
            for hidden_gan in ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']:
                if self.has_hidden_gan(zhi, hidden_gan):
                    shishen = self.get_shishen_name(rizhu, hidden_gan)
                    zhi_shishens.append(f"{hidden_gan}({shishen})")
            
            result['details'].append({
                'pillar': pillar,
                'ganzhi': ganzhi,
                'gan': gan,
                'gan_shishen': shishen_gan,
                'zhi': zhi,
                'zhi_shishens': zhi_shishens
            })
        
        self._generate_summary(result)
        return result
    
    def get_wuxing(self, tian_gan):
        idx = self.tian_gan_map[tian_gan]
        if idx < 2:
            return '木'
        elif idx < 4:
            return '火'
        elif idx < 6:
            return '土'
        elif idx < 8:
            return '金'
        else:
            return '水'
    
    def has_hidden_gan(self, zhi, gan):
        hidden_map = {
            '子': ['癸'],
            '丑': ['己', '辛', '癸'],
            '寅': ['甲', '丙', '戊'],
            '卯': ['乙'],
            '辰': ['戊', '乙', '癸'],
            '巳': ['丙', '戊', '庚'],
            '午': ['丁', '己'],
            '未': ['己', '丁', '乙'],
            '申': ['庚', '壬', '戊'],
            '酉': ['辛'],
            '戌': ['戊', '辛', '丁'],
            '亥': ['壬', '甲']
        }
        return gan in hidden_map.get(zhi, [])
    
    def _generate_summary(self, result):
        shishen_counts = {}
        for detail in result['details']:
            shishen = detail['gan_shishen']
            shishen_counts[shishen] = shishen_counts.get(shishen, 0) + 1
        
        result['summary'] = shishen_counts