"""
历史记录面板
展示已保存的排盘记录（pan_records 表），支持按类型、姓名、日期范围筛选、
查看详情、载入到八字结果、删除记录。数据库未配置时优雅降级（提示而非崩溃）。
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QComboBox, QPushButton, QTextEdit, QMessageBox, QSizePolicy,
    QLineEdit, QDateEdit, QCheckBox,
)
from PySide6.QtCore import Signal, Qt, QDate
from ui.styles import Colors, Fonts, Spacing, Stylesheets


class HistoryFilterPanel(QWidget):
    """历史记录左侧筛选面板（类型 / 姓名 / 日期范围 / 五行·格局·强弱）"""
    # (pan_type, name, start, end, wuxing, geju_type, strength)  —— '' 表示不限制
    filter_changed = Signal(str, str, str, str, str, str, str)

    _MAP = {'全部': '', '八字四柱': '八字排盘', '梅花易数': '梅花易数'}
    _WUXING_OPTS = ['（不限）', '金', '木', '水', '火', '土']
    _GEJU_OPTS = ['（不限）', '专旺格', '从格', '扶抑格', '中和格']
    _STRENGTH_OPTS = ['（不限）', '身强', '身弱', '中和']

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        l = QVBoxLayout(self)
        l.setContentsMargins(16, 16, 16, 16)
        l.setSpacing(12)

        title = QLabel('历史记录')
        title.setStyleSheet(
            f"font-size:{Fonts.SZ_SECTION}; font-weight:{Fonts.W_BOLD}; "
            f"color:{Colors.TEXT}; font-family:{Fonts.TITLE};"
        )
        l.addWidget(title)

        hint = QLabel('按条件筛选已保存的排盘记录；在右侧列表中选择可查看详情、载入或删除。')
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};"
        )
        l.addWidget(hint)

        # 类型筛选
        row_type = QHBoxLayout()
        row_type.addWidget(QLabel('类型'))
        self.type_cb = QComboBox()
        self.type_cb.addItems(['全部', '八字四柱', '梅花易数'])
        self.type_cb.setCursor(Qt.PointingHandCursor)
        self.type_cb.setStyleSheet(
            f"padding:6px 10px; border:2px solid {Colors.LIUJIN}; "
            f"border-radius:{Spacing.RADIUS_SM}px; font-size:13px; background:white; "
            f"font-family:{Fonts.BODY};"
        )
        self.type_cb.currentTextChanged.connect(lambda _: self._emit())
        row_type.addWidget(self.type_cb, 1)
        l.addLayout(row_type)

        # 姓名搜索
        row_name = QHBoxLayout()
        row_name.addWidget(QLabel('姓名'))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('输入姓名关键字')
        self.name_edit.setClearButtonEnabled(True)
        self.name_edit.setStyleSheet(
            f"padding:6px 10px; border:2px solid {Colors.QINGHUA_LIGHT}; "
            f"border-radius:{Spacing.RADIUS_SM}px; font-size:13px; background:white; "
            f"font-family:{Fonts.BODY};"
        )
        self.name_edit.textChanged.connect(lambda _: self._emit())
        row_name.addWidget(self.name_edit, 1)
        l.addLayout(row_name)

        # 日期范围（可选）
        self.date_chk = QCheckBox('按保存日期筛选')
        self.date_chk.setCursor(Qt.PointingHandCursor)
        self.date_chk.stateChanged.connect(self._on_date_toggle)
        l.addWidget(self.date_chk)

        row_date = QHBoxLayout()
        row_date.setSpacing(8)
        row_date.addWidget(QLabel('起'))
        self.start_de = QDateEdit()
        self.start_de.setCalendarPopup(True)
        self.start_de.setDisplayFormat('yyyy-MM-dd')
        self.start_de.setDate(QDate.currentDate().addYears(-1))
        self.start_de.setEnabled(False)
        self._style_date(self.start_de)

        row_date.addWidget(self.start_de, 1)
        row_date.addWidget(QLabel('止'))
        self.end_de = QDateEdit()
        self.end_de.setCalendarPopup(True)
        self.end_de.setDisplayFormat('yyyy-MM-dd')
        self.end_de.setDate(QDate.currentDate())
        self.end_de.setEnabled(False)
        self._style_date(self.end_de)
        row_date.addWidget(self.end_de, 1)
        l.addLayout(row_date)

        # 高级筛选：五行属性 / 格局类型 / 日主强弱
        adv_label = QLabel('高级筛选（按命局特征）')
        adv_label.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; font-weight:{Fonts.W_MEDIUM}; "
            f"color:{Colors.QINGHUA}; font-family:{Fonts.BODY}; margin-top:6px;"
        )
        l.addWidget(adv_label)

        self.wuxing_cb = self._add_adv_row(l, '五行', self._WUXING_OPTS)
        self.geju_cb = self._add_adv_row(l, '格局', self._GEJU_OPTS)
        self.strength_cb = self._add_adv_row(l, '强弱', self._STRENGTH_OPTS)

        # 按钮
        btn_row = QHBoxLayout()
        self.search_btn = QPushButton('🔍 搜索')
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
        self.search_btn.clicked.connect(self._emit)

        self.reset_btn = QPushButton('✕ 重置')
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
        self.reset_btn.clicked.connect(self._on_reset)

        btn_row.addWidget(self.search_btn)
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch()
        l.addLayout(btn_row)

        self.refresh_btn = QPushButton('🔄 刷新全部')
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
        self.refresh_btn.clicked.connect(self._emit)
        l.addWidget(self.refresh_btn)

        l.addStretch()

        tip = QLabel('提示：记录保存在数据库（pan_records）。若未配置数据库，将提示连接失败。')
        tip.setWordWrap(True)
        tip.setStyleSheet(
            f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};"
        )
        l.addWidget(tip)

    def _style_date(self, de: QDateEdit):
        de.setStyleSheet(
            f"padding:5px 8px; border:2px solid {Colors.LIUJIN}; "
            f"border-radius:{Spacing.RADIUS_SM}px; font-size:13px; background:white; "
            f"font-family:{Fonts.BODY};"
        )

    def _add_adv_row(self, layout: QHBoxLayout, label: str, options: list) -> QComboBox:
        """新增一行高级筛选下拉框，返回该 QComboBox"""
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        cb = QComboBox()
        cb.addItems(options)
        cb.setCursor(Qt.PointingHandCursor)
        cb.setStyleSheet(
            f"padding:5px 8px; border:2px solid {Colors.QINGHUA_LIGHT}; "
            f"border-radius:{Spacing.RADIUS_SM}px; font-size:13px; background:white; "
            f"font-family:{Fonts.BODY};"
        )
        cb.currentTextChanged.connect(lambda _: self._emit())
        row.addWidget(cb, 1)
        layout.addLayout(row)
        return cb

    def _on_date_toggle(self, state):
        enabled = state == Qt.Checked
        self.start_de.setEnabled(enabled)
        self.end_de.setEnabled(enabled)
        self._emit()

    def _on_reset(self):
        self.type_cb.setCurrentText('全部')
        self.name_edit.clear()
        self.date_chk.setChecked(False)
        self.start_de.setDate(QDate.currentDate().addYears(-1))
        self.end_de.setDate(QDate.currentDate())
        self.wuxing_cb.setCurrentIndex(0)
        self.geju_cb.setCurrentIndex(0)
        self.strength_cb.setCurrentIndex(0)
        self._emit()

    def _emit(self):
        pan_type = self._MAP.get(self.type_cb.currentText(), '')
        name = self.name_edit.text().strip()
        if self.date_chk.isChecked():
            start = self.start_de.date().toString('yyyy-MM-dd')
            end = self.end_de.date().toString('yyyy-MM-dd')
            if start > end:  # 起止颠倒则交换
                start, end = end, start
        else:
            start = ''
            end = ''
        # 高级筛选：下拉第一项「（不限）」映射为空串
        wuxing = '' if self.wuxing_cb.currentIndex() == 0 else self.wuxing_cb.currentText()
        geju = '' if self.geju_cb.currentIndex() == 0 else self.geju_cb.currentText()
        strength = '' if self.strength_cb.currentIndex() == 0 else self.strength_cb.currentText()
        self.filter_changed.emit(pan_type, name, start, end, wuxing, geju, strength)

    def trigger_refresh(self):
        self._emit()


class HistoryListPanel(QWidget):
    """历史记录右侧列表 + 详情面板"""
    load_to_bazi = Signal(dict)   # 把选中的记录 dict 抛给主窗口载入

    def __init__(self, db_manager, user_id_getter, parent=None):
        super().__init__(parent)
        self.db = db_manager               # DatabaseManager 实例（可能为 None）
        self.uid_getter = user_id_getter  # callable -> int
        self._records = []
        self._build()

    def _build(self):
        l = QVBoxLayout(self)
        l.setContentsMargins(16, 16, 16, 16)
        l.setSpacing(12)

        # 工具栏
        bar = QHBoxLayout()
        self.status_lbl = QLabel('历史记录')
        self.status_lbl.setStyleSheet(
            f"font-size:{Fonts.SZ_BODY}; color:{Colors.TEXT2}; font-family:{Fonts.BODY};"
        )
        bar.addWidget(self.status_lbl)

        self.del_btn = QPushButton('🗑 删除选中')
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
        self.del_btn.clicked.connect(self._on_delete)

        self.load_btn = QPushButton('📥 载入到八字')
        self.load_btn.setCursor(Qt.PointingHandCursor)
        self.load_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
        self.load_btn.clicked.connect(self._on_load)

        bar.addStretch()
        bar.addWidget(self.del_btn)
        bar.addWidget(self.load_btn)
        l.addLayout(bar)

        # 列表
        self.list_w = QListWidget()
        self.list_w.setStyleSheet(f"""
            QListWidget {{
                background: {Colors.CARD};
                border: 1px solid {Colors.QINGHUA_LIGHT};
                border-radius: {Spacing.RADIUS}px;
                font-family: {Fonts.BODY};
                font-size: {Fonts.SZ_SMALL};
            }}
            QListWidget::item {{ padding: 8px 10px; border-bottom: 1px solid #EEE6D6; }}
            QListWidget::item:selected {{
                background: {Colors.QINGHUA_GLOW};
                color: {Colors.QINGHUA};
            }}
        """)
        self.list_w.currentItemChanged.connect(self._on_select)
        self.list_w.itemDoubleClicked.connect(self._on_load)
        l.addWidget(self.list_w, 1)

        # 详情
        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setFixedHeight(190)
        self.detail.setStyleSheet(f"""
            QTextEdit {{
                background: {Colors.CARD};
                border: 1px solid {Colors.QINGHUA_LIGHT};
                border-radius: {Spacing.RADIUS}px;
                font-family: {Fonts.MONO};
                font-size: {Fonts.SZ_SMALL};
                color: {Colors.TEXT};
                padding: 10px;
            }}
        """)
        self.detail.setPlainText('（暂无记录，或数据库未连接）')
        l.addWidget(self.detail)

    # ----------------- 数据加载 -----------------
    def load(self, pan_type: str = '', name: str = '', start: str = '', end: str = '',
             wuxing: str = '', geju_type: str = '', strength: str = ''):
        uid = self.uid_getter() or 1
        try:
            if self.db:
                recs = self.db.search_records(
                    uid, pan_type, name, start, end,
                    wuxing, geju_type, strength, 200)
            else:
                recs = []
        except Exception as e:
            self.status_lbl.setText(f'⚠ 数据库读取失败：{e}')
            self.status_lbl.setStyleSheet(
                f"font-size:{Fonts.SZ_SMALL}; color:{Colors.DANGER}; font-family:{Fonts.BODY};")
            self.list_w.clear()
            self.detail.setPlainText('（数据库未连接或读取失败，请检查 config.ini 的 [database] 段）')
            return

        self._records = recs or []

        # 构造筛选描述
        desc = []
        if pan_type:
            desc.append(f"类型={pan_type}")
        if name:
            desc.append(f"姓名≈'{name}'")
        if start or end:
            desc.append(f"日期 {start or '…'} ~ {end or '…'}")
        if wuxing:
            desc.append(f"五行~'{wuxing}'")
        if geju_type:
            desc.append(f"格局={geju_type}")
        if strength:
            desc.append(f"强弱={strength}")
        desc_txt = f"（{'; '.join(desc)}）" if desc else ''

        self.list_w.clear()
        if not self._records:
            self.status_lbl.setText(f'（无匹配记录）{desc_txt}')
            self.status_lbl.setStyleSheet(
                f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};")
            self.detail.setPlainText('（暂无匹配记录。排盘并保存后将出现在此处）')
            return

        self.status_lbl.setText(f'共 {len(self._records)} 条记录{desc_txt}')
        self.status_lbl.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT2}; font-family:{Fonts.BODY};")
        for r in self._records:
            label = f"{r.get('name','?')} · {r.get('pan_type','?')} · {str(r.get('created_at',''))[:19]}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, r['id'])
            self.list_w.addItem(item)
        self.list_w.setCurrentRow(0)

    # ----------------- 交互 -----------------
    def _on_select(self, cur, _prev):
        if not cur:
            return
        rid = cur.data(Qt.UserRole)
        rec = next((r for r in self._records if r['id'] == rid), None)
        if rec:
            self.detail.setPlainText(self._format(rec))

    def _on_delete(self):
        cur = self.list_w.currentItem()
        if not cur:
            QMessageBox.information(self, '提示', '请先选择一条记录')
            return
        rid = cur.data(Qt.UserRole)
        uid = self.uid_getter() or 1
        if self.db and self.db.delete_record(rid, uid):
            QMessageBox.information(self, '已删除', '记录已删除')
            self.load()
        else:
            QMessageBox.warning(self, '删除失败', '删除失败，请检查数据库连接')

    def _on_load(self):
        cur = self.list_w.currentItem()
        if not cur:
            return
        rid = cur.data(Qt.UserRole)
        rec = next((r for r in self._records if r['id'] == rid), None)
        if rec:
            self.load_to_bazi.emit(rec)

    # ----------------- 工具 -----------------
    @staticmethod
    def _format(rec: dict) -> str:
        lines = [
            f"姓名：{rec.get('name','-')}",
            f"性别：{rec.get('gender','-')}",
            f"类型：{rec.get('pan_type','-')}",
            f"出生：{rec.get('birth_date','-')} {rec.get('birth_time','-')}",
            f"出生地：{rec.get('city','-')}",
            f"保存时间：{rec.get('created_at','-')}",
        ]
        res = rec.get('result', {}) or {}
        bi = res.get('basic_info', {})
        if bi:
            lines.append('')
            lines.append('— 命盘概要 —')
            if bi.get('solar_date'):
                lines.append(f"公历：{bi.get('solar_date')}")
            if bi.get('lunar_date'):
                lines.append(f"农历：{bi.get('lunar_date')}")
            if bi.get('location'):
                lines.append(f"地点：{bi.get('location')}")
            bt = res.get('bazi_types', {}) or {}
            if bt.get('strength'):
                lines.append(f"日主强弱：{bt.get('strength')}")
            if bt.get('geju_type'):
                lines.append(f"格局类型：{bt.get('geju_type')}{('（'+bt.get('geju_name','')+'）') if bt.get('geju_name') else ''}")
            if bt.get('wuxing_summary'):
                lines.append(f"五行旺衰：{bt.get('wuxing_summary')}")
        return '\n'.join(lines)
