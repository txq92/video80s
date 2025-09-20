@echo off
echo =====================================
echo   Installing Video Processor
echo =====================================
echo.

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [2/3] Installing dependencies...
pip install -r requirements.txt

echo.
echo [3/3] Creating directories structure...
if not exist "input" mkdir input
if not exist "output" mkdir output  
if not exist "assets" mkdir assets
if not exist "data" mkdir data
if not exist "temp" mkdir temp
if not exist "logs" mkdir logs

echo.
echo =====================================
echo   Installation Complete!
echo =====================================
echo.
echo Next steps:
echo 1. Copy .env.example to .env and configure
echo 2. Add logo.png and banner.png to assets folder
echo 3. Setup YouTube API credentials (client_secrets.json)
echo 4. Put videos in input folder
echo 5. Run the program with: run.bat
echo.
pause