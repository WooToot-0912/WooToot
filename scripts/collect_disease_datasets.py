#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云南烤烟病害数据集收集和整理脚本
使用相似植物病害数据扩展烟草病害检测数据集
"""

import os
import shutil
import requests
import zipfile
from pathlib import Path
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
import json
import yaml

class DiseaseDatasetCollector:
    def __init__(self, base_dir="data"):
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "raw" / "collected"
        self.processed_dir = self.base_dir / "processed_multiclass"
        
        # 创建目录结构
        self.create_directories()
        
        # 病害类别映射 - 从相似植物病害到烟草病害
        self.disease_mapping = {
            "healthy": [
                "Tomato___healthy",
                "Pepper,_bell___healthy", 
                "Potato___healthy",
                "Apple___healthy",
                "Cherry_(including_sour)___healthy"
            ],
            "mosaic_virus": [
                "Tomato___Tomato_mosaic_virus",
                "Tomato___Tomato_Yellow_Leaf_Curl_Virus"
            ],
            "brown_spot": [
                "Apple___Apple_scab",
                "Potato___Early_blight",
                "Tomato___Early_blight"
            ],
            "wildfire": [
                "Tomato___Bacterial_spot",
                "Pepper,_bell___Bacterial_spot",
                "Peach___Bacterial_spot"
            ],
            "bacterial_wilt": [
                "Tomato___Late_blight",
                "Potato___Late_blight"
            ]
        }
    
    def create_directories(self):
        """创建目录结构"""
        directories = [
            self.raw_dir,
            self.processed_dir / "images",
            self.processed_dir / "labels",
            self.base_dir / "train_multiclass" / "images",
            self.base_dir / "train_multiclass" / "labels", 
            self.base_dir / "val_multiclass" / "images",
            self.base_dir / "val_multiclass" / "labels",
            self.base_dir / "test_multiclass" / "images",
            self.base_dir / "test_multiclass" / "labels"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"创建目录: {directory}")
    
    def download_plantvillage_subset(self):
        """
        下载PlantVillage数据集的相关子集
        注意: 这需要手动下载，这里提供下载指南
        """
        download_info = {
            "PlantVillage": {
                "url": "https://www.kaggle.com/datasets/arjuntejaswi/plant-village",
                "description": "需要手动从Kaggle下载",
                "target_classes": list(self.disease_mapping.values())
            },
            "Plant_Pathology_2021": {
                "url": "https://www.kaggle.com/c/plant-pathology-2021-fgvc8/data",
                "description": "Apple disease dataset - 需要手动下载"
            }
        }
        
        print("📋 数据集下载指南:")
        print("=" * 50)
        for name, info in download_info.items():
            print(f"\n🔗 {name}:")
            print(f"   URL: {info['url']}")
            print(f"   说明: {info['description']}")
            if 'target_classes' in info:
                print(f"   需要的类别: {info['target_classes']}")
        
        print("\n📝 下载步骤:")
        print("1. 访问上述链接")
        print("2. 下载数据集到 data/raw/collected/ 目录")
        print("3. 解压后运行 process_collected_data() 方法")
        
        return download_info
    
    def process_collected_data(self, source_dir):
        """
        处理收集到的数据集
        
        Args:
            source_dir: 解压后的数据集目录
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            print(f"❌ 源目录不存在: {source_dir}")
            return
        
        print(f"🔄 开始处理数据集: {source_dir}")
        
        # 统计信息
        stats = {disease: 0 for disease in self.disease_mapping.keys()}
        
        # 遍历源目录中的所有类别文件夹
        for class_dir in source_path.iterdir():
            if not class_dir.is_dir():
                continue
                
            class_name = class_dir.name
            target_disease = self.find_target_disease(class_name)
            
            if target_disease:
                print(f"📁 处理类别: {class_name} -> {target_disease}")
                self.process_class_images(class_dir, target_disease)
                stats[target_disease] += len(list(class_dir.glob("*.jpg")))
        
        print("\n📊 数据集统计:")
        for disease, count in stats.items():
            print(f"   {disease}: {count} 张图像")
        
        # 生成新的数据集配置
        self.generate_multiclass_config()
    
    def find_target_disease(self, class_name):
        """查找原始类别对应的目标病害类别"""
        for target_disease, source_classes in self.disease_mapping.items():
            if class_name in source_classes:
                return target_disease
        return None
    
    def process_class_images(self, class_dir, target_disease):
        """
        处理单个类别的图像
        
        Args:
            class_dir: 源类别目录
            target_disease: 目标病害类别
        """
        target_dir = self.processed_dir / "images" / target_disease
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取所有图像文件
        image_files = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
        
        for i, img_path in enumerate(image_files):
            try:
                # 读取图像
                img = cv2.imread(str(img_path))
                if img is None:
                    continue
                
                # 调整图像大小到640x640
                img_resized = cv2.resize(img, (640, 640))
                
                # 保存处理后的图像
                new_filename = f"{target_disease}_{class_dir.name}_{i:04d}.jpg"
                new_path = target_dir / new_filename
                cv2.imwrite(str(new_path), img_resized)
                
                # 生成对应的标签文件
                self.generate_label_file(new_filename.replace('.jpg', '.txt'), target_disease)
                
            except Exception as e:
                print(f"⚠️ 处理图像失败 {img_path}: {e}")
    
    def generate_label_file(self, label_filename, disease_class):
        """
        生成YOLO格式的标签文件
        
        Args:
            label_filename: 标签文件名
            disease_class: 病害类别
        """
        label_dir = self.processed_dir / "labels"
        label_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取类别ID
        class_names = list(self.disease_mapping.keys())
        class_id = class_names.index(disease_class)
        
        # 创建覆盖整个图像的边界框 (中心点0.5, 0.5, 宽高1.0, 1.0)
        label_content = f"{class_id} 0.5 0.5 1.0 1.0\n"
        
        label_path = label_dir / label_filename
        with open(label_path, 'w') as f:
            f.write(label_content)
    
    def split_multiclass_dataset(self, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1):
        """
        划分多类别数据集
        
        Args:
            train_ratio: 训练集比例
            val_ratio: 验证集比例  
            test_ratio: 测试集比例
        """
        print("📊 开始划分多类别数据集...")
        
        # 收集所有图像文件
        all_images = []
        all_labels = []
        
        for disease in self.disease_mapping.keys():
            disease_dir = self.processed_dir / "images" / disease
            if disease_dir.exists():
                for img_file in disease_dir.glob("*.jpg"):
                    all_images.append(img_file)
                    # 对应的标签文件
                    label_file = self.processed_dir / "labels" / img_file.name.replace('.jpg', '.txt')
                    all_labels.append(label_file)
        
        print(f"总计图像数: {len(all_images)}")
        
        # 第一次划分: 分离测试集
        train_val_images, test_images, train_val_labels, test_labels = train_test_split(
            all_images, all_labels, test_size=test_ratio, random_state=42, 
            stratify=[self.get_disease_from_path(img) for img in all_images]
        )
        
        # 第二次划分: 分离训练集和验证集
        val_size = val_ratio / (train_ratio + val_ratio)
        train_images, val_images, train_labels, val_labels = train_test_split(
            train_val_images, train_val_labels, test_size=val_size, random_state=42,
            stratify=[self.get_disease_from_path(img) for img in train_val_images]
        )
        
        # 复制文件到对应目录
        self.copy_files_to_split("train_multiclass", train_images, train_labels)
        self.copy_files_to_split("val_multiclass", val_images, val_labels)
        self.copy_files_to_split("test_multiclass", test_images, test_labels)
        
        print(f"✅ 数据集划分完成:")
        print(f"   训练集: {len(train_images)} 张")
        print(f"   验证集: {len(val_images)} 张")
        print(f"   测试集: {len(test_images)} 张")
    
    def get_disease_from_path(self, img_path):
        """从图像路径获取病害类别"""
        return img_path.parent.name
    
    def copy_files_to_split(self, split_name, images, labels):
        """复制文件到指定的数据集分割目录"""
        img_dir = self.base_dir / split_name / "images"
        label_dir = self.base_dir / split_name / "labels"
        
        for img_path, label_path in zip(images, labels):
            # 复制图像
            shutil.copy2(img_path, img_dir / img_path.name)
            # 复制标签
            if label_path.exists():
                shutil.copy2(label_path, label_dir / label_path.name)
    
    def generate_multiclass_config(self):
        """生成多类别数据集配置文件"""
        config = {
            "path": "./data",
            "train": "train_multiclass/images",
            "val": "val_multiclass/images", 
            "test": "test_multiclass/images",
            "nc": len(self.disease_mapping),
            "names": list(self.disease_mapping.keys())
        }
        
        config_path = self.base_dir / "dataset_multiclass.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ 生成配置文件: {config_path}")
        print("📋 配置内容:")
        for key, value in config.items():
            print(f"   {key}: {value}")
    
    def create_download_script(self):
        """创建数据集下载辅助脚本"""
        script_content = '''#!/bin/bash
# 云南烤烟病害数据集下载脚本

echo "🌱 云南烤烟病害数据集收集工具"
echo "=================================="

echo "📋 需要手动下载的数据集:"
echo "1. PlantVillage Dataset"
echo "   URL: https://www.kaggle.com/datasets/arjuntejaswi/plant-village"
echo "   下载到: data/raw/collected/plantvillage/"

echo ""
echo "2. Plant Pathology 2021 Challenge"  
echo "   URL: https://www.kaggle.com/c/plant-pathology-2021-fgvc8/data"
echo "   下载到: data/raw/collected/plant_pathology/"

echo ""
echo "📝 下载完成后请运行:"
echo "python scripts/collect_disease_datasets.py"

echo ""
echo "🔧 所需工具:"
echo "- Kaggle账户和API密钥"
echo "- kaggle命令行工具: pip install kaggle"
'''
        
        script_path = self.base_dir.parent / "download_datasets.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        print(f"✅ 创建下载脚本: {script_path}")

def main():
    """主函数"""
    print("🌱 云南烤烟病害数据集收集工具")
    print("=" * 40)
    
    collector = DiseaseDatasetCollector()
    
    # 显示下载指南
    collector.download_plantvillage_subset()
    
    # 创建下载脚本
    collector.create_download_script()
    
    print("\n🚀 使用指南:")
    print("1. 按照上述指南下载数据集")
    print("2. 运行: collector.process_collected_data('data/raw/collected/plantvillage')")
    print("3. 运行: collector.split_multiclass_dataset()")
    print("4. 开始训练多类别模型!")

if __name__ == "__main__":
    main()