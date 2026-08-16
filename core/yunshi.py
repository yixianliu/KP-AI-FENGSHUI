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
    """返回 DatabaseManager 实例，供本模块加载大运/流年天干地支运势分析数据。"""
    return DatabaseManager()


# 模块级变量，首次使用时加载
_YUNSHI_GAN = None
_YUNSHI_ZHI = None


def _lazy_init():
    """首次调用时从数据库加载天干/地支运势分析表；之后幂等。"""
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
        """初始化时确保历法常量已加载，并构建天干/地支/干支名→序号索引。"""
        _cal_module._lazy_init()
        self.tian_gan_map = {tg: i for i, tg in enumerate(_cal_module.TIAN_GAN)}
        self.di_zhi_map = {dz: i for i, dz in enumerate(_cal_module.DI_ZHI)}
        self.ganzhi_map = {gz: i for i, gz in enumerate(_cal_module.YEAR_GANZHI)}

    def get_year_ganzhi(self, year):
        """计算年干支（使用标准公式）"""
        idx = (year - 4) % 60
        return _cal_module.YEAR_GANZHI[idx]

    def calculate_major_fortune(self, bazhi, gender, birth_year, birth_dt=None):
        """计算大运

        修正内容：
        1. 起运岁数 = 出生时刻到最近「节」的天数 ÷ 3（传统「三天为一岁」）。
           顺行（阳男阴女）顺数到出生后的第一个「节」；
           逆行（阴男阳女）逆数到出生前的最后一个「节」。
           原代码把起运年龄硬编码为 0/10/20/…，完全忽略了真实起运岁数，
           导致每一步大运都提前开始，此版本予以修正。
        2. 大运干支顺/逆排，第一步大运为月柱的相邻干支（月柱 ± 1），
           而非月柱本身。
        """
        rizhu = bazhi['rizhu']
        day_gan_idx = self.tian_gan_map[rizhu]

        is_male = gender == '男'
        is_yang = day_gan_idx % 2 == 0

        direction = '顺行' if (is_male and is_yang) or (not is_male and not is_yang) else '逆行'

        month_ganzhi = bazhi['month']
        start_idx = self.ganzhi_map[month_ganzhi]

        # —— 起运岁数 ——
        qiyun_days = self._calculate_qiyun_days(birth_dt, direction) if birth_dt else None
        if qiyun_days is not None:
            qiyun_age = abs(qiyun_days) / 3.0
        else:
            # 无出生精确时刻时退化为旧逻辑（从 0 岁起，仅保底）
            qiyun_age = 0.0

        periods = []
        for i in range(9):
            # 第一步大运 = 月柱相邻干支（顺行 +1 / 逆行 -1）
            if direction == '顺行':
                ganzhi_idx = (start_idx + i + 1) % 60
            else:
                ganzhi_idx = (start_idx - i - 1 + 60) % 60

            ganzhi = _cal_module.YEAR_GANZHI[ganzhi_idx]

            start_age = qiyun_age + i * 10
            if birth_dt is not None:
                # 以真实出生时刻推算交运公历年份：起运岁数 = qiyun_age 年
                from datetime import timedelta
                start_dt = birth_dt + timedelta(days=(qiyun_age + i * 10) * 365.2422)
                start_year = start_dt.year
            else:
                start_year = int(birth_year + start_age)

            analysis = self._analyze_fortune_period(ganzhi, bazhi)

            periods.append({
                'period': i + 1,
                'ganzhi': ganzhi,
                'start_age': int(start_age),
                'end_age': int(start_age + 9),
                'start_year': start_year,
                'end_year': start_year + 9,
                'direction': direction,
                'analysis': analysis['text'],
                'detailed_analysis': analysis
            })

        qiyun_text = self._format_qiyun(qiyun_days) if qiyun_days is not None else ''
        return {
            'periods': periods,
            'direction': direction,
            'qiyun_days': round(qiyun_days, 2) if qiyun_days is not None else None,
            'qiyun_age': round(qiyun_age, 2),
            'qiyun_text': qiyun_text,
        }

    @staticmethod
    def _jie_indices():
        """返回十二「节」的节气索引（偶数位：立春0、惊蛰2、…、小寒22）"""
        return list(range(0, 24, 2))

    def _calculate_qiyun_days(self, birth_dt, direction):
        """计算起运天数：出生时刻到最近「节」的天数（浮点，单位：天）"""
        jieqi = _cal_module.JieQiCalculator()
        candidates = []
        for year in (birth_dt.year - 1, birth_dt.year, birth_dt.year + 1):
            for idx in self._jie_indices():
                jt = jieqi.calculate_jieqi(year, idx)
                if jt:
                    candidates.append(jt)
        candidates.sort()
        if not candidates:
            return None

        if direction == '顺行':
            target = None
            for jt in candidates:
                if jt > birth_dt:
                    target = jt
                    break
            if target is None:
                return None
            days = (target - birth_dt).total_seconds() / 86400.0
        else:  # 逆行
            target = None
            for jt in reversed(candidates):
                if jt < birth_dt:
                    target = jt
                    break
            if target is None:
                return None
            days = (birth_dt - target).total_seconds() / 86400.0

        # 三天为一岁；传统上「进位」取整，但此处保留小数以便精确推算交运年
        return days

    @staticmethod
    def _format_qiyun(qiyun_days):
        """将起运天数格式化为「X岁Y个月」"""
        if qiyun_days is None:
            return ''
        days = abs(qiyun_days)
        years = int(days // 3)
        rem_days = days - years * 3
        months = int(rem_days * 4)  # 1天 = 4个月
        parts = []
        if years:
            parts.append(f'{years}岁')
        if months:
            parts.append(f'{months}个月')
        return '起运：' + (''.join(parts) if parts else '0岁')

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
