#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统集成指南和示例
展示如何将所有改进模块集成到现有的智能交易系统中
"""

import time
import logging
import threading
from typing import Dict, Optional
import cv2
import numpy as np

# 导入所有改进模块
from enhanced_ui_detection import EnhancedUIDetector
from robust_error_handler import RobustErrorHandler, ErrorType, auto_error_handler
from advanced_strategy_engine import AdvancedStrategyEngine, SignalStrength
from enhanced_risk_manager import EnhancedRiskManager, RiskLevel
from real_time_monitor import RealTimeMonitor, AlertLevel, AlertType

class IntegratedTradingSystem:
    """集成交易系统
    
    将所有改进模块整合为一个完整的交易系统
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # 初始化各个组件
        self.ui_detector = EnhancedUIDetector()
        self.error_handler = RobustErrorHandler(config_manager=None)
        self.strategy_engine = AdvancedStrategyEngine(config.get('strategy', {}))
        self.risk_manager = EnhancedRiskManager(
            initial_capital=config.get('initial_capital', 10000),
            config=config.get('risk', {})
        )
        self.monitor = RealTimeMonitor(config.get('monitoring', {}))
        
        # 系统状态
        self.is_running = False
        self.trading_thread = None
        self.last_trade_time = 0
        
        # 性能统计
        self.stats = {
            'total_signals': 0,
            'total_trades': 0,
            'successful_trades': 0,
            'total_errors': 0,
            'system_uptime': 0
        }
        
        self.logger.info("集成交易系统初始化完成")
    
    def start_system(self) -> bool:
        """启动整个交易系统"""
        try:
            self.logger.info("启动集成交易系统...")
            
            # 1. 启动错误处理监控
            self.error_handler.start_monitoring()
            
            # 2. 启动风险管理监控
            self.risk_manager.start_monitoring()
            
            # 3. 启动实时监控
            self.monitor.start_monitoring(['system', 'trading', 'alerts', 'heartbeat'])
            
            # 4. 启动主交易循环
            self.is_running = True
            self.trading_thread = threading.Thread(target=self._main_trading_loop)
            self.trading_thread.daemon = True
            self.trading_thread.start()
            
            # 5. 记录系统启动
            self.stats['system_uptime'] = time.time()
            self.monitor.create_alert(
                AlertLevel.INFO,
                AlertType.SYSTEM_ERROR,
                "系统启动",
                "集成交易系统已成功启动"
            )
            
            self.logger.info("集成交易系统启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"系统启动失败: {e}")
            self.error_handler.handle_error(
                ErrorType.SYSTEM_ERROR,
                f"系统启动失败: {str(e)}",
                auto_recover=False
            )
            return False
    
    def stop_system(self):
        """停止交易系统"""
        try:
            self.logger.info("停止集成交易系统...")
            
            # 1. 停止主交易循环
            self.is_running = False
            if self.trading_thread and self.trading_thread.is_alive():
                self.trading_thread.join(timeout=10)
            
            # 2. 紧急平仓所有持仓
            self.risk_manager.emergency_liquidate_all("系统停止")
            
            # 3. 停止各个监控
            self.error_handler.stop_monitoring()
            self.risk_manager.stop_monitoring()
            self.monitor.stop_monitoring()
            
            # 4. 记录系统停止
            self.monitor.create_alert(
                AlertLevel.INFO,
                AlertType.SYSTEM_ERROR,
                "系统停止",
                "集成交易系统已停止"
            )
            
            self.logger.info("集成交易系统已停止")
            
        except Exception as e:
            self.logger.error(f"系统停止失败: {e}")
    
    @auto_error_handler(ErrorType.TRADING_TIMEOUT, auto_recover=True)
    def _main_trading_loop(self):
        """主交易循环"""
        self.logger.info("主交易循环已启动")
        
        while self.is_running:
            try:
                # 1. 捕获市场数据
                market_image = self._capture_market_data()
                if market_image is None:
                    time.sleep(5)
                    continue
                
                # 2. 策略分析
                signal = self.strategy_engine.analyze_market(
                    market_image, 
                    self._get_current_price_data()
                )
                self.stats['total_signals'] += 1
                
                # 3. 风险评估
                if signal.signal_type in ['buy', 'sell']:
                    risk_assessment = self._evaluate_trade_risk(signal)
                    
                    # 4. 执行交易
                    if risk_assessment['allowed']:
                        trade_success = self._execute_trade(signal, risk_assessment)
                        if trade_success:
                            self.stats['successful_trades'] += 1
                        self.stats['total_trades'] += 1
                
                # 5. 更新监控数据
                self._update_monitoring_data()
                
                # 6. 检查系统健康状态
                self._check_system_health()
                
                time.sleep(5)  # 5秒循环间隔
                
            except Exception as e:
                self.logger.error(f"主交易循环错误: {e}")
                self.stats['total_errors'] += 1
                self.error_handler.handle_error(
                    ErrorType.TRADING_ERROR,
                    f"主交易循环错误: {str(e)}",
                    auto_recover=True
                )
                time.sleep(10)  # 错误后延长等待时间
    
    def _capture_market_data(self) -> Optional[np.ndarray]:
        """捕获市场数据"""
        try:
            # 使用增强的UI检测器捕获窗口
            image = self.ui_detector.capture_window_direct("景陶易购")
            
            if image is None:
                self.error_handler.handle_error(
                    ErrorType.UI_DETECTION_FAILED,
                    "无法捕获交易窗口",
                    auto_recover=True
                )
                return None
            
            return image
            
        except Exception as e:
            self.logger.error(f"捕获市场数据失败: {e}")
            return None
    
    def _get_current_price_data(self) -> Dict:
        """获取当前价格数据"""
        # 这里应该从实际的数据源获取价格信息
        # 暂时返回模拟数据
        return {
            'price': 100.0,
            'volume': 1000,
            'timestamp': time.time()
        }
    
    def _evaluate_trade_risk(self, signal) -> Dict:
        """评估交易风险"""
        try:
            # 基础参数
            symbol = "DEFAULT"  # 实际应该从信号中获取
            action = signal.signal_type
            quantity = 100  # 实际应该根据资金管理计算
            price = signal.price_level or 100.0
            
            # 风险评估
            risk_result = self.risk_manager.evaluate_trade_risk(
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                signal_confidence=signal.confidence
            )
            
            return risk_result
            
        except Exception as e:
            self.logger.error(f"风险评估失败: {e}")
            return {'allowed': False, 'reason': f"风险评估错误: {str(e)}"}
    
    def _execute_trade(self, signal, risk_assessment: Dict) -> bool:
        """执行交易"""
        try:
            self.logger.info(f"执行交易: {signal.signal_type} 信号强度: {signal.strength.value}")
            
            # 检查交易冷却时间
            current_time = time.time()
            if current_time - self.last_trade_time < 30:  # 30秒冷却
                self.logger.info("交易冷却时间未到，跳过交易")
                return False
            
            # 获取建议数量
            quantity = risk_assessment.get('suggested_quantity', 100)
            price = signal.price_level or 100.0
            
            # 1. UI操作：检测和点击交易按钮
            trade_success = self._perform_ui_trading_operation(
                signal.signal_type, quantity, price
            )
            
            if trade_success:
                # 2. 更新持仓
                self.risk_manager.update_position(
                    symbol="DEFAULT",
                    action=signal.signal_type,
                    quantity=quantity,
                    price=price,
                    commission=5.0  # 假设手续费
                )
                
                # 3. 记录交易时间
                self.last_trade_time = current_time
                
                # 4. 发送交易成功通知
                self.monitor.create_alert(
                    AlertLevel.INFO,
                    AlertType.TRADING_ERROR,
                    "交易执行成功",
                    f"{signal.signal_type.upper()} {quantity}股 @{price:.2f}",
                    {
                        'action': signal.signal_type,
                        'quantity': quantity,
                        'price': price,
                        'confidence': signal.confidence
                    }
                )
                
                return True
            else:
                # 交易失败处理
                self.error_handler.handle_error(
                    ErrorType.TRADING_TIMEOUT,
                    "UI交易操作失败",
                    context={'signal': signal.signal_type, 'quantity': quantity},
                    auto_recover=True
                )
                return False
                
        except Exception as e:
            self.logger.error(f"交易执行失败: {e}")
            self.error_handler.handle_error(
                ErrorType.TRADING_ERROR,
                f"交易执行异常: {str(e)}",
                auto_recover=True
            )
            return False
    
    def _perform_ui_trading_operation(self, action: str, quantity: int, price: float) -> bool:
        """执行UI交易操作"""
        try:
            # 1. 检测交易界面
            current_image = self._capture_market_data()
            if current_image is None:
                return False
            
            # 2. 检测买入/卖出按钮
            button_name = 'buy_mode_button' if action == 'buy' else 'sell_mode_button'
            button_result = self.ui_detector.multi_level_button_detection(
                current_image, 
                button_name,
                '买' if action == 'buy' else '卖'
            )
            
            if not button_result.get('detected', False):
                self.logger.warning(f"未检测到{action}按钮")
                return False
            
            # 3. 点击按钮
            button_pos = button_result.get('position')
            if button_pos:
                import pyautogui
                pyautogui.click(button_pos[0], button_pos[1])
                time.sleep(1)
                
                # 4. 输入价格和数量（这里简化处理）
                # 实际应该检测输入框并输入具体数值
                
                # 5. 确认交易
                confirm_result = self.ui_detector.multi_level_button_detection(
                    current_image, 
                    'confirm_button',
                    '确定'
                )
                
                if confirm_result.get('detected', False):
                    confirm_pos = confirm_result.get('position')
                    if confirm_pos:
                        pyautogui.click(confirm_pos[0], confirm_pos[1])
                        time.sleep(2)
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"UI交易操作失败: {e}")
            return False
    
    def _update_monitoring_data(self):
        """更新监控数据"""
        try:
            # 更新价格数据到风险管理器
            current_prices = {"DEFAULT": 100.0}  # 实际应该获取真实价格
            self.risk_manager.update_market_prices(current_prices)
            
        except Exception as e:
            self.logger.error(f"更新监控数据失败: {e}")
    
    def _check_system_health(self):
        """检查系统健康状态"""
        try:
            # 获取风险指标
            risk_metrics = self.risk_manager.get_risk_metrics()
            
            # 检查关键风险指标
            if risk_metrics.risk_score > 0.8:
                self.monitor.create_alert(
                    AlertLevel.CRITICAL,
                    AlertType.RISK_WARNING,
                    "系统风险过高",
                    f"风险评分: {risk_metrics.risk_score:.2f}",
                    {'risk_metrics': risk_metrics.__dict__}
                )
            
            # 检查回撤
            if risk_metrics.current_drawdown > 0.10:  # 10%回撤
                self.monitor.create_alert(
                    AlertLevel.WARNING,
                    AlertType.RISK_WARNING,
                    "回撤过大",
                    f"当前回撤: {risk_metrics.current_drawdown:.2%}",
                    {'drawdown': risk_metrics.current_drawdown}
                )
            
        except Exception as e:
            self.logger.error(f"系统健康检查失败: {e}")
    
    def get_system_status(self) -> Dict:
        """获取系统整体状态"""
        try:
            return {
                'running': self.is_running,
                'uptime': time.time() - self.stats['system_uptime'] if self.stats['system_uptime'] > 0 else 0,
                'stats': self.stats.copy(),
                'strategy_performance': self.strategy_engine.get_strategy_performance(),
                'risk_metrics': self.risk_manager.get_risk_metrics().__dict__,
                'error_statistics': self.error_handler.get_error_statistics(),
                'monitoring_status': self.monitor.get_monitoring_status()
            }
        except Exception as e:
            self.logger.error(f"获取系统状态失败: {e}")
            return {'error': str(e)}

