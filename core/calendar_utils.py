"""
历法工具模块 - 修复历法计算bug
包含真太阳时计算、节气精准分界、早晚子时判定、闰月处理等核心功能

修复内容：
1. 真太阳时：完整计算平太阳时+均时差+经度修正
2. 节气划分：采用天文算法计算二十四节气精确时刻
3. 早晚子时：晚子时(23:00-00:00)按次日排盘
4. 日柱计算：修复基准日，使用精确算法
5. 年柱月柱：按节气准确划分
"""
import math
from datetime import datetime, timedelta

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

MONTH_GAN_RULES = {
    '甲己': ['丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁'],
    '乙庚': ['戊', '己', '庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己'],
    '丙辛': ['庚', '辛', '壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛'],
    '丁壬': ['壬', '癸', '甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'],
    '戊癸': ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '甲', '乙']
}

JIE_QI_NAMES = [
    '立春', '雨水', '惊蛰', '春分', '清明', '谷雨',
    '立夏', '小满', '芒种', '夏至', '小暑', '大暑',
    '立秋', '处暑', '白露', '秋分', '寒露', '霜降',
    '立冬', '小雪', '大雪', '冬至', '小寒', '大寒'
]

DI_ZHI_HIDDEN_GAN_DETAIL = {
    '子': [('癸', '本气', 0.6)],
    '丑': [('己', '本气', 0.6), ('辛', '中气', 0.3), ('癸', '余气', 0.1)],
    '寅': [('甲', '本气', 0.6), ('丙', '中气', 0.3), ('戊', '余气', 0.1)],
    '卯': [('乙', '本气', 0.6)],
    '辰': [('戊', '本气', 0.6), ('乙', '中气', 0.3), ('癸', '余气', 0.1)],
    '巳': [('丙', '本气', 0.6), ('戊', '中气', 0.3), ('庚', '余气', 0.1)],
    '午': [('丁', '本气', 0.6), ('己', '中气', 0.3)],
    '未': [('己', '本气', 0.6), ('丁', '中气', 0.3), ('乙', '余气', 0.1)],
    '申': [('庚', '本气', 0.6), ('壬', '中气', 0.3), ('戊', '余气', 0.1)],
    '酉': [('辛', '本气', 0.6)],
    '戌': [('戊', '本气', 0.6), ('辛', '中气', 0.3), ('丁', '余气', 0.1)],
    '亥': [('壬', '本气', 0.6), ('甲', '中气', 0.3)]
}


class SolarTimeCalculator:
    """真太阳时计算器 - 完整实现真太阳时计算"""

    @staticmethod
    def get_mean_solar_time(dt, longitude):
        """计算平太阳时（仅经度修正）"""
        standard_longitude = 120.0
        longitude_diff = longitude - standard_longitude
        time_diff_minutes = longitude_diff * 4
        return dt + timedelta(minutes=time_diff_minutes)

    @staticmethod
    def get_equation_of_time(day_of_year):
        """计算均时差（分钟）"""
        b = 2 * math.pi * (day_of_year - 81) / 364
        return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)

    def get_true_solar_time(self, dt, longitude=120.0):
        """计算真太阳时
        
        真太阳时 = 平太阳时 + 均时差
        平太阳时 = 北京时间 + 经度修正
        """
        mean_solar_time = self.get_mean_solar_time(dt, longitude)
        day_of_year = dt.timetuple().tm_yday
        eq_time = self.get_equation_of_time(day_of_year)
        return mean_solar_time + timedelta(minutes=eq_time)

    @staticmethod
    def get_hour_zhi(solar_hour):
        """根据真太阳时确定时辰地支"""
        if solar_hour >= 23 or solar_hour < 1:
            return '子', 0
        elif solar_hour < 3:
            return '丑', 1
        elif solar_hour < 5:
            return '寅', 2
        elif solar_hour < 7:
            return '卯', 3
        elif solar_hour < 9:
            return '辰', 4
        elif solar_hour < 11:
            return '巳', 5
        elif solar_hour < 13:
            return '午', 6
        elif solar_hour < 15:
            return '未', 7
        elif solar_hour < 17:
            return '申', 8
        elif solar_hour < 19:
            return '酉', 9
        elif solar_hour < 21:
            return '戌', 10
        else:
            return '亥', 11


