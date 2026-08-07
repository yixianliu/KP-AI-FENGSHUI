"""
历法工具模块 - 修复历法计算bug
包含真太阳时计算、节气精准分界、早晚子时判定、闰月处理等核心功能

修复内容：
1. 真太阳时：完整计算平太阳时+均时差+经度修正
2. 节气划分：采用天文算法计算二十四节气精确时刻
3. 早晚子时：晚子时(23:00-00:00)按次日排盘
4. 日柱计算：修复基准日，使用精确算法
5. 年柱月柱：按节气准确划分
数据来源：MySQL数据库
"""
import math
from datetime import datetime, timedelta
from core.database_manager import DatabaseManager


def _get_db():
    """返回 DatabaseManager 实例，供本模块各计算类惰性加载干支/节气等基础数据。"""
    return DatabaseManager()


def _ensure_data():
    """确保基础数据已加载"""
    global TIAN_GAN, DI_ZHI, YEAR_GANZHI, MONTH_GAN_RULES
    global JIE_QI_NAMES, DI_ZHI_HIDDEN_GAN_DETAIL, JIE_QI_ANGLES, JIE_QI_BASE_DAYS, JIE_QI_MONTH_MAP
    db = _get_db()
    TIAN_GAN = db.get_tian_gan_list()
    DI_ZHI = db.get_di_zhi_list()
    YEAR_GANZHI = db.get_sixty_jiazi()
    MONTH_GAN_RULES = db.get_month_gan_rules()
    JIE_QI_NAMES = db.get_jie_qi_list()
    DI_ZHI_HIDDEN_GAN_DETAIL = db.get_di_zhi_hidden_gan()
    JIE_QI_ANGLES = db.get_jie_qi_angles()
    JIE_QI_BASE_DAYS = db.get_jie_qi_base_days()
    JIE_QI_MONTH_MAP = db.get_jie_qi_month_map()


# 模块级变量，首次使用时从数据库加载
TIAN_GAN = None
DI_ZHI = None
YEAR_GANZHI = None
MONTH_GAN_RULES = None
JIE_QI_NAMES = None
DI_ZHI_HIDDEN_GAN_DETAIL = None
JIE_QI_ANGLES = None
JIE_QI_BASE_DAYS = None
JIE_QI_MONTH_MAP = None


def _lazy_init():
    """延迟初始化"""
    if TIAN_GAN is None:
        _ensure_data()


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

    @property
    def JIE_QI_ANGLES(self):
        """返回二十四节气对应的黄经角度表（list[float]）。

        首次访问触发数据库惰性加载；库内为空时回退空列表，避免排盘崩溃。
        """
        _lazy_init()
        return list(JIE_QI_ANGLES) if JIE_QI_ANGLES else []

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

        _lazy_init()
        target_angle = JIE_QI_ANGLES[jieqi_index] if JIE_QI_ANGLES else 0
        
        try:
            julian_day = JieQiCalculator._find_julian_day_for_angle(target_angle, year)
            jieqi_time = JieQiCalculator._julian_day_to_datetime(julian_day)
            return jieqi_time
        except Exception:
            return JieQiCalculator._calculate_jieqi_fallback(year, jieqi_index)

    @staticmethod
    def _calculate_jieqi_fallback(year, jieqi_index):
        """节气计算降级方案（使用经验公式）"""
        _lazy_init()
        base_date = datetime(year, 1, 1, 0, 0, 0)
        
        days_offset = JIE_QI_BASE_DAYS[jieqi_index] if JIE_QI_BASE_DAYS else 0
        
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
        _lazy_init()
        jieqi_info = self.get_jieqi_info(dt)
        if not jieqi_info:
            return None
        
        index = jieqi_info['index']
        
        return JIE_QI_MONTH_MAP.get(index) if JIE_QI_MONTH_MAP else None

    def get_lunar_year(self, dt):
        """根据立春确定农历年"""
        lichun_time = self.calculate_jieqi(dt.year, 0)
        if dt < lichun_time:
            return dt.year - 1
        return dt.year


class GanZhiCalculator:
    """干支计算器 - 修复年柱、月柱、日柱计算逻辑"""

    def __init__(self):
        """初始化干支映射表（天干/地支/六十甲子 → 序号），供年/月/日/时柱计算取用。"""
        _lazy_init()
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
        3. 基准日：2000年1月1日 午夜 JD = 2451544.5

        ⚠️ 历史偏移修正：原代码直接用 (JD - 2451544.5) % 60 并把 2000-01-01 当作「甲子」，
        但经权威万年历核验，2000-01-01 实为「戊午」（干支序号 54），1949-10-01 实为「甲子」
        （序号 0），2026-07-09 实为「甲申」（序号 20）。即代码结果整体比真实历法
        **落后 6 个干支位**，等价于真实序号 = (代码序号 - 6) mod 60。
        故在取模后减去 6 以对齐真实历法。

        验证数据（已核验一致）：
        - 2000-01-01 = 戊午
        - 1949-10-01 = 甲子
        - 2026-07-09 = 甲申
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
        # 真实历法相对代码基准存在 -6 个干支位的固定偏移（见函数说明）
        idx = (int((delta % 60 + 60) % 60) - 6) % 60

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
        """聚合历法三大组件：真太阳时、节气、干支计算器，作为八字计算的核心入口。"""
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
    """五行量化分析器 - 完善五行能量计算（已废弃，请使用core.wuxing.WuXingAnalyzer）
    
    保留此类仅为兼容旧代码，实际逻辑已迁移至core.wuxing模块。
    """
    from core.wuxing import WuXingAnalyzer as _WuXingAnalyzer, TIAN_GAN_WUXING, DI_ZHI_WUXING, DI_ZHI_HIDDEN_GAN_DETAIL, YUE_LING_WEIGHT
    
    TIAN_GAN_WUXING = TIAN_GAN_WUXING
    DI_ZHI_WUXING = DI_ZHI_WUXING
    YUE_LING_WEIGHT = YUE_LING_WEIGHT
    
    def __init__(self):
        """兼容旧接口：内部委托给 core.wuxing.WuXingAnalyzer，本类仅作薄包装。"""
        self._analyzer = self._WuXingAnalyzer()

    def analyze(self, bazi, month_zhi=None):
        """委托计算八字五行能量分布，签名与旧 WuxingQuantifier 保持一致。"""
        return self._analyzer.analyze(bazi, month_zhi)

    def analyze_wangshuai(self, bazi, month_zhi=None):
        """委托计算五行旺衰（身强/身弱/中和），对齐旧接口。"""
        return self._analyzer.analyze_wangshuai(bazi, month_zhi)