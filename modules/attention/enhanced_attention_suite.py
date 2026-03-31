#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云南烤烟病害检测增强注意力套件
整合并优化所有注意力机制
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math

from .eca import ECA
from .background_suppression import BackgroundSuppressionBranch

class MultiScaleECAAttention(nn.Module):
    """
    多尺度ECA注意力机制
    在不同尺度下应用ECA注意力
    """
    def __init__(self, channels, scales=[1, 3, 5]):
        super(MultiScaleECAAttention, self).__init__()
        self.scales = scales
        self.eca_modules = nn.ModuleList([
            ECA(channels) for _ in scales
        ])
        
        # 融合层
        self.fusion_conv = nn.Conv2d(channels * len(scales), channels, 1)
        self.fusion_bn = nn.BatchNorm2d(channels)
        
    def forward(self, x):
        multi_scale_features = []
        
        for i, scale in enumerate(self.scales):
            if scale == 1:
                # 原始尺度
                feat = self.eca_modules[i](x)
            else:
                # 下采样后应用ECA，再上采样
                h, w = x.shape[2], x.shape[3]
                x_scaled = F.interpolate(x, scale_factor=1/scale, mode='bilinear', align_corners=False)
                feat_scaled = self.eca_modules[i](x_scaled)
                feat = F.interpolate(feat_scaled, size=(h, w), mode='bilinear', align_corners=False)
            
            multi_scale_features.append(feat)
        
        # 融合多尺度特征
        fused = torch.cat(multi_scale_features, dim=1)
        fused = self.fusion_conv(fused)
        fused = self.fusion_bn(fused)
        
        return F.relu(fused)

