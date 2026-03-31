# GPU加速训练安装指南

## 问题诊断

您的训练脚本慢的根本原因：**安装的是CPU版本的PyTorch (2.8.0+cpu)**，无法使用GPU加速。

## 解决方案

### 1. 检查GPU硬件
```bash
# 检查NVIDIA GPU
nvidia-smi
```

### 2. 安装NVIDIA驱动程序
- 访问 [NVIDIA官网](https://www.nvidia.com/Download/index.aspx)
- 下载并安装最新的GPU驱动程序

### 3. 安装CUDA工具包
- 访问 [CUDA官网](https://developer.nvidia.com/cuda-downloads)
- 下载CUDA 11.8或12.1版本（推荐）

### 4. 卸载CPU版本PyTorch
```bash
pip uninstall torch torchvision torchaudio
```

### 5. 安装GPU版本PyTorch

#### CUDA 11.8版本：
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### CUDA 12.1版本：
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 6. 验证GPU支持
```bash
python check_gpu.py
```

## 性能对比

| 设备类型 | 估计训练时间 | 批次大小 | 内存使用 |
|---------|------------|---------|----------|
| CPU     | 2-4小时    | 8-16    | 系统内存 |
| GPU 4GB | 15-30分钟  | 16-32   | 显存     |
| GPU 8GB | 10-20分钟  | 32-64   | 显存     |

## 优化后的训练脚本特性

✅ **智能设备检测** - 自动选择最佳设备(GPU/CPU)  
✅ **动态批次优化** - 根据显存大小自动调整  
✅ **混合精度训练** - GPU模式下自动启用AMP  
✅ **缓存策略优化** - 不同设备使用不同缓存方式  
✅ **工作进程调整** - GPU/CPU模式使用不同进程数

## 如果无GPU可用

即使没有GPU，优化后的脚本也会：
- 根据CPU核心数和内存优化批次大小
- 使用更高效的数据加载策略
- 禁用GPU专用的混合精度训练
- 提供更详细的训练进度信息

## 测试优化效果
```bash
python scripts/train_fast_5class.py
```

## 常见问题

**Q: 安装GPU版本PyTorch后仍显示CPU模式？**  
A: 重启Python环境，确保CUDA驱动正确安装

**Q: 显存不足错误？**  
A: 脚本会自动检测并推荐合适的批次大小

**Q: 想手动指定设备？**  
A: 可以修改脚本中的device参数