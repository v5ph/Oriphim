import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
from supabase import create_client, Client
import os
from typing import Dict, Any, List

# Page config
st.set_page_config(
    page_title="Oriphim - AI Trading Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f1f2e;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
    }
    .bot-status-running {
        color: #28a745;
        font-weight: bold;
    }
    .bot-status-stopped {
        color: #6c757d;
        font-weight: bold;
    }
    .bot-status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Supabase
@st.cache_resource
def init_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    return create_client(url, key)

def authenticate_user():
    """Handle user authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user = None

    if not st.session_state.authenticated:
        st.markdown("<div class='main-header'>🔥 Welcome to Oriphim</div>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            with st.form("signin_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In")
                
                if submitted:
                    # Placeholder authentication
                    if email and password:
                        st.session_state.authenticated = True
                        st.session_state.user = {
                            'email': email,
                            'id': 'user_123',
                            'plan': 'free'
                        }
                        st.rerun()
                    else:
                        st.error("Please enter email and password")
        
        with tab2:
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Sign Up")
                
                if submitted:
                    if password == confirm_password and email and password:
                        st.success("Account created! Please sign in.")
                    else:
                        st.error("Please check your inputs")
        
        return False
    
    return True

def main_dashboard():
    """Main dashboard interface"""
    supabase = init_supabase()
    
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("<div class='main-header'>🔥 Oriphim Dashboard</div>", unsafe_allow_html=True)
    with col2:
        st.metric("Plan", st.session_state.user['plan'].title())
    with col3:
        if st.button("Sign Out"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()

    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox("Select Page", [
            "🏠 Overview",
            "🤖 My Bots", 
            "📊 Live Trading",
            "📈 Analytics",
            "⚙️ Settings"
        ])
    
    # Main content based on selected page
    if page == "🏠 Overview":
        show_overview()
    elif page == "🤖 My Bots":
        show_my_bots()
    elif page == "📊 Live Trading":
        show_live_trading()
    elif page == "📈 Analytics":
        show_analytics()
    elif page == "⚙️ Settings":
        show_settings()

def show_overview():
    """Overview page"""
    st.header("Account Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total P&L", "$1,247.50", "12.3%")
    with col2:
        st.metric("Active Bots", "2", "0")
    with col3:
        st.metric("Trades Today", "14", "3")
    with col4:
        st.metric("Win Rate", "68%", "2%")
    
    # Recent activity
    st.subheader("Recent Activity")
    
    # Sample data
    activity_data = [
        {"Time": "14:32", "Bot": "PUT-Lite", "Action": "Opened position", "Symbol": "SPY", "P&L": "+$45.20"},
        {"Time": "14:15", "Bot": "Condor", "Action": "Closed position", "Symbol": "QQQ", "P&L": "+$23.50"},
        {"Time": "13:45", "Bot": "PUT-Lite", "Action": "Risk limit hit", "Symbol": "TSLA", "P&L": "-$15.00"},
        {"Time": "13:20", "Bot": "Buy-Write", "Action": "Started session", "Symbol": "SPY", "P&L": "$0.00"},
    ]
    
    df = pd.DataFrame(activity_data)
    st.dataframe(df, use_container_width=True)
    
    # Runner status
    st.subheader("Runner Status")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("🟢 **Runner Connected**\nLast heartbeat: 2 seconds ago")
    with col2:
        if st.button("Download Runner"):
            st.info("Runner download would start here")

def show_my_bots():
    """My bots configuration page"""
    st.header("My Trading Bots")
    
    # Bot templates
    st.subheader("Available Bot Templates")
    
    templates = [
        {
            "name": "PUT-Lite Harvester",
            "type": "putlite",
            "description": "Harvests volatility risk premium with 0DTE/1DTE put spreads",
            "risk": "Low-Medium",
            "avg_return": "2-4% monthly"
        },
        {
            "name": "Buy-Write Engine", 
            "type": "buywrite",
            "description": "Sells covered calls against stock positions",
            "risk": "Medium",
            "avg_return": "1-3% monthly"
        },
        {
            "name": "Condor Spreads",
            "type": "condor", 
            "description": "Iron condors in calm market conditions",
            "risk": "Medium",
            "avg_return": "3-6% monthly"
        },
        {
            "name": "Gamma Burst",
            "type": "gammaburst",
            "description": "Aggressive scalping during volatility spikes",
            "risk": "High",
            "avg_return": "5-15% monthly"
        }
    ]
    
    for template in templates:
        with st.expander(f"🤖 {template['name']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Description:** {template['description']}")
                st.write(f"**Risk Level:** {template['risk']}")
                st.write(f"**Avg Return:** {template['avg_return']}")
            
            with col2:
                st.subheader("Configuration")
                risk_per_trade = st.number_input("Risk per trade ($)", 10, 1000, 50, key=f"risk_{template['type']}")
                max_daily_loss = st.number_input("Max daily loss (%)", 1, 20, 5, key=f"daily_{template['type']}")
                
                symbols = st.multiselect(
                    "Symbols",
                    ["SPY", "QQQ", "IWM", "NVDA", "TSLA", "AAPL", "MSFT"],
                    ["SPY"],
                    key=f"symbols_{template['type']}"
                )
            
            with col3:
                st.subheader("Actions")
                mode = st.selectbox("Mode", ["Paper", "Live"], key=f"mode_{template['type']}")
                
                if st.session_state.user['plan'] == 'free' and mode == "Live":
                    st.warning("Live trading requires Pro plan")
                    if st.button("Upgrade to Pro", key=f"upgrade_{template['type']}"):
                        st.info("Stripe checkout would open here")
                else:
                    if st.button(f"Start {template['name']}", key=f"start_{template['type']}"):
                        st.success(f"Starting {template['name']} in {mode} mode...")
                        # This would call the start-run edge function

def show_live_trading():
    """Live trading page with real-time logs"""
    st.header("Live Trading")
    
    # Active runs
    st.subheader("Active Bot Runs")
    
    # Sample active runs
    runs_data = [
        {"Bot": "PUT-Lite", "Status": "Running", "Started": "10:30 AM", "P&L": "+$127.50", "Trades": 8},
        {"Bot": "Condor", "Status": "Running", "Started": "11:15 AM", "P&L": "+$45.20", "Trades": 3},
    ]
    
    for run in runs_data:
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.write(f"**{run['Bot']}**")
        with col2:
            st.markdown(f"<span class='bot-status-running'>{run['Status']}</span>", unsafe_allow_html=True)
        with col3:
            st.write(run['Started'])
        with col4:
            color = "green" if run['P&L'].startswith('+') else "red"
            st.markdown(f"<span style='color: {color}'>{run['P&L']}</span>", unsafe_allow_html=True)
        with col5:
            st.write(f"{run['Trades']} trades")
        with col6:
            if st.button("Stop", key=f"stop_{run['Bot']}"):
                st.warning(f"Stopping {run['Bot']}...")
    
    # Live logs
    st.subheader("Live Logs")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh logs", value=True)
    
    # Placeholder for live logs
    log_placeholder = st.empty()
    
    # Sample log data
    sample_logs = [
        "14:32:15 [PUT-Lite] INFO: Scanning for opportunities...",
        "14:32:20 [PUT-Lite] INFO: Found bull put spread setup on SPY",
        "14:32:25 [PUT-Lite] INFO: Expected move: $2.45, IV Rank: 67%",
        "14:32:30 [PUT-Lite] INFO: Placing order: Sell SPY 430P/425P @ $0.45 credit",
        "14:32:35 [PUT-Lite] INFO: Order filled: +$45.00",
        "14:32:40 [Condor] INFO: Managing existing QQQ position",
    ]
    
    with log_placeholder.container():
        for log in sample_logs[-10:]:  # Show last 10 logs
            st.text(log)
    
    if auto_refresh:
        # Simulate real-time updates
        time.sleep(1)
        st.rerun()

def show_analytics():
    """Analytics and performance page"""
    st.header("Performance Analytics")
    
    # Time period selector
    period = st.selectbox("Time Period", ["1 Day", "1 Week", "1 Month", "3 Months", "1 Year"])
    
    # Generate sample data
    dates = pd.date_range(start="2024-01-01", end="2024-10-28", freq="D")
    cumulative_pnl = (1 + pd.Series(np.random.normal(0.002, 0.02, len(dates)))).cumprod() - 1
    
    # P&L chart
    st.subheader("Cumulative P&L")
    fig = px.line(x=dates, y=cumulative_pnl * 10000, title="Portfolio Performance ($)")
    fig.update_layout(xaxis_title="Date", yaxis_title="Cumulative P&L ($)")
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Performance Metrics")
        metrics_data = {
            "Total Return": "12.47%",
            "Sharpe Ratio": "1.34",
            "Max Drawdown": "-3.2%",
            "Win Rate": "67.8%",
            "Avg Win": "$47.20",
            "Avg Loss": "-$23.10"
        }
        
        for metric, value in metrics_data.items():
            st.metric(metric, value)
    
    with col2:
        st.subheader("Bot Performance Comparison")
        
        bot_data = {
            "Bot": ["PUT-Lite", "Buy-Write", "Condor", "Gamma-Burst"],
            "Total P&L": [1247, 856, 432, -89],
            "Win Rate": [68, 72, 58, 45],
            "Trades": [156, 89, 67, 23]
        }
        
        df = pd.DataFrame(bot_data)
        st.dataframe(df, use_container_width=True)

def show_settings():
    """Settings page"""
    st.header("Settings")
    
    tab1, tab2, tab3 = st.tabs(["Account", "API Keys", "Billing"])
    
    with tab1:
        st.subheader("Account Settings")
        
        with st.form("account_form"):
            email = st.text_input("Email", value=st.session_state.user['email'])
            notifications = st.checkbox("Email notifications", value=True)
            risk_limit = st.number_input("Global daily loss limit ($)", 100, 10000, 1000)
            
            if st.form_submit_button("Update"):
                st.success("Settings updated!")
    
    with tab2:
        st.subheader("API Keys")
        st.write("Manage your Runner API keys")
        
        if st.button("Generate New API Key"):
            new_key = "ORX_" + "".join(random.choices(string.ascii_letters + string.digits, k=32))
            st.code(new_key)
            st.success("New API key generated! Copy and save it securely.")
        
        st.subheader("Active Keys")
        keys_data = [
            {"Name": "Default Runner", "Created": "2024-10-01", "Last Used": "2 minutes ago", "Status": "Active"},
            {"Name": "Backup Runner", "Created": "2024-09-15", "Last Used": "3 days ago", "Status": "Active"}
        ]
        
        df = pd.DataFrame(keys_data)
        st.dataframe(df, use_container_width=True)
    
    with tab3:
        st.subheader("Billing")
        
        current_plan = st.session_state.user['plan']
        st.write(f"**Current Plan:** {current_plan.title()}")
        
        if current_plan == 'free':
            st.info("**Free Plan Limits:**\n- Paper trading only\n- 2 active bots\n- Basic analytics")
            
            if st.button("Upgrade to Pro - $29/month"):
                st.info("Stripe checkout would open here")
        else:
            st.success("**Pro Plan Benefits:**\n- Live trading enabled\n- Unlimited bots\n- Advanced analytics\n- Priority support")
            
            if st.button("Manage Subscription"):
                st.info("Stripe customer portal would open here")

# Main app execution
if __name__ == "__main__":
    import numpy as np
    import random
    import string
    
    if authenticate_user():
        main_dashboard()