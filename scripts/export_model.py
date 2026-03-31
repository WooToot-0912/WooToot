#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
云南烤烟病害检测模型导出脚本
用于将训练好的PyTorch模型导出为ONNX、TFLite等格式，并进行优化
"""

import os
import sys
import argparse
from pathlib import Path
import torch
import yaml
import time

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules import ECA, BackgroundSuppressionBranch

def parse_args():
    parser = argparse.ArgumentParser(description='云南烤烟病害检测模型导出')
    parser.add_argument('--weights', type=str, required=True, help='模型权重路径')
    parser.add_argument('--output', type=str, default='models/exported', help='输出目录')
    parser.add_argument('--format', type=str, default='onnx', choices=['onnx', 'tflite', 'coreml', 'all'], help='导出格式')
    parser.add_argument('--imgsz', type=int, default=640, help='输入图像尺寸')
    parser.add_argument('--half', action='store_true', help='使用FP16半精度')
    parser.add_argument('--simplify', action='store_true', help='简化ONNX模型')
    parser.add_argument('--optimize', action='store_true', help='优化模型大小')
    return parser.parse_args()

def register_custom_modules():
    """注册自定义模块到YOLO模型注册表"""
    from ultralytics.nn.tasks import DetectionModel
    
    # 注册自定义模块
    DetectionModel.add_module('ECA', ECA)
    DetectionModel.add_module('BackgroundSuppressionBranch', BackgroundSuppressionBranch)
    
    print("自定义模块注册完成")

def export_onnx(model, output_path, imgsz=640, half=False, simplify=False):
    """导出ONNX模型"""
    from ultralytics.engine.exporter import Exporter
    
    try:
        # 创建导出器
        exporter = Exporter(model=model, imgsz=imgsz)
        
        # 导出ONNX模型
        f = str(output_path)
        print(f"开始导出ONNX模型到 {f}")
        
        # 导出
        f = exporter.export_onnx(
            opset=12,
            simplify=simplify,
            half=half,
            dynamic=True,
            prefix=int(time.time())
        )
        
        print(f"ONNX模型导出成功: {f}")
        return f
    except Exception as e:
        print(f"导出ONNX模型失败: {e}")
        return None

def optimize_onnx(onnx_path, output_path=None):
    """优化ONNX模型大小"""
    try:
        import onnx
        import onnxoptimizer
        
        if output_path is None:
            output_path = onnx_path.replace('.onnx', '_optimized.onnx')
        
        print(f"开始优化ONNX模型: {onnx_path}")
        
        # 加载模型
        model = onnx.load(onnx_path)
        
        # 优化模型
        passes = [
            'eliminate_identity',
            'eliminate_nop_transpose',
            'eliminate_nop_pad',
            'eliminate_unused_initializer',
            'eliminate_deadend',
            'fuse_add_bias_into_conv',
            'fuse_bn_into_conv',
            'fuse_consecutive_concats',
            'fuse_consecutive_reduce_unsqueeze',
            'fuse_consecutive_squeezes',
            'fuse_consecutive_transposes',
        ]
        
        optimized_model = onnxoptimizer.optimize(model, passes)
        
        # 保存优化后的模型
        onnx.save(optimized_model, output_path)
        
        # 检查优化效果
        original_size = os.path.getsize(onnx_path) / (1024 * 1024)
        optimized_size = os.path.getsize(output_path) / (1024 * 1024)
        reduction = (1 - optimized_size / original_size) * 100
        
        print(f"ONNX模型优化完成: {output_path}")
        print(f"原始大小: {original_size:.2f} MB")
        print(f"优化后大小: {optimized_size:.2f} MB")
        print(f"减少: {reduction:.2f}%")
        
        return output_path
    except ImportError:
        print("需要安装onnx和onnxoptimizer: pip install onnx onnxoptimizer")
        return onnx_path
    except Exception as e:
        print(f"优化ONNX模型失败: {e}")
        return onnx_path

def export_tflite(model, output_path, imgsz=640):
    """导出TFLite模型"""
    try:
        # 先导出为ONNX
        onnx_path = str(output_path).replace('.tflite', '.onnx')
        onnx_path = export_onnx(model, onnx_path, imgsz)
        
        if onnx_path is None:
            return None
        
        # 从ONNX转换为TFLite
        import onnx_tf
        import tensorflow as tf
        
        # 转换为TF模型
        tf_path = str(output_path).replace('.tflite', '_saved_model')
        print(f"将ONNX转换为TensorFlow模型: {tf_path}")
        
        # 加载ONNX模型
        onnx_model = onnx.load(onnx_path)
        
        # 转换为TF模型
        tf_rep = onnx_tf.backend.prepare(onnx_model)
        tf_rep.export_graph(tf_path)
        
        # 转换为TFLite
        print(f"将TensorFlow模型转换为TFLite: {output_path}")
        converter = tf.lite.TFLiteConverter.from_saved_model(tf_path)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
        tflite_model = converter.convert()
        
        # 保存TFLite模型
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        print(f"TFLite模型导出成功: {output_path}")
        return output_path
    except ImportError:
        print("需要安装tensorflow和onnx-tf: pip install tensorflow onnx-tf")
        return None
    except Exception as e:
        print(f"导出TFLite模型失败: {e}")
        return None

def export_coreml(model, output_path, imgsz=640, half=False):
    """导出CoreML模型"""
    try:
        from ultralytics.engine.exporter import Exporter
        
        # 创建导出器
        exporter = Exporter(model=model, imgsz=imgsz)
        
        # 导出CoreML模型
        f = str(output_path)
        print(f"开始导出CoreML模型到 {f}")
        
        # 导出
        f = exporter.export_coreml(half=half)
        
        print(f"CoreML模型导出成功: {f}")
        return f
    except Exception as e:
        print(f"导出CoreML模型失败: {e}")
        return None

def main():
    args = parse_args()
    
    # 注册自定义模块
    register_custom_modules()
    
    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)
    
    # 加载模型
    print(f"加载模型权重: {args.weights}")
    from ultralytics import YOLO
    model = YOLO(args.weights)
    
    # 导出模型
    if args.format == 'onnx' or args.format == 'all':
        onnx_path = os.path.join(args.output, Path(args.weights).stem + '.onnx')
        onnx_model = export_onnx(model, onnx_path, args.imgsz, args.half, args.simplify)
        
        if onnx_model and args.optimize:
            optimize_onnx(onnx_model, onnx_model.replace('.onnx', '_optimized.onnx'))
    
    if args.format == 'tflite' or args.format == 'all':
        tflite_path = os.path.join(args.output, Path(args.weights).stem + '.tflite')
        export_tflite(model, tflite_path, args.imgsz)
    
    if args.format == 'coreml' or args.format == 'all':
        coreml_path = os.path.join(args.output, Path(args.weights).stem + '.mlmodel')
        export_coreml(model, coreml_path, args.imgsz, args.half)
    
    print("模型导出完成！")

if __name__ == '__main__':
    main()