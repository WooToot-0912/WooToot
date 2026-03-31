#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动高级界面 - 智能量化交易系统高级版启动脚本
"""

import sys
import os
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "unified_gui"))

def main():
    """启动高级界面"""
    try:
        print("🚀 启动智能量化交易系统高级版...")
        
        # 创建必要的目录
        config_dir = current_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        logs_dir = current_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # 导入并启动高级主窗口
        from unified_gui.advanced_main_window import AdvancedMainWindow
        
        print("✅ 正在初始化高级界面...")
        app = AdvancedMainWindow()
        
        print("🎯 高级界面启动成功！")
        app.run()
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保所有依赖模块都已正确安装")
        input("按回车键退出...")
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()
