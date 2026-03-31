#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
云南烤烟病害数据集划分脚本
用于将处理后和增强后的数据集划分为训练集、验证集和测试集
"""

import os
import sys
import argparse
import shutil
from tqdm import tqdm
from pathlib import Path
from sklearn.model_selection import train_test_split
import glob

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.data_utils import split_dataset

def parse_args():
    parser = argparse.ArgumentParser(description='云南烤烟病害数据集划分')
    parser.add_argument('--processed', type=str, default='data/processed', help='处理后的数据目录')
    parser.add_argument('--augmented', type=str, default='data/augmented', help='增强后的数据目录')
    parser.add_argument('--output', type=str, default='data', help='输出目录')
    parser.add_argument('--ratio', type=str, default='8:1:1', help='训练:验证:测试比例，如8:1:1')
    parser.add_argument('--stratify', action='store_true', help='是否按类别分层抽样')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 解析划分比例
    try:
        train_ratio, val_ratio, test_ratio = map(int, args.ratio.split(':'))
        total = train_ratio + val_ratio + test_ratio
        train_ratio /= total
        val_ratio /= total
        test_ratio /= total
    except:
        print(f"无效的比例格式: {args.ratio}，使用默认值8:1:1")
        train_ratio, val_ratio, test_ratio = 0.8, 0.1, 0.1
    
    print(f"数据集划分比例: 训练集 {train_ratio:.1%}, 验证集 {val_ratio:.1%}, 测试集 {test_ratio:.1%}")
    
    # 创建输出目录
    for split in ['train', 'val', 'test']:
        for subdir in ['images', 'labels']:
            os.makedirs(os.path.join(args.output, split, subdir), exist_ok=True)
    
    # 获取所有图像和标签文件
    processed_images = glob.glob(os.path.join(args.processed, 'images', '*.jpg')) + \
                      glob.glob(os.path.join(args.processed, 'images', '*.jpeg')) + \
                      glob.glob(os.path.join(args.processed, 'images', '*.png'))
    
    augmented_images = glob.glob(os.path.join(args.augmented, 'images', '*.jpg')) + \
                      glob.glob(os.path.join(args.augmented, 'images', '*.jpeg')) + \
                      glob.glob(os.path.join(args.augmented, 'images', '*.png'))
    
    all_images = processed_images + augmented_images
    
    print(f"找到处理后图像: {len(processed_images)} 张")
    print(f"找到增强后图像: {len(augmented_images)} 张")
    print(f"总图像数量: {len(all_images)} 张")
    
    # 验证每个图像都有对应的标签
    valid_images = []
    class_counts = {}
    
    for img_path in tqdm(all_images, desc="验证图像和标签"):
        base_name = os.path.basename(img_path).rsplit('.', 1)[0]
        if 'processed' in img_path:
            label_path = os.path.join(args.processed, 'labels', f"{base_name}.txt")
        else:
            label_path = os.path.join(args.augmented, 'labels', f"{base_name}.txt")
        
        if os.path.exists(label_path):
            # 读取标签获取类别
            try:
                with open(label_path, 'r') as f:
                    first_line = f.readline().strip()
                    if first_line:
                        class_id = int(first_line.split()[0])
                        if class_id not in class_counts:
                            class_counts[class_id] = 0
                        class_counts[class_id] += 1
                
                valid_images.append((img_path, label_path, class_id))
            except:
                print(f"无法读取标签文件: {label_path}")
    
    print(f"有效图像数量: {len(valid_images)} 张")
    print("类别分布:")
    for class_id, count in sorted(class_counts.items()):
        print(f"  - 类别 {class_id}: {count} 张 ({count/len(valid_images):.1%})")
    
    # 准备分层抽样的标签
    if args.stratify:
        stratify_labels = [item[2] for item in valid_images]
    else:
        stratify_labels = None
    
    # 划分数据集
    train_val_data, test_data = train_test_split(
        valid_images, 
        test_size=test_ratio,
        random_state=42,
        stratify=stratify_labels if args.stratify else None
    )
    
    if args.stratify and stratify_labels is not None:
        stratify_labels = [item[2] for item in train_val_data]
    
    train_data, val_data = train_test_split(
        train_val_data,
        test_size=val_ratio/(train_ratio + val_ratio),
        random_state=42,
        stratify=stratify_labels if args.stratify else None
    )
    
    print(f"数据集划分结果: 训练集 {len(train_data)} 张, 验证集 {len(val_data)} 张, 测试集 {len(test_data)} 张")
    
    # 复制文件到对应目录
    for dataset, split in [(train_data, 'train'), (val_data, 'val'), (test_data, 'test')]:
        for img_path, label_path, _ in tqdm(dataset, desc=f"复制{split}集"):
            img_filename = os.path.basename(img_path)
            label_filename = os.path.basename(label_path)
            
            # 复制图像
            shutil.copy(img_path, os.path.join(args.output, split, 'images', img_filename))
            
            # 复制标签
            shutil.copy(label_path, os.path.join(args.output, split, 'labels', label_filename))
    
    # 检查类别分布
    for split in ['train', 'val', 'test']:
        split_labels_dir = os.path.join(args.output, split, 'labels')
        split_class_counts = {}
        
        for label_file in glob.glob(os.path.join(split_labels_dir, '*.txt')):
            try:
                with open(label_file, 'r') as f:
                    for line in f:
                        class_id = int(line.strip().split()[0])
                        if class_id not in split_class_counts:
                            split_class_counts[class_id] = 0
                        split_class_counts[class_id] += 1
            except:
                pass
        
        print(f"\n{split}集类别分布:")
        for class_id, count in sorted(split_class_counts.items()):
            print(f"  - 类别 {class_id}: {count} 个")
    
    print("\n数据集划分完成！")

if __name__ == '__main__':
    main()