@echo off
echo 准备微信小程序上传版本...

REM 创建临时文件夹
if not exist "upload_temp" mkdir upload_temp

REM 复制必要文件
echo 复制基础文件...
xcopy /E /Y "pages" "upload_temp\pages\"
xcopy /E /Y "images" "upload_temp\images\"
xcopy /E /Y "styles" "upload_temp\styles\"
xcopy /E /Y "utils" "upload_temp\utils\"
copy app.js "upload_temp\"
copy app.json "upload_temp\"
copy app.wxss "upload_temp\"
copy config.js "upload_temp\"
copy project.config.json "upload_temp\"
copy sitemap.json "upload_temp\"

echo 清理完成，请打开upload_temp文件夹中的项目进行上传。
echo 提示：在微信开发者工具中选择"upload_temp"文件夹打开项目。

echo 完成! 