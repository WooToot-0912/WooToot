#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版配置管理器
支持动态配置更新、多环境配置、配置验证等功能
"""

import json
import os
import logging
import shutil
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading

class EnhancedConfigManager:
    """增强版配置管理器"""
    
    def __init__(self, config_file: str = None):
        # 智能查找配置文件
        if config_file is None:
            config_file = self._find_config_file()
        
        print(f"🔧 开始初始化EnhancedConfigManager: {config_file}")
        self.config_file = config_file
        self.config_dir = os.path.dirname(config_file) if config_file else "config"
        self.config = {}
        self.default_config = {}
        # 使用可重入锁，避免在同一线程内重复获取锁引发死锁
        self.config_lock = threading.RLock()
        
        # 安全初始化日志器（避免循环依赖）
        try:
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            print(f"⚠️ 日志器初始化失败，使用print: {e}")
            self.logger = None
        
        print("🔧 确保配置目录存在...")
        # 确保配置目录存在
        if self.config_dir and not os.path.exists(self.config_dir):
            try:
                os.makedirs(self.config_dir)
                print(f"✅ 创建配置目录: {self.config_dir}")
            except Exception as e:
                print(f"❌ 创建配置目录失败: {e}")
        
        print("🔧 开始加载配置...")
        # 加载配置
        try:
            self.load_config()
            print("✅ 配置加载完成")
        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            # 使用最基本的默认配置
            self.config = self.get_minimal_default_config()
        
        print("✅ EnhancedConfigManager初始化完成")
        if self.logger:
            self.logger.info("增强版配置管理器初始化完成")

    def _find_config_file(self) -> str:
        """智能查找配置文件"""
        # 获取当前文件的位置
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        
        # 可能的配置文件位置
        possible_paths = [
            # 同级目录
            os.path.join(current_dir, "trading_config.json"),
            # 项目根目录的config
            os.path.join(os.path.dirname(os.path.dirname(current_dir)), "config", "trading_config.json"),
            # app目录下的config
            os.path.join(os.path.dirname(current_dir), "config", "trading_config.json"),
            # 当前工作目录的config
            os.path.join(os.getcwd(), "config", "trading_config.json"),
            os.path.join(os.getcwd(), "app", "config", "trading_config.json"),
        ]
        
        print("🔍 查找配置文件...")
        for path in possible_paths:
            print(f"   检查: {path}")
            if os.path.exists(path):
                print(f"✅ 找到配置文件: {path}")
                return path
        
        print("⚠️ 未找到现有配置文件，将创建新的")
        # 如果都不存在，返回一个合适的默认路径
        return os.path.join(os.getcwd(), "config", "trading_config.json")

    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            print(f"🔧 开始加载配置文件: {self.config_file}")
            with self.config_lock:
                if os.path.exists(self.config_file):
                    print("📂 配置文件存在，正在读取...")
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        self.config = json.load(f)
                    print("✅ 配置文件读取成功")
                    if self.logger:
                        self.logger.info(f"配置文件加载成功: {self.config_file}")
                else:
                    print("⚠️ 配置文件不存在，创建默认配置...")
                    if self.logger:
                        self.logger.warning(f"配置文件不存在，使用默认配置: {self.config_file}")
                    self.config = self.get_default_config()
                    print("🔧 正在保存默认配置...")
                    try:
                        self.save_config()
                        print("✅ 默认配置保存完成")
                    except Exception as save_e:
                        print(f"⚠️ 默认配置保存失败，继续运行: {save_e}")
                
                print("🔧 开始验证配置...")
                # 验证配置
                try:
                    self.validate_config()
                    print("✅ 配置验证完成")
                except Exception as validate_e:
                    print(f"⚠️ 配置验证失败，继续运行: {validate_e}")
                return True
                
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            if self.logger:
                self.logger.error(f"加载配置文件失败: {e}")
            self.config = self.get_minimal_default_config()
            return False

    def save_config(self) -> bool:
        """保存配置文件"""
        try:
            with self.config_lock:
                # 备份现有配置
                if self.config_file and os.path.exists(self.config_file):
                    backup_file = f"{self.config_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    try:
                        shutil.copy2(self.config_file, backup_file)
                    except Exception:
                        # 备份失败不应阻塞主流程
                        pass
                
                # 确保目录存在
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                
                # 保存新配置
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                
                if self.logger:
                    self.logger.info("配置文件保存成功")
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"保存配置文件失败: {e}")
            else:
                print(f"保存配置文件失败: {e}")
            return False

    def get_minimal_default_config(self) -> Dict[str, Any]:
        """获取最小默认配置（避免阻塞）"""
        return {
            "system": {"name": "简化交易系统", "version": "1.0"},
            "trading": {
                "parameters": {"trade_cooldown": 30},
                "profit_loss": {"profit_threshold": 1.0, "loss_threshold": -3.0}
            },
            "detection": {
                "yellow_line": {"enabled": True},
                "profit_loss": {"enabled": True}
            }
        }
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "system": {
                "version": "2.0.0",
                "environment": "production",
                "debug_mode": False,
                "log_level": "INFO"
            },
            "trading": {
                "parameters": {
                    "trade_cooldown": 30,
                    "max_trades_per_hour": 10
                },
                "profit_loss": {
                    "profit_threshold": 1.0,
                    "loss_threshold": -3.0
                }
            },
            "detection": {
                "yellow_line": {
                    "color_ranges": [
                        {
                            "name": "yellow",
                            "lower": [20, 150, 150],
                            "upper": [35, 255, 255]
                        },
                        {
                            "name": "bright_yellow",
                            "lower": [15, 100, 100],
                            "upper": [35, 255, 255]
                        }
                    ],
                    "min_area": 50,
                    "data_points_used": 2
                },
                "profit_loss": {
                    "region": {
                        "x_ratio": 0.6,
                        "y_ratio": 0.6,
                        "width_ratio": 0.35,
                        "height_ratio": 0.3
                    }
                }
            },
            "ui": {
                "window": {
                    "width": 1200,
                    "height": 800
                },
                "theme": {
                    "name": "dark"
                }
            }
        }
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 验证必需的配置项
            required_keys = [
                "system",
                "trading.parameters",
                "trading.profit_loss",
                "detection.yellow_line",
                "detection.profit_loss"
            ]
            
            for key in required_keys:
                if not self.get(key):
                    if self.logger:
                        self.logger.warning(f"缺少必需的配置项: {key}")
                    return False
            
            # 验证数值范围
            trade_cooldown = self.get("trading.parameters.trade_cooldown", 10)
            if not (1 <= trade_cooldown <= 300):
                if self.logger:
                    self.logger.warning(f"交易冷却时间超出范围: {trade_cooldown}")
                self.set("trading.parameters.trade_cooldown", 10, save=False)
            
            profit_threshold = self.get("trading.profit_loss.profit_threshold", 1.0)
            if not (0.1 <= profit_threshold <= 100):
                if self.logger:
                    self.logger.warning(f"止盈阈值超出范围: {profit_threshold}")
                self.set("trading.profit_loss.profit_threshold", 1.0, save=False)
            
            loss_threshold = self.get("trading.profit_loss.loss_threshold", -3.0)
            if not (-100 <= loss_threshold <= -0.1):
                if self.logger:
                    self.logger.warning(f"止损阈值超出范围: {loss_threshold}")
                self.set("trading.profit_loss.loss_threshold", -3.0, save=False)
            
            if self.logger:
                self.logger.info("配置验证通过")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"配置验证失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        try:
            with self.config_lock:
                keys = key.split('.')
                value = self.config
                
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default
                
                return value
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"获取配置失败 {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """设置配置值"""
        try:
            with self.config_lock:
                keys = key.split('.')
                node = self.config
                for k in keys[:-1]:
                    if k not in node or not isinstance(node[k], dict):
                        node[k] = {}
                    node = node[k]
                node[keys[-1]] = value
                
                if save:
                    self.save_config()
                return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"设置配置失败 {key}: {e}")
            return False
    
    def get_trading_config(self) -> Dict[str, Any]:
        """获取交易配置"""
        return self.get('trading', {})
    
    def get_detection_config(self) -> Dict[str, Any]:
        """获取检测配置"""
        return self.get('detection', {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取界面配置"""
        return self.get('ui', {})
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return self.get('system', {})
    
    def update_trading_parameters(self, params: Dict[str, Any]) -> bool:
        """更新交易参数"""
        try:
            current_params = self.get('trading.parameters', {})
            current_params.update(params)
            return self.set('trading.parameters', current_params)
        except Exception as e:
            self.logger.error(f"更新交易参数失败: {e}")
            return False
    
    def update_profit_loss_config(self, config: Dict[str, Any]) -> bool:
        """更新止盈止损配置"""
        try:
            current_config = self.get('trading.profit_loss', {})
            current_config.update(config)
            return self.set('trading.profit_loss', current_config)
        except Exception as e:
            self.logger.error(f"更新止盈止损配置失败: {e}")
            return False
    
    def reset_to_default(self) -> bool:
        """重置为默认配置"""
        try:
            with self.config_lock:
                self.config = self.get_default_config()
                return self.save_config()
        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")
            return False
    
    def export_config(self, export_file: str) -> bool:
        """导出配置"""
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"配置导出成功: {export_file}")
            return True
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_file: str) -> bool:
        """导入配置"""
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            with self.config_lock:
                self.config = imported_config
                self.validate_config()
                self.save_config()
            
            self.logger.info(f"配置导入成功: {import_file}")
            return True
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            return False
    
    def get_coordinate_config_path(self) -> str:
        """获取坐标配置文件路径"""
        coordinate_file = self.get('system.coordinate_config_file', 'smart_coordinates_config.json')
        
        # 如果是相对路径，则相对于主配置文件目录
        if not os.path.isabs(coordinate_file):
            coordinate_file = os.path.join(self.config_dir, coordinate_file)
        
        return coordinate_file
    
    def load_coordinate_config(self) -> Dict[str, Any]:
        """加载坐标配置文件"""
        try:
            coord_file = self.get_coordinate_config_path()
            
            if not os.path.exists(coord_file):
                if self.logger:
                    self.logger.warning(f"⚠️ 坐标配置文件不存在: {coord_file}")
                return {}
            
            with open(coord_file, 'r', encoding='utf-8') as f:
                coord_config = json.load(f)
            
            if self.logger:
                self.logger.info(f"✅ 坐标配置加载成功: {coord_file}")
            
            return coord_config
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ 加载坐标配置失败: {e}")
            return {}
    
    def get_button_positions(self) -> Dict[str, Any]:
        """获取按钮位置配置"""
        coord_config = self.load_coordinate_config()
        return coord_config.get('button_positions', {})
    
    def get_detection_regions(self) -> Dict[str, Any]:
        """获取检测区域配置"""
        coord_config = self.load_coordinate_config()
        return coord_config.get('detection_regions', {})

# 全局配置管理器实例
config_manager = EnhancedConfigManager()
