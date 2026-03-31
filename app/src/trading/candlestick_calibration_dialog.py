#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K线颜色校准对话框
专门用于K线颜色校准的集成对话框
"""

import os
import sys
import json
import time
import cv2
import numpy as np
import pyautogui
import threading
from datetime import datetime
from typing import Dict, Optional, Tuple

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QPlainTextEdit, QProgressBar, QMessageBox, QTabWidget,
    QWidget, QGroupBox, QGridLayout, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QSlider, QFormLayout, QSplitter,
    QListWidget, QListWidgetItem, QFileDialog
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap, QImage

class CandlestickCalibrationWorker(QThread):
    """K线校准工作线程"""
    
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, mode='calibrate', chart_area=None, color_ranges=None):
        super().__init__()
        self.mode = mode  # 'calibrate', 'test', 'area_select'
        self.chart_area = chart_area or {
            'x': 0.05, 'y': 0.12, 'width': 0.65, 'height': 0.55
        }
        self.color_ranges = color_ranges or self.get_default_color_ranges()
        self.running = True
    
    def get_default_color_ranges(self):
        """获取默认颜色范围"""
        return {
            'red': {
                'lower1': [0, 50, 50],
                'upper1': [10, 255, 255],
                'lower2': [170, 50, 50],
                'upper2': [180, 255, 255]
            },
            'blue': {
                'lower': [80, 50, 50],
                'upper': [110, 255, 255]
            },
            'cyan': {
                'lower': [85, 100, 200],
                'upper': [95, 255, 255]
            },
            'green': {
                'lower': [35, 50, 50],
                'upper': [85, 255, 255]
            }
        }
    
    def run(self):
        """执行校准任务"""
        try:
            if self.mode == 'calibrate':
                self.run_calibration()
            elif self.mode == 'test':
                self.run_test()
            elif self.mode == 'area_select':
                self.run_area_selection()
        except Exception as e:
            self.error_signal.emit(f"校准任务失败: {e}")
    
    def run_calibration(self):
        """执行颜色校准"""
        self.progress_signal.emit("📸 正在截取屏幕...")
        
        # 截取屏幕
        screenshot = pyautogui.screenshot()
        screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # 提取K线图区域
        self.progress_signal.emit("📊 提取K线图区域...")
        chart_region = self.extract_chart_region(screenshot_np)
        
        if chart_region is None:
            self.error_signal.emit("无法提取K线图区域，请检查区域设置")
            return
        
        # 保存调试图像
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_dir = f"logs/candlestick_calibration_{timestamp}"
        os.makedirs(debug_dir, exist_ok=True)
        
        chart_path = os.path.join(debug_dir, "chart_region.jpg")
        cv2.imwrite(chart_path, chart_region)
        
        # 转换为HSV
        hsv = cv2.cvtColor(chart_region, cv2.COLOR_BGR2HSV)
        
        # 检测各种颜色
        self.progress_signal.emit("🎨 分析颜色分布...")
        results = {}
        
        for color_name in ['red', 'blue', 'cyan', 'green']:
            if not self.running:
                return
                
            self.progress_signal.emit(f"🔍 检测 {color_name} 颜色...")
            
            if color_name == 'red':
                # 红色需要两个范围
                mask1 = cv2.inRange(hsv, 
                                  np.array(self.color_ranges[color_name]['lower1']),
                                  np.array(self.color_ranges[color_name]['upper1']))
                mask2 = cv2.inRange(hsv,
                                  np.array(self.color_ranges[color_name]['lower2']),
                                  np.array(self.color_ranges[color_name]['upper2']))
                mask = cv2.bitwise_or(mask1, mask2)
            else:
                mask = cv2.inRange(hsv,
                                 np.array(self.color_ranges[color_name]['lower']),
                                 np.array(self.color_ranges[color_name]['upper']))
            
            # 查找轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            valid_contours = [c for c in contours if cv2.contourArea(c) >= 20]
            
            results[color_name] = len(valid_contours)
            
            # 保存调试图像
            mask_path = os.path.join(debug_dir, f"{color_name}_mask.jpg")
            cv2.imwrite(mask_path, mask)
            
            # 绘制检测结果
            result_img = chart_region.copy()
            for contour in valid_contours:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(result_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(result_img, color_name[:3].upper(), (x, y-5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            
            result_path = os.path.join(debug_dir, f"{color_name}_detection.jpg")
            cv2.imwrite(result_path, result_img)
        
        self.progress_signal.emit("✅ 颜色校准完成")
        
        # 返回结果
        result_data = {
            'detection_results': results,
            'debug_dir': debug_dir,
            'chart_path': chart_path,
            'total_detections': sum(results.values())
        }
        
        self.result_signal.emit(result_data)
    
    def run_test(self):
        """执行检测测试"""
        self.progress_signal.emit("🧪 执行检测测试...")
        # 与校准类似，但侧重于实时检测效果
        self.run_calibration()  # 复用校准逻辑
    
    def run_area_selection(self):
        """执行区域选择"""
        self.progress_signal.emit("📍 启动区域选择...")
        
        try:
            # 截取屏幕
            screenshot = pyautogui.screenshot()
            screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 使用OpenCV的selectROI
            window_name = '选择K线图区域 - 拖拽选择后按SPACE确认'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 1200, 800)
            
            roi = cv2.selectROI(window_name, screenshot_np, False, False)
            cv2.destroyAllWindows()
            
            if roi[2] > 0 and roi[3] > 0:
                # 转换为相对坐标
                screen_width, screen_height = screenshot.size
                
                area_config = {
                    'x': roi[0] / screen_width,
                    'y': roi[1] / screen_height,
                    'width': roi[2] / screen_width,
                    'height': roi[3] / screen_height
                }
                
                self.result_signal.emit({'area_config': area_config})
                self.progress_signal.emit("✅ 区域选择完成")
            else:
                self.error_signal.emit("未选择有效区域")
                
        except Exception as e:
            self.error_signal.emit(f"区域选择失败: {e}")
    
    def extract_chart_region(self, screenshot):
        """从截图中提取K线图区域"""
        try:
            height, width = screenshot.shape[:2]
            
            # 计算绝对坐标
            x = int(width * self.chart_area['x'])
            y = int(height * self.chart_area['y'])
            w = int(width * self.chart_area['width'])
            h = int(height * self.chart_area['height'])
            
            # 确保坐标在有效范围内
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = max(1, min(w, width - x))
            h = max(1, min(h, height - y))
            
            # 提取区域
            chart_region = screenshot[y:y+h, x:x+w]
            
            if chart_region.size == 0:
                return None
                
            return chart_region
            
        except Exception:
            return None
    
    def stop(self):
        """停止工作线程"""
        self.running = False

class CandlestickCalibrationDialog(QDialog):
    """K线校准对话框"""
    
    def __init__(self, parent=None, trading_engine=None):
        super().__init__(parent)
        self.trading_engine = trading_engine
        self.worker = None
        
        # 配置文件路径
        self.config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'config'
        )
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.area_config_file = os.path.join(self.config_dir, 'candlestick_area_config.json')
        self.color_config_file = os.path.join(self.config_dir, 'candlestick_color_config.json')
        
        # 当前配置
        self.chart_area = {'x': 0.05, 'y': 0.12, 'width': 0.65, 'height': 0.55}
        self.color_ranges = self.get_default_color_ranges()
        
        # 加载配置
        self.load_configurations()
        
        self.setup_ui()
        self.setup_connections()
        
        self.setWindowTitle("K线颜色校准工具")
        self.setGeometry(200, 200, 900, 700)
        self.setModal(True)
    
    def get_default_color_ranges(self):
        """获取默认颜色范围"""
        return {
            'red': {
                'lower1': [0, 50, 50],
                'upper1': [10, 255, 255],
                'lower2': [170, 50, 50],
                'upper2': [180, 255, 255]
            },
            'blue': {
                'lower': [80, 50, 50],
                'upper': [110, 255, 255]
            },
            'cyan': {
                'lower': [85, 100, 200],
                'upper': [95, 255, 255]
            },
            'green': {
                'lower': [35, 50, 50],
                'upper': [85, 255, 255]
            }
        }
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("🎨 K线颜色校准工具")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 区域设置标签页
        self.setup_area_tab()
        
        # 颜色校准标签页
        self.setup_calibration_tab()
        
        # 测试标签页
        self.setup_test_tab()
        
        # 进度和状态
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 保存配置")
        self.load_btn = QPushButton("📁 加载配置")
        self.reset_btn = QPushButton("🔄 重置默认")
        self.close_btn = QPushButton("❌ 关闭")
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def setup_area_tab(self):
        """设置区域配置标签页"""
        area_tab = QWidget()
        layout = QVBoxLayout(area_tab)
        
        # 说明
        info_label = QLabel(
            "设置K线图在屏幕中的位置（相对坐标 0-1）\n"
            "提示：左上角为(0,0)，右下角为(1,1)"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 当前区域显示
        current_group = QGroupBox("当前区域设置")
        current_layout = QFormLayout(current_group)
        
        self.x_spinbox = QDoubleSpinBox()
        self.x_spinbox.setRange(0.0, 1.0)
        self.x_spinbox.setSingleStep(0.01)
        self.x_spinbox.setDecimals(3)
        self.x_spinbox.setValue(self.chart_area['x'])
        current_layout.addRow("左边界 (X):", self.x_spinbox)
        
        self.y_spinbox = QDoubleSpinBox()
        self.y_spinbox.setRange(0.0, 1.0)
        self.y_spinbox.setSingleStep(0.01)
        self.y_spinbox.setDecimals(3)
        self.y_spinbox.setValue(self.chart_area['y'])
        current_layout.addRow("上边界 (Y):", self.y_spinbox)
        
        self.width_spinbox = QDoubleSpinBox()
        self.width_spinbox.setRange(0.1, 1.0)
        self.width_spinbox.setSingleStep(0.01)
        self.width_spinbox.setDecimals(3)
        self.width_spinbox.setValue(self.chart_area['width'])
        current_layout.addRow("宽度:", self.width_spinbox)
        
        self.height_spinbox = QDoubleSpinBox()
        self.height_spinbox.setRange(0.1, 1.0)
        self.height_spinbox.setSingleStep(0.01)
        self.height_spinbox.setDecimals(3)
        self.height_spinbox.setValue(self.chart_area['height'])
        current_layout.addRow("高度:", self.height_spinbox)
        
        layout.addWidget(current_group)
        
        # 区域选择按钮
        area_buttons = QHBoxLayout()
        
        self.select_area_btn = QPushButton("🖱️ 交互式选择区域")
        self.apply_area_btn = QPushButton("✅ 应用区域设置")
        
        area_buttons.addWidget(self.select_area_btn)
        area_buttons.addWidget(self.apply_area_btn)
        
        layout.addLayout(area_buttons)
        layout.addStretch()
        
        self.tab_widget.addTab(area_tab, "📍 区域设置")
    
    def setup_calibration_tab(self):
        """设置颜色校准标签页"""
        calibration_tab = QWidget()
        layout = QVBoxLayout(calibration_tab)
        
        # 校准控制
        control_group = QGroupBox("校准控制")
        control_layout = QVBoxLayout(control_group)
        
        calibration_buttons = QHBoxLayout()
        
        self.calibrate_btn = QPushButton("🎨 开始颜色校准")
        self.calibrate_btn.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        
        calibration_buttons.addWidget(self.calibrate_btn)
        control_layout.addLayout(calibration_buttons)
        
        layout.addWidget(control_group)
        
        # 结果显示
        result_group = QGroupBox("校准结果")
        result_layout = QVBoxLayout(result_group)
        
        self.result_text = QPlainTextEdit()
        self.result_text.setMaximumHeight(200)
        result_layout.addWidget(self.result_text)
        
        layout.addWidget(result_group)
        
        # 调试信息
        debug_group = QGroupBox("调试信息")
        debug_layout = QVBoxLayout(debug_group)
        
        self.debug_text = QPlainTextEdit()
        self.debug_text.setMaximumHeight(150)
        debug_layout.addWidget(self.debug_text)
        
        debug_buttons = QHBoxLayout()
        self.open_debug_btn = QPushButton("📁 打开调试目录")
        debug_buttons.addWidget(self.open_debug_btn)
        debug_buttons.addStretch()
        debug_layout.addLayout(debug_buttons)
        
        layout.addWidget(debug_group)
        
        self.tab_widget.addTab(calibration_tab, "🎨 颜色校准")
    
    def setup_test_tab(self):
        """设置测试标签页"""
        test_tab = QWidget()
        layout = QVBoxLayout(test_tab)
        
        # 测试控制
        test_group = QGroupBox("检测测试")
        test_layout = QVBoxLayout(test_group)
        
        test_buttons = QHBoxLayout()
        
        self.test_btn = QPushButton("🧪 测试检测效果")
        self.test_btn.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        
        test_buttons.addWidget(self.test_btn)
        test_layout.addLayout(test_buttons)
        
        layout.addWidget(test_group)
        
        # 实时统计
        stats_group = QGroupBox("检测统计")
        stats_layout = QGridLayout(stats_group)
        
        stats_layout.addWidget(QLabel("红色K线:"), 0, 0)
        self.red_count_label = QLabel("0")
        stats_layout.addWidget(self.red_count_label, 0, 1)
        
        stats_layout.addWidget(QLabel("蓝色K线:"), 0, 2)
        self.blue_count_label = QLabel("0")
        stats_layout.addWidget(self.blue_count_label, 0, 3)
        
        stats_layout.addWidget(QLabel("青色K线:"), 1, 0)
        self.cyan_count_label = QLabel("0")
        stats_layout.addWidget(self.cyan_count_label, 1, 1)
        
        stats_layout.addWidget(QLabel("绿色K线:"), 1, 2)
        self.green_count_label = QLabel("0")
        stats_layout.addWidget(self.green_count_label, 1, 3)
        
        layout.addWidget(stats_group)
        
        # 测试日志
        log_group = QGroupBox("测试日志")
        log_layout = QVBoxLayout(log_group)
        
        self.test_log = QPlainTextEdit()
        log_layout.addWidget(self.test_log)
        
        layout.addWidget(log_group)
        
        self.tab_widget.addTab(test_tab, "🧪 检测测试")
    
    def setup_connections(self):
        """设置信号连接"""
        # 区域设置
        self.select_area_btn.clicked.connect(self.select_area_interactive)
        self.apply_area_btn.clicked.connect(self.apply_area_settings)
        
        # 颜色校准
        self.calibrate_btn.clicked.connect(self.start_calibration)
        
        # 测试
        self.test_btn.clicked.connect(self.start_test)
        
        # 底部按钮
        self.save_btn.clicked.connect(self.save_configuration)
        self.load_btn.clicked.connect(self.load_configuration_file)
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        self.close_btn.clicked.connect(self.close)
        
        # 调试
        self.open_debug_btn.clicked.connect(self.open_debug_directory)
        
        # SpinBox值变化
        self.x_spinbox.valueChanged.connect(self.update_area_from_spinboxes)
        self.y_spinbox.valueChanged.connect(self.update_area_from_spinboxes)
        self.width_spinbox.valueChanged.connect(self.update_area_from_spinboxes)
        self.height_spinbox.valueChanged.connect(self.update_area_from_spinboxes)
    
    def update_area_from_spinboxes(self):
        """从spinbox更新区域设置"""
        self.chart_area = {
            'x': self.x_spinbox.value(),
            'y': self.y_spinbox.value(),
            'width': self.width_spinbox.value(),
            'height': self.height_spinbox.value()
        }
    
    def select_area_interactive(self):
        """交互式选择区域"""
        self.update_status("启动交互式区域选择...")
        self.calibrate_btn.setEnabled(False)
        self.test_btn.setEnabled(False)
        
        self.worker = CandlestickCalibrationWorker('area_select', self.chart_area, self.color_ranges)
        self.worker.progress_signal.connect(self.update_status)
        self.worker.result_signal.connect(self.on_area_selection_result)
        self.worker.error_signal.connect(self.on_worker_error)
        self.worker.start()
    
    def on_area_selection_result(self, result):
        """处理区域选择结果"""
        if 'area_config' in result:
            self.chart_area = result['area_config']
            
            # 更新界面
            self.x_spinbox.setValue(self.chart_area['x'])
            self.y_spinbox.setValue(self.chart_area['y'])
            self.width_spinbox.setValue(self.chart_area['width'])
            self.height_spinbox.setValue(self.chart_area['height'])
            
            self.update_status("✅ 区域选择完成")
            
            # 自动保存区域配置
            self.save_area_config()
        
        self.calibrate_btn.setEnabled(True)
        self.test_btn.setEnabled(True)
    
    def apply_area_settings(self):
        """应用区域设置"""
        self.update_area_from_spinboxes()
        self.save_area_config()
        self.update_status("✅ 区域设置已应用并保存")
    
    def start_calibration(self):
        """开始颜色校准"""
        self.update_status("开始K线颜色校准...")
        self.result_text.clear()
        self.debug_text.clear()
        
        self.calibrate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        self.worker = CandlestickCalibrationWorker('calibrate', self.chart_area, self.color_ranges)
        self.worker.progress_signal.connect(self.update_status)
        self.worker.result_signal.connect(self.on_calibration_result)
        self.worker.error_signal.connect(self.on_worker_error)
        self.worker.start()
    
    def on_calibration_result(self, result):
        """处理校准结果"""
        detection_results = result.get('detection_results', {})
        debug_dir = result.get('debug_dir', '')
        total_detections = result.get('total_detections', 0)
        
        # 显示结果
        result_text = "🎨 K线颜色校准结果:\n\n"
        
        for color_name, count in detection_results.items():
            status = "✅" if count > 0 else "❌"
            result_text += f"{status} {color_name}: {count} 个色块\n"
        
        result_text += f"\n📈 总计检测到: {total_detections} 个K线色块\n"
        
        if total_detections > 0:
            result_text += "\n✅ 校准成功！检测到K线色块。"
        else:
            result_text += "\n⚠️ 未检测到K线色块，可能需要调整:\n"
            result_text += "  1. K线图区域设置\n"
            result_text += "  2. 颜色范围参数\n"
            result_text += "  3. 确保当前显示K线图"
        
        self.result_text.setPlainText(result_text)
        
        # 显示调试信息
        debug_text = f"📁 调试文件保存位置: {debug_dir}\n\n"
        debug_text += "🖼️ 生成的调试图像:\n"
        debug_text += "  - chart_region.jpg: K线图区域\n"
        debug_text += "  - *_mask.jpg: 各颜色掩码\n"
        debug_text += "  - *_detection.jpg: 检测结果\n"
        
        self.debug_text.setPlainText(debug_text)
        
        self.update_status("✅ 颜色校准完成")
        self.calibrate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # 保存当前配置为校准结果
        self.save_color_config()
    
    def start_test(self):
        """开始测试"""
        self.update_status("开始检测测试...")
        self.test_log.clear()
        
        self.test_btn.setEnabled(False)
        
        self.worker = CandlestickCalibrationWorker('test', self.chart_area, self.color_ranges)
        self.worker.progress_signal.connect(self.update_test_status)
        self.worker.result_signal.connect(self.on_test_result)
        self.worker.error_signal.connect(self.on_worker_error)
        self.worker.start()
    
    def on_test_result(self, result):
        """处理测试结果"""
        detection_results = result.get('detection_results', {})
        
        # 更新统计标签
        self.red_count_label.setText(str(detection_results.get('red', 0)))
        self.blue_count_label.setText(str(detection_results.get('blue', 0)))
        self.cyan_count_label.setText(str(detection_results.get('cyan', 0)))
        self.green_count_label.setText(str(detection_results.get('green', 0)))
        
        # 更新测试日志
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text = f"[{timestamp}] 检测结果:\n"
        for color, count in detection_results.items():
            log_text += f"  {color}: {count} 个\n"
        log_text += f"  总计: {sum(detection_results.values())} 个\n\n"
        
        self.test_log.appendPlainText(log_text)
        
        self.update_status("✅ 检测测试完成")
        self.test_btn.setEnabled(True)
    
    def update_test_status(self, message):
        """更新测试状态"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.test_log.appendPlainText(f"[{timestamp}] {message}")
        self.update_status(message)
    
    def on_worker_error(self, error_msg):
        """处理工作线程错误"""
        self.update_status(f"❌ {error_msg}")
        QMessageBox.warning(self, "错误", error_msg)
        
        self.calibrate_btn.setEnabled(True)
        self.test_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def update_status(self, message):
        """更新状态"""
        self.status_label.setText(message)
    
    def save_configuration(self):
        """保存所有配置"""
        success1 = self.save_area_config()
        success2 = self.save_color_config()
        
        if success1 and success2:
            self.update_status("✅ 所有配置已保存")
            QMessageBox.information(self, "保存成功", "所有配置已成功保存！")
        else:
            QMessageBox.warning(self, "保存失败", "部分配置保存失败，请检查权限")
    
    def save_area_config(self):
        """保存区域配置"""
        try:
            with open(self.area_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.chart_area, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.update_status(f"❌ 保存区域配置失败: {e}")
            return False
    
    def save_color_config(self):
        """保存颜色配置"""
        try:
            with open(self.color_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.color_ranges, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.update_status(f"❌ 保存颜色配置失败: {e}")
            return False
    
    def load_configuration_file(self):
        """从文件加载配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载配置文件", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新配置
                if 'area' in config:
                    self.chart_area.update(config['area'])
                if 'colors' in config:
                    self.color_ranges.update(config['colors'])
                
                self.update_ui_from_config()
                self.update_status("✅ 配置文件加载成功")
                
            except Exception as e:
                QMessageBox.warning(self, "加载失败", f"配置文件加载失败:\n{e}")
    
    def load_configurations(self):
        """加载配置文件"""
        # 加载区域配置
        try:
            if os.path.exists(self.area_config_file):
                with open(self.area_config_file, 'r', encoding='utf-8') as f:
                    self.chart_area.update(json.load(f))
        except Exception:
            pass
        
        # 加载颜色配置
        try:
            if os.path.exists(self.color_config_file):
                with open(self.color_config_file, 'r', encoding='utf-8') as f:
                    self.color_ranges.update(json.load(f))
        except Exception:
            pass
    
    def update_ui_from_config(self):
        """从配置更新界面"""
        self.x_spinbox.setValue(self.chart_area['x'])
        self.y_spinbox.setValue(self.chart_area['y'])
        self.width_spinbox.setValue(self.chart_area['width'])
        self.height_spinbox.setValue(self.chart_area['height'])
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        reply = QMessageBox.question(
            self, "重置确认", 
            "确定要重置为默认配置吗？这将清除所有自定义设置。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.chart_area = {'x': 0.05, 'y': 0.12, 'width': 0.65, 'height': 0.55}
            self.color_ranges = self.get_default_color_ranges()
            self.update_ui_from_config()
            self.update_status("✅ 已重置为默认配置")
    
    def open_debug_directory(self):
        """打开调试目录"""
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        if os.path.exists(logs_dir):
            os.startfile(logs_dir)
        else:
            QMessageBox.information(self, "提示", "调试目录不存在，请先执行校准操作")
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)
        event.accept()