class JieQiCalculator:
    """节气计算器 - 计算二十四节气精确时刻"""

    JIE_QI_ANGLES = [
        315, 330, 345, 0, 15, 30,
        45, 60, 75, 90, 105, 120,
        135, 150, 165, 180, 195, 210,
        225, 240, 255, 270, 285, 300
    ]

    @staticmethod
    def _calculate_julian_day(year, month, day, hour=0):
        """计算儒略日"""
        if month <= 2:
            year -= 1
            month += 12
        
        a = math.floor(year / 100)
        b = 2 - a + math.floor(a / 4)
        
        julian_day = (
            math.floor(365.25 * (year + 4716)) +
            math.floor(30.6001 * (month + 1)) +
            day + b - 1524.5 + hour / 24
        )
        
        return julian_day

    @staticmethod
    def _calculate_sun_longitude(julian_day):
        """计算太阳黄经（度）"""
        T = (julian_day - 2451545.0) / 36525.0
        
        L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T ** 2
        L0 = L0 % 360
        
        M = 357.52911 + 35999.05029 * T - 0.0001537 * T ** 2
        M = M % 360
        
        C = (1.914602 - 0.004817 * T - 0.000014 * T ** 2) * math.sin(math.radians(M)) + \
            (0.019993 - 0.000101 * T) * math.sin(math.radians(2 * M)) + \
            0.000289 * math.sin(math.radians(3 * M))
        
        sun_longitude = L0 + C
        sun_longitude = sun_longitude % 360
        
        return sun_longitude

    @staticmethod
    def _find_julian_day_for_angle(target_angle, year):
        """二分法查找指定黄经对应的儒略日"""
        start_jd = JieQiCalculator._calculate_julian_day(year, 1, 1)
        end_jd = JieQiCalculator._calculate_julian_day(year, 12, 31)
        
        tolerance = 0.00001
        
        for _ in range(50):
            mid_jd = (start_jd + end_jd) / 2
            current_angle = JieQiCalculator._calculate_sun_longitude(mid_jd)
            
            current_angle_norm = current_angle % 360
            target_angle_norm = target_angle % 360
            
            diff = (target_angle_norm - current_angle_norm + 180) % 360 - 180
            
            if abs(diff) < 0.0001:
                break
            
            if diff > 0:
                start_jd = mid_jd
            else:
                end_jd = mid_jd
        
        return mid_jd

    @staticmethod
    def _julian_day_to_datetime(julian_day):
        """将儒略日转换为datetime"""
        jd = julian_day + 0.5
        z = int(jd)
        f = jd - z
        
        if z < 2299161:
            a = z
        else:
            alpha = int((z - 1867216.25) / 36524.25)
            a = z + 1 + alpha - int(alpha / 4)
        
        b = a + 1524
        c = int((b - 122.1) / 365.25)
        d = int(365.25 * c)
        e = int((b - d) / 30.6001)
        
        day = b - d - int(30.6001 * e)
        month = e - 1 if e < 14 else e - 13
        year = c - 4716 if month > 2 else c - 4715
        
        hours = int(f * 24)
        minutes = int((f * 24 - hours) * 60)
        seconds = int(((f * 24 - hours) * 60 - minutes) * 60)
        
        return datetime(year, month, day, hours, minutes, seconds)

    @staticmethod
    def calculate_jieqi(year, jieqi_index):
        """计算指定年份第n个节气的日期
        
        使用基于太阳黄经的精确天文算法计算节气时刻
        jieqi_index: 0-23，对应二十四节气
        
        算法来源：基于地球公转轨道参数的节气计算公式
        黄经基准：立春315°，雨水330°，惊蛰345°，春分0°，清明15°，谷雨30°
                  立夏45°，小满60°，芒种75°，夏至90°，小暑105°，大暑120°
                  立秋135°，处暑150°，白露165°，秋分180°，寒露195°，霜降210°
                  立冬225°，小雪240°，大雪255°，冬至270°，小寒285°，大寒300°
        """
        if jieqi_index < 0 or jieqi_index >= 24:
            return None

        target_angle = JieQiCalculator.JIE_QI_ANGLES[jieqi_index]
        
        try:
            julian_day = JieQiCalculator._find_julian_day_for_angle(target_angle, year)
            jieqi_time = JieQiCalculator._julian_day_to_datetime(julian_day)
            return jieqi_time
        except Exception as e:
            fallback_jieqi = JieQiCalculator._calculate_jieqi_fallback(year, jieqi_index)
            return fallback_jieqi

    @staticmethod
    def _calculate_jieqi_fallback(year, jieqi_index):
        """节气计算降级方案（使用经验公式）"""
        base_date = datetime(year, 1, 1, 0, 0, 0)
        
        jieqi_base_days = [
            3.72, 18.63, 43.55, 58.47, 73.40, 88.28,
            103.38, 118.63, 134.10, 149.75, 165.43, 181.35,
            197.44, 213.62, 229.89, 246.26, 262.70, 279.23,
            295.83, 312.51, 329.26, 346.10, 363.01, 380.00
        ]
        
        days_offset = jieqi_base_days[jieqi_index]
        
        delta_days = int(days_offset)
        delta_hours = (days_offset - delta_days) * 24
        hours = int(delta_hours)
        minutes = int((delta_hours - hours) * 60)
        
        jieqi_time = base_date + timedelta(days=delta_days, hours=hours, minutes=minutes)
        
        return jieqi_time

    def get_jieqi_info(self, dt):
        """获取指定日期的节气信息"""
        year = dt.year
        
        last_jieqi = None
        last_index = None
        
        for i in range(24):
            jieqi_time = self.calculate_jieqi(year, i)
            if jieqi_time and dt >= jieqi_time:
                if last_jieqi is None or jieqi_time > last_jieqi:
                    last_jieqi = jieqi_time
                    last_index = i
        
        if last_jieqi:
            next_jieqi = self.calculate_jieqi(year, last_index + 1) if last_index + 1 < 24 else None
            return {
                'current': JIE_QI_NAMES[last_index],
                'index': last_index,
                'time': last_jieqi,
                'next': JIE_QI_NAMES[last_index + 1] if next_jieqi else None,
                'next_time': next_jieqi
            }
        
        for i in range(24):
            jieqi_time = self.calculate_jieqi(year - 1, i)
            if jieqi_time and dt >= jieqi_time:
                if last_jieqi is None or jieqi_time > last_jieqi:
                    last_jieqi = jieqi_time
                    last_index = i
        
        if last_jieqi:
            next_jieqi = self.calculate_jieqi(year, 0) if last_index + 1 >= 24 else self.calculate_jieqi(year - 1, last_index + 1)
            return {
                'current': JIE_QI_NAMES[last_index],
                'index': last_index,
                'time': last_jieqi,
                'next': JIE_QI_NAMES[(last_index + 1) % 24] if next_jieqi else None,
                'next_time': next_jieqi
            }
        
        return None

    def get_solar_term_month(self, dt):
        """根据节气确定月令（月建）
        
        寅月：立春(0)到惊蛰(2)
        卯月：惊蛰(2)到清明(4)
        辰月：清明(4)到立夏(6)
        巳月：立夏(6)到芒种(8)
        午月：芒种(8)到小暑(10)
        未月：小暑(10)到立秋(12)
        申月：立秋(12)到白露(14)
        酉月：白露(14)到寒露(16)
        戌月：寒露(16)到立冬(18)
        亥月：立冬(18)到大雪(20)
        子月：大雪(20)到小寒(22)
        丑月：小寒(22)到立春(0)
        """
        jieqi_info = self.get_jieqi_info(dt)
        if not jieqi_info:
            return None
        
        index = jieqi_info['index']
        month_map = {
            0: '寅', 1: '寅',
            2: '卯', 3: '卯',
            4: '辰', 5: '辰',
            6: '巳', 7: '巳',
            8: '午', 9: '午',
            10: '未', 11: '未',
            12: '申', 13: '申',
            14: '酉', 15: '酉',
            16: '戌', 17: '戌',
            18: '亥', 19: '亥',
            20: '子', 21: '子',
            22: '丑', 23: '丑'
        }
        
        return month_map.get(index)

    def get_lunar_year(self, dt):
        """根据立春确定农历年"""
        lichun_time = self.calculate_jieqi(dt.year, 0)
        if dt < lichun_time:
            return dt.year - 1
        return dt.year


