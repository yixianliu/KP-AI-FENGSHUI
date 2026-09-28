"""
导出排盘结果对话框
提供 CSV / Excel / PDF 三种导出格式选择、可选导出章节（来自 ui.export.base_exporter.CHAPTERS）
以及导出文件名前缀；确认后通过 export_signal 抛出所选格式，交由主窗口驱动 ui/export/ 下的导出器。
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QCheckBox, QPushButton, QWidget,
                             QGroupBox, QLineEdit, QRadioButton,
                             QMessageBox, QGridLayout, QFrame, QScrollArea)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation

from ui.export.base_exporter import CHAPTERS
from ui.export.ai_titles import AI_SECTION_TITLE
from ui.styles import Colors, Spacing

# 章节分组定义（基础信息 / 命局分析 / 运程 / AI 解读），
# 用于 12.3 分组折叠卡片展示；本定义覆盖 CHAPTERS 全部 12 项。
_CHAPTER_GROUP_DEFS = [
    ('基础信息', '📋', ['basic_info']),
    ('命局分析', '☯',  ['bazi_types', 'bazi', 'wuxing', 'shishen',
                       'analysis', 'meihua', 'liuren']),
    ('运程',     '⏳', ['yunshi', 'yuncheng']),
    ('AI 解读',  '🧙', ['ai_analysis', 'zonghe']),
]


class ExportDialog(QDialog):
    """导出排盘结果对话框：选择格式 / 章节与文件名，确认后发出导出信号。"""
    export_signal = Signal(str)

    def __init__(self, data, parent=None):
        """初始化导出对话框。

        Args:
            data: 排盘结果数据（dict），用于推导默认文件名。
            parent: 父窗口（可选）。
        """
        super().__init__(parent)
        self.data = data
        self.init_ui()

    def init_ui(self):
        """构建导出对话框全部 UI：格式单选、章节勾选、文件名输入与操作按钮。"""
        self.setWindowTitle('导出排盘结果')
        self.setFixedSize(470, 560)
        # 浅色国风主题（宣纸-墨褐-古金）：模拟纸质报告，与深色主界面区分「成品态」。
        # 色值全部走 Colors 令牌（P14/P19），业务文件不写裸色值。
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.PAPER};
            }}
            QLabel {{
                color: {Colors.TEXT_PAPER};
                font-size: 13px;
            }}
            QGroupBox {{
                font-weight: bold;
                color: {Colors.INK_PAPER};
                border: 1px solid {Colors.GOLD_PAPER};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QComboBox {{
                padding: 8px 12px;
                border: 2px solid {Colors.GOLD_PAPER};
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
            }}
            QComboBox:focus {{
                border-color: {Colors.INK_PAPER};
            }}
            QCheckBox {{
                color: {Colors.TEXT_PAPER};
                font-size: 13px;
                padding: 3px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {Colors.GOLD_PAPER};
                border-radius: 4px;
                background-color: white;
            }}
            QCheckBox::indicator:checked {{
                background-color: {Colors.INK_PAPER};
                border-color: {Colors.INK_PAPER};
            }}
            QRadioButton {{
                color: {Colors.TEXT_PAPER};
                font-size: 13px;
                padding: 3px;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {Colors.GOLD_PAPER};
                border-radius: 9px;
                background-color: white;
            }}
            QRadioButton::indicator:checked {{
                background-color: {Colors.INK_PAPER};
                border-color: {Colors.INK_PAPER};
            }}
            QLineEdit {{
                padding: 8px 12px;
                border: 2px solid {Colors.GOLD_PAPER};
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
            }}
            QLineEdit:focus {{
                border-color: {Colors.INK_PAPER};
            }}
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.INK_PAPER}, stop:1 {Colors.INK_PAPER_DARK});
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.INK_PAPER_HOVER}, stop:1 {Colors.INK_PAPER_BORDER});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.INK_PAPER_DARK}, stop:1 {Colors.INK_PAPER_DARKEST});
            }}
            QPushButton#ghost {{
                background: transparent;
                color: {Colors.INK_PAPER};
                border: 1px solid {Colors.GOLD_PAPER};
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: normal;
            }}
            QPushButton#ghost:hover {{
                background: {Colors.PAPER_ACTIVE};
            }}
            /* 键盘焦点环（P17）：Qt QSS 不支持 outline，必须用 border。
               焦点色按背景反相选色——深褐渐变按钮用金，浅底控件用墨褐 */
            QPushButton:focus {{
                border: 2px solid {Colors.GOLD_PAPER};
            }}
            QPushButton#ghost:focus {{
                border-color: {Colors.INK_PAPER};
            }}
            QCheckBox:focus {{
                border: 2px solid {Colors.INK_PAPER};
            }}
            QRadioButton:focus {{
                border: 2px solid {Colors.INK_PAPER};
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(Spacing.S3)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel('导出排盘结果')
        title_label.setStyleSheet(f"""
            font-size: 17px;
            font-weight: bold;
            color: {Colors.INK_PAPER};
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # ---------- 导出格式（T6.3：单选按钮组升级为图标卡片） ----------
        format_group = QGroupBox('导出格式')
        format_layout = QVBoxLayout(format_group)
        format_layout.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）

        # 格式卡片数据：(属性名, 图标, 标题, 说明, 默认选中)
        fmt_specs = [
            ('csv',   '📄', 'CSV',   '兼容性强 · 文本表格',   True),
            ('excel', '📊', 'Excel', '推荐 · 斑马纹色阶',     False),
            ('pdf',   '📑', 'PDF',   '报告格式 · 适合打印',   False),
        ]
        fmt_card_row = QHBoxLayout()
        fmt_card_row.setSpacing(Spacing.S3)
        self._fmt_cards = {}
        for attr, icon, name, desc, default_checked in fmt_specs:
            card = _FormatCard(icon, name, desc)
            fmt_card_row.addWidget(card)
            self._fmt_cards[attr] = card
            # 保留原 QRadioButton 属性名（csv_radio/excel_radio/pdf_radio），
            # 让 on_export / get_selected_format 的既有 isChecked() 逻辑零变更复用
            setattr(self, f'{attr}_radio', card)
            if default_checked:
                card.setChecked(True)
        # 互斥：点击一张即取消其他
        for attr, card in self._fmt_cards.items():
            card.clicked.connect(lambda _=False, a=attr: self._select_format(a))
        format_layout.addLayout(fmt_card_row)

        # 格式说明文字（12.3：让用户明确各格式适用场景）
        self._fmt_hint = QLabel()
        self._fmt_hint.setWordWrap(True)
        self._fmt_hint.setStyleSheet(
            f'font-size: 11px; color: {Colors.TEXT_PAPER_DIM};'
            ' font-family: "Microsoft YaHei";')
        self._fmt_hint.setContentsMargins(2, 2, 2, 0)
        format_layout.addWidget(self._fmt_hint)
        self._update_fmt_hint('csv')

        layout.addWidget(format_group)

        # ---------- 导出内容（章节分组折叠卡片，12.3） ----------
        quick_row = QHBoxLayout()
        quick_row.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        self.select_all_btn = QPushButton('全选')
        self.select_all_btn.setObjectName('ghost')
        self.select_all_btn.clicked.connect(lambda: self._set_all(True))
        self.select_none_btn = QPushButton('全不选')
        self.select_none_btn.setObjectName('ghost')
        self.select_none_btn.clicked.connect(lambda: self._set_all(False))
        quick_row.addStretch()
        quick_row.addWidget(self.select_all_btn)
        quick_row.addWidget(self.select_none_btn)
        layout.addLayout(quick_row)

        # 章节分组折叠卡片（可滚动，避免窄高对话框溢出）
        self._chapter_scroll = QScrollArea()
        self._chapter_scroll.setWidgetResizable(True)
        self._chapter_scroll.setFrameShape(QFrame.NoFrame)
        self._chapter_scroll.setStyleSheet(
            'QScrollArea { background: transparent; border: none; }'
            'QScrollBar:vertical { background: transparent; width: 6px; margin: 0; }'
            f'QScrollBar::handle:vertical {{ background: {Colors.GOLD_PAPER};'
            ' border-radius: 3px; min-height: 20px; }}'
            'QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }'
        )
        chapter_widget = QWidget()
        chapter_widget.setStyleSheet('background: transparent;')
        chapter_layout = QVBoxLayout(chapter_widget)
        chapter_layout.setContentsMargins(0, 0, 0, 0)
        chapter_layout.setSpacing(Spacing.S3)
        self._build_chapter_groups(chapter_layout)
        chapter_layout.addStretch()
        self._chapter_scroll.setWidget(chapter_widget)
        layout.addWidget(self._chapter_scroll, 1)

        # ---------- 文件名 ----------
        filename_group = QGroupBox('文件名')
        filename_layout = QHBoxLayout(filename_group)
        filename_layout.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        filename_layout.addWidget(QLabel('前缀:'))
        self.filename_edit = QLineEdit()
        _dft = self.data.get('basic_info', {}).get('solar_date') or '八字排盘'
        self.filename_edit.setText(f"八字排盘_{_dft}")
        filename_layout.addWidget(self.filename_edit)
        layout.addWidget(filename_group)

        # ---------- 按钮 ----------
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        button_layout.addStretch()
        self.export_btn = QPushButton('导出')
        self.export_btn.clicked.connect(self.on_export)
        button_layout.addWidget(self.export_btn)
        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _set_all(self, checked: bool):
        """由「全选/全不选」按钮触发：批量设置所有章节勾选框状态。"""
        for cb in self._checks.values():
            cb.setChecked(checked)

    def _select_format(self, attr: str):
        """T6.3 格式卡片互斥选择：选中目标卡片、取消其余卡片。"""
        for a, card in self._fmt_cards.items():
            card.setChecked(a == attr)
        self._update_fmt_hint(attr)

    def _update_fmt_hint(self, attr: str):
        """更新格式说明文字（CSV/Excel/PDF 各自适用场景）。"""
        hints = {
            'csv':   'CSV · 纯文本表格，可被 Excel / 记事本 / 数据工具直接打开，适合二次处理',
            'excel': 'Excel · 斑马纹与色阶报告，适合数据筛选、分析与打印',
            'pdf':   'PDF · 报告式排版，适合分享、存档与打印',
        }
        try:
            self._fmt_hint.setText(hints.get(attr, ''))
        except RuntimeError:
            pass

    def _build_chapter_groups(self, container_layout):
        """构建章节分组折叠卡片，填充 self._checks（键顺序同 CHAPTERS）。

        分组定义见模块级 _CHAPTER_GROUP_DEFS；ai_analysis 的占位标签
        'universal.ai.SECTION_TITLE' 在此解析为真实标题 AI_SECTION_TITLE。
        """
        label_of = {}
        for key, label in CHAPTERS:
            if label == 'universal.ai.SECTION_TITLE':
                label = AI_SECTION_TITLE
            label_of[key] = label

        self._checks = {}
        for g_title, g_icon, keys in _CHAPTER_GROUP_DEFS:
            group = _ChapterGroup(g_title, g_icon)
            for key in keys:
                if key not in label_of:
                    continue
                cb = QCheckBox(label_of[key])
                cb.setChecked(True)
                group.add_check(cb)
                self._checks[key] = cb
            container_layout.addWidget(group)

    def get_selected_chapters(self):
        """返回勾选的章节 key 列表（顺序与 ui.export.base_exporter.CHAPTERS 一致）。"""
        return [key for key, _ in CHAPTERS
                if self._checks.get(key) and self._checks[key].isChecked()]

    def on_export(self):
        """由「导出」按钮 clicked 触发：确定格式、校验章节、发出 export_signal 并关闭。"""
        if self.csv_radio.isChecked():
            format_type = 'csv'
        elif self.excel_radio.isChecked():
            format_type = 'excel'
        else:
            format_type = 'pdf'

        if not self.get_selected_chapters():
            QMessageBox.warning(self, '请选择章节', '至少勾选一个导出章节。')
            return

        self.export_signal.emit(format_type)
        self.accept()

    def get_selected_format(self):
        """返回当前选中的导出格式字符串（'csv' / 'excel' / 'pdf'）。"""
        if self.csv_radio.isChecked():
            return 'csv'
        elif self.excel_radio.isChecked():
            return 'excel'
        else:
            return 'pdf'


