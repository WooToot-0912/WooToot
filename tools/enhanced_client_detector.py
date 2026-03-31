#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的景陶易购客户端检测器
专门用于检测和识别景陶易购客户端窗口
"""

import os
import sys
import time
import json
from typing import List, Dict, Optional, Tuple

try:
    import win32gui
    import win32con
    import win32api
    import win32process
    WINDOWS_API_AVAILABLE = True
except ImportError:
    WINDOWS_API_AVAILABLE = False
    print("⚠️ Windows API不可用，客户端检测功能受限")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil不可用，进程检测功能受限")

class JingTaoClientDetector:
    """景陶易购客户端检测器"""
    
    def __init__(self):
        self.client_patterns = {
            # 窗口标题关键词
            'title_keywords': [
                '景陶', '易购', 'jingtao', 'yigou', 
                '交易', 'trading', '证券', '股票',
                'client', '客户端'
            ],
            
            # 进程名关键词
            'process_keywords': [
                'jingtao', '景陶', 'yigou', '易购',
                'trading', 'client', 'stock'
            ],
            
            # 窗口类名模式
            'class_patterns': [
                'AfxFrameOrView',      # MFC应用
                'AfxWnd',              # MFC窗口
                'Qt',                  # Qt应用
                'Windows.UI',          # 现代应用
                '#32770',              # 对话框
                'ThunderRT6Form'       # VB应用
            ],
            
            # 文件名模式
            'file_patterns': [
                '景陶易购', 'jingtao', 'yigou',
                'client.exe', 'trading.exe'
            ]
        }
        
        self.detected_clients = []
        
    def detect_all_clients(self) -> List[Dict]:
        """检测所有可能的客户端窗口"""
        self.detected_clients = []
        
        if not WINDOWS_API_AVAILABLE:
            print("❌ Windows API不可用，无法检测客户端")
            return []
        
        print("🔍 开始全面检测景陶易购客户端...")
        
        # 方法1: 枚举所有窗口
        self._detect_by_window_enumeration()
        
        # 方法2: 通过进程检测
        self._detect_by_process_scan()
        
        # 方法3: 通过文件名检测
        self._detect_by_file_scan()
        
        # 去重和评分
        self._deduplicate_and_score()
        
        print(f"✅ 检测完成，找到 {len(self.detected_clients)} 个潜在客户端")
        
        return self.detected_clients
    
    def _detect_by_window_enumeration(self):
        """通过窗口枚举检测"""
        print("  📋 方法1: 枚举所有窗口...")
        
        def enum_callback(hwnd, windows):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                
                # 获取窗口信息
                window_text = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                
                # 获取窗口大小
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                except:
                    return True
                
                # 过滤太小的窗口
                if width < 200 or height < 150:
                    return True
                
                # 评估窗口是否可能是客户端
                score = self._evaluate_window(hwnd, window_text, class_name, rect)
                
                if score > 0:
                    client_info = {
                        'hwnd': hwnd,
                        'title': window_text or f"[{class_name}]",
                        'class': class_name,
                        'rect': rect,
                        'width': width,
                        'height': height,
                        'score': score,
                        'detection_method': 'window_enum',
                        'process_info': self._get_process_info(hwnd)
                    }
                    
                    windows.append(client_info)
                    
            except Exception as e:
                # 忽略单个窗口的错误
                pass
            
            return True
        
        windows = []
        try:
            win32gui.EnumWindows(enum_callback, windows)
            self.detected_clients.extend(windows)
            print(f"    找到 {len(windows)} 个候选窗口")
        except Exception as e:
            print(f"    ❌ 窗口枚举失败: {e}")
    
    def _detect_by_process_scan(self):
        """通过进程扫描检测"""
        print("  🔍 方法2: 扫描所有进程...")
        
        if not PSUTIL_AVAILABLE:
            print("    ⚠️ psutil不可用，跳过进程扫描")
            return
        
        try:
            suspicious_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info.get('name', '').lower()
                    proc_exe = proc_info.get('exe', '') or ''
                    
                    # 检查进程名和可执行文件路径
                    is_suspicious = False
                    for keyword in self.client_patterns['process_keywords']:
                        if keyword.lower() in proc_name or keyword.lower() in proc_exe.lower():
                            is_suspicious = True
                            break
                    
                    if is_suspicious:
                        suspicious_processes.append(proc_info)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 为可疑进程查找对应的窗口
            for proc_info in suspicious_processes:
                pid = proc_info['pid']
                windows = self._find_windows_by_pid(pid)
                
                for hwnd in windows:
                    try:
                        window_text = win32gui.GetWindowText(hwnd)
                        class_name = win32gui.GetClassName(hwnd)
                        rect = win32gui.GetWindowRect(hwnd)
                        
                        client_info = {
                            'hwnd': hwnd,
                            'title': window_text or f"[{class_name}]",
                            'class': class_name,
                            'rect': rect,
                            'width': rect[2] - rect[0],
                            'height': rect[3] - rect[1],
                            'score': 8,  # 进程检测的得分较高
                            'detection_method': 'process_scan',
                            'process_info': proc_info
                        }
                        
                        self.detected_clients.append(client_info)
                        
                    except Exception as e:
                        continue
            
            print(f"    找到 {len(suspicious_processes)} 个可疑进程")
            
        except Exception as e:
            print(f"    ❌ 进程扫描失败: {e}")
    
    def _detect_by_file_scan(self):
        """通过文件扫描检测"""
        print("  📁 方法3: 扫描常见位置...")
        
        # 常见的客户端安装位置
        common_paths = [
            "C:\\景陶易购客户端.exe",
            "C:\\Program Files\\景陶易购\\",
            "C:\\Program Files (x86)\\景陶易购\\",
            "D:\\景陶易购客户端.exe",
            "D:\\Program Files\\景陶易购\\",
            os.path.expanduser("~/Desktop/景陶易购客户端.exe"),
            os.path.expanduser("~/AppData/Local/景陶易购/"),
            os.path.expanduser("~/AppData/Roaming/景陶易购/")
        ]
        
        found_files = []
        for path in common_paths:
            if os.path.exists(path):
                found_files.append(path)
                print(f"    ✅ 找到客户端文件: {path}")
        
        print(f"    找到 {len(found_files)} 个客户端文件")
    
    def _evaluate_window(self, hwnd, title, class_name, rect) -> int:
        """评估窗口是否可能是客户端"""
        score = 0
        
        # 评估窗口标题
        for keyword in self.client_patterns['title_keywords']:
            if keyword.lower() in title.lower():
                score += 3
                break
        
        # 评估窗口类名
        for pattern in self.client_patterns['class_patterns']:
            if pattern.lower() in class_name.lower():
                score += 2
                break
        
        # 评估窗口大小（交易软件通常有一定的最小尺寸）
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        
        if 800 <= width <= 1920 and 600 <= height <= 1080:
            score += 2
        elif 600 <= width <= 800 and 400 <= height <= 600:
            score += 1
        
        # 评估进程信息
        process_info = self._get_process_info(hwnd)
        if process_info:
            proc_name = process_info.get('name', '').lower()
            for keyword in self.client_patterns['process_keywords']:
                if keyword.lower() in proc_name:
                    score += 3
                    break
        
        return score
    
    def _get_process_info(self, hwnd) -> Optional[Dict]:
        """获取窗口对应的进程信息"""
        try:
            if not PSUTIL_AVAILABLE:
                return None
                
            thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            
            return {
                'pid': pid,
                'name': process.name(),
                'exe': process.exe(),
                'cmdline': ' '.join(process.cmdline()) if hasattr(process, 'cmdline') else '',
                'create_time': process.create_time()
            }
            
        except Exception:
            return None
    
    def _find_windows_by_pid(self, pid) -> List[int]:
        """根据进程ID查找窗口"""
        windows = []
        
        def enum_callback(hwnd, windows_list):
            try:
                thread_id, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                if window_pid == pid and win32gui.IsWindowVisible(hwnd):
                    windows_list.append(hwnd)
            except:
                pass
            return True
        
        try:
            win32gui.EnumWindows(enum_callback, windows)
        except:
            pass
        
        return windows
    
    def _deduplicate_and_score(self):
        """去重和重新评分"""
        # 根据hwnd去重
        seen_hwnds = set()
        unique_clients = []
        
        for client in self.detected_clients:
            hwnd = client['hwnd']
            if hwnd not in seen_hwnds:
                seen_hwnds.add(hwnd)
                unique_clients.append(client)
        
        # 按得分排序
        unique_clients.sort(key=lambda x: x['score'], reverse=True)
        
        self.detected_clients = unique_clients
    
    def get_best_client(self) -> Optional[Dict]:
        """获取最可能的客户端"""
        if not self.detected_clients:
            return None
        
        return self.detected_clients[0]
    
    def get_all_clients(self) -> List[Dict]:
        """获取所有检测到的客户端"""
        return self.detected_clients
    
    def display_results(self):
        """显示检测结果"""
        if not self.detected_clients:
            print("❌ 没有检测到景陶易购客户端")
            print("\n💡 建议:")
            print("1. 确保景陶易购客户端正在运行")
            print("2. 确保客户端窗口可见（未最小化）")
            print("3. 尝试手动选择窗口")
            return
        
        print(f"\n📊 检测结果 (共 {len(self.detected_clients)} 个):")
        print("=" * 80)
        
        for i, client in enumerate(self.detected_clients):
            title = client['title']
            score = client['score']
            method = client['detection_method']
            size_info = f"{client['width']}x{client['height']}"
            
            print(f"[{i}] 得分:{score} | {title} | {size_info} | 方法:{method}")
            
            if client.get('process_info'):
                proc_info = client['process_info']
                print(f"    进程: {proc_info.get('name', 'Unknown')} (PID: {proc_info.get('pid', 'Unknown')})")
        
        # 推荐最佳选择
        best_client = self.get_best_client()
        if best_client:
            print(f"\n🎯 推荐客户端: {best_client['title']} (得分: {best_client['score']})")

def main():
    """主函数 - 用于测试"""
    print("🚀 景陶易购客户端检测器")
    print("=" * 50)
    
    detector = JingTaoClientDetector()
    clients = detector.detect_all_clients()
    detector.display_results()
    
    if clients:
        print(f"\n✅ 检测完成，建议使用得分最高的客户端")
    else:
        print(f"\n❌ 未检测到客户端，请检查:")
        print("1. 景陶易购客户端是否正在运行")
        print("2. 客户端窗口是否可见")
        print("3. 是否有权限访问窗口信息")

if __name__ == "__main__":
    main()