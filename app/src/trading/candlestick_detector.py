#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K线颜色检测器
用于实时检测K线颜色变化并生成交易信号
"""

import cv2
import numpy as np
import pyautogui
import time
import threading
import logging
import os
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass

@dataclass
class ColorBlock:
    """颜色块数据结构"""
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    area: float
    color_type: str
    confidence: float

class CandlestickColorDetector:
    """K线颜色检测器"""
    
    def __init__(self, trading_engine=None):
        self.logger = logging.getLogger(__name__)
        self.trading_engine = trading_engine
        
        # 监控状态
        self.is_monitoring = False
        self.monitoring_thread = None
        self.signal_callback = None
        
        # K线图区域配置 (相对坐标)
        self.chart_area = {
            'x': 0.05,      # 左边距 5%
            'y': 0.12,      # 上边距 12%
            'width': 0.65,  # 宽度 65%
            'height': 0.55  # 高度 55%
        }
        
        # 加载配置文件中的区域设置
        self._load_chart_area_config()
        
        # 颜色检测范围 (HSV)
        self.color_ranges = {
            'red': {
                'lower1': [0, 30, 30],    # 红色范围1 (0-15)
                'upper1': [15, 255, 255],
                'lower2': [160, 30, 30],  # 红色范围2 (160-180)
                'upper2': [180, 255, 255]
            },
            'blue': {
                'lower': [80, 50, 50],    # 蓝色范围 (80-110)
                'upper': [110, 255, 255]
            },
            'cyan': {
                'lower': [85, 100, 200],  # 青色范围 (专门针对#50ffff)
                'upper': [95, 255, 255]
            },
            'green': {
                'lower': [35, 30, 30],    # 绿色范围 (35-85)
                'upper': [85, 255, 255]
            }
        }
        
        # 检测参数
        self.min_candlestick_area = 20  # 最小K线面积
        self.detection_interval = 1.0   # 检测间隔（秒）
        
        # 信号控制
        self.last_signal_time = 0
        self.signal_cooldown = 1.0  # 信号冷却时间（秒）- 减少到1秒
        self.previous_color_counts = {'red': 0, 'blue': 0, 'cyan': 0, 'green': 0}  # 记录上次的颜色数量
        
        # 统计数据
        self.detection_stats = {
            'total_detections': 0,
            'red_detected': 0,
            'blue_detected': 0,
            'cyan_detected': 0,
            'green_detected': 0,
            'loop_count': 0,
            'last_signal': None,
            'last_signal_time': 0
        }
        
        print("=" * 60)
        print("✅ K线颜色检测器初始化完成 (新版本-检测新色块)")
        print("🎯 新版本特性: 检测新出现的色块触发交易")
        print(f"📊 初始状态: is_monitoring={self.is_monitoring}")
        print(f"📊 信号冷却: {self.signal_cooldown}秒")
        print(f"📊 检测间隔: {self.detection_interval}秒")
        print("=" * 60)
        self.logger.info("✅ K线颜色检测器初始化完成 (新版本-检测新色块)")
    
    def set_signal_callback(self, callback: Callable):
        """设置信号回调函数"""
        self.signal_callback = callback
    
    def get_chart_region(self, screenshot: np.ndarray) -> Optional[np.ndarray]:
        """获取K线图区域"""
        try:
            height, width = screenshot.shape[:2]
            
            # 计算绝对坐标
            x = int(width * self.chart_area['x'])
            y = int(height * self.chart_area['y'])
            w = int(width * self.chart_area['width'])
            h = int(height * self.chart_area['height'])
            
            # 边界检查
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = max(1, min(w, width - x))
            h = max(1, min(h, height - y))
            
            # 提取区域
            chart_region = screenshot[y:y+h, x:x+w]
            
            self.logger.debug(f"📊 K线区域: 屏幕({width}x{height}) → 区域({w}x{h}) at ({x},{y})")
            
            return chart_region
            
        except Exception as e:
            self.logger.error(f"❌ 获取K线区域失败: {e}")
            return None
    
    def detect_color_blocks(self, image: np.ndarray) -> Dict[str, List[ColorBlock]]:
        """检测图像中的颜色块"""
        try:
            if image is None or image.size == 0:
                return {}
            
            # 转换为HSV色彩空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            results = {}
            
            # 检测红色 (需要两个范围)
            red_mask1 = cv2.inRange(hsv, 
                                  np.array(self.color_ranges['red']['lower1']),
                                  np.array(self.color_ranges['red']['upper1']))
            red_mask2 = cv2.inRange(hsv,
                                  np.array(self.color_ranges['red']['lower2']),
                                  np.array(self.color_ranges['red']['upper2']))
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            results['red'] = self._extract_color_blocks(red_mask, 'red')
            
            # 检测蓝色
            blue_mask = cv2.inRange(hsv,
                                  np.array(self.color_ranges['blue']['lower']),
                                  np.array(self.color_ranges['blue']['upper']))
            results['blue'] = self._extract_color_blocks(blue_mask, 'blue')
            
            # 检测青色
            cyan_mask = cv2.inRange(hsv,
                                  np.array(self.color_ranges['cyan']['lower']),
                                  np.array(self.color_ranges['cyan']['upper']))
            cyan_blocks = self._extract_color_blocks(cyan_mask, 'cyan')
            results['cyan'] = cyan_blocks
            
            # 将青色块也加入蓝色类别（兼容性）
            results['blue'].extend([
                ColorBlock(block.bbox, block.area, 'cyan', block.confidence)
                for block in cyan_blocks
            ])
            
            # 检测绿色
            green_mask = cv2.inRange(hsv,
                                   np.array(self.color_ranges['green']['lower']),
                                   np.array(self.color_ranges['green']['upper']))
            results['green'] = self._extract_color_blocks(green_mask, 'green')
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 颜色检测失败: {e}")
            return {}
    
    def _extract_color_blocks(self, mask: np.ndarray, color_type: str) -> List[ColorBlock]:
        """从掩码中提取颜色块"""
        try:
            # 查找轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            color_blocks = []
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # 过滤太小的区域
                if area >= self.min_candlestick_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    confidence = min(area / 100.0, 1.0)  # 简单的置信度计算
                    
                    color_blocks.append(ColorBlock(
                        bbox=(x, y, w, h),
                        area=area,
                        color_type=color_type,
                        confidence=confidence
                    ))
            
            return color_blocks
            
        except Exception as e:
            self.logger.error(f"❌ 提取{color_type}颜色块失败: {e}")
            return []
    
    def monitor_candlesticks(self):
        """监控K线颜色变化"""
        print("🚀 K线监控线程已启动，开始监控...")
        self.logger.info("🚀 开始K线颜色监控...")
        
        try:
            while self.is_monitoring:
                try:
                    # 更新循环计数
                    self.detection_stats['loop_count'] += 1
                
                    # 获取屏幕截图
                    screenshot = pyautogui.screenshot()
                    screenshot_np = np.array(screenshot)
                    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
                    
                    # 提取K线区域
                    chart_region = self.get_chart_region(screenshot_bgr)
                    if chart_region is None:
                        self.logger.warning("⚠️ 无法获取K线区域")
                        time.sleep(self.detection_interval)
                        continue
                    
                    # 检测颜色
                    color_blocks = self.detect_color_blocks(chart_region)
                    
                    # 更新统计数据
                    red_count = len(color_blocks.get('red', []))
                    blue_count = len(color_blocks.get('blue', []))
                    cyan_count = len(color_blocks.get('cyan', []))
                    green_count = len(color_blocks.get('green', []))
                    
                    # 每次都更新统计，确保GUI能看到最新数据
                    self.detection_stats.update({
                        'red_detected': red_count,
                        'blue_detected': blue_count,
                        'cyan_detected': cyan_count,
                        'green_detected': green_count,
                        'total_detections': red_count + blue_count + cyan_count + green_count
                    })
                    
                    # 检测新出现的色块（符合"下一个色块完成出现后"的要求）
                    current_time = time.time()
                    
                    # 计算新增的色块数量
                    red_new = red_count - self.previous_color_counts['red']
                    blue_new = blue_count - self.previous_color_counts['blue']
                    cyan_new = cyan_count - self.previous_color_counts['cyan']
                    
                    # 只有当有新色块出现时才触发交易
                    has_new_blocks = (red_new > 0 or blue_new > 0 or cyan_new > 0)
                    
                    # 检查信号冷却时间
                    time_since_last_signal = current_time - self.last_signal_time
                    signal_ready = time_since_last_signal >= self.signal_cooldown
                    
                    # 添加调试日志（每次循环都输出详细信息）
                    if True:  # 临时改为每次都输出
                        debug_msg = f"🔍 K线状态检查 (循环{self.detection_stats['loop_count']}): 红={red_count}, 蓝={blue_count}, 青={cyan_count} | 新增: 红{red_new:+d}, 蓝{blue_new:+d}, 青{cyan_new:+d} | 新色块: {has_new_blocks}, 信号就绪: {signal_ready}, 冷却剩余: {max(0, self.signal_cooldown - time_since_last_signal):.1f}s"
                        print(debug_msg)
                        self.logger.info(debug_msg)
                    
                    if has_new_blocks and signal_ready:
                        # 强制输出到控制台和日志
                        print(f"🆕 检测到新的K线色块: 红{red_new:+d}, 蓝{blue_new:+d}, 青{cyan_new:+d}")
                        self.logger.info(f"🆕 检测到新的K线色块: 红{red_new:+d}, 蓝{blue_new:+d}, 青{cyan_new:+d}")
                        
                        # 根据新出现的色块颜色判断交易信号
                        signal = self._analyze_new_colors(red_new, blue_new, cyan_new)
                        if signal and signal != 'hold':
                            self.detection_stats['last_signal'] = signal
                            self.detection_stats['last_signal_time'] = current_time
                            self.last_signal_time = current_time
                            
                            if self.signal_callback:
                                # 构造符合要求的信号数据
                                signal_data = {
                                    'type': signal,
                                    'color': 'blue' if signal == 'sell' else 'red',
                                    'confidence': 0.8,  # 基础置信度
                                    'timestamp': current_time,
                                    'color_blocks': color_blocks,
                                    'current_colors': {
                                        'red_count': red_count,
                                        'blue_count': blue_count,
                                        'cyan_count': cyan_count
                                    }
                                }
                                
                                # 强化信号输出
                                signal_msg = f"🚨 K线交易信号触发！信号类型: {signal.upper()}, 基于颜色: {signal_data['color']}, 置信度: {signal_data['confidence']}"
                                print("=" * 80)
                                print(signal_msg)
                                print("=" * 80)
                                self.logger.info(signal_msg)
                                
                                # 调用信号回调
                                self.signal_callback(signal_data)
                                print(f"✅ 信号已传递给交易处理器")
                            else:
                                print("⚠️ 警告：检测到交易信号但没有设置回调函数！")
                                self.logger.warning("⚠️ 警告：检测到交易信号但没有设置回调函数！")
                    
                    # 更新上次的颜色计数
                    self.previous_color_counts.update({
                        'red': red_count,
                        'blue': blue_count,
                        'cyan': cyan_count,
                        'green': green_count
                    })
                    
                    time.sleep(self.detection_interval)
                
                except Exception as e:
                    print(f"❌ K线监控循环异常: {e}")
                    self.logger.error(f"❌ K线监控循环异常: {e}")
                    time.sleep(self.detection_interval)
        
        except Exception as e:
            print(f"❌ K线监控致命异常: {e}")
            self.logger.error(f"❌ K线监控致命异常: {e}")
            self.is_monitoring = False
        
        print("⏹️ K线颜色监控已停止")
        self.logger.info("⏹️ K线颜色监控已停止")
    
    def _analyze_trading_signal(self, color_blocks: Dict[str, List[ColorBlock]]) -> Optional[str]:
        """分析交易信号"""
        try:
            red_blocks = color_blocks.get('red', [])
            blue_blocks = color_blocks.get('blue', [])
            cyan_blocks = color_blocks.get('cyan', [])
            
            # 新出现的蓝色/青色K线 → 卖出信号
            if blue_blocks or cyan_blocks:
                self.logger.info("🔵 检测到蓝色/青色K线 → 卖出信号")
                return 'sell'
            
            # 新出现的红色K线 → 买入信号
            if red_blocks:
                self.logger.info("🔴 检测到红色K线 → 买入信号")
                return 'buy'
            
            return 'hold'
            
        except Exception as e:
            self.logger.error(f"❌ 交易信号分析失败: {e}")
            return None
    
    def _analyze_new_colors(self, red_new: int, blue_new: int, cyan_new: int) -> Optional[str]:
        """根据新出现的色块颜色分析交易信号"""
        try:
            # 根据新出现的色块颜色决定交易
            # 优先级：蓝色/青色（卖出） > 红色（买入）
            
            if blue_new > 0 or cyan_new > 0:
                msg = f"🔵 新的蓝色/青色K线出现 → 执行卖出 (新增蓝色={blue_new}, 新增青色={cyan_new})"
                print(msg)
                self.logger.info(msg)
                return 'sell'
            elif red_new > 0:
                msg = f"🔴 新的红色K线出现 → 执行买入 (新增红色={red_new})"
                print(msg)
                self.logger.info(msg)
                return 'buy'
            
            return 'hold'
            
        except Exception as e:
            self.logger.error(f"❌ 新色块信号分析失败: {e}")
            return None
    
    def start_monitoring(self) -> bool:
        """启动监控"""
        try:
            if self.is_monitoring:
                print("⚠️ K线监控已在运行")
                self.logger.warning("⚠️ K线监控已在运行")
                return True
            
            print("🚀 正在启动K线监控线程...")
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self.monitor_candlesticks, daemon=True)
            self.monitoring_thread.start()
            
            print("✅ K线监控线程已启动")
            self.logger.info("✅ K线监控已启动")
            return True
            
        except Exception as e:
            print(f"❌ 启动K线监控失败: {e}")
            self.logger.error(f"❌ 启动K线监控失败: {e}")
            self.is_monitoring = False
            return False
    
    def stop_monitoring(self):
        """停止监控"""
        try:
            if not self.is_monitoring:
                return
            
            self.is_monitoring = False
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=2.0)
            
            self.logger.info("✅ K线监控已停止")
            
        except Exception as e:
            self.logger.error(f"❌ 停止K线监控失败: {e}")
    
    def get_detection_stats(self) -> Dict:
        """获取检测统计数据"""
        return self.detection_stats.copy()
    
    def reset_stats(self):
        """重置统计数据"""
        self.detection_stats = {
            'total_detections': 0,
            'red_detected': 0,
            'blue_detected': 0,
            'cyan_detected': 0,
            'green_detected': 0,
            'loop_count': 0,
            'last_signal': None,
            'last_signal_time': 0
        }
        self.logger.info("📊 检测统计数据已重置")
    
    def update_chart_area(self, x: float, y: float, width: float, height: float):
        """更新K线图区域"""
        self.chart_area = {
            'x': x,
            'y': y,
            'width': width,
            'height': height
        }
        self.logger.info(f"📊 K线区域已更新: {self.chart_area}")
    
    def update_color_ranges(self, color_ranges: Dict):
        """更新颜色范围"""
        self.color_ranges.update(color_ranges)
        self.logger.info("🎨 颜色范围已更新")
    
    def _load_chart_area_config(self):
        """加载K线图区域配置"""
        try:
            import json
            import os
            
            # 构造配置文件路径
            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config'
            )
            config_file = os.path.join(config_dir, 'candlestick_area_config.json')
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新区域配置
                self.chart_area.update(config)
                self.logger.info(f"✅ 已加载K线区域配置: {self.chart_area}")
            else:
                self.logger.info("📄 K线区域配置文件不存在，使用默认配置")
                
        except Exception as e:
            self.logger.error(f"❌ 加载K线区域配置失败: {e}")
            self.logger.info("🔄 使用默认K线区域配置")
    
    def reload_config(self):
        """重新加载配置"""
        self.logger.info("🔄 重新加载K线配置...")
        self._load_chart_area_config()
        self.logger.info("✅ 配置重新加载完成")