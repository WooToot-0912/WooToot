#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险控制管理器
实现交易风险控制、资金管理、异常检测等功能
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import os

class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TradeRecord:
    """交易记录"""
    timestamp: float
    action: str  # 'buy', 'sell', 'transfer'
    price: float
    quantity: int
    profit_loss: float = 0.0
    success: bool = True
    reason: str = ""

@dataclass
class RiskMetrics:
    """风险指标"""
    daily_trades: int = 0
    daily_profit_loss: float = 0.0
    consecutive_losses: int = 0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW

class RiskManager:
    """风险控制管理器"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        # 交易记录
        self.trade_history: List[TradeRecord] = []
        self.daily_trades = 0
        self.daily_profit_loss = 0.0
        self.consecutive_losses = 0
        self.max_drawdown = 0.0
        self.peak_value = 0.0
        
        # 风险控制状态
        self.is_trading_allowed = True
        self.circuit_breaker_triggered = False
        self.last_reset_date = datetime.now().date()
        
        # 风险阈值（从配置加载）
        self.load_risk_thresholds()
        
        # 数据文件
        self.data_file = "risk_data.json"
        self.load_historical_data()
        
        self.logger.info("风险控制管理器初始化完成")
    
    def load_risk_thresholds(self):
        """加载风险阈值配置"""
        if self.config_manager:
            risk_config = self.config_manager.get('trading.risk_management', {})
            self.max_daily_trades = risk_config.get('max_daily_trades', 100)
            self.max_daily_loss = risk_config.get('max_daily_loss', 500)
            self.max_consecutive_losses = risk_config.get('max_consecutive_losses', 5)
            self.circuit_breaker_threshold = risk_config.get('circuit_breaker_threshold', -100)
            self.enable_circuit_breaker = risk_config.get('enable_circuit_breaker', True)
        else:
            # 默认值
            self.max_daily_trades = 100
            self.max_daily_loss = 500
            self.max_consecutive_losses = 5
            self.circuit_breaker_threshold = -100
            self.enable_circuit_breaker = True
    
    def load_historical_data(self):
        """加载历史数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 恢复今日数据
                today = datetime.now().date().isoformat()
                if today in data:
                    today_data = data[today]
                    self.daily_trades = today_data.get('daily_trades', 0)
                    self.daily_profit_loss = today_data.get('daily_profit_loss', 0.0)
                    self.consecutive_losses = today_data.get('consecutive_losses', 0)
                    self.max_drawdown = today_data.get('max_drawdown', 0.0)
                    self.peak_value = today_data.get('peak_value', 0.0)
                
                self.logger.info("历史风险数据加载成功")
        except Exception as e:
            self.logger.error(f"加载历史数据失败: {e}")
    
    def save_data(self):
        """保存风险数据"""
        try:
            data = {}
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            today = datetime.now().date().isoformat()
            data[today] = {
                'daily_trades': self.daily_trades,
                'daily_profit_loss': self.daily_profit_loss,
                'consecutive_losses': self.consecutive_losses,
                'max_drawdown': self.max_drawdown,
                'peak_value': self.peak_value,
                'last_update': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"保存风险数据失败: {e}")
    
    def check_daily_reset(self):
        """检查是否需要重置日数据"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.logger.info("新的一天开始，重置风险数据")
            self.daily_trades = 0
            self.daily_profit_loss = 0.0
            self.consecutive_losses = 0
            self.circuit_breaker_triggered = False
            self.is_trading_allowed = True
            self.last_reset_date = current_date
            self.save_data()
    
    def can_trade(self) -> Tuple[bool, str]:
        """检查是否允许交易"""
        self.check_daily_reset()
        
        # 检查熔断机制
        if self.circuit_breaker_triggered:
            return False, "熔断机制已触发，今日交易已停止"
        
        # 检查日交易次数限制
        if self.daily_trades >= self.max_daily_trades:
            return False, f"已达到日交易次数限制: {self.max_daily_trades}"
        
        # 检查日亏损限制
        if self.daily_profit_loss <= -self.max_daily_loss:
            return False, f"已达到日亏损限制: {self.max_daily_loss}"
        
        # 检查连续亏损次数
        if self.consecutive_losses >= self.max_consecutive_losses:
            return False, f"连续亏损次数过多: {self.consecutive_losses}"
        
        # 检查熔断阈值
        if (self.enable_circuit_breaker and 
            self.daily_profit_loss <= self.circuit_breaker_threshold):
            self.circuit_breaker_triggered = True
            self.is_trading_allowed = False
            self.logger.critical(f"触发熔断机制: 日亏损 {self.daily_profit_loss}")
            return False, "触发熔断机制，自动停止交易"
        
        return True, "允许交易"
    
    def record_trade(self, action: str, price: float, quantity: int, 
                    profit_loss: float = 0.0, success: bool = True, 
                    reason: str = "") -> bool:
        """记录交易"""
        try:
            self.check_daily_reset()
            
            # 创建交易记录
            trade = TradeRecord(
                timestamp=time.time(),
                action=action,
                price=price,
                quantity=quantity,
                profit_loss=profit_loss,
                success=success,
                reason=reason
            )
            
            self.trade_history.append(trade)
            
            # 更新统计数据
            if success:
                self.daily_trades += 1
                self.daily_profit_loss += profit_loss
                
                # 更新连续亏损计数
                if profit_loss < 0:
                    self.consecutive_losses += 1
                else:
                    self.consecutive_losses = 0
                
                # 更新最大回撤
                if self.daily_profit_loss > self.peak_value:
                    self.peak_value = self.daily_profit_loss
                
                current_drawdown = self.peak_value - self.daily_profit_loss
                if current_drawdown > self.max_drawdown:
                    self.max_drawdown = current_drawdown
            
            # 保存数据
            self.save_data()
            
            self.logger.info(f"交易记录已保存: {action} {price} {quantity} P&L:{profit_loss}")
            return True
            
        except Exception as e:
            self.logger.error(f"记录交易失败: {e}")
            return False
    
    def get_risk_metrics(self) -> RiskMetrics:
        """获取风险指标"""
        self.check_daily_reset()
        
        # 计算胜率
        recent_trades = [t for t in self.trade_history 
                        if t.timestamp > time.time() - 86400 and t.success]
        
        if recent_trades:
            winning_trades = len([t for t in recent_trades if t.profit_loss > 0])
            win_rate = winning_trades / len(recent_trades) * 100
        else:
            win_rate = 0.0
        
        # 确定风险等级
        risk_level = self.calculate_risk_level()
        
        return RiskMetrics(
            daily_trades=self.daily_trades,
            daily_profit_loss=self.daily_profit_loss,
            consecutive_losses=self.consecutive_losses,
            max_drawdown=self.max_drawdown,
            win_rate=win_rate,
            risk_level=risk_level
        )
    
    def calculate_risk_level(self) -> RiskLevel:
        """计算风险等级"""
        # 基于多个指标计算风险等级
        risk_score = 0
        
        # 日亏损比例
        loss_ratio = abs(self.daily_profit_loss) / self.max_daily_loss
        if loss_ratio > 0.8:
            risk_score += 3
        elif loss_ratio > 0.6:
            risk_score += 2
        elif loss_ratio > 0.4:
            risk_score += 1
        
        # 连续亏损
        loss_ratio = self.consecutive_losses / self.max_consecutive_losses
        if loss_ratio > 0.8:
            risk_score += 3
        elif loss_ratio > 0.6:
            risk_score += 2
        elif loss_ratio > 0.4:
            risk_score += 1
        
        # 交易频率
        trade_ratio = self.daily_trades / self.max_daily_trades
        if trade_ratio > 0.9:
            risk_score += 2
        elif trade_ratio > 0.7:
            risk_score += 1
        
        # 确定风险等级
        if risk_score >= 6:
            return RiskLevel.CRITICAL
        elif risk_score >= 4:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def get_daily_summary(self) -> Dict:
        """获取日总结"""
        self.check_daily_reset()
        
        metrics = self.get_risk_metrics()
        
        return {
            'date': datetime.now().date().isoformat(),
            'total_trades': self.daily_trades,
            'profit_loss': self.daily_profit_loss,
            'consecutive_losses': self.consecutive_losses,
            'max_drawdown': self.max_drawdown,
            'win_rate': metrics.win_rate,
            'risk_level': metrics.risk_level.value,
            'circuit_breaker_triggered': self.circuit_breaker_triggered,
            'trading_allowed': self.is_trading_allowed
        }
    
    def reset_circuit_breaker(self) -> bool:
        """重置熔断机制（需要手动确认）"""
        try:
            self.circuit_breaker_triggered = False
            self.is_trading_allowed = True
            self.logger.warning("熔断机制已手动重置")
            return True
        except Exception as e:
            self.logger.error(f"重置熔断机制失败: {e}")
            return False
    
    def emergency_stop(self, reason: str = "紧急停止"):
        """紧急停止交易"""
        self.is_trading_allowed = False
        self.circuit_breaker_triggered = True
        self.logger.critical(f"紧急停止交易: {reason}")
        self.save_data()
