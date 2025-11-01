#!/usr/bin/env python3
"""
Bot A: PUT-Lite Intraday Premium Harvester (Refactored for SaaS)

Executes 0DTE/1DTE bull put spreads on SPY/SPX during mid-day volatility compression.
Harvests the volatility risk premium with strict risk controls.
"""

import os
import sys
import time
from datetime import datetime, time as dt_time, timedelta
from typing import Dict, Any, Iterator, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.broker import get_broker
from core.options import get_options_analyzer
from core.risk import get_risk_manager
from core.regime import get_regime_analyzer
from core.events import get_event_calendar
from core.crowd import get_crowd_analyzer
from core.exec import get_execution_engine
from core.telemetry import get_telemetry_manager

from .bot_interface import OriphimBot, LogLevel, BotMessage


class PutLiteBot(OriphimBot):
    """PUT-Lite intraday premium harvesting bot (SaaS version)"""
    
    def get_bot_kind(self) -> str:
        return "putlite"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate bot configuration"""
        required_fields = ['trade_window', 'risk', 'symbols']
        
        for field in required_fields:
            if field not in config:
                return False
                
        # Validate trade window
        trade_window = config.get('trade_window', {})
        if 'start' not in trade_window or 'end' not in trade_window:
            return False
            
        # Validate risk parameters
        risk = config.get('risk', {})
        if 'max_loss_per_trade' not in risk:
            return False
            
        return True
    
    def run(self) -> Iterator[BotMessage]:
        """Main bot execution with real-time message streaming"""
        try:
            self.running = True
            
            yield self.log(LogLevel.INFO, "Initializing PUT-Lite Bot", 
                          mode=self.mode, config_valid=True)
            
            # Initialize components
            if not self._initialize_components():
                yield self.log(LogLevel.ERROR, "Failed to initialize bot components")
                return
            
            yield self.log(LogLevel.INFO, "Components initialized successfully",
                          primary_symbol=self.primary_symbol,
                          trade_window=f"{self.start_time}-{self.end_time}")
            
            # Wait for market open if needed
            if not self._is_market_hours():
                yield self.log(LogLevel.INFO, "Waiting for market hours")
                while not self._is_market_hours() and self.running:
                    time.sleep(30)
                    
            if not self.running:
                yield self.log(LogLevel.INFO, "Bot stopped during market wait")
                return
                
            # Main trading loop
            yield self.log(LogLevel.INFO, "Starting main trading loop")
            
            while self.running and self._should_continue_trading():
                try:
                    # Market regime check
                    regime_data = self._check_market_regime()
                    if regime_data:
                        yield self.log(LogLevel.INFO, "Market regime analysis",
                                      **regime_data)
                    
                    # Look for trading opportunities
                    if self._in_trading_window():
                        opportunity = self._scan_for_opportunity()
                        
                        if opportunity:
                            yield self.log(LogLevel.INFO, "Found trading opportunity",
                                          **opportunity)
                            
                            # Execute trade
                            execution_result = self._execute_trade(opportunity)
                            
                            if execution_result.get('success'):
                                yield self.log(LogLevel.INFO, "Trade executed successfully",
                                              **execution_result)
                            else:
                                yield self.log(LogLevel.WARNING, "Trade execution failed",
                                              reason=execution_result.get('reason', 'Unknown'))
                    
                    # Manage existing positions
                    position_updates = self._manage_positions()
                    for update in position_updates:
                        yield self.log(LogLevel.INFO, "Position update", **update)
                    
                    # Risk monitoring
                    risk_status = self._check_risk_limits()
                    if risk_status.get('breach'):
                        yield self.log(LogLevel.WARNING, "Risk limit breach detected",
                                      **risk_status)
                        if risk_status.get('halt_trading'):
                            yield self.log(LogLevel.ERROR, "Halting trading due to risk breach")
                            break
                    
                    # Wait before next iteration
                    time.sleep(30)
                    
                except Exception as e:
                    yield self.log(LogLevel.ERROR, f"Error in trading loop: {str(e)}",
                                  error_type=type(e).__name__)
                    time.sleep(60)  # Wait longer on errors
            
            # Cleanup and final position management
            yield self.log(LogLevel.INFO, "Trading session ending, managing final positions")
            self._cleanup_positions()
            
            yield self.log(LogLevel.INFO, "PUT-Lite Bot session completed")
            
        except Exception as e:
            yield self.log(LogLevel.ERROR, f"Critical bot error: {str(e)}",
                          error_type=type(e).__name__)
            
        finally:
            self.running = False
    
    def _initialize_components(self) -> bool:
        """Initialize all bot components"""
        try:
            # Initialize core components
            self.broker = get_broker()
            self.options_analyzer = get_options_analyzer()
            self.risk_manager = get_risk_manager(self.config)
            self.regime_analyzer = get_regime_analyzer(self.config)
            self.event_calendar = get_event_calendar(self.config)
            self.crowd_analyzer = get_crowd_analyzer(self.config)
            self.execution_engine = get_execution_engine(self.config)
            self.telemetry = get_telemetry_manager()
            
            # Bot-specific config
            bot_config = self.config.get('bot_a', {})
            self.profit_target_pct = bot_config.get('profit_target_pct', 0.55)
            self.delta_stop = bot_config.get('delta_stop', 0.20)
            self.breach_stop_ratio = bot_config.get('breach_stop_ratio', 0.5)
            self.max_dte = bot_config.get('max_dte', 1)
            
            # Trading window
            trade_window = self.config.get('trade_window', {})
            self.start_time = self._parse_time(trade_window.get('start', '10:30'))
            self.end_time = self._parse_time(trade_window.get('end', '13:30'))
            self.flatten_before_close = self.config.get('flatten_before_close_min', 90)
            
            # Symbol selection
            symbols_config = self.config.get('symbols', {})
            self.prefer_spx = symbols_config.get('prefer_spx', False)
            self.primary_symbol = symbols_config.get('primary_index', 'SPY')
            self.backup_symbol = symbols_config.get('backup_index', 'QQQ')
            
            # Position tracking
            self.current_positions = {}
            
            return True
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            return False
    
    def _parse_time(self, time_str: str) -> dt_time:
        """Parse time string to time object"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return dt_time(hour, minute)
        except:
            return dt_time(10, 30)  # Default fallback
    
    def _is_market_hours(self) -> bool:
        """Check if currently in market hours"""
        now = datetime.now().time()
        market_open = dt_time(9, 30)
        market_close = dt_time(16, 0)
        return market_open <= now <= market_close
    
    def _in_trading_window(self) -> bool:
        """Check if currently in bot's trading window"""
        now = datetime.now().time()
        return self.start_time <= now <= self.end_time
    
    def _should_continue_trading(self) -> bool:
        """Check if bot should continue trading"""
        if not self.running:
            return False
            
        now = datetime.now().time()
        market_close = dt_time(16, 0)
        
        # Stop trading X minutes before market close
        close_buffer = (datetime.combine(datetime.today(), market_close) - 
                       timedelta(minutes=self.flatten_before_close)).time()
        
        return now < close_buffer
    
    def _check_market_regime(self) -> Optional[Dict[str, Any]]:
        """Analyze current market regime"""
        try:
            if self.regime_analyzer:
                regime = self.regime_analyzer.get_current_regime()
                return {
                    'regime': regime.get('type', 'unknown'),
                    'confidence': regime.get('confidence', 0),
                    'volatility_rank': regime.get('iv_rank', 0)
                }
        except Exception as e:
            self.logger.error(f"Regime analysis failed: {e}")
        return None
    
    def _scan_for_opportunity(self) -> Optional[Dict[str, Any]]:
        """Scan for PUT-Lite trading opportunities"""
        try:
            # This would contain the actual opportunity scanning logic
            # For now, return a placeholder
            return {
                'symbol': self.primary_symbol,
                'setup_type': 'bull_put_spread',
                'expected_move': 2.5,
                'iv_rank': 65,
                'credit': 0.45,
                'probability': 0.72
            }
        except Exception as e:
            self.logger.error(f"Opportunity scan failed: {e}")
            return None
    
    def _execute_trade(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trade based on opportunity"""
        try:
            # Placeholder for actual trade execution
            return {
                'success': True,
                'order_id': 'ORD123456',
                'fill_price': opportunity.get('credit', 0),
                'quantity': 1
            }
        except Exception as e:
            return {
                'success': False,
                'reason': str(e)
            }
    
    def _manage_positions(self) -> Iterator[Dict[str, Any]]:
        """Manage existing positions"""
        # Placeholder for position management
        if self.current_positions:
            yield {'action': 'position_check', 'count': len(self.current_positions)}
    
    def _check_risk_limits(self) -> Dict[str, Any]:
        """Check risk limits and return status"""
        try:
            if self.risk_manager:
                risk_status = self.risk_manager.check_limits()
                return {
                    'breach': risk_status.get('breach', False),
                    'halt_trading': risk_status.get('halt', False),
                    'current_pnl': risk_status.get('pnl', 0),
                    'max_loss': risk_status.get('max_loss', 0)
                }
        except Exception as e:
            self.logger.error(f"Risk check failed: {e}")
        
        return {'breach': False, 'halt_trading': False}
    
    def _cleanup_positions(self):
        """Clean up positions at end of session"""
        try:
            # Placeholder for position cleanup
            if self.current_positions:
                self.logger.info(f"Cleaning up {len(self.current_positions)} positions")
        except Exception as e:
            self.logger.error(f"Position cleanup failed: {e}")