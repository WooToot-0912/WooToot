#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易监测线程模块
负责异步执行交易监测和信号处理
"""

import time
import logging
import pyautogui
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

# 暂时完全禁用增强检测器以排除卡死问题
ENHANCED_DETECTION_AVAILABLE = False
enhanced_detector = None


class TradingThread(QThread):
    """交易监测线程"""
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    
    def __init__(self, trading_engine):
        super().__init__()
        self.trading_engine = trading_engine
        self.is_running = False
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """运行交易监测主循环"""
        try:
            self.is_running = True
            self.log_signal.emit("🚀 开始智能监测和交易...")
            
            # 检测客户端并进行校准
            if not self.trading_engine.start_client():
                self.log_signal.emit("❌ 客户端检测或校准失败")
                self.log_signal.emit("请确保：")
                self.log_signal.emit("1. 景陶易购客户端已打开")
                self.log_signal.emit("2. 客户端窗口可见且未被最小化")
                self.log_signal.emit("3. 重新点击'启动智能交易'")
                return
            
            self.log_signal.emit("✅ 客户端检测和按钮校准成功")
            self.log_signal.emit("📊 开始监测黄线变化和价格变化...")
            
            # 开始监测主循环
            while self.is_running:
                try:
                    # 确保客户端窗口存在
                    if not self._ensure_client_window():
                        time.sleep(10)
                        continue
                    
                    # 捕获屏幕截图
                    screen_array = self._capture_screen()
                    if screen_array is None:
                        time.sleep(5)
                        continue
                    
                    # 保存调试截图（可选）
                    self._save_debug_screenshot(screen_array)
                    
                    # 执行信号检测
                    signals = self._detect_all_signals(screen_array)
                    
                    # 分析并执行交易
                    self._process_trading_signals(signals)
                    
                    # 更新状态
                    self.status_signal.emit("运行中...")
                    
                    time.sleep(5)  # 每5秒检查一次
                    
                except Exception as e:
                    self.log_signal.emit(f"⚠️ 监测循环异常: {e}")
                    self.logger.error(f"监测循环异常: {e}")
                    time.sleep(10)
            
        except Exception as e:
            self.log_signal.emit(f"❌ 交易线程异常: {e}")
            self.logger.error(f"交易线程异常: {e}")
        finally:
            self.status_signal.emit("已停止")
    
    def _ensure_client_window(self) -> bool:
        """确保客户端窗口可用"""
        try:
            if not self.trading_engine.client_window:
                self.log_signal.emit("🔍 客户端窗口丢失，重新查找...")
                if not self.trading_engine.find_client_window():
                    self.log_signal.emit("❌ 无法找到客户端窗口")
                    return False
                else:
                    self.log_signal.emit("✅ 重新连接客户端窗口成功")
            
            return True
            
        except Exception as e:
            self.log_signal.emit(f"❌ 客户端窗口检查失败: {e}")
            return False
    
    def _capture_screen(self) -> np.ndarray:
        """捕获全屏截图 - 全屏监测模式"""
        try:
            # 使用全屏截图而不是窗口区域截图
            screen = pyautogui.screenshot()
            
            # 转换为numpy数组
            screen_array = np.array(screen)
            return screen_array
            
        except Exception as e:
            self.log_signal.emit(f"❌ 屏幕截图失败: {e}")
            self.logger.error(f"屏幕截图失败: {e}")
            return None
    
    def _save_debug_screenshot(self, screen_array: np.ndarray):
        """保存调试截图（每30秒保存一次）"""
        try:
            current_time = time.time()
            
            if not hasattr(self, 'last_debug_save') or current_time - self.last_debug_save > 30:
                import cv2
                debug_filename = f"logs/debug_screenshot_{int(current_time)}.png"
                
                # 确保logs目录存在
                import os
                os.makedirs("logs", exist_ok=True)
                
                # 保存截图
                cv2.imwrite(debug_filename, cv2.cvtColor(screen_array, cv2.COLOR_RGB2BGR))
                self.log_signal.emit(f"📸 保存调试截图: {debug_filename}")
                self.last_debug_save = current_time
                
        except Exception as e:
            self.logger.error(f"保存调试截图失败: {e}")
    
    def _detect_all_signals(self, screen_array: np.ndarray) -> dict:
        """执行所有信号检测"""
        signals = {}
        
        try:
            # 1. 黄线检测
            yellow_signal = self.trading_engine.detect_yellow_line_change(screen_array)
            signals['yellow'] = yellow_signal
            
            if yellow_signal['signal'] != 'none':
                angle_change = yellow_signal.get('angle_change', 0)
                confidence = yellow_signal.get('confidence', 0.0)
                self.log_signal.emit(f"🟡 黄线监测: {yellow_signal['signal']} - 角度变化: {angle_change:.2f}度 (置信度: {confidence:.2f})")
            else:
                self.log_signal.emit("🟡 黄线监测: 稳定状态")
            
            # 2. 景陶易购专用检测（优先使用）
            enhanced_signal = None
            if hasattr(self.trading_engine, 'detect_jingtao_signals'):
                enhanced_signal = self.trading_engine.detect_jingtao_signals(screen_array)
                signals['jingtao'] = enhanced_signal
                
                if enhanced_signal['signal'] != 'none':
                    self.log_signal.emit(f"🎯 景陶易购检测: {enhanced_signal['signal']} "
                                       f"(置信度: {enhanced_signal['confidence']:.2f})")
            
            # 3. 备用增强检测（如果景陶易购检测不可用）
            if enhanced_signal is None or enhanced_signal['signal'] == 'none':
                if ENHANCED_DETECTION_AVAILABLE:
                    fallback_signal = self.trading_engine.detect_enhanced_signals(screen_array)
                    signals['enhanced'] = fallback_signal
                    
                    if fallback_signal['signal'] != 'hold':
                        enhanced_signal = fallback_signal
                        self.log_signal.emit(f"🔍 备用检测: {enhanced_signal['signal']} "
                                           f"(置信度: {enhanced_signal['confidence']:.2f})")
            
            signals['final_enhanced'] = enhanced_signal
            
        except Exception as e:
            self.log_signal.emit(f"❌ 信号检测失败: {e}")
            self.logger.error(f"信号检测失败: {e}")
        
        return signals
    
    def _process_trading_signals(self, signals: dict, value_change_info: dict = None):
        """处理交易信号并执行交易"""
        try:
            yellow_signal = signals.get('yellow', {})
            enhanced_signal = signals.get('final_enhanced', {})
            
            # 分析交易信号，传入货值变化信息
            trade_signal = self.trading_engine.analyze_trade_signal(
                yellow_signal, enhanced_signal, value_change_info
            )
            
            if trade_signal['should_trade']:
                self.log_signal.emit(f"🎯 触发交易信号: {trade_signal['reason']}")
                self.status_signal.emit("执行交易中...")
                
                # 执行交易
                success = self.trading_engine.execute_trade(trade_signal)
                if success:
                    self.log_signal.emit("✅ 交易执行完成")
                    self.status_signal.emit("交易完成")
                else:
                    self.log_signal.emit("❌ 交易执行失败")
                    self.status_signal.emit("交易失败")
            else:
                self.log_signal.emit(f"📊 无交易信号: {trade_signal['reason']}")
                
        except Exception as e:
            self.log_signal.emit(f"❌ 交易信号处理失败: {e}")
            self.logger.error(f"交易信号处理失败: {e}")
    
    def stop(self):
        """停止监测线程"""
        self.is_running = False
        self.log_signal.emit("⏹️ 正在停止交易监测...")
        self.logger.info("交易监测线程停止信号已发送")
    
    def pause(self):
        """暂停监测（保留线程但暂停处理）"""
        # 这里可以添加暂停逻辑
        self.log_signal.emit("⏸️ 监测已暂停")
        self.status_signal.emit("已暂停")
    
    def resume(self):
        """恢复监测"""
        # 这里可以添加恢复逻辑
        self.log_signal.emit("▶️ 监测已恢复")
        self.status_signal.emit("运行中...")
    
    def get_thread_status(self) -> dict:
        """获取线程状态"""
        return {
            'is_running': self.is_running,
            'is_alive': self.isRunning(),
            'has_client_window': self.trading_engine.client_window is not None,
            'last_trade_time': getattr(self.trading_engine, 'last_trade_time', 0)
        }


class AdvancedTradingThread(TradingThread):
    """高级交易线程，支持更多功能"""
    
    def __init__(self, trading_engine, config: dict = None):
        super().__init__(trading_engine)
        self.config = config or {}
        self.monitor_interval = self.config.get('monitor_interval', 5)
        self.debug_mode = self.config.get('debug_mode', False)
        self.auto_screenshot = self.config.get('auto_screenshot', True)
        
    def run(self):
        """运行高级监测循环"""
        try:
            self.is_running = True
            self.log_signal.emit("🚀 启动高级交易监测模式...")
            
            # 执行预检查
            if not self._pre_flight_check():
                return
            
            # 主监测循环
            while self.is_running:
                try:
                    # 执行一轮完整的监测
                    self._execute_monitoring_cycle()
                    
                    # 动态调整监测间隔
                    if self.debug_mode:
                        time.sleep(self.monitor_interval / 2)  # 调试模式更频繁
                    else:
                        time.sleep(self.monitor_interval)
                        
                except Exception as e:
                    self.log_signal.emit(f"⚠️ 监测周期异常: {e}")
                    time.sleep(self.monitor_interval * 2)  # 出错时延长间隔
                    
        except Exception as e:
            self.log_signal.emit(f"❌ 高级交易线程异常: {e}")
        finally:
            self.log_signal.emit("🛑 高级交易监测已停止")
    
    def _pre_flight_check(self) -> bool:
        """执行飞行前检查"""
        try:
            self.log_signal.emit("🔍 执行系统预检查...")
            
            # 检查客户端连接
            if not self.trading_engine.start_client():
                self.log_signal.emit("❌ 客户端连接失败")
                return False
            
            # 检查坐标配置
            if not self.trading_engine.test_coordinates():
                self.log_signal.emit("⚠️ 坐标测试发现问题，但继续运行")
            
            # 检查检测器状态
            self._check_detector_status()
            
            self.log_signal.emit("✅ 系统预检查完成")
            return True
            
        except Exception as e:
            self.log_signal.emit(f"❌ 预检查失败: {e}")
            return False
    
    def _check_detector_status(self):
        """检查各种检测器的状态"""
        try:
            status_info = []
            
            # 检查景陶易购检测器
            if hasattr(self.trading_engine, 'jingtao_detector') and self.trading_engine.jingtao_detector:
                status_info.append("✅ 景陶易购专用检测器")
            else:
                status_info.append("❌ 景陶易购专用检测器不可用")
            
            # 检查自动确认处理器
            if hasattr(self.trading_engine, 'auto_confirm_handler') and self.trading_engine.auto_confirm_handler:
                status_info.append("✅ 自动确认处理器")
            else:
                status_info.append("❌ 自动确认处理器不可用")
            
            # 检查增强检测器
            if ENHANCED_DETECTION_AVAILABLE:
                status_info.append("✅ 增强检测器")
            else:
                status_info.append("❌ 增强检测器不可用")
            
            self.log_signal.emit("🔧 检测器状态:")
            for status in status_info:
                self.log_signal.emit(f"   {status}")
                
        except Exception as e:
            self.log_signal.emit(f"❌ 检测器状态检查失败: {e}")
    
    def _execute_monitoring_cycle(self):
        """执行一轮完整的监测周期"""
        try:
            # 1. 确保客户端可用
            if not self._ensure_client_window():
                return
            
            # 2. 捕获屏幕
            screen_array = self._capture_screen()
            if screen_array is None:
                return
            
            # 3. 保存截图（如果启用）
            if self.auto_screenshot:
                self._save_debug_screenshot(screen_array)
            
            # 4. 执行信号检测
            signals = self._detect_all_signals(screen_array)
            
            # 4.5. 监控实时货值变化
            value_change_info = {}
            try:
                value_change = self.trading_engine.monitor_realtime_value_change(screen_array)
                if value_change.get('detected', False):
                    change_rate = value_change.get('change_rate', 0.0)
                    value_change_info = value_change  # 保存完整的货值变化信息
                    if abs(change_rate) > 0.5:  # 如果货值变化超过0.5%
                        self.log_signal.emit(f"📊 货值变化: {change_rate:+.2f}%")
                
                # 4.6. 更新当前价格
                current_price = self.trading_engine.get_current_price_from_display(screen_array)
                if current_price and current_price != self.trading_engine.current_price:
                    self.log_signal.emit(f"💰 当前价格: {current_price}")
            except Exception as e:
                self.log_signal.emit(f"⚠️ 实时监控失败: {e}")
            
            # 5. 信号质量评估
            signal_quality = self._evaluate_signal_quality(signals)
            
            # 6. 交易决策（始终进行交易决策，不再依赖信号质量阈值）
            # 将货值变化信息传递给交易决策
            self._process_trading_signals(signals, value_change_info)
            
        except Exception as e:
            self.log_signal.emit(f"❌ 监测周期执行失败: {e}")
    
    def _evaluate_signal_quality(self, signals: dict) -> dict:
        """评估信号质量"""
        try:
            total_confidence = 0.0
            signal_count = 0
            
            # 评估各个信号的质量
            for signal_type, signal_data in signals.items():
                if isinstance(signal_data, dict) and 'confidence' in signal_data:
                    confidence = signal_data['confidence']
                    total_confidence += confidence
                    signal_count += 1
            
            # 计算平均置信度
            avg_confidence = total_confidence / signal_count if signal_count > 0 else 0.0
            
            return {
                'confidence': avg_confidence,
                'signal_count': signal_count,
                'quality_level': 'high' if avg_confidence > 0.8 else 'medium' if avg_confidence > 0.5 else 'low'
            }
            
        except Exception as e:
            self.logger.error(f"信号质量评估失败: {e}")
            return {'confidence': 0.0, 'signal_count': 0, 'quality_level': 'unknown'}


if __name__ == "__main__":
    # 测试代码
    print("交易线程模块已加载")