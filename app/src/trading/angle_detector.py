"""
黄线角度检测器 - 专门处理角度变化检测和交易信号生成
"""
import numpy as np
import time
from typing import Dict, List, Tuple
import logging

class AngleDetector:
    """黄线角度检测器"""
    
    def __init__(self, angle_threshold: float = 20.0, history_size: int = 10):
        """
        初始化角度检测器
        
        Args:
            angle_threshold: 角度变化阈值（度），超过此值触发交易信号
            history_size: 保存的历史数据点数量
        """
        self.angle_threshold = angle_threshold
        self.history_size = history_size
        self.angle_history = []
        self.logger = logging.getLogger(__name__)
        
    def set_angle_threshold(self, threshold: float):
        """设置角度阈值"""
        self.angle_threshold = threshold
        self.logger.info(f"角度阈值已设置为: {threshold}°")
        
    def calculate_line_angle(self, points: List[Tuple[int, int]]) -> float:
        """
        计算线条角度
        
        Args:
            points: 线条上的点列表 [(x1, y1), (x2, y2), ...]
            
        Returns:
            角度值（度）
        """
        if len(points) < 2:
            return 0.0
            
        # 使用线性回归计算更准确的角度
        x_coords = np.array([p[0] for p in points])
        y_coords = np.array([p[1] for p in points])
        
        if len(x_coords) > 1:
            # 线性回归拟合
            slope, intercept = np.polyfit(x_coords, y_coords, 1)
            angle_radians = np.arctan(slope)
            angle_degrees = np.degrees(angle_radians)
            
            # 标准化角度到 -90 到 90 度范围
            if angle_degrees > 90:
                angle_degrees = angle_degrees - 180
            elif angle_degrees < -90:
                angle_degrees = angle_degrees + 180
                
            return angle_degrees
        else:
            # 备用方法：使用首尾两点
            p1, p2 = points[0], points[-1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            
            if dx != 0:
                angle_radians = np.arctan(dy / dx)
                return np.degrees(angle_radians)
            else:
                return 90.0 if dy > 0 else -90.0
    
    def add_angle_data(self, angle: float, timestamp: float = None) -> Dict:
        """
        添加角度数据并检测变化
        
        Args:
            angle: 当前角度值
            timestamp: 时间戳，默认为当前时间
            
        Returns:
            检测结果字典
        """
        if timestamp is None:
            timestamp = time.time()
            
        # 添加到历史数据
        self.angle_history.append({
            'angle': angle,
            'timestamp': timestamp
        })
        
        # 保持历史数据大小
        if len(self.angle_history) > self.history_size:
            self.angle_history.pop(0)
            
        # 检测角度变化
        return self._detect_angle_change()
    
    def _detect_angle_change(self) -> Dict:
        """检测角度变化"""
        if len(self.angle_history) < 2:
            return {
                'signal': 'none',
                'direction': 'stable',
                'angle_change': 0.0,
                'confidence': 0.0,
                'current_angle': self.angle_history[-1]['angle'] if self.angle_history else 0.0
            }
            
        current = self.angle_history[-1]
        previous = self.angle_history[-2]
        
        angle_change = current['angle'] - previous['angle']
        
        # 处理角度跳跃（-180到180度边界问题）
        if angle_change > 180:
            angle_change -= 360
        elif angle_change < -180:
            angle_change += 360
            
        # 检查是否达到阈值
        signal = 'none'
        direction = 'stable'
        confidence = 0.0
        
        if abs(angle_change) > self.angle_threshold:
            if angle_change > self.angle_threshold:
                signal = 'up'
                direction = 'rising'
                confidence = min(0.9, abs(angle_change) / (self.angle_threshold * 2))
                self.logger.info(f"🔥 触发上升信号! 角度变化: {angle_change:.2f}° > {self.angle_threshold}°")
            elif angle_change < -self.angle_threshold:
                signal = 'down'
                direction = 'falling'
                confidence = min(0.9, abs(angle_change) / (self.angle_threshold * 2))
                self.logger.info(f"🔥 触发下降信号! 角度变化: {angle_change:.2f}° < -{self.angle_threshold}°")
        else:
            self.logger.debug(f"⚪ 角度变化未达到阈值: {angle_change:.2f}° (需要>{self.angle_threshold}°)")
            
        return {
            'signal': signal,
            'direction': direction,
            'angle_change': angle_change,
            'confidence': confidence,
            'current_angle': current['angle'],
            'threshold': self.angle_threshold
        }
    
    def get_angle_statistics(self) -> Dict:
        """获取角度统计信息"""
        if not self.angle_history:
            return {}
            
        angles = [data['angle'] for data in self.angle_history]
        
        return {
            'count': len(angles),
            'current': angles[-1],
            'mean': np.mean(angles),
            'std': np.std(angles),
            'min': np.min(angles),
            'max': np.max(angles),
            'range': np.max(angles) - np.min(angles)
        }
    
    def reset_history(self):
        """重置历史数据"""
        self.angle_history.clear()
        self.logger.info("角度历史数据已重置")
        
    def get_recent_changes(self, count: int = 5) -> List[float]:
        """获取最近的角度变化"""
        if len(self.angle_history) < 2:
            return []
            
        changes = []
        for i in range(max(1, len(self.angle_history) - count), len(self.angle_history)):
            current = self.angle_history[i]['angle']
            previous = self.angle_history[i-1]['angle']
            change = current - previous
            
            # 处理角度跳跃
            if change > 180:
                change -= 360
            elif change < -180:
                change += 360
                
            changes.append(change)
            
        return changes
