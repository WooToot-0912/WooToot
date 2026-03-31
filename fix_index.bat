@echo off
chcp 65001
title Fix Music Index
color 0A

echo Running Music Index Fix Tool...
echo This tool will repair the music index file to fix encoding issues.
echo.

python fix_music_index.py

echo.
echo Fix completed. Press any key to exit.
pause > nul 