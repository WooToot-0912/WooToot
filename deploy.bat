@echo off
echo Building project...
call npm run build

if not exist "dist" (
    echo Build failed! dist directory not found.
    exit /b 1
)

echo Build successful!
echo.
echo Please upload the 'dist' folder to Cloudflare Pages:
echo https://dash.cloudflare.com
echo.
pause
