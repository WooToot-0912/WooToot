#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背景抑制分支深度分析工具
用于量化验证背景抑制效果，包括红土抑制率、杂草抑制率和前景保留率

功能包括:
1. 背景抑制效果量化分析
2. 前景/背景分割质量评估
3. 抑制率统计和可视化
4. 自适应阈值选择
5. 抑制效果对比分析

作者: 云南烤烟病害检测项目
版本: v1.0
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import cv2
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime
from sklearn.metrics import precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class BackgroundSuppressionAnalyzer:
    """背景抑制分析器"""

    def __init__(self, model=None, device='cpu'):
        self.model = model
        self.device = device
        self.suppression_history = []

        # 背景类别定义
        self.background_types = {
            'red_soil': {'name': '红土', 'color_range': ([0, 30, 30], [15, 255, 255]), 'target_suppression': 0.912},
            'weeds': {'name': '杂草', 'color_range': ([35, 40, 40], [85, 255, 255]), 'target_suppression': 0.846},
            'shadows': {'name': '阴影', 'color_range': ([0, 0, 0], [180, 255, 80]), 'target_suppression': 0.750}
        }

        # 前景保留目标
        self.foreground_preservation_target = 0.958

    def analyze_suppression_performance(self, image: np.ndarray, suppression_mask: np.ndarray,
                                      ground_truth_mask: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        分析背景抑制性能

        Args:
            image: 原始图像 [H, W, 3]
            suppression_mask: 背景抑制掩码 [H, W] (0-1之间的浮点数)
            ground_truth_mask: 真实前景掩码 [H, W] (可选)

        Returns:
            包含抑制性能分析结果的字典
        """
        print("🎯 开始背景抑制性能分析...")

        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'image_info': {
                'height': image.shape[0],
                'width': image.shape[1],
                'channels': image.shape[2] if len(image.shape) > 2 else 1
            },
            'background_suppression': {},
            'foreground_preservation': {},
            'overall_performance': {},
            'adaptive_thresholds': {}
        }

        # 1. 背景类别抑制分析
        analysis_result['background_suppression'] = self._analyze_background_suppression(
            image, suppression_mask
        )

        # 2. 前景保留分析
        analysis_result['foreground_preservation'] = self._analyze_foreground_preservation(
            image, suppression_mask, ground_truth_mask
        )

        # 3. 整体性能评估
        analysis_result['overall_performance'] = self._evaluate_overall_performance(
            analysis_result['background_suppression'],
            analysis_result['foreground_preservation']
        )

        # 4. 自适应阈值分析
        analysis_result['adaptive_thresholds'] = self._analyze_adaptive_thresholds(
            suppression_mask
        )

        # 保存到历史记录
        self.suppression_history.append(analysis_result)

        return analysis_result

    def _analyze_background_suppression(self, image: np.ndarray, suppression_mask: np.ndarray) -> Dict[str, Any]:
        """分析背景抑制效果"""
        # 转换到HSV色彩空间进行颜色分析
        hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        suppression_results = {}

        for bg_type, bg_info in self.background_types.items():
            # 创建颜色掩码
            lower_bound = np.array(bg_info['color_range'][0])
            upper_bound = np.array(bg_info['color_range'][1])
            color_mask = cv2.inRange(hsv_image, lower_bound, upper_bound)

            # 计算该背景类型的像素数量
            bg_pixels = np.sum(color_mask > 0)

            if bg_pixels > 0:
                # 计算抑制率
                suppressed_pixels = np.sum((color_mask > 0) & (suppression_mask < 0.5))
                suppression_rate = suppressed_pixels / bg_pixels

                # 计算抑制强度
                bg_suppression_values = suppression_mask[color_mask > 0]
                avg_suppression_strength = 1.0 - np.mean(bg_suppression_values)

                suppression_results[bg_type] = {
                    'total_pixels': int(bg_pixels),
                    'suppressed_pixels': int(suppressed_pixels),
                    'suppression_rate': float(suppression_rate),
                    'target_rate': bg_info['target_suppression'],
                    'rate_achievement': float(suppression_rate / bg_info['target_suppression']),
                    'avg_suppression_strength': float(avg_suppression_strength),
                    'performance_grade': self._grade_suppression_performance(
                        suppression_rate, bg_info['target_suppression']
                    )
                }
            else:
                suppression_results[bg_type] = {
                    'total_pixels': 0,
                    'suppressed_pixels': 0,
                    'suppression_rate': 0.0,
                    'target_rate': bg_info['target_suppression'],
                    'rate_achievement': 0.0,
                    'avg_suppression_strength': 0.0,
                    'performance_grade': 'N/A'
                }

        return suppression_results

    def _analyze_foreground_preservation(self, image: np.ndarray, suppression_mask: np.ndarray,
                                       ground_truth_mask: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """分析前景保留效果"""
        if ground_truth_mask is not None:
            # 使用真实标签计算精确的前景保留率
            foreground_pixels = np.sum(ground_truth_mask > 0)
            preserved_pixels = np.sum((ground_truth_mask > 0) & (suppression_mask > 0.5))
            preservation_rate = preserved_pixels / foreground_pixels if foreground_pixels > 0 else 0

            # 计算前景区域的平均保留强度
            fg_preservation_values = suppression_mask[ground_truth_mask > 0]
            avg_preservation_strength = np.mean(fg_preservation_values) if len(fg_preservation_values) > 0 else 0

        else:
            # 使用启发式方法估计前景区域
            # 假设图像中心区域和高对比度区域更可能是前景
            h, w = image.shape[:2]
            center_mask = np.zeros((h, w), dtype=np.uint8)
            center_mask[h//4:3*h//4, w//4:3*w//4] = 1

            # 计算梯度作为前景指示
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)

            # 高梯度区域可能是前景
            gradient_threshold = np.percentile(gradient_magnitude, 75)
            gradient_mask = (gradient_magnitude > gradient_threshold).astype(np.uint8)

            # 组合中心区域和高梯度区域作为估计的前景
            estimated_foreground = np.logical_or(center_mask, gradient_mask)

            foreground_pixels = np.sum(estimated_foreground)
            preserved_pixels = np.sum(estimated_foreground & (suppression_mask > 0.5))
            preservation_rate = preserved_pixels / foreground_pixels if foreground_pixels > 0 else 0

            fg_preservation_values = suppression_mask[estimated_foreground]
            avg_preservation_strength = np.mean(fg_preservation_values) if len(fg_preservation_values) > 0 else 0

        return {
            'total_foreground_pixels': int(foreground_pixels),
            'preserved_pixels': int(preserved_pixels),
            'preservation_rate': float(preservation_rate),
            'target_rate': self.foreground_preservation_target,
            'rate_achievement': float(preservation_rate / self.foreground_preservation_target),
            'avg_preservation_strength': float(avg_preservation_strength),
            'performance_grade': self._grade_preservation_performance(
                preservation_rate, self.foreground_preservation_target
            ),
            'has_ground_truth': ground_truth_mask is not None
        }

    def _grade_suppression_performance(self, actual_rate: float, target_rate: float) -> str:
        """评估抑制性能等级"""
        achievement = actual_rate / target_rate if target_rate > 0 else 0

        if achievement >= 0.95:
            return "优秀"
        elif achievement >= 0.85:
            return "良好"
        elif achievement >= 0.70:
            return "一般"
        else:
            return "较差"

    def _grade_preservation_performance(self, actual_rate: float, target_rate: float) -> str:
        """评估保留性能等级"""
        achievement = actual_rate / target_rate if target_rate > 0 else 0

        if achievement >= 0.95:
            return "优秀"
        elif achievement >= 0.90:
            return "良好"
        elif achievement >= 0.80:
            return "一般"
        else:
            return "较差"

    def _evaluate_overall_performance(self, bg_suppression: Dict, fg_preservation: Dict) -> Dict[str, Any]:
        """评估整体性能"""
        # 计算加权综合得分
        suppression_scores = []
        suppression_weights = []

        for bg_type, result in bg_suppression.items():
            if result['total_pixels'] > 0:
                suppression_scores.append(result['rate_achievement'])
                suppression_weights.append(result['total_pixels'])

        if suppression_scores:
            weighted_suppression_score = np.average(suppression_scores, weights=suppression_weights)
        else:
            weighted_suppression_score = 0

        preservation_score = fg_preservation['rate_achievement']

        # 综合评分 (抑制70%, 保留30%)
        overall_score = weighted_suppression_score * 0.7 + preservation_score * 0.3

        return {
            'weighted_suppression_score': float(weighted_suppression_score),
            'preservation_score': float(preservation_score),
            'overall_score': float(overall_score),
            'performance_level': self._assess_overall_performance(overall_score),
            'meets_targets': self._check_target_achievement(bg_suppression, fg_preservation)
        }

    def _assess_overall_performance(self, score: float) -> str:
        """评估整体性能水平"""
        if score >= 0.95:
            return "优秀"
        elif score >= 0.85:
            return "良好"
        elif score >= 0.70:
            return "一般"
        else:
            return "需要改进"

    def _check_target_achievement(self, bg_suppression: Dict, fg_preservation: Dict) -> Dict[str, bool]:
        """检查目标达成情况"""
        targets_met = {}

        for bg_type, result in bg_suppression.items():
            targets_met[f"{bg_type}_suppression"] = result['rate_achievement'] >= 0.90

        targets_met['foreground_preservation'] = fg_preservation['rate_achievement'] >= 0.90
        targets_met['all_targets'] = all(targets_met.values())

        return targets_met

    def _analyze_adaptive_thresholds(self, suppression_mask: np.ndarray) -> Dict[str, Any]:
        """分析自适应阈值"""
        # 计算不同阈值下的性能
        thresholds = np.arange(0.1, 1.0, 0.1)
        threshold_analysis = {}

        for threshold in thresholds:
            binary_mask = (suppression_mask > threshold).astype(np.uint8)
            foreground_ratio = np.mean(binary_mask)

            threshold_analysis[f"threshold_{threshold:.1f}"] = {
                'threshold': float(threshold),
                'foreground_ratio': float(foreground_ratio),
                'background_ratio': float(1 - foreground_ratio)
            }

        # 找到最优阈值 (使前景比例接近期望值)
        target_fg_ratio = 0.3  # 假设前景占30%
        optimal_threshold = min(thresholds,
                              key=lambda t: abs(np.mean(suppression_mask > t) - target_fg_ratio))

        return {
            'threshold_analysis': threshold_analysis,
            'optimal_threshold': float(optimal_threshold),
            'current_foreground_ratio': float(np.mean(suppression_mask > 0.5)),
            'mask_statistics': {
                'mean': float(np.mean(suppression_mask)),
                'std': float(np.std(suppression_mask)),
                'min': float(np.min(suppression_mask)),
                'max': float(np.max(suppression_mask)),
                'median': float(np.median(suppression_mask))
            }
        }

    def visualize_suppression_analysis(self, image: np.ndarray, suppression_mask: np.ndarray,
                                     analysis_result: Dict, save_path: str = None) -> None:
        """可视化抑制分析结果"""
        print("📊 生成背景抑制分析可视化...")

        # 创建多子图布局
        fig = plt.figure(figsize=(20, 15))

        # 1. 原始图像
        ax1 = plt.subplot(2, 4, 1)
        plt.imshow(image)
        plt.title('原始图像', fontsize=14, fontweight='bold')
        plt.axis('off')

        # 2. 抑制掩码
        ax2 = plt.subplot(2, 4, 2)
        plt.imshow(suppression_mask, cmap='RdYlGn', vmin=0, vmax=1)
        plt.title('背景抑制掩码', fontsize=14, fontweight='bold')
        plt.colorbar(shrink=0.8)
        plt.axis('off')

        # 3. 背景抑制效果对比
        ax3 = plt.subplot(2, 4, 3)
        bg_suppression = analysis_result['background_suppression']

        bg_types = []
        suppression_rates = []
        target_rates = []
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

        for i, (bg_type, result) in enumerate(bg_suppression.items()):
            if result['total_pixels'] > 0:
                bg_types.append(self.background_types[bg_type]['name'])
                suppression_rates.append(result['suppression_rate'])
                target_rates.append(result['target_rate'])

        if bg_types:
            x = np.arange(len(bg_types))
            width = 0.35

            bars1 = plt.bar(x - width/2, suppression_rates, width, label='实际抑制率',
                           color=colors[:len(bg_types)], alpha=0.7)
            bars2 = plt.bar(x + width/2, target_rates, width, label='目标抑制率',
                           color='gray', alpha=0.5)

            plt.xlabel('背景类型')
            plt.ylabel('抑制率')
            plt.title('背景抑制效果对比', fontsize=14, fontweight='bold')
            plt.xticks(x, bg_types)
            plt.legend()
            plt.ylim(0, 1)

            # 添加数值标签
            for bar, rate in zip(bars1, suppression_rates):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{rate:.3f}', ha='center', va='bottom', fontsize=10)

        # 4. 前景保留分析
        ax4 = plt.subplot(2, 4, 4)
        fg_preservation = analysis_result['foreground_preservation']

        preservation_data = [
            fg_preservation['preservation_rate'],
            1 - fg_preservation['preservation_rate']
        ]
        labels = ['保留', '丢失']
        colors_pie = ['#32CD32', '#FF6347']

        plt.pie(preservation_data, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
        plt.title('前景保留分析', fontsize=14, fontweight='bold')

        # 5. 整体性能雷达图
        ax5 = plt.subplot(2, 4, 5, projection='polar')

        metrics = ['红土抑制', '杂草抑制', '阴影抑制', '前景保留']
        values = []

        for bg_type in ['red_soil', 'weeds', 'shadows']:
            if bg_type in bg_suppression and bg_suppression[bg_type]['total_pixels'] > 0:
                values.append(bg_suppression[bg_type]['rate_achievement'])
            else:
                values.append(0)

        values.append(fg_preservation['rate_achievement'])

        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        values += values[:1]  # 闭合图形
        angles += angles[:1]

        ax5.plot(angles, values, 'o-', linewidth=2, color='#FF6B6B')
        ax5.fill(angles, values, alpha=0.25, color='#FF6B6B')
        ax5.set_xticks(angles[:-1])
        ax5.set_xticklabels(metrics)
        ax5.set_ylim(0, 1.2)
        ax5.set_title('整体性能评估', fontsize=14, fontweight='bold', pad=20)

        # 6. 阈值分析
        ax6 = plt.subplot(2, 4, 6)
        threshold_analysis = analysis_result['adaptive_thresholds']['threshold_analysis']

        thresholds = [float(k.split('_')[1]) for k in threshold_analysis.keys()]
        fg_ratios = [v['foreground_ratio'] for v in threshold_analysis.values()]

        plt.plot(thresholds, fg_ratios, 'o-', linewidth=2, markersize=6, color='#4ECDC4')
        optimal_threshold = analysis_result['adaptive_thresholds']['optimal_threshold']
        plt.axvline(x=optimal_threshold, color='red', linestyle='--', alpha=0.7, label=f'最优阈值: {optimal_threshold:.1f}')
        plt.axvline(x=0.5, color='gray', linestyle=':', alpha=0.7, label='当前阈值: 0.5')

        plt.xlabel('阈值')
        plt.ylabel('前景比例')
        plt.title('自适应阈值分析', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # 7. 统计摘要表格
        ax7 = plt.subplot(2, 4, 7)
        ax7.axis('off')

        overall_perf = analysis_result['overall_performance']
        summary_data = [
            ['整体评分', f"{overall_perf['overall_score']:.3f}"],
            ['性能等级', overall_perf['performance_level']],
            ['前景保留率', f"{fg_preservation['preservation_rate']:.3f}"],
            ['最优阈值', f"{analysis_result['adaptive_thresholds']['optimal_threshold']:.2f}"],
            ['目标达成', '是' if overall_perf['meets_targets']['all_targets'] else '否']
        ]

        table = ax7.table(cellText=summary_data,
                         colLabels=['指标', '数值'],
                         cellLoc='center',
                         loc='center',
                         colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 2)
        ax7.set_title('性能摘要', fontsize=14, fontweight='bold', pad=20)

        # 8. 掩码直方图
        ax8 = plt.subplot(2, 4, 8)
        plt.hist(suppression_mask.flatten(), bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        plt.axvline(x=0.5, color='red', linestyle='--', alpha=0.7, label='默认阈值')
        plt.axvline(x=optimal_threshold, color='green', linestyle='--', alpha=0.7, label='最优阈值')
        plt.xlabel('抑制掩码值')
        plt.ylabel('像素数量')
        plt.title('掩码值分布', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 抑制分析图已保存至: {save_path}")
        else:
            plt.show()

        return fig

    def generate_suppression_report(self, analysis_result: Dict, save_path: str = None) -> Dict:
        """生成背景抑制分析报告"""
        report = {
            'analysis_timestamp': analysis_result['timestamp'],
            'image_info': analysis_result['image_info'],
            'performance_summary': {
                'overall_score': analysis_result['overall_performance']['overall_score'],
                'performance_level': analysis_result['overall_performance']['performance_level'],
                'targets_achieved': analysis_result['overall_performance']['meets_targets']['all_targets']
            },
            'background_suppression_details': analysis_result['background_suppression'],
            'foreground_preservation_details': analysis_result['foreground_preservation'],
            'adaptive_threshold_recommendation': analysis_result['adaptive_thresholds']['optimal_threshold'],
            'recommendations': self._generate_suppression_recommendations(analysis_result)
        }

        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"✅ 背景抑制分析报告已保存至: {save_path}")

        return report

    def _generate_suppression_recommendations(self, analysis_result: Dict) -> List[str]:
        """生成背景抑制优化建议"""
        recommendations = []

        bg_suppression = analysis_result['background_suppression']
        fg_preservation = analysis_result['foreground_preservation']
        overall_perf = analysis_result['overall_performance']

        # 基于整体性能的建议
        if overall_perf['overall_score'] < 0.8:
            recommendations.append("整体抑制性能需要改进，建议调整网络结构或训练策略")

        # 基于具体背景类型的建议
        for bg_type, result in bg_suppression.items():
            if result['total_pixels'] > 0 and result['rate_achievement'] < 0.9:
                bg_name = self.background_types[bg_type]['name']
                recommendations.append(
                    f"{bg_name}抑制效果不佳（{result['suppression_rate']:.1%}），"
                    f"建议增强{bg_name}相关的训练样本或调整颜色空间特征"
                )

        # 基于前景保留的建议
        if fg_preservation['rate_achievement'] < 0.9:
            recommendations.append(
                f"前景保留率偏低（{fg_preservation['preservation_rate']:.1%}），"
                "建议降低抑制强度或改进前景检测算法"
            )

        # 基于阈值的建议
        optimal_threshold = analysis_result['adaptive_thresholds']['optimal_threshold']
        if abs(optimal_threshold - 0.5) > 0.1:
            recommendations.append(
                f"建议将抑制阈值从0.5调整为{optimal_threshold:.2f}以获得更好的前景/背景平衡"
            )

        # 通用建议
        if not recommendations:
            recommendations.append("背景抑制性能良好，各项指标均达到预期目标")

        return recommendations

    def compare_suppression_methods(self, results_list: List[Dict], method_names: List[str] = None) -> Dict:
        """比较不同背景抑制方法的性能"""
        if not results_list:
            return {}

        if method_names is None:
            method_names = [f"Method_{i+1}" for i in range(len(results_list))]

        comparison = {
            'num_methods': len(results_list),
            'method_names': method_names,
            'performance_comparison': {},
            'best_method': {},
            'improvement_suggestions': []
        }

        # 收集各方法的性能指标
        overall_scores = []
        suppression_scores = []
        preservation_scores = []

        for i, result in enumerate(results_list):
            overall_perf = result['overall_performance']
            overall_scores.append(overall_perf['overall_score'])
            suppression_scores.append(overall_perf['weighted_suppression_score'])
            preservation_scores.append(overall_perf['preservation_score'])

        comparison['performance_comparison'] = {
            'overall_scores': overall_scores,
            'suppression_scores': suppression_scores,
            'preservation_scores': preservation_scores,
            'score_statistics': {
                'overall_mean': float(np.mean(overall_scores)),
                'overall_std': float(np.std(overall_scores)),
                'suppression_mean': float(np.mean(suppression_scores)),
                'preservation_mean': float(np.mean(preservation_scores))
            }
        }

        # 找出最佳方法
        best_idx = np.argmax(overall_scores)
        comparison['best_method'] = {
            'method_name': method_names[best_idx],
            'method_index': best_idx,
            'overall_score': overall_scores[best_idx],
            'performance_advantage': float(overall_scores[best_idx] - np.mean(overall_scores))
        }

        return comparison


def create_synthetic_suppression_mask(image: np.ndarray, noise_level: float = 0.1) -> np.ndarray:
    """创建合成的背景抑制掩码用于测试"""
    h, w = image.shape[:2]

    # 基于图像内容创建掩码
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # 使用边缘检测识别前景
    edges = cv2.Canny(gray, 50, 150)

    # 膨胀边缘以创建前景区域
    kernel = np.ones((5, 5), np.uint8)
    foreground_mask = cv2.dilate(edges, kernel, iterations=2)

    # 转换为概率掩码
    suppression_mask = foreground_mask.astype(np.float32) / 255.0

    # 添加噪声
    noise = np.random.normal(0, noise_level, (h, w))
    suppression_mask = np.clip(suppression_mask + noise, 0, 1)

    # 平滑处理
    suppression_mask = cv2.GaussianBlur(suppression_mask, (5, 5), 1.0)

    return suppression_mask


def main():
    """主函数 - 背景抑制分析示例"""
    print("🎯 背景抑制分支分析工具")
    print("=" * 50)

    # 创建分析器
    analyzer = BackgroundSuppressionAnalyzer()

    try:
        # 示例：使用合成数据进行测试
        print("\n📸 生成测试数据...")

        # 创建测试图像 (可以替换为实际图像)
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # 创建合成的抑制掩码
        suppression_mask = create_synthetic_suppression_mask(test_image)

        print(f"   测试图像尺寸: {test_image.shape}")
        print(f"   抑制掩码范围: [{suppression_mask.min():.3f}, {suppression_mask.max():.3f}]")

        # 运行分析
        print("\n🔍 开始背景抑制性能分析...")
        analysis_result = analyzer.analyze_suppression_performance(
            test_image, suppression_mask
        )

        # 打印关键结果
        overall_perf = analysis_result['overall_performance']
        print(f"\n📊 分析结果:")
        print(f"   整体评分: {overall_perf['overall_score']:.3f}")
        print(f"   性能等级: {overall_perf['performance_level']}")
        print(f"   目标达成: {'是' if overall_perf['meets_targets']['all_targets'] else '否'}")

        # 背景抑制详情
        bg_suppression = analysis_result['background_suppression']
        print(f"\n🎯 背景抑制详情:")
        for bg_type, result in bg_suppression.items():
            if result['total_pixels'] > 0:
                bg_name = analyzer.background_types[bg_type]['name']
                print(f"   {bg_name}: {result['suppression_rate']:.1%} (目标: {result['target_rate']:.1%})")

        # 前景保留详情
        fg_preservation = analysis_result['foreground_preservation']
        print(f"\n🌿 前景保留详情:")
        print(f"   保留率: {fg_preservation['preservation_rate']:.1%}")
        print(f"   目标: {fg_preservation['target_rate']:.1%}")

        # 生成可视化
        print("\n📊 生成可视化分析...")
        save_path = f"results/background_suppression_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        Path("results").mkdir(exist_ok=True)

        analyzer.visualize_suppression_analysis(
            test_image, suppression_mask, analysis_result, save_path
        )

        # 生成报告
        print("\n📋 生成分析报告...")
        report_path = f"results/suppression_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report = analyzer.generate_suppression_report(analysis_result, report_path)

        # 打印建议
        print("\n💡 优化建议:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"   {i}. {recommendation}")

        print(f"\n✅ 分析完成！")

    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()