#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tesseract配置模块
统一管理Tesseract路径配置
"""

import os
import logging

logger = logging.getLogger(__name__)

def setup_tesseract_path():
    """
    设置Tesseract路径
    根据系统中实际安装的Tesseract位置自动配置
    
    Returns:
        str: 找到的Tesseract路径，如果未找到返回None
    """
    # 可能的Tesseract安装路径（按优先级排序）
    tesseract_paths = [
        r"D:\Program Files\tessdata\tesseract.exe",  # 用户当前安装路径
        r"D:\Program Files\tesseract.exe",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', '')),
        "tesseract"  # 系统PATH中的tesseract
    ]
    
    for path in tesseract_paths:
        if path == "tesseract":
            # 检查系统PATH中是否有tesseract
            try:
                import subprocess
                result = subprocess.run(['tesseract', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"✅ 找到Tesseract: 系统PATH")
                    return "tesseract"
            except:
                continue
        else:
            # 检查文件是否存在
            if os.path.exists(path):
                logger.info(f"✅ 找到Tesseract: {path}")
                return path
    
    logger.warning("❌ 未找到可用的Tesseract安装")
    return None

def configure_pytesseract():
    """
    配置pytesseract
    
    Returns:
        bool: 配置是否成功
    """
    try:
        import pytesseract
        
        tesseract_path = setup_tesseract_path()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            # 测试是否可用
            try:
                version = pytesseract.get_tesseract_version()
                logger.info(f"✅ Tesseract配置成功，版本: {version}")
                return True
            except Exception as e:
                logger.error(f"❌ Tesseract测试失败: {e}")
                return False
        else:
            logger.error("❌ 未找到Tesseract，OCR功能将不可用")
            return False
            
    except ImportError:
        logger.error("❌ pytesseract未安装")
        return False
    except Exception as e:
        logger.error(f"❌ 配置Tesseract失败: {e}")
        return False

def get_tesseract_config():
    """
    获取OCR配置
    
    Returns:
        dict: OCR配置字典
    """
    return {
        'price_config': '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.',
        'text_config': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz买卖入出确定认订立价格数量委托银证转账',
        'number_config': '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.-+',
        'general_config': '--oem 3 --psm 6'
    }

if __name__ == "__main__":
    # 测试配置
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 测试Tesseract配置...")
    path = setup_tesseract_path()
    if path:
        print(f"✅ 找到Tesseract: {path}")
        
        success = configure_pytesseract()
        if success:
            print("✅ Tesseract配置成功")
        else:
            print("❌ Tesseract配置失败")
    else:
        print("❌ 未找到Tesseract")
