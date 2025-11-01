# Oriphim Runner-First Data Architecture

## 🎯 Core Philosophy: Cost-First, Runner-First

**We are NOT building a market data vendor. We are building an automation control plane.**

The source of truth is **local** (Runner), not cloud. Market data flows through the user's broker → their Runner → minimal events to cloud.

## 🏗️ Data Flow Architecture

```
[User's IBKR/Tradier/TD] 
       ↓ (live market data - FREE to user)
[Oriphim Runner on User PC]
       ↓ (tiny JSON events ONLY)
[Supabase: runs, logs, status]
       ↓ (realtime subscriptions)
[React Dashboard] → rich charts from sparse events
```

## ✅ What Goes to Cloud (Event-Driven)

### 1. Trading Session Events
- **runs**: session lifecycle (start, running, stopped, error)
- **Final P/L**: `+$23.40 on run 91`
- **Entry/Exit conditions**: `{"em": 3.4, "ivr": 62, "regime": "chop"}`
- **Sparse P/L snapshots**: 5-10 points per run, not tick-by-tick

### 2. Human-Readable Logs
- **run_logs**: `"Bot A skipped because EM/RR < 1.1"`
- **AI rationale**: `"Detected volatility compression, ideal for PUT-Lite"`
- **Warnings**: `"IBKR connection lost, retrying..."`

### 3. Runner Status (Heartbeat)
- **runner_status**: connection state, broker status, active bots
- **System info**: CPU, memory (for health monitoring)

### 4. Position Summaries (Normalized)
- **positions**: small, derived fill data
- **Contract details**: `{"strike": 450, "exp": "2025-11-01", "type": "C"}`
- **Entry/exit rationale**: not raw Greeks

## ❌ What NEVER Goes to Cloud

### 1. Raw Market Data
- ❌ Per-quote inserts
- ❌ Full options chains every 5 seconds  
- ❌ Tick-level OHLCV writes
- ❌ Real-time Greeks for 500 strikes

### 2. Heavy Computation Results
- ❌ Full IV surfaces
- ❌ Complete expected move calculations
- ❌ Regime classification raw inputs

All heavy work stays on Runner. Cloud only gets the **decision**, not the **data**.

## 🎛️ Dashboard Rendering Strategy

### Real-time Subscriptions (4 channels max)
1. **`runner_status`** → "Runner Connected" indicator
2. **`runs`** → update active/last runs  
3. **`run_logs`** → show what bot just did
4. **`positions`** → current positions (optional)

### Charts from Sparse Events
- **P&L Chart**: Built from `pnl_snapshots` (5-10 points per run)
- **Market Chart**: Simulated frontend data OR local Runner fetch
- **"Live" feel**: Generated from sparse real events, not fake streams

## 💾 Database Schema (Updated)

### Core Tables (Already Implemented)
```sql
-- Trading automation state
bots                 -- Bot configurations
runs                 -- Session lifecycle + derived analytics
  ├─ entry_conditions  -- {"em": 3.4, "ivr": 62}
  ├─ pnl_snapshots     -- [{"ts": "10:30", "pnl": 12.40}]
  └─ market_regime     -- {"vix": 18.2, "breadth": "neutral"}

run_logs            -- Human-readable events
positions           -- Normalized fills (NOT full chains)
runner_status       -- Live connection + heartbeat
api_keys           -- Runner authentication
```

### What We DON'T Store
```sql
-- ❌ These tables do NOT exist:
market_data        -- No OHLCV time series
options_data       -- No full chain snapshots  
greeks_history     -- No tick-by-tick Greeks
```

## 🔄 Real-time Subscriptions (Configured)

```sql
CREATE PUBLICATION supabase_realtime FOR TABLE 
  runner_status,  -- Live connection status
  runs,          -- Trading session lifecycle  
  run_logs,      -- Human-readable events
  positions;     -- Small, normalized fills
```

**Critical**: No market data tables in realtime pub. Keeps costs low.

## 🎨 Frontend Implementation

### CandlestickChart 
- **Current**: Simulated market data
- **Production Option A**: Keep simulated (works great for MVP)
- **Production Option B**: Runner fetches on-demand → display → not saved

### PnLChart
- **Data Source**: `runs.pnl_snapshots` (sparse, event-driven)
- **Intraday**: Uses Runner's 5-10 snapshots per session
- **Daily/Weekly**: Aggregated run totals

### Runner Status Indicator
- **Data Source**: `runner_status.last_heartbeat`
- **Real-time**: Updates via Supabase subscription
- **Shows**: Connected, broker status, active bots

## 💰 Cost Benefits

### Why This Works
1. **No Data Feed Costs**: User's broker data is free to them, free to us
2. **Low Postgres Writes**: ~10 events per run vs 10,000+ ticks
3. **Minimal Realtime**: 4 tables vs hundreds of market data streams
4. **Storage Efficient**: Decision logs vs raw time series

### Compliance Clean
- Not reselling exchange data
- Not redistributing broker feeds  
- User owns their data flow

## 🚀 Implementation Status

### ✅ Completed
- [x] Runner-First database schema
- [x] Event-driven table structure
- [x] Supabase realtime for events only
- [x] TypeScript types for new tables
- [x] P&L Chart using sparse snapshots
- [x] Simulated market chart (cost-free)

### 🔄 Next Steps
1. **Runner Integration**: Connect Runner to push events
2. **Real-time Dashboard**: Subscribe to runner_status, runs, logs
3. **Position Tracking**: Show live positions from normalized data

## 📋 Rules to Enforce

### Development Guidelines
1. **Dashboard must NEVER depend on storing full market data in Supabase**
2. **Runner must NEVER push raw ticks/full chains to Supabase**
3. **Supabase is for state, logs, and P/L summaries - NOT market time-series**
4. **If dashboard needs "real" bars → frontend simulation OR on-demand fetch**

### Data Validation
- Max 10 P&L snapshots per run
- Max 1KB per run_log entry
- Max 100 events per bot per day
- Runner heartbeat every 30 seconds max

This architecture ensures we **never pay for data costs** while providing rich, real-time trading automation experience.