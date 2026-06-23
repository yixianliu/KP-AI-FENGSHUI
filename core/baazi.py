from core.calendar_utils import BaZiCalendar
from datetime import datetime

TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

YEAR_GANZHI = [
    '甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉',
    '甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未',
    '甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳',
    '甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯',
    '甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑',
    '甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥'
]

MONTH_GAN = [
    ('甲己', ['丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁']),
    ('乙庚', ['戊', '己', '庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己']),
    ('丙辛', ['庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛']),
    ('丁壬', ['壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']),
    ('戊癸', ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '甲', '乙'])
]

SHIER_SHEN = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养']

SHIER_SHEN_DETAIL = {
    '长生': {'description': '万物初生，生机勃勃，主开端、潜力、发展', 'influence': '生命力旺盛，有发展潜力，适合开创事业'},
    '沐浴': {'description': '万物始生，形体柔脆，主接受、修养、调整', 'influence': '需要静心修养，不宜急进，适合学习提升'},
    '冠带': {'description': '万物渐荣，初具形态，主成长、准备、修饰', 'influence': '能力逐渐显现，适合展现才华，准备承担重任'},
    '临官': {'description': '万物长成，开始发挥作用，主事业、权力、地位', 'influence': '事业发展期，适合追求功名，提升地位'},
    '帝旺': {'description': '万物成熟，达到鼎盛，主成功、辉煌、巅峰', 'influence': '运势强盛，适合把握机会，追求最大成就'},
    '衰': {'description': '万物开始衰退，主渐退、保守、调整', 'influence': '运势转弱，不宜冒进，适合巩固成果'},
    '病': {'description': '万物病弱，主疾病、困扰、阻碍', 'influence': '需要注意健康，谨慎行事，避免风险'},
    '死': {'description': '万物死亡，主结束、终止、衰败', 'influence': '运势低落，适合总结反思，准备新的开始'},
    '墓': {'description': '万物收藏，主储存、积聚、隐藏', 'influence': '适合积累资源，隐藏锋芒，等待时机'},
    '绝': {'description': '万物灭绝，主断绝、消亡、重生', 'influence': '旧事物终结，新事物开始，适合彻底改变'},
    '胎': {'description': '万物孕育，主孕育、萌芽、准备', 'influence': '新的机会正在孕育，适合耐心等待，做好准备'},
    '养': {'description': '万物养形，主滋养、成长、培养', 'influence': '适合培养能力，积累经验，为未来发展打基础'}
}

TIAN_GAN_SHIER_SHEN_MAP = {
    '甲': ['亥', '子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌'],
    '乙': ['午', '巳', '辰', '卯', '寅', '丑', '子', '亥', '戌', '酉', '申', '未'],
    '丙': ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑'],
    '丁': ['酉', '申', '未', '午', '巳', '辰', '卯', '寅', '丑', '子', '亥', '戌'],
    '戊': ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑'],
    '己': ['酉', '申', '未', '午', '巳', '辰', '卯', '寅', '丑', '子', '亥', '戌'],
    '庚': ['巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑', '寅', '卯', '辰'],
    '辛': ['子', '亥', '戌', '酉', '申', '未', '午', '巳', '辰', '卯', '寅', '丑'],
    '壬': ['申', '酉', '戌', '亥', '子', '丑', '寅', '卯', '辰', '巳', '午', '未'],
    '癸': ['卯', '寅', '丑', '子', '亥', '戌', '酉', '申', '未', '午', '巳', '辰']
}

SHIER_SHEN_LOOKUP = {}
for gan, zhi_list in TIAN_GAN_SHIER_SHEN_MAP.items():
    SHIER_SHEN_LOOKUP[gan] = {}
    for idx, zhi in enumerate(zhi_list):
        shen_name = SHIER_SHEN[idx]
        detail = SHIER_SHEN_DETAIL.get(shen_name, {})
        SHIER_SHEN_LOOKUP[gan][zhi] = {
            'name': shen_name,
            'description': detail.get('description', ''),
            'influence': detail.get('influence', '')
        }

FIRST_DAY_GANZHI = '甲子'
BASE_YEAR = 1900


