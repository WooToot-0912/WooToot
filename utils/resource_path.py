#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源路径处理模块
用于处理打包后的资源文件路径问题
"""

import os
import sys
from pathlib import Path

def get_resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径
    
    Args:
        relative_path: 相对路径
        
    Returns:
        str: 绝对路径
    """
    try:
        # PyInstaller打包后的临时目录
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境下的当前目录
        base_path = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(base_path)  # 回到项目根目录
    
    return os.path.join(base_path, relative_path)

def get_config_path(config_name: str = "trading_config.json") -> str:
    """
    获取配置文件路径
    
    Args:
        config_name: 配置文件名
        
    Returns:
        str: 配置文件绝对路径
    """
    return get_resource_path(os.path.join("config", config_name))

def get_data_path(data_name: str) -> str:
    """
    获取数据文件路径
    
    Args:
        data_name: 数据文件名
        
    Returns:
        str: 数据文件绝对路径
    """
    # 数据文件放在用户目录下，避免权限问题
    user_data_dir = os.path.join(os.path.expanduser("~"), "SmartTradingSystem")
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    
    return os.path.join(user_data_dir, data_name)

def get_log_path(log_name: str = "trading.log") -> str:
    """
    获取日志文件路径
    
    Args:
        log_name: 日志文件名
        
    Returns:
        str: 日志文件绝对路径
    """
    return get_data_path(log_name)

def ensure_directory(file_path: str) -> str:
    """
    确保目录存在
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 文件路径
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    return file_path

def is_packaged() -> bool:
    """
    检查是否为打包后的程序
    
    Returns:
        bool: 是否为打包程序
    """
    return hasattr(sys, '_MEIPASS')

def get_executable_dir() -> str:
    """
    获取可执行文件所在目录
    
    Returns:
        str: 可执行文件目录
    """
    if is_packaged():
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def copy_default_config():
    """
    复制默认配置文件到用户目录
    """
    try:
        import shutil
        
        # 源配置文件路径
        source_config = get_resource_path(os.path.join("config", "trading_config.json"))
        
        # 目标配置文件路径
        target_config = get_data_path("trading_config.json")
        
        # 如果用户配置不存在，复制默认配置
        if not os.path.exists(target_config) and os.path.exists(source_config):
            shutil.copy2(source_config, target_config)
            print(f"已复制默认配置到: {target_config}")
        
        return target_config
        
    except Exception as e:
        print(f"复制配置文件失败: {e}")
        return source_config

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_path = None
        self.config_data = {}
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            import json
            
            # 优先使用用户目录的配置
            user_config = get_data_path("trading_config.json")
            default_config = get_resource_path(os.path.join("config", "trading_config.json"))
            
            if os.path.exists(user_config):
                self.config_path = user_config
            elif os.path.exists(default_config):
                self.config_path = default_config
                # 复制到用户目录
                copy_default_config()
                self.config_path = get_data_path("trading_config.json")
            else:
                # 创建默认配置
                self.create_default_config()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
                
        except Exception as e:
            print(f"加载配置失败: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置"""
        self.config_data = {
            "system": {
                "debug": False,
                "log_level": "INFO"
            },
            "trading": {
                "enabled": True,
                "cooldown": 30
            },
            "enhanced_detection": {
                "enabled": True,
                "signal_thresholds": {
                    "min_confidence": 0.6
                }
            }
        }
        self.config_path = get_data_path("trading_config.json")
        self.save_config()
    
    def save_config(self):
        """保存配置"""
        try:
            import json
            ensure_directory(self.config_path)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        data = self.config_data
        
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return default
        
        return data
    
    def set(self, key: str, value):
        """设置配置值"""
        keys = key.split('.')
        data = self.config_data
        
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        data[keys[-1]] = value
        self.save_config()

# 全局配置管理器实例
try:
    from config.config_manager import EnhancedConfigManager
    config_manager = EnhancedConfigManager()
except ImportError:
    # 如果无法导入增强版，使用本地版本
    config_manager = ConfigManager()
