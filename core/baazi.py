from utils.calendar import TIAN_GAN, DI_ZHI
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

class BaZiCalculator:
    def __init__(self):
        self.tian_gan_map = {tg: i for i, tg in enumerate(TIAN_GAN)}
        self.di_zhi_map = {dz: i for i, dz in enumerate(DI_ZHI)}

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

    def get_day_ganzhi(self, solar):
        lunar = Converter.Solar2Lunar(solar)
        return lunar.dayzodiac

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
        
        day_ganzhi = self.get_day_ganzhi(solar)
        
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
        rizhu_idx = self.tian_gan_map[rizhu]
        zhi_idx = self.di_zhi_map[ganzhi[1]]
        shen_idx = (zhi_idx - rizhu_idx * 2 + 12) % 12
        return SHIER_SHEN[shen_idx]