class BaZiCalculator:
    """八字排盘计算器
    
    修复内容：
    1. 年柱：按立春分界（使用BaZiCalendar）
    2. 月柱：按节气划分月建（使用BaZiCalendar）
    3. 日柱：基于公历日期计算（优化算法）
    4. 时柱：基于真太阳时，支持早晚子时（使用BaZiCalendar）
    5. 新增真太阳时修正、节气精准计算、晚子时处理
    """
    
    def __init__(self):
        self.tian_gan_map = {tg: i for i, tg in enumerate(TIAN_GAN)}
        self.di_zhi_map = {dz: i for i, dz in enumerate(DI_ZHI)}
        self.ganzhi_map = {gz: i for i, gz in enumerate(YEAR_GANZHI)}
        self.calendar = BaZiCalendar()

    def get_year_ganzhi(self, year):
        """计算年干支（按立春分界）
        
        修正：原算法直接用公历年，现在通过BaZiCalendar按立春计算
        """
        return self.calendar.ganzhi.get_year_ganzhi(year)

    def get_month_ganzhi(self, year_gan, month):
        """计算月干支（五虎遁）
        
        注意：此方法为兼容旧接口保留，实际排盘应使用calculate()方法
        因为月柱必须按节气划分，不能仅用公历月份
        """
        month_idx = month - 1
        for key, gan_list in MONTH_GAN:
            if year_gan in key:
                month_gan = gan_list[month_idx]
                month_zhi = DI_ZHI[month_idx]
                return month_gan + month_zhi
        return ''

    def get_day_ganzhi(self, year, month, day):
        """计算日干支（基于基准日推算）"""
        from datetime import date
        base_date = date(BASE_YEAR, 1, 1)
        target_date = date(year, month, day)
        delta = target_date - base_date
        idx = (self.ganzhi_map[FIRST_DAY_GANZHI] + delta.days) % 60
        return YEAR_GANZHI[idx]

    def is_leap_year(self, year):
        if year % 400 == 0:
            return True
        if year % 100 == 0:
            return False
        if year % 4 == 0:
            return True
        return False

    def get_hour_ganzhi(self, day_gan, hour):
        """计算时干支（五鼠遁）
        
        注意：此方法为兼容旧接口保留，实际排盘应使用calculate()方法
        因为时柱必须基于真太阳时计算
        """
        hour_zhi_idx = self.get_hour_zhi_idx(hour)
        hour_zhi = DI_ZHI[hour_zhi_idx]
        hour_gan_idx = (self.tian_gan_map[day_gan] * 2 + hour_zhi_idx) % 10
        hour_gan = TIAN_GAN[hour_gan_idx]
        return hour_gan + hour_zhi

    def get_hour_zhi_idx(self, hour):
        if hour >= 23 or hour < 1:
            return 0
        elif hour < 3:
            return 1
        elif hour < 5:
            return 2
        elif hour < 7:
            return 3
        elif hour < 9:
            return 4
        elif hour < 11:
            return 5
        elif hour < 13:
            return 6
        elif hour < 15:
            return 7
        elif hour < 17:
            return 8
        elif hour < 19:
            return 9
        elif hour < 21:
            return 10
        else:
            return 11

    def calculate(self, year, month, day, hour, minute=0, longitude=120.0, is_lunar=False):
        """完整计算八字四柱（使用BaZiCalendar修复算法）
        
        修正内容：
        1. 使用真太阳时修正（经度+均时差）
        2. 年柱按立春分界
        3. 月柱按节气划分月建
        4. 支持晚子时（23:00-00:00按次日排盘）
        5. 增加经度参数支持不同时区
        
        Args:
            year: 公历年
            month: 公历月
            day: 公历日
            hour: 小时
            minute: 分钟（新增）
            longitude: 经度（新增，默认120°E）
            is_lunar: 是否为农历（保留兼容）
        
        Returns:
            八字排盘结果字典
        """
        if is_lunar:
            try:
                from lunarcalendar import Converter, Lunar
                lunar = Lunar(year, month, day)
                solar = Converter.Lunar2Solar(lunar)
                year, month, day = solar.year, solar.month, solar.day
            except ImportError:
                pass

        bazi_result = self.calendar.calculate_bazi(year, month, day, hour, minute, longitude)
        
        return {
            'solar_date': f"{year}-{month}-{day}",
            'lunar_date': self._get_lunar_date(year, month, day),
            'year': bazi_result['year'],
            'month': bazi_result['month'],
            'day': bazi_result['day'],
            'hour': bazi_result['hour'],
            'rizhu': bazi_result['rizhu'],
            '四柱': bazi_result['四柱'],
            'lunar_year': bazi_result['lunar_year'],
            'month_zhi': bazi_result['month_zhi'],
            'hour_zhi': bazi_result['hour_zhi'],
            'solar_time': bazi_result['solar_time'],
            'original_time': bazi_result['original_time'],
            'longitude': bazi_result['longitude']
        }

    def _get_lunar_date(self, year, month, day):
        """获取农历日期（兼容旧接口）"""
        try:
            from lunarcalendar import Converter, Solar
            solar = Solar(year, month, day)
            lunar = Converter.Solar2Lunar(solar)
            return f"{lunar.year}年{lunar.month}月{lunar.day}日"
        except ImportError:
            return f"{year}年{month}月{day}日"

    def get_shier_shen(self, rizhu, ganzhi):
        """获取十二长生信息"""
        zhi = ganzhi[1]
        return SHIER_SHEN_LOOKUP.get(rizhu, {}).get(zhi)

    def analyze_shier_shen(self, bazhi):
        """分析八字十二长生"""
        rizhu = bazhi['rizhu']
        pillars = ['年柱', '月柱', '日柱', '时柱']
        ganzhi_list = bazhi['四柱']
        
        result = []
        for i, ganzhi in enumerate(ganzhi_list):
            shen_info = self.get_shier_shen(rizhu, ganzhi)
            if shen_info:
                result.append({
                    'pillar': pillars[i],
                    'ganzhi': ganzhi,
                    'rizhu': rizhu,
                    'shier_shen': shen_info['name'],
                    'description': shen_info['description'],
                    'influence': shen_info['influence']
                })
        
        return {'shier_shen': result}