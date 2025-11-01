#!/usr/bin/env bash
#
# Run IBKR Options Bot in Live Trading Mode (GUARDED)
#
# Usage: bash scripts/run_live.sh --i-understand
#
# ⚠️  WARNING: This script executes LIVE TRADING with real money
# ⚠️  Only use with funded accounts and proper risk management
# ⚠️  Requires explicit confirmation flag
#

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Safety check - require explicit confirmation
if [[ "${1:-}" != "--i-understand" ]]; then
    echo "❌ SAFETY CHECK FAILED"
    echo ""
    echo "This script runs the bot in LIVE TRADING mode with real money."
    echo "To proceed, you must explicitly acknowledge the risks:"
    echo ""
    echo "Usage: $0 --i-understand"
    echo ""
    echo "⚠️  WARNINGS:"
    echo "   • Real money will be at risk"
    echo "   • Options trading involves substantial risk of loss"
    echo "   • Automated systems can malfunction"
    echo "   • Market conditions can change rapidly"
    echo "   • You may lose your entire investment"
    echo ""
    echo "Ensure you have:"
    echo "   ✓ Thoroughly backtested the strategy"
    echo "   ✓ Paper traded successfully for multiple sessions"
    echo "   ✓ Configured appropriate risk limits"
    echo "   ✓ Funded account with risk capital only"
    echo "   ✓ Monitored the system actively"
    echo ""
    exit 1
fi

echo "🚨 LIVE TRADING MODE INITIATED"
echo "Project root: $PROJECT_ROOT"

# Change to project directory  
cd "$PROJECT_ROOT"

# Verify MODE environment variable
if [[ "${MODE:-}" != "live" ]]; then
    echo "❌ Error: MODE environment variable must be set to 'live'"
    echo "   Current MODE: ${MODE:-unset}"
    echo "   Set with: export MODE=live"
    exit 1
fi

# Set up live trading environment
export IB_HOST=${IB_HOST:-127.0.0.1}
export IB_PORT=${IB_PORT:-7496}  # Live trading port
export IB_CLIENT_ID=${IB_CLIENT_ID:-1}

echo "📊 LIVE Configuration:"
echo "  Mode: $MODE"
echo "  IB Host: $IB_HOST"  
echo "  IB Port: $IB_PORT (LIVE)"
echo "  Client ID: $IB_CLIENT_ID"

# Additional safety checks
echo ""
echo "🔍 Running safety checks..."

# Check virtual environment
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "❌ Error: Virtual environment required for live trading"
    exit 1
fi
echo "✅ Virtual environment: $VIRTUAL_ENV"

# Check config file
if [[ ! -f "config/strategy.yaml" ]]; then
    echo "❌ Error: config/strategy.yaml not found"
    exit 1
fi
echo "✅ Config file exists"

# Check TWS/Gateway connection (live port)
if ! nc -z "$IB_HOST" "$IB_PORT" 2>/dev/null; then
    echo "❌ Error: Cannot connect to $IB_HOST:$IB_PORT"
    echo "   Please ensure IBKR TWS or IB Gateway is running in LIVE mode"
    echo "   TWS Live Trading Port: 7496"
    echo "   IB Gateway Live Trading Port: 4001"
    exit 1
fi
echo "✅ Live connection test passed"

# Check for paper trading indicators
if grep -q "mode: paper" config/strategy.yaml 2>/dev/null; then
    echo "⚠️  Warning: Config file may be set to paper mode"
    echo "   Please verify configuration is appropriate for live trading"
fi

# Final confirmation
echo ""
echo "🚨 FINAL WARNING"
echo "You are about to start LIVE TRADING with real money."
echo "The bot will place actual orders that can result in financial loss."
echo ""
read -p "Type 'I ACCEPT THE RISK' to continue: " confirmation

if [[ "$confirmation" != "I ACCEPT THE RISK" ]]; then
    echo "❌ Confirmation failed. Exiting for safety."
    exit 1
fi

# Create required directories
mkdir -p logs data

# Log the live trading session start
echo "$(date): LIVE TRADING SESSION STARTED by $(whoami)" >> logs/live_trading.log

echo ""
echo "🤖 Starting Bot A (PUT-Lite) in LIVE mode..."
echo "   ⚠️  REAL MONEY AT RISK"
echo "   Press Ctrl+C to stop (will close positions safely)"
echo "   Logs: logs/bot_A.log"
echo "   Live log: logs/live_trading.log"
echo "   Dashboard: streamlit run dashboards/app.py"
echo ""

# Set Python path and run in live mode
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

# Execute the bot in live mode (without --dry-run flag)
exec python -m ibkr_bots.bots.bot_A_putlite \
    --config config/strategy.yaml \
    --live