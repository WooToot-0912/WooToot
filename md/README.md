# 基于YOLOv8的云南烤烟病害检测系统

本项目基于YOLOv8目标检测算法，结合ECA注意力机制和背景抑制分支，实现对云南烤烟典型病害（烟草花叶病毒病、赤星病、野火病、青枯病）的精准检测，特别针对云南山地烟田复杂背景环境进行优化。

## 功能特点

- **高精度检测**：针对云南烤烟特有病害特征进行优化，提高检测准确率
- **复杂背景适应**：通过背景抑制分支过滤山地烟田杂草、红壤等干扰
- **小样本识别**：采用Focal Loss和SMOTE过采样技术，增强对青枯病等稀有病害的检测能力
- **轻量化部署**：优化模型体积，支持移动端部署，满足田间巡检需求
- **实用防治建议**：提供针对性的病害防治建议，辅助精准施药

## 系统架构

```
云南烤烟病害检测/
├── data/                   # 数据集管理
│   ├── raw/                # 原始图像
│   ├── processed/          # 处理后数据
│   ├── augmented/          # 增强后数据
│   └── dataset.yaml        # 数据集配置
├── models/                 # 模型定义
│   ├── backbone/           # 基础模型
│   ├── custom/             # 自定义模型
│   └── weights/            # 训练权重
├── modules/                # 自定义模块
│   ├── attention/          # 注意力机制
│   ├── loss/               # 损失函数
│   └── neck/               # 特征融合
├── utils/                  # 工具函数
├── configs/                # 配置文件
├── app/                    # 应用部署
│   ├── api/                # 后端API
│   ├── web/                # 网页前端
│   └── mobile/             # 移动端
├── train.py                # 训练脚本
├── evaluate.py             # 评估脚本
└── detect.py               # 检测脚本
```

## 技术实现

### 1. 数据集构建

- 基于PlantVillage公开烟草数据集与云南玉溪、曲靖实地采集图像
- 针对云南烤烟特有病害特征（如赤星病轮纹、野火病黄晕）筛选样本
- 通过旋转、亮度变换、杂草背景叠加等数据增强手段扩充样本
- 采用SMOTE过采样技术平衡数据分布，解决青枯病等低发病害样本稀缺问题

### 2. 模型改进

- **ECA注意力机制**：强化病斑细粒度特征（如赤星病轮纹纹理、野火病黄晕边缘）提取
- **背景抑制分支**：过滤山地烟田杂草、红壤等干扰
- **Focal Loss**：缓解数据不平衡问题，提高对稀有类别的检测能力

### 3. 部署应用

- **Flask API**：提供RESTful接口，支持图像上传与检测
- **Web前端**：响应式设计，支持PC端与移动端访问
- **实时检测**：单张图像处理时间≤0.8秒，满足田间巡检需求

## 安装与使用

### 环境要求

- Python 3.8+
- PyTorch 2.0+
- CUDA 11.7+（推荐，用于GPU加速）

### 安装依赖

```bash
# 创建虚拟环境
conda create -n tobacco_disease python=3.9
conda activate tobacco_disease

# 安装依赖
pip install -r requirements.txt
```

### 数据准备

```bash
# 数据处理
python scripts/prepare_data.py --source data/raw --output data/processed

# 数据增强
python scripts/augment_data.py --input data/processed --output data/augmented

# 数据集划分
python scripts/split_dataset.py --ratio 8:1:1
```

### 模型训练

```bash
# 使用默认配置训练
python train.py

# 使用自定义配置训练
python train.py --cfg configs/train.yaml --model models/custom/yolov8_tobacco.yaml
```

### 模型评估

```bash
# 在测试集上评估
python evaluate.py --weights runs/train/exp/weights/best.pt
```

### 病害检测

```bash
# 检测单张图像
python detect.py --weights runs/train/exp/weights/best.pt --source path/to/image.jpg --save

# 使用摄像头实时检测
python detect.py --weights runs/train/exp/weights/best.pt --source 0 --show
```

### 启动Web应用

```bash
# 启动API服务
cd app/api
python app.py

# 访问Web界面
# 打开浏览器访问 app/web/index.html
```

## 实验结果

| 模型 | mAP@0.5 | 推理时间(ms) | 模型大小(MB) |
|------|---------|--------------|-------------|
| YOLOv5s | 0.76 | 95 | 14.1 |
| YOLOv8n | 0.81 | 85 | 6.3 |
| YOLOv8n+ECA | 0.85 | 83 | 6.5 |
| YOLOv8n+ECA+BG | 0.89 | 78 | 7.2 |

## 许可证

本项目采用 MIT 许可证

## 致谢

- 感谢云南省农业科学院提供的烟草病害数据支持
- 感谢Ultralytics团队开发的YOLOv8框架