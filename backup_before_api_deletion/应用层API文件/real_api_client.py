#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
景陶易购真实API客户端
基于浏览器抓包获得的真实API接口
"""

import requests
import json
import hashlib
import time
import urllib3
from datetime import datetime

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RealAPIClient:
    """真实API客户端 - 基于抓包数据"""
    
    def __init__(self):
        self.base_url = "https://zxyw.ceramic-copyright.com"
        self.session = requests.Session()
        self.session.verify = False
        
        # 设置标准请求头（从抓包数据获得）
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Host': 'zxyw.ceramic-copyright.com',
            'Referer': 'https://zxyw.ceramic-copyright.com/mobile/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Sec-Ch-Ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
        
        self.session_str = None
        self.user_info = None
        self.user_id = None
        self.firm_id = None
        self.user_code = None
        
    def md5_encrypt(self, password):
        """MD5加密密码"""
        return hashlib.md5(password.encode('utf-8')).hexdigest()
    
    def login(self, phone, password):
        """
        用户登录
        使用从抓包获得的真实API接口
        """
        try:
            # 加密密码
            encrypted_password = self.md5_encrypt(password)
            
            # 登录数据（基于抓包数据）
            login_data = {
                "loginWay": 1,
                "captchaCode": "",
                "captchaId": "",
                "loginAccount": phone,
                "marketId": 28,
                "password": encrypted_password,
                "terminalType": "3",
                "type": 1
            }
            
            print(f"🔐 正在登录账号: {phone}")
            print(f"📡 请求数据: {json.dumps(login_data, ensure_ascii=False)}")
            
            # 发送登录请求
            response = self.session.post(
                f"{self.base_url}/apigateway/authn/authn/v1/frontLogin",
                json=login_data,
                timeout=30
            )
            
            print(f"📊 响应状态码: {response.status_code}")
            print(f"📋 响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 登录响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 检查登录是否成功 - 更新为正确的成功判断
                if result.get('code') == '0' or result.get('code') == 0:
                    # 提取用户信息
                    value_data = result.get('value', {})
                    self.user_info = value_data
                    self.session_str = value_data.get('sessionStr')
                    self.user_id = value_data.get('userId')
                    self.firm_id = value_data.get('firmId')
                    self.user_code = value_data.get('userCode')

                    # 更新session的认证信息
                    if self.session_str:
                        self.session.headers.update({
                            'Authorization': f'Bearer {self.session_str}',
                            'Token': self.session_str,
                            'SessionStr': self.session_str,
                            'UserId': str(self.user_id),
                            'FirmId': str(self.firm_id)
                        })

                    print(f"🎉 登录成功！")
                    print(f"👤 用户: {value_data.get('userName', '未知')}")
                    print(f"📱 手机: {value_data.get('cellphone', '未知')}")
                    print(f"🔑 会话令牌: {self.session_str}")
                    print(f"🏢 公司ID: {self.firm_id}")
                    print(f"👨‍💼 用户ID: {self.user_id}")
                    return True, result
                else:
                    print(f"❌ 登录失败: {result.get('message', '未知错误')}")
                    return False, result
            else:
                print(f"❌ HTTP请求失败: {response.status_code}")
                print(f"📄 响应内容: {response.text}")
                return False, {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ 登录异常: {str(e)}")
            return False, {"error": str(e)}

    def test_api_endpoints(self):
        """测试各种API端点"""
        print("🔍 测试API端点可用性...")

        # 可能的API端点（基于常见的交易系统API结构）
        api_endpoints = {
            "用户信息": "/apigateway/user/v1/info",
            "账户余额": "/apigateway/account/v1/balance",
            "市场列表": "/apigateway/market/v1/list",
            "商品列表": "/apigateway/commodity/v1/list",
            "交易记录": "/apigateway/trade/v1/history",
            "持仓信息": "/apigateway/position/v1/list",
            "市场行情": "/apigateway/market/v1/quotes"
        }

        results = {}

        for name, endpoint in api_endpoints.items():
            try:
                print(f"  🔍 测试 {name}: {endpoint}")
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    timeout=10
                )

                results[name] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code == 200,
                    "response_length": len(response.text)
                }

                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        results[name]["has_data"] = bool(json_data)
                        print(f"    ✅ {name} 可访问")
                    except:
                        results[name]["has_data"] = False
                        print(f"    ⚠️  {name} 可访问但非JSON格式")
                else:
                    print(f"    ❌ {name} 不可访问 (状态码: {response.status_code})")

            except Exception as e:
                results[name] = {"error": str(e)}
                print(f"    ❌ {name} 请求异常: {str(e)}")

        return results

    def get_market_data(self):
        """获取市场数据"""
        try:
            if not self.token:
                print("❌ 未登录，无法获取市场数据")
                return False, {"error": "未登录"}
            
            # 这里需要根据实际的市场数据API来调整
            # 可能的API路径（需要进一步抓包确认）
            api_paths = [
                "/apigateway/market/v1/list",
                "/apigateway/market/data/v1/list",
                "/apigateway/commodity/v1/list"
            ]
            
            for api_path in api_paths:
                try:
                    response = self.session.get(f"{self.base_url}{api_path}", timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        print(f"✅ 获取市场数据成功: {api_path}")
                        return True, result
                except:
                    continue
            
            print("❌ 所有市场数据API都失败")
            return False, {"error": "无法获取市场数据"}
            
        except Exception as e:
            print(f"❌ 获取市场数据异常: {str(e)}")
            return False, {"error": str(e)}
    
    def place_order(self, commodity_id, quantity, price, order_type="buy"):
        """下单交易"""
        try:
            if not self.token:
                print("❌ 未登录，无法下单")
                return False, {"error": "未登录"}
            
            order_data = {
                "commodityId": commodity_id,
                "quantity": quantity,
                "price": price,
                "type": order_type,
                "marketId": 28
            }
            
            print(f"📦 正在下单: {json.dumps(order_data, ensure_ascii=False)}")
            
            # 这里需要根据实际的下单API来调整
            response = self.session.post(
                f"{self.base_url}/apigateway/trade/v1/order",
                json=order_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 下单响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return True, result
            else:
                print(f"❌ 下单失败: {response.status_code}")
                return False, {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ 下单异常: {str(e)}")
            return False, {"error": str(e)}

def test_real_api():
    """测试真实API"""
    print("🚀 开始测试真实API...")
    
    client = RealAPIClient()
    
    # 测试登录（请替换为您的真实账号信息）
    phone = "17508840912"  # 从抓包数据中看到的手机号
    password = "your_password"  # 请替换为真实密码
    
    print(f"\n📱 测试账号: {phone}")
    print("⚠️  请确保密码正确，否则可能导致账号锁定")
    
    # 执行登录
    success, result = client.login(phone, password)
    
    if success:
        print("\n🎉 登录测试成功！")
        print("📊 现在可以进行其他API测试...")
        
        # 测试获取市场数据
        success, market_data = client.get_market_data()
        if success:
            print("✅ 市场数据获取成功")
        else:
            print("❌ 市场数据获取失败")
    else:
        print("\n❌ 登录测试失败")
        print("💡 请检查账号密码是否正确")

if __name__ == "__main__":
    test_real_api()