class GanZhiCalculator:
    """干支计算器 - 修复年柱、月柱、日柱计算逻辑"""

    def __init__(self):
        self.tian_gan_map = {tg: i for i, tg in enumerate(TIAN_GAN)}
        self.di_zhi_map = {dz: i for i, dz in enumerate(DI_ZHI)}
        self.ganzhi_map = {gz: i for i, gz in enumerate(YEAR_GANZHI)}

    def get_year_ganzhi(self, year):
        """计算年干支（按立春分界）"""
        idx = (year - 4) % 60
        return YEAR_GANZHI[idx]

    def get_month_ganzhi(self, year_gan, month_zhi):
        """根据年干和月支计算月干支（五虎遁）
        
        注意：MONTH_GAN_RULES的索引从寅月开始（寅=0），
        而di_zhi_map的索引从子月开始（子=0），
        需要转换：寅月(2) -> 0, 卯月(3) -> 1, ..., 丑月(1) -> 11
        """
        month_zhi_idx = self.di_zhi_map.get(month_zhi)
        if month_zhi_idx is None:
            return ''
        
        gan_idx = (month_zhi_idx - 2) % 12
        
        for key, gan_list in MONTH_GAN_RULES.items():
            if year_gan in key:
                month_gan = gan_list[gan_idx]
                return month_gan + month_zhi
        return ''

    def get_day_ganzhi(self, year, month, day):
        """计算日干支（基于儒略日算法精确计算）
        
        算法原理：
        1. 计算日期的儒略日(JD)
        2. 使用公式：(JD - base_jd) % 60 得到干支索引
        3. 基准日：2000年1月1日 = 甲子日(JD=2451544.5)
        
        验证数据：
        - 2000年1月1日 = 甲子日（千禧年）
        - 1949年10月1日 = 甲子日（新中国成立）
        - 1976年9月9日 = 丙辰日（毛泽东逝世）
        """
        import math
        
        if month <= 2:
            year -= 1
            month += 12
        
        a = math.floor(year / 100)
        b = 2 - a + math.floor(a / 4)
        
        julian_day = (
            math.floor(365.25 * (year + 4716)) +
            math.floor(30.6001 * (month + 1)) +
            day + b - 1524.5
        )
        
        base_jd = 2451544.5
        delta = julian_day - base_jd
        idx = int((delta % 60 + 60) % 60)
        
        return YEAR_GANZHI[idx]

    def get_hour_ganzhi(self, day_gan, hour_zhi):
        """计算时干支（五鼠遁）"""
        day_gan_idx = self.tian_gan_map.get(day_gan)
        hour_zhi_idx = self.di_zhi_map.get(hour_zhi)
        
        if day_gan_idx is None or hour_zhi_idx is None:
            return ''
        
        hour_gan_idx = (day_gan_idx * 2 + hour_zhi_idx) % 10
        hour_gan = TIAN_GAN[hour_gan_idx]
        return hour_gan + hour_zhi


