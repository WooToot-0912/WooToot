@echo off
echo ========================================
echo Development Environment Check
echo ========================================

echo.
echo Checking system requirements...

echo.
echo 1. Python Environment:
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please install Python 3.7+ from https://python.org
    set /a errors+=1
) else (
    echo [OK] Python is installed
)

echo.
echo 2. Python Dependencies:
if exist "requirements.txt" (
    echo Checking Python packages...
    pip list | findstr "flask" >nul
    if errorlevel 1 (
        echo [WARNING] Flask not found
        echo Run: pip install -r requirements.txt
        set /a warnings+=1
    ) else (
        echo [OK] Flask is installed
    )
    
    pip list | findstr "flask-cors" >nul
    if errorlevel 1 (
        echo [WARNING] Flask-CORS not found
        set /a warnings+=1
    ) else (
        echo [OK] Flask-CORS is installed
    )
) else (
    echo [ERROR] requirements.txt not found
    set /a errors+=1
)

echo.
echo 3. Project Structure:
set required_dirs=pages utils images download scripts
for %%d in (%required_dirs%) do (
    if exist "%%d" (
        echo [OK] %%d directory exists
    ) else (
        echo [ERROR] Missing %%d directory
        set /a errors+=1
    )
)

echo.
echo 4. Configuration Files:
set config_files=config.js app.js app.json project.config.json
for %%f in (%config_files%) do (
    if exist "%%f" (
        echo [OK] %%f exists
    ) else (
        echo [ERROR] Missing %%f
        set /a errors+=1
    )
)

echo.
echo 5. Utility Files:
set util_files=utils\api-client.js utils\error-handler.js utils\ui-helper.js utils\validators.js utils\security.js utils\cache-manager.js
for %%f in (%util_files%) do (
    if exist "%%f" (
        echo [OK] %%f exists
    ) else (
        echo [WARNING] Missing %%f
        set /a warnings+=1
    )
)

echo.
echo 6. Service Connectivity:
echo Testing Ollama service...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama service not responding on port 11434
    echo Please start Ollama service: ollama serve
    set /a warnings+=1
) else (
    echo [OK] Ollama service is running
)

echo Testing music service...
curl -s http://127.0.0.1:5000/api/status >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Music service not responding on port 5000
    echo Please start music service: start_music_server.bat
    set /a warnings+=1
) else (
    echo [OK] Music service is running
)

echo.
echo ========================================
echo Environment Check Summary
echo ========================================

if defined errors (
    echo [ERROR] Found %errors% critical issues
    echo Please fix these issues before proceeding
) else (
    echo [OK] No critical issues found
)

if defined warnings (
    echo [WARNING] Found %warnings% warnings
    echo These should be addressed for optimal performance
) else (
    echo [OK] No warnings
)

echo.
echo Development Tips:
echo - Use WeChat Developer Tools for testing
echo - Check logs in music_server.log for debugging
echo - Refer to PROJECT_IMPROVEMENT_PLAN.md for optimization
echo.
pause
