# -*- coding: utf-8 -*-
"""
core/path_utils.py — 统一应用目录路径工具

打包 (PyInstaller) 后:
  - sys.frozen == True
  - sys._MEIPASS 为只读临时解包目录
  - sys.executable 为 exe 所在目录（用户可写）

源码运行时:
  - 返回项目根目录

所有模块应统一使用本模块的 get_app_dir() / get_config_path() / get_resource_path()
，避免各自用 Path(__file__) 链式推导导致打包后路径错误。
"""
import os
import sys
from pathlib import Path


def _exe_dir() -> str:
    """返回 exe 所在目录（打包时）或项目根目录（源码运行时）。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_app_dir() -> Path:
    """应用可写目录：打包后为 exe 同级目录，源码为项目根目录。"""
    return Path(_exe_dir())


def get_config_path() -> Path:
    """config.ini 路径：优先读 exe 同级；不存在则从资源目录复制一份。"""
    app_dir = get_app_dir()
    cfg = app_dir / 'config.ini'
    if cfg.exists():
        return cfg
    # 资源目录（_MEIPASS 或项目根）中有默认 config.ini
    if getattr(sys, 'frozen', False):
        resource_cfg = Path(sys._MEIPASS) / 'config.ini'
    else:
        resource_cfg = app_dir / 'config.ini'
    if resource_cfg.exists():
        # 首次运行：把资源 config.ini 复制到可写目录
        try:
            cfg.write_bytes(resource_cfg.read_bytes())
            return cfg
        except OSError:
            pass
    return cfg


def get_resource_path(relative: str) -> Path:
    """读取打包后只读资源文件路径（favicon.ico / database/*.sql 等）。

    打包后优先从 _MEIPASS 读取，回退到 exe 同级目录（兼容用户手动放置资源）。
    源码运行时直接在项目根目录查找。
    """
    if getattr(sys, 'frozen', False):
        # 打包环境：先在 _MEIPASS 找，再在 exe 目录找（用户可能放了自定义资源）
        candidate = Path(sys._MEIPASS) / relative
        if candidate.exists():
            return candidate
        candidate = Path(_exe_dir()) / relative
        if candidate.exists():
            return candidate
    # 源码运行：项目根目录
    return get_app_dir() / relative


def get_data_dir() -> Path:
    """可写数据目录（database/、fengshui.db、logs/ 等均放于此）。

    与 core.sqlite_db._data_dir() 逻辑保持一致。
    """
    app_dir = get_app_dir()
    data_dir = app_dir / 'data'
    if _is_writable(data_dir):
        return data_dir
    # 回退到用户目录
    fallback = Path.home() / '.kp-fengshui' / 'data'
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def get_logs_dir() -> Path:
    """可写日志目录（logs/）。"""
    app_dir = get_app_dir()
    logs_dir = app_dir / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def _is_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        test = path / '.write_test'
        test.write_text('ok')
        test.unlink()
        return True
    except OSError:
        return False
