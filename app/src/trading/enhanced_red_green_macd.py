#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略四（红绿线）+ 策略二（MACD趋势）完整结合实现
基于您现有的smart_trading.py，集成两种策略
"""

import time
import logging
import pyautogui
import cv2
import numpy as np
from typing import Dict, Optional, List, Tuple
import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QPushButton, QLabel, QTextEdit, QGroupBox, QMessageBox, QComboBox, QSlider
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
import json

# 导入您现有的smart_trading.py中的类
from smart_trading import SmartTradingEngine


class RedGreenLineStrategy:
    """策略四：红绿线策略"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def detect_red_green_lines(self, image: np.ndarray) -> Dict:
        """检测红绿线趋势"""
        try:
            if image is None:
                return {'signal': 'none', 'confidence': 0.0}

            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # 定义红色和绿色的HSV范围
            red_lower1 = np.array([0, 50, 50])
            red_upper1 = np.array([10, 255, 255])
            red_lower2 = np.array([170, 50, 50])
            red_upper2 = np.array([180, 255, 255])

            green_lower = np.array([35, 50, 50])
            green_upper = np.array([85, 255, 255])

            # 创建红色和绿色掩码
            red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
            red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
            red_mask = red_mask1 + red_mask2

            green_mask = cv2.inRange(hsv, green_lower, green_upper)

            # 计算红色和绿色像素数量
            red_pixels = cv2.countNonZero(red_mask)
            green_pixels = cv2.countNonZero(green_mask)

            # 计算总面积
            total_pixels = image.shape[0] * image.shape[1]

            # 计算比例
            red_ratio = red_pixels / total_pixels
            green_ratio = green_pixels / total_pixels

            # 判断趋势
            if red_ratio > 0.01 and red_ratio > green_ratio * 1.5:
                confidence = min(red_ratio * 10, 0.9)
                return {'signal': 'sell', 'confidence': confidence, 'red_ratio': red_ratio}
            elif green_ratio > 0.01 and green_ratio > red_ratio * 1.5:
                confidence = min(green_ratio * 10, 0.9)
                return {'signal': 'buy', 'confidence': confidence, 'green_ratio': green_ratio}
            else:
                return {'signal': 'none', 'confidence': 0.0}

        except Exception as e:
            self.logger.error(f"红绿线检测失败: {e}")
            return {'signal': 'none', 'confidence': 0.0}


