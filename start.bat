@echo off
REM ============================================================
REM KP-AI-FENGSHUI 启动脚本 (Windows)
REM 版本：v1.0
REM 编制日期：2026-09-17
REM 用途：一键启动应用，自动检测 Python 环境和虚拟环境
REM ============================================================

chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8

echo ========================================
echo   KP-AI-FENGSHUI v1.0 启动器
echo   仅供文化研究参考，不构成决策依据
echo ========================================
echo.

REM 检测当前目录
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

REM 检测虚拟环境
if exist "%PROJECT_DIR%\venv\Scripts\python.exe" (
    echo [OK] 检测到虚拟环境 venv
    set PYTHON="%PROJECT_DIR%\venv\Scripts\python.exe"
) else if exist "%PROJECT_DIR%\env\Scripts\python.exe" (
    echo [OK] 检测到虚拟环境 env
    set PYTHON="%PROJECT_DIR%\env\Scripts\python.exe"
) else (
    where python >nul 2>&1
    REM 必须用 errorlevel 动态判断（不加 %）：写在 () 复合块内的 %ERRORLEVEL%
    REM 会在整块解析时提前展开，拿到的是 where 执行前的旧值，导致判定失真。
    if not errorlevel 1 (
        echo [WARN] 未检测到虚拟环境，使用系统 Python
        set PYTHON=python
    ) else (
        echo [ERROR] 未找到 Python 解释器，请先安装 Python 3.10+
        pause
        exit /b 1
    )
)

REM 检测依赖
echo.
echo [INFO] 检查依赖...
REM 检测依赖：探测核心包能否导入（纯探测，不产生副作用）。
REM 目的：仅当探测失败（依赖缺失/损坏）时才执行 pip install，避免每次启动都重装。
REM 注意：模块名大小写敏感，PySide6 必须大写 P/S（曾误写为 pyside6，导致每次启动都判为缺依赖并静默重装）。
%PYTHON% -c "import PySide6; import lunarcalendar; import numpy; print('[OK] 核心依赖已安装')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [WARN] 部分依赖缺失，尝试安装...
    %PYTHON% -m pip install -r requirements.txt -q
)

REM 启动应用
echo.
echo [INFO] 启动 KP-AI-FENGSHUI ...
echo.
%PYTHON% main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] 应用启动失败，退出码: %ERRORLEVEL%
    pause
)
