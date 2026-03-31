@echo off
chcp 65001 >nul
title 用户管理工具

echo.
echo ========================================
echo    🔧 智能量化交易系统 - 用户管理
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 启动用户管理工具
echo 🚀 正在启动用户管理工具...
echo.
python user_manager.py

pause
