"""
ui/components/xuan_kong_input.py — 玄空飞星输入面板

提供坐向（如'子山午向'）、建造年份、当前年份三个输入项，供主窗口派发排盘。
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame)
from PySide6.QtCore import Qt
from ui.styles import Colors, Fonts, Spacing, Stylesheets


class XuanKongInputPanel(QWidget):
    """玄空飞星输入面板（左侧）。

    收集坐向、建造年份、当前年份后打包 dict，供 service/ai 层排盘。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.BG};")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        # 标题
        hdr = QHBoxLayout()
        icon = QLabel('⛰')
        icon.setStyleSheet(f"font-size: 14px; color: {Colors.LIUJIN};")
        title = QLabel('玄空飞星排盘参数')
        title.setStyleSheet(f"font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD}; "
                            f"color: {Colors.TEXT}; font-family: {Fonts.TITLE};")
        hdr.addWidget(icon)
        hdr.addWidget(title)
        hdr.addStretch()
        lay.addLayout(hdr)

        # 青蓝分割线
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Colors.QINGHUA}; border-radius: 1px;")
        lay.addWidget(sep)

        # 坐向输入
        lay.addWidget(QLabel('坐向（如：子山午向）'))
        self.sui_xiang_edit = QLineEdit('子山午向')
        self.sui_xiang_edit.setStyleSheet(Stylesheets.INPUT)
        lay.addWidget(self.sui_xiang_edit)

        # 建造年份
        lay.addWidget(QLabel('建造年份'))
        self.build_year_edit = QLineEdit('2024')
        self.build_year_edit.setStyleSheet(Stylesheets.INPUT)
        lay.addWidget(self.build_year_edit)

        # 当前年份
        lay.addWidget(QLabel('当前年份（流年叠加）'))
        self.current_year_edit = QLineEdit('2025')
        self.current_year_edit.setStyleSheet(Stylesheets.INPUT)
        lay.addWidget(self.current_year_edit)

        lay.addStretch()

        # 按钮组
        btn_hl = QHBoxLayout()
        btn_hl.setSpacing(8)
        self.submit_btn = QPushButton('起盘')
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        self.reset_btn = QPushButton('重置')
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)
        btn_hl.addWidget(self.submit_btn)
        btn_hl.addWidget(self.reset_btn)
        lay.addLayout(btn_hl)

    # ----- 数据读写契约（与 InputPanel / MeihuaInputPanel 保持一致） -----

    def get_data(self) -> dict:
        """打包当前输入为 dict。"""
        try:
            build = int(self.build_year_edit.text())
        except ValueError:
            build = 2024
        try:
            current = int(self.current_year_edit.text())
        except ValueError:
            current = build
        return {
            'sui_xiang': self.sui_xiang_edit.text().strip() or '子山午向',
            'build_year': build,
            'current_year': current,
        }

    def clear(self):
        """清空输入。"""
        self.sui_xiang_edit.setText('子山午向')
        self.build_year_edit.setText('2024')
        self.current_year_edit.setText('2025')
