"""
农历转换器 —— 面向 UI 的公历/农历互转轻量适配层

设计说明：
    真正的历法换算由 core.calendar_utils 完成，本模块只做两件事：
      1. 把「排盘结果字典」里的日期字符串拆解成 (年, 月, 日) 元组，
         方便 UI 的 QDateEdit / QComboBox 直接消费；
      2. 换算失败时返回 None 或原样字符串，保证界面不会因异常中断。

    统一传入 hour=12（正午）是刻意为之：中午时刻远离子时边界，
    可避免早晚子时规则把日期推到前后一天，从而保证纯日期换算的稳定性。
"""
import logging

from ._baazi_compat import BaZiCalculator

logger = logging.getLogger(__name__)


class LunarConverter:
    """农历转换器适配类，内部委托 BaZiCalculator 完成历法计算。"""

    def __init__(self):
        """构造时持有一个排盘计算器实例，供后续各转换方法复用。"""
        self.core = BaZiCalculator()

    def lunar_to_solar(self, year, month, day, is_leap=False):
        """农历日期转公历日期。

        Args:
            year: 农历年。
            month: 农历月。
            day: 农历日。
            is_leap: 是否闰月（当前底层按普通月处理，保留参数以兼容调用方）。

        Returns:
            tuple[int, int, int] | None: 成功返回 (公历年, 月, 日)，
            日期非法或底层计算异常时返回 None。
        """
        try:
            result = self.core.calculate(year, month, day, 12, is_lunar=True)
            solar = result['solar_date'].split('-')
            return (int(solar[0]), int(solar[1]), int(solar[2]))
        except Exception as exc:
            logger.warning('[农历转换] 农历转公历失败 %s-%s-%s: %s', year, month, day, exc)
            return None

    def solar_to_lunar(self, year, month, day):
        """公历日期转农历日期。

        底层返回的是「YYYY年M月D日」格式字符串，这里把三个汉字分隔符
        统一替换为 '-' 后再切分，得到纯数字元组。

        Args:
            year: 公历年。
            month: 公历月。
            day: 公历日。

        Returns:
            tuple[int, int, int] | None: 成功返回 (农历年, 月, 日)，失败返回 None。
        """
        try:
            result = self.core.calculate(year, month, day, 12, is_lunar=False)
            lunar = result['lunar_date']
            lunar = lunar.replace('年', '-').replace('月', '-').replace('日', '')
            parts = lunar.split('-')
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except Exception as exc:
            logger.warning('[农历转换] 公历转农历失败 %s-%s-%s: %s', year, month, day, exc)
            return None

    def get_lunar_date_string(self, year, month, day):
        """获取可直接展示的农历日期字符串。

        与 :meth:`solar_to_lunar` 的区别：本方法不做拆分，直接返回
        「YYYY年M月D日」文本；换算失败时降级返回公历文本，
        保证界面上始终有内容显示。

        Args:
            year: 公历年。
            month: 公历月。
            day: 公历日。

        Returns:
            str: 农历日期文本；失败时为对应的公历日期文本。
        """
        try:
            result = self.core.calculate(year, month, day, 12, is_lunar=False)
            return result['lunar_date']
        except Exception as exc:
            logger.warning('[农历转换] 取农历文本失败 %s-%s-%s: %s', year, month, day, exc)
            return f"{year}年{month}月{day}日"
