"""
可折叠卡片（共享组件）v2.1 - 概率统计/关键词高亮增强版
========================
三套右侧结果面板（八字 / 梅花易数 / 大六壬）统一复用此组件，保证
视觉一致：左侧强调色条 + 图标 + 标题 + 内容区。

配色约定（视觉层次）：
  - 排盘类卡片：青色条 (Colors.QINGHUA)
  - AI 解读类卡片：鎏金色条 (Colors.LIUJIN)
强调色由调用方通过 accent_color 传入，便于语义化区分。

注：卡片默认展开；v6.0 起恢复折叠交互（点击标题栏可收起/展开，带高度
动画与 ▼/▶ 箭头指示），配合面板顶部「全部收起/展开」按钮使用，
避免用户错以为内容「消失」。

新增 v2.1：
- 概率统计：智能分组、多格式解析、阈值色标、排序、增强工具提示
- 关键词高亮：正/负面情感词内联高亮、情感标签、可视化情感评分

新增 v6.0（本次）：
- CollapsibleCard 折叠动画回归（QPropertyAnimation 高度过渡）
- TaijiSpinner：旋转太极加载动画控件（三面板复用）
- loading_panel：居中加载面板（旋转太极 + 主文案 + 轮播提示语）
- ResponsiveFlow：响应式流式网格（随宽度自动换列，适配窄屏）
- set_all_cards_collapsed：批量折叠/展开布局内全部卡片
"""
import re
import logging
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
                               QGraphicsOpacityEffect, QButtonGroup,
                               QPushButton, QScrollArea, QGridLayout, QSizePolicy,
                               QGraphicsDropShadowEffect)
from PySide6.QtCore import (Qt, QEvent, QPropertyAnimation, QEasingCurve, QTimer,
                            Signal, Property, QObject)
from PySide6.QtGui import QFont, QCursor
from ui.styles import Colors, Fonts, Spacing
from ui.components.typography import TLabel  # M3-3：分区标题/副标题/时间戳走 TLabel 工厂

# 模块级 logger：便于排查 _strength_verdict 文案是否按预期产出
logger = logging.getLogger(__name__)


class _ClickableHeader(QFrame):
    """可点击的卡片标题栏：点击发出 clicked 信号（用于折叠/展开）。"""

    clicked = Signal()

    def mousePressEvent(self, event):  # noqa: N802（Qt 命名）
        """左键点击标题栏即触发折叠/展开。"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class CollapsibleCard(QFrame):
    """结果显示卡片 - 支持折叠/展开（默认展开）。

    点击标题栏可收起/展开内容区（高度过渡动画 + ▼/▶ 箭头指示），
    也可通过 set_collapsed() / toggle() 程序化控制。
    M3-5：支持折叠态记忆（persist_key，进程内持久化用户折叠偏好）。
    """

    # M3-5：折叠态记忆字典（进程内有效，键 -> 是否折叠）
    _COLLAPSE_STATE: dict[str, bool] = {}

    def __init__(self, title: str, icon: str = '', parent=None,
                 accent_color=None, collapsed: bool = False,
                 persist_key: str = ''):
        """
        构建卡片骨架：标题栏（强调色条 + 图标 + 标题 + 折叠箭头）与内容容器。

        Args:
            title:        卡片标题文字。
            icon:         标题左侧图标字符（emoji 或卦符），空串表示不显示。
            parent:       Qt 父控件。
            accent_color: 左侧强调色条颜色；None 时取青色 Colors.QINGHUA。
                          约定排盘类卡片用青色、AI 解读类卡片用鎏金 Colors.LIUJIN。
            collapsed:    初始是否折叠，默认 False（展开）。
            persist_key:  折叠态记忆键（M3-5），非空时读取/写入进程内折叠偏好。
        """
        super().__init__(parent)
        self._persist_key = persist_key
        # 读取记忆：persist_key 命中则覆盖默认 collapsed
        if self._persist_key and self._persist_key in self._COLLAPSE_STATE:
            self._collapsed = self._COLLAPSE_STATE[self._persist_key]
        else:
            self._collapsed = bool(collapsed)
        self._accent_color = accent_color or Colors.QINGHUA
        self._content_widget = None
        self._collapse_anim = None  # 保持动画引用防 GC

        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS};
            }}
            /* P07：hover 统一反馈 = 背景提亮 + 边框强调色。
               原实现仅改 border-color——1px 边框变色在深色卡片底上几乎
               不可见，反馈严重不足。背景渐变与 probability_stats_widget 的
               prob-row hover 对齐，保证四面板列表项视觉语言一致。
               阴影变化无法用 QSS（Qt 不支持 box-shadow），见 enterEvent。 */
            QFrame:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD_HOVER}, stop:1 {Colors.HOVER});
                border-color: {self._accent_color};
            }}
        """)

        # 统一卡片阴影（CARD 基础阴影，QGraphicsDropShadowEffect）
        # 全程只建一个实例、hover 时只改参数（见 _apply_card_hover）。
        # 这样同时避开两个真踩过的坑：
        # ① setGraphicsEffect() 换装时 Qt 会删除旧 effect（Qt 接管所有权），
        #    保存两个 effect 来回换会让先装的那个变悬空指针，下次抛
        #    RuntimeError: Internal C++ object already deleted；
        # ② QGraphicsDropShadowEffect 不是 QWidget，PySide6 不做 Qt 父对象生命周期
        #    管理，不留 Python 引用会被 CPython 立刻 GC，表现为 setGraphicsEffect
        #    后 graphicsEffect() 立即返回 None（静默失效）。
        from ui.styles import Shadows, make_shadow
        self._shadow_supported = False
        self._shadow_hover_state = False  # 当前是否为 hover 阴影
        self._current_shadow = None       # 唯一实例，卡片存活期内不更换
        try:
            self._current_shadow = make_shadow(Shadows.CARD)
            self.setGraphicsEffect(self._current_shadow)
            self._shadow_supported = True
        except Exception:
            self._current_shadow = None

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(Spacing.S0)

        # 标题栏（可点击折叠/展开）
        self._header = _ClickableHeader()
        self._header.setCursor(QCursor(Qt.PointingHandCursor))
        self._header.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: none;
                border-radius: {Spacing.RADIUS};
            }}
        """)
        self._header.clicked.connect(self.toggle)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(Spacing.S4, Spacing.S3, Spacing.S4, Spacing.S3)
        header_layout.setSpacing(Spacing.S3)

        # 强调色条（视觉层次标识：排盘=青 / AI=金）
        self._accent_bar = QFrame()
        self._accent_bar.setFixedSize(4, 20)
        self._accent_bar.setStyleSheet(f"background: {self._accent_color}; border-radius: 2px;")

        # 图标
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 15px; color: {self._accent_color}; background: transparent;")
        icon_label.setFixedWidth(24)

        # 标题（五号字阶梯：SECTION 级）
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT};
            font-family: {Fonts.BODY};
            background: transparent;
        """)

        # 折叠箭头指示（▼ 展开 / ▶ 收起）
        self._chevron = QLabel('▶' if self._collapsed else '▼')
        self._chevron.setStyleSheet(f"""
            font-size: 12px;
            color: {self._accent_color};
            background: transparent;
        """)
        self._chevron.setFixedWidth(16)
        self._chevron.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(self._accent_bar)
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self._chevron)

        self._main_layout.addWidget(self._header)

        # 内容容器
        self._content_container = QWidget()
        self._content_container.setStyleSheet("background: transparent; border: none;")
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(Spacing.S4, Spacing.S0, Spacing.S4, Spacing.S4)
        self._content_layout.setSpacing(Spacing.S0)
        self._main_layout.addWidget(self._content_container)

        # 初始折叠态：直接隐藏内容（无动画）
        if self._collapsed:
            self._content_container.setMaximumHeight(0)
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

    def is_collapsed(self) -> bool:
        """返回当前是否处于折叠状态。"""
        return self._collapsed

    def toggle(self):
        """切换折叠/展开状态（M3-5：写入持久化记忆）。"""
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool, animated: bool = True):
        """设置折叠状态（M3-5：写入进程内折叠记忆）。

        Args:
            collapsed: True 收起内容；False 展开内容。
            animated:  是否使用高度过渡动画（初次构建可传 False）。
        """
        if collapsed == self._collapsed:
            return
        self._collapsed = bool(collapsed)
        self._chevron.setText('▶' if self._collapsed else '▼')
        # M3-5：persist_key 命中时写入折叠偏好（进程内有效）
        if self._persist_key:
            self._COLLAPSE_STATE[self._persist_key] = self._collapsed
        container = self._content_container

        if not animated:
            container.setVisible(not self._collapsed)
            container.setMaximumHeight(0 if self._collapsed else 16777215)
            return

        if self._collapse_anim is not None:
            self._collapse_anim.stop()

        if self._collapsed:
            # 收起：从当前高度动画到 0（M6 规范：300ms IN_OUT_CUBIC）
            from ui.animation import DURATION_NORMAL, EASING_STANDARD
            start_h = max(container.sizeHint().height(), container.height())
            container.setMaximumHeight(start_h)
            anim = QPropertyAnimation(container, b'maximumHeight', container)
            anim.setDuration(DURATION_NORMAL)
            anim.setStartValue(start_h)
            anim.setEndValue(0)
            anim.setEasingCurve(EASING_STANDARD)
            anim.finished.connect(lambda: container.setVisible(False))
            self._collapse_anim = anim
            anim.start()
        else:
            # 展开：先显示，从 0 动画到内容推荐高度，结束后放开高度上限
            from ui.animation import DURATION_NORMAL, EASING_STANDARD
            container.setVisible(True)
            container.setMaximumHeight(0)
            target_h = container.sizeHint().height()
            anim = QPropertyAnimation(container, b'maximumHeight', container)
            anim.setDuration(DURATION_NORMAL)
            anim.setStartValue(0)
            anim.setEndValue(target_h)
            anim.setEasingCurve(EASING_STANDARD)
            anim.finished.connect(lambda: container.setMaximumHeight(16777215))
            self._collapse_anim = anim
            anim.start()

    # ---- P07：hover 统一反馈（阴影部分）----
    # Qt QSS 不支持 box-shadow，阴影只能在事件里用 QGraphicsDropShadowEffect
    # 切换：基础黑阴影（下沉感）↔ 古金光晕（抬起感）。背景/边框由 QSS 负责。
    def enterEvent(self, event):
        self._apply_card_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_card_hover(False)
        super().leaveEvent(event)

    def _apply_card_hover(self, hover: bool):
        """切换卡片阴影（P07）：只改参数，不换装 effect 实例。

        Args:
            hover: True 切古金光晕（抬起感），False 还原基础黑阴影（下沉感）。
        """
        hover = bool(hover)
        if not self._shadow_supported or self._shadow_hover_state == hover:
            return
        # 安全检查：控件可能已销毁或 effect 被 Qt 删除，避免 RuntimeError
        if self._current_shadow is None or self.graphicsEffect() is not self._current_shadow:
            self._shadow_supported = False
            return
        self._shadow_hover_state = hover
        from ui.styles import Shadows, apply_shadow
        spec = Shadows.CARD_HOVER if hover else Shadows.CARD
        try:
            apply_shadow(spec, self._current_shadow)
        except RuntimeError:
            # effect 已被删除（控件销毁或 Qt 内部释放），禁用阴影
            self._shadow_supported = False
            self._current_shadow = None


def apply_click_feedback(button, scale: float = 0.94, duration: int = 90):
    """T7.3 为按钮绑定点击微缩放反馈（press 缩小 → release 复原）。

    用 QPropertyAnimation 驱动 minimumWidth 做「手感缩放」：QWidget 没有
    setScale 接口，而 QGraphicsEffect 又与卡片阴影冲突，改宽度是最稳的
    等效实现（按钮在布局中会随之视觉收缩再弹回）。

    可重复调用：内部用 _click_feedback_bound 标记，避免重复绑定导致
    一次点击触发多组动画。

    Args:
        button: 目标 QAbstractButton（QPushButton / QToolButton）
        scale:  按下时相对原宽度的比例，默认 0.94
        duration: 单程动画时长（毫秒），默认 90

    Returns:
        传入的 button，便于链式调用
    """
    if button is None or getattr(button, '_click_feedback_bound', False):
        return button
    try:
        anim = QPropertyAnimation(button, b'minimumWidth', button)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _base_width():
            # 布局撑开后 width 才是真实宽度；minimumWidth 为 0 时退回 width
            return button.minimumWidth() or button.width() or 1

        def _press():
            try:
                w = _base_width()
                button.setProperty('_cf_base_width', w)
                anim.stop()
                anim.setStartValue(w)
                anim.setEndValue(max(1, int(w * scale)))
                anim.start()
            except RuntimeError:
                pass

        def _release():
            try:
                w = button.property('_cf_base_width') or _base_width()
                anim.stop()
                anim.setStartValue(button.minimumWidth() or w)
                anim.setEndValue(int(w))
                anim.start()
            except RuntimeError:
                pass

        button.pressed.connect(_press)
        button.released.connect(_release)
        button._click_feedback_bound = True
    except Exception:
        pass
    return button


def set_all_cards_collapsed(container: QWidget, collapsed: bool):
    """批量折叠/展开容器内所有 CollapsibleCard。

    Args:
        container: 卡片所在的父控件（通常是滚动区内容控件），
                   通过 findChildren 递归查找全部卡片。
        collapsed: True 全部收起；False 全部展开。
    """
    for card in container.findChildren(CollapsibleCard):
        try:
            card.set_collapsed(collapsed)
        except RuntimeError:
            # 控件已被销毁（deleteLater 后引用悬空），跳过
            continue


