#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云南烤烟病害检测高级损失函数套件
整合并优化所有损失函数
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

from .focal_loss import FocalLoss

class WeightedFocalLoss(FocalLoss):
    """
    加权Focal Loss
    基于现有FocalLoss增强，支持类别权重
    """
    def __init__(self, alpha=0.25, gamma=2.0, class_weights=None, reduction='mean'):
        super(WeightedFocalLoss, self).__init__(alpha, gamma, reduction)
        
        # 烟草病害的类别权重 (根据数据分布调整)
        if class_weights is None:
            # 默认权重：稀有病害给予更高权重
            self.class_weights = torch.tensor([
                1.0,  # healthy - 权重正常
                2.0,  # mosaic_virus - 中等权重
                1.5,  # brown_spot - 中等权重  
                3.0,  # wildfire - 高权重 (稀有)
                4.0   # bacterial_wilt - 最高权重 (最稀有)
            ])
        else:
            self.class_weights = torch.tensor(class_weights)
    
    def forward(self, inputs, targets):
        # 确保class_weights在正确的设备上
        if self.class_weights.device != inputs.device:
            self.class_weights = self.class_weights.to(inputs.device)
        
        # 计算标准Focal Loss
        focal_loss = super().forward(inputs, targets)
        
        # 应用类别权重
        if len(targets.shape) > 1:  # one-hot编码
            weights = torch.sum(targets * self.class_weights.unsqueeze(0), dim=1)
        else:  # 类别索引
            weights = self.class_weights[targets.long()]
        
        weighted_focal_loss = focal_loss * weights
        
        if self.reduction == 'mean':
            return weighted_focal_loss.mean()
        elif self.reduction == 'sum':
            return weighted_focal_loss.sum()
        else:
            return weighted_focal_loss

class DiceLoss(nn.Module):
    """
    Dice Loss
    适用于病斑分割任务
    """
    def __init__(self, smooth=1e-6, reduction='mean'):
        super(DiceLoss, self).__init__()
        self.smooth = smooth
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        # 应用sigmoid激活
        inputs = torch.sigmoid(inputs)
        
        # 展平张量
        inputs_flat = inputs.view(-1)
        targets_flat = targets.view(-1)
        
        # 计算交集和并集
        intersection = (inputs_flat * targets_flat).sum()
        total = inputs_flat.sum() + targets_flat.sum()
        
        # 计算Dice系数
        dice = (2.0 * intersection + self.smooth) / (total + self.smooth)
        
        # 计算Dice Loss
        dice_loss = 1 - dice
        
        if self.reduction == 'mean':
            return dice_loss.mean()
        elif self.reduction == 'sum':
            return dice_loss.sum()
        else:
            return dice_loss

class IoULoss(nn.Module):
    """
    IoU Loss (Intersection over Union)
    适用于目标检测和分割
    """
    def __init__(self, smooth=1e-6, reduction='mean'):
        super(IoULoss, self).__init__()
        self.smooth = smooth
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        # 应用sigmoid激活
        inputs = torch.sigmoid(inputs)
        
        # 展平张量
        inputs_flat = inputs.view(-1)
        targets_flat = targets.view(-1)
        
        # 计算交集和并集
        intersection = (inputs_flat * targets_flat).sum()
        union = inputs_flat.sum() + targets_flat.sum() - intersection
        
        # 计算IoU
        iou = (intersection + self.smooth) / (union + self.smooth)
        
        # 计算IoU Loss
        iou_loss = 1 - iou
        
        if self.reduction == 'mean':
            return iou_loss.mean()
        elif self.reduction == 'sum':
            return iou_loss.sum()
        else:
            return iou_loss

class TverskyLoss(nn.Module):
    """
    Tversky Loss
    Dice Loss的泛化版本，适用于不平衡数据
    """
    def __init__(self, alpha=0.3, beta=0.7, smooth=1e-6, reduction='mean'):
        super(TverskyLoss, self).__init__()
        self.alpha = alpha  # False Positive权重
        self.beta = beta    # False Negative权重
        self.smooth = smooth
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        # 应用sigmoid激活
        inputs = torch.sigmoid(inputs)
        
        # 展平张量
        inputs_flat = inputs.view(-1)
        targets_flat = targets.view(-1)
        
        # 计算True Positive, False Positive, False Negative
        tp = (inputs_flat * targets_flat).sum()
        fp = (inputs_flat * (1 - targets_flat)).sum()
        fn = ((1 - inputs_flat) * targets_flat).sum()
        
        # 计算Tversky系数
        tversky = (tp + self.smooth) / (tp + self.alpha * fp + self.beta * fn + self.smooth)
        
        # 计算Tversky Loss
        tversky_loss = 1 - tversky
        
        if self.reduction == 'mean':
            return tversky_loss.mean()
        elif self.reduction == 'sum':
            return tversky_loss.sum()
        else:
            return tversky_loss

