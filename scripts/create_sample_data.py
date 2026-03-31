#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建示例数据集脚本
用于生成简单的示例数据，以便测试系统功能
"""

import os
import cv2
import numpy as np
from pathlib import Path
import random
import shutil

def create_sample_image(output_path, width=640, height=640, disease_type=None):
    """创建一个示例图像"""
    # 创建基础图像（绿色背景模拟叶片）
    img = np.ones((height, width, 3), dtype=np.uint8) * np.array([30, 180, 30], dtype=np.uint8)
    
    # 根据病害类型添加特征
    if disease_type == "healthy":
        # 健康叶片，添加一些纹理
        for _ in range(20):
            x = random.randint(0, width-1)
            y = random.randint(0, height-1)
            cv2.line(img, (x, y), (x + random.randint(20, 50), y + random.randint(20, 50)), 
                     (20, 160, 20), random.randint(1, 3))
    
    elif disease_type == "mosaic_virus":
        # 花叶病毒病，添加花叶斑驳
        for _ in range(30):
            x = random.randint(0, width-100)
            y = random.randint(0, height-100)
            w = random.randint(30, 100)
            h = random.randint(30, 100)
            color = (30, random.randint(100, 220), 30)
            cv2.rectangle(img, (x, y), (x+w, y+h), color, -1)
    
    elif disease_type == "brown_spot":
        # 赤星病，添加圆形褐色病斑
        for _ in range(random.randint(3, 8)):
            x = random.randint(50, width-50)
            y = random.randint(50, height-50)
            radius = random.randint(20, 60)
            color = (30, 50, 140)  # 褐色
            cv2.circle(img, (x, y), radius, color, -1)
            # 添加轮纹
            for r in range(radius-15, radius, 5):
                cv2.circle(img, (x, y), r, (30, 70, 160), 2)
    
    elif disease_type == "wildfire":
        # 野火病，添加不规则黄褐色病斑
        for _ in range(random.randint(2, 5)):
            x = random.randint(50, width-150)
            y = random.randint(50, height-150)
            points = []
            for i in range(6):
                angle = i * 60
                r = random.randint(30, 80)
                px = x + int(r * np.cos(np.radians(angle)))
                py = y + int(r * np.sin(np.radians(angle)))
                points.append([px, py])
            points = np.array(points, np.int32)
            points = points.reshape((-1, 1, 2))
            cv2.fillPoly(img, [points], (30, 140, 200))  # 黄褐色
            # 添加黄色晕圈
            cv2.polylines(img, [points], True, (30, 200, 220), 5)
    
    elif disease_type == "bacterial_wilt":
        # 青枯病，添加萎蔫效果
        # 基础颜色变暗
        img = (img * 0.7).astype(np.uint8)
        # 添加萎蔫纹理
        for _ in range(40):
            x = random.randint(0, width-1)
            y = random.randint(0, height-1)
            cv2.line(img, (x, y), (x + random.randint(50, 150), y), 
                     (20, 120, 20), random.randint(1, 4))
    
    # 添加一些随机噪声
    noise = np.random.randint(0, 20, (height, width, 3), dtype=np.uint8)
    img = cv2.add(img, noise)
    
    # 保存图像
    cv2.imwrite(output_path, img)
    return img

def create_yolo_label(output_path, img_width, img_height, disease_type):
    """创建YOLO格式标签文件"""
    class_id = {
        "healthy": 0,
        "mosaic_virus": 1,
        "brown_spot": 2,
        "wildfire": 3,
        "bacterial_wilt": 4
    }.get(disease_type, 0)
    
    # 创建一个覆盖大部分图像的边界框
    x_center = 0.5
    y_center = 0.5
    width = random.uniform(0.6, 0.8)
    height = random.uniform(0.6, 0.8)
    
    # 写入标签文件
    with open(output_path, 'w') as f:
        f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")

def main():
    # 定义数据集目录
    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    # 确保目录存在
    for dir_path in [raw_dir / "yunnan", processed_dir / "images", processed_dir / "labels"]:
        os.makedirs(dir_path, exist_ok=True)
    
    # 定义病害类型
    disease_types = ["healthy", "mosaic_virus", "brown_spot", "wildfire", "bacterial_wilt"]
    
    # 为每种病害创建示例图像
    print("创建示例数据集...")
    for disease in disease_types:
        # 每种病害创建10张图像
        for i in range(10):
            # 创建原始图像
            raw_img_path = raw_dir / "yunnan" / f"{disease}_{i}.jpg"
            create_sample_image(str(raw_img_path), disease_type=disease)
            
            # 复制到处理目录
            processed_img_path = processed_dir / "images" / f"{disease}_{i}.jpg"
            shutil.copy(raw_img_path, processed_img_path)
            
            # 创建标签
            label_path = processed_dir / "labels" / f"{disease}_{i}.txt"
            create_yolo_label(str(label_path), 640, 640, disease)
    
    print(f"示例数据集创建完成，共 {len(disease_types) * 10} 张图像")

if __name__ == "__main__":
    main()