class SpatialChannelAttention(nn.Module):
    """
    空间-通道联合注意力
    结合ECA和空间注意力
    """
    def __init__(self, channels, reduction_ratio=16):
        super(SpatialChannelAttention, self).__init__()
        
        # 通道注意力 (使用现有的ECA)
        self.channel_attention = ECA(channels)
        
        # 空间注意力
        self.spatial_conv = nn.Sequential(
            nn.Conv2d(2, 1, 7, padding=3, bias=False),
            nn.BatchNorm2d(1),
            nn.Sigmoid()
        )
        
        # 特征增强
        self.enhance_conv = nn.Sequential(
            nn.Conv2d(channels, channels//reduction_ratio, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels//reduction_ratio, channels, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        # 1. 通道注意力
        x_channel = self.channel_attention(x)
        
        # 2. 空间注意力
        avg_spatial = torch.mean(x_channel, dim=1, keepdim=True)
        max_spatial, _ = torch.max(x_channel, dim=1, keepdim=True)
        spatial_input = torch.cat([avg_spatial, max_spatial], dim=1)
        spatial_attention = self.spatial_conv(spatial_input)
        x_spatial = x_channel * spatial_attention
        
        # 3. 特征增强
        enhancement = self.enhance_conv(x_spatial)
        output = x_spatial * enhancement
        
        return output

class AdaptiveBackgroundSuppression(BackgroundSuppressionBranch):
    """
    自适应背景抑制
    基于现有BackgroundSuppressionBranch增强
    """
    def __init__(self, in_channels, disease_specific=True):
        super(AdaptiveBackgroundSuppression, self).__init__(in_channels)
        self.disease_specific = disease_specific
        
        if disease_specific:
            # 疾病特定的背景抑制
            self.disease_conv = nn.Sequential(
                nn.Conv2d(in_channels//4, in_channels//8, 3, padding=1),
                nn.BatchNorm2d(in_channels//8),
                nn.ReLU(inplace=True),
                nn.Conv2d(in_channels//8, 5, 1),  # 5类疾病
                nn.Softmax(dim=1)
            )
    
    def forward(self, x):
        # 调用父类的基础背景抑制
        suppressed_features, base_mask = super().forward(x)
        
        if self.disease_specific:
            # 生成疾病特定的抑制掩码
            disease_mask = self.disease_conv(self.conv2(self.conv1(x)))
            
            # 融合基础掩码和疾病特定掩码
            # 选择最大概率的疾病类别掩码
            max_disease_mask, _ = torch.max(disease_mask, dim=1, keepdim=True)
            enhanced_mask = base_mask * max_disease_mask
            
            return x * enhanced_mask.expand_as(x), enhanced_mask
        else:
            return suppressed_features, base_mask

class TobaccoSpecificAttention(nn.Module):
    """
    烟草病害特定注意力机制
    针对烟草叶片特征优化
    """
    def __init__(self, channels):
        super(TobaccoSpecificAttention, self).__init__()
        
        # 叶脉检测分支
        self.vein_detector = nn.Sequential(
            nn.Conv2d(channels, channels//4, 1),
            nn.BatchNorm2d(channels//4),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels//4, 1, 3, padding=1),
            nn.Sigmoid()
        )
        
        # 病斑检测分支
        self.lesion_detector = nn.Sequential(
            nn.Conv2d(channels, channels//4, 1),
            nn.BatchNorm2d(channels//4),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels//4, 1, 5, padding=2),
            nn.Sigmoid()
        )
        
        # 边缘检测分支
        self.edge_detector = nn.Sequential(
            nn.Conv2d(channels, channels//4, 1),
            nn.BatchNorm2d(channels//4),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels//4, 1, 3, padding=1),
            nn.Sigmoid()
        )
        
        # 特征融合
        self.fusion = nn.Conv2d(3, 1, 1)
        self.final_attention = nn.Sigmoid()
    
    def forward(self, x):
        # 检测不同特征
        vein_attention = self.vein_detector(x)
        lesion_attention = self.lesion_detector(x)
        edge_attention = self.edge_detector(x)
        
        # 融合注意力
        combined_attention = torch.cat([vein_attention, lesion_attention, edge_attention], dim=1)
        final_attention = self.final_attention(self.fusion(combined_attention))
        
        return x * final_attention.expand_as(x)

class ComprehensiveAttentionModule(nn.Module):
    """
    综合注意力模块
    整合所有注意力机制
    """
    def __init__(self, channels, use_multi_scale=True, use_spatial_channel=True, 
                 use_background_suppression=True, use_tobacco_specific=True):
        super(ComprehensiveAttentionModule, self).__init__()
        
        self.use_multi_scale = use_multi_scale
        self.use_spatial_channel = use_spatial_channel
        self.use_background_suppression = use_background_suppression
        self.use_tobacco_specific = use_tobacco_specific
        
        # 各种注意力机制
        if use_multi_scale:
            self.multi_scale_attention = MultiScaleECAAttention(channels)
        
        if use_spatial_channel:
            self.spatial_channel_attention = SpatialChannelAttention(channels)
        
        if use_background_suppression:
            self.background_suppression = AdaptiveBackgroundSuppression(channels)
        
        if use_tobacco_specific:
            self.tobacco_attention = TobaccoSpecificAttention(channels)
        
        # 最终融合层
        num_streams = sum([use_multi_scale, use_spatial_channel, use_background_suppression, use_tobacco_specific])
        if num_streams > 1:
            self.final_fusion = nn.Sequential(
                nn.Conv2d(channels * num_streams, channels, 1),
                nn.BatchNorm2d(channels),
                nn.ReLU(inplace=True)
            )
    
    def forward(self, x):
        attention_outputs = []
        
        # 应用各种注意力机制
        if self.use_multi_scale:
            multi_scale_out = self.multi_scale_attention(x)
            attention_outputs.append(multi_scale_out)
        
        if self.use_spatial_channel:
            spatial_channel_out = self.spatial_channel_attention(x)
            attention_outputs.append(spatial_channel_out)
        
        if self.use_background_suppression:
            bg_suppressed_out, _ = self.background_suppression(x)
            attention_outputs.append(bg_suppressed_out)
        
        if self.use_tobacco_specific:
            tobacco_out = self.tobacco_attention(x)
            attention_outputs.append(tobacco_out)
        
        # 融合输出
        if len(attention_outputs) == 1:
            return attention_outputs[0]
        else:
            combined = torch.cat(attention_outputs, dim=1)
            return self.final_fusion(combined)

def create_attention_block(channels, attention_type='comprehensive'):
    """
    创建注意力块的工厂函数
    
    Args:
        channels: 输入通道数
        attention_type: 注意力类型
            - 'eca': 基础ECA注意力
            - 'multi_scale': 多尺度ECA
            - 'spatial_channel': 空间-通道联合注意力
            - 'background_suppression': 背景抑制
            - 'tobacco_specific': 烟草特定注意力
            - 'comprehensive': 综合注意力 (默认)
    """
    if attention_type == 'eca':
        return ECA(channels)
    elif attention_type == 'multi_scale':
        return MultiScaleECAAttention(channels)
    elif attention_type == 'spatial_channel':
        return SpatialChannelAttention(channels)
    elif attention_type == 'background_suppression':
        return AdaptiveBackgroundSuppression(channels)
    elif attention_type == 'tobacco_specific':
        return TobaccoSpecificAttention(channels)
    elif attention_type == 'comprehensive':
        return ComprehensiveAttentionModule(channels)
    else:
        raise ValueError(f"Unknown attention type: {attention_type}")

# 导出主要类和函数
__all__ = [
    'MultiScaleECAAttention',
    'SpatialChannelAttention', 
    'AdaptiveBackgroundSuppression',
    'TobaccoSpecificAttention',
    'ComprehensiveAttentionModule',
    'create_attention_block'
]