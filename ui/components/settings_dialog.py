# -*- coding: utf-8 -*-
"""
ui/components/settings_dialog.py — AI 模型配置（GUI，极简版）

【定位】
程序仅接入一个固定的官方后端「龙虎山大师兄 AI（Agnes AI）」，
端点与模型名已固化为产品常量（core.ai_config.OFFICIAL_AGNES_*），
GUI 不再提供任何模型选择 / 端点 / 参数配置项。

用户在此只需填写自己的 API 密钥即可；保存即热生效，无需重启。

【安全说明】
  - 程序本体不含任何密钥；密钥由用户填写，落盘时按设备指纹混淆存储。
  - 官方端点 / 模型名为公开、非机密的产品常量，随包分发属正常。
"""
from __future__ import annotations

import logging

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QLineEdit, QMessageBox, QWidget,
                               QFrame)
from PySide6.QtCore import Qt, QThread, Signal

from ui.styles import Colors, Fonts, Spacing
from core.ai_config import (AIProfile, OFFICIAL_AGNES_ENDPOINT,
                            OFFICIAL_AGNES_MODEL, get_config_manager,
                            make_default_profile)

logger = logging.getLogger(__name__)


# ================================================================
# 连接测试后台线程（避免长超时把界面卡死）
# ================================================================
class _ConnectionTestWorker(QThread):
    """用给定配置档发一次最小请求，验证密钥是否可用。"""

    finished_ok = Signal(str)     # 返回内容片段
    finished_err = Signal(str)    # 错误描述

    def __init__(self, profile: AIProfile, parent=None):
        """初始化连接测试后台线程。

        Args:
            profile: 待测试的 AI 配置档（含端点、模型、密钥）。
            parent: 父对象。
        """
        super().__init__(parent)
        self._profile = profile

    def run(self):
        """线程入口：用最小请求验证密钥可用性，结果通过信号回传主线程。"""
        try:
            from api.agnes_client import AgnesClient
            client = AgnesClient(profile=self._profile)
            resp = client.chat_completion(
                [{"role": "user", "content": "你好"}],
                temperature=0.0, max_tokens=8,
            )
            self.finished_ok.emit((resp.get('content') or '').strip()[:60])
        except Exception as e:
            # 异常文本来自客户端与上游，已确保不含凭据信息
            self.finished_err.emit(str(e))


