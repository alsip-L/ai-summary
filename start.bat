@echo off
chcp 936 >nul
echo ================================
echo AI Summary Launcher
echo ================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not detected. Please install Python 3.11 or higher.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python installed
python --version
echo.

REM Check virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Found virtual environment, activating...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found, using system Python
)

REM Check dependencies
echo.
echo Checking dependencies...
pip show flask >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Dependencies not installed, installing...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Dependency installation failed
        pause
        exit /b 1
    )
    echo Dependencies installed
) else (
    echo Dependencies installed
)

REM Create necessary directories
echo.
echo Creating directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "output" mkdir output
echo Directories created

REM Check config file
echo.
echo Checking config file...
if not exist "config.json" (
    echo Config file not found, creating default config...
    echo {"providers":[],"current_provider":{},"custom_prompts":{},"current_prompt":"","file_paths":{"input":"","output":""},"trash":{"providers":[],"custom_prompts":{}}} > config.json
    echo Default config created
) else (
    echo Config file exists
)

REM Start application
echo.
echo ================================
echo Starting AI Summary application...
echo ================================
echo.
echo Access: http://localhost:5000
echo Press Ctrl+C to stop
echo.

python run.py

REM Pause on exit
echo.
echo Application stopped
echo.
pause
