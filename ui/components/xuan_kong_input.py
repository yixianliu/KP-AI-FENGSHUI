"""
ui/components/xuan_kong_input.py — 玄空飞星输入面板

提供坐向（如'子山午向'）、建造年份、当前年份三个输入项，供主窗口派发排盘。
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QScrollArea)
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from ui.styles import Colors, Fonts, Spacing, Stylesheets
from ui.components.collapsible_card import CollapsibleCard
from ui.components.input_panel import (build_action_bar, form_label,
                                       refresh_form_labels)

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

    #: 本面板全部标签文案：显式清单决定标签列宽（不遍历控件猜测）
    LABEL_TEXTS = ('建造年份', '当前年份')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._form_labels = []           # 已创建的标签，字体变化时统一重算宽度
        self.setStyleSheet(f"background-color: {Colors.BG};")
        self._build()

    def _build(self):
        """构建输入表单：滚动容器 + 吸底操作条（与八字 / 梅花面板同构）。

        罗盘 self.compass 仍按自身 210×210 固定尺寸自绘与换算点击坐标，
        本方法只在外层套一个 QScrollArea，不改变罗盘任何几何参数。
        """
        scroll = QScrollArea()
        scroll.setStyleSheet(Stylesheets.SCROLL)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.BG};")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(Spacing.S6, Spacing.S5, Spacing.S6, Spacing.S5)
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

        # 分组隐喻与八字 / 梅花统一：两个默认展开的折叠卡片
        # 卡片 1：坐向（环形罗盘点选 + 文本框手工输入，二者双向联动）
        sui_card = CollapsibleCard('坐向选择', '⛰', accent_color=Colors.QINGHUA, collapsed=False)
        sui_body = QWidget()
        sui_body.setStyleSheet('background: transparent;')
        sui_lay = QVBoxLayout(sui_body)
        sui_lay.setContentsMargins(Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM)
        sui_lay.setSpacing(Spacing.S3)

        # 长说明允许换行并缩写，窄窗口（350px 左栏）下不再被裁切。
        sui_xiang_hint = QLabel('坐向（点选罗盘或输入「子山午向」）')
        sui_xiang_hint.setWordWrap(True)
        sui_xiang_hint.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT2}; font-family:{Fonts.BODY};")
        sui_lay.addWidget(sui_xiang_hint)

        compass_row = QHBoxLayout()
        compass_row.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        compass_row.addStretch()
        self.compass = _Compass24(size=210)
        self.compass.mountain_selected.connect(self._on_compass_pick)
        compass_row.addWidget(self.compass)
        compass_row.addStretch()
        sui_lay.addLayout(compass_row)

        self.sui_xiang_edit = QLineEdit('子山午向')
        self.sui_xiang_edit.setStyleSheet(Stylesheets.INPUT)
        self.sui_xiang_edit.setAlignment(Qt.AlignCenter)
        sui_lay.addWidget(self.sui_xiang_edit)

        # 当前选中山的度数范围提示
        self.mnt_info = QLabel('')
        self.mnt_info.setAlignment(Qt.AlignCenter)
        self.mnt_info.setStyleSheet(
            f"font-size:{Fonts.SZ_MICRO}; color:{Colors.LIUJIN}; font-family:{Fonts.BODY};")
        sui_lay.addWidget(self.mnt_info)
        self._sync_mnt_info()
        # 手工改写文本框时，反向同步罗盘高亮
        self.sui_xiang_edit.textChanged.connect(self._on_sui_xiang_changed)
        sui_card.set_content(sui_body)
        lay.addWidget(sui_card)

        # 卡片 2：年份（建造年份 + 当前年份流年叠加）
        year_card = CollapsibleCard('年份设置', '◷', accent_color=Colors.QINGHUA, collapsed=False)
        year_body = QWidget()
        year_body.setStyleSheet('background: transparent;')
        year_lay = QVBoxLayout(year_body)
        year_lay.setContentsMargins(Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM)
        year_lay.setSpacing(Spacing.S3)

        # 建造年份：与其余两块面板同构的定宽标签列
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        row.addWidget(self._label('建造年份'))
        self.build_year_edit = QLineEdit('2024')
        self.build_year_edit.setStyleSheet(Stylesheets.INPUT)
        row.addWidget(self.build_year_edit, 1)
        year_lay.addLayout(row)

        # 当前年份（流年叠加）
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        row.addWidget(self._label('当前年份'))
        self.current_year_edit = QLineEdit('2025')
        self.current_year_edit.setStyleSheet(Stylesheets.INPUT)
        row.addWidget(self.current_year_edit, 1)
        year_lay.addLayout(row)
        year_card.set_content(year_body)
        lay.addWidget(year_card)

        lay.addStretch()
        scroll.setWidget(content)

        # 吸底操作条：按钮脱离滚动容器，最小窗口下仍恒定可见
        self.submit_btn = QPushButton('起盘')
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        self.reset_btn = QPushButton('重置')
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet(Stylesheets.BUTTON_SECONDARY)

        outer = QVBoxLayout(self)
        outer.setSpacing(Spacing.S0)  # 操作条紧贴滚动区，1px 上分隔线即面板分界
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll, 1)
        outer.addWidget(build_action_bar(self.submit_btn, self.reset_btn))

    def _label(self, text):
        """生成表单左侧定宽说明标签（与八字 / 梅花面板共用同一套实现）。

        Args:
            text: 标签文字。

        Returns:
            FormLabel: 宽度由本面板文案集合实测字体宽度决定的次级灰标签。
        """
        lb = form_label(text, Colors.TEXT2, self.LABEL_TEXTS)
        self._form_labels.append(lb)
        return lb

    def changeEvent(self, event):
        """字体变化时按新字体重算所有标签列宽（换字体/DPI 后不裁切）。"""
        super().changeEvent(event)
        if event.type() == QEvent.FontChange:
            refresh_form_labels(self._form_labels)

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
        """打包当前输入为 dict。

        Raises:
            ValueError: 坐向为空，或建造/当前年份不是整数。
                        由主窗口统一捕获并展示错误态，避免静默套用默认值出盘。
        """
        sui_xiang = self.sui_xiang_edit.text().strip()
        if not sui_xiang:
            raise ValueError('坐向不能为空，请输入如「子山午向」')
        raw_build = self.build_year_edit.text().strip()
        try:
            build = int(raw_build)
        except ValueError:
            raise ValueError(f'建造年份必须为整数，收到「{raw_build}」')
        raw_current = self.current_year_edit.text().strip()
        if raw_current:
            try:
                current = int(raw_current)
            except ValueError:
                raise ValueError(f'当前年份必须为整数，收到「{raw_current}」')
        else:
            current = build
        return {
            'sui_xiang': sui_xiang,
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
