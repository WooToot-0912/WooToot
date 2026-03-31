import torch
import torch.nn as nn
import math

class ECA(nn.Module):
    """
    基于CVPR2020论文优化的烤烟病害ECA注意力机制
    参考: ECA-Net: Efficient Channel Attention for Deep Convolutional Neural Networks
    https://blog.csdn.net/qq_37151108/article/details/107157996
    
    核心改进:
    1. 避免SE-Net的降维问题，保持通道直接对应
    2. 自适应卷积核大小选择，适配不同病害特征尺度
    3. 局部跨通道交互，提升病害区分能力
    """
    def __init__(self, channels, gamma=2, b=1, adaptive_kernel=True):
        super(ECA, self).__init__()
        self.channels = channels
        self.adaptive_kernel = adaptive_kernel
        
        # 全局平均池化 - 不进行降维，保持通道对应关系
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        
        if adaptive_kernel:
            # 基于论文的自适应核大小计算公式
            # k = |log2(C)/γ + b/γ|_odd
            t = int(abs((math.log(channels, 2) + b) / gamma))
            k = t if t % 2 else t + 1  # 确保奇数
            k = max(k, 3)  # 最小核大小为3
        else:
            # 固定核大小，适用于特定病害检测
            k = 3
        
        self.kernel_size = k
        
        # 1D卷积实现局部跨通道交互
        # 论文核心: 避免全连接层的维度压缩
        self.conv = nn.Conv1d(
            in_channels=1, 
            out_channels=1, 
            kernel_size=k, 
            padding=(k - 1) // 2, 
            bias=False
        )
        
        self.sigmoid = nn.Sigmoid()
        
        # 用于调试和可视化
        self.attention_weights = None

    def forward(self, x):
        """
        前向传播
        
        Args:
            x: 输入特征图 [B, C, H, W]
            
        Returns:
            重校准后的特征图 [B, C, H, W]
        """
        batch_size, channels, height, width = x.size()
        
        # Step 1: 全局平均池化 [B, C, H, W] -> [B, C, 1, 1]
        y = self.avg_pool(x)
        
        # Step 2: 维度变换准备1D卷积 [B, C, 1, 1] -> [B, 1, C]
        y = y.squeeze(-1).transpose(-1, -2)
        
        # Step 3: 1D卷积进行局部跨通道交互
        # 这是论文的核心创新：用1D卷积替代FC层
        y = self.conv(y)
        
        # Step 4: 恢复维度 [B, 1, C] -> [B, C, 1, 1]
        y = y.transpose(-1, -2).unsqueeze(-1)
        
        # Step 5: Sigmoid激活生成注意力权重
        attention = self.sigmoid(y)
        
        # 保存注意力权重用于可视化分析
        self.attention_weights = attention.detach()
        
        # Step 6: 特征重校准
        return x * attention.expand_as(x)
    
    def get_attention_weights(self):
        """获取最后一次前向传播的注意力权重"""
        if self.attention_weights is not None:
            return self.attention_weights.cpu().numpy()
        return None

    def visualize_attention_weights(self, save_path=None, top_k=10):
        """
        可视化注意力权重分布

        Args:
            save_path: 保存路径，如果为None则显示图像
            top_k: 显示前k个最高权重的通道

        Returns:
            matplotlib figure对象
        """
        import matplotlib.pyplot as plt

        if self.attention_weights is None:
            print("⚠️ 没有可用的注意力权重，请先进行前向传播")
            return None

        weights = self.attention_weights.squeeze().cpu().numpy()

        # 创建图像
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 左图：所有通道权重分布
        ax1.bar(range(len(weights)), weights, alpha=0.7, color='skyblue')
        ax1.set_title(f'ECA注意力权重分布 (共{len(weights)}个通道)', fontsize=14)
        ax1.set_xlabel('通道索引')
        ax1.set_ylabel('注意力权重')
        ax1.grid(True, alpha=0.3)

        # 右图：Top-K高权重通道
        top_indices = np.argsort(weights)[-top_k:][::-1]
        top_weights = weights[top_indices]

        colors = plt.cm.Reds(np.linspace(0.4, 1.0, top_k))
        bars = ax2.bar(range(top_k), top_weights, color=colors)
        ax2.set_title(f'Top-{top_k} 高权重通道', fontsize=14)
        ax2.set_xlabel('排名')
        ax2.set_ylabel('注意力权重')
        ax2.set_xticks(range(top_k))
        ax2.set_xticklabels([f'Ch{idx}' for idx in top_indices])

        # 添加数值标签
        for i, (bar, weight) in enumerate(zip(bars, top_weights)):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                    f'{weight:.3f}', ha='center', va='bottom', fontsize=10)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 注意力权重可视化已保存至: {save_path}")
        else:
            plt.show()

        return fig

    def get_channel_importance_analysis(self):
        """
        分析通道重要性

        Returns:
            包含通道重要性分析的字典
        """
        if self.attention_weights is None:
            return None

        weights = self.attention_weights.squeeze().cpu().numpy()

        analysis = {
            'total_channels': len(weights),
            'mean_weight': float(np.mean(weights)),
            'std_weight': float(np.std(weights)),
            'max_weight': float(np.max(weights)),
            'min_weight': float(np.min(weights)),
            'weight_range': float(np.max(weights) - np.min(weights)),
            'top_10_channels': np.argsort(weights)[-10:][::-1].tolist(),
            'top_10_weights': weights[np.argsort(weights)[-10:][::-1]].tolist(),
            'bottom_10_channels': np.argsort(weights)[:10].tolist(),
            'bottom_10_weights': weights[np.argsort(weights)[:10]].tolist(),
            'high_attention_ratio': float(np.sum(weights > np.mean(weights)) / len(weights)),
            'attention_concentration': float(np.sum(weights[np.argsort(weights)[-10:]]) / np.sum(weights))
        }

        return analysis
    
    def extra_repr(self):
        """打印模块信息"""
        return f'channels={self.channels}, kernel_size={self.kernel_size}, adaptive_kernel={self.adaptive_kernel}'


