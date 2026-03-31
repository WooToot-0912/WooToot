#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接客户端控制器
直接操作景陶易购客户端.exe，无需坐标定位
"""

import subprocess
import time
import logging
import pyautogui
import cv2
import numpy as np
from typing import Dict, Optional, List
import os
import psutil

class DirectClientController:
    """直接客户端控制器"""
    
    def __init__(self, client_path: str = None):
        self.logger = logging.getLogger(__name__)
        
        # 客户端路径
        self.client_path = client_path or r"C:\景陶易购客户端.exe"
        self.client_process = None
        self.client_window = None
        
        # 价格历史数据
        self.price_history = []
        self.max_price_history = 10
        
        # 黄线监测
        self.yellow_line_history = []
        self.max_line_history = 5
        
        # 交易状态
        self.is_client_running = False
        self.last_trade_time = 0
        self.trade_cooldown = 30  # 交易冷却时间（秒）
        
        self.logger.info("直接客户端控制器初始化完成")
    
    def start_client(self) -> bool:
        """启动景陶易购客户端"""
        try:
            # 检查客户端是否已运行
            if self.is_client_running:
                self.logger.info("客户端已在运行")
                return True
            
            # 检查客户端文件是否存在
            if not os.path.exists(self.client_path):
                self.logger.error(f"客户端文件不存在: {self.client_path}")
                return False
            
            # 启动客户端
            self.logger.info(f"正在启动客户端: {self.client_path}")
            self.client_process = subprocess.Popen([self.client_path])
            
            # 等待客户端启动
            time.sleep(10)
            
            # 检查进程是否成功启动
            if self.client_process.poll() is None:
                self.is_client_running = True
                self.logger.info("客户端启动成功")
                return True
            else:
                self.logger.error("客户端启动失败")
                return False
                
        except Exception as e:
            self.logger.error(f"启动客户端失败: {e}")
            return False
    
    def stop_client(self):
        """停止客户端"""
        try:
            if self.client_process:
                self.client_process.terminate()
                self.client_process.wait(timeout=10)
                self.logger.info("客户端已停止")
            
            self.is_client_running = False
            
        except Exception as e:
            self.logger.error(f"停止客户端失败: {e}")
    
    def find_client_window(self) -> bool:
        """查找客户端窗口"""
        try:
            # 使用pyautogui查找窗口
            windows = pyautogui.getWindowsWithTitle("景陶易购")
            if windows:
                self.client_window = windows[0]
                self.client_window.activate()
                self.logger.info("找到客户端窗口并激活")
                return True
            else:
                self.logger.warning("未找到客户端窗口")
                return False
                
        except Exception as e:
            self.logger.error(f"查找客户端窗口失败: {e}")
            return False
    
    def monitor_yellow_line(self, screen_image: np.ndarray) -> Dict:
        """监测黄线变动"""
        try:
            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(screen_image, cv2.COLOR_BGR2HSV)
            
            # 黄色范围
            yellow_lower = np.array([15, 100, 100])
            yellow_upper = np.array([35, 255, 255])
            
            # 创建黄色掩码
            yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
            
            # 查找轮廓
            contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # 找到最大的黄色区域
                largest_contour = max(contours, key=cv2.contourArea)
                
                # 获取轮廓的边界框
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # 计算黄线特征
                line_feature = {
                    'x': x, 'y': y, 'width': w, 'height': h,
                    'area': cv2.contourArea(largest_contour),
                    'timestamp': time.time()
                }
                
                # 更新历史
                self.yellow_line_history.append(line_feature)
                if len(self.yellow_line_history) > self.max_line_history:
                    self.yellow_line_history.pop(0)
                
                # 分析变动
                return self._analyze_yellow_line_change()
            
            return {'detected': False, 'change': 'none'}
            
        except Exception as e:
            self.logger.error(f"监测黄线失败: {e}")
            return {'detected': False, 'change': 'error'}
    
    def _analyze_yellow_line_change(self) -> Dict:
        """分析黄线变动"""
        try:
            if len(self.yellow_line_history) < 2:
                return {'detected': True, 'change': 'insufficient_data'}
            
            # 获取最新的两个数据点
            current = self.yellow_line_history[-1]
            previous = self.yellow_line_history[-2]
            
            # 计算变动
            area_change = current['area'] - previous['area']
            position_change = current['y'] - previous['y']
            
            # 判断变动方向
            if area_change > 1000:  # 面积显著增加
                return {'detected': True, 'change': 'expanding', 'direction': 'up'}
            elif area_change < -1000:  # 面积显著减少
                return {'detected': True, 'change': 'contracting', 'direction': 'down'}
            elif position_change > 10:  # 位置向下移动
                return {'detected': True, 'change': 'moving_down', 'direction': 'down'}
            elif position_change < -10:  # 位置向上移动
                return {'detected': True, 'change': 'moving_up', 'direction': 'up'}
            else:
                return {'detected': True, 'change': 'stable', 'direction': 'none'}
                
        except Exception as e:
            self.logger.error(f"分析黄线变动失败: {e}")
            return {'detected': False, 'change': 'error'}
    
    def extract_price_from_screen(self, screen_image: np.ndarray) -> Optional[float]:
        """从屏幕提取最新价格"""
        try:
            # 使用OCR识别价格
            import pytesseract
            
            # 预处理图像
            gray = cv2.cvtColor(screen_image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # 尝试多种OCR配置
            ocr_configs = [
                '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.',
                '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.',
                '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.'
            ]
            
            for config in ocr_configs:
                try:
                    text = pytesseract.image_to_string(blurred, config=config)
                    # 提取数字
                    import re
                    numbers = re.findall(r'\d+\.?\d*', text)
                    if numbers:
                        price = float(numbers[0])
                        if 1000 <= price <= 10000:  # 合理的价格范围
                            return price
                except:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"提取价格失败: {e}")
            return None
    
    def monitor_price_changes(self, screen_image: np.ndarray) -> Dict:
        """监测价格变化"""
        try:
            current_price = self.extract_price_from_screen(screen_image)
            
            if current_price is None:
                return {'detected': False, 'change': 'no_price'}
            
            # 更新价格历史
            self.price_history.append({
                'price': current_price,
                'timestamp': time.time()
            })
            
            if len(self.price_history) > self.max_price_history:
                self.price_history.pop(0)
            
            # 分析价格变化
            if len(self.price_history) >= 3:
                return self._analyze_price_change()
            
            return {'detected': True, 'change': 'insufficient_data', 'price': current_price}
            
        except Exception as e:
            self.logger.error(f"监测价格变化失败: {e}")
            return {'detected': False, 'change': 'error'}
    
    def _analyze_price_change(self) -> Dict:
        """分析价格变化"""
        try:
            if len(self.price_history) < 3:
                return {'detected': True, 'change': 'insufficient_data'}
            
            # 获取最近三个价格点
            recent_prices = self.price_history[-3:]
            
            # 计算变化趋势
            price1, price2, price3 = recent_prices[0]['price'], recent_prices[1]['price'], recent_prices[2]['price']
            
            # 计算变化率
            change1 = (price2 - price1) / price1 * 100
            change2 = (price3 - price2) / price2 * 100
            
            # 判断趋势
            if change1 > 0.5 and change2 > 0.5:  # 连续上涨
                return {
                    'detected': True,
                    'change': 'rising',
                    'trend': 'up',
                    'current_price': price3,
                    'change_rate': change2
                }
            elif change1 < -0.5 and change2 < -0.5:  # 连续下跌
                return {
                    'detected': True,
                    'change': 'falling',
                    'trend': 'down',
                    'current_price': price3,
                    'change_rate': change2
                }
            else:
                return {
                    'detected': True,
                    'change': 'stable',
                    'trend': 'none',
                    'current_price': price3,
                    'change_rate': change2
                }
                
        except Exception as e:
            self.logger.error(f"分析价格变化失败: {e}")
            return {'detected': False, 'change': 'error'}
    
    def auto_order(self, signal_type: str, price: float, quantity: int = 1) -> bool:
        """自动下单"""
        try:
            current_time = time.time()
            
            # 检查交易冷却时间
            if current_time - self.last_trade_time < self.trade_cooldown:
                self.logger.info("交易冷却中，跳过下单")
                return False
            
            self.logger.info(f"开始自动下单: {signal_type} at {price}")
            
            # 激活客户端窗口
            if not self.find_client_window():
                self.logger.error("无法找到客户端窗口")
                return False
            
            # 根据信号类型执行不同的操作
            if signal_type == 'buy':
                success = self._execute_buy_order(price, quantity)
            elif signal_type == 'sell':
                success = self._execute_sell_order(price, quantity)
            else:
                self.logger.error(f"未知的信号类型: {signal_type}")
                return False
            
            if success:
                self.last_trade_time = current_time
                self.logger.info(f"自动下单成功: {signal_type}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"自动下单失败: {e}")
            return False
    
    def _execute_buy_order(self, price: float, quantity: int) -> bool:
        """执行买入订单"""
        try:
            # 点击买入按钮
            pyautogui.click(x=100, y=200)  # 买入按钮位置（需要根据实际界面调整）
            time.sleep(1)
            
            # 输入价格
            pyautogui.click(x=200, y=300)  # 价格输入框位置
            pyautogui.hotkey('ctrl', 'a')  # 全选
            pyautogui.typewrite(str(price))
            time.sleep(0.5)
            
            # 输入数量
            pyautogui.click(x=200, y=350)  # 数量输入框位置
            pyautogui.hotkey('ctrl', 'a')  # 全选
            pyautogui.typewrite(str(quantity))
            time.sleep(0.5)
            
            # 点击确认下单
            pyautogui.click(x=300, y=400)  # 确认按钮位置
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"执行买入订单失败: {e}")
            return False
    
    def _execute_sell_order(self, price: float, quantity: int) -> bool:
        """执行卖出订单"""
        try:
            # 点击卖出按钮
            pyautogui.click(x=100, y=250)  # 卖出按钮位置（需要根据实际界面调整）
            time.sleep(1)
            
            # 输入价格
            pyautogui.click(x=200, y=300)  # 价格输入框位置
            pyautogui.hotkey('ctrl', 'a')  # 全选
            pyautogui.typewrite(str(price))
            time.sleep(0.5)
            
            # 输入数量
            pyautogui.click(x=200, y=350)  # 数量输入框位置
            pyautogui.hotkey('ctrl', 'a')  # 全选
            pyautogui.typewrite(str(quantity))
            time.sleep(0.5)
            
            # 点击确认下单
            pyautogui.click(x=300, y=400)  # 确认按钮位置
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"执行卖出订单失败: {e}")
            return False
    
    def get_monitoring_status(self) -> Dict:
        """获取监测状态"""
        return {
            'client_running': self.is_client_running,
            'price_history_count': len(self.price_history),
            'line_history_count': len(self.yellow_line_history),
            'last_trade_time': self.last_trade_time,
            'trade_cooldown': self.trade_cooldown
        } 