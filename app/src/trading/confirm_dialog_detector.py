#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
确认对话框检测器
专门用于检测和处理交易确认对话框，支持智能等待和多种检测方法
"""

import cv2
import numpy as np
import time
import logging
import pyautogui
from typing import Dict, Tuple, Optional, List

class ConfirmDialogDetector:
    """确认对话框检测器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 确认按钮的可能文本
        self.confirm_texts = ['确定', '确认', '提交', '订立', 'OK', 'Confirm']
        
        # 对话框检测的颜色范围（通常是灰色或白色背景）
        self.dialog_color_ranges = [
            # 灰色对话框
            {'lower': np.array([0, 0, 180]), 'upper': np.array([180, 30, 255])},
            # 白色对话框
            {'lower': np.array([0, 0, 240]), 'upper': np.array([180, 15, 255])},
        ]
        
        # 按钮颜色范围（通常是蓝色或绿色）
        self.button_color_ranges = [
            # 蓝色按钮
            {'lower': np.array([100, 50, 50]), 'upper': np.array([130, 255, 255])},
            # 绿色按钮
            {'lower': np.array([40, 50, 50]), 'upper': np.array([80, 255, 255])},
        ]
        
    def detect_confirm_dialog(self, screenshot: np.ndarray = None) -> Dict:
        """检测确认对话框"""
        try:
            if screenshot is None:
                screenshot = self._capture_screen()
                
            if screenshot is None:
                return {'detected': False, 'reason': 'screenshot_failed'}
            
            # 方法1：检测对话框区域
            dialog_result = self._detect_dialog_area(screenshot)
            if dialog_result['detected']:
                return dialog_result
                
            # 方法2：检测确认按钮
            button_result = self._detect_confirm_button(screenshot)
            if button_result['detected']:
                return button_result
                
            # 方法3：检测文本特征
            text_result = self._detect_confirm_text(screenshot)
            if text_result['detected']:
                return text_result
                
            return {'detected': False, 'reason': 'no_dialog_found'}
            
        except Exception as e:
            self.logger.error(f"检测确认对话框失败: {e}")
            return {'detected': False, 'reason': f'error: {e}'}
    
    def _capture_screen(self) -> Optional[np.ndarray]:
        """捕获屏幕截图"""
        try:
            screenshot = pyautogui.screenshot()
            return np.array(screenshot)
        except Exception as e:
            self.logger.error(f"屏幕截图失败: {e}")
            return None
    
    def _detect_dialog_area(self, screenshot: np.ndarray) -> Dict:
        """检测对话框区域"""
        try:
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_RGB2HSV)
            
            for color_range in self.dialog_color_ranges:
                mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
                
                # 形态学操作
                kernel = np.ones((5, 5), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                
                # 查找轮廓
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    
                    # 对话框通常有一定的面积
                    if 5000 < area < 100000:
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # 对话框通常是矩形且宽高比合理
                        aspect_ratio = w / h
                        if 0.5 < aspect_ratio < 3.0:
                            center_x = x + w // 2
                            center_y = y + h // 2
                            
                            self.logger.info(f"检测到对话框区域: ({x}, {y}, {w}, {h})")
                            return {
                                'detected': True,
                                'method': 'dialog_area',
                                'position': (center_x, center_y),
                                'bbox': (x, y, w, h),
                                'area': area
                            }
            
            return {'detected': False, 'reason': 'no_dialog_area'}
            
        except Exception as e:
            self.logger.error(f"检测对话框区域失败: {e}")
            return {'detected': False, 'reason': f'dialog_area_error: {e}'}
    
    def _detect_confirm_button(self, screenshot: np.ndarray) -> Dict:
        """检测确认按钮"""
        try:
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_RGB2HSV)
            
            for color_range in self.button_color_ranges:
                mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
                
                # 形态学操作
                kernel = np.ones((3, 3), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                
                # 查找轮廓
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    
                    # 按钮通常有适中的面积
                    if 500 < area < 5000:
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # 按钮通常是矩形
                        aspect_ratio = w / h
                        if 1.0 < aspect_ratio < 4.0:
                            center_x = x + w // 2
                            center_y = y + h // 2
                            
                            self.logger.info(f"检测到确认按钮: ({x}, {y}, {w}, {h})")
                            return {
                                'detected': True,
                                'method': 'confirm_button',
                                'position': (center_x, center_y),
                                'bbox': (x, y, w, h),
                                'area': area
                            }
            
            return {'detected': False, 'reason': 'no_confirm_button'}
            
        except Exception as e:
            self.logger.error(f"检测确认按钮失败: {e}")
            return {'detected': False, 'reason': f'button_error: {e}'}
    
    def _detect_confirm_text(self, screenshot: np.ndarray) -> Dict:
        """检测确认文本（简化版本，基于颜色和形状）"""
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
            
            # 二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 查找轮廓
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 寻找可能的文本区域
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # 文本区域通常有适中的面积
                if 100 < area < 2000:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 文本区域通常是矩形
                    aspect_ratio = w / h
                    if 1.0 < aspect_ratio < 6.0:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        # 简单的位置判断（确认按钮通常在对话框下方中央）
                        screen_height, screen_width = screenshot.shape[:2]
                        if (screen_width * 0.3 < center_x < screen_width * 0.7 and
                            screen_height * 0.4 < center_y < screen_height * 0.8):
                            
                            self.logger.info(f"检测到可能的确认文本: ({x}, {y}, {w}, {h})")
                            return {
                                'detected': True,
                                'method': 'confirm_text',
                                'position': (center_x, center_y),
                                'bbox': (x, y, w, h),
                                'area': area
                            }
            
            return {'detected': False, 'reason': 'no_confirm_text'}
            
        except Exception as e:
            self.logger.error(f"检测确认文本失败: {e}")
            return {'detected': False, 'reason': f'text_error: {e}'}
    
    def wait_for_dialog(self, max_wait_time: float = 3.0, check_interval: float = 0.2) -> Dict:
        """等待确认对话框出现"""
        try:
            self.logger.info(f"开始等待确认对话框 (最大等待: {max_wait_time}秒)")
            
            start_time = time.time()
            check_count = 0
            
            while time.time() - start_time < max_wait_time:
                check_count += 1
                
                # 检测对话框
                result = self.detect_confirm_dialog()
                
                if result['detected']:
                    elapsed_time = time.time() - start_time
                    self.logger.info(f"✅ 检测到确认对话框 (等待时间: {elapsed_time:.1f}秒, 检查次数: {check_count})")
                    result['wait_time'] = elapsed_time
                    result['check_count'] = check_count
                    return result
                
                # 等待下次检查
                time.sleep(check_interval)
            
            elapsed_time = time.time() - start_time
            self.logger.warning(f"⏰ 等待超时，未检测到确认对话框 (等待时间: {elapsed_time:.1f}秒, 检查次数: {check_count})")
            
            return {
                'detected': False,
                'reason': 'timeout',
                'wait_time': elapsed_time,
                'check_count': check_count
            }
            
        except Exception as e:
            self.logger.error(f"等待确认对话框失败: {e}")
            return {'detected': False, 'reason': f'wait_error: {e}'}
    
    def click_confirm_button(self, detection_result: Dict) -> bool:
        """点击确认按钮"""
        try:
            if not detection_result.get('detected', False):
                self.logger.warning("未检测到确认对话框，无法点击")
                return False
            
            position = detection_result.get('position')
            if not position:
                self.logger.warning("确认对话框位置信息缺失")
                return False
            
            x, y = position
            self.logger.info(f"点击确认按钮位置: ({x}, {y})")
            
            # 点击确认按钮
            pyautogui.click(x, y)
            time.sleep(0.5)  # 等待点击生效
            
            self.logger.info("✅ 确认按钮点击完成")
            return True
            
        except Exception as e:
            self.logger.error(f"点击确认按钮失败: {e}")
            return False
    
    def wait_and_confirm(self, max_wait_time: float = 3.0) -> bool:
        """等待并确认对话框"""
        try:
            # 等待对话框出现
            result = self.wait_for_dialog(max_wait_time)
            
            if result['detected']:
                # 点击确认按钮
                return self.click_confirm_button(result)
            else:
                self.logger.warning("未检测到确认对话框，无法确认")
                return False
                
        except Exception as e:
            self.logger.error(f"等待并确认失败: {e}")
            return False

if __name__ == "__main__":
    # 测试确认对话框检测器
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    detector = ConfirmDialogDetector()
    
    print("🔍 确认对话框检测器测试")
    print("请在5秒内打开一个确认对话框...")
    
    time.sleep(2)
    
    # 测试检测功能
    result = detector.detect_confirm_dialog()
    print(f"检测结果: {result}")
    
    # 测试等待功能
    print("\n等待确认对话框出现...")
    wait_result = detector.wait_and_confirm(max_wait_time=5.0)
    print(f"等待并确认结果: {wait_result}")
