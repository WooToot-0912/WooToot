"""
病害区域深度分析模块
对检测到的病害区域进行详细的颜色、纹理和形态学分析
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Any
from skimage import feature, measure, filters
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

class RegionAnalyzer:
    """病害区域深度分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.texture_window_size = 16  # 纹理分析窗口大小
        self.color_clusters = 5        # 颜色聚类数量
    
    def analyze_region(self, image: np.ndarray, bbox: List[int]) -> Dict[str, Any]:
        """
        深度分析病害区域
        
        Args:
            image: 原始图像
            bbox: 边界框 [x1, y1, x2, y2]
            
        Returns:
            详细分析结果
        """
        try:
            # 提取感兴趣区域
            x1, y1, x2, y2 = bbox
            roi = image[y1:y2, x1:x2]
            
            if roi.size == 0:
                return self._empty_analysis()
            
            # 多维度分析
            color_analysis = self._analyze_colors(roi)
            texture_analysis = self._analyze_texture(roi)
            morphology_analysis = self._analyze_morphology(roi)
            edge_analysis = self._analyze_edges(roi)
            intensity_analysis = self._analyze_intensity(roi)
            
            # 综合健康评估
            health_score = self._calculate_health_score(
                color_analysis, texture_analysis, morphology_analysis
            )
            
            return {
                'color_analysis': color_analysis,
                'texture_analysis': texture_analysis,
                'morphology_analysis': morphology_analysis,
                'edge_analysis': edge_analysis,
                'intensity_analysis': intensity_analysis,
                'health_score': health_score,
                'region_classification': self._classify_region(health_score, color_analysis),
                'detailed_metrics': self._extract_detailed_metrics(roi)
            }
            
        except Exception as e:
            print(f"区域分析失败: {e}")
            return self._empty_analysis()
    
    def _analyze_colors(self, roi: np.ndarray) -> Dict[str, Any]:
        """颜色分析"""
        # 转换色彩空间
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
        
        # HSV统计
        h_mean, h_std = cv2.meanStdDev(hsv[:,:,0])
        s_mean, s_std = cv2.meanStdDev(hsv[:,:,1])
        v_mean, v_std = cv2.meanStdDev(hsv[:,:,2])
        
        # 颜色聚类分析
        pixels = roi.reshape(-1, 3)
        if len(pixels) > self.color_clusters:
            kmeans = KMeans(n_clusters=self.color_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(pixels)
            centers = kmeans.cluster_centers_
            
            # 计算每个聚类的占比
            unique, counts = np.unique(labels, return_counts=True)
            cluster_ratios = counts / len(pixels)
            
            # 分析主导色
            dominant_colors = []
            for i, center in enumerate(centers):
                color_name = self._classify_color(center)
                dominant_colors.append({
                    'color': color_name,
                    'bgr_value': center.astype(int).tolist(),
                    'ratio': float(cluster_ratios[i])
                })
            
            # 按占比排序
            dominant_colors.sort(key=lambda x: x['ratio'], reverse=True)
        else:
            dominant_colors = []
        
        # 病害特征色彩检测
        disease_indicators = self._detect_disease_colors(hsv)
        
        return {
            'hsv_stats': {
                'hue_mean': float(h_mean[0][0]),
                'hue_std': float(h_std[0][0]),
                'saturation_mean': float(s_mean[0][0]),
                'saturation_std': float(s_std[0][0]),
                'value_mean': float(v_mean[0][0]),
                'value_std': float(v_std[0][0])
            },
            'dominant_colors': dominant_colors,
            'disease_indicators': disease_indicators,
            'color_diversity': len(dominant_colors),
            'color_uniformity': 1.0 / (1.0 + float(h_std[0][0] + s_std[0][0]))
        }
    
    def _analyze_texture(self, roi: np.ndarray) -> Dict[str, Any]:
        """纹理分析"""
        # 转换为灰度图
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # LBP (Local Binary Patterns) 纹理特征
        radius = 3
        n_points = 8 * radius
        lbp = feature.local_binary_pattern(gray, n_points, radius, method='uniform')
        
        # LBP直方图
        n_bins = n_points + 2
        lbp_hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins))
        lbp_hist = lbp_hist.astype(float)
        lbp_hist /= (lbp_hist.sum() + 1e-7)  # 归一化
        
        # GLCM (灰度共生矩阵) 特征
        try:
            glcm = feature.graycomatrix(gray, distances=[1], angles=[0], levels=256, symmetric=True, normed=True)
            contrast = feature.graycoprops(glcm, 'contrast')[0, 0]
            dissimilarity = feature.graycoprops(glcm, 'dissimilarity')[0, 0]
            homogeneity = feature.graycoprops(glcm, 'homogeneity')[0, 0]
            energy = feature.graycoprops(glcm, 'energy')[0, 0]
        except:
            contrast = dissimilarity = homogeneity = energy = 0.0
        
        # 梯度统计
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # 纹理复杂度指标
        texture_complexity = np.std(gradient_magnitude)
        edge_density = np.sum(gradient_magnitude > np.mean(gradient_magnitude)) / gradient_magnitude.size
        
        return {
            'lbp_features': {
                'histogram': lbp_hist.tolist(),
                'uniformity': np.sum(lbp_hist**2),
                'entropy': -np.sum(lbp_hist * np.log2(lbp_hist + 1e-7))
            },
            'glcm_features': {
                'contrast': float(contrast),
                'dissimilarity': float(dissimilarity),
                'homogeneity': float(homogeneity),
                'energy': float(energy)
            },
            'gradient_features': {
                'texture_complexity': float(texture_complexity),
                'edge_density': float(edge_density),
                'mean_gradient': float(np.mean(gradient_magnitude)),
                'std_gradient': float(np.std(gradient_magnitude))
            },
            'roughness_score': float(contrast + dissimilarity - homogeneity)
        }
    
    def _analyze_morphology(self, roi: np.ndarray) -> Dict[str, Any]:
        """形态学分析"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {
                'shape_metrics': {'area': 0, 'perimeter': 0, 'circularity': 0, 'aspect_ratio': 1},
                'irregularity_score': 0,
                'fragmentation': 0
            }
        
        # 找到最大轮廓
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 基本形状指标
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)
        
        # 外接矩形
        x, y, w, h = cv2.boundingRect(largest_contour)
        aspect_ratio = float(w) / h if h > 0 else 1
        
        # 圆形度
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        # 凸包分析
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        # 不规则性评分
        irregularity_score = 1.0 - solidity
        
        # 碎片化程度
        fragmentation = len(contours) / (area / 1000 + 1)  # 轮廓数量与面积的比值
        
        return {
            'shape_metrics': {
                'area': float(area),
                'perimeter': float(perimeter),
                'circularity': float(circularity),
                'aspect_ratio': float(aspect_ratio),
                'solidity': float(solidity)
            },
            'irregularity_score': float(irregularity_score),
            'fragmentation': float(fragmentation),
            'convex_hull_ratio': float(hull_area / area) if area > 0 else 1
        }
    
    def _analyze_edges(self, roi: np.ndarray) -> Dict[str, Any]:
        """边缘分析"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Canny边缘检测
        edges = cv2.Canny(gray, 50, 150)
        edge_count = np.sum(edges > 0)
        edge_density = edge_count / edges.size
        
        # 边缘方向统计
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        angles = np.arctan2(grad_y, grad_x)
        
        # 边缘强度
        edge_strength = np.sqrt(grad_x**2 + grad_y**2)
        mean_edge_strength = np.mean(edge_strength)
        
        return {
            'edge_density': float(edge_density),
            'edge_count': int(edge_count),
            'mean_edge_strength': float(mean_edge_strength),
            'edge_direction_variance': float(np.var(angles))
        }
    
    def _analyze_intensity(self, roi: np.ndarray) -> Dict[str, Any]:
        """强度分析"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 基本统计
        mean_intensity = np.mean(gray)
        std_intensity = np.std(gray)
        min_intensity = np.min(gray)
        max_intensity = np.max(gray)
        
        # 直方图分析
        hist, _ = np.histogram(gray, bins=256, range=(0, 256))
        hist = hist.astype(float)
        hist /= hist.sum()
        
        # 熵计算
        entropy = -np.sum(hist * np.log2(hist + 1e-7))
        
        # 对比度
        contrast_ratio = (max_intensity - min_intensity) / 255.0
        
        return {
            'mean_intensity': float(mean_intensity),
            'std_intensity': float(std_intensity),
            'intensity_range': float(max_intensity - min_intensity),
            'contrast_ratio': float(contrast_ratio),
            'entropy': float(entropy),
            'brightness_level': self._classify_brightness(mean_intensity)
        }
    
    def _classify_color(self, bgr_color: np.ndarray) -> str:
        """颜色分类"""
        b, g, r = bgr_color
        
        # 转换为HSV进行分类
        hsv_color = cv2.cvtColor(np.uint8([[bgr_color]]), cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = hsv_color
        
        # 基于HSV值分类颜色
        if v < 50:
            return 'dark'
        elif s < 30:
            return 'gray'
        elif h < 15 or h > 165:
            return 'red'
        elif h < 35:
            return 'yellow'
        elif h < 85:
            return 'green'
        elif h < 135:
            return 'blue'
        else:
            return 'purple'
    
    def _detect_disease_colors(self, hsv: np.ndarray) -> Dict[str, float]:
        """检测病害特征颜色 - 收紧范围避免误检健康叶片"""
        # 定义病害颜色范围 - 提高饱和度和亮度阈值
        disease_ranges = {
            'brown_spots': [(5, 80, 40), (25, 255, 160)],   # 褐色斑点 - 提高饱和度到80
            'yellow_areas': [(15, 100, 100), (32, 255, 240)], # 黄化区域 - 提高饱和度到100，避免匹配正常叶片
            # 移除dark_lesions，因为它会误检所有阴影和背景
            'chlorosis': [(25, 80, 120), (32, 200, 255)]    # 叶绿素缺失 - 提高饱和度到80
        }

        indicators = {}
        total_pixels = hsv.shape[0] * hsv.shape[1]

        for disease_name, (lower, upper) in disease_ranges.items():
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            ratio = np.sum(mask > 0) / total_pixels
            indicators[disease_name] = float(ratio)

        return indicators
    
    def _classify_brightness(self, mean_intensity: float) -> str:
        """亮度分类"""
        if mean_intensity < 85:
            return 'dark'
        elif mean_intensity < 170:
            return 'medium'
        else:
            return 'bright'
    
    def _calculate_health_score(self, color_analysis: Dict, texture_analysis: Dict,
                              morphology_analysis: Dict) -> float:
        """计算健康评分 - 优化公式避免过度惩罚"""
        # 颜色健康指标 (绿色比例高、病害色彩少)
        green_ratio = sum(c['ratio'] for c in color_analysis['dominant_colors']
                         if c['color'] == 'green')
        disease_color_ratio = sum(color_analysis['disease_indicators'].values())

        # 优化颜色健康计算：使用比例而非简单相减，避免过度惩罚
        if green_ratio + disease_color_ratio > 0:
            color_health = green_ratio / (green_ratio + disease_color_ratio * 1.5 + 0.1)
        else:
            color_health = 0.5  # 默认中等健康

        # 纹理健康指标 (均匀度高、粗糙度低)
        texture_uniformity = texture_analysis['glcm_features']['homogeneity']
        texture_health = texture_uniformity

        # 形态健康指标 (规则度高、碎片化低)
        shape_regularity = 1.0 - morphology_analysis['irregularity_score']
        fragmentation_penalty = min(morphology_analysis['fragmentation'] / 10, 0.5)
        morphology_health = max(0, shape_regularity - fragmentation_penalty)

        # 综合健康评分
        health_score = (color_health * 0.4 + texture_health * 0.3 + morphology_health * 0.3)
        return float(np.clip(health_score, 0, 1))
    
    def _classify_region(self, health_score: float, color_analysis: Dict) -> str:
        """区域分类"""
        disease_ratio = sum(color_analysis['disease_indicators'].values())
        
        if health_score > 0.8 and disease_ratio < 0.1:
            return 'healthy'
        elif health_score > 0.6:
            return 'mild_disease'
        elif health_score > 0.3:
            return 'moderate_disease'
        else:
            return 'severe_disease'
    
    def _extract_detailed_metrics(self, roi: np.ndarray) -> Dict[str, Any]:
        """提取详细指标"""
        return {
            'region_size': {
                'width': roi.shape[1],
                'height': roi.shape[0],
                'area_pixels': roi.shape[0] * roi.shape[1]
            },
            'color_channels': {
                'blue_mean': float(np.mean(roi[:,:,0])),
                'green_mean': float(np.mean(roi[:,:,1])),
                'red_mean': float(np.mean(roi[:,:,2]))
            }
        }
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """返回空分析结果"""
        return {
            'color_analysis': {'dominant_colors': [], 'disease_indicators': {}},
            'texture_analysis': {'glcm_features': {}, 'gradient_features': {}},
            'morphology_analysis': {'shape_metrics': {}, 'irregularity_score': 0},
            'edge_analysis': {'edge_density': 0},
            'intensity_analysis': {'mean_intensity': 0},
            'health_score': 0.5,
            'region_classification': 'unknown',
            'detailed_metrics': {}
        }