@echo off
REM Oriphim Runner - Windows Build Script
REM Run this from Windows Command Prompt or PowerShell

echo 🚀 Oriphim Runner Windows Build Script
echo ========================================

REM Check if we're in the right directory
if not exist "package.json" (
    echo ❌ Error: package.json not found. Please run this script from the oriphim_runner directory.
    pause
    exit /b 1
)

REM Check Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js from https://nodejs.org
    pause
    exit /b 1
) else (
    echo ✅ Node.js found
)

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
) else (
    echo ✅ Python found
)

REM Check Rust
where cargo >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Rust not found. Please install Rust from https://rustup.rs
    pause
    exit /b 1
) else (
    echo ✅ Rust found
)

echo.
echo 📦 Installing dependencies...

REM Install Node.js dependencies
echo Installing Node.js packages...
call npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install Node.js dependencies
    pause
    exit /b 1
)

REM Install Python dependencies
echo Installing Python packages...
if exist "requirements-minimal.txt" (
    echo Using minimal requirements for initial setup...
    pip install -r requirements-minimal.txt
) else (
    pip install -r requirements.txt
)
if %errorlevel% neq 0 (
    echo ❌ Failed to install Python dependencies
    echo 💡 Trying to install essential packages only...
    pip install ib_insync websockets python-dotenv pydantic pandas numpy SQLAlchemy cryptography aiohttp
    if %errorlevel% neq 0 (
        echo ❌ Critical: Could not install required packages
        pause
        exit /b 1
    )
)

echo.
echo ✅ Dependencies installed successfully!

REM Check command line arguments
if "%1"=="dev" (
    echo 🛠️  Starting development server...
    npm run dev
) else if "%1"=="build" (
    echo 📦 Building production release...
    npm run build
    if %errorlevel% equ 0 (
        echo ✅ Build successful! Check src-tauri\target\release\ for output
        dir /b src-tauri\target\release\*.exe 2>nul
        dir /b src-tauri\target\release\bundle\msi\*.msi 2>nul
    )
) else (
    echo.
    echo 📖 Usage:
    echo   build.bat dev    - Start development server
    echo   build.bat build  - Build production release
    echo.
    echo 🔧 Setup complete! Next steps:
    echo 1. Start Interactive Brokers TWS
    echo 2. Enable API access in TWS settings
    echo 3. Run 'build.bat dev' to start development
    echo 4. Get your API key from Oriphim dashboard
)

echo.
echo 🎉 Ready to go!
pause