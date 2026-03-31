#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据记录和分析模块
实现交易数据记录、统计分析、报告生成等功能
"""

import sqlite3
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import os
import threading

@dataclass
class TradeData:
    """交易数据"""
    id: Optional[int] = None
    timestamp: float = 0.0
    date: str = ""
    time_str: str = ""
    action: str = ""  # 'buy', 'sell', 'transfer'
    price: float = 0.0
    quantity: int = 0
    profit_loss: float = 0.0
    yellow_line_angle: float = 0.0
    signal_strength: float = 0.0
    success: bool = True
    error_message: str = ""
    processing_time: float = 0.0

@dataclass
class DetectionData:
    """检测数据"""
    id: Optional[int] = None
    timestamp: float = 0.0
    date: str = ""
    time_str: str = ""
    detection_type: str = ""  # 'yellow_line', 'profit_loss', 'price'
    detected_value: float = 0.0
    confidence: float = 0.0
    processing_time: float = 0.0
    success: bool = True
    error_message: str = ""

@dataclass
class SystemMetrics:
    """系统指标"""
    id: Optional[int] = None
    timestamp: float = 0.0
    date: str = ""
    time_str: str = ""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    screenshot_count: int = 0
    detection_count: int = 0
    trade_count: int = 0
    error_count: int = 0

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "trading_data.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock()
        
        # 初始化数据库
        self.init_database()
        
        self.logger.info(f"数据库管理器初始化完成: {db_path}")
    
    def init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 交易数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        date TEXT NOT NULL,
                        time_str TEXT NOT NULL,
                        action TEXT NOT NULL,
                        price REAL NOT NULL,
                        quantity INTEGER NOT NULL,
                        profit_loss REAL DEFAULT 0.0,
                        yellow_line_angle REAL DEFAULT 0.0,
                        signal_strength REAL DEFAULT 0.0,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT DEFAULT '',
                        processing_time REAL DEFAULT 0.0
                    )
                ''')
                
                # 检测数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS detections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        date TEXT NOT NULL,
                        time_str TEXT NOT NULL,
                        detection_type TEXT NOT NULL,
                        detected_value REAL NOT NULL,
                        confidence REAL DEFAULT 0.0,
                        processing_time REAL DEFAULT 0.0,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT DEFAULT ''
                    )
                ''')
                
                # 系统指标表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        date TEXT NOT NULL,
                        time_str TEXT NOT NULL,
                        cpu_usage REAL DEFAULT 0.0,
                        memory_usage REAL DEFAULT 0.0,
                        screenshot_count INTEGER DEFAULT 0,
                        detection_count INTEGER DEFAULT 0,
                        trade_count INTEGER DEFAULT 0,
                        error_count INTEGER DEFAULT 0
                    )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_detections_date ON detections(date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_detections_type ON detections(detection_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_date ON system_metrics(date)')
                
                conn.commit()
                self.logger.info("数据库表初始化完成")
                
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
    
    def insert_trade(self, trade: TradeData) -> bool:
        """插入交易数据"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO trades (
                            timestamp, date, time_str, action, price, quantity,
                            profit_loss, yellow_line_angle, signal_strength,
                            success, error_message, processing_time
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        trade.timestamp, trade.date, trade.time_str, trade.action,
                        trade.price, trade.quantity, trade.profit_loss,
                        trade.yellow_line_angle, trade.signal_strength,
                        trade.success, trade.error_message, trade.processing_time
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            self.logger.error(f"插入交易数据失败: {e}")
            return False
    
    def insert_detection(self, detection: DetectionData) -> bool:
        """插入检测数据"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO detections (
                            timestamp, date, time_str, detection_type,
                            detected_value, confidence, processing_time,
                            success, error_message
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        detection.timestamp, detection.date, detection.time_str,
                        detection.detection_type, detection.detected_value,
                        detection.confidence, detection.processing_time,
                        detection.success, detection.error_message
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            self.logger.error(f"插入检测数据失败: {e}")
            return False
    
    def insert_system_metrics(self, metrics: SystemMetrics) -> bool:
        """插入系统指标"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO system_metrics (
                            timestamp, date, time_str, cpu_usage, memory_usage,
                            screenshot_count, detection_count, trade_count, error_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        metrics.timestamp, metrics.date, metrics.time_str,
                        metrics.cpu_usage, metrics.memory_usage,
                        metrics.screenshot_count, metrics.detection_count,
                        metrics.trade_count, metrics.error_count
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            self.logger.error(f"插入系统指标失败: {e}")
            return False
    
    def get_trades_by_date(self, date: str) -> List[Dict]:
        """获取指定日期的交易数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM trades WHERE date = ? ORDER BY timestamp', (date,))
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"查询交易数据失败: {e}")
            return []
    
    def get_detections_by_date(self, date: str) -> List[Dict]:
        """获取指定日期的检测数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM detections WHERE date = ? ORDER BY timestamp', (date,))
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"查询检测数据失败: {e}")
            return []

