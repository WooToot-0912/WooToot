#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能交易系统 - 重构后的主模块
保持向后兼容性，同时使用新的模块化架构

此文件现在作为新架构的入口点，主要功能已拆分到：
- trading_engine.py: 核心交易引擎
- trading_thread.py: 交易监测线程  
- trading_gui.py: GUI界面
- main_app.py: 应用主入口
"""

import sys
import warnings
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入新的模块化组件
try:
    from .trading_engine import SmartTradingEngine
    from .trading_thread import TradingThread, AdvancedTradingThread
    from .trading_gui import SmartTradingWindow
    from .main_app import main as run_main_app
    
    # 为了向后兼容，重新导出主要类
    __all__ = [
        'SmartTradingEngine',
        'TradingThread', 
        'AdvancedTradingThread',
        'SmartTradingWindow',
        'main'
    ]
    
    print("✅ 新模块化架构加载成功")
    
except ImportError as e:
    # 如果新模块无法导入，显示错误信息
    print(f"❌ 新模块加载失败: {e}")
    print("⚠️ 请检查项目结构是否正确")
    raise


def main():
    """
    主函数 - 兼容性入口
    
    现在重定向到新的main_app.py
    """
    warnings.warn(
        "直接运行smart_trading.py已弃用，请使用 main_app.py 或新的 main.py",
        DeprecationWarning,
        stacklevel=2
    )
    
    print("🔄 重定向到新的应用入口...")
    return run_main_app()


# 为了完全向后兼容，保留一些重要的别名
class SmartTradingEngine_Legacy(SmartTradingEngine):
    """Legacy wrapper for SmartTradingEngine"""
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "使用SmartTradingEngine_Legacy已弃用，请直接使用SmartTradingEngine",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class TradingThread_Legacy(TradingThread):
    """Legacy wrapper for TradingThread"""
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "使用TradingThread_Legacy已弃用，请直接使用TradingThread",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class SmartTradingWindow_Legacy(SmartTradingWindow):
    """Legacy wrapper for SmartTradingWindow"""
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "使用SmartTradingWindow_Legacy已弃用，请直接使用SmartTradingWindow",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


def show_migration_guide():
    """显示迁移指南"""
    guide = """
    🔄 项目架构升级指南
    
    原有的 smart_trading.py (2241行) 已被重构为模块化架构：
    
    📁 新的文件结构：
    ├── trading_engine.py     # 核心交易引擎逻辑
    ├── trading_thread.py     # 交易监测线程
    ├── trading_gui.py        # GUI界面组件
    ├── main_app.py          # 应用主入口
    └── smart_trading.py     # 兼容性模块（本文件）
    
    🚀 推荐使用方式：
    
    1. 直接运行新的主应用：
       python src/trading/main_app.py
    
    2. 使用项目根目录的主入口：
       python main.py
    
    3. 导入特定模块：
       from src.trading.trading_engine import SmartTradingEngine
       from src.trading.trading_gui import SmartTradingWindow
    
    ✨ 新架构优势：
    - 更好的代码组织和维护性
    - 模块化设计，便于扩展
    - 更清晰的职责分离
    - 更好的测试支持
    - 向后兼容性保证
    
    📚 详细信息请查看：docs/IMPROVEMENTS_README.md
    """
    
    print(guide)


def check_compatibility():
    """检查兼容性"""
    try:
        # 检查Python版本
        if sys.version_info < (3, 7):
            print("⚠️ 警告: 建议使用Python 3.7+")
        
        # 检查必要的依赖
        import PyQt5
        import cv2
        import numpy as np
        
        print("✅ 依赖检查通过")
        return True
        
    except ImportError as e:
        print(f"❌ 依赖检查失败: {e}")
        print("请运行: pip install -r requirements.txt")
        return False


if __name__ == "__main__":
    print("🚀 景陶易购智能交易系统 - 模块化版本")
    print("=" * 50)
    
    # 显示迁移指南
    show_migration_guide()
    
    # 检查兼容性
    if not check_compatibility():
        sys.exit(1)
    
    # 询问用户是否继续
    try:
        choice = input("\n是否继续运行？(y/n): ").lower().strip()
        if choice in ['y', 'yes', '是', '']:
            print("🔄 启动应用...")
            main()
        else:
            print("👋 已取消运行")
            
    except KeyboardInterrupt:
        print("\n👋 用户取消运行")
        sys.exit(0)
    except EOFError:
        # 非交互模式，直接运行
        print("🔄 非交互模式，直接启动...")
        main()