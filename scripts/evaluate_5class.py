#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云南烤烟病害5类检测模型评估脚本
支持详细的性能分析和可视化
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from ultralytics import YOLO
import yaml
import cv2

# 添加模块路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入自定义模块
from modules import ECA, BackgroundSuppressionBranch, FocalLoss

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

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

def load_class_info():
    """加载类别信息"""
    try:
        with open('data/dataset.yaml', 'r', encoding='utf-8') as f:
            data_cfg = yaml.safe_load(f)
            class_names = data_cfg.get('names', ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt'])
    except Exception as e:
        print(f"警告: 无法加载数据集配置: {e}")
        class_names = ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt']
    
    # 中文类别名称映射
    class_names_cn = {
        'healthy': '健康叶片',
        'mosaic_virus': '花叶病毒病',
        'brown_spot': '赤星病', 
        'wildfire': '野火病',
        'bacterial_wilt': '青枯病'
    }
    
    return class_names, class_names_cn

def evaluate_model(weights_path, data_config='data/dataset.yaml'):
    """评估模型性能"""
    print(f"📊 开始评估模型: {weights_path}")
    
    # 注册自定义模块
    if not register_custom_modules():
        return None
    
    # 加载模型
    try:
        model = YOLO(weights_path)
        print("✅ 模型加载成功")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return None
    
    # 运行验证
    try:
        print("🔍 运行模型验证...")
        metrics = model.val(data=data_config, verbose=True)
        print("✅ 验证完成")
        return metrics
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return None

def create_evaluation_report(metrics, weights_path, output_dir):
    """创建详细的评估报告"""
    class_names, class_names_cn = load_class_info()
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 提取关键指标
    if hasattr(metrics, 'box'):
        # 总体指标
        overall_metrics = {
            'mAP@0.5': float(metrics.box.map50),
            'mAP@0.5:0.95': float(metrics.box.map),
            'Precision': float(metrics.box.mp),
            'Recall': float(metrics.box.mr),
            'F1-Score': 2 * float(metrics.box.mp) * float(metrics.box.mr) / (float(metrics.box.mp) + float(metrics.box.mr) + 1e-6)
        }
        
        # 每类指标
        class_metrics = {}
        if hasattr(metrics.box, 'maps') and len(metrics.box.maps) == len(class_names):
            for i, class_name in enumerate(class_names):
                class_metrics[class_name] = {
                    'mAP@0.5': float(metrics.box.maps[i]),
                    'name_cn': class_names_cn.get(class_name, class_name)
                }
    else:
        print("⚠️ 无法提取详细指标，使用默认值")
        overall_metrics = {
            'mAP@0.5': 0.0,
            'mAP@0.5:0.95': 0.0,
            'Precision': 0.0,
            'Recall': 0.0,
            'F1-Score': 0.0
        }
        class_metrics = {}
    
    # 生成评估报告
    report = {
        'model_path': str(weights_path),
        'evaluation_time': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'overall_metrics': overall_metrics,
        'class_metrics': class_metrics,
        'summary': {
            'total_classes': len(class_names),
            'best_class': max(class_metrics.keys(), key=lambda x: class_metrics[x]['mAP@0.5']) if class_metrics else 'N/A',
            'worst_class': min(class_metrics.keys(), key=lambda x: class_metrics[x]['mAP@0.5']) if class_metrics else 'N/A'
        }
    }
    
    # 保存JSON报告
    with open(output_path / 'evaluation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 生成可视化报告
    create_visualizations(report, output_path)
    
    # 生成文本报告
    create_text_report(report, output_path)
    
    print(f"📋 评估报告已生成: {output_path}")
    return report

def create_visualizations(report, output_path):
    """创建可视化图表"""
    class_names, class_names_cn = load_class_info()
    
    # 1. 总体指标柱状图
    plt.figure(figsize=(10, 6))
    metrics_names = ['mAP@0.5', 'mAP@0.5:0.95', 'Precision', 'Recall', 'F1-Score']
    metrics_values = [report['overall_metrics'][m] for m in metrics_names]
    
    bars = plt.bar(metrics_names, metrics_values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
    plt.title('云南烤烟病害检测模型 - 总体性能指标', fontsize=16, fontweight='bold')
    plt.ylabel('得分', fontsize=12)
    plt.ylim(0, 1.0)
    
    # 添加数值标签
    for bar, value in zip(bars, metrics_values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path / 'overall_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. 各类别mAP对比
    if report['class_metrics']:
        plt.figure(figsize=(12, 8))
        class_names_list = list(report['class_metrics'].keys())
        class_names_cn_list = [report['class_metrics'][cls]['name_cn'] for cls in class_names_list]
        map_values = [report['class_metrics'][cls]['mAP@0.5'] for cls in class_names_list]
        
        # 创建颜色映射
        colors = ['#2ECC71', '#E74C3C', '#F39C12', '#F1C40F', '#9B59B6']
        
        bars = plt.bar(class_names_cn_list, map_values, color=colors[:len(class_names_list)])
        plt.title('各病害类别检测精度 (mAP@0.5)', fontsize=16, fontweight='bold')
        plt.ylabel('mAP@0.5', fontsize=12)
        plt.ylim(0, 1.0)
        
        # 添加数值标签
        for bar, value in zip(bars, map_values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path / 'class_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()

def create_text_report(report, output_path):
    """生成文本格式的评估报告"""
    report_text = f"""
# 云南烤烟病害检测模型评估报告

## 基本信息
- 模型路径: {report['model_path']}
- 评估时间: {report['evaluation_time']}
- 检测类别数: {report['summary']['total_classes']}

## 总体性能指标

| 指标 | 数值 |
|------|------|
| mAP@0.5 | {report['overall_metrics']['mAP@0.5']:.4f} |
| mAP@0.5:0.95 | {report['overall_metrics']['mAP@0.5:0.95']:.4f} |
| 精确率 (Precision) | {report['overall_metrics']['Precision']:.4f} |
| 召回率 (Recall) | {report['overall_metrics']['Recall']:.4f} |
| F1-Score | {report['overall_metrics']['F1-Score']:.4f} |

## 各类别详细指标

"""
    
    if report['class_metrics']:
        for class_name, metrics in report['class_metrics'].items():
            report_text += f"### {metrics['name_cn']} ({class_name})\n"
            report_text += f"- mAP@0.5: {metrics['mAP@0.5']:.4f}\n\n"
        
        report_text += f"## 性能分析\n\n"
        report_text += f"- 最佳检测类别: {report['class_metrics'][report['summary']['best_class']]['name_cn']}\n"
        report_text += f"- 需改进类别: {report['class_metrics'][report['summary']['worst_class']]['name_cn']}\n\n"
    
    report_text += f"""
## 模型评价

根据评估结果：
- 整体mAP@0.5达到 {report['overall_metrics']['mAP@0.5']:.4f}
- F1-Score为 {report['overall_metrics']['F1-Score']:.4f}

### 建议
1. 如果mAP@0.5 > 0.7，模型性能良好，可以投入使用
2. 如果mAP@0.5 在 0.5-0.7之间，建议增加训练数据或调整参数
3. 如果mAP@0.5 < 0.5，建议重新检查数据质量和模型配置

生成时间: {report['evaluation_time']}
"""
    
    # 保存文本报告
    with open(output_path / 'evaluation_report.md', 'w', encoding='utf-8') as f:
        f.write(report_text)

def main():
    """主函数"""
    print("📊 云南烤烟病害5类检测模型评估器")
    print("=" * 60)
    
    # 查找最新的训练结果
    runs_dir = Path("runs/train")
    if not runs_dir.exists():
        print("❌ 没有找到训练结果目录")
        return
    
    # 获取所有训练结果目录
    train_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
    if not train_dirs:
        print("❌ 没有找到训练结果")
        return
    
    # 按修改时间排序，获取最新的
    latest_dir = max(train_dirs, key=lambda x: x.stat().st_mtime)
    weights_path = latest_dir / "weights" / "best.pt"
    
    if not weights_path.exists():
        print(f"❌ 没有找到模型权重文件: {weights_path}")
        return
    
    print(f"🔍 找到最新训练模型: {weights_path}")
    
    # 评估模型
    metrics = evaluate_model(weights_path)
    
    if metrics is None:
        print("❌ 模型评估失败")
        return
    
    # 生成报告
    output_dir = f"results/evaluation_{latest_dir.name}"
    report = create_evaluation_report(metrics, weights_path, output_dir)
    
    # 显示结果摘要
    print("\n📋 评估结果摘要:")
    print(f"   mAP@0.5: {report['overall_metrics']['mAP@0.5']:.4f}")
    print(f"   mAP@0.5:0.95: {report['overall_metrics']['mAP@0.5:0.95']:.4f}")
    print(f"   精确率: {report['overall_metrics']['Precision']:.4f}")
    print(f"   召回率: {report['overall_metrics']['Recall']:.4f}")
    print(f"   F1-Score: {report['overall_metrics']['F1-Score']:.4f}")
    
    print(f"\n📁 详细报告保存位置: {output_dir}")
    print("   - evaluation_report.json (JSON格式)")
    print("   - evaluation_report.md (Markdown格式)")
    print("   - overall_metrics.png (总体指标图)")
    print("   - class_metrics.png (分类指标图)")

if __name__ == "__main__":
    main()