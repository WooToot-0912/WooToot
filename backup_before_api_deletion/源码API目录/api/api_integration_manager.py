#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API集成管理器
将景陶易购API集成到现有的智能交易系统中
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

try:
    from .enhanced_trading_api import EnhancedTradingAPI, LoginCredentials, OrderRequest, ApiResponse
except ImportError:
    from enhanced_trading_api import EnhancedTradingAPI, LoginCredentials, OrderRequest, ApiResponse

class TradingMode(Enum):
    """交易模式"""
    MANUAL = "manual"           # 手动模式
    SEMI_AUTO = "semi_auto"     # 半自动模式
    FULL_AUTO = "full_auto"     # 全自动模式

class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"         # 待提交
    SUBMITTED = "submitted"     # 已提交
    FILLED = "filled"          # 已成交
    CANCELLED = "cancelled"     # 已撤销
    FAILED = "failed"          # 失败

@dataclass
class TradingSignal:
    """交易信号"""
    action: str                 # buy/sell
    commodity_id: str
    price: float
    quantity: int
    confidence: float           # 信号置信度
    reason: str                 # 信号原因
    timestamp: datetime

@dataclass
class OrderRecord:
    """订单记录"""
    signal: TradingSignal
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    submit_time: Optional[datetime] = None
    fill_time: Optional[datetime] = None
    fill_price: Optional[float] = None
    error_message: Optional[str] = None

