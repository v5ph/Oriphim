# Deployment Guide - Oriphim MVP

Complete step-by-step guide to deploy Oriphim from development to production.

## 🎯 Prerequisites

- Supabase account
- Stripe account (for billing)
- Domain name (optional)
- Python 3.9+ installed

## 📋 Phase 1: Supabase Backend Setup

### 1.1 Create Supabase Project

```bash
# Install Supabase CLI
npm install -g supabase

# Create new project at supabase.com
# Note your project URL and anon key
```

### 1.2 Initialize Database

```bash
cd cloud/supabase
supabase init
supabase link --project-ref YOUR_PROJECT_REF

# Deploy schema
supabase db push
```

### 1.3 Deploy Edge Functions

```bash
# Deploy all functions
supabase functions deploy start-run
supabase functions deploy stop-run  
supabase functions deploy exchange-device-token
supabase functions deploy stripe-webhook

# Set environment variables
supabase secrets set STRIPE_SECRET_KEY=sk_test_...
supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_...
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

### 1.4 Configure Row Level Security

```sql
-- Enable RLS on all tables (already in schema.sql)
-- Test with a user account
```

## 📋 Phase 2: Stripe Billing Setup

### 2.1 Create Stripe Products

```bash
# Using Stripe CLI
stripe products create --name="Oriphim Pro" --description="Pro trading plan"

# Create price
stripe prices create \
  --product=prod_xxx \
  --unit-amount=2900 \
  --currency=usd \
  --recurring-interval=month \
  --lookup-key=pro
```

### 2.2 Setup Webhooks

```bash
# Add webhook endpoint in Stripe Dashboard:
# URL: https://your-project.supabase.co/functions/v1/stripe-webhook
# Events: customer.subscription.*, invoice.payment_*
```

## 📋 Phase 3: Dashboard Deployment

### 3.1 Deploy Streamlit App

```bash
cd cloud/app

# Install dependencies
pip install -r requirements.txt

# Create requirements.txt
echo "streamlit>=1.28.0
supabase>=2.0.0
plotly>=5.17.0
pandas>=2.0.0" > requirements.txt

# Deploy to Streamlit Cloud or other platform
# Set environment variables:
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=eyJ...
```

### 3.2 Alternative: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY streamlit_app.py .
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t oriphim-dashboard .
docker run -p 8501:8501 -e SUPABASE_URL=... oriphim-dashboard
```

## 📋 Phase 4: Runner Distribution

### 4.1 Create Executable

```bash
cd runner

# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed --icon=assets/oriphim.ico main.py

# Test
./dist/main
```

### 4.2 Create Installers

**Windows (NSIS)**
```nsis
# installer.nsi
!define APPNAME "Oriphim Runner"
!define VERSION "1.0.0"

OutFile "OriphimRunnerSetup.exe"
InstallDir "$PROGRAMFILES\Oriphim"

Section "Main"
    SetOutPath $INSTDIR
    File "dist\main.exe"
    CreateShortcut "$DESKTOP\Oriphim Runner.lnk" "$INSTDIR\main.exe"
SectionEnd
```

**macOS**
```bash
# Create .app bundle
py2app --windowed main.py

# Create DMG
hdiutil create -volname "Oriphim Runner" -srcfolder dist/main.app -ov OriphimRunner.dmg
```

### 4.3 Auto-Update System (Future)

```python
# In runner/updater.py
import requests
import os

def check_for_updates():
    response = requests.get("https://api.oriphim.com/version")
    latest_version = response.json()["version"]
    current_version = "1.0.0"  # From config
    
    if latest_version > current_version:
        download_update(latest_version)
```

## 📋 Phase 5: Domain & SSL Setup

### 5.1 Custom Domain (Optional)

```bash
# Point your domain to Streamlit/hosting provider
# Example DNS records:
# dashboard.oriphim.com -> streamlit-app-url
# api.oriphim.com -> supabase-project-url
```

### 5.2 SSL Certificate

```bash
# If using custom hosting, setup SSL
# Most platforms (Streamlit Cloud, Vercel, etc.) provide SSL automatically
```

## 📋 Phase 6: Monitoring & Analytics

### 6.1 Supabase Analytics

```sql
-- Add analytics views
CREATE VIEW daily_signups AS
SELECT DATE(created_at) as date, COUNT(*) as signups
FROM auth.users
GROUP BY DATE(created_at);

CREATE VIEW active_runners AS  
SELECT COUNT(DISTINCT user_id) as active_count
FROM api_keys 
WHERE last_used_at > NOW() - INTERVAL '1 hour';
```

### 6.2 Error Monitoring

```python
# Add to runner/main.py
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

## 📋 Phase 7: Testing & Validation

### 7.1 End-to-End Testing

```bash
# Test complete user journey
1. Sign up at dashboard
2. Download Runner
3. Connect with API key
4. Start paper bot
5. View real-time logs
6. Upgrade to Pro
7. Run live bot
```

### 7.2 Load Testing

```python
# Test concurrent users
import asyncio
import aiohttp

async def simulate_user():
    # Simulate Runner connection + bot execution
    pass

async def load_test():
    tasks = [simulate_user() for _ in range(100)]
    await asyncio.gather(*tasks)
```

## 🔧 Environment Variables Summary

### Supabase (Edge Functions)
```bash
SUPABASE_URL=https://your-project.supabase.co  
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Dashboard (Streamlit)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
```

### Runner (User's Machine)
```bash
ORIPHIM_API_KEY=user_api_key_from_dashboard
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
```

## 🳎 Go-Live Checklist

- [ ] Database schema deployed
- [ ] Edge functions working
- [ ] Stripe webhook receiving events
- [ ] Dashboard accessible
- [ ] Runner executable created
- [ ] End-to-end test passed
- [ ] SSL certificates active
- [ ] Monitoring setup
- [ ] Terms of Service + Privacy Policy
- [ ] Support documentation

## 🚨 Security Checklist

- [ ] RLS policies tested
- [ ] JWT tokens validated
- [ ] API keys revocable
- [ ] Webhook signatures verified
- [ ] HTTPS enforced
- [ ] Rate limiting enabled
- [ ] Input validation active
- [ ] Logs sanitized

## 📈 Post-Launch

### Metrics to Track
- User signups & activation rate
- Runner downloads & connections
- Bot runs (paper vs live)
- Free → Pro conversion rate
- Support tickets & common issues
- Revenue & churn

### Optimization
- A/B testing for conversion
- Performance monitoring
- User feedback collection
- Feature usage analytics

---

🔥 **You're ready to launch Oriphim!** Follow this guide step-by-step and you'll have a fully functional SaaS trading platform.