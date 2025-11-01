# Oriphim Runner 🚀

**AI-Driven Options Trading Automation Desktop Client**

Oriphim Runner is a Windows desktop application that connects your local Interactive Brokers (IBKR) account to the Oriphim cloud platform, enabling automated options trading execution with ML-powered decision making.

## ✨ Features

- **🔗 Cloud Integration**: Secure WebSocket connection to Oriphim dashboard
- **📊 IBKR Integration**: Direct connection to Interactive Brokers API
- **🤖 AI-Powered Trading**: Local ML models for trade analysis and execution
- **🖥️ Desktop UI**: Clean, minimal interface with real-time status updates
- **🛡️ Security**: Encrypted configuration and secure tunneling
- **📈 System Tray**: Run in background with status indicators
- **📝 Comprehensive Logging**: Detailed logs for monitoring and debugging

## 🏗️ Architecture

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   Oriphim       │◄──────────────►│   Oriphim       │
│   Dashboard     │   (Secure)      │   Runner        │
│   (Cloud)       │                 │   (Desktop)     │
└─────────────────┘                 └─────────────────┘
                                            │
                                            │ API
                                            ▼
                                    ┌─────────────────┐
                                    │  Interactive    │
                                    │  Brokers TWS    │
                                    │  (Local)        │
                                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Interactive Brokers Account**
   - TWS (Trader Workstation) installed and configured
   - API access enabled in TWS settings
   - Paper trading account for testing

2. **Development Environment**
   - Windows 10/11
   - Node.js 16+
   - Python 3.9+
   - Rust toolchain (for Tauri)

### Installation

1. **Clone and Setup**
   ```bash
   cd oriphim_runner
   npm install
   pip install -r requirements.txt
   ```

2. **Install Tauri CLI**
   ```bash
   npm install -g @tauri-apps/cli
   ```

3. **Setup IBKR Connection**
   - Start TWS (Trader Workstation)
   - Enable API access: Global Configuration → API → Settings
   - Note the API port (usually 7497 for paper, 7496 for live)

### Development

```bash
# Start development server
npm run dev

# This will:
# 1. Start the Tauri development server
# 2. Launch the desktop application
# 3. Auto-reload on file changes
```

### Building for Production

```bash
# Build optimized desktop application
npm run build

# Output will be in src-tauri/target/release/
```

## 📱 User Interface

### Main Window
- **Connection Status**: Cloud and broker connection indicators
- **Current Activity**: Active trading jobs and strategy details
- **Recent Logs**: Real-time activity feed with timestamps
- **Controls**: Pause/resume, restart, and logs access

### System Tray
- **Status Indicators**: 
  - 🔴 Red: Disconnected
  - 🟡 Yellow: Connected, running jobs
  - 🟢 Green: Connected, idle
- **Quick Actions**: Open, start/stop, view logs, exit

## 🔧 Configuration

### API Key Setup
On first launch, you'll be prompted to enter your Oriphim API key:
1. Get your API key from the Oriphim dashboard (Settings → API Keys)
2. Enter it in the setup dialog
3. The Runner will save it securely and connect automatically

### IBKR Configuration
The Runner auto-detects your TWS connection:
- **Paper Trading**: Port 7497 (default)
- **Live Trading**: Port 7496
- **Gateway**: Ports 4001/4002

### Advanced Settings
Configuration is stored in `~/.oriphim/config.json`:
```json
{
  "api_key": "encrypted_key_here",
  "ibkr": {
    "host": "127.0.0.1",
    "port": 7497,
    "client_id": 1
  },
  "logging": {
    "level": "INFO",
    "max_files": 10
  }
}
```

## 📊 Trading Strategies

The Runner supports these automated strategies:

### Bot A - PUT-Lite Intraday Premium Harvester
- **Strategy**: Cash-secured put writing on SPX/SPY
- **Timeframe**: 0DTE/1DTE options
- **Edge**: Volatility risk premium harvesting
- **Risk**: Max $50 per trade

