import os
import cv2
import numpy as np
import albumentations as A
from tqdm import tqdm
import glob
import shutil
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from sklearn.decomposition import PCA

def create_dataset_structure():
    """创建数据集目录结构"""
    for split in ['train', 'val', 'test']:
        for subdir in ['images', 'labels']:
            os.makedirs(f"data/{split}/{subdir}", exist_ok=True)
    print("数据集目录结构创建完成")

def process_raw_images(source_dirs, target_dir='data/processed/images'):
    """处理原始图像并复制到处理目录"""
    os.makedirs(target_dir, exist_ok=True)
    
    processed_count = 0
    for source_dir in source_dirs:
        if not os.path.exists(source_dir):
            print(f"目录不存在: {source_dir}")
            continue
            
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    src_path = os.path.join(root, file)
                    
                    # 读取图像
                    img = cv2.imread(src_path)
                    if img is None:
                        print(f"无法读取图像: {src_path}")
                        continue
                    
                    # 图像质量检查
                    if img.size == 0 or cv2.Laplacian(img, cv2.CV_64F).var() < 100:
                        print(f"跳过低质量图像: {src_path}")
                        continue
                    
                    # 生成目标文件名
                    rel_path = os.path.relpath(root, source_dir)
                    category = os.path.basename(rel_path)
                    dst_filename = f"{category}_{os.path.basename(src_path)}"
                    dst_path = os.path.join(target_dir, dst_filename)
                    
                    # 复制图像
                    shutil.copy(src_path, dst_path)
                    processed_count += 1
    
    print(f"处理完成，共处理 {processed_count} 张图像")
    return processed_count

