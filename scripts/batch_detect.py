#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云南烤烟病害批量检测脚本
支持文件夹批量检测和结果统计分析
"""

import os
import sys
import cv2
import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO
import yaml
import numpy as np

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
    except:
        class_names = ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt']
    
    # 中文名称和颜色映射
    class_info = {
        'healthy': {'name_cn': '健康叶片', 'color': (0, 255, 0), 'severity': 0},
        'mosaic_virus': {'name_cn': '花叶病毒病', 'color': (255, 0, 0), 'severity': 3},
        'brown_spot': {'name_cn': '赤星病', 'color': (0, 165, 255), 'severity': 2},
        'wildfire': {'name_cn': '野火病', 'color': (0, 255, 255), 'severity': 3},
        'bacterial_wilt': {'name_cn': '青枯病', 'color': (255, 0, 255), 'severity': 4}
    }
    
    return class_names, class_info

def batch_detect(model, image_dir, output_dir, conf_threshold=0.5):
    """批量检测图片"""
    image_dir = Path(image_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 支持的图像格式
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    
    # 收集所有图像文件
    image_files = []
    for ext in image_extensions:
        image_files.extend(image_dir.glob(f"*{ext}"))
        image_files.extend(image_dir.glob(f"*{ext.upper()}"))
    
    if not image_files:
        print(f"❌ 在 {image_dir} 中没有找到图像文件")
        return []
    
    print(f"📁 找到 {len(image_files)} 张图像，开始批量检测...")
    
    class_names, class_info = load_class_info()
    detection_results = []
    
    for i, img_path in enumerate(image_files, 1):
        print(f"🔍 处理 ({i}/{len(image_files)}): {img_path.name}")
        
        try:
            # 读取图像
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"⚠️ 无法读取图像: {img_path}")
                continue
            
            # 运行检测
            results = model(img, conf=conf_threshold)
            result = results[0]
            
            # 处理检测结果
            detections = []
            img_result = img.copy()
            
            if len(result.boxes) > 0:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    if cls_id < len(class_names):
                        class_name = class_names[cls_id]
                        class_cn = class_info[class_name]['name_cn']
                        color = class_info[class_name]['color']
                        severity = class_info[class_name]['severity']
                        
                        # 记录检测结果
                        detections.append({
                            'class_id': cls_id,
                            'class_name': class_name,
                            'class_cn': class_cn,
                            'confidence': conf,
                            'bbox': [x1, y1, x2, y2],
                            'severity': severity
                        })
                        
                        # 绘制检测框
                        cv2.rectangle(img_result, (x1, y1), (x2, y2), color, 2)
                        
                        # 添加标签
                        label = f"{class_cn} {conf:.2f}"
                        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                        cv2.rectangle(img_result, (x1, y1 - label_size[1] - 10), 
                                    (x1 + label_size[0], y1), color, -1)
                        cv2.putText(img_result, label, (x1, y1 - 5), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # 保存检测结果图像
            output_img_path = output_dir / f"detected_{img_path.name}"
            cv2.imwrite(str(output_img_path), img_result)
            
            # 记录整体结果
            result_record = {
                'image_name': img_path.name,
                'image_path': str(img_path),
                'output_path': str(output_img_path),
                'total_detections': len(detections),
                'detections': detections,
                'health_status': 'healthy' if not detections or all(d['class_name'] == 'healthy' for d in detections) else 'diseased',
                'max_severity': max([d['severity'] for d in detections], default=0),
                'dominant_disease': max(detections, key=lambda x: x['confidence'])['class_cn'] if detections else 'healthy'
            }
            
            detection_results.append(result_record)
            
        except Exception as e:
            print(f"❌ 处理 {img_path.name} 时出错: {e}")
            continue
    
    print(f"✅ 批量检测完成，共处理 {len(detection_results)} 张图像")
    return detection_results

def create_analysis_report(detection_results, output_dir):
    """创建分析报告"""
    output_dir = Path(output_dir)
    class_names, class_info = load_class_info()
    
    # 统计分析
    total_images = len(detection_results)
    healthy_count = sum(1 for r in detection_results if r['health_status'] == 'healthy')
    diseased_count = total_images - healthy_count
    
    # 病害类型统计
    disease_stats = {}
    severity_stats = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    
    for result in detection_results:
        for detection in result['detections']:
            class_name = detection['class_name']
            severity = detection['severity']
            
            if class_name not in disease_stats:
                disease_stats[class_name] = 0
            disease_stats[class_name] += 1
            severity_stats[severity] += 1
    
    # 生成统计图表
    create_statistics_charts(total_images, healthy_count, diseased_count, 
                           disease_stats, severity_stats, class_info, output_dir)
    
    # 生成详细报告
    report = {
        'summary': {
            'total_images': total_images,
            'healthy_images': healthy_count,
            'diseased_images': diseased_count,
            'health_rate': healthy_count / total_images if total_images > 0 else 0,
            'disease_rate': diseased_count / total_images if total_images > 0 else 0
        },
        'disease_statistics': disease_stats,
        'severity_distribution': severity_stats,
        'detailed_results': detection_results,
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 保存JSON报告
    with open(output_dir / 'batch_detection_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 生成Excel报告
    create_excel_report(detection_results, output_dir)
    
    # 生成文本摘要
    create_text_summary(report, output_dir)
    
    return report

def create_statistics_charts(total_images, healthy_count, diseased_count, 
                           disease_stats, severity_stats, class_info, output_dir):
    """创建统计图表"""
    
    # 1. 健康状态饼图
    plt.figure(figsize=(10, 8))
    
    plt.subplot(2, 2, 1)
    labels = ['健康叶片', '病害叶片']
    sizes = [healthy_count, diseased_count]
    colors = ['#2ECC71', '#E74C3C']
    
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('叶片健康状态分布', fontweight='bold')
    
    # 2. 病害类型分布
    plt.subplot(2, 2, 2)
    if disease_stats:
        disease_names = [class_info[name]['name_cn'] for name in disease_stats.keys()]
        disease_counts = list(disease_stats.values())
        disease_colors = [class_info[name]['color'] for name in disease_stats.keys()]
        # 转换BGR到RGB
        disease_colors = [(c[2]/255, c[1]/255, c[0]/255) for c in disease_colors]
        
        plt.bar(disease_names, disease_counts, color=disease_colors)
        plt.title('病害类型检测统计', fontweight='bold')
        plt.xticks(rotation=45)
        plt.ylabel('检测次数')
    
    # 3. 严重程度分布
    plt.subplot(2, 2, 3)
    severity_labels = ['健康', '轻微', '中等', '严重', '极严重']
    severity_counts = [severity_stats[i] for i in range(5)]
    severity_colors = ['#2ECC71', '#F1C40F', '#F39C12', '#E74C3C', '#8B0000']
    
    plt.bar(severity_labels, severity_counts, color=severity_colors)
    plt.title('病害严重程度分布', fontweight='bold')
    plt.ylabel('检测次数')
    plt.xticks(rotation=45)
    
    # 4. 整体健康率
    plt.subplot(2, 2, 4)
    health_rate = healthy_count / total_images if total_images > 0 else 0
    disease_rate = 1 - health_rate
    
    plt.barh(['健康率', '患病率'], [health_rate, disease_rate], 
             color=['#2ECC71', '#E74C3C'])
    plt.title('整体健康指标', fontweight='bold')
    plt.xlabel('比例')
    
    # 添加数值标签
    plt.text(health_rate/2, 0, f'{health_rate:.1%}', 
             ha='center', va='center', fontweight='bold', color='white')
    plt.text(health_rate + disease_rate/2, 1, f'{disease_rate:.1%}', 
             ha='center', va='center', fontweight='bold', color='white')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'detection_statistics.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_excel_report(detection_results, output_dir):
    """创建Excel格式的详细报告"""
    # 准备数据
    rows = []
    for result in detection_results:
        if result['detections']:
            for detection in result['detections']:
                rows.append({
                    '图像名称': result['image_name'],
                    '检测类别': detection['class_cn'],
                    '置信度': f"{detection['confidence']:.3f}",
                    '严重程度': detection['severity'],
                    '健康状态': '健康' if result['health_status'] == 'healthy' else '患病',
                    '主要病害': result['dominant_disease']
                })
        else:
            rows.append({
                '图像名称': result['image_name'],
                '检测类别': '健康叶片',
                '置信度': 'N/A',
                '严重程度': 0,
                '健康状态': '健康',
                '主要病害': '健康叶片'
            })
    
    # 创建DataFrame并保存
    df = pd.DataFrame(rows)
    df.to_excel(output_dir / 'detection_details.xlsx', index=False, engine='openpyxl')

def create_text_summary(report, output_dir):
    """创建文本摘要报告"""
    summary_text = f"""
