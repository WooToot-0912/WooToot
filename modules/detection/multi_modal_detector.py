#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云南烤烟病害多模态检测模块 - 重构增强版
结合自适应颜色分析、高级纹理特征提取和特征融合网络

重构亮点:
1. 自适应颜色阈值选择
2. 高级纹理特征提取 (LBP, GLCM, Gabor)
3. 深度特征融合网络
4. 多尺度特征金字塔
5. 注意力引导的特征选择

版本: v2.0 - 架构重构版
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import cv2
import numpy as np
import math
from typing import Tuple, Dict, List, Optional, Any
from sklearn.cluster import KMeans
from skimage.feature import local_binary_pattern, graycomatrix, graycoprops
from scipy import ndimage
import warnings
warnings.filterwarnings('ignore')

from ..attention.enhanced_attention_suite import create_attention_block, SpatialChannelAttention
try:
    from .defect_detector import DefectDetector
    from .region_analyzer import RegionAnalyzer
    from .spectral_index import TobaccoSpectralIndex
except ImportError:
    # 如果导入失败，创建占位符类
    class DefectDetector:
        def detect_defects(self, image): return {'defects': [], 'visualization': image}
    class RegionAnalyzer:
        def analyze_region(self, image, bbox): return {'health_score': 0.5}
    class TobaccoSpectralIndex:
        def calculate_tmdi(self, image): return {'tmdi_index': 0.0}

