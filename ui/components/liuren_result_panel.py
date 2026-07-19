"""
大六壬起课结果展示面板
展示：基本信息 / 天地盘 / 四课 / 三传（门法）/ 十二天将 / 神煞 / AI 解读。
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QScrollArea, QPushButton, QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, Property
from PySide6.QtGui import QPainter, QColor
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from ui.components.collapsible_card import CollapsibleCard, ai_section_header

# 五行 → 颜色（本地 hex，避免引用未定义样式属性）
WX_COLOR = {
    '木': '#3a7d44', '火': '#c0392b', '土': '#b9770e',
    '金': '#7f8c8d', '水': '#2471a3',
}
# 地支五行
ZHI_WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火', '午': '火',
           '辰': '土', '戌': '土', '丑': '土', '未': '土', '申': '金', '酉': '金'}
ZHI_ORDER = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']


class RotatingLabel(QLabel):
    """支持 rotation 属性的 QLabel，用于在 paintEvent 中按角度旋转绘制。"""

    def __init__(self, text='☯', parent=None):
        super().__init__(text, parent)
        self._angle = 0.0
        self.setAlignment(Qt.AlignCenter)

    def getRotation(self):
        return self._angle

    def setRotation(self, value):
        self._angle = value
        self.update()

    rotation = Property(float, getRotation, setRotation)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)
        painter.translate(-self.width() / 2, -self.height() / 2)
        super().paintEvent(event)


class LiurenResultPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_result = {}
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.BACKGROUND};
            }}
        """)

        main_layout = QVBoxLayout()
        card_padding = int(Spacing.CARD_PADDING.replace('px', ''))
        main_layout.setContentsMargins(card_padding, card_padding, card_padding, card_padding)
        main_layout.setSpacing(16)

        # 头部
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        title_icon = QLabel('☵')
        title_icon.setStyleSheet("font-size: 22px;")
        self.title_label = QLabel('大六壬起课结果')
        self.title_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_TITLE};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_SERIF};
            letter-spacing: 2px;
        """)
        header_layout.addWidget(title_icon)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.ai_analyze_btn = QPushButton('🤖 重新解读')
        self.ai_analyze_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        self.ai_analyze_btn.setCursor(Qt.PointingHandCursor)
        self.ai_analyze_btn.setVisible(False)
        header_layout.addWidget(self.ai_analyze_btn)
        main_layout.addLayout(header_layout)

        # 状态栏
        self.status_bar = QFrame()
        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 12px 20px;
            }}
        """)
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(16, 10, 16, 10)
        status_layout.setAlignment(Qt.AlignCenter)
        self.status_label = QLabel('请完善左侧起课参数')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        status_layout.addWidget(self.status_label)
        main_layout.addWidget(self.status_bar)

        # 滚动区
        self.content_area = QScrollArea()
        self.content_area.setStyleSheet(Stylesheets.SCROLL_AREA)
        self.content_area.setWidgetResizable(True)
        self.content_area.setFrameShape(QFrame.NoFrame)

        self.content_widget = QWidget()
        self.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(18)

        self.empty_state = self._create_empty_state()
        self.content_layout.addWidget(self.empty_state)

        self.content_area.setWidget(self.content_widget)
        main_layout.addWidget(self.content_area)
        self.setLayout(main_layout)

    # ---------- 空状态 ----------
    def _create_empty_state(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        icon = QLabel('☵')
        icon.setStyleSheet(f"font-size: 64px; color: {Colors.BORDER}; opacity: 0.5;")
        icon.setAlignment(Qt.AlignCenter)
        title = QLabel('请完善左侧起课参数')
        title.setStyleSheet(f"""
            font-size: 18px; color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel('点击「起课」获取大六壬天地盘与三传分析')
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN}; opacity: 0.7;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return widget

    # ---------- 通用卡片（统一复用 CollapsibleCard） ----------
    def _create_result_card(self, title, icon, content_widget, highlight=False):
        """创建结果卡片（统一复用 CollapsibleCard：左侧强调色条 + 图标 + 标题，可折叠）。

        配色：排盘类卡片用青色条(Colors.QINGHUA)，AI/强调类用鎏金色条(Colors.LIUJIN)，
        与八字、梅花易数面板保持一致。
        """
        accent = Colors.LIUJIN if highlight else Colors.QINGHUA
        card = CollapsibleCard(title, icon, accent_color=accent, collapsed=False)
        card.set_content(content_widget)
        return card

    @staticmethod
    def _wx_chip(text, wx):
        chip = QLabel(text)
        color = WX_COLOR.get(wx, Colors.TEXT_SECONDARY)
        chip.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SMALL}; font-family: {Fonts.FAMILY_CN};
            color: #ffffff; background-color: {color};
            border-radius: 4px; padding: 2px 8px;
        """)
        chip.setAlignment(Qt.AlignCenter)
        return chip

    # ---------- 基本信息 ----------
    def _basic_info_card(self, r):
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        rows = [
            ('起课方式', r.get('method_name', '')),
            ('占问', r.get('question') or '—'),
            ('时间', r.get('time', '')),
            ('日干支', f"{r.get('ri_gan','')}{r.get('ri_zhi','')}（{r.get('ri_gan_wx','')}）"),
            ('月将', f"{r.get('yue_jiang_name','')}（{r.get('yue_jiang','')}）"),
            ('占时', r.get('zhan_shi', '')),
        ]
        for i, (k, v) in enumerate(rows):
            kl = QLabel(k)
            kl.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; font-family: {Fonts.FAMILY_CN};")
            kl.setFixedWidth(76)
            kl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            vl = QLabel(str(v))
            vl.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY}; font-family: {Fonts.FAMILY_CN};")
            vl.setWordWrap(True)
            grid.addWidget(kl, i, 0)
            grid.addWidget(vl, i, 1)
        w = QWidget(); w.setLayout(grid)
        return w

    # ---------- 天地盘 ----------
    def _tiandi_card(self, r):
        tian_pan = r.get('tian_pan', {})
        tian_jiang = {t['pos']: t['jiang'] for t in r.get('tian_jiang', [])}
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        # 表头：地盘12宫
        for c, dz in enumerate(ZHI_ORDER):
            h = QLabel(dz)
            h.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; font-family: {Fonts.FAMILY_CN}; font-weight: {Fonts.WEIGHT_BOLD};")
            h.setAlignment(Qt.AlignCenter)
            grid.addWidget(h, 0, c)
        # 天盘支
        for c, dz in enumerate(ZHI_ORDER):
            tp = tian_pan.get(dz, dz)
            cell = QLabel(tp)
            cell.setStyleSheet(f"font-size: 16px; color: {Colors.ACCENT}; font-family: {Fonts.FAMILY_SERIF}; font-weight: {Fonts.WEIGHT_BOLD};")
            cell.setAlignment(Qt.AlignCenter)
            cell.setFixedHeight(28)
            grid.addWidget(cell, 1, c)
        # 天将
        for c, dz in enumerate(ZHI_ORDER):
            jiang = tian_jiang.get(dz, '')
            cell = QLabel(jiang)
            cell.setStyleSheet(f"font-size: {Fonts.SIZE_MICRO}; color: {Colors.TEXT_SECONDARY}; font-family: {Fonts.FAMILY_CN};")
            cell.setAlignment(Qt.AlignCenter)
            cell.setFixedHeight(20)
            grid.addWidget(cell, 2, c)
        w = QWidget(); w.setLayout(grid)
        return w

    # ---------- 四课 ----------
    def _sike_card(self, r):
        si_ke = r.get('si_ke', {})
        order = [('干上（第一课）', 'gan_shang'), ('干阴（第二课）', 'gan_yin'),
                  ('支上（第三课）', 'zhi_shang'), ('支阴（第四课）', 'zhi_yin')]
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)
        grid.setColumnStretch(1, 1)
        for i, (label, key) in enumerate(order):
            v = si_ke.get(key, {})
            kl = QLabel(label)
            kl.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; font-family: {Fonts.FAMILY_CN};")
            kl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            kl.setFixedWidth(110)
            formula = QLabel(f"{v.get('dizhi','')} → {v.get('tianpan','')}")
            formula.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY}; font-family: {Fonts.FAMILY_CN};")
            formula.setAlignment(Qt.AlignCenter)
            grid.addWidget(kl, i, 0)
            grid.addWidget(formula, i, 1)
            chip = self._wx_chip(v.get('wx', ''), v.get('wx', ''))
            grid.addWidget(chip, i, 2)
        w = QWidget(); w.setLayout(grid)
        return w

    # ---------- 三传 ----------
    def _sanchuan_card(self, r):
        sc = r.get('san_chuan', {})
        gate = sc.get('gate', '')
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)
        items = [('初传', sc.get('chu', '')), ('中传', sc.get('zhong', '')), ('末传', sc.get('mo', ''))]
        for c, (label, val) in enumerate(items):
            col = QVBoxLayout()
            col.setSpacing(4)
            lab = QLabel(label)
            lab.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; font-family: {Fonts.FAMILY_CN};")
            lab.setAlignment(Qt.AlignCenter)
            val_lab = QLabel(val)
            val_lab.setStyleSheet(f"""
                font-size: 22px; color: {Colors.ACCENT}; font-family: {Fonts.FAMILY_SERIF};
                font-weight: {Fonts.WEIGHT_BOLD};
            """)
            val_lab.setAlignment(Qt.AlignCenter)
            col.addWidget(lab)
            col.addWidget(val_lab)
            grid.addLayout(col, 0, c)
        # 门法说明
        gate_lab = QLabel(f"取用法：{gate}")
        gate_lab.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_SECONDARY}; font-family: {Fonts.FAMILY_CN};")
        gate_lab.setAlignment(Qt.AlignCenter)
        grid.addWidget(gate_lab, 1, 0, 1, 3)
        w = QWidget(); w.setLayout(grid)
        return w

    # ---------- 十二天将 ----------
    def _tianjiang_card(self, r):
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        for i, t in enumerate(r.get('tian_jiang', [])):
            row = i // 3
            col = i % 3
            cell = QLabel(f"{t['pos']}　{t['tianpan']}　{t['jiang']}")
            cell.setStyleSheet(f"""
                font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_PRIMARY};
                font-family: {Fonts.FAMILY_CN}; background: {Colors.QINGHUA_LIGHT};
                border-radius: 4px; padding: 6px 8px;
            """)
            cell.setAlignment(Qt.AlignCenter)
            layout.addWidget(cell, row, col)
        w = QWidget(); w.setLayout(layout)
        return w

    # ---------- 神煞 ----------
    def _shensha_card(self, r):
        sha = r.get('shen_sha', {})
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        if not sha:
            layout.addWidget(self._muted('本课无明显神煞'))
        else:
            for k, v in sha.items():
                row = QHBoxLayout()
                kl = QLabel(k)
                kl.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; font-family: {Fonts.FAMILY_CN};")
                kl.setFixedWidth(60)
                vl = QLabel(str(v))
                vl.setStyleSheet(f"font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_PRIMARY}; font-family: {Fonts.FAMILY_CN};")
                vl.setWordWrap(True)
                row.addWidget(kl); row.addWidget(vl, 1)
                layout.addLayout(row)
        w = QWidget(); w.setLayout(layout)
        return w

    @staticmethod
    def _muted(text):
        l = QLabel(text)
        l.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}; color: {Colors.TEXT_TERTIARY}; font-family: {Fonts.FAMILY_CN};")
        return l

    @staticmethod
    def _safe_set_visible(widget, visible: bool):
        """安全切换可见性：防御 C++ 对象已被销毁（deleteLater 后）的悬空引用。"""
        if widget is None:
            return
        try:
            widget.setVisible(visible)
        except RuntimeError:
            # 底层 C++ 对象已被销毁，忽略
            pass

    # ---------- AI 解读占位 ----------
    def _ai_placeholder(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._muted('AI 智能解读将在起课后自动生成，或点击右上角「重新解读」。'))
        return w

    # ---------- 对外入口 ----------
    def show_loading(self):
        """显示加载状态"""
        self.status_label.setText('⏳ 正在起课分析，请稍候')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        self.title_label.setText('大六壬起课结果')
        self._safe_set_visible(self.empty_state, False)
        self.ai_analyze_btn.setVisible(False)
        # 加载动画
        self.taiji = RotatingLabel('☯')
        self.taiji.setStyleSheet(f"font-size: 80px; color: {Colors.PRIMARY};")
        self.taiji.setFixedSize(120, 120)
        self.taiji_animation = QPropertyAnimation(self.taiji, b"rotation")
        self.taiji_animation.setDuration(3000)
        self.taiji_animation.setStartValue(0)
        self.taiji_animation.setEndValue(360)
        self.taiji_animation.setEasingCurve(QEasingCurve.Linear)
        self.taiji_animation.setLoopCount(-1)
        self.taiji_animation.start()
        self.content_layout.addWidget(self.taiji)

    def show_ai_loading(self, text='AI 正在解读六壬玄机…'):
        self.status_label.setText('⏳ ' + text)
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
        """)

    def display_result(self, result_data):
        try:
            # 清理旧内容（含加载动画）
            if hasattr(self, 'taiji_animation'):
                self.taiji_animation.stop()
            # 清理动态内容；empty_state 是持久控件，绝不可 deleteLater，否则后续 setVisible 会命中已销毁的 C++ 对象
            while self.content_layout.count():
                item = self.content_layout.takeAt(0)
                w = item.widget()
                if w and w is not self.empty_state:
                    w.deleteLater()
            self._current_result = result_data
            self._safe_set_visible(self.empty_state, False)

            self.status_label.setText('✓ 起课完成，天地盘已生成')
            self.status_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY}; color: {Colors.SUCCESS};
                font-family: {Fonts.FAMILY_CN}; font-weight: {Fonts.WEIGHT_BOLD};
            """)

            self.content_layout.addWidget(
                self._create_result_card('基本信息', '📋', self._basic_info_card(result_data)))
            self.content_layout.addWidget(
                self._create_result_card('天地盘', '🌐', self._tiandi_card(result_data)))
            self.content_layout.addWidget(
                self._create_result_card('四课', '📜', self._sike_card(result_data)))
            self.content_layout.addWidget(
                self._create_result_card('三传', '⚡', self._sanchuan_card(result_data), highlight=True))
            self.content_layout.addWidget(
                self._create_result_card('十二天将', '🐉', self._tianjiang_card(result_data)))
            self.content_layout.addWidget(
                self._create_result_card('神煞', '✨', self._shensha_card(result_data)))
            # AI 占位
            self.content_layout.addWidget(
                self._create_result_card('AI 智能解读', '🤖', self._ai_placeholder(), highlight=True))

            self.ai_analyze_btn.setVisible(True)
            self.ai_analyze_btn.setEnabled(True)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def display_ai_analysis_result(self, ai_analysis):
        """将 AI 结构化解读渲染到「AI 智能解读」卡片。"""
        try:
            if not ai_analysis:
                self.status_label.setText('⚠ AI 解读为空')
                return
            # 用 AI 内容替换最后一个 AI 卡片
            if hasattr(self, 'taiji_animation'):
                self.taiji_animation.stop()
            # 移除 AI 占位卡片（最后一个），重建为解读内容
            if self.content_layout.count():
                last = self.content_layout.itemAt(self.content_layout.count() - 1)
                w = last.widget()
                if w:
                    w.deleteLater()
                    self.content_layout.removeWidget(w)

            # 构建 AI 结果容器：金色分隔标题 + 各子项折叠卡片（与八字/梅花面板一致）
            cards = self._ai_body(ai_analysis)
            container = QWidget()
            cv = QVBoxLayout(container)
            cv.setContentsMargins(0, 0, 0, 0)
            cv.setSpacing(12)
            cv.addWidget(ai_section_header('AI 智能深度解读'))
            for c in cards:
                cv.addWidget(c)
            self.content_layout.addWidget(container)
            self.status_label.setText('✓ AI 解读完成')
            self.status_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY}; color: {Colors.SUCCESS};
                font-family: {Fonts.FAMILY_CN}; font-weight: {Fonts.WEIGHT_BOLD};
            """)
            self.ai_analyze_btn.setVisible(True)
            self.ai_analyze_btn.setEnabled(True)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _ai_body(self, ai):
        """返回 AI 各子项的折叠卡片列表（与八字/梅花面板一致）。"""
        cards = []
        sections = [
            ('课体总览', '📜', Colors.QINGHUA, ai.get('ke_overview')),
            ('四课精解', '📖', Colors.LIUJIN, ai.get('si_ke_analysis')),
            ('三传推演', '⚡', Colors.ZHUSHA, ai.get('san_chuan_analysis')),
            ('天将神煞', '🐉', Colors.SUCCESS, ai.get('tian_jiang_analysis')),
            ('综合建议', '✨', Colors.QINGHUA, ai.get('final_verdict')),
        ]
        for title, icon, color, text in sections:
            if not text:
                continue
            # AI 返回的字段可能是字符串数组（如四课/三传精解），统一 join 成字符串
            if isinstance(text, list):
                text = '\n'.join(str(t) for t in text)
            body = QLabel(text)
            body.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_SECONDARY};
                font-family: {Fonts.FAMILY_CN}; line-height: 1.7;
            """)
            body.setWordWrap(True)
            card = CollapsibleCard(title, icon, accent_color=color, collapsed=False)
            card.set_content(body)
            cards.append(card)
        return cards

    def clear(self):
        if hasattr(self, 'taiji_animation'):
            self.taiji_animation.stop()
        # 清理动态内容；empty_state 持久控件不可删除
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w and w is not self.empty_state:
                w.deleteLater()
        # 仅当 empty_state 不在布局中时才挂载（避免重复 addWidget）
        if self.content_layout.indexOf(self.empty_state) == -1:
            self.content_layout.addWidget(self.empty_state)
        self._safe_set_visible(self.empty_state, True)
        self.ai_analyze_btn.setVisible(False)
        self.status_label.setText('请完善左侧起课参数')
        self.status_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY}; color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        self._current_result = {}

    def get_liuren_data_for_ai(self):
        """供 AI 管道消费的结构化取数。"""
        r = getattr(self, '_current_result', {}) or {}
        if not r:
            return {}
        si_ke = r.get('si_ke', {})
        sc = r.get('san_chuan', {})
        return {
            'method_name': r.get('method_name', ''),
            'question': r.get('question', ''),
            'time': r.get('time', ''),
            'ri_gan': r.get('ri_gan', ''),
            'ri_zhi': r.get('ri_zhi', ''),
            'ri_gan_wx': r.get('ri_gan_wx', ''),
            'yue_jiang': r.get('yue_jiang_name', '') + '（' + r.get('yue_jiang', '') + '）',
            'zhan_shi': r.get('zhan_shi', ''),
            'tian_pan': r.get('tian_pan', {}),
            'si_ke': {
                'gan_shang': si_ke.get('gan_shang', {}).get('tianpan', ''),
                'gan_yin': si_ke.get('gan_yin', {}).get('tianpan', ''),
                'zhi_shang': si_ke.get('zhi_shang', {}).get('tianpan', ''),
                'zhi_yin': si_ke.get('zhi_yin', {}).get('tianpan', ''),
            },
            'san_chuan': {
                'chu': sc.get('chu', ''),
                'zhong': sc.get('zhong', ''),
                'mo': sc.get('mo', ''),
                'gate': sc.get('gate', ''),
            },
            'tian_jiang': [f"{t['pos']}{t['tianpan']}{t['jiang']}" for t in r.get('tian_jiang', [])],
            'shen_sha': r.get('shen_sha', {}),
        }
