# IBKR Options Bot System

AI-driven, rules-based options trading automation using Interactive Brokers API.

## Features

- **Bot A (PUT-Lite)**: 0DTE/1DTE bull put spreads on SPY/SPX
- **Bot B/C**: Skeleton implementations for buy-write and iron condor strategies
- **Risk Management**: Per-trade and daily loss limits with kill switches
- **Regime Detection**: IV rank, RV vs EM, VWAP band analysis
- **Event Awareness**: Blackout periods for CPI/FOMC/earnings
- **Real-time Dashboard**: Streamlit interface for monitoring and control

## Quick Start

### Prerequisites

1. **Interactive Brokers Account**: Set up TWS or IB Gateway
2. **Enable API Access**: TWS → Global Config → API → Settings → Enable Socket Clients
3. **Python 3.10+**: Required for this system

### Installation

```bash
# Navigate to project directory
cd ibkr_bots

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (Command Prompt):
.venv\Scripts\activate
# Windows (PowerShell):  
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
# Windows:
copy config\.env.example .env
# macOS/Linux:
cp config/.env.example .env
```

### Configuration

Edit `config/strategy.yaml` for your risk preferences and `config/universe.json` for symbols.

### Running Paper Trading

```bash
# First, test connection
python scripts/connection_test.py

# Run Bot A in paper mode
# Windows (WSL/Git Bash):
bash scripts/run_paper.sh
# Windows (Command Prompt):
python -m ibkr_bots.bots.bot_A_putlite --config config/strategy.yaml --dry-run

# In another terminal, start dashboard
streamlit run dashboards/app.py
```

### Safety Features

- **Paper-only by default**: Live trading requires explicit confirmation
- **Time windows**: Trading only during 10:30-13:30 ET
- **Auto-flatten**: Closes positions 90 minutes before market close
- **Risk limits**: Configurable per-trade and daily loss caps
- **Kill switches**: Automatic halt on volatility spikes or breach conditions

## Architecture

```
ibkr_bots/
├── bots/           # Trading strategy implementations
├── core/           # Shared infrastructure (broker, risk, options)
├── config/         # Strategy parameters and universe definitions
├── dashboards/     # Streamlit monitoring interface
├── scripts/        # Execution scripts
├── data/           # SQLite databases and cache files
└── logs/           # Trade logs and EOD reports
```

## Trading Logic (Bot A)

1. **Market Hours**: Active 10:30-13:30 ET
2. **Filters**: IV rank ≥45%, RV/EM ≥1.1, no blackout events
3. **Entry**: 0DTE/1DTE bull put spread at 5-10 delta
4. **Exit**: 50-60% profit target or time stop
5. **Risk**: Stop if underlying breaches halfway to short strike

## Monitoring

The Streamlit dashboard shows:
- Connection status and trading mode
- Live positions and P&L
- Filter status (IV rank, regime, events)
- Today's trading decisions and fills
- Emergency halt controls

## Safety Notes

⚠️ **PAPER TRADING ONLY** by default. Live mode requires `--i-understand` flag.

⚠️ **Real Money Risk**: Even paper trading uses real market data and order logic.

⚠️ **API Limits**: Respect IBKR rate limits and connection quotas.

## Support

- Check TWS/Gateway connection and API settings
- Verify market hours and symbol availability  
- Review logs in `logs/` directory for debugging
- Monitor dashboard for real-time system status

## License

Educational and research use only. No warranty for trading performance.