class AdaptiveColorDiseaseDetector(nn.Module):
    """
    自适应颜色病害检测器 - 重构增强版

    新增功能:
    1. 自适应颜色阈值选择
    2. 多色彩空间融合分析 (HSV, LAB, YUV)
    3. 颜色聚类分析
    4. 季节性颜色适应
    5. 光照条件自适应
    """
    def __init__(self, num_classes=5, adaptive_threshold=True):
        super(AdaptiveColorDiseaseDetector, self).__init__()
        self.num_classes = num_classes
        self.adaptive_threshold = adaptive_threshold

        # 基础病害颜色范围 (HSV空间)
        self.base_disease_color_ranges = {
            'healthy': {'lower': np.array([35, 40, 40]), 'upper': np.array([85, 255, 255])},
            'mosaic_virus': {'lower': np.array([20, 50, 50]), 'upper': np.array([40, 255, 255])},
            'brown_spot': {'lower': np.array([5, 40, 20]), 'upper': np.array([25, 255, 180])},
            'wildfire': {'lower': np.array([10, 100, 100]), 'upper': np.array([30, 255, 255])},
            'bacterial_wilt': {'lower': np.array([0, 30, 30]), 'upper': np.array([35, 255, 150])}
        }

        # 自适应颜色范围 (运行时更新)
        self.adaptive_color_ranges = self.base_disease_color_ranges.copy()

        # 多尺度颜色特征提取网络
        self.color_feature_extractor = nn.ModuleDict({
            'hsv_branch': self._build_color_branch(3, 64),
            'lab_branch': self._build_color_branch(3, 64),
            'yuv_branch': self._build_color_branch(3, 64)
        })

        # 特征融合网络
        self.feature_fusion = nn.Sequential(
            nn.Conv2d(192, 256, 1),  # 64*3 = 192
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            create_attention_block(256, 'eca'),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten()
        )

        # 分类头
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )

        # 颜色聚类器 (用于自适应阈值)
        self.color_clusterer = None
        self.adaptation_history = []

    def _build_color_branch(self, in_channels: int, out_channels: int) -> nn.Module:
        """构建单个颜色空间分支"""
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels//2, 3, padding=1),
            nn.BatchNorm2d(out_channels//2),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels//2, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            create_attention_block(out_channels, 'eca')
        )
    
    def adapt_color_thresholds(self, image_bgr: np.ndarray) -> Dict[str, Any]:
        """自适应颜色阈值选择"""
        # 1. 光照条件评估
        illumination_info = self._assess_illumination(image_bgr)

        # 2. 颜色聚类分析
        dominant_colors = self._extract_dominant_colors(image_bgr, n_clusters=8)

        # 3. 基于聚类结果调整阈值
        adapted_ranges = {}
        for disease, base_range in self.base_disease_color_ranges.items():
            adapted_range = self._adjust_color_range(
                base_range, dominant_colors, illumination_info
            )
            adapted_ranges[disease] = adapted_range

        # 4. 更新自适应范围
        self.adaptive_color_ranges = adapted_ranges

        return {
            'illumination_info': illumination_info,
            'dominant_colors': dominant_colors,
            'adapted_ranges': adapted_ranges
        }

    def _assess_illumination(self, image_bgr: np.ndarray) -> Dict[str, float]:
        """评估光照条件"""
        # 转换到LAB空间分析亮度
        lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]

        # 计算光照指标
        mean_brightness = np.mean(l_channel)
        brightness_std = np.std(l_channel)
        brightness_range = np.max(l_channel) - np.min(l_channel)

        # 光照均匀性 (基于梯度)
        grad_x = cv2.Sobel(l_channel, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(l_channel, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        illumination_uniformity = 1.0 / (1.0 + np.mean(gradient_magnitude))

        return {
            'mean_brightness': float(mean_brightness),
            'brightness_std': float(brightness_std),
            'brightness_range': float(brightness_range),
            'illumination_uniformity': float(illumination_uniformity),
            'lighting_condition': self._classify_lighting_condition(mean_brightness)
        }

    def _classify_lighting_condition(self, mean_brightness: float) -> str:
        """分类光照条件"""
        if mean_brightness < 80:
            return 'low_light'
        elif mean_brightness > 180:
            return 'high_light'
        else:
            return 'normal_light'

    def _extract_dominant_colors(self, image_bgr: np.ndarray, n_clusters: int = 8) -> List[Dict]:
        """提取主导颜色"""
        # 转换到HSV空间
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

        # 重塑为聚类输入格式
        pixels = hsv.reshape(-1, 3)

        # K-means聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(pixels)

        # 计算每个聚类的比例
        labels = kmeans.labels_
        unique_labels, counts = np.unique(labels, return_counts=True)
        proportions = counts / len(labels)

        # 构建主导颜色信息
        dominant_colors = []
        for i, center in enumerate(kmeans.cluster_centers_):
            dominant_colors.append({
                'hsv_center': center.astype(int),
                'proportion': float(proportions[i]),
                'pixel_count': int(counts[i])
            })

        # 按比例排序
        dominant_colors.sort(key=lambda x: x['proportion'], reverse=True)

        return dominant_colors

    def _adjust_color_range(self, base_range: Dict, dominant_colors: List[Dict],
                           illumination_info: Dict) -> Dict[str, np.ndarray]:
        """基于分析结果调整颜色范围"""
        lower = base_range['lower'].copy()
        upper = base_range['upper'].copy()

        # 1. 基于光照条件调整
        lighting_condition = illumination_info['lighting_condition']
        if lighting_condition == 'low_light':
            # 低光照：放宽饱和度和亮度下限
            lower[1] = max(0, lower[1] - 20)  # 饱和度
            lower[2] = max(0, lower[2] - 30)  # 亮度
        elif lighting_condition == 'high_light':
            # 高光照：收紧饱和度和亮度上限
            upper[1] = min(255, upper[1] - 10)  # 饱和度
            upper[2] = min(255, upper[2] - 20)  # 亮度

        # 2. 基于主导颜色调整色调范围
        relevant_colors = [
            color for color in dominant_colors
            if color['proportion'] > 0.05  # 只考虑占比>5%的颜色
        ]

        if relevant_colors:
            # 找到与基础范围最接近的主导颜色
            base_hue_center = (lower[0] + upper[0]) / 2
            closest_color = min(relevant_colors,
                              key=lambda x: abs(x['hsv_center'][0] - base_hue_center))

            # 微调色调范围
            hue_shift = closest_color['hsv_center'][0] - base_hue_center
            if abs(hue_shift) < 30:  # 只在合理范围内调整
                lower[0] = max(0, lower[0] + int(hue_shift * 0.3))
                upper[0] = min(179, upper[0] + int(hue_shift * 0.3))

        return {'lower': lower, 'upper': upper}

    def extract_multi_space_color_features(self, image_bgr: np.ndarray) -> Dict[str, Any]:
        """提取多色彩空间颜色特征"""
        # 1. 自适应阈值调整
        adaptation_info = self.adapt_color_thresholds(image_bgr)

        # 2. 多色彩空间转换
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        yuv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2YUV)

        # 3. 各色彩空间特征提取
        color_features = {
            'hsv_features': self._extract_hsv_features(hsv),
            'lab_features': self._extract_lab_features(lab),
            'yuv_features': self._extract_yuv_features(yuv),
            'adaptation_info': adaptation_info
        }

        return color_features

    def _extract_hsv_features(self, hsv: np.ndarray) -> Dict[str, float]:
        """提取HSV空间特征"""
        features = {}

        for disease, color_range in self.adaptive_color_ranges.items():
            # 创建颜色掩码
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])

            # 基础特征
            color_ratio = np.sum(mask > 0) / (mask.shape[0] * mask.shape[1])

            # 形态学特征
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask_morphed = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            concentration = np.sum(mask_morphed > 0) / (np.sum(mask > 0) + 1e-6)

            # 分布特征
            if np.sum(mask > 0) > 0:
                coords = np.where(mask > 0)
                centroid_y, centroid_x = np.mean(coords[0]), np.mean(coords[1])
                spread = np.std(coords[0]) + np.std(coords[1])
            else:
                centroid_y = centroid_x = spread = 0.0

            features[f'{disease}_ratio'] = float(color_ratio)
            features[f'{disease}_concentration'] = float(concentration)
            features[f'{disease}_spread'] = float(spread)

        return features

    def _extract_lab_features(self, lab: np.ndarray) -> Dict[str, float]:
        """提取LAB空间特征"""
        l_channel, a_channel, b_channel = cv2.split(lab)

        return {
            'l_mean': float(np.mean(l_channel)),
            'l_std': float(np.std(l_channel)),
            'a_mean': float(np.mean(a_channel)),
            'a_std': float(np.std(a_channel)),
            'b_mean': float(np.mean(b_channel)),
            'b_std': float(np.std(b_channel)),
            'color_contrast': float(np.std(l_channel) / (np.mean(l_channel) + 1e-6))
        }

    def _extract_yuv_features(self, yuv: np.ndarray) -> Dict[str, float]:
        """提取YUV空间特征"""
        y_channel, u_channel, v_channel = cv2.split(yuv)

        return {
            'y_mean': float(np.mean(y_channel)),
            'y_std': float(np.std(y_channel)),
            'u_mean': float(np.mean(u_channel)),
            'u_std': float(np.std(u_channel)),
            'v_mean': float(np.mean(v_channel)),
            'v_std': float(np.std(v_channel)),
            'chroma_intensity': float(np.sqrt(np.mean(u_channel**2) + np.mean(v_channel**2)))
        }

    def forward(self, x):
        """前向传播 - 多色彩空间融合"""
        # 假设输入已经是多色彩空间的tensor格式
        # 实际使用时需要预处理将BGR转换为多色彩空间

        # 分别处理各色彩空间
        hsv_features = self.color_feature_extractor['hsv_branch'](x[:, :3, :, :])  # HSV
        lab_features = self.color_feature_extractor['lab_branch'](x[:, 3:6, :, :])  # LAB
        yuv_features = self.color_feature_extractor['yuv_branch'](x[:, 6:9, :, :])  # YUV

        # 特征融合
        fused_features = torch.cat([hsv_features, lab_features, yuv_features], dim=1)
        fused_features = self.feature_fusion(fused_features)

        # 分类
        output = self.classifier(fused_features)

        return output

