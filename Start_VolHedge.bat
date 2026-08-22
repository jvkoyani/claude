@echo off
REM VolHedge Pro - Daily Launcher

title VolHedge Pro

echo.
echo ========================================
echo    VolHedge Pro - Launching Terminal
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please run SETUP_AND_RUN.bat first
    pause
    exit /b 1
)

echo Starting VolHedge Pro on http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python desktop_app.py

pause
