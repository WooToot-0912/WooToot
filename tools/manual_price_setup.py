#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动价格区域设置工具
用于设置和管理价格监测区域
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import os
import sys

# 添加源码路径
src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from trading.real_price_detector import RealPriceDetector
    from price_region_selector import PriceRegionSelector
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

class ManualPriceSetupGUI:
    """手动价格设置GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("价格区域设置工具")
        self.root.geometry("500x400")
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化检测器
        self.detector = None
        self.selector = PriceRegionSelector()
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主标题
        title_label = tk.Label(
            self.root, 
            text="景陶易购价格监测区域设置", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # 说明文字
        info_text = """
此工具用于设置价格监测区域，替代OCR方法。
设置完成后，系统将使用手动选择的区域进行价格监测。

操作步骤：
1. 确保景陶易购客户端已打开
2. 点击"设置价格区域"按钮
3. 按提示选择各个价格区域
4. 完成后点击"测试设置"验证
        """
        
        info_label = tk.Label(
            self.root, 
            text=info_text, 
            justify=tk.LEFT,
            wraplength=450
        )
        info_label.pack(pady=10, padx=20)
        
        # 按钮框架
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        # 设置区域按钮
        setup_btn = tk.Button(
            button_frame,
            text="设置价格区域",
            command=self.setup_regions,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12),
            width=15,
            height=2
        )
        setup_btn.pack(side=tk.LEFT, padx=10)
        
        # 测试设置按钮
        test_btn = tk.Button(
            button_frame,
            text="测试设置",
            command=self.test_setup,
            bg="#2196F3",
            fg="white",
            font=("Arial", 12),
            width=15,
            height=2
        )
        test_btn.pack(side=tk.LEFT, padx=10)
        
        # 重置按钮
        reset_btn = tk.Button(
            button_frame,
            text="重置设置",
            command=self.reset_setup,
            bg="#FF9800",
            fg="white",
            font=("Arial", 12),
            width=15,
            height=2
        )
        reset_btn.pack(side=tk.LEFT, padx=10)
        
        # 状态框架
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=20, fill=tk.X, padx=20)
        
        # 状态标签
        self.status_label = tk.Label(
            status_frame,
            text="就绪",
            font=("Arial", 10),
            bg="#f0f0f0",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X)
        
        # 区域状态显示
        self.region_status_frame = tk.LabelFrame(self.root, text="区域配置状态")
        self.region_status_frame.pack(pady=10, fill=tk.X, padx=20)
        
        self.update_region_status()
    
    def update_status(self, message: str):
        """更新状态显示"""
        self.status_label.config(text=message)
        self.root.update()
    
    def update_region_status(self):
        """更新区域配置状态"""
        # 清除现有状态
        for widget in self.region_status_frame.winfo_children():
            widget.destroy()
        
        # 获取已配置的区域
        regions = self.selector.selected_regions
        
        if not regions:
            no_config_label = tk.Label(
                self.region_status_frame,
                text="尚未配置任何价格区域",
                fg="red"
            )
            no_config_label.pack(pady=5)
        else:
            for region_name, region_data in regions.items():
                status_text = f"✓ {region_name}: {region_data.get('description', '')}"
                status_label = tk.Label(
                    self.region_status_frame,
                    text=status_text,
                    fg="green"
                )
                status_label.pack(anchor=tk.W, padx=10)
    
    def setup_regions(self):
        """设置价格区域"""
        try:
            self.update_status("开始设置价格区域...")
            
            # 显示说明
            messagebox.showinfo(
                "开始设置",
                "请确保景陶易购客户端已打开并显示价格信息。\n\n"
                "接下来将逐一设置各个价格区域。\n"
                "请按照提示在截图上拖拽选择相应的价格区域。"
            )
            
            # 隐藏主窗口
            self.root.withdraw()
            
            # 设置区域
            success = self.selector.setup_all_regions()
            
            # 显示主窗口
            self.root.deiconify()
            
            if success:
                self.update_status("价格区域设置完成")
                messagebox.showinfo("设置完成", "所有价格区域设置完成！")
            else:
                self.update_status("价格区域设置未完成")
                messagebox.showwarning("设置未完成", "部分价格区域设置未完成，请重新设置")
            
            # 更新状态显示
            self.update_region_status()
            
        except Exception as e:
            self.update_status(f"设置失败: {e}")
            messagebox.showerror("设置失败", f"设置价格区域时出错：{e}")
            self.root.deiconify()
    
    def test_setup(self):
        """测试设置"""
        try:
            self.update_status("正在测试价格获取...")
            
            if not self.selector.selected_regions:
                messagebox.showwarning("无配置", "请先设置价格区域")
                return
            
            # 获取所有价格
            prices = self.selector.get_all_prices()
            
            if not prices:
                self.update_status("测试失败 - 未获取到任何价格")
                messagebox.showerror("测试失败", "未能获取到任何价格数据")
                return
            
            # 显示测试结果
            result_text = "价格获取测试结果：\n\n"
            for region_name, price in prices.items():
                if price:
                    result_text += f"✓ {region_name}: {price}\n"
                else:
                    result_text += f"✗ {region_name}: 获取失败\n"
            
            self.update_status("测试完成")
            messagebox.showinfo("测试结果", result_text)
            
        except Exception as e:
            self.update_status(f"测试失败: {e}")
            messagebox.showerror("测试失败", f"测试时出错：{e}")
    
    def reset_setup(self):
        """重置设置"""
        try:
            result = messagebox.askyesno(
                "确认重置",
                "这将删除所有已配置的价格区域。\n确定要继续吗？"
            )
            
            if result:
                # 清空配置
                self.selector.selected_regions = {}
                self.selector.save_regions()
                
                self.update_status("设置已重置")
                self.update_region_status()
                messagebox.showinfo("重置完成", "所有价格区域配置已清除")
            
        except Exception as e:
            self.update_status(f"重置失败: {e}")
            messagebox.showerror("重置失败", f"重置时出错：{e}")
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()

def main():
    """主函数"""
    app = ManualPriceSetupGUI()
    app.run()

if __name__ == "__main__":
    main()