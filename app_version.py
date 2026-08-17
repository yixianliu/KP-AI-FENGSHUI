# -*- coding: utf-8 -*-
"""应用程序版本号 —— 单一权威源 (single source of truth)。

设计目标
--------
GUI 各处（主窗口状态栏、关于对话框）、打包后的 EXE 文件版本资源（version_info.txt）、
README 等所有对外展示的版本号，都必须从本模块读取，不得各自硬编码。

这样「界面所展示的版本」与「程序实际版本」始终完全一致；升级版本时只需修改
本文件的 __version__，重新打包（scripts/build_release.py）即自动同步到
界面、EXE 资源与分发物，无需改动多处。

版本号遵循语义化版本：主版本.次版本.修订号，例如 '5.0.3'。
"""
from __future__ import annotations

__version__ = '5.0.3'

APP_NAME = '风水排盘专业工具'


def get_version() -> str:
    """返回纯数字版本号，例如 '5.0.3'（不带前缀）。"""
    return __version__


def get_version_label() -> str:
    """返回带前缀的展示版本号，例如 'v5.0.3'，用于界面与文案。"""
    return 'v' + __version__


def get_version_tuple() -> tuple[int, int, int, int]:
    """返回 4 段整数元组 (major, minor, patch, 0)，用于 EXE 版本资源。

    版本号不足 4 段时补 0；多余段忽略。解析失败回落 (0, 0, 0, 0)。
    """
    parts: list[int] = []
    try:
        for piece in __version__.split('.'):
            piece = piece.strip()
            if piece.isdigit():
                parts.append(int(piece))
    except Exception:
        parts = []
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


if __name__ == '__main__':
    print(get_version_label())
