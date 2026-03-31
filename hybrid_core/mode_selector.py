#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能模式选择器 - 根据环境和信号质量自动选择最佳交易模式
"""

import time
import logging
import statistics
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

class TradingMode(Enum):
    """交易模式"""
    API_ONLY = "api_only"
    IMAGE_ONLY = "image_only"
    HYBRID = "hybrid"
    AUTO = "auto"

@dataclass
class ModePerformance:
    """模式性能数据"""
    mode: TradingMode
    success_rate: float
    avg_confidence: float
    execution_time: float
    error_count: int
    total_trades: int

class IntelligentModeSelector:
    """智能模式选择器"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化智能模式选择器

        Args:
            config: 选择器配置
        """
        self.logger = logging.getLogger(__name__)

        # 默认配置
        default_config = {
            "performance_window": 20,        # 性能评估窗口大小
            "mode_switch_threshold": 0.15,   # 模式切换阈值
            "min_samples": 5,               # 最小样本数
            "api_priority_bonus": 0.1,      # API优先级加成
            "stability_weight": 0.3,        # 稳定性权重
            "speed_weight": 0.2,            # 速度权重
            "accuracy_weight": 0.5          # 准确性权重
        }

        self.config = {**default_config, **(config or {})}

        # 性能历史记录
        self.performance_history: Dict[TradingMode, List[Dict]] = {
            TradingMode.API_ONLY: [],
            TradingMode.IMAGE_ONLY: [],
            TradingMode.HYBRID: []
        }

        # 当前推荐模式
        self.recommended_mode = TradingMode.AUTO
        self.last_evaluation_time = 0

        self.logger.info("✅ 智能模式选择器初始化完成")

    def record_performance(self, mode: TradingMode, success: bool,
                          confidence: float, execution_time: float):
        """记录模式性能"""
        try:
            performance_record = {
                'timestamp': time.time(),
                'success': success,
                'confidence': confidence,
                'execution_time': execution_time
            }

            if mode in self.performance_history:
                self.performance_history[mode].append(performance_record)

                # 限制历史记录大小
                max_size = self.config["performance_window"]
                if len(self.performance_history[mode]) > max_size:
                    self.performance_history[mode] = self.performance_history[mode][-max_size:]

            self.logger.debug(f"📊 记录性能: {mode.value} - 成功:{success}, 置信度:{confidence:.2f}")

        except Exception as e:
            self.logger.error(f"记录性能失败: {e}")

    def evaluate_modes(self) -> Dict[TradingMode, ModePerformance]:
        """评估各模式性能"""
        try:
            mode_performances = {}

            for mode, history in self.performance_history.items():
                if len(history) >= self.config["min_samples"]:
                    performance = self._calculate_mode_performance(mode, history)
                    mode_performances[mode] = performance
                else:
                    # 样本不足，使用默认性能
                    mode_performances[mode] = ModePerformance(
                        mode=mode,
                        success_rate=0.5,
                        avg_confidence=0.5,
                        execution_time=10.0,
                        error_count=0,
                        total_trades=0
                    )

            return mode_performances

        except Exception as e:
            self.logger.error(f"模式评估失败: {e}")
            return {}

    def _calculate_mode_performance(self, mode: TradingMode, history: List[Dict]) -> ModePerformance:
        """计算模式性能指标"""
        try:
            total_trades = len(history)
            successful_trades = sum(1 for record in history if record['success'])
            success_rate = successful_trades / total_trades if total_trades > 0 else 0

            confidences = [record['confidence'] for record in history]
            avg_confidence = statistics.mean(confidences) if confidences else 0

            execution_times = [record['execution_time'] for record in history]
            avg_execution_time = statistics.mean(execution_times) if execution_times else 0

            error_count = total_trades - successful_trades

            return ModePerformance(
                mode=mode,
                success_rate=success_rate,
                avg_confidence=avg_confidence,
                execution_time=avg_execution_time,
                error_count=error_count,
                total_trades=total_trades
            )

        except Exception as e:
            self.logger.error(f"计算模式性能失败: {e}")
            return ModePerformance(
                mode=mode,
                success_rate=0.0,
                avg_confidence=0.0,
                execution_time=0.0,
                error_count=0,
                total_trades=0
            )

    def select_optimal_mode(self, api_available: bool = True,
                           image_available: bool = True) -> TradingMode:
        """
        选择最优交易模式

        Args:
            api_available: API是否可用
            image_available: 图像识别是否可用

        Returns:
            TradingMode: 推荐的交易模式
        """
        try:
            # 检查可用性
            if not api_available and not image_available:
                self.logger.error("❌ 所有交易方式都不可用")
                return TradingMode.API_ONLY  # 默认返回

            if not api_available:
                self.logger.info("⚠️ API不可用，选择图像模式")
                return TradingMode.IMAGE_ONLY

            if not image_available:
                self.logger.info("⚠️ 图像识别不可用，选择API模式")
                return TradingMode.API_ONLY

            # 评估各模式性能
            performances = self.evaluate_modes()

            if not performances:
                # 无历史数据，使用默认策略
                self.logger.info("📊 无历史数据，使用默认API优先策略")
                return TradingMode.API_ONLY

            # 计算综合得分
            mode_scores = {}
            for mode, perf in performances.items():
                if mode != TradingMode.AUTO:  # 排除AUTO模式
                    score = self._calculate_mode_score(perf)
                    mode_scores[mode] = score

            # 选择最高得分的模式
            if mode_scores:
                best_mode = max(mode_scores.keys(), key=lambda m: mode_scores[m])
                best_score = mode_scores[best_mode]

                self.logger.info(f"🎯 智能选择模式: {best_mode.value} (得分: {best_score:.2f})")

                # 更新推荐模式
                self.recommended_mode = best_mode
                self.last_evaluation_time = time.time()

                return best_mode
            else:
                return TradingMode.API_ONLY

        except Exception as e:
            self.logger.error(f"模式选择失败: {e}")
            return TradingMode.API_ONLY

    def _calculate_mode_score(self, performance: ModePerformance) -> float:
        """计算模式综合得分"""
        try:
            # 准确性得分
            accuracy_score = performance.success_rate

            # 稳定性得分（基于置信度）
            stability_score = performance.avg_confidence

            # 速度得分（执行时间越短得分越高）
            max_time = 30.0  # 假设最大执行时间30秒
            speed_score = max(0, (max_time - performance.execution_time) / max_time)

            # 综合得分
            total_score = (
                accuracy_score * self.config["accuracy_weight"] +
                stability_score * self.config["stability_weight"] +
                speed_score * self.config["speed_weight"]
            )

            # API模式加成
            if performance.mode == TradingMode.API_ONLY:
                total_score += self.config["api_priority_bonus"]

            return min(total_score, 1.0)

        except Exception as e:
            self.logger.error(f"计算模式得分失败: {e}")
            return 0.0
