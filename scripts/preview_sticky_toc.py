# -*- coding: utf-8 -*-
"""M3-2 后半 设计预览：AI 目录条悬浮吸顶（设计签核用，非断言门禁）
================================================================
用**真实面板** `ResultPanel` + `render_analysis` 渲染一份八字 AI 解读，
分别截取两种状态：
  - `sticky_toc_before.png`  —— 顶部：内联目录条在视野中，无悬浮条
  - `sticky_toc_pinned.png`  —— 下滚后：目录条已吸顶，AI 正文从其下滚动

用法：
    QT_QPA_PLATFORM=offscreen ./venv/Scripts/python.exe scripts/preview_sticky_toc.py
产物：build/screenshots/{sticky_toc_before,sticky_toc_pinned}.png
"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QPoint, QEvent
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QFrame

from ui.components.result_panel import ResultPanel
from ui.components.ai_analysis_renderer import render_analysis

_CJK_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
)


def _install_cjk_font(app):
    """离屏 QPA 字体库为空 → 注入系统 CJK 字体，否则中文全是豆腐块。"""
    family = "Microsoft YaHei"
    for path in _CJK_FONT_CANDIDATES:
        if not os.path.exists(path):
            continue
        fid = QFontDatabase.addApplicationFont(path)
        names = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
        if names:
            family = names[0]
            print(f"[font] loaded {path} -> {names[:2]}")
            break
    app.setFont(QFont(family, 10))


def _payload():
    return {
        'key_points': ['印星护身，贵人相助', '宜稳中求进，忌急功近利'],
        'final_verdict': '整体格局中上：印星护身而财官得用，适合走稳中求进的路线，'
                         '以柔克刚、借力打力，则中年后渐入佳境。',
        'personality': ['聪颖好学，重情重义', '做事有始有终，认准便不回头',
                        '偶有优柔寡断，需果断决断'],
        'career': ['事业呈稳步上升之势，2026 年有贵人提携', '适合文教、咨询、策划方向',
                   '忌多头并进，宜专精一门'],
        'relationships': ['感情需主动经营，勿待对方先开口', '相处忌急进，宜细水长流'],
        'health': ['注意脾胃与作息规律', '少熬夜、忌生冷，四季调养为宜'],
        'study_exam': '学业考试运佳，文昌得地，宜进修考证、以考促学。',
        'annual_fortune': ['2026 丙午：事业有机遇，同时留意口舌是非',
                           '2027 丁未：财星入库，适合稳健理财'],
        'scenario_advice': ['宜早做三年规划，按部就班推进',
                            '忌盲目投资与轻信他人许诺'],
        'disclaimer': '',
    }


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    _install_cjk_font(app)

    panel = ResultPanel()
    panel.resize(920, 760)
    panel.show()
    for _ in range(4):
        app.processEvents()

    panel._clear_content()                      # 移除空状态，画面更干净
    # deleteLater 是延迟删除，需显式派发 DeferredDelete，否则空状态残留浮在画面上
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    for _ in range(3):
        app.processEvents()
    render_analysis('bazi', _payload(), panel.clay, scroll_area=panel.scroll)
    for _ in range(5):
        app.processEvents()

    shot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'build', 'screenshots')
    os.makedirs(shot_dir, exist_ok=True)

    def _grab(name):
        for _ in range(3):
            app.processEvents()
        path = os.path.join(shot_dir, name)
        ok = panel.grab().save(path)
        img = panel.grab().toImage()
        print(f"saved={ok} path={path} size={img.width()}x{img.height()}")

    # ① 顶部：内联目录条可见，无悬浮副本
    panel.scroll.verticalScrollBar().setValue(0)
    _grab('sticky_toc_before.png')

    # ② 下滚到「内联条刚滚出视口顶部」处 → 悬浮副本应吸顶
    inline = panel.scroll.viewport().findChild(QFrame, 'ai_toc_bar')
    if inline is not None:
        top = inline.mapTo(panel.content, QPoint(0, 0)).y()
        panel.scroll.verticalScrollBar().setValue(top + inline.height() + 40)
    else:
        print('[warn] 未找到内联目录条 ai_toc_bar')
    _grab('sticky_toc_pinned.png')

    pinned = panel.scroll.viewport().findChild(QFrame, 'ai_toc_bar_pinned')
    print(f"[check] 悬浮副本存在={pinned is not None} "
          f"可见={pinned.isVisible() if pinned else False}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
