"""
大六壬起课输入面板
提供：占问、历法/时间（默认当前时辰）、占时（可覆盖）、起课方式（九宗门）。
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QComboBox, QButtonGroup,
                             QScrollArea, QGroupBox, QGridLayout)
from PySide6.QtCore import Qt
from ui.styles import Stylesheets, Colors, Fonts
from core.liuren import GATE_METHODS, GATE_NAMES

ZHI_LIST = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']


class LiurenInputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_method = 'auto'
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
        icon = QLabel('☵')
        icon.setStyleSheet(f"font-size: 14px; color: {Colors.LIUJIN};")
        title = QLabel('大六壬参数')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT}; font-family: {Fonts.TITLE};
        """)
        hdr.addWidget(icon); hdr.addWidget(title); hdr.addStretch()
        lay.addLayout(hdr)

        div = QFrame(); div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {Colors.QINGHUA_LIGHT};")
        lay.addWidget(div)

        # 占问分类选择
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

        # 时间设置
        time_group = QGroupBox('起课时间')
        time_lay = QGridLayout(); time_lay.setSpacing(8)
        time_lay.addWidget(QLabel('历法:'), 0, 0)
        self.calendar_combo = QComboBox()
        self.calendar_combo.addItems(['公历', '农历'])
        time_lay.addWidget(self.calendar_combo, 0, 1)
        time_lay.addWidget(QLabel('时间:'), 1, 0)
        self.time_edit = QLineEdit()
        self.time_edit.setStyleSheet(Stylesheets.INPUT)
        self.time_edit.setPlaceholderText('留空取当前时辰 (格式: YYYY-MM-DD HH:MM)')
        time_lay.addWidget(self.time_edit, 1, 1, 1, 2)
        time_lay.setColumnStretch(2, 1)
        time_group.setLayout(time_lay)
        lay.addWidget(time_group)

        # 占时覆盖（可选）
        zs_row = QHBoxLayout(); zs_row.setSpacing(8)
        zs_row.addWidget(self._label('占时'))
        self.zhan_shi_combo = QComboBox()
        self.zhan_shi_combo.setStyleSheet(Stylesheets.COMBO)
        self.zhan_shi_combo.addItem('自动(从时辰)')
        for z in ZHI_LIST:
            self.zhan_shi_combo.addItem(z)
        zs_row.addWidget(self.zhan_shi_combo, 1)
        lay.addLayout(zs_row)

        # 起课方式（九宗门）
        method_group = QGroupBox('起课方式（三传取用法）')
        method_lay = QGridLayout(); method_lay.setSpacing(8)
        self.method_btns = []
        self.method_grp = QButtonGroup(self)
        self.method_grp.setExclusive(True)
        for i, m in enumerate(GATE_METHODS):
            b = QPushButton(GATE_NAMES[m])
            b.setStyleSheet(Stylesheets.BTN_SWITCH)
            b.setCheckable(True); b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(34)
            self.method_grp.addButton(b, i)
            r, c = divmod(i, 2)
            method_lay.addWidget(b, r, c)
            self.method_btns.append(b)
            b.clicked.connect(lambda _, idx=i: self._on_method(idx))
        method_lay.setColumnStretch(0, 1)
        method_lay.setColumnStretch(1, 1)
        self.method_btns[0].setChecked(True)
        method_group.setLayout(method_lay)
        lay.addWidget(method_group)

        lay.addStretch()

        # 按钮
        btn_row = QHBoxLayout(); btn_row.setSpacing(12)
        self.submit_btn = QPushButton('起课')
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
        self.selected_method = GATE_METHODS[i]

    def get_data(self):
        d = {'method': self.selected_method, 'question': self.question.text().strip()}

        cat_idx = self.question_category.currentIndex()
        if cat_idx > 0:
            d['question_category'] = self.question_category.itemText(cat_idx)

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
        d['calendar_type'] = self.calendar_combo.currentText()

        zs = self.zhan_shi_combo.currentText()
        if zs != '自动(从时辰)':
            d['zhan_shi'] = zs

        return d

    def clear(self):
        self.method_btns[0].setChecked(True); self._on_method(0)
        self.question.clear()
        self.question_category.setCurrentIndex(0)
        self.time_edit.clear()
        self.calendar_combo.setCurrentIndex(0)
        self.zhan_shi_combo.setCurrentIndex(0)
