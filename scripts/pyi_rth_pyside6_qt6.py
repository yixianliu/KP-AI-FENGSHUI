"""
PyInstaller runtime hook：在 frozen 环境下预加载 Qt6 核心 DLL，解决 Python 3.13
Windows 签名验证和系统 DLL 冲突问题。

原理：
- Python 3.13 对 .pyd 导入时的 DLL 查找执行签名验证（LOAD_LIBRARY_REQUIRE_SIGNED）
- kernel32.LoadLibraryW() 绕过签名验证，将 DLL 加载到进程地址空间
- 使用绝对路径预加载我们自己的 ICU/Qt 等 DLL，确保优先于系统 DLL
- 预加载核心 DLL 后保持句柄不释放，使 DLL 常驻进程内存，阻止系统旧版覆盖
- _setupQtDirectories() 负责设置 DLL 搜索路径，应正常执行

注意：本 hook 由 PyInstaller 自动注入，不需手动调用。
"""
import os
import sys


def _pyi_rthook():
    # 仅在 frozen 环境中执行
    meipass = getattr(sys, '_MEIPASS', None)
    if not meipass or not os.path.isdir(meipass):
        return

    pydir = os.path.join(meipass, 'PySide6')
    shiboken_dir = os.path.join(meipass, 'shiboken6')

    # ── 1. 将 meipass 和 PySide6 目录加入 PATH ──
    current_path = os.environ.get('PATH', '')
    for d in [meipass, pydir]:
        if d and d not in current_path:
            os.environ['PATH'] = d + os.pathsep + current_path

    # ── 2. 将 meipass 加入 sys.path ──
    if meipass not in sys.path:
        sys.path.insert(0, meipass)

    # ── 3. 使用绝对路径预加载关键 DLL，并保持句柄（不释放） ──
    import ctypes
    kernel32 = ctypes.windll.kernel32

    # 需要绝对路径预加载的 DLL 列表（优先级高于系统 DLL）
    critical_dlls = [
        # ICU 国际化库（必须先用绝对路径加载，防止系统旧版抢占）
        # Qt6Core 动态链接 icuuc/icudt/icuin 等（无后缀），需同时加载有/无后缀版本
        ('icuuc.dll',   [meipass, pydir]),
        ('icuuc73.dll', [meipass, pydir]),
        ('icudt.dll',   [meipass, pydir]),
        ('icudt73.dll', [meipass, pydir]),
        ('icuin.dll',   [meipass, pydir]),
        ('icuin73.dll', [meipass, pydir]),
        ('icuio.dll',   [meipass, pydir]),
        ('icuio73.dll', [meipass, pydir]),
        ('icutu.dll',   [meipass, pydir]),
        ('icutu73.dll', [meipass, pydir]),
        # VC 运行时
        ('vcruntime140.dll', [meipass]),
        ('vcruntime140_1.dll', [meipass]),
        ('msvcp140.dll', [meipass]),
        ('vccorlib140.dll', [meipass]),
        ('concrt140.dll', [meipass]),
        # OpenSSL
        ('libssl-3-x64.dll', [meipass]),
        ('libcrypto-3-x64.dll', [meipass]),
        # PySide6/shiboken6 ABI
        ('pyside6.abi3.dll', [pydir, meipass]),
        ('pyside6qml.abi3.dll', [pydir]),
        ('python3.dll', [meipass]),
        ('shiboken6.abi3.dll', [shiboken_dir, meipass]),
        # Qt6 核心库
        ('Qt6Core.dll', [meipass, pydir]),
        ('Qt6Gui.dll', [meipass, pydir]),
        ('Qt6Widgets.dll', [meipass, pydir]),
        ('Qt6Qml.dll', [meipass, pydir]),
        ('Qt6Quick.dll', [meipass, pydir]),
    ]

    def _load_absolute(name, search_dirs):
        """用绝对路径加载 DLL 并保持句柄，确保优先于系统 DLL"""
        for d in search_dirs:
            p = os.path.join(d, name)
            if os.path.isfile(p):
                try:
                    h = kernel32.LoadLibraryW(os.path.abspath(p))
                    if h:
                        return True
                except OSError:
                    pass
        return False

    for dll_name, dirs in critical_dlls:
        _load_absolute(dll_name, dirs)

    # ── 4. 设置 Qt 平台插件路径 ──
    platform_candidates = [
        os.path.join(pydir, 'plugins', 'platforms'),
        os.path.join(pydir, 'plugins'),
        pydir,
        os.path.join(meipass, 'plugins', 'platforms'),
        os.path.join(meipass, 'plugins'),
        meipass,
    ]
    for pd in platform_candidates:
        if os.path.isdir(pd) and os.path.isfile(os.path.join(pd, 'qwindows.dll')):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = pd
            break

    # ── 5. 设置 Qt 插件路径 ──
    plugins_candidates = [
        os.path.join(pydir, 'plugins'),
        os.path.join(meipass, 'plugins'),
    ]
    for pd in plugins_candidates:
        if os.path.isdir(pd):
            os.environ.setdefault('QT_PLUGIN_PATH', pd)
            break


# PyInstaller 运行时 hook 入口
_pyi_rthook()