class DataRecorder:
    """数据记录器"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        # 加载配置
        self.load_config()
        
        # 初始化数据库
        if self.recording_enabled:
            self.db_manager = DatabaseManager(self.database_path)
        else:
            self.db_manager = None
        
        # 统计计数器
        self.session_stats = {
            'trades': 0,
            'detections': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        self.logger.info(f"数据记录器初始化完成，记录功能: {'启用' if self.recording_enabled else '禁用'}")
    
    def load_config(self):
        """加载配置"""
        if self.config_manager:
            record_config = self.config_manager.get('data_recording', {})
            self.recording_enabled = record_config.get('enabled', True)
            self.database_path = record_config.get('database_path', 'trading_data.db')
            self.record_trades = record_config.get('record_trades', True)
            self.record_detections = record_config.get('record_signals', True)
            self.record_screenshots = record_config.get('record_screenshots', False)
        else:
            # 默认配置
            self.recording_enabled = True
            self.database_path = 'trading_data.db'
            self.record_trades = True
            self.record_detections = True
            self.record_screenshots = False
    
    def record_trade(self, action: str, price: float, quantity: int,
                    profit_loss: float = 0.0, yellow_line_angle: float = 0.0,
                    signal_strength: float = 0.0, success: bool = True,
                    error_message: str = "", processing_time: float = 0.0) -> bool:
        """记录交易"""
        if not self.recording_enabled or not self.record_trades or not self.db_manager:
            return True
        
        try:
            now = datetime.now()
            trade = TradeData(
                timestamp=time.time(),
                date=now.strftime('%Y-%m-%d'),
                time_str=now.strftime('%H:%M:%S'),
                action=action,
                price=price,
                quantity=quantity,
                profit_loss=profit_loss,
                yellow_line_angle=yellow_line_angle,
                signal_strength=signal_strength,
                success=success,
                error_message=error_message,
                processing_time=processing_time
            )
            
            result = self.db_manager.insert_trade(trade)
            if result:
                self.session_stats['trades'] += 1
                self.logger.info(f"交易记录已保存: {action} {price} {quantity}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"记录交易失败: {e}")
            return False
    
    def record_detection(self, detection_type: str, detected_value: float,
                        confidence: float = 0.0, processing_time: float = 0.0,
                        success: bool = True, error_message: str = "") -> bool:
        """记录检测"""
        if not self.recording_enabled or not self.record_detections or not self.db_manager:
            return True
        
        try:
            now = datetime.now()
            detection = DetectionData(
                timestamp=time.time(),
                date=now.strftime('%Y-%m-%d'),
                time_str=now.strftime('%H:%M:%S'),
                detection_type=detection_type,
                detected_value=detected_value,
                confidence=confidence,
                processing_time=processing_time,
                success=success,
                error_message=error_message
            )
            
            result = self.db_manager.insert_detection(detection)
            if result:
                self.session_stats['detections'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"记录检测失败: {e}")
            return False
    
    def record_system_metrics(self, cpu_usage: float, memory_usage: float,
                             screenshot_count: int, detection_count: int,
                             trade_count: int, error_count: int) -> bool:
        """记录系统指标"""
        if not self.recording_enabled or not self.db_manager:
            return True
        
        try:
            now = datetime.now()
            metrics = SystemMetrics(
                timestamp=time.time(),
                date=now.strftime('%Y-%m-%d'),
                time_str=now.strftime('%H:%M:%S'),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                screenshot_count=screenshot_count,
                detection_count=detection_count,
                trade_count=trade_count,
                error_count=error_count
            )
            
            return self.db_manager.insert_system_metrics(metrics)
            
        except Exception as e:
            self.logger.error(f"记录系统指标失败: {e}")
            return False
    
    def get_daily_summary(self, date: str = None) -> Dict[str, Any]:
        """获取日总结"""
        if not self.db_manager:
            return {}
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            trades = self.db_manager.get_trades_by_date(date)
            detections = self.db_manager.get_detections_by_date(date)
            
            # 计算交易统计
            total_trades = len(trades)
            successful_trades = len([t for t in trades if t['success']])
            total_profit_loss = sum(t['profit_loss'] for t in trades)
            
            # 计算检测统计
            total_detections = len(detections)
            successful_detections = len([d for d in detections if d['success']])
            avg_confidence = 0.0
            if successful_detections > 0:
                avg_confidence = sum(d['confidence'] for d in detections if d['success']) / successful_detections
            
            return {
                'date': date,
                'trades': {
                    'total': total_trades,
                    'successful': successful_trades,
                    'success_rate': successful_trades / total_trades if total_trades > 0 else 0,
                    'total_profit_loss': total_profit_loss
                },
                'detections': {
                    'total': total_detections,
                    'successful': successful_detections,
                    'success_rate': successful_detections / total_detections if total_detections > 0 else 0,
                    'average_confidence': avg_confidence
                },
                'session_stats': self.session_stats
            }
            
        except Exception as e:
            self.logger.error(f"获取日总结失败: {e}")
            return {}
    
    def export_data(self, start_date: str, end_date: str, export_path: str) -> bool:
        """导出数据"""
        if not self.db_manager:
            return False
        
        try:
            # 这里可以实现数据导出功能
            # 例如导出为CSV、Excel等格式
            self.logger.info(f"数据导出功能待实现: {start_date} 到 {end_date}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            return False

# 全局数据记录器实例
data_recorder = DataRecorder()
