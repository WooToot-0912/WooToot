#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECA注意力机制深度分析工具
用于分析ECA注意力权重分布、通道重要性和病害特征关联性

作者: 云南烤烟病害检测项目
版本: v1.0
"""

import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import cv2
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class ECAAnalyzer:
    """ECA注意力机制分析器"""

    def __init__(self, model=None, device='cpu'):
        self.model = model
        self.device = device
        self.attention_history = []
        self.disease_classes = ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt']
        self.disease_classes_cn = ['健康叶片', '花叶病毒病', '赤星病', '野火病', '青枯病']

    def extract_eca_features(self, image: np.ndarray, eca_module: nn.Module) -> Dict[str, Any]:
        """
        提取ECA注意力特征

        Args:
            image: 输入图像 [H, W, 3]
            eca_module: ECA模块实例

        Returns:
            包含注意力分析结果的字典
        """
        # 预处理图像
        if isinstance(image, np.ndarray):
            # 转换为tensor并添加batch维度
            image_tensor = torch.from_numpy(image).permute(2, 0, 1).unsqueeze(0).float()
            image_tensor = image_tensor / 255.0  # 归一化
        else:
            image_tensor = image

        image_tensor = image_tensor.to(self.device)

        # 前向传播获取注意力权重
        with torch.no_grad():
            # 假设输入特征图 (这里需要根据实际模型结构调整)
            # 通常ECA模块接收的是卷积特征图
            if hasattr(eca_module, 'forward'):
                output = eca_module(image_tensor)
                attention_weights = eca_module.get_attention_weights()
            else:
                print("⚠️ ECA模块没有forward方法")
                return {}

        if attention_weights is None:
            print("⚠️ 无法获取注意力权重")
            return {}

        # 分析注意力权重
        analysis_result = {
            'attention_weights': attention_weights,
            'channel_analysis': self._analyze_channel_importance(attention_weights),
            'spatial_analysis': self._analyze_spatial_distribution(attention_weights, image.shape),
            'disease_correlation': self._analyze_disease_correlation(attention_weights),
            'timestamp': datetime.now().isoformat()
        }

        # 保存到历史记录
        self.attention_history.append(analysis_result)

        return analysis_result

    def _analyze_channel_importance(self, attention_weights: np.ndarray) -> Dict[str, Any]:
        """分析通道重要性"""
        weights = attention_weights.flatten()

        # 基础统计
        stats = {
            'mean': float(np.mean(weights)),
            'std': float(np.std(weights)),
            'max': float(np.max(weights)),
            'min': float(np.min(weights)),
            'median': float(np.median(weights)),
            'q75': float(np.percentile(weights, 75)),
            'q25': float(np.percentile(weights, 25))
        }

        # 通道排序
        sorted_indices = np.argsort(weights)[::-1]

        # 重要通道分析
        top_10_percent = int(len(weights) * 0.1)
        high_importance_channels = sorted_indices[:top_10_percent]
        low_importance_channels = sorted_indices[-top_10_percent:]

        # 注意力集中度分析
        attention_concentration = np.sum(weights[high_importance_channels]) / np.sum(weights)

        return {
            'statistics': stats,
            'total_channels': len(weights),
            'high_importance_channels': high_importance_channels.tolist(),
            'low_importance_channels': low_importance_channels.tolist(),
            'attention_concentration': float(attention_concentration),
            'effective_channels': int(np.sum(weights > stats['mean'])),
            'channel_utilization_rate': float(np.sum(weights > stats['mean']) / len(weights))
        }

    def _analyze_spatial_distribution(self, attention_weights: np.ndarray, image_shape: Tuple) -> Dict[str, Any]:
        """分析空间分布特性"""
        # 这里简化处理，实际应该根据特征图的空间维度分析
        weights = attention_weights.flatten()

        # 模拟空间分布分析
        spatial_variance = float(np.var(weights))
        spatial_entropy = -np.sum(weights * np.log(weights + 1e-8))

        return {
            'spatial_variance': spatial_variance,
            'spatial_entropy': float(spatial_entropy),
            'uniformity_score': 1.0 / (1.0 + spatial_variance),
            'complexity_score': float(spatial_entropy / len(weights))
        }

    def _analyze_disease_correlation(self, attention_weights: np.ndarray) -> Dict[str, Any]:
        """分析与病害特征的关联性"""
        weights = attention_weights.flatten()

        # 基于权重分布推断可能的病害特征关联
        # 这里是简化的启发式分析，实际应该结合病害特征数据

        # 高权重通道可能对应重要病害特征
        high_weight_threshold = np.percentile(weights, 80)
        high_weight_channels = np.where(weights > high_weight_threshold)[0]

        # 模拟病害特征关联分析
        disease_correlations = {}
        for i, disease in enumerate(self.disease_classes):
            # 简化的关联性计算
            correlation_score = np.mean(weights[i::len(self.disease_classes)])
            disease_correlations[disease] = float(correlation_score)

        return {
            'high_weight_channels': high_weight_channels.tolist(),
            'disease_correlations': disease_correlations,
            'dominant_feature_channels': int(len(high_weight_channels)),
            'feature_selectivity': float(len(high_weight_channels) / len(weights))
        }

    def visualize_comprehensive_analysis(self, analysis_result: Dict, save_dir: str = None) -> None:
        """生成综合分析可视化"""
        if save_dir:
            save_path = Path(save_dir)
            save_path.mkdir(parents=True, exist_ok=True)

        # 创建多子图布局
        fig = plt.figure(figsize=(20, 15))

        # 1. 注意力权重分布直方图
        ax1 = plt.subplot(2, 3, 1)
        weights = analysis_result['attention_weights'].flatten()
        plt.hist(weights, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        plt.title('ECA注意力权重分布', fontsize=14, fontweight='bold')
        plt.xlabel('注意力权重值')
        plt.ylabel('频次')
        plt.grid(True, alpha=0.3)

        # 2. Top-20通道权重
        ax2 = plt.subplot(2, 3, 2)
        channel_analysis = analysis_result['channel_analysis']
        top_channels = channel_analysis['high_importance_channels'][:20]
        top_weights = weights[top_channels]

        bars = plt.bar(range(len(top_weights)), top_weights,
                      color=plt.cm.Reds(np.linspace(0.4, 1.0, len(top_weights))))
        plt.title('Top-20 重要通道权重', fontsize=14, fontweight='bold')
        plt.xlabel('通道排名')
        plt.ylabel('注意力权重')
        plt.xticks(range(0, len(top_weights), 2))

        # 3. 病害关联性分析
        ax3 = plt.subplot(2, 3, 3)
        disease_corr = analysis_result['disease_correlation']['disease_correlations']
        diseases = list(disease_corr.keys())
        correlations = list(disease_corr.values())

        colors = ['#2E8B57', '#FF6347', '#8B4513', '#FF8C00', '#9932CC']
        bars = plt.bar(range(len(diseases)), correlations, color=colors)
        plt.title('病害特征关联性分析', fontsize=14, fontweight='bold')
        plt.xlabel('病害类型')
        plt.ylabel('关联强度')
        plt.xticks(range(len(diseases)), self.disease_classes_cn, rotation=45)

        # 4. 通道利用率分析
        ax4 = plt.subplot(2, 3, 4)
        utilization_data = [
            channel_analysis['channel_utilization_rate'],
            1 - channel_analysis['channel_utilization_rate']
        ]
        labels = ['有效通道', '低效通道']
        colors = ['#32CD32', '#D3D3D3']

        plt.pie(utilization_data, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('通道利用率分析', fontsize=14, fontweight='bold')

        # 5. 注意力集中度分析
        ax5 = plt.subplot(2, 3, 5)
        concentration = channel_analysis['attention_concentration']
        dispersion = 1 - concentration

        plt.bar(['注意力集中', '注意力分散'], [concentration, dispersion],
                color=['#FF4500', '#4169E1'], alpha=0.7)
        plt.title('注意力集中度分析', fontsize=14, fontweight='bold')
        plt.ylabel('比例')
        plt.ylim(0, 1)

        # 6. 统计摘要表格
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')

        stats = channel_analysis['statistics']
        summary_data = [
            ['总通道数', f"{channel_analysis['total_channels']}"],
            ['有效通道数', f"{channel_analysis['effective_channels']}"],
            ['平均权重', f"{stats['mean']:.4f}"],
            ['权重标准差', f"{stats['std']:.4f}"],
            ['最大权重', f"{stats['max']:.4f}"],
            ['注意力集中度', f"{concentration:.3f}"],
            ['通道利用率', f"{channel_analysis['channel_utilization_rate']:.3f}"]
        ]

        table = ax6.table(cellText=summary_data,
                         colLabels=['指标', '数值'],
                         cellLoc='center',
                         loc='center',
                         colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 2)
        ax6.set_title('ECA注意力统计摘要', fontsize=14, fontweight='bold', pad=20)

        plt.tight_layout()

        if save_dir:
            save_file = save_path / f"eca_comprehensive_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(save_file, dpi=300, bbox_inches='tight')
            print(f"✅ 综合分析图已保存至: {save_file}")
        else:
            plt.show()

        return fig

    def generate_analysis_report(self, analysis_result: Dict, save_path: str = None) -> Dict:
        """生成分析报告"""
        report = {
            'analysis_timestamp': analysis_result['timestamp'],
            'model_info': {
                'eca_kernel_size': getattr(self.model, 'kernel_size', 'unknown') if self.model else 'unknown',
                'total_channels': analysis_result['channel_analysis']['total_channels']
            },
            'attention_summary': {
                'mean_attention': analysis_result['channel_analysis']['statistics']['mean'],
                'attention_concentration': analysis_result['channel_analysis']['attention_concentration'],
                'channel_utilization_rate': analysis_result['channel_analysis']['channel_utilization_rate'],
                'effective_channels': analysis_result['channel_analysis']['effective_channels']
            },
            'disease_analysis': analysis_result['disease_correlation'],
            'spatial_analysis': analysis_result['spatial_analysis'],
            'recommendations': self._generate_recommendations(analysis_result)
        }

        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"✅ 分析报告已保存至: {save_path}")

        return report

    def _generate_recommendations(self, analysis_result: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []

        channel_analysis = analysis_result['channel_analysis']
        utilization_rate = channel_analysis['channel_utilization_rate']
        concentration = channel_analysis['attention_concentration']

        if utilization_rate < 0.3:
            recommendations.append("通道利用率较低，建议考虑减少通道数或增强特征学习")

        if concentration > 0.8:
            recommendations.append("注意力过度集中，可能存在过拟合风险，建议增加正则化")
        elif concentration < 0.3:
            recommendations.append("注意力过于分散，建议增强关键特征的学习")

        spatial_analysis = analysis_result['spatial_analysis']
        if spatial_analysis['uniformity_score'] < 0.3:
            recommendations.append("空间注意力分布不均匀，建议检查数据增强策略")

        if not recommendations:
            recommendations.append("ECA注意力机制工作正常，各项指标均在合理范围内")

        return recommendations

    def compare_attention_patterns(self, results_list: List[Dict], labels: List[str] = None) -> Dict:
        """比较不同图像的注意力模式"""
        if not results_list:
            return {}

        if labels is None:
            labels = [f"Image_{i+1}" for i in range(len(results_list))]

        comparison = {
            'num_samples': len(results_list),
            'labels': labels,
            'attention_statistics': [],
            'channel_consistency': {},
            'disease_pattern_analysis': {}
        }

        # 收集所有样本的统计信息
        all_concentrations = []
        all_utilization_rates = []
        all_effective_channels = []

        for i, result in enumerate(results_list):
            channel_analysis = result['channel_analysis']
            stats = {
                'label': labels[i],
                'concentration': channel_analysis['attention_concentration'],
                'utilization_rate': channel_analysis['channel_utilization_rate'],
                'effective_channels': channel_analysis['effective_channels'],
                'mean_attention': channel_analysis['statistics']['mean']
            }
            comparison['attention_statistics'].append(stats)

            all_concentrations.append(channel_analysis['attention_concentration'])
            all_utilization_rates.append(channel_analysis['channel_utilization_rate'])
            all_effective_channels.append(channel_analysis['effective_channels'])

        # 计算一致性指标
        comparison['channel_consistency'] = {
            'concentration_std': float(np.std(all_concentrations)),
            'utilization_rate_std': float(np.std(all_utilization_rates)),
            'effective_channels_std': float(np.std(all_effective_channels)),
            'pattern_stability': 1.0 / (1.0 + np.std(all_concentrations))
        }

        return comparison