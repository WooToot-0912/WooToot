#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
信号融合引擎 - 多模态信号融合的核心算法
将API信号和图像信号进行智能融合，生成最优交易决策
"""

import time
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

class SignalType(Enum):
    """信号类型"""
    BUY_UP = "buy_up"       # 买涨
    BUY_DOWN = "buy_down"   # 买跌
    HOLD = "hold"           # 持有
    UNKNOWN = "unknown"     # 未知

class SignalSource(Enum):
    """信号源"""
    API_KLINE = "api_kline"
    IMAGE_DETECTION = "image_detection"
    FUSION = "fusion"

@dataclass
class TradingSignal:
    """交易信号数据类"""
    action: str
    confidence: float
    source: SignalSource
    timestamp: float
    reason: str = ""
    price: Optional[float] = None
    additional_data: Optional[Dict] = None

class SignalFusionEngine:
    """信号融合引擎"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化信号融合引擎

        Args:
            config: 融合配置参数
        """
        self.logger = logging.getLogger(__name__)

        # 默认配置
        default_config = {
            "api_weight": 0.6,              # API信号权重
            "image_weight": 0.4,            # 图像信号权重
            "confidence_threshold": 0.7,     # 融合信号置信度阈值
            "consistency_bonus": 0.2,        # 信号一致性加成
            "conflict_penalty": 0.3,         # 信号冲突惩罚
            "time_window": 60,               # 信号时间窗口(秒)
            "max_signal_age": 30             # 信号最大年龄(秒)
        }

        self.config = {**default_config, **(config or {})}

        # 信号历史记录
        self.signal_history: List[TradingSignal] = []
        self.max_history_size = 100

        self.logger.info("✅ 信号融合引擎初始化完成")

    def add_signal(self, signal: TradingSignal):
        """添加信号到历史记录"""
        self.signal_history.append(signal)

        # 限制历史记录大小
        if len(self.signal_history) > self.max_history_size:
            self.signal_history = self.signal_history[-self.max_history_size:]

    def fuse_signals(self, api_signal: Dict, image_signal: Dict) -> TradingSignal:
        """
        融合API信号和图像信号

        Args:
            api_signal: API信号字典
            image_signal: 图像信号字典

        Returns:
            TradingSignal: 融合后的交易信号
        """
        try:
            current_time = time.time()

            # 验证信号有效性
            api_valid = self._validate_signal(api_signal)
            image_valid = self._validate_signal(image_signal)

            if not api_valid and not image_valid:
                return TradingSignal(
                    action="hold",
                    confidence=0.0,
                    source=SignalSource.FUSION,
                    timestamp=current_time,
                    reason="无有效信号"
                )

            # 单一信号处理
            if api_valid and not image_valid:
                return self._convert_to_trading_signal(api_signal, SignalSource.API_KLINE)
            elif image_valid and not api_valid:
                return self._convert_to_trading_signal(image_signal, SignalSource.IMAGE_DETECTION)

            # 双信号融合
            return self._perform_signal_fusion(api_signal, image_signal, current_time)

        except Exception as e:
            self.logger.error(f"信号融合失败: {e}")
            return TradingSignal(
                action="hold",
                confidence=0.0,
                source=SignalSource.FUSION,
                timestamp=time.time(),
                reason=f"融合异常: {str(e)}"
            )

    def _validate_signal(self, signal: Dict) -> bool:
        """验证信号有效性"""
        if not signal or signal.get('error'):
            return False

        action = signal.get('action', 'hold')
        confidence = signal.get('confidence', 0.0)

        return action != 'hold' and confidence > 0.3

    def _convert_to_trading_signal(self, signal: Dict, source: SignalSource) -> TradingSignal:
        """转换为标准交易信号"""
        return TradingSignal(
            action=signal.get('action', 'hold'),
            confidence=signal.get('confidence', 0.0),
            source=source,
            timestamp=time.time(),
            reason=signal.get('reason', ''),
            price=signal.get('price'),
            additional_data=signal
        )

    def _perform_signal_fusion(self, api_signal: Dict, image_signal: Dict, timestamp: float) -> TradingSignal:
        """执行信号融合算法"""
        api_action = api_signal.get('action', 'hold')
        image_action = image_signal.get('action', 'hold')
        api_conf = api_signal.get('confidence', 0.0)
        image_conf = image_signal.get('confidence', 0.0)

        # 信号一致性检查
        if api_action == image_action and api_action != 'hold':
            # 信号一致，增强置信度
            fused_confidence = (
                api_conf * self.config["api_weight"] +
                image_conf * self.config["image_weight"]
            ) * (1 + self.config["consistency_bonus"])

            return TradingSignal(
                action=api_action,
                confidence=min(fused_confidence, 1.0),
                source=SignalSource.FUSION,
                timestamp=timestamp,
                reason=f"API+图像一致信号: {api_action}",
                price=api_signal.get('price') or image_signal.get('price'),
                additional_data={
                    'api_signal': api_signal,
                    'image_signal': image_signal,
                    'fusion_type': 'consistent'
                }
            )

        # 信号冲突处理
        elif api_action != image_action and api_action != 'hold' and image_action != 'hold':
            # 选择置信度更高的信号，但降低置信度
            if api_conf > image_conf:
                selected_signal = api_signal
                selected_source = SignalSource.API_KLINE
                confidence_penalty = self.config["conflict_penalty"]
            else:
                selected_signal = image_signal
                selected_source = SignalSource.IMAGE_DETECTION
                confidence_penalty = self.config["conflict_penalty"]

            final_confidence = selected_signal.get('confidence', 0.0) * (1 - confidence_penalty)

            return TradingSignal(
                action=selected_signal.get('action', 'hold'),
                confidence=final_confidence,
                source=selected_source,
                timestamp=timestamp,
                reason=f"信号冲突，选择高置信度: {selected_signal.get('action')}",
                price=selected_signal.get('price'),
                additional_data={
                    'api_signal': api_signal,
                    'image_signal': image_signal,
                    'fusion_type': 'conflict_resolved'
                }
            )

        # 单一有效信号
        else:
            if api_action != 'hold':
                return self._convert_to_trading_signal(api_signal, SignalSource.API_KLINE)
            elif image_action != 'hold':
                return self._convert_to_trading_signal(image_signal, SignalSource.IMAGE_DETECTION)
            else:
                return TradingSignal(
                    action="hold",
                    confidence=0.0,
                    source=SignalSource.FUSION,
                    timestamp=timestamp,
                    reason="无交易信号"
                )

    def get_signal_statistics(self) -> Dict[str, Any]:
        """获取信号统计信息"""
        if not self.signal_history:
            return {"total_signals": 0}

        total = len(self.signal_history)
        api_signals = sum(1 for s in self.signal_history if s.source == SignalSource.API_KLINE)
        image_signals = sum(1 for s in self.signal_history if s.source == SignalSource.IMAGE_DETECTION)
        fusion_signals = sum(1 for s in self.signal_history if s.source == SignalSource.FUSION)

        # 计算平均置信度
        avg_confidence = np.mean([s.confidence for s in self.signal_history])

        # 计算信号分布
        actions = [s.action for s in self.signal_history]
        buy_up_count = actions.count('buy_up')
        buy_down_count = actions.count('buy_down')
        hold_count = actions.count('hold')

        return {
            "total_signals": total,
            "api_signals": api_signals,
            "image_signals": image_signals,
            "fusion_signals": fusion_signals,
            "avg_confidence": float(avg_confidence),
            "signal_distribution": {
                "buy_up": buy_up_count,
                "buy_down": buy_down_count,
                "hold": hold_count
            },
            "api_ratio": api_signals / total if total > 0 else 0,
            "image_ratio": image_signals / total if total > 0 else 0,
            "fusion_ratio": fusion_signals / total if total > 0 else 0
        }

    def optimize_fusion_parameters(self):
        """基于历史数据优化融合参数"""
        try:
            if len(self.signal_history) < 20:
                return False

            # 分析最近的信号表现
            recent_signals = self.signal_history[-20:]

            # 计算API和图像信号的准确性（这里简化处理）
            api_accuracy = self._calculate_signal_accuracy(recent_signals, SignalSource.API_KLINE)
            image_accuracy = self._calculate_signal_accuracy(recent_signals, SignalSource.IMAGE_DETECTION)

            # 动态调整权重
            total_accuracy = api_accuracy + image_accuracy
            if total_accuracy > 0:
                self.config["api_weight"] = api_accuracy / total_accuracy
                self.config["image_weight"] = image_accuracy / total_accuracy

                self.logger.info(f"🔧 融合参数已优化: API权重={self.config['api_weight']:.2f}, 图像权重={self.config['image_weight']:.2f}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"融合参数优化失败: {e}")
            return False

    def _calculate_signal_accuracy(self, signals: List[TradingSignal], source: SignalSource) -> float:
        """计算特定源的信号准确性（简化版本）"""
        source_signals = [s for s in signals if s.source == source]
        if not source_signals:
            return 0.5  # 默认准确性

        # 这里简化为基于置信度的准确性估算
        # 实际应用中应该基于交易结果计算
        avg_confidence = np.mean([s.confidence for s in source_signals])
        return avg_confidence

    def get_fusion_recommendation(self, api_signal: Dict, image_signal: Dict) -> Dict[str, Any]:
        """获取融合建议"""
        try:
            # 分析信号质量
            api_quality = self._assess_signal_quality(api_signal)
            image_quality = self._assess_signal_quality(image_signal)

            # 生成融合建议
            recommendation = {
                "api_signal_quality": api_quality,
                "image_signal_quality": image_quality,
                "recommended_mode": self._recommend_trading_mode(api_quality, image_quality),
                "fusion_confidence": self._calculate_fusion_confidence(api_signal, image_signal),
                "risk_assessment": self._assess_fusion_risk(api_signal, image_signal)
            }

            return recommendation

        except Exception as e:
            self.logger.error(f"生成融合建议失败: {e}")
            return {"error": str(e)}

    def _assess_signal_quality(self, signal: Dict) -> Dict[str, Any]:
        """评估信号质量"""
        if not signal or signal.get('error'):
            return {"score": 0.0, "issues": ["信号无效或有错误"]}

        confidence = signal.get('confidence', 0.0)
        action = signal.get('action', 'hold')

        issues = []
        if confidence < 0.5:
            issues.append("置信度较低")
        if action == 'hold':
            issues.append("无明确交易方向")

        score = confidence * (0.8 if action != 'hold' else 0.2)

        return {
            "score": score,
            "confidence": confidence,
            "action": action,
            "issues": issues
        }

    def _recommend_trading_mode(self, api_quality: Dict, image_quality: Dict) -> str:
        """推荐交易模式"""
        api_score = api_quality.get("score", 0.0)
        image_score = image_quality.get("score", 0.0)

        if api_score > 0.8 and image_score > 0.8:
            return "hybrid"  # 双高质量，使用混合模式
        elif api_score > 0.7:
            return "api_only"  # API质量高，使用API模式
        elif image_score > 0.7:
            return "image_only"  # 图像质量高，使用图像模式
        else:
            return "hold"  # 质量都不高，建议持有

    def _calculate_fusion_confidence(self, api_signal: Dict, image_signal: Dict) -> float:
        """计算融合置信度"""
        api_conf = api_signal.get('confidence', 0.0)
        image_conf = image_signal.get('confidence', 0.0)

        # 加权平均
        weighted_conf = (
            api_conf * self.config["api_weight"] +
            image_conf * self.config["image_weight"]
        )

        # 一致性调整
        api_action = api_signal.get('action', 'hold')
        image_action = image_signal.get('action', 'hold')

        if api_action == image_action and api_action != 'hold':
            # 信号一致，增加置信度
            weighted_conf *= (1 + self.config["consistency_bonus"])
        elif api_action != image_action and api_action != 'hold' and image_action != 'hold':
            # 信号冲突，降低置信度
            weighted_conf *= (1 - self.config["conflict_penalty"])

        return min(weighted_conf, 1.0)

    def _assess_fusion_risk(self, api_signal: Dict, image_signal: Dict) -> Dict[str, Any]:
        """评估融合风险"""
        risk_factors = []
        risk_score = 0.0

        # 信号冲突风险
        api_action = api_signal.get('action', 'hold')
        image_action = image_signal.get('action', 'hold')

        if api_action != image_action and api_action != 'hold' and image_action != 'hold':
            risk_factors.append("信号方向冲突")
            risk_score += 0.3

        # 置信度差异风险
        api_conf = api_signal.get('confidence', 0.0)
        image_conf = image_signal.get('confidence', 0.0)
        conf_diff = abs(api_conf - image_conf)

        if conf_diff > 0.4:
            risk_factors.append("置信度差异较大")
            risk_score += 0.2

        # 数据质量风险
        if api_signal.get('error') or image_signal.get('error'):
            risk_factors.append("数据质量问题")
            risk_score += 0.2

        return {
            "risk_score": min(risk_score, 1.0),
            "risk_factors": risk_factors,
            "risk_level": "高" if risk_score > 0.6 else "中" if risk_score > 0.3 else "低"
        }
