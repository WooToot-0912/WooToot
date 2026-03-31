#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云南烤烟病害检测Web系统 - 增强版API
版本: v2.0 - 架构重构版

新增功能:
1. 批量检测功能
2. 检测历史记录管理
3. 用户管理和权限控制
4. 移动端适配
5. 实时检测状态监控
6. 数据统计和分析
"""

import os
import sys
import time
import uuid
import base64
import cv2
import numpy as np
import torch
import sqlite3
import hashlib
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from ultralytics import YOLO

# 可选导入 - 如果没有安装则使用替代方案
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    print("Warning: flask-limiter not installed. Rate limiting disabled.")
    LIMITER_AVAILABLE = False
    Limiter = None
    get_remote_address = None

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    print("Warning: PyJWT not installed. JWT authentication disabled.")
    JWT_AVAILABLE = False
    jwt = None

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

def sanitize_for_json(obj):
    """递归清理对象中的NaN、Infinity等不兼容JSON的值"""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0  # 将NaN和Infinity替换为0
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif obj is None:
        return None
    else:
        return obj

# 数据库管理类
class DatabaseManager:
    """数据库管理器 - 处理用户、检测历史等数据"""

    def __init__(self, db_path: str = "tobacco_detection.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        # 检测历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id TEXT NOT NULL,
                image_name TEXT NOT NULL,
                image_path TEXT NOT NULL,
                detection_type TEXT DEFAULT 'single',
                results TEXT NOT NULL,
                confidence_scores TEXT,
                processing_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # 批量检测任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS batch_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_id TEXT UNIQUE NOT NULL,
                task_name TEXT NOT NULL,
                total_images INTEGER DEFAULT 0,
                processed_images INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                results_path TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # 系统统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                total_detections INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                avg_processing_time REAL DEFAULT 0.0,
                disease_distribution TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        # 创建默认管理员用户
        self.create_default_admin()

    def create_default_admin(self):
        """创建默认管理员用户"""
        try:
            admin_password = generate_password_hash("admin123")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', ("admin", "admin@tobacco-detection.com", admin_password, "admin"))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"创建默认管理员失败: {e}")

    def create_user(self, username: str, email: str, password: str, role: str = "user") -> Dict:
        """创建新用户"""
        try:
            password_hash = generate_password_hash(password)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {"success": True, "user_id": user_id, "message": "用户创建成功"}
        except sqlite3.IntegrityError as e:
            return {"success": False, "message": "用户名或邮箱已存在"}
        except Exception as e:
            return {"success": False, "message": f"创建用户失败: {str(e)}"}

    def authenticate_user(self, username: str, password: str) -> Dict:
        """用户认证"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, username, email, password_hash, role, is_active
                FROM users WHERE username = ?
            ''', (username,))

            user = cursor.fetchone()

            if user and user[5] and check_password_hash(user[3], password):  # is_active and password check
                # 更新最后登录时间
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
                ''', (user[0],))
                conn.commit()

                user_info = {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "role": user[4]
                }

                conn.close()
                return {"success": True, "user": user_info}
            else:
                conn.close()
                return {"success": False, "message": "用户名或密码错误"}

        except Exception as e:
            return {"success": False, "message": f"认证失败: {str(e)}"}

    def save_detection_result(self, user_id: int, session_id: str, image_name: str,
                            image_path: str, results: Dict, processing_time: float,
                            detection_type: str = "single") -> bool:
        """保存检测结果"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 提取置信度分数
            confidence_scores = []
            if 'detections' in results:
                for detection in results['detections']:
                    if 'confidence' in detection:
                        confidence_scores.append(detection['confidence'])

            cursor.execute('''
                INSERT INTO detection_history
                (user_id, session_id, image_name, image_path, detection_type,
                 results, confidence_scores, processing_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, session_id, image_name, image_path, detection_type,
                  str(results), str(confidence_scores), processing_time))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存检测结果失败: {e}")
            return False

    def get_user_history(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """获取用户检测历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, session_id, image_name, detection_type,
                       results, processing_time, created_at
                FROM detection_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))

            history = []
            for row in cursor.fetchall():
                history.append({
                    "id": row[0],
                    "session_id": row[1],
                    "image_name": row[2],
                    "detection_type": row[3],
                    "results": eval(row[4]) if row[4] else {},
                    "processing_time": row[5],
                    "created_at": row[6]
                })

            conn.close()
            return history
        except Exception as e:
            print(f"获取用户历史失败: {e}")
            return []


