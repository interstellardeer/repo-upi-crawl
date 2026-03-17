@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   UPI Repository Scraper API - Startup Script
echo ===================================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8 or newer and try again.
    pause
    exit /b 1
)

:: 2. Virtual Environment Setup
set VENV_DIR=venv
if not exist "%VENV_DIR%\" (
    echo [INFO] Creating virtual environment in "%VENV_DIR%"...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo [INFO] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

:: Ensure pip is up to date
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

:: 3. Install dependencies
if exist "requirements.txt" (
    echo [INFO] Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies. Please check the errors above.
        pause
        exit /b 1
    )
) else (
    echo [WARNING] requirements.txt not found. Skipping dependency installation.
)

:: 4. Environment variables setup
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating .env file from .env.example...
        copy .env.example .env >nul
        echo [INFO] Initial setup complete. Please check the new .env file to configure any custom database paths.
        echo Press any key to start the server now...
        pause >nul
    ) else (
        echo [WARNING] No .env or .env.example file found.
    )
)

:: 5. Start the server
echo.
echo [INFO] Starting the API server...
echo ===================================================
python -m app.cli serve

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] The API server crashed or failed to start.
    pause
    exit /b 1
)

pause
