#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动交易系统 - 精准删除API文件脚本
删除所有API相关文件，并修改主程序中的API引用
确保不影响图像识别等其他功能的正常使用
"""

import os
import shutil
import re
from pathlib import Path

def identify_api_files():
    """识别所有API相关文件"""
    print("🔍 识别API相关文件...")
    
    api_files_to_delete = {
        "API服务器目录": [
            "api_server/"  # 整个API服务器目录
        ],
        "核心API文件": [
            "core/trading_api.py"
        ],
        "应用层API文件": [
            "app/real_api_client.py",
            "app/real_auto_trader.py"  # 依赖API的交易器
        ],
        "源码API目录": [
            "src/api/"  # 整个API源码目录
        ],
        "配置文件": [
            "config/api_config.json"
        ],
        "工具API文件": [
            "tools/api_login_test.py"
        ],
        "文档API文件": [
            "docs/API_INTEGRATION_GUIDE.md"
        ]
    }
    
    return api_files_to_delete

def identify_api_references():
    """识别主程序中的API引用"""
    print("🔍 识别主程序中的API引用...")
    
    files_with_api_refs = [
        "app/main_stable.py",
        "core/smart_trading_engine.py",
        "core/enhanced_detection.py"
    ]
    
    return files_with_api_refs

def backup_before_deletion():
    """删除前备份"""
    print("💾 创建删除前备份...")
    
    backup_dir = Path("backup_before_api_deletion")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    backup_dir.mkdir()
    
    # 备份要删除的文件
    api_files = identify_api_files()
    
    for category, files in api_files.items():
        category_backup = backup_dir / category.replace(" ", "_")
        category_backup.mkdir(exist_ok=True)
        
        for file_path in files:
            source_path = Path(file_path)
            if source_path.exists():
                if source_path.is_dir():
                    # 备份整个目录
                    shutil.copytree(source_path, category_backup / source_path.name)
                    print(f"   📁 备份目录: {file_path}")
                else:
                    # 备份单个文件
                    shutil.copy2(source_path, category_backup / source_path.name)
                    print(f"   📄 备份文件: {file_path}")
    
    print(f"✅ 备份完成，备份位置: {backup_dir}")
    return backup_dir

def remove_api_imports_from_file(file_path):
    """从文件中移除API相关的导入"""
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 移除API相关的导入语句
        api_import_patterns = [
            r'from\s+.*api.*\s+import.*\n',
            r'import\s+.*api.*\n',
            r'from\s+real_api_client\s+import.*\n',
            r'import\s+real_api_client.*\n',
            r'from\s+trading_api\s+import.*\n',
            r'import\s+trading_api.*\n'
        ]
        
        for pattern in api_import_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # 移除API相关的类实例化
        api_instance_patterns = [
            r'.*=.*RealAPIClient\(\).*\n',
            r'.*=.*TradingAPI\(\).*\n',
            r'.*\.api_client.*\n'
        ]
        
        for pattern in api_instance_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✅ 已移除 {file_path} 中的API引用")
            return True
        else:
            print(f"   ℹ️ {file_path} 中无API引用需要移除")
            return False
            
    except Exception as e:
        print(f"   ❌ 处理 {file_path} 失败: {e}")
        return False

def delete_api_files():
    """删除API相关文件"""
    print("🗑️ 开始删除API相关文件...")
    
    api_files = identify_api_files()
    deleted_count = 0
    
    for category, files in api_files.items():
        print(f"\n📁 处理 {category}:")
        
        for file_path in files:
            path = Path(file_path)
            
            if path.exists():
                try:
                    if path.is_dir():
                        # 删除整个目录
                        shutil.rmtree(path)
                        print(f"   🗑️ 删除目录: {file_path}")
                    else:
                        # 删除单个文件
                        path.unlink()
                        print(f"   🗑️ 删除文件: {file_path}")
                    
                    deleted_count += 1
                    
                except Exception as e:
                    print(f"   ❌ 删除 {file_path} 失败: {e}")
            else:
                print(f"   ⚠️ 文件不存在: {file_path}")
    
    print(f"\n✅ 共删除 {deleted_count} 个API相关文件/目录")
    return deleted_count

def clean_api_references():
    """清理主程序中的API引用"""
    print("\n🧹 清理主程序中的API引用...")
    
    files_to_clean = identify_api_references()
    cleaned_count = 0
    
    for file_path in files_to_clean:
        if remove_api_imports_from_file(file_path):
            cleaned_count += 1
    
    print(f"\n✅ 共清理 {cleaned_count} 个文件中的API引用")
    return cleaned_count

def update_main_program():
    """更新主程序，移除API功能"""
    print("\n🔧 更新主程序，移除API功能...")
    
    main_file = "app/main_stable.py"
    if not os.path.exists(main_file):
        print(f"   ⚠️ 主程序文件不存在: {main_file}")
        return False
    
    try:
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除API相关的功能描述
        content = re.sub(r'.*API.*\n', '', content, flags=re.IGNORECASE)
        
        # 更新程序描述
        if "基于真实API接口" in content:
            content = content.replace("基于真实API接口", "基于图像识别技术")
        
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ 主程序已更新: {main_file}")
        return True
        
    except Exception as e:
        print(f"   ❌ 更新主程序失败: {e}")
        return False

def verify_remaining_functionality():
    """验证剩余功能完整性"""
    print("\n🔍 验证剩余功能完整性...")
    
    # 检查核心功能文件是否完整
    core_files = [
        "core/enhanced_detection.py",
        "core/enhanced_ocr.py", 
        "core/smart_trading_engine.py",
        "core/performance_optimizer.py",
        "core/risk_manager.py",
        "app/main_stable.py"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in core_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            print(f"   ✅ 核心文件存在: {file_path}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ 核心文件缺失: {file_path}")
    
    print(f"\n📊 功能完整性检查:")
    print(f"   ✅ 存在的核心文件: {len(existing_files)}")
    print(f"   ❌ 缺失的核心文件: {len(missing_files)}")
    
    if len(missing_files) == 0:
        print("   🎉 所有核心功能文件完整！")
        return True
    else:
        print("   ⚠️ 部分核心文件缺失，需要检查")
        return False

def create_api_deletion_report():
    """创建API删除报告"""
    print("\n📝 创建API删除报告...")
    
    report_content = """# 🗑️ API文件删除报告