# ================================================================
# 主对话框（极简：仅填写 API 密钥）
# ================================================================
class SettingsDialog(QDialog):
    """龙虎山大师兄配置对话框（极简版）。"""

    def __init__(self, parent=None):
        """初始化极简配置对话框：固定官方后端，仅向用户索取 API 密钥。

        端点与模型在构造时即锁定为 core.ai_config 中的官方常量
        OFFICIAL_AGNES_ENDPOINT / OFFICIAL_AGNES_MODEL，GUI 不暴露多模型与
        端点配置项——这是刻意移除的取舍，密钥由用户填写并经设备指纹混淆落盘。

        Args:
            parent: 父窗口（可选）。
        """
        super().__init__(parent)
        self.setWindowTitle('设置 · 龙虎山大师兄配置')
        self.setMinimumSize(520, 430)

        self._manager = get_config_manager()
        self._test_worker = None

        # 单一固定配置档：官方后端，用户只填密钥
        active = self._manager.get_active()
        self._draft = active if active is not None else make_default_profile()
        # 固定字段锁定为官方后端，确保不会被旧草稿 / 外部编辑意外改写
        self._draft.provider = 'agnes'
        self._draft.api_url = OFFICIAL_AGNES_ENDPOINT
        self._draft.model = OFFICIAL_AGNES_MODEL
        self._draft.auth_scheme = 'bearer'
        self._draft.send_no_think = True

        self._build_ui()
        self._refresh_status()

    # ============================================================
    # 布局构建
    # ============================================================
    def _build_ui(self):
        """构建对话框布局：标题 / 说明 / 状态横幅 / 只读后端信息卡 / 密钥输入 / 按钮。"""
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        title = QLabel('龙虎山大师兄配置')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_TITLE};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
            letter-spacing: 1px;
        """)
        root.addWidget(title)

        desc = QLabel(
            '本程序使用龙虎山大师兄 AI 服务（Agnes AI）。请填写你的 API 密钥；'
            '密钥仅保存在本机，并按设备指纹混淆存储。'
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3};")
        root.addWidget(desc)

        # 状态横幅
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(38)
        root.addWidget(self.status_label)

        # 官方后端信息卡（只读展示，非配置项）
        info = QFrame()
        info.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER2};
                border-radius: {Spacing.RADIUS_SM};
            }}
        """)
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(14, 12, 14, 12)
        info_layout.setSpacing(6)
        info_layout.addWidget(self._label('服务：龙虎山大师兄 AI（Agnes AI）'))
        info_layout.addWidget(self._label(f'端点：{OFFICIAL_AGNES_ENDPOINT}'))
        info_layout.addWidget(self._label(f'模型：{OFFICIAL_AGNES_MODEL}'))
        root.addWidget(info)

        # 密钥输入行：输入框 + 显示 / 隐藏
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setPlaceholderText('sk-... （仅保存在本机）')
        self.key_edit.setToolTip('认证密钥（API Key）；仅保存在本机并按设备指纹混淆，不会被上传')
        self.key_edit.setStyleSheet(self._input_style())
        self.key_edit.setText(self._draft.api_key)
        self.key_edit.textChanged.connect(self._on_key_changed)

        key_row = QWidget()
        key_layout = QHBoxLayout(key_row)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.setSpacing(6)
        key_layout.addWidget(self.key_edit, 1)

        self.key_toggle = QPushButton('显示')
        self.key_toggle.setCheckable(True)
        self.key_toggle.setCursor(Qt.PointingHandCursor)
        self.key_toggle.setFixedWidth(54)
        self.key_toggle.setMinimumHeight(36)
        self.key_toggle.setToolTip('临时显示 / 隐藏密钥明文')
        self.key_toggle.setStyleSheet(
            self._btn_style(Colors.TEXT2, Colors.BORDER, Colors.HOVER))
        self.key_toggle.toggled.connect(self._on_toggle_key_visible)
        key_layout.addWidget(self.key_toggle)

        root.addWidget(self._label('API 密钥'))
        root.addWidget(key_row)

        root.addStretch()

        # 按钮
        btns = QHBoxLayout()
        self.test_btn = QPushButton('测试连接')
        self.test_btn.setCursor(Qt.PointingHandCursor)
        self.test_btn.setMinimumHeight(38)
        self.test_btn.setStyleSheet(
            self._btn_style(Colors.QINGHUA, Colors.QINGHUA_LIGHT, Colors.QINGHUA_GLOW))
        self.test_btn.clicked.connect(self._on_test)
        btns.addWidget(self.test_btn)
        btns.addStretch()

        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setMinimumHeight(38)
        self.cancel_btn.setStyleSheet(
            self._btn_style(Colors.TEXT2, Colors.BORDER, Colors.HOVER))
        self.cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.cancel_btn)

        self.save_btn = QPushButton('保存并应用')
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setMinimumHeight(38)
        self.save_btn.setStyleSheet(
            self._btn_style(Colors.ZHUSHA, Colors.ZHUSHA_LIGHT, Colors.ZHUSHA_GLOW))
        self.save_btn.clicked.connect(self._on_save)
        btns.addWidget(self.save_btn)
        root.addLayout(btns)

    # ============================================================
    # 状态刷新
    # ============================================================
    def _refresh_status(self, override: str = '', level: str = ''):
        """刷新状态横幅。level: ok / warn / err，留空则按当前草稿自动判定。"""
        if override:
            text, lv = override, (level or 'ok')
        else:
            err = self._draft.validate()
            if err:
                text, lv = f'配置未完成：{err}', 'warn'
            else:
                text, lv = '配置完整，已就绪。', 'ok'

        palette = {
            'ok':   (Colors.SUCCESS, Colors.SUCCESS_LIGHT),
            'warn': (Colors.WARNING, Colors.WARNING_LIGHT),
            'err':  (Colors.DANGER, Colors.DANGER_LIGHT),
        }
        fg, bg = palette.get(lv, palette['warn'])
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {fg};
                border: 1px solid {fg};
                border-radius: {Spacing.RADIUS_SM};
                padding: 8px 12px;
                font-size: {Fonts.SZ_SMALL};
            }}
        """)

    # ============================================================
    # 事件
    # ============================================================
    def _on_key_changed(self, *_):
        """由密钥输入框 textChanged 触发：同步草稿密钥并刷新状态横幅。"""
        self._draft.api_key = self.key_edit.text().strip()
        self._refresh_status()

    def _on_toggle_key_visible(self, shown: bool):
        """由「显示」按钮 toggled 触发：切换密钥明文/密文显示。"""
        self.key_edit.setEchoMode(QLineEdit.Normal if shown else QLineEdit.Password)
        self.key_toggle.setText('隐藏' if shown else '显示')

    # ---------- 测试连接 ----------
    def _on_test(self):
        """由「测试连接」按钮 clicked 触发：校验后启动后台连接测试线程。"""
        self._draft.api_key = self.key_edit.text().strip()
        err = self._draft.validate()
        if err:
            QMessageBox.warning(self, '配置不完整', err)
            return

        self.test_btn.setEnabled(False)
        self.test_btn.setText('测试中…')
        self._refresh_status('正在连接，请稍候…', 'warn')

        self._test_worker = _ConnectionTestWorker(self._draft.clone(), self)
        self._test_worker.finished_ok.connect(self._on_test_ok)
        self._test_worker.finished_err.connect(self._on_test_err)
        self._test_worker.finished.connect(self._on_test_done)
        self._test_worker.start()

    def _on_test_ok(self, snippet: str):
        """由测试线程 finished_ok 触发：展示连接成功提示与模型返回片段。"""
        self._refresh_status(f'连接成功，模型已响应：{snippet or "（空回复）"}', 'ok')
        QMessageBox.information(
            self, '连接测试',
            f'连接成功！\n模型: {OFFICIAL_AGNES_MODEL}\n返回: {snippet}'
        )

    def _on_test_err(self, message: str):
        """由测试线程 finished_err 触发：展示连接失败原因并提示排查。"""
        self._refresh_status(f'连接失败：{message}', 'err')
        QMessageBox.warning(
            self, '连接测试',
            f'连接失败：{message}\n\n请检查 API 密钥与网络后重试。'
        )

    def _on_test_done(self):
        """由测试线程 finished 触发：复位测试按钮状态并释放后台线程引用。"""
        self.test_btn.setEnabled(True)
        self.test_btn.setText('测试连接')
        self._test_worker = None

    # ---------- 保存 ----------
    def _on_save(self):
        """由「保存并应用」按钮 clicked 触发：校验后整体替换配置档并即时生效。"""
        self._draft.api_key = self.key_edit.text().strip()
        err = self._draft.validate()
        if err:
            QMessageBox.warning(self, '配置不完整', err)
            return
        # 单一固定配置档：整体替换，清掉旧版本可能遗留的多余配置档
        if not self._manager.replace_all([self._draft], self._draft.id):
            QMessageBox.critical(
                self, '保存失败', '配置写入失败，请检查程序目录的磁盘写入权限。')
            return
        QMessageBox.information(self, '保存成功', '配置已保存并即时生效。')
        self.accept()

    # ============================================================
    # 样式辅助
    # ============================================================
    def _label(self, text: str) -> QLabel:
        """生成统一风格的信息卡标签（次级文字、无边框）。"""
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2}; border: none;")
        return lbl

    def _input_style(self) -> str:
        """统一的输入框样式（与全局设计系统保持一致）。"""
        return f"""
            QLineEdit {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_SM};
                padding: 7px 12px;
                min-height: 36px;
                font-size: {Fonts.SZ_BODY};
                color: {Colors.TEXT};
                font-family: {Fonts.BODY};
                selection-background-color: {Colors.QINGHUA};
                selection-color: {Colors.TEXT_INV};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {Colors.QINGHUA};
                background: {Colors.CARD_HOVER};
            }}
            QLineEdit:hover:!focus {{
                border-color: {Colors.BORDER2};
            }}
            QLineEdit::placeholder {{ color: {Colors.TEXT3}; }}
        """

    def _btn_style(self, fg, border, hover) -> str:
        """生成统一样式的描边按钮样式表。

        Args:
            fg: 文字/边框颜色。
            border: 默认边框颜色。
            hover: 悬停/按下时的背景色。
        """
        return f"""
            QPushButton {{
                background: {Colors.CARD};
                color: {fg};
                border: 1px solid {border};
                border-radius: {Spacing.RADIUS_SM};
                font-size: {Fonts.SZ_BODY};
                font-family: {Fonts.BODY};
                padding: 4px 18px;
            }}
            QPushButton:hover {{ background: {hover}; }}
            QPushButton:pressed {{ background: {hover}; }}
        """
