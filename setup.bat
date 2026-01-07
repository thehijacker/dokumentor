@echo off
REM Quick setup script for Windows

echo ========================================
echo Dokumentor - Windows Setup
echo ========================================
echo.

REM Check Python
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from python.org
    pause
    exit /b 1
)
echo.

REM Create virtual environment
echo Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo.

REM Create directories
echo Creating directories...
if not exist data mkdir data
if not exist documents mkdir documents
if not exist watch_folder mkdir watch_folder
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist data\models mkdir data\models
echo.

REM Copy env file
echo Setting up environment file...
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo Created .env file from template
        echo Please edit .env with your configuration
    ) else (
        echo Warning: .env.example not found
    )
) else (
    echo .env file already exists
)
echo.

REM Initialize database
echo Initializing database...
python -c "from backend.database import init_db; init_db()"
if errorlevel 1 (
    echo Warning: Database initialization failed
)
echo.

REM Done
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit .env file with your settings (optional)
echo   2. Edit config.yaml to customize (optional)
echo   3. Run: python app.py
echo   4. Open: http://localhost:5000
echo.
echo To start the application now, run:
echo   python app.py
echo.
echo For Docker deployment:
echo   docker-compose up -d
echo.
pause
