"""
Machine Learning Labels Module

Production label generation for supervised learning models:
- Trade outcome labels (TP/SL classification)
- P&L regression targets  
- Regime classification labels
- Feature importance tracking
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

logger = logging.getLogger('ml.labels')


class LabelGenerator:
    """
    Production label generation for ML model training
    
    Creates labels for:
    - Binary classification (profitable/unprofitable trades)
    - Regression (P&L magnitude prediction)
    - Multi-class (regime classification based on realized outcomes)
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Label generation parameters
        self.tp_threshold = config.get('tp_threshold', 0.50)  # 50% of max profit
        self.sl_threshold = config.get('sl_threshold', 0.75)  # 75% of max loss
        self.regime_lookback_hours = config.get('regime_lookback_hours', 2)
        
        logger.info("Label generator initialized for production")
    
    def generate_trade_outcome_labels(self, trades: List[Dict[str, Any]]) -> List[Tuple[Dict[str, float], bool]]:
        """
        Generate binary labels for trade success (TP hit before SL)
        
        Args:
            trades: List of completed trade dictionaries with entry/exit data
            
        Returns:
            List of (features, outcome) tuples for training
        """
        training_data = []
        
        try:
            for trade in trades:
                if not self._is_complete_trade(trade):
                    continue
                
                # Extract entry features  
                entry_features = trade.get('entry_features', {})
                if not entry_features:
                    continue
                
                # Determine outcome
                outcome = self._classify_trade_outcome(trade)
                if outcome is not None:
                    training_data.append((entry_features, outcome))
            
            logger.info(f"Generated {len(training_data)} trade outcome labels")
            return training_data
            
        except Exception as e:
            logger.error(f"Error generating trade outcome labels: {e}")
            return []
    
    def generate_pnl_regression_labels(self, trades: List[Dict[str, Any]]) -> List[Tuple[Dict[str, float], float]]:
        """
        Generate P&L regression labels for magnitude prediction
        
        Args:
            trades: List of completed trade dictionaries
            
        Returns:
            List of (features, pnl) tuples for training
        """
        training_data = []
        
        try:
            for trade in trades:
                if not self._is_complete_trade(trade):
                    continue
                
                entry_features = trade.get('entry_features', {})
                final_pnl = trade.get('final_pnl', 0.0)
                
                if entry_features and final_pnl is not None:
                    # Normalize P&L by risk amount for fair comparison
                    risk_amount = abs(trade.get('max_loss', 1.0))
                    normalized_pnl = final_pnl / risk_amount if risk_amount > 0 else 0.0
                    
                    training_data.append((entry_features, normalized_pnl))
            
            logger.info(f"Generated {len(training_data)} P&L regression labels")
            return training_data
            
        except Exception as e:
            logger.error(f"Error generating P&L regression labels: {e}")
            return []
    
    def generate_regime_labels(self, market_sessions: List[Dict[str, Any]]) -> List[Tuple[Dict[str, float], str]]:
        """
        Generate regime classification labels based on realized market behavior
        
        Args:
            market_sessions: List of market session data with features and outcomes
            
        Returns:
            List of (features, regime) tuples for training
        """
        training_data = []
        
        try:
            for session in market_sessions:
                session_features = session.get('features', {})
                if not session_features:
                    continue
                
                # Classify regime based on realized behavior
                regime = self._classify_session_regime(session)
                if regime:
                    training_data.append((session_features, regime))
            
            logger.info(f"Generated {len(training_data)} regime classification labels")
            return training_data
            
        except Exception as e:
            logger.error(f"Error generating regime labels: {e}")
            return []
    
    def generate_expected_move_labels(self, sessions: List[Dict[str, Any]]) -> List[Tuple[Dict[str, float], float]]:
        """
        Generate expected move regression labels using realized moves
        
        Args:
            sessions: Market sessions with predicted vs realized moves
            
        Returns:
            List of (features, realized_move) tuples
        """
        training_data = []
        
        try:
            for session in sessions:
                features = session.get('features', {})
                realized_move = session.get('realized_move_pct')
                
                if features and realized_move is not None:
                    training_data.append((features, realized_move))
            
            logger.info(f"Generated {len(training_data)} expected move labels")
            return training_data
            
        except Exception as e:
            logger.error(f"Error generating expected move labels: {e}")
            return []
    
    def _is_complete_trade(self, trade: Dict[str, Any]) -> bool:
        """Check if trade has complete data for labeling"""
        required_fields = ['entry_time', 'exit_time', 'final_pnl', 'entry_features']
        return all(field in trade and trade[field] is not None for field in required_fields)
    
    def _classify_trade_outcome(self, trade: Dict[str, Any]) -> Optional[bool]:
        """
        Classify trade as successful (True) or unsuccessful (False)
        Based on whether TP was hit before SL
        """
        try:
            exit_reason = trade.get('exit_reason', 'unknown')
            final_pnl = trade.get('final_pnl', 0.0)
            max_profit = trade.get('max_profit', 0.0)
            max_loss = trade.get('max_loss', 0.0)
            
            # Direct exit reason classification
            if exit_reason == 'take_profit':
                return True
            elif exit_reason == 'stop_loss':
                return False
            elif exit_reason == 'time_stop':
                # For time stops, check if profitable
                return final_pnl > 0
            
            # Fallback: classify by P&L relative to targets
            if max_profit > 0 and final_pnl >= (max_profit * self.tp_threshold):
                return True
            elif max_loss < 0 and final_pnl <= (max_loss * self.sl_threshold):
                return False
            else:
                # Unclear outcome - exclude from training
                return None
                
        except Exception as e:
            logger.warning(f"Error classifying trade outcome: {e}")
            return None
    
    def _classify_session_regime(self, session: Dict[str, Any]) -> Optional[str]:
        """
        Classify market session regime based on realized behavior
        
        Returns:
            'trend' - strong directional movement
            'chop' - range-bound, mean-reverting
            'volatile' - high movement, unstable
        """
        try:
            # Extract session metrics
            price_range_pct = session.get('price_range_pct', 0)
            direction_consistency = session.get('direction_consistency', 0.5) 
            volatility_spike = session.get('volatility_spike', False)
            volume_surge = session.get('volume_surge', False)
            
            # Classification logic
            if volatility_spike or volume_surge:
                return 'volatile'
            elif direction_consistency > 0.7 and price_range_pct > 1.5:
                return 'trend'  # Consistent direction + significant move
            elif price_range_pct < 1.0 and direction_consistency < 0.6:
                return 'chop'   # Small range + back-and-forth
            else:
                # Mixed signals - exclude from training
                return None
                
        except Exception as e:
            logger.warning(f"Error classifying session regime: {e}")
            return None
    
    def create_training_datasets(self, historical_data: Dict[str, List]) -> Dict[str, List]:
        """
        Create complete training datasets for all models
        
        Args:
            historical_data: Dict with 'trades' and 'sessions' lists
            
        Returns:
            Dict with training datasets for each model type
        """
        datasets = {}
        
        # Trade outcome classification dataset
        if 'trades' in historical_data:
            datasets['trade_outcomes'] = self.generate_trade_outcome_labels(
                historical_data['trades']
            )
        
        # P&L regression dataset
        if 'trades' in historical_data:
            datasets['pnl_regression'] = self.generate_pnl_regression_labels(
                historical_data['trades']
            )
        
        # Regime classification dataset
        if 'sessions' in historical_data:
            datasets['regime_classification'] = self.generate_regime_labels(
                historical_data['sessions']
            )
        
        # Expected move regression dataset
        if 'sessions' in historical_data:
            datasets['expected_move'] = self.generate_expected_move_labels(
                historical_data['sessions']
            )
        
        # Summary statistics
        for dataset_name, dataset in datasets.items():
            logger.info(f"{dataset_name}: {len(dataset)} training samples")
        
        return datasets
    
    def save_training_data(self, datasets: Dict[str, List], output_dir: str = 'ml/data'):
        """Save training datasets to files"""
        import os
        import json
        
        os.makedirs(output_dir, exist_ok=True)
        
        for name, dataset in datasets.items():
            if not dataset:
                continue
                
            filepath = os.path.join(output_dir, f"{name}_training.json")
            
            # Convert to JSON-serializable format
            json_data = []
            for features, label in dataset:
                json_data.append({
                    'features': features,
                    'label': label,
                    'timestamp': datetime.now().isoformat()
                })
            
            with open(filepath, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            logger.info(f"Saved {len(json_data)} samples to {filepath}")


def get_label_generator(config: Dict[str, Any] = None) -> LabelGenerator:
    """Get label generator instance"""
    if config is None:
        config = {
            'tp_threshold': 0.50,
            'sl_threshold': 0.75,
            'regime_lookback_hours': 2
        }
    return LabelGenerator(config)