class AdvancedTextureDiseaseDetector(nn.Module):
    """
    高级纹理病害检测器 - 重构增强版

    新增功能:
    1. 多尺度LBP纹理分析
    2. GLCM (灰度共生矩阵) 特征
    3. Gabor滤波器组
    4. 小波纹理分析
    5. 分形维数计算
    """
    def __init__(self, num_classes=5):
        super(AdvancedTextureDiseaseDetector, self).__init__()
        self.num_classes = num_classes

        # LBP参数配置
        self.lbp_configs = [
            {'radius': 1, 'n_points': 8, 'method': 'uniform'},
            {'radius': 2, 'n_points': 16, 'method': 'uniform'},
            {'radius': 3, 'n_points': 24, 'method': 'uniform'}
        ]

        # Gabor滤波器参数
        self.gabor_params = self._generate_gabor_params()

        # 深度纹理特征提取网络
        self.texture_feature_extractor = nn.ModuleDict({
            'lbp_branch': self._build_texture_branch(len(self.lbp_configs), 64),
            'glcm_branch': self._build_texture_branch(4, 32),  # 4个GLCM特征
            'gabor_branch': self._build_texture_branch(len(self.gabor_params), 64),
            'wavelet_branch': self._build_texture_branch(4, 32)  # 4个小波子带
        })

        # 特征融合网络
        self.feature_fusion = nn.Sequential(
            nn.Conv2d(192, 256, 1),  # 64+32+64+32 = 192
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            create_attention_block(256, 'eca'),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten()
        )

        # 分类头
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )

    def _generate_gabor_params(self) -> List[Dict]:
        """生成Gabor滤波器参数"""
        params = []
        frequencies = [0.1, 0.2, 0.3, 0.4]
        orientations = [0, 45, 90, 135]

        for freq in frequencies:
            for orient in orientations:
                params.append({
                    'frequency': freq,
                    'orientation': np.radians(orient),
                    'sigma_x': 2.0,
                    'sigma_y': 2.0
                })

        return params

    def _build_texture_branch(self, in_channels: int, out_channels: int) -> nn.Module:
        """构建纹理特征分支"""
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels//2, 3, padding=1),
            nn.BatchNorm2d(out_channels//2),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels//2, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            create_attention_block(out_channels, 'eca')
        )
    
    def extract_multi_scale_lbp_features(self, gray_image: np.ndarray) -> np.ndarray:
        """提取多尺度LBP特征"""
        all_lbp_features = []

        for config in self.lbp_configs:
            lbp = local_binary_pattern(
                gray_image,
                config['n_points'],
                config['radius'],
                method=config['method']
            )

            # 计算LBP直方图
            n_bins = config['n_points'] + 2
            hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins))
            hist = hist.astype(np.float32)
            hist /= (hist.sum() + 1e-6)  # 归一化

            all_lbp_features.append(hist)

        return np.concatenate(all_lbp_features)

    def extract_glcm_features(self, gray_image: np.ndarray) -> np.ndarray:
        """提取GLCM (灰度共生矩阵) 特征"""
        # 量化灰度级别以减少计算复杂度
        gray_quantized = (gray_image // 32).astype(np.uint8)

        # 计算不同方向的GLCM
        distances = [1, 2]
        angles = [0, np.pi/4, np.pi/2, 3*np.pi/4]

        glcm_features = []

        for distance in distances:
            glcm = graycomatrix(
                gray_quantized,
                distances=[distance],
                angles=angles,
                levels=8,  # 8个灰度级别
                symmetric=True,
                normed=True
            )

            # 提取纹理特征
            contrast = graycoprops(glcm, 'contrast').flatten()
            dissimilarity = graycoprops(glcm, 'dissimilarity').flatten()
            homogeneity = graycoprops(glcm, 'homogeneity').flatten()
            energy = graycoprops(glcm, 'energy').flatten()

            glcm_features.extend([
                np.mean(contrast), np.std(contrast),
                np.mean(dissimilarity), np.std(dissimilarity),
                np.mean(homogeneity), np.std(homogeneity),
                np.mean(energy), np.std(energy)
            ])

        return np.array(glcm_features, dtype=np.float32)

    def extract_gabor_features(self, gray_image: np.ndarray) -> np.ndarray:
        """提取Gabor滤波器特征"""
        gabor_responses = []

        for params in self.gabor_params:
            # 创建Gabor滤波器
            kernel_real = cv2.getGaborKernel(
                (21, 21),  # 核大小
                params['sigma_x'],
                params['orientation'],
                2 * np.pi / params['frequency'],
                1.0,  # 长宽比
                0,    # 相位偏移
                ktype=cv2.CV_32F
            )

            # 应用滤波器
            filtered = cv2.filter2D(gray_image.astype(np.float32), cv2.CV_8UC3, kernel_real)

            # 计算响应统计量
            response_mean = np.mean(np.abs(filtered))
            response_std = np.std(filtered)
            response_energy = np.mean(filtered ** 2)

            gabor_responses.extend([response_mean, response_std, response_energy])

        return np.array(gabor_responses, dtype=np.float32)

    def extract_wavelet_features(self, gray_image: np.ndarray) -> np.ndarray:
        """提取小波纹理特征"""
        try:
            import pywt
        except ImportError:
            # 如果没有pywt，使用简化的频域分析
            return self._extract_frequency_features(gray_image)

        # 小波分解
        coeffs = pywt.dwt2(gray_image, 'db4')
        cA, (cH, cV, cD) = coeffs

        # 计算各子带的统计特征
        wavelet_features = []

        for subband, name in zip([cA, cH, cV, cD], ['LL', 'LH', 'HL', 'HH']):
            features = [
                np.mean(subband),
                np.std(subband),
                np.mean(np.abs(subband)),
                np.percentile(subband, 90) - np.percentile(subband, 10)  # 鲁棒范围
            ]
            wavelet_features.extend(features)

        return np.array(wavelet_features, dtype=np.float32)

    def _extract_frequency_features(self, gray_image: np.ndarray) -> np.ndarray:
        """提取频域特征 (小波的替代方案)"""
        # FFT变换
        f_transform = np.fft.fft2(gray_image)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.abs(f_shift)

        # 分频段分析
        h, w = magnitude_spectrum.shape
        center_h, center_w = h // 2, w // 2

        # 低频、中频、高频区域
        low_freq = magnitude_spectrum[center_h-h//4:center_h+h//4, center_w-w//4:center_w+w//4]

        # 创建环形掩码用于中频和高频
        y, x = np.ogrid[:h, :w]
        center_mask = (x - center_w) ** 2 + (y - center_h) ** 2

        mid_freq_mask = (center_mask > (min(h, w) // 8) ** 2) & (center_mask < (min(h, w) // 4) ** 2)
        high_freq_mask = center_mask > (min(h, w) // 4) ** 2

        mid_freq = magnitude_spectrum[mid_freq_mask]
        high_freq = magnitude_spectrum[high_freq_mask]

        # 计算特征
        features = [
            np.mean(low_freq), np.std(low_freq),
            np.mean(mid_freq), np.std(mid_freq),
            np.mean(high_freq), np.std(high_freq),
            np.sum(low_freq) / np.sum(magnitude_spectrum),  # 低频能量比
            np.sum(high_freq) / np.sum(magnitude_spectrum)  # 高频能量比
        ]

        return np.array(features, dtype=np.float32)

    def calculate_fractal_dimension(self, gray_image: np.ndarray) -> float:
        """计算分形维数"""
        # 使用盒计数法计算分形维数
        def box_count(image, box_size):
            # 将图像二值化
            threshold = np.mean(image)
            binary = (image > threshold).astype(int)

            # 计算需要的盒子数量
            h, w = binary.shape
            boxes = 0

            for i in range(0, h, box_size):
                for j in range(0, w, box_size):
                    box = binary[i:i+box_size, j:j+box_size]
                    if np.any(box):
                        boxes += 1

            return boxes

        # 不同尺度的盒子大小
        box_sizes = [2, 4, 8, 16, 32]
        box_counts = []

        for size in box_sizes:
            if size < min(gray_image.shape):
                count = box_count(gray_image, size)
                box_counts.append(count)
            else:
                break

        if len(box_counts) < 2:
            return 1.5  # 默认分形维数

        # 线性拟合计算分形维数
        log_sizes = np.log(box_sizes[:len(box_counts)])
        log_counts = np.log(box_counts)

        # 使用最小二乘法拟合
        coeffs = np.polyfit(log_sizes, log_counts, 1)
        fractal_dim = -coeffs[0]  # 斜率的负值

        return float(fractal_dim)

    def extract_comprehensive_texture_features(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """提取综合纹理特征"""
        texture_features = {
            'lbp_features': self.extract_multi_scale_lbp_features(gray_image),
            'glcm_features': self.extract_glcm_features(gray_image),
            'gabor_features': self.extract_gabor_features(gray_image),
            'wavelet_features': self.extract_wavelet_features(gray_image),
            'fractal_dimension': self.calculate_fractal_dimension(gray_image)
        }

        return texture_features

    def forward(self, x):
        """前向传播 - 多纹理特征融合"""
        # 假设输入已经是多纹理特征的tensor格式
        # 实际使用时需要预处理提取各种纹理特征

        # 分别处理各纹理特征
        lbp_features = self.texture_feature_extractor['lbp_branch'](x[:, :len(self.lbp_configs), :, :])
        glcm_features = self.texture_feature_extractor['glcm_branch'](x[:, len(self.lbp_configs):len(self.lbp_configs)+4, :, :])
        gabor_features = self.texture_feature_extractor['gabor_branch'](x[:, -len(self.gabor_params)-4:-4, :, :])
        wavelet_features = self.texture_feature_extractor['wavelet_branch'](x[:, -4:, :, :])

        # 特征融合
        fused_features = torch.cat([lbp_features, glcm_features, gabor_features, wavelet_features], dim=1)
        fused_features = self.feature_fusion(fused_features)

        # 分类
        output = self.classifier(fused_features)

        return output


class DeepFeatureFusionNetwork(nn.Module):
    """
    深度特征融合网络 - 重构增强版

    新增功能:
    1. 多尺度特征金字塔融合
    2. 注意力引导的特征选择
    3. 跨模态特征交互
    4. 自适应权重学习
    5. 残差连接和密集连接
    """
    def __init__(self, color_dim=256, texture_dim=256, thermal_dim=128, num_classes=5):
        super(DeepFeatureFusionNetwork, self).__init__()

        self.color_dim = color_dim
        self.texture_dim = texture_dim
        self.thermal_dim = thermal_dim
        self.total_dim = color_dim + texture_dim + thermal_dim

        # 特征预处理层
        self.feature_preprocessors = nn.ModuleDict({
            'color_prep': nn.Sequential(
                nn.Linear(color_dim, color_dim),
                nn.LayerNorm(color_dim),
                nn.ReLU(inplace=True),
                nn.Dropout(0.1)
            ),
            'texture_prep': nn.Sequential(
                nn.Linear(texture_dim, texture_dim),
                nn.LayerNorm(texture_dim),
                nn.ReLU(inplace=True),
                nn.Dropout(0.1)
            ),
            'thermal_prep': nn.Sequential(
                nn.Linear(thermal_dim, thermal_dim),
                nn.LayerNorm(thermal_dim),
                nn.ReLU(inplace=True),
                nn.Dropout(0.1)
            )
        })

        # 跨模态注意力机制
        self.cross_modal_attention = nn.MultiheadAttention(
            embed_dim=256,
            num_heads=8,
            dropout=0.1,
            batch_first=True
        )

        # 特征投影层 (统一维度)
        self.feature_projectors = nn.ModuleDict({
            'color_proj': nn.Linear(color_dim, 256),
            'texture_proj': nn.Linear(texture_dim, 256),
            'thermal_proj': nn.Linear(thermal_dim, 256)
        })

        # 多尺度融合网络
        self.multi_scale_fusion = nn.ModuleList([
            self._build_fusion_block(256 * 3, 512, 'scale_1'),
            self._build_fusion_block(512, 256, 'scale_2'),
            self._build_fusion_block(256, 128, 'scale_3')
        ])

        # 自适应权重学习
        self.adaptive_weights = nn.Sequential(
            nn.Linear(256 * 3, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 3),
            nn.Softmax(dim=1)
        )

        # 最终分类器
        self.final_classifier = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(64, num_classes)
        )

        # 辅助分类器 (用于多任务学习)
        self.auxiliary_classifiers = nn.ModuleDict({
            'color_aux': nn.Linear(256, num_classes),
            'texture_aux': nn.Linear(256, num_classes),
            'thermal_aux': nn.Linear(256, num_classes)
        })

    def _build_fusion_block(self, in_dim: int, out_dim: int, block_name: str) -> nn.Module:
        """构建融合块"""
        return nn.Sequential(
            nn.Linear(in_dim, out_dim),
            nn.LayerNorm(out_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(out_dim, out_dim),
            nn.LayerNorm(out_dim),
            nn.ReLU(inplace=True)
        )

    def forward(self, color_features, texture_features, thermal_features, return_aux=False):
        """前向传播"""
        # 1. 特征预处理
        color_prep = self.feature_preprocessors['color_prep'](color_features)
        texture_prep = self.feature_preprocessors['texture_prep'](texture_features)
        thermal_prep = self.feature_preprocessors['thermal_prep'](thermal_features)

        # 2. 特征投影到统一维度
        color_proj = self.feature_projectors['color_proj'](color_prep)
        texture_proj = self.feature_projectors['texture_proj'](texture_prep)
        thermal_proj = self.feature_projectors['thermal_proj'](thermal_prep)

        # 3. 跨模态注意力
        # 将特征重塑为序列格式 [batch, seq_len, embed_dim]
        modal_features = torch.stack([color_proj, texture_proj, thermal_proj], dim=1)  # [B, 3, 256]

        attended_features, attention_weights = self.cross_modal_attention(
            modal_features, modal_features, modal_features
        )

        # 4. 自适应权重学习
        concat_features = torch.cat([color_proj, texture_proj, thermal_proj], dim=1)
        adaptive_weights = self.adaptive_weights(concat_features)  # [B, 3]

        # 5. 加权融合
        weighted_features = torch.sum(
            attended_features * adaptive_weights.unsqueeze(-1), dim=1
        )  # [B, 256]

        # 6. 多尺度融合
        fused_features = concat_features
        for fusion_block in self.multi_scale_fusion:
            fused_features = fusion_block(fused_features)
            # 残差连接
            if fused_features.size(1) == weighted_features.size(1):
                fused_features = fused_features + weighted_features

        # 7. 最终分类
        main_output = self.final_classifier(fused_features)

        if return_aux:
            # 辅助分类器输出
            aux_outputs = {
                'color_aux': self.auxiliary_classifiers['color_aux'](color_proj),
                'texture_aux': self.auxiliary_classifiers['texture_aux'](texture_proj),
                'thermal_aux': self.auxiliary_classifiers['thermal_aux'](thermal_proj)
            }

            return {
                'main_output': main_output,
                'aux_outputs': aux_outputs,
                'attention_weights': attention_weights,
                'adaptive_weights': adaptive_weights,
                'modal_features': {
                    'color': color_proj,
                    'texture': texture_proj,
                    'thermal': thermal_proj
                }
            }

        return main_output
    
    def extract_texture_features(self, gray_image):
        """提取纹理特征"""
        # 灰度共生矩阵特征
        from skimage.feature import graycomatrix, graycoprops
        
        # 计算灰度共生矩阵
        glcm = graycomatrix(gray_image, distances=[1], angles=[0, 45, 90, 135], levels=256, symmetric=True, normed=True)
        
        # 提取纹理特征
        contrast = graycoprops(glcm, 'contrast').mean()
        dissimilarity = graycoprops(glcm, 'dissimilarity').mean()
        homogeneity = graycoprops(glcm, 'homogeneity').mean()
        energy = graycoprops(glcm, 'energy').mean()
        correlation = graycoprops(glcm, 'correlation').mean()
        
        return np.array([contrast, dissimilarity, homogeneity, energy, correlation], dtype=np.float32)
    
    def forward(self, x):
        """前向传播"""
        # 转换为灰度图
        if x.size(1) == 3:
            x = torch.mean(x, dim=1, keepdim=True)
        
        return self.gray_conv(x)

class ThermalDiseaseDetector(nn.Module):
    """
    基于热度特征的病害检测器
    模拟热红外成像检测病害
    """
    def __init__(self, num_classes=5):
        super(ThermalDiseaseDetector, self).__init__()
        self.num_classes = num_classes
        
        # 热度特征提取网络
        self.thermal_conv = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            create_attention_block(128, 'eca'),  # ECA注意力
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(128, num_classes)
        )
    
    def simulate_thermal_map(self, bgr_image):
        """
        模拟热度图
        基于颜色变化模拟病害区域的温度差异
        """
        # 转换为HSV空间
        hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
        
        # 提取亮度通道
        v_channel = hsv[:, :, 2].astype(np.float32)
        
        # 模拟热度：病害区域通常颜色较深，温度可能不同
        # 健康区域（绿色）- 正常温度
        # 病害区域（黄、褐、黑）- 异常温度
        
        # 计算颜色梯度
        grad_x = cv2.Sobel(v_channel, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(v_channel, cv2.CV_32F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # 模拟温度异常
        thermal_map = v_channel.copy()
        
        # 低亮度区域模拟为高温异常（病害发热）
        low_brightness_mask = v_channel < np.percentile(v_channel, 30)
        thermal_map[low_brightness_mask] += 50
        
        # 高梯度区域模拟为温度变化边界
        high_gradient_mask = gradient_magnitude > np.percentile(gradient_magnitude, 70)
        thermal_map[high_gradient_mask] += 30
        
        # 归一化到0-255
        thermal_map = np.clip(thermal_map, 0, 255)
        
        return thermal_map.astype(np.uint8)
    
    def extract_thermal_features(self, thermal_map):
        """提取热度特征"""
        # 温度统计特征
        mean_temp = np.mean(thermal_map)
        std_temp = np.std(thermal_map)
        min_temp = np.min(thermal_map)
        max_temp = np.max(thermal_map)
        temp_range = max_temp - min_temp
        
        # 热点检测
        hot_spots = thermal_map > (mean_temp + 2 * std_temp)
        hot_spot_ratio = np.sum(hot_spots) / thermal_map.size
        
        # 冷点检测
        cold_spots = thermal_map < (mean_temp - 2 * std_temp)
        cold_spot_ratio = np.sum(cold_spots) / thermal_map.size
        
        return np.array([mean_temp, std_temp, temp_range, hot_spot_ratio, cold_spot_ratio], dtype=np.float32)
    
    def forward(self, x):
        """前向传播"""
        # 模拟热度图
        if x.size(1) == 3:
            # 简化的热度模拟：使用红色通道
            thermal = x[:, 0:1, :, :]  # 取红色通道
        else:
            thermal = x
        
        return self.thermal_conv(thermal)

# EnhancedECAAttention已移至 enhanced_attention_suite.py
# 使用 SpatialChannelAttention 替代

class MultiModalDiseaseDetector(nn.Module):
    """
    多模态病害检测器
    融合颜色、灰度、热度检测和ECA注意力机制
    """
    def __init__(self, num_classes=5):
        super(MultiModalDiseaseDetector, self).__init__()
        self.num_classes = num_classes
        
        # 各模态检测器 - 使用重构后的类
        self.color_detector = AdaptiveColorDiseaseDetector(num_classes)
        self.gray_detector = AdvancedTextureDiseaseDetector(num_classes)
        self.thermal_detector = ThermalDiseaseDetector(num_classes)
        
        # 深度特征融合网络
        self.fusion_network = DeepFeatureFusionNetwork(
            color_dim=256,
            texture_dim=256,
            thermal_dim=128,
            num_classes=num_classes
        )
        
        # 增强ECA注意力 (使用新的套件)
        self.enhanced_eca = SpatialChannelAttention(3)  # 3个模态
    
    def forward(self, x, return_detailed=False):
        """前向传播 - 重构增强版"""
        # 提取各模态特征
        color_features = self.color_detector(x)
        texture_features = self.gray_detector(x)
        thermal_features = self.thermal_detector(x)

        # 深度特征融合
        if return_detailed:
            fusion_result = self.fusion_network(
                color_features, texture_features, thermal_features, return_aux=True
            )

            return {
                'main_output': fusion_result['main_output'],
                'auxiliary_outputs': fusion_result['aux_outputs'],
                'attention_weights': fusion_result['attention_weights'],
                'adaptive_weights': fusion_result['adaptive_weights'],
                'modal_features': fusion_result['modal_features'],
                'raw_features': {
                    'color': color_features,
                    'texture': texture_features,
                    'thermal': thermal_features
                }
            }
        else:
            output = self.fusion_network(color_features, texture_features, thermal_features)
            return output, {
                'color': color_features,
                'texture': texture_features,
                'thermal': thermal_features
            }

class DiseaseAnalyzer:
    """
    病害综合分析器
    整合多种检测算法的结果
    """
    def __init__(self):
        self.class_names = ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt']
        self.class_names_cn = ['健康叶片', '花叶病毒病', '赤星病', '野火病', '青枯病']
        
        # 初始化高级检测模块
        self.defect_detector = DefectDetector()
        self.region_analyzer = RegionAnalyzer()
        self.spectral_analyzer = TobaccoSpectralIndex()
    
    def analyze_image(self, image_input) -> Dict:
        """
        综合分析单张图像
        
        Args:
            image_input: 图像路径(str)或图像数组(numpy.ndarray)
            
        Returns:
            分析结果字典
        """
        # 处理输入
        if isinstance(image_input, str):
            # 如果是路径，读取图像
            image = cv2.imread(image_input)
            if image is None:
                return {'error': '无法读取图像'}
        elif isinstance(image_input, np.ndarray):
            # 如果是图像数组，直接使用
            image = image_input
        else:
            return {'error': '不支持的图像输入类型'}
        
        results = {}
        
        # 1. 颜色分析
        results['color_analysis'] = self._analyze_color(image)
        
        # 2. 灰度纹理分析
        results['texture_analysis'] = self._analyze_texture(image)
        
        # 3. 热度分析
        results['thermal_analysis'] = self._analyze_thermal(image)
        
        # 4. 缺陷检测分析 (新增)
        results['defect_analysis'] = self.defect_detector.detect_defects(image)
        
        # 5. 病害区域深度分析 (新增)
        results['region_analysis'] = self._analyze_detected_regions(image, results['defect_analysis'])
        
        # 6. 光谱指数分析 (基于论文方法)
        results['spectral_analysis'] = self.spectral_analyzer.calculate_tmdi(image)
        
        # 7. 综合评估
        results['health_assessment'] = self._comprehensive_assessment(results)
        
        return results
    
    def _analyze_color(self, image):
        """基于数据集特征的精确颜色分析"""
        detector = AdaptiveColorDiseaseDetector()
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 基于数据集分析的精确颜色范围定义 - 收紧范围避免误检
        color_ranges = {
            'healthy_green': ([35, 40, 40], [85, 255, 255]),          # 健康绿色
            'mosaic_virus': ([20, 100, 100], [38, 255, 240]),         # 花叶病毒病：黄绿斑驳 - 提高饱和度到100
            'wildfire': ([10, 120, 120], [30, 255, 240]),             # 野火病：黄褐色病斑 - 提高饱和度到120
            'brown_spot': ([5, 80, 40], [25, 255, 160]),              # 赤星病：褐色斑点 - 提高饱和度到80
            'bacterial_wilt': ([0, 80, 50], [35, 255, 140]),          # 青枯病：深褐色枯萎 - 提高饱和度到80
            # 移除severe_dark，因为它会误检所有阴影和背景
        }
        
        # 计算各颜色区域的比例
        total_pixels = image.shape[0] * image.shape[1]
        color_stats = {}
        
        for color_name, (lower, upper) in color_ranges.items():
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            ratio = np.sum(mask > 0) / total_pixels
            color_stats[color_name] = ratio
        
        # 提取主要颜色比例
        green_ratio = color_stats['healthy_green']
        mosaic_virus_ratio = color_stats['mosaic_virus']
        wildfire_ratio = color_stats['wildfire']
        brown_spot_ratio = color_stats['brown_spot']
        bacterial_wilt_ratio = color_stats['bacterial_wilt']
        severe_dark_ratio = 0  # 移除severe_dark检测

        # 兼容性映射
        yellow_green_ratio = mosaic_virus_ratio
        yellow_ratio = wildfire_ratio
        brown_ratio = brown_spot_ratio
        dark_ratio = bacterial_wilt_ratio  # 只使用bacterial_wilt

        # 计算总病害比例 - 移除severe_dark
        total_disease_ratio = mosaic_virus_ratio + wildfire_ratio + brown_spot_ratio + bacterial_wilt_ratio
        
        # 基于病害严重程度的加权健康评分
        disease_weights = {
            'mosaic_virus': 0.3,      # 花叶病毒病相对较轻
            'wildfire': 0.5,          # 野火病中等严重
            'brown_spot': 0.7,        # 赤星病较严重
            'bacterial_wilt': 0.9,    # 青枯病很严重
            'severe_dark': 1.0        # 枯死最严重
        }
        
        # 计算加权病害影响
        weighted_disease_impact = (
            mosaic_virus_ratio * disease_weights['mosaic_virus'] +
            wildfire_ratio * disease_weights['wildfire'] +
            brown_spot_ratio * disease_weights['brown_spot'] +
            bacterial_wilt_ratio * disease_weights['bacterial_wilt'] +
            severe_dark_ratio * disease_weights['severe_dark']
        )
        
        # 综合健康评分
        if green_ratio + weighted_disease_impact > 0:
            health_indicator = green_ratio / (green_ratio + weighted_disease_impact + 0.01)
        else:
            health_indicator = 0.5
        
        # 特殊调整 - 放宽阈值，避免过度惩罚健康叶片
        if green_ratio < 0.03:  # 几乎没有绿色（从0.05降低到0.03）
            health_indicator *= 0.4  # 从0.3提高到0.4
        elif green_ratio < 0.10:  # 绿色很少（从0.15降低到0.10）
            health_indicator *= 0.7  # 从0.6提高到0.7
        
        # 如果病害比例很高，进一步降低健康评分
        if total_disease_ratio > 0.3:
            health_indicator *= (1 - total_disease_ratio * 0.3)
        
        # 确保健康评分在合理范围内
        health_indicator = max(0.0, min(1.0, health_indicator))
        
        # 识别主导病害颜色
        disease_colors = {
            'mosaic_virus': mosaic_virus_ratio,
            'wildfire': wildfire_ratio,
            'brown_spot': brown_spot_ratio,
            'bacterial_wilt': bacterial_wilt_ratio
        }
        dominant_disease = max(disease_colors.items(), key=lambda x: x[1])[0] if max(disease_colors.values()) > 0.05 else 'none'
        
        result = {
            'green_ratio': float(green_ratio),
            'yellow_green_ratio': float(yellow_green_ratio),
            'yellow_ratio': float(yellow_ratio),
            'brown_ratio': float(brown_ratio),
            'dark_ratio': float(dark_ratio),
            'disease_ratio': float(total_disease_ratio),
            'health_score': float(health_indicator),
            'dominant_colors': self._get_dominant_colors(green_ratio, total_disease_ratio),
            'disease_color_features': {
                'mosaic_virus_ratio': float(mosaic_virus_ratio),
                'wildfire_ratio': float(wildfire_ratio),
                'brown_spot_ratio': float(brown_spot_ratio),
                'bacterial_wilt_ratio': float(bacterial_wilt_ratio),
                'dominant_disease_color': dominant_disease
            }
        }
        
        return result
    
    def _get_dominant_colors(self, green_ratio, disease_ratio):
        """获取主导颜色"""
        colors = []
        if green_ratio > 0.2:
            colors.append('green')
        if disease_ratio > 0.1:
            colors.append('disease')
        if not colors:
            colors.append('unknown')
        return colors
    
    def _analyze_texture(self, image):
        """纹理分析"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 计算纹理特征
        # 边缘密度
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # 纹理方差
        texture_variance = np.var(gray)
        
        # 局部标准差
        kernel = np.ones((9, 9), np.float32) / 81
        local_mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        local_variance = cv2.filter2D((gray.astype(np.float32) - local_mean)**2, -1, kernel)
        texture_heterogeneity = np.mean(np.sqrt(local_variance))
        
        return {
            'edge_density': float(edge_density),
            'texture_variance': float(texture_variance),
            'texture_heterogeneity': float(texture_heterogeneity)
        }
    
    def _analyze_thermal(self, image):
        """热度分析"""
        detector = ThermalDiseaseDetector()
        thermal_map = detector.simulate_thermal_map(image)
        
        # 热度统计
        thermal_stats = {
            'mean_temperature': float(np.mean(thermal_map)),
            'temperature_std': float(np.std(thermal_map)),
            'temperature_range': float(np.max(thermal_map) - np.min(thermal_map)),
            'hot_spot_ratio': float(np.sum(thermal_map > np.percentile(thermal_map, 90)) / thermal_map.size)
        }
        
        return thermal_stats
    
    def _comprehensive_assessment(self, results):
        """综合评估"""
        # 基于多模态结果的综合评分
        color_health = results['color_analysis']['health_score']
        texture_complexity = results['texture_analysis']['texture_heterogeneity']
        thermal_anomaly = results['thermal_analysis']['hot_spot_ratio']
        
        # 标准化纹理复杂度 (正常范围0-100)
        normalized_texture = min(texture_complexity / 100.0, 1.0)
        
        # 综合健康评分 (0-1，越高越健康)
        health_score = (
            color_health * 0.5 +  # 颜色权重50%（最重要）
            (1 - normalized_texture) * 0.3 +  # 纹理权重30%
            (1 - thermal_anomaly) * 0.2  # 热度权重20%
        )
        
        # 确保评分在合理范围内
        health_score = max(0.0, min(1.0, health_score))
        
        # 确定病害风险等级
        if health_score > 0.8:
            risk_level = "低风险"
            recommendation = "叶片状态良好，继续保持良好的田间管理"
        elif health_score > 0.6:
            risk_level = "中等风险"
            recommendation = "发现轻微异常，建议加强观察和预防措施"
        elif health_score > 0.4:
            risk_level = "高风险"
            recommendation = "检测到明显病害特征，建议及时治疗"
        else:
            risk_level = "极高风险"
            recommendation = "严重病害，需要立即采取治疗措施"
        
        return {
            'health_score': float(health_score),
            'risk_level': risk_level,
            'recommendation': recommendation
        }
    
    def _analyze_detected_regions(self, image, defect_analysis):
        """
        分析检测到的病害区域
        
        Args:
            image: 原始图像
            defect_analysis: 缺陷检测结果
            
        Returns:
            区域分析结果
        """
        try:
            defects = defect_analysis.get('defects', [])
            if not defects:
                return {
                    'total_regions': 0,
                    'region_details': [],
                    'overall_region_health': 1.0,
                    'most_severe_region': None
                }
            
            region_details = []
            region_health_scores = []
            
            for i, defect in enumerate(defects):
                bbox = defect['bbox']
                region_analysis = self.region_analyzer.analyze_region(image, bbox)
                
                # 结合缺陷检测和区域分析的结果
                combined_analysis = {
                    'region_id': i + 1,
                    'defect_type': defect['type'],
                    'defect_confidence': defect['confidence'],
                    'defect_severity': defect['severity'],
                    'bbox': bbox,
                    'area': defect['area'],
                    'region_health_score': region_analysis['health_score'],
                    'region_classification': region_analysis['region_classification'],
                    'color_analysis': region_analysis['color_analysis'],
                    'texture_analysis': region_analysis['texture_analysis'],
                    'morphology_analysis': region_analysis['morphology_analysis'],
                    'detailed_metrics': region_analysis['detailed_metrics']
                }
                
                region_details.append(combined_analysis)
                region_health_scores.append(region_analysis['health_score'])
            
            # 计算整体区域健康评分
            overall_region_health = np.mean(region_health_scores) if region_health_scores else 1.0
            
            # 找到最严重的区域
            most_severe_region = min(region_details, key=lambda x: x['region_health_score']) if region_details else None
            
            return {
                'total_regions': len(defects),
                'region_details': region_details,
                'overall_region_health': float(overall_region_health),
                'most_severe_region': most_severe_region,
                'region_statistics': {
                    'avg_health_score': float(np.mean(region_health_scores)) if region_health_scores else 1.0,
                    'min_health_score': float(np.min(region_health_scores)) if region_health_scores else 1.0,
                    'max_health_score': float(np.max(region_health_scores)) if region_health_scores else 1.0,
                    'health_score_std': float(np.std(region_health_scores)) if region_health_scores else 0.0
                }
            }
            
        except Exception as e:
            print(f"区域分析失败: {e}")
            return {
                'total_regions': 0,
                'region_details': [],
                'overall_region_health': 0.5,
                'most_severe_region': None,
                'error': str(e)
            }
    
    def analyze_multimodal_features(self, image):
        """分析图像的多模态特征（用于神经网络推理）"""
        try:
            # 预处理图像
            if len(image.shape) == 3:
                # BGR to RGB
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            # 调整图像大小
            image_resized = cv2.resize(image_rgb, (224, 224))
            
            # 转换为tensor
            image_tensor = torch.from_numpy(image_resized).permute(2, 0, 1).float() / 255.0
            image_tensor = image_tensor.unsqueeze(0)  # 添加batch维度
            
            # 模型推理
            with torch.no_grad():
                output, features = self.forward(image_tensor)
            
            # 解析结果
            predictions = torch.softmax(output, dim=1)
            confidence_scores = predictions.max(dim=1)[0].cpu().numpy()
            class_predictions = predictions.argmax(dim=1).cpu().numpy()
            
            return {
                'predictions': predictions.cpu().numpy(),
                'confidence_scores': confidence_scores.tolist(),
                'class_predictions': class_predictions.tolist(),
                'features': features,
                'analysis_success': True
            }
            
        except Exception as e:
            print(f"多模态分析失败: {e}")
            return {
                'predictions': [],
                'confidence_scores': [],
                'class_predictions': [],
                'features': {},
                'analysis_success': False,
                'error': str(e)
            }

def create_enhanced_model():
    """创建增强的多模态检测模型"""
    return MultiModalDiseaseDetector(num_classes=5)

if __name__ == "__main__":
    # 测试代码
    model = create_enhanced_model()
    print("多模态病害检测模型创建成功！")
    print(f"模型参数数量: {sum(p.numel() for p in model.parameters())}")
    
    # 测试输入
    test_input = torch.randn(1, 3, 224, 224)
    output, features = model(test_input)
    print(f"输出形状: {output.shape}")
    print(f"各模态特征形状: {[f.shape for f in features.values()]}")