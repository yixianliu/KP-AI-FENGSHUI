"""
真太阳时计算器 - 完整实现真太阳时计算

修复内容：
1. 使用 calendar_utils 中的 SolarTimeCalculator 实现完整真太阳时
2. 包含平太阳时+均时差+经度修正
3. 支持时辰地支判断
"""
from datetime import datetime, timedelta
from .calendar_utils import SolarTimeCalculator as CoreSolarTimeCalculator


class SolarTimeCalculator:
    """真太阳时计算器 - 使用核心模块实现完整真太阳时计算"""

    def __init__(self):
        self.core = CoreSolarTimeCalculator()

    def get_solar_time(self, dt, longitude):
        """计算真太阳时（完整实现）
        
        真太阳时 = 平太阳时 + 均时差
        平太阳时 = 北京时间 + 经度修正
        
        参数：
            dt: datetime对象
            longitude: 经度（度）
        
        返回：
            真太阳时datetime对象
        """
        return self.core.get_true_solar_time(dt, longitude)

    def get_mean_solar_time(self, dt, longitude):
        """计算平太阳时（仅经度修正）"""
        return self.core.get_mean_solar_time(dt, longitude)

    def get_equation_of_time(self, day_of_year):
        """计算均时差（分钟）"""
        return self.core.get_equation_of_time(day_of_year)

    def get_hour_zhi(self, solar_hour):
        """根据真太阳时确定时辰地支"""
        return self.core.get_hour_zhi(solar_hour)
