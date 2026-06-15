from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QComboBox, QPushButton, QFrame, QCheckBox, QSizePolicy,
                             QSpacerItem, QTextEdit, QGridLayout, QDateEdit,
                             QScrollArea, QButtonGroup)
from PySide6.QtCore import QDate, Qt, QEvent
from PySide6.QtGui import QFont
from ui.styles import Stylesheets, Colors, Fonts, Spacing

HOUR_NAMES = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时',
              '午时', '未时', '申时', '酉时', '戌时', '亥时']
HOUR_RANGES = [(23, 1), (1, 3), (3, 5), (5, 7), (7, 9), (9, 11),
               (11, 13), (13, 15), (15, 17), (17, 19), (19, 21), (21, 23)]

CITIES = [
    ('北京', (116.4074, 39.9042)),
    ('上海', (121.4737, 31.2304)),
    ('广州', (113.2644, 23.1291)),
    ('深圳', (114.0579, 22.5431)),
    ('杭州', (120.1552, 30.2875)),
    ('南京', (118.7969, 32.0603)),
    ('成都', (104.0668, 30.5728)),
    ('武汉', (114.3055, 30.5928)),
    ('西安', (108.948, 34.2631)),
    ('重庆', (106.5516, 29.563)),
    ('天津', (117.2008, 39.0842)),
    ('苏州', (120.6293, 31.3251)),
    ('郑州', (113.6243, 34.7466)),
    ('长沙', (112.9388, 28.228)),
    ('青岛', (120.3316, 36.0671)),
    ('沈阳', (123.4328, 41.8045)),
    ('大连', (121.6147, 38.914)),
    ('宁波', (121.5429, 29.8753)),
    ('无锡', (120.3199, 31.573)),
    ('佛山', (113.1064, 23.0208)),
]

PAN_TYPES = [
    ('bazi', '八字排盘', '四柱八字'),
    ('ziwei', '紫微排盘', '紫微斗数'),
    ('qimen', '奇门遁甲', '奇门遁甲'),
    ('liuyao', '六爻', '六爻占卜'),
    ('fengshui', '风水宅盘', '阳宅风水'),
]


class InputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_validation()

    def init_ui(self):
        self.setStyleSheet(Stylesheets.LEFT_PANEL)
        self.setMinimumWidth(380)
        self.setMaximumWidth(520)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ===== 滚动区域 =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(Stylesheets.SCROLL_AREA)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 滚动内容容器
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        card_padding = int(Spacing.CARD_PADDING.replace('px', ''))
        module_gap = int(Spacing.MODULE_GAP.replace('px', ''))
        scroll_layout.setContentsMargins(card_padding, card_padding, card_padding, card_padding)
        scroll_layout.setSpacing(module_gap)

        # ===== 标题区域 =====
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        title_layout.setAlignment(Qt.AlignLeft)

        title_icon = QLabel('☯')
        title_icon.setStyleSheet(f"font-size: 22px; color: {Colors.PRIMARY};")

        title_label = QLabel('风水排盘参数设置')
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

        # ===== 表单区域 =====
        # 基础时间录入
        time_section = self._create_section_card('基础时间录入', self._create_time_content())
        scroll_layout.addWidget(time_section)

        # 性别选择
        gender_section = self._create_section_card('性别', self._create_gender_content())
        scroll_layout.addWidget(gender_section)

        # 地域信息
        location_section = self._create_section_card('地域信息', self._create_location_content())
        scroll_layout.addWidget(location_section)

        # 排盘类型
        pan_type_section = self._create_section_card('排盘类型', self._create_pan_type_content())
        scroll_layout.addWidget(pan_type_section)

        # 自定义参数
        custom_section = self._create_section_card('自定义参数', self._create_custom_content())
        scroll_layout.addWidget(custom_section)

        # 备注
        notes_section = self._create_section_card('备注（可选）', self._create_notes_content())
        scroll_layout.addWidget(notes_section)

        scroll_layout.addStretch(1)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)

        # ===== 底部固定区域 =====
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

        # 验证提示
        self.validation_hint = QLabel('')
        self.validation_hint.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.DANGER};
            font-family: {Fonts.FAMILY_CN};
            padding: 8px 12px;
            background-color: rgba(196, 92, 72, 0.06);
            border-radius: {Spacing.CONTROL_RADIUS};
            border-left: 3px solid {Colors.DANGER};
        """)
        self.validation_hint.setVisible(False)
        self.validation_hint.setWordWrap(True)
        bottom_layout.addWidget(self.validation_hint)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(14)
        button_layout.setAlignment(Qt.AlignCenter)

        self.reset_btn = QPushButton('重置参数')
        self.reset_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)
        self.reset_btn.setCursor(Qt.PointingHandCursor)

        self.submit_btn = QPushButton('开始排盘')
        self.submit_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setEnabled(False)

        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.submit_btn)

        bottom_layout.addLayout(button_layout)
        main_layout.addWidget(bottom_widget)

    def _create_section_card(self, title, content_widget):
        """创建输入区块卡片"""
        card = QFrame()
        card.setStyleSheet(Stylesheets.SECTION_CARD)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # 标题行：带左侧色条
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

    # ===== 各字段内容构建 =====
    def _create_time_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 公历/农历切换
        calendar_row = QHBoxLayout()
        calendar_row.setSpacing(4)

        self.solar_btn = QPushButton('公历')
        self.solar_btn.setStyleSheet(Stylesheets.BUTTON_SWITCH)
        self.solar_btn.setCheckable(True)
        self.solar_btn.setChecked(True)
        self.solar_btn.setCursor(Qt.PointingHandCursor)

        self.lunar_btn = QPushButton('农历')
        self.lunar_btn.setStyleSheet(Stylesheets.BUTTON_SWITCH)
        self.lunar_btn.setCheckable(True)
        self.lunar_btn.setCursor(Qt.PointingHandCursor)

        calendar_row.addWidget(self.solar_btn)
        calendar_row.addWidget(self.lunar_btn)
        calendar_row.addStretch()

        layout.addLayout(calendar_row)

        # 出生日期
        date_layout = QVBoxLayout()
        date_layout.setSpacing(4)

        date_label = QLabel('出生日期')
        date_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        self.date_edit = QDateEdit()
        self.date_edit.setStyleSheet(Stylesheets.DATE_EDIT)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat('yyyy-MM-dd')

        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)

        layout.addLayout(date_layout)

        # 出生时辰
        hour_layout = QVBoxLayout()
        hour_layout.setSpacing(6)

        hour_label = QLabel('出生时辰')
        hour_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        hour_grid = QGridLayout()
        hour_grid.setSpacing(4)
        hour_grid.setColumnStretch(0, 1)
        hour_grid.setColumnStretch(1, 1)
        hour_grid.setColumnStretch(2, 1)
        hour_grid.setColumnStretch(3, 1)
        hour_grid.setColumnStretch(4, 1)
        hour_grid.setColumnStretch(5, 1)

        self.hour_buttons = []
        self.hour_group = QButtonGroup(self)
        self.hour_group.setExclusive(True)

        for i, name in enumerate(HOUR_NAMES):
            btn = QPushButton(name)
            btn.setStyleSheet(Stylesheets.BUTTON_HOUR)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty('hour_index', i)
            self.hour_group.addButton(btn, i)
            hour_grid.addWidget(btn, i // 6, i % 6)
            self.hour_buttons.append(btn)

        # 默认选中午时
        self.hour_buttons[6].setChecked(True)
        self.selected_hour = 6

        hour_layout.addWidget(hour_label)
        hour_layout.addLayout(hour_grid)

        layout.addLayout(hour_layout)

        # 具体时间
        time_row = QHBoxLayout()
        time_row.setSpacing(8)

        time_label = QLabel('具体时间')
        time_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        self.time_edit = QLineEdit()
        self.time_edit.setStyleSheet(Stylesheets.LINE_EDIT)
        self.time_edit.setPlaceholderText('时:分')
        self.time_edit.setMaximumWidth(100)
        self.time_edit.setText('12:00')

        time_row.addWidget(time_label)
        time_row.addWidget(self.time_edit)
        time_row.addStretch()

        layout.addLayout(time_row)

        return widget

    def _create_gender_content(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.gender_group = QButtonGroup(self)
        self.gender_group.setExclusive(True)

        self.male_btn = QPushButton('♂ 男')
        self.male_btn.setStyleSheet(Stylesheets.GENDER_CARD)
        self.male_btn.setCheckable(True)
        self.male_btn.setChecked(True)
        self.male_btn.setCursor(Qt.PointingHandCursor)
        self.gender_group.addButton(self.male_btn, 0)

        self.female_btn = QPushButton('♀ 女')
        self.female_btn.setStyleSheet(Stylesheets.GENDER_CARD)
        self.female_btn.setCheckable(True)
        self.female_btn.setCursor(Qt.PointingHandCursor)
        self.gender_group.addButton(self.female_btn, 1)

        layout.addWidget(self.male_btn)
        layout.addWidget(self.female_btn)

        return widget

    def _create_location_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 城市选择
        city_row = QHBoxLayout()
        city_row.setSpacing(8)

        self.city_combo = QComboBox()
        self.city_combo.setStyleSheet(Stylesheets.COMBO_BOX)
        self.city_combo.setMinimumWidth(140)
        for city, coords in CITIES:
            self.city_combo.addItem(city, coords)

        self.lat_label = QLabel('')
        self.lat_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        self.lat_label.setMaximumWidth(200)

        city_row.addWidget(self.city_combo)
        city_row.addWidget(self.lat_label)
        city_row.addStretch()

        layout.addLayout(city_row)

        # 经纬度
        coord_row = QHBoxLayout()
        coord_row.setSpacing(8)

        self.lng_edit = QLineEdit()
        self.lng_edit.setStyleSheet(Stylesheets.LINE_EDIT)
        self.lng_edit.setPlaceholderText('经度，如: 116.4074')

        self.lat_edit = QLineEdit()
        self.lat_edit.setStyleSheet(Stylesheets.LINE_EDIT)
        self.lat_edit.setPlaceholderText('纬度，如: 39.9042')

        coord_row.addWidget(self.lng_edit)
        coord_row.addWidget(self.lat_edit)

        layout.addLayout(coord_row)

        self._update_coords_label()

        return widget

    def _create_pan_type_content(self):
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        self.pan_type_buttons = []
        self.pan_type_group = QButtonGroup(self)
        self.pan_type_group.setExclusive(True)

        for i, (value, name, desc) in enumerate(PAN_TYPES):
            btn = QPushButton(name)
            btn.setStyleSheet(Stylesheets.PAN_TYPE_CARD)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty('pan_type', value)
            btn.setMinimumHeight(70)
            self.pan_type_group.addButton(btn, i)
            layout.addWidget(btn, i // 2, i % 2)
            self.pan_type_buttons.append(btn)

        # 默认选中八字排盘
        self.pan_type_buttons[0].setChecked(True)
        self.selected_pan_type = 'bazi'

        return widget

    def _create_custom_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 节气起算方式
        algo_row = self._create_param_row('节气起算方式', ['传统', '现代'])
        layout.addLayout(algo_row)

        # 昼夜时区分割
        day_night_row = self._create_switch_row('昼夜时区分割')
        layout.addLayout(day_night_row)

        # 真太阳时校正
        solar_row = self._create_switch_row('真太阳时校正')
        layout.addLayout(solar_row)

        return widget

    def _create_notes_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(Stylesheets.TEXT_EDIT)
        self.notes_edit.setPlaceholderText('请输入特殊条件说明或备注信息...')
        self.notes_edit.setMaximumHeight(80)

        layout.addWidget(self.notes_edit)

        return widget

    def _create_param_row(self, label_text, items):
        """创建参数行（标签 + 选项按钮）"""
        row = QHBoxLayout()
        row.setSpacing(10)

        label = QLabel(label_text)
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        label.setMinimumWidth(90)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        group = QButtonGroup(self)
        group.setExclusive(True)

        for idx, item in enumerate(items):
            btn = QPushButton(item)
            btn.setStyleSheet(Stylesheets.BUTTON_SWITCH)
            btn.setCheckable(True)
            if item == '传统':
                btn.setChecked(True)
            btn.setCursor(Qt.PointingHandCursor)
            group.addButton(btn, idx)
            btn_layout.addWidget(btn)

        row.addWidget(label)
        row.addLayout(btn_layout)
        row.addStretch()

        return row

    def _create_switch_row(self, label_text):
        """创建开关行"""
        row = QHBoxLayout()
        row.setSpacing(10)

        label = QLabel(label_text)
        label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        checkbox = QCheckBox()
        checkbox.setStyleSheet(Stylesheets.TOGGLE_SWITCH)
        if label_text == '昼夜时区分割':
            checkbox.setChecked(True)
            self.day_night_switch = checkbox
        elif label_text == '真太阳时校正':
            checkbox.setChecked(False)
            self.true_solar_switch = checkbox

        row.addWidget(label)
        row.addStretch()
        row.addWidget(checkbox)

        return row

    # ===== 事件处理 =====
    def _on_hour_selected(self, index):
        self.selected_hour = index
        self._update_time_from_hour()
        self.validate_input()

    def _on_pan_type_selected(self, value):
        self.selected_pan_type = value

    def _update_coords_label(self):
        coords = self.city_combo.currentData()
        if coords:
            lat, lng = coords
            self.lat_label.setText(f'坐标: {lat:.4f}, {lng:.4f}')
            self.lng_edit.setText(str(lng))
            self.lat_edit.setText(str(lat))
        else:
            self.lat_label.setText('')

    def _update_time_from_hour(self):
        hour_index = self.selected_hour
        start, end = HOUR_RANGES[hour_index]
        if start == 23:
            self.time_edit.setText('23:00')
        else:
            self.time_edit.setText(f"{start:02d}:00")

    # ===== 验证 =====
    def setup_validation(self):
        self.city_combo.currentIndexChanged.connect(self._update_coords_label)
        self.submit_btn.clicked.connect(self.on_submit_clicked)
        self.reset_btn.clicked.connect(self.clear)
        self.male_btn.clicked.connect(lambda: self._on_gender_toggle(True))
        self.female_btn.clicked.connect(lambda: self._on_gender_toggle(False))
        self.solar_btn.clicked.connect(lambda: self._on_calendar_toggle(True))
        self.lunar_btn.clicked.connect(lambda: self._on_calendar_toggle(False))
        self.time_edit.textChanged.connect(self._on_time_changed)
        self.hour_group.idClicked.connect(self._on_hour_selected)
        self.pan_type_group.idClicked.connect(lambda idx: self._on_pan_type_selected(PAN_TYPES[idx][0]))

    def _on_gender_toggle(self, is_male):
        self.male_btn.setChecked(is_male)
        self.female_btn.setChecked(not is_male)

    def _on_calendar_toggle(self, is_solar):
        self.solar_btn.setChecked(is_solar)
        self.lunar_btn.setChecked(not is_solar)

    def _on_time_changed(self, text):
        self.validate_input()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusOut:
            if obj == self.time_edit:
                self.validate_input()
        return super().eventFilter(obj, event)

    def validate_input(self):
        time_text = self.time_edit.text().strip()

        if not time_text:
            self.validation_hint.setText('请输入出生时间')
            self.validation_hint.setVisible(True)
            self.submit_btn.setEnabled(False)
            return False

        try:
            hh, mm = map(int, time_text.split(':'))
            if hh < 0 or hh > 23 or mm < 0 or mm > 59:
                self.validation_hint.setText('时间格式错误，请输入有效的时分（00:00-23:59）')
                self.validation_hint.setVisible(True)
                self.submit_btn.setEnabled(False)
                return False
        except:
            self.validation_hint.setText('时间格式错误，请使用 时:分 格式')
            self.validation_hint.setVisible(True)
            self.submit_btn.setEnabled(False)
            return False

        self.validation_hint.setVisible(False)
        self.submit_btn.setEnabled(True)
        return True

    def on_submit_clicked(self):
        if not self.validate_input():
            pass

    def get_data(self):
        hour_index = self.selected_hour

        try:
            hh, mm = map(int, self.time_edit.text().split(':'))
        except:
            hh, mm = 12, 0

        date = self.date_edit.date()
        city, coords = CITIES[self.city_combo.currentIndex()]

        return {
            'name': '',
            'gender': '男' if self.male_btn.isChecked() else '女',
            'is_lunar': self.lunar_btn.isChecked(),
            'year': date.year(),
            'month': date.month(),
            'day': date.day(),
            'hour': hh,
            'minute': mm,
            'hour_index': hour_index,
            'is_early_zi': False,
            'city': city,
            'latitude': coords[1],
            'longitude': coords[0],
            'solar_time_mode': '自动',
            'age_type': '虚岁',
            'leap_rule': '归前',
            'pan_type': self.selected_pan_type,
            'notes': self.notes_edit.toPlainText(),
        }

    def clear(self):
        self.date_edit.setDate(QDate.currentDate())
        self.male_btn.setChecked(True)
        self.female_btn.setChecked(False)
        self.solar_btn.setChecked(True)
        self.lunar_btn.setChecked(False)
        self._on_hour_selected(6)
        self.time_edit.setText('12:00')
        self.city_combo.setCurrentIndex(0)
        self._update_coords_label()
        self.notes_edit.clear()
        self.validation_hint.setVisible(False)
        self.submit_btn.setEnabled(False)
