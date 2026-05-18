#!/usr/bin/env python3
"""一键启动金融终端"""
import subprocess
import sys
import os

# 确保在项目目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*50)
print("📈 金融终端 - 启动中...")
print("="*50)

# 检查依赖
try:
    import akshare
    print("✓ akshare 已安装")
except ImportError:
    print("✗ 正在安装 akshare...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "akshare", "-q"])

try:
    import fastapi
    print("✓ fastapi 已安装")
except ImportError:
    print("✗ 正在安装 fastapi...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "-q"])

print("\n正在下载股票数据...")
print("(首次运行可能需要几分钟)\n")

# 下载数据
subprocess.run([sys.executable, "download_data.py"])

print("\n启动 Web 服务...")
print("="*50)
print("🌐 访问: http://localhost:8080")
print("📱 手机访问: http://<电脑IP>:8080")
print("="*50 + "\n")

# 启动服务
subprocess.run(["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9000"])