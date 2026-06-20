"""
梅花易数起卦输入面板
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QComboBox, QTextEdit, QButtonGroup,
                             QScrollArea, QGridLayout, QSpinBox)
from PySide6.QtCore import Qt
from ui.styles import Stylesheets, Colors, Fonts, Spacing


DIVINATION_METHODS = [
    ('time', '时间起卦', '根据当前时间起卦'),
    ('number', '数字起卦', '输入两个数字起卦'),
    ('direction', '方位起卦', '根据方位起卦'),
    ('text', '文字起卦', '根据汉字笔画起卦'),
]


class MeihuaInputPanel(QWidget):
    """梅花易数起卦输入面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(Stylesheets.LEFT_PANEL)
        self.setMinimumWidth(380)
        self.setMaximumWidth(520)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(Stylesheets.SCROLL_AREA)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        card_padding = int(Spacing.CARD_PADDING.replace('px', ''))
        module_gap = int(Spacing.MODULE_GAP.replace('px', ''))
        scroll_layout.setContentsMargins(card_padding, card_padding, card_padding, card_padding)
        scroll_layout.setSpacing(module_gap)

        # 标题区域
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        title_icon = QLabel('🔮')
        title_icon.setStyleSheet(f"font-size: 22px;")
        title_label = QLabel('梅花易数起卦')
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_TITLE};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_SERIF};
            letter-spacing: 2px;
        """)
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        scroll_layout.addLayout(title_layout)

        # 鎏金分割线
        gold_divider = QFrame()
        gold_divider.setFixedHeight(2)
        gold_divider.setStyleSheet(Stylesheets.GOLD_DIVIDER)
        scroll_layout.addWidget(gold_divider)

        # 起卦方式选择
        method_section = self._create_section_card('起卦方式', self._create_method_content())
        scroll_layout.addWidget(method_section)

        # 起卦参数（动态内容）
        self.params_section = self._create_section_card('起卦参数', self._create_time_params())
        scroll_layout.addWidget(self.params_section)

        # 占问事项
        question_section = self._create_section_card('占问事项（可选）', self._create_question_content())
        scroll_layout.addWidget(question_section)

        scroll_layout.addStretch(1)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)

        # 底部按钮
        bottom_widget = QWidget()
        bottom_widget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 transparent, stop:0.3 {Colors.CARD});
                border-top: 1px solid {Colors.BORDER_LIGHT};
            }}
        """)
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(card_padding, 12, card_padding, 12)
        bottom_layout.setSpacing(10)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(14)
        button_layout.setAlignment(Qt.AlignCenter)

        self.reset_btn = QPushButton('重置')
        self.reset_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)
        self.reset_btn.setCursor(Qt.PointingHandCursor)

        self.submit_btn = QPushButton('起卦')
        self.submit_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        self.submit_btn.setCursor(Qt.PointingHandCursor)

        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.submit_btn)

        bottom_layout.addLayout(button_layout)
        main_layout.addWidget(bottom_widget)

        self.selected_method = 'time'

    def _create_section_card(self, title, content_widget):
        card = QFrame()
        card.setStyleSheet(Stylesheets.SECTION_CARD)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        color_bar = QFrame()
        color_bar.setFixedWidth(4)
        color_bar.setFixedHeight(16)
        color_bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.HIGHLIGHT}, stop:1 {Colors.HIGHLIGHT_LIGHT});
            border-radius: 2px;
        """)
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SECTION};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        header.addWidget(color_bar)
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)
        layout.addWidget(content_widget)
        return card

    def _create_method_content(self):
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        self.method_buttons = []
        self.method_group = QButtonGroup(self)
        self.method_group.setExclusive(True)

        for i, (value, name, desc) in enumerate(DIVINATION_METHODS):
            btn = QPushButton(name)
            btn.setStyleSheet(Stylesheets.PAN_TYPE_CARD)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty('method', value)
            btn.setMinimumHeight(60)
            self.method_group.addButton(btn, i)
            layout.addWidget(btn, i // 2, i % 2)
            self.method_buttons.append(btn)
            btn.clicked.connect(lambda checked, idx=i: self._on_method_changed(idx))

        self.method_buttons[0].setChecked(True)
        return widget

    def _create_time_params(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        hint = QLabel('使用当前系统时间起卦，也可手动指定时间')
        hint.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        time_row = QHBoxLayout()
        time_label = QLabel('指定时间:')
        time_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        self.time_edit = QLineEdit()
        self.time_edit.setStyleSheet(Stylesheets.LINE_EDIT)
        self.time_edit.setPlaceholderText('留空则使用当前时间')
        time_row.addWidget(time_label)
        time_row.addWidget(self.time_edit, 1)
        layout.addLayout(time_row)

        return widget

    def _create_number_params(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        hint = QLabel('输入两个数字，第一个数为上卦，第二个数为下卦')
        hint.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        num_row = QHBoxLayout()
        num_row.setSpacing(10)

        num1_layout = QVBoxLayout()
        num1_label = QLabel('第一个数:')
        num1_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        self.num1_spin = QSpinBox()
        self.num1_spin.setStyleSheet(Stylesheets.LINE_EDIT)
        self.num1_spin.setRange(1, 999)
        self.num1_spin.setValue(3)
        num1_layout.addWidget(num1_label)
        num1_layout.addWidget(self.num1_spin)

        num2_layout = QVBoxLayout()
        num2_label = QLabel('第二个数:')
        num2_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        self.num2_spin = QSpinBox()
        self.num2_spin.setStyleSheet(Stylesheets.LINE_EDIT)
        self.num2_spin.setRange(1, 999)
        self.num2_spin.setValue(5)
        num2_layout.addWidget(num2_label)
        num2_layout.addWidget(self.num2_spin)

        num_row.addLayout(num1_layout)
        num_row.addLayout(num2_layout)
        layout.addLayout(num_row)

        return widget

    def _create_direction_params(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        hint = QLabel('选择方位起卦，方位对应后天八卦')
        hint.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        dir_layout = QHBoxLayout()
        dir_label = QLabel('方位:')
        dir_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        self.direction_combo = QComboBox()
        self.direction_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        directions = ['正北方', '东北方', '正东方', '东南方',
                      '正南方', '西南方', '正西方', '西北方']
        for d in directions:
            self.direction_combo.addItem(d)
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.direction_combo, 1)
        layout.addLayout(dir_layout)

        return widget

    def _create_text_params(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        hint = QLabel('输入汉字，按笔画数起卦')
        hint.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        text_label = QLabel('输入文字:')
        text_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        self.text_edit = QLineEdit()
        self.text_edit.setStyleSheet(Stylesheets.LINE_EDIT)
        self.text_edit.setPlaceholderText('请输入汉字')
        self.text_edit.setText('梅花易数')
        layout.addWidget(text_label)
        layout.addWidget(self.text_edit)

        return widget

    def _create_question_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.question_edit = QTextEdit()
        self.question_edit.setStyleSheet(Stylesheets.TEXT_EDIT)
        self.question_edit.setPlaceholderText('请输入您想占问的事情，如：事业发展、感情姻缘、财运如何...')
        self.question_edit.setMaximumHeight(100)
        layout.addWidget(self.question_edit)

        return widget

    def _on_method_changed(self, index):
        """起卦方式切换"""
        method = DIVINATION_METHODS[index][0]
        self.selected_method = method

        # 更新参数区域
        old_content = self.params_section.layout().itemAt(1).widget()
        if old_content:
            old_content.setParent(None)
            old_content.deleteLater()

        if method == 'time':
            new_content = self._create_time_params()
        elif method == 'number':
            new_content = self._create_number_params()
        elif method == 'direction':
            new_content = self._create_direction_params()
        else:
            new_content = self._create_text_params()

        self.params_section.layout().addWidget(new_content)

    def get_data(self):
        """获取起卦参数"""
        data = {
            'method': self.selected_method,
            'question': self.question_edit.toPlainText().strip(),
        }

        if self.selected_method == 'number':
            data['num1'] = self.num1_spin.value()
            data['num2'] = self.num2_spin.value()
        elif self.selected_method == 'direction':
            data['direction'] = self.direction_combo.currentText()
        elif self.selected_method == 'text':
            data['text'] = self.text_edit.text().strip()
        elif self.selected_method == 'time':
            data['time_str'] = self.time_edit.text().strip()

        return data

    def clear(self):
        """重置输入"""
        self.method_buttons[0].setChecked(True)
        self._on_method_changed(0)
        self.question_edit.clear