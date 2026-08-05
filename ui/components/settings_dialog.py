# -*- coding: utf-8 -*-
"""
ui/components/settings_dialog.py — AI 模型配置中心（GUI）

【定位】
全程序唯一的 AI 参数录入界面。用户在此集中管理：
    模型类型（供应商）/ API 端点 / 认证密钥 / 模型名称 / 请求参数
所有改动写入 `core.ai_config` 中央管理器，保存即热生效，无需重启。

【结构】
    SettingsDialog
      ├─ 状态横幅        _build_status_banner
      ├─ 配置档管理条    _build_profile_bar    （新建 / 复制 / 删除 / 切换）
      ├─ 模型接入表单    _build_model_form     （类型/端点/密钥/模型/认证方式）
      ├─ 请求参数表单    _build_request_form   （超时/重试/温度/token/SSL…）
      └─ 操作按钮        _build_buttons        （测试连接 / 取消 / 保存并应用）

【安全说明】
  - 程序本体不含任何内置端点或密钥，全部由用户填写；
  - 密钥落盘时按设备指纹派生密钥做混淆，配置文件拷到别的机器无法还原；
    这属于提高门槛而非真正加密，本机上仍可被还原，请勿绑定高价值账户。
"""
from __future__ import annotations

import logging

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QLineEdit, QFormLayout, QComboBox,
                               QMessageBox, QScrollArea, QWidget, QFrame,
                               QSpinBox, QDoubleSpinBox, QCheckBox, QInputDialog)
from PySide6.QtCore import Qt, QThread, Signal

from ui.styles import Colors, Fonts, Spacing
from core.ai_config import (AIProfile, PROVIDER_PRESETS, DEFAULT_PROVIDER,
                            get_config_manager, make_default_profile)

logger = logging.getLogger(__name__)


