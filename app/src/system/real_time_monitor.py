#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控和报警系统
全方位监控交易系统运行状态并提供智能预警
"""

import time
import logging
import threading
import json
import smtplib
import os
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import psutil
import queue
import requests
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class AlertLevel(Enum):
    """报警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(Enum):
    """报警类型"""
    SYSTEM_ERROR = "system_error"
    TRADING_ERROR = "trading_error"
    RISK_WARNING = "risk_warning"
    PERFORMANCE_ISSUE = "performance_issue"
    CONNECTIVITY_ISSUE = "connectivity_issue"
    STRATEGY_ANOMALY = "strategy_anomaly"

@dataclass
class Alert:
    """报警信息"""
    timestamp: float
    level: AlertLevel
    alert_type: AlertType
    title: str
    message: str
    details: Dict = None
    acknowledged: bool = False
    resolved: bool = False

@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    active_threads: int
    open_files: int

@dataclass
class TradingMetrics:
    """交易指标"""
    timestamp: float
    total_trades: int
    successful_trades: int
    failed_trades: int
    total_pnl: float
    daily_pnl: float
    win_rate: float
    avg_trade_time: float
    strategy_signals: Dict

class RealTimeMonitor:
    """实时监控系统"""
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # 监控配置
        self.monitor_interval = self.config.get('monitor_interval', 5)  # 5秒
        self.alert_cooldown = self.config.get('alert_cooldown', 300)  # 5分钟
        self.max_alerts = self.config.get('max_alerts', 1000)
        
        # 阈值配置
        self.thresholds = self.config.get('thresholds', {
            'cpu_usage': 85.0,
            'memory_usage': 90.0,
            'disk_usage': 95.0,
            'network_latency': 1000.0,  # ms
            'error_rate': 0.1,  # 10%
            'daily_loss': 0.05,  # 5%
            'drawdown': 0.15,  # 15%
            'response_time': 5.0  # 秒
        })
        
        # 数据存储
        self.alerts: List[Alert] = []
        self.system_metrics: List[SystemMetrics] = []
        self.trading_metrics: List[TradingMetrics] = []
        self.last_alert_time: Dict[str, float] = {}
        
        # 线程管理
        self.monitor_threads = {}
        self.running = False
        self.alert_queue = queue.Queue()
        
        # 通知方式
        self.notification_channels = {
            'email': self._send_email_alert,
            'webhook': self._send_webhook_alert,
            'log': self._log_alert,
            'file': self._write_alert_to_file
        }
        
        # 性能统计
        self.performance_stats = {
            'total_alerts': 0,
            'alerts_by_level': {level.value: 0 for level in AlertLevel},
            'alerts_by_type': {alert_type.value: 0 for alert_type in AlertType},
            'system_uptime': time.time(),
            'last_heartbeat': time.time()
        }
        
        self.logger.info("实时监控系统初始化完成")
    
    def start_monitoring(self, components: List[str] = None):
        """启动监控"""
        try:
            self.running = True
            
            # 默认监控组件
            if components is None:
                components = ['system', 'trading', 'alerts', 'heartbeat']
            
            # 启动各个监控线程
            for component in components:
                if component == 'system':
                    self._start_system_monitor()
                elif component == 'trading':
                    self._start_trading_monitor()
                elif component == 'alerts':
                    self._start_alert_processor()
                elif component == 'heartbeat':
                    self._start_heartbeat_monitor()
            
            self.logger.info(f"监控系统已启动，监控组件: {components}")
            
        except Exception as e:
            self.logger.error(f"启动监控失败: {e}")
            self.running = False
    
    def stop_monitoring(self):
        """停止监控"""
        try:
            self.running = False
            
            # 等待所有线程结束
            for thread_name, thread in self.monitor_threads.items():
                if thread.is_alive():
                    thread.join(timeout=5)
                    self.logger.info(f"监控线程 {thread_name} 已停止")
            
            self.logger.info("监控系统已停止")
            
        except Exception as e:
            self.logger.error(f"停止监控失败: {e}")
    
    def _start_system_monitor(self):
        """启动系统监控"""
        def system_monitor_loop():
            while self.running:
                try:
                    # 收集系统指标
                    metrics = self._collect_system_metrics()
                    self.system_metrics.append(metrics)
                    
                    # 限制历史数据量
                    if len(self.system_metrics) > 1000:
                        self.system_metrics.pop(0)
                    
                    # 检查系统阈值
                    self._check_system_thresholds(metrics)
                    
                    time.sleep(self.monitor_interval)
                    
                except Exception as e:
                    self.logger.error(f"系统监控错误: {e}")
                    time.sleep(30)
        
        thread = threading.Thread(target=system_monitor_loop, name="SystemMonitor")
        thread.daemon = True
        thread.start()
        self.monitor_threads['system'] = thread
    
    def _start_trading_monitor(self):
        """启动交易监控"""
        def trading_monitor_loop():
            while self.running:
                try:
                    # 收集交易指标
                    metrics = self._collect_trading_metrics()
                    if metrics:
                        self.trading_metrics.append(metrics)
                        
                        # 限制历史数据量
                        if len(self.trading_metrics) > 1000:
                            self.trading_metrics.pop(0)
                        
                        # 检查交易阈值
                        self._check_trading_thresholds(metrics)
                    
                    time.sleep(self.monitor_interval * 2)  # 交易监控频率稍低
                    
                except Exception as e:
                    self.logger.error(f"交易监控错误: {e}")
                    time.sleep(30)
        
        thread = threading.Thread(target=trading_monitor_loop, name="TradingMonitor")
        thread.daemon = True
        thread.start()
        self.monitor_threads['trading'] = thread
    
    def _start_alert_processor(self):
        """启动报警处理器"""
        def alert_processor_loop():
            while self.running:
                try:
                    # 处理队列中的报警
                    try:
                        alert = self.alert_queue.get(timeout=1)
                        self._process_alert(alert)
                        self.alert_queue.task_done()
                    except queue.Empty:
                        continue
                        
                except Exception as e:
                    self.logger.error(f"报警处理错误: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=alert_processor_loop, name="AlertProcessor")
        thread.daemon = True
        thread.start()
        self.monitor_threads['alerts'] = thread
    
    def _start_heartbeat_monitor(self):
        """启动心跳监控"""
        def heartbeat_loop():
            while self.running:
                try:
                    self.performance_stats['last_heartbeat'] = time.time()
                    
                    # 检查各组件健康状态
                    self._check_component_health()
                    
                    time.sleep(30)  # 30秒心跳
                    
                except Exception as e:
                    self.logger.error(f"心跳监控错误: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=heartbeat_loop, name="HeartbeatMonitor")
        thread.daemon = True
        thread.start()
        self.monitor_threads['heartbeat'] = thread
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # 网络延迟（ping本地回环）
            network_latency = self._measure_network_latency()
            
            # 活跃线程数
            active_threads = threading.active_count()
            
            # 打开文件数
            try:
                process = psutil.Process()
                open_files = len(process.open_files())
            except:
                open_files = 0
            
            return SystemMetrics(
                timestamp=time.time(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_latency=network_latency,
                active_threads=active_threads,
                open_files=open_files
            )
            
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
            return SystemMetrics(
                timestamp=time.time(),
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_latency=0.0,
                active_threads=0,
                open_files=0
            )
    
    def _collect_trading_metrics(self) -> Optional[TradingMetrics]:
        """收集交易指标"""
        try:
            # 这里需要从实际的交易系统组件获取数据
            # 暂时返回模拟数据
            current_time = time.time()
            
            # 模拟数据 - 实际应该从交易引擎获取
            return TradingMetrics(
                timestamp=current_time,
                total_trades=100,
                successful_trades=85,
                failed_trades=15,
                total_pnl=1500.0,
                daily_pnl=50.0,
                win_rate=0.65,
                avg_trade_time=2.5,
                strategy_signals={'buy': 45, 'sell': 40, 'hold': 15}
            )
            
        except Exception as e:
            self.logger.error(f"收集交易指标失败: {e}")
            return None
    
    def _measure_network_latency(self) -> float:
        """测量网络延迟"""
        try:
            start_time = time.time()
            socket.create_connection(("127.0.0.1", 80), timeout=5)
            end_time = time.time()
            return (end_time - start_time) * 1000  # 转换为毫秒
        except:
            return float('inf')
    
    def _check_system_thresholds(self, metrics: SystemMetrics):
        """检查系统阈值"""
        try:
            # CPU使用率检查
            if metrics.cpu_usage > self.thresholds['cpu_usage']:
                self.create_alert(
                    AlertLevel.WARNING,
                    AlertType.PERFORMANCE_ISSUE,
                    "CPU使用率过高",
                    f"CPU使用率: {metrics.cpu_usage:.1f}%，超过阈值 {self.thresholds['cpu_usage']}%",
                    {'cpu_usage': metrics.cpu_usage}
                )
            
            # 内存使用率检查
            if metrics.memory_usage > self.thresholds['memory_usage']:
                self.create_alert(
                    AlertLevel.ERROR,
                    AlertType.PERFORMANCE_ISSUE,
                    "内存使用率过高",
                    f"内存使用率: {metrics.memory_usage:.1f}%，超过阈值 {self.thresholds['memory_usage']}%",
                    {'memory_usage': metrics.memory_usage}
                )
            
            # 磁盘使用率检查
            if metrics.disk_usage > self.thresholds['disk_usage']:
                self.create_alert(
                    AlertLevel.CRITICAL,
                    AlertType.SYSTEM_ERROR,
                    "磁盘空间不足",
                    f"磁盘使用率: {metrics.disk_usage:.1f}%，超过阈值 {self.thresholds['disk_usage']}%",
                    {'disk_usage': metrics.disk_usage}
                )
            
            # 网络延迟检查
            if metrics.network_latency > self.thresholds['network_latency']:
                self.create_alert(
                    AlertLevel.WARNING,
                    AlertType.CONNECTIVITY_ISSUE,
                    "网络延迟过高",
                    f"网络延迟: {metrics.network_latency:.1f}ms，超过阈值 {self.thresholds['network_latency']}ms",
                    {'network_latency': metrics.network_latency}
                )
                
        except Exception as e:
            self.logger.error(f"系统阈值检查失败: {e}")
    
    def _check_trading_thresholds(self, metrics: TradingMetrics):
        """检查交易阈值"""
        try:
            # 错误率检查
            if metrics.total_trades > 0:
                error_rate = metrics.failed_trades / metrics.total_trades
                if error_rate > self.thresholds['error_rate']:
                    self.create_alert(
                        AlertLevel.ERROR,
                        AlertType.TRADING_ERROR,
                        "交易错误率过高",
                        f"错误率: {error_rate:.2%}，超过阈值 {self.thresholds['error_rate']:.2%}",
                        {'error_rate': error_rate, 'failed_trades': metrics.failed_trades}
                    )
            
            # 日亏损检查
            if metrics.daily_pnl < 0:
                daily_loss_rate = abs(metrics.daily_pnl) / 10000  # 假设初始资金10000
                if daily_loss_rate > self.thresholds['daily_loss']:
                    self.create_alert(
                        AlertLevel.CRITICAL,
                        AlertType.RISK_WARNING,
                        "日亏损超过限制",
                        f"日亏损: {metrics.daily_pnl:.2f}，亏损率: {daily_loss_rate:.2%}",
                        {'daily_pnl': metrics.daily_pnl, 'loss_rate': daily_loss_rate}
                    )
            
            # 胜率异常检查
            if metrics.win_rate < 0.3:  # 胜率低于30%
                self.create_alert(
                    AlertLevel.WARNING,
                    AlertType.STRATEGY_ANOMALY,
                    "胜率异常偏低",
                    f"胜率: {metrics.win_rate:.2%}，可能存在策略问题",
                    {'win_rate': metrics.win_rate}
                )
                
        except Exception as e:
            self.logger.error(f"交易阈值检查失败: {e}")
    
    def _check_component_health(self):
        """检查组件健康状态"""
        try:
            current_time = time.time()
            
            # 检查各监控线程状态
            for thread_name, thread in self.monitor_threads.items():
                if not thread.is_alive():
                    self.create_alert(
                        AlertLevel.CRITICAL,
                        AlertType.SYSTEM_ERROR,
                        f"监控线程 {thread_name} 已停止",
                        f"监控线程 {thread_name} 意外停止，系统监控能力受损",
                        {'thread_name': thread_name}
                    )
            
            # 检查数据更新时间
            if self.system_metrics:
                last_system_update = self.system_metrics[-1].timestamp
                if current_time - last_system_update > 60:  # 超过1分钟未更新
                    self.create_alert(
                        AlertLevel.ERROR,
                        AlertType.SYSTEM_ERROR,
                        "系统指标更新停滞",
                        f"系统指标已超过 {current_time - last_system_update:.0f} 秒未更新",
                        {'last_update': last_system_update}
                    )
                    
        except Exception as e:
            self.logger.error(f"组件健康检查失败: {e}")
    
    def create_alert(self, level: AlertLevel, alert_type: AlertType, 
                    title: str, message: str, details: Dict = None):
        """创建报警"""
        try:
            # 检查报警冷却
            alert_key = f"{alert_type.value}_{title}"
            current_time = time.time()
            
            if alert_key in self.last_alert_time:
                if current_time - self.last_alert_time[alert_key] < self.alert_cooldown:
                    return  # 在冷却期内，跳过重复报警
            
            # 创建报警对象
            alert = Alert(
                timestamp=current_time,
                level=level,
                alert_type=alert_type,
                title=title,
                message=message,
                details=details or {}
            )
            
            # 添加到队列处理
            self.alert_queue.put(alert)
            
            # 更新最后报警时间
            self.last_alert_time[alert_key] = current_time
            
            # 更新统计
            self.performance_stats['total_alerts'] += 1
            self.performance_stats['alerts_by_level'][level.value] += 1
            self.performance_stats['alerts_by_type'][alert_type.value] += 1
            
        except Exception as e:
            self.logger.error(f"创建报警失败: {e}")
    
    def _process_alert(self, alert: Alert):
        """处理报警"""
        try:
            # 添加到历史记录
            self.alerts.append(alert)
            if len(self.alerts) > self.max_alerts:
                self.alerts.pop(0)
            
            # 根据配置发送通知
            enabled_channels = self.config.get('notification_channels', ['log'])
            
            for channel in enabled_channels:
                if channel in self.notification_channels:
                    try:
                        self.notification_channels[channel](alert)
                    except Exception as e:
                        self.logger.error(f"通知渠道 {channel} 发送失败: {e}")
            
            self.logger.info(f"报警已处理: {alert.level.value} - {alert.title}")
            
        except Exception as e:
            self.logger.error(f"处理报警失败: {e}")
    
    def _send_email_alert(self, alert: Alert):
        """发送邮件报警"""
        try:
            email_config = self.config.get('email', {})
            if not email_config:
                return
            
            smtp_server = email_config.get('smtp_server')
            smtp_port = email_config.get('smtp_port', 587)
            username = email_config.get('username')
            password = email_config.get('password')
            to_emails = email_config.get('to_emails', [])
            
            if not all([smtp_server, username, password, to_emails]):
                return
            
            # 创建邮件
            msg = MimeMultipart()
            msg['From'] = username
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"[{alert.level.value.upper()}] {alert.title}"
            
            # 邮件内容
            body = f"""
            报警时间: {datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
            报警级别: {alert.level.value}
            报警类型: {alert.alert_type.value}
            报警标题: {alert.title}
            报警消息: {alert.message}
            
            详细信息:
            {json.dumps(alert.details, indent=2, ensure_ascii=False) if alert.details else '无'}
            """
            
            msg.attach(MimeText(body, 'plain', 'utf-8'))
            
            # 发送邮件
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"发送邮件报警失败: {e}")
    
    def _send_webhook_alert(self, alert: Alert):
        """发送Webhook报警"""
        try:
            webhook_config = self.config.get('webhook', {})
            if not webhook_config:
                return
            
            url = webhook_config.get('url')
            if not url:
                return
            
            # 构造payload
            payload = {
                'timestamp': alert.timestamp,
                'level': alert.level.value,
                'type': alert.alert_type.value,
                'title': alert.title,
                'message': alert.message,
                'details': alert.details
            }
            
            # 发送POST请求
            response = requests.post(
                url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            
        except Exception as e:
            self.logger.error(f"发送Webhook报警失败: {e}")
    
    def _log_alert(self, alert: Alert):
        """记录报警到日志"""
        log_message = f"[{alert.level.value.upper()}] {alert.alert_type.value}: {alert.title} - {alert.message}"
        
        if alert.level == AlertLevel.CRITICAL:
            self.logger.critical(log_message)
        elif alert.level == AlertLevel.ERROR:
            self.logger.error(log_message)
        elif alert.level == AlertLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _write_alert_to_file(self, alert: Alert):
        """将报警写入文件"""
        try:
            alert_file = self.config.get('alert_file', 'alerts.json')
            
            alert_data = {
                'timestamp': alert.timestamp,
                'datetime': datetime.fromtimestamp(alert.timestamp).isoformat(),
                'level': alert.level.value,
                'type': alert.alert_type.value,
                'title': alert.title,
                'message': alert.message,
                'details': alert.details
            }
            
            # 追加到文件
            with open(alert_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(alert_data, ensure_ascii=False) + '\n')
                
        except Exception as e:
            self.logger.error(f"写入报警文件失败: {e}")
    
    def get_monitoring_status(self) -> Dict:
        """获取监控状态"""
        try:
            current_time = time.time()
            
            # 基本状态
            status = {
                'running': self.running,
                'uptime': current_time - self.performance_stats['system_uptime'],
                'last_heartbeat': current_time - self.performance_stats['last_heartbeat'],
                'total_alerts': self.performance_stats['total_alerts'],
                'alerts_by_level': self.performance_stats['alerts_by_level'].copy(),
                'alerts_by_type': self.performance_stats['alerts_by_type'].copy()
            }
            
            # 线程状态
            status['threads'] = {
                name: thread.is_alive() 
                for name, thread in self.monitor_threads.items()
            }
            
            # 最新指标
            if self.system_metrics:
                status['latest_system_metrics'] = asdict(self.system_metrics[-1])
            
            if self.trading_metrics:
                status['latest_trading_metrics'] = asdict(self.trading_metrics[-1])
            
            # 近期报警
            recent_alerts = [
                {
                    'timestamp': alert.timestamp,
                    'level': alert.level.value,
                    'type': alert.alert_type.value,
                    'title': alert.title,
                    'acknowledged': alert.acknowledged,
                    'resolved': alert.resolved
                }
                for alert in self.alerts[-10:]  # 最近10条
            ]
            status['recent_alerts'] = recent_alerts
            
            return status
            
        except Exception as e:
            self.logger.error(f"获取监控状态失败: {e}")
            return {'error': str(e)}
    
    def acknowledge_alert(self, alert_index: int) -> bool:
        """确认报警"""
        try:
            if 0 <= alert_index < len(self.alerts):
                self.alerts[alert_index].acknowledged = True
                return True
            return False
        except Exception as e:
            self.logger.error(f"确认报警失败: {e}")
            return False
    
    def resolve_alert(self, alert_index: int) -> bool:
        """解决报警"""
        try:
            if 0 <= alert_index < len(self.alerts):
                self.alerts[alert_index].resolved = True
                return True
            return False
        except Exception as e:
            self.logger.error(f"解决报警失败: {e}")
            return False

if __name__ == "__main__":
    # 测试配置
    config = {
        'monitor_interval': 5,
        'notification_channels': ['log', 'file'],
        'alert_file': 'test_alerts.json',
        'thresholds': {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'daily_loss': 0.03
        }
    }
    
    # 创建监控实例
    monitor = RealTimeMonitor(config)
    
    # 启动监控
    monitor.start_monitoring()
    
    # 模拟报警
    monitor.create_alert(
        AlertLevel.WARNING,
        AlertType.PERFORMANCE_ISSUE,
        "测试报警",
        "这是一个测试报警消息"
    )
    
    # 运行一段时间
    time.sleep(10)
    
    # 获取状态
    status = monitor.get_monitoring_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    # 停止监控
    monitor.stop_monitoring()