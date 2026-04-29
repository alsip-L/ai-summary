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

REM Check Python dependencies
echo.
echo Checking Python dependencies...
pip show fastapi >nul 2>&1
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

REM Check Node.js installation
echo.
echo Checking Node.js...
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Node.js not detected. Frontend will not be built.
    echo Download: https://nodejs.org/
) else (
    echo Node.js installed
    node --version

    REM Install frontend dependencies
    echo.
    echo Checking frontend dependencies...
    if not exist "frontend-vue\node_modules" (
        echo Installing frontend dependencies...
        cd frontend-vue
        npm install
        if %ERRORLEVEL% NEQ 0 (
            echo Frontend dependency installation failed
            cd ..
            pause
            exit /b 1
        )
        cd ..
    )

    REM Build frontend
    echo.
    echo Building frontend...
    cd frontend-vue
    npm run build
    if %ERRORLEVEL% NEQ 0 (
        echo Frontend build failed
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo Frontend built successfully
)

REM Create necessary directories
echo.
echo Creating directories...
if not exist "data" mkdir data
echo Directories created

REM Check config file
echo.
echo Checking config file...
if not exist "config.json" (
    if exist "config.example.json" (
        echo Config file not found, copying from config.example.json...
        copy config.example.json config.json >nul
        echo Config created from example - please edit config.json with your settings
    ) else (
        echo Config file not found, creating default config...
        echo {"system_settings":{"debug_level":"ERROR","secret_key":"default-dev-secret-key-please-change-in-prod","host":"0.0.0.0","port":5000,"debug":false}} > config.json
        echo Default config created
    )
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
