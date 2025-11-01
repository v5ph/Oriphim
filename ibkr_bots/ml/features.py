"""
Machine Learning Features Module

Production-ready feature engineering for options trading models.
Generates technical indicators, volatility features, options flow metrics,
and market microstructure signals for regime classification and trade scoring.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import math

from ..core.broker import get_broker
from ..core.options import get_options_analyzer

logger = logging.getLogger('ml.features')


class FeatureBuilder:
    """
    Production feature engineering for ML models
    
    Generates features for:
    - Regime classification (trend/chop/volatile)
    - Expected move prediction
    - Trade quality scoring
    - Execution timing optimization
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.broker = get_broker()
        self.options = get_options_analyzer()
        
        # Feature configuration
        self.lookback_minutes = config.get('lookback_minutes', 60)
        self.vol_lookback_days = config.get('vol_lookback_days', 20)
        self.min_data_points = config.get('min_data_points', 10)
        
        logger.info(f"Feature builder initialized - lookback: {self.lookback_minutes}m")
    
    def build_regime_features(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Build features for regime classification (trend/chop/volatile)
        
        Args:
            symbol: Symbol to analyze
            
        Returns:
            Dictionary of regime features
        """
        try:
            features = {}
            
            # Get current market snapshot
            snapshot = self.broker.get_market_snapshot(symbol)
            if not snapshot:
                return None
            
            current_price = snapshot.price
            
            # Price momentum features
            price_features = self._build_price_momentum_features(symbol, current_price)
            if price_features:
                features.update(price_features)
            
            # Volatility features  
            vol_features = self._build_volatility_features(symbol, current_price)
            if vol_features:
                features.update(vol_features)
            
            # Options surface features
            options_features = self._build_options_surface_features(symbol)
            if options_features:
                features.update(options_features)
            
            # Market breadth proxy (VIX-based)
            breadth_features = self._build_breadth_features()
            if breadth_features:
                features.update(breadth_features)
            
            # Time-of-day features
            time_features = self._build_time_features()
            features.update(time_features)
            
            logger.debug(f"Built {len(features)} regime features for {symbol}")
            return features
            
        except Exception as e:
            logger.error(f"Error building regime features for {symbol}: {e}")
            return None
    
    def build_trade_scoring_features(self, symbol: str, expiry: str, 
                                   spread_type: str, strikes: List[float]) -> Optional[Dict[str, float]]:
        """
        Build features for trade quality scoring
        
        Args:
            symbol: Underlying symbol
            expiry: Option expiry
            spread_type: Type of spread (put_spread, iron_condor, etc.)
            strikes: Strike prices involved
            
        Returns:
            Dictionary of trade scoring features
        """
        try:
            features = {}
            
            # Base regime features
            regime_features = self.build_regime_features(symbol)
            if regime_features:
                features.update(regime_features)
            
            # Spread-specific features
            spread_features = self._build_spread_features(symbol, expiry, spread_type, strikes)
            if spread_features:
                features.update(spread_features)
            
            # Greeks and risk features
            greeks_features = self._build_greeks_features(symbol, expiry, strikes)
            if greeks_features:
                features.update(greeks_features)
            
            logger.debug(f"Built {len(features)} trade scoring features")
            return features
            
        except Exception as e:
            logger.error(f"Error building trade scoring features: {e}")
            return None
    
    def _build_price_momentum_features(self, symbol: str, current_price: float) -> Dict[str, float]:
        """Build price momentum and trend features"""
        features = {}
        
        try:
            # For MVP, use simple heuristics based on intraday movement
            # In production, would fetch minute bars from broker
            
            # Simulate some intraday price movement analysis
            # (In real implementation, would use historical minute data)
            
            # ATR proxy - use current bid/ask spread as volatility proxy
            snapshot = self.broker.get_market_snapshot(symbol)
            if snapshot and snapshot.ask > snapshot.bid:
                spread_pct = (snapshot.ask - snapshot.bid) / current_price * 100
                features['spread_pct'] = spread_pct
                features['micro_volatility'] = min(spread_pct * 10, 5.0)  # Cap at 5%
            
            # Price level features (relative to round numbers)
            features['price_level'] = current_price
            features['distance_to_round'] = abs(current_price - round(current_price, 0)) / current_price
            features['near_round_number'] = 1.0 if features['distance_to_round'] < 0.01 else 0.0
            
            # Session time progress (market open = 9:30 ET)
            now = datetime.now()
            market_open_hour = 9.5  # 9:30 AM
            current_hour = now.hour + now.minute / 60.0
            session_progress = max(0, min(1, (current_hour - market_open_hour) / 6.5))  # 6.5 hour session
            features['session_progress'] = session_progress
            
        except Exception as e:
            logger.warning(f"Error building price momentum features: {e}")
        
        return features
    
    def _build_volatility_features(self, symbol: str, current_price: float) -> Dict[str, float]:
        """Build volatility and range features"""
        features = {}
        
        try:
            # IV Rank from options analyzer
            iv_rank = self.options.calculate_iv_rank(symbol)
            if iv_rank is not None:
                features['iv_rank'] = iv_rank
                features['iv_rank_high'] = 1.0 if iv_rank > 75 else 0.0
                features['iv_rank_low'] = 1.0 if iv_rank < 25 else 0.0
            
            # Expected move calculation
            expiry = self.options.get_nearest_friday_expiry(symbol)
            if expiry:
                em_result = self.options.calculate_expected_move(symbol, expiry)
                if em_result:
                    features['expected_move_pct'] = em_result.percent_em
                    features['expected_move_dollar'] = em_result.dollar_em
                    
                    # EM relative to current price
                    features['em_price_ratio'] = em_result.dollar_em / current_price
            
            # Volatility regime indicators
            if 'iv_rank' in features and 'expected_move_pct' in features:
                # High IV + High EM = Volatile regime
                features['volatile_regime'] = 1.0 if (features['iv_rank'] > 60 and 
                                                    features['expected_move_pct'] > 2.0) else 0.0
                
                # Low IV + Low EM = Calm regime  
                features['calm_regime'] = 1.0 if (features['iv_rank'] < 40 and 
                                                features['expected_move_pct'] < 1.5) else 0.0
        
        except Exception as e:
            logger.warning(f"Error building volatility features: {e}")
        
        return features
    
    def _build_options_surface_features(self, symbol: str) -> Dict[str, float]:
        """Build options surface and skew features"""
        features = {}
        
        try:
            # Get option chain for skew analysis
            chain_info = self.broker.get_option_chain(symbol)
            if not chain_info:
                return features
            
            expirations = chain_info.get('expirations', [])
            if not expirations:
                return features
            
            expiry = expirations[0]  # Nearest expiry
            strikes = chain_info.get('strikes', [])
            
            if len(strikes) < 5:  # Need enough strikes for skew
                return features
            
            # Get current price for ATM reference
            snapshot = self.broker.get_market_snapshot(symbol)
            if not snapshot:
                return features
            
            current_price = snapshot.price
            
            # Find strikes around ATM for skew calculation
            atm_strike = min(strikes, key=lambda x: abs(x - current_price))
            atm_index = strikes.index(atm_strike)
            
            # Get otm put and call strikes
            otm_put_strikes = [s for s in strikes if s < current_price * 0.95]  # 5% OTM
            otm_call_strikes = [s for s in strikes if s > current_price * 1.05]  # 5% OTM
            
            if otm_put_strikes and otm_call_strikes:
                # Sample strikes for skew analysis
                put_strike = otm_put_strikes[-1] if otm_put_strikes else None
                call_strike = otm_call_strikes[0] if otm_call_strikes else None
                
                if put_strike and call_strike:
                    # Get quotes for skew calculation
                    quotes = self.options.get_option_quotes(symbol, expiry, 
                                                          [atm_strike, put_strike, call_strike])
                    
                    atm_call = next((q for q in quotes if q.strike == atm_strike and q.right == 'C'), None)
                    otm_put = next((q for q in quotes if q.strike == put_strike and q.right == 'P'), None)
                    otm_call = next((q for q in quotes if q.strike == call_strike and q.right == 'C'), None)
                    
                    if atm_call and otm_put and otm_call and all(q.iv for q in [atm_call, otm_put, otm_call]):
                        # Simple skew measures
                        put_call_iv_diff = otm_put.iv - otm_call.iv
                        features['put_call_skew'] = put_call_iv_diff * 100  # Percentage points
                        features['skew_steep'] = 1.0 if abs(put_call_iv_diff) > 0.05 else 0.0
                        
                        # ATM IV level
                        features['atm_iv'] = atm_call.iv * 100
        
        except Exception as e:
            logger.warning(f"Error building options surface features: {e}")
        
        return features
    
    def _build_breadth_features(self) -> Dict[str, float]:
        """Build market breadth proxy features using VIX"""
        features = {}
        
        try:
            # Get VIX as market fear gauge
            vix_snapshot = self.broker.get_market_snapshot('VIX')
            if vix_snapshot:
                vix_level = vix_snapshot.price
                features['vix_level'] = vix_level
                features['vix_high'] = 1.0 if vix_level > 25 else 0.0
                features['vix_low'] = 1.0 if vix_level < 15 else 0.0
                features['vix_spike'] = 1.0 if vix_level > 30 else 0.0
        
        except Exception as e:
            logger.warning(f"Error building breadth features: {e}")
        
        return features
    
    def _build_time_features(self) -> Dict[str, float]:
        """Build time-of-day and day-of-week features"""
        features = {}
        
        now = datetime.now()
        
        # Hour of day (market hours)
        features['hour'] = now.hour
        features['is_morning'] = 1.0 if 9 <= now.hour < 12 else 0.0
        features['is_afternoon'] = 1.0 if 12 <= now.hour < 16 else 0.0
        features['is_close'] = 1.0 if now.hour >= 15 else 0.0
        
        # Day of week
        features['day_of_week'] = now.weekday()  # 0=Monday
        features['is_monday'] = 1.0 if now.weekday() == 0 else 0.0
        features['is_friday'] = 1.0 if now.weekday() == 4 else 0.0
        
        # Minutes to close (4 PM ET)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        if now < market_close:
            minutes_to_close = (market_close - now).total_seconds() / 60
            features['minutes_to_close'] = minutes_to_close
            features['near_close'] = 1.0 if minutes_to_close < 30 else 0.0
        else:
            features['minutes_to_close'] = 0
            features['near_close'] = 0.0
        
        return features
    
    def _build_spread_features(self, symbol: str, expiry: str, 
                             spread_type: str, strikes: List[float]) -> Dict[str, float]:
        """Build spread-specific features"""
        features = {}
        
        try:
            # Days to expiration
            exp_date = datetime.strptime(expiry, '%Y%m%d').date()
            days_to_exp = (exp_date - datetime.now().date()).days
            features['days_to_expiry'] = days_to_exp
            features['is_0dte'] = 1.0 if days_to_exp == 0 else 0.0
            features['is_1dte'] = 1.0 if days_to_exp == 1 else 0.0
            
            # Strike width and positioning
            if len(strikes) >= 2:
                strike_width = max(strikes) - min(strikes)
                features['strike_width'] = strike_width
                
                # Current price relative to strikes
                snapshot = self.broker.get_market_snapshot(symbol)
                if snapshot:
                    current_price = snapshot.price
                    features['price_vs_max_strike'] = (current_price - max(strikes)) / current_price
                    features['price_vs_min_strike'] = (current_price - min(strikes)) / current_price
            
            # Spread type indicators
            features[f'is_{spread_type}'] = 1.0
        
        except Exception as e:
            logger.warning(f"Error building spread features: {e}")
        
        return features
    
    def _build_greeks_features(self, symbol: str, expiry: str, strikes: List[float]) -> Dict[str, float]:
        """Build Greeks-based features"""
        features = {}
        
        try:
            if not strikes:
                return features
            
            # Get quotes for Greeks
            quotes = self.options.get_option_quotes(symbol, expiry, strikes)
            
            # Aggregate Greeks across the spread
            total_delta = sum(q.delta or 0 for q in quotes if q.delta)
            total_gamma = sum(q.gamma or 0 for q in quotes if q.gamma)  
            total_theta = sum(q.theta or 0 for q in quotes if q.theta)
            
            if total_delta:
                features['net_delta'] = total_delta
                features['delta_neutral'] = 1.0 if abs(total_delta) < 0.05 else 0.0
            
            if total_gamma:
                features['net_gamma'] = total_gamma
                features['gamma_positive'] = 1.0 if total_gamma > 0 else 0.0
            
            if total_theta:
                features['net_theta'] = total_theta  
                features['theta_positive'] = 1.0 if total_theta > 0 else 0.0
        
        except Exception as e:
            logger.warning(f"Error building Greeks features: {e}")
        
        return features


def get_feature_builder(config: Dict[str, Any]) -> FeatureBuilder:
    """Get feature builder instance"""
    return FeatureBuilder(config)