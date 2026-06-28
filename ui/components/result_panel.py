"""
右侧结果面板 v5.0 - 精美国风 · 可折叠卡片 · 清晰排版 · 流畅动画
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
                             QPushButton, QScrollArea, QProgressBar, QGraphicsOpacityEffect,
                             QToolButton)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QTimer
from PySide6.QtGui import QColor
from ui.styles import Stylesheets, Colors, Fonts, Spacing

# 天干五行颜色映射
TIANGAN_WUXING = {
    '甲': ('木', Colors.WOOD), '乙': ('木', Colors.WOOD),
    '丙': ('火', Colors.FIRE), '丁': ('火', Colors.FIRE),
    '戊': ('土', Colors.EARTH), '己': ('土', Colors.EARTH),
    '庚': ('金', Colors.METAL), '辛': ('金', Colors.METAL),
    '壬': ('水', Colors.WATER), '癸': ('水', Colors.WATER),
}

# 地支五行颜色映射
DIZHI_WUXING = {
    '寅': ('木', Colors.WOOD), '卯': ('木', Colors.WOOD),
    '巳': ('火', Colors.FIRE), '午': ('火', Colors.FIRE),
    '辰': ('土', Colors.EARTH), '戌': ('土', Colors.EARTH), '丑': ('土', Colors.EARTH), '未': ('土', Colors.EARTH),
    '申': ('金', Colors.METAL), '酉': ('金', Colors.METAL),
    '子': ('水', Colors.WATER), '亥': ('水', Colors.WATER),
}


class CollapsibleCard(QFrame):
    """可折叠卡片组件 - 点击标题栏展开/折叠内容区"""

    def __init__(self, title: str, icon: str, parent=None, accent_color=None, collapsed: bool = False):
        super().__init__(parent)
        self._collapsed = collapsed
        self._accent_color = accent_color or Colors.QINGHUA
        self._content_widget = None

        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS};
            }}
            QFrame:hover {{
                border-color: {self._accent_color};
            }}
        """)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # 标题栏（可点击）
        self._header = QFrame()
        self._header.setCursor(Qt.PointingHandCursor)
        self._header.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: none;
                border-radius: {Spacing.RADIUS};
                padding: 0;
            }}
            QFrame:hover {{
                background: {Colors.CARD_HOVER};
            }}
        """)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(10)

        # 折叠/展开图标
        self._collapse_icon = QLabel('▼' if not collapsed else '▶')
        self._collapse_icon.setStyleSheet(f"""
            font-size: 10px;
            color: {Colors.TEXT3};
            min-width: 12px;
        """)
        self._collapse_icon.setAlignment(Qt.AlignCenter)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 16px;")
        icon_label.setFixedWidth(24)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT};
            font-family: {Fonts.BODY};
        """)

        header_layout.addWidget(self._collapse_icon)
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self._main_layout.addWidget(self._header)

        # 内容容器
        self._content_container = QWidget()
        self._content_container.setStyleSheet("background: transparent; border: none;")
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(16, 0, 16, 14)
        self._content_layout.setSpacing(0)
        self._main_layout.addWidget(self._content_container)

        # 标题栏点击事件
        self._header.mousePressEvent = self._on_header_click

        if collapsed:
            self._content_container.setVisible(False)

    def set_content(self, widget: QWidget):
        """设置卡片内容"""
        if self._content_widget:
            self._content_layout.removeWidget(self._content_widget)
            self._content_widget.deleteLater()
        self._content_widget = widget
        # 添加分割线
        if self._content_layout.count() == 0:
            div = QFrame()
            div.setFixedHeight(1)
            div.setStyleSheet(f"background-color: {Colors.DIVIDER}; margin-bottom: 12px;")
            self._content_layout.addWidget(div)
        self._content_layout.addWidget(widget)

    def _on_header_click(self, event):
        self._collapsed = not self._collapsed
        self._collapse_icon.setText('▶' if self._collapsed else '▼')
        self._content_container.setVisible(not self._collapsed)

    def is_collapsed(self) -> bool:
        return self._collapsed


