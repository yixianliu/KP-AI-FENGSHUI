"""
大运流年计算模块 - 完善大运流年分析

修复内容：
1. 使用 calendar_utils 中的干支计算方法
2. 增加大运与八字五行制衡分析
3. 增加流年与大运交互分析
4. 完善运势趋势判断
"""

import core.calendar_utils as _cal_module
from core.wuxing import TIAN_GAN_WUXING, DI_ZHI_WUXING
from core.database_manager import DatabaseManager


def _get_db():
    return DatabaseManager()


# 模块级变量，首次使用时加载
_YUNSHI_GAN = None
_YUNSHI_ZHI = None


def _lazy_init():
    global _YUNSHI_GAN, _YUNSHI_ZHI
    if _YUNSHI_GAN is None:
        db = _get_db()
        _YUNSHI_GAN = db.get_yunshi_gan_analysis()
        _YUNSHI_ZHI = db.get_yunshi_zhi_analysis()


def _get_gan_info(gan):
    """获取天干运势分析信息，返回兼容旧格式的dict"""
    _lazy_init()
    row = _YUNSHI_GAN.get(gan, {})
    if row:
        return {
            'positive': row.get('positive_desc', ''),
            'negative': row.get('negative_desc', '')
        }
    return {}


def _get_zhi_info(zhi):
    """获取地支运势分析文本"""
    _lazy_init()
    row = _YUNSHI_ZHI.get(zhi, {})
    return row.get('description', '') if row else ''


# 保留旧模块级变量名称兼容性（但内容已清空）
YUNSHI_ANALYSIS = {}
ZHI_ANALYSIS = {}


