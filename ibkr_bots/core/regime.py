"""
Market regime detection module.
Analyzes realized volatility vs expected moves, IV rank, VWAP bands, and breadth.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics
import json
import os

from .broker import get_broker
from .options import get_options_analyzer

logger = logging.getLogger(__name__)


@dataclass
class RegimeSignals:
    """Market regime analysis signals"""
    symbol: str
    rv_vs_em_ratio: Optional[float] = None
    iv_rank: Optional[float] = None
    vwap_signal: Optional[str] = None  # 'above', 'below', 'neutral'
    breadth_signal: Optional[str] = None  # 'bullish', 'bearish', 'neutral'
    overall_regime: str = 'unknown'  # 'calm', 'volatile', 'trending', 'reverting'
    entry_allowed: bool = False
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class RegimeAnalyzer:
    """Market regime detection and analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.broker = get_broker()
        self.options_analyzer = get_options_analyzer()
        self.price_cache = {}  # Cache recent prices for calculations
        
        # Get filter thresholds from config
        filters = config.get('filters', {})
        self.iv_rank_min = filters.get('iv_rank_min', 45)
        self.rv_em_min = filters.get('rv_em_min', 1.1)
        self.vwap_band_sigma = filters.get('vwap_band_sigma', 0.5)
        
        logger.info(f"Regime filters: IV rank ≥ {self.iv_rank_min}%, "
                   f"RV/EM ≥ {self.rv_em_min}, VWAP σ = {self.vwap_band_sigma}")
    
    def calculate_realized_volatility(self, symbol: str, lookback_minutes: int = 60) -> Optional[float]:
        """
        Calculate realized volatility from recent price movements
        
        Args:
            symbol: Symbol to analyze
            lookback_minutes: Minutes to look back for calculation
            
        Returns:
            Realized volatility (annualized) or None
        """
        try:
            # For simplicity, we'll use session high/low range as proxy for RV
            # In production, you'd want minute-by-minute price data
            
            snapshot = self.broker.get_market_snapshot(symbol)
            if not snapshot:
                return None
            
            current_price = snapshot.price
            
            # Get intraday range from ticker if available
            ticker = self.broker.market_data_stock(symbol)
            if ticker and hasattr(ticker, 'high') and hasattr(ticker, 'low'):
                session_high = ticker.high
                session_low = ticker.low
                
                if session_high > 0 and session_low > 0:
                    # Calculate range-based volatility estimate
                    range_pct = (session_high - session_low) / current_price
                    
                    # Annualize assuming this range represents ~6 trading hours
                    # and 252 trading days per year
                    trading_hours_per_day = 6.5
                    hours_in_range = 6
                    periods_per_year = 252 * (trading_hours_per_day / hours_in_range)
                    
                    realized_vol = range_pct * (periods_per_year ** 0.5)
                    
                    logger.debug(f"Realized vol for {symbol}: {realized_vol:.1%} "
                                f"(range: {session_low:.2f}-{session_high:.2f})")
                    
                    return realized_vol
            
            # Fallback: use recent price changes if available
            if symbol in self.price_cache:
                prices = self.price_cache[symbol]
                if len(prices) >= 5:
                    returns = []
                    for i in range(1, len(prices)):
                        ret = (prices[i] - prices[i-1]) / prices[i-1]
                        returns.append(ret)
                    
                    if returns:
                        vol_estimate = statistics.stdev(returns) * (252 ** 0.5)  # Annualize
                        return vol_estimate
            
            # Update price cache
            now = datetime.now()
            if symbol not in self.price_cache:
                self.price_cache[symbol] = []
            
            # Add current price with timestamp
            self.price_cache[symbol].append(current_price)
            
            # Keep only recent prices (last hour)
            if len(self.price_cache[symbol]) > 60:
                self.price_cache[symbol] = self.price_cache[symbol][-60:]
            
            return None  # Not enough data yet
            
        except Exception as e:
            logger.error(f"Error calculating realized volatility for {symbol}: {e}")
            return None
    
    def calculate_vwap_bands(self, symbol: str) -> Dict[str, float]:
        """
        Calculate VWAP and bands (simplified version)
        
        Args:
            symbol: Symbol to analyze
            
        Returns:
            Dict with vwap, upper_band, lower_band
        """
        try:
            # For MVP, we'll use a simplified VWAP based on current price
            # In production, you'd calculate true VWAP from volume-weighted prices
            
            snapshot = self.broker.get_market_snapshot(symbol)
            if not snapshot:
                return {}
            
            current_price = snapshot.price
            
            # Estimate intraday volatility for bands
            ticker = self.broker.market_data_stock(symbol)
            if ticker and hasattr(ticker, 'high') and hasattr(ticker, 'low'):
                session_high = ticker.high or current_price
                session_low = ticker.low or current_price
                
                # Use session range as volatility proxy
                range_size = session_high - session_low
                sigma = range_size / 4  # Rough estimate
                
                # For simplicity, assume VWAP ≈ (high + low + close) / 3
                estimated_vwap = (session_high + session_low + current_price) / 3
                
                upper_band = estimated_vwap + (self.vwap_band_sigma * sigma)
                lower_band = estimated_vwap - (self.vwap_band_sigma * sigma)
                
                return {
                    'vwap': estimated_vwap,
                    'upper_band': upper_band,
                    'lower_band': lower_band,
                    'current_price': current_price
                }
            
            # Fallback: use current price as VWAP with narrow bands
            return {
                'vwap': current_price,
                'upper_band': current_price * 1.002,  # 0.2% bands
                'lower_band': current_price * 0.998,
                'current_price': current_price
            }
            
        except Exception as e:
            logger.error(f"Error calculating VWAP bands for {symbol}: {e}")
            return {}
    
    def analyze_regime(self, symbol: str, expiry: str = None) -> RegimeSignals:
        """
        Perform comprehensive regime analysis
        
        Args:
            symbol: Symbol to analyze
            expiry: Option expiry for expected move calculation
            
        Returns:
            RegimeSignals object
        """
        signals = RegimeSignals(symbol=symbol)
        
        try:
            # Get IV rank
            iv_rank = self.options_analyzer.iv_rank(symbol)
            signals.iv_rank = iv_rank
            
            # Calculate RV vs EM ratio
            if expiry:
                expected_move = self.options_analyzer.expected_move_from_chain(symbol, expiry)
                realized_vol = self.calculate_realized_volatility(symbol)
                
                if expected_move and realized_vol:
                    # Convert EM to annualized vol equivalent for comparison
                    em_vol_equiv = expected_move.percent_em
                    signals.rv_vs_em_ratio = realized_vol / em_vol_equiv
                    
                    logger.debug(f"RV/EM for {symbol}: {signals.rv_vs_em_ratio:.2f} "
                                f"(RV: {realized_vol:.1%}, EM: {em_vol_equiv:.1%})")
            
            # VWAP analysis
            vwap_data = self.calculate_vwap_bands(symbol)
            if vwap_data:
                current = vwap_data['current_price']
                vwap = vwap_data['vwap']
                upper = vwap_data['upper_band']
                lower = vwap_data['lower_band']
                
                if current > upper:
                    signals.vwap_signal = 'above'
                elif current < lower:
                    signals.vwap_signal = 'below'
                else:
                    signals.vwap_signal = 'neutral'
            
            # Determine overall regime
            signals.overall_regime = self._classify_regime(signals)
            
            # Check if entry conditions are met
            signals.entry_allowed = self._check_entry_filters(signals)
            
            logger.info(f"Regime analysis for {symbol}: {signals.overall_regime}, "
                       f"Entry allowed: {signals.entry_allowed}")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in regime analysis for {symbol}: {e}")
            return signals
    
    def _classify_regime(self, signals: RegimeSignals) -> str:
        """Classify market regime based on signals"""
        
        # High IV rank suggests elevated volatility
        if signals.iv_rank and signals.iv_rank > 75:
            if signals.rv_vs_em_ratio and signals.rv_vs_em_ratio < 0.8:
                return 'volatile'  # High IV but low realized - good for selling vol
            else:
                return 'trending'  # High IV and high realized - trending market
        
        # Low IV rank suggests calm conditions
        elif signals.iv_rank and signals.iv_rank < 25:
            return 'calm'  # Low volatility environment
        
        # Medium IV with different RV patterns
        elif signals.rv_vs_em_ratio:
            if signals.rv_vs_em_ratio < 0.8:
                return 'reverting'  # Realized < implied - mean reverting
            elif signals.rv_vs_em_ratio > 1.2:
                return 'trending'  # Realized > implied - trending
            else:
                return 'neutral'  # Balanced
        
        return 'unknown'
    
    def _check_entry_filters(self, signals: RegimeSignals) -> bool:
        """Check if all entry filters are satisfied"""
        
        # IV rank filter
        if signals.iv_rank is None or signals.iv_rank < self.iv_rank_min:
            logger.debug(f"IV rank filter failed: {signals.iv_rank} < {self.iv_rank_min}")
            return False
        
        # RV/EM ratio filter (for vol selling strategies)
        if signals.rv_vs_em_ratio is None or signals.rv_vs_em_ratio < self.rv_em_min:
            logger.debug(f"RV/EM filter failed: {signals.rv_vs_em_ratio} < {self.rv_em_min}")
            return False
        
        # VWAP filter - prefer trading when not at extremes
        if signals.vwap_signal and signals.vwap_signal != 'neutral':
            logger.debug(f"VWAP filter: price is {signals.vwap_signal} band, proceeding with caution")
            # Don't fail completely, but note the condition
        
        logger.info(f"All entry filters passed for {signals.symbol}")
        return True
    
    def get_market_breadth_signal(self) -> str:
        """
        Get broad market breadth signal (simplified)
        
        Returns:
            'bullish', 'bearish', or 'neutral'
        """
        try:
            # Simple breadth check using SPY vs QQQ performance
            spy_data = self.broker.get_market_snapshot('SPY')
            qqq_data = self.broker.get_market_snapshot('QQQ')
            
            if not spy_data or not qqq_data:
                return 'neutral'
            
            # For MVP, just return neutral - more sophisticated breadth
            # analysis would require additional data feeds
            return 'neutral'
            
        except Exception as e:
            logger.warning(f"Error getting breadth signal: {e}")
            return 'neutral'


# Global analyzer instance
_regime_analyzer = None

def get_regime_analyzer(config: Dict[str, Any]) -> RegimeAnalyzer:
    """Get the global regime analyzer instance"""
    global _regime_analyzer
    if _regime_analyzer is None:
        _regime_analyzer = RegimeAnalyzer(config)
    return _regime_analyzer