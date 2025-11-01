"""
Options pricing, chain analysis, and Greeks calculations.
Handles expected moves, IV rank, and spread construction.
"""

import logging
import json
import os
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, date
from dataclasses import dataclass
import math

import numpy as np
import pandas as pd

from .broker import get_broker

logger = logging.getLogger(__name__)


@dataclass
class OptionQuote:
    """Option quote data"""
    symbol: str
    expiry: str
    strike: float
    right: str  # 'C' or 'P'
    bid: float
    ask: float
    mid: float
    iv: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    volume: int = 0


@dataclass
class ExpectedMove:
    """Expected move calculation result"""
    symbol: str
    expiry: str
    dollar_em: float
    percent_em: float
    underlying_price: float
    timestamp: datetime


class OptionsAnalyzer:
    """Options chain analysis and calculations"""
    
    def __init__(self):
        self.broker = get_broker()
        self.iv_cache_file = "data/iv_cache.json"
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
    
    def get_option_quotes(self, symbol: str, expiry: str, strikes: List[float]) -> List[OptionQuote]:
        """
        Get option quotes for given strikes and expiry
        
        Args:
            symbol: Underlying symbol
            expiry: Option expiry (YYYYMMDD format)
            strikes: List of strikes to get quotes for
            
        Returns:
            List of OptionQuote objects
        """
        quotes = []
        
        try:
            for strike in strikes:
                for right in ['C', 'P']:
                    try:
                        option = self.broker.get_option_contract(symbol, expiry, strike, right)
                        ticker = self.broker.ib.reqMktData(option, "", False, False)
                        
                        # Wait for data
                        self.broker.ib.sleep(0.5)
                        
                        if ticker.bid > 0 and ticker.ask > 0:
                            mid = (ticker.bid + ticker.ask) / 2
                            
                            quote = OptionQuote(
                                symbol=symbol,
                                expiry=expiry,
                                strike=strike,
                                right=right,
                                bid=ticker.bid,
                                ask=ticker.ask,
                                mid=mid,
                                iv=getattr(ticker, 'impliedVolatility', None),
                                delta=getattr(ticker, 'delta', None),
                                volume=getattr(ticker, 'volume', 0)
                            )
                            quotes.append(quote)
                        
                        # Cancel market data to avoid hitting limits
                        self.broker.ib.cancelMktData(option)
                        
                    except Exception as e:
                        logger.warning(f"Failed to get quote for {symbol} {expiry} {strike} {right}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error getting option quotes for {symbol}: {e}")
        
        return quotes
    
    def expected_move_from_chain(self, symbol: str, expiry: str) -> Optional[ExpectedMove]:
        """
        Calculate expected move from ATM straddle
        
        Args:
            symbol: Underlying symbol  
            expiry: Option expiry
            
        Returns:
            ExpectedMove object or None if calculation fails
        """
        try:
            # Get current stock price
            snapshot = self.broker.get_market_snapshot(symbol)
            if not snapshot:
                logger.error(f"Could not get market data for {symbol}")
                return None
            
            underlying_price = snapshot.price
            
            # Find ATM strike (closest to current price)
            chain_info = self.broker.get_option_chain(symbol)
            if not chain_info or not chain_info.get('strikes'):
                logger.error(f"No option chain data for {symbol}")
                return None
            
            strikes = chain_info['strikes']
            atm_strike = min(strikes, key=lambda x: abs(x - underlying_price))
            
            # Get ATM call and put quotes
            quotes = self.get_option_quotes(symbol, expiry, [atm_strike])
            
            atm_call = next((q for q in quotes if q.right == 'C' and q.strike == atm_strike), None)
            atm_put = next((q for q in quotes if q.right == 'P' and q.strike == atm_strike), None)
            
            if not atm_call or not atm_put:
                logger.warning(f"Could not find ATM straddle quotes for {symbol} {expiry}")
                return None
            
            # Expected move = (Call_mid + Put_mid)
            dollar_em = atm_call.mid + atm_put.mid
            percent_em = dollar_em / underlying_price
            
            logger.info(f"Expected move for {symbol} {expiry}: ${dollar_em:.2f} ({percent_em:.1%})")
            
            return ExpectedMove(
                symbol=symbol,
                expiry=expiry,
                dollar_em=dollar_em,
                percent_em=percent_em,
                underlying_price=underlying_price,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating expected move for {symbol} {expiry}: {e}")
            return None
    
    def find_put_spread_by_delta(self, symbol: str, expiry: str, 
                                delta_range: Tuple[float, float] = (0.05, 0.10)) -> Optional[Dict]:
        """
        Find bull put spread with target delta range
        
        Args:
            symbol: Underlying symbol
            expiry: Option expiry
            delta_range: Target delta range (min, max)
            
        Returns:
            Dict with spread details or None
        """
        try:
            # Get current price and chain
            snapshot = self.broker.get_market_snapshot(symbol)
            if not snapshot:
                return None
            
            underlying_price = snapshot.price
            chain_info = self.broker.get_option_chain(symbol)
            strikes = chain_info.get('strikes', [])
            
            if not strikes:
                return None
            
            # Filter strikes below current price for puts
            put_strikes = [s for s in strikes if s < underlying_price]
            put_strikes.sort(reverse=True)  # Start from highest (closest to ATM)
            
            # Get put quotes
            quotes = self.get_option_quotes(symbol, expiry, put_strikes[:20])  # Limit to 20 strikes
            put_quotes = [q for q in quotes if q.right == 'P' and q.delta is not None]
            
            if len(put_quotes) < 2:
                logger.warning(f"Not enough put quotes with delta for {symbol} {expiry}")
                return None
            
            # Find short put in target delta range
            target_puts = [q for q in put_quotes 
                          if delta_range[0] <= abs(q.delta) <= delta_range[1]]
            
            if not target_puts:
                logger.warning(f"No puts found in delta range {delta_range} for {symbol} {expiry}")
                return None
            
            # Choose the put closest to middle of delta range
            target_delta = sum(delta_range) / 2
            short_put = min(target_puts, key=lambda q: abs(abs(q.delta) - target_delta))
            
            # Find long put (5-10 points OTM from short put)
            long_put_strikes = [s for s in put_strikes if s < short_put.strike - 3]
            if not long_put_strikes:
                return None
            
            # Choose long put strike
            spread_width = min(10, short_put.strike - long_put_strikes[0])
            long_strike = short_put.strike - spread_width
            
            long_put = next((q for q in put_quotes if q.strike == long_strike), None)
            
            if not long_put:
                # Get quote for the calculated long strike
                long_quotes = self.get_option_quotes(symbol, expiry, [long_strike])
                long_put = next((q for q in long_quotes if q.right == 'P'), None)
            
            if not long_put:
                logger.warning(f"Could not find long put at strike {long_strike}")
                return None
            
            # Calculate spread metrics
            credit = short_put.mid - long_put.mid
            max_loss = spread_width - credit
            max_profit = credit
            
            # Risk-reward check
            if credit <= 0 or max_loss <= 0:
                logger.warning(f"Invalid spread pricing: credit={credit}, max_loss={max_loss}")
                return None
            
            return {
                'short_put': {
                    'strike': short_put.strike,
                    'mid': short_put.mid,
                    'delta': short_put.delta,
                    'contract': self.broker.get_option_contract(symbol, expiry, short_put.strike, 'P')
                },
                'long_put': {
                    'strike': long_put.strike,
                    'mid': long_put.mid,
                    'delta': long_put.delta,
                    'contract': self.broker.get_option_contract(symbol, expiry, long_put.strike, 'P')
                },
                'spread_metrics': {
                    'credit': credit,
                    'max_loss': max_loss,
                    'max_profit': max_profit,
                    'width': spread_width,
                    'pop': credit / spread_width  # Probability of profit estimate
                }
            }
            
        except Exception as e:
            logger.error(f"Error finding put spread for {symbol} {expiry}: {e}")
            return None
    
    def iv_rank(self, symbol: str, lookback_days: int = 252) -> Optional[float]:
        """
        Calculate IV rank (current IV percentile vs historical range)
        
        Args:
            symbol: Symbol to calculate IV rank for
            lookback_days: Days to look back for historical IV
            
        Returns:
            IV rank as a percentile (0-100) or None
        """
        try:
            # Try to get current ATM IV
            snapshot = self.broker.get_market_snapshot(symbol)
            if not snapshot:
                return None
            
            underlying_price = snapshot.price
            
            # Get nearest expiry with options
            chain_info = self.broker.get_option_chain(symbol)
            expirations = chain_info.get('expirations', [])
            
            if not expirations:
                return None
            
            # Use nearest expiry (typically weekly or monthly)
            nearest_expiry = expirations[0]
            
            # Get ATM straddle IV
            strikes = chain_info.get('strikes', [])
            atm_strike = min(strikes, key=lambda x: abs(x - underlying_price))
            
            quotes = self.get_option_quotes(symbol, nearest_expiry, [atm_strike])
            atm_call = next((q for q in quotes if q.right == 'C'), None)
            
            if not atm_call or not atm_call.iv:
                logger.warning(f"Could not get current IV for {symbol}")
                return 50.0  # Default to neutral rank
            
            current_iv = atm_call.iv * 100  # Convert to percentage
            
            # Load historical IV from cache
            iv_history = self._load_iv_cache(symbol)
            
            # Add current IV to history
            today = date.today().isoformat()
            iv_history[today] = current_iv
            
            # Keep only recent history
            dates = sorted(iv_history.keys())
            if len(dates) > lookback_days:
                for old_date in dates[:-lookback_days]:
                    del iv_history[old_date]
            
            # Save updated cache
            self._save_iv_cache(symbol, iv_history)
            
            # Calculate percentile rank
            iv_values = list(iv_history.values())
            if len(iv_values) < 10:  # Need minimum history
                return 50.0
            
            rank = (sum(1 for iv in iv_values if iv < current_iv) / len(iv_values)) * 100
            
            logger.debug(f"IV rank for {symbol}: {rank:.1f}% (current IV: {current_iv:.1f}%)")
            return rank
            
        except Exception as e:
            logger.error(f"Error calculating IV rank for {symbol}: {e}")
            return None
    
    def _load_iv_cache(self, symbol: str) -> Dict[str, float]:
        """Load IV history from cache file"""
        try:
            if os.path.exists(self.iv_cache_file):
                with open(self.iv_cache_file, 'r') as f:
                    cache = json.load(f)
                    return cache.get(symbol, {})
        except Exception as e:
            logger.warning(f"Could not load IV cache: {e}")
        
        return {}
    
    def _save_iv_cache(self, symbol: str, iv_history: Dict[str, float]):
        """Save IV history to cache file"""
        try:
            cache = {}
            if os.path.exists(self.iv_cache_file):
                with open(self.iv_cache_file, 'r') as f:
                    cache = json.load(f)
            
            cache[symbol] = iv_history
            
            with open(self.iv_cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save IV cache: {e}")
    
    def get_nearest_friday_expiry(self, symbol: str) -> Optional[str]:
        """Get the nearest Friday expiry (0DTE or 1DTE preferred)"""
        try:
            chain_info = self.broker.get_option_chain(symbol)
            expirations = chain_info.get('expirations', [])
            
            if not expirations:
                return None
            
            today = datetime.now().date()
            
            # Look for 0DTE or 1DTE first
            for exp_str in expirations[:3]:  # Check first few expiries
                exp_date = datetime.strptime(exp_str, '%Y%m%d').date()
                days_to_exp = (exp_date - today).days
                
                # Prefer 0DTE (same day) or 1DTE
                if days_to_exp <= 1:
                    return exp_str
            
            # Fallback to nearest expiry
            return expirations[0]
            
        except Exception as e:
            logger.error(f"Error getting expiry for {symbol}: {e}")
            return None

    def build_iron_condor(self, symbol: str, expiry: str, expected_move: float, 
                         wing_multiplier: float = 1.3) -> Optional[Dict]:
        """
        Build iron condor spread around expected move
        
        Args:
            symbol: Underlying symbol
            expiry: Option expiry
            expected_move: Expected move in dollars
            wing_multiplier: Multiplier for wing strikes (1.3 = 30% outside EM)
            
        Returns:
            Dict with condor spread details
        """
        try:
            snapshot = self.broker.get_market_snapshot(symbol)
            if not snapshot:
                return None
            
            underlying_price = snapshot.price
            
            # Calculate strike levels
            call_short_strike = underlying_price + expected_move
            call_long_strike = underlying_price + (expected_move * wing_multiplier)
            put_short_strike = underlying_price - expected_move  
            put_long_strike = underlying_price - (expected_move * wing_multiplier)
            
            # Get option chain and find nearest strikes
            chain_info = self.broker.get_option_chain(symbol)
            strikes = sorted(chain_info.get('strikes', []))
            
            # Find closest available strikes
            call_short = min(strikes, key=lambda x: abs(x - call_short_strike))
            call_long = min([s for s in strikes if s > call_short], 
                          key=lambda x: abs(x - call_long_strike))
            put_short = min(strikes, key=lambda x: abs(x - put_short_strike))
            put_long = max([s for s in strikes if s < put_short],
                         key=lambda x: abs(x - put_long_strike))
            
            # Get quotes for all legs
            quotes = self.get_option_quotes(symbol, expiry, 
                                          [call_short, call_long, put_short, put_long])
            
            call_short_quote = next((q for q in quotes if q.strike == call_short and q.right == 'C'), None)
            call_long_quote = next((q for q in quotes if q.strike == call_long and q.right == 'C'), None)
            put_short_quote = next((q for q in quotes if q.strike == put_short and q.right == 'P'), None)
            put_long_quote = next((q for q in quotes if q.strike == put_long and q.right == 'P'), None)
            
            if not all([call_short_quote, call_long_quote, put_short_quote, put_long_quote]):
                logger.warning(f"Could not get all condor quotes for {symbol}")
                return None
            
            # Calculate net credit (sell short strikes, buy long strikes)
            net_credit = (call_short_quote.mid - call_long_quote.mid + 
                         put_short_quote.mid - put_long_quote.mid)
            
            # Calculate max profit and max loss
            call_width = call_long - call_short
            put_width = put_short - put_long
            max_width = max(call_width, put_width)
            max_loss = max_width - net_credit
            
            # Liquidity check
            min_volume = 10
            total_volume = (call_short_quote.volume + call_long_quote.volume + 
                          put_short_quote.volume + put_long_quote.volume)
            
            return {
                'type': 'iron_condor',
                'symbol': symbol,
                'expiry': expiry,
                'underlying_price': underlying_price,
                'legs': [
                    {'strike': put_long, 'right': 'P', 'action': 'BUY', 'quote': put_long_quote},
                    {'strike': put_short, 'right': 'P', 'action': 'SELL', 'quote': put_short_quote},
                    {'strike': call_short, 'right': 'C', 'action': 'SELL', 'quote': call_short_quote},
                    {'strike': call_long, 'right': 'C', 'action': 'BUY', 'quote': call_long_quote}
                ],
                'net_credit': net_credit,
                'max_profit': net_credit,
                'max_loss': max_loss,
                'breakeven_low': put_short - net_credit,
                'breakeven_high': call_short + net_credit,
                'prob_profit': self._estimate_prob_profit(underlying_price, put_short - net_credit, 
                                                        call_short + net_credit, expected_move),
                'total_volume': total_volume,
                'is_liquid': total_volume >= min_volume,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error building iron condor for {symbol}: {e}")
            return None

    def build_bull_put_spread(self, symbol: str, expiry: str, target_delta: float = 0.10,
                             width: int = 5, min_credit: float = 0.15) -> Optional[Dict]:
        """
        Build bull put spread for Bot A PUT-Lite strategy
        
        Args:
            symbol: Underlying symbol  
            expiry: Option expiry
            target_delta: Target delta for short put (0.05-0.15)
            width: Strike width in dollars
            min_credit: Minimum credit required
            
        Returns:
            Dict with spread details
        """
        try:
            snapshot = self.broker.get_market_snapshot(symbol)
            if not snapshot:
                return None
            
            underlying_price = snapshot.price
            
            # Get option quotes for puts below current price
            chain_info = self.broker.get_option_chain(symbol)
            strikes = [s for s in chain_info.get('strikes', []) if s < underlying_price]
            strikes.sort(reverse=True)  # Highest first
            
            # Get quotes for potential short strikes
            quotes = self.get_option_quotes(symbol, expiry, strikes[:10])  # Top 10 strikes
            
            # Find strike with target delta
            best_spread = None
            best_delta_diff = float('inf')
            
            for quote in quotes:
                if quote.right != 'P' or not quote.delta:
                    continue
                    
                delta_diff = abs(abs(quote.delta) - target_delta)
                if delta_diff > best_delta_diff:
                    continue
                    
                short_strike = quote.strike
                long_strike = short_strike - width
                
                # Get long put quote
                long_quotes = self.get_option_quotes(symbol, expiry, [long_strike])
                long_quote = next((q for q in long_quotes if q.right == 'P'), None)
                
                if not long_quote:
                    continue
                    
                # Calculate spread credit
                net_credit = quote.mid - long_quote.mid
                
                if net_credit < min_credit:
                    continue
                    
                # Check liquidity
                total_volume = quote.volume + long_quote.volume
                if total_volume < 20:  # Minimum volume threshold
                    continue
                
                max_loss = width - net_credit
                
                spread = {
                    'type': 'bull_put_spread',
                    'symbol': symbol,
                    'expiry': expiry,
                    'underlying_price': underlying_price,
                    'legs': [
                        {'strike': long_strike, 'right': 'P', 'action': 'BUY', 'quote': long_quote},
                        {'strike': short_strike, 'right': 'P', 'action': 'SELL', 'quote': quote}
                    ],
                    'net_credit': net_credit,
                    'max_profit': net_credit,
                    'max_loss': max_loss,
                    'breakeven': short_strike - net_credit,
                    'short_delta': abs(quote.delta),
                    'prob_profit': self._estimate_put_spread_prob(underlying_price, short_strike, net_credit),
                    'total_volume': total_volume,
                    'is_liquid': total_volume >= 20,
                    'timestamp': datetime.now()
                }
                
                if delta_diff < best_delta_diff:
                    best_delta_diff = delta_diff
                    best_spread = spread
            
            return best_spread
            
        except Exception as e:
            logger.error(f"Error building bull put spread for {symbol}: {e}")
            return None

    def build_covered_call(self, symbol: str, expiry: str, shares_owned: int,
                          target_delta: float = 0.30, min_premium: float = 0.50) -> Optional[Dict]:
        """
        Build covered call for Bot B Buy-Write strategy
        
        Args:
            symbol: Underlying symbol
            expiry: Option expiry  
            shares_owned: Number of shares owned
            target_delta: Target delta for short call
            min_premium: Minimum premium per share
            
        Returns:
            Dict with covered call details
        """
        try:
            snapshot = self.broker.get_market_snapshot(symbol)
            if not snapshot:
                return None
            
            underlying_price = snapshot.price
            
            # Get call strikes above current price
            chain_info = self.broker.get_option_chain(symbol)
            strikes = [s for s in chain_info.get('strikes', []) if s > underlying_price]
            strikes.sort()  # Lowest first
            
            # Get quotes for potential call strikes
            quotes = self.get_option_quotes(symbol, expiry, strikes[:10])
            
            # Find best call to sell
            best_call = None
            best_delta_diff = float('inf')
            
            for quote in quotes:
                if quote.right != 'C' or not quote.delta:
                    continue
                    
                if quote.mid < min_premium:
                    continue
                    
                delta_diff = abs(quote.delta - target_delta)
                if delta_diff < best_delta_diff:
                    best_delta_diff = delta_diff
                    best_call = quote
            
            if not best_call:
                return None
            
            # Calculate number of contracts (1 contract = 100 shares)
            contracts = min(shares_owned // 100, 10)  # Max 10 contracts
            
            if contracts == 0:
                return None
            
            total_premium = best_call.mid * contracts * 100
            upside_capture = best_call.strike - underlying_price
            
            return {
                'type': 'covered_call',
                'symbol': symbol,
                'expiry': expiry,
                'underlying_price': underlying_price,
                'shares_owned': shares_owned,
                'contracts': contracts,
                'strike': best_call.strike,
                'premium_per_share': best_call.mid,
                'total_premium': total_premium,
                'call_delta': best_call.delta,
                'upside_capture': upside_capture,
                'max_profit': total_premium + (upside_capture * contracts * 100),
                'breakeven': underlying_price - best_call.mid,
                'volume': best_call.volume,
                'is_liquid': best_call.volume >= 50,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error building covered call for {symbol}: {e}")
            return None

    def validate_spread_liquidity(self, spread: Dict) -> bool:
        """Validate spread has sufficient liquidity for execution"""
        if not spread.get('is_liquid', False):
            return False
            
        # Check individual leg volumes
        total_volume = spread.get('total_volume', 0)
        min_volume = 20 if spread['type'] == 'bull_put_spread' else 40
        
        return total_volume >= min_volume

    def _estimate_prob_profit(self, underlying: float, breakeven_low: float, 
                            breakeven_high: float, expected_move: float) -> float:
        """Estimate probability of profit for iron condor using simple heuristic"""
        try:
            # Calculate distance from current price to breakevens as % of expected move
            range_width = breakeven_high - breakeven_low
            expected_range = expected_move * 2  # Expected move both ways
            
            # Simple heuristic: wider spreads relative to expected move = higher prob profit
            if range_width > expected_range * 1.5:
                prob = 0.75
            elif range_width > expected_range:
                prob = 0.65
            elif range_width > expected_range * 0.8:
                prob = 0.55
            else:
                prob = 0.45
            
            return max(0.1, min(0.9, prob))
            
        except:
            return 0.5  # Default neutral probability

    def _estimate_put_spread_prob(self, underlying: float, short_strike: float, 
                                 credit: float) -> float:
        """Estimate probability of profit for put spread"""
        try:
            breakeven = short_strike - credit
            prob = (underlying - breakeven) / underlying
            return max(0.1, min(0.9, prob))
        except:
            return 0.5


# Global analyzer instance
_analyzer = None

def get_options_analyzer() -> OptionsAnalyzer:
    """Get the global options analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = OptionsAnalyzer()
    return _analyzer