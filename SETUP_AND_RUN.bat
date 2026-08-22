@echo off
REM VolHedge Pro - Automated Setup & Run Script for Windows

title VolHedge Pro - Setup & Launch

echo.
echo ========================================
echo    VolHedge Pro - Setup & Installation
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add python.exe to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python is installed. Proceeding with dependency installation...
echo.

REM Install dependencies
echo Installing required packages from requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Error: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Dependencies installed successfully!
echo ========================================
echo.

REM Create necessary directories
if not exist "portfolio" mkdir portfolio
if not exist "static" mkdir static

REM Launch the application
echo Starting VolHedge Pro...
echo.
echo The application will open in your browser at http://127.0.0.1:8000
echo.

python desktop_app.py

pause
