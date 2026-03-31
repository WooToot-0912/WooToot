#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能交易系统主应用入口
整合所有模块，提供统一的启动接口
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 添加当前目录到路径以支持相对导入
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# 修复导入路径
try:
    from trading_gui import SmartTradingWindow
except ImportError:
    from .trading_gui import SmartTradingWindow


def setup_logging():
    """设置日志系统"""
    try:
        # 确保logs目录存在
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'trading_system.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info("日志系统初始化完成")
        
    except Exception as e:
        print(f"日志系统初始化失败: {e}")


def setup_application():
    """设置应用程序"""
    try:
        # 创建QApplication实例
        app = QApplication(sys.argv)
        
        # 设置应用程序属性
        app.setApplicationName("景陶易购智能交易系统")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("SmartTrading")
        app.setOrganizationDomain("smarttrading.local")
        
        # 设置高DPI支持
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        return app
        
    except Exception as e:
        print(f"应用程序初始化失败: {e}")
        return None


def main():
    """主函数"""
    try:
        print("🚀 启动景陶易购智能交易系统...")
        
        # 1. 设置日志
        setup_logging()
        logger = logging.getLogger(__name__)
        
        # 2. 设置应用程序
        app = setup_application()
        if not app:
            logger.error("应用程序初始化失败")
            return 1
        
        logger.info("应用程序初始化成功")
        
        # 3. 创建主窗口
        try:
            main_window = SmartTradingWindow()
            main_window.show()
            logger.info("主窗口创建成功")
            
        except Exception as e:
            logger.error(f"主窗口创建失败: {e}")
            return 1
        
        # 4. 显示启动信息
        print("✅ 系统启动成功")
        print("📊 主窗口已显示")
        print("ℹ️  请在GUI界面中操作")
        print("\n按 Ctrl+C 可以安全退出程序")
        
        # 5. 运行应用程序
        try:
            exit_code = app.exec_()
            logger.info(f"应用程序正常退出，退出代码: {exit_code}")
            return exit_code
            
        except KeyboardInterrupt:
            logger.info("收到键盘中断信号")
            print("\n⏹️ 收到退出信号，正在安全关闭...")
            return 0
            
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        if 'logger' in locals():
            logger.error(f"系统启动失败: {e}")
        return 1


def run_console_mode():
    """控制台模式运行（用于调试）"""
    try:
        print("🔧 启动控制台调试模式...")
        
        # 设置简单日志
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        # 导入交易引擎
        try:
            from trading_engine import SmartTradingEngine
        except ImportError:
            from .trading_engine import SmartTradingEngine
        
        # 创建交易引擎
        engine = SmartTradingEngine()
        logger.info("交易引擎创建成功")
        
        # 测试客户端连接
        if engine.start_client():
            print("✅ 客户端连接成功")
            
            # 测试坐标
            if engine.test_coordinates():
                print("✅ 坐标测试通过")
            else:
                print("⚠️ 坐标测试失败")
                
        else:
            print("❌ 客户端连接失败")
        
        print("🔧 控制台模式测试完成")
        return 0
        
    except Exception as e:
        print(f"❌ 控制台模式失败: {e}")
        return 1


def run_test_mode():
    """测试模式运行"""
    try:
        print("🧪 启动测试模式...")
        
        # 设置测试日志
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        # 测试各个模块的导入
        test_results = {}
        
        # 测试交易引擎
        try:
            try:
                from trading_engine import SmartTradingEngine
            except ImportError:
                from .trading_engine import SmartTradingEngine
            engine = SmartTradingEngine()
            test_results['trading_engine'] = True
            logger.info("✅ 交易引擎模块测试通过")
        except Exception as e:
            test_results['trading_engine'] = False
            logger.error(f"❌ 交易引擎模块测试失败: {e}")
        
        # 测试交易线程
        try:
            try:
                from trading_thread import TradingThread, AdvancedTradingThread
            except ImportError:
                from .trading_thread import TradingThread, AdvancedTradingThread
            test_results['trading_thread'] = True
            logger.info("✅ 交易线程模块测试通过")
        except Exception as e:
            test_results['trading_thread'] = False
            logger.error(f"❌ 交易线程模块测试失败: {e}")
        
        # 测试GUI模块
        try:
            try:
                from trading_gui import SmartTradingWindow
            except ImportError:
                from .trading_gui import SmartTradingWindow
            test_results['trading_gui'] = True
            logger.info("✅ GUI模块测试通过")
        except Exception as e:
            test_results['trading_gui'] = False
            logger.error(f"❌ GUI模块测试失败: {e}")
        
        # 显示测试结果
        print("\n📊 测试结果总结:")
        for module, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {module}: {status}")
        
        # 计算成功率
        success_rate = sum(test_results.values()) / len(test_results) * 100
        print(f"\n🎯 总体成功率: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 所有模块测试通过！")
            return 0
        else:
            print("⚠️ 部分模块测试失败，请检查错误信息")
            return 1
            
    except Exception as e:
        print(f"❌ 测试模式失败: {e}")
        return 1


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "console":
            # 控制台模式
            exit_code = run_console_mode()
        elif mode == "test":
            # 测试模式
            exit_code = run_test_mode()
        elif mode == "gui" or mode == "main":
            # GUI模式（默认）
            exit_code = main()
        else:
            print("使用方法:")
            print("  python main_app.py           # GUI模式（默认）")
            print("  python main_app.py gui       # GUI模式")
            print("  python main_app.py console   # 控制台调试模式")
            print("  python main_app.py test      # 测试模式")
            exit_code = 1
    else:
        # 默认GUI模式
        exit_code = main()
    
    sys.exit(exit_code)