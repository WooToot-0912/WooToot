#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本信息管理模块
"""

# 版本信息
VERSION = "2.0.0"
BUILD_DATE = "2024-01-15"
BUILD_NUMBER = "20240115001"

# 版本历史
VERSION_HISTORY = {
    "2.0.0": {
        "date": "2024-01-15",
        "features": [
            "新增高级黄线检测算法",
            "优化ROI区域选择功能", 
            "修复价格检测准确性问题",
            "重构代码架构，提升稳定性"
        ],
        "fixes": [
            "修复Qt平台插件问题",
            "解决日志重定向错误",
            "优化内存使用"
        ]
    },
    "1.9.0": {
        "date": "2024-01-10",
        "features": [
            "添加真实价格检测",
            "集成坐标校准工具"
        ]
    }
}

# 更新服务器配置
UPDATE_SERVER = "https://your-domain.com/updates/"
UPDATE_CHECK_URL = f"{UPDATE_SERVER}version.json"
DOWNLOAD_URL = f"{UPDATE_SERVER}downloads/"

def get_version_info():
    """获取当前版本信息"""
    return {
        "version": VERSION,
        "build_date": BUILD_DATE,
        "build_number": BUILD_NUMBER
    }

def get_version_string():
    """获取版本字符串"""
    return f"景陶易购智能交易系统 v{VERSION} (Build {BUILD_NUMBER})"

def compare_versions(current, latest):
    """比较版本号"""
    def version_tuple(v):
        return tuple(map(int, v.split('.')))
    
    return version_tuple(latest) > version_tuple(current)