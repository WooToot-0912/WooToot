#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动真实高级界面 - 集成所有真实交易功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "unified_gui"))

def main():
    """启动真实高级界面"""
    try:
        print("🚀 启动智能量化交易系统真实高级版...")
        print("🔗 集成所有真实交易功能...")
        
        # 创建必要的目录
        config_dir = current_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        logs_dir = current_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # 导入并启动真实高级窗口
        from unified_gui.real_advanced_window import RealAdvancedWindow
        
        print("✅ 正在初始化真实高级界面...")
        app = RealAdvancedWindow()
        
        print("🎯 真实高级界面启动成功！")
        print("📋 功能说明:")
        print("   🔑 请先点击'登录'按钮登录系统")
        print("   📊 登录后可查看真实持仓和委托")
        print("   🚀 启动监控后开始真实交易")
        print("   💰 所有操作都是真实的，请谨慎操作")
        
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
