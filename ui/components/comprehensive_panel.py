"""
综合建议面板 v1.0 - 融合「八字排盘 + 梅花易数 + 大六壬」三方结论，由龙虎山大师兄生成统筹建议。
左侧 ComprehensiveInputPanel（状态 + 生成按钮），右侧 ComprehensiveResultPanel（融合建议展示）。
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QPushButton, QScrollArea, QSizePolicy, QProgressBar)
from PySide6.QtCore import Qt, Signal
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from ui.components.collapsible_card import CollapsibleCard


class ComprehensiveInputPanel(QWidget):
    """左侧控制面板：展示三方就绪状态，提供『生成综合建议』入口。"""

    generate_clicked = Signal()

    METHODS = [
        ('bazi', '八字排盘'),
        ('meihua', '梅花易数'),
        ('liuren', '大六壬'),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = {m: False for m, _ in self.METHODS}
        self._pills = {}
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(18)

        # 标题
        hdr = QHBoxLayout()
        icon = QLabel('☰')
        icon.setStyleSheet(f"font-size: 20px; color: {Colors.LIUJIN};")
        title = QLabel('综合建议')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT}; font-family: {Fonts.TITLE}; letter-spacing: 1px;
        """)
        hdr.addWidget(icon)
        hdr.addWidget(title)
        hdr.addStretch()
        root.addLayout(hdr)

        desc = QLabel(
            '龙虎山大师兄将汇总你在【八字排盘】【梅花易数】【大六壬】三处的分析结论，'
            '做矛盾校验与印证，给出一份统筹、精准、可落地的综合建议。\n\n'
            '请先分别完成这三处的「龙虎山大师兄分析」，再点击下方按钮生成综合建议。'
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2};
            font-family: {Fonts.BODY}; line-height: 1.7;
            background: {Colors.CARD}; border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS}; padding: 14px 16px;
        """)
        root.addWidget(desc)

        # 三方状态
        status_card = QFrame()
        status_card.setStyleSheet(f"""
            background: {Colors.CARD}; border: 1px solid {Colors.BORDER};
            border-radius: {Spacing.RADIUS}; padding: 6px 4px;
        """)
        sl = QVBoxLayout(status_card)
        sl.setContentsMargins(16, 14, 16, 14)
        sl.setSpacing(12)

        slabel = QLabel('三方分析就绪状态')
        slabel.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
        sl.addWidget(slabel)

        for method, name in self.METHODS:
            row = QHBoxLayout()
            row.setSpacing(10)
            dot = QLabel('●')
            dot.setStyleSheet(f"color: {Colors.TEXT3}; font-size: 10px;")
            row.addWidget(dot)
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; font-family: {Fonts.BODY};")
            row.addWidget(name_lbl)
            row.addStretch()
            pill = QLabel('待分析')
            pill.setStyleSheet(f"""
                font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3};
                background: {Colors.HOVER}; border-radius: {Spacing.RADIUS_SM};
                padding: 3px 10px; font-family: {Fonts.BODY};
            """)
            row.addWidget(pill)
            self._pills[method] = (dot, pill)
            sl.addLayout(row)

        root.addWidget(status_card)

        # 生成按钮
        self.gen_btn = QPushButton('🔮 生成综合建议')
        self.gen_btn.setCursor(Qt.PointingHandCursor)
        self.gen_btn.setFixedHeight(44)
        self.gen_btn.setStyleSheet(Stylesheets.BTN_PRIMARY)
        self.gen_btn.clicked.connect(lambda: self.generate_clicked.emit())
        root.addWidget(self.gen_btn)

        hint = QLabel('提示：三处分析结论越完整，综合建议越精准。')
        hint.setWordWrap(True)
        hint.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
        root.addWidget(hint)

        root.addStretch()

    # ----------------- 对外接口 -----------------
    def update_status(self, method: str, ready: bool):
        if method not in self._pills:
            return
        self._status[method] = ready
        dot, pill = self._pills[method]
        if ready:
            dot.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 10px;")
            pill.setText('✓ 已就绪')
            pill.setStyleSheet(f"""
                font-size: {Fonts.SZ_SMALL}; color: {Colors.SUCCESS};
                background: {Colors.HOVER};
                border-radius: {Spacing.RADIUS_SM}; padding: 3px 10px; font-family: {Fonts.BODY};
            """)
        else:
            dot.setStyleSheet(f"color: {Colors.TEXT3}; font-size: 10px;")
            pill.setText('待分析')
            pill.setStyleSheet(f"""
                font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3};
                background: {Colors.HOVER}; border-radius: {Spacing.RADIUS_SM};
                padding: 3px 10px; font-family: {Fonts.BODY};
            """)
        all_ready = all(self._status.values())
        self.gen_btn.setEnabled(all_ready)
        self.gen_btn.setText('🔮 生成综合建议' if all_ready else '🔮 请先完成三方分析')

    def refresh_status(self, status_dict: dict):
        for m, ready in status_dict.items():
            self.update_status(m, bool(ready))

    def set_busy(self, busy: bool):
        self.gen_btn.setEnabled(not busy)
        self.gen_btn.setText('⏳ 综合建议生成中…' if busy else '🔮 生成综合建议')


class ComprehensiveResultPanel(QWidget):
    """右侧结果面板：展示融合后的综合建议。"""

    SECTIONS = [
        ('tri_method_overview', '三方概览', '🧭', Colors.QINGHUA),
        ('consistency_check', '矛盾与印证', '⚖', Colors.ZHUSHA),
        ('synthesis', '综合定论', '🏛', Colors.LIUJIN),
        ('unified_plan', '统一趋吉避凶方案', '🌟', Colors.QINGHUA),
        ('key_timing', '关键时机与禁忌', '⏳', Colors.LIUJIN),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_zonghe = None  # 最近一次综合建议 AI 结论，供导出
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG};")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setStyleSheet(Stylesheets.SCROLL)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.content = QWidget()
        self.content.setStyleSheet(f"background-color: {Colors.BG};")
        self.content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.clay = QVBoxLayout(self.content)
        self.clay.setContentsMargins(24, 20, 24, 20)
        self.clay.setSpacing(16)

        self.clay.addLayout(self._header())
        self.scroll.setWidget(self.content)
        main.addWidget(self.scroll, 1)

    def _header(self):
        hdr = QHBoxLayout()
        hdr.setSpacing(8)
        icon = QLabel('🧙')
        icon.setStyleSheet(f"font-size: 18px; color: {Colors.LIUJIN};")
        title = QLabel('龙虎山大师兄 · 综合建议')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT}; font-family: {Fonts.TITLE};
        """)
        hdr.addWidget(icon)
        hdr.addWidget(title)
        hdr.addStretch()
        # 导出按钮：有综合建议结论时显示
        self.export_btn = QPushButton('📤 导出')
        self.export_btn.setStyleSheet(f"""
            background: {Colors.LIUJIN}; color: white; border: none;
            border-radius: 6px; padding: 6px 14px; font-size: {Fonts.SZ_SMALL};
            font-family: {Fonts.BODY}; font-weight: {Fonts.W_MEDIUM};
        """)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.clicked.connect(self._on_export_click)
        self.export_btn.setVisible(bool(self._current_zonghe))
        hdr.addWidget(self.export_btn)
        if not hasattr(self, 'status_lbl') or self.status_lbl is None:
            self.status_lbl = QLabel('')
            self.status_lbl.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
        hdr.addWidget(self.status_lbl)
        return hdr

    # ----------------- 内容渲染 -----------------
    def _clear_content(self):
        while self.clay.count():
            item = self.clay.takeAt(0)
            w = item.widget() if item else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                lay = item.layout() if item else None
                if lay is not None:
                    while lay.count():
                        ci = lay.takeAt(0)
                        cw = ci.widget() if ci else None
                        if cw is not None:
                            cw.setParent(None)
                            cw.deleteLater()
                    self.clay.removeItem(lay)

    def show_loading(self, msg: str):
        self._clear_content()
        self._current_zonghe = None
        self.clay.addLayout(self._header())
        self.status_lbl.setText('生成中')
        self.status_lbl.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.LIUJIN}; font-family: {Fonts.BODY};")
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(20, 60, 20, 20)
        wl.setSpacing(18)
        bar = QProgressBar()
        bar.setRange(0, 0)
        bar.setFixedHeight(6)
        bar.setStyleSheet(f"""
            QProgressBar {{ background: {Colors.HOVER}; border: none; border-radius: 3px; }}
            QProgressBar::chunk {{ background: {Colors.QINGHUA}; border-radius: 3px; }}
        """)
        tip = QLabel(msg)
        tip.setWordWrap(True)
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2}; font-family: {Fonts.BODY};")
        wl.addWidget(bar)
        wl.addWidget(tip)
        wl.addStretch()
        self.clay.addWidget(wrap)
        self.clay.addStretch()

    def show_error(self, msg: str):
        self._clear_content()
        self._current_zonghe = None
        self.clay.addLayout(self._header())
        self.status_lbl.setText('异常')
        self.status_lbl.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.DANGER}; font-family: {Fonts.BODY};")
        tip = QLabel(f'⚠ {msg}')
        tip.setWordWrap(True)
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet(f"color:{Colors.TEXT2}; font-size:{Fonts.SZ_BODY}; font-family:{Fonts.BODY}; padding:60px 20px;")
        self.clay.addWidget(tip)
        self.clay.addStretch()

    def display_result(self, ai_analysis: dict):
        self._clear_content()
        self._current_zonghe = ai_analysis or {}
        self.clay.addLayout(self._header())
        self.status_lbl.setText('已完成')
        self.status_lbl.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.SUCCESS}; font-family: {Fonts.BODY};")
        self._render_sections(ai_analysis or {})
        self.clay.addStretch()

    def _render_sections(self, ai_data: dict):
        # 分隔线 + 大标题
        divider = QFrame()
        divider.setFixedHeight(2)
        divider.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 transparent, stop:0.5 {Colors.LIUJIN}, stop:1 transparent); "
            f"margin: 6px 0 10px 0; border: none;"
        )
        self.clay.addWidget(divider)

        title_widget = QWidget()
        title_widget.setStyleSheet("background: transparent;")
        tl = QHBoxLayout(title_widget)
        tl.setContentsMargins(0, 0, 0, 4)
        tl.setSpacing(8)
        icon = QLabel('🧙')
        icon.setStyleSheet(f"font-size: 18px; color: {Colors.LIUJIN};")
        t = QLabel('龙虎山大师兄智能综合研判')
        t.setStyleSheet(f"font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD}; color: {Colors.LIUJIN}; font-family: {Fonts.TITLE};")
        tl.addWidget(icon)
        tl.addWidget(t)
        tl.addStretch()
        self.clay.addWidget(title_widget)

        has_content = False
        for key, title, icon, color in self.SECTIONS:
            val = ai_data.get(key)
            if not val:
                continue
            has_content = True
            card = CollapsibleCard(f'龙虎山大师兄·{title}', icon, accent_color=color, collapsed=False)
            if isinstance(val, list):
                card.set_content(self._ai_list(val, color))
            else:
                card.set_content(self._text_block(str(val), color))
            self.clay.addWidget(card)

        disclaimer = ai_data.get('disclaimer')
        if disclaimer:
            has_content = True
            card = CollapsibleCard('龙虎山大师兄·免责说明', '📜', accent_color=Colors.TEXT2, collapsed=True)
            card.set_content(self._text_block(str(disclaimer), Colors.TEXT2))
            self.clay.addWidget(card)

        if not has_content:
            empty = QLabel('龙虎山大师兄未返回有效条目，请点击「生成综合建议」重试')
            empty.setStyleSheet(f"color:{Colors.TEXT3}; font-size:{Fonts.SZ_BODY}; font-family:{Fonts.BODY}; padding:24px;")
            empty.setAlignment(Qt.AlignCenter)
            self.clay.addWidget(empty)

    def _ai_list(self, items: list, color: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(10)
        for idx, item in enumerate(items):
            row = QHBoxLayout()
            row.setSpacing(10)
            num = QLabel(f'{idx + 1}')
            num.setStyleSheet(f"""
                background: {color}; color: white;
                font-size: 11px; font-weight: {Fonts.W_MEDIUM};
                border-radius: 10px; min-width: 20px; min-height: 20px;
                font-family: {Fonts.BODY};
            """)
            num.setAlignment(Qt.AlignCenter)
            num.setFixedSize(20, 20)
            txt = QLabel(str(item))
            txt.setStyleSheet(f"""
                font-size:{Fonts.SZ_BODY}; color:{Colors.TEXT};
                font-family:{Fonts.BODY}; line-height: 1.7; padding: 2px 0;
            """)
            txt.setWordWrap(True)
            row.addWidget(num)
            row.addWidget(txt, 1)
            l.addLayout(row)
        return w

    def _text_block(self, text: str, color: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(6)
        txt = QLabel(text)
        txt.setWordWrap(True)
        txt.setStyleSheet(f"""
            font-size:{Fonts.SZ_BODY}; color:{Colors.TEXT};
            font-family:{Fonts.BODY}; line-height: 1.8;
        """)
        l.addWidget(txt)
        return w

    # ----------------- 导出 -----------------
    def _on_export_click(self):
        """导出综合建议为 CSV / Excel / PDF（复用导出对话框与三导出器）。"""
        from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox
        from ui.components.export_dialog import ExportDialog
        from ui.export import CsvExporter, ExcelExporter
        from ui.export.base_exporter import filter_export_data

        z = getattr(self, '_current_zonghe', None)
        if not z:
            QMessageBox.warning(self, '导出失败', '暂无可导出的综合建议')
            return

        export_data = {
            'zonghe': z,
            'basic_info': {'pan_type': '综合建议'},
        }
        dialog = ExportDialog(export_data, parent=self)
        dialog.filename_edit.setText('综合建议')
        if dialog.exec() == QDialog.DialogCode.Accepted:
            format_type = dialog.get_selected_format()
            chapters = dialog.get_selected_chapters()
            export_data = filter_export_data(export_data, chapters)

            filename = dialog.filename_edit.text().strip() or '综合建议'
            if format_type == 'csv':
                ext, file_filter = '.csv', 'CSV Files (*.csv)'
            elif format_type == 'excel':
                ext, file_filter = '.xlsx', 'Excel Files (*.xlsx)'
            else:
                ext, file_filter = '.pdf', 'PDF Files (*.pdf)'

            file_path, _ = QFileDialog.getSaveFileName(
                self, '导出综合建议', filename + ext, file_filter)
            if not file_path:
                return
            try:
                if format_type == 'csv':
                    exporter = CsvExporter()
                elif format_type == 'excel':
                    exporter = ExcelExporter()
                else:
                    try:
                        from ui.export import PdfExporter
                    except Exception:
                        QMessageBox.warning(
                            self, '导出失败',
                            '未安装 reportlab，无法导出 PDF。\n请执行：pip install reportlab')
                        return
                    exporter = PdfExporter()

                if exporter.export(export_data, file_path):
                    QMessageBox.information(self, '导出成功', f'文件已保存至：\n{file_path}')
                else:
                    QMessageBox.warning(self, '导出失败', '导出过程中发生错误')
            except Exception as e:
                QMessageBox.warning(self, '导出失败', f'导出失败：{e}')
