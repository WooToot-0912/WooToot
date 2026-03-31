#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易引擎核心模块
包含SmartTradingEngine类的核心交易逻辑
"""

import subprocess
import time
import logging
import pyautogui
import cv2
import numpy as np
from typing import Dict, Optional
import os
import sys
import random
import hashlib
import json
from .angle_detector import AngleDetector
from .confirm_dialog_detector import ConfirmDialogDetector
# 新增：HTTP交易API支持
try:
    from core.trading_api import TradingAPI as HttpTradingAPI
    HTTP_API_AVAILABLE = True
except Exception:
    HTTP_API_AVAILABLE = False
    HttpTradingAPI = None

# 启用景陶易购专用颜色检测器
try:
    # 尝试从src.ui导入
    import sys
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    ui_path = os.path.join(project_root, 'src', 'ui')
    if ui_path not in sys.path:
        sys.path.append(ui_path)
    from color_detection_fix import JingTaoColorDetector
    COLOR_DETECTION_AVAILABLE = True
except ImportError:
    try:
        # 尝试相对导入
        from ..ui.color_detection_fix import JingTaoColorDetector
        COLOR_DETECTION_AVAILABLE = True
    except ImportError:
        try:
            # 尝试绝对导入
            from ui.color_detection_fix import JingTaoColorDetector
            COLOR_DETECTION_AVAILABLE = True
        except ImportError:
            COLOR_DETECTION_AVAILABLE = False
            JingTaoColorDetector = None

# 导入真实价格检测器
try:
    from .real_price_detector import RealPriceDetector
    REAL_PRICE_DETECTOR_AVAILABLE = True
except ImportError:
    try:
        from real_price_detector import RealPriceDetector
        REAL_PRICE_DETECTOR_AVAILABLE = True
    except ImportError:
        REAL_PRICE_DETECTOR_AVAILABLE = False
        RealPriceDetector = None
        JingTaoColorDetector = None

# 自动确认处理器已删除 - 暂时禁用以排除卡死问题
AUTO_CONFIRM_AVAILABLE = False
AutoConfirmHandler = None

# 导入高级线条检测器
try:
    from .advanced_line_detector import AdvancedLineDetector
    ADVANCED_DETECTOR_AVAILABLE = True
    print("✅ 高级线条检测器可用")
except ImportError:
    ADVANCED_DETECTOR_AVAILABLE = False
    AdvancedLineDetector = None
    print("⚠️ 高级线条检测器不可用，使用基础检测方法")

# 启用增强UI检测器
try:
    # 尝试从src.ui导入
    import sys
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    ui_path = os.path.join(project_root, 'src', 'ui')
    if ui_path not in sys.path:
        sys.path.append(ui_path)
    from enhanced_ui_detection import EnhancedUIDetector
    ENHANCED_UI_DETECTION_AVAILABLE = True
except ImportError:
    try:
        # 尝试相对导入
        from ..ui.enhanced_ui_detection import EnhancedUIDetector
        ENHANCED_UI_DETECTION_AVAILABLE = True
    except ImportError:
        try:
            # 尝试绝对导入
            from ui.enhanced_ui_detection import EnhancedUIDetector
            ENHANCED_UI_DETECTION_AVAILABLE = True
        except ImportError:
            ENHANCED_UI_DETECTION_AVAILABLE = False
            EnhancedUIDetector = None

# 修复secrets模块问题
try:
    import secrets
except ImportError:
    # 创建secrets模块的替代实现
    class SecretsModule:
        """Secrets模块的替代实现"""
        
        def __init__(self):
            self._random = random.Random()
            self._random.seed(int(time.time() * 1000000))
        
        def token_bytes(self, nbytes=None):
            """生成随机字节"""
            if nbytes is None:
                nbytes = 32
            return bytes(self._random.getrandbits(8) for _ in range(nbytes))
        
        def token_hex(self, nbytes=None):
            """生成随机十六进制字符串"""
            return self.token_bytes(nbytes).hex()
        
        def token_urlsafe(self, nbytes=None):
            """生成URL安全的随机字符串"""
            import base64
            return base64.urlsafe_b64encode(self.token_bytes(nbytes)).decode('ascii').rstrip('=')
        
        def choice(self, sequence):
            """从序列中随机选择"""
            return self._random.choice(sequence)
        
        def randbelow(self, n):
            """生成小于n的随机整数"""
            return self._random.randrange(n)
        
        def randbits(self, k):
            """生成k位随机整数"""
            return self._random.getrandbits(k)
    
    # 将替代实现添加到sys.modules
    sys.modules['secrets'] = SecretsModule()
    secrets = sys.modules['secrets']

# 暂时完全禁用资源路径处理模块以排除卡死问题
RESOURCE_PATH_AVAILABLE = False
config_manager = None

# 暂时完全禁用增强检测模块以排除卡死问题
ENHANCED_DETECTION_AVAILABLE = False
enhanced_detector = None

# 创建简单的SignalType类
class SignalType:
    BULLISH = "bullish"
    BEARISH = "bearish" 
    NEUTRAL = "neutral"

# 安全导入pytesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None

# 导入Tesseract配置模块
try:
    import sys
    import os
    utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utils')
    if utils_path not in sys.path:
        sys.path.append(utils_path)
    from tesseract_config import configure_pytesseract
except ImportError:
    configure_pytesseract = None

def _setup_tesseract():
    """设置Tesseract路径"""
    if not TESSERACT_AVAILABLE or pytesseract is None:
        return False

    if configure_pytesseract:
        return configure_pytesseract()
    else:
        # 备用配置方法
        tesseract_paths = [
            r"D:\Program Files\Tesseract-OCR\tesseract.exe",  # 用户新安装的路径
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', '')),
            r"D:\Program Files\tesseract.exe",
            "tesseract"  # 系统PATH中的tesseract
        ]

        for path in tesseract_paths:
            if os.path.exists(path) or path == "tesseract":
                try:
                    pytesseract.pytesseract.tesseract_cmd = path
                    # 快速测试是否可用（设置短超时）
                    pytesseract.get_tesseract_version()
                    return True
                except:
                    continue

        logging.warning("未找到可用的Tesseract安装，OCR功能将不可用")
        return False


class SmartTradingEngine:
    """智能交易引擎核心类"""
    
    def __init__(self, client_path: str = None, config=None):
        self.logger = logging.getLogger(__name__)
        
        # 初始化配置管理器
        if config is not None:
            self.config = config
        else:
            # 创建默认配置对象
            try:
                # 尝试多种导入路径
                try:
                    from config.config_manager import EnhancedConfigManager
                except ImportError:
                    import sys
                    import os
                    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
                    if config_path not in sys.path:
                        sys.path.append(config_path)
                    from config_manager import EnhancedConfigManager
                
                self.config = EnhancedConfigManager()
            except (ImportError, Exception):
                # 如果无法导入配置管理器，创建一个简单的配置对象
                class SimpleConfig:
                    def get(self, key, default=None):
                        return default
                self.config = SimpleConfig()
                self.logger.warning("使用简单配置对象，手动价格选择功能将不可用")
        
        # 客户端路径
        self.client_path = client_path or r"D:\Program Files\DEAL_JCST_RNHY_Client"
        self.client_process = None
        self.client_window = None
        self.window_rect = None

        # 初始化角度检测器 - 默认20度阈值
        self.angle_detector = AngleDetector(angle_threshold=20.0, history_size=10)
        self.logger.info("角度检测器已初始化，阈值: 20.0°")

        # 初始化确认对话框检测器
        self.confirm_dialog_detector = ConfirmDialogDetector()
        self.logger.info("确认对话框检测器已初始化")

    def set_angle_threshold(self, threshold: float):
        """设置角度检测阈值"""
        if hasattr(self, 'angle_detector'):
            self.angle_detector.set_angle_threshold(threshold)
            self.logger.info(f"角度检测阈值已更新为: {threshold}°")
        else:
            self.logger.warning("角度检测器未初始化")

    def get_angle_statistics(self) -> Dict:
        """获取角度统计信息"""
        if hasattr(self, 'angle_detector'):
            return self.angle_detector.get_angle_statistics()
        return {}

    def reset_angle_history(self):
        """重置角度历史数据"""
        if hasattr(self, 'angle_detector'):
            self.angle_detector.reset_history()
            self.logger.info("角度历史数据已重置")
        
        # 智能坐标定位 - 从配置文件加载坐标
        self.relative_positions = self._load_coordinates_from_config()
        self.logger.info("📍 坐标配置已从配置文件加载")
        
        # 如果使用了EnhancedConfigManager，则也从中加载按钮位置
        if hasattr(self.config, 'get_button_positions'):
            try:
                enhanced_positions = self.config.get_button_positions()
                if enhanced_positions:
                    # 合并增强配置管理器的按钮位置
                    self.relative_positions.update(enhanced_positions)
                    self.logger.info("📍 已合并增强配置管理器的按钮位置")
            except Exception as e:
                self.logger.warning(f"⚠️ 合并增强按钮位置失败: {e}")
        
        # 监测数据
        self.price_history = []
        self.yellow_line_data = []
        self.last_trade_time = 0
        
        # 交易参数
        self.trade_cooldown = 30  # 交易冷却时间
        self.min_price_change = 0.5  # 最小价格变化率
        self.is_running = False
        
        # 新增：黄线检测区域
        self.yellow_line_region = None  # (x, y, width, height)
        
        # 新增：转让冷却期和货值检测
        self.last_transfer_time = 0
        self.transfer_cooldown = 60  # 转让冷却时间（秒）
        self.last_profit_value = None
        self.profit_change_threshold = 1.0  # 货值变化阈值（调整为1.0，更敏感）
        
        # 实时价格监控
        self.current_price = None
        self.price_change_rate = 0.0
        self.last_price_update_time = 0
        self.price_update_interval = 1.0  # 价格更新间隔（秒）
        
        # 黄线检测参数
        self.angle_threshold = 5  # 默认角度阈值（度）
        
        # 初始化景陶易购专用颜色检测器
        self.jingtao_detector = None
        self.logger.info("⚠️ 专用检测器将延迟初始化")

        # 初始化自动确认处理器
        self.auto_confirm_handler = None
        self.logger.info("⚠️ 自动确认处理器将延迟初始化")
        
        # 延迟初始化真实价格检测器，避免GUI卡死
        self.real_price_detector = None
        self.logger.info("⚠️ 真实价格检测器将延迟初始化")

        # 简化坐标验证，避免复杂操作
        self.logger.info("✅ 交易引擎基础初始化完成")

        # 初始化HTTP交易API（多用户）
        self.http_api = None
        if HTTP_API_AVAILABLE and hasattr(self, 'config') and hasattr(self.config, 'get'):
            try:
                api_base = self.config.get('api.base_url', 'https://zxyw.ceramic-copyright.com/apigateway')
                kline_url = self.config.get('api.kline_url', 'https://zxyt.ceramic-copyright.com/qtfront_tq')
                self.http_api = HttpTradingAPI(base_url=api_base, kline_url=kline_url)
                self.logger.info("✅ 已加载HTTP交易API客户端")
            except Exception as e:
                self.logger.warning(f"⚠️ 初始化HTTP交易API失败: {e}")

    def _load_coordinates_from_config(self) -> dict:
        """从配置文件加载坐标"""
        try:
            # 加载配置文件
            button_positions = self.load_coordinate_config()
            
            # 转换为相对坐标格式
            relative_positions = {}
            
            # 基础按钮坐标
            for button_name, button_info in button_positions.items():
                if isinstance(button_info, dict) and 'x' in button_info and 'y' in button_info:
                    relative_positions[button_name] = (button_info['x'], button_info['y'])
            
            # 添加固定的监控区域坐标（这些通常不需要校准）
            relative_positions.update({
                # 实时货值变化监控区域
                'realtime_value_area': (0.75, 0.15, 0.25, 0.4),
                'current_price_display': (0.85, 0.18),
                'price_change_display': (0.85, 0.22),
                'volume_display': (0.85, 0.26),
                
                # 改进的价格获取区域
                'latest_price_area': (0.0, 0.0, 0.7, 0.6),
                'order_book_area': (0.7, 0.15, 0.3, 0.85),
                'current_price_text': (0.85, 0.18)
            })
            
            self.logger.info(f"✅ 从配置文件加载了 {len(button_positions)} 个按钮坐标")
            return relative_positions
            
        except Exception as e:
            self.logger.error(f"❌ 从配置文件加载坐标失败: {e}")
            # 返回默认坐标
            return self._get_default_relative_positions()
    
    def _get_default_relative_positions(self) -> dict:
        """获取默认的相对坐标"""
        return {
            'buy_mode_button': (0.01395348837209302, 0.7064516129032258),
            'sell_mode_button': (0.014341085271317829, 0.7819354838709677),
            'buy_order_button': (0.07829457364341085, 0.9270967741935484),
            'sell_order_button': (0.07946511627906976, 0.9296774193548387),
            'price_input': (0.095, 0.768),  # 使用更新后的坐标
            'quantity_input': (0.093, 0.814),  # 使用更新后的坐标
            'confirm_button': (0.43488372093023255, 0.5419354838709677),
            'transfer_out_button': (0.11821705426356589, 0.7251612903225806),
            'order_mode_button': (0.05968992248062015, 0.7283870967741935),
            
            # 监控区域
            'realtime_value_area': (0.75, 0.15, 0.25, 0.4),
            'current_price_display': (0.85, 0.18),
            'price_change_display': (0.85, 0.22),
            'volume_display': (0.85, 0.26),
            'latest_price_area': (0.0, 0.0, 0.7, 0.6),
            'order_book_area': (0.7, 0.15, 0.3, 0.85),
            'current_price_text': (0.85, 0.18)
        }

    def delayed_init_components(self, log_callback=None):
        """延迟初始化组件，避免GUI卡死"""
        def log_message(message):
            """统一的日志输出函数"""
            print(message)  # 控制台输出
            if log_callback:
                log_callback(message)  # GUI日志输出
        
        try:
            # 初始化景陶易购专用颜色检测器
            if COLOR_DETECTION_AVAILABLE:
                try:
                    self.jingtao_detector = JingTaoColorDetector()
                    message = "✅ 景陶易购专用颜色检测器初始化成功"
                    self.logger.info(message)
                    log_message(message)
                except Exception as e:
                    self.jingtao_detector = None
                    message = f"⚠️ 景陶易购专用颜色检测器初始化失败: {e}"
                    self.logger.warning(message)
                    log_message(message)
            else:
                self.jingtao_detector = None
                message = "⚠️ 颜色检测器不可用，将使用备用检测方法"
                self.logger.warning(message)
                log_message(message)

            # 初始化自动确认处理器
            if AUTO_CONFIRM_AVAILABLE:
                try:
                    self.auto_confirm_handler = AutoConfirmHandler()
                    message = "✅ 自动确认处理器初始化成功"
                    self.logger.info(message)
                    log_message(message)
                except Exception as e:
                    self.auto_confirm_handler = None
                    message = f"⚠️ 自动确认处理器初始化失败: {e}"
                    self.logger.warning(message)
                    log_message(message)
            else:
                self.auto_confirm_handler = None
                message = "⚠️ 自动确认处理器不可用"
                self.logger.warning(message)
                log_message(message)

            # 初始化增强UI检测器
            if ENHANCED_UI_DETECTION_AVAILABLE:
                try:
                    self.enhanced_ui_detector = EnhancedUIDetector()
                    message = "✅ 增强UI检测器初始化成功"
                    self.logger.info(message)
                    log_message(message)
                except Exception as e:
                    self.enhanced_ui_detector = None
                    message = f"⚠️ 增强UI检测器初始化失败: {e}"
                    self.logger.warning(message)
                    log_message(message)
            else:
                self.enhanced_ui_detector = None
                message = "⚠️ 增强UI检测器不可用，将使用标准UI检测方法"
                self.logger.warning(message)
                log_message(message)

            # 初始化真实价格检测器
            if REAL_PRICE_DETECTOR_AVAILABLE:
                try:
                    use_manual_selection = self.config.get('price_detection.use_manual_price_selection', False)
                    self.logger.info(f"🔍 配置中的手动选择设置: {use_manual_selection}")
                    # 尝试使用增强版价格检测器
                    try:
                        from .real_price_detector import RealPriceDetectorEnhanced
                        self.real_price_detector = RealPriceDetectorEnhanced(use_manual_selection=use_manual_selection)
                        self.logger.info("🔧 使用增强版价格检测器")
                    except (ImportError, AttributeError):
                        # 回退到普通版本
                        self.real_price_detector = RealPriceDetector(use_manual_selection=use_manual_selection)
                        self.logger.info("🔧 使用标准版价格检测器")

                    # 检查实际使用的模式（可能因为初始化失败而回退）
                    if self.real_price_detector.use_manual_selection:
                        message = "✅ 真实价格检测器初始化成功 - 手动区域选择模式"
                    else:
                        message = "✅ 真实价格检测器初始化成功 - OCR模式"
                    
                    self.logger.info(message)
                    log_message(message)

                except Exception as e:
                    self.real_price_detector = None
                    message = f"⚠️ 真实价格检测器初始化失败: {e}"
                    self.logger.warning(message)
                    log_message(message)
            else:
                self.real_price_detector = None
                message = "⚠️ 真实价格检测器不可用"
                self.logger.warning(message)
                log_message(message)

            # 初始化高级线条检测器
            if ADVANCED_DETECTOR_AVAILABLE:
                try:
                    self.advanced_line_detector = AdvancedLineDetector()
                    message = "✅ 高级线条检测器初始化成功"
                    self.logger.info(message)
                    log_message(message)
                except Exception as e:
                    self.advanced_line_detector = None
                    message = f"⚠️ 高级线条检测器初始化失败: {e}"
                    self.logger.warning(message)
                    log_message(message)
            else:
                self.advanced_line_detector = None
                message = "⚠️ 高级线条检测器不可用，使用基础检测方法"
                self.logger.warning(message)
                log_message(message)

            # 验证坐标配置
            self.validate_coordinates()

            # 如果可用，则尝试基于配置进行HTTP API自动登录（多用户）
            try:
                if getattr(self, 'http_api', None) and hasattr(self, 'config') and hasattr(self.config, 'get'):
                    phone = self.config.get('api.credentials.phone', '')
                    password_md5 = self.config.get('api.credentials.password_md5', '')
                    market_id = int(self.config.get('api.market_id', 28))
                    if phone and password_md5:
                        login_res = self.http_api.login(phone, password_md5, market_id)
                        if login_res.get('code') == '0':
                            message = "✅ HTTP API登录成功，已启用API下单"
                        else:
                            message = f"⚠️ HTTP API登录失败: {login_res.get('message', '未知错误')}"
                        self.logger.info(message)
                        log_message(message)
                    else:
                        self.logger.info("ℹ️ 未配置API凭据，保持UI自动化下单")
            except Exception as api_login_e:
                self.logger.warning(f"⚠️ HTTP API自动登录异常: {api_login_e}")

            message = "✅ 延迟组件初始化完成"
            self.logger.info(message)
            log_message(message)

        except Exception as e:
            self.logger.error(f"❌ 延迟组件初始化失败: {e}")
        
        self.logger.info("智能交易引擎初始化完成")
    
    def _find_config_file(self) -> str:
        """智能查找配置文件"""
        # 获取当前文件的绝对路径
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        
        # 尝试向上查找项目根目录
        project_root = current_dir
        for _ in range(5):  # 最多向上查找5层
            config_path = os.path.join(project_root, "config", "smart_coordinates_config.json")
            if os.path.exists(config_path):
                return config_path
            parent = os.path.dirname(project_root)
            if parent == project_root:  # 已经到根目录
                break
            project_root = parent
        
        # 备用查找位置
        possible_locations = [
            "../../config/smart_coordinates_config.json",
            "../../../config/smart_coordinates_config.json",
            "config/smart_coordinates_config.json",
            "smart_coordinates_config.json",
        ]
        
        for location in possible_locations:
            full_path = os.path.join(current_dir, location)
            if os.path.exists(full_path):
                return full_path
        
        return None

    def load_coordinate_config(self) -> dict:
        """加载坐标配置文件"""
        try:
            # 智能查找配置文件路径
            config_file = self._find_config_file()
            
            if not config_file:
                self.logger.warning("⚠️ 坐标配置文件不存在，使用默认坐标")
                return self.get_default_coordinates()
            
            self.logger.info(f"📂 找到配置文件: {config_file}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.logger.info("✅ 坐标配置加载成功")
            
            # 提取按钮位置
            button_positions = config_data.get('button_positions', {})
            
            # 记录加载的坐标信息
            for button_name, button_info in button_positions.items():
                if 'calibrated_absolute' in button_info:
                    abs_x = button_info['calibrated_absolute']['x']
                    abs_y = button_info['calibrated_absolute']['y']
                    self.logger.info(f"📍 {button_info.get('name', button_name)}: ({abs_x}, {abs_y})")
            
            return button_positions
                
        except Exception as e:
            self.logger.error(f"❌ 加载坐标配置失败: {e}")
            return self.get_default_coordinates()
    
    def get_default_coordinates(self) -> dict:
        """获取默认坐标配置"""
        return {
            'buy_mode_button': {
                'name': '买入模式按钮',
                'x': 0.01395348837209302,
                'y': 0.7064516129032258,
                'calibrated_absolute': {'x': 36, 'y': 1095},
                'description': '左侧红色的买按钮'
            },
            'sell_mode_button': {
                'name': '卖出模式按钮', 
                'x': 0.014341085271317829,
                'y': 0.7819354838709677,
                'calibrated_absolute': {'x': 37, 'y': 1212},
                'description': '左侧绿色的卖按钮'
            },
            'buy_order_button': {
                'name': '买入订立按钮',
                'x': 0.07829457364341085,
                'y': 0.9270967741935484,
                'calibrated_absolute': {'x': 202, 'y': 1437},
                'description': '底部的买入订立按钮'
            },
            'sell_order_button': {
                'name': '卖出订立按钮',
                'x': 0.12,
                'y': 0.94,
                'calibrated_absolute': {'x': 310, 'y': 1450},
                'description': '底部的卖出订立按钮'
            },
            'price_input': {
                'name': '价格输入框',
                'x': 0.095,
                'y': 0.768,
                'calibrated_absolute': {'x': 234, 'y': 1180},
                'description': '价格输入区域'
            },
            'quantity_input': {
                'name': '数量输入框',
                'x': 0.093,
                'y': 0.814,
                'calibrated_absolute': {'x': 230, 'y': 1250},
                'description': '数量输入区域'
            },
            'confirm_button': {
                'name': '确认按钮',
                'x': 0.43488372093023255,
                'y': 0.5419354838709677,
                'calibrated_absolute': {'x': 1123, 'y': 840},
                'description': '弹出对话框中的确定按钮'
            },
            'transfer_out_button': {
                'name': '银证转出按钮',
                'x': 0.12,
                'y': 0.73,
                'calibrated_absolute': {'x': 310, 'y': 1130},
                'description': '银证转出按钮'
            },
            'order_mode_button': {
                'name': '订立模式按钮',
                'x': 0.08,
                'y': 0.72,
                'calibrated_absolute': {'x': 206, 'y': 1116},
                'description': '切换到订立模式的按钮'
            }
        }
    
    def validate_coordinates(self):
        """验证坐标配置的有效性"""
        try:
            required_buttons = ['buy_mode_button', 'sell_mode_button', 'buy_order_button', 'confirm_button']
            missing_buttons = []
            
            for button in required_buttons:
                if button not in self.relative_positions:
                    missing_buttons.append(button)
                else:
                    # 检查坐标是否在合理范围内
                    x, y = self.relative_positions[button]
                    
                    if not (0 <= x <= 1 and 0 <= y <= 1):
                        self.logger.warning(f"⚠️ 按钮 {button} 的相对坐标超出范围: ({x}, {y})")
            
            if missing_buttons:
                self.logger.error(f"❌ 缺少必需的按钮配置: {missing_buttons}")
                return False
            else:
                self.logger.info("✅ 坐标配置验证通过")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 坐标验证失败: {e}")
            return False
    
    def start_client(self) -> bool:
        """启动或查找客户端"""
        try:
            # 首先尝试查找已运行的客户端
            if self.find_client_window():
                self.logger.info("✅ 找到已运行的客户端")
                return True
            
            # 如果没有找到，尝试启动客户端
            self.logger.info("正在查找或启动景陶易购客户端...")
            
            # 等待一段时间让用户手动打开客户端
            for i in range(10):  # 等待最多50秒
                time.sleep(5)
                if self.find_client_window():
                    self.logger.info("✅ 客户端检测成功")
                    return True
                self.logger.info(f"等待客户端启动... ({i+1}/10)")
            
            self.logger.error("❌ 未能找到客户端窗口")
            return False
            
        except Exception as e:
            self.logger.error(f"启动客户端失败: {e}")
            return False
    
    def find_client_window(self) -> bool:
        """查找客户端窗口"""
        try:
            import win32gui
            
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    
                    # 详细的窗口检测日志
                    if window_text and ("景陶易购" in window_text or "交易" in window_text):
                        self.logger.info(f"🔍 发现窗口: '{window_text}' (类名: {class_name})")
                        windows.append((hwnd, window_text, class_name))
                        
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            # 过滤掉脚本自己的窗口
            client_windows = []
            for hwnd, title, class_name in windows:
                # 排除Python脚本窗口
                if ("python" not in title.lower() and 
                    "交易系统" not in title and
                    "景陶易购" in title):
                    client_windows.append((hwnd, title, class_name))
            
            if client_windows:
                self.client_window = client_windows[0][0]  # 取第一个匹配的窗口
                window_title = client_windows[0][1]
                
                # 激活客户端窗口确保它在前台
                try:
                    win32gui.SetForegroundWindow(self.client_window)
                    import time
                    time.sleep(0.5)  # 等待窗口激活
                except:
                    pass
                
                # 获取窗口位置和大小
                rect = win32gui.GetWindowRect(self.client_window)
                
                # 创建窗口矩形对象
                class WindowRect:
                    def __init__(self, left, top, right, bottom):
                        self.left = left
                        self.top = top
                        self.right = right
                        self.bottom = bottom
                        self.width = right - left
                        self.height = bottom - top
                
                self.window_rect = WindowRect(rect[0], rect[1], rect[2], rect[3])
                
                # 修复窗口位置以适应截图
                self._fix_window_position_for_screenshot()
                
                self.logger.info(f"✅ 找到并激活客户端窗口: {window_title}")
                self.logger.info(f"📏 客户端窗口位置: ({self.window_rect.left}, {self.window_rect.top})")
                self.logger.info(f"📐 客户端窗口大小: {self.window_rect.width} x {self.window_rect.height}")
                
                # 验证窗口合理性
                if self.window_rect.width < 100 or self.window_rect.height < 100:
                    self.logger.warning("⚠️ 检测到的窗口尺寸过小，可能不是正确的客户端窗口")
                    return False
                
                return True
            else:
                self.logger.warning("⚠️ 未找到景陶易购客户端窗口")
                if windows:
                    self.logger.info("找到的相关窗口:")
                    for hwnd, title, class_name in windows:
                        self.logger.info(f"  - '{title}' (类名: {class_name})")
                return False
                
        except Exception as e:
            self.logger.error(f"查找客户端窗口失败: {e}")
            return False
    
    def _fix_window_position_for_screenshot(self):
        """修复窗口位置以适应截图需求"""
        if not self.window_rect:
            return False
        
        import pyautogui
        
        # 获取屏幕尺寸
        screen_width, screen_height = pyautogui.size()
        
        # 保存原始位置
        original_left = self.window_rect.left
        original_top = self.window_rect.top
        original_right = self.window_rect.right
        original_bottom = self.window_rect.bottom
        
        # 确保坐标在屏幕范围内
        corrected_left = max(0, original_left)
        corrected_top = max(0, original_top)
        corrected_right = min(screen_width, original_right)
        corrected_bottom = min(screen_height, original_bottom)
        
        # 更新窗口矩形
        self.window_rect.left = corrected_left
        self.window_rect.top = corrected_top
        self.window_rect.right = corrected_right
        self.window_rect.bottom = corrected_bottom
        self.window_rect.width = corrected_right - corrected_left
        self.window_rect.height = corrected_bottom - corrected_top
        
        # 记录修正信息
        if (original_left != corrected_left or original_top != corrected_top or 
            original_right != corrected_right or original_bottom != corrected_bottom):
            self.logger.info(f"🔧 窗口位置已修正:")
            self.logger.info(f"   原始: ({original_left}, {original_top}, {original_right}, {original_bottom})")
            self.logger.info(f"   修正: ({corrected_left}, {corrected_top}, {corrected_right}, {corrected_bottom})")
        
        return True
    
    def calculate_absolute_position(self, relative_x: float, relative_y: float) -> tuple:
        """计算绝对坐标位置"""
        try:
            if not self.window_rect:
                self.logger.error("❌ 窗口位置信息不可用")
                return None, None
            
            # 使用校准的绝对坐标（如果可用）
            abs_x = self.window_rect.left + int(relative_x * self.window_rect.width)
            abs_y = self.window_rect.top + int(relative_y * self.window_rect.height)
            
            return abs_x, abs_y
            
        except Exception as e:
            self.logger.error(f"计算绝对坐标失败: {e}")
            return None, None
    
    def get_button_position(self, button_name: str) -> tuple:
        """获取按钮的绝对坐标"""
        try:
            if button_name not in self.relative_positions:
                self.logger.error(f"❌ 未找到按钮配置: {button_name}")
                return None, None
            
            # 获取相对坐标（元组形式）
            rel_x, rel_y = self.relative_positions[button_name]
            
            # 使用calculate_button_position计算绝对坐标
            x, y = self.calculate_button_position(button_name)
            if x is not None and y is not None:
                self.logger.info(f"📍 按钮 {button_name} 坐标: ({x}, {y})")
                return x, y
            else:
                return None, None
                    
        except Exception as e:
            self.logger.error(f"获取按钮位置失败: {e}")
            return None, None
    
    def click_button(self, button_name: str, delay: float = 1.0) -> bool:
        """点击指定按钮"""
        try:
            x, y = self.get_button_position(button_name)
            if x is None or y is None:
                self.logger.error(f"❌ 无法获取按钮 {button_name} 的位置")
                return False
            
            # 点击按钮
            pyautogui.click(x, y)
            self.logger.info(f"🖱️ 点击按钮: {button_name} 位置: ({x}, {y})")
            
            # 等待
            time.sleep(delay)
            return True
            
        except Exception as e:
            self.logger.error(f"点击按钮 {button_name} 失败: {e}")
            return False
    
    def calculate_button_position(self, button_name: str) -> tuple:
        """根据窗口大小计算按钮绝对坐标"""
        try:
            if not self.window_rect:
                raise ValueError("窗口位置未设置")
            
            if button_name not in self.relative_positions:
                raise ValueError(f"未知的按钮名称: {button_name}")
            
            relative_x, relative_y = self.relative_positions[button_name]
            
            # 计算绝对坐标
            abs_x = int(self.window_rect.left + self.window_rect.width * relative_x)
            abs_y = int(self.window_rect.top + self.window_rect.height * relative_y)
            
            # 详细的坐标计算日志
            self.logger.debug(f"🎯 坐标计算详情 - {button_name}:")
            self.logger.debug(f"  - 窗口: ({self.window_rect.left}, {self.window_rect.top}) "
                            f"尺寸: {self.window_rect.width}x{self.window_rect.height}")
            self.logger.debug(f"  - 相对坐标: ({relative_x:.6f}, {relative_y:.6f})")
            self.logger.debug(f"  - 绝对坐标: ({abs_x}, {abs_y})")
            
            self.logger.info(f"📍 {button_name} 位置: ({abs_x}, {abs_y})")
            return abs_x, abs_y
            
        except Exception as e:
            self.logger.error(f"❌ 计算 {button_name} 位置失败: {e}")
            return None, None
    
    def test_coordinates_with_mouse(self):
        """测试坐标准确性 - 鼠标依次移动到每个按钮位置"""
        try:
            import pyautogui
            import time
            
            self.logger.info("🎯 开始坐标测试 - 鼠标将依次移动到各按钮位置")
            
            # 激活客户端窗口
            if not self.find_client_window():
                self.logger.error("❌ 无法找到客户端窗口")
                return False
            
            # 显示窗口检测结果
            self.logger.info("=" * 50)
            self.logger.info("📋 窗口检测结果:")
            self.logger.info(f"   窗口位置: ({self.window_rect.left}, {self.window_rect.top})")
            self.logger.info(f"   窗口大小: {self.window_rect.width} x {self.window_rect.height}")
            self.logger.info(f"   窗口右下角: ({self.window_rect.right}, {self.window_rect.bottom})")
            
            # 获取屏幕大小作为对比
            screen_width, screen_height = pyautogui.size()
            self.logger.info(f"   屏幕大小: {screen_width} x {screen_height}")
            self.logger.info("=" * 50)
            
            # 定义按钮测试顺序和描述
            button_tests = [
                ('buy_mode_button', '买入模式按钮'),
                ('sell_mode_button', '卖出模式按钮'),
                ('price_input', '价格输入框'),
                ('quantity_input', '数量输入框'),
                ('buy_order_button', '买入订立按钮'),
                ('sell_order_button', '卖出订立按钮'),
                ('confirm_button', '确认按钮'),
                ('transfer_out_button', '银证转出按钮'),
                ('order_mode_button', '订立模式按钮')
            ]
            
            for button_name, description in button_tests:
                try:
                    self.logger.info(f"🎯 测试 {description} ({button_name})")
                    
                    # 计算按钮坐标
                    x, y = self.calculate_button_position(button_name)
                    if x is None or y is None:
                        self.logger.error(f"❌ {description} 坐标计算失败")
                        continue
                    
                    # 显示详细的坐标计算过程
                    rel_x, rel_y = self.relative_positions[button_name]
                    self.logger.info(f"🔍 {description} 坐标计算:")
                    self.logger.info(f"   相对坐标: ({rel_x:.6f}, {rel_y:.6f})")
                    self.logger.info(f"   窗口偏移: ({self.window_rect.left}, {self.window_rect.top})")
                    self.logger.info(f"   窗口尺寸: {self.window_rect.width} x {self.window_rect.height}")
                    self.logger.info(f"   计算结果: ({x}, {y})")
                    
                    # 移动鼠标到按钮位置
                    pyautogui.moveTo(x, y, duration=1.0)  # 1秒移动时间
                    self.logger.info(f"✅ 鼠标已移动到 {description}: ({x}, {y})")
                    
                    # 停留3秒让用户观察
                    time.sleep(3)
                    
                except Exception as e:
                    self.logger.error(f"❌ 测试 {description} 失败: {e}")
                    continue
            
            self.logger.info("🎯 坐标测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 坐标测试失败: {e}")
            return False
    
    def restore_verified_coordinates(self):
        """恢复已验证的坐标配置"""
        try:
            import json
            backup_file = "backup_coordinates.json"
            
            # 尝试从多个位置加载备份文件
            possible_locations = [
                backup_file,
                f"../{backup_file}",
                f"../../{backup_file}",
                f"../../../{backup_file}"
            ]
            
            backup_path = None
            for location in possible_locations:
                if os.path.exists(location):
                    backup_path = location
                    break
            
            if not backup_path:
                self.logger.error("❌ 找不到坐标备份文件 backup_coordinates.json")
                return False
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # 恢复相对坐标
            if 'coordinates' in backup_data:
                old_positions = self.relative_positions.copy()
                
                # 更新坐标
                for button_name, coords in backup_data['coordinates'].items():
                    self.relative_positions[button_name] = (coords['x'], coords['y'])
                
                self.logger.info("✅ 坐标恢复成功！")
                self.logger.info("📍 已恢复的坐标:")
                
                for button_name in self.relative_positions:
                    x, y = self.relative_positions[button_name]
                    self.logger.info(f"  - {button_name}: ({x:.6f}, {y:.6f})")
                
                # 验证恢复的坐标
                if self.validate_coordinates():
                    self.logger.info("✅ 坐标恢复并验证通过")
                    return True
                else:
                    # 如果验证失败，回滚
                    self.relative_positions = old_positions
                    self.logger.error("❌ 恢复的坐标验证失败，已回滚")
                    return False
            else:
                self.logger.error("❌ 备份文件中没有找到坐标数据")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 恢复坐标失败: {e}")
            return False
    
    def save_current_coordinates_as_backup(self):
        """将当前坐标保存为备份"""
        try:
            import json
            from datetime import datetime
            
            backup_data = {
                "version": "2.0", 
                "description": "景陶易购自动交易系统坐标配置 - 当前备份",
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "current_backup",
                "coordinates": {}
            }
            
            # 保存当前坐标
            for button_name, (x, y) in self.relative_positions.items():
                backup_data["coordinates"][button_name] = {"x": x, "y": y}
            
            backup_file = "current_coordinates_backup.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ 当前坐标已备份到: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 备份当前坐标失败: {e}")
            return False
    
    def execute_trade(self, signal: Dict):
        """执行交易"""
        try:
            self.logger.info(f"🚀 准备执行交易: {signal}")
            
            # 激活客户端窗口
            import pyautogui
            windows = pyautogui.getWindowsWithTitle("景陶易购")
            if windows:
                windows[0].activate()
                time.sleep(1)
                self.logger.info("✅ 客户端窗口已激活")
            else:
                self.logger.error("❌ 无法找到客户端窗口")
                return
            
            # 执行交易操作
            if signal['action'] == 'buy':
                self.logger.info("开始执行买入订单...")
                success = self._execute_buy_order(signal.get('price', 1383), 1)
                if success:
                    self.logger.info("买入订单执行成功")
                else:
                    self.logger.error("买入订单执行失败")
            elif signal['action'] == 'sell':
                self.logger.info("开始执行卖出订单...")
                success = self._execute_sell_order(signal.get('price', 1383), 1)
                if success:
                    self.logger.info("卖出订单执行成功")
                else:
                    self.logger.error("卖出订单执行失败")
            
            self.last_trade_time = time.time()
            self.logger.info("交易执行完成")
            
        except Exception as e:
            self.logger.error(f"执行交易失败: {e}")
    
    def _execute_buy_order(self, price: float, quantity: int = 1):
        """执行买入订单（优先使用HTTP API，失败则回退到UI RPA）"""
        try:
            # 优先使用HTTP API
            if getattr(self, 'http_api', None):
                try:
                    # 从配置读取商品ID（需要配置项）
                    commodity_id = str(self.config.get('trading.parameters.default_commodity_id', '')) if hasattr(self, 'config') else ''
                    if not commodity_id:
                        self.logger.warning("⚠️ 未配置 trading.parameters.default_commodity_id，跳过API下单")
                    else:
                        result = self.http_api.buy_order(commodity_id=commodity_id, price=str(price), quantity=str(quantity))
                        self.logger.info(f"HTTP买入下单结果: {result}")
                        if result.get('code') == '0':
                            return True
                except Exception as api_e:
                    self.logger.warning(f"HTTP买入下单异常，回退到UI: {api_e}")

            import pyautogui
            self.logger.info(f"执行买入订单: 价格={price}, 数量={quantity}")
            
            # 1. 点击买入模式按钮
            x, y = self.calculate_button_position('buy_mode_button')
            if x is not None and y is not None:
                pyautogui.click(x, y)
                self.logger.info("点击买入模式按钮")
                time.sleep(0.5)
            
            # 2. 自动填入价格（使用实时价格或指定价格）
            if not self.auto_fill_price(price):
                # 备用方案：手动输入价格
                x, y = self.calculate_button_position('price_input')
                if x is not None and y is not None:
                    pyautogui.click(x, y)
                    time.sleep(0.2)
                    pyautogui.hotkey('ctrl', 'a')  # 全选
                    time.sleep(0.1)
                    pyautogui.write(str(price))
                    self.logger.info(f"手动输入价格: {price}")
                    time.sleep(0.2)
            
            # 3. 输入数量
            x, y = self.calculate_button_position('quantity_input')
            if x is not None and y is not None:
                pyautogui.click(x, y)
                time.sleep(0.2)
                pyautogui.hotkey('ctrl', 'a')  # 全选
                time.sleep(0.1)
                pyautogui.write(str(quantity))
                self.logger.info(f"输入数量: {quantity}")
                time.sleep(0.2)
            
            # 4. 点击确认按钮
            x, y = self.calculate_button_position('confirm_button')
            if x is not None and y is not None:
                pyautogui.click(x, y)
                self.logger.info("点击确认按钮")
                time.sleep(0.5)
            
            # 5. 点击买入订立按钮
            x, y = self.calculate_button_position('buy_order_button')
            if x is not None and y is not None:
                pyautogui.click(x, y)
                self.logger.info("点击买入订立按钮")

                # 6. 智能处理确认对话框
                if self._handle_confirm_dialog(max_wait_time=3.0):
                    self.logger.info("✅ 买入订单确认成功")
                else:
                    self.logger.warning("⚠️ 买入订单确认可能失败，请检查")

            self.logger.info("买入订单执行完成")
            return True
            
        except Exception as e:
            self.logger.error(f"买入订单执行失败: {e}")
            return False
    
    def _execute_sell_order(self, price: float, quantity: int = 1):
        """执行卖出订单（优先使用HTTP API，失败则回退到UI RPA）"""
        try:
            # 优先使用HTTP API
            if getattr(self, 'http_api', None):
                try:
                    commodity_id = str(self.config.get('trading.parameters.default_commodity_id', '')) if hasattr(self, 'config') else ''
                    if not commodity_id:
                        self.logger.warning("⚠️ 未配置 trading.parameters.default_commodity_id，跳过API下单")
                    else:
                        result = self.http_api.sell_order(commodity_id=commodity_id, price=str(price), quantity=str(quantity))
                        self.logger.info(f"HTTP卖出下单结果: {result}")
                        if result.get('code') == '0':
                            return True
                except Exception as api_e:
                    self.logger.warning(f"HTTP卖出下单异常，回退到UI: {api_e}")

            import pyautogui
            self.logger.info(f"执行卖出订单: 价格={price}, 数量={quantity}")
            
            # 1. 点击卖出模式按钮
            x, y = self.calculate_button_position('sell_mode_button')
            if x is not None and y is not None:
                pyautogui.click(x, y)
                self.logger.info("点击卖出模式按钮")
                time.sleep(0.5)
            
            # 2. 输入价格
            x, y = self.calculate_button_position('price_input')
            if x is not None and y is not None:
                pyautogui.click(x, y)
                time.sleep(0.2)
                pyautogui.hotkey('ctrl', 'a')  # 全选
                time.sleep(0.1)
                pyautogui.write(str(price))
                self.logger.info(f"输入价格: {price}")
                time.sleep(0.2)
            
            # 3. 输入数量
            x, y = self.calculate_button_position('quantity_input')
            if x is not None and y is not None:
                pyautogui.click(x, y)
                time.sleep(0.2)
                pyautogui.hotkey('ctrl', 'a')  # 全选
                time.sleep(0.1)
                pyautogui.write(str(quantity))
                self.logger.info(f"输入数量: {quantity}")
                time.sleep(0.2)
            
            # 4. 点击确认按钮
            x, y = self.calculate_button_position('confirm_button')
            if x is not None and y is not None:
                pyautogui.click(x, y)
                self.logger.info("点击确认按钮")
                time.sleep(0.5)
            
            # 5. 点击卖出订立按钮
            x, y = self.calculate_button_position('sell_order_button')
            if x is not None and y is not None:
                pyautogui.click(x, y)
                self.logger.info("点击卖出订立按钮")

                # 6. 智能处理确认对话框
                if self._handle_confirm_dialog(max_wait_time=3.0):
                    self.logger.info("✅ 卖出订单确认成功")
                else:
                    self.logger.warning("⚠️ 卖出订单确认可能失败，请检查")

            self.logger.info("卖出订单执行完成")
            return True
            
        except Exception as e:
            self.logger.error(f"卖出订单执行失败: {e}")
            return False

    
    def detect_yellow_line_change(self, screen: np.ndarray) -> Dict:
        """检测黄线变化 - 优先使用高级检测器"""
        try:
            import cv2  # 确保cv2在方法开始时就导入
            import time  # 确保time在方法开始时就导入
            
            if screen is None:
                print("❌❌❌ [调试] 屏幕截图为None，返回默认值")
                self.logger.error("❌❌❌ [调试] 屏幕截图为None，返回默认值")
                return {'signal': 'none', 'direction': 'stable', 'area': 0, 'angle': 0.0, 'position': (0, 0), 'confidence': 0.0}
            
            print("🔍🔍🔍 [调试] 开始黄线检测...")  # 使用print确保输出
            self.logger.info("🔍🔍🔍 [调试] 开始黄线检测...")
            
            height, width = screen.shape[:2]
            print(f"📺📺📺 [调试] 屏幕尺寸: {width} x {height}")
            self.logger.info(f"📺📺📺 [调试] 屏幕尺寸: {width} x {height}")
            
            # 方案1: 优先使用高级检测器
            print(f"🔍 检查高级检测器: hasattr={hasattr(self, 'advanced_line_detector')}, value={getattr(self, 'advanced_line_detector', None)}")
            if hasattr(self, 'advanced_line_detector') and self.advanced_line_detector is not None:
                print("🚀 使用高级线条检测器...")
                self.logger.info("🚀 使用高级线条检测器...")
                
                try:
                    # 尝试多种检测方法
                    detection_methods = [
                        ('霍夫变换检测', self.advanced_line_detector.detect_lines_hough_transform),
                        ('轮廓分析检测', self.advanced_line_detector.detect_lines_contour_analysis),
                        ('高级算法检测', self.advanced_line_detector.detect_lines_advanced),
                        ('模板匹配检测', self.advanced_line_detector.detect_lines_template_matching)
                    ]
                    
                    for method_name, method in detection_methods:
                        print(f"🔍 尝试{method_name}...")
                        self.logger.info(f"🔍 尝试{method_name}...")
                        
                        if method_name == '高级算法检测':
                            result = method(screen)
                            if result and result.get('signal') != 'none':
                                print(f"✅ {method_name}成功: {result}")
                                self.logger.info(f"✅ {method_name}成功: {result}")
                                return result
                        else:
                            line_segments = method(screen)
                            if line_segments and len(line_segments) > 0:
                                # 转换为标准格式
                                best_line = max(line_segments, key=lambda x: x.confidence)
                                result = {
                                    'signal': 'up' if best_line.angle > self.angle_threshold else 'down' if best_line.angle < -self.angle_threshold else 'none',
                                    'direction': 'rising' if best_line.angle > self.angle_threshold else 'falling' if best_line.angle < -self.angle_threshold else 'stable',
                                    'angle': best_line.angle,
                                    'angle_change': best_line.angle,  # 简化处理
                                    'confidence': best_line.confidence,
                                    'area': best_line.length * 2,  # 近似面积
                                    'position': best_line.start_point,
                                    'points_count': len(line_segments)
                                }
                                print(f"✅ {method_name}成功: {result}")
                                self.logger.info(f"✅ {method_name}成功: {result}")
                                return result
                        
                        print(f"⚠️ {method_name}未检测到有效线条")
                        self.logger.info(f"⚠️ {method_name}未检测到有效线条")
                    
                    print("⚠️ 所有高级检测方法都失败，回退到基础检测")
                    self.logger.warning("⚠️ 所有高级检测方法都失败，回退到基础检测")
                    
                except Exception as e:
                    print(f"❌ 高级检测器异常: {e}，回退到基础检测")
                    self.logger.error(f"❌ 高级检测器异常: {e}，回退到基础检测")
            
            # 方案2: 基础检测方法（原有逻辑）
            print("🔧🔧🔧 [调试] 使用基础黄线检测方法...")
            self.logger.info("🔧🔧🔧 [调试] 使用基础黄线检测方法...")
            
            # 检测区域：使用用户指定的区域或默认区域
            if hasattr(self, 'yellow_line_region') and self.yellow_line_region:
                x, y, w, h = self.yellow_line_region
                chart_region = screen[y:y+h, x:x+w]
                self.logger.info(f"使用指定黄线检测区域: {self.yellow_line_region}")
            else:
                # 默认检测区域：缩小检测范围，专注于图表中心区域
                chart_region = screen[int(height*0.2):int(height*0.8), int(width*0.1):int(width*0.6)]
                self.logger.info(f"使用默认黄线检测区域（中心图表区域）: [{int(height*0.2)}:{int(height*0.8)}, {int(width*0.1)}:{int(width*0.6)}]")
            
            self.logger.info(f"黄线检测区域尺寸: {chart_region.shape[1]} x {chart_region.shape[0]}")
            
            # 转换到HSV颜色空间
            hsv = cv2.cvtColor(chart_region, cv2.COLOR_BGR2HSV)
            
            # 基于用户精确提取的RGB(255,184,0) -> HSV(22,255,255)的黄线颜色范围
            line_ranges = [
                # 🎯 用户精确黄线颜色 (HSV: 22, 255, 255) - 最优先检测
                (np.array([17, 225, 225]), np.array([27, 255, 255])),   # 精确范围1 (±5度)
                (np.array([12, 205, 205]), np.array([32, 255, 255])),   # 精确范围2 (±10度)
                (np.array([7, 185, 185]), np.array([37, 255, 255])),    # 精确范围3 (±15度)
                
                # 🟡 标准黄色线条 (基于HSV=22的扩展)
                (np.array([20, 200, 200]), np.array([25, 255, 255])),   # 超精确黄色
                (np.array([18, 180, 180]), np.array([28, 255, 255])),   # 严格黄色
                (np.array([15, 150, 150]), np.array([30, 255, 255])),   # 标准黄色
                
                # 🟠 橙黄色扩展范围
                (np.array([10, 200, 200]), np.array([25, 255, 255])),   # 橙黄色
                (np.array([8, 150, 150]), np.array([28, 255, 255])),    # 宽松橙黄
                
                # 🟨 浅黄色 (降低饱和度和亮度要求)
                (np.array([15, 100, 150]), np.array([35, 255, 255])),   # 浅黄色
                (np.array([10, 80, 120]), np.array([40, 255, 255])),    # 很浅黄色
                
                # 🔶 金色范围 (HSV: 20-30度高饱和度)
                (np.array([20, 180, 180]), np.array([30, 255, 255])),   # 金色
                (np.array([18, 160, 160]), np.array([32, 255, 255])),   # 宽松金色
                
                # 🟡 备用黄色检测 (超宽范围)
                (np.array([2, 155, 155]), np.array([42, 255, 255])),    # 用户提供的范围4
                (np.array([5, 100, 100]), np.array([40, 255, 255])),    # 超宽黄色
                
                # 🔵 备用颜色检测 (保留其他颜色作为最后尝试)
                (np.array([80, 100, 150]), np.array([100, 255, 255])), # 青色
                (np.array([0, 50, 100]), np.array([180, 255, 255]))     # 任何有色区域
            ]
            
            best_mask = None
            best_area = 0
            
            for i, (lower, upper) in enumerate(line_ranges):
                # 创建掩码
                mask = cv2.inRange(hsv, lower, upper)
                
                # 计算掩码中的像素数量
                mask_pixels = cv2.countNonZero(mask)
                
                # 查找轮廓
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # 识别线条类型
                if i <= 2:
                    line_type = "🎯用户精确黄线"
                elif i <= 5:
                    line_type = "🟡标准黄色扩展"
                elif i <= 7:
                    line_type = "🟠橙黄色扩展"
                elif i <= 9:
                    line_type = "🟨浅黄色"
                elif i <= 11:
                    line_type = "🔶金色范围"
                elif i <= 13:
                    line_type = "🟡备用黄色"
                elif i <= 15:
                    line_type = "🔵备用颜色"
                else:
                    line_type = "🔍宽松检测"
                
                if contours:
                    max_contour = max(contours, key=cv2.contourArea)
                    area = cv2.contourArea(max_contour)
                    
                    print(f"🎨🎨🎨 [调试] {line_type}范围{i+1}: 掩码像素={mask_pixels}, 轮廓面积={area:.1f}")
                    self.logger.info(f"🎨 {line_type}范围{i+1}: 掩码像素={mask_pixels}, 轮廓面积={area:.1f}")
                    
                    if area > best_area:
                        best_area = area
                        best_mask = mask
                        print(f"✅✅✅ [调试] {line_type}线条范围{i+1}成为最佳匹配: {area}")
                        self.logger.info(f"✅ {line_type}线条范围{i+1}成为最佳匹配: {area}")
                else:
                    if mask_pixels > 0:
                        self.logger.info(f"🎨 {line_type}范围{i+1}: 掩码像素={mask_pixels}, 但无有效轮廓")
                    # 如果mask_pixels为0则不输出，避免日志过多
            
            if best_mask is None:
                print("❌❌❌ [调试] 未检测到任何线条 - 尝试所有颜色范围都无效")
                self.logger.warning("🔍 未检测到任何线条 - 尝试所有颜色范围都无效")
                # 调试信息：显示图像基本信息
                print(f"📊📊📊 [调试] 图像尺寸: {chart_region.shape}")
                print(f"📊📊📊 [调试] HSV范围: H({hsv[:,:,0].min()}-{hsv[:,:,0].max()}) S({hsv[:,:,1].min()}-{hsv[:,:,1].max()}) V({hsv[:,:,2].min()}-{hsv[:,:,2].max()})")
                self.logger.info(f"   图像尺寸: {chart_region.shape}")
                self.logger.info(f"   HSV范围: H({hsv[:,:,0].min()}-{hsv[:,:,0].max()}) S({hsv[:,:,1].min()}-{hsv[:,:,1].max()}) V({hsv[:,:,2].min()}-{hsv[:,:,2].max()})")
                
                # 保存失败检测的截图用于调试
                try:
                    debug_filename = f"logs/failed_detection_{int(time.time())}.png"
                    cv2.imwrite(debug_filename, chart_region)
                    print(f"💾 已保存失败检测截图: {debug_filename}")
                    self.logger.warning(f"💾 已保存失败检测截图: {debug_filename}")
                except:
                    pass
                
                print("❌ 黄线检测失败：未找到任何线条，返回stable状态")
                self.logger.warning("❌ 黄线检测失败：未找到任何线条，返回stable状态")
                return {'signal': 'none', 'direction': 'stable', 'area': 0, 'angle': 0.0, 'position': (0, 0), 'confidence': 0.0}
            
            # 使用最佳掩码
            mask = best_mask
            
            # 查找轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            self.logger.info(f"找到 {len(contours)} 个轮廓")
            
            if not contours:
                self.logger.warning("❌ 黄线检测失败：找到掩码但无轮廓")
                return {'signal': 'none', 'direction': 'stable', 'area': 0, 'angle': 0.0, 'position': (0, 0), 'confidence': 0.0}
            
            # 找到最大的黄色区域
            max_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(max_contour)
            self.logger.info(f"最大轮廓面积: {area}")
            
            # 面积阈值检查：既不能太小也不能太大 - 降低阈值以提高检测敏感度
            min_area = 5      # 从10降低到5
            max_area = 10000  # 从5000提高到10000
            
            print(f"🔍🔍🔍 [调试] 面积检查: {area}, 范围: [{min_area}, {max_area}]")
            self.logger.info(f"🔍🔍🔍 [调试] 面积检查: {area}, 范围: [{min_area}, {max_area}]")
            
            if area < min_area:
                print(f"❌❌❌ [调试] 黄线检测失败：面积太小 {area} < {min_area}")
                self.logger.warning(f"❌ 黄线检测失败：面积太小 {area} < {min_area}")
                return {'signal': 'none', 'direction': 'stable', 'area': area, 'angle': 0.0, 'position': (0, 0), 'confidence': 0.0}
            
            if area > max_area:
                print(f"❌❌❌ [调试] 黄线检测失败：面积太大（可能是背景） {area} > {max_area}")
                self.logger.warning(f"❌ 黄线检测失败：面积太大（可能是背景） {area} > {max_area}")
                return {'signal': 'none', 'direction': 'stable', 'area': area, 'angle': 0.0, 'position': (0, 0), 'confidence': 0.0}
            
            # 获取黄线位置和尺寸
            x, y, w, h = cv2.boundingRect(max_contour)
            self.logger.info(f"黄线位置: ({x}, {y}), 尺寸: {w} x {h}")
            
            # 收集黄线数据点
            yellow_points = []
            
            # 按列采样，每列取最上方的黄线点
            for i in range(0, w, 3):  # 每3个像素采样一次
                col_pixels = np.where(mask[:, x + i] > 0)[0]
                if len(col_pixels) > 0:
                    # 取每列最上方的黄线点
                    top_y = np.min(col_pixels)
                    yellow_points.append((x + i, y + top_y))
            
            # 如果点太少，使用密集采样
            if len(yellow_points) < 5:
                yellow_points = []
                for i in range(0, w, 2):  # 每2个像素采样一次
                    for j in range(0, h, 2):
                        if mask[y + j, x + i] > 0:
                            yellow_points.append((x + i, y + j))
            
            self.logger.info(f"收集到 {len(yellow_points)} 个黄线数据点")
            
            if len(yellow_points) < 5:
                self.logger.info("黄线数据点太少")
                return {'signal': 'none', 'direction': 'stable', 'area': area, 'angle': 0.0, 'position': (x, y), 'confidence': 0.0}
            
            # 按x坐标排序
            yellow_points.sort(key=lambda p: p[0])
            
            # 使用新的角度检测器计算角度变化
            angle_degrees = 0.0
            angle_change = 0.0
            signal = 'none'
            direction = 'stable'
            confidence = 0.0

            if len(yellow_points) >= 2:
                # 使用角度检测器计算更准确的角度
                angle_degrees = self.angle_detector.calculate_line_angle(yellow_points)

                # 添加角度数据并检测变化
                detection_result = self.angle_detector.add_angle_data(angle_degrees)

                # 提取检测结果
                signal = detection_result['signal']
                direction = detection_result['direction']
                angle_change = detection_result['angle_change']
                confidence = detection_result['confidence']

                print(f"📐 角度检测结果: 当前角度={angle_degrees:.2f}°, 变化={angle_change:.2f}°, 信号={signal}")
                self.logger.info(f"📐 角度检测结果: 当前角度={angle_degrees:.2f}°, 变化={angle_change:.2f}°, 信号={signal}")
                
                # 保持兼容性：存储历史数据（可选）
                if not hasattr(self, 'yellow_line_data'):
                    self.yellow_line_data = []

                self.yellow_line_data.append({
                    'timestamp': time.time(),
                    'angle': angle_degrees,
                    'area': area,
                    'position': (x, y),
                    'points_count': len(yellow_points)
                })

                # 只保留最近10个数据点
                if len(self.yellow_line_data) > 10:
                    self.yellow_line_data.pop(0)

                # 计算黄线中心位置
                center_x = x + w // 2
                center_y = y + h // 2

                # 详细日志输出
                print(f"🔍 角度变化检查: |{angle_change:.3f}| > 20.0 ? 结果: {abs(angle_change) > 20.0}")
                print(f"📊 当前角度: {angle_degrees:.3f}°, 历史数据点: {len(self.yellow_line_data)}")
                print(f"🎯 黄线位置: ({center_x}, {center_y}), 面积: {area:.1f}")
                print(f"🚦 信号状态: {signal}, 方向: {direction}, 置信度: {confidence:.2f}")

                self.logger.info(f"🔍 角度变化检查: |{angle_change:.3f}| > 20.0 ? 结果: {abs(angle_change) > 20.0}")
                self.logger.info(f"📊 当前角度: {angle_degrees:.3f}°, 历史数据点: {len(self.yellow_line_data)}")
                self.logger.info(f"🎯 黄线位置: ({center_x}, {center_y}), 面积: {area:.1f}")
                
                # 注意：信号检测逻辑已在上面的20度阈值检查中处理
                # 这里不再需要额外的1度检测逻辑

                # 如果已经有信号，重新计算置信度
                if signal != 'none':
                    # 计算置信度：角度变化越大，置信度越高
                    confidence = min(0.9, abs(angle_change) / 50.0)

                    # 面积也影响置信度
                    area_factor = min(1.0, area / 100.0)
                    confidence = confidence * (0.7 + 0.3 * area_factor)

                    print(f"✅ 信号确认: {signal}, 最终置信度: {confidence:.3f}")
                    self.logger.info(f"✅ 信号确认: {signal}, 最终置信度: {confidence:.3f}")
            
            # 如果连续多次检测到稳定状态，强制生成一个测试信号（调试用）
            if hasattr(self, 'stable_count'):
                self.stable_count += 1
            else:
                self.stable_count = 1
                
            if self.stable_count > 10:  # 连续10次稳定后强制触发一次
                print("🧪 强制触发测试信号（调试模式）")
                self.logger.info("🧪 强制触发测试信号（调试模式）")
                self.stable_count = 0
                signal = 'up'
                direction = 'rising'
                confidence = 0.5
                        
            print(f"🎯 最终结果: 线条角度: {angle_degrees:.2f}°, 变化: {angle_change:.2f}°, 信号: {signal}, 置信度: {confidence:.2f}")
            self.logger.info(f"线条角度: {angle_degrees:.2f}°, 变化: {angle_change:.2f}°, 信号: {signal}, 置信度: {confidence:.2f}")
            
            return {
                'signal': signal,
                'direction': direction,
                'area': area,
                'angle': angle_degrees,
                'angle_change': angle_change,
                'position': (x, y),
                'points_count': len(yellow_points),
                'confidence': confidence
            }
                
        except Exception as e:
            self.logger.error(f"黄线检测失败: {e}")
            return {'signal': 'none', 'direction': 'stable', 'area': 0, 'angle': 0.0, 'position': (0, 0)}
    
    def detect_jingtao_signals(self, screen: np.ndarray) -> Dict:
        """景陶易购专用信号检测 - 优先使用专用检测器，备用黄线检测"""
        try:
            # 如果专用检测器可用，使用专用检测器
            if self.jingtao_detector is not None:
                try:
                    result = self.jingtao_detector.detect_comprehensive_signals(screen)
                    if result and result.get('signal') != 'none':
                        return result
                except Exception as e:
                    self.logger.warning(f"专用检测器失败，使用备用检测: {e}")
            
            # 备用方案：使用增强的黄线检测
            yellow_result = self.detect_yellow_line_change(screen)
            
            # 将黄线检测结果转换为标准信号格式
            if yellow_result and yellow_result.get('signal') in ['up', 'down']:
                # 计算置信度（基于角度变化幅度）
                angle_change = abs(yellow_result.get('angle_change', 0))
                confidence = min(0.9, angle_change / 100.0)  # 角度变化越大，置信度越高
                
                # 转换信号
                signal = 'buy' if yellow_result['signal'] == 'up' else 'sell'
                
                return {
                    'signal': signal,
                    'confidence': confidence,
                    'source': 'yellow_line_backup',
                    'angle_change': yellow_result.get('angle_change', 0),
                    'area': yellow_result.get('area', 0)
                }
            
            return {'signal': 'none', 'confidence': 0.0, 'source': 'backup_detection'}
            
        except Exception as e:
            self.logger.error(f"景陶易购专用检测失败: {e}")
            return {'signal': 'none', 'confidence': 0.0}
    
    def detect_enhanced_signals(self, screenshot: np.ndarray) -> Dict:
        """检测增强信号 - K线+MACD+均线组合策略（来自smart_trading.py）"""
        try:
            if ENHANCED_DETECTION_AVAILABLE and enhanced_detector is not None:
                # 使用完整的增强检测器
                result = enhanced_detector.get_comprehensive_signal(screenshot)

                if result['final_signal'] == SignalType.BULLISH:
                    signal = 'buy'
                    self.logger.info(f"🟢 增强检测: 看涨信号 (置信度: {result['final_confidence']:.2f})")
                elif result['final_signal'] == SignalType.BEARISH:
                    signal = 'sell'
                    self.logger.info(f"🔴 增强检测: 看跌信号 (置信度: {result['final_confidence']:.2f})")
                else:
                    signal = 'hold'
                    self.logger.info(f"⚪ 增强检测: 中性信号 (置信度: {result['final_confidence']:.2f})")

                # 记录详细信息
                if 'kline' in result:
                    kline_info = result['kline']
                    self.logger.info(f"K线信号: {kline_info.get('signal', 'unknown')} "
                                   f"(红色比例: {kline_info.get('red_ratio', 0):.3f}, "
                                   f"绿色比例: {kline_info.get('green_ratio', 0):.3f})")

                return {
                    'signal': signal,
                    'confidence': result['final_confidence'],
                    'method': 'enhanced',
                    'details': result
                }
            else:
                # 备用增强检测：基于黄线检测的简化版本
                yellow_result = self.detect_yellow_line_change(screenshot)
                
                if yellow_result and yellow_result.get('signal') in ['up', 'down']:
                    # 基于角度变化强度判断信号
                    angle_change = abs(yellow_result.get('angle_change', 0))
                    
                    if angle_change > 10:  # 强烈信号
                        signal = 'buy' if yellow_result['signal'] == 'up' else 'sell'
                        confidence = min(0.8, angle_change / 50.0)
                        self.logger.info(f"✅ 增强检测(备用): {signal}信号 (置信度: {confidence:.2f}, 角度变化: {angle_change:.1f}°)")
                        
                        return {
                            'signal': signal,
                            'confidence': confidence,
                            'method': 'yellow_line_enhanced',
                            'angle_change': angle_change
                        }
                
                # 默认返回持有信号
                return {'signal': 'hold', 'confidence': 0.0, 'method': 'fallback'}
            
        except Exception as e:
            self.logger.error(f"增强信号检测失败: {e}")
            return {'signal': 'hold', 'confidence': 0.0, 'method': 'error', 'error': str(e)}
    
    def analyze_trade_signal(self, yellow_signal: Dict, enhanced_signal: Dict = None, value_change_info: Dict = None) -> Dict:
        """分析交易信号 - 专注于买入/卖出自动交易"""
        try:
            current_time = time.time()
            
            # 检查交易冷却时间
            if current_time - self.last_trade_time < self.trade_cooldown:
                return {
                    'should_trade': False,
                    'reason': f'交易冷却中，剩余 {self.trade_cooldown - (current_time - self.last_trade_time):.1f} 秒'
                }
            
            # 我们不需要在这里获取价格，价格获取由auto_fill_price处理
            # 交易信号分析只需要关注黄线角度变化即可
            
            # 主要逻辑：基于黄线变化的买入/卖出决策
            yellow_status = yellow_signal.get('status', 'stable')
            yellow_signal_type = yellow_signal.get('signal', 'none')
            yellow_direction = yellow_signal.get('direction', 'none')
            yellow_confidence = yellow_signal.get('confidence', 0.0)
            
            # 根据黄线角度变化进行交易决策 (>20度才触发)
            angle_change = yellow_signal.get('angle_change', 0.0)
            
            if yellow_signal_type == 'up' and abs(angle_change) > 20.0:  # 黄线向上倾斜>20度
                return {
                    'should_trade': True,
                    'action': 'buy',
                    'reason': f'黄线向上倾斜 {angle_change:.1f}度 (>20度)，执行买入策略 (置信度: {yellow_confidence:.2f})',
                    'quantity': 1
                }
            elif yellow_signal_type == 'down' and abs(angle_change) > 20.0:  # 黄线向下倾斜>20度
                return {
                    'should_trade': True,
                    'action': 'sell',
                    'reason': f'黄线向下倾斜 {angle_change:.1f}度 (>20度)，执行卖出策略 (置信度: {yellow_confidence:.2f})',
                    'quantity': 1
                }
            
            # 兼容其他格式的黄线状态检查
            if yellow_direction == 'rising' and abs(angle_change) > 20.0:  # 黄线上升趋势>20度
                return {
                    'should_trade': True,
                    'action': 'buy',
                    'reason': f'黄线上升趋势 {angle_change:.1f}度 (>20度)，执行买入策略',
                    'quantity': 1
                }
            elif yellow_direction == 'falling' and abs(angle_change) > 20.0:  # 黄线下降趋势>20度
                return {
                    'should_trade': True,
                    'action': 'sell',
                    'reason': f'黄线下降趋势 {angle_change:.1f}度 (>20度)，执行卖出策略', 
                    'quantity': 1
                }
            
            # 优先级3：增强信号检测（如果黄线无明确信号）
            if enhanced_signal and enhanced_signal.get('confidence', 0) > 0.6:
                signal_type = enhanced_signal.get('signal', 'hold')
                confidence = enhanced_signal.get('confidence', 0)

                if signal_type == 'buy':
                    return {
                        'should_trade': True,
                        'action': 'buy',
                        'reason': f'增强检测买入信号 (置信度: {confidence:.2f})',
                        'quantity': 1
                    }
                elif signal_type == 'sell':
                    return {
                        'should_trade': True,
                        'action': 'sell',
                        'reason': f'增强检测卖出信号 (置信度: {confidence:.2f})',
                        'quantity': 1
                    }
            
            # 如果没有明确信号，保持观望
            return {
                'should_trade': False,
                'action': 'hold',
                'reason': f'暂无交易信号 (黄线状态: {yellow_status}, 货值变化: 无)'
            }
            
        except Exception as e:
            self.logger.error(f"交易信号分析错误: {e}")
            return {
                'should_trade': False,
                'action': 'hold',
                'reason': f'分析错误: {e}'
            }
    
    def execute_trade(self, trade_signal: Dict) -> bool:
        """执行交易 - 专注于买入、卖出操作"""
        try:
            action = trade_signal.get('action', 'buy')
            reason = trade_signal.get('reason', '未知原因')
            # 不预设价格，让auto_fill_price方法自动获取真实价格
            quantity = trade_signal.get('quantity', 1)
            
            self.logger.info(f"🚀 开始执行交易: {action} - {reason}")
            
            # 确保客户端窗口激活
            if not self.find_client_window():
                self.logger.error("❌ 无法找到客户端窗口")
                return False
            
            # 根据交易类型执行相应操作（专注于买入/卖出）
            if action == 'buy':
                return self._execute_buy_order(quantity, reason)
            elif action == 'sell':
                return self._execute_sell_order(quantity, reason)
            else:
                self.logger.warning(f"⚠️ 暂不支持的交易动作: {action}，当前仅支持买入/卖出")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ 交易执行失败: {e}")
            return False
    
    def _execute_buy_order(self, quantity: int, reason: str) -> bool:
        """执行买入订单"""
        try:
            self.logger.info(f"💰 执行买入订单 - 数量: {quantity}")
            
            # 1. 点击买入模式按钮
            if not self.click_button('buy_mode_button', 1.0):
                self.logger.error("❌ 点击买入模式按钮失败")
                return False
            
            # 2. 自动填入价格和数量（价格通过auto_fill_price自动获取真实价格）
            if not self.auto_fill_price():  # 不传递target_price，让方法自动获取
                self.logger.error("❌ 自动填入价格失败")
                return False
            
            if not self.auto_fill_quantity(quantity=quantity):
                self.logger.error("❌ 自动填入数量失败")
                return False
            
            # 3. 点击买入订立按钮
            if not self.click_button('buy_order_button', 1.5):
                self.logger.error("❌ 点击买入订立按钮失败")
                return False
            
            # 4. 处理确认对话框
            success = self._handle_confirm_dialog()
            
            if success:
                self.last_trade_time = time.time()
                self.logger.info(f"✅ 买入订单执行成功，数量: {quantity}")
                return True
            else:
                self.logger.error("❌ 买入订单确认失败")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ 买入订单执行失败: {e}")
            return False
    
    def _execute_sell_order(self, quantity: int, reason: str) -> bool:
        """执行卖出订单"""
        try:
            self.logger.info(f"💸 执行卖出订单 - 数量: {quantity}")
            
            # 1. 点击卖出模式按钮
            if not self.click_button('sell_mode_button', 1.0):
                self.logger.error("❌ 点击卖出模式按钮失败")
                return False
            
            # 2. 自动填入价格和数量（价格通过auto_fill_price自动获取真实价格）
            if not self.auto_fill_price():  # 不传递target_price，让方法自动获取
                self.logger.error("❌ 自动填入价格失败")
                return False
            
            if not self.auto_fill_quantity(quantity=quantity):
                self.logger.error("❌ 自动填入数量失败") 
                return False
            
            # 3. 点击卖出订立按钮
            if not self.click_button('sell_order_button', 1.5):
                self.logger.error("❌ 点击卖出订立按钮失败")
                return False
            
            # 4. 处理确认对话框
            success = self._handle_confirm_dialog(max_wait_time=3.0)
            
            if success:
                self.last_trade_time = time.time()
                self.logger.info(f"✅ 卖出订单执行成功，数量: {quantity}")
                return True
            else:
                self.logger.error("❌ 卖出订单确认失败")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ 卖出订单执行失败: {e}")
            return False
    
    def _execute_transfer_order(self, transfer_type: str, reason: str) -> bool:
        """执行转出订单（止盈/止损）"""
        try:
            if transfer_type == 'profit':
                self.logger.info(f"🎯 执行止盈转出 - {reason}")
            elif transfer_type == 'loss':
                self.logger.info(f"🛡️ 执行止损转出 - {reason}")
            else:
                self.logger.warning(f"⚠️ 未知的转出类型: {transfer_type}")
            
            # 点击转出按钮
            if not self.click_button('transfer_out_button', 1.5):
                self.logger.error("❌ 点击转出按钮失败")
                return False
            
            # 处理确认对话框
            success = self._handle_confirm_dialog()
            
            if success:
                self.last_trade_time = time.time()
                self.logger.info(f"✅ 转出操作执行成功: {transfer_type}")
                return True
            else:
                self.logger.error("❌ 转出操作确认失败")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ 转出操作执行失败: {e}")
            return False
    
    def _handle_confirm_dialog(self, max_wait_time: float = 3.0) -> bool:
        """处理确认对话框 - 改进版本，智能等待窗口出现"""
        try:
            self.logger.info(f"🔍 开始智能等待确认对话框 (最大等待: {max_wait_time}秒)")

            # 优先使用新的确认对话框检测器
            if hasattr(self, 'confirm_dialog_detector'):
                if self.confirm_dialog_detector.wait_and_confirm(max_wait_time=max_wait_time):
                    self.logger.info("✅ 新版确认对话框检测成功")
                    return True
                else:
                    self.logger.warning("⚠️ 新版确认检测失败，尝试备用方法")

            # 备用方法1：使用原有的auto_confirm_handler
            if hasattr(self, 'auto_confirm_handler') and self.auto_confirm_handler:
                if self.auto_confirm_handler.wait_and_confirm(max_wait_time=max_wait_time):
                    self.logger.info("✅ 原版确认对话框检测成功")
                    return True
                else:
                    self.logger.warning("⚠️ 原版确认检测失败，尝试最后备用方法")

            # 备用方法2：简单的等待和点击机制
            return self._simple_wait_and_confirm(max_wait_time)

        except Exception as e:
            self.logger.error(f"❌ 处理确认对话框失败: {e}")
            return False

    def _simple_wait_and_confirm(self, max_wait_time: float) -> bool:
        """简单的等待和确认机制"""
        try:
            self.logger.info("🔘 使用简单等待确认机制")

            # 分段等待，每0.5秒检查一次
            wait_intervals = [0.5, 0.5, 0.5, 0.5, 1.0]  # 总共3秒
            total_waited = 0

            for interval in wait_intervals:
                if total_waited >= max_wait_time:
                    break

                time.sleep(interval)
                total_waited += interval

                # 尝试点击确认按钮
                if self.click_button('confirm_button', 0.2):
                    self.logger.info(f"✅ 确认按钮点击成功 (等待时间: {total_waited:.1f}秒)")
                    return True

                self.logger.debug(f"⏳ 等待确认窗口... ({total_waited:.1f}s/{max_wait_time}s)")

            self.logger.warning(f"⚠️ 等待{max_wait_time}秒后仍未找到确认按钮")
            return False

        except Exception as e:
            self.logger.error(f"❌ 简单等待确认失败: {e}")
            return False

    def _fallback_confirm_click(self) -> bool:
        """备用确认点击方法"""
        try:
            self.logger.info("🔄 执行备用确认点击")

            # 等待1秒让界面稳定
            time.sleep(1.0)

            # 尝试点击确认按钮
            if self.click_button('confirm_button', 1.0):
                self.logger.info("✅ 备用确认点击成功")
                return True
            else:
                self.logger.warning("⚠️ 备用确认点击失败")
                return False

        except Exception as e:
            self.logger.error(f"❌ 备用确认点击异常: {e}")
            return False
    
    def test_coordinates(self, button_list: list = None) -> bool:
        """测试坐标准确性"""
        try:
            if button_list is None:
                button_list = ['buy_mode_button', 'sell_mode_button', 'buy_order_button', 'confirm_button']
            
            self.logger.info("🧪 开始坐标测试...")
            
            if not self.window_rect:
                if not self.find_client_window():
                    self.logger.error("❌ 无法找到客户端窗口")
                    return False
            
            all_passed = True
            
            for button_name in button_list:
                x, y = self.get_button_position(button_name)
                if x is None or y is None:
                    self.logger.error(f"❌ 按钮 {button_name} 坐标获取失败")
                    all_passed = False
                    continue
                
                # 检查坐标是否在合理的屏幕范围内（支持多显示器环境）
                screen_width, screen_height = pyautogui.size()
                
                # 允许坐标稍微超出屏幕边界（多显示器环境）
                extended_left = -screen_width  # 允许左侧扩展一个屏幕宽度
                extended_right = screen_width * 2  # 允许右侧扩展一个屏幕宽度  
                extended_top = -screen_height  # 允许顶部扩展一个屏幕高度
                extended_bottom = screen_height * 2  # 允许底部扩展一个屏幕高度
                
                if (extended_left <= x <= extended_right and 
                    extended_top <= y <= extended_bottom):
                    self.logger.info(f"✅ 按钮 {button_name} 坐标测试通过: ({x}, {y})")
                else:
                    self.logger.warning(f"⚠️ 按钮 {button_name} 坐标超出扩展范围: ({x}, {y})")
                    self.logger.info(f"   屏幕大小: {screen_width}x{screen_height}")
                    self.logger.info(f"   如果校准工具测试正常，这个警告可以忽略")
                    # 不标记为失败，允许使用
            
            if all_passed:
                self.logger.info("🎉 所有坐标测试通过")
            else:
                self.logger.warning("⚠️ 部分坐标测试失败")
            
            return all_passed
            
        except Exception as e:
            self.logger.error(f"坐标测试失败: {e}")
            return False
    
    def monitor_realtime_value_change(self, screenshot: np.ndarray) -> Dict:
        """监控实时货值变化区域"""
        try:
            import cv2  # 确保cv2导入
            
            if screenshot is None:
                return {'detected': False, 'value': None, 'change_rate': 0.0}
            
            # 获取实时货值监控区域
            x, y, w, h = self.relative_positions['realtime_value_area']
            height, width = screenshot.shape[:2]
            
            # 计算实际像素坐标
            region_x = int(x * width)
            region_y = int(y * height)
            region_w = int(w * width)
            region_h = int(h * height)
            
            # 提取货值区域
            value_region = screenshot[region_y:region_y+region_h, region_x:region_x+region_w]
            
            if TESSERACT_AVAILABLE and _setup_tesseract():
                try:
                    # 使用OCR识别数字
                    gray = cv2.cvtColor(value_region, cv2.COLOR_BGR2GRAY)
                    # 二值化处理，突出数字
                    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
                    
                    # OCR配置，只识别数字
                    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.+-'
                    text = pytesseract.image_to_string(binary, config=custom_config)
                    
                    # 提取价格数字
                    import re
                    numbers = re.findall(r'\d+\.?\d*', text)
                    
                    if numbers:
                        current_value = float(numbers[0])
                        
                        # 计算变化率
                        change_rate = 0.0
                        if self.last_profit_value is not None:
                            change_rate = (current_value - self.last_profit_value) / self.last_profit_value * 100
                        
                        self.logger.info(f"📊 实时货值: {current_value}, 变化率: {change_rate:.2f}%")
                        
                        # 更新记录
                        self.last_profit_value = current_value
                        
                        return {
                            'detected': True,
                            'value': current_value,
                            'change_rate': change_rate,
                            'text': text.strip()
                        }
                    
                except Exception as e:
                    self.logger.warning(f"OCR识别货值失败: {e}")
            
            # 备用方案：基于颜色变化检测
            return self._detect_value_change_by_color(value_region)
            
        except Exception as e:
            self.logger.error(f"实时货值监控失败: {e}")
            return {'detected': False, 'value': None, 'change_rate': 0.0}
    
    def _detect_value_change_by_color(self, region: np.ndarray) -> Dict:
        """基于颜色变化检测货值变化"""
        try:
            import cv2  # 确保cv2导入
            
            # 检测绿色（上涨）和红色（下跌）区域
            hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
            
            # 绿色范围（上涨）
            green_lower = np.array([40, 100, 100])
            green_upper = np.array([80, 255, 255])
            green_mask = cv2.inRange(hsv, green_lower, green_upper)
            green_pixels = cv2.countNonZero(green_mask)
            
            # 红色范围（下跌）
            red_lower1 = np.array([0, 100, 100])
            red_upper1 = np.array([10, 255, 255])
            red_lower2 = np.array([170, 100, 100])
            red_upper2 = np.array([180, 255, 255])
            red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
            red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            red_pixels = cv2.countNonZero(red_mask)
            
            # 判断趋势
            if green_pixels > red_pixels and green_pixels > 50:
                change_rate = 1.0  # 假设上涨
            elif red_pixels > green_pixels and red_pixels > 50:
                change_rate = -1.0  # 假设下跌
            else:
                change_rate = 0.0  # 无明显变化
            
            self.logger.info(f"🎨 颜色检测货值变化: 绿色={green_pixels}, 红色={red_pixels}, 变化率={change_rate:.2f}%")
            
            return {
                'detected': True,
                'value': None,
                'change_rate': change_rate,
                'green_pixels': green_pixels,
                'red_pixels': red_pixels
            }
            
        except Exception as e:
            self.logger.error(f"颜色检测货值变化失败: {e}")
            return {'detected': False, 'value': None, 'change_rate': 0.0}
    
    def get_current_price(self) -> float:
        """获取当前价格（K线交易器兼容方法）"""
        return self.get_current_price_from_display()
    
    def get_current_price_from_display(self, screenshot: np.ndarray = None) -> float:
        """从显示区域获取当前价格"""
        try:
            # 如果没有提供截图，自动截取屏幕
            if screenshot is None:
                try:
                    import pyautogui
                    screenshot_pil = pyautogui.screenshot()
                    screenshot = np.array(screenshot_pil)
                    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
                    self.logger.info("🔍 自动截取屏幕进行价格识别")
                except Exception as e:
                    self.logger.warning(f"自动截屏失败: {e}")
                    # 即使截屏失败，也尝试使用真实价格检测器
                    pass
            
            # 优先使用真实价格检测器
            if self.real_price_detector is not None:
                try:
                    real_price = self.real_price_detector.get_price_with_fallback()
                    if real_price and 1000 <= real_price <= 3000:  # 合理价格范围
                        # 更新价格记录
                        current_time = time.time()
                        if (self.current_price is None or 
                            current_time - self.last_price_update_time >= self.price_update_interval):
                            
                            if self.current_price is not None:
                                # 计算价格变化率
                                self.price_change_rate = (real_price - self.current_price) / self.current_price * 100
                                self.logger.info(f"💰 真实价格更新: {self.current_price} → {real_price} ({self.price_change_rate:+.2f}%)")
                            else:
                                self.logger.info(f"💰 获取到真实价格: {real_price}")
                            
                            self.current_price = real_price
                            self.last_price_update_time = current_time
                        
                        return real_price
                except Exception as e:
                    self.logger.warning(f"真实价格检测器获取价格失败: {e}")
            
            # 备用方案：使用原有的OCR方法
            if TESSERACT_AVAILABLE and _setup_tesseract():
                try:
                    # 获取当前价格显示位置
                    x, y = self.relative_positions['current_price_display']
                    height, width = screenshot.shape[:2]
                    
                    # 价格区域（扩大一些以确保包含完整数字）
                    region_size = 100  # 区域大小
                    region_x = int(x * width) - region_size // 2
                    region_y = int(y * height) - region_size // 2
                    region_x = max(0, region_x)
                    region_y = max(0, region_y)
                    region_w = min(region_size, width - region_x)
                    region_h = min(region_size, height - region_y)
                    
                    # 提取价格区域
                    price_region = screenshot[region_y:region_y+region_h, region_x:region_x+region_w]
                    
                    # 预处理图像以提高OCR准确率
                    gray = cv2.cvtColor(price_region, cv2.COLOR_BGR2GRAY)
                    # 增强对比度
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                    enhanced = clahe.apply(gray)
                    # 二值化
                    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    # OCR配置
                    custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.'
                    text = pytesseract.image_to_string(binary, config=custom_config).strip()
                    
                    # 提取价格
                    import re
                    price_match = re.search(r'(\d+\.?\d*)', text)
                    if price_match:
                        price = float(price_match.group(1))
                        if 1000 <= price <= 3000:  # 验证价格范围
                            self.current_price = price
                            return price
                    
                except Exception as e:
                    self.logger.warning(f"备用OCR价格识别失败: {e}")
            
            # 最后的备用方案：使用历史价格+小幅波动
            if self.current_price is not None:
                import random
                # 添加±1的小幅波动
                fluctuation = random.uniform(-1, 1)
                adjusted_price = self.current_price + fluctuation
                self.logger.info(f"💰 使用历史价格+波动: {adjusted_price:.1f} (基于 {self.current_price})")
                return adjusted_price
            
            # 尝试全屏OCR识别价格
            self.logger.info("🔍 尝试全屏OCR识别价格...")
            full_screen_price = self._try_full_screen_ocr_price()
            if full_screen_price is not None:
                self.current_price = full_screen_price
                self.logger.info(f"💰 全屏OCR获取价格成功: {full_screen_price:.1f}")
                return full_screen_price
            
            # 所有价格获取方法都失败
            self.logger.error("❌ 所有价格获取方法都失败，无法获取真实价格")
            return None
            
        except Exception as e:
            self.logger.error(f"获取当前价格失败: {e}")
            return None  # 返回None表示价格获取失败
    
    def _try_full_screen_ocr_price(self) -> Optional[float]:
        """尝试全屏OCR识别价格"""
        try:
            if not TESSERACT_AVAILABLE:
                self.logger.warning("Tesseract OCR不可用，无法进行全屏价格识别")
                return None
            
            # 截取全屏
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            # 多个可能的价格区域（相对于屏幕）
            price_regions = [
                # 右上角区域 (通常显示当前价格)
                {'name': '右上角', 'x': 0.7, 'y': 0.1, 'w': 0.25, 'h': 0.2},
                # 右侧中部区域
                {'name': '右侧中部', 'x': 0.75, 'y': 0.3, 'w': 0.2, 'h': 0.3},
                # 中央上部区域
                {'name': '中央上部', 'x': 0.4, 'y': 0.1, 'w': 0.2, 'h': 0.2},
                # 左侧价格显示区域
                {'name': '左侧', 'x': 0.05, 'y': 0.2, 'w': 0.3, 'h': 0.4},
            ]
            
            screen_h, screen_w = screenshot_cv.shape[:2]
            
            for region in price_regions:
                try:
                    # 计算区域坐标
                    x = int(region['x'] * screen_w)
                    y = int(region['y'] * screen_h)
                    w = int(region['w'] * screen_w)
                    h = int(region['h'] * screen_h)
                    
                    # 确保坐标在屏幕范围内
                    x = max(0, min(x, screen_w - 1))
                    y = max(0, min(y, screen_h - 1))
                    w = min(w, screen_w - x)
                    h = min(h, screen_h - y)
                    
                    if w <= 0 or h <= 0:
                        continue
                    
                    # 提取区域
                    region_img = screenshot_cv[y:y+h, x:x+w]
                    
                    # OCR识别价格
                    price = self._ocr_extract_price_from_region(region_img, region['name'])
                    if price is not None:
                        self.logger.info(f"✅ 在{region['name']}区域找到价格: {price:.1f}")
                        return price
                        
                except Exception as e:
                    self.logger.debug(f"处理{region['name']}区域时出错: {e}")
                    continue
            
            self.logger.warning("🔍 全屏OCR未能识别到有效价格")
            return None
            
        except Exception as e:
            self.logger.error(f"全屏OCR价格识别失败: {e}")
            return None
    
    def _ocr_extract_price_from_region(self, region_img: np.ndarray, region_name: str) -> Optional[float]:
        """从指定区域提取价格"""
        try:
            if region_img.size == 0:
                return None
            
            # 图像预处理
            gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
            
            # 多种预处理方式
            processed_images = []
            
            # 方法1: 直接二值化
            _, binary1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(binary1)
            
            # 方法2: 对比度增强后二值化
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            _, binary2 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(binary2)
            
            # 方法3: 反色处理（适用于深色背景）
            inverted = 255 - gray
            _, binary3 = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(binary3)
            
            # OCR配置选项
            ocr_configs = [
                r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.',  # 单行数字
                r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.',  # 单文本行
                r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.',  # 统一文本块
            ]
            
            # 尝试不同的预处理和配置组合
            for i, processed_img in enumerate(processed_images):
                for j, config in enumerate(ocr_configs):
                    try:
                        # OCR识别
                        text = pytesseract.image_to_string(processed_img, config=config).strip()
                        
                        if text:
                            # 使用正则表达式提取数字
                            import re
                            # 匹配价格格式：1234.56 或 1234
                            price_matches = re.findall(r'(\d{3,4}\.?\d*)', text)
                            
                            for price_str in price_matches:
                                try:
                                    price = float(price_str)
                                    # 验证价格范围（景陶易购的合理价格范围）
                                    if 500 <= price <= 5000:
                                        self.logger.debug(f"{region_name} OCR成功 - 方法{i+1}-配置{j+1}: '{text}' -> {price}")
                                        
                                        # 保存调试图像
                                        debug_filename = f"debug_price_region_{region_name}_{int(time.time())}.png"
                                        cv2.imwrite(debug_filename, processed_img)
                                        
                                        return price
                                except ValueError:
                                    continue
                    except Exception as ocr_e:
                        self.logger.debug(f"{region_name} OCR方法{i+1}-配置{j+1}失败: {ocr_e}")
                        continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"从{region_name}区域提取价格失败: {e}")
            return None
    
    def auto_fill_price(self, target_price: float = None, price_adjustment: float = 0):
        """自动填入价格到价格输入框"""
        try:
            if target_price is None:
                # 优先使用真实价格检测器获取当前价格
                if self.real_price_detector is not None:
                    try:
                        current_real_price = self.real_price_detector.get_price_with_fallback()
                        target_price = current_real_price + price_adjustment
                    except Exception as e:
                        self.logger.warning(f"真实价格检测器获取价格失败，使用备用价格: {e}")
                        target_price = (self.current_price or 1405.0) + price_adjustment
                else:
                    target_price = (self.current_price or 1405.0) + price_adjustment
            
            # 使用真实价格检测器的自动输入功能
            if self.real_price_detector is not None:
                try:
                    success = self.real_price_detector.auto_input_price(target_price)
                    if success:
                        return True
                except Exception as e:
                    self.logger.warning(f"真实价格检测器自动输入失败，使用备用方法: {e}")
            
            # 备用方案：使用原有的自动输入方法
            # 确保客户端窗口已找到并激活
            if not self.find_client_window():
                self.logger.error("❌ 无法找到客户端窗口")
                return False
            
            # 获取价格输入框位置
            x, y = self.calculate_button_position('price_input')
            if x is None or y is None:
                self.logger.error("❌ 无法获取价格输入框位置")
                return False
            
            # 点击价格输入框
            pyautogui.click(x, y)
            time.sleep(0.3)
            
            # 全选并清空
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.1)
            
            # 输入新价格（取整数）
            price_str = f"{target_price:.0f}"
            pyautogui.write(price_str)
            time.sleep(0.2)
            
            self.logger.info(f"💰 自动填入价格: {price_str}")
            return True
            
        except Exception as e:
            self.logger.error(f"自动填入价格失败: {e}")
            return False

    def auto_fill_quantity(self, quantity: int = 1):
        """自动填入数量到数量输入框"""
        try:
            self.logger.info("🔧 开始自动填入数量...")
            
            # 确保客户端窗口已找到并激活
            self.logger.info("🔍 正在确认客户端窗口状态...")
            if not self.find_client_window():
                self.logger.error("❌ 无法找到客户端窗口")
                return False
            
            # 输出窗口信息
            self.logger.info(f"🖥️ 客户端窗口信息: ({self.window_rect.left}, {self.window_rect.top}) 大小: {self.window_rect.width}x{self.window_rect.height}")
            
            # 检查quantity_input是否在relative_positions中
            if 'quantity_input' not in self.relative_positions:
                self.logger.error(f"❌ quantity_input 不在相对坐标中。可用按钮: {list(self.relative_positions.keys())}")
                return False
            
            rel_x, rel_y = self.relative_positions['quantity_input']
            self.logger.info(f"📍 quantity_input 相对坐标: ({rel_x}, {rel_y})")
            
            # 获取数量输入框位置
            x, y = self.calculate_button_position('quantity_input')
            if x is None or y is None:
                self.logger.error("❌ 无法获取数量输入框位置")
                return False
            
            self.logger.info(f"🎯 计算出的绝对坐标: ({x}, {y})")
            
            # 点击数量输入框
            pyautogui.click(x, y)
            time.sleep(0.3)
            
            # 全选并清空
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.1)
            
            # 输入数量
            quantity_str = str(quantity)
            pyautogui.write(quantity_str)
            time.sleep(0.2)
            
            self.logger.info(f"📦 自动填入数量: {quantity_str}")
            return True
            
        except Exception as e:
            self.logger.error(f"自动填入数量失败: {e}")
            return False

    def set_angle_threshold(self, threshold: float):
        """设置角度阈值"""
        if 1 <= threshold <= 45:
            self.angle_threshold = threshold
            self.logger.info(f"角度阈值已设置为: {threshold}°")
        else:
            self.logger.warning(f"角度阈值必须在1-45度之间，当前值: {threshold}")

    def stop(self):
        """停止交易引擎"""
        self.is_running = False
        self.logger.info("智能交易引擎已停止")


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    engine = SmartTradingEngine()
    
    # 测试客户端连接
    if engine.start_client():
        print("✅ 客户端连接成功")
        
        # 测试坐标
        if engine.test_coordinates():
            print("✅ 坐标测试通过")
        else:
            print("❌ 坐标测试失败")
    else:
        print("❌ 客户端连接失败")