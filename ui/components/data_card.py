# -*- coding: utf-8 -*-
"""
ui/components/data_card.py — 数值卡片组件

UI 升级方案 M5 / 4.2：展示「指标 + 数值 + 单位 + 可选徽章 + 可选迷你趋势」
的紧凑数据卡片，供各结果面板的统计/指标区复用。
"""
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

from ui.styles import Colors, Fonts, Spacing


class DataCard(QFrame):
    """数值卡片：标题 + 大数值 + 单位 + 可选徽章/迷你趋势。

    用法：
        DataCard(title='命中率', value='92.5', unit='%',
                 badge='优', badge_semantic='success', parent=self)

    Args:
        title:    指标名称（caption 级灰阶）。
        value:    主数值（等宽大字，品牌金色）。
        unit:     单位（小字，紧跟数值）。
        badge:    可选状态徽章文字（如 '优'/'警'）。
        badge_semantic: 徽章语义色键（success/danger/warning/info/brand/accent）。
        color:    数值强调色，None 取 Colors.BRAND。
    """

    def __init__(self, title: str = '', value: str = '', unit: str = '',
                 badge: str = '', badge_semantic: str = 'info',
                 color: str = None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS};
            }}
            QFrame:hover {{
                border-color: {Colors.BRAND_LIGHT};
                background: {Colors.CARD_HOVER};
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(Spacing.S5, Spacing.S4, Spacing.S5, Spacing.S4)
        lay.setSpacing(Spacing.S1)

        # 标题行：标题 + 徽章（右对齐）
        head = QHBoxLayout()
        head.setSpacing(Spacing.S1)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(
            f"font-size: {Fonts.FS_CAPTION}px; color: {Colors.TEXT3}; "
            f"font-family: {Fonts.BODY};")
        head.addWidget(t_lbl)
        head.addStretch(1)
        if badge:
            from ui.components.badge import Badge
            b = Badge(badge, semantic=badge_semantic)
            head.addWidget(b)
        lay.addLayout(head)

        # 数值行：大数值 + 单位
        val_row = QHBoxLayout()
        val_row.setSpacing(Spacing.S1)
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(
            f"font-size: {Fonts.FS_HERO}px; font-weight: {Fonts.W_BOLD_NUM}; "
            f"color: {color or Colors.BRAND}; font-family: {Fonts.MONO};")
        val_row.addWidget(val_lbl)
        if unit:
            u_lbl = QLabel(unit)
            u_lbl.setStyleSheet(
                f"font-size: {Fonts.FS_CAPTION}px; color: {Colors.TEXT3}; "
                f"font-family: {Fonts.BODY};")
            u_lbl.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
            val_row.addWidget(u_lbl, 0, Qt.AlignBottom)
        val_row.addStretch(1)
        lay.addLayout(val_row)

    def set_value(self, value: str, unit: str = ''):
        """动态更新数值与单位。"""
        labels = self.findChildren(QLabel)
        for lbl in labels:
            if lbl.objectName() == 'dc_value':
                lbl.setText(value)
                break
