"""
梅花易数起卦结果展示面板
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QScrollArea, QPushButton, QGridLayout)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from ui.styles import Stylesheets, Colors, Fonts, Spacing


class MeihuaResultPanel(QWidget):
    """梅花易数结果展示面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
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

        self.ai_analyze_btn = QPushButton('🤖 AI解读')
        self.ai_analyze_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        self.ai_analyze_btn.setCursor(Qt.PointingHandCursor)
        self.ai_analyze_btn.setVisible(False)
        header_layout.addWidget(self.ai_analyze_btn)

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
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)

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
        """创建结果卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CARD_RADIUS};
            }}
            QFrame:hover {{
                border-color: {Colors.HIGHLIGHT};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 20px; color: {Colors.PRIMARY};")

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SECTION};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        header.addWidget(icon_label)
        header.addWidget(title_label)
        header.addStretch()

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT};")

        layout.addLayout(header)
        layout.addWidget(divider)
        layout.addWidget(content_widget)

        return card

    def _create_hexagram_display(self, hexagram_info, hex_type='本卦'):
        """创建卦象展示组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        name = hexagram_info.get('name', '')
        symbol = hexagram_info.get('symbol', '')
        judgment = hexagram_info.get('judgment', '')
        explanation = hexagram_info.get('explanation', '')
        upper_gua = hexagram_info.get('upper_gua', '')
        lower_gua = hexagram_info.get('lower_gua', '')

        header_row = QHBoxLayout()
        header_row.setSpacing(20)
        header_row.setAlignment(Qt.AlignCenter)

        type_label = QLabel(hex_type)
        type_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-weight: {Fonts.WEIGHT_BOLD};
            font-family: {Fonts.FAMILY_CN};
            padding: 4px 12px;
            background-color: {Colors.HIGHLIGHT_GLOW};
            border-radius: 4px;
        """)

        name_label = QLabel(f'{name} {symbol}')
        name_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.ACCENT};
            font-family: {Fonts.FAMILY_SERIF};
            letter-spacing: 2px;
        """)

        header_row.addWidget(type_label)
        header_row.addWidget(name_label)
        header_row.addStretch()
        layout.addLayout(header_row)

        gua_info = QLabel(f'上卦：{upper_gua}　下卦：{lower_gua}')
        gua_info.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        layout.addWidget(gua_info)

        if judgment:
            judgment_label = QLabel(f'【卦辞】{judgment}')
            judgment_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.PRIMARY};
                font-family: {Fonts.FAMILY_SERIF};
                font-weight: {Fonts.WEIGHT_BOLD};
                padding: 8px 12px;
                background-color: {Colors.BACKGROUND};
                border-radius: {Spacing.CONTROL_RADIUS};
            """)
            judgment_label.setWordWrap(True)
            layout.addWidget(judgment_label)

        if explanation:
            explanation_label = QLabel(explanation)
            explanation_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_SECONDARY};
                font-family: {Fonts.FAMILY_CN};
                line-height: 1.6;
            """)
            explanation_label.setWordWrap(True)
            layout.addWidget(explanation_label)

        return widget

    def _create_yao_display(self, yao_info_list):
        """创建爻辞展示"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        for yao in yao_info_list:
            yao_widget = QFrame()
            yao_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND};
                    border-radius: {Spacing.CONTROL_RADIUS};
                    padding: 10px;
                }}
            """)

            yao_layout = QVBoxLayout(yao_widget)
            yao_layout.setContentsMargins(12, 8, 12, 8)
            yao_layout.setSpacing(4)

            name = yao.get('name', '')
            text = yao.get('text', '')
            explanation = yao.get('explanation', '')
            is_moving = yao.get('is_moving', False)

            name_label = QLabel(f'{"● " if is_moving else ""}{name}')
            name_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.ACCENT if is_moving else Colors.PRIMARY};
                font-family: {Fonts.FAMILY_SERIF};
            """)

            text_label = QLabel(text)
            text_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_PRIMARY};
                font-family: {Fonts.FAMILY_CN};
            """)
            text_label.setWordWrap(True)

            if explanation:
                exp_label = QLabel(f'释义：{explanation}')
                exp_label.setStyleSheet(f"""
                    font-size: {Fonts.SIZE_SMALL};
                    color: {Colors.TEXT_TERTIARY};
                    font-family: {Fonts.FAMILY_CN};
                """)
                exp_label.setWordWrap(True)
                yao_layout.addWidget(exp_label)

            yao_layout.insertWidget(0, text_label)
            yao_layout.insertWidget(0, name_label)
            layout.addWidget(yao_widget)

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
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_SECONDARY};
                font-family: {Fonts.FAMILY_CN};
                line-height: 1.6;
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
                color: {Colors.TEXT_SECONDARY};
                font-family: {Fonts.FAMILY_CN};
                line-height: 1.5;
            """)
            text.setWordWrap(True)

            sug_layout.addWidget(num_badge)
            sug_layout.addWidget(text, 1)
            layout.addWidget(sug_widget)

        return widget

    def display_result(self, result_data):
        """显示起卦结果"""
        self._current_result = result_data
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.ai_analyze_btn.setVisible(True)

        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(90, 143, 110, 0.08);
                border: 1px solid {Colors.SUCCESS};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        self.status_label.setText('✓ 起卦完成')
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
                method_names = {'time': '时间起卦', 'number': '数字起卦', 'direction': '方位起卦', 'text': '文字起卦'}
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

        suggestions = result_data.get('suggestions', [])
        if suggestions:
            sug_widget = self._create_suggestions(suggestions)
            sug_card = self._create_result_card('行动建议', '💡', sug_widget)
            self.content_layout.addWidget(sug_card)

        ai_placeholder = QFrame()
        ai_placeholder.setVisible(False)
        ai_placeholder.setObjectName('ai_result_placeholder')
        self.content_layout.addWidget(ai_placeholder)

        self.content_layout.addStretch()

    def _create_info_grid(self, data):
        """创建信息网格"""
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setColumnStretch(1, 1)

        for i, (label, value) in enumerate(data):
            label_widget = QLabel(label)
            label_widget.setStyleSheet(f"""
                font-size: {Fonts.SIZE_SMALL};
                color: {Colors.TEXT_TERTIARY};
                font-family: {Fonts.FAMILY_CN};
            """)

            value_widget = QLabel(str(value))
            value_widget.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_PRIMARY};
                font-weight: {Fonts.WEIGHT_BOLD};
                font-family: {Fonts.FAMILY_CN};
            """)
            value_widget.setWordWrap(True)

            layout.addWidget(label_widget, i, 0)
            layout.addWidget(value_widget, i, 1)

        return widget

    def show_loading(self):
        """显示加载状态"""
        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.CARD}, stop:0.5 {Colors.HIGHLIGHT_GLOW}, stop:1 {Colors.CARD});
                background-size: 200% 100%;
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

        self.ai_analyze_btn.setVisible(False)

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

        taiji = QLabel('☯')
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

    def display_ai_analysis(self, ai_result):
        """显示AI分析结果"""
        placeholder = self.content_widget.findChild(QFrame, 'ai_result_placeholder')
        if not placeholder:
            return

        ai_widget = QWidget()
        ai_layout = QVBoxLayout(ai_widget)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        ai_layout.setSpacing(10)

        sections = [
            ('overview', '📋 卦象概览'),
            ('situation', '🌟 情势分析'),
            ('auspicious', '🍀 吉祥机遇'),
            ('inauspicious', '⚠️ 凶险隐患'),
            ('advice', '💡 行动建议'),
            ('summary', '🎯 总结判断'),
        ]

        for key, title in sections:
            content = ai_result.get(key, '')
            if not content:
                continue

            section_widget = QFrame()
            section_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND};
                    border-radius: {Spacing.CONTROL_RADIUS};
                    padding: 12px;
                }}
            """)

            section_layout = QVBoxLayout(section_widget)
            section_layout.setContentsMargins(12, 8, 12, 8)
            section_layout.setSpacing(8)

            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.PRIMARY};
                font-family: {Fonts.FAMILY_CN};
            """)

            content_label = QLabel(content)
            content_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_SECONDARY};
                font-family: {Fonts.FAMILY_CN};
                line-height: 1.7;
            """)
            content_label.setWordWrap(True)

            section_layout.addWidget(title_label)
            section_layout.addWidget(content_label)
            ai_layout.addWidget(section_widget)

        ai_card = self._create_result_card('🤖 AI智能解读', '🤖', ai_widget, highlight=True)

        placeholder_idx = None
        for i in range(self.content_layout.count()):
            item = self.content_layout.itemAt(i)
            if item.widget() and item.widget() == placeholder:
                placeholder_idx = i
                break

        if placeholder_idx is not None:
            self.content_layout.insertWidget(placeholder_idx, ai_card)
            placeholder.setParent(None)
            placeholder.deleteLater()

    def show_ai_loading(self, message: str = 'AI正在解读卦象玄机…'):
        """显示AI分析加载状态"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.ai_analyze_btn.setVisible(False)
        self.ai_analyze_btn.setEnabled(False)

        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(196, 154, 60, 0.08);
                border: 1px solid {Colors.HIGHLIGHT};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        self.status_label.setText('🤖 AI解读中…')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.HIGHLIGHT};
            font-family: {Fonts.FAMILY_CN};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)

        loading_widget = self._create_ai_loading_widget(message)
        self.content_layout.addWidget(loading_widget)
        self.content_layout.addStretch()

    def _create_ai_loading_widget(self, message: str) -> QWidget:
        """创建AI分析加载控件"""
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

        sub_label = QLabel('请稍候，AI正在结合卦辞爻辞进行深度解读')
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

    def display_ai_analysis_result(self, ai_data: dict):
        """显示AI分析结果（适配analysis_pipeline输出格式）

        关键修复：
        1) 不再完全依赖 placeholder 机制（display_result 创建的占位 QFrame），
           改为兼容两种情况：placeholder 存在 / 已被消费。
        2) 防御性处理：AI 返回为空、字段类型异常时给出兜底提示，避免右侧空白。
        3) 完成后滚动到 AI 区域，让用户第一眼看到 AI 解读内容。
        """
        # 0) 防御性检查
        if not ai_data or not isinstance(ai_data, dict):
            self._show_ai_error('AI 未返回有效内容，请重试')
            return

        rd = getattr(self, '_current_result', {}) or {}

        # 1) 先恢复原始面板（不重建占位）
        self.display_result(rd)

        sections = [
            ('gua_overview', '卦象概述', '📋', Colors.PRIMARY),
            ('situation_analysis', '事态分析', '🌟', Colors.HIGHLIGHT),
            ('good_omens', '吉兆机遇', '🍀', Colors.SUCCESS),
            ('bad_omens', '凶兆隐患', '⚠️', Colors.DANGER),
            ('action_advice', '行动建议', '💡', Colors.PRIMARY),
        ]

        # 2) 构建 AI 内容容器
        ai_widget = QWidget()
        ai_layout = QVBoxLayout(ai_widget)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        ai_layout.setSpacing(10)

        has_ai_content = False
        for key, title, icon, color in sections:
            items = ai_data.get(key, []) or []
            if not items:
                continue
            has_ai_content = True

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

            title_label = QLabel(f'{icon} {title}')
            title_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {color};
                font-family: {Fonts.FAMILY_CN};
            """)
            section_layout.addWidget(title_label)

            for idx, item in enumerate(items):
                item_layout = QHBoxLayout()
                item_layout.setSpacing(10)

                num_label = QLabel(f'{idx+1}')
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

            ai_layout.addWidget(section_widget)

        final_verdict = ai_data.get('final_verdict', '')
        if final_verdict:
            has_ai_content = True
            verdict_widget = QFrame()
            verdict_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(91, 143, 168, 0.08);
                    border: 1px solid {Colors.PRIMARY_LIGHT};
                    border-radius: {Spacing.CONTROL_RADIUS};
                }}
            """)
            verdict_layout = QVBoxLayout(verdict_widget)
            verdict_layout.setContentsMargins(16, 12, 16, 12)
            verdict_layout.setSpacing(6)

            verdict_title = QLabel('🎯 总结判断')
            verdict_title.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.PRIMARY};
                font-family: {Fonts.FAMILY_CN};
            """)

            verdict_text = QLabel(str(final_verdict))
            verdict_text.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_PRIMARY};
                font-family: {Fonts.FAMILY_SERIF};
                line-height: 1.8;
            """)
            verdict_text.setWordWrap(True)

            verdict_layout.addWidget(verdict_title)
            verdict_layout.addWidget(verdict_text)
            ai_layout.addWidget(verdict_widget)

        # 没有任何 AI 内容的兜底提示
        if not has_ai_content:
            tip = QLabel('AI 未返回有效条目，请点击「重新解读」重试')
            tip.setStyleSheet(
                f"color:{Colors.TEXT3}; font-size:{Fonts.SIZE_BODY}; "
                f"font-family:{Fonts.FAMILY_CN}; padding:30px 20px;"
            )
            tip.setAlignment(Qt.AlignCenter)
            tip.setWordWrap(True)
            ai_layout.addWidget(tip)

        # 3) 构造 AI 结果卡片（高亮）
        ai_card = self._create_result_card('🤖 AI智能深度解读', '🤖', ai_widget, highlight=True)

        # 4) 兼容两种插入位置：占位符存在则替换占位符，否则插入到 stretch 之前
        placeholder = self.content_widget.findChild(QFrame, 'ai_result_placeholder')
        inserted = False
        if placeholder is not None:
            placeholder_idx = None
            for i in range(self.content_layout.count()):
                item = self.content_layout.itemAt(i)
                if item and item.widget() and item.widget() == placeholder:
                    placeholder_idx = i
                    break
            if placeholder_idx is not None:
                self.content_layout.insertWidget(placeholder_idx, ai_card)
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
                self.content_layout.insertWidget(stretch_idx, ai_card)
            else:
                self.content_layout.addWidget(ai_card)

        # 5) 更新状态栏与 AI 按钮
        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(90, 143, 110, 0.08);
                border: 1px solid {Colors.SUCCESS};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        self.status_label.setText('✓ AI解读完成')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.SUCCESS};
            font-family: {Fonts.FAMILY_CN};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)

        self.ai_analyze_btn.setVisible(True)
        self.ai_analyze_btn.setEnabled(True)
        self.ai_analyze_btn.setText('🤖 重新解读')

        # 6) 滚动到 AI 区域
        QTimer.singleShot(50, self._scroll_to_ai_section_meihua)

    # ----------------- 辅助方法：AI 面板相关 -----------------

    def _show_ai_error(self, message: str):
        """AI 失败/数据异常时的兜底显示（梅花易数版）"""
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
        self.status_label.setText('⚠ AI 异常')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.DANGER};
            font-family: {Fonts.FAMILY_CN};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)
        self.ai_analyze_btn.setVisible(True)
        self.ai_analyze_btn.setEnabled(True)
        self.ai_analyze_btn.setText('🤖 重新解读')
        tip = QLabel(f'⚠ {message}')
        tip.setStyleSheet(
            f"color:{Colors.TEXT2}; font-size:{Fonts.SIZE_BODY}; "
            f"font-family:{Fonts.FAMILY_CN}; padding:60px 20px;"
        )
        tip.setAlignment(Qt.AlignCenter)
        tip.setWordWrap(True)
        self.content_layout.addWidget(tip)

    def _scroll_to_ai_section_meihua(self):
        """滚动到 AI 解读区域"""
        try:
            target = self.content_widget.findChild(QFrame, 'ai_result_placeholder')
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
        """获取用于AI分析的卦象数据"""
        rd = getattr(self, '_current_result', {})
        if not rd:
            return {}

        base = rd.get('ben_gua', {})
        hu = rd.get('hu_gua', {})
        bian = rd.get('bian_gua', {})
        overall = rd.get('overall', {})

        hexagram_data = {
            'base': {
                'name': base.get('name', ''),
                'upper_name': base.get('upper_name', ''),
                'lower_name': base.get('lower_name', ''),
                'upper_nature': base.get('upper_element', ''),
                'lower_nature': base.get('lower_element', ''),
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

        self.ai_analyze_btn.setVisible(False)
