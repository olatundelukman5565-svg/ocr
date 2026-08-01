@echo off
echo ============================================
echo   ImageOCR Pro - First Time Setup
echo ============================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python was not found on this computer.
    echo.
    echo Please install it first, then run this file again:
    echo   1. Go to https://www.python.org/downloads/
    echo   2. Download and run the Windows installer
    echo   3. IMPORTANT: tick the box "Add python.exe to PATH" during install
    echo.
    pause
    exit /b 1
)

where tesseract >nul 2>nul
if %errorlevel% neq 0 (
    echo Tesseract OCR was not found on this computer.
    echo.
    echo Please install it first, then run this file again:
    echo   1. Go to https://github.com/UB-Mannheim/tesseract/wiki
    echo   2. Download and run the Windows installer ^(default options are fine^)
    echo.
    pause
    exit /b 1
)

echo Creating a private Python environment for the app...
python -m venv .venv
call .venv\Scripts\activate.bat

echo.
echo Installing required packages - this can take a few minutes, please wait...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt

echo.
echo ============================================
echo   Setup complete!
echo   Double-click run_windows.bat to start ImageOCR Pro.
echo ============================================
pause
