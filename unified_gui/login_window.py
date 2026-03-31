#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
登录窗口 - 智能量化交易系统用户登录界面
支持多用户登录，账号管理和自动登录功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import hashlib
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Callable

class LoginWindow:
    """登录窗口"""
    
    def __init__(self, on_login_success: Callable[[str, str], None]):
        """
        初始化登录窗口
        
        Args:
            on_login_success: 登录成功回调函数，参数为(username, password)
        """
        self.on_login_success = on_login_success
        
        # 创建登录窗口
        self.root = tk.Tk()
        self.root.title("🔐 智能量化交易系统 - 用户登录")
        self.root.geometry("450x600")
        self.root.resizable(False, False)
        
        # 居中显示
        self.center_window()
        
        # 用户数据文件
        self.users_file = Path("config/users.json")
        self.ensure_config_dir()
        
        # 加载用户数据
        self.users_data = self.load_users_data()
        
        # 创建界面
        self.create_widgets()
        self.setup_layout()
        
        # 加载保存的登录信息
        self.load_saved_login()
        
        print("✅ 登录窗口初始化完成")
    
    def center_window(self):
        """窗口居中"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def ensure_config_dir(self):
        """确保配置目录存在"""
        config_dir = Path("config")
        if not config_dir.exists():
            config_dir.mkdir()
    
    def load_users_data(self) -> Dict:
        """加载用户数据"""
        try:
            if self.users_file.exists():
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 创建默认用户数据
                default_users = {
                    "users": {
                        "17508840912": {
                            "password": "327b77fa8761b11b9fd5acc3cf5466bc",
                            "nickname": "鲁博",
                            "last_login": "",
                            "login_count": 0
                        }
                    },
                    "settings": {
                        "remember_login": True,
                        "auto_login": False,
                        "last_user": ""
                    }
                }
                
                self.save_users_data(default_users)
                return default_users
                
        except Exception as e:
            print(f"❌ 加载用户数据失败: {e}")
            return {"users": {}, "settings": {}}
    
    def save_users_data(self, data: Dict):
        """保存用户数据"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 保存用户数据失败: {e}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 主标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=20)
        
        title_label = ttk.Label(
            title_frame,
            text="🎯 智能量化交易系统",
            font=('Arial', 16, 'bold')
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="🔗 多模态融合 - API + 图像识别",
            font=('Arial', 10)
        )
        subtitle_label.pack(pady=5)
        
        # 登录表单
        login_frame = ttk.LabelFrame(self.root, text="🔐 用户登录", padding=20)
        login_frame.pack(pady=20, padx=40, fill=tk.X)
        
        # 用户名
        username_frame = ttk.Frame(login_frame)
        username_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(username_frame, text="📱 手机号:", width=10).pack(side=tk.LEFT)
        self.username_var = tk.StringVar()
        self.username_combo = ttk.Combobox(
            username_frame,
            textvariable=self.username_var,
            width=25,
            values=list(self.users_data.get("users", {}).keys())
        )
        self.username_combo.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.username_combo.bind('<<ComboboxSelected>>', self.on_username_selected)
        
        # 密码
        password_frame = ttk.Frame(login_frame)
        password_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(password_frame, text="🔑 密码:", width=10).pack(side=tk.LEFT)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(
            password_frame,
            textvariable=self.password_var,
            show="*",
            width=25
        )
        self.password_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # 显示/隐藏密码
        self.show_password_var = tk.BooleanVar()
        show_password_check = ttk.Checkbutton(
            password_frame,
            text="👁️",
            variable=self.show_password_var,
            command=self.toggle_password_visibility
        )
        show_password_check.pack(side=tk.RIGHT, padx=5)
        
        # 记住登录
        options_frame = ttk.Frame(login_frame)
        options_frame.pack(fill=tk.X, pady=10)
        
        self.remember_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="💾 记住登录信息",
            variable=self.remember_var
        ).pack(side=tk.LEFT)
        
        self.auto_login_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame,
            text="🚀 自动登录",
            variable=self.auto_login_var
        ).pack(side=tk.RIGHT)
        
        # 登录按钮
        button_frame = ttk.Frame(login_frame)
        button_frame.pack(fill=tk.X, pady=15)
        
        self.login_button = ttk.Button(
            button_frame,
            text="🚀 登录系统",
            command=self.login,
            style='Accent.TButton'
        )
        self.login_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="👤 新用户注册",
            command=self.show_register_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="🔧 管理账号",
            command=self.show_manage_dialog
        ).pack(side=tk.RIGHT, padx=5)
        
        # 快速登录
        quick_frame = ttk.LabelFrame(self.root, text="⚡ 快速登录", padding=15)
        quick_frame.pack(pady=10, padx=40, fill=tk.X)
        
        # 显示已保存的用户
        self.create_quick_login_buttons(quick_frame)
        
        # 状态显示
        self.status_label = ttk.Label(
            self.root,
            text="🔴 请输入登录信息",
            font=('Arial', 9)
        )
        self.status_label.pack(pady=10)
        
        # 绑定回车键登录
        self.root.bind('<Return>', lambda e: self.login())
    
    def create_quick_login_buttons(self, parent):
        """创建快速登录按钮"""
        users = self.users_data.get("users", {})
        
        if users:
            for username, user_info in users.items():
                nickname = user_info.get("nickname", username)
                login_count = user_info.get("login_count", 0)
                
                button_text = f"👤 {nickname} ({username}) - 登录{login_count}次"
                
                ttk.Button(
                    parent,
                    text=button_text,
                    command=lambda u=username: self.quick_login(u)
                ).pack(fill=tk.X, pady=2)
        else:
            ttk.Label(parent, text="暂无保存的用户").pack()
    
    def setup_layout(self):
        """设置布局"""
        pass  # 布局已在create_widgets中完成
    
    def on_username_selected(self, event):
        """用户名选择事件"""
        username = self.username_var.get()
        if username in self.users_data.get("users", {}):
            # 自动填充密码
            user_info = self.users_data["users"][username]
            self.password_var.set(user_info.get("password", ""))
            self.status_label.config(text=f"👤 已选择用户: {user_info.get('nickname', username)}")
    
    def toggle_password_visibility(self):
        """切换密码显示/隐藏"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def quick_login(self, username: str):
        """快速登录"""
        try:
            if username in self.users_data.get("users", {}):
                user_info = self.users_data["users"][username]
                self.username_var.set(username)
                self.password_var.set(user_info.get("password", ""))
                self.login()
        except Exception as e:
            messagebox.showerror("快速登录失败", f"快速登录失败: {e}")
    
    def login(self):
        """执行登录"""
        try:
            username = self.username_var.get().strip()
            password = self.password_var.get().strip()
            
            if not username or not password:
                messagebox.showerror("输入错误", "请输入完整的登录信息")
                return
            
            # 更新状态
            self.status_label.config(text="🔄 正在验证登录...")
            self.login_button.config(state=tk.DISABLED, text="🔄 登录中...")
            
            # 在后台线程中执行登录
            threading.Thread(target=self._perform_login, args=(username, password), daemon=True).start()
            
        except Exception as e:
            self.reset_login_button()
            messagebox.showerror("登录异常", f"登录过程异常: {e}")
    
    def _perform_login(self, username: str, password: str):
        """执行登录验证"""
        try:
            # 这里可以添加实际的API登录验证
            # 目前使用简化验证
            login_success = True  # 假设登录成功
            
            def update_ui():
                if login_success:
                    # 保存登录信息
                    if self.remember_var.get():
                        self.save_login_info(username, password)
                    
                    # 更新用户登录统计
                    self.update_user_stats(username, password)
                    
                    self.status_label.config(text="✅ 登录成功，正在启动系统...")
                    
                    # 延迟关闭登录窗口并启动主系统
                    self.root.after(1000, lambda: self.complete_login(username, password))
                    
                else:
                    self.status_label.config(text="❌ 登录失败，请检查账号密码")
                    self.reset_login_button()
                    messagebox.showerror("登录失败", "账号或密码错误，请重新输入")
            
            self.root.after(0, update_ui)
            
        except Exception as e:
            def update_ui():
                self.status_label.config(text="❌ 登录异常")
                self.reset_login_button()
                messagebox.showerror("登录异常", f"登录验证异常: {e}")
            
            self.root.after(0, update_ui)
    
    def save_login_info(self, username: str, password: str):
        """保存登录信息"""
        try:
            # 更新用户数据
            if "users" not in self.users_data:
                self.users_data["users"] = {}
            
            if username not in self.users_data["users"]:
                self.users_data["users"][username] = {
                    "password": password,
                    "nickname": username,
                    "last_login": "",
                    "login_count": 0
                }
            else:
                self.users_data["users"][username]["password"] = password
            
            # 更新设置
            if "settings" not in self.users_data:
                self.users_data["settings"] = {}
            
            self.users_data["settings"]["remember_login"] = self.remember_var.get()
            self.users_data["settings"]["auto_login"] = self.auto_login_var.get()
            self.users_data["settings"]["last_user"] = username
            
            # 保存到文件
            self.save_users_data(self.users_data)
            
        except Exception as e:
            print(f"❌ 保存登录信息失败: {e}")
    
    def update_user_stats(self, username: str, password: str):
        """更新用户统计"""
        try:
            import time
            
            if username in self.users_data.get("users", {}):
                user_info = self.users_data["users"][username]
                user_info["last_login"] = time.strftime("%Y-%m-%d %H:%M:%S")
                user_info["login_count"] = user_info.get("login_count", 0) + 1
                
                self.save_users_data(self.users_data)
                
        except Exception as e:
            print(f"❌ 更新用户统计失败: {e}")
    
    def load_saved_login(self):
        """加载保存的登录信息"""
        try:
            settings = self.users_data.get("settings", {})
            
            if settings.get("remember_login", False):
                last_user = settings.get("last_user", "")
                if last_user and last_user in self.users_data.get("users", {}):
                    user_info = self.users_data["users"][last_user]
                    
                    self.username_var.set(last_user)
                    self.password_var.set(user_info.get("password", ""))
                    self.remember_var.set(True)
                    self.auto_login_var.set(settings.get("auto_login", False))
                    
                    # 如果启用自动登录
                    if settings.get("auto_login", False):
                        self.root.after(2000, self.login)  # 2秒后自动登录
                        self.status_label.config(text="🚀 自动登录已启用，2秒后自动登录...")
            
        except Exception as e:
            print(f"❌ 加载保存的登录信息失败: {e}")
    
    def show_register_dialog(self):
        """显示注册对话框"""
        try:
            register_window = tk.Toplevel(self.root)
            register_window.title("👤 新用户注册")
            register_window.geometry("400x300")
            register_window.resizable(False, False)
            
            # 居中显示
            register_window.transient(self.root)
            register_window.grab_set()
            
            # 注册表单
            ttk.Label(register_window, text="👤 新用户注册", font=('Arial', 14, 'bold')).pack(pady=10)
            
            # 手机号
            phone_frame = ttk.Frame(register_window)
            phone_frame.pack(fill=tk.X, padx=20, pady=5)
            ttk.Label(phone_frame, text="📱 手机号:", width=10).pack(side=tk.LEFT)
            phone_var = tk.StringVar()
            ttk.Entry(phone_frame, textvariable=phone_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            
            # 密码
            pwd_frame = ttk.Frame(register_window)
            pwd_frame.pack(fill=tk.X, padx=20, pady=5)
            ttk.Label(pwd_frame, text="🔑 密码:", width=10).pack(side=tk.LEFT)
            pwd_var = tk.StringVar()
            ttk.Entry(pwd_frame, textvariable=pwd_var, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            
            # 昵称
            nick_frame = ttk.Frame(register_window)
            nick_frame.pack(fill=tk.X, padx=20, pady=5)
            ttk.Label(nick_frame, text="😊 昵称:", width=10).pack(side=tk.LEFT)
            nick_var = tk.StringVar()
            ttk.Entry(nick_frame, textvariable=nick_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            
            # 注册按钮
            def register_user():
                phone = phone_var.get().strip()
                password = pwd_var.get().strip()
                nickname = nick_var.get().strip() or phone
                
                if not phone or not password:
                    messagebox.showerror("输入错误", "请输入完整信息")
                    return
                
                # 添加新用户
                if "users" not in self.users_data:
                    self.users_data["users"] = {}
                
                self.users_data["users"][phone] = {
                    "password": password,
                    "nickname": nickname,
                    "last_login": "",
                    "login_count": 0
                }
                
                self.save_users_data(self.users_data)
                
                # 更新用户名下拉框
                self.username_combo['values'] = list(self.users_data["users"].keys())
                
                messagebox.showinfo("注册成功", f"用户 {nickname} 注册成功！")
                register_window.destroy()
            
            ttk.Button(register_window, text="✅ 注册", command=register_user).pack(pady=20)
            
        except Exception as e:
            messagebox.showerror("注册异常", f"显示注册对话框失败: {e}")
    
    def show_manage_dialog(self):
        """显示账号管理对话框"""
        try:
            manage_window = tk.Toplevel(self.root)
            manage_window.title("🔧 账号管理")
            manage_window.geometry("500x400")
            
            # 居中显示
            manage_window.transient(self.root)
            manage_window.grab_set()
            
            ttk.Label(manage_window, text="🔧 账号管理", font=('Arial', 14, 'bold')).pack(pady=10)
            
            # 用户列表
            list_frame = ttk.Frame(manage_window)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # 创建表格
            columns = ("手机号", "昵称", "最后登录", "登录次数")
            tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            
            # 填充数据
            users = self.users_data.get("users", {})
            for username, user_info in users.items():
                tree.insert('', 'end', values=(
                    username,
                    user_info.get("nickname", ""),
                    user_info.get("last_login", "从未登录"),
                    user_info.get("login_count", 0)
                ))
            
            tree.pack(fill=tk.BOTH, expand=True)
            
            # 管理按钮
            button_frame = ttk.Frame(manage_window)
            button_frame.pack(fill=tk.X, padx=20, pady=10)
            
            def delete_user():
                selection = tree.selection()
                if selection:
                    item = tree.item(selection[0])
                    username = item['values'][0]
                    
                    result = messagebox.askyesno("确认删除", f"确定要删除用户 {username} 吗？")
                    if result:
                        del self.users_data["users"][username]
                        self.save_users_data(self.users_data)
                        tree.delete(selection[0])
                        
                        # 更新主窗口下拉框
                        self.username_combo['values'] = list(self.users_data["users"].keys())
                        
                        messagebox.showinfo("删除成功", f"用户 {username} 已删除")
            
            ttk.Button(button_frame, text="🗑️ 删除用户", command=delete_user).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="✅ 关闭", command=manage_window.destroy).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("管理异常", f"显示账号管理失败: {e}")
    
    def reset_login_button(self):
        """重置登录按钮"""
        self.login_button.config(state=tk.NORMAL, text="🚀 登录系统")
    
    def complete_login(self, username: str, password: str):
        """完成登录"""
        try:
            # 关闭登录窗口
            self.root.destroy()
            
            # 调用登录成功回调
            self.on_login_success(username, password)
            
        except Exception as e:
            print(f"❌ 完成登录失败: {e}")
    
    def run(self):
        """运行登录窗口"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"❌ 登录窗口运行异常: {e}")

def main():
    """测试登录窗口"""
    def on_success(username, password):
        print(f"✅ 登录成功: {username}")
    
    login_window = LoginWindow(on_success)
    login_window.run()

if __name__ == "__main__":
    main()
