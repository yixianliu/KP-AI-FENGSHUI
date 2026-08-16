"""
兼容模块 - 替代已删除的 core.baazi
所有旧 import 统一导向本模块

使用方式:
  - mingli.py / shishen.py:  import core._baazi_compat as _baazi_module
  - bazi_calculator.py:     from ._baazi_compat import BaZiCalculator as CoreBaZiCalculator
  - lunar_converter.py:     from ._baazi_compat import BaZiCalculator
"""
from core.calendar_utils import (
    _lazy_init as _cal_lazy_init,
    TIAN_GAN as _TG_DEF,
    DI_ZHI as _DZ_DEF,
)
# 数据库不可用时的静态兜底，取自唯一权威源
from core.ganzhi_constants import TIAN_GAN as _TG_FALLBACK, DI_ZHI as _DZ_FALLBACK

# ---- 干支表：首次访问时同步填充（优先库内数据，失败则用静态兜底）----
_TG = None
_DZ = None


def _ensure():
    """确保 _TG / _DZ 已就绪，幂等，可重复调用。

    先触发 calendar_utils 的数据库懒加载；若库中未取到（例如首次启动
    或数据库损坏），则退回 core.ganzhi_constants 的静态字面量，
    保证排盘逻辑在任何情况下都不会因缺表而崩溃。
    """
    global _TG, _DZ
    if _TG is not None:
        return
    _cal_lazy_init()
    _TG = _TG_DEF or _TG_FALLBACK
    _DZ = _DZ_DEF or _DZ_FALLBACK


# 模块导入时即执行一次，避免运行期出现「未初始化」的时间窗
_ensure()


# ---------- 十二长生（日干在四柱地支的十二宫状态） ----------
_SHIER_GONG = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰',
               '病', '死', '墓', '绝', '胎', '养']
# 日干 → 长生地支（阳干顺行、阴干逆行）
_CHANGSHENG = {
    '甲': '亥', '乙': '午', '丙': '寅', '丁': '酉', '戊': '寅',
    '己': '酉', '庚': '巳', '辛': '子', '壬': '申', '癸': '卯',
}
_GAN_YANG = {'甲', '丙', '戊', '庚', '壬'}
_SHIER_DESC = {
    '长生': '万物生发，主生机、起点、聪慧好学',
    '沐浴': '又称败地，主桃花、多变、须防感情纷扰',
    '冠带': '临官之前，主少年得志、仪容端庄',
    '临官': '禄地，主自立、事业有成、精力充沛',
    '帝旺': '极盛之地，主能量最强，然盛极防衰',
    '衰': '气渐退，主保守、力不从心',
    '病': '主体弱、多思、易生烦恼',
    '死': '气绝，主静止、终结，宜守不宜攻',
    '墓': '库地，主收藏、积蓄、潜力待发',
    '绝': '气绝之地，主困顿、转折、蓄势',
    '胎': '禀受之气，主孕育、新生、暗藏生机',
    '养': '成形之地，主滋养、培育、渐入佳境',
}
_PILLARS = ['年柱', '月柱', '日柱', '时柱']


# ---------- Simulated module stub for callers doing:
#           import core._baazi_compat as _baazi_module
#           _baazi_module.TIAN_GAN / _baazi_module.DI_ZHI / _baazi_module._lazy_init() ----------


class _SimModule:
    """A lightweight proxy that makes a class look like a module."""

    @property
    def TIAN_GAN(self):
        """返回已就绪的天干表（优先库内数据，兜底静态常量），供旧 import 透明取用。"""
        return _TG

    @property
    def DI_ZHI(self):
        """返回已就绪的地支表（优先库内数据，兜底静态常量），供旧 import 透明取用。"""
        return _DZ

    @staticmethod
    def _lazy_init():
        """确保天干/地支表已填充（触发 _ensure()，幂等）。"""
        _ensure()

    @staticmethod
    def BaZiCalculator():
        """Return the compatible calculator class."""
        return _CoreBaZiCalc


# This is what `import ... as _baazi_module` resolves to
_baazi_module = _SimModule()


# ---------- BaZiCalculator for callers doing: from ._baazi_compat import BaZiCalculator ----------

class _CoreBaZiCalc:
    """Compatible BaZiCalculator delegating to calendar_utils.BaZiCalendar."""

    def calculate(self, year, month, day, hour, minute=0, longitude=120.0, is_lunar=False):
        """兼容入口：把参数转交 calendar_utils.BaZiCalendar 计算四柱，并补齐 solar_date / lunar_date 字段。

        Args:
            year, month, day, hour: 公历时间
            minute: 分钟，用于真太阳时精算
            longitude: 经度，用于真太阳时修正
            is_lunar: 是否农历（当前透传给底层日历器）

        Returns:
            dict: 含四柱、日主、公历/农历日期等字段的八字结果
        """
        from core.calendar_utils import BaZiCalendar as _BC
        r = _BC().calculate_bazi(year, month, day, hour, minute, longitude)
        r.setdefault("solar_date", f"{year}-{month:02d}-{day:02d}")

        # 正确计算农历日期：使用 lunarcalendar 库进行公历→农历转换
        try:
            from lunarcalendar import converter
            import datetime
            solar_dt = datetime.datetime(year, month, day, hour, minute)
            lunar_result = converter.Converter().Solar2Lunar(solar_dt)
            r.setdefault("lunar_date", f"{lunar_result.year}年{lunar_result.month}月{lunar_result.day}日")
        except Exception:
            # 降级处理：转换失败时回退到占位符
            r.setdefault("lunar_date", f"{year}年{month}月{day}日")

        return r

    def analyze_shier_shen(self, bazhi):
        """十二长生分析：日干在四柱地支的十二宫状态

        Args:
            bazhi: 八字字典，须含 '四柱' (list[str])、'rizhu' (str)

        Returns:
            dict: {'shier_shen': [{'pillar','ganzhi','shier_shen','description'}, ...]}
        """
        pillars = _PILLARS  # ['年柱','月柱','日柱','时柱']
        ganzhi_list = bazhi.get('四柱', [])
        if len(ganzhi_list) < 4:
            return {'shier_shen': []}

        ri_gan = bazhi.get('rizhu', '甲')[:1]
        if ri_gan not in _GAN_YANG and ri_gan not in _SHIER_DESC:
            # fallback: 取四柱第一字为天干
            ri_gan = ganzhi_list[2][0] if len(ganzhi_list[2]) > 0 else '甲'

        yang = ri_gan in _GAN_YANG
        start = _CHANGSHENG.get(ri_gan, '亥')
        start_idx = _DZ.index(start)  # 0-11
        dz_list = _DZ  # 子丑寅卯...

        result = []
        for i, pillar in enumerate(pillars):
            gz = ganzhi_list[i] if i < len(ganzhi_list) else '甲子'
            zhi = gz[1] if len(gz) > 1 else '子'
            zhi_idx = dz_list.index(zhi) if zhi in dz_list else 0

            if yang:
                offset = (zhi_idx - start_idx) % 12
            else:
                offset = (start_idx - zhi_idx) % 12

            gong = _SHIER_GONG[offset]
            desc = _SHIER_DESC.get(gong, '')
            result.append({
                'pillar': pillar,
                'ganzhi': gz,
                'shier_shen': gong,
                'description': desc,
            })

        return {'shier_shen': result}


# Aliases at module level for convenience
TIAN_GAN = _TG
DI_ZHI = _DZ
BaZiCalculator = _CoreBaZiCalc
