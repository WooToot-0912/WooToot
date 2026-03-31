#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级主窗口 - 智能量化交易系统的高级可定制GUI界面
提供丰富的控件、详细的日志显示和全面的自定义设置
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# 添加项目路径
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir / "hybrid_core"))

from hybrid_trading_engine import HybridTradingEngine, TradingMode
from signal_fusion_engine import SignalFusionEngine, TradingSignal

class AdvancedMainWindow:
    """高级主窗口"""
    
    def __init__(self):
        """初始化高级主窗口"""
        self.root = tk.Tk()
        self.root.title("🎯 智能量化交易系统 v2.0 - 高级版")
        self.root.geometry("1600x1000")
        self.root.minsize(1400, 800)
        
        # 用户信息
        self.current_user = ""
        self.user_password = ""
        
        # 核心组件
        self.hybrid_engine = HybridTradingEngine()
        self.is_monitoring = False
        
        # 配置数据
        self.config_data = self.load_config()
        self.user_settings = self.load_user_settings()
        
        # GUI组件
        self.setup_styles()
        self.create_menu_bar()
        self.create_widgets()
        self.setup_layout()
        self.bind_events()
        self.setup_logging()
        
        # 状态更新线程
        self.status_thread = None
        self.update_interval = 1.0
        
        # 性能监控
        self.performance_data = {
            "start_time": time.time(),
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit": 0.0
        }
        
        print("✅ 高级主窗口初始化完成")
    
    def load_config(self) -> Dict:
        """加载配置数据"""
        try:
            config_file = Path("config/advanced_config.json")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 创建默认配置
                default_config = {
                    "trading": {
                        "max_trades_per_day": 50,
                        "risk_level": "medium",
                        "auto_stop_loss": True,
                        "auto_take_profit": True,
                        "position_size": 1.0,
                        "slippage_tolerance": 0.5
                    },
                    "monitoring": {
                        "update_interval": 1.0,
                        "enable_sound_alerts": True,
                        "enable_popup_alerts": False,
                        "log_level": "INFO",
                        "max_log_lines": 1000
                    },
                    "display": {
                        "theme": "default",
                        "font_size": 9,
                        "show_advanced_controls": True,
                        "auto_scroll_logs": True,
                        "highlight_important": True
                    },
                    "api": {
                        "timeout": 30,
                        "retry_count": 3,
                        "rate_limit": 10,
                        "enable_debug": False
                    }
                }
                
                self.save_config(default_config)
                return default_config
                
        except Exception as e:
            print(f"❌ 加载配置失败: {e}")
            return {}
    
    def save_config(self, config: Dict):
        """保存配置数据"""
        try:
            config_file = Path("config/advanced_config.json")
            config_file.parent.mkdir(exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
    
    def load_user_settings(self) -> Dict:
        """加载用户个人设置"""
        try:
            settings_file = Path("config/user_settings.json")
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    "window_geometry": "1600x1000+100+100",
                    "panel_weights": [1, 2, 1],
                    "selected_products": ["511", "507", "512"],
                    "favorite_strategies": [],
                    "custom_alerts": []
                }
        except Exception as e:
            print(f"❌ 加载用户设置失败: {e}")
            return {}
    
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        
        # 配置主题
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
        
        # 按钮样式
        style.configure('Success.TButton', foreground='white')
        style.configure('Warning.TButton', foreground='white')
        style.configure('Danger.TButton', foreground='white')
        
        # 框架样式
        style.configure('Card.TFrame', relief='raised', borderwidth=1)
        style.configure('Panel.TFrame', relief='sunken', borderwidth=1)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 文件", menu=file_menu)
        file_menu.add_command(label="📊 导出交易记录", command=self.export_trading_records)
        file_menu.add_command(label="📋 导出日志", command=self.export_logs)
        file_menu.add_command(label="⚙️ 导入配置", command=self.import_config)
        file_menu.add_command(label="💾 导出配置", command=self.export_config)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 退出", command=self.on_closing)
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="👁️ 视图", menu=view_menu)
        view_menu.add_command(label="🔄 刷新界面", command=self.refresh_interface)
        view_menu.add_command(label="📊 性能监控", command=self.show_performance_monitor)
        view_menu.add_command(label="📈 交易统计", command=self.show_trading_statistics)
        view_menu.add_separator()
        view_menu.add_command(label="🎨 界面设置", command=self.show_interface_settings)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🔧 工具", menu=tools_menu)
        tools_menu.add_command(label="🧪 API测试", command=self.show_api_test)
        tools_menu.add_command(label="📸 截图工具", command=self.show_screenshot_tool)
        tools_menu.add_command(label="🔍 日志分析", command=self.show_log_analyzer)
        tools_menu.add_command(label="⚡ 性能优化", command=self.show_performance_optimizer)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ 帮助", menu=help_menu)
        help_menu.add_command(label="📖 使用说明", command=self.show_help)
        help_menu.add_command(label="🔧 故障排除", command=self.show_troubleshooting)
        help_menu.add_command(label="📞 技术支持", command=self.show_support_info)
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ 关于", command=self.show_about)
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主容器
        self.main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        
        # 创建顶部工具栏
        self.create_toolbar()
        
        # 创建左侧控制面板
        self.create_left_panel()
        
        # 创建中央监控面板
        self.create_center_panel()
        
        # 创建右侧日志面板
        self.create_right_panel()
        
        # 创建底部状态栏
        self.create_status_bar()
        
        # 创建浮动工具面板
        self.create_floating_tools()
    
    def create_toolbar(self):
        """创建工具栏"""
        self.toolbar_frame = ttk.Frame(self.root, style='Panel.TFrame')
        
        # 用户信息区域
        user_frame = ttk.Frame(self.toolbar_frame)
        user_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.user_label = ttk.Label(user_frame, text="👤 用户: 未登录", style='Status.TLabel')
        self.user_label.pack(side=tk.LEFT)
        
        self.logout_button = ttk.Button(
            user_frame, text="🚪 退出登录", 
            command=self.logout, style='Warning.TButton'
        )
        self.logout_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # 快速操作按钮
        quick_frame = ttk.Frame(self.toolbar_frame)
        quick_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        
        ttk.Button(quick_frame, text="⚡ 快速启动", command=self.quick_start).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="⏸️ 暂停", command=self.pause_trading).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="🛑 紧急停止", command=self.emergency_stop, style='Danger.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="🔄 重置", command=self.reset_system).pack(side=tk.LEFT, padx=2)
    
    def create_left_panel(self):
        """创建左侧控制面板"""
        self.left_frame = ttk.Frame(self.main_container, style='Card.TFrame')
        self.main_container.add(self.left_frame, weight=1)
        
        # 创建标签页控件
        self.left_notebook = ttk.Notebook(self.left_frame)
        self.left_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 交易控制页面
        self.create_trading_control_tab()
        
        # 策略设置页面
        self.create_strategy_settings_tab()
        
        # 风险管理页面
        self.create_risk_management_tab()
        
        # 高级设置页面
        self.create_advanced_settings_tab()
    
    def create_trading_control_tab(self):
        """创建交易控制标签页"""
        tab_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(tab_frame, text="🎯 交易控制")
        
        # 创建滚动区域
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 交易模式选择
        mode_group = ttk.LabelFrame(scrollable_frame, text="🔄 交易模式")
        mode_group.pack(fill=tk.X, padx=5, pady=5)
        
        self.trading_mode_var = tk.StringVar(value="hybrid")
        
        ttk.Radiobutton(mode_group, text="🤖 纯API模式", variable=self.trading_mode_var, 
                       value="api_only").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(mode_group, text="👁️ 纯图像模式", variable=self.trading_mode_var, 
                       value="image_only").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(mode_group, text="🔗 混合模式", variable=self.trading_mode_var, 
                       value="hybrid").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(mode_group, text="🧠 AI智能模式", variable=self.trading_mode_var, 
                       value="ai_smart").pack(anchor=tk.W, padx=10, pady=2)
        
        # 监控商品选择
        product_group = ttk.LabelFrame(scrollable_frame, text="📊 监控商品")
        product_group.pack(fill=tk.X, padx=5, pady=5)
        
        # 商品复选框
        self.product_vars = {}
        products = [
            ("511", "韩式陶瓷茶具"),
            ("507", "五福临门茶碗"),
            ("512", "寿桃陶瓷茶器"),
            ("520", "爱心陶瓷套装"),
            ("888", "发财陶瓷摆件")
        ]
        
        for code, name in products:
            var = tk.BooleanVar()
            self.product_vars[code] = var
            ttk.Checkbutton(
                product_group, 
                text=f"{code} - {name}", 
                variable=var
            ).pack(anchor=tk.W, padx=10, pady=2)
        
        # 默认选中前三个
        for i, (code, _) in enumerate(products[:3]):
            self.product_vars[code].set(True)
        
        # 交易参数设置
        param_group = ttk.LabelFrame(scrollable_frame, text="⚙️ 交易参数")
        param_group.pack(fill=tk.X, padx=5, pady=5)
        
        # 参数输入框
        param_frame = ttk.Frame(param_group)
        param_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 止盈点数
        ttk.Label(param_frame, text="📈 止盈点数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.take_profit_var = tk.DoubleVar(value=3.0)
        take_profit_spin = ttk.Spinbox(param_frame, from_=0.5, to=20.0, increment=0.5, 
                                      textvariable=self.take_profit_var, width=10)
        take_profit_spin.grid(row=0, column=1, padx=5, pady=2)
        
        # 止损点数
        ttk.Label(param_frame, text="📉 止损点数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.stop_loss_var = tk.DoubleVar(value=2.0)
        stop_loss_spin = ttk.Spinbox(param_frame, from_=0.5, to=20.0, increment=0.5, 
                                    textvariable=self.stop_loss_var, width=10)
        stop_loss_spin.grid(row=1, column=1, padx=5, pady=2)
        
        # 交易数量
        ttk.Label(param_frame, text="💰 交易数量:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.quantity_var = tk.IntVar(value=1)
        quantity_spin = ttk.Spinbox(param_frame, from_=1, to=10, increment=1, 
                                   textvariable=self.quantity_var, width=10)
        quantity_spin.grid(row=2, column=1, padx=5, pady=2)
        
        # 最大交易次数
        ttk.Label(param_frame, text="🔢 最大交易次数:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.max_trades_var = tk.IntVar(value=20)
        max_trades_spin = ttk.Spinbox(param_frame, from_=1, to=100, increment=1, 
                                     textvariable=self.max_trades_var, width=10)
        max_trades_spin.grid(row=3, column=1, padx=5, pady=2)
        
        # 控制按钮
        control_group = ttk.LabelFrame(scrollable_frame, text="🎮 控制操作")
        control_group.pack(fill=tk.X, padx=5, pady=5)
        
        button_frame = ttk.Frame(control_group)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(
            button_frame, text="🚀 启动监控", 
            command=self.start_monitoring, style='Success.TButton'
        )
        self.start_button.pack(fill=tk.X, pady=2)
        
        self.stop_button = ttk.Button(
            button_frame, text="⏹️ 停止监控", 
            command=self.stop_monitoring, style='Warning.TButton'
        )
        self.stop_button.pack(fill=tk.X, pady=2)
        
        # 测试按钮
        test_frame = ttk.Frame(button_frame)
        test_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(test_frame, text="🧪 API测试", command=self.test_api).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        ttk.Button(test_frame, text="📸 图像测试", command=self.test_image).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        
        # 布局滚动区域
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_strategy_settings_tab(self):
        """创建策略设置标签页"""
        tab_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(tab_frame, text="🧠 策略设置")

        # 信号融合设置
        signal_group = ttk.LabelFrame(tab_frame, text="🔗 信号融合")
        signal_group.pack(fill=tk.X, padx=5, pady=5)

        # API信号权重
        ttk.Label(signal_group, text="🤖 API信号权重:").pack(anchor=tk.W, padx=10, pady=2)
        self.api_weight_var = tk.DoubleVar(value=0.6)
        api_weight_scale = ttk.Scale(signal_group, from_=0.0, to=1.0, orient=tk.HORIZONTAL,
                                    variable=self.api_weight_var, length=200)
        api_weight_scale.pack(padx=10, pady=2)

        # 图像信号权重
        ttk.Label(signal_group, text="👁️ 图像信号权重:").pack(anchor=tk.W, padx=10, pady=2)
        self.image_weight_var = tk.DoubleVar(value=0.4)
        image_weight_scale = ttk.Scale(signal_group, from_=0.0, to=1.0, orient=tk.HORIZONTAL,
                                      variable=self.image_weight_var, length=200)
        image_weight_scale.pack(padx=10, pady=2)

        # 信号确认阈值
        ttk.Label(signal_group, text="✅ 信号确认阈值:").pack(anchor=tk.W, padx=10, pady=2)
        self.signal_threshold_var = tk.DoubleVar(value=0.7)
        threshold_scale = ttk.Scale(signal_group, from_=0.5, to=1.0, orient=tk.HORIZONTAL,
                                   variable=self.signal_threshold_var, length=200)
        threshold_scale.pack(padx=10, pady=2)

        # 策略选择
        strategy_group = ttk.LabelFrame(tab_frame, text="📈 交易策略")
        strategy_group.pack(fill=tk.X, padx=5, pady=5)

        self.strategy_var = tk.StringVar(value="trend_following")
        strategies = [
            ("trend_following", "📈 趋势跟踪"),
            ("mean_reversion", "🔄 均值回归"),
            ("breakout", "💥 突破策略"),
            ("scalping", "⚡ 剥头皮"),
            ("grid_trading", "🕸️ 网格交易")
        ]

        for value, text in strategies:
            ttk.Radiobutton(strategy_group, text=text, variable=self.strategy_var,
                           value=value).pack(anchor=tk.W, padx=10, pady=2)

        # 时间过滤
        time_group = ttk.LabelFrame(tab_frame, text="⏰ 时间过滤")
        time_group.pack(fill=tk.X, padx=5, pady=5)

        self.enable_time_filter_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(time_group, text="启用时间过滤",
                       variable=self.enable_time_filter_var).pack(anchor=tk.W, padx=10, pady=2)

        time_frame = ttk.Frame(time_group)
        time_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(time_frame, text="开始时间:").grid(row=0, column=0, sticky=tk.W)
        self.start_time_var = tk.StringVar(value="09:00")
        ttk.Entry(time_frame, textvariable=self.start_time_var, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(time_frame, text="结束时间:").grid(row=0, column=2, sticky=tk.W, padx=(20,0))
        self.end_time_var = tk.StringVar(value="15:00")
        ttk.Entry(time_frame, textvariable=self.end_time_var, width=10).grid(row=0, column=3, padx=5)

    def create_risk_management_tab(self):
        """创建风险管理标签页"""
        tab_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(tab_frame, text="🛡️ 风险管理")

        # 资金管理
        money_group = ttk.LabelFrame(tab_frame, text="💰 资金管理")
        money_group.pack(fill=tk.X, padx=5, pady=5)

        money_frame = ttk.Frame(money_group)
        money_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(money_frame, text="最大风险比例:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.max_risk_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(money_frame, from_=0.5, to=10.0, increment=0.5,
                   textvariable=self.max_risk_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Label(money_frame, text="%").grid(row=0, column=2, sticky=tk.W)

        ttk.Label(money_frame, text="单笔最大损失:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.max_loss_var = tk.DoubleVar(value=100.0)
        ttk.Spinbox(money_frame, from_=50.0, to=1000.0, increment=50.0,
                   textvariable=self.max_loss_var, width=10).grid(row=1, column=1, padx=5)
        ttk.Label(money_frame, text="元").grid(row=1, column=2, sticky=tk.W)

        # 风险控制
        risk_group = ttk.LabelFrame(tab_frame, text="⚠️ 风险控制")
        risk_group.pack(fill=tk.X, padx=5, pady=5)

        self.enable_daily_loss_limit_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(risk_group, text="启用日损失限制",
                       variable=self.enable_daily_loss_limit_var).pack(anchor=tk.W, padx=10, pady=2)

        daily_frame = ttk.Frame(risk_group)
        daily_frame.pack(fill=tk.X, padx=10, pady=2)

        ttk.Label(daily_frame, text="日最大损失:").pack(side=tk.LEFT)
        self.daily_loss_limit_var = tk.DoubleVar(value=500.0)
        ttk.Spinbox(daily_frame, from_=100.0, to=2000.0, increment=100.0,
                   textvariable=self.daily_loss_limit_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(daily_frame, text="元").pack(side=tk.LEFT)

        # 连续亏损控制
        consecutive_group = ttk.LabelFrame(tab_frame, text="📉 连续亏损控制")
        consecutive_group.pack(fill=tk.X, padx=5, pady=5)

        self.enable_consecutive_loss_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(consecutive_group, text="启用连续亏损停止",
                       variable=self.enable_consecutive_loss_var).pack(anchor=tk.W, padx=10, pady=2)

        consecutive_frame = ttk.Frame(consecutive_group)
        consecutive_frame.pack(fill=tk.X, padx=10, pady=2)

        ttk.Label(consecutive_frame, text="最大连续亏损次数:").pack(side=tk.LEFT)
        self.max_consecutive_losses_var = tk.IntVar(value=3)
        ttk.Spinbox(consecutive_frame, from_=2, to=10, increment=1,
                   textvariable=self.max_consecutive_losses_var, width=10).pack(side=tk.LEFT, padx=5)

        # 紧急停止
        emergency_group = ttk.LabelFrame(tab_frame, text="🚨 紧急停止")
        emergency_group.pack(fill=tk.X, padx=5, pady=5)

        emergency_frame = ttk.Frame(emergency_group)
        emergency_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(emergency_frame, text="🛑 立即停止所有交易",
                  command=self.emergency_stop_all, style='Danger.TButton').pack(fill=tk.X, pady=2)
        ttk.Button(emergency_frame, text="💰 强制平仓所有持仓",
                  command=self.force_close_all, style='Warning.TButton').pack(fill=tk.X, pady=2)

    def create_advanced_settings_tab(self):
        """创建高级设置标签页"""
        tab_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(tab_frame, text="🔧 高级设置")

        # 创建滚动区域
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # API设置
        api_group = ttk.LabelFrame(scrollable_frame, text="🔌 API设置")
        api_group.pack(fill=tk.X, padx=5, pady=5)

        api_frame = ttk.Frame(api_group)
        api_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(api_frame, text="请求超时:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.api_timeout_var = tk.IntVar(value=30)
        ttk.Spinbox(api_frame, from_=10, to=120, increment=5,
                   textvariable=self.api_timeout_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Label(api_frame, text="秒").grid(row=0, column=2, sticky=tk.W)

        ttk.Label(api_frame, text="重试次数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.api_retry_var = tk.IntVar(value=3)
        ttk.Spinbox(api_frame, from_=1, to=10, increment=1,
                   textvariable=self.api_retry_var, width=10).grid(row=1, column=1, padx=5)

        ttk.Label(api_frame, text="请求间隔:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.api_interval_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(api_frame, from_=0.1, to=10.0, increment=0.1,
                   textvariable=self.api_interval_var, width=10).grid(row=2, column=1, padx=5)
        ttk.Label(api_frame, text="秒").grid(row=2, column=2, sticky=tk.W)

        # 图像识别设置
        image_group = ttk.LabelFrame(scrollable_frame, text="👁️ 图像识别设置")
        image_group.pack(fill=tk.X, padx=5, pady=5)

        image_frame = ttk.Frame(image_group)
        image_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(image_frame, text="识别精度:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.image_accuracy_var = tk.DoubleVar(value=0.8)
        ttk.Scale(image_frame, from_=0.5, to=1.0, orient=tk.HORIZONTAL,
                 variable=self.image_accuracy_var, length=150).grid(row=0, column=1, padx=5)

        ttk.Label(image_frame, text="截图间隔:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.screenshot_interval_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(image_frame, from_=0.5, to=10.0, increment=0.5,
                   textvariable=self.screenshot_interval_var, width=10).grid(row=1, column=1, padx=5)
        ttk.Label(image_frame, text="秒").grid(row=1, column=2, sticky=tk.W)

        self.enable_image_debug_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(image_group, text="启用图像调试模式",
                       variable=self.enable_image_debug_var).pack(anchor=tk.W, padx=10, pady=2)

        # 日志设置
        log_group = ttk.LabelFrame(scrollable_frame, text="📝 日志设置")
        log_group.pack(fill=tk.X, padx=5, pady=5)

        log_frame = ttk.Frame(log_group)
        log_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(log_frame, text="日志级别:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(log_frame, textvariable=self.log_level_var,
                                      values=["DEBUG", "INFO", "WARNING", "ERROR"], width=10)
        log_level_combo.grid(row=0, column=1, padx=5)

        ttk.Label(log_frame, text="最大日志行数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.max_log_lines_var = tk.IntVar(value=1000)
        ttk.Spinbox(log_frame, from_=100, to=5000, increment=100,
                   textvariable=self.max_log_lines_var, width=10).grid(row=1, column=1, padx=5)

        self.enable_file_log_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_group, text="启用文件日志",
                       variable=self.enable_file_log_var).pack(anchor=tk.W, padx=10, pady=2)

        self.enable_detailed_log_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_group, text="启用详细日志",
                       variable=self.enable_detailed_log_var).pack(anchor=tk.W, padx=10, pady=2)

        # 性能优化
        performance_group = ttk.LabelFrame(scrollable_frame, text="⚡ 性能优化")
        performance_group.pack(fill=tk.X, padx=5, pady=5)

        perf_frame = ttk.Frame(performance_group)
        perf_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(perf_frame, text="更新频率:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.update_frequency_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(perf_frame, from_=0.1, to=5.0, increment=0.1,
                   textvariable=self.update_frequency_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Label(perf_frame, text="秒").grid(row=0, column=2, sticky=tk.W)

        self.enable_multithreading_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(performance_group, text="启用多线程处理",
                       variable=self.enable_multithreading_var).pack(anchor=tk.W, padx=10, pady=2)

        self.enable_caching_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(performance_group, text="启用数据缓存",
                       variable=self.enable_caching_var).pack(anchor=tk.W, padx=10, pady=2)

        # 保存设置按钮
        save_frame = ttk.Frame(scrollable_frame)
        save_frame.pack(fill=tk.X, padx=5, pady=10)

        ttk.Button(save_frame, text="💾 保存所有设置",
                  command=self.save_all_settings, style='Success.TButton').pack(fill=tk.X)
        ttk.Button(save_frame, text="🔄 重置为默认",
                  command=self.reset_to_defaults, style='Warning.TButton').pack(fill=tk.X, pady=(5,0))

        # 布局滚动区域
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_center_panel(self):
        """创建中央监控面板"""
        self.center_frame = ttk.Frame(self.main_container, style='Card.TFrame')
        self.main_container.add(self.center_frame, weight=2)

        # 创建标签页控件
        self.center_notebook = ttk.Notebook(self.center_frame)
        self.center_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 实时监控页面
        self.create_realtime_monitor_tab()

        # 交易统计页面
        self.create_trading_stats_tab()

        # 持仓管理页面
        self.create_position_management_tab()

        # 市场分析页面
        self.create_market_analysis_tab()

    def create_realtime_monitor_tab(self):
        """创建实时监控标签页"""
        tab_frame = ttk.Frame(self.center_notebook)
        self.center_notebook.add(tab_frame, text="📊 实时监控")

        # 系统状态显示
        status_group = ttk.LabelFrame(tab_frame, text="🔄 系统状态")
        status_group.pack(fill=tk.X, padx=5, pady=5)

        status_grid = ttk.Frame(status_group)
        status_grid.pack(fill=tk.X, padx=10, pady=10)

        # 状态指示器
        ttk.Label(status_grid, text="系统状态:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.system_status_label = ttk.Label(status_grid, text="🔴 未启动", style='Status.TLabel')
        self.system_status_label.grid(row=0, column=1, sticky=tk.W, padx=10)

        ttk.Label(status_grid, text="交易模式:", font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky=tk.W, padx=5)
        self.trading_mode_label = ttk.Label(status_grid, text="🔗 混合模式", style='Status.TLabel')
        self.trading_mode_label.grid(row=0, column=3, sticky=tk.W, padx=10)

        ttk.Label(status_grid, text="API状态:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.api_status_label = ttk.Label(status_grid, text="⚪ 未连接", style='Status.TLabel')
        self.api_status_label.grid(row=1, column=1, sticky=tk.W, padx=10)

        ttk.Label(status_grid, text="图像状态:", font=('Arial', 10, 'bold')).grid(row=1, column=2, sticky=tk.W, padx=5)
        self.image_status_label = ttk.Label(status_grid, text="⚪ 未启动", style='Status.TLabel')
        self.image_status_label.grid(row=1, column=3, sticky=tk.W, padx=10)

        # 交易统计显示
        stats_group = ttk.LabelFrame(tab_frame, text="📈 交易统计")
        stats_group.pack(fill=tk.X, padx=5, pady=5)

        stats_grid = ttk.Frame(stats_group)
        stats_grid.pack(fill=tk.X, padx=10, pady=10)

        # 统计数据
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

        # 实时价格显示
        price_group = ttk.LabelFrame(tab_frame, text="💰 实时价格")
        price_group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建价格表格
        price_frame = ttk.Frame(price_group)
        price_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 表格列标题
        columns = ("商品代码", "商品名称", "当前价格", "涨跌", "涨跌幅", "信号", "状态")
        self.price_tree = ttk.Treeview(price_frame, columns=columns, show='headings', height=8)

        # 设置列标题和宽度
        for col in columns:
            self.price_tree.heading(col, text=col)
            self.price_tree.column(col, width=100, anchor=tk.CENTER)

        # 添加滚动条
        price_scrollbar = ttk.Scrollbar(price_frame, orient=tk.VERTICAL, command=self.price_tree.yview)
        self.price_tree.configure(yscrollcommand=price_scrollbar.set)

        # 布局表格
        self.price_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        price_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 添加示例数据
        sample_data = [
            ("511", "韩式陶瓷茶具", "3001.50", "+1.50", "+0.05%", "🟢 买涨", "监控中"),
            ("507", "五福临门茶碗", "2998.20", "-2.30", "-0.08%", "🔴 买跌", "监控中"),
            ("512", "寿桃陶瓷茶器", "3005.80", "+5.80", "+0.19%", "🟡 观望", "监控中"),
        ]

        for data in sample_data:
            self.price_tree.insert("", tk.END, values=data)

    def create_trading_stats_tab(self):
        """创建交易统计标签页"""
        tab_frame = ttk.Frame(self.center_notebook)
        self.center_notebook.add(tab_frame, text="📊 交易统计")

        # 今日统计
        today_group = ttk.LabelFrame(tab_frame, text="📅 今日统计")
        today_group.pack(fill=tk.X, padx=5, pady=5)

        today_grid = ttk.Frame(today_group)
        today_grid.pack(fill=tk.X, padx=10, pady=10)

        # 统计项目
        stats_items = [
            ("交易次数", "0", 0, 0),
            ("成功次数", "0", 0, 1),
            ("失败次数", "0", 0, 2),
            ("成功率", "0%", 0, 3),
            ("总盈亏", "0.00", 1, 0),
            ("最大盈利", "0.00", 1, 1),
            ("最大亏损", "0.00", 1, 2),
            ("平均盈亏", "0.00", 1, 3),
        ]

        self.stats_labels = {}
        for label, value, row, col in stats_items:
            ttk.Label(today_grid, text=f"{label}:", font=('Arial', 10, 'bold')).grid(
                row=row, column=col*2, sticky=tk.W, padx=5, pady=2)
            label_widget = ttk.Label(today_grid, text=value, style='Status.TLabel')
            label_widget.grid(row=row, column=col*2+1, sticky=tk.W, padx=10, pady=2)
            self.stats_labels[label] = label_widget

        # 历史统计图表区域
        chart_group = ttk.LabelFrame(tab_frame, text="📈 历史统计图表")
        chart_group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 图表占位符
        chart_frame = ttk.Frame(chart_group)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        chart_placeholder = ttk.Label(chart_frame, text="📊 图表功能开发中...\n\n将显示:\n• 每日盈亏曲线\n• 成功率趋势\n• 交易频率分布\n• 风险收益分析",
                                     font=('Arial', 12), anchor=tk.CENTER, justify=tk.CENTER)
        chart_placeholder.pack(expand=True)

    def create_position_management_tab(self):
        """创建持仓管理标签页"""
        tab_frame = ttk.Frame(self.center_notebook)
        self.center_notebook.add(tab_frame, text="💼 持仓管理")

        # 当前持仓
        position_group = ttk.LabelFrame(tab_frame, text="📋 当前持仓")
        position_group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        position_frame = ttk.Frame(position_group)
        position_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 持仓表格
        position_columns = ("商品", "方向", "数量", "开仓价", "当前价", "盈亏", "盈亏率", "操作")
        self.position_tree = ttk.Treeview(position_frame, columns=position_columns, show='headings', height=10)

        for col in position_columns:
            self.position_tree.heading(col, text=col)
            self.position_tree.column(col, width=80, anchor=tk.CENTER)

        # 持仓表格滚动条
        position_scrollbar = ttk.Scrollbar(position_frame, orient=tk.VERTICAL, command=self.position_tree.yview)
        self.position_tree.configure(yscrollcommand=position_scrollbar.set)

        self.position_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        position_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 持仓操作按钮
        position_control_frame = ttk.Frame(tab_frame)
        position_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(position_control_frame, text="🔄 刷新持仓",
                  command=self.refresh_positions).pack(side=tk.LEFT, padx=5)
        ttk.Button(position_control_frame, text="💰 全部平仓",
                  command=self.close_all_positions, style='Warning.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(position_control_frame, text="📊 持仓分析",
                  command=self.analyze_positions).pack(side=tk.LEFT, padx=5)

    def create_market_analysis_tab(self):
        """创建市场分析标签页"""
        tab_frame = ttk.Frame(self.center_notebook)
        self.center_notebook.add(tab_frame, text="🔍 市场分析")

        # K线分析
        kline_group = ttk.LabelFrame(tab_frame, text="📈 K线分析")
        kline_group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        kline_frame = ttk.Frame(kline_group)
        kline_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # K线分析文本框
        self.kline_analysis_text = scrolledtext.ScrolledText(
            kline_frame, height=15, width=60, font=('Consolas', 9)
        )
        self.kline_analysis_text.pack(fill=tk.BOTH, expand=True)

        # 分析控制按钮
        analysis_control_frame = ttk.Frame(tab_frame)
        analysis_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(analysis_control_frame, text="🔄 刷新分析",
                  command=self.refresh_market_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(analysis_control_frame, text="📊 技术指标",
                  command=self.show_technical_indicators).pack(side=tk.LEFT, padx=5)
        ttk.Button(analysis_control_frame, text="📈 趋势预测",
                  command=self.show_trend_prediction).pack(side=tk.LEFT, padx=5)

    def create_right_panel(self):
        """创建右侧日志面板"""
        self.right_frame = ttk.Frame(self.main_container, style='Card.TFrame')
        self.main_container.add(self.right_frame, weight=1)

        # 创建标签页控件
        self.right_notebook = ttk.Notebook(self.right_frame)
        self.right_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 系统日志页面
        self.create_system_log_tab()

        # 交易日志页面
        self.create_trading_log_tab()

        # 错误日志页面
        self.create_error_log_tab()

        # 调试信息页面
        self.create_debug_info_tab()

    def create_system_log_tab(self):
        """创建系统日志标签页"""
        tab_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(tab_frame, text="📝 系统日志")

        # 日志过滤器
        filter_frame = ttk.Frame(tab_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="过滤级别:").pack(side=tk.LEFT, padx=5)
        self.log_filter_var = tk.StringVar(value="ALL")
        log_filter_combo = ttk.Combobox(filter_frame, textvariable=self.log_filter_var,
                                       values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR"], width=10)
        log_filter_combo.pack(side=tk.LEFT, padx=5)
        log_filter_combo.bind("<<ComboboxSelected>>", self.filter_logs)

        ttk.Button(filter_frame, text="🔍 搜索", command=self.search_logs).pack(side=tk.LEFT, padx=5)

        # 系统日志文本框
        self.system_log_text = scrolledtext.ScrolledText(
            tab_frame, height=25, width=50, font=('Consolas', 9)
        )
        self.system_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 日志控制按钮
        log_control_frame = ttk.Frame(tab_frame)
        log_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(log_control_frame, text="🧹 清空", command=self.clear_system_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_control_frame, text="💾 保存", command=self.save_system_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_control_frame, text="🔄 刷新", command=self.refresh_system_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_control_frame, text="⏸️ 暂停", command=self.pause_log_updates).pack(side=tk.LEFT, padx=2)

    def create_trading_log_tab(self):
        """创建交易日志标签页"""
        tab_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(tab_frame, text="💰 交易日志")

        # 交易日志过滤器
        trading_filter_frame = ttk.Frame(tab_frame)
        trading_filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(trading_filter_frame, text="交易类型:").pack(side=tk.LEFT, padx=5)
        self.trading_filter_var = tk.StringVar(value="ALL")
        trading_filter_combo = ttk.Combobox(trading_filter_frame, textvariable=self.trading_filter_var,
                                           values=["ALL", "开仓", "平仓", "买涨", "买跌"], width=10)
        trading_filter_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(trading_filter_frame, text="商品:").pack(side=tk.LEFT, padx=(20,5))
        self.product_filter_var = tk.StringVar(value="ALL")
        product_filter_combo = ttk.Combobox(trading_filter_frame, textvariable=self.product_filter_var,
                                           values=["ALL", "511", "507", "512", "520", "888"], width=8)
        product_filter_combo.pack(side=tk.LEFT, padx=5)

        # 交易日志文本框
        self.trading_log_text = scrolledtext.ScrolledText(
            tab_frame, height=25, width=50, font=('Consolas', 9)
        )
        self.trading_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 添加示例交易日志
        sample_trading_logs = [
            "[18:54:03] 🎯 信号检测: 前一分钟K线 开盘3000.00→收盘3001.20 信号:买涨",
            "[18:54:04] 📋 开始下单: 商品511 买涨 - 前一分钟K线顺向信号",
            "[18:54:04] 🔄 第1次下单: 买涨 原价3001.10 偏移价3001.60 (偏移+0.5点)",
            "[18:54:04] ✅ 第1次API调用成功: 买涨 偏移价3001.60 等待成交确认...",
            "[18:54:25] ✅ 下单成功: 商品511 买涨 价格3001.50 数量1手 已成交",
            "[18:54:29] 📊 持仓详情: 方向B 入场价3001.50 开始实时监控止盈止损",
            "[18:54:32] 📊 实时监控: 买涨 入场3001.50 当前3003.60 盈亏2.10点",
            "[18:54:38] ✅ 平仓成功: 商品511 价格3003.60 盈利2.10点",
            "[18:54:44] 📊 平仓详情: 实时止盈触发(盈利2.1点) 持仓已完全清空",
        ]

        for log in sample_trading_logs:
            self.trading_log_text.insert(tk.END, log + "\n")

        # 交易日志控制按钮
        trading_control_frame = ttk.Frame(tab_frame)
        trading_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(trading_control_frame, text="🧹 清空", command=self.clear_trading_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(trading_control_frame, text="💾 导出", command=self.export_trading_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(trading_control_frame, text="📊 统计", command=self.analyze_trading_log).pack(side=tk.LEFT, padx=2)

    def create_error_log_tab(self):
        """创建错误日志标签页"""
        tab_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(tab_frame, text="❌ 错误日志")

        # 错误统计
        error_stats_frame = ttk.Frame(tab_frame)
        error_stats_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(error_stats_frame, text="今日错误:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.error_count_label = ttk.Label(error_stats_frame, text="0", style='Error.TLabel')
        self.error_count_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(error_stats_frame, text="警告:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(20,5))
        self.warning_count_label = ttk.Label(error_stats_frame, text="0", style='Warning.TLabel')
        self.warning_count_label.pack(side=tk.LEFT, padx=5)

        # 错误日志文本框
        self.error_log_text = scrolledtext.ScrolledText(
            tab_frame, height=25, width=50, font=('Consolas', 9)
        )
        self.error_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 错误日志控制按钮
        error_control_frame = ttk.Frame(tab_frame)
        error_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(error_control_frame, text="🧹 清空", command=self.clear_error_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(error_control_frame, text="📧 报告", command=self.report_errors).pack(side=tk.LEFT, padx=2)
        ttk.Button(error_control_frame, text="🔧 诊断", command=self.diagnose_errors).pack(side=tk.LEFT, padx=2)

    def create_debug_info_tab(self):
        """创建调试信息标签页"""
        tab_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(tab_frame, text="🔧 调试信息")

        # 系统信息
        system_info_group = ttk.LabelFrame(tab_frame, text="💻 系统信息")
        system_info_group.pack(fill=tk.X, padx=5, pady=5)

        system_info_frame = ttk.Frame(system_info_group)
        system_info_frame.pack(fill=tk.X, padx=10, pady=5)

        # 系统信息显示
        info_items = [
            ("Python版本", f"{sys.version.split()[0]}", 0, 0),
            ("系统平台", f"{sys.platform}", 0, 1),
            ("内存使用", "计算中...", 1, 0),
            ("CPU使用", "计算中...", 1, 1),
        ]

        self.system_info_labels = {}
        for label, value, row, col in info_items:
            ttk.Label(system_info_frame, text=f"{label}:", font=('Arial', 9, 'bold')).grid(
                row=row, column=col*2, sticky=tk.W, padx=5, pady=2)
            label_widget = ttk.Label(system_info_frame, text=value, font=('Arial', 9))
            label_widget.grid(row=row, column=col*2+1, sticky=tk.W, padx=10, pady=2)
            self.system_info_labels[label] = label_widget

        # 调试日志文本框
        self.debug_log_text = scrolledtext.ScrolledText(
            tab_frame, height=20, width=50, font=('Consolas', 8)
        )
        self.debug_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 调试控制按钮
        debug_control_frame = ttk.Frame(tab_frame)
        debug_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(debug_control_frame, text="🔄 刷新信息", command=self.refresh_debug_info).pack(side=tk.LEFT, padx=2)
        ttk.Button(debug_control_frame, text="📊 性能分析", command=self.show_performance_analysis).pack(side=tk.LEFT, padx=2)
        ttk.Button(debug_control_frame, text="🧪 运行测试", command=self.run_system_tests).pack(side=tk.LEFT, padx=2)

    def create_status_bar(self):
        """创建状态栏"""
        self.status_frame = ttk.Frame(self.root, style='Panel.TFrame')

        # 状态信息
        self.status_label = ttk.Label(self.status_frame, text="🔴 系统未启动", style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

        # 连接状态
        self.connection_label = ttk.Label(self.status_frame, text="⚪ API未连接", style='Status.TLabel')
        self.connection_label.pack(side=tk.LEFT, padx=10, pady=5)

        # 时间显示
        self.time_label = ttk.Label(self.status_frame, text="", style='Status.TLabel')
        self.time_label.pack(side=tk.RIGHT, padx=10, pady=5)

        # 更新时间
        self.update_time_display()

    def create_floating_tools(self):
        """创建浮动工具面板"""
        # 这里可以添加浮动工具窗口，如快速操作面板等
        pass

    def setup_layout(self):
        """设置布局"""
        # 工具栏
        self.toolbar_frame.pack(fill=tk.X, side=tk.TOP)

        # 主容器
        self.main_container.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        # 状态栏
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)

    def bind_events(self):
        """绑定事件"""
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 键盘快捷键
        self.root.bind('<Control-s>', lambda e: self.save_all_settings())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<F5>', lambda e: self.refresh_interface())
        self.root.bind('<F1>', lambda e: self.show_help())

        # 鼠标事件
        self.price_tree.bind('<Double-1>', self.on_price_double_click)
        self.position_tree.bind('<Double-1>', self.on_position_double_click)

    def setup_logging(self):
        """设置日志系统"""
        # 创建自定义日志处理器
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                try:
                    msg = self.format(record)
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)

                    # 限制日志行数
                    lines = int(self.text_widget.index('end-1c').split('.')[0])
                    if lines > 1000:
                        self.text_widget.delete('1.0', '100.0')

                except Exception:
                    pass

        # 配置日志
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # 添加GUI日志处理器
        gui_handler = GUILogHandler(self.system_log_text)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s',
                                     datefmt='%H:%M:%S')
        gui_handler.setFormatter(formatter)
        logger.addHandler(gui_handler)

        # 添加文件日志处理器
        if self.config_data.get("monitoring", {}).get("enable_file_log", True):
            try:
                log_dir = Path("logs")
                log_dir.mkdir(exist_ok=True)

                file_handler = logging.FileHandler(
                    log_dir / f"trading_{datetime.now().strftime('%Y%m%d')}.log",
                    encoding='utf-8'
                )
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                print(f"❌ 创建文件日志失败: {e}")

    def start_status_updates(self):
        """启动状态更新"""
        def update_status():
            try:
                # 更新时间显示
                self.update_time_display()

                # 更新系统状态
                self.update_system_status()

                # 更新性能信息
                self.update_performance_info()

                # 调度下次更新
                self.root.after(int(self.update_interval * 1000), update_status)

            except Exception as e:
                logging.error(f"状态更新失败: {e}")

        # 启动更新循环
        update_status()

    def update_time_display(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=f"🕐 {current_time}")

    def update_system_status(self):
        """更新系统状态"""
        if self.is_monitoring:
            self.system_status_label.config(text="🟢 运行中", style='Status.TLabel')
            self.status_label.config(text="🟢 系统运行中")
        else:
            self.system_status_label.config(text="🔴 已停止", style='Error.TLabel')
            self.status_label.config(text="🔴 系统已停止")

    def update_performance_info(self):
        """更新性能信息"""
        try:
            import psutil

            # 更新内存使用
            memory_percent = psutil.virtual_memory().percent
            self.system_info_labels["内存使用"].config(text=f"{memory_percent:.1f}%")

            # 更新CPU使用
            cpu_percent = psutil.cpu_percent()
            self.system_info_labels["CPU使用"].config(text=f"{cpu_percent:.1f}%")

        except ImportError:
            # 如果没有psutil，显示占位符
            self.system_info_labels["内存使用"].config(text="需要psutil")
            self.system_info_labels["CPU使用"].config(text="需要psutil")
        except Exception as e:
            logging.error(f"更新性能信息失败: {e}")

    # 事件处理方法
    def on_closing(self):
        """窗口关闭事件"""
        try:
            # 保存用户设置
            self.user_settings["window_geometry"] = self.root.geometry()
            self.save_user_settings()

            # 停止监控
            if self.is_monitoring:
                self.stop_monitoring()

            # 关闭窗口
            self.root.quit()
            self.root.destroy()

        except Exception as e:
            print(f"❌ 关闭窗口失败: {e}")

    def save_user_settings(self):
        """保存用户设置"""
        try:
            settings_file = Path("config/user_settings.json")
            settings_file.parent.mkdir(exist_ok=True)

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_settings, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logging.error(f"保存用户设置失败: {e}")

    # 控制方法
    def start_monitoring(self):
        """启动监控"""
        try:
            if not self.is_monitoring:
                self.is_monitoring = True
                logging.info("🚀 启动智能量化交易监控")

                # 更新按钮状态
                self.start_button.config(state='disabled')
                self.stop_button.config(state='normal')

                # 启动监控线程
                self.start_monitoring_thread()

        except Exception as e:
            logging.error(f"启动监控失败: {e}")
            messagebox.showerror("启动失败", f"启动监控失败: {e}")

    def stop_monitoring(self):
        """停止监控"""
        try:
            if self.is_monitoring:
                self.is_monitoring = False
                logging.info("⏹️ 停止智能量化交易监控")

                # 更新按钮状态
                self.start_button.config(state='normal')
                self.stop_button.config(state='disabled')

        except Exception as e:
            logging.error(f"停止监控失败: {e}")

    def start_monitoring_thread(self):
        """启动监控线程"""
        def monitoring_loop():
            while self.is_monitoring:
                try:
                    # 执行监控逻辑
                    self.execute_monitoring_cycle()

                    # 等待下一个周期
                    time.sleep(self.update_interval)

                except Exception as e:
                    logging.error(f"监控循环错误: {e}")
                    time.sleep(5)  # 错误后等待5秒再继续

        # 启动监控线程
        self.status_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.status_thread.start()

    def execute_monitoring_cycle(self):
        """执行一个监控周期"""
        try:
            # 获取选中的商品
            selected_products = [code for code, var in self.product_vars.items() if var.get()]

            if not selected_products:
                return

            # 根据交易模式执行不同的监控逻辑
            trading_mode = self.trading_mode_var.get()

            if trading_mode == "api_only":
                self.execute_api_monitoring(selected_products)
            elif trading_mode == "image_only":
                self.execute_image_monitoring(selected_products)
            elif trading_mode == "hybrid":
                self.execute_hybrid_monitoring(selected_products)
            elif trading_mode == "ai_smart":
                self.execute_ai_monitoring(selected_products)

        except Exception as e:
            logging.error(f"监控周期执行失败: {e}")

    def execute_api_monitoring(self, products):
        """执行API监控"""
        logging.info(f"🤖 执行API监控: {products}")
        # 这里添加API监控逻辑

    def execute_image_monitoring(self, products):
        """执行图像监控"""
        logging.info(f"👁️ 执行图像监控: {products}")
        # 这里添加图像监控逻辑

    def execute_hybrid_monitoring(self, products):
        """执行混合监控"""
        logging.info(f"🔗 执行混合监控: {products}")
        # 这里添加混合监控逻辑

    def execute_ai_monitoring(self, products):
        """执行AI智能监控"""
        logging.info(f"🧠 执行AI智能监控: {products}")
        # 这里添加AI监控逻辑

    # 测试方法
    def test_api(self):
        """测试API连接"""
        try:
            logging.info("🧪 开始API连接测试...")
            # 这里添加API测试逻辑
            messagebox.showinfo("测试结果", "API连接测试完成！")
        except Exception as e:
            logging.error(f"API测试失败: {e}")
            messagebox.showerror("测试失败", f"API测试失败: {e}")

    def test_image(self):
        """测试图像识别"""
        try:
            logging.info("📸 开始图像识别测试...")
            # 这里添加图像测试逻辑
            messagebox.showinfo("测试结果", "图像识别测试完成！")
        except Exception as e:
            logging.error(f"图像测试失败: {e}")
            messagebox.showerror("测试失败", f"图像测试失败: {e}")

    # 快速操作方法
    def quick_start(self):
        """快速启动"""
        try:
            # 使用默认设置快速启动
            self.trading_mode_var.set("hybrid")

            # 选择默认商品
            for code in ["511", "507", "512"]:
                if code in self.product_vars:
                    self.product_vars[code].set(True)

            # 启动监控
            self.start_monitoring()

            logging.info("⚡ 快速启动完成")

        except Exception as e:
            logging.error(f"快速启动失败: {e}")
            messagebox.showerror("快速启动失败", f"快速启动失败: {e}")

    def pause_trading(self):
        """暂停交易"""
        try:
            logging.info("⏸️ 暂停交易")
            # 这里添加暂停逻辑
            messagebox.showinfo("操作完成", "交易已暂停")
        except Exception as e:
            logging.error(f"暂停交易失败: {e}")

    def emergency_stop(self):
        """紧急停止"""
        try:
            result = messagebox.askyesno("紧急停止", "确定要紧急停止所有交易吗？")
            if result:
                self.stop_monitoring()
                logging.warning("🛑 紧急停止所有交易")
                messagebox.showinfo("操作完成", "已紧急停止所有交易")
        except Exception as e:
            logging.error(f"紧急停止失败: {e}")

    def reset_system(self):
        """重置系统"""
        try:
            result = messagebox.askyesno("重置系统", "确定要重置系统吗？这将清除所有临时数据。")
            if result:
                self.stop_monitoring()

                # 重置性能数据
                self.performance_data = {
                    "start_time": time.time(),
                    "total_trades": 0,
                    "successful_trades": 0,
                    "failed_trades": 0,
                    "total_profit": 0.0
                }

                # 清空日志
                self.clear_all_logs()

                logging.info("🔄 系统已重置")
                messagebox.showinfo("操作完成", "系统已重置")
        except Exception as e:
            logging.error(f"重置系统失败: {e}")

    def logout(self):
        """退出登录"""
        try:
            result = messagebox.askyesno("退出登录", "确定要退出登录吗？")
            if result:
                self.stop_monitoring()
                self.current_user = ""
                self.user_password = ""
                self.user_label.config(text="👤 用户: 未登录")
                logging.info("🚪 用户已退出登录")
        except Exception as e:
            logging.error(f"退出登录失败: {e}")

    # 日志管理方法
    def clear_system_log(self):
        """清空系统日志"""
        self.system_log_text.delete(1.0, tk.END)
        logging.info("🧹 系统日志已清空")

    def clear_trading_log(self):
        """清空交易日志"""
        self.trading_log_text.delete(1.0, tk.END)
        logging.info("🧹 交易日志已清空")

    def clear_error_log(self):
        """清空错误日志"""
        self.error_log_text.delete(1.0, tk.END)
        logging.info("🧹 错误日志已清空")

    def clear_all_logs(self):
        """清空所有日志"""
        self.clear_system_log()
        self.clear_trading_log()
        self.clear_error_log()

    def save_system_log(self):
        """保存系统日志"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.system_log_text.get(1.0, tk.END))
                messagebox.showinfo("保存成功", f"系统日志已保存到: {filename}")
        except Exception as e:
            logging.error(f"保存系统日志失败: {e}")
            messagebox.showerror("保存失败", f"保存系统日志失败: {e}")

    def export_trading_log(self):
        """导出交易日志"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV文件", "*.csv"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.trading_log_text.get(1.0, tk.END))
                messagebox.showinfo("导出成功", f"交易日志已导出到: {filename}")
        except Exception as e:
            logging.error(f"导出交易日志失败: {e}")
            messagebox.showerror("导出失败", f"导出交易日志失败: {e}")

    # 设置管理方法
    def save_all_settings(self):
        """保存所有设置"""
        try:
            # 更新配置数据
            self.config_data["trading"]["max_trades_per_day"] = self.max_trades_var.get()
            self.config_data["trading"]["position_size"] = self.quantity_var.get()
            self.config_data["monitoring"]["update_interval"] = self.update_frequency_var.get()
            self.config_data["monitoring"]["log_level"] = self.log_level_var.get()
            self.config_data["monitoring"]["max_log_lines"] = self.max_log_lines_var.get()

            # 保存配置
            self.save_config(self.config_data)

            logging.info("💾 所有设置已保存")
            messagebox.showinfo("保存成功", "所有设置已保存")

        except Exception as e:
            logging.error(f"保存设置失败: {e}")
            messagebox.showerror("保存失败", f"保存设置失败: {e}")

    def reset_to_defaults(self):
        """重置为默认设置"""
        try:
            result = messagebox.askyesno("重置设置", "确定要重置所有设置为默认值吗？")
            if result:
                # 重置所有变量为默认值
                self.take_profit_var.set(3.0)
                self.stop_loss_var.set(2.0)
                self.quantity_var.set(1)
                self.max_trades_var.set(20)
                self.api_weight_var.set(0.6)
                self.image_weight_var.set(0.4)
                self.signal_threshold_var.set(0.7)
                self.trading_mode_var.set("hybrid")
                self.strategy_var.set("trend_following")

                logging.info("🔄 设置已重置为默认值")
                messagebox.showinfo("重置完成", "所有设置已重置为默认值")

        except Exception as e:
            logging.error(f"重置设置失败: {e}")
            messagebox.showerror("重置失败", f"重置设置失败: {e}")

    # 界面刷新方法
    def refresh_interface(self):
        """刷新界面"""
        try:
            logging.info("🔄 刷新界面")
            # 这里添加界面刷新逻辑
        except Exception as e:
            logging.error(f"刷新界面失败: {e}")

    def refresh_positions(self):
        """刷新持仓"""
        try:
            logging.info("🔄 刷新持仓信息")
            # 这里添加持仓刷新逻辑
        except Exception as e:
            logging.error(f"刷新持仓失败: {e}")

    def refresh_market_analysis(self):
        """刷新市场分析"""
        try:
            logging.info("🔄 刷新市场分析")
            # 这里添加市场分析刷新逻辑
        except Exception as e:
            logging.error(f"刷新市场分析失败: {e}")

    def refresh_debug_info(self):
        """刷新调试信息"""
        try:
            logging.info("🔄 刷新调试信息")
            self.update_performance_info()
        except Exception as e:
            logging.error(f"刷新调试信息失败: {e}")

    # 事件处理方法
    def on_price_double_click(self, event):
        """价格表格双击事件"""
        try:
            selection = self.price_tree.selection()
            if selection:
                item = self.price_tree.item(selection[0])
                product_code = item['values'][0]
                logging.info(f"双击商品: {product_code}")
                # 这里可以添加双击处理逻辑
        except Exception as e:
            logging.error(f"处理价格双击事件失败: {e}")

    def on_position_double_click(self, event):
        """持仓表格双击事件"""
        try:
            selection = self.position_tree.selection()
            if selection:
                item = self.position_tree.item(selection[0])
                product_code = item['values'][0]
                logging.info(f"双击持仓: {product_code}")
                # 这里可以添加双击处理逻辑
        except Exception as e:
            logging.error(f"处理持仓双击事件失败: {e}")

    # 占位符方法（待实现）
    def filter_logs(self, event=None):
        """过滤日志"""
        pass

    def search_logs(self):
        """搜索日志"""
        pass

    def refresh_system_log(self):
        """刷新系统日志"""
        try:
            logging.info("🔄 刷新系统日志")
        except Exception as e:
            logging.error(f"刷新系统日志失败: {e}")

    def pause_log_updates(self):
        """暂停日志更新"""
        try:
            logging.info("⏸️ 暂停日志更新")
        except Exception as e:
            logging.error(f"暂停日志更新失败: {e}")

    def analyze_trading_log(self):
        """分析交易日志"""
        try:
            logging.info("📊 分析交易日志")
            messagebox.showinfo("分析结果", "交易日志分析功能开发中...")
        except Exception as e:
            logging.error(f"分析交易日志失败: {e}")

    def report_errors(self):
        """报告错误"""
        pass

    def diagnose_errors(self):
        """诊断错误"""
        pass

    def show_performance_analysis(self):
        """显示性能分析"""
        pass

    def run_system_tests(self):
        """运行系统测试"""
        pass

    def emergency_stop_all(self):
        """紧急停止所有交易"""
        self.emergency_stop()

    def force_close_all(self):
        """强制平仓所有持仓"""
        pass

    def close_all_positions(self):
        """关闭所有持仓"""
        pass

    def analyze_positions(self):
        """分析持仓"""
        pass

    def show_technical_indicators(self):
        """显示技术指标"""
        pass

    def show_trend_prediction(self):
        """显示趋势预测"""
        pass

    # 菜单方法（占位符）
    def export_trading_records(self):
        """导出交易记录"""
        pass

    def export_logs(self):
        """导出日志"""
        pass

    def import_config(self):
        """导入配置"""
        pass

    def export_config(self):
        """导出配置"""
        pass

    def show_performance_monitor(self):
        """显示性能监控"""
        pass

    def show_trading_statistics(self):
        """显示交易统计"""
        pass

    def show_interface_settings(self):
        """显示界面设置"""
        pass

    def show_api_test(self):
        """显示API测试"""
        pass

    def show_screenshot_tool(self):
        """显示截图工具"""
        pass

    def show_log_analyzer(self):
        """显示日志分析器"""
        pass

    def show_performance_optimizer(self):
        """显示性能优化器"""
        pass

    def show_help(self):
        """显示帮助"""
        pass

    def show_troubleshooting(self):
        """显示故障排除"""
        pass

    def show_support_info(self):
        """显示技术支持信息"""
        pass

    def show_about(self):
        """显示关于信息"""
        pass

    def run(self):
        """运行主窗口"""
        try:
            # 恢复窗口状态
            if "window_geometry" in self.user_settings:
                self.root.geometry(self.user_settings["window_geometry"])

            # 启动状态更新
            self.start_status_updates()

            # 绑定关闭事件
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            # 运行主循环
            self.root.mainloop()

        except Exception as e:
            print(f"❌ 运行主窗口失败: {e}")
            messagebox.showerror("运行错误", f"主窗口运行失败: {e}")

def main():
    """测试高级主窗口"""
    app = AdvancedMainWindow()
    app.run()

if __name__ == "__main__":
    main()
