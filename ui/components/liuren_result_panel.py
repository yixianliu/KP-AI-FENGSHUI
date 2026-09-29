"""
大六壬起课结果展示面板
展示：基本信息 / 天地盘 / 四课 / 三传（门法）/ 十二天将 / 神煞 / 智能 解读。
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QScrollArea, QPushButton, QGridLayout, QSizePolicy,
                             QStackedWidget)
from PySide6.QtCore import (Qt, QPropertyAnimation, QEasingCurve, Property,
                            QPointF, QRectF)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
import math
from ui.styles import Stylesheets, Colors, Fonts, Spacing
# 别名导入：本模块多处存在局部变量 `icon = QLabel(...)`，用原名调用有遮蔽地雷风险
from ui.components.icons import icon as load_icon
from ui.components.collapsible_card import (CollapsibleCard, ai_section_header,
                                          highlight_label, probability_stats_widget,
                                          loading_panel, ResponsiveFlow,
                                          set_all_cards_collapsed)

# 文案常量：优先使用 ai_analysis_renderer 维护的单一权威源；缺失时退回本地兜底
try:  # 兼容独立导入 / API 层独立打包场景
    from ui.components.ai_analysis_renderer import (
        FINAL_VERDICT_TITLE,
        DISCLAIMER_TITLE,
        AI_SECTION_TITLE,
        _as_text,
    )
except Exception:
    FINAL_VERDICT_TITLE = '总体判断'
    DISCLAIMER_TITLE = '免责声明'
    AI_SECTION_TITLE = '龙虎山大师兄分析预测'
    def _as_text(v):
        # 兜底简化实现
        if v is None:
            return ''
        if isinstance(v, (list, tuple)):
            return '\n'.join(str(x) for x in v if x)
        if isinstance(v, dict):
            return '\n'.join(f'{k}: {v2}' for k, v2 in v.items())
        return str(v).strip()

# 地支五行对照表复用排盘引擎的定义，展示层不再自建一份
from core.divination.liuren import ZHI_WX
from core.ganzhi_constants import DI_ZHI
from ui.components.states import EmptyState

#: 五行 → 盘面标注文字色（面板局部色板，高饱和版）。
#: 刻意不用 Colors.WOOD/FIRE/... 令牌：那是深底提亮版，用于盘面背景块；
#: 此处是文字着色，需要更饱和才能在小字号下与暗底区分（单点使用，L393）。
#: 已知审计豁免，勿「顺手统一」为 Colors 五行色（会改变视觉）。
WX_COLOR = {
    '木': '#3a7d44', '火': '#c0392b', '土': '#b9770e',
    '金': '#5a5a5a', '水': '#2471a3',
}

#: 地盘绘制顺序（罗盘顺时针，自北「子」起），复用权威地支表
ZHI_ORDER = DI_ZHI


class RotatingLabel(QLabel):
    """支持 rotation 属性的 QLabel，用于在 paintEvent 中按角度旋转绘制。"""

    def __init__(self, text='☯', parent=None):
        """初始化旋转标签，默认显示太极符号，中心对齐。

        Args:
            text: 标签文本，默认太极符「☯」。
            parent: 父控件。
        """
        super().__init__(text, parent)
        self._angle = 0.0
        self.setAlignment(Qt.AlignCenter)

    def getRotation(self):
        """返回当前旋转角度（供 Qt 的 rotation 属性读取）。"""
        return self._angle

    def setRotation(self, value):
        """设置旋转角度并触发重绘（供 Qt 的 rotation 属性写入）。

        Args:
            value: 旋转角度，单位度。
        """
        self._angle = value
        self.update()

    rotation = Property(float, getRotation, setRotation)

    def paintEvent(self, event):
        """重写绘制：以控件中心为原点旋转坐标系后再绘制，实现太极动画。

        Args:
            event: 绘制事件。
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)
        painter.translate(-self.width() / 2, -self.height() / 2)
        super().paintEvent(event)


