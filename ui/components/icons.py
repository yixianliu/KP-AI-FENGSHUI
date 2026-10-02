# -*- coding: utf-8 -*-
"""
ui/components/icons.py — 统一图标加载器

UI 升级方案 M5 / 5.2：全部图标统一走 assets/icons/*.svg，
经 icon(name, size) 加载，QIcon 缓存，禁止各处裸构造 QIcon(path)。

规范（对齐实施计划 4.3）：
    - 目录：assets/icons/{name}.svg（kebab-case 小写短横线命名）
    - 尺寸：仅 16 / 20 / 24 / 32 / 48 五档
    - 路径：打包后走 core.path_utils.get_resource_path，源码走项目根
    - 缺失：图标不存在时回退到 1×1 透明占位 QIcon（不崩溃），
      并输出告警日志，便于审计漏下图标；调用方需自行用 `setText` 提供文本兜底。
"""
from typing import Optional

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize, Qt, QByteArray
import logging

logger = logging.getLogger(__name__)

# 允许的尺寸档位（5 档）
_VALID_SIZES = (16, 20, 24, 32, 48)

# 默认图标着色：与 Colors.TEXT（#F5F1E8）一致。
# SVG 源文件用 stroke="currentColor"，QPixmap 直接加载会渲染为纯黑（深色底不可见），
# 故必须显式着色。此处硬编码避免 icons -> styles 反向导入（styles 可能反过来用图标）。
_DEFAULT_ICON_COLOR = '#F5F1E8'

# QIcon 缓存：(name, size, color) -> QIcon
_ICON_CACHE: dict = {}


def icon(name: str, size: int = 24, color: Optional[str] = None) -> QIcon:
    """按名称加载 SVG 图标，缓存 QIcon。size 只支持 16/20/24/32/48。

    Args:
        name:  图标名（kebab-case，不含 .svg 后缀），如 'bazi' / 'export-pdf'。
        size:  像素尺寸，必须为 16/20/24/32/48 之一，否则抛 ValueError。
        color: SVG 着色（#RRGGBB）。SVG 用 stroke="currentColor"，
               QPixmap 直接加载会渲染为黑色（深色底不可见），故在此把
               currentColor 文本替换为指定色后用 loadFromData 解析。

    Returns:
        QIcon。文件存在时返回 SVG 图标；缺失时回退到 1×1 透明占位 QIcon，
        调用方需自行用 `setText` 提供文本兜底（图标层不维护 Unicode 字形表）。
    """
    if size not in _VALID_SIZES:
        raise ValueError(f"图标尺寸必须为 16/20/24/32/48，收到 {size}")

    # 未显式着色时用默认文字色，避免 SVG currentColor 渲染为纯黑
    color = color or _DEFAULT_ICON_COLOR

    key = (name, size, color)
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    from core.path_utils import get_resource_path
    path = get_resource_path(f"assets/icons/{name}.svg")

    qicon = None
    if path.exists():
        pix = _load_svg_pixmap(path, color, size)
        if not pix.isNull():
            qicon = QIcon()
            qicon.addPixmap(pix.scaled(QSize(size, size),
                                       Qt.KeepAspectRatio,
                                       Qt.SmoothTransformation))
            # 高分屏：直接加原始 2x 渲染结果
            qicon.addPixmap(pix)
            _ICON_CACHE[key] = qicon
            return qicon

    # 回退：1×1 透明占位（不阻断 UI；调用方需用 setText 提供文本兜底）
    logger.warning("图标文件缺失，返回透明占位: %s.svg", name)
    fallback = QIcon()
    fallback.addPixmap(QPixmap(1, 1))
    _ICON_CACHE[key] = fallback
    return fallback


def _load_svg_pixmap(path, color: Optional[str], size: int = 24) -> QPixmap:
    """加载 SVG 为 2x 尺寸的 QPixmap；color 非空时先做 currentColor 文本替换。

    QPixmap 直接加载 SVG 时 currentColor 渲染为黑色（深色底不可见），
    故统一走「文本替换 + QSvgRenderer 渲染」路径：先把 currentColor 替换为
    目标色，再用 QSvgRenderer 直接渲染到 2x 画布（高分屏清晰）。
    QSvgRenderer 不可用时回退到 loadFromData / 路径加载。
    """
    pix = QPixmap()
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("读取图标失败 %s: %s", path, e)
        return pix

    if color:
        try:
            text = raw.decode('utf-8')
            if 'currentColor' in text:
                raw = text.replace('currentColor', color).encode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            pass

    from PySide6.QtGui import QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtCore import QRectF
    renderer = QSvgRenderer(QByteArray(raw))
    if renderer.isValid():
        target = size * 2
        pix = QPixmap(target, target)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter, QRectF(0, 0, target, target))
        painter.end()
        return pix

    # 回退路径
    if not pix.loadFromData(QByteArray(raw), b'SVG'):
        pix = QPixmap(str(path))
    return pix


def has_icon(name: str) -> bool:
    """判断某图标 SVG 文件是否存在（用于走查/审计）。"""
    from core.path_utils import get_resource_path
    return get_resource_path(f"assets/icons/{name}.svg").exists()