class ComboLoss(nn.Module):
    """
    组合损失函数
    结合多种损失函数的优势
    """
    def __init__(self, losses_config=None):
        super(ComboLoss, self).__init__()
        
        # 默认损失配置
        if losses_config is None:
            losses_config = {
                'focal': {'weight': 0.5, 'params': {'alpha': 0.25, 'gamma': 2.0}},
                'dice': {'weight': 0.3, 'params': {'smooth': 1e-6}},
                'iou': {'weight': 0.2, 'params': {'smooth': 1e-6}}
            }
        
        self.losses = nn.ModuleDict()
        self.weights = {}
        
        # 初始化各种损失函数
        for loss_name, config in losses_config.items():
            weight = config['weight']
            params = config.get('params', {})
            
            if loss_name == 'focal':
                self.losses[loss_name] = WeightedFocalLoss(**params)
            elif loss_name == 'dice':
                self.losses[loss_name] = DiceLoss(**params)
            elif loss_name == 'iou':
                self.losses[loss_name] = IoULoss(**params)
            elif loss_name == 'tversky':
                self.losses[loss_name] = TverskyLoss(**params)
            
            self.weights[loss_name] = weight
    
    def forward(self, inputs, targets):
        total_loss = 0
        loss_details = {}
        
        for loss_name, loss_fn in self.losses.items():
            loss_value = loss_fn(inputs, targets)
            weighted_loss = self.weights[loss_name] * loss_value
            total_loss += weighted_loss
            loss_details[loss_name] = loss_value.item()
        
        return total_loss, loss_details

class AdaptiveLoss(nn.Module):
    """
    自适应损失函数
    根据训练阶段动态调整损失权重
    """
    def __init__(self, base_losses_config=None, adaptation_strategy='difficulty'):
        super(AdaptiveLoss, self).__init__()
        
        self.combo_loss = ComboLoss(base_losses_config)
        self.adaptation_strategy = adaptation_strategy
        self.training_step = 0
        
        # 困难样本计数器
        self.difficulty_tracker = {}
    
    def update_difficulty(self, inputs, targets, predictions):
        """更新样本困难度统计"""
        with torch.no_grad():
            # 计算预测错误率
            pred_classes = torch.argmax(predictions, dim=1)
            true_classes = torch.argmax(targets, dim=1) if len(targets.shape) > 1 else targets
            
            # 更新困难样本统计
            for class_id in range(5):  # 5类病害
                class_mask = (true_classes == class_id)
                if class_mask.sum() > 0:
                    class_accuracy = (pred_classes[class_mask] == class_id).float().mean()
                    
                    if class_id not in self.difficulty_tracker:
                        self.difficulty_tracker[class_id] = []
                    
                    self.difficulty_tracker[class_id].append(class_accuracy.item())
                    
                    # 保持最近100个样本的记录
                    if len(self.difficulty_tracker[class_id]) > 100:
                        self.difficulty_tracker[class_id].pop(0)
    
    def get_adaptive_weights(self):
        """根据困难度获取自适应权重"""
        if not self.difficulty_tracker:
            return None
        
        adaptive_weights = []
        for class_id in range(5):
            if class_id in self.difficulty_tracker and self.difficulty_tracker[class_id]:
                # 计算平均准确率
                avg_accuracy = np.mean(self.difficulty_tracker[class_id])
                # 准确率越低，权重越高
                weight = 2.0 - avg_accuracy
            else:
                weight = 1.0
            adaptive_weights.append(weight)
        
        return torch.tensor(adaptive_weights)
    
    def forward(self, inputs, targets, predictions=None):
        # 更新困难度统计
        if predictions is not None and self.training:
            self.update_difficulty(inputs, targets, predictions)
        
        # 获取自适应权重
        if self.adaptation_strategy == 'difficulty':
            adaptive_weights = self.get_adaptive_weights()
            if adaptive_weights is not None:
                # 更新Focal Loss的类别权重
                if 'focal' in self.combo_loss.losses:
                    self.combo_loss.losses['focal'].class_weights = adaptive_weights.to(inputs.device)
        
        # 计算损失
        total_loss, loss_details = self.combo_loss(inputs, targets)
        
        self.training_step += 1
        return total_loss, loss_details

