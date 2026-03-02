@echo off
REM Build script for Windows

echo ==========================================
echo Snapmaker U1 Flasher - Windows Build
echo ==========================================

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Build executable
echo Building Windows executable...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "SnapmakerU1-Flasher" ^
    --clean ^
    snapmaker_u1_flasher.py

if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo.
echo ==========================================
echo Build complete!
echo Executable: dist\SnapmakerU1-Flasher.exe
echo ==========================================
pause
