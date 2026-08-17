"""
右侧结果面板 v5.0 - 精美国风 · 可折叠卡片 · 清晰排版 · 流畅动画
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
                             QPushButton, QScrollArea, QProgressBar, QGraphicsOpacityEffect,
                             QDialog, QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from ui.components.collapsible_card import (CollapsibleCard,
                                          probability_stats_widget,
                                          conclusion_block, suggestion_block,
                                          risk_aware_label)
from ui.components.timeline import fortune_timeline_widget

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



class ResultPanel(QWidget):
    """右侧排盘结果面板：负责展示八字/梅花/六壬等排盘结果、加载与脉冲动画、智能 分析分隔与呈现。

    由 MainWindow 在各板块的结果栈中实例化，接受排盘结果字典并渲染为可折叠卡片；
    同时通过 display_result / show_loading 衔接龙虎山大师兄分析流程。
    """
    def __init__(self, parent=None, stacked_widget=None):
        """初始化结果面板。

        Args:
            parent: 父控件（通常为 MainWindow 的结果栈）
            stacked_widget: 预留的堆叠控件参数，当前未使用，保留以兼容调用

        初始化 智能 可用性标记与淡入动画列表，并构建 UI。
        """
        super().__init__(parent)
        self._current_result = None
        # 智能 功能可用性标记（由 MainWindow 在初始化后注入）
        self._available = True
        self._fade_anims = []
        self.init_ui()

    def init_ui(self):
        """构建面板基础布局：滚动区 + 内容容器 + 顶部标题行 + 空状态。

        内容容器 self.content 使用横向 Expanding 策略以填满右侧宽度；
        顶部标题行与空状态由 _header / _empty 生成并加入 clay 垂直布局。
        """
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
        # 横向自适应填满滚动区视口，使内部卡片随右侧宽度撑满
        self.content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.clay = QVBoxLayout(self.content)
        self.clay.setContentsMargins(24, 20, 24, 20)
        self.clay.setSpacing(16)

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

        # 智能分析按钮
        if not hasattr(self, 'smart_analyze_btn') or self.smart_analyze_btn is None:
            self.smart_analyze_btn = QPushButton('🤖 重新分析')
            self.smart_analyze_btn.setStyleSheet(Stylesheets.BTN_PRIMARY)
            self.smart_analyze_btn.setCursor(Qt.PointingHandCursor)
            self.smart_analyze_btn.setVisible(False)
        hdr.addWidget(self.smart_analyze_btn)

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
            self.export_btn.clicked.connect(self._on_export_click)
        hdr.addWidget(self.refresh_btn)
        hdr.addWidget(self.copy_btn)
        hdr.addWidget(self.export_btn)

        return hdr

    def _empty(self):
        """生成未排盘时的空状态占位部件（太极图标 + 引导文案）。"""
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
        sub = QLabel('支持八字排盘 · 五行分析 · 龙虎山大师兄解读')
        sub.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT4}; font-family: {Fonts.BODY};")
        sub.setAlignment(Qt.AlignCenter)
        l.addStretch(); l.addWidget(t); l.addWidget(s); l.addWidget(sub); l.addStretch()
        w.setMinimumHeight(400)
        return w

    def _info_row(self, data):
        """信息行 - 优化可读性"""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        gl = QGridLayout(w)
        gl.setContentsMargins(8, 6, 8, 6)
        gl.setHorizontalSpacing(24)
        gl.setVerticalSpacing(12)
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
            il.setContentsMargins(14, 10, 14, 10)
            il.setSpacing(4)
            lb = QLabel(label)
            lb.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
            vb = QLabel(str(value))
            vb.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT}; font-weight: {Fonts.W_MEDIUM}; font-family: {Fonts.BODY};")
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

    def _pillars(self, bazi, mingli=None):
        """四柱展示 - 增强版（含藏干、纳音、空亡、十神）"""
        mingli = mingli or {}

        # 把 mingli 里的衍生数据整理成按柱名索引，方便渲染时直接取用
        hidden_stems_map = {}
        for item in mingli.get('hidden_stems', {}).get('hidden_stems', []):
            if isinstance(item, dict):
                hidden_stems_map[item.get('pillar')] = item.get('hidden_stems', [])
        nayin_map = {}
        for item in mingli.get('nayin', []):
            if isinstance(item, dict):
                nayin_map[item.get('pillar')] = item
        kongwang_info = mingli.get('kongwang', {})
        affected_pillars = {}
        for item in kongwang_info.get('affected_pillars', []):
            if isinstance(item, dict):
                affected_pillars[item.get('pillar')] = item
        shishen_map = {}
        for item in mingli.get('shishen', {}).get('details', []):
            if isinstance(item, dict):
                shishen_map[item.get('pillar')] = item.get('gan_shishen', '')

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(w)
        hl.setContentsMargins(10, 6, 10, 6)
        hl.setSpacing(16)
        hl.setAlignment(Qt.AlignCenter)

        for idx, (name, p) in enumerate([('年柱', bazi['year_pillar']), ('月柱', bazi['month_pillar']),
                                          ('日柱', bazi['day_pillar']), ('时柱', bazi['hour_pillar'])]):
            is_day = name == '日柱'

            # 整柱横向排列：天干·地支 左右并排
            c = QFrame()
            if is_day:
                c.setStyleSheet(f"""
                    QFrame {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #FFFBF0, stop:1 #FFF5E0);
                        border: 2px solid {Colors.LIUJIN};
                        border-radius: {Spacing.RADIUS_LG};
                    }}
                """)
            else:
                c.setStyleSheet(f"""
                    QFrame {{
                        background: {Colors.CARD};
                        border: 1.5px solid {Colors.BORDER};
                        border-radius: {Spacing.RADIUS_LG};
                    }}
                    QFrame:hover {{
                        border-color: {Colors.QINGHUA_LIGHT};
                    }}
                """)

            cl = QVBoxLayout(c)
            cl.setContentsMargins(16, 12, 16, 12)
            cl.setSpacing(8)
            cl.setAlignment(Qt.AlignCenter)

            # 柱名（如“年柱”）
            nl = QLabel(name)
            nl_color = Colors.LIUJIN if is_day else Colors.TEXT3
            nl.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {nl_color}; font-family: {Fonts.BODY}; font-weight: {Fonts.W_MEDIUM};")
            nl.setAlignment(Qt.AlignCenter)

            # 五行标签（如“金·火”）
            gan_char = p[0]
            wx_gan = TIANGAN_WUXING.get(gan_char, ('', ''))[0]
            wx_zhi = DIZHI_WUXING.get(p[1], ('', ''))[0]
            wx_label = QLabel(f'{wx_gan}·{wx_zhi}' if wx_gan or wx_zhi else '')
            wx_label.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
            wx_label.setAlignment(Qt.AlignCenter)

            # 天干·地支 圆角色块 + 白色文字
            row_gv = QHBoxLayout()
            row_gv.setSpacing(6)
            row_gv.setAlignment(Qt.AlignCenter)

            gan_color = self._get_wuxing_color(gan_char, is_gan=True)
            gan_chip = QLabel(gan_char)
            gan_chip.setStyleSheet(f"""
                background: {gan_color};
                color: white;
                font-size: 22px;
                font-weight: {Fonts.W_BOLD};
                font-family: {Fonts.TITLE};
                border-radius: {Spacing.RADIUS_SM};
                padding: 6px 10px;
                min-width: 36px;
                min-height: 36px;
            """)
            gan_chip.setAlignment(Qt.AlignCenter)

            dot = QLabel('·')
            dot.setStyleSheet(f"font-size: 14px; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
            dot.setAlignment(Qt.AlignCenter)

            zhi_char = p[1]
            zhi_color = self._get_wuxing_color(zhi_char, is_gan=False)
            zhi_chip = QLabel(zhi_char)
            zhi_chip.setStyleSheet(f"""
                background: {zhi_color};
                color: white;
                font-size: 22px;
                font-weight: {Fonts.W_BOLD};
                font-family: {Fonts.TITLE};
                border-radius: {Spacing.RADIUS_SM};
                padding: 6px 10px;
                min-width: 36px;
                min-height: 36px;
            """)
            zhi_chip.setAlignment(Qt.AlignCenter)

            row_gv.addWidget(gan_chip)
            row_gv.addWidget(dot)
            row_gv.addWidget(zhi_chip)

            # 藏干 + 十神 + 纳音 + 空亡：水平圆角小标签
            detail_widget = QWidget()
            detail_widget.setStyleSheet("background: transparent;")
            detail_row = QHBoxLayout(detail_widget)
            detail_row.setContentsMargins(0, 0, 0, 0)
            detail_row.setSpacing(4)
            detail_row.setAlignment(Qt.AlignCenter)

            hidden = hidden_stems_map.get(name, [])
            if hidden:
                hidden_str = ' '.join(f'{h[0]}' for h in hidden[:3])
                tag = QLabel(f'藏:{hidden_str}')
                tag.setStyleSheet(
                    f"background: {Colors.HOVER}; color: {Colors.TEXT2}; "
                    f"border-radius: {Spacing.RADIUS_SM}; padding: 2px 8px; "
                    f"font-size: {Fonts.SZ_MICRO}; font-family: {Fonts.BODY};"
                )
                detail_row.addWidget(tag)

            pillar_shishen = shishen_map.get(name, '')
            if pillar_shishen:
                tag2 = QLabel(pillar_shishen)
                tag2.setStyleSheet(
                    f"background: {Colors.QINGHUA_GLOW}; color: {Colors.QINGHUA}; "
                    f"border-radius: {Spacing.RADIUS_SM}; padding: 2px 8px; "
                    f"font-size: {Fonts.SZ_MICRO}; font-family: {Fonts.BODY};"
                )
                detail_row.addWidget(tag2)

            nayin_item = nayin_map.get(name, {})
            if nayin_item:
                tag3 = QLabel(nayin_item.get('nayin', ''))
                tag3.setStyleSheet(
                    f"background: {Colors.LIUJIN_GLOW}; color: {Colors.LIUJIN}; "
                    f"border-radius: {Spacing.RADIUS_SM}; padding: 2px 8px; "
                    f"font-size: {Fonts.SZ_MICRO}; font-family: {Fonts.BODY};"
                )
                detail_row.addWidget(tag3)

            kw = affected_pillars.get(name, {})
            if kw:
                tag4 = QLabel(f"空:{kw.get('kongwang_type', '')}")
                tag4.setStyleSheet(
                    f"background: {Colors.DIVIDER}; color: {Colors.TEXT3}; "
                    f"border-radius: {Spacing.RADIUS_SM}; padding: 2px 8px; "
                    f"font-size: {Fonts.SZ_MICRO}; font-family: {Fonts.BODY};"
                )
                detail_row.addWidget(tag4)

            # 把 row_gv layout 包成 widget 再加到 cl，避免 TypeError
            row_gv_widget = QWidget()
            row_gv_widget.setStyleSheet("background: transparent;")
            row_gv_widget.setLayout(row_gv)

            cl.addWidget(nl)
            cl.addWidget(row_gv_widget)
            cl.addWidget(wx_label)
            cl.addWidget(detail_widget)

            hl.addWidget(c, 1)
        return w

    def _wuxing(self, wx, rizhu_wx=None):
        """五行分析 - 强化可读性
        每行：【圆角彩色标签】 + 【大号百分比数字】 + 【宽圆角渐变进度条】 + 【旺/中/弱标注】
        日主五行额外以鎏金高亮并标注『日主』字样。
        """
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 10, 12, 10)
        l.setSpacing(12)

        els = [
            ('金', wx.get('金', 0), Colors.METAL, Colors.METAL_LIGHT, Colors.METAL_DARK),
            ('木', wx.get('木', 0), Colors.WOOD, Colors.WOOD_LIGHT, Colors.WOOD_DARK),
            ('水', wx.get('水', 0), Colors.WATER, Colors.WATER_LIGHT, Colors.WATER_DARK),
            ('火', wx.get('火', 0), Colors.FIRE, Colors.FIRE_LIGHT, Colors.FIRE_DARK),
            ('土', wx.get('土', 0), Colors.EARTH, Colors.EARTH_LIGHT, Colors.EARTH_DARK),
        ]
        total = sum(v for _, v, _, _, _ in els) or 1

        for name, val, c_main, c_light, c_dark in els:
            is_rizhu = bool(rizhu_wx) and name == rizhu_wx
            pct = int(round(val / total * 100)) if total > 0 else 0
            strength = '旺' if pct >= 30 else ('中' if pct >= 15 else '弱')

            # 整行容器
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(10)

            # ---- 彩色圆角标签 ----
            tag_text = f'{name} · 日主' if is_rizhu else name
            tag = QLabel(tag_text)
            tag.setFixedHeight(26)
            tag.setAlignment(Qt.AlignCenter)
            if is_rizhu:
                tag.setStyleSheet(f"""
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Colors.LIUJIN_DARK}, stop:0.5 {Colors.LIUJIN}, stop:1 {Colors.LIUJIN_LIGHT});
                    color: white;
                    font-size: 11px;
                    font-weight: {Fonts.W_BOLD};
                    border-radius: 13px;
                    padding: 0 12px;
                    font-family: {Fonts.BODY};
                """)
            else:
                tag.setStyleSheet(f"""
                    background: {c_main};
                    color: white;
                    font-size: 11px;
                    font-weight: {Fonts.W_MEDIUM};
                    border-radius: 13px;
                    padding: 0 12px;
                    font-family: {Fonts.BODY};
                """)
            rl.addWidget(tag)

            # ---- 大号百分比数字 ----
            pct_lbl = QLabel(f'{pct}%')
            pct_lbl.setFixedWidth(48)
            pct_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            pct_lbl.setStyleSheet(
                f"font-size: 18px; color: {Colors.LIUJIN if is_rizhu else Colors.TEXT}; "
                f"font-weight: {Fonts.W_BOLD}; font-family: {Fonts.MONO};"
            )
            rl.addWidget(pct_lbl)

            # ---- 宽圆角渐变进度条 ----
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(pct)
            bar.setTextVisible(False)
            bar.setFixedHeight(18)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 9px;
                    background: {Colors.BG_DARK};
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {c_dark}, stop:0.5 {c_main}, stop:1 {c_light});
                    border-radius: 9px;
                }}
            """)
            rl.addWidget(bar, 1)

            # ---- 旺/中/弱标注 ----
            st_lbl = QLabel(f'{strength}')
            st_lbl.setFixedWidth(32)
            st_lbl.setAlignment(Qt.AlignCenter)
            if strength == '旺':
                st_sheet = f"background: {Colors.SUCCESS_LIGHT}; color: {Colors.SUCCESS};"
            elif strength == '弱':
                st_sheet = f"background: {Colors.DANGER_LIGHT}; color: {Colors.DANGER};"
            else:
                st_sheet = f"background: {Colors.WARNING_LIGHT}; color: {Colors.WARNING};"
            st_lbl.setStyleSheet(f"""
                {st_sheet}
                font-size: 10px;
                font-weight: {Fonts.W_BOLD};
                border-radius: 10px;
                padding: 0 6px;
                font-family: {Fonts.BODY};
            """)
            rl.addWidget(st_lbl)

            l.addWidget(row)
        return w

    def _annotations(self, data):
        """吉凶批注 - 增强版"""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(10)
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

    def _bazi_types(self, bt):
        """命局类型 - 日主强弱 / 格局类型 / 五行旺衰类别（含含义与用途）"""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(16)

        # 日主强弱
        if bt.get('strength'):
            color = Colors.SUCCESS if bt['strength'] == '身强' else (Colors.WARNING if bt['strength'] == '身弱' else Colors.LIUJIN)
            info = bt.get('strength_info', {}) or {}
            l.addLayout(self._type_block('日主强弱', bt['strength'], color, info.get('meaning', ''), info.get('purpose', '')))

        # 格局类型
        if bt.get('geju_type'):
            geju_color_map = {'专旺格': Colors.LIUJIN, '从格': Colors.ZHUSHA,
                              '扶抑格': Colors.QINGHUA, '中和格': Colors.WOOD}
            color = geju_color_map.get(bt['geju_type'], Colors.QINGHUA)
            info = bt.get('geju_info', {}) or {}
            meaning = info.get('meaning', '')
            sub = bt.get('geju_name', '')
            if sub:
                meaning = f'{sub}（{meaning}）' if meaning else sub
            l.addLayout(self._type_block('格局类型', bt['geju_type'], color, meaning, info.get('purpose', '')))

        # 五行旺衰类别
        cats = bt.get('wuxing_categories') or []
        if cats:
            for cat in cats:
                color = Colors.FIRE if '旺' in cat['label'] else (Colors.WATER if '弱' in cat['label'] else Colors.WOOD)
                element = cat.get('element', '')
                label = f"{element}{cat['label']}" if element else cat['label']
                l.addLayout(self._type_block('五行旺衰', label, color, cat.get('meaning', ''), ''))
        elif bt.get('wuxing_summary'):
            l.addLayout(self._type_block('五行旺衰', bt['wuxing_summary'], Colors.TEXT2, '', ''))

        # 用神 / 喜神 / 忌神
        ys = bt.get('yongshen') or {}
        if ys.get('yongshen') or ys.get('xishen') or ys.get('jishen'):
            yong_txt = f"用神·{ys.get('yongshen', '')}"
            if ys.get('yongshen_name'):
                yong_txt += f"（{ys.get('yongshen_name')}）"
            xi_txt = '、'.join(ys.get('xishen_names', [])) or '—'
            ji_txt = '、'.join(ys.get('jishen_names', [])) or '—'
            purpose = f"{ys.get('purpose', '')}　喜神：{xi_txt}　忌神：{ji_txt}"
            l.addLayout(self._type_block(
                '用神喜忌', yong_txt, Colors.LIUJIN,
                ys.get('meaning', ''), purpose))

        return w

    def _type_block(self, label, value, color, meaning='', purpose=''):
        """类型条目：固定标签 + 色块值 + 含义/用途说明"""
        row = QHBoxLayout()
        row.setSpacing(12)
        row.setAlignment(Qt.AlignTop)

        lb = QLabel(label)
        lb.setFixedWidth(60)
        lb.setStyleSheet(f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY}; padding-top:5px;")
        row.addWidget(lb)

        vb = QVBoxLayout()
        vb.setSpacing(5)

        chip = QLabel(value)
        chip.setStyleSheet(f"""
            background: {color};
            color: white;
            font-size: {Fonts.SZ_SMALL};
            font-weight: {Fonts.W_MEDIUM};
            border-radius: {Spacing.RADIUS_SM};
            padding: 4px 14px;
            font-family: {Fonts.BODY};
        """)
        chip.setFixedHeight(26)
        chip.setAlignment(Qt.AlignCenter)
        vb.addWidget(chip)

        desc = meaning
        if purpose:
            desc = f"{desc}　·　用途：{purpose}" if desc else f"用途：{purpose}"
        if desc:
            dl = QLabel(desc)
            dl.setStyleSheet(f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT2}; font-family:{Fonts.BODY}; line-height:1.5;")
            dl.setWordWrap(True)
            vb.addWidget(dl)

        row.addLayout(vb)
        return row

    # 大运流年展示已迁移至 ui/components/timeline.py::fortune_timeline_widget


    def _rebuild_header(self):
        """重建头部：先移除已有的第一个 header layout，再添加新的"""
        # 移除 init_ui 或上次重建留下的 header layout
        while self.clay.count() > 0:
            first = self.clay.itemAt(0)
            if first is not None and first.layout():
                # 移除但不删除（属顶层布局，不销毁）
                self.clay.removeLayout(first.layout())
                break
            # 如果第一个是 widget（如空状态），也移除
            elif first is not None:
                w = first.widget()
                if w is not None:
                    w.deleteLater()
                self.clay.removeWidget(w) if w else None
                break
            else:
                break
        self.clay.addLayout(self._header())

    def _fade_in_widgets(self):
        """淡入动画效果"""
        self._fade_anims = []
        for i in range(self.clay.count()):
            item = self.clay.itemAt(i)
            if not item:
                continue
            widget = item.widget()
            if widget is None or not widget.isVisible():
                continue
            effect = QGraphicsOpacityEffect(widget)
            effect.setOpacity(0.0)
            widget.setGraphicsEffect(effect)
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(350)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            self._fade_anims.append(anim)
            # 每个widget延迟20ms，总延迟不超过800ms
            QTimer.singleShot(min(i * 20, 800), anim.start)

    def _yuncheng(self, yc):
        """渲染运程总结（事业 / 财运 / 健康 / 感情）"""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(14)

        # 综合（置顶高亮）
        overview = yc.get('overview', '')
        if overview:
            ov = QLabel(overview)
            ov.setWordWrap(True)
            ov.setStyleSheet(
                f"font-size:{Fonts.SZ_BODY}; color:{Colors.TEXT}; "
                f"font-family:{Fonts.BODY}; line-height:1.5; "
                f"background:{Colors.QINGHUA_GLOW}; border-left:3px solid {Colors.LIUJIN}; "
                f"padding:8px 12px; border-radius:{Spacing.RADIUS_SM};"
            )
            l.addWidget(ov)

        sections = [
            ('事业', yc.get('career', ''), Colors.QINGHUA),
            ('财运', yc.get('wealth', ''), Colors.ZHUSHA),
            ('健康', yc.get('health', ''), Colors.SUCCESS),
            ('感情', yc.get('love', ''), Colors.LIUJIN),
        ]
        for title, text, color in sections:
            if not text:
                continue
            sub = QWidget()
            sub.setStyleSheet("background: transparent;")
            sl = QVBoxLayout(sub)
            sl.setContentsMargins(0, 0, 0, 0)
            sl.setSpacing(4)
            th = QLabel(f'▍ {title}')
            th.setStyleSheet(
                f"font-size:{Fonts.SZ_BODY}; font-weight:{Fonts.W_MEDIUM}; "
                f"color:{color}; font-family:{Fonts.BODY};"
            )
            tb = QLabel(text)
            tb.setWordWrap(True)
            tb.setStyleSheet(
                f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT}; "
                f"font-family:{Fonts.BODY}; line-height:1.5;"
            )
            sl.addWidget(th)
            sl.addWidget(tb)
            l.addWidget(sub)

        # 标签
        tags = yc.get('tags', [])
        if tags:
            tg = QWidget()
            tg.setStyleSheet("background: transparent;")
            tl = QHBoxLayout(tg)
            tl.setContentsMargins(0, 4, 0, 0)
            tl.setSpacing(6)
            for t in tags[:8]:
                chip = QLabel(t)
                chip.setStyleSheet(
                    f"background:{Colors.QINGHUA_GLOW}; color:{Colors.QINGHUA}; "
                    f"border:1px solid {Colors.QINGHUA_LIGHT}; "
                    f"border-radius:{Spacing.RADIUS_SM}; font-size:{Fonts.SZ_MICRO}; "
                    f"font-family:{Fonts.BODY}; padding:3px 10px;"
                )
                tl.addWidget(chip)
            tl.addStretch()
            l.addWidget(tg)

        return w

    def display_result(self, rd):
        """显示排盘结果 - 使用可折叠卡片"""
        self._current_result = rd
        self._clear_content()

        # 重建头部
        self._rebuild_header()

        self.refresh_btn.setVisible(True)
        self.copy_btn.setVisible(True)
        self.export_btn.setVisible(True)
        self.smart_analyze_btn.setVisible(True)
        self.smart_analyze_btn.setText('🤖 重新分析')
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

        # 命局类型卡片（默认展开）—— 八字「类型」分类的核心呈现
        bt = rd.get('bazi_types', {})
        if bt and (bt.get('strength') or bt.get('geju_type') or bt.get('wuxing_summary')):
            type_card = CollapsibleCard('命局类型', '📿', accent_color=Colors.ZHUSHA, collapsed=False)
            type_card.set_content(self._bazi_types(bt))
            self.clay.addWidget(type_card)

        # 四柱卡片（默认展开，高亮）
        bazi = rd.get('bazi', {})
        if bazi:
            bazi_card = CollapsibleCard('四柱天干地支', '★', accent_color=Colors.LIUJIN, collapsed=False)
            bazi_card.set_content(self._pillars(bazi, rd.get('mingli')))
            self.clay.addWidget(bazi_card)

        # 五行分析卡片（默认展开）
        wx = rd.get('wuxing', {})
        if wx:
            wx_card = CollapsibleCard('五行分析', '◆', accent_color=Colors.QINGHUA, collapsed=False)
            wx_card.set_content(self._wuxing(wx, bt.get('rizhu_wx')))
            self.clay.addWidget(wx_card)

        # 吉凶批注卡片（默认展开）
        an = rd.get('analysis', [])
        if an:
            an_card = CollapsibleCard('吉凶批注', '⚖', accent_color=Colors.ZHUSHA, collapsed=False)
            an_card.set_content(self._annotations(an))
            self.clay.addWidget(an_card)

        # 运程总结卡片（事业 / 财运 / 健康 / 感情）
        yc = rd.get('yuncheng', {})
        if yc and (yc.get('career') or yc.get('wealth') or yc.get('health') or yc.get('love')):
            yc_card = CollapsibleCard('运程总结', '☯', accent_color=Colors.LIUJIN, collapsed=False)
            yc_card.set_content(self._yuncheng(yc))
            self.clay.addWidget(yc_card)

        # 大运流年卡片（默认展开）
        dayun = rd.get('dayun', {})
        liunian = rd.get('liunian', {})
        if dayun.get('periods') or liunian.get('years'):
            yunshi_card = CollapsibleCard('大运流年', '⏳', accent_color=Colors.LIUJIN, collapsed=False)
            yunshi_card.set_content(fortune_timeline_widget(dayun, liunian, Colors.LIUJIN))
            self.clay.addWidget(yunshi_card)

        self.clay.addStretch()
        self._fade_in_widgets()

    def show_loading(self, message: str = '排盘中…'):
        """展示加载状态（支持排盘和AI分析两种模式）。

        清空旧内容并重建头部，隐藏刷新/复制/导出/智能分析按钮，居中显示太极图标脉冲动画
        与提示文字。排盘时使用青色脉冲，AI分析时使用鎏金色脉冲。
        """
        self._clear_content()
        self._rebuild_header()

        is_ai_loading = message and message != '排盘中…'

        if is_ai_loading:
            self.status_lbl.setText('龙虎山大师兄分析中…')
            self.status_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.LIUJIN}; font-family:{Fonts.BODY};")
        else:
            self.status_lbl.setText('排盘中…')
            self.status_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.QINGHUA}; font-family:{Fonts.BODY};")

        self.refresh_btn.setVisible(False)
        self.copy_btn.setVisible(False)
        self.export_btn.setVisible(False)
        self.smart_analyze_btn.setVisible(False)
        self.smart_analyze_btn.setEnabled(False)

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignCenter)
        l.setSpacing(14)

        tj = QLabel('☯')
        tj.setStyleSheet(f"font-size: 56px; color: {Colors.LIUJIN if is_ai_loading else Colors.QINGHUA};")
        tj.setAlignment(Qt.AlignCenter)
        self._pulse_widget(tj)

        if is_ai_loading:
            tx = QLabel(message)
            tx.setStyleSheet(f"font-size:15px; color:{Colors.TEXT2}; font-family:{Fonts.BODY};")
            tx.setAlignment(Qt.AlignCenter)

            sub = QLabel('请稍候，龙虎山大师兄正在结合命理知识进行深度解读')
            sub.setStyleSheet(f"font-size:12px; color:{Colors.TEXT3}; font-family:{Fonts.BODY};")
            sub.setAlignment(Qt.AlignCenter)
            l.addStretch()
            l.addWidget(tj)
            l.addWidget(tx)
            l.addWidget(sub)
            l.addStretch()
        else:
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

    def show_ai_loading(self, message: str = '龙虎山大师兄正在深度分析中…'):
        """显示智能分析加载状态（别名方法，兼容调用方使用 show_ai_loading 的情况）"""
        self.show_loading(message)

    def _pulse_widget(self, widget):
        """为加载态的图标部件启动脉冲定时器（排盘用青色，AI分析用鎏金色）。"""
        self._stop_pulse()
        self._pulse_state = True
        self._pulse_widget_ref = widget
        self._pulse_color = Colors.LIUJIN if (getattr(self, '_ai_loading', False)) else Colors.QINGHUA
        self._pulse_color_light = Colors.LIUJIN_LIGHT if (getattr(self, '_ai_loading', False)) else Colors.QINGHUA_LIGHT

        def toggle_pulse():
            """脉冲定时器回调：可见时切换图标明暗色，部件销毁则停止脉冲。"""
            w = self._pulse_widget_ref
            try:
                if not w or not w.isVisible():
                    return
                self._pulse_state = not self._pulse_state
                color = self._pulse_color if self._pulse_state else self._pulse_color_light
                w.setStyleSheet(f"font-size: 56px; color: {color};")
            except RuntimeError:
                self._stop_pulse()

        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(toggle_pulse)
        self.pulse_timer.start(750)

    def _stop_pulse(self):
        """停止并销毁加载态的脉冲定时器，解除对脉冲部件的引用。"""
        if hasattr(self, 'pulse_timer') and self.pulse_timer:
            self.pulse_timer.stop()
            self.pulse_timer.deleteLater()
            self.pulse_timer = None
        self._pulse_widget_ref = None

    def clear(self):
        """清空面板：停止脉冲、清除当前结果、重建空状态并隐藏操作按钮。"""
        self._stop_pulse()
        self._current_result = None
        self._clear_content()
        self._rebuild_header()
        self.clay.addWidget(self._empty())
        self.status_lbl.setText('')
        self.refresh_btn.setVisible(False)
        self.copy_btn.setVisible(False)
        self.export_btn.setVisible(False)
        self.smart_analyze_btn.setVisible(False)

    def display_ai_analysis_result(self, smart_data: dict):
        """显示AI分析结果（别名方法，兼容调用方使用 display_ai_analysis_result 的情况）"""
        self.display_ai_result(smart_data)

    def display_ai_result(self, smart_data: dict):
        """显示智能分析结果 - 使用可折叠卡片"""
        self._stop_pulse()
        # 保存 智能 数据，供导出（PDF/Excel/CSV）合并使用
        self._data = smart_data

        rd = getattr(self, '_current_result', {}) or {}

        if not smart_data or not isinstance(smart_data, dict):
            self._show_error('龙虎山大师兄未返回有效内容，请重试')
            return

        self._clear_content()
        self._rebuild_header()

        if hasattr(self, 'refresh_btn') and self.refresh_btn:
            self.refresh_btn.setVisible(True)
        if hasattr(self, 'copy_btn') and self.copy_btn:
            self.copy_btn.setVisible(True)
        if hasattr(self, 'export_btn') and self.export_btn:
            self.export_btn.setVisible(True)
        if hasattr(self, 'smart_analyze_btn') and self.smart_analyze_btn:
            self.smart_analyze_btn.setVisible(True)
            self.smart_analyze_btn.setEnabled(True)
            self.smart_analyze_btn.setText('🔄 重新分析')
        self.status_lbl.setText('✓ 龙虎山大师兄分析完成')
        self.status_lbl.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.SUCCESS}; font-family:{Fonts.BODY};"
        )

        # 原始排盘结果（始终展开，不再折叠；v5.1 起移除折叠导致内容「消失」的问题）
        bi = rd.get('basic_info', {}) or {}
        bt = rd.get('bazi_types', {}) or {}
        if bi:
            orig_card = CollapsibleCard('命盘信息', 'ℹ', accent_color=Colors.QINGHUA, collapsed=False)
            orig_card.set_content(self._info_row([
                ('排盘类型', bi.get('pan_type', '-')),
                ('公历日期', bi.get('solar_date', '-')),
                ('农历日期', bi.get('lunar_date', '-')),
                ('出生时辰', bi.get('hour', '-')),
                ('出生地点', bi.get('location', '-')),
                ('性别', bi.get('gender', '-')),
            ]))
            self.clay.addWidget(orig_card)

        # 命局类型
        if bt and (bt.get('strength') or bt.get('geju_type') or bt.get('wuxing_summary')):
            type_card = CollapsibleCard('命局类型', '📿', accent_color=Colors.ZHUSHA, collapsed=False)
            type_card.set_content(self._bazi_types(bt))
            self.clay.addWidget(type_card)

        bazi = rd.get('bazi', {}) or {}
        if bazi:
            bazi_card = CollapsibleCard('四柱天干地支', '★', accent_color=Colors.LIUJIN, collapsed=False)
            bazi_card.set_content(self._pillars(bazi, rd.get('mingli')))
            self.clay.addWidget(bazi_card)

        wx = rd.get('wuxing', {}) or {}
        if wx:
            wx_card = CollapsibleCard('五行分析', '◆', accent_color=Colors.QINGHUA, collapsed=False)
            wx_card.set_content(self._wuxing(wx, bt.get('rizhu_wx')))
            self.clay.addWidget(wx_card)

        an = rd.get('analysis', []) or []
        if an:
            an_card = CollapsibleCard('吉凶批注', '⚖', accent_color=Colors.ZHUSHA, collapsed=False)
            an_card.set_content(self._annotations(an))
            self.clay.addWidget(an_card)

        # 运程总结
        yc = rd.get('yuncheng', {}) or {}
        if yc and (yc.get('career') or yc.get('wealth') or yc.get('health') or yc.get('love')):
            yc_card = CollapsibleCard('运程总结', '☯', accent_color=Colors.LIUJIN, collapsed=False)
            yc_card.set_content(self._yuncheng(yc))
            self.clay.addWidget(yc_card)

        # 大运流年卡片
        dayun = rd.get('dayun', {}) or {}
        liunian = rd.get('liunian', {}) or {}
        if dayun.get('periods') or liunian.get('years'):
            yunshi_card = CollapsibleCard('大运流年', '⏳', accent_color=Colors.LIUJIN, collapsed=False)
            yunshi_card.set_content(fortune_timeline_widget(dayun, liunian, Colors.LIUJIN))
            self.clay.addWidget(yunshi_card)

        # AI分隔标识
        self._add_section_header(smart_data)

    def _on_export_click(self):
        """导出按钮点击事件"""
        from ui.components.export_dialog import ExportDialog
        from ui.export import CsvExporter, ExcelExporter
        from ui.export.base_exporter import filter_export_data
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        rd = getattr(self, '_current_result', {})
        if not rd:
            QMessageBox.warning(self, '导出失败', '没有可导出的数据')
            return

        # 合并 AI分析数据，使其可随报告一并导出
        export_data = dict(rd)
        ai_data = getattr(self, '_data', None)
        if ai_data and isinstance(ai_data, dict):
            export_data['smart_analysis'] = ai_data

        # 显示导出对话框
        dialog = ExportDialog(rd, parent=self)
        if dialog.exec() == QDialog.Accepted:
            format_type = dialog.get_selected_format()
            # 按用户勾选的章节过滤导出数据
            chapters = dialog.get_selected_chapters()
            export_data = filter_export_data(export_data, chapters)

            # 选择保存路径
            filename = dialog.filename_edit.text().strip()
            if not filename:
                filename = "八字排盘结果"

            if format_type == 'csv':
                ext = '.csv'
                file_filter = 'CSV Files (*.csv)'
            elif format_type == 'excel':
                ext = '.xlsx'
                file_filter = 'Excel Files (*.xlsx)'
            else:
                ext = '.pdf'
                file_filter = 'PDF Files (*.pdf)'

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                '导出文件',
                filename + ext,
                file_filter
            )

            if file_path:
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

    # AI分隔标识
    def _add_section_header(self, smart_data):
        """在原始排盘结果之后插入大师兄分析分隔区与各分析卡片。

        Args:
            smart_data: 大师兄 返回的分析字典，按 personality/career/marriage 等键分组渲染

        以渐变分隔线 + 『龙虎山大师兄分析预测』标题作为 大师兄 内容起点，
        随后按预设章节渲染可折叠分析卡片；若无任何条目则展示空提示。
        末尾清理残留图形特效并延迟滚动到该分隔区（见 _scroll_to_section）。
        """
        # 分隔线
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

        icon = QLabel('🧙')
        icon.setStyleSheet(f"font-size: 18px; color: {Colors.LIUJIN};")
        title_layout.addWidget(icon)

        title = QLabel('龙虎山大师兄分析预测')
        title.setStyleSheet(
            f"font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD}; "
            f"color: {Colors.LIUJIN}; font-family: {Fonts.TITLE};"
        )
        title_layout.addWidget(title)
        title_layout.addStretch()
        self.clay.addWidget(title_widget)

        has_content = False

        # 1) 重点提示（风险感知高亮，含风险关键词的行自动标红）
        key_points = smart_data.get('key_points')
        if isinstance(key_points, (list, tuple)):
            kp_text = '\n'.join(str(x) for x in key_points if x and str(x).strip())
        elif isinstance(key_points, str):
            kp_text = key_points
        else:
            kp_text = ''
        if kp_text and kp_text.strip():
            self.clay.addWidget(risk_aware_label(kp_text.strip(), Colors.LIUJIN))
            has_content = True

        # 2) 整体结论（醒目金边色块，视觉层级高于普通卡片）
        verdict = self._as_text(smart_data.get('final_verdict'))
        if verdict:
            self.clay.addWidget(conclusion_block(verdict, Colors.LIUJIN))
            has_content = True

        # 3) 普通分析列表（字符串列表逐条编号）
        # 字段契约以 core.analysis_storage._JSON_SCHEMAS['bazi'] 为准；
        # marriage / pattern_analysis / suggestions 等为历史废弃键，AI 已不再产出。
        list_fields = [
            ('personality', '性格特质', '🧠', Colors.QINGHUA),
            ('career', '事业财运', '💼', Colors.LIUJIN),
            ('relationships', '婚姻感情', '💕', Colors.ZHUSHA),
            ('health', '健康注意', '💪', Colors.SUCCESS),
            ('four_pillars_detail', '四柱详细解读', '🕰', Colors.LIUJIN),
            ('historical_cases', '历史案例', '📚', Colors.ZHUSHA),
        ]
        for key, title, icon, color in list_fields:
            items = self._as_list(smart_data.get(key))
            if not items:
                continue
            has_content = True
            card = CollapsibleCard(f'龙虎山大师兄·{title}', icon, accent_color=color, collapsed=False)
            card.set_content(self._list(items, color))
            self.clay.addWidget(card)

        # 4) 核心建议（绿边独立色块，从普通列表中提升）
        advice_items = self._as_list(smart_data.get('scenario_advice'))
        if advice_items:
            has_content = True
            self.clay.addWidget(suggestion_block(advice_items, Colors.SUCCESS))

        # 5) 概率统计（含「如何理解这些数据」说明块）
        prob_items = self._as_list(smart_data.get('probability_stats'))
        if prob_items:
            has_content = True
            card = CollapsibleCard('龙虎山大师兄·概率统计', '📊', accent_color=Colors.SUCCESS, collapsed=False)
            card.set_content(probability_stats_widget(prob_items, Colors.SUCCESS))
            self.clay.addWidget(card)

        # 6) 免责声明（段落卡）
        disclaimer = self._as_text(smart_data.get('disclaimer'))
        if disclaimer:
            has_content = True
            card = CollapsibleCard('龙虎山大师兄·免责声明', '⚠', accent_color=Colors.TEXT3, collapsed=False)
            card.set_content(self._paragraph(disclaimer, Colors.TEXT3))
            self.clay.addWidget(card)

        if not has_content:
            empty_label = QLabel('龙虎山大师兄未返回有效条目，请点击「重新分析」重试')
            empty_label.setStyleSheet(
                f"color:{Colors.TEXT3}; font-size:{Fonts.SZ_BODY}; "
                f"font-family:{Fonts.BODY}; padding:24px;"
            )
            empty_label.setAlignment(Qt.AlignCenter)
            self.clay.addWidget(empty_label)

        self.clay.addStretch()
        self._safe_clear_graphics_effects()

        if has_content:
            QTimer.singleShot(50, self._scroll_to_section)

    # ----------------- 辅助方法 -----------------

    def _clear_content(self):
        """清空内容容器：先停掉所有淡入动画，再释放并删除所有子部件。"""
        # 停止并清理所有淡入动画，防止旧动画引用已删除的 widget
        if hasattr(self, '_fade_anims'):
            for anim in self._fade_anims:
                try:
                    anim.stop()
                    anim.deleteLater()
                except Exception:
                    pass
            self._fade_anims = []
        while self.clay.count():
            item = self.clay.takeAt(0)
            w = item.widget() if item else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _safe_clear_graphics_effects(self):
        """遍历内容部件，清除仍残留的 QGraphicsOpacityEffect，避免半透明或动画残留。"""
        for i in range(self.clay.count()):
            item = self.clay.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if w is not None and w.graphicsEffect() is not None:
                w.setGraphicsEffect(None)

    def _scroll_to_section(self):
        """将滚动区定位到 智能 分析分隔标题处。

        通过遍历内容部件、匹配文本包含『分析预测』的 QLabel 实现定位
        （_add_section_header 生成的标题即为此文本）。
        注意：此定位强依赖该文案字面量，若修改用户可见的标题文字会破坏滚动定位。
        """
        try:
            for i in range(self.clay.count()):
                item = self.clay.itemAt(i)
                if not item:
                    continue
                w = item.widget()
                if w is None:
                    continue
                if isinstance(w, QLabel) and '分析预测' in w.text():
                    self.scroll.ensureWidgetVisible(w)
                    return
            sb = self.scroll.verticalScrollBar()
            if sb:
                sb.setValue(sb.maximum())
        except Exception:
            pass

    def _show_error(self, message: str):
        """展示 大师兄 分析异常提示。

        Args:
            message: 要展示的异常/错误说明文案

        清空内容并重建头部，置红状态标签，居中显示带 ⚠ 的提示并重新显示『重新分析』按钮。
        """
        self._clear_content()
        self._rebuild_header()
        self.status_lbl.setText('龙虎山大师兄异常')
        self.status_lbl.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.DANGER}; font-family:{Fonts.BODY};"
        )
        if hasattr(self, 'smart_analyze_btn') and self.smart_analyze_btn:
            self.smart_analyze_btn.setVisible(True)
            self.smart_analyze_btn.setEnabled(True)
            self.smart_analyze_btn.setText('🔄 重新分析')
        tip = QLabel(f'⚠ {message}')
        tip.setStyleSheet(
            f"color:{Colors.TEXT2}; font-size:{Fonts.SZ_BODY}; "
            f"font-family:{Fonts.BODY}; padding:60px 20px;"
        )
        tip.setAlignment(Qt.AlignCenter)
        tip.setWordWrap(True)
        self.clay.addWidget(tip)
        self.clay.addStretch()

    def _list(self, items: list, color: str) -> QWidget:
        """智能分析列表项 - 增强版"""
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
                font-family:{Fonts.BODY}; line-height: 1.7;
                padding: 2px 0;
            """)
            txt.setWordWrap(True)
            row.addWidget(num)
            row.addWidget(txt, 1)
            l.addLayout(row)
        return w

    @staticmethod
    def _as_text(value) -> str:
        """将可能为 None / 字符串 / 列表的字段值统一归一化为纯文本。

        用于 final_verdict / disclaimer 等段落型字段：无论 AI 返回字符串还是
        （退化情况下的）列表，都合并为一段可读文本，避免被当成列表逐字符渲染。
        """
        if value is None:
            return ''
        if isinstance(value, (list, tuple)):
            return '\n'.join(str(x) for x in value if x is not None and str(x).strip())
        return str(value).strip()

    @staticmethod
    def _as_list(value) -> list:
        """将字段值归一化为『字符串列表』，供 _list 逐条编号渲染。

        防御性兜底：字符串会被整体作为单条（而非拆成单字符）；
        None / 空值返回空列表，确保调用方无需再判断类型。
        """
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, (list, tuple)):
            return [str(x) for x in value if x is not None and str(x).strip()]
        return [str(value)]

    def _paragraph(self, text: str, color: str) -> QWidget:
        """段落型内容渲染：单节整体文本，自动换行、行距舒适。"""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(4)
        txt = QLabel(text)
        txt.setWordWrap(True)
        txt.setStyleSheet(
            f"font-size:{Fonts.SZ_BODY}; color:{Colors.TEXT}; "
            f"font-family:{Fonts.BODY}; line-height:1.8; padding: 2px 0;"
        )
        l.addWidget(txt)
        return w

    def get_chart_data_for_ai(self) -> dict:
        """获取用于智能分析的完整排盘数据（含五行明细/十神/命理/大运），确保大师兄分析有充分命理依据

        注意：早期实现只透传「四柱 + 五行计数」，导致十神/命理/大运等核心数据从未送达 AI，
        分析只能泛泛而谈。此处补全全部已计算字段，让 DataIntegrator 能拼出完整 prompt。
        """
        rd = getattr(self, '_current_result', None)
        if not rd or not isinstance(rd, dict):
            return {}

        bazi = rd.get('bazi') or {}
        bi = rd.get('basic_info') or {}

        chart_data = {
            'bazi': {
                'year_pillar': bazi.get('year_pillar', ''),
                'month_pillar': bazi.get('month_pillar', ''),
                'day_pillar': bazi.get('day_pillar', ''),
                'hour_pillar': bazi.get('hour_pillar', ''),
                'rizhu': bazi.get('rizhu', ''),
                'month_zhi': bazi.get('month_zhi', ''),
                'hour_zhi': bazi.get('hour_zhi', ''),
                'solar_date': bi.get('solar_date', ''),
                'lunar_date': bi.get('lunar_date', ''),
            },
            'wuxing': self._adapt_wuxing_for_ai(rd.get('wuxing_detail') or {}),
            'shishen': self._adapt_shishen_for_ai(rd.get('shishen') or {}),
            'mingli': rd.get('mingli') or {},
            'major_fortune': rd.get('dayun') or {},
        }
        return chart_data

    def _adapt_wuxing_for_ai(self, wx_detail: dict) -> dict:
        """将 wuxing_detail 整理为 DataIntegrator 期望的五行结构（补齐占比与强弱字段）。"""
        if not wx_detail or not isinstance(wx_detail, dict):
            return {}
        total = float(wx_detail.get('total_score', 0) or 0)
        out = {}
        for k, v in wx_detail.items():
            if k in ('summary', 'tonggen', 'total_score', 'rizhu_wx'):
                out[k] = v
            elif isinstance(v, dict):
                score = float(v.get('score', 0) or 0)
                pct = round(score / total * 100, 1) if total > 0 else 0.0
                if total > 0:
                    if score >= total * 0.30:
                        strength = '旺'
                    elif score <= total * 0.12:
                        strength = '弱'
                    else:
                        strength = '中'
                else:
                    strength = ''
                out[k] = {
                    'score': score,
                    'count': int(v.get('count', 0) or 0),
                    'percentage': pct,
                    'strength': strength,
                    'description': str(v.get('description', '') or ''),
                }
        return out

    def _adapt_shishen_for_ai(self, ss: dict) -> dict:
        """将十神 details 列表映射为 DataIntegrator 期望的 pillars 结构。"""
        if not ss or not isinstance(ss, dict):
            return {}
        pillars = {}
        for d in ss.get('details', []) or []:
            if not isinstance(d, dict):
                continue
            pillar = d.get('pillar', '')
            if not pillar:
                continue
            pillars.setdefault(pillar, []).append({
                'gan': d.get('gan', ''),
                'zhi': d.get('zhi', ''),
                'shishen': d.get('gan_shishen', ''),
                'weight': 1.0,
            })
        return {
            'summary': ss.get('summary', {}) or {},
            'weight_summary': ss.get('weight_summary', {}) or {},
            'total_weights': ss.get('total_weights', {}) or {},
            'analysis': ss.get('analysis', '') or '',
            'pillars': pillars,
        }
