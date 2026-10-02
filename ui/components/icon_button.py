# -*- coding: utf-8 -*-
"""
ui/components/icon_button.py — 图标按钮组件

UI 升级方案 M5 / 4.2：统一图标按钮，替代侧边栏/工具栏裸 QPushButton。
图标经 icons.icon() 加载，支持 6 态（默认/悬停/按下/选中/禁用/焦点），
强制 20×20（或 24×24）图标尺寸与 accessibleName（可访问性）。
"""
from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QSize

from ui.styles import Colors, Fonts, Spacing, FOCUS_BORDER
from ui.components.icons import icon


class IconButton(QPushButton):
    """图标按钮：QIcon + 固定尺寸 + tooltip + accessibleName。

    用法：
        IconButton(icon_name='robot', tooltip='龙虎山大师兄解读',
                   accessible='AI 深度解读', parent=self)

    Args:
        icon_name:    图标名（icons.icon 的 name）。
        tooltip:      鼠标悬停提示。
        accessible:   无障碍名称（默认取 tooltip）。
        size:         图标尺寸档位（16/20/24/32/48），默认 20。
        checkable:    是否可选中（导航类按钮 True）。
        parent:       Qt 父控件。
    """

    def __init__(self, icon_name: str = '', tooltip: str = '',
                 accessible: str = None, size: int = 20,
                 checkable: bool = False, text: str = '', parent=None):
        super().__init__(text, parent)
        self._icon_name = icon_name
        self._size = size if size in (16, 20, 24, 32, 48) else 20

        # 图标
        try:
            self.setIcon(icon(icon_name, self._size))
            self.setIconSize(QSize(self._size, self._size))
        except Exception:
            # 图标缺失时保留文本/回退，不阻断
            if text:
                self.setText(text)

        # 可选文本（图标 + 文字同显）
        if text and icon_name:
            self.setText(f"  {text}")

        self.setCheckable(checkable)
        self.setToolTip(tooltip)
        # 可访问性：图标按钮 100% 具备 accessibleName
        self.setAccessibleName(accessible or tooltip or icon_name or '按钮')
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()

    def _apply_style(self):
        # 焦点环说明（必须留在 QSS 字符串**之外**）：
        #   · 用 border 而非 outline —— Qt QSS 不支持 outline（实测被静默忽略）；
        #   · 不能写 :focus:not(:disabled) —— Qt QSS 不支持 :not()，整条规则会失效。
        # ⚠️ QSS 的注释语法是 /* */，`#` 在 QSS 里是「对象名选择器」。
        #    曾把上面两行以 `#` 写进样式串，导致紧随其后的 QPushButton:focus 规则
        #    整体失效（实测聚焦时边框仍为默认 Colors.BORDER #33335a 而非 BRAND #c9a227，
        #    键盘焦点环不可见）。守卫见 scripts/audit_style_tokens.py::scan_qss_hash_comments。
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.TEXT3};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_SM};
                font-size: {Fonts.FS_BODY}px;
                font-family: {Fonts.BODY};
                font-weight: {Fonts.W_MEDIUM};
                padding: 6px 10px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background: {Colors.HOVER};
                color: {Colors.BRAND};
                border-color: {Colors.BRAND_LIGHT};
            }}
            QPushButton:pressed {{
                background: {Colors.BG_DARK};
            }}
            QPushButton:checked {{
                background: {Colors.BRAND_GLOW};
                color: {Colors.BRAND};
                border-color: {Colors.BRAND};
                font-weight: {Fonts.W_SEMIBOLD};
            }}
            QPushButton:disabled {{
                background: transparent;
                color: {Colors.TEXT4};
                border-color: {Colors.BORDER};
            }}
            QPushButton:focus {{
                border: {FOCUS_BORDER};
            }}
        """)

    def set_icon_color(self, color: str):
        """预留：动态图标着色（SVG currentColor 暂未实现，记录颜色）。"""
        self._icon_color = color
