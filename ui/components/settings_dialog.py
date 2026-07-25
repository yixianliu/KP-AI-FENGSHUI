"""
设置对话框
============
提供「AI 模型配置」运行时设置。所有持久化（界面配置 / 操作记录 / 系统日志）
已统一迁移至本地嵌入式 SQLite 数据库（data/fengshui.db），无需在此处配置存储后端。
- AI 模型配置：写入 config.ini [agnes] 段，保存后即时生效
"""
import configparser
import logging
import os
import tempfile
from pathlib import Path

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QLineEdit, QComboBox, QFormLayout,
                               QMessageBox, QScrollArea, QWidget)
from PySide6.QtCore import Qt

from ui.styles import Colors, Fonts, Spacing

logger = logging.getLogger(__name__)

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
    """设置对话框（AI 模型配置）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('设置')
        self.setMinimumSize(580, 600)
        self.fields = {}
        self.field_widgets = {}
        self._agn_fields = {}
        self._build_ui()
        self._fill_ai_defaults()

    # ======================== 主布局 ========================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        title = QLabel('AI 模型配置')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_TITLE};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
            letter-spacing: 1px;
        """)
        root.addWidget(title)

        self._build_ai_tab(root)

    # ======================== AI 模型配置 Tab ========================
    def _build_ai_tab(self, root: QVBoxLayout):
        lbl = QLabel('AI 模型配置')
        lbl.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
        """)
        root.addWidget(lbl)

        desc = QLabel('配置 Agnes AI 分析模型的接口参数。修改保存后即时生效。')
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3};")
        root.addWidget(desc)

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
        root.addWidget(scroll, 1)

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
        root.addLayout(btns)

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
        import api.agnes_client as ac
        ac._default_client = None

        QMessageBox.information(self, '保存成功',
                                'AI 模型配置已保存并即时生效。\n'
                                '后续 AI 分析将使用新配置。')
        self.accept()

    # -------------------- 样式辅助 --------------------
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
