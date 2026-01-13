@echo off
REM Quick setup script for Windows development environment

echo.
echo 🚀 TaskFlow Development Setup
echo ==============================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)

echo ✓ Python found

REM Create virtual environment
echo.
echo 📦 Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

REM Create .env file
echo.
echo 📝 Setting up environment...
if not exist .env (
    copy .env.example .env
    echo ⚠️  Created .env - please update with your credentials
)

REM Start Docker services
echo.
echo 🐳 Starting Docker services...
docker-compose -f docker-compose.local.yml up -d

REM Wait for services
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak

REM Initialize database
echo.
echo 🗄️  Initializing database...
python scripts\init_db.py

echo.
echo ✓ Setup complete!
echo.
echo Next steps:
echo 1. Run API server:    python run.py
echo 2. Run worker:        python -m src.core.worker
echo 3. Run tests:         pytest tests/
echo.
