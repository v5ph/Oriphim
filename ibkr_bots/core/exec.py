"""
Order execution module with intelligent retry logic and timeout handling.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ib_insync import Contract, LimitOrder, ComboLeg

from .broker import get_broker
from .telemetry import get_telemetry_manager

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted" 
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


@dataclass
class OrderResult:
    """Result of order execution attempt"""
    success: bool
    order_id: Optional[int] = None
    fill_price: Optional[float] = None
    fill_quantity: int = 0
    status: OrderStatus = OrderStatus.PENDING
    message: str = ""
    execution_time: Optional[datetime] = None
    attempts: int = 0


class ExecutionEngine:
    """Smart order execution with retry logic and market impact minimization"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.broker = get_broker()
        self.telemetry = get_telemetry_manager()
        
        # Execution settings from config
        exec_config = config.get('execution', {})
        self.timeout_seconds = exec_config.get('timeout_seconds', 10)
        self.max_requotes = exec_config.get('max_requotes', 3)
        self.max_bid_ask_spread = exec_config.get('bid_ask_spread_max', 0.05)
        
        logger.info(f"Execution engine initialized: timeout={self.timeout_seconds}s, "
                   f"max_requotes={self.max_requotes}, max_spread=${self.max_bid_ask_spread}")
    
    def create_put_spread_combo(self, short_put: Contract, long_put: Contract, 
                               quantity: int = 1) -> Contract:
        """
        Create a combo contract for a bull put spread
        
        Args:
            short_put: Short put contract
            long_put: Long put contract  
            quantity: Number of spreads
            
        Returns:
            Combo contract
        """
        try:
            combo = Contract()
            combo.symbol = short_put.symbol
            combo.secType = 'BAG'
            combo.currency = 'USD'
            combo.exchange = 'SMART'
            
            # Create combo legs: sell short put, buy long put
            combo.comboLegs = [
                ComboLeg(conId=short_put.conId, ratio=1, action='SELL', exchange='SMART'),
                ComboLeg(conId=long_put.conId, ratio=1, action='BUY', exchange='SMART')
            ]
            
            logger.debug(f"Created put spread combo: sell {short_put.strike} / buy {long_put.strike}")
            return combo
            
        except Exception as e:
            logger.error(f"Error creating put spread combo: {e}")
            raise
    
    def get_combo_market_price(self, combo: Contract) -> Optional[Dict[str, float]]:
        """
        Get market price for a combo (spread)
        
        Args:
            combo: Combo contract
            
        Returns:
            Dict with bid, ask, mid prices or None
        """
        try:
            # Request market data for the combo
            ticker = self.broker.ib.reqMktData(combo, '', False, False)
            
            # Wait for initial quote
            start_time = time.time()
            while time.time() - start_time < 3:  # Wait up to 3 seconds
                self.broker.ib.sleep(0.1)
                
                if ticker.bid > 0 and ticker.ask > 0:
                    bid = ticker.bid
                    ask = ticker.ask
                    mid = (bid + ask) / 2
                    spread = ask - bid
                    
                    # Cancel market data
                    self.broker.ib.cancelMktData(combo)
                    
                    logger.debug(f"Combo quote: {bid:.3f} x {ask:.3f} (mid: {mid:.3f}, spread: {spread:.3f})")
                    
                    return {
                        'bid': bid,
                        'ask': ask, 
                        'mid': mid,
                        'spread': spread
                    }
            
            # Timeout - cancel and return None
            self.broker.ib.cancelMktData(combo)
            logger.warning("Timeout getting combo market price")
            return None
            
        except Exception as e:
            logger.error(f"Error getting combo market price: {e}")
            return None
    
    def execute_spread_order(self, combo: Contract, side: str, quantity: int, 
                           target_price: Optional[float] = None) -> OrderResult:
        """
        Execute a spread order with smart pricing and retry logic
        
        Args:
            combo: Combo contract to trade
            side: 'SELL' for credit spreads, 'BUY' for debit spreads
            quantity: Number of spreads
            target_price: Target price (if None, will use market-based pricing)
            
        Returns:
            OrderResult with execution details
        """
        result = OrderResult()
        result.attempts = 1
        
        try:
            # Get current market prices
            market_data = self.get_combo_market_price(combo)
            
            if not market_data:
                result.message = "Could not get market data for combo"
                return result
            
            # Check bid-ask spread
            if market_data['spread'] > self.max_bid_ask_spread:
                result.message = f"Spread too wide: ${market_data['spread']:.3f} > ${self.max_bid_ask_spread:.3f}"
                return result
            
            # Determine limit price
            if target_price is not None:
                limit_price = target_price
                logger.info(f"Using target price: ${limit_price:.3f}")
            else:
                # Smart pricing: slightly aggressive to get fills
                if side == 'SELL':
                    # For credit spreads, start slightly below mid
                    limit_price = market_data['mid'] - 0.01
                    limit_price = max(limit_price, market_data['bid'])  # Don't go below bid
                else:
                    # For debit spreads, start slightly above mid  
                    limit_price = market_data['mid'] + 0.01
                    limit_price = min(limit_price, market_data['ask'])  # Don't go above ask
                
                logger.info(f"Smart pricing: {side} at ${limit_price:.3f} (mid: ${market_data['mid']:.3f})")
            
            # Execute with retry logic
            for attempt in range(1, self.max_requotes + 2):  # +1 for initial attempt
                result.attempts = attempt
                
                # Create limit order
                order = LimitOrder(side, quantity, limit_price)
                order.orderType = 'LMT'
                order.tif = 'IOC' if attempt > 1 else 'DAY'  # Use IOC for requotes
                
                # Place order
                trade = self.broker.ib.placeOrder(combo, order)
                result.order_id = order.orderId
                result.status = OrderStatus.SUBMITTED
                
                logger.info(f"Attempt {attempt}: {side} {quantity} spreads at ${limit_price:.3f} "
                           f"(Order ID: {order.orderId})")
                
                # Log the order attempt
                self.telemetry.log_order({
                    'order_id': order.orderId,
                    'symbol': combo.symbol,
                    'side': side,
                    'quantity': quantity,
                    'limit_price': limit_price,
                    'attempt': attempt,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Wait for fill or timeout
                start_time = time.time()
                while time.time() - start_time < self.timeout_seconds:
                    self.broker.ib.sleep(0.1)
                    
                    # Check order status
                    if trade.orderStatus.status in ['Filled', 'Cancelled', 'ApiCancelled']:
                        break
                
                # Process final status
                if trade.orderStatus.status == 'Filled':
                    result.success = True
                    result.status = OrderStatus.FILLED
                    result.fill_price = trade.orderStatus.avgFillPrice
                    result.fill_quantity = trade.orderStatus.filled
                    result.execution_time = datetime.now()
                    result.message = f"Filled {result.fill_quantity} at ${result.fill_price:.3f}"
                    
                    # Log the fill
                    self.telemetry.log_fill({
                        'order_id': order.orderId,
                        'fill_price': result.fill_price,
                        'fill_quantity': result.fill_quantity,
                        'timestamp': result.execution_time.isoformat()
                    })
                    
                    logger.info(f"✅ Order filled: {result.message}")
                    return result
                
                elif trade.orderStatus.status in ['Cancelled', 'ApiCancelled']:
                    result.status = OrderStatus.CANCELLED
                    logger.info(f"Order cancelled, attempt {attempt}")
                    
                    # If not the last attempt, requote
                    if attempt < self.max_requotes + 1:
                        # Get fresh market data  
                        fresh_data = self.get_combo_market_price(combo)
                        
                        if fresh_data:
                            # Adjust price more aggressively
                            if side == 'SELL':
                                limit_price = fresh_data['mid'] - (0.01 * attempt)
                                limit_price = max(limit_price, fresh_data['bid'])
                            else:
                                limit_price = fresh_data['mid'] + (0.01 * attempt)  
                                limit_price = min(limit_price, fresh_data['ask'])
                            
                            logger.info(f"Requoting at ${limit_price:.3f} (attempt {attempt + 1})")
                            time.sleep(0.5)  # Brief pause before retry
                        else:
                            result.message = "Could not get fresh quotes for retry"
                            break
                else:
                    # Still pending after timeout
                    logger.warning(f"Order timeout after {self.timeout_seconds}s, cancelling")
                    
                    # Cancel the order
                    self.broker.ib.cancelOrder(order)
                    time.sleep(0.5)  # Wait for cancellation
                    
                    result.status = OrderStatus.TIMEOUT
                    
                    # Continue to next attempt if available
            
            # All attempts exhausted
            if not result.success:
                result.message = f"Failed after {result.attempts} attempts"
                logger.error(f"❌ Order execution failed: {result.message}")
            
            return result
            
        except Exception as e:
            result.message = f"Execution error: {str(e)}"
            result.status = OrderStatus.REJECTED
            logger.error(f"Order execution exception: {e}")
            return result
    
    def cancel_order(self, order_id: int) -> bool:
        """
        Cancel an order by ID
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancellation succeeded
        """
        try:
            # Find the order in open trades
            open_trades = self.broker.ib.openTrades()
            
            for trade in open_trades:
                if trade.order.orderId == order_id:
                    self.broker.ib.cancelOrder(trade.order)
                    logger.info(f"Cancelled order {order_id}")
                    return True
            
            logger.warning(f"Order {order_id} not found in open trades")
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def cancel_all_orders(self) -> int:
        """
        Cancel all open orders
        
        Returns:
            Number of orders cancelled
        """
        try:
            open_trades = self.broker.ib.openTrades()
            cancelled_count = 0
            
            for trade in open_trades:
                if trade.orderStatus.status in ['Submitted', 'PreSubmitted']:
                    self.broker.ib.cancelOrder(trade.order)
                    cancelled_count += 1
                    logger.info(f"Cancelled order {trade.order.orderId}")
            
            if cancelled_count > 0:
                logger.info(f"Cancelled {cancelled_count} open orders")
            
            return cancelled_count
            
        except Exception as e:
            logger.error(f"Error cancelling all orders: {e}")
            return 0


# Global execution engine instance
_execution_engine = None

def get_execution_engine(config: Dict[str, Any]) -> ExecutionEngine:
    """Get the global execution engine instance"""
    global _execution_engine
    if _execution_engine is None:
        _execution_engine = ExecutionEngine(config)
    return _execution_engine