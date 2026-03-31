#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的UI检测模块
多重验证机制提高识别稳定性
"""

import cv2
import numpy as np
import pyautogui
import time
import logging
from typing import Dict, List, Tuple, Optional
import win32gui
import win32ui
import win32con
from PIL import Image
import pytesseract

class EnhancedUIDetector:
    """增强的UI检测器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 模板库（存储按钮模板）
        self.button_templates = {}
        self.template_threshold = 0.8
        
        # OCR配置
        self.ocr_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,买卖确定取消'
        
        # 窗口信息缓存
        self.window_cache = {}
        self.cache_timeout = 30  # 缓存30秒
        
        self.logger.info("增强UI检测器初始化完成")
    
    def capture_window_direct(self, window_title: str) -> Optional[np.ndarray]:
        """直接捕获指定窗口内容（避免遮挡影响）"""
        try:
            # 查找窗口
            hwnd = win32gui.FindWindow(None, window_title)
            if not hwnd:
                self.logger.error(f"未找到窗口: {window_title}")
                return None
            
            # 获取窗口矩形
            left, top, right, bot = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bot - top
            
            # 创建设备上下文
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # 创建位图
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # 复制窗口内容
            result = saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
            
            if result:
                # 转换为numpy数组
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)
                im = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1)
                
                # 转换为OpenCV格式
                opencv_image = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
                
                # 清理资源
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwndDC)
                
                return opencv_image
            else:
                self.logger.error("窗口截图失败")
                return None
                
        except Exception as e:
            self.logger.error(f"直接窗口捕获失败: {e}")
            return None
    
    def multi_level_button_detection(self, image: np.ndarray, button_name: str, 
                                   target_text: str = None) -> Dict:
        """多层次按钮检测"""
        try:
            results = []
            
            # 方法1: 模板匹配
            if button_name in self.button_templates:
                template_result = self._template_matching(image, button_name)
                if template_result['confidence'] > 0.7:
                    results.append(('template', template_result))
            
            # 方法2: 颜色+形状检测
            color_result = self._color_shape_detection(image, button_name)
            if color_result['confidence'] > 0.6:
                results.append(('color', color_result))
            
            # 方法3: OCR文字识别
            if target_text:
                ocr_result = self._ocr_text_detection(image, target_text)
                if ocr_result['confidence'] > 0.5:
                    results.append(('ocr', ocr_result))
            
            # 方法4: 轮廓检测
            contour_result = self._contour_detection(image, button_name)
            if contour_result['confidence'] > 0.5:
                results.append(('contour', contour_result))
            
            # 综合评估结果
            if results:
                best_result = self._evaluate_detection_results(results)
                self.logger.info(f"按钮 {button_name} 检测成功: {best_result['method']}")
                return best_result
            else:
                return {'detected': False, 'confidence': 0.0}
                
        except Exception as e:
            self.logger.error(f"多层次按钮检测失败: {e}")
            return {'detected': False, 'confidence': 0.0}
    
    def _template_matching(self, image: np.ndarray, button_name: str) -> Dict:
        """模板匹配检测"""
        try:
            template = self.button_templates[button_name]
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > self.template_threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                return {
                    'detected': True,
                    'confidence': float(max_val),
                    'position': (center_x, center_y),
                    'method': 'template'
                }
            else:
                return {'detected': False, 'confidence': float(max_val)}
                
        except Exception as e:
            self.logger.error(f"模板匹配失败: {e}")
            return {'detected': False, 'confidence': 0.0}
    
    def _color_shape_detection(self, image: np.ndarray, button_name: str) -> Dict:
        """颜色+形状检测"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 根据按钮类型定义颜色范围
            color_ranges = {
                'buy_mode_button': [(np.array([0, 100, 100]), np.array([10, 255, 255]))],  # 红色
                'sell_mode_button': [(np.array([35, 100, 100]), np.array([85, 255, 255]))], # 绿色
                'confirm_button': [(np.array([100, 100, 100]), np.array([130, 255, 255]))] # 蓝色
            }
            
            if button_name not in color_ranges:
                return {'detected': False, 'confidence': 0.0}
            
            # 创建掩码
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in color_ranges[button_name]:
                mask += cv2.inRange(hsv, lower, upper)
            
            # 形态学处理
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # 查找轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # 选择最大轮廓
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                
                if area > 100:  # 最小面积阈值
                    # 计算中心点
                    M = cv2.moments(largest_contour)
                    if M["m00"] != 0:
                        center_x = int(M["m10"] / M["m00"])
                        center_y = int(M["m01"] / M["m00"])
                        
                        # 计算置信度（基于面积和形状）
                        rect_area = cv2.boundingRect(largest_contour)[2] * cv2.boundingRect(largest_contour)[3]
                        confidence = min(area / rect_area, 0.9)
                        
                        return {
                            'detected': True,
                            'confidence': confidence,
                            'position': (center_x, center_y),
                            'method': 'color_shape'
                        }
            
            return {'detected': False, 'confidence': 0.0}
            
        except Exception as e:
            self.logger.error(f"颜色形状检测失败: {e}")
            return {'detected': False, 'confidence': 0.0}
    
    def _ocr_text_detection(self, image: np.ndarray, target_text: str) -> Dict:
        """OCR文字检测"""
        try:
            # 预处理图像
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR识别
            data = pytesseract.image_to_data(binary, config=self.ocr_config, output_type=pytesseract.Output.DICT)
            
            # 查找目标文字
            for i, text in enumerate(data['text']):
                if target_text in text and int(data['conf'][i]) > 50:
                    x = data['left'][i] + data['width'][i] // 2
                    y = data['top'][i] + data['height'][i] // 2
                    confidence = int(data['conf'][i]) / 100.0
                    
                    return {
                        'detected': True,
                        'confidence': confidence,
                        'position': (x, y),
                        'method': 'ocr',
                        'text': text
                    }
            
            return {'detected': False, 'confidence': 0.0}
            
        except Exception as e:
            self.logger.error(f"OCR文字检测失败: {e}")
            return {'detected': False, 'confidence': 0.0}
    
    def _contour_detection(self, image: np.ndarray, button_name: str) -> Dict:
        """轮廓检测"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # 查找轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 按钮特征（矩形、适中大小）
            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < 5000:  # 按钮大小范围
                    # 检查是否接近矩形
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    
                    if len(approx) == 4:  # 四边形
                        # 计算中心点
                        M = cv2.moments(contour)
                        if M["m00"] != 0:
                            center_x = int(M["m10"] / M["m00"])
                            center_y = int(M["m01"] / M["m00"])
                            
                            # 计算矩形度
                            rect_area = cv2.boundingRect(contour)[2] * cv2.boundingRect(contour)[3]
                            rectangularity = area / rect_area
                            
                            if rectangularity > 0.7:
                                return {
                                    'detected': True,
                                    'confidence': rectangularity,
                                    'position': (center_x, center_y),
                                    'method': 'contour'
                                }
            
            return {'detected': False, 'confidence': 0.0}
            
        except Exception as e:
            self.logger.error(f"轮廓检测失败: {e}")
            return {'detected': False, 'confidence': 0.0}
    
    def _evaluate_detection_results(self, results: List[Tuple[str, Dict]]) -> Dict:
        """评估检测结果，选择最佳方法"""
        if not results:
            return {'detected': False, 'confidence': 0.0}
        
        # 按置信度排序
        results.sort(key=lambda x: x[1]['confidence'], reverse=True)
        
        # 如果最高置信度足够高，直接返回
        best_method, best_result = results[0]
        if best_result['confidence'] > 0.8:
            best_result['method'] = best_method
            return best_result
        
        # 多方法一致性检查
        if len(results) >= 2:
            pos1 = results[0][1].get('position', (0, 0))
            pos2 = results[1][1].get('position', (0, 0))
            
            # 计算位置差异
            distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
            
            if distance < 20:  # 位置相近，增加置信度
                best_result['confidence'] = min(best_result['confidence'] * 1.2, 0.95)
                best_result['method'] = f"{best_method}_verified"
        
        best_result['method'] = best_method
        return best_result
    
    def save_button_template(self, button_name: str, image: np.ndarray, 
                            position: Tuple[int, int], size: Tuple[int, int] = (50, 30)):
        """保存按钮模板"""
        try:
            x, y = position
            w, h = size
            
            # 提取按钮区域
            template = image[y-h//2:y+h//2, x-w//2:x+w//2]
            
            if template.size > 0:
                self.button_templates[button_name] = template
                
                # 保存到文件
                cv2.imwrite(f"templates/{button_name}.png", template)
                self.logger.info(f"按钮模板已保存: {button_name}")
            
        except Exception as e:
            self.logger.error(f"保存按钮模板失败: {e}")

if __name__ == "__main__":
    # 测试代码
    detector = EnhancedUIDetector()
    
    # 捕获窗口
    image = detector.capture_window_direct("景陶易购")
    
    if image is not None:
        # 测试按钮检测
        result = detector.multi_level_button_detection(image, "buy_mode_button", "买")
        print(f"检测结果: {result}")