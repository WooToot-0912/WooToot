#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
真实高级窗口 - 集成所有真实交易功能的高级界面
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

# 添加项目路径
current_dir = Path(__file__).parent.parent
main_project_path = current_dir.parent / "Main"
auto_system_path = current_dir.parent / "自动交易系统"

sys.path.extend([
    str(current_dir),
    str(main_project_path),
    str(auto_system_path),
    str(main_project_path / "core"),
    str(main_project_path / "api"),
    str(auto_system_path / "core"),
    str(auto_system_path / "app" / "src"),
    str(current_dir / "hybrid_core")
])

try:
    # 导入真实的交易组件
    from Main.core.auto_trading_system import AutoTradingSystem
    from Main.api.jingtao_api import JingTaoAPI
    from hybrid_core.hybrid_trading_engine import HybridTradingEngine, TradingMode
    from hybrid_core.signal_fusion_engine import SignalFusionEngine, TradingSignal
    REAL_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 部分真实组件不可用: {e}")
    REAL_COMPONENTS_AVAILABLE = False

class RealAdvancedWindow:
    """真实高级窗口 - 集成所有真实功能"""
    
    def __init__(self):
        """初始化真实高级窗口"""
        self.root = tk.Tk()
        self.root.title("🎯 智能量化交易系统 v2.0 - 真实高级版")
        self.root.geometry("1600x1000")
        self.root.minsize(1400, 800)
        
        # 用户信息
        self.current_user = ""
        self.user_password = ""
        self.is_logged_in = False
        
        # 核心组件初始化
        self.initialize_real_components()
        
        # 状态变量
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # 配置数据
        self.config_data = self.load_config()
        
        # 实时数据
        self.real_data = {
            "positions": [],
            "orders": [],
            "trades_today": 0,
            "total_pnl": 0.0,
            "current_prices": {},
            "api_status": "disconnected",
            "image_status": "stopped"
        }
        
        # 创建界面
        self.setup_styles()
        self.create_menu_bar()
        self.create_widgets()
        self.setup_layout()
        self.bind_events()
        self.setup_real_logging()
        
        # 启动实时更新
        self.start_real_updates()
        
        print("✅ 真实高级窗口初始化完成")
    
    def initialize_real_components(self):
        """初始化真实组件"""
        try:
            if REAL_COMPONENTS_AVAILABLE:
                # 初始化真实的交易引擎
                self.hybrid_engine = HybridTradingEngine()
                self.api_trader = None  # 将在登录后初始化
                self.signal_fusion = SignalFusionEngine()
                
                print("✅ 真实交易组件初始化成功")
            else:
                # 使用占位符组件
                self.hybrid_engine = None
                self.api_trader = None
                self.signal_fusion = None
                
                print("⚠️ 使用占位符组件")
                
        except Exception as e:
            print(f"❌ 初始化真实组件失败: {e}")
            self.hybrid_engine = None
            self.api_trader = None
            self.signal_fusion = None
    
    def setup_real_logging(self):
        """设置真实日志系统"""
        # 创建日志处理器，将日志输出到GUI
        class RealGUILogHandler(logging.Handler):
            def __init__(self, window):
                super().__init__()
                self.window = window
                
            def emit(self, record):
                try:
                    msg = self.format(record)
                    
                    # 根据日志级别分发到不同的日志框
                    if record.levelno >= logging.ERROR:
                        self.window.add_error_log(msg)
                    elif "交易" in msg or "下单" in msg or "平仓" in msg:
                        self.window.add_trading_log(msg)
                    else:
                        self.window.add_system_log(msg)
                        
                except Exception:
                    pass
        
        # 配置根日志器
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # 添加GUI处理器
        gui_handler = RealGUILogHandler(self)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', 
                                     datefmt='%H:%M:%S')
        gui_handler.setFormatter(formatter)
        logger.addHandler(gui_handler)
        
        # 添加文件处理器
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(
                log_dir / f"real_trading_{datetime.now().strftime('%Y%m%d')}.log",
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"❌ 创建文件日志失败: {e}")
    
    def load_config(self) -> Dict:
        """加载真实配置"""
        try:
            config_file = Path("config/real_config.json")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 创建真实配置
                default_config = {
                    "trading": {
                        "take_profit_points": 3.0,
                        "stop_loss_points": 2.0,
                        "max_trades_per_day": 20,
                        "position_size": 1,
                        "enable_auto_trading": True
                    },
                    "api": {
                        "timeout": 30,
                        "retry_count": 3,
                        "base_url": "https://api.jingtao.com"
                    },
                    "image": {
                        "screenshot_interval": 2.0,
                        "detection_accuracy": 0.8,
                        "enable_debug": False
                    },
                    "fusion": {
                        "api_weight": 0.6,
                        "image_weight": 0.4,
                        "confirmation_threshold": 0.7
                    },
                    "risk": {
                        "max_daily_loss": 500.0,
                        "max_consecutive_losses": 3,
                        "enable_risk_control": True
                    }
                }
                
                self.save_config(default_config)
                return default_config
                
        except Exception as e:
            logging.error(f"加载配置失败: {e}")
            return {}
    
    def save_config(self, config: Dict):
        """保存配置"""
        try:
            config_file = Path("config/real_config.json")
            config_file.parent.mkdir(exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logging.error(f"保存配置失败: {e}")
    
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
        style.configure('Warning.TLabel', font=('Arial', 9), foreground='#f39c12')
        style.configure('Success.TButton', foreground='white')
        style.configure('Warning.TButton', foreground='white')
        style.configure('Danger.TButton', foreground='white')
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 系统菜单
        system_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🔧 系统", menu=system_menu)
        system_menu.add_command(label="🔑 重新登录", command=self.relogin)
        system_menu.add_command(label="🔄 重新连接API", command=self.reconnect_api)
        system_menu.add_command(label="📊 刷新数据", command=self.refresh_all_real_data)
        system_menu.add_separator()
        system_menu.add_command(label="🚪 退出", command=self.on_closing)
        
        # 交易菜单
        trading_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="💰 交易", menu=trading_menu)
        trading_menu.add_command(label="📊 查看持仓", command=self.refresh_positions)
        trading_menu.add_command(label="📋 查看委托", command=self.refresh_orders)
        trading_menu.add_command(label="💰 强制平仓", command=self.force_close_all_positions)
        trading_menu.add_command(label="🗑️ 撤销所有委托", command=self.cancel_all_orders)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🔧 工具", menu=tools_menu)
        tools_menu.add_command(label="🧪 测试API连接", command=self.test_real_api)
        tools_menu.add_command(label="📸 测试图像识别", command=self.test_real_image)
        tools_menu.add_command(label="💾 导出交易记录", command=self.export_real_trades)
        tools_menu.add_command(label="📊 生成交易报告", command=self.generate_trading_report)
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主容器
        self.main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        
        # 创建顶部工具栏
        self.create_real_toolbar()
        
        # 创建左侧控制面板
        self.create_real_left_panel()
        
        # 创建中央监控面板
        self.create_real_center_panel()
        
        # 创建右侧日志面板
        self.create_real_right_panel()
        
        # 创建底部状态栏
        self.create_real_status_bar()
    
    def create_real_toolbar(self):
        """创建真实工具栏"""
        self.toolbar_frame = ttk.Frame(self.root)
        
        # 用户信息区域
        user_frame = ttk.Frame(self.toolbar_frame)
        user_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.user_label = ttk.Label(user_frame, text="👤 用户: 未登录", style='Status.TLabel')
        self.user_label.pack(side=tk.LEFT)
        
        self.login_button = ttk.Button(user_frame, text="🔑 登录", command=self.show_login_dialog)
        self.login_button.pack(side=tk.LEFT, padx=(10, 0))
        
        self.logout_button = ttk.Button(user_frame, text="🚪 退出", command=self.logout, 
                                       style='Warning.TButton', state='disabled')
        self.logout_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # 连接状态
        status_frame = ttk.Frame(self.toolbar_frame)
        status_frame.pack(side=tk.LEFT, padx=20, pady=5)
        
        self.api_status_label = ttk.Label(status_frame, text="🔴 API未连接", style='Error.TLabel')
        self.api_status_label.pack(side=tk.LEFT, padx=5)
        
        self.image_status_label = ttk.Label(status_frame, text="🔴 图像未启动", style='Error.TLabel')
        self.image_status_label.pack(side=tk.LEFT, padx=5)
        
        # 快速操作按钮
        quick_frame = ttk.Frame(self.toolbar_frame)
        quick_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        
        self.quick_start_button = ttk.Button(quick_frame, text="⚡ 快速启动", 
                                           command=self.quick_start_real_trading, 
                                           style='Success.TButton', state='disabled')
        self.quick_start_button.pack(side=tk.LEFT, padx=2)
        
        self.emergency_stop_button = ttk.Button(quick_frame, text="🛑 紧急停止", 
                                              command=self.emergency_stop_real_trading, 
                                              style='Danger.TButton')
        self.emergency_stop_button.pack(side=tk.LEFT, padx=2)
        
        self.refresh_button = ttk.Button(quick_frame, text="🔄 刷新数据", 
                                       command=self.refresh_all_real_data)
        self.refresh_button.pack(side=tk.LEFT, padx=2)
    
    def show_login_dialog(self):
        """显示登录对话框"""
        login_window = tk.Toplevel(self.root)
        login_window.title("🔑 用户登录")
        login_window.geometry("400x300")
        login_window.resizable(False, False)
        
        # 居中显示
        login_window.transient(self.root)
        login_window.grab_set()
        
        # 登录表单
        ttk.Label(login_window, text="🔑 用户登录", style='Title.TLabel').pack(pady=20)
        
        form_frame = ttk.Frame(login_window)
        form_frame.pack(padx=40, pady=20)
        
        ttk.Label(form_frame, text="📱 手机号:").grid(row=0, column=0, sticky=tk.W, pady=10)
        username_entry = ttk.Entry(form_frame, width=20, font=('Arial', 11))
        username_entry.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(form_frame, text="🔒 密码:").grid(row=1, column=0, sticky=tk.W, pady=10)
        password_entry = ttk.Entry(form_frame, width=20, font=('Arial', 11), show='*')
        password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # 登录按钮
        button_frame = ttk.Frame(login_window)
        button_frame.pack(pady=20)
        
        def do_login():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            
            if not username or not password:
                messagebox.showerror("输入错误", "请输入手机号和密码")
                return
            
            # 执行真实登录
            success = self.perform_real_login(username, password)
            if success:
                login_window.destroy()
            
        def do_cancel():
            login_window.destroy()
        
        ttk.Button(button_frame, text="🔑 登录", command=do_login, 
                  style='Success.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="❌ 取消", command=do_cancel, 
                  style='Warning.TButton').pack(side=tk.LEFT, padx=10)
        
        # 焦点设置
        username_entry.focus()
        
        # 回车登录
        login_window.bind('<Return>', lambda e: do_login())
    
    def perform_real_login(self, username: str, password: str) -> bool:
        """执行真实登录"""
        try:
            logging.info(f"🔑 开始登录: {username}")
            
            if REAL_COMPONENTS_AVAILABLE:
                # 创建真实API实例
                self.api_trader = JingTaoAPI()
                
                # 执行登录
                login_result = self.api_trader.login(username, password)
                
                if login_result and login_result.get('code') == '0':
                    self.current_user = username
                    self.user_password = password
                    self.is_logged_in = True
                    
                    # 更新界面状态
                    self.user_label.config(text=f"👤 用户: {username}")
                    self.login_button.config(state='disabled')
                    self.logout_button.config(state='normal')
                    self.quick_start_button.config(state='normal')
                    self.api_status_label.config(text="🟢 API已连接", style='Status.TLabel')
                    
                    # 更新实时数据状态
                    self.real_data["api_status"] = "connected"
                    
                    logging.info("✅ 登录成功")
                    messagebox.showinfo("登录成功", f"欢迎 {username}！")
                    
                    # 初始化混合引擎
                    if self.hybrid_engine:
                        self.hybrid_engine.initialize_api_trader(self.api_trader)
                    
                    # 刷新数据
                    self.refresh_all_real_data()
                    
                    return True
                else:
                    error_msg = login_result.get('message', '登录失败') if login_result else '网络连接失败'
                    logging.error(f"❌ 登录失败: {error_msg}")
                    messagebox.showerror("登录失败", error_msg)
                    return False
            else:
                # 模拟登录成功（用于测试）
                self.current_user = username
                self.is_logged_in = True
                self.user_label.config(text=f"👤 用户: {username}")
                self.login_button.config(state='disabled')
                self.logout_button.config(state='normal')
                self.quick_start_button.config(state='normal')
                
                logging.info("✅ 模拟登录成功")
                messagebox.showinfo("登录成功", f"模拟登录成功: {username}")
                return True
                
        except Exception as e:
            logging.error(f"❌ 登录异常: {e}")
            messagebox.showerror("登录异常", f"登录过程发生异常: {e}")
            return False
    
    def logout(self):
        """退出登录"""
        try:
            if self.is_monitoring:
                self.stop_real_monitoring()
            
            self.current_user = ""
            self.user_password = ""
            self.is_logged_in = False
            self.api_trader = None
            
            # 更新界面状态
            self.user_label.config(text="👤 用户: 未登录")
            self.login_button.config(state='normal')
            self.logout_button.config(state='disabled')
            self.quick_start_button.config(state='disabled')
            self.api_status_label.config(text="🔴 API未连接", style='Error.TLabel')
            
            # 更新实时数据状态
            self.real_data["api_status"] = "disconnected"
            
            logging.info("🚪 用户已退出登录")
            
        except Exception as e:
            logging.error(f"退出登录失败: {e}")

    def create_real_left_panel(self):
        """创建真实左侧控制面板"""
        left_frame = ttk.Frame(self.main_container)
        self.main_container.add(left_frame, weight=1)

        # 创建标签页
        self.left_notebook = ttk.Notebook(left_frame)
        self.left_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 交易控制页面
        self.create_real_trading_control_tab()

        # 参数设置页面
        self.create_real_parameter_tab()

        # 风险管理页面
        self.create_real_risk_tab()

    def create_real_trading_control_tab(self):
        """创建真实交易控制标签页"""
        tab_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(tab_frame, text="🎯 交易控制")

        # 交易模式选择
        mode_group = ttk.LabelFrame(tab_frame, text="🔄 交易模式")
        mode_group.pack(fill=tk.X, padx=5, pady=5)

        self.trading_mode_var = tk.StringVar(value="hybrid")

        ttk.Radiobutton(mode_group, text="🤖 纯API模式", variable=self.trading_mode_var,
                       value="api_only", command=self.on_mode_change).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(mode_group, text="👁️ 纯图像模式", variable=self.trading_mode_var,
                       value="image_only", command=self.on_mode_change).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(mode_group, text="🔗 混合模式", variable=self.trading_mode_var,
                       value="hybrid", command=self.on_mode_change).pack(anchor=tk.W, padx=10, pady=2)

        # 监控商品选择（真实商品）
        product_group = ttk.LabelFrame(tab_frame, text="📊 监控商品")
        product_group.pack(fill=tk.X, padx=5, pady=5)

        self.product_vars = {}
        # 使用真实的商品代码
        real_products = [
            ("511", "韩式陶瓷茶具"),
            ("507", "五福临门茶碗"),
            ("512", "寿桃陶瓷茶器")
        ]

        for code, name in real_products:
            var = tk.BooleanVar(value=True)
            self.product_vars[code] = var
            cb = ttk.Checkbutton(product_group, text=f"{code} - {name}",
                               variable=var, command=self.on_product_selection_change)
            cb.pack(anchor=tk.W, padx=10, pady=2)

        # 控制按钮
        control_group = ttk.LabelFrame(tab_frame, text="🎮 控制操作")
        control_group.pack(fill=tk.X, padx=5, pady=5)

        button_frame = ttk.Frame(control_group)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        self.start_button = ttk.Button(button_frame, text="🚀 启动监控",
                                      command=self.start_real_monitoring,
                                      style='Success.TButton', state='disabled')
        self.start_button.pack(fill=tk.X, pady=2)

        self.stop_button = ttk.Button(button_frame, text="⏹️ 停止监控",
                                     command=self.stop_real_monitoring,
                                     style='Warning.TButton', state='disabled')
        self.stop_button.pack(fill=tk.X, pady=2)

        # 测试按钮
        test_frame = ttk.Frame(button_frame)
        test_frame.pack(fill=tk.X, pady=5)

        self.api_test_button = ttk.Button(test_frame, text="🧪 API测试",
                                        command=self.test_real_api, state='disabled')
        self.api_test_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        self.image_test_button = ttk.Button(test_frame, text="📸 图像测试",
                                          command=self.test_real_image)
        self.image_test_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

    def create_real_parameter_tab(self):
        """创建真实参数设置标签页"""
        tab_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(tab_frame, text="⚙️ 参数设置")

        # 交易参数
        param_group = ttk.LabelFrame(tab_frame, text="💰 交易参数")
        param_group.pack(fill=tk.X, padx=5, pady=5)

        param_frame = ttk.Frame(param_group)
        param_frame.pack(fill=tk.X, padx=10, pady=5)

        # 止盈点数
        ttk.Label(param_frame, text="📈 止盈点数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.take_profit_var = tk.DoubleVar(value=self.config_data.get("trading", {}).get("take_profit_points", 3.0))
        take_profit_spin = ttk.Spinbox(param_frame, from_=0.5, to=20.0, increment=0.5,
                                      textvariable=self.take_profit_var, width=10,
                                      command=self.on_parameter_change)
        take_profit_spin.grid(row=0, column=1, padx=5, pady=2)

        # 止损点数
        ttk.Label(param_frame, text="📉 止损点数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.stop_loss_var = tk.DoubleVar(value=self.config_data.get("trading", {}).get("stop_loss_points", 2.0))
        stop_loss_spin = ttk.Spinbox(param_frame, from_=0.5, to=20.0, increment=0.5,
                                    textvariable=self.stop_loss_var, width=10,
                                    command=self.on_parameter_change)
        stop_loss_spin.grid(row=1, column=1, padx=5, pady=2)

        # 交易数量
        ttk.Label(param_frame, text="💰 交易数量:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.quantity_var = tk.IntVar(value=self.config_data.get("trading", {}).get("position_size", 1))
        quantity_spin = ttk.Spinbox(param_frame, from_=1, to=10, increment=1,
                                   textvariable=self.quantity_var, width=10,
                                   command=self.on_parameter_change)
        quantity_spin.grid(row=2, column=1, padx=5, pady=2)

        # 最大交易次数
        ttk.Label(param_frame, text="🔢 最大交易次数:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.max_trades_var = tk.IntVar(value=self.config_data.get("trading", {}).get("max_trades_per_day", 20))
        max_trades_spin = ttk.Spinbox(param_frame, from_=1, to=100, increment=1,
                                     textvariable=self.max_trades_var, width=10,
                                     command=self.on_parameter_change)
        max_trades_spin.grid(row=3, column=1, padx=5, pady=2)

        # 信号融合参数
        fusion_group = ttk.LabelFrame(tab_frame, text="🔗 信号融合")
        fusion_group.pack(fill=tk.X, padx=5, pady=5)

        fusion_frame = ttk.Frame(fusion_group)
        fusion_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(fusion_frame, text="🤖 API权重:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.api_weight_var = tk.DoubleVar(value=self.config_data.get("fusion", {}).get("api_weight", 0.6))
        api_weight_scale = ttk.Scale(fusion_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL,
                                    variable=self.api_weight_var, length=150,
                                    command=self.on_fusion_change)
        api_weight_scale.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(fusion_frame, text="👁️ 图像权重:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.image_weight_var = tk.DoubleVar(value=self.config_data.get("fusion", {}).get("image_weight", 0.4))
        image_weight_scale = ttk.Scale(fusion_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL,
                                      variable=self.image_weight_var, length=150,
                                      command=self.on_fusion_change)
        image_weight_scale.grid(row=1, column=1, padx=5, pady=2)

        # 保存参数按钮
        save_frame = ttk.Frame(tab_frame)
        save_frame.pack(fill=tk.X, padx=5, pady=10)

        ttk.Button(save_frame, text="💾 保存参数", command=self.save_real_parameters,
                  style='Success.TButton').pack(fill=tk.X)

    def create_real_risk_tab(self):
        """创建真实风险管理标签页"""
        tab_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(tab_frame, text="🛡️ 风险管理")

        # 资金管理
        money_group = ttk.LabelFrame(tab_frame, text="💰 资金管理")
        money_group.pack(fill=tk.X, padx=5, pady=5)

        money_frame = ttk.Frame(money_group)
        money_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(money_frame, text="日最大损失:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.daily_loss_limit_var = tk.DoubleVar(value=self.config_data.get("risk", {}).get("max_daily_loss", 500.0))
        ttk.Spinbox(money_frame, from_=100.0, to=2000.0, increment=50.0,
                   textvariable=self.daily_loss_limit_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Label(money_frame, text="元").grid(row=0, column=2, sticky=tk.W)

        ttk.Label(money_frame, text="连续亏损限制:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.max_consecutive_losses_var = tk.IntVar(value=self.config_data.get("risk", {}).get("max_consecutive_losses", 3))
        ttk.Spinbox(money_frame, from_=2, to=10, increment=1,
                   textvariable=self.max_consecutive_losses_var, width=10).grid(row=1, column=1, padx=5)

        # 风险控制开关
        self.enable_risk_control_var = tk.BooleanVar(value=self.config_data.get("risk", {}).get("enable_risk_control", True))
        ttk.Checkbutton(money_group, text="启用风险控制",
                       variable=self.enable_risk_control_var).pack(anchor=tk.W, padx=10, pady=2)

        # 紧急操作
        emergency_group = ttk.LabelFrame(tab_frame, text="🚨 紧急操作")
        emergency_group.pack(fill=tk.X, padx=5, pady=5)

        emergency_frame = ttk.Frame(emergency_group)
        emergency_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(emergency_frame, text="💰 查看真实持仓",
                  command=self.view_real_positions).pack(fill=tk.X, pady=2)
        ttk.Button(emergency_frame, text="🗑️ 撤销所有委托",
                  command=self.cancel_all_real_orders, style='Warning.TButton').pack(fill=tk.X, pady=2)
        ttk.Button(emergency_frame, text="💰 强制平仓",
                  command=self.force_close_all_real_positions, style='Danger.TButton').pack(fill=tk.X, pady=2)

    def create_real_center_panel(self):
        """创建真实中央监控面板"""
        center_frame = ttk.Frame(self.main_container)
        self.main_container.add(center_frame, weight=2)

        # 创建标签页
        self.center_notebook = ttk.Notebook(center_frame)
        self.center_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 实时监控页面
        self.create_real_monitor_tab()

        # 持仓管理页面
        self.create_real_positions_tab()

        # 委托管理页面
        self.create_real_orders_tab()

    def create_real_monitor_tab(self):
        """创建真实监控标签页"""
        tab_frame = ttk.Frame(self.center_notebook)
        self.center_notebook.add(tab_frame, text="📊 实时监控")

        # 系统状态
        status_group = ttk.LabelFrame(tab_frame, text="🔄 系统状态")
        status_group.pack(fill=tk.X, padx=5, pady=5)

        status_grid = ttk.Frame(status_group)
        status_grid.pack(fill=tk.X, padx=10, pady=10)

        # 状态显示
        ttk.Label(status_grid, text="系统状态:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.system_status_label = ttk.Label(status_grid, text="🔴 未启动", style='Error.TLabel')
        self.system_status_label.grid(row=0, column=1, sticky=tk.W, padx=10)

        ttk.Label(status_grid, text="交易模式:", font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky=tk.W, padx=5)
        self.mode_display_label = ttk.Label(status_grid, text="🔗 混合模式", style='Status.TLabel')
        self.mode_display_label.grid(row=0, column=3, sticky=tk.W, padx=10)

        # 今日统计（真实数据）
        stats_group = ttk.LabelFrame(tab_frame, text="📈 今日统计")
        stats_group.pack(fill=tk.X, padx=5, pady=5)

        stats_grid = ttk.Frame(stats_group)
        stats_grid.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(stats_grid, text="今日交易:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.today_trades_label = ttk.Label(stats_grid, text="0", style='Status.TLabel')
        self.today_trades_label.grid(row=0, column=1, sticky=tk.W, padx=10)

        ttk.Label(stats_grid, text="当前持仓:", font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky=tk.W, padx=5)
        self.current_positions_label = ttk.Label(stats_grid, text="0", style='Status.TLabel')
        self.current_positions_label.grid(row=0, column=3, sticky=tk.W, padx=10)

        ttk.Label(stats_grid, text="总盈亏:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.total_pnl_label = ttk.Label(stats_grid, text="0.00", style='Status.TLabel')
        self.total_pnl_label.grid(row=1, column=1, sticky=tk.W, padx=10)

        ttk.Label(stats_grid, text="委托单数:", font=('Arial', 10, 'bold')).grid(row=1, column=2, sticky=tk.W, padx=5)
        self.pending_orders_label = ttk.Label(stats_grid, text="0", style='Status.TLabel')
        self.pending_orders_label.grid(row=1, column=3, sticky=tk.W, padx=10)

        # 实时价格显示（真实数据）
        price_group = ttk.LabelFrame(tab_frame, text="💰 实时价格")
        price_group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        price_frame = ttk.Frame(price_group)
        price_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 价格表格
        columns = ("商品代码", "商品名称", "当前价格", "更新时间", "信号", "监控状态")
        self.real_price_tree = ttk.Treeview(price_frame, columns=columns, show='headings', height=8)

        for col in columns:
            self.real_price_tree.heading(col, text=col)
            self.real_price_tree.column(col, width=120, anchor=tk.CENTER)

        # 滚动条
        price_scrollbar = ttk.Scrollbar(price_frame, orient=tk.VERTICAL, command=self.real_price_tree.yview)
        self.real_price_tree.configure(yscrollcommand=price_scrollbar.set)

        self.real_price_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        price_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 价格控制按钮
        price_control_frame = ttk.Frame(tab_frame)
        price_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(price_control_frame, text="🔄 刷新价格",
                  command=self.refresh_real_prices).pack(side=tk.LEFT, padx=5)
        ttk.Button(price_control_frame, text="📊 获取K线",
                  command=self.get_real_kline_data).pack(side=tk.LEFT, padx=5)

    def create_real_positions_tab(self):
        """创建真实持仓管理标签页"""
        tab_frame = ttk.Frame(self.center_notebook)
        self.center_notebook.add(tab_frame, text="💼 持仓管理")

        # 持仓表格
        position_group = ttk.LabelFrame(tab_frame, text="📋 当前持仓")
        position_group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        position_frame = ttk.Frame(position_group)
        position_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 持仓表格列
        position_columns = ("持仓ID", "商品", "方向", "数量", "开仓价", "当前价", "盈亏点数", "盈亏金额")
        self.real_position_tree = ttk.Treeview(position_frame, columns=position_columns, show='headings', height=10)

        for col in position_columns:
            self.real_position_tree.heading(col, text=col)
            self.real_position_tree.column(col, width=100, anchor=tk.CENTER)

        # 持仓滚动条
        position_scrollbar = ttk.Scrollbar(position_frame, orient=tk.VERTICAL, command=self.real_position_tree.yview)
        self.real_position_tree.configure(yscrollcommand=position_scrollbar.set)

        self.real_position_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        position_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 持仓操作按钮
        position_control_frame = ttk.Frame(tab_frame)
        position_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(position_control_frame, text="🔄 刷新持仓",
                  command=self.refresh_real_positions).pack(side=tk.LEFT, padx=5)
        ttk.Button(position_control_frame, text="💰 平仓选中",
                  command=self.close_selected_position, style='Warning.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(position_control_frame, text="💰 全部平仓",
                  command=self.close_all_real_positions, style='Danger.TButton').pack(side=tk.LEFT, padx=5)

    def create_real_orders_tab(self):
        """创建真实委托管理标签页"""
        tab_frame = ttk.Frame(self.center_notebook)
        self.center_notebook.add(tab_frame, text="📋 委托管理")

        # 委托表格
        order_group = ttk.LabelFrame(tab_frame, text="📋 当前委托")
        order_group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        order_frame = ttk.Frame(order_group)
        order_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 委托表格列
        order_columns = ("委托ID", "商品", "方向", "数量", "委托价", "状态", "时间")
        self.real_order_tree = ttk.Treeview(order_frame, columns=order_columns, show='headings', height=10)

        for col in order_columns:
            self.real_order_tree.heading(col, text=col)
            self.real_order_tree.column(col, width=100, anchor=tk.CENTER)

        # 委托滚动条
        order_scrollbar = ttk.Scrollbar(order_frame, orient=tk.VERTICAL, command=self.real_order_tree.yview)
        self.real_order_tree.configure(yscrollcommand=order_scrollbar.set)

        self.real_order_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        order_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 委托操作按钮
        order_control_frame = ttk.Frame(tab_frame)
        order_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(order_control_frame, text="🔄 刷新委托",
                  command=self.refresh_real_orders).pack(side=tk.LEFT, padx=5)
        ttk.Button(order_control_frame, text="❌ 撤销选中",
                  command=self.cancel_selected_order, style='Warning.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(order_control_frame, text="🗑️ 撤销全部",
                  command=self.cancel_all_real_orders, style='Danger.TButton').pack(side=tk.LEFT, padx=5)

    def create_real_right_panel(self):
        """创建真实右侧日志面板"""
        right_frame = ttk.Frame(self.main_container)
        self.main_container.add(right_frame, weight=1)

        # 创建标签页
        self.right_notebook = ttk.Notebook(right_frame)
        self.right_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 系统日志
        self.create_real_system_log_tab()

        # 交易日志
        self.create_real_trading_log_tab()

        # 错误日志
        self.create_real_error_log_tab()

    def create_real_system_log_tab(self):
        """创建真实系统日志标签页"""
        tab_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(tab_frame, text="📝 系统日志")

        # 日志过滤器
        filter_frame = ttk.Frame(tab_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="级别:").pack(side=tk.LEFT, padx=5)
        self.log_level_filter_var = tk.StringVar(value="ALL")
        log_filter_combo = ttk.Combobox(filter_frame, textvariable=self.log_level_filter_var,
                                       values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR"], width=8)
        log_filter_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(filter_frame, text="🔍", command=self.filter_system_logs).pack(side=tk.LEFT, padx=5)

        # 系统日志文本框
        self.real_system_log_text = scrolledtext.ScrolledText(
            tab_frame, height=25, width=50, font=('Consolas', 9)
        )
        self.real_system_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 日志控制
        log_control_frame = ttk.Frame(tab_frame)
        log_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(log_control_frame, text="🧹 清空", command=self.clear_system_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_control_frame, text="💾 保存", command=self.save_system_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_control_frame, text="📊 分析", command=self.analyze_system_log).pack(side=tk.LEFT, padx=2)

    def create_real_trading_log_tab(self):
        """创建真实交易日志标签页"""
        tab_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(tab_frame, text="💰 交易日志")

        # 交易日志文本框
        self.real_trading_log_text = scrolledtext.ScrolledText(
            tab_frame, height=25, width=50, font=('Consolas', 9)
        )
        self.real_trading_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 交易日志控制
        trading_control_frame = ttk.Frame(tab_frame)
        trading_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(trading_control_frame, text="🧹 清空", command=self.clear_trading_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(trading_control_frame, text="💾 导出", command=self.export_trading_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(trading_control_frame, text="📊 统计", command=self.analyze_trading_performance).pack(side=tk.LEFT, padx=2)

    def create_real_error_log_tab(self):
        """创建真实错误日志标签页"""
        tab_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(tab_frame, text="❌ 错误日志")

        # 错误统计
        error_stats_frame = ttk.Frame(tab_frame)
        error_stats_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(error_stats_frame, text="今日错误:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.error_count_label = ttk.Label(error_stats_frame, text="0", style='Error.TLabel')
        self.error_count_label.pack(side=tk.LEFT, padx=5)

        # 错误日志文本框
        self.real_error_log_text = scrolledtext.ScrolledText(
            tab_frame, height=25, width=50, font=('Consolas', 9)
        )
        self.real_error_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 错误日志控制
        error_control_frame = ttk.Frame(tab_frame)
        error_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(error_control_frame, text="🧹 清空", command=self.clear_error_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(error_control_frame, text="📧 报告", command=self.report_errors).pack(side=tk.LEFT, padx=2)

    def create_real_status_bar(self):
        """创建真实状态栏"""
        self.status_frame = ttk.Frame(self.root)

        # 状态信息
        self.status_label = ttk.Label(self.status_frame, text="🔴 系统未启动", style='Error.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

        # 连接状态
        self.connection_status_label = ttk.Label(self.status_frame, text="⚪ 未连接", style='Status.TLabel')
        self.connection_status_label.pack(side=tk.LEFT, padx=10, pady=5)

        # 时间显示
        self.time_label = ttk.Label(self.status_frame, text="", style='Status.TLabel')
        self.time_label.pack(side=tk.RIGHT, padx=10, pady=5)

    def setup_layout(self):
        """设置布局"""
        self.toolbar_frame.pack(fill=tk.X, side=tk.TOP)
        self.main_container.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)

    def bind_events(self):
        """绑定事件"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind('<F5>', lambda e: self.refresh_all_real_data())
        self.real_position_tree.bind('<Double-1>', self.on_position_double_click)
        self.real_order_tree.bind('<Double-1>', self.on_order_double_click)

    # 真实交易功能方法
    def start_real_monitoring(self):
        """启动真实监控"""
        try:
            if not self.is_logged_in:
                messagebox.showerror("未登录", "请先登录后再启动监控")
                return

            if not self.is_monitoring:
                self.is_monitoring = True

                # 更新界面状态
                self.system_status_label.config(text="🟢 运行中", style='Status.TLabel')
                self.status_label.config(text="🟢 系统运行中")
                self.start_button.config(state='disabled')
                self.stop_button.config(state='normal')

                # 启动真实监控线程
                self.start_real_monitoring_thread()

                logging.info("🚀 启动真实交易监控")

        except Exception as e:
            logging.error(f"启动真实监控失败: {e}")
            messagebox.showerror("启动失败", f"启动监控失败: {e}")

    def stop_real_monitoring(self):
        """停止真实监控"""
        try:
            if self.is_monitoring:
                self.is_monitoring = False

                # 更新界面状态
                self.system_status_label.config(text="🔴 已停止", style='Error.TLabel')
                self.status_label.config(text="🔴 系统已停止")
                self.start_button.config(state='normal')
                self.stop_button.config(state='disabled')

                logging.info("⏹️ 停止真实交易监控")

        except Exception as e:
            logging.error(f"停止真实监控失败: {e}")

    def start_real_monitoring_thread(self):
        """启动真实监控线程"""
        def real_monitoring_loop():
            while self.is_monitoring:
                try:
                    # 执行真实监控周期
                    self.execute_real_monitoring_cycle()

                    # 等待下一个周期
                    time.sleep(2.0)  # 每2秒执行一次

                except Exception as e:
                    logging.error(f"真实监控循环错误: {e}")
                    time.sleep(5)  # 错误后等待5秒

        self.monitoring_thread = threading.Thread(target=real_monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def execute_real_monitoring_cycle(self):
        """执行真实监控周期"""
        try:
            if not self.is_logged_in or not self.api_trader:
                return

            # 获取选中的商品
            selected_products = [code for code, var in self.product_vars.items() if var.get()]

            if not selected_products:
                return

            # 刷新真实数据
            self.refresh_real_positions()
            self.refresh_real_orders()
            self.refresh_real_prices()

            # 根据交易模式执行监控
            trading_mode = self.trading_mode_var.get()

            for product_code in selected_products:
                if trading_mode == "api_only":
                    self.execute_real_api_monitoring(product_code)
                elif trading_mode == "image_only":
                    self.execute_real_image_monitoring(product_code)
                elif trading_mode == "hybrid":
                    self.execute_real_hybrid_monitoring(product_code)

        except Exception as e:
            logging.error(f"真实监控周期执行失败: {e}")

    def execute_real_api_monitoring(self, product_code: str):
        """执行真实API监控"""
        try:
            if not self.api_trader:
                return

            # 获取K线数据进行信号分析
            kline_data = self.api_trader.get_kline_data(product_code, period=1, count=10)

            if kline_data and kline_data.get('code') == '0':
                # 分析K线信号
                signal = self.analyze_kline_signal(kline_data.get('data', []))

                if signal and signal != 'hold':
                    logging.info(f"🎯 API信号检测: 商品{product_code} 信号:{signal}")

                    # 执行交易
                    self.execute_real_trade(product_code, signal, "API信号")

        except Exception as e:
            logging.error(f"API监控失败: {e}")

    def execute_real_hybrid_monitoring(self, product_code: str):
        """执行真实混合监控"""
        try:
            if not self.hybrid_engine:
                return

            # 使用混合引擎获取融合信号
            signal = self.hybrid_engine.get_trading_signal(product_code)

            if signal and signal.action != 'hold':
                logging.info(f"🔗 混合信号检测: 商品{product_code} 信号:{signal.action} 置信度:{signal.confidence}")

                # 执行交易
                self.execute_real_trade(product_code, signal.action, f"混合信号(置信度:{signal.confidence:.2f})")

        except Exception as e:
            logging.error(f"混合监控失败: {e}")

    def execute_real_trade(self, product_code: str, signal: str, reason: str):
        """执行真实交易"""
        try:
            if not self.api_trader:
                logging.error("❌ API交易器不可用")
                return

            # 获取当前价格
            current_price = self.get_real_current_price(product_code)
            if not current_price:
                logging.error(f"❌ 无法获取商品{product_code}的当前价格")
                return

            # 计算交易价格（添加滑点）
            if signal == 'buy_up':
                trade_price = current_price + 0.5  # 买涨加0.5点
                bs_flag = "B"
                direction_text = "买涨"
            elif signal == 'buy_down':
                trade_price = current_price - 0.5  # 买跌减0.5点
                bs_flag = "S"
                direction_text = "买跌"
            else:
                return

            quantity = self.quantity_var.get()

            logging.info(f"📋 开始下单: 商品{product_code} {direction_text} 价格{trade_price} 数量{quantity} - {reason}")

            # 执行真实下单
            order_result = self.api_trader.place_order(product_code, trade_price, quantity, bs_flag)

            if order_result and order_result.get('code') == '0':
                logging.info(f"✅ 下单成功: 商品{product_code} {direction_text} 价格{trade_price}")

                # 更新统计
                self.real_data["trades_today"] += 1
                self.update_real_stats_display()

            else:
                error_msg = order_result.get('message', '未知错误') if order_result else '网络错误'
                logging.error(f"❌ 下单失败: 商品{product_code} {direction_text} - {error_msg}")

        except Exception as e:
            logging.error(f"执行真实交易失败: {e}")

    # 真实数据获取方法
    def refresh_real_positions(self):
        """刷新真实持仓"""
        try:
            if not self.api_trader:
                return

            # 获取真实持仓数据
            positions_result = self.api_trader.get_current_positions()

            if positions_result and positions_result.get('code') == '0':
                positions = positions_result.get('data', [])
                self.real_data["positions"] = positions

                # 更新持仓表格
                self.update_positions_display(positions)

                # 更新统计
                self.current_positions_label.config(text=str(len(positions)))

                logging.info(f"🔄 刷新持仓: 当前{len(positions)}个持仓")
            else:
                logging.warning("⚠️ 获取持仓数据失败")

        except Exception as e:
            logging.error(f"刷新真实持仓失败: {e}")

    def refresh_real_orders(self):
        """刷新真实委托"""
        try:
            if not self.api_trader:
                return

            # 获取真实委托数据
            orders_result = self.api_trader.get_current_orders()

            if orders_result and orders_result.get('code') == '0':
                orders = orders_result.get('data', [])
                self.real_data["orders"] = orders

                # 更新委托表格
                self.update_orders_display(orders)

                # 更新统计
                self.pending_orders_label.config(text=str(len(orders)))

                logging.info(f"🔄 刷新委托: 当前{len(orders)}个委托")
            else:
                logging.warning("⚠️ 获取委托数据失败")

        except Exception as e:
            logging.error(f"刷新真实委托失败: {e}")

    def refresh_real_prices(self):
        """刷新真实价格"""
        try:
            if not self.api_trader:
                return

            # 获取选中商品的实时价格
            selected_products = [code for code, var in self.product_vars.items() if var.get()]

            for product_code in selected_products:
                try:
                    # 获取K线数据获取最新价格
                    kline_result = self.api_trader.get_kline_data(product_code, period=1, count=1)

                    if kline_result and kline_result.get('code') == '0':
                        kline_data = kline_result.get('data', [])
                        if kline_data:
                            latest_kline = kline_data[0]
                            current_price = float(latest_kline.get('close', 0))

                            if current_price > 0:
                                self.real_data["current_prices"][product_code] = current_price

                except Exception as e:
                    logging.error(f"获取商品{product_code}价格失败: {e}")

            # 更新价格显示
            self.update_prices_display()

        except Exception as e:
            logging.error(f"刷新真实价格失败: {e}")

    def get_real_current_price(self, product_code: str) -> Optional[float]:
        """获取真实当前价格"""
        try:
            if not self.api_trader:
                return None

            # 从K线数据获取最新价格
            kline_result = self.api_trader.get_kline_data(product_code, period=1, count=1)

            if kline_result and kline_result.get('code') == '0':
                kline_data = kline_result.get('data', [])
                if kline_data:
                    latest_kline = kline_data[0]
                    current_price = float(latest_kline.get('close', 0))
                    return current_price if current_price > 0 else None

            return None

        except Exception as e:
            logging.error(f"获取真实价格失败: {e}")
            return None

    def analyze_kline_signal(self, kline_data: List) -> str:
        """分析K线信号"""
        try:
            if len(kline_data) < 2:
                return 'hold'

            # 简单的信号分析：比较最近两根K线
            current_kline = kline_data[0]
            previous_kline = kline_data[1]

            current_close = float(current_kline.get('close', 0))
            previous_close = float(previous_kline.get('close', 0))

            if current_close > previous_close:
                return 'buy_up'
            elif current_close < previous_close:
                return 'buy_down'
            else:
                return 'hold'

        except Exception as e:
            logging.error(f"分析K线信号失败: {e}")
            return 'hold'

    # 界面更新方法
    def update_positions_display(self, positions: List):
        """更新持仓显示"""
        try:
            # 清空现有数据
            for item in self.real_position_tree.get_children():
                self.real_position_tree.delete(item)

            # 添加真实持仓数据
            for position in positions:
                hold_id = position.get('holdDetailId', '')
                commodity_name = position.get('commodityName', '')
                direction = "多头" if position.get('direction') == 'long' else "空头"
                quantity = position.get('quantity', 0)
                avg_price = float(position.get('avgPrice', 0))

                # 获取当前价格计算盈亏
                commodity_id = position.get('commodityId', '')
                current_price = self.real_data["current_prices"].get(commodity_id, avg_price)

                # 计算盈亏
                if position.get('direction') == 'long':
                    profit_points = current_price - avg_price
                else:
                    profit_points = avg_price - current_price

                profit_amount = profit_points * quantity * 10  # 假设每点10元

                self.real_position_tree.insert("", tk.END, values=(
                    hold_id[:8] + "...",  # 截断显示ID
                    commodity_name,
                    direction,
                    quantity,
                    f"{avg_price:.2f}",
                    f"{current_price:.2f}",
                    f"{profit_points:+.2f}",
                    f"{profit_amount:+.2f}"
                ))

        except Exception as e:
            logging.error(f"更新持仓显示失败: {e}")

    def update_orders_display(self, orders: List):
        """更新委托显示"""
        try:
            # 清空现有数据
            for item in self.real_order_tree.get_children():
                self.real_order_tree.delete(item)

            # 添加真实委托数据
            for order in orders:
                order_id = order.get('orderId', '')
                commodity_name = order.get('commodityName', '')
                direction = "买入" if order.get('bsFlag') == 'B' else "卖出"
                quantity = order.get('quantity', 0)
                price = float(order.get('price', 0))
                status = order.get('status', '')
                create_time = order.get('createTime', '')

                self.real_order_tree.insert("", tk.END, values=(
                    order_id[:8] + "...",  # 截断显示ID
                    commodity_name,
                    direction,
                    quantity,
                    f"{price:.2f}",
                    status,
                    create_time[:19] if create_time else ""  # 只显示日期时间部分
                ))

        except Exception as e:
            logging.error(f"更新委托显示失败: {e}")

    def update_prices_display(self):
        """更新价格显示"""
        try:
            # 清空现有数据
            for item in self.real_price_tree.get_children():
                self.real_price_tree.delete(item)

            # 添加真实价格数据
            product_names = {"511": "韩式陶瓷茶具", "507": "五福临门茶碗", "512": "寿桃陶瓷茶器"}

            for product_code, var in self.product_vars.items():
                if var.get():  # 只显示选中的商品
                    product_name = product_names.get(product_code, f"商品{product_code}")
                    current_price = self.real_data["current_prices"].get(product_code, 0.0)
                    update_time = datetime.now().strftime("%H:%M:%S")
                    signal = "🟡 观望"  # 默认信号
                    status = "监控中" if self.is_monitoring else "待启动"

                    self.real_price_tree.insert("", tk.END, values=(
                        product_code,
                        product_name,
                        f"{current_price:.2f}" if current_price > 0 else "获取中...",
                        update_time,
                        signal,
                        status
                    ))

        except Exception as e:
            logging.error(f"更新价格显示失败: {e}")

    def update_real_stats_display(self):
        """更新真实统计显示"""
        try:
            self.today_trades_label.config(text=str(self.real_data["trades_today"]))
            self.current_positions_label.config(text=str(len(self.real_data["positions"])))
            self.pending_orders_label.config(text=str(len(self.real_data["orders"])))
            self.total_pnl_label.config(text=f"{self.real_data['total_pnl']:+.2f}")

        except Exception as e:
            logging.error(f"更新统计显示失败: {e}")

    # 真实操作方法
    def test_real_api(self):
        """测试真实API"""
        try:
            if not self.api_trader:
                messagebox.showerror("API未连接", "请先登录")
                return

            logging.info("🧪 开始API连接测试...")

            # 测试获取商品信息
            commodity_result = self.api_trader.get_commodity_strategy()

            if commodity_result and commodity_result.get('code') == '0':
                commodities = commodity_result.get('data', [])
                logging.info(f"✅ API测试成功: 获取到{len(commodities)}个商品")
                messagebox.showinfo("测试成功", f"API连接正常！\n获取到{len(commodities)}个商品信息")
            else:
                error_msg = commodity_result.get('message', '未知错误') if commodity_result else '网络错误'
                logging.error(f"❌ API测试失败: {error_msg}")
                messagebox.showerror("测试失败", f"API测试失败: {error_msg}")

        except Exception as e:
            logging.error(f"API测试异常: {e}")
            messagebox.showerror("测试异常", f"API测试异常: {e}")

    def test_real_image(self):
        """测试真实图像识别"""
        try:
            logging.info("📸 开始图像识别测试...")

            if REAL_COMPONENTS_AVAILABLE and self.hybrid_engine:
                # 使用真实的图像检测
                import pyautogui
                screenshot = pyautogui.screenshot()

                # 执行图像检测
                result = self.hybrid_engine.get_image_signal(screenshot)

                if result:
                    action = result.get('action', 'hold')
                    confidence = result.get('confidence', 0.0)

                    logging.info(f"✅ 图像测试成功: 信号={action}, 置信度={confidence:.2f}")
                    messagebox.showinfo("测试成功", f"图像识别正常！\n信号: {action}\n置信度: {confidence:.2f}")
                else:
                    logging.warning("⚠️ 图像识别无结果")
                    messagebox.showwarning("测试结果", "图像识别无明确信号")
            else:
                logging.info("📸 图像识别功能不可用，使用模拟测试")
                messagebox.showinfo("测试结果", "图像识别功能不可用（缺少依赖组件）")

        except Exception as e:
            logging.error(f"图像测试异常: {e}")
            messagebox.showerror("测试异常", f"图像测试异常: {e}")

    def force_close_all_real_positions(self):
        """强制平仓所有真实持仓"""
        try:
            if not self.api_trader:
                messagebox.showerror("API未连接", "请先登录")
                return

            positions = self.real_data.get("positions", [])
            if not positions:
                messagebox.showinfo("无持仓", "当前没有持仓需要平仓")
                return

            result = messagebox.askyesno("确认平仓", f"确定要平仓所有{len(positions)}个持仓吗？")
            if not result:
                return

            logging.info(f"💰 开始强制平仓{len(positions)}个持仓")

            success_count = 0
            for position in positions:
                try:
                    hold_id = position.get('holdDetailId')
                    quantity = position.get('quantity')
                    current_price = self.get_real_current_price(position.get('commodityId'))

                    if current_price:
                        # 执行平仓
                        close_result = self.api_trader.transfer_position(
                            hold_id, str(current_price), str(quantity)
                        )

                        if close_result and close_result.get('code') == '0':
                            success_count += 1
                            logging.info(f"✅ 平仓成功: {position.get('commodityName')} 价格{current_price}")
                        else:
                            error_msg = close_result.get('message', '未知错误') if close_result else '网络错误'
                            logging.error(f"❌ 平仓失败: {position.get('commodityName')} - {error_msg}")

                except Exception as e:
                    logging.error(f"平仓持仓失败: {e}")

            logging.info(f"💰 强制平仓完成: 成功{success_count}/{len(positions)}")
            messagebox.showinfo("平仓完成", f"强制平仓完成！\n成功: {success_count}/{len(positions)}")

            # 刷新持仓数据
            self.refresh_real_positions()

        except Exception as e:
            logging.error(f"强制平仓失败: {e}")
            messagebox.showerror("平仓失败", f"强制平仓失败: {e}")

    def cancel_all_real_orders(self):
        """撤销所有真实委托"""
        try:
            if not self.api_trader:
                messagebox.showerror("API未连接", "请先登录")
                return

            orders = self.real_data.get("orders", [])
            if not orders:
                messagebox.showinfo("无委托", "当前没有委托需要撤销")
                return

            result = messagebox.askyesno("确认撤单", f"确定要撤销所有{len(orders)}个委托吗？")
            if not result:
                return

            logging.info(f"🗑️ 开始撤销{len(orders)}个委托")

            # 执行撤销所有委托
            cancel_result = self.api_trader.cancel_all_orders()

            if cancel_result and cancel_result.get('code') == '0':
                logging.info("✅ 撤销所有委托成功")
                messagebox.showinfo("撤单成功", "所有委托已成功撤销！")
            else:
                error_msg = cancel_result.get('message', '未知错误') if cancel_result else '网络错误'
                logging.error(f"❌ 撤销委托失败: {error_msg}")
                messagebox.showerror("撤单失败", f"撤销委托失败: {error_msg}")

            # 刷新委托数据
            self.refresh_real_orders()

        except Exception as e:
            logging.error(f"撤销委托失败: {e}")
            messagebox.showerror("撤单失败", f"撤销委托失败: {e}")

    # 日志管理方法
    def add_system_log(self, message: str):
        """添加系统日志"""
        try:
            self.real_system_log_text.insert(tk.END, message + "\n")
            self.real_system_log_text.see(tk.END)
        except Exception:
            pass

    def add_trading_log(self, message: str):
        """添加交易日志"""
        try:
            self.real_trading_log_text.insert(tk.END, message + "\n")
            self.real_trading_log_text.see(tk.END)
        except Exception:
            pass

    def add_error_log(self, message: str):
        """添加错误日志"""
        try:
            self.real_error_log_text.insert(tk.END, message + "\n")
            self.real_error_log_text.see(tk.END)

            # 更新错误计数
            current_count = int(self.error_count_label.cget("text"))
            self.error_count_label.config(text=str(current_count + 1))
        except Exception:
            pass

    def clear_system_log(self):
        """清空系统日志"""
        self.real_system_log_text.delete(1.0, tk.END)
        logging.info("🧹 系统日志已清空")

    def clear_trading_log(self):
        """清空交易日志"""
        self.real_trading_log_text.delete(1.0, tk.END)
        logging.info("🧹 交易日志已清空")

    def clear_error_log(self):
        """清空错误日志"""
        self.real_error_log_text.delete(1.0, tk.END)
        self.error_count_label.config(text="0")
        logging.info("🧹 错误日志已清空")

    # 事件处理方法
    def on_mode_change(self):
        """交易模式变更事件"""
        mode = self.trading_mode_var.get()
        mode_text = {"api_only": "🤖 纯API模式", "image_only": "👁️ 纯图像模式", "hybrid": "🔗 混合模式"}
        self.mode_display_label.config(text=mode_text.get(mode, mode))
        logging.info(f"🔄 交易模式切换为: {mode_text.get(mode, mode)}")

    def on_product_selection_change(self):
        """商品选择变更事件"""
        selected = [code for code, var in self.product_vars.items() if var.get()]
        logging.info(f"📊 监控商品更新: {selected}")
        self.update_prices_display()

    def on_parameter_change(self):
        """参数变更事件"""
        logging.info("⚙️ 交易参数已更新")

    def on_fusion_change(self, value):
        """信号融合参数变更事件"""
        api_weight = self.api_weight_var.get()
        image_weight = self.image_weight_var.get()

        # 自动调整权重使其总和为1
        total = api_weight + image_weight
        if total > 0:
            self.api_weight_var.set(api_weight / total)
            self.image_weight_var.set(image_weight / total)

        logging.info(f"🔗 信号权重更新: API={api_weight:.2f}, 图像={image_weight:.2f}")

    def start_real_updates(self):
        """启动真实数据更新"""
        def update_real_data():
            try:
                # 更新时间显示
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.time_label.config(text=f"🕐 {current_time}")

                # 如果已登录，定期刷新数据
                if self.is_logged_in and not self.is_monitoring:
                    # 非监控状态下，每30秒刷新一次数据
                    if int(time.time()) % 30 == 0:
                        self.refresh_all_real_data()

                # 调度下次更新
                self.root.after(1000, update_real_data)

            except Exception as e:
                logging.error(f"真实数据更新失败: {e}")

        update_real_data()

    def refresh_all_real_data(self):
        """刷新所有真实数据"""
        try:
            if self.is_logged_in:
                logging.info("🔄 刷新所有真实数据")
                self.refresh_real_positions()
                self.refresh_real_orders()
                self.refresh_real_prices()
                self.update_real_stats_display()
        except Exception as e:
            logging.error(f"刷新所有数据失败: {e}")

    def save_real_parameters(self):
        """保存真实参数"""
        try:
            # 更新配置
            self.config_data["trading"]["take_profit_points"] = self.take_profit_var.get()
            self.config_data["trading"]["stop_loss_points"] = self.stop_loss_var.get()
            self.config_data["trading"]["position_size"] = self.quantity_var.get()
            self.config_data["trading"]["max_trades_per_day"] = self.max_trades_var.get()
            self.config_data["fusion"]["api_weight"] = self.api_weight_var.get()
            self.config_data["fusion"]["image_weight"] = self.image_weight_var.get()

            # 保存配置
            self.save_config(self.config_data)

            logging.info("💾 真实参数已保存")
            messagebox.showinfo("保存成功", "所有参数已保存！")

        except Exception as e:
            logging.error(f"保存真实参数失败: {e}")
            messagebox.showerror("保存失败", f"保存参数失败: {e}")

    def on_closing(self):
        """窗口关闭事件"""
        try:
            if self.is_monitoring:
                result = messagebox.askyesno("确认退出", "系统正在监控中，确定要退出吗？")
                if not result:
                    return

                self.stop_real_monitoring()

            self.root.quit()
            self.root.destroy()

        except Exception as e:
            logging.error(f"关闭窗口失败: {e}")

    # 占位符方法（待完善）
    def quick_start_real_trading(self): pass
    def emergency_stop_real_trading(self): pass
    def relogin(self): pass
    def reconnect_api(self): pass
    def view_real_positions(self): pass
    def close_selected_position(self): pass
    def close_all_real_positions(self): pass
    def cancel_selected_order(self): pass
    def get_real_kline_data(self): pass
    def filter_system_logs(self): pass
    def save_system_log(self): pass
    def analyze_system_log(self): pass
    def export_trading_log(self): pass
    def analyze_trading_performance(self): pass
    def report_errors(self): pass
    def on_position_double_click(self, event): pass
    def on_order_double_click(self, event): pass
    def execute_real_image_monitoring(self, product_code): pass
    def export_real_trades(self): pass
    def generate_trading_report(self): pass

    def run(self):
        """运行真实主窗口"""
        try:
            # 绑定关闭事件
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            # 运行主循环
            self.root.mainloop()

        except Exception as e:
            logging.error(f"运行主窗口失败: {e}")
            messagebox.showerror("运行错误", f"主窗口运行失败: {e}")

def main():
    """启动真实高级界面"""
    print("🚀 启动智能量化交易系统真实高级版...")
    app = RealAdvancedWindow()
    print("🎯 真实高级界面启动成功！")
    app.run()

if __name__ == "__main__":
    main()
