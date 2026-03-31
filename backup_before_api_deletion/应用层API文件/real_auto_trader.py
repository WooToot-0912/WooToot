#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
景陶易购真实自动交易系统
基于真实API接口的自动交易程序
"""

import time
import json
import threading
from datetime import datetime
from real_api_client import RealAPIClient

class RealAutoTrader:
    """真实自动交易系统"""
    
    def __init__(self, phone, password):
        self.phone = phone
        self.password = password
        self.client = RealAPIClient()
        self.is_running = False
        self.trade_thread = None
        
        # 交易配置
        self.config = {
            "check_interval": 5,  # 检查间隔（秒）
            "max_price": 1000,    # 最大购买价格
            "min_price": 10,      # 最小购买价格
            "quantity": 1,        # 购买数量
            "target_commodities": [],  # 目标商品ID列表
            "auto_buy": True,     # 是否自动购买
            "auto_sell": False,   # 是否自动卖出
        }
        
        self.trade_log = []
        
    def login(self):
        """登录系统"""
        print("🔐 正在登录交易系统...")
        success, result = self.client.login(self.phone, self.password)
        
        if success:
            print("✅ 登录成功！")
            print(f"👤 用户信息: {json.dumps(self.client.user_info, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"❌ 登录失败: {result}")
            return False
    
    def get_market_status(self):
        """获取市场状态"""
        try:
            success, data = self.client.get_market_data()
            if success:
                print("📊 市场数据获取成功")
                return data
            else:
                print("❌ 无法获取市场数据")
                return None
        except Exception as e:
            print(f"❌ 获取市场状态异常: {str(e)}")
            return None
    
    def analyze_market(self, market_data):
        """分析市场数据，寻找交易机会"""
        opportunities = []
        
        if not market_data:
            return opportunities
        
        try:
            # 这里需要根据实际的市场数据结构来分析
            # 示例分析逻辑
            commodities = market_data.get('data', {}).get('list', [])
            
            for commodity in commodities:
                commodity_id = commodity.get('id')
                name = commodity.get('name', '未知商品')
                price = commodity.get('price', 0)
                stock = commodity.get('stock', 0)
                
                # 分析是否符合购买条件
                if (self.config['min_price'] <= price <= self.config['max_price'] and 
                    stock > 0 and 
                    (not self.config['target_commodities'] or commodity_id in self.config['target_commodities'])):
                    
                    opportunities.append({
                        'id': commodity_id,
                        'name': name,
                        'price': price,
                        'stock': stock,
                        'action': 'buy'
                    })
                    
                    print(f"💡 发现购买机会: {name} - 价格: ¥{price} - 库存: {stock}")
            
        except Exception as e:
            print(f"❌ 市场分析异常: {str(e)}")
        
        return opportunities
    
    def execute_trade(self, opportunity):
        """执行交易"""
        try:
            commodity_id = opportunity['id']
            name = opportunity['name']
            price = opportunity['price']
            action = opportunity['action']
            
            print(f"🚀 执行交易: {action} {name} - 价格: ¥{price}")
            
            if action == 'buy' and self.config['auto_buy']:
                success, result = self.client.place_order(
                    commodity_id=commodity_id,
                    quantity=self.config['quantity'],
                    price=price,
                    order_type='buy'
                )
                
                if success:
                    print(f"✅ 购买成功: {name}")
                    self.log_trade('buy', name, price, self.config['quantity'], True, result)
                else:
                    print(f"❌ 购买失败: {name} - {result}")
                    self.log_trade('buy', name, price, self.config['quantity'], False, result)
                
                return success
            
        except Exception as e:
            print(f"❌ 交易执行异常: {str(e)}")
            return False
    
    def log_trade(self, action, name, price, quantity, success, result):
        """记录交易日志"""
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': action,
            'commodity': name,
            'price': price,
            'quantity': quantity,
            'success': success,
            'result': result
        }
        
        self.trade_log.append(log_entry)
        
        # 保存到文件
        try:
            with open('trade_log.json', 'w', encoding='utf-8') as f:
                json.dump(self.trade_log, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def trading_loop(self):
        """交易主循环"""
        print("🔄 开始自动交易循环...")
        
        while self.is_running:
            try:
                print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - 检查市场...")
                
                # 获取市场数据
                market_data = self.get_market_status()
                
                if market_data:
                    # 分析市场机会
                    opportunities = self.analyze_market(market_data)
                    
                    if opportunities:
                        print(f"🎯 发现 {len(opportunities)} 个交易机会")
                        
                        # 执行交易
                        for opportunity in opportunities:
                            if not self.is_running:
                                break
                            self.execute_trade(opportunity)
                            time.sleep(1)  # 避免请求过快
                    else:
                        print("📊 暂无交易机会")
                else:
                    print("❌ 无法获取市场数据")
                
                # 等待下次检查
                for i in range(self.config['check_interval']):
                    if not self.is_running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                print(f"❌ 交易循环异常: {str(e)}")
                time.sleep(5)
        
        print("🛑 交易循环已停止")
    
    def start_trading(self):
        """开始自动交易"""
        if self.is_running:
            print("⚠️ 交易系统已在运行中")
            return
        
        # 先登录
        if not self.login():
            print("❌ 登录失败，无法开始交易")
            return
        
        print("🚀 启动自动交易系统...")
        self.is_running = True
        self.trade_thread = threading.Thread(target=self.trading_loop)
        self.trade_thread.daemon = True
        self.trade_thread.start()
        
        print("✅ 自动交易系统已启动")
    
    def stop_trading(self):
        """停止自动交易"""
        print("🛑 正在停止交易系统...")
        self.is_running = False
        
        if self.trade_thread and self.trade_thread.is_alive():
            self.trade_thread.join(timeout=10)
        
        print("✅ 交易系统已停止")
    
    def show_status(self):
        """显示系统状态"""
        print("\n" + "="*50)
        print("📊 交易系统状态")
        print("="*50)
        print(f"🔐 登录状态: {'已登录' if self.client.token else '未登录'}")
        print(f"🔄 运行状态: {'运行中' if self.is_running else '已停止'}")
        print(f"📱 交易账号: {self.phone}")
        print(f"⏰ 检查间隔: {self.config['check_interval']}秒")
        print(f"💰 价格范围: ¥{self.config['min_price']} - ¥{self.config['max_price']}")
        print(f"📦 购买数量: {self.config['quantity']}")
        print(f"🤖 自动购买: {'开启' if self.config['auto_buy'] else '关闭'}")
        print(f"📈 交易记录: {len(self.trade_log)}条")
        print("="*50)

def main():
    """主程序"""
    print("🎯 景陶易购真实自动交易系统")
    print("基于真实API接口，请谨慎使用")
    print("="*50)
    
    # 配置账号信息
    phone = input("📱 请输入手机号: ").strip()
    password = input("🔐 请输入密码: ").strip()
    
    if not phone or not password:
        print("❌ 账号信息不能为空")
        return
    
    # 创建交易系统
    trader = RealAutoTrader(phone, password)
    
    print("\n🎮 控制命令:")
    print("start - 开始交易")
    print("stop  - 停止交易") 
    print("status - 查看状态")
    print("quit  - 退出程序")
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == 'start':
                trader.start_trading()
            elif command == 'stop':
                trader.stop_trading()
            elif command == 'status':
                trader.show_status()
            elif command == 'quit':
                trader.stop_trading()
                print("👋 程序已退出")
                break
            else:
                print("❓ 未知命令，请输入: start/stop/status/quit")
                
        except KeyboardInterrupt:
            print("\n🛑 检测到Ctrl+C，正在退出...")
            trader.stop_trading()
            break
        except Exception as e:
            print(f"❌ 程序异常: {str(e)}")

if __name__ == "__main__":
    main()
