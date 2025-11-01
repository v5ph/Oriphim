#!/usr/bin/env python3
"""
IBKR Options Bot Dashboard

Real-time monitoring dashboard for the options trading bot system.
Shows live positions, P&L, filter status, and system controls.
"""

import streamlit as st
import pandas as pd
import json
import os
import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import logging

# Configure logging for dashboard
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dashboard')

# Page configuration
st.set_page_config(
    page_title="IBKR Options Bot Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
}
.status-green { color: #10b981; font-weight: bold; }
.status-red { color: #ef4444; font-weight: bold; }
.status-yellow { color: #f59e0b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=30)  # Cache for 30 seconds
def load_daily_summary():
    """Load today's trading summary from database"""
    db_path = "data/trades.db"
    
    if not os.path.exists(db_path):
        return {
            'decisions': {},
            'fills': {'count': 0, 'total_quantity': 0, 'avg_price': 0},
            'total_pnl': 0.0,
            'symbols_traded': []
        }
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        
        # Get decision counts
        cursor.execute('''
            SELECT decision, COUNT(*) as count
            FROM decisions 
            WHERE created_date = ?
            GROUP BY decision
        ''', (today,))
        
        decisions = {row['decision']: row['count'] for row in cursor.fetchall()}
        
        # Get fill summary
        cursor.execute('''
            SELECT COUNT(*) as fill_count, 
                   SUM(fill_quantity) as total_quantity,
                   AVG(fill_price) as avg_price
            FROM fills 
            WHERE created_date = ?
        ''', (today,))
        
        fill_data = cursor.fetchone()
        
        # Get P&L summary (simplified)
        cursor.execute('''
            SELECT symbol, SUM(total_pnl) as total_pnl
            FROM pnl_snapshots 
            WHERE created_date = ?
            GROUP BY symbol
        ''', (today,))
        
        pnl_by_symbol = {row['symbol']: row['total_pnl'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'decisions': decisions,
            'fills': {
                'count': fill_data['fill_count'] or 0,
                'total_quantity': fill_data['total_quantity'] or 0,
                'avg_price': fill_data['avg_price'] or 0
            },
            'pnl_by_symbol': pnl_by_symbol,
            'total_pnl': sum(pnl_by_symbol.values()),
            'symbols_traded': list(pnl_by_symbol.keys())
        }
        
    except Exception as e:
        logger.error(f"Error loading daily summary: {e}")
        return {'error': str(e)}


@st.cache_data(ttl=10)  # Cache for 10 seconds
def load_recent_decisions(limit: int = 20):
    """Load recent trading decisions"""
    db_path = "data/trades.db"
    
    if not os.path.exists(db_path):
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, symbol, strategy, decision, reason
            FROM decisions 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        decisions = []
        for row in cursor.fetchall():
            decisions.append({
                'timestamp': row['timestamp'],
                'symbol': row['symbol'],
                'strategy': row['strategy'],
                'decision': row['decision'],
                'reason': row['reason']
            })
        
        conn.close()
        return decisions
        
    except Exception as e:
        logger.error(f"Error loading recent decisions: {e}")
        return []


def load_risk_state():
    """Load current risk management state"""
    risk_file = "data/risk_state.json"
    
    if not os.path.exists(risk_file):
        return {
            'trading_allowed': True,
            'daily_pnl': 0.0,
            'positions': '0/3',
            'trades_today': 0,
            'is_halted': False,
            'halt_reason': ''
        }
    
    try:
        with open(risk_file, 'r') as f:
            data = json.load(f)
        
        today_str = date.today().isoformat()
        today_data = data.get(today_str, {})
        
        return {
            'trading_allowed': not today_data.get('is_halted', False),
            'daily_pnl': today_data.get('daily_pnl', 0.0),
            'positions': f"{today_data.get('current_positions', 0)}/3",
            'trades_today': today_data.get('trades_today', 0),
            'is_halted': today_data.get('is_halted', False),
            'halt_reason': today_data.get('halt_reason', '')
        }
        
    except Exception as e:
        logger.error(f"Error loading risk state: {e}")
        return {'error': str(e)}


def check_connection_status():
    """Check if bot appears to be running"""
    # Simple check - look for recent log activity
    log_file = "logs/bot_A.log"
    
    if not os.path.exists(log_file):
        return False, "No log file found"
    
    try:
        # Check if log has been updated recently (within 5 minutes)
        last_modified = datetime.fromtimestamp(os.path.getmtime(log_file))
        time_diff = datetime.now() - last_modified
        
        if time_diff.total_seconds() < 300:  # 5 minutes
            return True, f"Last activity: {last_modified.strftime('%H:%M:%S')}"
        else:
            return False, f"Last activity: {last_modified.strftime('%H:%M:%S')} ({int(time_diff.total_seconds()/60)} min ago)"
            
    except Exception as e:
        return False, f"Error checking status: {e}"


def emergency_halt():
    """Create emergency halt flag"""
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/emergency_halt.flag", 'w') as f:
            f.write(f"{datetime.now().isoformat()}: Emergency halt from dashboard\n")
        return True
    except Exception as e:
        logger.error(f"Error creating halt flag: {e}")
        return False


def remove_halt():
    """Remove emergency halt flag"""
    try:
        halt_file = "data/emergency_halt.flag"
        if os.path.exists(halt_file):
            os.remove(halt_file)
        return True
    except Exception as e:
        logger.error(f"Error removing halt flag: {e}")
        return False


def main():
    """Main dashboard function"""
    
    # Title and header
    st.title("📊 IBKR Options Bot Dashboard")
    st.markdown("Real-time monitoring for automated options trading")
    
    # Sidebar controls
    st.sidebar.header("🎛️ Controls")
    
    # Emergency controls
    st.sidebar.subheader("Emergency Controls")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🚨 HALT", type="secondary", help="Emergency stop all trading"):
            if emergency_halt():
                st.sidebar.success("Emergency halt activated")
            else:
                st.sidebar.error("Failed to activate halt")
    
    with col2:
        if st.button("▶️ RESUME", help="Resume trading"):
            if remove_halt():
                st.sidebar.success("Halt removed")
            else:
                st.sidebar.error("Failed to remove halt")
    
    # Refresh controls
    st.sidebar.subheader("Refresh")
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=True)
    
    if st.sidebar.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()
    
    # Auto-refresh logic
    if auto_refresh:
        import time
        time.sleep(30)
        st.rerun()
    
    # Main content area
    col1, col2, col3, col4 = st.columns(4)
    
    # Connection status
    with col1:
        is_connected, status_msg = check_connection_status()
        status_class = "status-green" if is_connected else "status-red"
        status_text = "🟢 Connected" if is_connected else "🔴 Disconnected"
        
        st.markdown(f"""
        <div class="metric-card">
        <h4>Connection Status</h4>
        <p class="{status_class}">{status_text}</p>
        <small>{status_msg}</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Trading mode
    with col2:
        mode = os.getenv('MODE', 'paper').upper()
        mode_class = "status-yellow" if mode == "PAPER" else "status-red"
        mode_icon = "📝" if mode == "PAPER" else "💰"
        
        st.markdown(f"""
        <div class="metric-card">
        <h4>Trading Mode</h4>
        <p class="{mode_class}">{mode_icon} {mode}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Load risk state
    risk_state = load_risk_state()
    
    # Risk status
    with col3:
        is_halted = risk_state.get('is_halted', False)
        halt_class = "status-red" if is_halted else "status-green"
        halt_text = "🚨 HALTED" if is_halted else "✅ Active"
        
        st.markdown(f"""
        <div class="metric-card">
        <h4>Risk Status</h4>
        <p class="{halt_class}">{halt_text}</p>
        <small>Positions: {risk_state.get('positions', 'N/A')}</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Daily P&L
    with col4:
        daily_pnl = risk_state.get('daily_pnl', 0.0)
        pnl_class = "status-green" if daily_pnl >= 0 else "status-red"
        pnl_icon = "📈" if daily_pnl >= 0 else "📉"
        
        st.markdown(f"""
        <div class="metric-card">
        <h4>Daily P&L</h4>
        <p class="{pnl_class}">{pnl_icon} ${daily_pnl:.2f}</p>
        <small>Trades: {risk_state.get('trades_today', 0)}</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Today's Activity", "📊 Performance", "⚙️ System Status", "📖 Logs"])
    
    # Today's Activity Tab
    with tab1:
        st.header("Today's Trading Activity")
        
        # Load daily summary
        summary = load_daily_summary()
        
        if 'error' in summary:
            st.error(f"Error loading data: {summary['error']}")
        else:
            # Decisions summary
            st.subheader("Trading Decisions")
            decisions_df = pd.DataFrame([
                {'Decision': k, 'Count': v} 
                for k, v in summary.get('decisions', {}).items()
            ])
            
            if not decisions_df.empty:
                st.dataframe(decisions_df, hide_index=True)
            else:
                st.info("No decisions recorded today")
            
            # Recent decisions detail
            st.subheader("Recent Decisions")
            recent_decisions = load_recent_decisions(10)
            
            if recent_decisions:
                decisions_detail_df = pd.DataFrame(recent_decisions)
                decisions_detail_df['timestamp'] = pd.to_datetime(decisions_detail_df['timestamp'])
                decisions_detail_df = decisions_detail_df.sort_values('timestamp', ascending=False)
                
                st.dataframe(
                    decisions_detail_df,
                    column_config={
                        'timestamp': st.column_config.DatetimeColumn(
                            'Time',
                            format='HH:mm:ss'
                        ),
                        'symbol': 'Symbol',
                        'strategy': 'Bot',
                        'decision': 'Decision',
                        'reason': 'Reason'
                    },
                    hide_index=True
                )
            else:
                st.info("No recent decisions found")
    
    # Performance Tab
    with tab2:
        st.header("Performance Metrics")
        
        summary = load_daily_summary()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Today's Summary")
            st.metric("Total P&L", f"${summary.get('total_pnl', 0):.2f}")
            st.metric("Fills", summary.get('fills', {}).get('count', 0))
            st.metric("Avg Fill Price", f"${summary.get('fills', {}).get('avg_price', 0):.3f}")
        
        with col2:
            st.subheader("Symbols Traded")
            symbols = summary.get('symbols_traded', [])
            if symbols:
                for symbol in symbols:
                    pnl = summary.get('pnl_by_symbol', {}).get(symbol, 0)
                    st.write(f"**{symbol}**: ${pnl:.2f}")
            else:
                st.info("No symbols traded today")
    
    # System Status Tab
    with tab3:
        st.header("System Status")
        
        # Risk management status
        st.subheader("Risk Management")
        risk_state = load_risk_state()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Trading Allowed**: {risk_state.get('trading_allowed', 'Unknown')}")
            st.write(f"**Daily P&L**: ${risk_state.get('daily_pnl', 0):.2f}")
            st.write(f"**Open Positions**: {risk_state.get('positions', 'N/A')}")
        
        with col2:
            st.write(f"**Trades Today**: {risk_state.get('trades_today', 0)}")
            st.write(f"**Is Halted**: {risk_state.get('is_halted', False)}")
            if risk_state.get('halt_reason'):
                st.write(f"**Halt Reason**: {risk_state['halt_reason']}")
        
        # File system status
        st.subheader("File System")
        
        files_to_check = [
            ("Config File", "config/strategy.yaml"),
            ("Risk State", "data/risk_state.json"),
            ("Trade Database", "data/trades.db"),
            ("Bot A Log", "logs/bot_A.log"),
            ("Halt Flag", "data/emergency_halt.flag")
        ]
        
        for name, path in files_to_check:
            exists = os.path.exists(path)
            status_icon = "✅" if exists else "❌"
            st.write(f"{status_icon} **{name}**: {path}")
    
    # Logs Tab
    with tab4:
        st.header("Recent Logs")
        
        log_file = "logs/bot_A.log"
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                # Show last 50 lines
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                log_text = ''.join(recent_lines)
                
                st.text_area(
                    "Bot A Logs (Last 50 lines)",
                    log_text,
                    height=400,
                    disabled=True
                )
                
            except Exception as e:
                st.error(f"Error reading log file: {e}")
        else:
            st.info("No log file found")
    
    # Footer
    st.markdown("---")
    st.markdown(f"**Dashboard last updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("**⚠️ Trading involves risk. Monitor positions carefully.**")


if __name__ == "__main__":
    main()