class _TiandiCompass(QWidget):
    """大六壬天地盘圆形罗盘（11.1）：12 地支环形排列（子北/午南/卯东/酉西），
    天盘支覆盖于地盘宫之上，天将标注于宫下，日支以鎏金描边高亮。

    绘制用 QPainter 完成；paintEvent 全程 try/except 包裹，避免虚函数抛错触发
    qFatal 闪退（exit 127）。尺寸随可用空间自适应（min 280px），窄屏下自动缩小。
    """

    def __init__(self, r, parent=None):
        """缓存起课数据并初始化罗盘控件。

        Args:
            r: 起课结果字典（含 tian_pan / tian_jiang / ri_gan / ri_zhi）。
            parent: Qt 父控件。
        """
        super().__init__(parent)
        self._r = r or {}
        tian_pan = self._r.get('tian_pan', {}) or {}
        self._tian_jiang = {t['pos']: t['jiang'] for t in self._r.get('tian_jiang', [])}
        self._ri_zhi = self._r.get('ri_zhi', '')
        self._ri_gan = self._r.get('ri_gan', '')
        # 每个宫位：(地盘支, 天盘支, 天将, 是否日支)
        self._positions = []
        for dz in ZHI_ORDER:
            tp = tian_pan.get(dz, dz)
            jiang = self._tian_jiang.get(dz, '')
            self._positions.append(
                (dz, tp, jiang, bool(self._ri_zhi) and dz == self._ri_zhi))
        self.setMinimumSize(280, 280)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):  # noqa: N802（Qt 命名）
        """重写绘制：try 包裹避免虚函数抛错导致进程闪退。"""
        try:
            self._draw()
        except Exception:
            pass

    @staticmethod
    def _q(hex_):
        """把 hex 颜色字符串转为 QColor。"""
        return QColor(hex_)

    def _draw(self):
        """绘制圆形罗盘：外环 + 12 宫位圆盘 + 中心盘。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        cx, cy = w / 2.0, h / 2.0
        R = min(w, h) / 2.0 - 26.0
        if R < 18:
            return

        # 外环装饰线
        painter.setPen(QPen(self._q(Colors.MO_LIGHT), 1))
        painter.drawEllipse(QPointF(cx, cy), R + 14, R + 14)
        painter.drawEllipse(QPointF(cx, cy), R + 6, R + 6)

        rd = max(13.0, R * 0.15)
        for i, (dz, tp, jiang, is_ri) in enumerate(self._positions):
            ang = math.radians(-90 + 30 * i)  # 子北起，顺时针每宫 30°
            px = cx + R * math.cos(ang)
            py = cy + R * math.sin(ang)

            # 宫位圆盘
            if is_ri:
                painter.setBrush(self._q(Colors.HIGHLIGHT_WARM))
                painter.setPen(QPen(self._q(Colors.LIUJIN), 2.5))
            else:
                painter.setBrush(self._q(Colors.BG))
                painter.setPen(QPen(self._q(Colors.BORDER_LIGHT), 1))
            painter.drawEllipse(QPointF(px, py), rd, rd)

            # 天盘支（朱红大字，居中）
            painter.setPen(self._q(Colors.ZHUSHA))
            f = QFont(Fonts.FAMILY_SERIF, max(11, int(rd * 0.95)))
            f.setBold(True)
            painter.setFont(f)
            self._draw_text(painter, px, py, tp)

            # 地盘宫（上方小字灰）
            painter.setPen(self._q(Colors.TEXT_TERTIARY))
            sf = QFont(Fonts.FAMILY_CN, max(9, int(rd * 0.55)))
            painter.setFont(sf)
            self._draw_text(painter, px, py - rd - 8, dz)

            # 天将（下方小字青）
            if jiang:
                painter.setPen(self._q(Colors.QINGHUA))
                painter.setFont(sf)
                self._draw_text(painter, px, py + rd + 8, jiang)

        # 中心圆盘
        cr = R * 0.30
        painter.setBrush(self._q(Colors.BG_DARK))
        painter.setPen(QPen(self._q(Colors.LIUJIN), 1.5))
        painter.drawEllipse(QPointF(cx, cy), cr, cr)
        painter.setPen(self._q(Colors.LIUJIN))
        painter.setFont(QFont(Fonts.FAMILY_CN, max(10, int(cr * 0.32))))
        self._draw_text(painter, cx, cy - cr * 0.18, '天地盘')
        if self._ri_gan or self._ri_zhi:
            painter.setPen(self._q(Colors.ZHUSHA))
            painter.setFont(QFont(Fonts.FAMILY_SERIF, max(11, int(cr * 0.38))))
            self._draw_text(painter, cx, cy + cr * 0.30, f'{self._ri_gan}{self._ri_zhi}')

    @staticmethod
    def _draw_text(painter, x, y, text):
        """在 (x, y) 居中点绘制文字（固定宽度矩形实现水平+垂直居中）。"""
        fm = painter.fontMetrics()
        rect = QRectF(x - 60, y - fm.height() / 2.0, 120, fm.height())
        painter.drawText(rect, Qt.AlignCenter, text)


class LiurenResultPanel(QWidget):
    """大六壬起课结果展示面板：呈现天地盘、四课、三传、十二天将、神煞及KP模型解读。"""

    def __init__(self, parent=None):
        """初始化面板，缓存当前起课结果与 智能 解读，并构建 UI。

        Args:
            parent: 父控件。
        """
        super().__init__(parent)
        self._current_result = {}
        self._current_智能 = {}  # 最近一次 智能 解读结果，供导出复用
        self.init_ui()

    def init_ui(self):
        """构建面板整体布局：标题栏（含「重新解读」「导出」按钮）、状态栏与滚动内容区。"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.BACKGROUND};
            }}
        """)

        main_layout = QVBoxLayout()
        card_padding = int(Spacing.CARD_PADDING.replace('px', ''))
        main_layout.setContentsMargins(card_padding, card_padding, card_padding, card_padding)
        main_layout.setSpacing(Spacing.S4)

        # 头部
        header_layout = QHBoxLayout()
        header_layout.setSpacing(Spacing.S3)
        title_icon = QLabel('☵')
        title_icon.setStyleSheet("font-size: 22px;")
        self.title_label = QLabel('大六壬起课结果')
        self.title_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_TITLE};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_SERIF};
            letter-spacing: 2px;
        """)
        header_layout.addWidget(title_icon)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.smart_analyze_btn = QPushButton('⚡ 智能分析')
        self.smart_analyze_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        self.smart_analyze_btn.setCursor(Qt.PointingHandCursor)
        self.smart_analyze_btn.setVisible(False)
        header_layout.addWidget(self.smart_analyze_btn)

        self.export_btn = QPushButton('导出')
        self.export_btn.setIcon(load_icon('export', 16))
        self.export_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setVisible(False)
        self.export_btn.clicked.connect(self._on_export_click)
        header_layout.addWidget(self.export_btn)

        # 全部卡片 收起/展开 切换按钮
        self.collapse_all_btn = QPushButton('全部收起')
        self.collapse_all_btn.setIcon(load_icon('collapse-all', 16))
        self.collapse_all_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)
        self.collapse_all_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_all_btn.setVisible(False)
        self.collapse_all_btn.clicked.connect(self._toggle_collapse_all)
        header_layout.addWidget(self.collapse_all_btn)

        main_layout.addLayout(header_layout)

        # 状态栏
        self.status_bar = QFrame()
        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        status_layout.setContentsMargins(Spacing.S4, Spacing.S_MARGIN_XS, Spacing.S4, Spacing.S_MARGIN_XS)
        status_layout.setAlignment(Qt.AlignCenter)
        self.status_label = QLabel('请完善左侧起课参数')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        status_layout.addWidget(self.status_label)
        main_layout.addWidget(self.status_bar)

        # 滚动区
        self.content_area = QScrollArea()
        self.content_area.setStyleSheet(Stylesheets.SCROLL_AREA)
        self.content_area.setWidgetResizable(True)
        self.content_area.setFrameShape(QFrame.NoFrame)

        self.content_widget = QWidget()
        self.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.content_widget.setStyleSheet(f"background-color: {Colors.BG};")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        self.content_layout.setSpacing(Spacing.S4)

        self.empty_state = self._create_empty_state()
        self.content_layout.addWidget(self.empty_state)

        self.content_area.setWidget(self.content_widget)
        main_layout.addWidget(self.content_area)
        self.setLayout(main_layout)

    # ---------- 空状态 ----------
    def _create_empty_state(self):
        """创建空状态，委托 EmptyState（M3-6：统一视觉语言 + 引导动效）。

        保留对外方法签名，避免破坏既有测试契约（返回 QWidget 实例）。
        """
        from ui.components.states import EmptyState
        empty = EmptyState(
            title='请完善左侧起课参数',
            hint='点击「起课」获取大六壬天地盘与三传分析',
            icon='☵',
            color=Colors.TEXT3,
            parent=self.content_widget,
        )
        return empty

    def _toggle_collapse_all(self):
        """一键收起/展开全部结果卡片，并联动按钮文案。"""
        cards = self.content_widget.findChildren(CollapsibleCard)
        any_expanded = any(not c.is_collapsed() for c in cards)
        set_all_cards_collapsed(self.content_widget, collapsed=any_expanded)
        self.collapse_all_btn.setText('全部展开' if any_expanded else '全部收起')

    # ---------- 通用卡片（统一复用 CollapsibleCard） ----------
    def _create_result_card(self, title, icon, content_widget, highlight=False):
        """创建结果卡片（统一复用 CollapsibleCard：左侧强调色条 + 图标 + 标题，可折叠）。

        配色：排盘类卡片用青色条(Colors.QINGHUA)，AI/强调类用鎏金色条(Colors.LIUJIN)，
        与八字、梅花易数面板保持一致。

        占位卡片（标题为 AI_SECTION_TITLE）会额外打上 objectName 锚点，
        供 _clear_ai_placeholder 精准删除，避免遍历整个布局寻找。
        """
        accent = Colors.LIUJIN if highlight else Colors.QINGHUA
        card = CollapsibleCard(title, icon, accent_color=accent, collapsed=False)
        if title == AI_SECTION_TITLE:
            card.setObjectName(self._AI_PLACEHOLDER_OBJECT_NAME)
            # 内容 widget 上保留原属性作为兼容查询路径（不会成为主路径）
            try:
                content_widget.setProperty('is_placeholder', True)
            except Exception:
                pass
        card.set_content(content_widget)
        return card

    @staticmethod
    def _wx_chip(text, wx):
        """生成五行标签小色块（chip），按五行配色渲染背景，直观展示地支所属五行。

        Args:
            text: 标签文字（如地支）。
            wx: 五行名（木/火/土/金/水），决定背景色。

        Returns:
            渲染好的 QLabel。
        """
        chip = QLabel(text)
        color = WX_COLOR.get(wx, Colors.TEXT_SECONDARY)
        chip.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL}; font-family: {Fonts.FAMILY_CN};
            color: {Colors.WHITE}; background-color: {color};
            border-radius: 4px; padding: 2px 8px;
        """)
        chip.setAlignment(Qt.AlignCenter)
        return chip

    # ---------- 基本信息 ----------
    def _basic_info_card(self, r):
        """构建「基本信息」卡片：起课方式、占问、日干支、月将、占时等起课元数据。

        Args:
            r: 起课结果字典。

        Returns:
            渲染好的 QWidget。
        """
        rows = [
            ('起课方式', r.get('method_name', '')),
            ('占问', r.get('question') or '—'),
            ('时间', r.get('time', '')),
            ('日干支', f"{r.get('ri_gan','')}{r.get('ri_zhi','')}（{r.get('ri_gan_wx','')}）"),
            ('月将', f"{r.get('yue_jiang_name','')}（{r.get('yue_jiang','')}）"),
            ('占时', r.get('zhan_shi', '')),
        ]
        # 行式布局：鎏金微光小药丸标签 + 粗体值 + 行间细分隔（与梅花「起卦信息」一致）
        vlay = QVBoxLayout()
        vlay.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        vlay.setSpacing(Spacing.S0)
        for i, (k, v) in enumerate(rows):
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(Spacing.S_MARGIN_XS, Spacing.S2, Spacing.S_MARGIN_XS, Spacing.S2)
            rl.setSpacing(Spacing.S3)
            kl = QLabel(k)
            kl.setFixedWidth(64)
            kl.setAlignment(Qt.AlignCenter)
            kl.setStyleSheet(f"""
                font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT2};
                font-weight: {Fonts.W_MEDIUM}; font-family: {Fonts.BODY};
                background-color: {Colors.HIGHLIGHT_GLOW};
                border-radius: {Spacing.RADIUS_SM}; padding: 3px 6px;
            """)
            vl = QLabel(str(v))
            vl.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; font-family: {Fonts.BODY}; line-height: 1.5;")
            vl.setWordWrap(True)
            rl.addWidget(kl)
            rl.addWidget(vl, 1)
            vlay.addWidget(row)
            if i < len(rows) - 1:
                div = QFrame()
                div.setFixedHeight(1)
                div.setStyleSheet(f"background: {Colors.DIVIDER}; margin: 0 10px;")
                vlay.addWidget(div)
        w = QWidget(); w.setLayout(vlay)
        return w

    # ---------- 天地盘 ----------
    def _tiandi_card(self, r):
        """构建「天地盘」卡片：默认圆形罗盘视图（11.1），并提供卡片列表视图切换。

        罗盘视图：12 地支环形排列（子北/午南/卯东/酉西），天盘支覆盖于地盘宫之上，
        天将标注于宫下，日支以鎏金描边高亮；窄屏或偏好时可切换为卡片流（保留原样式）。

        Args:
            r: 起课结果字典。

        Returns:
            渲染好的 QWidget。
        """
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        vlay = QVBoxLayout(w)
        vlay.setContentsMargins(Spacing.S1, Spacing.S1, Spacing.S1, Spacing.S1)
        vlay.setSpacing(Spacing.S3)

        # 图例
        legend = QLabel('▍地盘为宫位（小字灰）｜天盘为加临之支（大字朱）｜天将为临宫神将')
        legend.setStyleSheet(
            f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT_TERTIARY}; "
            f"font-family: {Fonts.FAMILY_CN}; background: transparent;")
        legend.setWordWrap(True)
        vlay.addWidget(legend)

        # 视图切换（罗盘 / 卡片列表），窄屏默认卡片列表
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(Spacing.S2)
        self._td_compass_btn = QPushButton('◎ 罗盘')
        self._td_list_btn = QPushButton('▤ 卡片')
        for b in (self._td_compass_btn, self._td_list_btn):
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(30)
            b.clicked.connect(
                lambda _=False, btn=b: self._set_tiandi_view(
                    0 if btn is self._td_compass_btn else 1))
        toggle_row.addStretch()
        toggle_row.addWidget(self._td_compass_btn)
        toggle_row.addWidget(self._td_list_btn)
        vlay.addLayout(toggle_row)

        self._td_stack = QStackedWidget()
        self._td_compass = _TiandiCompass(r)
        self._td_list = self._tiandi_list_widget(r)
        self._td_stack.addWidget(self._td_compass)  # index 0：罗盘
        self._td_stack.addWidget(self._td_list)      # index 1：卡片
        vlay.addWidget(self._td_stack, 1)

        # 默认视图：宽屏用罗盘，窄屏（<520px）降级为卡片列表
        self._set_tiandi_view(1 if (self.width() or 900) < 520 else 0)
        return w

    def _set_tiandi_view(self, idx: int):
        """切换天地盘视图（0=罗盘 / 1=卡片），并联动按钮高亮状态。"""
        if not hasattr(self, '_td_stack'):
            return
        try:
            self._td_stack.setCurrentIndex(idx)
            on, off = Stylesheets.BUTTON_PRIMARY, Stylesheets.BUTTON_SECONDARY
            self._td_compass_btn.setStyleSheet(on if idx == 0 else off)
            self._td_list_btn.setStyleSheet(on if idx == 1 else off)
        except RuntimeError:
            pass

    def _tiandi_list_widget(self, r):
        """天地盘卡片流（窄屏/列表视图）：12 宫位卡片，地盘宫/天盘支/天将。"""
        tian_pan = r.get('tian_pan', {})
        # 预建「宫位→天将」映射，便于按地支宫快速取对应天将
        tian_jiang = {t['pos']: t['jiang'] for t in r.get('tian_jiang', [])}
        ri_zhi = r.get('ri_zhi', '')

        flow = ResponsiveFlow(min_item_width=72, max_cols=12, min_cols=4, spacing=6)
        for dz in ZHI_ORDER:
            tp = tian_pan.get(dz, dz)
            jiang = tian_jiang.get(dz, '')
            is_ri = bool(ri_zhi) and dz == ri_zhi

            cell = QFrame()
            if is_ri:
                cell.setStyleSheet(f"""
                    QFrame {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 {Colors.HIGHLIGHT_WARM_STRONG}, stop:1 {Colors.HIGHLIGHT_WARM});
                        border: 1.5px solid {Colors.LIUJIN};
                        border-radius: {Spacing.RADIUS_SM};
                    }}
                """)
            else:
                cell.setStyleSheet(f"""
                    QFrame {{
                        background: {Colors.BG};
                        border: 1px solid {Colors.BORDER_LIGHT};
                        border-radius: {Spacing.RADIUS_SM};
                    }}
                    QFrame:hover {{
                        border-color: {Colors.QINGHUA_LIGHT};
                    }}
                """)
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(Spacing.S_MIN, Spacing.S_PAD_SM, Spacing.S_MIN, Spacing.S_PAD_SM)
            cl.setSpacing(Spacing.S1)

            # 地盘宫位（灰小字）
            gong = QLabel(dz + ('·日' if is_ri else ''))
            gong.setAlignment(Qt.AlignCenter)
            gong.setStyleSheet(
                f"font-size: {Fonts.SZ_MICRO}; color: {Colors.LIUJIN if is_ri else Colors.TEXT_TERTIARY}; "
                f"font-family: {Fonts.FAMILY_CN}; background: transparent;")
            # 天盘支（朱红大字）
            tian = QLabel(tp)
            tian.setAlignment(Qt.AlignCenter)
            tian.setStyleSheet(
                f"font-size: 17px; color: {Colors.ZHUSHA}; font-family: {Fonts.FAMILY_SERIF}; "
                f"font-weight: {Fonts.WEIGHT_BOLD}; background: transparent;")
            # 天将（青灰小字）
            jiang_lbl = QLabel(jiang)
            jiang_lbl.setAlignment(Qt.AlignCenter)
            jiang_lbl.setStyleSheet(
                f"font-size: {Fonts.SZ_MICRO}; color: {Colors.QINGHUA}; "
                f"font-family: {Fonts.FAMILY_CN}; background: transparent;")
            cl.addWidget(gong)
            cl.addWidget(tian)
            cl.addWidget(jiang_lbl)
            flow.add_widget(cell)

        return flow

    # ---------- 四课 ----------
    def _sike_card(self, r):
        """构建「四课」卡片：干上/干阴/支上/支阴四课，展示日干支上下神及五行关系。

        四课由日干、日支分别取其上神（天盘）与下神（地盘）构成，是立三传的依据。

        Args:
            r: 起课结果字典。

        Returns:
            渲染好的 QWidget。
        """
        si_ke = r.get('si_ke', {})
        order = [('干上（第一课）', 'gan_shang'), ('干阴（第二课）', 'gan_yin'),
                  ('支上（第三课）', 'zhi_shang'), ('支阴（第四课）', 'zhi_yin')]
        grid = QGridLayout()
        grid.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        grid.setSpacing(Spacing.S3)
        grid.setColumnStretch(1, 1)
        for i, (label, key) in enumerate(order):
            v = si_ke.get(key, {})
            kl = QLabel(label)
            kl.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; font-family: {Fonts.FAMILY_CN};")
            kl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            kl.setFixedWidth(110)
            # 四课表达为「本神 → 天盘上神」，箭头直观体现上下神生克关系
            formula = QLabel(f"{v.get('dizhi','')} → {v.get('tianpan','')}")
            formula.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY}; font-family: {Fonts.FAMILY_CN};")
            formula.setAlignment(Qt.AlignCenter)
            grid.addWidget(kl, i, 0)
            grid.addWidget(formula, i, 1)
            chip = self._wx_chip(v.get('wx', ''), v.get('wx', ''))
            grid.addWidget(chip, i, 2)
        w = QWidget(); w.setLayout(grid)
        return w

    # ---------- 三传 ----------
    def _sanchuan_card(self, r):
        """构建「三传」卡片：初传、中传、末传（即贼克/比用等取传门法得出的三传序列）。

        三传揭示事态发端、过程与结局，门法（gate）说明取用哪一传法的规则。

        Args:
            r: 起课结果字典。

        Returns:
            渲染好的 QWidget。
        """
        sc = r.get('san_chuan', {})
        gate = sc.get('gate', '')

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        vlay = QVBoxLayout(w)
        vlay.setContentsMargins(Spacing.S1, Spacing.S1, Spacing.S1, Spacing.S1)
        vlay.setSpacing(Spacing.S3)

        # 门法徽章（置顶）
        if gate:
            gate_row = QHBoxLayout()
            gate_row.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
            gate_row.setAlignment(Qt.AlignCenter)
            gate_lab = QLabel(f'⌘ 取用法：{gate}')
            gate_lab.setStyleSheet(f"""
                font-size: {Fonts.SIZE_SMALL}; color: {Colors.LIUJIN};
                font-family: {Fonts.FAMILY_CN}; font-weight: {Fonts.WEIGHT_BOLD};
                background: {Colors.HIGHLIGHT_GLOW};
                border: 1px solid {Colors.LIUJIN};
                border-radius: {Spacing.RADIUS_SM}; padding: 4px 14px;
            """)
            gate_row.addWidget(gate_lab)
            vlay.addLayout(gate_row)

        # 三传响应式卡片：宽屏横排、窄屏纵向堆叠
        # 三色高亮（方案 §11.2）：初传鎏金 / 中传古金 / 末传靛蓝
        flow = ResponsiveFlow(min_item_width=170, max_cols=3, min_cols=1, spacing=12)
        items = [('初传 · 发端', sc.get('chu', ''), 'liujin'),
                 ('中传 · 过程', sc.get('zhong', ''), 'qinghua'),
                 ('末传 · 归结', sc.get('mo', ''), 'dianqing')]
        for label, val, style in items:
            card = QFrame()
            if style == 'liujin':
                card.setStyleSheet(f"""
                    QFrame {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 {Colors.HIGHLIGHT_WARM_STRONG}, stop:1 {Colors.HIGHLIGHT_WARM});
                        border: 1.5px solid {Colors.LIUJIN};
                        border-radius: {Spacing.RADIUS};
                    }}
                """)
                val_color = Colors.LIUJIN
            elif style == 'dianqing':
                card.setStyleSheet(f"""
                    QFrame {{
                        background: {Colors.BG_DARK};
                        border: 1px solid {Colors.DIANQING};
                        border-radius: {Spacing.RADIUS};
                    }}
                """)
                val_color = Colors.DIANQING
            else:
                card.setStyleSheet(f"""
                    QFrame {{
                        background: {Colors.BG};
                        border: 1px solid {Colors.QINGHUA};
                        border-radius: {Spacing.RADIUS};
                    }}
                """)
                val_color = Colors.QINGHUA
            cl = QVBoxLayout(card)
            cl.setContentsMargins(Spacing.S_MARGIN_XS, Spacing.S_MARGIN_XS, Spacing.S_MARGIN_XS, Spacing.S_MARGIN_XS)
            cl.setSpacing(Spacing.S1)
            lab = QLabel(label)
            lab.setAlignment(Qt.AlignCenter)
            lab.setStyleSheet(
                f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; "
                f"font-family: {Fonts.FAMILY_CN}; background: transparent;")
            val_lab = QLabel(val or '—')
            val_lab.setAlignment(Qt.AlignCenter)
            val_lab.setStyleSheet(
                f"font-size: 24px; color: {val_color}; font-family: {Fonts.FAMILY_SERIF}; "
                f"font-weight: {Fonts.WEIGHT_BOLD}; background: transparent;")
            cl.addWidget(lab)
            cl.addWidget(val_lab)
            flow.add_widget(card)
        vlay.addWidget(flow)

        tip = QLabel('※ 初传主事之发端、中传主事之中途变化、末传主事之最终结局。')
        tip.setWordWrap(True)
        tip.setStyleSheet(
            f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT_TERTIARY}; "
            f"font-family: {Fonts.FAMILY_CN}; background: transparent;")
        vlay.addWidget(tip)
        return w

    # ---------- 十二天将 ----------
    #: 天将吉凶分类（传统六壬：贵人/六合/青龙/太常/太阴/天后为吉将；
    #: 螣蛇/朱雀/勾陈/天空/白虎/玄武为凶将，朱雀亦主文书）
    _JIANG_GOOD = {'贵人', '六合', '青龙', '太常', '太阴', '天后'}
    _JIANG_BAD = {'螣蛇', '腾蛇', '朱雀', '勾陈', '天空', '白虎', '玄武'}

    def _tianjiang_card(self, r):
        """构建「十二天将」卡片：宫位—天盘—天将三元组卡片化展示，吉将绿、凶将红。

        Args:
            r: 起课结果字典。

        Returns:
            渲染好的 QWidget。
        """
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        vlay = QVBoxLayout(w)
        vlay.setContentsMargins(Spacing.S1, Spacing.S1, Spacing.S1, Spacing.S1)
        vlay.setSpacing(Spacing.S2)

        legend = QLabel('▍吉将（贵人/六合/青龙/太常/太阴/天后）标绿｜凶将（螣蛇/朱雀/勾陈/天空/白虎/玄武）标红')
        legend.setWordWrap(True)
        legend.setStyleSheet(
            f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT_TERTIARY}; "
            f"font-family: {Fonts.FAMILY_CN}; background: transparent;")
        vlay.addWidget(legend)

        flow = ResponsiveFlow(min_item_width=200, max_cols=3, min_cols=1, spacing=8)
        for t in r.get('tian_jiang', []):
            jiang = t.get('jiang', '')
            is_good = jiang in self._JIANG_GOOD
            is_bad = jiang in self._JIANG_BAD
            if is_good:
                bg, fg, border = Colors.SUCCESS_LIGHT, Colors.SUCCESS, Colors.SUCCESS
            elif is_bad:
                bg, fg, border = Colors.DANGER_LIGHT, Colors.DANGER, Colors.DANGER
            else:
                bg, fg, border = Colors.QINGHUA_LIGHT, Colors.QINGHUA, Colors.QINGHUA_LIGHT

            cell = QFrame()
            cell.setStyleSheet(f"""
                QFrame {{
                    background: {bg};
                    border: 1px solid {border};
                    border-radius: {Spacing.RADIUS_SM};
                }}
            """)
            cl = QHBoxLayout(cell)
            cl.setContentsMargins(Spacing.S_MARGIN_XS, Spacing.S_PAD_SM, Spacing.S_MARGIN_XS, Spacing.S_PAD_SM)
            cl.setSpacing(Spacing.S2)
            pos_lbl = QLabel(f"{t.get('pos', '')}宫")
            pos_lbl.setStyleSheet(
                f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT_TERTIARY}; "
                f"font-family: {Fonts.FAMILY_CN}; background: transparent;")
            tp_lbl = QLabel(t.get('tianpan', ''))
            tp_lbl.setStyleSheet(
                f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_PRIMARY}; "
                f"font-family: {Fonts.FAMILY_SERIF}; font-weight: {Fonts.WEIGHT_BOLD}; background: transparent;")
            jiang_lbl = QLabel(jiang)
            jiang_lbl.setStyleSheet(
                f"font-size: {Fonts.SIZE_SMALL}; color: {fg}; "
                f"font-family: {Fonts.FAMILY_CN}; font-weight: {Fonts.WEIGHT_BOLD}; background: transparent;")
            cl.addWidget(pos_lbl)
            cl.addStretch()
            cl.addWidget(tp_lbl)
            cl.addWidget(jiang_lbl)
            flow.add_widget(cell)
        vlay.addWidget(flow)
        return w

    # ---------- 神煞 ----------
    def _shensha_card(self, r):
        """构建「神煞」卡片：展示本课所临吉凶神煞（如贵人、驿马、劫煞等）及其含义。

        Args:
            r: 起课结果字典。

        Returns:
            渲染好的 QWidget。
        """
        sha = r.get('shen_sha', {})
        layout = QVBoxLayout()
        layout.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        layout.setSpacing(Spacing.S2)
        if not sha:
            layout.addWidget(self._muted('本课无明显神煞'))
        else:
            for k, v in sha.items():
                row = QHBoxLayout()
                row.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
                kl = QLabel(k)
                kl.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; font-family: {Fonts.FAMILY_CN};")
                kl.setFixedWidth(60)
                vl = QLabel(str(v))
                vl.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY}; font-family: {Fonts.FAMILY_CN};")
                vl.setWordWrap(True)
                row.addWidget(kl); row.addWidget(vl, 1)
                layout.addLayout(row)
        w = QWidget(); w.setLayout(layout)
        return w

    @staticmethod
    def _muted(text):
        """生成弱化样式的灰色提示文字（用于占位或「无内容」说明）。

        Args:
            text: 提示文字。

        Returns:
            渲染好的 QLabel。
        """
        l = QLabel(text)
        l.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; font-family: {Fonts.FAMILY_CN};")
        return l

    @staticmethod
    def _safe_set_visible(widget, visible: bool):
        """安全切换可见性：防御 C++ 对象已被销毁（deleteLater 后）的悬空引用。"""
        if widget is None:
            return
        try:
            widget.setVisible(visible)
        except RuntimeError:
            # 底层 C++ 对象已被销毁，忽略
            pass

    # ---------- 智能 解读占位 ----------
    # 占位卡片稳定锚点：_clear_ai_placeholder 靠此 objectName 精准定位并删除，
    # 不依赖不可靠的 dynamicProperty 或 windowTitle，避免出现死循环导致白屏卡死。
    _AI_PLACEHOLDER_OBJECT_NAME = 'ai_placeholder_card_liuren'

    def _placeholder(self):
        """创建 AI_SECTION_TITLE 卡片的占位内容，提示解读将在起课后生成。"""
        w = QWidget()
        w.setProperty('is_placeholder', True)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        layout.setSpacing(Spacing.S3)
        layout.addWidget(self._muted(f'{AI_SECTION_TITLE}将在起课后自动生成，或点击右上角「重新解读」。'))
        return w

    # ---------- 对外入口 ----------
    def _clear_dynamic_content(self):
        """清理动态内容控件（empty_state 为持久控件，绝不可删除）。"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w and w is not self.empty_state:
                w.deleteLater()

    def show_loading(self, text='正在起课，请稍候…', ai: bool = False):
        """显示加载状态：内容区旋转太极动画 + 状态栏文案。

        Args:
            text: 主提示文案。
            ai:   True 为龙虎山大师兄解读加载（鎏金主题）；
                  False 为起课加载（青花蓝主题）。
        """
        self.status_label.setText('⏳ ' + text)
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY}; color: {Colors.LIUJIN if ai else Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN}; font-weight: {Fonts.WEIGHT_BOLD if ai else Fonts.WEIGHT_NORMAL};
        """)
        self._safe_set_visible(self.empty_state, False)
        self.smart_analyze_btn.setVisible(False)
        self.export_btn.setVisible(False)
        if hasattr(self, 'collapse_all_btn'):
            self.collapse_all_btn.setVisible(False)

        # 清理旧动态内容后挂载加载面板
        self._clear_dynamic_content()
        if ai:
            panel = loading_panel(
                message=text or '龙虎山大师兄正在解读六壬玄机…',
                sub='请稍候，大师兄正依四课三传、天将神煞逐项推演',
                color=Colors.LIUJIN,
                hints=['大师兄正凝神审课…', '正在推敲四课生克…',
                       '正在研判三传发用与门法…', '正在参详天将吉凶与应期…'])
        else:
            panel = loading_panel(
                message=text or '正在起课，请稍候…',
                sub='月将加时，天地盘排布中',
                color=Colors.QINGHUA,
                hints=['正在排布天地盘…', '正在立四课…',
                       '正在发三传、定门法…', '正在布十二天将与神煞…'])
        panel.setMinimumHeight(360)
        self.content_layout.addWidget(panel)

    def show_ai_loading(self, text='龙虎山大师兄正在解读六壬玄机…'):
        """显示 AI 解读加载状态（鎏金主题，供主窗口统一调用）。

        Args:
            text: 主提示文案。
        """
        self.show_loading(text, ai=True)

    def display_result(self, result_data):
        """对外入口：接收起课结果并渲染全部卡片（基本信息/天地盘/四课/三传/天将/神煞/智能 占位）。

        Args:
            result_data: 排盘引擎返回的起课结果字典。
        """
        try:
            # 清理旧内容（含加载动画）；empty_state 是持久控件，绝不可 deleteLater
            self._clear_dynamic_content()
            self._current_result = result_data
            self._safe_set_visible(self.empty_state, False)
            if hasattr(self, 'export_btn'):
                self.export_btn.setVisible(True)
            if hasattr(self, 'collapse_all_btn'):
                self.collapse_all_btn.setVisible(True)
                self.collapse_all_btn.setText('全部收起')

            self.status_label.setText('✓ 起课完成，天地盘已生成')
            self.status_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY}; color: {Colors.SUCCESS};
                font-family: {Fonts.FAMILY_CN}; font-weight: {Fonts.WEIGHT_BOLD};
            """)

            self.content_layout.addWidget(
                self._create_result_card('基本信息', '📋', self._basic_info_card(result_data)))
            self.content_layout.addWidget(
                self._create_result_card('天地盘', '🌐', self._tiandi_card(result_data)))
            self.content_layout.addWidget(
                self._create_result_card('四课', '📜', self._sike_card(result_data)))
            self.content_layout.addWidget(
                self._create_result_card('三传', '⚡', self._sanchuan_card(result_data), highlight=True))
            self.content_layout.addWidget(
                self._create_result_card('十二天将', '🐉', self._tianjiang_card(result_data)))
            self.content_layout.addWidget(
                self._create_result_card('神煞', '✨', self._shensha_card(result_data)))
            # 智能 占位
            self.content_layout.addWidget(
                self._create_result_card(AI_SECTION_TITLE, '🧙', self._placeholder(), highlight=True))

            self.smart_analyze_btn.setVisible(True)
            self.smart_analyze_btn.setEnabled(True)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _clear_ai_placeholder(self):
        """移除 AI_SECTION_TITLE 占位卡片，为 AI 结果腾出位置。

        实现要点（修复历史白屏卡死）：
        1. 优先按 objectName 锚点（_AI_PLACEHOLDER_OBJECT_NAME）精确删除，单次匹配即退出。
        2. 找不到时回退按标题匹配，同样只删首个匹配项，绝不进入 while 死循环。
        3. 整个遍历最多扫一遍布局（最多 N 次），不会出现「永不退出」的 while 循环。
        """
        removed = False
        # 主路径：按 objectName 精确锚点
        placeholder = self.findChild(QWidget, self._AI_PLACEHOLDER_OBJECT_NAME)
        if placeholder is not None:
            self.content_layout.removeWidget(placeholder)
            placeholder.deleteLater()
            removed = True
        if removed:
            return

        # 兜底路径：从后向前扫描一次，按标题匹配第一个占位卡
        for i in range(self.content_layout.count() - 1, -1, -1):
            item = self.content_layout.itemAt(i)
            if item is None:
                continue
            w = item.widget()
            if w is None:
                continue
            # 占位卡是 CollapsibleCard，外层无 windowTitle，靠子 QLabel 文本判定
            # 同时仍兼容旧的 is_placeholder 属性
            if w.property('is_placeholder'):
                self.content_layout.removeWidget(w)
                w.deleteLater()
                return
            # 标题文本匹配：扫描子 QLabel
            for lbl in w.findChildren(QLabel):
                if AI_SECTION_TITLE in (lbl.text() or ''):
                    self.content_layout.removeWidget(w)
                    w.deleteLater()
                    return

    def display_ai_analysis_result(self, smart_analysis):
        """显示智能分析结果（别名方法，兼容调用方使用 display_ai_analysis_result 的情况）"""
        self.display_analysis_result(smart_analysis)

    def display_analysis_result(self, smart_analysis):
        """将AI结构化解读渲染到面板。

        修复点：
        1. 渲染前先清掉「占位卡」与历史 AI 渲染容器（ai_analysis_container），
           防止多次起课或旧 worker 完成回调产生两份 AI 解读；
        2. 渲染后恢复状态栏文案与样式，提示「解读完成」，
           避免「解读中…」一直挂着的体验问题。
        """
        # 若 AI 未配置，则不显示龙虎山大师兄分析预测
        try:
            from core.ai_config import is_ai_configured
            if not is_ai_configured():
                self._clear_ai_placeholder()
                self._clear_prev_ai_container()
                return
        except Exception:
            pass
        # 1) 清掉占位卡 + 历次 AI 渲染容器，避免重复追加
        self._clear_ai_placeholder()
        self._clear_prev_ai_container()
        # 缓存解读结果供导出（PDF/Excel/CSV）复用
        if isinstance(smart_analysis, dict):
            self._current_智能 = smart_analysis
        from ui.components.ai_analysis_renderer import render_analysis as render
        render('liuren', smart_analysis, self.content_layout)

        # 2) 恢复顶部状态栏：AI 已完成（不再停留在「解读中…」）
        try:
            self.status_label.setText('✓ 龙虎山大师兄解读完成')
            self.status_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.SUCCESS};
                font-family: {Fonts.FAMILY_CN};
                font-weight: {Fonts.WEIGHT_BOLD};
            """)
        except Exception:
            pass

    def _clear_prev_ai_container(self):
        """移除上一次 AI 解读渲染时插入的容器（ai_analysis_container），
        防止连续起课/重复完成回调导致两份 AI 解读并存。"""
        try:
            for i in range(self.content_layout.count() - 1, -1, -1):
                item = self.content_layout.itemAt(i)
                if item is None:
                    continue
                w = item.widget()
                if w is None:
                    continue
                if w.objectName() == 'ai_analysis_container':
                    self.content_layout.removeWidget(w)
                    w.deleteLater()
                    return
        except Exception:
            pass

    def _body(self, ai):
        """返回 智能 各子项的折叠卡片列表（与八字/梅花面板一致）。

        字段契约以 core.analysis_storage._JSON_SCHEMAS['liuren'] 为准：
        final_verdict / analysis / scenario_advice / historical_cases /
        probability_stats / timing / disclaimer。
        注意：ke_overview / si_ke_analysis 等为历史废弃键，AI 已不再产出，必须移除；
        其中『综合建议』对应 AI 的 scenario_advice（而非 final_verdict），否则会误把
        空泛的总体断语当建议展示（曾出现『课体未成，事机未现，无所指归』占位语）。
        """
        cards = []
        sections = [
            (FINAL_VERDICT_TITLE, '🎯', Colors.QINGHUA, ai.get('final_verdict')),
            ('课体分析', '☯', Colors.LIUJIN, ai.get('analysis')),
            ('综合建议', '✨', Colors.ZHUSHA, ai.get('scenario_advice')),
            ('应期时机', '⏳', Colors.SUCCESS, ai.get('timing')),
            ('历史案例', '📚', Colors.QINGHUA, ai.get('historical_cases')),
            ('概率统计', '📊', Colors.LIUJIN, ai.get('probability_stats')),
            (DISCLAIMER_TITLE, '⚠', Colors.TEXT_TERTIARY, ai.get('disclaimer')),
        ]
        _PROBABILITY_TITLE = '概率统计'
        for title, icon, color, text in sections:
            if text is None:
                continue
            # 概率统计需要可视化展示（标签+进度条+说明），不走纯文本
            if title == '概率统计':
                if isinstance(text, (list, tuple)):
                    items = [_as_text(x) for x in text if _as_text(x).strip()]
                else:
                    items = [_as_text(text)]
                items = [i for i in items if i and i.strip()]
                if not items:
                    continue
                card = CollapsibleCard(title, icon, accent_color=color, collapsed=False)
                card.set_content(probability_stats_widget(items, color))
                cards.append(card)
                continue
            # 统一使用归一化函数处理 dict/list/str，避免 JSON repr 显示
            text = _as_text(text).strip()
            if not text:
                continue

            # 结论段落优先级更高亮；正文走统一重点提示渲染
            if title == '总体判断':
                card = CollapsibleCard(title, icon, accent_color=color, collapsed=False)
                card.set_content(conclusion_block(text, color))
            else:
                card = CollapsibleCard(title, icon, accent_color=color, collapsed=False)
                card.set_content(risk_aware_label(text, color=Colors.LIUJIN, show_sentiment=False))
            cards.append(card)
        return cards

    def clear(self):
        """清空面板：移除动态内容、恢复空状态占位与初始提示文案，并隐藏操作按钮。"""
        # 清理动态内容；empty_state 持久控件不可删除
        self._clear_dynamic_content()
        # 仅当 empty_state 不在布局中时才挂载（避免重复 addWidget）
        if self.content_layout.indexOf(self.empty_state) == -1:
            self.content_layout.addWidget(self.empty_state)
        self._safe_set_visible(self.empty_state, True)
        self.smart_analyze_btn.setVisible(False)
        self.export_btn.setVisible(False)
        if hasattr(self, 'collapse_all_btn'):
            self.collapse_all_btn.setVisible(False)
        self.status_label.setText('请完善左侧起课参数')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        self._current_result = {}

    def get_liuren_data_for_ai(self):
        """供 智能 管道消费的结构化取数。"""
        r = getattr(self, '_current_result', {}) or {}
        if not r:
            return {}
        si_ke = r.get('si_ke', {})
        sc = r.get('san_chuan', {})
        return {
            'method_name': r.get('method_name', ''),
            'question': r.get('question', ''),
            'time': r.get('time', ''),
            'ri_gan': r.get('ri_gan', ''),
            'ri_zhi': r.get('ri_zhi', ''),
            'ri_gan_wx': r.get('ri_gan_wx', ''),
            'yue_jiang': r.get('yue_jiang_name', '') + '（' + r.get('yue_jiang', '') + '）',
            'zhan_shi': r.get('zhan_shi', ''),
            'tian_pan': r.get('tian_pan', {}),
            'si_ke': {
                'gan_shang': si_ke.get('gan_shang', {}).get('tianpan', ''),
                'gan_yin': si_ke.get('gan_yin', {}).get('tianpan', ''),
                'zhi_shang': si_ke.get('zhi_shang', {}).get('tianpan', ''),
                'zhi_yin': si_ke.get('zhi_yin', {}).get('tianpan', ''),
            },
            'san_chuan': {
                'chu': sc.get('chu', ''),
                'zhong': sc.get('zhong', ''),
                'mo': sc.get('mo', ''),
                'gate': sc.get('gate', ''),
            },
            'tian_jiang': r.get('tian_jiang', []),  # 保留 dict 列表，供 AI fallback 分析使用
            'shen_sha': r.get('shen_sha', {}),
        }

    def _on_export_click(self):
        """导出大六壬起课结果（复用 ExportDialog 与三导出器）。"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox, QDialog
        from ui.components.export_dialog import ExportDialog
        from ui.export import CsvExporter, ExcelExporter
        from ui.export.base_exporter import filter_export_data

        rd = getattr(self, '_current_result', None)
        if not rd:
            QMessageBox.warning(self, '导出失败', '暂无可导出的起课结果')
            return

        # 组装导出数据：liuren_data = 起课结果, liuren_智能 = KP模型解读
        export_data = {
            'liuren_data': dict(rd),
            'basic_info': {'pan_type': '大六壬'},
        }
        智能 = getattr(self, '_current_智能', None)
        if isinstance(智能, dict) and 智能:
            export_data['liuren_ai'] = 智能

        dialog = ExportDialog(export_data, parent=self)
        dialog.filename_edit.setText('大六壬')
        if dialog.exec() == QDialog.DialogCode.Accepted:
            format_type = dialog.get_selected_format()
            chapters = dialog.get_selected_chapters()
            export_data = filter_export_data(export_data, chapters)

            filename = dialog.filename_edit.text().strip() or '大六壬'
            if format_type == 'csv':
                ext, file_filter = '.csv', 'CSV Files (*.csv)'
            elif format_type == 'excel':
                ext, file_filter = '.xlsx', 'Excel Files (*.xlsx)'
            else:
                ext, file_filter = '.pdf', 'PDF Files (*.pdf)'

            file_path, _ = QFileDialog.getSaveFileName(
                self, '导出大六壬起课结果', filename + ext, file_filter)
            if not file_path:
                return
            try:
                if format_type == 'csv':
                    exporter = CsvExporter()
                elif format_type == 'excel':
                    exporter = ExcelExporter()
                else:
                    try:
                        from ui.export import PdfExporter
                    except Exception:
                        QMessageBox.warning(
                            self, '导出失败',
                            '未安装 reportlab，无法导出 PDF。\n请执行：pip install reportlab')
                        return
                    exporter = PdfExporter()

                if exporter.export(export_data, file_path):
                    QMessageBox.information(self, '导出成功', f'文件已保存至：\n{file_path}')
                else:
                    QMessageBox.warning(self, '导出失败', '导出过程中发生错误')
            except Exception as e:
                QMessageBox.warning(self, '导出失败', f'导出失败：{e}')
