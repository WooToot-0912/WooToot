#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新管理器
负责检查和处理软件更新
"""

import os
import sys
import json
import requests
import threading
import subprocess
from typing import Dict, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from version import VERSION, UPDATE_CHECK_URL, DOWNLOAD_URL, compare_versions

class UpdateManager(QObject):
    """更新管理器"""
    
    # 信号定义
    update_available = pyqtSignal(dict)  # 有更新可用
    update_downloaded = pyqtSignal(str)  # 更新下载完成
    update_error = pyqtSignal(str)       # 更新错误
    update_progress = pyqtSignal(int)    # 下载进度
    
    def __init__(self):
        super().__init__()
        self.current_version = VERSION
        self.update_info = None
        self.download_path = None
        
    def check_for_updates(self, silent=False):
        """检查更新（异步）"""
        def check_worker():
            try:
                response = requests.get(UPDATE_CHECK_URL, timeout=10)
                response.raise_for_status()
                
                server_info = response.json()
                latest_version = server_info.get('version', '0.0.0')
                
                if compare_versions(self.current_version, latest_version):
                    self.update_info = server_info
                    self.update_available.emit(server_info)
                elif not silent:
                    self.update_error.emit("已是最新版本")
                    
            except requests.RequestException as e:
                if not silent:
                    self.update_error.emit(f"检查更新失败: {e}")
            except Exception as e:
                if not silent:
                    self.update_error.emit(f"更新检查错误: {e}")
        
        thread = threading.Thread(target=check_worker, daemon=True)
        thread.start()
    
    def download_update(self, update_info: dict):
        """下载更新"""
        def download_worker():
            try:
                download_url = update_info.get('download_url')
                if not download_url:
                    self.update_error.emit("下载链接无效")
                    return
                
                # 创建下载目录
                download_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'JingTaoTrading')
                os.makedirs(download_dir, exist_ok=True)
                
                filename = f"景陶易购智能交易系统_v{update_info['version']}_安装程序.exe"
                self.download_path = os.path.join(download_dir, filename)
                
                # 下载文件
                response = requests.get(download_url, stream=True)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(self.download_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size > 0:
                                progress = int((downloaded / total_size) * 100)
                                self.update_progress.emit(progress)
                
                self.update_downloaded.emit(self.download_path)
                
            except Exception as e:
                self.update_error.emit(f"下载失败: {e}")
        
        thread = threading.Thread(target=download_worker, daemon=True)
        thread.start()
    
    def install_update(self):
        """安装更新"""
        if not self.download_path or not os.path.exists(self.download_path):
            self.update_error.emit("安装文件不存在")
            return
        
        try:
            # 启动安装程序
            subprocess.Popen([self.download_path], shell=True)
            
            # 退出当前程序
            sys.exit(0)
            
        except Exception as e:
            self.update_error.emit(f"安装失败: {e}")

class UpdateDialog:
    """更新对话框"""
    
    def __init__(self, parent, update_info: dict):
        self.parent = parent
        self.update_info = update_info
        self.update_manager = UpdateManager()
        
        # 连接信号
        self.update_manager.update_downloaded.connect(self.on_download_complete)
        self.update_manager.update_error.connect(self.on_update_error)
        self.update_manager.update_progress.connect(self.on_progress_update)
        
    def show_update_dialog(self):
        """显示更新对话框"""
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                     QLabel, QPushButton, QTextEdit, QProgressBar)
        
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("软件更新")
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel(f"发现新版本 v{self.update_info['version']}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")
        layout.addWidget(title)
        
        # 更新内容
        content = QTextEdit()
        content.setReadOnly(True)
        content.setMaximumHeight(200)
        
        update_text = f"""
发布日期: {self.update_info.get('release_date', 'N/A')}

新增功能:
{chr(10).join('• ' + f for f in self.update_info.get('features', []))}

问题修复:
{chr(10).join('• ' + f for f in self.update_info.get('fixes', []))}

文件大小: {self.update_info.get('file_size', 'N/A')}
        """
        
        content.setPlainText(update_text.strip())
        layout.addWidget(content)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        download_btn = QPushButton("立即更新")
        download_btn.clicked.connect(lambda: self.start_download(dialog))
        
        later_btn = QPushButton("稍后更新")
        later_btn.clicked.connect(dialog.reject)
        
        skip_btn = QPushButton("跳过此版本")
        skip_btn.clicked.connect(lambda: self.skip_version(dialog))
        
        button_layout.addWidget(download_btn)
        button_layout.addWidget(later_btn)
        button_layout.addWidget(skip_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        self.dialog = dialog
        return dialog.exec_()
    
    def start_download(self, dialog):
        """开始下载"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.update_manager.download_update(self.update_info)
    
    def on_progress_update(self, progress):
        """更新进度"""
        self.progress_bar.setValue(progress)
    
    def on_download_complete(self, file_path):
        """下载完成"""
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self.dialog, 
            "下载完成",
            "更新已下载完成，是否立即安装？\n\n注意：安装时会关闭当前程序",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.update_manager.install_update()
        else:
            self.dialog.accept()
    
    def on_update_error(self, error_msg):
        """更新错误"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(self.dialog, "更新失败", error_msg)
    
    def skip_version(self, dialog):
        """跳过版本"""
        # 可以在这里记录跳过的版本
        dialog.reject()

# 自动更新检查（程序启动时）
def check_updates_on_startup(main_window, silent=True):
    """程序启动时检查更新"""
    update_manager = UpdateManager()
    
    def on_update_available(update_info):
        if not silent:
            dialog = UpdateDialog(main_window, update_info)
            dialog.show_update_dialog()
    
    update_manager.update_available.connect(on_update_available)
    update_manager.check_for_updates(silent=silent)