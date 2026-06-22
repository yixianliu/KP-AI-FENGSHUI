"""
右侧结果面板 - 极简轻量国风（与左侧风格一致）
无独立顶部栏，卡片直接平铺，与左侧表单对齐
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
                             QPushButton, QScrollArea, QProgressBar, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QTimer
from ui.styles import Stylesheets, Colors, Fonts, Spacing

# 天干五行颜色映射
TIANGAN_WUXING = {
    '甲': ('木', '#5A8F6E'), '乙': ('木', '#5A8F6E'),
    '丙': ('火', '#C45C48'), '丁': ('火', '#C45C48'),
    '戊': ('土', '#8B7355'), '己': ('土', '#8B7355'),
    '庚': ('金', '#B8B0A0'), '辛': ('金', '#B8B0A0'),
    '壬': ('水', '#5B8FA8'), '癸': ('水', '#5B8FA8'),
}

# 地支五行颜色映射
DIZHI_WUXING = {
    '寅': ('木', '#5A8F6E'), '卯': ('木', '#5A8F6E'),
    '巳': ('火', '#C45C48'), '午': ('火', '#C45C48'),
    '辰': ('土', '#8B7355'), '戌': ('土', '#8B7355'), '丑': ('土', '#8B7355'), '未': ('土', '#8B7355'),
    '申': ('金', '#B8B0A0'), '酉': ('金', '#B8B0A0'),
    '子': ('水', '#5B8FA8'), '亥': ('水', '#5B8FA8'),
}

# 吉凶图标
LUCK_ICONS = {'吉': '✦', '凶': '✦', '中': '◈'}


class ResultPanel(QWidget):
    def __init__(self, parent=None, stacked_widget=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG};")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # 内容滚动区（无独立顶部栏，与左侧对齐）
        self.scroll = QScrollArea()
        self.scroll.setStyleSheet(Stylesheets.SCROLL)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.content = QWidget()
        self.content.setStyleSheet(f"background-color: {Colors.BG};")
        self.clay = QVBoxLayout(self.content)
        self.clay.setContentsMargins(24, 20, 24, 20)
        self.clay.setSpacing(14)

        # 顶部标题行（与左侧标题对齐）
        self.clay.addLayout(self._header())

        # 青蓝分割线（与左侧对齐）
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {Colors.QINGHUA_LIGHT};")
        self.clay.addWidget(div)

        # 空状态
        self.clay.addWidget(self._empty())
        self.scroll.setWidget(self.content)
        main.addWidget(self.scroll, 1)

    def _header(self):
        """与左侧输入面板标题对齐的头部
        关键修复：保留已存在的按钮/status_lbl 实例，避免重建导致 main_window 中
        提前连接的 clicked 信号失效的问题。
        """
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

        # 状态标签：仅在首次创建
        if not hasattr(self, 'status_lbl') or self.status_lbl is None:
            self.status_lbl = QLabel('')
            self.status_lbl.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
        hdr.addWidget(self.status_lbl)

        # AI分析按钮：仅在首次创建（关键：保留信号连接）
        if not hasattr(self, 'ai_analyze_btn') or self.ai_analyze_btn is None:
            self.ai_analyze_btn = QPushButton('🤖 AI深度分析')
            self.ai_analyze_btn.setStyleSheet(Stylesheets.BTN_PRIMARY)
            self.ai_analyze_btn.setCursor(Qt.PointingHandCursor)
            self.ai_analyze_btn.setVisible(False)
        hdr.addWidget(self.ai_analyze_btn)

        # 刷新/复制/导出按钮：仅在首次创建
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
        l.setSpacing(10)
        t = QLabel('☯')
        t.setStyleSheet(f"font-size: 48px; color: {Colors.BORDER};")
        t.setAlignment(Qt.AlignCenter)
        s = QLabel('填写左侧参数，点击开始排盘')
        s.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
        s.setAlignment(Qt.AlignCenter)
        l.addStretch(); l.addWidget(t); l.addWidget(s); l.addStretch()
        w.setMinimumHeight(400)
        return w

    def _card(self, title, icon, child):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS};
            }}
            QFrame:hover {{
                border: 1.5px solid {Colors.QINGHUA};
            }}
        """)
        # 添加阴影效果（通过样式模拟）
        card.setGraphicsEffect(None)
        l = QVBoxLayout(card)
        l.setContentsMargins(16, 12, 16, 12)
        l.setSpacing(8)

        hdr = QHBoxLayout()
        ic = QLabel(icon)
        ic.setStyleSheet(f"font-size: 14px; color: {Colors.QINGHUA};")
        tl = QLabel(title)
        tl.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL}; font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT2}; font-family: {Fonts.BODY};
        """)
        hdr.addWidget(ic); hdr.addWidget(tl); hdr.addStretch()
        l.addLayout(hdr)

        # 青蓝分割线（与左侧风格一致）
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {Colors.QINGHUA_LIGHT};")
        l.addWidget(div)
        l.addWidget(child)
        return card

    def _info_row(self, data):
        w = QWidget(); w.setStyleSheet("background: transparent;")
        # 使用网格布局，允许换行
        gl = QGridLayout(w); gl.setContentsMargins(0,0,0,0); gl.setSpacing(8)
        cols = 3  # 每行3列
        for i, (label, value) in enumerate(data):
            row, col = divmod(i, cols)
            item = QFrame()
            item.setStyleSheet(f"background: {Colors.BG}; border-radius: {Spacing.RADIUS_SM};")
            il = QVBoxLayout(item); il.setContentsMargins(10,6,10,6); il.setSpacing(2)
            lb = QLabel(label)
            lb.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
            vb = QLabel(str(value))
            vb.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; font-weight: {Fonts.W_BOLD}; font-family: {Fonts.BODY};")
            vb.setWordWrap(True)
            il.addWidget(lb); il.addWidget(vb)
            gl.addWidget(item, row, col)
        return w

    def _get_wuxing_color(self, char, is_gan=True):
        """获取天干/地支的五行颜色"""
        mapping = TIANGAN_WUXING if is_gan else DIZHI_WUXING
        info = mapping.get(char)
        if info:
            return info[1]
        return Colors.TEXT

    def _pillars(self, bazi):
        w = QWidget(); w.setStyleSheet("background: transparent;")
        # 使用网格布局，2x2排列，自动适应宽度
        gl = QGridLayout(w); gl.setContentsMargins(0,0,0,0); gl.setSpacing(8)
        for idx, (name, p) in enumerate([('年柱',bazi['year_pillar']),('月柱',bazi['month_pillar']),
                                          ('日柱',bazi['day_pillar']),('时柱',bazi['hour_pillar'])]):
            is_day = name == '日柱'
            c = QFrame()
            bc = Colors.LIUJIN if is_day else Colors.BORDER
            c.setStyleSheet(f"""
                QFrame {{ background: {Colors.BG}; border: 1.5px solid {bc}; border-radius: {Spacing.RADIUS_SM}; }}
            """)
            cl = QVBoxLayout(c); cl.setContentsMargins(10,8,10,8); cl.setSpacing(3); cl.setAlignment(Qt.AlignCenter)
            nl = QLabel(name)
            nl.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
            nl.setAlignment(Qt.AlignCenter)

            # 天干带五行颜色
            gan_char = p[0]
            gan_color = self._get_wuxing_color(gan_char, is_gan=True)
            gan = QLabel(gan_char)
            gan.setStyleSheet(f"font-size: 22px; font-weight: {Fonts.W_BOLD}; color: {gan_color}; font-family: {Fonts.TITLE};")
            gan.setAlignment(Qt.AlignCenter)

            line = QFrame(); line.setFixedHeight(1.5); line.setFixedWidth(18)
            line.setStyleSheet(f"background-color: {bc}; border-radius: 1px;")

            # 地支带五行颜色
            zhi_char = p[1]
            zhi_color = self._get_wuxing_color(zhi_char, is_gan=False)
            zhi = QLabel(zhi_char)
            zhi.setStyleSheet(f"font-size: 22px; font-weight: {Fonts.W_BOLD}; color: {zhi_color}; font-family: {Fonts.TITLE};")
            zhi.setAlignment(Qt.AlignCenter)

            # 五行标签
            wx_gan = TIANGAN_WUXING.get(gan_char, ('', Colors.TEXT3))[0]
            wx_zhi = DIZHI_WUXING.get(zhi_char, ('', Colors.TEXT3))[0]
            wx_label = QLabel(f'{wx_gan}·{wx_zhi}')
            wx_label.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
            wx_label.setAlignment(Qt.AlignCenter)

            cl.addWidget(nl); cl.addWidget(gan); cl.addWidget(line); cl.addWidget(zhi); cl.addWidget(wx_label)
            row, col = divmod(idx, 2)
            gl.addWidget(c, row, col)
        return w

    def _wuxing(self, wx):
        w = QWidget(); w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(8)
        els = [('金',wx.get('金',0),'#B8B0A0','#D0C8B8'),('木',wx.get('木',0),'#5A8F6E','#7AB89A'),
               ('水',wx.get('水',0),'#5B8FA8','#8AB8D0'),('火',wx.get('火',0),'#C45C48','#D88A78'),
               ('土',wx.get('土',0),'#8B7355','#A68B6B')]
        total = sum(v for _,v,_,_ in els) or 1
        for name, val, c1, c2 in els:
            row = QHBoxLayout(); row.setSpacing(8)
            tag = QLabel(f' {name} ')
            tag.setStyleSheet(f"background:{c1}; color:white; font-size:12px; font-weight:{Fonts.W_BOLD}; border-radius:3px; padding:2px 8px; font-family:{Fonts.BODY};")
            tag.setFixedHeight(22)
            bar = QProgressBar(); bar.setValue(val); bar.setTextVisible(False); bar.setFixedHeight(10)
            pct = int(val/total*100)
            bar.setStyleSheet(f"""
                QProgressBar {{ border:none; border-radius:5px; background:{Colors.BG}; }}
                QProgressBar::chunk {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {c1},stop:1 {c2}); border-radius:5px; }}
            """)
            vl = QLabel(f'{val} ({pct}%)')
            vl.setStyleSheet(f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT2}; font-family:{Fonts.MONO};")
            vl.setFixedWidth(55); vl.setAlignment(Qt.AlignRight)
            row.addWidget(tag); row.addWidget(bar,1); row.addWidget(vl)
            l.addLayout(row)
        return w

    def _annotations(self, data):
        w = QWidget(); w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(6)
        for item in data:
            tp = item.get('type','中')
            if tp == '吉': bc, bg, icon = Colors.SUCCESS, 'rgba(90,143,110,0.08)', '✦'
            elif tp == '凶': bc, bg, icon = Colors.DANGER, 'rgba(196,92,72,0.08)', '✦'
            else: bc, bg, icon = Colors.WARNING, 'rgba(196,149,72,0.08)', '◈'
            if tp == '吉': tc = Colors.SUCCESS
            elif tp == '凶': tc = Colors.DANGER
            else: tc = Colors.TEXT
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background:{bg};
                    border-left: 3px solid {bc};
                    border-radius: {Spacing.RADIUS_SM};
                }}
                QFrame:hover {{
                    background: {bg.replace('0.08', '0.12')};
                    border-left: 3px solid {bc};
                }}
            """)
            cl = QHBoxLayout(card); cl.setContentsMargins(10,7,10,7); cl.setSpacing(8)

            # 图标+标签组合
            badge_container = QVBoxLayout()
            badge_container.setSpacing(2)
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"font-size: 16px; color: {bc};")
            icon_lbl.setAlignment(Qt.AlignCenter)
            badge = QLabel(tp)
            badge.setStyleSheet(f"background:{bc}; color:white; font-size:11px; font-weight:{Fonts.W_BOLD}; border-radius:3px; padding:2px 8px; font-family:{Fonts.BODY};")
            badge.setFixedHeight(20)
            badge_container.addWidget(icon_lbl)
            badge_container.addWidget(badge)
            badge_container.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

            txt = QLabel(item.get('text',''))
            txt.setStyleSheet(f"font-size:{Fonts.SZ_BODY}; color:{tc}; font-family:{Fonts.BODY};")
            txt.setWordWrap(True)
            cl.addLayout(badge_container)
            cl.addWidget(txt,1)
            l.addWidget(card)
        return w

    def _rebuild_header(self):
        """重建头部+分割线，保持与init_ui一致的结构"""
        self.clay.addLayout(self._header())
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {Colors.QINGHUA_LIGHT};")
        self.clay.addWidget(div)

    def _fade_in_widgets(self):
        """为卡片添加淡入动画效果"""
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
                QTimer.singleShot(i * 80, anim.start)

    def display_result(self, rd):
        self._current_result = rd
        while self.clay.count():
            item = self.clay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        # 重建头部
        self._rebuild_header()

        self.refresh_btn.setVisible(True); self.copy_btn.setVisible(True); self.export_btn.setVisible(True)
        self.ai_analyze_btn.setVisible(True)
        self.status_lbl.setText('✓ 排盘完成')
        self.status_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.SUCCESS}; font-family:{Fonts.BODY};")

        bi = rd.get('basic_info',{})
        self.clay.addWidget(self._card('命盘信息','ℹ',self._info_row([
            ('类型',bi.get('pan_type','-')),('公历',bi.get('solar_date','-')),
            ('农历',bi.get('lunar_date','-')),('时辰',bi.get('hour','-')),
            ('地点',bi.get('location','-')),('性别',bi.get('gender','-'))])))

        bazi = rd.get('bazi',{})
        if bazi:
            self.clay.addWidget(self._card('四柱天干地支','★',self._pillars(bazi)))

        wx = rd.get('wuxing',{})
        if wx:
            self.clay.addWidget(self._card('五行分析','◆',self._wuxing(wx)))

        an = rd.get('analysis',[])
        if an:
            self.clay.addWidget(self._card('吉凶批注','⚖',self._annotations(an)))

        self.clay.addStretch()
        self._fade_in_widgets()

    def show_loading(self):
        while self.clay.count():
            item = self.clay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        # 重建头部
        self._rebuild_header()

        self.status_lbl.setText('排盘中…')
        self.status_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.QINGHUA}; font-family:{Fonts.BODY};")
        self.refresh_btn.setVisible(False); self.copy_btn.setVisible(False); self.export_btn.setVisible(False)
        self.ai_analyze_btn.setVisible(False)

        w = QWidget(); w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w); l.setAlignment(Qt.AlignCenter); l.setSpacing(14)
        tj = QLabel('☯')
        tj.setStyleSheet(f"font-size: 56px; color: {Colors.QINGHUA};")
        tj.setAlignment(Qt.AlignCenter)

        # 脉冲缩放动画替代旋转
        self.anim = QPropertyAnimation(tj, b"styleSheet")
        self.anim.setDuration(1500)
        self.anim.setStartValue(f"font-size: 56px; color: {Colors.QINGHUA};")
        self.anim.setEndValue(f"font-size: 56px; color: {Colors.QINGHUA_LIGHT};")
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setLoopCount(-1)
        # 使用定时器实现脉冲效果
        self._pulse_widget(tj)

        tx = QLabel('排盘中…')
        tx.setStyleSheet(f"font-size:15px; color:{Colors.TEXT3}; font-family:{Fonts.BODY};")
        tx.setAlignment(Qt.AlignCenter)
        l.addStretch(); l.addWidget(tj); l.addWidget(tx); l.addStretch()
        w.setMinimumHeight(350)
        self.clay.addWidget(w); self.clay.addStretch()

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
                # C++对象已销毁，停止定时器
                self._stop_pulse()
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(toggle_pulse)
        self.pulse_timer.start(750)

    def _stop_pulse(self):
        """停止脉冲动画定时器"""
        if hasattr(self, 'pulse_timer') and self.pulse_timer:
            self.pulse_timer.stop()
            self.pulse_timer.deleteLater()
            self.pulse_timer = None
        self._pulse_widget_ref = None

    def clear(self):
        self._stop_pulse()
        self._current_result = None
        while self.clay.count():
            item = self.clay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._rebuild_header()
        self.clay.addWidget(self._empty())
        self.status_lbl.setText('')
        self.refresh_btn.setVisible(False); self.copy_btn.setVisible(False); self.export_btn.setVisible(False)
        self.ai_analyze_btn.setVisible(False)

    def show_ai_loading(self, message: str = 'AI正在深度分析中…'):
        """显示AI分析加载状态"""
        while self.clay.count():
            item = self.clay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self._rebuild_header()

        self.status_lbl.setText('AI分析中…')
        self.status_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.LIUJIN}; font-family:{Fonts.BODY};")
        self.refresh_btn.setVisible(False); self.copy_btn.setVisible(False); self.export_btn.setVisible(False)
        self.ai_analyze_btn.setVisible(False)
        self.ai_analyze_btn.setEnabled(False)

        w = QWidget(); w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w); l.setAlignment(Qt.AlignCenter); l.setSpacing(14)

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

        l.addStretch(); l.addWidget(tj); l.addWidget(tx); l.addWidget(sub); l.addStretch()
        w.setMinimumHeight(350)
        self.clay.addWidget(w); self.clay.addStretch()

    def _ai_pulse_widget(self, widget):
        """AI分析脉冲动画效果"""
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
        """停止AI分析脉冲动画"""
        if hasattr(self, 'ai_pulse_timer') and self.ai_pulse_timer:
            self.ai_pulse_timer.stop()
            self.ai_pulse_timer.deleteLater()
            self.ai_pulse_timer = None
        self._ai_pulse_widget_ref = None

    def display_ai_result(self, ai_data: dict):
        """显示AI分析结果
        关键修复：不再调用 display_result(rd) 重建面板（会触发 _fade_in_widgets 把
        全部原始卡片设为 opacity 0），改为直接清空布局后，依次重建：原始结果卡片 →
        AI 分隔标识 → AI 智能分析卡片。
        避免与 fade-in 冲突，确保 AI 内容实时、完整地呈现在右侧面板。
        """
        self._stop_ai_pulse()

        rd = getattr(self, '_current_result', {}) or {}

        # 防御性检查：AI 返回的字段为空时，提示用户重试
        if not ai_data or not isinstance(ai_data, dict):
            self._show_ai_error('AI 未返回有效内容，请重试')
            return

        # 1) 清理当前内容
        self._clear_content()

        # 2) 重建头部（保留已有按钮实例，确保信号连接有效）
        self._rebuild_header()

        # 3) 设置右上角按钮与状态文本
        if hasattr(self, 'refresh_btn') and self.refresh_btn:
            self.refresh_btn.setVisible(True)
        if hasattr(self, 'copy_btn') and self.copy_btn:
            self.copy_btn.setVisible(True)
        if hasattr(self, 'export_btn') and self.export_btn:
            self.export_btn.setVisible(True)
        if hasattr(self, 'ai_analyze_btn') and self.ai_analyze_btn:
            self.ai_analyze_btn.setVisible(True)
            self.ai_analyze_btn.setEnabled(True)
            self.ai_analyze_btn.setText('🤖 重新分析')
        self.status_lbl.setText('✓ AI分析完成')
        self.status_lbl.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.SUCCESS}; font-family:{Fonts.BODY};"
        )

        # 4) 先放回原始排盘结果（命盘信息/四柱/五行/吉凶批注）
        self._add_original_cards(rd)

        # 5) 添加 AI 分隔标识与标题（视觉上明确区分 AI 区域）
        self._add_ai_section_header()

        # 6) 逐项添加 AI 分析卡片
        sections = [
            ('personality', '性格特质', '🧠', Colors.QINGHUA),
            ('career', '事业财运', '💼', Colors.LIUJIN),
            ('marriage', '婚姻感情', '💕', Colors.ZHUSHA),
            ('health', '健康注意', '💪', Colors.SUCCESS),
            ('suggestions', '综合建议', '✨', Colors.QINGHUA),
        ]
        has_ai_content = False
        for key, title, icon, color in sections:
            items = ai_data.get(key, []) or []
            if items:
                has_ai_content = True
                card = self._card(f'AI·{title}', icon, self._ai_list(items, color))
                # 显式取消可能残留的 GraphicsEffect，保证新卡片 opacity=1.0
                card.setGraphicsEffect(None)
                self.clay.addWidget(card)

        if not has_ai_content:
            # 没有任何 AI 内容时给出兜底提示
            empty_label = QLabel('AI 未返回有效条目，请点击「重新分析」重试')
            empty_label.setStyleSheet(
                f"color:{Colors.TEXT3}; font-size:{Fonts.SZ_BODY}; "
                f"font-family:{Fonts.BODY}; padding:24px;"
            )
            empty_label.setAlignment(Qt.AlignCenter)
            self.clay.addWidget(empty_label)

        # 7) 底部弹簧
        self.clay.addStretch()

        # 8) 关键：AI 完成后不再调用 _fade_in_widgets()，避免任何卡片 opacity=0
        # 主动取消旧动画可能残留的 GraphicsEffect
        self._safe_clear_graphics_effects()

        # 9) 滚动到 AI 区域，确保用户能看到 AI 内容
        if has_ai_content:
            QTimer.singleShot(50, self._scroll_to_ai_section)

    # ----------------- 辅助方法：AI 面板重建相关 -----------------

    def _clear_content(self):
        """清空右侧面板内容布局"""
        while self.clay.count():
            item = self.clay.takeAt(0)
            w = item.widget() if item else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _add_original_cards(self, rd: dict):
        """按原顺序重建命盘信息/四柱/五行/吉凶批注卡片"""
        bi = rd.get('basic_info', {}) or {}
        self.clay.addWidget(self._card('命盘信息', 'ℹ', self._info_row([
            ('类型', bi.get('pan_type', '-')),
            ('公历', bi.get('solar_date', '-')),
            ('农历', bi.get('lunar_date', '-')),
            ('时辰', bi.get('hour', '-')),
            ('地点', bi.get('location', '-')),
            ('性别', bi.get('gender', '-')),
        ])))

        bazi = rd.get('bazi', {}) or {}
        if bazi:
            self.clay.addWidget(self._card('四柱天干地支', '★', self._pillars(bazi)))

        wx = rd.get('wuxing', {}) or {}
        if wx:
            self.clay.addWidget(self._card('五行分析', '◆', self._wuxing(wx)))

        an = rd.get('analysis', []) or []
        if an:
            self.clay.addWidget(self._card('吉凶批注', '⚖', self._annotations(an)))

    def _add_ai_section_header(self):
        """添加 AI 分析区域的分隔线与标题，让 AI 区域在视觉上独立且醒目"""
        # 鎏金渐变分隔线
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(2)
        divider.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 transparent, stop:0.5 {Colors.LIUJIN}, stop:1 transparent); "
            f"margin: 18px 0 10px 0; border: none;"
        )
        self.clay.addWidget(divider)

        # 标题行：🤖 + AI 智能深度分析
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

        # 副标题
        sub = QLabel('基于 AI 大模型的专业命理深度解读')
        sub.setStyleSheet(
            f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; "
            f"font-family: {Fonts.BODY}; margin-bottom: 6px;"
        )
        self.clay.addWidget(sub)

    def _safe_clear_graphics_effects(self):
        """清除所有已渲染卡片上的 GraphicsEffect，确保 opacity=1.0（避免淡入残留）"""
        for i in range(self.clay.count()):
            item = self.clay.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if w is not None and w.graphicsEffect() is not None:
                w.setGraphicsEffect(None)

    def _scroll_to_ai_section(self):
        """滚动到 AI 区域，让用户第一眼就看到 AI 分析结果"""
        try:
            # 找到第一个标题包含 'AI' 或 '智能' 的标签作为锚点
            for i in range(self.clay.count()):
                item = self.clay.itemAt(i)
                if not item:
                    continue
                w = item.widget()
                if w is None:
                    continue
                # 通过 objectName 或文本识别
                if isinstance(w, QLabel) and ('AI' in w.text() or '智能' in w.text()):
                    self.scroll.ensureWidgetVisible(w)
                    return
            # 回退：滚动到底部
            sb = self.scroll.verticalScrollBar()
            if sb:
                sb.setValue(sb.maximum())
        except Exception:
            # 滚动失败不影响主流程
            pass

    def _show_ai_error(self, message: str):
        """AI 失败/数据异常时的兜底显示"""
        self._clear_content()
        self._rebuild_header()
        self.status_lbl.setText('AI 异常')
        self.status_lbl.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.DANGER}; font-family:{Fonts.BODY};"
        )
        if hasattr(self, 'ai_analyze_btn') and self.ai_analyze_btn:
            self.ai_analyze_btn.setVisible(True)
            self.ai_analyze_btn.setEnabled(True)
            self.ai_analyze_btn.setText('🤖 重新分析')
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
        """AI分析列表项"""
        w = QWidget(); w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(8)
        for idx, item in enumerate(items):
            row = QHBoxLayout(); row.setSpacing(10)
            num = QLabel(f'{idx+1}')
            num.setStyleSheet(f"""
                background: {color}; color: white;
                font-size: 11px; font-weight: {Fonts.W_BOLD};
                border-radius: 10px; min-width: 20px; min-height: 20px;
                font-family: {Fonts.BODY};
            """)
            num.setAlignment(Qt.AlignCenter)
            num.setFixedSize(20, 20)
            txt = QLabel(str(item))
            txt.setStyleSheet(f"""
                font-size:{Fonts.SZ_BODY}; color:{Colors.TEXT};
                font-family:{Fonts.BODY}; line-height: 1.6;
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
            for wx in ['金', '木', '水', '火', '土']:
                val = wuxing.get(wx, 0)
                if isinstance(val, (int, float)):
                    chart_data['wuxing'][wx] = {
                        'count': val,
                        'percentage': int(val / total * 100)
                    }

        return chart_data
