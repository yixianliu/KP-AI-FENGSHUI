from lunarcalendar import Converter, Solar, Lunar

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

FIRST_DAY_GANZHI = '甲子'
BASE_YEAR = 1900

class BaZiCalculator:
    def __init__(self):
        self.tian_gan_map = {tg: i for i, tg in enumerate(TIAN_GAN)}
        self.di_zhi_map = {dz: i for i, dz in enumerate(DI_ZHI)}
        self.ganzhi_map = {gz: i for i, gz in enumerate(YEAR_GANZHI)}

    def get_year_ganzhi(self, year):
        idx = (year - 4) % 60
        return YEAR_GANZHI[idx]

    def get_month_ganzhi(self, year_gan, month):
        month_idx = month - 1
        for key, gan_list in MONTH_GAN:
            if year_gan in key:
                month_gan = gan_list[month_idx]
                month_zhi = DI_ZHI[month_idx]
                return month_gan + month_zhi
        return ''

    def get_day_ganzhi(self, year, month, day):
        total_days = self.get_days_since_base(year, month, day)
        idx = (self.ganzhi_map[FIRST_DAY_GANZHI] + total_days) % 60
        return YEAR_GANZHI[idx]

    def get_days_since_base(self, year, month, day):
        days = 0
        
        for y in range(BASE_YEAR, year):
            if self.is_leap_year(y):
                days += 366
            else:
                days += 365
        
        month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if self.is_leap_year(year):
            month_days[1] = 29
        
        for m in range(1, month):
            days += month_days[m-1]
        
        days += (day - 1)
        
        return days

    def is_leap_year(self, year):
        if year % 400 == 0:
            return True
        if year % 100 == 0:
            return False
        if year % 4 == 0:
            return True
        return False

    def get_hour_ganzhi(self, day_gan, hour):
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

    def calculate(self, year, month, day, hour, is_lunar=False):
        if is_lunar:
            lunar = Lunar(year, month, day)
            solar = Converter.Lunar2Solar(lunar)
        else:
            solar = Solar(year, month, day)
            lunar = Converter.Solar2Lunar(solar)

        year_ganzhi = self.get_year_ganzhi(solar.year)
        year_gan = year_ganzhi[0]
        
        month_idx = solar.month
        month_ganzhi = self.get_month_ganzhi(year_gan, month_idx)
        
        day_ganzhi = self.get_day_ganzhi(solar.year, solar.month, solar.day)
        
        hour_ganzhi = self.get_hour_ganzhi(day_ganzhi[0], hour)

        return {
            'solar_date': f"{solar.year}-{solar.month}-{solar.day}",
            'lunar_date': f"{lunar.year}年{lunar.month}月{lunar.day}日",
            'year': year_ganzhi,
            'month': month_ganzhi,
            'day': day_ganzhi,
            'hour': hour_ganzhi,
            'rizhu': day_ganzhi[0],
            '四柱': [year_ganzhi, month_ganzhi, day_ganzhi, hour_ganzhi]
        }

    def get_shier_shen(self, rizhu, ganzhi):
        zhi = ganzhi[1]
        shier_shen_list = TIAN_GAN_SHIER_SHEN_MAP.get(rizhu, [])
        if shier_shen_list and zhi in shier_shen_list:
            shen_idx = shier_shen_list.index(zhi)
            shen_name = SHIER_SHEN[shen_idx]
            detail = SHIER_SHEN_DETAIL.get(shen_name, {})
            return {
                'name': shen_name,
                'description': detail.get('description', ''),
                'influence': detail.get('influence', '')
            }
        return None

    def analyze_shier_shen(self, bazhi):
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