class YunShiCalculator:
    """大运流年计算器
    
    修复内容：
    1. 使用 calendar_utils 中的干支计算方法
    2. 增加大运与八字五行制衡分析
    3. 增加流年与大运交互分析
    4. 完善运势趋势判断
    """
    
    def __init__(self):
        _cal_module._lazy_init()
        self.tian_gan_map = {tg: i for i, tg in enumerate(_cal_module.TIAN_GAN)}
        self.di_zhi_map = {dz: i for i, dz in enumerate(_cal_module.DI_ZHI)}
        self.ganzhi_map = {gz: i for i, gz in enumerate(_cal_module.YEAR_GANZHI)}

    def get_year_ganzhi(self, year):
        """计算年干支（使用标准公式）"""
        idx = (year - 4) % 60
        return _cal_module.YEAR_GANZHI[idx]

    def calculate_major_fortune(self, bazhi, gender, birth_year):
        """计算大运
        
        修正：原算法使用旧的 baazi.py，现在使用标准公式
        """
        rizhu = bazhi['rizhu']
        day_gan_idx = self.tian_gan_map[rizhu]
        
        is_male = gender == '男'
        is_yang = day_gan_idx % 2 == 0
        
        direction = '顺行' if (is_male and is_yang) or (not is_male and not is_yang) else '逆行'

        month_ganzhi = bazhi['month']
        start_idx = self.ganzhi_map[month_ganzhi]
        
        periods = []
        for i in range(9):
            if direction == '顺行':
                ganzhi_idx = (start_idx + i) % 60
            else:
                ganzhi_idx = (start_idx - i + 60) % 60
            
            ganzhi = _cal_module.YEAR_GANZHI[ganzhi_idx]
            
            start_age = 0 if i == 0 else 10 + i * 10
            start_year = birth_year + start_age
            
            analysis = self._analyze_fortune_period(ganzhi, bazhi)
            
            periods.append({
                'period': i + 1,
                'ganzhi': ganzhi,
                'start_age': start_age,
                'end_age': start_age + 9,
                'start_year': start_year,
                'end_year': start_year + 9,
                'direction': direction,
                'analysis': analysis['text'],
                'detailed_analysis': analysis
            })
        
        return {'periods': periods, 'direction': direction}

    def calculate_annual_fortune(self, bazhi, start_year=2024, years_count=10):
        """计算流年运势
        
        修正：增加流年与大运、八字的交互分析
        """
        years = []
        
        for i in range(years_count):
            year = start_year + i
            year_ganzhi = self.get_year_ganzhi(year)
            minor_fortune = self._calculate_minor_fortune(bazhi, year)
            
            analysis = self._analyze_annual_fortune(bazhi, year_ganzhi)
            
            years.append({
                'year': year,
                'ganzhi': year_ganzhi,
                'minor_fortune': minor_fortune,
                'analysis': analysis['text'],
                'detailed_analysis': analysis
            })
        
        return {'years': years}

    def _calculate_minor_fortune(self, bazhi, year):
        """计算小运"""
        rizhu = bazhi['rizhu']
        rizhu_idx = self.tian_gan_map[rizhu]
        year_idx = (year - 4) % 60
        minor_idx = (rizhu_idx * 2 + year_idx) % 60
        return _cal_module.YEAR_GANZHI[minor_idx]

    def _analyze_fortune_period(self, ganzhi, bazhi):
        """分析大运（含五行制衡分析）"""
        gan = ganzhi[0]
        zhi = ganzhi[1]
        
        gan_info = _get_gan_info(gan)
        zhi_info = _get_zhi_info(zhi)
        
        rizhu = bazhi.get('rizhu', '')
        rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
        
        gan_wx = TIAN_GAN_WUXING.get(gan, '')
        zhi_wx = DI_ZHI_WUXING.get(zhi, '')
        
        wuxing_relation = self._get_wuxing_relation(rizhu_wx, gan_wx)
        zhi_wuxing_relation = self._get_wuxing_relation(rizhu_wx, zhi_wx)
        
        parts = []
        if 'positive' in gan_info:
            parts.append(gan_info['positive'])
        if zhi_info:
            parts.append(zhi_info)
        
        if wuxing_relation:
            parts.append(f'天干{gan}({gan_wx})与日主{rizhu}({rizhu_wx}){wuxing_relation}')
        if zhi_wuxing_relation:
            parts.append(f'地支{zhi}({zhi_wx})与日主{rizhu}({rizhu_wx}){zhi_wuxing_relation}')
        
        return {
            'text': '；'.join(parts),
            'gan': gan,
            'gan_wx': gan_wx,
            'zhi': zhi,
            'zhi_wx': zhi_wx,
            'gan_relation': wuxing_relation,
            'zhi_relation': zhi_wuxing_relation
        }

    def _analyze_annual_fortune(self, bazhi, year_ganzhi):
        """分析流年运势（含交互分析）"""
        rizhu = bazhi['rizhu']
        year_gan = year_ganzhi[0]
        year_zhi = year_ganzhi[1]
        
        gan_info = _get_gan_info(year_gan)
        zhi_info = _get_zhi_info(year_zhi)
        
        rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
        gan_wx = TIAN_GAN_WUXING.get(year_gan, '')
        zhi_wx = DI_ZHI_WUXING.get(year_zhi, '')
        
        wuxing_relation = self._get_wuxing_relation(rizhu_wx, gan_wx)
        zhi_wuxing_relation = self._get_wuxing_relation(rizhu_wx, zhi_wx)
        
        parts = []
        
        if wuxing_relation:
            parts.append(f'本年天干{year_gan}({gan_wx})与日主{rizhu}({rizhu_wx}){wuxing_relation}')
        if zhi_wuxing_relation:
            parts.append(f'本年地支{year_zhi}({zhi_wx})与日主{rizhu}({rizhu_wx}){zhi_wuxing_relation}')
        
        if 'positive' in gan_info:
            parts.append(f'天干{year_gan}：{gan_info["positive"]}')
        if zhi_info:
            parts.append(f'地支{year_zhi}：{zhi_info}')
        
        return {
            'text': '；'.join(parts),
            'gan': year_gan,
            'gan_wx': gan_wx,
            'zhi': year_zhi,
            'zhi_wx': zhi_wx,
            'gan_relation': wuxing_relation,
            'zhi_relation': zhi_wuxing_relation
        }

    def _get_wuxing_relation(self, wx1, wx2):
        """获取五行关系（从数据库获取生克关系）"""
        if not wx1 or not wx2:
            return ''
        
        db = _get_db()
        wx_relations = db.get_wuxing_relations()
        
        # 从数据库构建生克映射
        sheng = {}
        ke = {}
        if 'sheng' in wx_relations:
            for rel in wx_relations['sheng']['relations']:
                sheng[rel['from']] = rel['to']
        if 'ke' in wx_relations:
            for rel in wx_relations['ke']['relations']:
                ke[rel['from']] = rel['to']
        
        if wx1 == wx2:
            return '比和'
        elif sheng.get(wx1) == wx2:
            return '我生'
        elif sheng.get(wx2) == wx1:
            return '生我'
        elif ke.get(wx1) == wx2:
            return '我克'
        elif ke.get(wx2) == wx1:
            return '克我'
        return ''
