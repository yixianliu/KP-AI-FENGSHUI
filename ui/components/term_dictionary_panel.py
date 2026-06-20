"""
专业术语词典查询面板
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                             QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, Signal
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from core.term_explainer import TermExplainer


class TermDictionaryPanel(QWidget):
    """专业术语词典查询面板"""

    term_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.term_explainer = TermExplainer()
        self.current_category = 'all'
        self.init_ui()
        self.load_hot_terms()
        self.load_all_categories()

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

        # ===== 顶部标题栏 =====
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title_icon = QLabel('📖')
        title_icon.setStyleSheet("font-size: 22px;")

        title_label = QLabel('专业术语词典')
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_TITLE};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_SERIF};
            letter-spacing: 2px;
        """)

        header_layout.addWidget(title_icon)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # 鎏金分割线
        gold_divider = QFrame()
        gold_divider.setFixedHeight(2)
        gold_divider.setStyleSheet(Stylesheets.GOLD_DIVIDER)
        main_layout.addWidget(gold_divider)

        # ===== 搜索区域 =====
        search_card = QFrame()
        search_card.setStyleSheet(Stylesheets.SECTION_CARD)
        search_layout = QVBoxLayout(search_card)
        search_layout.setContentsMargins(16, 14, 16, 14)
        search_layout.setSpacing(12)

        search_header = QHBoxLayout()
        search_icon = QLabel('🔍')
        search_icon.setStyleSheet("font-size: 18px;")
        search_title = QLabel('术语搜索')
        search_title.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SECTION};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        search_header.addWidget(search_icon)
        search_header.addWidget(search_title)
        search_header.addStretch()
        search_layout.addLayout(search_header)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setStyleSheet(Stylesheets.LINE_EDIT)
        self.search_input.setPlaceholderText('输入术语名称或关键词搜索...')
        self.search_input.setMinimumHeight(40)

        self.search_btn = QPushButton('搜索')
        self.search_btn.setStyleSheet(Stylesheets.BUTTON_PRIMARY)
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.setMinimumWidth(80)

        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.search_btn)
        search_layout.addLayout(search_row)

        main_layout.addWidget(search_card)

        # ===== 内容区域（三栏布局） =====
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # 左侧：分类列表
        self.category_list = QListWidget()
        self.category_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 8px;
                font-size: {Fonts.SIZE_BODY};
                font-family: {Fonts.FAMILY_CN};
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: 6px;
                margin: 2px 0;
            }}
            QListWidget::item:hover {{
                background-color: {Colors.HOVER_BG};
            }}
            QListWidget::item:selected {{
                background-color: {Colors.PRIMARY};
                color: white;
            }}
        """)
        self.category_list.setFixedWidth(200)
        content_layout.addWidget(self.category_list)

        # 中间：术语列表
        self.term_list = QListWidget()
        self.term_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CONTROL_RADIUS};
                padding: 8px;
                font-size: {Fonts.SIZE_BODY};
                font-family: {Fonts.FAMILY_CN};
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: 6px;
                margin: 2px 0;
            }}
            QListWidget::item:hover {{
                background-color: {Colors.HOVER_BG};
            }}
            QListWidget::item:selected {{
                background-color: {Colors.ACCENT};
                color: white;
            }}
        """)
        self.term_list.setFixedWidth(240)
        content_layout.addWidget(self.term_list)

        # 右侧：术语详情
        self.detail_area = QScrollArea()
        self.detail_area.setStyleSheet(Stylesheets.SCROLL_AREA)
        self.detail_area.setWidgetResizable(True)
        self.detail_area.setFrameShape(QFrame.NoFrame)

        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_layout.setSpacing(16)

        self._show_detail_placeholder()
        self.detail_area.setWidget(self.detail_widget)
        content_layout.addWidget(self.detail_area, 1)

        main_layout.addLayout(content_layout, 1)

        # ===== 热门术语 =====
        hot_card = QFrame()
        hot_card.setStyleSheet(Stylesheets.SECTION_CARD)
        hot_layout = QVBoxLayout(hot_card)
        hot_layout.setContentsMargins(16, 14, 16, 14)
        hot_layout.setSpacing(10)

        hot_header = QHBoxLayout()
        hot_icon = QLabel('🔥')
        hot_icon.setStyleSheet("font-size: 16px;")
        hot_title = QLabel('热门术语')
        hot_title.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SECTION};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        hot_header.addWidget(hot_icon)
        hot_header.addWidget(hot_title)
        hot_header.addStretch()
        hot_layout.addLayout(hot_header)

        self.hot_terms_layout = QHBoxLayout()
        self.hot_terms_layout.setSpacing(8)
        hot_layout.addLayout(self.hot_terms_layout)

        main_layout.addWidget(hot_card)

        self.setLayout(main_layout)

        # 连接信号
        self.search_btn.clicked.connect(self.on_search)
        self.search_input.returnPressed.connect(self.on_search)
        self.category_list.currentRowChanged.connect(self.on_category_changed)
        self.term_list.itemClicked.connect(self.on_term_clicked)

    def load_all_categories(self):
        """加载所有分类"""
        self.category_list.clear()
        categories = self.term_explainer.get_all_categories()

        all_item = QListWidgetItem('📚 全部术语')
        all_item.setData(Qt.UserRole, 'all')
        self.category_list.addItem(all_item)

        for cat in categories:
            terms = self.term_explainer.get_terms_by_category(cat)
            count = len(terms)
            item = QListWidgetItem(f'{cat} ({count})')
            item.setData(Qt.UserRole, cat)
            self.category_list.addItem(item)

        self.category_list.setCurrentRow(0)
        self.load_terms_by_category('all')

    def load_hot_terms(self):
        """加载热门术语"""
        hot_terms = self.term_explainer.get_hot_terms()
        for i in reversed(range(self.hot_terms_layout.count())):
            item = self.hot_terms_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        for term in hot_terms[:8]:
            term_name = term.get('name', str(term))
            btn = QPushButton(term_name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BACKGROUND};
                    color: {Colors.TEXT_SECONDARY};
                    border: 1px solid {Colors.BORDER};
                    border-radius: 16px;
                    padding: 6px 14px;
                    font-size: {Fonts.SIZE_SMALL};
                    font-family: {Fonts.FAMILY_CN};
                }}
                QPushButton:hover {{
                    border-color: {Colors.HIGHLIGHT};
                    color: {Colors.HIGHLIGHT};
                    background-color: {Colors.HIGHLIGHT_GLOW};
                }}
            """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, t=term_name: self.show_term_detail(t))
            self.hot_terms_layout.addWidget(btn)

        self.hot_terms_layout.addStretch()

    def load_terms_by_category(self, category):
        """按分类加载术语列表"""
        self.term_list.clear()
        terms = self.term_explainer.get_terms_by_category(category)

        for term_info in terms:
            term_name = term_info.get('name', '')
            brief = term_info.get('brief', '')
            item = QListWidgetItem(f'{term_name} - {brief[:20]}...' if len(brief) > 20 else f'{term_name} - {brief}')
            item.setData(Qt.UserRole, term_name)
            self.term_list.addItem(item)

    def on_category_changed(self, row):
        """分类切换"""
        if row < 0:
            return
        item = self.category_list.item(row)
        category = item.data(Qt.UserRole)
        self.current_category = category
        self.load_terms_by_category(category)

    def on_search(self):
        """搜索术语"""
        keyword = self.search_input.text().strip()
        self.term_list.clear()

        results = self.term_explainer.search(keyword)

        for term_info in results:
            term_name = term_info.get('name', '')
            brief = term_info.get('brief', '')
            display_text = f'{term_name} - {brief[:20]}...' if len(brief) > 20 else f'{term_name} - {brief}'
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, term_name)
            self.term_list.addItem(item)

        if results:
            self.term_list.setCurrentRow(0)
            self.show_term_detail(results[0].get('name', ''))

    def on_term_clicked(self, item):
        """术语点击"""
        term_name = item.data(Qt.UserRole)
        self.show_term_detail(term_name)
        self.term_clicked.emit(term_name)

    def show_term_detail(self, term_name):
        """显示术语详情"""
        detail = self.term_explainer.get_term_detail(term_name)
        if not detail:
            return

        details = detail.get('details', {})

        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        name_card = QFrame()
        name_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CARD_RADIUS};
            }}
        """)
        name_layout = QVBoxLayout(name_card)
        name_layout.setContentsMargins(20, 16, 20, 16)
        name_layout.setSpacing(8)

        term_type = details.get('type', 'neutral')
        type_colors = {
            'positive': Colors.SUCCESS,
            'negative': Colors.DANGER,
            'neutral': Colors.INFO,
        }
        type_names = {
            'positive': '吉神',
            'negative': '凶煞',
            'neutral': '中性',
        }
        type_color = type_colors.get(term_type, Colors.INFO)
        type_name = type_names.get(term_type, term_type)

        name_header = QHBoxLayout()
        name_label = QLabel(term_name)
        name_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_SERIF};
            letter-spacing: 2px;
        """)

        type_badge = QLabel(type_name)
        type_badge.setStyleSheet(f"""
            background-color: {type_color};
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: {Fonts.SIZE_SMALL};
            font-weight: {Fonts.WEIGHT_BOLD};
            font-family: {Fonts.FAMILY_CN};
        """)

        category_label = QLabel(detail.get('category', ''))
        category_label.setStyleSheet(f"""
            color: {Colors.TEXT_TERTIARY};
            font-size: {Fonts.SIZE_SMALL};
            font-family: {Fonts.FAMILY_CN};
        """)

        name_header.addWidget(name_label)
        name_header.addSpacing(12)
        name_header.addWidget(type_badge)
        name_header.addStretch()
        name_header.addWidget(category_label)
        name_layout.addLayout(name_header)

        brief = detail.get('brief', '')
        if brief:
            brief_label = QLabel(brief)
            brief_label.setStyleSheet(f"""
                font-size: {Fonts.SIZE_BODY};
                color: {Colors.TEXT_SECONDARY};
                font-family: {Fonts.FAMILY_CN};
                line-height: 1.6;
            """)
            brief_label.setWordWrap(True)
            name_layout.addWidget(brief_label)

        self.detail_layout.addWidget(name_card)

        description = detail.get('description', '')
        if description:
            desc_card = self._create_detail_card('📝 详细解释', description)
            self.detail_layout.addWidget(desc_card)

        check_method = details.get('check_method', '')
        if check_method:
            check_card = self._create_detail_card('🔍 查法', check_method)
            self.detail_layout.addWidget(check_card)

        influence = details.get('influence', [])
        if influence:
            influence_text = '、'.join(influence)
            inf_card = self._create_detail_card('✨ 主要影响', influence_text)
            self.detail_layout.addWidget(inf_card)

        related = details.get('related_terms', [])
        if not related:
            related = detail.get('related_terms', [])
        if not related:
            related_details = detail.get('related_details', [])
            related = [rd.get('name', '') for rd in related_details if rd.get('name')]

        if related:
            rel_widget = QWidget()
            rel_layout = QVBoxLayout(rel_widget)
            rel_layout.setContentsMargins(0, 0, 0, 0)
            rel_layout.setSpacing(8)

            rel_title = QLabel('🔗 相关术语')
            rel_title.setStyleSheet(f"""
                font-size: {Fonts.SIZE_SECTION};
                font-weight: {Fonts.WEIGHT_BOLD};
                color: {Colors.PRIMARY};
                font-family: {Fonts.FAMILY_CN};
            """)
            rel_layout.addWidget(rel_title)

            rel_btns = QHBoxLayout()
            rel_btns.setSpacing(8)
            for rel_term in related[:8]:
                btn = QPushButton(rel_term)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Colors.HIGHLIGHT_GLOW};
                        color: {Colors.ACCENT};
                        border: 1px solid {Colors.HIGHLIGHT};
                        border-radius: 12px;
                        padding: 4px 12px;
                        font-size: {Fonts.SIZE_SMALL};
                        font-family: {Fonts.FAMILY_CN};
                    }}
                    QPushButton:hover {{
                        background-color: {Colors.HIGHLIGHT};
                        color: white;
                    }}
                """)
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(lambda checked, t=rel_term: self.show_term_detail(t))
                rel_btns.addWidget(btn)
            rel_btns.addStretch()
            rel_layout.addLayout(rel_btns)

            rel_card = QFrame()
            rel_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.CARD};
                    border: 1px solid {Colors.BORDER_LIGHT};
                    border-radius: {Spacing.CARD_RADIUS};
                    padding: 16px;
                }}
            """)
            rel_card_layout = QVBoxLayout(rel_card)
            rel_card_layout.setContentsMargins(16, 14, 16, 14)
            rel_card_layout.addWidget(rel_widget)
            self.detail_layout.addWidget(rel_card)

        self.detail_layout.addStretch()

    def _create_detail_card(self, title, content):
        """创建详情卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Spacing.CARD_RADIUS};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_SECTION};
            font-weight: {Fonts.WEIGHT_BOLD};
            color: {Colors.PRIMARY};
            font-family: {Fonts.FAMILY_CN};
        """)

        content_label = QLabel(content)
        content_label.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.FAMILY_CN};
            line-height: 1.8;
        """)
        content_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(content_label)

        return card

    def _show_detail_placeholder(self):
        """显示详情占位符"""
        placeholder = QWidget()
        ph_layout = QVBoxLayout(placeholder)
        ph_layout.setAlignment(Qt.AlignCenter)
        ph_layout.setSpacing(16)

        icon = QLabel('📖')
        icon.setStyleSheet(f"font-size: 64px; color: {Colors.BORDER}; opacity: 0.5;")
        icon.setAlignment(Qt.AlignCenter)

        title = QLabel('选择术语查看详情')
        title.setStyleSheet(f"""
            font-size: 18px;
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
        """)
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel('从左侧列表选择术语，或使用搜索功能查找')
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.SIZE_BODY};
            color: {Colors.TEXT_TERTIARY};
            font-family: {Fonts.FAMILY_CN};
            opacity: 0.7;
        """)
        subtitle.setAlignment(Qt.AlignCenter)

        ph_layout.addStretch()
        ph_layout.addWidget(icon)
        ph_layout.addWidget(title)
        ph_layout.addWidget(subtitle)
        ph_layout.addStretch()

        placeholder.setMinimumHeight(400)
        self.detail_layout.addWidget(placeholder)
