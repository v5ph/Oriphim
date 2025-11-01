# Project Market Watch

AI-Driven Options Trading Automation

## I. Mission Overview

Develop and deploy three AI-assisted, rules-based options trading bots that execute proven, risk-adjusted strategies in high-liquidity sectors. All bots begin with paper trading through Interactive Brokers (IBKR), then transition to live execution once backtests confirm profitability.

## II. Strategy Framework

### Top 3 Options Strategies (Evidence-Based)

1) Cash-Secured Put Writing (Index Options)
   - Edge: Harvests the Volatility Risk Premium (VRP) — implied volatility consistently exceeds realized volatility.
   - Historical: ~9.4% annualized since 1986 (Cboe PutWrite Index), with lower drawdowns than S&P 500.
   - Day-trading adaptation:
     - Sell short-dated (0DTE/1DTE) far OTM puts on SPX/SPY during mid-day volatility compression.
     - Entry filter: Implied > Realized volatility spread positive.
     - Exit rule: 50–60% credit capture or time stop before close.
   - Bot: Bot A — “PUT-Lite Intraday Premium Harvester.”

2) Covered Calls / Buy-Write (Index or Large Caps)
   - Edge: Consistent risk-adjusted outperformance versus buy-and-hold (BXM index).
   - Day-trading adaptation:
     - Sell 1-day or same-day calls against small intraday equity positions when IV is high but trend is neutral.
     - Partial overwrite (25–50% of shares).
     - Exit on 40–60% premium capture or before close.
   - Bot: Bot B — “Micro Buy-Write.”

3) Short-Vol Range Plays (Iron Condors / Strangles)
   - Edge: Profitable during calm, mean-reverting volatility regimes.
   - Day-trading adaptation:
     - 0DTE iron condors placed after morning range forms.
     - Use expected-move (EM) based wings ±1.2–1.5× EM.
     - Exit on 50% credit capture or stop before close.
   - Bot: Bot C — “Calm-Tape Condor.”

## III. Sector Focus

- Mega-Cap Tech (High Liquidity & Volatility): AAPL, NVDA, TSLA, MSFT, AMZN, META, GOOGL — tight spreads, predictable events, heavy flow.
- Broad Market Indices: SPX, SPY, QQQ (core for Bots A & C) — mature vol structures and abundant 0DTE liquidity.
- Energy & Healthcare: XLE, XLV, XLF, SMH — macro/earnings catalysts create event-driven IV edges.

## IV. Oversaturation → Opportunity

- Crowding Meter: Track IV rank, 0DTE imbalance, skew, and options flow.
- Contrarian Timing: Fade overbought option sides post-IV spikes.
- Post-Event Harvest: Sell premium after macro/earnings events when IV collapses.
- Regime Filter: Only sell volatility when realized < implied range.

## V. Automation Architecture

### Core Bots

| Bot   | Strategy          | Market Universe       | Edge Mechanism                  |
|-------|-------------------|-----------------------|---------------------------------|
| Bot A | PUT-Lite          | SPX / SPY             | Intraday VRP harvesting         |
| Bot B | Micro Buy-Write   | SPY / QQQ / Big 7     | Gamma rent (theta decay)        |
| Bot C | Calm-Tape Condor  | SPX                   | Regime-aware short volatility   |

### Shared Safety Systems

- Max loss per trade: e.g., $50
- Daily loss cap: e.g., 3R
- Volatility kill-switch: halt if realized range > EM
- Event blackout: CPI, FOMC, earnings days
- Auto-close all trades before market close

## VI. Tech Stack (Free to Start)

| Layer        | Tool / Service                           | Cost |
|--------------|-------------------------------------------|------|
| Broker       | Interactive Brokers (IBKR) Paper Account  | $0   |
| API Wrapper  | ib_insync (Python)                        | Free |
| Backtesting  | vectorbt / backtrader                     | Free |
| Server       | Localhost / Free Cloud VM                 | $0   |
| Database     | SQLite / Neon PostgreSQL                  | Free |
| Visualization| Streamlit / Grafana / TradingView overlay | Free |
| Alerts       | Telegram / Discord bots                   | Free |

Estimated monthly cost (after scaling): $5–$25.

## VII. Deployment Phases

### Phase 1: Setup & Connectivity

Install Trader Workstation (TWS) and connect IBKR Paper account. Enable API Access in TWS → Global Configuration → API → Settings → Enable Socket Clients.

Environment setup:

```bash
mkdir ibkr_bot && cd ibkr_bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install ib_insync pandas numpy fastapi uvicorn python-dotenv
```

Verify connection:

```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)
print("Connected:", ib.isConnected())
ib.disconnect()
```

### Phase 2: Market Data Pull

- Use `ib.reqMktData()` to stream underlying quotes.
- Pull option chains via `ib.reqSecDefOptParams()`.
- Save top tickers in `config/universe.json`.

### Phase 3: Bot Implementation

Folder structure:

```text
ibkr_bot/
 ├── bots/
 │   ├── bot_A_putlite.py
 │   ├── bot_B_buywrite.py
 │   └── bot_C_condor.py
 ├── config/
 │   └── universe.json
 ├── logs/
 └── main.py
```

