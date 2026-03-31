#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能交易引擎
直接操作景陶易购客户端，无需坐标定位
"""

import subprocess
import time
import logging
import pyautogui
import cv2
import numpy as np
from typing import Dict, Optional
import os

class SmartTradingEngine:
    """智能交易引擎"""
    
    def __init__(self, client_path: str = None):
        self.logger = logging.getLogger(__name__)
        
        # 客户端路径
        self.client_path = client_path or r"C:\景陶易购客户端.exe"
        self.client_process = None
        
        # 监测数据
        self.price_history = []
        self.yellow_line_data = []
        self.last_trade_time = 0
        
        # 交易参数
        self.trade_cooldown = 30  # 交易冷却时间
        self.min_price_change = 0.5  # 最小价格变化率
        self.is_running = False
        
        self.logger.info("智能交易引擎初始化完成")
    
    def start_client(self) -> bool:
        """启动客户端"""
        try:
            if not os.path.exists(self.client_path):
                self.logger.error(f"客户端文件不存在: {self.client_path}")
                return False
            
            self.logger.info("启动景陶易购客户端...")
            self.client_process = subprocess.Popen([self.client_path])
            time.sleep(10)  # 等待启动
            
            if self.client_process.poll() is None:
                self.logger.info("客户端启动成功")
                return True
            else:
                self.logger.error("客户端启动失败")
                return False
                
        except Exception as e:
            self.logger.error(f"启动客户端失败: {e}")
            return False
    
    def monitor_and_trade(self):
        """监测并交易"""
        try:
            self.is_running = True
            self.logger.info("开始智能监测和交易")
            
            while self.is_running:
                # 截取屏幕
                screen = pyautogui.screenshot()
                screen_array = np.array(screen)
                
                # 监测黄线
                yellow_signal = self.detect_yellow_line_change(screen_array)
                
                # 监测价格
                price_signal = self.detect_price_change(screen_array)
                
                # 综合判断交易信号
                if yellow_signal['detected'] and price_signal['detected']:
                    trade_signal = self.analyze_trade_signal(yellow_signal, price_signal)
                    
                    if trade_signal['should_trade']:
                        self.execute_trade(trade_signal)
                
                time.sleep(5)  # 每5秒检查一次
                
        except Exception as e:
            self.logger.error(f"监测交易失败: {e}")
    
    def detect_yellow_line_change(self, screen: np.ndarray) -> Dict:
        """检测黄线变化"""
        try:
            # 转换为HSV
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            
            # 黄色范围
            yellow_lower = np.array([15, 100, 100])
            yellow_upper = np.array([35, 255, 255])
            
            # 创建掩码
            mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
            
            # 查找轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)
                x, y, w, h = cv2.boundingRect(largest)
                
                # 记录数据
                self.yellow_line_data.append({
                    'area': area, 'x': x, 'y': y, 'time': time.time()
                })
                
                # 保持最近10个数据点
                if len(self.yellow_line_data) > 10:
                    self.yellow_line_data.pop(0)
                
                # 分析变化
                if len(self.yellow_line_data) >= 2:
                    current = self.yellow_line_data[-1]
                    previous = self.yellow_line_data[-2]
                    
                    area_change = current['area'] - previous['area']
                    position_change = current['y'] - previous['y']
                    
                    if abs(area_change) > 1000 or abs(position_change) > 10:
                        direction = 'up' if area_change > 0 or position_change < 0 else 'down'
                        return {
                            'detected': True,
                            'direction': direction,
                            'change': 'significant'
                        }
                
                return {'detected': True, 'direction': 'none', 'change': 'stable'}
            
            return {'detected': False, 'direction': 'none', 'change': 'none'}
            
        except Exception as e:
            self.logger.error(f"检测黄线变化失败: {e}")
            return {'detected': False, 'direction': 'none', 'change': 'error'}
    
    def detect_price_change(self, screen: np.ndarray) -> Dict:
        """检测价格变化"""
        try:
            # 使用OCR提取价格
            import pytesseract
            
            # 预处理图像
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # OCR识别
            text = pytesseract.image_to_string(blurred, config='--oem 3 --psm 7')
            
            # 提取数字
            import re
            numbers = re.findall(r'\d+\.?\d*', text)
            
            if numbers:
                current_price = float(numbers[0])
                
                # 记录价格历史
                self.price_history.append({
                    'price': current_price,
                    'time': time.time()
                })
                
                # 保持最近5个价格点
                if len(self.price_history) > 5:
                    self.price_history.pop(0)
                
                # 分析价格变化
                if len(self.price_history) >= 3:
                    recent = self.price_history[-3:]
                    change1 = (recent[1]['price'] - recent[0]['price']) / recent[0]['price'] * 100
                    change2 = (recent[2]['price'] - recent[1]['price']) / recent[1]['price'] * 100
                    
                    if abs(change1) > self.min_price_change and abs(change2) > self.min_price_change:
                        if change1 > 0 and change2 > 0:
                            return {
                                'detected': True,
                                'direction': 'up',
                                'price': current_price,
                                'change_rate': change2
                            }
                        elif change1 < 0 and change2 < 0:
                            return {
                                'detected': True,
                                'direction': 'down',
                                'price': current_price,
                                'change_rate': change2
                            }
                
                return {
                    'detected': True,
                    'direction': 'none',
                    'price': current_price,
                    'change_rate': 0
                }
            
            return {'detected': False, 'direction': 'none', 'price': 0, 'change_rate': 0}
            
        except Exception as e:
            self.logger.error(f"检测价格变化失败: {e}")
            return {'detected': False, 'direction': 'none', 'price': 0, 'change_rate': 0}
    
    def analyze_trade_signal(self, yellow_signal: Dict, price_signal: Dict) -> Dict:
        """分析交易信号"""
        try:
            current_time = time.time()
            
            # 检查交易冷却
            if current_time - self.last_trade_time < self.trade_cooldown:
                return {'should_trade': False, 'reason': 'cooldown'}
            
            # 黄线和价格方向一致
            if (yellow_signal['direction'] == price_signal['direction'] and 
                yellow_signal['direction'] != 'none'):
                
                if yellow_signal['direction'] == 'up':
                    return {
                        'should_trade': True,
                        'action': 'buy',
                        'price': price_signal['price'],
                        'reason': '黄线上涨且价格上涨'
                    }
                elif yellow_signal['direction'] == 'down':
                    return {
                        'should_trade': True,
                        'action': 'sell',
                        'price': price_signal['price'],
                        'reason': '黄线下跌且价格下跌'
                    }
            
            return {'should_trade': False, 'reason': 'no_signal'}
            
        except Exception as e:
            self.logger.error(f"分析交易信号失败: {e}")
            return {'should_trade': False, 'reason': 'error'}
    
    def execute_trade(self, signal: Dict):
        """执行交易"""
        try:
            self.logger.info(f"执行交易: {signal['action']} at {signal['price']}")
            
            # 激活客户端窗口
            windows = pyautogui.getWindowsWithTitle("景陶易购")
            if windows:
                windows[0].activate()
                time.sleep(1)
            
            # 执行交易操作
            if signal['action'] == 'buy':
                self._click_buy_button()
                self._input_price(signal['price'])
                self._input_quantity(1)
                self._confirm_order()
            elif signal['action'] == 'sell':
                self._click_sell_button()
                self._input_price(signal['price'])
                self._input_quantity(1)
                self._confirm_order()
            
            self.last_trade_time = time.time()
            self.logger.info("交易执行完成")
            
        except Exception as e:
            self.logger.error(f"执行交易失败: {e}")
    
    def _click_buy_button(self):
        """点击买入按钮"""
        pyautogui.click(x=100, y=200)  # 需要根据实际界面调整
        time.sleep(1)
    
    def _click_sell_button(self):
        """点击卖出按钮"""
        pyautogui.click(x=100, y=250)  # 需要根据实际界面调整
        time.sleep(1)
    
    def _input_price(self, price: float):
        """输入价格"""
        pyautogui.click(x=200, y=300)  # 价格输入框
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.typewrite(str(price))
        time.sleep(0.5)
    
    def _input_quantity(self, quantity: int):
        """输入数量"""
        pyautogui.click(x=200, y=350)  # 数量输入框
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.typewrite(str(quantity))
        time.sleep(0.5)
    
    def _confirm_order(self):
        """确认下单"""
        pyautogui.click(x=300, y=400)  # 确认按钮
        time.sleep(2)
    
    def stop(self):
        """停止交易"""
        self.is_running = False
        if self.client_process:
            self.client_process.terminate()
        self.logger.info("智能交易引擎已停止") 