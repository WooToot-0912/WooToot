#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
景陶易购API服务器安装脚本
"""

import os
import sys
import subprocess

def main():
    print("景陶易购API服务器安装脚本")
    print("=" * 40)
    
    # 安装依赖
    print("安装依赖包...")
    packages = ["flask", "flask-cors", "requests"]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} 安装成功")
        except:
            print(f"❌ {package} 安装失败")
    
    # 创建目录
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    print("\n安装完成!")
    print("启动服务器: python simple_server.py")

if __name__ == "__main__":
    main() 