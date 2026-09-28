# -*- coding: utf-8 -*-
"""
ui/components/ai_metrics_chart.py
AI 缓存命中率与熔断历史曲线图表组件
依赖 PySide6 + matplotlib

UI 升级方案 M2 重写 + P12/P13 修复：
- 主题映射：Colors 常量 → Matplotlib rcParams / 轴样式（_apply_theme），禁止硬编码色值
- 响应式（P12 修复）：真 DPI（跟随系统 physicalDotsPerInch）+ resizeEvent 防抖重绘
  仅 set_size_inches(forward=True) 不触发重绘，必须显式 draw_idle，否则位图尺寸与
  显示尺寸不一致 → DPI 抖动
- 交互：悬停 tooltip + 最近数据点高亮（_on_motion 桥接 event_data）
- 空数据（P13 修复）：EmptyState 引导替代 generate_demo_data 伪造；
  加载失败走 ErrorState + 重试，不再把异常静默吞掉当成「无数据」
- 加载态：load_real_data 期间叠加 TaijiSpinner 覆盖层
"""
import logging
from datetime import datetime
from typing import List, Tuple

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QStackedWidget,
                               QFrame, QApplication)
from PySide6.QtCore import Qt, QTimer

import matplotlib
matplotlib.use('QtAgg')
from matplotlib import rcParams  # noqa: E402
# 设置中文字体（Windows 优先使用微软雅黑/黑体）
rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False  # 正常显示负号
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402

from ui.styles import Colors, Fonts, Spacing

logger = logging.getLogger(__name__)

# 图表布局下界（响应式最小尺寸，避免极窄布局挤爆坐标轴）
_MIN_WIDTH = 320
_MIN_HEIGHT = 200
_ASPECT_RATIO = 0.45
_RESIZE_DEBOUNCE_MS = 120


def _apply_theme(fig, ax_list):
    """将 Colors 常量映射为 Matplotlib rcParams 与轴样式（M2 主题映射）。

    所有颜色走 Colors，禁止硬编码 #xxxxxx。
    """
    bg = Colors.BG          # #1a1a2e
    card = Colors.CARD      # #21213a
    text = Colors.TEXT      # #F5F1E8
    text2 = Colors.TEXT2
    grid = Colors.DIVIDER   # #2E2E4C
    brand = Colors.BRAND     # #c9a227
    accent = Colors.ACCENT  # #8b0000

    fig.patch.set_facecolor(bg)
    for ax in ax_list:
        ax.set_facecolor(card)
        ax.tick_params(colors=text2, labelsize=10)
        ax.xaxis.label.set_color(text)
        ax.yaxis.label.set_color(text)
        ax.grid(True, color=grid, alpha=0.5, linewidth=0.6)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(grid)
        ax.spines['bottom'].set_color(grid)
    return {'brand': brand, 'accent': accent, 'text': text, 'text2': text2}


