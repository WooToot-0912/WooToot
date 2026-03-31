"""
Web端检测评价指标计算模块
为烤烟病害检测结果提供多维度评价指标
"""

import numpy as np
import cv2
from typing import Dict, List, Any, Tuple
import json
from datetime import datetime

class DetectionMetricsCalculator:
    """检测结果评价指标计算器"""
    
    def __init__(self):
        self.disease_names = ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt']
        self.disease_names_cn = ['健康叶片', '花叶病毒病', '赤星病', '野火病', '青枯病']
        
        # 疾病严重程度阈值
        self.severity_thresholds = {
            'confidence': {'low': 0.3, 'medium': 0.6, 'high': 0.8},
            'coverage': {'low': 0.1, 'medium': 0.3, 'high': 0.5},
            'health_score': {'critical': 0.2, 'poor': 0.4, 'fair': 0.6, 'good': 0.8}
        }
    
    def calculate_detection_metrics(self, detections: List[Dict], 
                                  enhanced_analysis: Dict,
                                  image_info: Dict) -> Dict[str, Any]:
        """
        计算检测结果的综合评价指标
        
        Args:
            detections: YOLO检测结果列表
            enhanced_analysis: 多模态分析结果
            image_info: 图像基本信息
            
        Returns:
            包含各种评价指标的字典
        """
        metrics = {}
        
        # 1. 基础检测指标
        metrics['basic_metrics'] = self._calculate_basic_metrics(detections, image_info)
        
        # 2. 置信度分析
        metrics['confidence_analysis'] = self._analyze_confidence(detections)
        
        # 3. 覆盖率分析
        metrics['coverage_analysis'] = self._analyze_coverage(detections, enhanced_analysis, image_info)
        
        # 4. 健康评估指标
        metrics['health_assessment'] = self._calculate_health_metrics(enhanced_analysis)
        
        # 5. 病害严重程度评估
        metrics['severity_assessment'] = self._assess_disease_severity(detections, enhanced_analysis)
        
        # 6. 检测质量评分
        metrics['quality_score'] = self._calculate_quality_score(metrics)
        
        # 7. 可信度评估
        metrics['reliability_score'] = self._calculate_reliability_score(detections, enhanced_analysis)
        
        # 8. 检测建议
        metrics['recommendations'] = self._generate_recommendations(metrics, detections)
        
        # 9. 统计摘要
        metrics['summary'] = self._generate_summary(metrics, detections)
        
        # 10. 时间戳
        metrics['timestamp'] = datetime.now().isoformat()
        
        return metrics
    
    def _calculate_basic_metrics(self, detections: List[Dict], image_info: Dict) -> Dict:
        """计算基础检测指标"""
        total_detections = len(detections)
        image_area = image_info.get('width', 640) * image_info.get('height', 640)
        
        # 统计各类疾病检测数量 - 修复字段名匹配
        disease_counts = {name: 0 for name in self.disease_names}
        for detection in detections:
            # 兼容两种字段名：'class' 和 'class_name'
            class_name = detection.get('class_name', detection.get('class', 'unknown'))
            if class_name in disease_counts:
                disease_counts[class_name] += 1
        
        # 计算检测密度
        detection_density = total_detections / (image_area / (640 * 640))  # 标准化到640x640
        
        # 基于置信度的主要病害逻辑
        disease_confidences = {}  # 记录每种病害的总置信度
        healthy_confidence = 0
        
        for detection in detections:
            # 兼容两种字段名：'class' 和 'class_name'
            class_name = detection.get('class_name', detection.get('class', 'unknown'))
            confidence = float(detection.get('confidence', 0.0))
            
            if class_name == 'healthy':
                healthy_confidence += confidence
            elif class_name in self.disease_names:
                if class_name not in disease_confidences:
                    disease_confidences[class_name] = 0
                disease_confidences[class_name] += confidence
        
        # 智能健康叶片判断 - 基于您的要求
        total_disease_confidence = sum(disease_confidences.values())
        disease_detections = {k: v for k, v in disease_counts.items() if k != 'healthy' and v > 0}
        total_disease_count = sum(disease_detections.values())
        healthy_count = disease_counts.get('healthy', 0)
        
        # 检查是否有明显的病害检测
        significant_disease = False
        for disease, conf in disease_confidences.items():
            if conf > 0.3:  # 置信度>0.3认为是明显病害
                significant_disease = True
                break
        
        # 检查检测面积是否明显
        significant_area = False
        for detection in detections:
            if detection.get('class_name', '') != 'healthy':
                area_ratio = detection.get('area_ratio', 0)
                if area_ratio > 0.05:  # 检测面积>5%认为是明显病害
                    significant_area = True
                    break
        
        # 健康叶片判断逻辑
        if not significant_disease and not significant_area:
            # 没有明显病害，判定为健康叶片
            dominant_disease = 'healthy'
            has_disease = False
        elif total_disease_count > 0:
            # 有病害检测，找出置信度最高的病害类型
            if disease_confidences:
                dominant_disease = max(disease_confidences.items(), key=lambda x: x[1])[0]
                has_disease = True
            else:
                dominant_disease = 'none'
                has_disease = False
        else:
            # 无检测
            dominant_disease = 'none'
            has_disease = False
        
        return {
            'total_detections': total_detections,
            'disease_distribution': disease_counts,
            'detection_density': round(detection_density, 3),
            'has_disease': has_disease,
            'dominant_disease': dominant_disease,
            'healthy_count': healthy_count,
            'disease_count': total_disease_count
        }
    
    def _analyze_confidence(self, detections: List[Dict]) -> Dict:
        """分析检测置信度"""
        if not detections:
            return {
                'average_confidence': 0.0,
                'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
                'min_confidence': 0.0,
                'max_confidence': 0.0,
                'confidence_std': 0.0
            }
        
        confidences = [float(det.get('confidence', 0)) for det in detections]
        
        # 置信度分布统计
        high_conf = sum(1 for c in confidences if c >= self.severity_thresholds['confidence']['high'])
        medium_conf = sum(1 for c in confidences if self.severity_thresholds['confidence']['medium'] <= c < self.severity_thresholds['confidence']['high'])
        low_conf = sum(1 for c in confidences if c < self.severity_thresholds['confidence']['medium'])
        
        return {
            'average_confidence': round(np.mean(confidences), 3),
            'confidence_distribution': {
                'high': high_conf,
                'medium': medium_conf, 
                'low': low_conf
            },
            'min_confidence': round(min(confidences), 3),
            'max_confidence': round(max(confidences), 3),
            'confidence_std': round(np.std(confidences), 3),
            'confidence_range': round(max(confidences) - min(confidences), 3)
        }
    
    def _analyze_coverage(self, detections: List[Dict], enhanced_analysis: Dict, image_info: Dict) -> Dict:
        """分析病害覆盖率 - 基于实际病害区域计算"""
        image_area = image_info.get('width', 640) * image_info.get('height', 640)
        
        # 计算真实的病害区域覆盖率
        disease_detection_area = 0
        healthy_detection_area = 0
        total_disease_bbox_area = 0
        
        # 统计YOLO检测的病害区域
        disease_types = []
        for detection in detections:
            bbox = detection.get('bbox', [0, 0, 0, 0])
            # 兼容两种字段名：'class' 和 'class_name'
            class_name = detection.get('class_name', detection.get('class', 'unknown'))
            confidence = detection.get('confidence', 0)
            
            if len(bbox) >= 4:
                # 计算检测框面积
                bbox_area = abs((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]))
                
                if class_name == 'healthy':
                    healthy_detection_area += bbox_area
                else:
                    # 只统计置信度较高的病害检测
                    if confidence > 0.1:  # 置信度阈值
                        disease_detection_area += bbox_area
                        total_disease_bbox_area += bbox_area
                        disease_types.append(class_name)
        
        # 基于检测框计算的病害覆盖率
        yolo_disease_coverage = (disease_detection_area / image_area) * 100 if image_area > 0 else 0
        
        # 从缺陷检测获取更精确的病害区域覆盖率
        defect_coverage = 0
        defect_area = 0
        if enhanced_analysis and 'defect_analysis' in enhanced_analysis:
            defect_info = enhanced_analysis['defect_analysis']
            defect_coverage = defect_info.get('severity_analysis', {}).get('defect_coverage_percent', 0)
            # 获取实际缺陷像素面积
            image_analysis = defect_info.get('image_analysis', {})
            defect_area = image_analysis.get('total_area', image_area) * (defect_coverage / 100)
        
        # 使用更精确的覆盖率：优先使用缺陷检测结果，因为它基于像素级分析
        if defect_coverage > 0:
            actual_disease_coverage = defect_coverage
            disease_area = defect_area
        else:
            actual_disease_coverage = yolo_disease_coverage
            disease_area = disease_detection_area
        
        # 尝试从热力图/注意力映射获取更精确的病害覆盖率
        heatmap_coverage = self._calculate_heatmap_coverage(enhanced_analysis, image_area)
        if heatmap_coverage > 0:
            # 如果热力图覆盖率显著不同且更合理，使用热力图结果
            if abs(heatmap_coverage - actual_disease_coverage) > 5:  # 差异超过5%
                actual_disease_coverage = heatmap_coverage
                print(f"   🔥 使用热力图覆盖率: {heatmap_coverage:.1f}%")
        
        # 健康区域覆盖率
        healthy_coverage = (healthy_detection_area / image_area) * 100 if image_area > 0 else 0
        
        # 总检测覆盖率
        total_detection_coverage = actual_disease_coverage + healthy_coverage
        
        # 覆盖率等级（基于实际病害覆盖率）
        if actual_disease_coverage >= 40:
            coverage_level = 'severe'
        elif actual_disease_coverage >= 20:
            coverage_level = 'moderate' 
        elif actual_disease_coverage >= 5:
            coverage_level = 'mild'
        else:
            coverage_level = 'minimal'
        
        return {
            'disease_coverage_percent': round(actual_disease_coverage, 2),  # 使用实际病害覆盖率
            'healthy_coverage_percent': round(healthy_coverage, 2),
            'total_detection_coverage_percent': round(total_detection_coverage, 2),
            'defect_coverage_percent': round(defect_coverage, 2),
            'combined_coverage_percent': round(actual_disease_coverage, 2),  # 实际病害覆盖率
            'coverage_level': coverage_level,
            'disease_area_pixels': int(disease_area),  # 使用实际病害面积
            'healthy_area_pixels': int(healthy_detection_area),
            'total_image_area': int(image_area),
            'yolo_disease_coverage': round(yolo_disease_coverage, 2),  # YOLO检测的病害覆盖率
            'disease_types': list(set(disease_types))  # 检测到的病害类型
        }
    
    def _calculate_heatmap_coverage(self, enhanced_analysis: Dict, image_area: int) -> float:
        """基于热力图/注意力映射计算病害覆盖率"""
        try:
            # 尝试从多个数据源获取热力图信息
            heatmap_coverage = 0
            
            # 1. 从缺陷分析获取（这是最精确的像素级分析）
            if enhanced_analysis and 'defect_analysis' in enhanced_analysis:
                defect_info = enhanced_analysis['defect_analysis']
                defect_coverage = defect_info.get('severity_analysis', {}).get('defect_coverage_percent', 0)
                if defect_coverage > 0:
                    return defect_coverage
            
            # 2. 从颜色分析估算病害区域
            if enhanced_analysis and 'color_analysis' in enhanced_analysis:
                color_analysis = enhanced_analysis['color_analysis']
                disease_ratio = color_analysis.get('disease_ratio', 0)
                yellow_ratio = color_analysis.get('yellow_ratio', 0)
                brown_ratio = color_analysis.get('brown_ratio', 0)
                dark_ratio = color_analysis.get('dark_ratio', 0)
                
                # 综合病害颜色比例估算覆盖率
                estimated_disease_coverage = (disease_ratio + yellow_ratio + brown_ratio + dark_ratio) * 100
                if estimated_disease_coverage > 0:
                    heatmap_coverage = min(estimated_disease_coverage, 80)  # 限制最大值
            
            # 3. 从区域分析获取（如果可用）
            if enhanced_analysis and 'region_analysis' in enhanced_analysis:
                region_analysis = enhanced_analysis['region_analysis']
                if isinstance(region_analysis, list) and len(region_analysis) > 0:
                    # 计算所有病害区域的总覆盖率
                    total_region_coverage = 0
                    for region in region_analysis:
                        if isinstance(region, dict):
                            health_score = region.get('health_score', 1.0)
                            # 低健康评分表示病害区域
                            if health_score < 0.7:
                                region_disease_ratio = (1.0 - health_score) * 10  # 估算病害比例
                                total_region_coverage += region_disease_ratio
                    
                    if total_region_coverage > 0:
                        heatmap_coverage = max(heatmap_coverage, min(total_region_coverage, 60))
            
            return round(heatmap_coverage, 2)
            
        except Exception as e:
            print(f"⚠️ 热力图覆盖率计算失败: {e}")
            return 0
    
    def _calculate_health_metrics(self, enhanced_analysis: Dict) -> Dict:
        """计算健康评估指标"""
        if not enhanced_analysis or 'health_assessment' not in enhanced_analysis:
            return {
                'overall_health_score': 0.5,
                'health_level': 'unknown',
                'color_health': 0.5,
                'texture_health': 0.5,
                'thermal_health': 0.5
            }
        
        health_data = enhanced_analysis['health_assessment']
        overall_score = health_data.get('health_score', 0.5)
        
        # 健康等级判定
        if overall_score >= self.severity_thresholds['health_score']['good']:
            health_level = 'excellent'
        elif overall_score >= self.severity_thresholds['health_score']['fair']:
            health_level = 'good'
        elif overall_score >= self.severity_thresholds['health_score']['poor']:
            health_level = 'fair'
        elif overall_score >= self.severity_thresholds['health_score']['critical']:
            health_level = 'poor'
        else:
            health_level = 'critical'
        
        # 分析各维度健康状况
        color_analysis = enhanced_analysis.get('color_analysis', {})
        texture_analysis = enhanced_analysis.get('texture_analysis', {})
        thermal_analysis = enhanced_analysis.get('thermal_analysis', {})
        
        return {
            'overall_health_score': round(overall_score, 3),
            'health_level': health_level,
            'color_health': round(color_analysis.get('health_score', 0.5), 3),
            'texture_health': round(1 - texture_analysis.get('complexity', 0.5), 3),  # 纹理复杂度越低越健康
            'thermal_health': round(1 - thermal_analysis.get('anomaly_score', 0.5), 3),  # 热异常越少越健康
            'risk_level': health_data.get('risk_level', 'medium'),
            'recommendation': health_data.get('recommendation', '建议进一步观察')
        }
    
    def _assess_disease_severity(self, detections: List[Dict], enhanced_analysis: Dict) -> Dict:
        """评估病害严重程度 - 基于病害区域检测和AI深度分析结果"""
        if not detections:
            return {
                'severity_level': 'none',
                'severity_score': 0.0,
                'urgent_attention_needed': False,
                'treatment_priority': 'low'
            }
        
        # 获取AI深度分析结果
        health_score = 0.5
        risk_level = 'medium'
        if enhanced_analysis and 'health_assessment' in enhanced_analysis:
            health_score = enhanced_analysis['health_assessment'].get('health_score', 0.5)
            risk_level = enhanced_analysis['health_assessment'].get('risk_level', 'medium')
        
        # 获取病害区域检测结果
        defect_analysis = enhanced_analysis.get('defect_analysis', {}) if enhanced_analysis else {}
        defect_count = defect_analysis.get('total_defects', 0)
        defect_coverage = defect_analysis.get('severity_analysis', {}).get('defect_coverage_percent', 0)
        
        # 获取颜色分析结果
        color_analysis = enhanced_analysis.get('color_analysis', {}) if enhanced_analysis else {}
        disease_ratio = color_analysis.get('disease_ratio', 0)
        health_ratio = color_analysis.get('health_ratio', 0)
        
        print(f"   🔍 病害区域检测: {defect_count}个区域, 覆盖率{defect_coverage:.1f}%")
        print(f"   🧠 AI健康评分: {health_score:.3f}, 风险等级: {risk_level}")
        print(f"   🎨 颜色分析: 病害比例{disease_ratio:.1f}%, 健康比例{health_ratio:.1f}%")
        
        # 综合判断是否为健康叶片
        is_healthy = False
        if health_score > 0.7 and defect_count == 0 and defect_coverage < 5:
            is_healthy = True
            print(f"   ✅ 判定为健康叶片: AI评分{health_score:.3f}>0.7, 无病害区域, 覆盖率{defect_coverage:.1f}%<5%")
        
        if is_healthy:
            return {
                'severity_level': 'healthy',
                'severity_score': 0.0,
                'urgent_attention_needed': False,
                'treatment_priority': 'none',
                'dominant_disease': 'healthy',
                'disease_severity_factor': 0.0,
                'coverage_factor': 0.0,
                'count_factor': 0.0,
                'confidence_factor': health_score
            }
        
        # 基于病害区域检测和AI深度分析的综合评估
        detection_count = len(detections)
        avg_confidence = np.mean([float(det.get('confidence', 0)) for det in detections])
        
        # 优先使用病害区域检测的覆盖率
        if defect_coverage > 0:
            coverage_percent = defect_coverage
            print(f"   📊 使用病害区域检测覆盖率: {coverage_percent:.1f}%")
        else:
            coverage_info = self._analyze_coverage(detections, enhanced_analysis, {'width': 640, 'height': 640})
            coverage_percent = coverage_info['combined_coverage_percent']
            print(f"   📊 使用YOLO检测覆盖率: {coverage_percent:.1f}%")
        
        # 基于AI深度分析确定主要病害类型
        dominant_disease = 'none'
        disease_severity_weights = {
            'bacterial_wilt': 0.9,    # 青枯病 - 严重
            'wildfire': 0.8,          # 野火病 - 严重
            'mosaic_virus': 0.7,      # 花叶病毒病 - 中等偏重
            'brown_spot': 0.6,        # 赤星病 - 中等
            'dark_spot': 0.5,         # 黑斑病 - 中等偏轻
            'healthy': 0.0            # 健康 - 无病害
        }
        
        # 1. 优先使用病害区域检测结果确定病害类型
        if defect_count > 0:
            # 从病害区域检测中推断主要病害类型
            # 基于AI深度分析的颜色特征和健康评分进行推断
            if health_score < 0.3:  # 健康评分很低，说明病害严重
                if disease_ratio > 0.8:  # 病害颜色比例很高
                    # 青枯病特征：健康评分极低，病害比例很高，颜色偏黑褐色
                    dominant_disease = 'bacterial_wilt'
                    print(f"   🔍 基于AI分析推断为青枯病: 健康评分{health_score:.3f}<0.3, 病害比例{disease_ratio:.1f}%>80%")
                elif disease_ratio > 0.6:
                    # 野火病特征：健康评分低，病害比例较高，颜色偏黄褐色
                    dominant_disease = 'wildfire'
                    print(f"   🔍 基于AI分析推断为野火病: 健康评分{health_score:.3f}<0.3, 病害比例{disease_ratio:.1f}%>60%")
                elif disease_ratio > 0.4:
                    # 花叶病毒病特征：健康评分低，病害比例中等，颜色偏黄绿色
                    dominant_disease = 'mosaic_virus'
                    print(f"   🔍 基于AI分析推断为花叶病毒病: 健康评分{health_score:.3f}<0.3, 病害比例{disease_ratio:.1f}%>40%")
                else:
                    # 赤星病特征：健康评分低，病害比例较低，颜色偏褐色
                    dominant_disease = 'brown_spot'
                    print(f"   🔍 基于AI分析推断为赤星病: 健康评分{health_score:.3f}<0.3, 病害比例{disease_ratio:.1f}%<40%")
            elif health_score < 0.5:  # 健康评分中等
                if disease_ratio > 0.5:
                    # 中等严重程度的病害
                    dominant_disease = 'brown_spot'
                    print(f"   🔍 基于AI分析推断为赤星病: 健康评分{health_score:.3f}<0.5, 病害比例{disease_ratio:.1f}%>50%")
                else:
                    # 轻微病害
                    dominant_disease = 'brown_spot'
                    print(f"   🔍 基于AI分析推断为赤星病: 健康评分{health_score:.3f}<0.5, 病害比例{disease_ratio:.1f}%<50%")
            else:
                # 健康评分较高，可能是轻微病害或误检
                dominant_disease = 'brown_spot'
                print(f"   🔍 基于AI分析推断为赤星病: 健康评分{health_score:.3f}≥0.5")
        
        # 2. 如果病害区域检测无法确定，使用YOLO检测结果
        if dominant_disease == 'none' and detections:
            max_disease_severity = 0.0
            for detection in detections:
                class_name = detection.get('class_name', detection.get('class', 'unknown'))
                confidence = float(detection.get('confidence', 0))
                
                if class_name in disease_severity_weights:
                    disease_severity = disease_severity_weights[class_name] * confidence
                    if disease_severity > max_disease_severity:
                        max_disease_severity = disease_severity
                        dominant_disease = class_name
            print(f"   🔍 基于YOLO检测确定病害类型: {dominant_disease}")
        
        # 3. 综合严重程度评分 - 基于多源数据
        # 病害区域检测权重更高
        defect_severity = min(defect_count / 20, 1.0)  # 20个区域为满分
        coverage_severity = min(coverage_percent / 100, 1.0)
        ai_severity = 1.0 - health_score  # AI健康评分越低，病害越严重
        risk_severity = 0.8 if risk_level == 'high' else 0.4 if risk_level == 'medium' else 0.2
        
        # 综合评分权重分配
        severity_score = (
            defect_severity * 0.3 +        # 病害区域数量权重30%
            coverage_severity * 0.25 +     # 覆盖率权重25%
            ai_severity * 0.25 +           # AI健康评分权重25%
            risk_severity * 0.2            # 风险等级权重20%
        )
        severity_score = min(severity_score, 1.0)
        
        print(f"   📊 严重程度评分: {severity_score:.3f} (区域:{defect_severity:.3f}, 覆盖:{coverage_severity:.3f}, AI:{ai_severity:.3f}, 风险:{risk_severity:.3f})")
        
        # 4. 严重程度等级判断 - 基于综合评分和病害类型
        if severity_score >= 0.8 or dominant_disease in ['bacterial_wilt', 'wildfire']:
            severity_level = 'severe'
            treatment_priority = 'urgent'
            urgent_attention = True
            print(f"   🚨 严重病害: {dominant_disease}, 评分{severity_score:.3f}≥0.8")
        elif severity_score >= 0.6 or coverage_percent > 30:
            severity_level = 'moderate'
            treatment_priority = 'high'
            urgent_attention = True
            print(f"   ⚠️ 中等病害: {dominant_disease}, 评分{severity_score:.3f}≥0.6 或 覆盖率{coverage_percent:.1f}%>30%")
        elif severity_score >= 0.3 or coverage_percent > 10:
            severity_level = 'mild'
            treatment_priority = 'medium'
            urgent_attention = False
            print(f"   ⚠️ 轻微病害: {dominant_disease}, 评分{severity_score:.3f}≥0.3 或 覆盖率{coverage_percent:.1f}%>10%")
        else:
            severity_level = 'minimal'
            treatment_priority = 'low'
            urgent_attention = False
            print(f"   ℹ️ 最小病害: {dominant_disease}, 评分{severity_score:.3f}<0.3 且 覆盖率{coverage_percent:.1f}%<10%")
        
        return {
            'severity_level': severity_level,
            'severity_score': round(severity_score, 3),
            'urgent_attention_needed': urgent_attention,
            'treatment_priority': treatment_priority,
            'dominant_disease': dominant_disease,
            'disease_severity_factor': round(defect_severity, 3),
            'coverage_factor': round(coverage_severity, 3),
            'count_factor': round(defect_severity, 3),
            'confidence_factor': round(avg_confidence, 3)
        }
    
    def _calculate_quality_score(self, metrics: Dict) -> Dict:
        """计算检测质量评分 - 基于实际检测结果而非理想状态"""
        confidence_metrics = metrics.get('confidence_analysis', {})
        coverage_metrics = metrics.get('coverage_analysis', {})
        health_metrics = metrics.get('health_assessment', {})
        basic_metrics = metrics.get('basic_metrics', {})
        
        # 质量因子 - 基于实际检测表现
        confidence_quality = confidence_metrics.get('average_confidence', 0)
        confidence_consistency = 1 - confidence_metrics.get('confidence_std', 1)  # 标准差越小质量越高
        
        # 检测准确性 - 基于检测结果的一致性
        detection_consistency = 1.0
        if basic_metrics.get('total_detections', 0) > 0:
            # 检测数量合理（1-5个检测框比较正常）
            detection_count = basic_metrics.get('total_detections', 0)
            if 1 <= detection_count <= 5:
                detection_consistency = 1.0
            elif detection_count > 10:  # 过度检测
                detection_consistency = 0.6
            else:
                detection_consistency = 0.8
        
        # 健康评估合理性 - 基于实际病害情况
        health_score = health_metrics.get('overall_health_score', 0.5)
        coverage_percent = coverage_metrics.get('combined_coverage_percent', 0)
        
        # 如果检测到病害但健康评分很高，说明检测质量有问题
        has_disease = basic_metrics.get('dominant_disease', 'none') != 'none'
        if has_disease and health_score > 0.8:
            health_consistency = 0.3  # 检测到病害但健康评分高，质量差
        elif not has_disease and health_score < 0.3:
            health_consistency = 0.3  # 没检测到病害但健康评分低，质量差
        else:
            health_consistency = 0.8  # 检测结果与健康评估一致
        
        # 综合质量评分 - 更注重实际检测准确性
        quality_score = (
            confidence_quality * 0.3 +      # 置信度权重30%
            confidence_consistency * 0.2 +   # 一致性权重20%
            detection_consistency * 0.3 +    # 检测合理性权重30%
            health_consistency * 0.2         # 健康评估一致性权重20%
        )
        
        # 质量等级 - 更严格的阈值
        if quality_score >= 0.85:
            quality_level = 'excellent'
        elif quality_score >= 0.7:
            quality_level = 'good'
        elif quality_score >= 0.5:
            quality_level = 'fair'
        else:
            quality_level = 'poor'
        
        return {
            'overall_quality_score': round(quality_score, 3),
            'quality_level': quality_level,
            'confidence_quality': round(confidence_quality, 3),
            'consistency_score': round(confidence_consistency, 3),
            'detection_consistency': round(detection_consistency, 3),
            'health_consistency': round(health_consistency, 3)
        }
    
    def _calculate_reliability_score(self, detections: List[Dict], enhanced_analysis: Dict) -> Dict:
        """计算可信度评分"""
        if not detections:
            return {
                'reliability_score': 0.5,
                'reliability_level': 'low',
                'factors': {}
            }
        
        factors = {}
        
        # 1. 检测一致性 (YOLO vs 多模态分析)
        yolo_health = 'healthy' in [det.get('class', '') for det in detections]
        enhanced_health = enhanced_analysis.get('health_assessment', {}).get('health_score', 0.5) > 0.6
        consistency_factor = 1.0 if yolo_health == enhanced_health else 0.5
        factors['yolo_enhanced_consistency'] = consistency_factor
        
        # 2. 置信度稳定性
        confidences = [float(det.get('confidence', 0)) for det in detections]
        confidence_stability = 1 - np.std(confidences) if confidences else 0.5
        factors['confidence_stability'] = confidence_stability
        
        # 3. 多模态分析支持度
        defect_count = enhanced_analysis.get('defect_analysis', {}).get('total_defects', 0)
        multimodal_support = min(defect_count / 5, 1.0) if defect_count > 0 else 0.3
        factors['multimodal_support'] = multimodal_support
        
        # 4. 光谱指数支持度 (如果有)
        spectral_support = 0.7  # 默认值
        if 'spectral_analysis' in enhanced_analysis:
            tmdi_index = enhanced_analysis['spectral_analysis'].get('tmdi_index', 0.5)
            spectral_support = abs(tmdi_index - 0.5) * 2  # 偏离0.5越远越可信
        factors['spectral_support'] = spectral_support
        
        # 综合可信度
        reliability_score = np.mean(list(factors.values()))
        
        # 可信度等级
        if reliability_score >= 0.8:
            reliability_level = 'very_high'
        elif reliability_score >= 0.6:
            reliability_level = 'high'
        elif reliability_score >= 0.4:
            reliability_level = 'medium'
        else:
            reliability_level = 'low'
        
        return {
            'reliability_score': round(reliability_score, 3),
            'reliability_level': reliability_level,
            'factors': {k: round(v, 3) for k, v in factors.items()}
        }
    
    def _generate_recommendations(self, metrics: Dict, detections: List[Dict]) -> List[Dict]:
        """生成检测建议"""
        recommendations = []
        
        severity = metrics.get('severity_assessment', {})
        quality = metrics.get('quality_score', {})
        reliability = metrics.get('reliability_score', {})
        
        # 基于严重程度的建议
        if severity.get('urgent_attention_needed', False):
            recommendations.append({
                'type': 'urgent',
                'title': '紧急处理建议',
                'message': f"检测到{severity.get('severity_level', '中等')}程度病害，建议立即采取防治措施",
                'priority': 'high'
            })
        
        # 基于检测质量的建议
        if quality.get('quality_level') == 'poor':
            recommendations.append({
                'type': 'quality',
                'title': '检测质量提升建议',
                'message': '检测质量偏低，建议重新拍摄更清晰的图像或调整光照条件',
                'priority': 'medium'
            })
        
        # 基于可信度的建议
        if reliability.get('reliability_level') == 'low':
            recommendations.append({
                'type': 'reliability',
                'title': '结果可信度提醒',
                'message': '检测结果可信度较低，建议结合专业诊断或多张图像进行综合判断',
                'priority': 'medium'
            })
        
        # 基于检测数量的建议
        detection_count = len(detections)
        if detection_count == 0:
            recommendations.append({
                'type': 'monitoring',
                'title': '继续监测建议',
                'message': '未检测到明显病害，建议定期监测叶片健康状况',
                'priority': 'low'
            })
        elif detection_count > 5:
            recommendations.append({
                'type': 'prevention',
                'title': '预防措施建议',
                'message': '检测到多处病害，建议加强田间管理和预防措施',
                'priority': 'high'
            })
        
        return recommendations
    
    def _generate_treatment_recommendation(self, detections: List[Dict], severity: Dict) -> str:
        """生成治疗建议 - 基于实际病害类型和严重程度"""
        if not detections:
            return "叶片健康，继续保持良好的田间管理。"
        
        # 检查是否为健康叶片
        severity_level = severity.get('severity_level', 'minimal')
        if severity_level == 'healthy':
            return "✅ 叶片健康！继续保持良好的田间管理，定期监测叶片状况，预防病害发生。"
        
        # 获取主要病害类型
        dominant_disease = severity.get('dominant_disease', 'none')
        severity_level = severity.get('severity_level', 'minimal')
        treatment_priority = severity.get('treatment_priority', 'low')
        
        # 病害类型对应的治疗建议
        disease_treatments = {
            'wildfire': {
                'urgent': "🚨 野火病严重感染！立即喷施72%农用链霉素4000倍液，避免暴雨后田间操作。",
                'high': "⚠️ 野火病感染！及时喷施77%可杀得可湿性粉剂1500倍液，加强田间管理。",
                'medium': "野火病初期，喷施农用链霉素预防，避免叶片湿润时操作。",
                'low': "疑似野火病症状，建议密切观察，做好预防措施。"
            },
            'bacterial_wilt': {
                'urgent': "🚨 青枯病严重感染！立即隔离病株，用硫酸铜溶液灌根处理，加强排水。",
                'high': "⚠️ 青枯病感染！及时移除病叶，用铜制剂喷洒，改善土壤排水。",
                'medium': "青枯病初期，加强田间管理，适当施用铜制剂预防。",
                'low': "疑似青枯病症状，建议密切观察，做好预防措施。"
            },
            'mosaic_virus': {
                'urgent': "🚨 花叶病毒病严重！立即清除病株，控制蚜虫传播，加强田间卫生。",
                'high': "⚠️ 花叶病毒病感染！及时清除病叶，控制传毒昆虫。",
                'medium': "花叶病毒病初期，加强病毒病防控，控制传毒媒介。",
                'low': "疑似花叶病毒症状，建议观察并做好预防。"
            },
            'brown_spot': {
                'urgent': "🚨 赤星病严重！立即喷施75%百菌清可湿性粉剂600倍液，加强通风。",
                'high': "⚠️ 赤星病感染！及时喷施杀菌剂，改善田间通风条件。",
                'medium': "赤星病初期，适当喷施保护性杀菌剂预防。",
                'low': "疑似赤星病症状，建议观察并做好预防。"
            },
            'dark_spot': {
                'urgent': "🚨 黑斑病严重！立即喷施铜制杀菌剂，加强田间管理。",
                'high': "⚠️ 黑斑病感染！及时喷施杀菌剂，降低田间湿度。",
                'medium': "黑斑病初期，加强通风，适当喷施保护性杀菌剂。",
                'low': "疑似黑斑病症状，建议观察并做好预防。"
            }
        }
        
        # 根据病害类型和严重程度选择建议
        if dominant_disease in disease_treatments:
            treatment = disease_treatments[dominant_disease].get(treatment_priority, 
                                                               disease_treatments[dominant_disease]['low'])
        else:
            # 通用建议
            if severity_level == 'severe':
                treatment = "🚨 病害严重！建议立即咨询农业专家，采取紧急防治措施。"
            elif severity_level == 'moderate':
                treatment = "⚠️ 病害中等程度，建议及时采取防治措施，加强田间管理。"
            elif severity_level == 'mild':
                treatment = "病害轻微，建议观察并做好预防措施。"
            else:
                treatment = "叶片健康，继续保持良好的田间管理。"
        
        return treatment
    
    def _generate_summary(self, metrics: Dict, detections: List[Dict]) -> Dict:
        """生成检测摘要"""
        basic = metrics.get('basic_metrics', {})
        severity = metrics.get('severity_assessment', {})
        health = metrics.get('health_assessment', {})
        quality = metrics.get('quality_score', {})
        
        # 生成治疗建议
        treatment_recommendation = self._generate_treatment_recommendation(detections, severity)
        
        return {
            'total_detections': basic.get('total_detections', 0),
            'dominant_condition': basic.get('dominant_disease', 'unknown'),
            'overall_health': health.get('health_level', 'unknown'),
            'severity_level': severity.get('severity_level', 'unknown'),
            'quality_assessment': quality.get('quality_level', 'unknown'),
            'confidence_range': f"{metrics.get('confidence_analysis', {}).get('min_confidence', 0):.2f} - {metrics.get('confidence_analysis', {}).get('max_confidence', 0):.2f}",
            'coverage_percentage': f"{metrics.get('coverage_analysis', {}).get('combined_coverage_percent', 0):.1f}%",
            'treatment_needed': severity.get('urgent_attention_needed', False),
            'treatment_recommendation': treatment_recommendation
        }


