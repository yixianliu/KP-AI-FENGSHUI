#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
_ROOT = str(Path(__file__).resolve().parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
_VENDOR = os.path.join(_ROOT, 'build', 'vendor_libs')
if os.path.isdir(_VENDOR) and _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from ui.components.result_panel import ResultPanel

app = QApplication.instance() or QApplication(sys.argv)

# 构造一个最小的 bazi 结果，包含 result_panel 需要的所有顶层键
result = {
    'type': 'bazi',
    'bazi': {
        'year': '甲子',
        'month': '丙子',
        'day': '戊寅',
        'hour': '庚辰'
    },
    'year_pillar': '甲子',
    'month_pillar': '丙子',
    'day_pillar': '戊寅',
    'hour_pillar': '庚辰',
    'rizhu': '戊寅',
    'month_zhi': '子',
    'hour_zhi': '辰',
    'wuxing': {'木':3, '火':2, '土':2, '金':2, '水':1},
    'wuxing_detail': {},
    'analysis': [{'type': '吉'}],
    'yuncheng': {'career': '好'},
    'shier_shen': {'shier_shen': []},
    'bazi_types': {},
    'mingli': {},
    'yunshi': {},
    'ai_analysis': {}
}

panel = ResultPanel()
panel.display_result(result)
print("SUCCESS: display_result did not crash")
print(f"Panel visible: {panel.isVisible()}")
app.quit()