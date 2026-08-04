"""
可折叠卡片（共享组件）
========================
三套右侧结果面板（八字 / 梅花易数 / 大六壬）统一复用此组件，保证
视觉一致：左侧强调色条 + 图标 + 标题 + 内容区。点击标题栏可折叠/展开
（带高度动画）。

配色约定（视觉层次）：
  - 排盘类卡片：青色条 (Colors.QINGHUA)
  - AI 解读类卡片：鎏金色条 (Colors.LIUJIN)
强调色由调用方通过 accent_color 传入，便于语义化区分。
"""
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from ui.styles import Colors, Fonts, Spacing


class CollapsibleCard(QFrame):
    """可折叠卡片组件 - 点击标题栏展开/折叠内容区（带高度动画）。"""

    def __init__(self, title: str, icon: str = '', parent=None,
                 accent_color=None, collapsed: bool = False):
        super().__init__(parent)
        self._collapsed = collapsed
        self._accent_color = accent_color or Colors.QINGHUA
        self._content_widget = None

        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS};
            }}
            QFrame:hover {{
                border-color: {self._accent_color};
            }}
        """)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # 标题栏（可点击）
        self._header = QFrame()
        self._header.setCursor(Qt.PointingHandCursor)
        self._header.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: none;
                border-radius: {Spacing.RADIUS};
            }}
            QFrame:hover {{
                background: {Colors.CARD_HOVER};
            }}
        """)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(10)

        # 折叠/展开图标
        self._collapse_icon = QLabel('▼' if not collapsed else '▶')
        self._collapse_icon.setStyleSheet(f"""
            font-size: 10px;
            color: {Colors.TEXT3};
            min-width: 12px;
        """)
        self._collapse_icon.setAlignment(Qt.AlignCenter)

        # 左侧强调色条（视觉层次标识：排盘=青 / AI=金）
        self._accent_bar = QFrame()
        self._accent_bar.setFixedSize(4, 20)
        self._accent_bar.setStyleSheet(f"background: {self._accent_color}; border-radius: 2px;")

        # 图标
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 16px; color: {self._accent_color};")
        icon_label.setFixedWidth(24)

        # 标题（五号字阶梯：SECTION 级）
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT};
            font-family: {Fonts.BODY};
        """)

        header_layout.addWidget(self._collapse_icon)
        header_layout.addWidget(self._accent_bar)
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self._main_layout.addWidget(self._header)

        # 内容容器
        self._content_container = QWidget()
        self._content_container.setStyleSheet("background: transparent; border: none;")
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(16, 0, 16, 14)
        self._content_layout.setSpacing(0)
        self._main_layout.addWidget(self._content_container)

        # 标题栏点击事件
        self._header.mousePressEvent = self._on_header_click

        if collapsed:
            self._content_container.setVisible(False)

    def set_content(self, widget: QWidget):
        """设置卡片内容（首次/更新均安全）。"""
        if self._content_widget:
            self._content_layout.removeWidget(self._content_widget)
            self._content_widget.deleteLater()
        self._content_widget = widget
        # 内容顶部加一条分割线，强化标题与内容的层次
        if self._content_layout.count() == 0:
            div = QFrame()
            div.setFixedHeight(1)
            div.setStyleSheet(f"background-color: {Colors.DIVIDER}; margin-bottom: 12px;")
            self._content_layout.addWidget(div)
        self._content_layout.addWidget(widget)

    def _on_header_click(self, event):
        self.toggle_collapsed()

    def toggle_collapsed(self):
        """点击标题栏展开/折叠内容区（带高度动画，增强交互反馈）。"""
        self._collapsed = not self._collapsed
        self._collapse_icon.setText('▶' if self._collapsed else '▼')
        content = self._content_container
        if self._collapsed:
            self._animate_collapse(content.height(), 0, hide=True)
        else:
            content.setVisible(True)
            content.setMaximumHeight(0)
            self._animate_collapse(0, content.sizeHint().height(), hide=False)

    def _animate_collapse(self, start: int, end: int, hide: bool):
        content = self._content_container
        anim = QPropertyAnimation(content, b"maximumHeight")
        anim.setDuration(260)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(start)
        anim.setEndValue(end)
        if hide:
            anim.finished.connect(lambda: content.setVisible(False))
        else:
            anim.finished.connect(lambda: content.setMaximumHeight(16777215))
        anim.start()

    def is_collapsed(self) -> bool:
        return self._collapsed


def ai_section_header(title: str = '龙虎山大师兄智能深度解读', icon: str = '🧙') -> QWidget:
    """金色渐变分隔条 + 鎏金色标题，用于在各面板中分隔『龙虎山大师兄解读区』，与八字面板视觉一致。

    返回可直接 addWidget 的 QWidget（自身无外边距，由父布局控制间距）。
    """
    container = QWidget()
    v = QVBoxLayout(container)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(0)

    # 金色渐变分隔线（中亮两端透明）
    divider = QFrame()
    divider.setFixedHeight(2)
    divider.setStyleSheet(
        f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        f"stop:0 transparent, stop:0.5 {Colors.LIUJIN}, stop:1 transparent); "
        f"border: none; margin: 18px 0 10px 0;"
    )
    v.addWidget(divider)

    h = QHBoxLayout()
    h.setContentsMargins(0, 0, 0, 4)
    h.setSpacing(8)
    icon_label = QLabel(icon)
    icon_label.setStyleSheet(f"font-size: 18px; color: {Colors.LIUJIN};")
    title_label = QLabel(title)
    title_label.setStyleSheet(
        f"font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD}; "
        f"color: {Colors.LIUJIN}; font-family: {Fonts.TITLE};"
    )
    h.addWidget(icon_label)
    h.addWidget(title_label)
    h.addStretch()
    v.addLayout(h)
    return container