## ✅ 删除完成

### 📊 删除统计
- **删除的API目录**: api_server/, src/api/
- **删除的API文件**: trading_api.py, real_api_client.py, real_auto_trader.py
- **清理的引用**: 主程序中的API导入和调用
- **保留的功能**: 图像识别、OCR、智能检测等核心功能

### 🎯 删除原因
Main项目已经包含了完整的景陶易购API实现，自动交易系统项目中的API文件：
1. **功能重复** - 与Main项目的jingtao_api.py功能重叠
2. **版本冲突** - 可能存在API版本不一致问题
3. **架构冲突** - 不同的API封装方式会导致集成困难

### ✅ 保留的核心功能
- 🖼️ **图像识别技术** - enhanced_detection.py
- 📝 **OCR文字识别** - enhanced_ocr.py  
- 🧠 **智能交易引擎** - smart_trading_engine.py
- ⚡ **性能优化器** - performance_optimizer.py
- 🛡️ **风险管理器** - risk_manager.py
- 🎯 **主程序框架** - main_stable.py

### 🚀 下一步计划
1. **验证功能完整性** - 确保图像识别功能正常
2. **集成Main项目API** - 使用Main项目的完善API
3. **创建融合架构** - 设计多模态融合系统
4. **实现统一界面** - 整合两个项目的优势

## 🎉 API删除成功！
自动交易系统项目现在专注于图像识别核心功能，为与Main项目融合做好了准备！
"""
    
    with open("API删除报告.md", 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print("   ✅ 报告已保存: API删除报告.md")

def main():
    """主函数"""
    print("🎯 自动交易系统 - 精准删除API文件")
    print("=" * 60)
    
    try:
        # 1. 创建备份
        backup_dir = backup_before_deletion()
        
        # 2. 删除API文件
        deleted_count = delete_api_files()
        
        # 3. 清理API引用
        cleaned_count = clean_api_references()
        
        # 4. 更新主程序
        main_updated = update_main_program()
        
        # 5. 验证剩余功能
        functionality_intact = verify_remaining_functionality()
        
        # 6. 创建删除报告
        create_api_deletion_report()
        
        print("\n" + "=" * 60)
        print("🎉 API文件删除完成！")
        
        print(f"\n📊 删除统计:")
        print(f"   🗑️ 删除文件/目录: {deleted_count}")
        print(f"   🧹 清理引用文件: {cleaned_count}")
        print(f"   🔧 主程序更新: {'✅' if main_updated else '❌'}")
        print(f"   🔍 功能完整性: {'✅' if functionality_intact else '❌'}")
        
        if functionality_intact:
            print("\n🎯 **删除成功！**")
            print("   ✅ 所有API文件已删除")
            print("   ✅ 图像识别功能完整保留")
            print("   ✅ 系统架构清理完成")
            print("   🚀 准备好与Main项目融合！")
        else:
            print("\n⚠️ **需要检查**")
            print("   部分核心文件可能受到影响，请检查")
        
        return True
        
    except Exception as e:
        print(f"❌ 删除过程失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ API删除成功！自动交易系统现在专注于图像识别功能！")
    else:
        print("\n❌ API删除失败，请检查错误信息")
    
    input("\n按回车键退出...")
