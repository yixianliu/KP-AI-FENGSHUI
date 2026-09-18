#!/bin/bash
# ============================================================
# KP-AI-FENGSHUI 启动脚本 (Linux/macOS)
# 版本：v1.0
# 编制日期：2026-09-17
# ============================================================

export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  KP-AI-FENGSHUI v1.0 启动器"
echo "  仅供文化研究参考，不构成决策依据"
echo "========================================"
echo ""

# 检测虚拟环境
if [ -f "./venv/bin/python" ]; then
    PYTHON="./venv/bin/python"
    echo "[OK] 检测到虚拟环境 venv"
elif [ -f "./env/bin/python" ]; then
    PYTHON="./env/bin/python"
    echo "[OK] 检测到虚拟环境 env"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
    echo "[WARN] 使用系统 Python3"
else
    echo "[ERROR] 未找到 Python 解释器"
    exit 1
fi

# 检查依赖
echo ""
echo "[INFO] 检查依赖..."
$PYTHON -c "import pyside6; import lunarcalendar; import numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[WARN] 部分依赖缺失，尝试安装..."
    $PYTHON -m pip install -r requirements.txt -q
fi

# 启动应用
echo ""
echo "[INFO] 启动 KP-AI-FENGSHUI ..."
echo ""
$PYTHON main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] 应用启动失败，退出码: $?"
    exit 1
fi
