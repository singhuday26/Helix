@echo off
SETLOCAL EnableDelayedExpansion

TITLE Helix Setup Script

echo ===================================================
echo       Helix Inference Engine Setup 🧬
echo ===================================================
echo.

REM Check for Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

echo [1/4] Checking virtual environment...
IF NOT EXIST "venv" (
    echo       Creating virtual environment 'venv'...
    python -m venv venv
) ELSE (
    echo       Virtual environment already exists.
)

echo [2/4] Activating environment...
call venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
echo       - Upgrading pip...
python -m pip install --upgrade pip

echo       - Installing PyTorch (CPU base)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo       - Installing Torch-DirectML...
pip install torch-directml

echo       - Installing remaining requirements...
pip install -r requirements.txt

echo.
echo [4/4] Setup Complete!
echo ===================================================
echo.
echo To start the server, run:
echo    python run.py
echo.
pause
