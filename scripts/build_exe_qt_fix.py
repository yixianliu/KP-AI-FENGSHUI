#!/usr/bin/env python
"""PyInstaller build script for KP-AI-FENGSHUI Windows executable - with Qt platform plugin fix and data directories."""
import os
import sys
import shutil
from pathlib import Path

# Project root directory
project_root = Path(__file__).resolve().parent

# Add pyside6_packages to path so PyInstaller can find them
pyside6_packages = project_root / "pyside6_packages"
if pyside6_packages.exists():
    if str(pyside6_packages) not in sys.path:
        sys.path.insert(0, str(pyside6_packages))

# PyInstaller configuration using PyInstaller.__main__
import PyInstaller.__main__

project_root_str = str(project_root)
dist_path = os.path.join(project_root_str, "dist")
work_path = os.path.join(project_root_str, "build")

# Remove old dist/build directories if needed
if os.path.exists(dist_path):
    shutil.rmtree(dist_path)
if os.path.exists(work_path):
    shutil.rmtree(work_path)

# Custom runtime hook to fix Qt platform plugin path
# This hook sets QT_QPA_PLATFORM_PLUGIN_PATH so Qt can find the platform plugins
hook_content = r'''
import os
import sys

def patch():
    """Set Qt platform plugin path for PyInstaller single-file mode."""
    # Get the directory where the executable is running
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    # Also check _MEIPASS which PyInstaller extracts to for single-file mode
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        exe_dir = meipass
    
    # Set the platform plugin path - look for platforms directory next to exe
    platforms_dir = os.path.join(exe_dir, "platforms")
    if os.path.isdir(platforms_dir):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms_dir
    
    # Fallback: look in PySide6/packages directory (also via _MEIPASS)
    if "QT_QPA_PLATFORM_PLUGIN_PATH" not in os.environ:
        # Check _MEIPASS first (PyInstaller extracted dir)
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            platforms_from_meipass = os.path.join(meipass, "platforms")
            if os.path.isdir(platforms_from_meipass):
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms_from_meipass
        # Fallback: look relative to project root
        if "QT_QPA_PLATFORM_PLUGIN_PATH" not in os.environ:
            pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            platforms = os.path.join(pkg_dir, "pyside6_packages", "PySide6", "plugins", "platforms")
            if os.path.isdir(platforms):
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms

# Run the patch when module is imported
patch()
'''

# Write the runtime hook file
hooks_dir = project_root / "scripts"
hooks_dir.mkdir(exist_ok=True)
hook_file = hooks_dir / "pyi_rth_qt_platform.py"
with open(hook_file, "w", encoding="utf-8") as f:
    f.write(hook_content)

print(f"Created runtime hook: {hook_file}")

pyinstaller_args = [
    # Main script
    "main.py",
    
    # Output directory
    f"--distpath={dist_path}",
    f"--workpath={work_path}",
    
    # Executable name (via -n)
    "-n", "KP-AI-FENGSHUI",
    
    # GUI mode (no console window)
    "-w",
    
    # Icon
    f"-i={project_root}/assets/favicon.ico",
    
    # Optimize bytecode
    "--optimize=2",
    
    # Include hidden imports
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
    "--hidden-import=PySide6",
    "--hidden-import=PySide6.QtCore",
    "--hidden-import=PySide6.QtGui",
    "--hidden-import=PySide6.QtWidgets",
    "--hidden-import=PySide6.QtQml",
    "--hidden-import=PySide6.QtQuick",
    "--hidden-import=lunarcalendar",
    "--hidden-import=requests",
    "--hidden-import=urllib3",
    "--hidden-import=certifi",
    "--hidden-import=openpyxl",
    "--hidden-import=reportlab",
    
    # Include additional data files
    # icudtl.dat
    f"--add-data={project_root}/pyside6_packages/PySide6/resources/icudtl.dat;.",
    
    # **关键：Qt 平台插件目录 - 必须显式添加**
    f"--add-data={project_root}/pyside6_packages/PySide6/plugins/platforms;platforms",
    
    # Database and data directories (critical for application function)
    f"--add-data={project_root}/database;database",
    f"--add-data={project_root}/data;data",
    
    # QR code images directory (payment QR codes - Alipay/WeChat)
    # qrcode 目录位于项目父级: D:\PythonProject\qrcode
    f"--add-data=D:\\\\PythonProject\\\\qrcode;qrcode",
    
    # Clean build
    "--clean",
    
    # 禁用 UPX 压缩，避免与某些 Qt DLLs 兼容性问题
    "--noconfirm",
    
    # Use custom runtime hook for Qt platform plugin
    f"--runtime-hook={project_root}/scripts/pyi_rth_qt_platform.py",
]

print("Running PyInstaller build...")
print(f"Project root: {project_root_str}")
print(f"Dist path: {dist_path}")
print(f"Work path: {work_path}")

# Run PyInstaller
PyInstaller.__main__.run(pyinstaller_args)

print("\nBuild completed!")
print(f"Executable located at: {os.path.join(dist_path, 'KP-AI-FENGSHUI.exe')}")