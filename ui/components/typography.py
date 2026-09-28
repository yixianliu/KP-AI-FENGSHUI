# -*- coding: utf-8 -*-
"""
ui/components/typography.py — 统一排版组件（TLabel 工厂 + Font Scale QSS）

UI 升级方案 M3：取代全 UI 层散落的 QLabel 硬编码字号/颜色，
所有标签经 TLabel 工厂产出，强制 7 级 Font Scale + 4 级文字灰阶。

规范（对齐实施计划 3.2 / 4.1）：
    - 禁止直接 QLabel(...).setStyleSheet('font-size: ...px') 硬编码。
    - 一律走 TLabel.hero/h1/h2/h3/body/caption/micro/value。
    - 配套 FONT_SCALE_QSS 注入 objectName 选择器（#t-hero ~ #t-value），
      供全局集中样式管理，组件内不写死字号。
"""
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

from ui.styles import Colors, Fonts, Spacing

# Font Scale → objectName 映射（QSS 选择器用）
_T_NAMES = {
    'hero': 't-hero',
    'h1': 't-h1',
    'h2': 't-h2',
    'h3': 't-h3',
    'body': 't-body',
    'caption': 't-caption',
    'micro': 't-micro',
    'value': 't-value',
    # UI 升级 M1-3：长文本段落与代码块两个专用级别
    'para': 't-para',
    'code': 't-code',
}

# 各级规格：(字号, 字族, 字重, 颜色, 额外)
_SPECS = {
    'hero':    (Fonts.FS_HERO,    Fonts.TITLE, Fonts.W_BOLD,      Colors.TEXT,    {'letter-spacing': 2}),
    'h1':      (Fonts.FS_H1,      Fonts.TITLE, Fonts.W_SEMIBOLD,  Colors.TEXT,    {}),
    'h2':      (Fonts.FS_H2,      Fonts.TITLE, Fonts.W_SEMIBOLD,  Colors.TEXT,    {'letter-spacing': 0.5}),
    'h3':      (Fonts.FS_H3,      Fonts.BODY,  Fonts.W_MEDIUM,    Colors.TEXT,    {}),
    'body':    (Fonts.FS_BODY,    Fonts.BODY,  Fonts.W_REGULAR,   Colors.TEXT2,   {'line-height': Spacing.LINE_HEIGHT}),
    'caption': (Fonts.FS_CAPTION, Fonts.BODY,  Fonts.W_REGULAR,   Colors.TEXT3,    {}),
    'micro':   (Fonts.FS_MICRO,   Fonts.BODY,  Fonts.W_REGULAR,   Colors.TEXT4,    {}),
    'value':   (Fonts.FS_BODY,    Fonts.MONO,  Fonts.W_SEMIBOLD,  Colors.BRAND,    {}),
    # M1-3：长文本段落（正文列）
    'para':    (Fonts.FS_BODY,    Fonts.BODY,  Fonts.W_REGULAR,   Colors.TEXT2,
                {'line-height': Spacing.LINE_HEIGHT_BODY}),
    # M1-3：代码块（等宽 + 可选中复制）
    'code':    (Fonts.FS_CAPTION, Fonts.MONO,  Fonts.W_REGULAR,   Colors.TEXT2,
                {'line-height': Spacing.LINE_HEIGHT_BODY}),
}


def _qss_font_scale() -> str:
    """生成 Font Scale 的 QSS（按 objectName 选择器），供全局注入。"""
    parts = []
    for key, (size, fam, weight, color, extra) in _SPECS.items():
        oname = _T_NAMES[key]
        extra_qss = ''.join(f'{k}: {v};' for k, v in extra.items())
        parts.append(
            f"QLabel#{oname} {{ font-family: {fam}; font-size: {size}px; "
            f"font-weight: {weight}; color: {color}; {extra_qss} }}"
        )
    return '\n'.join(parts)


# 全局 Font Scale QSS（注入 QApplication 或顶层容器）
FONT_SCALE_QSS = _qss_font_scale()


def _make(text: str, level: str) -> QLabel:
    """按级别构造一个 QLabel（objectName + 内联样式双保险，离屏/任意父容器均生效）。"""
    size, fam, weight, color, extra = _SPECS[level]
    lbl = QLabel(text)
    lbl.setObjectName(_T_NAMES[level])
    extra_qss = ''.join(f'{k}: {v};' for k, v in extra.items())
    lbl.setStyleSheet(
        f"font-family: {fam}; font-size: {size}px; font-weight: {weight}; "
        f"color: {color}; {extra_qss} background: transparent;"
    )
    return lbl


class TLabel:
    """统一的 QLabel 工厂，取代散落的 font-size/padding 硬编码。

    每个类方法返回已配置 objectName + 内联样式的 QLabel，可直接 addWidget。
    """

    @staticmethod
    def hero(text: str) -> QLabel:
        """首页大标题（28px Bold 楷体）。"""
        return _make(text, 'hero')

    @staticmethod
    def h1(text: str) -> QLabel:
        """主标题（20px Semibold 楷体）。"""
        return _make(text, 'h1')

    @staticmethod
    def h2(text: str) -> QLabel:
        """页内标题（17px Semibold 楷体）。"""
        return _make(text, 'h2')

    @staticmethod
    def h3(text: str) -> QLabel:
        """小标题/卡片标题（15px Medium 雅黑）。"""
        return _make(text, 'h3')

    @staticmethod
    def body(text: str) -> QLabel:
        """正文（13px Regular 雅黑，二级灰阶）。"""
        return _make(text, 'body')

    @staticmethod
    def caption(text: str) -> QLabel:
        """辅助说明（12px 雅黑，三级灰阶）。"""
        return _make(text, 'caption')

    @staticmethod
    def micro(text: str) -> QLabel:
        """极小字（11px 时间戳/单位，四级灰阶）。"""
        return _make(text, 'micro')

    @staticmethod
    def value(text: str) -> QLabel:
        """数值/等宽（13px Semibold 等宽，品牌金色）。"""
        return _make(text, 'value')

    @staticmethod
    def paragraph(text: str) -> QLabel:
        """长文本段落（13px Regular，二级灰阶，统一行高，自动换行）。

        UI 升级 M1-3 / M3-4：正文段落的唯一排版出口，配合
        `collapsible_card.paragraph_block()` 实现「分段落 + 最大行宽居中」。
        """
        lbl = _make(text, 'para')
        lbl.setWordWrap(True)
        return lbl

    @staticmethod
    def code(text: str) -> QLabel:
        """代码块文本（12px 等宽，可选中复制）。

        UI 升级 M1-3 / M3-4：``` 围栏内容专用；设为鼠标可选中以便复制，
        换行由外层 QScrollArea 负责（不自动换行，保留代码缩进结构）。
        """
        lbl = _make(text, 'code')
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        return lbl

    @staticmethod
    def of(text: str, level: str = 'body') -> QLabel:
        """通用工厂：按级别名构造（level 取值见 _T_NAMES）。"""
        return _make(text, level if level in _SPECS else 'body')
