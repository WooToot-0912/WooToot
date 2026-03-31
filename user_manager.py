#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户管理工具 - 智能量化交易系统用户管理
支持添加、删除、修改用户信息
"""

import json
import hashlib
import getpass
from pathlib import Path
from typing import Dict, Any

class UserManager:
    """用户管理器"""
    
    def __init__(self):
        """初始化用户管理器"""
        self.users_file = Path("config/users.json")
        self.ensure_config_dir()
        self.users_data = self.load_users_data()
    
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
                            "password": "327b77fa8761b11b9fd5acc3cf5466bc",  # 默认密码的MD5
                            "nickname": "鲁博",
                            "last_login": "",
                            "login_count": 0,
                            "role": "admin"
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
            print("✅ 用户数据保存成功")
        except Exception as e:
            print(f"❌ 保存用户数据失败: {e}")
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.md5(password.encode()).hexdigest()
    
    def add_user(self, phone: str, password: str, nickname: str = "", role: str = "user"):
        """添加用户"""
        try:
            if phone in self.users_data.get("users", {}):
                print(f"❌ 用户 {phone} 已存在")
                return False
            
            if "users" not in self.users_data:
                self.users_data["users"] = {}
            
            self.users_data["users"][phone] = {
                "password": self.hash_password(password),
                "nickname": nickname or phone,
                "last_login": "",
                "login_count": 0,
                "role": role
            }
            
            self.save_users_data(self.users_data)
            print(f"✅ 用户 {nickname or phone} ({phone}) 添加成功")
            return True
            
        except Exception as e:
            print(f"❌ 添加用户失败: {e}")
            return False
    
    def remove_user(self, phone: str):
        """删除用户"""
        try:
            if phone not in self.users_data.get("users", {}):
                print(f"❌ 用户 {phone} 不存在")
                return False
            
            user_info = self.users_data["users"][phone]
            nickname = user_info.get("nickname", phone)
            
            del self.users_data["users"][phone]
            self.save_users_data(self.users_data)
            
            print(f"✅ 用户 {nickname} ({phone}) 删除成功")
            return True
            
        except Exception as e:
            print(f"❌ 删除用户失败: {e}")
            return False
    
    def update_user(self, phone: str, **kwargs):
        """更新用户信息"""
        try:
            if phone not in self.users_data.get("users", {}):
                print(f"❌ 用户 {phone} 不存在")
                return False
            
            user_info = self.users_data["users"][phone]
            
            # 更新密码需要哈希
            if "password" in kwargs:
                kwargs["password"] = self.hash_password(kwargs["password"])
            
            # 更新用户信息
            user_info.update(kwargs)
            
            self.save_users_data(self.users_data)
            print(f"✅ 用户 {phone} 信息更新成功")
            return True
            
        except Exception as e:
            print(f"❌ 更新用户失败: {e}")
            return False
    
    def list_users(self):
        """列出所有用户"""
        try:
            users = self.users_data.get("users", {})
            
            if not users:
                print("📝 暂无用户")
                return
            
            print("\n📋 用户列表:")
            print("-" * 80)
            print(f"{'手机号':<15} {'昵称':<15} {'角色':<10} {'登录次数':<10} {'最后登录':<20}")
            print("-" * 80)
            
            for phone, user_info in users.items():
                nickname = user_info.get("nickname", "")
                role = user_info.get("role", "user")
                login_count = user_info.get("login_count", 0)
                last_login = user_info.get("last_login", "从未登录")
                
                print(f"{phone:<15} {nickname:<15} {role:<10} {login_count:<10} {last_login:<20}")
            
            print("-" * 80)
            print(f"总计: {len(users)} 个用户\n")
            
        except Exception as e:
            print(f"❌ 列出用户失败: {e}")
    
    def reset_password(self, phone: str):
        """重置用户密码"""
        try:
            if phone not in self.users_data.get("users", {}):
                print(f"❌ 用户 {phone} 不存在")
                return False
            
            print(f"🔑 重置用户 {phone} 的密码")
            new_password = getpass.getpass("请输入新密码: ")
            confirm_password = getpass.getpass("请确认新密码: ")
            
            if new_password != confirm_password:
                print("❌ 两次输入的密码不一致")
                return False
            
            if len(new_password) < 6:
                print("❌ 密码长度至少6位")
                return False
            
            self.users_data["users"][phone]["password"] = self.hash_password(new_password)
            self.save_users_data(self.users_data)
            
            print(f"✅ 用户 {phone} 密码重置成功")
            return True
            
        except Exception as e:
            print(f"❌ 重置密码失败: {e}")
            return False

def main():
    """主函数"""
    print("🔧 智能量化交易系统 - 用户管理工具")
    print("=" * 50)
    
    manager = UserManager()
    
    while True:
        print("\n📋 请选择操作:")
        print("1. 📝 列出所有用户")
        print("2. ➕ 添加用户")
        print("3. ❌ 删除用户")
        print("4. ✏️ 修改用户信息")
        print("5. 🔑 重置密码")
        print("0. 🚪 退出")
        
        try:
            choice = input("\n请输入选项 (0-5): ").strip()
            
            if choice == "0":
                print("👋 再见！")
                break
            elif choice == "1":
                manager.list_users()
            elif choice == "2":
                phone = input("📱 请输入手机号: ").strip()
                password = getpass.getpass("🔑 请输入密码: ")
                nickname = input("😊 请输入昵称 (可选): ").strip()
                role = input("👤 请输入角色 (admin/user，默认user): ").strip() or "user"
                
                manager.add_user(phone, password, nickname, role)
            elif choice == "3":
                phone = input("📱 请输入要删除的手机号: ").strip()
                confirm = input(f"⚠️ 确定要删除用户 {phone} 吗？(y/N): ").strip().lower()
                
                if confirm == "y":
                    manager.remove_user(phone)
                else:
                    print("❌ 操作已取消")
            elif choice == "4":
                phone = input("📱 请输入要修改的手机号: ").strip()
                
                if phone not in manager.users_data.get("users", {}):
                    print(f"❌ 用户 {phone} 不存在")
                    continue
                
                print("请输入要修改的信息 (直接回车跳过):")
                nickname = input("😊 新昵称: ").strip()
                role = input("👤 新角色 (admin/user): ").strip()
                
                updates = {}
                if nickname:
                    updates["nickname"] = nickname
                if role:
                    updates["role"] = role
                
                if updates:
                    manager.update_user(phone, **updates)
                else:
                    print("❌ 没有要更新的信息")
            elif choice == "5":
                phone = input("📱 请输入要重置密码的手机号: ").strip()
                manager.reset_password(phone)
            else:
                print("❌ 无效选项，请重新输入")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，退出程序")
            break
        except Exception as e:
            print(f"❌ 操作异常: {e}")

if __name__ == "__main__":
    main()