class TaijiSpinner(QLabel):
    """旋转太极加载动画控件。

    通过 QPropertyAnimation 循环改变 rotation 属性，paintEvent 中
    旋转绘制太极字符；动画随控件生命周期自动停止。
    """

    def __init__(self, size: int = 56, color: str = Colors.QINGHUA,
                 duration: int = 2400, parent=None):
        """
        Args:
            size:     控件边长（像素，正方形）。
            color:    太极字符颜色（排盘=青花蓝、AI=鎏金）。
            duration: 旋转一周时长（毫秒），越小转得越快。
            parent:   Qt 父控件。
        """
        super().__init__(parent)
        self._rotation = 0
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setText('☯')
        self.setStyleSheet(f"font-size: {int(size * 0.62)}px; color: {color}; background: transparent;")

        # 无限循环旋转动画（parent 绑定到自身，控件销毁时动画自动停止）
        self._anim = QPropertyAnimation(self, b'rotation', self)
        self._anim.setStartValue(0)
        self._anim.setEndValue(360)
        self._anim.setDuration(duration)
        self._anim.setLoopCount(-1)
        self._anim.start()

    def get_rotation(self) -> float:
        """当前旋转角度（属性 getter）。"""
        return self._rotation

    def set_rotation(self, angle: float):
        """设置旋转角度并触发重绘（属性 setter）。"""
        self._rotation = angle
        self.update()

    # Qt 属性：供 QPropertyAnimation 驱动旋转
    rotation = Property(float, get_rotation, set_rotation)

    def paintEvent(self, event):  # noqa: N802（Qt 命名）
        """以控件中心为原点旋转绘制太极字符。"""
        from PySide6.QtGui import QPainter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._rotation)
        painter.translate(-self.width() / 2, -self.height() / 2)
        super().paintEvent(event)
        painter.end()


class LoadingPanel(QWidget):
    """居中加载面板：旋转太极 + 主文案 + 副标题 + 轮播提示语。

    三大板块排盘 / AI 解读加载态统一复用，视觉一致。
    """

    def __init__(self, message: str = '正在排盘…', sub: str = '',
                 color: str = Colors.QINGHUA, hints: Optional[List[str]] = None,
                 parent=None):
        """
        Args:
            message: 主文案（如「龙虎山大师兄正在解读命盘…」）。
            sub:     副标题小字（可空）。
            color:   主题色（排盘=青花蓝 Colors.QINGHUA / AI=鎏金 Colors.LIUJIN）。
            hints:   轮播提示语列表，每 2.6 秒切换一条；None/空则不显示。
            parent:  Qt 父控件。
        """
        super().__init__(parent)
        self.setStyleSheet('background: transparent;')
        outer = QVBoxLayout(self)
        outer.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        outer.setContentsMargins(Spacing.S6, Spacing.S8, Spacing.S6, Spacing.S8)
        outer.addStretch(1)

        col = QVBoxLayout()
        col.setAlignment(Qt.AlignCenter)
        col.setSpacing(Spacing.S4)

        # 旋转太极
        col.addWidget(TaijiSpinner(size=58, color=color), 0, Qt.AlignCenter)

        # 主文案
        msg_label = QLabel(message)
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setStyleSheet(f"""
            font-size: {Fonts.SZ_BODY};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT};
            font-family: {Fonts.BODY};
        """)
        col.addWidget(msg_label)

        # 副标题
        if sub:
            sub_label = QLabel(sub)
            sub_label.setAlignment(Qt.AlignCenter)
            sub_label.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT_SUB};")
            col.addWidget(sub_label)

        # 轮播提示语（进度感）
        self._hint_label = None
        self._hints = list(hints or [])
        self._hint_index = 0
        if self._hints:
            self._hint_label = QLabel(self._hints[0])
            self._hint_label.setAlignment(Qt.AlignCenter)
            self._hint_label.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {color};")
            col.addWidget(self._hint_label)
            self._hint_timer = QTimer(self)
            self._hint_timer.setInterval(2600)
            self._hint_timer.timeout.connect(self._rotate_hint)
            self._hint_timer.start()

        outer.addLayout(col)
        outer.addStretch(1)

    def _rotate_hint(self):
        """轮播切换提示语（带淡入效果由样式简化，直接切换文本）。"""
        if not self._hints or self._hint_label is None:
            return
        self._hint_index = (self._hint_index + 1) % len(self._hints)
        try:
            self._hint_label.setText(self._hints[self._hint_index])
        except RuntimeError:
            # 控件已销毁
            pass


def loading_panel(message: str = '正在排盘…', sub: str = '',
                  color: str = Colors.QINGHUA,
                  hints: Optional[List[str]] = None) -> QWidget:
    """工厂函数：构造一个居中 LoadingPanel（直接 addWidget 即可）。"""
    return LoadingPanel(message=message, sub=sub, color=color, hints=hints)


class ResponsiveFlow(QWidget):
    """响应式流式网格容器：随可用宽度自动换列。

    替代固定列数的 QHBoxLayout/QGridLayout：宽屏一行多列、
    窄屏自动降为单列纵向排列，适配不同屏幕尺寸。
    内部使用 QGridLayout 重排，reflowed 信号在列数变化时发出，
    便于调用方联动（如箭头方向切换）。
    """

    reflowed = Signal(int)  # 参数：当前列数

    def __init__(self, min_item_width: int = 240, max_cols: int = 4,
                 min_cols: int = 1, spacing: int = 12, parent=None):
        """
        Args:
            min_item_width: 每个子项的最小宽度（像素），据此计算列数。
            max_cols:       最大列数。
            min_cols:       最小列数（窄屏下限，默认 1）。
            spacing:        子项间距（像素）。
            parent:         Qt 父控件。
        """
        super().__init__(parent)
        self.setStyleSheet('background: transparent;')
        self._min_item_width = min_item_width
        self._max_cols = max(1, max_cols)
        self._min_cols = max(1, min_cols)
        self._items = []           # list[QWidget]
        self._cols = -1
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(spacing)

    def add_widget(self, widget: QWidget):
        """追加一个子项并立即重排。"""
        self._items.append(widget)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._reflow(force=True)

    def count(self) -> int:
        """已添加的子项数量。"""
        return len(self._items)

    def _compute_cols(self) -> int:
        """根据当前宽度计算应使用的列数。"""
        avail = max(self.width(), self._min_item_width * self._min_cols)
        cols = int(avail // (self._min_item_width + self._grid.spacing()))
        cols = max(self._min_cols, min(self._max_cols, cols, len(self._items) or 1))
        return cols

    def _clear_grid(self):
        """从网格中移除全部子项（不销毁控件本身）。"""
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                self._grid.removeWidget(w)
        # 重置所有列拉伸系数
        for c in range(self._max_cols + 1):
            self._grid.setColumnStretch(c, 0)

    def _reflow(self, force: bool = False):
        """按当前列数重新摆放子项。"""
        if not self._items:
            return
        cols = self._compute_cols()
        if not force and cols == self._cols:
            return
        changed = cols != self._cols
        self._cols = cols
        self._clear_grid()
        for idx, w in enumerate(self._items):
            row, col = divmod(idx, cols)
            self._grid.addWidget(w, row, col)
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)
        if changed:
            self.reflowed.emit(cols)

    def resizeEvent(self, event):  # noqa: N802（Qt 命名）
        """宽度变化时自动重排。"""
        super().resizeEvent(event)
        self._reflow()

    def showEvent(self, event):  # noqa: N802（Qt 命名）
        """首次显示时按实际宽度重排（构造时宽度可能尚未确定）。"""
        super().showEvent(event)
        self._reflow(force=True)


def ai_section_header(title: str = '龙虎山大师兄算命详批', icon: str = '🧙') -> QWidget:
    """龙虎山大师兄算命区 hero 标题 v2.3：鎏金渐变背景 + 大图标 + 大标题 + 副标题 + 时间戳。

    视觉与文案升级（v2.3）：
    - 顶部 1px 鎏金渐变分隔线，营造仪式感
    - 双层背景：鎏金微透底 + 装饰性金色光晕
    - 左侧 64px 大圆形图标（外圈光晕 + 内圈实心）+ 20px 加粗主标题
    - 副标题改为「龙虎山大师兄亲批 · 承古法、参五行、酌神煞」，强化算命语境
    - 右侧显示算命时间戳 + 「法旨/批语」徽章（取代原「KP v1.0」徽章）
    - 底部装饰文案改为「☯ 大师兄亲批，仅供文化研究参考 ☯」，剔除「AI 自动生成」字样

    Returns:
        可直接 addWidget 的 QWidget（无外边距，由父布局控制间距）。
    """
    container = QFrame()
    container.setObjectName('longhushan_hero_header')
    container.setStyleSheet(f"""
        QFrame#longhushan_hero_header {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {Colors.LIUJIN_GLOW}, stop:0.5 {Colors.LIUJIN_GLOW},
                stop:1 rgba(184, 138, 48, 0.02));
            border: 1px solid {Colors.LIUJIN_LIGHT};
            border-radius: {Spacing.RADIUS_LG};
            margin: 18px 0 8px 0;
        }}
    """)
    v = QVBoxLayout(container)
    v.setContentsMargins(Spacing.S_MARGIN_EXTRA, Spacing.S_GAP_SM, Spacing.S_MARGIN_EXTRA, Spacing.S_GAP_SM)
    v.setSpacing(Spacing.S3)

    # ---------- 顶部：图标 + 标题 + 时间戳 ----------
    h = QHBoxLayout()
    h.setSpacing(Spacing.S4)
    h.setAlignment(Qt.AlignVCenter)

    # 左侧大圆形图标：外圈光晕 + 内圈实心 + 中央字符
    icon_outer = QFrame()
    icon_outer.setFixedSize(72, 72)
    icon_outer.setStyleSheet(f"""
        QFrame {{
            background: qradialgradient(cx:0.5, cy:0.5, radius:0.6,
                stop:0 {Colors.LIUJIN}40, stop:1 transparent);
            border: none;
        }}
    """)
    icon_outer_lay = QVBoxLayout(icon_outer)
    icon_outer_lay.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
    icon_outer_lay.setContentsMargins(Spacing.S_MIN, Spacing.S_MIN, Spacing.S_MIN, Spacing.S_MIN)
    icon_outer_lay.setAlignment(Qt.AlignCenter)

    icon_box = QFrame()
    icon_box.setFixedSize(60, 60)
    icon_box.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {Colors.LIUJIN_LIGHT}, stop:1 {Colors.LIUJIN});
            border: 2px solid {Colors.LIUJIN};
            border-radius: 30px;
        }}
    """)
    icon_lay = QVBoxLayout(icon_box)
    icon_lay.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
    icon_lay.setContentsMargins(0, 0, 0, 0)
    icon_inner = QLabel(icon)
    icon_inner.setAlignment(Qt.AlignCenter)
    icon_inner.setStyleSheet(f"""
        font-size: 30px;
        color: white;
        background: transparent;
        border: none;
    """)
    icon_lay.addWidget(icon_inner)
    icon_outer_lay.addWidget(icon_box)
    h.addWidget(icon_outer)

    # 标题区（主标题 + 副标题）：M3-3 统一走 TLabel 工厂
    title_col = QVBoxLayout()
    title_col.setSpacing(Spacing.S1)
    title_col.setAlignment(Qt.AlignVCenter)

    # 主标题（TLabel.h1 = 20px，§ 由 TLabel.h1 的 _SPECS 给出）
    title_label = TLabel.h1(title)
    title_label.setStyleSheet(
        f"font-weight: {Fonts.W_BOLD}; color: {Colors.LIUJIN_DARK}; "
        f"letter-spacing: 2px;"
    )

    # 副标题：去 AI 化、改为龙虎山大师兄算命描述（TLabel.caption = 12px）
    sub_label = TLabel.caption(
        '· 龙虎山大师兄亲批  ·  承古法、参五行、酌神煞  ·'
    )
    sub_label.setStyleSheet(f"color: {Colors.TEXT2}; letter-spacing: 1px;")

    title_col.addWidget(title_label)
    title_col.addWidget(sub_label)

    # 三段式标签：体现「算命」语境而非 AI 语境
    tag_row = QHBoxLayout()
    tag_row.setSpacing(Spacing.S2)
    tag_row.setContentsMargins(Spacing.S0, Spacing.S1, Spacing.S0, Spacing.S0)
    tag_items = [
        ('古法', Colors.ZHUSHA),
        ('五行', Colors.LIUJIN),
        ('神煞', Colors.QINGHUA),
    ]
    for text, tag_color in tag_items:
        chip = QLabel(text)
        chip.setStyleSheet(f"""
            background: {tag_color}1A;
            color: {tag_color};
            border: 1px solid {tag_color}55;
            border-radius: 8px;
            padding: 1px 8px;
            font-size: 11px;
            font-weight: {Fonts.W_MEDIUM};
            font-family: {Fonts.BODY};
        """)
        chip.setFixedHeight(18)
        tag_row.addWidget(chip)
    tag_row.addStretch()

    title_col.addWidget(title_label)
    title_col.addWidget(sub_label)
    title_col.addLayout(tag_row)
    h.addLayout(title_col, 1)

    # 右侧：时间戳 + 「法旨」徽章（取代 AI 徽章）
    ts_col = QVBoxLayout()
    ts_col.setSpacing(Spacing.S1)
    ts_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    ts_text = datetime.now().strftime('%Y-%m-%d %H:%M')
    ts_lbl = QLabel(f'🕐 {ts_text}')
    ts_lbl.setStyleSheet(
        f"font-size: 11px; color: {Colors.TEXT3}; "
        f"font-family: {Fonts.MONO};"
    )
    ts_lbl.setAlignment(Qt.AlignRight)

    badge = QLabel('法旨 · 批语')
    badge.setStyleSheet(f"""
        background: {Colors.LIUJIN};
        color: white;
        font-size: 11px;
        font-weight: {Fonts.W_BOLD};
        padding: 3px 10px;
        border-radius: 9px;
        font-family: {Fonts.BODY};
        letter-spacing: 1px;
    """)
    badge.setAlignment(Qt.AlignRight)
    badge.setFixedHeight(20)

    ts_col.addWidget(ts_lbl)
    ts_col.addWidget(badge)
    h.addLayout(ts_col)

    v.addLayout(h)

    # ---------- 底部装饰：金线 + 文字点缀（去 AI 描述） ----------
    deco_row = QHBoxLayout()
    deco_row.setSpacing(Spacing.S2)
    deco_row.setAlignment(Qt.AlignVCenter)

    line_left = QFrame()
    line_left.setFixedHeight(1)
    line_left.setStyleSheet(
        f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        f"stop:0 transparent, stop:1 {Colors.LIUJIN_LIGHT}); border: none;"
    )

    # 装饰文案：改为「大师兄亲批」，去掉 AI 字样
    deco_text = QLabel('☯  大师兄亲批 · 仅供文化研究参考  ☯')
    deco_text.setStyleSheet(
        f"font-size: 11px; color: {Colors.LIUJIN}; "
        f"font-family: {Fonts.BODY}; letter-spacing: 1.5px;"
    )

    line_right = QFrame()
    line_right.setFixedHeight(1)
    line_right.setStyleSheet(
        f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        f"stop:0 {Colors.LIUJIN_LIGHT}, stop:1 transparent); border: none;"
    )

    deco_row.addWidget(line_left, 1)
    deco_row.addWidget(deco_text)
    deco_row.addWidget(line_right, 1)
    v.addLayout(deco_row)

    return container


def ai_section_nav(items: List[Tuple[str, str, str]], active_color: str = Colors.LIUJIN) -> QWidget:
    """AI 解读区目录导航条 v2.2：横向胶囊按钮组 + 滚动支持。

    提供可视化的章节目录，点击触发锚点跳转。章节按钮采用圆角胶囊样式，
    hover/active 状态变色，简洁直观。

    Args:
        items: 导航条目列表，每项 (anchor_id, label, icon)：
                - anchor_id: 锚点 ID，用于跳转定位
                - label: 按钮文字
                - icon: 按钮左侧图标
        active_color: 默认主题色（鎏金）

    Returns:
        可直接 addWidget 的 QWidget（导航条容器）
    """
    outer = QFrame()
    outer.setStyleSheet(f"""
        QFrame {{
            background: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS};
            margin: 0 0 4px 0;
        }}
    """)

    outer_layout = QVBoxLayout(outer)
    outer_layout.setContentsMargins(0, 0, 0, 0)
    outer_layout.setSpacing(Spacing.S0)

    # 滚动容器
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFixedHeight(46)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet(f"""
        QScrollArea {{ background: transparent; border: none; }}
        QScrollBar:horizontal {{
            background: transparent; height: 4px; margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {Colors.BORDER2}; border-radius: 2px; min-width: 20px;
        }}
        QScrollBar::handle:horizontal:hover {{ background: {Colors.LIUJIN}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}
    """)

    chip_container = QWidget()
    chip_container.setStyleSheet('background: transparent; border: none;')
    chip_layout = QHBoxLayout(chip_container)
    chip_layout.setContentsMargins(Spacing.S_MARGIN_XS, Spacing.S2, Spacing.S_MARGIN_XS, Spacing.S2)
    chip_layout.setSpacing(Spacing.S2)

    btn_group = QButtonGroup(outer)
    btn_group.setExclusive(False)  # 不互斥，仅作为点击回调容器

    nav_buttons = []  # 存储 (btn, anchor_id, label)

    for idx, (anchor_id, label, icon) in enumerate(items):
        btn = _NavChipButton(label, icon, active_color)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.clicked.connect(lambda _checked=False, aid=anchor_id: _scroll_to_anchor(aid))
        chip_layout.addWidget(btn)
        btn_group.addButton(btn, idx)
        nav_buttons.append((btn, anchor_id, label))

    chip_layout.addStretch()
    scroll.setWidget(chip_container)
    outer_layout.addWidget(scroll)

    # 保存引用，供外部更新激活状态
    outer._nav_buttons = nav_buttons
    return outer


class _NavChipButton(QPushButton):
    """导航条胶囊按钮：自定义圆角胶囊样式 + hover/active 反馈。"""

    def __init__(self, text: str, icon: str, active_color: str):
        self.active_color = active_color
        super().__init__()
        display = f'{icon} {text}' if icon else text
        self.setText(display)
        self.setFixedHeight(30)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._apply_style(False)

    def _apply_style(self, hovered: bool):
        if hovered:
            bg = f'{self.active_color}25'
            border = self.active_color
            color = self.active_color
        else:
            bg = Colors.HOVER
            border = Colors.BORDER
            color = Colors.TEXT2

        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: {color};
                border: 1px solid {border};
                border-radius: 14px;
                padding: 0 12px;
                font-size: {Fonts.SZ_SMALL};
                font-family: {Fonts.BODY};
                font-weight: {Fonts.W_MEDIUM};
            }}
            QPushButton:hover {{
                background: {self.active_color}30;
                border-color: {self.active_color};
                color: {self.active_color};
            }}
            QPushButton:pressed {{
                background: {self.active_color};
                color: white;
            }}
        """)

    def enterEvent(self, event):
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        super().leaveEvent(event)


