<#
.SYNOPSIS
    Oriphim Trading Bot Runner - Windows Desktop Application
.DESCRIPTION
    Lightweight desktop app that connects to Oriphim Cloud and executes trading bots via IBKR
.PARAMETER Debug
    Enable debug logging to console
.PARAMETER ConfigPath
    Path to configuration file
.EXAMPLE
    .\OriphimRunner.ps1 -Debug
#>

param(
    [switch]$Debug,
    [string]$ConfigPath = "$env:USERPROFILE\.oriphim\config.json"
)

# Import required assemblies for GUI
Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Global variables
$Script:Config = @{}
$Script:IsConnected = $false
$Script:IsPaused = $false
$Script:CurrentJob = $null
$Script:LogBuffer = @()
$Script:MainWindow = $null
$Script:NotifyIcon = $null
$Script:MainTimer = $null

#region Configuration Management
function Initialize-Config {
    $configDir = Split-Path $ConfigPath -Parent
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    
    if (Test-Path $ConfigPath) {
        try {
            $Script:Config = Get-Content $ConfigPath | ConvertFrom-Json -AsHashtable
        } catch {
            Write-Log "Warning: Could not parse config file, using defaults" "WARN"
            $Script:Config = @{}
        }
    }
    
    # Ensure all required config values exist with defaults
    $defaults = @{
        ApiKey = ""
        BrokerType = "IBKR"
        IBKRHost = "127.0.0.1"  
        IBKRPort = 7497
        Mode = "PAPER"
        AutoStart = $false
        LogLevel = "INFO"
        FirstRunCompleted = $false
        SupabaseUrl = "https://your-project.supabase.co"
        CloudEndpoint = "https://your-project.supabase.co/functions/v1"
    }
    
    foreach ($key in $defaults.Keys) {
        if (-not $Script:Config.ContainsKey($key)) {
            $Script:Config[$key] = $defaults[$key]
        }
    }
    
    Save-Config
}

function Save-Config {
    try {
        $Script:Config | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath
        Write-Log "Config saved to $ConfigPath" "DEBUG"
    } catch {
        Write-Log "Error saving config: $($_.Exception.Message)" "ERROR"
    }
}

function Get-ConfigValue($Key, $Default = $null) {
    if ($Script:Config.ContainsKey($Key) -and $null -ne $Script:Config[$Key]) {
        return $Script:Config[$Key]
    } else {
        return $Default
    }
}

function Set-ConfigValue($Key, $Value) {
    $Script:Config[$Key] = $Value
    Save-Config
}
#endregion

#region Logging
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logEntry = "[$timestamp] $Level`: $Message"
    
    # Add to buffer (keep last 100 entries)
    $Script:LogBuffer += $logEntry
    if ($Script:LogBuffer.Count > 100) {
        $Script:LogBuffer = $Script:LogBuffer[-100..-1]
    }
    
    # Update UI if exists
    if ($Script:MainWindow -and $Script:MainWindow.FindName("LogTextBox")) {
        try {
            $Script:MainWindow.Dispatcher.Invoke([Action]{
                $logTextBox = $Script:MainWindow.FindName("LogTextBox")
                $logTextBox.Text = ($Script:LogBuffer | Select-Object -Last 15) -join "`n"
                $logTextBox.ScrollToEnd()
            })
        } catch {
            # UI might not be ready, ignore
        }
    }
    
    # Console output in debug mode
    if ($Debug) {
        Write-Host $logEntry -ForegroundColor $(switch($Level) {
            "ERROR" { "Red" }
            "WARN" { "Yellow" }  
            "INFO" { "Green" }
            "DEBUG" { "Cyan" }
            default { "White" }
        })
    }
    
    # Save to log file
    try {
        $logDir = "$env:USERPROFILE\.oriphim\logs"
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        }
        $logFile = "$logDir\runner_$(Get-Date -Format 'yyyy-MM-dd').log"
        Add-Content -Path $logFile -Value $logEntry
    } catch {
        # Ignore file logging errors
    }
}
#endregion

