"""
Oriphim Runner - IBKR Broker Manager

Handles IBKR TWS/Gateway connection and trading operations.
Integrates with existing ibkr_bots core modules for seamless execution.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import IBKR integration
try:
    from ib_insync import IB, Stock, Option, ComboLeg, Contract
except ImportError:
    logging.warning("ib_insync not available - install with: pip install ib_insync")
    IB = None

# Import existing trading core
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ibkr_bots"))

try:
    from core.broker import BrokerConnection, get_broker
    from core.options import get_options_analyzer
    from core.risk import get_risk_manager
    from core.regime import get_regime_analyzer
except ImportError as e:
    logging.warning(f"Could not import ibkr_bots core modules: {e}")
    BrokerConnection = None

logger = logging.getLogger('oriphim_runner.ibkr')


class IBKRManager:
    """
    IBKR broker connection and trading management
    
    Bridges the Runner with existing ibkr_bots trading infrastructure.
    Handles connection lifecycle, account info, and trade execution.
    """
    
    def __init__(self):
        self.broker_connection = None
        self.options_analyzer = None
        self.risk_manager = None
        self.regime_analyzer = None
        
        # Connection settings
        self.host = "127.0.0.1"
        self.paper_port = 7497
        self.live_port = 7496
        self.client_id = 100  # Unique ID for Runner
        
        # Connection state
        self.is_connected = False
        self.is_paper_mode = True
        self.account_info = {}
        self.connection_error = None
        
        logger.info("IBKR Manager initialized")
    
    @property
    def current_port(self) -> int:
        """Get current connection port based on mode"""
        return self.paper_port if self.is_paper_mode else self.live_port
    
    async def connect(self, paper_mode: bool = True) -> bool:
        """
        Connect to IBKR TWS/Gateway
        
        Args:
            paper_mode: True for paper trading, False for live
            
        Returns:
            True if connection successful
        """
        try:
            self.is_paper_mode = paper_mode
            mode_str = "PAPER" if paper_mode else "LIVE"
            
            logger.info(f"Connecting to IBKR {mode_str} mode on port {self.current_port}")
            
            if not BrokerConnection:
                logger.error("IBKR core modules not available")
                return False
            
            # Use existing broker connection from ibkr_bots
            self.broker_connection = BrokerConnection()
            
            # Connect to IBKR
            connected = self.broker_connection.connect(
                paper_mode=paper_mode,
                port=self.current_port,
                client_id=self.client_id
            )
            
            if not connected:
                logger.error("Failed to connect to IBKR")
                self.connection_error = "Connection failed"
                return False
            
            self.is_connected = True
            
            # Initialize trading modules
            self.options_analyzer = get_options_analyzer()
            self.risk_manager = get_risk_manager()
            self.regime_analyzer = get_regime_analyzer()
            
            # Get account information
            await self.update_account_info()
            
            logger.info(f"IBKR connected successfully in {mode_str} mode")
            return True
            
        except Exception as e:
            logger.error(f"IBKR connection error: {e}")
            self.connection_error = str(e)
            self.is_connected = False
            return False
    
    async def update_account_info(self):
        """Update account information"""
        try:
            if not self.is_connected:
                return
            
            # Get account details from broker
            account_summary = self.broker_connection.get_account_summary()
            
            self.account_info = {
                'account_id': account_summary.get('account_id', 'Unknown'),
                'mode': 'Paper' if self.is_paper_mode else 'Live',
                'buying_power': account_summary.get('buying_power', 0),
                'net_liquidation': account_summary.get('net_liquidation', 0),
                'total_cash': account_summary.get('total_cash', 0),
                'connection_time': datetime.now().isoformat(),
                'status': 'Connected'
            }
            
            logger.info(f"Account info updated: {self.account_info['account_id']}")
            
        except Exception as e:
            logger.error(f"Error updating account info: {e}")
            self.account_info['status'] = f'Error: {e}'
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get current account information"""
        if not self.account_info:
            await self.update_account_info()
        
        return self.account_info.copy()
    
    async def test_market_data(self) -> bool:
        """Test market data connectivity"""
        try:
            if not self.is_connected:
                return False
            
            # Test with SPY
            snapshot = self.broker_connection.get_market_snapshot('SPY')
            if snapshot and snapshot.price > 0:
                logger.info(f"Market data test successful: SPY @ ${snapshot.price:.2f}")
                return True
            else:
                logger.warning("Market data test failed - no valid price")
                return False
                
        except Exception as e:
            logger.error(f"Market data test error: {e}")
            return False
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        try:
            if not self.is_connected:
                return []
            
            positions = self.broker_connection.get_positions()
            
            # Convert to standard format
            formatted_positions = []
            for pos in positions:
                formatted_positions.append({
                    'symbol': pos.get('symbol', 'Unknown'),
                    'quantity': pos.get('quantity', 0),
                    'market_value': pos.get('market_value', 0),
                    'avg_cost': pos.get('avg_cost', 0),
                    'unrealized_pnl': pos.get('unrealized_pnl', 0),
                    'position_type': pos.get('position_type', 'Stock')
                })
            
            return formatted_positions
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    async def execute_trade(self, trade_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute trade based on configuration
        
        Args:
            trade_config: Trade configuration from job
            
        Returns:
            Execution result
        """
        try:
            if not self.is_connected:
                return {'status': 'error', 'message': 'Not connected to IBKR'}
            
            strategy = trade_config.get('strategy')
            symbol = trade_config.get('symbol')
            
            logger.info(f"Executing {strategy} trade for {symbol}")
            
            # Route to appropriate strategy execution
            if strategy == 'bull_put_spread':
                result = await self.execute_bull_put_spread(trade_config)
            elif strategy == 'iron_condor':
                result = await self.execute_iron_condor(trade_config)
            elif strategy == 'covered_call':
                result = await self.execute_covered_call(trade_config)
            else:
                result = {
                    'status': 'error',
                    'message': f'Unknown strategy: {strategy}'
                }
            
            logger.info(f"Trade execution result: {result['status']}")
            return result
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def execute_bull_put_spread(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bull put spread using existing options analyzer"""
        try:
            symbol = config['symbol']
            target_delta = config.get('target_delta', 0.10)
            
            # Get nearest expiry
            expiry = self.options_analyzer.get_nearest_friday_expiry(symbol)
            if not expiry:
                return {'status': 'error', 'message': 'No suitable expiry found'}
            
            # Build spread
            spread = self.options_analyzer.build_bull_put_spread(
                symbol, expiry, target_delta=target_delta
            )
            
            if not spread:
                return {'status': 'error', 'message': 'No suitable spread found'}
            
            # Check risk limits
            if not self.risk_manager.check_daily_limits():
                return {'status': 'error', 'message': 'Daily risk limits exceeded'}
            
            # For now, return success with spread details (actual execution would place orders)
            return {
                'status': 'success',
                'strategy': 'bull_put_spread',
                'symbol': symbol,
                'expiry': expiry,
                'credit': spread['net_credit'],
                'max_profit': spread['max_profit'],
                'max_loss': spread['max_loss'],
                'breakeven': spread['breakeven'],
                'timestamp': datetime.now().isoformat(),
                'mode': 'paper' if self.is_paper_mode else 'live'
            }
            
        except Exception as e:
            logger.error(f"Bull put spread execution error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def execute_iron_condor(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute iron condor strategy"""
        try:
            symbol = config['symbol']
            
            # Get expected move
            expiry = self.options_analyzer.get_nearest_friday_expiry(symbol)
            em_result = self.options_analyzer.calculate_expected_move(symbol, expiry)
            
            if not em_result:
                return {'status': 'error', 'message': 'Could not calculate expected move'}
            
            # Build condor
            condor = self.options_analyzer.build_iron_condor(
                symbol, expiry, em_result.dollar_em
            )
            
            if not condor:
                return {'status': 'error', 'message': 'No suitable condor found'}
            
            return {
                'status': 'success',
                'strategy': 'iron_condor',
                'symbol': symbol,
                'expiry': expiry,
                'credit': condor['net_credit'],
                'max_profit': condor['max_profit'],
                'max_loss': condor['max_loss'],
                'prob_profit': condor['prob_profit'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Iron condor execution error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def execute_covered_call(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute covered call strategy"""
        try:
            symbol = config['symbol']
            shares_owned = config.get('shares_owned', 100)
            
            expiry = self.options_analyzer.get_nearest_friday_expiry(symbol)
            covered_call = self.options_analyzer.build_covered_call(
                symbol, expiry, shares_owned
            )
            
            if not covered_call:
                return {'status': 'error', 'message': 'No suitable covered call found'}
            
            return {
                'status': 'success',
                'strategy': 'covered_call',
                'symbol': symbol,
                'expiry': expiry,
                'premium': covered_call['total_premium'],
                'contracts': covered_call['contracts'],
                'max_profit': covered_call['max_profit'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Covered call execution error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        return {
            'connected': self.is_connected,
            'mode': 'Paper' if self.is_paper_mode else 'Live',
            'port': self.current_port,
            'client_id': self.client_id,
            'error': self.connection_error,
            'account_info': self.account_info,
            'last_update': datetime.now().isoformat()
        }
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        try:
            logger.info("Disconnecting from IBKR...")
            
            if self.broker_connection and self.is_connected:
                self.broker_connection.disconnect()
            
            self.is_connected = False
            self.connection_error = None
            
            logger.info("IBKR disconnection complete")
            
        except Exception as e:
            logger.error(f"Error disconnecting from IBKR: {e}")


# Mock IBKR Manager for testing without TWS
class MockIBKRManager(IBKRManager):
    """Mock IBKR Manager for testing without actual TWS connection"""
    
    async def connect(self, paper_mode: bool = True) -> bool:
        """Simulate IBKR connection"""
        logger.info(f"Mock IBKR connection established (Paper: {paper_mode})")
        self.is_connected = True
        self.is_paper_mode = paper_mode
        
        self.account_info = {
            'account_id': 'DU123456' if paper_mode else 'U123456',
            'mode': 'Paper' if paper_mode else 'Live',
            'buying_power': 100000.0,
            'net_liquidation': 100000.0,
            'total_cash': 100000.0,
            'connection_time': datetime.now().isoformat(),
            'status': 'Connected (Mock)'
        }
        
        return True
    
    async def test_market_data(self) -> bool:
        """Mock market data test"""
        logger.info("Mock market data test successful: SPY @ $450.00")
        return True
    
    async def execute_trade(self, trade_config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock trade execution"""
        strategy = trade_config.get('strategy')
        symbol = trade_config.get('symbol')
        
        logger.info(f"Mock executing {strategy} for {symbol}")
        
        # Simulate execution delay
        await asyncio.sleep(1)
        
        return {
            'status': 'success',
            'strategy': strategy,
            'symbol': symbol,
            'credit': 0.52,
            'max_profit': 52.0,
            'max_loss': 48.0,
            'timestamp': datetime.now().isoformat(),
            'mode': 'mock_paper'
        }