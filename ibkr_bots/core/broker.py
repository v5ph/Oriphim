"""
IBKR broker connection and contract handling module.
Provides connection management, contract qualification, and market data access.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from ib_insync import IB, Stock, Option, ComboLeg, Contract, Ticker
from ib_insync import util as ibutil

logger = logging.getLogger(__name__)


@dataclass
class MarketDataSnapshot:
    """Snapshot of market data for a symbol"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume: int
    timestamp: datetime


class BrokerConnection:
    """IBKR connection wrapper with auto-reconnect and error handling"""
    
    def __init__(self):
        self.ib = IB()
        self.connected = False
        self.host = "127.0.0.1"
        self.port = 7497
        self.client_id = 1
        
    def connect(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1) -> bool:
        """
        Connect to IBKR TWS or Gateway
        
        Args:
            host: IBKR host address
            port: IBKR port (7497 for TWS paper, 7496 for TWS live)
            client_id: Unique client identifier
            
        Returns:
            bool: True if connected successfully
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        
        try:
            if self.ib.isConnected():
                logger.info("Already connected to IBKR")
                return True
                
            logger.info(f"Connecting to IBKR at {host}:{port} with client_id {client_id}")
            self.ib.connect(host, port, clientId=client_id, timeout=30)
            
            if self.ib.isConnected():
                self.connected = True
                logger.info("Successfully connected to IBKR")
                
                # Get account info to verify connection
                accounts = self.ib.managedAccounts()
                logger.info(f"Connected accounts: {accounts}")
                
                return True
            else:
                logger.error("Failed to connect to IBKR")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Gracefully disconnect from IBKR"""
        try:
            if self.ib.isConnected():
                self.ib.disconnect()
                logger.info("Disconnected from IBKR")
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
        finally:
            self.connected = False
    
    def reconnect(self) -> bool:
        """Attempt to reconnect with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            logger.info(f"Reconnection attempt {attempt + 1}/{max_retries}")
            
            try:
                self.disconnect()
                time.sleep(2)
                
                if self.connect(self.host, self.port, self.client_id):
                    return True
                    
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
                
            if attempt < max_retries - 1:
                time.sleep(5)
        
        logger.error("All reconnection attempts failed")
        return False
    
    def is_connected(self) -> bool:
        """Check if connection is active"""
        try:
            return self.ib.isConnected()
        except:
            return False
    
    def qualify_contracts(self, contracts: List[Contract]) -> List[Contract]:
        """
        Qualify contracts to get complete contract details
        
        Args:
            contracts: List of contracts to qualify
            
        Returns:
            List of qualified contracts
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to IBKR")
        
        try:
            qualified = self.ib.qualifyContracts(*contracts)
            logger.debug(f"Qualified {len(qualified)} contracts")
            return qualified
        except Exception as e:
            logger.error(f"Contract qualification failed: {e}")
            raise
    
    def get_stock_contract(self, symbol: str, exchange: str = "SMART") -> Stock:
        """Create and qualify a stock contract"""
        stock = Stock(symbol, exchange, "USD")
        qualified = self.qualify_contracts([stock])
        
        if not qualified:
            raise ValueError(f"Could not qualify stock contract for {symbol}")
            
        return qualified[0]
    
    def get_option_contract(self, symbol: str, expiry: str, strike: float, 
                          right: str, exchange: str = "SMART") -> Option:
        """Create and qualify an option contract"""
        option = Option(symbol, expiry, strike, right, exchange, currency="USD")
        qualified = self.qualify_contracts([option])
        
        if not qualified:
            raise ValueError(f"Could not qualify option contract {symbol} {expiry} {strike} {right}")
            
        return qualified[0]
    
    def market_data_stock(self, symbol: str, exchange: str = "SMART") -> Optional[Ticker]:
        """
        Get real-time market data for a stock
        
        Args:
            symbol: Stock symbol
            exchange: Exchange to get data from
            
        Returns:
            Ticker object with live data
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to IBKR")
        
        try:
            stock = self.get_stock_contract(symbol, exchange)
            ticker = self.ib.reqMktData(stock, "", False, False)
            
            # Wait a moment for initial data
            self.ib.sleep(1)
            
            return ticker
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return None
    
    def get_market_snapshot(self, symbol: str) -> Optional[MarketDataSnapshot]:
        """Get a snapshot of current market data"""
        ticker = self.market_data_stock(symbol)
        
        if ticker and ticker.last > 0:
            return MarketDataSnapshot(
                symbol=symbol,
                price=ticker.last,
                bid=ticker.bid if ticker.bid > 0 else ticker.last,
                ask=ticker.ask if ticker.ask > 0 else ticker.last,
                volume=ticker.volume if ticker.volume else 0,
                timestamp=datetime.now()
            )
        return None
    
    def get_option_chain(self, symbol: str, exchange: str = "SMART") -> Dict[str, Any]:
        """
        Get option chain information for a symbol
        
        Args:
            symbol: Underlying symbol
            exchange: Exchange
            
        Returns:
            Dict containing expirations, strikes, and multiplier
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to IBKR")
        
        try:
            stock = self.get_stock_contract(symbol, exchange)
            
            chains = self.ib.reqSecDefOptParams(
                underlyingSymbol=stock.symbol,
                futFopExchange="",
                underlyingSecType=stock.secType,
                underlyingConId=stock.conId
            )
            
            if not chains:
                logger.warning(f"No option chains found for {symbol}")
                return {}
            
            # Use the first chain (typically the most liquid exchange)
            chain = chains[0]
            
            return {
                "expirations": sorted(chain.expirations),
                "strikes": sorted(chain.strikes),
                "multiplier": chain.multiplier,
                "exchange": chain.exchange
            }
            
        except Exception as e:
            logger.error(f"Failed to get option chain for {symbol}: {e}")
            return {}
    
    def place_combo_order(self, combo_contract: Contract, side: str, 
                         quantity: int, limit_price: float) -> Any:
        """
        Place a combo (spread) order
        
        Args:
            combo_contract: Combo contract with legs
            side: 'BUY' or 'SELL'
            quantity: Number of combos
            limit_price: Limit price for the combo
            
        Returns:
            Trade object
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to IBKR")
        
        try:
            from ib_insync import LimitOrder
            
            order = LimitOrder(side, quantity, limit_price)
            order.orderType = "LMT"
            order.tif = "DAY"
            
            trade = self.ib.placeOrder(combo_contract, order)
            logger.info(f"Placed {side} order for {quantity} {combo_contract.symbol} combo at {limit_price}")
            
            return trade
            
        except Exception as e:
            logger.error(f"Failed to place combo order: {e}")
            raise
    
    def cancel_all_orders(self):
        """Cancel all pending orders"""
        try:
            open_orders = self.ib.openTrades()
            for trade in open_orders:
                if trade.orderStatus.status in ['Submitted', 'PreSubmitted']:
                    self.ib.cancelOrder(trade.order)
                    logger.info(f"Cancelled order {trade.order.orderId}")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
    
    def get_positions(self) -> List[Any]:
        """Get current positions"""
        try:
            return self.ib.positions()
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary information"""
        try:
            summary = self.ib.accountSummary()
            result = {}
            for item in summary:
                result[item.tag] = item.value
            return result
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {}


# Global connection instance
_broker = None

def get_broker() -> BrokerConnection:
    """Get the global broker connection instance"""
    global _broker
    if _broker is None:
        _broker = BrokerConnection()
    return _broker