"""
左侧输入面板 - 极简轻量国风
垂直表单 · 圆角控件 · 朱砂红主按钮 · 白底灰框副按钮
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QComboBox, QPushButton, QFrame, QButtonGroup,
                             QDateEdit, QTextEdit, QScrollArea, QSpinBox)
from PySide6.QtCore import QDate, Qt
from ui.styles import Stylesheets, Colors, Fonts, Spacing

HOUR_NAMES = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时',
              '午时', '未时', '申时', '酉时', '戌时', '亥时']
HOUR_RANGES = [(23,1),(1,3),(3,5),(5,7),(7,9),(9,11),(11,13),(13,15),(15,17),(17,19),(19,21),(21,23)]

PAN_TYPES = [
    ('bazi','八字四柱'),('ziwei','紫微斗数'),('qimen','奇门遁甲'),
    ('liuyao','六爻纳甲'),('yangzhai','阳宅风水'),('yinning','阴宅风水'),
]


class InputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_hour = 6
        self.selected_pan_type = 'bazi'
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
        icon = QLabel('☯')
        icon.setStyleSheet(f"font-size: 14px; color: {Colors.LIUJIN};")
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

        # ===== 姓名 =====
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self._label('姓名'))
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(Stylesheets.INPUT)
        self.name_edit.setPlaceholderText('请输入姓名')
        row.addWidget(self.name_edit, 1)
        lay.addLayout(row)

        # ===== 历法 =====
        row = QHBoxLayout()
        row.setSpacing(8)
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
        lay.addLayout(row)

        # ===== 日期 =====
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self._label('日期'))
        self.date_edit = QDateEdit()
        self.date_edit.setStyleSheet(Stylesheets.DATE)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        row.addWidget(self.date_edit, 1)
        lay.addLayout(row)

        # ===== 时辰 + 时间 =====
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self._label('时辰'))
        self.hour_combo = QComboBox()
        self.hour_combo.setStyleSheet(Stylesheets.COMBO)
        for i, n in enumerate(HOUR_NAMES):
            self.hour_combo.addItem(f'{n} ({HOUR_RANGES[i][0]:02d}:00~{HOUR_RANGES[i][1]:02d}:00)', i)
        self.hour_combo.setCurrentIndex(6)
        row.addWidget(self.hour_combo, 1)
        self.time_edit = QLineEdit()
        self.time_edit.setStyleSheet(Stylesheets.INPUT)
        self.time_edit.setPlaceholderText('时:分')
        self.time_edit.setFixedWidth(70)
        self.time_edit.setText('12:00')
        row.addWidget(self.time_edit)
        lay.addLayout(row)

        # ===== 出生地（手动文本，可经 AI 解析经纬度/时区）=====
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self._label('出生地'))
        self.location_edit = QLineEdit()
        self.location_edit.setStyleSheet(Stylesheets.INPUT)
        self.location_edit.setPlaceholderText('如：北京市朝阳区 / 纽约 / 洛杉矶（留空则按默认经度 120°E 计算）')
        row.addWidget(self.location_edit, 1)
        lay.addLayout(row)

        # ===== 性别 =====
        row = QHBoxLayout()
        row.setSpacing(8)
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
        lay.addLayout(row)

        # 注：原「类型」选择按钮组已移除——八字标签仅支持八字四柱，
        # 旧代码列出的紫微斗数/奇门遁甲/六爻/风水等未实现，属误导性选项。

        # ===== 排盘类型（当前标签即八字排盘，类型固定，避免误导） =====
        row = QHBoxLayout()
        row.setSpacing(8)
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
        lay.addLayout(row)

        # ===== 流派 =====
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self._label('流派'))
        self.school_combo = QComboBox()
        self.school_combo.setStyleSheet(Stylesheets.COMBO)
        self.school_combo.addItems(['子平真诠', '滴天髓', '三命通会'])
        row.addWidget(self.school_combo, 1)
        lay.addLayout(row)

        # ===== 备注 =====
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self._label('备注'))
        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(Stylesheets.TEXT_EDIT)
        self.notes_edit.setPlaceholderText('可选补充…')
        self.notes_edit.setFixedHeight(60)
        row.addWidget(self.notes_edit, 1)
        lay.addLayout(row)

        lay.addStretch()

        # ===== 按钮 =====
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
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
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # 隐藏兼容字段
        self.lng_edit = QLineEdit(); self.lng_edit.setVisible(False)
        self.lat_edit = QLineEdit(); self.lat_edit.setVisible(False)
        self.day_night_switch = QFrame(); self.day_night_switch.setVisible(False)
        self.true_solar_switch = QFrame(); self.true_solar_switch.setVisible(False)

        # 信号
        self.hour_combo.currentIndexChanged.connect(self._on_hour)
        self.time_edit.textChanged.connect(self._validate)
        self.name_edit.textChanged.connect(self._validate)
        self.solar_btn.clicked.connect(lambda: self._cal(True))
        self.lunar_btn.clicked.connect(lambda: self._cal(False))
        self.male_btn.clicked.connect(lambda: self._gen(True))
        self.female_btn.clicked.connect(lambda: self._gen(False))
        self._validate()

    def _label(self, text):
        l = QLabel(text)
        l.setFixedWidth(42)
        l.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            color: {Colors.TEXT2};
            font-family: {Fonts.BODY};
        """)
        return l

    def _on_hour(self, i):
        self.selected_hour = i
        s, _ = HOUR_RANGES[i]
        self.time_edit.setText(f'{s:02d}:00')
        self._validate()

    def _cal(self, s):
        self.solar_btn.setChecked(s); self.lunar_btn.setChecked(not s)

    def _gen(self, m):
        self.male_btn.setChecked(m); self.female_btn.setChecked(not m)

    def _validate(self):
        name = self.name_edit.text().strip()
        t = self.time_edit.text().strip()
        if not name or not t:
            self.submit_btn.setEnabled(False)
            return
        try:
            h, m = map(int, t.split(':'))
            self.submit_btn.setEnabled(0 <= h <= 23 and 0 <= m <= 59)
        except:
            self.submit_btn.setEnabled(False)

    def get_data(self):
        """获取输入数据。若时间格式非法则直接抛出 ValueError，不调用方做阻断。"""
        t = self.time_edit.text().strip()
        try:
            hh, mm = map(int, t.split(':'))
            if not (0 <= hh <= 23 and 0 <= mm <= 59):
                raise ValueError(f"时间格式或范围错误: {t}")
        except ValueError as e:
            raise ValueError(f"时间格式错误（需 HH:MM，00:00~23:59）: {e}") from e

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
        self.name_edit.clear()
        self.date_edit.setDate(QDate.currentDate())
        self.male_btn.setChecked(True); self.female_btn.setChecked(False)
        self.solar_btn.setChecked(True); self.lunar_btn.setChecked(False)
        self.hour_combo.setCurrentIndex(6); self.time_edit.setText('12:00')
        self.notes_edit.clear(); self.submit_btn.setEnabled(False)
