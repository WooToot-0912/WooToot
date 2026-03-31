# 景陶易购共享API服务器

这是一个为景陶易购交易系统提供多用户API接口的服务器，允许有景陶易购账号的用户通过登录后连接API实现自助下单。

## 功能特性

- 🔐 **多用户支持**: 支持多个景陶易购用户同时登录使用
- 🚀 **实时交易**: 基于现有的TradingAPI实现实时下单
- 🛡️ **会话管理**: 安全的用户会话管理，支持超时自动清理
- 📊 **交易接口**: 提供完整的交易、查询、持仓等接口
- 🔒 **安全认证**: 基于会话令牌的身份验证
- 🌐 **RESTful API**: 标准的REST API设计，易于集成

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   客户端应用     │    │   API服务器     │    │   景陶易购      │
│                │    │                │    │   交易系统      │
│ - 用户注册     │◄──►│ - 用户管理      │◄──►│ - 登录认证      │
│ - 用户登录     │    │ - 会话管理      │    │ - 交易执行      │
│ - 交易操作     │    │ - 交易服务      │    │ - 数据查询      │
│ - 数据查询     │    │ - 风险控制      │    │                │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 快速开始

### 1. 环境要求

- Python 3.7+
- 景陶易购交易账号
- 网络连接

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务器

#### Windows用户
```bash
start_server.bat
```

#### Linux/Mac用户
```bash
python simple_server.py
```

### 4. 服务器信息

- 地址: http://localhost:8080
- 状态检查: http://localhost:8080/api/health

## API接口文档

### 基础接口

#### 健康检查
```
GET /api/health
```
返回服务器状态信息

#### 用户注册
```
POST /api/register
Content-Type: application/json

{
    "username": "用户名",
    "phone": "手机号",
    "password": "密码",
    "email": "邮箱(可选)"
}
```

#### 用户登录
```
POST /api/login
Content-Type: application/json

{
    "phone": "手机号",
    "password": "密码"
}
```

返回:
```json
{
    "message": "登录成功",
    "session_token": "会话令牌",
    "user_info": {
        "username": "用户名",
        "phone": "手机号"
    },
    "trading_session": "交易会话ID"
}
```

### 交易接口

所有交易接口都需要在请求头中包含会话令牌:
```
X-Session-Token: 你的会话令牌
```

#### 下单
```
POST /api/trading/order
Content-Type: application/json

{
    "bs_flag": "B",           // B-买入, S-卖出
    "commodity_id": "商品ID",
    "price": "价格",
    "quantity": "数量"
}
```

#### 获取持仓
```
GET /api/trading/positions
```

#### 获取商品信息
```
GET /api/trading/commodities
```

## 客户端示例

项目包含一个完整的客户端示例 (`client_example.py`)，演示如何使用API进行各种操作。

### 运行客户端示例
```bash
python client_example.py
```

### 客户端功能
- 用户注册和登录
- 买入/卖出下单
- 查询持仓和商品信息
- 交互式命令行界面

## 安全特性

### 会话管理
- 每个用户登录后获得唯一的会话令牌
- 会话令牌有过期时间，超时自动失效
- 支持多设备同时登录

### 请求限制
- 可配置的请求频率限制
- 防止恶意请求和滥用

### 数据验证
- 所有输入参数进行验证
- 防止SQL注入和XSS攻击

## 配置说明

服务器配置文件位于 `config.py`，主要配置项包括:

```python
# 服务器配置
"server": {
    "host": "0.0.0.0",        # 监听地址
    "port": 8080,             # 监听端口
    "debug": False,            # 调试模式
    "workers": 4               # 工作进程数
}

# 安全配置
"security": {
    "enable_rate_limit": True,     # 启用频率限制
    "max_requests_per_minute": 100, # 每分钟最大请求数
    "session_timeout": 3600        # 会话超时时间(秒)
}

# 交易配置
"trading": {
    "base_url": "https://zxyw.ceramic-copyright.com/apigateway",
    "market_id": 28,
    "max_order_amount": 100000,    # 最大下单金额
    "enable_risk_control": True    # 启用风险控制
}
```

## 部署建议

### 生产环境
1. 使用生产级Web服务器 (如Gunicorn + Nginx)
2. 配置HTTPS证书
3. 设置防火墙规则
4. 配置日志轮转
5. 设置监控和告警

### 性能优化
1. 启用数据库连接池
2. 配置Redis缓存
3. 使用异步处理
4. 负载均衡

## 故障排除

### 常见问题

#### 1. 登录失败
- 检查景陶易购账号密码是否正确
- 确认网络连接正常
- 查看服务器日志

#### 2. 下单失败
- 确认会话令牌有效
- 检查商品ID、价格、数量参数
- 验证账户余额和持仓

#### 3. 服务器启动失败
- 检查端口是否被占用
- 确认Python环境和依赖包
- 查看错误日志

### 日志查看
服务器日志保存在 `logs/api_server.log`，包含详细的运行信息和错误记录。

## 开发说明

### 项目结构
```
api_server/
├── __init__.py              # 包初始化
├── config.py                # 配置管理
├── database.py              # 数据库管理
├── trading_service.py       # 交易服务
├── simple_server.py         # 简化版服务器
├── server.py                # 完整版服务器
├── client_example.py        # 客户端示例
├── requirements.txt         # 依赖包列表
├── start_server.bat         # Windows启动脚本
└── README.md                # 说明文档
```

### 扩展开发
1. 添加新的API接口
2. 实现数据库持久化
3. 添加风险控制功能
4. 集成监控和告警
5. 支持更多交易功能

## 技术支持

如有问题或建议，请查看:
1. 项目文档
2. 错误日志
3. 景陶易购官方文档
4. 提交Issue或联系开发者

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和景陶易购的使用条款。 