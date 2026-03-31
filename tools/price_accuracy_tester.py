#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格准确性测试工具
用于测试和优化各种价格检测方法的准确性
"""

import sys
import os
import time
import pyautogui
import numpy as np
import cv2

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'src'))

try:
    from trading.real_price_detector import RealPriceDetectorEnhanced
    from trading.trading_engine import SmartTradingEngine
    from trading.candlestick_detector import CandlestickColorDetector
    CANDLESTICK_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 部分模块导入失败: {e}")
    CANDLESTICK_AVAILABLE = False

class PriceAccuracyTester:
    """价格准确性测试器"""
    
    def __init__(self):
        self.detector = RealPriceDetectorEnhanced(use_manual_selection=True)
        self.test_results = []
    
    def run_comprehensive_test(self, test_duration=60):
        """
        运行综合测试
        test_duration: 测试时长（秒）
        """
        print(f"🚀 开始价格检测准确性测试 (时长: {test_duration}秒)")
        print("=" * 60)
        
        start_time = time.time()
        test_count = 0
        
        while time.time() - start_time < test_duration:
            test_count += 1
            print(f"\n🔍 第 {test_count} 次测试:")
            
            # 获取屏幕截图
            screenshot = pyautogui.screenshot()
            
            # 测试所有方法
            results = self.test_all_methods(screenshot)
            
            # 分析结果
            analysis = self.analyze_results(results)
            
            # 保存结果
            self.test_results.append({
                'timestamp': time.time(),
                'test_id': test_count,
                'results': results,
                'analysis': analysis
            })
            
            # 显示结果
            self.display_test_result(test_count, results, analysis)
            
            # 等待间隔
            time.sleep(5)
        
        # 生成最终报告
        self.generate_final_report()
    
    def test_all_methods(self, screenshot):
        """测试所有价格检测方法"""
        methods = {
            '手动区域': lambda: self.detector._get_price_from_manual_region('current_price'),
            '颜色检测': lambda: self.detector.get_price_by_color_detection(screenshot, debug=False),
            '模板匹配': lambda: self.detector.get_price_by_template_matching(screenshot, debug=False),
            '增强OCR': lambda: self.detector.get_price_from_screen_ocr_enhanced(debug=False),
            '综合方法': lambda: self.detector.get_price_enhanced_fallback(debug=False),
        }
        
        results = {}
        
        for method_name, method_func in methods.items():
            try:
                start_time = time.time()
                price = method_func()
                duration = time.time() - start_time
                
                results[method_name] = {
                    'price': price,
                    'duration': duration,
                    'success': price is not None and isinstance(price, (int, float)) and 100 <= price <= 100000,
                    'error': None
                }
            except Exception as e:
                results[method_name] = {
                    'price': None,
                    'duration': 0,
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def analyze_results(self, results):
        """分析测试结果"""
        successful_methods = [name for name, result in results.items() if result['success']]
        successful_prices = [result['price'] for result in results.values() if result['success']]
        
        analysis = {
            'success_count': len(successful_methods),
            'successful_methods': successful_methods,
            'price_variance': 0,
            'recommended_price': None,
            'consistency_score': 0
        }
        
        if successful_prices:
            # 计算价格方差
            if len(successful_prices) > 1:
                mean_price = sum(successful_prices) / len(successful_prices)
                variance = sum((p - mean_price) ** 2 for p in successful_prices) / len(successful_prices)
                analysis['price_variance'] = variance
            
            # 推荐价格（中位数）
            successful_prices.sort()
            analysis['recommended_price'] = successful_prices[len(successful_prices) // 2]
            
            # 一致性评分（价格差异越小分数越高）
            if len(successful_prices) > 1:
                max_price = max(successful_prices)
                min_price = min(successful_prices)
                price_range = max_price - min_price
                # 一致性评分：价格差异小于5%得满分
                if price_range / analysis['recommended_price'] < 0.05:
                    analysis['consistency_score'] = 100
                else:
                    analysis['consistency_score'] = max(0, 100 - (price_range / analysis['recommended_price'] * 100))
            else:
                analysis['consistency_score'] = 100
        
        return analysis
    
    def display_test_result(self, test_id, results, analysis):
        """显示单次测试结果"""
        print(f"📊 测试结果:")
        
        for method_name, result in results.items():
            status = "✅" if result['success'] else "❌"
            price_str = f"{result['price']:.1f}" if result['price'] else "N/A"
            duration_str = f"{result['duration']:.3f}s"
            error_str = f" ({result['error']})" if result['error'] else ""
            
            print(f"  {status} {method_name:12} | 价格: {price_str:8} | 耗时: {duration_str:8}{error_str}")
        
        print(f"🎯 分析结果:")
        print(f"  • 成功方法数: {analysis['success_count']}/5")
        print(f"  • 推荐价格: {analysis['recommended_price']:.1f}" if analysis['recommended_price'] else "  • 推荐价格: N/A")
        print(f"  • 一致性评分: {analysis['consistency_score']:.1f}%")
        print(f"  • 价格方差: {analysis['price_variance']:.2f}")
    
    def generate_final_report(self):
        """生成最终测试报告"""
        if not self.test_results:
            print("❌ 没有测试数据")
            return
        
        print("\n" + "=" * 60)
        print("📋 最终测试报告")
        print("=" * 60)
        
        # 统计各方法成功率
        method_stats = {}
        total_tests = len(self.test_results)
        
        for test in self.test_results:
            for method_name, result in test['results'].items():
                if method_name not in method_stats:
                    method_stats[method_name] = {
                        'success_count': 0,
                        'total_duration': 0,
                        'prices': []
                    }
                
                if result['success']:
                    method_stats[method_name]['success_count'] += 1
                    method_stats[method_name]['prices'].append(result['price'])
                
                method_stats[method_name]['total_duration'] += result['duration']
        
        print(f"\n📈 方法性能统计 (总测试次数: {total_tests}):")
        print("-" * 60)
        
        for method_name, stats in method_stats.items():
            success_rate = (stats['success_count'] / total_tests) * 100
            avg_duration = stats['total_duration'] / total_tests
            
            price_info = ""
            if stats['prices']:
                avg_price = sum(stats['prices']) / len(stats['prices'])
                price_std = np.std(stats['prices']) if len(stats['prices']) > 1 else 0
                price_info = f" | 平均价格: {avg_price:.1f}±{price_std:.1f}"
            
            print(f"{method_name:12} | 成功率: {success_rate:5.1f}% | 平均耗时: {avg_duration:.3f}s{price_info}")
        
        # 推荐最佳方法
        best_method = max(method_stats.items(), key=lambda x: x[1]['success_count'])
        print(f"\n🏆 推荐方法: {best_method[0]} (成功率: {(best_method[1]['success_count']/total_tests)*100:.1f}%)")
        
        # 一致性分析
        consistency_scores = [test['analysis']['consistency_score'] for test in self.test_results if test['analysis']['consistency_score'] > 0]
        if consistency_scores:
            avg_consistency = sum(consistency_scores) / len(consistency_scores)
            print(f"📊 平均一致性评分: {avg_consistency:.1f}%")
        
        print("\n💡 优化建议:")
        if method_stats['综合方法']['success_count'] / total_tests < 0.8:
            print("  • 建议优化综合检测方法的参数")
        if method_stats['手动区域']['success_count'] / total_tests < 0.5:
            print("  • 建议重新配置手动区域坐标")
        if avg_consistency < 80:
            print("  • 建议增加价格验证和过滤机制")


def test_candlestick_detection():
    """K线颜色检测调试功能"""
    if not CANDLESTICK_AVAILABLE:
        print("❌ K线检测模块不可用")
        return
    
    print("🔵 K线颜色检测调试开始...")
    print("请确保景陶易购客户端窗口可见")
    
    # 初始化交易引擎 (使用默认配置)
    print("📄 初始化交易引擎...")
    
    try:
        # 创建简单配置对象以避免配置文件问题
        class SimpleConfig:
            def get(self, key, default=None):
                return default
        
        simple_config = SimpleConfig()
        engine = SmartTradingEngine(config=simple_config)
        print("✅ 交易引擎初始化成功")
        
        print("🔍 查找客户端窗口...")
        if not engine.find_client_window():
            print("❌ 找不到客户端窗口")
            print("   请确保景陶易购客户端已打开")
            return
        
        print(f"✅ 找到客户端窗口: {engine.window_rect}")
        
    except Exception as e:
        print(f"❌ 交易引擎初始化失败: {e}")
        return
    
    # 初始化K线检测器
    detector = CandlestickColorDetector(engine)
    
    # 创建调试输出目录
    debug_dir = "logs/candlestick_debug"
    os.makedirs(debug_dir, exist_ok=True)
    
    # 获取屏幕截图
    screenshot = pyautogui.screenshot()
    screenshot_array = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_array, cv2.COLOR_RGB2BGR)
    
    # 保存完整截图
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    full_path = os.path.join(debug_dir, f"full_screenshot_{timestamp}.jpg")
    cv2.imwrite(full_path, screenshot_bgr)
    print(f"📸 完整截图已保存: {full_path}")
    
    # 提取K线图区域
    chart_region = detector.get_chart_region(screenshot_bgr)
    if chart_region is None:
        print("❌ 无法提取K线图区域")
        return
    
    print(f"📊 K线图区域大小: {chart_region.shape}")
    
    # 保存K线图区域
    chart_path = os.path.join(debug_dir, f"chart_region_{timestamp}.jpg")
    cv2.imwrite(chart_path, chart_region)
    print(f"📊 K线图区域已保存: {chart_path}")
    
    # 测试颜色检测
    color_blocks = detector.detect_color_blocks(chart_region)
    print(f"🎨 检测结果:")
    print(f"  红色块数量: {len(color_blocks.get('red', []))}")
    print(f"  蓝色块数量: {len(color_blocks.get('blue', []))}")
    print(f"  青色块数量: {len(color_blocks.get('cyan', []))}")
    print(f"  绿色块数量: {len(color_blocks.get('green', []))}")
    
    # 创建可视化结果
    result_img = chart_region.copy()
    
    # 绘制检测到的红色块
    for red_block in color_blocks.get('red', []):
        x, y, w, h = red_block['bbox']
        cv2.rectangle(result_img, (x, y), (x+w, y+h), (0, 0, 255), 2)
        cv2.putText(result_img, 'RED', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    # 绘制检测到的蓝色块
    for blue_block in color_blocks.get('blue', []):
        x, y, w, h = blue_block['bbox']
        cv2.rectangle(result_img, (x, y), (x+w, y+h), (255, 0, 0), 2)
        # 根据颜色类型显示不同标签
        color_type = blue_block.get('color_type', 'blue')
        label = 'CYAN' if color_type == 'cyan' else 'BLUE'
        cv2.putText(result_img, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    
    # 绘制检测到的青色块 (单独显示)
    for cyan_block in color_blocks.get('cyan', []):
        x, y, w, h = cyan_block['bbox']
        cv2.rectangle(result_img, (x, y), (x+w, y+h), (255, 255, 0), 2)  # 用黄色边框标记青色块
        cv2.putText(result_img, 'CYAN', (x, y-30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    # 绘制检测到的绿色块
    for green_block in color_blocks.get('green', []):
        x, y, w, h = green_block['bbox']
        cv2.rectangle(result_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(result_img, 'GREEN', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # 保存检测结果
    result_path = os.path.join(debug_dir, f"detection_result_{timestamp}.jpg")
    cv2.imwrite(result_path, result_img)
    print(f"🎯 检测结果已保存: {result_path}")
    
    # 显示颜色范围调试建议
    print("\n💡 颜色范围调试建议:")
    total_blue_cyan = len(color_blocks.get('blue', [])) + len(color_blocks.get('cyan', []))
    if total_blue_cyan == 0:
        print("  • 蓝色/青色检测失败，建议调整HSV范围")
        print("  • 针对RGB(80,255,255)的HSV范围已更新: H=85-95, S=100-255, V=200-255")
        print("  • 通用蓝色范围: H=80-110, S=50-255, V=50-255")
    else:
        print(f"  ✅ 蓝色/青色检测成功! 总数: {total_blue_cyan} (蓝色: {len(color_blocks.get('blue', []))}, 青色: {len(color_blocks.get('cyan', []))})")
    
    if len(color_blocks.get('red', [])) == 0:
        print("  • 红色检测失败，建议调整HSV范围")
        print("  • 尝试HSV范围: H=0-15或160-180, S=30-255, V=30-255")
    else:
        print(f"  ✅ 红色检测成功! 数量: {len(color_blocks.get('red', []))}")
    
    print(f"\n📈 检测统计:")
    print(f"  • 最小面积阈值: {detector.min_candlestick_area}")
    print(f"  • 青色HSV范围: {detector.color_ranges['cyan']['lower']} - {detector.color_ranges['cyan']['upper']}")
    print(f"  • 蓝色HSV范围: {detector.color_ranges['blue']['lower']} - {detector.color_ranges['blue']['upper']}")
    
    print(f"\n📁 所有调试文件已保存到: {debug_dir}")


def main():
    """主函数"""
    print("🎯 价格检测与K线调试工具")
    print("请确保景陶易购客户端窗口可见")
    print("\n请选择测试模式:")
    print("1. 价格检测准确性测试 (原有功能)")
    print("2. K线颜色检测调试 (新增功能)")
    print("3. 退出")
    
    while True:
        try:
            choice = input("\n请输入选择 (1-3): ").strip()
            
            if choice == "1":
                print("\n🚀 启动价格检测测试...")
                print("测试将在5秒后开始...")
                
                for i in range(5, 0, -1):
                    print(f"⏰ {i}秒...")
                    time.sleep(1)
                
                tester = PriceAccuracyTester()
                # 运行60秒测试
                tester.run_comprehensive_test(test_duration=60)
                print("\n✅ 价格检测测试完成！")
                break
                
            elif choice == "2":
                print("\n🔵 启动K线颜色检测调试...")
                test_candlestick_detection()
                print("\n✅ K线检测调试完成！")
                break
                
            elif choice == "3":
                print("👋 再见!")
                break
                
            else:
                print("❌ 无效选择，请输入 1、2 或 3")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，退出程序")
            break
        except Exception as e:
            print(f"❌ 输入错误: {e}")
            print("请重新选择")


if __name__ == "__main__":
    main()