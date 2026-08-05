"""
设置对话框
============
提供「龙虎山大师兄」服务的运行时设置。

【安全变更说明】
旧版此处提供 API Key 输入框，并把密钥明文写入 config.ini。
该做法在面向公众分发的场景下不成立：config.ini 随 exe 一起分发，
任何用户都能直接打开读取密钥。

现改为中转服务架构：
  - 客户端不再持有、不再展示、不再可配置任何上游 API 密钥；
  - 服务地址与模型为只读展示，避免用户误改导致不可用；
  - 仅保留超时、重试等无害的本地参数供调整。
"""
import configparser
import logging
import os
import tempfile
from pathlib import Path

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QLineEdit, QFormLayout,
                               QMessageBox, QScrollArea, QWidget, QFrame)
from PySide6.QtCore import Qt

from ui.styles import Colors, Fonts, Spacing
from core.path_utils import get_config_path

logger = logging.getLogger(__name__)

# 可调参数规范：(key, 显示名, 默认值, 占位符, 验证类型)
# 仅保留无害的本地行为参数。任何凭据类字段一律不得出现在此处。
TUNABLE_FIELD_SPECS = [
    ('timeout',     '请求超时（秒）', '120', '', 'int'),
    ('max_retries', '最大重试次数',   '2',   '', 'int'),
    ('retry_delay', '重试间隔（秒）', '5',   '', 'int'),
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
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except Exception as e:
        logger.error(f"[设置] config.ini 原子写入失败: {e}")
        return False


class SettingsDialog(QDialog):
    """设置对话框（龙虎山大师兄服务设置）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('设置')
        self.setMinimumSize(580, 560)
        self._fields = {}
        self._build_ui()
        self._fill_defaults()

    # ======================== 主布局 ========================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

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
            '分析服务由云端统一提供，无需配置密钥。'
            '下方为服务信息与本地请求参数。'
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT3};")
        root.addWidget(desc)

        self._build_service_info(root)
        self._build_tunables(root)
        self._build_buttons(root)

    # ======================== 服务信息（只读） ========================
    def _build_service_info(self, root: QVBoxLayout):
        cfg = self._read_relay_config()

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
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        for label_text, value in (
            ('服务地址', cfg.get('base_url', '') or '（未配置）'),
            ('分析模型', cfg.get('model', '') or '（未配置）'),
        ):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2}; border: none;")
            val = QLabel(value)
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            val.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; border: none;")
            form.addRow(lbl, val)

        root.addWidget(box)

    # ======================== 可调参数 ========================
    def _build_tunables(self, root: QVBoxLayout):
        lbl = QLabel('请求参数')
        lbl.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
        """)
        root.addWidget(lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        inner = QWidget()
        form = QFormLayout(inner)
        form.setContentsMargins(4, 4, 4, 4)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        for key, label, default, placeholder, validator in TUNABLE_FIELD_SPECS:
            w_lbl = QLabel(label)
            w_lbl.setStyleSheet(f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT2};")

            w = QLineEdit(str(default))
            w.setStyleSheet(self._input_style())
            w.setMinimumHeight(34)
            if placeholder:
                w.setPlaceholderText(placeholder)
            if validator == 'int':
                w.setInputMask('9' * 5)

            self._fields[key] = (w, validator)
            form.addRow(w_lbl, w)

        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

    # ======================== 按钮 ========================
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

    # ======================== 配置读写 ========================
    def _read_relay_config(self) -> dict:
        """从 config.ini 读取 [relay] 段配置。"""
        defaults = {
            'base_url': '',
            'model': '',
            'timeout': '120',
            'max_retries': '2',
            'retry_delay': '5',
        }
        try:
            p = get_config_path()
            parser = configparser.ConfigParser()
            if p.exists():
                parser.read(p, encoding='utf-8')
            if 'relay' in parser:
                for key in defaults:
                    val = parser['relay'].get(key)
                    if val:
                        defaults[key] = val
        except Exception as e:
            logger.debug(f"[设置] 读取配置失败: {e}")
        return defaults

    def _fill_defaults(self):
        cfg = self._read_relay_config()
        for key, (w, _) in self._fields.items():
            val = cfg.get(key, '')
            if val:
                w.setText(str(val))

    def _collect_params(self) -> dict | None:
        """收集可调参数，整数字段校验失败返回 None。"""
        params = {}
        for key, (w, validator) in self._fields.items():
            val = w.text().strip()
            if validator == 'int':
                try:
                    params[key] = int(val)
                except ValueError:
                    return None
            else:
                params[key] = val
        return params

    def _validate(self, params: dict) -> str | None:
        """校验参数，返回错误信息；正确则返回 None。"""
        timeout = params.get('timeout')
        if timeout is not None and (timeout <= 0 or timeout > 3600):
            return '超时时间须在 1~3600 秒之间'

        max_retries = params.get('max_retries')
        if max_retries is not None and (max_retries < 0 or max_retries > 10):
            return '最大重试次数须在 0~10 之间'

        retry_delay = params.get('retry_delay')
        if retry_delay is not None and (retry_delay < 0 or retry_delay > 60):
            return '重试间隔须在 0~60 秒之间'

        return None

    def _persist(self, params: dict) -> bool:
        """把参数写入 config.ini 的 [relay] 段。"""
        cfg_path = get_config_path()
        parser = configparser.ConfigParser()
        parser.read(str(cfg_path), encoding='utf-8')
        if not parser.has_section('relay'):
            parser.add_section('relay')
        for k, v in params.items():
            parser.set('relay', k, str(v))
        return _atomic_write_ini(cfg_path, parser)

    # ======================== 事件 ========================
    def _on_test(self):
        """测试与中转服务的连通性。"""
        params = self._collect_params()
        if params is None:
            QMessageBox.warning(self, '参数错误', '请检查所有数值字段是否正确填写。')
            return

        err = self._validate(params)
        if err:
            QMessageBox.warning(self, '校验失败', err)
            return

        if not self._persist(params):
            QMessageBox.warning(self, '保存失败', '配置文件写入失败，请检查磁盘权限。')
            return

        self.test_btn.setEnabled(False)
        self.test_btn.setText('测试中…')
        try:
            from api.agnes_client import AgnesClient
            client = AgnesClient(config_path=str(get_config_path()))
            resp = client.chat_completion(
                [{"role": "user", "content": "你好"}],
                temperature=0.0, max_tokens=4,
            )
            QMessageBox.information(
                self, '连接测试',
                '\u2705 龙虎山大师兄服务连接成功！\n'
                f'模型: {client.model}\n'
                f'返回: {resp.get("content", "")[:50]}'
            )
        except Exception as e:
            # 异常文本来自客户端与中转服务，均已确保不含凭据信息
            QMessageBox.warning(
                self, '连接测试',
                f'\u26a0\ufe0f 连接失败：{e}\n请检查网络连接后重试。'
            )
        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText('测试连接')

    def _on_save(self):
        """保存参数并即时生效。"""
        params = self._collect_params()
        if params is None:
            QMessageBox.warning(self, '参数错误', '请检查所有数值字段是否正确填写。')
            return

        err = self._validate(params)
        if err:
            QMessageBox.warning(self, '校验失败', err)
            return

        if not self._persist(params):
            QMessageBox.critical(self, '保存失败', '配置文件写入失败，请检查磁盘权限。')
            return

        # 重建客户端单例，使新参数即时生效
        import api.agnes_client as ac
        ac._default_client = None

        QMessageBox.information(
            self, '保存成功',
            '设置已保存并即时生效。'
        )
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
