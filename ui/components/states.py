# -*- coding: utf-8 -*-
"""
ui/components/states.py — 统一状态组件（空 / 加载 / 错误）

UI 升级方案 M3：替代各面板"自造轮子"的空/错误实现，
提供统一视觉语言的三个状态组件，供四结果面板与图表复用。

规范（对齐实施计划 3.6 / 步骤 6）：
    - EmptyState：空数据引导（图标 + 标题 + 提示），支持图标呼吸 + 文案淡入动画，禁止伪造数据
    - LoadingState：加载中（复用 CollapsibleCard.TaijiSpinner + 主文案 + 轮播提示）
    - ErrorState：错误/异常（图标 + 标题 + 描述 + 重试按钮，retry 信号）
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                               QPushButton, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve

from ui.styles import Colors, Fonts, Spacing


class EmptyState(QWidget):
    """空数据引导组件（M3-6：统一视觉语言 + 引导动效）。

    用法：
        EmptyState(title='暂无数据', hint='请在「设置」中启用 AI 指标采集',
                   icon='○', color=Colors.TEXT3, parent=self)
        # 或工厂方法
        EmptyState.empty(title='...')
    """

    def __init__(self, title: str = '暂无数据', hint: str = '',
                 icon: str = '○', color: str = Colors.TEXT3,
                 parent: QWidget = None,
                 breathe: bool = True, fade_in: bool = True,
                 breathe_duration: int = 2400, fade_delay: int = 0):
        """
        空数据引导组件，图标呼吸（透明度循环）+ 文案延迟淡入（引导节奏）。

        Args:
            title:       标题文字。
            hint:        提示文字（可选）。
            icon:        图标字符。
            color:       图标颜色。
            parent:      Qt 父控件。
            breathe:     是否启用图标呼吸动画（默认 True）。
            fade_in:     是否启用文案淡入动画（默认 True）。
            breathe_duration: 呼吸动画周期（毫秒），默认 2400。
            fade_delay:  文案淡入延迟起始（毫秒），默认 0（图标即起）。
        """
        super().__init__(parent)
        self.setStyleSheet('background: transparent;')
        self._breathe_anim = None
        self._fade_anims = []

        outer = QVBoxLayout(self)
        outer.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        outer.setContentsMargins(Spacing.S6, Spacing.S6, Spacing.S6, Spacing.S6)
        outer.addStretch(1)

        col = QVBoxLayout()
        col.setAlignment(Qt.AlignCenter)
        col.setSpacing(Spacing.S2)

        # 图标 + 呼吸
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"font-size: 40px; color: {color}; background: transparent;")
        col.addWidget(icon_lbl)

        if breathe:
            try:
                eff = QGraphicsOpacityEffect(icon_lbl)
                eff.setOpacity(1.0)
                icon_lbl.setGraphicsEffect(eff)
                self._breathe_anim = QPropertyAnimation(
                    eff, b'opacity', self)
                self._breathe_anim.setDuration(breathe_duration)
                self._breathe_anim.setStartValue(0.45)
                self._breathe_anim.setEndValue(1.0)
                self._breathe_anim.setEasingCurve(QEasingCurve.InOutSine)
                self._breathe_anim.setLoopCount(-1)
                self._breathe_anim.start()
            except Exception:
                self._breathe_anim = None

        # 标题
        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            f"font-size: {Fonts.FS_H3}px; font-weight: {Fonts.W_MEDIUM}; "
            f"color: {Colors.TEXT2}; font-family: {Fonts.BODY};")
        col.addWidget(title_lbl)

        if hint:
            hint_lbl = QLabel(hint)
            hint_lbl.setAlignment(Qt.AlignCenter)
            hint_lbl.setWordWrap(True)
            hint_lbl.setStyleSheet(
                f"font-size: {Fonts.FS_CAPTION}px; color: {Colors.TEXT3}; "
                f"font-family: {Fonts.BODY};")
            col.addWidget(hint_lbl)

        outer.addLayout(col)
        outer.addStretch(1)

    @staticmethod
    def empty(title: str = '暂无数据', hint: str = '',
              icon: str = '○', parent: QWidget = None,
              **kwargs) -> 'EmptyState':
        """工厂方法：构造一个 EmptyState（直接 addWidget 即可）。

        支持 breathe / fade_in / breathe_duration / fade_delay 等透传参数。
        """
        return EmptyState(title=title, hint=hint, icon=icon, parent=parent, **kwargs)


class LoadingState(QWidget):
    """加载中状态组件：旋转太极 + 主文案 + 轮播提示。

    复用 CollapsibleCard.LoadingPanel（太极 + 主文案 + 副标题 + 轮播提示语），
    作为独立封装对外提供一致的加载态接口。
    """

    def __init__(self, message: str = '正在加载…', sub: str = '',
                 color: str = Colors.LIUJIN, hints=None, parent=None):
        super().__init__(parent)
        # 复用既有 LoadingPanel，保证与面板加载态视觉一致
        from ui.components.collapsible_card import LoadingPanel
        self._panel = LoadingPanel(message=message, sub=sub, color=color,
                                   hints=hints, parent=self)
        lay = QVBoxLayout(self)
        lay.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._panel, 1)

    @staticmethod
    def of(message: str = '正在加载…', color: str = Colors.LIUJIN,
           hints=None, parent=None) -> 'LoadingState':
        """工厂方法：构造一个 LoadingState。"""
        return LoadingState(message=message, color=color, hints=hints, parent=parent)


class ErrorState(QWidget):
    """错误/异常状态组件：图标 + 标题 + 描述 + 可选重试按钮。

    发出 retry 信号，由调用方绑定重试逻辑。
    """

    retry = Signal()

    def __init__(self, title: str = '出错了', message: str = '',
                 retry_hint: str = '重试', show_retry: bool = True,
                 color: str = Colors.DANGER, parent=None):
        super().__init__(parent)
        self.setStyleSheet('background: transparent;')
        outer = QVBoxLayout(self)
        outer.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        outer.setContentsMargins(Spacing.S6, Spacing.S6, Spacing.S6, Spacing.S6)
        outer.addStretch(1)

        col = QVBoxLayout()
        col.setAlignment(Qt.AlignCenter)
        col.setSpacing(Spacing.S2)

        icon_lbl = QLabel('⚠')
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"font-size: 36px; color: {color}; background: transparent;")
        col.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            f"font-size: {Fonts.FS_H3}px; font-weight: {Fonts.W_SEMIBOLD}; "
            f"color: {Colors.TEXT}; font-family: {Fonts.BODY};")
        col.addWidget(title_lbl)

        if message:
            msg_lbl = QLabel(message)
            msg_lbl.setAlignment(Qt.AlignCenter)
            msg_lbl.setWordWrap(True)
            msg_lbl.setStyleSheet(
                f"font-size: {Fonts.FS_CAPTION}px; color: {Colors.TEXT2}; "
                f"font-family: {Fonts.BODY};")
            col.addWidget(msg_lbl)

        if show_retry and retry_hint:
            btn = QPushButton(retry_hint)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedWidth(96)
            btn.setStyleSheet(self._btn_style())
            btn.clicked.connect(self.retry.emit)
            col.addWidget(btn, 0, Qt.AlignCenter)
            self._retry_btn = btn
        else:
            self._retry_btn = None

        outer.addLayout(col)
        outer.addStretch(1)

    def _btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {Colors.CARD};
                color: {Colors.BRAND};
                border: 1px solid {Colors.BORDER2};
                border-radius: {Spacing.RADIUS_SM};
                font-size: {Fonts.FS_BODY}px;
                font-weight: {Fonts.W_MEDIUM};
                font-family: {Fonts.BODY};
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {Colors.CARD_HOVER};
                border-color: {Colors.BRAND_LIGHT};
            }}
        """

    def set_retry_enabled(self, enabled: bool):
        """启用/禁用重试按钮。"""
        if self._retry_btn is not None:
            self._retry_btn.setEnabled(enabled)

    @staticmethod
    def of(title: str = '出错了', message: str = '', retry_hint: str = '重试',
           show_retry: bool = True, parent=None) -> 'ErrorState':
        """工厂方法：构造一个 ErrorState。"""
        return ErrorState(title=title, message=message, retry_hint=retry_hint,
                          show_retry=show_retry, parent=parent)