class MetricsVisualizer:
    """评价指标可视化生成器"""
    
    def __init__(self):
        self.colors = {
            'excellent': '#28a745',
            'good': '#6f42c1', 
            'fair': '#ffc107',
            'poor': '#fd7e14',
            'critical': '#dc3545'
        }
    
    def generate_metrics_html(self, metrics: Dict) -> str:
        """生成指标的HTML可视化代码"""
        html = f"""
        <div class="metrics-dashboard">
            {self._generate_score_cards(metrics)}
            {self._generate_charts_scripts(metrics)}
        </div>
        """
        return html
    
    def _generate_score_cards(self, metrics: Dict) -> str:
        """生成评分卡片"""
        quality = metrics.get('quality_score', {})
        health = metrics.get('health_assessment', {})
        reliability = metrics.get('reliability_score', {})
        
        return f"""
        <div class="score-cards">
            <div class="score-card">
                <h4>检测质量</h4>
                <div class="score">{quality.get('overall_quality_score', 0):.2f}</div>
                <div class="level {quality.get('quality_level', 'fair')}">{quality.get('quality_level', '一般')}</div>
            </div>
            <div class="score-card">
                <h4>健康状况</h4>
                <div class="score">{health.get('overall_health_score', 0):.2f}</div>
                <div class="level {health.get('health_level', 'fair')}">{health.get('health_level', '一般')}</div>
            </div>
            <div class="score-card">
                <h4>结果可信度</h4>
                <div class="score">{reliability.get('reliability_score', 0):.2f}</div>
                <div class="level {reliability.get('reliability_level', 'medium')}">{reliability.get('reliability_level', '中等')}</div>
            </div>
        </div>
        """
    
    def _generate_charts_scripts(self, metrics: Dict) -> str:
        """生成图表JavaScript代码"""
        confidence_data = metrics.get('confidence_analysis', {}).get('confidence_distribution', {})
        coverage_data = metrics.get('coverage_analysis', {})
        
        return f"""
        <script>
            // 置信度分布图表数据
            const confidenceData = {json.dumps(confidence_data)};
            
            // 覆盖率数据
            const coverageData = {json.dumps(coverage_data)};
            
            // 这里可以添加Chart.js或其他图表库的代码
        </script>
        """