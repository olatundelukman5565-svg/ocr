@echo off
if not exist ".venv\Scripts\activate.bat" (
    echo It looks like setup hasn't been run yet.
    echo Please double-click setup_windows.bat first.
    echo.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python -m app.main

if %errorlevel% neq 0 (
    echo.
    echo The app closed with an error - see the message above.
    pause
)
