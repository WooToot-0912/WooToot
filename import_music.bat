@echo off
chcp 65001
title Import Local Music
color 0A

echo Running Local Music Import Tool...
echo This tool will help you add your local music files to the music index.
echo.

python add_local_music.py

echo.
echo Import completed. Press any key to exit.
pause > nul 