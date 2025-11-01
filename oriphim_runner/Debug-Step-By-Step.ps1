param([switch]$Debug = $false)
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName PresentationFramework

Write-Host "Step 1: Config initialization..." -ForegroundColor Yellow
$configDir = "$env:USERPROFILE\.oriphim"
if (-not (Test-Path $configDir)) { New-Item -ItemType Directory -Path $configDir -Force | Out-Null }

Write-Host "Step 2: System tray..." -ForegroundColor Yellow
$notifyIcon = New-Object System.Windows.Forms.NotifyIcon
$notifyIcon.Icon = [System.Drawing.SystemIcons]::Information
$notifyIcon.Text = "Oriphim Runner - Debug"
$notifyIcon.Visible = $true

Write-Host "Step 3: Testing WPF window..." -ForegroundColor Yellow
$xaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" Title="Oriphim Test" Height="300" Width="400">
    <Grid><TextBlock Text="Hello Oriphim!" HorizontalAlignment="Center" VerticalAlignment="Center" FontSize="20"/></Grid>
</Window>
"@

try {
    $window = [Windows.Markup.XamlReader]::Parse($xaml)
    $window.Show()
    Write-Host "? WPF window created successfully!" -ForegroundColor Green
    Write-Host "? System tray icon visible!" -ForegroundColor Green
    Write-Host "Press Enter to exit..." -ForegroundColor Cyan
    Read-Host
    $window.Close()
} catch {
    Write-Host "? WPF Error: $($_.Exception.Message)" -ForegroundColor Red
}

$notifyIcon.Dispose()
