param([switch]$Debug = $false)
Add-Type -AssemblyName System.Windows.Forms

$Script:Config = @{
    ibkr_host = "127.0.0.1"
    ibkr_port = 7497
}

function Write-Log($Message) {
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor Green
}

function Test-IBKR {
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.ReceiveTimeout = 3000
        $tcpClient.Connect($Script:Config.ibkr_host, $Script:Config.ibkr_port)
        if ($tcpClient.Connected) {
            Write-Log "? IBKR Connected"
            $tcpClient.Close()
            return $true
        }
    } catch {
        Write-Log "? IBKR Offline"
        return $false
    }
}

Write-Log "?? Oriphim Runner (Simple Edition)"

# System tray
$notifyIcon = New-Object System.Windows.Forms.NotifyIcon
$notifyIcon.Icon = [System.Drawing.SystemIcons]::Information
$notifyIcon.Text = "Oriphim Runner"
$notifyIcon.Visible = $true

# Context menu
$contextMenu = New-Object System.Windows.Forms.ContextMenuStrip
$testItem = New-Object System.Windows.Forms.ToolStripMenuItem
$testItem.Text = "Test IBKR"
$testItem.Add_Click({ Test-IBKR })
$exitItem = New-Object System.Windows.Forms.ToolStripMenuItem
$exitItem.Text = "Exit"
$exitItem.Add_Click({ 
    $notifyIcon.Visible = $false
    $notifyIcon.Dispose()
    [System.Windows.Forms.Application]::Exit()
})

$contextMenu.Items.Add($testItem) | Out-Null
$contextMenu.Items.Add($exitItem) | Out-Null
$notifyIcon.ContextMenuStrip = $contextMenu

Write-Log "? System tray active - right-click to test IBKR"
Write-Log "?? Press Ctrl+C to exit"

# Test IBKR on startup
Test-IBKR | Out-Null

# Keep running
try {
    while ($true) {
        Start-Sleep -Seconds 10
        Write-Log "?? Heartbeat"
    }
} finally {
    $notifyIcon.Dispose()
}
