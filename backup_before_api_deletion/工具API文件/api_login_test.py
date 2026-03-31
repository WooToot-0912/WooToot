#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI: Test API login using config credentials for any user

Usage:
  python -m tools.api_login_test
"""

import json
import sys
from pathlib import Path

from core.trading_api import TradingAPI


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    app_cfg = project_root / "app" / "config" / "trading_config.json"
    repo_cfg = project_root / "config" / "trading_config.json"
    cfg_file = app_cfg if app_cfg.exists() else repo_cfg

    print(f"读取配置: {cfg_file}")
    try:
        conf = json.loads(cfg_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ 无法读取配置: {e}")
        return 1

    api_conf = conf.get("api", {})
    phone = api_conf.get("credentials", {}).get("phone", "")
    password_md5 = api_conf.get("credentials", {}).get("password_md5", "")
    base_url = api_conf.get("base_url", "https://zxyw.ceramic-copyright.com/apigateway")
    kline_url = api_conf.get("kline_url", "https://zxyt.ceramic-copyright.com/qtfront_tq")
    market_id = int(api_conf.get("market_id", 28))

    if not phone or not password_md5:
        print("⚠️ 请在 config/trading_config.json 的 api.credentials 中填写 phone 和 password_md5 (MD5加密后)")
        return 2

    api = TradingAPI(base_url=base_url, kline_url=kline_url)
    res = api.login(phone, password_md5, market_id)
    print("登录结果:", res)
    if res.get("code") != "0":
        return 3

    # 拉取基础数据验证
    positions = api.get_current_positions()
    print("持仓: ", positions)
    orders = api.get_current_orders()
    print("委托: ", orders)
    return 0


if __name__ == "__main__":
    sys.exit(main())

