#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云南烤烟病害检测模型综合评估脚本
对比RTX 5090训练模型与基线模型的性能
"""

import os
import time
import torch
import numpy as np
from ultralytics import YOLO
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pandas as pd

def comprehensive_evaluation():
    """综合评估RTX 5090训练模型"""
    print("🔬 云南烤烟病害检测模型综合评估")
    print("=" * 60)
    
    # 模型路径
    rtx5090_model = "models/rtx5090_trained_best.pt"
    baseline_model = "yolov8n.pt"
    
    # 数据集配置
    data_config = "data/dataset.yaml"
    
    # 结果目录
    results_dir = Path("results/comprehensive_evaluation")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print("📊 评估配置:")
    print(f"   RTX 5090模型: {rtx5090_model}")
    print(f"   基线模型: {baseline_model}")
    print(f"   数据集: {data_config}")
    print("=" * 60)
    
    # 评估结果存储
    evaluation_results = {}
    
    # 评估RTX 5090模型
    print("\n🚀 评估RTX 5090训练模型...")
    if os.path.exists(rtx5090_model):
        model_rtx = YOLO(rtx5090_model)
        
        start_time = time.time()
        metrics_rtx = model_rtx.val(data=data_config, split='test')
        eval_time_rtx = time.time() - start_time
        
        evaluation_results['RTX 5090'] = {
            'mAP50': metrics_rtx.box.map50,
            'mAP50-95': metrics_rtx.box.map,
            'precision': metrics_rtx.box.mp,
            'recall': metrics_rtx.box.mr,
            'eval_time': eval_time_rtx
        }
        
        print(f"✅ RTX 5090模型评估完成")
        print(f"   mAP50: {metrics_rtx.box.map50:.4f}")
        print(f"   mAP50-95: {metrics_rtx.box.map:.4f}")
        print(f"   评估时间: {eval_time_rtx:.2f}秒")
    else:
        print(f"❌ RTX 5090模型文件不存在: {rtx5090_model}")
    
    # 评估基线模型
    print("\n📋 评估基线YOLOv8n模型...")
    model_baseline = YOLO(baseline_model)
    
    start_time = time.time()
    metrics_baseline = model_baseline.val(data=data_config, split='test')
    eval_time_baseline = time.time() - start_time
    
    evaluation_results['YOLOv8n'] = {
        'mAP50': metrics_baseline.box.map50,
        'mAP50-95': metrics_baseline.box.map,
        'precision': metrics_baseline.box.mp,
        'recall': metrics_baseline.box.mr,
        'eval_time': eval_time_baseline
    }
    
    print(f"✅ 基线模型评估完成")
    print(f"   mAP50: {metrics_baseline.box.map50:.4f}")
    print(f"   mAP50-95: {metrics_baseline.box.map:.4f}")
    print(f"   评估时间: {eval_time_baseline:.2f}秒")
    
    # 生成对比报告
    print("\n📈 生成对比报告...")
    generate_comparison_report(evaluation_results, results_dir)
    
    # 推理速度测试
    print("\n⚡ 推理速度测试...")
    speed_test(rtx5090_model, baseline_model, results_dir)
    
    print(f"\n✅ 综合评估完成！结果保存在: {results_dir}")
    
    return evaluation_results

def generate_comparison_report(results, output_dir):
    """生成对比报告"""
    # 创建对比表格
    df = pd.DataFrame(results).T
    
    # 保存到CSV
    csv_path = output_dir / "model_comparison.csv"
    df.to_csv(csv_path)
    print(f"📊 对比表格保存至: {csv_path}")
    
    # 生成可视化图表
    if len(results) >= 2:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # mAP50对比
        models = list(results.keys())
        map50_values = [results[model]['mAP50'] for model in models]
        
        axes[0, 0].bar(models, map50_values, color=['#FF6B6B', '#4ECDC4'])
        axes[0, 0].set_title('mAP50 对比')
        axes[0, 0].set_ylabel('mAP50')
        for i, v in enumerate(map50_values):
            axes[0, 0].text(i, v + 0.01, f'{v:.3f}', ha='center')
        
        # mAP50-95对比
        map5095_values = [results[model]['mAP50-95'] for model in models]
        axes[0, 1].bar(models, map5095_values, color=['#FF6B6B', '#4ECDC4'])
        axes[0, 1].set_title('mAP50-95 对比')
        axes[0, 1].set_ylabel('mAP50-95')
        for i, v in enumerate(map5095_values):
            axes[0, 1].text(i, v + 0.01, f'{v:.3f}', ha='center')
        
        # Precision对比
        precision_values = [results[model]['precision'] for model in models]
        axes[1, 0].bar(models, precision_values, color=['#FF6B6B', '#4ECDC4'])
        axes[1, 0].set_title('Precision 对比')
        axes[1, 0].set_ylabel('Precision')
        for i, v in enumerate(precision_values):
            axes[1, 0].text(i, v + 0.01, f'{v:.3f}', ha='center')
        
        # Recall对比
        recall_values = [results[model]['recall'] for model in models]
        axes[1, 1].bar(models, recall_values, color=['#FF6B6B', '#4ECDC4'])
        axes[1, 1].set_title('Recall 对比')
        axes[1, 1].set_ylabel('Recall')
        for i, v in enumerate(recall_values):
            axes[1, 1].text(i, v + 0.01, f'{v:.3f}', ha='center')
        
        plt.tight_layout()
        chart_path = output_dir / "performance_comparison.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📈 性能对比图保存至: {chart_path}")

def speed_test(rtx5090_model, baseline_model, output_dir, num_tests=100):
    """推理速度测试"""
    print(f"   测试图像数量: {num_tests}")
    
    # 创建测试图像
    test_img = torch.randn(1, 3, 640, 640)
    
    speed_results = {}
    
    # 测试RTX 5090模型
    if os.path.exists(rtx5090_model):
        model_rtx = YOLO(rtx5090_model)
        
        # 预热
        for _ in range(10):
            _ = model_rtx.predict(test_img, verbose=False)
        
        # 速度测试
        start_time = time.time()
        for _ in range(num_tests):
            _ = model_rtx.predict(test_img, verbose=False)
        rtx_time = time.time() - start_time
        
        speed_results['RTX 5090'] = {
            'total_time': rtx_time,
            'avg_time': rtx_time / num_tests,
            'fps': num_tests / rtx_time
        }
        
        print(f"   RTX 5090模型: {rtx_time/num_tests*1000:.2f}ms/张, {num_tests/rtx_time:.1f}FPS")
    
    # 测试基线模型
    model_baseline = YOLO(baseline_model)
    
    # 预热
    for _ in range(10):
        _ = model_baseline.predict(test_img, verbose=False)
    
    # 速度测试
    start_time = time.time()
    for _ in range(num_tests):
        _ = model_baseline.predict(test_img, verbose=False)
    baseline_time = time.time() - start_time
    
    speed_results['YOLOv8n'] = {
        'total_time': baseline_time,
        'avg_time': baseline_time / num_tests,
        'fps': num_tests / baseline_time
    }
    
    print(f"   基线模型: {baseline_time/num_tests*1000:.2f}ms/张, {num_tests/baseline_time:.1f}FPS")
    
    # 保存速度测试结果
    speed_df = pd.DataFrame(speed_results).T
    speed_csv = output_dir / "speed_comparison.csv"
    speed_df.to_csv(speed_csv)
    print(f"⚡ 速度测试结果保存至: {speed_csv}")
    
    return speed_results

if __name__ == "__main__":
    try:
        results = comprehensive_evaluation()
        
        print("\n🎉 评估总结:")
        for model_name, metrics in results.items():
            print(f"\n{model_name}:")
            print(f"   mAP50: {metrics['mAP50']:.4f}")
            print(f"   mAP50-95: {metrics['mAP50-95']:.4f}")
            print(f"   Precision: {metrics['precision']:.4f}")
            print(f"   Recall: {metrics['recall']:.4f}")
        
        if 'RTX 5090' in results and 'YOLOv8n' in results:
            improvement = {
                'mAP50': (results['RTX 5090']['mAP50'] - results['YOLOv8n']['mAP50']) / results['YOLOv8n']['mAP50'] * 100,
                'mAP50-95': (results['RTX 5090']['mAP50-95'] - results['YOLOv8n']['mAP50-95']) / results['YOLOv8n']['mAP50-95'] * 100
            }
            
            print(f"\n📈 RTX 5090模型相对提升:")
            print(f"   mAP50提升: {improvement['mAP50']:+.1f}%")
            print(f"   mAP50-95提升: {improvement['mAP50-95']:+.1f}%")
        
    except Exception as e:
        print(f"❌ 评估过程中出现错误: {e}")
        import traceback
        traceback.print_exc()