class _FormatCard(QFrame):
    """T6.3 导出格式图标卡片：图标 + 标题 + 说明，可勾选互斥。

    替代原 QRadioButton，保留 setChecked/isChecked 语义，
    使 on_export / get_selected_format 的既有调用零变更。
    """

    clicked = Signal()

    def __init__(self, icon: str, title: str, desc: str, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedHeight(74)
        self.setMinimumWidth(110)
        self.setCursor(Qt.PointingHandCursor)

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(Spacing.S1)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet('font-size: 22px;')
        icon_lbl.setAlignment(Qt.AlignCenter)
        v.addWidget(icon_lbl)

        t = QLabel(title)
        t.setStyleSheet(f'font-weight: bold; font-size: 13px; color: {Colors.INK_PAPER};')
        t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)

        d = QLabel(desc)
        d.setStyleSheet(f'font-size: 11px; color: {Colors.TEXT_PAPER_DIM};')
        d.setAlignment(Qt.AlignCenter)
        v.addWidget(d)

        self._apply_style()

    def _apply_style(self):
        if self._checked:
            self.setStyleSheet(
                f'QFrame {{ background: {Colors.PAPER_LIGHT};'
                f' border: 2px solid {Colors.GOLD_PAPER}; border-radius: 8px; }}'
            )
        else:
            self.setStyleSheet(
                f'QFrame {{ background: white;'
                f' border: 2px solid {Colors.GOLD_PAPER}; border-radius: 8px; }}'
            )

    def setChecked(self, checked: bool):
        self._checked = checked
        self._apply_style()

    def isChecked(self) -> bool:
        return self._checked

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class _ClickableFrame(QFrame):
    """可点击标题栏：左键点击发出 clicked 信号（用于分组折叠/展开）。"""

    clicked = Signal()

    def mousePressEvent(self, event):  # noqa: N802（Qt 命名）
        """左键点击标题栏即触发折叠/展开。"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class _ChapterGroup(QFrame):
    """导出对话框浅色分组折叠卡片：标题栏可点击折叠/展开，内含章节勾选框。

    与对话框浅色国风主题（宣纸底 + 古金描边）保持一致；不使用深色
    CollapsibleCard，避免与对话框整体视觉冲突。折叠/展开用高度过渡动画。
    """

    def __init__(self, title: str, icon: str = '', parent=None):
        """构建分组卡片：浅金标题栏 + 可折叠内容容器。

        Args:
            title: 分组标题（基础信息/命局分析/运程/AI 解读）。
            icon:  标题左侧图标字符。
            parent: Qt 父控件。
        """
        super().__init__(parent)
        self._collapsed = False
        self.setStyleSheet(
            f'QFrame {{ background: white; border: 1px solid {Colors.PAPER_BORDER};'
            ' border-radius: 8px; }}'
        )
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(Spacing.S0)

        header = _ClickableFrame()
        header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet(
            f'QFrame {{ background: {Colors.PAPER_HOVER}; border: none;'
            ' border-top-left-radius: 8px; border-top-right-radius: 8px; }}'
        )
        header.clicked.connect(self.toggle)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 10, 12, 10)
        hl.setSpacing(Spacing.S2)

        bar = QFrame()
        bar.setFixedSize(4, 18)
        bar.setStyleSheet(f'background: {Colors.GOLD_PAPER}; border-radius: 2px;')
        ic = QLabel(icon)
        ic.setStyleSheet('font-size: 15px; background: transparent;')
        ic.setFixedWidth(22)
        ttl = QLabel(title)
        ttl.setStyleSheet(
            f'font-size: 13px; font-weight: bold; color: {Colors.INK_PAPER};'
            ' font-family: "Microsoft YaHei"; background: transparent;')
        self._chevron = QLabel('▼')
        self._chevron.setStyleSheet(f'font-size: 11px; color: {Colors.GOLD_PAPER_DARK};')
        self._chevron.setFixedWidth(14)
        self._chevron.setAlignment(Qt.AlignCenter)

        hl.addWidget(bar)
        hl.addWidget(ic)
        hl.addWidget(ttl)
        hl.addStretch()
        hl.addWidget(self._chevron)
        main.addWidget(header)

        self._content = QWidget()
        self._content.setStyleSheet('background: transparent;')
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(14, 10, 14, 12)
        self._content_layout.setSpacing(Spacing.S2)
        main.addWidget(self._content)

    def add_check(self, cb: QCheckBox):
        """向分组内容区追加一个章节勾选框。"""
        self._content_layout.addWidget(cb)

    def toggle(self):
        """切换折叠/展开状态。"""
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool, animated: bool = True):
        """设置折叠状态（高度过渡动画）。"""
        if collapsed == self._collapsed:
            return
        self._collapsed = bool(collapsed)
        self._chevron.setText('▶' if self._collapsed else '▼')
        c = self._content
        if not animated:
            c.setVisible(not self._collapsed)
            c.setMaximumHeight(0 if self._collapsed else 16777215)
            return
        if self._collapsed:
            start = c.height()
            c.setMaximumHeight(start)
            anim = QPropertyAnimation(c, b'maximumHeight', c)
            anim.setDuration(180)
            anim.setStartValue(start)
            anim.setEndValue(0)
            anim.finished.connect(lambda: c.setVisible(False))
            anim.start()
        else:
            c.setVisible(True)
            c.setMaximumHeight(0)
            target = c.sizeHint().height()
            anim = QPropertyAnimation(c, b'maximumHeight', c)
            anim.setDuration(220)
            anim.setStartValue(0)
            anim.setEndValue(target)
            anim.finished.connect(lambda: c.setMaximumHeight(16777215))
            anim.start()
