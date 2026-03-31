#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强错误处理和容错机制
实现网络重连、客户端恢复、异常处理等功能
"""

import time
import logging
import psutil
import subprocess
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum
import threading
import traceback

class ErrorType(Enum):
    """错误类型"""
    NETWORK_ERROR = "network_error"
    CLIENT_CRASH = "client_crash"
    OCR_ERROR = "ocr_error"
    SCREENSHOT_ERROR = "screenshot_error"
    TRADING_ERROR = "trading_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN_ERROR = "unknown_error"

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorRecord:
    """错误记录"""
    def __init__(self, error_type: ErrorType, severity: ErrorSeverity, 
                 message: str, exception: Exception = None):
        self.timestamp = time.time()
        self.error_type = error_type
        self.severity = severity
        self.message = message
        self.exception = exception
        self.traceback = traceback.format_exc() if exception else ""
        self.resolved = False
        self.resolution_time = None
        self.resolution_method = ""

class ClientMonitor:
    """客户端监控器"""
    
    def __init__(self, process_names: List[str], window_titles: List[str]):
        self.process_names = process_names
        self.window_titles = window_titles
        self.logger = logging.getLogger(__name__)
        self.last_check_time = 0
        self.check_interval = 10  # 10秒检查一次
        
    def is_client_running(self) -> bool:
        """检查客户端是否运行"""
        try:
            # 检查进程
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] in self.process_names:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查客户端进程失败: {e}")
            return False
    
    def restart_client(self, client_path: str = None) -> bool:
        """重启客户端"""
        try:
            if client_path:
                self.logger.info(f"尝试重启客户端: {client_path}")
                subprocess.Popen(client_path)
                time.sleep(5)  # 等待启动
                return self.is_client_running()
            else:
                self.logger.warning("未配置客户端路径，无法自动重启")
                return False
                
        except Exception as e:
            self.logger.error(f"重启客户端失败: {e}")
            return False

class NetworkMonitor:
    """网络监控器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.last_check_time = 0
        self.check_interval = 30  # 30秒检查一次
        self.connection_timeout = 5
        
    def check_network_connection(self) -> bool:
        """检查网络连接"""
        try:
            import socket
            
            # 尝试连接到公共DNS服务器
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connection_timeout)
            result = sock.connect_ex(('8.8.8.8', 53))
            sock.close()
            
            return result == 0
            
        except Exception as e:
            self.logger.error(f"网络连接检查失败: {e}")
            return False
    
    def wait_for_network_recovery(self, max_wait_time: int = 300) -> bool:
        """等待网络恢复"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            if self.check_network_connection():
                self.logger.info("网络连接已恢复")
                return True
            
            self.logger.info("等待网络恢复...")
            time.sleep(10)
        
        self.logger.error(f"网络恢复超时: {max_wait_time}秒")
        return False

class ErrorHandler:
    """增强错误处理器"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        # 错误记录
        self.error_history: List[ErrorRecord] = []
        self.max_history_size = 1000
        
        # 重试配置
        self.max_retries = 3
        self.retry_delays = [1, 3, 5]  # 重试延迟（秒）
        
        # 监控器
        self.client_monitor = None
        self.network_monitor = NetworkMonitor()
        
        # 恢复策略
        self.recovery_strategies = {
            ErrorType.NETWORK_ERROR: self._handle_network_error,
            ErrorType.CLIENT_CRASH: self._handle_client_crash,
            ErrorType.OCR_ERROR: self._handle_ocr_error,
            ErrorType.SCREENSHOT_ERROR: self._handle_screenshot_error,
            ErrorType.TRADING_ERROR: self._handle_trading_error,
            ErrorType.SYSTEM_ERROR: self._handle_system_error
        }
        
        # 加载配置
        self.load_config()
        
        self.logger.info("增强错误处理器初始化完成")
    
    def load_config(self):
        """加载配置"""
        if self.config_manager:
            client_config = self.config_manager.get('client', {})
            process_names = client_config.get('process_names', [])
            window_titles = client_config.get('window_titles', [])
            
            if process_names or window_titles:
                self.client_monitor = ClientMonitor(process_names, window_titles)
    
    def handle_error(self, error_type: ErrorType, severity: ErrorSeverity,
                    message: str, exception: Exception = None,
                    context: Dict[str, Any] = None) -> bool:
        """处理错误"""
        try:
            # 记录错误
            error_record = ErrorRecord(error_type, severity, message, exception)
            self.error_history.append(error_record)
            
            # 限制历史记录大小
            if len(self.error_history) > self.max_history_size:
                self.error_history = self.error_history[-self.max_history_size:]
            
            # 记录日志
            log_message = f"错误处理: {error_type.value} - {severity.value} - {message}"
            if exception:
                log_message += f" - 异常: {str(exception)}"
            
            if severity == ErrorSeverity.CRITICAL:
                self.logger.critical(log_message)
            elif severity == ErrorSeverity.HIGH:
                self.logger.error(log_message)
            elif severity == ErrorSeverity.MEDIUM:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
            
            # 尝试恢复
            if error_type in self.recovery_strategies:
                recovery_success = self.recovery_strategies[error_type](
                    error_record, context or {}
                )
                
                if recovery_success:
                    error_record.resolved = True
                    error_record.resolution_time = time.time()
                    self.logger.info(f"错误已恢复: {error_type.value}")
                    return True
                else:
                    self.logger.error(f"错误恢复失败: {error_type.value}")
                    return False
            else:
                self.logger.warning(f"未知错误类型，无法自动恢复: {error_type.value}")
                return False
                
        except Exception as e:
            self.logger.error(f"错误处理器本身发生错误: {e}")
            return False
    
    def retry_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """重试操作"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    self.logger.warning(f"操作失败，{delay}秒后重试 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(delay)
                else:
                    self.logger.error(f"操作重试失败，已达最大重试次数: {e}")
        
        raise last_exception
    
    def _handle_network_error(self, error_record: ErrorRecord, 
                             context: Dict[str, Any]) -> bool:
        """处理网络错误"""
        try:
            self.logger.info("检测到网络错误，尝试恢复...")
            
            # 等待网络恢复
            if self.network_monitor.wait_for_network_recovery():
                error_record.resolution_method = "网络自动恢复"
                return True
            else:
                error_record.resolution_method = "网络恢复超时"
                return False
                
        except Exception as e:
            self.logger.error(f"网络错误处理失败: {e}")
            return False
    
    def _handle_client_crash(self, error_record: ErrorRecord,
                            context: Dict[str, Any]) -> bool:
        """处理客户端崩溃"""
        try:
            if not self.client_monitor:
                self.logger.warning("客户端监控器未配置")
                return False
            
            self.logger.info("检测到客户端崩溃，尝试重启...")
            
            # 尝试重启客户端
            client_path = context.get('client_path')
            if self.client_monitor.restart_client(client_path):
                error_record.resolution_method = "客户端自动重启"
                return True
            else:
                error_record.resolution_method = "客户端重启失败"
                return False
                
        except Exception as e:
            self.logger.error(f"客户端崩溃处理失败: {e}")
            return False
    
    def _handle_ocr_error(self, error_record: ErrorRecord,
                         context: Dict[str, Any]) -> bool:
        """处理OCR错误"""
        try:
            self.logger.info("检测到OCR错误，尝试恢复...")
            
            # OCR错误通常是临时的，等待一段时间后重试
            time.sleep(2)
            error_record.resolution_method = "OCR错误等待恢复"
            return True
            
        except Exception as e:
            self.logger.error(f"OCR错误处理失败: {e}")
            return False
    
    def _handle_screenshot_error(self, error_record: ErrorRecord,
                                context: Dict[str, Any]) -> bool:
        """处理截图错误"""
        try:
            self.logger.info("检测到截图错误，尝试恢复...")
            
            # 截图错误可能是窗口被遮挡或最小化
            # 尝试激活窗口
            time.sleep(1)
            error_record.resolution_method = "截图错误等待恢复"
            return True
            
        except Exception as e:
            self.logger.error(f"截图错误处理失败: {e}")
            return False
    
    def _handle_trading_error(self, error_record: ErrorRecord,
                             context: Dict[str, Any]) -> bool:
        """处理交易错误"""
        try:
            self.logger.info("检测到交易错误，尝试恢复...")
            
            # 交易错误可能需要重新校准坐标或重新登录
            time.sleep(3)
            error_record.resolution_method = "交易错误等待恢复"
            return True
            
        except Exception as e:
            self.logger.error(f"交易错误处理失败: {e}")
            return False
    
    def _handle_system_error(self, error_record: ErrorRecord,
                            context: Dict[str, Any]) -> bool:
        """处理系统错误"""
        try:
            self.logger.info("检测到系统错误，尝试恢复...")
            
            # 系统错误可能需要清理资源或重启组件
            import gc
            gc.collect()  # 强制垃圾回收
            
            time.sleep(2)
            error_record.resolution_method = "系统错误资源清理"
            return True
            
        except Exception as e:
            self.logger.error(f"系统错误处理失败: {e}")
            return False
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        if not self.error_history:
            return {}
        
        # 按类型统计
        type_counts = {}
        severity_counts = {}
        resolved_count = 0
        
        for error in self.error_history:
            # 错误类型统计
            error_type = error.error_type.value
            type_counts[error_type] = type_counts.get(error_type, 0) + 1
            
            # 严重程度统计
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # 解决状态统计
            if error.resolved:
                resolved_count += 1
        
        total_errors = len(self.error_history)
        resolution_rate = resolved_count / total_errors if total_errors > 0 else 0
        
        return {
            'total_errors': total_errors,
            'resolved_errors': resolved_count,
            'resolution_rate': resolution_rate,
            'error_types': type_counts,
            'severity_distribution': severity_counts,
            'recent_errors': [
                {
                    'timestamp': error.timestamp,
                    'type': error.error_type.value,
                    'severity': error.severity.value,
                    'message': error.message,
                    'resolved': error.resolved
                }
                for error in self.error_history[-10:]  # 最近10个错误
            ]
        }

# 全局错误处理器实例
error_handler = ErrorHandler()
