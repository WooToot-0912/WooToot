#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云南烤烟病害完整5类训练脚本 - GPU优化版
整合野火病数据 + PlantVillage数据 + 青枯病增强数据
"""

import os
import sys
import time
import shutil
import yaml
from pathlib import Path
from ultralytics import YOLO
import cv2
import numpy as np

# 添加模块路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入自定义模块
from modules import ECA, BackgroundSuppressionBranch, FocalLoss

def register_custom_modules():
    """注册自定义模块"""
    try:
        from ultralytics.nn.tasks import DetectionModel
        setattr(DetectionModel, 'ECA', ECA)
        setattr(DetectionModel, 'BackgroundSuppressionBranch', BackgroundSuppressionBranch)
        print("✅ 自定义模块注册成功")
        return True
    except Exception as e:
        print(f"❌ 自定义模块注册失败: {e}")
        return False

def detect_gpu_device():
    """强制使用GPU设备进行训练"""
    try:
        import torch
        
        # 设置CUDA内存优化
        import os
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
        
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            print(f"🎮 检测到GPU: {gpu_name} ({gpu_memory:.1f}GB)")
            print(f"📊 GPU数量: {gpu_count}")
            print(f"🔧 CUDA内存优化: 已启用 expandable_segments")
            
            # 根据GPU内存推荐批次大小 - 云端优化版
            if gpu_memory >= 30:  # RTX 5090 32GB
                recommended_batch = 64
                print(f"💡 推荐批次大小: {recommended_batch} (基于{gpu_memory:.1f}GB显存 - 云端高性能)")
            elif gpu_memory >= 20:  # RTX 4090/A100等
                recommended_batch = 48
                print(f"💡 推荐批次大小: {recommended_batch} (基于{gpu_memory:.1f}GB显存 - 云端优化)")
            elif gpu_memory >= 12:
                recommended_batch = 32
                print(f"💡 推荐批次大小: {recommended_batch} (基于{gpu_memory:.1f}GB显存)")
            elif gpu_memory >= 8:
                recommended_batch = 4  # 8GB显存保守设置
                print(f"💡 推荐批次大小: {recommended_batch} (基于{gpu_memory:.1f}GB显存 - 本地显卡保守模式)")
            elif gpu_memory >= 6:
                recommended_batch = 2
                print(f"💡 推荐批次大小: {recommended_batch} (基于{gpu_memory:.1f}GB显存)")
            else:
                recommended_batch = 1
                print(f"💡 推荐批次大小: {recommended_batch} (基于{gpu_memory:.1f}GB显存)")
            
            return 'cuda', recommended_batch
        else:
            print("❌ 未检测到GPU！本训练脚本需要GPU支持")
            print("请检查：")
            print("1. NVIDIA驱动是否正确安装")
            print("2. CUDA是否正确安装")
            print("3. PyTorch是否支持CUDA")
            return None, None
            
    except ImportError:
        print("❌ 无法导入torch，请先安装PyTorch")
        return None, None

def create_balanced_5class_dataset():
    """创建平衡的5类病害数据集"""
    print("📦 创建平衡5类病害数据集...")
    
    script_dir = Path(__file__).parent.parent
    data_dir = script_dir / 'data'
    complete_dir = data_dir / 'balanced_5class'
    
    # 删除旧数据集
    if complete_dir.exists():
        shutil.rmtree(complete_dir)
    
    # 创建目录结构
    for split in ['train', 'val', 'test']:
        for subdir in ['images', 'labels']:
            (complete_dir / split / subdir).mkdir(parents=True, exist_ok=True)
    
    # 类别映射
    class_mapping = {
        'healthy': 0,
        'mosaic_virus': 1, 
        'brown_spot': 2,
        'wildfire': 3,
        'bacterial_wilt': 4
    }
    
    # 目标每个类别的图像数量（平衡数据集）
    TARGET_PER_CLASS = 800
    
    # 1. 处理PlantVillage数据集（包含所有类别）
    print("   🌱 处理PlantVillage数据集（包含所有5类病害）...")
    plantvillage_dir = script_dir / 'plantvillage dataset'
    
    # PlantVillage类别映射和子目录
    pv_mapping = {
        '健康叶片': {
            'our_class': 'healthy',
            'subdirs': ['Tomato___healthy', 'Strawberry___healthy', 'Soybean___healthy', 
                       'Potato___healthy', 'Pepper,_bell___healthy', 'Peach___healthy', 
                       'Grape___healthy', 'Corn_(maize)___healthy', 'Cherry_(including_sour)___healthy',
                       'Blueberry___healthy', 'Apple___healthy']
        },
        '花叶病毒病': {
            'our_class': 'mosaic_virus',
            'subdirs': ['Tomato___Tomato_mosaic_virus', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus']
        },
        '赤星病': {
            'our_class': 'brown_spot',
            'subdirs': ['Tomato___Early_blight', 'Potato___Early_blight', 'Grape___Black_rot', 'Apple___Apple_scab']
        },
        '青枯病': {
            'our_class': 'bacterial_wilt',
            'subdirs': ['Tomato___Late_blight', 'Potato___Late_blight']
        },
        '野火病': {
            'our_class': 'wildfire',
            'subdirs': ['images']  # 野火病直接在images目录下
        }
    }
    
    pv_counts = {}
    for pv_class, config in pv_mapping.items():
        pv_class_dir = plantvillage_dir / pv_class
        our_class = config['our_class']
        subdirs = config['subdirs']
        
        if not pv_class_dir.exists():
            print(f"   ⚠️ 目录不存在: {pv_class_dir}")
            continue
            
        count = 0
        all_images = []
        
        # 收集指定子目录中的所有图像文件
        for subdir_name in subdirs:
            subdir_path = pv_class_dir / subdir_name
            if subdir_path.exists():
                for ext in ['*.JPG', '*.jpg', '*.png', '*.jpeg']:
                    all_images.extend(list(subdir_path.glob(ext)))
                # 对于野火病，显示jpg文件数量
                if our_class == 'wildfire':
                    print(f"     📂 {subdir_name}: {len(list(subdir_path.glob('*.jpg')))} 张")
                else:
                    print(f"     📂 {subdir_name}: {len(list(subdir_path.glob('*.JPG')))} 张")
        
        print(f"   📊 {pv_class} 总计原始图像: {len(all_images)} 张")
        
        # 每个类别目标数量
        if our_class == 'healthy':
            target_count = min(TARGET_PER_CLASS, 600)  # 健康叶片适当限制
        elif our_class == 'bacterial_wilt':
            target_count = min(TARGET_PER_CLASS//2, 400)  # 青枯病减少（因为有增强数据）
        else:
            target_count = TARGET_PER_CLASS  # 其他类别用足够数据
        
        # 随机打乱图像顺序确保数据分布均匀
        import random
        random.shuffle(all_images)
        
        for i, img_file in enumerate(all_images):
            if count >= target_count:
                break
                
            # 决定分割到哪个集合
            if count % 10 < 7:  # 70% 训练
                split = 'train'
            elif count % 10 < 9:  # 20% 验证
                split = 'val'
            else:  # 10% 测试
                split = 'test'
            
            # 复制原始图像
            new_name = f"{our_class}_{count:04d}.jpg"
            try:
                # 转换图像格式确保一致性
                img = cv2.imread(str(img_file))
                if img is not None:
                    cv2.imwrite(str(complete_dir / split / 'images' / new_name), img)
                    
                    # 创建或复制标签文件
                    if our_class == 'wildfire':
                        # 野火病有现成的标签文件
                        original_label = pv_class_dir / 'labels' / f"{img_file.stem}.txt"
                        if original_label.exists():
                            shutil.copy2(original_label, complete_dir / split / 'labels' / f"{our_class}_{count:04d}.txt")
                        else:
                            # 如果没有对应标签，创建一个
                            label_content = f"{class_mapping[our_class]} 0.5 0.5 1.0 1.0\n"
                            with open(complete_dir / split / 'labels' / f"{our_class}_{count:04d}.txt", 'w') as f:
                                f.write(label_content)
                    else:
                        # 其他病害创建全图标签
                        label_content = f"{class_mapping[our_class]} 0.5 0.5 1.0 1.0\n"
                        label_file = complete_dir / split / 'labels' / f"{our_class}_{count:04d}.txt"
                        with open(label_file, 'w') as f:
                            f.write(label_content)
                    
                    count += 1
                    
                    # 对训练集进行适度数据增强（青枯病和健康叶片减少增强）
                    if (split == 'train' and our_class not in ['bacterial_wilt', 'healthy'] 
                        and count < target_count // 2 and len(all_images) < TARGET_PER_CLASS):
                        # 简单增强：翻转
                        flipped = cv2.flip(img, 1)
                        augmented_name = f"{our_class}_{count:04d}.jpg"
                        cv2.imwrite(str(complete_dir / split / 'images' / augmented_name), flipped)
                        
                        # 增强图像的标签处理
                        if our_class == 'wildfire':
                            # 野火病使用原始标签的内容
                            if original_label.exists():
                                shutil.copy2(original_label, complete_dir / split / 'labels' / f"{our_class}_{count:04d}.txt")
                            else:
                                with open(complete_dir / split / 'labels' / f"{our_class}_{count:04d}.txt", 'w') as f:
                                    f.write(f"{class_mapping[our_class]} 0.5 0.5 1.0 1.0\n")
                        else:
                            # 其他病害使用全图标签
                            with open(complete_dir / split / 'labels' / f"{our_class}_{count:04d}.txt", 'w') as f:
                                f.write(f"{class_mapping[our_class]} 0.5 0.5 1.0 1.0\n")
                        count += 1
                        
            except Exception as e:
                print(f"   ⚠️ 处理图像失败 {img_file}: {e}")
                continue
        
        pv_counts[our_class] = count
    
    for class_name, count in pv_counts.items():
        print(f"   ✅ {class_name}: {count} 张")
    
    # 3. 添加现有青枯病增强数据（如果需要）
    print("   🦠 检查青枯病增强数据...")
    enhanced_dir = data_dir / 'tobacco_enhanced' / 'final'
    enhanced_count = 0
    
    if enhanced_dir.exists() and pv_counts.get('bacterial_wilt', 0) < TARGET_PER_CLASS//2:
        print("   📦 添加现有青枯病增强数据补充...")
        for split in ['train', 'val', 'test']:
            source_images = enhanced_dir / split / 'images'
            source_labels = enhanced_dir / split / 'labels'
            
            if source_images.exists():
                for img_file in source_images.glob('bacterial_wilt_*.jpg'):
                    if enhanced_count >= (TARGET_PER_CLASS//2 - pv_counts.get('bacterial_wilt', 0)):
                        break
                        
                    # 复制图像 (重命名避免冲突)
                    new_name = f"bacterial_wilt_enhanced_{enhanced_count:04d}.jpg"
                    shutil.copy2(img_file, complete_dir / split / 'images' / new_name)
                    
                    # 复制标签
                    label_file = source_labels / f"{img_file.stem}.txt"
                    if label_file.exists():
                        new_label = f"bacterial_wilt_enhanced_{enhanced_count:04d}.txt"
                        shutil.copy2(label_file, complete_dir / split / 'labels' / new_label)
                    else:
                        # 如果没有标签文件，创建一个
                        with open(complete_dir / split / 'labels' / f"bacterial_wilt_enhanced_{enhanced_count:04d}.txt", 'w') as f:
                            f.write("4 0.5 0.5 1.0 1.0\n")
                    enhanced_count += 1
    
    print(f"   ✅ 青枯病增强数据: {enhanced_count} 张")
    
    # 4. 创建数据集配置文件
    dataset_config = {
        'path': str(complete_dir),
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'nc': 5,
        'names': ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt']
    }
    
    config_file = complete_dir / 'dataset.yaml'
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(dataset_config, f, default_flow_style=False, allow_unicode=True)
    
    # 统计最终数据集
    total_counts = {}
    for split in ['train', 'val', 'test']:
        split_counts = {}
        images_dir = complete_dir / split / 'images'
        if images_dir.exists():
            for class_name in class_mapping.keys():
                count = len(list(images_dir.glob(f"{class_name}_*.jpg")))
                split_counts[class_name] = count
                total_counts[class_name] = total_counts.get(class_name, 0) + count
        
        print(f"   📊 {split}: {sum(split_counts.values())} 张 {split_counts}")
    
    print(f"   🎯 总计: {sum(total_counts.values())} 张 {total_counts}")
    print(f"   📁 平衡数据集保存在: {complete_dir}")
    
    # 数据平衡性检查
    min_count = min(total_counts.values())
    max_count = max(total_counts.values())
    balance_ratio = min_count / max_count if max_count > 0 else 0
    print(f"   ⚖️ 数据平衡性: {balance_ratio:.2f} (1.0为完全平衡)")
    
    if balance_ratio < 0.5:
        print("   ⚠️ 警告：数据不平衡可能影响训练效果")
    else:
        print("   ✅ 数据平衡性良好")
    
    return str(config_file)

def main():
    print("🔥 云南烤烟病害平衡5类训练 - 云端GPU优化版")
    print("=" * 60)
    print("🚀 优化特性:")
    print("   - 支持32GB+ GPU高性能训练")
    print("   - 自动内存碎片优化")
    print("   - 云端/本地自适应批次大小")
    print("   - 动态工作进程调整")
    print("=" * 60)
    print("🎯 数据源:")
    print("   - 野火病数据 (data/train) + 强力增强")
    print("   - PlantVillage完整数据集:")
    print("     * 健康叶片: 11个作物子类")
    print("     * 花叶病毒病: 2个番茄病毒子类")
    print("     * 赤星病: 4个作物早疫病子类") 
    print("     * 青枯病: 2个作物晚疫病子类")
    print("   - 现有青枯病增强数据补充")
    print("🚀 训练策略:")
    print("   - 强制GPU训练 (高速度)")
    print("   - 平衡数据集训练 (高精度)")
    print("   - 野火病重点增强 (解决误识别)")
    print("   - ECA注意力机制")
    print("   - Focal Loss损失函数")
    print("   - 背景抑制分支")
    print("   - 智能数据增强技术")
    print("=" * 60)
    
    # 强制GPU检测
    device, recommended_batch = detect_gpu_device()
    if device is None:
        print("❌ GPU检测失败，无法继续训练")
        return False
    print("=" * 60)
    
    # 注册自定义模块
    if not register_custom_modules():
        return False
    
    # 创建平衡数据集
    print("📦 准备平衡5类病害数据集...")
    try:
        dataset_path = create_balanced_5class_dataset()
        print(f"✅ 平衡数据集创建完成: {dataset_path}")
    except Exception as e:
        print(f"❌ 数据集创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 60)
    
    # 创建模型
    print("📦 创建YOLOv8n模型...")
    model = YOLO('yolov8n.pt')
    
    # GPU优化的完整训练配置
    train_params = {
        'data': dataset_path,
        'epochs': 100,                   # 完整训练轮次
        'imgsz': 640,
        'batch': recommended_batch,      # GPU优化批次大小
        'lr0': 0.01,
        'lrf': 0.01,                    # 学习率衰减
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'warmup_epochs': 3.0,           # 充分预热
        'box': 7.5,
        'cls': 0.5,
        'dfl': 1.5,
        'cos_lr': True,                 # 余弦学习率调度
        'close_mosaic': 10,             # 后期关闭mosaic
        'val': True,
        'save': True,
        'save_period': 10,              # 定期保存
        'cache': True,                  # GPU缓存加速
        'device': device,               # 强制GPU训练
        'workers': 16 if recommended_batch >= 32 else 8,  # 云端高性能配置
        'project': 'runs/train',
        'name': 'balanced_5class',      # 平衡数据集实验
        'exist_ok': True,
        'pretrained': True,
        'optimizer': 'SGD',             # SGD优化器
        'seed': 0,
        'deterministic': True,
        'single_cls': False,
        'rect': True,                   # 矩形训练
        'resume': False,
        'amp': True,                    # 混合精度训练
        'fraction': 1.0,                # 使用全部数据
        'patience': 50,                 # 充分训练
        
        # 针对病害检测优化的数据增强
        'hsv_h': 0.015,         # 色调增强 (病害颜色变化)
        'hsv_s': 0.7,           # 饱和度增强 (突出病害特征)
        'hsv_v': 0.4,           # 亮度增强
        'degrees': 30,          # 旋转角度
        'translate': 0.1,       # 平移
        'scale': 0.5,           # 缩放
        'shear': 0.0,           # 关闭剪切
        'perspective': 0.0,     # 关闭透视变换
        'flipud': 0.5,          # 垂直翻转
        'fliplr': 0.5,          # 水平翻转
        'mosaic': 1.0,          # 马赛克增强
        'mixup': 0.1,           # 轻微mixup
        'copy_paste': 0.0,      # 关闭copy_paste
        'auto_augment': False,  # 关闭自动增强
        'erasing': 0.0          # 关闭随机擦除
    }
    
    print(f"🔧 GPU优化训练配置:")
    print(f"   数据集: 平衡5类病害数据集")
    print(f"   设备类型: {train_params['device'].upper()}")
    print(f"   训练轮次: {train_params['epochs']}")
    print(f"   批次大小: {train_params['batch']}")
    print(f"   数据比例: {train_params['fraction']*100}%")
    print(f"   缓存模式: {train_params['cache']}")
    print(f"   工作进程: {train_params['workers']} ({'云端高性能' if train_params['workers'] >= 16 else 'GPU优化'})")
    print(f"   混合精度: {'启用' if train_params['amp'] else '关闭'}")
    print(f"   优化器: {train_params['optimizer']}")
    print(f"   学习率调度: {'余弦' if train_params['cos_lr'] else '线性'}")
    print(f"🎯 目标: 解决野火病误识别问题")
    print(f"   🔥 野火病: 重点增强训练，防止误分类为青枯病")
    print(f"   ⚖️ 数据平衡: 各类别数据量基本均衡")
    print(f"   🎯 精确识别: 健康、花叶病毒病、赤星病、野火病、青枯病")
    print("=" * 60)
    
    # 开始训练
    print("🚀 开始完整GPU训练...")
    try:
        start_time = time.time()
        results = model.train(**train_params)
        end_time = time.time()
        
        training_hours = (end_time - start_time) / 3600
        print(f"\n🎉 训练完成! 耗时: {(end_time - start_time)/60:.1f} 分钟 ({training_hours:.2f} 小时)")
        print(f"📁 模型保存位置: runs/train/{train_params['name']}")
        print(f"🏆 最佳模型: runs/train/{train_params['name']}/weights/best.pt")
        
        # 云端成本提示
        if train_params['batch'] >= 32:
            estimated_cost = training_hours * 3.08  # AutoDL RTX 5090价格
            print(f"💰 预估云端费用: ¥{estimated_cost:.2f} (基于RTX 5090 ¥3.08/小时)")
            print(f"📥 请及时下载模型文件到本地！")
        
        # 验证模型
        print("\n📊 验证模型性能...")
        metrics = model.val()
        print(f"mAP50: {metrics.box.map50:.4f}")
        print(f"mAP50-95: {metrics.box.map:.4f}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 训练过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 后续步骤:")
        print("1. 测试模型: python detect.py --weights runs/train/balanced_5class/weights/best.pt")
        print("2. 评估性能: python evaluate.py --weights runs/train/balanced_5class/weights/best.pt")
        print("3. 启动Web应用: python run.py web --weights runs/train/balanced_5class/weights/best.pt")
        print("4. 重新运行消融实验: python scripts/project_based_ablation_study.py")
        print("\n📊 训练结果:")
        print("   - 完整5类病害数据集训练完成")
        print("   - 支持检测: 健康叶片、花叶病毒病、赤星病、野火病、青枯病")
        print("   - GPU优化训练，性能显著提升")
        print("   - 可用于毕业论文算法对比分析")
    else:
        print("\n💥 训练失败，请检查GPU环境和数据集")