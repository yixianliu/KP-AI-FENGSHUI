"""Import hook to fix PySide6 DLL loading order.
This module uses Python's import hooks to ensure the correct Qt6Core.dll
is loaded before any PySide6 modules are imported.
Critical: Must work correctly in both development and frozen (PyInstaller) modes.
"""

import os
import sys
import ctypes
import importlib
import importlib.abc
import importlib.machinery
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory, handling both dev and frozen modes.
    
    In frozen mode (PyInstaller), use the directory of the main script/exe.
    In development mode, use the project root relative to this module.
    """
    # Frozen mode: PyInstaller extracts to a temporary directory
    # The _MEIPASS attribute contains the extraction directory
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        # In frozen mode, go up from the extraction dir to find project root
        # Structure: .../dist/KP-AI-FENGSHUI.exe, temp dir is sibling
        meipass_path = Path(meipass)
        # The exe is in dist/, pyside6_packages is at project root
        # Go up one level from meipass to get closer
        candidate = meipass_path.parent.parent if meipass_path.parent.name == 'dist' else meipass_path.parent
        return candidate
    
    # Development mode: use the module's location
    # fix_dll_import.py is in the project root
    return Path(__file__).resolve().parent


class DLLDirectLoader(importlib.abc.MetaPathFinder):
    """Meta path finder that ensures correct DLL loading order.
    
    Ensures that when PySide6 modules are imported, the correct Qt6Core.dll
    from the bundled pyside6_packages directory is loaded first, preventing
    the "UCNV_TO_U_CALLBACK_SUBSTITUTE" error and other DLL conflicts.
    """
    
    def find_spec(self, fullname, path, target=None):
        """Called when Python imports a module.
        
        If we're about to import PySide6, ensure the correct Qt6Core.dll
        is loaded first.
        """
        # Only intercept PySide6 imports
        if fullname.startswith('PySide6'):
            # Ensure correct Qt6Core.dll is loaded
            self._ensure_correct_dll()
        
        # Continue with normal import
        return None
    
    def _ensure_correct_dll(self):
        """Ensure the correct Qt6Core.dll from pyside6_packages is loaded."""
        project_root = get_project_root()
        dll_path = str(project_root / 'pyside6_packages' / 'PySide6' / 'Qt6Core.dll')
        
        if os.path.exists(dll_path):
            dll_path_resolved = os.path.abspath(dll_path)
            print(f"[DLL钩子] 确保加载正确的 Qt6Core.dll: {dll_path_resolved}")
            try:
                # Use AddDllDirectory to add the bundled DLL directory to PATH
                # This takes precedence over system DLLs and temp extracted DLLs
                if hasattr(ctypes, 'windll'):
                    ctypes.windll.kernel32.AddDllDirectory(dll_path_resolved)
            except Exception as e:
                print(f"[DLL警告] 无法添加 DLL 目录: {e}")
        else:
            print(f"[DLL警告] Qt6Core.dll 未找到: {dll_path}")


# Register the hook at module level
# This will be called when Python starts importing modules

def setup_dll_hook():
    """Set up the DLL import hook."""
    # Get the existing meta path finders
    finders = sys.meta_path[:]
    
    # Check if our hook is already registered
    if any(isinstance(f, DLLDirectLoader) for f in finders):
        return  # Already registered
    
    # Insert our hook at the beginning (highest priority)
    sys.meta_path.insert(0, DLLDirectLoader())

# Set up the hook when this module is imported
setup_dll_hook()