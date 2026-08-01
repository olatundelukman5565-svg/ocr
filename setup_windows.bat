@echo off
setlocal enabledelayedexpansion

rem Always operate from the folder this script lives in, regardless of how
rem it was launched (double-click, right-click "Run as administrator", etc).
cd /d "%~dp0"

echo ============================================
echo   ImageOCR Pro - First Time Setup
echo ============================================
echo.

rem --- Find a real Python, avoiding Windows' fake "App Execution Alias" ------
rem Windows ships a placeholder python.exe that "where python" happily finds
rem even when no real Python is installed; running it just prints a Microsoft
rem Store prompt and fails. The "py" launcher isn't affected by that alias,
rem so we prefer it, then fall back to checking python's actual output text.
set PYTHON_CMD=

py -3 --version >nul 2>nul
if !errorlevel! equ 0 set PYTHON_CMD=py -3

if not defined PYTHON_CMD (
    for /f "delims=" %%i in ('python --version 2^>^&1') do set PY_CHECK=%%i
    echo !PY_CHECK! | findstr /C:"was not found" >nul
    if !errorlevel! neq 0 (
        python --version >nul 2>nul
        if !errorlevel! equ 0 set PYTHON_CMD=python
    )
)

if not defined PYTHON_CMD (
    for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
        if exist "%%D\python.exe" set PYTHON_CMD="%%D\python.exe"
    )
)

if not defined PYTHON_CMD (
    echo Python was not found on this computer.
    echo.
    echo Please install it, then run this file again:
    echo   1. Go to https://www.python.org/downloads/
    echo   2. Download and run the Windows installer
    echo   3. IMPORTANT: tick the box "Add python.exe to PATH" during install
    echo.
    echo If you already installed Python and still see this message, it is
    echo very often caused by Windows' "App Execution Alias" for Python:
    echo   1. Open Settings ^> Apps ^> Advanced app settings ^> App execution aliases
    echo   2. Turn OFF the switches next to "python.exe" and "python3.exe"
    echo   3. Run this file again
    echo.
    pause
    exit /b 1
)

echo Using Python: !PYTHON_CMD!

rem --- Tesseract OCR ----------------------------------------------------------
set TESSERACT_FOUND=0
where tesseract >nul 2>nul
if !errorlevel! equ 0 set TESSERACT_FOUND=1
if exist "%ProgramFiles%\Tesseract-OCR\tesseract.exe" set TESSERACT_FOUND=1
if exist "%ProgramFiles(x86)%\Tesseract-OCR\tesseract.exe" set TESSERACT_FOUND=1

if !TESSERACT_FOUND! equ 0 (
    echo.
    echo Tesseract OCR was not found on this computer.
    echo.
    echo Please install it, then run this file again:
    echo   1. Go to https://github.com/UB-Mannheim/tesseract/wiki
    echo   2. Download and run the Windows installer ^(default options are fine^)
    echo.
    pause
    exit /b 1
)

echo Tesseract OCR: found

rem --- Create the virtual environment ------------------------------------------
echo.
echo Creating a private Python environment for the app...
!PYTHON_CMD! -m venv .venv

if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo Something went wrong creating the Python environment - the
    echo .venv folder was not created. Please copy the messages above
    echo and send them back for help.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

if not exist "requirements.txt" (
    echo.
    echo ============================================
    echo   Cannot find requirements.txt
    echo ============================================
    echo This script is running from:
    echo   %cd%
    echo and expected to find requirements.txt right there, but it isn't.
    echo Here is what IS in this folder:
    echo.
    dir /b
    echo.
    echo Please make sure you extracted the ENTIRE zip file into one
    echo folder, then run setup_windows.bat from directly inside it.
    echo.
    pause
    exit /b 1
)

echo.
echo Installing required packages - this can take a few minutes, please wait...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo.
    echo Installing the required packages failed - please copy the messages
    echo above and send them back for help.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Setup complete!
echo   Double-click run_windows.bat to start ImageOCR Pro.
echo ============================================
pause
exit /b 0
