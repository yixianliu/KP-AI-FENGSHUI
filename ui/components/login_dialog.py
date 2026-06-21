"""
用户登录注册对话框 - 极简轻量国风
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from ui.styles import Stylesheets, Colors, Fonts, Spacing
import hashlib


def _hash_password(password: str) -> str:
    """对密码进行SHA256哈希"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


class LoginDialog(QDialog):
    """登录对话框"""

    user_logged_in = Signal(int, str)  # user_id, username
    switch_to_register = Signal()

    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle('用户登录')
        self.setFixedSize(420, 360)
        self.setStyleSheet(f"background-color: {Colors.BG};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # 标题
        title = QLabel('☯ 用户登录')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_TITLE};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel('登录后可保存排盘记录')
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            color: {Colors.TEXT3};
            font-family: {Fonts.BODY};
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # 分割线
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {Colors.QINGHUA_LIGHT};")
        layout.addWidget(div)

        # 用户名
        layout.addWidget(self._form_label('用户名'))
        self.username_edit = QLineEdit()
        self.username_edit.setStyleSheet(Stylesheets.INPUT)
        self.username_edit.setPlaceholderText('请输入用户名')
        layout.addWidget(self.username_edit)

        # 密码
        layout.addWidget(self._form_label('密码'))
        self.password_edit = QLineEdit()
        self.password_edit.setStyleSheet(Stylesheets.INPUT)
        self.password_edit.setPlaceholderText('请输入密码')
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_edit)

        layout.addSpacing(8)

        # 登录按钮
        self.login_btn = QPushButton('登 录')
        self.login_btn.setStyleSheet(Stylesheets.BTN_PRIMARY)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setFixedHeight(44)
        self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn)

        # 切换到注册
        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignCenter)
        switch_label = QLabel('还没有账号？')
        switch_label.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
        self.switch_btn = QPushButton('立即注册')
        self.switch_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.QINGHUA};
                font-size: {Fonts.SZ_SMALL};
                font-family: {Fonts.BODY};
                text-decoration: underline;
                padding: 0;
            }}
            QPushButton:hover {{ color: {Colors.QINGHUA_LIGHT}; }}
        """)
        self.switch_btn.setCursor(Qt.PointingHandCursor)
        self.switch_btn.clicked.connect(self.switch_to_register.emit)
        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(self.switch_btn)
        layout.addLayout(switch_layout)

        layout.addStretch()

    def _form_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            color: {Colors.TEXT2};
            font-family: {Fonts.BODY};
        """)
        return label

    def _on_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            QMessageBox.warning(self, '输入错误', '请输入用户名和密码')
            return

        if self.db_manager:
            user = self.db_manager.verify_user(username, _hash_password(password))
            if user:
                self.user_logged_in.emit(user['id'], user['username'])
                self.accept()
            else:
                QMessageBox.warning(self, '登录失败', '用户名或密码错误')
        else:
            # 无数据库时模拟登录
            self.user_logged_in.emit(1, username)
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self._on_login()
        else:
            super().keyPressEvent(event)


class RegisterDialog(QDialog):
    """注册对话框"""

    user_registered = Signal(int, str)  # user_id, username
    switch_to_login = Signal()

    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle('用户注册')
        self.setFixedSize(420, 420)
        self.setStyleSheet(f"background-color: {Colors.BG};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # 标题
        title = QLabel('☯ 用户注册')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_TITLE};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel('创建账号以保存您的排盘记录')
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            color: {Colors.TEXT3};
            font-family: {Fonts.BODY};
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {Colors.QINGHUA_LIGHT};")
        layout.addWidget(div)

        # 用户名
        layout.addWidget(self._form_label('用户名'))
        self.username_edit = QLineEdit()
        self.username_edit.setStyleSheet(Stylesheets.INPUT)
        self.username_edit.setPlaceholderText('请输入用户名（3-20位字符）')
        layout.addWidget(self.username_edit)

        # 密码
        layout.addWidget(self._form_label('密码'))
        self.password_edit = QLineEdit()
        self.password_edit.setStyleSheet(Stylesheets.INPUT)
        self.password_edit.setPlaceholderText('请输入密码（至少6位）')
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_edit)

        # 确认密码
        layout.addWidget(self._form_label('确认密码'))
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setStyleSheet(Stylesheets.INPUT)
        self.confirm_edit.setPlaceholderText('请再次输入密码')
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.confirm_edit)

        layout.addSpacing(8)

        # 注册按钮
        self.register_btn = QPushButton('注 册')
        self.register_btn.setStyleSheet(Stylesheets.BTN_PRIMARY)
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.setFixedHeight(44)
        self.register_btn.clicked.connect(self._on_register)
        layout.addWidget(self.register_btn)

        # 切换到登录
        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignCenter)
        switch_label = QLabel('已有账号？')
        switch_label.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3}; font-family: {Fonts.BODY};")
        self.switch_btn = QPushButton('立即登录')
        self.switch_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.QINGHUA};
                font-size: {Fonts.SZ_SMALL};
                font-family: {Fonts.BODY};
                text-decoration: underline;
                padding: 0;
            }}
            QPushButton:hover {{ color: {Colors.QINGHUA_LIGHT}; }}
        """)
        self.switch_btn.setCursor(Qt.PointingHandCursor)
        self.switch_btn.clicked.connect(self.switch_to_login.emit)
        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(self.switch_btn)
        layout.addLayout(switch_layout)

        layout.addStretch()

    def _form_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"""
            font-size: {Fonts.SZ_SMALL};
            color: {Colors.TEXT2};
            font-family: {Fonts.BODY};
        """)
        return label

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

            user_id = self.db_manager.create_user(username, _hash_password(password))
            if user_id:
                self.user_registered.emit(user_id, username)
                QMessageBox.information(self, '注册成功', '账号注册成功，即将自动登录')
                self.accept()
            else:
                QMessageBox.warning(self, '注册失败', '注册失败，请稍后重试')
        else:
            # 无数据库时模拟注册
            self.user_registered.emit(1, username)
            QMessageBox.information(self, '注册成功', '账号注册成功，即将自动登录')
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self._on_register()
        else:
            super().keyPressEvent(event)