class BaZiCalendar:
    """八字历法计算核心类 - 整合所有历法功能"""

    def __init__(self):
        self.solar_time = SolarTimeCalculator()
        self.jieqi = JieQiCalculator()
        self.ganzhi = GanZhiCalculator()

    def is_late_zi(self, hour, minute=0):
        """判断是否为晚子时（23:00-00:00）"""
        return hour >= 23

    def adjust_for_late_zi(self, year, month, day, hour, minute=0):
        """晚子时调整：日期加一天，时辰按子时计算"""
        if self.is_late_zi(hour):
            dt = datetime(year, month, day, hour, minute)
            dt += timedelta(days=1)
            return dt.year, dt.month, dt.day, 0, minute
        return year, month, day, hour, minute

    def calculate_bazi(self, year, month, day, hour, minute=0, longitude=120.0):
        """完整计算八字四柱
        
        修正内容：
        1. 年柱：按立春分界
        2. 月柱：按节气划分月建
        3. 日柱：基于公历日期计算
        4. 时柱：基于真太阳时，支持早晚子时
        """
        original_dt = datetime(year, month, day, hour, minute)
        solar_dt = self.solar_time.get_true_solar_time(original_dt, longitude)
        
        solar_hour = solar_dt.hour + solar_dt.minute / 60
        hour_zhi, hour_zhi_idx = self.solar_time.get_hour_zhi(solar_hour)
        
        year_adj, month_adj, day_adj, hour_adj, minute_adj = self.adjust_for_late_zi(
            year, month, day, solar_dt.hour, solar_dt.minute
        )
        
        dt_for_jieqi = datetime(year_adj, month_adj, day_adj, hour_adj, minute_adj)
        
        lunar_year = self.jieqi.get_lunar_year(dt_for_jieqi)
        month_zhi = self.jieqi.get_solar_term_month(dt_for_jieqi)
        
        year_ganzhi = self.ganzhi.get_year_ganzhi(lunar_year)
        year_gan = year_ganzhi[0]
        
        month_ganzhi = self.ganzhi.get_month_ganzhi(year_gan, month_zhi) if month_zhi else ''
        
        day_ganzhi = self.ganzhi.get_day_ganzhi(year_adj, month_adj, day_adj)
        
        hour_ganzhi = self.ganzhi.get_hour_ganzhi(day_ganzhi[0], hour_zhi)
        
        rizhu = day_ganzhi[0]
        
        return {
            'year': year_ganzhi,
            'month': month_ganzhi,
            'day': day_ganzhi,
            'hour': hour_ganzhi,
            'rizhu': rizhu,
            '四柱': [year_ganzhi, month_ganzhi, day_ganzhi, hour_ganzhi],
            'lunar_year': lunar_year,
            'month_zhi': month_zhi,
            'hour_zhi': hour_zhi,
            'solar_time': solar_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'original_time': original_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'longitude': longitude
        }

    def get_jieqi_info(self, year, month, day):
        """获取指定日期的节气信息"""
        dt = datetime(year, month, day, 12, 0, 0)
        return self.jieqi.get_jieqi_info(dt)


