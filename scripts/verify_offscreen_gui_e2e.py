# -*- coding: utf-8 -*-
"""scripts/verify_offscreen_gui_e2e.py — 离屏 GUI e2e 冒烟验证

验证打包形态下平台插件加载 + MainWindow 构造 + 本轮改动模块实例化。
对应「工程师自主推进」下的离屏 e2e 回归门禁。

用法：
    QT_QPA_PLATFORM=offscreen python scripts/verify_offscreen_gui_e2e.py
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 支持 dist 模式：python scripts/verify_offscreen_gui_e2e.py --dist <dist_dir>
# dist 模式下优先用产物内置的 PySide6 平台插件 + _internal，验证打包后形态。
_dist = None
for i, a in enumerate(sys.argv):
    if a == '--dist' and i + 1 < len(sys.argv):
        _dist = sys.argv[i + 1]

if _dist:
    _dist_path = Path(_dist)
    _internal = _dist_path / '_internal'
    # 产物形态：优先用产物内置的平台插件目录（_internal/PySide6/plugins/platforms），
    # 其次才是源码树自带的 pyside6_packages。
    _p = _internal / 'PySide6' / 'plugins' / 'platforms'
    if _p.is_dir():
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(_p)
    else:
        _plugins = ROOT / 'pyside6_packages' / 'PySide6' / 'plugins' / 'platforms'
        if _plugins.is_dir():
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(_plugins)
    # 把产物 _internal 加入 sys.path（含 PySide6 字节码），但项目模块仍从 ROOT 取
    if _internal.is_dir():
        sys.path.insert(0, str(_internal))
    sys.path.insert(0, str(ROOT))
    print(f'[模式] dist 产物形态: {_dist}')
else:
    _plugins = ROOT / 'pyside6_packages' / 'PySide6' / 'plugins' / 'platforms'
    if _plugins.is_dir():
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(_plugins)
    sys.path.insert(0, str(ROOT))

os.environ.setdefault('KP_HEADLESS', '1')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

PASS: list[str] = []


def ok(name: str, cond: bool, detail: str = '') -> None:
    """断言一条冒烟项，失败即抛异常终止（快速失败）。"""
    if not cond:
        raise AssertionError(f'[FAIL] {name} {detail}')
    PASS.append(name)
    print(f'[PASS] {name}' + (f'  ({detail})' if detail else ''))


def main() -> int:
    # 1) Qt 平台插件加载（offscreen）
    from PySide6.QtWidgets import QApplication, QPushButton
    from PySide6 import QtCore
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle('Fusion')
    ok('offscreen 平台插件加载', QApplication.instance() is not None)

    # 2) 构造 MainWindow
    from ui.main_window import MainWindow, NAV_INDEX, Spacing
    win = MainWindow()
    ok('MainWindow 构造成功', win is not None)

    # 3) 路由单一真相源 + 断点常量（M2-1 / M2-2：原 SIDEBAR_WIDTH 死常量已删除）
    ok('NAV 路由索引完整',
       set(NAV_INDEX) == {'bazi', 'meihua', 'liuren', 'xuan_kong'}
       and NAV_INDEX['xuan_kong'] == 3,
       f'NAV_INDEX={NAV_INDEX}')
    ok('断点常量正确', Spacing.BP_XS == 900 and Spacing.BP_S == 1100 and Spacing.BP_L == 1440,
       f'BP_XS={Spacing.BP_XS} BP_S={Spacing.BP_S} BP_L={Spacing.BP_L}')
    sidebar_btns = [w for w in win.findChildren(QPushButton)]
    nav_labels = [b.text() for b in sidebar_btns]
    # 导航按钮「图标+文字」：实际实现将 Unicode 字形（☯ 等）内嵌进文字，
    # 未走 QIcon 体系，故判据为文字含模块名（修正原错误断言 icon().isNull()）。
    bazi_btn = next((b for b in sidebar_btns if '八字' in b.text()), None)
    ok('导航按钮含「图标+文字」',
       bazi_btn is not None and '八字' in bazi_btn.text()
       and bazi_btn.text().strip().startswith('☯'),
       f'labels={nav_labels[:6]}')

    # 4) 结果面板双路径兜底（问题 5 修复：BaziService 顶层摊平）
    from ui.components.result_panel import ResultPanel
    rp = win.bazi_result if hasattr(win, 'bazi_result') else None
    chart = {
        'year_pillar': '庚午', 'month_pillar': '辛巳',
        'day_pillar': '戊午', 'hour_pillar': '戊午',
        'wuxing_detail': {}, 'shishen': {}, 'mingli': {},
        'dayun': [], 'liunian': [],
    }
    got = ResultPanel.get_chart_data_for_ai(chart) if hasattr(ResultPanel, 'get_chart_data_for_ai') else None
    ok('ResultPanel.get_chart_data_for_ai 可调用', got is not None)

    # 5) 本轮新增/改动模块可导入 + 实例化
    import importlib
    for mod in ('ui.components.collapsible_card',
                'ui.components.ai_analysis_renderer',
                'ui.components.timeline',
                'ui.export.ai_titles',
                'service.bazi_service',
                'core.knowledge.analysis_fallback'):
        m = importlib.import_module(mod)
        ok(f'import {mod}', m is not None)

    # 6) hero_conclusion_block 渲染（结论可读性优化 + 黑字）
    from ui.components.collapsible_card import hero_conclusion_block
    from PySide6.QtWidgets import QVBoxLayout
    container = QPushButton()
    lay = QVBoxLayout(container)
    blk = hero_conclusion_block('【核心论断】身强用财，事业顺遂。多穿红色可增强火运。', color='#C9A046')
    ok('hero_conclusion_block 渲染', blk is not None)

    print('\n' + '=' * 56)
    print(f'[完成] 离屏 GUI e2e 冒烟全部通过：{len(PASS)} 项')
    print('=' * 56)
    return 0


if __name__ == '__main__':
    sys.exit(main())
