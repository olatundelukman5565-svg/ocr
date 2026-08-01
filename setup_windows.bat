@echo off
echo ============================================
echo   ImageOCR Pro - First Time Setup
echo ============================================
echo.

where winget >nul 2>nul
set HAS_WINGET=%errorlevel%

where python >nul 2>nul
if %errorlevel% neq 0 (
    if %HAS_WINGET% equ 0 (
        echo Python was not found - installing it automatically via winget...
        echo ^(Windows may show a permission/confirmation prompt - please accept it.^)
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        echo.
        echo Python has been installed. Please CLOSE this window, reopen this
        echo folder, and double-click setup_windows.bat again so Windows picks
        echo up the change.
        pause
        exit /b 0
    ) else (
        echo Python was not found on this computer, and it could not be
        echo installed automatically ^(winget is unavailable^).
        echo.
        echo Please install it manually, then run this file again:
        echo   1. Go to https://www.python.org/downloads/
        echo   2. Download and run the Windows installer
        echo   3. IMPORTANT: tick the box "Add python.exe to PATH" during install
        echo.
        pause
        exit /b 1
    )
)

set TESSERACT_FOUND=0
where tesseract >nul 2>nul
if %errorlevel% equ 0 set TESSERACT_FOUND=1
if exist "%ProgramFiles%\Tesseract-OCR\tesseract.exe" set TESSERACT_FOUND=1
if exist "%ProgramFiles(x86)%\Tesseract-OCR\tesseract.exe" set TESSERACT_FOUND=1

if %TESSERACT_FOUND% equ 0 (
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