Example PUT-Lite core logic (illustrative):

```python
from ib_insync import *
import datetime

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=2)

# Example SPY 0DTE Bull Put Spread
expiry = '2025-10-21'
short_put = Option('SPY', expiry, 450, 'P', 'SMART')
long_put  = Option('SPY', expiry, 445, 'P', 'SMART')
ib.qualifyContracts(short_put, long_put)

combo = Contract(
    symbol='SPY', secType='BAG', exchange='SMART', currency='USD',
    comboLegs=[
        ComboLeg(short_put.conId, 1, 'SELL', 'SMART'),
        ComboLeg(long_put.conId, 1, 'BUY', 'SMART')
    ]
)

order = LimitOrder('SELL', 1, 0.50)
trade = ib.placeOrder(combo, order)
print("Trade placed:", trade)
```

### Phase 4: Monitoring & Visualization

- Observe trades in TWS → Orders & Trades.
- Log JSON events to `logs/trades.log`.
- Optional: Send alerts via Telegram; plot signals on TradingView using PineScript webhooks.

### Phase 5: Paper-to-Live Ramp

- Backtest for 2–5 years (synthetic minute data).
- Paper trade for 4–8 weeks; record metrics.
- Confirm positive expectancy (Sharpe > 1).
- Switch to small-size live account (defined-risk spreads).
- Scale only after 20–30 consecutive compliant sessions.

## VIII. Data & Analytics Layer

- Market Data: IBKR live feeds; fallback to Barchart or Cboe delayed data.
- Volatility & Expected Move: computed locally from option mid-IV.
- Event Calendars: JSON feed (CPI, FOMC, jobs, OPEC).
- Trade Database: SQLite/Postgres with all signals, fills, and rule flags.
- Dashboard: Streamlit UI — live positions, P/L, IV rank, delta, EM vs. RV ratio.

## IX. Universe of Tracked Symbols

| Category               | Symbols                                         |
|------------------------|--------------------------------------------------|
| Indexes                | SPX, SPY, QQQ                                    |
| Mega-Cap Tech          | AAPL, MSFT, NVDA, TSLA, AMZN, META, GOOGL        |
| Sector ETFs            | XLF, XLE, XLV, SMH                               |
| Event-Driven (Selective)| AMD, NFLX, SHOP, BA, CRM, ORCL, COST, WMT       |

This set covers >70% of total US options volume daily.

## X. Risk Management

- Trade window: 10:30–13:30 ET
- Max loss per trade: $50
- Daily loss cap: $150
- Halt on:
  - Price exceeds 1.25× expected move
  - VIX spike > 3 pts
- Auto-close before 15:30 ET
- All spreads defined-risk

## XI. Next Action Plan

- ✅ Set up IBKR Paper Account and confirm API connection.
- ✅ Clone Project Folder & Install Dependencies.
- ✅ Run `connect_test.py` → verify connectivity.
- ✅ Load `universe.json` and start fetching SPY/QQQ chains.
- ✅ Deploy Bot A in paper mode for 5–10 sessions.
- 🔄 Add Bots B & C once Bot A metrics stabilize.
- 📊 Create simple Streamlit dashboard to track trades.
- 💰 Transition to small live account once edge confirmed.

## XII. References (Empirical Basis)

- Cboe Global Markets: PutWrite Index (PUT), BuyWrite Index (BXM), 0DTE Insights.
- Ibbotson & Callan Studies: Risk-adjusted Buy-Write performance (1988–2004).
- SSRN Research: Iron Condor profitability and volatility regime dependence.
- Tim de Silva (2025): Retail crowding in volatility trades.
- WSJ (2025): 100M+ daily options contracts — mega-cap tech dominance.

## XIII. Summary

The edge is not prediction — it’s discipline, risk control, and regime awareness. Each bot systematically harvests small, repeatable inefficiencies while enforcing strict filters and size limits. Your cost of entry is nearly zero, your infrastructure is enterprise-grade, and your growth path is controlled: Paper → Proof → Profit.

### Target architecture
```
ibkr_bots/
  bots/
    bot_A_putlite.py        # executable
    bot_B_buywrite.py       # implement
    bot_C_condor.py         # implement
  core/
    broker.py               # ib_insync wrapper (connect, qualify, place)
    options.py              # chains, IV, Greeks, expected move
    risk.py                 # per-trade, daily caps, kill-switches
    regime.py               # EM vs RV, IV rank, skew, breadth
    events.py               # CPI/FOMC/earnings calendar + API
    crowd.py                # flow proxies, volume leaders, skew tilt
    exec.py                 # order lifecycle (mid quotes, re-quote, timeouts)
    telemetry.py            # logging to DB, metrics, EOD report
  ml/
    features.py             # feature builders (intraday rolling, vol, flow)
    labels.py               # realized outcomes (PnL/greeks/price paths)
    models.py               # training/inference wrapper
    offline_backtest/       # minute-bar sim + option proxy
  config/
    universe.json
    strategy.yaml           # thresholds, risk, schedules per bot
  data/
  logs/
  dashboards/
    app.py                  # Streamlit
  scripts/
    run_paper.sh
    run_live.sh
```

