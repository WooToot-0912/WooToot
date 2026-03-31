#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨作物迁移学习数据处理脚本
将其他植物的相似病害数据映射到烟草病害检测任务
"""

import os
import cv2
import numpy as np
from pathlib import Path
import shutil
import yaml
import json
from sklearn.model_selection import train_test_split
import albumentations as A
from albumentations.pytorch import ToTensorV2

class CrossCropTransferProcessor:
    def __init__(self, output_dir="data/cross_crop_enhanced"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 病害映射关系 - 从其他植物病害到烟草病害
        self.disease_mapping = {
            # 健康叶片
            "healthy": {
                "source_classes": [
                    "Tomato___healthy",
                    "Pepper,_bell___healthy", 
                    "Potato___healthy",
                    "Apple___healthy",
                    "Cherry_(including_sour)___healthy",
                    "Corn_(maize)___healthy",
                    "Grape___healthy"
                ],
                "target_class": "healthy",
                "class_id": 0,
                "color": (0, 255, 0)  # 绿色
            },
            
            # 花叶病毒病 - 病毒性病害
            "mosaic_virus": {
                "source_classes": [
                    "Tomato___Tomato_mosaic_virus",
                    "Tomato___Tomato_Yellow_Leaf_Curl_Virus"
                ],
                "target_class": "mosaic_virus", 
                "class_id": 1,
                "color": (255, 0, 0)  # 红色
            },
            
            # 赤星病 - 真菌性病害，圆形病斑
            "brown_spot": {
                "source_classes": [
                    "Apple___Apple_scab",
                    "Potato___Early_blight",
                    "Tomato___Early_blight",
                    "Grape___Black_rot",
                    "Strawberry___Leaf_scorch"
                ],
                "target_class": "brown_spot",
                "class_id": 2, 
                "color": (0, 165, 255)  # 橙色
            },
            
            # 野火病 - 细菌性病害 (已有数据，保持兼容)
            "wildfire": {
                "source_classes": [
                    "Tomato___Bacterial_spot",
                    "Pepper,_bell___Bacterial_spot",
                    "Peach___Bacterial_spot"
                ],
                "target_class": "wildfire",
                "class_id": 3,
                "color": (0, 255, 255)  # 黄色
            },
            
            # 青枯病 - 细菌性萎蔫
            "bacterial_wilt": {
                "source_classes": [
                    "Tomato___Late_blight",
                    "Potato___Late_blight"
                ],
                "target_class": "bacterial_wilt",
                "class_id": 4,
                "color": (255, 0, 255)  # 紫色
            }
        }
        
        # 数据增强配置
        self.setup_augmentations()
    
    def setup_augmentations(self):
        """设置数据增强策略"""
        # 基础增强 - 保持病害特征
        self.basic_augment = A.Compose([
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.2),
            A.RandomRotate90(p=0.3),
            A.Rotate(limit=15, p=0.3),
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
            A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=15, p=0.3)
        ])
        
        # 高级增强 - 适应烟草特征
        self.tobacco_adapt_augment = A.Compose([
            # 模拟烟草叶片的颜色特征
            A.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.2, hue=0.05, p=0.4),
            # 模拟田间光照条件
            A.RandomGamma(gamma_limit=(80, 120), p=0.3),
            # 增强绿色通道，适应烟草叶片
            A.ChannelShuffle(p=0.1),
            # 模拟不同拍摄条件
            A.GaussNoise(var_limit=(10, 50), p=0.2),
            A.Blur(blur_limit=3, p=0.1)
        ])
    
    def process_source_dataset(self, source_path, dataset_name="unknown"):
        """
        处理源数据集，将其他植物病害映射到烟草病害
        
        Args:
            source_path: 源数据集路径
            dataset_name: 数据集名称
        """
        source_path = Path(source_path)
        if not source_path.exists():
            print(f"❌ 源数据集路径不存在: {source_path}")
            return
        
        print(f"🔄 开始处理数据集: {dataset_name}")
        print(f"📁 源路径: {source_path}")
        
        # 统计信息
        stats = {disease: 0 for disease in self.disease_mapping.keys()}
        
        # 遍历源数据集中的所有类别
        for class_dir in source_path.iterdir():
            if not class_dir.is_dir():
                continue
                
            class_name = class_dir.name
            target_disease = self.find_target_disease(class_name)
            
            if target_disease:
                print(f"📊 映射: {class_name} → {target_disease}")
                processed_count = self.process_disease_class(
                    class_dir, target_disease, dataset_name
                )
                stats[target_disease] += processed_count
            else:
                print(f"⚠️ 跳过未映射的类别: {class_name}")
        
        print(f"\n📈 {dataset_name} 处理统计:")
        for disease, count in stats.items():
            print(f"   {disease}: {count} 张图像")
    
    def find_target_disease(self, source_class):
        """查找源类别对应的目标烟草病害"""
        for target_disease, mapping in self.disease_mapping.items():
            if source_class in mapping["source_classes"]:
                return target_disease
        return None
    
    def process_disease_class(self, class_dir, target_disease, dataset_name):
        """
        处理单个病害类别的图像
        
        Args:
            class_dir: 源类别目录
            target_disease: 目标病害类别
            dataset_name: 数据集名称
            
        Returns:
            int: 处理的图像数量
        """
        # 创建输出目录
        output_img_dir = self.output_dir / "images" / target_disease
        output_label_dir = self.output_dir / "labels" / target_disease
        output_img_dir.mkdir(parents=True, exist_ok=True)
        output_label_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取所有图像文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(class_dir.glob(f"*{ext}"))
            image_files.extend(class_dir.glob(f"*{ext.upper()}"))
        
        processed_count = 0
        
        for i, img_path in enumerate(image_files):
            try:
                # 读取图像
                img = cv2.imread(str(img_path))
                if img is None:
                    continue
                
                # 预处理图像
                processed_img = self.preprocess_image(img, target_disease)
                
                # 生成文件名
                base_name = f"{target_disease}_{dataset_name}_{class_dir.name}_{i:04d}"
                img_filename = f"{base_name}.jpg"
                label_filename = f"{base_name}.txt"
                
                # 保存处理后的图像
                img_path_output = output_img_dir / img_filename
                cv2.imwrite(str(img_path_output), processed_img)
                
                # 生成YOLO格式标签
                self.generate_yolo_label(
                    output_label_dir / label_filename, 
                    target_disease
                )
                
                # 应用数据增强生成更多样本
                if processed_count < 100:  # 限制每个类别的增强数量
                    self.apply_augmentation(
                        processed_img, target_disease, dataset_name, 
                        class_dir.name, i, output_img_dir, output_label_dir
                    )
                
                processed_count += 1
                
            except Exception as e:
                print(f"⚠️ 处理图像失败 {img_path}: {e}")
        
        return processed_count
    
    def preprocess_image(self, img, target_disease):
        """
        预处理图像，适应烟草叶片特征
        
        Args:
            img: 输入图像
            target_disease: 目标病害类型
            
        Returns:
            numpy.ndarray: 处理后的图像
        """
        # 调整尺寸
        img_resized = cv2.resize(img, (640, 640))
        
        # 根据病害类型进行特定的颜色调整
        if target_disease == "healthy":
            # 增强绿色通道，模拟健康烟草叶片
            img_resized[:, :, 1] = np.clip(img_resized[:, :, 1] * 1.1, 0, 255)
            
        elif target_disease == "mosaic_virus":
            # 轻微增强对比度，突出花叶症状
            img_resized = cv2.convertScaleAbs(img_resized, alpha=1.1, beta=10)
            
        elif target_disease == "brown_spot":
            # 增强红色和棕色通道，突出病斑
            img_resized[:, :, 2] = np.clip(img_resized[:, :, 2] * 1.05, 0, 255)
            
        elif target_disease == "bacterial_wilt":
            # 轻微黄化处理，模拟萎蔫症状
            img_resized[:, :, 0] = np.clip(img_resized[:, :, 0] * 1.05, 0, 255)
            img_resized[:, :, 1] = np.clip(img_resized[:, :, 1] * 1.1, 0, 255)
        
        return img_resized
    
    def apply_augmentation(self, img, target_disease, dataset_name, class_name, 
                          img_idx, output_img_dir, output_label_dir):
        """应用数据增强"""
        try:
            # 应用基础增强
            augmented1 = self.basic_augment(image=img)['image']
            base_name1 = f"{target_disease}_{dataset_name}_{class_name}_{img_idx:04d}_aug1"
            cv2.imwrite(str(output_img_dir / f"{base_name1}.jpg"), augmented1)
            self.generate_yolo_label(output_label_dir / f"{base_name1}.txt", target_disease)
            
            # 应用烟草适应增强
            augmented2 = self.tobacco_adapt_augment(image=img)['image']
            base_name2 = f"{target_disease}_{dataset_name}_{class_name}_{img_idx:04d}_aug2"
            cv2.imwrite(str(output_img_dir / f"{base_name2}.jpg"), augmented2)
            self.generate_yolo_label(output_label_dir / f"{base_name2}.txt", target_disease)
            
        except Exception as e:
            print(f"⚠️ 数据增强失败: {e}")
    
    def generate_yolo_label(self, label_path, target_disease):
        """生成YOLO格式标签文件"""
        class_id = self.disease_mapping[target_disease]["class_id"]
        
        # 创建覆盖整个图像的边界框
        label_content = f"{class_id} 0.5 0.5 1.0 1.0\n"
        
        with open(label_path, 'w') as f:
            f.write(label_content)
    
    def organize_final_dataset(self, include_wildfire_data=True):
        """整理最终的数据集结构"""
        print("📁 整理最终数据集结构...")
        
        # 创建最终数据集目录
        final_dir = self.output_dir / "final"
        splits = ["train", "val", "test"]
        
        for split in splits:
            (final_dir / split / "images").mkdir(parents=True, exist_ok=True)
            (final_dir / split / "labels").mkdir(parents=True, exist_ok=True)
        
        # 收集所有图像和标签
        all_files = []
        
        for disease in self.disease_mapping.keys():
            img_dir = self.output_dir / "images" / disease
            label_dir = self.output_dir / "labels" / disease
            
            if img_dir.exists():
                for img_file in img_dir.glob("*.jpg"):
                    label_file = label_dir / img_file.name.replace('.jpg', '.txt')
                    if label_file.exists():
                        all_files.append((img_file, label_file, disease))
        
        # 包含现有的野火病数据
        if include_wildfire_data and Path("data/train").exists():
            print("🔄 整合现有野火病数据...")
            for img_file in Path("data/train/images").glob("*.jpg"):
                label_file = Path("data/train/labels") / img_file.name.replace('.jpg', '.txt')
                if label_file.exists():
                    all_files.append((img_file, label_file, "wildfire"))
        
        print(f"📊 总计收集到 {len(all_files)} 个图像-标签对")
        
        # 按病害类别分层划分数据集
        train_files, temp_files = train_test_split(
            all_files, test_size=0.3, random_state=42,
            stratify=[disease for _, _, disease in all_files]
        )
        
        val_files, test_files = train_test_split(
            temp_files, test_size=0.33, random_state=42,
            stratify=[disease for _, _, disease in temp_files]
        )
        
        # 复制文件到对应目录
        self.copy_files_to_split(final_dir / "train", train_files)
        self.copy_files_to_split(final_dir / "val", val_files)
        self.copy_files_to_split(final_dir / "test", test_files)
        
        print(f"✅ 数据集划分完成:")
        print(f"   训练集: {len(train_files)} 张")
        print(f"   验证集: {len(val_files)} 张") 
        print(f"   测试集: {len(test_files)} 张")
        
        # 生成配置文件
        self.generate_dataset_config(final_dir)
        
        return final_dir
    
    def copy_files_to_split(self, split_dir, file_list):
        """复制文件到指定的分割目录"""
        for img_file, label_file, disease in file_list:
            # 复制图像
            shutil.copy2(img_file, split_dir / "images" / img_file.name)
            # 复制标签
            shutil.copy2(label_file, split_dir / "labels" / label_file.name)
    
    def generate_dataset_config(self, dataset_dir):
        """生成数据集配置文件"""
        config = {
            "path": str(dataset_dir.relative_to(Path.cwd())),
            "train": "train/images",
            "val": "val/images",
            "test": "test/images",
            "nc": len(self.disease_mapping),
            "names": [mapping["target_class"] for mapping in self.disease_mapping.values()]
        }
        
        config_path = dataset_dir / "dataset.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ 生成配置文件: {config_path}")
        print("📋 配置内容:")
        for key, value in config.items():
            print(f"   {key}: {value}")
        
        return config_path
    
    def create_usage_guide(self):
        """创建使用指南"""
        guide_content = """# 跨作物迁移学习数据集使用指南

