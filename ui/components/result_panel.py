from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
                             QScrollArea, QSizePolicy, QSpacerItem, QProgressBar)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PySide6.QtGui import QFont
from ui.styles import Stylesheets, Colors, Fonts, Spacing


class ResultPanel(QWidget):
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

        # ===== 顶部标题栏 =====
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title_icon = QLabel('☯')
        title_icon.setStyleSheet(f"font-size: 22px; color: {Colors.PRIMARY};")

        self.title_label = QLabel('排盘结果展示')
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

        # 结果操作按钮（默认隐藏）
        self.result_actions = QWidget()
        actions_layout = QHBoxLayout(self.result_actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        self.refresh_btn = QPushButton('⟳ 刷新')
        self.refresh_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setVisible(False)

        self.copy_btn = QPushButton('📋 复制')
        self.copy_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setVisible(False)

        self.save_btn = QPushButton('💾 保存')
        self.save_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setVisible(False)

        self.export_btn = QPushButton('📤 导出')
        self.export_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setVisible(False)

        actions_layout.addWidget(self.refresh_btn)
        actions_layout.addWidget(self.copy_btn)
        actions_layout.addWidget(self.save_btn)
        actions_layout.addWidget(self.export_btn)

        header_layout.addWidget(self.result_actions)

        main_layout.addLayout(header_layout)

        # ===== 状态栏 =====
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

        self.status_label = QLabel('ℹ 请完善左侧参数，点击「开始排盘」获取专业风水分析')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        status_layout.addWidget(self.status_label)

        main_layout.addWidget(self.status_bar)

        # ===== 内容区域 =====
        self.content_area = QScrollArea()
        self.content_area.setStyleSheet(Stylesheets.SCROLL_AREA)
        self.content_area.setWidgetResizable(True)
        self.content_area.setFrameShape(QFrame.NoFrame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)

        # 空状态
        self.empty_state = self._create_empty_state()
        self.content_layout.addWidget(self.empty_state)

        self.content_area.setWidget(self.content_widget)
        main_layout.addWidget(self.content_area)

        self.setLayout(main_layout)

    def _create_empty_state(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        icon = QLabel('☯')
        icon.setStyleSheet(f"""
            font-size: 64px;
            color: {Colors.BORDER};
            opacity: 0.5;
        """)
        icon.setAlignment(Qt.AlignCenter)

        title = QLabel('请完善左侧参数')
        title.setStyleSheet(f"""
            font-size: 18px;
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel('点击「开始排盘」获取专业风水分析')
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

        # 卡片标题
        header = QHBoxLayout()
        header.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            font-size: 20px;
            color: {Colors.PRIMARY};
        """)

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

        # 分割线
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT};")

        layout.addLayout(header)
        layout.addWidget(divider)
        layout.addWidget(content_widget)

        return card

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

            layout.addWidget(label_widget, i // 2, (i % 2) * 2)
            layout.addWidget(value_widget, i // 2, (i % 2) * 2 + 1)

        return widget

    def _create_bazi_grid(self, bazi_data):
        """创建天干地支展示"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        pillars = [
            ('年柱', bazi_data['year_pillar']),
            ('月柱', bazi_data['month_pillar']),
            ('日柱', bazi_data['day_pillar']),
            ('时柱', bazi_data['hour_pillar']),
        ]

        for label, pillar in pillars:
            pillar_widget = QFrame()
            is_day = label == '日柱'
            pillar_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND};
                    border-radius: {Spacing.CONTROL_RADIUS};
                    padding: 12px;
                }}
                QFrame:hover {{
                    background-color: {Colors.HOVER_BG};
                }}
            """)

            p_layout = QVBoxLayout(pillar_widget)
            p_layout.setContentsMargins(12, 10, 12, 10)
            p_layout.setSpacing(6)
            p_layout.setAlignment(Qt.AlignCenter)

            label_widget = QLabel(label)
            label_widget.setStyleSheet(f"""
                font-size: {Fonts.SIZE_SMALL};
                color: {Colors.TEXT_TERTIARY};
                font-family: {Fonts.FAMILY_CN};
            """)
            label_widget.setAlignment(Qt.AlignCenter)

            gan_widget = QLabel(pillar[0])
            gan_widget.setStyleSheet(f"""
                font-size: 24px;
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.ACCENT if is_day else Colors.PRIMARY};
                font-family: {Fonts.FAMILY_CN};
            """)
            gan_widget.setAlignment(Qt.AlignCenter)

            zhi_widget = QLabel(pillar[1])
            zhi_widget.setStyleSheet(f"""
                font-size: 24px;
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.ACCENT if is_day else Colors.PRIMARY};
                font-family: {Fonts.FAMILY_CN};
            """)
            zhi_widget.setAlignment(Qt.AlignCenter)

            p_layout.addWidget(label_widget)
            p_layout.addWidget(gan_widget)
            p_layout.addWidget(zhi_widget)

            layout.addWidget(pillar_widget)

        return widget

    def _create_wuxing_bars(self, wuxing_data):
        """创建五行进度条"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        elements = [
            ('金', wuxing_data.get('金', 0), '#C0C0C0', '#E8E8E8'),
            ('木', wuxing_data.get('木', 0), '#4A7C59', '#6BA37A'),
            ('水', wuxing_data.get('水', 0), '#2E5C8A', '#4A7FB5'),
            ('火', wuxing_data.get('火', 0), '#C45C48', '#D97B6A'),
            ('土', wuxing_data.get('土', 0), '#8B7355', '#A68B6B'),
        ]

        for name, value, color1, color2 in elements:
            row = QHBoxLayout()
            row.setSpacing(12)

            name_label = QLabel(name)
            name_label.setFixedWidth(30)
            name_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_SECONDARY};
                font-weight: {Fonts.WEIGHT_BOLD};
                font-family: {Fonts.FAMILY_CN};
            """)
            name_label.setAlignment(Qt.AlignCenter)

            bar = QProgressBar()
            bar.setValue(value)
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 5px;
                    background-color: {Colors.BACKGROUND};
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {color1}, stop:1 {color2});
                    border-radius: 5px;
                }}
            """)

            value_label = QLabel(str(value))
            value_label.setFixedWidth(24)
            value_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_SMALL};
                color: {Colors.TEXT_SECONDARY};
                font-family: {Fonts.FAMILY_CN};
            """)
            value_label.setAlignment(Qt.AlignRight)

            row.addWidget(name_label)
            row.addWidget(bar, 1)
            row.addWidget(value_label)

            layout.addLayout(row)

        return widget

    def _create_analysis_list(self, analysis_data):
        """创建吉凶批注列表"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        for item in analysis_data:
            item_widget = QFrame()
            item_type = item.get('type', '中')
            badge_color = Colors.SUCCESS if item_type == '吉' else (Colors.DANGER if item_type == '凶' else Colors.WARNING)

            item_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BACKGROUND};
                    border-radius: {Spacing.CONTROL_RADIUS};
                    padding: 10px;
                }}
                QFrame:hover {{
                    background-color: {Colors.HOVER_BG};
                }}
            """)

            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(12, 8, 12, 8)
            item_layout.setSpacing(12)

            badge = QLabel(item_type)
            badge.setFixedSize(28, 28)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(f"""
                background-color: {badge_color};
                color: white;
                font-size: 12px;
                font-weight: {Fonts.WEIGHT_BOLD};
                border-radius: 4px;
                font-family: {Fonts.FAMILY_CN};
            """)

            text = QLabel(item.get('text', ''))
            text.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_SECONDARY};
                font-family: {Fonts.FAMILY_CN};
                line-height: 1.5;
            """)
            text.setWordWrap(True)

            item_layout.addWidget(badge)
            item_layout.addWidget(text, 1)

            layout.addWidget(item_widget)

        return widget

    def display_result(self, result_data):
        """显示排盘结果"""
        # 清除旧内容
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 显示操作按钮
        self.refresh_btn.setVisible(True)
        self.copy_btn.setVisible(True)
        self.save_btn.setVisible(True)
        self.export_btn.setVisible(True)

        # 更新状态栏
        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(90, 143, 110, 0.08);
                border: 1px solid {Colors.SUCCESS};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        self.status_label.setText('✓ 排盘完成')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.SUCCESS};
            font-family: {Fonts.FAMILY_CN};
            font-weight: {Fonts.WEIGHT_BOLD};
        """)

        # 基础命盘信息卡片
        basic_info = result_data.get('basic_info', {})
        info_data = [
            ('排盘类型', basic_info.get('pan_type', '八字排盘')),
            ('公历日期', basic_info.get('solar_date', '-')),
            ('农历日期', basic_info.get('lunar_date', '-')),
            ('出生时辰', basic_info.get('hour', '-')),
            ('出生地点', basic_info.get('location', '-')),
            ('性别', basic_info.get('gender', '男')),
        ]
        info_widget = self._create_info_grid(info_data)
        info_card = self._create_result_card('基础命盘信息', 'ℹ', info_widget)
        self.content_layout.addWidget(info_card)

        # 天干地支卡片
        bazi_data = result_data.get('bazi', {})
        if bazi_data:
            bazi_widget = self._create_bazi_grid(bazi_data)
            bazi_card = self._create_result_card('天干地支', '★', bazi_widget, highlight=True)
            self.content_layout.addWidget(bazi_card)

        # 五行分析卡片
        wuxing_data = result_data.get('wuxing', {})
        if wuxing_data:
            wuxing_widget = self._create_wuxing_bars(wuxing_data)
            wuxing_card = self._create_result_card('五行分析', '◆', wuxing_widget)
            self.content_layout.addWidget(wuxing_card)

        # 吉凶批注卡片
        analysis_data = result_data.get('analysis', [])
        if analysis_data:
            analysis_widget = self._create_analysis_list(analysis_data)
            analysis_card = self._create_result_card('吉凶批注', '⚖', analysis_widget, highlight=True)
            self.content_layout.addWidget(analysis_card)

        self.content_layout.addStretch()

    def show_loading(self):
        """显示加载状态"""
        # 更新状态栏
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
        self.status_label.setText('⏳ 正在精准排盘，请稍候...')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        # 隐藏操作按钮
        self.refresh_btn.setVisible(False)
        self.copy_btn.setVisible(False)
        self.save_btn.setVisible(False)
        self.export_btn.setVisible(False)

        # 清除内容，显示加载动画
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

        # 太极图标（用Unicode代替）
        taiji = QLabel('☯')
        taiji.setStyleSheet(f"""
            font-size: 80px;
            color: {Colors.PRIMARY};
        """)
        taiji.setAlignment(Qt.AlignCenter)

        # 添加旋转动画
        self.taiji_animation = QPropertyAnimation(taiji, b"rotation")
        self.taiji_animation.setDuration(3000)
        self.taiji_animation.setStartValue(0)
        self.taiji_animation.setEndValue(360)
        self.taiji_animation.setEasingCurve(QEasingCurve.Linear)
        self.taiji_animation.setLoopCount(-1)
        self.taiji_animation.start()

        text = QLabel('正在精准排盘，请稍候...')
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

    def clear(self):
        """清空结果"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.empty_state = self._create_empty_state()
        self.content_layout.addWidget(self.empty_state)

        # 重置状态栏
        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        self.status_label.setText('ℹ 请完善左侧参数，点击「开始排盘」获取专业风水分析')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        # 隐藏操作按钮
        self.refresh_btn.setVisible(False)
        self.copy_btn.setVisible(False)
        self.save_btn.setVisible(False)
        self.export_btn.setVisible(False)
