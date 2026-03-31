#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坐标校准对话框
集成到主界面的智能坐标校准工具
"""

import sys
import os
import json
import time
import cv2
import numpy as np
import pyautogui
import threading
from pathlib import Path
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QTextEdit, QProgressBar, QMessageBox,
                            QListWidget, QListWidgetItem, QSplitter,
                            QGroupBox, QGridLayout, QCheckBox, QSpinBox)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap, QImage

# 导入必要的模块
try:
    import win32gui
    import win32con
    import win32api
    import win32process
    WINDOWS_API_AVAILABLE = True
except ImportError:
    WINDOWS_API_AVAILABLE = False
    win32gui = None
    win32process = None
    print("⚠️ Windows API不可用，部分功能受限")

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR功能不可用")

class WindowDetector(QThread):
    """窗口检测线程 - 使用增强检测器"""
    
    windows_found = pyqtSignal(list)
    status_update = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
    
    def run(self):
        """检测所有窗口"""
        self.running = True
        self.status_update.emit("🔍 正在使用增强检测器扫描客户端...")
        
        try:
            # 导入增强的客户端检测器
            import sys
            import os
            tools_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tools')
            if tools_path not in sys.path:
                sys.path.append(tools_path)
            
            try:
                from enhanced_client_detector import JingTaoClientDetector
            except ImportError:
                # 如果导入失败，使用基础检测
                raise ImportError("Enhanced detector not available")
            
            # 使用增强检测器
            detector = JingTaoClientDetector()
            clients = detector.detect_all_clients()
            
            # 转换格式以兼容现有界面
            windows = []
            for client in clients:
                window_info = {
                    'hwnd': client['hwnd'],
                    'title': client['title'],
                    'class': client['class'],
                    'rect': client['rect'],
                    'width': client['width'],
                    'height': client['height'],
                    'is_potential_client': client['score'] > 3,  # 得分>3认为是潜在客户端
                    'score': client['score'],
                    'detection_method': client['detection_method'],
                    'process_info': client.get('process_info')
                }
                windows.append(window_info)
            
            # 按得分排序
            windows.sort(key=lambda w: (w['score']), reverse=True)
            
            self.windows_found.emit(windows)
            
            if windows:
                best_score = windows[0]['score']
                self.status_update.emit(f"✅ 找到 {len(windows)} 个窗口，最佳匹配得分: {best_score}")
            else:
                self.status_update.emit("❌ 未找到景陶易购客户端")
                
        except Exception as e:
            self.status_update.emit(f"❌ 客户端检测失败: {e}")
            # 降级到基础检测
            try:
                windows = self.basic_window_detection()
                self.windows_found.emit(windows)
                self.status_update.emit(f"⚠️ 使用基础检测，找到 {len(windows)} 个窗口")
            except Exception as e2:
                self.status_update.emit(f"❌ 基础检测也失败: {e2}")
                self.windows_found.emit([])
    
    def basic_window_detection(self):
        """基础窗口检测（降级方案）"""
        windows = []
        
        if not WINDOWS_API_AVAILABLE:
            return windows
        
        def enum_callback(hwnd, windows_list):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                
                window_text = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                except:
                    return True
                
                if width < 200 or height < 150:
                    return True
                
                # 简单的关键词匹配
                is_potential_client = False
                if window_text:
                    keywords = ['景陶', '易购', '交易', '证券', '股票', 'client', 'trading']
                    if any(keyword.lower() in window_text.lower() for keyword in keywords):
                        is_potential_client = True
                
                if window_text.strip() or is_potential_client:
                    window_info = {
                        'hwnd': hwnd,
                        'title': window_text or f"[{class_name}]",
                        'class': class_name,
                        'rect': rect,
                        'width': width,
                        'height': height,
                        'is_potential_client': is_potential_client,
                        'score': 5 if is_potential_client else 1,
                        'detection_method': 'basic',
                        'process_info': None
                    }
                    windows_list.append(window_info)
                
            except:
                pass
            return True
        
        try:
            win32gui.EnumWindows(enum_callback, windows)
        except:
            pass
        
        return windows

class CalibrationWorker(QThread):
    """校准工作线程"""
    
    progress_update = pyqtSignal(str)
    result_ready = pyqtSignal(dict)
    screenshot_ready = pyqtSignal(object)
    
    def __init__(self, window_info):
        super().__init__()
        self.window_info = window_info
        self.found_coords = {}
        
        # 按钮定义
        self.buttons = {
            'buy_mode_button': {
                'name': '买入模式按钮',
                'keywords': ['买', '买入', 'BUY', 'B'],
                'color_ranges': [
                    ([0, 50, 50], [10, 255, 255]),    # 红色1
                    ([170, 50, 50], [180, 255, 255])  # 红色2
                ],
                'description': '左侧红色买入按钮'
            },
            'sell_mode_button': {
                'name': '卖出模式按钮',
                'keywords': ['卖', '卖出', 'SELL', 'S'],
                'color_ranges': [
                    ([40, 50, 50], [80, 255, 255])    # 绿色
                ],
                'description': '左侧绿色卖出按钮'
            },
            'buy_order_button': {
                'name': '买入订立按钮',
                'keywords': ['买入订立', '订立', '买入确认'],
                'description': '底部买入订立按钮'
            },
            'sell_order_button': {
                'name': '卖出订立按钮',
                'keywords': ['卖出订立', '卖出确认'],
                'description': '底部卖出订立按钮'
            },
            'confirm_button': {
                'name': '确认按钮',
                'keywords': ['确定', '确认', 'OK', '是', '同意'],
                'description': '确认对话框按钮'
            },
            'price_input': {
                'name': '价格输入框',
                'keywords': ['价格', '委托价', '单价', '价'],
                'description': '价格输入区域'
            }
        }
    
    def run(self):
        """执行校准流程"""
        try:
            self.progress_update.emit("📸 正在截取窗口...")
            
            # 截取窗口
            screenshot = self.capture_window()
            if screenshot is None:
                self.progress_update.emit("❌ 截图失败")
                return
            
            self.screenshot_ready.emit(screenshot)
            self.progress_update.emit("✅ 截图成功")
            
            # 颜色检测
            self.progress_update.emit("🎨 进行颜色分析...")
            self.color_detection(screenshot)
            
            # OCR检测
            if OCR_AVAILABLE:
                self.progress_update.emit("📝 进行文字识别...")
                self.ocr_detection(screenshot)
            
            # 返回结果
            total_coords = sum(len(coords) for coords in self.found_coords.values())
            self.progress_update.emit(f"✅ 检测完成，找到 {total_coords} 个坐标候选")
            self.result_ready.emit(self.found_coords)
            
        except Exception as e:
            self.progress_update.emit(f"❌ 校准失败: {e}")
    
    def capture_window(self):
        """截取窗口"""
        try:
            hwnd = self.window_info['hwnd']
            rect = self.window_info['rect']
            
            # 尝试激活窗口
            try:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.5)
            except:
                self.progress_update.emit("⚠️ 无法激活窗口，继续截图")
            
            # 截图
            x, y, x2, y2 = rect
            screenshot = pyautogui.screenshot(region=(x, y, x2-x, y2-y))
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            return screenshot_cv
            
        except Exception as e:
            self.progress_update.emit(f"截图失败: {e}")
            return None
    
    def color_detection(self, screenshot):
        """颜色检测"""
        try:
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
            height, width = screenshot.shape[:2]
            
            # 检测红色区域（买入按钮）
            for color_ranges in [self.buttons['buy_mode_button']['color_ranges']]:
                mask = np.zeros((height, width), dtype=np.uint8)
                for lower, upper in color_ranges:
                    color_mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                    mask = cv2.bitwise_or(mask, color_mask)
                
                centers = self.find_button_candidates(mask, "红色区域")
                for center in centers:
                    self.add_coordinate('buy_mode_button', center[0], center[1], "红色检测")
            
            # 检测绿色区域（卖出按钮）
            for color_ranges in [self.buttons['sell_mode_button']['color_ranges']]:
                mask = np.zeros((height, width), dtype=np.uint8)
                for lower, upper in color_ranges:
                    color_mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                    mask = cv2.bitwise_or(mask, color_mask)
                
                centers = self.find_button_candidates(mask, "绿色区域")
                for center in centers:
                    self.add_coordinate('sell_mode_button', center[0], center[1], "绿色检测")
                    
        except Exception as e:
            self.progress_update.emit(f"颜色检测失败: {e}")
    
    def ocr_detection(self, screenshot):
        """OCR检测"""
        try:
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # OCR配置
            config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz买卖入出确定认订立价格数量委托'
            
            # 执行OCR
            data = pytesseract.image_to_data(gray, lang='chi_sim', config=config, output_type=pytesseract.Output.DICT)
            
            # 分析结果
            for i, text in enumerate(data['text']):
                if text.strip() and int(data['conf'][i]) > 30:
                    x = data['left'][i] + data['width'][i] // 2
                    y = data['top'][i] + data['height'][i] // 2
                    
                    # 匹配按钮关键词
                    for button_id, button_info in self.buttons.items():
                        if 'keywords' in button_info:
                            for keyword in button_info['keywords']:
                                if keyword in text or text in keyword:
                                    confidence = int(data['conf'][i])
                                    self.add_coordinate(button_id, x, y, f"OCR:{text}({confidence}%)")
                                    
        except Exception as e:
            self.progress_update.emit(f"OCR检测失败: {e}")
    
    def find_button_candidates(self, mask, region_name, min_area=50, max_area=5000):
        """查找按钮候选区域"""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area < area < max_area:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                if 0.3 < aspect_ratio < 3.0:
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        candidates.append((cx, cy))
        
        return candidates
    
    def add_coordinate(self, button_id, x, y, method):
        """添加坐标"""
        window_width = self.window_info['width']
        window_height = self.window_info['height']
        
        rel_x = x / window_width
        rel_y = y / window_height
        
        abs_x = self.window_info['rect'][0] + x
        abs_y = self.window_info['rect'][1] + y
        
        # 避免重复坐标
        if button_id in self.found_coords:
            for existing in self.found_coords[button_id]:
                if abs(existing['x'] - rel_x) < 0.01 and abs(existing['y'] - rel_y) < 0.01:
                    return
        
        if button_id not in self.found_coords:
            self.found_coords[button_id] = []
        
        coord_info = {
            'x': rel_x,
            'y': rel_y,
            'abs_x': abs_x,
            'abs_y': abs_y,
            'method': method
        }
        
        self.found_coords[button_id].append(coord_info)

class CalibrationDialog(QDialog):
    """坐标校准对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("智能坐标校准工具")
        self.setGeometry(200, 200, 800, 600)
        self.setModal(True)
        
        self.windows = []
        self.selected_window = None
        self.found_coords = {}
        
        self.setup_ui()
        self.setup_connections()
        
        # 自动扫描窗口
        self.scan_windows()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("🎯 智能坐标校准工具")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 主界面分割
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧：窗口选择
        left_group = QGroupBox("1. 选择目标窗口")
        left_layout = QVBoxLayout(left_group)
        
        self.window_list = QListWidget()
        self.window_list.setMinimumWidth(300)
        left_layout.addWidget(self.window_list)
        
        window_buttons = QHBoxLayout()
        self.scan_btn = QPushButton("🔄 重新扫描")
        self.select_btn = QPushButton("✅ 选择窗口")
        self.select_btn.setEnabled(False)
        window_buttons.addWidget(self.scan_btn)
        window_buttons.addWidget(self.select_btn)
        left_layout.addLayout(window_buttons)
        
        splitter.addWidget(left_group)
        
        # 右侧：校准控制
        right_group = QGroupBox("2. 执行校准")
        right_layout = QVBoxLayout(right_group)
        
        # 进度显示
        self.status_label = QLabel("请先选择目标窗口")
        self.status_label.setWordWrap(True)
        right_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        # 校准按钮
        self.calibrate_btn = QPushButton("🚀 开始校准")
        self.calibrate_btn.setEnabled(False)
        self.calibrate_btn.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        right_layout.addWidget(self.calibrate_btn)
        
        # 结果显示
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(200)
        right_layout.addWidget(self.result_text)
        
        splitter.addWidget(right_group)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("🧪 测试坐标")
        self.test_btn.setEnabled(False)
        
        self.save_btn = QPushButton("💾 保存配置")
        self.save_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("❌ 取消")
        
        button_layout.addWidget(self.test_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 设置分割比例
        splitter.setSizes([400, 400])
    
    def setup_connections(self):
        """设置信号连接"""
        self.scan_btn.clicked.connect(self.scan_windows)
        self.select_btn.clicked.connect(self.select_window)
        self.calibrate_btn.clicked.connect(self.start_calibration)
        self.test_btn.clicked.connect(self.test_coordinates)
        self.save_btn.clicked.connect(self.save_configuration)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.window_list.itemSelectionChanged.connect(self.on_window_selection_changed)
    
    def scan_windows(self):
        """扫描窗口"""
        self.status_label.setText("🔍 正在扫描窗口...")
        self.window_list.clear()
        
        # 创建并启动检测线程
        self.detector = WindowDetector()
        self.detector.windows_found.connect(self.on_windows_found)
        self.detector.status_update.connect(self.status_label.setText)
        self.detector.start()
    
    def on_windows_found(self, windows):
        """处理找到的窗口"""
        self.windows = windows
        self.window_list.clear()
        
        if not windows:
            self.status_label.setText("❌ 没有找到可用窗口")
            return
        
        # 添加窗口到列表
        for window in windows:
            title = window['title']
            size_info = f"({window['width']}x{window['height']})"
            score = window.get('score', 0)
            detection_method = window.get('detection_method', 'unknown')
            
            # 根据得分显示不同的图标和格式
            if score >= 8:
                icon = "🎯"  # 高分匹配
                confidence = "极高"
            elif score >= 5:
                icon = "✅"  # 中等匹配
                confidence = "较高"
            elif score >= 3:
                icon = "⚠️"  # 可能匹配
                confidence = "一般"
            else:
                icon = "📄"  # 普通窗口
                confidence = "较低"
            
            display_text = f"{icon} {title} {size_info} [得分:{score} 置信度:{confidence}]"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, window)
            
            # 高分窗口高亮显示
            if score >= 5:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            self.window_list.addItem(item)
        
        self.status_label.setText(f"✅ 找到 {len(windows)} 个窗口，请选择目标窗口")
    
    def on_window_selection_changed(self):
        """窗口选择改变"""
        current = self.window_list.currentItem()
        self.select_btn.setEnabled(current is not None)
    
    def select_window(self):
        """选择窗口"""
        current = self.window_list.currentItem()
        if not current:
            return
        
        self.selected_window = current.data(Qt.UserRole)
        title = self.selected_window['title']
        
        self.status_label.setText(f"✅ 已选择: {title}")
        self.calibrate_btn.setEnabled(True)
    
    def start_calibration(self):
        """开始校准"""
        if not self.selected_window:
            QMessageBox.warning(self, "警告", "请先选择目标窗口")
            return
        
        self.calibrate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 无限进度条
        
        self.result_text.clear()
        self.result_text.append("🚀 开始校准流程...")
        
        # 创建校准工作线程
        self.worker = CalibrationWorker(self.selected_window)
        self.worker.progress_update.connect(self.on_progress_update)
        self.worker.result_ready.connect(self.on_calibration_complete)
        self.worker.start()
    
    def on_progress_update(self, message):
        """更新进度"""
        self.status_label.setText(message)
        self.result_text.append(message)
    
    def on_calibration_complete(self, coords):
        """校准完成"""
        self.found_coords = coords
        self.progress_bar.setVisible(False)
        self.calibrate_btn.setEnabled(True)
        
        if not coords:
            self.status_label.setText("❌ 未检测到任何按钮")
            self.result_text.append("\n❌ 校准失败：未检测到任何按钮")
            self.result_text.append("建议：")
            self.result_text.append("1. 确保选择了正确的窗口")
            self.result_text.append("2. 确保窗口显示交易界面")
            self.result_text.append("3. 确保界面有红色/绿色按钮")
            return
        
        # 显示结果
        total_coords = sum(len(coord_list) for coord_list in coords.values())
        self.status_label.setText(f"✅ 校准完成，找到 {total_coords} 个坐标")
        
        self.result_text.append(f"\n📊 校准结果:")
        for button_id, coord_list in coords.items():
            if coord_list:
                button_name = self.get_button_name(button_id)
                self.result_text.append(f"  🔘 {button_name}: {len(coord_list)} 个候选位置")
        
        self.test_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
    
    def get_button_name(self, button_id):
        """获取按钮名称"""
        button_names = {
            'buy_mode_button': '买入模式按钮',
            'sell_mode_button': '卖出模式按钮',
            'buy_order_button': '买入订立按钮',
            'sell_order_button': '卖出订立按钮',
            'confirm_button': '确认按钮',
            'price_input': '价格输入框'
        }
        return button_names.get(button_id, button_id)
    
    def test_coordinates(self):
        """测试坐标"""
        if not self.found_coords:
            QMessageBox.warning(self, "警告", "没有坐标可测试")
            return
        
        reply = QMessageBox.question(self, "坐标测试", 
                                   "是否开始坐标测试？\n\n测试过程中鼠标会自动移动到各个按钮位置。\n请确保目标窗口可见。",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        self.result_text.append("\n🧪 开始坐标测试...")
        
        for button_id, coord_list in self.found_coords.items():
            if not coord_list:
                continue
            
            button_name = self.get_button_name(button_id)
            self.result_text.append(f"\n测试 {button_name}:")
            
            for i, coord in enumerate(coord_list):
                try:
                    # 移动鼠标到坐标位置
                    pyautogui.moveTo(coord['abs_x'], coord['abs_y'], duration=0.5)
                    
                    # 高亮效果
                    for _ in range(2):
                        pyautogui.moveRel(-5, -5, duration=0.1)
                        pyautogui.moveRel(10, 10, duration=0.1)
                        pyautogui.moveRel(-5, -5, duration=0.1)
                    
                    self.result_text.append(f"  ✅ 候选 {i+1}: ({coord['abs_x']}, {coord['abs_y']}) - {coord['method']}")
                    time.sleep(1)
                    
                except Exception as e:
                    self.result_text.append(f"  ❌ 候选 {i+1}: 测试失败 - {e}")
        
        self.result_text.append("\n✅ 坐标测试完成")
    
    def save_configuration(self):
        """保存配置"""
        if not self.found_coords:
            QMessageBox.warning(self, "警告", "没有配置可保存")
            return
        
        try:
            # 选择最佳坐标（简化版：选择第一个）
            final_coords = {}
            for button_id, coord_list in self.found_coords.items():
                if coord_list:
                    final_coords[button_id] = coord_list[0]  # 选择第一个坐标
            
            # 创建配置
            config_data = {
                "window_info": {
                    "title": self.selected_window['title'],
                    "rect": list(self.selected_window['rect']),
                    "calibrated_time": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                "button_positions": {}
            }
            
            for button_id, coord in final_coords.items():
                config_data["button_positions"][button_id] = {
                    "name": self.get_button_name(button_id),
                    "x": coord['x'],
                    "y": coord['y'],
                    "calibrated_absolute": {
                        "x": coord['abs_x'],
                        "y": coord['abs_y']
                    },
                    "method": coord['method']
                }
            
            # 保存到配置目录
            config_dir = Path(__file__).parent.parent.parent / "config"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "smart_coordinates_config.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.result_text.append(f"\n✅ 配置已保存到: {config_file}")
            self.result_text.append(f"📊 保存了 {len(config_data['button_positions'])} 个按钮配置")
            
            QMessageBox.information(self, "保存成功", 
                                  f"坐标配置已保存成功！\n\n保存位置: {config_file}\n保存按钮数: {len(config_data['button_positions'])}")
            
            self.accept()  # 关闭对话框
            
        except Exception as e:
            error_msg = f"保存配置失败: {e}"
            self.result_text.append(f"\n❌ {error_msg}")
            QMessageBox.critical(self, "保存失败", error_msg)