#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版景陶易购交易API
基于auto_taoci-main项目的API实现，增强功能和稳定性
"""

import requests
import json
import logging
import time
import hashlib
import urllib3
from typing import Optional, Dict, Any, List, Callable
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
import threading
from dataclasses import dataclass

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class LoginCredentials:
    """登录凭证"""
    phone: str
    password: str
    market_id: int = 28

@dataclass
class OrderRequest:
    """下单请求"""
    bs_flag: str  # B-买入, S-卖出
    commodity_id: str
    price: str
    quantity: str

@dataclass
class ApiResponse:
    """API响应封装"""
    success: bool
    code: str
    message: str
    data: Any = None
    raw_response: Dict = None

class EnhancedTradingAPI:
    """增强版交易API客户端"""
    
    def __init__(self, on_connection_lost: Optional[Callable] = None):
        """
        初始化API客户端
        
        Args:
            on_connection_lost: 连接丢失回调函数
        """
        self.base_url = "https://zxyw.ceramic-copyright.com/apigateway"
        self.kline_url = "https://zxyt.ceramic-copyright.com/qtfront_tq"
        
        # 创建session并配置
        self.session = self._create_session()
        
        # 登录状态
        self.session_str = None
        self.firm_id = None
        self.user_id = None
        self.user_code = None
        self.login_time = None
        self.credentials = None
        
        # 回调函数
        self.on_connection_lost = on_connection_lost
        
        # 日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 请求头模板
        self.base_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "cn",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/json;charset=UTF-8",
            "Host": "zxyw.ceramic-copyright.com",
            "Origin": "https://zxyw.ceramic-copyright.com",
            "Pragma": "no-cache",
            "Referer": "https://zxyw.ceramic-copyright.com/client/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "terminalType": "4"
        }
        
        # 心跳检测
        self._heartbeat_thread = None
        self._heartbeat_running = False
        
    def _create_session(self) -> requests.Session:
        """创建配置好的session"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 禁用SSL验证
        session.verify = False
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """获取当前请求头"""
        headers = self.base_headers.copy()
        
        if self.session_str:
            headers.update({
                "User-Id": str(self.user_id),
                "userId": str(self.user_id),
                "firmId": str(self.firm_id),
                "marketId": "28",
                "sessionStr": self.session_str,
                "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"'
            })
        
        return headers
    
    def _make_request(self, method: str, url: str, data: Dict = None, 
                     timeout: int = 30, retry_on_auth_fail: bool = True) -> ApiResponse:
        """
        发送API请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            data: 请求数据
            timeout: 超时时间
            retry_on_auth_fail: 认证失败时是否重试
            
        Returns:
            ApiResponse: 封装的响应结果
        """
        try:
            headers = self._get_headers()
            
            if method.upper() == "POST":
                response = self.session.post(url, json=data or {}, headers=headers, timeout=timeout)
            else:
                response = self.session.get(url, headers=headers, timeout=timeout)
            
            if response.status_code != 200:
                return ApiResponse(
                    success=False,
                    code=str(response.status_code),
                    message=f"HTTP错误: {response.status_code}",
                    raw_response={"status_code": response.status_code}
                )
            
            try:
                result = response.json()
            except json.JSONDecodeError:
                return ApiResponse(
                    success=False,
                    code="-1",
                    message="响应JSON解析失败",
                    raw_response={"text": response.text[:500]}
                )
            
            # 检查业务状态码
            code = result.get("code", "-1")
            message = result.get("message", "未知错误")
            
            # 处理认证失败
            if code in ["401", "403", "10001"] and retry_on_auth_fail and self.credentials:
                self.logger.warning("检测到认证失败，尝试重新登录...")
                if self._auto_relogin():
                    # 重新发送请求
                    return self._make_request(method, url, data, timeout, False)
            
            return ApiResponse(
                success=(code == "0"),
                code=code,
                message=message,
                data=result.get("value"),
                raw_response=result
            )
            
        except requests.exceptions.Timeout:
            return ApiResponse(
                success=False,
                code="-1",
                message="请求超时"
            )
        except requests.exceptions.ConnectionError:
            return ApiResponse(
                success=False,
                code="-1",
                message="网络连接错误"
            )
        except Exception as e:
            return ApiResponse(
                success=False,
                code="-1",
                message=f"请求异常: {str(e)}"
            )
    
    def login(self, credentials: LoginCredentials) -> ApiResponse:
        """
        用户登录
        
        Args:
            credentials: 登录凭证
            
        Returns:
            ApiResponse: 登录结果
        """
        url = f"{self.base_url}/authn/authn/v1/frontLogin"
        data = {
            "captchaCode": "",
            "captchaId": "",
            "loginAccount": credentials.phone,
            "marketId": credentials.market_id,
            "terminalType": "4",
            "type": 1,
            "password": credentials.password,
            "loginWay": 1
        }
        
        response = self._make_request("POST", url, data, retry_on_auth_fail=False)
        
        if response.success and response.data:
            # 保存登录信息
            self.session_str = response.data.get("sessionStr")
            self.firm_id = response.data.get("firmId")
            self.user_id = response.data.get("userId")
            self.user_code = response.data.get("userCode")
            self.login_time = datetime.now()
            self.credentials = credentials
            
            # 启动心跳检测
            self._start_heartbeat()
            
            self.logger.info(f"✅ 登录成功: 用户ID={self.user_id}, 公司ID={self.firm_id}")
        
        return response
    
    def _auto_relogin(self) -> bool:
        """自动重新登录"""
        if not self.credentials:
            return False
        
        try:
            response = self.login(self.credentials)
            return response.success
        except Exception as e:
            self.logger.error(f"自动重新登录失败: {e}")
            return False
    
    def _start_heartbeat(self):
        """启动心跳检测"""
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        
        self._heartbeat_running = True
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
        self._heartbeat_thread.start()
    
    def _heartbeat_worker(self):
        """心跳检测工作线程"""
        while self._heartbeat_running:
            try:
                time.sleep(300)  # 5分钟检测一次
                
                if not self._heartbeat_running:
                    break
                
                # 发送心跳请求（获取账户信息）
                response = self.get_account_info()
                
                if not response.success:
                    self.logger.warning("心跳检测失败，可能需要重新登录")
                    if self.on_connection_lost:
                        self.on_connection_lost()
                
            except Exception as e:
                self.logger.error(f"心跳检测异常: {e}")
    
    def stop_heartbeat(self):
        """停止心跳检测"""
        self._heartbeat_running = False
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=1)
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return bool(self.session_str and self.user_id)
    
    def get_account_info(self) -> ApiResponse:
        """获取账户信息"""
        if not self.is_logged_in():
            return ApiResponse(False, "-1", "请先登录")

        url = f"{self.base_url}/intraday-trade-query/query/findUserInfo"
        return self._make_request("POST", url)

    # ==================== 交易相关API ====================

    def place_order(self, order: OrderRequest) -> ApiResponse:
        """
        下单

        Args:
            order: 下单请求

        Returns:
            ApiResponse: 下单结果
        """
        if not self.is_logged_in():
            return ApiResponse(False, "-1", "请先登录")

        url = f"{self.base_url}/intraday-trade/trade/make"
        data = {
            "bsFlag": order.bs_flag,
            "commodityId": order.commodity_id,
            "price": order.price,
            "quantity": order.quantity
        }

        response = self._make_request("POST", url, data)

        action = "买入" if order.bs_flag == "B" else "卖出"
        if response.success:
            self.logger.info(f"✅ {action}订单提交成功: {order.commodity_id} {order.quantity}手 @{order.price}")
        else:
            self.logger.error(f"❌ {action}订单提交失败: {response.message}")

        return response

    def buy_order(self, commodity_id: str, price: str, quantity: str) -> ApiResponse:
        """买入下单"""
        order = OrderRequest("B", commodity_id, price, quantity)
        return self.place_order(order)

    def sell_order(self, commodity_id: str, price: str, quantity: str) -> ApiResponse:
        """卖出下单"""
        order = OrderRequest("S", commodity_id, price, quantity)
        return self.place_order(order)

    def cancel_all_orders(self) -> ApiResponse:
        """全部撤单"""
        if not self.is_logged_in():
            return ApiResponse(False, "-1", "请先登录")

        url = f"{self.base_url}/intraday-trade/trade/cancelAll"
        response = self._make_request("POST", url)

        if response.success:
            self.logger.info("✅ 全部撤单成功")
        else:
            self.logger.error(f"❌ 全部撤单失败: {response.message}")

        return response

    def cancel_order(self, order_id: str) -> ApiResponse:
        """撤销指定订单"""
        if not self.is_logged_in():
            return ApiResponse(False, "-1", "请先登录")

        url = f"{self.base_url}/intraday-trade/trade/cancel"
        data = {"orderId": order_id}

        response = self._make_request("POST", url, data)

        if response.success:
            self.logger.info(f"✅ 撤单成功: {order_id}")
        else:
            self.logger.error(f"❌ 撤单失败: {response.message}")

        return response

    # ==================== 查询相关API ====================

    def get_current_orders(self, page: int = 0, size: int = 20,
                          commodity_id: Optional[str] = None) -> ApiResponse:
        """获取当前委托"""
        if not self.is_logged_in():
            return ApiResponse(False, "-1", "请先登录")

        url = f"{self.base_url}/intraday-trade-query-mongo/tradeQuery/queryOrderNewFront"
        data = {
            "page": page,
            "size": str(size),
            "bsFlag": None,
            "orderType": [1, 2, 4, 15],
            "sort": [{"direction": "DESC", "property": "orderId"}],
            "firmId": self.firm_id,
            "commodityId": commodity_id,
            "orderStatus": [1, 4]
        }

        return self._make_request("POST", url, data)

    def get_current_positions(self) -> ApiResponse:
        """获取当前持仓"""
        if not self.is_logged_in():
            return ApiResponse(False, "-1", "请先登录")

        url = f"{self.base_url}/intraday-trade-query-mongo/tradeQuery/queryHoldDetailNewList"
        data = {
            "page": 0,
            "size": "20",
            "sort": [{"direction": "DESC", "property": "holdDetailId"}]
        }

        return self._make_request("POST", url, data)

    def get_current_trades(self, page: int = 0, size: int = 20) -> ApiResponse:
        """获取当前成交记录"""
        if not self.is_logged_in():
            return ApiResponse(False, "-1", "请先登录")

        url = f"{self.base_url}/intraday-trade-query-mongo/tradeQuery/queryTradeNewList"
        data = {
            "page": page,
            "size": str(size),
            "tradeType": [1, 2, 4, 8, 15],
            "sort": [{"direction": "DESC", "property": "tradeId"}],
            "orderStatus": None
        }

        return self._make_request("POST", url, data)

    def get_commodity_strategy(self) -> ApiResponse:
        """获取商品策略（包含当前价格等信息）"""
        if not self.is_logged_in():
            return ApiResponse(False, "-1", "请先登录")

        url = f"{self.base_url}/intraday-trade-query/strategy/queryCommodityStrategy"
        return self._make_request("POST", url)

    def get_price_limit(self, commodity_id: str) -> ApiResponse:
        """获取当日涨停/跌停价格"""
        if not self.is_logged_in():
            return ApiResponse(False, "-1", "请先登录")

        url = f"{self.base_url}/intraday-trade-query/query/findCommodityHighLow"
        data = {"commodityId": commodity_id}

        return self._make_request("POST", url, data)
