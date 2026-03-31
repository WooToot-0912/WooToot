#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
景陶易购API客户端示例
演示如何使用共享API进行交易
"""

import requests
import json
import time

class JTYGAPIClient:
    """景陶易购API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url.rstrip("/")
        self.session_token = None
        self.user_info = None
    
    def register(self, username: str, phone: str, password: str) -> dict:
        """用户注册"""
        url = f"{self.base_url}/api/register"
        data = {
            "username": username,
            "phone": phone,
            "password": password
        }
        
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}
    
    def login(self, phone: str, password: str) -> dict:
        """用户登录"""
        url = f"{self.base_url}/api/login"
        data = {
            "phone": phone,
            "password": password
        }
        
        try:
            response = requests.post(url, json=data)
            result = response.json()
            
            if response.status_code == 200:
                self.session_token = result.get("session_token")
                self.user_info = result.get("user_info")
                print(f"登录成功! 欢迎 {self.user_info['username']}")
            
            return result
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}
    
    def place_order(self, bs_flag: str, commodity_id: str, price: str, quantity: str) -> dict:
        """下单"""
        if not self.session_token:
            return {"error": "请先登录"}
        
        url = f"{self.base_url}/api/trading/order"
        headers = {"X-Session-Token": self.session_token}
        data = {
            "bs_flag": bs_flag,
            "commodity_id": commodity_id,
            "price": price,
            "quantity": quantity
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            return response.json()
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}
    
    def get_positions(self) -> dict:
        """获取持仓"""
        if not self.session_token:
            return {"error": "请先登录"}
        
        url = f"{self.base_url}/api/trading/positions"
        headers = {"X-Session-Token": self.session_token}
        
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}
    
    def get_commodities(self) -> dict:
        """获取商品信息"""
        if not self.session_token:
            return {"error": "请先登录"}
        
        url = f"{self.base_url}/api/trading/commodities"
        headers = {"X-Session-Token": self.session_token}
        
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}
    
    def buy_order(self, commodity_id: str, price: str, quantity: str) -> dict:
        """买入下单"""
        return self.place_order("B", commodity_id, price, quantity)
    
    def sell_order(self, commodity_id: str, price: str, quantity: str) -> dict:
        """卖出下单"""
        return self.place_order("S", commodity_id, price, quantity)

def main():
    """主函数 - 演示API使用"""
    print("=== 景陶易购API客户端示例 ===")
    
    # 创建客户端
    client = JTYGAPIClient()
    
    while True:
        print("\n请选择操作:")
        print("1. 用户注册")
        print("2. 用户登录")
        print("3. 买入下单")
        print("4. 卖出下单")
        print("5. 查看持仓")
        print("6. 查看商品信息")
        print("0. 退出")
        
        choice = input("请输入选择 (0-6): ").strip()
        
        if choice == "0":
            print("再见!")
            break
        
        elif choice == "1":
            username = input("请输入用户名: ").strip()
            phone = input("请输入手机号: ").strip()
            password = input("请输入密码: ").strip()
            
            result = client.register(username, phone, password)
            print(f"注册结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        elif choice == "2":
            phone = input("请输入手机号: ").strip()
            password = input("请输入密码: ").strip()
            
            result = client.login(phone, password)
            print(f"登录结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        elif choice == "3":
            if not client.session_token:
                print("请先登录!")
                continue
            
            commodity_id = input("请输入商品ID: ").strip()
            price = input("请输入价格: ").strip()
            quantity = input("请输入数量: ").strip()
            
            result = client.buy_order(commodity_id, price, quantity)
            print(f"买入结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        elif choice == "4":
            if not client.session_token:
                print("请先登录!")
                continue
            
            commodity_id = input("请输入商品ID: ").strip()
            price = input("请输入价格: ").strip()
            quantity = input("请输入数量: ").strip()
            
            result = client.sell_order(commodity_id, price, quantity)
            print(f"卖出结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        elif choice == "5":
            if not client.session_token:
                print("请先登录!")
                continue
            
            result = client.get_positions()
            print(f"持仓信息: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        elif choice == "6":
            if not client.session_token:
                print("请先登录!")
                continue
            
            result = client.get_commodities()
            print(f"商品信息: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main() 