def _pyi_rthook():
    """SSL 运行时钩子 - 确保 SSL 模块和证书在打包应用中正确初始化"""
    try:
        import ssl
        import certifi
        import os
        
        # 设置SSL证书路径
        ssl_path = certifi.where()
        os.environ['SSL_CERT_FILE'] = ssl_path
        os.environ['CURL_CA_BUNDLE'] = ssl_path
        
        # 验证SSL模块是否可用
        try:
            ctx = ssl.create_default_context()
            ctx.load_default_certs()
        except Exception as e:
            print(f"Warning: SSL initialization issue: {e}")
    except Exception as e:
        print(f"Warning: SSL hook failed: {e}")
