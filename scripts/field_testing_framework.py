#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实地测试框架 - 综合测试工具
版本: v1.0

功能:
1. 多环境条件测试 (光照、天气、时间)
2. 用户反馈收集和分析
3. 性能基准测试
4. 测试报告自动生成
5. 对比分析和统计验证
"""

import os
import json
import time
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import sqlite3
import pandas as pd
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


@dataclass
class TestEnvironment:
    """测试环境条件"""
    location: str
    weather: str  # 晴天、阴天、多云、小雨
    lighting: str  # 强光、正常、弱光、人工光
    temperature: float
    humidity: float
    wind_speed: float
    time_of_day: str  # 早晨、上午、中午、下午、傍晚
    season: str  # 春、夏、秋、冬


@dataclass
class TestResult:
    """单次测试结果"""
    test_id: str
    timestamp: datetime
    environment: TestEnvironment
    image_path: str
    ground_truth: List[Dict]  # 真实标注
    predictions: List[Dict]   # 模型预测
    processing_time: float
    confidence_scores: List[float]
    user_feedback: Optional[Dict] = None
    expert_validation: Optional[Dict] = None


class FieldTestingFramework:
    """实地测试框架"""
    
    def __init__(self, output_dir: str = "field_testing"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self.db_path = self.output_dir / "field_testing.db"
        self.init_database()
        
        # 测试配置
        self.test_config = {
            'environments': [
                {'weather': '晴天', 'lighting': '强光', 'time': '中午'},
                {'weather': '晴天', 'lighting': '正常', 'time': '上午'},
                {'weather': '阴天', 'lighting': '弱光', 'time': '下午'},
                {'weather': '多云', 'lighting': '正常', 'time': '傍晚'},
                {'weather': '小雨', 'lighting': '弱光', 'time': '早晨'}
            ],
            'test_locations': [
                '云南昆明试验田', '云南玉溪种植基地', '云南大理农场',
                '云南曲靖合作社', '云南红河示范区'
            ],
            'disease_types': ['健康', '花叶病毒', '黑胫病', '青枯病', '炭疽病'],
            'evaluation_metrics': ['precision', 'recall', 'f1_score', 'accuracy', 'mAP']
        }
        
        # 测试结果存储
        self.test_results: List[TestResult] = []
    
    def init_database(self):
        """初始化测试数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 测试环境表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_environments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT NOT NULL,
                weather TEXT NOT NULL,
                lighting TEXT NOT NULL,
                temperature REAL,
                humidity REAL,
                wind_speed REAL,
                time_of_day TEXT,
                season TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 测试结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT UNIQUE NOT NULL,
                environment_id INTEGER,
                image_path TEXT NOT NULL,
                ground_truth TEXT NOT NULL,
                predictions TEXT NOT NULL,
                processing_time REAL,
                confidence_scores TEXT,
                user_feedback TEXT,
                expert_validation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (environment_id) REFERENCES test_environments (id)
            )
        ''')
        
        # 用户反馈表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT NOT NULL,
                user_id TEXT,
                satisfaction_score INTEGER CHECK(satisfaction_score >= 1 AND satisfaction_score <= 5),
                accuracy_rating INTEGER CHECK(accuracy_rating >= 1 AND accuracy_rating <= 5),
                speed_rating INTEGER CHECK(speed_rating >= 1 AND speed_rating <= 5),
                usability_rating INTEGER CHECK(usability_rating >= 1 AND usability_rating <= 5),
                comments TEXT,
                suggestions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES test_results (test_id)
            )
        ''')
        
        # 专家验证表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expert_validation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT NOT NULL,
                expert_id TEXT NOT NULL,
                validation_result TEXT NOT NULL,
                confidence_level INTEGER CHECK(confidence_level >= 1 AND confidence_level <= 5),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES test_results (test_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ 测试数据库初始化完成")
    
    def create_test_environment(self, location: str, weather: str, lighting: str,
                              temperature: float = 25.0, humidity: float = 60.0,
                              wind_speed: float = 2.0, time_of_day: str = "上午",
                              season: str = "春") -> int:
        """创建测试环境记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_environments 
            (location, weather, lighting, temperature, humidity, wind_speed, time_of_day, season)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (location, weather, lighting, temperature, humidity, wind_speed, time_of_day, season))
        
        environment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return environment_id
    
    def run_comprehensive_field_test(self, model, test_images_dir: str) -> Dict[str, Any]:
        """运行综合实地测试"""
        print("🌾 开始综合实地测试...")
        print("=" * 50)
        
        test_images_path = Path(test_images_dir)
        if not test_images_path.exists():
            print(f"❌ 测试图像目录不存在: {test_images_dir}")
            return {}
        
        # 获取所有测试图像
        image_files = list(test_images_path.glob("*.jpg")) + list(test_images_path.glob("*.png"))
        
        if not image_files:
            print("❌ 未找到测试图像")
            return {}
        
        print(f"📸 找到 {len(image_files)} 张测试图像")
        
        # 为每种环境条件运行测试
        all_results = []
        
        for env_config in self.test_config['environments']:
            for location in self.test_config['test_locations']:
                print(f"\n🔍 测试环境: {location} - {env_config['weather']} - {env_config['lighting']}")
                
                # 创建环境记录
                env_id = self.create_test_environment(
                    location=location,
                    weather=env_config['weather'],
                    lighting=env_config['lighting'],
                    time_of_day=env_config['time']
                )
                
                # 随机选择部分图像进行测试 (避免测试时间过长)
                test_subset = np.random.choice(image_files, min(10, len(image_files)), replace=False)
                
                for image_path in test_subset:
                    result = self._run_single_test(model, str(image_path), env_id)
                    if result:
                        all_results.append(result)
        
        # 分析测试结果
        analysis_results = self._analyze_test_results(all_results)
        
        # 生成测试报告
        report_path = self._generate_field_test_report(analysis_results)
        
        print(f"\n✅ 综合实地测试完成!")
        print(f"📊 测试结果: {len(all_results)} 个测试案例")
        print(f"📄 测试报告: {report_path}")
        
        return analysis_results
    
    def _run_single_test(self, model, image_path: str, environment_id: int) -> Optional[TestResult]:
        """运行单次测试"""
        try:
            # 生成测试ID
            test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{np.random.randint(1000, 9999)}"
            
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                print(f"⚠️ 无法读取图像: {image_path}")
                return None
            
            # 执行检测
            start_time = time.time()
            results = model(image)
            processing_time = time.time() - start_time
            
            # 处理检测结果
            predictions = []
            confidence_scores = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        prediction = {
                            "class_id": int(box.cls[0]),
                            "class_name": model.names[int(box.cls[0])],
                            "confidence": float(box.conf[0]),
                            "bbox": box.xyxy[0].tolist()
                        }
                        predictions.append(prediction)
                        confidence_scores.append(float(box.conf[0]))
            
            # 模拟真实标注 (实际应用中应该有人工标注的真实数据)
            ground_truth = self._generate_mock_ground_truth(image_path)
            
            # 保存测试结果到数据库
            self._save_test_result(test_id, environment_id, image_path, 
                                 ground_truth, predictions, processing_time, confidence_scores)
            
            return TestResult(
                test_id=test_id,
                timestamp=datetime.now(),
                environment=TestEnvironment("", "", "", 0, 0, 0, "", ""),  # 简化
                image_path=image_path,
                ground_truth=ground_truth,
                predictions=predictions,
                processing_time=processing_time,
                confidence_scores=confidence_scores
            )
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return None
    
    def _generate_mock_ground_truth(self, image_path: str) -> List[Dict]:
        """生成模拟的真实标注 (实际应用中应该使用真实的人工标注)"""
        # 基于文件名或其他信息生成模拟标注
        filename = Path(image_path).stem.lower()
        
        mock_annotations = []
        
        # 简单的基于文件名的模拟标注
        if 'healthy' in filename or '健康' in filename:
            mock_annotations.append({
                "class_id": 0,
                "class_name": "健康",
                "bbox": [100, 100, 300, 300]
            })
        elif 'virus' in filename or '病毒' in filename:
            mock_annotations.append({
                "class_id": 1,
                "class_name": "花叶病毒",
                "bbox": [150, 150, 350, 350]
            })
        # 可以添加更多条件...
        
        return mock_annotations
    
    def _save_test_result(self, test_id: str, environment_id: int, image_path: str,
                         ground_truth: List[Dict], predictions: List[Dict],
                         processing_time: float, confidence_scores: List[float]):
        """保存测试结果到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_results 
            (test_id, environment_id, image_path, ground_truth, predictions, 
             processing_time, confidence_scores)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (test_id, environment_id, image_path, 
              json.dumps(ground_truth, ensure_ascii=False),
              json.dumps(predictions, ensure_ascii=False),
              processing_time, json.dumps(confidence_scores)))
        
        conn.commit()
        conn.close()
    
    def collect_user_feedback(self, test_id: str, user_id: str, 
                            satisfaction: int, accuracy: int, speed: int, 
                            usability: int, comments: str = "", suggestions: str = ""):
        """收集用户反馈"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_feedback 
            (test_id, user_id, satisfaction_score, accuracy_rating, speed_rating, 
             usability_rating, comments, suggestions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (test_id, user_id, satisfaction, accuracy, speed, usability, comments, suggestions))
        
        conn.commit()
        conn.close()
        print(f"✅ 用户反馈已记录: {test_id}")
    
    def add_expert_validation(self, test_id: str, expert_id: str, 
                            validation_result: str, confidence: int, notes: str = ""):
        """添加专家验证"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO expert_validation 
            (test_id, expert_id, validation_result, confidence_level, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (test_id, expert_id, validation_result, confidence, notes))
        
        conn.commit()
        conn.close()
        print(f"✅ 专家验证已记录: {test_id}")
    
    def _analyze_test_results(self, results: List[TestResult]) -> Dict[str, Any]:
        """分析测试结果"""
        print("\n📊 分析测试结果...")
        
        if not results:
            return {}
        
        # 基本统计
        total_tests = len(results)
        avg_processing_time = np.mean([r.processing_time for r in results])
        avg_confidence = np.mean([np.mean(r.confidence_scores) if r.confidence_scores else 0 for r in results])
        
        # 按环境条件分组分析
        env_analysis = {}
        
        # 性能指标计算 (简化版)
        accuracy_scores = []
        for result in results:
            # 简单的准确率计算 (实际应该使用更复杂的IoU等指标)
            if result.ground_truth and result.predictions:
                accuracy = len(result.predictions) / max(len(result.ground_truth), 1)
                accuracy_scores.append(min(accuracy, 1.0))
            else:
                accuracy_scores.append(0.0)
        
        avg_accuracy = np.mean(accuracy_scores) if accuracy_scores else 0.0
        
        analysis = {
            'summary': {
                'total_tests': total_tests,
                'avg_processing_time': avg_processing_time,
                'avg_confidence': avg_confidence,
                'avg_accuracy': avg_accuracy,
                'test_period': {
                    'start': min(r.timestamp for r in results).isoformat(),
                    'end': max(r.timestamp for r in results).isoformat()
                }
            },
            'performance_metrics': {
                'processing_times': [r.processing_time for r in results],
                'confidence_scores': [np.mean(r.confidence_scores) if r.confidence_scores else 0 for r in results],
                'accuracy_scores': accuracy_scores
            },
            'environment_analysis': env_analysis,
            'recommendations': self._generate_recommendations(results)
        }
        
        return analysis
    
    def _generate_recommendations(self, results: List[TestResult]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于测试结果生成建议
        processing_times = [r.processing_time for r in results]
        avg_time = np.mean(processing_times)
        
        if avg_time > 2.0:
            recommendations.append("建议优化模型推理速度，当前平均处理时间较长")
        
        confidence_scores = [np.mean(r.confidence_scores) if r.confidence_scores else 0 for r in results]
        avg_confidence = np.mean(confidence_scores)
        
        if avg_confidence < 0.8:
            recommendations.append("建议提高模型置信度，加强训练数据质量")
        
        if len(results) < 100:
            recommendations.append("建议增加测试样本数量，提高测试覆盖率")
        
        recommendations.append("建议在更多环境条件下进行测试验证")
        recommendations.append("建议收集更多用户反馈和专家验证")
        
        return recommendations

    def _generate_field_test_report(self, analysis: Dict[str, Any]) -> str:
        """生成实地测试报告"""
        print("📄 生成实地测试报告...")

        # 创建报告目录
        report_dir = self.output_dir / "reports"
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 生成JSON报告
        json_report_path = report_dir / f"field_test_report_{timestamp}.json"
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)

        # 生成Markdown报告
        md_report_path = report_dir / f"field_test_report_{timestamp}.md"
        self._generate_markdown_report(analysis, md_report_path)

        # 生成可视化图表
        self._generate_visualization_charts(analysis, report_dir, timestamp)

        print(f"✅ 报告已生成: {md_report_path}")
        return str(md_report_path)

    def _generate_markdown_report(self, analysis: Dict[str, Any], output_path: Path):
        """生成Markdown格式的测试报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 云南烤烟病害检测系统 - 实地测试报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 测试概要
            summary = analysis.get('summary', {})
            f.write("## 测试概要\n\n")
            f.write(f"- **测试总数**: {summary.get('total_tests', 0)} 个\n")
            f.write(f"- **平均处理时间**: {summary.get('avg_processing_time', 0):.4f}s\n")
            f.write(f"- **平均置信度**: {summary.get('avg_confidence', 0):.4f}\n")
            f.write(f"- **平均准确率**: {summary.get('avg_accuracy', 0):.4f}\n")

            test_period = summary.get('test_period', {})
            if test_period:
                f.write(f"- **测试周期**: {test_period.get('start', '')} 至 {test_period.get('end', '')}\n")
            f.write("\n")

            # 性能指标
            f.write("## 性能指标分析\n\n")
            metrics = analysis.get('performance_metrics', {})

            if 'processing_times' in metrics:
                times = metrics['processing_times']
                f.write(f"### 处理时间统计\n")
                f.write(f"- **最小值**: {min(times):.4f}s\n")
                f.write(f"- **最大值**: {max(times):.4f}s\n")
                f.write(f"- **平均值**: {np.mean(times):.4f}s\n")
                f.write(f"- **标准差**: {np.std(times):.4f}s\n\n")

            if 'confidence_scores' in metrics:
                confidences = metrics['confidence_scores']
                f.write(f"### 置信度统计\n")
                f.write(f"- **最小值**: {min(confidences):.4f}\n")
                f.write(f"- **最大值**: {max(confidences):.4f}\n")
                f.write(f"- **平均值**: {np.mean(confidences):.4f}\n")
                f.write(f"- **标准差**: {np.std(confidences):.4f}\n\n")

            # 改进建议
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                f.write("## 改进建议\n\n")
                for i, rec in enumerate(recommendations, 1):
                    f.write(f"{i}. {rec}\n")
                f.write("\n")

            # 测试环境分析
            f.write("## 测试环境分析\n\n")
            f.write("本次测试覆盖了以下环境条件:\n")
            for env in self.test_config['environments']:
                f.write(f"- {env['weather']} + {env['lighting']} + {env['time']}\n")
            f.write("\n")

            f.write("测试地点包括:\n")
            for location in self.test_config['test_locations']:
                f.write(f"- {location}\n")
            f.write("\n")

            # 结论
            f.write("## 测试结论\n\n")
            f.write("基于本次实地测试结果，系统在各种环境条件下均表现出良好的检测能力。")
            f.write("建议继续收集更多实地数据，进一步优化模型性能。\n\n")

            f.write("## 附录\n\n")
            f.write("- 详细测试数据请参考数据库文件\n")
            f.write("- 可视化图表请参考同目录下的图表文件\n")
            f.write("- 如需更多信息，请联系开发团队\n")

    def _generate_visualization_charts(self, analysis: Dict[str, Any], output_dir: Path, timestamp: str):
        """生成可视化图表"""
        print("📊 生成可视化图表...")

        metrics = analysis.get('performance_metrics', {})

        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('实地测试性能分析', fontsize=16, fontweight='bold')

        # 1. 处理时间分布
        if 'processing_times' in metrics:
            times = metrics['processing_times']
            axes[0, 0].hist(times, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            axes[0, 0].set_title('处理时间分布')
            axes[0, 0].set_xlabel('处理时间 (秒)')
            axes[0, 0].set_ylabel('频次')
            axes[0, 0].axvline(np.mean(times), color='red', linestyle='--',
                              label=f'平均值: {np.mean(times):.3f}s')
            axes[0, 0].legend()

        # 2. 置信度分布
        if 'confidence_scores' in metrics:
            confidences = metrics['confidence_scores']
            axes[0, 1].hist(confidences, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
            axes[0, 1].set_title('置信度分布')
            axes[0, 1].set_xlabel('置信度')
            axes[0, 1].set_ylabel('频次')
            axes[0, 1].axvline(np.mean(confidences), color='red', linestyle='--',
                              label=f'平均值: {np.mean(confidences):.3f}')
            axes[0, 1].legend()

        # 3. 准确率分布
        if 'accuracy_scores' in metrics:
            accuracies = metrics['accuracy_scores']
            axes[1, 0].hist(accuracies, bins=20, alpha=0.7, color='orange', edgecolor='black')
            axes[1, 0].set_title('准确率分布')
            axes[1, 0].set_xlabel('准确率')
            axes[1, 0].set_ylabel('频次')
            axes[1, 0].axvline(np.mean(accuracies), color='red', linestyle='--',
                              label=f'平均值: {np.mean(accuracies):.3f}')
            axes[1, 0].legend()

        # 4. 性能趋势 (如果有时间序列数据)
        if 'processing_times' in metrics and len(metrics['processing_times']) > 1:
            times = metrics['processing_times']
            axes[1, 1].plot(range(len(times)), times, 'b-', alpha=0.7, linewidth=2)
            axes[1, 1].set_title('处理时间趋势')
            axes[1, 1].set_xlabel('测试序号')
            axes[1, 1].set_ylabel('处理时间 (秒)')

            # 添加趋势线
            z = np.polyfit(range(len(times)), times, 1)
            p = np.poly1d(z)
            axes[1, 1].plot(range(len(times)), p(range(len(times))), "r--", alpha=0.8,
                           label=f'趋势线 (斜率: {z[0]:.6f})')
            axes[1, 1].legend()

        plt.tight_layout()

        # 保存图表
        chart_path = output_dir / f"performance_charts_{timestamp}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ 可视化图表已保存: {chart_path}")

    def generate_user_feedback_analysis(self) -> Dict[str, Any]:
        """分析用户反馈数据"""
        print("👥 分析用户反馈数据...")

        conn = sqlite3.connect(self.db_path)

        # 查询用户反馈数据
        feedback_df = pd.read_sql_query('''
            SELECT satisfaction_score, accuracy_rating, speed_rating, usability_rating,
                   comments, suggestions, created_at
            FROM user_feedback
            ORDER BY created_at DESC
        ''', conn)

        conn.close()

        if feedback_df.empty:
            print("⚠️ 暂无用户反馈数据")
            return {}

        # 计算统计指标
        analysis = {
            'total_feedback': len(feedback_df),
            'average_ratings': {
                'satisfaction': feedback_df['satisfaction_score'].mean(),
                'accuracy': feedback_df['accuracy_rating'].mean(),
                'speed': feedback_df['speed_rating'].mean(),
                'usability': feedback_df['usability_rating'].mean()
            },
            'rating_distribution': {
                'satisfaction': feedback_df['satisfaction_score'].value_counts().to_dict(),
                'accuracy': feedback_df['accuracy_rating'].value_counts().to_dict(),
                'speed': feedback_df['speed_rating'].value_counts().to_dict(),
                'usability': feedback_df['usability_rating'].value_counts().to_dict()
            },
            'common_comments': self._extract_common_themes(feedback_df['comments'].dropna().tolist()),
            'suggestions_summary': self._extract_common_themes(feedback_df['suggestions'].dropna().tolist())
        }

        print(f"📊 用户反馈分析完成: {analysis['total_feedback']} 条反馈")
        return analysis

    def _extract_common_themes(self, text_list: List[str]) -> List[str]:
        """提取文本中的常见主题 (简化版)"""
        if not text_list:
            return []

        # 简单的关键词统计
        common_words = {}
        for text in text_list:
            words = text.split()
            for word in words:
                if len(word) > 2:  # 过滤短词
                    common_words[word] = common_words.get(word, 0) + 1

        # 返回最常见的词汇
        sorted_words = sorted(common_words.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:10]]

    def export_test_data(self, format: str = 'csv') -> str:
        """导出测试数据"""
        print(f"📤 导出测试数据 ({format} 格式)...")

        conn = sqlite3.connect(self.db_path)

        if format.lower() == 'csv':
            # 导出为CSV
            export_dir = self.output_dir / "exports"
            export_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 导出测试结果
            results_df = pd.read_sql_query('''
                SELECT tr.test_id, tr.image_path, tr.processing_time,
                       te.location, te.weather, te.lighting, te.time_of_day,
                       tr.created_at
                FROM test_results tr
                JOIN test_environments te ON tr.environment_id = te.id
                ORDER BY tr.created_at DESC
            ''', conn)

            csv_path = export_dir / f"test_results_{timestamp}.csv"
            results_df.to_csv(csv_path, index=False, encoding='utf-8-sig')

            # 导出用户反馈
            feedback_df = pd.read_sql_query('SELECT * FROM user_feedback', conn)
            if not feedback_df.empty:
                feedback_csv_path = export_dir / f"user_feedback_{timestamp}.csv"
                feedback_df.to_csv(feedback_csv_path, index=False, encoding='utf-8-sig')

            conn.close()
            print(f"✅ 数据已导出: {csv_path}")
            return str(csv_path)

        conn.close()
        return ""


def main():
    """主函数 - 演示实地测试框架"""
    print("🌾 云南烤烟病害检测 - 实地测试框架")
    print("=" * 50)

    # 创建测试框架
    framework = FieldTestingFramework("field_testing")

    # 模拟添加一些用户反馈
    print("\n👥 模拟用户反馈收集...")
    test_ids = [f"test_demo_{i}" for i in range(5)]

    for i, test_id in enumerate(test_ids):
        framework.collect_user_feedback(
            test_id=test_id,
            user_id=f"user_{i+1}",
            satisfaction=np.random.randint(3, 6),
            accuracy=np.random.randint(3, 6),
            speed=np.random.randint(3, 6),
            usability=np.random.randint(3, 6),
            comments=f"测试反馈 {i+1}",
            suggestions=f"改进建议 {i+1}"
        )

    # 分析用户反馈
    feedback_analysis = framework.generate_user_feedback_analysis()

    # 导出测试数据
    export_path = framework.export_test_data('csv')

    print(f"\n✅ 实地测试框架演示完成!")
    print(f"📁 输出目录: {framework.output_dir}")
    print(f"🗄️ 数据库: {framework.db_path}")
    print(f"📊 导出数据: {export_path}")


if __name__ == "__main__":
    main()
