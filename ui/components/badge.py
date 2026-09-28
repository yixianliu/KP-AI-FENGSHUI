# -*- coding: utf-8 -*-
"""
ui/components/badge.py — 状态徽章组件

UI 升级方案 M4 / 步骤 4.3：语义色小标签（吉 / 凶 / 中 / 吉星 / 凶星 等）。
统一视觉语言：药丸圆角 + 语义色背景 + 自动前景色对比。
"""
from PySide6.QtWidgets import QLabel

from ui.styles import Colors, Fonts, Spacing

# 语义色映射（badge 可用 semantic 取值）
# 注意：danger 刻意用 Colors.DANGER_DARK（#A03E32）而非 SEMANTIC_DANGER（#C45545）——
# 徽章文字仅 FS_MICRO 11px，属 WCAG 小字，需 ≥4.5:1。#C45545 配浅字仅 3.94:1
# 不达 AA；DANGER_DARK 配浅字 8.89→5.80:1 达标。该令牌本就是为「危险深底 +
# 浅字对比度」而新增（见 styles.py DANGER_DARK 注释），语义完全一致。
_BADGE_COLORS = {
    'success': Colors.SEMANTIC_SUCCESS,
    'danger': Colors.DANGER_DARK,
    'warning': Colors.SEMANTIC_WARNING,
    'info': Colors.SEMANTIC_INFO,
    'brand': Colors.BRAND,
    'accent': Colors.ACCENT,
}


def _contrast_fg(hex_color: str) -> str:
    """按背景色感知亮度自动选前景色，保证徽章文字始终可读。

    根因（长期 bug）：原实现只在 brand/accent 用 TEXT_INV，其余语义色
    （success/danger/warning/info）的前景色直接取背景色 c——文字与背景同色，
    对比度 1:1，**文字完全不可见**。
    修正：按感知亮度（ITU-R BT.709 权重）判断，亮底（>0.5）配深字 TEXT_INV，
    暗底配浅字 TEXT。各语义色的正确前景：
        SEMANTIC_SUCCESS #5DAF74 lum=0.63 → TEXT_INV
        SEMANTIC_WARNING #D8A94E lum=0.73 → TEXT_INV
        SEMANTIC_INFO    #7FB3C8 lum=0.71 → TEXT_INV
        SEMANTIC_DANGER  #C45545 lum=0.42 → TEXT
        BRAND #c9a227    lum=0.61 → TEXT_INV
        ACCENT #8b0000   lum=0.12 → TEXT（原配 TEXT_INV 仅 1.5:1，也不达标）
    """
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    return Colors.TEXT_INV if lum > 0.5 else Colors.TEXT


class Badge(QLabel):
    """状态徽章：吉 / 凶 / 中 / 吉星 / 凶星 等语义色小标签。

    用法：
        Badge('吉', semantic='success')
        Badge('凶', semantic='danger')
        Badge('平', semantic='info')

    Args:
        text: 徽章文字。
        semantic: 语义色键，取值 success/danger/warning/info/brand/accent，
                  默认 'info'。
    """

    def __init__(self, text: str, semantic: str = 'info', parent=None):
        super().__init__(parent)
        c = _BADGE_COLORS.get(semantic, Colors.SEMANTIC_INFO)
        fg = _contrast_fg(c)  # 前景色由背景亮度决定，不再按 semantic 硬编码
        self.setText(f" {text} ")
        self.setStyleSheet(f"""
            QLabel {{
                color: {fg};
                background: {c};
                border-radius: {Spacing.RADIUS_PILL}px;
                padding: 2px 8px;
                font-size: {Fonts.FS_MICRO}px;
                font-weight: {Fonts.W_SEMIBOLD};
                font-family: {Fonts.BODY};
            }}
        """)
        self.setFixedHeight(18)

    def set_text(self, text: str):
        """更新徽章文字（保留样式）。"""
        self.setText(f" {text} ")
