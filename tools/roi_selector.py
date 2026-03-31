#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROI区域选择工具
帮助用户手动选择黄线检测区域
"""

import cv2
import numpy as np
import pyautogui
import tkinter as tk
from tkinter import messagebox, ttk
import json
import os

class ROISelector:
    """ROI区域选择器"""
    
    def __init__(self):
        self.roi_region = None
        self.config_file = None
        
    def select_roi_interactive(self):
        """交互式选择ROI区域"""
        try:
            # 截取屏幕
            print("📸 正在截取屏幕...")
            screenshot = pyautogui.screenshot()
            screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 使用OpenCV的selectROI功能
            cv2.namedWindow('选择黄线检测区域 - 拖拽选择后按SPACE确认或ESC取消', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('选择黄线检测区域 - 拖拽选择后按SPACE确认或ESC取消', 1200, 800)
            
            print("🖱️  请在弹出窗口中拖拽选择黄线区域...")
            print("   - 拖拽鼠标选择区域")
            print("   - 按SPACE键确认选择")
            print("   - 按ESC键取消选择")
            
            roi = cv2.selectROI('选择黄线检测区域 - 拖拽选择后按SPACE确认或ESC取消', screenshot_np, False, False)
            cv2.destroyAllWindows()
            
            if roi[2] > 0 and roi[3] > 0:  # 确保选择了有效区域
                self.roi_region = roi
                print(f"✅ ROI区域已选择: x={roi[0]}, y={roi[1]}, w={roi[2]}, h={roi[3]}")
                return True
            else:
                print("⚠️ 未选择有效区域")
                return False
                
        except Exception as e:
            print(f"❌ ROI选择失败: {e}")
            return False
    
    def save_roi_to_config(self, config_path=None):
        """保存ROI到配置文件"""
        if not self.roi_region:
            print("⚠️ 没有ROI区域可保存")
            return False
            
        if not config_path:
            # 查找配置文件
            possible_paths = [
                "config/smart_coordinates_config.json",
                "../config/smart_coordinates_config.json",
                "../../config/smart_coordinates_config.json",
                "smart_coordinates_config.json"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
        
        if not config_path:
            print("❌ 找不到配置文件")
            return False
            
        try:
            # 读取现有配置
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 添加ROI配置
            if 'detection_regions' not in config:
                config['detection_regions'] = {}
            
            config['detection_regions']['yellow_line_roi'] = {
                'x': int(self.roi_region[0]),
                'y': int(self.roi_region[1]),
                'width': int(self.roi_region[2]),
                'height': int(self.roi_region[3]),
                'description': '黄线检测区域'
            }
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"✅ ROI区域已保存到配置文件: {config_path}")
            self.config_file = config_path
            return True
            
        except Exception as e:
            print(f"❌ 保存ROI配置失败: {e}")
            return False
    
    def create_gui(self):
        """创建图形界面"""
        root = tk.Tk()
        root.title("黄线检测ROI选择器")
        root.geometry("400x300")
        root.resizable(False, False)
        
        # 标题
        title_label = tk.Label(root, text="黄线检测区域选择器", 
                              font=("Arial", 16, "bold"), fg="blue")
        title_label.pack(pady=20)
        
        # 说明文字
        info_text = """
请按照以下步骤操作：

1. 确保景陶易购客户端已打开
2. 点击"选择ROI区域"按钮
3. 在弹出窗口中拖拽选择黄线区域
4. 按SPACE键确认，ESC键取消
5. 选择完成后点击"保存配置"
        """
        
        info_label = tk.Label(root, text=info_text, justify=tk.LEFT, 
                             font=("Arial", 10), wraplength=350)
        info_label.pack(pady=10)
        
        # 状态显示
        self.status_var = tk.StringVar(value="准备就绪")
        status_label = tk.Label(root, textvariable=self.status_var, 
                               font=("Arial", 10), fg="green")
        status_label.pack(pady=5)
        
        # 按钮框架
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)
        
        # 选择ROI按钮
        select_btn = tk.Button(button_frame, text="选择ROI区域", 
                              command=self.on_select_roi,
                              bg="lightblue", font=("Arial", 12), width=15)
        select_btn.pack(side=tk.LEFT, padx=10)
        
        # 保存配置按钮
        save_btn = tk.Button(button_frame, text="保存配置", 
                            command=self.on_save_config,
                            bg="lightgreen", font=("Arial", 12), width=15)
        save_btn.pack(side=tk.LEFT, padx=10)
        
        # 退出按钮
        exit_btn = tk.Button(root, text="退出", command=root.destroy,
                            bg="lightcoral", font=("Arial", 12), width=10)
        exit_btn.pack(pady=10)
        
        self.root = root
        root.mainloop()
    
    def on_select_roi(self):
        """选择ROI按钮回调"""
        self.status_var.set("正在选择ROI区域...")
        self.root.update()
        
        # 最小化窗口
        self.root.iconify()
        
        try:
            if self.select_roi_interactive():
                self.status_var.set(f"ROI已选择: {self.roi_region}")
                messagebox.showinfo("成功", "ROI区域选择成功！\n请点击'保存配置'按钮保存设置。")
            else:
                self.status_var.set("ROI选择失败或取消")
                messagebox.showwarning("取消", "ROI选择失败或被取消")
        except Exception as e:
            self.status_var.set(f"错误: {e}")
            messagebox.showerror("错误", f"ROI选择出错: {e}")
        finally:
            # 恢复窗口
            self.root.deiconify()
    
    def on_save_config(self):
        """保存配置按钮回调"""
        if not self.roi_region:
            messagebox.showwarning("警告", "请先选择ROI区域")
            return
        
        try:
            if self.save_roi_to_config():
                self.status_var.set("配置已保存")
                messagebox.showinfo("成功", f"ROI配置已保存到:\n{self.config_file}")
            else:
                self.status_var.set("保存失败")
                messagebox.showerror("失败", "保存ROI配置失败")
        except Exception as e:
            self.status_var.set(f"保存错误: {e}")
            messagebox.showerror("错误", f"保存配置出错: {e}")

def main():
    """主函数"""
    print("🎯 黄线检测ROI选择器")
    print("=" * 40)
    print("\n📋 准备步骤:")
    print("1. 请先打开景陶易购客户端")
    print("2. 确保图表界面完全显示")
    print("3. 确保可以看到黄线或需要检测的线条")
    print("4. 准备好后按回车键继续...")
    
    # 等待用户准备
    input()
    
    print("\n⏳ 5秒后开始截屏，请准备好客户端界面...")
    import time
    for i in range(5, 0, -1):
        print(f"   {i}秒...")
        time.sleep(1)
    
    selector = ROISelector()
    
    try:
        print("\n📸 正在截屏并开始ROI选择...")
        if selector.select_roi_interactive():
            if selector.save_roi_to_config():
                print("✅ ROI配置完成！")
                print("🚀 现在可以重新运行主程序测试检测效果！")
            else:
                print("❌ 配置保存失败")
        else:
            print("❌ ROI选择失败或被取消")
            
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")
    except Exception as e:
        print(f"❌ 程序出错: {e}")
        
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()