#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易服务模块
集成现有的TradingAPI，提供多用户交易支持
"""

import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.trading_api import TradingAPI

logger = logging.getLogger(__name__)

class TradingService:
    """交易服务管理器"""
    
    def __init__(self):
        self.active_sessions: Dict[str, TradingAPI] = {}
        self.session_info: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_trading_session(self, user_id: str, phone: str, password: str) -> Dict[str, Any]:
        """为用户创建交易会话"""
        try:
            # 创建新的TradingAPI实例
            api = TradingAPI()
            
            # 尝试登录
            login_result = api.login(phone, password)
            
            if login_result.get("code") == "0":
                # 生成会话ID
                session_id = f"session_{user_id}_{int(time.time())}"
                
                # 保存会话信息
                self.active_sessions[session_id] = api
                self.session_info[session_id] = {
                    "user_id": user_id,
                    "phone": phone,
                    "created_at": time.time(),
                    "last_activity": time.time(),
                    "login_result": login_result
                }
                
                self.logger.info(f"用户 {user_id} 交易会话创建成功")
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "message": "登录成功",
                    "user_info": {
                        "firm_id": api.firm_id,
                        "user_id": api.user_id,
                        "user_code": api.user_code
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"登录失败: {login_result.get('message', '未知错误')}",
                    "error_code": login_result.get("code")
                }
                
        except Exception as e:
            self.logger.error(f"创建交易会话失败: {e}")
            return {
                "success": False,
                "message": f"系统错误: {str(e)}"
            }
    
    def get_session(self, session_id: str) -> Optional[TradingAPI]:
        """获取交易会话"""
        if session_id in self.active_sessions:
            # 更新最后活动时间
            self.session_info[session_id]["last_activity"] = time.time()
            return self.active_sessions[session_id]
        return None
    
    def place_order(self, session_id: str, bs_flag: str, commodity_id: str, 
                   price: str, quantity: str) -> Dict[str, Any]:
        """下单"""
        try:
            api = self.get_session(session_id)
            if not api:
                return {
                    "success": False,
                    "message": "会话无效或已过期"
                }
            
            # 执行下单
            result = api.place_order(bs_flag, commodity_id, price, quantity)
            
            if result.get("code") == "0":
                self.logger.info(f"用户下单成功: {bs_flag} {commodity_id} {price} {quantity}")
                return {
                    "success": True,
                    "message": "下单成功",
                    "order_result": result
                }
            else:
                return {
                    "success": False,
                    "message": f"下单失败: {result.get('message', '未知错误')}",
                    "error_code": result.get("code")
                }
                
        except Exception as e:
            self.logger.error(f"下单失败: {e}")
            return {
                "success": False,
                "message": f"系统错误: {str(e)}"
            }
    
    def get_positions(self, session_id: str) -> Dict[str, Any]:
        """获取持仓"""
        try:
            api = self.get_session(session_id)
            if not api:
                return {
                    "success": False,
                    "message": "会话无效或已过期"
                }
            
            result = api.get_current_positions()
            
            if result.get("code") == "0":
                return {
                    "success": True,
                    "positions": result.get("value", {}).get("content", []),
                    "total": result.get("value", {}).get("totalElements", 0)
                }
            else:
                return {
                    "success": False,
                    "message": f"获取持仓失败: {result.get('message', '未知错误')}",
                    "error_code": result.get("code")
                }
                
        except Exception as e:
            self.logger.error(f"获取持仓失败: {e}")
            return {
                "success": False,
                "message": f"系统错误: {str(e)}"
            }

# 全局交易服务实例
trading_service = TradingService() 