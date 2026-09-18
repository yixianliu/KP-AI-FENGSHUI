
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