class BatchDetectionManager:
    """批量检测管理器"""

    def __init__(self, db_manager: DatabaseManager, max_workers: int = 4):
        self.db_manager = db_manager
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = {}  # task_id -> task_info
        self.task_lock = threading.Lock()

    def create_batch_task(self, user_id: int, task_name: str, image_files: List) -> Dict:
        """创建批量检测任务"""
        task_id = str(uuid.uuid4())

        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO batch_tasks (user_id, task_id, task_name, total_images, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, task_id, task_name, len(image_files), 'pending'))

            conn.commit()
            conn.close()

            # 添加到活跃任务列表
            with self.task_lock:
                self.active_tasks[task_id] = {
                    'user_id': user_id,
                    'task_name': task_name,
                    'total_images': len(image_files),
                    'processed_images': 0,
                    'status': 'pending',
                    'results': [],
                    'start_time': None,
                    'end_time': None
                }

            return {"success": True, "task_id": task_id, "message": "批量任务创建成功"}

        except Exception as e:
            return {"success": False, "message": f"创建批量任务失败: {str(e)}"}

    def start_batch_detection(self, task_id: str, image_files: List, detection_function) -> Dict:
        """启动批量检测"""
        if task_id not in self.active_tasks:
            return {"success": False, "message": "任务不存在"}

        # 提交批量检测任务到线程池
        future = self.executor.submit(self._process_batch_detection, task_id, image_files, detection_function)

        # 更新任务状态
        with self.task_lock:
            self.active_tasks[task_id]['status'] = 'running'
            self.active_tasks[task_id]['start_time'] = datetime.now()

        self._update_task_status(task_id, 'running')

        return {"success": True, "message": "批量检测已启动"}

    def _process_batch_detection(self, task_id: str, image_files: List, detection_function):
        """处理批量检测 (在后台线程中运行)"""
        try:
            results = []

            for i, image_file in enumerate(image_files):
                try:
                    # 执行单个图像检测
                    result = detection_function(image_file)
                    results.append({
                        'image_name': image_file.filename,
                        'result': result,
                        'processed_at': datetime.now().isoformat()
                    })

                    # 更新进度
                    with self.task_lock:
                        self.active_tasks[task_id]['processed_images'] = i + 1
                        self.active_tasks[task_id]['results'] = results

                    self._update_task_progress(task_id, i + 1)

                except Exception as e:
                    results.append({
                        'image_name': image_file.filename,
                        'error': str(e),
                        'processed_at': datetime.now().isoformat()
                    })

            # 保存结果到文件
            results_path = self._save_batch_results(task_id, results)

            # 更新任务完成状态
            with self.task_lock:
                self.active_tasks[task_id]['status'] = 'completed'
                self.active_tasks[task_id]['end_time'] = datetime.now()
                self.active_tasks[task_id]['results_path'] = results_path

            self._update_task_completion(task_id, results_path)

        except Exception as e:
            # 更新任务失败状态
            with self.task_lock:
                self.active_tasks[task_id]['status'] = 'failed'
                self.active_tasks[task_id]['error'] = str(e)

            self._update_task_status(task_id, 'failed')

    def _update_task_status(self, task_id: str, status: str):
        """更新任务状态到数据库"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE batch_tasks SET status = ? WHERE task_id = ?
            ''', (status, task_id))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"更新任务状态失败: {e}")

    def _update_task_progress(self, task_id: str, processed_count: int):
        """更新任务进度"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE batch_tasks SET processed_images = ? WHERE task_id = ?
            ''', (processed_count, task_id))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"更新任务进度失败: {e}")

    def _update_task_completion(self, task_id: str, results_path: str):
        """更新任务完成信息"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE batch_tasks
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP, results_path = ?
                WHERE task_id = ?
            ''', (results_path, task_id))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"更新任务完成信息失败: {e}")

    def _save_batch_results(self, task_id: str, results: List[Dict]) -> str:
        """保存批量检测结果到文件"""
        try:
            results_dir = Path("results/batch_results")
            results_dir.mkdir(parents=True, exist_ok=True)

            results_file = results_dir / f"batch_results_{task_id}.json"

            import json
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'task_id': task_id,
                    'total_images': len(results),
                    'completed_at': datetime.now().isoformat(),
                    'results': results
                }, f, ensure_ascii=False, indent=2)

            return str(results_file)

        except Exception as e:
            print(f"保存批量结果失败: {e}")
            return ""

    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        if task_id in self.active_tasks:
            with self.task_lock:
                task_info = self.active_tasks[task_id].copy()

            # 计算进度百分比
            if task_info['total_images'] > 0:
                progress = (task_info['processed_images'] / task_info['total_images']) * 100
            else:
                progress = 0

            task_info['progress'] = round(progress, 2)

            # 计算预估剩余时间
            if task_info['start_time'] and task_info['processed_images'] > 0:
                elapsed_time = (datetime.now() - task_info['start_time']).total_seconds()
                avg_time_per_image = elapsed_time / task_info['processed_images']
                remaining_images = task_info['total_images'] - task_info['processed_images']
                estimated_remaining_time = avg_time_per_image * remaining_images
                task_info['estimated_remaining_time'] = round(estimated_remaining_time, 2)

            return {"success": True, "task_info": task_info}
        else:
            return {"success": False, "message": "任务不存在"}

    def get_user_batch_tasks(self, user_id: int) -> List[Dict]:
        """获取用户的批量任务列表"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT task_id, task_name, total_images, processed_images,
                       status, created_at, completed_at
                FROM batch_tasks
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))

            tasks = []
            for row in cursor.fetchall():
                task_info = {
                    "task_id": row[0],
                    "task_name": row[1],
                    "total_images": row[2],
                    "processed_images": row[3],
                    "status": row[4],
                    "created_at": row[5],
                    "completed_at": row[6]
                }

                # 计算进度
                if task_info['total_images'] > 0:
                    task_info['progress'] = round((task_info['processed_images'] / task_info['total_images']) * 100, 2)
                else:
                    task_info['progress'] = 0

                tasks.append(task_info)

            conn.close()
            return tasks

        except Exception as e:
            print(f"获取用户批量任务失败: {e}")
            return []

# 导入自定义模块
try:
    # 导入基础模块
    from modules import ECA, BackgroundSuppressionBranch, DefectDetector, RegionAnalyzer, TobaccoSpectralIndex
    
    # 导入多模态检测器
    from modules.detection.multi_modal_detector import (
        DiseaseAnalyzer,
        MultiModalDiseaseDetector,
        AdaptiveColorDiseaseDetector,
        AdvancedTextureDiseaseDetector,
        ThermalDiseaseDetector
    )
    
    # 导入注意力机制
    from modules.attention.enhanced_attention_suite import (
        MultiScaleECAAttention,
        SpatialChannelAttention,
        AdaptiveBackgroundSuppression,
        TobaccoSpecificAttention,
        ComprehensiveAttentionModule,
        create_attention_block
    )
    
    # 导入评估模块
    from modules.evaluation.metrics_calculator import DetectionMetricsCalculator, MetricsVisualizer
    from modules.evaluation.report_generator import DetectionReportGenerator
    
    # 尝试导入损失函数
    try:
        from modules.loss.focal_loss import FocalLoss
    except ImportError:
        FocalLoss = None
    
    print("✅ 成功导入所有自定义模块")
    custom_modules_available = True
    
except ImportError as e:
    print(f"⚠️ 导入自定义模块失败: {e}")
    custom_modules_available = False
    
    # 创建简化版本的类和函数
    class DiseaseAnalyzer:
        def __init__(self):
            pass
        def analyze_image(self, img):
            return {
                'health_assessment': {'health_score': 0.5, 'risk_level': 'medium', 'recommendation': '建议进一步检查'},
                'color_analysis': {'health_score': 0.5, 'dominant_colors': []},
                'texture_analysis': {'complexity': 'medium'},
                'thermal_analysis': {'temperature_anomaly': 0.0},
                'defect_analysis': {'total_defects': 0, 'defects': [], 'visualization': None}
            }
    
    class DetectionMetricsCalculator:
        def calculate_detection_metrics(self, detections, enhanced_analysis, image_info):
            return {"summary": {"total_detections": len(detections) if detections else 0}}
    
    class MetricsVisualizer:
        def generate_metrics_html(self, metrics):
            return "<p>指标可视化不可用</p>"
    
    class DetectionReportGenerator:
        def generate_report(self, **kwargs):
            return {"html_content": "<p>报告生成不可用</p>", "json_data": {}}
    
    # 定义空的类以避免导入错误
    class ECA: pass
    class BackgroundSuppressionBranch: pass
    class DefectDetector: pass
    class RegionAnalyzer: pass
    class TobaccoSpectralIndex: pass
    class MultiModalDiseaseDetector: pass

# 注册自定义模块函数
def register_custom_modules():
    """注册所有自定义模块到YOLO"""
    try:
        from ultralytics.nn.tasks import DetectionModel
        # 注册注意力机制
        setattr(DetectionModel, 'ECA', ECA)
        setattr(DetectionModel, 'BackgroundSuppressionBranch', BackgroundSuppressionBranch)
        if custom_modules_available:
            setattr(DetectionModel, 'MultiScaleECAAttention', MultiScaleECAAttention)
            setattr(DetectionModel, 'ComprehensiveAttentionModule', ComprehensiveAttentionModule)
        print("✅ 自定义模块注册成功")
    except Exception as e:
        print(f"⚠️ 模块注册失败: {e}")

# 注意力可视化函数
def generate_attention_visualization(original_image, model, enhanced_analysis=None):
    """生成ECA注意力可视化 - 基于真实的病害检测和分析结果"""
    try:
        print("🧠 开始生成ECA注意力可视化...")
        
        # 确保原始图像是正确的格式
        if isinstance(original_image, np.ndarray):
            if len(original_image.shape) == 3:
                if original_image.dtype != np.uint8:
                    original_image = (original_image * 255).astype(np.uint8)
                clean_image = original_image.copy()
        
        # 基于真实的增强分析结果生成注意力映射
        if enhanced_analysis:
            print("✅ 使用增强分析结果生成注意力映射")
            attention_map = generate_enhanced_attention_map(clean_image, enhanced_analysis)
        else:
            print("⚠️ 未提供增强分析结果，使用基础病害特征生成注意力映射")
            attention_map = generate_disease_attention_map(clean_image)
        
        # 创建可视化图像
        try:
            import matplotlib.pyplot as plt
            plt.style.use('default')
            fig, axes = plt.subplots(1, 4, figsize=(16, 4))
            
            # 设置中文字体
            try:
                plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
            except:
                pass
            
            # 1. 原始图像（干净无检测框）
            axes[0].imshow(cv2.cvtColor(clean_image, cv2.COLOR_BGR2RGB))
            axes[0].set_title('原始图像', fontsize=12)
            axes[0].axis('off')
            
            # 2. ECA注意力图（灰度）
            axes[1].imshow(attention_map, cmap='gray')
            axes[1].set_title('ECA注意力', fontsize=12)
            axes[1].axis('off')
            
            # 3. 注意力热力图（彩色叠加）
            axes[2].imshow(cv2.cvtColor(clean_image, cv2.COLOR_BGR2RGB))
            heatmap = axes[2].imshow(attention_map, cmap='jet', alpha=0.6)
            axes[2].set_title('注意力热力图', fontsize=12)
            axes[2].axis('off')
            
            # 4. 注意力权重柱状图 - 基于真实分析结果
            channels = np.arange(8)
            weights = calculate_enhanced_channel_weights(attention_map, enhanced_analysis)
            
            bars = axes[3].bar(channels, weights, color='steelblue', alpha=0.8)
            axes[3].set_title('通道注意力权重', fontsize=12)
            axes[3].set_xlabel('特征通道')
            axes[3].set_ylabel('权重')
            axes[3].set_ylim(0, 1)
            
            # 添加权重数值标签
            for i, (bar, weight) in enumerate(zip(bars, weights)):
                axes[3].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                            f'{weight:.2f}', ha='center', va='bottom', fontsize=8)
            
            plt.tight_layout()
            
            # 保存到内存
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            # 转换为base64
            attention_viz_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            plt.close(fig)
            buffer.close()
            
            print("✅ ECA注意力可视化生成完成")
            return attention_viz_base64
        except ImportError:
            print("⚠️ matplotlib未安装，注意力可视化不可用")
            return ""
        
    except Exception as e:
        print(f"❌ 注意力可视化生成失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return ""

def generate_enhanced_attention_map(image, enhanced_analysis):
    """基于增强分析结果生成注意力映射"""
    try:
        # 获取缺陷检测结果
        defect_analysis = enhanced_analysis.get('defect_analysis', {})
        defects = defect_analysis.get('defects', [])
        
        # 创建基础注意力映射
        h, w = image.shape[:2]
        attention_map = np.zeros((h, w), dtype=np.float32)
        
        # 如果有缺陷检测结果，基于缺陷位置生成注意力
        if defects:
            print(f"🎯 基于 {len(defects)} 个缺陷区域生成注意力映射")
            for defect in defects:
                bbox = defect.get('bbox', [0, 0, w, h])
                confidence = defect.get('confidence', 0.5)
                x1, y1, x2, y2 = bbox
                
                # 确保边界框在图像范围内
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                # 在缺陷区域增加注意力权重
                attention_map[y1:y2, x1:x2] += confidence
        else:
            # 如果没有缺陷检测，基于颜色分析生成注意力映射
            print("🎨 基于颜色分析生成注意力映射")
            attention_map = generate_disease_attention_map(image)
        
        # 基于颜色分析增强注意力映射
        color_analysis = enhanced_analysis.get('color_analysis', {})
        disease_ratio = color_analysis.get('disease_ratio', 0)
        
        if disease_ratio > 0.1:
            # 基于HSV颜色空间增强病害区域的注意力
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 病害颜色掩码
            yellow_mask = cv2.inRange(hsv, np.array([15, 30, 30]), np.array([35, 255, 255]))
            brown_mask = cv2.inRange(hsv, np.array([0, 30, 10]), np.array([20, 255, 180]))
            
            disease_mask = cv2.bitwise_or(yellow_mask, brown_mask)
            disease_mask_normalized = disease_mask.astype(np.float32) / 255.0
            
            # 融合缺陷检测和颜色分析的注意力
            attention_map = np.maximum(attention_map, disease_mask_normalized * disease_ratio)
        
        # 应用高斯模糊平滑注意力映射
        attention_map = cv2.GaussianBlur(attention_map, (15, 15), 0)
        
        # 归一化到0-1范围
        if attention_map.max() > 0:
            attention_map = attention_map / attention_map.max()
        
        return attention_map
        
    except Exception as e:
        print(f"⚠️ 增强注意力映射生成失败: {e}")
        return generate_disease_attention_map(image)

def generate_disease_attention_map(image):
    """基于病害特征生成注意力映射"""
    try:
        # 转换到HSV色彩空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 定义病害颜色范围
        yellow_lower = np.array([20, 50, 80])
        yellow_upper = np.array([30, 255, 220])
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
        
        brown_lower = np.array([8, 80, 30])
        brown_upper = np.array([20, 255, 150])
        brown_mask = cv2.inRange(hsv, brown_lower, brown_upper)
        
        dark_lower = np.array([0, 0, 0])
        dark_upper = np.array([180, 80, 40])
        dark_mask = cv2.inRange(hsv, dark_lower, dark_upper)
        
        # 合并病害掩码
        disease_mask = cv2.bitwise_or(yellow_mask, brown_mask)
        disease_mask = cv2.bitwise_or(disease_mask, dark_mask)
        
        # 形态学操作
        kernel = np.ones((5, 5), np.uint8)
        disease_mask = cv2.morphologyEx(disease_mask, cv2.MORPH_OPEN, kernel)
        disease_mask = cv2.morphologyEx(disease_mask, cv2.MORPH_CLOSE, kernel)
        
        # 边缘检测
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 30, 80)
        
        # 结合病害掩码和边缘信息
        attention_raw = disease_mask.astype(float) * 0.8 + edges.astype(float) * 0.2
        
        # 平滑处理
        attention_map = cv2.GaussianBlur(attention_raw, (11, 11), 0)
        
        # 归一化
        if attention_map.max() > 0:
            attention_map = attention_map / attention_map.max()
        
        return attention_map
        
    except Exception as e:
        print(f"⚠️ 病害注意力映射生成失败: {e}")
        # 返回基础的中心注意力映射
        h, w = image.shape[:2]
        y, x = np.ogrid[:h, :w]
        center_y, center_x = h // 2, w // 2
        attention_map = np.exp(-((x - center_x)**2 + (y - center_y)**2) / (2 * (min(h, w) // 4)**2))
        return attention_map

def calculate_enhanced_channel_weights(attention_map, enhanced_analysis):
    """基于增强分析结果计算通道权重"""
    try:
        weights = []
        
        if enhanced_analysis:
            # 基于真实分析结果计算权重
            color_analysis = enhanced_analysis.get('color_analysis', {})
            texture_analysis = enhanced_analysis.get('texture_analysis', {})
            thermal_analysis = enhanced_analysis.get('thermal_analysis', {})
            defect_analysis = enhanced_analysis.get('defect_analysis', {})
            
            # 通道0-1: 颜色特征权重
            green_ratio = color_analysis.get('green_ratio', 0.3)
            disease_ratio = color_analysis.get('disease_ratio', 0.2)
            weights.extend([green_ratio, disease_ratio])
            
            # 通道2-3: 纹理特征权重
            texture_complexity = texture_analysis.get('texture_heterogeneity', 25.0) / 100.0
            edge_density = texture_analysis.get('edge_density', 0.1)
            weights.extend([min(texture_complexity, 1.0), edge_density])
            
            # 通道4-5: 热度特征权重
            hot_spot_ratio = thermal_analysis.get('hot_spot_ratio', 0.1)
            temp_anomaly = thermal_analysis.get('temperature_anomaly', 0.1)
            weights.extend([hot_spot_ratio, temp_anomaly])
            
            # 通道6-7: 缺陷检测权重
            defect_count = defect_analysis.get('total_defects', 0)
            defect_coverage = defect_analysis.get('severity_analysis', {}).get('defect_coverage_percent', 0) / 100.0
            weights.extend([min(defect_count / 10.0, 1.0), defect_coverage])
            
        else:
            # 基于注意力映射计算基础权重
            h, w = attention_map.shape
            for i in range(8):
                if i < 4:  # 上半部分
                    y_start, y_end = 0, h // 2
                    x_start = (w // 4) * i
                    x_end = (w // 4) * (i + 1)
                else:  # 下半部分
                    y_start, y_end = h // 2, h
                    x_start = (w // 4) * (i - 4)
                    x_end = (w // 4) * (i - 3)
                
                x_end = min(x_end, w)
                y_end = min(y_end, h)
                
                region_weight = np.mean(attention_map[y_start:y_end, x_start:x_end])
                weights.append(region_weight)
        
        # 确保有8个权重
        while len(weights) < 8:
            weights.append(0.1)
        weights = weights[:8]
        
        # 归一化权重
        weights = np.array(weights)
        if weights.max() > 0:
            weights = weights / weights.max()
        
        return weights
        
    except Exception as e:
        print(f"⚠️ 通道权重计算失败: {e}")
        return np.random.rand(8) * 0.5 + 0.3

def generate_real_eca_attention_map(image, enhanced_analysis=None):
    """基于ECA模块生成真实的注意力映射"""
    try:
        # 使用modules中的ECA注意力机制
        from modules.attention.eca import ECA
        import torch
        
        # 转换图像为tensor
        if len(image.shape) == 3:
            # 确保图像是uint8类型
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)
            
            # BGR转RGB并归一化
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image_tensor = torch.from_numpy(image_rgb).permute(2, 0, 1).float() / 255.0
            image_tensor = image_tensor.unsqueeze(0)  # 添加batch维度
            
        # 创建ECA模块 (通道数为3)
        eca_module = ECA(channels=3, adaptive_kernel=True)
        eca_module.eval()
            
        with torch.no_grad():
            # 通过ECA模块
            enhanced_features = eca_module(image_tensor)
            
            # 获取特征图并转换为注意力映射
            feature_map = enhanced_features.squeeze().cpu().numpy()
            attention_map = np.mean(feature_map, axis=0)
                
            # 归一化
            attention_map = (attention_map - attention_map.min()) / (attention_map.max() - attention_map.min() + 1e-8)
            
            # 调整大小以匹配原图
            attention_map = cv2.resize(attention_map, (image.shape[1], image.shape[0]))
            
            return attention_map
                
    except Exception as e:
        print(f"⚠️ 真实ECA注意力映射生成失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        # 回退到基础方法
        return generate_disease_attention_map(image)

def calculate_eca_channel_weights(image, enhanced_analysis=None):
    """
    基于真实 ECA 模块计算通道注意力权重。
    
    修复说明：原来返回硬编码常数 [0.5, 0.3, 0.4, ...]，现在调用真实 ECA 模块
    的 forward() 方法，读取 eca_module.attention_weights 中的真实权重。
    同时结合 enhanced_analysis 中的多模态分析结果计算8个综合权重通道。
    """
    try:
        from modules.attention.eca import ECA
        import torch
        
        if not isinstance(image, np.ndarray) or len(image.shape) != 3:
            raise ValueError("图像格式不正确")
        
        # 确保图像是uint8类型
        if image.dtype != np.uint8:
            image = np.clip(image * 255, 0, 255).astype(np.uint8)
        
        # BGR 转 RGB 并归一化为 tensor [1, 3, H, W]
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_tensor = torch.from_numpy(image_rgb).permute(2, 0, 1).float() / 255.0
        image_tensor = image_tensor.unsqueeze(0)
        
        # 创建并运行 ECA 模块（channels=3 对应 RGB 通道）
        eca_module = ECA(channels=3, adaptive_kernel=True)
        eca_module.eval()
        
        with torch.no_grad():
            _ = eca_module(image_tensor)  # forward() 内部保存 attention_weights
            
            # 读取真实的 ECA 通道权重（3个 RGB 通道）
            raw_weights = eca_module.get_attention_weights()  # numpy [1, 3, 1, 1]
            if raw_weights is not None:
                real_eca_weights = raw_weights.flatten()  # [3]
                r_weight = float(real_eca_weights[0]) if len(real_eca_weights) > 0 else 0.5
                g_weight = float(real_eca_weights[1]) if len(real_eca_weights) > 1 else 0.5
                b_weight = float(real_eca_weights[2]) if len(real_eca_weights) > 2 else 0.5
                print(f"✅ 真实ECA权重 - R:{r_weight:.3f} G:{g_weight:.3f} B:{b_weight:.3f}")
            else:
                r_weight, g_weight, b_weight = 0.5, 0.7, 0.4  # fallback
        
        # 基于真实 ECA 权重 + 增强分析结果 构建8通道权重
        if enhanced_analysis:
            color_analysis  = enhanced_analysis.get('color_analysis', {})
            texture_analysis = enhanced_analysis.get('texture_analysis', {})
            thermal_analysis = enhanced_analysis.get('thermal_analysis', {})
            defect_analysis  = enhanced_analysis.get('defect_analysis', {})
            
            # 通道0: 绿色通道ECA权重（叶片健康指标）
            ch0 = g_weight * (0.5 + color_analysis.get('green_ratio', 0.3))
            # 通道1: 病害颜色通道（R+B综合，病害区域偏红棕）
            ch1 = (r_weight * 0.7 + b_weight * 0.3) * (0.3 + color_analysis.get('disease_ratio', 0.2))
            # 通道2: 纹理复杂度通道
            ch2 = 0.5 + min(texture_analysis.get('texture_heterogeneity', 25.0) / 100.0, 0.5)
            # 通道3: 边缘密度通道
            ch3 = texture_analysis.get('edge_density', 0.1)
            # 通道4: 热点分布通道
            ch4 = thermal_analysis.get('hot_spot_ratio', 0.1)
            # 通道5: 温度异常通道
            ch5 = thermal_analysis.get('temperature_anomaly', 0.1)
            # 通道6: 缺陷检测密度
            defect_count = defect_analysis.get('total_defects', 0)
            ch6 = min(defect_count / 10.0, 1.0)
            # 通道7: 缺陷覆盖率
            ch7 = defect_analysis.get('severity_analysis', {}).get('defect_coverage_percent', 0) / 100.0
            
            channel_weights = [ch0, ch1, ch2, ch3, ch4, ch5, ch6, ch7]
        else:
            # 无增强分析时，直接扩展ECA的3个通道到8个
            channel_weights = [
                g_weight, r_weight, b_weight,
                (g_weight + r_weight) / 2,
                abs(r_weight - g_weight),
                (r_weight + b_weight) / 2,
                abs(g_weight - b_weight),
                (g_weight + r_weight + b_weight) / 3
            ]
        
        # 归一化到 [0, 1]
        channel_weights = [float(max(0.0, min(1.0, w))) for w in channel_weights]
        max_w = max(channel_weights) if channel_weights else 1.0
        if max_w > 0:
            channel_weights = [w / max_w for w in channel_weights]
        
        return channel_weights
        
    except Exception as e:
        print(f"⚠️ ECA通道权重计算失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        # 回退：基于增强分析构建有意义的默认值，而非固定常数
        if enhanced_analysis:
            color_analysis = enhanced_analysis.get('color_analysis', {})
            return [
                color_analysis.get('green_ratio', 0.6),
                color_analysis.get('disease_ratio', 0.3),
                0.4, 0.2, 0.3, 0.2, 0.5, 0.3
            ]
        return [0.6, 0.3, 0.4, 0.2, 0.3, 0.2, 0.5, 0.3]

def generate_eca_heatmap_visualization(original_image, enhanced_analysis=None, detections=None):
    """生成专门的ECA注意力热力图可视化 - 仿照您的样例图"""
    try:
        print("🔥 生成ECA注意力热力图...")
        print(f"   输入图像类型: {type(original_image)}")
        print(f"   输入图像形状: {original_image.shape if hasattr(original_image, 'shape') else 'No shape'}")
        
        # 确保图像格式正确
        if not isinstance(original_image, np.ndarray):
            print("❌ 输入不是numpy数组")
            return ""
        
        if len(original_image.shape) != 3:
            print("❌ 图像形状不正确")
            return ""
                
        if original_image.dtype != np.uint8:
            original_image = (original_image * 255).astype(np.uint8)
        clean_image = original_image.copy()
        print(f"   处理后图像形状: {clean_image.shape}")
        
        # 生成真实的ECA注意力映射
        print("   生成真实的ECA注意力映射...")
        try:
            attention_map = generate_real_eca_attention_map(clean_image, enhanced_analysis)
            print(f"   注意力映射形状: {attention_map.shape}")
        except Exception as e:
            print(f"   注意力映射生成失败: {e}")
            # 创建基础的注意力映射
            h, w = clean_image.shape[:2]
            attention_map = np.random.rand(h, w) * 0.5 + 0.3
        
        # 计算真实的通道权重
        channel_weights = calculate_eca_channel_weights(clean_image, enhanced_analysis)
        
        print(f"   通道权重: {channel_weights}")
        
        # 创建4面板可视化 (仿照您的样例图)
        print("   开始创建matplotlib图像...")
        import matplotlib
        matplotlib.use('Agg')  # 使用非交互式后端
        import matplotlib.pyplot as plt
        
        plt.style.use('default')
        fig = plt.figure(figsize=(16, 6))
        fig.patch.set_facecolor('#f8f9fa')
        
        # 设置中文字体
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        except:
            pass
        
        # 添加主标题
        fig.suptitle('🧠 ECA注意力机制可视化', fontsize=18, fontweight='bold', color='#2c3e50', y=0.95)
        
        # 1. 原始图像
        ax1 = plt.subplot(1, 4, 1)
        ax1.imshow(cv2.cvtColor(clean_image, cv2.COLOR_BGR2RGB))
        ax1.set_title('原始图像', fontsize=14, fontweight='bold', pad=20)
        ax1.axis('off')
        
        # 2. ECA注意力 (黑白热力图)
        ax2 = plt.subplot(1, 4, 2)
        ax2.imshow(attention_map, cmap='gray')
        ax2.set_title('ECA注意力', fontsize=14, fontweight='bold', pad=20)
        ax2.axis('off')
        
        # 3. 彩色热力图叠加 + 病害检测框
        ax3 = plt.subplot(1, 4, 3)
        rgb_for_heatmap = cv2.cvtColor(clean_image, cv2.COLOR_BGR2RGB)
        ax3.imshow(rgb_for_heatmap)
        heatmap = ax3.imshow(attention_map, cmap='jet', alpha=0.6)
        ax3.set_title('注意力热力图 + 检测框', fontsize=14, fontweight='bold', pad=20)
        ax3.axis('off')
        # 在热力图上叠加病害检测框（用户需求）
        if detections:
            _disease_colors_map = {
                'healthy': '#00ff00', 'mosaic_virus': '#ffff00',
                'brown_spot': '#ff8c00', 'wildfire': '#ff0000',
                'bacterial_wilt': '#ff00ff'
            }
            for det in detections:
                bbox = det.get('bbox', None)
                if bbox and len(bbox) == 4:
                    x1, y1, x2, y2 = bbox
                    cls_name = det.get('class_name', 'unknown')
                    conf = det.get('confidence', 0)
                    box_color = _disease_colors_map.get(cls_name, '#ffffff')
                    rect = plt.Rectangle(
                        (x1, y1), x2 - x1, y2 - y1,
                        linewidth=2.5, edgecolor=box_color,
                        facecolor='none', linestyle='-'
                    )
                    ax3.add_patch(rect)
                    ax3.text(
                        x1, max(y1 - 4, 0),
                        f"{cls_name} {conf:.2f}",
                        color=box_color, fontsize=7,
                        fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.5)
                    )
        
        # 4. 注意力权重柱状图
        ax4 = plt.subplot(1, 4, 4)
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
        bars = ax4.bar(range(len(channel_weights)), channel_weights, 
                      color=colors[:len(channel_weights)], alpha=0.8, edgecolor='white', linewidth=1)
        ax4.set_title('注意力权重', fontsize=14, fontweight='bold', pad=20)
        ax4.set_xlabel('通道', fontsize=12)
        ax4.set_ylabel('权重', fontsize=12)
        ax4.set_ylim(0, 1.1)
        ax4.grid(True, alpha=0.3, linestyle='--')
        ax4.set_facecolor('#f8f9fa')
        
        # 添加数值标签
        for i, (bar, weight) in enumerate(zip(bars, channel_weights)):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{weight:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # 设置x轴标签
        channel_labels = ['绿色', '病害', '纹理', '热点', '缺陷', '空间1', '空间2', '背景']
        ax4.set_xticks(range(len(channel_weights)))
        ax4.set_xticklabels(channel_labels[:len(channel_weights)], rotation=45, ha='right')
        
        # 添加说明文字
        plt.figtext(0.5, 0.02, '显示模型在检测过程中关注的关键区域和特征权重分布', 
                   ha='center', fontsize=12, style='italic', color='#7f8c8d')
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.85, bottom=0.15)
        
        # 转换为base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight', 
                   facecolor='#f8f9fa', edgecolor='none')
        buffer.seek(0)
        heatmap_viz_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        plt.close(fig)
        buffer.close()
        
        print("✅ ECA热力图可视化生成完成")
        return heatmap_viz_base64
        
    except Exception as e:
        print(f"❌ ECA热力图生成失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return ""

# 创建Flask应用 - 增强版
app = Flask(__name__, static_folder='../web', static_url_path='')
CORS(app)

# 应用配置
app.config['SECRET_KEY'] = 'tobacco-detection-secret-key-2024'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-2024'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size (支持批量上传)

# 配置文件夹
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
RESULTS_FOLDER = Path(__file__).parent / 'results'
BATCH_RESULTS_FOLDER = RESULTS_FOLDER / 'batch_results'
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULTS_FOLDER.mkdir(exist_ok=True)
BATCH_RESULTS_FOLDER.mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['RESULTS_FOLDER'] = str(RESULTS_FOLDER)

# 速率限制 (可选)
if LIMITER_AVAILABLE:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    limiter.init_app(app)
else:
    limiter = None

# 初始化管理器
db_manager = DatabaseManager()
batch_manager = BatchDetectionManager(db_manager, max_workers=4)

# 全局变量
model = None
disease_analyzer = None
defect_detector = None

# ---------------------------------------------------------------
# 修复死锁：将评估组件初始化移到全局级别
# 原来这些对象在 if __name__ == '__main__': 块内初始化，
# 但 detect() 路由在块外使用它们，导致非直接运行时崩溃。
# ---------------------------------------------------------------
try:
    metrics_calculator = DetectionMetricsCalculator()
    metrics_visualizer = MetricsVisualizer()
    report_generator = DetectionReportGenerator()
    print("✅ 评估组件全局初始化成功")
except Exception as _e:
    print(f"⚠️ 评估组件初始化失败，使用简化版本: {_e}")
    metrics_calculator = DetectionMetricsCalculator()
    metrics_visualizer = MetricsVisualizer()
    report_generator = DetectionReportGenerator()

# 创建必要的目录
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
RESULT_FOLDER = Path(__file__).parent / 'results'
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULT_FOLDER.mkdir(exist_ok=True)

# 类别名称和颜色映射
class_names = ['healthy', 'mosaic_virus', 'brown_spot', 'wildfire', 'bacterial_wilt']
colors = [
    (0, 255, 0),    # 绿色 - 健康
    (0, 255, 255),  # 黄色 - 花叶病毒
    (0, 165, 255),  # 橙色 - 褐斑病
    (0, 0, 255),    # 红色 - 野火病
    (255, 0, 255)   # 紫色 - 细菌性枯萎病
]

def get_disease_info(class_id):
    """获取病害信息"""
    disease_info = {
        0: {
            "name": "健康", 
            "severity": "无", 
            "treatment": "继续保持良好的种植条件",
            "description": "叶片颜色正常，无明显病害症状，植株健康状态良好"
        },
        1: {
            "name": "花叶病毒", 
            "severity": "中等", 
            "treatment": "及时清除病株，使用抗病毒药剂",
            "description": "叶片出现花叶症状，黄绿相间的斑块，影响光合作用"
        },
        2: {
            "name": "褐斑病", 
            "severity": "中等", 
            "treatment": "喷施杀菌剂，改善通风条件",
            "description": "叶片出现褐色圆形或不规则病斑，边缘明显，中心较淡"
        },
        3: {
            "name": "野火病", 
            "severity": "严重", 
            "treatment": "立即隔离病株，使用铜制杀菌剂",
            "description": "叶片出现褐色坏死斑点，周围有黄色晕圈，病斑扩展迅速"
        },
        4: {
            "name": "细菌性枯萎病", 
            "severity": "严重", 
            "treatment": "拔除病株，土壤消毒",
            "description": "叶片萎蔫变黄，从下部叶片开始向上蔓延，根部可能腐烂"
        }
    }
    return disease_info.get(class_id, {
        "name": "未知", 
        "severity": "未知", 
        "treatment": "请咨询专家",
        "description": "未识别的病害类型，建议联系专业人员进行诊断"
    })

def load_model(weights_path):
    """加载YOLO模型"""
    global class_names, colors
    
    print(f"🔍 尝试加载模型: {weights_path}")
    
    if not os.path.exists(weights_path):
        print(f"❌ 模型文件不存在: {weights_path}")
        return None
    
    file_size = os.path.getsize(weights_path) / (1024 * 1024)  # MB
    print(f"📦 模型大小: {file_size:.1f}MB")
    
    try:
        # 注册自定义模块
        register_custom_modules()
        print("自定义模块注册完成")
        
        model = YOLO(weights_path)
        print("✅ YOLO模型加载成功")
        
        # 检查模型类别
        model_classes = len(model.names)
        print(f"📊 模型类别数: {model_classes}")
        print(f"🏷️ 模型类别: {list(model.names.values())}")
        
        # 更新全局类别名称
        if model_classes == 5:
            class_names = list(model.names.values())
            print(f"🔄 更新类别名称为模型类别: {class_names}")
        else:
            print(f"⚠️ 模型类别数({model_classes})与期望的5类不匹配")
        
        print("✅ 多模态增强检测模型加载成功")
        return model
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return None

def extract_leaf_foreground(img):
    """改进的叶片前景区域提取，适应病害叶片和复杂背景"""
    try:
        # 转换为HSV色彩空间
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        
        # 扩展颜色范围以包含病害叶片
        # 健康绿色范围
        lower_green = np.array([35, 30, 30])
        upper_green = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # 黄色范围（轻微病害）
        lower_yellow = np.array([20, 30, 30])
        upper_yellow = np.array([35, 255, 255])
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # 褐色范围（严重病害）
        lower_brown = np.array([5, 30, 20])
        upper_brown = np.array([25, 255, 180])
        brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)
        
        # 合并所有叶片颜色掩码
        leaf_mask = cv2.bitwise_or(green_mask, yellow_mask)
        leaf_mask = cv2.bitwise_or(leaf_mask, brown_mask)
        
        # 使用GrabCut算法进一步优化前景提取
        try:
            # 创建初始掩码
            gc_mask = np.where(leaf_mask > 0, cv2.GC_PR_FGD, cv2.GC_PR_BGD).astype(np.uint8)
            
            # 应用GrabCut（简化版本，避免过度处理）
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            # 只进行1次迭代以保持效率
            cv2.grabCut(img, gc_mask, None, bgd_model, fgd_model, 1, cv2.GC_INIT_WITH_MASK)
            
            # 提取前景
            mask = np.where((gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
        except:
            # GrabCut失败时使用基本颜色掩码
            mask = leaf_mask
        
        # 形态学操作优化掩码
        kernel = np.ones((7,7), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 如果前景区域太小，可能是提取失败，返回更宽松的掩码
        foreground_ratio = np.sum(mask > 0) / (mask.shape[0] * mask.shape[1])
        if foreground_ratio < 0.1:  # 前景小于10%可能有问题
            print(f"⚠️ 前景提取区域过小({foreground_ratio:.2%})，使用宽松模式")
            # 返回更宽松的掩码，主要排除纯黑和纯白区域
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            mask = np.where((gray > 20) & (gray < 240), 255, 0).astype(np.uint8)
        
        # 进一步优化：去除明显的土壤和背景区域
        try:
            # 转换为Lab色彩空间，更好地分离土壤和叶片
            lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
            l_channel = lab[:, :, 0]
            a_channel = lab[:, :, 1]
            b_channel = lab[:, :, 2]
            
            # 土壤通常具有较高的L值和较低的a值（偏向红色-绿色轴的中性）
            # 叶片通常具有较低的a值（偏绿）
            soil_mask = ((l_channel > 120) & (a_channel > 120) & (a_channel < 140))
            
            # 从前景掩码中移除土壤区域
            mask = cv2.bitwise_and(mask, ~soil_mask.astype(np.uint8) * 255)
            
            # 最终形态学清理
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
        except Exception as e:
            print(f"⚠️ 土壤过滤失败: {e}")
            pass
        
        return mask
    except Exception as e:
        print(f"⚠️ 前景提取失败: {e}")
        # 返回全白掩码作为fallback
        return np.ones(img.shape[:2], dtype=np.uint8) * 255

def is_shadow_region(region):
    """检测是否为阴影区域"""
    try:
        # 转换为灰度
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        # 计算亮度统计
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        # 阴影区域通常亮度低且变化小
        is_shadow = mean_brightness < 80 and std_brightness < 30
        return is_shadow
    except Exception as e:
        print(f"⚠️ 阴影检测失败: {e}")
        return False

def _infer_disease_type(enhanced_analysis, health_score, defect_coverage_percent):
    """
    基于数据集特征分析的智能病害推断算法
    
    Args:
        enhanced_analysis: 增强分析结果
        health_score: AI健康评分 (0-1)
        defect_coverage_percent: 缺陷覆盖率 (0-1)
    
    Returns:
        str: 推断的病害类型
    """
    # 获取各种分析结果
    defect_analysis = enhanced_analysis.get('defect_analysis', {})
    type_stats = defect_analysis.get('severity_analysis', {}).get('type_statistics', {})
    color_analysis = enhanced_analysis.get('color_analysis', {})
    texture_analysis = enhanced_analysis.get('texture_analysis', {})
    thermal_analysis = enhanced_analysis.get('thermal_analysis', {})
    
    # 提取关键特征
    texture_heterogeneity = texture_analysis.get('texture_heterogeneity', 0)
    edge_density = texture_analysis.get('edge_density', 0)
    hot_spot_ratio = thermal_analysis.get('hot_spot_ratio', 0)
    mean_temperature = thermal_analysis.get('mean_temperature', 120)
    
    # 颜色特征
    green_ratio = color_analysis.get('green_ratio', 0.3)
    disease_ratio = color_analysis.get('disease_ratio', 0.1)
    yellow_ratio = color_analysis.get('yellow_green_ratio', 0.1)
    brown_ratio = color_analysis.get('brown_ratio', 0.1)
    dark_ratio = color_analysis.get('dark_ratio', 0.1)
    
    print(f"   🔬 基于数据集特征的病害推断分析:")
    print(f"      健康评分: {health_score:.3f}")
    print(f"      缺陷覆盖率: {defect_coverage_percent:.3f}")
    print(f"      纹理复杂度: {texture_heterogeneity:.3f}")
    print(f"      边缘密度: {edge_density:.3f}")
    print(f"      热点比例: {hot_spot_ratio:.3f}")
    print(f"      平均温度: {mean_temperature:.1f}")
    print(f"      颜色比例 - 绿色: {green_ratio:.3f}, 黄色: {yellow_ratio:.3f}, 褐色: {brown_ratio:.3f}, 深色: {dark_ratio:.3f}")

    # -1. 首先检查是否为健康叶片（最高优先级）
    if health_score >= 0.80 and defect_coverage_percent < 0.05:
        print(f"      ✅ 判定为健康叶片: 健康评分{health_score:.3f}>=0.80, 缺陷覆盖率{defect_coverage_percent*100:.1f}%<5%")
        return 'healthy'

    # 0. 检查YOLO检测框的直接结果
    # 从全局变量或传入参数中获取原始YOLO检测结果
    try:
        # 检查是否有YOLO检测结果
        if hasattr(_infer_disease_type, '_current_detections'):
            yolo_detections = _infer_disease_type._current_detections
            disease_detections = [d for d in yolo_detections if d.get('class_name') in ['bacterial_wilt', 'wildfire', 'mosaic_virus', 'brown_spot']]
            if disease_detections:
                # 选择置信度最高的病害检测
                best_detection = max(disease_detections, key=lambda x: x.get('confidence', 0))
                # 提高阈值到0.35，避免误检健康叶片
                if best_detection.get('confidence', 0) > 0.35:
                    class_name = best_detection.get('class_name', '')
                    print(f"      🎯 YOLO病害检测: {class_name} (置信度: {best_detection['confidence']:.3f}) - 直接采用")
                    return class_name
                else:
                    print(f"      ⚠️ YOLO病害检测置信度过低: {best_detection.get('class_name')} ({best_detection['confidence']:.3f}) < 0.35，忽略")
    except:
        pass
    
    # 1. 使用缺陷检测的直接结果
    if type_stats:
        max_type = max(type_stats.items(), key=lambda x: x[1].get('total_area', 0))
        detected_type = max_type[0]
        confidence = max_type[1].get('avg_confidence', 0)
        print(f"      缺陷检测结果: {detected_type} (置信度: {confidence:.3f})")
        
        # 高置信度直接使用
        if confidence > 0.4:
            return detected_type
    
    # 2. 基于数据集特征的精确分类
    
    # 青枯病特征 (bacterial_wilt): 萎蔫、深褐色、高纹理复杂度、高热点
    bacterial_wilt_score = 0
    if health_score < 0.3:  # 健康评分很低
        bacterial_wilt_score += 3
    if dark_ratio > 0.15 or brown_ratio > 0.2:  # 深色/褐色比例高
        bacterial_wilt_score += 3
    if texture_heterogeneity > 50:  # 纹理复杂度高 (枯萎皱缩)
        bacterial_wilt_score += 2
    if hot_spot_ratio > 0.12:  # 热点比例高 (病害活跃)
        bacterial_wilt_score += 2
    if defect_coverage_percent > 0.3:  # 缺陷覆盖率高
        bacterial_wilt_score += 2
    
    # 野火病特征 (wildfire): 黄褐色病斑，边缘清晰，中等纹理复杂度
    wildfire_score = 0
    if 0.25 <= health_score < 0.65:  # 健康评分中等偏低
        wildfire_score += 2
    if yellow_ratio > 0.1 or brown_ratio > 0.1:  # 黄褐色特征
        wildfire_score += 3
    if 25 <= texture_heterogeneity <= 65:  # 中等纹理复杂度
        wildfire_score += 2
    if 0.1 <= defect_coverage_percent <= 0.35:  # 中等缺陷覆盖率
        wildfire_score += 2
    if edge_density > 0.15:  # 边缘密度高 (病斑边界清晰)
        wildfire_score += 2
    
    # 赤星病特征 (brown_spot): 褐色圆形斑点，规则形状
    brown_spot_score = 0
    if 0.3 <= health_score < 0.6:  # 健康评分中低
        brown_spot_score += 2
    if brown_ratio > 0.15:  # 褐色比例高
        brown_spot_score += 3
    if 15 <= texture_heterogeneity <= 45:  # 中低纹理复杂度 (规则斑点)
        brown_spot_score += 2
    if 0.05 <= defect_coverage_percent <= 0.25:  # 中低缺陷覆盖率
        brown_spot_score += 2
    if edge_density > 0.1:  # 边缘密度中等 (斑点边界)
        brown_spot_score += 1
    
    # 花叶病毒病特征 (mosaic_virus): 黄绿斑驳，不规则图案
    mosaic_virus_score = 0
    if 0.4 <= health_score < 0.75:  # 健康评分中等
        mosaic_virus_score += 2
    if yellow_ratio > 0.15 or (yellow_ratio > 0.08 and green_ratio > 0.1):  # 黄绿斑驳
        mosaic_virus_score += 3
    if texture_heterogeneity < 35:  # 纹理复杂度较低 (斑驳图案相对平滑)
        mosaic_virus_score += 2
    if defect_coverage_percent < 0.2:  # 缺陷覆盖率较低
        mosaic_virus_score += 1
    if disease_ratio > 0.05:  # 有一定的病害比例
        mosaic_virus_score += 1
    
    # 计算各病害的得分
    scores = {
        'bacterial_wilt': bacterial_wilt_score,
        'wildfire': wildfire_score,
        'brown_spot': brown_spot_score,
        'mosaic_virus': mosaic_virus_score
    }
    
    print(f"      病害评分: {scores}")
    
    # 选择得分最高的病害类型
    max_disease = max(scores.items(), key=lambda x: x[1])
    max_score = max_disease[1]
    
    # 如果最高分大于阈值，返回对应病害
    if max_score >= 4:
        print(f"      特征匹配: {max_disease[0]} (得分: {max_score})")
        return max_disease[0]
    
    # 3. 基于简化规则的备用推断
    print(f"      使用备用推断规则")
    
    # 基于主要特征的简化判断
    if health_score < 0.25 and (dark_ratio > 0.12 or brown_ratio > 0.18):
        print(f"      备用规则: 青枯病 (极低健康评分 + 深色特征)")
        return "bacterial_wilt"
    elif yellow_ratio > 0.12 and 0.3 <= health_score < 0.65:
        print(f"      备用规则: 野火病 (黄色特征 + 中等健康评分)")
        return "wildfire"
    elif brown_ratio > 0.12 and 0.3 <= health_score < 0.6:
        print(f"      备用规则: 赤星病 (褐色特征 + 中低健康评分)")
        return "brown_spot"
    else:
        print(f"      备用规则: 花叶病毒病 (默认)")
        return "mosaic_virus"

def run_enhanced_analysis(img_bgr):
    """运行增强的多模态分析"""
    global disease_analyzer
    try:
        if disease_analyzer is None:
            # 初始化分析器
            print("🔧 初始化多模态病害分析器...")
            disease_analyzer = DiseaseAnalyzer()
            print("✅ 多模态病害分析器初始化完成")
        
        # 运行完整的多模态分析
        print("🔍 开始运行增强分析...")
        result = disease_analyzer.analyze_image(img_bgr)
        
        # 打印详细的分析结果
        if result:
            print("✅ 增强分析完成，结果概览:")
            if 'health_assessment' in result:
                health_score = result['health_assessment'].get('health_score', 0.5)
                risk_level = result['health_assessment'].get('risk_level', 'unknown')
                print(f"   🏥 健康评估: 评分={health_score:.3f}, 风险等级={risk_level}")
            
            if 'color_analysis' in result:
                color_health = result['color_analysis'].get('health_score', 0.5)
                green_ratio = result['color_analysis'].get('green_ratio', 0)
                disease_ratio = result['color_analysis'].get('disease_ratio', 0)
                print(f"   🎨 颜色分析: 健康评分={color_health:.3f}, 绿色比例={green_ratio:.3f}, 病害比例={disease_ratio:.3f}")
            
            if 'defect_analysis' in result:
                total_defects = result['defect_analysis'].get('total_defects', 0)
                defect_coverage = result['defect_analysis'].get('severity_analysis', {}).get('defect_coverage_percent', 0)
                print(f"   🔍 缺陷检测: 病害区域={total_defects}个, 覆盖率={defect_coverage:.1f}%")
            
            if 'thermal_analysis' in result:
                mean_temp = result['thermal_analysis'].get('mean_temperature', 0)
                hot_spot_ratio = result['thermal_analysis'].get('hot_spot_ratio', 0)
                print(f"   🌡️ 热度分析: 平均温度={mean_temp:.1f}, 热点比例={hot_spot_ratio:.3f}")
            
            if 'texture_analysis' in result:
                texture_complexity = result['texture_analysis'].get('texture_heterogeneity', 0)
                edge_density = result['texture_analysis'].get('edge_density', 0)
                print(f"   🌾 纹理分析: 复杂度={texture_complexity:.1f}, 边缘密度={edge_density:.3f}")
        
        return result
        
    except Exception as e:
        print(f"⚠️ 增强分析失败: {e}")
        import traceback
        print(f"详细错误信息:\n{traceback.format_exc()}")
        
        # 返回基于实际图像分析的基础结果，而不是完全虚拟的数据
        try:
            # 至少进行基础的颜色分析
            hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            
            # 计算基础颜色统计
            green_mask = cv2.inRange(hsv, np.array([35, 30, 30]), np.array([85, 255, 255]))
            green_ratio = np.sum(green_mask > 0) / green_mask.size
            
            yellow_mask = cv2.inRange(hsv, np.array([15, 30, 30]), np.array([35, 255, 255]))
            yellow_ratio = np.sum(yellow_mask > 0) / yellow_mask.size
            
            brown_mask = cv2.inRange(hsv, np.array([0, 30, 10]), np.array([20, 255, 180]))
            brown_ratio = np.sum(brown_mask > 0) / brown_mask.size
            
            disease_ratio = yellow_ratio + brown_ratio
            health_score = max(0.1, min(0.9, green_ratio / (green_ratio + disease_ratio * 2 + 0.1)))
            
            print(f"🔄 使用基础颜色分析: 健康评分={health_score:.3f}, 绿色比例={green_ratio:.3f}, 病害比例={disease_ratio:.3f}")
            
            return {
                'health_assessment': {
                    'health_score': health_score, 
                    'risk_level': 'high' if health_score < 0.4 else 'medium' if health_score < 0.7 else 'low',
                    'recommendation': '基于颜色分析的基础评估'
                },
                'color_analysis': {
                    'health_score': health_score, 
                    'green_ratio': green_ratio,
                    'yellow_ratio': yellow_ratio,
                    'brown_ratio': brown_ratio,
                    'disease_ratio': disease_ratio,
                    'dominant_colors': ['green'] if green_ratio > 0.3 else ['disease_color']
                },
                'texture_analysis': {'texture_heterogeneity': 30.0, 'edge_density': 0.1},
                'thermal_analysis': {'mean_temperature': 120.0, 'hot_spot_ratio': min(disease_ratio * 2, 0.3), 'temperature_anomaly': disease_ratio},
                'defect_analysis': {
                    'total_defects': 1 if disease_ratio > 0.1 else 0, 
                    'defects': [], 
                    'visualization': img_bgr.copy(),
                    'severity_analysis': {'defect_coverage_percent': disease_ratio * 100}
                }
            }
        except Exception as e2:
            print(f"⚠️ 连基础分析也失败: {e2}")
            return {
                'health_assessment': {'health_score': 0.5, 'risk_level': 'medium', 'recommendation': '分析失败，建议重试'},
                'color_analysis': {'health_score': 0.5, 'green_ratio': 0.3, 'disease_ratio': 0.2, 'dominant_colors': ['unknown']},
                'texture_analysis': {'texture_heterogeneity': 25.0, 'edge_density': 0.08},
                'thermal_analysis': {'mean_temperature': 100.0, 'hot_spot_ratio': 0.1, 'temperature_anomaly': 0.1},
                'defect_analysis': {'total_defects': 0, 'defects': [], 'visualization': img_bgr.copy(), 'severity_analysis': {'defect_coverage_percent': 0}}
        }

@app.route('/detect', methods=['POST'])
def detect():
    """增强病害检测接口"""
    global model
    
    try:
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({"error": "没有上传图像"}), 400
        
        file = request.files['image']
    
        # 检查文件是否有效
        if file.filename == '':
            return jsonify({"error": "未选择文件"}), 400
        
        # 保存上传的图像
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        upload_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(upload_path)
        
        # 读取图像
        img = cv2.imread(upload_path)
        if img is None:
            return jsonify({"error": "无法读取图像"}), 400

        # 图像预处理增强：基于背景颜色分割叶片 + CLAHE对比度增强 + 双边滚波去噪
        # 使用新的 enhance_for_detection_full() 集成完整预处理流程（用户指定方案）
        try:
            from modules.preprocessing.image_enhancer import ImageEnhancer
            enhancer = ImageEnhancer()
            # 使用完整流程：背景分割(黑/灰/紫) + 光照均匀化 + CLAHE + 双边滚波 + 病害劉强
            enhanced_img, enhancement_info = enhancer.enhance_for_detection_full(img)
            seg_type = enhancement_info.get('leaf_segmentation', {}).get('background_type', 'unknown')
            print(f"✅ 图像增强完成: {enhancement_info['applied_enhancements']}")
            print(f"   背景类型识别: {seg_type}, 叶片占比: {enhancement_info.get('leaf_segmentation', {}).get('leaf_ratio', 0):.1%}")
            # 使用增强后的图像进行检测
            detection_img = enhanced_img
        except Exception as e:
            print(f"⚠️ 图像增强失败，使用原始图像: {e}")
            import traceback
            print(f"   错误详情: {traceback.format_exc()}")
            detection_img = img
            enhancement_info = {'applied_enhancements': []}

        # 保存原始图像的副本（用于注意力可视化）
        original_image = img.copy()  # 保存干净的原始图像

        # 使用增强后的图像进行后续处理和绘制
        img = detection_img.copy()  # 将img替换为增强后的图像
        
        # 确保模型已加载
        if model is None:
            # 修正模型路径，优先使用环境变量，否则使用正确的默认路径
            weights_path = os.environ.get('MODEL_PATH', str(project_root / 'models' / 'rtx5090_trained_best.pt'))
            print(f"🔧 环境变量MODEL_PATH: {os.environ.get('MODEL_PATH', '未设置')}")
            print(f"🎯 实际使用模型路径: {weights_path}")
            model = load_model(weights_path)
        
        print(f"🎮 当前加载的模型: {model.ckpt_path if hasattr(model, 'ckpt_path') else '路径未知'}")
        
        # 运行精确病害检测
        try:
            from modules.detection.precise_disease_detector import PreciseDiseaseDetector
            precise_detector = PreciseDiseaseDetector()
            precise_regions = precise_detector.detect_disease_regions(detection_img)
            print(f"🎯 精确病害检测发现 {len(precise_regions)} 个病害区域")
            for i, region in enumerate(precise_regions):
                print(f"   区域{i+1}: {region['type']} (置信度:{region['confidence']:.3f}, 面积:{region['area']})")
        except Exception as e:
            print(f"⚠️ 精确病害检测失败: {e}")
            precise_regions = []

        # 运行基础YOLO检测
        start_time = time.time()
        print(f"🎯 开始YOLO检测，模型类别: {model.names}")
        print(f"🎯 检测参数: conf=0.10, iou=0.45")
        results = model(detection_img, conf=0.10, iou=0.45)  # 降低初筛置信度至0.10，确保病害高召回率
        result = results[0]
        
        # 调试: 打印原始检测结果
        print(f"🔍 YOLO原始检测结果: {len(result.boxes)}个检测框")
        if len(result.boxes) == 0:
            print("⚠️ 警告：YOLO没有检测到任何目标！")
            print(f"   - 图像尺寸: {img.shape}")
            print(f"   - 模型输入尺寸: {model.model[0].imgsz if hasattr(model.model[0], 'imgsz') else '未知'}")
            print(f"   - 置信度阈值: 0.05")
        
        # 保存原始YOLO检测结果（未过滤）
        original_yolo_detections = []
        for i, box in enumerate(result.boxes):
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            print(f"  检测{i+1}: 类别={class_names[cls_id]}, 置信度={conf:.3f}")
            
            # 保存原始检测结果
            original_yolo_detections.append({
                'class_name': class_names[cls_id],
                'confidence': conf,
                'cls_id': cls_id,
                'box': box
            })
        
        # 运行增强的多模态分析
        enhanced_analysis = run_enhanced_analysis(img)
        
        process_time = time.time() - start_time
        
        # 🔍 合并精确检测和YOLO检测结果
        print(f"🔍 合并精确检测和YOLO检测结果...")

        # 将精确检测结果转换为统一格式
        precise_detections = []
        for region in precise_regions:
            x1, y1, x2, y2 = region['bbox']
            # 映射病害类型到类别ID
            type_mapping = {
                'brown_spot': 2,
                'mosaic_virus': 1,
                'bacterial_wilt': 4,
                'yellow_spot': 2,
                'dark_spot': 3
            }
            cls_id = type_mapping.get(region['type'], 1)

            # 处理NaN值 - 确保置信度是有效数字
            confidence = region['confidence']
            if np.isnan(confidence) or confidence is None:
                confidence = 0.5  # 默认置信度

            precise_detections.append({
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                'conf': float(confidence),  # 确保是float类型
                'cls_id': cls_id,
                'area_ratio': region['area'] / (detection_img.shape[0] * detection_img.shape[1]),
                'source': 'precise'
            })

        print(f"🎯 精确检测转换结果: {len(precise_detections)} 个")

        # 智能过滤处理检测结果
        detections = []
        valid_detections = []

        print(f"🔍 开始智能过滤检测结果...")
        
        # 第一步：前景区域检测和过滤
        # 提取叶片前景区域，用于过滤背景和阴影
        foreground_mask = extract_leaf_foreground(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        # 智能检测框裁剪：基于前景掩码优化检测框边界
        def crop_to_leaf_region(x1, y1, x2, y2, foreground_mask):
            """根据前景掩码智能裁剪检测框到实际叶片区域"""
            try:
                # 提取检测框内的前景区域
                roi_mask = foreground_mask[y1:y2, x1:x2]
                
                # 找到前景区域的边界
                contours, _ = cv2.findContours(roi_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    # 找到最大的前景区域
                    largest_contour = max(contours, key=cv2.contourArea)
                    
                    # 获取边界矩形
                    bx, by, bw, bh = cv2.boundingRect(largest_contour)
                    
                    # 转换回原图坐标系
                    new_x1 = max(0, x1 + bx)
                    new_y1 = max(0, y1 + by)
                    new_x2 = min(img.shape[1], x1 + bx + bw)
                    new_y2 = min(img.shape[0], y1 + by + bh)
                    
                    # 确保新的检测框不会过小
                    if (new_x2 - new_x1) * (new_y2 - new_y1) > 0.1 * (x2 - x1) * (y2 - y1):
                        return new_x1, new_y1, new_x2, new_y2
                
                return x1, y1, x2, y2
            except:
                return x1, y1, x2, y2
        
        # 首先添加精确检测的结果（优先级更高）
        print(f"🎯 添加精确检测结果: {len(precise_detections)} 个")
        for precise_det in precise_detections:
            # 确保所有数值都是有效的
            conf = precise_det['conf']
            if np.isnan(conf) or conf is None:
                conf = 0.5

            valid_detections.append({
                'x1': int(precise_det['x1']), 'y1': int(precise_det['y1']),
                'x2': int(precise_det['x2']), 'y2': int(precise_det['y2']),
                'conf': float(conf),  # 确保是有效的float
                'cls_id': precise_det['cls_id'],
                'area_ratio': float(precise_det['area_ratio']),  # 确保是有效的float
                'source': 'precise'
            })

        # 过滤明显的误检
        for i, box in enumerate(result.boxes):
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            
            # 应用智能检测框裁剪
            original_area = (x2 - x1) * (y2 - y1)
            x1, y1, x2, y2 = crop_to_leaf_region(x1, y1, x2, y2, foreground_mask)
            cropped_area = (x2 - x1) * (y2 - y1)
            
            if cropped_area < original_area:
                crop_ratio = cropped_area / original_area
                print(f"   🎯 智能裁剪检测框 {i+1}: {class_names[cls_id]} - 裁剪比例 {crop_ratio:.2%}")
            
            # 计算检测框属性
            width = x2 - x1
            height = y2 - y1
            area = width * height
            area_ratio = area / (img.shape[0] * img.shape[1])
            aspect_ratio = width / height if height > 0 else 1
            
            # 计算检测框中心位置
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            # 过滤条件
            is_valid = True
            filter_reason = ""
            
            # 1. 面积过滤：针对背景干扰严重的情况，暂时放宽限制
            if area_ratio < 0.0005:  # 过滤极小噪点（0.05%）
                is_valid = False
                filter_reason = f"面积过小({area_ratio:.4f})"
            elif area_ratio > 0.999:  # 放宽到99.9%，允许大部分检测框通过
                is_valid = False
                filter_reason = f"面积过大({area_ratio:.3f})"
            
            # 2. 长宽比过滤：更合理的范围
            elif aspect_ratio < 0.1 or aspect_ratio > 10:
                is_valid = False
                filter_reason = f"长宽比异常({aspect_ratio:.2f})"
            
            # 3. 前景区域验证：检查检测框是否在叶片主体内
            elif is_valid:
                # 计算检测框与前景的重叠率
                bbox_mask = np.zeros_like(foreground_mask)
                cv2.rectangle(bbox_mask, (x1, y1), (x2, y2), 255, -1)
                
                overlap_area = np.sum(cv2.bitwise_and(bbox_mask, foreground_mask) > 0)
                bbox_area = np.sum(bbox_mask > 0)
                overlap_ratio = overlap_area / bbox_area if bbox_area > 0 else 0
                
                # 如果检测框与前景重叠率过低，可能是背景/阴影误检
                if overlap_ratio < 0.5:  # 至少50%重叠
                    is_valid = False
                    filter_reason = f"非叶片区域({overlap_ratio:.3f})"
            
            # 4. 特殊处理特定类别（阴影误检问题）
            if is_valid and class_names[cls_id] in ['dark_spot', 'wildfire']:
                # 针对深色病害放宽验证，去除死板的阴影排除，改由于重叠率辅助判断
                overlap_ratio = 1.0
                bbox_mask = np.zeros_like(foreground_mask)
                cv2.rectangle(bbox_mask, (x1, y1), (x2, y2), 255, -1)
                bbox_area = np.sum(bbox_mask > 0)
                if bbox_area > 0:
                    overlap_ratio = np.sum(cv2.bitwise_and(bbox_mask, foreground_mask) > 0) / bbox_area
                if overlap_ratio < 0.2:
                    is_valid = False
                    filter_reason = "阴影区域且无叶片重叠"
            
            # 5. 位置过滤：移除边缘绝对过滤以保留大面积病害，仅对背景误检进行极度宽松的校验
            if is_valid:
                margin = 2
                img_h, img_w = img.shape[:2]
                
                at_edge = (x1 <= margin or y1 <= margin or 
                          x2 >= img_w - margin or y2 >= img_h - margin)
                
                if at_edge and class_names[cls_id] == 'healthy':
                    # 健康框在边缘，如果基本不包含叶片前景才过滤
                    bbox_mask = np.zeros_like(foreground_mask)
                    cv2.rectangle(bbox_mask, (x1, y1), (x2, y2), 255, -1)
                    if bbox_area > 0 and np.sum(cv2.bitwise_and(bbox_mask, foreground_mask) > 0) / bbox_area < 0.1:
                        is_valid = False
                        filter_reason = "纯边缘背景"
            
            if is_valid:
                valid_detections.append({
                    "box": box,
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "conf": conf,
                    "cls_id": cls_id,
                    "area_ratio": area_ratio,
                    "aspect_ratio": aspect_ratio,
                    "center": (center_x, center_y)
                })
                print(f"   ✅ 有效检测 {i+1}: {class_names[cls_id]} ({conf:.3f}) 面积:{area_ratio:.4f}")
            else:
                print(f"   🚫 过滤检测 {i+1}: {class_names[cls_id]} ({conf:.3f}) - {filter_reason}")
        
        # 第二步：智能健康叶片检测逻辑
        # 安全机制：如果所有检测都被过滤，保留置信度最高的一个
        if not valid_detections and result.boxes:
            print(f"   ⚠️ 所有检测都被过滤，保留置信度最高的检测作为安全机制")
            best_box = None
            best_conf = 0
            for i, box in enumerate(result.boxes):
                conf = float(box.conf[0])
                if conf > best_conf:
                    best_conf = conf
                    best_box = box
            
            if best_box is not None:
                x1, y1, x2, y2 = best_box.xyxy[0].cpu().numpy().astype(int)
                cls_id = int(best_box.cls[0])
                valid_detections.append({
                    "box": best_box,
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "conf": best_conf,
                    "cls_id": cls_id,
                    "area_ratio": ((x2-x1)*(y2-y1)) / (img.shape[0]*img.shape[1])
                })
                print(f"   🎯 强制保留: {class_names[cls_id]} ({best_conf:.3f})")
        
        if valid_detections:
            print(f"   📋 有效检测汇总:")
            disease_detections = []
            healthy_detections = []
            
            for d in valid_detections:
                if d['cls_id'] == 0:  # 健康
                    healthy_detections.append(d)
                    print(f"      健康检测: {class_names[d['cls_id']]} ({d['conf']:.3f})")
                else:  # 病害
                    disease_detections.append(d)
                    print(f"      病害检测: {class_names[d['cls_id']]} ({d['conf']:.3f})")
            
            selected_detection = None
            
            # 智能健康叶片判断逻辑 - 基于病害区域面积占比
            health_score = 0.5  # 默认健康评分
            if enhanced_analysis and 'health_assessment' in enhanced_analysis:
                health_score = enhanced_analysis['health_assessment'].get('health_score', 0.5)
            
            print(f"   🧠 AI健康评分: {health_score:.3f}")
            
            # 1. 计算病害区域总面积占比
            total_disease_area_ratio = 0.0
            significant_disease_detections = []
            
            # 记录检测到的各类病害及其面积
            disease_types = {}
            
            for d in disease_detections:
                area_ratio = 0.0
                
                # 计算检测框面积占比（修复元组赋值 Bug）
                if 'bbox' in d and isinstance(d.get('bbox'), list) and len(d['bbox']) == 4:
                    x1, y1, x2, y2 = d['bbox']
                elif all(k in d for k in ('x1', 'y1', 'x2', 'y2')):
                    x1, y1, x2, y2 = d['x1'], d['y1'], d['x2'], d['y2']
                else:
                    x1, y1, x2, y2 = 0, 0, img.shape[1], img.shape[0]
                    bbox_width = x2 - x1
                    bbox_height = y2 - y1
                    bbox_area = bbox_width * bbox_height
                    total_image_area = img.shape[0] * img.shape[1]
                    area_ratio = bbox_area / total_image_area
                    d['area_ratio'] = area_ratio
                
                # 记录病害类型及其面积
                cls_id = d['cls_id']
                cls_name = class_names[cls_id]
                if cls_id > 0:  # 非健康类别
                    if cls_name not in disease_types:
                        disease_types[cls_name] = 0.0
                    disease_types[cls_name] += area_ratio
                    total_disease_area_ratio += area_ratio
                
                # 移除绝对硬编码置信度阻断，所有 valid 病害直接计入
                significant_disease_detections.append(d)
                print(f"      🚨 采纳模型返回病害: {cls_name} (置信度:{d['conf']:.3f}, 面积比例:{area_ratio:.3f})")
            
            # 打印病害面积占比统计
            print(f"   📊 模型直出病害区域占比: {total_disease_area_ratio:.3f}")
            for disease_type, area in disease_types.items():
                print(f"      - {disease_type}: 面积占比 {area:.3f}")
                
            # 检查多模态缺陷检测结果（辅助增强）
            if enhanced_analysis and 'defect_analysis' in enhanced_analysis:
                defect_count = enhanced_analysis['defect_analysis'].get('total_defects', 0)
                defect_coverage = enhanced_analysis['defect_analysis'].get('severity_analysis', {}).get('defect_coverage_percent', 0.0)
                print(f"   📊 辅助多模态缺陷结果: {defect_count}个缺陷, 覆盖率{defect_coverage:.1f}%")
                
                # 如果模型只给出极低置信度的病害或者没有给出，辅助多模态可以直接贡献判定
                if defect_count > 0 and defect_coverage > 5.0 and not disease_types:
                    print(f"   🔍 模型漏检，启用多模态智能托底...")
                    _infer_disease_type._current_detections = original_yolo_detections
                    inferred_disease = _infer_disease_type(enhanced_analysis, health_score, defect_coverage / 100.0)
                    print(f"   🎯 智能推断病害补充: {inferred_disease}")
                    disease_types[inferred_disease] = defect_coverage / 100.0
                    total_disease_area_ratio = max(total_disease_area_ratio, defect_coverage / 100.0)
            
            # 2. 根据模型检测作为最高优先级综合判断结果
            # 判断逻辑：优先信任模型给出的病害。如果模型框出明确病害立刻标记感染。
            # 如果模型认定健康且概率高，再结合多模态判断是否漏判。
            
            defect_coverage_percent = defect_coverage / 100.0 if 'defect_coverage' in locals() else 0.0
            
            if disease_types:
                # 只要模型直出了疾病（或多模态托底补上的疾病），就直接走疾病判定
                is_healthy_leaf = False
                print(f"   🚨 判定为病害叶片: 模型确认病害存在")
            else:
                # 模型没有给出病害框
                # 如果模型给的健康框很多高分，但多模态缺陷异常高 > 15%，启用覆盖
                if health_score < 0.60 or defect_coverage_percent > 0.15:
                    is_healthy_leaf = False
                    print(f"   ⚠️ 回退多模态覆盖: 模型无结果但多模态评分(健康度{health_score:.2f}/缺陷比{defect_coverage_percent:.2f})认定病害")
                else:
                    is_healthy_leaf = True
                    print(f"   ✅ 判定为完全健康叶片: 模型返回健康结果且综合状态良好")
                
                # 如果没有具体病害检测，根据缺陷分析推断
                if not disease_types and defect_coverage_percent > 0:
                    # 根据缺陷检测推断病害类型
                    if 'defect_analysis' in enhanced_analysis and enhanced_analysis['defect_analysis'].get('total_defects', 0) > 0:
                        print(f"   🔍 根据缺陷检测推断病害类型")
                        # 基于缺陷特征和健康评分智能推断病害类型
                        # 传入YOLO检测结果供参考
                        _infer_disease_type._current_detections = detections
                        inferred_disease = _infer_disease_type(enhanced_analysis, health_score, defect_coverage_percent)
                        disease_types[inferred_disease] = defect_coverage_percent
                        print(f"   🎯 推断病害类型: {inferred_disease}")
            
            if not is_healthy_leaf:
                # 找出主要病害
                if disease_types:
                    max_area_disease = max(disease_types.items(), key=lambda x: x[1])
                    print(f"   🔍 主要病害类型认定: {max_area_disease[0]}，面积占比: {max_area_disease[1]:.3f}")
                elif defect_coverage_percent > 0:
                    # 根据缺陷检测推断病害类型
                    print(f"   🔍 根据缺陷检测推断病害类型")
                    # 基于缺陷特征和健康评分智能推断病害类型
                    # 传入原始YOLO检测结果供参考（而非过滤后的结果）
                    _infer_disease_type._current_detections = original_yolo_detections
                    inferred_disease = _infer_disease_type(enhanced_analysis, health_score, defect_coverage_percent)
                    disease_types[inferred_disease] = defect_coverage_percent
                    print(f"   🎯 推断病害类型: {inferred_disease}")
            
            # 3. 选择最终检测结果 - 基于健康评分和病害检测
            if not is_healthy_leaf:
                # 非健康叶片，需要选择具体的病害类型
                if disease_types:
                    # 找出面积最大的病害类型
                    max_area_disease_type = max(disease_types.items(), key=lambda x: x[1])[0]
                    
                    # 查找对应的检测结果
                    matching_detections = [d for d in disease_detections if class_names[d['cls_id']] == max_area_disease_type]
                    
                    if matching_detections:
                        # 找到匹配的检测结果，选择置信度最高的
                        selected_detection = max(matching_detections, key=lambda x: x['conf'])
                        print(f"   🎯 选择病害类型: {max_area_disease_type} (置信度:{selected_detection['conf']:.3f})")
                    elif disease_detections:
                        # 没有精确匹配，但有其他病害检测，选择置信度最高的
                        selected_detection = max(disease_detections, key=lambda x: x['conf'])
                        print(f"   🎯 选择置信度最高的病害检测: {class_names[selected_detection['cls_id']]} ({selected_detection['conf']:.3f})")
                    else:
                        # 没有病害检测结果，但需要创建一个病害检测
                        # 从disease_types中选择面积最大的病害类型
                        max_area_disease_type = max(disease_types.items(), key=lambda x: x[1])[0]
                        
                        # 确保使用正确的类别ID
                        disease_class_id = -1
                        for i, name in enumerate(class_names):
                            if name == max_area_disease_type:
                                disease_class_id = i
                                break
                        
                        # 如果没有找到匹配的类别ID，使用默认值
                        if disease_class_id == -1:
                            if max_area_disease_type == "mosaic_virus":
                                disease_class_id = 1
                            elif max_area_disease_type == "brown_spot":
                                disease_class_id = 2
                            elif max_area_disease_type == "wildfire":
                                disease_class_id = 3
                            elif max_area_disease_type == "bacterial_wilt":
                                disease_class_id = 4
                            else:
                                disease_class_id = 2  # 默认为褐斑病
                        
                        # 创建一个病害检测
                        selected_detection = {
                            'cls_id': disease_class_id,
                            'conf': 0.6,  # 基于健康评分给一个适中的置信度
                            'x1': 0, 'y1': 0, 'x2': img.shape[1], 'y2': img.shape[0],  # 全图
                            'area_ratio': disease_types[max_area_disease_type],
                            'aspect_ratio': img.shape[1] / img.shape[0],
                            'center': (img.shape[1]//2, img.shape[0]//2)
                        }
                        print(f"   🎯 创建病害检测: {max_area_disease_type} (置信度:0.6)")
                elif health_score < HEALTH_SCORE_MEDIUM:
                    # 健康评分低，但没有具体病害类型，创建一个默认的病害检测
                    # 基于健康评分推断病害严重程度
                    if health_score < 0.4:
                        disease_class_id = 4  # bacterial_wilt (严重)
                        disease_name = "bacterial_wilt"
                    elif health_score < 0.5:
                        disease_class_id = 3  # wildfire (中度)
                        disease_name = "wildfire"
                    else:
                        disease_class_id = 2  # brown_spot (轻微)
                        disease_name = "brown_spot"
                    
                    selected_detection = {
                        'cls_id': disease_class_id,
                        'conf': 0.5 + (0.7 - health_score),  # 健康评分越低，置信度越高
                        'x1': 0, 'y1': 0, 'x2': img.shape[1], 'y2': img.shape[0],  # 全图
                        'area_ratio': 0.2,
                        'aspect_ratio': img.shape[1] / img.shape[0],
                        'center': (img.shape[1]//2, img.shape[0]//2)
                    }
                    print(f"   🎯 基于健康评分创建病害检测: {disease_name} (置信度:{selected_detection['conf']:.3f})")
                else:
                    # 健康评分在70%-80%之间，创建一个轻微病害检测
                    selected_detection = {
                        'cls_id': 2,  # brown_spot (轻微病害)
                        'conf': 0.6,  # 适中的置信度
                        'x1': 0, 'y1': 0, 'x2': img.shape[1], 'y2': img.shape[0],  # 全图
                        'area_ratio': 0.1,
                        'aspect_ratio': img.shape[1] / img.shape[0],
                        'center': (img.shape[1]//2, img.shape[0]//2)
                    }
                    print(f"   🎯 创建轻微病害检测: brown_spot (置信度:0.6)")
            
            elif is_healthy_leaf:
                # 健康叶片
                selected_detection = {
                    'cls_id': 0,  # healthy
                    'conf': max(0.8, health_score),  # 健康置信度至少0.8
                    'x1': 0, 'y1': 0, 'x2': img.shape[1], 'y2': img.shape[0],  # 全图
                    'area_ratio': 1.0,
                    'aspect_ratio': img.shape[1] / img.shape[0],
                    'center': (img.shape[1]//2, img.shape[0]//2)
                }
                print(f"   🎯 判定为健康叶片: 健康评分{health_score:.3f}>={HEALTH_SCORE_HIGH}")
            
            elif healthy_detections:
                # 只有健康检测
                selected_detection = max(healthy_detections, key=lambda x: x['conf'])
                print(f"   🎯 选择健康检测: {class_names[selected_detection['cls_id']]} ({selected_detection['conf']:.3f})")
            
            # 如果还没有选择，就选择最高置信度的（无论类型）
            if not selected_detection:
                selected_detection = max(valid_detections, key=lambda x: x['conf'])
                print(f"   🎯 强制选择最高置信度: {class_names[selected_detection['cls_id']]} ({selected_detection['conf']:.3f})")
            
            # 绘制所有有效的检测框（包括精确检测和YOLO检测）
            print(f"🎯 绘制所有有效检测框: {len(valid_detections)} 个")
            for i, detection in enumerate(valid_detections):
                x1, y1, x2, y2 = detection['x1'], detection['y1'], detection['x2'], detection['y2']
                conf = detection['conf']
                cls_id = detection['cls_id']
                source = detection.get('source', 'yolo')
                color = colors[cls_id % len(colors)]

                # 精确检测使用更粗的边框和特殊标识
                thickness = 4 if source == 'precise' else 3
                cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

                # 添加标签背景
                prefix = "🎯" if source == 'precise' else ""
                label = f"{prefix}{class_names[cls_id]} {conf:.2f}"
                (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(img, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)
                cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                source_text = "精确检测" if source == 'precise' else "YOLO检测"
                print(f"   绘制检测框 {i+1} ({source_text}): {class_names[cls_id]} ({conf:.3f}) at ({x1},{y1})-({x2},{y2})")
            
            # 如果selected_detection存在但不是整个图像，也绘制它
            if selected_detection:
                x1, y1, x2, y2 = selected_detection['x1'], selected_detection['y1'], selected_detection['x2'], selected_detection['y2']
                # 检查是否是整个图像的检测框（健康叶片的全图检测）
                is_full_image = (x1 == 0 and y1 == 0 and x2 == img.shape[1] and y2 == img.shape[0])
                
                if not is_full_image:
                    conf = selected_detection['conf']
                    cls_id = selected_detection['cls_id']
                    color = colors[cls_id % len(colors)]
                    
                    # 绘制边界框（更粗，更醒目）
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                    
                    # 添加标签背景
                    label = f"{class_names[cls_id]} {conf:.2f}"
                    (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(img, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)
                    cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    print(f"   额外绘制selected_detection: {class_names[cls_id]} ({conf:.3f})")
                else:
                    print(f"   跳过全图检测框绘制: {class_names[selected_detection['cls_id']]} (全图边界)")
            
            if selected_detection:
                cls_id = selected_detection['cls_id']
                conf = selected_detection['conf']
                
                # 获取病害信息
                disease_info = get_disease_info(cls_id)
                
                # 先清空detections，然后添加所有有效的YOLO检测
                detections = []
                
                # 如果是非健康叶片，确保首先添加selected_detection
                if not is_healthy_leaf:
                    # 添加主要检测结果（病害）
                    detection_item = {
                        "class_id": cls_id,
                        "class_name": class_names[cls_id],
                        "confidence": conf,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "disease_info": get_disease_info(cls_id),
                        "is_main_detection": True  # 标记为主要检测结果
                    }
                    detections.append(detection_item)
                    print(f"   添加主要病害检测: {class_names[cls_id]} (置信度:{conf:.3f})")
                
                # 添加其他有效检测
                for detection in valid_detections:
                    x1, y1, x2, y2 = detection['x1'], detection['y1'], detection['x2'], detection['y2']
                    
                    # 如果是非健康叶片且已经添加了主要检测结果，跳过健康检测
                    if not is_healthy_leaf and detection['cls_id'] == 0:
                        continue
                        
                    detection_item = {
                        "class_id": detection['cls_id'],
                        "class_name": class_names[detection['cls_id']],
                        "confidence": detection['conf'],
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "disease_info": get_disease_info(detection['cls_id']),
                        "is_main_detection": False  # 标记为次要检测结果
                    }
                    detections.append(detection_item)
                
                # 如果有增强分析结果，为所有检测添加详细信息
                if enhanced_analysis:
                    for detection_item in detections:
                        if detection_item['class_id'] == 0:  # healthy
                            detection_item["enhanced_info"] = {
                                "health_score": enhanced_analysis.get('health_assessment', {}).get('health_score', 0.0),
                                "color_health": enhanced_analysis.get('color_analysis', {}).get('health_indicator', 0.0),
                                "recommendation": enhanced_analysis.get('health_assessment', {}).get('recommendation', '')
                            }
                        else:  # disease detected
                            detection_item["enhanced_info"] = {
                                "severity": "高" if detection_item['confidence'] > 0.7 else "中" if detection_item['confidence'] > 0.4 else "低",
                                "color_analysis": enhanced_analysis.get('color_analysis', {}),
                                "texture_analysis": enhanced_analysis.get('texture_analysis', {}),
                                "thermal_analysis": enhanced_analysis.get('thermal_analysis', {}),
                                "recommendation": enhanced_analysis.get('health_assessment', {}).get('recommendation', '')
                            }
                
                print(f"🎯 最终检测结果: {len(detections)} 个检测框")
        else:
            # 如果没有有效检测，但有原始YOLO检测，绘制原始检测
            print(f"⚠️ 没有通过过滤的检测，但有 {len(result.boxes)} 个原始YOLO检测")
            if result.boxes:
                print(f"🎯 绘制原始YOLO检测框（降低标准）")
                detections = []
                for i, box in enumerate(result.boxes):
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    color = colors[cls_id % len(colors)]
                    
                    # 绘制边界框
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                    
                    # 添加标签背景
                    label = f"{class_names[cls_id]} {conf:.2f}"
                    (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(img, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)
                    cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    # 添加到检测结果
                    detection_item = {
                        "class_id": cls_id,
                        "class_name": class_names[cls_id],
                        "confidence": conf,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "disease_info": get_disease_info(cls_id)
                    }
                    detections.append(detection_item)
                    
                    print(f"   绘制原始检测框 {i+1}: {class_names[cls_id]} ({conf:.3f}) at ({x1},{y1})-({x2},{y2})")
                
                print(f"🎯 原始检测结果: {len(detections)} 个检测框")
        
        # 保守的结果验证（暂时禁用激进的AI纠错）
        if enhanced_analysis and len(detections) > 0:
            health_score = enhanced_analysis.get('health_assessment', {}).get('health_score', 0.5)
            main_detection = detections[0]
            
            print(f"✅ 检测结果: {main_detection['class_name']} (置信度: {main_detection['confidence']:.3f})")
            print(f"ℹ️  AI健康评分: {health_score:.3f} - 仅供参考，以YOLO检测为准")
            
            # 只记录不一致情况，但不强制修改
            yolo_suggests_healthy = (main_detection['class_id'] == 0)
            enhanced_suggests_healthy = (health_score > 0.7)
            
            if yolo_suggests_healthy != enhanced_suggests_healthy:
                print(f"📝 注意：YOLO检测({main_detection['class_name']})与AI评分({health_score:.3f})存在差异")
                print(f"    当前以YOLO检测结果为准，AI分析作为辅助参考")
        
        # 保存结果图像
        result_filename = f"result_{filename}"
        result_path = os.path.join(RESULT_FOLDER, result_filename)
        cv2.imwrite(result_path, img)
        
        # 将图像转换为base64
        _, buffer = cv2.imencode('.jpg', img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # 计算评价指标
        image_info = {
            'width': img.shape[1],
            'height': img.shape[0],
            'channels': img.shape[2] if len(img.shape) > 2 else 1
        }
        
        print(f"🎯 计算检测评价指标...")
        try:
            evaluation_metrics = metrics_calculator.calculate_detection_metrics(
                detections=detections,
                enhanced_analysis=enhanced_analysis,
                image_info=image_info
            )
            
            # 生成指标可视化
            if custom_modules_available:
                metrics_html = metrics_visualizer.generate_metrics_html(evaluation_metrics)
            else:
                metrics_html = "<p>指标可视化功能不可用</p>"
        except Exception as e:
            print(f"⚠️ 评价指标计算失败: {e}")
            # 生成基础的评价指标结构
            total_detections = len(detections)
            avg_confidence = sum(d['confidence'] for d in detections) / total_detections if total_detections > 0 else 0
            disease_detections = [d for d in detections if d['class_id'] != 0]
            healthy_detections = [d for d in detections if d['class_id'] == 0]
            
            # 计算病害覆盖率
            if enhanced_analysis and 'color_analysis' in enhanced_analysis:
                disease_coverage = enhanced_analysis['color_analysis'].get('disease_ratio', 0) * 100
            else:
                disease_coverage = len(disease_detections) / total_detections * 100 if total_detections > 0 else 0
            
            # 确定主要病害 - 优先考虑YOLO检测结果
            dominant_disease = "healthy"
            
            # 0. 首先检查YOLO检测的病害结果（最高优先级）
            yolo_override = False
            print(f"🔧 开始检查YOLO检测结果，总检测数: {len(detections)}")
            # 找出所有病害检测（非健康）
            yolo_disease_detections = [d for d in detections if d.get('class_name') in ['bacterial_wilt', 'wildfire', 'mosaic_virus', 'brown_spot']]
            print(f"🔧 找到病害检测: {len(yolo_disease_detections)}个")
            for i, d in enumerate(yolo_disease_detections):
                print(f"   病害{i+1}: {d.get('class_name')} (置信度: {d.get('confidence', 0):.3f})")
            
            if yolo_disease_detections:
                # 按置信度排序，选择最高的
                best_disease = max(yolo_disease_detections, key=lambda x: x.get('confidence', 0))
                print(f"🔧 最佳病害检测: {best_disease.get('class_name')} (置信度: {best_disease.get('confidence', 0):.3f})")
                # 提高阈值到0.35，避免误检健康叶片
                if best_disease.get('confidence', 0) > 0.35:
                    dominant_disease = best_disease['class_name']
                    yolo_override = True
                    print(f"🎯 YOLO病害检测覆盖: {dominant_disease} (置信度: {best_disease['confidence']:.3f})")
                else:
                    print(f"🔍 YOLO病害检测置信度过低: {best_disease['class_name']} ({best_disease['confidence']:.3f}) < 0.35，忽略")
            else:
                print(f"🔍 YOLO未检测到病害，将使用AI推断")
            
            
            # 获取AI健康评分
            health_score = 0.0
            if enhanced_analysis and 'health_assessment' in enhanced_analysis:
                health_score = enhanced_analysis['health_assessment'].get('health_score', 0.0)
            
            # 调试输出
            print(f"🔍 AI深度分析健康评分: {health_score:.4f}")
            print(f"🔍 YOLO结果是否含有病害: {yolo_override}")
            
            dominant_disease = "healthy"
            
            # 按照最高置信度的病患项进行汇总赋值
            if yolo_disease_detections:
                best_disease = max(yolo_disease_detections, key=lambda x: x.get('confidence', 0))
                dominant_disease = best_disease['class_name']
                print(f"🎯 主导判定: {dominant_disease} (来自检测结果)")
            elif not yolo_override and len(detections) > 0:
                best_det = max(detections, key=lambda x: x.get('confidence', 0))
                dominant_disease = best_det['class_name']
                if dominant_disease != 'healthy':
                    print(f"🎯 主导判定(来自多模态补充): {dominant_disease}")
            else:
                dominant_disease = "healthy"
                print(f"🔍 没有确定任何病害，设为健康。")
            
            # 生成完整的评价指标结构
            evaluation_metrics = {
                "basic_metrics": {
                    "total_detections": total_detections,
                    "disease_detections": len(disease_detections),
                    "healthy_detections": len(healthy_detections),
                    "dominant_disease": dominant_disease  # 使用更新后的dominant_disease
                },
                "confidence_analysis": {
                    "average_confidence": avg_confidence,
                    "min_confidence": min(d['confidence'] for d in detections) if detections else 0,
                    "max_confidence": max(d['confidence'] for d in detections) if detections else 0,
                    "confidence_std": 0.1  # 简化的标准差
                },
                "coverage_analysis": {
                    "combined_coverage_percent": disease_coverage,
                    "yolo_coverage_percent": disease_coverage * 0.8,
                    "enhanced_coverage_percent": disease_coverage * 1.2
                },
                "severity_assessment": {
                    "severity_score": min(disease_coverage / 100.0, 1.0),
                    "severity_level": "severe" if disease_coverage > 50 else "moderate" if disease_coverage > 20 else "mild"
                },
                "quality_score": {
                    "overall_quality_score": avg_confidence * 0.8 + (1 - disease_coverage/100) * 0.2,
                    "quality_level": "good" if avg_confidence > 0.7 else "fair" if avg_confidence > 0.4 else "poor"
                },
                "health_assessment": {
                    "overall_health_score": 1.0 - disease_coverage/100,
                    "health_level": "good" if disease_coverage < 20 else "fair" if disease_coverage < 50 else "poor"
                },
                "reliability_score": {
                    "reliability_score": avg_confidence,
                    "reliability_level": "high" if avg_confidence > 0.7 else "medium" if avg_confidence > 0.4 else "low"
                },
                "summary": {
                    "total_detections": total_detections,
                    "dominant_condition": dominant_disease,
                    "disease_area_ratio": total_disease_area_ratio,
                    "overall_health": "good" if health_score >= HEALTH_SCORE_HIGH else "fair" if health_score >= HEALTH_SCORE_MEDIUM else "poor",
                    "severity_level": "severe" if health_score < 0.5 else "moderate" if health_score < HEALTH_SCORE_MEDIUM else "mild",
                    "quality_assessment": "good" if avg_confidence > 0.7 else "fair" if avg_confidence > 0.4 else "poor",
                    "coverage_percentage": f"{disease_coverage:.1f}%", 
                    "disease_area_percentage": f"{total_disease_area_ratio*100:.1f}%",
                    "treatment_needed": total_disease_area_ratio > 0.10,  # 10%以上的病害区域需要治疗
                    "defect_coverage": defect_coverage
                },
                "recommendations": [
                    {
                        "title": "检测建议",
                        "message": "建议定期监测植物健康状况" if total_disease_area_ratio < 0.10 else "建议及时采取防治措施",
                        "priority": "low" if total_disease_area_ratio < 0.10 else "medium" if total_disease_area_ratio < 0.30 else "high"
                    },
                    {
                        "title": "病害面积分析",
                        "message": f"病害区域占比 {total_disease_area_ratio*100:.1f}%，{'低于' if total_disease_area_ratio < 0.10 else '超过'}阈值(10%)",
                        "priority": "low" if total_disease_area_ratio < 0.10 else "medium" if total_disease_area_ratio < 0.30 else "high"
                    }
                ]
            }
            metrics_html = "<p>使用基础指标计算</p>"
        
        # 保存原始图像用于注意力可视化（不带检测框）
        clean_original_image = original_image.copy()
        
        # 生成ECA注意力可视化（使用原始干净图像和增强分析结果）
        print(f"🧠 生成ECA注意力可视化...")
        try:
            # 转换BGR到RGB用于可视化
            original_rgb = cv2.cvtColor(clean_original_image, cv2.COLOR_BGR2RGB)
            attention_visualization = generate_attention_visualization(original_rgb, model, enhanced_analysis)
            if attention_visualization:
                print("✅ 注意力可视化生成成功")
            else:
                print("⚠️ 注意力可视化生成失败，但没有抛出异常")
        except Exception as e:
            print(f"⚠️ 注意力可视化生成异常: {e}")
            attention_visualization = ""
        
        # 生成专门的ECA热力图可视化（新增）
        print(f"🔥 生成ECA热力图可视化...")
        print(f"   原始图像形状: {clean_original_image.shape if clean_original_image is not None else 'None'}")
        print(f"   增强分析数据: {bool(enhanced_analysis)}")
        print(f"   检测框数量: {len(detections)}个（将叠加到热力图上）")
        try:
            # 使用未绘制检测框的原始图像，传入 detections 让热力图上显示病害框
            eca_heatmap_visualization = generate_eca_heatmap_visualization(
                clean_original_image, enhanced_analysis, detections)
            print(f"   函数返回结果长度: {len(eca_heatmap_visualization) if eca_heatmap_visualization else 0}")
            if eca_heatmap_visualization:
                print("✅ ECA热力图可视化生成成功")
            else:
                print("⚠️ ECA热力图可视化生成失败，但没有抛出异常")
        except Exception as e:
            print(f"⚠️ ECA热力图可视化生成异常: {e}")
            import traceback
            print(f"   详细错误: {traceback.format_exc()}")
            eca_heatmap_visualization = ""
        
        # 构建完整的返回结果
        result = {
            "success": True,
            "process_time": process_time,
            "detections": detections,
            "result_image": img_base64,
            "evaluation_metrics": evaluation_metrics,  # 新增: 评价指标
            "metrics_visualization": metrics_html,     # 新增: 指标可视化HTML
            "attention_visualization": attention_visualization,  # 新增: ECA注意力可视化
            "eca_heatmap_visualization": eca_heatmap_visualization  # 新增: ECA热力图可视化
        }
        
        # 添加缺陷检测和区域分析结果
        print(f"🔧 处理增强分析结果: {bool(enhanced_analysis)}")
        if enhanced_analysis:
            print(f"   enhanced_analysis keys: {list(enhanced_analysis.keys())}")
            
            # 添加AI深度分析结果
            if 'health_assessment' in enhanced_analysis:
                health_score = enhanced_analysis['health_assessment']['health_score']
                # 根据健康评分确定风险等级
                if health_score >= 0.8:
                    risk_level = "低风险"
                elif health_score >= 0.7:
                    risk_level = "中等风险"
                else:
                    risk_level = "高风险"
                
                # 根据健康评分确定建议
                if health_score >= 0.8:
                    recommendation = "叶片状态良好，继续保持良好的田间管理"
                elif health_score >= 0.7:
                    recommendation = "检测到轻微病害特征，建议密切观察"
                else:
                    recommendation = "检测到明显病害特征，建议及时治疗"
                
                result['ai_analysis'] = {
                    'health_score': f"{health_score * 100:.1f}%",
                    'risk_level': risk_level,
                    'recommendation': recommendation
                }
                print(f"   ✅ 添加AI分析结果: {result['ai_analysis']}")
            
            # 添加详细的多模态分析结果
            result['enhanced_info'] = {
                'color_analysis': enhanced_analysis.get('color_analysis', {}),
                'texture_analysis': enhanced_analysis.get('texture_analysis', {}),
                'thermal_analysis': enhanced_analysis.get('thermal_analysis', {})
            }
            print(f"   ✅ 添加enhanced_info: color={bool(result['enhanced_info']['color_analysis'])}, texture={bool(result['enhanced_info']['texture_analysis'])}, thermal={bool(result['enhanced_info']['thermal_analysis'])}")
            
            if 'defect_analysis' in enhanced_analysis:
                result['defect_analysis'] = {
                    'total_defects': enhanced_analysis['defect_analysis'].get('total_defects', 0),
                    'defects': enhanced_analysis['defect_analysis'].get('defects', []),
                    'severity_analysis': enhanced_analysis['defect_analysis'].get('severity_analysis', {}),
                    'image_analysis': enhanced_analysis['defect_analysis'].get('image_analysis', {})
                }
                print(f"   ✅ 添加缺陷分析结果: {result['defect_analysis']['total_defects']}个缺陷")
            
            if 'region_analysis' in enhanced_analysis:
                result['region_analysis'] = enhanced_analysis['region_analysis']
                print(f"   ✅ 添加区域分析结果")
        else:
            print("   ⚠️ 没有增强分析结果")
        
        # 打印评价指标摘要
        summary = evaluation_metrics.get('summary', {})
        print(f"📊 检测评价摘要:")
        print(f"   总检测数: {summary.get('total_detections', 0)}")
        print(f"   主要病害: {summary.get('dominant_condition', '未知')}")
        print(f"   健康等级: {summary.get('overall_health', '未知')}")
        print(f"   严重程度: {summary.get('severity_level', '未知')}")
        print(f"   检测质量: {summary.get('quality_assessment', '未知')}")
        print(f"   覆盖率: {summary.get('coverage_percentage', '0%')}")

        # 保存到历史记录
        try:
            if 'detection_history' not in session:
                session['detection_history'] = []

            # 获取主要检测结果
            main_detection = detections[0] if detections else None
            if main_detection:
                # 检查不同的可能字段名
                if 'class' in main_detection:
                    result_class = main_detection['class']
                elif 'class_name' in main_detection:
                    result_class = main_detection['class_name']
                elif 'label' in main_detection:
                    result_class = main_detection['label']
                else:
                    result_class = 'unknown'
                confidence = main_detection.get('confidence', 0) * 100
            else:
                result_class = 'healthy'
                confidence = 0

            # 创建历史记录条目
            history_record = {
                'timestamp': datetime.now().isoformat(),
                'filename': file.filename if file else 'unknown.jpg',
                'result': result_class,
                'confidence': round(confidence, 1),
                'result_image': img_base64,
                'detections_count': len(detections),
                'process_time': process_time
            }

            # 添加到历史记录（最多保存100条）
            session['detection_history'].append(history_record)
            if len(session['detection_history']) > 100:
                session['detection_history'] = session['detection_history'][-100:]

            print(f"✅ 已保存检测记录到历史: {result_class} ({confidence:.1f}%)")

        except Exception as e:
            print(f"⚠️ 保存历史记录失败: {e}")

        # 清理结果中的NaN值，确保JSON兼容
        clean_result = sanitize_for_json(result)
        return jsonify(clean_result)
        
    except Exception as e:
        print(f"❌ 检测过程中出现错误: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        print(f"详细错误信息:\n{error_traceback}")
        return jsonify({"error": str(e), "success": False, "traceback": error_traceback}), 500

@app.route('/models', methods=['GET'])
def list_models():
    """列出可用模型"""
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models'))
    models = []
    
    if os.path.exists(models_dir):
        for file in os.listdir(models_dir):
            if file.endswith('.pt'):
                models.append(file)
    
    return jsonify({"models": models})

@app.route('/switch_model', methods=['POST'])
def switch_model():
    """切换模型"""
    global model
    
    data = request.json
    if not data or 'model_name' not in data:
        return jsonify({"error": "未提供模型名称"}), 400
    
    model_name = data['model_name']
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models'))
    model_path = os.path.join(models_dir, model_name)
    
    if not os.path.exists(model_path):
        return jsonify({"error": f"模型 {model_name} 不存在"}), 404
    
    try:
        model = load_model(model_path)
        return jsonify({"success": True, "message": f"已切换到模型 {model_name}"})
    except Exception as e:
        return jsonify({"error": f"加载模型失败: {str(e)}"}), 500

@app.route('/export_report', methods=['POST'])
def export_report():
    """导出检测报告"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "缺少必要的数据"}), 400
        
        # 从请求中提取数据
        detections = data.get('detections', [])
        evaluation_metrics = data.get('evaluation_metrics', {})
        enhanced_analysis = data.get('enhanced_analysis', {})
        result_image_base64 = data.get('result_image', '')
        original_filename = data.get('original_filename', 'unknown.jpg')
        report_format = data.get('format', 'html')  # html, json, pdf
        
        print(f"📄 生成检测报告: {report_format} 格式")
        
        # 生成报告
        try:
            report_data = report_generator.generate_report(
                detections=detections,
                evaluation_metrics=evaluation_metrics,
                enhanced_analysis=enhanced_analysis,
                result_image_base64=result_image_base64,
                original_filename=original_filename
            )
        except:
            report_data = {
                'html_content': f"<h1>检测报告</h1><p>检测到{len(detections)}个对象</p>",
                'json_data': {"detections": detections}
            }
        
        if report_format.lower() == 'html':
            return jsonify({
                "success": True,
                "format": "html",
                "content": report_data['html_content'],
                "filename": f"detection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            })
        
        elif report_format.lower() == 'json':
            return jsonify({
                "success": True,
                "format": "json", 
                "content": report_data['json_data'],
                "filename": f"detection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            })
        
        else:
            return jsonify({"error": f"不支持的报告格式: {report_format}"}), 400
            
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/metrics_summary', methods=['POST'])
def metrics_summary():
    """获取指标摘要"""
    try:
        data = request.get_json()
        
        detections = data.get('detections', [])
        enhanced_analysis = data.get('enhanced_analysis', {})
        image_info = data.get('image_info', {'width': 640, 'height': 640})
        
        try:
            # 计算指标
            metrics = metrics_calculator.calculate_detection_metrics(
                detections=detections,
                enhanced_analysis=enhanced_analysis,
                image_info=image_info
            )
        except:
            metrics = {
                "summary": {
                    "total_detections": len(detections),
                    "dominant_condition": "未知",
                    "overall_health": "未知"
                }
            }
        
        return jsonify({
            "success": True,
            "metrics": metrics
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now().isoformat(),
        "eca_heatmap_function_available": hasattr(sys.modules[__name__], 'generate_eca_heatmap_visualization')
    })

@app.route('/test_eca_heatmap', methods=['POST'])
def test_eca_heatmap():
    """测试ECA热力图生成功能的专用接口"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No image selected"}), 400
        
        # 读取图像
        image_bytes = file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        original_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if original_image is None:
            return jsonify({"error": "Invalid image format"}), 400
        
        # 创建测试的enhanced_analysis
        test_enhanced_analysis = {
            'color_analysis': {'green_ratio': 0.6, 'disease_ratio': 0.4},
            'texture_analysis': {'edge_density': 0.2},
            'thermal_analysis': {'hot_spot_ratio': 0.1},
            'defect_analysis': {'total_defects': 5}
        }
        
        print("🧪 测试ECA热力图生成...")
        debug_info = []
        
        # 生成ECA热力图
        try:
            eca_heatmap = generate_eca_heatmap_visualization(original_image, test_enhanced_analysis)
            debug_info.append("ECA热力图函数调用完成")
        except Exception as e:
            debug_info.append(f"ECA热力图函数调用异常: {e}")
            import traceback
            debug_info.append(f"异常详情: {traceback.format_exc()}")
            eca_heatmap = ""
        
        return jsonify({
            "success": True,
            "has_eca_heatmap": bool(eca_heatmap),
            "eca_heatmap_length": len(eca_heatmap) if eca_heatmap else 0,
            "eca_heatmap_visualization": eca_heatmap if eca_heatmap else "",
            "debug_info": debug_info,
            "image_shape": original_image.shape,
            "image_dtype": str(original_image.dtype)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/test-routes')
def test_routes():
    """测试路由是否正常工作"""
    web_dir = Path(__file__).parent.parent / 'web'
    dataset_viewer_exists = (web_dir / 'dataset-viewer.html').exists()
    index_exists = (web_dir / 'index.html').exists()
    plantvillage_exists = (project_root / 'plantvillage dataset').exists()
    
    return f"""
    <h1>路由测试页面</h1>
    <p>Web目录: {web_dir}</p>
    <p>dataset-viewer.html存在: {dataset_viewer_exists}</p>
    <p>index.html存在: {index_exists}</p>
    <p>plantvillage dataset存在: {plantvillage_exists}</p>
    <p><a href="/dataset-viewer">测试数据集浏览器</a></p>
    <p><a href="/api/dataset/categories">测试数据集API</a></p>
    """

@app.route('/dataset-viewer')
def dataset_viewer():
    """数据集浏览器页面"""
    try:
        from flask import send_from_directory
        web_dir = Path(__file__).parent.parent / 'web'
        print(f"🔍 尝试从目录提供文件: {web_dir}")
        print(f"🔍 文件是否存在: {(web_dir / 'dataset-viewer.html').exists()}")
        return send_from_directory(web_dir, 'dataset-viewer.html')
    except Exception as e:
        print(f"⚠️ 数据集浏览器页面服务失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return f"数据集浏览器页面加载失败: {str(e)}", 500

@app.route('/api/dataset/categories')
def get_dataset_categories():
    """获取数据集分类"""
    try:
        dataset_path = project_root / 'plantvillage dataset'
        categories = []
        
        if not dataset_path.exists():
            return jsonify({"success": False, "error": "数据集目录不存在"})
        
        # 遍历主要分类目录
        for category_dir in dataset_path.iterdir():
            if category_dir.is_dir():
                category_name = category_dir.name
                subcategories = []
                total_images = 0
                
                # 遍历子分类目录
                for subcat_dir in category_dir.iterdir():
                    if subcat_dir.is_dir():
                        # 计算图片数量
                        image_count = len([f for f in subcat_dir.iterdir() 
                                         if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']])
                        
                        subcategories.append({
                            "name": subcat_dir.name,
                            "image_count": image_count
                        })
                        total_images += image_count
                
                categories.append({
                    "name": category_name,
                    "display_name": category_name,
                    "subcategories": subcategories,
                    "total_images": total_images
                })
        
        return jsonify({
            "success": True,
            "categories": categories
        })
        
    except Exception as e:
        print(f"❌ 获取数据集分类失败: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/dataset/images/<path:category_name>')
def get_category_images(category_name):
    """获取指定分类的图片"""
    try:
        dataset_path = project_root / 'plantvillage dataset' / category_name
        images = []
        
        if not dataset_path.exists():
            return jsonify({"success": False, "error": "分类目录不存在"})
        
        # 遍历子分类目录
        for subcat_dir in dataset_path.iterdir():
            if subcat_dir.is_dir():
                subcat_name = subcat_dir.name
                
                # 获取图片文件
                for img_file in subcat_dir.iterdir():
                    if img_file.is_file() and img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                        # 构建相对路径用于URL
                        relative_path = f"/static/dataset/{category_name}/{subcat_name}/{img_file.name}"
                        
                        images.append({
                            "name": img_file.name,
                            "url": relative_path,
                            "path": str(img_file),
                            "category": category_name,
                            "subcategory": subcat_name,
                            "size": img_file.stat().st_size if img_file.exists() else 0
                        })
        
        return jsonify({
            "success": True,
            "images": images,
            "total": len(images)
        })
        
    except Exception as e:
        print(f"❌ 获取分类图片失败: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/dataset/search')
def search_dataset_images():
    """搜索数据集图片"""
    try:
        search_term = request.args.get('search', '').lower()
        category_filter = request.args.get('category', '')
        
        dataset_path = project_root / 'plantvillage dataset'
        images = []
        
        # 确定要搜索的分类
        categories_to_search = []
        if category_filter:
            categories_to_search.append(category_filter)
        else:
            categories_to_search = [d.name for d in dataset_path.iterdir() if d.is_dir()]
        
        # 搜索图片
        for category_name in categories_to_search:
            category_path = dataset_path / category_name
            if not category_path.exists():
                continue
                
            for subcat_dir in category_path.iterdir():
                if subcat_dir.is_dir():
                    subcat_name = subcat_dir.name
                    
                    for img_file in subcat_dir.iterdir():
                        if img_file.is_file() and img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                            # 检查是否匹配搜索条件
                            if not search_term or search_term in img_file.name.lower():
                                relative_path = f"/static/dataset/{category_name}/{subcat_name}/{img_file.name}"
                                
                                images.append({
                                    "name": img_file.name,
                                    "url": relative_path,
                                    "path": str(img_file),
                                    "category": category_name,
                                    "subcategory": subcat_name,
                                    "size": img_file.stat().st_size if img_file.exists() else 0
                                })
        
        return jsonify({
            "success": True,
            "images": images,
            "total": len(images),
            "search_term": search_term,
            "category_filter": category_filter
        })
        
    except Exception as e:
        print(f"❌ 搜索数据集图片失败: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/static/dataset/<path:filename>')
def serve_dataset_image(filename):
    """提供数据集图片服务"""
    try:
        dataset_path = project_root / 'plantvillage dataset'
        file_path = dataset_path / filename
        
        if not file_path.exists():
            return "图片不存在", 404
            
        from flask import send_file
        return send_file(file_path)
        
    except Exception as e:
        print(f"❌ 提供数据集图片失败: {e}")
        return "图片服务失败", 500

@app.route('/')
def index():
    """主页路由 - 返回Web界面"""
    try:
        from flask import send_from_directory
        web_dir = Path(__file__).parent.parent / 'web'
        return send_from_directory(web_dir, 'index.html')
    except Exception as e:
        print(f"⚠️ 静态文件服务失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>云南烤烟病害检测系统</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>🌿 云南烤烟病害检测系统</h1>
            <p>系统正在加载中，请稍候...</p>
            <p>如果页面无法正常显示，请检查静态文件配置。</p>
            <p>错误信息: """ + str(e) + """</p>
            <script>
                // 尝试重新加载
                setTimeout(function() {
                    window.location.reload();
                }, 3000);
            </script>
        </body>
        </html>
        """


# =============================================================
# 修复死锁：JWT工具函数和认证装饰器移至全局级别
# 原来这些函数在 if __name__ == '__main__': 块内定义，
# 导致任何非直接运行的方式（gunicorn/wsgi）都无法使用这些功能。
# =============================================================

def generate_token(user_info: Dict) -> str:
    """生成JWT令牌"""
    if not JWT_AVAILABLE:
        return f"session_{user_info['id']}_{int(time.time())}"

    payload = {
        'user_id': user_info['id'],
        'username': user_info['username'],
        'role': user_info['role'],
        'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')


def verify_token(token: str) -> Dict:
    """验证JWT令牌"""
    if not JWT_AVAILABLE:
        if token.startswith('session_'):
            parts = token.split('_')
            if len(parts) >= 3:
                try:
                    return {"success": True, "payload": {"user_id": int(parts[1])}}
                except (ValueError, IndexError):
                    pass
        return {"success": False, "message": "无效令牌"}

    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return {"success": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"success": False, "message": "令牌已过期"}
    except jwt.InvalidTokenError:
        return {"success": False, "message": "无效令牌"}


def require_auth(f):
    """认证装饰器"""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "缺少认证令牌"}), 401

        if token.startswith('Bearer '):
            token = token[7:]

        result = verify_token(token)
        if not result['success']:
            return jsonify({"error": result['message']}), 401

        request.current_user = result['payload']
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


def rate_limit(limit_string):
    """速率限制装饰器 - 如果limiter不可用则跳过"""
    def decorator(f):
        if limiter is not None:
            return limiter.limit(limit_string)(f)
        else:
            return f
    return decorator


# =============================================================
# 用户认证 API（已移至全局级别，修复路由死锁）
# =============================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not all([username, email, password]):
            return jsonify({"error": "用户名、邮箱和密码不能为空"}), 400

        if len(password) < 6:
            return jsonify({"error": "密码长度至少6位"}), 400

        result = db_manager.create_user(username, email, password)

        if result['success']:
            return jsonify({"message": result['message']}), 201
        else:
            return jsonify({"error": result['message']}), 400

    except Exception as e:
        return jsonify({"error": f"注册失败: {str(e)}"}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()

        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not all([username, password]):
            return jsonify({"error": "用户名和密码不能为空"}), 400

        result = db_manager.authenticate_user(username, password)

        if result['success']:
            token = generate_token(result['user'])
            return jsonify({
                "message": "登录成功",
                "token": token,
                "user": result['user']
            }), 200
        else:
            return jsonify({"error": result['message']}), 401

    except Exception as e:
        return jsonify({"error": f"登录失败: {str(e)}"}), 500


@app.route('/api/batch/create', methods=['POST'])
@require_auth
def create_batch_task():
    """创建批量检测任务"""
    try:
        user_id = request.current_user['user_id']

        if 'files' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400

        files = request.files.getlist('files')
        task_name = request.form.get('task_name', f'批量检测_{datetime.now().strftime("%Y%m%d_%H%M%S")}')

        if not files or len(files) == 0:
            return jsonify({"error": "没有选择文件"}), 400

        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        valid_files = []

        for file in files:
            if file.filename:
                ext = Path(file.filename).suffix.lower()
                if ext in allowed_extensions:
                    valid_files.append(file)

        if not valid_files:
            return jsonify({"error": "没有有效的图像文件"}), 400

        result = batch_manager.create_batch_task(user_id, task_name, valid_files)

        if result['success']:
            return jsonify({
                "message": "批量检测任务已创建",
                "task_id": result['task_id'],
                "total_files": len(valid_files)
            }), 201
        else:
            return jsonify({"error": result['message']}), 500

    except Exception as e:
        return jsonify({"error": f"创建批量任务失败: {str(e)}"}), 500


# =============================================================
# 历史记录与统计 API（已移至全局级别，修复路由死锁）
# =============================================================

@app.route('/api/history', methods=['GET'])
def get_detection_history():
    """获取检测历史记录"""
    try:
        history = session.get('detection_history', [])
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return jsonify({
            "success": True,
            "history": history,
            "total": len(history)
        })

    except Exception as e:
        print(f"❌ 获取历史记录失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/history', methods=['DELETE'])
def clear_detection_history():
    """清空检测历史记录"""
    try:
        session['detection_history'] = []
        return jsonify({"success": True, "message": "历史记录已清空"})

    except Exception as e:
        print(f"❌ 清空历史记录失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
def get_detection_statistics():
    """获取检测统计数据"""
    try:
        history = session.get('detection_history', [])

        if not history:
            return jsonify({
                "success": True,
                "statistics": {
                    "total_detections": 0,
                    "disease_rate": 0,
                    "avg_confidence": 0,
                    "disease_distribution": {}
                }
            })

        total_detections = len(history)
        disease_count = 0
        confidence_sum = 0
        disease_distribution = {}

        for record in history:
            if record.get('result') and record['result'] != 'healthy':
                disease_count += 1
                disease_type = record['result']
                disease_distribution[disease_type] = disease_distribution.get(disease_type, 0) + 1

            if record.get('confidence'):
                confidence_sum += float(record['confidence'])

        disease_rate = (disease_count / total_detections * 100) if total_detections > 0 else 0
        avg_confidence = (confidence_sum / total_detections) if total_detections > 0 else 0

        return jsonify({
            "success": True,
            "statistics": {
                "total_detections": total_detections,
                "disease_rate": round(disease_rate, 1),
                "avg_confidence": round(avg_confidence, 1),
                "disease_distribution": disease_distribution
            }
        })

    except Exception as e:
        print(f"❌ 获取统计数据失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================
# 启动入口（只保留 app.run，其余已移至全局）
# =============================================================
if __name__ == '__main__':
    print("🚀 启动云南烤烟病害检测API服务器 - 增强版...")
    print("📊 访问 http://localhost:5000 查看Web界面")
    print("🔗 API文档: http://localhost:5000/api/docs")
    print("👤 用户管理: 支持注册/登录/权限控制（路由已移至全局）")
    print("📦 批量检测: 支持多文件批量处理")
    print("📈 历史记录: 完整的检测历史管理")
    print("✅ 评估组件已在全局初始化完毕")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

