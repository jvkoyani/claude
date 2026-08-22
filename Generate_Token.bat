@echo off
REM VolHedge Pro - Token Generator

title VolHedge Pro - Fyers Token Generator

echo.
echo ========================================
echo  VolHedge Pro - Token Generator
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

echo Launching Fyers API token generator...
echo.

python generate_token.py

pause
