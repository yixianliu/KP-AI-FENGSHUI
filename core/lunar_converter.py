"""
农历转换器 - 适配新UI的简化接口
"""
from .baazi import BaZiCalculator


class LunarConverter:
    """农历转换器适配类"""

    def __init__(self):
        self.core = BaZiCalculator()

    def lunar_to_solar(self, year, month, day, is_leap=False):
        """农历转公历"""
        try:
            result = self.core.calculate(year, month, day, 12, is_lunar=True)
            solar = result['solar_date'].split('-')
            return (int(solar[0]), int(solar[1]), int(solar[2]))
        except:
            return None

    def solar_to_lunar(self, year, month, day):
        """公历转农历"""
        try:
            result = self.core.calculate(year, month, day, 12, is_lunar=False)
            lunar = result['lunar_date']
            # 解析 "2026年1月1日" 格式
            lunar = lunar.replace('年', '-').replace('月', '-').replace('日', '')
            parts = lunar.split('-')
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except:
            return None
