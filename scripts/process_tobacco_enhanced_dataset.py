#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
烟草增强数据集处理脚本
处理和增强烟草病害数据集，包括数据清洗、增强和格式转换
"""

import os
import sys
import cv2
import numpy as np
import yaml
import shutil
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import albumentations as A
from sklearn.model_selection import train_test_split
import json

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

class TobaccoEnhancedDatasetProcessor:
    """烟草增强数据集处理器"""
    
    def __init__(self, source_dir: str, output_dir: str = "data/tobacco_enhanced"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 病害类别配置
        self.disease_classes = {
            'healthy': 0,
            'mosaic_virus': 1,
            'brown_spot': 2,
            'wildfire': 3,
            'bacterial_wilt': 4
        }
        
        # 数据增强配置
        self.augmentation_transforms = A.Compose([
            # 几何变换
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.3),
            A.Rotate(limit=30, p=0.5),
            A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.1, rotate_limit=15, p=0.5),
            
            # 颜色变换
            A.HueSaturationValue(hue_shift_limit=20, sat_shift_limit=30, val_shift_limit=20, p=0.5),
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
            A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1, p=0.3),
            
            # 模糊和噪声
            A.GaussianBlur(blur_limit=(1, 3), p=0.3),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
            
            # 其他增强
            A.RandomGamma(gamma_limit=(80, 120), p=0.3),
            A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=0.3),
        ])
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'augmented_images': 0,
            'class_distribution': {},
            'errors': []
        }
    
    def scan_source_directory(self):
        """扫描源目录结构"""
        print(f"📁 扫描源目录: {self.source_dir}")
        
        if not self.source_dir.exists():
            raise ValueError(f"源目录不存在: {self.source_dir}")
        
        image_files = []
        label_files = []
        
        # 支持的图像格式
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        # 递归扫描所有文件
        for file_path in self.source_dir.rglob('*'):
            if file_path.is_file():
                if file_path.suffix.lower() in image_extensions:
                    image_files.append(file_path)
                elif file_path.suffix.lower() == '.txt':
                    label_files.append(file_path)
        
        print(f"✅ 找到 {len(image_files)} 张图像文件")
        print(f"✅ 找到 {len(label_files)} 个标签文件")
        
        return image_files, label_files
    
    def parse_label_file(self, label_path: Path):
        """解析YOLO格式标签文件"""
        try:
            with open(label_path, 'r') as f:
                lines = f.readlines()
            
            annotations = []
            for line in lines:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 5:
                        class_id = int(parts[0])
                        x_center = float(parts[1])
                        y_center = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])
                        
                        annotations.append({
                            'class_id': class_id,
                            'x_center': x_center,
                            'y_center': y_center,
                            'width': width,
                            'height': height
                        })
            
            return annotations
            
        except Exception as e:
            self.stats['errors'].append(f"解析标签文件失败 {label_path}: {e}")
            return []
    
    def apply_augmentation(self, image: np.ndarray, annotations: list):
        """应用数据增强"""
        try:
            # 转换YOLO格式到像素坐标
            h, w = image.shape[:2]
            bboxes = []
            class_labels = []
            
            for ann in annotations:
                x_center = ann['x_center'] * w
                y_center = ann['y_center'] * h
                bbox_width = ann['width'] * w
                bbox_height = ann['height'] * h
                
                x_min = x_center - bbox_width / 2
                y_min = y_center - bbox_height / 2
                x_max = x_center + bbox_width / 2
                y_max = y_center + bbox_height / 2
                
                bboxes.append([x_min, y_min, x_max, y_max])
                class_labels.append(ann['class_id'])
            
            # 应用增强
            if bboxes:
                augmented = self.augmentation_transforms(
                    image=image,
                    bboxes=bboxes,
                    class_labels=class_labels
                )
                
                augmented_image = augmented['image']
                augmented_bboxes = augmented['bboxes']
                augmented_labels = augmented['class_labels']
                
                # 转换回YOLO格式
                augmented_annotations = []
                h_aug, w_aug = augmented_image.shape[:2]
                
                for bbox, label in zip(augmented_bboxes, augmented_labels):
                    x_min, y_min, x_max, y_max = bbox
                    
                    x_center = (x_min + x_max) / 2 / w_aug
                    y_center = (y_min + y_max) / 2 / h_aug
                    width = (x_max - x_min) / w_aug
                    height = (y_max - y_min) / h_aug
                    
                    augmented_annotations.append({
                        'class_id': int(label),
                        'x_center': x_center,
                        'y_center': y_center,
                        'width': width,
                        'height': height
                    })
                
                return augmented_image, augmented_annotations
            else:
                # 无边界框的情况，只增强图像
                augmented = self.augmentation_transforms(image=image)
                return augmented['image'], annotations
                    
            except Exception as e:
            self.stats['errors'].append(f"数据增强失败: {e}")
            return image, annotations
    
    def save_augmented_data(self, image: np.ndarray, annotations: list, 
                          output_image_path: Path, output_label_path: Path):
        """保存增强后的数据"""
        try:
            # 保存图像
            cv2.imwrite(str(output_image_path), image)
            
            # 保存标签
            with open(output_label_path, 'w') as f:
                for ann in annotations:
                    f.write(f"{ann['class_id']} {ann['x_center']:.6f} {ann['y_center']:.6f} "
                           f"{ann['width']:.6f} {ann['height']:.6f}\n")
            
            return True
            
        except Exception as e:
            self.stats['errors'].append(f"保存数据失败: {e}")
            return False
    
    def process_single_image(self, image_path: Path, label_path: Path = None, 
                           augment_count: int = 3):
        """处理单张图像"""
        try:
            # 读取图像
            image = cv2.imread(str(image_path))
            if image is None:
                self.stats['errors'].append(f"无法读取图像: {image_path}")
                return False
            
            # 解析标签
            annotations = []
            if label_path and label_path.exists():
                annotations = self.parse_label_file(label_path)
            
            # 推断类别（从文件名或路径）
            class_name = self.infer_class_from_path(image_path)
            if class_name not in self.disease_classes:
                class_name = 'healthy'  # 默认为健康
            
            class_id = self.disease_classes[class_name]
            
            # 更新统计
            if class_name not in self.stats['class_distribution']:
                self.stats['class_distribution'][class_name] = 0
            self.stats['class_distribution'][class_name] += 1
            
            # 创建输出目录
            class_output_dir = self.output_dir / class_name
            (class_output_dir / 'images').mkdir(parents=True, exist_ok=True)
            (class_output_dir / 'labels').mkdir(parents=True, exist_ok=True)
            
            # 保存原始图像
            original_name = image_path.stem
            original_image_output = class_output_dir / 'images' / f"{original_name}.jpg"
            original_label_output = class_output_dir / 'labels' / f"{original_name}.txt"
            
            cv2.imwrite(str(original_image_output), image)
            
            # 保存原始标签或创建默认标签
            if annotations:
                with open(original_label_output, 'w') as f:
                    for ann in annotations:
                        f.write(f"{ann['class_id']} {ann['x_center']:.6f} {ann['y_center']:.6f} "
                               f"{ann['width']:.6f} {ann['height']:.6f}\n")
            else:
                # 创建全图标签
                with open(original_label_output, 'w') as f:
                    f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            
            # 生成增强图像
            for i in range(augment_count):
                augmented_image, augmented_annotations = self.apply_augmentation(image, annotations)
                
                augmented_image_output = class_output_dir / 'images' / f"{original_name}_aug_{i:03d}.jpg"
                augmented_label_output = class_output_dir / 'labels' / f"{original_name}_aug_{i:03d}.txt"
                
                if self.save_augmented_data(augmented_image, augmented_annotations,
                                          augmented_image_output, augmented_label_output):
                    self.stats['augmented_images'] += 1
            
            self.stats['total_processed'] += 1
            return True
            
        except Exception as e:
            self.stats['errors'].append(f"处理图像失败 {image_path}: {e}")
            return False
    
    def infer_class_from_path(self, file_path: Path) -> str:
        """从文件路径推断病害类别"""
        path_str = str(file_path).lower()
        
        if 'healthy' in path_str or 'normal' in path_str:
            return 'healthy'
        elif 'mosaic' in path_str or 'virus' in path_str:
            return 'mosaic_virus'
        elif 'brown' in path_str or 'spot' in path_str:
            return 'brown_spot'
        elif 'wildfire' in path_str or 'fire' in path_str:
            return 'wildfire'
        elif 'bacterial' in path_str or 'wilt' in path_str:
            return 'bacterial_wilt'
        else:
            return 'healthy'  # 默认
    
    def create_dataset_yaml(self):
        """创建数据集配置文件"""
        dataset_config = {
            'path': str(self.output_dir.absolute()),
            'train': 'train/images',
            'val': 'val/images',
            'test': 'test/images',
            'nc': len(self.disease_classes),
            'names': list(self.disease_classes.keys())
        }
        
        yaml_path = self.output_dir / 'dataset.yaml'
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(dataset_config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"📝 数据集配置文件已保存: {yaml_path}")
    
    def split_dataset(self, train_ratio: float = 0.7, val_ratio: float = 0.2):
        """划分训练、验证和测试集"""
        print("📊 划分数据集...")
        
        # 创建目标目录
        for split in ['train', 'val', 'test']:
            (self.output_dir / split / 'images').mkdir(parents=True, exist_ok=True)
            (self.output_dir / split / 'labels').mkdir(parents=True, exist_ok=True)
        
        # 为每个类别划分数据
        for class_name in self.disease_classes.keys():
            class_dir = self.output_dir / class_name
            if not class_dir.exists():
                continue
            
            images_dir = class_dir / 'images'
            labels_dir = class_dir / 'labels'
            
            if not images_dir.exists():
                continue
            
            # 获取所有图像文件
            image_files = list(images_dir.glob('*.jpg'))
            
            if len(image_files) == 0:
                continue
            
            # 划分数据
            train_files, temp_files = train_test_split(
                image_files, train_size=train_ratio, random_state=42
            )
            
            val_files, test_files = train_test_split(
                temp_files, train_size=val_ratio/(1-train_ratio), random_state=42
            )
            
            # 复制文件到对应目录
            for split_name, file_list in [('train', train_files), ('val', val_files), ('test', test_files)]:
                for image_file in file_list:
                    label_file = labels_dir / f"{image_file.stem}.txt"
                    
                    # 复制图像
                    target_image = self.output_dir / split_name / 'images' / image_file.name
                    shutil.copy2(image_file, target_image)
                    
                    # 复制标签
                    if label_file.exists():
                        target_label = self.output_dir / split_name / 'labels' / label_file.name
                        shutil.copy2(label_file, target_label)
            
            print(f"✅ {class_name}: 训练{len(train_files)}, 验证{len(val_files)}, 测试{len(test_files)}")
    
    def generate_statistics_report(self):
        """生成统计报告"""
        print("\n📈 处理统计报告")
        print("=" * 50)
        print(f"📁 输出目录: {self.output_dir}")
        print(f"🖼️ 总处理图像: {self.stats['total_processed']}")
        print(f"🔄 增强图像数: {self.stats['augmented_images']}")
        print(f"❌ 错误数量: {len(self.stats['errors'])}")
        print()
        print("📊 类别分布:")
        for class_name, count in self.stats['class_distribution'].items():
            print(f"   {class_name}: {count}")
        
        if self.stats['errors']:
            print("\n❌ 错误详情:")
            for error in self.stats['errors'][:10]:  # 只显示前10个错误
                print(f"   {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... 还有 {len(self.stats['errors'])-10} 个错误")
        
        # 保存详细报告
        report_path = self.output_dir / 'processing_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n📝 详细报告已保存: {report_path}")
    
    def process_dataset(self, augment_count: int = 3):
        """处理整个数据集"""
        print("🚀 开始处理烟草增强数据集...")
        
        # 扫描源目录
        image_files, label_files = self.scan_source_directory()
        
        if not image_files:
            print("❌ 未找到图像文件")
            return False
        
        # 创建标签文件映射
        label_map = {}
        for label_file in label_files:
            label_map[label_file.stem] = label_file
        
        # 处理每张图像
        print(f"🔄 开始处理 {len(image_files)} 张图像...")
        
        for i, image_path in enumerate(image_files):
            if (i + 1) % 50 == 0:
                print(f"进度: {i + 1}/{len(image_files)}")
            
            # 查找对应的标签文件
            label_path = label_map.get(image_path.stem)
            
            # 处理图像
            self.process_single_image(image_path, label_path, augment_count)
        
        # 划分数据集
        self.split_dataset()
        
        # 创建数据集配置
        self.create_dataset_yaml()
        
        # 生成报告
        self.generate_statistics_report()
        
        print("✅ 数据集处理完成！")
        return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='烟草增强数据集处理')
    parser.add_argument('--source', type=str, required=True, help='源数据目录')
    parser.add_argument('--output', type=str, default='data/tobacco_enhanced', help='输出目录')
    parser.add_argument('--augment', type=int, default=3, help='每张图像的增强次数')
    
    args = parser.parse_args()
    
    # 创建处理器
    processor = TobaccoEnhancedDatasetProcessor(
        source_dir=args.source,
        output_dir=args.output
    )
    
    # 处理数据集
    success = processor.process_dataset(augment_count=args.augment)
    
    if success:
        print("🎉 数据集处理成功完成！")
    else:
        print("💥 数据集处理失败")

if __name__ == "__main__":
    main()