# 云南烤烟病害批量检测报告

## 检测摘要
- 检测时间: {report['analysis_time']}
- 总图像数: {report['summary']['total_images']}
- 健康图像: {report['summary']['healthy_images']} ({report['summary']['health_rate']:.1%})
- 患病图像: {report['summary']['diseased_images']} ({report['summary']['disease_rate']:.1%})

## 病害分布
"""
    
    class_names, class_info = load_class_info()
    for disease, count in report['disease_statistics'].items():
        disease_cn = class_info[disease]['name_cn']
        summary_text += f"- {disease_cn}: {count} 次检测\n"
    
    summary_text += f"""
## 健康评估
- 整体健康率: {report['summary']['health_rate']:.1%}
- 建议关注: {'需要重点防治' if report['summary']['disease_rate'] > 0.3 else '整体状况良好'}

## 报告文件
- 详细数据: batch_detection_report.json
- Excel报告: detection_details.xlsx  
- 统计图表: detection_statistics.png
- 检测结果图片: detected_*.jpg

生成时间: {report['analysis_time']}
"""
    
    with open(output_dir / 'detection_summary.md', 'w', encoding='utf-8') as f:
        f.write(summary_text)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='云南烤烟病害批量检测')
    parser.add_argument('--weights', type=str, help='模型权重路径')
    parser.add_argument('--source', type=str, help='图像文件夹路径')
    parser.add_argument('--conf', type=float, default=0.5, help='置信度阈值')
    parser.add_argument('--output', type=str, default='results/batch_detection', help='输出目录')
    
    args = parser.parse_args()
    
    print("🔍 云南烤烟病害批量检测系统")
    print("=" * 50)
    
    # 确定模型路径
    if args.weights:
        weights_path = args.weights
    else:
        # 自动查找最新训练的模型
        runs_dir = Path("runs/train")
        if runs_dir.exists():
            train_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
            if train_dirs:
                latest_dir = max(train_dirs, key=lambda x: x.stat().st_mtime)
                weights_path = latest_dir / "weights" / "best.pt"
            else:
                weights_path = "yolov8n.pt"
        else:
            weights_path = "yolov8n.pt"
    
    # 确定图像源
    if args.source:
        image_dir = args.source
    else:
        # 默认使用wildfire目录
        if Path("wildfire").exists():
            image_dir = "wildfire"
        else:
            print("❌ 请指定图像文件夹路径 --source")
            return
    
    print(f"📦 使用模型: {weights_path}")
    print(f"📁 图像源: {image_dir}")
    print(f"🎯 置信度阈值: {args.conf}")
    print(f"📄 输出目录: {args.output}")
    
    # 注册自定义模块
    if not register_custom_modules():
        return
    
    # 加载模型
    try:
        model = YOLO(weights_path)
        print("✅ 模型加载成功")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return
    
    # 批量检测
    detection_results = batch_detect(model, image_dir, args.output, args.conf)
    
    if not detection_results:
        print("❌ 没有检测结果")
        return
    
    # 生成分析报告
    report = create_analysis_report(detection_results, args.output)
    
    # 显示摘要
    print(f"\n📊 检测结果摘要:")
    print(f"   总图像数: {report['summary']['total_images']}")
    print(f"   健康图像: {report['summary']['healthy_images']} ({report['summary']['health_rate']:.1%})")
    print(f"   患病图像: {report['summary']['diseased_images']} ({report['summary']['disease_rate']:.1%})")
    print(f"\n📁 详细报告保存在: {args.output}")

if __name__ == "__main__":
    main()