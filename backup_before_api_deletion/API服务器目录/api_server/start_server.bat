@echo off
chcp 65001 >nul
echo ========================================
echo 景陶易购共享API服务器启动脚本
echo ========================================
echo.

echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境，请先安装Python 3.7+
    pause
    exit /b 1
)

echo 检查依赖包...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo 安装Flask...
    pip install flask flask-cors requests
)

echo.
echo 启动API服务器...
echo 服务器地址: http://localhost:8081
echo 按 Ctrl+C 停止服务器
echo.

python simple_server.py

pause 