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
from ui.components.collapsible_card import (CollapsibleCard, ai_section_header,
                                          highlight_label, probability_stats_widget)


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

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

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
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(18)

        self.empty_state = self._create_empty_state()
        self.content_layout.addWidget(self.empty_state)

        self.content_area.setWidget(self.content_widget)
        main_layout.addWidget(self.content_area)

        self.setLayout(main_layout)

    def _create_empty_state(self):
        """创建空状态"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        icon = QLabel('🔮')
        icon.setStyleSheet(f"font-size: 64px; color: {Colors.BORDER}; opacity: 0.5;")
        icon.setAlignment(Qt.AlignCenter)

        title = QLabel('请完善左侧起卦参数')
        title.setStyleSheet(f"""
            font-size: 18px;
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel('点击「起卦」获取梅花易数卦象分析')
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
            opacity: 0.7;
        """)
        subtitle.setAlignment(Qt.AlignCenter)

        layout.addStretch()
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()

        widget.setMinimumHeight(400)
        return widget

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
        layout.setSpacing(10)

        name = hexagram_info.get('name', '')
        symbol = hexagram_info.get('symbol', '')
        judgment = hexagram_info.get('judgment', '')
        explanation = hexagram_info.get('explanation', '')
        upper_gua = hexagram_info.get('upper_gua', '')
        lower_gua = hexagram_info.get('lower_gua', '')

        # ---- 头部：类型徽标 + 卦名（衬线大字） ----
        header_row = QHBoxLayout()
        header_row.setSpacing(10)
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
            ob_lay.setSpacing(4)

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
            eb_lay.setSpacing(4)
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
        layout.setSpacing(10)

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
            card_lay.setSpacing(0)

            # ---- 爻头：强调色条 + 爻名 + （动爻徽标） ----
            header = QWidget()
            header_lay = QHBoxLayout(header)
            header_lay.setContentsMargins(12, 10, 12, 10)
            header_lay.setSpacing(8)

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
                ob_lay.setSpacing(4)

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
                eb_lay.setSpacing(4)

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
        layout.setSpacing(12)

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
        layout.setSpacing(8)

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
            sug_layout.setSpacing(12)

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
        """创庺体用生克关系图"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        upper_element = ben_gua.get('upper_element', '')
        lower_element = ben_gua.get('lower_element', '')
        upper_gua_name = ben_gua.get('upper_name', '')
        lower_gua_name = ben_gua.get('lower_name', '')

        if not upper_element or not lower_element:
            return None

        # 五行元素颜色映射（使用系统自带五行色）
        WX_COLORS = {
            '金': Colors.METAL,
            '木': Colors.WOOD,
            '水': Colors.WATER,
            '火': Colors.FIRE,
            '土': Colors.EARTH,
        }
        
        # 体用关系判断（梅花易数：不动为体，动者为用）
        ti_gua = f"{upper_gua_name}(体)"
        yong_gua = f"{lower_gua_name}(用)"
        
        # 生克关系计算
        GENERATES = {'金→水', '水→木', '木→火', '火→土', '土→金'}
        OVERCOMES = {'金→木', '木→土', '土→水', '水→火', '火→金'}
        
        relation_key = f"{upper_element}→{lower_element}"
        reverse_relation_key = f"{lower_element}→{upper_element}"
        
        if relation_key in GENERATES or reverse_relation_key in OVERCOMES:
            relationship = f"{upper_element}生{lower_element}" if relation_key in GENERATES else f"{lower_element}生{upper_element}"
            relation_color = Colors.SUCCESS
            relation_icon = "✨"
        elif relation_key in OVERCOMES or reverse_relation_key in GENERATES:
            relationship = f"{upper_element}克{lower_element}" if relation_key in OVERCOMES else f"{lower_element}克{upper_element}"
            relation_color = Colors.WARNING
            relation_icon = "⚔️"
        else:
            relationship = f"{upper_element}与{lower_element}比和"
            relation_color = Colors.QINGHUA
            relation_icon = "🤝"

        # 绘制体用生克关系卡片
        info_layout = QGridLayout()
        info_layout.setSpacing(16)
        
        # 体卦
        ti_widget = QFrame()
        ti_widget.setStyleSheet(f"""
            QFrame {{
                background: linear-gradient(to bottom, {WX_COLORS.get(upper_element, Colors.TEXT)}, rgba(255,255,255,0.1));
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        ti_inner = QVBoxLayout(ti_widget)
        ti_label = QLabel(ti_gua)
        ti_label.setAlignment(Qt.AlignCenter)
        ti_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: white;")
        ti_elem = QLabel(upper_element)
        ti_elem.setAlignment(Qt.AlignCenter)
        ti_elem.setStyleSheet(f"font-size: 24px; color: white;")
        ti_inner.addWidget(ti_label)
        ti_inner.addWidget(ti_elem)
        info_layout.addWidget(ti_widget, 0, 0)
        
        # 关系
        rel_widget = QFrame()
        rel_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BACKGROUND};
                border: 2px solid {relation_color};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        rel_inner = QVBoxLayout(rel_widget)
        rel_icon = QLabel(relation_icon)
        rel_icon.setAlignment(Qt.AlignCenter)
        rel_icon.setStyleSheet("font-size: 28px;")
        rel_text = QLabel(relationship)
        rel_text.setAlignment(Qt.AlignCenter)
        rel_text.setStyleSheet(f"font-size: 16px; color: {relation_color}; font-weight: bold;")
        rel_inner.addWidget(rel_icon)
        rel_inner.addWidget(rel_text)
        info_layout.addWidget(rel_widget, 0, 1)
        
        # 用卦
        yong_widget = QFrame()
        yong_widget.setStyleSheet(f"""
            QFrame {{
                background: linear-gradient(to bottom, {WX_COLORS.get(lower_element, Colors.TEXT)}, rgba(255,255,255,0.1));
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        yong_inner = QVBoxLayout(yong_widget)
        yong_label = QLabel(yong_gua)
        yong_label.setAlignment(Qt.AlignCenter)
        yong_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: white;")
        yong_elem = QLabel(lower_element)
        yong_elem.setAlignment(Qt.AlignCenter)
        yong_elem.setStyleSheet(f"font-size: 24px; color: white;")
        yong_inner.addWidget(yong_label)
        yong_inner.addWidget(yong_elem)
        info_layout.addWidget(yong_widget, 0, 2)

        layout.addLayout(info_layout)
        return widget

    def _create_evolution_diagram(self, result_data):
        """创建卦象演变流程图（优化版：阶段序号徽标 + 鎏金顶条，与爻辞详解视觉一致）。"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

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

        stage_layout = QHBoxLayout()
        stage_layout.setSpacing(12)
        stage_layout.setAlignment(Qt.AlignCenter)

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
            card_lay.setSpacing(6)
            card_lay.setAlignment(Qt.AlignCenter)

            # 顶部：阶段序号徽标 + 阶段名（青花蓝）
            head = QHBoxLayout()
            head.setSpacing(6)
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
                f"font-size: 14px; color: {Colors.PRIMARY}; "
                f"font-weight: {Fonts.W_BOLD}; font-family: {Fonts.BODY};")

            head.addWidget(idx_badge)
            head.addWidget(name_label)
            card_lay.addLayout(head)

            # 卦名（衬线大字）
            gua_label = QLabel(gua_name)
            gua_label.setAlignment(Qt.AlignCenter)
            gua_label.setStyleSheet(
                f"font-size: 18px; color: {Colors.TEXT}; "
                f"font-weight: {Fonts.W_BOLD}; font-family: {Fonts.FAMILY_SERIF};")

            # 意义（鎏金小字）
            meaning_label = QLabel(meaning)
            meaning_label.setAlignment(Qt.AlignCenter)
            meaning_label.setStyleSheet(
                f"font-size: 12px; color: {Colors.LIUJIN}; font-family: {Fonts.BODY};")

            card_lay.addWidget(gua_label)
            card_lay.addWidget(meaning_label)
            stage_layout.addWidget(card)

            if i < len(stages) - 1:
                arrow = QLabel('➜')
                arrow.setAlignment(Qt.AlignCenter)
                arrow.setStyleSheet(
                    f"font-size: 22px; color: {Colors.LIUJIN}; font-family: {Fonts.BODY};")
                stage_layout.addWidget(arrow)

        layout.addLayout(stage_layout)
        return widget

    def display_result(self, result_data):
        """显示起卦结果"""
        self._current_result = result_data
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.smart_analyze_btn.setVisible(True)
        # 起卦结果出来后即可导出（即使暂无 智能 解读）
        if hasattr(self, 'export_btn'):
            self.export_btn.setVisible(True)

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
            cuo_zong_widget = QWidget()
            cz_layout = QHBoxLayout(cuo_zong_widget)
            cz_layout.setContentsMargins(0, 0, 0, 0)
            cz_layout.setSpacing(12)

            if cuo_gua:
                cuo_widget = self._create_hexagram_display(cuo_gua, '错卦')
                cz_layout.addWidget(cuo_widget, 1)

            if zong_gua:
                zong_widget = self._create_hexagram_display(zong_gua, '综卦')
                cz_layout.addWidget(zong_widget, 1)

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
        layout.setSpacing(0)

        for i, (label, value) in enumerate(data):
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(10, 8, 10, 8)
            rl.setSpacing(12)

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

    def show_loading(self):
        """显示加载状态"""
        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.CARD}, stop:0.5 {Colors.HIGHLIGHT_GLOW}, stop:1 {Colors.CARD});
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        self.status_label.setText('⏳ 正在起卦分析，请稍候...')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        self.smart_analyze_btn.setVisible(False)
        if hasattr(self, 'export_btn'):
            self.export_btn.setVisible(False)

        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        loading_widget = self._create_loading_widget()
        self.content_layout.addWidget(loading_widget)
        self.content_layout.addStretch()

    def _create_loading_widget(self):
        """创建加载动画组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        taiji = RotatingLabel('☯')
        taiji.setFixedSize(120, 120)
        taiji.setStyleSheet(f"font-size: 80px; color: {Colors.PRIMARY};")
        taiji.setAlignment(Qt.AlignCenter)

        self.taiji_animation = QPropertyAnimation(taiji, b"rotation")
        self.taiji_animation.setDuration(3000)
        self.taiji_animation.setStartValue(0)
        self.taiji_animation.setEndValue(360)
        self.taiji_animation.setEasingCurve(QEasingCurve.Linear)
        self.taiji_animation.setLoopCount(-1)
        self.taiji_animation.start()

        text = QLabel('正在起卦分析，请稍候...')
        text.setStyleSheet(f"""
            font-size: 16px;
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
            letter-spacing: 1px;
        """)
        text.setAlignment(Qt.AlignCenter)

        layout.addStretch()
        layout.addWidget(taiji)
        layout.addWidget(text)
        layout.addStretch()

        widget.setMinimumHeight(400)
        return widget

    def show_loading(self, message: str = '龙虎山大师兄正在解读卦象玄机…'):
        """显示智能分析加载状态"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.smart_analyze_btn.setVisible(False)
        self.smart_analyze_btn.setEnabled(False)

        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(196, 154, 60, 0.08);
                border: 1px solid {Colors.HIGHLIGHT};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        self.status_label.setText('🧙 龙虎山大师兄解读中…')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.HIGHLIGHT};
            font-family: {Fonts.FAMILY_CN};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)

        loading_widget = self._create_loading_widget(message)
        self.content_layout.addWidget(loading_widget)
        self.content_layout.addStretch()

    def _create_loading_widget(self, message: str) -> QWidget:
        """创建智能分析加载控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        icon_label = QLabel('☯')
        icon_label.setStyleSheet(f"font-size: 56px; color: {Colors.HIGHLIGHT};")
        icon_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel(message)
        text_label.setStyleSheet(f"""
            font-size: 16px;
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        text_label.setAlignment(Qt.AlignCenter)

        sub_label = QLabel('请稍候，龙虎山大师兄正在结合卦辞爻辞进行深度解读')
        sub_label.setStyleSheet(f"""
            font-size: 12px;
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        sub_label.setAlignment(Qt.AlignCenter)

        layout.addStretch()
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addWidget(sub_label)
        layout.addStretch()
        widget.setMinimumHeight(400)
        return widget

    def display_ai_analysis_result(self, smart_data: dict):
        """显示智能分析结果（别名方法，兼容调用方使用 display_ai_analysis_result 的情况）"""
        self.display_analysis_result(smart_data)

    def display_analysis_result(self, smart_data: dict):
        """显示智能分析结果（适配analysis_pipeline输出格式）

        关键修复：
        1) 不再完全依赖 placeholder 机制（display_result 创建的占位 QFrame），
           改为兼容两种情况：placeholder 存在 / 已被消费。
        2) 防御性处理：智能 返回为空、字段类型异常时给出兜底提示，避免右侧空白。
        3) 完成后滚动到 智能 区域，让用户第一眼看到 智能 解读内容。
        """
        # 0) 防御性检查
        if not smart_data or not isinstance(smart_data, dict):
            self._show_error('龙虎山大师兄未返回有效内容，请重试')
            return

        # 缓存 智能 解读，供导出按钮复用
        self._current_智能 = smart_data

        rd = getattr(self, '_current_result', {}) or {}

        # 1) 先恢复原始面板（不重建占位）
        self.display_result(rd)

        # 字段契约以 core.analysis_storage._JSON_SCHEMAS['meihua'] 为准：
        #   - 段落型（字符串）：final_verdict / disclaimer
        #   - 列表型（字符串列表）：analysis / hexagram_interpretations /
        #     scenario_advice / historical_cases / probability_stats / advice
        # 注意：gua_overview / situation_analysis 等为历史废弃键，AI 已不再产出，必须移除，
        # 否则只能看到『总结判断』而丢失全部卦象与建议详情（表现为总结过于简单）。
        paragraph_fields = [
            ('final_verdict', '总结判断', '🎯', Colors.QINGHUA),
            ('disclaimer', '免责声明', '⚠', Colors.TEXT_TERTIARY),
        ]
        list_fields = [
            ('analysis', '卦象分析', '☯', Colors.PRIMARY),
            ('hexagram_interpretations', '卦爻解释', '📖', Colors.HIGHLIGHT),
            ('advice', '行动建议', '💡', Colors.PRIMARY),
            ('scenario_advice', '场景化建议', '🎯', Colors.HIGHLIGHT),
            ('historical_cases', '历史案例', '📚', Colors.SUCCESS),
            ('probability_stats', '概率统计', '📊', Colors.DANGER),
        ]

        # 2) 构建 智能 内容容器：金色分隔标题 + 各子项折叠卡片（与八字面板 智能 区一致）
        container = QWidget()
        cv = QVBoxLayout(container)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(12)
        cv.addWidget(ai_section_header('龙虎山大师兄分析预测'))

        # 重点提示（高亮标注最重要结论）：key_points 为 '\n' 分隔的多段短句
        key_points = smart_data.get('key_points')
        if isinstance(key_points, (list, tuple)):
            kp_text = '\n'.join(str(x) for x in key_points if x and str(x).strip())
        elif isinstance(key_points, str):
            kp_text = key_points
        else:
            kp_text = ''
        if kp_text and kp_text.strip():
            cv.addWidget(highlight_label('【重点提示】\n' + kp_text.strip(), Colors.LIUJIN))

        has_content = False

        def _build_section_card(title, icon, color, items):
            """根据字段值（字符串或列表）构建一节折叠卡片，健壮处理类型。"""
            if isinstance(items, str):
                items = [items] if items.strip() else []
            elif isinstance(items, (list, tuple)):
                items = [str(x) for x in items if x is not None and str(x).strip()]
            else:
                items = [str(items)] if items else []
            if not items:
                return None
            section_widget = QFrame()
            section_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND};
                    border-radius: {Spacing.CONTROL_RADIUS};
                }}
            """)
            section_layout = QVBoxLayout(section_widget)
            section_layout.setContentsMargins(12, 10, 12, 10)
            section_layout.setSpacing(8)
            for idx, item in enumerate(items):
                item_layout = QHBoxLayout()
                item_layout.setSpacing(10)

                num_label = QLabel(f'{idx + 1}')
                num_label.setStyleSheet(f"""
                    background: {color}; color: white;
                    font-size: 11px; font-weight: {Fonts.WEIGHT_BOLD};
                    border-radius: 10px; min-width: 20px; min-height: 20px;
                    font-family: {Fonts.FAMILY_CN};
                """)
                num_label.setAlignment(Qt.AlignCenter)
                num_label.setFixedSize(20, 20)

                text_label = QLabel(str(item))
                text_label.setStyleSheet(f"""
                    font-size: {Fonts.SIZE_BODY};
                    color: {Colors.TEXT_SECONDARY};
                    font-family: {Fonts.FAMILY_CN};
                    line-height: 1.6;
                """)
                text_label.setWordWrap(True)

                item_layout.addWidget(num_label)
                item_layout.addWidget(text_label, 1)
                section_layout.addLayout(item_layout)
            card = CollapsibleCard(title, icon, accent_color=color, collapsed=False)
            card.set_content(section_widget)
            return card

        # 段落型字段（整体一节，不拆分）
        for key, title, icon, color in paragraph_fields:
            val = smart_data.get(key)
            if isinstance(val, (list, tuple)):
                val = '\n'.join(str(x) for x in val if x)
            if not val or not str(val).strip():
                continue
            has_content = True
            card = _build_section_card(title, icon, color, [str(val)])
            if card:
                cv.addWidget(card)

        # 列表型字段
        for key, title, icon, color in list_fields:
            items = smart_data.get(key)
            # 概率统计需要可视化展示（标签+进度条+说明），不走纯文本列表
            if key == 'probability_stats':
                if isinstance(items, (list, tuple)):
                    items = [str(x) for x in items if x and str(x).strip()]
                elif isinstance(items, str):
                    items = [items] if items.strip() else []
                else:
                    items = []
                if not items:
                    continue
                has_content = True
                card = CollapsibleCard(title, icon, accent_color=color, collapsed=False)
                card.set_content(probability_stats_widget(items, color))
                cv.addWidget(card)
                continue
            if key == 'advice':
                card = _build_advice_card(title, icon, color, items)
                if card:
                    has_content = True
                    cv.addWidget(card)
                continue
            card = _build_section_card(title, icon, color, items)
            if card:
                has_content = True
                cv.addWidget(card)

        def _build_advice_card(title, icon, color, items):
            """将 advice 列表渲染为「可执行建议卡片」：优先级标签 + 行动说明 + 时机/规避提示。"""
            if isinstance(items, str):
                items = [items] if items.strip() else []
            elif isinstance(items, (list, tuple)):
                items = [str(x) for x in items if x is not None and str(x).strip()]
            else:
                items = [str(items)] if items else []
            if not items:
                return None

            # 优先级 → 对应颜色映射（高=鎏金/中=青花蓝/低=灰）
            _PRIORITY_STYLE = {
                '高': (Colors.LIUJIN, Colors.LIUJIN_GLOW, '🔥'),
                '中': (Colors.QINGHUA, Colors.QINGHUA_GLOW, '📌'),
                '低': (Colors.TEXT_TERTIARY, Colors.CARD, '💬'),
            }
            # 关键词 → 风险色 / 正向色
            _RISK_KW = ('避免', '忌讳', '不宜', '切勿', '危险', '小心', '防')
            _POSITIVE_KW = ('宜', '建议', '可', '应该', '应当')

            section_widget = QFrame()
            section_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND};
                    border-radius: {Spacing.CONTROL_RADIUS};
                }}
            """)
            section_layout = QVBoxLayout(section_widget)
            section_layout.setContentsMargins(12, 10, 12, 10)
            section_layout.setSpacing(10)

            for idx, item in enumerate(items, 1):
                # 解析优先级前缀 「【高】」「【中】」「【低】」
                prio_label = '中'
                prio_icon = '📌'
                prio_color, prio_bg, prio_icon = _PRIORITY_STYLE.get('中', _PRIORITY_STYLE['中'])
                cleaned = item.strip()
                if cleaned.startswith('【') and '】' in cleaned:
                    end = cleaned.index('】')
                    tag = cleaned[2:end]
                    if tag in _PRIORITY_STYLE:
                        prio_color, prio_bg, prio_icon = _PRIORITY_STYLE[tag]
                        prio_label = tag
                        cleaned = cleaned[end + 1:].strip()

                # 按句拆分：识别「时机」「避免」「建议」等关键词分段
                parts = _split_advice_parts(cleaned)

                row = QFrame()
                row.setStyleSheet(
                    f"QFrame {{ background-color: {prio_bg}; "
                    f"border-left: 4px solid {prio_color}; "
                    f"border-radius: {Spacing.RADIUS_SM}; }}"
                )
                rl = QVBoxLayout(row)
                rl.setContentsMargins(14, 10, 14, 10)
                rl.setSpacing(6)

                # 头部：序号 + 优先级图标 + 首句（核心行动）
                head = QHBoxLayout()
                head.setSpacing(8)
                num = QLabel(f'{idx}')
                num.setFixedSize(22, 22)
                num.setAlignment(Qt.AlignCenter)
                num.setStyleSheet(
                    f"background: {prio_color}; color: white; font-size: 11px; "
                    f"font-weight: {Fonts.WEIGHT_BOLD}; border-radius: 11px; "
                    f"font-family: {Fonts.FAMILY_CN};"
                )
                icon_lbl = QLabel(prio_icon)
                icon_lbl.setFixedSize(20, 20)
                icon_lbl.setStyleSheet(f"font-size: 14px;")
                title_lbl = QLabel(parts.get('main', cleaned))
                title_lbl.setWordWrap(True)
                title_lbl.setStyleSheet(
                    f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; "
                    f"font-weight: {Fonts.W_MEDIUM}; font-family: {Fonts.BODY}; "
                    f"line-height: 1.6;"
                )
                head.addWidget(num)
                head.addWidget(icon_lbl)
                head.addWidget(title_lbl, 1)
                rl.addLayout(head)

                # 细节：时机 / 规避 / 补充说明
                detail_texts = []
                if parts.get('timing'):
                    detail_texts.append(f"⏰ 时机：{parts['timing']}")
                if parts.get('avoid'):
                    detail_texts.append(f"⚠ 规避：{parts['avoid']}")
                if parts.get('extra'):
                    detail_texts.append(parts['extra'])

                for dt in detail_texts:
                    dl = QLabel(dt)
                    dl.setWordWrap(True)
                    is_risk = any(kw in dt for kw in _RISK_KW)
                    dl.setStyleSheet(
                        f"font-size: {Fonts.SZ_SMALL}; "
                        f"color: {Colors.DANGER if is_risk else Colors.TEXT2}; "
                        f"font-family: {Fonts.BODY}; line-height: 1.55; "
                        f"padding-left: 30px;"
                    )
                    rl.addWidget(dl)

                # 优先级徽章
                badge = QLabel(f"优先级：{prio_label}")
                badge.setStyleSheet(
                    f"font-size: {Fonts.SZ_SMALL}; color: {prio_color}; "
                    f"font-weight: {Fonts.W_MEDIUM}; font-family: {Fonts.BODY}; "
                    f"padding-left: 30px;"
                )
                rl.addWidget(badge)

                section_layout.addWidget(row)

            card = CollapsibleCard(title, icon, accent_color=color, collapsed=False)
            card.set_content(section_widget)
            return card

        def _split_advice_parts(text: str) -> dict:
            """将单条建议按关键词拆分为 main / timing / avoid / extra。"""
            import re as _re
            result = {'main': text, 'timing': '', 'avoid': '', 'extra': ''}
            # 时机：含「时机」「应期」「在…时」「…前后」
            m = _re.search(r'[时机应期].{0,20}?[。；;]', text)
            if m:
                result['timing'] = m.group(0).strip('。；; ')
                result['main'] = text[:m.start()].strip()
                text = text[m.end():].strip()
            # 规避：含「避免」「忌讳」「不宜」「切勿」
            m = _re.search(r'(?:避免|忌讳|不宜|切勿|小心|防)[^。]{0,30}?[。；;]', text)
            if m:
                result['avoid'] = m.group(0).strip('。；; ')
            return result

        # 没有任何 智能 内容的兜底提示（缩进与上方同级）
        if not has_content:
            tip = QLabel('龙虎山大师兄未返回有效条目，请点击「重新解读」重试')
            tip.setStyleSheet(
                f"color:{Colors.TEXT3}; font-size:{Fonts.SIZE_BODY}; "
                f"font-family:{Fonts.FAMILY_CN}; padding:30px 20px;"
            )
            tip.setAlignment(Qt.AlignCenter)
            tip.setWordWrap(True)
            cv.addWidget(tip)

        # 3) 构造 智能 结果容器（金色分隔标题 + 各子项折叠卡片）
        smart_card = container

        # 4) 兼容两种插入位置：占位符存在则替换占位符，否则插入到 stretch 之前
        placeholder = self.content_widget.findChild(QFrame, 'smart_result_placeholder')
        inserted = False
        if placeholder is not None:
            placeholder_idx = None
            for i in range(self.content_layout.count()):
                item = self.content_layout.itemAt(i)
                if item and item.widget() and item.widget() == placeholder:
                    placeholder_idx = i
                    break
            if placeholder_idx is not None:
                self.content_layout.insertWidget(placeholder_idx, smart_card)
                placeholder.setParent(None)
                placeholder.deleteLater()
                inserted = True
        if not inserted:
            # 寻找 stretch 位置插入
            stretch_idx = -1
            for i in range(self.content_layout.count()):
                item = self.content_layout.itemAt(i)
                if item and item.spacerItem():
                    stretch_idx = i
                    break
            if stretch_idx >= 0:
                self.content_layout.insertWidget(stretch_idx, smart_card)
            else:
                self.content_layout.addWidget(smart_card)

        # 5) 更新状态栏与 智能 按钮
        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(90, 143, 110, 0.08);
                border: 1px solid {Colors.SUCCESS};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        self.status_label.setText('✓ 龙虎山大师兄解读完成')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.SUCCESS};
            font-family: {Fonts.FAMILY_CN};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)

        self.smart_analyze_btn.setVisible(True)
        self.smart_analyze_btn.setEnabled(True)
        self.smart_analyze_btn.setText('🔄 重新解读')

        # 6) 滚动到 智能 区域
        QTimer.singleShot(50, self._scroll_to_section_meihua)

    # ----------------- 辅助方法：智能 面板相关 -----------------

    def _show_error(self, message: str):
        """智能 失败/数据异常时的兜底显示（梅花易数版）"""
        try:
            # 重新构建原始面板
            rd = getattr(self, '_current_result', {}) or {}
            self.display_result(rd)
        except Exception:
            pass

        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(196, 92, 72, 0.08);
                border: 1px solid {Colors.DANGER};
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
        self.smart_analyze_btn.setVisible(True)
        self.smart_analyze_btn.setEnabled(True)
        self.smart_analyze_btn.setText('🔄 重新解读')
        tip = QLabel(f'⚠ {message}')
        tip.setStyleSheet(
            f"color:{Colors.TEXT2}; font-size:{Fonts.SIZE_BODY}; "
            f"font-family:{Fonts.FAMILY_CN}; padding:60px 20px;"
        )
        tip.setAlignment(Qt.AlignCenter)
        tip.setWordWrap(True)
        self.content_layout.addWidget(tip)

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
        智能 = getattr(self, '_current_ai', None)
        if 智能 and isinstance(ai, dict):
            export_data['meihua_ai'] = ai

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
