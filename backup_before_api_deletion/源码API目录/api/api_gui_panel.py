#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API管理GUI面板
为景陶易购API功能提供图形化管理界面
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QTabWidget,
    QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox,
    QMessageBox, QProgressBar, QFrame
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QPalette

try:
    from .api_integration_manager import APIIntegrationManager, TradingMode, TradingSignal
except ImportError:
    from api_integration_manager import APIIntegrationManager, TradingMode, TradingSignal

class APIStatusWidget(QWidget):
    """API状态显示组件"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QGridLayout(self)
        
        # 连接状态
        self.connection_label = QLabel("连接状态:")
        self.connection_status = QLabel("未连接")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        
        # 交易状态
        self.trading_label = QLabel("交易状态:")
        self.trading_status = QLabel("已禁用")
        self.trading_status.setStyleSheet("color: orange; font-weight: bold;")
        
        # 交易模式
        self.mode_label = QLabel("交易模式:")
        self.mode_status = QLabel("手动")
        
        # 今日订单
        self.orders_label = QLabel("今日订单:")
        self.orders_count = QLabel("0/100")
        
        layout.addWidget(self.connection_label, 0, 0)
        layout.addWidget(self.connection_status, 0, 1)
        layout.addWidget(self.trading_label, 0, 2)
        layout.addWidget(self.trading_status, 0, 3)
        layout.addWidget(self.mode_label, 1, 0)
        layout.addWidget(self.mode_status, 1, 1)
        layout.addWidget(self.orders_label, 1, 2)
        layout.addWidget(self.orders_count, 1, 3)
    
    def update_status(self, status: Dict[str, Any]):
        """更新状态显示"""
        # 连接状态
        if status.get("api_connected", False):
            self.connection_status.setText("已连接")
            self.connection_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connection_status.setText("未连接")
            self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        
        # 交易状态
        if status.get("trading_enabled", False):
            self.trading_status.setText("已启用")
            self.trading_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.trading_status.setText("已禁用")
            self.trading_status.setStyleSheet("color: orange; font-weight: bold;")
        
        # 交易模式
        mode_map = {
            "manual": "手动",
            "semi_auto": "半自动",
            "full_auto": "全自动"
        }
        mode = status.get("trading_mode", "manual")
        self.mode_status.setText(mode_map.get(mode, "未知"))
        
        # 订单计数
        daily_count = status.get("daily_order_count", 0)
        max_count = status.get("max_daily_orders", 100)
        self.orders_count.setText(f"{daily_count}/{max_count}")

class APIControlPanel(QWidget):
    """API控制面板"""
    
    # 信号定义
    connect_requested = pyqtSignal(str, str, int)
    disconnect_requested = pyqtSignal()
    trading_mode_changed = pyqtSignal(str)
    trading_enabled_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 连接设置组
        connection_group = QGroupBox("连接设置")
        connection_layout = QGridLayout(connection_group)
        
        # 手机号
        connection_layout.addWidget(QLabel("手机号:"), 0, 0)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("请输入手机号")
        connection_layout.addWidget(self.phone_input, 0, 1)
        
        # 密码
        connection_layout.addWidget(QLabel("密码:"), 1, 0)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("请输入密码")
        connection_layout.addWidget(self.password_input, 1, 1)
        
        # 市场ID
        connection_layout.addWidget(QLabel("市场ID:"), 2, 0)
        self.market_id_input = QSpinBox()
        self.market_id_input.setRange(1, 999)
        self.market_id_input.setValue(28)
        connection_layout.addWidget(self.market_id_input, 2, 1)
        
        # 连接按钮
        button_layout = QHBoxLayout()
        self.connect_button = QPushButton("连接")
        self.connect_button.clicked.connect(self.on_connect_clicked)
        self.disconnect_button = QPushButton("断开")
        self.disconnect_button.clicked.connect(self.on_disconnect_clicked)
        self.disconnect_button.setEnabled(False)
        
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.disconnect_button)
        connection_layout.addLayout(button_layout, 3, 0, 1, 2)
        
        layout.addWidget(connection_group)
        
        # 交易设置组
        trading_group = QGroupBox("交易设置")
        trading_layout = QGridLayout(trading_group)
        
        # 交易模式
        trading_layout.addWidget(QLabel("交易模式:"), 0, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["手动", "半自动", "全自动"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        trading_layout.addWidget(self.mode_combo, 0, 1)
        
        # 启用交易
        self.trading_enabled_checkbox = QCheckBox("启用交易")
        self.trading_enabled_checkbox.stateChanged.connect(self.on_trading_enabled_changed)
        trading_layout.addWidget(self.trading_enabled_checkbox, 1, 0, 1, 2)
        
        layout.addWidget(trading_group)
        
        # 风险设置组
        risk_group = QGroupBox("风险设置")
        risk_layout = QGridLayout(risk_group)
        
        # 日订单限制
        risk_layout.addWidget(QLabel("日订单限制:"), 0, 0)
        self.max_orders_input = QSpinBox()
        self.max_orders_input.setRange(1, 1000)
        self.max_orders_input.setValue(100)
        risk_layout.addWidget(self.max_orders_input, 0, 1)
        
        # 最大持仓
        risk_layout.addWidget(QLabel("最大持仓:"), 1, 0)
        self.max_position_input = QSpinBox()
        self.max_position_input.setRange(1, 100)
        self.max_position_input.setValue(10)
        risk_layout.addWidget(self.max_position_input, 1, 1)
        
        # 最小信号置信度
        risk_layout.addWidget(QLabel("最小置信度:"), 2, 0)
        self.min_confidence_input = QDoubleSpinBox()
        self.min_confidence_input.setRange(0.0, 1.0)
        self.min_confidence_input.setSingleStep(0.1)
        self.min_confidence_input.setValue(0.6)
        risk_layout.addWidget(self.min_confidence_input, 2, 1)
        
        layout.addWidget(risk_group)
        
        # 快速操作组
        quick_group = QGroupBox("快速操作")
        quick_layout = QVBoxLayout(quick_group)
        
        self.cancel_all_button = QPushButton("撤销所有订单")
        self.cancel_all_button.setStyleSheet("background-color: #ff6b6b; color: white;")
        self.cancel_all_button.setEnabled(False)
        quick_layout.addWidget(self.cancel_all_button)
        
        layout.addWidget(quick_group)
    
    def on_connect_clicked(self):
        """连接按钮点击"""
        phone = self.phone_input.text().strip()
        password = self.password_input.text().strip()
        market_id = self.market_id_input.value()
        
        if not phone or not password:
            QMessageBox.warning(self, "警告", "请输入手机号和密码")
            return
        
        self.connect_requested.emit(phone, password, market_id)
    
    def on_disconnect_clicked(self):
        """断开按钮点击"""
        self.disconnect_requested.emit()
    
    def on_mode_changed(self, text):
        """交易模式改变"""
        mode_map = {
            "手动": "manual",
            "半自动": "semi_auto",
            "全自动": "full_auto"
        }
        mode = mode_map.get(text, "manual")
        self.trading_mode_changed.emit(mode)
    
    def on_trading_enabled_changed(self, state):
        """交易启用状态改变"""
        enabled = state == Qt.Checked
        self.trading_enabled_changed.emit(enabled)
    
    def set_connected(self, connected: bool):
        """设置连接状态"""
        self.connect_button.setEnabled(not connected)
        self.disconnect_button.setEnabled(connected)
        self.cancel_all_button.setEnabled(connected)
        
        # 禁用/启用输入框
        self.phone_input.setEnabled(not connected)
        self.password_input.setEnabled(not connected)
        self.market_id_input.setEnabled(not connected)

class APIGUIPanel(QWidget):
    """API管理GUI主面板"""
    
    def __init__(self, api_manager: APIIntegrationManager):
        super().__init__()
        self.api_manager = api_manager
        self.logger = logging.getLogger(__name__)
        
        # 设置回调
        self.api_manager.on_connection_status_changed = self.on_connection_status_changed
        self.api_manager.on_order_filled = self.on_order_filled
        self.api_manager.on_order_failed = self.on_order_failed
        
        self.init_ui()
        self.setup_timer()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("景陶易购API管理")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 状态显示
        self.status_widget = APIStatusWidget()
        layout.addWidget(self.status_widget)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 控制面板
        self.control_panel = APIControlPanel()
        self.control_panel.connect_requested.connect(self.on_connect_requested)
        self.control_panel.disconnect_requested.connect(self.on_disconnect_requested)
        self.control_panel.trading_mode_changed.connect(self.on_trading_mode_changed)
        self.control_panel.trading_enabled_changed.connect(self.on_trading_enabled_changed)
        layout.addWidget(self.control_panel)
        
        # 日志显示
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
    
    def setup_timer(self):
        """设置定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # 每秒更新一次
    
    def update_status(self):
        """更新状态显示"""
        try:
            status = self.api_manager.get_status()
            self.status_widget.update_status(status)
        except Exception as e:
            self.logger.error(f"更新状态异常: {e}")
    
    def on_connect_requested(self, phone: str, password: str, market_id: int):
        """处理连接请求"""
        self.log_message(f"正在连接API... 手机号: {phone}")
        
        success = self.api_manager.connect(phone, password, market_id)
        
        if success:
            self.log_message("✅ API连接成功")
            self.control_panel.set_connected(True)
        else:
            self.log_message("❌ API连接失败")
            QMessageBox.critical(self, "错误", "API连接失败，请检查账号密码")
    
    def on_disconnect_requested(self):
        """处理断开请求"""
        self.api_manager.disconnect()
        self.log_message("🔌 API已断开连接")
        self.control_panel.set_connected(False)
    
    def on_trading_mode_changed(self, mode: str):
        """处理交易模式改变"""
        mode_enum = TradingMode(mode)
        self.api_manager.set_trading_mode(mode_enum)
        self.log_message(f"🔧 交易模式已设置为: {mode}")
    
    def on_trading_enabled_changed(self, enabled: bool):
        """处理交易启用状态改变"""
        self.api_manager.enable_trading(enabled)
        status = "启用" if enabled else "禁用"
        self.log_message(f"🎯 交易功能已{status}")
    
    def on_connection_status_changed(self, connected: bool):
        """连接状态改变回调"""
        status = "连接" if connected else "断开"
        self.log_message(f"🔗 连接状态: {status}")
        self.control_panel.set_connected(connected)
    
    def on_order_filled(self, order_record):
        """订单成交回调"""
        signal = order_record.signal
        self.log_message(f"✅ 订单成交: {signal.action} {signal.commodity_id} @{order_record.fill_price}")
    
    def on_order_failed(self, order_record):
        """订单失败回调"""
        signal = order_record.signal
        self.log_message(f"❌ 订单失败: {signal.action} {signal.commodity_id} - {order_record.error_message}")
    
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # 限制日志行数
        if self.log_text.document().blockCount() > 100:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
    
    def submit_signal(self, action: str, commodity_id: str, price: float, 
                     quantity: int, confidence: float = 0.8, reason: str = "手动信号"):
        """提交交易信号（供外部调用）"""
        signal = TradingSignal(
            action=action,
            commodity_id=commodity_id,
            price=price,
            quantity=quantity,
            confidence=confidence,
            reason=reason,
            timestamp=datetime.now()
        )
        
        success = self.api_manager.submit_trading_signal(signal)
        
        if success:
            self.log_message(f"📤 交易信号已提交: {action} {commodity_id}")
        else:
            self.log_message(f"❌ 交易信号提交失败: {action} {commodity_id}")
        
        return success
