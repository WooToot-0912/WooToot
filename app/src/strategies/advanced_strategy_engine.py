#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级策略引擎
基于多重技术分析的智能交易策略
"""

import cv2
import numpy as np
import logging
import time
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import statistics
from collections import deque
import pandas as pd

class SignalStrength(Enum):
    """信号强度"""
    VERY_WEAK = 0.1
    WEAK = 0.3
    MODERATE = 0.5
    STRONG = 0.7
    VERY_STRONG = 0.9

class TrendDirection(Enum):
    """趋势方向"""
    STRONG_UP = "strong_up"
    UP = "up"
    SIDEWAYS = "sideways"
    DOWN = "down"
    STRONG_DOWN = "strong_down"

@dataclass
class MarketSignal:
    """市场信号"""
    signal_type: str  # 'buy', 'sell', 'hold'
    confidence: float
    strength: SignalStrength
    timestamp: float
    price_level: float = 0.0
    volume_factor: float = 1.0
    trend_direction: TrendDirection = TrendDirection.SIDEWAYS
    indicators: Dict = None

@dataclass
class MarketData:
    """市场数据"""
    timestamp: float
    price: float
    volume: int = 0
    red_ratio: float = 0.0
    green_ratio: float = 0.0
    macd_value: float = 0.0
    volatility: float = 0.0

class AdvancedStrategyEngine:
    """高级策略引擎"""
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # 数据缓存
        self.price_history = deque(maxlen=100)
        self.signal_history = deque(maxlen=50)
        self.market_data_buffer = deque(maxlen=200)
        
        # 策略参数
        self.strategy_weights = {
            'red_green_strategy': 0.25,
            'macd_strategy': 0.20,
            'price_action_strategy': 0.20,
            'volume_strategy': 0.15,
            'trend_following_strategy': 0.20
        }
        
        # 技术指标参数
        self.ma_short_period = 5
        self.ma_long_period = 20
        self.rsi_period = 14
        self.volatility_period = 10
        
        # 信号过滤器
        self.min_confidence_threshold = 0.6
        self.signal_cooldown = 30  # 30秒信号冷却
        self.last_signal_time = 0
        
        # 适应性参数
        self.adaptive_mode = True
        self.market_regime = "normal"  # normal, volatile, trending
        
        self.logger.info("高级策略引擎初始化完成")
    
    def analyze_market(self, image: np.ndarray, price_data: Dict = None) -> MarketSignal:
        """综合市场分析"""
        try:
            # 1. 基础数据提取
            market_data = self._extract_market_data(image, price_data)
            self.market_data_buffer.append(market_data)
            
            # 2. 市场状态识别
            market_regime = self._identify_market_regime()
            
            # 3. 动态调整策略权重
            if self.adaptive_mode:
                self._adjust_strategy_weights(market_regime)
            
            # 4. 多策略信号生成
            signals = self._generate_multi_strategy_signals(market_data)
            
            # 5. 信号融合和过滤
            final_signal = self._fuse_and_filter_signals(signals, market_data)
            
            # 6. 信号增强
            enhanced_signal = self._enhance_signal(final_signal, market_data)
            
            # 7. 记录信号历史
            self.signal_history.append(enhanced_signal)
            
            return enhanced_signal
            
        except Exception as e:
            self.logger.error(f"市场分析失败: {e}")
            return MarketSignal(
                signal_type='hold',
                confidence=0.0,
                strength=SignalStrength.VERY_WEAK,
                timestamp=time.time()
            )
    
    def _extract_market_data(self, image: np.ndarray, price_data: Dict) -> MarketData:
        """提取市场数据"""
        try:
            # 基础图像分析
            red_ratio, green_ratio = self._analyze_color_distribution(image)
            
            # 价格数据
            current_price = price_data.get('price', 0.0) if price_data else 0.0
            volume = price_data.get('volume', 0) if price_data else 0
            
            # 计算技术指标
            macd_value = self._calculate_macd(current_price)
            volatility = self._calculate_volatility()
            
            return MarketData(
                timestamp=time.time(),
                price=current_price,
                volume=volume,
                red_ratio=red_ratio,
                green_ratio=green_ratio,
                macd_value=macd_value,
                volatility=volatility
            )
            
        except Exception as e:
            self.logger.error(f"市场数据提取失败: {e}")
            return MarketData(timestamp=time.time(), price=0.0)
    
    def _analyze_color_distribution(self, image: np.ndarray) -> Tuple[float, float]:
        """分析颜色分布（改进版）"""
        try:
            if image is None:
                return 0.0, 0.0
            
            # 转换为HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 改进的颜色范围定义
            red_ranges = [
                (np.array([0, 70, 70]), np.array([10, 255, 255])),
                (np.array([170, 70, 70]), np.array([180, 255, 255]))
            ]
            green_ranges = [
                (np.array([35, 70, 70]), np.array([85, 255, 255]))
            ]
            
            # 创建掩码
            red_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in red_ranges:
                red_mask += cv2.inRange(hsv, lower, upper)
            
            green_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in green_ranges:
                green_mask += cv2.inRange(hsv, lower, upper)
            
            # 形态学处理减少噪声
            kernel = np.ones((3, 3), np.uint8)
            red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
            
            # 计算像素比例
            total_pixels = image.shape[0] * image.shape[1]
            red_ratio = cv2.countNonZero(red_mask) / total_pixels
            green_ratio = cv2.countNonZero(green_mask) / total_pixels
            
            return red_ratio, green_ratio
            
        except Exception as e:
            self.logger.error(f"颜色分布分析失败: {e}")
            return 0.0, 0.0
    
    def _identify_market_regime(self) -> str:
        """识别市场状态"""
        try:
            if len(self.market_data_buffer) < 20:
                return "normal"
            
            # 计算最近20个数据点的统计特征
            recent_data = list(self.market_data_buffer)[-20:]
            
            # 价格波动率
            prices = [data.price for data in recent_data if data.price > 0]
            if len(prices) < 10:
                return "normal"
            
            price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] 
                           for i in range(1, len(prices)) if prices[i-1] > 0]
            
            if not price_changes:
                return "normal"
            
            avg_volatility = statistics.mean(price_changes)
            
            # 趋势强度
            price_trend = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
            
            # 市场状态判断
            if avg_volatility > 0.02:  # 2%以上波动
                return "volatile"
            elif abs(price_trend) > 0.05:  # 5%以上趋势
                return "trending"
            else:
                return "normal"
                
        except Exception as e:
            self.logger.error(f"市场状态识别失败: {e}")
            return "normal"
    
    def _adjust_strategy_weights(self, market_regime: str):
        """根据市场状态调整策略权重"""
        try:
            if market_regime == "volatile":
                # 波动市场：降低趋势跟随，增加均值回归
                self.strategy_weights.update({
                    'red_green_strategy': 0.30,
                    'macd_strategy': 0.15,
                    'price_action_strategy': 0.25,
                    'volume_strategy': 0.20,
                    'trend_following_strategy': 0.10
                })
            elif market_regime == "trending":
                # 趋势市场：增加趋势跟随
                self.strategy_weights.update({
                    'red_green_strategy': 0.20,
                    'macd_strategy': 0.25,
                    'price_action_strategy': 0.15,
                    'volume_strategy': 0.10,
                    'trend_following_strategy': 0.30
                })
            else:
                # 正常市场：平衡权重
                self.strategy_weights.update({
                    'red_green_strategy': 0.25,
                    'macd_strategy': 0.20,
                    'price_action_strategy': 0.20,
                    'volume_strategy': 0.15,
                    'trend_following_strategy': 0.20
                })
            
            self.market_regime = market_regime
            
        except Exception as e:
            self.logger.error(f"策略权重调整失败: {e}")
    
    def _generate_multi_strategy_signals(self, market_data: MarketData) -> Dict[str, MarketSignal]:
        """生成多策略信号"""
        signals = {}
        
        try:
            # 1. 红绿线策略（改进版）
            signals['red_green_strategy'] = self._red_green_strategy_v2(market_data)
            
            # 2. MACD策略（改进版）
            signals['macd_strategy'] = self._macd_strategy_v2(market_data)
            
            # 3. 价格行为策略
            signals['price_action_strategy'] = self._price_action_strategy(market_data)
            
            # 4. 成交量策略
            signals['volume_strategy'] = self._volume_strategy(market_data)
            
            # 5. 趋势跟随策略
            signals['trend_following_strategy'] = self._trend_following_strategy(market_data)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"多策略信号生成失败: {e}")
            return {}
    
    def _red_green_strategy_v2(self, market_data: MarketData) -> MarketSignal:
        """改进的红绿线策略"""
        try:
            red_ratio = market_data.red_ratio
            green_ratio = market_data.green_ratio
            
            # 基础信号
            if red_ratio > 0.015 and red_ratio > green_ratio * 1.8:
                base_signal = 'sell'
                base_confidence = min(red_ratio * 15, 0.9)
            elif green_ratio > 0.015 and green_ratio > red_ratio * 1.8:
                base_signal = 'buy'
                base_confidence = min(green_ratio * 15, 0.9)
            else:
                base_signal = 'hold'
                base_confidence = 0.1
            
            # 信号增强
            if len(self.market_data_buffer) >= 3:
                recent_data = list(self.market_data_buffer)[-3:]
                
                # 连续信号确认
                if base_signal == 'buy':
                    green_trend = [data.green_ratio for data in recent_data]
                    if all(green_trend[i] >= green_trend[i-1] for i in range(1, len(green_trend))):
                        base_confidence *= 1.2
                elif base_signal == 'sell':
                    red_trend = [data.red_ratio for data in recent_data]
                    if all(red_trend[i] >= red_trend[i-1] for i in range(1, len(red_trend))):
                        base_confidence *= 1.2
            
            # 计算信号强度
            if base_confidence > 0.8:
                strength = SignalStrength.VERY_STRONG
            elif base_confidence > 0.6:
                strength = SignalStrength.STRONG
            elif base_confidence > 0.4:
                strength = SignalStrength.MODERATE
            elif base_confidence > 0.2:
                strength = SignalStrength.WEAK
            else:
                strength = SignalStrength.VERY_WEAK
            
            return MarketSignal(
                signal_type=base_signal,
                confidence=min(base_confidence, 0.95),
                strength=strength,
                timestamp=time.time(),
                indicators={'red_ratio': red_ratio, 'green_ratio': green_ratio}
            )
            
        except Exception as e:
            self.logger.error(f"红绿线策略失败: {e}")
            return MarketSignal(
                signal_type='hold',
                confidence=0.0,
                strength=SignalStrength.VERY_WEAK,
                timestamp=time.time()
            )
    
    def _price_action_strategy(self, market_data: MarketData) -> MarketSignal:
        """价格行为策略"""
        try:
            if len(self.market_data_buffer) < 10:
                return MarketSignal(
                    signal_type='hold',
                    confidence=0.0,
                    strength=SignalStrength.VERY_WEAK,
                    timestamp=time.time()
                )
            
            recent_prices = [data.price for data in list(self.market_data_buffer)[-10:] if data.price > 0]
            if len(recent_prices) < 5:
                return MarketSignal(
                    signal_type='hold',
                    confidence=0.0,
                    strength=SignalStrength.VERY_WEAK,
                    timestamp=time.time()
                )
            
            # 计算移动平均
            short_ma = statistics.mean(recent_prices[-self.ma_short_period:])
            long_ma = statistics.mean(recent_prices[-self.ma_long_period:]) if len(recent_prices) >= self.ma_long_period else short_ma
            
            current_price = recent_prices[-1]
            
            # 信号生成
            if short_ma > long_ma * 1.01 and current_price > short_ma:
                signal_type = 'buy'
                confidence = min((short_ma - long_ma) / long_ma * 10, 0.8)
            elif short_ma < long_ma * 0.99 and current_price < short_ma:
                signal_type = 'sell'
                confidence = min((long_ma - short_ma) / long_ma * 10, 0.8)
            else:
                signal_type = 'hold'
                confidence = 0.1
            
            # 计算强度
            strength = SignalStrength.MODERATE if confidence > 0.5 else SignalStrength.WEAK
            
            return MarketSignal(
                signal_type=signal_type,
                confidence=confidence,
                strength=strength,
                timestamp=time.time(),
                indicators={'short_ma': short_ma, 'long_ma': long_ma, 'current_price': current_price}
            )
            
        except Exception as e:
            self.logger.error(f"价格行为策略失败: {e}")
            return MarketSignal(
                signal_type='hold',
                confidence=0.0,
                strength=SignalStrength.VERY_WEAK,
                timestamp=time.time()
            )
    
    def _volume_strategy(self, market_data: MarketData) -> MarketSignal:
        """成交量策略"""
        try:
            if len(self.market_data_buffer) < 5:
                return MarketSignal(
                    signal_type='hold',
                    confidence=0.0,
                    strength=SignalStrength.VERY_WEAK,
                    timestamp=time.time()
                )
            
            recent_volumes = [data.volume for data in list(self.market_data_buffer)[-5:] if data.volume > 0]
            if len(recent_volumes) < 3:
                return MarketSignal(
                    signal_type='hold',
                    confidence=0.0,
                    strength=SignalStrength.VERY_WEAK,
                    timestamp=time.time()
                )
            
            current_volume = recent_volumes[-1]
            avg_volume = statistics.mean(recent_volumes[:-1])
            
            # 量价分析
            recent_prices = [data.price for data in list(self.market_data_buffer)[-5:] if data.price > 0]
            if len(recent_prices) >= 2:
                price_change = (recent_prices[-1] - recent_prices[-2]) / recent_prices[-2]
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                
                # 量价配合判断
                if price_change > 0.01 and volume_ratio > 1.5:  # 价升量增
                    signal_type = 'buy'
                    confidence = min(volume_ratio * 0.3, 0.7)
                elif price_change < -0.01 and volume_ratio > 1.5:  # 价跌量增
                    signal_type = 'sell'
                    confidence = min(volume_ratio * 0.3, 0.7)
                else:
                    signal_type = 'hold'
                    confidence = 0.1
            else:
                signal_type = 'hold'
                confidence = 0.1
            
            strength = SignalStrength.MODERATE if confidence > 0.4 else SignalStrength.WEAK
            
            return MarketSignal(
                signal_type=signal_type,
                confidence=confidence,
                strength=strength,
                timestamp=time.time(),
                volume_factor=current_volume / avg_volume if avg_volume > 0 else 1,
                indicators={'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1}
            )
            
        except Exception as e:
            self.logger.error(f"成交量策略失败: {e}")
            return MarketSignal(
                signal_type='hold',
                confidence=0.0,
                strength=SignalStrength.VERY_WEAK,
                timestamp=time.time()
            )
    
    def _trend_following_strategy(self, market_data: MarketData) -> MarketSignal:
        """趋势跟随策略"""
        try:
            if len(self.market_data_buffer) < 15:
                return MarketSignal(
                    signal_type='hold',
                    confidence=0.0,
                    strength=SignalStrength.VERY_WEAK,
                    timestamp=time.time()
                )
            
            # 识别趋势方向
            trend_direction = self._identify_trend_direction()
            
            # 根据趋势生成信号
            if trend_direction == TrendDirection.STRONG_UP:
                signal_type = 'buy'
                confidence = 0.8
                strength = SignalStrength.STRONG
            elif trend_direction == TrendDirection.UP:
                signal_type = 'buy'
                confidence = 0.6
                strength = SignalStrength.MODERATE
            elif trend_direction == TrendDirection.STRONG_DOWN:
                signal_type = 'sell'
                confidence = 0.8
                strength = SignalStrength.STRONG
            elif trend_direction == TrendDirection.DOWN:
                signal_type = 'sell'
                confidence = 0.6
                strength = SignalStrength.MODERATE
            else:
                signal_type = 'hold'
                confidence = 0.1
                strength = SignalStrength.WEAK
            
            return MarketSignal(
                signal_type=signal_type,
                confidence=confidence,
                strength=strength,
                timestamp=time.time(),
                trend_direction=trend_direction,
                indicators={'trend_direction': trend_direction.value}
            )
            
        except Exception as e:
            self.logger.error(f"趋势跟随策略失败: {e}")
            return MarketSignal(
                signal_type='hold',
                confidence=0.0,
                strength=SignalStrength.VERY_WEAK,
                timestamp=time.time()
            )
    
    def _identify_trend_direction(self) -> TrendDirection:
        """识别趋势方向"""
        try:
            recent_data = list(self.market_data_buffer)[-15:]
            prices = [data.price for data in recent_data if data.price > 0]
            
            if len(prices) < 10:
                return TrendDirection.SIDEWAYS
            
            # 线性回归计算趋势斜率
            x = list(range(len(prices)))
            y = prices
            
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            avg_price = sum_y / n
            
            # 趋势强度
            trend_strength = abs(slope) / avg_price
            
            if slope > 0 and trend_strength > 0.02:
                return TrendDirection.STRONG_UP
            elif slope > 0 and trend_strength > 0.005:
                return TrendDirection.UP
            elif slope < 0 and trend_strength > 0.02:
                return TrendDirection.STRONG_DOWN
            elif slope < 0 and trend_strength > 0.005:
                return TrendDirection.DOWN
            else:
                return TrendDirection.SIDEWAYS
                
        except Exception as e:
            self.logger.error(f"趋势识别失败: {e}")
            return TrendDirection.SIDEWAYS
    
    def _fuse_and_filter_signals(self, signals: Dict[str, MarketSignal], 
                                market_data: MarketData) -> MarketSignal:
        """信号融合和过滤"""
        try:
            if not signals:
                return MarketSignal(
                    signal_type='hold',
                    confidence=0.0,
                    strength=SignalStrength.VERY_WEAK,
                    timestamp=time.time()
                )
            
            # 加权信号融合
            buy_score = 0.0
            sell_score = 0.0
            total_weight = 0.0
            
            all_indicators = {}
            
            for strategy_name, signal in signals.items():
                if strategy_name in self.strategy_weights:
                    weight = self.strategy_weights[strategy_name]
                    confidence = signal.confidence
                    
                    if signal.signal_type == 'buy':
                        buy_score += weight * confidence
                    elif signal.signal_type == 'sell':
                        sell_score += weight * confidence
                    
                    total_weight += weight
                    
                    # 合并指标
                    if signal.indicators:
                        all_indicators.update({
                            f"{strategy_name}_{k}": v for k, v in signal.indicators.items()
                        })
            
            # 计算最终信号
            if total_weight > 0:
                buy_score /= total_weight
                sell_score /= total_weight
            
            # 信号决策
            if buy_score > sell_score and buy_score > self.min_confidence_threshold:
                final_signal = 'buy'
                final_confidence = buy_score
            elif sell_score > buy_score and sell_score > self.min_confidence_threshold:
                final_signal = 'sell'
                final_confidence = sell_score
            else:
                final_signal = 'hold'
                final_confidence = max(buy_score, sell_score) * 0.5
            
            # 信号过滤
            current_time = time.time()
            if current_time - self.last_signal_time < self.signal_cooldown:
                if final_signal != 'hold':
                    final_confidence *= 0.5  # 降低置信度
            
            # 计算强度
            if final_confidence > 0.8:
                strength = SignalStrength.VERY_STRONG
            elif final_confidence > 0.6:
                strength = SignalStrength.STRONG
            elif final_confidence > 0.4:
                strength = SignalStrength.MODERATE
            elif final_confidence > 0.2:
                strength = SignalStrength.WEAK
            else:
                strength = SignalStrength.VERY_WEAK
            
            return MarketSignal(
                signal_type=final_signal,
                confidence=final_confidence,
                strength=strength,
                timestamp=current_time,
                price_level=market_data.price,
                volume_factor=market_data.volume,
                indicators=all_indicators
            )
            
        except Exception as e:
            self.logger.error(f"信号融合失败: {e}")
            return MarketSignal(
                signal_type='hold',
                confidence=0.0,
                strength=SignalStrength.VERY_WEAK,
                timestamp=time.time()
            )
    
    def _enhance_signal(self, signal: MarketSignal, market_data: MarketData) -> MarketSignal:
        """信号增强"""
        try:
            enhanced_signal = signal
            
            # 波动率调整
            if market_data.volatility > 0.02:  # 高波动
                enhanced_signal.confidence *= 0.8  # 降低置信度
            elif market_data.volatility < 0.005:  # 低波动
                enhanced_signal.confidence *= 1.1  # 提高置信度
            
            # 时间过滤
            current_time = time.time()
            if signal.signal_type != 'hold':
                self.last_signal_time = current_time
            
            # 限制置信度范围
            enhanced_signal.confidence = max(0.0, min(0.95, enhanced_signal.confidence))
            
            return enhanced_signal
            
        except Exception as e:
            self.logger.error(f"信号增强失败: {e}")
            return signal
    
    def get_strategy_performance(self) -> Dict:
        """获取策略表现"""
        try:
            if not self.signal_history:
                return {}
            
            recent_signals = list(self.signal_history)[-20:]
            
            buy_signals = [s for s in recent_signals if s.signal_type == 'buy']
            sell_signals = [s for s in recent_signals if s.signal_type == 'sell']
            
            avg_buy_confidence = statistics.mean([s.confidence for s in buy_signals]) if buy_signals else 0
            avg_sell_confidence = statistics.mean([s.confidence for s in sell_signals]) if sell_signals else 0
            
            return {
                'total_signals': len(recent_signals),
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'avg_buy_confidence': avg_buy_confidence,
                'avg_sell_confidence': avg_sell_confidence,
                'market_regime': self.market_regime,
                'strategy_weights': self.strategy_weights.copy()
            }
            
        except Exception as e:
            self.logger.error(f"获取策略表现失败: {e}")
            return {}

if __name__ == "__main__":
    # 测试
    engine = AdvancedStrategyEngine()
    
    # 模拟市场数据测试
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    test_price_data = {'price': 100.0, 'volume': 1000}
    
    signal = engine.analyze_market(test_image, test_price_data)
    print(f"信号: {signal}")
    
    performance = engine.get_strategy_performance()
    print(f"表现: {performance}")