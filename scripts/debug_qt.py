import sys
import os
from pathlib import Path

project_root = Path(__file__).resolve().parent
print(f"Project root: {project_root}")
print(f"PATH: {os.environ.get('PATH', '')[:200]}...")
print()

# Check if pixas6_packages exists
dll_packages_path = project_root / 'pyside6_packages' / 'PySide6'
plugin_path = project_root / 'pyside6_packages' / 'PySide6' / 'plugins' / 'platforms'

print(f"pyside6_packages exists: {dll_packages_path.exists()}")
print(f"plugins path exists: {plugin_path.exists()}")
print()

# Check current loaded Qt6Core
import ctypes
import ctypes.util

print("Checking DLL loading order...")

# Try to find Qt6Core
common_paths = [
    Path(sys.executable).parent / 'Qt6Core.dll',
    Path(sys.executable).parent.parent / 'Qt6Core.dll',
    Path.cwd() / 'Qt6Core.dll',
    Path(sys.prefix) / 'Lib' / 'site-packages' / 'PySide6' / 'Qt6' / 'bin' / 'Qt6Core.dll',
    Path(sys.prefix) / 'Lib' / 'site-packages' / 'PyQt6' / 'Qt6' / 'bin' / 'Qt6Core.dll',
]

for p in common_paths:
    if p.exists():
        print(f"Found Qt6Core.dll at: {p}")
        lib = ctypes.CDLL(str(p.resolve()), winmode=8)
        print("  Loaded successfully")
        # Check for symbol
        if hasattr(lib, 'UCN_TO_U_CALLBACK_SUBSTITUTE'):
            print("  Has UCN_TO_U_CALLBACK_SUBSTITUTE: True")
        else:
            print("  Has UCN_TO_U_CALLBACK_SUBSTITUTE: False")
        break
else:
    print("Qt6Core.dll not found in common paths")
    
# Now try with add_dll_directory
print()
print("Testing add_dll_directory...")

if hasattr(os, 'add_dll_directory'):
    try:
        os.add_dll_directory(str(dll_packages_path.resolve()))
        print(f"Added pyside6_packages to DLL directory: {dll_packages_path}")
    except Exception as e:
        print(f"Failed to add DLL directory: {e}")

# Check PATH after modification
print(f"\nPATH after modification: {os.environ.get('PATH', '')[:200]}...")
print()

# Set QT_QPA_PLATFORM_PLUGIN_PATH
if plugin_path.exists():
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(plugin_path.resolve())
    print(f"Set QT_QPA_PLATFORM_PLUGIN_PATH: {plugin_path}")
else:
    print(f"Plugin path does not exist: {plugin_path}")

# Try importing PySide6
print()
print("Trying to import PySide6.QtWidgets...")
try:
    from PySide6.QtWidgets import QApplication
    print("Successfully imported QApplication!")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"Import error: {type(e).__name__}: {e}")