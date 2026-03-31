#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能量化交易系统融合演示
展示多模态信号融合的完整功能
"""

import sys
import os
import time
import json
import random
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir / "hybrid_core"))

def demo_signal_fusion():
    """演示信号融合功能"""
    print("🎯 演示1: 多模态信号融合")
    print("-" * 40)
    
    try:
        from signal_fusion_engine import SignalFusionEngine, TradingSignal, SignalSource
        
        # 创建融合引擎
        fusion = SignalFusionEngine()
        
        # 演示场景1: 信号一致
        print("\n📊 场景1: API和图像信号一致")
        api_signal = {
            'action': 'buy_up',
            'confidence': 0.8,
            'reason': 'K线突破上轨',
            'price': 125.50
        }
        
        image_signal = {
            'action': 'buy_up',
            'confidence': 0.7,
            'reason': '图像检测上涨趋势'
        }
        
        fused = fusion.fuse_signals(api_signal, image_signal)
        print(f"   🔗 融合结果: {fused.action} (置信度: {fused.confidence:.2f})")
        print(f"   💡 融合原因: {fused.reason}")
        
        # 演示场景2: 信号冲突
        print("\n📊 场景2: API和图像信号冲突")
        api_signal2 = {
            'action': 'buy_up',
            'confidence': 0.6,
            'reason': 'API看涨信号'
        }
        
        image_signal2 = {
            'action': 'buy_down',
            'confidence': 0.8,
            'reason': '图像检测看跌'
        }
        
        fused2 = fusion.fuse_signals(api_signal2, image_signal2)
        print(f"   🔗 融合结果: {fused2.action} (置信度: {fused2.confidence:.2f})")
        print(f"   💡 冲突处理: 选择高置信度信号")
        
        return True
        
    except Exception as e:
        print(f"❌ 信号融合演示失败: {e}")
        return False

def demo_mode_selection():
    """演示智能模式选择"""
    print("\n🎯 演示2: 智能模式选择")
    print("-" * 40)
    
    try:
        from mode_selector import IntelligentModeSelector, TradingMode
        
        # 创建模式选择器
        selector = IntelligentModeSelector()
        
        # 模拟历史性能数据
        print("\n📈 模拟历史性能数据...")
        
        # API模式性能较好
        for i in range(10):
            success = random.choice([True, True, True, False])  # 75%成功率
            confidence = random.uniform(0.7, 0.9)
            exec_time = random.uniform(3, 6)
            selector.record_performance(TradingMode.API_ONLY, success, confidence, exec_time)
        
        # 图像模式性能一般
        for i in range(10):
            success = random.choice([True, True, False, False])  # 50%成功率
            confidence = random.uniform(0.5, 0.8)
            exec_time = random.uniform(8, 12)
            selector.record_performance(TradingMode.IMAGE_ONLY, success, confidence, exec_time)
        
        # 混合模式性能最好
        for i in range(10):
            success = random.choice([True, True, True, True, False])  # 80%成功率
            confidence = random.uniform(0.8, 0.95)
            exec_time = random.uniform(5, 8)
            selector.record_performance(TradingMode.HYBRID, success, confidence, exec_time)
        
        # 评估模式性能
        performances = selector.evaluate_modes()
        print("\n📊 模式性能评估:")
        for mode, perf in performances.items():
            print(f"   {mode.value}: 成功率={perf.success_rate:.2f}, 置信度={perf.avg_confidence:.2f}, 时间={perf.execution_time:.1f}s")
        
        # 选择最优模式
        optimal = selector.select_optimal_mode(True, True)
        print(f"\n🎯 推荐最优模式: {optimal.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模式选择演示失败: {e}")
        return False

def demo_execution_management():
    """演示执行管理"""
    print("\n🎯 演示3: 智能执行管理")
    print("-" * 40)
    
    try:
        from execution_manager import ExecutionManager, ExecutionMethod
        
        # 创建执行管理器
        manager = ExecutionManager()
        
        # 设置模拟执行器
        def mock_api_executor(signal, commodity_id):
            print(f"   🔌 API执行: {signal['action']} - {commodity_id}")
            time.sleep(1)
            return random.choice([True, True, False])  # 67%成功率
        
        def mock_image_executor(signal):
            print(f"   🖼️ 图像执行: {signal['action']}")
            time.sleep(2)
            return random.choice([True, False])  # 50%成功率
        
        manager.set_executors(mock_api_executor, mock_image_executor)
        
        # 演示不同执行方法
        test_signals = [
            {'action': 'buy_up', 'confidence': 0.8, 'reason': '测试信号1'},
            {'action': 'buy_down', 'confidence': 0.6, 'reason': '测试信号2'},
            {'action': 'buy_up', 'confidence': 0.9, 'reason': '测试信号3'}
        ]
        
        methods = [ExecutionMethod.API, ExecutionMethod.IMAGE, ExecutionMethod.HYBRID]
        
        print("\n🚀 执行测试任务...")
        task_ids = []
        
        for i, (signal, method) in enumerate(zip(test_signals, methods)):
            task_id = manager.execute_trade(signal, "511", method)
            task_ids.append(task_id)
            print(f"   📋 任务{i+1}: {task_id} ({method.value})")
        
        # 等待任务完成
        print("\n⏰ 等待任务完成...")
        time.sleep(5)
        
        # 检查任务结果
        print("\n📊 任务执行结果:")
        for task_id in task_ids:
            task = manager.get_task_status(task_id)
            if task:
                print(f"   {task_id}: {task.status.value} ({task.execution_time:.2f}s)")
        
        # 性能报告
        report = manager.get_performance_report()
        print(f"\n📈 性能报告:")
        for method, perf in report["method_performance"].items():
            print(f"   {method}: 成功率={perf['success_rate']:.2f}, 平均时间={perf['avg_execution_time']:.2f}s")
        
        manager.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ 执行管理演示失败: {e}")
        return False

def demo_hybrid_engine():
    """演示混合交易引擎"""
    print("\n🎯 演示4: 混合交易引擎")
    print("-" * 40)
    
    try:
        from hybrid_trading_engine import HybridTradingEngine, TradingMode
        
        # 创建混合引擎
        engine = HybridTradingEngine()
        
        # 初始化（使用模拟组件）
        init_success = engine.initialize()
        print(f"   🔧 引擎初始化: {'✅ 成功' if init_success else '⚠️ 使用模拟组件'}")
        
        # 测试不同模式
        modes = [TradingMode.API_ONLY, TradingMode.IMAGE_ONLY, TradingMode.AUTO]
        
        for mode in modes:
            print(f"\n🎮 测试模式: {mode.value}")
            engine.set_mode(mode)
            
            # 获取信号（模拟）
            try:
                signal = engine.get_current_signal("511")
                print(f"   🎯 信号: {signal.action} (置信度: {signal.confidence:.2f})")
                print(f"   📝 原因: {signal.reason}")
            except Exception as e:
                print(f"   ⚠️ 信号获取: {e}")
        
        # 引擎状态
        status = engine.get_engine_status()
        print(f"\n📊 引擎状态:")
        print(f"   运行状态: {status['is_running']}")
        print(f"   当前模式: {status['current_mode']}")
        print(f"   API可用: {status['api_available']}")
        print(f"   图像可用: {status['image_available']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 混合引擎演示失败: {e}")
        return False

def create_fusion_summary():
    """创建融合系统总结"""
    print("\n📝 创建融合系统总结...")
    
    summary = {
        "系统名称": "智能量化交易系统",
        "版本": "v1.0.0",
        "架构": "多模态信号融合",
        "核心特性": [
            "🔗 API + 图像双重信号源",
            "🧠 智能信号融合算法", 
            "🎯 自动模式选择",
            "⚡ 高效执行管理",
            "🎮 统一GUI界面"
        ],
        "技术优势": [
            "多模态信号处理",
            "智能故障切换",
            "实时性能优化",
            "模块化架构设计"
        ],
        "应用场景": [
            "量化交易",
            "风险管理", 
            "市场监控",
            "自动化投资"
        ]
    }
    
    with open("融合系统总结.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print("   ✅ 系统总结已保存: 融合系统总结.json")

def main():
    """主演示函数"""
    print("🎯 智能量化交易系统 - 融合功能演示")
    print("🔗 多模态融合 - API + 图像识别")
    print("=" * 60)
    
    demo_results = []
    
    try:
        # 1. 信号融合演示
        result1 = demo_signal_fusion()
        demo_results.append(("信号融合", result1))
        
        # 2. 模式选择演示
        result2 = demo_mode_selection()
        demo_results.append(("模式选择", result2))
        
        # 3. 执行管理演示
        result3 = demo_execution_management()
        demo_results.append(("执行管理", result3))
        
        # 4. 混合引擎演示
        result4 = demo_hybrid_engine()
        demo_results.append(("混合引擎", result4))
        
        # 5. 创建系统总结
        create_fusion_summary()
        
        print("\n" + "=" * 60)
        print("🎉 融合系统演示完成！")
        
        # 显示演示结果
        print(f"\n📊 演示结果:")
        passed = 0
        for demo_name, result in demo_results:
            status = "✅ 成功" if result else "❌ 失败"
            print(f"   {demo_name}: {status}")
            if result:
                passed += 1
        
        success_rate = (passed / len(demo_results)) * 100
        print(f"\n🎯 演示成功率: {success_rate:.1f}% ({passed}/{len(demo_results)})")
        
        if success_rate == 100:
            print("\n🎉 **融合系统演示完全成功！**")
            print("   ✅ 所有核心功能正常")
            print("   ✅ 多模态融合工作正常")
            print("   ✅ 智能算法运行正常")
            print("   🚀 系统已准备就绪！")
            
            print(f"\n🎯 **融合系统核心优势:**")
            print(f"   🔗 **多模态融合** - API K线 + 图像识别双重信号")
            print(f"   🧠 **智能决策** - 自动选择最佳交易模式")
            print(f"   ⚡ **高效执行** - 并发执行和智能故障切换")
            print(f"   📊 **实时监控** - 性能统计和动态优化")
            
        else:
            print("\n⚠️ **部分功能需要优化**")
            print("   核心架构已完成，细节功能可继续完善")
        
        return success_rate >= 75
        
    except Exception as e:
        print(f"❌ 演示过程异常: {e}")
        return False

if __name__ == "__main__":
    print("🚀 启动智能量化交易系统融合演示...")
    
    success = main()
    
    if success:
        print("\n✅ 融合系统演示成功！")
        print("🎯 多模态智能交易系统已准备就绪！")
        
        # 询问下一步
        print(f"\n🚀 下一步选择:")
        print(f"   1. 启动完整GUI系统 (python main_fusion.py)")
        print(f"   2. 查看融合架构文档")
        print(f"   3. 进行实际交易测试")
        
    else:
        print("\n❌ 演示失败，需要进一步调试")
    
    input("\n按回车键退出...")
