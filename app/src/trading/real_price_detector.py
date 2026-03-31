#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
景陶易购真实价格检测器
专门针对景陶易购界面设计的精确价格识别系统
支持OCR和手动区域选择两种模式
"""

import cv2
import numpy as np
import re
import logging
import time
import pyautogui
import os
import sys
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

# 添加工具路径
tools_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tools')
if tools_path not in sys.path:
    sys.path.append(tools_path)

# 安全导入pytesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True

    # 导入Tesseract配置模块
    try:
        utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utils')
        if utils_path not in sys.path:
            sys.path.append(utils_path)
        from tesseract_config import configure_pytesseract
        configure_pytesseract()  # 自动配置Tesseract路径
    except ImportError:
        # 备用配置 - 使用新的安装路径
        pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'

except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None

# 导入手动区域选择器
try:
    from price_region_selector import PriceRegionSelector
    MANUAL_SELECTOR_AVAILABLE = True
except ImportError:
    MANUAL_SELECTOR_AVAILABLE = False
    PriceRegionSelector = None

@dataclass
class PriceRegion:
    """价格区域定义"""
    name: str
    x: int
    y: int
    width: int
    height: int
    description: str

class RealPriceDetector:
    """真实价格检测器 - 专门针对景陶易购界面"""
    
    def __init__(self, use_manual_selection: bool = False):
        self.logger = logging.getLogger(__name__)
        self.current_price = None
        self.last_price_update = 0
        self.price_history = []
        self.max_history = 50
        self.use_manual_selection = use_manual_selection
        
        # 手动区域选择模式不依赖GUI组件，直接使用配置文件
        self.manual_selector = None
        if use_manual_selection:
            # 检查手动区域配置文件是否存在 - 尝试多个可能的路径
            possible_paths = [
                # 主配置目录
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "price_regions_manual.json"),
                # tools配置目录
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tools", "config", "price_regions_manual.json"),
                # 相对路径
                os.path.join(os.getcwd(), "config", "price_regions_manual.json"),
                os.path.join(os.getcwd(), "tools", "config", "price_regions_manual.json")
            ]
            
            print(f"🔍 开始搜索手动区域配置文件...")  # 使用print确保输出到控制台
            config_file = None
            for path in possible_paths:
                print(f"🔍 检查配置文件路径: {path}")
                self.logger.info(f"🔍 检查配置文件路径: {path}")
                if os.path.exists(path):
                    config_file = path
                    print(f"✅ 找到手动区域配置文件: {config_file}")
                    self.logger.info(f"✅ 找到手动区域配置文件: {config_file}")
                    break
                else:
                    print(f"❌ 配置文件不存在: {path}")
                    self.logger.warning(f"❌ 配置文件不存在: {path}")
            
            if config_file:
                self.config_file = config_file  # 保存找到的配置文件路径
                print("✅ 手动区域配置文件存在，使用手动区域选择模式")
                self.logger.info("✅ 手动区域配置文件存在，使用手动区域选择模式")
            else:
                print("❌ 未找到手动区域配置文件，回退到OCR模式")
                self.logger.warning("❌ 未找到手动区域配置文件，回退到OCR模式")
                self.use_manual_selection = False
        else:
            self.logger.info("📋 配置设置为使用OCR模式")
        
        # 景陶易购界面的价格区域配置（OCR模式使用）
        self.price_regions = {
            # 主要价格显示区域（根据截图调整）
            'main_price': PriceRegion(
                name='main_price',
                x=30, y=88, width=100, height=25,  # 左上角WFLM后的价格区域
                description='主要价格显示区域'
            ),
            'current_price': PriceRegion(
                name='current_price', 
                x=240, y=88, width=80, height=25,  # 最新价格区域
                description='当前最新价格'
            ),
            'bid_price': PriceRegion(
                name='bid_price',
                x=900, y=425, width=60, height=25,  # 买价区域
                description='买入价格'
            ),
            'ask_price': PriceRegion(
                name='ask_price',
                x=1050, y=425, width=60, height=25,  # 卖价区域
                description='卖出价格'
            ),
            'input_price': PriceRegion(
                name='input_price',
                x=45, y=642, width=100, height=25,  # 价格输入框区域
                description='价格输入框'
            )
        }
        
        # OCR配置
        self.ocr_configs = [
            '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.',
            '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.',
            '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.',
            '--oem 3 --psm 13 -c tessedit_char_whitelist=0123456789.'
        ]
        
        # 价格验证范围
        self.min_price = 1000
        self.max_price = 3000
        
        self.logger.info(f"真实价格检测器初始化完成 - 模式: {'手动区域选择' if self.use_manual_selection else 'OCR'}")
    
    def setup_manual_regions(self) -> bool:
        """设置手动选择区域"""
        if not self.use_manual_selection or not self.manual_selector:
            self.logger.error("手动区域选择模式未启用")
            return False
        
        return self.manual_selector.setup_all_regions()
    
    def switch_to_manual_mode(self) -> bool:
        """切换到手动区域选择模式"""
        if not MANUAL_SELECTOR_AVAILABLE:
            self.logger.error("手动区域选择器不可用")
            return False
        
        self.use_manual_selection = True
        if not self.manual_selector:
            self.manual_selector = PriceRegionSelector()
        
        self.logger.info("已切换到手动区域选择模式")
        return True
    
    def switch_to_ocr_mode(self):
        """切换到OCR模式"""
        self.use_manual_selection = False
        self.logger.info("已切换到OCR模式")
    
    def _prompt_manual_region_setup(self, region_name: str):
        """提示用户设置手动区域"""
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            # 创建一个隐藏的根窗口
            root = tk.Tk()
            root.withdraw()
            
            result = messagebox.askyesno(
                "价格区域未配置",
                f"价格区域 '{region_name}' 尚未配置。\n是否现在设置？"
            )
            
            root.destroy()
            
            if result and self.manual_selector:
                region_descriptions = {
                    'main_price': '主要价格显示区域',
                    'current_price': '当前最新价格',
                    'bid_price': '买入价格',
                    'ask_price': '卖出价格'
                }
                description = region_descriptions.get(region_name, region_name)
                self.manual_selector.select_region_gui(region_name, description)
        except Exception as e:
            self.logger.error(f"提示设置区域失败: {e}")
    
    def get_screenshot(self) -> Optional[np.ndarray]:
        """获取屏幕截图"""
        try:
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            return screenshot_bgr
        except Exception as e:
            self.logger.error(f"获取截图失败: {e}")
            return None
    
    def extract_price_region(self, screenshot: np.ndarray, region: PriceRegion) -> Optional[np.ndarray]:
        """提取指定价格区域"""
        try:
            h, w = screenshot.shape[:2]
            
            # 确保坐标在有效范围内
            x = max(0, min(region.x, w - region.width))
            y = max(0, min(region.y, h - region.height))
            x2 = min(w, x + region.width)
            y2 = min(h, y + region.height)
            
            if x2 <= x or y2 <= y:
                self.logger.warning(f"无效的价格区域: {region.name}")
                return None
            
            price_region = screenshot[y:y2, x:x2]
            
            # 保存调试图像
            debug_filename = f"debug_price_region_{region.name}_{int(time.time())}.png"
            cv2.imwrite(f"logs/{debug_filename}", price_region)
            self.logger.debug(f"保存价格区域调试图: {debug_filename}")
            
            return price_region
            
        except Exception as e:
            self.logger.error(f"提取价格区域失败: {e}")
            return None
    
    def preprocess_price_image(self, image: np.ndarray) -> List[np.ndarray]:
        """预处理价格图像，返回多种处理结果"""
        try:
            processed_images = []
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 方法1: 直接使用灰度图
            processed_images.append(gray)
            
            # 方法2: 增强对比度
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            processed_images.append(enhanced)
            
            # 方法3: 自适应阈值
            adaptive_thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            processed_images.append(adaptive_thresh)
            
            # 方法4: OTSU阈值
            _, otsu_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(otsu_thresh)
            
            # 方法5: 形态学处理
            kernel = np.ones((2,2), np.uint8)
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            processed_images.append(morph)
            
            # 方法6: 缩放增强
            scaled = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            processed_images.append(scaled)
            
            return processed_images
            
        except Exception as e:
            self.logger.error(f"图像预处理失败: {e}")
            return [image]
    
    def ocr_extract_price(self, image: np.ndarray) -> Optional[float]:
        """使用OCR提取价格"""
        if not TESSERACT_AVAILABLE:
            self.logger.warning("Tesseract OCR不可用")
            return None
        
        try:
            # 获取多种预处理结果
            processed_images = self.preprocess_price_image(image)
            
            for i, processed_img in enumerate(processed_images):
                for j, config in enumerate(self.ocr_configs):
                    try:
                        # OCR识别
                        text = pytesseract.image_to_string(processed_img, config=config).strip()
                        
                        # 提取数字
                        numbers = re.findall(r'(\d{3,4}\.?\d*)', text)  # 匹配3-4位数字开头的价格
                        
                        for number_str in numbers:
                            try:
                                price = float(number_str)
                                if self.min_price <= price <= self.max_price:
                                    self.logger.debug(f"OCR成功 - 方法{i+1}-配置{j+1}: {text} -> {price}")
                                    return price
                            except ValueError:
                                continue
                                
                    except Exception as ocr_e:
                        self.logger.debug(f"OCR方法{i+1}-配置{j+1}失败: {ocr_e}")
                        continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"OCR价格提取失败: {e}")
            return None
    
    def _get_price_from_manual_region(self, region_name: str) -> Optional[float]:
        """从手动配置的区域获取价格"""
        try:
            # 直接使用保存的区域配置，无需GUI初始化
            import json
            
            # 使用已找到的配置文件路径
            config_file = getattr(self, 'config_file', None)
            if not config_file:
                # 如果没有保存的路径，重新搜索
                possible_paths = [
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "price_regions_manual.json"),
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tools", "config", "price_regions_manual.json"),
                    os.path.join(os.getcwd(), "config", "price_regions_manual.json"),
                    os.path.join(os.getcwd(), "tools", "config", "price_regions_manual.json")
                ]
                
                for path in possible_paths:
                    self.logger.info(f"🔍 搜索配置文件: {path}")
                    if os.path.exists(path):
                        config_file = path
                        self.logger.info(f"✅ 找到配置文件: {config_file}")
                        break
                    else:
                        self.logger.warning(f"❌ 文件不存在: {path}")
            
            if not config_file or not os.path.exists(config_file):
                self.logger.warning("手动区域配置文件不存在")
                return None
            
            # 加载区域配置
            with open(config_file, 'r', encoding='utf-8') as f:
                regions = json.load(f)
            
            if region_name not in regions:
                self.logger.warning(f"区域 '{region_name}' 未配置")
                return None
            
            # 获取屏幕截图
            screenshot = pyautogui.screenshot()
            screenshot = np.array(screenshot)
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
            
            # 提取区域图像
            region = regions[region_name]
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            region_img = screenshot[y:y+h, x:x+w]
            
            if region_img.size > 0:
                # 使用OCR识别价格
                price = self.ocr_extract_price(region_img)
                if price is not None:
                    self.logger.debug(f"手动区域 '{region_name}' 识别价格: {price:.1f}")
                    return price
            
            return None
            
        except Exception as e:
            self.logger.error(f"手动区域价格获取失败: {e}")
            return None

    def template_match_digits(self, image: np.ndarray) -> Optional[float]:
        """使用模板匹配识别数字（备用方案）"""
        try:
            # 这里可以实现数字模板匹配
            # 暂时返回None，使用OCR为主
            return None
        except Exception as e:
            self.logger.error(f"模板匹配失败: {e}")
            return None
    
    def get_real_price(self, region_name: str = 'current_price') -> Optional[float]:
        """获取真实价格"""
        try:
            # 使用手动区域选择模式
            if self.use_manual_selection:
                price = self._get_price_from_manual_region(region_name)
                if price is not None:
                    self.update_price_history(price)
                    self.current_price = price
                    self.last_price_update = time.time()
                    self.logger.info(f"💰 手动区域获取价格: {price} (区域: {region_name})")
                    return price
                else:
                    self.logger.warning(f"手动区域 '{region_name}' 未配置或获取失败，回退到OCR模式")
                    # 回退到OCR模式继续执行
            
            # 使用OCR模式
            # 获取屏幕截图
            screenshot = self.get_screenshot()
            if screenshot is None:
                return None
            
            # 检查指定区域是否存在
            if region_name not in self.price_regions:
                self.logger.error(f"未知的价格区域: {region_name}")
                return None
            
            region = self.price_regions[region_name]
            
            # 提取价格区域
            price_region = self.extract_price_region(screenshot, region)
            if price_region is None:
                return None
            
            # 尝试OCR识别
            price = self.ocr_extract_price(price_region)
            if price is not None:
                self.update_price_history(price)
                self.current_price = price
                self.last_price_update = time.time()
                self.logger.info(f"💰 获取到真实价格: {price} (区域: {region.description})")
                return price
            
            # 如果OCR失败，尝试模板匹配
            price = self.template_match_digits(price_region)
            if price is not None:
                self.update_price_history(price)
                self.current_price = price
                self.last_price_update = time.time()
                self.logger.info(f"💰 模板匹配获取价格: {price}")
                return price
            
            # 如果区域OCR和模板匹配都失败，尝试增强OCR全屏检测
            self.logger.info(f"🔍 区域 {region.description} 获取失败，尝试增强OCR...")
            enhanced_price = self.get_price_from_screen_ocr_enhanced()
            if enhanced_price:
                self.update_price_history(enhanced_price)
                self.current_price = enhanced_price
                self.last_price_update = time.time()
                self.logger.info(f"💰 增强OCR获取价格: {enhanced_price:.2f}")
                return enhanced_price
            
            self.logger.warning(f"未能从区域 {region.description} 识别出价格")
            return None
            
        except Exception as e:
            self.logger.error(f"获取真实价格失败: {e}")
            return None
    
    def get_multiple_prices(self) -> Dict[str, Optional[float]]:
        """获取多个区域的价格"""
        try:
            # 使用手动区域选择模式
            if self.use_manual_selection and self.manual_selector:
                prices = self.manual_selector.get_all_prices()
                for region_name, price in prices.items():
                    if price:
                        self.logger.info(f"💰 手动区域 {region_name}: {price}")
                return prices
            
            # 使用OCR模式
            screenshot = self.get_screenshot()
            if screenshot is None:
                return {}
            
            prices = {}
            for region_name, region in self.price_regions.items():
                if region_name == 'input_price':  # 跳过输入框
                    continue
                    
                price_region = self.extract_price_region(screenshot, region)
                if price_region is not None:
                    price = self.ocr_extract_price(price_region)
                    prices[region_name] = price
                    if price:
                        self.logger.info(f"💰 {region.description}: {price}")
                else:
                    prices[region_name] = None
            
            return prices
            
        except Exception as e:
            self.logger.error(f"获取多区域价格失败: {e}")
            return {}
    
    def update_price_history(self, price: float):
        """更新价格历史"""
        try:
            self.price_history.append({
                'price': price,
                'timestamp': time.time()
            })
            
            # 限制历史记录数量
            if len(self.price_history) > self.max_history:
                self.price_history = self.price_history[-self.max_history:]
                
        except Exception as e:
            self.logger.error(f"更新价格历史失败: {e}")
    
    def get_price_with_fallback(self) -> float:
        """获取价格，带降级方案"""
        try:
            # 优先级1: 当前价格区域
            price = self.get_real_price('current_price')
            if price:
                return price
            
            # 优先级2: 主价格区域
            price = self.get_real_price('main_price')
            if price:
                return price
            
            # 优先级3: 买价区域
            price = self.get_real_price('bid_price')
            if price:
                return price
            
            # 优先级4: 增强OCR全屏检测
            self.logger.info("🔍 尝试增强OCR全屏价格检测...")
            enhanced_price = self.get_price_from_screen_ocr_enhanced()
            if enhanced_price:
                self.logger.info(f"✅ 增强OCR检测成功: {enhanced_price:.2f}")
                return enhanced_price
            
            # 优先级5: 使用历史价格（无波动）
            if self.price_history:
                last_price = self.price_history[-1]['price']
                self.logger.warning(f"使用历史价格: {last_price:.1f}")
                return last_price
            
            # 所有价格获取方法都失败
            self.logger.error("❌ 所有价格获取方法都失败，无法获取真实价格")
            return None
            
        except Exception as e:
            self.logger.error(f"获取价格失败: {e}")
            return None  # 返回None表示价格获取失败
    
    def auto_input_price(self, target_price: Optional[float] = None, price_adjustment: float = 0) -> bool:
        """自动输入价格到价格框"""
        try:
            if target_price is None:
                # 获取当前真实价格
                current_price = self.get_price_with_fallback()
                target_price = current_price + price_adjustment
            
            # 获取价格输入框位置
            input_region = self.price_regions['input_price']
            input_x = input_region.x + input_region.width // 2
            input_y = input_region.y + input_region.height // 2
            
            # 点击价格输入框
            pyautogui.click(input_x, input_y)
            time.sleep(0.3)
            
            # 全选并清空当前内容
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.1)
            
            # 输入新价格
            price_str = f"{target_price:.0f}"  # 取整数
            pyautogui.write(price_str)
            time.sleep(0.2)
            
            self.logger.info(f"💰 自动输入价格: {price_str}")
            return True
            
        except Exception as e:
            self.logger.error(f"自动输入价格失败: {e}")
            return False
    
    def calibrate_price_regions(self):
        """校准价格区域（交互式）"""
        print("=== 价格区域校准 ===")
        print("请按照提示点击相应的价格区域")
        
        try:
            screenshot = self.get_screenshot()
            if screenshot is None:
                print("❌ 无法获取截图")
                return
            
            for region_name, region in self.price_regions.items():
                if region_name == 'input_price':
                    continue
                    
                print(f"\n请点击 {region.description} 区域...")
                input("按回车后点击区域...")
                
                # 获取鼠标位置
                x, y = pyautogui.position()
                print(f"获取到坐标: ({x}, {y})")
                
                # 更新区域配置
                self.price_regions[region_name].x = x - region.width // 2
                self.price_regions[region_name].y = y - region.height // 2
                
                # 验证区域
                test_region = self.extract_price_region(screenshot, self.price_regions[region_name])
                if test_region is not None:
                    price = self.ocr_extract_price(test_region)
                    if price:
                        print(f"✅ 识别到价格: {price}")
                    else:
                        print("⚠️ 未能识别价格，可能需要调整")
            
            print("校准完成！")
            
        except Exception as e:
            print(f"校准失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'current_price': self.current_price,
            'last_update': self.last_price_update,
            'history_count': len(self.price_history),
            'tesseract_available': TESSERACT_AVAILABLE
        }
    
    def get_price_from_screen_ocr_enhanced(self) -> Optional[float]:
        """增强版全屏OCR价格检测 - 基于"最新价"文字定位"""
        try:
            import pyautogui
            import re
            
            # 获取屏幕截图
            screenshot = pyautogui.screenshot()
            screenshot_array = np.array(screenshot)
            
            if not TESSERACT_AVAILABLE:
                self.logger.warning("Tesseract OCR不可用，无法进行增强OCR检测")
                return None
            
            # 方法1: 快速数字模式（最高性能）
            quick_price = self._quick_number_search(screenshot_array)
            if quick_price:
                return quick_price
            
            # 方法2: 传统数字搜索（备用）
            return self._traditional_number_search(screenshot_array)
            
        except Exception as e:
            self.logger.error(f"增强OCR价格检测失败: {e}")
            return None
    
    def get_price_by_text_location(self, image: np.ndarray, target_text: str) -> Optional[float]:
        """基于目标文字定位价格"""
        try:
            self.logger.info(f"🎯 快速搜索关键词: '{target_text}'")
            
            # 快速OCR配置（优先性能）
            fast_configs = [
                '--psm 6',  # 默认配置（最快）
                '--psm 6 -l chi_sim+eng',  # 中英文混合（如果可用）
                '--psm 7',  # 单行文本
            ]
            
            # 尝试不同配置，找到第一个有效的
            ocr_data = None
            for config in fast_configs:
                try:
                    # 获取完整OCR结果（包含位置信息）
                    ocr_data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
                    self.logger.info(f"✅ OCR配置成功: {config}")
                    break
                except Exception as e:
                    self.logger.warning(f"⚠️ OCR配置失败: {config} - {e}")
                    continue
            
            if ocr_data is None:
                self.logger.error("❌ 所有OCR配置都失败")
                return None
            
            # 查找目标文字的位置
            target_boxes = []
            for i, text in enumerate(ocr_data['text']):
                if target_text in text and int(ocr_data['conf'][i]) > 30:  # 置信度阈值
                    x = int(ocr_data['left'][i])
                    y = int(ocr_data['top'][i])
                    w = int(ocr_data['width'][i])
                    h = int(ocr_data['height'][i])
                    target_boxes.append((x, y, w, h))
                    self.logger.info(f"✅ 找到'{target_text}' 位置: ({x}, {y}, {w}, {h}), 置信度: {ocr_data['conf'][i]}")
            
            if not target_boxes:
                self.logger.warning(f"❌ 未找到'{target_text}'文字")
                return None
            
            # 为每个找到的目标文字搜索附近的价格
            for box_idx, (x, y, w, h) in enumerate(target_boxes):
                self.logger.info(f"🔍 在'{target_text}'附近搜索价格 (位置{box_idx+1})...")
                
                # 扩展搜索区域（文字右侧和下方）
                search_regions = [
                    (x + w, y - h//2, min(200, image.shape[1] - x - w), h * 2),  # 右侧
                    (x - 50, y + h, w + 100, min(50, image.shape[0] - y - h)),   # 下方
                    (x, y - 30, w + 150, h + 60),  # 周围区域
                ]
                
                for region_idx, (rx, ry, rw, rh) in enumerate(search_regions):
                    # 边界检查
                    rx = max(0, rx)
                    ry = max(0, ry)
                    rw = min(rw, image.shape[1] - rx)
                    rh = min(rh, image.shape[0] - ry)
                    
                    if rw <= 0 or rh <= 0:
                        continue
                    
                    # 提取搜索区域
                    search_region = image[ry:ry+rh, rx:rx+rw]
                    
                    # 在该区域搜索数字
                    price = self._extract_price_from_region(search_region, f"{target_text}附近区域{region_idx+1}")
                    if price:
                        self.logger.info(f"✅ 在'{target_text}'附近找到价格: {price:.2f}")
                        return price
            
            self.logger.warning(f"❌ 在'{target_text}'附近未找到有效价格")
            return None
            
        except Exception as e:
            self.logger.error(f"基于文字定位价格检测失败: {e}")
            return None
    
    def _extract_price_from_region(self, region: np.ndarray, region_name: str) -> Optional[float]:
        """从指定区域提取价格数字"""
        try:
            # 数字识别配置
            number_configs = [
                '--psm 7 -c tessedit_char_whitelist=0123456789.',  # 单行数字
                '--psm 8 -c tessedit_char_whitelist=0123456789.',  # 单词数字
                '--psm 6 -c tessedit_char_whitelist=0123456789.',  # 块数字
            ]
            
            # 预处理区域图像
            processed_regions = self.preprocess_price_image(region)
            
            for img_idx, processed_region in enumerate(processed_regions):
                for config_idx, config in enumerate(number_configs):
                    try:
                        text = pytesseract.image_to_string(processed_region, config=config)
                        text = text.strip()
                        
                        if text:
                            self.logger.info(f"🔍 {region_name}-图像{img_idx+1}-配置{config_idx+1}: '{text}'")
                            
                            # 提取数字
                            import re
                            price_matches = re.findall(r'\d+\.?\d*', text)
                            for match in price_matches:
                                try:
                                    price = float(match)
                                    if 10 <= price <= 99999:  # 合理价格范围
                                        return price
                                except ValueError:
                                    continue
                    except Exception:
                        continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"区域价格提取失败: {e}")
            return None
    
    def _traditional_number_search(self, image: np.ndarray) -> Optional[float]:
        """传统数字搜索方法（备用）"""
        try:
            # 多种OCR配置
            ocr_configs = [
                '--psm 6 -c tessedit_char_whitelist=0123456789.',  # 只识别数字和小数点
                '--psm 7 -c tessedit_char_whitelist=0123456789.',  # 单行数字
                '--psm 8 -c tessedit_char_whitelist=0123456789.',  # 单词数字
                '--psm 13 -c tessedit_char_whitelist=0123456789.', # 原始行数字
                '--psm 6',  # 默认配置
            ]
            
            # 预处理图像
            processed_images = self.preprocess_price_image(image)
            
            for img_idx, processed_img in enumerate(processed_images):
                for config_idx, config in enumerate(ocr_configs):
                    try:
                        # OCR识别
                        text = pytesseract.image_to_string(processed_img, config=config)
                        self.logger.info(f"🔍 传统OCR配置{config_idx+1}/图像{img_idx+1}: '{text.strip()}'")
                        
                        # 提取价格数字
                        price_matches = re.findall(r'\d+\.?\d*', text)
                        for match in price_matches:
                            try:
                                price = float(match)
                                # 合理的价格范围检查
                                if 10 <= price <= 99999:
                                    self.logger.info(f"✅ 传统OCR检测到合理价格: {price:.2f}")
                                    return price
                            except ValueError:
                                continue
                    except Exception as ocr_e:
                        continue
            
            self.logger.warning("❌ 传统OCR未检测到合理价格")
            return None
            
        except Exception as e:
            self.logger.error(f"传统OCR价格检测失败: {e}")
            return None
    
    def _quick_number_search(self, image: np.ndarray) -> Optional[float]:
        """快速数字搜索 - 高性能模式"""
        try:
            # 只使用最快的配置
            quick_config = '--psm 6 -c tessedit_char_whitelist=0123456789.'
            
            # 简化预处理 - 只使用灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 直接OCR识别
            text = pytesseract.image_to_string(gray, config=quick_config)
            
            # 查找合理的价格数字 - 优化正则表达式
            import re
            # 匹配常见价格格式：1000-9999 或 1000.00-9999.99
            price_matches = re.findall(r'\b[1-9]\d{2,4}\.?\d{0,2}\b', text)
            
            for match in price_matches:
                try:
                    price = float(match)
                    if 100 <= price <= 99999:  # 合理价格范围
                        self.logger.info(f"⚡ 快速检测到价格: {price:.2f}")
                        return price
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            return None

# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    detector = RealPriceDetector()
    
    # 测试获取价格
    print("测试获取当前价格...")
    price = detector.get_real_price('current_price')
    if price:
        print(f"获取到价格: {price}")
    else:
        print("未能获取价格")
    
    # 测试获取多区域价格
    print("\n测试获取多区域价格...")
    prices = detector.get_multiple_prices()
    for region, price in prices.items():
        print(f"{region}: {price}")
    
    # 测试自动输入价格
    print("\n测试自动输入价格...")
    success = detector.auto_input_price(price_adjustment=1)
    print(f"自动输入价格{'成功' if success else '失败'}")


class RealPriceDetectorEnhanced(RealPriceDetector):
    """增强版价格检测器，包含多种检测方法"""
    
    def get_price_by_color_detection(self, screenshot=None, debug=False):
        """
        通过颜色检测方式获取价格
        检测特定颜色的数字区域（如红色/绿色价格显示）
        """
        try:
            if screenshot is None:
                import pyautogui
                screenshot = pyautogui.screenshot()
            
            import cv2
            img_array = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            
            # 定义红色和绿色的HSV范围（常见的价格显示颜色）
            red_ranges = [
                (np.array([0, 50, 50]), np.array([10, 255, 255])),    # 红色1
                (np.array([170, 50, 50]), np.array([180, 255, 255]))  # 红色2
            ]
            green_range = (np.array([35, 50, 50]), np.array([85, 255, 255]))  # 绿色
            
            all_ranges = red_ranges + [green_range]
            
            for color_range in all_ranges:
                if isinstance(color_range, tuple) and len(color_range) == 2:
                    lower, upper = color_range
                    mask = cv2.inRange(img_hsv, lower, upper)
                else:
                    continue
                
                # 查找轮廓
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    # 过滤掉太小或太大的区域
                    if 100 < area < 5000:
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # 提取该区域
                        roi = img_array[y:y+h, x:x+w]
                        
                        # OCR识别数字
                        try:
                            import pytesseract
                            text = pytesseract.image_to_string(roi, config='--psm 8 -c tessedit_char_whitelist=0123456789.')
                            
                            import re
                            numbers = re.findall(r'\d+\.?\d*', text)
                            
                            if numbers:
                                prices = [float(num) for num in numbers if 100 <= float(num) <= 100000]
                                if prices:
                                    price = max(prices)
                                    if debug:
                                        print(f"💰 通过颜色检测获取价格: {price} (区域: {x},{y},{w},{h})")
                                    return price
                        except Exception as ocr_e:
                            continue
            
            if debug:
                print("⚠️ 颜色检测未找到价格")
            return None
            
        except Exception as e:
            if debug:
                print(f"❌ 颜色检测价格获取失败: {e}")
            return None

    def get_price_by_template_matching(self, screenshot=None, debug=False):
        """
        通过模板匹配方式获取价格
        在屏幕的关键区域进行精确搜索
        """
        try:
            if screenshot is None:
                import pyautogui
                screenshot = pyautogui.screenshot()
            
            import cv2
            img_array = np.array(screenshot)
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # 在屏幕中央区域搜索（价格通常显示在显眼位置）
            height, width = img_gray.shape
            center_x, center_y = width // 2, height // 2
            
            # 定义搜索区域（屏幕中央的大部分区域）
            search_regions = [
                (center_x - 400, center_y - 300, 800, 600),  # 中央大区域
                (50, 50, width - 100, 200),                   # 顶部区域
                (50, height - 250, width - 100, 200),        # 底部区域
                (width - 300, 50, 250, height - 100),        # 右侧区域
            ]
            
            for region in search_regions:
                x, y, w, h = region
                x, y = max(0, x), max(0, y)
                w, h = min(w, width - x), min(h, height - y)
                
                roi = img_gray[y:y+h, x:x+w]
                
                try:
                    # 使用更精确的OCR配置
                    import pytesseract
                    custom_config = '--psm 6 -c tessedit_char_whitelist=0123456789.'
                    text = pytesseract.image_to_string(roi, config=custom_config)
                    
                    import re
                    # 查找3-6位数的价格模式
                    price_patterns = [
                        r'\b(\d{3,6}\.?\d{0,2})\b',  # 标准价格格式
                        r'(\d{1,3},\d{3}\.?\d{0,2})',  # 带逗号的价格格式
                    ]
                    
                    for pattern in price_patterns:
                        matches = re.findall(pattern, text)
                        if matches:
                            # 清理并转换价格
                            for match in matches:
                                try:
                                    clean_price = match.replace(',', '')
                                    price = float(clean_price)
                                    # 价格合理性检查
                                    if 100 <= price <= 100000:
                                        if debug:
                                            print(f"💰 通过模板匹配获取价格: {price} (区域: {region})")
                                        return price
                                except ValueError:
                                    continue
                except Exception as ocr_e:
                    continue
            
            if debug:
                print("⚠️ 模板匹配未找到价格")
            return None
            
        except Exception as e:
            if debug:
                print(f"❌ 模板匹配价格获取失败: {e}")
            return None

    def get_price_enhanced_fallback(self, debug=True):
        """
        增强版价格获取，使用多种方法的智能回退
        """
        methods = [
            ("手动区域检测", lambda: self._get_price_from_manual_region('current_price')),
            ("颜色检测", lambda: self.get_price_by_color_detection(debug=debug)),
            ("模板匹配", lambda: self.get_price_by_template_matching(debug=debug)),
            ("增强OCR", lambda: self.get_price_from_screen_ocr_enhanced(debug=debug)),
        ]
        
        results = []
        
        for method_name, method_func in methods:
            try:
                if debug:
                    print(f"🔍 尝试{method_name}...")
                price = method_func()
                if price and isinstance(price, (int, float)) and 100 <= price <= 100000:
                    results.append((method_name, price))
                    if debug:
                        print(f"✅ {method_name}成功: {price}")
                else:
                    if debug:
                        print(f"⚠️ {method_name}失败或价格不合理: {price}")
            except Exception as e:
                if debug:
                    print(f"❌ {method_name}出错: {e}")
        
        if results:
            # 如果有多个结果，使用中位数或最常见值
            prices = [price for _, price in results]
            
            if len(prices) == 1:
                final_price = prices[0]
                method_used = results[0][0]
            else:
                # 多个结果时，选择中位数
                prices.sort()
                final_price = prices[len(prices) // 2]
                method_used = "多方法综合"
            
            if debug:
                print(f"🎯 最终价格: {final_price} (来源: {method_used})")
                print(f"📊 所有结果: {results}")
            
            return final_price
        
        if debug:
            print("❌ 所有价格获取方法都失败了")
        return None