"""
设置对话框
============
提供「AI 模型配置」与「存储方式」运行时切换。
- AI 模型配置：写入 config.ini [agnes] 段，保存后即时生效
- 存储方式：写入 config.ini [storage] 段，保存时热切换当前激活后端
"""
import configparser
import logging
import os
import tempfile
from pathlib import Path

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                               QPushButton, QButtonGroup, QRadioButton, QStackedWidget,
                               QLineEdit, QComboBox, QFormLayout, QGroupBox,
                               QMessageBox, QScrollArea, QWidget, QSizePolicy,
                               QTabWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.styles import Colors, Fonts, Spacing
from core.storage_backend import (get_storage_manager, StorageBackendError,
                                 backend_default_params, VALID_BACKENDS)

logger = logging.getLogger(__name__)

# 存储后端参数表单定义：(param_key, 显示名, 默认值, 是否密码, 是否下拉[选项])
FIELD_SPECS = {
    'mysql': [
        ('host', '主机', '127.0.0.1', False, None),
        ('port', '端口', '3306', False, None),
        ('user', '用户名', 'root', False, None),
        ('password', '密码', '', True, None),
        ('database', '数据库名', 'ai_fengshui', False, None),
        ('charset', '字符集', 'utf8mb4', False, None),
    ],
    'redis': [
        ('host', '主机', '127.0.0.1', False, None),
        ('port', '端口', '6379', False, None),
        ('db', '数据库号', '0', False, None),
        ('password', '密码', '', True, None),
        ('key_prefix', '键前缀', 'kp_fengshui:storage', False, None),
    ],
    'csv': [
        ('dir', '存储目录', 'storage/csv', False, None),
        ('encoding', '文件编码', 'utf-8', False, None),
    ],
    'text': [
        ('dir', '存储目录', 'storage/text', False, None),
        ('ext', '文件扩展名', '.txt', False, None),
        ('mode', '写入模式', 'append', False, ['append', 'per_record']),
        ('encoding', '文件编码', 'utf-8', False, None),
    ],
}

BACKEND_LABELS = {
    'mysql': '数据库 (MySQL)',
    'redis': 'Redis',
    'csv': 'CSV 文件',
    'text': '文本文件',
}

BACKEND_DESC = {
    'mysql': '界面配置、操作记录、系统日志存入 MySQL 表（复用 config.ini [database]）。',
    'redis': '三类数据写入 Redis 列表/哈希（复用全局 RedisManager）。',
    'csv': '每类数据一个 CSV 文件，便于导出与审计。',
    'text': '每类数据追加到文本文件，最轻量。',
}

# AI 模型配置字段规范：(key, 显示名, 默认值, 是否密码, 占位符, 验证类型)
AI_FIELD_SPECS = [
    ('api_key',    'API Key',             '',   True,  'sk-xxxxxxxx...', None),
    ('api_url',    'API 接口地址',        '',  False,  'https://apihub.agnes-ai.com/v1/chat/completions', 'url'),
    ('model',      '模型名称',            '',  False,  'agnes-2.0-flash', None),
    ('timeout',    '请求超时（秒）',       '120', False, '', 'int'),
    ('max_tokens', '最大 Token 数',        '4096', False, '', 'int'),
    ('max_retries', '最大重试次数',        '3',  False, '', 'int'),
    ('retry_delay', '重试间隔（秒）',      '3',  False, '', 'int'),
]


def _atomic_write_ini(path: Path, parser: configparser.ConfigParser) -> bool:
    """原子写入 config.ini：先写临时文件再 os.replace，防止程序崩溃导致配置损坏。"""
    try:
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(parent), suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                parser.write(f)
            os.replace(tmp_path, str(path))  # 原子替换
            return True
        except Exception:
            # 原子替换失败，尝试删除临时文件
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except Exception as e:
        logger.error(f"[设置] config.ini 原子写入失败: {e}")
        return False


