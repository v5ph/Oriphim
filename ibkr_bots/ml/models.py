"""
Machine Learning Models Module

Production ML models for options trading predictions:
- Regime classification (trend/chop/volatile)  
- Expected move prediction
- Trade quality scoring
- Risk anomaly detection
"""

import logging
import json
import os
import pickle
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import numpy as np

logger = logging.getLogger('ml.models')


class BaseModel:
    """Base class for all trading ML models"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.trained = False
        self.model_version = "1.0"
        
        # Model storage paths
        self.models_dir = config.get('models_dir', 'ml/registry/artifacts')
        os.makedirs(self.models_dir, exist_ok=True)
        
    def _prepare_features(self, features: Union[Dict[str, float], List[Dict[str, float]]]) -> np.ndarray:
        """Convert feature dict(s) to numpy array"""
        if isinstance(features, dict):
            features = [features]
        
        if not self.feature_names:
            # First time - establish feature order
            self.feature_names = sorted(features[0].keys())
        
        # Convert to array maintaining feature order
        X = []
        for feature_dict in features:
            row = [feature_dict.get(name, 0.0) for name in self.feature_names]
            X.append(row)
        
        return np.array(X)
    
    def save(self, model_name: str) -> bool:
        """Save model artifacts"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_path = os.path.join(self.models_dir, f"{model_name}_{timestamp}")
            
            # Save model
            model_path = f"{base_path}_model.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            # Save metadata
            metadata = {
                'model_name': model_name,
                'model_version': self.model_version,
                'feature_names': self.feature_names,
                'config': self.config,
                'trained': self.trained,
                'timestamp': timestamp
            }
            
            metadata_path = f"{base_path}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Model saved: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving model {model_name}: {e}")
            return False
    
    @classmethod
    def load(cls, model_name: str, models_dir: str = 'ml/registry/artifacts'):
        """Load latest model version"""
        try:
            # Find latest model file
            model_files = [f for f in os.listdir(models_dir) 
                          if f.startswith(f"{model_name}_") and f.endswith("_model.pkl")]
            
            if not model_files:
                logger.warning(f"No saved model found for {model_name}")
                return None
            
            # Get latest by timestamp
            latest_file = sorted(model_files)[-1]
            model_path = os.path.join(models_dir, latest_file)
            
            # Load metadata
            metadata_file = latest_file.replace('_model.pkl', '_metadata.json')
            metadata_path = os.path.join(models_dir, metadata_file)
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Create instance
            instance = cls(metadata['config'])
            
            # Load model
            with open(model_path, 'rb') as f:
                instance.model = pickle.load(f)
            
            instance.feature_names = metadata['feature_names']
            instance.trained = metadata['trained']
            instance.model_version = metadata['model_version']
            
            logger.info(f"Model loaded: {model_path}")
            return instance
            
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return None


