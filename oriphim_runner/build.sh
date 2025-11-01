#!/bin/bash

# Oriphim Runner - Build Script
# Sets up the development environment and builds the desktop application

echo "🚀 Oriphim Runner Build Script"
echo "================================"

# Check dependencies
echo "📋 Checking dependencies..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+ from https://nodejs.org"
    exit 1
fi

# Check Python (try python3 first, then python)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.9+ from https://python.org"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
if [[ $(echo "$PYTHON_VERSION >= 3.9" | bc -l 2>/dev/null || echo "0") == "0" ]]; then
    echo "⚠️  Python $PYTHON_VERSION found. Python 3.9+ recommended."
fi

# Check Rust (source cargo env if needed)
if ! command -v cargo &> /dev/null; then
    if [ -f "$HOME/.cargo/env" ]; then
        echo "🦀 Sourcing Rust environment..."
        source "$HOME/.cargo/env"
    fi
    
    if ! command -v cargo &> /dev/null; then
        echo "❌ Rust not found. Please install Rust from https://rustup.rs"
        exit 1
    fi
fi

echo "✅ All dependencies found"

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt
else
    $PYTHON_CMD -m pip install -r requirements.txt
fi

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p src/assets
mkdir -p build
mkdir -p tests

# Check for TWS installation (Windows)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    TWS_PATH="/c/Jts/tws/tws.exe"
    if [ -f "$TWS_PATH" ]; then
        echo "✅ Interactive Brokers TWS found at $TWS_PATH"
    else
        echo "⚠️  TWS not found at expected location. Please ensure it's installed."
    fi
fi

# Build the application
echo "🔨 Building Oriphim Runner..."

if [ "$1" == "dev" ]; then
    echo "🛠️  Starting development server..."
    npm run dev
elif [ "$1" == "build" ]; then
    echo "📦 Building production release..."
    npm run build
    
    if [ $? -eq 0 ]; then
        echo "✅ Build successful! Executable created in src-tauri/target/release/"
        
        # Show build artifacts
        echo "📋 Build artifacts:"
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
            ls -la src-tauri/target/release/*.exe 2>/dev/null || echo "   No .exe files found"
            ls -la src-tauri/target/release/bundle/msi/*.msi 2>/dev/null || echo "   No .msi files found"
        else
            ls -la src-tauri/target/release/
        fi
    else
        echo "❌ Build failed"
        exit 1
    fi
else
    echo "📖 Usage:"
    echo "  ./build.sh dev    - Start development server"
    echo "  ./build.sh build  - Build production release"
    echo ""
    echo "🔧 Setup complete! Next steps:"
    echo "1. Start Interactive Brokers TWS"
    echo "2. Enable API access in TWS settings"
    echo "3. Run './build.sh dev' to start development"
    echo "4. Get your API key from Oriphim dashboard"
fi

echo ""
echo "🎉 Setup complete!"