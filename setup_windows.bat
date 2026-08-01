@echo off
setlocal enabledelayedexpansion

rem Always operate from the folder this script lives in, regardless of how
rem it was launched (double-click, right-click "Run as administrator", etc).
cd /d "%~dp0"

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
        call :install_via_winget "Python.Python.3.12"
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
        call :install_via_winget "UB-Mannheim.TesseractOCR"
        echo.
        echo Continuing setup - the app will find Tesseract automatically
        echo even if this window's PATH hasn't refreshed yet.
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
exit /b 0

rem --- Helper: install a winget package, elevating only if it turns out to ---
rem require admin rights. This deliberately does NOT elevate the whole
rem script (that resets the working directory to System32 on Windows and
rem broke relative paths like requirements.txt) - only this one install
rem command runs elevated, in an isolated child process, when needed.
:install_via_winget
set WINGET_ID=%~1
echo ^(Windows may show a permission/confirmation prompt - please accept it.^)
winget install -e --id %WINGET_ID% --accept-source-agreements --accept-package-agreements
if !errorlevel! neq 0 (
    echo That install needs administrator permission - requesting it now,
    echo please click "Yes" on the Windows prompt that appears...
    powershell -NoProfile -Command "Start-Process winget -ArgumentList 'install -e --id %WINGET_ID% --accept-source-agreements --accept-package-agreements' -Verb RunAs -Wait"
)
exit /b
