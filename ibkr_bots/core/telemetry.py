"""
Telemetry and logging module for trade tracking and performance analysis.
Handles SQLite database operations and EOD reporting.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from dataclasses import dataclass, asdict
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class TradeDecision:
    """Record of a trading decision"""
    timestamp: str
    symbol: str
    strategy: str  # 'bot_A', 'bot_B', 'bot_C'
    decision: str  # 'ENTER', 'EXIT', 'SKIP', 'HOLD'
    reason: str
    filters: Dict[str, Any]
    market_data: Dict[str, Any]
    trade_id: Optional[str] = None


@dataclass
class OrderRecord:
    """Record of an order placement"""
    timestamp: str
    order_id: int
    symbol: str
    side: str  # 'BUY', 'SELL'
    quantity: int
    limit_price: float
    order_type: str
    attempt: int
    status: str


@dataclass
class FillRecord:
    """Record of an order fill"""
    timestamp: str
    order_id: int
    symbol: str
    fill_price: float
    fill_quantity: int
    commission: Optional[float] = None


@dataclass
class PnLSnapshot:
    """Point-in-time P&L snapshot"""
    timestamp: str
    symbol: str
    position_id: str
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    underlying_price: float
    delta: Optional[float] = None


class TelemetryManager:
    """Centralized logging and database management for trading activity"""
    
    def __init__(self):
        self.db_path = "data/trades.db"
        self.log_path = "logs"
        self._ensure_directories()
        self._init_database()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Decisions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS decisions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        strategy TEXT NOT NULL,
                        decision TEXT NOT NULL,
                        reason TEXT,
                        filters TEXT,  -- JSON
                        market_data TEXT,  -- JSON
                        trade_id TEXT,
                        created_date TEXT DEFAULT (date('now'))
                    )
                ''')
                
                # Orders table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        order_id INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        limit_price REAL NOT NULL,
                        order_type TEXT NOT NULL,
                        attempt INTEGER DEFAULT 1,
                        status TEXT NOT NULL,
                        created_date TEXT DEFAULT (date('now'))
                    )
                ''')
                
                # Fills table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fills (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        order_id INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        fill_price REAL NOT NULL,
                        fill_quantity INTEGER NOT NULL,
                        commission REAL,
                        created_date TEXT DEFAULT (date('now'))
                    )
                ''')
                
                # PnL snapshots table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS pnl_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        position_id TEXT NOT NULL,
                        unrealized_pnl REAL NOT NULL,
                        realized_pnl REAL NOT NULL,
                        total_pnl REAL NOT NULL,
                        underlying_price REAL NOT NULL,
                        delta REAL,
                        created_date TEXT DEFAULT (date('now'))
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_date ON decisions(created_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_symbol ON decisions(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(created_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_fills_date ON fills(created_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pnl_date ON pnl_snapshots(created_date)')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def log_decision(self, decision_data: Dict[str, Any]):
        """
        Log a trading decision
        
        Args:
            decision_data: Dictionary containing decision details
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO decisions 
                    (timestamp, symbol, strategy, decision, reason, filters, market_data, trade_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    decision_data.get('timestamp', datetime.now().isoformat()),
                    decision_data['symbol'],
                    decision_data['strategy'],
                    decision_data['decision'],
                    decision_data.get('reason', ''),
                    json.dumps(decision_data.get('filters', {})),
                    json.dumps(decision_data.get('market_data', {})),
                    decision_data.get('trade_id')
                ))
                
                conn.commit()
                logger.debug(f"Logged decision: {decision_data['decision']} for {decision_data['symbol']}")
                
        except Exception as e:
            logger.error(f"Error logging decision: {e}")
    
    def log_order(self, order_data: Dict[str, Any]):
        """
        Log an order placement
        
        Args:
            order_data: Dictionary containing order details
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO orders 
                    (timestamp, order_id, symbol, side, quantity, limit_price, order_type, attempt, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order_data.get('timestamp', datetime.now().isoformat()),
                    order_data['order_id'],
                    order_data['symbol'],
                    order_data['side'],
                    order_data['quantity'],
                    order_data['limit_price'],
                    order_data.get('order_type', 'LMT'),
                    order_data.get('attempt', 1),
                    order_data.get('status', 'SUBMITTED')
                ))
                
                conn.commit()
                logger.debug(f"Logged order: {order_data['order_id']}")
                
        except Exception as e:
            logger.error(f"Error logging order: {e}")
    
    def log_fill(self, fill_data: Dict[str, Any]):
        """
        Log an order fill
        
        Args:
            fill_data: Dictionary containing fill details
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO fills 
                    (timestamp, order_id, symbol, fill_price, fill_quantity, commission)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    fill_data.get('timestamp', datetime.now().isoformat()),
                    fill_data['order_id'],
                    fill_data.get('symbol', ''),
                    fill_data['fill_price'],
                    fill_data['fill_quantity'],
                    fill_data.get('commission')
                ))
                
                conn.commit()
                logger.info(f"Logged fill: Order {fill_data['order_id']} "
                           f"filled {fill_data['fill_quantity']} @ {fill_data['fill_price']}")
                
        except Exception as e:
            logger.error(f"Error logging fill: {e}")
    
    def log_pnl_snapshot(self, pnl_data: Dict[str, Any]):
        """
        Log a P&L snapshot
        
        Args:
            pnl_data: Dictionary containing P&L details
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO pnl_snapshots 
                    (timestamp, symbol, position_id, unrealized_pnl, realized_pnl, 
                     total_pnl, underlying_price, delta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pnl_data.get('timestamp', datetime.now().isoformat()),
                    pnl_data['symbol'],
                    pnl_data['position_id'],
                    pnl_data['unrealized_pnl'],
                    pnl_data['realized_pnl'],
                    pnl_data['total_pnl'],
                    pnl_data['underlying_price'],
                    pnl_data.get('delta')
                ))
                
                conn.commit()
                logger.debug(f"Logged P&L snapshot for {pnl_data['symbol']}: ${pnl_data['total_pnl']:.2f}")
                
        except Exception as e:
            logger.error(f"Error logging P&L snapshot: {e}")
    
    def get_todays_decisions(self) -> List[Dict[str, Any]]:
        """Get all decisions made today"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                today = date.today().isoformat()
                cursor.execute('''
                    SELECT * FROM decisions 
                    WHERE created_date = ?
                    ORDER BY timestamp DESC
                ''', (today,))
                
                rows = cursor.fetchall()
                decisions = []
                
                for row in rows:
                    decision = dict(row)
                    # Parse JSON fields
                    if decision['filters']:
                        decision['filters'] = json.loads(decision['filters'])
                    if decision['market_data']:
                        decision['market_data'] = json.loads(decision['market_data'])
                    decisions.append(decision)
                
                return decisions
                
        except Exception as e:
            logger.error(f"Error getting today's decisions: {e}")
            return []
    
    def get_todays_fills(self) -> List[Dict[str, Any]]:
        """Get all fills from today"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                today = date.today().isoformat()
                cursor.execute('''
                    SELECT * FROM fills 
                    WHERE created_date = ?
                    ORDER BY timestamp DESC
                ''', (today,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting today's fills: {e}")
            return []
    
    def get_daily_summary(self, target_date: date = None) -> Dict[str, Any]:
        """
        Generate daily trading summary
        
        Args:
            target_date: Date to summarize (default: today)
            
        Returns:
            Dictionary with daily metrics
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get decision counts
                cursor.execute('''
                    SELECT decision, COUNT(*) as count
                    FROM decisions 
                    WHERE created_date = ?
                    GROUP BY decision
                ''', (date_str,))
                
                decision_counts = {row['decision']: row['count'] for row in cursor.fetchall()}
                
                # Get fill summary
                cursor.execute('''
                    SELECT COUNT(*) as fill_count, 
                           SUM(fill_quantity) as total_quantity,
                           AVG(fill_price) as avg_price
                    FROM fills 
                    WHERE created_date = ?
                ''', (date_str,))
                
                fill_data = cursor.fetchone()
                
                # Get latest P&L snapshots
                cursor.execute('''
                    SELECT symbol, SUM(total_pnl) as total_pnl
                    FROM pnl_snapshots 
                    WHERE created_date = ?
                    GROUP BY symbol
                ''', (date_str,))
                
                pnl_by_symbol = {row['symbol']: row['total_pnl'] for row in cursor.fetchall()}
                
                return {
                    'date': date_str,
                    'decisions': decision_counts,
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
            logger.error(f"Error generating daily summary: {e}")
            return {'date': date_str, 'error': str(e)}
    
    def generate_eod_report(self, target_date: date = None) -> str:
        """
        Generate end-of-day report
        
        Args:
            target_date: Date to report on (default: today)
            
        Returns:
            Formatted EOD report string
        """
        if target_date is None:
            target_date = date.today()
        
        summary = self.get_daily_summary(target_date)
        
        # Generate text report
        report_lines = [
            f"=== EOD REPORT - {summary['date']} ===",
            "",
            "DECISIONS:",
        ]
        
        decisions = summary.get('decisions', {})
        for decision_type, count in decisions.items():
            report_lines.append(f"  {decision_type}: {count}")
        
        if not decisions:
            report_lines.append("  No decisions recorded")
        
        report_lines.extend([
            "",
            "FILLS:",
            f"  Count: {summary['fills']['count']}",
            f"  Total Quantity: {summary['fills']['total_quantity']}",
            f"  Avg Price: ${summary['fills']['avg_price']:.3f}",
            "",
            "P&L BY SYMBOL:",
        ])
        
        for symbol, pnl in summary.get('pnl_by_symbol', {}).items():
            report_lines.append(f"  {symbol}: ${pnl:.2f}")
        
        report_lines.extend([
            "",
            f"TOTAL P&L: ${summary.get('total_pnl', 0):.2f}",
            f"SYMBOLS TRADED: {len(summary.get('symbols_traded', []))}",
            "",
            f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])
        
        report_text = "\n".join(report_lines)
        
        # Save to file
        try:
            eod_file = os.path.join(self.log_path, f"eod_{summary['date']}.txt")
            with open(eod_file, 'w') as f:
                f.write(report_text)
            
            # Also save JSON version
            json_file = os.path.join(self.log_path, f"eod_{summary['date']}.json")
            with open(json_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"EOD report saved to {eod_file}")
            
        except Exception as e:
            logger.error(f"Error saving EOD report: {e}")
        
        return report_text


# Global telemetry manager instance
_telemetry_manager = None

def get_telemetry_manager() -> TelemetryManager:
    """Get the global telemetry manager instance"""
    global _telemetry_manager
    if _telemetry_manager is None:
        _telemetry_manager = TelemetryManager()
    return _telemetry_manager