@echo off
chcp 65001 >nul
echo ========================================
echo 景陶易购共享API服务器 - 管理员模式
echo ========================================
echo.

echo 检查管理员权限...
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ 已获得管理员权限
) else (
    echo ❌ 需要管理员权限运行此脚本
    echo 请右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo.
echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境，请先安装Python 3.7+
    pause
    exit /b 1
)

echo.
echo 启动API服务器...
echo 服务器地址: http://localhost:8081
echo 按 Ctrl+C 停止服务器
echo.

python simple_server.py

pause 