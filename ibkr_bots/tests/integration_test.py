#!/usr/bin/env python3
"""
IBKR Options Bot - System Integration Test

Comprehensive test suite that validates all core components:
- Broker connection and authentication
- Options chain fetching and analysis
- Spread construction and pricing
- Risk management and position sizing
- Regime detection and ML features
- Order execution pipeline (paper mode only)

Run this before deploying any bot to ensure system integrity.
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.broker import BrokerConnection, get_broker
from core.options import OptionsAnalyzer, get_options_analyzer  
from core.risk import RiskManager, get_risk_manager
from core.regime import RegimeAnalyzer, get_regime_analyzer
from core.events import EventCalendar
from core.exec import OrderExecutor
from core.telemetry import get_telemetry_manager
from ml.features import FeatureBuilder
from ml.models import get_ml_ensemble

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('integration_test')


class IntegrationTestSuite:
    """Comprehensive integration test suite"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.test_results = []
        self.test_symbols = ['SPY', 'QQQ', 'SPX']
        
        # Initialize components
        self.broker = None
        self.options = None
        self.risk_manager = None
        self.regime_analyzer = None
        self.feature_builder = None
        
        logger.info("Integration test suite initialized")
    
    def run_all_tests(self) -> bool:
        """Run complete test suite"""
        logger.info("=" * 60)
        logger.info("STARTING COMPREHENSIVE INTEGRATION TEST")
        logger.info("=" * 60)
        
        success = True
        
        # Core infrastructure tests
        success &= self.test_broker_connection()
        success &= self.test_options_analysis()
        success &= self.test_spread_construction()
        success &= self.test_risk_management()
        success &= self.test_regime_detection()
        success &= self.test_event_calendar()
        
        # ML pipeline tests
        success &= self.test_feature_generation()
        success &= self.test_ml_models()
        
        # Integration tests
        success &= self.test_end_to_end_workflow()
        success &= self.test_paper_order_execution()
        
        # Report results
        self.generate_test_report()
        
        logger.info("=" * 60)
        if success:
            logger.info("✅ ALL TESTS PASSED - System ready for deployment")
        else:
            logger.error("❌ SOME TESTS FAILED - Review issues before deployment")
        logger.info("=" * 60)
        
        return success
    
    def test_broker_connection(self) -> bool:
        """Test IBKR broker connection and basic functionality"""
        logger.info("🧪 Testing broker connection...")
        
        try:
            # Initialize broker
            self.broker = BrokerConnection()
            
            # Test paper mode connection
            connected = self.broker.connect(paper_mode=True)
            if not connected:
                self.log_failure("Broker connection", "Failed to connect to IBKR paper account")
                return False
            
            # Test market data
            for symbol in self.test_symbols[:2]:  # Test first 2 symbols
                snapshot = self.broker.get_market_snapshot(symbol)
                if not snapshot:
                    self.log_failure("Market data", f"Failed to get snapshot for {symbol}")
                    return False
                
                if not (snapshot.price > 0 and snapshot.bid > 0 and snapshot.ask > 0):
                    self.log_failure("Market data", f"Invalid prices for {symbol}: {snapshot}")
                    return False
            
            # Test option chain fetching
            chain_info = self.broker.get_option_chain('SPY')
            if not chain_info or not chain_info.get('expirations'):
                self.log_failure("Option chains", "Failed to fetch SPY option chain")
                return False
            
            self.log_success("Broker connection", "All broker tests passed")
            return True
            
        except Exception as e:
            self.log_failure("Broker connection", f"Exception: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_options_analysis(self) -> bool:
        """Test options analysis and pricing"""
        logger.info("🧪 Testing options analysis...")
        
        try:
            self.options = get_options_analyzer()
            
            # Test expected move calculation
            expiry = self.options.get_nearest_friday_expiry('SPY')
            if not expiry:
                self.log_failure("Options analysis", "Failed to get nearest expiry")
                return False
            
            em_result = self.options.calculate_expected_move('SPY', expiry)
            if not em_result or em_result.percent_em <= 0:
                self.log_failure("Options analysis", "Invalid expected move calculation")
                return False
            
            # Test IV rank calculation
            iv_rank = self.options.calculate_iv_rank('SPY')
            if iv_rank is None or not (0 <= iv_rank <= 100):
                self.log_failure("Options analysis", f"Invalid IV rank: {iv_rank}")
                return False
            
            # Test option quotes
            chain_info = self.broker.get_option_chain('SPY')
            strikes = chain_info.get('strikes', [])[:5]  # Test first 5 strikes
            
            quotes = self.options.get_option_quotes('SPY', expiry, strikes)
            if not quotes or len(quotes) == 0:
                self.log_failure("Options analysis", "Failed to get option quotes")
                return False
            
            # Validate quote data
            for quote in quotes:
                if quote.bid <= 0 or quote.ask <= quote.bid:
                    self.log_failure("Options analysis", f"Invalid quote: {quote}")
                    return False
            
            self.log_success("Options analysis", f"EM: {em_result.percent_em:.2f}%, IV Rank: {iv_rank:.1f}%")
            return True
            
        except Exception as e:
            self.log_failure("Options analysis", f"Exception: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_spread_construction(self) -> bool:
        """Test spread construction methods"""
        logger.info("🧪 Testing spread construction...")
        
        try:
            expiry = self.options.get_nearest_friday_expiry('SPY')
            
            # Test bull put spread construction
            put_spread = self.options.build_bull_put_spread('SPY', expiry, target_delta=0.10)
            if not put_spread:
                self.log_failure("Spread construction", "Failed to build bull put spread")
                return False
            
            # Validate spread structure
            if not put_spread.get('net_credit', 0) > 0:
                self.log_failure("Spread construction", "Bull put spread should generate credit")
                return False
            
            # Test iron condor construction
            em_result = self.options.calculate_expected_move('SPY', expiry)
            condor = self.options.build_iron_condor('SPY', expiry, em_result.dollar_em)
            if not condor:
                self.log_failure("Spread construction", "Failed to build iron condor")
                return False
            
            # Validate condor structure
            if len(condor.get('legs', [])) != 4:
                self.log_failure("Spread construction", "Iron condor should have 4 legs")
                return False
            
            # Test liquidity validation
            is_liquid = self.options.validate_spread_liquidity(put_spread)
            if is_liquid is None:
                self.log_failure("Spread construction", "Liquidity validation failed")
                return False
            
            self.log_success("Spread construction", f"Put spread credit: ${put_spread['net_credit']:.2f}")
            return True
            
        except Exception as e:
            self.log_failure("Spread construction", f"Exception: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_risk_management(self) -> bool:
        """Test risk management system"""
        logger.info("🧪 Testing risk management...")
        
        try:
            self.risk_manager = get_risk_manager()
            
            # Test position sizing
            trade_config = {
                'max_loss': 50.0,
                'credit_received': 0.75,
                'strategy': 'bull_put_spread'
            }
            
            position_size = self.risk_manager.calculate_position_size(trade_config)
            if position_size <= 0:
                self.log_failure("Risk management", "Invalid position size calculation")
                return False
            
            # Test daily limit enforcement
            is_allowed = self.risk_manager.check_daily_limits()
            if is_allowed is None:
                self.log_failure("Risk management", "Daily limit check failed")
                return False
            
            # Test kill switch functionality
            kill_switch_active = self.risk_manager.check_kill_switches()
            if kill_switch_active is None:
                self.log_failure("Risk management", "Kill switch check failed")
                return False
            
            # Test portfolio heat calculation
            current_heat = self.risk_manager.calculate_portfolio_heat()
            if current_heat < 0:
                self.log_failure("Risk management", "Invalid portfolio heat calculation")
                return False
            
            self.log_success("Risk management", f"Position size: {position_size}, Heat: {current_heat:.1f}%")
            return True
            
        except Exception as e:
            self.log_failure("Risk management", f"Exception: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_regime_detection(self) -> bool:
        """Test market regime detection"""
        logger.info("🧪 Testing regime detection...")
        
        try:
            self.regime_analyzer = get_regime_analyzer()
            
            # Test regime analysis for SPY
            regime_signals = self.regime_analyzer.analyze_regime('SPY')
            if not regime_signals:
                self.log_failure("Regime detection", "Failed to analyze regime")
                return False
            
            # Validate regime signals
            if not regime_signals.overall_regime:
                self.log_failure("Regime detection", "No regime classification")
                return False
            
            # Test multiple symbols
            for symbol in ['SPY', 'QQQ']:
                signals = self.regime_analyzer.analyze_regime(symbol)
                if not signals:
                    self.log_failure("Regime detection", f"Failed regime analysis for {symbol}")
                    return False
            
            self.log_success("Regime detection", f"SPY regime: {regime_signals.overall_regime}")
            return True
            
        except Exception as e:
            self.log_failure("Regime detection", f"Exception: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_event_calendar(self) -> bool:
        """Test economic event calendar"""
        logger.info("🧪 Testing event calendar...")
        
        try:
            event_calendar = EventCalendar(self.config)
            
            # Test blackout checking
            is_blackout = event_calendar.is_blackout_day()
            if is_blackout is None:
                self.log_failure("Event calendar", "Blackout check failed")
                return False
            
            # Test upcoming events
            upcoming = event_calendar.get_upcoming_events(days_ahead=7)
            if upcoming is None:
                self.log_failure("Event calendar", "Failed to get upcoming events")
                return False
            
            self.log_success("Event calendar", f"Blackout today: {is_blackout}, Upcoming: {len(upcoming)}")
            return True
            
        except Exception as e:
            self.log_failure("Event calendar", f"Exception: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_feature_generation(self) -> bool:
        """Test ML feature generation"""
        logger.info("🧪 Testing ML feature generation...")
        
        try:
            self.feature_builder = FeatureBuilder(self.config)
            
            # Test regime features
            regime_features = self.feature_builder.build_regime_features('SPY')
            if not regime_features or len(regime_features) < 10:
                self.log_failure("Feature generation", f"Insufficient regime features: {len(regime_features) if regime_features else 0}")
                return False
            
            # Test trade scoring features
            expiry = self.options.get_nearest_friday_expiry('SPY')
            strikes = [400, 405]  # Sample strikes
            
            trade_features = self.feature_builder.build_trade_scoring_features(
                'SPY', expiry, 'bull_put_spread', strikes
            )
            if not trade_features or len(trade_features) < 15:
                self.log_failure("Feature generation", f"Insufficient trade features: {len(trade_features) if trade_features else 0}")
                return False
            
            self.log_success("Feature generation", f"Regime: {len(regime_features)}, Trade: {len(trade_features)} features")
            return True
            
        except Exception as e:
            self.log_failure("Feature generation", f"Exception: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_ml_models(self) -> bool:
        """Test ML model ensemble"""
        logger.info("🧪 Testing ML models...")
        
        try:
            ml_ensemble = get_ml_ensemble(self.config)
            
            # Generate sample features
            features = self.feature_builder.build_regime_features('SPY')
            if not features:
                self.log_failure("ML models", "No features available for testing")
                return False
            
            # Test ensemble prediction (will work with untrained models)
            signals = ml_ensemble.get_trading_signals(features)
            if not signals:
                self.log_failure("ML models", "Failed to get trading signals")
                return False
            
            # Validate signal structure
            required_keys = ['timestamp', 'features_used', 'recommendation']
            for key in required_keys:
                if key not in signals:
                    self.log_failure("ML models", f"Missing signal key: {key}")
                    return False
            
            self.log_success("ML models", f"Recommendation: {signals['recommendation']}")
            return True
            
        except Exception as e:
            self.log_failure("ML models", f"Exception: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_end_to_end_workflow(self) -> bool:
        """Test complete bot workflow without placing orders"""
        logger.info("🧪 Testing end-to-end workflow...")
        
        try:
            # Simulate Bot A (PUT-Lite) workflow
            symbol = 'SPY'
            
            # 1. Check events and regime
            event_calendar = EventCalendar(self.config)
            if event_calendar.is_blackout_day():
                self.log_success("End-to-end workflow", "Correctly identified blackout day")
                return True
            
            # 2. Analyze regime
            regime_signals = self.regime_analyzer.analyze_regime(symbol)
            if not regime_signals.entry_allowed:
                self.log_success("End-to-end workflow", "Regime correctly blocked entry")
                return True
            
            # 3. Build spread
            expiry = self.options.get_nearest_friday_expiry(symbol)
            spread = self.options.build_bull_put_spread(symbol, expiry)
            if not spread:
                self.log_success("End-to-end workflow", "No suitable spread found (normal)")
                return True
            
            # 4. Check risk limits
            if not self.risk_manager.check_daily_limits():
                self.log_success("End-to-end workflow", "Risk limits correctly enforced")
                return True
            
            # 5. Generate ML features and score
            features = self.feature_builder.build_trade_scoring_features(
                symbol, expiry, 'bull_put_spread', [spread['legs'][0]['strike'], spread['legs'][1]['strike']]
            )
            
            ml_signals = get_ml_ensemble(self.config).get_trading_signals(features)
            
            self.log_success("End-to-end workflow", f"Complete workflow executed, ML rec: {ml_signals['recommendation']}")
            return True
            
        except Exception as e:
            self.log_failure("End-to-end workflow", f"Exception: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_paper_order_execution(self) -> bool:
        """Test paper order execution (no real money)"""
        logger.info("🧪 Testing paper order execution...")
        
        try:
            # This would test actual order placement in paper mode
            # For safety, we'll just validate the order construction
            
            executor = OrderExecutor(self.config)
            
            # Test order construction for bull put spread
            expiry = self.options.get_nearest_friday_expiry('SPY')
            spread = self.options.build_bull_put_spread('SPY', expiry, min_credit=0.10)
            
            if not spread:
                self.log_success("Paper execution", "No suitable spread for testing (normal)")
                return True
            
            # Validate order structure (without placing)
            order_valid = True
            for leg in spread['legs']:
                if not all(key in leg for key in ['strike', 'right', 'action']):
                    order_valid = False
                    break
            
            if not order_valid:
                self.log_failure("Paper execution", "Invalid order structure")
                return False
            
            self.log_success("Paper execution", "Order structure validation passed")
            return True
            
        except Exception as e:
            self.log_failure("Paper execution", f"Exception: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def log_success(self, test_name: str, message: str):
        """Log successful test"""
        self.test_results.append({'test': test_name, 'status': 'PASS', 'message': message})
        logger.info(f"✅ {test_name}: {message}")
    
    def log_failure(self, test_name: str, message: str):
        """Log failed test"""
        self.test_results.append({'test': test_name, 'status': 'FAIL', 'message': message})
        logger.error(f"❌ {test_name}: {message}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 60)
        logger.info("INTEGRATION TEST REPORT")
        logger.info("=" * 60)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        
        logger.info(f"Total Tests: {len(self.test_results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {passed/len(self.test_results)*100:.1f}%")
        
        if failed > 0:
            logger.info("\nFAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    logger.info(f"  ❌ {result['test']}: {result['message']}")
        
        logger.info("=" * 60)


def main():
    """Run integration test suite"""
    # Default configuration
    config = {
        'events': {
            'blackout_kinds': ['CPI', 'FOMC', 'NFP'],
            'manual_blackout': False
        },
        'lookback_minutes': 60,
        'vol_lookback_days': 20,
        'models_dir': 'ml/registry/artifacts'
    }
    
    # Run tests
    test_suite = IntegrationTestSuite(config)
    success = test_suite.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()