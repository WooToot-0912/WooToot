#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化模块
实现内存管理、图像缓存、截图优化等功能
"""

import time
import gc
import psutil
import threading
import logging
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
import numpy as np
import cv2
from datetime import datetime, timedelta

class ImageCache:
    """图像缓存管理器"""
    
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl  # 生存时间（秒）
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[np.ndarray]:
        """获取缓存图像"""
        with self.lock:
            if key in self.cache:
                # 检查是否过期
                if time.time() - self.timestamps[key] < self.ttl:
                    # 移到末尾（LRU）
                    self.cache.move_to_end(key)
                    return self.cache[key].copy()
                else:
                    # 过期，删除
                    del self.cache[key]
                    del self.timestamps[key]
        return None
    
    def put(self, key: str, image: np.ndarray):
        """存储图像到缓存"""
        with self.lock:
            # 如果已存在，更新
            if key in self.cache:
                self.cache[key] = image.copy()
                self.timestamps[key] = time.time()
                self.cache.move_to_end(key)
                return
            
            # 检查缓存大小
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            # 添加新图像
            self.cache[key] = image.copy()
            self.timestamps[key] = time.time()
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'memory_usage_mb': sum(img.nbytes for img in self.cache.values()) / 1024 / 1024
            }

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        self.metrics = {
            'screenshot_count': 0,
            'detection_count': 0,
            'trade_count': 0,
            'memory_usage': [],
            'cpu_usage': [],
            'processing_times': []
        }
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5分钟
    
    def record_screenshot(self):
        """记录截图操作"""
        self.metrics['screenshot_count'] += 1
    
    def record_detection(self, processing_time: float):
        """记录检测操作"""
        self.metrics['detection_count'] += 1
        self.metrics['processing_times'].append(processing_time)
        
        # 保持最近1000次记录
        if len(self.metrics['processing_times']) > 1000:
            self.metrics['processing_times'] = self.metrics['processing_times'][-1000:]
    
    def record_trade(self):
        """记录交易操作"""
        self.metrics['trade_count'] += 1
    
    def update_system_metrics(self):
        """更新系统指标"""
        try:
            # 内存使用率
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'].append({
                'timestamp': time.time(),
                'percent': memory.percent,
                'available_gb': memory.available / 1024 / 1024 / 1024
            })
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=None)
            self.metrics['cpu_usage'].append({
                'timestamp': time.time(),
                'percent': cpu_percent
            })
            
            # 保持最近100个记录
            for key in ['memory_usage', 'cpu_usage']:
                if len(self.metrics[key]) > 100:
                    self.metrics[key] = self.metrics[key][-100:]
                    
        except Exception as e:
            self.logger.error(f"更新系统指标失败: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        self.update_system_metrics()
        
        # 计算平均处理时间
        avg_processing_time = 0
        if self.metrics['processing_times']:
            avg_processing_time = sum(self.metrics['processing_times']) / len(self.metrics['processing_times'])
        
        # 计算运行时间
        runtime = time.time() - self.start_time
        
        # 获取当前内存和CPU使用率
        current_memory = self.metrics['memory_usage'][-1] if self.metrics['memory_usage'] else {'percent': 0}
        current_cpu = self.metrics['cpu_usage'][-1] if self.metrics['cpu_usage'] else {'percent': 0}
        
        return {
            'runtime_hours': runtime / 3600,
            'screenshot_count': self.metrics['screenshot_count'],
            'detection_count': self.metrics['detection_count'],
            'trade_count': self.metrics['trade_count'],
            'avg_processing_time_ms': avg_processing_time * 1000,
            'current_memory_percent': current_memory['percent'],
            'current_cpu_percent': current_cpu['percent'],
            'screenshots_per_hour': self.metrics['screenshot_count'] / (runtime / 3600) if runtime > 0 else 0,
            'detections_per_hour': self.metrics['detection_count'] / (runtime / 3600) if runtime > 0 else 0
        }

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        # 初始化组件
        self.image_cache = ImageCache()
        self.monitor = PerformanceMonitor()
        
        # 优化参数
        self.load_optimization_config()
        
        # 自适应参数
        self.adaptive_screenshot_interval = 5.0
        self.last_screenshot_time = 0
        self.last_detection_time = 0
        
        self.logger.info("性能优化器初始化完成")
    
    def load_optimization_config(self):
        """加载优化配置"""
        if self.config_manager:
            perf_config = self.config_manager.get('performance', {})
            self.enable_screenshot_optimization = perf_config.get('screenshot_optimization', True)
            self.enable_image_cache = perf_config.get('image_cache_enabled', True)
            self.max_cache_size = perf_config.get('max_cache_size', 100)
            self.memory_cleanup_interval = perf_config.get('memory_cleanup_interval', 300)
            self.cpu_usage_limit = perf_config.get('cpu_usage_limit', 80)
            self.max_concurrent_operations = perf_config.get('max_concurrent_operations', 3)
        else:
            # 默认值
            self.enable_screenshot_optimization = True
            self.enable_image_cache = True
            self.max_cache_size = 100
            self.memory_cleanup_interval = 300
            self.cpu_usage_limit = 80
            self.max_concurrent_operations = 3
    
    def should_take_screenshot(self) -> bool:
        """判断是否应该截图"""
        if not self.enable_screenshot_optimization:
            return True
        
        current_time = time.time()
        
        # 基础间隔检查
        if current_time - self.last_screenshot_time < self.adaptive_screenshot_interval:
            return False
        
        # CPU使用率检查
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            if cpu_percent > self.cpu_usage_limit:
                # CPU使用率过高，延长截图间隔
                self.adaptive_screenshot_interval = min(10.0, self.adaptive_screenshot_interval * 1.2)
                return False
            else:
                # CPU使用率正常，恢复截图间隔
                self.adaptive_screenshot_interval = max(3.0, self.adaptive_screenshot_interval * 0.9)
        except:
            pass
        
        return True
    
    def optimize_image(self, image: np.ndarray, operation: str = "detection") -> np.ndarray:
        """优化图像处理"""
        try:
            # 根据操作类型优化
            if operation == "yellow_line_detection":
                # 黄线检测：降低分辨率，提高处理速度
                height, width = image.shape[:2]
                if width > 1920:
                    scale = 1920 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            elif operation == "ocr":
                # OCR识别：增强对比度，提高识别准确性
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image
                
                # 自适应直方图均衡化
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                image = clahe.apply(gray)
                
                # 放大图像提高OCR准确性
                image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            
            return image
            
        except Exception as e:
            self.logger.error(f"图像优化失败: {e}")
            return image
    
    def get_cached_image(self, key: str) -> Optional[np.ndarray]:
        """获取缓存图像"""
        if self.enable_image_cache:
            return self.image_cache.get(key)
        return None
    
    def cache_image(self, key: str, image: np.ndarray):
        """缓存图像"""
        if self.enable_image_cache:
            self.image_cache.put(key, image)
    
    def cleanup_memory(self):
        """清理内存"""
        try:
            # 清理图像缓存
            if self.enable_image_cache:
                cache_stats = self.image_cache.get_stats()
                if cache_stats['memory_usage_mb'] > 100:  # 超过100MB清理
                    self.image_cache.clear()
                    self.logger.info("图像缓存已清理")
            
            # 强制垃圾回收
            gc.collect()
            
            # 记录内存使用情况
            memory = psutil.virtual_memory()
            self.logger.info(f"内存清理完成，当前使用率: {memory.percent}%")
            
        except Exception as e:
            self.logger.error(f"内存清理失败: {e}")
    
    def auto_cleanup(self):
        """自动清理"""
        current_time = time.time()
        if current_time - self.monitor.last_cleanup > self.memory_cleanup_interval:
            self.cleanup_memory()
            self.monitor.last_cleanup = current_time
    
    def record_operation(self, operation: str, processing_time: float):
        """记录操作"""
        if operation == "screenshot":
            self.monitor.record_screenshot()
            self.last_screenshot_time = time.time()
        elif operation == "detection":
            self.monitor.record_detection(processing_time)
            self.last_detection_time = time.time()
        elif operation == "trade":
            self.monitor.record_trade()
        
        # 自动清理检查
        self.auto_cleanup()
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计"""
        perf_stats = self.monitor.get_performance_stats()
        cache_stats = self.image_cache.get_stats()
        
        return {
            'performance': perf_stats,
            'cache': cache_stats,
            'optimization': {
                'screenshot_optimization_enabled': self.enable_screenshot_optimization,
                'image_cache_enabled': self.enable_image_cache,
                'adaptive_screenshot_interval': self.adaptive_screenshot_interval,
                'cpu_usage_limit': self.cpu_usage_limit
            }
        }
    
    def adjust_performance_settings(self, cpu_usage: float, memory_usage: float):
        """根据系统负载调整性能设置"""
        try:
            # 根据CPU使用率调整
            if cpu_usage > 90:
                self.adaptive_screenshot_interval = min(15.0, self.adaptive_screenshot_interval * 1.5)
                self.logger.warning(f"CPU使用率过高({cpu_usage}%)，调整截图间隔至{self.adaptive_screenshot_interval}秒")
            elif cpu_usage < 50:
                self.adaptive_screenshot_interval = max(3.0, self.adaptive_screenshot_interval * 0.8)
            
            # 根据内存使用率调整
            if memory_usage > 85:
                self.cleanup_memory()
                self.logger.warning(f"内存使用率过高({memory_usage}%)，执行内存清理")
            
        except Exception as e:
            self.logger.error(f"调整性能设置失败: {e}")

# 全局性能优化器实例
performance_optimizer = PerformanceOptimizer()
