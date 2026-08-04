#!/usr/bin/env python3
"""Portable build script for 风水排盘专业工具"""
import subprocess
import sys
import os

os.chdir(r'D:\PythonProject\KP-AI-FENGSHUI')

PYINSTALLER_EXE = r'D:\anaconda3\Scripts\pyinstaller.exe'

cmd = [PYINSTALLER_EXE, 'build_release.spec', '--noconfirm', '--debug', 'all']
result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

log_file = r'D:\PythonProject\KP-AI-FENGSHUI\build_log.txt'
with open(log_file, 'w', encoding='utf-8') as f:
    f.write(f"Return: {result.returncode}\n")
    f.write(f"STDOUT ({len(result.stdout)} chars):\n")
    f.write(result.stdout)
    f.write(f"\nSTDERR ({len(result.stderr)} chars):\n")
    f.write(result.stderr)

print(f"Wrote {len(result.stdout)} stdout chars to {log_file}")
print(f"Return code: {result.returncode}")