class RegimeClassifier(BaseModel):
    """
    Classifies market regime: trend, chop, volatile
    Uses gradient boosting for robust classification
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.classes = ['trend', 'chop', 'volatile']
        
        # Try to use LightGBM, fallback to sklearn
        self.use_lgb = config.get('use_lightgbm', True)
        
    def train(self, features: List[Dict[str, float]], labels: List[str]) -> bool:
        """Train regime classification model"""
        try:
            X = self._prepare_features(features)
            y = np.array([self.classes.index(label) for label in labels])
            
            if self.use_lgb:
                try:
                    import lightgbm as lgb
                    
                    # LightGBM parameters for trading
                    params = {
                        'objective': 'multiclass',
                        'num_class': len(self.classes),
                        'metric': 'multi_logloss',
                        'boosting_type': 'gbdt',
                        'num_leaves': 31,
                        'learning_rate': 0.1,
                        'feature_fraction': 0.8,
                        'verbosity': -1
                    }
                    
                    train_data = lgb.Dataset(X, label=y)
                    self.model = lgb.train(params, train_data, num_boost_round=100)
                    
                except ImportError:
                    logger.warning("LightGBM not available, using RandomForest")
                    self.use_lgb = False
            
            if not self.use_lgb:
                from sklearn.ensemble import RandomForestClassifier
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                self.model.fit(X, y)
            
            self.trained = True
            logger.info(f"Regime classifier trained on {len(features)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Error training regime classifier: {e}")
            return False
    
    def predict(self, features: Dict[str, float]) -> Optional[Dict[str, float]]:
        """Predict regime probabilities"""
        try:
            if not self.trained or not self.model:
                return None
            
            X = self._prepare_features(features)
            
            if self.use_lgb:
                probs = self.model.predict(X[0].reshape(1, -1))[0]
            else:
                probs = self.model.predict_proba(X)[0]
            
            # Return probabilities for each class
            result = {
                class_name: float(prob) 
                for class_name, prob in zip(self.classes, probs)
            }
            
            # Add predicted class
            result['predicted_regime'] = self.classes[np.argmax(probs)]
            result['confidence'] = float(np.max(probs))
            
            return result
            
        except Exception as e:
            logger.error(f"Error predicting regime: {e}")
            return None


class ExpectedMovePredictor(BaseModel):
    """
    Predicts expected move for better spread positioning
    Uses regression to improve on IV-based estimates
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.target_horizon = config.get('horizon_minutes', 60)  # Minutes to close
        
    def train(self, features: List[Dict[str, float]], 
              realized_moves: List[float]) -> bool:
        """Train expected move prediction model"""
        try:
            X = self._prepare_features(features)
            y = np.array(realized_moves)
            
            # Use gradient boosting regressor
            try:
                import lightgbm as lgb
                
                params = {
                    'objective': 'regression',
                    'metric': 'rmse',
                    'boosting_type': 'gbdt',
                    'num_leaves': 31,
                    'learning_rate': 0.1,
                    'verbosity': -1
                }
                
                train_data = lgb.Dataset(X, label=y)
                self.model = lgb.train(params, train_data, num_boost_round=100)
                
            except ImportError:
                from sklearn.ensemble import GradientBoostingRegressor
                self.model = GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                )
                self.model.fit(X, y)
            
            self.trained = True
            logger.info(f"Expected move predictor trained on {len(features)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Error training expected move predictor: {e}")
            return False
    
    def predict(self, features: Dict[str, float]) -> Optional[Dict[str, float]]:
        """Predict expected move"""
        try:
            if not self.trained or not self.model:
                return None
            
            X = self._prepare_features(features)
            
            if hasattr(self.model, 'predict'):
                # sklearn model
                predicted_move = self.model.predict(X)[0]
            else:
                # LightGBM model  
                predicted_move = self.model.predict(X[0].reshape(1, -1))[0]
            
            return {
                'predicted_move_pct': float(predicted_move),
                'horizon_minutes': self.target_horizon,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting expected move: {e}")
            return None


class TradeScorer(BaseModel):
    """
    Scores trade quality - probability of hitting TP before SL
    Critical for entry filtering
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.min_score_threshold = config.get('min_score', 0.55)
        
    def train(self, features: List[Dict[str, float]], 
              outcomes: List[bool]) -> bool:
        """Train trade scoring model (1=TP hit, 0=SL hit)"""
        try:
            X = self._prepare_features(features)
            y = np.array([1 if outcome else 0 for outcome in outcomes])
            
            # Use classifier for probability estimation
            try:
                import lightgbm as lgb
                
                params = {
                    'objective': 'binary',
                    'metric': 'binary_logloss',
                    'boosting_type': 'gbdt',
                    'num_leaves': 31,
                    'learning_rate': 0.1,
                    'is_unbalance': True,  # Handle class imbalance
                    'verbosity': -1
                }
                
                train_data = lgb.Dataset(X, label=y)
                self.model = lgb.train(params, train_data, num_boost_round=100)
                
            except ImportError:
                from sklearn.ensemble import RandomForestClassifier
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=8,
                    class_weight='balanced',
                    random_state=42
                )
                self.model.fit(X, y)
            
            self.trained = True
            logger.info(f"Trade scorer trained on {len(features)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Error training trade scorer: {e}")
            return False
    
    def predict(self, features: Dict[str, float]) -> Optional[Dict[str, float]]:
        """Score trade quality"""
        try:
            if not self.trained or not self.model:
                return None
            
            X = self._prepare_features(features)
            
            if hasattr(self.model, 'predict_proba'):
                # sklearn model
                prob_success = self.model.predict_proba(X)[0][1]
            else:
                # LightGBM model
                prob_success = self.model.predict(X[0].reshape(1, -1))[0]
            
            return {
                'trade_score': float(prob_success),
                'pass_threshold': prob_success >= self.min_score_threshold,
                'confidence_level': 'high' if prob_success > 0.7 else 'medium' if prob_success > 0.6 else 'low'
            }
            
        except Exception as e:
            logger.error(f"Error scoring trade: {e}")
            return None


class MLEnsemble:
    """
    Ensemble wrapper combining all models for integrated decisions
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.regime_model = None
        self.em_model = None  
        self.trade_scorer = None
        
        # Load or create models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all component models"""
        try:
            # Try to load existing models
            self.regime_model = RegimeClassifier.load('regime_classifier')
            self.em_model = ExpectedMovePredictor.load('expected_move')
            self.trade_scorer = TradeScorer.load('trade_scorer')
            
            # Create new models if loading failed
            if not self.regime_model:
                self.regime_model = RegimeClassifier(self.config)
                logger.info("Created new regime classifier")
                
            if not self.em_model:
                self.em_model = ExpectedMovePredictor(self.config)
                logger.info("Created new expected move predictor")
                
            if not self.trade_scorer:
                self.trade_scorer = TradeScorer(self.config)
                logger.info("Created new trade scorer")
                
        except Exception as e:
            logger.error(f"Error initializing ML ensemble: {e}")
    
    def get_trading_signals(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Get comprehensive trading signals from all models"""
        signals = {
            'timestamp': datetime.now().isoformat(),
            'features_used': len(features)
        }
        
        # Regime classification
        if self.regime_model and self.regime_model.trained:
            regime_result = self.regime_model.predict(features)
            if regime_result:
                signals['regime'] = regime_result
        
        # Expected move prediction
        if self.em_model and self.em_model.trained:
            em_result = self.em_model.predict(features)
            if em_result:
                signals['expected_move'] = em_result
        
        # Trade scoring
        if self.trade_scorer and self.trade_scorer.trained:
            score_result = self.trade_scorer.predict(features)
            if score_result:
                signals['trade_quality'] = score_result
        
        # Overall recommendation
        signals['recommendation'] = self._generate_recommendation(signals)
        
        return signals
    
    def _generate_recommendation(self, signals: Dict[str, Any]) -> str:
        """Generate overall trading recommendation"""
        try:
            # Extract key signals
            regime = signals.get('regime', {})
            trade_quality = signals.get('trade_quality', {})
            
            regime_type = regime.get('predicted_regime', 'unknown')
            regime_confidence = regime.get('confidence', 0.5)
            trade_score = trade_quality.get('trade_score', 0.5)
            
            # Decision logic
            if regime_confidence < 0.6:
                return 'hold'  # Low confidence in regime
            
            if trade_score < 0.55:
                return 'hold'  # Low probability trade
            
            if regime_type == 'volatile' and trade_score > 0.7:
                return 'enter'  # High confidence in volatile market
            elif regime_type == 'chop' and trade_score > 0.65:
                return 'enter'  # Good for range strategies
            elif regime_type == 'trend' and trade_score > 0.6:
                return 'caution'  # Trend can continue
            else:
                return 'hold'
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return 'hold'


# Global ensemble instance
_ml_ensemble = None

def get_ml_ensemble(config: Dict[str, Any] = None) -> MLEnsemble:
    """Get global ML ensemble instance"""
    global _ml_ensemble
    if _ml_ensemble is None:
        if config is None:
            config = {'models_dir': 'ml/registry/artifacts'}
        _ml_ensemble = MLEnsemble(config)
    return _ml_ensemble