class SettingsDialog(QDialog):
    """设置对话框（AI 模型配置 + 存储方式）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('设置')
        self.setMinimumSize(580, 600)
        self.fields = {}
        self.field_widgets = {}
        self._agn_fields = {}
        self._build_ui()
        self._prefill()

    # ======================== 主布局 ========================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        title = QLabel('AI 模型配置 · 存储方式')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_TITLE};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
            letter-spacing: 1px;
        """)
        root.addWidget(title)

        tab = QTabWidget()
        tab.setStyleSheet(f"""
            QTabBar::tab {{
                font-size: {Fonts.SZ_BODY};
                color: {Colors.TEXT2};
                padding: 8px 20px;
                border-radius: {Spacing.RADIUS} {Spacing.RADIUS} 0 0;
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                color: {Colors.QINGHUA_DARK};
                background: {Colors.QINGHUA_GLOW};
                font-weight: {Fonts.W_MEDIUM};
            }}
            QTabBar::tab:!selected {{ margin-top: 2px; }}
        """)

        # Tab 1: AI 模型配置
        tab.addTab(self._build_ai_tab(), '\U0001F916 AI 模型配置')
        # Tab 2: 存储方式
        tab.addTab(self._build_storage_tab(), '\U0001F4BE 存储方式')

        root.addWidget(tab, 1)

    # ======================== AI 模型配置 Tab ========================
    def _build_ai_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        # 说明
        lbl = QLabel('AI 模型配置')
        lbl.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
        """)
        layout.addWidget(lbl)

        desc = QLabel('配置 Agnes AI 分析模型的接口参数。修改保存后即时生效。')
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3};")
        layout.addWidget(desc)

        # 参数表单（滚动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        inner = QWidget()
        form = QFormLayout(inner)
        form.setContentsMargins(4, 4, 4, 4)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._agn_fields = {}
        for key, label, default, is_pwd, placeholder, validator in AI_FIELD_SPECS:
            w_lbl = QLabel(label)
            w_lbl.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2};")

            w = QLineEdit(str(default))
            w.setStyleSheet(self._input_style())
            w.setMinimumHeight(34)
            if placeholder:
                w.setPlaceholderText(placeholder)
            if is_pwd:
                w.setEchoMode(QLineEdit.Password)
            if validator == 'int':
                w.setInputMask('9' * 5)

            self._agn_fields[key] = (w, validator)
            form.addRow(w_lbl, w)

        scroll.setWidget(inner)
        layout.addWidget(scroll, 1)

        # 底部按钮
        btns = QHBoxLayout()
        self.ai_test_btn = QPushButton('测试连接')
        self.ai_test_btn.setCursor(Qt.PointingHandCursor)
        self.ai_test_btn.setMinimumHeight(38)
        self.ai_test_btn.setStyleSheet(self._btn_style(Colors.QINGHUA, Colors.QINGHUA_LIGHT, Colors.QINGHUA_GLOW))
        self.ai_test_btn.clicked.connect(self._on_ai_test)
        btns.addWidget(self.ai_test_btn)
        btns.addStretch()

        self.ai_cancel_btn = QPushButton('取消')
        self.ai_cancel_btn.setCursor(Qt.PointingHandCursor)
        self.ai_cancel_btn.setMinimumHeight(38)
        self.ai_cancel_btn.setStyleSheet(self._btn_style(Colors.TEXT2, Colors.BORDER, Colors.HOVER))
        self.ai_cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.ai_cancel_btn)

        self.ai_save_btn = QPushButton('保存并应用')
        self.ai_save_btn.setCursor(Qt.PointingHandCursor)
        self.ai_save_btn.setMinimumHeight(38)
        self.ai_save_btn.setStyleSheet(self._btn_style(Colors.ZHUSHA, Colors.ZHUSHA_LIGHT, Colors.ZHUSHA_GLOW))
        self.ai_save_btn.clicked.connect(self._on_ai_save)
        btns.addWidget(self.ai_save_btn)
        layout.addLayout(btns)

        return page

    def _read_ai_config(self) -> dict:
        """从 config.ini 读取当前 [agnes] 段配置。"""
        try:
            p = Path(__file__).resolve().parent.parent.parent / 'config.ini'
            parser = configparser.ConfigParser()
            if p.exists():
                parser.read(p, encoding='utf-8')
            cfg = {sp[0]: str(sp[2]) for sp in AI_FIELD_SPECS}
            if 'agnes' in parser:
                for key, *_ in AI_FIELD_SPECS:
                    if parser['agnes'].get(key):
                        cfg[key] = parser['agnes'][key]
            return cfg
        except Exception:
            return {sp[0]: str(sp[2]) for sp in AI_FIELD_SPECS}

    def _fill_ai_defaults(self):
        """用 config.ini 中已存在的 [agnes] 段参数预填 AI 表单。"""
        cfg = self._read_ai_config()
        for key, (w, _) in self._agn_fields.items():
            val = cfg.get(key, '')
            if val:
                w.setText(val)

    def _collect_ai_params(self) -> dict | None:
        """收集 AI 表单参数，非整数字段校验失败返回 None。"""
        params = {}
        for key, (w, validator) in self._agn_fields.items():
            val = w.text().strip()
            if validator == 'int' and val:
                try:
                    params[key] = int(val)
                except ValueError:
                    return None
            elif val or validator == 'int':
                params[key] = val
            else:
                params[key] = ''
        return params

    def _validate_ai_params(self, params: dict) -> str | None:
        """校验 AI 参数，返回错误信息；正确则返回 None。"""
        api_key = params.get('api_key', '').strip()
        if not api_key:
            return 'API Key 不能为空'

        api_url = params.get('api_url', '').strip()
        if not api_url:
            return 'API 接口地址不能为空'
        if not api_url.startswith(('https://', 'http://')):
            return '接口地址须以 http:// 或 https:// 开头'

        model = params.get('model', '').strip()
        if not model:
            return '模型名称不能为空'

        timeout = params.get('timeout')
        if timeout is not None and (timeout <= 0 or timeout > 3600):
            return '超时时间须在 1~3600 秒之间'

        max_tokens = params.get('max_tokens')
        if max_tokens is not None and (max_tokens <= 0 or max_tokens > 131072):
            return '最大 Token 数须在 1~131072 之间'

        max_retries = params.get('max_retries')
        if max_retries is not None and max_retries < 0:
            return '最大重试次数须为非负整数'

        retry_delay = params.get('retry_delay')
        if retry_delay is not None and retry_delay < 0:
            return '重试间隔须为非负整数'

        return None

    def _on_ai_test(self):
        """测试 Agnes AI 连接。"""
        params = self._collect_ai_params()
        if params is None:
            QMessageBox.warning(self, '参数错误', '请检查所有数值字段是否正确填写。')
            return

        err = self._validate_ai_params(params)
        if err:
            QMessageBox.warning(self, '校验失败', err)
            return

        self.ai_test_btn.setEnabled(False)
        self.ai_test_btn.setText('测试中…')
        try:
            cfg_path = Path(__file__).resolve().parent.parent.parent / 'config.ini'
            parser = configparser.ConfigParser()
            parser.read(str(cfg_path), encoding='utf-8')
            if not parser.has_section('agnes'):
                parser.add_section('agnes')
            for k, v in params.items():
                parser.set('agnes', k, str(v))

            if not _atomic_write_ini(cfg_path, parser):
                QMessageBox.warning(self, '保存失败', '配置文件写入失败，请检查磁盘权限。')
                return

            from api.agnes_client import AgnesClient
            client = AgnesClient(config_path=str(cfg_path), verify_ssl=False)
            resp = client.chat_completion(
                [{"role": "user", "content": "你好"}],
                temperature=0.0, max_tokens=4,
            )
            QMessageBox.information(self, '连接测试',
                                    '\u2705 Agnes AI 接口连接成功！\n'
                                    f'模型: {client.model}\n'
                                    f'返回: {resp.get("content", "")[:50]}')
        except Exception as e:
            QMessageBox.warning(self, '连接测试',
                                f'\u26a0\ufe0f 连接失败：{e}\n'
                                '请检查网络或配置是否正确。')
        finally:
            self.ai_test_btn.setEnabled(True)
            self.ai_test_btn.setText('测试连接')

    def _on_ai_save(self):
        """保存 AI 配置并即时生效。"""
        params = self._collect_ai_params()
        if params is None:
            QMessageBox.warning(self, '参数错误', '请检查所有数值字段是否正确填写。')
            return

        err = self._validate_ai_params(params)
        if err:
            QMessageBox.warning(self, '校验失败', err)
            return

        # 写入 config.ini（原子写入）
        cfg_path = Path(__file__).resolve().parent.parent.parent / 'config.ini'
        parser = configparser.ConfigParser()
        parser.read(str(cfg_path), encoding='utf-8')
        if not parser.has_section('agnes'):
            parser.add_section('agnes')
        for k, v in params.items():
            parser.set('agnes', k, str(v))

        if not _atomic_write_ini(cfg_path, parser):
            QMessageBox.critical(self, '保存失败', '配置文件写入失败，请检查磁盘权限。')
            return

        # 重建 AgnesClient 单例
        from api.agnes_client import _default_client as _dc
        import api.agnes_client as ac
        ac._default_client = None

        QMessageBox.information(self, '保存成功',
                                'AI 模型配置已保存并即时生效。\n'
                                '后续 AI 分析将使用新配置。')
        self.accept()

    # ======================== 存储方式 Tab ========================
    def _build_storage_tab(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        title = QLabel('存储方式设置')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_TITLE};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
            letter-spacing: 1px;
        """)
        root.addWidget(title)

        sub = QLabel('配置界面配置 / 操作记录 / 系统日志的持久化后端，可运行时切换（命理排盘与 AI 结果仍存于既有 MySQL，不在此列）。')
        sub.setWordWrap(True)
        sub.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3};")
        root.addWidget(sub)

        cur = get_storage_manager()
        cur_type = cur.backend_type if cur else '未知'
        self.cur_label = QLabel(f'当前激活后端：<b>{BACKEND_LABELS.get(cur_type, cur_type)}</b>')
        self.cur_label.setStyleSheet(f"""
            font-size: {Fonts.SZ_BODY};
            color: {Colors.QINGHUA_DARK};
            background: {Colors.QINGHUA_GLOW};
            border-radius: {Spacing.RADIUS_SM};
            padding: 8px 12px;
        """)
        root.addWidget(self.cur_label)

        mode_box = QGroupBox('存储方式')
        mode_box.setStyleSheet(self._group_style())
        mv = QVBoxLayout(mode_box)
        mv.setSpacing(8)
        self.bg = QButtonGroup(self)
        self.bg.setExclusive(True)
        self._radio_map = {}
        for btype in VALID_BACKENDS:
            rb = QRadioButton(BACKEND_LABELS.get(btype, btype))
            rb.setStyleSheet(f"""
                QRadioButton {{ font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; spacing: 6px; }}
                QRadioButton::indicator {{ width: 16px; height: 16px; }}
            """)
            rb.toggled.connect(lambda checked, t=btype: self._on_type_changed(t, checked))
            self.bg.addButton(rb)
            self._radio_map[btype] = rb
            mv.addWidget(rb)
            desc = QLabel(BACKEND_DESC.get(btype, ''))
            desc.setWordWrap(True)
            desc.setStyleSheet(f"font-size: {Fonts.SZ_MICRO}; color: {Colors.TEXT3}; margin-left: 24px;")
            mv.addWidget(desc)
        cur_type = cur.backend_type if cur else 'mysql'
        if cur_type not in self._radio_map:
            cur_type = 'mysql'
        root.addWidget(mode_box)

        self.stack = QStackedWidget()
        for btype in VALID_BACKENDS:
            p = self._build_fields_page(btype)
            self.field_widgets[btype] = p
            self.stack.addWidget(p)
        root.addWidget(self.stack, 1)

        self._radio_map[cur_type].setChecked(True)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        self.test_btn = QPushButton('测试连接')
        self.test_btn.setCursor(Qt.PointingHandCursor)
        self.test_btn.setMinimumHeight(38)
        self.test_btn.setStyleSheet(self._btn_style(Colors.QINGHUA, Colors.QINGHUA_LIGHT, Colors.QINGHUA_GLOW))
        self.test_btn.clicked.connect(self._on_test)
        btns.addWidget(self.test_btn)
        btns.addStretch()

        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setMinimumHeight(38)
        self.cancel_btn.setStyleSheet(self._btn_style(Colors.TEXT2, Colors.BORDER, Colors.HOVER))
        self.cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.cancel_btn)

        self.save_btn = QPushButton('保存并切换')
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setMinimumHeight(38)
        self.save_btn.setStyleSheet(self._btn_style(Colors.ZHUSHA, Colors.ZHUSHA_LIGHT, Colors.ZHUSHA_GLOW))
        self.save_btn.clicked.connect(self._on_save)
        btns.addWidget(self.save_btn)
        root.addLayout(btns)

        return page

    # -------------------- 原存储方式逻辑（不变） --------------------
    def _build_fields_page(self, btype: str) -> QWidget:
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        inner = QWidget()
        form = QFormLayout(inner)
        form.setContentsMargins(4, 4, 4, 4)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fields[btype] = {}
        for spec in FIELD_SPECS.get(btype, []):
            key, label, default, is_pwd, combo = spec
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2};")
            if combo:
                w = QComboBox()
                w.addItems(combo)
                w.setCurrentText(default)
                w.setStyleSheet(self._input_style())
            else:
                w = QLineEdit(str(default))
                w.setStyleSheet(self._input_style())
                if is_pwd:
                    w.setEchoMode(QLineEdit.Password)
            w.setMinimumHeight(34)
            self.fields[btype][key] = w
            form.addRow(lbl, w)
        scroll.setWidget(inner)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        return page

    def _prefill(self):
        self._fill_ai_defaults()
        try:
            import configparser
            from pathlib import Path
            p = Path(__file__).resolve().parent.parent.parent / 'config.ini'
            parser = configparser.ConfigParser()
            if p.exists():
                parser.read(p, encoding='utf-8')
            for btype, specs in FIELD_SPECS.items():
                target = {'mysql': 'database', 'redis': 'redis', 'csv': 'csv', 'text': 'text'}.get(btype)
                for spec in specs:
                    key, _label, default, _pwd, _combo = spec
                    val = default
                    if target and target in parser and key in parser[target]:
                        val = parser[target][key]
                    w = self.fields.get(btype, {}).get(key)
                    if w is None:
                        continue
                    if isinstance(w, QComboBox):
                        if val in [w.itemText(i) for i in range(w.count())]:
                            w.setCurrentText(val)
                    else:
                        w.setText(str(val))
        except Exception as e:
            logger.warning(f"[设置] 预填参数失败：{e}")

    def _on_type_changed(self, btype: str, checked: bool):
        if checked:
            idx = VALID_BACKENDS.index(btype)
            self.stack.setCurrentIndex(idx)

    def _collect_params(self, btype: str) -> dict:
        params = {}
        for key, w in self.fields.get(btype, {}).items():
            if isinstance(w, QComboBox):
                params[key] = w.currentText()
            else:
                params[key] = w.text().strip()
        for int_key in ('port', 'db'):
            if int_key in params and params[int_key] != '':
                try:
                    params[int_key] = int(params[int_key])
                except ValueError:
                    pass
        return params

    def _on_test(self):
        btype = [k for k, v in self._radio_map.items() if v.isChecked()]
        btype = btype[0] if btype else 'mysql'
        params = self._collect_params(btype)
        self.test_btn.setEnabled(False)
        self.test_btn.setText('测试中…')
        try:
            ok = get_storage_manager().test_backend(btype, params)
            if ok:
                QMessageBox.information(self, '连接测试', f'\u2705 \u300c{BACKEND_LABELS.get(btype, btype)}\u300d连接可用。')
            else:
                QMessageBox.warning(self, '连接测试', f'\u26a0\ufe0f \u300c{BACKEND_LABELS.get(btype, btype)}\u300d连接不可用，请检查参数与网络。')
        except Exception as e:
            QMessageBox.critical(self, '连接测试', f'测试出错：{e}')
        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText('测试连接')

    def _on_save(self):
        btype = [k for k, v in self._radio_map.items() if v.isChecked()]
        btype = btype[0] if btype else 'mysql'
        params = self._collect_params(btype)
        try:
            get_storage_manager().switch_backend(btype, params)
            QMessageBox.information(self, '保存成功',
                                    f'\u5df2\u5207\u6362\u5b58\u50a8\u540e\u7aef\u81f3\u300c{BACKEND_LABELS.get(btype, btype)}\u300d\u3002')
            cur = get_storage_manager().backend_type
            self.cur_label.setText(f'\u5f53\u524d\u6fc0\u6d3b\u540e\u7aef\uff1a<b>{BACKEND_LABELS.get(cur, cur)}</b>')
            self.accept()
        except StorageBackendError as e:
            QMessageBox.critical(self, '切换失败', f'\u540e\u7aef\u300c{BACKEND_LABELS.get(btype, btype)}\u300d\u6821\u9a8c\u672a\u901a\u8fc7\uff0c\u5df2\u56de\u6eda\uff1a\n{e}')
        except Exception as e:
            QMessageBox.critical(self, '切换失败', f'\u4fdd\u5b58\u51fa\u9519\uff1a{e}')

    # -------------------- 样式辅助 --------------------
    def _group_style(self) -> str:
        return f"""
            QGroupBox {{
                font-size: {Fonts.SZ_SECTION};
                font-weight: {Fonts.W_MEDIUM};
                color: {Colors.TEXT};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS};
                margin-top: 10px;
                padding: 10px 14px 14px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px; top: -8px;
                background: {Colors.CARD};
                padding: 0 6px;
            }}
        """

    def _input_style(self) -> str:
        return f"""
            QLineEdit, QComboBox {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER2};
                border-radius: {Spacing.RADIUS_SM};
                padding: 6px 10px;
                font-size: {Fonts.SZ_BODY};
                color: {Colors.TEXT};
                font-family: {Fonts.BODY};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {Colors.QINGHUA};
            }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
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
