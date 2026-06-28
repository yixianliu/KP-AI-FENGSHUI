from core.calendar_utils import BaZiCalendar
from core.database_manager import DatabaseManager
from datetime import datetime


def _get_db():
    return DatabaseManager()


def _ensure_data():
    global TIAN_GAN, DI_ZHI, YEAR_GANZHI, MONTH_GAN, SHIER_SHEN
    global SHIER_SHEN_DETAIL, SHIER_SHEN_LOOKUP
    db = _get_db()
    TIAN_GAN = db.get_tian_gan_list()
    DI_ZHI = db.get_di_zhi_list()
    YEAR_GANZHI = db.get_sixty_jiazi()
    
    # 月干规则
    rules = db.get_month_gan_rules()
    MONTH_GAN = []
    for key, gan_list in rules.items():
        MONTH_GAN.append((key, gan_list))
    
    # 十二长生
    changsheng_rows = db.get_shier_changsheng()
    SHIER_SHEN = list(changsheng_rows.keys())
    SHIER_SHEN_DETAIL = {}
    for name, info in changsheng_rows.items():
        SHIER_SHEN_DETAIL[name] = {
            'description': info.get('description', info.get('meaning', '')),
            'influence': info.get('influence', '')
        }
    
    # 十二长生映射 - 从数据库 changsheng_lookup 表获取
    changsheng_lookup = db.get_changsheng_lookup()
    SHIER_SHEN_LOOKUP = {}
    for gan, zhi_map in changsheng_lookup.items():
        SHIER_SHEN_LOOKUP[gan] = {}
        for zhi, shen_name in zhi_map.items():
            detail = SHIER_SHEN_DETAIL.get(shen_name, {})
            SHIER_SHEN_LOOKUP[gan][zhi] = {
                'name': shen_name,
                'description': detail.get('description', ''),
                'influence': detail.get('influence', '')
            }


# 模块级变量，首次使用时加载
TIAN_GAN = None
DI_ZHI = None
YEAR_GANZHI = None
MONTH_GAN = None
SHIER_SHEN = None
SHIER_SHEN_DETAIL = None
SHIER_SHEN_LOOKUP = None

FIRST_DAY_GANZHI = '甲子'
BASE_YEAR = 1900


def _lazy_init():
    if TIAN_GAN is None:
        _ensure_data()


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
        _lazy_init()
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