def apply_augmentation(image_dir='data/processed/images', label_dir='data/processed/labels',
                      output_img_dir='data/augmented/images', output_label_dir='data/augmented/labels'):
    """应用数据增强"""
    os.makedirs(output_img_dir, exist_ok=True)
    os.makedirs(output_label_dir, exist_ok=True)
    
    # 定义数据增强管道
    transform = A.Compose([
        # 基本增强
        A.RandomRotate90(p=0.5),
        A.Rotate(limit=30, p=0.7),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.7),
        
        # 云南特色环境增强
        A.OneOf([
            A.RandomFog(fog_coef_lower=0.1, fog_coef_upper=0.3, p=0.5),  # 模拟山区雾气
            A.RandomRain(p=0.3),  # 模拟雨季环境
            A.RandomSunFlare(p=0.2),  # 模拟强光照
        ], p=0.5),
        
        # 背景干扰增强
        A.OneOf([
            A.CoarseDropout(max_holes=8, max_height=32, max_width=32, p=0.5),  # 模拟叶片遮挡
            A.GridDistortion(p=0.3),  # 模拟叶片弯曲
        ], p=0.5),
        
        # 病斑特征增强
        A.OneOf([
            A.Sharpen(alpha=(0.2, 0.5), p=0.5),  # 增强病斑边缘
            A.CLAHE(p=0.3),  # 增强对比度
        ], p=0.5),
    ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
    
    # 获取所有图像文件
    image_files = glob.glob(os.path.join(image_dir, '*.jpg')) + \
                  glob.glob(os.path.join(image_dir, '*.jpeg')) + \
                  glob.glob(os.path.join(image_dir, '*.png'))
    
    augmented_count = 0
    for img_path in tqdm(image_files, desc="数据增强"):
        # 读取图像
        img = cv2.imread(img_path)
        if img is None:
            continue
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 读取对应标签
        base_name = os.path.basename(img_path).rsplit('.', 1)[0]
        label_path = os.path.join(label_dir, f"{base_name}.txt")
        
        if not os.path.exists(label_path):
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
        for i in range(3):  # 每张图像生成3个增强版本
            augmented = transform(image=img, bboxes=annotations, class_labels=class_labels)
            aug_img = augmented['image']
            aug_bboxes = augmented['bboxes']
            aug_labels = augmented['class_labels']
            
            # 保存增强图像
            aug_img_path = os.path.join(output_img_dir, f"{base_name}_aug{i}.jpg")
            cv2.imwrite(aug_img_path, cv2.cvtColor(aug_img, cv2.COLOR_RGB2BGR))
            
            # 保存增强标签
            aug_label_path = os.path.join(output_label_dir, f"{base_name}_aug{i}.txt")
            with open(aug_label_path, 'w') as f:
                for j in range(len(aug_bboxes)):
                    bbox = aug_bboxes[j]
                    label = aug_labels[j]
                    f.write(f"{label} {bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}\n")
            
            augmented_count += 1
    
    print(f"数据增强完成，生成 {augmented_count} 张增强图像")
    return augmented_count

def split_dataset(processed_dir='data/processed', augmented_dir='data/augmented', train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
    """划分数据集"""
    # 获取所有图像和标签文件
    processed_images = glob.glob(os.path.join(processed_dir, 'images', '*.jpg')) + \
                      glob.glob(os.path.join(processed_dir, 'images', '*.jpeg')) + \
                      glob.glob(os.path.join(processed_dir, 'images', '*.png'))
    
    augmented_images = glob.glob(os.path.join(augmented_dir, 'images', '*.jpg')) + \
                      glob.glob(os.path.join(augmented_dir, 'images', '*.jpeg')) + \
                      glob.glob(os.path.join(augmented_dir, 'images', '*.png'))
    
    all_images = processed_images + augmented_images
    
    # 验证每个图像都有对应的标签
    valid_images = []
    for img_path in all_images:
        base_name = os.path.basename(img_path).rsplit('.', 1)[0]
        if 'processed' in img_path:
            label_path = os.path.join(processed_dir, 'labels', f"{base_name}.txt")
        else:
            label_path = os.path.join(augmented_dir, 'labels', f"{base_name}.txt")
        
        if os.path.exists(label_path):
            valid_images.append((img_path, label_path))
    
    # 按照比例划分数据集
    train_data, temp_data = train_test_split(valid_images, test_size=(val_ratio + test_ratio), random_state=42)
    val_data, test_data = train_test_split(temp_data, test_size=test_ratio/(val_ratio + test_ratio), random_state=42)
    
    # 创建数据集目录
    for split in ['train', 'val', 'test']:
        for subdir in ['images', 'labels']:
            os.makedirs(f"data/{split}/{subdir}", exist_ok=True)
    
    # 复制文件到对应目录
    for dataset, split in [(train_data, 'train'), (val_data, 'val'), (test_data, 'test')]:
        for img_path, label_path in dataset:
            img_filename = os.path.basename(img_path)
            label_filename = os.path.basename(label_path)
            
            shutil.copy(img_path, f"data/{split}/images/{img_filename}")
            shutil.copy(label_path, f"data/{split}/labels/{label_filename}")
    
    print(f"数据集划分完成: 训练集 {len(train_data)}张, 验证集 {len(val_data)}张, 测试集 {len(test_data)}张")
    return len(train_data), len(val_data), len(test_data)

def apply_smote_for_rare_classes(rare_class_id=4, target_count=500):
    """为稀有类别应用SMOTE过采样"""
    # 统计各类别样本数量
    class_counts = {}
    label_files = glob.glob('data/train/labels/*.txt')
    
    for label_file in label_files:
        with open(label_file, 'r') as f:
            for line in f:
                class_id = int(line.strip().split()[0])
                if class_id not in class_counts:
                    class_counts[class_id] = 0
                class_counts[class_id] += 1
    
    print("原始类别分布:", class_counts)
    
    # 如果稀有类别样本数足够，则不需要过采样
    if rare_class_id not in class_counts or class_counts[rare_class_id] >= target_count:
        print(f"类别 {rare_class_id} 样本数量充足，无需过采样")
        return 0
    
    # 提取稀有类别样本
    rare_samples = []
    rare_features = []
    rare_labels = []
    
    for label_file in label_files:
        with open(label_file, 'r') as f:
            content = f.read()
            if f"{rare_class_id} " in content:  # 包含稀有类别
                img_file = os.path.basename(label_file).replace('.txt', '.jpg')
                img_path = os.path.join('data/train/images', img_file)
                
                if os.path.exists(img_path):
                    # 简单特征提取
                    img = cv2.imread(img_path)
                    img = cv2.resize(img, (64, 64))
                    img_flat = img.flatten()
                    
                    rare_samples.append(img_path)
                    rare_features.append(img_flat)
                    rare_labels.append(0)  # 虚拟标签，SMOTE需要
    
    # 应用SMOTE过采样
    if len(rare_samples) >= 5:  # SMOTE需要至少5个样本
        rare_features = np.array(rare_features)
        rare_labels = np.array(rare_labels)
        
        # 降维以加速SMOTE
        pca = PCA(n_components=min(50, len(rare_features)))
        rare_features_pca = pca.fit_transform(rare_features)
        
        # 生成合成样本
        smote = SMOTE(sampling_strategy={0: target_count})
        X_resampled, _ = smote.fit_resample(rare_features_pca, rare_labels)
        
        # 将合成样本投影回原始空间
        synthetic_features = pca.inverse_transform(X_resampled[len(rare_features):])
        
        # 生成合成图像和标签
        synthetic_count = len(synthetic_features)
        print(f"为稀有类别 {rare_class_id} 生成了 {synthetic_count} 个合成样本")
        
        # 这里仅作为示例，实际应用中需要更复杂的图像重构和标签生成
        for i, feature in enumerate(synthetic_features):
            # 重构图像
            img_reconstructed = feature.reshape(64, 64, 3).astype(np.uint8)
            
            # 保存合成图像
            synthetic_img_path = f"data/train/images/synthetic_{rare_class_id}_{i}.jpg"
            cv2.imwrite(synthetic_img_path, img_reconstructed)
            
            # 创建对应的标签文件
            synthetic_label_path = f"data/train/labels/synthetic_{rare_class_id}_{i}.txt"
            
            # 生成简单的中心标签
            with open(synthetic_label_path, 'w') as f:
                f.write(f"{rare_class_id} 0.5 0.5 0.5 0.5\n")
        
        return synthetic_count
    else:
        print(f"类别 {rare_class_id} 样本数量不足5个，无法应用SMOTE")
        return 0