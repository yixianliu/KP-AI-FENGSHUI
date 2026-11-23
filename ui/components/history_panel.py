# -*- coding: utf-8 -*-
"""
ui/components/history_panel.py — 历史记录面板

功能：
    - 板块过滤（全部 / 八字 / 梅花 / 玄空）+ 日期范围 + 关键字搜索（300ms 防抖）
    - 分页列表（默认 50 条/页），展示时间、板块、摘要、是否已有 AI 解读
    - 多选 + 详情预览（选中单条时展示输入参数与结论摘要）
    - 载入 / 批量删除（二次确认）
    - 后台线程执行查询，避免阻塞 UI

对外只暴露意图信号，不直接改写其它板块控件：
    load_requested(str pan_kind, int record_id, object payload)
    delete_requested(object entries)   # [{'source_table': ..., 'id': ...}]
    refresh_requested()

注意：数据横跨 pan_records 与 analysis_records 两张表，二者 id 空间独立，
因此删除信号中每条记录都携带 source_table，不能只传裸 id。
"""
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QDate, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDateEdit, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QSplitter,
    QStackedWidget, QTableWidget, QTableWidgetItem, QTextBrowser,
    QVBoxLayout, QWidget,
)

from ui.styles import Colors, Fonts, Spacing, Stylesheets
from ui.components.states import EmptyState, ErrorState
from ui.thread_shutdown import shutdown_threads

# 板块下拉项：(显示文案, 内部 kind)
_KIND_OPTIONS = (
    ('全部', ''),
    ('八字', 'bazi'),
    ('梅花', 'meihua'),
    ('玄空', 'xuan_kong'),
)

# 列表列索引
_COL_TIME, _COL_KIND, _COL_TITLE, _COL_AI = range(4)

#: 响应式分档阈值（按**面板自身可用宽度**，不是窗口宽度）
#: - ≥ WIDE：筛选一行 + 底栏一行 + 四列全显示
#: - MEDIUM~WIDE：搜索独立一行 + 底栏两行 + 隐藏「时间」列
#: - < MEDIUM：筛选两行 + 底栏两行 + 图标按钮 + 仅保留「摘要 / AI」列
TIER_WIDE_MIN = 560
TIER_MEDIUM_MIN = 480
#: 面板允许被压缩到的最窄宽度。布局在宽档下的最小宽约 590（底栏一行 + 四列），
#: 若不放开这个下限，左栏给 350px 时面板根本不会被缩窄，也就永远进不了窄档。
MIN_PANEL_WIDTH = 320


class HistoryQueryThread(QThread):
    """一次性后台查询线程：执行任意无参 callable，成功/失败分别发信号。"""

    loaded = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self):  # pragma: no cover - Qt 线程入口，逻辑由面板测试覆盖
        # 协作式取消：尚未开始查询时直接退出；SQLite 查询本身不可中断，
        # 已进入的查询允许跑完，但结果不再发信号（面板可能已随窗口销毁）。
        if self.isInterruptionRequested():
            return
        try:
            result = self._fn()
        except Exception as exc:  # noqa: BLE001 - 查询失败需完整回报给 UI
            if not self.isInterruptionRequested():
                self.failed.emit(str(exc))
            return
        if self.isInterruptionRequested():
            return
        self.loaded.emit(result)


