@echo off
echo Cleaning up project duplicate files and directories...

echo.
echo 1. Removing duplicate upload_temp_music directory...
if exist "upload_temp_music" (
    rmdir /s /q "upload_temp_music"
    echo    [OK] Removed upload_temp_music directory
) else (
    echo    [INFO] upload_temp_music directory does not exist
)

echo.
echo 2. Cleaning Python cache files...
if exist "__pycache__" (
    rmdir /s /q "__pycache__"
    echo    [OK] Removed __pycache__ directory
) else (
    echo    [INFO] __pycache__ directory does not exist
)

echo.
echo 3. Cleaning temporary files...
del /q *.tmp 2>nul
del /q *.log 2>nul
echo    [OK] Cleaned temporary files

echo.
echo 4. Cleaning music cache...
if exist "download\cache" (
    del /q "download\cache\*" 2>nul
    echo    [OK] Cleaned music cache
) else (
    echo    [INFO] Music cache directory does not exist
)

echo.
echo 5. Removing duplicate README files...
if exist "README_OPTIMIZATION.md" (
    del /q "README_OPTIMIZATION.md"
    echo    [OK] Removed README_OPTIMIZATION.md
)
if exist "README_OPTIMIZATION_CN.md" (
    del /q "README_OPTIMIZATION_CN.md"
    echo    [OK] Removed README_OPTIMIZATION_CN.md
)

echo.
echo Cleanup completed!
pause
