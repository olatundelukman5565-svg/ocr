@echo off
cd /d "%~dp0"

echo Running setup and saving everything to setup_log.txt ...
echo This window may look blank or seem paused at times - that is normal.
echo If it seems stuck, just click into this window and press any key.
echo.

call setup_windows.bat > setup_log.txt 2>&1

echo.
echo ============================================
echo Done. Opening setup_log.txt now in Notepad.
echo Please copy EVERYTHING in that Notepad window
echo (Ctrl+A then Ctrl+C) and send it back.
echo ============================================
notepad setup_log.txt
pause
