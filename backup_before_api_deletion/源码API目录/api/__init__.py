#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
景陶易购API直连功能模块
提供完整的API交易功能，包括登录、下单、查询、风险管理等
"""

__version__ = "1.0.0"
__author__ = "智能交易系统开发团队"

# 导入核心类
from .enhanced_trading_api import (
    EnhancedTradingAPI,
    LoginCredentials,
    OrderRequest,
    ApiResponse
)

from .api_integration_manager import (
    APIIntegrationManager,
    TradingMode,
    TradingSignal,
    OrderRecord,
    OrderStatus
)

from .api_gui_panel import (
    APIGUIPanel,
    APIStatusWidget,
    APIControlPanel
)

# 导出的公共接口
__all__ = [
    # API客户端
    'EnhancedTradingAPI',
    'LoginCredentials', 
    'OrderRequest',
    'ApiResponse',
    
    # 集成管理器
    'APIIntegrationManager',
    'TradingMode',
    'TradingSignal',
    'OrderRecord',
    'OrderStatus',
    
    # GUI组件
    'APIGUIPanel',
    'APIStatusWidget',
    'APIControlPanel',
    
    # 便捷函数
    'create_api_manager',
    'create_gui_panel',
    'quick_connect'
]

def create_api_manager(config=None):
    """
    创建API管理器的便捷函数
    
    Args:
        config: 配置字典，可选
        
    Returns:
        APIIntegrationManager: 配置好的API管理器实例
    """
    default_config = {
        'max_daily_orders': 100,
        'max_position_size': 10,
        'min_signal_confidence': 0.6,
        'max_order_history': 1000
    }
    
    if config:
        default_config.update(config)
    
    return APIIntegrationManager(default_config)

def create_gui_panel(api_manager=None):
    """
    创建GUI面板的便捷函数
    
    Args:
        api_manager: API管理器实例，如果为None则自动创建
        
    Returns:
        APIGUIPanel: GUI面板实例
    """
    if api_manager is None:
        api_manager = create_api_manager()
    
    return APIGUIPanel(api_manager)

def quick_connect(phone, password, market_id=28, config=None):
    """
    快速连接API的便捷函数
    
    Args:
        phone: 手机号
        password: 密码
        market_id: 市场ID，默认28
        config: 配置字典，可选
        
    Returns:
        tuple: (api_manager, success) API管理器实例和连接是否成功
    """
    api_manager = create_api_manager(config)
    success = api_manager.connect(phone, password, market_id)
    return api_manager, success

# 模块信息
def get_version():
    """获取模块版本"""
    return __version__

def get_features():
    """获取功能特性列表"""
    return [
        "完整的API封装",
        "智能重连机制", 
        "多种交易模式",
        "实时订单监控",
        "风险管理系统",
        "图形化管理界面",
        "异步处理",
        "线程安全",
        "错误恢复",
        "配置灵活"
    ]

def get_supported_operations():
    """获取支持的操作列表"""
    return [
        "用户登录/登出",
        "买入/卖出下单",
        "撤销订单/全部撤单",
        "查询持仓",
        "查询委托",
        "查询成交",
        "查询账户信息",
        "获取商品价格",
        "获取价格限制",
        "实时状态监控"
    ]

# 模块级别的配置
DEFAULT_CONFIG = {
    "api_settings": {
        "base_url": "https://zxyw.ceramic-copyright.com/apigateway",
        "kline_url": "https://zxyt.ceramic-copyright.com/qtfront_tq",
        "timeout": 30,
        "retry_attempts": 3,
        "heartbeat_interval": 300
    },
    "trading_settings": {
        "default_trading_mode": "manual",
        "max_daily_orders": 100,
        "max_position_size": 10,
        "min_signal_confidence": 0.6,
        "max_order_history": 1000,
        "order_check_interval": 5
    },
    "risk_management": {
        "enable_risk_check": True,
        "max_daily_loss": 10000,
        "max_single_order_value": 50000,
        "position_limit_per_commodity": 5,
        "enable_circuit_breaker": True,
        "circuit_breaker_threshold": -5000
    }
}

def get_default_config():
    """获取默认配置"""
    return DEFAULT_CONFIG.copy()

# 模块初始化检查
def _check_dependencies():
    """检查依赖包"""
    required_packages = ['requests', 'PyQt5']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        import warnings
        warnings.warn(
            f"缺少依赖包: {', '.join(missing_packages)}. "
            f"请运行: pip install {' '.join(missing_packages)}"
        )
    
    return len(missing_packages) == 0

# 执行依赖检查
_dependencies_ok = _check_dependencies()

def is_ready():
    """检查模块是否准备就绪"""
    return _dependencies_ok

# 使用示例
USAGE_EXAMPLE = '''
# 基础使用示例
from src.api import quick_connect, TradingMode, TradingSignal
from datetime import datetime

# 快速连接
api_manager, success = quick_connect("手机号", "密码")

if success:
    # 设置交易模式
    api_manager.set_trading_mode(TradingMode.SEMI_AUTO)
    api_manager.enable_trading(True)
    
    # 提交交易信号
    signal = TradingSignal(
        action="buy",
        commodity_id="1001", 
        price=100.0,
        quantity=1,
        confidence=0.8,
        reason="测试信号",
        timestamp=datetime.now()
    )
    
    api_manager.submit_trading_signal(signal)

# GUI使用示例
from PyQt5.QtWidgets import QApplication
from src.api import create_gui_panel

app = QApplication([])
gui_panel = create_gui_panel()
gui_panel.show()
app.exec_()
'''

def print_usage():
    """打印使用示例"""
    print("景陶易购API模块使用示例:")
    print("=" * 50)
    print(USAGE_EXAMPLE)

if __name__ == "__main__":
    print(f"景陶易购API模块 v{__version__}")
    print(f"作者: {__author__}")
    print(f"依赖检查: {'✅ 通过' if is_ready() else '❌ 失败'}")
    print(f"支持的功能: {len(get_features())} 项")
    print(f"支持的操作: {len(get_supported_operations())} 种")
    print_usage()