# 锚点跳转调度：避免循环导入，使用全局缓存
_ANCHOR_SCROLL_CALLBACK = None


def register_anchor_scroller(callback) -> None:
    """注册锚点跳转回调（由 result_panel 设置）。"""
    global _ANCHOR_SCROLL_CALLBACK
    _ANCHOR_SCROLL_CALLBACK = callback


def _scroll_to_anchor(anchor_id: str) -> None:
    """点击导航按钮时调用，跳转到对应锚点。"""
    if _ANCHOR_SCROLL_CALLBACK:
        try:
            _ANCHOR_SCROLL_CALLBACK(anchor_id)
        except Exception:
            pass


def highlight_label(text: str, color: str = Colors.LIUJIN) -> QWidget:
    """生成一条「重要内容」高亮提示块：左侧色条 + 鎏金/强调色图标 + 文案。

    用于龙虎山大师兄算命解读中标注关键结论、关键信息或风险提示，
    与排盘卡片视觉一致，强化信息层级。

    Args:
        text:  要强调的文案（支持换行）。
        color: 强调色（默认鎏金 Colors.LIUJIN）。

    Returns:
        可直接 addWidget 到卡片内容容器的 QWidget。
    """
    container = QFrame()
    container.setStyleSheet(f"""
        QFrame {{
            background: {Colors.LIUJIN_GLOW};
            border-left: 4px solid {color};
            border-radius: {Spacing.RADIUS_SM};
        }}
    """)
    hl = QHBoxLayout(container)
    hl.setContentsMargins(Spacing.S3, Spacing.S_MARGIN_XS, Spacing.S3, Spacing.S_MARGIN_XS)
    hl.setSpacing(Spacing.S3)

    # 图标由 ⭐ 改为 批（算命语境专属标识，呼应「大师兄亲批」标题）
    star = QLabel('批')
    star.setStyleSheet(f"""
        font-size: 13px; font-weight: {Fonts.W_BOLD};
        color: white; background: {color};
        border: 1px solid {color};
        border-radius: 11px;
        font-family: {Fonts.TITLE};
    """)
    star.setFixedSize(22, 22)
    star.setAlignment(Qt.AlignCenter)

    txt = QLabel(text)
    txt.setWordWrap(True)
    txt.setStyleSheet(
        f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; "
        f"font-family: {Fonts.BODY}; line-height: 1.6;"
    )
    hl.addWidget(star)
    hl.addWidget(txt, 1)
    return container


def _strength_verdict(group: str, strength: str) -> tuple:
    """根据「维度分组 + 强度等级」返回一对描述：(趋势, 指引)。

    不返回百分比，避免空洞的数值显示；改用龙虎山大师兄算命语境的文字解读，
    强调「运势强弱」与「行动方向」，与各维度语义贴合。

    Args:
        group:   维度分组（事业 / 财运 / 感情 / 健康 / 学业 / 人际 / 其他）
        strength: 强度等级（强 / 中 / 弱）

    Returns:
        (趋势, 指引) 两段文字描述的元组。
    """
    # 通用基础描述（按维度分组）
    _GROUP_TREND = {
        '事业': {
            '强': '命局官杀得力、印星扶身，事业运势呈上升之势；近期有升迁、掌权、独当一面之象，宜顺势而行。',
            '中': '事业运势起伏不大，以守成为主；当前阶段宜深耕本业、稳步积累，等待下一轮大运转机。',
            '弱': '官星受克、印绶不显，事业上易遇阻滞或小人掣肘；宜静守本分、修养内功，忌冒进跳槽。',
        },
        '财运': {
            '强': '财星当令、伤官生财，正财偏财皆有所得；近期有进财之象，宜广开财源、量入为出。',
            '中': '财来财去相对平稳，无大起大落；宜量力而行、稳健理财，忌投机取巧、盲目扩张。',
            '弱': '财星受制、耗泄过重，求财较为费力；近期宜守不宜攻，多置不动产或学习理财以补偏。',
        },
        '感情': {
            '强': '桃花星动、配偶星明润，感情运势向好；单身者有良缘佳兆，已婚者宜增进沟通、共筑温暖。',
            '中': '感情运势波澜不惊，宜以平常心相处；多关注伴侣情绪、用心经营，方能细水长流。',
            '弱': '感情宫受冲、桃花星隐伏，易生误会或疏离；宜加强沟通、避免猜疑，必要时可借风水调和。',
        },
        '健康': {
            '强': '五行流通有情、气血调和；近期身心状态俱佳，宜保持规律作息，延续良好势态。',
            '中': '体质尚可但偶有疲累；宜按时休养、劳逸结合，关注饮食与情绪调节。',
            '弱': '五行偏枯之象已现，恐有暗疾潜伏；宜定期体检、调理作息，必要时及时就医。',
        },
        '学业': {
            '强': '文昌得位、印星护身，利于考试晋升与学术研究；宜把握关键节点、深耕细作。',
            '中': '学业运势中规中矩，需勤学不辍；宜夯实基础、循序渐进，切勿临阵松懈。',
            '弱': '学业受阻、心绪易浮；宜调整心态、求助良师益友，避免临阵换将、好高骛远。',
        },
        '人际': {
            '强': '贵人星动、六合临宫，社交场上左右逢源；近期宜主动拓展人脉、合作共赢。',
            '中': '人际运势平稳，无大喜大忧；宜真诚待人、维系旧交，遇事可求稳不求多。',
            '弱': '小人星动、口舌易生；近期宜谨言慎行、低调处世，远离是非漩涡。',
        },
        '其他': {
            '强': '此维度命理走势向好，宜把握时机、积极作为。',
            '中': '此维度运势平稳，宜顺势而为、不急不躁。',
            '弱': '此维度略显薄弱，宜守成避险、静待转机。',
        },
    }

    _GROUP_ACTION = {
        '事业': {
            '强': '把握升迁/合作机会，主动承担核心项目，可考虑进修以夯实根基。',
            '中': '深耕本业、提升专业度，以稳为主，可适度进修考取资质。',
            '弱': '守好本分、避免跳槽，多向贵人请教，借团队之力化解困局。',
        },
        '财运': {
            '强': '可适度扩张投资、配置长线资产，但忌孤注一掷、以稳为主。',
            '中': '稳健理财、量入为出，避免高杠杆操作。',
            '弱': '守财为先、忌投机取巧，可多学习理财知识、广积福德。',
        },
        '感情': {
            '强': '主动表达爱意、制造仪式感，单身者可参加社交活动拓缘。',
            '中': '多用心思经营日常，避免冷暴力与疏离。',
            '弱': '少争执、多倾听，可借助旅行、共同爱好重塑亲密感。',
        },
        '健康': {
            '强': '坚持运动与作息，延展良好势态。',
            '中': '增加户外活动、规律饮食、避免熬夜。',
            '弱': '及时体检、对症调理，必要时寻求专业医师帮助。',
        },
        '学业': {
            '强': '深耕专业、争取发表或项目成果。',
            '中': '夯实基础、循序渐进，制定可执行的学习计划。',
            '弱': '调整学习方法、求助良师，避免临时抱佛脚。',
        },
        '人际': {
            '强': '主动拓圈、参与高质量社交活动，借力共赢。',
            '中': '维系旧交、适度社交，重质不重量。',
            '弱': '谨言慎行，远离是非，必要时主动化解误会。',
        },
        '其他': {
            '强': '顺势而动、积极作为。',
            '中': '保持节奏、不急不躁。',
            '弱': '守成避险、静待转机。',
        },
    }

    trend_map = _GROUP_TREND.get(group, _GROUP_TREND['其他'])
    action_map = _GROUP_ACTION.get(group, _GROUP_ACTION['其他'])

    # ---------- 调试日志：方便排查文案是否正确 ----------
    group_fallback = group not in _GROUP_TREND
    strength_fallback = strength not in trend_map
    verdict, action = trend_map.get(strength, trend_map['中']), action_map.get(strength, action_map['中'])
    try:
        logger.debug(
            "[_strength_verdict] group=%s strength=%s fallback_group=%s fallback_strength=%s "
            "→ trend=%r | action=%r",
            group, strength, group_fallback, strength_fallback, verdict, action,
        )
    except Exception:
        # 日志失败不影响业务路径
        pass
    return verdict, action


