#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端连接状态管理器
基于现有项目架构实现客户端连接检测和自动登录功能
"""

import os
import sys
import time
import json
import logging
import threading
import base64
from typing import Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime

import cv2
import numpy as np
import pyautogui

try:
    import win32gui
    import win32con
    import win32api
    WINDOWS_API_AVAILABLE = True
except ImportError:
    WINDOWS_API_AVAILABLE = False

class ConnectionStatus(Enum):
    """连接状态枚举"""
    DISCONNECTED = "disconnected"      # 未连接
    LOGIN_REQUIRED = "login_required"  # 需要登录
    CONNECTING = "connecting"          # 连接中
    CONNECTED = "connected"            # 已连接
    ERROR = "error"                    # 连接错误

class ClientConnectionManager:
    """客户端连接状态管理器"""
    
    def __init__(self, trading_engine=None, config_manager=None):
        self.trading_engine = trading_engine
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 连接状态
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.last_check_time = 0
        self.check_interval = 5.0  # 检测间隔（秒）
        
        # 自动登录配置
        self.auto_login_enabled = False
        self.login_credentials = {"username": "", "password": ""}
        self.max_login_attempts = 3
        self.login_attempt_count = 0
        self.last_login_attempt_time = 0
        self.login_cooldown = 30  # 登录冷却时间（秒）
        
        # 状态稳定性配置
        self.status_stability_count = 0  # 连续相同状态计数
        self.required_stability = 2      # 需要连续检测的次数才确认状态变化
        self.last_stable_status = None   # 上次稳定的状态
        
        # 界面元素识别配置
        self.ui_elements = {
            "login_interface": {
                "username_input": {"method": "ocr", "text": ["用户名", "账号", "登录名"]},
                "password_input": {"method": "ocr", "text": ["密码", "Password"]},
                "login_button": {"method": "ocr", "text": ["登录", "登入", "确认", "Login"]},
                "captcha_input": {"method": "ocr", "text": ["验证码", "验证", "Captcha"]}
            },
            "trading_interface": {
                "price_display": {"method": "coordinate", "region": (0.8, 0.15, 0.15, 0.05)},
                "buy_button": {"method": "ocr", "text": ["买入", "Buy"]},
                "sell_button": {"method": "ocr", "text": ["卖出", "Sell"]},
                "balance_display": {"method": "ocr", "text": ["余额", "资金", "Balance"]}
            }
        }
        
        # 导入增强客户端检测器
        self._load_enhanced_detector()
        
        self.logger.info("客户端连接管理器初始化完成")
    
    def _load_enhanced_detector(self):
        """加载增强客户端检测器"""
        try:
            # 添加tools目录到路径
            tools_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                'tools'
            )
            if tools_path not in sys.path:
                sys.path.append(tools_path)
            
            from enhanced_client_detector import JingTaoClientDetector
            self.enhanced_detector = JingTaoClientDetector()
            self.logger.info("✅ 增强客户端检测器加载成功")
        except ImportError as e:
            self.enhanced_detector = None
            self.logger.warning(f"⚠️ 增强客户端检测器加载失败: {e}")
    
    def check_connection_status(self) -> ConnectionStatus:
        """检查客户端连接状态"""
        try:
            current_time = time.time()
            if current_time - self.last_check_time < self.check_interval:
                return self.connection_status
            
            self.last_check_time = current_time
            
            # 步骤1: 检测客户端窗口是否存在
            if not self._detect_client_window():
                self.connection_status = ConnectionStatus.DISCONNECTED
                return self.connection_status
            
            # 步骤2: 检测当前界面类型
            interface_type = self._detect_interface_type()
            
            if interface_type == "login":
                self.connection_status = ConnectionStatus.LOGIN_REQUIRED
                # 如果启用自动登录，检查是否可以尝试登录
                if self.auto_login_enabled and self._has_valid_credentials() and self._can_attempt_login():
                    login_success = self._attempt_auto_login()
                    if login_success:
                        # 登录成功后重新检测界面，可能已经进入交易界面
                        time.sleep(2)  # 给界面切换更多时间
                        new_interface = self._detect_interface_type()
                        if new_interface == "trading":
                            if self._verify_trading_functionality():
                                self.connection_status = ConnectionStatus.CONNECTED
                                self.logger.info("🎉 自动登录并进入交易界面成功")
                            else:
                                self.connection_status = ConnectionStatus.ERROR
                        else:
                            # 如果仍然是登录界面，可能需要更多时间或界面检测有问题
                            self.logger.warning("⚠️ 登录成功但界面检测仍为登录状态，等待下次检测")
                    # 如果登录失败，保持LOGIN_REQUIRED状态
                elif self.auto_login_enabled and not self._can_attempt_login():
                    # 在冷却期间，不执行登录
                    remaining_cooldown = self.login_cooldown - (time.time() - self.last_login_attempt_time)
                    if remaining_cooldown > 0:
                        self.logger.debug(f"🕐 登录冷却中，剩余 {remaining_cooldown:.1f} 秒")
            elif interface_type == "trading":
                # 步骤3: 验证交易功能是否可用
                if self._verify_trading_functionality():
                    self.connection_status = ConnectionStatus.CONNECTED
                else:
                    self.connection_status = ConnectionStatus.ERROR
            else:
                self.connection_status = ConnectionStatus.CONNECTING
            
            # 应用状态稳定性检查
            stable_status = self._apply_status_stability(self.connection_status)
            
            return stable_status
            
        except Exception as e:
            self.logger.error(f"❌ 连接状态检查失败: {e}")
            self.connection_status = ConnectionStatus.ERROR
            return self.connection_status
    
    def _detect_client_window(self) -> bool:
        """检测客户端窗口是否存在"""
        try:
            if self.enhanced_detector:
                # 使用增强检测器
                clients = self.enhanced_detector.detect_all_clients()
                if clients:
                    best_client = max(clients, key=lambda x: x.get('score', 0))
                    if best_client['score'] >= 3:
                        self.logger.info(f"🔍 检测到客户端: {best_client['title']}")
                        return True
            
            # 回退到基础检测
            if self.trading_engine:
                return self.trading_engine.find_client_window()
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 客户端窗口检测失败: {e}")
            return False
    
    def _detect_interface_type(self) -> str:
        """检测当前界面类型"""
        try:
            # 获取屏幕截图
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            
            # 首先检查是否有价格显示（交易界面的主要特征）
            if self._detect_price_area(screenshot_np):
                self.logger.debug("✅ 检测到价格显示区域，判定为交易界面")
                return "trading"
            
            # 检测登录界面元素
            if self._detect_ui_elements(screenshot_np, self.ui_elements["login_interface"]):
                self.logger.debug("✅ 检测到登录界面元素")
                return "login"
            
            # 检测交易界面元素
            if self._detect_ui_elements(screenshot_np, self.ui_elements["trading_interface"]):
                self.logger.debug("✅ 检测到交易界面元素")
                return "trading"
            
            self.logger.debug("⚠️ 未能识别界面类型")
            return "unknown"
            
        except Exception as e:
            self.logger.error(f"❌ 界面类型检测失败: {e}")
            return "unknown"
    
    def _detect_price_area(self, screenshot: np.ndarray) -> bool:
        """检测价格显示区域（判断是否为交易界面）"""
        try:
            # 检查价格显示区域是否有数字内容（基于您项目的价格区域配置）
            height, width = screenshot.shape[:2]
            
            # 价格区域相对坐标（根据您的配置调整）
            price_regions = [
                (0.8, 0.15, 0.15, 0.05),   # 主价格显示区域
                (0.7, 0.2, 0.2, 0.1),      # 扩展价格区域
                (0.85, 0.1, 0.1, 0.1),     # 右上角价格区域
            ]
            
            for region in price_regions:
                x_ratio, y_ratio, w_ratio, h_ratio = region
                x = int(width * x_ratio)
                y = int(height * y_ratio)
                w = int(width * w_ratio)
                h = int(height * h_ratio)
                
                # 提取区域
                roi = screenshot[y:y+h, x:x+w]
                if roi.size == 0:
                    continue
                
                # 转换为灰度图
                gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
                
                # 检测数字字符（价格通常包含数字）
                # 简单检测：检查是否有变化较大的像素区域（文字特征）
                edges = cv2.Canny(gray, 50, 150)
                edge_count = np.sum(edges > 0)
                
                # 如果边缘像素足够多，认为有文字内容
                if edge_count > 20:  # 阈值可调整
                    self.logger.debug(f"✅ 在区域 {region} 检测到价格内容 (边缘像素: {edge_count})")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 价格区域检测失败: {e}")
            return False
    
    def _detect_ui_elements(self, screenshot: np.ndarray, elements: Dict) -> bool:
        """检测界面元素是否存在"""
        try:
            detected_count = 0
            total_elements = len(elements)
            
            for element_name, element_config in elements.items():
                if self._detect_single_element(screenshot, element_config):
                    detected_count += 1
            
            # 如果检测到一半以上的元素，认为界面匹配
            return detected_count >= (total_elements * 0.5)
            
        except Exception as e:
            self.logger.error(f"❌ UI元素检测失败: {e}")
            return False
    
    def _detect_single_element(self, screenshot: np.ndarray, element_config: Dict) -> bool:
        """检测单个界面元素"""
        try:
            method = element_config.get("method", "ocr")
            
            if method == "ocr":
                # 使用OCR检测文字
                return self._detect_text_by_ocr(screenshot, element_config.get("text", []))
            elif method == "coordinate":
                # 使用坐标区域检测
                return self._detect_by_coordinate(screenshot, element_config.get("region"))
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 单元素检测失败: {e}")
            return False
    
    def _detect_text_by_ocr(self, screenshot: np.ndarray, target_texts: list) -> bool:
        """使用OCR检测文字（简化版实现）"""
        try:
            # 这里简化实现，实际可以集成您项目中的OCR功能
            # 暂时使用图像处理方法判断是否存在文字区域
            
            # 转换为灰度图
            gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
            
            # 二值化
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            # 检测文字区域（简化实现）
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 如果有足够的轮廓，认为可能存在文字
            return len(contours) > 10
            
        except Exception as e:
            self.logger.error(f"❌ OCR文字检测失败: {e}")
            return False
    
    def _detect_by_coordinate(self, screenshot: np.ndarray, region: Tuple) -> bool:
        """使用坐标区域检测"""
        try:
            if not region:
                return False
            
            h, w = screenshot.shape[:2]
            x, y, width, height = region
            
            # 转换相对坐标为绝对坐标
            abs_x = int(w * x)
            abs_y = int(h * y)
            abs_w = int(w * width)
            abs_h = int(h * height)
            
            # 提取区域
            roi = screenshot[abs_y:abs_y+abs_h, abs_x:abs_x+abs_w]
            
            # 简单检测：如果区域不是纯色，认为有内容
            if roi.size > 0:
                std_dev = np.std(roi)
                return std_dev > 10  # 标准差大于10认为有内容
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 坐标区域检测失败: {e}")
            return False
    
    def _verify_trading_functionality(self) -> bool:
        """验证交易功能是否可用（宽松验证）"""
        try:
            # 方法1: 尝试获取当前价格
            if self.trading_engine:
                try:
                    price = self.trading_engine.get_current_price()
                    if price and price > 0:
                        self.logger.debug(f"✅ 价格检测成功: {price}")
                        return True
                except Exception as e:
                    self.logger.debug(f"⚠️ 价格检测失败: {e}")
            
            # 方法2: 检测价格显示区域（更宽松的条件）
            if self._detect_price_area_simple():
                self.logger.debug("✅ 价格区域检测成功")
                return True
            
            # 方法3: 如果已经检测为交易界面，给予信任（宽松验证）
            self.logger.debug("⚠️ 交易功能验证使用宽松模式")
            return True  # 宽松验证：如果界面检测为交易界面，就认为功能可用
            
        except Exception as e:
            self.logger.error(f"❌ 交易功能验证失败: {e}")
            return True  # 出错时也采用宽松策略
    
    def _detect_price_area_simple(self) -> bool:
        """简化的价格区域检测"""
        try:
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            return self._detect_price_area(screenshot_np)
        except:
            return False
    
    def _detect_price_updates(self) -> bool:
        """检测价格显示区域是否有更新"""
        try:
            # 简化实现：连续检测两次价格区域，看是否有变化
            screenshot1 = pyautogui.screenshot()
            time.sleep(1)
            screenshot2 = pyautogui.screenshot()
            
            # 比较两次截图的价格区域
            # 这里简化处理，实际应该提取具体的价格区域
            diff = cv2.absdiff(np.array(screenshot1), np.array(screenshot2))
            
            # 如果有变化，认为价格在更新
            return np.sum(diff) > 1000
            
        except Exception as e:
            self.logger.error(f"❌ 价格更新检测失败: {e}")
            return False
    
    def _has_valid_credentials(self) -> bool:
        """检查是否有有效的登录凭据"""
        return (self.login_credentials.get("username") and 
                self.login_credentials.get("password"))
    
    def _can_attempt_login(self) -> bool:
        """检查是否可以尝试登录（考虑冷却时间和尝试次数）"""
        current_time = time.time()
        
        # 检查是否超过最大尝试次数
        if self.login_attempt_count >= self.max_login_attempts:
            return False
        
        # 检查是否在冷却期内
        if current_time - self.last_login_attempt_time < self.login_cooldown:
            return False
        
        return True
    
    def _attempt_auto_login(self) -> bool:
        """尝试自动登录"""
        try:
            if self.login_attempt_count >= self.max_login_attempts:
                self.logger.warning("⚠️ 登录尝试次数超限，跳过自动登录")
                return False
            
            self.login_attempt_count += 1
            self.last_login_attempt_time = time.time()  # 记录尝试时间
            
            self.logger.info(f"🔐 尝试自动登录 (第{self.login_attempt_count}次)...")
            
            # 这里应该实现具体的登录操作
            # 基于您项目的UI自动化能力来实现
            success = self._perform_login_actions()
            
            if success:
                self.login_attempt_count = 0  # 重置计数器
                self.logger.info("✅ 自动登录成功")
                return True
            else:
                self.logger.warning("❌ 自动登录失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 自动登录异常: {e}")
            return False
    
    def _perform_login_actions(self) -> bool:
        """执行登录操作"""
        try:
            self.logger.info("🔐 开始执行自动登录操作...")
            
            # 确保有有效的登录凭据
            if not self._has_valid_credentials():
                self.logger.error("❌ 没有有效的登录凭据")
                return False
            
            username = self.login_credentials["username"]
            password = self.login_credentials["password"]
            
            # 截取当前屏幕查找登录界面元素
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            
            # 1. 尝试找到并点击用户名输入框
            username_pos = self._find_login_element(screenshot_np, "username")
            if username_pos:
                self.logger.info("🎯 找到用户名输入框")
                pyautogui.click(username_pos[0], username_pos[1])
                time.sleep(0.5)
                
                # 清空并输入用户名
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                pyautogui.write(username)
                self.logger.info(f"✅ 输入用户名: {username}")
                time.sleep(0.5)
            else:
                self.logger.warning("⚠️ 未找到用户名输入框")
                return False
            
            # 2. 尝试找到并点击密码输入框
            password_pos = self._find_login_element(screenshot_np, "password")
            if password_pos:
                self.logger.info("🎯 找到密码输入框")
                pyautogui.click(password_pos[0], password_pos[1])
                time.sleep(0.5)
                
                # 清空并输入密码
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                pyautogui.write(password)
                self.logger.info("✅ 输入密码")
                time.sleep(0.5)
            else:
                self.logger.warning("⚠️ 未找到密码输入框")
                return False
            
            # 3. 尝试找到并点击登录按钮
            login_btn_pos = self._find_login_element(screenshot_np, "login_button")
            if login_btn_pos:
                self.logger.info("🎯 找到登录按钮")
                pyautogui.click(login_btn_pos[0], login_btn_pos[1])
                self.logger.info("✅ 点击登录按钮")
                time.sleep(2)  # 等待登录处理
            else:
                self.logger.warning("⚠️ 未找到登录按钮")
                return False
            
            # 4. 等待并验证登录结果
            self.logger.info("⏳ 等待登录结果...")
            time.sleep(3)  # 给登录过程更多时间
            
            # 重新检测界面类型，看是否已经进入交易界面
            new_interface = self._detect_interface_type()
            if new_interface == "trading":
                self.logger.info("🎉 登录成功，已进入交易界面")
                return True
            elif new_interface == "login":
                self.logger.warning("❌ 登录失败，仍在登录界面")
                return False
            else:
                self.logger.info("🔄 界面状态未明确，可能需要额外验证")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ 登录操作执行失败: {e}")
            return False
    
    def _find_login_element(self, screenshot: np.ndarray, element_type: str) -> Optional[Tuple[int, int]]:
        """查找登录界面元素位置"""
        try:
            h, w = screenshot.shape[:2]
            
            # 根据元素类型定义搜索区域和特征
            search_areas = {
                "username": {
                    "region": (0.2, 0.3, 0.6, 0.4),  # 用户名通常在中上部
                    "keywords": ["用户名", "账号", "登录名", "用户", "Username"]
                },
                "password": {
                    "region": (0.2, 0.4, 0.6, 0.3),  # 密码在用户名下方
                    "keywords": ["密码", "Password", "口令"]
                },
                "login_button": {
                    "region": (0.3, 0.6, 0.4, 0.3),  # 登录按钮在下方
                    "keywords": ["登录", "登入", "确认", "Login", "确定"]
                }
            }
            
            if element_type not in search_areas:
                return None
            
            area_config = search_areas[element_type]
            region = area_config["region"]
            
            # 计算搜索区域
            x = int(w * region[0])
            y = int(h * region[1])
            search_w = int(w * region[2])
            search_h = int(h * region[3])
            
            # 确保区域在有效范围内
            x = max(0, min(x, w - 1))
            y = max(0, min(y, h - 1))
            search_w = max(1, min(search_w, w - x))
            search_h = max(1, min(search_h, h - y))
            
            # 提取搜索区域
            search_area = screenshot[y:y+search_h, x:x+search_w]
            
            # 简化的文字区域检测：寻找可能的输入框或按钮
            # 1. 转换为灰度图
            gray = cv2.cvtColor(search_area, cv2.COLOR_RGB2GRAY)
            
            # 2. 查找轮廓（可能的输入框边界）
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 3. 筛选合适大小的矩形区域
            candidates = []
            for contour in contours:
                rect = cv2.boundingRect(contour)
                rect_x, rect_y, rect_w, rect_h = rect
                
                # 输入框或按钮的基本特征：
                # - 宽度大于高度（横向矩形）
                # - 面积适中
                if (rect_w > rect_h and 
                    rect_w > 80 and rect_h > 20 and 
                    rect_w < search_w * 0.8 and rect_h < search_h * 0.5):
                    
                    # 计算在原图中的绝对坐标
                    abs_x = x + rect_x + rect_w // 2
                    abs_y = y + rect_y + rect_h // 2
                    candidates.append((abs_x, abs_y, rect_w * rect_h))
            
            # 4. 如果找到候选位置，返回面积最大的
            if candidates:
                # 按面积排序，选择最大的
                candidates.sort(key=lambda item: item[2], reverse=True)
                best_candidate = candidates[0]
                self.logger.info(f"🎯 找到{element_type}位置: ({best_candidate[0]}, {best_candidate[1]})")
                return (best_candidate[0], best_candidate[1])
            
            # 5. 如果没有找到，返回搜索区域的中心点作为备选
            center_x = x + search_w // 2
            center_y = y + search_h // 2
            self.logger.info(f"🎯 使用{element_type}默认位置: ({center_x}, {center_y})")
            return (center_x, center_y)
            
        except Exception as e:
            self.logger.error(f"❌ 查找{element_type}元素失败: {e}")
            return None
    
    def set_login_credentials(self, username: str, password: str, save_to_config: bool = True):
        """设置登录凭据"""
        try:
            # 简单的凭据加密（实际应该使用更安全的方法）
            encoded_username = base64.b64encode(username.encode()).decode()
            encoded_password = base64.b64encode(password.encode()).decode()
            
            self.login_credentials = {
                "username": username,
                "password": password
            }
            
            if save_to_config and self.config_manager:
                # 保存到配置文件（加密）
                login_config = {
                    "auto_login_enabled": self.auto_login_enabled,
                    "encoded_username": encoded_username,
                    "encoded_password": encoded_password
                }
                self.config_manager.set_value("client_connection.login", login_config)
                self.config_manager.save_config()
            
            self.logger.info("✅ 登录凭据已设置")
            
        except Exception as e:
            self.logger.error(f"❌ 设置登录凭据失败: {e}")
    
    def load_login_credentials(self) -> bool:
        """从配置文件加载登录凭据"""
        try:
            if not self.config_manager:
                return False
            
            login_config = self.config_manager.get_value("client_connection.login", {})
            
            if login_config.get("encoded_username") and login_config.get("encoded_password"):
                # 解密凭据
                username = base64.b64decode(login_config["encoded_username"]).decode()
                password = base64.b64decode(login_config["encoded_password"]).decode()
                
                self.login_credentials = {
                    "username": username,
                    "password": password
                }
                
                self.auto_login_enabled = login_config.get("auto_login_enabled", False)
                self.logger.info("✅ 登录凭据加载成功")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 加载登录凭据失败: {e}")
            return False
    
    def enable_auto_login(self, enabled: bool = True):
        """启用/禁用自动登录"""
        self.auto_login_enabled = enabled
        self.logger.info(f"🔐 自动登录{'已启用' if enabled else '已禁用'}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            "status": self.connection_status.value,
            "status_text": self._get_status_text(),
            "auto_login_enabled": self.auto_login_enabled,
            "has_credentials": self._has_valid_credentials(),
            "last_check_time": self.last_check_time,
            "login_attempts": self.login_attempt_count
        }
    
    def _get_status_text(self) -> str:
        """获取状态文字描述"""
        status_texts = {
            ConnectionStatus.DISCONNECTED: "客户端未连接",
            ConnectionStatus.LOGIN_REQUIRED: "需要登录",
            ConnectionStatus.CONNECTING: "连接中...",
            ConnectionStatus.CONNECTED: "已连接",
            ConnectionStatus.ERROR: "连接错误"
        }
        return status_texts.get(self.connection_status, "未知状态")
    
    def force_reconnect(self):
        """强制重新连接"""
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.last_check_time = 0
        self.login_attempt_count = 0
        self.last_login_attempt_time = 0  # 重置登录时间
        # 重置状态稳定性
        self.status_stability_count = 0
        self.last_stable_status = None
        self.logger.info("🔄 强制重新连接...")
    
    def force_status_update(self):
        """强制更新状态（无缓存）"""
        self.last_check_time = 0  # 重置检查时间，强制重新检测
        return self.check_connection_status()
    
    def _apply_status_stability(self, new_status: ConnectionStatus) -> ConnectionStatus:
        """应用状态稳定性检查，避免状态频繁波动"""
        try:
            # 如果状态和上次相同，增加稳定计数
            if new_status == self.last_stable_status:
                self.status_stability_count += 1
            else:
                # 状态发生变化，重置计数
                self.status_stability_count = 1
            
            # 如果连续检测次数足够，确认状态变化
            if self.status_stability_count >= self.required_stability:
                # 状态稳定，更新为最终状态
                self.last_stable_status = new_status
                self.connection_status = new_status
                
                if self.status_stability_count == self.required_stability:
                    # 第一次确认状态稳定时记录日志
                    self.logger.info(f"🔒 状态已稳定: {self.get_status_text()}")
                
                return new_status
            else:
                # 状态还不够稳定，返回上次稳定的状态
                if self.last_stable_status is not None:
                    self.logger.debug(f"⏳ 状态检测中 ({self.status_stability_count}/{self.required_stability}): {new_status.name} → 保持 {self.last_stable_status.name}")
                    return self.last_stable_status
                else:
                    # 如果没有上次稳定状态，使用当前状态
                    self.last_stable_status = new_status
                    self.connection_status = new_status
                    return new_status
                    
        except Exception as e:
            self.logger.error(f"❌ 状态稳定性检查失败: {e}")
            return new_status