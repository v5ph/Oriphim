# Offline Backtesting Module

## Overview

This directory will contain the offline backtesting infrastructure for validating trading strategies before live deployment.

## Planned Components

### 1. Data Pipeline (`data_loader.py`)
- Historical minute-bar data ingestion
- Options chain reconstruction
- Market data normalization
- Event calendar integration

### 2. Simulation Engine (`simulator.py`)
- Order execution simulation
- Slippage and commission modeling
- Market impact estimation
- Realistic fill simulation

### 3. Options Pricing (`options_proxy.py`)
- Black-Scholes pricing model
- Volatility surface interpolation
- Greeks calculation
- Time decay simulation

### 4. Strategy Testing (`backtest_runner.py`)
- Strategy execution framework
- Performance metrics calculation
- Risk analysis
- Walk-forward validation

### 5. Results Analysis (`analyzer.py`)
- P&L attribution
- Risk-adjusted returns
- Drawdown analysis
- Trade statistics

## Implementation Priority

This module is marked as **future development** in the current MVP. The priority is:

1. ✅ Live trading infrastructure (core/*)
2. ✅ Real-time bot execution (bots/*)
3. ⏳ Backtesting framework (ml/offline_backtest/*)

## Usage (Future)

```python
from ml.offline_backtest import BacktestRunner
from bots.bot_A_putlite import PutLiteStrategy

# Initialize backtester
runner = BacktestRunner(
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=10000
)

# Load strategy
strategy = PutLiteStrategy(config)

# Run backtest
results = runner.run_backtest(strategy)

# Analyze results
print(f"Total Return: {results.total_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.max_drawdown:.2%}")
```

## Data Requirements

- SPY/QQQ minute bars (1+ years)
- Options chain snapshots
- Volatility surface data
- Economic event calendar
- Earnings announcement dates

## Timeline

Target implementation: Q2 2025 (after live trading validation)