class TobaccoSpecificLoss(nn.Module):
    """
    烟草病害特定损失函数
    针对烟草病害特点优化
    """
    def __init__(self):
        super(TobaccoSpecificLoss, self).__init__()
        
        # 病害严重程度权重
        self.severity_weights = torch.tensor([
            1.0,  # healthy - 无风险
            2.0,  # mosaic_virus - 中等风险
            2.5,  # brown_spot - 中高风险
            3.0,  # wildfire - 高风险
            4.0   # bacterial_wilt - 极高风险
        ])
        
        # 基础损失函数
        self.focal_loss = WeightedFocalLoss(
            alpha=0.25, 
            gamma=2.0,
            class_weights=self.severity_weights
        )
        
        # 相似病害混淆惩罚
        self.confusion_penalty = nn.CrossEntropyLoss(reduction='none')
        
        # 定义容易混淆的病害对
        self.confusion_pairs = [
            (1, 2),  # mosaic_virus vs brown_spot
            (2, 3),  # brown_spot vs wildfire
            (3, 4),  # wildfire vs bacterial_wilt
        ]
    
    def forward(self, inputs, targets):
        # 确保inputs和targets维度匹配
        if len(targets.shape) == 1:  # 类别索引
            target_indices = targets
        else:  # one-hot编码
            target_indices = torch.argmax(targets, dim=1)
        
        # 基础Focal Loss
        focal_loss = self.focal_loss(inputs, targets)
        
        # 混淆惩罚
        confusion_loss = 0
        for class1, class2 in self.confusion_pairs:
            # 对容易混淆的类别增加额外惩罚
            mask1 = (target_indices == class1)
            mask2 = (target_indices == class2)
            
            if mask1.sum() > 0:
                pred1 = inputs[mask1]
                wrong_pred = (torch.argmax(pred1, dim=1) == class2).float()
                confusion_loss += wrong_pred.mean() * 0.5
            
            if mask2.sum() > 0:
                pred2 = inputs[mask2]
                wrong_pred = (torch.argmax(pred2, dim=1) == class1).float()
                confusion_loss += wrong_pred.mean() * 0.5
        
        # 总损失
        total_loss = focal_loss + 0.1 * confusion_loss
        
        return total_loss

def create_loss_function(loss_type='adaptive', **kwargs):
    """
    创建损失函数的工厂函数
    
    Args:
        loss_type: 损失函数类型
            - 'focal': Focal Loss
            - 'weighted_focal': 加权Focal Loss
            - 'dice': Dice Loss
            - 'iou': IoU Loss
            - 'tversky': Tversky Loss
            - 'combo': 组合损失
            - 'adaptive': 自适应损失
            - 'tobacco_specific': 烟草特定损失
    """
    if loss_type == 'focal':
        return FocalLoss(**kwargs)
    elif loss_type == 'weighted_focal':
        return WeightedFocalLoss(**kwargs)
    elif loss_type == 'dice':
        return DiceLoss(**kwargs)
    elif loss_type == 'iou':
        return IoULoss(**kwargs)
    elif loss_type == 'tversky':
        return TverskyLoss(**kwargs)
    elif loss_type == 'combo':
        return ComboLoss(**kwargs)
    elif loss_type == 'adaptive':
        return AdaptiveLoss(**kwargs)
    elif loss_type == 'tobacco_specific':
        return TobaccoSpecificLoss(**kwargs)
    else:
        raise ValueError(f"Unknown loss type: {loss_type}")

# 导出主要类和函数
__all__ = [
    'WeightedFocalLoss',
    'DiceLoss',
    'IoULoss', 
    'TverskyLoss',
    'ComboLoss',
    'AdaptiveLoss',
    'TobaccoSpecificLoss',
    'create_loss_function'
]