class AIMetricsChart(QWidget):
    """缓存命中率与熔断历史曲线图表（M2 交互化重写 + P12/P13 修复）。

    双轴展示命中率（ax1）与熔断次数（ax2），支持悬停 tooltip、
    响应式重绘、空数据引导与加载失败错误态。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('AI 性能指标')

        # 真 DPI：跟随系统物理 DPI（125%/150%/200% 屏）。
        # 固定 dpi=100 是窗口 resize 时「DPI 抖动」的根因——低 DPI 位图被 Qt 拉伸放大。
        self._dpi = self._detect_dpi()

        # resize 防抖：拖拽窗口时连续 resizeEvent 合并为一次重绘（tight_layout 昂贵）
        self._resize_debounce = QTimer(self)
        self._resize_debounce.setSingleShot(True)
        self._resize_debounce.setInterval(_RESIZE_DEBOUNCE_MS)
        self._resize_debounce.timeout.connect(self._apply_chart_size)

        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        root.setSpacing(Spacing.S0)

        # 图表标题
        title = QLabel('AI 缓存命中率 & 熔断历史')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: {Fonts.FS_H3}px; font-weight: {Fonts.W_SEMIBOLD}; "
            f"color: {Colors.TEXT}; font-family: {Fonts.TITLE};")
        root.addWidget(title)

        # 内容区：QStackedWidget 在「图表 / 空态 / 错误态」之间切换
        self._stack = QStackedWidget()

        # 创建 Figure（尺寸随 resize 动态调整）
        self.figure = Figure(figsize=(8, 6), dpi=self._dpi)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet('background: transparent;')
        self._chart_frame = QFrame()
        self._chart_frame.setStyleSheet('background: transparent; border: none;')
        cf = QVBoxLayout(self._chart_frame)
        cf.setContentsMargins(Spacing.S3, Spacing.S3, Spacing.S3, Spacing.S3)
        cf.setSpacing(Spacing.S0)
        cf.addWidget(self.canvas)
        self._stack.addWidget(self._chart_frame)      # index 0

        # 空态组件（EmptyState，替代伪造演示数据）
        self._empty = self._build_empty_state()
        self._stack.addWidget(self._empty)            # index 1

        # 错误态组件（ErrorState + 重试）
        self._error = self._build_error_state()
        self._stack.addWidget(self._error)            # index 2

        root.addWidget(self._stack, 1)

        # 双轴
        self.ax1 = self.figure.add_subplot(211)
        self.ax2 = self.figure.add_subplot(212, sharex=self.ax1)
        self._theme = _apply_theme(self.figure, [self.ax1, self.ax2])
        self._init_axes()

        # 交互：悬停 tooltip + 数据点高亮
        self._highlight = {}
        self._last_tooltip = None
        self._last_tooltip_key = None
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.canvas.mpl_connect('axes_leave_event', self._on_leave)

        # 加载覆盖层（TaijiSpinner）
        self._loading_overlay = self._build_loading_overlay()
        self._loading_overlay.hide()
        root.addWidget(self._loading_overlay, 0)

        self.figure.tight_layout()
        # 初始尺寸与当前控件对齐
        QTimer.singleShot(0, self._apply_chart_size)

    @staticmethod
    def _detect_dpi() -> float:
        """读取系统物理 DPI，失败时回退 100。"""
        try:
            app = QApplication.instance()
            screen = app.primaryScreen() if app else None
            dpi = float(screen.physicalDotsPerInch()) if screen else 100.0
        except Exception:
            dpi = 100.0
        return dpi if dpi and dpi > 0 else 100.0

    # ---------- 构建空态 ----------
    def _build_empty_state(self) -> QWidget:
        """构建空数据引导面板（M2/P13：不伪造数据，给出可操作提示）。"""
        from ui.components.states import EmptyState
        holder = QWidget()
        holder.setStyleSheet('background: transparent;')
        v = QVBoxLayout(holder)
        v.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        v.setSpacing(Spacing.S0)
        empty = EmptyState(
            title='暂无指标数据',
            hint='完成一次 AI 分析后，命中率与熔断记录会自动显示在这里',
            icon='☯',
            color=Colors.TEXT3,
            parent=holder,
        )
        v.addWidget(empty, 1)
        return holder

    # ---------- 构建错误态 ----------
    def _build_error_state(self) -> QWidget:
        """构建加载失败面板（P13：区分「无数据」与「加载异常」，支持重试）。"""
        from ui.components.states import ErrorState
        holder = QWidget()
        holder.setStyleSheet('background: transparent;')
        v = QVBoxLayout(holder)
        v.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        v.setSpacing(Spacing.S0)
        err = ErrorState(
            title='指标加载失败',
            message='',
            retry_hint='重试加载',
            show_retry=True,
            color=Colors.DANGER,
            parent=holder,
        )
        err.retry.connect(self.load_real_data)
        v.addWidget(err, 1)
        return holder

    # ---------- 构建加载覆盖层 ----------
    def _build_loading_overlay(self) -> QFrame:
        """构建加载覆盖层（旋转太极），load_real_data 期间显示。"""
        from ui.components.collapsible_card import TaijiSpinner
        overlay = QFrame()
        overlay.setStyleSheet(
            f"background: rgba(18, 18, 31, 0.7); border: 1px solid {Colors.BORDER}; "
            f"border-radius: {Spacing.RADIUS}px;")
        lay = QVBoxLayout(overlay)
        lay.setContentsMargins(Spacing.S4, Spacing.S4, Spacing.S4, Spacing.S4)
        lay.setSpacing(Spacing.S2)
        spinner = TaijiSpinner(size=48, color=Colors.LIUJIN)
        lay.addWidget(spinner, 0, Qt.AlignCenter)
        lbl = QLabel('正在加载 AI 指标…')
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"font-size: {Fonts.FS_CAPTION}px; color: {Colors.TEXT2}; "
            f"font-family: {Fonts.BODY};")
        lay.addWidget(lbl)
        return overlay

    def _init_axes(self):
        # 命中率轴
        self.ax1.set_ylabel('命中率 %')
        self.ax1.set_ylim(0, 100)
        # 熔断轴
        self.ax2.set_ylabel('熔断次数')
        self.ax2.set_xlabel('时间')
        # 网格与 spines 已在 _apply_theme 配置，这里仅设限
        self.ax1.grid(True, alpha=0.5)
        self.ax2.grid(True, alpha=0.5)

    def load_real_data(self):
        """从数据库加载真实数据。

        加载期显示覆盖层；数据为空 → EmptyState；加载异常 → ErrorState（P13：
        异常不再被静默当成「无数据」，用户能看到真实原因并可重试）。
        """
        from core.ai_cache import get_cache_history
        from core.sqlite_db import get_circuit_breaker_history

        self._show_loading(True)
        try:
            # 缓存命中率数据
            cache_rows = get_cache_history(limit=48)
            cache_data = []
            for ts_str, rate in cache_rows:
                try:
                    ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                    cache_data.append((ts, float(rate)))
                except Exception:
                    pass

            # 熔断数据：统计 open_count 变化
            breaker_rows = get_circuit_breaker_history(limit=48)
            circuit_data = []
            for row in breaker_rows:
                try:
                    ts = datetime.strptime(row['ts'], '%Y-%m-%d %H:%M:%S')
                    circuit_data.append((ts, int(row.get('open_count', 0))))
                except Exception:
                    pass

            self.update_charts(cache_data, circuit_data)
        except Exception as exc:  # noqa: BLE001
            logger.exception('加载 AI 指标失败')
            self._show_error(f'指标加载失败：{exc}')
        finally:
            self._show_loading(False)

    def _show_loading(self, on: bool):
        """切换加载覆盖层可见性。"""
        try:
            self._loading_overlay.setVisible(on)
            if on:
                self._loading_overlay.raise_()
        except Exception:
            pass

    def _show_error(self, message: str):
        """切换到错误态面板（P13）。

        ErrorState 的 message 在构造期固化，无 setter，故重建该页组件。
        """
        from ui.components.states import ErrorState

        holder = QWidget()
        holder.setStyleSheet('background: transparent;')
        v = QVBoxLayout(holder)
        v.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        v.setSpacing(Spacing.S0)
        err = ErrorState(
            title='指标加载失败',
            message=message,
            retry_hint='重试加载',
            show_retry=True,
            color=Colors.DANGER,
            parent=holder,
        )
        err.retry.connect(self.load_real_data)
        v.addWidget(err, 1)

        old = self._error
        self._stack.removeWidget(old)
        self._stack.insertWidget(2, holder)  # 保持在第 3 页（index 2）
        self._error = holder
        old.deleteLater()
        self._stack.setCurrentIndex(2)

    def update_charts(self, cache_data: List[Tuple[datetime, float]],
                      circuit_data: List[Tuple[datetime, int]]):
        """更新图表数据。

        cache_data: [(datetime, hit_rate)]
        circuit_data: [(datetime, count)]
        双轴均空时切换到 EmptyState 面板（不再伪造数据）。
        """
        if not cache_data and not circuit_data:
            self._stack.setCurrentIndex(1)  # EmptyState
            return
        self._stack.setCurrentIndex(0)      # 图表

        # 重建前清理交互状态，避免旧轴对象/旧 tooltip 残留在新图上
        self._highlight.clear()
        if self._last_tooltip is not None:
            try:
                self._last_tooltip.remove()
            except Exception:
                pass
        self._last_tooltip = None
        self._last_tooltip_key = None

        self.ax1.clear()
        self.ax2.clear()
        # 重建双轴
        self.ax1 = self.figure.add_subplot(211)
        self.ax2 = self.figure.add_subplot(212, sharex=self.ax1)
        self._theme = _apply_theme(self.figure, [self.ax1, self.ax2])
        self._init_axes()

        theme = self._theme
        if cache_data:
            times, rates = zip(*cache_data)
            ln = self.ax1.plot(times, rates, color=theme['brand'], linewidth=2,
                               marker='o', label='缓存命中率')[0]
            self._highlight[self.ax1] = ln
            self.ax1.legend(loc='upper left', facecolor=Colors.CARD,
                            edgecolor=Colors.BORDER2, labelcolor=Colors.TEXT2)

        if circuit_data:
            times, counts = zip(*circuit_data)
            ln = self.ax2.plot(times, counts, color=theme['accent'], linewidth=2,
                               marker='x', label='熔断次数')[0]
            self._highlight[self.ax2] = ln
            self.ax2.legend(loc='upper left', facecolor=Colors.CARD,
                            edgecolor=Colors.BORDER2, labelcolor=Colors.TEXT2)

        # 格式化 x 轴
        self.ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        self.figure.autofmt_xdate()
        # 重建后重新应用当前控件尺寸（否则新图回退到 Figure 默认 8x6）
        self._apply_chart_size()
        self.canvas.draw()

    # ---------- 悬停 tooltip + 数据点高亮（M2 交互） ----------
    def _on_motion(self, event):
        """鼠标移入图元时显示 tooltip 并高亮最近数据点。"""
        if event.inaxes not in (self.ax1, self.ax2):
            return
        if event.xdata is None or event.ydata is None:
            return
        ax = event.inaxes
        line = self._highlight.get(ax)
        if line is None or len(line.get_xydata()) == 0:
            return
        try:
            ex = float(event.xdata)
            # 找最近数据点（日期轴在 matplotlib 内部为 float 序号）
            nearest_x, nearest_y = min(
                line.get_xydata(), key=lambda p: abs(float(p[0]) - ex))
        except (TypeError, ValueError):
            return
        nearest_x, nearest_y = float(nearest_x), float(nearest_y)

        # 节流：同一点不重复 annotate
        key = (id(ax), round(nearest_x, 4), round(nearest_y, 4))
        if key == self._last_tooltip_key:
            return

        label = '缓存命中率' if ax is self.ax1 else '熔断次数'
        try:
            ts_str = mdates.num2date(nearest_x).strftime('%m-%d %H:%M')
        except Exception:
            ts_str = str(nearest_x)
        text = f"{label}\n{ts_str}: {nearest_y:.1f}"
        color = self._theme.get('brand' if ax is self.ax1 else 'accent', Colors.BRAND)
        self._show_tooltip(ax, nearest_x, nearest_y, text, color)
        self._last_tooltip_key = key

    def _show_tooltip(self, ax, x, y, text, color):
        """显示/更新 tooltip annotation，并立即重绘使其可见。"""
        if self._last_tooltip is None:
            self._last_tooltip = ax.annotate(
                text, xy=(x, y),
                xytext=(8, 8), textcoords='offset points',
                fontsize=Fonts.FS_MICRO, color=Colors.TEXT,
                bbox=dict(boxstyle='round,pad=0.4',
                          facecolor=Colors.CARD, edgecolor=color, alpha=0.95),
                arrowprops=dict(arrowstyle='->', color=color, lw=1))
        else:
            self._last_tooltip.set_text(text)
            self._last_tooltip.xy = (x, y)
        try:
            self.canvas.draw_idle()
        except Exception:
            pass

    def _on_leave(self, event):
        """鼠标移出图区时隐藏 tooltip。"""
        if self._last_tooltip is not None:
            self._last_tooltip.set_text('')
            self._last_tooltip.get_bbox_patch().set_visible(False)
            self._last_tooltip_key = None
            try:
                self.canvas.draw_idle()
            except Exception:
                pass

    # ---------- 响应式重绘（P12：真 DPI + forward + 防抖 + 重绘） ----------
    def _apply_chart_size(self):
        """按当前控件尺寸重设 Figure 英寸数并重绘。

        仅 set_size_inches(forward=True) 不会触发重绘，必须显式 draw_idle，
        否则显示尺寸与实际位图尺寸不一致 → DPI 抖动。
        """
        if self.figure is None:
            return
        w = max(_MIN_WIDTH, self.width() - Spacing.S6 * 2)
        h = max(_MIN_HEIGHT, int(w * _ASPECT_RATIO))
        self.figure.set_size_inches(w / self._dpi, h / self._dpi, forward=True)
        try:
            self.figure.tight_layout()
        except Exception:
            pass
        try:
            self.canvas.draw_idle()
        except Exception:
            pass

    def resizeEvent(self, event):
        """窗口 resize：防抖后重设图表尺寸（拖拽时合并连续事件）。"""
        super().resizeEvent(event)
        if self.figure is not None:
            self._resize_debounce.start()
