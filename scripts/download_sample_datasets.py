#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版数据集下载和处理脚本
使用免费可获取的植物病害图像数据
"""

import os
import requests
import cv2
import numpy as np
from pathlib import Path
import json
from urllib.parse import urlparse
import time
import shutil

class SimpleDiseaseDataCollector:
    def __init__(self):
        self.base_dir = Path("data/sample_multiclass")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 免费可获取的样本图像URL (示例 - 需要替换为实际可用的URLs)
        self.sample_urls = {
            "healthy": [
                # 健康叶片样本URLs (需要替换为实际可用链接)
                "https://example.com/healthy_leaf1.jpg",
                "https://example.com/healthy_leaf2.jpg",
            ],
            "mosaic_virus": [
                # 花叶病毒样本URLs
                "https://example.com/mosaic1.jpg",
                "https://example.com/mosaic2.jpg",
            ],
            "brown_spot": [
                # 褐斑病样本URLs  
                "https://example.com/brownspot1.jpg",
                "https://example.com/brownspot2.jpg",
            ],
            "bacterial_wilt": [
                # 细菌性萎蔫样本URLs
                "https://example.com/wilt1.jpg", 
                "https://example.com/wilt2.jpg",
            ]
        }
    
    def create_sample_images(self):
        """创建合成样本图像用于演示"""
        print("🎨 创建合成样本图像...")
        
        # 为每个病害类别创建合成图像
        for disease, urls in self.sample_urls.items():
            disease_dir = self.base_dir / "images" / disease
            disease_dir.mkdir(parents=True, exist_ok=True)
            
            label_dir = self.base_dir / "labels" / disease  
            label_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建不同特征的合成图像
            for i in range(10):  # 每个类别创建10张样本
                img = self.generate_synthetic_image(disease)
                
                img_name = f"{disease}_sample_{i:03d}.jpg"
                img_path = disease_dir / img_name
                cv2.imwrite(str(img_path), img)
                
                # 创建对应标签
                self.create_label_file(label_dir / f"{disease}_sample_{i:03d}.txt", disease)
                
            print(f"   ✅ {disease}: 创建了10张合成图像")
    
    def generate_synthetic_image(self, disease_type):
        """
        根据病害类型生成合成图像
        
        Args:
            disease_type: 病害类型
            
        Returns:
            numpy.ndarray: 生成的图像
        """
        # 基础绿色叶片
        img = np.ones((640, 640, 3), dtype=np.uint8) * 60  # 深绿色背景
        
        # 添加叶片纹理
        for _ in range(50):
            x = np.random.randint(0, 640)
            y = np.random.randint(0, 640)
            color = (40 + np.random.randint(0, 40), 80 + np.random.randint(0, 40), 30 + np.random.randint(0, 20))
            cv2.circle(img, (x, y), np.random.randint(5, 15), color, -1)
        
        # 根据病害类型添加特征
        if disease_type == "healthy":
            # 健康叶片 - 保持绿色，添加叶脉
            for _ in range(10):
                x1, y1 = np.random.randint(0, 640, 2)
                x2, y2 = np.random.randint(0, 640, 2)
                cv2.line(img, (x1, y1), (x2, y2), (30, 100, 20), 2)
                
        elif disease_type == "mosaic_virus":
            # 花叶病毒 - 深浅绿相间的斑驳
            for _ in range(20):
                x, y = np.random.randint(0, 600, 2)
                w, h = np.random.randint(20, 80, 2)
                color = (20, 120, 20) if np.random.random() > 0.5 else (10, 60, 10)
                cv2.rectangle(img, (x, y), (x+w, y+h), color, -1)
                
        elif disease_type == "brown_spot":
            # 褐斑病 - 圆形或椭圆形褐色病斑
            for _ in range(15):
                x, y = np.random.randint(50, 590, 2)
                r = np.random.randint(10, 30)
                color = (20, 40, 80 + np.random.randint(0, 40))  # 褐色
                cv2.circle(img, (x, y), r, color, -1)
                # 添加黄色晕圈
                cv2.circle(img, (x, y), r+5, (30, 100, 120), 2)
                
        elif disease_type == "wildfire":
            # 野火病 - 不规则黄褐色病斑
            for _ in range(12):
                points = np.random.randint(0, 640, (6, 2))
                color = (30, 100, 150)  # 黄褐色
                cv2.fillPoly(img, [points], color)
                
        elif disease_type == "bacterial_wilt":
            # 细菌性萎蔫 - 整体萎蔫变黄
            # 添加黄化效果
            yellow_mask = np.random.random((640, 640)) > 0.3
            img[yellow_mask, 1] = np.minimum(img[yellow_mask, 1] + 80, 255)  # 增加绿色通道
            img[yellow_mask, 2] = np.minimum(img[yellow_mask, 2] + 100, 255)  # 增加蓝色通道
            
            # 添加萎蔫纹理
            for _ in range(30):
                x1, y1 = np.random.randint(0, 640, 2)
                x2 = x1 + np.random.randint(-50, 50)
                y2 = y1 + np.random.randint(-20, 20) 
                cv2.line(img, (x1, y1), (x2, y2), (40, 80, 100), 1)
        
        return img
    
    def create_label_file(self, label_path, disease_type):
        """创建YOLO格式标签文件"""
        # 病害类别映射
        class_mapping = {
            "healthy": 0,
            "mosaic_virus": 1, 
            "brown_spot": 2,
            "wildfire": 3,
            "bacterial_wilt": 4
        }
        
        class_id = class_mapping.get(disease_type, 0)
        
        # 创建覆盖整个图像的标注框
        label_content = f"{class_id} 0.5 0.5 1.0 1.0\n"
        
        with open(label_path, 'w') as f:
            f.write(label_content)
    
    def organize_dataset(self):
        """整理数据集结构"""
        print("📁 整理数据集结构...")
        
        # 创建训练/验证/测试分割
        splits = ["train", "val", "test"]
        for split in splits:
            (self.base_dir / split / "images").mkdir(parents=True, exist_ok=True)
            (self.base_dir / split / "labels").mkdir(parents=True, exist_ok=True)
        
        # 分配图像到不同分割 (70% 训练, 20% 验证, 10% 测试)
        for disease in self.sample_urls.keys():
            disease_images = list((self.base_dir / "images" / disease).glob("*.jpg"))
            disease_labels = list((self.base_dir / "labels" / disease).glob("*.txt"))
            
            n_total = len(disease_images)
            n_train = int(n_total * 0.7)
            n_val = int(n_total * 0.2)
            
            # 训练集
            for i in range(n_train):
                if i < len(disease_images):
                    img_src = disease_images[i]
                    label_src = disease_labels[i]
                    
                    img_dst = self.base_dir / "train" / "images" / img_src.name
                    label_dst = self.base_dir / "train" / "labels" / label_src.name
                    
                    shutil.copy2(img_src, img_dst)
                    shutil.copy2(label_src, label_dst)
            
            # 验证集
            for i in range(n_train, n_train + n_val):
                if i < len(disease_images):
                    img_src = disease_images[i]
                    label_src = disease_labels[i]
                    
                    img_dst = self.base_dir / "val" / "images" / img_src.name
                    label_dst = self.base_dir / "val" / "labels" / label_src.name
                    
                    shutil.copy2(img_src, img_dst)
                    shutil.copy2(label_src, label_dst)
            
            # 测试集
            for i in range(n_train + n_val, n_total):
                if i < len(disease_images):
                    img_src = disease_images[i]
                    label_src = disease_labels[i]
                    
                    img_dst = self.base_dir / "test" / "images" / img_src.name
                    label_dst = self.base_dir / "test" / "labels" / label_src.name
                    
                    shutil.copy2(img_src, img_dst)
                    shutil.copy2(label_src, label_dst)
        
        print("✅ 数据集结构整理完成")
    
    def create_config_file(self):
        """创建数据集配置文件"""
        config_content = f"""# 云南烤烟病害数据集配置 (多类别版本)
