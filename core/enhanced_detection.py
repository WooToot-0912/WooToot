#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强检测模块
扩展原有黄线检测功能，添加红绿K线、MACD、均线检测
支持多种交易策略的技术指标识别
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

class SignalType(Enum):
    """信号类型"""
    BULLISH = "bullish"      # 看涨
    BEARISH = "bearish"      # 看跌
    NEUTRAL = "neutral"      # 中性
    UNKNOWN = "unknown"      # 未知

class IndicatorType(Enum):
    """指标类型"""
    KLINE = "kline"          # K线
    MACD = "macd"            # MACD
    MOVING_AVERAGE = "ma"    # 均线
    VOLUME = "volume"        # 成交量

class ColorRange:
    """颜色范围定义"""
    
    # 红色范围（阳线）
    RED_RANGES = [
        ([0, 50, 50], [10, 255, 255]),      # 红色1
        ([170, 50, 50], [180, 255, 255])   # 红色2
    ]
    
    # 绿色范围（阴线）
    GREEN_RANGES = [
        ([40, 50, 50], [80, 255, 255])     # 绿色
    ]
    
    # 蓝色范围（均线）
    BLUE_RANGES = [
        ([100, 50, 50], [130, 255, 255])   # 蓝色
    ]
    
    # 黄色范围（原有黄线）
    YELLOW_RANGES = [
        ([20, 50, 50], [30, 255, 255])     # 黄色
    ]
    
    # 白色范围（均线）
    WHITE_RANGES = [
        ([0, 0, 200], [180, 30, 255])      # 白色
    ]

