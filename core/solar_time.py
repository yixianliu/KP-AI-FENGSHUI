"""
真太阳时计算器
"""
import math
from datetime import datetime, timedelta


class SolarTimeCalculator:
    """真太阳时计算器"""

    def get_solar_time(self, dt, longitude):
        """计算真太阳时

        根据经度调整时区，每15度经度相差1小时
        """
        standard_longitude = 120.0
        longitude_diff = longitude - standard_longitude
        time_diff_minutes = longitude_diff * 4
        return dt + timedelta(minutes=time_diff_minutes)

    @staticmethod
    def get_equation_of_time(day_of_year):
        """计算均时差（分钟）

        使用简化公式
        """
        b = 2 * math.pi * (day_of_year - 81) / 364
        return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
