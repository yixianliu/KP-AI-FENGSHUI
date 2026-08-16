"""
大六壬起课结果展示面板
展示：基本信息 / 天地盘 / 四课 / 三传（门法）/ 十二天将 / 神煞 / 智能 解读。
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QScrollArea, QPushButton, QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from ui.components.collapsible_card import (CollapsibleCard, ai_section_header,
                                          highlight_label, probability_stats_widget)
# 地支五行对照表复用排盘引擎的定义，展示层不再自建一份
from core.liuren import ZHI_WX
from core.ganzhi_constants import DI_ZHI

#: 五行 → 颜色（本地 hex，避免引用未定义样式属性）
WX_COLOR = {
    '木': '#3a7d44', '火': '#c0392b', '土': '#b9770e',
    '金': '#7f8c8d', '水': '#2471a3',
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
        main_layout.setSpacing(16)

        # 头部
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
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

        self.smart_analyze_btn = QPushButton('🤖 重新解读')
        self.smart_analyze_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        self.smart_analyze_btn.setCursor(Qt.PointingHandCursor)
        self.smart_analyze_btn.setVisible(False)
        header_layout.addWidget(self.smart_analyze_btn)

        self.export_btn = QPushButton('📤 导出')
        self.export_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setVisible(False)
        self.export_btn.clicked.connect(self._on_export_click)
        header_layout.addWidget(self.export_btn)
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
        status_layout.setContentsMargins(16, 10, 16, 10)
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
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(18)

        self.empty_state = self._create_empty_state()
        self.content_layout.addWidget(self.empty_state)

        self.content_area.setWidget(self.content_widget)
        main_layout.addWidget(self.content_area)
        self.setLayout(main_layout)

    # ---------- 空状态 ----------
    def _create_empty_state(self):
        """创建未起课时的占位界面（太极图标 + 引导文案）。"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        icon = QLabel('☵')
        icon.setStyleSheet(f"font-size: 64px; color: {Colors.BORDER}; opacity: 0.5;")
        icon.setAlignment(Qt.AlignCenter)
        title = QLabel('请完善左侧起课参数')
        title.setStyleSheet(f"""
            font-size: 18px; color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel('点击「起课」获取大六壬天地盘与三传分析')
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN}; opacity: 0.7;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return widget

    # ---------- 通用卡片（统一复用 CollapsibleCard） ----------
    def _create_result_card(self, title, icon, content_widget, highlight=False):
        """创建结果卡片（统一复用 CollapsibleCard：左侧强调色条 + 图标 + 标题，可折叠）。

        配色：排盘类卡片用青色条(Colors.QINGHUA)，AI/强调类用鎏金色条(Colors.LIUJIN)，
        与八字、梅花易数面板保持一致。
        """
        accent = Colors.LIUJIN if highlight else Colors.QINGHUA
        card = CollapsibleCard(title, icon, accent_color=accent, collapsed=False)
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
            color: #ffffff; background-color: {color};
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
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        rows = [
            ('起课方式', r.get('method_name', '')),
            ('占问', r.get('question') or '—'),
            ('时间', r.get('time', '')),
            ('日干支', f"{r.get('ri_gan','')}{r.get('ri_zhi','')}（{r.get('ri_gan_wx','')}）"),
            ('月将', f"{r.get('yue_jiang_name','')}（{r.get('yue_jiang','')}）"),
            ('占时', r.get('zhan_shi', '')),
        ]
        for i, (k, v) in enumerate(rows):
            kl = QLabel(k)
            kl.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; font-family: {Fonts.FAMILY_CN};")
            kl.setFixedWidth(76)
            kl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            vl = QLabel(str(v))
            vl.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY}; font-family: {Fonts.FAMILY_CN};")
            vl.setWordWrap(True)
            grid.addWidget(kl, i, 0)
            grid.addWidget(vl, i, 1)
        w = QWidget(); w.setLayout(grid)
        return w

    # ---------- 天地盘 ----------
    def _tiandi_card(self, r):
        """构建「天地盘」卡片：展示十二地支宫位下的天盘支与临宫天将（罗盘式布局）。

        天盘为日辰加临后各宫所临地支，天将为人盘十二神将，是六壬推演的盘面基础。

        Args:
            r: 起课结果字典。

        Returns:
            渲染好的 QWidget。
        """
        tian_pan = r.get('tian_pan', {})
        # 预建「宫位→天将」映射，便于按地支列快速取对应天将
        tian_jiang = {t['pos']: t['jiang'] for t in r.get('tian_jiang', [])}
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        # 表头：地盘12宫
        for c, dz in enumerate(ZHI_ORDER):
            h = QLabel(dz)
            h.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; font-family: {Fonts.FAMILY_CN}; font-weight: {Fonts.WEIGHT_BOLD};")
            h.setAlignment(Qt.AlignCenter)
            grid.addWidget(h, 0, c)
        # 天盘支
        for c, dz in enumerate(ZHI_ORDER):
            tp = tian_pan.get(dz, dz)
            cell = QLabel(tp)
            cell.setStyleSheet(f"font-size: 16px; color: {Colors.ACCENT}; font-family: {Fonts.FAMILY_SERIF}; font-weight: {Fonts.WEIGHT_BOLD};")
            cell.setAlignment(Qt.AlignCenter)
            cell.setFixedHeight(28)
            grid.addWidget(cell, 1, c)
        # 天将
        for c, dz in enumerate(ZHI_ORDER):
            jiang = tian_jiang.get(dz, '')
            cell = QLabel(jiang)
            cell.setStyleSheet(f"font-size: {Fonts.SIZE_MICRO}; color: {Colors.TEXT_SECONDARY}; font-family: {Fonts.FAMILY_CN};")
            cell.setAlignment(Qt.AlignCenter)
            cell.setFixedHeight(20)
            grid.addWidget(cell, 2, c)
        w = QWidget(); w.setLayout(grid)
        return w

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
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)
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
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)
        items = [('初传', sc.get('chu', '')), ('中传', sc.get('zhong', '')), ('末传', sc.get('mo', ''))]
        for c, (label, val) in enumerate(items):
            col = QVBoxLayout()
            col.setSpacing(4)
            lab = QLabel(label)
            lab.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; font-family: {Fonts.FAMILY_CN};")
            lab.setAlignment(Qt.AlignCenter)
            val_lab = QLabel(val)
            val_lab.setStyleSheet(f"""
                font-size: 22px; color: {Colors.ACCENT}; font-family: {Fonts.FAMILY_SERIF};
                font-weight: {Fonts.WEIGHT_BOLD};
            """)
            val_lab.setAlignment(Qt.AlignCenter)
            col.addWidget(lab)
            col.addWidget(val_lab)
            grid.addLayout(col, 0, c)
        # 门法说明
        gate_lab = QLabel(f"取用法：{gate}")
        gate_lab.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_SECONDARY}; font-family: {Fonts.FAMILY_CN};")
        gate_lab.setAlignment(Qt.AlignCenter)
        grid.addWidget(gate_lab, 1, 0, 1, 3)
        w = QWidget(); w.setLayout(grid)
        return w

    # ---------- 十二天将 ----------
    def _tianjiang_card(self, r):
        """构建「十二天将」卡片：以宫位—天盘—天将三元组逐行展示人盘十二神将布局。

        Args:
            r: 起课结果字典。

        Returns:
            渲染好的 QWidget。
        """
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        for i, t in enumerate(r.get('tian_jiang', [])):
            row = i // 3
            col = i % 3
            cell = QLabel(f"{t['pos']}　{t['tianpan']}　{t['jiang']}")
            cell.setStyleSheet(f"""
                font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_PRIMARY};
                font-family: {Fonts.FAMILY_CN}; background: {Colors.QINGHUA_LIGHT};
                border-radius: 4px; padding: 6px 8px;
            """)
            cell.setAlignment(Qt.AlignCenter)
            layout.addWidget(cell, row, col)
        w = QWidget(); w.setLayout(layout)
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        if not sha:
            layout.addWidget(self._muted('本课无明显神煞'))
        else:
            for k, v in sha.items():
                row = QHBoxLayout()
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
    def _placeholder(self):
        """创建「KP模型智能解读」卡片的占位内容，提示解读将在起课后生成。"""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._muted('龙虎山大师兄分析预测将在起课后自动生成，或点击右上角「重新解读」。'))
        return w

    # ---------- 对外入口 ----------
    def show_loading(self, text='龙虎山大师兄正在解读六壬玄机…'):
        """显示加载状态：太极动画 + 状态栏文案。

        Args:
            text: 状态栏提示文案，默认「龙虎山大师兄正在解读六壬玄机…」；
                  传入「起课中」类文案时会自动覆盖为起课加载状态。
        """
        self.status_label.setText('⏳ ' + text)
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        self._safe_set_visible(self.empty_state, False)
        self.smart_analyze_btn.setVisible(False)
        self.export_btn.setVisible(False)
        """更新状态栏为「龙虎山大师兄解读中」，供业务层在发起 大师兄 解读时调用。

        Args:
            text: 状态提示文案，默认为六壬解读提示。
        """
        self.status_label.setText('⏳ ' + text)
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)

    def display_result(self, result_data):
        """对外入口：接收起课结果并渲染全部卡片（基本信息/天地盘/四课/三传/天将/神煞/智能 占位）。

        Args:
            result_data: 排盘引擎返回的起课结果字典。
        """
        try:
            # 清理旧内容（含加载动画）
            if hasattr(self, 'taiji_animation'):
                self.taiji_animation.stop()
            # 清理动态内容；empty_state 是持久控件，绝不可 deleteLater，否则后续 setVisible 会命中已销毁的 C++ 对象
            while self.content_layout.count():
                item = self.content_layout.takeAt(0)
                w = item.widget()
                if w and w is not self.empty_state:
                    w.deleteLater()
            self._current_result = result_data
            self._safe_set_visible(self.empty_state, False)
            if hasattr(self, 'export_btn'):
                self.export_btn.setVisible(True)

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
                self._create_result_card('龙虎山大师兄分析预测', '🧙', self._placeholder(), highlight=True))

            self.smart_analyze_btn.setVisible(True)
            self.smart_analyze_btn.setEnabled(True)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def display_ai_analysis_result(self, smart_analysis):
        """显示智能分析结果（别名方法，兼容调用方使用 display_ai_analysis_result 的情况）"""
        self.display_analysis_result(smart_analysis)

    def display_analysis_result(self, smart_analysis):
        """将 智能 结构化解读渲染到「智能 智能解读」卡片。"""
        try:
            if not smart_analysis:
                self.status_label.setText('⚠ 龙虎山大师兄解读为空')
                return
            # 用 智能 内容替换最后一个 智能 卡片
            if hasattr(self, 'taiji_animation'):
                self.taiji_animation.stop()
            # 移除 智能 占位卡片（最后一个），重建为解读内容
            if self.content_layout.count():
                last = self.content_layout.itemAt(self.content_layout.count() - 1)
                w = last.widget()
                if w:
                    w.deleteLater()
                    self.content_layout.removeWidget(w)

            # 构建 智能 结果容器：金色分隔标题 + 各子项折叠卡片（与八字/梅花面板一致）
            cards = self._body(smart_analysis)
            container = QWidget()
            cv = QVBoxLayout(container)
            cv.setContentsMargins(0, 0, 0, 0)
            cv.setSpacing(12)
            # 设置最大宽度约束，防止内容超出滚动区域
            cv_container_max = QWidget()
            cv_container_max_layout = QVBoxLayout(cv_container_max)
            cv_container_max_layout.setContentsMargins(0, 0, 0, 0)
            cv_container_max_layout.setSpacing(0)
            cv_container_max.setMaximumWidth(800)
            cv_container_max_layout.addWidget(ai_section_header('龙虎山大师兄分析预测'))

            key_points = smart_analysis.get('key_points')
            if isinstance(key_points, (list, tuple)):
                kp_text = '\n'.join(str(x) for x in key_points if x and str(x).strip())
            elif isinstance(key_points, str):
                kp_text = key_points
            else:
                kp_text = ''
            if kp_text and kp_text.strip():
                cv_container_max_layout.addWidget(highlight_label('【重点提示】\n' + kp_text.strip(), Colors.LIUJIN))

            for c in cards:
                cv_container_max_layout.addWidget(c)

            cv.addWidget(cv_container_max)
            self.content_layout.addWidget(container)
            self.status_label.setText('✓ 龙虎山大师兄解读完成')
            self.status_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY}; color: {Colors.SUCCESS};
                font-family: {Fonts.FAMILY_CN}; font-weight: {Fonts.WEIGHT_BOLD};
            """)
            self.smart_analyze_btn.setVisible(True)
            self.smart_analyze_btn.setEnabled(True)
        except Exception as e:
            import traceback
            traceback.print_exc()

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
            ('总体判断', '🎯', Colors.QINGHUA, ai.get('final_verdict')),
            ('课体分析', '☯', Colors.LIUJIN, ai.get('analysis')),
            ('综合建议', '✨', Colors.ZHUSHA, ai.get('scenario_advice')),
            ('应期时机', '⏳', Colors.SUCCESS, ai.get('timing')),
            ('历史案例', '📚', Colors.QINGHUA, ai.get('historical_cases')),
            ('概率统计', '📊', Colors.LIUJIN, ai.get('probability_stats')),
            ('免责声明', '⚠', Colors.TEXT_TERTIARY, ai.get('disclaimer')),
        ]
        for title, icon, color, text in sections:
            if text is None:
                continue
            # 概率统计需要可视化展示（标签+进度条+说明），不走纯文本
            if title == '概率统计':
                items = text if isinstance(text, (list, tuple)) else [str(text)]
                items = [str(x) for x in items if x and str(x).strip()]
                if not items:
                    continue
                card = CollapsibleCard(title, icon, accent_color=color, collapsed=False)
                card.set_content(probability_stats_widget(items, color))
                cards.append(card)
                continue
            # AI 返回字段可能为字符串列表（如课体分析 / 三传精解），统一 join 成可读文本
            if isinstance(text, (list, tuple)):
                text = '\n'.join(str(t) for t in text if t)
            if not str(text).strip():
                continue
            body = QLabel(str(text))
            body.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_SECONDARY};
                font-family: {Fonts.FAMILY_CN}; line-height: 1.7;
            """)
            body.setWordWrap(True)
            card = CollapsibleCard(title, icon, accent_color=color, collapsed=False)
            card.set_content(body)
            cards.append(card)
        return cards

    def clear(self):
        """清空面板：移除动态内容、恢复空状态占位与初始提示文案，并隐藏操作按钮。"""
        if hasattr(self, 'taiji_animation'):
            self.taiji_animation.stop()
        # 清理动态内容；empty_state 持久控件不可删除
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w and w is not self.empty_state:
                w.deleteLater()
        # 仅当 empty_state 不在布局中时才挂载（避免重复 addWidget）
        if self.content_layout.indexOf(self.empty_state) == -1:
            self.content_layout.addWidget(self.empty_state)
        self._safe_set_visible(self.empty_state, True)
        self.smart_analyze_btn.setVisible(False)
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
            'tian_jiang': [f"{t['pos']}{t['tianpan']}{t['jiang']}" for t in r.get('tian_jiang', [])],
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
        智能 = getattr(self, '_current_ai', None)
        if 智能 and isinstance(智能, dict):
            export_data['liuren_ai'] = ai

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
