"""
梅花易数起卦输入面板 - 极简轻量国风
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QComboBox, QButtonGroup,
                             QSpinBox, QStackedWidget, QScrollArea)
from PySide6.QtCore import Qt
from ui.styles import Stylesheets, Colors, Fonts, Spacing

METHODS = [
    ('time', '时间起卦'), ('number', '数字起卦'),
    ('direction', '方位起卦'), ('text', '文字起卦'),
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

        # 起卦方式
        row = QHBoxLayout(); row.setSpacing(8)
        row.addWidget(self._label('方式'))
        self.method_btns = []
        self.method_grp = QButtonGroup(self)
        self.method_grp.setExclusive(True)
        for i, (v, n) in enumerate(METHODS):
            b = QPushButton(n)
            b.setStyleSheet(Stylesheets.BTN_SWITCH)
            b.setCheckable(True); b.setCursor(Qt.PointingHandCursor)
            self.method_grp.addButton(b, i); row.addWidget(b)
            self.method_btns.append(b)
            b.clicked.connect(lambda _, idx=i: self._on_method(idx))
        self.method_btns[0].setChecked(True)
        lay.addLayout(row)

        # 动态参数
        self.params = QStackedWidget()
        self.params.setStyleSheet("background: transparent;")

        # 时间
        tw = QWidget(); tw.setStyleSheet("background: transparent;")
        tl = QHBoxLayout(tw); tl.setContentsMargins(0,0,0,0); tl.setSpacing(8)
        tl.addWidget(self._label('时间'))
        self.time_edit = QLineEdit()
        self.time_edit.setStyleSheet(Stylesheets.INPUT)
        self.time_edit.setPlaceholderText('留空取当前时辰')
        tl.addWidget(self.time_edit, 1)
        self.params.addWidget(tw)

        # 数字
        nw = QWidget(); nw.setStyleSheet("background: transparent;")
        nl = QHBoxLayout(nw); nl.setContentsMargins(0,0,0,0); nl.setSpacing(8)
        nl.addWidget(self._label('上卦'))
        self.num1 = QSpinBox()
        self.num1.setStyleSheet(Stylesheets.INPUT)
        self.num1.setRange(1, 999); self.num1.setValue(3)
        nl.addWidget(self.num1)
        nl.addWidget(self._label('下卦'))
        self.num2 = QSpinBox()
        self.num2.setStyleSheet(Stylesheets.INPUT)
        self.num2.setRange(1, 999); self.num2.setValue(5)
        nl.addWidget(self.num2)
        self.params.addWidget(nw)

        # 方位
        dw = QWidget(); dw.setStyleSheet("background: transparent;")
        dl = QHBoxLayout(dw); dl.setContentsMargins(0,0,0,0); dl.setSpacing(8)
        dl.addWidget(self._label('方位'))
        self.dir_combo = QComboBox()
        self.dir_combo.setStyleSheet(Stylesheets.COMBO)
        for d in ['正北方','东北方','正东方','东南方','正南方','西南方','正西方','西北方']:
            self.dir_combo.addItem(d)
        dl.addWidget(self.dir_combo, 1)
        self.params.addWidget(dw)

        # 文字
        xw = QWidget(); xw.setStyleSheet("background: transparent;")
        xl = QHBoxLayout(xw); xl.setContentsMargins(0,0,0,0); xl.setSpacing(8)
        xl.addWidget(self._label('文字'))
        self.text_edit = QLineEdit()
        self.text_edit.setStyleSheet(Stylesheets.INPUT)
        self.text_edit.setPlaceholderText('请输入汉字')
        self.text_edit.setText('梅花易数')
        xl.addWidget(self.text_edit, 1)
        self.params.addWidget(xw)

        lay.addWidget(self.params)

        # 占问
        row = QHBoxLayout(); row.setSpacing(8)
        row.addWidget(self._label('占问'))
        self.question = QLineEdit()
        self.question.setStyleSheet(Stylesheets.INPUT)
        self.question.setPlaceholderText('可选，如：事业、感情…')
        row.addWidget(self.question, 1)
        lay.addLayout(row)

        lay.addStretch()

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

    def get_data(self):
        d = {'method': self.selected_method, 'question': self.question.text().strip()}
        if self.selected_method == 'number':
            d['num1'] = self.num1.value()
            d['num2'] = self.num2.value()
            # 数据验证器期望 upper_num/lower_num 字段名
            d['upper_num'] = self.num1.value()
            d['lower_num'] = self.num2.value()
        elif self.selected_method == 'direction': d['direction'] = self.dir_combo.currentText()
        elif self.selected_method == 'text': d['text'] = self.text_edit.text().strip()
        elif self.selected_method == 'time':
            time_str = self.time_edit.text().strip()
            d['time_str'] = time_str
            # 解析时间字符串，格式: "YYYY-MM-DD HH:MM"
            try:
                from datetime import datetime as dt
                parsed = dt.strptime(time_str, '%Y-%m-%d %H:%M')
                d['year'] = parsed.year
                d['month'] = parsed.month
                d['day'] = parsed.day
                d['hour'] = parsed.hour
            except (ValueError, TypeError):
                # 如果解析失败，使用当前时间
                now = dt.now()
                d['year'] = now.year
                d['month'] = now.month
                d['day'] = now.day
                d['hour'] = now.hour
        return d

    def clear(self):
        self.method_btns[0].setChecked(True); self._on_method(0)
        self.question.clear(); self.time_edit.clear()
        self.text_edit.setText('梅花易数')
        self.num1.setValue(3); self.num2.setValue(5)
        self.dir_combo.setCurrentIndex(0)
