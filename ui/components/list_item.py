# -*- coding: utf-8 -*-
"""
ui/components/list_item.py — 统一列表项组件

UI 升级方案 M4 / 步骤 4.1：所有"列表项"（大运柱、流年柱、星宿、六爻、
章节项、十二天将、宫位详情等）共享同一视觉语言。

结构：图标(可选) + 主标题 + 副标题 + 右侧数值/状态徽章。
支持状态：default / hover / active / disabled。
"""
import re

from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

from ui.styles import Colors, Fonts, Spacing

# 列表项 QSS（按 property("state") 区分四态）
LIST_ITEM_QSS = f"""
    QFrame[state="default"]  {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: {Spacing.RADIUS_SM};
    }}
    QFrame[state="hover"]    {{
        background: {Colors.HOVER};
        border: 1px solid {Colors.BORDER};
    }}
    QFrame[state="active"]   {{
        background: {Colors.CARD_HOVER};
        border: 1px solid {Colors.BORDER};
        border-left: 3px solid {Colors.BRAND};
    }}
    QFrame[state="disabled"] {{
        background: transparent;
        border: 1px solid transparent;
        color: {Colors.TEXT4};
    }}
"""

# 四态集合；未知状态一律回落 default，避免写出 QSS 里不存在的分支
STATES = ('default', 'hover', 'active', 'disabled')


class ListItem(QFrame):
    """统一列表项：图标 + 主标题 + 副标题 + 右侧数值/状态徽章。

    用法：
        item = ListItem(title='甲子', subtitle='大运', value='1990-1999', icon='☘')
        item.clicked.connect(on_click)

    Args:
        icon:       左侧图标字符（emoji / 卦符 / SVG 名占位），空串不显示。
        title:      主标题（15px DemiBold）。
        subtitle:   副标题（12px muted），可空。
        value:      右侧数值/状态（13px 金色），可空。
        badge_color: value 颜色，None 取 Colors.BRAND。
    """

    clicked = Signal()

    def __init__(self, icon: str = '', title: str = '', subtitle: str = '',
                 value: str = '', badge_color: str = None, parent=None):
        super().__init__(parent)
        self.setProperty('state', 'default')
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(LIST_ITEM_QSS)

        # 子 label 与其原始样式，供 disabled 态统一压色 / 还原
        self._child_labels = []
        # 鼠标进入前的状态：离开时还原用它（见 enterEvent/leaveEvent）
        self._enter_base_state = 'default'

        lay = QHBoxLayout(self)
        lay.setContentsMargins(Spacing.S3, Spacing.S2, Spacing.S3, Spacing.S2)
        lay.setSpacing(Spacing.S3)

        def _register(lbl, ss, container, stretch=0):
            """建样式 + 登记，便于 disabled 态改色 / 还原。

            每个子 label 都必须带 `background: transparent`——Qt 的一个实测坑：
            子 QLabel 若不显式声明透明背景，会盖住父 QFrame 的 QSS 背景，
            导致下面 LIST_ITEM_QSS 的四态背景**全部静默失效**（整份 QSS 等于没写）。
            """
            if 'background' not in ss:
                ss = ss.rstrip() + ' background: transparent;'
            lbl.setStyleSheet(ss)
            self._child_labels.append((lbl, ss))
            container.addWidget(lbl, stretch) if stretch else container.addWidget(lbl)

        # 左侧图标
        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setFixedSize(24, 24)
            icon_lbl.setAlignment(Qt.AlignCenter)
            _register(icon_lbl,
                      f"font-size: 15px; color: {Colors.BRAND};", lay)

        # 中部：主标题 + 副标题
        mid = QVBoxLayout()
        mid.setSpacing(Spacing.S1)
        _register(QLabel(title),
                  f"font-size: {Fonts.FS_H3}px; font-weight: {Fonts.W_SEMIBOLD}; "
                  f"color: {Colors.TEXT}; font-family: {Fonts.TITLE};", mid)
        if subtitle:
            _register(QLabel(subtitle),
                      f"font-size: {Fonts.FS_CAPTION}px; color: {Colors.TEXT3}; "
                      f"font-family: {Fonts.BODY};", mid)
        lay.addLayout(mid, 1)

        # 右侧数值 / 徽章
        if value:
            _register(QLabel(value),
                      f"font-size: {Fonts.FS_BODY}px; font-weight: {Fonts.W_MEDIUM}; "
                      f"color: {badge_color or Colors.BRAND}; "
                      f"font-family: {Fonts.MONO};", lay)

    def set_state(self, state: str):
        """切换列表项状态（default/hover/active/disabled），触发重绘。

        Qt 的 dynamic property 变更后必须 unset/set 配合 style() 刷新，
        否则 QSS 的 [state=...] 选择器不会即时生效。

        disabled 态额外做两件事（原实现都缺，导致「禁用」形同虚设）：
        ① setEnabled(False)——真正禁止点击与焦点，否则 clicked 照旧发出；
        ② 把子 label 文字压到 TEXT4——QFrame 上的 `color:` 会被子 label 内联
           声明覆盖，只改外框等于什么都没改。
        """
        state = state if state in STATES else 'default'
        self.setProperty('state', state)
        self.style().unpolish(self)
        self.style().polish(self)
        if state == 'disabled':
            self.setEnabled(False)
            self._set_children_dimmed(True)
        else:
            self.setEnabled(True)
            self._set_children_dimmed(False)
        self.update()

    def _set_children_dimmed(self, dim: bool):
        """禁用态把子文字统一压到 TEXT4；否则还原各自原色。

        只替换每个样式里第一个 `color:` 声明——本子组件生成的样式恰好各含一条。
        """
        for lbl, base in self._child_labels:
            if not dim:
                lbl.setStyleSheet(base)
                continue
            css = base
            m = re.search(r'color:\s*([^;]+);', css)
            if m:
                css = css[:m.start(1)] + Colors.TEXT4 + css[m.end(1):]
            else:
                css = css.rstrip('}') + f' color: {Colors.TEXT4};'
            lbl.setStyleSheet(css)

    # Qt 事件：进入/离开自动切 hover 态
    def enterEvent(self, event):
        """进入记基础态、显示 hover；leave 时还原基础态。

        原实现进入写死 'active'、离开写死 'default'，有两个后果：
        ① 程序化 `set_state('active')`（表示固定选中/高亮）会在鼠标路过的
           同一秒内被抹平，该 API 实际不可用；
        ② QSS 里的 'hover' 分支从未被任何代码赋值，是死分支，而 hover 时
           直接上最重的 'active'（金色左边框）反馈过重。
        现改为进入置 'hover'，离开还原进入前的基础态。
        """
        self._enter_base_state = self.property('state')
        if self._enter_base_state != 'disabled':
            self.set_state('hover')
        super().enterEvent(event)

    def leaveEvent(self, event):
        base = self._enter_base_state
        if base != 'disabled':
            self.set_state(base)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
