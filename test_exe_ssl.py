
import sys
import os

# 添加打包路径
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
    
    # 尝试导入SSL
    try:
        import ssl
        print(f'SSL模块导入成功: {ssl.__file__}')
        print(f'SSL版本: {ssl.OPENSSL_VERSION}')
    except Exception as e:
        print(f'SSL导入失败: {e}')
        
    try:
        import certifi
        print(f'certifi导入成功: {certifi.where()}')
    except Exception as e:
        print(f'certifi导入失败: {e}')
        
    # 测试HTTPS连接
    try:
        import urllib.request
        req = urllib.request.urlopen('https://httpbin.org/get', timeout=5)
        print(f'HTTPS连接成功: {req.status}')
    except Exception as e:
        print(f'HTTPS连接失败: {e}')