def create_default_config() -> Dict:
    """创建默认配置"""
    return {
        'initial_capital': 10000,
        'strategy': {
            'adaptive_mode': True,
            'min_confidence_threshold': 0.6,
            'signal_cooldown': 30
        },
        'risk': {
            'max_daily_loss_pct': 0.05,
            'max_single_loss_pct': 0.02,
            'max_position_size_pct': 0.20,
            'max_positions': 5
        },
        'monitoring': {
            'monitor_interval': 5,
            'notification_channels': ['log', 'file'],
            'alert_file': 'system_alerts.json',
            'thresholds': {
                'cpu_usage': 85.0,
                'memory_usage': 90.0,
                'daily_loss': 0.05,
                'error_rate': 0.1
            }
        }
    }

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('integrated_trading_system.log'),
            logging.StreamHandler()
        ]
    )
    
    # 创建配置
    config = create_default_config()
    
    # 创建集成系统
    trading_system = IntegratedTradingSystem(config)
    
    try:
        # 启动系统
        if trading_system.start_system():
            print("✅ 集成交易系统启动成功")
            
            # 运行一段时间进行测试
            time.sleep(60)  # 运行1分钟
            
            # 显示系统状态
            status = trading_system.get_system_status()
            print("\n📊 系统状态:")
            print(f"运行时间: {status['uptime']:.1f}秒")
            print(f"总信号数: {status['stats']['total_signals']}")
            print(f"总交易数: {status['stats']['total_trades']}")
            print(f"成功交易数: {status['stats']['successful_trades']}")
            print(f"总错误数: {status['stats']['total_errors']}")
            
        else:
            print("❌ 系统启动失败")
            
    except KeyboardInterrupt:
        print("\n⏹️ 收到停止信号")
    except Exception as e:
        print(f"❌ 系统运行错误: {e}")
    finally:
        # 停止系统
        trading_system.stop_system()
        print("✅ 系统已安全停止")