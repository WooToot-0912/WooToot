#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API服务器配置文件
"""

import os
from pathlib import Path
from typing import Dict, Any

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 默认配置
DEFAULT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8080,
        "debug": False,
        "workers": 4,
        "max_connections": 1000,
        "timeout": 30
    },
    "security": {
        "enable_rate_limit": True,
        "max_requests_per_minute": 100,
        "enable_api_key": True,
        "session_timeout": 3600,  # 1小时
        "max_concurrent_sessions": 10
    },
    "database": {
        "type": "sqlite",
        "path": str(PROJECT_ROOT / "api_server" / "data" / "users.db"),
        "backup_enabled": True,
        "backup_interval": 86400  # 24小时
    },
    "logging": {
        "level": "INFO",
        "file": str(PROJECT_ROOT / "api_server" / "logs" / "api_server.log"),
        "max_size": 10485760,  # 10MB
        "backup_count": 5
    },
    "trading": {
        "base_url": "https://zxyw.ceramic-copyright.com/apigateway",
        "kline_url": "https://zxyt.ceramic-copyright.com/qtfront_tq",
        "market_id": 28,
        "max_order_amount": 100000,  # 最大下单金额
        "enable_risk_control": True,
        "daily_loss_limit": 1000,  # 日亏损限制
        "max_daily_trades": 100
    }
}

class APIServerConfig:
    """API服务器配置管理器"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or str(PROJECT_ROOT / "api_server" / "config" / "server_config.json")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                import json
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 创建默认配置文件
                self._create_default_config()
                return DEFAULT_CONFIG
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return DEFAULT_CONFIG
    
    def _create_default_config(self):
        """创建默认配置文件"""
        try:
            config_dir = os.path.dirname(self.config_file)
            os.makedirs(config_dir, exist_ok=True)
            
            import json
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            print(f"已创建默认配置文件: {self.config_file}")
        except Exception as e:
            print(f"创建配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """保存配置到文件"""
        try:
            import json
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

# 全局配置实例
config = APIServerConfig() 