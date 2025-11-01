# Oriphim MVP - AI Trading SaaS Platform

🔥 **Transform your IBKR bots into a scalable SaaS trading automation platform**

## Overview

Oriphim is a complete SaaS solution that transforms the existing IBKR bot repository into a cloud-managed trading automation platform. Users sign up, download a lightweight Runner app, connect their broker, and manage AI-powered trading bots through a web dashboard - all while keeping their trading data and credentials completely private on their local machine.

## 🏗️ Architecture

### Two-Part System

**Oriphim Cloud** (Web Control Plane)
- Supabase backend with auth, billing, real-time logs
- Streamlit dashboard for bot management
- Stripe billing integration
- Edge functions for bot orchestration

**Oriphim Runner** (Local Desktop Agent)  
- Executes bots locally using existing IBKR code
- Connects securely to user's broker API
- Streams logs to Cloud via encrypted WebSocket
- Keeps all sensitive data on user's machine

## 🚀 Quick Start

### 1. Deploy Oriphim Cloud

```bash
# Deploy to Supabase
cd cloud/supabase
supabase init
supabase db push
supabase functions deploy

# Start dashboard
cd ../app
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### 2. Setup Runner

```bash
cd runner
pip install -r requirements.txt
python main.py
```

### 3. Environment Variables

```bash
# Runner (.env)
ORIPHIM_API_KEY=your_api_key_from_dashboard
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key

# Cloud (Environment Variables)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## 🎯 User Journey

1. **Sign Up** → User creates account at Oriphim dashboard
2. **Download** → Gets Runner installer and API key
3. **Connect** → Runner authenticates and connects to broker
4. **Configure** → Web dashboard to setup bot parameters
5. **Execute** → Bots run locally, stream logs to dashboard
6. **Monitor** → Real-time P&L and trade logs in browser
7. **Scale** → Upgrade to Pro for live trading

## 📁 Project Structure

```
oriphim/
├── cloud/                     # SaaS Backend
│   ├── supabase/
│   │   ├── sql/schema.sql     # Database schema + RLS
│   │   └── functions/         # Edge functions
│   └── app/streamlit_app.py   # Web dashboard
│
├── runner/                    # Desktop Agent
│   ├── main.py               # Main Runner application
│   └── requirements.txt      # Python dependencies
│
├── ibkr_bots/                # Enhanced Bot Engine
│   ├── bots/
│   │   ├── bot_interface.py  # SaaS callable interface
│   │   └── bot_A_putlite_refactored.py
│   ├── ml/                   # AI Assistant (Local)
│   │   ├── __init__.py       # ML interface
│   │   ├── config/ml_defaults.yaml
│   │   └── models/           # Local ML models
│   └── core/                 # Existing bot infrastructure
│
└── AGENTS.md                 # Project specification
```

## 🤖 Available Bots

| Bot | Strategy | Risk Level | Description |
|-----|----------|------------|-------------|
| **PUT-Lite** | Bull Put Spreads | Low-Medium | Harvests volatility premium with 0DTE/1DTE puts |
| **Buy-Write** | Covered Calls | Medium | Sells calls against stock positions |
| **Condor** | Iron Condors | Medium | Range-bound strategies in calm markets |
| **Gamma-Burst** | Vol Scalping | High | Aggressive strategies during vol spikes |

## 🧠 AI Features (Local ML)

- **Regime Detection**: Trend/Chop/Event classification
- **Expected Move**: Intraday volatility forecasting  
- **Trade Scoring**: P(win) probability for setups
- **Execution Timing**: Optimal entry timing
- **Risk Guard**: Anomaly detection and circuit breakers

*All ML runs locally using broker data - zero external data costs.*

## 💰 Business Model

| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0/month | Paper trading, 2 bots, basic analytics |
| **Pro** | $29/month | Live trading, unlimited bots, AI assist, priority support |

## 🔒 Security

- **Broker credentials** stay on user's machine only
- **TLS encryption** for all Runner ↔ Cloud communication  
- **Row-level security** ensures data isolation
- **Revocable device tokens** for Runner authentication
- **No PII or financial data** stored in cloud

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Supabase (Postgres + Auth + Realtime) | Cloud control plane |
| Frontend | Streamlit | Web dashboard (MVP) |
| Runner | Python + PyInstaller | Local bot execution |
| Broker API | ib_insync, Tradier REST | Market data + orders |
| Billing | Stripe | Subscription management |
| ML | LightGBM, scikit-learn | Local AI models |

## 📊 Operating Costs

- **Supabase**: Free tier → $25/month
- **Stripe**: 2.9% + $0.30/transaction  
- **Per-user cost**: ~$0.10/month
- **Total infrastructure**: <$50/month

## 🚦 Development Phases

### ✅ Phase 1: Core Infrastructure
- [x] Supabase schema and edge functions
- [x] Bot interface refactoring  
- [x] Runner authentication system

### ✅ Phase 2: SaaS Integration  
- [x] Streamlit dashboard
- [x] Real-time log streaming
- [x] ML framework structure

### 🔄 Phase 3: Production Ready
- [ ] Stripe billing integration
- [ ] Runner installers (Windows/Mac/Linux)
- [ ] End-to-end testing

### 🔄 Phase 4: Scale & Polish
- [ ] Advanced ML models
- [ ] Mobile-responsive dashboard
- [ ] Multi-broker support

## 🧪 Testing

```bash
# Test Runner authentication
cd runner
python -c "from main import authenticate; print(authenticate('test_key'))"

# Test bot execution
python -c "from ibkr_bots.bots.bot_interface import run_bot; list(run_bot('putlite', {}, 'paper'))"

# Test edge functions
curl -X POST https://your-project.supabase.co/functions/v1/start-run \
  -H "Authorization: Bearer your_jwt" \
  -d '{"bot_id": "123", "mode": "paper"}'
```

## 📈 Success Metrics

- **User Activation**: Runner download → first paper trade
- **Conversion**: Free → Pro upgrade rate
- **Retention**: Monthly active users
- **Performance**: Bot win rates and user satisfaction

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔥 Get Started

Ready to transform your trading bots into a SaaS platform?

1. **Clone this repo**
2. **Follow the Quick Start guide**
3. **Deploy to Supabase**
4. **Start building your trading empire**

---

*Built with ❤️ for algorithmic traders who want to scale their strategies.*