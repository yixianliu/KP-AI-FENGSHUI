"""
ui/components/xuan_kong_input.py — 玄空飞星输入面板

提供坐向（如'子山午向'）、建造年份、当前年份三个输入项，供主窗口派发排盘。
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from ui.styles import Colors, Fonts, Spacing, Stylesheets

import math

# T3.5 二十四山（自正北「子」起顺时针一周，每山占 15°）
# 顺序依据传统罗盘：子癸丑艮寅甲卯乙辰巽巳丙午丁未坤申庚酉辛戌乾亥壬
MOUNTAINS_24 = [
    '子', '癸', '丑', '艮', '寅', '甲', '卯', '乙', '辰', '巽',
    '巳', '丙', '午', '丁', '未', '坤', '申', '庚', '酉', '辛',
    '戌', '乾', '亥', '壬',
]
_SECTOR_DEG = 360.0 / 24  # 每山 15°


def _sector_range(index: int):
    """返回某山的度数区间 (起, 止)，以正北为 0°、顺时针递增。

    Args:
        index: 山在 MOUNTAINS_24 中的下标（0=子）

    Returns:
        tuple[float, float]: (起始角, 结束角)，取值 0~360
    """
    center = index * _SECTOR_DEG
    return (center - _SECTOR_DEG / 2) % 360, (center + _SECTOR_DEG / 2) % 360


def _opposite_mountain(name: str) -> str:
    """返回与某山正对（相差 180°）的向山名，用于拼「X山Y向」。

    Args:
        name: 坐山名（如 '子'）

    Returns:
        str: 正对山名（如 '午'）；不在表中时原样返回
    """
    if name in MOUNTAINS_24:
        return MOUNTAINS_24[(MOUNTAINS_24.index(name) + 12) % 24]
    return name


class _Compass24(QWidget):
    """T3.5 二十四山环形罗盘选择器（QPainter 自绘）。

    外圈二十四山均分 15°，中宫留白；点击某山即选为「坐山」，
    并自动取正对之山为「向山」，通过 mountain_selected 信号抛出。
    """

    mountain_selected = Signal(str, str)  # (坐山, 向山)

    def __init__(self, size: int = 210, parent=None):
        super().__init__(parent)
        self._size = size
        self._selected = '子'
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip('点击罗盘上的山向即可选定坐向（正对之山自动为向山）')

    def set_selected(self, name: str):
        """外部同步选中态（如手工改写输入框时）。"""
        if name != self._selected:
            self._selected = name
            self.update()

    def _polar(self, radius, az_deg):
        """方位角 → 画布坐标（正北 0°，顺时针，屏幕 y 轴向下）。"""
        a = math.radians(az_deg)
        return self.width() / 2 + radius * math.sin(a), self.height() / 2 - radius * math.cos(a)

    def paintEvent(self, event):  # noqa: N802（Qt 命名）
        """绘制罗盘：外圈、二十四山分界线与山名、选中扇区高亮、中宫。"""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        cx, cy = self.width() / 2, self.height() / 2
        r_out = min(cx, cy) - 4
        r_in = r_out * 0.52

        # 底盘
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(Colors.BG_DARK))
        p.drawEllipse(cx - r_out, cy - r_out, r_out * 2, r_out * 2)

        # 选中扇区高亮（多边形近似扇形，避开 Qt 角度系换算的坑）
        sel_idx = MOUNTAINS_24.index(self._selected) if self._selected in MOUNTAINS_24 else 0
        start_az = sel_idx * _SECTOR_DEG - _SECTOR_DEG / 2
        pts = [(cx, cy)]
        step = 3
        for k in range(int(_SECTOR_DEG / step) + 1):
            pts.append(self._polar(r_out - 2, start_az + k * step))
        pts.append((cx, cy))
        p.setBrush(QColor(Colors.LIUJIN_GLOW))
        p.setPen(Qt.NoPen)
        from PySide6.QtGui import QPolygonF
        from PySide6.QtCore import QPointF
        p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))

        # 外圈与中宫圈
        p.setPen(QPen(QColor(Colors.QINGHUA), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(cx - r_out, cy - r_out, r_out * 2, r_out * 2)
        p.setPen(QPen(QColor(Colors.BORDER), 1))
        p.drawEllipse(cx - r_in, cy - r_in, r_in * 2, r_in * 2)

        # 二十四山：分界线 + 山名
        f = QFont(Fonts.TITLE)
        f.setPixelSize(11)
        p.setFont(f)
        for i, name in enumerate(MOUNTAINS_24):
            az = i * _SECTOR_DEG
            # 分界线（每山边界）
            edge = az - _SECTOR_DEG / 2
            x1, y1 = self._polar(r_in, edge)
            x2, y2 = self._polar(r_out, edge)
            p.setPen(QPen(QColor(Colors.DIVIDER), 1))
            p.drawLine(x1, y1, x2, y2)

            # 山名（选中用鎏金加粗）
            is_sel = (name == self._selected)
            tx, ty = self._polar((r_in + r_out) / 2, az)
            p.setPen(QColor(Colors.LIUJIN if is_sel else Colors.TEXT2))
            if is_sel:
                f2 = QFont(f)
                f2.setBold(True)
                p.setFont(f2)
            else:
                p.setFont(f)
            p.drawText(int(tx - 9), int(ty - 8), 18, 16, Qt.AlignCenter, name)

        # 中宫：显示当前坐向
        p.setPen(QColor(Colors.LIUJIN))
        f3 = QFont(Fonts.TITLE)
        f3.setPixelSize(15)
        f3.setBold(True)
        p.setFont(f3)
        p.drawText(int(cx - r_in), int(cy - 14), int(r_in * 2), 28,
                   Qt.AlignCenter, self._selected)
        p.end()

    def mousePressEvent(self, event):  # noqa: N802（Qt 命名）
        """点击定位山向：由点击点反算方位角 → 山下标 → 抛出坐山/向山。"""
        cx, cy = self.width() / 2, self.height() / 2
        dx = event.position().x() - cx
        dy = cy - event.position().y()  # 屏幕 y 向下，转换为向北为正
        radius = math.hypot(dx, dy)
        r_out = min(cx, cy) - 4
        if radius > r_out or radius < r_out * 0.52:
            return  # 落在盘外或中宫内，忽略
        az = math.degrees(math.atan2(dx, dy)) % 360
        idx = int((az + _SECTOR_DEG / 2) % 360 // _SECTOR_DEG)
        zuo = MOUNTAINS_24[idx]
        self.set_selected(zuo)
        self.mountain_selected.emit(zuo, _opposite_mountain(zuo))


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
        lay.setSpacing(Spacing.S4)

        # 标题
        hdr = QHBoxLayout()
        hdr.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        icon = QLabel('⛰')
        icon.setStyleSheet(f"font-size: 13px; color: {Colors.LIUJIN};")
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

        # 坐向输入（T3.5：环形罗盘点选 + 文本框手工输入，二者双向联动）
        lay.addWidget(QLabel('坐向（点击罗盘选山，或直接输入如：子山午向）'))

        compass_row = QHBoxLayout()
        compass_row.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        compass_row.addStretch()
        self.compass = _Compass24(size=210)
        self.compass.mountain_selected.connect(self._on_compass_pick)
        compass_row.addWidget(self.compass)
        compass_row.addStretch()
        lay.addLayout(compass_row)

        self.sui_xiang_edit = QLineEdit('子山午向')
        self.sui_xiang_edit.setStyleSheet(Stylesheets.INPUT)
        self.sui_xiang_edit.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.sui_xiang_edit)

        # 当前选中山的度数范围提示
        self.mnt_info = QLabel('')
        self.mnt_info.setAlignment(Qt.AlignCenter)
        self.mnt_info.setStyleSheet(
            f"font-size:{Fonts.SZ_MICRO}; color:{Colors.LIUJIN}; font-family:{Fonts.BODY};")
        lay.addWidget(self.mnt_info)
        self._sync_mnt_info()
        # 手工改写文本框时，反向同步罗盘高亮
        self.sui_xiang_edit.textChanged.connect(self._on_sui_xiang_changed)

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
        btn_hl.setSpacing(Spacing.S2)
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

    def _on_compass_pick(self, zuo: str, xiang: str):
        """T3.5 罗盘点选槽：把「X山Y向」写回输入框。

        刻意只改输入框文本而不另存状态：get_data 仍从 sui_xiang_edit 读取，
        保证罗盘与手工输入两条路径最终收敛到同一份数据。

        Args:
            zuo: 坐山名
            xiang: 正对之向山名
        """
        self.sui_xiang_edit.blockSignals(True)
        self.sui_xiang_edit.setText(f'{zuo}山{xiang}向')
        self.sui_xiang_edit.blockSignals(False)
        self._sync_mnt_info()

    def _on_sui_xiang_changed(self, text: str):
        """T3.5 输入框改写槽：解析首字为坐山，反向同步罗盘高亮。"""
        t = (text or '').strip()
        if t:
            self.compass.set_selected(t[0])
        self._sync_mnt_info()

    def _sync_mnt_info(self):
        """T3.5 刷新山向度数范围提示（如「坐山 子 0.0°~15.0°（正北）」）。"""
        t = self.sui_xiang_edit.text().strip()
        zuo = t[0] if t else ''
        if zuo in MOUNTAINS_24:
            s, e = _sector_range(MOUNTAINS_24.index(zuo))
            self.mnt_info.setText(f'坐山 {zuo}　{s:.1f}° ~ {e:.1f}°（正北为 0°，顺时针）')
        else:
            self.mnt_info.setText('')

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
        # 复位罗盘高亮（textChanged 已同步过一次，此处显式兜底）
        self.compass.set_selected('子')
        self._sync_mnt_info()
