import sys
import os
os.chdir(r'D:\PythonProject\KP-AI-FENGSHUI')
sys.argv = ['pyinstaller', 'build_release.spec', '--noconfirm', '--debug', 'all']
from PyInstaller.__main__ import run
result = run(sys.argv[1:])
print('Build result:', result)
