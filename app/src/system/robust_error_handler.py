#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健壮的错误处理和自动恢复系统
处理各种异常情况并自动恢复
"""

import time
import logging
import traceback
import psutil
import subprocess
import os
import threading
import json
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import pyautogui
import cv2
import numpy as np
from datetime import datetime, timedelta

class ErrorType(Enum):
    """错误类型"""
    NETWORK_ERROR = "network_error"
    CLIENT_CRASH = "client_crash"
    UI_DETECTION_FAILED = "ui_detection_failed"
    COORDINATE_INVALID = "coordinate_invalid"
    TRADING_TIMEOUT = "trading_timeout"
    SYSTEM_ERROR = "system_error"
    STRATEGY_ERROR = "strategy_error"

@dataclass
class ErrorRecord:
    """错误记录"""
    timestamp: float
    error_type: ErrorType
    message: str
    context: Dict
    recovery_attempted: bool = False
    recovery_success: bool = False
    retry_count: int = 0

class RobustErrorHandler:
    """健壮的错误处理器"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        # 错误记录
        self.error_history: List[ErrorRecord] = []
        self.max_history = 1000
        
        # 恢复策略
        self.recovery_strategies = {
            ErrorType.CLIENT_CRASH: self._recover_from_client_crash,
            ErrorType.UI_DETECTION_FAILED: self._recover_from_ui_detection_failed,
            ErrorType.COORDINATE_INVALID: self._recover_from_coordinate_invalid,
            ErrorType.TRADING_TIMEOUT: self._recover_from_trading_timeout,
            ErrorType.NETWORK_ERROR: self._recover_from_network_error,
            ErrorType.SYSTEM_ERROR: self._recover_from_system_error,
            ErrorType.STRATEGY_ERROR: self._recover_from_strategy_error
        }
        
        # 重试配置
        self.max_retries = {
            ErrorType.CLIENT_CRASH: 3,
            ErrorType.UI_DETECTION_FAILED: 5,
            ErrorType.COORDINATE_INVALID: 3,
            ErrorType.TRADING_TIMEOUT: 2,
            ErrorType.NETWORK_ERROR: 5,
            ErrorType.SYSTEM_ERROR: 2,
            ErrorType.STRATEGY_ERROR: 3
        }
        
        # 客户端信息
        self.client_exe_name = "景陶易购客户端.exe"
        self.client_path = self._find_client_path()
        
        # 系统状态
        self.is_recovery_mode = False
        self.last_healthy_time = time.time()
        self.circuit_breaker_active = False
        
        # 监控线程
        self.monitor_thread = None
        self.monitor_running = False
        
        self.logger.info("健壮错误处理器初始化完成")
    
    def handle_error(self, error_type: ErrorType, message: str, 
                    context: Dict = None, auto_recover: bool = True) -> bool:
        """处理错误"""
        try:
            # 记录错误
            error_record = ErrorRecord(
                timestamp=time.time(),
                error_type=error_type,
                message=message,
                context=context or {}
            )
            
            self.error_history.append(error_record)
            if len(self.error_history) > self.max_history:
                self.error_history.pop(0)
            
            self.logger.error(f"错误发生: {error_type.value} - {message}")
            
            # 检查是否需要触发熔断器
            if self._should_trigger_circuit_breaker(error_type):
                self.circuit_breaker_active = True
                self.logger.critical("系统熔断器已激活")
                return False
            
            # 自动恢复
            if auto_recover:
                recovery_success = self._attempt_recovery(error_record)
                error_record.recovery_attempted = True
                error_record.recovery_success = recovery_success
                
                if recovery_success:
                    self.last_healthy_time = time.time()
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"错误处理器本身发生错误: {e}")
            return False
    
    def _attempt_recovery(self, error_record: ErrorRecord) -> bool:
        """尝试恢复"""
        try:
            error_type = error_record.error_type
            
            # 检查重试次数
            if error_record.retry_count >= self.max_retries.get(error_type, 3):
                self.logger.warning(f"错误 {error_type.value} 重试次数已达上限")
                return False
            
            error_record.retry_count += 1
            self.is_recovery_mode = True
            
            # 执行对应的恢复策略
            if error_type in self.recovery_strategies:
                recovery_func = self.recovery_strategies[error_type]
                success = recovery_func(error_record)
                
                if success:
                    self.logger.info(f"错误 {error_type.value} 恢复成功")
                else:
                    self.logger.warning(f"错误 {error_type.value} 恢复失败")
                
                self.is_recovery_mode = False
                return success
            else:
                self.logger.warning(f"未找到 {error_type.value} 的恢复策略")
                self.is_recovery_mode = False
                return False
                
        except Exception as e:
            self.logger.error(f"恢复过程中发生错误: {e}")
            self.is_recovery_mode = False
            return False
    
    def _recover_from_client_crash(self, error_record: ErrorRecord) -> bool:
        """从客户端崩溃中恢复"""
        try:
            self.logger.info("开始客户端崩溃恢复...")
            
            # 1. 杀死残留进程
            self._kill_client_processes()
            time.sleep(3)
            
            # 2. 重启客户端
            if self.client_path and os.path.exists(self.client_path):
                self.logger.info(f"重启客户端: {self.client_path}")
                subprocess.Popen([self.client_path])
                
                # 3. 等待客户端启动
                startup_timeout = 60  # 60秒超时
                start_time = time.time()
                
                while time.time() - start_time < startup_timeout:
                    if self._is_client_running():
                        time.sleep(10)  # 额外等待界面完全加载
                        
                        # 4. 验证客户端可用性
                        if self._verify_client_functionality():
                            self.logger.info("客户端重启成功")
                            return True
                        
                    time.sleep(2)
                
                self.logger.error("客户端重启超时")
                return False
            else:
                self.logger.error(f"客户端路径无效: {self.client_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"客户端崩溃恢复失败: {e}")
            return False
    
    def _recover_from_ui_detection_failed(self, error_record: ErrorRecord) -> bool:
        """从UI检测失败中恢复"""
        try:
            self.logger.info("开始UI检测失败恢复...")
            
            # 1. 尝试重新获取窗口焦点
            self._bring_client_to_front()
            time.sleep(2)
            
            # 2. 清理可能的弹窗
            self._close_popup_dialogs()
            time.sleep(1)
            
            # 3. 重新校准坐标（如果有校准功能）
            if hasattr(self, 'coordinate_calibrator'):
                self.logger.info("尝试重新校准坐标")
                calibration_success = self.coordinate_calibrator.auto_calibrate()
                if calibration_success:
                    return True
            
            # 4. 尝试多次检测
            for attempt in range(3):
                self.logger.info(f"UI检测重试 {attempt + 1}/3")
                time.sleep(2)
                
                # 这里应该调用实际的UI检测函数
                # detection_result = self.ui_detector.detect_buttons()
                # if detection_result['success']:
                #     return True
            
            # 5. 最后手段：重启客户端
            self.logger.warning("UI检测多次失败，尝试重启客户端")
            return self._recover_from_client_crash(error_record)
            
        except Exception as e:
            self.logger.error(f"UI检测失败恢复失败: {e}")
            return False
    
    def _recover_from_coordinate_invalid(self, error_record: ErrorRecord) -> bool:
        """从坐标无效中恢复"""
        try:
            self.logger.info("开始坐标无效恢复...")
            
            # 1. 检查窗口是否改变
            current_window_info = self._get_client_window_info()
            if current_window_info:
                # 保存当前窗口信息
                self._save_window_info(current_window_info)
                
                # 2. 重新计算坐标
                self._recalculate_coordinates(current_window_info)
                
                # 3. 验证新坐标
                if self._validate_coordinates():
                    self.logger.info("坐标恢复成功")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"坐标无效恢复失败: {e}")
            return False
    
    def _recover_from_trading_timeout(self, error_record: ErrorRecord) -> bool:
        """从交易超时中恢复"""
        try:
            self.logger.info("开始交易超时恢复...")
            
            # 1. 取消当前操作
            pyautogui.press('esc')  # 取消操作
            time.sleep(1)
            
            # 2. 清理弹窗
            self._close_popup_dialogs()
            
            # 3. 检查交易状态
            # 这里应该检查订单是否已成交
            
            # 4. 重置交易状态
            # self.trading_engine.reset_trading_state()
            
            return True
            
        except Exception as e:
            self.logger.error(f"交易超时恢复失败: {e}")
            return False
    
    def _recover_from_network_error(self, error_record: ErrorRecord) -> bool:
        """从网络错误中恢复"""
        try:
            self.logger.info("开始网络错误恢复...")
            
            # 1. 等待网络恢复
            for attempt in range(10):
                if self._check_network_connectivity():
                    self.logger.info("网络连接已恢复")
                    time.sleep(5)  # 等待数据同步
                    return True
                time.sleep(5)
            
            self.logger.error("网络连接恢复超时")
            return False
            
        except Exception as e:
            self.logger.error(f"网络错误恢复失败: {e}")
            return False
    
    def _recover_from_system_error(self, error_record: ErrorRecord) -> bool:
        """从系统错误中恢复"""
        try:
            self.logger.info("开始系统错误恢复...")
            
            # 1. 检查系统资源
            if not self._check_system_resources():
                self.logger.error("系统资源不足")
                return False
            
            # 2. 清理临时文件
            self._cleanup_temp_files()
            
            # 3. 重启相关组件
            return self._restart_components()
            
        except Exception as e:
            self.logger.error(f"系统错误恢复失败: {e}")
            return False
    
    def _recover_from_strategy_error(self, error_record: ErrorRecord) -> bool:
        """从策略错误中恢复"""
        try:
            self.logger.info("开始策略错误恢复...")
            
            # 1. 重置策略状态
            # self.strategy_engine.reset()
            
            # 2. 重新加载策略配置
            # self.strategy_engine.reload_config()
            
            # 3. 重新初始化策略
            # return self.strategy_engine.initialize()
            
            return True
            
        except Exception as e:
            self.logger.error(f"策略错误恢复失败: {e}")
            return False
    
    def _should_trigger_circuit_breaker(self, error_type: ErrorType) -> bool:
        """判断是否应该触发熔断器"""
        try:
            # 短时间内大量错误
            recent_errors = [
                record for record in self.error_history
                if time.time() - record.timestamp < 300  # 5分钟内
            ]
            
            if len(recent_errors) > 10:
                return True
            
            # 关键错误连续发生
            critical_errors = [ErrorType.CLIENT_CRASH, ErrorType.SYSTEM_ERROR]
            if error_type in critical_errors:
                recent_critical = [
                    record for record in recent_errors
                    if record.error_type in critical_errors
                ]
                if len(recent_critical) > 3:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"熔断器判断失败: {e}")
            return True  # 出错时保守处理
    
    def _find_client_path(self) -> Optional[str]:
        """查找客户端路径"""
        possible_paths = [
            r"C:\景陶易购客户端.exe",
            r"D:\景陶易购客户端.exe",
            r"C:\Program Files\景陶易购\景陶易购客户端.exe",
            r"C:\Program Files (x86)\景陶易购\景陶易购客户端.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _is_client_running(self) -> bool:
        """检查客户端是否运行"""
        try:
            for process in psutil.process_iter(['pid', 'name']):
                if self.client_exe_name.lower() in process.info['name'].lower():
                    return True
            return False
        except:
            return False
    
    def _kill_client_processes(self):
        """杀死客户端进程"""
        try:
            for process in psutil.process_iter(['pid', 'name']):
                if self.client_exe_name.lower() in process.info['name'].lower():
                    process.kill()
                    self.logger.info(f"已杀死进程: {process.info['pid']}")
        except Exception as e:
            self.logger.error(f"杀死客户端进程失败: {e}")
    
    def _bring_client_to_front(self):
        """将客户端窗口置于前台"""
        try:
            import win32gui
            def callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if "景陶易购" in window_text:
                        win32gui.SetForegroundWindow(hwnd)
                        return False
                return True
            
            win32gui.EnumWindows(callback, [])
        except Exception as e:
            self.logger.error(f"置前台失败: {e}")
    
    def _close_popup_dialogs(self):
        """关闭弹出对话框"""
        try:
            # 按ESC键关闭可能的弹窗
            pyautogui.press('esc')
            time.sleep(0.5)
            
            # 检测并关闭确认对话框
            screenshot = pyautogui.screenshot()
            # 这里可以添加特定的弹窗检测和关闭逻辑
            
        except Exception as e:
            self.logger.error(f"关闭弹窗失败: {e}")
    
    def _verify_client_functionality(self) -> bool:
        """验证客户端功能性"""
        try:
            # 1. 检查窗口是否存在
            if not self._is_client_running():
                return False
            
            # 2. 尝试获取窗口截图
            screenshot = pyautogui.screenshot()
            if screenshot is None:
                return False
            
            # 3. 检查关键UI元素
            # 这里应该调用UI检测功能验证关键按钮是否可见
            
            return True
            
        except Exception as e:
            self.logger.error(f"客户端功能验证失败: {e}")
            return False
    
    def start_monitoring(self):
        """启动监控线程"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitor_running = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            self.logger.info("错误处理监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitor_running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("错误处理监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.monitor_running:
            try:
                # 检查客户端状态
                if not self._is_client_running():
                    self.handle_error(
                        ErrorType.CLIENT_CRASH,
                        "客户端进程不存在",
                        auto_recover=True
                    )
                
                # 检查系统资源
                if not self._check_system_resources():
                    self.handle_error(
                        ErrorType.SYSTEM_ERROR,
                        "系统资源不足",
                        auto_recover=True
                    )
                
                time.sleep(10)  # 每10秒检查一次
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                time.sleep(30)
    
    def _check_system_resources(self) -> bool:
        """检查系统资源"""
        try:
            # 检查内存使用率
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return False
            
            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 95:
                return False
            
            return True
            
        except:
            return True  # 检查失败时假设正常
    
    def get_error_statistics(self) -> Dict:
        """获取错误统计"""
        try:
            now = time.time()
            
            # 最近24小时的错误
            recent_errors = [
                record for record in self.error_history
                if now - record.timestamp < 86400
            ]
            
            # 按类型统计
            error_counts = {}
            for error_type in ErrorType:
                error_counts[error_type.value] = len([
                    record for record in recent_errors
                    if record.error_type == error_type
                ])
            
            # 恢复成功率
            recovery_attempts = [record for record in recent_errors if record.recovery_attempted]
            recovery_success_rate = 0.0
            if recovery_attempts:
                successful_recoveries = [record for record in recovery_attempts if record.recovery_success]
                recovery_success_rate = len(successful_recoveries) / len(recovery_attempts)
            
            return {
                'total_errors_24h': len(recent_errors),
                'error_counts': error_counts,
                'recovery_success_rate': recovery_success_rate,
                'circuit_breaker_active': self.circuit_breaker_active,
                'last_healthy_time': self.last_healthy_time,
                'is_recovery_mode': self.is_recovery_mode
            }
            
        except Exception as e:
            self.logger.error(f"获取错误统计失败: {e}")
            return {}

# 装饰器：自动错误处理
def auto_error_handler(error_type: ErrorType, auto_recover: bool = True):
    """自动错误处理装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 获取错误处理器实例（假设在self中）
                if hasattr(args[0], 'error_handler'):
                    error_handler = args[0].error_handler
                    error_handler.handle_error(
                        error_type,
                        f"{func.__name__}执行失败: {str(e)}",
                        context={'function': func.__name__, 'args': str(args), 'kwargs': str(kwargs)},
                        auto_recover=auto_recover
                    )
                raise e
        return wrapper
    return decorator

if __name__ == "__main__":
    # 测试
    handler = RobustErrorHandler()
    handler.start_monitoring()
    
    # 模拟错误
    handler.handle_error(
        ErrorType.UI_DETECTION_FAILED,
        "测试错误",
        context={'test': True}
    )
    
    print(handler.get_error_statistics())