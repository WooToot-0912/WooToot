#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端口检查脚本
检查常用端口是否被占用
"""

import socket
import subprocess
import sys

def check_port(port):
    """检查指定端口是否被占用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            if result == 0:
                return True, "被占用"
            else:
                return False, "可用"
    except Exception as e:
        return False, f"检查失败: {e}"

def get_process_using_port(port):
    """获取占用指定端口的进程信息"""
    try:
        if sys.platform.startswith('win'):
            # Windows
            cmd = f'netstat -ano | findstr :{port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "未找到进程信息"
        else:
            # Linux/Mac
            cmd = f'lsof -i :{port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "未找到进程信息"
    except Exception as e:
        return f"获取进程信息失败: {e}"

def main():
    print("端口检查工具")
    print("=" * 50)
    
    # 检查常用端口
    ports_to_check = [8080, 8081, 8082, 3000, 5000, 8000]
    
    print("检查常用端口状态:")
    print("-" * 50)
    
    for port in ports_to_check:
        is_occupied, status = check_port(port)
        print(f"端口 {port:4d}: {status}")
        
        if is_occupied:
            print(f"  进程信息:")
            process_info = get_process_using_port(port)
            for line in process_info.split('\n'):
                if line.strip():
                    print(f"    {line.strip()}")
            print()
    
    print("=" * 50)
    print("建议:")
    print("1. 如果8080被占用，可以使用8081或8082")
    print("2. 如果所有端口都被占用，请关闭不必要的程序")
    print("3. 或者使用更高的端口号（如9000+）")
    
    # 交互式端口选择
    print("\n" + "=" * 50)
    print("端口选择建议:")
    
    available_ports = []
    for port in ports_to_check:
        is_occupied, _ = check_port(port)
        if not is_occupied:
            available_ports.append(port)
    
    if available_ports:
        print(f"推荐使用端口: {', '.join(map(str, available_ports))}")
        if 8081 in available_ports:
            print("✅ 8081端口可用，推荐使用")
        elif 8082 in available_ports:
            print("✅ 8082端口可用，推荐使用")
    else:
        print("❌ 所有检查的端口都被占用")
        print("建议使用更高的端口号（如9000+）")

if __name__ == "__main__":
    main() 