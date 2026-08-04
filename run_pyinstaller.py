import sys
import os
from PyInstaller.archive.wip import exe_file
from PyInstaller.building.main import main
from PyInstaller.utils.hooks import get_package_version

# 设置工作目录
os.chdir('D:/PythonProject/KP-AI-FENGSHUI')

# 运行 PyInstaller
args = ['--debug=all', 'build_release.spec']
print("Running PyInstaller with args:", args)
result = main(args)
print("PyInstaller result:", result)
sys.exit(0 if result else 1)