def probability_stats_widget(stats: object, color: str = Colors.LIUJIN) -> QWidget:
    """把「概率统计」渲染为可读卡片：智能分组 + 多格式解析 + 阈值色标 + 排序 + 文字描述 + 详细工具提示 + 强度图例。

    设计目标：解决原先只丢几个数字、用户完全看不懂的问题。
    - 支持格式： "事业财运：82%" / "感情婚姻:65%" / "事业 85分" / "整体 0.75" / "财运 70-80%" / "健康 [高] 90%"
    - 自动分组：事业/财运/官运归「事业组」，感情/婚姻/姻缘归「感情组」，健康/疾病/寿命归「健康组」
    - 阈值色标：≥80% 绿(强) / 60-79% 黄(中) / <60% 红(弱)
    - 可按数值排序，附带「如何理解这些数据」说明块
    - 悬浮显示：维度含义、计算依据、置信度、参考建议
    - 新增强度图例：直观展示颜色与强度对应关系。

    Args:
        stats: AI 返回的 probability_stats，可能是字符串列表或字符串。
        color: 强调色（默认鎏金）。

    Returns:
        可直接 set_content / addWidget 的 QWidget。
    """
    import html  # 添加HTML转义导入

    container = QWidget()
    v = QVBoxLayout(container)
    v.setContentsMargins(Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM)
    v.setSpacing(Spacing.S4)

    items = []
    if isinstance(stats, (list, tuple)):
        items = [str(x).strip() for x in stats if x and str(x).strip()]
    elif isinstance(stats, str):
        items = [stats] if stats.strip() else []

    # ---------- 解析器：支持多种格式 ----------
    # 匹配模式：
    #   标签：数值%    标签 数值%    标签：数值分    标签 数值分
    #   标签：数值-数值%    标签 [等级] 数值%
    #   纯描述文本
    _num_pat = re.compile(
        r'[:：]?\s*'
        r'(\[?[\u4e00-\u9fff\w]+\]?\s*)?'  # 可选等级标签 [高]/[强] 等
        r'([0-9]+(?:\.[0-9]+)?)'          # 数值
        r'\s*([-%％分]?)'                  # 单位
        r'(?:\s*[~-]\s*([0-9]+(?:\.[0-9]+)?)\s*[%％])?'  # 可选范围上限
        r'\s*$'
    )

    # 维度分组映射
    DIMENSION_GROUPS = {
        '事业': ['事业', '财运', '官运', '工作', '职业', '创业', '投资', '偏财', '正财'],
        '感情': ['感情', '婚姻', '姻缘', '桃花', '恋爱', '伴侣', '配偶', '子女'],
        '健康': ['健康', '疾病', '寿命', '体质', '病灾', '意外', '手术', '康复'],
        '学业': ['学业', '考试', '文昌', '升学', '证书', '技能', '进修'],
        '人际': ['人际', '贵人', '小人', '朋友', '合作', '伙伴', '兄弟', '姐妹'],
    }

    def _classify_dimension(label: str) -> str:
        """根据关键字将维度归类。"""
        for group, keywords in DIMENSION_GROUPS.items():
            if any(kw in label for kw in keywords):
                return group
        return '其他'

    parsed = []  # (group, label, pct_min, pct_max, raw, level_tag)
    for it in items:
        m = _num_pat.search(it)
        if m:
            level_tag = (m.group(1) or '').strip(' []')
            num = float(m.group(2))
            unit = m.group(3)
            range_max = m.group(4)

            if unit in ('%', '％'):
                pct_min = num
            elif unit == '分':
                pct_min = num * 10 if num <= 10 else (num / 100 if num <= 100 else num)
            elif num <= 1.5:
                pct_min = num * 100
            else:
                pct_min = num
            pct_min = max(0.0, min(100.0, pct_min))

            if range_max:
                pct_max = float(range_max)
                pct_max = max(0.0, min(100.0, pct_max))
            else:
                pct_max = pct_min

            label = _num_pat.sub('', it).strip(' :：·-')
            if not label:
                label = it
            group = _classify_dimension(label)
            parsed.append((group, label, pct_min, pct_max, it, level_tag))
        else:
            # 无数字：纯描述条目
            group = _classify_dimension(it)
            parsed.append((group, it, None, None, it, ''))

    # ---------- 排序：按组优先级 + 数值降序 ----------
    GROUP_ORDER = {'事业': 0, '财运': 1, '感情': 2, '健康': 3, '学业': 4, '人际': 5, '其他': 99}
    parsed.sort(key=lambda x: (GROUP_ORDER.get(x[0], 99), -(x[2] or 0)))

    # ---------- 动态提取维度名，用于「如何理解这些数据」说明块 ----------
    dimension_labels = [label for (g, label, pmin, pmax, raw, lvl) in parsed if label]
    if dimension_labels:
        v.insertWidget(0, _build_explanation_box(dimension_labels, color))
    # ---------- 强度图例 ----------
    v.addWidget(_build_strength_legend(color))

    if parsed:
        # 按分组渲染
        current_group = None
        group_widget = None
        group_layout = None
        row_idx = {}

        for group, label, pct_min, pct_max, raw, level_tag in parsed:
            if group != current_group:
                # 结束上一组
                if group_widget:
                    v.addWidget(group_widget)
                # 开始新组
                current_group = group
                group_widget = QWidget()
                group_widget.setStyleSheet("background: transparent;")
                group_layout = QGridLayout(group_widget)
                group_layout.setContentsMargins(0, 0, 0, 0)
                group_layout.setSpacing(Spacing.S4)
                group_layout.setColumnStretch(0, 1)
                group_layout.setColumnStretch(1, 1)
                row_idx[current_group] = 1  # header occupies row 0

                # 分组标题 - 更精致的样式
                header_wrap = QFrame()
                header_wrap.setStyleSheet(f"""
                    QFrame {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 {_glow(color)}, stop:1 transparent);
                        border: 1px solid {color}40;
                        border-radius: {Spacing.RADIUS_SM};
                    }}
                """)
                hh = QHBoxLayout(header_wrap)
                hh.setContentsMargins(Spacing.S_MARGIN_XS, Spacing.S_PAD_SM, Spacing.S_MARGIN_XS, Spacing.S_PAD_SM)
                hh.setSpacing(Spacing.S2)

                # 装饰性左侧色条
                accent_bar = QFrame()
                accent_bar.setFixedSize(3, 18)
                accent_bar.setStyleSheet(f"background: {color}; border-radius: 2px;")

                icon_lbl = QLabel('◈')
                icon_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{color};")
                name_lbl = QLabel(group)
                name_lbl.setStyleSheet(f"""
                    font-size: {Fonts.SZ_SMALL}; font-weight: {Fonts.W_BOLD};
                    color: {color}; font-family: {Fonts.TITLE}; letter-spacing: 1px;
                """)
                hh.addWidget(accent_bar)
                hh.addWidget(icon_lbl)
                hh.addWidget(name_lbl)
                hh.addStretch()
                group_layout.addWidget(header_wrap, 0, 0, 1, 2)

            row = QFrame()
            row.setObjectName(f"prob-row-{hash(label) & 0xFFFF:04x}")
            row.setStyleSheet(f"""
                QFrame#prob-row-* {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {Colors.CARD}, stop:1 {Colors.BG});
                    border: 1px solid {Colors.BORDER};
                    border-left: 4px solid {color};
                    border-radius: {Spacing.RADIUS};
                }}
                QFrame#prob-row-*:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {Colors.CARD_HOVER}, stop:1 {Colors.HOVER});
                    border-color: {color}80;
                    border-left-width: 5px;
                }}
            """)
            # 使用 QGraphicsDropShadowEffect 正确实现阴影（替代无效的 CSS box-shadow）
            # P29：只建一个实例、hover 时改参数。
            # 原实现是「两个 effect + setEnabled 切换」——只有装在 widget 上的那个生效，
            # 对未安装的 _shadow_hover 调 setEnabled(True) 没有任何渲染效果，实际表现是
            # 「hover 时阴影消失」而不是「切换为强调阴影」（静默失效多年）。
            # 改成改同一实例的参数（setter 会触发 changed() 重绘），同时避开两个坑：
            # 换装会让 Qt 删除旧 effect 导致悬空指针；不留引用会被 CPython 立刻 GC。
            from ui.styles import Shadows, apply_shadow, make_shadow
            _row_shadow = make_shadow(Shadows.ROW)
            row.setGraphicsEffect(_row_shadow)

            # hover 时切换阴影参数（QEventLoop 驱动，避免重入）
            class _ShadowSwapFilter(QObject):
                """轻量事件过滤器：hover 进入/退出时切换同一 effect 的参数。"""
                def __init__(self, parent_frame: QFrame,
                             shadow: 'QGraphicsDropShadowEffect') -> None:
                    super().__init__(parent_frame)
                    self._shadow = shadow          # 保持引用，防 CPython 立刻 GC
                    self._spec_base = Shadows.ROW
                    self._spec_hover = Shadows.ROW_HOVER

                def eventFilter(self, obj: object, event: object) -> bool:  # noqa: N802
                    etype = event.type()
                    if etype == QEvent.Type.Enter or etype == QEvent.Enter:
                        apply_shadow(self._spec_hover, self._shadow)
                    elif etype == QEvent.Type.Leave or etype == QEvent.Leave:
                        apply_shadow(self._spec_base, self._shadow)
                    return False
            row.installEventFilter(_ShadowSwapFilter(row, _row_shadow))
            rv = QVBoxLayout(row)
            rv.setContentsMargins(Spacing.S_PAD_XS, Spacing.S3, Spacing.S_PAD_XS, Spacing.S_PAD_XS)
            rv.setSpacing(Spacing.S3)

            head = QHBoxLayout()
            head.setSpacing(Spacing.S3)
            name_lbl = QLabel(label)
            name_lbl.setStyleSheet(
                f"font-size: {Fonts.SZ_BODY}; font-weight: {Fonts.W_BOLD}; "
                f"color: {Colors.TEXT}; font-family: {Fonts.TITLE}; letter-spacing: 0.5px;")
            head.addWidget(name_lbl)

            # 等级标签（如 [高] / [中] / [低]）
            if level_tag:
                lvl_lbl = QLabel(level_tag)
                lvl_color = Colors.SUCCESS if level_tag in ('高', '强', '旺') else (
                    Colors.WARNING if level_tag in ('中', '平') else Colors.DANGER)
                lvl_lbl.setStyleSheet(f"""
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {lvl_color}, stop:1 {lvl_color}CC);
                    color: white;
                    font-size: {Fonts.SZ_MICRO}; font-weight: {Fonts.W_BOLD};
                    border-radius: {Spacing.RADIUS_SM}; padding: 2px 8px;
                    font-family: {Fonts.BODY};
                """)
                head.addWidget(lvl_lbl)

            head.addStretch()

            # 计算强度等级（用于文案而非百分比）
            if pct_min is not None:
                avg_pct = (pct_min + pct_max) / 2
                if avg_pct >= 80:
                    strength = '强'
                    strength_color = Colors.SUCCESS
                    verdict, action = _strength_verdict(group, '强')
                elif avg_pct >= 60:
                    strength = '中'
                    strength_color = Colors.WARNING
                    verdict, action = _strength_verdict(group, '中')
                else:
                    strength = '弱'
                    strength_color = Colors.DANGER
                    verdict, action = _strength_verdict(group, '弱')

                # 调用方日志：记录输入参数 + 强度判定依据，便于排查文案是否符合预期
                try:
                    logger.debug(
                        "[probability_stats] row group=%s label=%s "
                        "pct_min=%.1f pct_max=%.1f avg_pct=%.1f → strength=%s "
                        "verdict=%r | action=%r",
                        group, label, pct_min, pct_max, avg_pct, strength, verdict, action,
                    )
                except Exception:
                    pass

                # 强度徽章 - 更精致的样式
                strength_lbl = QLabel(f'·  {strength}  ·')
                strength_lbl.setStyleSheet(f"""
                    background: qlineargient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {strength_color}22, stop:1 {strength_color}11);
                    color: {strength_color};
                    font-size: {Fonts.SZ_SMALL};
                    font-weight: {Fonts.W_BOLD};
                    border: 1px solid {strength_color}55;
                    border-radius: 14px;
                    padding: 4px 14px;
                    font-family: {Fonts.BODY};
                    letter-spacing: 2px;
                """)
                head.addWidget(strength_lbl)
            rv.addLayout(head)

            if pct_min is not None:
                # 进度条视觉增强 - 更流畅的样式
                from PySide6.QtWidgets import QProgressBar
                avg_pct = (pct_min + pct_max) / 2
                target_val = int(avg_pct)
                progress = QProgressBar()
                progress.setRange(0, 100)
                progress.setValue(0)
                progress.setTextVisible(False)
                progress.setFixedHeight(10)
                progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: none;
                        border-radius: 5px;
                        background: {Colors.BG_DARK};
                        text-align: center;
                    }}
                    QProgressBar::chunk {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 {strength_color}CC, stop:1 {strength_color});
                        border-radius: 5px;
                    }}
                """)
                rv.addWidget(progress)
                # 动态数显动画：进度条从 0 增长到目标值
                anim = QPropertyAnimation(progress, b"value")
                anim.setDuration(900)
                anim.setStartValue(0)
                anim.setEndValue(target_val)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                anim.start()
                # 百分比数值显示 - 独立标签，带动画
                pct_display = QLabel(f'{target_val}%')
                pct_display.setStyleSheet(f"""
                    font-size: 22px;
                    font-weight: {Fonts.W_BOLD};
                    color: {strength_color};
                    font-family: {Fonts.MONO};
                    background: transparent;
                """)
                pct_display.setAlignment(Qt.AlignCenter)
                rv.addWidget(pct_display)

                # 描述性文字区：标题 + 主体判断 + 行动指引
                trend_lbl = QLabel('【趋势研判】')
                trend_lbl.setStyleSheet(
                    f"font-size: {Fonts.SZ_MICRO}; font-weight: {Fonts.W_BOLD}; "
                    f"color: {strength_color}; font-family: {Fonts.BODY}; "
                    f"letter-spacing: 1.5px;")
                rv.addWidget(trend_lbl)

                verdict_lbl = QLabel(verdict)
                verdict_lbl.setWordWrap(True)
                verdict_lbl.setStyleSheet(
                    f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; "
                    f"font-family: {Fonts.BODY}; line-height: 1.7;"
                    f"padding: 2px 0 4px 0;")
                rv.addWidget(verdict_lbl)

                action_lbl = QLabel('【趋吉避凶】')
                action_lbl.setStyleSheet(
                    f"font-size: {Fonts.SZ_MICRO}; font-weight: {Fonts.W_BOLD}; "
                    f"color: {strength_color}; font-family: {Fonts.BODY}; "
                    f"letter-spacing: 1.5px;")
                rv.addWidget(action_lbl)

                action_text = QLabel(action)
                action_text.setWordWrap(True)
                action_text.setStyleSheet(
                    f"font-size: {Fonts.SZ_BODY}; color: {strength_color}; "
                    f"font-family: {Fonts.BODY}; line-height: 1.7;"
                    f"padding: 2px 0 0 0;")
                rv.addWidget(action_text)
            else:
                # 纯描述条目（无百分比）
                desc = QLabel(raw)
                desc.setWordWrap(True)
                desc.setStyleSheet(
                    f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT2}; "
                    f"font-family: {Fonts.BODY}; line-height: 1.6;")
                rv.addWidget(desc)

            # 参考信息与免责声明
            if pct_min is not None:
                ref_text = f'参考值：{pct_min:.0f}%' if pct_max == pct_min else f'参考范围：{pct_min:.0f}% - {pct_max:.0f}%'
                ref_lbl = QLabel(f'◈ {ref_text} · 所属维度：{group}')
                ref_lbl.setStyleSheet(
                    f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT3}; "
                    f"font-family: {Fonts.BODY}; line-height: 1.5;"
                )
                ref_lbl.setWordWrap(True)
                rv.addWidget(ref_lbl)
                # 分割线（视觉分隔参考信息和免责声明）
                spacer = QWidget()
                spacer.setFixedHeight(6)
                rv.addWidget(spacer)
                note_lbl = QLabel('⚠ 参考值系基于命理数据的相对估算，非统计采样，不可作为绝对决策依据。')
                note_lbl.setStyleSheet(
                    f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT4}; "
                    f"font-family: {Fonts.BODY}; line-height: 1.4;")
                note_lbl.setWordWrap(True)
                rv.addWidget(note_lbl)
            # 网格布局放置
            col = (row_idx[current_group] - 1) % 2
            row_pos = (row_idx[current_group] - 1) // 2
            group_layout.addWidget(row, row_pos + 1, col)
            row_idx[current_group] += 1

        # 添加最后一组
        if group_widget:
            v.addWidget(group_widget)
    else:
        empty = QLabel('本次分析未给出概率统计。')
        empty.setStyleSheet(
            f"color: {Colors.TEXT3}; font-size: {Fonts.SZ_BODY}; "
            f"font-family: {Fonts.BODY};")
        empty.setAlignment(Qt.AlignCenter)
        v.addWidget(empty)

    return container


# ---------------------------------------------------------------------------
# 强调色 → 浅色底（部分主题色无 *_GLOW，用 *_LIGHT 顶替）
# ---------------------------------------------------------------------------
_GLOW_MAP = {
    Colors.LIUJIN: Colors.LIUJIN_GLOW,
    Colors.QINGHUA: Colors.QINGHUA_GLOW,
    Colors.ZHUSHA: Colors.ZHUSHA_GLOW,
    Colors.SUCCESS: Colors.SUCCESS_LIGHT,
    Colors.WARNING: Colors.WARNING_LIGHT,
    Colors.DANGER: Colors.DANGER_LIGHT,
    Colors.INFO: Colors.INFO_LIGHT,
}


def _glow(color):
    """返回强调色对应的浅色底，用于色块背景。"""
    return _GLOW_MAP.get(color, Colors.LIUJIN_GLOW)


def _build_explanation_box(dimension_labels, color=Colors.LIUJIN) -> QWidget:
    """概率统计的「如何理解这些数据？」说明块：含义 / 计算维度 / 实际用途。

    说明块置于各维度卡片上方，帮助用户理解所列强弱判断的依据，而非孤立标签。
    """
    box = QFrame()
    box.setStyleSheet(f"""
        QFrame {{
            background: {_glow(color)};
            border-left: 4px solid {color};
            border-radius: {Spacing.RADIUS_SM};
        }}
    """)
    bl = QVBoxLayout(box)
    bl.setContentsMargins(Spacing.S3, Spacing.S_MARGIN_XS, Spacing.S3, Spacing.S_MARGIN_XS)
    bl.setSpacing(Spacing.S2)

    head = QLabel('📜 如何理解这些批断？')
    head.setStyleSheet(
        f"font-size: {Fonts.SZ_SMALL}; font-weight: {Fonts.W_MEDIUM}; "
        f"color: {color}; font-family: {Fonts.BODY};")
    bl.addWidget(head)

    dims = '、'.join(dimension_labels) if dimension_labels else '各维度'
    lines = [
        f'含义：以上为龙虎山大师兄据命主八字推演所得的趋势强弱判断，每维度以「强 / 中 / 弱」呈现。',
        f'涉及维度：{dims}（按命局结构自动给出）。',
        '实际用途：用于直观对比命主各维度走势、辅助整体判断；非统计采样结果，仅供文化研究参考。',
    ]
    for ln in lines:
        t = QLabel(ln)
        t.setWordWrap(True)
        t.setStyleSheet(
            f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT2}; "
            f"font-family: {Fonts.BODY}; line-height: 1.6;")
        bl.addWidget(t)
    return box


def _build_strength_legend(color: str = Colors.LIUJIN) -> QWidget:
    """返回强度图例：胶囊芯片风格，带悬停高亮。"""
    container = QFrame()
    container.setStyleSheet(f"""
        QFrame {{
            background: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            padding: 6px 8px;
        }}
    """)
    main = QHBoxLayout(container)
    main.setContentsMargins(Spacing.S2, Spacing.S_PAD_SM, Spacing.S2, Spacing.S_PAD_SM)
    main.setSpacing(Spacing.S3)

    title = QLabel('强度')
    title.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; font-weight:{Fonts.W_MEDIUM}; color:{color};")
    title.setAlignment(Qt.AlignVCenter)
    main.addWidget(title)

    def chip(bg, text):
        w = QFrame()
        w.setStyleSheet(f"""
            QFrame {{
                background: {bg}20;
                border: 1px solid {bg}55;
                border-radius: 10px;
                padding: 2px 8px;
            }}
            QFrame:hover {{
                background: {bg}35;
                border-color: {bg};
            }}
        """)
        h = QHBoxLayout(w)
        h.setContentsMargins(Spacing.S_MIN, Spacing.S0, Spacing.S_MIN, Spacing.S0)
        h.setSpacing(Spacing.S1)
        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background:{bg}; border-radius:4px;")
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT}; font-family:{Fonts.BODY};")
        h.addWidget(dot)
        h.addWidget(lbl)
        return w

    main.addWidget(chip(Colors.SUCCESS, '强'))
    main.addWidget(chip(Colors.WARNING, '中'))
    main.addWidget(chip(Colors.DANGER, '弱'))
    main.addStretch()
    return container


def conclusion_block(text: str, color=Colors.LIUJIN) -> QWidget:
    """整体结论高亮块 v2.1/v2.2：粗金边 + 强调色底 + 「🎯 整体结论」标题 + 情感徽章 + 段落/代码正文。

    v2.2（M3-4）：正文改用 paragraph_block（分段落 + 超宽居中）与 code_block
    （代码块），长文本可读、代码等宽可选中、段落不黏连（修 Q09）。

    Args:
        text:    整体结论正文（含 ``` 围栏代码片段）。
        color:   强调色。

    Returns:
        可直接 addWidget 的 QWidget。
    """
    score, _, _ = _compute_sentiment(text)

    box = QFrame()
    box.setStyleSheet(f"""
        QFrame {{
            background: {_glow(color)};
            border-left: 8px solid {color};
            border-top: 2px solid {color};
            border-radius: {Spacing.RADIUS_SM};
        }}
    """)
    bl = QVBoxLayout(box)
    bl.setContentsMargins(Spacing.S_PAD_XS, Spacing.S3, Spacing.S_PAD_XS, Spacing.S3)
    bl.setSpacing(Spacing.S2)

    # 标题行
    header_row = QHBoxLayout()
    header_row.setSpacing(Spacing.S2)
    head = QLabel('🎯 整体结论')
    head.setStyleSheet(
        f"font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD}; "
        f"color: {color}; font-family: {Fonts.TITLE};")
    header_row.addWidget(head)
    header_row.addWidget(_create_sentiment_badge(score))
    header_row.addStretch()
    bl.addLayout(header_row)

    # 正文：切分段落/代码，逐块渲染（M3-4 a）
    blocks = _split_blocks(text)
    max_width = Spacing.COL_MAX_TEXT
    for blk in blocks:
        kind, content = blk
        if kind == 'code':
            block_widget = code_block(content, language='AI')
            block_widget.setObjectName('conclusion_code')
            bl.addWidget(block_widget)
        else:
            para = content
            block_widget = paragraph_block(para, max_width=max_width, highlight=False)
            block_widget.setObjectName('conclusion_para')
            bl.addWidget(block_widget)
    return box


def suggestion_block(items, color=Colors.SUCCESS) -> QWidget:
    """核心建议高亮块 v2.1：粗绿边 + 浅绿底 + 「💡 核心建议」标题 + 情感徽章 + 关键词高亮逐条列表。"""
    if isinstance(items, str):
        items = [items]
    full_text = '\n'.join(str(item) for item in items or [] if item and str(item).strip())
    score, _, _ = _compute_sentiment(full_text)

    box = QFrame()
    box.setStyleSheet(f"""
        QFrame {{
            background: {_glow(color)};
            border-left: 8px solid {color};
            border-top: 2px solid {color};
            border-radius: {Spacing.RADIUS_SM};
        }}
    """)
    bl = QVBoxLayout(box)
    bl.setContentsMargins(Spacing.S_PAD_XS, Spacing.S3, Spacing.S_PAD_XS, Spacing.S3)
    bl.setSpacing(Spacing.S2)

    # 标题行
    header_row = QHBoxLayout()
    header_row.setSpacing(Spacing.S2)
    head = QLabel('💡 核心建议')
    head.setStyleSheet(
        f"font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD}; "
        f"color: {color}; font-family: {Fonts.TITLE};")
    header_row.addWidget(head)
    header_row.addWidget(_create_sentiment_badge(score))
    header_row.addStretch()
    bl.addLayout(header_row)

    for item in items or []:
        if not item or not str(item).strip():
            continue
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(Spacing.S2)
        dot = QLabel('•')
        dot.setStyleSheet(
            f"color: {color}; font-size: {Fonts.SZ_BODY}; "
            f"font-weight: {Fonts.W_BOLD}; font-family: {Fonts.BODY};")
        dot.setFixedWidth(14)
        dot.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        txt = QLabel()
        txt.setWordWrap(True)
        txt.setTextFormat(Qt.RichText)
        txt.setOpenExternalLinks(False)
        txt.setText(_highlight_keywords_in_text(str(item).strip(), color))
        txt.setStyleSheet(
            f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; "
            f"font-family: {Fonts.BODY}; line-height: 1.7;")
        rl.addWidget(dot)
        rl.addWidget(txt, 1)
        bl.addWidget(row)
    return box


# =====================================================================
# 关键词高亮系统：风险词 / 正面词 / 情感评分
# =====================================================================
# 风险关键词（负面/警示）
_RISK_KEYWORDS = (
    # 通用
    '忌', '避', '凶', '慎', '危', '不宜', '切忌', '规避', '少', '减', '防', '勿', '禁',
    '克', '冲', '破', '害', '刑', '空亡', '劫煞', '灾煞', '病符', '丧门', '吊客',
    '官非', '口舌', '破财', '漏财', '阻滞', '延迟', '受阻', '不利', '欠佳', '薄弱',
    '亏损', '损耗', '衰退', '下滑', '低迷', '动荡', '波折', '坎坷', '险阻',
    # 六壬术语偏负向/需留意
    '鬼', '墓', '绝', '死', '病', '囚', '死气', '绝气', '墓库',
    '刑克', '冲克', '刑害', '空绝', '暗鬼', '克害', '克应', '刑冲',
    # 命理纳音等
    '剑锋', '流霞', '阴差阳错', '孤辰', '寡宿', '十恶大败',
)

# 正面关键词（正面/吉利）
_POSITIVE_KEYWORDS = (
    '吉', '宜', '利', '旺', '强', '好', '顺', '昌', '盛', '兴', '隆', '达', '通', '亨',
    '贵', '福', '禄', '寿', '喜', '庆', '祥', '瑞', '和', '合', '成', '就', '得', '获',
    '富', '贵', '荣', '华', '显', '扬', '发', '旺', '相', '生', '扶', '助', '拱', '照',
    '贵人', '天乙', '文昌', '天德', '月德', '福星', '禄神', '驿马', '将星', '华盖',
    '逢凶化吉', '转危为安', '有救', '可为', '大吉', '上吉', '中吉', '小吉',
    '顺遂', '圆满', '美满', '亨通', '旺盛', '兴旺', '繁荣', '富足', '康健', '安宁',
    # 命理/六壬术语偏正向
    '身强', '身旺', '从旺', '专旺', '流通', '生化', '得令', '得地', '得势',
    '财官双美', '食神生财', '伤官佩印', '比劫帮身', '印旺', '官印相生',
    '长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养',
    '青龙', '太常', '六合', '太阴', '勾陈', '天空', '贵人', '日禄',
)

# 中性/描述性关键词（用于情感分析权重调整）
_NEUTRAL_KEYWORDS = (
    '平', '中', '常', '稳', '守', '维持', '现状', '不变', '般', '普通', '正常',
    '论', '见', '以', '而', '则', '之', '其',
)


def _compute_sentiment(text: str) -> Tuple[float, List[str], List[str]]:
    """计算文本情感得分：返回 (score, matched_risk, matched_positive)。
    score: -1.0(极负面) 到 +1.0(极正面)
    """
    risk_matches = [kw for kw in _RISK_KEYWORDS if kw in text]
    pos_matches = [kw for kw in _POSITIVE_KEYWORDS if kw in text]
    neutral_matches = [kw for kw in _NEUTRAL_KEYWORDS if kw in text]

    risk_score = -len(risk_matches) * 0.15
    pos_score = len(pos_matches) * 0.12
    neutral_score = -len(neutral_matches) * 0.02  # 中性词略微降低正面倾向

    total = risk_score + pos_score + neutral_score
    return max(-1.0, min(1.0, total)), risk_matches, pos_matches


def _highlight_keywords_in_text(text: str, color: str = Colors.LIUJIN) -> str:
    """在文本中为关键词添加 HTML 高亮标记（用于 QLabel 的富文本显示）。"""
    import html
    escaped = html.escape(text)

    # 高亮风险词（红色加粗）
    for kw in _RISK_KEYWORDS:
        if kw in escaped:
            escaped = escaped.replace(
                kw,
                f'<span style="color:{Colors.DANGER}; font-weight:bold; background:{Colors.DANGER_LIGHT}; padding:0 2px; border-radius:2px;">{kw}</span>'
            )

    # 高亮正面词（绿色加粗）
    for kw in _POSITIVE_KEYWORDS:
        if kw in escaped:
            escaped = escaped.replace(
                kw,
                f'<span style="color:{Colors.SUCCESS}; font-weight:bold; background:{Colors.SUCCESS_LIGHT}; padding:0 2px; border-radius:2px;">{kw}</span>'
            )

    # T5.4 古籍引用高亮：《书名》→ 古金色斜体
    # 注：replacement 必须用 lambda（不能用 r-string）——r-string 不是 f-string，
    # {Colors.LIUJIN} 会原样输出到 HTML 导致 CSS 静默失效（曾长期存在的 bug）。
    # lambda 方案同时规避 \1 在 f-string 中被解释为八进制转义的陷阱。
    import re as _re
    escaped = _re.sub(
        r'(《[^》]+》)',
        lambda m: (f'<em style="color:{Colors.LIUJIN}; font-style:italic;">'
                   f'{m.group(1)}</em>'),
        escaped,
    )

    return escaped


# ---------------------------------------------------------------------------
# 文本块切分：段落 / 代码围栏
# ---------------------------------------------------------------------------
_CODE_FENCE_RE = re.compile(r'```[a-zA-Z0-9]*\n(.*?)```', re.S)


def _split_blocks(text: str) -> list:
    """把文本切成 [('p', 段落文本) | ('code', 代码文本)] 序列。

    识别 ``` 围栏：围栏前的文本按 \\n 分段为段落；围栏代码内容切为
    ('code', 代码文本)；围栏后的文本按 \\n 分段为段落。无围栏时按段落切分。

    围栏不匹配时（如 ``` 开头无闭合）整体按段落处理，绝不抛异常。

    Args:
        text:    待切分的文本。

    Returns:
        段落/代码元组列表，元素为 ('p', str) 或 ('code', str)。
    """
    if not text:
        return [('p', '')]

    blocks = []
    last_pos = 0
    fence_re = _CODE_FENCE_RE
    for m in fence_re.finditer(text):
        # 围栏前的文本按 \\n 分段为段落
        pre_text = text[last_pos:m.start()]
        for para in pre_text.split('\n'):
            if para.strip():
                blocks.append(('p', para))
        # 围栏代码内容：去掉结尾换行，作为独立代码块
        code_text = m.group(1).rstrip('\n')
        blocks.append(('code', code_text))
        last_pos = m.end()

    # 围栏之后的文本按 \\n 分段为段落
    post_text = text[last_pos:]
    for para in post_text.split('\n'):
        if para.strip():
            blocks.append(('p', para))

    return blocks


def _create_sentiment_badge(score: float) -> QWidget:
    """创建情感评分徽章：-1.0 到 +1.0 映射为颜色和标签。"""
    badge = QLabel()
    badge.setFixedHeight(20)
    badge.setAlignment(Qt.AlignCenter)

    if score >= 0.5:
        label, bg, fg = '🌟 极吉', Colors.SUCCESS, Colors.SUCCESS
    elif score >= 0.2:
        label, bg, fg = '✨ 吉', Colors.SUCCESS_LIGHT, Colors.SUCCESS
    elif score >= -0.1:
        label, bg, fg = '⚖ 平', Colors.WARNING_LIGHT, Colors.WARNING
    elif score >= -0.4:
        label, bg, fg = '⚠ 凶', Colors.DANGER_LIGHT, Colors.DANGER
    else:
        label, bg, fg = '☠ 大凶', Colors.DANGER, Colors.TEXT_INV

    badge.setText(label)
    badge.setStyleSheet(f"""
        background: {bg}; color: {fg};
        font-size: {Fonts.SZ_MICRO}; font-weight: {Fonts.W_BOLD};
        border-radius: {Spacing.RADIUS_SM}; padding: 2px 8px;
        font-family: {Fonts.BODY};
    """)
    return badge


def risk_aware_label(text: str, color=Colors.LIUJIN, show_sentiment: bool = True) -> QWidget:
    """重点提示块 v2.1：自带「【重点提示】」标题 + 情感评分徽章；
    关键词内联高亮（风险词红、正面词绿）；行级风险标记；支持列表/字符串输入。"""
    container = QFrame()
    container.setStyleSheet(f"""
        QFrame {{
            background: {_glow(color)};
            border-left: 8px solid {color};
            border-top: 2px solid {color};
            border-radius: {Spacing.RADIUS_SM};
        }}
    """)
    cl = QVBoxLayout(container)
    cl.setContentsMargins(Spacing.S3, Spacing.S_MARGIN_XS, Spacing.S3, Spacing.S_MARGIN_XS)
    cl.setSpacing(Spacing.S2)

    # 标题行：标题 + 情感徽章
    header_row = QHBoxLayout()
    header_row.setSpacing(Spacing.S2)
    title = QLabel('⭐ 【重点提示】')
    title.setStyleSheet(
        f"font-size: {Fonts.SZ_BODY}; font-weight: {Fonts.W_MEDIUM}; "
        f"color: {color}; font-family: {Fonts.BODY};")
    header_row.addWidget(title)

    if show_sentiment and isinstance(text, str):
        full_text = text
    elif show_sentiment and isinstance(text, (list, tuple)):
        full_text = '\n'.join(str(x) for x in text if x and str(x).strip())
    else:
        full_text = ''

    if full_text and show_sentiment:
        score, _, _ = _compute_sentiment(full_text)
        header_row.addWidget(_create_sentiment_badge(score))
    header_row.addStretch()
    cl.addLayout(header_row)

    if isinstance(text, (list, tuple)):
        lines = [str(x) for x in text if x and str(x).strip()]
    else:
        lines = [ln for ln in str(text).split('\n') if ln.strip()]

    for ln in lines:
        ln = ln.strip()
        is_risk = any(kw in ln for kw in _RISK_KEYWORDS)
        is_positive = any(kw in ln for kw in _POSITIVE_KEYWORDS)

        # 行容器
        row = QFrame()
        if is_risk and not is_positive:
            row.setStyleSheet(f"""
                QFrame {{
                    background: {Colors.DANGER_LIGHT};
                    border-left: 3px solid {Colors.DANGER};
                    border-radius: {Spacing.RADIUS_SM};
                }}
            """)
        elif is_positive and not is_risk:
            row.setStyleSheet(f"""
                QFrame {{
                    background: {Colors.SUCCESS_LIGHT};
                    border-left: 3px solid {Colors.SUCCESS};
                    border-radius: {Spacing.RADIUS_SM};
                }}
            """)
        else:
            row.setStyleSheet(f"""
                QFrame {{
                    background: transparent;
                    border-left: 3px solid {Colors.BORDER};
                    border-radius: {Spacing.RADIUS_SM};
                }}
            """)

        sl = QHBoxLayout(row)
        sl.setContentsMargins(Spacing.S2, Spacing.S_PAD_SM, Spacing.S2, Spacing.S_PAD_SM)
        sl.setSpacing(Spacing.S2)

        # 图标前缀
        if is_risk and not is_positive:
            icon = QLabel('⚠')
            icon_color = Colors.DANGER
        elif is_positive and not is_risk:
            icon = QLabel('✦')
            icon_color = Colors.SUCCESS
        else:
            icon = QLabel('•')
            icon_color = Colors.TEXT3

        icon.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {icon_color};")
        icon.setFixedWidth(16)
        icon.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        sl.addWidget(icon)

        # 富文本内容（关键词高亮）
        rt = QLabel()
        rt.setWordWrap(True)
        rt.setTextFormat(Qt.RichText)
        rt.setOpenExternalLinks(False)
        rt.setText(_highlight_keywords_in_text(ln, color))
        rt.setStyleSheet(
            f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; "
            f"font-family: {Fonts.BODY}; line-height: 1.6;")
        sl.addWidget(rt, 1)
        cl.addWidget(row)

    return container


# =====================================================================
# v2.2 新增：章节卡片头部 + 升级免责声明 + 锚点组件
# =====================================================================

def ai_section_card_header(
    index: int,
    title: str,
    icon: str,
    color: str = Colors.LIUJIN,
    anchor_id: Optional[str] = None,
) -> QWidget:
    """章节卡片标题头 v2.2：序号徽章 + 大标题 + 装饰性边条。

    取代 CollapsibleCard 默认的简单标题行，提供更强的视觉层次：
    - 左侧 4px 渐变色条（从粗到细渐隐）
    - 序号圆形徽章（带阴影感）
    - 大标题 + 图标
    - 右侧可选副标题/字数

    Args:
        index: 章节序号（从 1 开始）
        title: 章节标题
        icon: 章节图标
        color: 主题强调色
        anchor_id: 锚点 ID（设置后标题区有 anchor_id objectName，用于导航跳转）

    Returns:
        可直接 addWidget 的 QWidget（标题容器）
    """
    container = QFrame()
    if anchor_id:
        container.setObjectName(anchor_id)
    container.setStyleSheet('background: transparent; border: none;')

    h = QHBoxLayout(container)
    h.setContentsMargins(Spacing.S0, Spacing.S1, Spacing.S0, Spacing.S2)
    h.setSpacing(Spacing.S3)
    h.setAlignment(Qt.AlignVCenter)

    # 渐变色条（立体感）
    bar = QFrame()
    bar.setFixedSize(4, 28)
    bar.setStyleSheet(f"""
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {color}, stop:1 {color}55);
        border: none;
        border-radius: 2px;
    """)
    h.addWidget(bar)

    # 序号徽章（圆形）
    badge = QFrame()
    badge.setFixedSize(30, 30)
    badge.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {color}, stop:1 {color}DD);
            border: 1.5px solid {color}66;
            border-radius: 15px;
        }}
    """)
    bl = QVBoxLayout(badge)
    bl.setContentsMargins(0, 0, 0, 0)
    bl.setAlignment(Qt.AlignCenter)
    num = QLabel(f'{index:02d}')
    num.setAlignment(Qt.AlignCenter)
    num.setStyleSheet(f"""
        color: white;
        font-size: 12px;
        font-weight: {Fonts.W_BOLD};
        font-family: {Fonts.MONO};
        background: transparent;
        border: none;
    """)
    bl.addWidget(num)
    h.addWidget(badge)

    # 图标 + 标题
    title_col = QVBoxLayout()
    title_col.setSpacing(Spacing.S0)
    title_col.setAlignment(Qt.AlignVCenter)

    if icon:
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 15px; color: {color}; background: transparent;")
        icon_lbl.setFixedHeight(20)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            font-size: 15px;
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
            letter-spacing: 0.5px;
            background: transparent;
        """)

        title_row = QHBoxLayout()
        title_row.setSpacing(Spacing.S2)
        title_row.setAlignment(Qt.AlignVCenter)
        title_row.addWidget(icon_lbl)
        title_row.addWidget(title_lbl)
        title_row.addStretch()

        title_col.addLayout(title_row)
    else:
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            font-size: 15px;
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
            letter-spacing: 0.5px;
            background: transparent;
        """)
        title_col.addWidget(title_lbl)

    h.addLayout(title_col, 1)

    return container


def disclaimer_card(text: str = '') -> QWidget:
    """免责声明卡片 v2.2：双边框 + 警示条纹底 + 详细分条说明 + 图标点缀。

    升级点：
    - 顶部红色警示条纹 + 卡片外框双层边框
    - 「⚠ 免责声明」大标题 + 「使用须知」副标题
    - 默认三条核心声明（文化研究 / 非决策依据 / 专业咨询）
    - 支持传入自定义追加说明

    Args:
        text: 自定义追加说明（可选，将以「补充说明」形式追加）

    Returns:
        可直接 addWidget 的 QWidget（免责声明卡片）
    """
    container = QFrame()
    container.setStyleSheet(f"""
        QFrame {{
            background: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-left: 6px solid {Colors.WARNING};
            border-radius: {Spacing.RADIUS};
        }}
    """)

    v = QVBoxLayout(container)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(Spacing.S0)

    # 顶部警示条纹
    stripe = QFrame()
    stripe.setFixedHeight(3)
    stripe.setStyleSheet(f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {Colors.WARNING}, stop:0.5 {Colors.DANGER}, stop:1 {Colors.WARNING});
        border: none;
        border-top-left-radius: {Spacing.RADIUS};
        border-top-right-radius: {Spacing.RADIUS};
    """)
    v.addWidget(stripe)

    # 内容区
    content = QFrame()
    content.setStyleSheet('background: transparent; border: none;')
    cl = QVBoxLayout(content)
    cl.setContentsMargins(Spacing.S4, Spacing.S3, Spacing.S4, Spacing.S3)
    cl.setSpacing(Spacing.S3)

    # 标题行
    title_row = QHBoxLayout()
    title_row.setSpacing(Spacing.S2)
    title_row.setAlignment(Qt.AlignVCenter)

    icon_lbl = QLabel('⚠')
    icon_lbl.setStyleSheet(f"font-size: 17px; color: {Colors.WARNING};")
    icon_lbl.setFixedWidth(22)

    title_col = QVBoxLayout()
    title_col.setSpacing(Spacing.S0)
    title = QLabel('免责声明')
    title.setStyleSheet(f"""
        font-size: 15px;
        font-weight: {Fonts.W_BOLD};
        color: {Colors.WARNING};
        font-family: {Fonts.TITLE};
        background: transparent;
    """)
    sub = QLabel('使用须知 · Disclaimer')
    sub.setStyleSheet(f"""
        font-size: 11px;
        color: {Colors.TEXT3};
        font-family: {Fonts.BODY};
        background: transparent;
    """)
    title_col.addWidget(title)
    title_col.addWidget(sub)

    title_row.addWidget(icon_lbl)
    title_row.addLayout(title_col, 1)

    tag = QLabel('必读')
    tag.setStyleSheet(f"""
        background: {Colors.WARNING};
        color: white;
        font-size: 11px;
        font-weight: {Fonts.W_BOLD};
        padding: 2px 8px;
        border-radius: 8px;
        font-family: {Fonts.BODY};
    """)
    title_row.addWidget(tag)

    cl.addLayout(title_row)

    # 分隔细线
    div = QFrame()
    div.setFixedHeight(1)
    div.setStyleSheet(f'background: {Colors.DIVIDER}; border: none;')
    cl.addWidget(div)

    # 默认三条核心声明
    default_items = [
        ('📚', '仅供文化研究', '本结果基于传统命理算法与 AI 大模型生成，仅用于中国传统文化研究与学习参考，'),
        ('🚫', '非决策依据', '命理推演不具备科学决策效力，不构成医疗、法律、投资、婚恋等任何重大事项的决策依据。'),
        ('💼', '专业问题咨询专业人士', '涉及健康、法律、投资等专业领域，请咨询具有资质的专业人士。'),
    ]

    for emoji, head, body in default_items:
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        row.setAlignment(Qt.AlignTop)
        e = QLabel(emoji)
        e.setStyleSheet('font-size: 13px;')
        e.setFixedWidth(20)
        e.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        body_w = QLabel()
        body_w.setWordWrap(True)
        body_w.setTextFormat(Qt.RichText)
        body_w.setOpenExternalLinks(False)
        body_w.setText(
            f'<span style="font-weight:bold; color:{Colors.TEXT};">{head}：</span>'
            f'<span style="color:{Colors.TEXT2};">{body}</span>'
        )
        body_w.setStyleSheet(
            f"font-size: {Fonts.SZ_SMALL}; font-family: {Fonts.BODY}; line-height: 1.7;"
        )
        row.addWidget(e)
        row.addWidget(body_w, 1)
        cl.addLayout(row)

    # 用户自定义追加说明
    custom = (text or '').strip()
    if custom:
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet(f'background: {Colors.DIVIDER}; border: none;')
        cl.addWidget(div2)

        ct_lbl = QLabel('📝 补充说明')
        ct_lbl.setStyleSheet(f"""
            font-size: 12px;
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.WARNING};
            font-family: {Fonts.BODY};
            background: transparent;
        """)
        cl.addWidget(ct_lbl)

        ct_body = QLabel(custom)
        ct_body.setWordWrap(True)
        ct_body.setTextFormat(Qt.RichText)
        ct_body.setOpenExternalLinks(False)
        ct_body.setText(_highlight_keywords_in_text(custom, Colors.WARNING))
        ct_body.setStyleSheet(
            f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT2}; "
            f"font-family: {Fonts.BODY}; line-height: 1.6;"
        )
        cl.addWidget(ct_body)

    v.addWidget(content)
    return container


# =====================================================================
# 整体结论结构化辅助：分段 / 关键句抽取
# 仅影响「展示结构」（层次、段落、要点高亮），不增删/改写任何原文语义，
# 保证龙虎山大师兄结论的准确性不变。
# =====================================================================
def _split_conclusion_sentences(text: str) -> List[str]:
    """把结论文本切成句子（保留句末标点，含分句号；；以保证原文一字不丢）。

    用于分段与要点抽取；句末标点（。！？!?；;）均随句保留，确保结论准确性不变。
    """
    if not text:
        return []
    parts = re.split(r'([。！？!?；;])', text)
    out: List[str] = []
    buf = ''
    for p in parts:
        buf += p
        if p in '。！？!?；;':
            s = buf.strip()
            if s:
                out.append(s)
            buf = ''
    if buf.strip():
        out.append(buf.strip())
    return out


def _split_conclusion_paragraphs(text: str) -> List[str]:
    """把整体结论文本规范化分段：保留 AI 原始换行；无换行时长句按 ~3 句一组自动分段。

    不增删文字，仅调整展示层次，保证结论准确性不变。
    """
    raw = (text or '').strip()
    if not raw:
        return []
    blocks = [b.strip() for b in raw.split('\n') if b.strip()]
    if len(blocks) >= 2:
        return blocks
    # 单段长文：按句分组，每组约 3 句，避免一整块密排难以阅读
    sents = _split_conclusion_sentences(raw)
    if len(sents) <= 3:
        return [raw]
    paras: List[str] = []
    for i in range(0, len(sents), 3):
        paras.append(''.join(sents[i:i + 3]))
    return paras


def _extract_conclusion_keypoints(text: str, max_n: int = 3) -> List[str]:
    """从结论中抽取最具决定性的要点句（含吉/凶等强信号词），跳过首句以免与核心论断重复。

    仅用于「速读」展示，不改动原文；正文中仍含完整句子。
    """
    sents = _split_conclusion_sentences(text)
    if len(sents) <= 1:
        return []
    scored = []
    for s in sents[1:]:  # 跳首句（作为核心论断单独展示）
        if len(s) < 6:
            continue
        pos = sum(1 for kw in _POSITIVE_KEYWORDS if kw in s)
        neg = sum(1 for kw in _RISK_KEYWORDS if kw in s)
        score = pos + neg
        if score > 0:
            scored.append((score, s))
    scored.sort(key=lambda x: (-x[0], len(x[1])))
    seen: set = set()
    out: List[str] = []
    for _score, s in scored:
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
        if len(out) >= max_n:
            break
    return out


def _build_conclusion_keypoints(items: List[str], color: str) -> QWidget:
    """渲染「关键要点」卡片：浅色底 + 左色条 + 逐项要点（关键词高亮）。"""
    box = QFrame()
    box.setStyleSheet(f"""
        QFrame {{
            background: {_glow(color)};
            border-left: 4px solid {color};
            border-radius: {Spacing.RADIUS_SM};
        }}
    """)
    bl = QVBoxLayout(box)
    bl.setContentsMargins(Spacing.S3, Spacing.S_MARGIN_XS, Spacing.S3, Spacing.S_MARGIN_XS)
    bl.setSpacing(Spacing.S2)

    head = QLabel('✨ 关键要点')
    head.setStyleSheet(
        f"font-size: 13px; font-weight: {Fonts.W_BOLD}; "
        f"color: {color}; font-family: {Fonts.TITLE}; letter-spacing: 0.5px;"
    )
    bl.addWidget(head)

    for s in items:
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        row.setAlignment(Qt.AlignTop)
        dot = QLabel('▸')
        dot.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: {Fonts.W_BOLD};"
        )
        dot.setFixedWidth(14)
        dot.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        t = QLabel()
        t.setWordWrap(True)
        t.setTextFormat(Qt.RichText)
        t.setOpenExternalLinks(False)
        t.setText(_highlight_keywords_in_text(s, color))
        t.setStyleSheet(
            f"font-size: 13px; color: {Colors.TEXT_INV}; "
            f"font-family: {Fonts.BODY}; line-height: 1.7;"
        )
        row.addWidget(dot)
        row.addWidget(t, 1)
        bl.addLayout(row)
    return box


def hero_conclusion_block(text: str, color: str = Colors.LIUJIN) -> QWidget:
    """hero 整体结论块 v2.3：高级视觉权重的总结性 hero 卡片（可读性优化版）。

    升级点（v2.3，仅改展示结构，不改结论语义）：
    - 双层渐变背景 + 顶部/底部装饰双金线（视觉权重最高）
    - 「🎯 整体结论」hero 标题 + 古籍副标题 + 情感徽章
    - 「✨ 关键要点」速读卡：抽取最具决定性的结论句（吉/凶强信号），
      左色条 + 圆点列表 + 关键词高亮，便于一眼抓住重点（已排除首句以免与核心论断重复）
    - 正文按段落结构化渲染：保留 AI 原始换行；无换行长文按 ~3 句自动分段；
      首段作为「核心论断」略放大加粗建立层级，后续段落统一字号/行距，规范间距
    - 关键词内联高亮贯穿始终，字体统一为 BODY 家族，行距 1.9 舒适易读

    Args:
        text: 整体结论正文
        color: 强调色（默认鎏金；梅花易数面板传入青花蓝）

    Returns:
        可直接 addWidget 的 QWidget（hero 结论块）
    """
    score, _, _ = _compute_sentiment(text)

    box = QFrame()
    box.setStyleSheet(f"""
        QFrame {{
            # M3-3（Q05）：背景由浅色 #FFF9E8 渐变改为深色卡片语言，消除浅色孤岛
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {Colors.CARD_HOVER},
                stop:0.5 {Colors.CARD},
                stop:1 {Colors.CARD});
            border: 1.5px solid {Colors.LIUJIN_LIGHT};
            border-radius: {Spacing.RADIUS_LG};
        }}
    """)
    bl = QVBoxLayout(box)
    bl.setContentsMargins(Spacing.S5, Spacing.S4, Spacing.S5, Spacing.S4)
    bl.setSpacing(Spacing.S3)

    # 顶部装饰双线
    line_top = QFrame()
    line_top.setFixedHeight(2)
    line_top.setStyleSheet(
        f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        f"stop:0 transparent, stop:0.5 {Colors.LIUJIN}, stop:1 transparent); "
        f"border: none;"
    )
    bl.addWidget(line_top)

    # 标题行
    header_row = QHBoxLayout()
    header_row.setSpacing(Spacing.S3)
    header_row.setAlignment(Qt.AlignVCenter)

    head_col = QVBoxLayout()
    head_col.setSpacing(Spacing.S0)
    head = QLabel('🎯 整体结论')
    head.setStyleSheet(
        f"font-size: {Fonts.FS_H3}px; font-weight: {Fonts.W_BOLD}; "
        f"color: {Colors.LIUJIN_DARK}; font-family: {Fonts.TITLE}; "
        f"letter-spacing: 1px;")
    # T5.1 古籍副标题：动态检测正文中的《书名》引用，否则回退默认文案
    import re as _re
    books = _re.findall(r'《([^》]+)》', text)
    if books:
        sub_text = '· 基于《' + '》《'.join(books[:3]) + '》等古籍参校 ·'
    else:
        sub_text = '· 龙虎山大师兄核心论断 ·'
    sub = QLabel(sub_text)
    sub.setStyleSheet(
        f"font-size: 11px; color: {Colors.TEXT3}; "
        f"font-family: {Fonts.BODY}; letter-spacing: 0.5px;"
    )
    head_col.addWidget(head)
    head_col.addWidget(sub)

    header_row.addLayout(head_col, 1)
    header_row.addWidget(_create_sentiment_badge(score))
    bl.addLayout(header_row)

    # 分隔线
    div = QFrame()
    div.setFixedHeight(1)
    div.setStyleSheet(
        f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        f"stop:0 {Colors.LIUJIN_LIGHT}, stop:1 transparent); "
        f"border: none;"
    )
    bl.addWidget(div)

    # 关键要点：抽取最具决定性的结论句，便于快速浏览（与正文不重复核心论断）
    key_points = _extract_conclusion_keypoints(text, max_n=3)
    if key_points:
        bl.addWidget(_build_conclusion_keypoints(key_points, color))
        kp_div = QFrame()
        kp_div.setFixedHeight(1)
        kp_div.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 {Colors.LIUJIN_LIGHT}, stop:1 transparent); border: none;"
        )
        bl.addWidget(kp_div)

    # 正文：按段落结构化渲染（保留 AI 原始换行 / 长句自动分段），层次分明、便于细读
    paragraphs = _split_conclusion_paragraphs(text)
    for idx, para in enumerate(paragraphs):
        para_rich = _highlight_keywords_in_text(para, color)
        lbl = QLabel()
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.RichText)
        lbl.setOpenExternalLinks(False)
        lbl.setText(para_rich)
        if idx == 0:
            # 首段作为「核心论断」，略放大加粗，建立视觉层级
            lbl.setStyleSheet(
                f"font-size: {Fonts.FS_BODY}px; font-weight: {Fonts.W_MEDIUM}; "
                f"color: {Colors.TEXT}; font-family: {Fonts.BODY}; "
                f"line-height: {Spacing.LINE_HEIGHT_BODY}; padding: 2px 0;"
            )
        else:
            lbl.setStyleSheet(
                f"font-size: {Fonts.FS_BODY}px; color: {Colors.TEXT}; "
                f"font-family: {Fonts.BODY}; line-height: {Spacing.LINE_HEIGHT_BODY}; "
                f"padding: 2px 0;"
            )
        bl.addWidget(lbl)

    # 底部装饰双线
    line_bot = QFrame()
    line_bot.setFixedHeight(2)
    line_bot.setStyleSheet(
        f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        f"stop:0 transparent, stop:0.5 {Colors.LIUJIN}, stop:1 transparent); "
        f"border: none;"
    )
    bl.addWidget(line_bot)

    return box


def rich_list_block(items: List[str], color: str = Colors.QINGHUA, title: str = '', icon: str = '') -> QWidget:
    """强化版列表块 v2.2：编号 + 引述竖线 + 关键词高亮。

    替代原有扁平化列表，提供：
    - 序号（01、02、03...）
    - 引述竖线（左侧彩色）
    - 富文本关键词高亮

    Args:
        items: 字符串列表
        color: 强调色
        title: 列表标题（可选）
        icon: 标题图标（可选）

    Returns:
        可直接 addWidget 的 QWidget
    """
    container = QFrame()
    container.setStyleSheet(f"""
        QFrame {{
            background: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-left: 4px solid {color};
            border-radius: {Spacing.RADIUS};
        }}
    """)
    cl = QVBoxLayout(container)
    cl.setContentsMargins(Spacing.S4, Spacing.S3, Spacing.S4, Spacing.S3)
    cl.setSpacing(Spacing.S2)

    if title:
        head = QLabel(f'{icon} {title}' if icon else title)
        head.setStyleSheet(f"""
            font-size: 13px;
            font-weight: {Fonts.W_BOLD};
            color: {color};
            font-family: {Fonts.TITLE};
            background: transparent;
            padding-bottom: 4px;
        """)
        cl.addWidget(head)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 {color}55, stop:1 transparent); border: none;"
        )
        cl.addWidget(div)

    for idx, item in enumerate(items or [], 1):
        if not item or not str(item).strip():
            continue
        row = QHBoxLayout()
        row.setSpacing(Spacing.S3)
        row.setAlignment(Qt.AlignTop)

        num_lbl = QLabel(f'{idx:02d}')
        num_lbl.setStyleSheet(f"""
            color: {color};
            font-size: 13px;
            font-weight: {Fonts.W_BOLD};
            font-family: {Fonts.MONO};
            background: transparent;
            min-width: 22px;
        """)
        num_lbl.setAlignment(Qt.AlignTop | Qt.AlignRight)

        text_lbl = QLabel()
        text_lbl.setWordWrap(True)
        text_lbl.setTextFormat(Qt.RichText)
        text_lbl.setOpenExternalLinks(False)
        text_lbl.setText(_highlight_keywords_in_text(str(item).strip(), color))
        text_lbl.setStyleSheet(
            f"font-size: 13px; color: {Colors.TEXT}; "
            f"font-family: {Fonts.BODY}; line-height: 1.8;"
        )

def rich_list_block(items: List[str],
                     color: str = Colors.QINGHUA,
                     title: str = '', icon: str = '',
                     ordered: bool = True) -> QWidget:
    """强化版列表块 v2.2：编号 + 引述竖线 + 关键词高亮，有序/无序语义区分。

    替代原有扁平化列表，提供：
    - 有序模式：序号（01、02、03...）前置，序号等宽、26px 宽
    - 无序模式：• 圆点前置，替代序号（用于并列建议/提示类）
    - 引述竖线（左侧彩色）
    - 富文本关键词高亮
    - >50 条时仅渲染前 50 条 + 「展开剩余 N 条」按钮补齐

    Args:
        items:   字符串列表
        color:   强调色
        title:   列表标题（可选）
        icon:    标题图标（可选）
        ordered: 有序（True=序号）/ 无序（False=圆点）。默认 True。
    """
    container = QFrame()
    container.setStyleSheet(f"""
        QFrame {{
            background: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-left: 4px solid {color};
            border-radius: {Spacing.RADIUS};
        }}
    """)
    cl = QVBoxLayout(container)
    cl.setContentsMargins(Spacing.S4, Spacing.S3, Spacing.S4, Spacing.S3)
    cl.setSpacing(Spacing.S3)  # M3-4（b）：条目间距 8→12

    if title:
        head = QLabel(f'{icon} {title}' if icon else title)
        head.setStyleSheet(f"""
            font-size: 13px;
            font-weight: {Fonts.W_BOLD};
            color: {color};
            font-family: {Fonts.TITLE};
            background: transparent;
            padding-bottom: 4px;
        """)
        cl.addWidget(head)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 {color}55, stop:1 transparent); border: none;"
        )
        cl.addWidget(div)

    # 截断：>50 条仅渲染前 50 条，剩余用展开按钮补齐
    total = len(items or [])
    render_items = items[:50]
    remain_count = max(0, total - 50)

    for idx, item in enumerate(render_items, 1):
        if not item or not str(item).strip():
            continue
        # 序号
        num_lbl = QLabel('')
        num_lbl.setStyleSheet(f"""
            color: {color};
            font-size: {Fonts.FS_CAPTION}px;  # 序号字体降为 FS_CAPTION
            font-weight: {Fonts.W_MEDIUM};
            font-family: {Fonts.MONO};
            background: transparent;
            min-width: 26px;  # M3-4（b）：宽度 22→26，容纳三位数
        """)
        if ordered:
            num_lbl.setText(f'{idx:02d}')
            num_lbl.setAlignment(Qt.AlignTop | Qt.AlignRight)
        else:
            num_lbl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            num_lbl.setText('•')

        text_lbl = QLabel()
        text_lbl.setWordWrap(True)
        text_lbl.setTextFormat(Qt.RichText)
        text_lbl.setOpenExternalLinks(False)
        text_lbl.setText(_highlight_keywords_in_text(str(item).strip(), color))
        text_lbl.setStyleSheet(
            f"font-size: 13px; color: {Colors.TEXT}; "
            f"font-family: {Fonts.BODY}; line-height: {Spacing.LINE_HEIGHT_BODY}; "
            f"padding: 2px 0;"
        )

        row = QHBoxLayout()
        row.setSpacing(Spacing.S3)
        row.setAlignment(Qt.AlignTop)

        if ordered:
            row.addWidget(num_lbl)
        row.addWidget(text_lbl, 1)
        cl.addLayout(row)

    # 剩余条目展开按钮（>50 时显示）
    if remain_count > 0:
        expand_btn = QPushButton(f'展开剩余 {remain_count} 条')
        expand_btn.setCursor(Qt.PointingHandCursor)
        expand_btn.setStyleSheet(
            f"QPushButton {{ "
            f"    background: {Colors.CARD_HOVER}; "
            f"    color: {color}; "
            f"    border: 1px solid {color}55; "
            f"    border-radius: 8px; "
            f"    padding: 2px 10px; "
            f"    font-size: 12px; "
            f"    font-family: {Fonts.BODY}; }} "
            f"QPushButton:hover {{ "
            f"    background: {color}; color: white; }}"
        )
        expand_btn.clicked.connect(lambda: _append_rich_list_items(
            cl, items, ordered, color, len(render_items)))
        expand_btn.setFixedHeight(32)
        cl.addWidget(expand_btn)

    return container


def _append_rich_list_items(cl: QVBoxLayout, items: List[str],
                            ordered: bool, color: str,
                            rendered_count: int) -> int:
    """展开列表剩余条目，追加到给定布局。

    从已渲染条目的位置续接，保持序号连续。

    Args:
        cl:         目标列表布局。
        items:      完整条目列表。
        ordered:    是否有序（True=序号 / False=圆点）。
        color:      强调色。
        rendered_count: 已渲染条目数。

    Returns:
        追加后的总条目数。
    """
    full = list(items or [])
    for idx, item in enumerate(full[rendered_count:], rendered_count + 1):
        if not item or not str(item).strip():
            continue
        num_lbl = QLabel('')
        num_lbl.setStyleSheet(f"""
            color: {color}; font-size: {Fonts.FS_CAPTION}px;
            font-weight: {Fonts.W_MEDIUM}; font-family: {Fonts.MONO};
            background: transparent; min-width: 26px;
        """)
        if ordered:
            num_lbl.setText(f'{idx:02d}')
            num_lbl.setAlignment(Qt.AlignTop | Qt.AlignRight)
        else:
            num_lbl.setText('•')
            num_lbl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        text_lbl = QLabel()
        text_lbl.setWordWrap(True)
        text_lbl.setTextFormat(Qt.RichText)
        text_lbl.setOpenExternalLinks(False)
        text_lbl.setText(_highlight_keywords_in_text(str(item).strip(), color))
        text_lbl.setStyleSheet(
            f"font-size: 13px; color: {Colors.TEXT}; "
            f"font-family: {Fonts.BODY}; line-height: {Spacing.LINE_HEIGHT_BODY}; "
            f"padding: 2px 0;"
        )

        row = QHBoxLayout()
        row.setSpacing(Spacing.S3)
        row.setAlignment(Qt.AlignTop)
        row.addWidget(num_lbl)
        row.addWidget(text_lbl, 1)
        cl.addLayout(row)

    return len(full)


def paragraph_block(text: str, max_width: int = Spacing.COL_MAX_TEXT,
                    highlight: bool = False) -> QWidget:
    """长文本段落块 v2.2：按换行分段，每段一个 TLabel.paragraph，超宽居中。

    替代内联单段 QLabel，提供清晰的段落分隔与超宽自适应（适配宽屏与窄屏）。
    支持文本已做关键词高亮（highlight=True，text 含 HTML 标记）时直接渲染。

    Args:
        text:    原始文本，按 \\n 切分为段落；highlight=True 时为已高亮的富文本。
        max_width: 段落容器最大宽度（超宽时左右 stretch 居中）。
        highlight: 是否文本已做关键词高亮（False=普通文本，True=富文本直接渲染）。

    Returns:
        可直接 addWidget 的 QWidget。
    """
    container = QFrame()
    container.setObjectName('paragraph_block')
    container.setStyleSheet(f"background: transparent; border: none;")

    outer = QHBoxLayout(container)
    outer.setSpacing(Spacing.S0)
    outer.setAlignment(Qt.AlignHCenter)
    outer.setContentsMargins(0, 0, 0, 0)
    # 注：QHBoxLayout 无 setMaximumWidth 方法（旧代码在此抛 AttributeError，
    # 导致 conclusion_block / 结果面板 AI 结论渲染崩溃）。宽度上限须设在容器
    # QWidget 上；配合 outer 的 AlignHCenter 实现「超宽居中」。
    container.setMaximumWidth(max_width)

    inner = QVBoxLayout()
    inner.setSpacing(Spacing.S3)  # 段间距 > 行距，形成段落感
    inner.setContentsMargins(0, 0, 0, 0)

    raw_text = text or ''
    for para in raw_text.split('\n'):
        if not para.strip():
            continue
        lbl = TLabel.paragraph(para)
        if highlight:
            # 富文本已高亮，仅设样式（颜色/行距走令牌）
            lbl.setStyleSheet(
                f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; "
                f"font-family: {Fonts.BODY}; line-height: {Spacing.LINE_HEIGHT_BODY}; "
                f"padding: 2px 0;"
            )
        else:
            lbl.setStyleSheet(
                f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; "
                f"font-family: {Fonts.BODY}; line-height: {Spacing.LINE_HEIGHT_BODY}; "
                f"padding: 2px 0;"
            )
        inner.addWidget(lbl)

    outer.addLayout(inner, 1)

    # 超宽自适应：展开式宽度 + 首选，配合外层最大宽度实现居中
    container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return container


def code_block(text: str, language: str = '') -> QWidget:
    """代码块容器 v2.2：深色底 + 等宽可选中 + 语言标签 + 复制按钮。

    用于 AI 输出中的代码片段（如算法伪代码 / 示例），等宽可读、可选中复制。

    Args:
        text:   代码文本。
        language: 代码语言标识（用于顶部标签，空串时不显示）。

    Returns:
        可直接 addWidget 的 QWidget。
    """
    container = QFrame()
    container.setObjectName('code_block')
    container.setStyleSheet(f"""
        QFrame {{
            background: {Colors.BG_DARK};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            padding: {Spacing.S3}px;
        }}
    """)

    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(Spacing.S2)

    # 顶部行：语言标签 + 复制按钮
    top = QHBoxLayout()
    top.setSpacing(Spacing.S3)
    top.setContentsMargins(0, 0, 0, 0)
    top.setAlignment(Qt.AlignTop)

    lang_lbl = QLabel(language or 'CODE')
    lang_lbl.setStyleSheet(
        f"font-size: {Fonts.FS_MICRO}px; color: {Colors.TEXT3}; "
        f"font-family: {Fonts.MONO};"
    )

    copy_btn = QPushButton('复制')
    copy_btn.setCursor(Qt.PointingHandCursor)
    copy_btn.setFixedHeight(24)
    copy_btn.setStyleSheet(
        f"QPushButton {{ "
        f"    background: {Colors.BG_DARK}; "
        f"    color: {Colors.TEXT2}; "
        f"    border: 1px dashed {Colors.BORDER}; "
        f"    border-radius: 6px; "
        f"    font-size: {Fonts.FS_MICRO}px; "
        f"    font-family: {Fonts.BODY}; }} "
        f"QPushButton:hover {{ "
        f"    border-color: {Colors.LIUJIN}; color: {Colors.LIUJIN}; }}"
    )
    copy_btn.clicked.connect(lambda: _copy_text(container, text))
    top.addWidget(lang_lbl, 0, 1)
    top.addWidget(copy_btn, 0, 2)
    layout.addLayout(top)

    # 代码区：等宽、可滚动
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setStyleSheet(f"background: {Colors.BG_DARK};")

    code_label = QLabel()
    code_label.setWordWrap(False)
    code_label.setTextFormat(Qt.RichText)
    code_label.setOpenExternalLinks(False)
    # 等宽字体 + 可选中
    code_label.setFont(QFont('Consolas', 12))
    code_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    code_label.setStyleSheet(f"color: {Colors.TEXT}; background: transparent;")

    scroll.setWidget(code_label)
    layout.addWidget(scroll)

    return container


def _copy_text(container: QWidget, text: str) -> None:
    """将代码文本写入剪贴板（幂等，无额外资源）。"""
    import app as _app  # 延迟 import，避免循环依赖
    clip = _app.QApplication.clipboard()
    try:
        clip.copy(text or '')
    except Exception:
        pass
