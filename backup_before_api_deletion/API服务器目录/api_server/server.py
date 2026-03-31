#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
景陶易购共享API服务器
提供多用户登录和交易接口
"""

import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify, session
from flask_cors import CORS

# 导入自定义模块
from config import config
from database import UserDatabase
from trading_service import trading_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.get('logging.file', 'api_server.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.secret_key = os.urandom(24)

# 启用CORS
CORS(app, supports_credentials=True)

# 初始化数据库
db = UserDatabase(config.get('database.path'))

def require_auth(f):
    """认证装饰器"""
    def decorated_function(*args, **kwargs):
        session_token = request.headers.get('X-Session-Token')
        if not session_token:
            return jsonify({"error": "缺少会话令牌"}), 401
        
        session_info = db.validate_session(session_token)
        if not session_info:
            return jsonify({"error": "会话无效或已过期"}), 401
        
        request.user_info = session_info
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    })

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username')
        phone = data.get('phone')
        password = data.get('password')
        email = data.get('email')
        
        if not all([username, phone, password]):
            return jsonify({"error": "缺少必要参数"}), 400
        
        # 创建用户
        if db.create_user(username, phone, password, email):
            return jsonify({"message": "注册成功"}), 201
        else:
            return jsonify({"error": "用户已存在"}), 409
            
    except Exception as e:
        logger.error(f"注册失败: {e}")
        return jsonify({"error": "注册失败"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        password = data.get('password')
        
        if not all([phone, password]):
            return jsonify({"error": "缺少必要参数"}), 400
        
        # 验证用户
        user = db.authenticate_user(phone, password)
        if not user:
            return jsonify({"error": "用户名或密码错误"}), 401
        
        # 创建交易会话
        trading_result = trading_service.create_trading_session(
            str(user['id']), phone, password
        )
        
        if not trading_result['success']:
            return jsonify({"error": trading_result['message']}), 500
        
        # 创建API会话
        session_token = db.create_session(
            user['id'],
            trading_result['session_id'],
            trading_result['user_info'].get('firm_id'),
            trading_result['user_info'].get('user_id')
        )
        
        if not session_token:
            return jsonify({"error": "创建会话失败"}), 500
        
        return jsonify({
            "message": "登录成功",
            "session_token": session_token,
            "user_info": {
                "username": user['username'],
                "phone": user['phone'],
                "email": user['email'],
                "permissions": user['permissions']
            },
            "trading_session": trading_result['session_id']
        }), 200
        
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return jsonify({"error": "登录失败"}), 500

@app.route('/api/trading/order', methods=['POST'])
@require_auth
def place_order():
    """下单"""
    try:
        data = request.get_json()
        bs_flag = data.get('bs_flag')
        commodity_id = data.get('commodity_id')
        price = data.get('price')
        quantity = data.get('quantity')
        
        if not all([bs_flag, commodity_id, price, quantity]):
            return jsonify({"error": "缺少必要参数"}), 400
        
        # 获取用户的交易会话
        session_token = request.headers.get('X-Session-Token')
        session_info = db.validate_session(session_token)
        trading_session = session_info.get('trading_session')
        
        # 执行下单
        result = trading_service.place_order(
            trading_session, bs_flag, commodity_id, price, quantity
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"下单失败: {e}")
        return jsonify({"error": "下单失败"}), 500

@app.route('/api/trading/positions', methods=['GET'])
@require_auth
def get_positions():
    """获取持仓"""
    try:
        session_token = request.headers.get('X-Session-Token')
        session_info = db.validate_session(session_token)
        trading_session = session_info.get('trading_session')
        
        result = trading_service.get_positions(trading_session)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        return jsonify({"error": "获取持仓失败"}), 500

if __name__ == '__main__':
    # 创建必要的目录
    os.makedirs(os.path.dirname(config.get('logging.file')), exist_ok=True)
    os.makedirs(os.path.dirname(config.get('database.path')), exist_ok=True)
    
    # 启动服务器
    host = config.get('server.host', '0.0.0.0')
    port = config.get('server.port', 8080)
    debug = config.get('server.debug', False)
    
    logger.info(f"启动API服务器: {host}:{port}")
    app.run(host=host, port=port, debug=debug) 