### Bot B - Micro Buy-Write
- **Strategy**: Covered calls on large-cap positions
- **Timeframe**: Same-day to 1-day options
- **Edge**: Theta decay on neutral trends
- **Risk**: 25-50% position coverage

### Bot C - Calm-Tape Condor
- **Strategy**: Iron condors during low volatility
- **Timeframe**: 0DTE range-bound plays
- **Edge**: Mean-reversion in calm markets
- **Risk**: Defined-risk spreads

## 🛡️ Security & Safety

### Risk Management
- **Per-trade limit**: $50 maximum loss
- **Daily limit**: $150 total exposure
- **Time stops**: All positions closed before market close
- **Volatility kill-switch**: Trading halted during high volatility events

### Data Security
- **Encrypted storage**: API keys and sensitive data encrypted at rest
- **Secure tunneling**: WebSocket connections use TLS encryption
- **Local processing**: Trade decisions made locally, not in cloud

### Safety Features
- **Paper trading first**: All strategies start in paper mode
- **Event blackouts**: No trading during CPI, FOMC, earnings
- **Connection monitoring**: Automatic reconnection and failsafes

## 📁 Project Structure

```
oriphim_runner/
├── src/                      # Frontend (HTML/CSS/JS)
│   ├── index.html           # Main UI
│   ├── styles.css           # UI styling
│   ├── app.js               # Frontend logic
│   └── assets/              # Images and icons
├── src-tauri/               # Tauri backend (Rust)
│   ├── src/main.rs          # Main Tauri application
│   ├── Cargo.toml           # Rust dependencies
│   └── tauri.conf.json      # Tauri configuration
├── src/                     # Python backend
│   ├── main.py              # Main orchestration
│   ├── websocket_client.py  # Cloud communication
│   ├── broker_ibkr.py       # IBKR integration
│   ├── engine.py            # Trading engine
│   ├── storage.py           # Data management
│   └── ui_manager.py        # Python UI (optional)
├── package.json             # Node.js dependencies
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔍 Monitoring & Debugging

### Logs Location
- **Windows**: `%USERPROFILE%\.oriphim\logs\`
- **Format**: Structured JSON logs with timestamps
- **Retention**: Last 10 files, 10MB each

### Debug Mode
```bash
# Enable verbose logging
npm run dev -- --debug

# View real-time logs
tail -f ~/.oriphim/logs/runner.log
```

### Health Checks
The Runner performs continuous health monitoring:
- Connection status every 30 seconds
- Trade position reconciliation every 5 minutes
- ML model performance tracking
- System resource usage monitoring

## 🚨 Troubleshooting

### Common Issues

**"Cannot connect to IBKR"**
- Verify TWS is running and API is enabled
- Check port settings (7497 for paper, 7496 for live)
- Ensure no firewall blocking localhost connections

**"Cloud connection failed"**
- Verify API key is correct and active
- Check internet connection
- Look for proxy/VPN interference

**"Python runner not starting"**
- Ensure Python 3.9+ is installed and in PATH
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check logs for specific error messages

### Support Channels
- **Documentation**: [docs.oriphim.com](https://docs.oriphim.com)
- **Discord**: [discord.gg/oriphim](https://discord.gg/oriphim)
- **Email**: support@oriphim.com

## 🔄 Updates & Maintenance

### Auto-Updates
- The Runner checks for updates on startup
- Critical security updates are applied automatically
- Feature updates require user confirmation

### Manual Updates
```bash
# Update to latest version
git pull origin main
npm install
pip install -r requirements.txt --upgrade
npm run build
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**⚠️ Disclaimer**: Options trading involves significant risk. This software is provided for educational and research purposes. Always start with paper trading and understand the risks before deploying real capital.

**🏦 Interactive Brokers**: This software is not affiliated with Interactive Brokers. IBKR is a trademark of Interactive Brokers LLC.