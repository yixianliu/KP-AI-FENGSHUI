"""
梅花易数起卦结果展示面板
"""
import re

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QScrollArea, QPushButton, QGridLayout, QSizePolicy,
                             QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, Property
from PySide6.QtGui import QPainter
from ui.styles import Stylesheets, Colors, Fonts, Spacing
# 别名导入：本模块多处存在局部变量 `icon = QLabel(...)`，用原名调用有遮蔽地雷风险
from ui.components.icons import icon as load_icon
from ui.components.collapsible_card import (CollapsibleCard, ai_section_header,
                                          highlight_label, probability_stats_widget,
                                          loading_panel, ResponsiveFlow,
                                          set_all_cards_collapsed)
from ui.components.states import EmptyState, ErrorState


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
        """重写绘制：仅在存在旋转角度时以中心为原点旋转坐标系后绘制，否则直接绘制。

        Args:
            event: 绘制事件。
        """
        if self._angle:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.translate(self.width() / 2.0, self.height() / 2.0)
            painter.rotate(self._angle)
            painter.translate(-self.width() / 2.0, -self.height() / 2.0)
            super().paintEvent(event)
        else:
            super().paintEvent(event)


class MeihuaResultPanel(QWidget):
    """梅花易数结果展示面板"""

    def __init__(self, parent=None):
        """初始化梅花易数结果面板，缓存最近一次 智能 解读供导出复用，并构建 UI。

        Args:
            parent: 父控件。
        """
        super().__init__(parent)
        self._current_智能 = {}   # 最近一次 智能 解读结果，供导出复用
        self._error_holder = None  # M3-6：错误态 holder 引用，供清理
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

        header_layout = QHBoxLayout()
        header_layout.setSpacing(Spacing.S3)

        title_icon = QLabel('🔮')
        title_icon.setStyleSheet("font-size: 22px;")

        self.title_label = QLabel('梅花易数起卦结果')
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
        # 不显式设 spacing 会取 Qt 默认值 6（非 8-4 体系）；此布局仅一个子项，
        # 设 S2 使实测值落入体系，不影响单居中子项的视觉表现
        status_layout.setSpacing(Spacing.S2)
        status_layout.setContentsMargins(16, 10, 16, 10)
        status_layout.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel('ℹ 请完善左侧参数，点击「起卦」获取卦象分析')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        status_layout.addWidget(self.status_label)

        main_layout.addWidget(self.status_bar)

        self.content_area = QScrollArea()
        self.content_area.setStyleSheet(Stylesheets.SCROLL_AREA)
        self.content_area.setWidgetResizable(True)
        self.content_area.setFrameShape(QFrame.NoFrame)

        self.content_widget = QWidget()
        # 横向自适应填满滚动区视口，使内部卡片随右侧宽度撑满、不拥挤
        self.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.content_widget.setStyleSheet(f"background-color: {Colors.BG};")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(Spacing.S4)

        self.empty_state = self._create_empty_state()
        self.content_layout.addWidget(self.empty_state)

        self.content_area.setWidget(self.content_widget)
        main_layout.addWidget(self.content_area)

        self.setLayout(main_layout)

    def _create_empty_state(self):
        """创建空状态，委托 EmptyState（M3-6：统一视觉语言 + 引导动效）。

        保留对外方法签名，避免破坏既有测试契约（返回 QWidget 实例）。
        """
        from ui.components.states import EmptyState
        empty = EmptyState(
            title='请完善左侧起卦参数',
            hint='点击「起卦」获取梅花易数卦象分析',
            icon='🔮',
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

    def _create_result_card(self, title, icon, content_widget, highlight=False):
        """创建结果卡片（统一复用 CollapsibleCard：左侧强调色条 + 图标 + 标题，可折叠）。

        配色：排盘类卡片用青色条(Colors.QINGHUA)，AI/强调类用鎏金色条(Colors.LIUJIN)，
        与八字、大六壬面板保持一致。
        """
        accent = Colors.LIUJIN if highlight else Colors.QINGHUA
        card = CollapsibleCard(title, icon, accent_color=accent, collapsed=False)
        card.set_content(content_widget)
        return card

    def _create_hexagram_display(self, hexagram_info, hex_type='本卦'):
        """创建卦象展示组件（优化版：头部卦名 + 上/下卦卡 + 卦辞原文块 + 释义，与爻辞详解一致）。"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.S3)

        name = hexagram_info.get('name', '')
        symbol = hexagram_info.get('symbol', '')
        judgment = hexagram_info.get('judgment', '')
        explanation = hexagram_info.get('explanation', '')
        upper_gua = hexagram_info.get('upper_gua', '')
        lower_gua = hexagram_info.get('lower_gua', '')

        # ---- 头部：类型徽标 + 卦名（衬线大字） ----
        header_row = QHBoxLayout()
        header_row.setSpacing(Spacing.S3)
        header_row.setAlignment(Qt.AlignCenter)

        type_label = QLabel(hex_type)
        type_label.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            color: {Colors.TEXT2};
            font-weight: {Fonts.W_BOLD};
            font-family: {Fonts.BODY};
            padding: 3px 10px;
            background-color: {Colors.HIGHLIGHT_GLOW};
            border-radius: {Spacing.RADIUS_SM};
        """)

        name_label = QLabel(f'{name}　{symbol}')
        name_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_KEY};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.ACCENT};
            font-family: {Fonts.FAMILY_SERIF};
            letter-spacing: 3px;
        """)

        header_row.addWidget(type_label)
        header_row.addWidget(name_label)
        header_row.addStretch()
        layout.addLayout(header_row)

        # ---- 上/下卦信息卡（描边圆角，与爻辞子卡一致） ----
        gua_info = QLabel(f'上卦　{upper_gua}　　下卦　{lower_gua}')
        gua_info.setStyleSheet(f"""
            font-size: {Fonts.SZ_BODY};
            color: {Colors.TEXT2};
            font-family: {Fonts.BODY};
            background-color: {Colors.BACKGROUND};
            border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS_SM};
            padding: 8px 12px;
        """)
        gua_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(gua_info)

        # ---- 卦辞原文块（羊皮纸 + 左边条，与爻辞原文一致） ----
        if judgment:
            orig_block = QFrame()
            orig_block.setStyleSheet(f"""
                QFrame {{
                    background: {Colors.BG_DARK};
                    border: none;
                    border-left: 3px solid {Colors.PRIMARY};
                    border-radius: {Spacing.RADIUS_SM};
                }}
            """)
            ob_lay = QVBoxLayout(orig_block)
            ob_lay.setContentsMargins(12, 8, 12, 8)
            ob_lay.setSpacing(Spacing.S1)

            orig_tag = QLabel('卦辞')
            orig_tag.setStyleSheet(
                f"font-size: {Fonts.SZ_MICRO}; font-weight: {Fonts.W_MEDIUM}; "
                f"color: {Colors.PRIMARY}; font-family: {Fonts.BODY};")
            orig_text = QLabel(f'【卦辞】{judgment}')
            orig_text.setWordWrap(True)
            orig_text.setStyleSheet(
                f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; "
                f"font-family: {Fonts.FAMILY_SERIF}; line-height: 1.7;")
            ob_lay.addWidget(orig_tag)
            ob_lay.addWidget(orig_text)
            layout.addWidget(orig_block)

        # ---- 释义块（弱化层级） ----
        if explanation:
            exp_block = QWidget()
            eb_lay = QVBoxLayout(exp_block)
            eb_lay.setContentsMargins(12, 4, 12, 4)
            eb_lay.setSpacing(Spacing.S1)
            exp_tag = QLabel('释义')
            exp_tag.setStyleSheet(
                f"font-size: {Fonts.SZ_MICRO}; font-weight: {Fonts.W_MEDIUM}; "
                f"color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
            exp_text = QLabel(explanation)
            exp_text.setWordWrap(True)
            exp_text.setStyleSheet(
                f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2}; "
                f"font-family: {Fonts.BODY}; line-height: 1.6;")
            eb_lay.addWidget(exp_tag)
            eb_lay.addWidget(exp_text)
            layout.addWidget(exp_block)

        return widget

    def _create_yao_display(self, yao_info_list):
        """创建爻辞展示（优化版：清晰爻头 + 动爻徽标 + 原文/释义分层）。

        视觉层次设计：
          - 每一爻 = 一张独立卡片，左侧强调色条（动爻=朱砂红、静爻=青花蓝）；
          - 顶部爻头：爻名（衬线粗体）+ 右侧「⚡ 动爻」徽标（仅在动爻时）；
          - 爻辞原文：置于羊皮纸底色块（动爻用朱砂红微光 + 朱砂红左边条），
            衬线大字凸显，作为核心内容；
          - 释义：用细分隔线与原文隔开，灰色小字弱化层级，便于快速扫读。
        全部沿用设计系统配色与 RADIUS_SM 圆角，提升国风质感与可读性。
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.S3)

        for yao in yao_info_list:
            name = yao.get('name', '')
            text = yao.get('text', '')
            explanation = yao.get('explanation', '')
            is_moving = yao.get('is_moving', False)
            accent = Colors.ACCENT if is_moving else Colors.PRIMARY

            yao_card = QFrame()
            yao_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND};
                    border: 1px solid {Colors.BORDER};
                    border-radius: {Spacing.RADIUS_SM};
                }}
            """)

            card_lay = QVBoxLayout(yao_card)
            card_lay.setContentsMargins(0, 0, 0, 0)
            card_lay.setSpacing(Spacing.S0)

            # ---- 爻头：强调色条 + 爻名 + （动爻徽标） ----
            header = QWidget()
            header_lay = QHBoxLayout(header)
            header_lay.setContentsMargins(12, 10, 12, 10)
            header_lay.setSpacing(Spacing.S2)

            bar = QFrame()
            bar.setFixedSize(4, 18)
            bar.setStyleSheet(f"background: {accent}; border: none; border-radius: 2px;")

            name_label = QLabel(name)
            name_label.setStyleSheet(f"""
                font-size: {Fonts.SZ_SECTION};
                font-weight: {Fonts.W_BOLD};
                color: {accent};
                font-family: {Fonts.FAMILY_SERIF};
            """)

            header_lay.addWidget(bar)
            header_lay.addWidget(name_label)
            header_lay.addStretch()

            if is_moving:
                badge = QLabel('⚡ 动爻')
                badge.setStyleSheet(f"""
                    font-size: {Fonts.SZ_MICRO};
                    font-weight: {Fonts.W_BOLD};
                    color: {Colors.TEXT_INV};
                    background: {Colors.ZHUSHA};
                    border: none;
                    border-radius: {Spacing.RADIUS_SM};
                    padding: 2px 8px;
                """)
                header_lay.addWidget(badge)

            card_lay.addWidget(header)

            # 头部分隔线
            head_div = QFrame()
            head_div.setFixedHeight(1)
            head_div.setStyleSheet(f"background: {Colors.DIVIDER}; border: none;")
            card_lay.addWidget(head_div)

            # ---- 爻辞原文块 ----
            if text:
                orig_block = QFrame()
                orig_block.setStyleSheet(f"""
                    QFrame {{
                        background: {Colors.ZHUSHA_GLOW if is_moving else Colors.BG_DARK};
                        border: none;
                        border-left: 3px solid {accent};
                        border-radius: {Spacing.RADIUS_SM};
                    }}
                """)
                ob_lay = QVBoxLayout(orig_block)
                ob_lay.setContentsMargins(12, 8, 12, 8)
                ob_lay.setSpacing(Spacing.S1)

                orig_tag = QLabel('爻辞原文')
                orig_tag.setStyleSheet(
                    f"font-size: {Fonts.SZ_MICRO}; font-weight: {Fonts.W_MEDIUM}; "
                    f"color: {accent}; font-family: {Fonts.BODY};")

                orig_text = QLabel(text)
                orig_text.setWordWrap(True)
                orig_text.setStyleSheet(
                    f"font-size: {Fonts.SZ_SECTION}; color: {Colors.TEXT}; "
                    f"font-family: {Fonts.FAMILY_SERIF}; line-height: 1.8;")

                ob_lay.addWidget(orig_tag)
                ob_lay.addWidget(orig_text)
                card_lay.addWidget(orig_block)

            # ---- 释义块 ----
            if explanation:
                exp_block = QWidget()
                eb_lay = QVBoxLayout(exp_block)
                eb_lay.setContentsMargins(12, 8, 12, 10)
                eb_lay.setSpacing(Spacing.S1)

                exp_tag = QLabel('释义')
                exp_tag.setStyleSheet(
                    f"font-size: {Fonts.SZ_MICRO}; font-weight: {Fonts.W_MEDIUM}; "
                    f"color: {Colors.TEXT3}; font-family: {Fonts.BODY};")

                exp_text = QLabel(explanation)
                exp_text.setWordWrap(True)
                exp_text.setStyleSheet(
                    f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2}; "
                    f"font-family: {Fonts.BODY}; line-height: 1.6;")

                eb_lay.addWidget(exp_tag)
                eb_lay.addWidget(exp_text)
                card_lay.addWidget(exp_block)

            layout.addWidget(yao_card)

        return widget

    def _create_judgment_summary(self, overall_info):
        """创建吉凶总览"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.S3)

        overall = overall_info.get('overall', '')
        level = overall_info.get('level', '中')

        color_map = {
            '吉': Colors.SUCCESS,
            '凶': Colors.DANGER,
            '中': Colors.WARNING,
            '大吉': Colors.SUCCESS,
            '小吉': Colors.SUCCESS,
            '小凶': Colors.DANGER,
        }
        badge_color = color_map.get(level, Colors.WARNING)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        badge_row.setAlignment(Qt.AlignCenter)

        badge = QLabel(level)
        badge.setFixedSize(80, 80)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"""
            background-color: {badge_color};
            color: white;
            font-size: 28px;
            font-weight: {Fonts.WEIGHT_BOLD};
            border-radius: 40px;
            font-family: {Fonts.FAMILY_SERIF};
        """)
        badge_row.addWidget(badge)
        layout.addLayout(badge_row)

        if overall:
            overall_label = QLabel(overall)
            overall_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_SECTION};
                color: {Colors.TEXT_SECONDARY};
                font-family: {Fonts.FAMILY_CN};
                line-height: 1.7;
                text-align: center;
            """)
            overall_label.setWordWrap(True)
            overall_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(overall_label)

        return widget

    def _create_suggestions(self, suggestions):
        """创建建议列表"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.S2)

        for i, suggestion in enumerate(suggestions, 1):
            sug_widget = QFrame()
            sug_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND};
                    border-radius: {Spacing.CONTROL_RADIUS};
                    padding: 10px;
                }}
            """)

            sug_layout = QHBoxLayout(sug_widget)
            sug_layout.setContentsMargins(12, 8, 12, 8)
            sug_layout.setSpacing(Spacing.S3)

            num_badge = QLabel(str(i))
            num_badge.setFixedSize(24, 24)
            num_badge.setAlignment(Qt.AlignCenter)
            num_badge.setStyleSheet(f"""
                background-color: {Colors.HIGHLIGHT};
                color: white;
                font-size: 12px;
                font-weight: {Fonts.WEIGHT_BOLD};
                border-radius: 12px;
                font-family: {Fonts.FAMILY_CN};
            """)

            text = QLabel(suggestion)
            text.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_PRIMARY};
                font-family: {Fonts.FAMILY_CN};
                line-height: 1.6;
            """)
            text.setWordWrap(True)

            sug_layout.addWidget(num_badge)
            sug_layout.addWidget(text, 1)
            layout.addWidget(sug_widget)

        return widget

    def _create_ti_yong_relationship(self, ben_gua):
        """体用生克关系图（按动爻定体用：不动为体、动者为用）。

        梅花古法：体卦为主、为自己；用卦为事、为对方。动爻在上卦（4-6爻）
        则上卦为用、下卦为体；动爻在下卦（1-3爻）则下卦为用、上卦为体。
        生克吉凶：用生体为吉、体克用为小吉、体生用为泄气、用克体为凶、比和平稳。
        """
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(Spacing.S3)

        upper_element = ben_gua.get('upper_element', '')
        lower_element = ben_gua.get('lower_element', '')
        upper_gua_name = ben_gua.get('upper_name', '')
        lower_gua_name = ben_gua.get('lower_name', '')

        if not upper_element or not lower_element:
            return None

        # 五行色（与八字天干地支 chip 一致的实色方案，白字可读）
        wx_colors = {
            '金': Colors.METAL, '木': Colors.WOOD, '水': Colors.WATER,
            '火': Colors.FIRE, '土': Colors.EARTH,
        }

        # ---- 按动爻位置判定体用（动爻 1-3 在下卦、4-6 在上卦）----
        changing_yao = ben_gua.get('changing_yao', 0) or 0
        try:
            changing_yao = int(changing_yao)
        except (TypeError, ValueError):
            changing_yao = 0
        upper_is_yong = changing_yao >= 4  # 动爻在上卦 → 上卦为用
        if upper_is_yong:
            ti_name, ti_el = lower_gua_name, lower_element
            yong_name, yong_el = upper_gua_name, upper_element
            dong_desc = f'动爻在第 {changing_yao} 爻（上卦动）→ 上卦为用、下卦为体'
        else:
            ti_name, ti_el = upper_gua_name, upper_element
            yong_name, yong_el = lower_gua_name, lower_element
            dong_desc = (f'动爻在第 {changing_yao} 爻（下卦动）→ 下卦为用、上卦为体'
                         if changing_yao else '动爻信息缺失，暂以上卦为体、下卦为用')

        # ---- 五行生克：以体卦为中心判吉凶 ----
        sheng = {'金': '水', '水': '木', '木': '火', '火': '土', '土': '金'}
        ke = {'金': '木', '木': '土', '土': '水', '水': '火', '火': '金'}
        if sheng.get(yong_el) == ti_el:
            relation_text, verdict, relation_color, icon = (
                f'用卦生体卦（{yong_el}生{ti_el}）', '用生体 · 谋事易成、有外力相助',
                Colors.SUCCESS, '✨')
        elif sheng.get(ti_el) == yong_el:
            relation_text, verdict, relation_color, icon = (
                f'体卦生用卦（{ti_el}生{yong_el}）', '体生用 · 自己付出较多、宜稳勿急',
                Colors.WARNING, '💧')
        elif ke.get(ti_el) == yong_el:
            relation_text, verdict, relation_color, icon = (
                f'体卦克用卦（{ti_el}克{yong_el}）', '体克用 · 劳而可得、需主动争取',
                Colors.QINGHUA, '⚒')
        elif ke.get(yong_el) == ti_el:
            relation_text, verdict, relation_color, icon = (
                f'用卦克体卦（{yong_el}克{ti_el}）', '用克体 · 阻力较大、宜守不宜进',
                Colors.DANGER, '⚠')
        else:
            relation_text, verdict, relation_color, icon = (
                f'体用比和（{ti_el}与{yong_el}同行）', '比和 · 平稳顺遂、谋为稍待',
                Colors.QINGHUA, '🤝')

        def _gua_card(tag_text, gua_name, el):
            """构造体/用卦色块卡片。"""
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {wx_colors.get(el, Colors.QINGHUA)};
                    border-radius: {Spacing.RADIUS_SM};
                    padding: 10px;
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 8, 8, 8)
            cl.setSpacing(Spacing.S1)
            tag = QLabel(tag_text)
            tag.setAlignment(Qt.AlignCenter)
            tag.setStyleSheet(
                "font-size: 12px; color: rgba(255,255,255,0.85); "
                f"font-family: {Fonts.FAMILY_CN}; background: transparent;")
            name = QLabel(gua_name)
            name.setAlignment(Qt.AlignCenter)
            name.setStyleSheet(
                f"font-size: 17px; font-weight: {Fonts.WEIGHT_BOLD}; color: white; "
                f"font-family: {Fonts.FAMILY_SERIF}; background: transparent;")
            elem = QLabel(f'{el}行')
            elem.setAlignment(Qt.AlignCenter)
            elem.setStyleSheet(
                "font-size: 13px; color: white; background: transparent; "
                f"font-family: {Fonts.FAMILY_CN};")
            cl.addWidget(tag)
            cl.addWidget(name)
            cl.addWidget(elem)
            return card

        def _relation_card():
            """构造中间生克关系卡片。"""
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {Colors.CARD};
                    border: 2px solid {relation_color};
                    border-radius: {Spacing.RADIUS_SM};
                    padding: 10px;
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 8, 8, 8)
            cl.setSpacing(Spacing.S1)
            ic = QLabel(icon)
            ic.setAlignment(Qt.AlignCenter)
            ic.setStyleSheet("font-size: 26px; background: transparent;")
            rt = QLabel(relation_text)
            rt.setAlignment(Qt.AlignCenter)
            rt.setWordWrap(True)
            rt.setStyleSheet(
                f"font-size: 13px; color: {relation_color}; "
                f"font-weight: {Fonts.WEIGHT_BOLD}; font-family: {Fonts.FAMILY_CN}; background: transparent;")
            cl.addWidget(ic)
            cl.addWidget(rt)
            return card

        # 响应式三格：宽屏横排（体 → 关系 → 用），窄屏自动纵向堆叠
        flow = ResponsiveFlow(min_item_width=150, max_cols=3, min_cols=1, spacing=12)
        flow.add_widget(_gua_card('体卦（主 / 自己）', ti_name, ti_el))
        flow.add_widget(_relation_card())
        flow.add_widget(_gua_card('用卦（事 / 对方）', yong_name, yong_el))
        layout.addWidget(flow)

        # 断语 + 体用判定说明（白话小字）
        verdict_lbl = QLabel(verdict)
        verdict_lbl.setWordWrap(True)
        verdict_lbl.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY}; color: {relation_color};
            font-weight: {Fonts.WEIGHT_BOLD}; font-family: {Fonts.FAMILY_CN};
            background: transparent;
        """)
        layout.addWidget(verdict_lbl)

        dong_lbl = QLabel(f'※ {dong_desc}；体卦代表问卦者自身，用卦代表所问之事与外部环境。')
        dong_lbl.setWordWrap(True)
        dong_lbl.setStyleSheet(f"""
            font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN}; background: transparent;
        """)
        layout.addWidget(dong_lbl)
        return widget

    def _create_evolution_diagram(self, result_data):
        """创建卦象演变流程图（优化版：阶段序号徽标 + 鎏金顶条，与爻辞详解视觉一致）。"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.S3)

        ben_gua = result_data.get('ben_gua', {})
        hu_gua = result_data.get('hu_gua', {})
        bian_gua = result_data.get('bian_gua', {})

        stages = []
        if ben_gua and ben_gua.get('name'):
            stages.append(('本卦', ben_gua.get('name', ''), '初始'))
        if hu_gua and hu_gua.get('name'):
            stages.append(('互卦', hu_gua.get('name', ''), '过程'))
        if bian_gua and bian_gua.get('name'):
            stages.append(('变卦', bian_gua.get('name', ''), '结果'))

        if not stages:
            return None

        # 响应式：宽屏三阶段横排（带 ➜ 箭头），窄屏自动纵向堆叠（隐藏箭头）
        flow = ResponsiveFlow(min_item_width=200, max_cols=3, min_cols=1, spacing=8)
        arrows = []

        for i, (stage_name, gua_name, meaning) in enumerate(stages):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND};
                    border: 1px solid {Colors.QINGHUA_LIGHT};
                    border-radius: {Spacing.RADIUS_SM};
                    padding: 10px 12px;
                }}
            """)
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(0, 0, 0, 0)
            card_lay.setSpacing(Spacing.S2)
            card_lay.setAlignment(Qt.AlignCenter)

            # 顶部：阶段序号徽标 + 阶段名（青花蓝）
            head = QHBoxLayout()
            head.setSpacing(Spacing.S2)
            head.setAlignment(Qt.AlignCenter)

            idx_badge = QLabel(str(i + 1))
            idx_badge.setFixedSize(20, 20)
            idx_badge.setAlignment(Qt.AlignCenter)
            idx_badge.setStyleSheet(
                f"background: {Colors.QINGHUA}; color: {Colors.TEXT_INV}; "
                f"font-size: 11px; font-weight: {Fonts.W_BOLD}; "
                f"border-radius: 10px; font-family: {Fonts.BODY};")

            name_label = QLabel(stage_name)
            name_label.setStyleSheet(
                f"font-size: 13px; color: {Colors.PRIMARY}; "
                f"font-weight: {Fonts.W_BOLD}; font-family: {Fonts.BODY};")

            head.addWidget(idx_badge)
            head.addWidget(name_label)
            card_lay.addLayout(head)

            # 卦名（衬线大字）
            gua_label = QLabel(gua_name)
            gua_label.setAlignment(Qt.AlignCenter)
            gua_label.setStyleSheet(
                f"font-size: 17px; color: {Colors.TEXT}; "
                f"font-weight: {Fonts.W_BOLD}; font-family: {Fonts.FAMILY_SERIF};")

            # 意义（鎏金小字）
            meaning_label = QLabel(meaning)
            meaning_label.setAlignment(Qt.AlignCenter)
            meaning_label.setStyleSheet(
                f"font-size: 12px; color: {Colors.LIUJIN}; font-family: {Fonts.BODY};")

            card_lay.addWidget(gua_label)
            card_lay.addWidget(meaning_label)

            # 槽位：卡片 + 可选箭头（箭头随重排自动显隐）
            slot = QWidget()
            slot.setStyleSheet("background: transparent;")
            sl = QHBoxLayout(slot)
            sl.setContentsMargins(0, 0, 0, 0)
            sl.setSpacing(Spacing.S2)
            sl.addWidget(card, 1)
            if i < len(stages) - 1:
                arrow = QLabel('➜')
                arrow.setFixedWidth(22)
                arrow.setAlignment(Qt.AlignCenter)
                arrow.setStyleSheet(
                    f"font-size: 20px; color: {Colors.LIUJIN}; "
                    f"font-family: {Fonts.BODY}; background: transparent;")
                sl.addWidget(arrow)
                arrows.append(arrow)
            flow.add_widget(slot)

        def _on_reflow(cols):
            """重排回调：仅当全部阶段同一行时显示横向箭头。"""
            show_arrow = cols >= len(stages)
            for a in arrows:
                a.setVisible(show_arrow)

        flow.reflowed.connect(_on_reflow)
        layout.addWidget(flow)
        return widget

    def display_result(self, result_data):
        """显示起卦结果"""
        self._current_result = result_data
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        # M3-6：显示结果前清理旧错误态 holder，避免残留
        self._clear_error_holder()

        self.smart_analyze_btn.setVisible(True)
        # 起卦结果出来后即可导出（即使暂无 智能 解读）
        if hasattr(self, 'export_btn'):
            self.export_btn.setVisible(True)
        if hasattr(self, 'collapse_all_btn'):
            self.collapse_all_btn.setVisible(True)
            self.collapse_all_btn.setText('全部收起')

        # 更新顶部状态栏（注意：直接更新 init_ui 中已创建的 status_bar / status_label，
        # 切勿在此处重新 new 一个 status_bar 并塞进 content_layout，否则顶栏会一直显示加载文案）
        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(90, 143, 110, 0.08);
                border: 1px solid {Colors.SUCCESS};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        self.status_label.setText('✓ 起卦完成，卦象已生成')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.SUCCESS};
            font-family: {Fonts.FAMILY_CN};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)

        basic_info = result_data.get('basic_info', {})
        if basic_info:
            info_items = []
            if 'method' in basic_info:
                method_names = {
                    'time': '时间起卦', 'number': '数字起卦', 'direction': '方位起卦', 
                    'text': '文字起卦', 'copper_coin': '铜钱摇卦', 'stroke': '笔画起卦'
                }
                info_items.append(('起卦方式', method_names.get(basic_info['method'], basic_info['method'])))
            if 'question' in basic_info and basic_info['question']:
                info_items.append(('占问事项', basic_info['question']))
            if 'time' in basic_info:
                info_items.append(('起卦时间', basic_info['time']))
            if 'moving_yao' in basic_info:
                info_items.append(('动爻', basic_info['moving_yao']))

            if info_items:
                info_widget = self._create_info_grid(info_items)
                info_card = self._create_result_card('起卦信息', 'ℹ', info_widget)
                self.content_layout.addWidget(info_card)

        overall_info = result_data.get('overall', {})
        if overall_info:
            overall_widget = self._create_judgment_summary(overall_info)
            overall_card = self._create_result_card('吉凶总览', '⚖', overall_widget, highlight=True)
            self.content_layout.addWidget(overall_card)

        ben_gua = result_data.get('ben_gua', {})
        if ben_gua:
            ben_widget = self._create_hexagram_display(ben_gua, '本卦')
            ben_card = self._create_result_card('本卦（体卦）', '☯', ben_widget, highlight=True)
            self.content_layout.addWidget(ben_card)

        hu_gua = result_data.get('hu_gua', {})
        if hu_gua:
            hu_widget = self._create_hexagram_display(hu_gua, '互卦')
            hu_card = self._create_result_card('互卦（发展过程）', '🔄', hu_widget)
            self.content_layout.addWidget(hu_card)

        bian_gua = result_data.get('bian_gua', {})
        if bian_gua:
            bian_widget = self._create_hexagram_display(bian_gua, '变卦')
            bian_card = self._create_result_card('变卦（结果趋势）', '✨', bian_widget)
            self.content_layout.addWidget(bian_card)

        cuo_gua = result_data.get('cuo_gua', {})
        zong_gua = result_data.get('zong_gua', {})
        if cuo_gua or zong_gua:
            # 响应式：宽屏错/综并排，窄屏纵向堆叠
            cuo_zong_widget = ResponsiveFlow(min_item_width=270, max_cols=2,
                                             min_cols=1, spacing=12)

            if cuo_gua:
                cuo_widget = self._create_hexagram_display(cuo_gua, '错卦')
                cuo_zong_widget.add_widget(cuo_widget)

            if zong_gua:
                zong_widget = self._create_hexagram_display(zong_gua, '综卦')
                cuo_zong_widget.add_widget(zong_widget)

            cz_card = self._create_result_card('错卦 / 综卦（反面视角）', '🔄', cuo_zong_widget)
            self.content_layout.addWidget(cz_card)

        yao_list = result_data.get('yao_list', [])
        if yao_list:
            yao_widget = self._create_yao_display(yao_list)
            yao_card = self._create_result_card('爻辞详解', '📜', yao_widget)
            self.content_layout.addWidget(yao_card)

        # 新增：体用生克关系可视化
        ben_gua = result_data.get('ben_gua', {})
        if ben_gua:
            ti_yong_widget = self._create_ti_yong_relationship(ben_gua)
            if ti_yong_widget:
                ti_yong_card = self._create_result_card('体用生克', '⚗', ti_yong_widget)
                self.content_layout.addWidget(ti_yong_card)

        # 新增：卦象演变流程图
        if ben_gua or result_data.get('hu_gua') or result_data.get('bian_gua'):
            evolution_widget = self._create_evolution_diagram(result_data)
            if evolution_widget:
                evolution_card = self._create_result_card('卦象演变', '🔄', evolution_widget)
                self.content_layout.addWidget(evolution_card)

        smart_placeholder = QFrame()
        smart_placeholder.setVisible(False)
        smart_placeholder.setObjectName('smart_result_placeholder')
        self.content_layout.addWidget(smart_placeholder)

        self.content_layout.addStretch()

        # 结果卡片依次淡入，增强视觉交互（与八字面板一致）
        self._fade_in_widgets()

    def _fade_in_widgets(self):
        """淡入动画：起卦结果各卡片依次淡入（与八字面板一致），增强视觉交互。

        每张卡片套一层 QGraphicsOpacityEffect，从 0→1 用 OutCubic 缓动淡入，
        并按序号错峰 20ms 启动（总延迟不超过 800ms），营造「逐张浮现」的层次感。

        注意：不按 isVisible() 跳过——若仅当可见才淡入，则当结果面板此刻不是
        当前堆叠页（未切换/未映射）时会导致整段淡入被跳过、动画失效。动画始终
        启动并收敛到 opacity=1，隐藏控件（setVisible(False) 的占位）仍保持隐藏，
        无副作用。
        """
        self._fade_anims = []
        for i in range(self.content_layout.count()):
            item = self.content_layout.itemAt(i)
            if not item:
                continue
            widget = item.widget()
            if widget is None:
                continue
            effect = QGraphicsOpacityEffect(widget)
            effect.setOpacity(0.0)
            widget.setGraphicsEffect(effect)
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(350)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            self._fade_anims.append(anim)
            # 错峰启动，总延迟不超过 800ms
            QTimer.singleShot(min(i * 20, 800), anim.start)

    def _create_info_grid(self, data):
        """创建信息网格（标签徽标 + 值，行间细分隔，与面板国风风格一致）。"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.S0)

        for i, (label, value) in enumerate(data):
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(10, 8, 10, 8)
            rl.setSpacing(Spacing.S3)

            # 标签：鎏金微光小药丸（与卦象类型徽标同源）
            label_widget = QLabel(label)
            label_widget.setFixedWidth(64)
            label_widget.setAlignment(Qt.AlignCenter)
            label_widget.setStyleSheet(f"""
                font-size: {Fonts.SZ_MICRO};
                color: {Colors.TEXT2};
                font-weight: {Fonts.W_MEDIUM};
                font-family: {Fonts.BODY};
                background-color: {Colors.HIGHLIGHT_GLOW};
                border-radius: {Spacing.RADIUS_SM};
                padding: 3px 6px;
            """)

            value_widget = QLabel(str(value))
            value_widget.setStyleSheet(f"""
                font-size: {Fonts.SZ_BODY};
                color: {Colors.TEXT};
                font-weight: {Fonts.W_BOLD};
                font-family: {Fonts.BODY};
                line-height: 1.5;
            """)
            value_widget.setWordWrap(True)

            rl.addWidget(label_widget)
            rl.addWidget(value_widget, 1)
            layout.addWidget(row)

            # 行间细分隔线（末行不加）
            if i < len(data) - 1:
                div = QFrame()
                div.setFixedHeight(1)
                div.setStyleSheet(f"background: {Colors.DIVIDER}; margin: 0 10px;")
                layout.addWidget(div)

        return widget

    def show_loading(self, message: str = None):
        """显示加载状态（起卦 / AI 解读统一入口）。

        Args:
            message: 传 None（或不传）为起卦加载，青花蓝主题；
                     传入文案则为龙虎山大师兄解读加载，鎏金主题。
        """
        is_ai = bool(message)

        # 清空内容区旧控件
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.smart_analyze_btn.setVisible(False)
        self.smart_analyze_btn.setEnabled(not is_ai)
        if hasattr(self, 'export_btn'):
            self.export_btn.setVisible(False)
        if hasattr(self, 'collapse_all_btn'):
            self.collapse_all_btn.setVisible(False)

        # M3-6：显示加载态前清理旧错误态 holder，避免残留
        self._clear_error_holder()

        if is_ai:
            # AI 解读：鎏金主题
            self.status_bar.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(184, 138, 48, 0.08);
                    border: 1px solid {Colors.LIUJIN};
                    border-radius: {Spacing.CONTROL_RADIUS};
                    padding: 12px 20px;
                }}
            """)
            self.status_label.setText('🧙 龙虎山大师兄解读中…')
            self.status_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.LIUJIN};
                font-family: {Fonts.FAMILY_CN};
                font-weight: {Fonts.WEIGHT_BOLD};
            """)
            panel = loading_panel(
                message=message,
                sub='请稍候，大师兄正结合卦辞爻辞、体用生克逐项推演',
                color=Colors.LIUJIN,
                hints=['大师兄正凝神审卦…', '正在参详本卦、互卦、变卦…',
                       '正在推敲体用生克与动爻…', '正在撰写趋吉避凶建议…'])
        else:
            # 起卦：青花蓝主题
            self.status_bar.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Colors.CARD}, stop:0.5 {Colors.QINGHUA_GLOW}, stop:1 {Colors.CARD});
                    border: 1px solid {Colors.BORDER_LIGHT};
                    border-radius: {Spacing.CONTROL_RADIUS};
                    padding: 12px 20px;
                }}
            """)
            self.status_label.setText('⏳ 正在起卦分析，请稍候…')
            self.status_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_TERTIARY};
                font-family: {Fonts.FAMILY_CN};
            """)
            panel = loading_panel(
                message='正在起卦分析，请稍候…',
                sub='心诚则灵，卦爻排布中',
                color=Colors.QINGHUA,
                hints=['正在排布卦爻…', '正在推演本卦、互卦、变卦…',
                       '正在分析体用生克…', '正在参详卦辞爻辞…'])

        panel.setMinimumHeight(380)
        self.content_layout.addWidget(panel)
        self.content_layout.addStretch()

    def show_ai_loading(self, message: str = '龙虎山大师兄正在解读卦象玄机…'):
        """显示龙虎山大师兄解读加载态（供主窗口调用）。"""
        self.show_loading(message)

    def display_ai_analysis_result(self, smart_data: dict):
        """显示智能分析结果（别名方法，兼容调用方使用 display_ai_analysis_result 的情况）"""
        self.display_analysis_result(smart_data)

    def display_analysis_result(self, smart_data: dict):
        """显示智能分析结果（统一渲染入口）。

        修复点：
        1. 渲染前先清掉上一次 AI 解读容器（ai_analysis_container），
           防止重复回调产生两份解读；
        2. 渲染后状态栏文案已由 display_result 重置为起卦完成，
           进一步恢复为「解读完成」与可点击的重新解读按钮。
        """
        # 若 AI 未配置，则不显示龙虎山大师兄分析预测
        try:
            from core.ai_config import is_ai_configured
            if not is_ai_configured():
                # 清理旧 AI 容器并返回，避免展示
                self._clear_prev_ai_container()
                self.display_result(getattr(self, "_current_result", {}) or {})
                return
        except Exception:
            pass
        if not smart_data or not isinstance(smart_data, dict):
            self._show_error("龙虎山大师兄未返回有效内容，请重试")
            return
        self._current_智能 = smart_data
        rd = getattr(self, "_current_result", {}) or {}
        # 渲染前先清掉旧 AI 解读容器，避免重复
        self._clear_prev_ai_container()
        self.display_result(rd)
        from ui.components.ai_analysis_renderer import render_analysis as render
        render("meihua", smart_data, self.content_layout)
        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(90, 143, 110, 0.08);
                border: 1px solid {Colors.SUCCESS};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        self.status_label.setText("✓ 龙虎山大师兄解读完成")
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.SUCCESS};
            font-family: {Fonts.FAMILY_CN};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)
        self.smart_analyze_btn.setVisible(True)
        self.smart_analyze_btn.setEnabled(True)
        self.smart_analyze_btn.setText("⚡ 智能分析")
        QTimer.singleShot(50, self._scroll_to_section_meihua)

    def _show_error(self, message: str):
        """展示 AI 解读异常提示，委托 ErrorState（M3-6：统一错误视觉 + 重试信号）。

        Args:
            message: 异常/错误说明文案

        清空内容区并重建错误态 holder，ErrorState 提供统一错误视觉与重试入口，
        重试信号连到 show_ai_loading 重新展示加载态（供用户再次触发解读）。
        """
        from ui.components.states import ErrorState

        # 清空内容区旧控件（含旧错误态/提示）
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 重建头部：确保智能分析按钮可见（供用户再次触发解读）
        self.smart_analyze_btn.setVisible(True)
        self.smart_analyze_btn.setEnabled(True)
        self.smart_analyze_btn.setText('⚡ 智能分析')

        # 清空状态栏旧样式，切换到错误态样式
        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        self.status_label.setText('⚠ 龙虎山大师兄异常')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.DANGER};
            font-family: {Fonts.FAMILY_CN};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)

        # 重建错误态 holder（清空旧 holder，接管 ErrorState）
        self._clear_error_holder()
        holder = QWidget()
        holder.setStyleSheet('background: transparent;')
        v = QVBoxLayout(holder)
        v.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        v.setSpacing(Spacing.S0)
        err = ErrorState(
            title='分析异常',
            message=message,
            retry_hint='重试',
            show_retry=True,
            color=Colors.DANGER,
            parent=holder,
        )
        # M3-6：重试信号连到重新展示加载态（用户可再次触发解读）
        err.retry.connect(self.show_ai_loading)
        v.addWidget(err, 1)

        # 保存错误态 holder，供后续清理
        self._set_error_holder(holder)
        self.content_layout.addWidget(holder)

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

    def _clear_error_holder(self):
        """移除当前错误态 holder（重建错误态时清理旧实例）。"""
        old = self._error_holder
        if old is not None:
            try:
                old.deleteLater()
            except Exception:
                pass
            self._error_holder = None

    def _set_error_holder(self, holder: QWidget):
        """设置错误态 holder（供上层/显示逻辑调用）。"""
        self._error_holder = holder

    def _scroll_to_section_meihua(self):
        """滚动到 智能 解读区域"""
        try:
            target = self.content_widget.findChild(QFrame, 'smart_result_placeholder')
            if target is not None:
                self.content_area.ensureWidgetVisible(target)
                return
            # 回退：滚到底
            sb = self.content_area.verticalScrollBar()
            if sb:
                sb.setValue(sb.maximum())
        except Exception:
            pass

    def get_hexagram_data_for_ai(self) -> dict:
        """获取用于智能分析的卦象数据"""
        rd = getattr(self, '_current_result', {})
        if not rd:
            return {}

        base = rd.get('ben_gua', {})
        hu = rd.get('hu_gua', {})
        bian = rd.get('bian_gua', {})
        overall = rd.get('overall', {})
        
        # 新增：铜钱摇卦/笔画起卦的特殊信息
        div_extra = rd.get('divination_extra', {})

        hexagram_data = {
            'base': {
                'name': base.get('name', ''),
                'upper_name': base.get('upper_name', ''),
                'lower_name': base.get('lower_name', ''),
                'upper_element': base.get('upper_element', ''),
                'lower_element': base.get('lower_element', ''),
                'upper_nature': base.get('upper_nature', ''),
                'lower_nature': base.get('lower_nature', ''),
                'gua_ci': base.get('gua_ci', ''),
                'description': base.get('description', ''),
            },
            'hu': {
                'name': hu.get('name', ''),
                'description': hu.get('description', '')
            },
            'bian': {
                'name': bian.get('name', ''),
                'description': bian.get('description', ''),
                'judgment': overall.get('level', '')
            },
            'overall_judgment': overall.get('level', '')
        }
        
        # 铜钱摇卦特殊信息
        if div_extra.get('six_lines'):
            hexagram_data['copper_coin_six_lines'] = div_extra['six_lines']
            hexagram_data['changing_positions'] = div_extra.get('changing_positions', [])
        
        # 笔画起卦特殊信息
        if div_extra.get('char'):
            hexagram_data['stroke_char'] = div_extra.get('char', '')
            hexagram_data['stroke_count'] = div_extra.get('stroke_count', 0)
        
        # 时间起卦
        if div_extra.get('year'):
            hexagram_data['time_year'] = div_extra.get('year')
            hexagram_data['time_month'] = div_extra.get('month')
            hexagram_data['time_day'] = div_extra.get('day')
            hexagram_data['time_hour'] = div_extra.get('hour')
        
        # 数字起卦
        if div_extra.get('numbers'):
            hexagram_data['numbers'] = div_extra['numbers']

        yao_list = rd.get('yao_list', [])
        if yao_list:
            for yao in yao_list:
                if yao.get('is_moving', False):
                    hexagram_data['base']['changing_yao'] = yao.get('position', 0)
                    hexagram_data['base']['changing_yao_name'] = yao.get('name', '')
                    hexagram_data['base']['changing_yao_text'] = yao.get('text', '')
                    hexagram_data['base']['changing_yao_meaning'] = yao.get('meaning', '')
                    break

        return hexagram_data

    def clear(self):
        """清空结果"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        # M3-6：清空错误态 holder 引用，避免遗留已删控件
        self._clear_error_holder()

        self.empty_state = self._create_empty_state()
        self.content_layout.addWidget(self.empty_state)

        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        self.status_label.setText('ℹ 请完善左侧参数，点击「起卦」获取卦象分析')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        self.smart_analyze_btn.setVisible(False)
        if hasattr(self, 'export_btn'):
            self.export_btn.setVisible(False)
        if hasattr(self, 'collapse_all_btn'):
            self.collapse_all_btn.setVisible(False)
        self._current_智能 = {}

    def _on_export_click(self):
        """导出梅花起卦结果（复用 ExportDialog 与三导出器）。"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox, QDialog
        from ui.components.export_dialog import ExportDialog
        from ui.export import CsvExporter, ExcelExporter
        from ui.export.base_exporter import filter_export_data

        rd = getattr(self, '_current_result', None)
        if not rd:
            QMessageBox.warning(self, '导出失败', '暂无可导出的起卦结果')
            return

        export_data = {
            'meihua_data': dict(rd),
            'basic_info': {'pan_type': '梅花易数'},
        }
        智能 = getattr(self, '_current_智能', None)
        if isinstance(智能, dict) and 智能:
            export_data['meihua_ai'] = 智能

        dialog = ExportDialog(export_data, parent=self)
        dialog.filename_edit.setText('梅花易数')
        if dialog.exec() == QDialog.DialogCode.Accepted:
            format_type = dialog.get_selected_format()
            chapters = dialog.get_selected_chapters()
            export_data = filter_export_data(export_data, chapters)

            filename = dialog.filename_edit.text().strip() or '梅花易数'
            if format_type == 'csv':
                ext, file_filter = '.csv', 'CSV Files (*.csv)'
            elif format_type == 'excel':
                ext, file_filter = '.xlsx', 'Excel Files (*.xlsx)'
            else:
                ext, file_filter = '.pdf', 'PDF Files (*.pdf)'

            file_path, _ = QFileDialog.getSaveFileName(
                self, '导出梅花起卦结果', filename + ext, file_filter)
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
