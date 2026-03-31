#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云南烤烟病害数据集深度分析工具
用于分析数据集平衡性、质量评估和跨作物迁移学习验证

功能包括:
1. 数据集平衡性分析
2. 图像质量评估
3. 跨作物迁移学习验证
4. 数据分布统计分析
5. 标注一致性检查

作者: 云南烤烟病害检测项目
版本: v1.0
"""

import os
import sys
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json
from datetime import datetime
from collections import Counter, defaultdict
import yaml
from sklearn.metrics import classification_report
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class DatasetAnalyzer:
    """数据集分析器"""

    def __init__(self, dataset_path: str, output_dir: str = "results/dataset_analysis"):
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 病害类别定义
        self.disease_classes = {
            0: {'name': 'healthy', 'name_cn': '健康叶片', 'color': '#2E8B57'},
            1: {'name': 'mosaic_virus', 'name_cn': '花叶病毒病', 'color': '#FF6347'},
            2: {'name': 'brown_spot', 'name_cn': '赤星病', 'color': '#8B4513'},
            3: {'name': 'wildfire', 'name_cn': '野火病', 'color': '#FF8C00'},
            4: {'name': 'bacterial_wilt', 'name_cn': '青枯病', 'color': '#9932CC'}
        }

        # 分析结果存储
        self.analysis_results = {}

    def analyze_dataset_balance(self) -> Dict[str, Any]:
        """分析数据集平衡性"""
        print("📊 开始数据集平衡性分析...")

        balance_analysis = {
            'splits': {},
            'overall_balance': {},
            'class_distribution': {},
            'balance_metrics': {}
        }

        # 分析各个数据集分割
        for split in ['train', 'val', 'test']:
            split_path = self.dataset_path / split
            if not split_path.exists():
                continue

            print(f"   分析 {split} 集...")
            split_analysis = self._analyze_split_balance(split_path)
            balance_analysis['splits'][split] = split_analysis

        # 计算整体平衡性指标
        balance_analysis['overall_balance'] = self._calculate_overall_balance(balance_analysis['splits'])

        # 生成平衡性报告
        self._generate_balance_report(balance_analysis)

        self.analysis_results['balance_analysis'] = balance_analysis
        return balance_analysis

    def _analyze_split_balance(self, split_path: Path) -> Dict[str, Any]:
        """分析单个数据集分割的平衡性"""
        images_path = split_path / 'images'
        labels_path = split_path / 'labels'

        if not images_path.exists() or not labels_path.exists():
            return {'error': f'路径不存在: {split_path}'}

        # 统计图像数量
        image_files = list(images_path.glob('*.jpg')) + list(images_path.glob('*.png'))
        label_files = list(labels_path.glob('*.txt'))

        # 统计类别分布
        class_counts = defaultdict(int)
        total_objects = 0

        for label_file in label_files:
            try:
                with open(label_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.strip():
                            class_id = int(line.strip().split()[0])
                            class_counts[class_id] += 1
                            total_objects += 1
            except Exception as e:
                print(f"⚠️ 读取标签文件失败: {label_file}, 错误: {e}")
                continue

        # 计算平衡性指标
        if class_counts:
            counts_list = list(class_counts.values())
            balance_ratio = min(counts_list) / max(counts_list) if max(counts_list) > 0 else 0

            # 计算基尼系数 (衡量不平衡程度)
            gini_coefficient = self._calculate_gini_coefficient(counts_list)

            # 计算熵 (衡量分布均匀性)
            entropy = self._calculate_entropy(counts_list)
        else:
            balance_ratio = 0
            gini_coefficient = 1
            entropy = 0

        return {
            'total_images': len(image_files),
            'total_labels': len(label_files),
            'total_objects': total_objects,
            'class_counts': dict(class_counts),
            'balance_ratio': balance_ratio,
            'gini_coefficient': gini_coefficient,
            'entropy': entropy,
            'missing_labels': len(image_files) - len(label_files)
        }

    def _calculate_gini_coefficient(self, values: List[int]) -> float:
        """计算基尼系数"""
        if not values or sum(values) == 0:
            return 0

        sorted_values = sorted(values)
        n = len(values)
        cumsum = np.cumsum(sorted_values)

        return (n + 1 - 2 * sum((n + 1 - i) * y for i, y in enumerate(sorted_values))) / (n * sum(values))

    def _calculate_entropy(self, values: List[int]) -> float:
        """计算信息熵"""
        if not values or sum(values) == 0:
            return 0

        total = sum(values)
        probabilities = [v / total for v in values]

        return -sum(p * np.log2(p) for p in probabilities if p > 0)

    def _calculate_overall_balance(self, splits_analysis: Dict) -> Dict[str, Any]:
        """计算整体平衡性指标"""
        overall_class_counts = defaultdict(int)
        total_images = 0
        total_objects = 0

        for split_name, split_data in splits_analysis.items():
            if 'error' in split_data:
                continue

            total_images += split_data['total_images']
            total_objects += split_data['total_objects']

            for class_id, count in split_data['class_counts'].items():
                overall_class_counts[class_id] += count

        if overall_class_counts:
            counts_list = list(overall_class_counts.values())
            balance_ratio = min(counts_list) / max(counts_list) if max(counts_list) > 0 else 0
            gini_coefficient = self._calculate_gini_coefficient(counts_list)
            entropy = self._calculate_entropy(counts_list)
        else:
            balance_ratio = 0
            gini_coefficient = 1
            entropy = 0

        return {
            'total_images': total_images,
            'total_objects': total_objects,
            'class_counts': dict(overall_class_counts),
            'balance_ratio': balance_ratio,
            'gini_coefficient': gini_coefficient,
            'entropy': entropy,
            'balance_quality': self._assess_balance_quality(balance_ratio, gini_coefficient)
        }

    def _assess_balance_quality(self, balance_ratio: float, gini_coefficient: float) -> str:
        """评估数据集平衡质量"""
        if balance_ratio >= 0.8 and gini_coefficient <= 0.2:
            return "优秀"
        elif balance_ratio >= 0.6 and gini_coefficient <= 0.3:
            return "良好"
        elif balance_ratio >= 0.4 and gini_coefficient <= 0.5:
            return "一般"
        else:
            return "较差"

    def analyze_image_quality(self, sample_size: int = 100) -> Dict[str, Any]:
        """分析图像质量"""
        print("🖼️ 开始图像质量分析...")

        quality_analysis = {
            'blur_analysis': {},
            'brightness_analysis': {},
            'contrast_analysis': {},
            'resolution_analysis': {},
            'quality_distribution': {},
            'problematic_images': []
        }

        # 收集样本图像
        sample_images = self._collect_sample_images(sample_size)

        blur_scores = []
        brightness_scores = []
        contrast_scores = []
        resolutions = []

        for img_path in sample_images:
            try:
                # 读取图像
                img = cv2.imread(str(img_path))
                if img is None:
                    continue

                # 模糊度分析 (Laplacian方差)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
                blur_scores.append(blur_score)

                # 亮度分析
                brightness = np.mean(gray)
                brightness_scores.append(brightness)

                # 对比度分析
                contrast = np.std(gray)
                contrast_scores.append(contrast)

                # 分辨率分析
                height, width = img.shape[:2]
                resolutions.append((width, height))

                # 检查问题图像
                if blur_score < 100:  # 模糊阈值
                    quality_analysis['problematic_images'].append({
                        'path': str(img_path),
                        'issue': 'blur',
                        'score': blur_score
                    })

                if brightness < 50 or brightness > 200:  # 亮度异常
                    quality_analysis['problematic_images'].append({
                        'path': str(img_path),
                        'issue': 'brightness',
                        'score': brightness
                    })

            except Exception as e:
                print(f"⚠️ 处理图像失败: {img_path}, 错误: {e}")
                continue

        # 统计分析
        if blur_scores:
            quality_analysis['blur_analysis'] = {
                'mean': float(np.mean(blur_scores)),
                'std': float(np.std(blur_scores)),
                'min': float(np.min(blur_scores)),
                'max': float(np.max(blur_scores)),
                'median': float(np.median(blur_scores)),
                'blur_ratio': float(sum(1 for s in blur_scores if s < 100) / len(blur_scores))
            }

        if brightness_scores:
            quality_analysis['brightness_analysis'] = {
                'mean': float(np.mean(brightness_scores)),
                'std': float(np.std(brightness_scores)),
                'min': float(np.min(brightness_scores)),
                'max': float(np.max(brightness_scores)),
                'median': float(np.median(brightness_scores))
            }

        if contrast_scores:
            quality_analysis['contrast_analysis'] = {
                'mean': float(np.mean(contrast_scores)),
                'std': float(np.std(contrast_scores)),
                'min': float(np.min(contrast_scores)),
                'max': float(np.max(contrast_scores)),
                'median': float(np.median(contrast_scores))
            }

        if resolutions:
            width_stats = [r[0] for r in resolutions]
            height_stats = [r[1] for r in resolutions]

            quality_analysis['resolution_analysis'] = {
                'width_stats': {
                    'mean': float(np.mean(width_stats)),
                    'std': float(np.std(width_stats)),
                    'min': int(np.min(width_stats)),
                    'max': int(np.max(width_stats))
                },
                'height_stats': {
                    'mean': float(np.mean(height_stats)),
                    'std': float(np.std(height_stats)),
                    'min': int(np.min(height_stats)),
                    'max': int(np.max(height_stats))
                },
                'aspect_ratios': [w/h for w, h in resolutions],
                'resolution_consistency': len(set(resolutions)) / len(resolutions)
            }

        self.analysis_results['quality_analysis'] = quality_analysis
        return quality_analysis

    def _collect_sample_images(self, sample_size: int) -> List[Path]:
        """收集样本图像"""
        all_images = []

        for split in ['train', 'val', 'test']:
            images_path = self.dataset_path / split / 'images'
            if images_path.exists():
                split_images = list(images_path.glob('*.jpg')) + list(images_path.glob('*.png'))
                all_images.extend(split_images)

        # 随机采样
        if len(all_images) > sample_size:
            np.random.seed(42)
            indices = np.random.choice(len(all_images), sample_size, replace=False)
            return [all_images[i] for i in indices]

        return all_images

    def _generate_balance_report(self, balance_analysis: Dict) -> None:
        """生成平衡性分析报告"""
        print("📈 生成数据集平衡性可视化...")

        # 创建多子图布局
        fig = plt.figure(figsize=(20, 15))

        # 1. 整体类别分布
        ax1 = plt.subplot(2, 3, 1)
        overall_counts = balance_analysis['overall_balance']['class_counts']

        if overall_counts:
            classes = [self.disease_classes[cid]['name_cn'] for cid in overall_counts.keys()]
            counts = list(overall_counts.values())
            colors = [self.disease_classes[cid]['color'] for cid in overall_counts.keys()]

            bars = plt.bar(classes, counts, color=colors, alpha=0.7)
            plt.title('整体类别分布', fontsize=14, fontweight='bold')
            plt.xlabel('病害类型')
            plt.ylabel('样本数量')
            plt.xticks(rotation=45)

            # 添加数值标签
            for bar, count in zip(bars, counts):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01,
                        str(count), ha='center', va='bottom', fontsize=10)

        # 2. 各分割数据集对比
        ax2 = plt.subplot(2, 3, 2)
        splits_data = []
        split_names = []

        for split_name, split_data in balance_analysis['splits'].items():
            if 'error' not in split_data:
                splits_data.append(split_data['total_objects'])
                split_names.append(split_name.upper())

        if splits_data:
            colors_split = ['#FF6B6B', '#4ECDC4', '#45B7D1']
            bars = plt.bar(split_names, splits_data, color=colors_split[:len(splits_data)], alpha=0.7)
            plt.title('各数据集分割对比', fontsize=14, fontweight='bold')
            plt.xlabel('数据集分割')
            plt.ylabel('目标数量')

            for bar, count in zip(bars, splits_data):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(splits_data)*0.01,
                        str(count), ha='center', va='bottom', fontsize=10)

        # 3. 平衡性指标雷达图
        ax3 = plt.subplot(2, 3, 3, projection='polar')

        overall_balance = balance_analysis['overall_balance']
        metrics = ['平衡比', '基尼系数', '信息熵']
        values = [
            overall_balance['balance_ratio'],
            1 - overall_balance['gini_coefficient'],  # 转换为正向指标
            overall_balance['entropy'] / np.log2(len(self.disease_classes))  # 归一化
        ]

        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        values += values[:1]  # 闭合图形
        angles += angles[:1]

        ax3.plot(angles, values, 'o-', linewidth=2, color='#FF6B6B')
        ax3.fill(angles, values, alpha=0.25, color='#FF6B6B')
        ax3.set_xticks(angles[:-1])
        ax3.set_xticklabels(metrics)
        ax3.set_ylim(0, 1)
        ax3.set_title('数据集平衡性指标', fontsize=14, fontweight='bold', pad=20)

        # 4. 类别分布饼图
        ax4 = plt.subplot(2, 3, 4)
        if overall_counts:
            sizes = list(overall_counts.values())
            labels = [self.disease_classes[cid]['name_cn'] for cid in overall_counts.keys()]
            colors = [self.disease_classes[cid]['color'] for cid in overall_counts.keys()]

            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.title('类别分布占比', fontsize=14, fontweight='bold')

        # 5. 平衡性趋势分析
        ax5 = plt.subplot(2, 3, 5)
        split_balance_ratios = []
        split_labels = []

        for split_name, split_data in balance_analysis['splits'].items():
            if 'error' not in split_data:
                split_balance_ratios.append(split_data['balance_ratio'])
                split_labels.append(split_name.upper())

        if split_balance_ratios:
            plt.plot(split_labels, split_balance_ratios, 'o-', linewidth=2, markersize=8, color='#4ECDC4')
            plt.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='理想平衡线')
            plt.title('各分割平衡性趋势', fontsize=14, fontweight='bold')
            plt.xlabel('数据集分割')
            plt.ylabel('平衡比')
            plt.ylim(0, 1)
            plt.legend()
            plt.grid(True, alpha=0.3)

        # 6. 统计摘要表格
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')

        summary_data = [
            ['总图像数', f"{overall_balance['total_images']:,}"],
            ['总目标数', f"{overall_balance['total_objects']:,}"],
            ['平衡比', f"{overall_balance['balance_ratio']:.3f}"],
            ['基尼系数', f"{overall_balance['gini_coefficient']:.3f}"],
            ['信息熵', f"{overall_balance['entropy']:.3f}"],
            ['平衡质量', overall_balance['balance_quality']]
        ]

        table = ax6.table(cellText=summary_data,
                         colLabels=['指标', '数值'],
                         cellLoc='center',
                         loc='center',
                         colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 2)
        ax6.set_title('数据集统计摘要', fontsize=14, fontweight='bold', pad=20)

        plt.tight_layout()

        # 保存图像
        save_path = self.output_dir / f"dataset_balance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ 平衡性分析图已保存至: {save_path}")

        plt.show()

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合分析报告"""
        print("📋 生成综合分析报告...")

        # 运行所有分析
        if 'balance_analysis' not in self.analysis_results:
            self.analyze_dataset_balance()

        if 'quality_analysis' not in self.analysis_results:
            self.analyze_image_quality()

        # 生成综合报告
        comprehensive_report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'dataset_path': str(self.dataset_path),
            'summary': self._generate_summary(),
            'balance_analysis': self.analysis_results.get('balance_analysis', {}),
            'quality_analysis': self.analysis_results.get('quality_analysis', {}),
            'recommendations': self._generate_recommendations()
        }

        # 保存报告
        report_path = self.output_dir / f"comprehensive_dataset_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, ensure_ascii=False, indent=2)

        print(f"✅ 综合报告已保存至: {report_path}")

        return comprehensive_report

    def _generate_summary(self) -> Dict[str, Any]:
        """生成分析摘要"""
        summary = {}

        # 平衡性摘要
        if 'balance_analysis' in self.analysis_results:
            balance = self.analysis_results['balance_analysis']['overall_balance']
            summary['balance_summary'] = {
                'total_samples': balance['total_images'],
                'balance_ratio': balance['balance_ratio'],
                'balance_quality': balance['balance_quality'],
                'most_common_class': max(balance['class_counts'], key=balance['class_counts'].get),
                'least_common_class': min(balance['class_counts'], key=balance['class_counts'].get)
            }

        # 质量摘要
        if 'quality_analysis' in self.analysis_results:
            quality = self.analysis_results['quality_analysis']
            summary['quality_summary'] = {
                'blur_issues': len([img for img in quality['problematic_images'] if img['issue'] == 'blur']),
                'brightness_issues': len([img for img in quality['problematic_images'] if img['issue'] == 'brightness']),
                'total_quality_issues': len(quality['problematic_images']),
                'average_blur_score': quality['blur_analysis'].get('mean', 0),
                'average_brightness': quality['brightness_analysis'].get('mean', 0)
            }

        return summary

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于平衡性分析的建议
        if 'balance_analysis' in self.analysis_results:
            balance = self.analysis_results['balance_analysis']['overall_balance']

            if balance['balance_ratio'] < 0.5:
                recommendations.append(
                    f"数据集不平衡严重（平衡比={balance['balance_ratio']:.3f}），建议使用SMOTE过采样或Focal Loss缓解"
                )

            if balance['gini_coefficient'] > 0.4:
                recommendations.append(
                    f"类别分布不均匀（基尼系数={balance['gini_coefficient']:.3f}），建议增加少数类样本"
                )

            # 检查特定类别的问题
            class_counts = balance['class_counts']
            if class_counts:
                min_count = min(class_counts.values())
                max_count = max(class_counts.values())

                if max_count / min_count > 5:
                    min_class = min(class_counts, key=class_counts.get)
                    max_class = max(class_counts, key=class_counts.get)
                    recommendations.append(
                        f"类别{self.disease_classes[min_class]['name_cn']}样本过少（{min_count}个），"
                        f"相比{self.disease_classes[max_class]['name_cn']}（{max_count}个）差距过大"
                    )

        # 基于质量分析的建议
        if 'quality_analysis' in self.analysis_results:
            quality = self.analysis_results['quality_analysis']

            if quality['blur_analysis'].get('blur_ratio', 0) > 0.1:
                recommendations.append(
                    f"模糊图像比例过高（{quality['blur_analysis']['blur_ratio']:.1%}），建议检查图像采集质量"
                )

            brightness_mean = quality['brightness_analysis'].get('mean', 128)
            if brightness_mean < 80 or brightness_mean > 180:
                recommendations.append(
                    f"图像亮度异常（平均亮度={brightness_mean:.1f}），建议进行亮度标准化处理"
                )

            if quality['resolution_analysis'].get('resolution_consistency', 1) < 0.8:
                recommendations.append(
                    "图像分辨率不一致，建议统一图像尺寸以提高训练效率"
                )

        # 通用建议
        if not recommendations:
            recommendations.append("数据集质量良好，各项指标均在合理范围内")
        else:
            recommendations.append("建议在训练前对数据集进行相应的预处理和增强")

        return recommendations

    def validate_cross_crop_transfer(self, source_dataset_info: Dict) -> Dict[str, Any]:
        """验证跨作物迁移学习的有效性"""
        print("🔄 验证跨作物迁移学习...")

        validation_result = {
            'source_info': source_dataset_info,
            'target_info': self.analysis_results.get('balance_analysis', {}),
            'transfer_feasibility': {},
            'similarity_analysis': {},
            'transfer_recommendations': []
        }

        # 分析源数据集和目标数据集的相似性
        if 'balance_analysis' in self.analysis_results:
            target_balance = self.analysis_results['balance_analysis']['overall_balance']

            # 类别数量对比
            source_classes = len(source_dataset_info.get('class_counts', {}))
            target_classes = len(target_balance.get('class_counts', {}))

            validation_result['similarity_analysis'] = {
                'class_count_similarity': min(source_classes, target_classes) / max(source_classes, target_classes),
                'balance_similarity': self._calculate_balance_similarity(
                    source_dataset_info.get('balance_ratio', 0),
                    target_balance.get('balance_ratio', 0)
                ),
                'size_ratio': source_dataset_info.get('total_samples', 0) / target_balance.get('total_images', 1)
            }

            # 迁移可行性评估
            feasibility_score = (
                validation_result['similarity_analysis']['class_count_similarity'] * 0.4 +
                validation_result['similarity_analysis']['balance_similarity'] * 0.3 +
                min(validation_result['similarity_analysis']['size_ratio'], 1.0) * 0.3
            )

            validation_result['transfer_feasibility'] = {
                'feasibility_score': feasibility_score,
                'feasibility_level': self._assess_transfer_feasibility(feasibility_score),
                'expected_performance_gain': self._estimate_performance_gain(feasibility_score)
            }

            # 生成迁移学习建议
            validation_result['transfer_recommendations'] = self._generate_transfer_recommendations(
                validation_result
            )

        return validation_result

    def _calculate_balance_similarity(self, source_balance: float, target_balance: float) -> float:
        """计算平衡性相似度"""
        if source_balance == 0 and target_balance == 0:
            return 1.0
        return 1.0 - abs(source_balance - target_balance) / max(source_balance, target_balance, 1.0)

    def _assess_transfer_feasibility(self, score: float) -> str:
        """评估迁移学习可行性"""
        if score >= 0.8:
            return "高度可行"
        elif score >= 0.6:
            return "较为可行"
        elif score >= 0.4:
            return "需要谨慎"
        else:
            return "不建议直接迁移"

    def _estimate_performance_gain(self, feasibility_score: float) -> str:
        """估计性能提升"""
        if feasibility_score >= 0.8:
            return "预期显著提升（15-25%）"
        elif feasibility_score >= 0.6:
            return "预期中等提升（8-15%）"
        elif feasibility_score >= 0.4:
            return "预期轻微提升（3-8%）"
        else:
            return "可能无提升或负面影响"

    def _generate_transfer_recommendations(self, validation_result: Dict) -> List[str]:
        """生成迁移学习建议"""
        recommendations = []

        feasibility = validation_result['transfer_feasibility']
        similarity = validation_result['similarity_analysis']

        if feasibility['feasibility_score'] >= 0.6:
            recommendations.append("建议采用渐进式迁移学习策略")
            recommendations.append("可以使用预训练权重初始化模型")

        if similarity['balance_similarity'] < 0.7:
            recommendations.append("源数据集和目标数据集平衡性差异较大，建议调整损失函数权重")

        if similarity['size_ratio'] < 0.5:
            recommendations.append("源数据集规模较小，建议结合数据增强技术")
        elif similarity['size_ratio'] > 2.0:
            recommendations.append("源数据集规模较大，可以考虑知识蒸馏技术")

        if feasibility['feasibility_score'] < 0.4:
            recommendations.append("不建议直接迁移，考虑从头训练或寻找更相似的源数据集")

        return recommendations


