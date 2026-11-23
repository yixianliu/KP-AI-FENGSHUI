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
# 模块名大小写敏感：PySide6 必须大写 P/S（曾误写 pyside6，会每次启动都静默重装依赖）
$PYTHON -c "import PySide6; import lunarcalendar; import numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[WARN] 部分依赖缺失，尝试安装..."
    $PYTHON -m pip install -r requirements.txt -q
fi

# 启动应用
echo ""
echo "[INFO] 启动 KP-AI-FENGSHUI ..."
echo ""
$PYTHON main.py
# 必须先落存退出码：直接写 echo "...$?" 时，$? 已被上一条 echo 重置为 0，
# 会把真实的启动失败报成「退出码: 0」，脚本也以 0 退出（对上层等于宣称成功）。
code=$?

if [ $code -ne 0 ]; then
    echo ""
    echo "[ERROR] 应用启动失败，退出码: $code"
    exit $code
fi