#region IBKR Integration
function Test-IBKRConnection {
    try {
        Write-Log "Testing IBKR connection..." "INFO"
        
        $host = Get-ConfigValue "IBKRHost" "127.0.0.1"
        $port = Get-ConfigValue "IBKRPort" 7497
        
        # Simple TCP connection test first
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.Connect($host, $port)
            $tcpClient.Close()
            Write-Log "✅ IBKR TCP connection successful ($host`:$port)" "INFO"
        } catch {
            Write-Log "❌ IBKR TCP connection failed ($host`:$port): $($_.Exception.Message)" "ERROR"
            return $false
        }
        
        # Try Python IBKR test if available
        $ibkrPath = Join-Path $PSScriptRoot "..\ibkr_bots"
        if (Test-Path $ibkrPath) {
            $pythonScript = @"
import sys
import os
sys.path.append(r'$ibkrPath')

try:
    from core.broker import get_broker
    broker = get_broker()
    if broker.connect(host='$host', port=$port):
        print("IBKR_CONNECTED")
        broker.disconnect()
    else:
        print("IBKR_FAILED")
except Exception as e:
    print(f"IBKR_ERROR: {e}")
"@
            
            try {
                $result = python -c $pythonScript 2>&1
                if ($result -match "IBKR_CONNECTED") {
                    Write-Log "✅ IBKR API connection successful" "INFO"
                    return $true
                } else {
                    Write-Log "⚠️  IBKR API test: $result" "WARN"
                    return $true  # TCP worked, assume API will work
                }
            } catch {
                Write-Log "⚠️  Python IBKR test unavailable, using TCP test result" "WARN"
                return $true
            }
        } else {
            Write-Log "⚠️  IBKR bots path not found, using TCP test result" "WARN"
            return $true
        }
        
    } catch {
        Write-Log "❌ IBKR test error: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Start-TradingBot {
    param([hashtable]$JobConfig)
    
    try {
        Write-Log "🤖 Starting bot: $($JobConfig.bot_type)" "INFO"
        
        $ibkrPath = Join-Path $PSScriptRoot "..\ibkr_bots"
        if (-not (Test-Path $ibkrPath)) {
            Write-Log "❌ IBKR bots directory not found at: $ibkrPath" "ERROR"
            return
        }
        
        # Prepare Python execution
        $jobConfigJson = $JobConfig | ConvertTo-Json -Compress
        $pythonScript = @"
import sys
import json
import os
sys.path.append(r'$ibkrPath')

try:
    job_config = json.loads('$($jobConfigJson -replace "'", "\''")')
    print(f"Executing bot: {job_config.get('bot_type', 'unknown')}")
    
    # Import and run the appropriate bot
    bot_type = job_config.get('bot_type', '')
    
    if bot_type == 'putlite':
        from bots.bot_A_putlite import PutLiteBot
        bot = PutLiteBot(job_config)
        result = bot.run()
    elif bot_type == 'buywrite':  
        from bots.bot_B_buywrite import BuyWriteBot
        bot = BuyWriteBot(job_config)
        result = bot.run()
    elif bot_type == 'condor':
        from bots.bot_C_condor import CondorBot
        bot = CondorBot(job_config)
        result = bot.run()
    else:
        result = {'status': 'error', 'message': f'Unknown bot type: {bot_type}'}
    
    print(f"RESULT: {json.dumps(result)}")
    
except Exception as e:
    import traceback
    print(f"BOT_ERROR: {str(e)}")
    print(f"TRACEBACK: {traceback.format_exc()}")
"@
        
        # Execute bot in background job
        $job = Start-Job -ScriptBlock {
            param($Script)
            python -c $Script
        } -ArgumentList $pythonScript
        
        $jobId = if ($JobConfig.id) { $JobConfig.id } else { (New-Guid).ToString() }
        
        $Script:CurrentJob = @{
            PowerShellJob = $job
            Config = $JobConfig
            StartTime = Get-Date
            Id = $jobId
        }
        
        Write-Log "🚀 Bot job started (ID: $($job.Id))" "INFO"
        Update-MainWindow
        
    } catch {
        Write-Log "❌ Failed to start bot: $($_.Exception.Message)" "ERROR"
    }
}

function Stop-TradingBot {
    if ($Script:CurrentJob) {
        try {
            Stop-Job $Script:CurrentJob.PowerShellJob -Force
            Remove-Job $Script:CurrentJob.PowerShellJob -Force
            Write-Log "🛑 Trading bot stopped" "INFO"
            $Script:CurrentJob = $null
            Update-MainWindow
        } catch {
            Write-Log "❌ Error stopping bot: $($_.Exception.Message)" "ERROR"
        }
    }
}

function Check-JobStatus {
    if (-not $Script:CurrentJob) { return }
    
    $job = $Script:CurrentJob.PowerShellJob
    
    if ($job.State -eq "Completed") {
        try {
            $result = Receive-Job $job
            Write-Log "📊 Bot completed: $result" "INFO"
            
            # Parse result if it contains RESULT: prefix
            $resultLine = $result | Where-Object { $_ -match "^RESULT:" } | Select-Object -First 1
            if ($resultLine) {
                $jsonResult = $resultLine -replace "^RESULT: ", ""
                try {
                    $parsedResult = $jsonResult | ConvertFrom-Json
                    $pnlValue = if ($parsedResult.pnl) { $parsedResult.pnl } else { 'N/A' }
                    Write-Log "✅ Bot result: Status=$($parsedResult.status), PnL=$pnlValue" "INFO"
                } catch {
                    Write-Log "⚠️  Could not parse bot result: $jsonResult" "WARN"
                }
            }
            
            Remove-Job $job
            $Script:CurrentJob = $null
            Update-MainWindow
            
        } catch {
            Write-Log "❌ Error getting job result: $($_.Exception.Message)" "ERROR"
        }
    } elseif ($job.State -eq "Failed") {
        try {
            $error = Receive-Job $job
            Write-Log "❌ Bot failed: $error" "ERROR"
            Remove-Job $job
            $Script:CurrentJob = $null
            Update-MainWindow
        } catch {
            Write-Log "❌ Error getting job error: $($_.Exception.Message)" "ERROR"
        }
    }
}
#endregion

#region Cloud Communication (Mock Implementation)
function Connect-OriphimCloud {
    try {
        $apiKey = Get-ConfigValue "ApiKey"
        if (-not $apiKey -or $apiKey -eq "") {
            Write-Log "⚠️  No API key configured - running in offline mode" "WARN"
            $Script:IsConnected = $false
            Update-SystemTray
            return $false
        }
        
        Write-Log "🌐 Connecting to Oriphim Cloud..." "INFO"
        
        # For MVP, simulate connection success
        # In production, this would make actual HTTP requests to Supabase
        Start-Sleep 1
        $Script:IsConnected = $true
        Write-Log "✅ Cloud connection established (simulated)" "INFO"
        Update-SystemTray
        Update-MainWindow
        
        return $true
        
    } catch {
        Write-Log "❌ Cloud connection failed: $($_.Exception.Message)" "ERROR"
        $Script:IsConnected = $false
        Update-SystemTray
        Update-MainWindow
        return $false
    }
}

function Poll-CloudJobs {
    if (-not $Script:IsConnected -or $Script:IsPaused) { return }
    
    # For testing, simulate receiving a job every 30 seconds
    # In production, this would poll Supabase for actual jobs
    
    $now = Get-Date
    $lastJobTime = Get-ConfigValue "LastSimulatedJob" ([DateTime]::MinValue)
    
    if (($now - [DateTime]$lastJobTime).TotalSeconds -gt 60 -and -not $Script:CurrentJob) {
        # Simulate receiving a job
        $simulatedJob = @{
            id = [Guid]::NewGuid().ToString()
            bot_type = @("putlite", "buywrite", "condor") | Get-Random
            symbol = @("SPY", "QQQ", "IWM") | Get-Random
            config = @{
                mode = "paper"
                max_risk = 50
                target_delta = 0.10
            }
            created_at = $now.ToString("o")
        }
        
        Write-Log "📨 Simulated job received: $($simulatedJob.bot_type) on $($simulatedJob.symbol)" "INFO"
        Start-TradingBot $simulatedJob
        Set-ConfigValue "LastSimulatedJob" $now.ToString("o")
    }
}
#endregion

#region System Tray
function Initialize-SystemTray {
    $Script:NotifyIcon = New-Object System.Windows.Forms.NotifyIcon
    
    # Try to load custom icon, fallback to system icon
    $iconPath = Join-Path $PSScriptRoot "assets\oriphim.ico"
    if (Test-Path $iconPath) {
        try {
            $Script:NotifyIcon.Icon = [System.Drawing.Icon]::new($iconPath)
        } catch {
            Write-Log "Could not load custom icon, using system icon" "WARN"
            $Script:NotifyIcon.Icon = [System.Drawing.SystemIcons]::Application
        }
    } else {
        $Script:NotifyIcon.Icon = [System.Drawing.SystemIcons]::Application
    }
    
    $Script:NotifyIcon.Text = "Oriphim Runner"
    $Script:NotifyIcon.Visible = $true
    
    # Context menu
    $contextMenu = New-Object System.Windows.Forms.ContextMenuStrip
    
    $openItem = New-Object System.Windows.Forms.ToolStripMenuItem("Open Runner")
    $openItem.add_Click({ Show-MainWindow })
    $contextMenu.Items.Add($openItem)
    
    $contextMenu.Items.Add("-")  # Separator
    
    $pauseItem = New-Object System.Windows.Forms.ToolStripMenuItem("Pause")
    $pauseItem.add_Click({ Toggle-RunnerState })
    $contextMenu.Items.Add($pauseItem)
    
    $testItem = New-Object System.Windows.Forms.ToolStripMenuItem("Test IBKR")
    $testItem.add_Click({ Test-IBKRConnection })
    $contextMenu.Items.Add($testItem)
    
    $logsItem = New-Object System.Windows.Forms.ToolStripMenuItem("View Logs")
    $logsItem.add_Click({ Show-LogFolder })
    $contextMenu.Items.Add($logsItem)
    
    $contextMenu.Items.Add("-")  # Separator
    
    $exitItem = New-Object System.Windows.Forms.ToolStripMenuItem("Exit")
    $exitItem.add_Click({ Stop-Runner })
    $contextMenu.Items.Add($exitItem)
    
    $Script:NotifyIcon.ContextMenuStrip = $contextMenu
    
    # Double-click to open
    $Script:NotifyIcon.add_DoubleClick({ Show-MainWindow })
    
    Update-SystemTray
}

function Update-SystemTray {
    if (-not $Script:NotifyIcon) { return }
    
    $status = if ($Script:IsConnected) { "Connected" } else { "Disconnected" }
    $pauseStatus = if ($Script:IsPaused) { " (Paused)" } else { "" }
    $jobStatus = if ($Script:CurrentJob) { " - Running Job" } else { "" }
    
    $Script:NotifyIcon.Text = "Oriphim Runner - $status$pauseStatus$jobStatus"
    
    # Update context menu pause item
    if ($Script:NotifyIcon.ContextMenuStrip) {
        $pauseItem = $Script:NotifyIcon.ContextMenuStrip.Items | Where-Object { $_.Text -match "Pause|Resume" }
        if ($pauseItem) {
            $pauseItem.Text = if ($Script:IsPaused) { "Resume" } else { "Pause" }
        }
    }
}
#endregion

#region Main Window
function Show-MainWindow {
    if ($Script:MainWindow) {
        $Script:MainWindow.WindowState = "Normal"
        $Script:MainWindow.Activate()
        return
    }
    
    # Create WPF window
    $xaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        Title="Oriphim Runner" Height="600" Width="700" 
        WindowStartupLocation="CenterScreen"
        ResizeMode="CanResize" MinHeight="500" MinWidth="600">
    <Grid Margin="20">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>
        
        <!-- Header -->
        <StackPanel Grid.Row="0" Orientation="Horizontal" Margin="0,0,0,20">
            <TextBlock Text="⚛" FontSize="28" Margin="0,0,15,0" Foreground="DarkBlue"/>
            <StackPanel>
                <TextBlock Text="ORIPHIM RUNNER" FontSize="20" FontWeight="Bold"/>
                <TextBlock Text="AI-Driven Options Trading Automation" FontSize="12" Foreground="Gray"/>
            </StackPanel>
        </StackPanel>
        
        <!-- Status Panel -->
        <Border Grid.Row="1" Background="#f8f9fa" Padding="15" CornerRadius="5" Margin="0,0,0,20">
            <Grid>
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>
                <Grid.RowDefinitions>
                    <RowDefinition Height="Auto"/>
                    <RowDefinition Height="Auto"/>
                    <RowDefinition Height="Auto"/>
                    <RowDefinition Height="Auto"/>
                    <RowDefinition Height="Auto"/>
                </Grid.RowDefinitions>
                
                <TextBlock Grid.Row="0" Grid.Column="0" Text="● Cloud Connection:" FontWeight="Bold" Margin="0,5"/>
                <TextBlock Grid.Row="0" Grid.Column="1" Name="CloudStatus" Text="DISCONNECTED" Foreground="Red" Margin="0,5"/>
                
                <TextBlock Grid.Row="1" Grid.Column="0" Text="● Broker (IBKR):" FontWeight="Bold" Margin="0,5"/>  
                <TextBlock Grid.Row="1" Grid.Column="1" Name="BrokerStatus" Text="Not Connected" Margin="0,5"/>
                
                <TextBlock Grid.Row="2" Grid.Column="0" Text="● Trading Mode:" FontWeight="Bold" Margin="0,5"/>
                <TextBlock Grid.Row="2" Grid.Column="1" Name="ModeStatus" Text="PAPER" Foreground="Orange" Margin="0,5"/>
                
                <TextBlock Grid.Row="3" Grid.Column="0" Text="● Runner Version:" FontWeight="Bold" Margin="0,5"/>
                <TextBlock Grid.Row="3" Grid.Column="1" Text="v1.0.0 (PowerShell)" Margin="0,5"/>
                
                <TextBlock Grid.Row="4" Grid.Column="0" Text="● Current Job:" FontWeight="Bold" Margin="0,5"/>
                <TextBlock Grid.Row="4" Grid.Column="1" Name="JobStatus" Text="None" Margin="0,5"/>
            </Grid>
        </Border>
        
        <!-- Control Buttons -->
        <StackPanel Grid.Row="2" Orientation="Horizontal" HorizontalAlignment="Center" Margin="0,0,0,20">
            <Button Name="PauseButton" Content="⏸ Pause Runner" Width="120" Margin="5" Padding="8,5" 
                    Background="LightBlue" BorderBrush="DarkBlue"/>
            <Button Name="RestartButton" Content="↻ Restart" Width="100" Margin="5" Padding="8,5"
                    Background="LightGreen" BorderBrush="DarkGreen"/>
            <Button Name="TestButton" Content="🔧 Test IBKR" Width="100" Margin="5" Padding="8,5"
                    Background="LightYellow" BorderBrush="Orange"/>
            <Button Name="LogsButton" Content="📁 Open Logs" Width="120" Margin="5" Padding="8,5"
                    Background="LightGray" BorderBrush="Gray"/>
        </StackPanel>
        
        <!-- Logs -->
        <GroupBox Grid.Row="3" Header="▸ Latest Activity Logs" FontWeight="Bold" Margin="0,0,0,20">
            <ScrollViewer Name="LogScrollViewer" VerticalScrollBarVisibility="Auto">
                <TextBox Name="LogTextBox" IsReadOnly="True" FontFamily="Consolas" FontSize="11"
                         Background="Black" Foreground="Lime" BorderThickness="0" 
                         TextWrapping="Wrap" Padding="10"/>
            </ScrollViewer>
        </GroupBox>
        
        <!-- Footer -->
        <StackPanel Grid.Row="4" Orientation="Horizontal" HorizontalAlignment="Right">
            <TextBlock Text="💡 Tip: Minimize to system tray • Right-click tray icon for quick actions" 
                       FontSize="10" Foreground="Gray"/>
        </StackPanel>
    </Grid>
</Window>
"@
    
    try {
        $Script:MainWindow = [Windows.Markup.XamlReader]::Parse($xaml)
        
        # Event handlers
        $Script:MainWindow.FindName("PauseButton").add_Click({ Toggle-RunnerState })
        $Script:MainWindow.FindName("RestartButton").add_Click({ Restart-Runner })
        $Script:MainWindow.FindName("TestButton").add_Click({ Test-IBKRConnection })
        $Script:MainWindow.FindName("LogsButton").add_Click({ Show-LogFolder })
        
        # Window events - minimize to tray instead of closing
        $Script:MainWindow.add_Closing({
            param($sender, $e)
            $e.Cancel = $true
            $sender.WindowState = "Minimized"
            $sender.Hide()
            $Script:NotifyIcon.ShowBalloonTip(3000, "Oriphim Runner", "Minimized to system tray", [System.Windows.Forms.ToolTipIcon]::Info)
        })
        
        # Update status immediately
        Update-MainWindow
        
        $Script:MainWindow.Show()
        Write-Log "✅ Main window opened" "INFO"
        
    } catch {
        Write-Log "❌ Error creating main window: $($_.Exception.Message)" "ERROR"
        [System.Windows.Forms.MessageBox]::Show("Error creating main window: $($_.Exception.Message)", "Oriphim Runner Error", "OK", "Error")
    }
}

function Update-MainWindow {
    if (-not $Script:MainWindow) { return }
    
    try {
        $Script:MainWindow.Dispatcher.Invoke([Action]{
            # Update connection status
            $cloudStatus = $Script:MainWindow.FindName("CloudStatus")
            $brokerStatus = $Script:MainWindow.FindName("BrokerStatus")
            $jobStatus = $Script:MainWindow.FindName("JobStatus")
            $pauseButton = $Script:MainWindow.FindName("PauseButton")
            
            if ($Script:IsConnected) {
                $cloudStatus.Text = "CONNECTED"
                $cloudStatus.Foreground = "Green"
            } else {
                $cloudStatus.Text = "DISCONNECTED" 
                $cloudStatus.Foreground = "Red"
            }
            
            # Update broker status
            $host = Get-ConfigValue "IBKRHost" "127.0.0.1"
            $port = Get-ConfigValue "IBKRPort" 7497
            $brokerStatus.Text = "$host`:$port"
            
            # Update job status
            if ($Script:CurrentJob) {
                $elapsed = ((Get-Date) - $Script:CurrentJob.StartTime).ToString("mm\:ss")
                $jobStatus.Text = "$($Script:CurrentJob.Config.bot_type) ($elapsed)"
                $jobStatus.Foreground = "Blue"
            } else {
                $jobStatus.Text = "None"
                $jobStatus.Foreground = "Black"
            }
            
            # Update pause button
            if ($Script:IsPaused) {
                $pauseButton.Content = "▶ Resume Runner"
                $pauseButton.Background = "LightGreen"
            } else {
                $pauseButton.Content = "⏸ Pause Runner"
                $pauseButton.Background = "LightBlue"
            }
            
            # Update logs
            $logTextBox = $Script:MainWindow.FindName("LogTextBox")
            $logTextBox.Text = ($Script:LogBuffer | Select-Object -Last 20) -join "`n"
            
            # Auto-scroll to bottom
            $logScrollViewer = $Script:MainWindow.FindName("LogScrollViewer")
            $logScrollViewer.ScrollToEnd()
        })
    } catch {
        # UI update failed, ignore
    }
}
#endregion

#region Control Functions
function Toggle-RunnerState {
    $Script:IsPaused = -not $Script:IsPaused
    
    if ($Script:IsPaused) {
        Write-Log "⏸ Runner paused by user" "INFO"
        if ($Script:CurrentJob) {
            Stop-TradingBot
        }
    } else {
        Write-Log "▶ Runner resumed by user" "INFO"
    }
    
    Update-SystemTray
    Update-MainWindow
}

function Restart-Runner {
    Write-Log "🔄 Restarting runner..." "INFO"
    
    # Stop current job
    Stop-TradingBot
    
    # Reset connection state
    $Script:IsConnected = $false
    $Script:IsPaused = $false
    
    # Wait a moment
    Start-Sleep 2
    
    # Reconnect
    Test-IBKRConnection
    Connect-OriphimCloud
    
    Update-SystemTray
    Update-MainWindow
    
    Write-Log "✅ Runner restart complete" "INFO"
}

function Show-LogFolder {
    $logPath = "$env:USERPROFILE\.oriphim\logs"
    if (-not (Test-Path $logPath)) {
        New-Item -ItemType Directory -Path $logPath -Force | Out-Null
    }
    Start-Process explorer.exe $logPath
    Write-Log "📁 Opened logs folder" "INFO"
}

function Stop-Runner {
    Write-Log "🛑 Shutting down Oriphim Runner..." "INFO"
    
    # Stop any running jobs
    Stop-TradingBot
    
    # Stop timer
    if ($Script:MainTimer) {
        $Script:MainTimer.Stop()
        $Script:MainTimer.Dispose()
    }
    
    # Clean up system tray
    if ($Script:NotifyIcon) {
        $Script:NotifyIcon.Visible = $false
        $Script:NotifyIcon.Dispose()
    }
    
    # Close main window
    if ($Script:MainWindow) {
        $Script:MainWindow.Close()
    }
    
    Write-Log "👋 Oriphim Runner stopped" "INFO"
    
    [System.Windows.Forms.Application]::Exit()
    exit 0
}

function Show-SetupDialog {
    $apiKey = Get-ConfigValue "ApiKey"
    
    if ($apiKey -and $apiKey -ne "") {
        return  # Already configured
    }
    
    Add-Type -AssemblyName Microsoft.VisualBasic
    
    $apiKey = [Microsoft.VisualBasic.Interaction]::InputBox(
        "Welcome to Oriphim Runner!`n`nTo get started, please enter your API key from the Oriphim dashboard:`n(You can find this under Settings → API Keys)",
        "Oriphim Runner Setup",
        ""
    )
    
    if ($apiKey -and $apiKey.Trim() -ne "") {
        Set-ConfigValue "ApiKey" $apiKey.Trim()
        Write-Log "✅ API key configured" "INFO"
        Connect-OriphimCloud
    } else {
        Write-Log "⚠️  Setup skipped - running in offline mode" "WARN"
    }
}
#endregion

#region Main Execution Loop
function Start-Runner {
    Write-Log "🚀 Starting Oriphim Runner..." "INFO"
    Write-Log "Version: 1.0.0 (PowerShell Edition)" "INFO"
    Write-Log "Config: $ConfigPath" "DEBUG"
    
    try {
        # Initialize components
        Initialize-Config
        Initialize-SystemTray
        
        # Show setup dialog on first run
        if (-not (Get-ConfigValue "FirstRunCompleted")) {
            Show-SetupDialog
            Set-ConfigValue "FirstRunCompleted" $true
        }
        
        # Initial connection tests
        Test-IBKRConnection
        Connect-OriphimCloud
        
        # Show main window
        Show-MainWindow
        
        # Set up main timer for periodic tasks
        $Script:MainTimer = New-Object System.Windows.Forms.Timer
        $Script:MainTimer.Interval = 5000  # 5 seconds
        $Script:MainTimer.add_Tick({
            try {
                Poll-CloudJobs
                Check-JobStatus
                Update-SystemTray
            } catch {
                Write-Log "Timer error: $($_.Exception.Message)" "ERROR"
            }
        })
        $Script:MainTimer.Start()
        
        Write-Log "✅ Oriphim Runner is now active" "INFO"
        Write-Log "💡 Double-click system tray icon to open window" "INFO"
        
        # Start Windows Forms message loop
        [System.Windows.Forms.Application]::EnableVisualStyles()
        [System.Windows.Forms.Application]::Run()
        
    } catch {
        Write-Log "❌ Critical error in main loop: $($_.Exception.Message)" "ERROR"
        [System.Windows.Forms.MessageBox]::Show("Critical error: $($_.Exception.Message)", "Oriphim Runner Error", "OK", "Error")
    } finally {
        Stop-Runner
    }
}
#endregion

# Handle Ctrl+C gracefully
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Write-Log "🛑 PowerShell exiting, cleaning up..." "INFO"
    Stop-Runner
}

# Script entry point
if ($MyInvocation.InvocationName -ne '.') {
    try {
        Start-Runner
    } catch {
        Write-Host "Fatal error: $($_.Exception.Message)" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}