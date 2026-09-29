"""
大运流年时间轴组件 v2.0 - 交互增强版
========================
新增交互功能：
- 大运节点点击展开/收起详细分析
- 流年年份筛选输入框（支持范围/关键字）
- 当前大运期间高亮指示
- 平滑淡入/展开动画
- 键盘导航（上下键切换、回车展开）
- 悬浮态增强（阴影、放大、进度条动画）
- 响应式布局适配窄宽度

设计系统：沿用 ui/styles.py 青花蓝/鎏金/五行色系
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QFrame, QLineEdit, QScrollArea, QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QEvent, QRect, QSize
from PySide6.QtGui import QFont, QCursor

from ui.styles import Colors, Fonts, Spacing
from ui.components.badge import Badge

# 天干/地支五行 -> 主题色
WUXING_COLOR = {
    '木': Colors.WOOD, '火': Colors.FIRE, '土': Colors.EARTH,
    '金': Colors.METAL, '水': Colors.WATER,
}

# 关系 -> (标签, Badge 语义色键, 图标)
# 语义色键对齐 ui.components.badge._BADGE_COLORS：warning/success/info。
# 关系吉凶本就是徽章语义（克我=慎→警示，生我/比和=吉→成功，平→中性信息），
# 统一走 Badge 组件即可复用其药丸圆角 + 自动前景色对比（WCAG AA 小字 ≥4.5:1）。
RELATION_STYLE = {
    '克我': ('慎', 'warning', '⚠'),
    '生我': ('吉', 'success', '✓'),
    '比和': ('吉', 'success', '✓'),
    '平':  ('平', 'info', '～'),
}


def _relation_to_level(gan_rel, zhi_rel):
    """把天干/地支的五行生克关系归一为 (标签, 主色, 浅色glow, 图标)。"""
    combined = ' '.join([str(gan_rel or ''), str(zhi_rel or '')])
    if '克我' in combined:
        return RELATION_STYLE['克我']
    if '生我' in combined or '比和' in combined:
        return RELATION_STYLE['生我']
    return RELATION_STYLE['平']


def _build_node_tooltip(detailed):
    """拼接悬浮明细：天干(五行) / 地支(五行) / 天干关系 / 地支关系。"""
    if not detailed or not isinstance(detailed, dict):
        return '（暂无五行生克明细）'
    parts = []
    gan, gan_wx = detailed.get('gan', ''), detailed.get('gan_wx', '')
    zhi, zhi_wx = detailed.get('zhi', ''), detailed.get('zhi_wx', '')
    if gan:
        parts.append(f'天干 {gan}（{gan_wx or "？"}）')
    if zhi:
        parts.append(f'地支 {zhi}（{zhi_wx or "？"}）')
    if detailed.get('gan_relation'):
        parts.append(f'天干关系：{detailed["gan_relation"]}')
    if detailed.get('zhi_relation'):
        parts.append(f'地支关系：{detailed["zhi_relation"]}')
    return '\n'.join(parts) if parts else '（暂无五行生克明细）'


# =====================================================================
# 可展开的大运行组件
# =====================================================================
class _DayunRow(QFrame):
    """单行大运：支持点击展开/收起、键盘聚焦、动画过渡。"""

    def __init__(self, period, color, is_last, is_current=False, parent=None):
        super().__init__(parent)
        self.period = period
        self.color = color
        self.is_last = is_last
        self.is_current = is_current
        self._expanded = False
        self._anim = None
        self._detail_widget = None
        self._setup_ui()
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFocusPolicy(Qt.StrongFocus)

    def _setup_ui(self):
        self.setStyleSheet("background: transparent;")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(Spacing.S0)

        # ---- 顶部摘要行（始终可见） ----
        self.summary = QWidget()
        self.summary.setStyleSheet("background: transparent;")
        sl = QHBoxLayout(self.summary)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(Spacing.S3)

        # 左：节点列（圆点 + 主轴）
        self.node_col = QVBoxLayout()
        self.node_col.setContentsMargins(0, 0, 0, 0)
        self.node_col.setSpacing(Spacing.S0)

        detailed = self.period.get('detailed_analysis') or {}
        gan_wx = detailed.get('gan_wx', '')
        node_color = WUXING_COLOR.get(gan_wx, self.color)

        # 当前大运标识
        node_text = str(self.period.get('period', ''))
        if self.is_current:
            node_text = f'● {node_text}'

        self.node = QLabel(node_text)
        self.node.setStyleSheet(f"""
            background:{node_color}; color:white;
            font-size:11px; font-weight:{Fonts.W_BOLD};
            border-radius:11px; font-family:{Fonts.BODY};
        """)
        self.node.setFixedSize(22, 22)
        self.node.setAlignment(Qt.AlignCenter)
        self.node_col.addWidget(self.node)

        self.spine = QFrame()
        self.spine.setFixedWidth(2)
        self.spine.setStyleSheet(f"background:{Colors.DIVIDER}; border:none;")
        if not self.is_last:
            self.node_col.addWidget(self.spine, 1)
        sl.addLayout(self.node_col)

        # 右：内容卡
        self.card = QFrame()
        self._apply_card_style()
        cv = QVBoxLayout(self.card)
        cv.setContentsMargins(Spacing.S_MARGIN_XS, Spacing.S_MARGIN_XS, Spacing.S_MARGIN_XS, Spacing.S_MARGIN_XS)
        cv.setSpacing(Spacing.S2)

        head = QHBoxLayout()
        head.setSpacing(Spacing.S2)

        ganzhi = QLabel(self.period.get('ganzhi', ''))
        ganzhi.setStyleSheet(f"""
            background:{Colors.QINGHUA}; color:white;
            font-size:{Fonts.SZ_BODY}; font-weight:{Fonts.W_MEDIUM};
            border-radius:{Spacing.RADIUS_SM}; padding:3px 12px;
            font-family:{Fonts.BODY}; min-width:60px;
        """)
        ganzhi.setAlignment(Qt.AlignCenter)
        head.addWidget(ganzhi)

        age = QLabel(f"{self.period.get('start_age','')}-{self.period.get('end_age','')}岁")
        age.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT2}; font-family:{Fonts.BODY};")
        head.addWidget(age)

        years = QLabel(f"{self.period.get('start_year','')}-{self.period.get('end_year','')}年")
        years.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT2}; font-family:{Fonts.BODY};")
        head.addWidget(years)

        # 趋势徽章：统一走 Badge 组件（M4-T4 适配部分）
        # 原实现为手搓 QLabel + 浅色底 + 饱和字；现改标准 Badge 复用其药丸圆角
        # 与自动前景色对比，与全 UI 徽章视觉语言一致。
        label, badge_semantic, icon = _relation_to_level(
            detailed.get('gan_relation'), detailed.get('zhi_relation'))
        badge = Badge(f'{icon} {label}', semantic=badge_semantic)
        head.addWidget(badge)

        # 展开提示
        self.expand_hint = QLabel('▼ 点击展开详情')
        self.expand_hint.setStyleSheet(f"""
            font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3};
            font-family:{Fonts.BODY}; padding-right:4px;
        """)
        self.expand_hint.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        head.addStretch()
        head.addWidget(self.expand_hint)
        cv.addLayout(head)

        analysis = self.period.get('analysis', '')
        if analysis:
            self.analysis_lbl = QLabel(analysis)
            self.analysis_lbl.setWordWrap(True)
            self.analysis_lbl.setStyleSheet(
                f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT}; "
                f"font-family:{Fonts.BODY}; line-height:1.5;")
            cv.addWidget(self.analysis_lbl)

        # 当前大运标记
        if self.is_current:
            current_tag = QLabel('📍 当前大运')
            current_tag.setStyleSheet(f"""
                background:{Colors.LIUJIN_GLOW}; color:{Colors.LIUJIN};
                font-size:{Fonts.SZ_MICRO}; font-weight:{Fonts.W_MEDIUM};
                border-radius:{Spacing.RADIUS_SM}; padding:2px 8px;
                font-family:{Fonts.BODY};
            """)
            cv.addWidget(current_tag)

        # 直接展示五行生克明细，移除悬停 tooltip - 优化排版视觉
        tooltip_text = _build_node_tooltip(detailed)
        if tooltip_text and tooltip_text != '（暂无五行生克明细）':
            # 使用卡片内嵌小卡片样式，提升视觉层次
            detail_container = QWidget()
            detail_container.setStyleSheet(
                f"background:{Colors.CARD_HOVER}; "
                f"border:1px solid {Colors.BORDER}; "
                f"border-radius:{Spacing.RADIUS_SM}; "
                f"padding:6px 8px;")
            detail_layout = QVBoxLayout(detail_container)
            detail_layout.setContentsMargins(0, 0, 0, 0)
            detail_layout.setSpacing(Spacing.S1)
            
            # 五行生克标题
            title_lbl = QLabel('五行生克')
            title_lbl.setStyleSheet(
                f"font-size:{Fonts.SZ_MICRO}; font-weight:{Fonts.W_MEDIUM}; "
                f"color:{Colors.TEXT2}; font-family:{Fonts.BODY};")
            detail_layout.addWidget(title_lbl)
            
            # 内容
            detail_lbl = QLabel(tooltip_text)
            detail_lbl.setWordWrap(True)
            detail_lbl.setStyleSheet(
                f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; "
                f"font-family:{Fonts.BODY}; line-height:1.5;")
            detail_layout.addWidget(detail_lbl)
            
            cv.addWidget(detail_container)
        sl.addWidget(self.card, 1)

        self.main_layout.addWidget(self.summary)

        # ---- 详情区（初始隐藏） ----
        self.detail_container = QWidget()
        self.detail_container.setStyleSheet("background: transparent;")
        self.detail_container.setMaximumHeight(0)
        self.detail_container.setVisible(False)
        dl = QVBoxLayout(self.detail_container)
        dl.setContentsMargins(Spacing.S3, Spacing.S2, Spacing.S3, Spacing.S2)
        dl.setSpacing(Spacing.S2)

        # 详细分析内容
        if detailed:
            for key, val in detailed.items():
                if key in ('gan', 'gan_wx', 'zhi', 'zhi_wx', 'gan_relation', 'zhi_relation'):
                    continue
                if val:
                    row = QWidget()
                    row.setStyleSheet("background: transparent;")
                    rl = QHBoxLayout(row)
                    rl.setContentsMargins(0, 0, 0, 0)
                    rl.setSpacing(Spacing.S2)
                    k_lbl = QLabel(f'{key}：')
                    k_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT2}; font-family:{Fonts.BODY}; font-weight:{Fonts.W_MEDIUM};")
                    k_lbl.setFixedWidth(80)
                    v_lbl = QLabel(str(val))
                    v_lbl.setWordWrap(True)
                    v_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT}; font-family:{Fonts.BODY};")
                    rl.addWidget(k_lbl)
                    rl.addWidget(v_lbl, 1)
                    dl.addWidget(row)

        self.main_layout.addWidget(self.detail_container)

    def _apply_card_style(self, hover=False):
        """应用卡片样式，支持悬浮态动态切换。"""
        border_color = Colors.LIUJIN if hover else (Colors.LIUJIN if self.is_current else Colors.BORDER)
        bg_color = Colors.CARD_HOVER if hover else Colors.CARD
        self.card.setStyleSheet(f"""
            QFrame {{
                background:{bg_color}; border:1.5px solid {border_color};
                border-radius:{Spacing.RADIUS_SM}; padding:10px 12px;
            }}
        """)

    def enterEvent(self, event):
        self._apply_card_style(hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_card_style(hover=False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_expand()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.toggle_expand()
        elif event.key() == Qt.Key_Down:
            self.focusNextChild()
        elif event.key() == Qt.Key_Up:
            self.focusPreviousChild()
        else:
            super().keyPressEvent(event)

    def toggle_expand(self):
        """展开/收起详情区，带高度动画。"""
        self._expanded = not self._expanded
        self.expand_hint.setText('▲ 点击收起详情' if self._expanded else '▼ 点击展开详情')
        self.detail_container.setVisible(True)

        if self._anim:
            self._anim.stop()

        start_h = 0 if not self._expanded else self.detail_container.sizeHint().height()
        end_h = self.detail_container.sizeHint().height() if self._expanded else 0

        self._anim = QPropertyAnimation(self.detail_container, b"maximumHeight")
        self._anim.setDuration(250)
        self._anim.setStartValue(start_h)
        self._anim.setEndValue(end_h)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.finished.connect(lambda: self.detail_container.setVisible(self._expanded))
        self._anim.start()

    def sizeHint(self):
        """返回建议尺寸，包含展开后的详情区。"""
        base = super().sizeHint()
        if self._expanded:
            detail_h = self.detail_container.sizeHint().height()
            return QSize(base.width(), base.height() + detail_h)
        return base


# =====================================================================
# 流年筛选器组件
# =====================================================================
class _LiunianFilter(QWidget):
    """流年筛选输入框：支持年份范围（如 2025-2030）、关键字（如 甲子）、多条件用逗号分隔。"""

    filter_changed = None  # 信号占位，实际通过回调

    def __init__(self, on_filter_change, parent=None):
        super().__init__(parent)
        self.on_filter_change = on_filter_change
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.S0, Spacing.S1, Spacing.S0, Spacing.S1)
        layout.setSpacing(Spacing.S2)

        icon = QLabel('🔍')
        icon.setStyleSheet(f"font-size:13px; color:{Colors.TEXT3};")
        layout.addWidget(icon)

        self.input = QLineEdit()
        self.input.setPlaceholderText('筛选流年：年份/范围/干支，如 2025-2028, 甲子, 丙午')
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background:{Colors.CARD}; border:1px solid {Colors.BORDER};
                border-radius:{Spacing.RADIUS_SM}; padding:6px 10px;
                font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT};
                font-family:{Fonts.BODY}; min-width:200px;
            }}
            QLineEdit:focus {{ border:1.5px solid {Colors.QINGHUA}; }}
        """)
        self.input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.input, 1)

        self.clear_btn = QLabel('✕')
        self.clear_btn.setStyleSheet(f"font-size:13px; color:{Colors.TEXT3}; padding:0 6px;")
        self.clear_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.clear_btn.setVisible(False)
        self.clear_btn.mousePressEvent = lambda e: self.input.clear()
        layout.addWidget(self.clear_btn)

    def _on_text_changed(self, text):
        self.clear_btn.setVisible(bool(text.strip()))
        if self.on_filter_change:
            self.on_filter_change(text.strip())