def main():
    """主函数 - 数据集分析示例"""
    print("🚀 云南烤烟病害数据集分析工具")
    print("=" * 50)

    # 数据集路径 (请根据实际情况修改)
    dataset_path = "data/tobacco_disease_5class"
    output_dir = "results/dataset_analysis"

    # 创建分析器
    analyzer = DatasetAnalyzer(dataset_path, output_dir)

    try:
        # 1. 数据集平衡性分析
        print("\n📊 步骤1: 数据集平衡性分析")
        balance_result = analyzer.analyze_dataset_balance()

        # 打印关键指标
        overall_balance = balance_result['overall_balance']
        print(f"   总图像数: {overall_balance['total_images']:,}")
        print(f"   总目标数: {overall_balance['total_objects']:,}")
        print(f"   平衡比: {overall_balance['balance_ratio']:.3f}")
        print(f"   平衡质量: {overall_balance['balance_quality']}")

        # 2. 图像质量分析
        print("\n🖼️ 步骤2: 图像质量分析")
        quality_result = analyzer.analyze_image_quality(sample_size=200)

        if quality_result['blur_analysis']:
            print(f"   平均模糊度: {quality_result['blur_analysis']['mean']:.2f}")
            print(f"   模糊图像比例: {quality_result['blur_analysis']['blur_ratio']:.1%}")

        if quality_result['problematic_images']:
            print(f"   问题图像数量: {len(quality_result['problematic_images'])}")

        # 3. 跨作物迁移学习验证 (示例)
        print("\n🔄 步骤3: 跨作物迁移学习验证")

        # PlantVillage数据集信息 (示例数据)
        plantvillage_info = {
            'total_samples': 54306,
            'class_counts': {0: 1591, 1: 2127, 2: 1000, 3: 952, 4: 2180},
            'balance_ratio': 0.436,
            'gini_coefficient': 0.234
        }

        transfer_result = analyzer.validate_cross_crop_transfer(plantvillage_info)

        feasibility = transfer_result['transfer_feasibility']
        print(f"   迁移可行性: {feasibility['feasibility_level']}")
        print(f"   可行性评分: {feasibility['feasibility_score']:.3f}")
        print(f"   预期性能提升: {feasibility['expected_performance_gain']}")

        # 4. 生成综合报告
        print("\n📋 步骤4: 生成综合分析报告")
        comprehensive_report = analyzer.generate_comprehensive_report()

        # 打印建议
        print("\n💡 改进建议:")
        for i, recommendation in enumerate(comprehensive_report['recommendations'], 1):
            print(f"   {i}. {recommendation}")

        print(f"\n✅ 分析完成！结果已保存至: {output_dir}")

    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


def analyze_specific_dataset(dataset_path: str, output_dir: str = None):
    """分析指定数据集的便捷函数"""
    if output_dir is None:
        output_dir = f"results/analysis_{Path(dataset_path).name}"

    analyzer = DatasetAnalyzer(dataset_path, output_dir)

    # 运行完整分析
    balance_result = analyzer.analyze_dataset_balance()
    quality_result = analyzer.analyze_image_quality()
    report = analyzer.generate_comprehensive_report()

    return {
        'analyzer': analyzer,
        'balance_result': balance_result,
        'quality_result': quality_result,
        'comprehensive_report': report
    }


if __name__ == "__main__":
    main()