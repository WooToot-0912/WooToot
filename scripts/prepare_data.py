#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
云南烤烟病害数据集预处理脚本
用于处理原始图像数据，进行初步筛选和标准化
"""

import os
import sys
import argparse
import cv2
import shutil
from tqdm import tqdm
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.data_utils import process_raw_images

def parse_args():
    parser = argparse.ArgumentParser(description='云南烤烟病害数据集预处理')
    parser.add_argument('--source', type=str, required=True, help='原始数据目录')
    parser.add_argument('--output', type=str, default='data/processed/images', help='输出目录')
    parser.add_argument('--min-size', type=int, default=224, help='最小图像尺寸')
    parser.add_argument('--min-quality', type=float, default=100, help='最小图像质量（拉普拉斯方差）')
    return parser.parse_args()

def check_image_quality(img_path, min_size=224, min_quality=100):
    """检查图像质量"""
    try:
        img = cv2.imread(img_path)
        if img is None:
            return False, "无法读取图像"
        
        # 检查尺寸
        h, w = img.shape[:2]
        if h < min_size or w < min_size:
            return False, f"图像尺寸过小: {w}x{h}"
        
        # 检查模糊度（拉普拉斯方差）
        laplacian_var = cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
        if laplacian_var < min_quality:
            return False, f"图像模糊: {laplacian_var:.2f}"
        
        return True, "图像质量合格"
    except Exception as e:
        return False, f"处理错误: {str(e)}"

def main():
    args = parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)
    
    # 获取所有图像文件
    image_files = []
    for root, _, files in os.walk(args.source):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                image_files.append(os.path.join(root, file))
    
    print(f"找到 {len(image_files)} 张图像文件")
    
    # 处理图像
    processed_count = 0
    skipped_count = 0
    quality_issues = {"尺寸过小": 0, "图像模糊": 0, "读取错误": 0, "其他": 0}
    
    for img_path in tqdm(image_files, desc="处理图像"):
        # 检查图像质量
        is_good, reason = check_image_quality(img_path, args.min_size, args.min_quality)
        
        if is_good:
            # 确定目标路径
            rel_path = os.path.relpath(os.path.dirname(img_path), args.source)
            category = os.path.basename(rel_path) if rel_path != '.' else 'unknown'
            
            # 创建唯一文件名
            filename = f"{category}_{os.path.basename(img_path)}"
            dst_path = os.path.join(args.output, filename)
            
            # 复制图像
            shutil.copy(img_path, dst_path)
            processed_count += 1
        else:
            skipped_count += 1
            if "尺寸过小" in reason:
                quality_issues["尺寸过小"] += 1
            elif "图像模糊" in reason:
                quality_issues["图像模糊"] += 1
            elif "无法读取" in reason:
                quality_issues["读取错误"] += 1
            else:
                quality_issues["其他"] += 1
    
    # 输出处理结果
    print(f"\n处理完成！")
    print(f"处理图像: {processed_count} 张")
    print(f"跳过图像: {skipped_count} 张")
    print("跳过原因统计:")
    for issue, count in quality_issues.items():
        if count > 0:
            print(f"  - {issue}: {count} 张")

if __name__ == '__main__':
    main()