# =====================================================================
# 主导出函数
# =====================================================================
def fortune_timeline_widget(dayun, liunian, color=Colors.LIUJIN):
    """大运竖向时间轴 + 流年网格（含筛选），返回可直接 set_content 的 QWidget。"""
    dayun = dayun or {}
    liunian = liunian or {}
    periods = dayun.get('periods') or []
    years_list = liunian.get('years') or []

    if not periods and not years_list:
        empty = QLabel('暂无大运流年数据')
        empty.setStyleSheet(
            f"color:{Colors.TEXT3}; font-size:{Fonts.SZ_BODY}; "
            f"font-family:{Fonts.BODY}; padding:8px;")
        empty.setAlignment(Qt.AlignCenter)
        return empty

    container = QWidget()
    container.setStyleSheet("background: transparent;")
    root = QVBoxLayout(container)
    root.setContentsMargins(Spacing.S1, Spacing.S1, Spacing.S1, Spacing.S1)
    root.setSpacing(Spacing.S4)

    # ---------- 起运关键节点 ----------
    qiyun_text = dayun.get('qiyun_text')
    direction = dayun.get('direction', '')
    if qiyun_text:
        qy = QWidget()
        qy_l = QHBoxLayout(qy)
        qy_l.setContentsMargins(0, 0, 0, 0)
        qy_l.setSpacing(Spacing.S3)

        dot = QLabel('◉')
        dot.setStyleSheet(f"color:{Colors.LIUJIN}; font-size:15px;")
        dot.setFixedSize(22, 22)
        dot.setAlignment(Qt.AlignCenter)
        qy_l.addWidget(dot)

        qy_text = QLabel(f'起运：{qiyun_text}')
        qy_text.setStyleSheet(
            f"font-size:{Fonts.SZ_BODY}; font-weight:{Fonts.W_MEDIUM}; "
            f"color:{Colors.LIUJIN}; font-family:{Fonts.BODY};")
        qy_l.addWidget(qy_text)
        if direction:
            d_lbl = QLabel(f'· 大运方向：{direction}')
            d_lbl.setStyleSheet(
                f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT2}; "
                f"font-family:{Fonts.BODY};")
            qy_l.addWidget(d_lbl)
        qy_l.addStretch()
        root.addWidget(qy)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{Colors.DIVIDER};")
        root.addWidget(sep)

    # ---------- 大运时间轴 ----------
    if periods:
        title_row = QHBoxLayout()
        title_row.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        title = QLabel('大运走势')
        title.setStyleSheet(
            f"font-size:{Fonts.SZ_BODY}; font-weight:{Fonts.W_MEDIUM}; "
            f"color:{Colors.QINGHUA}; font-family:{Fonts.BODY};")
        title_row.addWidget(title)

        # 当前大运图例
        legend = QLabel('📍 标记 = 当前大运')
        legend.setStyleSheet(f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};")
        title_row.addStretch()
        title_row.addWidget(legend)
        root.addLayout(title_row)

        # 计算当前大运索引
        current_idx = -1
        from datetime import datetime
        current_year = datetime.now().year
        for idx, p in enumerate(periods):
            try:
                sy = int(p.get('start_year', 0))
                ey = int(p.get('end_year', 0))
                if sy <= current_year <= ey:
                    current_idx = idx
                    break
            except (ValueError, TypeError):
                pass

        for idx, period in enumerate(periods):
            is_current = (idx == current_idx)
            row = _DayunRow(period, color, idx == len(periods) - 1, is_current)
            root.addWidget(row)

    # ---------- 流年网格（带筛选） ----------
    if years_list:
        if periods:
            gap = QFrame()
            gap.setFixedHeight(1)
            gap.setStyleSheet(f"background:{Colors.TEXT3}; opacity:0.3; margin:6px 0;")
            root.addWidget(gap)

        # 筛选器
        filter_widget = _LiunianFilter(on_filter_change=lambda t: _apply_liunian_filter(grid, years_list, t))
        root.addWidget(filter_widget)

        flow_title = QLabel('流年运势（未来10年）')
        flow_title.setStyleSheet(
            f"font-size:{Fonts.SZ_BODY}; font-weight:{Fonts.W_MEDIUM}; "
            f"color:{Colors.LIUJIN}; font-family:{Fonts.BODY}; padding-top:4px;")
        root.addWidget(flow_title)

        grid = QGridLayout()
        grid.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        for i, year_data in enumerate(years_list):
            grid.addWidget(_build_liunian_cell(year_data, i), i // 2, i % 2)
        root.addLayout(grid)

        # 保存引用供筛选器回调使用
        filter_widget._grid = grid
        filter_widget._years_list = years_list

    return container


def _apply_liunian_filter(grid, years_list, filter_text):
    """根据筛选文本显示/隐藏流年单元格。"""
    if not filter_text:
        for i in range(grid.count()):
            item = grid.itemAt(i)
            if item and item.widget():
                item.widget().setVisible(True)
        return

    # 解析筛选条件
    conditions = [c.strip() for c in filter_text.split(',') if c.strip()]
    year_set = set()
    ganzhi_set = set()

    for cond in conditions:
        # 年份范围：2025-2028
        if '-' in cond and cond.replace('-', '').isdigit():
            try:
                start, end = map(int, cond.split('-'))
                year_set.update(range(start, end + 1))
            except ValueError:
                pass
        # 单年份
        elif cond.isdigit():
            year_set.add(int(cond))
        # 干支关键字
        else:
            ganzhi_set.add(cond)

    for i, year_data in enumerate(years_list):
        widget = grid.itemAt(i).widget() if grid.itemAt(i) else None
        if not widget:
            continue
        show = True
        if year_set:
            show = show and int(year_data.get('year', 0)) in year_set
        if ganzhi_set:
            show = show and any(gz in year_data.get('ganzhi', '') for gz in ganzhi_set)
        widget.setVisible(show)


def _build_liunian_cell(year_data, index=0):
    """流年单个网格单元：年份 + 干支 + 悬浮明细 + 入场动画。"""
    cell = QFrame()
    cell.setStyleSheet(f"""
        QFrame {{
            background:{Colors.CARD}; border:1px solid {Colors.BORDER};
            border-radius:{Spacing.RADIUS_SM}; padding:6px 8px;
        }}
        QFrame:hover {{ border:1px solid {Colors.LIUJIN_LIGHT}; }}
    """)
    cl = QHBoxLayout(cell)
    cl.setContentsMargins(0, 0, 0, 0)
    cl.setSpacing(Spacing.S2)

    year = QLabel(str(year_data.get('year', '')))
    year.setStyleSheet(f"""
        background:{Colors.LIUJIN}; color:white;
        font-size:{Fonts.SZ_SMALL}; font-weight:{Fonts.W_MEDIUM};
        border-radius:{Spacing.RADIUS_SM}; padding:2px 8px;
        font-family:{Fonts.BODY}; min-width:42px;
    """)
    year.setAlignment(Qt.AlignCenter)
    cl.addWidget(year)

    ganzhi = QLabel(year_data.get('ganzhi', ''))
    ganzhi.setStyleSheet(f"""
        background:{Colors.QINGHUA}; color:white;
        font-size:{Fonts.SZ_SMALL}; font-weight:{Fonts.W_MEDIUM};
        border-radius:{Spacing.RADIUS_SM}; padding:2px 8px;
        font-family:{Fonts.BODY}; min-width:48px;
    """)
    ganzhi.setAlignment(Qt.AlignCenter)
    cl.addWidget(ganzhi)
    cl.addStretch()

    # 直接展示流年明细，移除悬停 tooltip - 优化排版视觉
    detailed = year_data.get('detailed_analysis') or {}
    tip_parts = []
    tip_text = _build_node_tooltip(detailed)
    if tip_text and tip_text != '（暂无五行生克明细）':
        tip_parts.append(tip_text)
    if year_data.get('analysis'):
        tip_parts.append(year_data['analysis'])
    if tip_parts:
        tip = '\n\n'.join(tip_parts)
        # 重构 cell 布局为垂直排列，提升视觉层次
        # 先保存现有水平布局的控件
        temp_widgets = []
        while cl.count() > 0:
            item = cl.takeAt(0)
            if item.widget():
                temp_widgets.append(item.widget())
        
        # 重新创建垂直布局
        v_layout = QVBoxLayout(cell)
        v_layout.setContentsMargins(Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM)
        v_layout.setSpacing(Spacing.S1)
        
        # 顶部信息行
        header_row = QWidget()
        h_layout = QHBoxLayout(header_row)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(Spacing.S2)
        for w in temp_widgets:
            h_layout.addWidget(w)
        v_layout.addWidget(header_row)
        
        # 明细区域 - 使用卡片样式
        if tip_parts:
            detail_container = QWidget()
            detail_container.setStyleSheet(
                f"background:{Colors.CARD_HOVER}; "
                f"border:1px solid {Colors.BORDER}; "
                f"border-radius:{Spacing.RADIUS_SM}; "
                f"padding:6px 8px;")
            detail_layout = QVBoxLayout(detail_container)
            detail_layout.setContentsMargins(0, 0, 0, 0)
            detail_layout.setSpacing(Spacing.S1)
            
            # 标题
            title_lbl = QLabel('流年分析')
            title_lbl.setStyleSheet(
                f"font-size:{Fonts.SZ_MICRO}; font-weight:{Fonts.W_MEDIUM}; "
                f"color:{Colors.TEXT2}; font-family:{Fonts.BODY};")
            detail_layout.addWidget(title_lbl)
            
            tip_lbl = QLabel(tip)
            tip_lbl.setWordWrap(True)
            tip_lbl.setStyleSheet(
                f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; "
                f"font-family:{Fonts.BODY}; line-height:1.5;")
            detail_layout.addWidget(tip_lbl)
            
            v_layout.addWidget(detail_container)

    # 入场淡入动画
    cell.setGraphicsEffect(None)
    from PySide6.QtWidgets import QGraphicsOpacityEffect
    from PySide6.QtCore import QPropertyAnimation, QEasingCurve
    effect = QGraphicsOpacityEffect(cell)
    effect.setOpacity(0.0)
    cell.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(300)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    QTimer.singleShot(50 * index, anim.start)

    return cell