# ================================================================
# 连接测试后台线程（避免长超时把界面卡死）
# ================================================================
class _ConnectionTestWorker(QThread):
    """用给定配置档发一次最小请求，验证端点与密钥是否可用。"""

    finished_ok = Signal(str)     # 返回内容片段
    finished_err = Signal(str)    # 错误描述

    def __init__(self, profile: AIProfile, parent=None):
        super().__init__(parent)
        self._profile = profile

    def run(self):
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
# 主对话框
# ================================================================
class SettingsDialog(QDialog):
    """AI 模型配置对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('设置 · 龙虎山大师兄配置')
        self.setMinimumSize(640, 720)

        self._manager = get_config_manager()
        self._test_worker = None

        # 工作副本：所有编辑先落在草稿上，点「保存并应用」才整体提交
        self._drafts: list[AIProfile] = self._manager.list_profiles()
        self._active_id: str = self._manager.active_id
        if not self._drafts:
            draft = make_default_profile()
            self._drafts.append(draft)
            self._active_id = draft.id
        self._current_id: str = self._active_id
        self._loading = False    # 抑制填表期间的信号回环

        self._build_ui()
        self._refresh_profile_combo()
        self._load_draft_to_form()
        self._refresh_status()

    # ============================================================
    # 布局构建
    # ============================================================
    def _build_ui(self):
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
            '本程序不内置任何模型服务，请在此填写你自己的接口信息。'
            '密钥仅保存在本机，并按设备指纹混淆存储。'
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3};")
        root.addWidget(desc)

        self._build_status_banner(root)
        self._build_profile_bar(root)

        # 表单区滚动容器
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        inner = QWidget()
        body = QVBoxLayout(inner)
        body.setContentsMargins(2, 2, 2, 2)
        body.setSpacing(14)

        self._build_model_form(body)
        self._build_request_form(body)
        body.addStretch()

        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        self._build_buttons(root)

    # ---------- 状态横幅 ----------
    def _build_status_banner(self, root: QVBoxLayout):
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(38)
        root.addWidget(self.status_label)

    def _refresh_status(self, override: str = '', level: str = ''):
        """刷新状态横幅。level: ok / warn / err，留空则按当前草稿自动判定。"""
        if override:
            text, lv = override, (level or 'ok')
        else:
            draft = self._current_draft()
            err = draft.validate() if draft else '尚未创建配置'
            if err:
                text, lv = f'配置未完成：{err}', 'warn'
            else:
                text, lv = f'配置完整：{draft.model} @ {_host_of(draft.api_url)}', 'ok'

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

    # ---------- 配置档管理条 ----------
    def _build_profile_bar(self, root: QVBoxLayout):
        bar = QHBoxLayout()
        bar.setSpacing(8)

        lbl = QLabel('配置档')
        lbl.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2};")
        bar.addWidget(lbl)

        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet(self._input_style())
        self.profile_combo.setToolTip('切换配置档；「生效中」标记当前被程序使用的那份配置')
        self.profile_combo.currentIndexChanged.connect(self._on_profile_switched)
        bar.addWidget(self.profile_combo, 1)

        for text, slot in (('新建', self._on_new_profile),
                           ('复制', self._on_copy_profile),
                           ('删除', self._on_delete_profile)):
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(32)
            btn.setStyleSheet(
                self._btn_style(Colors.TEXT2, Colors.BORDER, Colors.HOVER))
            btn.clicked.connect(slot)
            bar.addWidget(btn)

        root.addLayout(bar)

    # ---------- 模型接入表单 ----------
    def _build_model_form(self, body: QVBoxLayout):
        box, form = self._section(body, '模型接入')

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('给这份配置起个名字，例如：主力模型')
        self.name_edit.setToolTip('配置档名称仅用于本机辨识，可随意命名')
        self._wire(self.name_edit)
        form.addRow(self._label('配置名称'), self.name_edit)

        self.provider_combo = QComboBox()
        for key, preset in PROVIDER_PRESETS.items():
            self.provider_combo.addItem(preset.label, key)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        self.provider_combo.setToolTip('选择模型服务商；切换后会自动套用该服务的默认端点与模型建议')
        self._style_input(self.provider_combo)
        form.addRow(self._label('模型类型'), self.provider_combo)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText('https://api.example.com/v1/chat/completions')
        self.url_edit.setToolTip('模型服务的聊天补全接口地址；OpenAI 兼容服务通常以 /chat/completions 结尾')
        self._wire(self.url_edit)
        form.addRow(self._label('API 端点'), self.url_edit)
        self._add_hint(form, '需以 http(s):// 开头；OpenAI 兼容服务通常以 /chat/completions 结尾')

        # 密钥行：输入框 + 显示/隐藏
        key_row = QWidget()
        key_layout = QHBoxLayout(key_row)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.setSpacing(6)
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setPlaceholderText('sk-... （仅保存在本机）')
        self.key_edit.setToolTip('认证密钥（API Key）；仅保存在本机并按设备指纹混淆，不会被上传')
        self._wire(self.key_edit)
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
        form.addRow(self._label('认证密钥'), key_row)

        self.auth_combo = QComboBox()
        self.auth_combo.addItem('Bearer（标准，自动加前缀）', 'bearer')
        self.auth_combo.addItem('原样发送（自定义网关）', 'raw')
        self.auth_combo.currentIndexChanged.connect(self._on_field_changed)
        self.auth_combo.setToolTip('Bearer：自动在密钥前加 "Bearer "；原样发送：自定义网关已自带鉴权头时使用')
        self._style_input(self.auth_combo)
        form.addRow(self._label('认证方式'), self.auth_combo)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setStyleSheet(self._input_style())
        self.model_combo.setToolTip('选择或手动输入模型名称；不同服务商的模型名不同')
        self.model_combo.currentTextChanged.connect(self._on_field_changed)
        form.addRow(self._label('模型名称'), self.model_combo)
        self._add_hint(form, '可直接输入自定义模型名，例如 deepseek-reasoner、qwen-max')

        box.setVisible(True)

    # ---------- 请求参数表单 ----------
    def _build_request_form(self, body: QVBoxLayout):
        _, form = self._section(body, '请求参数')

        self.timeout_spin = self._spin(1, 3600, ' 秒')
        self.timeout_spin.setToolTip('单次请求最长等待时间，超时将触发重试或失败')
        form.addRow(self._label('请求超时'), self.timeout_spin)

        self.retries_spin = self._spin(0, 10, ' 次')
        self.retries_spin.setToolTip('失败后自动重试次数；设为 0 表示不重试')
        form.addRow(self._label('最大重试'), self.retries_spin)

        self.delay_spin = self._spin(0, 60, ' 秒')
        self.delay_spin.setToolTip('每次重试之间的间隔')
        form.addRow(self._label('重试间隔'), self.delay_spin)

        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setDecimals(1)
        self.temp_spin.setStyleSheet(self._input_style())
        self.temp_spin.setToolTip('采样温度：0 更确定，2 更发散；本程序分析建议 0 ~ 0.7')
        self.temp_spin.valueChanged.connect(self._on_field_changed)
        form.addRow(self._label('采样温度'), self.temp_spin)

        self.tokens_spin = self._spin(16, 32768, '')
        self.tokens_spin.setSingleStep(256)
        self.tokens_spin.setToolTip('模型单次回复的最大 token 数')
        form.addRow(self._label('最大输出'), self.tokens_spin)

        self.ssl_check = QCheckBox('校验 SSL 证书（自签名证书可关闭）')
        self.ssl_check.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT2};")
        self.ssl_check.setToolTip('关闭后不校验 SSL 证书，仅用于自签名证书等测试环境')
        self.ssl_check.toggled.connect(self._on_field_changed)
        form.addRow(self._label('安全'), self.ssl_check)

        self.think_check = QCheckBox('关闭思考模式（部分模型支持，可大幅提速）')
        self.think_check.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT2};")
        self.think_check.setToolTip('部分模型（如带思考模式的版本）关闭后可显著提速')
        self.think_check.toggled.connect(self._on_field_changed)
        form.addRow(self._label('加速'), self.think_check)

    # ---------- 按钮 ----------
    def _build_buttons(self, root: QVBoxLayout):
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
    # 草稿 <-> 表单
    # ============================================================
    def _current_draft(self) -> AIProfile | None:
        for p in self._drafts:
            if p.id == self._current_id:
                return p
        return self._drafts[0] if self._drafts else None

    def _load_draft_to_form(self):
        """把当前草稿填入表单。"""
        draft = self._current_draft()
        if draft is None:
            return
        self._loading = True
        try:
            self.name_edit.setText(draft.name)

            idx = self.provider_combo.findData(draft.provider)
            self.provider_combo.setCurrentIndex(idx if idx >= 0 else 0)
            self._reload_model_candidates(draft.provider)

            self.url_edit.setText(draft.api_url)
            self.key_edit.setText(draft.api_key)

            idx = self.auth_combo.findData(draft.auth_scheme)
            self.auth_combo.setCurrentIndex(idx if idx >= 0 else 0)

            self.model_combo.setCurrentText(draft.model)

            self.timeout_spin.setValue(draft.timeout)
            self.retries_spin.setValue(draft.max_retries)
            self.delay_spin.setValue(draft.retry_delay)
            self.temp_spin.setValue(draft.temperature)
            self.tokens_spin.setValue(draft.max_tokens)
            self.ssl_check.setChecked(draft.verify_ssl)
            self.think_check.setChecked(draft.send_no_think)
            self._apply_provider_dependencies(draft.provider)
        finally:
            self._loading = False

    def _sync_form_to_draft(self):
        """把表单内容写回当前草稿。"""
        draft = self._current_draft()
        if draft is None or self._loading:
            return
        draft.name = self.name_edit.text().strip() or '未命名配置'
        draft.provider = self.provider_combo.currentData() or DEFAULT_PROVIDER
        draft.api_url = self.url_edit.text().strip()
        draft.api_key = self.key_edit.text().strip()
        draft.auth_scheme = self.auth_combo.currentData() or 'bearer'
        draft.model = self.model_combo.currentText().strip()
        draft.timeout = self.timeout_spin.value()
        draft.max_retries = self.retries_spin.value()
        draft.retry_delay = self.delay_spin.value()
        draft.temperature = round(self.temp_spin.value(), 2)
        draft.max_tokens = self.tokens_spin.value()
        draft.verify_ssl = self.ssl_check.isChecked()
        draft.send_no_think = self.think_check.isChecked()

    def _reload_model_candidates(self, provider: str):
        """按供应商预设刷新模型下拉候选（保留用户已填的自定义值）。"""
        current = self.model_combo.currentText()
        preset = PROVIDER_PRESETS.get(provider)
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        if preset and preset.models:
            self.model_combo.addItems(list(preset.models))
        if current:
            self.model_combo.setCurrentText(current)
        self.model_combo.blockSignals(False)

    def _apply_provider_dependencies(self, provider: str):
        """根据供应商预设调整界面细节：

        - 本地模型（如 Ollama）无需密钥时，置灰密钥框并给出提示；
        - 端点输入框的占位提示随预设端点更新，给用户更直接的可填样例。
        """
        preset = PROVIDER_PRESETS.get(provider)
        needs_key = preset.needs_key if preset else True
        self.key_edit.setEnabled(needs_key)
        self.key_toggle.setEnabled(needs_key)
        if needs_key:
            self.key_edit.setPlaceholderText('sk-... （仅保存在本机）')
        else:
            self.key_edit.setPlaceholderText('本地模型无需密钥')
        # 端点占位提示：带预设则展示预设地址，否则给通用模板
        if preset and preset.api_url:
            self.url_edit.setPlaceholderText(preset.api_url)
        else:
            self.url_edit.setPlaceholderText(
                'https://api.example.com/v1/chat/completions')

    def _refresh_profile_combo(self):
        self._loading = True
        try:
            self.profile_combo.clear()
            for p in self._drafts:
                label = p.name if p.id != self._active_id else f'{p.name} （生效中）'
                self.profile_combo.addItem(label, p.id)
            idx = self.profile_combo.findData(self._current_id)
            self.profile_combo.setCurrentIndex(idx if idx >= 0 else 0)
        finally:
            self._loading = False

    # ============================================================
    # 事件
    # ============================================================
    def _on_field_changed(self, *_):
        if self._loading:
            return
        self._sync_form_to_draft()
        self._refresh_status()

    def _on_provider_changed(self, *_):
        """切换模型类型：套用预设端点与模型候选（不覆盖用户已填内容）。"""
        if self._loading:
            return
        provider = self.provider_combo.currentData() or DEFAULT_PROVIDER
        preset = PROVIDER_PRESETS.get(provider)
        if preset:
            if preset.api_url and not self.url_edit.text().strip():
                self.url_edit.setText(preset.api_url)
            idx = self.auth_combo.findData(preset.auth_scheme)
            if idx >= 0:
                self.auth_combo.setCurrentIndex(idx)
            self.think_check.setChecked(preset.send_no_think)
            self._reload_model_candidates(provider)
            if preset.models and not self.model_combo.currentText().strip():
                self.model_combo.setCurrentText(preset.models[0])
        self._apply_provider_dependencies(provider)
        self._on_field_changed()

    def _on_toggle_key_visible(self, shown: bool):
        self.key_edit.setEchoMode(QLineEdit.Normal if shown else QLineEdit.Password)
        self.key_toggle.setText('隐藏' if shown else '显示')

    def _on_profile_switched(self, *_):
        if self._loading:
            return
        new_id = self.profile_combo.currentData()
        if not new_id or new_id == self._current_id:
            return
        self._sync_form_to_draft()      # 先保住当前编辑
        self._current_id = new_id
        self._load_draft_to_form()
        self._refresh_status()

    def _on_new_profile(self):
        self._sync_form_to_draft()
        name, ok = QInputDialog.getText(self, '新建配置档', '配置名称：', text='新配置')
        if not ok:
            return
        draft = make_default_profile()
        draft.name = name.strip() or '新配置'
        self._drafts.append(draft)
        self._current_id = draft.id
        self._refresh_profile_combo()
        self._load_draft_to_form()
        self._refresh_status()

    def _on_copy_profile(self):
        self._sync_form_to_draft()
        src = self._current_draft()
        if src is None:
            return
        copy_profile = src.clone(f'{src.name} 副本')
        self._drafts.append(copy_profile)
        self._current_id = copy_profile.id
        self._refresh_profile_combo()
        self._load_draft_to_form()
        self._refresh_status()

    def _on_delete_profile(self):
        if len(self._drafts) <= 1:
            QMessageBox.information(self, '无法删除', '至少需要保留一份配置档。')
            return
        draft = self._current_draft()
        if draft is None:
            return
        if QMessageBox.question(
                self, '删除配置档',
                f'确定删除「{draft.name}」吗？此操作在保存后生效。'
        ) != QMessageBox.Yes:
            return
        self._drafts = [p for p in self._drafts if p.id != draft.id]
        if self._active_id == draft.id:
            self._active_id = self._drafts[0].id
        self._current_id = self._drafts[0].id
        self._refresh_profile_combo()
        self._load_draft_to_form()
        self._refresh_status()

    # ---------- 测试连接 ----------
    def _on_test(self):
        self._sync_form_to_draft()
        draft = self._current_draft()
        if draft is None:
            return
        err = draft.validate()
        if err:
            QMessageBox.warning(self, '配置不完整', err)
            return

        self.test_btn.setEnabled(False)
        self.test_btn.setText('测试中…')
        self._refresh_status('正在连接，请稍候…', 'warn')

        self._test_worker = _ConnectionTestWorker(draft.clone(), self)
        self._test_worker.finished_ok.connect(self._on_test_ok)
        self._test_worker.finished_err.connect(self._on_test_err)
        self._test_worker.finished.connect(self._on_test_done)
        self._test_worker.start()

    def _on_test_ok(self, snippet: str):
        self._refresh_status(f'连接成功，模型已响应：{snippet or "（空回复）"}', 'ok')
        QMessageBox.information(
            self, '连接测试',
            f'连接成功！\n模型: {self.model_combo.currentText()}\n返回: {snippet}'
        )

    def _on_test_err(self, message: str):
        self._refresh_status(f'连接失败：{message}', 'err')
        QMessageBox.warning(
            self, '连接测试',
            f'连接失败：{message}\n\n请检查 API 端点、密钥与网络后重试。'
        )

    def _on_test_done(self):
        self.test_btn.setEnabled(True)
        self.test_btn.setText('测试连接')
        self._test_worker = None

    # ---------- 保存 ----------
    def _on_save(self):
        self._sync_form_to_draft()

        # 生效档必须完整可用；其余档允许暂存不完整
        self._active_id = self._current_id
        active = self._current_draft()
        if active is None:
            QMessageBox.warning(self, '保存失败', '没有可保存的配置。')
            return
        err = active.validate()
        if err:
            QMessageBox.warning(
                self, '配置不完整',
                f'{err}\n\n当前配置档将设为生效配置，必须填写完整。'
            )
            return

        if not self._manager.replace_all(self._drafts, self._active_id):
            QMessageBox.critical(
                self, '保存失败', '配置写入失败，请检查程序目录的磁盘写入权限。')
            return

        # 中央管理器已自增版本号并通知订阅者；客户端单例会在下次调用时按新配置重建。
        QMessageBox.information(
            self, '保存成功',
            f'配置已保存并即时生效。\n当前生效：{active.name}（{active.model}）'
        )
        self.accept()

    # ============================================================
    # 样式辅助
    # ============================================================
    def _section(self, body: QVBoxLayout, title: str):
        """生成一个带标题的表单分组，返回 (容器, QFormLayout)。"""
        lbl = QLabel(title)
        lbl.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
            border-left: 3px solid {Colors.QINGHUA};
            padding-left: 10px;
            margin-bottom: 2px;
        """)
        body.addWidget(lbl)

        box = QFrame()
        box.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER2};
                border-radius: {Spacing.RADIUS_SM};
            }}
        """)
        form = QFormLayout(box)
        form.setContentsMargins(16, 14, 16, 14)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        body.addWidget(box)
        return box, form

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2}; border: none;")
        return lbl

    def _add_hint(self, form: QFormLayout, text: str) -> None:
        """在表单内追加一行小字提示（右侧空标签占位，左对齐说明文字）。"""
        hint = QLabel(text)
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT3}; border: none;")
        form.addRow(QLabel(''), hint)

    def _spin(self, lo: int, hi: int, suffix: str) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(lo, hi)
        spin.setSuffix(suffix)
        spin.setStyleSheet(self._input_style())
        spin.valueChanged.connect(self._on_field_changed)
        return spin

    def _wire(self, edit: QLineEdit):
        """统一给输入框套样式并挂变更监听。"""
        edit.setStyleSheet(self._input_style())
        edit.textChanged.connect(self._on_field_changed)

    def _style_input(self, widget):
        widget.setStyleSheet(self._input_style())

    def _input_style(self) -> str:
        """统一的输入框 / 下拉框 / 微调框样式（与全局设计系统保持一致）。"""
        return f"""
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
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
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1.5px solid {Colors.QINGHUA};
                background: {Colors.CARD_HOVER};
            }}
            QLineEdit:hover:!focus, QComboBox:hover:!focus,
            QSpinBox:hover:!focus, QDoubleSpinBox:hover:!focus {{
                border-color: {Colors.BORDER2};
            }}
            QLineEdit:disabled, QComboBox:disabled,
            QSpinBox:disabled, QDoubleSpinBox:disabled {{
                background: {Colors.BG_DARK};
                color: {Colors.TEXT3};
                border: 1px solid {Colors.BORDER};
            }}
            QLineEdit::placeholder {{ color: {Colors.TEXT3}; }}

            /* ---- 下拉箭头（自定义三角，避免平台原生箭头不统一） ---- */
            QComboBox::drop-down {{
                border: none;
                width: 22px;
                subcontrol-origin: padding;
                subcontrol-position: right center;
                padding-right: 8px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {Colors.TEXT3};
            }}
            QComboBox::down-arrow:hover {{ border-top-color: {Colors.QINGHUA}; }}
            QComboBox:disabled::down-arrow {{ border-top-color: {Colors.TEXT4}; }}

            /* ---- 下拉弹出列表 ---- */
            QComboBox QAbstractItemView {{
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS_SM};
                background: {Colors.CARD};
                selection-background-color: {Colors.QINGHUA};
                selection-color: {Colors.TEXT_INV};
                padding: 6px;
                outline: none;
                font-size: {Fonts.SZ_BODY};
                font-family: {Fonts.BODY};
            }}
            QComboBox QAbstractItemView::item {{
                padding: 8px 12px;
                border-radius: 4px;
                min-height: 30px;
            }}
            QComboBox QAbstractItemView::item:hover {{ background-color: {Colors.HOVER}; }}

            /* 可编辑下拉（模型名称）内部的输入框保持清爽，不重复描边 */
            QComboBox QLineEdit {{
                background: transparent;
                border: none;
                padding: 0;
            }}

            /* ---- 微调框上下箭头 ---- */
            QSpinBox::up-button, QSpinBox::down-button {{
                subcontrol-origin: border;
                width: 20px;
                border: none;
                background: transparent;
            }}
            QSpinBox::up-arrow {{
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-bottom: 4px solid {Colors.TEXT3};
            }}
            QSpinBox::down-arrow {{
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 4px solid {Colors.TEXT3};
            }}
            QSpinBox::up-arrow:hover {{ border-bottom-color: {Colors.QINGHUA}; }}
            QSpinBox::down-arrow:hover {{ border-top-color: {Colors.QINGHUA}; }}
        """

    def _btn_style(self, fg, border, hover) -> str:
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


def _host_of(api_url: str) -> str:
    """从端点提取 scheme://host 用于简洁展示。"""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(api_url)
        if parsed.netloc:
            return f'{parsed.scheme}://{parsed.netloc}'
    except Exception:
        pass
    return api_url or '（未配置）'
