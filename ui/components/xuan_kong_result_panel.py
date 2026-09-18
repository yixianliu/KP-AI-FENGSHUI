"""
ui/components/xuan_kong_result_panel.py — 玄空飞星结果展示面板

左侧九宫格 Canvas + 右侧文字详情，含导出按钮。
九宫格绘制依据洛书九宫方位：巽离坤 / 震中兑 / 艮坎乾。
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QFrame, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QFont, QColor, QPen, QBrush
from ui.styles import Colors, Fonts, Spacing, Stylesheets


_CELL_COLORS = {
    '吉': '#8b0000',   # 朱红
    '凶': '#4a5a8a',   # 靛蓝（深色底可读）
    '中': '#c9a227',   # 古金
}


class XuanKongResultPanel(QWidget):
    """玄空飞星排盘结果面板（右侧）。

    顶部九宫格 Canvas，下方九宫详情文本。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_result = None
        self.setStyleSheet(f"background-color: {Colors.BG};")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)

        hdr = QHBoxLayout()
        hdr.setSpacing(8)
        icon = QLabel('⛰')
        icon.setStyleSheet(f"font-size: 14px; color: {Colors.LIUJIN};")
        title = QLabel('玄空飞星排盘结果')
        title.setStyleSheet(f"font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD}; "
                            f"color: {Colors.TEXT}; font-family: {Fonts.TITLE};")
        hdr.addWidget(icon)
        hdr.addWidget(title)
        hdr.addStretch()
        lay.addLayout(hdr)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Colors.QINGHUA}; border-radius: 1px;")
        lay.addWidget(sep)

        # 九宫格画布
        self.grid_canvas = QFrame()
        self.grid_canvas.setStyleSheet("background-color: #0f0f1a; border-radius: 8px;")
        grid_lay = QHBoxLayout(self.grid_canvas)
        grid_lay.setContentsMargins(12, 12, 12, 12)
        grid_lay.addWidget(QLabel('九宫飞星盘'))
        grid_lay.addStretch()
        lay.addWidget(self.grid_canvas)

        # 文字详情
        self.detail_area = QScrollArea()
        self.detail_area.setWidgetResizable(True)
        self.detail_area.setStyleSheet(Stylesheets.SCROLL)
        self.detail_content = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_content)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_layout.setSpacing(6)
        self.detail_area.setWidget(self.detail_content)
        lay.addWidget(self.detail_area)

        lay.addStretch()

        # 底部按钮
        btn_hl = QHBoxLayout()
        btn_hl.setSpacing(8)
        self.refresh_btn = QPushButton('刷新')
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        btn_hl.addWidget(self.refresh_btn)
        btn_hl.addStretch()
        lay.addLayout(btn_hl)

        self._redraw_grid()

    def display_result(self, result: dict):
        """渲染排盘结果到面板。

        Args:
            result: XuanKongCalculator.calculate 返回的字典
        """
        self._current_result = result
        self.detail_layout.takeAll()
        # 基本信息
        self._add_section('基本信息')
        self._add_para(f"坐向：{result.get('sui_xiang', '-')}")
        self._add_para(f"运序：{result.get('yun', '-')}（{result.get('yun_info', {}).get('start', '')}-{result.get('yun_info', {}).get('end', '')}年）")
        self._add_para(f"坐山：{result.get('mount', '-')} → 向首：{result.get('facing', '-')}")
        if result.get('has_tigua'):
            self._add_para(f"替卦：坐山={result.get('mount_tigua', '')}，向首={result.get('facing_tigua', '')}")
        self._add_para(f"建造年份：{result.get('build_year', '-')}, 当前年份：{result.get('current_year', '-')}")
        self._add_divider()

        # 九宫详情
        self._add_section('九宫飞星分布')
        for cell in result.get('grid', []):
            pos = cell.get('position', '')
            yun_v = cell.get('yun', '-')
            shan_v = cell.get('shan', '-')
            xiang_v = cell.get('xiang', '-')
            wx = cell.get('wuxing', '')
            jx = cell.get('jixiong', '')
            self._add_para(f"{pos}: 运星={yun_v} 山星={shan_v} 向星={xiang_v} [{wx}{jx}]")
        self._add_divider()

        liunian = result.get('liunian', [])
        if liunian:
            self._add_section(f"流年飞星叠加（{result.get('current_year', '')}）")
            for item in liunian[:9]:
                pos = item.get('position', '')
                star = item.get('star', '-')
                self._add_para(f"{pos}: {star}")

        # 九宫格重绘
        self._redraw_grid(result)

    def _add_section(self, title: str):
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; font-weight: {Fonts.W_BOLD}; "
                          f"color: {Colors.LIUJIN}; font-family: {Fonts.TITLE}; margin-top: 6px;")
        self.detail_layout.addWidget(lbl)

    def _add_para(self, text: str):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2}; "
                          f"font-family: {Fonts.BODY};")
        self.detail_layout.addWidget(lbl)

    def _add_divider(self):
        d = QFrame()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background-color: {Colors.LIUJIN_LIGHT}; border-radius: 1px;")
        self.detail_layout.addWidget(d)

    def _redraw_grid(self, result=None):
        """用独立画布（QWidget + QPainter）重绘九宫格。"""
        layout = self.grid_canvas.layout()
        if layout:
            # 先清空 grid_canvas 中的内容
            # 用 count() 判断而非 while layout()（layout 对象始终为真值，会死循环）
            while layout.count() > 0:
                item = layout.takeAt(0)
                w = item.widget() if item else None
                if w:
                    w.deleteLater()
                # QWidgetItem 没有 deleteLater 方法；takeAt 已将其从 layout 移除，
                # C++ 端随 GC 自动回收，无需手动删除。

        # 创建画布 widget
        canvas_w, canvas_h = 360, 360
        canvas = QWidget()
        canvas.setFixedSize(canvas_w, canvas_h)
        canvas.setStyleSheet("background-color: #0f0f1a; border-radius: 8px;")

        def paint(event):
            painter = QPainter(canvas)
            painter.setRenderHint(QPainter.Antialiasing)
            cw = canvas_w // 3
            ch = canvas_h // 3
            gap = 2
            # 画 3x3 网格
            for r in range(3):
                for c in range(3):
                    x = c * cw + gap // 2
                    y = r * ch + gap // 2
                    w = cw - gap
                    h = ch - gap
                    painter.setPen(QPen(QColor(Colors.LIUJIN_LIGHT), 1))
                    painter.drawRect(x, y, w, h)
                    # 九宫位置名
                    positions = ['巽', '离', '坤', '震', '中', '兑', '艮', '坎', '乾']
                    idx = r * 3 + c
                    pos_name = positions[idx]
                    # 中宫高亮
                    if pos_name == '中':
                        painter.fillRect(x, y, w, h, QBrush(QColor(Colors.CARD_HOVER)))
                    # 填充九宫数据
                    if result:
                        cells = result.get('grid', [])
                        cell = next((c for c in cells if c.get('position') == pos_name), None)
                        if cell:
                            jx = cell.get('jixiong', '')
                            color = QColor(_CELL_COLORS.get(jx, Colors.TEXT3))
                            painter.setPen(QPen(color, 2))
                            yun_v = cell.get('yun', '-')
                            shan_v = cell.get('shan', '-')
                            xiang_v = cell.get('xiang', '-')
                            painter.setFont(QFont(Fonts.BODY, 11, QFont.Bold))
                            painter.drawText(x + 4, y + ch // 2 - 6,
                                             f"运{yun_v} 山{shan_v} 向{xiang_v}")
                            painter.setFont(QFont(Fonts.BODY, 8))
                            painter.drawText(x + 4, y + ch // 2 + 10, pos_name)
                    else:
                        painter.setFont(QFont(Fonts.BODY, 9))
                        painter.setPen(QPen(Colors.TEXT3, 1))
                        painter.drawText(x + w // 2 - 10, y + h // 2 + 3, pos_name)
            painter.end()

        canvas.paintEvent = paint
        layout.addWidget(canvas)

    def clear(self):
        """清空结果。"""
        self._current_result = None
        self.detail_layout.takeAll()
        self._redraw_grid()

    def get_chart_data_for_ai(self) -> dict:
        """返回当前排盘数据，供 AI 解读使用。"""
        return self._current_result or {}


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = XuanKongResultPanel()
    w.show()
    sys.exit(app.exec())
