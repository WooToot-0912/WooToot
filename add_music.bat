@echo off
chcp 65001
title Add Local Music
color 0A

echo Running Local Music Import Tool...
echo.

python add_local_music.py

echo.
echo Import completed. Press any key to exit.
pause > nul 