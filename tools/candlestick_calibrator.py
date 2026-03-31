#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K线颜色校准和区域设置工具
完善的K线检测校准工具，支持颜色校准和区域选择
"""

import cv2
import numpy as np
import pyautogui
import json
import os
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'app', 'src'))

class CandlestickCalibrator:
    """K线校准器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # 配置文件路径
        self.config_dir = os.path.join(project_root, 'app', 'config')
        self.area_config_file = os.path.join(self.config_dir, 'candlestick_area_config.json')
        self.color_config_file = os.path.join(self.config_dir, 'candlestick_color_config.json')
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # 当前配置
        self.chart_area = {
            'x': 0.05,      # 左边界比例
            'y': 0.12,      # 上边界比例  
            'width': 0.65,  # 宽度比例
            'height': 0.55  # 高度比例
        }
        
        # 默认颜色范围
        self.color_ranges = {
            'red': {
                'lower1': [0, 50, 50],
                'upper1': [10, 255, 255],
                'lower2': [170, 50, 50],
                'upper2': [180, 255, 255]
            },
            'blue': {
                'lower': [80, 50, 50],
                'upper': [110, 255, 255]
            },
            'cyan': {
                'lower': [85, 100, 200],
                'upper': [95, 255, 255]
            },
            'green': {
                'lower': [35, 50, 50],
                'upper': [85, 255, 255]
            }
        }
        
        # 加载现有配置
        self.load_configs()
        
        self.logger.info("K线校准器初始化完成")
    
    def setup_logging(self):
        """设置日志"""
        # 确保日志目录存在
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'candlestick_calibrator.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def load_configs(self):
        """加载配置文件"""
        # 加载区域配置
        try:
            if os.path.exists(self.area_config_file):
                with open(self.area_config_file, 'r', encoding='utf-8') as f:
                    area_config = json.load(f)
                    self.chart_area.update(area_config)
                self.logger.info("✅ K线区域配置已加载")
        except Exception as e:
            self.logger.warning(f"⚠️ 加载区域配置失败: {e}")
        
        # 加载颜色配置
        try:
            if os.path.exists(self.color_config_file):
                with open(self.color_config_file, 'r', encoding='utf-8') as f:
                    color_config = json.load(f)
                    self.color_ranges.update(color_config)
                self.logger.info("✅ K线颜色配置已加载")
        except Exception as e:
            self.logger.warning(f"⚠️ 加载颜色配置失败: {e}")
    
    def save_area_config(self):
        """保存区域配置"""
        try:
            with open(self.area_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.chart_area, f, indent=2, ensure_ascii=False)
            self.logger.info("✅ K线区域配置已保存")
            return True
        except Exception as e:
            self.logger.error(f"❌ 保存区域配置失败: {e}")
            return False
    
    def save_color_config(self):
        """保存颜色配置"""
        try:
            with open(self.color_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.color_ranges, f, indent=2, ensure_ascii=False)
            self.logger.info("✅ K线颜色配置已保存")
            return True
        except Exception as e:
            self.logger.error(f"❌ 保存颜色配置失败: {e}")
            return False
    
    def select_chart_area_interactive(self):
        """交互式选择K线图区域"""
        try:
            print("📸 正在截取屏幕...")
            screenshot = pyautogui.screenshot()
            screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            print("🖱️ 请在弹出窗口中选择K线图区域...")
            print("   - 拖拽鼠标选择K线图显示区域")
            print("   - 按SPACE键确认选择")
            print("   - 按ESC键取消选择")
            
            # 创建选择窗口
            window_name = '选择K线图区域 - 拖拽选择后按SPACE确认'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 1200, 800)
            
            # 使用selectROI选择区域
            roi = cv2.selectROI(window_name, screenshot_np, False, False)
            cv2.destroyAllWindows()
            
            if roi[2] > 0 and roi[3] > 0:
                # 转换为相对坐标
                screen_width, screen_height = screenshot.size
                
                self.chart_area = {
                    'x': roi[0] / screen_width,
                    'y': roi[1] / screen_height,
                    'width': roi[2] / screen_width,
                    'height': roi[3] / screen_height
                }
                
                print(f"✅ K线图区域已选择:")
                print(f"   相对坐标: x={self.chart_area['x']:.3f}, y={self.chart_area['y']:.3f}")
                print(f"   尺寸: width={self.chart_area['width']:.3f}, height={self.chart_area['height']:.3f}")
                
                # 保存配置
                if self.save_area_config():
                    print("✅ 区域配置已保存")
                
                return True
            else:
                print("⚠️ 未选择有效区域")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 区域选择失败: {e}")
            return False
    
    def calibrate_colors_interactive(self):
        """交互式颜色校准"""
        try:
            print("🎨 开始K线颜色校准...")
            
            # 截取当前屏幕
            screenshot = pyautogui.screenshot()
            screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 提取K线图区域
            chart_region = self.extract_chart_region(screenshot_np)
            if chart_region is None:
                print("❌ 无法提取K线图区域")
                return False
            
            # 保存调试图像
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_dir = f"logs/color_calibration_{timestamp}"
            os.makedirs(debug_dir, exist_ok=True)
            
            # 保存原始K线图区域
            chart_path = os.path.join(debug_dir, "chart_region.jpg")
            cv2.imwrite(chart_path, chart_region)
            print(f"📊 K线图区域已保存: {chart_path}")
            
            # 转换为HSV
            hsv = cv2.cvtColor(chart_region, cv2.COLOR_BGR2HSV)
            
            # 检测各种颜色
            results = {}
            color_names = ['red', 'blue', 'cyan', 'green']
            
            for color_name in color_names:
                print(f"🔍 检测 {color_name} 颜色块...")
                
                if color_name == 'red':
                    # 红色需要两个范围
                    mask1 = cv2.inRange(hsv, 
                                      np.array(self.color_ranges[color_name]['lower1']),
                                      np.array(self.color_ranges[color_name]['upper1']))
                    mask2 = cv2.inRange(hsv,
                                      np.array(self.color_ranges[color_name]['lower2']),
                                      np.array(self.color_ranges[color_name]['upper2']))
                    mask = cv2.bitwise_or(mask1, mask2)
                else:
                    mask = cv2.inRange(hsv,
                                     np.array(self.color_ranges[color_name]['lower']),
                                     np.array(self.color_ranges[color_name]['upper']))
                
                # 查找轮廓
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # 过滤小轮廓
                min_area = 20
                valid_contours = [c for c in contours if cv2.contourArea(c) >= min_area]
                
                results[color_name] = len(valid_contours)
                
                # 保存调试图像
                mask_path = os.path.join(debug_dir, f"{color_name}_mask.jpg")
                cv2.imwrite(mask_path, mask)
                
                # 绘制检测结果
                result_img = chart_region.copy()
                for contour in valid_contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(result_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(result_img, color_name, (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                result_path = os.path.join(debug_dir, f"{color_name}_detection.jpg")
                cv2.imwrite(result_path, result_img)
                
                print(f"   检测到 {len(valid_contours)} 个 {color_name} 色块")
            
            # 显示检测结果摘要
            print(f"\n🎨 颜色检测结果摘要:")
            for color_name, count in results.items():
                status = "✅" if count > 0 else "❌"
                print(f"   {status} {color_name}: {count} 个色块")
            
            # 建议优化
            print(f"\n💡 优化建议:")
            if results['red'] == 0:
                print("   🔴 红色检测失败，建议调整红色HSV范围")
            if results['blue'] == 0 and results['cyan'] == 0:
                print("   🔵 蓝色/青色检测失败，建议调整蓝色HSV范围")
            if sum(results.values()) == 0:
                print("   ⚠️ 未检测到任何颜色块，请检查:")
                print("      1. K线图区域是否正确")
                print("      2. 当前是否显示K线图")
                print("      3. K线图是否包含彩色柱状图")
            
            print(f"\n📁 所有调试文件已保存到: {debug_dir}")
            
            # 询问是否调整颜色范围
            if sum(results.values()) > 0:
                adjust = input("\n🔧 是否需要调整颜色范围？(y/n): ").lower()
                if adjust == 'y':
                    self.interactive_color_adjustment(chart_region, hsv, debug_dir)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 颜色校准失败: {e}")
            return False
    
    def interactive_color_adjustment(self, chart_region, hsv, debug_dir):
        """交互式颜色范围调整"""
        print("\n🎛️ 进入交互式颜色调整模式...")
        print("提示: 这将打开颜色范围调整窗口")
        
        # 创建调整窗口
        def nothing(val):
            pass
        
        cv2.namedWindow('Color Range Adjustment')
        cv2.namedWindow('Original Chart')
        cv2.namedWindow('Color Mask')
        
        # 创建滑块
        cv2.createTrackbar('H Min', 'Color Range Adjustment', 0, 179, nothing)
        cv2.createTrackbar('S Min', 'Color Range Adjustment', 50, 255, nothing)
        cv2.createTrackbar('V Min', 'Color Range Adjustment', 50, 255, nothing)
        cv2.createTrackbar('H Max', 'Color Range Adjustment', 179, 179, nothing)
        cv2.createTrackbar('S Max', 'Color Range Adjustment', 255, 255, nothing)
        cv2.createTrackbar('V Max', 'Color Range Adjustment', 255, 255, nothing)
        
        print("🎛️ 调整滑块来优化颜色检测:")
        print("   - H: 色调 (0-179)")
        print("   - S: 饱和度 (0-255)")  
        print("   - V: 亮度 (0-255)")
        print("   - 按 'r' 检测红色")
        print("   - 按 'b' 检测蓝色")
        print("   - 按 'c' 检测青色")
        print("   - 按 'g' 检测绿色")
        print("   - 按 's' 保存当前设置")
        print("   - 按 'q' 退出")
        
        current_color = 'red'
        
        while True:
            # 获取滑块值
            h_min = cv2.getTrackbarPos('H Min', 'Color Range Adjustment')
            s_min = cv2.getTrackbarPos('S Min', 'Color Range Adjustment')
            v_min = cv2.getTrackbarPos('V Min', 'Color Range Adjustment')
            h_max = cv2.getTrackbarPos('H Max', 'Color Range Adjustment')
            s_max = cv2.getTrackbarPos('S Max', 'Color Range Adjustment')
            v_max = cv2.getTrackbarPos('V Max', 'Color Range Adjustment')
            
            # 创建掩码
            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])
            mask = cv2.inRange(hsv, lower, upper)
            
            # 显示结果
            cv2.imshow('Original Chart', chart_region)
            cv2.imshow('Color Mask', mask)
            
            # 应用掩码到原图
            result = cv2.bitwise_and(chart_region, chart_region, mask=mask)
            cv2.imshow('Color Range Adjustment', result)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('r'):
                current_color = 'red'
                print(f"🔴 切换到红色调整模式")
            elif key == ord('b'):
                current_color = 'blue'
                print(f"🔵 切换到蓝色调整模式")
            elif key == ord('c'):
                current_color = 'cyan'
                print(f"🔵 切换到青色调整模式")
            elif key == ord('g'):
                current_color = 'green'
                print(f"🟢 切换到绿色调整模式")
            elif key == ord('s'):
                # 保存当前设置
                if current_color == 'red':
                    self.color_ranges[current_color]['lower1'] = [h_min, s_min, v_min]
                    self.color_ranges[current_color]['upper1'] = [h_max, s_max, v_max]
                else:
                    self.color_ranges[current_color]['lower'] = [h_min, s_min, v_min]
                    self.color_ranges[current_color]['upper'] = [h_max, s_max, v_max]
                
                print(f"✅ {current_color} 颜色范围已保存: [{h_min}, {s_min}, {v_min}] - [{h_max}, {s_max}, {v_max}]")
                
                # 保存到配置文件
                self.save_color_config()
        
        cv2.destroyAllWindows()
    
    def extract_chart_region(self, screenshot):
        """从截图中提取K线图区域"""
        try:
            height, width = screenshot.shape[:2]
            
            # 计算绝对坐标
            x = int(width * self.chart_area['x'])
            y = int(height * self.chart_area['y'])
            w = int(width * self.chart_area['width'])
            h = int(height * self.chart_area['height'])
            
            # 确保坐标在有效范围内
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = max(1, min(w, width - x))
            h = max(1, min(h, height - y))
            
            # 提取区域
            chart_region = screenshot[y:y+h, x:x+w]
            
            if chart_region.size == 0:
                self.logger.error("❌ K线图区域为空")
                return None
                
            return chart_region
            
        except Exception as e:
            self.logger.error(f"❌ 提取K线图区域失败: {e}")
            return None
    
    def test_detection(self):
        """测试当前配置的检测效果"""
        try:
            print("🧪 测试当前K线检测配置...")
            
            # 截取屏幕
            screenshot = pyautogui.screenshot()
            screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 提取K线图区域
            chart_region = self.extract_chart_region(screenshot_np)
            if chart_region is None:
                return False
            
            # 保存测试图像
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_dir = f"logs/detection_test_{timestamp}"
            os.makedirs(test_dir, exist_ok=True)
            
            # 保存原始区域
            original_path = os.path.join(test_dir, "original_chart.jpg")
            cv2.imwrite(original_path, chart_region)
            
            # 转换为HSV
            hsv = cv2.cvtColor(chart_region, cv2.COLOR_BGR2HSV)
            
            # 检测各颜色并创建组合结果图
            result_img = chart_region.copy()
            total_detections = 0
            
            color_info = {
                'red': {'color': (0, 0, 255), 'count': 0},
                'blue': {'color': (255, 0, 0), 'count': 0},
                'cyan': {'color': (255, 255, 0), 'count': 0},
                'green': {'color': (0, 255, 0), 'count': 0}
            }
            
            for color_name in color_info.keys():
                if color_name == 'red':
                    # 红色需要两个范围
                    mask1 = cv2.inRange(hsv, 
                                      np.array(self.color_ranges[color_name]['lower1']),
                                      np.array(self.color_ranges[color_name]['upper1']))
                    mask2 = cv2.inRange(hsv,
                                      np.array(self.color_ranges[color_name]['lower2']),
                                      np.array(self.color_ranges[color_name]['upper2']))
                    mask = cv2.bitwise_or(mask1, mask2)
                else:
                    mask = cv2.inRange(hsv,
                                     np.array(self.color_ranges[color_name]['lower']),
                                     np.array(self.color_ranges[color_name]['upper']))
                
                # 查找轮廓
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                valid_contours = [c for c in contours if cv2.contourArea(c) >= 20]
                
                color_info[color_name]['count'] = len(valid_contours)
                total_detections += len(valid_contours)
                
                # 在结果图上标记
                for contour in valid_contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(result_img, (x, y), (x+w, y+h), color_info[color_name]['color'], 2)
                    cv2.putText(result_img, color_name[:3].upper(), (x, y-5), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_info[color_name]['color'], 1)
            
            # 保存结果图
            result_path = os.path.join(test_dir, "detection_result.jpg")
            cv2.imwrite(result_path, result_img)
            
            # 显示检测统计
            print(f"\n📊 检测结果统计:")
            print(f"   🔴 红色K线: {color_info['red']['count']} 个")
            print(f"   🔵 蓝色K线: {color_info['blue']['count']} 个") 
            print(f"   🔵 青色K线: {color_info['cyan']['count']} 个")
            print(f"   🟢 绿色K线: {color_info['green']['count']} 个")
            print(f"   📈 总计: {total_detections} 个K线")
            
            print(f"\n📁 测试结果已保存到: {test_dir}")
            
            return total_detections > 0
            
        except Exception as e:
            self.logger.error(f"❌ 检测测试失败: {e}")
            return False
    
    def run_gui(self):
        """运行图形界面"""
        root = tk.Tk()
        root.title("K线颜色校准和区域设置工具")
        root.geometry("500x600")
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="K线颜色校准和区域设置工具", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 区域设置部分
        area_frame = ttk.LabelFrame(main_frame, text="K线图区域设置", padding="10")
        area_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(area_frame, text="当前区域:").grid(row=0, column=0, sticky=tk.W)
        area_info = f"x: {self.chart_area['x']:.3f}, y: {self.chart_area['y']:.3f}\n"
        area_info += f"width: {self.chart_area['width']:.3f}, height: {self.chart_area['height']:.3f}"
        area_label = ttk.Label(area_frame, text=area_info)
        area_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 10))
        
        ttk.Button(area_frame, text="选择K线图区域", 
                  command=self.select_chart_area_interactive).grid(row=2, column=0, pady=5)
        
        # 颜色校准部分  
        color_frame = ttk.LabelFrame(main_frame, text="颜色校准", padding="10")
        color_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(color_frame, text="开始颜色校准", 
                  command=self.calibrate_colors_interactive).grid(row=0, column=0, pady=5)
        ttk.Button(color_frame, text="测试检测效果", 
                  command=self.test_detection).grid(row=1, column=0, pady=5)
        
        # 配置管理部分
        config_frame = ttk.LabelFrame(main_frame, text="配置管理", padding="10") 
        config_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(config_frame, text="保存区域配置", 
                  command=self.save_area_config).grid(row=0, column=0, padx=(0, 5), pady=5)
        ttk.Button(config_frame, text="保存颜色配置", 
                  command=self.save_color_config).grid(row=0, column=1, padx=(5, 0), pady=5)
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = tk.Text(log_frame, height=15, width=60)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 添加初始日志
        self.log_text.insert(tk.END, "K线校准工具已启动\n")
        self.log_text.insert(tk.END, f"配置文件位置:\n")
        self.log_text.insert(tk.END, f"- 区域: {self.area_config_file}\n")
        self.log_text.insert(tk.END, f"- 颜色: {self.color_config_file}\n\n")
        
        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 启动GUI
        root.mainloop()

