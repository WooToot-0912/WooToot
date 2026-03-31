#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能坐标校准工具 - 改进版
支持手动选择窗口，更精确的按钮检测
"""

import sys
import os
import json
import time
import cv2
import numpy as np
import pyautogui
import win32gui
import win32con
from pathlib import Path

# 设置pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

try:
    import pytesseract
    OCR_AVAILABLE = True
    print("✅ OCR功能可用")
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR功能不可用，将使用颜色检测")

class SmartCalibrator:
    """智能坐标校准器"""
    
    def __init__(self):
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
                'color_ranges': [],
                'description': '底部买入订立按钮'
            },
            'sell_order_button': {
                'name': '卖出订立按钮',
                'keywords': ['卖出订立', '卖出确认'],
                'color_ranges': [],
                'description': '底部卖出订立按钮'
            },
            'confirm_button': {
                'name': '确认按钮',
                'keywords': ['确定', '确认', 'OK', '是', '同意'],
                'color_ranges': [],
                'description': '确认对话框按钮'
            },
            'price_input': {
                'name': '价格输入框',
                'keywords': ['价格', '委托价', '单价', '价'],
                'color_ranges': [],
                'description': '价格输入区域'
            },
            'quantity_input': {
                'name': '数量输入框',
                'keywords': ['数量', '委托量', '股数', '量'],
                'color_ranges': [],
                'description': '数量输入区域'
            },
            'transfer_out_button': {
                'name': '银证转出按钮',
                'keywords': ['转出', '银证转出', '转账'],
                'color_ranges': [],
                'description': '银证转出按钮'
            },
            'order_mode_button': {
                'name': '订立模式按钮',
                'keywords': ['订立', '订立模式', '订单'],
                'color_ranges': [],
                'description': '切换到订立模式的按钮'
            }
        }
        
        self.found_coords = {}
        self.client_window = None
        self.window_rect = None
        
    def list_all_windows(self):
        """列出所有可见窗口"""
        def enum_windows(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_text.strip():  # 只显示有标题的窗口
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    if width > 100 and height > 100:  # 过滤太小的窗口
                        windows.append((hwnd, window_text, rect))
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows, windows)
        return windows
    
    def select_client_window(self):
        """选择客户端窗口"""
        print("🔍 正在扫描所有窗口...")
        windows = self.list_all_windows()
        
        if not windows:
            print("❌ 没有找到可用窗口")
            return False
        
        print("\n📋 可用窗口列表:")
        print("=" * 80)
        
        # 先尝试自动匹配
        auto_matches = []
        for i, (hwnd, title, rect) in enumerate(windows):
            if any(keyword in title for keyword in ['景陶', '易购', '交易', '证券', '股票']):
                auto_matches.append((i, hwnd, title, rect))
        
        if auto_matches:
            print("🎯 自动匹配到的可能窗口:")
            for i, hwnd, title, rect in auto_matches:
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                print(f"  [{i}] {title} ({width}x{height})")
        
        print("\n📋 所有窗口:")
        for i, (hwnd, title, rect) in enumerate(windows):
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            print(f"  [{i}] {title} ({width}x{height})")
        
        # 用户选择
        while True:
            try:
                choice = input(f"\n请选择窗口编号 (0-{len(windows)-1}): ").strip()
                if choice == '':
                    return False
                
                index = int(choice)
                if 0 <= index < len(windows):
                    self.client_window = windows[index][0]
                    self.window_rect = windows[index][2]
                    window_title = windows[index][1]
                    
                    print(f"✅ 已选择: {window_title}")
                    print(f"📐 窗口大小: {self.window_rect[2]-self.window_rect[0]}x{self.window_rect[3]-self.window_rect[1]}")
                    return True
                else:
                    print("❌ 编号超出范围，请重新输入")
                    
            except ValueError:
                print("❌ 请输入有效数字")
            except KeyboardInterrupt:
                return False
    
    def capture_and_analyze(self):
        """截图并分析"""
        if not self.client_window:
            print("❌ 未选择窗口")
            return None
        
        print("\n📸 正在截取窗口界面...")
        
        try:
            # 激活窗口
            try:
                win32gui.SetForegroundWindow(self.client_window)
                time.sleep(1)
            except:
                print("⚠️ 无法激活窗口，但继续尝试截图")
            
            # 截图
            x, y, x2, y2 = self.window_rect
            screenshot = pyautogui.screenshot(region=(x, y, x2-x, y2-y))
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            print(f"✅ 截图成功: {screenshot_cv.shape[1]}x{screenshot_cv.shape[0]}")
            
            # 保存截图以便调试
            cv2.imwrite("debug_screenshot.png", screenshot_cv)
            print("💾 调试截图已保存为: debug_screenshot.png")
            
            return screenshot_cv
            
        except Exception as e:
            print(f"❌ 截图失败: {e}")
            return None
    
    def enhanced_color_detection(self, screenshot):
        """增强的颜色检测"""
        print("🎨 进行颜色分析...")
        
        # 转换色彩空间
        hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
        height, width = screenshot.shape[:2]
        
        # 分析红色区域（买入按钮）
        red_mask = np.zeros((height, width), dtype=np.uint8)
        for lower, upper in self.buttons['buy_mode_button']['color_ranges']:
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            red_mask = cv2.bitwise_or(red_mask, mask)
        
        red_centers = self.find_button_candidates(red_mask, "红色区域")
        for center in red_centers:
            self.add_coordinate('buy_mode_button', center[0], center[1], "红色检测")
        
        # 分析绿色区域（卖出按钮）
        green_mask = np.zeros((height, width), dtype=np.uint8)
        for lower, upper in self.buttons['sell_mode_button']['color_ranges']:
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            green_mask = cv2.bitwise_or(green_mask, mask)
        
        green_centers = self.find_button_candidates(green_mask, "绿色区域")
        for center in green_centers:
            self.add_coordinate('sell_mode_button', center[0], center[1], "绿色检测")
        
        # 保存调试图像
        cv2.imwrite("debug_red_mask.png", red_mask)
        cv2.imwrite("debug_green_mask.png", green_mask)
        
    def enhanced_ocr_detection(self, screenshot):
        """增强的OCR检测"""
        if not OCR_AVAILABLE:
            return
        
        print("📝 进行文字识别...")
        
        try:
            # 预处理图像以提高OCR准确性
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # 尝试多种预处理方法
            methods = [
                ("原图", gray),
                ("增强对比度", cv2.convertScaleAbs(gray, alpha=1.5, beta=0)),
                ("二值化", cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])
            ]
            
            for method_name, processed_img in methods:
                print(f"  🔍 使用{method_name}进行OCR...")
                
                # OCR配置
                config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz买卖入出确定认订立价格数量委托银证转账'
                
                # 执行OCR
                data = pytesseract.image_to_data(processed_img, lang='chi_sim', config=config, output_type=pytesseract.Output.DICT)
                
                # 分析结果
                detected_texts = []
                for i, text in enumerate(data['text']):
                    if text.strip() and int(data['conf'][i]) > 30:
                        x = data['left'][i] + data['width'][i] // 2
                        y = data['top'][i] + data['height'][i] // 2
                        detected_texts.append((text, x, y, data['conf'][i]))
                        
                        # 匹配按钮关键词
                        for button_id, button_info in self.buttons.items():
                            for keyword in button_info['keywords']:
                                if keyword in text or text in keyword:
                                    confidence = int(data['conf'][i])
                                    self.add_coordinate(button_id, x, y, f"OCR-{method_name}:{text}({confidence}%)")
                
                if detected_texts:
                    print(f"    识别到 {len(detected_texts)} 个文字")
                    for text, x, y, conf in detected_texts[:5]:  # 只显示前5个
                        print(f"      '{text}' at ({x},{y}) - {conf}%")
                
        except Exception as e:
            print(f"⚠️ OCR检测失败: {e}")
    
    def find_button_candidates(self, mask, region_name, min_area=50, max_area=5000):
        """查找按钮候选区域"""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        
        print(f"  🔍 在{region_name}中找到 {len(contours)} 个轮廓")
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area < area < max_area:
                # 计算边界框
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # 过滤掉不太像按钮的形状
                if 0.3 < aspect_ratio < 3.0:  # 按钮通常不会太细长
                    # 计算中心点
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        candidates.append((cx, cy))
                        print(f"    找到候选点: ({cx}, {cy}) 面积:{area:.0f} 比例:{aspect_ratio:.2f}")
        
        return candidates
    
    def add_coordinate(self, button_id, x, y, method):
        """添加坐标"""
        if not self.window_rect:
            return
        
        # 计算相对坐标
        window_width = self.window_rect[2] - self.window_rect[0]
        window_height = self.window_rect[3] - self.window_rect[1]
        
        rel_x = x / window_width
        rel_y = y / window_height
        
        # 计算绝对坐标
        abs_x = self.window_rect[0] + x
        abs_y = self.window_rect[1] + y
        
        # 避免重复坐标（距离太近的认为是同一个）
        if button_id in self.found_coords:
            for existing in self.found_coords[button_id]:
                if abs(existing['x'] - rel_x) < 0.01 and abs(existing['y'] - rel_y) < 0.01:
                    return  # 太近了，跳过
        
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
        print(f"📍 {self.buttons[button_id]['name']}: ({abs_x}, {abs_y}) - {method}")
    
    def interactive_test(self):
        """交互式测试坐标"""
        if not self.found_coords:
            print("❌ 没有坐标可测试")
            return
        
        print("\n🧪 开始交互式坐标测试")
        print("=" * 50)
        
        for button_id, coords in self.found_coords.items():
            if not coords:
                continue
                
            button_name = self.buttons[button_id]['name']
            print(f"\n🎯 测试 {button_name} ({len(coords)} 个候选位置):")
            
            for i, coord in enumerate(coords):
                print(f"\n  候选 {i+1}: ({coord['abs_x']}, {coord['abs_y']}) - {coord['method']}")
                
                try:
                    # 移动鼠标并高亮
                    pyautogui.moveTo(coord['abs_x'], coord['abs_y'], duration=0.5)
                    
                    # 高亮效果
                    for _ in range(2):
                        pyautogui.moveRel(-8, -8, duration=0.1)
                        pyautogui.moveRel(16, 16, duration=0.1)
                        pyautogui.moveRel(-8, -8, duration=0.1)
                    
                    # 用户选择
                    while True:
                        choice = input("    [c]点击测试 [s]跳过 [n]下一个按钮 [q]退出: ").lower()
                        
                        if choice == 'c':
                            print("    🖱️ 执行点击...")
                            pyautogui.click(coord['abs_x'], coord['abs_y'])
                            
                            # 特殊处理
                            if 'confirm' in button_id:
                                time.sleep(2)
                                pyautogui.press('escape')
                                print("    ⚠️ 已按ESC关闭可能的弹窗")
                            
                            print("    ✅ 点击完成")
                            break
                            
                        elif choice == 's':
                            print("    ⏭️ 跳过此坐标")
                            break
                            
                        elif choice == 'n':
                            print("    ⏭️ 跳到下一个按钮")
                            return
                            
                        elif choice == 'q':
                            print("    🛑 退出测试")
                            return
                            
                        else:
                            print("    ❌ 无效选择，请重新输入")
                
                except Exception as e:
                    print(f"    ❌ 测试失败: {e}")
                    continue
    
    def save_config(self):
        """保存配置"""
        if not self.found_coords:
            print("❌ 没有坐标数据可保存")
            return False
        
        print("\n💾 准备保存配置...")
        
        # 让用户选择最佳坐标
        final_coords = {}
        for button_id, coords in self.found_coords.items():
            if not coords:
                continue
                
            button_name = self.buttons[button_id]['name']
            if len(coords) == 1:
                final_coords[button_id] = coords[0]
                print(f"✅ {button_name}: 自动选择唯一坐标")
            else:
                print(f"\n🎯 {button_name} 有 {len(coords)} 个候选坐标:")
                for i, coord in enumerate(coords):
                    print(f"  [{i}] ({coord['abs_x']}, {coord['abs_y']}) - {coord['method']}")
                
                while True:
                    try:
                        choice = input(f"请选择最佳坐标 (0-{len(coords)-1}): ").strip()
                        if choice == '':
                            break
                        
                        index = int(choice)
                        if 0 <= index < len(coords):
                            final_coords[button_id] = coords[index]
                            print(f"✅ 已选择坐标 {index}")
                            break
                        else:
                            print("❌ 编号超出范围")
                    except ValueError:
                        print("❌ 请输入有效数字")
                    except KeyboardInterrupt:
                        return False
        
        # 创建配置文件
        config_data = {
            "window_info": {
                "title": win32gui.GetWindowText(self.client_window) if self.client_window else "未知",
                "rect": list(self.window_rect) if self.window_rect else [0, 0, 1920, 1080],
                "calibrated_time": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "button_positions": {}
        }
        
        for button_id, coord in final_coords.items():
            button_info = self.buttons[button_id]
            config_data["button_positions"][button_id] = {
                "name": button_info['name'],
                "x": coord['x'],
                "y": coord['y'],
                "calibrated_absolute": {
                    "x": coord['abs_x'],
                    "y": coord['abs_y']
                },
                "description": button_info['description'],
                "method": coord['method']
            }
        
        # 保存文件
        config_file = "smart_coordinates_config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ 配置已保存到: {config_file}")
            print(f"📊 保存了 {len(config_data['button_positions'])} 个按钮配置")
            
            # 显示保存的内容
            print("\n📋 保存的坐标配置:")
            for button_id, button_data in config_data["button_positions"].items():
                rel_x, rel_y = button_data['x'], button_data['y']
                abs_x = button_data['calibrated_absolute']['x']
                abs_y = button_data['calibrated_absolute']['y']
                print(f"  🔘 {button_data['name']}: 相对({rel_x:.6f}, {rel_y:.6f}) 绝对({abs_x}, {abs_y})")
            
            return True
            
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return False
    
    def run_calibration(self):
        """运行完整的校准流程"""
        print("🎯 智能坐标校准工具 v2.0")
        print("=" * 60)
        
        # 步骤1: 选择窗口
        if not self.select_client_window():
            print("❌ 未选择窗口，退出")
            return False
        
        # 步骤2: 截图分析
        screenshot = self.capture_and_analyze()
        if screenshot is None:
            print("❌ 截图失败，退出")
            return False
        
        # 步骤3: 自动检测
        print("\n🤖 开始智能按钮检测...")
        self.enhanced_color_detection(screenshot)
        self.enhanced_ocr_detection(screenshot)
        
        # 步骤4: 显示结果
        print(f"\n📊 检测完成，找到 {sum(len(coords) for coords in self.found_coords.values())} 个坐标候选")
        
        if not self.found_coords:
            print("❌ 未检测到任何按钮，请检查:")
            print("  1. 是否选择了正确的窗口")
            print("  2. 窗口是否包含交易界面")
            print("  3. 界面是否有红色/绿色按钮")
            return False
        
        # 显示检测结果
        for button_id, coords in self.found_coords.items():
            if coords:
                button_name = self.buttons[button_id]['name']
                print(f"  🔘 {button_name}: {len(coords)} 个候选位置")
        
        # 步骤5: 测试坐标
        test_choice = input("\n🧪 是否进行坐标测试？(y/n): ").lower()
        if test_choice == 'y':
            self.interactive_test()
        
        # 步骤6: 保存配置
        save_choice = input("\n💾 是否保存坐标配置？(y/n): ").lower()
        if save_choice == 'y':
            return self.save_config()
        
        return True

def main():
    """主函数"""
    print("🚀 启动智能坐标校准工具")
    
    # 检查依赖
    required = ['cv2', 'numpy', 'pyautogui', 'win32gui']
    missing = []
    
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ 缺少依赖: {missing}")
        print("💡 请安装: pip install opencv-python numpy pyautogui pywin32")
        return
    
    # 运行校准
    calibrator = SmartCalibrator()
    success = calibrator.run_calibration()
    
    if success:
        print("\n🎉 坐标校准完成！")
        print("💡 现在可以运行 'python main_stable.py' 测试新配置")
    else:
        print("\n⚠️ 校准未完成")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()