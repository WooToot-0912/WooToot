"""
基于论文启发的烤烟病害光谱指数模块
参考: Zhang et al. (2025) Plant Methods - Apple Marssonina Blotch Index
https://plantmethods.biomedcentral.com/articles/10.1186/s13007-025-01414-4
"""

import cv2
import numpy as np
from typing import Dict, Any

class TobaccoSpectralIndex:
    """烤烟病害光谱指数计算器"""
    
    def __init__(self):
        """初始化光谱指数计算器"""
        # 基于论文的敏感波段，适配到RGB图像
        self.sensitive_bands = {
            'green_peak': 534,     # 对应G通道
            'red_edge': 690,       # 对应R通道
            'nir_equiv': 762       # 近红外等效（模拟）
        }
    
    def calculate_tmdi(self, image: np.ndarray) -> Dict[str, Any]:
        """
        计算烤烟多病害指数 (Tobacco Multi-Disease Index)
        基于AMBI原理适配RGB图像
        
        Args:
            image: BGR格式图像
            
        Returns:
            光谱指数分析结果
        """
        try:
            # 转换色彩空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            
            # 提取通道信息
            b, g, r = cv2.split(image)
            h, s, v = cv2.split(hsv)
            l, a, b_lab = cv2.split(lab)
            
            # 模拟光谱反射率（归一化到0-1）
            r_norm = r.astype(np.float32) / 255.0
            g_norm = g.astype(np.float32) / 255.0
            b_norm = b.astype(np.float32) / 255.0
            
            # 计算改进的TMDI指数
            # 基于AMBI公式：(R762nm - R534nm)/(R534nm + R690nm)
            # 适配RGB: (NIR_equiv - Green)/(Green + Red)
            nir_equiv = self._estimate_nir(r_norm, g_norm, v)
            
            # 避免除零错误
            denominator = g_norm + r_norm + 1e-7
            tmdi = (nir_equiv - g_norm) / denominator
            
            # 计算其他光谱指数
            spectral_indices = self._calculate_additional_indices(r_norm, g_norm, b_norm, tmdi)
            
            # 病害严重程度评估
            severity_assessment = self._assess_disease_severity(tmdi, spectral_indices)
            
            return {
                'tmdi_index': float(np.mean(tmdi)),
                'tmdi_std': float(np.std(tmdi)),
                'spectral_indices': spectral_indices,
                'severity_assessment': severity_assessment,
                'disease_probability': self._calculate_disease_probability(tmdi),
                'spatial_distribution': self._analyze_spatial_distribution(tmdi)
            }
            
        except Exception as e:
            print(f"TMDI计算失败: {e}")
            return self._empty_result()
    
    def _estimate_nir(self, r_norm: np.ndarray, g_norm: np.ndarray, v: np.ndarray) -> np.ndarray:
        """
        估算近红外等效值
        基于健康植被在近红外波段的高反射特性
        """
        # 健康植被在NIR波段反射率高，病害植被反射率低
        # 使用亮度和绿色通道的组合来模拟
        v_norm = v.astype(np.float32) / 255.0
        nir_equiv = (v_norm + g_norm) / 2.0 * (1.0 + g_norm - r_norm)
        return np.clip(nir_equiv, 0, 1)
    
    def _calculate_additional_indices(self, r: np.ndarray, g: np.ndarray, b: np.ndarray, 
                                    tmdi: np.ndarray) -> Dict[str, float]:
        """计算额外的光谱指数"""
        # NDVI等效 (归一化植被指数)
        nir_equiv = self._estimate_nir(r, g, (r + g + b) * 255 / 3)
        ndvi_equiv = (nir_equiv - r) / (nir_equiv + r + 1e-7)
        
        # 绿度指数
        green_index = g / (r + g + b + 1e-7)
        
        # 红边指数 (模拟)
        red_edge_index = (nir_equiv - g) / (nir_equiv + g + 1e-7)
        
        # 叶绿素指数
        chlorophyll_index = (nir_equiv - r) / (nir_equiv + r + 1e-7) * g
        
        return {
            'ndvi_equivalent': float(np.mean(ndvi_equiv)),
            'green_index': float(np.mean(green_index)),
            'red_edge_index': float(np.mean(red_edge_index)),
            'chlorophyll_index': float(np.mean(chlorophyll_index)),
            'brightness_index': float(np.mean((r + g + b) / 3))
        }
    
    def _assess_disease_severity(self, tmdi: np.ndarray, indices: Dict[str, float]) -> Dict[str, Any]:
        """基于光谱指数评估病害严重程度"""
        tmdi_mean = np.mean(tmdi)
        tmdi_std = np.std(tmdi)
        
        # 基于论文的阈值，调整适配烟草
        if tmdi_mean > 0.3:
            severity = "健康"
            risk_level = "低"
        elif tmdi_mean > 0.1:
            severity = "轻微病害"
            risk_level = "中"
        elif tmdi_mean > -0.1:
            severity = "中等病害"
            risk_level = "高"
        else:
            severity = "严重病害"
            risk_level = "极高"
        
        # 空间异质性分析
        heterogeneity = tmdi_std / (abs(tmdi_mean) + 1e-7)
        
        return {
            'severity_class': severity,
            'risk_level': risk_level,
            'confidence': float(1.0 - heterogeneity),
            'heterogeneity': float(heterogeneity),
            'recommendation': self._get_spectral_recommendation(severity, indices)
        }
    
    def _calculate_disease_probability(self, tmdi: np.ndarray) -> Dict[str, float]:
        """计算不同病害类型的概率"""
        # 基于TMDI值的分布特征
        tmdi_mean = np.mean(tmdi)
        tmdi_std = np.std(tmdi)
        
        # 不同病害在光谱上的特征差异
        probabilities = {
            'healthy': max(0, min(1, (tmdi_mean + 0.5) / 0.8)),
            'brown_spot': max(0, min(1, 0.8 - abs(tmdi_mean + 0.1) * 2)),
            'mosaic_virus': max(0, min(1, 0.6 - abs(tmdi_mean - 0.2) * 3)),
            'bacterial_wilt': max(0, min(1, 0.9 - abs(tmdi_mean + 0.3) * 2)),
            'wildfire': max(0, min(1, 0.7 - abs(tmdi_mean - 0.1) * 2.5))
        }
        
        # 归一化概率
        total_prob = sum(probabilities.values())
        if total_prob > 0:
            probabilities = {k: v/total_prob for k, v in probabilities.items()}
        
        return probabilities
    
    def _analyze_spatial_distribution(self, tmdi: np.ndarray) -> Dict[str, Any]:
        """分析病害的空间分布特征"""
        # 计算病害斑块
        disease_mask = tmdi < 0.1  # 病害阈值
        healthy_mask = tmdi > 0.2  # 健康阈值
        
        disease_ratio = np.sum(disease_mask) / tmdi.size
        healthy_ratio = np.sum(healthy_mask) / tmdi.size
        transitional_ratio = 1.0 - disease_ratio - healthy_ratio
        
        return {
            'disease_coverage': float(disease_ratio),
            'healthy_coverage': float(healthy_ratio),
            'transitional_coverage': float(transitional_ratio),
            'spatial_pattern': self._classify_spatial_pattern(disease_ratio, transitional_ratio)
        }
    
    def _classify_spatial_pattern(self, disease_ratio: float, transitional_ratio: float) -> str:
        """分类空间分布模式"""
        if disease_ratio < 0.05:
            return "点状分布"
        elif disease_ratio < 0.2 and transitional_ratio > 0.3:
            return "渐变分布" 
        elif disease_ratio > 0.5:
            return "大面积感染"
        else:
            return "斑块状分布"
    
    def _get_spectral_recommendation(self, severity: str, indices: Dict[str, float]) -> str:
        """基于光谱分析提供建议"""
        recommendations = []
        
        if severity == "健康":
            recommendations.append("光谱指标正常，继续保持良好管理")
        else:
            recommendations.append(f"检测到{severity}，建议立即采取防治措施")
            
            if indices['chlorophyll_index'] < 0.3:
                recommendations.append("叶绿素含量偏低，考虑补充氮肥")
            
            if indices['brightness_index'] < 0.4:
                recommendations.append("叶片亮度下降，注意病害发展")
        
        return "；".join(recommendations)
    
    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            'tmdi_index': 0.0,
            'tmdi_std': 0.0,
            'spectral_indices': {},
            'severity_assessment': {'severity_class': 'unknown'},
            'disease_probability': {},
            'spatial_distribution': {}
        }