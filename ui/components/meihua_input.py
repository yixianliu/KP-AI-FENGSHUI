"""
梅花易数起卦输入面板 - 增强版
支持8种起卦方式，每种提供丰富的输入选项
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QComboBox, QButtonGroup,
                             QSpinBox, QStackedWidget, QScrollArea, QGroupBox,
                             QRadioButton, QGridLayout)
from PySide6.QtCore import Qt
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from core.meihua import YAO_NAMES

METHODS = [
    ('time', '时间起卦'), ('number', '数字起卦'),
    ('direction', '方位起卦'), ('text', '文字起卦'),
    ('copper_coin', '铜钱摇卦'), ('stroke', '笔画起卦'),
]


class MeihuaInputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_method = 'time'
        self._build()

    def _build(self):
        self.setStyleSheet(f"background-color: {Colors.BG};")

        scroll = QScrollArea()
        scroll.setStyleSheet(Stylesheets.SCROLL)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.BG};")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        # 标题
        hdr = QHBoxLayout()
        hdr.setSpacing(8)
        icon = QLabel('⚊')
        icon.setStyleSheet(f"font-size: 14px; color: {Colors.LIUJIN};")
        title = QLabel('梅花易数参数')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT}; font-family: {Fonts.TITLE};
        """)
        hdr.addWidget(icon); hdr.addWidget(title); hdr.addStretch()
        lay.addLayout(hdr)

        div = QFrame(); div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {Colors.QINGHUA_LIGHT};")
        lay.addWidget(div)

        # 起卦方式（网格布局，避免窄屏单行被压窄/截断）
        method_lay = QVBoxLayout()
        method_lay.setSpacing(8)
        method_lay.addWidget(self._label('方式'))
        grid = QGridLayout()
        grid.setSpacing(8)
        self.method_btns = []
        self.method_grp = QButtonGroup(self)
        self.method_grp.setExclusive(True)
        for i, (v, n) in enumerate(METHODS):
            b = QPushButton(n)
            b.setStyleSheet(Stylesheets.BTN_SWITCH)
            b.setCheckable(True); b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(34)
            self.method_grp.addButton(b, i)
            r, c = divmod(i, 2)
            grid.addWidget(b, r, c)
            self.method_btns.append(b)
            b.clicked.connect(lambda _, idx=i: self._on_method(idx))
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.method_btns[0].setChecked(True)
        method_lay.addLayout(grid)
        lay.addLayout(method_lay)

        # 占问分类选择（新增）
        self.question_category = QComboBox()
        self.question_category.setStyleSheet(Stylesheets.COMBO)
        for cat in ['不限', '事业', '财运', '感情', '健康', '出行', '学业', '婚姻', '家宅', '运势']:
            self.question_category.addItem(cat)
        q_cat_row = QHBoxLayout(); q_cat_row.setSpacing(8)
        q_cat_row.addWidget(self._label('分类'))
        q_cat_row.addWidget(self.question_category, 1)
        lay.addLayout(q_cat_row)

        # 占问
        row = QHBoxLayout(); row.setSpacing(8)
        row.addWidget(self._label('占问'))
        self.question = QLineEdit()
        self.question.setStyleSheet(Stylesheets.INPUT)
        self.question.setPlaceholderText('可选，详细描述所问之事…')
        row.addWidget(self.question, 1)
        lay.addLayout(row)

        lay.addStretch()

        # 动态参数容器
        self.params = QStackedWidget()
        self.params.setStyleSheet("background: transparent;")

        # ========== 方式1: 时间起卦 ==========
        tw = QWidget(); tw.setStyleSheet("background: transparent;")
        tl = QVBoxLayout(tw); tl.setContentsMargins(0,0,0,0); tl.setSpacing(12)
        
        # 历法 + 时间输入
        cal_group = QGroupBox('时间设置')
        cal_lay = QVBoxLayout(cal_group)
        cal_lay.setContentsMargins(12, 12, 12, 12)
        cal_lay.setSpacing(10)
        
        # 历法单选：公历 / 农历
        cal_row = QHBoxLayout(); cal_row.setSpacing(16)
        cal_row.addWidget(QLabel('历法:'))
        self.calendar_btn_group = QButtonGroup(self)
        self.calendar_btn_group.setExclusive(True)
        self.cal_lunar = QRadioButton('公历')
        self.cal_lunar.setChecked(True)
        self.cal_lunar.setStyleSheet(Stylesheets.RADIO)
        self.cal_solar = QRadioButton('农历')
        self.cal_solar.setStyleSheet(Stylesheets.RADIO)
        self.calendar_btn_group.addButton(self.cal_lunar)
        self.calendar_btn_group.addButton(self.cal_solar)
        cal_row.addWidget(self.cal_lunar)
        cal_row.addWidget(self.cal_solar)
        cal_row.addStretch()
        cal_lay.addLayout(cal_row)
        
        # 时间输入
        time_row = QHBoxLayout(); time_row.setSpacing(12)
        time_row.addWidget(QLabel('时间:'))
        self.time_edit = QLineEdit()
        self.time_edit.setStyleSheet(Stylesheets.INPUT)
        self.time_edit.setPlaceholderText('留空取当前时辰 (格式: YYYY-MM-DD HH:MM)')
        time_row.addWidget(self.time_edit, 1)
        cal_lay.addLayout(time_row)
        
        tl.addWidget(cal_group)
        
        self.params.addWidget(tw)

        # ========== 方式2: 数字起卦 ==========
        nw = QWidget(); nw.setStyleSheet("background: transparent;")
        nl = QVBoxLayout(nw); nl.setContentsMargins(0,0,0,0); nl.setSpacing(12)
        
        num_group = QGroupBox('数字设置')
        num_lay = QGridLayout(num_group)
        num_lay.setSpacing(8)
        num_lay.setContentsMargins(12, 12, 12, 12)
        
        self.num1 = QSpinBox()
        self.num1.setStyleSheet(Stylesheets.INPUT)
        self.num1.setRange(1, 9999); self.num1.setValue(3)
        num_lay.addWidget(self.num1, 0, 0)
        
        self.num2 = QSpinBox()
        self.num2.setStyleSheet(Stylesheets.INPUT)
        self.num2.setRange(1, 9999); self.num2.setValue(5)
        num_lay.addWidget(self.num2, 0, 1)
        
        self.num3 = QSpinBox()
        self.num3.setStyleSheet(Stylesheets.INPUT)
        self.num3.setRange(1, 9999); self.num3.setValue(7)
        num_lay.addWidget(self.num3, 0, 2)
        
        lbl_upper = QLabel('上卦数'); lbl_upper.setAlignment(Qt.AlignCenter); lbl_upper.setStyleSheet(f"color: {Colors.TEXT2}; font-size: {Fonts.SZ_SMALL};")
        lbl_lower = QLabel('下卦数'); lbl_lower.setAlignment(Qt.AlignCenter); lbl_lower.setStyleSheet(f"color: {Colors.TEXT2}; font-size: {Fonts.SZ_SMALL};")
        lbl_yao   = QLabel('动爻数(可选)'); lbl_yao.setAlignment(Qt.AlignCenter); lbl_yao.setStyleSheet(f"color: {Colors.TEXT2}; font-size: {Fonts.SZ_SMALL};")
        num_lay.addWidget(lbl_upper, 1, 0)
        num_lay.addWidget(lbl_lower, 1, 1)
        num_lay.addWidget(lbl_yao, 1, 2)
        
        num_group.setLayout(num_lay)
        nl.addWidget(num_group)
        
        self.params.addWidget(nw)

        # ========== 方式3: 方位起卦 ==========
        dw = QWidget(); dw.setStyleSheet("background: transparent;")
        dl = QVBoxLayout(dw); dl.setContentsMargins(0,0,0,0); dl.setSpacing(12)
        
        dir_group = QGroupBox('方位选择')
        dir_lay = QGridLayout(dir_group)
        dir_lay.setSpacing(8)
        dir_lay.setContentsMargins(12, 12, 12, 12)
        
        self.dir_combo = QComboBox()
        self.dir_combo.setStyleSheet(Stylesheets.COMBO)
        for d in ['正北方','东北方','正东方','东南方','正南方','西南方','正西方','西北方']:
            self.dir_combo.addItem(d)
        dir_lay.addWidget(self.dir_combo, 0, 0, 1, 2)
        
        # 方位示意图标签
        compass_label = QLabel('🧭 先天八卦方位：\n乾西北 坎北 艮东北 震东\n巽东南 离南 坤西南 兑西')
        compass_label.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT2}; background: {Colors.QINGHUA_LIGHT}; padding: 8px; border-radius: 4px;")
        compass_label.setWordWrap(True)
        dir_lay.addWidget(compass_label, 1, 0, 1, 2)
        
        dir_group.setLayout(dir_lay)
        dl.addWidget(dir_group)
        
        self.params.addWidget(dw)

        # ========== 方式4: 文字起卦 ==========
        xw = QWidget(); xw.setStyleSheet("background: transparent;")
        xl = QVBoxLayout(xw); xl.setContentsMargins(0,0,0,0); xl.setSpacing(12)
        
        text_group = QGroupBox('文字设置')
        text_lay = QGridLayout(text_group)
        text_lay.setSpacing(8)
        text_lay.setContentsMargins(12, 12, 12, 12)
        
        self.char_mode_combo = QComboBox()
        self.char_mode_combo.addItems(['单字', '多字'])
        text_lay.addWidget(QLabel('模式:'), 0, 0)
        text_lay.addWidget(self.char_mode_combo, 0, 1)
        
        self.text_edit = QLineEdit()
        self.text_edit.setStyleSheet(Stylesheets.INPUT)
        self.text_edit.setPlaceholderText('请输入汉字')
        self.text_edit.setText('梅花易数')
        text_lay.addWidget(self.text_edit, 0, 2, 1, 2)
        text_lay.setColumnStretch(2, 1)
        
        text_group.setLayout(text_lay)
        xl.addWidget(text_group)
        
        self.params.addWidget(xw)

        # ========== 方式5: 铜钱摇卦 ==========
        ccw = QWidget(); ccw.setStyleSheet("background: transparent;")
        ccl = QVBoxLayout(ccw); ccl.setContentsMargins(0,0,0,0); ccl.setSpacing(12)
        
        coin_group = QGroupBox('铜钱摇卦')
        coin_lay = QVBoxLayout(coin_group)
        coin_lay.setSpacing(8)
        coin_lay.setContentsMargins(12, 12, 12, 12)
        
        coin_hint = QLabel('摇6次铜钱（从初爻到上爻）：\n● 少阳(1背2面) ○ 老阴(3背) ● 少阴(2背1面) ✕ 老阳(3面)\n默认初始：每次点击"自动"随机生成')
        coin_hint.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT2}; background: {Colors.ZHUSHA}; padding: 6px; border-radius: 4px;")
        coin_hint.setWordWrap(True)
        coin_hint.setTextInteractionFlags(Qt.TextSelectableByMouse)
        coin_lay.addWidget(coin_hint)
        
        self.coin_radio_buttons = []  # 6爻 × 4选项
        for i in range(6):
            row_lay = QHBoxLayout()
            row_lay.setSpacing(10)
            name_lbl = QLabel(f'{YAO_NAMES[i]}:')
            name_lbl.setFixedWidth(42)
            name_lbl.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; font-weight: {Fonts.W_MEDIUM}; font-family: {Fonts.BODY};")
            row_lay.addWidget(name_lbl)
            # 4 个爻选项改为 2×2 网格，窄宽度下可收缩不溢出
            rgrid = QGridLayout()
            rgrid.setSpacing(6)
            rgrid.setContentsMargins(0, 0, 0, 0)
            yao_buttons = []
            for j, yao_type in enumerate(['少阳', '老阴', '少阴', '老阳']):
                rb = QRadioButton(yao_type)
                rb.setStyleSheet(Stylesheets.RADIO)
                yao_buttons.append(rb)
                r, c = divmod(j, 2)
                rgrid.addWidget(rb, r, c)
            rgrid.setColumnStretch(0, 1)
            rgrid.setColumnStretch(1, 1)
            # 默认选中少阳
            yao_buttons[0].setChecked(True)
            self.coin_radio_buttons.append(yao_buttons)
            row_lay.addLayout(rgrid, 1)
            coin_lay.addLayout(row_lay)
        
        # 自动按钮
        self.auto_coin_btn = QPushButton('🎲 全部自动随机')
        self.auto_coin_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
        self.auto_coin_btn.setCursor(Qt.PointingHandCursor)
        coin_lay.addWidget(self.auto_coin_btn)
        
        coin_group.setLayout(coin_lay)
        ccl.addWidget(coin_group)
        
        self.params.addWidget(ccw)

        # ========== 方式6: 笔画起卦 ==========
        sw = QWidget(); sw.setStyleSheet("background: transparent;")
        sl = QVBoxLayout(sw); sl.setContentsMargins(0,0,0,0); sl.setSpacing(12)
        
        stroke_group = QGroupBox('笔画起卦')
        stroke_lay = QGridLayout(stroke_group)
        stroke_lay.setSpacing(8)
        stroke_lay.setContentsMargins(12, 12, 12, 12)
        
        stroke_label = QLabel('输入汉字:')
        stroke_lay.addWidget(stroke_label, 0, 0)
        self.stroke_char_edit = QLineEdit()
        self.stroke_char_edit.setStyleSheet(Stylesheets.INPUT)
        self.stroke_char_edit.setPlaceholderText('请输入一个汉字')
        stroke_lay.addWidget(self.stroke_char_edit, 0, 1)
        
        stroke_label2 = QLabel('笔画数:')
        stroke_lay.addWidget(stroke_label2, 1, 0)
        self.stroke_spin = QSpinBox()
        self.stroke_spin.setStyleSheet(Stylesheets.INPUT)
        self.stroke_spin.setRange(1, 50)
        self.stroke_spin.setValue(12)
        stroke_lay.addWidget(self.stroke_spin, 1, 1)
        
        stroke_hint = QLabel('提示：可用 Unicode 码位自动估算笔画，也可手动输入实际笔画数')
        stroke_hint.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT2};")
        stroke_hint.setWordWrap(True)
        stroke_lay.addWidget(stroke_hint, 2, 0, 1, 2)
        
        stroke_group.setLayout(stroke_lay)
        sl.addWidget(stroke_group)
        
        self.params.addWidget(sw)

        lay.addWidget(self.params)

        # 按钮
        btn_row = QHBoxLayout(); btn_row.setSpacing(12)
        self.submit_btn = QPushButton('起卦')
        self.submit_btn.setStyleSheet(Stylesheets.BTN_PRIMARY)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn = QPushButton('重置')
        self.reset_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        btn_row.addWidget(self.submit_btn); btn_row.addWidget(self.reset_btn)
        lay.addLayout(btn_row)

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _label(self, text):
        l = QLabel(text); l.setFixedWidth(42)
        l.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT2}; font-family:{Fonts.BODY};")
        return l

    def _on_method(self, i):
        self.selected_method = METHODS[i][0]
        self.params.setCurrentIndex(i)
        
        # 切换到铜钱摇卦时，确保只连接一次自动按钮
        if self.selected_method == 'copper_coin' and hasattr(self, 'auto_coin_btn'):
            # 防止重复连接
            try:
                self.auto_coin_btn.clicked.disconnect(self._auto_fill_coins)
            except RuntimeError:
                pass  # 未连接过，忽略
            self.auto_coin_btn.clicked.connect(self._auto_fill_coins)
    
    def _auto_fill_coins(self):
        """自动填充6爻为随机铜钱结果"""
        import random
        YAO_TYPES = ['少阳', '老阴', '少阴', '老阳']
        for i in range(6):
            yao = random.choice(YAO_TYPES)
            for rbtn in self.coin_radio_buttons[i]:
                if rbtn.text() == yao:
                    rbtn.setChecked(True)
                    break

    def get_data(self):
        d = {'method': self.selected_method, 'question': self.question.text().strip()}
        
        # 通用占问分类
        cat_idx = self.question_category.currentIndex()
        if cat_idx > 0:  # 选择了预设分类
            d['question_category'] = self.question_category.itemText(cat_idx)
        
        if self.selected_method == 'number':
            d['num1'] = self.num1.value()
            d['num2'] = self.num2.value()
            d['upper_num'] = self.num1.value()
            d['lower_num'] = self.num2.value()
            # 新增：数字起卦支持3个数字
            if hasattr(self, 'num3'):
                d['num3'] = self.num3.value()
                d['numbers'] = [self.num1.value(), self.num2.value(), self.num3.value()]
            else:
                d['numbers'] = [self.num1.value(), self.num2.value()]
        elif self.selected_method == 'direction':
            d['direction'] = self.dir_combo.currentText()
        elif self.selected_method == 'text':
            d['text'] = self.text_edit.text().strip()
            d['character_mode'] = 'multi' if self.char_mode_combo.currentText() == '多字' else 'single'
        elif self.selected_method == 'copper_coin':
            # 铜钱摇卦：收集6爻的结果
            six_lines = []
            for i in range(6):
                rb = self.coin_radio_buttons[i]
                for rbtn in rb:
                    if rbtn.isChecked():
                        six_lines.append(rbtn.text())
                        break
            if len(six_lines) == 6:
                d['six_lines'] = six_lines
            else:
                d['six_lines'] = ['少阴'] * 6  # 默认全部少阴
        elif self.selected_method == 'stroke':
            d['char'] = self.stroke_char_edit.text().strip()
            d['stroke_count'] = self.stroke_spin.value()
        elif self.selected_method == 'time':
            time_str = self.time_edit.text().strip()
            d['time_str'] = time_str
            try:
                from datetime import datetime as dt
                parsed = dt.strptime(time_str, '%Y-%m-%d %H:%M')
                d['year'] = parsed.year
                d['month'] = parsed.month
                d['day'] = parsed.day
                d['hour'] = parsed.hour
            except (ValueError, TypeError):
                now = dt.now()
                d['year'] = now.year
                d['month'] = now.month
                d['day'] = now.day
                d['hour'] = now.hour
            # 农历/公历选择
            d['calendar_type'] = '公历' if self.cal_lunar.isChecked() else '农历'
        
        return d

    def clear(self):
        self.method_btns[0].setChecked(True); self._on_method(0)
        self.question.clear()
        self.question_category.setCurrentIndex(0)
        self.time_edit.clear()
        self.text_edit.setText('梅花易数')
        self.char_mode_combo.setCurrentIndex(0)
        self.num1.setValue(3); self.num2.setValue(5)
        if hasattr(self, 'num3'): self.num3.setValue(7)
        self.dir_combo.setCurrentIndex(0)
        self.stroke_char_edit.clear()
        self.stroke_spin.setValue(12)
        self.cal_lunar.setChecked(True)
        if hasattr(self, 'coin_radio_buttons'):
            for i in range(6):
                for rbtn in self.coin_radio_buttons[i]:
                    rbtn.setChecked(False)
                if self.coin_radio_buttons[i]:
                    self.coin_radio_buttons[i][0].setChecked(True)
