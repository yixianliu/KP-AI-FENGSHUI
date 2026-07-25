"""
八字计算器 - 专业细盘系统，整合所有命理分析功能
"""
from ._baazi_compat import BaZiCalculator as CoreBaZiCalculator
from .wuxing import WuXingAnalyzer
from .shishen import ShiShenAnalyzer
from .yunshi import YunShiCalculator
from .mingli import MingLiAnalyzer


class BaziCalculator:
    """八字计算器 - 统一入口，整合所有命理分析功能"""

    def __init__(self):
        self.core = CoreBaZiCalculator()
        self.wuxing_analyzer = WuXingAnalyzer()
        self.shishen_analyzer = ShiShenAnalyzer()
        self.yunshi_calc = YunShiCalculator()
        self.mingli_analyzer = MingLiAnalyzer()

    def calculate(self, year, month, day, hour, minute=0, longitude=120.0, is_lunar=False):
        """计算八字四柱，返回同时兼容UI展示和底层分析器的格式
        
        参数：
            year: 公历年
            month: 公历月
            day: 公历日
            hour: 小时
            minute: 分钟（新增，支持真太阳时精确计算）
            longitude: 经度（新增，用于真太阳时修正）
            is_lunar: 是否为农历
        """
        result = self.core.calculate(year, month, day, hour, minute, longitude, is_lunar)
        return {
            'year_pillar': result['year'],
            'month_pillar': result['month'],
            'day_pillar': result['day'],
            'hour_pillar': result['hour'],
            'year': result['year'],
            'month': result['month'],
            'day': result['day'],
            'hour': result['hour'],
            'rizhu': result['rizhu'],
            'solar_date': result['solar_date'],
            'lunar_date': result['lunar_date'],
            '四柱': result['四柱'],
            'month_zhi': result.get('month_zhi', ''),
            'hour_zhi': result.get('hour_zhi', ''),
            'solar_time': result.get('solar_time', ''),
            'original_time': result.get('original_time', ''),
            'longitude': result.get('longitude', 120.0),
        }

    def get_wuxing(self, bazi):
        """获取五行分析"""
        return self.wuxing_analyzer.analyze(bazi)

    def get_shishen(self, bazi):
        """获取十神分析"""
        return self.shishen_analyzer.analyze(bazi)

    def get_dayun(self, bazhi, gender, birth_year, birth_dt=None):
        """获取大运"""
        return self.yunshi_calc.calculate_major_fortune(bazhi, gender, birth_year, birth_dt=birth_dt)

    def get_liunian(self, bazhi, start_year=2024, years_count=10):
        """获取流年"""
        return self.yunshi_calc.calculate_annual_fortune(bazhi, start_year, years_count)

    def get_mingli(self, bazhi):
        """获取命理综合分析（藏干、纳音、神煞、主星、干支关系、自坐、空亡）"""
        return self.mingli_analyzer.analyze_all(bazhi)

    def get_shier_shen(self, bazhi):
        """获取十二长生分析"""
        return self.core.analyze_shier_shen(bazhi)

    def analyze_all(self, bazi, gender, birth_year):
        """一键获取所有分析结果（专业细盘完整版）"""
        wuxing = self.get_wuxing(bazi)
        shishen = self.get_shishen(bazi)
        dayun = self.get_dayun(bazi, gender, birth_year)
        liunian = self.get_liunian(bazi)
        mingli = self.get_mingli(bazi)
        shier_shen = self.get_shier_shen(bazi)
        
        return {
            'bazi': bazi,
            'wuxing': wuxing,
            'shishen': shishen,
            'dayun': dayun,
            'liunian': liunian,
            'mingli': mingli,
            'shier_shen': shier_shen,
        }

    def get_professional_chart(self, bazi, gender, birth_year):
        """获取专业细盘完整数据，包含所有分析维度"""
        full_data = self.analyze_all(bazi, gender, birth_year)
        
        return {
            'basic': {
                '四柱': bazi['四柱'],
                'rizhu': bazi['rizhu'],
                'solar_date': bazi['solar_date'],
                'lunar_date': bazi['lunar_date'],
            },
            'wuxing': full_data['wuxing'],
            'shishen': full_data['shishen'],
            'shier_shen': full_data['shier_shen'],
            'nayin': full_data['mingli']['nayin'],
            'hidden_stems': full_data['mingli']['hidden_stems'],
            'shensha': full_data['mingli']['shensha'],
            'ganzhi_relations': full_data['mingli']['ganzhi_relations'],
            'self_seat': full_data['mingli']['self_seat'],
            'kongwang': full_data['mingli']['kongwang'],
            'dayun': full_data['dayun'],
            'liunian': full_data['liunian'],
        }
