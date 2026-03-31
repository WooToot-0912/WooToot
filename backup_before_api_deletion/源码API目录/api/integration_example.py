#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API集成示例
展示如何将景陶易购API功能集成到现有的智能交易系统中
"""

import sys
import logging
from typing import Dict, Any
from datetime import datetime

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTabWidget
from PyQt5.QtCore import QTimer

# 导入API模块
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from api_integration_manager import APIIntegrationManager, TradingMode, TradingSignal
from api_gui_panel import APIGUIPanel

# 导入现有系统模块（需要根据实际路径调整）
try:
    from trading.trading_engine import SmartTradingEngine
    from trading.trading_gui import SmartTradingWindow
except ImportError:
    try:
        # 尝试从app目录导入
        app_path = project_root / "app"
        if app_path not in sys.path:
            sys.path.insert(0, str(app_path))
        from main_stable import SmartTradingWindow
        SmartTradingEngine = None
    except ImportError:
        # 如果导入失败，创建模拟类
        class SmartTradingEngine:
            def __init__(self, *args, **kwargs):
                pass

            def get_latest_signal(self):
                return None

        class SmartTradingWindow:
            def __init__(self, *args, **kwargs):
                pass

class EnhancedTradingSystem(QMainWindow):
    """增强版交易系统 - 集成API功能"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 初始化API管理器
        self.api_config = {
            'max_daily_orders': 100,
            'max_position_size': 10,
            'min_signal_confidence': 0.6,
            'max_order_history': 1000
        }
        self.api_manager = APIIntegrationManager(self.api_config)
        
        # 初始化原有交易引擎
        self.trading_engine = None
        
        self.init_ui()
        self.setup_integration()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("景陶易购智能交易系统 - API增强版")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 原有交易界面（如果存在）
        try:
            self.trading_window = SmartTradingWindow()
            self.tab_widget.addTab(self.trading_window, "智能交易")
        except Exception as e:
            self.logger.warning(f"无法加载原有交易界面: {e}")
        
        # API管理界面
        self.api_panel = APIGUIPanel(self.api_manager)
        self.tab_widget.addTab(self.api_panel, "API管理")
        
        # 创建状态栏
        self.statusBar().showMessage("系统已启动")
    
    def setup_integration(self):
        """设置集成功能"""
        # 设置定时器检查交易信号
        self.signal_timer = QTimer()
        self.signal_timer.timeout.connect(self.check_trading_signals)
        self.signal_timer.start(5000)  # 每5秒检查一次
        
        # 设置API管理器回调
        self.api_manager.on_order_filled = self.on_api_order_filled
        self.api_manager.on_order_failed = self.on_api_order_failed
    
    def check_trading_signals(self):
        """检查交易信号并通过API执行"""
        try:
            # 如果API未连接或交易未启用，跳过
            if not self.api_manager.is_api_connected or not self.api_manager.is_trading_enabled:
                return
            
            # 从原有交易引擎获取信号（这里需要根据实际情况调整）
            if hasattr(self, 'trading_window') and hasattr(self.trading_window, 'trading_engine'):
                engine = self.trading_window.trading_engine
                if engine:
                    # 这里需要根据实际的信号获取方法调整
                    signal_data = self.get_signal_from_engine(engine)
                    if signal_data:
                        self.process_trading_signal(signal_data)
        
        except Exception as e:
            self.logger.error(f"检查交易信号异常: {e}")
    
    def get_signal_from_engine(self, engine) -> Dict[str, Any]:
        """从交易引擎获取信号"""
        try:
            # 这里需要根据实际的交易引擎接口调整
            # 示例：假设引擎有get_latest_signal方法
            if hasattr(engine, 'get_latest_signal'):
                return engine.get_latest_signal()
            
            # 或者从引擎的其他属性获取信号
            # 这里返回一个示例信号用于测试
            return None
            
        except Exception as e:
            self.logger.error(f"获取交易信号异常: {e}")
            return None
    
    def process_trading_signal(self, signal_data: Dict[str, Any]):
        """处理交易信号"""
        try:
            # 解析信号数据
            action = signal_data.get('action', 'buy')  # buy/sell
            commodity_id = signal_data.get('commodity_id', '1001')  # 商品ID
            price = float(signal_data.get('price', 0))
            quantity = int(signal_data.get('quantity', 1))
            confidence = float(signal_data.get('confidence', 0.8))
            reason = signal_data.get('reason', '系统信号')
            
            # 创建交易信号
            trading_signal = TradingSignal(
                action=action,
                commodity_id=commodity_id,
                price=price,
                quantity=quantity,
                confidence=confidence,
                reason=reason,
                timestamp=datetime.now()
            )
            
            # 提交信号
            success = self.api_manager.submit_trading_signal(trading_signal)
            
            if success:
                self.logger.info(f"✅ 交易信号已提交: {action} {commodity_id}")
                self.statusBar().showMessage(f"交易信号已提交: {action} {commodity_id}")
            else:
                self.logger.warning(f"⚠️ 交易信号提交失败: {action} {commodity_id}")
        
        except Exception as e:
            self.logger.error(f"处理交易信号异常: {e}")
    
    def on_api_order_filled(self, order_record):
        """API订单成交回调"""
        signal = order_record.signal
        message = f"API订单成交: {signal.action} {signal.commodity_id} @{order_record.fill_price}"
        self.logger.info(message)
        self.statusBar().showMessage(message)
        
        # 可以在这里通知原有系统订单已成交
        self.notify_original_system_order_filled(order_record)
    
    def on_api_order_failed(self, order_record):
        """API订单失败回调"""
        signal = order_record.signal
        message = f"API订单失败: {signal.action} {signal.commodity_id} - {order_record.error_message}"
        self.logger.error(message)
        self.statusBar().showMessage(message)
        
        # 可以在这里通知原有系统订单失败
        self.notify_original_system_order_failed(order_record)
    
    def notify_original_system_order_filled(self, order_record):
        """通知原有系统订单成交"""
        try:
            # 这里可以调用原有系统的接口来更新状态
            # 例如更新持仓、资金等信息
            if hasattr(self, 'trading_window') and hasattr(self.trading_window, 'trading_engine'):
                engine = self.trading_window.trading_engine
                if hasattr(engine, 'on_order_filled'):
                    engine.on_order_filled(order_record)
        except Exception as e:
            self.logger.error(f"通知原有系统订单成交异常: {e}")
    
    def notify_original_system_order_failed(self, order_record):
        """通知原有系统订单失败"""
        try:
            # 这里可以调用原有系统的接口来处理失败
            if hasattr(self, 'trading_window') and hasattr(self.trading_window, 'trading_engine'):
                engine = self.trading_window.trading_engine
                if hasattr(engine, 'on_order_failed'):
                    engine.on_order_failed(order_record)
        except Exception as e:
            self.logger.error(f"通知原有系统订单失败异常: {e}")
    
    def manual_submit_signal(self, action: str, commodity_id: str = "1001", 
                           price: float = 100.0, quantity: int = 1):
        """手动提交交易信号（用于测试）"""
        return self.api_panel.submit_signal(action, commodity_id, price, quantity, 0.9, "手动测试")
    
    def get_api_status(self) -> Dict[str, Any]:
        """获取API状态"""
        return self.api_manager.get_status()
    
    def get_api_positions(self):
        """获取API持仓"""
        return self.api_manager.get_positions()
    
    def get_api_orders(self):
        """获取API委托"""
        return self.api_manager.get_orders()
    
    def get_api_trades(self):
        """获取API成交"""
        return self.api_manager.get_trades()

def create_enhanced_trading_app():
    """创建增强版交易应用"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = EnhancedTradingSystem()
    main_window.show()
    
    return app, main_window

def main():
    """主函数"""
    app, main_window = create_enhanced_trading_app()
    
    # 运行应用
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("程序被用户中断")
        main_window.api_manager.disconnect()

if __name__ == "__main__":
    main()
