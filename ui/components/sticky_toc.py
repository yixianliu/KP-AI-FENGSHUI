# -*- coding: utf-8 -*-
"""M3-2 后半：AI 目录条「悬浮吸顶」控制器
========================================
目标（修 Q14）：AI 解读区的章节目录**不随内容滚走**。

形态取舍
--------
AI 解读区位于结果面板滚动内容的**最底部**，因此不能把目录条整体钉在面板顶部——
那会让 AI 目录常驻在「四柱 / 五行」等无关内容之上，UX 更差。
本模块采用 **内联条 + 视口钉住副本** 复合形态（对齐方案 §M3-2 所述
「`self._toc_bar` + 滚动时切换 setVisible 与悬浮吸顶样式」）：

- 内联条仍留在 AI 解读区起始处（章节锚点的自然入口，随内容滚动）；
- 另建同内容的「钉住副本」挂在滚动视口（viewport）上，仅当
  ① AI 解读区仍在视口内、且 ② 内联条已滚出视口顶部 时显示。

生命周期
--------
- 钉住副本的 parent 是 viewport → 由面板在清场时经 `clear_sticky_toc()` 显式回收
  （与既有 `ai_analysis_container` 的清理口径一致）。
- 控制器 parent 是 container → 容器销毁时随之销毁，不产生悬挂引用。
"""

import logging

from PySide6.QtCore import QObject, QEvent, QPoint, QTimer
from PySide6.QtWidgets import QFrame

logger = logging.getLogger(__name__)

# 钉住副本的 objectName（面板清场与测试定位用）
PINNED_OBJECT_NAME = 'ai_toc_bar_pinned'


class StickyTocController(QObject):
    """把目录条的「钉住副本」按滚动位置吸附到滚动视口顶部。

    Args:
        scroll_area: 结果面板的 QScrollArea。
        inline_bar:  AI 解读区内的内联目录条（随内容滚动）。
        pinned_bar:  挂在 viewport 上的钉住副本。
        container:   AI 解读容器（ai_analysis_container），用于判断是否仍在视口内。
        parent:      控制器父对象；默认取 container，随容器销毁而回收。
    """

    def __init__(self, scroll_area, inline_bar, pinned_bar, container, parent=None):
        super().__init__(parent if parent is not None else container)
        self._scroll = scroll_area
        self._vp = scroll_area.viewport() if scroll_area is not None else None
        self._inline = inline_bar
        self._pinned = pinned_bar
        self._container = container
        self._pinned.hide()

        sb = scroll_area.verticalScrollBar() if scroll_area is not None else None
        if sb is not None:
            sb.valueChanged.connect(self._on_scroll)
        if self._vp is not None:
            self._vp.installEventFilter(self)

        self.update()
        # 布局/滚动区尺寸在事件循环下一轮才最终确定，补一次定位
        QTimer.singleShot(0, self._safe_update)

    # ---------------------------------------------------------------- 内部
    def eventFilter(self, obj, event):
        """视口尺寸变化时重算吸附位置（Qt 回调）。"""
        if event.type() == QEvent.Type.Resize and obj is getattr(self, '_vp', None):
            self._safe_update()
        return False

    def _on_scroll(self, _value=0):
        self._safe_update()

    def _safe_update(self):
        """异步回调入口：对象可能正处 Python 侧拆解（属性先于 C++ 对象被清），
        故此处显式容忍 AttributeError；`update()` 自身仍保持严格（只容忍
        C++ 部件已销毁的 RuntimeError），以免掩盖真实属性错误。
        """
        try:
            self.update()
        except (RuntimeError, AttributeError):
            pass

    def update(self):
        """按当前滚动位置决定钉住副本的显隐与几何。"""
        try:
            if self._vp is None or not self._inline.isVisible():
                self._pinned.hide()
                return
            origin = QPoint(0, 0)
            inline_y = self._inline.mapTo(self._vp, origin).y()
            inline_h = self._inline.height()
            c_pt = self._container.mapTo(self._vp, origin)
            c_h = self._container.height()
            vp_h = self._vp.height()

            container_in_view = (c_pt.y() < vp_h) and (c_pt.y() + c_h > 0)
            inline_scrolled_out = (inline_y + inline_h) <= 0
            if container_in_view and inline_scrolled_out:
                self._pinned.setGeometry(c_pt.x(), 0, self._container.width(), inline_h)
                self._pinned.show()
                self._pinned.raise_()
            else:
                self._pinned.hide()
        except RuntimeError:
            # 底层 C++ 部件已随清场销毁（竞态），忽略即可
            pass


def build_pinned_bar(nav_items, active_color, viewport_widget):
    """构建目录条「钉住副本」：parent 设为滚动视口，手动定位（不入布局）。"""
    from ui.components.collapsible_card import ai_section_nav
    bar = ai_section_nav(nav_items, active_color=active_color,
                         object_name=PINNED_OBJECT_NAME)
    bar.setParent(viewport_widget)
    bar.hide()
    return bar


def clear_sticky_toc(scroll_area):
    """移除滚动视口上的全部「钉住目录条」（重复渲染 / 清空前调用，防叠加）。"""
    if scroll_area is None:
        return
    try:
        viewport = scroll_area.viewport()
        for child in viewport.findChildren(QFrame, PINNED_OBJECT_NAME):
            child.setParent(None)
            child.deleteLater()
    except RuntimeError:
        pass