def mount_error_state(layout, message: str, *, title: str = '排盘失败',
                      retry=None, retry_hint: str = '重试',
                      color: str = Colors.DANGER):
    """在 ``layout`` 中挂载统一错误态（M3-6 统一错误视觉 + 可选重试）。

    供四结果面板的 ``show_error()`` 共用，避免每个面板各自复制一份
    「透明 holder + ErrorState + 重试连线」实现。

    参数：
        layout:     目标内容布局（调用方须先清空该布局）。
        message:    错误说明文案（通常来自异常）。
        title:      错误标题。
        retry:      重试回调；None 时不显示重试按钮（仅展示错误）。
        retry_hint: 重试按钮文案。
        color:      图标色（默认 DANGER）。
    返回：
        (holder, err)：holder 为承载控件（调用方保存引用以便清理），
        err 为 ErrorState 实例。
    """
    holder = QWidget()
    holder.setStyleSheet('background: transparent;')
    v = QVBoxLayout(holder)
    v.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
    v.setSpacing(Spacing.S0)
    err = ErrorState(
        title=title,
        message=message,
        retry_hint=retry_hint,
        show_retry=retry is not None,
        color=color,
        parent=holder,
    )
    if retry is not None:
        err.retry.connect(retry)
    v.addWidget(err, 1)
    layout.addWidget(holder)
    return holder, err
