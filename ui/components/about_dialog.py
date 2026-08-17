"""
关于对话框 — 增强视觉交互效果
=====================================
包含：呼吸光环头像 · 卡片淡入动画 · 按钮发光反馈 · 国风青花蓝/朱砂红配色
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QWidget, QMessageBox,
                               QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import (QFont, QFontMetrics, QPainter, QColor,
                           QLinearGradient, QPen, QPainterPath, QDesktopServices)

from ui.styles import Colors, Fonts, Spacing


class AboutDialog(QDialog):
    """关于 / 联系我对话框（增强交互版 v5）。"""

    QQ = '1153602036'
    PHONE = '19258585274'
    # 版本号单一权威源：从 app_version 读取，确保与程序实际版本完全一致。
    # 导入失败时回落到常量，保证对话框永远能打开。
    try:
        from app_version import get_version_label
        APP_VERSION = get_version_label()
    except Exception:
        APP_VERSION = 'v5.0.3'

    # 卡片动画延迟参数
    _STAGGER_DELAY = 80      # 每张卡片延迟 ms
    _STAGGER_BASE = 120      # 首张基础延迟 ms
    _FADE_DURATION = 450     # 淡入动画时长 ms
    _WAVE_STAGGER = 60       # 波浪延迟 ms

    def __init__(self, parent=None):
        """初始化关于对话框。

        Args:
            parent: 父窗口（可选），通常为应用主窗口。
        """
        super().__init__(parent)
        self.setWindowTitle('关于')
        self.setModal(True)
        self.setMinimumSize(480, 520)
        self._cards = []  # 需要入场动画的卡片列表
        self._build_ui()

    def showEvent(self, event):
        """重写 showEvent：在对话框可见后依次触发动画。"""
        super().showEvent(event)
        self._start_staggered_animations()

    def _start_staggered_animations(self):
        """依次触发行级卡片淡入动画（opacity）。"""
        for i, (card, base_delay) in enumerate(self._cards):
            delay = base_delay + i * self._STAGGER_DELAY
            anim = QPropertyAnimation(card, b"windowOpacity")
            anim.setDuration(self._FADE_DURATION)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            QTimer.singleShot(delay, anim.start)

    # ======================== 主布局 ========================
    def _build_ui(self):
        """构建主布局：顶部渐变 Header + 内容区（介绍卡 / 联系方式 / 版权）。"""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- 顶部渐变 Header（含头像动画） ----
        header = self._header()
        root.addWidget(header)

        # ---- 内容区 ----
        body = QWidget()
        body.setStyleSheet(f"background: {Colors.BG};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(28, 24, 28, 24)
        body_layout.setSpacing(16)

        # 介绍卡片（入场动画）
        intro = self._intro_card()
        self._cards.append((intro, self._STAGGER_BASE))
        body_layout.addWidget(intro)

        # 联系方式
        contacts = self._contacts_section()
        self._cards.append((contacts, self._STAGGER_BASE + self._STAGGER_DELAY))
        body_layout.addWidget(contacts)

        # 底部版权（stretch=0）
        footer = self._footer_text()
        body_layout.addWidget(footer)
        body_layout.addStretch(1)

        root.addWidget(body, 1)

    # ======================== 顶部 Header ========================
    def _header(self) -> QWidget:
        """渐变 Header + 呼吸光环头像 + 波浪。"""
        bar = QFrame()
        bar.setFixedHeight(160)
        bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.QINGHUA},
                    stop:0.55 {Colors.QINGHUA_DARK},
                    stop:1 {Colors.ZHUSHA});
                border-radius: 0px;
            }}
        """)
        outer = QVBoxLayout(bar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---- 中心内容行 ----
        center = QWidget()
        clayout = QHBoxLayout(center)
        clayout.setContentsMargins(0, 0, 0, 0)
        clayout.setAlignment(Qt.AlignCenter)

        clayout.addSpacing(28)

        # 带呼吸光环的头像
        avatar = HaloAvatarWidget('风', size=72)
        clayout.addWidget(avatar)
        clayout.addSpacing(16)

        # 文字区
        text_grp = QVBoxLayout()
        text_grp.setSpacing(3)
        text_grp.setAlignment(Qt.AlignTop)

        title = QLabel('风水排盘专业工具')
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: {Fonts.W_BOLD};
            color: white;
            font-family: {Fonts.TITLE}, 'Microsoft YaHei', sans-serif;
            letter-spacing: 3px;
        """)
        text_grp.addWidget(title)

        sub = QLabel('龙虎山大师兄 · 中国传统命理学 × 玄学智能解读')
        sub.setStyleSheet("""
            font-size: 12px;
            color: rgba(255,255,255,0.80);
            font-family: 'Segoe UI', sans-serif;
            letter-spacing: 0.5px;
        """)
        text_grp.addWidget(sub)

        ver = QLabel(self.APP_VERSION)
        ver.setStyleSheet("""
            font-size: 11px;
            color: rgba(255,255,255,0.50);
            font-family: 'Courier New', monospace;
        """)
        text_grp.addWidget(ver)

        clayout.addLayout(text_grp)
        clayout.addSpacing(24)

        outer.addWidget(center, 1)

        # ---- 波浪 ----
        wave = WaveDivider()
        outer.addWidget(wave)

        return bar

    # ======================== 介绍卡片 ========================
    def _intro_card(self) -> QFrame:
        """去框线，只用阴影做区分。"""
        card = ShadowCard()
        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 16, 24, 16)
        inner.setSpacing(8)

        lbl = QLabel('关于本项目')
        lbl.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.QINGHUA_DARK};
            font-family: {Fonts.TITLE}, 'Microsoft YaHei', sans-serif;
        """)
        lbl.setAlignment(Qt.AlignCenter)
        inner.addWidget(lbl)

        text = QLabel(
            '这是一款将中国传统命理学（八字 / 梅花易数 / 大六壬）与龙虎山大师兄分析预测深度融合的'
            '桌面端专业命理分析工具。\n\n'
            '通过严谨的命理算法计算，结合龙虎山大师兄的智能解读，为用户提供全方位、多层次的命理解析与决策参考。'
        )
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignJustify)
        text.setStyleSheet(f"""
            font-size: {Fonts.SZ_BODY};
            color: {Colors.TEXT2};
            font-family: {Fonts.BODY}, 'Microsoft YaHei', sans-serif;
            line-height: 170%;
        """)
        inner.addWidget(text)

        return card

    # ======================== 联系方式 ========================
    def _contacts_section(self) -> QFrame:
        """构建「联系我」卡片，含 QQ 与手机两个带联系/复制按钮的联系组件。"""
        card = ShadowCard()
        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 16, 24, 16)
        inner.setSpacing(14)

        lbl = QLabel('联系我')
        lbl.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.QINGHUA_DARK};
            font-family: {Fonts.TITLE}, 'Microsoft YaHei', sans-serif;
        """)
        lbl.setAlignment(Qt.AlignCenter)
        inner.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(14)

        qq_btn = ContactButton('QQ', '\U0001F4AC', self.QQ,
                               f'tencent://message/?uin={self.QQ}',
                               'QQ', '#12B7F5')
        row.addWidget(qq_btn)

        phone_btn = ContactButton('手机', '\U0001F4DE', self.PHONE,
                                  f'tel:{self.PHONE}',
                                  '手机', Colors.ZHUSHA)
        row.addWidget(phone_btn)

        inner.addLayout(row)

        hint = QLabel('点击"联系"按钮自动唤起应用 · 点击"复制"写入剪贴板')
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"""
            font-size: {Fonts.SZ_MICRO};
            color: {Colors.TEXT3};
            font-family: {Fonts.BODY}, 'Microsoft YaHei', sans-serif;
            padding: 2px 0;
        """)
        inner.addWidget(hint)

        return card

    def _footer_text(self) -> QLabel:
        """生成底部版权说明文本（版本号 + 免责声明），居中小字。"""
        lbl = QLabel(
            f'Copyright © 2024-2026 风水排盘专业工具 · {self.APP_VERSION}\n'
            '仅供学习与娱乐参考，不构成人生决策依据 · All Rights Reserved'
        )
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"""
            font-size: {Fonts.SZ_MICRO};
            color: {Colors.TEXT3};
            font-family: {Fonts.BODY}, 'Microsoft YaHei', sans-serif;
            padding: 4px 0;
        """)
        return lbl


# ======================== 装饰组件 ========================

class ShadowCard(QFrame):
    """无框线卡片 — 纯白色底色 + 柔和阴影，悬停时阴影加深 + 背景微变。"""

    def __init__(self):
        """初始化无边框阴影卡片：白底 + 柔和投影，用于区分内容区块。"""
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self._hovered = False

        # 单一阴影效果（通过动画切换 blurRadius）
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(14)
        self._shadow.setXOffset(0)
        self._shadow.setYOffset(3)
        self._shadow.setColor(QColor(0, 0, 0, 28))
        self.setGraphicsEffect(self._shadow)

        # 阴影动画（blurRadius 平滑过渡）
        self._shadow_anim = QPropertyAnimation(self._shadow, b"blurRadius")
        self._shadow_anim.setDuration(200)
        self._shadow_anim.setEasingCurve(QEasingCurve.OutQuad)

        self._normal_style = f"""
            QFrame {{
                background: {Colors.CARD};
                border: none;
                border-radius: {Spacing.RADIUS};
            }}
        """
        self._hover_style = f"""
            QFrame {{
                background: {Colors.CARD_HOVER};
                border: none;
                border-radius: {Spacing.RADIUS};
            }}
        """
        self.setStyleSheet(self._normal_style)

    def enterEvent(self, event):
        """悬停时加深阴影并变背景。"""
        self._hovered = True
        self.setStyleSheet(self._hover_style)
        # 动画 blurRadius 14 -> 22
        self._shadow_anim.setStartValue(14)
        self._shadow_anim.setEndValue(22)
        self._shadow_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """离开时恢复阴影和背景。"""
        self._hovered = False
        self.setStyleSheet(self._normal_style)
        # 动画 blurRadius 22 -> 14
        self._shadow_anim.setStartValue(22)
        self._shadow_anim.setEndValue(14)
        self._shadow_anim.start()
        super().leaveEvent(event)


class HaloAvatarWidget(QFrame):
    """圆形头像徽章 — 带呼吸光环效果。"""

    def __init__(self, text: str, size: int = 64):
        """初始化带呼吸光环的圆形头像徽章。

        Args:
            text: 显示文字（实际仅取首字符作为徽标）。
            size: 徽章边长（像素），默认 64。
        """
        super().__init__()
        self.size = size
        self.setText(text)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 呼吸光环动画（opacity 循环）
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._breathe_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._breathe_anim.setDuration(2000)  # 2秒一个周期
        self._breathe_anim.setStartValue(0.5)
        self._breathe_anim.setEndValue(1.0)
        self._breathe_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._breathe_anim.setLoopCount(-1)  # 无限循环
        self._breathe_anim.start()

        # 悬停状态
        self._hovered = False

    def setText(self, text: str):
        """设置头像文字，仅保留首字符作为徽标（空文本回退为 '?'）。"""
        self._text = text[:1] if text else '?'

    def enterEvent(self, event):
        """悬停时光环变亮。"""
        self._hovered = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        """离开时光环恢复。"""
        self._hovered = False
        super().leaveEvent(event)

    def paintEvent(self, event):
        """重绘事件：绘制带光环的渐变圆底、白色细内环与居中文字。"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

        rect = self.rect()
        cx, cy = rect.center().x(), rect.center().y()
        r = min(cx, cy) - 1

        # 外圈渐变
        grad = QLinearGradient(cx - r, cy - r, cx + r, cy + r)
        grad.setColorAt(0, QColor(107, 181, 170))
        grad.setColorAt(0.5, QColor(109, 176, 156))
        grad.setColorAt(1, QColor(196, 74, 60))
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx, cy, r, r)

        # 光环（悬停时更亮）
        halo_color = QColor(74, 122, 144, 80 if self._hovered else 50)
        pen_halo = QPen(halo_color, 2)
        painter.setPen(pen_halo)
        painter.drawEllipse(cx, cy, r + 4, r + 4)

        # 白色细内环
        pen = QPen(QColor(255, 255, 255, 50), 1.5)
        painter.setPen(pen)
        painter.drawEllipse(cx, cy, r - 3, r - 3)

        # 文字
        font = QFont('STSong', 22, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(self._text)
        th = fm.height()
        tx = rect.x() + (rect.width() - tw) // 2
        ty = rect.y() + (rect.height() - th) // 2 + fm.ascent()
        painter.drawText(tx, ty, self._text)
        painter.end()


class WaveDivider(QFrame):
    """波浪形分隔线。"""

    def __init__(self):
        """初始化波浪分隔线组件（固定高度 22，透明背景）。"""
        super().__init__()
        self.setFixedHeight(22)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        """重绘事件：绘制半透明渐变波形分隔线，衔接 Header 与下方内容。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # 渐变底色
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(255, 255, 255, 0))
        grad.setColorAt(1, QColor(255, 255, 255, 25))
        painter.fillRect(0, 0, w, h, grad)

        # 波浪线
        line_grad = QLinearGradient(0, 0, w, 0)
        line_grad.setColorAt(0, QColor(255, 255, 255, 0))
        line_grad.setColorAt(0.25, QColor(255, 255, 255, 150))
        line_grad.setColorAt(0.75, QColor(255, 255, 255, 150))
        line_grad.setColorAt(1, QColor(255, 255, 255, 0))

        pen = QPen(line_grad, 1.5)

        path = QPainterPath()
        step = 2
        for x in range(0, w + step, step):
            t = x / max(w, 1)
            y = h // 2 + 3.0 * (t * 4)
            if x == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        painter.strokePath(path, pen)
        painter.end()


class ContactButton(QWidget):
    """联系按钮：图标 + 名称 + 号码 + 操作行。"""

    def __init__(self, name: str, icon: str, value: str, link: str,
                 copy_name: str, accent_color: str):
        """初始化单个联系方式按钮组件。

        Args:
            name: 渠道名称（如 'QQ' / '手机'），用于标题与提示。
            icon: 图标 emoji 文本。
            value: 号码 / 账号文本，用于展示与复制。
            link: 点击「联系」时唤起的协议链接（如 tencent://、tel:）。
            copy_name: 复制到剪贴板时提示用的名称。
            accent_color: 强调色（十六进制），用于图标底色与按钮主色。
        """
        super().__init__()
        self._value = value
        self._accent = accent_color
        self._link = link
        self._copy_name = copy_name

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(5)

        # 图标 + 名称
        top = QHBoxLayout()
        top.setSpacing(8)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFixedSize(42, 42)
        icon_lbl.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {accent_color},
                    stop:1 {accent_color}BB);
                border-radius: 12px;
                font-size: 20px;
            }}
        """)
        top.addWidget(icon_lbl)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"""
            font-size: 14px;
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE}, 'Microsoft YaHei', sans-serif;
        """)
        top.addWidget(name_lbl)
        top.addStretch()
        layout.addLayout(top)

        # 号码
        num_lbl = QLabel(value)
        num_lbl.setAlignment(Qt.AlignCenter)
        num_lbl.setStyleSheet(f"""
            font-size: 18px;
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: 'Courier New', 'Consolas', monospace;
            letter-spacing: 1px;
            padding: 0;
        """)
        layout.addWidget(num_lbl)

        # 操作按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        link_btn = self._make_btn('\U0001F517 联系', accent_color, True)
        link_btn.clicked.connect(lambda: self._open_link(link, name))
        btn_row.addWidget(link_btn)

        copy_btn = self._make_btn('\U0001F4CB 复制', accent_color, False)
        copy_btn.clicked.connect(lambda: self._copy(value, copy_name))
        btn_row.addWidget(copy_btn)

        layout.addLayout(btn_row)
        self.setToolTip(f'{name}: {value}')

    def _make_btn(self, text: str, accent: str, solid: bool) -> QPushButton:
        """按强调色生成统一样式的操作按钮（含 hover 变色 + 点击缩放动画）。

        Args:
            text: 按钮文字。
            accent: 强调色十六进制。
            solid: True 为实心主按钮，False 为透明描边次按钮。
        """
        p = QPushButton(text)
        p.setCursor(Qt.PointingHandCursor)
        p.setFixedHeight(26)

        if solid:
            base_style = (
                f"background:{accent};"
                f"border-radius:8px;font-size:11px;padding:0 14px;"
                f"font-family:{Fonts.BODY}, 'Microsoft YaHei', sans-serif;"
            )
            hover_style = f"background:{accent}DD;"
        else:
            base_style = (
                f"background:transparent;color:{Colors.TEXT2};"
                f"border:none;border-radius:8px;font-size:11px;padding:0 14px;"
                f"font-family:{Fonts.BODY}, 'Microsoft YaHei', sans-serif;"
            )
            hover_style = (
                f"color:{accent};background:{Colors.HOVER};"
            )

        p.setStyleSheet(f"""
            QPushButton {{
                {base_style}
            }}
            QPushButton:hover {{
                {hover_style}
            }}
        """)

        # 点击微缩放反馈（通过动画实现）
        self._add_click_feedback(p)
        return p

    def _add_click_feedback(self, btn: QPushButton):
        """为按钮添加点击时的微缩放视觉反馈（press 缩小 pressed 恢复）。"""
        # 用 minimumWidth 属性做缩放手感（动画 80ms，OutCubic 缓动）
        anim = QPropertyAnimation(btn, b"minimumWidth")
        anim.setDuration(80)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def do_press():
            btn.setProperty("original_width", btn.minimumWidth() if btn.minimumWidth() > 0 else btn.width())
            anim.setStartValue(btn.property("original_width") or btn.width())
            anim.setEndValue(max(1, int((btn.property("original_width") or btn.width()) * 0.92)))
            anim.start()

        def do_release():
            orig = btn.property("original_width") or btn.width()
            anim.setStartValue(btn.minimumWidth())
            anim.setEndValue(orig)
            anim.start()

        btn.pressed.connect(do_press)
        btn.released.connect(do_release)

    def _open_link(self, url: str, name: str):
        """由「联系」按钮 clicked 触发：用系统默认应用打开协议链接，失败则弹窗提示。"""
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception:
            QMessageBox.warning(self.parentWidget() or self, '打开失败',
                                f'无法自动唤起 {name}，请手动联系。\n\n'
                                f'{name}: {self._value}')

    def _copy(self, value: str, name: str):
        """由「复制」按钮 clicked 触发：将 value 写入系统剪贴板并提示已复制。"""
        from PySide6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        cb.setText(value)
        # 使用实例化方式确保文本正确显示
        msg = QMessageBox(self.parentWidget() or self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('已复制')
        msg.setText(f'{name} 已复制到剪贴板')
        msg.setInformativeText(value)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
