from lunarcalendar import Converter, Solar, Lunar, DateNotExist

TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

def solar_to_lunar(year, month, day):
    try:
        solar = Solar(year, month, day)
        lunar = Converter.Solar2Lunar(solar)
        return {
            'year': lunar.year,
            'month': lunar.month,
            'day': lunar.day,
            'isleap': lunar.isleap,
            'year_ganzhi': lunar.yearzodiac,
            'month_ganzhi': lunar.monthzodiac,
            'day_ganzhi': lunar.dayzodiac
        }
    except DateNotExist:
        return None

def lunar_to_solar(year, month, day, isleap=False):
    try:
        lunar = Lunar(year, month, day, isleap)
        solar = Converter.Lunar2Solar(lunar)
        return {
            'year': solar.year,
            'month': solar.month,
            'day': solar.day
        }
    except DateNotExist:
        return None

def get_ganzhi(year, month, day, is_lunar=False):
    if is_lunar:
        lunar = Lunar(year, month, day)
        return lunar.yearzodiac, lunar.monthzodiac, lunar.dayzodiac
    else:
        solar = Solar(year, month, day)
        lunar = Converter.Solar2Lunar(solar)
        return lunar.yearzodiac, lunar.monthzodiac, lunar.dayzodiac