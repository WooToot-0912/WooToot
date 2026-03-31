#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
演示高级界面 - 展示智能量化交易系统的高级功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
from datetime import datetime
import random

class DemoAdvancedWindow:
    """演示高级窗口"""
    
    def __init__(self):
        """初始化演示窗口"""
        self.root = tk.Tk()
        self.root.title("🎯 智能量化交易系统 v2.0 - 高级演示版")
        self.root.geometry("1400x900")
        
        # 状态变量
        self.is_monitoring = False
        self.demo_data = {
            "trades_today": 0,
            "success_rate": 0.0,
            "total_pnl": 0.0,
            "positions": 0
        }
        
        self.setup_styles()
        self.create_widgets()
        self.start_demo_updates()
        
        print("✅ 演示界面初始化完成")
    
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            style.theme_use('default')
        
        # 自定义样式
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'), foreground='#2c3e50')
        style.configure('Heading.TLabel', font=('Arial', 11, 'bold'), foreground='#34495e')
        style.configure('Status.TLabel', font=('Arial', 9), foreground='#27ae60')
        style.configure('Error.TLabel', font=('Arial', 9), foreground='#e74c3c')
        style.configure('Success.TButton', foreground='white')
        style.configure('Warning.TButton', foreground='white')
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主容器
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧控制面板
        self.create_left_panel(main_container)
        
        # 中央监控面板
        self.create_center_panel(main_container)
        
        # 右侧日志面板
        self.create_right_panel(main_container)
        
        # 底部状态栏
        self.create_status_bar()
    
    def create_left_panel(self, parent):
        """创建左侧控制面板"""
        left_frame = ttk.Frame(parent)
        parent.add(left_frame, weight=1)
        
        # 标题
        ttk.Label(left_frame, text="🎯 交易控制", style='Title.TLabel').pack(pady=10)
        
        # 交易模式
        mode_group = ttk.LabelFrame(left_frame, text="🔄 交易模式")
        mode_group.pack(fill=tk.X, padx=10, pady=5)
        
        self.trading_mode_var = tk.StringVar(value="hybrid")
        ttk.Radiobutton(mode_group, text="🤖 纯API模式", variable=self.trading_mode_var, 
                       value="api_only").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(mode_group, text="👁️ 纯图像模式", variable=self.trading_mode_var, 
                       value="image_only").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(mode_group, text="🔗 混合模式", variable=self.trading_mode_var, 
                       value="hybrid").pack(anchor=tk.W, padx=10, pady=2)
        
        # 监控商品
        product_group = ttk.LabelFrame(left_frame, text="📊 监控商品")
        product_group.pack(fill=tk.X, padx=10, pady=5)
        
        self.product_vars = {}
        products = [("511", "韩式陶瓷茶具"), ("507", "五福临门茶碗"), ("512", "寿桃陶瓷茶器")]
        
        for code, name in products:
            var = tk.BooleanVar(value=True)
            self.product_vars[code] = var
            ttk.Checkbutton(product_group, text=f"{code} - {name}", 
                           variable=var).pack(anchor=tk.W, padx=10, pady=2)
        
        # 交易参数
        param_group = ttk.LabelFrame(left_frame, text="⚙️ 交易参数")
        param_group.pack(fill=tk.X, padx=10, pady=5)
        
        param_frame = ttk.Frame(param_group)
        param_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(param_frame, text="📈 止盈点数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.take_profit_var = tk.DoubleVar(value=3.0)
        ttk.Spinbox(param_frame, from_=0.5, to=20.0, increment=0.5, 
                   textvariable=self.take_profit_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(param_frame, text="📉 止损点数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.stop_loss_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(param_frame, from_=0.5, to=20.0, increment=0.5, 
                   textvariable=self.stop_loss_var, width=10).grid(row=1, column=1, padx=5)
        
        # 控制按钮
        control_group = ttk.LabelFrame(left_frame, text="🎮 控制操作")
        control_group.pack(fill=tk.X, padx=10, pady=5)
        
        button_frame = ttk.Frame(control_group)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="🚀 启动监控", 
                                      command=self.start_monitoring, style='Success.TButton')
        self.start_button.pack(fill=tk.X, pady=2)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ 停止监控", 
                                     command=self.stop_monitoring, style='Warning.TButton')
        self.stop_button.pack(fill=tk.X, pady=2)
        
        # 高级设置
        advanced_group = ttk.LabelFrame(left_frame, text="🔧 高级设置")
        advanced_group.pack(fill=tk.X, padx=10, pady=5)
        
        advanced_frame = ttk.Frame(advanced_group)
        advanced_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(advanced_frame, text="🔗 API权重:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.api_weight_var = tk.DoubleVar(value=0.6)
        ttk.Scale(advanced_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL,
                 variable=self.api_weight_var, length=150).grid(row=0, column=1, padx=5)
        
        ttk.Label(advanced_frame, text="👁️ 图像权重:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.image_weight_var = tk.DoubleVar(value=0.4)
        ttk.Scale(advanced_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL,
                 variable=self.image_weight_var, length=150).grid(row=1, column=1, padx=5)
    
    def create_center_panel(self, parent):
        """创建中央监控面板"""
        center_frame = ttk.Frame(parent)
        parent.add(center_frame, weight=2)
        
        # 标题
        ttk.Label(center_frame, text="📊 实时监控", style='Title.TLabel').pack(pady=10)
        
        # 系统状态
        status_group = ttk.LabelFrame(center_frame, text="🔄 系统状态")
        status_group.pack(fill=tk.X, padx=10, pady=5)
        
        status_grid = ttk.Frame(status_group)
        status_grid.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(status_grid, text="系统状态:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.system_status_label = ttk.Label(status_grid, text="🔴 未启动", style='Status.TLabel')
        self.system_status_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(status_grid, text="交易模式:", font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky=tk.W, padx=5)
        self.trading_mode_label = ttk.Label(status_grid, text="🔗 混合模式", style='Status.TLabel')
        self.trading_mode_label.grid(row=0, column=3, sticky=tk.W, padx=10)
        
        # 交易统计
        stats_group = ttk.LabelFrame(center_frame, text="📈 交易统计")
        stats_group.pack(fill=tk.X, padx=10, pady=5)
        
        stats_grid = ttk.Frame(stats_group)
        stats_grid.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(stats_grid, text="今日交易:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.today_trades_label = ttk.Label(stats_grid, text="0", style='Status.TLabel')
        self.today_trades_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(stats_grid, text="成功率:", font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky=tk.W, padx=5)
        self.success_rate_label = ttk.Label(stats_grid, text="0%", style='Status.TLabel')
        self.success_rate_label.grid(row=0, column=3, sticky=tk.W, padx=10)
        
        ttk.Label(stats_grid, text="总盈亏:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.total_pnl_label = ttk.Label(stats_grid, text="0.00", style='Status.TLabel')
        self.total_pnl_label.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(stats_grid, text="持仓数量:", font=('Arial', 10, 'bold')).grid(row=1, column=2, sticky=tk.W, padx=5)
        self.position_count_label = ttk.Label(stats_grid, text="0", style='Status.TLabel')
        self.position_count_label.grid(row=1, column=3, sticky=tk.W, padx=10)
        
        # 实时价格表格
        price_group = ttk.LabelFrame(center_frame, text="💰 实时价格")
        price_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        price_frame = ttk.Frame(price_group)
        price_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("商品代码", "商品名称", "当前价格", "涨跌", "涨跌幅", "信号", "状态")
        self.price_tree = ttk.Treeview(price_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.price_tree.heading(col, text=col)
            self.price_tree.column(col, width=100, anchor=tk.CENTER)
        
        price_scrollbar = ttk.Scrollbar(price_frame, orient=tk.VERTICAL, command=self.price_tree.yview)
        self.price_tree.configure(yscrollcommand=price_scrollbar.set)
        
        self.price_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        price_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加示例数据
        self.update_price_data()
    
    def create_right_panel(self, parent):
        """创建右侧日志面板"""
        right_frame = ttk.Frame(parent)
        parent.add(right_frame, weight=1)
        
        # 标题
        ttk.Label(right_frame, text="📝 系统日志", style='Title.TLabel').pack(pady=10)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(right_frame, height=25, width=50, 
                                                 font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 日志控制按钮
        log_control_frame = ttk.Frame(right_frame)
        log_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_control_frame, text="🧹 清空", command=self.clear_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_control_frame, text="💾 保存", command=self.save_log).pack(side=tk.LEFT, padx=2)
        
        # 添加初始日志
        self.add_log("🎯 智能量化交易系统启动")
        self.add_log("✅ 界面初始化完成")
        self.add_log("📊 等待用户操作...")
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_frame, text="🔴 系统未启动", style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.time_label = ttk.Label(self.status_frame, text="", style='Status.TLabel')
        self.time_label.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def start_monitoring(self):
        """启动监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.add_log("🚀 启动智能量化交易监控")
            self.system_status_label.config(text="🟢 运行中")
            self.status_label.config(text="🟢 系统运行中")
            
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            
            # 启动模拟交易
            self.start_demo_trading()
    
    def stop_monitoring(self):
        """停止监控"""
        if self.is_monitoring:
            self.is_monitoring = False
            self.add_log("⏹️ 停止智能量化交易监控")
            self.system_status_label.config(text="🔴 已停止")
            self.status_label.config(text="🔴 系统已停止")
            
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
    
    def start_demo_trading(self):
        """启动模拟交易"""
        def demo_trading_loop():
            while self.is_monitoring:
                try:
                    # 模拟交易信号
                    if random.random() < 0.3:  # 30%概率产生交易信号
                        self.simulate_trade()
                    
                    # 更新价格数据
                    self.update_price_data()
                    
                    time.sleep(2)  # 每2秒更新一次
                    
                except Exception as e:
                    self.add_log(f"❌ 模拟交易错误: {e}")
        
        threading.Thread(target=demo_trading_loop, daemon=True).start()
    
    def simulate_trade(self):
        """模拟交易"""
        products = ["511", "507", "512"]
        product = random.choice(products)
        direction = random.choice(["买涨", "买跌"])
        price = round(3000 + random.uniform(-50, 50), 2)
        
        self.add_log(f"🎯 信号检测: 商品{product} {direction}信号 基准价{price}")
        self.add_log(f"📋 开始下单: 商品{product} {direction}")
        
        # 模拟下单过程
        time.sleep(0.5)
        self.add_log(f"✅ 下单成功: 商品{product} {direction} 价格{price} 数量1手")
        
        # 更新统计数据
        self.demo_data["trades_today"] += 1
        
        # 模拟盈亏
        pnl = round(random.uniform(-5, 8), 2)
        self.demo_data["total_pnl"] += pnl
        
        if pnl > 0:
            self.demo_data["success_rate"] = (self.demo_data["success_rate"] * (self.demo_data["trades_today"] - 1) + 100) / self.demo_data["trades_today"]
            self.add_log(f"✅ 平仓成功: 商品{product} 盈利{pnl}点")
        else:
            self.demo_data["success_rate"] = (self.demo_data["success_rate"] * (self.demo_data["trades_today"] - 1)) / self.demo_data["trades_today"]
            self.add_log(f"❌ 平仓亏损: 商品{product} 亏损{abs(pnl)}点")
        
        # 更新界面显示
        self.root.after(0, self.update_stats_display)
    
    def update_price_data(self):
        """更新价格数据"""
        # 清空现有数据
        for item in self.price_tree.get_children():
            self.price_tree.delete(item)
        
        # 添加新数据
        products_data = [
            ("511", "韩式陶瓷茶具", round(3000 + random.uniform(-10, 10), 2)),
            ("507", "五福临门茶碗", round(2995 + random.uniform(-8, 8), 2)),
            ("512", "寿桃陶瓷茶器", round(3005 + random.uniform(-12, 12), 2)),
        ]
        
        for code, name, price in products_data:
            change = round(random.uniform(-3, 3), 2)
            change_pct = round((change / price) * 100, 2)
            signal = random.choice(["🟢 买涨", "🔴 买跌", "🟡 观望"])
            status = "监控中" if self.is_monitoring else "待启动"
            
            self.price_tree.insert("", tk.END, values=(
                code, name, f"{price:.2f}", 
                f"{change:+.2f}", f"{change_pct:+.2f}%", 
                signal, status
            ))
    
    def update_stats_display(self):
        """更新统计显示"""
        self.today_trades_label.config(text=str(self.demo_data["trades_today"]))
        self.success_rate_label.config(text=f"{self.demo_data['success_rate']:.1f}%")
        self.total_pnl_label.config(text=f"{self.demo_data['total_pnl']:+.2f}")
        self.position_count_label.config(text=str(random.randint(0, 3)))
    
    def start_demo_updates(self):
        """启动演示更新"""
        def update_time():
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_label.config(text=f"🕐 {current_time}")
            self.root.after(1000, update_time)
        
        update_time()
    
    def add_log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.insert(tk.END, formatted_message + "\n")
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.add_log("🧹 日志已清空")
    
    def save_log(self):
        """保存日志"""
        self.add_log("💾 日志保存功能演示")
        messagebox.showinfo("保存成功", "日志保存功能演示完成！")
    
    def run(self):
        """运行演示窗口"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            print(f"❌ 运行演示窗口失败: {e}")
    
    def on_closing(self):
        """关闭事件"""
        self.is_monitoring = False
        self.root.quit()
        self.root.destroy()

def main():
    """启动演示"""
    print("🚀 启动高级界面演示...")
    app = DemoAdvancedWindow()
    print("🎯 演示界面启动成功！")
    app.run()

if __name__ == "__main__":
    main()
