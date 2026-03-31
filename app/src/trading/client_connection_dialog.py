#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端连接设置对话框
提供用户友好的客户端连接和自动登录配置界面
"""

import os
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QCheckBox, QPushButton, QTextEdit,
    QGroupBox, QGridLayout, QSpinBox, QMessageBox, QFrame,
    QProgressBar, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon

from .client_connection_manager import ClientConnectionManager, ConnectionStatus

class ClientConnectionDialog(QDialog):
    """客户端连接设置对话框"""
    
    def __init__(self, parent=None, connection_manager: ClientConnectionManager = None):
        super().__init__(parent)
        self.connection_manager = connection_manager
        self.parent_window = parent
        
        self.init_ui()
        self.load_current_settings()
        
        # 定时器用于实时状态更新
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_connection_status)
        self.status_timer.start(2000)  # 每2秒更新一次
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("客户端连接设置")
        self.setFixedSize(500, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 连接状态标签页
        self.create_status_tab()
        
        # 自动登录标签页
        self.create_login_tab()
        
        # 高级设置标签页
        self.create_advanced_tab()
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 测试连接按钮
        self.test_button = QPushButton("测试连接")
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)
        
        # 强制重连按钮
        self.reconnect_button = QPushButton("强制重连")
        self.reconnect_button.clicked.connect(self.force_reconnect)
        button_layout.addWidget(self.reconnect_button)
        
        # 刷新状态按钮
        self.refresh_button = QPushButton("刷新状态")
        self.refresh_button.clicked.connect(self.refresh_status)
        button_layout.addWidget(self.refresh_button)
        
        button_layout.addStretch()
        
        # 确定和取消按钮
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept_settings)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def create_status_tab(self):
        """创建连接状态标签页"""
        status_widget = QWidget()
        layout = QVBoxLayout(status_widget)
        
        # 当前连接状态组
        status_group = QGroupBox("当前连接状态")
        status_layout = QFormLayout(status_group)
        
        # 状态显示标签
        self.status_label = QLabel("检测中...")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        status_layout.addRow("连接状态:", self.status_label)
        
        # 客户端信息
        self.client_info_label = QLabel("未检测到客户端")
        status_layout.addRow("客户端:", self.client_info_label)
        
        # 上次检测时间
        self.last_check_label = QLabel("未知")
        status_layout.addRow("上次检测:", self.last_check_label)
        
        # 登录尝试次数
        self.login_attempts_label = QLabel("0")
        status_layout.addRow("登录尝试:", self.login_attempts_label)
        
        layout.addWidget(status_group)
        
        # 连接历史组
        history_group = QGroupBox("连接历史")
        history_layout = QVBoxLayout(history_group)
        
        self.status_log = QTextEdit()
        self.status_log.setMaximumHeight(150)
        self.status_log.setReadOnly(True)
        history_layout.addWidget(self.status_log)
        
        layout.addWidget(history_group)
        
        # 实时检测进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
        self.tab_widget.addTab(status_widget, "连接状态")
    
    def create_login_tab(self):
        """创建自动登录标签页"""
        login_widget = QWidget()
        layout = QVBoxLayout(login_widget)
        
        # 自动登录启用复选框
        self.auto_login_checkbox = QCheckBox("启用自动登录")
        self.auto_login_checkbox.toggled.connect(self.on_auto_login_toggled)
        layout.addWidget(self.auto_login_checkbox)
        
        # 登录凭据组
        self.credentials_group = QGroupBox("登录凭据")
        credentials_layout = QFormLayout(self.credentials_group)
        
        # 用户名输入
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入您的用户名/账号")
        credentials_layout.addRow("用户名:", self.username_input)
        
        # 密码输入
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("请输入您的密码")
        credentials_layout.addRow("密码:", self.password_input)
        
        # 显示密码复选框
        self.show_password_checkbox = QCheckBox("显示密码")
        self.show_password_checkbox.toggled.connect(self.toggle_password_visibility)
        credentials_layout.addRow("", self.show_password_checkbox)
        
        layout.addWidget(self.credentials_group)
        
        # 登录选项组
        options_group = QGroupBox("登录选项")
        options_layout = QFormLayout(options_group)
        
        # 最大登录尝试次数
        self.max_attempts_spinbox = QSpinBox()
        self.max_attempts_spinbox.setRange(1, 10)
        self.max_attempts_spinbox.setValue(3)
        options_layout.addRow("最大尝试次数:", self.max_attempts_spinbox)
        
        # 登录超时时间
        self.login_timeout_spinbox = QSpinBox()
        self.login_timeout_spinbox.setRange(5, 60)
        self.login_timeout_spinbox.setValue(10)
        self.login_timeout_spinbox.setSuffix(" 秒")
        options_layout.addRow("登录超时:", self.login_timeout_spinbox)
        
        layout.addWidget(options_group)
        
        # 注意事项
        note_label = QLabel(
            "注意事项:\n"
            "• 密码将被加密存储在配置文件中\n"
            "• 自动登录仅在检测到登录界面时触发\n" 
            "• 请确保客户端支持自动登录功能"
        )
        note_label.setStyleSheet("color: #666; font-size: 10px; padding: 10px;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        layout.addStretch()
        
        self.tab_widget.addTab(login_widget, "自动登录")
    
    def create_advanced_tab(self):
        """创建高级设置标签页"""
        advanced_widget = QWidget()
        layout = QVBoxLayout(advanced_widget)
        
        # 检测设置组
        detection_group = QGroupBox("检测设置")
        detection_layout = QFormLayout(detection_group)
        
        # 检测间隔
        self.check_interval_spinbox = QSpinBox()
        self.check_interval_spinbox.setRange(1, 30)
        self.check_interval_spinbox.setValue(5)
        self.check_interval_spinbox.setSuffix(" 秒")
        detection_layout.addRow("检测间隔:", self.check_interval_spinbox)
        
        # 客户端检测方法
        self.detection_method_combo = QComboBox()
        self.detection_method_combo.addItems([
            "增强检测器 (推荐)",
            "基础窗口检测", 
            "进程名称检测",
            "混合检测方法"
        ])
        detection_layout.addRow("检测方法:", self.detection_method_combo)
        
        layout.addWidget(detection_group)
        
        # 界面识别设置组
        ui_group = QGroupBox("界面识别设置")
        ui_layout = QFormLayout(ui_group)
        
        # OCR引擎选择
        self.ocr_engine_combo = QComboBox()
        self.ocr_engine_combo.addItems([
            "内置图像处理 (快速)",
            "Tesseract OCR (精确)", 
            "禁用OCR检测"
        ])
        ui_layout.addRow("OCR引擎:", self.ocr_engine_combo)
        
        # 界面检测精度
        self.ui_precision_spinbox = QSpinBox()
        self.ui_precision_spinbox.setRange(30, 90)
        self.ui_precision_spinbox.setValue(50)
        self.ui_precision_spinbox.setSuffix(" %")
        ui_layout.addRow("检测精度:", self.ui_precision_spinbox)
        
        layout.addWidget(ui_group)
        
        # 调试选项组
        debug_group = QGroupBox("调试选项")
        debug_layout = QVBoxLayout(debug_group)
        
        self.debug_mode_checkbox = QCheckBox("启用调试模式")
        debug_layout.addWidget(self.debug_mode_checkbox)
        
        self.save_screenshots_checkbox = QCheckBox("保存调试截图")
        debug_layout.addWidget(self.save_screenshots_checkbox)
        
        self.verbose_logging_checkbox = QCheckBox("详细日志记录")
        debug_layout.addWidget(self.verbose_logging_checkbox)
        
        layout.addWidget(debug_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(advanced_widget, "高级设置")
    
    def load_current_settings(self):
        """加载当前设置"""
        if not self.connection_manager:
            return
        
        try:
            # 加载连接信息
            connection_info = self.connection_manager.get_connection_info()
            
            # 设置自动登录状态
            self.auto_login_checkbox.setChecked(connection_info.get('auto_login_enabled', False))
            
            # 如果有保存的凭据，显示用户名（密码不显示）
            if connection_info.get('has_credentials', False):
                username = self.connection_manager.login_credentials.get('username', '')
                self.username_input.setText(username)
                self.password_input.setPlaceholderText("(已保存的密码)")
            
            # 更新连接状态
            self.update_connection_status()
            
        except Exception as e:
            self.status_log.append(f"❌ 加载设置失败: {e}")
    
    def on_auto_login_toggled(self, checked):
        """自动登录复选框状态改变"""
        self.credentials_group.setEnabled(checked)
        
        if self.connection_manager:
            self.connection_manager.enable_auto_login(checked)
    
    def toggle_password_visibility(self, show):
        """切换密码显示/隐藏"""
        if show:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def update_connection_status(self):
        """更新连接状态显示"""
        if not self.connection_manager:
            return
        
        try:
            # 检查连接状态
            status = self.connection_manager.check_connection_status()
            connection_info = self.connection_manager.get_connection_info()
            
            # 更新状态标签
            status_text = connection_info['status_text']
            self.status_label.setText(status_text)
            
            # 根据状态设置颜色
            if status == ConnectionStatus.CONNECTED:
                self.status_label.setStyleSheet("color: green; font-weight: bold; font-size: 12px;")
            elif status == ConnectionStatus.LOGIN_REQUIRED:
                self.status_label.setStyleSheet("color: orange; font-weight: bold; font-size: 12px;")
            elif status == ConnectionStatus.CONNECTING:
                self.status_label.setStyleSheet("color: blue; font-weight: bold; font-size: 12px;")
            else:
                self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 12px;")
            
            # 更新其他信息
            from datetime import datetime
            if connection_info['last_check_time'] > 0:
                check_time = datetime.fromtimestamp(connection_info['last_check_time'])
                self.last_check_label.setText(check_time.strftime("%H:%M:%S"))
            
            self.login_attempts_label.setText(str(connection_info['login_attempts']))
            
            # 更新客户端信息
            if self.connection_manager.enhanced_detector:
                try:
                    clients = self.connection_manager.enhanced_detector.detect_all_clients()
                    if clients:
                        best_client = max(clients, key=lambda x: x.get('score', 0))
                        client_info = f"{best_client['title']} (评分: {best_client['score']})"
                        self.client_info_label.setText(client_info)
                    else:
                        self.client_info_label.setText("未检测到客户端")
                except:
                    self.client_info_label.setText("检测器错误")
            
        except Exception as e:
            self.status_log.append(f"❌ 状态更新失败: {e}")
    
    def test_connection(self):
        """测试连接"""
        if not self.connection_manager:
            QMessageBox.warning(self, "错误", "连接管理器未初始化")
            return
        
        try:
            self.test_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 不确定进度
            
            self.status_log.append("🔍 开始连接测试...")
            
            # 强制检查连接状态
            self.connection_manager.force_reconnect()
            status = self.connection_manager.check_connection_status()
            
            self.status_log.append(f"✅ 测试完成，状态: {status.value}")
            
            # 显示结果
            connection_info = self.connection_manager.get_connection_info()
            result_msg = f"连接测试结果:\n\n状态: {connection_info['status_text']}"
            
            if status == ConnectionStatus.CONNECTED:
                QMessageBox.information(self, "测试成功", result_msg)
            else:
                QMessageBox.warning(self, "测试结果", result_msg)
                
        except Exception as e:
            error_msg = f"连接测试失败: {e}"
            self.status_log.append(f"❌ {error_msg}")
            QMessageBox.critical(self, "测试失败", error_msg)
        
        finally:
            self.test_button.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def force_reconnect(self):
        """强制重新连接"""
        if not self.connection_manager:
            return
        
        try:
            self.status_log.append("🔄 强制重新连接...")
            self.connection_manager.force_reconnect()
            self.status_log.append("✅ 重连完成")
            
            # 立即更新状态
            self.update_connection_status()
            
        except Exception as e:
            self.status_log.append(f"❌ 重连失败: {e}")
    
    def refresh_status(self):
        """刷新连接状态"""
        if not self.connection_manager:
            return
        
        try:
            self.status_log.append("🔄 刷新连接状态...")
            
            # 强制更新状态（无缓存）
            status = self.connection_manager.force_status_update()
            connection_info = self.connection_manager.get_connection_info()
            
            self.status_log.append(f"✅ 状态已刷新: {connection_info['status_text']}")
            
            # 立即更新界面显示
            self.update_connection_status()
            
        except Exception as e:
            self.status_log.append(f"❌ 状态刷新失败: {e}")
    
    def accept_settings(self):
        """应用设置并关闭对话框"""
        try:
            if not self.connection_manager:
                QMessageBox.warning(self, "错误", "连接管理器未初始化")
                return
            
            # 保存自动登录设置
            auto_login_enabled = self.auto_login_checkbox.isChecked()
            self.connection_manager.enable_auto_login(auto_login_enabled)
            
            # 保存登录凭据（如果启用了自动登录且填写了凭据）
            if auto_login_enabled:
                username = self.username_input.text().strip()
                password = self.password_input.text()
                
                if username and password:
                    self.connection_manager.set_login_credentials(username, password, save_to_config=True)
                    self.status_log.append("✅ 登录凭据已保存")
                elif username or password:
                    reply = QMessageBox.question(self, "确认", 
                                               "用户名或密码不完整，是否继续保存设置？",
                                               QMessageBox.Yes | QMessageBox.No)
                    if reply != QMessageBox.Yes:
                        return
            
            # 应用高级设置
            if hasattr(self.connection_manager, 'check_interval'):
                self.connection_manager.check_interval = self.check_interval_spinbox.value()
            
            # 应用登录选项
            if hasattr(self.connection_manager, 'max_login_attempts'):
                self.connection_manager.max_login_attempts = self.max_attempts_spinbox.value()
            
            self.status_log.append("✅ 设置已保存")
            self.accept()
            
        except Exception as e:
            error_msg = f"保存设置失败: {e}"
            self.status_log.append(f"❌ {error_msg}")
            QMessageBox.critical(self, "保存失败", error_msg)
    
    def closeEvent(self, event):
        """对话框关闭事件"""
        # 停止定时器
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        event.accept()