class EnhancedDetector:
    """增强检测器"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager

        # 如果没有提供配置管理器，尝试导入全局配置
        if self.config_manager is None:
            try:
                from utils.resource_path import config_manager as global_config
                self.config_manager = global_config
            except ImportError:
                self.config_manager = None
        
        # 检测区域配置
        self.detection_regions = {
            'kline': {'x_ratio': 0.1, 'y_ratio': 0.1, 'width_ratio': 0.6, 'height_ratio': 0.6},
            'macd': {'x_ratio': 0.1, 'y_ratio': 0.7, 'width_ratio': 0.6, 'height_ratio': 0.2},
            'volume': {'x_ratio': 0.1, 'y_ratio': 0.65, 'width_ratio': 0.6, 'height_ratio': 0.1}
        }
        
        # 加载配置
        self.load_config()
        
        self.logger.info("增强检测器初始化完成")
    
    def load_config(self):
        """加载配置"""
        if self.config_manager:
            detection_config = self.config_manager.get('enhanced_detection', {})
            
            # 更新检测区域
            regions = detection_config.get('regions', {})
            for region_name, region_config in regions.items():
                if region_name in self.detection_regions:
                    self.detection_regions[region_name].update(region_config)
    
    def detect_kline_signal(self, image: np.ndarray) -> Dict[str, Any]:
        """检测K线信号"""
        try:
            # 获取K线检测区域
            kline_region = self._get_detection_region(image, 'kline')
            
            # 转换为HSV
            hsv = cv2.cvtColor(kline_region, cv2.COLOR_BGR2HSV)
            
            # 检测红色K线（阳线）
            red_mask = self._create_color_mask(hsv, ColorRange.RED_RANGES)
            red_pixels = cv2.countNonZero(red_mask)
            
            # 检测绿色K线（阴线）
            green_mask = self._create_color_mask(hsv, ColorRange.GREEN_RANGES)
            green_pixels = cv2.countNonZero(green_mask)
            
            # 判断信号
            total_pixels = kline_region.shape[0] * kline_region.shape[1]
            red_ratio = red_pixels / total_pixels
            green_ratio = green_pixels / total_pixels
            
            # 信号判断逻辑
            if red_ratio > 0.01 and red_ratio > green_ratio * 1.5:
                signal = SignalType.BULLISH
                confidence = min(red_ratio * 100, 1.0)
            elif green_ratio > 0.01 and green_ratio > red_ratio * 1.5:
                signal = SignalType.BEARISH
                confidence = min(green_ratio * 100, 1.0)
            else:
                signal = SignalType.NEUTRAL
                confidence = 0.5
            
            return {
                'signal': signal,
                'confidence': confidence,
                'red_ratio': red_ratio,
                'green_ratio': green_ratio,
                'red_pixels': red_pixels,
                'green_pixels': green_pixels
            }
            
        except Exception as e:
            self.logger.error(f"K线信号检测失败: {e}")
            return {
                'signal': SignalType.UNKNOWN,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def detect_macd_signal(self, image: np.ndarray) -> Dict[str, Any]:
        """检测MACD信号"""
        try:
            # 获取MACD检测区域
            macd_region = self._get_detection_region(image, 'macd')
            
            # 转换为HSV
            hsv = cv2.cvtColor(macd_region, cv2.COLOR_BGR2HSV)
            
            # 检测红色柱（多头）
            red_mask = self._create_color_mask(hsv, ColorRange.RED_RANGES)
            red_pixels = cv2.countNonZero(red_mask)
            
            # 检测绿色柱（空头）
            green_mask = self._create_color_mask(hsv, ColorRange.GREEN_RANGES)
            green_pixels = cv2.countNonZero(green_mask)
            
            # 计算最新柱状图位置（右侧区域）
            height, width = macd_region.shape[:2]
            latest_region = macd_region[:, int(width*0.8):]  # 取右侧20%区域
            
            # 在最新区域重新检测
            latest_hsv = cv2.cvtColor(latest_region, cv2.COLOR_BGR2HSV)
            latest_red = cv2.countNonZero(self._create_color_mask(latest_hsv, ColorRange.RED_RANGES))
            latest_green = cv2.countNonZero(self._create_color_mask(latest_hsv, ColorRange.GREEN_RANGES))
            
            # 信号判断
            if latest_red > latest_green and latest_red > 10:
                signal = SignalType.BULLISH
                confidence = min(latest_red / (latest_region.shape[0] * latest_region.shape[1]) * 10, 1.0)
            elif latest_green > latest_red and latest_green > 10:
                signal = SignalType.BEARISH
                confidence = min(latest_green / (latest_region.shape[0] * latest_region.shape[1]) * 10, 1.0)
            else:
                signal = SignalType.NEUTRAL
                confidence = 0.5
            
            return {
                'signal': signal,
                'confidence': confidence,
                'red_pixels': red_pixels,
                'green_pixels': green_pixels,
                'latest_red': latest_red,
                'latest_green': latest_green
            }
            
        except Exception as e:
            self.logger.error(f"MACD信号检测失败: {e}")
            return {
                'signal': SignalType.UNKNOWN,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def detect_moving_average_trend(self, image: np.ndarray) -> Dict[str, Any]:
        """检测均线趋势"""
        try:
            # 获取K线检测区域
            kline_region = self._get_detection_region(image, 'kline')
            
            # 转换为HSV
            hsv = cv2.cvtColor(kline_region, cv2.COLOR_BGR2HSV)
            
            # 检测蓝色均线
            blue_mask = self._create_color_mask(hsv, ColorRange.BLUE_RANGES)
            
            # 检测黄色均线
            yellow_mask = self._create_color_mask(hsv, ColorRange.YELLOW_RANGES)
            
            # 检测白色均线
            white_mask = self._create_color_mask(hsv, ColorRange.WHITE_RANGES)
            
            # 分析均线趋势（通过检测线条的斜率）
            trend_analysis = self._analyze_line_trend(blue_mask)
            
            return {
                'trend': trend_analysis['trend'],
                'confidence': trend_analysis['confidence'],
                'blue_pixels': cv2.countNonZero(blue_mask),
                'yellow_pixels': cv2.countNonZero(yellow_mask),
                'white_pixels': cv2.countNonZero(white_mask),
                'slope': trend_analysis.get('slope', 0)
            }
            
        except Exception as e:
            self.logger.error(f"均线趋势检测失败: {e}")
            return {
                'trend': SignalType.UNKNOWN,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def get_comprehensive_signal(self, image: np.ndarray) -> Dict[str, Any]:
        """获取综合信号"""
        try:
            # 检测各项指标
            kline_result = self.detect_kline_signal(image)
            macd_result = self.detect_macd_signal(image)
            ma_result = self.detect_moving_average_trend(image)
            
            # 综合分析
            signals = []
            confidences = []
            
            # K线信号
            if kline_result['signal'] != SignalType.UNKNOWN:
                signals.append(kline_result['signal'])
                confidences.append(kline_result['confidence'])
            
            # MACD信号
            if macd_result['signal'] != SignalType.UNKNOWN:
                signals.append(macd_result['signal'])
                confidences.append(macd_result['confidence'])
            
            # 均线趋势
            if ma_result['trend'] != SignalType.UNKNOWN:
                signals.append(ma_result['trend'])
                confidences.append(ma_result['confidence'])
            
            # 计算综合信号
            if not signals:
                final_signal = SignalType.UNKNOWN
                final_confidence = 0.0
            else:
                # 统计信号
                bullish_count = signals.count(SignalType.BULLISH)
                bearish_count = signals.count(SignalType.BEARISH)
                
                if bullish_count > bearish_count:
                    final_signal = SignalType.BULLISH
                elif bearish_count > bullish_count:
                    final_signal = SignalType.BEARISH
                else:
                    final_signal = SignalType.NEUTRAL
                
                # 计算平均置信度
                final_confidence = sum(confidences) / len(confidences)
            
            return {
                'final_signal': final_signal,
                'final_confidence': final_confidence,
                'kline': kline_result,
                'macd': macd_result,
                'moving_average': ma_result,
                'signal_count': {
                    'bullish': signals.count(SignalType.BULLISH),
                    'bearish': signals.count(SignalType.BEARISH),
                    'neutral': signals.count(SignalType.NEUTRAL)
                }
            }
            
        except Exception as e:
            self.logger.error(f"综合信号分析失败: {e}")
            return {
                'final_signal': SignalType.UNKNOWN,
                'final_confidence': 0.0,
                'error': str(e)
            }
    
    def _get_detection_region(self, image: np.ndarray, region_name: str) -> np.ndarray:
        """获取检测区域"""
        if region_name not in self.detection_regions:
            return image
        
        region_config = self.detection_regions[region_name]
        height, width = image.shape[:2]
        
        x = int(width * region_config['x_ratio'])
        y = int(height * region_config['y_ratio'])
        w = int(width * region_config['width_ratio'])
        h = int(height * region_config['height_ratio'])
        
        return image[y:y+h, x:x+w]
    
    def _create_color_mask(self, hsv_image: np.ndarray, color_ranges: List[List]) -> np.ndarray:
        """创建颜色掩码"""
        mask = np.zeros(hsv_image.shape[:2], dtype=np.uint8)
        
        for color_range in color_ranges:
            lower = np.array(color_range[0])
            upper = np.array(color_range[1])
            range_mask = cv2.inRange(hsv_image, lower, upper)
            mask = cv2.bitwise_or(mask, range_mask)
        
        return mask
    
    def _analyze_line_trend(self, mask: np.ndarray) -> Dict[str, Any]:
        """分析线条趋势"""
        try:
            # 查找轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return {'trend': SignalType.NEUTRAL, 'confidence': 0.0, 'slope': 0}
            
            # 找到最长的轮廓（主要均线）
            main_contour = max(contours, key=cv2.contourArea)
            
            if len(main_contour) < 10:
                return {'trend': SignalType.NEUTRAL, 'confidence': 0.0, 'slope': 0}
            
            # 拟合直线
            [vx, vy, x, y] = cv2.fitLine(main_contour, cv2.DIST_L2, 0, 0.01, 0.01)
            
            # 计算斜率
            slope = vy / vx if vx != 0 else 0
            
            # 判断趋势
            if slope > 0.1:
                trend = SignalType.BULLISH
                confidence = min(abs(slope) * 2, 1.0)
            elif slope < -0.1:
                trend = SignalType.BEARISH
                confidence = min(abs(slope) * 2, 1.0)
            else:
                trend = SignalType.NEUTRAL
                confidence = 0.5
            
            return {
                'trend': trend,
                'confidence': confidence,
                'slope': float(slope)
            }
            
        except Exception as e:
            self.logger.error(f"线条趋势分析失败: {e}")
            return {'trend': SignalType.NEUTRAL, 'confidence': 0.0, 'slope': 0}

# 全局增强检测器实例
enhanced_detector = EnhancedDetector()
