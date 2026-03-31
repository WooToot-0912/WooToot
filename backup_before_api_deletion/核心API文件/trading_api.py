#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP Trading API Client for JTYG (景陶易购)

Purpose
- Provide multi-user API login and trading endpoints for the 自动交易系统 project
- Credentials and endpoints are read from the config manager (EnhancedConfigManager)

Notes
- This client builds request headers dynamically after successful login
- Do not hardcode session tokens or user ids; they are set from login response
- Keep this module UI-agnostic; it can be used by GUI/tools/engine
"""

from __future__ import annotations

import hashlib
import logging
from typing import Optional, Dict, Any, List

import requests


class TradingAPI:
    """交易API客户端（多用户）"""

    def __init__(self,
                 base_url: str = "https://zxyw.ceramic-copyright.com/apigateway",
                 kline_url: str = "https://zxyt.ceramic-copyright.com/qtfront_tq",
                 session: Optional[requests.Session] = None):
        self.logger = logging.getLogger(__name__)
        self.base_url = base_url.rstrip("/")
        self.kline_url = kline_url.rstrip("/")
        self.session = session or requests.Session()

        # 登录后动态设置
        self.session_str: Optional[str] = None
        self.firm_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.user_code: Optional[str] = None
        self.market_id: str = "28"
        self._headers: Dict[str, str] = {}

    # --------------- Utilities ---------------
    @staticmethod
    def md5_hex(plain_text: str) -> str:
        return hashlib.md5(plain_text.encode("utf-8")).hexdigest()

    def _require_login(self) -> None:
        if not self.session_str:
            raise RuntimeError("未登录：请先调用 login() 获取 sessionStr")

    def _build_headers(self) -> Dict[str, str]:
        """构建通用请求头（需在登录后调用）"""
        if not self.session_str:
            return {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json;charset=UTF-8",
                "User-Agent": "Mozilla/5.0"
            }

        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "cn",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://zxyw.ceramic-copyright.com",
            "Pragma": "no-cache",
            "Referer": "https://zxyw.ceramic-copyright.com/client/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36",
            "terminalType": "4",
            # 动态标识
            "sessionStr": self.session_str or "",
            "userId": str(self.user_id or ""),
            "User-Id": str(self.user_id or ""),
            "firmId": str(self.firm_id or ""),
            "marketId": str(self.market_id or "28"),
        }

    # --------------- Auth ---------------
    def login(self, phone: str, password_md5: str, market_id: int = 28) -> Dict[str, Any]:
        """
        用户登录
        - password_md5: 明文的MD5 32位十六进制
        返回后会设置 sessionStr/firmId/userId 等内部状态
        """
        url = f"{self.base_url}/authn/authn/v1/frontLogin"
        data = {
            "captchaCode": "",
            "captchaId": "",
            "loginAccount": phone,
            "marketId": market_id,
            "terminalType": "4",
            "type": 1,
            "password": password_md5,
            "loginWay": 1
        }
        try:
            response = self.session.post(url, json=data, headers=self._build_headers(), timeout=15)
            result = response.json()

            if result.get("code") == "0" and "value" in result:
                value = result["value"]
                self.session_str = value.get("sessionStr")
                self.firm_id = value.get("firmId")
                self.user_id = value.get("userId")
                self.user_code = value.get("userCode")
                self.market_id = str(market_id)
                self._headers = self._build_headers()
                self.logger.info("API登录成功: userId=%s firmId=%s", self.user_id, self.firm_id)
            else:
                self.logger.warning("登录失败: %s", result.get("message", "未知错误"))
            return result
        except Exception as e:
            self.logger.error("登录请求异常: %s", e)
            return {"code": "-1", "message": f"请求异常: {str(e)}"}

    # --------------- Queries ---------------
    def get_current_orders(self, page: int = 0, size: int = 6, commodity_id: Optional[str] = None) -> Dict[str, Any]:
        self._require_login()
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
        try:
            r = self.session.post(url, json=data, headers=self._headers, timeout=15)
            return r.json()
        except Exception as e:
            return {"code": "-1", "message": f"请求异常: {str(e)}"}

    def get_current_positions(self) -> Dict[str, Any]:
        self._require_login()
        url = f"{self.base_url}/intraday-trade-query-mongo/tradeQuery/queryHoldDetailNewList"
        data = {
            "page": 0,
            "size": "50",
            "sort": [{"direction": "DESC", "property": "holdDetailId"}]
        }
        try:
            r = self.session.post(url, json=data, headers=self._headers, timeout=15)
            return r.json()
        except Exception as e:
            return {"code": "-1", "message": f"请求异常: {str(e)}"}

    def get_current_trades(self,
                           page: int = 0,
                           size: int = 20,
                           commodity_id: Optional[int] = None,
                           bs_flag: Optional[str] = None,
                           trade_day: Optional[str] = None,
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None) -> Dict[str, Any]:
        self._require_login()
        url = f"{self.base_url}/intraday-trade-query-mongo/tradeQuery/queryTradeNewList"
        data = {
            "page": page,
            "size": str(size),
            "tradeType": [1, 2, 4, 8, 15],
            "sort": [{"direction": "DESC", "property": "tradeId"}],
            "commodityId": commodity_id,
            "bsFlag": bs_flag,
            "orderStatus": None
        }
        try:
            r = self.session.post(url, json=data, headers=self._headers, timeout=15)
            result = r.json()
            # 选填时间二次过滤（仅客户端侧）
            if result.get("code") == "0" and (trade_day or start_time or end_time):
                content = result.get("value", {}).get("content", [])
                filtered = []
                for t in content:
                    create_time = t.get("createTime")
                    if trade_day and t.get("tradeDay") != int(trade_day):
                        continue
                    if start_time and create_time and create_time < start_time:
                        continue
                    if end_time and create_time and create_time > end_time:
                        continue
                    filtered.append(t)
                if "value" in result:
                    result["value"]["content"] = filtered
                    result["value"]["totalElements"] = len(filtered)
                    result["value"]["size"] = len(filtered)
            return result
        except Exception as e:
            return {"code": "-1", "message": f"请求异常: {str(e)}"}

    # --------------- Trading ---------------
    def place_order(self, bs_flag: str, commodity_id: str, price: str, quantity: str) -> Dict[str, Any]:
        self._require_login()
        url = f"{self.base_url}/intraday-trade-biz/trade/entrust"
        data = {
            "bsFlag": bs_flag,  # 'B' 买入, 'S' 卖出
            "firmId": self.firm_id,
            "orderType": 1,
            "price": price,
            "commodityId": commodity_id,
            "quantity": quantity,
            "tradeWay": 1
        }
        try:
            r = self.session.post(url, json=data, headers=self._headers, timeout=15)
            return r.json()
        except Exception as e:
            return {"code": "-1", "message": f"请求异常: {str(e)}"}

    def buy_order(self, commodity_id: str, price: str, quantity: str) -> Dict[str, Any]:
        return self.place_order("B", commodity_id, price, quantity)

    def sell_order(self, commodity_id: str, price: str, quantity: str) -> Dict[str, Any]:
        return self.place_order("S", commodity_id, price, quantity)

    def cancel_all_orders(self) -> Dict[str, Any]:
        self._require_login()
        url = f"{self.base_url}/intraday-trade-biz/trade/cancelAll"
        data: Dict[str, Any] = {}
        try:
            r = self.session.post(url, json=data, headers=self._headers, timeout=15)
            return r.json()
        except Exception as e:
            return {"code": "-1", "message": f"请求异常: {str(e)}"}


# 便捷运行：允许作为脚本测试登录
if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    # 尝试读取项目配置
    project_root = Path(__file__).resolve().parents[1]
    app_config_path = project_root / "app" / "config" / "trading_config.json"
    repo_config_path = project_root / "config" / "trading_config.json"
    cfg_file = app_config_path if app_config_path.exists() else repo_config_path

    print(f"读取配置: {cfg_file}")
    conf = {}
    try:
        with open(cfg_file, "r", encoding="utf-8") as f:
            conf = json.load(f)
    except Exception as e:
        print(f"无法读取配置: {e}")

    api_conf = conf.get("api", {}) if isinstance(conf, dict) else {}
    phone = api_conf.get("credentials", {}).get("phone", "")
    password_md5 = api_conf.get("credentials", {}).get("password_md5", "")
    base_url = api_conf.get("base_url", "https://zxyw.ceramic-copyright.com/apigateway")
    kline_url = api_conf.get("kline_url", "https://zxyt.ceramic-copyright.com/qtfront_tq")
    market_id = int(api_conf.get("market_id", 28))

    if not phone or not password_md5:
        print("请在 config/trading_config.json 的 api.credentials 中填写 phone 和 password_md5")
        sys.exit(1)

    api = TradingAPI(base_url=base_url, kline_url=kline_url)
    res = api.login(phone, password_md5, market_id)
    print("登录结果:", res)
    if res.get("code") == "0":
        pos = api.get_current_positions()
        print("持仓:", pos)

