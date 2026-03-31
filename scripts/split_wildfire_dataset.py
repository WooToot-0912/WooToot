#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
野火病数据集划分脚本
将处理后的野火病数据划分为训练集、验证集和测试集
"""

import os
import shutil
import random
from pathlib import Path
from tqdm import tqdm

def split_wildfire_dataset(train_ratio=0.7, val_ratio=0.2, test_ratio=0.1, seed=42):
    """
    划分野火病数据集
    
    Args:
        train_ratio: 训练集比例
        val_ratio: 验证集比例
        test_ratio: 测试集比例
        seed: 随机种子
    """
    # 设置随机种子
    random.seed(seed)
    
    # 定义路径
    image_dir = "data/processed/images/wildfire"
    label_dir = "data/processed/labels/wildfire"
    
    train_img_dir = "data/train/images"
    train_label_dir = "data/train/labels"
    val_img_dir = "data/val/images"
    val_label_dir = "data/val/labels"
    test_img_dir = "data/test/images"
    test_label_dir = "data/test/labels"
    
    # 创建目标目录
    for dir_path in [train_img_dir, train_label_dir, val_img_dir, 
                     val_label_dir, test_img_dir, test_label_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    # 获取所有图像文件
    image_files = list(Path(image_dir).glob("*.jpg"))
    image_files = [f.stem for f in image_files]  # 只保留文件名（不含扩展名）
    
    # 打乱顺序
    random.shuffle(image_files)
    
    # 计算划分点
    total_count = len(image_files)
    train_count = int(total_count * train_ratio)
    val_count = int(total_count * val_ratio)
    
    # 划分数据集
    train_files = image_files[:train_count]
    val_files = image_files[train_count:train_count + val_count]
    test_files = image_files[train_count + val_count:]
    
    print(f"数据集划分：")
    print(f"训练集: {len(train_files)} 张图像")
    print(f"验证集: {len(val_files)} 张图像")
    print(f"测试集: {len(test_files)} 张图像")
    
    # 复制训练集
    print("复制训练集...")
    for filename in tqdm(train_files, desc="训练集"):
        # 复制图像
        src_img = os.path.join(image_dir, f"{filename}.jpg")
        dst_img = os.path.join(train_img_dir, f"{filename}.jpg")
        if os.path.exists(src_img):
            shutil.copy2(src_img, dst_img)
        
        # 复制标签
        src_label = os.path.join(label_dir, f"{filename}.txt")
        dst_label = os.path.join(train_label_dir, f"{filename}.txt")
        if os.path.exists(src_label):
            shutil.copy2(src_label, dst_label)
    
    # 复制验证集
    print("复制验证集...")
    for filename in tqdm(val_files, desc="验证集"):
        # 复制图像
        src_img = os.path.join(image_dir, f"{filename}.jpg")
        dst_img = os.path.join(val_img_dir, f"{filename}.jpg")
        if os.path.exists(src_img):
            shutil.copy2(src_img, dst_img)
        
        # 复制标签
        src_label = os.path.join(label_dir, f"{filename}.txt")
        dst_label = os.path.join(val_label_dir, f"{filename}.txt")
        if os.path.exists(src_label):
            shutil.copy2(src_label, dst_label)
    
    # 复制测试集
    print("复制测试集...")
    for filename in tqdm(test_files, desc="测试集"):
        # 复制图像
        src_img = os.path.join(image_dir, f"{filename}.jpg")
        dst_img = os.path.join(test_img_dir, f"{filename}.jpg")
        if os.path.exists(src_img):
            shutil.copy2(src_img, dst_img)
        
        # 复制标签
        src_label = os.path.join(label_dir, f"{filename}.txt")
        dst_label = os.path.join(test_label_dir, f"{filename}.txt")
        if os.path.exists(src_label):
            shutil.copy2(src_label, dst_label)
    
    print("数据集划分完成！")

def update_dataset_yaml():
    """
    更新dataset.yaml配置文件
    """
    yaml_content = """# 云南烤烟病害数据集配置
path: ./data
train: train/images
val: val/images
test: test/images

# 类别数量和名称
nc: 5  # 类别数量
names: ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt']  # 健康叶片、烟草花叶病毒病、赤星病、野火病、青枯病
"""
    
    with open("data/dataset.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_content)
    
    print("已更新 data/dataset.yaml 配置文件")

if __name__ == "__main__":
    print("开始划分野火病数据集...")
    split_wildfire_dataset()
    
    print("\n更新数据集配置文件...")
    update_dataset_yaml()
    
    print("\n数据集划分完成！")
    print("数据集结构：")
    print("- data/train/: 训练集")
    print("- data/val/: 验证集")
    print("- data/test/: 测试集")