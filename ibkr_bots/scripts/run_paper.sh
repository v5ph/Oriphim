#!/usr/bin/env bash
#
# Run IBKR Options Bot in Paper Trading Mode
#
# Usage: bash scripts/run_paper.sh
#
# Prerequisites:
# 1. IBKR TWS or IB Gateway running on localhost:7497 (paper account)
# 2. Python virtual environment activated
# 3. Dependencies installed (pip install -r requirements.txt)
#

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting IBKR Options Bot - Paper Trading Mode"
echo "Project root: $PROJECT_ROOT"

# Change to project directory
cd "$PROJECT_ROOT"

# Set environment for paper trading
export MODE=paper
export IB_HOST=${IB_HOST:-127.0.0.1}
export IB_PORT=${IB_PORT:-7497}
export IB_CLIENT_ID=${IB_CLIENT_ID:-1}

echo "📊 Configuration:"
echo "  Mode: $MODE"
echo "  IB Host: $IB_HOST"
echo "  IB Port: $IB_PORT"
echo "  Client ID: $IB_CLIENT_ID"

# Check if virtual environment is activated
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider running: python -m venv .venv && source .venv/bin/activate"
else
    echo "✅ Virtual environment: $VIRTUAL_ENV"
fi

# Check if config file exists
if [[ ! -f "config/strategy.yaml" ]]; then
    echo "❌ Error: config/strategy.yaml not found"
    echo "   Please ensure configuration file exists"
    exit 1
fi

# Check if TWS/Gateway is likely running
if ! nc -z "$IB_HOST" "$IB_PORT" 2>/dev/null; then
    echo "❌ Error: Cannot connect to $IB_HOST:$IB_PORT"
    echo "   Please ensure IBKR TWS or IB Gateway is running in paper mode"
    echo "   TWS Paper Trading Port: 7497"
    echo "   IB Gateway Paper Trading Port: 4002"
    exit 1
fi

echo "✅ Connection test passed"

# Create required directories
mkdir -p logs data

# Run the bot with paper trading settings
echo "🤖 Starting Bot A (PUT-Lite) in paper mode..."
echo "   Press Ctrl+C to stop"
echo "   Logs: logs/bot_A.log"
echo "   Dashboard: streamlit run dashboards/app.py"
echo ""

# Add current directory to Python path and run bot
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

# Execute the bot
exec python -m ibkr_bots.bots.bot_A_putlite \
    --config config/strategy.yaml \
    --dry-run