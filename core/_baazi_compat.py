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

# ---- populate lazily but synchronously at first access ----
_TG = None
_DZ = None


def _ensure():
    global _TG, _DZ
    if _TG is not None:
        return
    _cal_lazy_init()
    _TG = _TG_DEF or ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
    _DZ = _DZ_DEF or ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]


# Initial call — eager to avoid runtime gaps
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
        return _TG

    @property
    def DI_ZHI(self):
        return _DZ

    @staticmethod
    def _lazy_init():
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
        from core.calendar_utils import BaZiCalendar as _BC
        r = _BC().calculate_bazi(year, month, day, hour, minute, longitude)
        r.setdefault("solar_date", f"{year}-{month:02d}-{day:02d}")
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
