#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
景陶易购共享API服务器 - 简化版
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.trading_api import TradingAPI

app = Flask(__name__)
CORS(app)

# 存储用户会话
user_sessions = {}
user_credentials = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    phone = data.get('phone')
    password = data.get('password')
    
    if not all([username, phone, password]):
        return jsonify({"error": "缺少必要参数"}), 400
    
    # 简单的用户存储（实际应该用数据库）
    user_id = hashlib.md5(f"{username}{phone}".encode()).hexdigest()
    user_credentials[user_id] = {
        "username": username,
        "phone": phone,
        "password": password
    }
    
    return jsonify({"message": "注册成功", "user_id": user_id}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    
    if not all([phone, password]):
        return jsonify({"error": "缺少必要参数"}), 400
    
    # 查找用户
    user_id = None
    for uid, user in user_credentials.items():
        if user['phone'] == phone and user['password'] == password:
            user_id = uid
            break
    
    if not user_id:
        return jsonify({"error": "用户名或密码错误"}), 401
    
    # 创建交易API实例并登录
    try:
        api = TradingAPI()
        login_result = api.login(phone, password)
        
        if login_result.get("code") == "0":
            # 生成会话令牌
            session_token = hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()
            
            # 保存会话
            user_sessions[session_token] = {
                "user_id": user_id,
                "api": api,
                "created_at": time.time()
            }
            
            return jsonify({
                "message": "登录成功",
                "session_token": session_token,
                "user_info": {
                    "username": user_credentials[user_id]['username'],
                    "phone": phone
                }
            }), 200
        else:
            return jsonify({"error": f"登录失败: {login_result.get('message')}"}), 400
            
    except Exception as e:
        return jsonify({"error": f"系统错误: {str(e)}"}), 500

@app.route('/api/trading/order', methods=['POST'])
def place_order():
    session_token = request.headers.get('X-Session-Token')
    if not session_token or session_token not in user_sessions:
        return jsonify({"error": "会话无效"}), 401
    
    data = request.get_json()
    bs_flag = data.get('bs_flag')
    commodity_id = data.get('commodity_id')
    price = data.get('price')
    quantity = data.get('quantity')
    
    if not all([bs_flag, commodity_id, price, quantity]):
        return jsonify({"error": "缺少必要参数"}), 400
    
    try:
        session_info = user_sessions[session_token]
        api = session_info['api']
        
        result = api.place_order(bs_flag, commodity_id, price, quantity)
        
        if result.get("code") == "0":
            return jsonify({"success": True, "message": "下单成功"}), 200
        else:
            return jsonify({"success": False, "error": result.get("message")}), 400
            
    except Exception as e:
        return jsonify({"error": f"下单失败: {str(e)}"}), 500

@app.route('/api/trading/positions', methods=['GET'])
def get_positions():
    session_token = request.headers.get('X-Session-Token')
    if not session_token or session_token not in user_sessions:
        return jsonify({"error": "会话无效"}), 401
    
    try:
        session_info = user_sessions[session_token]
        api = session_info['api']
        
        result = api.get_current_positions()
        
        if result.get("code") == "0":
            return jsonify({
                "success": True,
                "positions": result.get("value", {}).get("content", [])
            }), 200
        else:
            return jsonify({"success": False, "error": result.get("message")}), 400
            
    except Exception as e:
        return jsonify({"error": f"获取持仓失败: {str(e)}"}), 500

@app.route('/api/trading/commodities', methods=['GET'])
def get_commodities():
    session_token = request.headers.get('X-Session-Token')
    if not session_token or session_token not in user_sessions:
        return jsonify({"error": "会话无效"}), 401
    
    try:
        session_info = user_sessions[session_token]
        api = session_info['api']
        
        result = api.get_commodity_strategy()
        
        if result.get("code") == "0":
            return jsonify({
                "success": True,
                "commodities": result.get("value", [])
            }), 200
        else:
            return jsonify({"success": False, "error": result.get("message")}), 400
            
    except Exception as e:
        return jsonify({"error": f"获取商品信息失败: {str(e)}"}), 500

if __name__ == '__main__':
    print("启动景陶易购共享API服务器...")
    print("服务器地址: http://localhost:8081")
    print("API文档:")
    print("  POST /api/register - 用户注册")
    print("  POST /api/login - 用户登录")
    print("  POST /api/trading/order - 下单")
    print("  GET  /api/trading/positions - 获取持仓")
    print("  GET  /api/trading/commodities - 获取商品信息")
    
    app.run(host='127.0.0.1', port=8081, debug=True) 