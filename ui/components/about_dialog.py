"""
关于对话框 — 增强视觉交互效果
=====================================
包含：呼吸光环头像 · 卡片淡入动画 · 按钮发光反馈 · 国风青花蓝/朱砂红配色 · 支付二维码
"""
import logging
import os
import sys
from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QWidget, QMessageBox,
                               QScrollArea,
                               QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve, QTimer, QSize
from PySide6.QtGui import (QFont, QFontMetrics, QPainter, QColor,
                           QLinearGradient, QPen, QPainterPath, QDesktopServices,
                           QPixmap, QPalette)

from ui.styles import Colors, Fonts, Spacing
from core.path_utils import get_resource_path, get_app_dir
from ui.components.typography import TLabel  # M4-5：分区标题/正文/提示统一走 TLabel 工厂


class AboutDialog(QDialog):
    """关于 / 联系我对话框（增强交互版 v5）。"""

    QQ = '1153602036'
    PHONE = '19258585274'
    # ---- 二维码资源（UI 升级 M4-1） ----
    # 旧实现 QRCODE_DIR = Path(r'D:\PythonProject\qrcode') 是硬编码绝对路径，
    # 该目录在源码树与打包产物中均不存在 → 4 张二维码 100% 走失败分支（方案 Q01）。
    # 改为「相对仓库根目录 + get_resource_path」：源码运行解析到 <root>/images，
    # 打包运行解析到 _MEIPASS/images（images 已由 M4-1 加入 spec datas）。
    # 均为**相对路径**，不依赖任何开发机绝对路径。
    QR_FRIEND_DIR = 'images/link_qrcode'   # 添加好友：wx.png / qq.png
    QR_PAY_DIR = 'images/pay_qrcode'       # 支付打赏：wx-pay.png / ali-pay.png
    # 版本号单一权威源：从 app_version 读取，确保与程序实际版本完全一致。
    # 导入失败时回落到常量，保证对话框永远能打开。
    try:
        from core.app_version import get_version_label
        APP_VERSION = get_version_label()
    except Exception:
        APP_VERSION = 'v5.0.6'

    # Header 固定高度（M4-5：原为裸数字 160，提为常量便于统一调整）
    HEADER_H = 160
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
        # M4-3：内容由 3 张卡增至 5 张（新增「添加我好友」「版本信息」），
        # 最小高度上调到 560；横向反降至 460，允许 XS 档窄窗口（body 可滚动）。
        self.setMinimumSize(460, 560)
        self._cards = []  # 需要入场动画的卡片列表
        self._qr_labels = []  # 所有二维码标签，供 resize 时统一改尺寸
        self._qr_size = QPixmapLabel.size_for(self.width())
        self._build_ui()

    def resizeEvent(self, event):
        """按对话框宽度切换二维码三档尺寸（M4-3）。

        只在档位变化时才调用 setSize，避免 resize 期间反复重缩放。
        """
        super().resizeEvent(event)
        target = QPixmapLabel.size_for(self.width())
        if target == self._qr_size:
            return
        self._qr_size = target
        for lbl in getattr(self, '_qr_labels', []):
            try:
                lbl.setSize(target)
            except RuntimeError:
                pass  # 控件已销毁

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
        """构建主布局：顶部渐变 Header + 可滚动内容区（M4-5 五个语义分区）。

        分区顺序（方案 M4-5）：
            关于本项目 → 联系我 → 添加我好友 → 支持我们 → 版本信息 → 版权声明
        body 用 QScrollArea 包裹，新增卡片后在 560px 最小高度下也不会被裁切。
        """
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(Spacing.S0)

        # ---- 顶部渐变 Header（含头像动画） ----
        header = self._header()
        root.addWidget(header)

        # ---- 内容区（可滚动） ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea {{ background: {Colors.BG}; border: none; }}"
        )

        body = QWidget()
        body.setStyleSheet(f"background: {Colors.BG};")
        body_layout = QVBoxLayout(body)
        # M4-5：裸数字 (28,24,28,24) → 令牌
        body_layout.setContentsMargins(
            Spacing.S6, Spacing.S5, Spacing.S6, Spacing.S5)
        body_layout.setSpacing(Spacing.S4)

        # 1) 关于本项目
        intro = self._intro_card()
        self._cards.append((intro, self._STAGGER_BASE))
        body_layout.addWidget(intro)

        # 2) 联系我
        contacts = self._contacts_section()
        self._cards.append((contacts, self._STAGGER_BASE + self._STAGGER_DELAY))
        body_layout.addWidget(contacts)

        # 3) 添加我好友（M4-2 新增）
        friend = self._friend_section()
        self._cards.append((friend, self._STAGGER_BASE + 2 * self._STAGGER_DELAY))
        body_layout.addWidget(friend)

        # 4) 支持我们（支付二维码）
        qrcode = self._qrcode_section()
        self._cards.append((qrcode, self._STAGGER_BASE + 3 * self._STAGGER_DELAY))
        body_layout.addWidget(qrcode)

        # 5) 版本信息（M4-5 / Q18 新增）
        version = self._version_section()
        self._cards.append((version, self._STAGGER_BASE + 4 * self._STAGGER_DELAY))
        body_layout.addWidget(version)

        # 6) 底部版权（stretch=0）
        footer = self._footer_text()
        body_layout.addWidget(footer)
        body_layout.addStretch(1)

        scroll.setWidget(body)
        root.addWidget(scroll, 1)

    # ======================== 顶部 Header ========================
    def _header(self) -> QWidget:
        """渐变 Header + 呼吸光环头像 + 波浪。"""
        bar = QFrame()
        # M4-5：裸数字 160 提为常量（Header 高度需容纳 72px 头像 + 三行文字 + 波浪）
        bar.setFixedHeight(self.HEADER_H)
        bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.QINGHUA},
                    stop:0.55 {Colors.QINGHUA_DARK},
                    stop:1 {Colors.ZHUSHA});
                border-radius: 0;
            }}
        """)
        outer = QVBoxLayout(bar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(Spacing.S0)

        # ---- 中心内容行 ----
        center = QWidget()
        clayout = QHBoxLayout(center)
        clayout.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        clayout.setContentsMargins(0, 0, 0, 0)
        clayout.setAlignment(Qt.AlignCenter)

        clayout.addSpacing(Spacing.S7)

        # 带呼吸光环的头像
        avatar = HaloAvatarWidget('风', size=72)
        clayout.addWidget(avatar)
        clayout.addSpacing(Spacing.S4)

        # 文字区
        text_grp = QVBoxLayout()
        text_grp.setSpacing(Spacing.S1)
        text_grp.setAlignment(Qt.AlignTop)

        title = QLabel('风水排盘专业工具')
        title.setStyleSheet(f"""
            font-size: {Fonts.FS_H1}px;
            font-weight: {Fonts.W_BOLD};
            color: white;
            font-family: {Fonts.TITLE}, 'Microsoft YaHei', sans-serif;
            letter-spacing: 3px;
        """)
        text_grp.addWidget(title)

        sub = QLabel('龙虎山大师兄 · 中国传统命理学 × 玄学智能解读')
        sub.setStyleSheet(f"""
            font-size: {Fonts.FS_CAPTION}px;
            color: rgba(255,255,255,0.80);
            font-family: 'Segoe UI', sans-serif;
            letter-spacing: 0.5px;
        """)
        text_grp.addWidget(sub)

        ver = QLabel(self.APP_VERSION)
        ver.setStyleSheet(f"""
            font-size: {Fonts.FS_MICRO}px;
            color: rgba(255,255,255,0.50);
            font-family: 'Courier New', monospace;
        """)
        text_grp.addWidget(ver)

        clayout.addLayout(text_grp)
        clayout.addSpacing(Spacing.S6)

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
        # M4-5：裸数字 (24,16,24,16) → 间距令牌（Q06 间距不变量）
        inner.setContentsMargins(Spacing.S6, Spacing.S4, Spacing.S6, Spacing.S4)
        inner.setSpacing(Spacing.S2)

        # M4-5：分区标题走 TLabel.h3（替代重复 QSS 字符串，字重 500）
        lbl = TLabel.h3('关于本项目')
        lbl.setStyleSheet(lbl.styleSheet() + f'color: {Colors.QINGHUA_DARK};')
        lbl.setAlignment(Qt.AlignCenter)
        inner.addWidget(lbl)

        # M4-5：正文走 TLabel.paragraph（统一行高 1.7 + 自动换行）
        text = TLabel.paragraph(
            '这是一款将中国传统命理学（八字 / 梅花易数 / 大六壬）与龙虎山大师兄分析预测深度融合的'
            '桌面端专业命理分析工具。\n\n'
            '通过严谨的命理算法计算，结合龙虎山大师兄的智能解读，为用户提供全方位、多层次的命理解析与决策参考。'
        )
        text.setAlignment(Qt.AlignJustify)
        inner.addWidget(text)

        return card

    # ======================== 联系方式 ========================
    def _contacts_section(self) -> QFrame:
        """构建「联系我」卡片，含 QQ 与手机两个带联系/复制按钮的联系组件。"""
        card = ShadowCard()
        inner = QVBoxLayout(card)
        # M4-5：裸数字 (24,16,24,16) → 间距令牌
        inner.setContentsMargins(Spacing.S6, Spacing.S4, Spacing.S6, Spacing.S4)
        inner.setSpacing(Spacing.S4)

        # M4-5：分区标题走 TLabel.h3
        lbl = TLabel.h3('联系我')
        lbl.setStyleSheet(lbl.styleSheet() + f'color: {Colors.QINGHUA_DARK};')
        lbl.setAlignment(Qt.AlignCenter)
        inner.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(Spacing.S4)

        # 已知审计豁免：#12B7F5 是腾讯 QQ 官方品牌蓝，属第三方品牌色，
        # 刻意不走 Colors 令牌（令牌表只承载本项目设计系统色）
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

    # ======================== 支付二维码 ========================
    def _qrcode_section(self) -> QFrame:
        """构建「支持我们」支付二维码卡片，展示微信与支付宝二维码。"""
        card = ShadowCard()
        inner = QVBoxLayout(card)
        # M4-5：裸数字 (24,16,24,16) → 间距令牌
        inner.setContentsMargins(Spacing.S6, Spacing.S4, Spacing.S6, Spacing.S4)
        inner.setSpacing(Spacing.S4)

        # M4-5：分区标题走 TLabel.h3
        lbl = TLabel.h3('支持我们')
        lbl.setStyleSheet(lbl.styleSheet() + f'color: {Colors.QINGHUA_DARK};')
        lbl.setAlignment(Qt.AlignCenter)
        inner.addWidget(lbl)

        # 双栏布局：微信 | 支付宝
        qr_row = QHBoxLayout()
        qr_row.setSpacing(Spacing.S5)

        wx_item = self._qr_item('微信支付', 'wx-pay.png', Colors.SUCCESS)
        alipay_item = self._qr_item('支付宝', 'ali-pay.png', Colors.QINGHUA)
        qr_row.addWidget(wx_item)
        qr_row.addWidget(alipay_item)

        inner.addLayout(qr_row)

        hint = QLabel('扫码支持本项目开发 · 金额随意，感谢认可 🙏')  # M4-2.4 文案微调
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"""
            font-size: {Fonts.SZ_MICRO};
            color: {Colors.TEXT3};
            font-family: {Fonts.BODY}, 'Microsoft YaHei', sans-serif;
            padding: 2px 0;
        """)
        inner.addWidget(hint)

        return card

    # ======================== 添加我好友（M4-2） ========================
    def _friend_section(self) -> QFrame:
        """构建「添加我好友」卡片，展示微信 / QQ 好友二维码（修 Q04）。

        结构与 `_qrcode_section()` 一致，但资源取自 QR_FRIEND_DIR
        （images/link_qrcode），缺图时走与支付区相同的降级文案。
        """
        card = ShadowCard()
        inner = QVBoxLayout(card)
        # M4-5：统一间距令牌
        inner.setContentsMargins(Spacing.S6, Spacing.S4, Spacing.S6, Spacing.S4)
        inner.setSpacing(Spacing.S4)

        # 分区标题（M4-5：TLabel.h3 + 品牌深金）
        lbl = TLabel.h3('添加我好友')
        lbl.setStyleSheet(lbl.styleSheet() + f'color: {Colors.QINGHUA_DARK};')
        lbl.setAlignment(Qt.AlignCenter)
        inner.addWidget(lbl)

        # 双栏布局：微信好友 | QQ 好友
        qr_row = QHBoxLayout()
        qr_row.setSpacing(Spacing.S5)

        wx_item = self._qr_item('微信好友', 'wx.png', Colors.SUCCESS,
                                sub_dir=self.QR_FRIEND_DIR)
        qq_item = self._qr_item('QQ 好友', 'qq.png', Colors.QINGHUA,
                                 sub_dir=self.QR_FRIEND_DIR)
        qr_row.addWidget(wx_item)
        qr_row.addWidget(qq_item)

        inner.addLayout(qr_row)

        # 提示文案（M4-2：扫码添加好友，备注「排盘」）
        hint = QLabel('扫码添加好友，交流命理与使用问题 · 好友申请请备注「排盘」')
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"""
            font-size: {Fonts.SZ_MICRO};
            color: {Colors.TEXT3};
            font-family: {Fonts.BODY}, 'Microsoft YaHei', sans-serif;
            padding: 2px 0;
        """)
        inner.addWidget(hint)

        return card

    # ======================== 版本信息（M4-5 / Q18） ========================
    def _version_section(self) -> QFrame:
        """构建「版本信息」小卡（Q18）：把版本/构建/运行环境集中成区。

        三行均用 TLabel.micro（等宽显示版本号），底部版权仍由 `_footer_text()` 负责。
        """
        card = ShadowCard()
        inner = QVBoxLayout(card)
        inner.setContentsMargins(Spacing.S6, Spacing.S4, Spacing.S6, Spacing.S4)
        inner.setSpacing(Spacing.S2)

        lbl = TLabel.h3('版本信息')
        lbl.setStyleSheet(lbl.styleSheet() + f'color: {Colors.QINGHUA_DARK};')
        lbl.setAlignment(Qt.AlignCenter)
        inner.addWidget(lbl)

        # 构建（git short hash），无 .git 时留空
        commit = self._git_commit_short()
        build_line = f'构建 {commit}' if commit else '构建 （本地源码）'

        # 版本号行：用 TLabel.value（等宽品牌金）突出版本
        ver_row = TLabel.value(self.APP_VERSION)
        ver_row.setAlignment(Qt.AlignCenter)
        inner.addWidget(ver_row)

        build_row = TLabel.micro(build_line)
        build_row.setAlignment(Qt.AlignCenter)
        inner.addWidget(build_row)

        env_row = TLabel.micro('运行环境 Python 3.13 · PySide6 6.9.2')
        env_row.setAlignment(Qt.AlignCenter)
        inner.addWidget(env_row)

        return card

    # ======================== 二维码资源解析（M4-1） ========================
    @classmethod
    def _resolve_qr(cls, sub_dir: str, filename: str):
        """按「打包(_MEIPASS) → 资源根 → 可执行文件同级」顺序解析二维码路径。

        Args:
            sub_dir: 相对仓库根的子目录（QR_FRIEND_DIR / QR_PAY_DIR）。
            filename: 图片文件名（如 'wx-pay.png'）。

        Returns:
            (Path | None, str)：成功时 (绝对路径, '')；失败时 (None, 失败原因文案)。
            失败原因**只写日志，不暴露给用户**（方案 M4-4：禁止显示 .png 文件名）。
        """
        rel = f'{sub_dir}/{filename}'
        try:
            p = get_resource_path(rel)
            if p and Path(p).exists():
                return Path(p), ''
        except Exception:
            pass
        # 打包回退：exe 同级 images/（用户可能自行放置/替换资源）
        try:
            p2 = get_app_dir() / sub_dir / filename
            if p2.exists():
                return p2, ''
        except Exception:
            pass
        return None, f'资源缺失: {rel}'

    def _qr_item(self, label: str, filename: str, accent: str,
                 sub_dir: str = None) -> QWidget:
        """生成单个二维码组件（白底容器 + 图片 + 标签），含加载失败降级处理。

        Args:
            label: 渠道名称（如 '微信支付' / '微信好友'）。
            filename: 图片文件名（相对于 sub_dir）。
            accent: 强调色十六进制，用于占位区边框与降级图标。
            sub_dir: 资源子目录；None 时取 QR_PAY_DIR（保持向后兼容）。

        Returns:
            包含白底容器、QPixmapLabel 和说明文字的组合 Widget。
        """
        sub_dir = sub_dir or self.QR_PAY_DIR
        grp = QWidget()
        v = QVBoxLayout(grp)
        v.setContentsMargins(Spacing.S1, Spacing.S1, Spacing.S1, Spacing.S1)
        v.setSpacing(Spacing.S2)
        v.setAlignment(Qt.AlignCenter)

        # 白底容器（quiet zone）：二维码四周留白是扫码成功率的硬要求，
        # 深色主题下直接贴深色底会显著降低识别率（方案 M4-3）。
        frame = QFrame()
        frame.setObjectName('qr_white_frame')
        # M4-5：白底容器色值 #FFFFFF → Colors.WHITE 令牌（二维码 quiet zone 必须纯白）
        frame.setStyleSheet(
            f"QFrame#qr_white_frame {{ background: {Colors.WHITE}; "
            f"border-radius: {Spacing.RADIUS_SM}; border: none; }}"
        )
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(Spacing.S2, Spacing.S2, Spacing.S2, Spacing.S2)
        fl.setSpacing(Spacing.S0)

        img_lbl = QPixmapLabel(label=label, accent=accent)
        fl.addWidget(img_lbl)
        if not hasattr(self, '_qr_labels'):
            self._qr_labels = []
        self._qr_labels.append(img_lbl)
        v.addWidget(frame)

        # 文字标签
        txt = QLabel(label)
        txt.setAlignment(Qt.AlignCenter)
        txt.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL}px;
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT2};
            font-family: {Fonts.BODY}, 'Microsoft YaHei', sans-serif;
            padding: 2px 0;
        """)
        v.addWidget(txt)

        # 加载（同步，避免闪烁）
        path, reason = self._resolve_qr(sub_dir, filename)
        if path is not None:
            img_lbl.setPixmap(QPixmap(str(path)))
        else:
            # M4-4：结构化降级，不暴露文件名，不弹窗（弹窗会阻塞且离屏测试 hang）
            img_lbl.setError(self._qr_error_text(label, accent))
            try:
                logging.getLogger(__name__).warning(f'[关于] 二维码加载失败 {reason}')
            except Exception:
                pass

        return grp

    @staticmethod
    def _qr_error_text(label: str, accent: str) -> str:
        """生成二维码加载失败的中文降级文案（M4-4）。

        Args:
            label: 渠道名称（'微信支付' / 'QQ 好友' 等）。
            accent: 强调色（保留参数以兼容既有调用；文案本身不使用）。

        Returns:
            两行文案：主提示 + 可操作引导（引导用户走下方联系方式）。
        """
        return f'{label}二维码暂未加载\n请通过下方联系方式添加'

    def _footer_text(self) -> QLabel:
        """生成底部版权说明文本（版本号 + 免责声明），居中小字。"""
        ver_line = f'{self.APP_VERSION}'
        # T6.2 调试版展示 Git commit hash（动态获取，失败静默回退，不影响正式构建）
        commit = self._git_commit_short()
        if commit:
            ver_line = f'{self.APP_VERSION} ({commit})'
        lbl = QLabel(
            f'Copyright © 2024-2026 风水排盘专业工具 · {ver_line}\n'
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

    @staticmethod
    def _git_commit_short() -> str:
        """T6.2 获取短 Git commit hash（调试版用），失败返回空串（不显示）。

        仅当源码目录下存在 .git 时尝试读取；打包产物无 .git 则静默回退。
        """
        try:
            import subprocess
            project_root = Path(__file__).resolve().parent.parent.parent
            if not (project_root / '.git').exists():
                return ''
            out = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=str(project_root),
                capture_output=True, text=True, timeout=2,
            )
            h = out.stdout.strip()
            return h if h else ''
        except Exception:
            return ''


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
            link: 点击"联系"时唤起的协议链接（如 tencent://、tel:）。
            copy_name: 复制到剪贴板时提示用的名称。
            accent_color: 强调色（十六进制），用于图标底色与按钮主色。
        """
        super().__init__()
        self._value = value
        self._accent = accent_color
        self._link = link
        self._copy_name = copy_name

        layout = QVBoxLayout(self)
        # M4-5：裸数字 (8,6,8,6) → 间距令牌（6 不在 8-4 网格，取 S1=4）
        layout.setContentsMargins(Spacing.S2, Spacing.S1, Spacing.S2, Spacing.S1)
        layout.setSpacing(Spacing.S1)

        # 图标 + 名称
        top = QHBoxLayout()
        top.setSpacing(Spacing.S2)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFixedSize(42, 42)
        icon_lbl.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {accent_color},
                    stop:1 {accent_color}BB);
                border-radius: {Spacing.RADIUS_LG_INT}px;
                font-size: {Fonts.FS_H1}px;
            }}
        """)
        top.addWidget(icon_lbl)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"""
            font-size: {Fonts.FS_BODY}px;
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
            font-size: {Fonts.FS_H2}px;
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: 'Courier New', 'Consolas', monospace;
            letter-spacing: 1px;
            padding: 0;
        """)
        layout.addWidget(num_lbl)

        # 操作按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(Spacing.S2)

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
        """由"联系"按钮 clicked 触发：用系统默认应用打开协议链接，失败则弹窗提示。"""
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception:
            QMessageBox.warning(self.parentWidget() or self, '打开失败',
                                f'无法自动唤起 {name}，请手动联系。\n\n'
                                f'{name}: {self._value}')

    def _copy(self, value: str, name: str):
        """由"复制"按钮 clicked 触发：将 value 写入系统剪贴板并提示已复制。"""
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


