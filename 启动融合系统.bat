@echo off
chcp 65001 >nul
title 智能量化交易系统 - 融合启动器

echo.
echo 🎯 智能量化交易系统 v1.0
echo 🔗 多模态融合 - API + 图像识别
echo ================================================

echo.
echo 🚀 启动选项:
echo    1. 启动完整GUI系统
echo    2. 运行功能演示
echo    3. 运行系统测试
echo    4. 查看项目文档
echo.

set /p choice="请选择启动方式 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🎮 启动完整GUI系统...
    python main_fusion.py
) else if "%choice%"=="2" (
    echo.
    echo 🎭 运行功能演示...
    python fusion_demo.py
) else if "%choice%"=="3" (
    echo.
    echo 🧪 运行系统测试...
    python test_fusion_system.py
) else if "%choice%"=="4" (
    echo.
    echo 📚 打开项目文档...
    start 第三步融合完成报告.md
    start 智能量化交易系统融合项目总结报告.md
) else (
    echo.
    echo ❌ 无效选择，启动默认GUI系统...
    python main_fusion.py
)

echo.
echo 🎉 感谢使用智能量化交易系统！
pause
