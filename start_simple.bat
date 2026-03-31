@echo off
chcp 65001
title Simple Local Music Server
color 0A

REM Kill existing Python processes
taskkill /f /im python.exe 2>nul

REM Show IP addresses
ipconfig | findstr "IPv4"
echo.
echo Please set apiBaseUrl in config.js to one of these IP addresses
echo Example: apiBaseUrl: 'http://192.168.1.x:5000'
echo.

REM Create directories if needed
if not exist "download\music" mkdir "download\music"
if not exist "download\cover" mkdir "download\cover"

REM Start the server
echo Starting Simple Local Music Server...
echo Press Ctrl+C to stop the server.
echo.

python simple_local_music.py

pause 