#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "==================================================="
echo "  UPI Repository Scraper API - Startup Script"
echo "==================================================="
echo ""

# 1. Check for Python installation
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python is not installed or not in PATH."
    echo "Please install Python 3.8 or newer and try again."
    exit 1
fi

echo "[INFO] Using Python: $($PYTHON_CMD --version)"

# 2. Virtual Environment Setup
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtual environment in '$VENV_DIR'..."
    $PYTHON_CMD -m venv "$VENV_DIR" || {
        echo "[ERROR] Failed to create virtual environment."
        exit 1
    }
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Ensure pip is up to date
echo "[INFO] Upgrading pip..."
python -m pip install --upgrade pip > /dev/null

# 3. Install dependencies
if [ -f "requirements.txt" ]; then
    echo "[INFO] Installing dependencies from requirements.txt..."
    pip install -r requirements.txt || {
        echo "[ERROR] Failed to install dependencies."
        exit 1
    }
else
    echo "[WARNING] requirements.txt not found. Skipping dependency installation."
fi

# 4. Environment variables setup
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "[INFO] Creating .env file from .env.example..."
        cp .env.example .env
        echo "[INFO] Initial setup complete. Please check the new .env file to configure any custom settings."
        read -p "Press Enter to start the server now..."
    else
        echo "[WARNING] No .env or .env.example file found."
    fi
fi

# 5. Start the server
echo ""
echo "[INFO] Starting the API server..."
echo "==================================================="
python -m app.cli serve || {
    echo ""
    echo "[ERROR] The API server crashed or failed to start."
    exit 1
}
