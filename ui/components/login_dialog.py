"""
用户登录注册对话框 v5.0 - 精美国风 · 柔和动画 · 优雅交互
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QGraphicsDropShadowEffect, QWidget
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor
from ui.styles import Stylesheets, Colors, Fonts, Spacing


class LoginDialog(QDialog):
    """登录对话框 v5.0"""

    user_logged_in = Signal(int, str)  # user_id, username
    switch_to_register = Signal()

    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle('用户登录')
        self.setFixedSize(440, 480)
        self.setStyleSheet(f"background-color: {Colors.BG};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ===== 顶部装饰条 =====
        top_bar = QFrame()
        top_bar.setFixedHeight(120)
        top_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.QINGHUA_DARK}, stop:0.5 {Colors.QINGHUA}, stop:1 {Colors.QINGHUA_DARK});
                border: none;
            }}
        """)
        top_layout = QVBoxLayout(top_bar)
        top_layout.setAlignment(Qt.AlignCenter)
        top_layout.setSpacing(6)

        top_icon = QLabel('☯')
        top_icon.setStyleSheet(f"font-size: 32px; color: {Colors.TEXT_INV}; background: transparent;")
        top_icon.setAlignment(Qt.AlignCenter)

        top_title = QLabel('风水排盘')
        top_title.setStyleSheet(f"""
            font-size: {Fonts.SZ_HERO};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT_INV};
            font-family: {Fonts.TITLE};
            background: transparent;
            letter-spacing: 4px;
        """)
        top_title.setAlignment(Qt.AlignCenter)

        top_sub = QLabel('登录以保存您的排盘记录')
        top_sub.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            color: rgba(255,255,255,0.75);
            font-family: {Fonts.BODY};
            background: transparent;
        """)
        top_sub.setAlignment(Qt.AlignCenter)

        top_layout.addWidget(top_icon)
        top_layout.addWidget(top_title)
        top_layout.addWidget(top_sub)
        layout.addWidget(top_bar)

        # ===== 内容区 =====
        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.CARD};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 32, 40, 24)
        content_layout.setSpacing(16)

        # 用户名
        username_label = QLabel('👤 用户名')
        username_label.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT2};
            font-family: {Fonts.BODY};
            margin-top: 4px;
        """)
        content_layout.addWidget(username_label)

        self.username_edit = QLineEdit()
        self.username_edit.setStyleSheet(Stylesheets.INPUT)
        self.username_edit.setPlaceholderText('请输入用户名')
        self.username_edit.setFixedHeight(42)
        content_layout.addWidget(self.username_edit)

        # 密码
        password_label = QLabel('🔒 密码')
        password_label.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT2};
            font-family: {Fonts.BODY};
            margin-top: 4px;
        """)
        content_layout.addWidget(password_label)

        self.password_edit = QLineEdit()
        self.password_edit.setStyleSheet(Stylesheets.INPUT)
        self.password_edit.setPlaceholderText('请输入密码')
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setFixedHeight(42)
        content_layout.addWidget(self.password_edit)

        content_layout.addSpacing(8)

        # 登录按钮（带阴影）
        self.login_btn = QPushButton('登 录')
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.ZHUSHA}, stop:1 {Colors.ZHUSHA_DARK});
                color: {Colors.TEXT_INV};
                border: none;
                border-radius: {Spacing.RADIUS_SM};
                font-size: 15px;
                font-weight: {Fonts.W_MEDIUM};
                font-family: {Fonts.BODY};
                padding: 12px 0;
                letter-spacing: 8px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.ZHUSHA_DARK}, stop:1 {Colors.ZHUSHA_DARK});
            }}
            QPushButton:pressed {{
                background: {Colors.ZHUSHA_DARK};
            }}
            QPushButton:disabled {{
                background: {Colors.BORDER};
                color: {Colors.TEXT3};
            }}
        """)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setFixedHeight(46)
        self.login_btn.clicked.connect(self._on_login)

        # 按钮阴影
        btn_shadow = QGraphicsDropShadowEffect()
        btn_shadow.setBlurRadius(12)
        btn_shadow.setOffset(0, 3)
        btn_shadow.setColor(QColor(196, 85, 69, 80))
        self.login_btn.setGraphicsEffect(btn_shadow)

        content_layout.addWidget(self.login_btn)

        content_layout.addSpacing(8)

        # 切换到注册
        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignCenter)
        switch_layout.setSpacing(4)
        switch_label = QLabel('还没有账号？')
        switch_label.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
        self.switch_btn = QPushButton('立即注册')
        self.switch_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.QINGHUA};
                font-size: {Fonts.SZ_SMALL};
                font-weight: {Fonts.W_MEDIUM};
                font-family: {Fonts.BODY};
                text-decoration: underline;
                padding: 0;
            }}
            QPushButton:hover {{ color: {Colors.QINGHUA_DARK}; }}
        """)
        self.switch_btn.setCursor(Qt.PointingHandCursor)
        self.switch_btn.clicked.connect(self.switch_to_register.emit)
        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(self.switch_btn)
        content_layout.addLayout(switch_layout)

        layout.addWidget(content, 1)

        # ===== 底部提示 =====
        bottom_hint = QLabel('支持离线排盘 · 数据安全加密存储')
        bottom_hint.setStyleSheet(f"""
            font-size: 10px;
            color: {Colors.TEXT4};
            font-family: {Fonts.BODY};
            padding: 8px 0;
            background: transparent;
        """)
        bottom_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(bottom_hint)

    def _on_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            QMessageBox.warning(self, '输入错误', '请输入用户名和密码')
            return

        if self.db_manager:
            user = self.db_manager.verify_user(username, password)
            if user:
                self.user_logged_in.emit(user['id'], user['username'])
                self.accept()
            else:
                QMessageBox.warning(self, '登录失败', '用户名或密码错误')
        else:
            # DB 不可用时明确报错，禁止"模拟登录"绕过（P2-2 用户体系加固）
            QMessageBox.critical(
                self, '登录不可用',
                '数据库未就绪，无法完成登录。\n\n'
                '排盘数据仍可正常使用，但保存历史记录需要先登录。\n'
                '请检查程序是否被授予 data/ 目录的写入权限。'
            )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self._on_login()
        else:
            super().keyPressEvent(event)


class RegisterDialog(QDialog):
    """注册对话框 v5.0"""

    user_registered = Signal(int, str)  # user_id, username
    switch_to_login = Signal()

    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle('用户注册')
        self.setFixedSize(440, 540)
        self.setStyleSheet(f"background-color: {Colors.BG};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ===== 顶部装饰条 =====
        top_bar = QFrame()
        top_bar.setFixedHeight(120)
        top_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.LIUJIN_DARK}, stop:0.5 {Colors.LIUJIN}, stop:1 {Colors.LIUJIN_DARK});
                border: none;
            }}
        """)
        top_layout = QVBoxLayout(top_bar)
        top_layout.setAlignment(Qt.AlignCenter)
        top_layout.setSpacing(6)

        top_icon = QLabel('☯')
        top_icon.setStyleSheet(f"font-size: 32px; color: {Colors.TEXT_INV}; background: transparent;")
        top_icon.setAlignment(Qt.AlignCenter)

        top_title = QLabel('创建账号')
        top_title.setStyleSheet(f"""
            font-size: {Fonts.SZ_HERO};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT_INV};
            font-family: {Fonts.TITLE};
            background: transparent;
            letter-spacing: 4px;
        """)
        top_title.setAlignment(Qt.AlignCenter)

        top_sub = QLabel('注册后即可保存排盘记录')
        top_sub.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            color: rgba(255,255,255,0.75);
            font-family: {Fonts.BODY};
            background: transparent;
        """)
        top_sub.setAlignment(Qt.AlignCenter)

        top_layout.addWidget(top_icon)
        top_layout.addWidget(top_title)
        top_layout.addWidget(top_sub)
        layout.addWidget(top_bar)

        # ===== 内容区 =====
        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.CARD};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 32, 40, 24)
        content_layout.setSpacing(14)

        # 用户名
        username_label = QLabel('👤 用户名')
        username_label.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT2};
            font-family: {Fonts.BODY};
            margin-top: 4px;
        """)
        content_layout.addWidget(username_label)

        self.username_edit = QLineEdit()
        self.username_edit.setStyleSheet(Stylesheets.INPUT)
        self.username_edit.setPlaceholderText('请输入用户名（3-20位字符）')
        self.username_edit.setFixedHeight(42)
        content_layout.addWidget(self.username_edit)

        # 密码
        password_label = QLabel('🔒 密码')
        password_label.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT2};
            font-family: {Fonts.BODY};
            margin-top: 4px;
        """)
        content_layout.addWidget(password_label)

        self.password_edit = QLineEdit()
        self.password_edit.setStyleSheet(Stylesheets.INPUT)
        self.password_edit.setPlaceholderText('请输入密码（至少6位）')
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setFixedHeight(42)
        content_layout.addWidget(self.password_edit)

        # 确认密码
        confirm_label = QLabel('🔒 确认密码')
        confirm_label.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT2};
            font-family: {Fonts.BODY};
            margin-top: 4px;
        """)
        content_layout.addWidget(confirm_label)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setStyleSheet(Stylesheets.INPUT)
        self.confirm_edit.setPlaceholderText('请再次输入密码')
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit.setFixedHeight(42)
        content_layout.addWidget(self.confirm_edit)

        content_layout.addSpacing(8)

        # 注册按钮（带阴影）
        self.register_btn = QPushButton('注 册')
        self.register_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.LIUJIN}, stop:1 {Colors.LIUJIN_DARK});
                color: {Colors.TEXT_INV};
                border: none;
                border-radius: {Spacing.RADIUS_SM};
                font-size: 15px;
                font-weight: {Fonts.W_MEDIUM};
                font-family: {Fonts.BODY};
                padding: 12px 0;
                letter-spacing: 8px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.LIUJIN_DARK}, stop:1 {Colors.LIUJIN_DARK});
            }}
            QPushButton:pressed {{
                background: {Colors.LIUJIN_DARK};
            }}
            QPushButton:disabled {{
                background: {Colors.BORDER};
                color: {Colors.TEXT3};
            }}
        """)
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.setFixedHeight(46)
        self.register_btn.clicked.connect(self._on_register)

        # 按钮阴影
        btn_shadow = QGraphicsDropShadowEffect()
        btn_shadow.setBlurRadius(12)
        btn_shadow.setOffset(0, 3)
        btn_shadow.setColor(QColor(184, 138, 48, 80))
        self.register_btn.setGraphicsEffect(btn_shadow)

        content_layout.addWidget(self.register_btn)

        content_layout.addSpacing(8)

        # 切换到登录
        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignCenter)
        switch_layout.setSpacing(4)
        switch_label = QLabel('已有账号？')
        switch_label.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
        self.switch_btn = QPushButton('立即登录')
        self.switch_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.QINGHUA};
                font-size: {Fonts.SZ_SMALL};
                font-weight: {Fonts.W_MEDIUM};
                font-family: {Fonts.BODY};
                text-decoration: underline;
                padding: 0;
            }}
            QPushButton:hover {{ color: {Colors.QINGHUA_DARK}; }}
        """)
        self.switch_btn.setCursor(Qt.PointingHandCursor)
        self.switch_btn.clicked.connect(self.switch_to_login.emit)
        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(self.switch_btn)
        content_layout.addLayout(switch_layout)

        layout.addWidget(content, 1)

        # ===== 底部提示 =====
        bottom_hint = QLabel('支持离线排盘 · 数据安全加密存储')
        bottom_hint.setStyleSheet(f"""
            font-size: 10px;
            color: {Colors.TEXT4};
            font-family: {Fonts.BODY};
            padding: 8px 0;
            background: transparent;
        """)
        bottom_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(bottom_hint)

    def _on_register(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        confirm = self.confirm_edit.text().strip()

        if not username or not password:
            QMessageBox.warning(self, '输入错误', '用户名和密码不能为空')
            return

        if len(username) < 3 or len(username) > 20:
            QMessageBox.warning(self, '输入错误', '用户名长度应为3-20位')
            return

        if len(password) < 6:
            QMessageBox.warning(self, '输入错误', '密码长度至少为6位')
            return

        if password != confirm:
            QMessageBox.warning(self, '输入错误', '两次输入的密码不一致')
            return

        if self.db_manager:
            # 检查用户名是否已存在
            existing = self.db_manager.get_user_by_username(username)
            if existing:
                QMessageBox.warning(self, '注册失败', '该用户名已被注册')
                return

            user_id = self.db_manager.create_user(username, password)
            if user_id:
                self.user_registered.emit(user_id, username)
                QMessageBox.information(self, '注册成功', '账号注册成功，即将自动登录')
                self.accept()
            else:
                QMessageBox.warning(self, '注册失败', '注册失败，请稍后重试')
        else:
            # DB 不可用时明确报错，禁止"模拟注册"绕过（P2-2 用户体系加固）
            QMessageBox.critical(
                self, '注册不可用',
                '数据库未就绪，无法完成注册。\n\n'
                '排盘数据仍可正常使用，但保存历史记录需要先注册。\n'
                '请检查程序是否被授予 data/ 目录的写入权限。'
            )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self._on_register()
        else:
            super().keyPressEvent(event)
