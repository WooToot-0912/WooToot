#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
景陶易购客户端颜色检测修复
专门针对您的客户端界面调整颜色检测范围
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple

class JingTaoColorDetector:
    """景陶易购专用颜色检测器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 根据您的截图调整颜色范围
        # 蓝绿色/青色 K线 (您截图中的涨势K线)
        self.cyan_ranges = [
            ([80, 50, 50], [100, 255, 255]),   # 青色范围1
            ([85, 30, 100], [95, 255, 255]),   # 青色范围2
        ]
        
        # 黄色 K线 (您截图中的跌势K线)
        self.yellow_ranges = [
            ([15, 100, 100], [35, 255, 255]),  # 黄色范围1
            ([20, 50, 150], [30, 255, 255]),   # 黄色范围2
        ]
        
        # 白色 (您截图中的均线)
        self.white_ranges = [
            ([0, 0, 200], [180, 30, 255]),     # 白色范围
        ]
        
        # MACD 柱状图颜色 (根据您的界面调整)
        self.macd_positive_ranges = [
            ([80, 50, 50], [100, 255, 255]),   # 正值 (青色)
        ]
        
        self.macd_negative_ranges = [
            ([15, 100, 100], [35, 255, 255]),  # 负值 (黄色)
        ]
        
        self.logger.info("景陶易购专用颜色检测器初始化完成")
    
    def detect_kline_trend(self, image: np.ndarray) -> Dict:
        """检测K线趋势 - 针对景陶易购界面优化"""
        try:
            if image is None:
                return {'signal': 'none', 'confidence': 0.0, 'details': '图像为空'}
            
            # 转换为HSV色彩空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 检测蓝绿色(涨势)K线
            cyan_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in self.cyan_ranges:
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                cyan_mask = cv2.bitwise_or(cyan_mask, mask)
            
            # 检测黄色(跌势)K线  
            yellow_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in self.yellow_ranges:
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                yellow_mask = cv2.bitwise_or(yellow_mask, mask)
            
            # 计算像素数量
            cyan_pixels = cv2.countNonZero(cyan_mask)
            yellow_pixels = cv2.countNonZero(yellow_mask)
            total_pixels = image.shape[0] * image.shape[1]
            
            # 计算比例
            cyan_ratio = cyan_pixels / total_pixels
            yellow_ratio = yellow_pixels / total_pixels
            
            self.logger.info(f"K线检测 - 青色比例: {cyan_ratio:.4f}, 黄色比例: {yellow_ratio:.4f}")
            
            # 保存调试掩码
            import time
            debug_mask = cv2.bitwise_or(cyan_mask, yellow_mask)
            cv2.imwrite(f"debug_kline_mask_{int(time.time())}.png", debug_mask)
            
            # 判断趋势 (降低阈值，提高灵敏度)
            min_ratio = 0.005  # 降低最小比例要求
            
            if cyan_ratio > min_ratio and cyan_ratio > yellow_ratio * 1.2:
                confidence = min(cyan_ratio * 50, 0.9)  # 提高置信度计算
                return {
                    'signal': 'buy',
                    'confidence': confidence,
                    'cyan_ratio': cyan_ratio,
                    'yellow_ratio': yellow_ratio,
                    'details': f'检测到青色K线主导: {cyan_ratio:.4f}'
                }
            elif yellow_ratio > min_ratio and yellow_ratio > cyan_ratio * 1.2:
                confidence = min(yellow_ratio * 50, 0.9)
                return {
                    'signal': 'sell', 
                    'confidence': confidence,
                    'cyan_ratio': cyan_ratio,
                    'yellow_ratio': yellow_ratio,
                    'details': f'检测到黄色K线主导: {yellow_ratio:.4f}'
                }
            else:
                return {
                    'signal': 'none',
                    'confidence': 0.0,
                    'cyan_ratio': cyan_ratio,
                    'yellow_ratio': yellow_ratio,
                    'details': f'颜色比例不足或相近'
                }
                
        except Exception as e:
            self.logger.error(f"K线趋势检测失败: {e}")
            return {'signal': 'none', 'confidence': 0.0, 'details': f'检测异常: {e}'}
    
    def detect_macd_signal(self, image: np.ndarray) -> Dict:
        """检测MACD信号 - 针对景陶易购界面优化"""
        try:
            if image is None:
                return {'signal': 'none', 'confidence': 0.0, 'details': '图像为空'}
            
            # 转换为HSV色彩空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 检测MACD正值(青色)
            positive_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in self.macd_positive_ranges:
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                positive_mask = cv2.bitwise_or(positive_mask, mask)
            
            # 检测MACD负值(黄色)
            negative_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in self.macd_negative_ranges:
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                negative_mask = cv2.bitwise_or(negative_mask, mask)
            
            # 计算像素数量
            positive_pixels = cv2.countNonZero(positive_mask)
            negative_pixels = cv2.countNonZero(negative_mask)
            total_pixels = image.shape[0] * image.shape[1]
            
            # 计算比例
            positive_ratio = positive_pixels / total_pixels
            negative_ratio = negative_pixels / total_pixels
            
            self.logger.info(f"MACD检测 - 正值比例: {positive_ratio:.4f}, 负值比例: {negative_ratio:.4f}")
            
            # 保存调试掩码
            import time
            debug_mask = cv2.bitwise_or(positive_mask, negative_mask)
            cv2.imwrite(f"debug_macd_mask_{int(time.time())}.png", debug_mask)
            
            # 判断MACD信号 (降低阈值)
            min_ratio = 0.003  # 进一步降低最小比例要求
            
            if positive_ratio > min_ratio and positive_ratio > negative_ratio * 1.1:
                confidence = min(positive_ratio * 80, 0.8)
                return {
                    'signal': 'buy',
                    'confidence': confidence,
                    'positive_ratio': positive_ratio,
                    'negative_ratio': negative_ratio,
                    'details': f'MACD正值主导: {positive_ratio:.4f}'
                }
            elif negative_ratio > min_ratio and negative_ratio > positive_ratio * 1.1:
                confidence = min(negative_ratio * 80, 0.8)
                return {
                    'signal': 'sell',
                    'confidence': confidence,
                    'positive_ratio': positive_ratio,
                    'negative_ratio': negative_ratio,
                    'details': f'MACD负值主导: {negative_ratio:.4f}'
                }
            else:
                return {
                    'signal': 'none',
                    'confidence': 0.0,
                    'positive_ratio': positive_ratio,
                    'negative_ratio': negative_ratio,
                    'details': f'MACD信号不明确'
                }
                
        except Exception as e:
            self.logger.error(f"MACD信号检测失败: {e}")
            return {'signal': 'none', 'confidence': 0.0, 'details': f'检测异常: {e}'}
    
    def analyze_color_distribution(self, image: np.ndarray) -> Dict:
        """分析图像颜色分布 - 用于调试"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 获取颜色直方图
            h_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
            s_hist = cv2.calcHist([hsv], [1], None, [256], [0, 256])
            v_hist = cv2.calcHist([hsv], [2], None, [256], [0, 256])
            
            # 找到主要颜色
            h_peak = np.argmax(h_hist)
            s_peak = np.argmax(s_hist)
            v_peak = np.argmax(v_hist)
            
            return {
                'dominant_hue': int(h_peak),
                'dominant_saturation': int(s_peak),
                'dominant_value': int(v_peak),
                'hsv_ranges_detected': {
                    'hue_range': [max(0, h_peak-10), min(179, h_peak+10)],
                    'sat_range': [max(0, s_peak-50), min(255, s_peak+50)],
                    'val_range': [max(0, v_peak-50), min(255, v_peak+50)]
                }
            }
        except Exception as e:
            self.logger.error(f"颜色分布分析失败: {e}")
            return {}

if __name__ == "__main__":
    import time
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    print("景陶易购颜色检测修复模块已创建")
    
    # 简单测试
    detector = JingTaoColorDetector()
    print("✅ 颜色检测器初始化成功")