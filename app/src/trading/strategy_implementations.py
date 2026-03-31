#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略实现模块
包含红绿线、MACD、K线阴阳等策略的具体实现
"""

import cv2
import numpy as np
import logging
from typing import Dict, List
import re

# 安全导入pytesseract
try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None


class RedGreenLineStrategy:
    """红绿线策略"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def detect_red_green_lines(self, image: np.ndarray) -> Dict:
        """检测红绿线趋势"""
        try:
            if image is None:
                return {'signal': 'none', 'confidence': 0.0}

            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # 定义红色和绿色的HSV范围
            red_lower1 = np.array([0, 50, 50])
            red_upper1 = np.array([10, 255, 255])
            red_lower2 = np.array([170, 50, 50])
            red_upper2 = np.array([180, 255, 255])

            green_lower = np.array([35, 50, 50])
            green_upper = np.array([85, 255, 255])

            # 创建红色和绿色掩码
            red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
            red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
            red_mask = red_mask1 + red_mask2

            green_mask = cv2.inRange(hsv, green_lower, green_upper)

            # 计算红色和绿色像素数量
            red_pixels = cv2.countNonZero(red_mask)
            green_pixels = cv2.countNonZero(green_mask)

            # 计算总面积
            total_pixels = image.shape[0] * image.shape[1]

            # 计算比例
            red_ratio = red_pixels / total_pixels
            green_ratio = green_pixels / total_pixels

            # 判断趋势
            if red_ratio > 0.01 and red_ratio > green_ratio * 1.5:
                confidence = min(red_ratio * 10, 0.9)
                return {'signal': 'sell', 'confidence': confidence, 'red_ratio': red_ratio}
            elif green_ratio > 0.01 and green_ratio > red_ratio * 1.5:
                confidence = min(green_ratio * 10, 0.9)
                return {'signal': 'buy', 'confidence': confidence, 'green_ratio': green_ratio}
            else:
                return {'signal': 'none', 'confidence': 0.0}

        except Exception as e:
            self.logger.error(f"红绿线检测失败: {e}")
            return {'signal': 'none', 'confidence': 0.0}


class MACDTrendStrategy:
    """MACD趋势策略"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def detect_macd_trend(self, image: np.ndarray) -> Dict:
        """检测MACD趋势"""
        try:
            if image is None:
                return {'signal': 'none', 'confidence': 0.0}

            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # 检测绿色（正值）和红色（负值）
            green_lower = np.array([35, 50, 50])
            green_upper = np.array([85, 255, 255])

            red_lower1 = np.array([0, 50, 50])
            red_upper1 = np.array([10, 255, 255])
            red_lower2 = np.array([170, 50, 50])
            red_upper2 = np.array([180, 255, 255])

            green_mask = cv2.inRange(hsv, green_lower, green_upper)
            red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
            red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
            red_mask = red_mask1 + red_mask2

            green_pixels = cv2.countNonZero(green_mask)
            red_pixels = cv2.countNonZero(red_mask)

            total_pixels = image.shape[0] * image.shape[1]

            if green_pixels > red_pixels * 1.2:
                confidence = min(green_pixels / total_pixels * 20, 0.7)
                return {'signal': 'buy', 'confidence': confidence}
            elif red_pixels > green_pixels * 1.2:
                confidence = min(red_pixels / total_pixels * 20, 0.7)
                return {'signal': 'sell', 'confidence': confidence}
            else:
                return {'signal': 'none', 'confidence': 0.0}

        except Exception as e:
            self.logger.error(f"MACD趋势检测失败: {e}")
            return {'signal': 'none', 'confidence': 0.0}


class KLinePatternStrategy:
    """K线阴阳策略"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def detect_kline_pattern(self, image: np.ndarray) -> Dict:
        """检测K线阴阳形态"""
        try:
            if image is None:
                return {'signal': 'none', 'confidence': 0.0}

            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 边缘检测
            edges = cv2.Canny(gray, 50, 150)

            # 查找轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 分析K线形态
            bullish_count = 0
            bearish_count = 0

            for contour in contours:
                # 计算轮廓特征
                area = cv2.contourArea(contour)
                if area < 10:  # 过滤小轮廓
                    continue

                # 获取边界矩形
                x, y, w, h = cv2.boundingRect(contour)

                # 判断K线形态（阳线：实体在上，阴线：实体在下）
                if h > w * 2:  # 长K线
                    if y < image.shape[0] / 2:  # 在上半部分
                        bullish_count += 1
                    else:  # 在下半部分
                        bearish_count += 1

            # 判断趋势
            if bullish_count > bearish_count * 1.5:
                confidence = min(bullish_count / (bullish_count + bearish_count), 0.8)
                return {'signal': 'buy', 'confidence': confidence}
            elif bearish_count > bullish_count * 1.5:
                confidence = min(bearish_count / (bullish_count + bearish_count), 0.8)
                return {'signal': 'sell', 'confidence': confidence}
            else:
                return {'signal': 'none', 'confidence': 0.0}

        except Exception as e:
            self.logger.error(f"K线形态检测失败: {e}")
            return {'signal': 'none', 'confidence': 0.0}


