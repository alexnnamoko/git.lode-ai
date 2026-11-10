@echo off
setlocal
cd /d "%~dp0"
echo ==============================================
echo LODE.ai / Atlas.ai - Windows setup
echo ==============================================
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo Python 3.11 was not found. Install Python 3.11 from python.org and enable the Python Launcher.
  pause
  exit /b 1
)
if not exist .venv py -3.11 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Check your internet connection and Python version.
  pause
  exit /b 1
)
echo.
echo Setup complete. Copy .env.example to .env and add your Groq API key.
echo No local AI model download is required. Groq free-tier limits may apply.
echo Install Tesseract OCR separately; see README.md.
echo Then run run_lode.bat.
pause
