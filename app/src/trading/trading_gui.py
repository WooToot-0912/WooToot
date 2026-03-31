#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易系统GUI界面模块
提供用户界面和交互功能
"""

import sys
import os
import logging
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QTextEdit, QPlainTextEdit, QGroupBox, QMessageBox, 
                            QStatusBar, QMenuBar, QAction, QSplitter, QTabWidget,
                            QProgressBar, QComboBox, QSpinBox, QCheckBox, QDialog)
from PyQt5.QtCore import QTimer, Qt, QSettings, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap
import json

# 新增：HTTP交易API登录入口
try:
    from core.trading_api import TradingAPI as HttpTradingAPI
    HTTP_API_AVAILABLE = True
except Exception:
    HTTP_API_AVAILABLE = False
    HttpTradingAPI = None

class LogRedirector:
    """重定向控制台输出到GUI"""
    def __init__(self, log_signal):
        self.log_signal = log_signal
        
    def write(self, text):
        if text.strip():  # 忽略空行
            self.log_signal.emit(text.strip())
            
    def flush(self):
        pass

# 修复导入路径 - 暂时简化导入以排除卡死问题
try:
    # 首先尝试相对导入
    from .trading_engine import SmartTradingEngine
    TRADING_ENGINE_AVAILABLE = True
except ImportError:
    try:
        # 然后尝试绝对导入
        from trading_engine import SmartTradingEngine
        TRADING_ENGINE_AVAILABLE = True
    except ImportError:
        # 最后尝试从src.trading导入
        import sys
        import os
        trading_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'trading')
        if trading_path not in sys.path:
            sys.path.append(trading_path)
        try:
            from trading_engine import SmartTradingEngine
            TRADING_ENGINE_AVAILABLE = True
        except ImportError:
            TRADING_ENGINE_AVAILABLE = False
            SmartTradingEngine = None

# 暂时禁用线程导入以排除卡死问题
TRADING_THREAD_AVAILABLE = False
TradingThread = None
AdvancedTradingThread = None

# 尝试导入K线识别模块
CANDLESTICK_DETECTION_AVAILABLE = False
CandlestickColorDetector = None
AutoCandlestickTrader = None

try:
    from .candlestick_detector import CandlestickColorDetector
    from .auto_candlestick_trader import AutoCandlestickTrader
    CANDLESTICK_DETECTION_AVAILABLE = True
    print("✅ K线识别模块导入成功")
except ImportError as e:
    print(f"⚠️ K线识别模块导入失败: {e}")
    CANDLESTICK_DETECTION_AVAILABLE = False
except Exception as e:
    print(f"❌ K线识别模块导入异常: {e}")
    CANDLESTICK_DETECTION_AVAILABLE = False


class SimpleTrading(QThread):
    """简化的交易线程 - 替代复杂的交易线程"""
    
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str, str)  # status_type, message
    
    def __init__(self, trading_engine, config=None, detection_mode=0, parent_window=None, angle_threshold=5):
        super().__init__()
        self.trading_engine = trading_engine
        self.config = config or {}
        self.detection_mode = detection_mode  # 检测模式索引
        self.parent_window = parent_window    # 主窗口引用
        self.angle_threshold = angle_threshold  # 角度阈值
        self.is_running = False
        self.last_fill_time = 0  # 上次自动填入价格的时间
        self.logger = logging.getLogger(__name__)
        
        # 初始化K线自动交易器
        self.candlestick_trader = None
        # 延迟初始化K线交易器，避免阻塞启动
        
        # 检测模式状态（从主窗口获取）
        self.yellow_line_enabled = getattr(parent_window, 'yellow_line_enabled', True)
        self.candlestick_enabled = getattr(parent_window, 'candlestick_enabled', False)
    
    def run(self):
        """运行简化的交易监测"""
        try:
            self.is_running = True
            self.log_signal.emit("🚀 启动高级交易监测模式...")
            
            # 设置交易引擎的角度阈值
            if hasattr(self.trading_engine, 'set_angle_threshold'):
                self.trading_engine.set_angle_threshold(self.angle_threshold)
                self.log_signal.emit(f"🎯 角度阈值已设置为: {self.angle_threshold}°")
            
            # 设置高级检测器的角度阈值
            if hasattr(self.trading_engine, 'advanced_line_detector') and self.trading_engine.advanced_line_detector:
                if hasattr(self.trading_engine.advanced_line_detector, 'set_angle_threshold'):
                    self.trading_engine.advanced_line_detector.set_angle_threshold(self.angle_threshold)
                    self.log_signal.emit(f"🎯 高级检测器角度阈值已设置为: {self.angle_threshold}°")
            
            # 初始化并启动K线自动交易（如果启用）
            if CANDLESTICK_DETECTION_AVAILABLE and self.candlestick_enabled:
                try:
                    self.log_signal.emit("🎯 K线识别功能已启用，将在监测循环中初始化...")
                    # 标记需要初始化K线交易器，但不在这里阻塞
                    self.need_init_candlestick = True
                        
                except Exception as e:
                    self.log_signal.emit(f"⚠️ K线功能启用失败: {e}")
                    self.candlestick_trader = None
            else:
                self.need_init_candlestick = False
                if not self.candlestick_enabled:
                    self.log_signal.emit("⏸️ K线识别功能已禁用")
            
            # 模拟交易监测循环
            monitor_interval = self.config.get('monitor_interval', 5)
            
            while self.is_running:
                try:
                    # 延迟初始化K线交易器（避免阻塞启动）
                    if hasattr(self, 'need_init_candlestick') and self.need_init_candlestick and not self.candlestick_trader:
                        try:
                            self.log_signal.emit("🎯 正在初始化K线自动交易器...")
                            
                            # 获取交易配置
                            trade_interval = getattr(self.parent_window, 'trade_interval_spinbox', None)
                            trade_quantity = getattr(self.parent_window, 'trade_quantity_spinbox', None)
                            
                            config = {
                                'auto_trading_enabled': True,
                                'default_quantity': trade_quantity.value() if trade_quantity else 1,
                                'min_trade_interval': trade_interval.value() if trade_interval else 30,
                                'max_trades_per_hour': 10,
                                'risk_management': True
                            }
                            
                            # 使用现有的交易引擎
                            self.candlestick_trader = AutoCandlestickTrader(config, self.trading_engine)
                            
                            self.log_signal.emit("✅ K线自动交易器初始化成功")
                            self.need_init_candlestick = False
                            
                            # 启动K线监控（非阻塞方式）
                            try:
                                # 正确启动K线检测器的监控线程
                                self.candlestick_trader.is_running = True
                                if self.candlestick_trader.candlestick_detector.start_monitoring():
                                    self.log_signal.emit("✅ K线监控已启动（检测器线程已启动）")
                                else:
                                    self.log_signal.emit("⚠️ K线监控启动失败")
                            except Exception as monitor_e:
                                self.log_signal.emit(f"⚠️ K线监控启动异常: {monitor_e}")
                                
                        except Exception as init_e:
                            self.log_signal.emit(f"⚠️ K线交易器初始化失败: {init_e}")
                            self.need_init_candlestick = False  # 避免重复尝试
                    
                    # 检测状态更新（动态获取主窗口状态）
                    if self.parent_window:
                        self.yellow_line_enabled = getattr(self.parent_window, 'yellow_line_enabled', True)
                        self.candlestick_enabled = getattr(self.parent_window, 'candlestick_enabled', False)
                    
                    # 1. 黄线变动检测（如果启用）
                    yellow_signal = None
                    trade_triggered = False
                    
                    if self.yellow_line_enabled:
                        self.log_signal.emit("🟡 开始黄线变动检测...")
                        
                        if self.trading_engine and hasattr(self.trading_engine, 'detect_yellow_line_change'):
                            try:
                                # 获取屏幕截图用于黄线检测
                                import pyautogui
                                import numpy as np
                                import cv2
                                
                                screenshot = pyautogui.screenshot()
                                screenshot_array = np.array(screenshot)
                                screen_bgr = cv2.cvtColor(screenshot_array, cv2.COLOR_RGB2BGR)
                                
                                # 使用用户选择的检测模式
                                detection_mode = self.detection_mode
                                
                                if detection_mode == 0:  # 高级检测-轮廓分析
                                    if hasattr(self.trading_engine, 'advanced_line_detector') and self.trading_engine.advanced_line_detector:
                                        line_segments = self.trading_engine.advanced_line_detector.detect_lines_contour_analysis(screen_bgr)
                                        yellow_signal = self._convert_line_segments_to_signal(line_segments, "轮廓分析")
                                    else:
                                        yellow_signal = {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'angle_change': 0.0, 'confidence': 0.0, 'area': 0}
                                elif detection_mode == 1:  # 高级检测-模板匹配
                                    if hasattr(self.trading_engine, 'advanced_line_detector') and self.trading_engine.advanced_line_detector:
                                        line_segments = self.trading_engine.advanced_line_detector.detect_lines_template_matching(screen_bgr)
                                        yellow_signal = self._convert_line_segments_to_signal(line_segments, "模板匹配")
                                    else:
                                        yellow_signal = {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'angle_change': 0.0, 'confidence': 0.0, 'area': 0}
                                elif detection_mode == 2:  # 高级检测-综合算法
                                    if hasattr(self.trading_engine, 'advanced_line_detector') and self.trading_engine.advanced_line_detector:
                                        yellow_signal = self.trading_engine.advanced_line_detector.detect_lines_advanced(screen_bgr)
                                    else:
                                        yellow_signal = {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'angle_change': 0.0, 'confidence': 0.0, 'area': 0}
                                else:
                                    # 默认使用轮廓分析
                                    if hasattr(self.trading_engine, 'advanced_line_detector') and self.trading_engine.advanced_line_detector:
                                        line_segments = self.trading_engine.advanced_line_detector.detect_lines_contour_analysis(screen_bgr)
                                        yellow_signal = self._convert_line_segments_to_signal(line_segments, "轮廓分析")
                                    else:
                                        yellow_signal = {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'angle_change': 0.0, 'confidence': 0.0, 'area': 0}
                                
                                if yellow_signal and yellow_signal.get('signal') in ['up', 'down']:
                                    # 检测到黄线变动信号！
                                    direction = yellow_signal.get('direction', 'unknown')
                                    angle = yellow_signal.get('angle', 0)
                                    angle_change = yellow_signal.get('angle_change', 0)
                                    
                                    self.log_signal.emit(f"🎯 检测到黄线变动信号！")
                                    self.log_signal.emit(f"   📊 方向: {direction}")
                                    self.log_signal.emit(f"   📐 角度: {angle:.2f}°")
                                    self.log_signal.emit(f"   📈 变化: {angle_change:.2f}°")
                                    
                                    trade_triggered = True
                                    
                                elif yellow_signal and yellow_signal.get('signal') == 'detected':
                                    self.log_signal.emit(f"🟡 检测到黄线但无明确方向 (角度: {yellow_signal.get('angle', 0):.1f}°)")
                                else:
                                    self.log_signal.emit(f"🟡 黄线状态: 稳定 (角度: {yellow_signal.get('angle', 0) if yellow_signal else 0:.1f}°)")
                                
                            except Exception as yellow_e:
                                self.log_signal.emit(f"❌ 黄线检测失败: {yellow_e}")
                        else:
                            self.log_signal.emit("❌ 黄线检测器不可用")
                    else:
                        self.log_signal.emit("⏸️ 黄线检测已禁用")
                    
                    # 2. 如果检测到黄线变动，立即获取价格并执行交易
                    if trade_triggered:
                        self.log_signal.emit("🚀 黄线变动触发，开始获取价格...")
                        
                        # 获取真实价格
                        price = None
                        if self.trading_engine:
                            try:
                                # 优先使用增强版价格检测器
                                if hasattr(self.trading_engine, 'real_price_detector') and self.trading_engine.real_price_detector:
                                    self.log_signal.emit("🔧 使用增强版价格检测器")
                                    
                                    # 尝试增强版检测方法
                                    if hasattr(self.trading_engine.real_price_detector, 'get_price_enhanced_fallback'):
                                        price = self.trading_engine.real_price_detector.get_price_enhanced_fallback(debug=True)
                                    else:
                                        price = self.trading_engine.real_price_detector.get_price_with_fallback()
                                        
                                elif hasattr(self.trading_engine, 'get_current_price_from_display'):
                                    self.log_signal.emit("🔧 使用备用价格检测方法")
                                    price = self.trading_engine.get_current_price_from_display(None)
                                
                                if price and isinstance(price, (int, float)) and price > 0:
                                    self.log_signal.emit(f"💰 获取到交易价格: {price:.1f}")
                                    
                                    # 立即自动填入价格和数量
                                    try:
                                        if hasattr(self.trading_engine, 'auto_fill_price'):
                                            self.log_signal.emit("🔧 自动填入价格...")
                                            success = self.trading_engine.auto_fill_price()
                                            if success:
                                                self.log_signal.emit("✅ 价格已自动填入")
                                                
                                                # 自动填入数量
                                                quantity_success = self.trading_engine.auto_fill_quantity(quantity=1)
                                                if quantity_success:
                                                    self.log_signal.emit("✅ 数量已自动填入: 1")
                                                    
                                                    # 执行交易决策
                                                    if hasattr(self.trading_engine, 'analyze_trade_signal'):
                                                        trade_signal = self.trading_engine.analyze_trade_signal(yellow_signal, None, None)
                                                        
                                                        if trade_signal.get('should_trade', False):
                                                            self.log_signal.emit(f"🎯 执行交易: {trade_signal['reason']}")
                                                            
                                                            # 执行交易
                                                            success = self.trading_engine.execute_trade(trade_signal)
                                                            if success:
                                                                self.log_signal.emit("✅ 自动交易执行成功！")
                                                            else:
                                                                self.log_signal.emit("❌ 自动交易执行失败")
                                                        else:
                                                            self.log_signal.emit(f"📊 交易分析结果: {trade_signal.get('reason', '无交易')}")
                                                else:
                                                    self.log_signal.emit("⚠️ 数量自动填入失败")
                                            else:
                                                self.log_signal.emit("⚠️ 价格自动填入失败")
                                    except Exception as fill_e:
                                        self.log_signal.emit(f"❌ 自动填入失败: {fill_e}")
                                else:
                                    self.log_signal.emit("⚠️ 未能获取到有效交易价格")
                            except Exception as e:
                                self.log_signal.emit(f"❌ 交易价格获取失败: {e}")
                        else:
                            self.log_signal.emit("❌ 交易引擎不可用")
                    
                    # 3. 如果没有交易信号，进行常规监测（降低频率）
                    else:
                        # 定期获取价格用于监测（不频繁）
                        import time
                        current_time = time.time()
                        if current_time - self.last_fill_time >= 10:  # 每10秒更新一次价格显示
                            price = None
                            if self.trading_engine and hasattr(self.trading_engine, 'real_price_detector') and self.trading_engine.real_price_detector:
                                try:
                                    # 使用增强版价格检测
                                    if hasattr(self.trading_engine.real_price_detector, 'get_price_enhanced_fallback'):
                                        price = self.trading_engine.real_price_detector.get_price_enhanced_fallback(debug=False)
                                    else:
                                        price = self.trading_engine.real_price_detector.get_price_with_fallback()
                                        
                                    if price and isinstance(price, (int, float)) and price > 0:
                                        self.log_signal.emit(f"📊 当前价格: {price:.1f}")
                                    else:
                                        self.log_signal.emit("📊 价格监测: 未获取到有效价格")
                                except Exception as e:
                                    self.log_signal.emit(f"📊 价格监测失败: {e}")
                            
                            self.last_fill_time = current_time
                        price = None
                    
                    # 真实信号检测和交易决策（如果黄线检测启用）
                    if self.yellow_line_enabled:
                        try:
                            # 获取屏幕截图用于信号检测
                            import pyautogui
                            import numpy as np
                            import cv2
                            screenshot = pyautogui.screenshot()
                            screen_array = np.array(screenshot)
                            # 转换RGB到BGR格式（OpenCV需要BGR）
                            screen_bgr = cv2.cvtColor(screen_array, cv2.COLOR_RGB2BGR)
                            
                            # 检测黄线信号（根据用户选择的模式）
                            yellow_signal = {}
                            detection_mode = self.detection_mode
                        
                            # 获取模式名称
                            mode_names = [
                                "高级检测-轮廓分析 (advanced_line_detector)", 
                                "高级检测-模板匹配 (advanced_line_detector)",
                                "高级检测-综合算法 (advanced_line_detector)"
                            ]
                            mode_name = mode_names[detection_mode] if 0 <= detection_mode < len(mode_names) else "未知模式"
                            
                            self.log_signal.emit(f"🔍 使用检测模式: {mode_name}")
                            
                            try:
                                if detection_mode == 0:  # 高级检测-轮廓分析
                                    if hasattr(self.trading_engine, 'advanced_line_detector') and self.trading_engine.advanced_line_detector:
                                        line_segments = self.trading_engine.advanced_line_detector.detect_lines_contour_analysis(screen_bgr)
                                        yellow_signal = self._convert_line_segments_to_signal(line_segments, "轮廓分析")
                                        
                                elif detection_mode == 1:  # 高级检测-模板匹配
                                    if hasattr(self.trading_engine, 'advanced_line_detector') and self.trading_engine.advanced_line_detector:
                                        line_segments = self.trading_engine.advanced_line_detector.detect_lines_template_matching(screen_bgr)
                                        yellow_signal = self._convert_line_segments_to_signal(line_segments, "模板匹配")
                                        
                                elif detection_mode == 2:  # 高级检测-综合算法
                                    if hasattr(self.trading_engine, 'advanced_line_detector') and self.trading_engine.advanced_line_detector:
                                        yellow_signal = self.trading_engine.advanced_line_detector.detect_lines_advanced(screen_bgr)
                                
                                # 如果检测失败，使用默认值
                                if not yellow_signal:
                                    yellow_signal = {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'angle_change': 0.0, 'confidence': 0.0, 'area': 0}
                                    
                            except Exception as detection_e:
                                self.log_signal.emit(f"❌ {mode_name} 检测失败: {detection_e}")
                                yellow_signal = {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'angle_change': 0.0, 'confidence': 0.0, 'area': 0}
                            
                            signal_type = yellow_signal.get('signal', 'none')
                            angle_change = yellow_signal.get('angle_change', 0.0)
                            direction = yellow_signal.get('direction', 'stable')
                            confidence = yellow_signal.get('confidence', 0.0)
                            area = yellow_signal.get('area', 0)
                            angle = yellow_signal.get('angle', 0)
                            
                            # 详细输出检测信息
                            if signal_type != 'none':
                                self.log_signal.emit(f"🔍 黄线检测详情: 信号={signal_type}, 方向={direction}, 面积={area:.1f}, 置信度={confidence:.2f}")
                                self.log_signal.emit(f"📐 角度详情: 当前={angle:.2f}°, 变化={angle_change:.2f}°")
                            
                            if signal_type == 'none':
                                self.log_signal.emit(f"🟡 黄线监测: detected {direction} 角度{angle_change:.1f}° (<{self.angle_threshold}° - 不满足阈值)")
                            else:
                                if abs(angle_change) > self.angle_threshold:
                                    action_desc = '买入' if signal_type == 'up' else '卖出'
                                    self.log_signal.emit(f"🟡 黄线监测: {signal_type} {direction} 角度{angle_change:.1f}° (>{self.angle_threshold}° - 将触发{action_desc})")
                                else:
                                    self.log_signal.emit(f"🟡 黄线监测: {signal_type} {direction} 角度{angle_change:.1f}° (<{self.angle_threshold}° - 不满足阈值)")
                            
                            # 检测货值变化
                            value_change_info = {}
                            if hasattr(self.trading_engine, 'monitor_realtime_value_change'):
                                value_change = self.trading_engine.monitor_realtime_value_change(screen_array)
                                if value_change.get('detected', False):
                                    change_rate = value_change.get('change_rate', 0.0)
                                    value_change_info = value_change
                                    self.log_signal.emit(f"📊 货值变化: {change_rate:+.2f}%")
                                    
                                    # 特别提示：检查是否达到交易条件
                                    if change_rate >= 1.0:
                                        self.log_signal.emit(f"🚨 检测到止盈条件: {change_rate:+.2f}% ≥ 1.0%")
                                    elif change_rate <= -3.0:
                                        self.log_signal.emit(f"🚨 检测到止损条件: {change_rate:+.2f}% ≤ -3.0%")
                                else:
                                    self.log_signal.emit("📊 货值变化: 无检测")
                            else:
                                self.log_signal.emit("📊 货值变化: 检测器不可用")
                            
                            # 执行交易决策
                            if hasattr(self.trading_engine, 'analyze_trade_signal') and (yellow_signal or value_change_info):
                                trade_signal = self.trading_engine.analyze_trade_signal(
                                    yellow_signal, None, value_change_info
                                )
                                
                                if trade_signal.get('should_trade', False):
                                    self.log_signal.emit(f"🎯 触发交易信号: {trade_signal['reason']}")
                                    
                                    # 执行交易
                                    success = self.trading_engine.execute_trade(trade_signal)
                                    if success:
                                        self.log_signal.emit("✅ 自动交易执行成功")
                                    else:
                                        self.log_signal.emit("❌ 自动交易执行失败")
                                else:
                                    self.log_signal.emit(f"📊 无交易信号: {trade_signal.get('reason', '未知')}")
                        
                        except Exception as signal_e:
                            self.log_signal.emit(f"⚠️ 信号检测失败: {signal_e}")
                            # 如果信号检测失败，至少显示基础状态
                            self.log_signal.emit("🟡 黄线监测: 检测器错误")
                            self.log_signal.emit("📊 货值变化: 检测器错误")
                    else:
                        # 黄线检测已禁用，检查是否启用K线检测
                        if self.candlestick_enabled and self.candlestick_trader:
                            try:
                                # 确保K线监控正在运行
                                if hasattr(self.candlestick_trader, 'candlestick_detector') and self.candlestick_trader.candlestick_detector:
                                    detector = self.candlestick_trader.candlestick_detector
                                    
                                    # 如果监控未启动，启动它
                                    if not detector.is_monitoring:
                                        self.log_signal.emit("🚀 启动K线颜色监控...")
                                        if detector.start_monitoring():
                                            self.log_signal.emit("✅ K线颜色监控已启动")
                                        else:
                                            self.log_signal.emit("❌ K线颜色监控启动失败")
                                    else:
                                        # 显示监控状态
                                        stats = detector.get_detection_stats()
                                        total_detections = stats.get('total_detections', 0)
                                        red_detected = stats.get('red_detected', 0)
                                        blue_detected = stats.get('blue_detected', 0)
                                        cyan_detected = stats.get('cyan_detected', 0)
                                        loop_count = stats.get('loop_count', 0)
                                        
                                        self.log_signal.emit(f"🔵 K线监控运行中 - Total: {total_detections}, Red: {red_detected}, Blue: {blue_detected}, Cyan: {cyan_detected}, 循环: {loop_count}")
                                
                                # 获取基础价格显示
                                if self.trading_engine and hasattr(self.trading_engine, 'real_price_detector') and self.trading_engine.real_price_detector:
                                    try:
                                        price = self.trading_engine.real_price_detector.get_price_enhanced_fallback(debug=False)
                                        if price and isinstance(price, (int, float)) and price > 0:
                                            self.log_signal.emit(f"📊 当前价格: {price:.1f}")
                                    except Exception as price_e:
                                        self.log_signal.emit(f"📊 价格获取失败: {price_e}")
                                        
                            except Exception as k_e:
                                self.log_signal.emit(f"❌ K线检测失败: {k_e}")
                        else:
                            # 两种检测都禁用，仅做基础监控
                            self.log_signal.emit("⏸️ 所有检测已禁用，仅做基础监控")
                    
                    # 状态更新
                    price_str = f"{price:.1f}" if price is not None else "N/A"
                    self.status_signal.emit("price", price_str)
                    self.status_signal.emit("status", "运行中")
                    
                    # 等待下一次检测
                    self.msleep(monitor_interval * 1000)
                    
                except Exception as e:
                    self.log_signal.emit(f"⚠️ 监测循环出错: {e}")
                    self.msleep(5000)  # 出错后等待5秒
            
            self.log_signal.emit("⏹️ 交易监测已停止")
            
        except Exception as e:
            self.log_signal.emit(f"❌ 交易监测失败: {e}")
    
    def stop(self):
        """停止交易监测"""
        self.is_running = False
        self.log_signal.emit("⏹️ 正在停止交易监测...")
        
        # 停止K线自动交易
        if self.candlestick_trader:
            try:
                self.candlestick_trader.stop_auto_trading()
                self.log_signal.emit("✅ K线自动交易已停止")
            except Exception as e:
                self.log_signal.emit(f"⚠️ 停止K线自动交易时出错: {e}")
    
    def _convert_line_segments_to_signal(self, line_segments, method_name):
        """将线段列表转换为标准信号格式"""
        try:
            if not line_segments or len(line_segments) == 0:
                self.log_signal.emit(f"⚠️ {method_name}: 未检测到线条")
                return {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'angle_change': 0.0, 'confidence': 0.0, 'area': 0}
            
            # 选择置信度最高的线条
            best_line = max(line_segments, key=lambda x: x.confidence)
            
            self.log_signal.emit(f"✅ {method_name}: 检测到{len(line_segments)}条线，最佳线条角度={best_line.angle:.1f}°, 置信度={best_line.confidence:.2f}")
            
            # 简化的角度变化计算（实际应该有历史数据对比）
            angle_change = best_line.angle  # 简化处理
            
            # 根据角度判断信号（使用可调节的角度阈值）
            signal = 'none'
            direction = 'stable'
            
            if abs(best_line.angle) > self.angle_threshold:  # 使用可调节的角度阈值
                if best_line.angle > 0:
                    signal = 'up'
                    direction = 'rising'
                else:
                    signal = 'down'
                    direction = 'falling'
            
            return {
                'signal': signal,
                'direction': direction,
                'angle': best_line.angle,
                'angle_change': angle_change,
                'confidence': best_line.confidence,
                'area': best_line.length * 2,  # 近似面积
                'line_count': len(line_segments),
                'angle_threshold': self.angle_threshold  # 包含当前使用的阈值信息
            }
            
        except Exception as e:
            self.log_signal.emit(f"❌ {method_name}: 格式转换失败: {e}")
            return {'signal': 'none', 'direction': 'stable', 'angle': 0.0, 'angle_change': 0.0, 'confidence': 0.0, 'area': 0}

    def get_thread_status(self):
        """获取线程状态信息"""
        return {
            "线程状态": "运行中" if self.is_running else "已停止",
            "监测模式": "简化模式",
            "监测间隔": f"{self.config.get('monitor_interval', 5)}秒",
            "调试模式": "开启" if self.config.get('debug_mode', False) else "关闭",
            "自动截图": "开启" if self.config.get('auto_screenshot', False) else "关闭"
        }


class InitializationThread(QThread):
    """初始化线程，避免阻塞GUI主线程"""

    # 信号定义
    log_signal = pyqtSignal(str)
    engine_ready_signal = pyqtSignal(object)
    progress_signal = pyqtSignal(str, int)  # 消息, 进度百分比

    def __init__(self, config=None):
        super().__init__()
        self.config = config
        self.trading_engine = None

    def run(self):
        """在后台线程中初始化交易引擎"""
        try:
            if not TRADING_ENGINE_AVAILABLE:
                self.log_signal.emit("❌ 交易引擎模块不可用")
                self.engine_ready_signal.emit(None)
                return

            self.progress_signal.emit("正在创建交易引擎...", 20)
            self.log_signal.emit("🔧 后台初始化交易引擎...")

            # 创建交易引擎
            self.trading_engine = SmartTradingEngine(config=self.config)
            self.progress_signal.emit("交易引擎基础初始化完成", 50)
            self.log_signal.emit("✅ 交易引擎基础初始化完成")

            # 延迟初始化组件（安全调用）
            self.progress_signal.emit("正在初始化检测器...", 70)
            self.log_signal.emit("🔧 正在初始化检测器...")

            try:
                if hasattr(self.trading_engine, 'delayed_init_components'):
                    # 传递日志回调函数，让检测器初始化日志也显示在GUI中
                    self.trading_engine.delayed_init_components(log_callback=self.log_signal.emit)
                    self.progress_signal.emit("检测器初始化完成", 90)
                    self.log_signal.emit("✅ 检测器初始化完成")
                else:
                    self.progress_signal.emit("跳过延迟初始化", 90)
                    self.log_signal.emit("⚠️ 跳过延迟初始化（方法不存在）")
            except Exception as delayed_e:
                self.log_signal.emit(f"⚠️ 延迟初始化失败（继续运行）: {delayed_e}")
                self.progress_signal.emit("延迟初始化失败", 90)

            # 发送完成信号
            self.progress_signal.emit("初始化完成", 100)
            self.log_signal.emit("🎉 交易引擎初始化成功")
            self.engine_ready_signal.emit(self.trading_engine)

        except Exception as e:
            self.log_signal.emit(f"❌ 后台初始化失败: {e}")
            import traceback
            self.log_signal.emit(f"详细错误: {traceback.format_exc()}")
            self.engine_ready_signal.emit(None)


class SmartTradingWindow(QMainWindow):
    """智能交易系统主窗口"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # 初始化组件
        self.trading_engine = None
        self.trading_thread = None
        self.init_thread = None
        self.settings = QSettings('SmartTrading', 'TradingSystem')
        self.connection_manager = None  # 客户端连接管理器
        
        # 检测功能状态
        self.yellow_line_enabled = True  # 默认启用黄线检测
        self.candlestick_enabled = False
        
        # 加载配置文件
        self.config = self.load_config()

        # 初始化UI
        self.init_ui()

        # 加载设置
        self.load_settings()
        
        # 设置日志重定向到GUI（在UI初始化完成后）
        self.setup_log_redirection()

        # 启动后台初始化线程
        self.start_background_initialization()

        # 状态定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # 每秒更新状态

        self.logger.info("智能交易窗口初始化完成")
    
    def setup_log_redirection(self):
        """设置日志重定向，将控制台输出显示到GUI"""
        try:
            # 检查GUI组件是否已经创建
            if not hasattr(self, 'log_text') or self.log_text is None:
                print("⚠️ GUI组件还未创建完成，跳过日志重定向")
                return
                
            # 创建一个简单的重定向器，直接调用方法而不是信号
            class SimpleLogRedirector:
                def __init__(self, log_method):
                    self.log_method = log_method
                    
                def write(self, text):
                    if text.strip():  # 忽略空行
                        self.log_method(text.strip())
                        
                def flush(self):
                    pass
                
            # 重定向标准输出和标准错误到GUI
            self.stdout_redirector = SimpleLogRedirector(self.log_to_gui)
            self.stderr_redirector = SimpleLogRedirector(self.log_to_gui)
            
            # 保存原始的stdout和stderr
            self.original_stdout = sys.stdout
            self.original_stderr = sys.stderr
            
            # 重定向
            sys.stdout = self.stdout_redirector
            sys.stderr = self.stderr_redirector
            
            # 设置root logger的handler也输出到GUI
            root_logger = logging.getLogger()
            gui_handler = logging.StreamHandler(self.stdout_redirector)
            gui_handler.setFormatter(logging.Formatter('%(message)s'))
            root_logger.addHandler(gui_handler)
            
            self.log_to_gui("✅ 日志重定向设置完成，控制台输出将显示在此界面")
        except Exception as e:
            print(f"❌ 日志重定向设置失败: {e}")
            # 不要在这里使用logger，可能会导致循环调用
    
    def log_to_gui(self, message):
        """将消息显示到GUI日志区域"""
        try:
            if hasattr(self, 'log_text') and self.log_text is not None:
                # 添加时间戳
                timestamp = time.strftime('%H:%M:%S')
                formatted_message = f"[{timestamp}] {message}"
                self.log_text.append(formatted_message)
                # 自动滚动到底部
                cursor = self.log_text.textCursor()
                cursor.movePosition(cursor.End)
                self.log_text.setTextCursor(cursor)
        except Exception as e:
            # 如果GUI日志失败，回退到原始输出
            pass
    
    def load_config(self):
        """加载配置文件"""
        try:
            import os
            import json
            
            # 查找配置文件
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_paths = [
                os.path.join(current_dir, '../../config/trading_config.json'),
                os.path.join(current_dir, '../../../config/trading_config.json'),
                os.path.join(current_dir, 'config/trading_config.json'),
                'config/trading_config.json'
            ]
            
            for config_path in config_paths:
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        self.logger.info(f"✅ 配置文件加载成功: {config_path}")
                        return config
            
            # 如果找不到配置文件，返回默认配置
            self.logger.warning("⚠️ 未找到配置文件，使用默认配置")
            return {
                'auto_fill': {'enabled': True, 'fill_interval': 10},
                'auto_trading': {
                    'enabled': True,
                    'profit_threshold': 1.0,
                    'loss_threshold': -3.0,
                    'trade_cooldown': 30
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ 配置文件加载失败: {e}")
            return {'auto_fill': {'enabled': True}, 'auto_trading': {'enabled': True}}

    def start_background_initialization(self):
        """启动后台初始化线程"""
        try:
            # 创建简单配置对象
            class SimpleConfig:
                def get(self, key, default=None):
                    config_map = {
                        'price_detection.use_manual_price_selection': True,  # 启用手动区域选择
                        'trading.angle_threshold': 20,  # 默认20度阈值
                        'trading.default_quantity': 1,
                        'trading.check_interval': 5
                    }
                    return config_map.get(key, default)

            config = SimpleConfig()

            # 创建并启动初始化线程
            self.init_thread = InitializationThread(config=config)
            self.init_thread.log_signal.connect(self.log_text.appendPlainText)
            self.init_thread.engine_ready_signal.connect(self.on_engine_ready)
            self.init_thread.progress_signal.connect(self.on_init_progress)

            self.log_text.appendPlainText("🚀 启动后台初始化线程...")
            self.init_thread.start()

        except Exception as e:
            self.log_text.appendPlainText(f"❌ 启动后台初始化失败: {e}")
            self.logger.error(f"启动后台初始化失败: {e}")

    def on_init_progress(self, message, progress):
        """初始化进度回调"""
        self.status_label.setText(f"{message} ({progress}%)")

    def on_engine_ready(self, engine):
        """交易引擎准备就绪回调"""
        if engine:
            self.trading_engine = engine
            self.log_text.appendPlainText("🎉 交易引擎已准备就绪，可以开始交易")
            self.status_label.setText("就绪")

            # 初始化连接管理器
            self._initialize_connection_manager()

            # 启用交易按钮
            self.start_button.setEnabled(True)
        else:
            self.log_text.appendPlainText("❌ 交易引擎初始化失败")
            self.status_label.setText("初始化失败")
    
    def _initialize_connection_manager(self):
        """初始化客户端连接管理器"""
        try:
            from .client_connection_manager import ClientConnectionManager
            
            # 创建配置管理器（简化版）
            config_manager = None
            if hasattr(self, 'config'):
                config_manager = self.config
            
            self.connection_manager = ClientConnectionManager(
                trading_engine=self.trading_engine,
                config_manager=config_manager
            )
            
            # 加载保存的登录凭据
            self.connection_manager.load_login_credentials()
            
            self.log_text.appendPlainText("✅ 客户端连接管理器初始化成功")
            
        except Exception as e:
            self.log_text.appendPlainText(f"⚠️ 客户端连接管理器初始化失败: {e}")
            self.logger.warning(f"连接管理器初始化失败: {e}")
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("景陶易购智能交易系统 v2.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置应用图标（如果有的话）
        try:
            self.setWindowIcon(QIcon('assets/icon.png'))
        except:
            pass
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        # 右侧信息面板
        info_panel = self.create_info_panel()
        splitter.addWidget(info_panel)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 应用样式
        self.apply_styles()
    
    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 系统控制组
        control_group = QGroupBox("🚀 系统控制")
        control_layout = QVBoxLayout(control_group)
        
        # 主要控制按钮
        self.start_button = QPushButton("启动智能交易")
        self.start_button.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.start_button.setMinimumHeight(50)
        self.start_button.setEnabled(False)  # 初始时禁用，等待初始化完成
        self.start_button.clicked.connect(self.start_trading)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止交易")
        self.stop_button.setFont(QFont("Microsoft YaHei", 12))
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_trading)
        control_layout.addWidget(self.stop_button)
        
        # 测试按钮
        button_layout = QHBoxLayout()
        
        self.test_coords_button = QPushButton("测试坐标")
        self.test_coords_button.clicked.connect(self.test_coordinates)
        button_layout.addWidget(self.test_coords_button)
        
        self.test_detection_button = QPushButton("测试检测")
        self.test_detection_button.clicked.connect(self.test_detection)
        button_layout.addWidget(self.test_detection_button)
        
        # 坐标校准按钮
        self.calibrate_button = QPushButton("坐标校准")
        self.calibrate_button.clicked.connect(self.open_coordinate_calibrator)
        self.calibrate_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        button_layout.addWidget(self.calibrate_button)
        
        control_layout.addLayout(button_layout)
        
        layout.addWidget(control_group)
        
        # 配置组
        config_group = QGroupBox("⚙️ 配置设置")
        config_layout = QVBoxLayout(config_group)
        
        # 监测间隔设置
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("监测间隔(秒):"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 60)
        self.interval_spinbox.setValue(5)
        interval_layout.addWidget(self.interval_spinbox)
        config_layout.addLayout(interval_layout)
        
        # 调试模式
        self.debug_checkbox = QCheckBox("调试模式")
        config_layout.addWidget(self.debug_checkbox)
        
        # 自动截图
        self.screenshot_checkbox = QCheckBox("自动截图")
        self.screenshot_checkbox.setChecked(True)
        config_layout.addWidget(self.screenshot_checkbox)
        
        # 高级模式
        self.advanced_checkbox = QCheckBox("高级监测模式")
        config_layout.addWidget(self.advanced_checkbox)
        
        # 检测模式控制
        detection_control_group = QGroupBox("🎯 检测模式控制")
        detection_control_layout = QVBoxLayout(detection_control_group)
        
        # 黄线检测开关
        self.yellow_line_checkbox = QCheckBox("黄线变动检测")
        self.yellow_line_checkbox.setChecked(True)  # 默认启用
        self.yellow_line_checkbox.setToolTip("启用传统的黄线角度变化检测\n基于黄线角度变化进行买入/卖出")
        self.yellow_line_checkbox.setStyleSheet("QCheckBox { color: #FFC107; font-weight: bold; }")
        self.yellow_line_checkbox.stateChanged.connect(self.on_yellow_line_mode_changed)
        detection_control_layout.addWidget(self.yellow_line_checkbox)
        
        # K线识别模式
        if CANDLESTICK_DETECTION_AVAILABLE:
            self.candlestick_checkbox = QCheckBox("K线颜色识别交易")
            self.candlestick_checkbox.setToolTip("启用基于K线颜色的自动交易\n蓝色K线→卖出，红色K线→买入")
            self.candlestick_checkbox.setStyleSheet("QCheckBox { color: #2196F3; font-weight: bold; }")
            self.candlestick_checkbox.stateChanged.connect(self.on_candlestick_mode_changed)
            detection_control_layout.addWidget(self.candlestick_checkbox)
        else:
            self.candlestick_checkbox = None
        
        config_layout.addWidget(detection_control_group)
        
        # K线交易配置组
        if CANDLESTICK_DETECTION_AVAILABLE:
            candlestick_config_group = QGroupBox("⚙️ K线交易配置")
            candlestick_config_layout = QVBoxLayout(candlestick_config_group)
            
            # 交易间隔
            trade_interval_layout = QHBoxLayout()
            trade_interval_layout.addWidget(QLabel("交易间隔(秒):"))
            self.trade_interval_spinbox = QSpinBox()
            self.trade_interval_spinbox.setRange(10, 300)
            self.trade_interval_spinbox.setValue(30)
            self.trade_interval_spinbox.setEnabled(False)
            trade_interval_layout.addWidget(self.trade_interval_spinbox)
            candlestick_config_layout.addLayout(trade_interval_layout)
            
            # 交易数量
            trade_quantity_layout = QHBoxLayout()
            trade_quantity_layout.addWidget(QLabel("交易数量:"))
            self.trade_quantity_spinbox = QSpinBox()
            self.trade_quantity_spinbox.setRange(1, 100)
            self.trade_quantity_spinbox.setValue(1)
            self.trade_quantity_spinbox.setEnabled(False)
            trade_quantity_layout.addWidget(self.trade_quantity_spinbox)
            candlestick_config_layout.addLayout(trade_quantity_layout)
            
            config_layout.addWidget(candlestick_config_group)
        
        # 黄线检测模式选择
        detection_layout = QVBoxLayout()
        detection_layout.addWidget(QLabel("黄线检测模式:"))
        self.detection_mode_combo = QComboBox()
        self.detection_mode_combo.addItems([
            "高级检测-轮廓分析 (advanced_line_detector)", 
            "高级检测-模板匹配 (advanced_line_detector)",
            "高级检测-综合算法 (advanced_line_detector)"
        ])
        self.detection_mode_combo.setCurrentIndex(0)  # 默认使用轮廓分析
        detection_layout.addWidget(self.detection_mode_combo)
        
        # 角度阈值调节
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("角度阈值:"))
        self.angle_threshold_spinbox = QSpinBox()
        self.angle_threshold_spinbox.setRange(5, 90)  # 角度范围5-90度
        self.angle_threshold_spinbox.setValue(20)  # 默认20度（与新的角度检测器一致）
        self.angle_threshold_spinbox.setSuffix("°")
        self.angle_threshold_spinbox.setToolTip("设置黄线角度变化的触发阈值，超过此角度才会触发交易信号\n推荐值：敏感模式10°，标准模式20°，保守模式30°")
        threshold_layout.addWidget(self.angle_threshold_spinbox)

        # 快速设置按钮
        preset_btn_layout = QHBoxLayout()
        sensitive_btn = QPushButton("敏感(10°)")
        sensitive_btn.setMaximumWidth(60)
        sensitive_btn.clicked.connect(lambda: self.angle_threshold_spinbox.setValue(10))
        sensitive_btn.setToolTip("敏感模式：10度阈值，更频繁的信号")
        preset_btn_layout.addWidget(sensitive_btn)

        normal_btn = QPushButton("标准(20°)")
        normal_btn.setMaximumWidth(60)
        normal_btn.clicked.connect(lambda: self.angle_threshold_spinbox.setValue(20))
        normal_btn.setToolTip("标准模式：20度阈值，平衡的信号频率")
        preset_btn_layout.addWidget(normal_btn)

        conservative_btn = QPushButton("保守(30°)")
        conservative_btn.setMaximumWidth(60)
        conservative_btn.clicked.connect(lambda: self.angle_threshold_spinbox.setValue(30))
        conservative_btn.setToolTip("保守模式：30度阈值，较少的信号")
        preset_btn_layout.addWidget(conservative_btn)

        threshold_layout.addLayout(preset_btn_layout)
        detection_layout.addLayout(threshold_layout)
        
        config_layout.addLayout(detection_layout)
        
        layout.addWidget(config_group)
        
        # 统计信息组
        stats_group = QGroupBox("📊 运行统计")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_labels = {
            'uptime': QLabel("运行时间: 00:00:00"),
            'trades': QLabel("交易次数: 0"),
            'signals': QLabel("信号数量: 0"),
            'success_rate': QLabel("成功率: 0%"),
            'yellow_line_status': QLabel("🟡 黄线检测: 启用"),
            'candlestick_status': QLabel("🔵 K线检测: 禁用")
        }
        
        for label in self.stats_labels.values():
            label.setFont(QFont("Consolas", 9))
            stats_layout.addWidget(label)
        
        layout.addWidget(stats_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel
    
    def create_info_panel(self) -> QWidget:
        """创建信息面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 日志标签页
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        
        # 日志文本区域
        self.log_text = QPlainTextEdit()
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMaximumBlockCount(1000)  # 限制日志行数
        log_layout.addWidget(self.log_text)
        
        # 日志控制按钮
        log_button_layout = QHBoxLayout()
        
        clear_log_button = QPushButton("清空日志")
        clear_log_button.clicked.connect(self.clear_log)
        log_button_layout.addWidget(clear_log_button)
        
        save_log_button = QPushButton("保存日志")
        save_log_button.clicked.connect(self.save_log)
        log_button_layout.addWidget(save_log_button)
        
        log_button_layout.addStretch()
        log_layout.addLayout(log_button_layout)
        
        tab_widget.addTab(log_tab, "📋 运行日志")
        
        # 状态标签页
        status_tab = QWidget()
        status_layout = QVBoxLayout(status_tab)
        
        self.status_text = QTextEdit()
        self.status_text.setFont(QFont("Consolas", 9))
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        
        tab_widget.addTab(status_tab, "📊 系统状态")
        
        # 配置标签页
        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab)
        
        self.config_text = QTextEdit()
        self.config_text.setFont(QFont("Consolas", 9))
        config_layout.addWidget(self.config_text)
        
        load_config_button = QPushButton("重新加载配置")
        load_config_button.clicked.connect(self.reload_config)
        config_layout.addWidget(load_config_button)
        
        tab_widget.addTab(config_tab, "⚙️ 配置信息")
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        # 导入配置
        import_action = QAction('导入配置...', self)
        import_action.triggered.connect(self.import_config)
        file_menu.addAction(import_action)
        
        # 导出配置
        export_action = QAction('导出配置...', self)
        export_action.triggered.connect(self.export_config)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具(&T)')
        
        # 坐标校准
        calibrate_action = QAction('坐标校准...', self)
        calibrate_action.triggered.connect(self.open_calibration)
        tools_menu.addAction(calibrate_action)
        
        # 检测测试
        detection_action = QAction('检测测试...', self)
        detection_action.triggered.connect(self.open_detection_test)
        tools_menu.addAction(detection_action)
        
        tools_menu.addSeparator()
        
        # 客户端连接设置
        connection_action = QAction('客户端连接设置...', self)
        connection_action.triggered.connect(self.open_connection_settings)
        tools_menu.addAction(connection_action)
        
        # K线区域设置
        if CANDLESTICK_DETECTION_AVAILABLE:
            tools_menu.addSeparator()
            candlestick_area_action = QAction('设置K线图区域...', self)
            candlestick_area_action.triggered.connect(self.set_candlestick_area)
            tools_menu.addAction(candlestick_area_action)
            
            # K线颜色校准
            candlestick_calibrate_action = QAction('K线颜色校准...', self)
            candlestick_calibrate_action.triggered.connect(self.calibrate_candlestick_colors)
            tools_menu.addAction(candlestick_calibrate_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        # 关于
        about_action = QAction('关于...', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 客户端状态
        self.client_status_label = QLabel("客户端: 未连接")
        self.status_bar.addPermanentWidget(self.client_status_label)
        
        # 时间标签
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)
    
    def apply_styles(self):
        """应用界面样式"""
        style = """
        QMainWindow {
            background-color: #f0f0f0;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QPushButton {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 8px 16px;
            text-align: center;
            text-decoration: none;
            font-size: 12px;
            margin: 2px;
            border-radius: 4px;
        }
        
        QPushButton:hover {
            background-color: #45a049;
        }
        
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        #start_button {
            background-color: #2196F3;
            font-size: 14px;
        }
        
        #start_button:hover {
            background-color: #1976D2;
        }
        
        #stop_button {
            background-color: #f44336;
        }
        
        #stop_button:hover {
            background-color: #d32f2f;
        }
        
        QTextEdit {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px;
            background-color: white;
        }
        
        QTabWidget::pane {
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #2196F3;
        }
        """
        
        self.setStyleSheet(style)
        
        # 为特定按钮设置ID
        self.start_button.setObjectName("start_button")
        self.stop_button.setObjectName("stop_button")
    
    # 原来的init_trading_engine方法已被InitializationThread替代
    
    def on_yellow_line_mode_changed(self, state):
        """黄线检测模式切换回调"""
        try:
            self.yellow_line_enabled = (state == 2)  # Qt.Checked = 2
            
            if self.yellow_line_enabled:
                self.log_to_gui("✅ 黄线变动检测已启用")
                self.log_to_gui("📈 黄线上升 → 自动买入")
                self.log_to_gui("📉 黄线下降 → 自动卖出")
            else:
                self.log_to_gui("⏸️ 黄线变动检测已禁用")
                
            # 如果交易线程正在运行，更新其状态
            if self.trading_thread and hasattr(self.trading_thread, 'yellow_line_enabled'):
                self.trading_thread.yellow_line_enabled = self.yellow_line_enabled
                
        except Exception as e:
            self.log_to_gui(f"❌ 黄线模式切换失败: {e}")
    
    def on_candlestick_mode_changed(self, state):
        """K线识别模式切换回调"""
        try:
            self.candlestick_enabled = (state == 2)  # Qt.Checked = 2
            
            # 启用/禁用相关控件
            if hasattr(self, 'trade_interval_spinbox'):
                self.trade_interval_spinbox.setEnabled(self.candlestick_enabled)
            if hasattr(self, 'trade_quantity_spinbox'):
                self.trade_quantity_spinbox.setEnabled(self.candlestick_enabled)
            
            if self.candlestick_enabled:
                self.log_to_gui("✅ K线颜色识别交易已启用")
                self.log_to_gui("🔵 蓝色K线 → 自动卖出")
                self.log_to_gui("🔴 红色K线 → 自动买入")
            else:
                self.log_to_gui("⏸️ K线颜色识别交易已禁用")
                
            # 如果交易线程正在运行，更新其状态
            if self.trading_thread and hasattr(self.trading_thread, 'candlestick_enabled'):
                self.trading_thread.candlestick_enabled = self.candlestick_enabled
                
        except Exception as e:
            self.log_to_gui(f"❌ K线模式切换失败: {e}")
    
    def start_trading(self):
        """启动交易"""
        try:
            if not self.trading_engine:
                QMessageBox.warning(self, "错误", "交易引擎未初始化，请等待初始化完成")
                return

            # 检查初始化线程是否还在运行
            if self.init_thread and self.init_thread.isRunning():
                QMessageBox.information(self, "提示", "交易引擎正在初始化中，请稍候...")
                return
            
            self.log_text.appendPlainText("🚀 正在启动智能交易...")
            
            # 获取配置
            config = {
                'monitor_interval': self.interval_spinbox.value(),
                'debug_mode': self.debug_checkbox.isChecked(),
                'auto_screenshot': self.screenshot_checkbox.isChecked()
            }
            
            # 创建交易线程
            if TRADING_THREAD_AVAILABLE:
                if self.advanced_checkbox.isChecked():
                    self.trading_thread = AdvancedTradingThread(self.trading_engine, config)
                    self.log_text.appendPlainText("🔧 使用高级监测模式")
                else:
                    self.trading_thread = TradingThread(self.trading_engine)
                    self.log_text.appendPlainText("🔧 使用标准监测模式")
            else:
                # 创建简单的交易线程替代方案
                detection_mode = self.detection_mode_combo.currentIndex()
                angle_threshold = self.angle_threshold_spinbox.value()
                self.trading_thread = SimpleTrading(self.trading_engine, config, detection_mode, self, angle_threshold)
                self.log_text.appendPlainText(f"🔧 使用简化监测模式 (角度阈值: {angle_threshold}°)")
            
            # 连接信号
            self.trading_thread.log_signal.connect(self.log_text.appendPlainText)
            self.trading_thread.status_signal.connect(self.update_trading_status)
            
            # 启动线程
            self.trading_thread.start()
            
            # 更新UI状态
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("运行中...")
            
            self.log_text.appendPlainText("✅ 智能交易已启动")
            
            # 检查自动下单配置并给出提示
            auto_trading_config = self.config.get('auto_trading', {})
            if auto_trading_config.get('enabled', True):
                trade_cooldown = auto_trading_config.get('trade_cooldown', 30)
                
                self.log_text.appendPlainText("🎯 自动交易功能已启用：")
                self.log_text.appendPlainText(f"   • 黄线上升趋势时自动执行买入操作")
                self.log_text.appendPlainText(f"   • 黄线下降趋势时自动执行卖出操作")
                self.log_text.appendPlainText(f"   • 交易冷却时间：{trade_cooldown}秒")
                self.log_text.appendPlainText("⚠️ 系统将根据黄线变化自动执行买入/卖出交易")
                self.log_text.appendPlainText("ℹ️ 当前版本专注于买入/卖出功能，转出功能待后续实现")
            else:
                self.log_text.appendPlainText("ℹ️ 自动交易功能已禁用，仅进行监测")
            
        except Exception as e:
            error_msg = f"启动交易失败: {e}"
            self.log_text.appendPlainText(f"❌ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
    
    def stop_trading(self):
        """停止交易"""
        try:
            if self.trading_thread and self.trading_thread.isRunning():
                self.log_text.appendPlainText("⏹️ 正在停止交易...")
                self.trading_thread.stop()
                
                # 等待线程结束
                if self.trading_thread.wait(5000):  # 等待5秒
                    self.log_text.appendPlainText("✅ 交易已停止")
                else:
                    self.log_text.appendPlainText("⚠️ 强制终止交易线程")
                    self.trading_thread.terminate()
            
            # 更新UI状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("已停止")
            
        except Exception as e:
            error_msg = f"停止交易失败: {e}"
            self.log_text.appendPlainText(f"❌ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
    
    def test_coordinates(self):
        """测试坐标"""
        try:
            if not self.trading_engine:
                QMessageBox.warning(self, "错误", "交易引擎未初始化")
                return
            
            # 询问用户选择测试方式
            reply = QMessageBox.question(self, "坐标测试", 
                                       "选择测试方式:\n\n"
                                       "✅ 是 - 鼠标移动测试 (可视化，鼠标会依次移动到各按钮)\n"
                                       "❌ 否 - 快速验证测试 (仅检查坐标计算)",
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                # 鼠标移动测试
                self.log_text.appendPlainText("🎯 开始鼠标移动测试...")
                self.log_text.appendPlainText("⚠️ 请确保景陶易购客户端窗口可见，鼠标将依次移动到各按钮位置")
                
                # 给用户3秒准备时间
                for i in range(3, 0, -1):
                    self.log_text.appendPlainText(f"⏰ {i}秒后开始测试...")
                    QApplication.processEvents()
                    time.sleep(1)
                
                test_result = self.trading_engine.test_coordinates_with_mouse()
                
                if test_result:
                    self.log_text.appendPlainText("✅ 鼠标移动测试完成")
                    QMessageBox.information(self, "测试结果", "✅ 鼠标移动测试完成！\n\n请检查鼠标移动的位置是否准确对应各按钮。")
                else:
                    self.log_text.appendPlainText("❌ 鼠标移动测试失败")
                    QMessageBox.warning(self, "测试结果", "❌ 鼠标移动测试失败，请查看日志")
            else:
                # 快速验证测试
                self.log_text.appendPlainText("🧪 开始快速坐标验证...")
                
                all_buttons = [
                    'buy_mode_button', 'sell_mode_button',
                    'buy_order_button', 'sell_order_button', 'price_input', 'quantity_input',
                    'confirm_button', 'transfer_out_button', 'order_mode_button'
                ]
                
                test_result = self.trading_engine.test_coordinates(all_buttons)
                
                if test_result:
                    self.log_text.appendPlainText("✅ 坐标验证通过")
                    QMessageBox.information(self, "测试结果", "✅ 坐标验证通过，所有按钮位置计算正确")
                else:
                    self.log_text.appendPlainText("⚠️ 坐标验证发现问题，请查看详细日志")
                    QMessageBox.warning(self, "测试结果", "⚠️ 坐标验证发现问题，部分按钮位置可能不准确\n\n请查看详细日志或考虑重新校准")
            
        except Exception as e:
            error_msg = f"坐标测试失败: {e}"
            self.log_text.appendPlainText(f"❌ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
    
    def test_detection(self):
        """测试检测功能"""
        try:
            self.log_text.appendPlainText("🔍 开始测试检测功能...")
            
            if not self.trading_engine:
                QMessageBox.warning(self, "错误", "交易引擎未初始化")
                return
            
            # 简单的检测测试
            import pyautogui
            import numpy as np
            
            # 捕获屏幕
            screen = pyautogui.screenshot()
            screen_array = np.array(screen)
            
            # 测试黄线检测
            yellow_result = self.trading_engine.detect_yellow_line_change(screen_array)
            self.log_text.appendPlainText(f"🟡 黄线检测结果: {yellow_result}")
            
            # 测试景陶易购检测
            if hasattr(self.trading_engine, 'detect_jingtao_signals'):
                jingtao_result = self.trading_engine.detect_jingtao_signals(screen_array)
                self.log_text.appendPlainText(f"🎯 景陶易购检测结果: {jingtao_result}")
            
            self.log_text.appendPlainText("✅ 检测功能测试完成")
            
        except Exception as e:
            error_msg = f"检测测试失败: {e}"
            self.log_text.appendPlainText(f"❌ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
    
    def update_status(self):
        """更新状态信息"""
        try:
            # 更新时间
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M:%S")
            self.time_label.setText(current_time)
            
            # 更新客户端状态
            if self.connection_manager:
                connection_info = self.connection_manager.get_connection_info()
                status_text = f"客户端: {connection_info['status_text']}"
                
                # 根据连接状态设置不同颜色
                if connection_info['status'] == 'connected':
                    self.client_status_label.setStyleSheet("color: green; font-weight: bold;")
                elif connection_info['status'] == 'login_required':
                    self.client_status_label.setStyleSheet("color: orange; font-weight: bold;")
                elif connection_info['status'] == 'connecting':
                    self.client_status_label.setStyleSheet("color: blue; font-weight: bold;")
                else:
                    self.client_status_label.setStyleSheet("color: red; font-weight: bold;")
                
                self.client_status_label.setText(status_text)
            elif self.trading_engine and self.trading_engine.client_window:
                self.client_status_label.setText("客户端: 已连接")
                self.client_status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.client_status_label.setText("客户端: 未连接")
                self.client_status_label.setStyleSheet("color: red; font-weight: bold;")
            
            # 更新运行统计
            self.update_statistics()
            
            # 更新系统状态
            self.update_system_status()
            
        except Exception as e:
            self.logger.error(f"状态更新失败: {e}")
    
    def update_statistics(self):
        """更新运行统计"""
        try:
            # 运行时间统计
            if hasattr(self, 'start_time'):
                from datetime import datetime
                uptime = datetime.now() - self.start_time
                self.stats_labels['uptime'].setText(f"运行时间: {str(uptime).split('.')[0]}")
            
            # 检测模式状态
            if hasattr(self, 'yellow_line_enabled'):
                yellow_status = "启用" if self.yellow_line_enabled else "禁用"
                self.stats_labels['yellow_line_status'].setText(f"🟡 黄线检测: {yellow_status}")
            
            if hasattr(self, 'candlestick_enabled'):
                candlestick_status = "启用" if self.candlestick_enabled else "禁用"
                self.stats_labels['candlestick_status'].setText(f"🔵 K线检测: {candlestick_status}")
            
            # K线交易统计
            if self.trading_thread and hasattr(self.trading_thread, 'candlestick_trader') and self.trading_thread.candlestick_trader:
                try:
                    stats = self.trading_thread.candlestick_trader.get_trade_stats()
                    self.stats_labels['trades'].setText(f"K线交易: {stats.get('total_trades', 0)}")
                    
                    # 计算成功率
                    total = stats.get('total_trades', 0)
                    successful = stats.get('successful_trades', 0)
                    success_rate = (successful / total * 100) if total > 0 else 0
                    self.stats_labels['success_rate'].setText(f"成功率: {success_rate:.1f}%")
                    
                    # 信号统计
                    detection_stats = stats.get('detection_stats', {})
                    total_signals = detection_stats.get('total_detections', 0)
                    self.stats_labels['signals'].setText(f"K线信号: {total_signals}")
                    
                except Exception as e:
                    self.logger.debug(f"K线统计获取失败: {e}")
            else:
                # 显示传统统计
                self.stats_labels['trades'].setText(f"交易次数: 0")
                self.stats_labels['signals'].setText(f"信号数量: 0")
            
        except Exception as e:
            self.logger.error(f"统计更新失败: {e}")
    
    def update_system_status(self):
        """更新系统状态"""
        try:
            status_info = []
            
            # 系统基本信息
            status_info.append("=== 系统状态 ===")
            status_info.append(f"交易引擎: {'正常' if self.trading_engine else '未初始化'}")
            status_info.append(f"监测线程: {'运行中' if self.trading_thread and self.trading_thread.isRunning() else '已停止'}")
            
            # 配置信息
            status_info.append("\n=== 当前配置 ===")
            status_info.append(f"监测间隔: {self.interval_spinbox.value()}秒")
            status_info.append(f"调试模式: {'开启' if self.debug_checkbox.isChecked() else '关闭'}")
            status_info.append(f"自动截图: {'开启' if self.screenshot_checkbox.isChecked() else '关闭'}")
            status_info.append(f"高级模式: {'开启' if self.advanced_checkbox.isChecked() else '关闭'}")
            status_info.append(f"检测模式: {self.detection_mode_combo.currentText()}")
            status_info.append(f"角度阈值: {self.angle_threshold_spinbox.value()}°")
            
            # 线程状态
            if self.trading_thread:
                try:
                    if hasattr(self.trading_thread, 'get_thread_status'):
                        thread_status = self.trading_thread.get_thread_status()
                        status_info.append("\n=== 线程状态 ===")
                        for key, value in thread_status.items():
                            status_info.append(f"{key}: {value}")
                    else:
                        status_info.append("\n=== 线程状态 ===")
                        status_info.append("线程状态: 运行中" if self.trading_thread.isRunning() else "已停止")
                except Exception as thread_e:
                    status_info.append(f"\n=== 线程状态 ===")
                    status_info.append(f"状态获取失败: {thread_e}")
            
            self.status_text.setPlainText('\n'.join(status_info))
            
        except Exception as e:
            self.logger.error(f"系统状态更新失败: {e}")
    
    def update_trading_status(self, status_type: str, message: str = ""):
        """更新交易状态"""
        if message:
            self.status_label.setText(f"{status_type}: {message}")
        else:
            # 兼容旧的单参数格式
            self.status_label.setText(status_type)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.log_text.appendPlainText("📋 日志已清空")
    
    def save_log(self):
        """保存日志"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/trading_log_{timestamp}.txt"
            
            # 确保logs目录存在
            os.makedirs("logs", exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
            
            self.log_text.appendPlainText(f"💾 日志已保存到: {filename}")
            QMessageBox.information(self, "保存成功", f"日志已保存到: {filename}")
            
        except Exception as e:
            error_msg = f"保存日志失败: {e}"
            self.log_text.appendPlainText(f"❌ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
    
    def reload_config(self):
        """重新加载配置"""
        try:
            if self.trading_engine:
                # 重新加载坐标配置
                self.trading_engine.relative_positions = self.trading_engine.load_coordinate_config()
                self.trading_engine.validate_coordinates()
                
                # 显示配置信息
                config_info = json.dumps(self.trading_engine.relative_positions, indent=2, ensure_ascii=False)
                self.config_text.setPlainText(config_info)
                
                self.log_text.appendPlainText("✅ 配置重新加载完成")
            
        except Exception as e:
            error_msg = f"重新加载配置失败: {e}"
            self.log_text.appendPlainText(f"❌ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
    
    def load_settings(self):
        """加载设置"""
        try:
            # 恢复窗口状态
            geometry = self.settings.value('geometry')
            if geometry:
                self.restoreGeometry(geometry)
            
            # 恢复配置选项
            self.interval_spinbox.setValue(self.settings.value('monitor_interval', 5, type=int))
            self.debug_checkbox.setChecked(self.settings.value('debug_mode', False, type=bool))
            self.screenshot_checkbox.setChecked(self.settings.value('auto_screenshot', True, type=bool))
            self.advanced_checkbox.setChecked(self.settings.value('advanced_mode', False, type=bool))
            self.detection_mode_combo.setCurrentIndex(self.settings.value('detection_mode', 0, type=int))
            self.angle_threshold_spinbox.setValue(self.settings.value('angle_threshold', 20, type=int))
            
        except Exception as e:
            self.logger.error(f"加载设置失败: {e}")
    
    def save_settings(self):
        """保存设置"""
        try:
            # 保存窗口状态
            self.settings.setValue('geometry', self.saveGeometry())
            
            # 保存配置选项
            self.settings.setValue('monitor_interval', self.interval_spinbox.value())
            self.settings.setValue('debug_mode', self.debug_checkbox.isChecked())
            self.settings.setValue('auto_screenshot', self.screenshot_checkbox.isChecked())
            self.settings.setValue('advanced_mode', self.advanced_checkbox.isChecked())
            self.settings.setValue('detection_mode', self.detection_mode_combo.currentIndex())
            self.settings.setValue('angle_threshold', self.angle_threshold_spinbox.value())
            
        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
    
    def import_config(self):
        """导入配置"""
        # TODO: 实现配置导入功能
        QMessageBox.information(self, "功能开发中", "配置导入功能正在开发中...")
    
    def export_config(self):
        """导出配置"""
        # TODO: 实现配置导出功能
        QMessageBox.information(self, "功能开发中", "配置导出功能正在开发中...")
    
    def open_calibration(self):
        """打开坐标校准"""
        try:
            self.log_signal.emit("🔧 正在检查校准工具依赖...")
            
            # 检查必要的依赖
            missing_deps = []
            try:
                import win32gui
            except ImportError:
                missing_deps.append("pywin32")
            
            try:
                import cv2
            except ImportError:
                missing_deps.append("opencv-python")
            
            try:
                import pyautogui
            except ImportError:
                missing_deps.append("pyautogui")
            
            if missing_deps:
                error_msg = f"缺少必要依赖包: {', '.join(missing_deps)}\n\n请安装: pip install {' '.join(missing_deps)}"
                QMessageBox.critical(self, "依赖缺失", error_msg)
                self.log_signal.emit(f"❌ 缺少依赖: {', '.join(missing_deps)}")
                return
            
            # 尝试导入校准对话框
            try:
                from .calibration_dialog import CalibrationDialog
            except ImportError:
                try:
                    from calibration_dialog import CalibrationDialog
                except ImportError:
                    import sys
                    import os
                    current_dir = os.path.dirname(__file__)
                    if current_dir not in sys.path:
                        sys.path.append(current_dir)
                    from calibration_dialog import CalibrationDialog
            
            self.log_signal.emit("✅ 依赖检查通过，正在打开校准工具...")
            
            # 创建并显示对话框
            dialog = CalibrationDialog(self)
            result = dialog.exec_()
            
            if result == dialog.Accepted:
                self.log_signal.emit("✅ 坐标校准完成")
                QMessageBox.information(self, "校准完成", 
                    "坐标校准已完成，新配置已保存。\n\n" + 
                    "配置文件位置: config/smart_coordinates_config.json\n\n" +
                    "建议重启系统以使用新配置。")
            else:
                self.log_signal.emit("⚠️ 坐标校准已取消")
                
        except ImportError as e:
            error_msg = f"导入错误: {str(e)}\n\n请确保所有依赖包已正确安装"
            self.log_signal.emit(f"❌ 导入失败: {e}")
            QMessageBox.critical(self, "导入错误", error_msg)
            
        except Exception as e:
            self.log_signal.emit(f"❌ 校准工具错误: {e}")
            import traceback
            error_detail = traceback.format_exc()
            print(f"校准工具详细错误: {error_detail}")
            
            # 提供降级方案
            reply = QMessageBox.question(self, "校准工具错误", 
                f"内置校准工具出现错误:\n{str(e)}\n\n" +
                "是否使用外部校准工具？\n" +
                "(将打开tools/coordinate_calibrator.py)",
                QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.run_external_calibrator()
    
    def run_external_calibrator(self):
        """运行外部校准工具"""
        try:
            import subprocess
            import os
            
            calibrator_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                         'tools', 'coordinate_calibrator.py')
            
            if os.path.exists(calibrator_path):
                self.log_signal.emit("🔧 正在启动外部校准工具...")
                subprocess.Popen([sys.executable, calibrator_path])
                self.log_signal.emit("✅ 外部校准工具已启动")
            else:
                QMessageBox.warning(self, "文件不存在", f"找不到外部校准工具:\n{calibrator_path}")
                
        except Exception as e:
            self.log_signal.emit(f"❌ 启动外部校准工具失败: {e}")
            QMessageBox.critical(self, "启动失败", f"无法启动外部校准工具:\n{str(e)}")
    
    def open_detection_test(self):
        """打开检测测试"""
        # TODO: 实现检测测试功能
        QMessageBox.information(self, "功能开发中", "检测测试功能正在开发中...")
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h3>景陶易购智能交易系统 v2.0</h3>
        <p>一个智能化的自动交易系统，支持多种交易策略和风险管理。</p>
        
        <p><b>主要功能：</b></p>
        <ul>
        <li>智能信号检测</li>
        <li>自动交易执行</li>
        <li>风险管理控制</li>
        <li>实时监控报警</li>
        </ul>
        
        <p><b>技术栈：</b></p>
        <ul>
        <li>Python 3.9+</li>
        <li>PyQt5</li>
        <li>OpenCV</li>
        <li>NumPy</li>
        </ul>
        
        <p><small>版权所有 © 2025</small></p>
        """
        
        QMessageBox.about(self, "关于", about_text)
    
    def open_coordinate_calibrator(self):
        """打开坐标校准工具"""
        try:
            # 询问用户选择恢复还是重新校准
            reply = QMessageBox.question(self, "坐标校准", 
                                       "选择操作:\n\n"
                                       "✅ 是 - 恢复已验证的坐标配置 (推荐)\n"
                                       "❌ 否 - 启动坐标校准工具 (重新校准)",
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                # 恢复已验证的坐标
                self.restore_coordinates()
            else:
                # 启动校准工具
                self.start_calibration_tool()
            
        except Exception as e:
            error_msg = f"坐标校准失败: {e}"
            self.logger.error(error_msg)
            self.log_text.appendPlainText(f"❌ {error_msg}")
            QMessageBox.critical(self, "坐标校准错误", error_msg)
    
    def open_connection_settings(self):
        """打开客户端连接设置对话框"""
        try:
            if not self.connection_manager:
                QMessageBox.information(self, "提示", "连接管理器未初始化，请等待系统加载完成")
                return
            
            # 导入并创建连接设置对话框
            from .client_connection_dialog import ClientConnectionDialog
            dialog = ClientConnectionDialog(self, self.connection_manager)
            
            if dialog.exec_() == QDialog.Accepted:
                self.log_to_gui("✅ 客户端连接设置已更新")
                
                # 强制重新检测连接状态
                self.connection_manager.force_reconnect()
            
        except Exception as e:
            error_msg = f"打开连接设置失败: {e}"
            self.logger.error(error_msg)
            self.log_to_gui(f"❌ {error_msg}")
            QMessageBox.critical(self, "连接设置错误", error_msg)
    
    def restore_coordinates(self):
        """恢复已验证的坐标配置"""
        try:
            self.log_text.appendPlainText("🔄 正在恢复已验证的坐标配置...")
            
            if not self.trading_engine:
                QMessageBox.warning(self, "错误", "交易引擎未初始化")
                return
            
            # 先备份当前坐标
            self.trading_engine.save_current_coordinates_as_backup()
            
            # 恢复验证过的坐标
            if self.trading_engine.restore_verified_coordinates():
                self.log_text.appendPlainText("✅ 坐标恢复成功！")
                
                # 测试恢复的坐标
                if self.trading_engine.test_coordinates():
                    self.log_text.appendPlainText("✅ 恢复的坐标验证通过")
                    QMessageBox.information(self, "恢复成功", 
                                          "✅ 坐标恢复成功！\n\n"
                                          "已恢复到验证通过的坐标配置。\n"
                                          "当前坐标已自动备份到 current_coordinates_backup.json")
                else:
                    self.log_text.appendPlainText("⚠️ 恢复的坐标需要进一步验证")
                    QMessageBox.warning(self, "提醒", 
                                      "坐标已恢复但验证时出现警告。\n\n"
                                      "建议使用'测试坐标'功能进行验证。")
            else:
                self.log_text.appendPlainText("❌ 坐标恢复失败")
                QMessageBox.critical(self, "恢复失败", 
                                   "❌ 坐标恢复失败！\n\n"
                                   "请检查 backup_coordinates.json 文件是否存在。")
                
        except Exception as e:
            error_msg = f"恢复坐标失败: {e}"
            self.logger.error(error_msg)
            self.log_text.appendPlainText(f"❌ {error_msg}")
            QMessageBox.critical(self, "恢复失败", error_msg)
    
    def start_calibration_tool(self):
        """启动坐标校准工具"""
        try:
            self.log_text.appendPlainText("🎯 启动坐标校准工具...")
            
            # 导入校准工具模块
            import sys
            from pathlib import Path
            
            # 添加utils路径
            utils_path = Path(__file__).parent.parent.parent / "utils"
            if str(utils_path) not in sys.path:
                sys.path.insert(0, str(utils_path))
            
            from coordinate_calibrator import CoordinateCalibrator
            
            # 创建校准器实例
            self.calibrator = CoordinateCalibrator()
            
            # 运行校准工具
            self.calibrator.run()
            
            # 校准完成后重新加载配置
            self.reload_config()
            self.log_text.appendPlainText("✅ 坐标校准工具已关闭，配置已重新加载")
            
        except Exception as e:
            error_msg = f"启动坐标校准工具失败: {e}"
            self.logger.error(error_msg)
            self.log_text.appendPlainText(f"❌ {error_msg}")
            QMessageBox.critical(self, "校准工具错误", 
                               f"无法启动坐标校准工具:\n{e}\n\n"
                               f"请检查 utils/coordinate_calibrator.py 文件是否存在")
    
    def closeEvent(self, event):
        """关闭事件"""
        try:
            # 停止交易
            if self.trading_thread and self.trading_thread.isRunning():
                reply = QMessageBox.question(self, '确认退出', 
                                           '交易正在运行中，确定要退出吗？',
                                           QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    event.ignore()
                    return
                
                self.stop_trading()
            
            # 保存设置
            self.save_settings()
            
            # 接受关闭事件
            event.accept()
            
        except Exception as e:
            self.logger.error(f"关闭事件处理失败: {e}")
            event.accept()
    
    def set_candlestick_area(self):
        """设置K线图监控区域"""
        try:
            if not CANDLESTICK_DETECTION_AVAILABLE:
                QMessageBox.warning(self, "功能不可用", "K线识别模块未安装")
                return
            
            # 创建选择对话框
            reply = QMessageBox.question(self, "K线图区域设置", 
                                       "选择设置方式:\n\n"
                                       "是 - 启动专业区域选择工具（推荐）\n"
                                       "否 - 使用简化输入界面\n"
                                       "取消 - 取消操作",
                                       QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            
            if reply == QMessageBox.Yes:
                # 启动集成校准工具
                self.log_to_gui("🔧 启动K线区域设置工具...")
                try:
                    # 导入校准对话框
                    from .candlestick_calibration_dialog import CandlestickCalibrationDialog
                    
                    # 创建并显示对话框，默认切换到区域设置标签页
                    dialog = CandlestickCalibrationDialog(self, self.trading_engine)
                    dialog.tab_widget.setCurrentIndex(0)  # 切换到区域设置标签页
                    dialog.exec_()
                    
                    self.log_to_gui("✅ K线区域设置工具已关闭")
                    
                except ImportError as e:
                    self.log_to_gui(f"❌ 校准工具导入失败: {e}")
                    # 备用方案：启动外部工具
                    try:
                        import subprocess
                        import sys
                        import os
                        
                        tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tools')
                        calibrator_path = os.path.join(tools_dir, 'candlestick_calibrator.py')
                        
                        if os.path.exists(calibrator_path):
                            subprocess.Popen([sys.executable, calibrator_path, 'area'], 
                                           cwd=tools_dir,
                                           creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
                            self.log_to_gui("✅ 启动备用区域选择工具")
                            QMessageBox.information(self, "工具启动", "K线区域选择工具已启动！\n请在弹出的窗口中拖拽选择K线图区域。")
                        else:
                            QMessageBox.warning(self, "错误", "找不到K线校准工具")
                    except Exception as backup_e:
                        QMessageBox.critical(self, "错误", f"启动校准工具失败:\n{str(backup_e)}")
                        
                except Exception as e:
                    self.log_to_gui(f"❌ 启动校准工具失败: {e}")
                    QMessageBox.critical(self, "错误", f"启动校准工具失败:\n{str(e)}")
            
            elif reply == QMessageBox.No:
                # 使用简化界面
                self._show_simple_area_dialog()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置K线区域失败: {e}")
    
    def _show_simple_area_dialog(self):
        """显示简化的区域设置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("设置K线图区域")
        dialog.setModal(True)
        dialog.resize(350, 280)
        
        layout = QVBoxLayout(dialog)
        
        # 说明文本
        info_label = QLabel("请设置K线图在客户端窗口中的位置（相对坐标 0-1）:\n"
                           "提示: 左上角为(0,0)，右下角为(1,1)")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 加载当前配置
        current_area = {'x': 0.05, 'y': 0.12, 'width': 0.65, 'height': 0.55}
        
        # 尝试从配置文件加载
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     'app', 'config', 'candlestick_area_config.json')
            if os.path.exists(config_path):
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    current_area.update(json.load(f))
        except:
            pass
        
        # 输入框
        from PyQt5.QtWidgets import QFormLayout, QDoubleSpinBox
        form_layout = QFormLayout()
        
        self.x_spinbox = QDoubleSpinBox()
        self.x_spinbox.setRange(0.0, 1.0)
        self.x_spinbox.setSingleStep(0.01)
        self.x_spinbox.setDecimals(3)
        self.x_spinbox.setValue(current_area['x'])
        form_layout.addRow("左边界(X):", self.x_spinbox)
        
        self.y_spinbox = QDoubleSpinBox()
        self.y_spinbox.setRange(0.0, 1.0)
        self.y_spinbox.setSingleStep(0.01)
        self.y_spinbox.setDecimals(3)
        self.y_spinbox.setValue(current_area['y'])
        form_layout.addRow("上边界(Y):", self.y_spinbox)
        
        self.width_spinbox = QDoubleSpinBox()
        self.width_spinbox.setRange(0.1, 1.0)
        self.width_spinbox.setSingleStep(0.01)
        self.width_spinbox.setDecimals(3)
        self.width_spinbox.setValue(current_area['width'])
        form_layout.addRow("宽度:", self.width_spinbox)
        
        self.height_spinbox = QDoubleSpinBox()
        self.height_spinbox.setRange(0.1, 1.0)
        self.height_spinbox.setSingleStep(0.01)
        self.height_spinbox.setDecimals(3)
        self.height_spinbox.setValue(current_area['height'])
        form_layout.addRow("高度:", self.height_spinbox)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # 应用设置
            x = self.x_spinbox.value()
            y = self.y_spinbox.value()
            width = self.width_spinbox.value()
            height = self.height_spinbox.value()
            
            # 保存配置到文件
            try:
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                         'app', 'config', 'candlestick_area_config.json')
                area_config = {'x': x, 'y': y, 'width': width, 'height': height}
                
                import json
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(area_config, f, indent=2, ensure_ascii=False)
                
                self.log_to_gui(f"✅ K线图区域已设置并保存: ({x:.3f}, {y:.3f}, {width:.3f}, {height:.3f})")
            except Exception as e:
                self.log_to_gui(f"⚠️ 配置保存失败: {e}")
            
            # 更新K线检测器的区域设置
            if self.trading_thread and hasattr(self.trading_thread, 'candlestick_trader') and self.trading_thread.candlestick_trader:
                try:
                    # 使用reload_config方法重新加载配置
                    self.trading_thread.candlestick_trader.reload_config()
                    self.log_to_gui(f"✅ K线检测器配置已重新加载")
                    
                    # 显示新的配置信息
                    detector = self.trading_thread.candlestick_trader.candlestick_detector
                    current_area = detector.chart_area
                    self.log_to_gui(f"📊 当前K线区域: x={current_area['x']:.3f}, y={current_area['y']:.3f}, w={current_area['width']:.3f}, h={current_area['height']:.3f}")
                except Exception as e:
                    self.log_to_gui(f"❌ 重新加载配置失败: {e}")
            else:
                self.log_to_gui("⚠️ K线检测器未初始化，配置将在下次启动时生效")
    
    def calibrate_candlestick_colors(self):
        """校准K线颜色"""
        try:
            if not CANDLESTICK_DETECTION_AVAILABLE:
                QMessageBox.warning(self, "功能不可用", "K线识别模块未安装")
                return
            
            # 创建选择对话框
            reply = QMessageBox.question(self, "K线颜色校准", 
                                       "选择校准方式:\n\n"
                                       "是 - 启动专业颜色校准工具（推荐）\n"
                                       "否 - 使用简单内置校准\n"
                                       "取消 - 取消操作\n\n"
                                       "请确保客户端窗口可见且显示K线图。",
                                       QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            
            if reply == QMessageBox.Yes:
                # 启动集成校准工具
                self.log_to_gui("🎨 启动K线颜色校准工具...")
                try:
                    # 导入校准对话框
                    from .candlestick_calibration_dialog import CandlestickCalibrationDialog
                    
                    # 创建并显示对话框
                    dialog = CandlestickCalibrationDialog(self, self.trading_engine)
                    dialog.exec_()
                    
                    self.log_to_gui("✅ K线颜色校准工具已关闭")
                    
                except ImportError as e:
                    self.log_to_gui(f"❌ 校准工具导入失败: {e}")
                    # 备用方案：启动外部工具
                    try:
                        import subprocess
                        import sys
                        import os
                        
                        tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tools')
                        calibrator_path = os.path.join(tools_dir, 'candlestick_calibrator.py')
                        
                        if os.path.exists(calibrator_path):
                            subprocess.Popen([sys.executable, calibrator_path, 'color'], 
                                           cwd=tools_dir,
                                           creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
                            self.log_to_gui("✅ 启动备用校准工具")
                        else:
                            QMessageBox.warning(self, "错误", "找不到K线校准工具")
                    except Exception as backup_e:
                        QMessageBox.critical(self, "错误", f"启动校准工具失败:\n{str(backup_e)}")
                        
                except Exception as e:
                    self.log_to_gui(f"❌ 启动校准工具失败: {e}")
                    QMessageBox.critical(self, "错误", f"启动校准工具失败:\n{str(e)}")
            
            elif reply == QMessageBox.No:
                # 使用简单内置校准
                self._run_simple_color_calibration()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"颜色校准失败: {e}")
    
    def _run_simple_color_calibration(self):
        """运行简单的内置颜色校准"""
        try:
            self.log_to_gui("🎨 开始简单颜色校准...")
            
            # 执行内置校准
            if self.trading_thread and hasattr(self.trading_thread, 'candlestick_trader') and self.trading_thread.candlestick_trader:
                if hasattr(self.trading_thread.candlestick_trader, 'candlestick_detector'):
                    success = self.trading_thread.candlestick_trader.candlestick_detector.calibrate_colors()
                    if success:
                        QMessageBox.information(self, "校准完成", 
                                              "K线颜色校准完成！\n\n"
                                              "校准图像已保存到 logs/ 目录。\n"
                                              "如果检测效果不理想，建议使用专业校准工具。")
                        self.log_to_gui("✅ K线颜色校准完成")
                    else:
                        QMessageBox.warning(self, "校准失败", 
                                          "K线颜色校准失败！\n\n"
                                          "可能原因:\n"
                                          "1. 客户端窗口不可见\n"
                                          "2. 当前未显示K线图\n"
                                          "3. K线图区域设置不正确\n\n"
                                          "建议使用专业校准工具进行详细调试。")
                        self.log_to_gui("❌ K线颜色校准失败")
                else:
                    QMessageBox.warning(self, "校准失败", "K线检测器未正确初始化")
                    self.log_to_gui("⚠️ K线检测器未正确初始化")
            else:
                QMessageBox.warning(self, "校准失败", 
                                  "K线交易模块未初始化。\n\n"
                                  "请先:\n"
                                  "1. 启用K线颜色识别交易\n"
                                  "2. 启动交易监测\n"
                                  "3. 然后再进行颜色校准")
                self.log_to_gui("⚠️ K线交易模块未初始化")
                
        except Exception as e:
            self.log_to_gui(f"❌ 简单颜色校准失败: {e}")
            QMessageBox.critical(self, "错误", f"简单颜色校准失败:\n{str(e)}")


if __name__ == "__main__":
    # 测试代码
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("智能交易系统")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("SmartTrading")
    
    # 创建主窗口
    window = SmartTradingWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())