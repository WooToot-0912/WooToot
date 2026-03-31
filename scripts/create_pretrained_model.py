#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建预训练模型脚本
用于创建一个简单的预训练模型，以便测试系统功能
"""

import os
import sys
import torch
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules import ECA, BackgroundSuppressionBranch

def register_custom_modules():
    """注册自定义模块到YOLO模型注册表"""
    from ultralytics.nn.tasks import DetectionModel
    
    # 使用更简单的方式注册自定义模块
    setattr(DetectionModel, 'ECA', ECA)
    setattr(DetectionModel, 'BackgroundSuppressionBranch', BackgroundSuppressionBranch)
    
    print("自定义模块注册完成")

def main():
    try:
        # 注册自定义模块
        register_custom_modules()
        
        # 导入YOLO
        from ultralytics import YOLO
        
        # 创建输出目录
        os.makedirs("runs/train/exp/weights", exist_ok=True)
        
        # 加载官方预训练模型
        print("加载官方YOLOv8n模型...")
        model = YOLO("yolov8n.pt")
        
        # 修改输出层以匹配我们的类别数量
        print("修改模型输出层...")
        model.model.model[-1].nc = 5  # 设置类别数为5
        
        # 保存修改后的模型
        output_path = "runs/train/exp/weights/best.pt"
        model.save(output_path)
        print(f"预训练模型已保存至: {output_path}")
        
        return True
    except Exception as e:
        print(f"创建预训练模型失败: {e}")
        return False

if __name__ == "__main__":
    main()