class MACDTrendStrategy:
    """策略二：MACD趋势策略"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def detect_macd_trend(self, image: np.ndarray) -> Dict:
        """检测MACD趋势"""
        try:
            if image is None:
                return {'signal': 'none', 'confidence': 0.0}

            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # 检测绿色（正值）和红色（负值）
            green_lower = np.array([35, 50, 50])
            green_upper = np.array([85, 255, 255])

            red_lower1 = np.array([0, 50, 50])
            red_upper1 = np.array([10, 255, 255])
            red_lower2 = np.array([170, 50, 50])
            red_upper2 = np.array([180, 255, 255])

            green_mask = cv2.inRange(hsv, green_lower, green_upper)
            red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
            red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
            red_mask = red_mask1 + red_mask2

            green_pixels = cv2.countNonZero(green_mask)
            red_pixels = cv2.countNonZero(red_mask)

            total_pixels = image.shape[0] * image.shape[1]

            if green_pixels > red_pixels * 1.2:
                confidence = min(green_pixels / total_pixels * 20, 0.7)
                return {'signal': 'buy', 'confidence': confidence}
            elif red_pixels > green_pixels * 1.2:
                confidence = min(red_pixels / total_pixels * 20, 0.7)
                return {'signal': 'sell', 'confidence': confidence}
            else:
                return {'signal': 'none', 'confidence': 0.0}

        except Exception as e:
            self.logger.error(f"MACD趋势检测失败: {e}")
            return {'signal': 'none', 'confidence': 0.0}


class SignalFusion:
    """信号融合器"""

    def __init__(self, red_green_weight: float = 0.6, macd_weight: float = 0.4):
        self.red_green_weight = red_green_weight
        self.macd_weight = macd_weight
        self.logger = logging.getLogger(__name__)

    def fuse_signals(self, red_green_signal: Dict, macd_signal: Dict) -> Dict:
        """融合红绿线和MACD信号"""
        try:
            # 获取信号值
            red_green_value = self.signal_to_value(red_green_signal['signal'])
            macd_value = self.signal_to_value(macd_signal['signal'])

            # 获取置信度
            red_green_confidence = red_green_signal.get('confidence', 0.0)
            macd_confidence = macd_signal.get('confidence', 0.0)

            # 计算加权分数
            red_green_score = red_green_value * red_green_confidence * self.red_green_weight
            macd_score = macd_value * macd_confidence * self.macd_weight

            total_score = red_green_score + macd_score
            total_weight = self.red_green_weight + self.macd_weight

            # 计算综合置信度
            overall_confidence = abs(total_score) / total_weight

            # 判断交易信号
            if total_score > 0.4:  # 降低阈值，提高灵敏度
                action = 'buy'
            elif total_score < -0.4:
                action = 'sell'
            else:
                action = 'none'

            return {
                'action': action,
                'confidence': overall_confidence,
                'score': total_score,
                'details': {
                    'red_green': {
                        'signal': red_green_signal['signal'],
                        'confidence': red_green_confidence,
                        'weight': self.red_green_weight,
                        'score': red_green_score
                    },
                    'macd': {
                        'signal': macd_signal['signal'],
                        'confidence': macd_confidence,
                        'weight': self.macd_weight,
                        'score': macd_score
                    }
                }
            }

        except Exception as e:
            self.logger.error(f"信号融合失败: {e}")
            return {'action': 'none', 'confidence': 0.0}

    def signal_to_value(self, signal: str) -> float:
        """将信号转换为数值"""
        if signal == 'buy':
            return 1.0
        elif signal == 'sell':
            return -1.0
        else:
            return 0.0


class EnhancedTradingEngine(SmartTradingEngine):
    """增强版交易引擎 - 结合策略四和策略二"""

    def __init__(self, client_path: str = None):
        super().__init__(client_path)

        # 初始化策略
        self.red_green_strategy = RedGreenLineStrategy()
        self.macd_strategy = MACDTrendStrategy()
        self.signal_fusion = SignalFusion(red_green_weight=0.6, macd_weight=0.4)

        # 检测区域
        self.red_green_region = None
        self.macd_region = None

        # 策略权重（可调整）
        self.red_green_weight = 0.6
        self.macd_weight = 0.4

        # 信号历史
        self.signal_history = []

        self.logger.info("增强版交易引擎初始化完成")

    def calibrate_detection_regions(self):
        """校准检测区域"""
        try:
            if not self.find_client_window():
                return False

            # 根据窗口大小设置检测区域
            window_width = self.window_rect[2]
            window_height = self.window_rect[3]

            # 设置检测区域（可根据实际界面调整）
            self.red_green_region = (50, 100, 400, 200)
            self.macd_region = (50, 350, 400, 150)

            self.logger.info("检测区域校准完成")
            return True

        except Exception as e:
            self.logger.error(f"检测区域校准失败: {e}")
            return False

    def capture_screen_region(self, region: tuple) -> np.ndarray:
        """截取指定区域"""
        try:
            if self.window_rect is None:
                return None

            # 计算绝对坐标
            abs_x = self.window_rect[0] + region[0]
            abs_y = self.window_rect[1] + region[1]
            abs_width = region[2]
            abs_height = region[3]

            screenshot = pyautogui.screenshot(region=(abs_x, abs_y, abs_width, abs_height))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            self.logger.error(f"截取屏幕区域失败: {e}")
            return None

    def analyze_combined_signals(self) -> Dict:
        """分析组合信号"""
        try:
            if not self.find_client_window():
                return {'action': 'none', 'reason': '未找到客户端窗口'}

            # 1. 红绿线策略分析
            red_green_image = self.capture_screen_region(self.red_green_region)
            red_green_signal = self.red_green_strategy.detect_red_green_lines(red_green_image)

            # 2. MACD策略分析
            macd_image = self.capture_screen_region(self.macd_region)
            macd_signal = self.macd_strategy.detect_macd_trend(macd_image)

            # 3. 信号融合
            fused_signal = self.signal_fusion.fuse_signals(red_green_signal, macd_signal)

            # 4. 记录信号历史
            self.signal_history.append({
                'timestamp': time.time(),
                'red_green': red_green_signal,
                'macd': macd_signal,
                'fused': fused_signal
            })

            # 5. 限制历史记录长度
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]

            return fused_signal

        except Exception as e:
            self.logger.error(f"组合信号分析失败: {e}")
            return {'action': 'none', 'reason': f'分析失败: {e}'}

    def execute_enhanced_trade(self, signal: Dict):
        """执行增强版交易"""
        try:
            if signal['action'] == 'none':
                return

            action = signal['action']
            confidence = signal.get('confidence', 0.0)

            self.logger.info(f"执行增强版交易: {action}, 置信度: {confidence:.2f}")

            # 调用原有的交易执行函数
            if action == 'buy':
                self._execute_buy_order(price=1383, quantity=1)
            elif action == 'sell':
                self._execute_sell_order(price=1383, quantity=1)

        except Exception as e:
            self.logger.error(f"增强版交易执行失败: {e}")

    def run_enhanced_trading_loop(self):
        """运行增强版交易循环"""
        try:
            while self.is_running:
                # 分析组合信号
                signal = self.analyze_combined_signals()

                # 执行交易
                if signal['action'] != 'none':
                    self.execute_enhanced_trade(signal)

                # 等待下次检测
                time.sleep(5)  # 5秒检测间隔

        except Exception as e:
            self.logger.error(f"增强版交易循环失败: {e}")

    def get_signal_statistics(self) -> Dict:
        """获取信号统计信息"""
        try:
            if not self.signal_history:
                return {'total_signals': 0}

            total_signals = len(self.signal_history)
            buy_signals = sum(1 for s in self.signal_history if s['fused']['action'] == 'buy')
            sell_signals = sum(1 for s in self.signal_history if s['fused']['action'] == 'sell')
            none_signals = sum(1 for s in self.signal_history if s['fused']['action'] == 'none')

            return {
                'total_signals': total_signals,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'none_signals': none_signals,
                'buy_ratio': buy_signals / total_signals if total_signals > 0 else 0,
                'sell_ratio': sell_signals / total_signals if total_signals > 0 else 0,
                'none_ratio': none_signals / total_signals if total_signals > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"获取信号统计失败: {e}")
            return {'total_signals': 0}


class EnhancedTradingThread(QThread):
    """增强版交易线程"""
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    statistics_signal = pyqtSignal(dict)

    def __init__(self, trading_engine):
        super().__init__()
        self.trading_engine = trading_engine
        self.is_running = False

    def run(self):
        """运行增强版交易循环"""
        self.is_running = True
        try:
            while self.is_running:
                # 分析组合信号
                signal = self.trading_engine.analyze_combined_signals()

                # 发送日志
                self.log_signal.emit(f"组合信号分析: {signal}")

                # 执行交易
                if signal['action'] != 'none':
                    self.trading_engine.execute_enhanced_trade(signal)
                    self.log_signal.emit(f"执行交易: {signal['action']}")

                # 发送统计信息
                stats = self.trading_engine.get_signal_statistics()
                self.statistics_signal.emit(stats)

                # 等待下次检测
                time.sleep(5)

        except Exception as e:
            self.log_signal.emit(f"增强版交易线程错误: {e}")

    def stop(self):
        """停止线程"""
        self.is_running = False


class EnhancedTradingWindow(QMainWindow):
    """增强版交易系统GUI界面"""

    def __init__(self):
        super().__init__()
        self.trading_engine = EnhancedTradingEngine()
        self.trading_thread = None
        self.setup_logging()
        self.setup_ui()

    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("增强版交易系统 - 策略四+策略二")
        self.setGeometry(100, 100, 900, 700)

        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 控制按钮
        control_group = QGroupBox("系统控制")
        control_layout = QHBoxLayout()

        self.start_button = QPushButton("启动交易")
        self.start_button.clicked.connect(self.start_trading)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("停止交易")
        self.stop_button.clicked.connect(self.stop_trading)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # 策略配置
        strategy_group = QGroupBox("策略配置")
        strategy_layout = QVBoxLayout()

        # 权重调整
        weight_layout = QHBoxLayout()
        weight_layout.addWidget(QLabel("红绿线权重:"))

        self.red_green_slider = QSlider(Qt.Horizontal)
        self.red_green_slider.setRange(0, 100)
        self.red_green_slider.setValue(60)
        self.red_green_slider.valueChanged.connect(self.update_weights)
        weight_layout.addWidget(self.red_green_slider)

        self.red_green_label = QLabel("60%")
        weight_layout.addWidget(self.red_green_label)

        weight_layout.addWidget(QLabel("MACD权重:"))

        self.macd_slider = QSlider(Qt.Horizontal)
        self.macd_slider.setRange(0, 100)
        self.macd_slider.setValue(40)
        self.macd_slider.valueChanged.connect(self.update_weights)
        weight_layout.addWidget(self.macd_slider)

        self.macd_label = QLabel("40%")
        weight_layout.addWidget(self.macd_label)

        strategy_layout.addLayout(weight_layout)
        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)

        # 统计信息
        stats_group = QGroupBox("信号统计")
        stats_layout = QVBoxLayout()

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(100)
        stats_layout.addWidget(self.stats_text)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # 日志显示
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
