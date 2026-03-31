"""
烤烟病害缺陷检测模块
实现病害区域的自动检测、定位和分析
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Any
import json

class DefectDetector:
    """病害缺陷检测器"""
    
    def __init__(self):
        """初始化检测器"""
        self.min_defect_area = 300  # 提高最小病害区域面积到300，减少误检
        self.max_defect_area = 50000  # 最大病害区域面积

        # 病害颜色范围定义 (HSV) - 放宽范围以召回病斑，阴影已由预处理模块去除
        self.disease_color_ranges = {
            'brown_spot': {  # 褐斑病 - 褐色斑点 (放宽S和V)
                'lower': np.array([5, 40, 30]),   
                'upper': np.array([25, 255, 200])
            },
            'mosaic_virus': {  # 花叶病毒病 - 黄绿色斑驳
                'lower': np.array([15, 40, 60]),  
                'upper': np.array([45, 255, 255])
            },
            'wildfire': {  # 野火病 - 黄色至褐色病斑，边缘明显
                'lower': np.array([10, 80, 80]),
                'upper': np.array([32, 255, 255])
            },
            'bacterial_wilt': {  # 青枯病 - 枯萎黄褐色至黑褐色
                'lower': np.array([0, 40, 30]),   
                'upper': np.array([35, 255, 160])
            },
            'dark_spot': { # 黑斑病 / 深色病斑（恢复检测）
                'lower': np.array([0, 10, 10]),
                'upper': np.array([180, 100, 80])
            }
        }
    
    def detect_defects(self, image: np.ndarray) -> Dict[str, Any]:
        """
        检测图像中的病害缺陷区域
        
        Args:
            image: 输入图像 (BGR格式)
            
        Returns:
            检测结果字典，包含病害区域信息
        """
        try:
            # 图像预处理
            processed_img = self._preprocess_image(image)
            
            # 检测所有病害类型
            all_defects = []
            disease_masks = {}
            
            for disease_name, color_range in self.disease_color_ranges.items():
                defects, mask = self._detect_disease_regions(
                    processed_img, color_range, disease_name
                )
                all_defects.extend(defects)
                disease_masks[disease_name] = mask
            
            # 合并相近的病害区域
            merged_defects = self._merge_nearby_defects(all_defects)
            
            # 分析病害严重程度
            severity_analysis = self._analyze_severity(image, merged_defects)
            
            # 生成可视化图像
            visualization = self._create_visualization(image.copy(), merged_defects)
            
            return {
                'defects': merged_defects,
                'total_defects': len(merged_defects),
                'severity_analysis': severity_analysis,
                'disease_masks': disease_masks,
                'visualization': visualization,
                'image_analysis': {
                    'total_area': image.shape[0] * image.shape[1],
                    'defect_coverage': severity_analysis['defect_coverage_percent']
                }
            }
            
        except Exception as e:
            print(f"病害检测失败: {e}")
            return {
                'defects': [],
                'total_defects': 0,
                'severity_analysis': {'severity': 'unknown', 'defect_coverage_percent': 0},
                'disease_masks': {},
                'visualization': image.copy(),
                'image_analysis': {'total_area': 0, 'defect_coverage_percent': 0}
            }
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """图像预处理"""
        # 转换到HSV色彩空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 高斯模糊去噪
        blurred = cv2.GaussianBlur(hsv, (5, 5), 0)
        
        # 增强对比度
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        enhanced_hsv = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2HSV)
        
        return enhanced_hsv
    
    def _detect_disease_regions(self, hsv_image: np.ndarray, color_range: Dict,
                               disease_name: str) -> Tuple[List[Dict], np.ndarray]:
        """检测特定疾病的区域 - 优化版，减少误检"""
        # 创建颜色掩码
        mask = cv2.inRange(hsv_image, color_range['lower'], color_range['upper'])

        # 轻度形态学操作去除噪声，避免过度侵蚀
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        defects = []
        for contour in contours:
            area = cv2.contourArea(contour)

            # 过滤太小或太大的区域
            if self.min_defect_area <= area <= self.max_defect_area:
                # 计算边界框
                x, y, w, h = cv2.boundingRect(contour)

                # 检查是否在图像边缘（可能是背景）
                img_h, img_w = hsv_image.shape[:2]
                margin = 5
                if x < margin or y < margin or x+w > img_w-margin or y+h > img_h-margin:
                    continue  # 跳过边缘区域

                # 计算形状特征
                perimeter = cv2.arcLength(contour, True)
                circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0

                # 计算病害置信度
                confidence = self._calculate_defect_confidence(
                    hsv_image[y:y+h, x:x+w], color_range, area, circularity
                )

                # 只保留合理置信度的检测 - 由于预处理已非常干净，我们降低置信度阈值至0.20即可认为疑似病害
                if confidence < 0.20:
                    continue

                defect_info = {
                    'type': disease_name,
                    'bbox': [x, y, x+w, y+h],
                    'center': [x + w//2, y + h//2],
                    'area': area,
                    'confidence': confidence,
                    'circularity': circularity,
                    'severity': self._classify_severity(area, confidence)
                }

                defects.append(defect_info)
        
        return defects, mask
    
    def _calculate_defect_confidence(self, region_hsv: np.ndarray, color_range: Dict,
                                   area: float, circularity: float) -> float:
        """计算病害区域的置信度 - 更严格的评估"""
        if region_hsv.size == 0:
            return 0.0

        # 颜色匹配度 - 要求更高的匹配比例
        mask = cv2.inRange(region_hsv, color_range['lower'], color_range['upper'])
        color_match_ratio = np.sum(mask > 0) / mask.size

        # 如果颜色匹配度太低，直接返回低置信度
        if color_match_ratio < 0.2:
            return 0.0

        # 面积因子 (中等大小的区域置信度更高)
        ideal_area = 800
        area_factor = min(area / ideal_area, ideal_area / area) if area > 0 else 0
        area_factor = min(area_factor, 1.0)

        # 形状因子 (圆形度适中的区域置信度更高)
        shape_factor = 1.0 - abs(circularity - 0.6)  # 0.6是经验值
        shape_factor = max(shape_factor, 0.1)

        # 综合置信度 - 提高颜色匹配的权重
        confidence = (color_match_ratio * 0.7 + area_factor * 0.15 + shape_factor * 0.15)
        return min(max(confidence, 0.0), 1.0)
    
    def _classify_severity(self, area: float, confidence: float) -> str:
        """根据面积和置信度分类病害严重程度"""
        severity_score = (area / 1000) * confidence
        
        if severity_score > 5:
            return '严重'
        elif severity_score > 2:
            return '中等'
        elif severity_score > 0.5:
            return '轻微'
        else:
            return '疑似'
    
    def _merge_nearby_defects(self, defects: List[Dict]) -> List[Dict]:
        """合并相近的病害区域"""
        if len(defects) <= 1:
            return defects
        
        merged = []
        used_indices = set()
        
        for i, defect1 in enumerate(defects):
            if i in used_indices:
                continue
                
            group = [defect1]
            used_indices.add(i)
            
            for j, defect2 in enumerate(defects[i+1:], i+1):
                if j in used_indices:
                    continue
                
                # 计算两个区域的距离
                dist = np.sqrt(
                    (defect1['center'][0] - defect2['center'][0]) ** 2 +
                    (defect1['center'][1] - defect2['center'][1]) ** 2
                )
                
                # 如果距离足够近且类型相同，则合并
                if dist < 50 and defect1['type'] == defect2['type']:
                    group.append(defect2)
                    used_indices.add(j)
            
            # 合并组内的缺陷
            if len(group) == 1:
                merged.append(group[0])
            else:
                merged_defect = self._merge_defect_group(group)
                merged.append(merged_defect)
        
        return merged
    
    def _merge_defect_group(self, group: List[Dict]) -> Dict:
        """合并一组病害区域"""
        # 计算合并后的边界框
        min_x = min(d['bbox'][0] for d in group)
        min_y = min(d['bbox'][1] for d in group)
        max_x = max(d['bbox'][2] for d in group)
        max_y = max(d['bbox'][3] for d in group)
        
        # 计算合并后的属性
        total_area = sum(d['area'] for d in group)
        avg_confidence = np.mean([d['confidence'] for d in group])
        
        # 选择置信度最高的类型
        best_type = max(group, key=lambda x: x['confidence'])['type']
        
        return {
            'type': best_type,
            'bbox': [min_x, min_y, max_x, max_y],
            'center': [(min_x + max_x) // 2, (min_y + max_y) // 2],
            'area': total_area,
            'confidence': avg_confidence,
            'circularity': np.mean([d['circularity'] for d in group]),
            'severity': self._classify_severity(total_area, avg_confidence),
            'merged_count': len(group)
        }
    
    def _analyze_severity(self, image: np.ndarray, defects: List[Dict]) -> Dict:
        """分析整体病害严重程度"""
        total_image_area = image.shape[0] * image.shape[1]
        total_defect_area = sum(d['area'] for d in defects)
        defect_coverage = (total_defect_area / total_image_area) * 100
        
        # 按类型统计
        type_stats = {}
        for defect in defects:
            dtype = defect['type']
            if dtype not in type_stats:
                type_stats[dtype] = {'count': 0, 'total_area': 0, 'avg_confidence': 0}
            type_stats[dtype]['count'] += 1
            type_stats[dtype]['total_area'] += defect['area']
        
        # 计算平均置信度
        for dtype in type_stats:
            defects_of_type = [d for d in defects if d['type'] == dtype]
            type_stats[dtype]['avg_confidence'] = np.mean([d['confidence'] for d in defects_of_type])
        
        # 整体严重程度评估
        if defect_coverage > 15:
            overall_severity = '严重'
        elif defect_coverage > 5:
            overall_severity = '中等'
        elif defect_coverage > 1:
            overall_severity = '轻微'
        else:
            overall_severity = '健康'
        
        return {
            'severity': overall_severity,
            'defect_coverage_percent': defect_coverage,
            'total_defect_area': total_defect_area,
            'defect_count': len(defects),
            'type_statistics': type_stats,
            'recommendation': self._get_treatment_recommendation(overall_severity, type_stats)
        }
    
    def _get_treatment_recommendation(self, severity: str, type_stats: Dict) -> str:
        """根据检测结果提供治疗建议"""
        if severity == '健康':
            return "叶片健康，继续保持良好的田间管理。"
        
        recommendations = []
        
        # 根据检测到的病害类型提供针对性建议
        if 'brown_spot' in type_stats:
            recommendations.append("褐斑病：喷施75%百菌清可湿性粉剂600倍液")
        
        if 'mosaic_virus' in type_stats:
            recommendations.append("花叶病毒病：清除病株，防治传播媒介，使用抗病毒剂")
        
        if 'wildfire' in type_stats:
            recommendations.append("野火病：喷施链霉素或铜制杀菌剂，加强田间卫生")
        
        if 'bacterial_wilt' in type_stats:
            recommendations.append("青枯病：立即隔离感染植株，用硫酸铜溶液处理，改善排水")
        
        if 'dark_spot' in type_stats:
            recommendations.append("黑斑病：加强通风，降低湿度，喷施铜制杀菌剂")
        
        # 通用建议
        if severity in ['中等', '严重']:
            recommendations.append("加强田间巡查，及时清除病叶")
            recommendations.append("改善田间通风条件，避免过度密植")
        
        return "；".join(recommendations) if recommendations else "建议咨询农业专家进行详细诊断。"
    
    def _create_visualization(self, image: np.ndarray, defects: List[Dict]) -> np.ndarray:
        """创建病害区域可视化图像"""
        # 定义不同病害类型的颜色
        colors = {
            'brown_spot': (0, 165, 255),      # 橙色
            'mosaic_virus': (0, 255, 255),    # 黄色
            'wildfire': (0, 215, 255),        # 金色
            'bacterial_wilt': (0, 0, 255),    # 红色
            'dark_spot': (128, 0, 128)        # 紫色
        }
        
        for defect in defects:
            bbox = defect['bbox']
            color = colors.get(defect['type'], (0, 255, 0))  # 默认绿色
            
            # 绘制边界框
            cv2.rectangle(image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            
            # 添加标签
            label = f"{defect['type']} ({defect['confidence']:.2f})"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            
            # 绘制标签背景
            cv2.rectangle(image, 
                         (bbox[0], bbox[1] - label_size[1] - 10),
                         (bbox[0] + label_size[0], bbox[1]),
                         color, -1)
            
            # 绘制标签文字
            cv2.putText(image, label, 
                       (bbox[0], bbox[1] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # 绘制中心点
            center = defect['center']
            cv2.circle(image, tuple(center), 3, color, -1)
        
        return image