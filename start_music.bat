@echo off
chcp 65001
title Music Service
color 0A

echo ===================================
echo    Music Service for WeChat Mini Program
echo ===================================
echo.

REM Check Python
python --version 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python 3.6+
    pause
    exit /b
)

REM Check required files
if not exist "simple_local_music.py" (
    echo [ERROR] simple_local_music.py not found
    pause
    exit /b
)

REM Create directories
if not exist "download\music" mkdir "download\music"
if not exist "download\cover" mkdir "download\cover"

echo [INFO] Starting music service...
echo [INFO] Service will run on port 5000
echo.
echo Press Ctrl+C to stop the service
echo.

REM Start music service
python simple_local_music.py 