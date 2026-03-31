#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
景陶易购自动交易系统 - 稳定版主入口
优化Python 3.9兼容性，增强错误处理
"""

import sys
import os
import traceback
from pathlib import Path

# 确保Python版本兼容性
if sys.version_info < (3, 7):
    print("❌ 需要Python 3.7或更高版本")
    sys.exit(1)

print(f"🐍 Python版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# 添加必要路径到Python路径
project_root = Path(__file__).parent
parent_root = project_root.parent  # 上级目录
src_path = project_root / "src"
utils_path = parent_root / "utils"
tools_path = parent_root / "tools"
core_path = parent_root / "core"

# 添加所有必要路径
for path in [str(src_path), str(utils_path), str(tools_path), str(core_path), str(project_root)]:
    if path not in sys.path:
        sys.path.insert(0, path)

def check_dependencies():
    """检查必要的依赖"""
    print("🔍 检查系统依赖...")
    
    missing_deps = []
    
    # 检查PyQt5
    try:
        import PyQt5
        print("✅ PyQt5 已安装")
        
        # 设置Qt插件路径以解决平台插件问题
        try:
            import PyQt5.QtCore
            qt_plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
            if os.path.exists(qt_plugin_path):
                os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
                print(f"✅ Qt插件路径已设置: {qt_plugin_path}")
            else:
                # 尝试另一个可能的路径
                alt_path = os.path.join(os.path.dirname(PyQt5.__file__), "Qt", "plugins")
                if os.path.exists(alt_path):
                    os.environ['QT_PLUGIN_PATH'] = alt_path
                    print(f"✅ Qt插件路径已设置: {alt_path}")
                else:
                    print("⚠️ 未找到Qt插件路径，可能会出现显示问题")
        except Exception as e:
            print(f"⚠️ Qt插件路径设置失败: {e}")
            
    except ImportError:
        missing_deps.append("PyQt5")
        print("❌ PyQt5 未安装")
    
    # 检查其他核心依赖
    try:
        import numpy
        print("✅ numpy 已安装")
    except ImportError:
        missing_deps.append("numpy")
        print("❌ numpy 未安装")
    
    try:
        import cv2
        print("✅ opencv-python 已安装")
    except ImportError:
        missing_deps.append("opencv-python")
        print("❌ opencv-python 未安装")
    
    try:
        import PIL
        print("✅ Pillow 已安装")
    except ImportError:
        missing_deps.append("Pillow")
        print("❌ Pillow 未安装")
    
    try:
        import pyautogui
        print("✅ pyautogui 已安装")
    except ImportError:
        missing_deps.append("pyautogui")
        print("❌ pyautogui 未安装")
    
    # 可选依赖
    try:
        import pytesseract
        print("✅ pytesseract 已安装 (可选)")

        # 配置Tesseract路径
        try:
            # 导入tesseract配置模块
            tesseract_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils')
            if tesseract_path not in sys.path:
                sys.path.insert(0, tesseract_path)
            
            from tesseract_config import configure_pytesseract
            if configure_pytesseract():
                print("✅ Tesseract配置成功")
            else:
                print("⚠️ Tesseract配置失败，OCR功能可能不可用")
        except Exception as e:
            print(f"⚠️ Tesseract配置异常: {e}")
            # 如果tesseract配置失败，继续运行程序（不影响核心功能）

    except ImportError:
        print("⚠️ pytesseract 未安装 (可选，OCR功能不可用)")
    
    if missing_deps:
        print("\n❌ 缺少必要依赖:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n💡 请安装缺少的依赖:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    
    return True

def safe_import_trading_modules():
    """安全导入交易模块"""
    print("📦 导入交易模块...")
    
    try:
        from trading.trading_engine import SmartTradingEngine
        print("✅ 交易引擎模块导入成功")
        return {'engine': SmartTradingEngine}
    except Exception as e:
        print(f"❌ 交易引擎模块导入失败: {e}")
        traceback.print_exc()
        return None

def run_gui_mode_safe():
    """安全运行GUI模式"""
    print("🖥️ 启动GUI模式...")
    
    try:
        # 导入PyQt5
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("智能交易系统")
        app.setApplicationVersion("2.0")
        
        print("✅ Qt应用创建成功")
        
        # 尝试导入GUI模块
        try:
            from trading.trading_gui import SmartTradingWindow
            print("✅ GUI模块导入成功")
            
            # 添加调试：验证导入的模块路径
            import trading.trading_gui
            print(f"🔍 GUI模块路径: {trading.trading_gui.__file__}")
            
            # 验证K线检测模块
            try:
                from trading.candlestick_detector import CandlestickColorDetector
                import trading.candlestick_detector
                print(f"🔍 K线检测器模块路径: {trading.candlestick_detector.__file__}")
                print("✅ K线检测器模块导入成功")
                
                # 创建一个测试实例来验证新版本
                test_detector = CandlestickColorDetector()
                print("✅ K线检测器测试实例创建成功")
            except Exception as e:
                print(f"❌ K线检测器模块导入失败: {e}")
            
            # 创建主窗口
            window = SmartTradingWindow()
            window.show()
            
            print("✅ GUI窗口已显示")
            print("🎯 系统就绪，请在界面中操作")
            
            # 运行应用
            return app.exec_()
            
        except Exception as e:
            print(f"❌ GUI模块初始化失败: {e}")
            print("📋 错误详情:")
            traceback.print_exc()
            
            # 显示简化的错误信息窗口
            from PyQt5.QtWidgets import QMessageBox, QWidget
            
            error_widget = QWidget()
            QMessageBox.critical(
                error_widget,
                "启动失败",
                f"GUI模块初始化失败:\n{str(e)}\n\n请检查控制台输出获取详细信息。"
            )
            return 1
            
    except ImportError as e:
        print(f"❌ PyQt5导入失败: {e}")
        print("💡 请安装PyQt5: pip install PyQt5")
        return 1
    except Exception as e:
        print(f"❌ GUI模式启动失败: {e}")
        traceback.print_exc()
        return 1

def run_console_mode_safe():
    """安全运行控制台模式"""
    print("🔧 启动控制台模式...")
    
    try:
        modules = safe_import_trading_modules()
        if not modules:
            return 1
        
        print("🔧 初始化交易引擎...")
        engine = modules['engine']()
        
        print("🔍 测试系统功能...")
        
        # 基本功能测试
        config = engine.load_coordinate_config()
        print(f"✅ 坐标配置: {len(config)} 个按钮")
        
        # 客户端连接测试
        if engine.start_client():
            print("✅ 客户端检测成功")
            
            # 坐标测试
            if engine.test_coordinates():
                print("✅ 坐标验证通过")
            else:
                print("⚠️ 坐标验证有问题，但可以继续")
        else:
            print("⚠️ 客户端未连接（景陶易购客户端可能未运行）")
        
        print("📊 系统状态检查完成")
        return 0
        
    except Exception as e:
        print(f"❌ 控制台模式失败: {e}")
        traceback.print_exc()
        return 1

def main():
    """主函数"""
    print("🚀 景陶易购智能交易系统 v2.0 (稳定版)")
    print("=" * 55)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，无法启动")
        return 1
    
    print("\n✅ 依赖检查通过")
    
    # 检查命令行参数
    mode = "gui"
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    print(f"🎯 启动模式: {mode}")
    
    try:
        if mode == "console":
            return run_console_mode_safe()
        elif mode == "test":
            print("🧪 运行测试模式...")
            # 导入并运行测试
            try:
                exec(open("test_modules.py").read())
                return 0
            except FileNotFoundError:
                print("❌ 测试模块不存在")
                return 1
        else:
            # 默认GUI模式
            return run_gui_mode_safe()
            
    except KeyboardInterrupt:
        print("\n👋 用户中断操作")
        return 0
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    
    print("\n" + "=" * 55)
    if exit_code == 0:
        print("✅ 程序正常结束")
    else:
        print(f"❌ 程序异常结束 (退出代码: {exit_code})")
    
    input("\n按回车键退出...")  # 暂停，便于查看输出
    sys.exit(exit_code)