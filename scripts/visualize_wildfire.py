#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
野火病数据集可视化脚本
用于检查标注质量和数据集结构
"""

import os
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path
import random

def read_yolo_annotation(label_path, img_width, img_height):
    """
    读取YOLO格式的标注文件
    
    Args:
        label_path: 标注文件路径
        img_width: 图像宽度
        img_height: 图像高度
    
    Returns:
        boxes: 边界框列表 [(x1, y1, x2, y2, class_id), ...]
    """
    boxes = []
    
    if not os.path.exists(label_path):
        return boxes
    
    with open(label_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split()
        if len(parts) < 5:
            continue
        
        class_id = int(parts[0])
        center_x = float(parts[1]) * img_width
        center_y = float(parts[2]) * img_height
        width = float(parts[3]) * img_width
        height = float(parts[4]) * img_height
        
        # 转换为左上角和右下角坐标
        x1 = center_x - width / 2
        y1 = center_y - height / 2
        x2 = center_x + width / 2
        y2 = center_y + height / 2
        
        boxes.append((x1, y1, x2, y2, class_id))
    
    return boxes

def visualize_sample_images(image_dir, label_dir, num_samples=9, save_path=None):
    """
    可视化样本图像和标注
    
    Args:
        image_dir: 图像目录
        label_dir: 标签目录
        num_samples: 样本数量
        save_path: 保存路径
    """
    # 获取所有图像文件
    image_files = list(Path(image_dir).glob("*.jpg"))
    
    if len(image_files) == 0:
        print(f"在目录 {image_dir} 中没有找到图像文件")
        return
    
    # 随机选择样本
    sample_files = random.sample(image_files, min(num_samples, len(image_files)))
    
    # 类别名称
    class_names = ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt']
    colors = ['green', 'blue', 'orange', 'red', 'purple']
    
    # 创建子图
    rows = int(np.ceil(np.sqrt(len(sample_files))))
    cols = int(np.ceil(len(sample_files) / rows))
    
    fig, axes = plt.subplots(rows, cols, figsize=(15, 15))
    if rows == 1 and cols == 1:
        axes = [axes]
    elif rows == 1 or cols == 1:
        axes = axes.flatten()
    else:
        axes = axes.flatten()
    
    for i, img_path in enumerate(sample_files):
        # 读取图像
        img = cv2.imread(str(img_path))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 读取标注
        label_path = os.path.join(label_dir, img_path.stem + ".txt")
        boxes = read_yolo_annotation(label_path, img.shape[1], img.shape[0])
        
        # 显示图像
        axes[i].imshow(img_rgb)
        axes[i].set_title(f"{img_path.name}", fontsize=10)
        axes[i].axis('off')
        
        # 绘制边界框
        for box in boxes:
            x1, y1, x2, y2, class_id = box
            
            if 0 <= class_id < len(class_names):
                color = colors[class_id]
                class_name = class_names[class_id]
            else:
                color = 'black'
                class_name = f'class_{class_id}'
            
            # 创建矩形框
            rect = patches.Rectangle(
                (x1, y1), x2 - x1, y2 - y1,
                linewidth=2, edgecolor=color, facecolor='none'
            )
            axes[i].add_patch(rect)
            
            # 添加类别标签
            axes[i].text(
                x1, y1 - 5, class_name,
                fontsize=8, color=color, weight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.7)
            )
    
    # 隐藏多余的子图
    for i in range(len(sample_files), len(axes)):
        axes[i].axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"可视化结果保存到: {save_path}")
    
    plt.show()

def analyze_dataset_statistics(image_dir, label_dir):
    """
    分析数据集统计信息
    
    Args:
        image_dir: 图像目录
        label_dir: 标签目录
    """
    print("数据集统计分析")
    print("=" * 50)
    
    # 获取所有图像文件
    image_files = list(Path(image_dir).glob("*.jpg"))
    
    print(f"图像总数: {len(image_files)}")
    
    if len(image_files) == 0:
        print("没有找到图像文件")
        return
    
    # 统计类别分布
    class_counts = {}
    total_boxes = 0
    
    for img_path in image_files:
        label_path = os.path.join(label_dir, img_path.stem + ".txt")
        
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line:
                    class_id = int(line.split()[0])
                    class_counts[class_id] = class_counts.get(class_id, 0) + 1
                    total_boxes += 1
    
    print(f"标注框总数: {total_boxes}")
    
    # 类别名称
    class_names = ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt']
    
    print("\n类别分布:")
    for class_id, count in sorted(class_counts.items()):
        if class_id < len(class_names):
            class_name = class_names[class_id]
        else:
            class_name = f'class_{class_id}'
        
        percentage = (count / total_boxes) * 100 if total_boxes > 0 else 0
        print(f"  {class_name}: {count} ({percentage:.1f}%)")
    
    # 分析图像尺寸
    image_sizes = []
    for img_path in image_files[:10]:  # 只检查前10张图像
        img = cv2.imread(str(img_path))
        if img is not None:
            image_sizes.append((img.shape[1], img.shape[0]))  # (width, height)
    
    if image_sizes:
        widths = [size[0] for size in image_sizes]
        heights = [size[1] for size in image_sizes]
        
        print(f"\n图像尺寸分析（前10张图像）:")
        print(f"  宽度范围: {min(widths)} - {max(widths)}")
        print(f"  高度范围: {min(heights)} - {max(heights)}")
        print(f"  平均尺寸: {np.mean(widths):.0f} x {np.mean(heights):.0f}")

def check_dataset_integrity():
    """
    检查数据集完整性
    """
    print("数据集完整性检查")
    print("=" * 50)
    
    # 检查目录结构
    required_dirs = [
        "data/processed/images/wildfire",
        "data/processed/labels/wildfire",
        "data/train/images",
        "data/train/labels",
        "data/val/images",
        "data/val/labels",
        "data/test/images",
        "data/test/labels"
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            file_count = len([f for f in os.listdir(dir_path) 
                            if f.endswith(('.jpg', '.txt'))])
            print(f"✓ {dir_path}: {file_count} 个文件")
        else:
            print(f"✗ {dir_path}: 目录不存在")
    
    # 检查配置文件
    config_file = "data/dataset.yaml"
    if os.path.exists(config_file):
        print(f"✓ {config_file}: 配置文件存在")
    else:
        print(f"✗ {config_file}: 配置文件不存在")
    
    # 检查图像和标签对应关系
    datasets = [
        ("train", "data/train/images", "data/train/labels"),
        ("val", "data/val/images", "data/val/labels"),
        ("test", "data/test/images", "data/test/labels")
    ]
    
    print("\n图像-标签对应关系检查:")
    for dataset_name, img_dir, label_dir in datasets:
        if os.path.exists(img_dir) and os.path.exists(label_dir):
            img_files = set(f.stem for f in Path(img_dir).glob("*.jpg"))
            label_files = set(f.stem for f in Path(label_dir).glob("*.txt"))
            
            missing_labels = img_files - label_files
            missing_images = label_files - img_files
            
            print(f"  {dataset_name}集:")
            print(f"    图像数量: {len(img_files)}")
            print(f"    标签数量: {len(label_files)}")
            
            if missing_labels:
                print(f"    缺少标签的图像: {len(missing_labels)}")
            if missing_images:
                print(f"    缺少图像的标签: {len(missing_images)}")
            
            if not missing_labels and not missing_images:
                print(f"    ✓ 图像和标签完全对应")

def main():
    """
    主函数
    """
    print("野火病数据集可视化和分析")
    print("=" * 50)
    
    # 检查数据集完整性
    check_dataset_integrity()
    
    # 分析处理后的数据
    processed_img_dir = "data/processed/images/wildfire"
    processed_label_dir = "data/processed/labels/wildfire"
    
    if os.path.exists(processed_img_dir):
        print(f"\n分析处理后的数据 ({processed_img_dir}):")
        analyze_dataset_statistics(processed_img_dir, processed_label_dir)
        
        # 可视化样本
        print(f"\n可视化处理后的样本:")
        visualize_sample_images(
            processed_img_dir, 
            processed_label_dir, 
            num_samples=9,
            save_path="results/wildfire_processed_samples.png"
        )
    
    # 分析训练集
    train_img_dir = "data/train/images"
    train_label_dir = "data/train/labels"
    
    if os.path.exists(train_img_dir):
        print(f"\n分析训练集 ({train_img_dir}):")
        analyze_dataset_statistics(train_img_dir, train_label_dir)
        
        # 可视化训练样本
        print(f"\n可视化训练样本:")
        visualize_sample_images(
            train_img_dir, 
            train_label_dir, 
            num_samples=9,
            save_path="results/wildfire_train_samples.png"
        )

if __name__ == "__main__":
    # 设置随机种子
    random.seed(42)
    
    # 创建结果目录
    os.makedirs("results", exist_ok=True)
    
    # 运行主函数
    main()