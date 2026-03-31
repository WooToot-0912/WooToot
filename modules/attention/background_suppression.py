import torch
import torch.nn as nn
import torch.nn.functional as F

class BackgroundSuppressionBranch(nn.Module):
    """
    云南山地烟田复杂背景抑制分支
    专门处理杂草、红壤等背景干扰
    """
    def __init__(self, in_channels):
        super(BackgroundSuppressionBranch, self).__init__()
        
        # 特征提取层
        self.conv1 = nn.Conv2d(in_channels, in_channels//2, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(in_channels//2)
        
        # 叶片区域分割层
        self.conv2 = nn.Conv2d(in_channels//2, in_channels//4, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(in_channels//4)
        
        # 输出掩码层
        self.conv3 = nn.Conv2d(in_channels//4, 1, kernel_size=1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # 特征提取
        feat = self.conv1(x)
        feat = F.relu(self.bn1(feat))
        
        # 区域分割
        feat = self.conv2(feat)
        feat = F.relu(self.bn2(feat))
        
        # 生成掩码
        mask = self.conv3(feat)
        mask = self.sigmoid(mask)
        
        # 应用掩码抑制背景
        return x * mask.expand_as(x), mask