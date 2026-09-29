"""
ui/components/xuan_kong_result_panel.py — 玄空飞星结果展示面板

左侧九宫格 Canvas + 右侧文字详情，含导出按钮。
九宫格绘制依据洛书九宫方位：巽离坤 / 震中兑 / 艮坎乾。
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QFrame, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QFont, QColor, QPen, QBrush
from ui.styles import (Colors, Fonts, Spacing, Stylesheets,
                       apply_density, DEFAULT_DENSITY)


def _clear_layout(layout):
    """清空布局中的全部子项（兼容 PySide6：无 takeAll，须逐个 takeAt）。"""
    while layout.count() > 0:
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        del item


# 吉凶盘面着色：吉=朱红 / 凶=深靛蓝 / 中=古金（走 Colors 令牌，勿写裸 hex）
_CELL_COLORS = {
    '吉': Colors.ZHONGYI,
    '凶': Colors.INDIGO_DEEP,
    '中': Colors.GOLD,
}

# 五行背景色：取 Colors 的 *_DARK 版（深色底提亮以保可读性，
# 与 styles.py 五行色单一权威源对齐，勿在面板内另建一份）
_WUXING_COLORS = {
    '木': Colors.WOOD_DARK,
    '火': Colors.FIRE_DARK,
    '土': Colors.EARTH_DARK,
    '金': Colors.METAL_DARK,
    '水': Colors.WATER_DARK,
}


class _GridCanvas(QWidget):
    """洛书九宫格自绘画布：五行背景 + 吉凶着色 + 中宫放大 + 星名标注。

    通过 paintEvent 重绘，避免 QPainter 直接挂在临时 lambda（原实现把 paint
    赋给 widget.paintEvent 不可靠）。支持数据缺失时仅画宫位名占位。

    9.2 升级：鼠标悬停高亮当前宫边框（鎏金发光）+ 显示该宫星数解读 ToolTip。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result = None
        self._hover_idx = -1  # 当前悬停的宫索引（0~8，-1 无）
        self.setFixedSize(380, 380)
        self.setMouseTracking(True)
        self.setStyleSheet(f"background-color: {Colors.BG_DARK}; border-radius: 8px;")

    def set_result(self, result: dict):
        self._result = result
        self._hover_idx = -1
        self.setToolTip('')
        self.update()

    def _cell_geometry(self):
        """返回 (positions, cell_rects)，cell_rects[idx] = QRect 像素矩形。"""
        W, H = self.width(), self.height()
        grid_w, grid_h = W - 8, H - 8
        cx, cy = 4, 4
        cell_w, cell_h = grid_w // 3, grid_h // 3
        positions = ['巽', '离', '坤', '震', '中', '兑', '艮', '坎', '乾']
        rects = []
        for r in range(3):
            for c in range(3):
                idx = r * 3 + c
                x = cx + c * cell_w + 1
                y = cy + r * cell_h + 1
                rects.append((x, y, cell_w - 2, cell_h - 2, positions[idx]))
        return positions, rects

    def _cell_at(self, px, py):
        """返回鼠标坐标命中的宫索引，未命中返回 -1。"""
        _, rects = self._cell_geometry()
        for idx, (x, y, w, h, _) in enumerate(rects):
            if x <= px <= x + w and y <= py <= y + h:
                return idx
        return -1

    def mouseMoveEvent(self, event):  # noqa: N802
        idx = self._cell_at(event.position().x(), event.position().y())
        if idx != self._hover_idx:
            self._hover_idx = idx
            self._update_tooltip(idx)
            self.update()

    def leaveEvent(self, event):  # noqa: N802
        if self._hover_idx != -1:
            self._hover_idx = -1
            self.setToolTip('')
            self.update()

    def _update_tooltip(self, idx):
        if idx < 0 or not self._result:
            self.setToolTip('')
            return
        positions, _ = self._cell_geometry()
        pos_name = positions[idx]
        cell = next((cc for cc in self._result.get('grid', [])
                     if cc.get('position') == pos_name), None)
        if not cell:
            self.setToolTip(pos_name)
            return
        tip = (f"{pos_name}宫\n运星 {cell.get('yun', '-')}（{cell.get('yun_star_name', '')}）\n"
               f"山星 {cell.get('shan', '-')}（{cell.get('shan_star_name', '')}）\n"
               f"向星 {cell.get('xiang', '-')}（{cell.get('xiang_star_name', '')}）\n"
               f"五行 {cell.get('wuxing', '-')} · {cell.get('jixiong', '-')}")
        self.setToolTip(tip)

    def paintEvent(self, event):  # noqa: N802
        from PySide6.QtGui import QPainter, QPen, QBrush, QFont, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        positions, rects = self._cell_geometry()

        cells = (self._result or {}).get('grid', []) if self._result else []

        for idx, (x, y, w, h, pos_name) in enumerate(rects):
            is_center = pos_name == '中'
            is_hover = idx == self._hover_idx

            # 五行背景（中宫略深）
            cell = next((cc for cc in cells if cc.get('position') == pos_name), None)
            wuxing = (cell or {}).get('wuxing', '')
            jixiong = (cell or {}).get('jixiong', '')
            bg_hex = _WUXING_COLORS.get(wuxing, Colors.MO_DARK)
            bg = QColor(bg_hex)
            if is_center:
                bg.setAlpha(200)
            else:
                bg.setAlpha(140)
            painter.fillRect(x, y, w, h, QBrush(bg))

            # 边框：悬停 > 中宫 > 普通
            if is_hover:
                painter.setPen(QPen(QColor(Colors.LIUJIN_LIGHT), 3))
                painter.drawRect(x - 1, y - 1, w + 2, h + 2)
            elif is_center:
                painter.setPen(QPen(QColor(Colors.LIUJIN), 2))
                painter.drawRect(x, y, w, h)
            else:
                painter.setPen(QPen(QColor(Colors.BORDER), 1))
                painter.drawRect(x, y, w, h)

            # 宫位名（左上角小字）
            painter.setFont(QFont(Fonts.BODY, 9, QFont.Bold))
            painter.setPen(QPen(QColor(Colors.TEXT), 1))
            painter.drawText(x + 5, y + 16, pos_name)

            if cell:
                # 星数字（大）：运星用吉凶色，山星向星用浅色
                star_color = QColor(_CELL_COLORS.get(jixiong, Colors.TEXT3))
                yun_v = cell.get('yun', '-')
                shan_v = cell.get('shan', '-')
                xiang_v = cell.get('xiang', '-')

                painter.setFont(QFont(Fonts.TITLE, 22, QFont.Bold))
                painter.setPen(QPen(star_color, 1))
                painter.drawText(x + w // 2 - 8, y + h // 2 + 8, str(yun_v))

                painter.setFont(QFont(Fonts.BODY, 10))
                painter.setPen(QPen(QColor(Colors.TEXT2), 1))
                painter.drawText(x + w // 2 - 16, y + h - 26, f"山{shan_v} 向{xiang_v}")

                # 星名（小字）
                painter.setFont(QFont(Fonts.BODY, 8))
                painter.setPen(QPen(QColor(Colors.TEXT3), 1))
                star_names = f"{cell.get('yun_star_name','')}·{cell.get('shan_star_name','')}·{cell.get('xiang_star_name','')}"
                painter.drawText(x + 5, y + h - 12, star_names[:14])
            else:
                # 占位：仅宫位名居中
                painter.setFont(QFont(Fonts.BODY, 11))
                painter.setPen(QPen(QColor(Colors.TEXT3), 1))
                painter.drawText(x + w // 2 - 8, y + h // 2 + 4, pos_name)

        painter.end()


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
        # M3-1：根布局归 0（与 bazi/meihua/liuren 一致），标题靠默认边距，内容区由内层承载 24
        lay.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        lay.setSpacing(Spacing.S4)

        hdr = QHBoxLayout()
        hdr.setSpacing(Spacing.S2)
        icon = QLabel('⛰')
        icon.setStyleSheet(f"font-size: 13px; color: {Colors.LIUJIN};")
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
        # 圆角 8px 无对应整数令牌（RADIUS_SM_INT=6 / RADIUS_INT=10），
        # 保留裸值以严格零视觉变化；色值已归位 Colors.CANVAS_DARK
        self.grid_canvas.setStyleSheet(
            f"background-color: {Colors.CANVAS_DARK}; border-radius: 8px;")
        grid_lay = QHBoxLayout(self.grid_canvas)
        grid_lay.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        grid_lay.setContentsMargins(Spacing.S3, Spacing.S3, Spacing.S3, Spacing.S3)
        grid_lay.addWidget(QLabel('九宫飞星盘'))
        grid_lay.addStretch()
        # M3-1：九宫格外包一行，左右 24 内边距，与其余面板内容区口径一致
        grid_row = QHBoxLayout()
        grid_row.setContentsMargins(Spacing.S6, Spacing.S0, Spacing.S6, Spacing.S0)
        grid_row.addWidget(self.grid_canvas)
        lay.addLayout(grid_row)

        # 文字详情
        self.detail_area = QScrollArea()
        self.detail_area.setWidgetResizable(True)
        self.detail_area.setStyleSheet(Stylesheets.SCROLL)
        self.detail_content = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_content)
        # M3-1：详情内容区边距/间距唯一入口 apply_density（normal 档 (24,24,24,24)/16）
        apply_density(self.detail_layout, DEFAULT_DENSITY)
        self.detail_area.setWidget(self.detail_content)
        lay.addWidget(self.detail_area)

        lay.addStretch()

        # 底部按钮
        btn_hl = QHBoxLayout()
        # M3-1：底部按钮行左右 24 内边距，与内容区对齐
        btn_hl.setContentsMargins(Spacing.S6, Spacing.S0, Spacing.S6, Spacing.S0)
        btn_hl.setSpacing(Spacing.S2)
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
        _clear_layout(self.detail_layout)
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
        """用独立画布（_GridCanvas + QPainter）重绘九宫格。"""
        layout = self.grid_canvas.layout()
        if layout:
            while layout.count() > 0:
                item = layout.takeAt(0)
                w = item.widget() if item else None
                if w:
                    w.deleteLater()
                del item

        # 使用自绘画布 widget（五行背景 + 吉凶着色 + 中宫放大）
        canvas = _GridCanvas()
        canvas.set_result(result)
        layout.addWidget(canvas, alignment=Qt.AlignHCenter)
        self._grid_canvas_widget = canvas

    def clear(self):
        """清空结果。"""
        self._current_result = None
        _clear_layout(self.detail_layout)
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
