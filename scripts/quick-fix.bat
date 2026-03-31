@echo off
echo ========================================
echo Quick Fix Script for WeChat AI Assistant
echo ========================================

echo.
echo Step 1: Cleaning up duplicate files...
call scripts\cleanup.bat

echo.
echo Step 2: Checking project structure...
if not exist "utils\api-client.js" (
    echo [ERROR] Missing utils/api-client.js
    echo Please ensure all utility files are present
    pause
    exit /b 1
)

if not exist "utils\error-handler.js" (
    echo [ERROR] Missing utils/error-handler.js
    echo Please ensure all utility files are present
    pause
    exit /b 1
)

echo [OK] All utility files present

echo.
echo Step 3: Validating configuration...
if not exist "config.js" (
    echo [ERROR] Missing config.js
    pause
    exit /b 1
)

echo [OK] Configuration file exists

echo.
echo Step 4: Checking Python dependencies...
python --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Python not found in PATH
    echo Please ensure Python is installed and accessible
) else (
    echo [OK] Python is available
)

echo.
echo Step 5: Checking required directories...
if not exist "download" mkdir download
if not exist "download\music" mkdir download\music
if not exist "download\cover" mkdir download\cover
if not exist "download\cache" mkdir download\cache

echo [OK] All required directories exist

echo.
echo Step 6: Validating package.json...
if not exist "package.json" (
    echo [ERROR] Missing package.json
    pause
    exit /b 1
)

echo [OK] Package.json exists

echo.
echo ========================================
echo Quick Fix Completed!
echo ========================================
echo.
echo Next steps:
echo 1. Run 'start_music_server.bat' to start the music service
echo 2. Ensure Ollama is running on port 11434
echo 3. Test the application in WeChat Developer Tools
echo.
echo For detailed improvement plan, see PROJECT_IMPROVEMENT_PLAN.md
echo.
pause