class SignalFusion:
    """信号融合器"""

    def __init__(self, strategy_weights: Dict[str, float]):
        self.strategy_weights = strategy_weights
        self.logger = logging.getLogger(__name__)

    def fuse_signals(self, signals: Dict[str, Dict]) -> Dict:
        """融合多个策略信号"""
        try:
            total_score = 0.0
            total_weight = 0.0
            signal_details = {}

            for strategy_name, signal in signals.items():
                if strategy_name in self.strategy_weights:
                    weight = self.strategy_weights[strategy_name]
                    signal_value = self.signal_to_value(signal['signal'])
                    confidence = signal.get('confidence', 0.0)

                    score = signal_value * confidence * weight
                    total_score += score
                    total_weight += weight

                    signal_details[strategy_name] = {
                        'signal': signal['signal'],
                        'confidence': confidence,
                        'weight': weight,
                        'score': score
                    }

            if total_weight == 0:
                return {'action': 'none', 'confidence': 0.0, 'details': signal_details}

            # 计算综合置信度
            overall_confidence = abs(total_score) / total_weight

            # 判断交易信号
            if total_score > 0.6:  # 最小信号置信度
                action = 'buy'
            elif total_score < -0.6:
                action = 'sell'
            else:
                action = 'none'

            return {
                'action': action,
                'confidence': overall_confidence,
                'score': total_score,
                'details': signal_details
            }

        except Exception as e:
            self.logger.error(f"信号融合失败: {e}")
            return {'action': 'none', 'confidence': 0.0}

    def signal_to_value(self, signal: str) -> float:
        """将信号转换为数值"""
        if signal == 'buy':
            return 1.0
        elif signal == 'sell':
            return -1.0
        else:
            return 0.0


class RiskManager:
    """风险管理器"""

    def __init__(self, max_daily_loss: float = 1000, max_position_size: int = 5):
        self.max_daily_loss = max_daily_loss
        self.max_position_size = max_position_size
        self.daily_loss = 0.0
        self.current_position_size = 0
        self.logger = logging.getLogger(__name__)

    def check_risk_limits(self, signal: Dict) -> bool:
        """检查风险限制"""
        try:
            # 检查日亏损限制
            if self.daily_loss >= self.max_daily_loss:
                self.logger.warning(f"达到日亏损限制: {self.daily_loss}")
                return False

            # 检查持仓限制
            if self.current_position_size >= self.max_position_size:
                self.logger.warning(f"达到最大持仓限制: {self.current_position_size}")
                return False

            # 检查信号置信度
            if signal.get('confidence', 0.0) < 0.6:
                self.logger.info(f"信号置信度不足: {signal.get('confidence', 0.0)}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"风险检查失败: {e}")
            return False

    def update_position(self, action: str, quantity: int = 1):
        """更新持仓"""
        if action == 'buy':
            self.current_position_size += quantity
        elif action == 'sell':
            self.current_position_size -= quantity

    def update_daily_loss(self, loss: float):
        """更新日亏损"""
        self.daily_loss += loss


if __name__ == "__main__":
    print("策略实现模块已创建")