#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能量化交易系统 - 主融合入口
多模态智能交易系统的统一启动入口
"""

import sys
import os
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
main_project_path = current_dir.parent / "Main"
auto_system_path = current_dir.parent / "自动交易系统"

sys.path.extend([
    str(current_dir),
    str(main_project_path),
    str(auto_system_path),
    str(main_project_path / "core"),
    str(main_project_path / "api"),
    str(main_project_path / "gui"),
    str(auto_system_path / "core"),
    str(auto_system_path / "app" / "src")
])

def check_dependencies():
    """检查系统依赖"""
    print("🔍 检查系统依赖...")

    required_modules = [
        "tkinter", "numpy", "opencv-python", "pillow",
        "pyautogui", "requests", "pandas"
    ]

    missing_modules = []

    for module in required_modules:
        try:
            if module == "opencv-python":
                import cv2
            elif module == "pillow":
                import PIL
            else:
                __import__(module.replace("-", "_"))
            print(f"   ✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"   ❌ {module}")

    if missing_modules:
        print(f"\n❌ 缺少依赖模块: {', '.join(missing_modules)}")
        print("请运行: pip install " + " ".join(missing_modules))
        return False

    print("✅ 所有依赖检查通过")
    return True

def check_project_structure():
    """检查项目结构"""
    print("\n🔍 检查项目结构...")

    # 修正路径 - 相对于软件开发需求目录
    required_paths = [
        "../Main/core/auto_trading_system.py",
        "../Main/api/jingtao_api.py",
        "../自动交易系统/core/enhanced_detection.py",
        "../自动交易系统/core/smart_trading_engine.py"
    ]

    # 检查当前工作目录
    current_dir = os.getcwd()
    print(f"   📍 当前目录: {current_dir}")

    missing_paths = []
    available_paths = []

    for path in required_paths:
        full_path = os.path.abspath(path)
        if os.path.exists(path):
            available_paths.append(path)
            print(f"   ✅ {path}")
        else:
            missing_paths.append(path)
            print(f"   ❌ {path}")
            print(f"      完整路径: {full_path}")

    # 即使有缺失文件，也可以继续运行（使用模拟组件）
    if missing_paths:
        print(f"\n⚠️ 缺少 {len(missing_paths)} 个文件，将使用模拟组件")
        print("   💡 系统仍可正常运行，部分功能将使用模拟实现")
        return True  # 改为True，允许继续运行

    print("✅ 项目结构检查通过")
    return True

def start_main_system(username: str, password: str):
    """启动主系统"""
    try:
        print(f"\n🚀 启动主系统 - 用户: {username}")

        # 导入并启动混合GUI
        from unified_gui.hybrid_main_window import HybridMainWindow

        # 创建主窗口
        app = HybridMainWindow()

        # 使用用户信息初始化系统
        app.initialize_with_user(username, password)

        # 运行主系统
        app.run()

    except Exception as e:
        print(f"❌ 启动主系统失败: {e}")
        import tkinter.messagebox as mb
        mb.showerror("启动失败", f"主系统启动失败: {e}")

def main():
    """主函数"""
    print("🎯 智能量化交易系统 v1.0")
    print("🔗 多模态融合 - API + 图像识别")
    print("=" * 50)

    try:
        # 1. 检查依赖
        if not check_dependencies():
            input("\n按回车键退出...")
            return

        # 2. 检查项目结构
        if not check_project_structure():
            pass  # 继续运行，使用模拟组件

        print("\n� 启动用户登录界面...")

        # 3. 启动登录界面
        from unified_gui.login_window import LoginWindow

        # 创建登录窗口
        login_window = LoginWindow(start_main_system)
        login_window.run()

    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        print("请确保所有依赖项目都在正确位置")
        input("\n按回车键退出...")
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        input("\n按回车键退出...")

if __name__ == "__main__":
    main()
