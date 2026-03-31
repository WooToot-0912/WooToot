@echo off
chcp 65001 >nul
title 智能量化交易系统

echo.
echo ========================================
echo    🎯 智能量化交易系统 v1.0
echo    🔗 多模态融合 - API + 图像识别
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 启动系统
echo 🚀 正在启动智能量化交易系统...
echo.
python main_fusion.py

REM 如果程序异常退出，显示错误信息
if errorlevel 1 (
    echo.
    echo ❌ 系统启动失败，请检查错误信息
    echo 💡 如需帮助，请联系技术支持
    pause
)
