#!/usr/bin/env python
"""PyInstaller build script for green portable EXE version of KP-AI-FENGSHUI.

This script generates a single-file, portable executable with:
- No console window (GUI mode)
- All dependencies embedded
- UPX compression for smaller file size
- Portable-friendly configuration
"""
import os
import sys
import shutil
from pathlib import Path

# 项目根目录
project_root = Path(__file__).resolve().parent

# 输出目录 - 作为参数传入，或使用默认值
DIST_DIR = Path(os.environ.get('DIST_PATH', project_root / 'dist'))

# 无需再添加 pyside6_packages 到路径，因为我们使用 venv 的 PySide6
# pyside6_packages = project_root / "pyside6_packages"
# if pyside6_packages.exists():
#     if str(pyside6_packages) not in sys.path:
#         sys.path.insert(0, str(pyside6_packages))

# 导入 PyInstaller
import PyInstaller.__main__

# 清理旧构建目录
if DIST_DIR.exists():
    shutil.rmtree(DIST_DIR)

build_dir = project_root / "build"
if build_dir.exists():
    shutil.rmtree(build_dir)

# 环境变量
os.environ['DIST_PATH'] = str(DIST_DIR)

# PyInstaller 参数配置
pyinstaller_args = [
    # 主程序入口
    "main.py",

    # 输出目录
    f"--distpath={DIST_DIR}",
    f"--workpath={build_dir}",

    # 可执行文件名称
    "-n", "KP-AI-FENGSHUI",

    # GUI 模式（无控制台窗口）
    "-w",

    # 图标
    f"-i={project_root}/assets/favicon.ico",

    # 优化级别
    "--optimize=2",

    # 隐藏导入模块列表
    "--hidden-import=core.bazi.bazi_calculator",
    "--hidden-import=core.bazi.bazi_types",
    "--hidden-import=core.ganzhi_constants",
    "--hidden-import=core.ai_config",
    "--hidden-import=core.database_manager",
    "--hidden-import=core.ai_cache",
    "--hidden-import=core.ai_metrics",
    "--hidden-import=core.ai_throttle",
    "--hidden-import=core.path_utils",
    "--hidden-import=core.secure_log",
    "--hidden-import=core.bazi.shishen",
    "--hidden-import=core.bazi.wuxing",
    "--hidden-import=core.divination.liuren",
    "--hidden-import=core.bazi.mingli",
    "--hidden-import=core.divination.meihua",
    "--hidden-import=core.divination.hexagram_analyzer",
    "--hidden-import=core.bazi.geju_analyzer",
    "--hidden-import=core.calendar_utils",
    "--hidden-import=core.lunar_converter",
    "--hidden-import=core.local_settings",
    "--hidden-import=core.location_db",
    "--hidden-import=core.log_handler",
    "--hidden-import=core.knowledge.data_integration",
    "--hidden-import=core.knowledge.data_validator",
    "--hidden-import=core.debug_keys",
    "--hidden-import=core.device_identity",
    "--hidden-import=core.dll_diagnostic",
    "--hidden-import=core.bazi._baazi_compat",
    "--hidden-import=core.divination.hexagram_data",
    "--hidden-import=core.bazi.yuncheng",
    "--hidden-import=core.bazi.yunshi",
    "--hidden-import=core.knowledge.analysis_fallback",
    "--hidden-import=core.knowledge.analysis_storage",
    "--hidden-import=core.app_version",
    "--hidden-import=api.agnes_client",

    # PySide6 相关
    "--hidden-import=PySide6",
    "--hidden-import=PySide6.QtCore",
    "--hidden-import=PySide6.QtGui",
    "--hidden-import=PySide6.QtWidgets",
    "--hidden-import=PySide6.QtQml",
    "--hidden-import=PySide6.QtQuick",

    # 其他依赖
    "--hidden-import=lunarcalendar",
    "--hidden-import=requests",
    "--hidden-import=urllib3",
    "--hidden-import=certifi",
    "--hidden-import=openpyxl",
    "--hidden-import=reportlab",

    # 数据文件
    "--add-data=database;database",
    "--add-data=data;data",

    # Qt 平台插件
    f"--add-data={project_root}/pyside6_packages/PySide6/plugins/platforms;platforms",
    f"--add-data={project_root}/pyside6_packages/PySide6/resources/icudtl.dat;.",

    # 资源文件
    "--add-data=assets;assets",

    # 清理构建
    "--clean",

    # 单文件模式（便携版）
    "--onefile",

    # UPX 压缩（减小文件大小） - 注释掉避免错误
    # "--upx-dir", str(project_root / "upx"),

    # 禁用 UPX 压缩（若遇到问题可取消注释下面一行）
    # "--noui",
]

print("=" * 60)
print("构建绿色便携版 EXE")
print("=" * 60)
print(f"项目根目录: {project_root}")
print(f"输出目录: {DIST_DIR}")
print(f"构建目录: {build_dir}")
print("=" * 60)

# 运行 PyInstaller
PyInstaller.__main__.run(pyinstaller_args)

print("\n" + "=" * 60)
print("构建完成!")
print(f"可执行文件位置: {DIST_DIR / 'KP-AI-FENGSHUI.exe'}")
print("=" * 60)