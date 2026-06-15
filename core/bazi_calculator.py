"""
八字计算器 - 适配新UI的简化接口
"""
from .baazi import BaZiCalculator as CoreBaZiCalculator
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

    def calculate(self, year, month, day, hour, is_early_zi=False):
        """计算八字四柱，返回同时兼容UI展示和底层分析器的格式"""
        result = self.core.calculate(year, month, day, hour, is_lunar=False)
        return {
            # UI展示用
            'year_pillar': result['year'],
            'month_pillar': result['month'],
            'day_pillar': result['day'],
            'hour_pillar': result['hour'],
            # 底层分析器用
            'year': result['year'],
            'month': result['month'],
            'day': result['day'],
            'hour': result['hour'],
            'rizhu': result['rizhu'],
            'solar_date': result['solar_date'],
            'lunar_date': result['lunar_date'],
            '四柱': result['四柱'],
        }

    def get_wuxing(self, bazi):
        """获取五行分析"""
        return self.wuxing_analyzer.analyze(bazi)

    def get_shishen(self, bazi):
        """获取十神分析"""
        return self.shishen_analyzer.analyze(bazi)

    def get_dayun(self, bazhi, gender, birth_year):
        """获取大运"""
        return self.yunshi_calc.calculate_major_fortune(bazhi, gender, birth_year)

    def get_liunian(self, bazhi, start_year=2024, years_count=10):
        """获取流年"""
        return self.yunshi_calc.calculate_annual_fortune(bazhi, start_year, years_count)

    def get_mingli(self, bazhi):
        """获取命理综合分析（藏干、纳音、神煞、主星、干支关系、自坐、空亡）"""
        return self.mingli_analyzer.analyze_all(bazhi)

    def analyze_all(self, bazi, gender, birth_year):
        """一键获取所有分析结果"""
        wuxing = self.get_wuxing(bazi)
        shishen = self.get_shishen(bazi)
        dayun = self.get_dayun(bazi, gender, birth_year)
        liunian = self.get_liunian(bazi)
        mingli = self.get_mingli(bazi)
        return {
            'bazi': bazi,
            'wuxing': wuxing,
            'shishen': shishen,
            'dayun': dayun,
            'liunian': liunian,
            'mingli': mingli,
        }
