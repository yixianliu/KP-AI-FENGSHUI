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
        return {}


# Aliases at module level for convenience
TIAN_GAN = _TG
DI_ZHI = _DZ
BaZiCalculator = _CoreBaZiCalc
