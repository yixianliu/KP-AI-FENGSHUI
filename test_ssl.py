
import sys
import ssl
import certifi
import os

print("=== SSL 模块测试 ===")
print(f"Python 版本: {sys.version}")

# 检查 SSL 模块
print(f"
SSL 模块: {ssl.__file__}")
print(f"SSL 版本: {ssl.OPENSSL_VERSION}")

# 检查证书
cert_path = certifi.where()
print(f"
证书路径: {cert_path}")
print(f"证书文件存在: {os.path.exists(cert_path)}")

# 测试 SSL 上下文
try:
    ctx = ssl.create_default_context()
    ctx.load_default_certs()
    print("
✓ SSL 上下文创建成功")
except Exception as e:
    print(f"
✗ SSL 上下文创建失败: {e}")

# 测试 HTTPS 连接
import urllib.request
try:
    url = "https://httpbin.org/get"
    req = urllib.request.urlopen(url, timeout=10)
    print(f"
✓ HTTPS 连接成功: {req.status}")
except Exception as e:
    print(f"
✗ HTTPS 连接失败: {e}")

print("
=== 测试完成 ===")
