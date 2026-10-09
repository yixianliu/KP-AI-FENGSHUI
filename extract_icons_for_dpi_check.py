"""
从 EXE 中提取所有尺寸的图标用于高 DPI 目视检查
"""
import struct
import os
from PIL import Image
import io

exe_path = r'D:\PythonProject\KP-AI-FENGSHUI\dist\KP-AI-FENGSHUI.exe'
output_dir = r'D:\PythonProject\KP-AI-FENGSHUI\extracted_icons'

os.makedirs(output_dir, exist_ok=True)

with open(exe_path, 'rb') as f:
    data = f.read()

# 查找 ICO 签名
ico_sig = b'\x00\x00\x01\x00'
pos = data.find(ico_sig)

if pos == -1:
    print("未找到 ICO 资源")
    exit(1)

# 读取 ICO 头部
reserved, img_type, count = struct.unpack('<HHH', data[pos:pos+6])
print(f"找到 ICO 资源：{count} 个图像")

# 提取每个图像
for i in range(count):
    offset = pos + 6 + i * 16
    if offset + 16 > len(data):
        break
    
    w, h, colors, reserved2, planes, bitcount, size, offset_img = struct.unpack('<BBBBHHII', data[offset:offset+16])
    w = 256 if w == 0 else w
    h = 256 if h == 0 else h
    
    # 图像数据在 EXE 中的实际偏移
    img_offset = offset_img
    if img_offset + size <= len(data):
        img_data = data[img_offset:img_offset+size]
        
        # 保存为单独的 PNG 文件
        try:
            img = Image.open(io.BytesIO(img_data))
            # ICO 中的图像可能是 BMP 或 PNG 格式
            out_path = os.path.join(output_dir, f'icon_{w}x{h}_{bitcount}bpp.png')
            img.save(out_path)
            print(f"  ✅ {w}x{h} @ {bitcount}bpp -> {out_path}")
        except Exception as e:
            print(f"  ❌ {w}x{h} 解析失败: {e}")

print(f"\n提取完成，文件保存在: {output_dir}")
print("\n高 DPI 验证建议：")
print("1. 用图片查看器打开每个 PNG，检查边缘锐度、透明度")
print("2. 256x256 应无锯齿、无色带、透明过渡自然")
print("3. 16x16 在放大查看时应保持识别度")