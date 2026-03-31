#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
景陶易购API服务器安装脚本
自动安装依赖包和配置环境
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """打印安装横幅"""
    print("=" * 60)
    print("景陶易购共享API服务器 - 自动安装脚本")
    print("=" * 60)
    print()

def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    
    if sys.version_info < (3, 7):
        print(f"❌ Python版本过低: {sys.version}")
        print("   需要Python 3.7或更高版本")
        return False
    
    print(f"✅ Python版本: {sys.version}")
    return True

def install_pip_packages():
    """安装pip包"""
    print("\n安装Python依赖包...")
    
    packages = [
        "flask>=2.3.0",
        "flask-cors>=4.0.0", 
        "requests>=2.31.0",
        "werkzeug>=2.3.0"
    ]
    
    for package in packages:
        print(f"安装 {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ {package} 安装失败: {e}")
            return False
    
    return True

def create_directories():
    """创建必要的目录"""
    print("\n创建必要的目录...")
    
    directories = [
        "logs",
        "data", 
        "config"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建目录: {directory}")
        else:
            print(f"✅ 目录已存在: {directory}")

def create_config_file():
    """创建配置文件"""
    print("\n创建配置文件...")
    
    config_content = '''{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false,
    "workers": 4,
    "max_connections": 1000,
    "timeout": 30
  },
  "security": {
    "enable_rate_limit": true,
    "max_requests_per_minute": 100,
    "enable_api_key": true,
    "session_timeout": 3600,
    "max_concurrent_sessions": 10
  },
  "database": {
    "type": "sqlite",
    "path": "data/users.db",
    "backup_enabled": true,
    "backup_interval": 86400
  },
  "logging": {
    "level": "INFO",
    "file": "logs/api_server.log",
    "max_size": 10485760,
    "backup_count": 5
  },
  "trading": {
    "base_url": "https://zxyw.ceramic-copyright.com/apigateway",
    "kline_url": "https://zxyt.ceramic-copyright.com/qtfront_tq",
    "market_id": 28,
    "max_order_amount": 100000,
    "enable_risk_control": true,
    "daily_loss_limit": 1000,
    "max_daily_trades": 100
  }
}'''
    
    config_file = Path("config/server_config.json")
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not config_file.exists():
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ 配置文件创建成功: config/server_config.json")
    else:
        print("✅ 配置文件已存在: config/server_config.json")

def create_startup_scripts():
    """创建启动脚本"""
    print("\n创建启动脚本...")
    
    # Windows批处理文件
    if platform.system() == "Windows":
        bat_content = '''@echo off
chcp 65001 >nul
echo ========================================
echo 景陶易购共享API服务器
echo ========================================
echo.
echo 启动服务器...
echo 地址: http://localhost:8080
echo 按 Ctrl+C 停止服务器
echo.

python simple_server.py

pause'''
        
        with open("start_server.bat", 'w', encoding='utf-8') as f:
            f.write(bat_content)
        print("✅ Windows启动脚本创建成功: start_server.bat")
    
    # Linux/Mac shell脚本
    shell_content = '''#!/bin/bash
echo "========================================"
echo "景陶易购共享API服务器"
echo "========================================"
echo ""
echo "启动服务器..."
echo "地址: http://localhost:8080"
echo "按 Ctrl+C 停止服务器"
echo ""

python3 simple_server.py'''
    
    shell_file = Path("start_server.sh")
    with open(shell_file, 'w', encoding='utf-8') as f:
        f.write(shell_content)
    
    # 设置执行权限
    if platform.system() != "Windows":
        os.chmod(shell_file, 0o755)
    
    print("✅ Shell启动脚本创建成功: start_server.sh")

def test_installation():
    """测试安装"""
    print("\n测试安装...")
    
    try:
        import flask
        import flask_cors
        import requests
        print("✅ 所有依赖包导入成功")
        return True
    except ImportError as e:
        print(f"❌ 依赖包导入失败: {e}")
        return False

def print_completion():
    """打印完成信息"""
    print("\n" + "=" * 60)
    print("🎉 安装完成!")
    print("=" * 60)
    print()
    print("下一步操作:")
    print("1. 启动服务器:")
    
    if platform.system() == "Windows":
        print("   start_server.bat")
    else:
        print("   ./start_server.sh")
        print("   或")
        print("   python3 simple_server.py")
    
    print()
    print("2. 测试API:")
    print("   http://localhost:8080/api/health")
    print()
    print("3. 运行客户端示例:")
    print("   python3 client_example.py")
    print()
    print("4. 查看详细文档:")
    print("   README.md")
    print()
    print("如有问题，请查看README.md或联系开发者")

def main():
    """主函数"""
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        print("\n❌ 安装失败: Python版本不兼容")
        return False
    
    # 安装依赖包
    if not install_pip_packages():
        print("\n❌ 安装失败: 依赖包安装失败")
        return False
    
    # 创建目录
    create_directories()
    
    # 创建配置文件
    create_config_file()
    
    # 创建启动脚本
    create_startup_scripts()
    
    # 测试安装
    if not test_installation():
        print("\n❌ 安装失败: 测试失败")
        return False
    
    # 打印完成信息
    print_completion()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n安装被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n安装过程中发生错误: {e}")
        sys.exit(1) 