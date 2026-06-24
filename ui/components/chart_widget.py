"""
图表展示组件
封装matplotlib图表，嵌入PySide6界面
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import traceback
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from core.chart_generator import ChartGenerator


class ChartWidget(QWidget):
    """图表展示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart_gen = ChartGenerator()
        self.current_fig = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        # 标记数据是否已就绪（用于 showEvent 时自动重绘）
        self._has_data = False

        # 工具栏
        toolbar_widget = QFrame()
        toolbar_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CONTROL_RADIUS};
            }}
        """)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(8)

        title_label = QLabel('📊 数据可视化')
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SECTION};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()

        # 图表切换按钮
        self.chart_type_buttons = []
        chart_types = [
            ('wuxing', '五行'),
            ('shishen_bar', '十神'),
            ('shishen_radar', '雷达图'),
            ('dayun', '大运'),
            ('changsheng', '长生'),
            ('dashboard', '仪表盘'),
        ]

        for key, name in chart_types:
            btn = QPushButton(name)
            btn.setStyleSheet(Stylesheets.BUTTON_SWITCH)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty('chart_type', key)
            btn.clicked.connect(lambda checked, k=key: self._on_chart_type_changed(k))
            toolbar_layout.addWidget(btn)
            self.chart_type_buttons.append(btn)

        # 默认选中五行
        if self.chart_type_buttons:
            self.chart_type_buttons[0].setChecked(True)

        layout.addWidget(toolbar_widget)

        # 图表面板
        self.canvas_container = QFrame()
        self.canvas_container.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CARD_RADIUS};
            }}
        """)
        canvas_layout = QVBoxLayout(self.canvas_container)
        canvas_layout.setContentsMargins(16, 16, 16, 16)

        # matplotlib canvas
        self.canvas = None
        self.current_chart_type = 'wuxing'
        self.wuxing_data = None
        self.shishen_data = None
        self.dayun_data = None
        self.changsheng_data = None

        # 初始显示空状态
        self._show_placeholder('暂无数据', '请先在「八字排盘」中完成排盘，然后切换到本视图查看图表')

        layout.addWidget(self.canvas_container, 1)

    def set_data(self, wuxing=None, shishen=None, dayun=None, changsheng=None):
        """设置图表数据

        关键修复：保证数据更新后立即渲染，并在数据为空时给出明确提示，
        避免图表区域出现「空白」「无响应」之类的体验问题。
        """
        self.wuxing_data = wuxing
        self.shishen_data = shishen
        self.dayun_data = dayun
        self.changsheng_data = changsheng
        # 标记数据已就绪，供 showEvent 时自动重绘
        self._has_data = any([wuxing, shishen, dayun, changsheng])
        try:
            self._render_chart()
        except Exception as e:
            # 渲染失败时显示错误信息，避免整个面板崩溃
            print(f"[ChartWidget] 图表渲染失败: {e}")
            traceback.print_exc()
            self._show_placeholder(
                '图表渲染失败',
                f'错误信息: {str(e)[:80]}\n请检查 matplotlib 字体或后端配置',
                is_error=True,
            )

    def showEvent(self, event):
        """切到本视图时，若已有数据则自动重绘

        关键修复：用户在「八字排盘」完成排盘后，切到「图表分析」标签时，
        之前调用 set_data 触发的渲染可能因为 widget 隐藏而未生效；
        此处保证 widget 重新可见时一定会重绘最新数据。
        """
        super().showEvent(event)
        if getattr(self, '_has_data', False):
            try:
                self._render_chart()
            except Exception as e:
                print(f"[ChartWidget] showEvent 重绘失败: {e}")
                traceback.print_exc()

    def _on_chart_type_changed(self, chart_type):
        """切换图表类型"""
        for btn in self.chart_type_buttons:
            btn.setChecked(btn.property('chart_type') == chart_type)
        self.current_chart_type = chart_type
        try:
            self._render_chart()
        except Exception as e:
            print(f"[ChartWidget] 切换图表类型失败: {e}")
            traceback.print_exc()
            self._show_placeholder(
                '图表渲染失败',
                f'错误信息: {str(e)[:80]}',
                is_error=True,
            )

    def _clear_canvas_layout(self):
        """清理 canvas_container 中所有旧 widget"""
        layout = self.canvas_container.layout()
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _show_placeholder(self, title, subtitle, is_error=False):
        """显示占位提示（无数据 / 错误）"""
        # 先清理旧 canvas
        if self.canvas:
            self.canvas.setParent(None)
            self.canvas.deleteLater()
            self.canvas = None
        if self.current_fig:
            try:
                plt.close(self.current_fig)
            except Exception:
                pass
            self.current_fig = None
        self._clear_canvas_layout()

        main_color = Colors.DANGER if is_error else Colors.TEXT_TERTIARY
        icon_char = '⚠' if is_error else '☯'

        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(wrap)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(8)
        vl.setAlignment(Qt.AlignCenter)

        icon = QLabel(icon_char)
        icon.setStyleSheet(f"font-size: 48px; color: {main_color};")
        icon.setAlignment(Qt.AlignCenter)

        t = QLabel(title)
        t.setStyleSheet(
            f"font-size: 16px; font-weight: 600; "
            f"color: {Colors.TEXT}; font-family: {Fonts.FAMILY_CN};"
        )
        t.setAlignment(Qt.AlignCenter)

        s = QLabel(subtitle)
        s.setStyleSheet(
            f"font-size: 13px; color: {main_color}; "
            f"font-family: {Fonts.FAMILY_CN};"
        )
        s.setAlignment(Qt.AlignCenter)
        s.setWordWrap(True)

        vl.addStretch()
        vl.addWidget(icon)
        vl.addWidget(t)
        vl.addWidget(s)
        vl.addStretch()

        self.canvas_container.layout().addWidget(wrap)

    def _render_chart(self):
        """渲染当前选中的图表"""
        # 清除旧图表
        if self.canvas:
            self.canvas.setParent(None)
            self.canvas.deleteLater()
            self.canvas = None
        if self.current_fig:
            try:
                plt.close(self.current_fig)
            except Exception:
                pass
            self.current_fig = None

        # 清除布局中的旧内容
        self._clear_canvas_layout()

        fig = None
        try:
            if self.current_chart_type == 'wuxing' and self.wuxing_data:
                fig = self.chart_gen.create_wuxing_pie_chart(
                    self.wuxing_data, '五行分布', figsize=(6, 5)
                )
            elif self.current_chart_type == 'shishen_bar' and self.shishen_data:
                fig = self.chart_gen.create_shishen_bar_chart(
                    self.shishen_data, '十神分布', figsize=(7, 5)
                )
            elif self.current_chart_type == 'shishen_radar' and self.shishen_data:
                fig = self.chart_gen.create_shishen_radar_chart(
                    self.shishen_data, '十神能量分布', figsize=(6, 6)
                )
            elif self.current_chart_type == 'dayun' and self.dayun_data:
                fig = self.chart_gen.create_dayun_line_chart(
                    self.dayun_data, '大运走势', figsize=(8, 4.5)
                )
            elif self.current_chart_type == 'changsheng' and self.changsheng_data:
                fig = self.chart_gen.create_shier_changsheng_chart(
                    self.changsheng_data, '十二长生', figsize=(7, 5)
                )
            elif self.current_chart_type == 'dashboard':
                fig = self.chart_gen.create_dashboard(
                    wuxing_result=self.wuxing_data,
                    shishen_result=self.shishen_data,
                    major_fortune=self.dayun_data,
                    shier_changsheng=self.changsheng_data,
                )
        except Exception as chart_err:
            # 单个图表生成失败不影响整体流程
            print(f"[ChartWidget] 生成 {self.current_chart_type} 失败: {chart_err}")
            traceback.print_exc()
            self._show_placeholder(
                f'「{self.current_chart_type}」图表生成失败',
                f'错误信息: {str(chart_err)[:80]}',
                is_error=True,
            )
            return

        if fig:
            self.current_fig = fig
            self.canvas = FigureCanvas(fig)
            self.canvas.setStyleSheet(f"background-color: {Colors.CARD};")
            self.canvas_container.layout().addWidget(self.canvas)
        else:
            # 数据为空时给出明确提示
            self._show_placeholder(
                '该图表暂无数据',
                '当前排盘结果中没有与此图表对应的数据，请先完成排盘',
            )

    def save_current_chart(self, filepath):
        """保存当前图表"""
        if self.current_fig:
            self.current_fig.savefig(filepath, dpi=150, bbox_inches='tight',
                                      facecolor=self.current_fig.get_facecolor())
            return True
        return False

    # 兼容旧版命名（部分代码可能引用了 _init_ui）
    def init_ui(self):
        self._init_ui()
