#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实坐标校准工具
用于获取景陶易购客户端的真实UI元素坐标
"""

import pyautogui
import cv2
import numpy as np
import json
import time
import os
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox

class RealCoordinateCalibrator:
    """真实坐标校准器"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("真实坐标校准工具")
        self.root.geometry("1200x800")
        
        # 存储坐标
        self.coordinates = {
            'price_reading': {
                'recognition_areas': {
                    'latest_price': None,
                    'real_time_value_change': None,
                    'value_change': None,
                    'market_status': None
                }
            },
            'order_execution': {
                'ui_elements': {
                    'buy_button': None,
                    'sell_button': None,
                    'price_input': None,
                    'quantity_input': None,
                    'confirm_order_button': None,
                    'cancel_order_button': None,
                    'transfer_button': None,
                    'place_order_button': None,
                    'agreement_checkbox': None
                }
            }
        }
        
        # 当前选择的元素
        self.current_element = None
        self.element_list = [
            ('price_reading', 'recognition_areas', 'latest_price', '最新价'),
            ('price_reading', 'recognition_areas', 'real_time_value_change', '实时货值变化'),
            ('price_reading', 'recognition_areas', 'value_change', '货值变化'),
            ('price_reading', 'recognition_areas', 'market_status', '市场状态'),
            ('order_execution', 'ui_elements', 'buy_button', '买入按钮'),
            ('order_execution', 'ui_elements', 'sell_button', '卖出按钮'),
            ('order_execution', 'ui_elements', 'price_input', '买价输入框'),
            ('order_execution', 'ui_elements', 'quantity_input', '买量输入框'),
            ('order_execution', 'ui_elements', 'place_order_button', '订立按钮'),
            ('order_execution', 'ui_elements', 'transfer_button', '转让按钮'),
            ('order_execution', 'ui_elements', 'confirm_order_button', '确定按钮'),
            ('order_execution', 'ui_elements', 'cancel_order_button', '取消按钮')
        ]
        
        self.current_index = 0
        self.screenshot = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="5")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 当前元素显示
        self.element_var = tk.StringVar(value="准备开始...")
        ttk.Label(control_frame, text="当前元素:").pack(anchor=tk.W, pady=5)
        ttk.Label(control_frame, textvariable=self.element_var, font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        # 进度显示
        self.progress_var = tk.StringVar(value="0/12")
        ttk.Label(control_frame, text="进度:").pack(anchor=tk.W, pady=5)
        ttk.Label(control_frame, textvariable=self.progress_var).pack(anchor=tk.W, pady=5)
        
        # 操作按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="截取屏幕", command=self.capture_screen).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="选择区域", command=self.select_area).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="跳过此元素", command=self.skip_element).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="重新开始", command=self.restart).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="保存配置", command=self.save_config).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="加载配置", command=self.load_config).pack(fill=tk.X, pady=2)
        
        # 坐标显示
        coord_frame = ttk.LabelFrame(control_frame, text="坐标信息", padding="5")
        coord_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.coord_text = tk.Text(coord_frame, width=30, height=15)
        self.coord_text.pack(fill=tk.BOTH, expand=True)
        
        # 右侧截图显示区域
        screenshot_frame = ttk.LabelFrame(main_frame, text="屏幕截图", padding="5")
        screenshot_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.screenshot_label = ttk.Label(screenshot_frame, text="点击'截取屏幕'获取截图")
        self.screenshot_label.pack(expand=True, fill=tk.BOTH)
        
        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        self.update_display()
    
    def update_display(self):
        """更新显示"""
        if self.current_index < len(self.element_list):
            category, subcategory, element_name, display_name = self.element_list[self.current_index]
            self.element_var.set(f"{display_name}")
            self.progress_var.set(f"{self.current_index + 1}/{len(self.element_list)}")
            
            # 显示当前元素的坐标信息
            if self.coordinates[category][subcategory][element_name]:
                coord = self.coordinates[category][subcategory][element_name]
                coord_text = f"元素: {display_name}\n"
                coord_text += f"X: {coord['x']}\n"
                coord_text += f"Y: {coord['y']}\n"
                coord_text += f"宽度: {coord['width']}\n"
                coord_text += f"高度: {coord['height']}\n"
            else:
                coord_text = f"元素: {display_name}\n"
                coord_text += "坐标: 未设置\n"
            
            self.coord_text.delete(1.0, tk.END)
            self.coord_text.insert(1.0, coord_text)
        else:
            self.element_var.set("所有元素已完成")
            self.progress_var.set(f"{len(self.element_list)}/{len(self.element_list)}")
    
    def capture_screen(self):
        """截取屏幕"""
        try:
            self.root.withdraw()  # 隐藏窗口
            time.sleep(1)  # 等待1秒
            
            # 截取屏幕
            screenshot = pyautogui.screenshot()
            self.screenshot = np.array(screenshot)
            
            # 显示截图
            screenshot_rgb = cv2.cvtColor(self.screenshot, cv2.COLOR_BGR2RGB)
            screenshot_resized = cv2.resize(screenshot_rgb, (800, 600))
            
            # 转换为PIL图像用于显示
            pil_image = Image.fromarray(screenshot_resized)
            photo = ImageTk.PhotoImage(pil_image)
            
            self.screenshot_label.configure(image=photo, text="")
            self.screenshot_label.image = photo  # 保持引用
            
            self.root.deiconify()  # 重新显示窗口
            messagebox.showinfo("成功", "屏幕截图已获取")
            
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("错误", f"截取屏幕失败: {e}")
    
    def select_area(self):
        """选择区域"""
        if self.screenshot is None:
            messagebox.showwarning("警告", "请先截取屏幕")
            return
        
        if self.current_index >= len(self.element_list):
            messagebox.showinfo("提示", "所有元素已完成")
            return
        
        try:
            self.root.withdraw()  # 隐藏窗口
            time.sleep(0.5)
            
            # 使用OpenCV选择ROI
            cv2.namedWindow("选择区域 - 拖动鼠标选择，按Enter确认", cv2.WINDOW_NORMAL)
            roi = cv2.selectROI("选择区域 - 拖动鼠标选择，按Enter确认", 
                               cv2.cvtColor(self.screenshot, cv2.COLOR_RGB2BGR))
            
            if roi[2] > 0 and roi[3] > 0:  # 确保选择了有效区域
                x, y, w, h = roi
                
                # 保存坐标
                category, subcategory, element_name, display_name = self.element_list[self.current_index]
                self.coordinates[category][subcategory][element_name] = {
                    'x': x, 'y': y, 'width': w, 'height': h
                }
                
                messagebox.showinfo("成功", f"已保存 {display_name} 的坐标")
                self.current_index += 1
                self.update_display()
            
            cv2.destroyAllWindows()
            self.root.deiconify()
            
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("错误", f"选择区域失败: {e}")
    
    def skip_element(self):
        """跳过当前元素"""
        if self.current_index < len(self.element_list):
            self.current_index += 1
            self.update_display()
            messagebox.showinfo("提示", "已跳过当前元素")
    
    def restart(self):
        """重新开始"""
        self.current_index = 0
        self.coordinates = {
            'price_reading': {'recognition_areas': {}},
            'order_execution': {'ui_elements': {}}
        }
        self.update_display()
        messagebox.showinfo("提示", "已重新开始")
    
    def save_config(self):
        """保存配置"""
        try:
            config_file = "real_coordinates_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.coordinates, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", f"配置已保存到 {config_file}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def load_config(self):
        """加载配置"""
        try:
            config_file = "real_coordinates_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.coordinates = json.load(f)
                
                self.update_display()
                messagebox.showinfo("成功", f"配置已从 {config_file} 加载")
            else:
                messagebox.showwarning("警告", "配置文件不存在")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {e}")
    
    def run(self):
        """运行工具"""
        self.root.mainloop()

def main():
    """主函数"""
    print("启动真实坐标校准工具...")
    calibrator = RealCoordinateCalibrator()
    calibrator.run()

if __name__ == "__main__":
    main() 