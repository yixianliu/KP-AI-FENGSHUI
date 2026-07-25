import os
base = r"D:\PythonProject\KP-AI-FENGSHUI\core"
# 直接拼接绝对路径用 open 读取（os.path.exists 在本环境对该文件异常，但 open 可用）
p = os.path.join(base, "_baizi_compat.py")
with open(p, encoding="utf-8") as f:
    src = f.read()
print("LINES:", len(src.split('\n')))
print("=" * 60)
print(src)
