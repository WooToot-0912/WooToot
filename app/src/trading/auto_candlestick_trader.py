#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K线自动交易系统 - 基于K线颜色的自动交易
集成K线识别和自动交易执行
"""

import time
import logging
import threading
from typing import Dict, Optional
from datetime import datetime
import numpy as np

from .candlestick_detector import CandlestickColorDetector
from .trading_engine import SmartTradingEngine

class AutoCandlestickTrader:
    """K线自动交易器"""
    
    def __init__(self, config: Dict = None, trading_engine=None):
        self.logger = logging.getLogger(__name__)
        
        # 使用传入的交易引擎或创建新的
        self.trading_engine = trading_engine if trading_engine else SmartTradingEngine()
        
        # 初始化K线检测器
        print("🔄 正在创建CandlestickColorDetector实例...")
        self.candlestick_detector = CandlestickColorDetector(self.trading_engine)
        self.candlestick_detector.set_signal_callback(self.handle_trading_signal)
        print("✅ CandlestickColorDetector实例创建完成")
        
        # 交易配置
        self.config = config or {}
        self.trade_config = {
            'auto_trading_enabled': self.config.get('auto_trading_enabled', True),
            'default_quantity': self.config.get('default_quantity', 1),
            'price_offset': self.config.get('price_offset', 0.0),  # 价格偏移
            'max_trades_per_hour': self.config.get('max_trades_per_hour', 10),
            'min_trade_interval': self.config.get('min_trade_interval', 10),  # 最小交易间隔（秒）
            'enable_buy_signals': self.config.get('enable_buy_signals', True),
            'enable_sell_signals': self.config.get('enable_sell_signals', True),
            'risk_management': self.config.get('risk_management', True)
        }
        
        # 状态管理
        self.is_running = False
        self.last_trade_time = 0
        self.trade_count_last_hour = 0
        self.hour_start_time = time.time()
        
        # 交易统计
        self.trade_stats = {
            'total_trades': 0,
            'buy_trades': 0,
            'sell_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'last_trade_time': None,
            'last_trade_type': None,
            'last_price': None
        }
        
        # 风险管理
        self.risk_manager = {
            'max_position': self.config.get('max_position', 10),
            'current_position': 0,
            'stop_loss_enabled': self.config.get('stop_loss_enabled', False),
            'stop_loss_percentage': self.config.get('stop_loss_percentage', 2.0)
        }
        
        self.logger.info("🚀 K线自动交易系统已初始化")
    
    def handle_trading_signal(self, signal_data: Dict):
        """处理交易信号回调"""
        try:
            signal_type = signal_data.get('type')
            color = signal_data.get('color')
            confidence = signal_data.get('confidence', 0.0)
            timestamp = signal_data.get('timestamp', time.time())
            
            print("=" * 60)
            print(f"📡 K线自动交易器收到信号: {signal_type.upper()} ({color}色K线)")
            print(f"   置信度: {confidence:.2f}")
            print(f"   时间戳: {timestamp}")
            print(f"   自动交易启用: {self.trade_config['auto_trading_enabled']}")
            print("=" * 60)
            self.logger.info(f"📡 收到交易信号: {signal_type} ({color}色K线) 置信度: {confidence:.2f}")
            
            # 检查是否启用自动交易
            if not self.trade_config['auto_trading_enabled']:
                print("⏸️ 自动交易已禁用，跳过信号")
                self.logger.info("⏸️ 自动交易已禁用，跳过信号")
                return
            
            # 检查交易间隔
            if not self._check_trade_interval():
                return
            
            # 根据信号类型执行交易
            if signal_type == 'buy' and self.trade_config['enable_buy_signals']:
                print(f"🟢 执行买入交易 - 基于{color}色K线信号")
                self._execute_buy_trade(signal_data)
            elif signal_type == 'sell' and self.trade_config['enable_sell_signals']:
                print(f"🔴 执行卖出交易 - 基于{color}色K线信号")
                self._execute_sell_trade(signal_data)
            else:
                print(f"⏸️ 跳过信号: {signal_type} (配置禁用或不支持)")
                self.logger.info(f"⏸️ 跳过信号: {signal_type}")
                
        except Exception as e:
            print(f"❌ 处理交易信号失败: {e}")
            self.logger.error(f"❌ 处理交易信号失败: {e}")
    
    def _check_trade_interval(self) -> bool:
        """检查交易间隔"""
        current_time = time.time()
        time_since_last_trade = current_time - self.last_trade_time
        
        if time_since_last_trade < self.trade_config['min_trade_interval']:
            remaining_time = self.trade_config['min_trade_interval'] - time_since_last_trade
            print(f"⏰ 交易间隔限制: 还需等待 {remaining_time:.1f} 秒")
            self.logger.info(f"⏰ 交易间隔限制: 还需等待 {remaining_time:.1f} 秒")
            return False
        
        # 检查每小时交易次数限制
        if current_time - self.hour_start_time > 3600:  # 重置每小时计数
            self.hour_start_time = current_time
            self.trade_count_last_hour = 0
        
        if self.trade_count_last_hour >= self.trade_config['max_trades_per_hour']:
            print(f"⏰ 每小时交易次数限制: {self.trade_count_last_hour}/{self.trade_config['max_trades_per_hour']}")
            self.logger.info(f"⏰ 每小时交易次数限制已达到")
            return False
        
        return True
    
    def _execute_buy_trade(self, signal_data: Dict):
        """执行买入交易"""
        try:
            print("🚀 开始执行买入交易...")
            self.logger.info("🚀 开始执行买入交易...")
            
            # 获取当前价格
            current_price = self.trading_engine.get_current_price()
            if not current_price:
                print("❌ 无法获取当前价格，取消交易")
                self.logger.error("❌ 无法获取当前价格，取消交易")
                return False
            
            print(f"💰 当前价格: {current_price}")
            
            # 自动填入价格和数量
            if not self.trading_engine.auto_fill_price():
                print("❌ 自动填入价格失败")
                return False
            
            if not self.trading_engine.auto_fill_quantity():
                print("❌ 自动填入数量失败")
                return False
            
            print("✅ 价格和数量已自动填入")
            
            # 点击订立按钮
            if not self.trading_engine.click_button('buy_order_button'):
                print("❌ 点击买入订立按钮失败")
                return False
            
            print("✅ 已点击买入订立按钮")
            time.sleep(0.5)  # 等待界面响应
            
            # 点击确认按钮
            if not self.trading_engine.click_button('confirm_button'):
                print("❌ 点击确认按钮失败")
                return False
            
            print("✅ 已点击确认按钮")
            
            # 更新统计
            self._update_trade_stats('buy', current_price, True)
            print("✅ 买入交易执行完成！")
            self.logger.info("✅ 买入交易执行完成！")
            
            return True
            
        except Exception as e:
            print(f"❌ 买入交易执行失败: {e}")
            self.logger.error(f"❌ 买入交易执行失败: {e}")
            self._update_trade_stats('buy', 0, False)
            return False
    
    def _execute_sell_trade(self, signal_data: Dict):
        """执行卖出交易"""
        try:
            print("🚀 开始执行卖出交易...")
            self.logger.info("🚀 开始执行卖出交易...")
            
            # 获取当前价格
            current_price = self.trading_engine.get_current_price()
            if not current_price:
                print("❌ 无法获取当前价格，取消交易")
                self.logger.error("❌ 无法获取当前价格，取消交易")
                return False
            
            print(f"💰 当前价格: {current_price}")
            
            # 自动填入价格和数量
            if not self.trading_engine.auto_fill_price():
                print("❌ 自动填入价格失败")
                return False
            
            if not self.trading_engine.auto_fill_quantity():
                print("❌ 自动填入数量失败")
                return False
            
            print("✅ 价格和数量已自动填入")
            
            # 点击订立按钮
            if not self.trading_engine.click_button('sell_order_button'):
                print("❌ 点击卖出订立按钮失败")
                return False
            
            print("✅ 已点击卖出订立按钮")
            time.sleep(0.5)  # 等待界面响应
            
            # 点击确认按钮
            if not self.trading_engine.click_button('confirm_button'):
                print("❌ 点击确认按钮失败")
                return False
            
            print("✅ 已点击确认按钮")
            
            # 更新统计
            self._update_trade_stats('sell', current_price, True)
            print("✅ 卖出交易执行完成！")
            self.logger.info("✅ 卖出交易执行完成！")
            
            return True
            
        except Exception as e:
            print(f"❌ 卖出交易执行失败: {e}")
            self.logger.error(f"❌ 卖出交易执行失败: {e}")
            self._update_trade_stats('sell', 0, False)
            return False
    
    def _update_trade_stats(self, trade_type: str, price: float, success: bool):
        """更新交易统计"""
        self.trade_stats['total_trades'] += 1
        self.trade_stats['last_trade_time'] = datetime.now()
        self.trade_stats['last_trade_type'] = trade_type
        self.trade_stats['last_price'] = price
        
        if success:
            self.trade_stats['successful_trades'] += 1
            if trade_type == 'buy':
                self.trade_stats['buy_trades'] += 1
            elif trade_type == 'sell':
                self.trade_stats['sell_trades'] += 1
        else:
            self.trade_stats['failed_trades'] += 1
        
        # 更新交易时间和计数
        self.last_trade_time = time.time()
        self.trade_count_last_hour += 1
    
    def start_monitoring(self) -> bool:
        """启动K线监控"""
        try:
            print("🎯 启动K线自动交易监控...")
            self.logger.info("🎯 启动K线自动交易监控...")
            
            if self.is_running:
                print("⚠️ K线监控已在运行")
                self.logger.warning("⚠️ K线监控已在运行")
                return True
            
            # 启动K线检测器
            if not self.candlestick_detector.start_monitoring():
                print("❌ K线检测器启动失败")
                self.logger.error("❌ K线检测器启动失败")
                return False
            
            self.is_running = True
            print("✅ K线自动交易监控已启动")
            self.logger.info("✅ K线自动交易监控已启动")
            return True
            
        except Exception as e:
            print(f"❌ 启动K线监控失败: {e}")
            self.logger.error(f"❌ 启动K线监控失败: {e}")
            return False
    
    def stop_monitoring(self):
        """停止K线监控"""
        try:
            print("⏹️ 停止K线自动交易监控...")
            self.logger.info("⏹️ 停止K线自动交易监控...")
            
            if not self.is_running:
                print("⚠️ K线监控未在运行")
                self.logger.warning("⚠️ K线监控未在运行")
                return
            
            # 停止K线检测器
            self.candlestick_detector.stop_monitoring()
            self.is_running = False
            
            print("✅ K线自动交易监控已停止")
            self.logger.info("✅ K线自动交易监控已停止")
            
        except Exception as e:
            print(f"❌ 停止K线监控失败: {e}")
            self.logger.error(f"❌ 停止K线监控失败: {e}")
    
    def get_trade_stats(self) -> Dict:
        """获取交易统计"""
        return self.trade_stats.copy()
    
    def get_detection_stats(self) -> Dict:
        """获取检测统计"""
        return self.candlestick_detector.get_detection_stats()
    
    def update_chart_area(self, x: float, y: float, width: float, height: float):
        """更新K线图监控区域"""
        self.candlestick_detector.update_chart_area(x, y, width, height)
    
    def set_chart_area(self, x: float, y: float, width: float, height: float):
        """设置K线图监控区域"""
        self.candlestick_detector.update_chart_area(x, y, width, height)
    
    def reset_detection_stats(self):
        """重置检测统计"""
        self.candlestick_detector.reset_stats()
    
    def reload_config(self):
        """重新加载K线配置"""
        self.candlestick_detector.reload_config()
    
    def set_auto_trading_enabled(self, enabled: bool):
        """设置是否启用自动交易"""
        self.trade_config['auto_trading_enabled'] = enabled
        status = "启用" if enabled else "禁用"
        print(f"⚙️ 自动交易已{status}")
        self.logger.info(f"⚙️ 自动交易已{status}")
    
    def is_monitoring_active(self) -> bool:
        """检查监控是否活跃"""
        return self.is_running and self.candlestick_detector.is_monitoring
    
    def stop_auto_trading(self):
        """停止自动交易（兼容性方法）"""
        self.stop_monitoring()