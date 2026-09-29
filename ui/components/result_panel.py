"""
右侧结果面板 v5.0 - 精美国风 · 可折叠卡片 · 清晰排版 · 流畅动画
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
                             QPushButton, QScrollArea, QProgressBar, QGraphicsOpacityEffect,
                             QDialog, QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from ui.styles import (Stylesheets, Colors, Fonts, Spacing,
                       apply_density, content_margins, DEFAULT_DENSITY)
from ui.components.collapsible_card import (CollapsibleCard,
                                          probability_stats_widget,
                                          conclusion_block, suggestion_block,
                                  risk_aware_label,
                                  register_anchor_scroller,
                                  loading_panel, ResponsiveFlow,
                                  set_all_cards_collapsed,
                                  apply_click_feedback)
from ui.components.timeline import fortune_timeline_widget
from ui.components.icons import icon as load_icon

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
        self._error_holder = None  # 初始化错误态 holder
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
        main.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        main.setSpacing(Spacing.S0)

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
        # M3-1：内容区边距/间距走唯一入口 apply_density（默认 normal 档 (24,24,24,24)/16），
        # 随 MainWindow.density_changed 信号经 on_density_changed 联动（M2-2）。
        self._content_density = DEFAULT_DENSITY
        apply_density(self.clay, self._content_density)

        # 顶部标题行（M3-2 sticky）：用 QWidget 包装，置于滚动区之上常驻可见，
        # 不再加入 clay（可滚动内容区），避免随内容滚出视野。
        self._header_widget = QWidget()
        self._header_widget.setObjectName('result_header_widget')
        self._header_widget.setStyleSheet(
            f"background-color: {Colors.CARD}; border-bottom: 1px solid {Colors.DIVIDER};")
        self._header_layout = self._header()
        self._header_widget.setLayout(self._header_layout)

        # 空状态
        self.clay.addWidget(self._empty())
        self.scroll.setWidget(self.content)
        main.addWidget(self._header_widget)      # 常驻，不随滚动（M3-2）
        main.addWidget(self.scroll, 1)

        # 注册锚点跳转回调：AI 解读区目录导航点击时调用本面板的滚动逻辑
        register_anchor_scroller(self._scroll_to_anchor_id)

    def _header(self):
        """顶部工具栏"""
        hdr = QHBoxLayout()
        hdr.setSpacing(Spacing.S2)

        icon = QLabel('☯')
        icon.setStyleSheet(f"font-size: 13px; color: {Colors.LIUJIN};")
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

        # 取消按钮
        if not hasattr(self, 'cancel_btn') or self.cancel_btn is None:
            self.cancel_btn = QPushButton('✗ 取消')
            self.cancel_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
            self.cancel_btn.setCursor(Qt.PointingHandCursor)
            self.cancel_btn.setVisible(False)
        hdr.addWidget(self.cancel_btn)

        # 智能分析按钮
        if not hasattr(self, 'smart_analyze_btn') or self.smart_analyze_btn is None:
            self.smart_analyze_btn = QPushButton('⚡ 智能分析')
            self.smart_analyze_btn.setStyleSheet(Stylesheets.BTN_PRIMARY)
            self.smart_analyze_btn.setCursor(Qt.PointingHandCursor)
            self.smart_analyze_btn.setVisible(False)
        hdr.addWidget(self.smart_analyze_btn)

        # 功能按钮
        if not hasattr(self, 'refresh_btn') or self.refresh_btn is None:
            self.refresh_btn = QPushButton('刷新')
            self.refresh_btn.setIcon(load_icon('refresh', 16))
            self.refresh_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
            self.refresh_btn.setCursor(Qt.PointingHandCursor)
            self.refresh_btn.setVisible(False)
        if not hasattr(self, 'copy_btn') or self.copy_btn is None:
            self.copy_btn = QPushButton('复制')
            self.copy_btn.setIcon(load_icon('copy', 16))
            self.copy_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
            self.copy_btn.setCursor(Qt.PointingHandCursor)
            self.copy_btn.setVisible(False)
        if not hasattr(self, 'export_btn') or self.export_btn is None:
            self.export_btn = QPushButton('导出')
            self.export_btn.setIcon(load_icon('export', 16))
            self.export_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
            self.export_btn.setCursor(Qt.PointingHandCursor)
            self.export_btn.setVisible(False)
            self.export_btn.clicked.connect(self._on_export_click)
        # 全部卡片 收起/展开 切换按钮（长结果列表快速折叠浏览）
        if not hasattr(self, 'collapse_all_btn') or self.collapse_all_btn is None:
            self.collapse_all_btn = QPushButton('全部收起')
            self.collapse_all_btn.setIcon(load_icon('collapse-all', 16))
            self.collapse_all_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
            self.collapse_all_btn.setCursor(Qt.PointingHandCursor)
            self.collapse_all_btn.setVisible(False)
            self.collapse_all_btn.clicked.connect(self._toggle_collapse_all)
        # T7.3 统一绑定点击微缩放反馈（5 个工具栏按钮一次收口）
        for _btn in (self.smart_analyze_btn, self.refresh_btn, self.copy_btn,
                     self.export_btn, self.collapse_all_btn):
            apply_click_feedback(_btn)
        hdr.addWidget(self.refresh_btn)
        hdr.addWidget(self.copy_btn)
        hdr.addWidget(self.export_btn)
        hdr.addWidget(self.collapse_all_btn)

        return hdr

    def on_density_changed(self, density: tuple):
        """M3-1：密度档变化槽——刷新内容区边距/间距（由 MainWindow.density_changed 驱动）。"""
        self._content_density = density
        apply_density(self.clay, density)
        self.clay.invalidate()

    def _toggle_collapse_all(self):
        """一键收起/展开全部结果卡片，并联动按钮文案。"""
        cards = self.content.findChildren(CollapsibleCard)
        # 任一卡片处于展开态则执行「全部收起」，否则「全部展开」
        any_expanded = any(not c.is_collapsed() for c in cards)
        set_all_cards_collapsed(self.content, collapsed=any_expanded)
        self.collapse_all_btn.setText('全部展开' if any_expanded else '全部收起')

    def _empty(self) -> QWidget:
        """生成未排盘时的空状态占位部件（太极图标 + 引导文案），委托 EmptyState。

        M3-6：统一走 ui/components/states.EmptyState（图标呼吸 + 文案淡入动画），
        消除各面板空状态视觉漂移，禁止伪造数据。
        """
        from ui.components.states import EmptyState
        empty = EmptyState(
            title='暂无排盘结果',
            hint='填写左侧参数，点击开始排盘，即可查看 大师兄 分析',
            icon='☯',
            color=Colors.QINGHUA,
            parent=self,
        )
        return empty

    def _info_row(self, data):
        """信息行 - 响应式流式网格（宽屏 3 列、窄屏自动降列）"""
        flow = ResponsiveFlow(min_item_width=210, max_cols=3, min_cols=1, spacing=12)
        flow.setContentsMargins(Spacing.S2, Spacing.S_PAD_SM, Spacing.S2, Spacing.S_PAD_SM)
        for label, value in data:
            item_w = QFrame()
            item_w.setStyleSheet(f"""
                QFrame {{
                    background: {Colors.BG};
                    border: 1px solid {Colors.DIVIDER};
                    border-radius: {Spacing.RADIUS_SM};
                }}
            """)
            il = QVBoxLayout(item_w)
            il.setContentsMargins(Spacing.S_PAD_XS, Spacing.S_MARGIN_XS, Spacing.S_PAD_XS, Spacing.S_MARGIN_XS)
            il.setSpacing(Spacing.S1)
            lb = QLabel(label)
            lb.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT3}; font-family: {Fonts.BODY}; background: transparent;")
            vb = QLabel(str(value))
            vb.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT}; font-weight: {Fonts.W_MEDIUM}; font-family: {Fonts.BODY}; background: transparent;")
            vb.setWordWrap(True)
            il.addWidget(lb)
            il.addWidget(vb)
            flow.add_widget(item_w)
        return flow

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

        # 响应式流式网格：宽屏四柱横排、窄屏自动换为 2 列 / 1 列
        flow = ResponsiveFlow(min_item_width=190, max_cols=4, min_cols=1, spacing=14)
        flow.setContentsMargins(Spacing.S_MARGIN_XS, Spacing.S_PAD_SM, Spacing.S_MARGIN_XS, Spacing.S_PAD_SM)

        for idx, (name, p) in enumerate([('年柱', bazi['year_pillar']), ('月柱', bazi['month_pillar']),
                                          ('日柱', bazi['day_pillar']), ('时柱', bazi['hour_pillar'])]):
            is_day = name == '日柱'

            # 整柱横向排列：天干·地支 左右并排
            c = QFrame()
            if is_day:
                c.setStyleSheet(f"""
                    QFrame {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 {Colors.HIGHLIGHT_WARM_STRONG}, stop:1 {Colors.HIGHLIGHT_WARM});
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
            cl.setContentsMargins(Spacing.S4, Spacing.S3, Spacing.S4, Spacing.S3)
            cl.setSpacing(Spacing.S2)
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
            row_gv.setSpacing(Spacing.S2)
            row_gv.setAlignment(Qt.AlignCenter)

            # 响应式色块尺寸：普通柱 42px / 日柱放大 48px（按 is_day 直接参数化，
            # 避免用 styleSheet().replace() 拼字符串的脆弱 hack）
            chip_min = 48 if is_day else 42
            chip_max = 52 if is_day else 48
            chip_font = 24 if is_day else 22

            gan_color = self._get_wuxing_color(gan_char, is_gan=True)
            gan_chip = QLabel(gan_char)
            gan_chip.setStyleSheet(f"""
                background: {gan_color};
                color: white;
                font-size: {chip_font}px;
                font-weight: {Fonts.W_BOLD};
                font-family: {Fonts.TITLE};
                border-radius: {Spacing.RADIUS_SM};
                padding: 6px 10px;
                min-width: {chip_min}px;
                min-height: {chip_min}px;
                max-width: {chip_max}px;
                max-height: {chip_max}px;
            """)
            gan_chip.setAlignment(Qt.AlignCenter)

            dot = QLabel('·')
            dot.setStyleSheet(f"font-size: 13px; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
            dot.setAlignment(Qt.AlignCenter)

            zhi_char = p[1]
            zhi_color = self._get_wuxing_color(zhi_char, is_gan=False)
            zhi_chip = QLabel(zhi_char)
            zhi_chip.setStyleSheet(f"""
                background: {zhi_color};
                color: white;
                font-size: {chip_font}px;
                font-weight: {Fonts.W_BOLD};
                font-family: {Fonts.TITLE};
                border-radius: {Spacing.RADIUS_SM};
                padding: 6px 10px;
                min-width: {chip_min}px;
                min-height: {chip_min}px;
                max-width: {chip_max}px;
                max-height: {chip_max}px;
            """)
            zhi_chip.setAlignment(Qt.AlignCenter)

            row_gv.addWidget(gan_chip)
            row_gv.addWidget(dot)
            row_gv.addWidget(zhi_chip)

            # 藏干 + 十神 + 纳音 + 空亡：水平圆角小标签
            detail_widget = QWidget()
            detail_widget.setStyleSheet("background: transparent;")
            detail_row = QHBoxLayout(detail_widget)
            detail_row.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
            detail_row.setSpacing(Spacing.S1)
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
            if row_gv_widget.layout() is None:
                row_gv_widget.setLayout(row_gv)

            cl.addWidget(nl)
            cl.addWidget(row_gv_widget)
            cl.addWidget(wx_label)
            cl.addWidget(detail_widget)

            flow.add_widget(c)
        return flow

    def _wuxing(self, wx, rizhu_wx=None):
        """五行分析 - 强化可读性
        每行：【圆角彩色标签】 + 【大号百分比数字】 + 【宽圆角渐变进度条】 + 【旺/中/弱标注】
        日主五行额外以鎏金高亮并标注『日主』字样。
        """
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(Spacing.S3, Spacing.S_MARGIN_XS, Spacing.S3, Spacing.S_MARGIN_XS)
        l.setSpacing(Spacing.S3)

        els = [
            ('金', wx.get('金', 0), Colors.METAL, Colors.METAL_LIGHT, Colors.METAL_DARK),
            ('木', wx.get('木', 0), Colors.WOOD, Colors.WOOD_LIGHT, Colors.WOOD_DARK),
            ('水', wx.get('水', 0), Colors.WATER, Colors.WATER_LIGHT, Colors.WATER_DARK),
            ('火', wx.get('火', 0), Colors.FIRE, Colors.FIRE_LIGHT, Colors.FIRE_DARK),
            ('土', wx.get('土', 0), Colors.EARTH, Colors.EARTH_LIGHT, Colors.EARTH_DARK),
        ]
        total = sum(v for _, v, _, _, _ in els) or 1

        for bar_idx, (name, val, c_main, c_light, c_dark) in enumerate(els):
            is_rizhu = bool(rizhu_wx) and name == rizhu_wx
            pct = int(round(val / total * 100)) if total > 0 else 0
            strength = '旺' if pct >= 30 else ('中' if pct >= 15 else '弱')

            # 整行容器
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
            rl.setSpacing(Spacing.S3)

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
                f"font-size: 17px; color: {Colors.LIUJIN if is_rizhu else Colors.TEXT}; "
                f"font-weight: {Fonts.W_BOLD}; font-family: {Fonts.MONO};"
            )
            rl.addWidget(pct_lbl)

            # ---- 宽圆角渐变进度条（0→目标值 增长动画）----
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
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

            # 进度条增长动画（动画 parent 绑定到 bar，控件销毁即自动停止）
            bar_anim = QPropertyAnimation(bar, b'value', bar)
            bar_anim.setDuration(700)
            bar_anim.setStartValue(0)
            bar_anim.setEndValue(pct)
            bar_anim.setEasingCurve(QEasingCurve.OutCubic)
            QTimer.singleShot(120 + bar_idx * 90, bar_anim.start)

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
                font-size: 11px;
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
        l.setContentsMargins(Spacing.S2, Spacing.S_PAD_SM, Spacing.S2, Spacing.S_PAD_SM)
        l.setSpacing(Spacing.S3)
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
            cl.setContentsMargins(Spacing.S3, Spacing.S_MARGIN_XS, Spacing.S3, Spacing.S_MARGIN_XS)
            cl.setSpacing(Spacing.S3)

            # 徽章
            badge_container = QVBoxLayout()
            badge_container.setSpacing(Spacing.S1)
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"font-size: 15px; color: {bc};")
            icon_lbl.setAlignment(Qt.AlignCenter)
            badge = QLabel(tp)
            badge.setStyleSheet(f"background:{bc}; color:white; font-size:11px; font-weight:{Fonts.W_MEDIUM}; border-radius:4px; padding:2px 8px; font-family:{Fonts.BODY};")
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
        l.setContentsMargins(Spacing.S2, Spacing.S_PAD_SM, Spacing.S2, Spacing.S_PAD_SM)
        l.setSpacing(Spacing.S4)

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

    def _shier_shen(self, ss_data):
        """十二长生展示：四柱各支在日干下的十二宫状态

        数据来源：bazi_calc.get_shier_shen() → result['shier_shen']
        """
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(Spacing.S2, Spacing.S_PAD_SM, Spacing.S2, Spacing.S_PAD_SM)
        l.setSpacing(Spacing.S3)

        items = ss_data.get('shier_shen', [])
        if not items:
            l.addWidget(QLabel('暂无十二长生数据'))
            return w

        # 十二宫吉凶颜色映射：帝旺/临官/长生 为吉，死/绝/墓 为凶，其余中性
        GONG_GOOD = {'长生', '沐浴', '冠带', '临官', '帝旺', '养', '胎'}
        GONG_BAD = {'死', '绝', '墓', '病', '衰'}

        th = QLabel('▍ 十二长生（日干在各柱的地支状态）')
        th.setStyleSheet(f"font-size:{Fonts.SZ_BODY}; font-weight:{Fonts.W_MEDIUM}; color:{Colors.QINGHUA}; font-family:{Fonts.BODY};")
        l.addWidget(th)

        for item in items:
            pillar = item.get('pillar', '')
            ganzhi = item.get('ganzhi', '')
            gong = item.get('shier_shen', '')
            desc = item.get('description', '')

            if gong in GONG_GOOD:
                bg_color, border_color = Colors.SUCCESS_LIGHT, Colors.SUCCESS
            elif gong in GONG_BAD:
                bg_color, border_color = Colors.DANGER_LIGHT, Colors.DANGER
            else:
                bg_color, border_color = Colors.HOVER, Colors.QINGHUA

            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(Spacing.S1, Spacing.S1, Spacing.S1, Spacing.S1)
            rl.setSpacing(Spacing.S3)

            pn = QLabel(pillar)
            pn.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; font-weight:{Fonts.W_MEDIUM}; color:{Colors.LIUJIN}; font-family:{Fonts.BODY}; min-width:40px;")
            rl.addWidget(pn)

            gz = QLabel(ganzhi)
            gz.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT}; font-family:{Fonts.TITLE};")
            rl.addWidget(gz)

            gong_chip = QLabel(gong)
            gong_chip.setStyleSheet(f"""
                background: {bg_color};
                color: {border_color};
                border: 1px solid {border_color};
                border-radius: {Spacing.RADIUS_SM};
                padding: 2px 10px;
                font-size: {Fonts.SZ_SMALL};
                font-weight: {Fonts.W_MEDIUM};
                font-family: {Fonts.BODY};
            """)
            rl.addWidget(gong_chip)

            dl = QLabel(desc)
            dl.setStyleSheet(f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT2}; font-family:{Fonts.BODY};")
            dl.setWordWrap(True)
            rl.addWidget(dl)
            rl.addStretch()
            l.addWidget(row)

        l.addStretch()
        return w

    def _shensha(self, ss_data):
        """神煞系统展示：吉神、凶煞、中性神煞分类呈现

        数据来源：mingli.shensha → result['mingli']['shensha']
        T4.3 升级：由纵向逐行改为「分类标签流式卡片组」——每组一个分组标题，
        下方为横向自动换行的标签流（QLabel 流布局），每个标签用彩色边框区分吉凶
        （吉神=绿框、凶煞=红框、中性=橙框），        并附「落x柱」小字；悬停标签显示释义。
        """
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(Spacing.S2, Spacing.S_PAD_SM, Spacing.S2, Spacing.S_PAD_SM)
        l.setSpacing(Spacing.S3)

        sections = [
            ('吉神', ss_data.get('positive', []), Colors.SUCCESS,
             Colors.SUCCESS_LIGHT),
            ('凶煞', ss_data.get('negative', []), Colors.DANGER,
             Colors.DANGER_LIGHT),
            ('中性', ss_data.get('neutral', []), Colors.WARNING,
             Colors.WARNING_LIGHT),
        ]

        has_any = False
        for title, items, color, cd in sections:
            if not items:
                continue
            has_any = True
            th = QLabel(f'▍ {title}（{len(items)}）')
            th.setStyleSheet(f"font-size:{Fonts.SZ_BODY}; font-weight:{Fonts.W_MEDIUM}; color:{color}; font-family:{Fonts.BODY};")
            l.addWidget(th)

            # 横向自动换行标签流（窄屏单列、宽屏多列）
            flow = ResponsiveFlow(min_item_width=120, max_cols=4, min_cols=1, spacing=8)
            for item in items:
                name = item.get('name', '')
                location = item.get('location', item.get('pillar', ''))
                txt = item.get('detailed', '') or item.get('description', '')
                badge = QLabel(f'{name} · 落{location}' if location else name)
                badge.setStyleSheet(f"""
                    background: {cd};
                    color: {color};
                    border: 1px solid {color};
                    border-radius: {Spacing.RADIUS_SM};
                    padding: 3px 10px;
                    font-size: {Fonts.SZ_SMALL};
                    font-weight: {Fonts.W_MEDIUM};
                    font-family: {Fonts.BODY};
                """)
                if txt:
                    badge.setToolTip(txt)
                flow.add_widget(badge)
            l.addWidget(flow)

            l.addSpacing(Spacing.S1)

        if not has_any:
            l.addWidget(QLabel('命中无明显神煞'))
        l.addStretch()
        return w

    def _di_zhi_relations(self, rel_data):
        """地支关系可视化：六合/三合/六冲/六害/三刑 → 关系徽章网格 + 图例。

        数据来源：mingli.ganzhi_relations['zhi_relations']
        升级（T4.4）：由平铺文字行改为 ResponsiveFlow 卡片网格，每条含
        关系徽章 + 双柱双支对照 + 吉凶色边框 + 释义；顶部附关系图例条。
        """
        zhi_rels = rel_data.get('zhi_relations', [])
        if not zhi_rels:
            w = QWidget()
            w.setStyleSheet("background: transparent;")
            l = QVBoxLayout(w)
            l.addWidget(QLabel('四柱间无明显地支关系'))
            l.addStretch()
            return w

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(Spacing.S2, Spacing.S_PAD_SM, Spacing.S2, Spacing.S_PAD_SM)
        l.setSpacing(Spacing.S3)

        th = QLabel('▍ 地支关系（四柱干支相互作用）')
        th.setStyleSheet(f"font-size:{Fonts.SZ_BODY}; font-weight:{Fonts.W_MEDIUM}; color:{Colors.ZHUSHA}; font-family:{Fonts.BODY};")
        l.addWidget(th)

        # 关系样式：色 + 图标 + 吉凶底色
        REL_STYLE = {
            '合': (Colors.SUCCESS, '∞', Colors.SUCCESS_LIGHT),
            '冲': (Colors.DANGER, '⚡', Colors.DANGER_LIGHT),
            '害': (Colors.WARNING, '◁', Colors.WARNING_LIGHT),
            '刑': (Colors.DANGER, '△', Colors.DANGER_LIGHT),
            '生': (Colors.WOOD, '↗', Colors.WOOD_DARK),
            '克': (Colors.FIRE, '↘', Colors.FIRE_DARK),
            '被生': (Colors.WATER, '↖', Colors.WATER_DARK),
            '被克': (Colors.METAL, '↙', Colors.METAL_DARK),
        }

        # 关系图例条（取实际出现的关系去重展示）
        seen = []
        for rel in zhi_rels:
            r = rel.get('relation', '')
            if r and r not in seen:
                seen.append(r)
        if seen:
            legend = QFrame()
            legend.setStyleSheet(f"""
                QFrame {{ background: {Colors.HOVER}; border: 1px solid {Colors.DIVIDER};
                    border-radius: {Spacing.RADIUS_SM}; }}
            """)
            lg = QHBoxLayout(legend)
            lg.setContentsMargins(Spacing.S3, Spacing.S2, Spacing.S3, Spacing.S2)
            lg.setSpacing(Spacing.S4)
            lt = QLabel('图例')
            lt.setStyleSheet(f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};")
            lg.addWidget(lt)
            for r in seen:
                color, icon, _bg = REL_STYLE.get(r, (Colors.QINGHUA, '·', Colors.HOVER))
                chip = QLabel(f'{icon} {r}')
                chip.setStyleSheet(
                    f"background:{color}; color:white; border-radius:{Spacing.RADIUS_SM}; "
                    f"padding:2px 8px; font-size:{Fonts.SZ_MICRO}; font-family:{Fonts.BODY};"
                )
                lg.addWidget(chip)
            lg.addStretch()
            l.addWidget(legend)

        # 关系卡片网格（宽屏 2 列、窄屏 1 列）
        flow = ResponsiveFlow(min_item_width=300, max_cols=2, min_cols=1, spacing=12)
        for rel in zhi_rels:
            p1 = rel.get('pillar1', '')
            p2 = rel.get('pillar2', '')
            zhi1 = rel.get('zhi1', '')
            zhi2 = rel.get('zhi2', '')
            relation = rel.get('relation', '')
            desc = rel.get('description', '')
            detail = rel.get('detail_description', '')
            influence = rel.get('influence', '')

            color, icon, bg = REL_STYLE.get(relation, (Colors.QINGHUA, '·', Colors.HOVER))

            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {bg};
                    border: 1px solid {color}66;
                    border-left: 4px solid {color};
                    border-radius: {Spacing.RADIUS};
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(Spacing.S_PAD_XS, Spacing.S3, Spacing.S_PAD_XS, Spacing.S3)
            cl.setSpacing(Spacing.S2)

            # 顶行：关系徽章 + 说明
            head = QHBoxLayout()
            head.setSpacing(Spacing.S2)
            chip = QLabel(f'{icon} {relation}')
            chip.setStyleSheet(f"""
                background: {color}; color: white; border-radius: {Spacing.RADIUS_SM};
                padding: 2px 12px; font-size: {Fonts.SZ_SMALL}; font-weight: {Fonts.W_MEDIUM};
                font-family: {Fonts.BODY};
            """)
            head.addWidget(chip)
            if desc:
                d = QLabel(desc)
                d.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT}; font-family:{Fonts.BODY};")
                head.addWidget(d)
            head.addStretch()
            cl.addLayout(head)

            # 双柱双支对照（p1(zhi1) ↔ p2(zhi2)）
            pair_row = QHBoxLayout()
            pair_row.setSpacing(Spacing.S2)
            pair_row.setAlignment(Qt.AlignVCenter)
            chip1 = QLabel(f'{p1}\n{zhi1}')
            chip1.setStyleSheet(f"""
                background: {Colors.CARD}; border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_SM}; padding: 6px 12px;
                font-size: {Fonts.SZ_SMALL}; font-family: {Fonts.TITLE};
                color: {Colors.LIUJIN}; text-align: center; line-height: 1.4;
            """)
            chip1.setAlignment(Qt.AlignCenter)
            arrow = QLabel('↔')
            arrow.setStyleSheet(f"font-size: 15px; color: {color};")
            arrow.setAlignment(Qt.AlignCenter)
            chip2 = QLabel(f'{p2}\n{zhi2}')
            chip2.setStyleSheet(f"""
                background: {Colors.CARD}; border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_SM}; padding: 6px 12px;
                font-size: {Fonts.SZ_SMALL}; font-family: {Fonts.TITLE};
                color: {Colors.LIUJIN}; text-align: center; line-height: 1.4;
            """)
            chip2.setAlignment(Qt.AlignCenter)
            pair_row.addWidget(chip1)
            pair_row.addWidget(arrow)
            pair_row.addWidget(chip2)
            pair_row.addStretch()
            cl.addLayout(pair_row)

            info_text = detail or influence
            if info_text:
                dl = QLabel(info_text)
                dl.setStyleSheet(f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT2}; font-family:{Fonts.BODY}; line-height:1.5;")
                dl.setWordWrap(True)
                cl.addWidget(dl)

            flow.add_widget(card)
        l.addWidget(flow)
        l.addStretch()
        return w

    def _type_block(self, label, value, color, meaning='', purpose=''):
        """类型条目：固定标签 + 色块值 + 含义/用途说明"""
        row = QHBoxLayout()
        row.setSpacing(Spacing.S3)
        row.setAlignment(Qt.AlignTop)

        lb = QLabel(label)
        lb.setFixedWidth(60)
        lb.setStyleSheet(f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY}; padding-top:5px;")
        row.addWidget(lb)

        vb = QVBoxLayout()
        vb.setSpacing(Spacing.S1)

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
        """重建头部：更新 header widget 内的布局，不清除其他内容。"""
        if hasattr(self, '_header_widget') and self._header_widget is not None:
            self._header_layout = self._header()
            if self._header_widget.layout() is not None:
                self._header_widget.layout().deleteLater()
            self._header_widget.setLayout(self._header_layout)

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
        l.setContentsMargins(Spacing.S2, Spacing.S_PAD_SM, Spacing.S2, Spacing.S_PAD_SM)
        l.setSpacing(Spacing.S4)

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
            sl.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
            sl.setSpacing(Spacing.S1)
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
            tl.setContentsMargins(Spacing.S0, Spacing.S1, Spacing.S0, Spacing.S0)
            tl.setSpacing(Spacing.S2)
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
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        try:
            self._current_result = rd
            self._clear_content()

            # 重建头部
            self._rebuild_header()

            self.refresh_btn.setVisible(True)
            self.copy_btn.setVisible(True)
            self.export_btn.setVisible(True)
            self.collapse_all_btn.setVisible(True)
            self.collapse_all_btn.setText('全部收起')
            self.smart_analyze_btn.setVisible(True)
            self.smart_analyze_btn.setText('⚡ 智能分析')
            self.status_lbl.setText('✓ 排盘完成')
            self.status_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.SUCCESS}; font-family:{Fonts.BODY};")

            logger.info("[ResultPanel] display_result 开始渲染")
        except Exception as e:
            logger.error(f"[ResultPanel] display_result 初始化失败: {e}\n{traceback.format_exc()}")
            self.status_lbl.setText('✗ 显示失败')
            self.status_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.DANGER}; font-family:{Fonts.BODY};")
            raise

        # 命盘信息卡片（默认展开）
        try:
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
            logger.debug("[ResultPanel] 命盘信息卡片渲染完成")
        except Exception as e:
            logger.error(f"[ResultPanel] 命盘信息卡片渲染失败: {e}\n{traceback.format_exc()}")

        # 命局类型卡片（默认展开）—— 八字「类型」分类的核心呈现
        try:
            bt = rd.get('bazi_types', {})
            if bt and (bt.get('strength') or bt.get('geju_type') or bt.get('wuxing_summary')):
                type_card = CollapsibleCard('命局类型', '📿', accent_color=Colors.ZHUSHA, collapsed=False)
                type_card.set_content(self._bazi_types(bt))
                self.clay.addWidget(type_card)
            logger.debug("[ResultPanel] 命局类型卡片渲染完成")
        except Exception as e:
            logger.error(f"[ResultPanel] 命局类型卡片渲染失败: {e}\n{traceback.format_exc()}")

        # 四柱卡片（默认展开，高亮）
        # 双路径兜底：Service 结构下 rd['bazi'] 为 None，回退到顶层摊平字段
        try:
            bazi = rd.get('bazi') or {}
            if not bazi:
                bazi = {
                    'year_pillar': rd.get('year_pillar', ''),
                    'month_pillar': rd.get('month_pillar', ''),
                    'day_pillar': rd.get('day_pillar', ''),
                    'hour_pillar': rd.get('hour_pillar', ''),
                    'rizhu': rd.get('rizhu', ''),
                    'month_zhi': rd.get('month_zhi', ''),
                    'hour_zhi': rd.get('hour_zhi', ''),
                }
            # 验证四柱数据有效性（每柱至少2个字符）
            if bazi and all(len(str(bazi.get(k, ''))) >= 2 for k in ['year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar']):
                bazi_card = CollapsibleCard('四柱天干地支', '★', accent_color=Colors.LIUJIN, collapsed=False)
                bazi_card.set_content(self._pillars(bazi, rd.get('mingli')))
                self.clay.addWidget(bazi_card)
            logger.debug("[ResultPanel] 四柱卡片渲染完成")
        except Exception as e:
            logger.error(f"[ResultPanel] 四柱卡片渲染失败: {e}\n{traceback.format_exc()}")

        # 五行分析卡片（默认展开）
        # 双路径兜底：Service 结构下 rd['wuxing'] 为 None，回退到 wuxing_detail 提取 count
        try:
            wx = rd.get('wuxing') or {}
            if not wx:
                wx_detail = rd.get('wuxing_detail') or {}
                if isinstance(wx_detail, dict):
                    wx = {k: v.get('count', 0) if isinstance(v, dict) else v
                          for k, v in wx_detail.items() if k in ('木', '火', '土', '金', '水')}
            if wx:
                wx_card = CollapsibleCard('五行分析', '◆', accent_color=Colors.QINGHUA, collapsed=False)
                wx_card.set_content(self._wuxing(wx, bt.get('rizhu_wx')))
                self.clay.addWidget(wx_card)
            logger.debug("[ResultPanel] 五行分析卡片渲染完成")
        except Exception as e:
            logger.error(f"[ResultPanel] 五行分析卡片渲染失败: {e}\n{traceback.format_exc()}")

        # 吉凶批注卡片（默认展开）
        try:
            an = rd.get('analysis', [])
            if an:
                an_card = CollapsibleCard('吉凶批注', '⚖', accent_color=Colors.ZHUSHA, collapsed=False)
                an_card.set_content(self._annotations(an))
                self.clay.addWidget(an_card)
            logger.debug("[ResultPanel] 吉凶批注卡片渲染完成")
        except Exception as e:
            logger.error(f"[ResultPanel] 吉凶批注卡片渲染失败: {e}\n{traceback.format_exc()}")

        # 运程总结卡片（事业 / 财运 / 健康 / 感情）
        try:
            yc = rd.get('yuncheng', {})
            if yc and (yc.get('career') or yc.get('wealth') or yc.get('health') or yc.get('love')):
                yc_card = CollapsibleCard('运程总结', '☯', accent_color=Colors.LIUJIN, collapsed=False)
                yc_card.set_content(self._yuncheng(yc))
                self.clay.addWidget(yc_card)
            logger.debug("[ResultPanel] 运程总结卡片渲染完成")
        except Exception as e:
            logger.error(f"[ResultPanel] 运程总结卡片渲染失败: {e}\n{traceback.format_exc()}")

        # 十二长生卡片（默认展开）
        try:
            ss_raw = rd.get('shier_shen', {})
            if ss_raw and ss_raw.get('shier_shen'):
                ss_card = CollapsibleCard('十二长生', '☰', accent_color=Colors.QINGHUA, collapsed=False)
                ss_card.set_content(self._shier_shen(ss_raw))
                self.clay.addWidget(ss_card)
            logger.debug("[ResultPanel] 十二长生卡片渲染完成")
        except Exception as e:
            logger.error(f"[ResultPanel] 十二长生卡片渲染失败: {e}\n{traceback.format_exc()}")

        # 神煞系统卡片（默认展开）
        try:
            shensha_data = rd.get('mingli', {}).get('shensha', {}) if isinstance(rd.get('mingli'), dict) else {}
            if shensha_data and (shensha_data.get('positive') or shensha_data.get('negative') or shensha_data.get('neutral')):
                ss_card2 = CollapsibleCard('神煞系统', '☆', accent_color=Colors.ZHUSHA, collapsed=False)
                ss_card2.set_content(self._shensha(shensha_data))
                self.clay.addWidget(ss_card2)
            logger.debug("[ResultPanel] 神煞系统卡片渲染完成")
        except Exception as e:
            logger.error(f"[ResultPanel] 神煞系统卡片渲染失败: {e}\n{traceback.format_exc()}")

        # 地支关系卡片（默认展开）
        try:
            gz_rel_data = rd.get('mingli', {}).get('ganzhi_relations', {}) if isinstance(rd.get('mingli'), dict) else {}
            if gz_rel_data and gz_rel_data.get('zhi_relations'):
                rel_card = CollapsibleCard('地支关系', '⚖', accent_color=Colors.LIUJIN, collapsed=False)
                rel_card.set_content(self._di_zhi_relations(gz_rel_data))
                self.clay.addWidget(rel_card)
            logger.debug("[ResultPanel] 地支关系卡片渲染完成")
        except Exception as e:
            logger.error(f"[ResultPanel] 地支关系卡片渲染失败: {e}\n{traceback.format_exc()}")

        # 大运流年卡片（默认展开）
        try:
            dayun = rd.get('dayun', {})
            liunian = rd.get('liunian', {})
            if dayun.get('periods') or liunian.get('years'):
                yunshi_card = CollapsibleCard('大运流年', '⏳', accent_color=Colors.LIUJIN, collapsed=False)
                yunshi_card.set_content(fortune_timeline_widget(dayun, liunian, Colors.LIUJIN))
                self.clay.addWidget(yunshi_card)
            logger.debug("[ResultPanel] 大运流年卡片渲染完成")
        except Exception as e:
            logger.error(f"[ResultPanel] 大运流年卡片渲染失败: {e}\n{traceback.format_exc()}")

        self.clay.addStretch()
        try:
            self._fade_in_widgets()
            logger.info("[ResultPanel] display_result 渲染全部完成")
        except Exception as e:
            logger.error(f"[ResultPanel] 淡入动画失败: {e}\n{traceback.format_exc()}")

    def show_loading(self, message: str = '排盘中…'):
        """展示加载状态（支持排盘和AI分析两种模式）。

        清空旧内容并重建头部，隐藏操作按钮，居中显示「旋转太极 + 主文案 +
        轮播进度提示」加载面板：排盘使用青花蓝主题，AI 解读使用鎏金主题。
        """
        self._stop_pulse()
        self._clear_content()
        self._rebuild_header()

        is_ai_loading = message and message != '排盘中…'

        if is_ai_loading:
            self.status_lbl.setText('龙虎山大师兄算命中…')
            self.status_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.LIUJIN}; font-family:{Fonts.BODY};")
            panel = loading_panel(
                message=message or '龙虎山大师兄正在亲批详断中…',
                sub='请稍候，大师兄正依四柱五行、大运流年逐项推敲',
                color=Colors.LIUJIN,
                hints=['大师兄正凝神审阅命盘…', '正在推敲五行旺衰与喜用…',
                       '正在结合大运流年研判趋势…', '正在撰写趋吉避凶建议…'])
        else:
            self.status_lbl.setText('排盘中…')
            self.status_lbl.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.QINGHUA}; font-family:{Fonts.BODY};")
            panel = loading_panel(
                message='正在排盘中…',
                sub='依立春换年、五虎遁月、五鼠遁时排布四柱',
                color=Colors.QINGHUA,
                hints=['正在排布四柱干支…', '正在推演五行旺衰…',
                       '正在核对神煞与格局…', '正在排布大运流年…'])

        self.refresh_btn.setVisible(False)
        self.copy_btn.setVisible(False)
        self.export_btn.setVisible(False)
        self.collapse_all_btn.setVisible(False)
        self.smart_analyze_btn.setVisible(False)
        self.smart_analyze_btn.setEnabled(False)

        panel.setMinimumHeight(360)
        self.clay.addWidget(panel)
        self.clay.addStretch()

    def show_ai_loading(self, message: str = '龙虎山大师兄正在亲批详断中…'):
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
        self.collapse_all_btn.setVisible(False)
        self.smart_analyze_btn.setVisible(False)

    def display_ai_analysis_result(self, smart_data: dict):
        """显示AI分析结果（别名方法，兼容调用方使用 display_ai_analysis_result 的情况）"""
        self.display_ai_result(smart_data)

    def display_ai_result(self, smart_data: dict):
        """显示智能分析结果 - 使用可折叠卡片。

        修复点：渲染前先清掉旧 AI 解读容器（ai_analysis_container），
        防止重复回调导致两份解读并存。
        """
        self._stop_pulse()
        # 渲染前先清掉旧 AI 解读容器，避免重复
        self._clear_prev_ai_container()
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
            self.smart_analyze_btn.setText('⚡ 智能分析')
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
        """把 AI 解读渲染委托给公共渲染器，避免三面板字段映射漂移。"""
        # 若 AI 未配置，则不显示龙虎山大师兄分析预测
        try:
            from core.ai_config import is_ai_configured
            if not is_ai_configured():
                return
        except Exception:
            pass
        from ui.components.ai_analysis_renderer import render_analysis as render
        render('bazi', smart_data, self.clay)
        QTimer.singleShot(50, self._scroll_to_section)

    # ----------------- 辅助方法 -----------------

    def _clear_content(self):
        """清空内容容器：M3-2 起 header 已移出 clay（改为 sticky），故删除全部子项。

        风险提示对应方案 §7：原「从索引 1 起删、保留索引 0 header」的约定随
        header 移出 clay 而失效，必须改为清空整个 clay。
        """
        # 停止并清理所有淡入动画，防止旧动画引用已删除的 widget
        if hasattr(self, '_fade_anims'):
            for anim in self._fade_anims:
                try:
                    anim.stop()
                    anim.deleteLater()
                except Exception:
                    pass
            self._fade_anims = []
        # clay 不再包含 header（sticky 在主布局），清空全部内容
        while self.clay.count() > 0:
            item = self.clay.takeAt(0)
            w = item.widget() if item else None
            if w is not None:
                self._stop_widget_anims(w)
                w.deleteLater()

    @staticmethod
    def _stop_widget_anims(widget):
        """停止挂在该部件上的自定义动画（空状态呼吸 / 文案淡入）。

        空状态部件被移除时其循环呼吸动画仍在跑，不显式 stop 会在
        deleteLater 生效前持续触发重绘，故在此统一收口。
        """
        for attr in ('_empty_breathe', '_empty_text_anims', '_page_fade_anim'):
            anim = getattr(widget, attr, None)
            if anim is None:
                continue
            try:
                if isinstance(anim, (list, tuple)):
                    for a in anim:
                        a.stop()
                else:
                    anim.stop()
            except RuntimeError:
                pass  # 动画对象已随部件销毁

    def _clear_prev_ai_container(self):
        """移除上一次 AI 解读渲染时插入的容器（ai_analysis_container），
        防止连续排盘/重复完成回调导致两份 AI 解读并存。"""
        try:
            for i in range(self.clay.count() - 1, -1, -1):
                item = self.clay.itemAt(i)
                if item is None:
                    continue
                w = item.widget()
                if w is None:
                    continue
                if w.objectName() == 'ai_analysis_container':
                    self.clay.removeWidget(w)
                    w.deleteLater()
                    return
        except Exception:
            pass

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

    def _scroll_to_anchor_id(self, anchor_id: str) -> None:
        """根据锚点 ID 滚动到对应章节（AI 解读区目录导航点击回调）。

        通过 findChild(QWidget, objectName) 定位带特定 objectName 的部件，
        再使用 ensureWidgetVisible 平滑滚动到目标位置。

        Args:
            anchor_id: 章节部件的 objectName（如 'ai_anchor_personality'）
        """
        if not anchor_id:
            return
        try:
            target = self.content.findChild(QWidget, anchor_id)
            if target is not None:
                self.scroll.ensureWidgetVisible(target, 0, 40)
            else:
                # 兜底：定位到 AI 解读区开始
                self._scroll_to_section()
        except Exception:
            pass

    def _show_error(self, message: str):
        """展示 大师兄 分析异常提示，委托 ErrorState（M3-6：统一错误视觉 + 重试信号）。

        Args:
            message: 要展示的异常/错误说明文案

        清空内容并重建头部，以 ErrorState 居中展示（统一错误视觉语言），
        保留操作按钮可见，错误态由 ErrorState 提供重试入口。
        """
        from ui.components.states import ErrorState

        self._clear_content()
        self._rebuild_header()

        # 清空状态标签，由 ErrorState 接管
        self.status_lbl.setText('')
        self.status_lbl.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.DANGER}; font-family:{Fonts.BODY};"
        )

        # 重建头部：确保智能分析按钮可见
        if hasattr(self, 'smart_analyze_btn') and self.smart_analyze_btn:
            self.smart_analyze_btn.setVisible(True)
            self.smart_analyze_btn.setEnabled(True)
            self.smart_analyze_btn.setText('⚡ 智能分析')

        holder = QWidget()
        holder.setStyleSheet('background: transparent;')
        v = QVBoxLayout(holder)
        v.setContentsMargins(Spacing.S0, Spacing.S0, Spacing.S0, Spacing.S0)
        v.setSpacing(Spacing.S0)
        err = ErrorState(
            title='分析异常',
            message=message,
            retry_hint='重试',
            show_retry=True,
            color=Colors.DANGER,
            parent=holder,
        )
        # M3-6：重试信号由上层 MainWindow 重绑（_on_*_ai_analyze 路径承接重试）
        err.retry.connect(self._handle_error_retry)
        v.addWidget(err, 1)

        # 替换旧错误态/提示
        self._clear_error_holder()
        self.clay.addWidget(holder)
        self.clay.addStretch()

    def _handle_error_retry(self):
        """ErrorState 重试触发：恢复面板至可重试状态（清空错误态 + 恢复按钮）。

        八字面板 AI 失败后由 MainWindow 通过 _on_bazi_ai_analyze 重新触发分析，
        此处负责将错误态还原为正常可分析状态，避免错误态残留阻断重试。
        """
        # 清空旧错误态 holder
        self._clear_error_holder()
        self._error_holder = None

        # 恢复智能分析按钮可见并可点击
        if hasattr(self, 'smart_analyze_btn') and self.smart_analyze_btn:
            self.smart_analyze_btn.setVisible(True)
            self.smart_analyze_btn.setEnabled(True)
            self.smart_analyze_btn.setText('⚡ 智能分析')

        # 恢复状态栏提示为可重试
        if hasattr(self, 'status_lbl'):
            self.status_lbl.setText('可重新进行智能分析')
            self.status_lbl.setStyleSheet(
                f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT}; "
                f"font-family:{Fonts.BODY};"
            )

    def _clear_error_holder(self):
        """移除当前错误态 holder（重建错误态时清理旧实例）。"""
        old = self._error_holder
        if old is not None:
            try:
                old.deleteLater()
            except Exception:
                pass
            self._error_holder = None

    def _set_error_holder(self, holder: QWidget):
        """设置错误态 holder（供上层/显示逻辑调用）。"""
        self._error_holder = holder

    def _list(self, items: list, color: str) -> QWidget:
        """智能分析列表项 - 增强版"""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(Spacing.S2, Spacing.S_PAD_SM, Spacing.S2, Spacing.S_PAD_SM)
        l.setSpacing(Spacing.S3)
        for idx, item in enumerate(items):
            row = QHBoxLayout()
            row.setSpacing(Spacing.S3)
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
        l.setContentsMargins(Spacing.S2, Spacing.S_PAD_SM, Spacing.S2, Spacing.S_PAD_SM)
        l.setSpacing(Spacing.S1)
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

        v5.x 关键修复：
        历史上有两条排盘数据路径：
        1. 旧结构：data['bazi'] 是 {'year_pillar','month_pillar','day_pillar','hour_pillar', ...} 嵌套字典
        2. Service 结构：BaziService.calculate 返回顶层摊平（year_pillar 等字段直接在顶层），
           且不含 'bazi' 与 'bazi_types' 键。

        若本方法只读 rd['bazi']（旧结构），Service 结构下会拿到 {} → chart_data['bazi']
        为空 → 上游 _trigger_bazi_auto_ai / _on_bazi_ai_analyze 的
        "chart_data.get('bazi', {}).get('year_pillar')" 门禁判定「排盘数据不完整」，
        直接 return，AI 分析永远不被触发。

        本方法按优先级读取：先 rd['bazi']，回退到顶层摊平字段，统一产出
        旧结构 shape（dict）给 AI。display_result 中「四柱卡片」也各自做了同型兜底，
        本方法是 AI 路径的唯一权威来源。
        """
        rd = getattr(self, '_current_result', None)
        if not rd or not isinstance(rd, dict):
            return {}

        # ---- 双路径兜底：优先读嵌套 bazi，回退到顶层摊平字段 ----
        bazi = rd.get('bazi') or {}
        if not bazi:
            bazi = {
                'year_pillar': rd.get('year_pillar', ''),
                'month_pillar': rd.get('month_pillar', ''),
                'day_pillar': rd.get('day_pillar', ''),
                'hour_pillar': rd.get('hour_pillar', ''),
                'rizhu': rd.get('rizhu', ''),
                'month_zhi': rd.get('month_zhi', ''),
                'hour_zhi': rd.get('hour_zhi', ''),
                'solar_date': rd.get('solar_date', ''),
                'lunar_date': rd.get('lunar_date', ''),
                'solar_time': rd.get('solar_time', ''),
                'original_time': rd.get('original_time', ''),
                'longitude': rd.get('longitude', 120.0),
            }
        bi = rd.get('basic_info') or {}

        # 双路径：wuxing 旧结构（计数）或 wuxing_detail（Service 结构）
        wuxing_for_ui = rd.get('wuxing') or {}
        wuxing_detail = rd.get('wuxing_detail') or {}
        # 旧结构：wuxing 已是 {wx: int}；Service 结构：wuxing_detail 是 {wx: {score, count, ...}}
        # 统一：优先用 wuxing_detail（带 strength 明细），否则用 wuxing
        if not wuxing_for_ui and wuxing_detail:
            wuxing_for_ui = {k: v.get('count', 0) if isinstance(v, dict) else v
                             for k, v in wuxing_detail.items() if k in ('木', '火', '土', '金', '水')}

        chart_data = {
            'bazi': bazi,
            'bazi_types': rd.get('bazi_types') or {},
            'wuxing': wuxing_for_ui,
            'wuxing_detail': wuxing_detail,
            'shishen': rd.get('shishen') or {},
            'mingli': rd.get('mingli') or {},
            'major_fortune': rd.get('dayun') or {},
            'liunian': rd.get('liunian') or {},
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
