"""
关于对话框 v4.0 — 无框线现代扁平设计
=====================================
包含：头像徽章 · 开发者介绍 · 社交联系方式 · 关闭按钮
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QWidget, QMessageBox,
                               QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import (QFont, QFontMetrics, QPainter, QColor,
                           QLinearGradient, QPen, QPainterPath, QDesktopServices)

from ui.styles import Colors, Fonts, Spacing


class AboutDialog(QDialog):
    """关于 / 联系我对话框（无框线现代扁平版 v4）。"""

    QQ = '1153602036'
    PHONE = '19258585274'
    APP_VERSION = 'v5.0'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('关于')
        self.setModal(True)
        self.setMinimumSize(480, 520)
        self._build_ui()

    # ======================== 主布局 ========================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- 顶部渐变 Header ----
        header = self._header()
        root.addWidget(header)

        # ---- 内容区 ----
        body = QWidget()
        body.setStyleSheet(f"background: {Colors.BG};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(28, 24, 28, 24)
        body_layout.setSpacing(16)

        # 介绍卡片
        intro = self._intro_card()
        body_layout.addWidget(intro)

        # 联系方式
        contacts = self._contacts_section()
        body_layout.addWidget(contacts)

        # 底部版权（stretch=0）
        footer = self._footer_text()
        body_layout.addWidget(footer)
        body_layout.addStretch(1)

        root.addWidget(body, 1)

    # ======================== 顶部 Header ========================
    def _header(self) -> QWidget:
        """渐变 Header + 头像 + 波浪。"""
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

        avatar = AvatarWidget('风', size=72)
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
            '这是一款将中国传统命理学（八字 / 梅花易数 / 大六壬）与龙虎山大师兄深度融合的'
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
    """无框线卡片 — 纯白色底色 + 柔和阴影，无边框线。"""

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: none;
                border-radius: {Spacing.RADIUS};
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(14)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 28))
        self.setGraphicsEffect(shadow)


class AvatarWidget(QFrame):
    """圆形头像徽章，纯 QPainter 绘制。"""

    def __init__(self, text: str, size: int = 64):
        super().__init__()
        self.size = size
        self.setText(text)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def setText(self, text: str):
        self._text = text[:1] if text else '?'

    def paintEvent(self, event):
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

        # 白色细内环（更淡）
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
        super().__init__()
        self.setFixedHeight(22)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
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
        p = QPushButton(text)
        p.setCursor(Qt.PointingHandCursor)
        p.setFixedHeight(26)
        p.setStyleSheet(f"""
            QPushButton {{
                {"background:" + accent if solid else "background:transparent;color:" + Colors.TEXT2 + ";border: none;"}
                border-radius: 8px;
                font-size: 11px;
                padding: 0 14px;
                font-family: {Fonts.BODY}, 'Microsoft YaHei', sans-serif;
            }}
            QPushButton:hover {{
                {"background:" + accent + "DD" if solid else "color:" + accent + ";background:" + Colors.HOVER + ";border: none;"}
            }}
        """)
        return p

    def _open_link(self, url: str, name: str):
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception:
            QMessageBox.warning(self.parentWidget() or self, '打开失败',
                                f'无法自动唤起 {name}，请手动联系。\n\n'
                                f'{name}: {self._value}')

    def _copy(self, value: str, name: str):
        from PySide6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        cb.setText(value)
        QMessageBox.information(self.parentWidget() or self, '已复制',
                                f'{name} 已复制到剪贴板\n\n{value}')