def main():
    """主函数"""
    print("🚀 启动K线颜色校准和区域设置工具")
    print("=" * 50)
    
    calibrator = CandlestickCalibrator()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == 'area':
            # 仅设置区域
            print("📍 区域设置模式")
            calibrator.select_chart_area_interactive()
        elif mode == 'color':
            # 仅颜色校准
            print("🎨 颜色校准模式")
            calibrator.calibrate_colors_interactive()
        elif mode == 'test':
            # 仅测试
            print("🧪 检测测试模式")
            calibrator.test_detection()
        elif mode == 'gui':
            # GUI模式
            calibrator.run_gui()
        else:
            print("使用方法:")
            print("  python candlestick_calibrator.py         # 交互式命令行模式")
            print("  python candlestick_calibrator.py gui     # 图形界面模式")
            print("  python candlestick_calibrator.py area    # 仅设置区域")
            print("  python candlestick_calibrator.py color   # 仅颜色校准")
            print("  python candlestick_calibrator.py test    # 仅测试检测")
    else:
        # 交互式命令行模式
        while True:
            print("\n🎯 请选择操作:")
            print("1. 设置K线图区域")
            print("2. 颜色校准")
            print("3. 测试检测效果")
            print("4. 启动图形界面")
            print("5. 退出")
            
            choice = input("\n请输入选择 (1-5): ").strip()
            
            if choice == '1':
                calibrator.select_chart_area_interactive()
            elif choice == '2':
                calibrator.calibrate_colors_interactive()
            elif choice == '3':
                calibrator.test_detection()
            elif choice == '4':
                calibrator.run_gui()
                break
            elif choice == '5':
                print("👋 再见!")
                break
            else:
                print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main()