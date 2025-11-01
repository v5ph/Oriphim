"""
Oriphim Runner - Local Data Storage Manager

Handles local data persistence including:
- Configuration storage with encrypted API keys
- Trade logs and execution history
- Model cache and ML artifacts
- Application state and preferences
"""

import os
import json
import sqlite3
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import base64
import hashlib

logger = logging.getLogger('oriphim_runner.storage')


class LocalDataManager:
    """
    Manages local data storage for Oriphim Runner
    
    Features:
    - Encrypted configuration storage
    - SQLite database for logs and history
    - JSON cache for model artifacts
    - Automatic cleanup of old data
    """
    
    def __init__(self):
        # Set up data directory
        self.data_dir = Path.home() / ".oriphim"
        self.config_file = self.data_dir / "config.json"
        self.db_file = self.data_dir / "runner.db"
        self.logs_dir = self.data_dir / "logs"
        self.models_dir = self.data_dir / "models"
        
        # Encryption key for sensitive data
        self.encryption_key = None
        
        logger.info(f"Data directory: {self.data_dir}")
    
    async def initialize(self):
        """Initialize local data storage"""
        try:
            # Create directories
            self.data_dir.mkdir(exist_ok=True)
            self.logs_dir.mkdir(exist_ok=True)
            self.models_dir.mkdir(exist_ok=True)
            
            # Initialize database
            await self.init_database()
            
            # Generate or load encryption key
            await self.init_encryption()
            
            logger.info("Local data storage initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize data storage: {e}")
            raise
    
    async def init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    status TEXT NOT NULL,
                    execution_details TEXT,
                    pnl REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    module TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS connection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_logs_timestamp ON trade_logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_logs_symbol ON trade_logs(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_app_logs_timestamp ON app_logs(timestamp)')
            
            conn.commit()
            conn.close()
            
            logger.info("Database initialized")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    async def init_encryption(self):
        """Initialize encryption for sensitive data"""
        try:
            key_file = self.data_dir / ".key"
            
            if key_file.exists():
                # Load existing key
                with open(key_file, 'rb') as f:
                    self.encryption_key = f.read()
            else:
                # Generate new key
                import secrets
                self.encryption_key = secrets.token_bytes(32)
                
                # Save key with restricted permissions
                with open(key_file, 'wb') as f:
                    f.write(self.encryption_key)
                
                # Set file permissions (Unix-like systems)
                if os.name != 'nt':  # Not Windows
                    os.chmod(key_file, 0o600)
            
            logger.info("Encryption initialized")
            
        except Exception as e:
            logger.error(f"Encryption initialization error: {e}")
            # Continue without encryption as fallback
            self.encryption_key = None
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            if not self.encryption_key:
                return data  # Return unencrypted if no key
            
            # Simple XOR encryption for demo (use proper encryption in production)
            encrypted = bytearray()
            key_len = len(self.encryption_key)
            
            for i, byte in enumerate(data.encode('utf-8')):
                encrypted.append(byte ^ self.encryption_key[i % key_len])
            
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return data
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            if not self.encryption_key:
                return encrypted_data  # Return as-is if no key
            
            # Reverse the XOR encryption
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = bytearray()
            key_len = len(self.encryption_key)
            
            for i, byte in enumerate(encrypted_bytes):
                decrypted.append(byte ^ self.encryption_key[i % key_len])
            
            return decrypted.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return encrypted_data
    
    async def save_config(self, config: Dict[str, Any]):
        """Save application configuration with encrypted sensitive data"""
        try:
            # Encrypt sensitive fields
            config_to_save = config.copy()
            
            if 'api_key' in config_to_save:
                config_to_save['api_key'] = self.encrypt_data(config_to_save['api_key'])
            
            if 'broker_credentials' in config_to_save:
                creds = json.dumps(config_to_save['broker_credentials'])
                config_to_save['broker_credentials'] = self.encrypt_data(creds)
            
            # Add metadata
            config_to_save['_encrypted'] = True
            config_to_save['_version'] = '1.0.0'
            config_to_save['_updated'] = datetime.now().isoformat()
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(config_to_save, f, indent=2)
            
            logger.info("Configuration saved")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    async def load_config(self) -> Optional[Dict[str, Any]]:
        """Load application configuration with decrypted sensitive data"""
        try:
            if not self.config_file.exists():
                logger.info("No configuration file found")
                return None
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Decrypt sensitive fields
            if config.get('_encrypted'):
                if 'api_key' in config:
                    config['api_key'] = self.decrypt_data(config['api_key'])
                
                if 'broker_credentials' in config:
                    creds_json = self.decrypt_data(config['broker_credentials'])
                    config['broker_credentials'] = json.loads(creds_json)
            
            logger.info("Configuration loaded")
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return None
    
    async def log_trade(self, job: Dict[str, Any], result: Dict[str, Any]):
        """Log trade execution to database"""
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            # Extract relevant data
            job_id = job.get('id', 'unknown')
            strategy = job.get('strategy', 'unknown')
            symbol = job.get('symbol', 'unknown')
            status = result.get('status', 'unknown')
            
            # Calculate P&L
            pnl = 0.0
            if status == 'success':
                data = result.get('data', {})
                execution_details = data.get('execution_details', {})
                pnl = execution_details.get('expected_return', 0)
            
            # Insert trade log
            cursor.execute('''
                INSERT INTO trade_logs 
                (timestamp, job_id, strategy, symbol, status, execution_details, pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                job_id,
                strategy,
                symbol,
                status,
                json.dumps(result),
                pnl
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Trade logged: {job_id} ({status})")
            
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
    
    async def log_app_event(self, level: str, module: str, message: str):
        """Log application event to database"""
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO app_logs (timestamp, level, module, message)
                VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                level,
                module,
                message
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging app event: {e}")
    
    async def log_connection_event(self, event_type: str, details: Dict[str, Any]):
        """Log connection event"""
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO connection_history (timestamp, event_type, details)
                VALUES (?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                event_type,
                json.dumps(details)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging connection event: {e}")
    
    async def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent application logs for UI display"""
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            # Get recent trade and app logs combined
            cursor.execute('''
                SELECT 'trade' as log_type, timestamp, 
                       printf('%s: %s %s (%s)', strategy, symbol, status, job_id) as message
                FROM trade_logs
                WHERE timestamp >= datetime('now', '-24 hours')
                UNION ALL
                SELECT 'app' as log_type, timestamp, 
                       printf('[%s] %s: %s', level, module, message) as message
                FROM app_logs 
                WHERE timestamp >= datetime('now', '-24 hours')
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            logs = []
            for row in rows:
                logs.append({
                    'type': row[0],
                    'timestamp': row[1],
                    'message': row[2]
                })
            
            return logs
            
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            return []
    
    async def get_trade_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get trade execution history"""
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM trade_logs
                WHERE timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            '''.format(days))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to dictionaries
            columns = ['id', 'timestamp', 'job_id', 'strategy', 'symbol', 'status', 'execution_details', 'pnl', 'created_at']
            trades = []
            
            for row in rows:
                trade = dict(zip(columns, row))
                if trade['execution_details']:
                    trade['execution_details'] = json.loads(trade['execution_details'])
                trades.append(trade)
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return []
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_trades,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    MAX(pnl) as max_pnl,
                    MIN(pnl) as min_pnl
                FROM trade_logs
                WHERE timestamp >= datetime('now', '-30 days')
            ''')
            
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0] > 0:
                stats = {
                    'total_trades': row[0],
                    'successful_trades': row[1],
                    'success_rate': row[1] / row[0] if row[0] > 0 else 0,
                    'total_pnl': row[2] or 0,
                    'avg_pnl': row[3] or 0,
                    'max_pnl': row[4] or 0,
                    'min_pnl': row[5] or 0,
                    'period_days': 30
                }
            else:
                stats = {
                    'total_trades': 0,
                    'successful_trades': 0,
                    'success_rate': 0,
                    'total_pnl': 0,
                    'avg_pnl': 0,
                    'max_pnl': 0,
                    'min_pnl': 0,
                    'period_days': 30
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {}
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to prevent database from growing too large"""
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            # Clean up old logs
            cursor.execute('DELETE FROM app_logs WHERE timestamp < ?', (cutoff_date,))
            app_deleted = cursor.rowcount
            
            # Keep trade logs longer (they're more valuable)
            trade_cutoff = (datetime.now() - timedelta(days=days_to_keep * 2)).isoformat()
            cursor.execute('DELETE FROM trade_logs WHERE timestamp < ?', (trade_cutoff,))
            trade_deleted = cursor.rowcount
            
            # Clean up connection history
            cursor.execute('DELETE FROM connection_history WHERE timestamp < ?', (cutoff_date,))
            conn_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleanup complete: {app_deleted} app logs, {trade_deleted} trade logs, {conn_deleted} connection events")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def backup_data(self, backup_path: Optional[Path] = None) -> bool:
        """Create backup of critical data"""
        try:
            if backup_path is None:
                backup_path = self.data_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Get trade history
            trades = await self.get_trade_history(days=365)  # Full year
            
            # Get configuration (excluding sensitive data for security)
            config = await self.load_config()
            if config:
                config = {k: v for k, v in config.items() if not k.startswith('_') and k != 'api_key'}
            
            backup_data = {
                'backup_timestamp': datetime.now().isoformat(),
                'runner_version': '1.0.0',
                'trades': trades,
                'config': config
            }
            
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Data backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False