#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级黄线检测器
提供多种先进的线条检测方案
"""

import cv2
import numpy as np
import time
import logging
import os
import json
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

try:
    from skimage import feature, filters, morphology, measure
    from scipy import ndimage, signal
    ADVANCED_LIBS_AVAILABLE = True
except ImportError:
    ADVANCED_LIBS_AVAILABLE = False
    print("⚠️ 高级库未安装，将使用基础检测方法")

@dataclass
class LineSegment:
    """线段数据结构"""
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]
    angle: float
    length: float
    confidence: float

class AdvancedLineDetector:
    """高级线条检测器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.history_data = []
        self.roi_region = None  # 用户手动选择的感兴趣区域
        self.angle_threshold = 5  # 默认角度阈值
        self._load_roi_from_config()
        
    def set_roi_region(self, x: int, y: int, w: int, h: int):
        """设置感兴趣区域"""
        self.roi_region = (x, y, w, h)
        self.logger.info(f"✅ 设置ROI区域: ({x}, {y}, {w}, {h})")
        
    def set_angle_threshold(self, threshold: float):
        """设置角度阈值"""
        if 1 <= threshold <= 45:
            self.angle_threshold = threshold
            self.logger.info(f"🎯 高级检测器角度阈值已设置为: {threshold}°")
        else:
            self.logger.warning(f"角度阈值必须在1-45度之间，当前值: {threshold}")
        
    def detect_lines_hough_transform(self, image: np.ndarray) -> List[LineSegment]:
        """方案1: 使用霍夫变换检测直线"""
        try:
            if self.roi_region:
                x, y, w, h = self.roi_region
                roi = image[y:y+h, x:x+w]
            else:
                roi = image
                
            # 转换为灰度图
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # 边缘检测 - 降低阈值以提高敏感度
            edges = cv2.Canny(gray, 30, 100, apertureSize=3)
            
            # 霍夫直线变换 - 降低阈值以提高检测敏感度
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=20, 
                                   minLineLength=15, maxLineGap=8)
            
            line_segments = []
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    
                    # 计算角度
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    
                    # 计算长度
                    length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    
                    # 基于长度和位置计算置信度
                    confidence = min(1.0, length / 100.0)
                    
                    line_segments.append(LineSegment(
                        start_point=(x1, y1),
                        end_point=(x2, y2),
                        angle=angle,
                        length=length,
                        confidence=confidence
                    ))
                    
            return line_segments
            
        except Exception as e:
            self.logger.error(f"霍夫变换检测失败: {e}")
            return []
    
    def detect_lines_contour_analysis(self, image: np.ndarray) -> List[LineSegment]:
        """方案2: 基于轮廓分析的线条检测"""
        try:
            if self.roi_region:
                x, y, w, h = self.roi_region
                roi = image[y:y+h, x:x+w]
            else:
                roi = image
                
            # 转换到HSV颜色空间
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # 多种颜色范围检测
            color_ranges = [
                # 黄色系列
                (np.array([20, 100, 100]), np.array([30, 255, 255])),
                # 橙色系列
                (np.array([10, 100, 100]), np.array([25, 255, 255])),
                # 绿色系列
                (np.array([40, 100, 100]), np.array([80, 255, 255])),
                # 青色系列
                (np.array([80, 100, 100]), np.array([100, 255, 255])),
                # 紫色系列
                (np.array([140, 100, 100]), np.array([160, 255, 255])),
            ]
            
            line_segments = []
            
            for lower, upper in color_ranges:
                # 创建颜色掩码
                mask = cv2.inRange(hsv, lower, upper)
                
                # 形态学操作清理噪声
                kernel = np.ones((3,3), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                
                # 查找轮廓
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    # 过滤小轮廓
                    if cv2.contourArea(contour) < 20:
                        continue
                        
                    # 使用最小外接矩形拟合线条
                    rect = cv2.minAreaRect(contour)
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    
                    # 计算线条的两个端点
                    center = rect[0]
                    angle = rect[2]
                    width, height = rect[1]
                    
                    # 选择较长的边作为主要方向
                    if width > height:
                        length = width
                        rad_angle = np.radians(angle)
                    else:
                        length = height
                        rad_angle = np.radians(angle + 90)
                    
                    # 计算端点
                    half_length = length / 2
                    x1 = int(center[0] - half_length * np.cos(rad_angle))
                    y1 = int(center[1] - half_length * np.sin(rad_angle))
                    x2 = int(center[0] + half_length * np.cos(rad_angle))
                    y2 = int(center[1] + half_length * np.sin(rad_angle))
                    
                    confidence = min(1.0, cv2.contourArea(contour) / 500.0)
                    
                    line_segments.append(LineSegment(
                        start_point=(x1, y1),
                        end_point=(x2, y2),
                        angle=np.degrees(rad_angle),
                        length=length,
                        confidence=confidence
                    ))
            
            return line_segments
            
        except Exception as e:
            self.logger.error(f"轮廓分析检测失败: {e}")
            return []
    
    def detect_lines_template_matching(self, image: np.ndarray, template_paths: List[str] = None) -> List[LineSegment]:
        """方案3: 模板匹配检测"""
        try:
            if not template_paths:
                # 创建基本的线条模板
                templates = self._create_line_templates()
            else:
                templates = [cv2.imread(path, cv2.IMREAD_GRAYSCALE) for path in template_paths]
                templates = [t for t in templates if t is not None]
            
            if self.roi_region:
                x, y, w, h = self.roi_region
                roi = image[y:y+h, x:x+w]
            else:
                roi = image
                
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            line_segments = []
            
            for i, template in enumerate(templates):
                # 多尺度模板匹配
                for scale in [0.5, 0.8, 1.0, 1.2, 1.5]:
                    scaled_template = cv2.resize(template, None, fx=scale, fy=scale)
                    
                    if scaled_template.shape[0] > gray.shape[0] or scaled_template.shape[1] > gray.shape[1]:
                        continue
                    
                    # 模板匹配
                    result = cv2.matchTemplate(gray, scaled_template, cv2.TM_CCOEFF_NORMED)
                    locations = np.where(result >= 0.6)  # 阈值可调
                    
                    for pt in zip(*locations[::-1]):
                        h_t, w_t = scaled_template.shape
                        
                        # 计算线条的角度（基于模板索引）
                        angle = i * 30 - 90  # 假设模板按角度排列
                        
                        # 计算线条端点
                        center_x = pt[0] + w_t // 2
                        center_y = pt[1] + h_t // 2
                        length = max(w_t, h_t)
                        
                        rad_angle = np.radians(angle)
                        half_length = length / 2
                        x1 = int(center_x - half_length * np.cos(rad_angle))
                        y1 = int(center_y - half_length * np.sin(rad_angle))
                        x2 = int(center_x + half_length * np.cos(rad_angle))
                        y2 = int(center_y + half_length * np.sin(rad_angle))
                        
                        confidence = result[pt[1], pt[0]]
                        
                        line_segments.append(LineSegment(
                            start_point=(x1, y1),
                            end_point=(x2, y2),
                            angle=angle,
                            length=length,
                            confidence=confidence
                        ))
            
            return line_segments
            
        except Exception as e:
            self.logger.error(f"模板匹配检测失败: {e}")
            return []
    
    def _create_line_templates(self) -> List[np.ndarray]:
        """创建基本线条模板"""
        templates = []
        
        # 创建不同角度的线条模板
        for angle in range(-90, 91, 15):  # -90到90度，每15度一个模板
            template = np.zeros((40, 40), dtype=np.uint8)
            
            # 在模板中心绘制线条
            center = (20, 20)
            length = 30
            rad_angle = np.radians(angle)
            
            x1 = int(center[0] - length/2 * np.cos(rad_angle))
            y1 = int(center[1] - length/2 * np.sin(rad_angle))
            x2 = int(center[0] + length/2 * np.cos(rad_angle))
            y2 = int(center[1] + length/2 * np.sin(rad_angle))
            
            cv2.line(template, (x1, y1), (x2, y2), 255, 2)
            templates.append(template)
        
        return templates
    
    def detect_lines_advanced(self, image: np.ndarray) -> Dict:
        """方案4: 高级算法综合检测"""
        if not ADVANCED_LIBS_AVAILABLE:
            print("⚠️ 高级库不可用，使用备用检测")
            return self._fallback_detection(image)
            
        try:
            # 添加调试信息
            print(f"🔍 高级检测开始，图像形状: {image.shape}")
            
            if self.roi_region:
                x, y, w, h = self.roi_region
                roi = image[y:y+h, x:x+w]
                print(f"📍 使用ROI区域: ({x}, {y}, {w}, {h})")
            else:
                roi = image
                print("📍 使用全屏检测")
                
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            print(f"🔍 灰度图形状: {gray.shape}")
            
            # 使用多种方法进行线条检测
            # 1. 先尝试基于颜色的检测 (主要方法)
            print("🎨 开始颜色检测...")
            color_lines = self._detect_colored_lines(roi)
            if color_lines:
                print(f"✅ 颜色检测找到 {len(color_lines)} 条线")
                return self._analyze_line_trend(color_lines)
            else:
                print("⚠️ 颜色检测未找到线条，尝试边缘检测...")
            
            # 2. 边缘检测方法
            edges = cv2.Canny(gray, 30, 100, apertureSize=3)  # 降低阈值
            print(f"🔍 边缘检测完成，边缘点数: {np.sum(edges > 0)}")
            
            # 3. 概率霍夫变换 - 降低阈值
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 
                                   threshold=15, minLineLength=10, maxLineGap=8)  # 降低阈值
            
            print(f"🔍 霍夫变换结果: {lines.shape if lines is not None else 'None'}")
            
            if lines is None:
                print("⚠️ 未检测到任何线条")
                return {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'confidence': 0.0}
            
            # 3. 分析线条趋势
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                # 只考虑足够长的线条
                if length > 15:
                    angles.append(angle)
            
            if not angles:
                return {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'confidence': 0.0}
            
            # 计算主要角度
            mean_angle = np.mean(angles)
            angle_std = np.std(angles)
            
            # 存储历史数据
            self.history_data.append({
                'timestamp': time.time(),
                'angle': mean_angle,
                'std': angle_std,
                'line_count': len(angles)
            })
            
            # 只保留最近10个数据点
            if len(self.history_data) > 10:
                self.history_data.pop(0)
            
            # 计算趋势
            if len(self.history_data) >= 2:
                current = self.history_data[-1]
                previous = self.history_data[-2]
                angle_change = current['angle'] - previous['angle']
                
                # 判断信号
                if abs(angle_change) > 5.0:  # 5度阈值
                    signal = 'up' if angle_change > 0 else 'down'
                    direction = 'rising' if angle_change > 0 else 'falling'
                    confidence = min(1.0, abs(angle_change) / 45.0)
                else:
                    signal = 'none'
                    direction = 'stable'
                    confidence = 0.0
                
                return {
                    'signal': signal,
                    'direction': direction,
                    'angle': mean_angle,
                    'angle_change': angle_change,
                    'confidence': confidence,
                    'line_count': len(angles),
                    'angle_std': angle_std
                }
            
            return {'signal': 'none', 'direction': 'stable', 'angle': mean_angle, 'confidence': 0.0}
            
        except Exception as e:
            self.logger.error(f"高级检测失败: {e}")
            return {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'confidence': 0.0}
    
    def _fallback_detection(self, image: np.ndarray) -> Dict:
        """备用检测方法"""
        try:
            # 使用基础OpenCV方法
            line_segments = self.detect_lines_hough_transform(image)
            
            if not line_segments:
                return {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'confidence': 0.0}
            
            # 计算平均角度
            angles = [seg.angle for seg in line_segments if seg.confidence > 0.3]
            
            if not angles:
                return {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'confidence': 0.0}
            
            mean_angle = np.mean(angles)
            
            # 简单的趋势判断
            self.history_data.append({'angle': mean_angle, 'timestamp': time.time()})
            
            if len(self.history_data) > 10:
                self.history_data.pop(0)
            
            if len(self.history_data) >= 2:
                angle_change = self.history_data[-1]['angle'] - self.history_data[-2]['angle']
                
                if abs(angle_change) > 5.0:
                    signal = 'up' if angle_change > 0 else 'down'
                    direction = 'rising' if angle_change > 0 else 'falling'
                    confidence = min(1.0, abs(angle_change) / 45.0)
                else:
                    signal = 'none'
                    direction = 'stable'
                    confidence = 0.0
                
                return {
                    'signal': signal,
                    'direction': direction,
                    'angle': mean_angle,
                    'angle_change': angle_change,
                    'confidence': confidence
                }
            
            return {'signal': 'none', 'direction': 'stable', 'angle': mean_angle, 'confidence': 0.0}
            
        except Exception as e:
            self.logger.error(f"备用检测失败: {e}")
            return {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'confidence': 0.0}

    def create_roi_selector_gui(self):
        """创建ROI选择GUI"""
        import tkinter as tk
        from tkinter import messagebox
        import pyautogui
        
        def select_roi():
            try:
                # 截取屏幕
                screenshot = pyautogui.screenshot()
                screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # 使用OpenCV的selectROI功能
                cv2.namedWindow('选择黄线检测区域', cv2.WINDOW_NORMAL)
                roi = cv2.selectROI('选择黄线检测区域', screenshot_np, False, False)
                cv2.destroyAllWindows()
                
                if roi[2] > 0 and roi[3] > 0:  # 确保选择了有效区域
                    self.set_roi_region(roi[0], roi[1], roi[2], roi[3])
                    messagebox.showinfo("成功", f"ROI区域已设置: {roi}")
                    return True
                else:
                    messagebox.showwarning("取消", "未选择有效区域")
                    return False
                    
            except Exception as e:
                messagebox.showerror("错误", f"ROI选择失败: {e}")
                return False
        
        root = tk.Tk()
        root.title("黄线检测ROI选择器")
        root.geometry("300x150")
        
        tk.Label(root, text="请点击按钮选择黄线检测区域", font=("Arial", 12)).pack(pady=20)
        
        tk.Button(root, text="选择ROI区域", command=select_roi, 
                 bg="lightblue", font=("Arial", 11)).pack(pady=10)
        
        tk.Button(root, text="关闭", command=root.destroy, 
                 bg="lightcoral", font=("Arial", 11)).pack(pady=5)
        
        root.mainloop()
    
    def _load_roi_from_config(self):
        """从配置文件加载ROI区域"""
        try:
            config_paths = [
                "config/smart_coordinates_config.json",
                "../config/smart_coordinates_config.json", 
                "../../config/smart_coordinates_config.json",
                "smart_coordinates_config.json"
            ]
            
            for config_path in config_paths:
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    roi_config = config.get('detection_regions', {}).get('yellow_line_roi')
                    if roi_config:
                        x = roi_config.get('x', 0)
                        y = roi_config.get('y', 0)
                        w = roi_config.get('width', 0)
                        h = roi_config.get('height', 0)
                        
                        if w > 0 and h > 0:
                            self.roi_region = (x, y, w, h)
                            print(f"✅ 从配置文件加载ROI区域: ({x}, {y}, {w}, {h})")
                            self.logger.info(f"✅ 从配置文件加载ROI区域: ({x}, {y}, {w}, {h})")
                            return
                    break
            
            print("⚠️ 未找到ROI配置，将使用全屏检测")
            self.logger.warning("⚠️ 未找到ROI配置，将使用全屏检测")
            
        except Exception as e:
            print(f"⚠️ 加载ROI配置失败: {e}")
            self.logger.warning(f"⚠️ 加载ROI配置失败: {e}")
    
    def _detect_colored_lines(self, image: np.ndarray) -> List[LineSegment]:
        """基于颜色检测线条"""
        try:
            # 转换到HSV颜色空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 基于用户精确提取的RGB(255,184,0) -> HSV(22,255,255)的黄线颜色范围
            yellow_ranges = [
                # 🎯 用户精确黄线颜色 (HSV: 22, 255, 255) - 最优先检测
                (np.array([17, 225, 225]), np.array([27, 255, 255])),   # 精确范围1 (±5度)
                (np.array([12, 205, 205]), np.array([32, 255, 255])),   # 精确范围2 (±10度)
                (np.array([7, 185, 185]), np.array([37, 255, 255])),    # 精确范围3 (±15度)
                
                # 🟡 基于HSV=22的扩展黄色范围
                (np.array([20, 200, 200]), np.array([25, 255, 255])),   # 超精确黄色
                (np.array([18, 180, 180]), np.array([28, 255, 255])),   # 严格黄色
                (np.array([15, 150, 150]), np.array([30, 255, 255])),   # 标准黄色
                
                # 🟠 橙黄色和金色扩展
                (np.array([10, 200, 200]), np.array([25, 255, 255])),   # 橙黄色
                (np.array([20, 180, 180]), np.array([30, 255, 255])),   # 金色
                
                # 🟡 备用宽松范围
                (np.array([2, 155, 155]), np.array([42, 255, 255])),    # 用户提供的超宽范围
                (np.array([5, 100, 100]), np.array([40, 255, 255])),    # 宽松黄色
            ]
            
            line_segments = []
            
            for i, (lower, upper) in enumerate(yellow_ranges):
                # 创建颜色掩码
                mask = cv2.inRange(hsv, lower, upper)
                
                # 形态学操作
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                
                # 查找轮廓
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area < 10:  # 降低面积阈值
                        continue
                    
                    # 拟合直线
                    if len(contour) >= 5:
                        [vx, vy, x, y] = cv2.fitLine(contour, cv2.DIST_L2, 0, 0.01, 0.01)
                        
                        # 计算线条端点
                        lefty = int((-x[0]*vy[0]/vx[0]) + y[0])
                        righty = int(((image.shape[1]-x[0])*vy[0]/vx[0])+y[0])
                        
                        # 计算角度和长度
                        angle = np.arctan2(vy[0], vx[0]) * 180 / np.pi  # vx, vy是数组，取第一个元素
                        length = np.sqrt((image.shape[1])**2 + (righty - lefty)**2)
                        
                        confidence = min(1.0, area / 100.0)
                        
                        line_segments.append(LineSegment(
                            start_point=(0, lefty),
                            end_point=(image.shape[1]-1, righty),
                            angle=angle,
                            length=length,
                            confidence=confidence
                        ))
                        
                        print(f"🟡 发现颜色线条 #{i}: 角度={angle:.1f}°, 长度={length:.1f}, 置信度={confidence:.2f}")
            
            return line_segments
            
        except Exception as e:
            print(f"❌ 颜色线条检测失败: {e}")
            return []
    
    def _analyze_line_trend(self, line_segments: List[LineSegment]) -> Dict:
        """分析线条趋势"""
        try:
            if not line_segments:
                return {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'confidence': 0.0}
            
            # 计算加权平均角度
            total_weight = sum(seg.confidence * seg.length for seg in line_segments)
            if total_weight == 0:
                return {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'confidence': 0.0}
            
            weighted_angle = sum(seg.angle * seg.confidence * seg.length for seg in line_segments) / total_weight
            avg_confidence = np.mean([seg.confidence for seg in line_segments])
            
            # 存储历史数据
            self.history_data.append({
                'timestamp': time.time(),
                'angle': weighted_angle,
                'confidence': avg_confidence,
                'line_count': len(line_segments)
            })
            
            # 只保留最近10个数据点
            if len(self.history_data) > 10:
                self.history_data.pop(0)
            
            # 计算趋势
            if len(self.history_data) >= 2:
                current = self.history_data[-1]
                previous = self.history_data[-2]
                angle_change = current['angle'] - previous['angle']
                
                print(f"📊 角度分析: 当前={current['angle']:.1f}°, 前次={previous['angle']:.1f}°, 变化={angle_change:.1f}°")
                
                # 基于当前角度判断信号（而不是角度变化）
                # 使用用户设置的角度阈值
                angle_threshold = self.angle_threshold
                
                print(f"🎯 综合算法判断: 当前角度={weighted_angle:.1f}°, 阈值={angle_threshold}°")
                
                if abs(weighted_angle) > angle_threshold:
                    # 正角度 = 向上倾斜 = 买入信号
                    # 负角度 = 向下倾斜 = 卖出信号
                    signal = 'up' if weighted_angle > 0 else 'down'
                    direction = 'rising' if weighted_angle > 0 else 'falling'
                    confidence = min(1.0, abs(weighted_angle) / 45.0)  # 基于角度大小计算置信度
                    print(f"✅ 触发信号: {signal} ({direction}), 角度={weighted_angle:.1f}° > 阈值{angle_threshold}°")
                else:
                    signal = 'none'
                    direction = 'stable'
                    confidence = avg_confidence
                    print(f"⚪ 无信号: 角度={weighted_angle:.1f}° <= 阈值{angle_threshold}°")
                
                result = {
                    'signal': signal,
                    'direction': direction,
                    'angle': weighted_angle,
                    'angle_change': angle_change,
                    'confidence': confidence,
                    'line_count': len(line_segments)
                }
                
                print(f"📈 趋势分析结果: {result}")
                return result
            
            return {'signal': 'none', 'direction': 'stable', 'angle': weighted_angle, 'confidence': avg_confidence}
            
        except Exception as e:
            print(f"❌ 趋势分析失败: {e}")
            return {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'confidence': 0.0}