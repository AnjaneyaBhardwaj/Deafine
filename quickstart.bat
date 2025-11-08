@echo off
REM Quick start script for Deafine (Windows)

echo 🎤 Deafine Quick Start
echo ====================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install package
echo 📥 Installing Deafine...
pip install -e . --quiet

REM Try to install webrtcvad (optional)
echo.
echo 💰 Attempting to install webrtcvad (optional - saves API costs)...
pip install webrtcvad --quiet 2>nul
if %errorlevel% equ 0 (
    echo ✅ webrtcvad installed - VAD enabled!
) else (
    echo ℹ️  webrtcvad not installed (requires C++ Build Tools)
    echo ℹ️  App works fine without it! VAD will be disabled.
)

REM Create .env if it doesn't exist
if not exist ".env" (
    echo.
    echo ⚙️  Creating .env file...
    copy env.template .env
    echo.
    echo ⚠️  IMPORTANT: Edit .env and add your ELEVEN_API_KEY!
    echo.
)

REM Test installation
echo.
echo 🧪 Testing installation...
python test_installation.py

echo.
echo ✅ Setup complete!
echo.
echo Next steps:
echo   1. Edit .env and add your ELEVEN_API_KEY
echo   2. Run: .venv\Scripts\activate
echo   3. Run: deafine run
echo.

pause
