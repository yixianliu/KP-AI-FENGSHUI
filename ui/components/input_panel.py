"""
左侧输入面板 - 极简轻量国风
垂直表单 · 圆角控件 · 朱砂红主按钮 · 白底灰框副按钮
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QComboBox, QPushButton, QFrame, QButtonGroup,
                             QDateEdit, QTextEdit, QScrollArea, QSpinBox)
from PySide6.QtCore import QDate, Qt
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from ui.components.collapsible_card import CollapsibleCard

HOUR_NAMES = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时',
              '午时', '未时', '申时', '酉时', '戌时', '亥时']
HOUR_RANGES = [(23,1),(1,3),(3,5),(5,7),(7,9),(9,11),(11,13),(13,15),(15,17),(17,19),(19,21),(21,23)]


def hour_to_index(hour: int) -> int:
    """T3.2 由小时数换算时辰索引（0=子时 … 11=亥时）。

    时辰以 2 小时为一格且子时跨日（23:00~01:00），故先把 23 点折算到 -1
    再看落在哪一格：((h + 1) // 2) % 12 即覆盖全部 24 小时且天然处理跨日。

    Args:
        hour: 小时数（0~23）

    Returns:
        int: 时辰索引
    """
    return ((int(hour) + 1) // 2) % 12

PAN_TYPES = [
    ('bazi','八字四柱'),('ziwei','紫微斗数'),('qimen','奇门遁甲'),
    ('liuyao','六爻纳甲'),('yangzhai','阳宅风水'),('yinning','阴宅风水'),
]


class InputPanel(QWidget):
    """八字排盘输入面板（主窗口左栏）。

    负责收集姓名、历法、日期、时辰、出生地、性别、流派、备注等排盘要素，
    由 get_data() 打包成 dict 交给 core 层排盘；面板自身不做任何命理计算。

    与主窗口的交互约定：
      - submit_btn / reset_btn 由主窗口连接到「排盘」「重置」槽函数；
      - 输入不合法时 submit_btn 自动置灰，见 _validate()。
    """

    def __init__(self, parent=None):
        """
        Args:
            parent: Qt 父控件。
        """
        super().__init__(parent)
        self.selected_hour = 6           # 时辰索引，默认 6 = 午时（11:00~13:00）
        self.selected_pan_type = 'bazi'  # 本标签页固定为八字四柱，保留字段供下游读取
        self._build()

    def _build(self):
        """构建表单界面并接线信号。

        结构：外层 QScrollArea 包一个 content 容器（窗口拉窄时可滚动，避免控件被压扁），
        内部按「标题 -> 分割线 -> 各输入行 -> 操作按钮」自上而下排列。
        末尾创建的 lng_edit / lat_edit / day_night_switch / true_solar_switch 是历史遗留
        的兼容字段，仍有下游代码按属性名读取，因此保留对象但设为不可见。
        """
        self.setStyleSheet(f"background-color: {Colors.BG};")

        scroll = QScrollArea()
        scroll.setStyleSheet(Stylesheets.SCROLL)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.BG};")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(Spacing.S4)

        # 标题
        hdr = QHBoxLayout()
        hdr.setSpacing(Spacing.S2)
        icon = QLabel('☯')
        icon.setStyleSheet(f"font-size: 13px; color: {Colors.LIUJIN};")
        title = QLabel('风水排盘参数')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
        """)
        hdr.addWidget(icon)
        hdr.addWidget(title)
        hdr.addStretch()
        lay.addLayout(hdr)

        # 青蓝分割线
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {Colors.QINGHUA_LIGHT};")
        lay.addWidget(div)

        # ===== 基本信息分组（姓名 / 历法 / 日期 / 时辰时间 / 性别 / 类型） =====
        basic_card = CollapsibleCard('基本信息', '☯', accent_color=Colors.QINGHUA, collapsed=False)
        basic_body = QWidget()
        basic_body.setStyleSheet("background: transparent;")
        basic_lay = QVBoxLayout(basic_body)
        basic_lay.setContentsMargins(6, 6, 6, 6)
        basic_lay.setSpacing(Spacing.S3)

        # 姓名
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        row.addWidget(self._label('姓名'))
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(Stylesheets.INPUT)
        self.name_edit.setPlaceholderText('请输入姓名')
        row.addWidget(self.name_edit, 1)
        basic_lay.addLayout(row)

        # 历法
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        row.addWidget(self._label('历法'))
        self.solar_btn = QPushButton('公历')
        self.solar_btn.setStyleSheet(Stylesheets.BTN_SWITCH)
        self.solar_btn.setCheckable(True)
        self.solar_btn.setChecked(True)
        self.solar_btn.setCursor(Qt.PointingHandCursor)
        self.lunar_btn = QPushButton('农历')
        self.lunar_btn.setStyleSheet(Stylesheets.BTN_SWITCH)
        self.lunar_btn.setCheckable(True)
        self.lunar_btn.setCursor(Qt.PointingHandCursor)
        row.addWidget(self.solar_btn)
        row.addWidget(self.lunar_btn)
        row.addStretch()
        basic_lay.addLayout(row)

        # 日期
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        row.addWidget(self._label('日期'))
        self.date_edit = QDateEdit()
        self.date_edit.setStyleSheet(Stylesheets.DATE)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        row.addWidget(self.date_edit, 1)
        basic_lay.addLayout(row)

        # T3.2 时辰 / 时间：时辰下拉（快速选）+ 时分双输入（精确调）+ 实时时辰映射
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        row.addWidget(self._label('时辰'))
        self.hour_combo = QComboBox()
        self.hour_combo.setStyleSheet(Stylesheets.COMBO)
        for i, n in enumerate(HOUR_NAMES):
            self.hour_combo.addItem(f'{n} ({HOUR_RANGES[i][0]:02d}:00~{HOUR_RANGES[i][1]:02d}:00)', i)
        self.hour_combo.setCurrentIndex(6)
        row.addWidget(self.hour_combo, 1)

        # 时 / 分 双 SpinBox：替代原单文本 time_edit，杜绝手填非法格式
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(12)
        self.hour_spin.setSuffix(' 时')
        self.hour_spin.setFixedWidth(72)
        self.hour_spin.setStyleSheet(Stylesheets.INPUT)
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(0)
        self.minute_spin.setSuffix(' 分')
        self.minute_spin.setFixedWidth(72)
        self.minute_spin.setStyleSheet(Stylesheets.INPUT)
        row.addWidget(self.hour_spin)
        row.addWidget(self.minute_spin)
        basic_lay.addLayout(row)

        # 实时时辰映射标签：随时分变化显示「午时 (11:00~13:00)」。
        # 独立成行并允许自动换行，避免与上方下拉/双微调争夺横向空间导致截断。
        self.time_label = QLabel()
        self.time_label.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.LIUJIN}; font-family:{Fonts.BODY};"
        )
        self.time_label.setWordWrap(True)
        tl_row = QHBoxLayout()
        tl_row.setSpacing(Spacing.S2)
        tl_row.addSpacing(Spacing.S8)  # 与上方输入框左边缘对齐（标签 42 + 间距 8）
        tl_row.addWidget(self.time_label, 1)
        basic_lay.addLayout(tl_row)

        # 性别
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        row.addWidget(self._label('性别'))
        self.gender_grp = QButtonGroup(self)
        self.male_btn = QPushButton('♂ 男')
        self.male_btn.setStyleSheet(Stylesheets.BTN_SWITCH)
        self.male_btn.setCheckable(True)
        self.male_btn.setChecked(True)
        self.male_btn.setCursor(Qt.PointingHandCursor)
        self.female_btn = QPushButton('♀ 女')
        self.female_btn.setStyleSheet(Stylesheets.BTN_SWITCH)
        self.female_btn.setCheckable(True)
        self.female_btn.setCursor(Qt.PointingHandCursor)
        self.gender_grp.addButton(self.male_btn, 0)
        self.gender_grp.addButton(self.female_btn, 1)
        row.addWidget(self.male_btn)
        row.addWidget(self.female_btn)
        row.addStretch()
        basic_lay.addLayout(row)

        # 类型徽章（八字标签类型固定，避免误导）
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        row.addWidget(self._label('类型'))
        type_badge = QLabel('八字四柱')
        type_badge.setCursor(Qt.PointingHandCursor)
        type_badge.setToolTip(
            '本程序当前支持的排盘类型：八字四柱、梅花易数。\n'
            '当前位于「八字排盘」标签，类型固定为八字四柱。'
        )
        type_badge.setStyleSheet(f"""
            background: {Colors.QINGHUA_GLOW};
            color: {Colors.QINGHUA};
            border: 1px solid {Colors.QINGHUA_LIGHT};
            border-radius: {Spacing.RADIUS_SM};
            font-size: 12px;
            font-weight: {Fonts.W_MEDIUM};
            font-family: {Fonts.BODY};
            padding: 5px 16px;
        """)
        row.addWidget(type_badge)
        row.addStretch()
        basic_lay.addLayout(row)

        basic_card.set_content(basic_body)
        lay.addWidget(basic_card)

        # ===== 地点与偏好分组（出生地 / 流派） =====
        pref_card = CollapsibleCard('地点与偏好', '◎', accent_color=Colors.QINGHUA, collapsed=False)
        pref_body = QWidget()
        pref_body.setStyleSheet("background: transparent;")
        pref_lay = QVBoxLayout(pref_body)
        pref_lay.setContentsMargins(6, 6, 6, 6)
        pref_lay.setSpacing(Spacing.S3)

        # 出生地（手动文本，可经 AI 解析经纬度/时区）
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        row.addWidget(self._label('出生地'))
        self.location_edit = QLineEdit()
        self.location_edit.setStyleSheet(Stylesheets.INPUT)
        self.location_edit.setPlaceholderText('如：北京市朝阳区 / 纽约 / 洛杉矶（留空则按默认经度 120°E 计算）')
        row.addWidget(self.location_edit, 1)
        pref_lay.addLayout(row)

        # 流派
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        row.addWidget(self._label('流派'))
        self.school_combo = QComboBox()
        self.school_combo.setStyleSheet(Stylesheets.COMBO)
        self.school_combo.addItems(['子平真诠', '滴天髓', '三命通会'])
        row.addWidget(self.school_combo, 1)
        pref_lay.addLayout(row)

        pref_card.set_content(pref_body)
        lay.addWidget(pref_card)

        # ===== 时间校准分组（6.1.3：默认折叠，展示出生时间与经度说明） =====
        # 输入面板不做任何命理计算（零功能变更），真太阳时由排盘引擎内部依据
        # 经度与节气校正；此处仅展示原始输入时间、经度基准与校正说明。
        self._ts_time_label = QLabel()
        self._ts_time_label.setStyleSheet(
            f"font-size:{Fonts.SZ_BODY}; color:{Colors.TEXT}; font-family:{Fonts.BODY};")
        self._ts_hour_label = QLabel()
        self._ts_hour_label.setStyleSheet(
            f"font-size:{Fonts.SZ_BODY}; color:{Colors.LIUJIN}; font-family:{Fonts.BODY};")
        self._ts_note = QLabel(
            '真太阳时校正由排盘引擎依据出生地与节气自动完成，无需手动输入。'
            '出生地填写具体城市（如「北京市朝阳区」）可让引擎估算更精确的经度。')
        self._ts_note.setStyleSheet(
            f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};")
        self._ts_note.setWordWrap(True)

        ts_card = CollapsibleCard('时间校准', '◷', accent_color=Colors.YU, collapsed=True)
        ts_body = QWidget()
        ts_body.setStyleSheet("background: transparent;")
        ts_lay = QVBoxLayout(ts_body)
        ts_lay.setContentsMargins(6, 6, 6, 6)
        ts_lay.setSpacing(Spacing.S2)
        ts_lay.addWidget(self._label('原始出生时间'))
        ts_lay.addWidget(self._ts_time_label)
        ts_lay.addWidget(self._label('当前时辰'))
        ts_lay.addWidget(self._ts_hour_label)
        ts_lay.addWidget(self._label('经度基准'))
        lng = QLabel('默认 120°E（东八区标准经度）；填写具体出生城市后将按实际经度校正。')
        lng.setStyleSheet(
            f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};")
        lng.setWordWrap(True)
        ts_lay.addWidget(lng)
        ts_lay.addWidget(self._ts_note)
        ts_card.set_content(ts_body)
        lay.addWidget(ts_card)
        self._refresh_true_solar()
        # 保留历史遗留兼容字段（仍有下游按属性名读取），但由新卡片驱动展示
        self.true_solar_switch = ts_card

        # ===== 备注分组 =====
        notes_card = CollapsibleCard('备注', '✎', accent_color=Colors.TEXT3, collapsed=False)
        notes_body = QWidget()
        notes_body.setStyleSheet("background: transparent;")
        notes_lay = QVBoxLayout(notes_body)
        notes_lay.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        notes_lay.setContentsMargins(6, 6, 6, 6)
        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(Stylesheets.TEXT_EDIT)
        self.notes_edit.setPlaceholderText('可选补充…')
        self.notes_edit.setFixedHeight(60)
        notes_lay.addWidget(self.notes_edit)
        notes_card.set_content(notes_body)
        lay.addWidget(notes_card)

        lay.addStretch()

        # ===== 按钮 =====
        btn_row = QHBoxLayout()
        btn_row.setSpacing(Spacing.S3)
        self.submit_btn = QPushButton('开始排盘')
        self.submit_btn.setStyleSheet(Stylesheets.BTN_PRIMARY)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setEnabled(False)
        self.reset_btn = QPushButton('重置')
        self.reset_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        btn_row.addWidget(self.submit_btn)
        btn_row.addWidget(self.reset_btn)
        lay.addLayout(btn_row)

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # 隐藏兼容字段
        self.lng_edit = QLineEdit(); self.lng_edit.setVisible(False)
        self.lat_edit = QLineEdit(); self.lat_edit.setVisible(False)
        self.day_night_switch = QFrame(); self.day_night_switch.setVisible(False)
        # 备注：true_solar_switch 已在「时间校准」卡片构建处指向真实折叠卡，
        # 此处不再用隐藏 QFrame 覆盖，保留属性名供下游读取。

        # 信号
        self.hour_combo.currentIndexChanged.connect(self._on_hour)
        # T3.2 时分 SpinBox 变更 → 反推时辰并回写下拉框（信号屏蔽防循环触发）
        self.hour_spin.valueChanged.connect(self._on_time_spin)
        self.minute_spin.valueChanged.connect(self._on_time_spin)
        self.date_edit.dateChanged.connect(self._refresh_true_solar)
        self.solar_btn.clicked.connect(self._refresh_true_solar)
        self.lunar_btn.clicked.connect(self._refresh_true_solar)
        self._sync_time_label()
        self._refresh_true_solar()
        self.name_edit.textChanged.connect(self._validate)
        self.solar_btn.clicked.connect(lambda: self._cal(True))
        self.lunar_btn.clicked.connect(lambda: self._cal(False))
        self.male_btn.clicked.connect(lambda: self._gen(True))
        self.female_btn.clicked.connect(lambda: self._gen(False))
        self._validate()

    def _label(self, text):
        """生成表单左侧的定宽说明标签，使各行输入框左边缘严格对齐。

        Args:
            text: 标签文字。

        Returns:
            QLabel: 固定宽 42px 的次级灰色标签。
        """
        l = QLabel(text)
        l.setFixedWidth(42)
        l.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            color: {Colors.TEXT2};
            font-family: {Fonts.BODY};
        """)
        return l

    def _on_hour(self, i):
        """时辰下拉框变更槽（由 hour_combo.currentIndexChanged 触发）。

        选定时辰后把时间输入框同步为该时辰的起始整点，省去用户手填；用户仍可
        自行改写分钟。改写后立即重新校验，及时更新提交按钮的可用状态。

        Args:
            i: 时辰索引，0=子时 … 11=亥时，与 HOUR_NAMES / HOUR_RANGES 对应。
        """
        self.selected_hour = i
        s, _ = HOUR_RANGES[i]
        # 同步时 SpinBox 为该时辰起始整点（如子时 23 点）；分保持不变
        self.hour_spin.blockSignals(True)
        self.hour_spin.setValue(s)
        self.hour_spin.blockSignals(False)
        self._sync_time_label()
        self._validate()

    def _on_time_spin(self, *_):
        """T3.2 时分 SpinBox 变更槽：反推时辰并同步下拉框与映射标签。

        用户直接调时分时，时辰下拉框需跟着走，否则两处显示会互相矛盾；
        回写前屏蔽 combo 信号，避免与 _on_hour 形成互相触发的死循环。
        """
        idx = hour_to_index(self.hour_spin.value())
        self.selected_hour = idx
        if self.hour_combo.currentIndex() != idx:
            self.hour_combo.blockSignals(True)
            self.hour_combo.setCurrentIndex(idx)
            self.hour_combo.blockSignals(False)
        self._sync_time_label()
        self._validate()

    def _sync_time_label(self):
        """T3.2 刷新实时时辰映射标签（如「午时 (11:00~13:00)」）。"""
        idx = self.selected_hour
        s, e = HOUR_RANGES[idx]
        self.time_label.setText(
            f'{HOUR_NAMES[idx]} ({s:02d}:00~{e:02d}:00)')
        self._refresh_true_solar()

    def _refresh_true_solar(self):
        """6.1.3 刷新「时间校准」折叠卡显示的原始出生时间与时辰。"""
        if not hasattr(self, '_ts_time_label'):
            return
        cal = '公历' if self.solar_btn.isChecked() else '农历'
        d = self.date_edit.date().toString('yyyy-MM-dd')
        hh = self.hour_spin.value()
        mm = self.minute_spin.value()
        self._ts_time_label.setText(f'{cal} {d} {hh:02d}:{mm:02d}')
        idx = self.selected_hour
        s, e = HOUR_RANGES[idx]
        self._ts_hour_label.setText(f'{HOUR_NAMES[idx]}（{s:02d}:00~{e:02d}:00）')

    def _cal(self, s):
        """历法切换槽（由 solar_btn / lunar_btn 的 clicked 触发）。

        这两个按钮没有加入 QButtonGroup，故须在此手动维持互斥。

        Args:
            s: True 表示选择公历，False 表示农历。
        """
        self.solar_btn.setChecked(s); self.lunar_btn.setChecked(not s)

    def _gen(self, m):
        """性别切换槽（由 male_btn / female_btn 的 clicked 触发）。

        虽然两按钮已加入 gender_grp 按钮组（默认互斥），这里仍显式设置一次，
        以便代码主动调用时（非用户点击）也能保证两个按钮不会同时高亮。

        Args:
            m: True 表示男，False 表示女。
        """
        self.male_btn.setChecked(m); self.female_btn.setChecked(not m)

    def _validate(self):
        """实时校验输入，决定「开始排盘」按钮是否可点。

        触发时机：姓名输入变化、时辰下拉或时分 SpinBox 变化时。
        通过条件：姓名非空（时分由 SpinBox 限定了 0-23 / 0-59，恒为合法值）。
        """
        name = self.name_edit.text().strip()
        self.submit_btn.setEnabled(bool(name))

    def _time_tuple(self):
        """T3.2 读取时分 SpinBox 并做范围兜底，返回 (时, 分)。

        返回:
            tuple[int, int]: 合法时分的二元组
        抛出:
            ValueError: 越界时抛出（SpinBox 正常情况下不会触发，属防御性校验）
        """
        hh, mm = self.hour_spin.value(), self.minute_spin.value()
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise ValueError(f"时间范围错误: {hh:02d}:{mm:02d}")
        return hh, mm

    def get_data(self):
        """获取输入数据。若时间范围非法则抛出 ValueError。"""
        hh, mm = self._time_tuple()

        d = self.date_edit.date()
        year, month, day = d.year(), d.month(), d.day()
        if year < 1900 or year > 2100:
            raise ValueError(f"年份范围错误: {year}（需 1900~2100）")

        return {
            'name': self.name_edit.text().strip(),
            'gender': '男' if self.male_btn.isChecked() else '女',
            'is_lunar': self.lunar_btn.isChecked(),
            'year': year, 'month': month, 'day': day,
            'hour': hh, 'minute': mm, 'hour_index': self.selected_hour,
            'is_early_zi': False,
            'location': self.location_edit.text().strip(),
            'latitude': 30.0, 'longitude': 120.0,
            'solar_time_mode': '自动', 'age_type': '虚岁', 'leap_rule': '归前',
            'pan_type': self.selected_pan_type, 'notes': self.notes_edit.toPlainText(),
        }

    def clear(self):
        """重置表单为初始状态（由主窗口「重置」按钮触发）。

        日期回到今天、时辰回到午时、性别归男、历法归公历，并把「开始排盘」按钮
        重新置灰——姓名已清空，此刻本就不满足提交条件。
        注意：出生地与流派刻意不在重置范围内，属于用户偏好，连续排盘时无需重填。
        """
        self.name_edit.clear()
        self.date_edit.setDate(QDate.currentDate())
        self.male_btn.setChecked(True); self.female_btn.setChecked(False)
        self.solar_btn.setChecked(True); self.lunar_btn.setChecked(False)
        self.hour_combo.setCurrentIndex(6)
        self.hour_spin.setValue(12); self.minute_spin.setValue(0)
        self._sync_time_label()
        self.notes_edit.clear(); self.submit_btn.setEnabled(False)
