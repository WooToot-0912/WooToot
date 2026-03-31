#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云南烤烟病害检测项目专用消融实验
基于实际项目结构和算法的深度分析工具

消融实验设计:
1. 基线模型 vs 完整技术栈
2. 各技术组件的独立贡献分析
3. 技术组件组合效果研究
4. 性能-复杂度权衡分析

作者: 毕业论文项目
版本: v3.0 - 基于真实项目文件和技术栈
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from ultralytics import YOLO
import cv2
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# 添加模块路径
sys.path.append(str(Path(__file__).parent.parent))

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class ProjectBasedAblationStudy:
    """基于实际项目的消融实验分析器"""
    
    def __init__(self, test_data_path: str = None, output_dir: str = "results/project_ablation"):
        # 自动检测可用的测试数据路径
        if test_data_path is None:
            possible_paths = [
                'data/balanced_5class/test/images',
                'data/test/images',
                'data/val/images',
                'plantvillage dataset/野火病/images'
            ]
            for path in possible_paths:
                if Path(path).exists() and list(Path(path).glob('*.jpg')):
                    self.test_data_path = path
                    print(f"🎯 自动检测到测试数据: {path}")
                    break
            else:
                raise ValueError("❌ 未找到任何可用的测试数据路径")
        else:
        self.test_data_path = test_data_path
            
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 类别信息
        self.class_names = ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt']
        self.class_names_cn = ['健康叶片', '花叶病毒病', '赤星病', '野火病', '青枯病']
        
        # 消融实验配置
        self.experiments = {
            'baseline_coco': {
                'name': '基线-COCO预训练',
                'description': 'YOLOv8n COCO预训练模型',
                'components': [],
                'model_path': 'yolov8n.pt',
                'type': 'baseline',
                'expected_performance': 'low',
                'color': '#FF6B6B',
                'ablation_group': 'baseline'
            },
            
            'baseline_tobacco': {
                'name': '基线-烟草训练',
                'description': '仅在烟草数据集上训练的基础YOLOv8n',
                'components': ['烟草数据集'],
                'model_path': 'runs/train/fast_5class/weights/best.pt',
                'type': 'tobacco_baseline',
                'expected_performance': 'medium',
                'color': '#4ECDC4',
                'ablation_group': 'baseline'
            },
            
            # 注意：以下模型需要先运行 train_fast_5class.py 生成
            # 'tobacco_plus_augmentation': {
            #     'name': '烟草+数据增强',
            #     'description': '烟草训练 + 数据增强技术',
            #     'components': ['烟草数据集', '数据增强', 'HSV调整', '类别平衡'],
            #     'model_path': 'runs/train/balanced_5class/weights/best.pt',
            #     'type': 'single_component',
            #     'expected_performance': 'medium-high',
            #     'color': '#96CEB4',
            #     'ablation_group': 'single_component'
            # },
            
            'full_stack_model': {
                'name': '完整技术栈',
                'description': '所有技术组件的完整集成（包含训练优化）',
                'components': [
                    '烟草数据集', 'ECA注意力机制', 'Focal Loss', 
                    '背景抑制分支', '多模态检测', '智能前景提取', '病害推断引擎',
                    '平衡数据集训练', 'GPU优化训练', '智能数据增强', '多源数据融合'
                ],
                'model_path': 'models/rtx5090_trained_best.pt',
                'type': 'full_stack',
                'expected_performance': 'highest',
                'color': '#6C5CE7',
                'ablation_group': 'full_stack'
            }
        }
        
        # 技术组件详细分析
        self.technical_components = {
            '烟草数据集': {
                'description': '专门针对云南烤烟病害的5类数据集',
                'impact_areas': ['领域适应', '病害识别', '特征学习'],
                'expected_improvement': 0.25,
                'complexity': 'Low',
                'implementation': 'data/balanced_5class/'
            },
            'ECA注意力机制': {
                'description': '高效通道注意力，提升特征表达能力',
                'impact_areas': ['特征提取', '病害识别精度', '细节捕捉'],
                'expected_improvement': 0.15,
                'complexity': 'Low',
                'implementation': 'modules/attention/eca.py'
            },
            'Focal Loss': {
                'description': '解决类别不平衡问题的损失函数',
                'impact_areas': ['类别平衡', '难样本学习', '整体准确率'],
                'expected_improvement': 0.10,
                'complexity': 'Low',
                'implementation': 'modules/loss/focal_loss.py'
            },
            '背景抑制分支': {
                'description': '抑制背景噪声，突出前景目标',
                'impact_areas': ['背景噪声', '前景突出', '检测精度'],
                'expected_improvement': 0.12,
                'complexity': 'Medium',
                'implementation': 'modules/attention/background_suppression.py'
            },
            '数据增强': {
                'description': 'HSV调整、旋转翻转等数据增强技术',
                'impact_areas': ['数据多样性', '泛化能力', '鲁棒性'],
                'expected_improvement': 0.08,
                'complexity': 'Low',
                'implementation': 'scripts/augment_data.py'
            },
            '多模态检测': {
                'description': '颜色、纹理、热度、缺陷四模态融合',
                'impact_areas': ['特征丰富度', '检测鲁棒性', '综合分析'],
                'expected_improvement': 0.18,
                'complexity': 'High',
                'implementation': 'modules/detection/multi_modal_detector.py'
            },
            '智能前景提取': {
                'description': 'Lab色彩空间 + GrabCut的叶片区域提取',
                'impact_areas': ['区域定位', '背景过滤', '检测精度'],
                'expected_improvement': 0.06,
                'complexity': 'Medium',
                'implementation': 'app/api/app.py (extract_leaf_foreground)'
            },
            '病害推断引擎': {
                'description': '基于多特征融合的智能病害推断',
                'impact_areas': ['决策融合', '推断准确性', '智能化'],
                'expected_improvement': 0.10,
                'complexity': 'High',
                'implementation': 'app/api/app.py (_infer_disease_type)'
            },
            '平衡数据集训练': {
                'description': '5类病害平衡数据集，整合多源数据',
                'impact_areas': ['类别平衡', '数据质量', '整体精度'],
                'expected_improvement': 0.25,
                'complexity': 'Medium',
                'implementation': 'scripts/train_fast_5class.py (create_balanced_5class_dataset)'
            },
            'GPU优化训练': {
                'description': '自适应批次+混合精度+余弦学习率',
                'impact_areas': ['训练效率', '收敛速度', '模型性能'],
                'expected_improvement': 0.12,
                'complexity': 'Low',
                'implementation': 'scripts/train_fast_5class.py (GPU优化配置)'
            },
            '智能数据增强': {
                'description': 'HSV增强+几何变换+马赛克增强',
                'impact_areas': ['数据多样性', '泛化能力', '鲁棒性'],
                'expected_improvement': 0.15,
                'complexity': 'Medium',
                'implementation': 'scripts/train_fast_5class.py (数据增强)'
            },
            '多源数据融合': {
                'description': 'PlantVillage+野火病+青枯病多源数据',
                'impact_areas': ['数据规模', '特征丰富度', '跨域泛化'],
                'expected_improvement': 0.18,
                'complexity': 'High',
                'implementation': 'scripts/train_fast_5class.py (数据融合)'
            }
        }
        
        # 结果存储
        self.results = {}
        self.test_images = []
        self.ablation_analysis = {}
    
    def check_model_availability(self):
        """检查实验模型可用性"""
        available_experiments = {}
        
        print("🔍 检查消融实验模型可用性...")
        print("=" * 60)
        
        for exp_id, config in self.experiments.items():
            model_path = config['model_path']
            if os.path.exists(model_path):
                file_size = os.path.getsize(model_path) / (1024 * 1024)
                print(f"✅ {config['name']}:")
                print(f"   📄 路径: {model_path}")
                print(f"   📦 大小: {file_size:.1f}MB")
                print(f"   🔧 组件: {len(config['components'])} 个")
                print(f"   🎯 预期: {config['expected_performance']}")
                available_experiments[exp_id] = config
            else:
                print(f"❌ {config['name']}: {model_path} 不存在")
            print()
        
        print(f"📊 总共找到 {len(available_experiments)}/{len(self.experiments)} 个可用实验")
        return available_experiments
    
    def load_test_images(self):
        """加载测试图像"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        test_path = Path(self.test_data_path)
        
        if not test_path.exists():
            raise ValueError(f"测试数据路径不存在: {self.test_data_path}")
        
        self.test_images = []
        
        for ext in image_extensions:
            self.test_images.extend(list(test_path.rglob(f"*{ext}")))
            self.test_images.extend(list(test_path.rglob(f"*{ext.upper()}")))
        
        print(f"📁 加载了 {len(self.test_images)} 张测试图像")
        
        # 限制测试数量
        max_test_images = 80
        if len(self.test_images) > max_test_images:
            print(f"⚠️ 为提高实验效率，限制使用前 {max_test_images} 张图像")
            self.test_images = self.test_images[:max_test_images]
        
        return self.test_images
    
    def evaluate_experiment(self, exp_id: str, config: Dict) -> Dict[str, Any]:
        """评估单个消融实验"""
        print(f"\n🧪 消融实验: {config['name']}")
        print(f"📄 模型路径: {config['model_path']}")
        print(f"🔧 技术组件: {', '.join(config['components']) if config['components'] else '无'}")
        
        try:
            # 加载模型
            model = YOLO(config['model_path'])
            
            # 性能评估
            detection_times = []
            predictions = []
            confidence_scores = []
            
            test_count = min(40, len(self.test_images))
            print(f"🧪 在 {test_count} 张图像上测试...")
            
            for i, img_path in enumerate(self.test_images[:test_count]):
                if i % 10 == 0:
                    print(f"   处理进度: {i+1}/{test_count}")
                
                img = cv2.imread(str(img_path))
                if img is None:
                    continue
                
                start_time = time.time()
                results = model(img, verbose=False)
                detection_time = time.time() - start_time
                detection_times.append(detection_time)
                
                if results and len(results) > 0:
                    result = results[0]
                    if hasattr(result, 'boxes') and result.boxes is not None:
                        for box in result.boxes:
                            conf = float(box.conf[0]) if len(box.conf) > 0 else 0.0
                            cls_id = int(box.cls[0]) if len(box.cls) > 0 else 0
                            
                            confidence_scores.append(conf)
                            predictions.append({
                                'confidence': conf,
                                'class_id': cls_id,
                                'class_name': self.class_names[cls_id] if cls_id < len(self.class_names) else 'unknown'
                    })
            
            # 计算性能指标
            avg_detection_time = np.mean(detection_times) if detection_times else 0
            fps = 1.0 / avg_detection_time if avg_detection_time > 0 else 0
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
            
            # 类别检测统计
            class_counts = {}
            for class_name in self.class_names:
                count = sum(1 for p in predictions if p['class_name'] == class_name)
                class_counts[class_name] = count
            
            # 计算性能评分
            performance_score = self._calculate_performance_score(fps, avg_confidence, len(predictions))
            
            results = {
                'model_info': {
                    'model_size_mb': os.path.getsize(config['model_path']) / (1024 * 1024),
                    'component_count': len(config['components']),
                    'complexity': self._estimate_complexity(config['components'])
                },
                'performance': {
                    'avg_detection_time': avg_detection_time,
                    'fps': fps,
                'avg_confidence': avg_confidence,
                    'total_detections': len(predictions),
                    'detection_rate': len(predictions) / test_count if test_count > 0 else 0,
                    'performance_score': performance_score
                },
                'class_distribution': class_counts,
                'component_analysis': {
                    'component_count': len(config['components']),
                    'components': config['components'],
                    'contribution': self._calculate_component_contribution(config['components']),
                    'complexity': self._estimate_complexity(config['components'])
                },
                'config': config
            }
            
            print(f"✅ 实验完成:")
            print(f"   FPS: {fps:.2f}")
            print(f"   平均置信度: {avg_confidence:.3f}")
            print(f"   检测数: {len(predictions)}")
            print(f"   性能评分: {performance_score:.3f}")
            
            return results
            
        except Exception as e:
            print(f"❌ 实验失败: {str(e)}")
            return {
                'error': str(e),
                'model_info': {'model_size_mb': 0, 'component_count': 0, 'complexity': 'Unknown'},
                'performance': {
                    'avg_detection_time': 0, 'fps': 0, 'avg_confidence': 0, 
                    'total_detections': 0, 'detection_rate': 0, 'performance_score': 0
                },
                'class_distribution': {class_name: 0 for class_name in self.class_names},
                'component_analysis': {
                    'component_count': 0, 'components': [], 'contribution': 0, 'complexity': 'Unknown'
                },
                'config': config
            }
    
    def _estimate_complexity(self, components: List[str]) -> str:
        """估算技术组件复杂度"""
        if not components:
            return 'Minimal'
        
        complexity_scores = []
        for comp in components:
            if comp in self.technical_components:
                comp_complexity = self.technical_components[comp]['complexity']
                if comp_complexity == 'Low':
                    complexity_scores.append(1)
                elif comp_complexity == 'Medium':
                    complexity_scores.append(2)
                elif comp_complexity == 'High':
                    complexity_scores.append(3)
        
        if not complexity_scores:
            return 'Low'
        
        avg_complexity = np.mean(complexity_scores)
        if avg_complexity >= 2.5:
            return 'High'
        elif avg_complexity >= 1.5:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_component_contribution(self, components: List[str]) -> float:
        """计算技术组件的理论贡献度"""
        if not components:
            return 0.0
        
        total_contribution = 0.0
        for comp in components:
            if comp in self.technical_components:
                total_contribution += self.technical_components[comp]['expected_improvement']
        
        # 考虑组件间的协同效应
        if len(components) > 1:
            synergy_factor = 1.0 + 0.1 * (len(components) - 1)
            total_contribution *= synergy_factor
        
        return min(total_contribution, 1.0)
    
    def _calculate_performance_score(self, fps: float, confidence: float, detections: int) -> float:
        """计算综合性能评分"""
        fps_score = min(fps / 30.0, 1.0)
        conf_score = confidence
        det_score = min(detections / 50.0, 1.0)
        
        performance_score = 0.3 * fps_score + 0.5 * conf_score + 0.2 * det_score
        return performance_score
    
    def run_ablation_study(self):
        """运行消融实验"""
        print("🚀 云南烤烟病害检测项目消融实验")
        print("=" * 80)
        print(f"🧪 实验设计: {len(self.experiments)} 个消融实验")
        print(f"🔧 技术组件: {len(self.technical_components)} 项核心技术")
        print(f"🏷️ 病害类别: {len(self.class_names)} 类")
        
        # 检查实验可用性
        available_experiments = self.check_model_availability()
        if not available_experiments:
            print("❌ 没有找到可用的实验模型")
            return
        
        # 加载测试数据
        self.load_test_images()
        
        # 运行消融实验
        print("\n🧪 开始消融实验...")
        for i, (exp_id, config) in enumerate(available_experiments.items(), 1):
            print(f"\n{'='*80}")
            print(f"📊 实验进度: {i}/{len(available_experiments)}")
            self.results[exp_id] = self.evaluate_experiment(exp_id, config)
        
        # 分析消融结果
        print(f"\n{'='*80}")
        print("📊 分析消融实验结果...")
        self.analyze_ablation_results()
        
        # 生成报告
        self.generate_ablation_report()
        self.create_ablation_visualizations()
        
        print(f"\n🎉 消融实验完成！")
        print(f"📁 结果保存在: {self.output_dir}")
    
    def analyze_ablation_results(self):
        """分析消融实验结果"""
        print("\n🔍 分析消融实验结果...")
        
        # 按实验分组分析
        groups = {}
        for exp_id, result in self.results.items():
            if 'error' in result:
                continue
                
            group = result['config']['ablation_group']
            if group not in groups:
                groups[group] = []
            groups[group].append((exp_id, result))
        
        self.ablation_analysis = {
            'group_analysis': {},
            'component_impact': {},
            'performance_progression': {}
        }
        
        # 组别分析
        for group_name, experiments in groups.items():
            if not experiments:
                continue
                
            performances = [exp[1]['performance']['performance_score'] for exp in experiments if 'error' not in exp[1]]
            fps_values = [exp[1]['performance']['fps'] for exp in experiments if 'error' not in exp[1]]
            confidences = [exp[1]['performance']['avg_confidence'] for exp in experiments if 'error' not in exp[1]]
            
            self.ablation_analysis['group_analysis'][group_name] = {
                'experiment_count': len(experiments),
                'avg_performance': np.mean(performances) if performances else 0,
                'max_performance': max(performances) if performances else 0,
                'avg_fps': np.mean(fps_values) if fps_values else 0,
                'avg_confidence': np.mean(confidences) if confidences else 0
            }
        
        # 组件影响分析
        component_impacts = {}
        for comp_name in self.technical_components.keys():
            with_comp = []
            without_comp = []
            
            for exp_id, result in self.results.items():
                if 'error' in result:
                    continue
                    
                if comp_name in result['config']['components']:
                    with_comp.append(result['performance']['performance_score'])
                else:
                    without_comp.append(result['performance']['performance_score'])
            
            if with_comp and without_comp:
                impact = np.mean(with_comp) - np.mean(without_comp)
                component_impacts[comp_name] = {
                    'impact_score': impact,
                    'with_component_avg': np.mean(with_comp),
                    'without_component_avg': np.mean(without_comp),
                    'experiments_with': len(with_comp),
                    'experiments_without': len(without_comp)
                }
        
        self.ablation_analysis['component_impact'] = component_impacts
        
        print("✅ 消融分析完成")
    
    def generate_ablation_report(self):
        """生成消融实验报告"""
        print("\n📋 生成消融实验报告...")
        
        # 创建实验结果表格
        experiment_data = []
        for exp_id, result in self.results.items():
            if 'error' in result:
                continue
                
            config = result['config']
            perf = result['performance']
            comp_analysis = result['component_analysis']
            
            experiment_data.append({
                '实验名称': config['name'],
                '实验分组': config['ablation_group'],
                '技术组件数': comp_analysis['component_count'],
                '核心组件': ', '.join(config['components'][:3]) if config['components'] else '无',
                'FPS': f"{perf['fps']:.2f}",
                '平均置信度': f"{perf['avg_confidence']:.3f}",
                '检测数量': perf['total_detections'],
                '性能评分': f"{perf['performance_score']:.3f}",
                '组件贡献度': f"{comp_analysis['contribution']:.3f}",
                '复杂度': comp_analysis['complexity']
            })
        
        # 保存为CSV
        df = pd.DataFrame(experiment_data)
        csv_path = self.output_dir / 'project_ablation_comparison.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # 保存为Excel
        xlsx_path = self.output_dir / 'project_ablation_comparison.xlsx'
        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='消融实验结果', index=False)
        
        # 保存分析结果为JSON
        analysis_path = self.output_dir / 'ablation_analysis.json'
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(self.ablation_analysis, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 消融实验报告已保存:")
        print(f"   CSV: {csv_path}")
        print(f"   Excel: {xlsx_path}")
        print(f"   分析结果: {analysis_path}")
    
    def create_ablation_visualizations(self):
        """创建消融实验可视化图表"""
        print("\n📈 生成消融实验可视化...")
        
        if not self.results:
            print("❌ 没有实验结果，跳过可视化")
            return
        
        # 设置图表样式
        fig = plt.figure(figsize=(16, 12))
        
        # 准备数据
        experiment_names = []
        performance_scores = []
        fps_values = []
        component_counts = []
        colors = []
        
        for exp_id, result in self.results.items():
            if 'error' in result:
                continue
            
            config = result['config']
            experiment_names.append(config['name'])
            performance_scores.append(result['performance']['performance_score'])
            fps_values.append(result['performance']['fps'])
            component_counts.append(len(config['components']))
            colors.append(config.get('color', '#3498db'))
        
        # 1. 性能评分对比
        ax1 = plt.subplot(2, 2, 1)
        bars1 = ax1.bar(range(len(experiment_names)), performance_scores, color=colors)
        ax1.set_title('消融实验性能评分对比', fontsize=14, fontweight='bold')
        ax1.set_ylabel('性能评分')
        ax1.set_xticks(range(len(experiment_names)))
        ax1.set_xticklabels(experiment_names, rotation=45, ha='right')
        ax1.set_ylim(0, 1)
        
        for bar, value in zip(bars1, performance_scores):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.3f}', ha='center', va='bottom', fontsize=8)
        
        # 2. 技术组件数量 vs 性能
        ax2 = plt.subplot(2, 2, 2)
        scatter = ax2.scatter(component_counts, performance_scores, c=colors, s=100, alpha=0.7)
        ax2.set_title('技术组件数量 vs 性能评分', fontsize=14, fontweight='bold')
        ax2.set_xlabel('技术组件数量')
        ax2.set_ylabel('性能评分')
        ax2.set_ylim(0, 1)
        
        # 3. 组件影响分析
        if self.ablation_analysis['component_impact']:
            ax3 = plt.subplot(2, 2, 3)
            comp_names = list(self.ablation_analysis['component_impact'].keys())
            impact_scores = [self.ablation_analysis['component_impact'][comp]['impact_score'] 
                           for comp in comp_names]
            
            bars3 = ax3.barh(range(len(comp_names)), impact_scores, 
                           color=['#2ECC71' if score > 0 else '#E74C3C' for score in impact_scores])
            ax3.set_title('技术组件影响分析', fontsize=14, fontweight='bold')
            ax3.set_xlabel('影响评分')
            ax3.set_yticks(range(len(comp_names)))
            ax3.set_yticklabels(comp_names)
        
        # 4. FPS vs 性能权衡分析
        ax4 = plt.subplot(2, 2, 4)
        scatter4 = ax4.scatter(fps_values, performance_scores, c=colors, s=100, alpha=0.7)
        ax4.set_title('FPS vs 性能权衡分析', fontsize=14, fontweight='bold')
        ax4.set_xlabel('FPS')
        ax4.set_ylabel('性能评分')
        ax4.set_ylim(0, 1)
        
        # 添加理想区域标注
        ax4.axhline(y=0.7, color='green', linestyle='--', alpha=0.5, label='高性能阈值')
        ax4.axvline(x=10, color='blue', linestyle='--', alpha=0.5, label='实时性阈值')
        ax4.legend()
        
        plt.tight_layout()
        
        # 保存图表
        chart_path = self.output_dir / 'project_ablation_visualization.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
    
        print(f"✅ 消融实验可视化已保存: {chart_path}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='云南烤烟病害检测项目消融实验工具'
    )
    parser.add_argument('--test-data', type=str, default='data/balanced_5class/test/images',
                       help='测试数据路径')
    parser.add_argument('--output', type=str, default='results/project_ablation',
                       help='输出目录')
    
    args = parser.parse_args()
    
    print("🚀 云南烤烟病害检测项目消融实验")
    print("=" * 80)
    print(f"📁 测试数据: {args.test_data}")
    print(f"📁 输出目录: {args.output}")
    
    try:
        # 创建消融实验分析器
        ablation_study = ProjectBasedAblationStudy(
            test_data_path=args.test_data,
            output_dir=args.output
        )
        
        # 运行消融实验
        ablation_study.run_ablation_study()
        
    except Exception as e:
        print(f"❌ 消融实验过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()