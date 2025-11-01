<#
.SYNOPSIS
    Build and Installation Script for Oriphim Runner PowerShell Edition
.DESCRIPTION
    Creates a deployable package and installs Oriphim Runner on Windows
.PARAMETER Action
    Action to perform: Build, Install, or Uninstall
.PARAMETER OutputDir
    Directory for build output
.EXAMPLE
    .\Build-OriphimRunner.ps1 -Action Build
    .\Build-OriphimRunner.ps1 -Action Install
#>

param(
    [ValidateSet("Build", "Install", "Uninstall", "Test")]
    [string]$Action = "Build",
    [string]$OutputDir = ".\dist"
)

function Write-Status {
    param([string]$Message, [string]$Color = "Green")
    Write-Host "🔧 $Message" -ForegroundColor $Color
}

function Build-Runner {
    Write-Status "Building Oriphim Runner PowerShell Edition..."
    
    # Create output directory
    if (Test-Path $OutputDir) {
        Remove-Item $OutputDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    
    # Copy main script
    Copy-Item "OriphimRunner.ps1" "$OutputDir\" -Force
    Write-Status "✅ Copied main script"
    
    # Create assets directory
    $assetsDir = "$OutputDir\assets"
    New-Item -ItemType Directory -Path $assetsDir -Force | Out-Null
    
    # Create a simple icon (you can replace this with a real icon file)
    $iconScript = @"
# Create a simple icon file
# In production, replace this with a real .ico file
Add-Type -AssemblyName System.Drawing
`$bitmap = New-Object System.Drawing.Bitmap(32, 32)
`$graphics = [System.Drawing.Graphics]::FromImage(`$bitmap)
`$graphics.FillEllipse([System.Drawing.Brushes]::DarkBlue, 4, 4, 24, 24)
`$graphics.FillEllipse([System.Drawing.Brushes]::LightBlue, 8, 8, 16, 16)
`$graphics.DrawString("O", (New-Object System.Drawing.Font("Arial", 12, [System.Drawing.FontStyle]::Bold)), [System.Drawing.Brushes]::White, 10, 8)
`$bitmap.Save("$assetsDir\oriphim.ico", [System.Drawing.Imaging.ImageFormat]::Icon)
`$graphics.Dispose()
`$bitmap.Dispose()
"@
    
    try {
        Invoke-Expression $iconScript
        Write-Status "✅ Created placeholder icon"
    } catch {
        Write-Status "⚠️  Could not create icon: $($_.Exception.Message)" "Yellow"
    }
    
    # Create launcher batch file
    $launcherScript = @"
@echo off
cd /d "%~dp0"
echo Starting Oriphim Runner...
powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "OriphimRunner.ps1"
if errorlevel 1 (
    echo.
    echo Error starting Oriphim Runner. Press any key to exit.
    pause >nul
)
"@
    
    $launcherScript | Out-File "$OutputDir\OriphimRunner.bat" -Encoding ASCII
    Write-Status "✅ Created launcher batch file"
    
    # Create debug launcher
    $debugLauncherScript = @"
@echo off
cd /d "%~dp0"
echo Starting Oriphim Runner in Debug Mode...
echo Close this window to stop the runner.
echo.
powershell.exe -ExecutionPolicy Bypass -File "OriphimRunner.ps1" -Debug
pause
"@
    
    $debugLauncherScript | Out-File "$OutputDir\OriphimRunner-Debug.bat" -Encoding ASCII
    Write-Status "✅ Created debug launcher"
    
    # Create uninstaller
    $uninstallScript = @"
<#
.SYNOPSIS
    Uninstaller for Oriphim Runner
#>

Write-Host "🗑️  Uninstalling Oriphim Runner..." -ForegroundColor Yellow

`$installPath = "`$env:LOCALAPPDATA\OriphimRunner"
`$configPath = "`$env:USERPROFILE\.oriphim"
`$desktopShortcut = "`$env:USERPROFILE\Desktop\Oriphim Runner.lnk"
`$startMenuShortcut = "`$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Oriphim Runner.lnk"

# Stop any running instances
try {
    Get-Process | Where-Object { `$_.ProcessName -eq "powershell" -and `$_.CommandLine -like "*OriphimRunner.ps1*" } | Stop-Process -Force
    Start-Sleep 2
} catch {
    # Ignore errors
}

# Remove installation directory
if (Test-Path `$installPath) {
    Remove-Item `$installPath -Recurse -Force
    Write-Host "✅ Removed installation files" -ForegroundColor Green
}

# Ask about config and logs
`$removeConfig = Read-Host "Remove configuration and logs? (y/N)"
if (`$removeConfig -eq "y" -or `$removeConfig -eq "Y") {
    if (Test-Path `$configPath) {
        Remove-Item `$configPath -Recurse -Force
        Write-Host "✅ Removed configuration and logs" -ForegroundColor Green
    }
}

# Remove shortcuts
if (Test-Path `$desktopShortcut) {
    Remove-Item `$desktopShortcut -Force
    Write-Host "✅ Removed desktop shortcut" -ForegroundColor Green
}

if (Test-Path `$startMenuShortcut) {
    Remove-Item `$startMenuShortcut -Force
    Write-Host "✅ Removed start menu shortcut" -ForegroundColor Green
}

Write-Host "🎉 Oriphim Runner uninstalled successfully!" -ForegroundColor Green
Write-Host "Press any key to exit..."
`$null = `$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
"@
    
    $uninstallScript | Out-File "$OutputDir\Uninstall.ps1" -Encoding UTF8
    Write-Status "✅ Created uninstaller"
    
    # Create installation script
    $installScript = @"
<#
.SYNOPSIS
    Installer for Oriphim Runner PowerShell Edition
#>

Write-Host "🚀 Installing Oriphim Runner..." -ForegroundColor Green
Write-Host "AI-Driven Options Trading Automation Desktop Client" -ForegroundColor Cyan
Write-Host ""

`$installPath = "`$env:LOCALAPPDATA\OriphimRunner"
`$currentPath = `$PSScriptRoot

# Create installation directory
Write-Host "📁 Creating installation directory..." -ForegroundColor Yellow
if (-not (Test-Path `$installPath)) {
    New-Item -ItemType Directory -Path `$installPath -Force | Out-Null
}

# Copy files
Write-Host "📋 Copying files..." -ForegroundColor Yellow
Copy-Item "`$currentPath\OriphimRunner.ps1" "`$installPath\" -Force
Copy-Item "`$currentPath\OriphimRunner.bat" "`$installPath\" -Force
Copy-Item "`$currentPath\OriphimRunner-Debug.bat" "`$installPath\" -Force
Copy-Item "`$currentPath\Uninstall.ps1" "`$installPath\" -Force

if (Test-Path "`$currentPath\assets") {
    Copy-Item "`$currentPath\assets" "`$installPath\" -Recurse -Force
}

Write-Host "✅ Files copied to: `$installPath" -ForegroundColor Green

# Create desktop shortcut
Write-Host "🔗 Creating desktop shortcut..." -ForegroundColor Yellow
try {
    `$shell = New-Object -ComObject WScript.Shell
    `$shortcut = `$shell.CreateShortcut("`$env:USERPROFILE\Desktop\Oriphim Runner.lnk")
    `$shortcut.TargetPath = "`$installPath\OriphimRunner.bat"
    `$shortcut.WorkingDirectory = `$installPath
    `$shortcut.Description = "Oriphim Runner - AI Trading Automation"
    if (Test-Path "`$installPath\assets\oriphim.ico") {
        `$shortcut.IconLocation = "`$installPath\assets\oriphim.ico"
    }
    `$shortcut.Save()
    Write-Host "✅ Desktop shortcut created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not create desktop shortcut: `$(`$_.Exception.Message)" -ForegroundColor Yellow
}

# Create start menu shortcut
Write-Host "📋 Creating start menu shortcut..." -ForegroundColor Yellow
try {
    `$startMenuPath = "`$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
    `$shortcut = `$shell.CreateShortcut("`$startMenuPath\Oriphim Runner.lnk")
    `$shortcut.TargetPath = "`$installPath\OriphimRunner.bat"
    `$shortcut.WorkingDirectory = `$installPath
    `$shortcut.Description = "Oriphim Runner - AI Trading Automation"
    if (Test-Path "`$installPath\assets\oriphim.ico") {
        `$shortcut.IconLocation = "`$installPath\assets\oriphim.ico"
    }
    `$shortcut.Save()
    Write-Host "✅ Start menu shortcut created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not create start menu shortcut: `$(`$_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Oriphim Runner installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Start Interactive Brokers TWS (Trader Workstation)" -ForegroundColor White
Write-Host "2. Enable API access in TWS: Global Configuration → API → Settings" -ForegroundColor White
Write-Host "3. Double-click 'Oriphim Runner' on your desktop to start" -ForegroundColor White
Write-Host "4. Get your API key from the Oriphim dashboard" -ForegroundColor White
Write-Host ""
Write-Host "💡 For debugging, use 'OriphimRunner-Debug.bat' to see console output" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit..."
`$null = `$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
"@
    
    $installScript | Out-File "$OutputDir\Install.ps1" -Encoding UTF8
    Write-Status "✅ Created installer"
    
    # Create README
    $readmeContent = @"
# Oriphim Runner - PowerShell Edition

## Quick Start

1. **Install**: Right-click `Install.ps1` → "Run with PowerShell"
2. **Start**: Double-click the "Oriphim Runner" desktop shortcut
3. **Setup**: Enter your API key when prompted

## Files

- `OriphimRunner.ps1` - Main application
- `OriphimRunner.bat` - Normal launcher
- `OriphimRunner-Debug.bat` - Debug launcher (shows console)
- `Install.ps1` - Installer script
- `Uninstall.ps1` - Uninstaller script

## Requirements

- Windows 10/11
- PowerShell 5.1+ (built into Windows)
- Interactive Brokers TWS or Gateway
- Python 3.9+ (for trading bots)

## Troubleshooting

### "Execution policy" error:
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debug mode:
Run `OriphimRunner-Debug.bat` to see detailed console output.

### Manual start:
```powershell
powershell -ExecutionPolicy Bypass -File "OriphimRunner.ps1" -Debug
```

## Features

- ✅ System tray integration
- ✅ Native Windows GUI
- ✅ IBKR connection testing
- ✅ Real-time log viewing
- ✅ Cloud job simulation
- ✅ Bot execution via Python backend
- ✅ Configuration management
- ✅ Automatic startup options

## Support

- Config location: `%USERPROFILE%\.oriphim\`
- Logs location: `%USERPROFILE%\.oriphim\logs\`
- Installation: `%LOCALAPPDATA%\OriphimRunner\`
"@
    
    $readmeContent | Out-File "$OutputDir\README.md" -Encoding UTF8
    Write-Status "✅ Created README"
    
    Write-Status "🎉 Build complete! Files in: $OutputDir" "Green"
    Write-Status "To install: Right-click Install.ps1 → Run with PowerShell" "Cyan"
}

function Install-Runner {
    Write-Status "Installing Oriphim Runner..."
    
    if (-not (Test-Path "$OutputDir\Install.ps1")) {
        Write-Status "❌ Installation files not found. Run with -Action Build first." "Red"
        return
    }
    
    # Run the installer
    & "$OutputDir\Install.ps1"
}

function Uninstall-Runner {
    Write-Status "Uninstalling Oriphim Runner..."
    
    $installPath = "$env:LOCALAPPDATA\OriphimRunner"
    if (Test-Path "$installPath\Uninstall.ps1") {
        & "$installPath\Uninstall.ps1"
    } else {
        Write-Status "❌ Uninstaller not found. May not be installed." "Red"
    }
}

function Test-Runner {
    Write-Status "Testing Oriphim Runner..."
    
    if (-not (Test-Path "OriphimRunner.ps1")) {
        Write-Status "❌ OriphimRunner.ps1 not found in current directory." "Red"
        return
    }
    
    Write-Status "Starting runner in test mode..." "Yellow"
    Write-Status "Press Ctrl+C to stop the test" "Yellow"
    
    try {
        & ".\OriphimRunner.ps1" -Debug
    } catch {
        Write-Status "❌ Test failed: $($_.Exception.Message)" "Red"
    }
}

# Main execution
switch ($Action) {
    "Build" { Build-Runner }
    "Install" { Install-Runner }
    "Uninstall" { Uninstall-Runner }
    "Test" { Test-Runner }
}