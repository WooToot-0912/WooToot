#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动增强界面 - 基于现有工作代码的增强版界面
"""

import sys
import os
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "unified_gui"))

def main():
    """启动增强界面"""
    try:
        print("🚀 启动智能量化交易系统增强版...")
        print("🔗 基于现有工作代码，集成真实功能...")
        
        # 创建必要的目录
        config_dir = current_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        logs_dir = current_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # 导入并启动混合主窗口
        from unified_gui.hybrid_main_window import HybridMainWindow
        
        print("✅ 正在初始化增强界面...")
        app = HybridMainWindow()
        
        print("🎯 增强界面启动成功！")
        print("📋 功能说明:")
        print("   🎯 多模态交易融合 (API + 图像识别)")
        print("   📊 实时监控和信号检测")
        print("   🛡️ 风险管理和参数控制")
        print("   📝 详细的操作日志")
        print("   ⚙️ 丰富的自定义设置")
        
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
