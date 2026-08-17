"""
梅花易数起卦输入面板 - 增强版
支持8种起卦方式，每种提供丰富的输入选项
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QComboBox, QButtonGroup,
                             QSpinBox, QStackedWidget, QScrollArea, QGroupBox,
                             QRadioButton, QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from core.meihua import YAO_NAMES

METHODS = [
    ('time', '时间起卦'), ('number', '数字起卦'),
    ('direction', '方位起卦'), ('text', '文字起卦'),
    ('copper_coin', '铜钱摇卦'), ('stroke', '笔画起卦'),
]


class _AdaptiveStack(QStackedWidget):
    """参数堆叠容器：只按 *当前页* 的自然尺寸和最小尺寸预留空间。

    原生 QStackedWidget 的 sizeHint() 与 minimumSizeHint() 都会返回所有页中
    最大的那个，导致选到较矮的页面（如数字起卦）时，下方仍被强行撑出大片
    空白（铜钱摇卦那页的高度），这就是「界面失衡 / 占问与内容间距过远」的
    直接成因。覆写后只取当前页尺寸，矮页不再被高页撑高。
    """

    def sizeHint(self):
        w = self.currentWidget()
        if w is not None:
            return w.sizeHint()
        return super().sizeHint()

    def minimumSizeHint(self):
        w = self.currentWidget()
        if w is not None:
            return w.minimumSizeHint()
        return super().minimumSizeHint()

    def hasHeightForWidth(self):
        # 关键修复：堆叠页里若含自动换行 QLabel，QStackedWidget 会继承
        # hasHeightForWidth()=True，导致父布局在算 totalSizeHint 时改走
        # heightForWidth(width)，而该方法对 QStackedWidget 返回「最高页」高度
        # （铜钱摇卦约 819px），于是即便当前是矮的数字起卦页，外层 content 仍被
        # 撑到 1195px，在占问与参数、参数与按钮之间凭空多出两段 ~309px 空隙。
        # 强制返回 False，让父布局改用我们覆写的 sizeHint()（仅当前页高度），
        # 矮页即可紧凑贴合，消除「界面失衡/间距过远」。
        return False


# 先天八卦数：乾1 兑2 离3 震4 巽5 坎6 艮7 坤8（与 core/hexagram_analyzer、数据库 ba_gua 一致）
TRIGRAMS = {
    1: {'name': '乾', 'symbol': '☰', 'wuxing': '金', 'nature': '天'},
    2: {'name': '兑', 'symbol': '☱', 'wuxing': '金', 'nature': '泽'},
    3: {'name': '离', 'symbol': '☲', 'wuxing': '火', 'nature': '火'},
    4: {'name': '震', 'symbol': '☳', 'wuxing': '木', 'nature': '雷'},
    5: {'name': '巽', 'symbol': '☴', 'wuxing': '木', 'nature': '风'},
    6: {'name': '坎', 'symbol': '☵', 'wuxing': '水', 'nature': '水'},
    7: {'name': '艮', 'symbol': '☶', 'wuxing': '土', 'nature': '山'},
    8: {'name': '坤', 'symbol': '☷', 'wuxing': '土', 'nature': '地'},
}

# 方位罗盘 3x3 布局坐标（与「方位起卦」下拉项一一对应）
DIR_POS = {
    '西北方': (0, 0), '正北方': (0, 1), '东北方': (0, 2),
    '正西方': (1, 0),                 '正东方': (1, 2),
    '西南方': (2, 0), '正南方': (2, 1), '东南方': (2, 2),
}


def _mod8(n):
    """先天八卦取模：余数 0 记 8（乾兑离震巽坎艮坤）。"""
    r = n % 8
    return 8 if r == 0 else r


def _mod6(n):
    """动爻取模：余数 0 记 6（自下而上第 6 爻）。"""
    r = n % 6
    return 6 if r == 0 else r


class MeihuaInputPanel(QWidget):
    """梅花易数起卦输入面板（主窗口左栏）。

    支持 METHODS 中列出的 6 种起卦方式（时间/数字/方位/文字/铜钱/笔画）。
    各方式所需参数差异很大，故用 QStackedWidget 承载参数区：方式按钮索引与
    堆叠页索引一一对应，切换方式即切换参数页，避免把无关控件堆在同一屏。
    """

    def __init__(self, parent=None):
        """
        Args:
            parent: Qt 父控件。
        """
        super().__init__(parent)
        # 默认时间起卦，与 METHODS[0] 及参数堆叠页索引 0 对齐
        self.selected_method = 'time'
        self._build()

    def _build(self):
        """构建起卦表单：公共输入区 + 6 个方式专属参数页。

        公共区为「方式选择 -> 占问分类 -> 占问」；其后 self.params 堆叠容器按
        METHODS 的顺序依次 addWidget 六个参数页。两者顺序必须严格一致，
        _on_method() 才能用同一个索引同时切换内部状态与显示页面。
        """
        self.setStyleSheet(f"""
            MeihuaInputPanel {{
                background-color: {Colors.BG};
            }}
            QGroupBox {{
                color: {Colors.TEXT};
                font-weight: {Fonts.W_MEDIUM};
                font-family: {Fonts.BODY};
            }}
        """)

        scroll = QScrollArea()
        scroll.setStyleSheet(Stylesheets.SCROLL)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.BG};")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(24, 18, 24, 18)
        lay.setSpacing(12)

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
        method_lay.setSpacing(6)
        method_lay.addWidget(self._label('方式'))
        grid = QGridLayout()
        grid.setSpacing(6)
        self.method_btns = []
        self.method_grp = QButtonGroup(self)
        self.method_grp.setExclusive(True)
        cols = 3
        for i, (v, n) in enumerate(METHODS):
            b = QPushButton(n)
            b.setStyleSheet(Stylesheets.BTN_SWITCH)
            b.setCheckable(True); b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(30)
            self.method_grp.addButton(b, i)
            r, c = divmod(i, cols)
            grid.addWidget(b, r, c)
            self.method_btns.append(b)
            b.clicked.connect(lambda _, idx=i: self._on_method(idx))
        for c in range(cols):
            grid.setColumnStretch(c, 1)
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

        # 动态参数容器（自适应：只按当前页高度预留，矮页不再留空）
        self.params = _AdaptiveStack()
        self.params.setStyleSheet("background: transparent;")
        # Maximum 垂直策略：确保布局不会把高页（铜钱摇卦）的高度塞给矮页，
        # 使矮页内容紧贴上方控件，消除「占问与内容间距过远」。
        self.params.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

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
        tl.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.params.addWidget(tw)

        # ========== 方式2: 数字起卦 ==========
        nw = QWidget(); nw.setStyleSheet("background: transparent;")
        nl = QVBoxLayout(nw); nl.setContentsMargins(0,0,0,0); nl.setSpacing(8)

        # 交互提示（实时说明，提升数据录入清晰度）
        num_tip = QLabel('输入 2~3 个数字，依次作为上卦 / 下卦 / 动爻（动爻可留空）；'
                         '数值较大时自动按先天八卦数取模换算。')
        num_tip.setWordWrap(True)
        num_tip.setStyleSheet(f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};")
        nl.addWidget(num_tip)

        # 数据框：卡片 + 内嵌滚动条（列宽自适应 / 数据对齐 / 大量输入仍整洁）
        num_card = QFrame()
        num_card.setObjectName('num_data_box')
        num_card.setStyleSheet(f"""
            QFrame#num_data_box {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS};
            }}
        """)
        num_grid = QGridLayout(num_card)
        num_grid.setContentsMargins(14, 14, 14, 14)
        num_grid.setHorizontalSpacing(10)
        num_grid.setVerticalSpacing(8)
        num_grid.setColumnStretch(0, 1)
        num_grid.setColumnStretch(1, 1)
        num_grid.setColumnStretch(2, 1)

        def _mk_num(label_text, default):
            """生成一列：标签（上、居中）+ 数字框（下、居中、等宽）。"""
            lbl = QLabel(label_text)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {Colors.TEXT2}; font-size: {Fonts.SZ_SMALL}; font-family: {Fonts.BODY};")
            sb = QSpinBox()
            sb.setStyleSheet(Stylesheets.INPUT)
            sb.setRange(1, 999999)
            sb.setValue(default)
            sb.setAlignment(Qt.AlignCenter)
            sb.setMinimumHeight(38)
            return lbl, sb

        l1, self.num1 = _mk_num('上卦数', 3)
        l2, self.num2 = _mk_num('下卦数', 5)
        l3, self.num3 = _mk_num('动爻数(可选)', 7)
        num_grid.addWidget(l1, 0, 0)
        num_grid.addWidget(l2, 0, 1)
        num_grid.addWidget(l3, 0, 2)
        num_grid.addWidget(self.num1, 1, 0)
        num_grid.addWidget(self.num2, 1, 1)
        num_grid.addWidget(self.num3, 1, 2)
        nl.addWidget(num_card)

        # 实时卦象预览：随数字变化即时刷新，填补空白并提供交互反馈
        num_preview_card, self._num_preview_update = self._build_gua_preview()
        nl.addWidget(num_preview_card)

        self.num1.valueChanged.connect(self._refresh_num_preview)
        self.num2.valueChanged.connect(self._refresh_num_preview)
        self.num3.valueChanged.connect(self._refresh_num_preview)
        self._refresh_num_preview()

        nl.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.params.addWidget(nw)

        # ========== 方式3: 方位起卦 ==========
        dw = QWidget(); dw.setStyleSheet("background: transparent;")
        dl = QVBoxLayout(dw); dl.setContentsMargins(0,0,0,0); dl.setSpacing(10)

        dir_group = QGroupBox('方位选择')
        dir_lay = QVBoxLayout(dir_group)
        dir_lay.setSpacing(10)
        dir_lay.setContentsMargins(12, 12, 12, 12)

        self.dir_combo = QComboBox()
        self.dir_combo.setStyleSheet(Stylesheets.COMBO)
        for d in ['正北方','东北方','正东方','东南方','正南方','西南方','正西方','西北方']:
            self.dir_combo.addItem(d)
        dir_lay.addWidget(self.dir_combo)

        # 紧凑罗盘：直观高亮当前方位（替代原大段文字说明，解决「框大内容少」）
        compass_widget, self._compass_update = self._build_compass()
        dir_lay.addWidget(compass_widget)

        dir_group.setLayout(dir_lay)
        dl.addWidget(dir_group)

        # 实时卦象预览
        dir_preview_card, self._dir_preview_update = self._build_gua_preview()
        dl.addWidget(dir_preview_card)

        dl.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.params.addWidget(dw)

        self.dir_combo.currentIndexChanged.connect(self._on_dir_changed)
        self._on_dir_changed()

        # ========== 方式4: 文字起卦 ==========
        xw = QWidget(); xw.setStyleSheet("background: transparent;")
        xl = QVBoxLayout(xw); xl.setContentsMargins(0,0,0,0); xl.setSpacing(10)

        text_group = QGroupBox('文字设置')
        text_lay = QGridLayout(text_group)
        text_lay.setSpacing(8)
        text_lay.setContentsMargins(12, 12, 12, 12)

        self.char_mode_combo = QComboBox()
        self.char_mode_combo.addItems(['单字', '多字'])
        self.char_mode_combo.currentIndexChanged.connect(self._on_char_mode_changed)
        text_lay.addWidget(QLabel('模式:'), 0, 0)
        text_lay.addWidget(self.char_mode_combo, 0, 1)

        self.text_edit = QLineEdit()
        self.text_edit.setStyleSheet(Stylesheets.INPUT)
        self.text_edit.setPlaceholderText('请输入汉字')
        self.text_edit.textChanged.connect(self._on_text_changed)
        text_lay.addWidget(self.text_edit, 0, 2, 1, 2)
        text_lay.setColumnStretch(2, 1)

        self._build_text_feedback(text_lay)

        text_group.setLayout(text_lay)
        xl.addWidget(text_group)

        # 实时卦象预览
        text_preview_card, self._text_preview_update = self._build_gua_preview()
        xl.addWidget(text_preview_card)

        xl.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.params.addWidget(xw)
        self._refresh_text_preview()

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
        # 构建期连接一次即可（避免切换方式时反复 disconnect 触发 libpyside 警告）
        self.auto_coin_btn.clicked.connect(self._auto_fill_coins)
        coin_lay.addWidget(self.auto_coin_btn)
        
        coin_group.setLayout(coin_lay)
        ccl.addWidget(coin_group, 1)
        ccl.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        
        self.params.addWidget(ccw)

        # ========== 方式6: 笔画起卦 ==========
        sw = QWidget(); sw.setStyleSheet("background: transparent;")
        sl = QVBoxLayout(sw); sl.setContentsMargins(0,0,0,0); sl.setSpacing(10)

        stroke_group = QGroupBox('笔画起卦')
        stroke_lay = QGridLayout(stroke_group)
        stroke_lay.setSpacing(8)
        stroke_lay.setContentsMargins(12, 12, 12, 12)

        stroke_label = QLabel('输入汉字:')
        stroke_lay.addWidget(stroke_label, 0, 0)
        self.stroke_char_edit = QLineEdit()
        self.stroke_char_edit.setStyleSheet(Stylesheets.INPUT)
        self.stroke_char_edit.setPlaceholderText('请输入一个汉字')
        self.stroke_char_edit.textChanged.connect(self._refresh_stroke_preview)
        stroke_lay.addWidget(self.stroke_char_edit, 0, 1)

        stroke_label2 = QLabel('笔画数:')
        stroke_lay.addWidget(stroke_label2, 1, 0)
        self.stroke_spin = QSpinBox()
        self.stroke_spin.setStyleSheet(Stylesheets.INPUT)
        self.stroke_spin.setRange(1, 50)
        self.stroke_spin.setValue(12)
        self.stroke_spin.valueChanged.connect(self._refresh_stroke_preview)
        stroke_lay.addWidget(self.stroke_spin, 1, 1)

        stroke_hint = QLabel('提示：可用 Unicode 码位自动估算笔画，也可手动输入实际笔画数')
        stroke_hint.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT2};")
        stroke_hint.setWordWrap(True)
        stroke_lay.addWidget(stroke_hint, 2, 0, 1, 2)

        stroke_group.setLayout(stroke_lay)
        sl.addWidget(stroke_group)

        # 实时卦象预览
        stroke_preview_card, self._stroke_preview_update = self._build_gua_preview()
        sl.addWidget(stroke_preview_card)

        sl.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.params.addWidget(sw)
        self._refresh_stroke_preview()

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

        # 末尾留白：把多余空间压到最底部，确保「占问→参数→按钮」紧凑成组、
        # 矮页（如数字起卦）下方不留突兀间隙，整体视觉更平衡。
        lay.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _label(self, text):
        """生成表单左侧的定宽说明标签，使各行输入控件左边缘对齐。

        Args:
            text: 标签文字。

        Returns:
            QLabel: 固定宽 42px 的深灰色标签，确保在浅色背景上清晰可读。
        """
        l = QLabel(text); l.setFixedWidth(42)
        l.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT}; font-family:{Fonts.BODY};")
        return l

    def _on_method(self, i):
        """起卦方式切换槽（由方式按钮的 clicked 触发）。

        同步 selected_method 并把参数堆叠页切到同一索引。铜钱摇卦的
        「全部自动随机」按钮已在 _build() 中连接一次，无需在此重复接线。

        Args:
            i: 方式索引，与 METHODS 及 self.params 的页序一一对应。
        """
        self.selected_method = METHODS[i][0]
        self.params.setCurrentIndex(i)

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
        """获取梅花易数输入数据。若必要数据缺失则抛 ValueError，不调用方做静默兜底。"""
        d = {'method': self.selected_method, 'question': self.question.text().strip()}

        # 通用占问分类
        cat_idx = self.question_category.currentIndex()
        if cat_idx > 0:
            d['question_category'] = self.question_category.itemText(cat_idx)

        method = self.selected_method

        if method == 'number':
            d['num1'] = self.num1.value()
            d['num2'] = self.num2.value()
            d['upper_num'] = self.num1.value()
            d['lower_num'] = self.num2.value()
            if hasattr(self, 'num3'):
                d['num3'] = self.num3.value()
                d['numbers'] = [self.num1.value(), self.num2.value(), self.num3.value()]
            else:
                d['numbers'] = [self.num1.value(), self.num2.value()]

        elif method == 'direction':
            d['direction'] = self.dir_combo.currentText()

        elif method == 'text':
            text_val = self.text_edit.text().strip()
            if not text_val:
                raise ValueError("文字起卦需输入文字内容")
            d['text'] = text_val
            d['character_mode'] = 'multi' if self.char_mode_combo.currentText() == '多字' else 'single'

        elif method == 'copper_coin':
            six_lines = []
            coin_btns = getattr(self, 'coin_radio_buttons', [])
            for i in range(6):
                if i < len(coin_btns):
                    rb = coin_btns[i]
                    for rbtn in rb:
                        if rbtn.isChecked():
                            six_lines.append(rbtn.text())
                            break
            if len(six_lines) == 6:
                d['six_lines'] = six_lines
            else:
                filled = len(six_lines)
                raise ValueError(f"铜钱摇卦需完成6爻，当前仅填{filled}爻")

        elif method == 'stroke':
            char_val = self.stroke_char_edit.text().strip()
            if not char_val:
                raise ValueError("笔画起卦需输入汉字")
            d['char'] = char_val
            d['stroke_count'] = self.stroke_spin.value()

        elif method == 'time':
            time_str = self.time_edit.text().strip()
            d['time_str'] = time_str
            if not time_str:
                # 时间留空则用当前时间（这是合理行为，非兜底）
                from datetime import datetime as dt
                now = dt.now()
                d['year'] = now.year
                d['month'] = now.month
                d['day'] = now.day
                d['hour'] = now.hour
            else:
                try:
                    parsed = dt.strptime(time_str, '%Y-%m-%d %H:%M')
                    d['year'] = parsed.year
                    d['month'] = parsed.month
                    d['day'] = parsed.day
                    d['hour'] = parsed.hour
                except (ValueError, TypeError):
                    raise ValueError(f"时间格式错误: {time_str}（需 YYYY-MM-DD HH:MM）")
            d['calendar_type'] = '公历' if self.cal_lunar.isChecked() else '农历'

        return d

    def _build_text_feedback(self, parent_layout):
        """在文字起卦面板中追加「字数/笔画」实时反馈区（增强数据交互）。"""
        self._text_feedback = QLabel('')
        self._text_feedback.setWordWrap(True)
        self._text_feedback.setStyleSheet(
            f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};"
        )
        parent_layout.addWidget(self._text_feedback, 1, 0, 1, 4)
        self._refresh_text_feedback()

    def _refresh_text_feedback(self):
        """根据当前文本框与模式，刷新字数/笔画提示（空值时淡显占位）。"""
        text = self.text_edit.text()
        mode = self.char_mode_combo.currentText()
        chars = [ch for ch in text if '\u4e00' <= ch <= '\u9fff']
        if not chars:
            self._text_feedback.setText(
                '未检测到有效汉字，请输入中文内容后再观察笔画反馈'
            )
            self._text_feedback.setStyleSheet(
                f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT4}; font-family:{Fonts.BODY};"
            )
            return
        if mode == '单字' and len(chars) > 1:
            self._text_feedback.setText(
                f'当前输入 {len(chars)} 字，单字模式将取第1个「{chars[0]}」参与起卦'
            )
            self._text_feedback.setStyleSheet(
                f"font-size:{Fonts.SZ_MICRO}; color:{Colors.WARNING}; font-family:{Fonts.BODY};"
            )
        else:
            strokes = [len(ch) * 2 for ch in chars]
            self._text_feedback.setText(
                f'共 {len(chars)} 字，累计 {sum(strokes)} 笔（按 Unicode 2 笔/字估算）'
            )
            self._text_feedback.setStyleSheet(
                f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};"
            )

    def _on_char_mode_changed(self, idx):
        """切换单字/多字时，立即刷新反馈与卦象预览、并更新输入提示。"""
        self._refresh_text_feedback()
        self._refresh_text_preview()
        if idx == 0:
            self.text_edit.setPlaceholderText('请输入一个汉字')
        else:
            self.text_edit.setPlaceholderText('请输入多个汉字，用于计算总笔画')

    def clear(self):
        """重置面板为初始态（由「重置」按钮触发）。

        方式回到第一项后必须手动调用 _on_method(0)：setChecked() 不会发出 clicked
        信号，否则参数堆叠页与 selected_method 会停留在上一次选择的起卦方式上。
        六爻区先整行取消勾选、再选中第一项（少阳），确保上次的摇卦结果被彻底清掉；
        文字与数字等输入框则恢复为示例默认值，方便用户直接再起一卦。
        """
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

    # ========== 实时卦象预览（四方式共用，填补空白 + 提升交互） ==========
    def _build_gua_preview(self):
        """构建可复用的「实时卦象预览」卡片，返回 (card, update_fn)。

        update_fn(upper_num, lower_num, changing_yao) 按先天八卦数刷新三栏
        （上卦 / 下卦 / 动爻）；输入非法时三栏显示占位横线。该卡片解决了
        「框大内容少、输入板块显空洞」的问题——把空余空间变为有意义的实时反馈。
        """
        card = QFrame()
        card.setObjectName('gua_preview')
        card.setStyleSheet(f"""
            QFrame#gua_preview {{
                background: {Colors.QINGHUA_GLOW};
                border: 1px solid {Colors.QINGHUA_LIGHT};
                border-radius: {Spacing.RADIUS};
            }}
        """)
        gl = QGridLayout(card)
        gl.setContentsMargins(14, 12, 14, 12)
        gl.setHorizontalSpacing(0)
        gl.setVerticalSpacing(6)

        hdr = QLabel('实时卦象预览')
        hdr.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.QINGHUA}; "
            f"font-weight:{Fonts.W_MEDIUM}; font-family:{Fonts.BODY};"
        )
        gl.addWidget(hdr, 0, 0, 1, 3)

        def _cell(title):
            box = QFrame()
            box.setStyleSheet("background: transparent;")
            bl = QVBoxLayout(box)
            bl.setContentsMargins(0, 0, 0, 0)
            bl.setSpacing(3)
            t = QLabel(title)
            t.setAlignment(Qt.AlignCenter)
            t.setStyleSheet(
                f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};"
            )
            sym = QLabel('—')
            sym.setAlignment(Qt.AlignCenter)
            sym.setStyleSheet(
                f"font-size:24px; color:{Colors.QINGHUA}; font-family:{Fonts.TITLE}; line-height:1.1;"
            )
            nm = QLabel('—')
            nm.setAlignment(Qt.AlignCenter)
            nm.setStyleSheet(
                f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT}; "
                f"font-weight:{Fonts.W_MEDIUM}; font-family:{Fonts.BODY};"
            )
            bl.addWidget(t)
            bl.addWidget(sym)
            bl.addWidget(nm)
            return box, sym, nm

        b1, s1, n1 = _cell('上卦')
        b2, s2, n2 = _cell('下卦')
        b3, s3, n3 = _cell('动爻')
        gl.addWidget(b1, 1, 0)
        gl.addWidget(b2, 1, 1)
        gl.addWidget(b3, 1, 2)
        gl.setColumnStretch(0, 1)
        gl.setColumnStretch(1, 1)
        gl.setColumnStretch(2, 1)

        def update(upper_num, lower_num, changing_yao):
            u = TRIGRAMS.get(upper_num)
            l = TRIGRAMS.get(lower_num)
            if u:
                s1.setText(u['symbol']); n1.setText(u['name'])
            else:
                s1.setText('—'); n1.setText('—')
            if l:
                s2.setText(l['symbol']); n2.setText(l['name'])
            else:
                s2.setText('—'); n2.setText('—')
            if changing_yao and 1 <= changing_yao <= 6:
                s3.setText('⚡'); n3.setText(YAO_NAMES[changing_yao - 1])
            else:
                s3.setText('—'); n3.setText('—')

        return card, update

    def _build_compass(self):
        """构建紧凑的 3×3 方位罗盘，选中方位高亮，返回 (widget, update_fn)。"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(widget)
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)

        center = QLabel('占')
        center.setAlignment(Qt.AlignCenter)
        center.setStyleSheet(
            f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; background:{Colors.CARD}; "
            f"border:1px solid {Colors.BORDER}; border-radius:{Spacing.RADIUS_SM}; padding:6px;"
        )
        grid.addWidget(center, 1, 1)

        self._compass_labels = {}
        for name, (r, c) in DIR_POS.items():
            lbl = QLabel(name.replace('正', ''))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(self._compass_cell_style(False))
            grid.addWidget(lbl, r, c)
            self._compass_labels[name] = lbl

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 1)

        def update(direction_text):
            for name, lbl in self._compass_labels.items():
                lbl.setStyleSheet(self._compass_cell_style(name == direction_text))

        return widget, update

    def _compass_cell_style(self, active):
        """方位罗盘单元格样式：选中态用青花蓝高亮，普通态为浅边框卡片。"""
        if active:
            return (
                f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT_INV}; background:{Colors.QINGHUA}; "
                f"border:1px solid {Colors.QINGHUA}; border-radius:{Spacing.RADIUS_SM}; "
                f"padding:6px; font-weight:{Fonts.W_BOLD};"
            )
        return (
            f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT2}; background:{Colors.CARD}; "
            f"border:1px solid {Colors.BORDER}; border-radius:{Spacing.RADIUS_SM}; padding:6px;"
        )

    def _refresh_num_preview(self):
        """数字起卦预览：上卦=num1%8，下卦=num2%8，动爻=num3%6（与核心算法一致）。"""
        n1 = self.num1.value()
        n2 = self.num2.value()
        n3 = self.num3.value()
        upper = _mod8(n1)
        lower = _mod8(n2)
        changing = _mod6(n3)
        self._num_preview_update(upper, lower, changing)

    def _on_dir_changed(self):
        """方位切换：同步高亮罗盘与刷新卦象预览。"""
        self._compass_update(self.dir_combo.currentText())
        self._refresh_dir_preview()

    def _refresh_dir_preview(self):
        """方位起卦预览：上卦=方位数%8，下卦=当前时辰数%8，动爻=(方位数+时辰数)%6。"""
        key = self.dir_combo.currentText().replace('正', '').replace('方', '')
        dm = {'北': 1, '东北': 8, '东': 3, '东南': 4, '南': 9, '西南': 2, '西': 7, '西北': 6}
        direction_num = dm.get(key)
        if direction_num is None:
            self._dir_preview_update(None, None, None)
            return
        from datetime import datetime as _dt
        hour_num = _dt.now().hour % 12 + 1
        upper = _mod8(direction_num)
        lower = _mod8(hour_num)
        changing = _mod6(direction_num + hour_num)
        self._dir_preview_update(upper, lower, changing)

    def _on_text_changed(self):
        """文字内容变化：同步刷新字数反馈与卦象预览。"""
        self._refresh_text_feedback()
        self._refresh_text_preview()

    def _refresh_text_preview(self):
        """文字起卦预览：上卦=总笔画%8，下卦=(总笔画+字数)%8，动爻=总笔画×字数%6。"""
        text = self.text_edit.text()
        chars = [ch for ch in text if '\u4e00' <= ch <= '\u9fff']
        if not chars:
            self._text_preview_update(None, None, None)
            return
        total_strokes = sum(2 for _ in chars)  # 与核心算法一致：每汉字估 2 笔
        char_count = len(chars)
        upper = _mod8(total_strokes)
        lower = _mod8(total_strokes + char_count)
        changing = _mod6(total_strokes * char_count)
        self._text_preview_update(upper, lower, changing)

    def _refresh_stroke_preview(self):
        """笔画起卦预览：上卦=笔画数%8，下卦=(笔画数//8)%8，动爻=笔画数%6。"""
        char = self.stroke_char_edit.text().strip()
        if not char or not ('\u4e00' <= char <= '\u9fff'):
            self._stroke_preview_update(None, None, None)
            return
        sc = self.stroke_spin.value()
        upper = _mod8(sc)
        lower = _mod8(sc // 8)
        changing = _mod6(sc)
        self._stroke_preview_update(upper, lower, changing)
