"""
精确病害区域检测器
专门用于精确定位和识别叶片上的病害区域
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple
import logging

class PreciseDiseaseDetector:
    """精确病害检测器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def detect_disease_regions(self, image: np.ndarray) -> List[Dict]:
        """
        精确检测病害区域
        
        Args:
            image: 输入图像 (BGR格式)
            
        Returns:
            List[Dict]: 病害区域列表，每个包含位置、类型、置信度等信息
        """
        disease_regions = []
        
        # 1. 预处理 - 增强病害特征
        enhanced_img = self._enhance_disease_features(image)
        
        # 2. 多色彩空间病害检测
        hsv_regions = self._detect_hsv_diseases(enhanced_img)
        lab_regions = self._detect_lab_diseases(enhanced_img)
        
        # 3. 纹理特征病害检测
        texture_regions = self._detect_texture_diseases(enhanced_img)
        
        # 4. 合并和过滤检测结果
        all_regions = hsv_regions + lab_regions + texture_regions
        filtered_regions = self._filter_and_merge_regions(all_regions, image.shape)
        
        # 5. 病害类型分类
        classified_regions = self._classify_disease_types(filtered_regions, enhanced_img)
        
        return classified_regions
    
    def _enhance_disease_features(self, image: np.ndarray) -> np.ndarray:
        """增强病害特征"""
        # 转换到HSV色彩空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 增强饱和度和明度对比
        hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], 1.3)  # 增强饱和度
        hsv[:, :, 2] = cv2.multiply(hsv[:, :, 2], 1.1)  # 轻微增强明度
        
        # 限制值范围
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 255)
        
        enhanced = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return enhanced
    
    def _detect_hsv_diseases(self, image: np.ndarray) -> List[Dict]:
        """基于HSV色彩空间检测病害 - 平衡版，准确检测病害"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        regions = []

        # 首先检测绿色健康区域，用于排除
        green_mask = cv2.inRange(hsv,
                                 np.array([35, 40, 40]),   # 绿色下限
                                 np.array([85, 255, 255])) # 绿色上限

        # 定义不同病害的HSV范围 - 平衡的阈值
        disease_ranges = {
            'brown_spot': {
                'lower': np.array([10, 60, 40]),   # 褐色病斑 - 适中的阈值
                'upper': np.array([25, 255, 200]),
                'confidence': 0.75,
                'min_area': 80  # 适中的最小面积
            },
            'yellow_spot': {
                'lower': np.array([20, 100, 100]), # 黄色病斑 - 适中的阈值
                'upper': np.array([35, 255, 255]),
                'confidence': 0.65,
                'min_area': 80
            },
            # 移除dark_spot检测，因为它会误检阴影
        }

        for disease_type, range_info in disease_ranges.items():
            mask = cv2.inRange(hsv, range_info['lower'], range_info['upper'])

            # 不排除绿色区域，因为病害可能在绿色叶片上
            # mask = cv2.bitwise_and(mask, cv2.bitwise_not(green_mask))

            # 轻度形态学操作去除噪声
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            # 找到连通区域
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)
                min_area = range_info.get('min_area', 60)  # 降低最小面积

                if area > min_area:
                    x, y, w, h = cv2.boundingRect(contour)

                    # 排除边缘区域，避免误检背景
                    img_h, img_w = image.shape[:2]
                    margin = 10  # 增加边缘距离到10像素
                    if x < margin or y < margin or x+w > img_w-margin or y+h > img_h-margin:
                        continue

                    # 计算颜色匹配度
                    roi = hsv[y:y+h, x:x+w]
                    in_range_pixels = cv2.inRange(roi, range_info['lower'], range_info['upper'])
                    color_match_ratio = np.count_nonzero(in_range_pixels) / (w * h)

                    # 只保留颜色匹配度高的区域
                    if color_match_ratio < 0.4:  # 至少40%的像素匹配
                        continue

                    # 计算置信度（基于面积和颜色匹配度）
                    area_factor = min(area / 200, 1.0)
                    confidence = range_info['confidence'] * area_factor * color_match_ratio

                    regions.append({
                        'type': disease_type,
                        'bbox': (x, y, x+w, y+h),
                        'confidence': confidence,
                        'area': area,
                        'method': 'hsv'
                    })
        
        return regions
    
    def _detect_lab_diseases(self, image: np.ndarray) -> List[Dict]:
        """基于LAB色彩空间检测病害 - 优化版，减少误检"""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        regions = []

        # LAB空间中的病害特征
        # L通道：亮度异常
        # A通道：绿-红色异常
        # B通道：蓝-黄色异常

        l_channel = lab[:, :, 0]
        a_channel = lab[:, :, 1]
        b_channel = lab[:, :, 2]

        # 更严格的阈值，避免误检阴影
        # 只检测明显的颜色异常，不检测亮度异常（避免误检阴影）
        red_mask = a_channel > 145    # 偏红区域（提高阈值）
        yellow_mask = b_channel > 145  # 偏黄区域（提高阈值）

        # 只检测同时偏红和偏黄的区域（典型病害特征）
        disease_mask = (red_mask & yellow_mask).astype(np.uint8) * 255

        # 形态学操作去除噪声
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        disease_mask = cv2.morphologyEx(disease_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        disease_mask = cv2.morphologyEx(disease_mask, cv2.MORPH_CLOSE, kernel)

        # 找到连通区域
        contours, _ = cv2.findContours(disease_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 150:  # 提高最小面积阈值
                x, y, w, h = cv2.boundingRect(contour)

                # 检查区域是否在图像边缘
                img_h, img_w = image.shape[:2]
                margin = 15
                if x < margin or y < margin or x+w > img_w-margin or y+h > img_h-margin:
                    continue  # 跳过边缘区域

                # 基于LAB特征计算置信度
                roi_a = a_channel[y:y+h, x:x+w]
                roi_b = b_channel[y:y+h, x:x+w]

                red_intensity = np.mean(roi_a[roi_a > 128]) if np.any(roi_a > 128) else 128
                yellow_intensity = np.mean(roi_b[roi_b > 128]) if np.any(roi_b > 128) else 128

                # 更严格的置信度计算
                confidence = min((red_intensity + yellow_intensity - 256) / 200, 0.85)

                # 只保留高置信度的检测，避免误检健康叶片
                if confidence > 0.5:
                    regions.append({
                        'type': 'bacterial_wilt',
                        'bbox': (x, y, x+w, y+h),
                        'confidence': confidence,
                        'area': area,
                    'method': 'lab'
                })
        
        return regions
    
    def _detect_texture_diseases(self, image: np.ndarray) -> List[Dict]:
        """基于纹理特征检测病害 - 禁用，避免过度检测"""
        # 纹理检测容易误检，暂时禁用
        # 只依赖颜色特征检测，更准确
        return []
    
    def _filter_and_merge_regions(self, regions: List[Dict], image_shape: Tuple) -> List[Dict]:
        """过滤和合并重叠的检测区域 - 平衡版"""
        if not regions:
            return []

        # 首先过滤低置信度的检测 - 提高阈值避免误检健康叶片
        high_conf_regions = [r for r in regions if r['confidence'] > 0.50]

        if not high_conf_regions:
            return []

        # 按置信度排序
        high_conf_regions.sort(key=lambda x: x['confidence'], reverse=True)

        filtered_regions = []
        for region in high_conf_regions:
            # 检查是否与已有区域重叠过多
            overlap = False
            for existing in filtered_regions:
                if self._calculate_iou(region['bbox'], existing['bbox']) > 0.5:
                    overlap = True
                    break

            if not overlap:
                filtered_regions.append(region)

        # 限制最大检测数量，避免过度检测
        max_detections = 15  # 增加到15个
        return filtered_regions[:max_detections]
    
    def _calculate_iou(self, bbox1: Tuple, bbox2: Tuple) -> float:
        """计算两个边界框的IoU"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # 计算交集
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _classify_disease_types(self, regions: List[Dict], image: np.ndarray) -> List[Dict]:
        """对检测到的区域进行病害类型分类"""
        classified_regions = []
        
        for region in regions:
            x1, y1, x2, y2 = region['bbox']
            roi = image[y1:y2, x1:x2]
            
            if roi.size == 0:
                continue
            
            # 分析ROI的颜色特征
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # 计算主要颜色
            h_mean = np.mean(hsv_roi[:, :, 0])
            s_mean = np.mean(hsv_roi[:, :, 1])
            v_mean = np.mean(hsv_roi[:, :, 2])
            
            # 基于颜色特征重新分类
            if h_mean < 20 and s_mean > 100:  # 褐色/红色
                disease_type = 'brown_spot'
                confidence_boost = 0.1
            elif 20 <= h_mean <= 35 and s_mean > 80:  # 黄色
                disease_type = 'mosaic_virus'
                confidence_boost = 0.05
            elif v_mean < 60 and s_mean > 50:  # 深色且饱和度高（避免误检阴影）
                disease_type = 'bacterial_wilt'
                confidence_boost = 0.08
            else:
                disease_type = region['type']
                confidence_boost = 0.0
            
            # 更新置信度
            new_confidence = min(region['confidence'] + confidence_boost, 0.95)
            
            classified_regions.append({
                'type': disease_type,
                'bbox': region['bbox'],
                'confidence': new_confidence,
                'area': region['area'],
                'method': region['method'],
                'color_features': {
                    'hue': h_mean,
                    'saturation': s_mean,
                    'value': v_mean
                }
            })
        
        return classified_regions