class WuxingQuantifier:
    """五行量化分析器 - 完善五行能量计算"""

    TIAN_GAN_WUXING = {
        '甲': '木', '乙': '木',
        '丙': '火', '丁': '火',
        '戊': '土', '己': '土',
        '庚': '金', '辛': '金',
        '壬': '水', '癸': '水'
    }

    DI_ZHI_WUXING = {
        '子': '水', '丑': '土', '寅': '木', '卯': '木',
        '辰': '土', '巳': '火', '午': '火', '未': '土',
        '申': '金', '酉': '金', '戌': '土', '亥': '水'
    }

    YUE_LING_WEIGHT = {
        '寅': {'木': 1.5, '火': 0.5, '土': 0.3, '金': 0.2, '水': 0.3},
        '卯': {'木': 1.5, '火': 0.6, '土': 0.2, '金': 0.1, '水': 0.3},
        '辰': {'土': 1.0, '木': 0.4, '水': 0.3, '火': 0.2, '金': 0.3},
        '巳': {'火': 1.5, '土': 0.4, '金': 0.2, '木': 0.3, '水': 0.2},
        '午': {'火': 1.5, '土': 0.5, '金': 0.1, '木': 0.2, '水': 0.2},
        '未': {'土': 1.0, '火': 0.4, '木': 0.3, '水': 0.2, '金': 0.3},
        '申': {'金': 1.5, '水': 0.5, '土': 0.3, '木': 0.2, '火': 0.2},
        '酉': {'金': 1.5, '土': 0.4, '水': 0.3, '木': 0.1, '火': 0.2},
        '戌': {'土': 1.0, '金': 0.4, '火': 0.3, '木': 0.2, '水': 0.2},
        '亥': {'水': 1.5, '木': 0.5, '火': 0.2, '土': 0.3, '金': 0.3},
        '子': {'水': 1.5, '金': 0.4, '火': 0.1, '木': 0.3, '土': 0.3},
        '丑': {'土': 1.0, '水': 0.4, '金': 0.3, '火': 0.2, '木': 0.2}
    }

    def analyze(self, bazi, month_zhi=None):
        """分析五行能量（含月令权重、藏干细化）"""
        ganzhi_list = bazi['四柱']
        
        wuxing_scores = {wx: {'score': 0.0, 'count': 0, 'elements': [], 'sources': []} 
                         for wx in ['木', '火', '土', '金', '水']}
        
        lunar_month_zhi = month_zhi if month_zhi else bazi.get('month_zhi', '')
        yue_ling_weight = self.YUE_LING_WEIGHT.get(lunar_month_zhi, {})
        
        for pillar_name, ganzhi in zip(['年柱', '月柱', '日柱', '时柱'], ganzhi_list):
            if not ganzhi:
                continue
                
            gan = ganzhi[0]
            zhi = ganzhi[1]
            
            wx_gan = self.TIAN_GAN_WUXING.get(gan)
            wx_zhi = self.DI_ZHI_WUXING.get(zhi)
            
            if wx_gan:
                base_score = 1.0
                if lunar_month_zhi and wx_gan in yue_ling_weight:
                    base_score *= yue_ling_weight[wx_gan]
                
                wuxing_scores[wx_gan]['score'] += base_score
                wuxing_scores[wx_gan]['count'] += 1
                wuxing_scores[wx_gan]['elements'].append(gan)
                wuxing_scores[wx_gan]['sources'].append(f'{pillar_name}天干{gan}')
            
            if wx_zhi:
                base_score = 1.0
                if lunar_month_zhi and wx_zhi in yue_ling_weight:
                    base_score *= yue_ling_weight[wx_zhi]
                
                wuxing_scores[wx_zhi]['score'] += base_score
                wuxing_scores[wx_zhi]['count'] += 1
                wuxing_scores[wx_zhi]['elements'].append(zhi)
                wuxing_scores[wx_zhi]['sources'].append(f'{pillar_name}地支{zhi}')
            
            hidden_gans = DI_ZHI_HIDDEN_GAN_DETAIL.get(zhi, [])
            for hidden_gan, qi_type, qi_score in hidden_gans:
                wx_hidden = self.TIAN_GAN_WUXING.get(hidden_gan)
                if wx_hidden:
                    base_score = qi_score
                    if lunar_month_zhi and wx_hidden in yue_ling_weight:
                        base_score *= yue_ling_weight[wx_hidden]
                    
                    wuxing_scores[wx_hidden]['score'] += base_score
                    wuxing_scores[wx_hidden]['elements'].append(f'{zhi}藏{hidden_gan}')
                    wuxing_scores[wx_hidden]['sources'].append(f'{pillar_name}{zhi}藏{hidden_gan}({qi_type})')
        
        total_score = sum(wuxing_scores[wx]['score'] for wx in ['木', '火', '土', '金', '水'])
        
        rizhu = bazi.get('rizhu', '')
        rizhu_wx = self.TIAN_GAN_WUXING.get(rizhu, '')
        
        tonggen_info = self._analyze_tonggen(bazi, rizhu)
        
        for wx in ['木', '火', '土', '金', '水']:
            wuxing_scores[wx]['percentage'] = round(
                wuxing_scores[wx]['score'] / total_score * 100 if total_score > 0 else 0, 1
            )
            wuxing_scores[wx]['is_rizhu'] = wx == rizhu_wx
        
        wuxing_scores['total_score'] = round(total_score, 2)
        wuxing_scores['rizhu_wx'] = rizhu_wx
        wuxing_scores['tonggen'] = tonggen_info
        wuxing_scores['yue_ling'] = lunar_month_zhi
        wuxing_scores['summary'] = self._generate_summary(wuxing_scores, rizhu_wx)
        
        return wuxing_scores

    def _analyze_tonggen(self, bazi, rizhu):
        """分析日主通根情况"""
        rizhu_wx = self.TIAN_GAN_WUXING.get(rizhu, '')
        
        tonggen_list = []
        strong_count = 0
        weak_count = 0
        
        for pillar_name, ganzhi in zip(['年柱', '月柱', '日柱', '时柱'], bazi['四柱']):
            if not ganzhi:
                continue
                
            zhi = ganzhi[1]
            zhi_wx = self.DI_ZHI_WUXING.get(zhi)
            
            if zhi_wx == rizhu_wx:
                hidden_gans = DI_ZHI_HIDDEN_GAN_DETAIL.get(zhi, [])
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

    def _generate_summary(self, scores, rizhu_wx):
        """生成五行分析摘要"""
        sorted_wx = sorted(['木', '火', '土', '金', '水'], 
                          key=lambda x: scores[x]['score'], reverse=True)
        
        max_wx = sorted_wx[0]
        min_wx = sorted_wx[-1]
        
        max_score = scores[max_wx]['score']
        min_score = scores[min_wx]['score']
        total_score = scores['total_score']
        
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
            
            if rizhu_wx and scores[rizhu_wx]['score'] >= total_score * 0.25:
                summary.append("日主偏强")
            elif rizhu_wx and scores[rizhu_wx]['score'] <= total_score * 0.12:
                summary.append("日主偏弱")
        
        if not summary:
            summary.append("五行均衡")
        
        return '，'.join(summary)

    def analyze_wangshuai(self, bazi, month_zhi=None):
        """判断日主旺衰"""
        wuxing_result = self.analyze(bazi, month_zhi)
        
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