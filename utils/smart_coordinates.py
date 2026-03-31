#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能坐标定位系统
根据客户端窗口大小动态计算按钮位置
"""

import pyautogui
import time
import logging
from typing import Dict, Tuple, Optional
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class SmartCoordinateFinder:
    """智能坐标定位器"""
    
    def __init__(self):
        self.client_window = None
        self.window_rect = None
        self.relative_positions = {
            'buy_button': (0.1, 0.3),      # 买入按钮相对位置 (x%, y%)
            'sell_button': (0.1, 0.4),     # 卖出按钮相对位置
            'buy_order_button': (0.15, 0.75),  # 买入订立按钮相对位置
            'sell_order_button': (0.15, 0.80), # 卖出订立按钮相对位置
            'order_button': (0.35, 0.75),      # 订立按钮相对位置
            'price_input': (0.3, 0.5),     # 价格输入框相对位置
            'quantity_input': (0.3, 0.6),  # 数量输入框相对位置
            'confirm_button': (0.5, 0.7),  # 确认按钮相对位置
            'transfer_out_button': (0.6, 0.8)  # 转出按钮相对位置
        }
        
        logger.info("智能坐标定位器初始化完成")
    
    def find_client_window(self) -> bool:
        """查找客户端窗口"""
        try:
            # 方法1: 通过窗口标题查找
            windows = pyautogui.getWindowsWithTitle("景陶易购")
            if windows:
                self.client_window = windows[0]
                self.window_rect = self.client_window.rect
                logger.info(f"找到客户端窗口: {self.client_window.title}")
                logger.info(f"窗口位置: {self.window_rect}")
                return True
            
            # 方法2: 通过关键词查找
            all_windows = pyautogui.getAllWindows()
            for window in all_windows:
                if any(keyword in window.title for keyword in ['景陶易购', 'DEAL', 'JCST', 'RNHY']):
                    self.client_window = window
                    self.window_rect = self.client_window.rect
                    logger.info(f"找到相关客户端窗口: {window.title}")
                    logger.info(f"窗口位置: {self.window_rect}")
                    return True
            
            logger.warning("未找到客户端窗口")
            return False
            
        except Exception as e:
            logger.error(f"查找客户端窗口失败: {e}")
            return False
    
    def calculate_absolute_position(self, relative_x: float, relative_y: float) -> Tuple[int, int]:
        """根据相对位置计算绝对坐标"""
        if not self.window_rect:
            raise ValueError("窗口位置未设置")
        
        # 计算绝对坐标
        abs_x = int(self.window_rect.left + self.window_rect.width * relative_x)
        abs_y = int(self.window_rect.top + self.window_rect.height * relative_y)
        
        return abs_x, abs_y
    
    def get_button_position(self, button_name: str) -> Tuple[int, int]:
        """获取按钮的绝对坐标"""
        try:
            if button_name not in self.relative_positions:
                raise ValueError(f"未知的按钮名称: {button_name}")
            
            relative_x, relative_y = self.relative_positions[button_name]
            abs_x, abs_y = self.calculate_absolute_position(relative_x, relative_y)
            
            logger.info(f"按钮 {button_name} 坐标: ({abs_x}, {abs_y})")
            return abs_x, abs_y
            
        except Exception as e:
            logger.error(f"获取按钮位置失败: {e}")
            return None, None
    
    def find_buttons_by_image(self) -> Dict[str, Tuple[int, int]]:
        """通过图像识别查找按钮"""
        try:
            # 激活客户端窗口
            if self.client_window:
                self.client_window.activate()
                time.sleep(1)
            
            # 截取窗口区域
            screenshot = pyautogui.screenshot(region=(
                self.window_rect.left, self.window_rect.top,
                self.window_rect.width, self.window_rect.height
            ))
            screen_array = np.array(screenshot)
            
            # 查找按钮
            buttons = {}
            
            # 查找买入按钮 (通常有"买入"文字)
            buy_pos = self.find_text_in_image(screen_array, "买入")
            if buy_pos:
                buttons['buy_button'] = (
                    self.window_rect.left + buy_pos[0],
                    self.window_rect.top + buy_pos[1]
                )
            
            # 查找卖出按钮
            sell_pos = self.find_text_in_image(screen_array, "卖出")
            if sell_pos:
                buttons['sell_button'] = (
                    self.window_rect.left + sell_pos[0],
                    self.window_rect.top + sell_pos[1]
                )
            
            # 查找确认按钮
            confirm_pos = self.find_text_in_image(screen_array, "确认")
            if confirm_pos:
                buttons['confirm_button'] = (
                    self.window_rect.left + confirm_pos[0],
                    self.window_rect.top + confirm_pos[1]
                )
            
            logger.info(f"通过图像识别找到 {len(buttons)} 个按钮")
            return buttons
            
        except Exception as e:
            logger.error(f"图像识别按钮失败: {e}")
            return {}
    
    def find_text_in_image(self, image: np.ndarray, text: str) -> Optional[Tuple[int, int]]:
        """在图像中查找文字位置"""
        try:
            import pytesseract
            
            # 设置Tesseract路径
            pytesseract.pytesseract.tesseract_cmd = r"D:\Program Files\tessdata\tesseract.exe"
            
            # OCR识别
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # 查找指定文字
            for i, word in enumerate(data['text']):
                if text in word:
                    x = data['left'][i]
                    y = data['top'][i]
                    return x, y
            
            return None
            
        except Exception as e:
            logger.error(f"查找文字失败: {e}")
            return None
    
    def auto_calibrate_positions(self) -> bool:
        """自动校准按钮位置"""
        try:
            logger.info("开始自动校准按钮位置...")
            
            # 查找客户端窗口
            if not self.find_client_window():
                return False
            
            # 通过图像识别查找按钮
            detected_buttons = self.find_buttons_by_image()
            
            if detected_buttons:
                # 更新相对位置
                for button_name, (abs_x, abs_y) in detected_buttons.items():
                    if self.window_rect:
                        rel_x = (abs_x - self.window_rect.left) / self.window_rect.width
                        rel_y = (abs_y - self.window_rect.top) / self.window_rect.height
                        self.relative_positions[button_name] = (rel_x, rel_y)
                        logger.info(f"校准 {button_name}: 相对位置 ({rel_x:.3f}, {rel_y:.3f})")
                
                return True
            
            logger.warning("未通过图像识别找到按钮，使用默认相对位置")
            return False
            
        except Exception as e:
            logger.error(f"自动校准失败: {e}")
            return False
    
    def click_button(self, button_name: str, wait_time: float = 1.0) -> bool:
        """点击按钮"""
        try:
            x, y = self.get_button_position(button_name)
            if x is not None and y is not None:
                # 激活窗口
                if self.client_window:
                    self.client_window.activate()
                    time.sleep(0.5)
                
                # 点击按钮
                pyautogui.click(x, y)
                time.sleep(wait_time)
                logger.info(f"成功点击 {button_name}")
                return True
            else:
                logger.error(f"无法获取 {button_name} 的位置")
                return False
                
        except Exception as e:
            logger.error(f"点击按钮失败: {e}")
            return False
    
    def input_text(self, input_name: str, text: str, wait_time: float = 0.5) -> bool:
        """在输入框中输入文字"""
        try:
            x, y = self.get_button_position(input_name)
            if x is not None and y is not None:
                # 激活窗口
                if self.client_window:
                    self.client_window.activate()
                    time.sleep(0.5)
                
                # 点击输入框
                pyautogui.click(x, y)
                time.sleep(0.2)
                
                # 全选并输入
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.typewrite(str(text))
                time.sleep(wait_time)
                
                logger.info(f"成功在 {input_name} 输入: {text}")
                return True
            else:
                logger.error(f"无法获取 {input_name} 的位置")
                return False
                
        except Exception as e:
            logger.error(f"输入文字失败: {e}")
            return False
    
    def get_window_info(self) -> Dict:
        """获取窗口信息"""
        if self.client_window and self.window_rect:
            return {
                'title': self.client_window.title,
                'left': self.window_rect.left,
                'top': self.window_rect.top,
                'width': self.window_rect.width,
                'height': self.window_rect.height,
                'right': self.window_rect.right,
                'bottom': self.window_rect.bottom
            }
        return {}

class SmartTradingExecutor:
    """智能交易执行器"""
    
    def __init__(self):
        self.coord_finder = SmartCoordinateFinder()
        logger.info("智能交易执行器初始化完成")
    
    def setup(self) -> bool:
        """设置交易执行器"""
        try:
            # 查找客户端窗口
            if not self.coord_finder.find_client_window():
                return False
            
            # 自动校准按钮位置
            self.coord_finder.auto_calibrate_positions()
            
            logger.info("智能交易执行器设置完成")
            return True
            
        except Exception as e:
            logger.error(f"设置交易执行器失败: {e}")
            return False
    
    def execute_buy_order(self, price: float, quantity: int = 1) -> bool:
        """执行买入订单"""
        try:
            logger.info(f"执行买入订单: 价格={price}, 数量={quantity}")
            
            # 点击买入按钮
            if not self.coord_finder.click_button('buy_button'):
                return False
            
            # 输入价格
            if not self.coord_finder.input_text('price_input', str(price)):
                return False
            
            # 输入数量
            if not self.coord_finder.input_text('quantity_input', str(quantity)):
                return False
            
            # 点击确认
            if not self.coord_finder.click_button('confirm_button', 2.0):
                return False
            
            logger.info("买入订单执行完成")
            return True
            
        except Exception as e:
            logger.error(f"执行买入订单失败: {e}")
            return False
    
    def execute_sell_order(self, price: float, quantity: int = 1) -> bool:
        """执行卖出订单"""
        try:
            logger.info(f"执行卖出订单: 价格={price}, 数量={quantity}")
            
            # 点击卖出按钮
            if not self.coord_finder.click_button('sell_button'):
                return False
            
            # 输入价格
            if not self.coord_finder.input_text('price_input', str(price)):
                return False
            
            # 输入数量
            if not self.coord_finder.input_text('quantity_input', str(quantity)):
                return False
            
            # 点击确认
            if not self.coord_finder.click_button('confirm_button', 2.0):
                return False
            
            logger.info("卖出订单执行完成")
            return True
            
        except Exception as e:
            logger.error(f"执行卖出订单失败: {e}")
            return False
    
    def execute_transfer(self) -> bool:
        """执行转账操作"""
        try:
            logger.info("执行转账操作")
            
            # 点击转账按钮
            if not self.coord_finder.click_button('transfer_button', 2.0):
                return False
            
            logger.info("转账操作执行完成")
            return True
            
        except Exception as e:
            logger.error(f"执行转账操作失败: {e}")
            return False
    
    def get_window_info(self) -> Dict:
        """获取窗口信息"""
        return self.coord_finder.get_window_info() 