# ======================== 支付二维码组件 ========================

class QPixmapLabel(QLabel):
    """支持等比缩放、错误降级占位图的图片标签。

    加载成功时以 KeepAspectRatio 平滑缩放至固定尺寸；
    加载失败或路径不存在时绘制带强调色的占位区域，提示"图片缺失"。
    """

    FIXED_SIZE = 140  # 默认显示尺寸（正方形）；实例级可覆盖，见 __init__(size=)
    # 三档尺寸（M4-3）：(对话宽度下限, 显示边长)；从大到小匹配第一个满足的档。
    # 紧凑档 132 是「二维码模块最小可扫尺寸」的经验下限，再小会掉识别率。
    SIZE_TIERS = ((680, 180), (520, 160), (0, 132))

    def __init__(self, label: str = '', parent=None, accent: str = Colors.QINGHUA,
                 size: int = 160):
        """初始化二维码占位标签。

        Args:
            label: 备用占位文字（图片加载失败时显示）。
            parent: 父 widget。
            accent: 强调色十六进制，用于占位区域的底边装饰条。
            size: 初始显示边长（正方形），默认 160（标准档）。
        """
        super().__init__(label, parent)
        self._accent = accent
        self._error_text = label
        self._size = int(size or self.FIXED_SIZE)
        self._raw_pixmap = None   # 保存原始图，避免反复缩放累积失真
        self._icon = ''           # 降级占位图标（渠道专属）
        self.setMinimumSize(self._size, self._size)
        self.setMaximumSize(self._size, self._size)
        self.setAlignment(Qt.AlignCenter)
        # 默认占位背景
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {Colors.BG_DARK};
                border: 2px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_SM};
                font-size: {Fonts.FS_MICRO}px;
                color: {Colors.TEXT3};
                font-family: {Fonts.BODY}, 'Microsoft YaHei', sans-serif;
            }}
        """)

    @classmethod
    def size_for(cls, dialog_width: int) -> int:
        """按对话框宽度返回二维码显示边长（M4-3 三档）。"""
        for min_w, sz in cls.SIZE_TIERS:
            if dialog_width >= min_w:
                return sz
        return cls.SIZE_TIERS[-1][1]

    def setSize(self, size: int):
        """改变显示尺寸并按缓存的原始图重缩放（不累积失真）。

        Args:
            size: 新的正方形边长 px。
        """
        size = int(size or self._size)
        if size == self._size and self._raw_pixmap is None:
            return
        self._size = size
        self.setMinimumSize(size, size)
        self.setMaximumSize(size, size)
        if self._raw_pixmap is not None and not self._raw_pixmap.isNull():
            super().setPixmap(self._raw_pixmap.scaled(
                QSize(size, size), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def setPixmap(self, pixmap: QPixmap):
        """设置 pixmap 并平滑缩放到当前尺寸，保持宽高比。

        Args:
            pixmap: 原始 QPixmap 对象。若为空则切换为错误占位。
        """
        if pixmap is None or pixmap.isNull():
            self.setError(self._error_text)
            return
        self._raw_pixmap = QPixmap(pixmap)   # 缓存原图，供 setSize 重缩放
        # PySide6 6.9.2：scaled 必须传显式 QSize，传 (0, 0) 会 TypeError；
        # 原图非正方（如 1085×919）时 KeepAspectRatio 居中，留白由白底容器吸收。
        super().setPixmap(self._raw_pixmap.scaled(
            QSize(self._size, self._size), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # 加载成功后移除边框样式，让图片完整展示
        self.setStyleSheet("")

    def setError(self, text: str):
        """切换为结构化降级占位（M4-4）：渠道图标 + 主文案 + 可操作引导。

        不再显示 `.png` 文件名等实现细节。

        Args:
            text: 占位区显示的说明文字，支持 \n 换行。
        """
        self._error_text = text
        self._raw_pixmap = None
        self.clear()
        self.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 {Colors.BG_DARK});
                border: 2px dashed {self._accent}88;
                border-radius: {Spacing.RADIUS_SM};
                font-size: {Fonts.FS_MICRO}px;
                color: {Colors.TEXT3};
                font-family: {Fonts.BODY}, 'Microsoft YaHei', sans-serif;
            }}
        """)
        self.setText(text)