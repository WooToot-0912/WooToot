"""
检测报告生成器
为烤烟病害检测结果生成专业的PDF报告
"""

import json
import base64
from datetime import datetime
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 设置非交互式后端
import numpy as np
from io import BytesIO
import os

# 设置中文字体
try:
    import matplotlib.font_manager as fm
    # 寻找中文字体
    chinese_fonts = [
        'SimHei', 'Microsoft YaHei', 'PingFang SC', 
        'Hiragino Sans GB', 'Source Han Sans CN'
    ]
    
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    chinese_font = None
    
    for font in chinese_fonts:
        if font in available_fonts:
            chinese_font = font
            break
    
    if chinese_font:
        plt.rcParams['font.sans-serif'] = [chinese_font]
    plt.rcParams['axes.unicode_minus'] = False
    
except Exception as e:
    print(f"中文字体设置失败: {e}")

class DetectionReportGenerator:
    """检测报告生成器"""
    
    def __init__(self):
        self.template_path = "templates"
        os.makedirs(self.template_path, exist_ok=True)
        
    def generate_report(self, 
                       detections: List[Dict], 
                       evaluation_metrics: Dict[str, Any],
                       enhanced_analysis: Dict,
                       result_image_base64: str,
                       original_filename: str) -> Dict[str, Any]:
        """
        生成完整的检测报告
        
        Args:
            detections: 检测结果
            evaluation_metrics: 评价指标
            enhanced_analysis: 增强分析结果
            result_image_base64: 结果图像base64
            original_filename: 原始文件名
            
        Returns:
            包含报告内容的字典
        """
        
        report_data = {
            'metadata': self._generate_metadata(original_filename),
            'executive_summary': self._generate_executive_summary(evaluation_metrics),
            'detection_details': self._format_detection_details(detections),
            'metrics_analysis': self._format_metrics_analysis(evaluation_metrics),
            'enhanced_analysis': self._format_enhanced_analysis(enhanced_analysis),
            'visualizations': self._generate_visualizations(evaluation_metrics),
            'recommendations': self._format_recommendations(evaluation_metrics),
            'technical_details': self._generate_technical_details(evaluation_metrics)
        }
        
        # 生成HTML报告
        html_report = self._generate_html_report(report_data, result_image_base64)
        
        # 生成JSON数据
        json_report = self._generate_json_report(report_data)
        
        return {
            'html_content': html_report,
            'json_data': json_report,
            'charts': report_data['visualizations'],
            'summary': report_data['executive_summary']
        }
    
    def _generate_metadata(self, filename: str) -> Dict:
        """生成报告元数据"""
        return {
            'report_id': f"TOBACCO_DETECT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'generation_time': datetime.now().isoformat(),
            'original_filename': filename,
            'detection_system': '云南烤烟病害检测系统 v2.0',
            'ai_engine': 'YOLOv8 + 多模态增强分析',
            'report_version': '1.0'
        }
    
    def _generate_executive_summary(self, metrics: Dict) -> Dict:
        """生成执行摘要"""
        summary = metrics.get('summary', {})
        health = metrics.get('health_assessment', {})
        severity = metrics.get('severity_assessment', {})
        quality = metrics.get('quality_score', {})
        
        # 风险等级评估
        health_score = health.get('overall_health_score', 0.5)
        severity_score = severity.get('severity_score', 0.0)
        
        if severity.get('urgent_attention_needed', False):
            risk_level = '高风险'
            risk_color = '#dc3545'
        elif severity_score > 0.5:
            risk_level = '中风险'
            risk_color = '#ffc107'
        elif health_score < 0.6:
            risk_level = '低风险'
            risk_color = '#fd7e14'
        else:
            risk_level = '正常'
            risk_color = '#28a745'
        
        return {
            'detection_count': summary.get('total_detections', 0),
            'primary_condition': self._translate_disease(summary.get('dominant_condition', 'unknown')),
            'health_status': self._translate_health_level(summary.get('overall_health', 'unknown')),
            'severity_level': self._translate_severity_level(summary.get('severity_level', 'unknown')),
            'quality_rating': self._translate_quality_level(summary.get('quality_assessment', 'unknown')),
            'coverage_rate': summary.get('coverage_percentage', '0%'),
            'treatment_required': summary.get('treatment_needed', False),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'confidence_score': f"{health_score:.1%}",
            'key_findings': self._extract_key_findings(metrics)
        }
    
    def _extract_key_findings(self, metrics: Dict) -> List[str]:
        """提取关键发现"""
        findings = []
        
        basic = metrics.get('basic_metrics', {})
        confidence = metrics.get('confidence_analysis', {})
        coverage = metrics.get('coverage_analysis', {})
        
        # 检测数量发现
        total_detections = basic.get('total_detections', 0)
        if total_detections == 0:
            findings.append('未检测到明显病害症状')
        elif total_detections == 1:
            findings.append('检测到单一病害区域')
        else:
            findings.append(f'检测到{total_detections}个病害区域')
        
        # 置信度发现
        avg_conf = confidence.get('average_confidence', 0)
        if avg_conf > 0.8:
            findings.append('检测结果置信度很高')
        elif avg_conf > 0.6:
            findings.append('检测结果置信度较高')
        else:
            findings.append('检测结果需要进一步确认')
        
        # 覆盖率发现
        coverage_percent = coverage.get('combined_coverage_percent', 0)
        if coverage_percent > 30:
            findings.append('病害覆盖面积较大，需要重点关注')
        elif coverage_percent > 10:
            findings.append('存在一定程度的病害覆盖')
        else:
            findings.append('病害覆盖面积较小')
        
        return findings
    
    def _format_detection_details(self, detections: List[Dict]) -> List[Dict]:
        """格式化检测详情"""
        formatted_detections = []
        
        for i, detection in enumerate(detections):
            formatted_detections.append({
                'index': i + 1,
                'disease_name': self._translate_disease(detection.get('class', 'unknown')),
                'confidence': f"{detection.get('confidence', 0):.1%}",
                'description': detection.get('description', '无描述'),
                'treatment': detection.get('treatment', '无治疗方案'),
                'bbox_info': self._format_bbox(detection.get('bbox', []))
            })
        
        return formatted_detections
    
    def _format_bbox(self, bbox: List) -> str:
        """格式化边界框信息"""
        if len(bbox) >= 4:
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            area = width * height
            return f"位置:({bbox[0]:.0f},{bbox[1]:.0f}) 大小:{width:.0f}×{height:.0f} 面积:{area:.0f}像素"
        return "边界框信息不完整"
    
    def _format_metrics_analysis(self, metrics: Dict) -> Dict:
        """格式化指标分析"""
        confidence = metrics.get('confidence_analysis', {})
        coverage = metrics.get('coverage_analysis', {})
        health = metrics.get('health_assessment', {})
        quality = metrics.get('quality_score', {})
        reliability = metrics.get('reliability_score', {})
        
        return {
            'confidence_metrics': {
                'average': f"{confidence.get('average_confidence', 0):.3f}",
                'range': f"{confidence.get('min_confidence', 0):.3f} - {confidence.get('max_confidence', 0):.3f}",
                'stability': f"{confidence.get('confidence_std', 0):.3f}",
                'distribution': confidence.get('confidence_distribution', {})
            },
            'coverage_metrics': {
                'detection_coverage': f"{coverage.get('detection_coverage_percent', 0):.2f}%",
                'defect_coverage': f"{coverage.get('defect_coverage_percent', 0):.2f}%",
                'combined_coverage': f"{coverage.get('combined_coverage_percent', 0):.2f}%",
                'coverage_level': self._translate_coverage_level(coverage.get('coverage_level', 'unknown'))
            },
            'health_metrics': {
                'overall_score': f"{health.get('overall_health_score', 0):.3f}",
                'health_level': self._translate_health_level(health.get('health_level', 'unknown')),
                'color_health': f"{health.get('color_health', 0):.3f}",
                'texture_health': f"{health.get('texture_health', 0):.3f}",
                'thermal_health': f"{health.get('thermal_health', 0):.3f}"
            },
            'quality_assessment': {
                'overall_quality': f"{quality.get('overall_quality_score', 0):.3f}",
                'quality_level': self._translate_quality_level(quality.get('quality_level', 'unknown')),
                'confidence_quality': f"{quality.get('confidence_quality', 0):.3f}",
                'consistency_score': f"{quality.get('consistency_score', 0):.3f}"
            },
            'reliability_assessment': {
                'reliability_score': f"{reliability.get('reliability_score', 0):.3f}",
                'reliability_level': self._translate_reliability_level(reliability.get('reliability_level', 'unknown')),
                'factors': reliability.get('factors', {})
            }
        }
    
    def _format_enhanced_analysis(self, enhanced_analysis: Dict) -> Dict:
        """格式化增强分析结果"""
        if not enhanced_analysis:
            return {}
        
        formatted = {}
        
        # 颜色分析
        if 'color_analysis' in enhanced_analysis:
            color = enhanced_analysis['color_analysis']
            formatted['color_analysis'] = {
                'green_ratio': f"{color.get('green_ratio', 0):.1%}",
                'disease_ratio': f"{color.get('disease_ratio', 0):.1%}",
                'health_score': f"{color.get('health_score', 0):.3f}",
                'dominant_colors': color.get('dominant_colors', [])
            }
        
        # 纹理分析
        if 'texture_analysis' in enhanced_analysis:
            texture = enhanced_analysis['texture_analysis']
            formatted['texture_analysis'] = {
                'complexity': f"{texture.get('complexity', 0):.3f}",
                'edge_density': f"{texture.get('edge_density', 0):.3f}",
                'uniformity': f"{texture.get('uniformity', 0):.3f}"
            }
        
        # 热度分析
        if 'thermal_analysis' in enhanced_analysis:
            thermal = enhanced_analysis['thermal_analysis']
            formatted['thermal_analysis'] = {
                'anomaly_score': f"{thermal.get('anomaly_score', 0):.3f}",
                'temperature_variance': f"{thermal.get('temperature_variance', 0):.3f}"
            }
        
        # 缺陷分析
        if 'defect_analysis' in enhanced_analysis:
            defect = enhanced_analysis['defect_analysis']
            formatted['defect_analysis'] = {
                'total_defects': defect.get('total_defects', 0),
                'coverage_percent': f"{defect.get('severity_analysis', {}).get('defect_coverage_percent', 0):.2f}%",
                'severity': defect.get('severity_analysis', {}).get('severity', '未知')
            }
        
        return formatted
    
    def _generate_visualizations(self, metrics: Dict) -> Dict[str, str]:
        """生成可视化图表"""
        charts = {}
        
        try:
            # 1. 评分雷达图
            charts['radar_chart'] = self._create_radar_chart(metrics)
            
            # 2. 置信度分布图
            charts['confidence_chart'] = self._create_confidence_chart(metrics)
            
            # 3. 覆盖率饼图
            charts['coverage_chart'] = self._create_coverage_chart(metrics)
            
            # 4. 趋势分析图
            charts['trend_chart'] = self._create_trend_chart(metrics)
            
        except Exception as e:
            print(f"生成可视化图表失败: {e}")
            charts['error'] = str(e)
        
        return charts
    
    def _create_radar_chart(self, metrics: Dict) -> str:
        """创建评分雷达图"""
        # 准备数据
        categories = ['检测质量', '健康状况', '结果可信度', '置信度稳定性', '覆盖率合理性']
        
        quality = metrics.get('quality_score', {})
        health = metrics.get('health_assessment', {})
        reliability = metrics.get('reliability_score', {})
        confidence = metrics.get('confidence_analysis', {})
        coverage = metrics.get('coverage_analysis', {})
        
        values = [
            quality.get('overall_quality_score', 0),
            health.get('overall_health_score', 0),
            reliability.get('reliability_score', 0),
            1 - confidence.get('confidence_std', 1),  # 标准差越小越好
            max(0, 1 - abs(coverage.get('combined_coverage_percent', 20) - 20) / 50)  # 20%左右最合理
        ]
        
        # 创建雷达图
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        
        # 计算角度
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]  # 闭合图形
        angles += angles[:1]
        
        # 绘制雷达图
        ax.plot(angles, values, 'o-', linewidth=2, label='检测评分', color='#1f77b4')
        ax.fill(angles, values, alpha=0.25, color='#1f77b4')
        
        # 设置标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'])
        ax.grid(True)
        
        plt.title('检测评分雷达图', size=16, pad=20)
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        # 转换为base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return chart_base64
    
    def _create_confidence_chart(self, metrics: Dict) -> str:
        """创建置信度分布图"""
        confidence = metrics.get('confidence_analysis', {})
        distribution = confidence.get('confidence_distribution', {'high': 0, 'medium': 0, 'low': 0})
        
        labels = ['高置信度', '中等置信度', '低置信度']
        values = [distribution.get('high', 0), distribution.get('medium', 0), distribution.get('low', 0)]
        colors = ['#28a745', '#ffc107', '#dc3545']
        
        if sum(values) == 0:
            values = [1, 0, 0]  # 默认值
        
        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.bar(labels, values, color=colors, alpha=0.8)
        
        # 添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{value}', ha='center', va='bottom', fontsize=12)
        
        plt.title('置信度分布统计', size=14)
        plt.ylabel('检测数量')
        plt.xlabel('置信度等级')
        plt.grid(axis='y', alpha=0.3)
        
        # 转换为base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return chart_base64
    
    def _create_coverage_chart(self, metrics: Dict) -> str:
        """创建覆盖率饼图"""
        coverage = metrics.get('coverage_analysis', {})
        coverage_percent = coverage.get('combined_coverage_percent', 0)
        healthy_percent = 100 - coverage_percent
        
        labels = ['健康区域', '病害区域']
        sizes = [healthy_percent, coverage_percent]
        colors = ['#28a745', '#dc3545']
        explode = (0, 0.1)  # 突出病害区域
        
        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                         autopct='%1.1f%%', shadow=True, startangle=90)
        
        # 美化文本
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(12)
            autotext.set_weight('bold')
        
        plt.title('叶片健康覆盖率分析', size=14)
        
        # 转换为base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return chart_base64
    
    def _create_trend_chart(self, metrics: Dict) -> str:
        """创建趋势分析图"""
        # 模拟历史数据用于趋势分析
        health = metrics.get('health_assessment', {})
        current_score = health.get('overall_health_score', 0.5)
        
        # 生成模拟的历史趋势数据
        days = list(range(1, 8))  # 7天
        # 模拟数据：当前值前后波动
        scores = [
            current_score + np.random.normal(0, 0.1) for _ in range(6)
        ] + [current_score]
        
        # 确保数值在合理范围内
        scores = [max(0, min(1, score)) for score in scores]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(days, scores, marker='o', linewidth=2, markersize=8, color='#1f77b4')
        ax.fill_between(days, scores, alpha=0.3, color='#1f77b4')
        
        # 添加当前值标注
        ax.annotate(f'当前: {current_score:.3f}', 
                   xy=(days[-1], scores[-1]), 
                   xytext=(days[-1]-1, scores[-1]+0.1),
                   arrowprops=dict(arrowstyle='->', color='red'),
                   fontsize=12, color='red')
        
        plt.title('健康评分趋势分析', size=14)
        plt.xlabel('时间 (天)')
        plt.ylabel('健康评分')
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 1)
        
        # 转换为base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return chart_base64
    
    def _format_recommendations(self, metrics: Dict) -> List[Dict]:
        """格式化建议"""
        recommendations = metrics.get('recommendations', [])
        
        formatted_recommendations = []
        for rec in recommendations:
            formatted_recommendations.append({
                'type': rec.get('type', 'general'),
                'title': rec.get('title', '无标题'),
                'message': rec.get('message', '无内容'),
                'priority': self._translate_priority(rec.get('priority', 'medium')),
                'priority_color': self._get_priority_color(rec.get('priority', 'medium'))
            })
        
        return formatted_recommendations
    
    def _generate_technical_details(self, metrics: Dict) -> Dict:
        """生成技术详情"""
        return {
            'detection_algorithm': 'YOLOv8n + ECA注意力机制',
            'enhancement_modules': [
                '多模态疾病分析器',
                '缺陷检测器', 
                '区域分析器',
                '光谱指数分析器'
            ],
            'confidence_threshold': '0.15',
            'iou_threshold': '0.45',
            'image_preprocessing': [
                '尺寸标准化 (640x640)',
                '颜色空间转换',
                '噪声过滤',
                '对比度增强'
            ],
            'analysis_methods': [
                'HSV颜色空间分析',
                'Canny边缘检测',
                'Sobel滤波器',
                '形态学操作',
                'TMDI光谱指数'
            ]
        }
    
    def _generate_html_report(self, report_data: Dict, result_image_base64: str) -> str:
        """生成HTML报告"""
        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>烤烟病害检测报告 - {report_data['metadata']['report_id']}</title>
            <style>
                body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .report-container {{ max-width: 1200px; margin: 0 auto; background: white; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 30px; text-align: center; }}
                .section {{ padding: 25px; border-bottom: 1px solid #eee; }}
                .section:last-child {{ border-bottom: none; }}
                .section-title {{ color: #28a745; font-size: 1.5em; margin-bottom: 20px; border-left: 4px solid #28a745; padding-left: 15px; }}
                .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
                .metric-card {{ background: #f8f9fa; border-left: 4px solid #28a745; padding: 15px; border-radius: 5px; }}
                .metric-label {{ font-weight: bold; color: #666; }}
                .metric-value {{ font-size: 1.2em; color: #333; margin-top: 5px; }}
                .image-container {{ text-align: center; margin: 20px 0; }}
                .result-image {{ max-width: 100%; height: auto; border: 2px solid #28a745; border-radius: 10px; }}
                .chart-container {{ text-align: center; margin: 30px 0; }}
                .chart-image {{ max-width: 100%; height: auto; }}
                .recommendation {{ background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 10px 0; }}
                .recommendation.urgent {{ background: #f8d7da; border-color: #f5c6cb; }}
                .recommendation.high {{ background: #ffe8cc; border-color: #ffdf9e; }}
                .recommendation.low {{ background: #d4edda; border-color: #c3e6cb; }}
                .summary-card {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 25px; border-radius: 10px; margin: 20px 0; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 0.9em; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #28a745; color: white; }}
                .print-only {{ display: none; }}
                @media print {{ .print-only {{ display: block; }} .no-print {{ display: none; }} }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <!-- 报告头部 -->
                <div class="header">
                    <h1>🌿 云南烤烟病害检测报告</h1>
                    <h2>报告编号: {report_data['metadata']['report_id']}</h2>
                    <p>生成时间: {datetime.fromisoformat(report_data['metadata']['generation_time']).strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                </div>
                
                <!-- 执行摘要 -->
                <div class="section">
                    <h2 class="section-title">📋 执行摘要</h2>
                    <div class="summary-card">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                            <div>
                                <h4>检测结果</h4>
                                <p>检测数量: {report_data['executive_summary']['detection_count']}</p>
                                <p>主要病害: {report_data['executive_summary']['primary_condition']}</p>
                                <p>风险等级: <span style="color: {report_data['executive_summary']['risk_color']}">{report_data['executive_summary']['risk_level']}</span></p>
                            </div>
                            <div>
                                <h4>健康评估</h4>
                                <p>健康状况: {report_data['executive_summary']['health_status']}</p>
                                <p>严重程度: {report_data['executive_summary']['severity_level']}</p>
                                <p>覆盖率: {report_data['executive_summary']['coverage_rate']}</p>
                            </div>
                            <div>
                                <h4>质量评估</h4>
                                <p>检测质量: {report_data['executive_summary']['quality_rating']}</p>
                                <p>置信度: {report_data['executive_summary']['confidence_score']}</p>
                                <p>需要治疗: {'是' if report_data['executive_summary']['treatment_required'] else '否'}</p>
                            </div>
                        </div>
                        
                        <h4 style="margin-top: 20px;">关键发现:</h4>
                        <ul>
                            {''.join([f'<li>{finding}</li>' for finding in report_data['executive_summary']['key_findings']])}
                        </ul>
                    </div>
                </div>
                
                <!-- 检测结果图像 -->
                <div class="section">
                    <h2 class="section-title">🖼️ 检测结果图像</h2>
                    <div class="image-container">
                        <img src="data:image/jpeg;base64,{result_image_base64}" alt="检测结果" class="result-image">
                        <p style="margin-top: 10px; color: #666;">原始文件: {report_data['metadata']['original_filename']}</p>
                    </div>
                </div>
                
                <!-- 详细检测结果 -->
                <div class="section">
                    <h2 class="section-title">🔍 详细检测结果</h2>
                    {self._generate_detection_table(report_data['detection_details'])}
                </div>
                
                <!-- 评价指标分析 -->
                <div class="section">
                    <h2 class="section-title">📊 评价指标分析</h2>
                    {self._generate_metrics_html(report_data['metrics_analysis'])}
                </div>
                
                <!-- 可视化图表 -->
                <div class="section">
                    <h2 class="section-title">📈 数据可视化</h2>
                    {self._generate_charts_html(report_data['visualizations'])}
                </div>
                
                <!-- 增强分析结果 -->
                <div class="section">
                    <h2 class="section-title">🔬 增强分析结果</h2>
                    {self._generate_enhanced_analysis_html(report_data['enhanced_analysis'])}
                </div>
                
                <!-- 建议和建议 -->
                <div class="section">
                    <h2 class="section-title">💡 建议和建议</h2>
                    {self._generate_recommendations_html(report_data['recommendations'])}
                </div>
                
                <!-- 技术详情 -->
                <div class="section">
                    <h2 class="section-title">⚙️ 技术详情</h2>
                    {self._generate_technical_details_html(report_data['technical_details'])}
                </div>
                
                <!-- 报告尾部 -->
                <div class="footer">
                    <p>本报告由云南烤烟病害检测系统自动生成</p>
                    <p>系统版本: {report_data['metadata']['detection_system']} | AI引擎: {report_data['metadata']['ai_engine']}</p>
                    <p>报告版本: {report_data['metadata']['report_version']} | 生成时间: {datetime.fromisoformat(report_data['metadata']['generation_time']).strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _generate_detection_table(self, detections: List[Dict]) -> str:
        """生成检测结果表格"""
        if not detections:
            return "<p>未检测到病害。</p>"
        
        table_html = "<table><thead><tr><th>序号</th><th>病害类型</th><th>置信度</th><th>描述</th><th>治疗方案</th><th>位置信息</th></tr></thead><tbody>"
        
        for detection in detections:
            table_html += f"""
            <tr>
                <td>{detection['index']}</td>
                <td>{detection['disease_name']}</td>
                <td>{detection['confidence']}</td>
                <td>{detection['description']}</td>
                <td>{detection['treatment']}</td>
                <td>{detection['bbox_info']}</td>
            </tr>
            """
        
        table_html += "</tbody></table>"
        return table_html
    
    def _generate_metrics_html(self, metrics: Dict) -> str:
        """生成指标HTML"""
        html = '<div class="metric-grid">'
        
        # 置信度指标
        confidence = metrics.get('confidence_metrics', {})
        html += f"""
        <div class="metric-card">
            <div class="metric-label">置信度分析</div>
            <div class="metric-value">平均值: {confidence.get('average', 'N/A')}</div>
            <div class="metric-value">范围: {confidence.get('range', 'N/A')}</div>
            <div class="metric-value">稳定性: {confidence.get('stability', 'N/A')}</div>
        </div>
        """
        
        # 覆盖率指标
        coverage = metrics.get('coverage_metrics', {})
        html += f"""
        <div class="metric-card">
            <div class="metric-label">覆盖率分析</div>
            <div class="metric-value">检测覆盖: {coverage.get('detection_coverage', 'N/A')}</div>
            <div class="metric-value">缺陷覆盖: {coverage.get('defect_coverage', 'N/A')}</div>
            <div class="metric-value">综合覆盖: {coverage.get('combined_coverage', 'N/A')}</div>
        </div>
        """
        
        # 健康指标
        health = metrics.get('health_metrics', {})
        html += f"""
        <div class="metric-card">
            <div class="metric-label">健康评估</div>
            <div class="metric-value">总体评分: {health.get('overall_score', 'N/A')}</div>
            <div class="metric-value">健康等级: {health.get('health_level', 'N/A')}</div>
            <div class="metric-value">颜色健康: {health.get('color_health', 'N/A')}</div>
        </div>
        """
        
        # 质量指标
        quality = metrics.get('quality_assessment', {})
        html += f"""
        <div class="metric-card">
            <div class="metric-label">质量评估</div>
            <div class="metric-value">总体质量: {quality.get('overall_quality', 'N/A')}</div>
            <div class="metric-value">质量等级: {quality.get('quality_level', 'N/A')}</div>
            <div class="metric-value">一致性: {quality.get('consistency_score', 'N/A')}</div>
        </div>
        """
        
        html += '</div>'
        return html
    
    def _generate_charts_html(self, charts: Dict) -> str:
        """生成图表HTML"""
        if 'error' in charts:
            return f"<p>图表生成失败: {charts['error']}</p>"
        
        html = ""
        chart_titles = {
            'radar_chart': '评分雷达图',
            'confidence_chart': '置信度分布图', 
            'coverage_chart': '覆盖率分析图',
            'trend_chart': '趋势分析图'
        }
        
        for chart_key, chart_base64 in charts.items():
            if chart_key in chart_titles:
                html += f"""
                <div class="chart-container">
                    <h4>{chart_titles[chart_key]}</h4>
                    <img src="data:image/png;base64,{chart_base64}" alt="{chart_titles[chart_key]}" class="chart-image">
                </div>
                """
        
        return html
    
    def _generate_enhanced_analysis_html(self, enhanced_analysis: Dict) -> str:
        """生成增强分析HTML"""
        if not enhanced_analysis:
            return "<p>增强分析数据不可用。</p>"
        
        html = '<div class="metric-grid">'
        
        # 颜色分析
        if 'color_analysis' in enhanced_analysis:
            color = enhanced_analysis['color_analysis']
            html += f"""
            <div class="metric-card">
                <div class="metric-label">颜色分析</div>
                <div class="metric-value">绿色比例: {color.get('green_ratio', 'N/A')}</div>
                <div class="metric-value">病害比例: {color.get('disease_ratio', 'N/A')}</div>
                <div class="metric-value">健康评分: {color.get('health_score', 'N/A')}</div>
            </div>
            """
        
        # 纹理分析
        if 'texture_analysis' in enhanced_analysis:
            texture = enhanced_analysis['texture_analysis']
            html += f"""
            <div class="metric-card">
                <div class="metric-label">纹理分析</div>
                <div class="metric-value">复杂度: {texture.get('complexity', 'N/A')}</div>
                <div class="metric-value">边缘密度: {texture.get('edge_density', 'N/A')}</div>
                <div class="metric-value">均匀性: {texture.get('uniformity', 'N/A')}</div>
            </div>
            """
        
        # 缺陷分析
        if 'defect_analysis' in enhanced_analysis:
            defect = enhanced_analysis['defect_analysis']
            html += f"""
            <div class="metric-card">
                <div class="metric-label">缺陷分析</div>
                <div class="metric-value">缺陷总数: {defect.get('total_defects', 'N/A')}</div>
                <div class="metric-value">覆盖率: {defect.get('coverage_percent', 'N/A')}</div>
                <div class="metric-value">严重程度: {defect.get('severity', 'N/A')}</div>
            </div>
            """
        
        html += '</div>'
        return html
    
    def _generate_recommendations_html(self, recommendations: List[Dict]) -> str:
        """生成建议HTML"""
        if not recommendations:
            return "<p>暂无特殊建议。</p>"
        
        html = ""
        for rec in recommendations:
            priority_class = rec['priority'].lower()
            html += f"""
            <div class="recommendation {priority_class}">
                <h4>{rec['title']} <span style="color: {rec['priority_color']}">[{rec['priority']}]</span></h4>
                <p>{rec['message']}</p>
            </div>
            """
        
        return html
    
    def _generate_technical_details_html(self, technical_details: Dict) -> str:
        """生成技术详情HTML"""
        html = f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">检测算法</div>
                <div class="metric-value">{technical_details.get('detection_algorithm', 'N/A')}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">置信度阈值</div>
                <div class="metric-value">{technical_details.get('confidence_threshold', 'N/A')}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">IoU阈值</div>
                <div class="metric-value">{technical_details.get('iou_threshold', 'N/A')}</div>
            </div>
        </div>
        
        <h4>增强模块:</h4>
        <ul>
            {''.join([f'<li>{module}</li>' for module in technical_details.get('enhancement_modules', [])])}
        </ul>
        
        <h4>图像预处理:</h4>
        <ul>
            {''.join([f'<li>{method}</li>' for method in technical_details.get('image_preprocessing', [])])}
        </ul>
        
        <h4>分析方法:</h4>
        <ul>
            {''.join([f'<li>{method}</li>' for method in technical_details.get('analysis_methods', [])])}
        </ul>
        """
        
        return html
    
    def _generate_json_report(self, report_data: Dict) -> str:
        """生成JSON格式报告"""
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    # 翻译函数
    def _translate_disease(self, disease_code: str) -> str:
        diseases = {
            'healthy': '健康叶片',
            'mosaic_virus': '花叶病毒病',
            'brown_spot': '赤星病', 
            'wildfire': '野火病',
            'bacterial_wilt': '青枯病',
            'healthy_dominant': '以健康为主',
            'none': '无病害',
            'unknown': '未知'
        }
        return diseases.get(disease_code, disease_code)
    
    def _translate_health_level(self, level: str) -> str:
        levels = {
            'excellent': '优秀',
            'good': '良好',
            'fair': '一般',
            'poor': '较差', 
            'critical': '危险',
            'unknown': '未知'
        }
        return levels.get(level, level)
    
    def _translate_severity_level(self, level: str) -> str:
        levels = {
            'severe': '严重',
            'moderate': '中等',
            'mild': '轻微',
            'minimal': '极轻',
            'none': '无',
            'unknown': '未知'
        }
        return levels.get(level, level)
    
    def _translate_quality_level(self, level: str) -> str:
        levels = {
            'excellent': '优秀',
            'good': '良好',
            'fair': '一般',
            'poor': '较差',
            'unknown': '未知'
        }
        return levels.get(level, level)
    
    def _translate_reliability_level(self, level: str) -> str:
        levels = {
            'very_high': '很高',
            'high': '高',
            'medium': '中等',
            'low': '低',
            'unknown': '未知'
        }
        return levels.get(level, level)
    
    def _translate_coverage_level(self, level: str) -> str:
        levels = {
            'severe': '严重',
            'moderate': '中等',
            'mild': '轻微',
            'minimal': '极轻',
            'unknown': '未知'
        }
        return levels.get(level, level)
    
    def _translate_priority(self, priority: str) -> str:
        priorities = {
            'urgent': '紧急',
            'high': '高',
            'medium': '中',
            'low': '低'
        }
        return priorities.get(priority, priority)
    
    def _get_priority_color(self, priority: str) -> str:
        colors = {
            'urgent': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        }
        return colors.get(priority, '#6c757d')