class APIIntegrationManager:
    """API集成管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化API集成管理器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # API客户端
        self.api_client = EnhancedTradingAPI(on_connection_lost=self._on_connection_lost)
        
        # 交易状态
        self.trading_mode = TradingMode.MANUAL
        self.is_trading_enabled = False
        self.is_api_connected = False
        
        # 订单管理
        self.pending_orders: List[OrderRecord] = []
        self.order_history: List[OrderRecord] = []
        self.order_lock = threading.Lock()
        
        # 回调函数
        self.on_order_filled: Optional[Callable] = None
        self.on_order_failed: Optional[Callable] = None
        self.on_connection_status_changed: Optional[Callable] = None
        
        # 监控线程
        self._monitor_thread = None
        self._monitor_running = False
        
        # 风险控制
        self.max_daily_orders = self.config.get('max_daily_orders', 100)
        self.max_position_size = self.config.get('max_position_size', 10)
        self.daily_order_count = 0
        self.last_reset_date = datetime.now().date()
    
    def connect(self, phone: str, password: str, market_id: int = 28) -> bool:
        """
        连接API
        
        Args:
            phone: 手机号
            password: 密码
            market_id: 市场ID
            
        Returns:
            bool: 连接是否成功
        """
        try:
            credentials = LoginCredentials(phone, password, market_id)
            response = self.api_client.login(credentials)
            
            if response.success:
                self.is_api_connected = True
                self.logger.info("✅ API连接成功")
                
                # 启动监控线程
                self._start_monitoring()
                
                # 通知连接状态变化
                if self.on_connection_status_changed:
                    self.on_connection_status_changed(True)
                
                return True
            else:
                self.logger.error(f"❌ API连接失败: {response.message}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ API连接异常: {e}")
            return False
    
    def disconnect(self):
        """断开API连接"""
        try:
            self.is_api_connected = False
            self.is_trading_enabled = False
            
            # 停止监控
            self._stop_monitoring()
            
            # 停止心跳
            self.api_client.stop_heartbeat()
            
            # 通知连接状态变化
            if self.on_connection_status_changed:
                self.on_connection_status_changed(False)
            
            self.logger.info("✅ API已断开连接")
            
        except Exception as e:
            self.logger.error(f"❌ 断开连接异常: {e}")
    
    def set_trading_mode(self, mode: TradingMode):
        """设置交易模式"""
        self.trading_mode = mode
        self.logger.info(f"🔧 交易模式设置为: {mode.value}")
    
    def enable_trading(self, enabled: bool = True):
        """启用/禁用交易"""
        self.is_trading_enabled = enabled
        status = "启用" if enabled else "禁用"
        self.logger.info(f"🎯 交易功能已{status}")
    
    def submit_trading_signal(self, signal: TradingSignal) -> bool:
        """
        提交交易信号
        
        Args:
            signal: 交易信号
            
        Returns:
            bool: 是否成功提交
        """
        if not self.is_api_connected:
            self.logger.error("❌ API未连接，无法提交交易信号")
            return False
        
        if not self.is_trading_enabled:
            self.logger.warning("⚠️ 交易功能未启用，忽略交易信号")
            return False
        
        # 风险检查
        if not self._risk_check(signal):
            return False
        
        try:
            # 创建订单记录
            order_record = OrderRecord(signal=signal)
            
            with self.order_lock:
                self.pending_orders.append(order_record)
            
            # 根据交易模式处理
            if self.trading_mode == TradingMode.FULL_AUTO:
                return self._execute_order_immediately(order_record)
            elif self.trading_mode == TradingMode.SEMI_AUTO:
                self.logger.info(f"📋 半自动模式: 交易信号已加入待处理队列")
                return True
            else:
                self.logger.info(f"📋 手动模式: 交易信号已记录，等待手动确认")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 提交交易信号异常: {e}")
            return False
    
    def _execute_order_immediately(self, order_record: OrderRecord) -> bool:
        """立即执行订单"""
        try:
            signal = order_record.signal
            
            # 提交订单
            if signal.action.lower() == "buy":
                response = self.api_client.buy_order(
                    signal.commodity_id,
                    str(signal.price),
                    str(signal.quantity)
                )
            elif signal.action.lower() == "sell":
                response = self.api_client.sell_order(
                    signal.commodity_id,
                    str(signal.price),
                    str(signal.quantity)
                )
            else:
                self.logger.error(f"❌ 不支持的交易动作: {signal.action}")
                return False
            
            # 更新订单状态
            order_record.submit_time = datetime.now()
            
            if response.success:
                order_record.status = OrderStatus.SUBMITTED
                order_record.order_id = response.data.get("orderId") if response.data else None
                self.daily_order_count += 1
                
                self.logger.info(f"✅ 订单提交成功: {signal.action} {signal.commodity_id}")
                return True
            else:
                order_record.status = OrderStatus.FAILED
                order_record.error_message = response.message
                
                self.logger.error(f"❌ 订单提交失败: {response.message}")
                
                # 通知订单失败
                if self.on_order_failed:
                    self.on_order_failed(order_record)
                
                return False
                
        except Exception as e:
            order_record.status = OrderStatus.FAILED
            order_record.error_message = str(e)
            
            self.logger.error(f"❌ 执行订单异常: {e}")
            return False
    
    def _risk_check(self, signal: TradingSignal) -> bool:
        """风险检查"""
        # 重置日计数器
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_order_count = 0
            self.last_reset_date = today
        
        # 检查日订单限制
        if self.daily_order_count >= self.max_daily_orders:
            self.logger.error(f"❌ 已达到日订单限制: {self.max_daily_orders}")
            return False
        
        # 检查信号置信度
        min_confidence = self.config.get('min_signal_confidence', 0.6)
        if signal.confidence < min_confidence:
            self.logger.warning(f"⚠️ 信号置信度过低: {signal.confidence} < {min_confidence}")
            return False
        
        # 检查价格合理性
        if signal.price <= 0:
            self.logger.error(f"❌ 价格无效: {signal.price}")
            return False
        
        # 检查数量合理性
        if signal.quantity <= 0 or signal.quantity > self.max_position_size:
            self.logger.error(f"❌ 数量无效: {signal.quantity}")
            return False
        
        return True
    
    def get_pending_orders(self) -> List[OrderRecord]:
        """获取待处理订单"""
        with self.order_lock:
            return [order for order in self.pending_orders if order.status == OrderStatus.PENDING]
    
    def confirm_pending_order(self, order_index: int) -> bool:
        """确认待处理订单"""
        try:
            with self.order_lock:
                if 0 <= order_index < len(self.pending_orders):
                    order = self.pending_orders[order_index]
                    if order.status == OrderStatus.PENDING:
                        return self._execute_order_immediately(order)
            return False
        except Exception as e:
            self.logger.error(f"❌ 确认订单异常: {e}")
            return False
    
    def cancel_pending_order(self, order_index: int) -> bool:
        """取消待处理订单"""
        try:
            with self.order_lock:
                if 0 <= order_index < len(self.pending_orders):
                    order = self.pending_orders[order_index]
                    if order.status == OrderStatus.PENDING:
                        order.status = OrderStatus.CANCELLED
                        self.logger.info(f"✅ 已取消待处理订单")
                        return True
            return False
        except Exception as e:
            self.logger.error(f"❌ 取消订单异常: {e}")
            return False

    def _start_monitoring(self):
        """启动监控线程"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self._monitor_thread.start()
        self.logger.info("🔍 订单监控已启动")

    def _stop_monitoring(self):
        """停止监控线程"""
        self._monitor_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        self.logger.info("🔍 订单监控已停止")

    def _monitor_worker(self):
        """监控工作线程"""
        while self._monitor_running:
            try:
                time.sleep(5)  # 每5秒检查一次

                if not self._monitor_running:
                    break

                # 检查已提交订单的状态
                self._check_order_status()

                # 清理历史订单
                self._cleanup_old_orders()

            except Exception as e:
                self.logger.error(f"❌ 监控线程异常: {e}")

    def _check_order_status(self):
        """检查订单状态"""
        try:
            with self.order_lock:
                submitted_orders = [order for order in self.pending_orders
                                  if order.status == OrderStatus.SUBMITTED]

            if not submitted_orders:
                return

            # 获取当前委托
            response = self.api_client.get_current_orders()
            if not response.success:
                return

            current_orders = []
            if response.data and isinstance(response.data, dict):
                content = response.data.get("content", [])
                if isinstance(content, list):
                    current_orders = content

            # 获取成交记录
            trades_response = self.api_client.get_current_trades()
            current_trades = []
            if trades_response.success and trades_response.data:
                trades_content = trades_response.data.get("content", [])
                if isinstance(trades_content, list):
                    current_trades = trades_content

            # 更新订单状态
            for order in submitted_orders:
                if not order.order_id:
                    continue

                # 检查是否已成交
                filled = False
                for trade in current_trades:
                    if trade.get("orderId") == order.order_id:
                        order.status = OrderStatus.FILLED
                        order.fill_time = datetime.now()
                        order.fill_price = float(trade.get("price", 0))
                        filled = True

                        self.logger.info(f"✅ 订单已成交: {order.order_id}")

                        # 通知订单成交
                        if self.on_order_filled:
                            self.on_order_filled(order)
                        break

                if filled:
                    continue

                # 检查是否还在委托中
                still_pending = False
                for current_order in current_orders:
                    if current_order.get("orderId") == order.order_id:
                        still_pending = True
                        break

                # 如果不在委托中且未成交，可能已被撤销
                if not still_pending:
                    order.status = OrderStatus.CANCELLED
                    self.logger.info(f"📋 订单已撤销: {order.order_id}")

        except Exception as e:
            self.logger.error(f"❌ 检查订单状态异常: {e}")

    def _cleanup_old_orders(self):
        """清理旧订单"""
        try:
            with self.order_lock:
                # 将已完成的订单移到历史记录
                completed_orders = [order for order in self.pending_orders
                                  if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.FAILED]]

                for order in completed_orders:
                    self.pending_orders.remove(order)
                    self.order_history.append(order)

                # 限制历史记录数量
                max_history = self.config.get('max_order_history', 1000)
                if len(self.order_history) > max_history:
                    self.order_history = self.order_history[-max_history:]

        except Exception as e:
            self.logger.error(f"❌ 清理订单异常: {e}")

    def _on_connection_lost(self):
        """连接丢失回调"""
        self.is_api_connected = False
        self.is_trading_enabled = False

        self.logger.error("❌ API连接丢失")

        if self.on_connection_status_changed:
            self.on_connection_status_changed(False)

    # ==================== 查询接口 ====================

    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        if not self.is_api_connected:
            return {"error": "API未连接"}

        response = self.api_client.get_account_info()
        if response.success:
            return response.data or {}
        else:
            return {"error": response.message}

    def get_positions(self) -> List[Dict[str, Any]]:
        """获取持仓信息"""
        if not self.is_api_connected:
            return []

        response = self.api_client.get_current_positions()
        if response.success and response.data:
            content = response.data.get("content", [])
            return content if isinstance(content, list) else []
        else:
            return []

    def get_orders(self) -> List[Dict[str, Any]]:
        """获取委托信息"""
        if not self.is_api_connected:
            return []

        response = self.api_client.get_current_orders()
        if response.success and response.data:
            content = response.data.get("content", [])
            return content if isinstance(content, list) else []
        else:
            return []

    def get_trades(self) -> List[Dict[str, Any]]:
        """获取成交信息"""
        if not self.is_api_connected:
            return []

        response = self.api_client.get_current_trades()
        if response.success and response.data:
            content = response.data.get("content", [])
            return content if isinstance(content, list) else []
        else:
            return []

    def get_commodity_prices(self) -> Dict[str, Any]:
        """获取商品价格信息"""
        if not self.is_api_connected:
            return {}

        response = self.api_client.get_commodity_strategy()
        if response.success:
            return response.data or {}
        else:
            return {}

    def cancel_all_orders(self) -> bool:
        """撤销所有订单"""
        if not self.is_api_connected:
            return False

        response = self.api_client.cancel_all_orders()
        return response.success

    def get_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        return {
            "api_connected": self.is_api_connected,
            "trading_enabled": self.is_trading_enabled,
            "trading_mode": self.trading_mode.value,
            "pending_orders_count": len(self.get_pending_orders()),
            "daily_order_count": self.daily_order_count,
            "max_daily_orders": self.max_daily_orders
        }