class ResultPanel(QWidget):
    def __init__(self, parent=None, stacked_widget=None):
        super().__init__(parent)
        self._current_result = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG};")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # 内容滚动区
        self.scroll = QScrollArea()
        self.scroll.setStyleSheet(Stylesheets.SCROLL)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.content = QWidget()
        self.content.setStyleSheet(f"background-color: {Colors.BG};")
        self.clay = QVBoxLayout(self.content)
        self.clay.setContentsMargins(24, 20, 24, 20)
        self.clay.setSpacing(12)

        # 顶部标题行
        self.clay.addLayout(self._header())

        # 空状态
        self.clay.addWidget(self._empty())
        self.scroll.setWidget(self.content)
        main.addWidget(self.scroll, 1)

    def _header(self):
        """顶部工具栏"""
        hdr = QHBoxLayout()
        hdr.setSpacing(8)

        icon = QLabel('☯')
        icon.setStyleSheet(f"font-size: 14px; color: {Colors.LIUJIN};")
        title = QLabel('排盘结果')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT}; font-family: {Fonts.TITLE};
        """)
        hdr.addWidget(icon)
        hdr.addWidget(title)
        hdr.addStretch()

        # 状态标签
        if not hasattr(self, 'status_lbl') or self.status_lbl is None:
            self.status_lbl = QLabel('')
            self.status_lbl.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
        hdr.addWidget(self.status_lbl)

        # AI分析按钮
        if not hasattr(self, 'ai_analyze_btn') or self.ai_analyze_btn is None:
            self.ai_analyze_btn = QPushButton('🤖 重新分析')
            self.ai_analyze_btn.setStyleSheet(Stylesheets.BTN_PRIMARY)
            self.ai_analyze_btn.setCursor(Qt.PointingHandCursor)
            self.ai_analyze_btn.setVisible(False)
        hdr.addWidget(self.ai_analyze_btn)

        # 功能按钮
        if not hasattr(self, 'refresh_btn') or self.refresh_btn is None:
            self.refresh_btn = QPushButton('⟳ 刷新')
            self.refresh_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
            self.refresh_btn.setCursor(Qt.PointingHandCursor)
            self.refresh_btn.setVisible(False)
        if not hasattr(self, 'copy_btn') or self.copy_btn is None:
            self.copy_btn = QPushButton('📋 复制')
            self.copy_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
            self.copy_btn.setCursor(Qt.PointingHandCursor)
            self.copy_btn.setVisible(False)
        if not hasattr(self, 'export_btn') or self.export_btn is None:
            self.export_btn = QPushButton('📤 导出')
            self.export_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
            self.export_btn.setCursor(Qt.PointingHandCursor)
            self.export_btn.setVisible(False)
        hdr.addWidget(self.refresh_btn)
        hdr.addWidget(self.copy_btn)
        hdr.addWidget(self.export_btn)

        return hdr

    def _empty(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignCenter)
        l.setSpacing(12)
        t = QLabel('☯')
        t.setStyleSheet(f"font-size: 56px; color: {Colors.BORDER};")
        t.setAlignment(Qt.AlignCenter)
        s = QLabel('填写左侧参数，点击开始排盘')
        s.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
        s.setAlignment(Qt.AlignCenter)
        sub = QLabel('支持八字排盘 · 五行分析 · AI智能解读')
        sub.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT4}; font-family: {Fonts.BODY};")
        sub.setAlignment(Qt.AlignCenter)
        l.addStretch(); l.addWidget(t); l.addWidget(s); l.addWidget(sub); l.addStretch()
        w.setMinimumHeight(400)
        return w

    def _info_row(self, data):
        """信息行 - 改为更清晰的key-value布局"""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        gl = QGridLayout(w)
        gl.setContentsMargins(0, 4, 0, 4)
        gl.setHorizontalSpacing(20)
        gl.setVerticalSpacing(10)
        cols = 3
        for i, (label, value) in enumerate(data):
            row, col = divmod(i, cols)
            item_w = QWidget()
            item_w.setStyleSheet(f"""
                background: {Colors.BG};
                border-radius: {Spacing.RADIUS_SM};
                padding: 2px;
            """)
            il = QVBoxLayout(item_w)
            il.setContentsMargins(12, 8, 12, 8)
            il.setSpacing(3)
            lb = QLabel(label)
            lb.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
            vb = QLabel(str(value))
            vb.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; font-weight: {Fonts.W_MEDIUM}; font-family: {Fonts.BODY};")
            vb.setWordWrap(True)
            il.addWidget(lb)
            il.addWidget(vb)
            gl.addWidget(item_w, row, col)
        return w

    def _get_wuxing_color(self, char, is_gan=True):
        """获取天干/地支的五行颜色"""
        mapping = TIANGAN_WUXING if is_gan else DIZHI_WUXING
        info = mapping.get(char)
        if info:
            return info[1]
        return Colors.TEXT

    def _pillars(self, bazi):
        """四柱展示 - 增强版"""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        gl = QGridLayout(w)
        gl.setContentsMargins(0, 4, 0, 4)
        gl.setHorizontalSpacing(10)
        gl.setVerticalSpacing(10)

        for idx, (name, p) in enumerate([('年柱', bazi['year_pillar']), ('月柱', bazi['month_pillar']),
                                          ('日柱', bazi['day_pillar']), ('时柱', bazi['hour_pillar'])]):
            is_day = name == '日柱'
            c = QFrame()
            if is_day:
                c.setStyleSheet(f"""
                    QFrame {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #FFFBF0, stop:1 #FFF5E0);
                        border: 2px solid {Colors.LIUJIN};
                        border-radius: {Spacing.RADIUS};
                    }}
                """)
            else:
                c.setStyleSheet(f"""
                    QFrame {{
                        background: {Colors.CARD};
                        border: 1.5px solid {Colors.BORDER};
                        border-radius: {Spacing.RADIUS};
                    }}
                    QFrame:hover {{
                        border-color: {Colors.QINGHUA_LIGHT};
                    }}
                """)

            cl = QVBoxLayout(c)
            cl.setContentsMargins(14, 12, 14, 12)
            cl.setSpacing(4)
            cl.setAlignment(Qt.AlignCenter)

            nl = QLabel(name)
            nl_color = Colors.LIUJIN if is_day else Colors.TEXT3
            nl.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {nl_color}; font-family: {Fonts.BODY}; font-weight: {Fonts.W_MEDIUM};")
            nl.setAlignment(Qt.AlignCenter)

            # 天干
            gan_char = p[0]
            gan_color = self._get_wuxing_color(gan_char, is_gan=True)
            gan = QLabel(gan_char)
            gan.setStyleSheet(f"font-size: 28px; font-weight: {Fonts.W_BOLD}; color: {gan_color}; font-family: {Fonts.TITLE};")
            gan.setAlignment(Qt.AlignCenter)

            # 分隔
            line = QFrame()
            line.setFixedHeight(1.5)
            line.setFixedWidth(20)
            line.setStyleSheet(f"background-color: {Colors.DIVIDER}; border-radius: 1px;")

            # 地支
            zhi_char = p[1]
            zhi_color = self._get_wuxing_color(zhi_char, is_gan=False)
            zhi = QLabel(zhi_char)
            zhi.setStyleSheet(f"font-size: 28px; font-weight: {Fonts.W_BOLD}; color: {zhi_color}; font-family: {Fonts.TITLE};")
            zhi.setAlignment(Qt.AlignCenter)

            # 五行标签
            wx_gan = TIANGAN_WUXING.get(gan_char, ('', Colors.TEXT3))[0]
            wx_zhi = DIZHI_WUXING.get(zhi_char, ('', Colors.TEXT3))[0]
            wx_label = QLabel(f'{wx_gan}·{wx_zhi}')
            wx_label.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
            wx_label.setAlignment(Qt.AlignCenter)

            cl.addWidget(nl)
            cl.addWidget(gan)
            cl.addWidget(line)
            cl.addWidget(zhi)
            cl.addWidget(wx_label)

            row, col = divmod(idx, 2)
            gl.addWidget(c, row, col)
        return w

    def _wuxing(self, wx):
        """五行分析 - 增强版进度条"""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 4, 0, 4)
        l.setSpacing(10)

        els = [
            ('金', wx.get('金', 0), Colors.METAL, Colors.METAL_LIGHT),
            ('木', wx.get('木', 0), Colors.WOOD, Colors.WOOD_LIGHT),
            ('水', wx.get('水', 0), Colors.WATER, Colors.WATER_LIGHT),
            ('火', wx.get('火', 0), Colors.FIRE, Colors.FIRE_LIGHT),
            ('土', wx.get('土', 0), Colors.EARTH, Colors.EARTH_LIGHT),
        ]
        total = sum(v for _, v, _, _ in els) or 1

        for name, val, c1, c2 in els:
            row = QHBoxLayout()
            row.setSpacing(10)

            # 五行标签
            tag = QLabel(name)
            tag.setFixedWidth(26)
            tag.setFixedHeight(22)
            tag.setAlignment(Qt.AlignCenter)
            tag.setStyleSheet(f"""
                background: {c1};
                color: white;
                font-size: 11px;
                font-weight: {Fonts.W_MEDIUM};
                border-radius: 4px;
                font-family: {Fonts.BODY};
            """)

            # 进度条
            bar = QProgressBar()
            bar.setValue(int(val))
            bar.setTextVisible(False)
            bar.setFixedHeight(14)
            pct = int(val / total * 100) if total > 0 else 0
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 7px;
                    background: {Colors.BG};
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {c1}, stop:1 {c2});
                    border-radius: 7px;
                }}
            """)

            # 数值
            vl = QLabel(f'{val} ({pct}%)')
            vl.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT2}; font-family: {Fonts.MONO};")
            vl.setFixedWidth(60)
            vl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            row.addWidget(tag)
            row.addWidget(bar, 1)
            row.addWidget(vl)
            l.addLayout(row)
        return w

    def _annotations(self, data):
        """吉凶批注 - 增强版"""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 4, 0, 4)
        l.setSpacing(8)
        for item in data:
            tp = item.get('type', '中')
            if tp == '吉':
                bc, bg, icon = Colors.SUCCESS, Colors.SUCCESS_LIGHT, '✦'
                tc = Colors.SUCCESS
            elif tp == '凶':
                bc, bg, icon = Colors.DANGER, Colors.DANGER_LIGHT, '✦'
                tc = Colors.DANGER
            else:
                bc, bg, icon = Colors.WARNING, Colors.WARNING_LIGHT, '◈'
                tc = Colors.WARNING

            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {bg};
                    border-left: 4px solid {bc};
                    border-radius: {Spacing.RADIUS_SM};
                }}
            """)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(12, 10, 12, 10)
            cl.setSpacing(10)

            # 徽章
            badge_container = QVBoxLayout()
            badge_container.setSpacing(2)
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"font-size: 16px; color: {bc};")
            icon_lbl.setAlignment(Qt.AlignCenter)
            badge = QLabel(tp)
            badge.setStyleSheet(f"background:{bc}; color:white; font-size:10px; font-weight:{Fonts.W_MEDIUM}; border-radius:4px; padding:2px 8px; font-family:{Fonts.BODY};")
            badge.setFixedHeight(20)
            badge_container.addWidget(icon_lbl)
            badge_container.addWidget(badge)
            badge_container.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

            txt = QLabel(item.get('text', ''))
            txt.setStyleSheet(f"font-size:{Fonts.SZ_BODY}; color:{tc}; font-family:{Fonts.BODY}; line-height: 1.6;")
            txt.setWordWrap(True)
            cl.addLayout(badge_container)
            cl.addWidget(txt, 1)
            l.addWidget(card)
        return w

    def _rebuild_header(self):
        """重建头部"""
        self.clay.addLayout(self._header())

    def _fade_in_widgets(self):
        """淡入动画效果"""
        self._fade_anims = []
        for i in range(self.clay.count()):
            item = self.clay.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                effect = QGraphicsOpacityEffect(widget)
                effect.setOpacity(0.0)
                widget.setGraphicsEffect(effect)
                anim = QPropertyAnimation(effect, b"opacity")
                anim.setDuration(400)
                anim.setStartValue(0.0)
                anim.setEndValue(1.0)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                self._fade_anims.append(anim)
                QTimer.singleShot(i * 60, anim.start)

    def display_result(self, rd):
        """显示排盘结果 - 使用可折叠卡片"""
        self._current_result = rd
        self._clear_content()

        # 重建头部
        self._rebuild_header()

        self.refresh_btn.setVisible(True)
        self.copy_btn.setVisible(True)
        self.export_btn.setVisible(True)
        self.ai_analyze_btn.setVisible(True)
        self.ai_analyze_btn.setText('🤖 重新分析')
        self.status_lbl.setText('✓ 排盘完成')
        self.status_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.SUCCESS}; font-family:{Fonts.BODY};")

        # 命盘信息卡片（默认展开）
        bi = rd.get('basic_info', {})
        if bi:
            info_card = CollapsibleCard('命盘信息', 'ℹ', accent_color=Colors.QINGHUA, collapsed=False)
            info_card.set_content(self._info_row([
                ('排盘类型', bi.get('pan_type', '-')),
                ('公历日期', bi.get('solar_date', '-')),
                ('农历日期', bi.get('lunar_date', '-')),
                ('出生时辰', bi.get('hour', '-')),
                ('出生地点', bi.get('location', '-')),
                ('性别', bi.get('gender', '-')),
            ]))
            self.clay.addWidget(info_card)

        # 四柱卡片（默认展开，高亮）
        bazi = rd.get('bazi', {})
        if bazi:
            bazi_card = CollapsibleCard('四柱天干地支', '★', accent_color=Colors.LIUJIN, collapsed=False)
            bazi_card.set_content(self._pillars(bazi))
            self.clay.addWidget(bazi_card)

        # 五行分析卡片（默认展开）
        wx = rd.get('wuxing', {})
        if wx:
            wx_card = CollapsibleCard('五行分析', '◆', accent_color=Colors.QINGHUA, collapsed=False)
            wx_card.set_content(self._wuxing(wx))
            self.clay.addWidget(wx_card)

        # 吉凶批注卡片（默认展开）
        an = rd.get('analysis', [])
        if an:
            an_card = CollapsibleCard('吉凶批注', '⚖', accent_color=Colors.ZHUSHA, collapsed=False)
            an_card.set_content(self._annotations(an))
            self.clay.addWidget(an_card)

        self.clay.addStretch()
        self._fade_in_widgets()

    def show_loading(self):
        self._clear_content()
        self._rebuild_header()

        self.status_lbl.setText('排盘中…')
        self.status_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.QINGHUA}; font-family:{Fonts.BODY};")
        self.refresh_btn.setVisible(False)
        self.copy_btn.setVisible(False)
        self.export_btn.setVisible(False)
        self.ai_analyze_btn.setVisible(False)

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignCenter)
        l.setSpacing(14)

        tj = QLabel('☯')
        tj.setStyleSheet(f"font-size: 56px; color: {Colors.QINGHUA};")
        tj.setAlignment(Qt.AlignCenter)
        self._pulse_widget(tj)

        tx = QLabel('正在排盘中…')
        tx.setStyleSheet(f"font-size:15px; color:{Colors.TEXT3}; font-family:{Fonts.BODY};")
        tx.setAlignment(Qt.AlignCenter)

        l.addStretch()
        l.addWidget(tj)
        l.addWidget(tx)
        l.addStretch()
        w.setMinimumHeight(350)
        self.clay.addWidget(w)
        self.clay.addStretch()

    def _pulse_widget(self, widget):
        """脉冲动画效果"""
        self._pulse_state = True
        self._pulse_widget_ref = widget

        def toggle_pulse():
            w = self._pulse_widget_ref
            try:
                if not w or not w.isVisible():
                    return
                self._pulse_state = not self._pulse_state
                color = Colors.QINGHUA if self._pulse_state else Colors.QINGHUA_LIGHT
                w.setStyleSheet(f"font-size: 56px; color: {color};")
            except RuntimeError:
                self._stop_pulse()

        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(toggle_pulse)
        self.pulse_timer.start(750)

    def _stop_pulse(self):
        if hasattr(self, 'pulse_timer') and self.pulse_timer:
            self.pulse_timer.stop()
            self.pulse_timer.deleteLater()
            self.pulse_timer = None
        self._pulse_widget_ref = None

    def clear(self):
        self._stop_pulse()
        self._current_result = None
        self._clear_content()
        self._rebuild_header()
        self.clay.addWidget(self._empty())
        self.status_lbl.setText('')
        self.refresh_btn.setVisible(False)
        self.copy_btn.setVisible(False)
        self.export_btn.setVisible(False)
        self.ai_analyze_btn.setVisible(False)

    def show_ai_loading(self, message: str = 'AI正在深度分析中…'):
        """显示AI分析加载状态"""
        self._clear_content()
        self._rebuild_header()

        self.status_lbl.setText('AI分析中…')
        self.status_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.LIUJIN}; font-family:{Fonts.BODY};")
        self.refresh_btn.setVisible(False)
        self.copy_btn.setVisible(False)
        self.export_btn.setVisible(False)
        self.ai_analyze_btn.setVisible(False)
        self.ai_analyze_btn.setEnabled(False)

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignCenter)
        l.setSpacing(14)

        tj = QLabel('☯')
        tj.setStyleSheet(f"font-size: 56px; color: {Colors.LIUJIN};")
        tj.setAlignment(Qt.AlignCenter)
        self._ai_pulse_widget(tj)

        tx = QLabel(message)
        tx.setStyleSheet(f"font-size:15px; color:{Colors.TEXT2}; font-family:{Fonts.BODY};")
        tx.setAlignment(Qt.AlignCenter)

        sub = QLabel('请稍候，AI正在结合命理知识进行深度解读')
        sub.setStyleSheet(f"font-size:12px; color:{Colors.TEXT3}; font-family:{Fonts.BODY};")
        sub.setAlignment(Qt.AlignCenter)

        l.addStretch()
        l.addWidget(tj)
        l.addWidget(tx)
        l.addWidget(sub)
        l.addStretch()
        w.setMinimumHeight(350)
        self.clay.addWidget(w)
        self.clay.addStretch()

    def _ai_pulse_widget(self, widget):
        self._ai_pulse_state = True
        self._ai_pulse_widget_ref = widget

        def toggle_pulse():
            w = self._ai_pulse_widget_ref
            try:
                if not w or not w.isVisible():
                    return
                self._ai_pulse_state = not self._ai_pulse_state
                color = Colors.LIUJIN if self._ai_pulse_state else Colors.LIUJIN_LIGHT
                w.setStyleSheet(f"font-size: 56px; color: {color};")
            except RuntimeError:
                self._stop_ai_pulse()

        self.ai_pulse_timer = QTimer(self)
        self.ai_pulse_timer.timeout.connect(toggle_pulse)
        self.ai_pulse_timer.start(750)

    def _stop_ai_pulse(self):
        if hasattr(self, 'ai_pulse_timer') and self.ai_pulse_timer:
            self.ai_pulse_timer.stop()
            self.ai_pulse_timer.deleteLater()
            self.ai_pulse_timer = None
        self._ai_pulse_widget_ref = None

    def display_ai_result(self, ai_data: dict):
        """显示AI分析结果 - 使用可折叠卡片"""
        self._stop_ai_pulse()

        rd = getattr(self, '_current_result', {}) or {}

        if not ai_data or not isinstance(ai_data, dict):
            self._show_ai_error('AI 未返回有效内容，请重试')
            return

        self._clear_content()
        self._rebuild_header()

        if hasattr(self, 'refresh_btn') and self.refresh_btn:
            self.refresh_btn.setVisible(True)
        if hasattr(self, 'copy_btn') and self.copy_btn:
            self.copy_btn.setVisible(True)
        if hasattr(self, 'export_btn') and self.export_btn:
            self.export_btn.setVisible(True)
        if hasattr(self, 'ai_analyze_btn') and self.ai_analyze_btn:
            self.ai_analyze_btn.setVisible(True)
            self.ai_analyze_btn.setEnabled(True)
            self.ai_analyze_btn.setText('🔄 重新分析')
        self.status_lbl.setText('✓ AI分析完成')
        self.status_lbl.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.SUCCESS}; font-family:{Fonts.BODY};"
        )

        # 原始排盘结果（折叠状态）
        bi = rd.get('basic_info', {}) or {}
        if bi:
            orig_card = CollapsibleCard('命盘信息', 'ℹ', accent_color=Colors.QINGHUA, collapsed=True)
            orig_card.set_content(self._info_row([
                ('排盘类型', bi.get('pan_type', '-')),
                ('公历日期', bi.get('solar_date', '-')),
                ('农历日期', bi.get('lunar_date', '-')),
                ('出生时辰', bi.get('hour', '-')),
                ('出生地点', bi.get('location', '-')),
                ('性别', bi.get('gender', '-')),
            ]))
            self.clay.addWidget(orig_card)

        bazi = rd.get('bazi', {}) or {}
        if bazi:
            bazi_card = CollapsibleCard('四柱天干地支', '★', accent_color=Colors.LIUJIN, collapsed=True)
            bazi_card.set_content(self._pillars(bazi))
            self.clay.addWidget(bazi_card)

        wx = rd.get('wuxing', {}) or {}
        if wx:
            wx_card = CollapsibleCard('五行分析', '◆', accent_color=Colors.QINGHUA, collapsed=True)
            wx_card.set_content(self._wuxing(wx))
            self.clay.addWidget(wx_card)

        an = rd.get('analysis', []) or []
        if an:
            an_card = CollapsibleCard('吉凶批注', '⚖', accent_color=Colors.ZHUSHA, collapsed=True)
            an_card.set_content(self._annotations(an))
            self.clay.addWidget(an_card)

        # AI分隔标识
        self._add_ai_section_header()

        # AI分析卡片（默认展开）
        sections = [
            ('personality', '性格特质', '🧠', Colors.QINGHUA),
            ('career', '事业财运', '💼', Colors.LIUJIN),
            ('marriage', '婚姻感情', '💕', Colors.ZHUSHA),
            ('health', '健康注意', '💪', Colors.SUCCESS),
            ('pattern_analysis', '格局分析', '🏛', Colors.QINGHUA),
            ('wuxing_balance', '五行平衡分析', '⚖', Colors.LIUJIN),
            ('shishen_analysis', '十神分析', '🔮', Colors.ZHUSHA),
            ('improvement_plan', '改善方案', '🌟', Colors.LIUJIN),
            ('suggestions', '综合建议', '✨', Colors.QINGHUA),
        ]
        has_ai_content = False
        for key, title, icon, color in sections:
            items = ai_data.get(key, []) or []
            if items:
                has_ai_content = True
                ai_card = CollapsibleCard(f'AI·{title}', icon, accent_color=color, collapsed=False)
                ai_card.set_content(self._ai_list(items, color))
                self.clay.addWidget(ai_card)

        if not has_ai_content:
            empty_label = QLabel('AI 未返回有效条目，请点击「重新分析」重试')
            empty_label.setStyleSheet(
                f"color:{Colors.TEXT3}; font-size:{Fonts.SZ_BODY}; "
                f"font-family:{Fonts.BODY}; padding:24px;"
            )
            empty_label.setAlignment(Qt.AlignCenter)
            self.clay.addWidget(empty_label)

        self.clay.addStretch()
        self._safe_clear_graphics_effects()

        if has_ai_content:
            QTimer.singleShot(50, self._scroll_to_ai_section)

    # ----------------- 辅助方法 -----------------

    def _clear_content(self):
        while self.clay.count():
            item = self.clay.takeAt(0)
            w = item.widget() if item else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _add_ai_section_header(self):
        """AI分隔标题"""
        divider = QFrame()
        divider.setFixedHeight(2)
        divider.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 transparent, stop:0.5 {Colors.LIUJIN}, stop:1 transparent); "
            f"margin: 18px 0 10px 0; border: none;"
        )
        self.clay.addWidget(divider)

        title_widget = QWidget()
        title_widget.setStyleSheet("background: transparent;")
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 4)
        title_layout.setSpacing(8)

        icon = QLabel('🤖')
        icon.setStyleSheet(f"font-size: 18px; color: {Colors.LIUJIN};")
        title_layout.addWidget(icon)

        title = QLabel('AI 智能深度分析')
        title.setStyleSheet(
            f"font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD}; "
            f"color: {Colors.LIUJIN}; font-family: {Fonts.TITLE};"
        )
        title_layout.addWidget(title)
        title_layout.addStretch()
        self.clay.addWidget(title_widget)

        sub = QLabel('基于 AI 大模型的专业命理深度解读')
        sub.setStyleSheet(
            f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; "
            f"font-family: {Fonts.BODY}; margin-bottom: 6px;"
        )
        self.clay.addWidget(sub)

    def _safe_clear_graphics_effects(self):
        for i in range(self.clay.count()):
            item = self.clay.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if w is not None and w.graphicsEffect() is not None:
                w.setGraphicsEffect(None)

    def _scroll_to_ai_section(self):
        try:
            for i in range(self.clay.count()):
                item = self.clay.itemAt(i)
                if not item:
                    continue
                w = item.widget()
                if w is None:
                    continue
                if isinstance(w, QLabel) and ('AI' in w.text() or '智能' in w.text()):
                    self.scroll.ensureWidgetVisible(w)
                    return
            sb = self.scroll.verticalScrollBar()
            if sb:
                sb.setValue(sb.maximum())
        except Exception:
            pass

    def _show_ai_error(self, message: str):
        self._clear_content()
        self._rebuild_header()
        self.status_lbl.setText('AI 异常')
        self.status_lbl.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.DANGER}; font-family:{Fonts.BODY};"
        )
        if hasattr(self, 'ai_analyze_btn') and self.ai_analyze_btn:
            self.ai_analyze_btn.setVisible(True)
            self.ai_analyze_btn.setEnabled(True)
            self.ai_analyze_btn.setText('🔄 重新分析')
        tip = QLabel(f'⚠ {message}')
        tip.setStyleSheet(
            f"color:{Colors.TEXT2}; font-size:{Fonts.SZ_BODY}; "
            f"font-family:{Fonts.BODY}; padding:60px 20px;"
        )
        tip.setAlignment(Qt.AlignCenter)
        tip.setWordWrap(True)
        self.clay.addWidget(tip)
        self.clay.addStretch()

    def _ai_list(self, items: list, color: str) -> QWidget:
        """AI分析列表项 - 增强版"""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 4, 0, 4)
        l.setSpacing(8)
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
                font-family:{Fonts.BODY}; line-height: 1.7;
                padding: 2px 0;
            """)
            txt.setWordWrap(True)
            row.addWidget(num)
            row.addWidget(txt, 1)
            l.addLayout(row)
        return w

    def get_chart_data_for_ai(self) -> dict:
        """获取用于AI分析的排盘数据"""
        rd = getattr(self, '_current_result', {})
        if not rd:
            return {}

        bazi = rd.get('bazi', {})
        wuxing = rd.get('wuxing', {})

        chart_data = {
            'bazi': {
                'year': bazi.get('year_pillar', ''),
                'month': bazi.get('month_pillar', ''),
                'day': bazi.get('day_pillar', ''),
                'hour': bazi.get('hour_pillar', ''),
                'rizhu': bazi.get('day_pillar', '')[0] if bazi.get('day_pillar', '') else ''
            },
            'wuxing': {}
        }

        if wuxing:
            total = sum(v for v in wuxing.values() if isinstance(v, (int, float))) or 1
            for wx_name in ['金', '木', '水', '火', '土']:
                val = wuxing.get(wx_name, 0)
                if isinstance(val, (int, float)):
                    chart_data['wuxing'][wx_name] = {
                        'count': val,
                        'percentage': int(val / total * 100)
                    }

        return chart_data
