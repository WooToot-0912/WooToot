#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API测试脚本
测试各个API接口是否正常工作
"""

import requests
import json
import time

def test_api():
    """测试API接口"""
    base_url = "http://localhost:8081"
    
    print("景陶易购API测试")
    print("=" * 40)
    
    # 测试健康检查
    print("\n1. 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
    
    # 测试用户注册
    print("\n2. 测试用户注册...")
    test_user = {
        "username": f"testuser_{int(time.time())}",
        "phone": f"138{int(time.time()) % 100000000:08d}",
        "password": "test123456"
    }
    
    try:
        response = requests.post(f"{base_url}/api/register", json=test_user)
        if response.status_code == 201:
            print("✅ 用户注册成功")
            print(f"   用户ID: {response.json().get('user_id')}")
        else:
            print(f"❌ 用户注册失败: {response.status_code}")
            print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"❌ 用户注册异常: {e}")
    
    # 测试用户登录
    print("\n3. 测试用户登录...")
    try:
        response = requests.post(f"{base_url}/api/login", json={
            "phone": test_user["phone"],
            "password": test_user["password"]
        })
        
        if response.status_code == 200:
            print("✅ 用户登录成功")
            login_data = response.json()
            session_token = login_data.get("session_token")
            print(f"   会话令牌: {session_token[:20]}...")
            
            # 测试获取持仓
            print("\n4. 测试获取持仓...")
            headers = {"X-Session-Token": session_token}
            response = requests.get(f"{base_url}/api/trading/positions", headers=headers)
            
            if response.status_code == 200:
                print("✅ 获取持仓成功")
                positions = response.json()
                print(f"   持仓数量: {len(positions.get('positions', []))}")
            else:
                print(f"❌ 获取持仓失败: {response.status_code}")
                print(f"   响应: {response.json()}")
            
            # 测试获取商品信息
            print("\n5. 测试获取商品信息...")
            response = requests.get(f"{base_url}/api/trading/commodities", headers=headers)
            
            if response.status_code == 200:
                print("✅ 获取商品信息成功")
                commodities = response.json()
                print(f"   商品数量: {len(commodities.get('commodities', []))}")
            else:
                print(f"❌ 获取商品信息失败: {response.status_code}")
                print(f"   响应: {response.json()}")
                
        else:
            print(f"❌ 用户登录失败: {response.status_code}")
            print(f"   响应: {response.json()}")
            
    except Exception as e:
        print(f"❌ 用户登录异常: {e}")
    
    print("\n" + "=" * 40)
    print("API测试完成!")
    
    return True

if __name__ == "__main__":
    test_api() 