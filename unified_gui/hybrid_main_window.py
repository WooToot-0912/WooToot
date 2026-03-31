#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
混合主窗口 - 智能量化交易系统的统一GUI界面
整合API交易和图像识别功能，提供直观的多模态交易控制
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目路径
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir / "hybrid_core"))

from hybrid_trading_engine import HybridTradingEngine, TradingMode
from signal_fusion_engine import SignalFusionEngine, TradingSignal

class HybridMainWindow:
    """混合主窗口"""

    def __init__(self):
        """初始化混合主窗口"""
        self.root = tk.Tk()
        self.root.title("🎯 智能量化交易系统 v2.0 - 高级多模态融合")
        self.root.geometry("1600x1000")
        self.root.minsize(1400, 800)

        # 用户信息
        self.current_user = ""
        self.user_password = ""

        # 核心组件
        self.hybrid_engine = HybridTradingEngine()
        self.is_monitoring = False

        # GUI组件
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()
        self.bind_events()

        # 状态更新线程
        self.status_thread = None
        self.update_interval = 1.0

        print("✅ 混合主窗口初始化完成")

    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()

        # 配置样式
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 10))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')

    def create_widgets(self):
        """创建GUI组件"""
        # 顶部信息栏
        self.top_frame = ttk.Frame(self.root)

        # 主标题
        self.title_label = ttk.Label(
            self.top_frame,
            text="🎯 智能量化交易系统 - 多模态融合",
            style='Title.TLabel'
        )

        # 用户信息
        self.user_info_frame = ttk.Frame(self.top_frame)
        self.user_label = ttk.Label(
            self.user_info_frame,
            text="👤 用户: 未登录",
            style='Status.TLabel'
        )

        # 退出登录按钮
        self.logout_button = ttk.Button(
            self.user_info_frame,
            text="🚪 退出登录",
            command=self.logout,
            style='Warning.TButton'
        )

        # 创建主框架
        self.main_frame = ttk.Frame(self.root)

        # 左侧控制面板
        self.control_frame = ttk.LabelFrame(self.main_frame, text="🎮 控制面板", padding=10)
        self.create_control_panel()

        # 中间监控面板
        self.monitor_frame = ttk.LabelFrame(self.main_frame, text="📊 实时监控", padding=10)
        self.create_monitor_panel()

        # 右侧日志面板
        self.log_frame = ttk.LabelFrame(self.main_frame, text="📋 系统日志", padding=10)
        self.create_log_panel()

        # 底部状态栏
        self.status_frame = ttk.Frame(self.root)
        self.create_status_bar()

    def create_control_panel(self):
        """创建控制面板"""
        # 模式选择
        mode_frame = ttk.LabelFrame(self.control_frame, text="🎯 交易模式", padding=5)
        mode_frame.pack(fill=tk.X, pady=5)

        self.mode_var = tk.StringVar(value="auto")
        modes = [
            ("🤖 自动模式", "auto"),
            ("🔌 API模式", "api_only"),
            ("🖼️ 图像模式", "image_only"),
            ("🔗 混合模式", "hybrid")
        ]

        for text, value in modes:
            ttk.Radiobutton(
                mode_frame,
                text=text,
                variable=self.mode_var,
                value=value,
                command=self.on_mode_changed
            ).pack(anchor=tk.W)

        # 商品选择
        commodity_frame = ttk.LabelFrame(self.control_frame, text="📈 监控商品", padding=5)
        commodity_frame.pack(fill=tk.X, pady=5)

        self.commodity_var = tk.StringVar(value="511")
        commodities = [
            ("511 - 鹊语梅香茶具", "511"),
            ("507 - 五福临门盖碗", "507"),
            ("512 - 寿桃临福盖碗", "512")
        ]

        for text, value in commodities:
            ttk.Radiobutton(
                commodity_frame,
                text=text,
                variable=self.commodity_var,
                value=value
            ).pack(anchor=tk.W)

        # 控制按钮
        button_frame = ttk.Frame(self.control_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.start_button = ttk.Button(
            button_frame,
            text="🚀 启动监控",
            command=self.start_monitoring,
            style='Success.TButton'
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="🛑 停止监控",
            command=self.stop_monitoring,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 测试按钮
        test_frame = ttk.Frame(self.control_frame)
        test_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            test_frame,
            text="🧪 测试API连接",
            command=self.test_api_connection
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            test_frame,
            text="🖼️ 测试图像检测",
            command=self.test_image_detection
        ).pack(side=tk.LEFT, padx=5)

    def create_monitor_panel(self):
        """创建监控面板"""
        # 信号显示
        signal_frame = ttk.LabelFrame(self.monitor_frame, text="🎯 当前信号", padding=5)
        signal_frame.pack(fill=tk.X, pady=5)

        # API信号
        api_signal_frame = ttk.Frame(signal_frame)
        api_signal_frame.pack(fill=tk.X, pady=2)

        ttk.Label(api_signal_frame, text="🔌 API信号:").pack(side=tk.LEFT)
        self.api_signal_label = ttk.Label(api_signal_frame, text="等待中...", style='Status.TLabel')
        self.api_signal_label.pack(side=tk.LEFT, padx=10)

        # 图像信号
        image_signal_frame = ttk.Frame(signal_frame)
        image_signal_frame.pack(fill=tk.X, pady=2)

        ttk.Label(image_signal_frame, text="🖼️ 图像信号:").pack(side=tk.LEFT)
        self.image_signal_label = ttk.Label(image_signal_frame, text="等待中...", style='Status.TLabel')
        self.image_signal_label.pack(side=tk.LEFT, padx=10)

        # 融合信号
        fusion_signal_frame = ttk.Frame(signal_frame)
        fusion_signal_frame.pack(fill=tk.X, pady=2)

        ttk.Label(fusion_signal_frame, text="🔗 融合信号:").pack(side=tk.LEFT)
        self.fusion_signal_label = ttk.Label(fusion_signal_frame, text="等待中...", style='Status.TLabel')
        self.fusion_signal_label.pack(side=tk.LEFT, padx=10)

        # 性能监控
        perf_frame = ttk.LabelFrame(self.monitor_frame, text="📊 性能监控", padding=5)
        perf_frame.pack(fill=tk.X, pady=5)

        # 交易统计
        stats_frame = ttk.Frame(perf_frame)
        stats_frame.pack(fill=tk.X, pady=2)

        ttk.Label(stats_frame, text="📈 今日交易:").pack(side=tk.LEFT)
        self.trade_count_label = ttk.Label(stats_frame, text="0", style='Status.TLabel')
        self.trade_count_label.pack(side=tk.LEFT, padx=10)

        ttk.Label(stats_frame, text="⏰ 最后交易:").pack(side=tk.LEFT, padx=(20,0))
        self.last_trade_label = ttk.Label(stats_frame, text="无", style='Status.TLabel')
        self.last_trade_label.pack(side=tk.LEFT, padx=10)

        # 成功率显示
        success_frame = ttk.Frame(perf_frame)
        success_frame.pack(fill=tk.X, pady=2)

        ttk.Label(success_frame, text="✅ API成功率:").pack(side=tk.LEFT)
        self.api_success_label = ttk.Label(success_frame, text="0%", style='Status.TLabel')
        self.api_success_label.pack(side=tk.LEFT, padx=10)

        ttk.Label(success_frame, text="🖼️ 图像成功率:").pack(side=tk.LEFT, padx=(20,0))
        self.image_success_label = ttk.Label(success_frame, text="0%", style='Status.TLabel')
        self.image_success_label.pack(side=tk.LEFT, padx=10)

    def create_log_panel(self):
        """创建日志面板"""
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            height=25,
            width=50,
            font=('Consolas', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 日志控制按钮
        log_control_frame = ttk.Frame(self.log_frame)
        log_control_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            log_control_frame,
            text="🧹 清空日志",
            command=self.clear_log
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            log_control_frame,
            text="💾 保存日志",
            command=self.save_log
        ).pack(side=tk.LEFT, padx=5)

    def create_status_bar(self):
        """创建状态栏"""
        # 系统状态
        self.system_status_label = ttk.Label(
            self.status_frame,
            text="🔴 系统未启动",
            style='Status.TLabel'
        )
        self.system_status_label.pack(side=tk.LEFT, padx=10)

        # 连接状态
        self.connection_status_label = ttk.Label(
            self.status_frame,
            text="🔌 API: 未连接 | 🖼️ 图像: 未检测",
            style='Status.TLabel'
        )
        self.connection_status_label.pack(side=tk.RIGHT, padx=10)

    def setup_layout(self):
        """设置布局"""
        # 顶部信息栏
        self.top_frame.pack(fill=tk.X, padx=10, pady=5)

        # 主标题
        self.title_label.pack(side=tk.LEFT)

        # 用户信息（右对齐）
        self.user_info_frame.pack(side=tk.RIGHT)
        self.user_label.pack(side=tk.LEFT, padx=10)
        self.logout_button.pack(side=tk.RIGHT)

        # 主框架
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 三列布局
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.monitor_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 状态栏
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

    def bind_events(self):
        """绑定事件"""
        # 设置引擎回调
        self.hybrid_engine.on_signal_detected = self.on_signal_detected
        self.hybrid_engine.on_trade_executed = self.on_trade_executed
        self.hybrid_engine.on_error_occurred = self.on_error_occurred

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_mode_changed(self):
        """模式改变事件"""
        try:
            mode_str = self.mode_var.get()
            mode = TradingMode(mode_str)
            self.hybrid_engine.set_mode(mode)

            self.log_message(f"🎯 交易模式已切换为: {mode.value}")

        except Exception as e:
            self.log_message(f"❌ 模式切换失败: {e}", "ERROR")

    def start_monitoring(self):
        """启动监控"""
        try:
            if self.is_monitoring:
                messagebox.showwarning("警告", "监控已在运行中")
                return

            commodity_id = self.commodity_var.get()

            # 启动混合引擎监控
            success = self.hybrid_engine.start_monitoring(commodity_id)

            if success:
                self.is_monitoring = True
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)

                # 启动状态更新
                self.start_status_updates()

                self.log_message(f"🚀 监控已启动: {commodity_id}")
                self.update_system_status("🟢 系统运行中")

                messagebox.showinfo("启动成功", f"智能监控已启动\n商品: {commodity_id}\n模式: {self.mode_var.get()}")
            else:
                self.log_message("❌ 监控启动失败", "ERROR")
                messagebox.showerror("启动失败", "监控启动失败，请检查系统配置")

        except Exception as e:
            self.log_message(f"❌ 启动监控异常: {e}", "ERROR")
            messagebox.showerror("异常", f"启动监控异常: {e}")

    def stop_monitoring(self):
        """停止监控"""
        try:
            if not self.is_monitoring:
                messagebox.showwarning("警告", "监控未在运行")
                return

            # 停止混合引擎
            self.hybrid_engine.stop_monitoring()

            self.is_monitoring = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

            # 停止状态更新
            self.stop_status_updates()

            self.log_message("🛑 监控已停止")
            self.update_system_status("🔴 系统已停止")

            messagebox.showinfo("停止成功", "监控已安全停止")

        except Exception as e:
            self.log_message(f"❌ 停止监控异常: {e}", "ERROR")

    def test_api_connection(self):
        """测试API连接"""
        try:
            self.log_message("🔍 测试API连接...")

            # 在后台线程中测试
            def test_thread():
                try:
                    success = self.hybrid_engine._initialize_api_components()

                    def update_ui():
                        if success:
                            self.log_message("✅ API连接测试成功", "SUCCESS")
                            messagebox.showinfo("测试成功", "API连接正常")
                        else:
                            self.log_message("❌ API连接测试失败", "ERROR")
                            messagebox.showerror("测试失败", "API连接失败，请检查网络和账号")

                    self.root.after(0, update_ui)

                except Exception as e:
                    def update_ui():
                        self.log_message(f"❌ API测试异常: {e}", "ERROR")
                        messagebox.showerror("测试异常", f"API测试异常: {e}")

                    self.root.after(0, update_ui)

            threading.Thread(target=test_thread, daemon=True).start()

        except Exception as e:
            self.log_message(f"❌ 启动API测试失败: {e}", "ERROR")

    def test_image_detection(self):
        """测试图像检测"""
        try:
            self.log_message("🔍 测试图像检测...")

            def test_thread():
                try:
                    success = self.hybrid_engine._initialize_image_components()

                    def update_ui():
                        if success:
                            self.log_message("✅ 图像检测测试成功", "SUCCESS")
                            messagebox.showinfo("测试成功", "图像检测功能正常")
                        else:
                            self.log_message("❌ 图像检测测试失败", "ERROR")
                            messagebox.showerror("测试失败", "图像检测初始化失败")

                    self.root.after(0, update_ui)

                except Exception as e:
                    def update_ui():
                        self.log_message(f"❌ 图像测试异常: {e}", "ERROR")
                        messagebox.showerror("测试异常", f"图像测试异常: {e}")

                    self.root.after(0, update_ui)

            threading.Thread(target=test_thread, daemon=True).start()

        except Exception as e:
            self.log_message(f"❌ 启动图像测试失败: {e}", "ERROR")

    def on_signal_detected(self, signal: TradingSignal):
        """信号检测回调"""
        try:
            def update_ui():
                # 更新信号显示
                signal_text = f"{signal.action} (置信度: {signal.confidence:.2f})"

                if signal.source.value == "api_kline":
                    self.api_signal_label.config(text=signal_text)
                elif signal.source.value == "image_detection":
                    self.image_signal_label.config(text=signal_text)
                elif signal.source.value == "fusion":
                    self.fusion_signal_label.config(text=signal_text)

                # 记录日志
                self.log_message(f"🎯 检测到信号: {signal_text} - {signal.reason}")

            self.root.after(0, update_ui)

        except Exception as e:
            self.log_message(f"❌ 信号回调异常: {e}", "ERROR")

    def on_trade_executed(self, signal: TradingSignal, success: bool):
        """交易执行回调"""
        try:
            def update_ui():
                if success:
                    self.log_message(f"✅ 交易成功: {signal.action} (置信度: {signal.confidence:.2f})", "SUCCESS")
                else:
                    self.log_message(f"❌ 交易失败: {signal.action}", "ERROR")

                # 更新交易计数
                status = self.hybrid_engine.get_engine_status()
                self.trade_count_label.config(text=str(status["daily_trade_count"]))

                # 更新最后交易时间
                if status["last_trade_time"] > 0:
                    last_trade_time = time.strftime("%H:%M:%S", time.localtime(status["last_trade_time"]))
                    self.last_trade_label.config(text=last_trade_time)

            self.root.after(0, update_ui)

        except Exception as e:
            self.log_message(f"❌ 交易回调异常: {e}", "ERROR")

    def on_error_occurred(self, error_msg: str):
        """错误发生回调"""
        try:
            def update_ui():
                self.log_message(f"❌ 系统错误: {error_msg}", "ERROR")

            self.root.after(0, update_ui)

        except Exception as e:
            print(f"错误回调异常: {e}")

    def log_message(self, message: str, level: str = "INFO"):
        """记录日志消息"""
        try:
            timestamp = time.strftime("%H:%M:%S")

            # 根据级别设置颜色
            if level == "SUCCESS":
                color = "green"
            elif level == "ERROR":
                color = "red"
            elif level == "WARNING":
                color = "orange"
            else:
                color = "black"

            # 插入日志
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")

            # 自动滚动到底部
            self.log_text.see(tk.END)

            # 限制日志长度
            lines = int(self.log_text.index('end-1c').split('.')[0])
            if lines > 1000:
                self.log_text.delete('1.0', '100.0')

        except Exception as e:
            print(f"记录日志失败: {e}")

    def update_system_status(self, status: str):
        """更新系统状态"""
        try:
            self.system_status_label.config(text=status)
        except Exception as e:
            print(f"更新系统状态失败: {e}")

    def update_user_info(self):
        """更新用户信息显示"""
        try:
            if self.current_user:
                # 加载用户数据获取昵称
                try:
                    users_file = Path("config/users.json")
                    if users_file.exists():
                        with open(users_file, 'r', encoding='utf-8') as f:
                            users_data = json.load(f)

                        user_info = users_data.get("users", {}).get(self.current_user, {})
                        nickname = user_info.get("nickname", self.current_user)
                        login_count = user_info.get("login_count", 0)

                        self.user_label.config(text=f"👤 {nickname} ({self.current_user}) - 第{login_count}次登录")
                    else:
                        self.user_label.config(text=f"👤 用户: {self.current_user}")

                except Exception as e:
                    self.user_label.config(text=f"👤 用户: {self.current_user}")
            else:
                self.user_label.config(text="👤 用户: 未登录")

        except Exception as e:
            print(f"更新用户信息失败: {e}")

    def logout(self):
        """退出登录"""
        try:
            if self.is_monitoring:
                result = messagebox.askyesno(
                    "确认退出",
                    "监控正在运行中，退出登录将停止所有交易监控。\n确定要退出登录吗？"
                )

                if not result:
                    return

                # 停止监控
                self.stop_monitoring()
                time.sleep(1)

            # 记录退出日志
            self.log_message(f"👋 用户 {self.current_user} 退出登录")

            # 关闭主窗口
            self.root.destroy()

            # 重新启动登录界面
            import subprocess
            import sys
            subprocess.Popen([sys.executable, "main_fusion.py"])

        except Exception as e:
            print(f"退出登录异常: {e}")
            messagebox.showerror("退出异常", f"退出登录异常: {e}")

    def initialize_with_user(self, username: str, password: str):
        """使用用户信息初始化系统"""
        try:
            self.current_user = username
            self.user_password = password

            # 更新用户信息显示
            self.update_user_info()

            # 使用用户信息初始化混合引擎
            self.hybrid_engine.user_credentials = {
                "username": username,
                "password": password
            }

            # 记录登录日志
            self.log_message(f"👤 用户登录: {username}")
            self.log_message("🎯 智能量化交易系统已启动")
            self.log_message("🔗 多模态融合 - API + 图像识别")
            self.log_message("=" * 50)

        except Exception as e:
            print(f"用户初始化失败: {e}")
            self.log_message(f"❌ 用户初始化失败: {e}", "ERROR")

    def start_status_updates(self):
        """启动状态更新"""
        try:
            if self.status_thread and self.status_thread.is_alive():
                return

            self.status_thread = threading.Thread(target=self._status_update_loop, daemon=True)
            self.status_thread.start()

        except Exception as e:
            self.log_message(f"❌ 启动状态更新失败: {e}", "ERROR")

    def stop_status_updates(self):
        """停止状态更新"""
        try:
            # 状态更新线程会在监控停止时自动结束
            pass
        except Exception as e:
            self.log_message(f"❌ 停止状态更新失败: {e}", "ERROR")

    def _status_update_loop(self):
        """状态更新循环"""
        while self.is_monitoring:
            try:
                # 获取引擎状态
                status = self.hybrid_engine.get_engine_status()

                def update_ui():
                    try:
                        # 更新连接状态
                        api_status = "✅ 已连接" if status["api_available"] else "❌ 未连接"
                        image_status = "✅ 可用" if status["image_available"] else "❌ 不可用"
                        self.connection_status_label.config(
                            text=f"🔌 API: {api_status} | 🖼️ 图像: {image_status}"
                        )

                        # 更新交易统计
                        self.trade_count_label.config(text=str(status["daily_trade_count"]))

                        # 更新最后交易时间
                        if status["last_trade_time"] > 0:
                            last_time = time.strftime("%H:%M:%S", time.localtime(status["last_trade_time"]))
                            self.last_trade_label.config(text=last_time)

                        # 更新性能统计
                        signal_stats = status.get("signal_statistics", {})
                        if signal_stats.get("total_signals", 0) > 0:
                            api_ratio = signal_stats.get("api_ratio", 0) * 100
                            image_ratio = signal_stats.get("image_ratio", 0) * 100

                            self.api_success_label.config(text=f"{api_ratio:.1f}%")
                            self.image_success_label.config(text=f"{image_ratio:.1f}%")

                    except Exception as e:
                        print(f"UI更新异常: {e}")

                self.root.after(0, update_ui)

                time.sleep(self.update_interval)

            except Exception as e:
                print(f"状态更新循环异常: {e}")
                time.sleep(5)

    def clear_log(self):
        """清空日志"""
        try:
            self.log_text.delete('1.0', tk.END)
            self.log_message("🧹 日志已清空")
        except Exception as e:
            print(f"清空日志失败: {e}")

    def save_log(self):
        """保存日志"""
        try:
            from tkinter import filedialog

            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="保存日志文件"
            )

            if filename:
                log_content = self.log_text.get('1.0', tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)

                self.log_message(f"💾 日志已保存: {filename}", "SUCCESS")
                messagebox.showinfo("保存成功", f"日志已保存到: {filename}")

        except Exception as e:
            self.log_message(f"❌ 保存日志失败: {e}", "ERROR")
            messagebox.showerror("保存失败", f"保存日志失败: {e}")

    def on_closing(self):
        """窗口关闭事件"""
        try:
            if self.is_monitoring:
                result = messagebox.askyesno(
                    "确认退出",
                    "监控正在运行中，确定要退出吗？\n这将停止所有交易监控。"
                )

                if result:
                    self.stop_monitoring()
                    time.sleep(1)  # 等待停止完成
                    self.root.destroy()
            else:
                self.root.destroy()

        except Exception as e:
            print(f"关闭窗口异常: {e}")
            self.root.destroy()

    def run(self):
        """运行GUI"""
        try:
            self.log_message("🎯 智能量化交易系统启动")
            self.log_message("🔗 多模态融合 - API + 图像识别")
            self.log_message("=" * 50)

            # 初始化系统检查
            self.log_message("🔍 正在初始化系统组件...")

            # 启动GUI主循环
            self.root.mainloop()

        except Exception as e:
            print(f"GUI运行异常: {e}")
            messagebox.showerror("系统异常", f"GUI运行异常: {e}")

def main():
    """主函数"""
    try:
        print("🎯 启动智能量化交易系统...")

        # 创建并运行GUI
        app = HybridMainWindow()
        app.run()

    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        messagebox.showerror("启动失败", f"系统启动失败: {e}")

if __name__ == "__main__":
    main()