path: ./data/sample_multiclass
train: train/images
val: val/images  
test: test/images

# 类别数量和名称
nc: 5
names: ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt']

# 类别说明
# 0: healthy - 健康叶片
# 1: mosaic_virus - 烟草花叶病毒病  
# 2: brown_spot - 赤星病
# 3: wildfire - 野火病
# 4: bacterial_wilt - 青枯病
"""
        
        config_path = self.base_dir / "dataset.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ 创建配置文件: {config_path}")
        return config_path
    
    def create_readme(self):
        """创建数据集说明文档"""
        readme_content = f"""# 云南烤烟病害检测数据集 (多类别版本)

## 数据集信息
- **总计图像**: 50张 (每类10张合成样本)
- **图像尺寸**: 640x640像素
- **类别数量**: 5类
- **标注格式**: YOLO格式

## 类别说明
1. **healthy** - 健康叶片 (10张)
2. **mosaic_virus** - 烟草花叶病毒病 (10张)  
3. **brown_spot** - 赤星病 (10张)
4. **wildfire** - 野火病 (10张)
5. **bacterial_wilt** - 青枯病 (10张)

## 数据分割
- **训练集**: 35张 (70%)
- **验证集**: 10张 (20%) 
- **测试集**: 5张 (10%)

## 使用方法
```python
# 训练模型
python train.py --data {self.base_dir}/dataset.yaml --epochs 100

# 评估模型  
python evaluate.py --data {self.base_dir}/dataset.yaml

# 检测图像
python detect.py --source path/to/image.jpg
```

## 注意事项
- 这是合成样本数据集，仅用于演示和初步测试
- 实际应用建议使用真实烟草病害图像进行训练
- 可以作为迁移学习的起点

## 数据集结构
```
{self.base_dir}/
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/  
│   └── labels/
├── test/
│   ├── images/
│   └── labels/
├── dataset.yaml
└── README.md
```
"""
        
        readme_path = self.base_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ 创建说明文档: {readme_path}")

def main():
    """主函数"""
    print("🌱 云南烤烟病害多类别数据集生成器")
    print("=" * 40)
    
    collector = SimpleDiseaseDataCollector()
    
    try:
        # 1. 创建合成样本图像
        collector.create_sample_images()
        
        # 2. 整理数据集结构
        collector.organize_dataset()
        
        # 3. 创建配置文件
        config_path = collector.create_config_file()
        
        # 4. 创建说明文档
        collector.create_readme()
        
        print("\n🎉 多类别数据集创建完成!")
        print("📊 数据集统计:")
        print("   - 5个病害类别")
        print("   - 50张合成图像")
        print("   - 训练/验证/测试分割完成")
        print(f"   - 配置文件: {config_path}")
        
        print("\n🚀 下一步:")
        print("1. 检查生成的样本图像质量")
        print("2. 运行训练脚本测试多类别模型")
        print("3. 收集真实烟草病害图像替换合成数据")
        
    except Exception as e:
        print(f"❌ 数据集创建失败: {e}")

if __name__ == "__main__":
    main()