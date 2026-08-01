@echo off
setlocal enabledelayedexpansion

rem --- Re-launch elevated if we're not already running as Administrator -------
rem Installing Python/Tesseract via winget often needs admin rights; without
rem them winget fails with a bare "Access is denied." instead of a helpful
rem prompt. "net session" only succeeds when elevated, so we use it as a
rem reliable admin check and relaunch ourselves via a UAC prompt if needed.
net session >nul 2>nul
if %errorlevel% neq 0 (
    echo Requesting administrator permission - please click "Yes" on the
    echo Windows prompt that appears...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -WorkingDirectory '%~dp0' -Verb RunAs"
    exit /b
)

echo ============================================
echo   ImageOCR Pro - First Time Setup
echo ============================================
echo.

where winget >nul 2>nul
set HAS_WINGET=%errorlevel%

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
    if %HAS_WINGET% equ 0 (
        echo Python was not found - installing it automatically via winget...
        echo ^(Windows may show a permission/confirmation prompt - please accept it.^)
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        echo.
        py -3 --version >nul 2>nul
        if !errorlevel! equ 0 set PYTHON_CMD=py -3
        if not defined PYTHON_CMD (
            for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
                if exist "%%D\python.exe" set PYTHON_CMD="%%D\python.exe"
            )
        )
    )
)

if not defined PYTHON_CMD (
    echo.
    echo Could not find a working Python installation.
    echo.
    echo This is very often caused by Windows' "App Execution Alias" for
    echo Python, which blocks the real python.exe. To fix it:
    echo   1. Open Settings ^> Apps ^> Advanced app settings ^> App execution aliases
    echo      ^(on older Windows: Settings ^> Apps ^> Apps ^& features ^> App execution aliases^)
    echo   2. Turn OFF the switches next to "python.exe" and "python3.exe"
    echo   3. Run this file again
    echo.
    echo If that setting isn't there, install Python manually from
    echo https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"
    echo during install^), then run this file again.
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
    if %HAS_WINGET% equ 0 (
        echo Tesseract OCR was not found - installing it automatically via winget...
        echo ^(Windows may show a permission/confirmation prompt - please accept it.^)
        winget install -e --id UB-Mannheim.TesseractOCR --accept-source-agreements --accept-package-agreements
        echo.
        echo Tesseract has been installed. The app will find it automatically
        echo even though this window's PATH hasn't refreshed - continuing setup...
    ) else (
        echo Tesseract OCR was not found on this computer, and it could not be
        echo installed automatically ^(winget is unavailable^).
        echo.
        echo Please install it manually, then run this file again:
        echo   1. Go to https://github.com/UB-Mannheim/tesseract/wiki
        echo   2. Download and run the Windows installer ^(default options are fine^)
        echo.
        pause
        exit /b 1
    )
)

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