class MultiScaleECA(nn.Module):
    """
    多尺度ECA模块，适用于不同大小的病害特征
    结合论文思想，为烤烟病害检测优化
    """
    def __init__(self, channels, scales=[3, 5, 7]):
        super(MultiScaleECA, self).__init__()
        self.scales = scales
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        
        # 多个不同核大小的1D卷积
        self.convs = nn.ModuleList([
            nn.Conv1d(1, 1, kernel_size=k, padding=(k-1)//2, bias=False)
            for k in scales
        ])
        
        # 融合不同尺度的特征
        self.fusion = nn.Conv1d(len(scales), 1, 1, bias=False)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        # 全局平均池化
        y = self.avg_pool(x).squeeze(-1).transpose(-1, -2)
        
        # 多尺度特征提取
        scale_features = []
        for conv in self.convs:
            scale_features.append(conv(y))
        
        # 拼接多尺度特征
        multi_scale = torch.cat(scale_features, dim=1)
        
        # 特征融合
        fused = self.fusion(multi_scale)
        attention = self.sigmoid(fused.transpose(-1, -2).unsqueeze(-1))
        
        return x * attention.expand_as(x)


class TobaccoECABlock(nn.Module):
    """
    专门为烤烟病害检测设计的ECA增强块
    基于论文优化，针对5种病害类型的特征差异
    """
    def __init__(self, in_channels, reduction_ratio=None):
        super(TobaccoECABlock, self).__init__()
        
        # 基础ECA模块
        self.eca = ECA(in_channels, adaptive_kernel=True)
        
        # 病害特异性增强
        self.disease_specific = nn.Sequential(
            nn.Conv2d(in_channels, in_channels//4, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels//4, in_channels, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        # ECA注意力
        eca_out = self.eca(x)
        
        # 病害特异性增强
        disease_attention = self.disease_specific(x)
        
        # 融合两种注意力
        return eca_out * disease_attention