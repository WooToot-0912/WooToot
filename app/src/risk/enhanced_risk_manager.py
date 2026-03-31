#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强风险管理系统
智能风险控制、动态资金管理、实时风险监控
"""

import time
import logging
import json
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import statistics
import math

class RiskLevel(Enum):
    """风险等级"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PositionSide(Enum):
    """持仓方向"""
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"

@dataclass
class Position:
    """持仓信息"""
    symbol: str
    side: PositionSide
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    timestamp: float
    stop_loss: float = 0.0
    take_profit: float = 0.0

@dataclass
class RiskMetrics:
    """风险指标"""
    total_exposure: float
    max_drawdown: float
    current_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    var_95: float  # 95% VaR
    risk_score: float

@dataclass
class TradeRecord:
    """交易记录"""
    timestamp: float
    symbol: str
    action: str  # 'buy', 'sell'
    quantity: int
    price: float
    commission: float
    pnl: float
    success: bool

class EnhancedRiskManager:
    """增强风险管理器"""
    
    def __init__(self, initial_capital: float = 10000, config: Dict = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # 资金管理
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.available_capital = initial_capital
        self.peak_capital = initial_capital
        
        # 持仓管理
        self.positions: Dict[str, Position] = {}
        self.max_positions = self.config.get('max_positions', 5)
        
        # 风险参数
        self.max_daily_loss_pct = self.config.get('max_daily_loss_pct', 0.05)  # 5%
        self.max_single_loss_pct = self.config.get('max_single_loss_pct', 0.02)  # 2%
        self.max_position_size_pct = self.config.get('max_position_size_pct', 0.20)  # 20%
        self.max_correlation_exposure = self.config.get('max_correlation_exposure', 0.30)  # 30%
        
        # 动态风险调整
        self.volatility_lookback = 20
        self.risk_adjustment_factor = 1.0
        self.kelly_criterion_enabled = True
        
        # 交易记录
        self.trade_history: List[TradeRecord] = []
        self.daily_pnl: List[float] = []
        self.max_history = 1000
        
        # 风险状态
        self.risk_level = RiskLevel.LOW
        self.daily_loss = 0.0
        self.circuit_breaker_active = False
        self.emergency_stop = False
        
        # 实时监控
        self.monitor_thread = None
        self.monitor_running = False
        self.alert_callbacks = []
        
        # 风险预警阈值
        self.warning_thresholds = {
            'drawdown': 0.10,  # 10%
            'daily_loss': 0.03,  # 3%
            'concentration': 0.40,  # 40%
            'volatility': 0.05   # 5%
        }
        
        self.logger.info("增强风险管理器初始化完成")
    
    def evaluate_trade_risk(self, symbol: str, action: str, quantity: int, 
                           price: float, signal_confidence: float) -> Dict:
        """评估交易风险"""
        try:
            # 1. 基础风险检查
            basic_check = self._basic_risk_check(action, quantity, price)
            if not basic_check['allowed']:
                return basic_check
            
            # 2. 持仓风险检查
            position_check = self._position_risk_check(symbol, action, quantity, price)
            if not position_check['allowed']:
                return position_check
            
            # 3. 资金管理检查
            capital_check = self._capital_management_check(quantity, price)
            if not capital_check['allowed']:
                return capital_check
            
            # 4. 波动率调整
            volatility_adjustment = self._calculate_volatility_adjustment()
            
            # 5. Kelly准则调整
            kelly_size = self._calculate_kelly_position_size(
                symbol, signal_confidence, price, quantity
            )
            
            # 6. 最终风险评分
            risk_score = self._calculate_trade_risk_score(
                symbol, action, quantity, price, signal_confidence
            )
            
            # 7. 建议调整
            suggested_quantity = min(quantity, kelly_size, int(quantity * volatility_adjustment))
            
            return {
                'allowed': True,
                'risk_score': risk_score,
                'suggested_quantity': suggested_quantity,
                'original_quantity': quantity,
                'kelly_size': kelly_size,
                'volatility_adjustment': volatility_adjustment,
                'stop_loss': self._calculate_stop_loss(action, price),
                'take_profit': self._calculate_take_profit(action, price),
                'risk_level': self._get_risk_level_from_score(risk_score)
            }
            
        except Exception as e:
            self.logger.error(f"交易风险评估失败: {e}")
            return {
                'allowed': False,
                'reason': f"风险评估错误: {str(e)}",
                'risk_score': 1.0
            }
    
    def _basic_risk_check(self, action: str, quantity: int, price: float) -> Dict:
        """基础风险检查"""
        try:
            # 1. 紧急停止检查
            if self.emergency_stop:
                return {
                    'allowed': False,
                    'reason': "紧急停止已激活",
                    'risk_level': RiskLevel.CRITICAL
                }
            
            # 2. 熔断器检查
            if self.circuit_breaker_active:
                return {
                    'allowed': False,
                    'reason': "熔断器已激活",
                    'risk_level': RiskLevel.CRITICAL
                }
            
            # 3. 日亏损限制
            trade_value = quantity * price
            potential_loss = trade_value * self.max_single_loss_pct
            
            if self.daily_loss + potential_loss > self.current_capital * self.max_daily_loss_pct:
                return {
                    'allowed': False,
                    'reason': f"超出日亏损限制: {self.max_daily_loss_pct*100}%",
                    'risk_level': RiskLevel.HIGH
                }
            
            # 4. 资金充足性检查
            if action == 'buy' and trade_value > self.available_capital:
                return {
                    'allowed': False,
                    'reason': "资金不足",
                    'risk_level': RiskLevel.MEDIUM
                }
            
            # 5. 最大持仓数量检查
            if action == 'buy' and len(self.positions) >= self.max_positions:
                return {
                    'allowed': False,
                    'reason': f"超出最大持仓数量: {self.max_positions}",
                    'risk_level': RiskLevel.MEDIUM
                }
            
            return {'allowed': True}
            
        except Exception as e:
            self.logger.error(f"基础风险检查失败: {e}")
            return {
                'allowed': False,
                'reason': f"基础风险检查错误: {str(e)}"
            }
    
    def _position_risk_check(self, symbol: str, action: str, 
                           quantity: int, price: float) -> Dict:
        """持仓风险检查"""
        try:
            trade_value = quantity * price
            
            # 1. 单一持仓集中度检查
            max_position_value = self.current_capital * self.max_position_size_pct
            
            if symbol in self.positions:
                current_position = self.positions[symbol]
                if action == 'buy' and current_position.side == PositionSide.LONG:
                    new_value = (current_position.quantity + quantity) * price
                    if new_value > max_position_value:
                        return {
                            'allowed': False,
                            'reason': f"超出单一持仓限制: {self.max_position_size_pct*100}%",
                            'risk_level': RiskLevel.HIGH
                        }
            else:
                if trade_value > max_position_value:
                    return {
                        'allowed': False,
                        'reason': f"超出单一持仓限制: {self.max_position_size_pct*100}%",
                        'risk_level': RiskLevel.HIGH
                    }
            
            # 2. 相关性风险检查
            correlation_exposure = self._calculate_correlation_exposure(symbol, trade_value)
            if correlation_exposure > self.max_correlation_exposure:
                return {
                    'allowed': False,
                    'reason': f"超出相关性暴露限制: {self.max_correlation_exposure*100}%",
                    'risk_level': RiskLevel.HIGH
                }
            
            return {'allowed': True}
            
        except Exception as e:
            self.logger.error(f"持仓风险检查失败: {e}")
            return {
                'allowed': False,
                'reason': f"持仓风险检查错误: {str(e)}"
            }
    
    def _capital_management_check(self, quantity: int, price: float) -> Dict:
        """资金管理检查"""
        try:
            trade_value = quantity * price
            
            # 1. 可用资金检查
            if trade_value > self.available_capital * 0.95:  # 保留5%缓冲
                return {
                    'allowed': False,
                    'reason': "资金使用过度集中",
                    'risk_level': RiskLevel.MEDIUM
                }
            
            # 2. 总暴露检查
            total_exposure = self._calculate_total_exposure()
            if total_exposure + trade_value > self.current_capital * 2:  # 最大2倍杠杆
                return {
                    'allowed': False,
                    'reason': "总暴露过高",
                    'risk_level': RiskLevel.HIGH
                }
            
            return {'allowed': True}
            
        except Exception as e:
            self.logger.error(f"资金管理检查失败: {e}")
            return {
                'allowed': False,
                'reason': f"资金管理检查错误: {str(e)}"
            }
    
    def _calculate_volatility_adjustment(self) -> float:
        """计算波动率调整因子"""
        try:
            if len(self.daily_pnl) < self.volatility_lookback:
                return 1.0
            
            recent_pnl = self.daily_pnl[-self.volatility_lookback:]
            if not recent_pnl:
                return 1.0
            
            # 计算波动率
            volatility = statistics.stdev(recent_pnl) if len(recent_pnl) > 1 else 0
            avg_capital = statistics.mean([self.current_capital] * len(recent_pnl))
            
            volatility_ratio = volatility / avg_capital if avg_capital > 0 else 0
            
            # 基于波动率调整仓位
            if volatility_ratio > 0.03:  # 高波动
                return 0.7
            elif volatility_ratio > 0.02:  # 中等波动
                return 0.85
            elif volatility_ratio < 0.01:  # 低波动
                return 1.15
            else:
                return 1.0
                
        except Exception as e:
            self.logger.error(f"波动率调整计算失败: {e}")
            return 1.0
    
    def _calculate_kelly_position_size(self, symbol: str, win_probability: float, 
                                     price: float, max_quantity: int) -> int:
        """计算Kelly准则建议仓位"""
        try:
            if not self.kelly_criterion_enabled or win_probability <= 0.5:
                return max_quantity
            
            # 历史胜率和盈亏比
            recent_trades = [t for t in self.trade_history[-50:] if t.symbol == symbol]
            if len(recent_trades) < 10:
                return max_quantity
            
            wins = [t for t in recent_trades if t.pnl > 0]
            losses = [t for t in recent_trades if t.pnl < 0]
            
            if not wins or not losses:
                return max_quantity
            
            avg_win = statistics.mean([t.pnl for t in wins])
            avg_loss = abs(statistics.mean([t.pnl for t in losses]))
            
            win_rate = len(wins) / len(recent_trades)
            win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 1
            
            # Kelly公式: f = (bp - q) / b
            # 其中 b = 盈亏比，p = 胜率，q = 败率
            kelly_fraction = (win_loss_ratio * win_rate - (1 - win_rate)) / win_loss_ratio
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # 限制在0-25%之间
            
            # 基于Kelly比例计算建议仓位
            kelly_capital = self.current_capital * kelly_fraction
            kelly_quantity = int(kelly_capital / price)
            
            return min(kelly_quantity, max_quantity)
            
        except Exception as e:
            self.logger.error(f"Kelly仓位计算失败: {e}")
            return max_quantity
    
    def _calculate_trade_risk_score(self, symbol: str, action: str, 
                                  quantity: int, price: float, 
                                  signal_confidence: float) -> float:
        """计算交易风险评分"""
        try:
            risk_factors = []
            
            # 1. 仓位大小风险
            trade_value = quantity * price
            position_risk = trade_value / self.current_capital
            risk_factors.append(position_risk * 2)
            
            # 2. 资金使用风险
            capital_usage = trade_value / self.available_capital
            risk_factors.append(capital_usage)
            
            # 3. 持仓集中度风险
            if len(self.positions) > 0:
                concentration = len([p for p in self.positions.values() 
                                   if p.side != PositionSide.FLAT]) / self.max_positions
                risk_factors.append(concentration)
            
            # 4. 信号质量风险
            signal_risk = 1 - signal_confidence
            risk_factors.append(signal_risk)
            
            # 5. 市场波动风险
            volatility_risk = self._calculate_current_volatility_risk()
            risk_factors.append(volatility_risk)
            
            # 6. 回撤风险
            drawdown_risk = self._calculate_current_drawdown() / 0.20  # 20%为满分
            risk_factors.append(drawdown_risk)
            
            # 综合风险评分
            avg_risk = statistics.mean(risk_factors)
            max_risk = max(risk_factors)
            
            # 加权组合（平均风险70%，最大风险30%）
            combined_risk = avg_risk * 0.7 + max_risk * 0.3
            
            return min(1.0, max(0.0, combined_risk))
            
        except Exception as e:
            self.logger.error(f"风险评分计算失败: {e}")
            return 0.5
    
    def update_position(self, symbol: str, action: str, quantity: int, 
                       price: float, commission: float = 0) -> bool:
        """更新持仓"""
        try:
            current_time = time.time()
            
            # 更新或创建持仓
            if symbol in self.positions:
                position = self.positions[symbol]
                
                if action == 'buy':
                    if position.side == PositionSide.LONG:
                        # 加仓
                        total_quantity = position.quantity + quantity
                        total_cost = position.avg_price * position.quantity + price * quantity
                        position.avg_price = total_cost / total_quantity
                        position.quantity = total_quantity
                    elif position.side == PositionSide.SHORT:
                        # 平空仓
                        if quantity >= position.quantity:
                            # 完全平仓或转多
                            remaining = quantity - position.quantity
                            if remaining > 0:
                                position.side = PositionSide.LONG
                                position.quantity = remaining
                                position.avg_price = price
                            else:
                                position.side = PositionSide.FLAT
                                position.quantity = 0
                        else:
                            position.quantity -= quantity
                    else:  # FLAT
                        position.side = PositionSide.LONG
                        position.quantity = quantity
                        position.avg_price = price
                        
                elif action == 'sell':
                    if position.side == PositionSide.LONG:
                        # 平多仓
                        if quantity >= position.quantity:
                            # 完全平仓或转空
                            remaining = quantity - position.quantity
                            pnl = (price - position.avg_price) * position.quantity - commission
                            self._record_trade(symbol, 'sell', position.quantity, price, commission, pnl)
                            
                            if remaining > 0:
                                position.side = PositionSide.SHORT
                                position.quantity = remaining
                                position.avg_price = price
                            else:
                                position.side = PositionSide.FLAT
                                position.quantity = 0
                        else:
                            pnl = (price - position.avg_price) * quantity - commission
                            self._record_trade(symbol, 'sell', quantity, price, commission, pnl)
                            position.quantity -= quantity
                            
                    elif position.side == PositionSide.SHORT:
                        # 加空仓
                        total_quantity = position.quantity + quantity
                        total_cost = position.avg_price * position.quantity + price * quantity
                        position.avg_price = total_cost / total_quantity
                        position.quantity = total_quantity
                    else:  # FLAT
                        position.side = PositionSide.SHORT
                        position.quantity = quantity
                        position.avg_price = price
                
                position.timestamp = current_time
                
            else:
                # 新建持仓
                side = PositionSide.LONG if action == 'buy' else PositionSide.SHORT
                self.positions[symbol] = Position(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    avg_price=price,
                    current_price=price,
                    unrealized_pnl=0.0,
                    timestamp=current_time
                )
            
            # 更新资金
            trade_value = quantity * price + commission
            if action == 'buy':
                self.available_capital -= trade_value
            else:
                self.available_capital += trade_value
            
            # 记录交易
            if action == 'buy':
                self._record_trade(symbol, action, quantity, price, commission, -commission)
            
            self.logger.info(f"持仓更新: {symbol} {action} {quantity}@{price}")
            return True
            
        except Exception as e:
            self.logger.error(f"持仓更新失败: {e}")
            return False
    
    def update_market_prices(self, price_data: Dict[str, float]):
        """更新市场价格"""
        try:
            total_unrealized_pnl = 0.0
            
            for symbol, current_price in price_data.items():
                if symbol in self.positions:
                    position = self.positions[symbol]
                    position.current_price = current_price
                    
                    # 计算未实现盈亏
                    if position.side == PositionSide.LONG:
                        position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
                    elif position.side == PositionSide.SHORT:
                        position.unrealized_pnl = (position.avg_price - current_price) * position.quantity
                    else:
                        position.unrealized_pnl = 0.0
                    
                    total_unrealized_pnl += position.unrealized_pnl
                    
                    # 检查止损止盈
                    self._check_stop_orders(position)
            
            # 更新总资金
            self.current_capital = self.available_capital + total_unrealized_pnl
            self.peak_capital = max(self.peak_capital, self.current_capital)
            
            # 更新风险状态
            self._update_risk_status()
            
        except Exception as e:
            self.logger.error(f"市场价格更新失败: {e}")
    
    def get_risk_metrics(self) -> RiskMetrics:
        """获取风险指标"""
        try:
            # 计算各项风险指标
            total_exposure = self._calculate_total_exposure()
            max_drawdown = self._calculate_max_drawdown()
            current_drawdown = self._calculate_current_drawdown()
            sharpe_ratio = self._calculate_sharpe_ratio()
            win_rate = self._calculate_win_rate()
            profit_factor = self._calculate_profit_factor()
            var_95 = self._calculate_var_95()
            risk_score = self._calculate_overall_risk_score()
            
            return RiskMetrics(
                total_exposure=total_exposure,
                max_drawdown=max_drawdown,
                current_drawdown=current_drawdown,
                sharpe_ratio=sharpe_ratio,
                win_rate=win_rate,
                profit_factor=profit_factor,
                var_95=var_95,
                risk_score=risk_score
            )
            
        except Exception as e:
            self.logger.error(f"风险指标计算失败: {e}")
            return RiskMetrics(
                total_exposure=0.0,
                max_drawdown=0.0,
                current_drawdown=0.0,
                sharpe_ratio=0.0,
                win_rate=0.0,
                profit_factor=1.0,
                var_95=0.0,
                risk_score=0.5
            )
    
    def emergency_liquidate_all(self, reason: str = "紧急平仓"):
        """紧急平仓所有持仓"""
        try:
            self.emergency_stop = True
            self.logger.critical(f"执行紧急平仓: {reason}")
            
            for symbol, position in self.positions.items():
                if position.side != PositionSide.FLAT and position.quantity > 0:
                    # 这里应该调用实际的平仓接口
                    self.logger.critical(f"紧急平仓: {symbol} {position.quantity}")
                    
                    # 更新持仓状态
                    position.side = PositionSide.FLAT
                    position.quantity = 0
                    position.unrealized_pnl = 0.0
            
            # 触发报警
            self._trigger_alert("emergency_liquidation", {
                'reason': reason,
                'timestamp': time.time(),
                'positions_closed': len(self.positions)
            })
            
        except Exception as e:
            self.logger.error(f"紧急平仓失败: {e}")
    
    def _record_trade(self, symbol: str, action: str, quantity: int, 
                     price: float, commission: float, pnl: float):
        """记录交易"""
        trade = TradeRecord(
            timestamp=time.time(),
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            commission=commission,
            pnl=pnl,
            success=True
        )
        
        self.trade_history.append(trade)
        if len(self.trade_history) > self.max_history:
            self.trade_history.pop(0)
        
        # 更新日盈亏
        today_pnl = sum([t.pnl for t in self.trade_history 
                        if time.time() - t.timestamp < 86400])
        
        if len(self.daily_pnl) == 0 or time.time() - self.trade_history[-2].timestamp > 86400:
            self.daily_pnl.append(today_pnl)
        else:
            self.daily_pnl[-1] = today_pnl
        
        if len(self.daily_pnl) > 100:
            self.daily_pnl.pop(0)
    
    def start_monitoring(self):
        """启动风险监控"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitor_running = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            self.logger.info("风险监控已启动")
    
    def stop_monitoring(self):
        """停止风险监控"""
        self.monitor_running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("风险监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.monitor_running:
            try:
                # 检查风险状态
                self._check_risk_limits()
                
                # 检查持仓风险
                self._check_position_risks()
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                self.logger.error(f"风险监控错误: {e}")
                time.sleep(30)

if __name__ == "__main__":
    # 测试
    risk_manager = EnhancedRiskManager(initial_capital=10000)
    risk_manager.start_monitoring()
    
    # 模拟交易风险评估
    result = risk_manager.evaluate_trade_risk("TEST", "buy", 100, 50.0, 0.8)
    print(f"风险评估结果: {result}")
    
    # 获取风险指标
    metrics = risk_manager.get_risk_metrics()
    print(f"风险指标: {metrics}")