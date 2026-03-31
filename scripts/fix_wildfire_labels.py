#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复野火病标签文件 - 将类别ID从0改为3
"""

import os
from pathlib import Path

def fix_wildfire_labels():
    """修复所有野火病标签文件中的类别ID"""
    print("🔧 开始修复野火病标签文件...")
    
    # 标签目录
    label_dirs = [
        Path("data/train/labels"),
        Path("data/val/labels"),
        Path("data/test/labels")
    ]
    
    total_fixed = 0
    
    for label_dir in label_dirs:
        if not label_dir.exists():
            print(f"   ⚠️ 目录不存在: {label_dir}")
            continue
            
        print(f"   📂 处理目录: {label_dir}")
        fixed_count = 0
        
        # 查找所有野火病标签文件
        for label_file in label_dir.glob("wildfire_*.txt"):
            try:
                # 读取原始内容
                with open(label_file, 'r') as f:
                    content = f.read().strip()
                
                if content:
                    # 将类别ID从0改为3
                    if content.startswith('0 '):
                        new_content = content.replace('0 ', '3 ', 1)
                        
                        # 写回文件
                        with open(label_file, 'w') as f:
                            f.write(new_content + '\n')
                        
                        print(f"     ✅ 修复: {label_file.name} -> 类别ID: 0→3")
                        fixed_count += 1
                    else:
                        print(f"     ℹ️ 跳过: {label_file.name} (已是正确格式)")
                        
            except Exception as e:
                print(f"     ❌ 错误: {label_file.name} - {e}")
        
        print(f"   📊 {label_dir} 修复了 {fixed_count} 个文件")
        total_fixed += fixed_count
    
    print(f"🎉 总共修复了 {total_fixed} 个野火病标签文件")
    return total_fixed

if __name__ == "__main__":
    fix_wildfire_labels()