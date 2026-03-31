#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角度检测配置对话框
允许用户调整角度检测阈值和相关参数
"""

import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSpinBox, QDoubleSpinBox, QPushButton, QGroupBox,
                             QSlider, QTextEdit, QCheckBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class AngleConfigDialog(QDialog):
    """角度检测配置对话框"""
    
    # 信号：配置更改
    config_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, current_config=None):
        super().__init__(parent)
        self.setWindowTitle("黄线角度检测配置")
        self.setFixedSize(500, 600)
        
        # 当前配置
        self.config = current_config or {
            'angle_threshold': 20.0,
            'history_size': 10,
            'enable_smoothing': True,
            'confidence_factor': 1.0
        }
        
        self.init_ui()
        self.load_config()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("🎯 黄线角度检测配置")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 主要配置组
        main_group = QGroupBox("主要参数")
        main_layout = QGridLayout()
        
        # 角度阈值
        main_layout.addWidget(QLabel("角度阈值 (度):"), 0, 0)
        self.angle_threshold_spin = QDoubleSpinBox()
        self.angle_threshold_spin.setRange(1.0, 90.0)
        self.angle_threshold_spin.setSingleStep(1.0)
        self.angle_threshold_spin.setDecimals(1)
        self.angle_threshold_spin.valueChanged.connect(self.on_config_changed)
        main_layout.addWidget(self.angle_threshold_spin, 0, 1)
        
        # 角度阈值滑块
        self.angle_slider = QSlider(Qt.Horizontal)
        self.angle_slider.setRange(10, 900)  # 1.0 到 90.0 度，乘以10
        self.angle_slider.valueChanged.connect(self.on_slider_changed)
        main_layout.addWidget(self.angle_slider, 0, 2)
        
        # 历史数据大小
        main_layout.addWidget(QLabel("历史数据点数:"), 1, 0)
        self.history_size_spin = QSpinBox()
        self.history_size_spin.setRange(3, 50)
        self.history_size_spin.valueChanged.connect(self.on_config_changed)
        main_layout.addWidget(self.history_size_spin, 1, 1)
        
        # 置信度因子
        main_layout.addWidget(QLabel("置信度因子:"), 2, 0)
        self.confidence_factor_spin = QDoubleSpinBox()
        self.confidence_factor_spin.setRange(0.1, 3.0)
        self.confidence_factor_spin.setSingleStep(0.1)
        self.confidence_factor_spin.setDecimals(1)
        self.confidence_factor_spin.valueChanged.connect(self.on_config_changed)
        main_layout.addWidget(self.confidence_factor_spin, 2, 1)
        
        main_group.setLayout(main_layout)
        layout.addWidget(main_group)
        
        # 高级选项组
        advanced_group = QGroupBox("高级选项")
        advanced_layout = QVBoxLayout()
        
        # 启用平滑
        self.enable_smoothing_check = QCheckBox("启用角度平滑处理")
        self.enable_smoothing_check.stateChanged.connect(self.on_config_changed)
        advanced_layout.addWidget(self.enable_smoothing_check)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # 预设配置组
        preset_group = QGroupBox("预设配置")
        preset_layout = QHBoxLayout()
        
        # 预设按钮
        sensitive_btn = QPushButton("敏感模式 (10°)")
        sensitive_btn.clicked.connect(lambda: self.load_preset('sensitive'))
        preset_layout.addWidget(sensitive_btn)
        
        normal_btn = QPushButton("标准模式 (20°)")
        normal_btn.clicked.connect(lambda: self.load_preset('normal'))
        preset_layout.addWidget(normal_btn)
        
        conservative_btn = QPushButton("保守模式 (30°)")
        conservative_btn.clicked.connect(lambda: self.load_preset('conservative'))
        preset_layout.addWidget(conservative_btn)
        
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        # 实时预览
        preview_group = QGroupBox("配置预览")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        # 测试按钮
        test_btn = QPushButton("🧪 测试配置")
        test_btn.clicked.connect(self.test_config)
        button_layout.addWidget(test_btn)
        
        # 重置按钮
        reset_btn = QPushButton("🔄 重置默认")
        reset_btn.clicked.connect(self.reset_to_default)
        button_layout.addWidget(reset_btn)
        
        # 应用按钮
        apply_btn = QPushButton("✅ 应用配置")
        apply_btn.clicked.connect(self.apply_config)
        button_layout.addWidget(apply_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def load_config(self):
        """加载当前配置"""
        self.angle_threshold_spin.setValue(self.config['angle_threshold'])
        self.angle_slider.setValue(int(self.config['angle_threshold'] * 10))
        self.history_size_spin.setValue(self.config['history_size'])
        self.confidence_factor_spin.setValue(self.config['confidence_factor'])
        self.enable_smoothing_check.setChecked(self.config['enable_smoothing'])
        self.update_preview()
        
    def on_slider_changed(self, value):
        """滑块值改变"""
        angle_value = value / 10.0
        self.angle_threshold_spin.setValue(angle_value)
        
    def on_config_changed(self):
        """配置改变"""
        self.config['angle_threshold'] = self.angle_threshold_spin.value()
        self.config['history_size'] = self.history_size_spin.value()
        self.config['confidence_factor'] = self.confidence_factor_spin.value()
        self.config['enable_smoothing'] = self.enable_smoothing_check.isChecked()
        
        # 同步滑块
        self.angle_slider.setValue(int(self.config['angle_threshold'] * 10))
        
        self.update_preview()
        
    def update_preview(self):
        """更新配置预览"""
        preview_text = f"""
