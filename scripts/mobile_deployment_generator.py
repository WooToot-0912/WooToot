#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动端部署配置生成器
版本: v1.0

功能:
1. 生成Android部署配置
2. 生成iOS部署配置
3. 生成跨平台部署方案
4. 自动化打包脚本生成
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class MobileDeploymentGenerator:
    """移动端部署配置生成器"""
    
    def __init__(self, output_dir: str = "deployment"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 部署配置模板
        self.deployment_templates = {
            'android': {
                'runtime': 'onnxruntime-android',
                'model_format': 'onnx',
                'optimization_level': 'all',
                'execution_providers': ['CPUExecutionProvider'],
                'target_architectures': ['arm64-v8a', 'armeabi-v7a'],
                'min_sdk_version': 21,
                'target_sdk_version': 33,
                'max_model_size_mb': 50,
                'memory_limit_mb': 512
            },
            'ios': {
                'runtime': 'coreml',
                'model_format': 'mlmodel',
                'optimization_level': 'all',
                'target_architectures': ['arm64'],
                'min_ios_version': '12.0',
                'max_model_size_mb': 50,
                'memory_limit_mb': 512,
                'compute_units': 'cpuAndGPU'
            }
        }
    
    def generate_android_config(self, model_path: str, app_name: str = "TobaccoDetector") -> Dict[str, Any]:
        """生成Android部署配置"""
        print("📱 生成Android部署配置...")
        
        config = {
            'app_info': {
                'name': app_name,
                'package_name': f'com.tobacco.{app_name.lower()}',
                'version_code': 1,
                'version_name': '1.0.0',
                'min_sdk_version': self.deployment_templates['android']['min_sdk_version'],
                'target_sdk_version': self.deployment_templates['android']['target_sdk_version']
            },
            'model_config': {
                'model_path': model_path,
                'model_format': self.deployment_templates['android']['model_format'],
                'input_size': [640, 640],
                'num_classes': 5,
                'class_names': ['健康', '花叶病毒', '黑胫病', '青枯病', '炭疽病']
            },
            'runtime_config': {
                'runtime': self.deployment_templates['android']['runtime'],
                'execution_providers': self.deployment_templates['android']['execution_providers'],
                'optimization_level': self.deployment_templates['android']['optimization_level'],
                'inter_op_num_threads': 4,
                'intra_op_num_threads': 4
            },
            'build_config': {
                'target_architectures': self.deployment_templates['android']['target_architectures'],
                'gradle_version': '7.4',
                'android_gradle_plugin': '7.2.0',
                'compile_sdk_version': 33,
                'build_tools_version': '33.0.0'
            },
            'performance_config': {
                'max_model_size_mb': self.deployment_templates['android']['max_model_size_mb'],
                'memory_limit_mb': self.deployment_templates['android']['memory_limit_mb'],
                'batch_size': 1,
                'enable_gpu_acceleration': False,
                'enable_nnapi': True
            }
        }
        
        # 保存Android配置
        android_config_path = self.output_dir / "android_config.json"
        with open(android_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Android配置已保存: {android_config_path}")
        return config
    
    def generate_ios_config(self, model_path: str, app_name: str = "TobaccoDetector") -> Dict[str, Any]:
        """生成iOS部署配置"""
        print("🍎 生成iOS部署配置...")
        
        config = {
            'app_info': {
                'name': app_name,
                'bundle_identifier': f'com.tobacco.{app_name.lower()}',
                'version': '1.0.0',
                'build': '1',
                'min_ios_version': self.deployment_templates['ios']['min_ios_version'],
                'target_architectures': self.deployment_templates['ios']['target_architectures']
            },
            'model_config': {
                'model_path': model_path,
                'model_format': self.deployment_templates['ios']['model_format'],
                'input_size': [640, 640],
                'num_classes': 5,
                'class_names': ['健康', '花叶病毒', '黑胫病', '青枯病', '炭疽病']
            },
            'runtime_config': {
                'runtime': self.deployment_templates['ios']['runtime'],
                'compute_units': self.deployment_templates['ios']['compute_units'],
                'optimization_level': self.deployment_templates['ios']['optimization_level']
            },
            'build_config': {
                'xcode_version': '14.0',
                'swift_version': '5.7',
                'deployment_target': self.deployment_templates['ios']['min_ios_version'],
                'frameworks': ['CoreML', 'Vision', 'UIKit', 'AVFoundation']
            },
            'performance_config': {
                'max_model_size_mb': self.deployment_templates['ios']['max_model_size_mb'],
                'memory_limit_mb': self.deployment_templates['ios']['memory_limit_mb'],
                'batch_size': 1,
                'enable_gpu_acceleration': True,
                'enable_neural_engine': True
            }
        }
        
        # 保存iOS配置
        ios_config_path = self.output_dir / "ios_config.json"
        with open(ios_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"✅ iOS配置已保存: {ios_config_path}")
        return config
    
    def generate_android_gradle_script(self, config: Dict[str, Any]) -> str:
        """生成Android Gradle构建脚本"""
        gradle_content = f'''
apply plugin: 'com.android.application'

android {{
    compileSdkVersion {config['build_config']['compile_sdk_version']}
    buildToolsVersion "{config['build_config']['build_tools_version']}"
    
    defaultConfig {{
        applicationId "{config['app_info']['package_name']}"
        minSdkVersion {config['app_info']['min_sdk_version']}
        targetSdkVersion {config['app_info']['target_sdk_version']}
        versionCode {config['app_info']['version_code']}
        versionName "{config['app_info']['version_name']}"
        
        ndk {{
            abiFilters {', '.join([f'"{arch}"' for arch in config['build_config']['target_architectures']])}
        }}
    }}
    
    buildTypes {{
        release {{
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
    }}
}}

dependencies {{
    implementation 'com.microsoft.onnxruntime:onnxruntime-android:1.15.1'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
    implementation 'androidx.camera:camera-core:1.2.3'
    implementation 'androidx.camera:camera-camera2:1.2.3'
    implementation 'androidx.camera:camera-lifecycle:1.2.3'
    implementation 'androidx.camera:camera-view:1.2.3'
}}
'''
        
        gradle_path = self.output_dir / "build.gradle"
        with open(gradle_path, 'w', encoding='utf-8') as f:
            f.write(gradle_content.strip())
        
        print(f"✅ Android Gradle脚本已生成: {gradle_path}")
        return str(gradle_path)
    
    def generate_ios_podfile(self, config: Dict[str, Any]) -> str:
        """生成iOS Podfile"""
        podfile_content = f'''
platform :ios, '{config['app_info']['min_ios_version']}'

target '{config['app_info']['name']}' do
  use_frameworks!
  
  # UI框架
  pod 'SnapKit', '~> 5.6.0'
  
  # 图像处理
  pod 'GPUImage2', '~> 3.0'
  
  # 网络请求
  pod 'Alamofire', '~> 5.6'
  
  # JSON解析
  pod 'SwiftyJSON', '~> 5.0'
  
  target '{config['app_info']['name']}Tests' do
    inherit! :search_paths
  end
  
  target '{config['app_info']['name']}UITests' do
    inherit! :search_paths
  end
end

post_install do |installer|
  installer.pods_project.targets.each do |target|
    target.build_configurations.each do |config|
      config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '{config['app_info']['min_ios_version']}'
    end
  end
end
'''
        
        podfile_path = self.output_dir / "Podfile"
        with open(podfile_path, 'w', encoding='utf-8') as f:
            f.write(podfile_content.strip())
        
        print(f"✅ iOS Podfile已生成: {podfile_path}")
        return str(podfile_path)
    
    def generate_deployment_scripts(self, android_config: Dict, ios_config: Dict) -> Dict[str, str]:
        """生成部署脚本"""
        scripts = {}
        
        # Android部署脚本
        android_script = f'''#!/bin/bash
# Android部署脚本

echo "🚀 开始Android应用构建..."

# 检查环境
if [ ! -d "$ANDROID_HOME" ]; then
    echo "❌ ANDROID_HOME未设置"
    exit 1
fi

# 清理项目
./gradlew clean

# 构建APK
./gradlew assembleRelease

# 检查构建结果
if [ -f "app/build/outputs/apk/release/app-release.apk" ]; then
    echo "✅ Android APK构建成功"
    echo "📦 APK路径: app/build/outputs/apk/release/app-release.apk"
else
    echo "❌ Android APK构建失败"
    exit 1
fi
'''
        
        android_script_path = self.output_dir / "deploy_android.sh"
        with open(android_script_path, 'w', encoding='utf-8') as f:
            f.write(android_script.strip())
        os.chmod(android_script_path, 0o755)
        scripts['android'] = str(android_script_path)
        
        # iOS部署脚本
        ios_script = f'''#!/bin/bash
# iOS部署脚本

echo "🚀 开始iOS应用构建..."

# 检查Xcode
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Xcode未安装"
    exit 1
fi

# 安装依赖
pod install

# 构建项目
xcodebuild -workspace {ios_config['app_info']['name']}.xcworkspace \\
           -scheme {ios_config['app_info']['name']} \\
           -configuration Release \\
           -destination generic/platform=iOS \\
           archive -archivePath build/{ios_config['app_info']['name']}.xcarchive

# 导出IPA
xcodebuild -exportArchive \\
           -archivePath build/{ios_config['app_info']['name']}.xcarchive \\
           -exportPath build/ \\
           -exportOptionsPlist ExportOptions.plist

echo "✅ iOS应用构建完成"
echo "📦 IPA路径: build/{ios_config['app_info']['name']}.ipa"
'''
        
        ios_script_path = self.output_dir / "deploy_ios.sh"
        with open(ios_script_path, 'w', encoding='utf-8') as f:
            f.write(ios_script.strip())
        os.chmod(ios_script_path, 0o755)
        scripts['ios'] = str(ios_script_path)
        
        print(f"✅ 部署脚本已生成")
        return scripts
    
    def generate_complete_deployment_package(self, model_path: str, app_name: str = "TobaccoDetector") -> Dict[str, Any]:
        """生成完整的移动端部署包"""
        print("📦 生成完整移动端部署包...")
        
        # 生成配置
        android_config = self.generate_android_config(model_path, app_name)
        ios_config = self.generate_ios_config(model_path, app_name)
        
        # 生成构建脚本
        gradle_script = self.generate_android_gradle_script(android_config)
        podfile = self.generate_ios_podfile(ios_config)
        
        # 生成部署脚本
        deployment_scripts = self.generate_deployment_scripts(android_config, ios_config)
        
        # 生成README
        readme_content = f'''# {app_name} 移动端部署包

## 项目概述
云南烤烟病害检测移动应用部署包，支持Android和iOS平台。

## 生成时间
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 目录结构
```
deployment/
├── android_config.json      # Android配置文件
├── ios_config.json         # iOS配置文件
├── build.gradle           # Android构建脚本
├── Podfile               # iOS依赖管理
├── deploy_android.sh     # Android部署脚本
├── deploy_ios.sh        # iOS部署脚本
└── README.md           # 本文件
```

## Android部署
1. 确保Android SDK已安装
2. 运行: `./deploy_android.sh`
3. APK文件将生成在 `app/build/outputs/apk/release/`

## iOS部署
1. 确保Xcode已安装
2. 运行: `pod install`
3. 运行: `./deploy_ios.sh`
4. IPA文件将生成在 `build/` 目录

## 模型配置
- **模型路径**: {model_path}
- **输入尺寸**: 640x640
- **类别数量**: 5
- **支持格式**: ONNX (Android), CoreML (iOS)

## 性能要求
- **最大模型大小**: 50MB
- **内存限制**: 512MB
- **最小Android版本**: API 21 (Android 5.0)
- **最小iOS版本**: iOS 12.0

## 技术支持
如有问题，请联系开发团队。
'''
        
        readme_path = self.output_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 汇总结果
        deployment_package = {
            'timestamp': datetime.now().isoformat(),
            'app_name': app_name,
            'model_path': model_path,
            'output_directory': str(self.output_dir),
            'android_config': android_config,
            'ios_config': ios_config,
            'generated_files': {
                'android_gradle': gradle_script,
                'ios_podfile': podfile,
                'deployment_scripts': deployment_scripts,
                'readme': str(readme_path)
            }
        }
        
        # 保存部署包信息
        package_info_path = self.output_dir / "deployment_package.json"
        with open(package_info_path, 'w', encoding='utf-8') as f:
            json.dump(deployment_package, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 完整移动端部署包已生成: {self.output_dir}")
        return deployment_package


def main():
    """主函数"""
    print("📱 移动端部署配置生成器")
    print("=" * 40)
    
    # 配置参数
    model_path = "models/optimized/quantized_int8.onnx"
    app_name = "TobaccoDetector"
    output_dir = "deployment/mobile"
    
    # 创建生成器
    generator = MobileDeploymentGenerator(output_dir)
    
    # 生成完整部署包
    package = generator.generate_complete_deployment_package(model_path, app_name)
    
    print(f"\n✅ 移动端部署包生成完成!")
    print(f"📁 输出目录: {package['output_directory']}")
    print(f"📱 Android配置: android_config.json")
    print(f"🍎 iOS配置: ios_config.json")
    print(f"📄 详细说明: README.md")


if __name__ == "__main__":
    main()