## 数据处理步骤

1. **准备源数据集**
   ```python
   processor = CrossCropTransferProcessor()
   
   # 处理PlantVillage数据集
   processor.process_source_dataset('path/to/plantvillage', 'plantvillage')
   
   # 处理Plant Pathology数据集  
   processor.process_source_dataset('path/to/plant_pathology', 'pathology')
   ```

2. **整理最终数据集**
   ```python
   final_dataset_dir = processor.organize_final_dataset(include_wildfire_data=True)
   ```

3. **训练模型**
   ```bash
   python train.py --data data/cross_crop_enhanced/final/dataset.yaml --epochs 100
   ```

## 病害映射关系

- healthy: 多种作物的健康叶片 → 烟草健康叶片
- mosaic_virus: 番茄花叶病毒 → 烟草花叶病毒病
- brown_spot: 苹果疥疮病等 → 烟草赤星病  
- wildfire: 番茄细菌斑点病 → 烟草野火病
- bacterial_wilt: 番茄晚疫病 → 烟草青枯病

## 数据增强策略

1. **基础增强**: 翻转、旋转、亮度对比度调整
2. **烟草适应增强**: 颜色调整、模拟田间条件
3. **高级增强**: MixUp、CutMix等混合策略

## 模型训练建议

1. **预训练**: 使用大规模植物病害数据
2. **域适应**: 使用相似病害数据中间训练
3. **微调**: 使用烟草特有数据最终优化
"""
        
        guide_path = self.output_dir / "使用指南.md"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"✅ 创建使用指南: {guide_path}")

def main():
    """主函数 - 演示用法"""
    print("🌱 跨作物迁移学习数据处理器")
    print("=" * 40)
    
    processor = CrossCropTransferProcessor()
    
    # 创建使用指南
    processor.create_usage_guide()
    
    print("\n🚀 使用方法:")
    print("1. 准备其他植物病害数据集")
    print("2. 调用 process_source_dataset() 处理数据")
    print("3. 调用 organize_final_dataset() 整理数据集")
    print("4. 开始跨作物迁移学习训练!")
    
    print("\n📋 支持的病害映射:")
    for disease, mapping in processor.disease_mapping.items():
        print(f"   {disease}: {len(mapping['source_classes'])} 个源类别")

if __name__ == "__main__":
    main()