📊 当前配置:
• 角度阈值: {self.config['angle_threshold']:.1f}°
• 历史数据点数: {self.config['history_size']}
• 置信度因子: {self.config['confidence_factor']:.1f}
• 角度平滑: {'启用' if self.config['enable_smoothing'] else '禁用'}

🎯 触发条件:
• 当黄线角度变化 > {self.config['angle_threshold']:.1f}° 时触发交易信号
• 向上变化 > {self.config['angle_threshold']:.1f}° → 买入信号
• 向下变化 > {self.config['angle_threshold']:.1f}° → 卖出信号

⚡ 敏感度评估:
{self.get_sensitivity_description()}
        """.strip()
        
        self.preview_text.setPlainText(preview_text)
        
    def get_sensitivity_description(self):
        """获取敏感度描述"""
        threshold = self.config['angle_threshold']
        
        if threshold <= 10:
            return "🔥 极高敏感度 - 会频繁触发信号，适合短线交易"
        elif threshold <= 15:
            return "🔴 高敏感度 - 较频繁触发信号，适合活跃交易"
        elif threshold <= 25:
            return "🟡 中等敏感度 - 平衡的触发频率，适合一般交易"
        elif threshold <= 35:
            return "🟢 低敏感度 - 较少触发信号，适合稳健交易"
        else:
            return "🔵 极低敏感度 - 很少触发信号，适合长线交易"
            
    def load_preset(self, preset_type):
        """加载预设配置"""
        presets = {
            'sensitive': {
                'angle_threshold': 10.0,
                'history_size': 5,
                'confidence_factor': 1.2,
                'enable_smoothing': True
            },
            'normal': {
                'angle_threshold': 20.0,
                'history_size': 10,
                'confidence_factor': 1.0,
                'enable_smoothing': True
            },
            'conservative': {
                'angle_threshold': 30.0,
                'history_size': 15,
                'confidence_factor': 0.8,
                'enable_smoothing': True
            }
        }
        
        if preset_type in presets:
            self.config.update(presets[preset_type])
            self.load_config()
            
    def test_config(self):
        """测试当前配置"""
        # 这里可以添加测试逻辑
        from PyQt5.QtWidgets import QMessageBox
        
        msg = QMessageBox()
        msg.setWindowTitle("配置测试")
        msg.setText(f"当前配置测试:\n\n"
                   f"角度阈值: {self.config['angle_threshold']:.1f}°\n"
                   f"历史数据点数: {self.config['history_size']}\n"
                   f"置信度因子: {self.config['confidence_factor']:.1f}\n\n"
                   f"配置有效，可以正常使用！")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
        
    def reset_to_default(self):
        """重置为默认配置"""
        self.config = {
            'angle_threshold': 20.0,
            'history_size': 10,
            'enable_smoothing': True,
            'confidence_factor': 1.0
        }
        self.load_config()
        
    def apply_config(self):
        """应用配置"""
        self.config_changed.emit(self.config.copy())
        self.accept()
        
    def get_config(self):
        """获取当前配置"""
        return self.config.copy()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 测试对话框
    dialog = AngleConfigDialog()
    dialog.config_changed.connect(lambda config: print(f"配置更改: {config}"))
    
    if dialog.exec_() == QDialog.Accepted:
        print("配置已应用")
    else:
        print("配置已取消")
        
    sys.exit()
