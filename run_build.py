#!/usr/bin/env python3
import sys
import os
import subprocess

os.chdir('D:\\PythonProject\\KP-AI-FENGSHUI')

# 使用系统 PyInstaller
result = subprocess.run(
    ['/d/anaconda3/Scripts/pyinstaller.exe', 'build_release.spec', '--noconfirm', '--debug', 'all'],
    capture_output=True,
    text=True,
    timeout=300
)

# 写入文件
with open('build_log.txt', 'w', encoding='utf-8') as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR:\n")
    f.write(result.stderr)
    f.write(f"\nReturn code: {result.returncode}\n")

print(f"Wrote {len(result.stdout)} stdout chars and {len(result.stderr)} stderr chars to build_log.txt")
