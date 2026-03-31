#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
云南烤烟病害数据集增强脚本
用于对处理后的图像进行数据增强，生成更多样本
"""

import os
import sys
import argparse
import cv2
import numpy as np
from tqdm import tqdm
import albumentations as A
from pathlib import Path
import glob

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.data_utils import apply_augmentation

def parse_args():
    parser = argparse.ArgumentParser(description='云南烤烟病害数据集增强')
    parser.add_argument('--input', type=str, default='data/processed', help='输入目录')
    parser.add_argument('--output', type=str, default='data/augmented', help='输出目录')
    parser.add_argument('--count', type=int, default=3, help='每张图像生成的增强版本数量')
    parser.add_argument('--fog', action='store_true', help='添加雾气效果（模拟云南山区环境）')
    parser.add_argument('--rain', action='store_true', help='添加雨水效果（模拟雨季环境）')
    return parser.parse_args()

def create_augmentation_pipeline(add_fog=False, add_rain=False):
    """创建数据增强管道"""
    transform = A.Compose([
        # 基本增强
        A.RandomRotate90(p=0.5),
        A.Rotate(limit=30, p=0.7),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.7),
        
        # 云南特色环境增强
        A.OneOf([
            A.RandomFog(fog_coef_lower=0.1, fog_coef_upper=0.3, p=0.8 if add_fog else 0.3) if hasattr(A, 'RandomFog') else A.GaussNoise(p=0.5),  # 模拟山区雾气
            A.RandomRain(p=0.8 if add_rain else 0.2) if hasattr(A, 'RandomRain') else A.GaussNoise(p=0.5),  # 模拟雨季环境
            A.RandomSunFlare(p=0.2) if hasattr(A, 'RandomSunFlare') else A.RandomBrightnessContrast(p=0.5),  # 模拟强光照
        ], p=0.5),
        
        # 背景干扰增强
        A.OneOf([
            A.CoarseDropout(p=0.5),  # 模拟叶片遮挡
            A.GridDistortion(p=0.3),  # 模拟叶片弯曲
        ], p=0.5),
        
        # 病斑特征增强
        A.OneOf([
            A.Sharpen(alpha=(0.2, 0.5), p=0.5),  # 增强病斑边缘
            A.CLAHE(p=0.3),  # 增强对比度
        ], p=0.5),
    ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
    
    return transform

def main():
    args = parse_args()
    
    # 确保输出目录存在
    os.makedirs(os.path.join(args.output, 'images'), exist_ok=True)
    os.makedirs(os.path.join(args.output, 'labels'), exist_ok=True)
    
    # 获取所有图像文件
    image_dir = os.path.join(args.input, 'images')
    label_dir = os.path.join(args.input, 'labels')
    
    image_files = glob.glob(os.path.join(image_dir, '*.jpg')) + \
                 glob.glob(os.path.join(image_dir, '*.jpeg')) + \
                 glob.glob(os.path.join(image_dir, '*.png'))
    
    print(f"找到 {len(image_files)} 张图像文件")
    
    # 创建数据增强管道
    transform = create_augmentation_pipeline(add_fog=args.fog, add_rain=args.rain)
    
    # 处理每个图像
    augmented_count = 0
    skipped_count = 0
    
    for img_path in tqdm(image_files, desc="增强图像"):
        # 读取图像
        img = cv2.imread(img_path)
        if img is None:
            skipped_count += 1
            continue
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 读取对应标签
        base_name = os.path.basename(img_path).rsplit('.', 1)[0]
        label_path = os.path.join(label_dir, f"{base_name}.txt")
        
        if not os.path.exists(label_path):
            skipped_count += 1
            continue
            
        # 读取标签
        with open(label_path, 'r') as f:
            annotations = []
            class_labels = []
            for line in f:
                parts = line.strip().split()
                class_id = int(parts[0])
                x_center, y_center, width, height = map(float, parts[1:5])
                annotations.append([x_center, y_center, width, height])
                class_labels.append(class_id)
        
        # 应用增强
        for i in range(args.count):
            try:
                augmented = transform(image=img, bboxes=annotations, class_labels=class_labels)
                aug_img = augmented['image']
                aug_bboxes = augmented['bboxes']
                aug_labels = augmented['class_labels']
                
                # 保存增强图像
                aug_img_path = os.path.join(args.output, 'images', f"{base_name}_aug{i}.jpg")
                cv2.imwrite(aug_img_path, cv2.cvtColor(aug_img, cv2.COLOR_RGB2BGR))
                
                # 保存增强标签
                aug_label_path = os.path.join(args.output, 'labels', f"{base_name}_aug{i}.txt")
                with open(aug_label_path, 'w') as f:
                    for j in range(len(aug_bboxes)):
                        bbox = aug_bboxes[j]
                        label = aug_labels[j]
                        f.write(f"{label} {bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}\n")
                
                augmented_count += 1
            except Exception as e:
                print(f"增强图像 {img_path} 时出错: {str(e)}")
                skipped_count += 1
    
    # 输出处理结果
    print(f"\n增强完成！")
    print(f"生成增强图像: {augmented_count} 张")
    print(f"跳过图像: {skipped_count} 张")

if __name__ == '__main__':
    main()