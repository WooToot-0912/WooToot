#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有类别的标签文件是否正确
"""

import os
from pathlib import Path
from collections import defaultdict

def check_labels():
    """检查所有标签文件的类别ID"""
    print("🔍 检查所有类别标签文件...")
    
    # 期望的类别映射
    expected_mapping = {
        'healthy': 0,
        'mosaic_virus': 1, 
        'brown_spot': 2,
        'wildfire': 3,
        'bacterial_wilt': 4
    }
    
    # 检查目录
    label_dir = Path("data/balanced_5class/train/labels")
    
    if not label_dir.exists():
        print(f"❌ 目录不存在: {label_dir}")
        return
    
    # 统计每个类别的标签
    class_counts = defaultdict(int)
    class_samples = defaultdict(list)
    
    for label_file in label_dir.glob("*.txt"):
        try:
            # 从文件名判断类别
            filename = label_file.name
            for class_name in expected_mapping.keys():
                if filename.startswith(class_name + "_"):
                    # 读取文件内容
                    with open(label_file, 'r') as f:
                        content = f.read().strip()
                    
                    if content:
                        class_id = int(content.split()[0])
                        expected_id = expected_mapping[class_name]
                        
                        class_counts[class_name] += 1
                        
                        # 记录前几个样本
                        if len(class_samples[class_name]) < 3:
                            class_samples[class_name].append((filename, class_id, expected_id))
                    
                    break
        
        except Exception as e:
            print(f"❌ 处理文件失败 {label_file}: {e}")
    
    # 显示结果
    print("\n📊 标签检查结果:")
    print("=" * 60)
    
    total_correct = 0
    total_files = 0
    
    for class_name, expected_id in expected_mapping.items():
        count = class_counts[class_name]
        samples = class_samples[class_name]
        
        print(f"\n🏷️ {class_name} (期望ID: {expected_id}):")
        print(f"   📄 文件数量: {count}")
        
        if samples:
            all_correct = True
            for filename, actual_id, expected_id in samples:
                status = "✅" if actual_id == expected_id else "❌"
                print(f"   {status} {filename}: 实际ID={actual_id}, 期望ID={expected_id}")
                if actual_id == expected_id:
                    total_correct += 1
                total_files += 1
                if actual_id != expected_id:
                    all_correct = False
            
            if all_correct and len(samples) > 0:
                print(f"   ✅ 前{len(samples)}个样本标签正确")
        else:
            print(f"   ⚠️ 没有找到文件")
    
    print("\n" + "=" * 60)
    print(f"📈 总体统计:")
    print(f"   检查样本: {total_files}")
    print(f"   正确样本: {total_correct}")
    print(f"   准确率: {total_correct/total_files*100:.1f}%" if total_files > 0 else "   准确率: N/A")
    
    if total_correct == total_files and total_files > 0:
        print("🎉 所有检查的标签都正确！")
        return True
    else:
        print("⚠️ 发现标签错误，需要修复")
        return False

if __name__ == "__main__":
    check_labels()