class HistoryPanel(QWidget):
    """历史记录面板（可独立构造，不依赖主窗口）。"""

    load_requested = Signal(str, int, object)
    delete_requested = Signal(object)
    refresh_requested = Signal()

    def __init__(self, db=None, page_size: int = 50, async_mode: bool = True,
                 confirm_callback=None, parent=None):
        """
        Args:
            db: DatabaseManager 实例；None 时首次查询懒加载 get_db_manager()
            page_size: 每页条数（1~200）
            async_mode: True 用 QThread 查库；False 同步（测试 / 调试用）
            confirm_callback: 删除确认回调 (panel, count) -> bool；
                              默认弹 QMessageBox，测试可注入
            parent: Qt 父控件
        """
        super().__init__(parent)
        self.setObjectName('history-panel')

        self._db = db
        self.page_size = max(1, min(int(page_size), 200))
        self._async_mode = async_mode
        self._confirm_callback = confirm_callback

        self._page = 1
        self._pages = 0
        self._total = 0
        self._items: List[Dict[str, Any]] = []
        self._thread: Optional[HistoryQueryThread] = None
        self._pending_refresh = False
        self._detail_entry: Optional[Dict[str, Any]] = None

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(lambda: self._request_page(1))

        #: 当前响应式档位（None = 尚未应用，首次 _apply_tier 时按实际宽度判定）
        self._tier = None

        self._build_ui()
        self._connect_signals()
        # 显式下限：布局在宽档下的最小宽约 590，不设这个下限面板无法被压窄
        self.setMinimumWidth(MIN_PANEL_WIDTH)
        # 构造即按当前宽度定档（默认 640px 为 WIDE，保证「第 1 / 3 页」等既有文案）
        self._apply_tier(self._tier_for_width(self.width()))

    # ==================== UI 构建 ====================

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.S6, Spacing.S6, Spacing.S6, Spacing.S6)
        root.setSpacing(Spacing.S4)

        # ---- 标题区 ----
        header = QHBoxLayout()
        header.setSpacing(Spacing.S2)
        title = QLabel('历史记录')
        title.setStyleSheet(
            f"font-family:{Fonts.TITLE}; font-size:{Fonts.FS_H1}px; "
            f"color:{Colors.TEXT}; background:transparent;")
        header.addWidget(title)
        subtitle = QLabel('归档的排盘与解读记录，可直接载入或批量清理')
        subtitle.setStyleSheet(
            f"font-family:{Fonts.BODY}; font-size:{Fonts.FS_CAPTION}px; "
            f"color:{Colors.TEXT3}; background:transparent;")
        header.addWidget(subtitle)
        header.addStretch(1)

        self.refresh_btn = QPushButton('刷新')
        self.refresh_btn.setStyleSheet(Stylesheets.BTN_ICON)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.refresh_btn)
        root.addLayout(header)

        # ---- 筛选区 ----
        root.addWidget(self._build_filter_card())

        # ---- 主体（列表 + 详情 / 空态 / 错误 / 加载） ----
        self.stack = QStackedWidget()
        self.content = self._build_content()
        self.stack.addWidget(self.content)                      # 0 内容

        self.empty_state = EmptyState(
            title='暂无历史记录',
            hint='完成一次排盘后，记录会自动归档到这里；也可调整筛选条件后重试。',
            icon='☷', parent=self, breathe=False, fade_in=False)
        self.stack.addWidget(self.empty_state)                  # 1 空态

        self.error_holder = QWidget()
        self._error_layout = QVBoxLayout(self.error_holder)
        self._error_layout.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self.error_holder)                 # 2 错误

        self.loading_label = QLabel('正在加载历史记录…')
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet(
            f"font-family:{Fonts.BODY}; font-size:{Fonts.FS_BODY}px; "
            f"color:{Colors.TEXT3}; background:transparent;")
        self.stack.addWidget(self.loading_label)                # 3 加载

        root.addWidget(self.stack, 1)

        # ---- 底栏（分页 + 操作） ----
        root.addWidget(self._build_footer())

    def _build_filter_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName('history-filter-card')
        card.setStyleSheet(f"""
            QFrame#history-filter-card {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS};
            }}
            QLabel {{
                background: transparent;
                color: {Colors.TEXT3};
                font-family: {Fonts.BODY};
                font-size: {Fonts.SZ_SMALL};
                border: none;
            }}
            QCheckBox {{
                background: transparent;
                color: {Colors.TEXT3};
                font-family: {Fonts.BODY};
                font-size: {Fonts.SZ_SMALL};
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 14px; height: 14px;
                border: 1px solid {Colors.BORDER2};
                border-radius: 3px;
                background: {Colors.BG_DARK};
            }}
            QCheckBox::indicator:checked {{
                background: {Colors.BRAND};
                border-color: {Colors.BRAND};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.S4, Spacing.S3, Spacing.S4, Spacing.S3)
        layout.setSpacing(Spacing.S2)

        # 用 QGridLayout：三档只改「控件所在行列」，不重建控件（不丢焦点与信号）
        self._filter_grid = QGridLayout()
        self._filter_grid.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        self._filter_grid.setSpacing(Spacing.S2)
        layout.addLayout(self._filter_grid)

        self._kind_label = QLabel('板块')
        self._kind_label.setFixedWidth(32)
        self.kind_combo = QComboBox()
        self.kind_combo.setStyleSheet(Stylesheets.COMBO)
        self.kind_combo.setMinimumWidth(110)
        for text, kind in _KIND_OPTIONS:
            self.kind_combo.addItem(text, kind)

        self._kw_label = QLabel('关键字')
        self._kw_label.setFixedWidth(48)
        self.search_edit = QLineEdit()
        self.search_edit.setStyleSheet(Stylesheets.INPUT)
        self.search_edit.setPlaceholderText('搜索姓名 / 出生地 / 日期 / 卦名 / 结论')
        self.search_edit.setClearButtonEnabled(True)
        # 窄档下搜索框独占一行，给足可输入宽度；宽档与板块同一行
        self._filter_grid.addWidget(self._kind_label, 0, 0)
        self._filter_grid.addWidget(self.kind_combo, 0, 1)
        self._filter_grid.addWidget(self._kw_label, 0, 2)
        self._filter_grid.addWidget(self.search_edit, 0, 3)
        self._filter_grid.setColumnStretch(3, 1)

        # 日期行：独立网格容器，窄档改为竖排（两个 QDateEdit 并排会撑破 350px）
        self._date_wrap = QWidget()
        self._date_wrap.setStyleSheet('background: transparent;')
        self._date_grid = QGridLayout(self._date_wrap)
        self._date_grid.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        self._date_grid.setSpacing(Spacing.S2)

        self.date_enabled = QCheckBox('按日期筛选')
        self.date_enabled.setCursor(Qt.PointingHandCursor)

        self.date_from = QDateEdit()
        self.date_from.setStyleSheet(Stylesheets.DATE)
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat('yyyy-MM-dd')
        self.date_from.setDate(QDate(2000, 1, 1))
        self.date_to = QDateEdit()
        self.date_to.setStyleSheet(Stylesheets.DATE)
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat('yyyy-MM-dd')
        self.date_to.setDate(QDate.currentDate())
        self._date_until_label = QLabel('至')
        self.date_from.setEnabled(False)
        self.date_to.setEnabled(False)

        # 默认（宽档）位置：一行四项 + 末尾伸展
        self._date_grid.addWidget(self.date_enabled, 0, 0)
        self._date_grid.addWidget(self.date_from, 0, 1)
        self._date_grid.addWidget(self._date_until_label, 0, 2)
        self._date_grid.addWidget(self.date_to, 0, 3)
        self._date_grid.setColumnStretch(3, 1)

        self._filter_grid.addWidget(self._date_wrap, 1, 0, 1, 4)
        return card

    def _build_content(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        # ---- 列表 ----
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['时间', '板块', '摘要', 'AI'])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.setStyleSheet(self._table_qss())
        # 列宽由 _apply_tier 按档位调整；表格本身不设最小宽，横向滚动条按需出现
        self.table.setMinimumWidth(0)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(Spacing.S4)
        header.setSectionResizeMode(_COL_TIME, QHeaderView.Fixed)
        header.setSectionResizeMode(_COL_KIND, QHeaderView.Fixed)
        header.setSectionResizeMode(_COL_TITLE, QHeaderView.Stretch)
        header.setSectionResizeMode(_COL_AI, QHeaderView.Fixed)
        self.table.setColumnWidth(_COL_TIME, 168)
        self.table.setColumnWidth(_COL_KIND, 64)
        self.table.setColumnWidth(_COL_AI, 76)
        splitter.addWidget(self.table)

        # ---- 详情 ----
        detail_card = QFrame()
        detail_card.setObjectName('history-detail-card')
        detail_card.setStyleSheet(f"""
            QFrame#history-detail-card {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(Spacing.S4, Spacing.S3, Spacing.S4, Spacing.S3)
        detail_layout.setSpacing(Spacing.S2)

        detail_header = QHBoxLayout()
        self.detail_title = QLabel('详情预览')
        self.detail_title.setStyleSheet(
            f"font-family:{Fonts.BODY}; font-size:{Fonts.FS_H3}px; "
            f"font-weight:{Fonts.W_MEDIUM}; color:{Colors.BRAND};")
        detail_header.addWidget(self.detail_title)
        detail_header.addStretch(1)
        self.detail_toggle = QPushButton('收起')
        self.detail_toggle.setStyleSheet(Stylesheets.BTN_ICON)
        self.detail_toggle.setCursor(Qt.PointingHandCursor)
        self.detail_toggle.setCheckable(True)
        self.detail_toggle.setChecked(True)
        detail_header.addWidget(self.detail_toggle)
        detail_layout.addLayout(detail_header)

        self.detail_body = QTextBrowser()
        self.detail_body.setOpenLinks(False)
        self.detail_body.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {Colors.BG_DARK};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_SM};
                color: {Colors.TEXT2};
                padding: {Spacing.S3}px;
                font-family: {Fonts.BODY};
                font-size: {Fonts.FS_BODY}px;
            }}
        """)
        self.detail_body.setPlainText('选中一条记录后，这里显示输入参数与结论摘要。')
        detail_layout.addWidget(self.detail_body, 1)
        splitter.addWidget(detail_card)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([360, 240])
        return splitter

    def _build_footer(self) -> QWidget:
        """底栏：页码 + 提示 + 操作按钮。

        用 QGridLayout 承载，档位切换时只重排行列：
        宽档一行（页码…提示…载入/删除），中/窄档拆两行（页码一行、操作一行），
        避免 350px 宽时按钮被压到 39px 不可点击。
        """
        footer = QWidget()
        footer.setStyleSheet('background: transparent;')
        self._footer_grid = QGridLayout(footer)
        self._footer_grid.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        self._footer_grid.setSpacing(Spacing.S2)

        self.prev_btn = QPushButton('上一页')
        self.prev_btn.setStyleSheet(Stylesheets.BTN_ICON)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setEnabled(False)
        self.next_btn = QPushButton('下一页')
        self.next_btn.setStyleSheet(Stylesheets.BTN_ICON)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setEnabled(False)
        self.page_label = QLabel('第 0 / 0 页')
        self.page_label.setStyleSheet(
            f"font-family:{Fonts.BODY}; font-size:{Fonts.FS_CAPTION}px; "
            f"color:{Colors.TEXT3}; background:transparent;")
        self.total_label = QLabel('共 0 条')
        self.total_label.setStyleSheet(
            f"font-family:{Fonts.BODY}; font-size:{Fonts.FS_CAPTION}px; "
            f"color:{Colors.TEXT3}; background:transparent;")

        self.hint_label = QLabel('')
        self.hint_label.setStyleSheet(
            f"font-family:{Fonts.BODY}; font-size:{Fonts.FS_CAPTION}px; "
            f"color:{Colors.TEXT3}; background:transparent;")

        self.load_btn = QPushButton('载入')
        self.load_btn.setStyleSheet(Stylesheets.BTN_6STATE_SECONDARY)
        self.load_btn.setCursor(Qt.PointingHandCursor)
        self.load_btn.setEnabled(False)
        self.load_btn.setToolTip('载入选中的记录')
        self.delete_btn = QPushButton('删除')
        self.delete_btn.setStyleSheet(Stylesheets.BTN_6STATE_DANGER)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setToolTip('删除选中的记录')

        # 默认（宽档）一行排布；窄档由 _apply_tier 重排
        for col, widget in enumerate((self.prev_btn, self.page_label, self.next_btn,
                                      self.total_label, self.hint_label,
                                      self.load_btn, self.delete_btn)):
            self._footer_grid.addWidget(widget, 0, col)
        self._footer_grid.setColumnStretch(4, 1)
        return footer

    @staticmethod
    def _table_qss() -> str:
        return f"""
            QTableWidget {{
                background-color: {Colors.CARD};
                alternate-background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS};
                gridline-color: {Colors.DIVIDER};
                color: {Colors.TEXT};
                font-family: {Fonts.BODY};
                font-size: {Fonts.SZ_BODY};
                selection-background-color: {Colors.CARD_SELECTED};
                selection-color: {Colors.TEXT};
            }}
            QTableWidget::item {{
                padding: 4px 8px;
                border: none;
            }}
            QTableWidget::item:hover {{
                background-color: {Colors.HOVER};
            }}
            QHeaderView::section {{
                background-color: {Colors.BG_DARK};
                color: {Colors.TEXT3};
                border: none;
                border-bottom: 1px solid {Colors.DIVIDER};
                padding: 8px;
                font-family: {Fonts.BODY};
                font-size: {Fonts.SZ_SMALL};
            }}
            QTableCornerButton::section {{
                background-color: {Colors.BG_DARK};
                border: none;
            }}
        """

    def _connect_signals(self):
        self.refresh_btn.clicked.connect(self.refresh)
        self.kind_combo.currentIndexChanged.connect(lambda _: self._request_page(1))
        self.search_edit.textChanged.connect(lambda _: self._search_timer.start())
        self.date_enabled.toggled.connect(self._on_date_enabled)
        self.date_from.dateChanged.connect(self._on_date_changed)
        self.date_to.dateChanged.connect(self._on_date_changed)
        self.prev_btn.clicked.connect(lambda: self._request_page(self._page - 1))
        self.next_btn.clicked.connect(lambda: self._request_page(self._page + 1))
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.cellDoubleClicked.connect(lambda *_: self._on_load_clicked())
        self.load_btn.clicked.connect(self._on_load_clicked)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.detail_toggle.toggled.connect(self._on_toggle_detail)

    # ==================== 响应式档位 ====================

    @staticmethod
    def _tier_for_width(width: int) -> str:
        """按面板自身可用宽度判定档位。

        Returns:
            str: ``'wide'``（≥560）/ ``'medium'``（480~559）/ ``'narrow'``（<480）。
        """
        if width >= TIER_WIDE_MIN:
            return 'wide'
        if width >= TIER_MEDIUM_MIN:
            return 'medium'
        return 'narrow'

    def resizeEvent(self, event):
        """宽度变化时重定档位；档位未变则不动布局，避免拖拽窗口时抖动。"""
        super().resizeEvent(event)
        self._apply_tier(self._tier_for_width(self.width()))

    def minimumSizeHint(self):
        """放开宽度下限：宽档布局的最小宽约 590，会把面板钉死，永远进不了窄档。

        这里只压宽度上限，高度仍按布局实际需求，避免面板被压扁。
        """
        base = super().minimumSizeHint()
        return QSize(min(base.width(), MIN_PANEL_WIDTH), base.height())

    @staticmethod
    def _place(layout, widget, row: int, col: int, row_span: int = 1, col_span: int = 1):
        """把控件移到网格指定格子（先摘除再插入，不保留旧格子占位）。"""
        layout.removeWidget(widget)
        layout.addWidget(widget, row, col, row_span, col_span)

    def _place_hint(self):
        """提示语定位：宽档「空文案不占位、有文案独占第二行」，中/窄档固定第二行。

        宽档 7 个控件并排时提示语只剩 12px（错误反馈等于不可读），因此空文案
        直接隐藏、有文案时让出整行；中/窄档底栏本就是两行，提示固定第二行。
        """
        if self._tier == 'wide' and not self.hint_label.text():
            self._place(self._footer_grid, self.hint_label, 0, 4)
            self.hint_label.hide()
            return
        span = 7 if self._tier == 'wide' else 5
        self._place(self._footer_grid, self.hint_label, 1, 0, 1, span)
        self.hint_label.show()

    def _apply_tier(self, tier: str):
        """应用档位：只调排布与文案，不改任何颜色 / 圆角 / 字体令牌。

        - 筛选区：宽档「板块 + 关键字」一行；中/窄档关键字独占一行。
        - 日期行：窄档竖排（起始 / 结束各占一整行），中档起折行。
        - 表格：宽档四列；中档隐藏「时间」；窄档再隐藏「板块」，仅留「摘要 / AI」。
        - 底栏：宽档默认一行（提示为空时隐藏，有提示才临时占第二行，避免 590px
          时提示语被挤到 12px）；中/窄档固定两行（页码一行、提示+操作一行）；
          窄档按钮改图标。
        """
        if tier == self._tier:
            return
        self._tier = tier
        wide = tier == 'wide'
        narrow = tier == 'narrow'

        # ---- 筛选区 ----
        if wide:
            self._place(self._filter_grid, self._kw_label, 0, 2)
            self._place(self._filter_grid, self.search_edit, 0, 3)
            self._place(self._filter_grid, self._date_wrap, 1, 0, 1, 4)
        else:
            self._place(self._filter_grid, self._kw_label, 1, 0)
            self._place(self._filter_grid, self.search_edit, 1, 1, 1, 3)
            self._place(self._filter_grid, self._date_wrap, 2, 0, 1, 4)

        # ---- 日期行：窄档竖排，两个日期框各占一整行 ----
        if narrow:
            self._date_until_label.hide()
            self._place(self._date_grid, self.date_enabled, 0, 0, 1, 2)
            self._place(self._date_grid, self.date_from, 1, 0, 1, 2)
            self._place(self._date_grid, self.date_to, 2, 0, 1, 2)
        else:
            self._date_until_label.show()
            self._place(self._date_grid, self.date_enabled, 0, 0)
            self._place(self._date_grid, self.date_from, 0, 1)
            self._place(self._date_grid, self._date_until_label, 0, 2)
            self._place(self._date_grid, self.date_to, 0, 3)
        self.date_from.setToolTip('起始日期')
        self.date_to.setToolTip('结束日期')

        # ---- 表格列 ----
        self.table.setColumnHidden(_COL_TIME, not wide)
        self.table.setColumnHidden(_COL_KIND, narrow)
        self.table.setColumnWidth(_COL_KIND, 56 if not wide else 64)
        self.table.setColumnWidth(_COL_AI, 64 if not wide else 76)

        # ---- 底栏：先摆页码行与操作按钮，提示语统一由 _place_hint 定位 ----
        self.hint_label.setWordWrap(not wide)
        for col, widget in enumerate((self.prev_btn, self.page_label, self.next_btn,
                                      self.total_label)):
            self._place(self._footer_grid, widget, 0, col)
        row = 0 if wide else 1
        self._place(self._footer_grid, self.load_btn, row, 5)
        self._place(self._footer_grid, self.delete_btn, row, 6)
        self._place_hint()
        for col in range(7):
            self._footer_grid.setColumnStretch(col, 1 if col == 4 else 0)

        # ---- 档位文案：窄档页码压缩为「1 / 12」，按钮只留图标 ----
        if narrow:
            self.search_edit.setPlaceholderText('搜索姓名 / 地点 / 卦名')
            self.prev_btn.setText('‹')
            self.next_btn.setText('›')
            self.load_btn.setText('↧')
            self.delete_btn.setText('✕')
            self.load_btn.setToolTip('载入选中的记录')
            self.delete_btn.setToolTip('删除选中的记录')
            hit = Spacing.S8 - Spacing.S1      # 44×44 可点击下限
            for btn in (self.prev_btn, self.next_btn, self.load_btn, self.delete_btn):
                # 图标按钮的下限取 max(44, 自身 sizeHint)：QSS 左右各 20px 内边距，
                # 只给 44px 会把图标挤没（实测 ↧/✕ 需要 55px）
                btn.setMinimumSize(max(hit, btn.sizeHint().width()), hit)
        else:
            self.search_edit.setPlaceholderText(
                '搜索姓名 / 出生地 / 卦名 / 结论' if wide
                else '搜索姓名 / 出生地 / 卦名')
            self.prev_btn.setText('上一页')
            self.next_btn.setText('下一页')
            self.load_btn.setText('载入')
            self.delete_btn.setText('删除')
            self.prev_btn.setToolTip('')
            self.next_btn.setToolTip('')
            self.load_btn.setToolTip('载入选中的记录')
            self.delete_btn.setToolTip('删除选中的记录')
            for btn in (self.prev_btn, self.next_btn, self.load_btn, self.delete_btn):
                # 网格在 489px 时会把「载入」压到 67（缺 1px），按 sizeHint 定下限；
                # 高度固定 44（Spacing.S8-S1）：两行底栏的行高会塌到 42，低于点击下限
                btn.setMinimumSize(btn.sizeHint().width(), Spacing.S8 - Spacing.S1)

        self._update_pager()

    # ==================== 查询 ====================

    def _ensure_db(self):
        """懒加载数据库管理器；不可用时返回 None，由上层展示明确错误文案。"""
        if self._db is not None:
            return self._db
        try:
            from core.database_manager import get_db_manager
            self._db = get_db_manager()
        except Exception as exc:  # noqa: BLE001 - 数据库未就绪需要展示给用户
            self._db = None
            self._last_db_error = str(exc)
        return self._db

    def _current_kind(self) -> Optional[str]:
        kind = self.kind_combo.currentData()
        return kind or None

    def _current_filters(self) -> Dict[str, str]:
        with_dates = self.date_enabled.isChecked()
        return {
            'pan_kind': self._current_kind() or '',
            'keyword': self.search_edit.text().strip(),
            'date_from': self.date_from.date().toString('yyyy-MM-dd') if with_dates else '',
            'date_to': self.date_to.date().toString('yyyy-MM-dd') if with_dates else '',
        }

    def _fetch(self) -> dict:
        db = self._ensure_db()
        if db is None:
            raise RuntimeError('数据库未就绪，请稍后重试或检查 data/fengshui.db')
        filters = self._current_filters()
        return db.get_history_page(
            pan_kind=filters['pan_kind'] or None,
            keyword=filters['keyword'],
            date_from=filters['date_from'],
            date_to=filters['date_to'],
            page=self._page,
            page_size=self.page_size,
        )

    def refresh(self, reset_page: bool = True):
        """重新查询当前筛选条件下的数据（默认回到第 1 页）。"""
        self.refresh_requested.emit()
        self._request_page(1 if reset_page else self._page)

    def _request_page(self, page: int):
        self._page = max(1, int(page))
        self._set_busy(True)
        self.stack.setCurrentIndex(3)

        if not self._async_mode:
            try:
                data = self._fetch()
            except Exception as exc:  # noqa: BLE001
                self._on_query_failed(str(exc))
            else:
                self._on_query_loaded(data)
            return

        # 后台线程：同一时刻只跑一个查询，期间的新请求合并为一次待办
        if self._thread is not None and self._thread.isRunning():
            self._pending_refresh = True
            return
        self._thread = HistoryQueryThread(self._fetch, parent=self)
        self._thread.loaded.connect(self._on_query_loaded)
        self._thread.failed.connect(self._on_query_failed)
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.start()

    def _on_thread_finished(self):
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None
        if self._pending_refresh:
            self._pending_refresh = False
            self._request_page(self._page)

    def active_query_thread(self):
        """返回当前在途的历史查询线程（无则 None），供主窗口关窗统一收尾。"""
        return self._thread

    def shutdown_query(self, timeout_ms: int = 3000) -> list:
        """协作式收尾在途查询线程，返回超时仍未结束（已托管）的线程列表。"""
        thread = self._thread
        if thread is None:
            return []
        still_running = shutdown_threads([thread], timeout_ms)
        if not still_running:
            # 已结束：由 _on_thread_finished 的 finished 信号负责 deleteLater，
            # 这里只清引用，避免后续再次启动查询时误判为“仍在运行”。
            self._thread = None
        return still_running

    def _on_query_loaded(self, data: dict):
        self._set_busy(False)
        self._items = list(data.get('items') or [])
        self._total = int(data.get('total') or 0)
        self._pages = int(data.get('pages') or 0)

        # 页码越界（删除后常见）：收敛到最后一页重新查询
        if self._pages and self._page > self._pages:
            self._page = self._pages
            self._request_page(self._page)
            return

        self._fill_table(self._items)
        self._update_pager()
        if self._items:
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)
        self._set_hint('')

    def _on_query_failed(self, message: str):
        self._set_busy(False)
        self._items = []
        self._fill_table([])
        self._pages = 0
        self._total = 0
        self._update_pager()
        self._show_error(message or '查询失败，请重试')

    def _show_error(self, message: str):
        while self._error_layout.count():
            item = self._error_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        error = ErrorState(
            title='历史记录加载失败',
            message=message,
            retry_hint='重试',
            parent=self.error_holder)
        error.retry.connect(lambda: self._request_page(self._page))
        self._error_layout.addWidget(error)
        self.stack.setCurrentIndex(2)

    # ==================== 列表渲染 ====================

    def _fill_table(self, items: List[Dict[str, Any]]):
        self.table.blockSignals(True)
        self.table.clearContents()
        self.table.setRowCount(len(items))
        for row, entry in enumerate(items):
            time_item = QTableWidgetItem(str(entry.get('created_at') or ''))
            time_item.setToolTip(str(entry.get('created_at') or ''))
            kind_item = QTableWidgetItem(str(entry.get('pan_label') or '其它'))
            kind_item.setTextAlignment(Qt.AlignCenter)
            title_item = QTableWidgetItem(str(entry.get('title') or ''))
            title_item.setToolTip(str(entry.get('title') or ''))
            has_ai = bool(entry.get('has_ai'))
            ai_item = QTableWidgetItem('已有' if has_ai else '—')
            ai_item.setTextAlignment(Qt.AlignCenter)
            ai_item.setForeground(QBrush(QColor(
                Colors.BRAND if has_ai else Colors.TEXT4)))

            # 每行把完整标识挂在首列，供选择/载入/删除取用
            time_item.setData(Qt.UserRole, {
                'source_table': entry.get('source_table'),
                'id': int(entry.get('id') or 0),
                'pan_kind': entry.get('pan_kind') or '',
            })
            self.table.setItem(row, _COL_TIME, time_item)
            self.table.setItem(row, _COL_KIND, kind_item)
            self.table.setItem(row, _COL_TITLE, title_item)
            self.table.setItem(row, _COL_AI, ai_item)
        self.table.blockSignals(False)
        self.table.clearSelection()
        self.load_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self._render_detail(None)

    def _update_pager(self):
        # 窄档页码压缩为「1 / 12」，中/宽档保留完整文案（既有用例依赖后者）
        pages = self._pages or 0
        if self._tier == 'narrow':
            self.page_label.setText(f'{self._page} / {pages}')
        else:
            self.page_label.setText(f'第 {self._page} / {pages} 页')
        self.total_label.setText(f'共 {self._total} 条')
        # 页码/统计按当前文案实测宽度设下限：网格里这两个标签没有伸展列，
        # 不设下限会被压到 44px（实测「第 1 / 1 页」需要 72px + 内边距）
        for label in (self.page_label, self.total_label):
            label.setMinimumWidth(
                label.fontMetrics().horizontalAdvance(label.text()) + Spacing.S2)
        self.prev_btn.setEnabled(self._page > 1)
        self.next_btn.setEnabled(self._pages > 0 and self._page < self._pages)

    def _set_busy(self, busy: bool):
        for widget in (self.kind_combo, self.search_edit, self.refresh_btn,
                       self.prev_btn, self.next_btn):
            widget.setEnabled(not busy)
        if busy:
            self.load_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def _set_hint(self, text: str, warning: bool = False):
        color = Colors.WARNING if warning else Colors.TEXT3
        self.hint_label.setStyleSheet(
            f"font-family:{Fonts.BODY}; font-size:{Fonts.FS_CAPTION}px; "
            f"color:{color}; background:transparent;")
        self.hint_label.setText(text)
        # 悬浮可见完整文案（窄档提示会换行，宽档独占一行时也可能被按钮挤窄）
        self.hint_label.setToolTip(text)
        self._place_hint()

    # ==================== 选择 / 详情 ====================

    def selected_entries(self) -> List[Dict[str, Any]]:
        """返回当前选中的记录标识列表（每项含 source_table / id / pan_kind）。"""
        model = self.table.selectionModel()
        if model is None:
            return []
        entries = []
        for index in model.selectedRows():
            item = self.table.item(index.row(), _COL_TIME)
            data = item.data(Qt.UserRole) if item is not None else None
            if isinstance(data, dict):
                entries.append(dict(data))
        return entries

    def _on_selection_changed(self):
        entries = self.selected_entries()
        count = len(entries)
        self.load_btn.setEnabled(count == 1)
        self.delete_btn.setEnabled(count > 0)
        if count != 1:
            self._render_detail(None, count)
            return

        entry = entries[0]
        try:
            db = self._ensure_db()
            detail = db.get_history_detail(
                entry['source_table'], int(entry['id'])) if db else None
        except Exception as exc:  # noqa: BLE001
            self._set_hint(f'读取详情失败：{exc}', warning=True)
            detail = None
        self._detail_entry = detail
        self._render_detail(detail, count)

    def _render_detail(self, detail: Optional[dict], count: int = 0):
        if detail is None:
            self.detail_title.setText('详情预览')
            if count > 1:
                self.detail_body.setPlainText(
                    f'已选中 {count} 条记录；详情预览仅支持单条。\n'
                    '可点击「删除」进行批量清理。')
            else:
                self.detail_body.setPlainText(
                    '选中一条记录后，这里显示输入参数与结论摘要。')
            return

        lines = [
            f"记录：{detail.get('pan_label') or '其它'} · #{detail.get('id')}",
            f"时间：{detail.get('created_at') or '—'}",
            f"姓名：{detail.get('name') or '—'}    性别：{detail.get('gender') or '—'}",
            f"出生：{detail.get('birth_date') or '—'} {detail.get('birth_time') or ''}"
            f"    出生地：{detail.get('city') or '—'}",
            '',
            '【输入参数】',
        ]
        payload = detail.get('payload') or {}
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                continue
            lines.append(f'  {key}：{value if value != "" else "—"}')
        if not payload:
            lines.append('  （该记录未保存原始输入）')

        lines.extend(['', '【结论摘要】', f'  {detail.get("title") or "—"}'])
        ai = detail.get('ai')
        lines.extend(['', '【AI 解读】', f'  {"已有解读：" + "、".join(ai.keys()) if ai else "暂无"}'])
        self.detail_title.setText(
            f"详情预览 · {detail.get('pan_label') or '其它'} #{detail.get('id')}")
        self.detail_body.setPlainText('\n'.join(lines))
        self.detail_toggle.setChecked(True)
        self.detail_body.setVisible(True)
        self.detail_toggle.setText('收起')

    def _on_toggle_detail(self, expanded: bool):
        self.detail_body.setVisible(expanded)
        self.detail_toggle.setText('收起' if expanded else '展开')

    # ==================== 筛选交互 ====================

    def _on_date_enabled(self, enabled: bool):
        self.date_from.setEnabled(enabled)
        self.date_to.setEnabled(enabled)
        self._request_page(1)

    def _on_date_changed(self, _date):
        if self.date_enabled.isChecked():
            self._request_page(1)

    # ==================== 操作 ====================

    def _on_load_clicked(self):
        entries = self.selected_entries()
        if len(entries) != 1:
            self._set_hint('请先选中一条记录再载入', warning=True)
            return
        entry = entries[0]
        if not entry.get('pan_kind'):
            self._set_hint('该记录板块无法识别，暂不支持载入', warning=True)
            return

        payload = {}
        try:
            db = self._ensure_db()
            detail = db.get_history_detail(
                entry['source_table'], int(entry['id'])) if db else None
            if detail is None:
                self._set_hint('记录不存在或已被删除，请刷新列表', warning=True)
                self.refresh()
                return
            payload = detail.get('payload') or {}
        except Exception as exc:  # noqa: BLE001
            self._set_hint(f'载入失败：{exc}', warning=True)
            return

        self.load_requested.emit(str(entry['pan_kind']), int(entry['id']), payload)
        self._set_hint(
            f"已发出载入请求：{entry.get('pan_kind')} #{entry.get('id')}")

    def _confirm_delete(self, count: int) -> bool:
        if self._confirm_callback is not None:
            return bool(self._confirm_callback(self, count))
        answer = QMessageBox.question(
            self, '删除历史记录',
            f'确认删除选中的 {count} 条历史记录？\n该操作不可撤销。',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return answer == QMessageBox.Yes

    def _on_delete_clicked(self):
        entries = self.selected_entries()
        if not entries:
            self._set_hint('请先选中要删除的记录', warning=True)
            return
        if not self._confirm_delete(len(entries)):
            return

        try:
            db = self._ensure_db()
            if db is None:
                raise RuntimeError('数据库未就绪，无法删除')
            deleted = db.delete_history_records(entries)
        except Exception as exc:  # noqa: BLE001
            self._set_hint(f'删除失败：{exc}', warning=True)
            return

        self.delete_requested.emit(entries)
        self._set_hint(f'已删除 {deleted} 条记录')
        self.refresh(reset_page=False)


__all__ = ['HistoryPanel', 'HistoryQueryThread']
