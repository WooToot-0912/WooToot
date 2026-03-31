# 🎯 景陶易购智能交易系统

## 📋 项目概述

这是一个基于UI自动化的智能交易系统，专为景陶易购客户端设计。

## 🚀 快速开始

### 1. 启动系统
```bash
python main_stable.py gui      # GUI模式
python main_stable.py console  # 控制台模式
```

### 2. 坐标校准
如果按钮位置不准确，使用集成的校准工具：
- 在GUI中点击"坐标校准"按钮
- 或运行: `python tools/coordinate_calibrator.py`

## 📁 项目结构

```
自动交易系统/
├── main_stable.py              # 🚀 主程序入口
├── src/                        # 📁 源代码
│   ├── trading/               # 💼 核心交易模块
│   │   ├── trading_engine.py  # 🔧 交易引擎
│   │   ├── trading_gui.py     # 🖥️ GUI界面
│   │   ├── trading_thread.py  # 🔄 交易线程
│   │   └── main_app.py        # 📱 应用入口
│   └── core/                  # ⚙️ 核心功能
├── config/                    # ⚙️ 配置文件
│   └── smart_coordinates_config.json
├── tools/                     # 🔧 工具脚本
│   └── coordinate_calibrator.py
├── scripts/                   # 📜 启动脚本
├── docs/                      # 📚 文档
└── requirements/              # 📦 依赖管理
```

## 🔧 核心功能

### 1. 交易策略
- 红绿线信号检测
- MACD趋势分析  
- K线形态识别
- 信号融合算法

### 2. 风险管理
- Kelly准则资金管理
- VaR风险控制
- 止损止盈机制

### 3. UI自动化
- 坐标自动校准
- 按钮智能识别
- 窗口状态检测

## ⚙️ 系统配置

主要配置文件位于 `config/smart_coordinates_config.json`，包含所有按钮的坐标信息。

## 🛠️ 故障排除

### 1. 坐标不准确
- 使用校准工具重新设置按钮位置
- 确保景陶易购窗口位置固定

### 2. 程序无响应  
- 检查客户端是否正常运行
- 重启程序并重新校准

### 3. 依赖问题
```bash
pip install -r requirements/requirements.txt
```

## 📞 技术支持

如遇问题，请检查：
1. 景陶易购客户端是否正常运行
2. 坐标配置是否正确
3. 依赖包是否完整安装

---
*更新时间: 2025-01-05*
