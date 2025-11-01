#!/usr/bin/env python3
"""
Bot A: PUT-Lite Intraday Premium Harvester

Executes 0DTE/1DTE bull put spreads on SPY/SPX during mid-day volatility compression.
Harvests the volatility risk premium with strict risk controls.
"""

import os
import sys
import logging
import argparse
import yaml
import json
from datetime import datetime, time, timedelta
from typing import Dict, Any, Optional
import signal
import time as time_module

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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot_A.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BotA')


class PutLiteBot:
    """PUT-Lite intraday premium harvesting bot"""
    
    def __init__(self, config_path: str, dry_run: bool = False, live_mode: bool = False):
        self.config_path = config_path
        self.dry_run = dry_run
        self.live_mode = live_mode
        self.running = False
        self.config = self._load_config()
        
        # Validate mode
        if live_mode and os.getenv('MODE', 'paper') != 'live':
            logger.error("Live mode requested but MODE env var is not 'live'")
            sys.exit(1)
        
        # Initialize components
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
        
        logger.info(f"PUT-Lite Bot initialized - Mode: {'LIVE' if live_mode else 'PAPER'}")
        logger.info(f"Trading window: {self.start_time} - {self.end_time}")
        logger.info(f"Primary symbol: {self.primary_symbol}, Profit target: {self.profit_target_pct:.1%}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded config from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string in HH:MM format"""
        try:
            return datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            logger.error(f"Invalid time format: {time_str}")
            return time(10, 30)  # Default fallback
    
    def _is_trading_hours(self) -> bool:
        """Check if current time is within trading hours"""
        now = datetime.now().time()
        return self.start_time <= now <= self.end_time
    
    def _should_flatten_positions(self) -> bool:
        """Check if positions should be flattened due to time"""
        now = datetime.now().time()
        market_close = time(16, 0)  # 4:00 PM ET
        
        # Calculate flatten time
        close_datetime = datetime.combine(datetime.now().date(), market_close)
        flatten_time = (close_datetime - timedelta(minutes=self.flatten_before_close)).time()
        
        return now >= flatten_time
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down gracefully...")
            self.running = False
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def connect_broker(self) -> bool:
        """Connect to IBKR"""
        try:
            host = os.getenv('IB_HOST', '127.0.0.1')
            port = int(os.getenv('IB_PORT', '7497'))
            client_id = int(os.getenv('IB_CLIENT_ID', '1'))
            
            success = self.broker.connect(host, port, client_id)
            
            if success:
                logger.info("✅ Connected to IBKR successfully")
                return True
            else:
                logger.error("❌ Failed to connect to IBKR")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def evaluate_entry_conditions(self, symbol: str) -> Dict[str, Any]:
        """
        Evaluate all entry conditions for a symbol
        
        Args:
            symbol: Symbol to evaluate
            
        Returns:
            Dict with evaluation results
        """
        evaluation = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'entry_allowed': False,
            'filters': {},
            'market_data': {},
            'rejection_reasons': []
        }
        
        try:
            # Check if trading is allowed by risk manager
            trading_allowed, risk_reason = self.risk_manager.is_trading_allowed()
            if not trading_allowed:
                evaluation['rejection_reasons'].append(f"Risk: {risk_reason}")
                return evaluation
            
            # Check event blackouts
            if self.event_calendar.is_blackout(symbol):
                evaluation['rejection_reasons'].append("Event blackout active")
                return evaluation
            
            # Get market data
            snapshot = self.broker.get_market_snapshot(symbol)
            if not snapshot:
                evaluation['rejection_reasons'].append("No market data available")
                return evaluation
            
            evaluation['market_data'] = {
                'price': snapshot.price,
                'bid': snapshot.bid,
                'ask': snapshot.ask,
                'volume': snapshot.volume
            }
            
            # Get nearest expiry (prefer 0DTE/1DTE)
            expiry = self.options_analyzer.get_nearest_friday_expiry(symbol)
            if not expiry:
                evaluation['rejection_reasons'].append("No suitable expiry found")
                return evaluation
            
            # Perform regime analysis
            regime_signals = self.regime_analyzer.analyze_regime(symbol, expiry)
            evaluation['filters']['regime'] = {
                'iv_rank': regime_signals.iv_rank,
                'rv_em_ratio': regime_signals.rv_vs_em_ratio,
                'vwap_signal': regime_signals.vwap_signal,
                'overall_regime': regime_signals.overall_regime,
                'entry_allowed': regime_signals.entry_allowed
            }
            
            if not regime_signals.entry_allowed:
                reasons = []
                if regime_signals.iv_rank and regime_signals.iv_rank < self.regime_analyzer.iv_rank_min:
                    reasons.append(f"IV rank too low: {regime_signals.iv_rank:.1f}%")
                if regime_signals.rv_vs_em_ratio and regime_signals.rv_vs_em_ratio < self.regime_analyzer.rv_em_min:
                    reasons.append(f"RV/EM ratio too low: {regime_signals.rv_vs_em_ratio:.2f}")
                
                evaluation['rejection_reasons'].extend(reasons)
                return evaluation
            
            # Find suitable put spread
            delta_range = tuple(self.config['filters']['delta_target_put'])
            spread_data = self.options_analyzer.find_put_spread_by_delta(symbol, expiry, delta_range)
            
            if not spread_data:
                evaluation['rejection_reasons'].append("No suitable put spread found")
                return evaluation
            
            evaluation['spread_data'] = spread_data
            
            # Check spread quality
            spread_metrics = spread_data['spread_metrics']
            if spread_metrics['credit'] <= 0:
                evaluation['rejection_reasons'].append(f"Invalid credit: ${spread_metrics['credit']:.3f}")
                return evaluation
            
            if spread_metrics['max_loss'] > self.risk_manager.metrics.per_trade_loss_limit:
                evaluation['rejection_reasons'].append(
                    f"Max loss ${spread_metrics['max_loss']:.2f} exceeds limit "
                    f"${self.risk_manager.metrics.per_trade_loss_limit}"
                )
                return evaluation
            
            # All filters passed
            evaluation['entry_allowed'] = True
            logger.info(f"✅ Entry conditions satisfied for {symbol}")
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating entry conditions for {symbol}: {e}")
            evaluation['rejection_reasons'].append(f"Evaluation error: {str(e)}")
            return evaluation
    
    def enter_position(self, evaluation: Dict[str, Any]) -> bool:
        """Enter a new position based on evaluation"""
        symbol = evaluation['symbol']
        spread_data = evaluation.get('spread_data')
        
        if not spread_data:
            logger.error("No spread data available for entry")
            return False
        
        try:
            # Risk assessment
            max_loss = spread_data['spread_metrics']['max_loss']
            trade_risk = self.risk_manager.assess_trade_risk(symbol, max_loss)
            
            if not trade_risk.approved:
                logger.warning(f"Trade rejected by risk manager: {trade_risk.rejection_reason}")
                return False
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would enter {symbol} put spread")
                logger.info(f"  Short: {spread_data['short_put']['strike']} put")
                logger.info(f"  Long: {spread_data['long_put']['strike']} put") 
                logger.info(f"  Credit: ${spread_data['spread_metrics']['credit']:.3f}")
                logger.info(f"  Max Loss: ${max_loss:.2f}")
                
                # Create mock position for tracking
                position_id = f"{symbol}_{datetime.now().strftime('%H%M%S')}"
                self.current_positions[position_id] = {
                    'symbol': symbol,
                    'entry_time': datetime.now(),
                    'short_strike': spread_data['short_put']['strike'],
                    'long_strike': spread_data['long_put']['strike'],
                    'entry_credit': spread_data['spread_metrics']['credit'],
                    'max_loss': max_loss,
                    'quantity': 1,
                    'profit_target': spread_data['spread_metrics']['credit'] * self.profit_target_pct,
                    'status': 'open'
                }
                
                self.risk_manager.record_trade_entry(symbol, max_loss)
                return True
            
            # Real execution would go here
            logger.info(f"PAPER: Entered {symbol} put spread")
            return True
            
        except Exception as e:
            logger.error(f"Error entering position for {symbol}: {e}")
            return False
    
    def manage_positions(self):
        """Monitor and manage existing positions"""
        if not self.current_positions:
            return
        
        positions_to_close = []
        
        for position_id, position in self.current_positions.items():
            if position['status'] != 'open':
                continue
                
            try:
                symbol = position['symbol']
                
                # Check time-based exit
                if self._should_flatten_positions():
                    positions_to_close.append((position_id, "Time stop - approaching close"))
                    continue
                
                # Get current market data
                snapshot = self.broker.get_market_snapshot(symbol)
                if not snapshot:
                    continue
                
                current_price = snapshot.price
                short_strike = position['short_strike']
                
                # Check breach stop
                breach_level = short_strike - (position['max_loss'] * self.breach_stop_ratio)
                if current_price <= breach_level:
                    positions_to_close.append((position_id, f"Breach stop: {current_price:.2f} <= {breach_level:.2f}"))
                    continue
                
                logger.debug(f"Position {position_id}: underlying @ {current_price:.2f}, "
                            f"short strike {short_strike:.2f}")
                
            except Exception as e:
                logger.error(f"Error managing position {position_id}: {e}")
        
        # Close positions that need to be closed
        for position_id, reason in positions_to_close:
            self.close_position(position_id, reason)
    
    def close_position(self, position_id: str, reason: str) -> bool:
        """Close a position"""
        if position_id not in self.current_positions:
            logger.warning(f"Position {position_id} not found")
            return False
        
        position = self.current_positions[position_id]
        
        try:
            # Estimate P&L (simplified for MVP)
            entry_credit = position['entry_credit']
            estimated_pnl = entry_credit * self.profit_target_pct  # Simplified
            
            position['status'] = 'closed'
            position['exit_time'] = datetime.now()
            position['exit_reason'] = reason
            position['realized_pnl'] = estimated_pnl
            
            # Update risk manager
            self.risk_manager.record_trade_exit(position['symbol'], estimated_pnl)
            
            logger.info(f"✅ Closed position {position_id}: {reason} (Est. P&L: ${estimated_pnl:.2f})")
            
            # Log decision
            self.telemetry.log_decision({
                'symbol': position['symbol'],
                'strategy': 'bot_A',
                'decision': 'EXIT',
                'reason': reason,
                'trade_id': position_id,
                'filters': {'realized_pnl': estimated_pnl},
                'market_data': {}
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error closing position {position_id}: {e}")
            return False
    
    def run_trading_session(self):
        """Main trading loop"""
        logger.info("Starting PUT-Lite trading session")
        
        if not self.connect_broker():
            return False
        
        self.running = True
        self.setup_signal_handlers()
        
        last_evaluation_time = None
        evaluation_interval = 300  # 5 minutes between evaluations
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check if we should be trading
                if not self._is_trading_hours():
                    if current_time.time() > self.end_time:
                        logger.info("Trading session ended")
                        break
                    
                    logger.debug("Outside trading hours, waiting...")
                    time_module.sleep(60)
                    continue
                
                # Manage existing positions
                self.manage_positions()
                
                # Check if it's time for new evaluation
                if (last_evaluation_time is None or 
                    (current_time - last_evaluation_time).total_seconds() >= evaluation_interval):
                    
                    # Evaluate entry conditions for primary symbol
                    evaluation = self.evaluate_entry_conditions(self.primary_symbol)
                    
                    # Log the decision
                    decision_type = 'ENTER' if evaluation['entry_allowed'] else 'SKIP'
                    skip_reason = '; '.join(evaluation.get('rejection_reasons', []))
                    
                    self.telemetry.log_decision({
                        'symbol': self.primary_symbol,
                        'strategy': 'bot_A',
                        'decision': decision_type,
                        'reason': skip_reason if skip_reason else 'Entry conditions satisfied',
                        'filters': evaluation.get('filters', {}),
                        'market_data': evaluation.get('market_data', {})
                    })
                    
                    # Enter position if conditions met and no current position
                    if evaluation['entry_allowed'] and len([p for p in self.current_positions.values() if p['status'] == 'open']) == 0:
                        self.enter_position(evaluation)
                    elif not evaluation['entry_allowed']:
                        logger.info(f"⏸️ Entry skipped for {self.primary_symbol}: {skip_reason}")
                    
                    last_evaluation_time = current_time
                
                # Sleep for a short interval
                time_module.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time_module.sleep(60)  # Wait before retrying
        
        # Cleanup
        self.shutdown()
        return True
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down PUT-Lite bot...")
        
        try:
            # Close all open positions
            open_positions = [pid for pid, pos in self.current_positions.items() if pos['status'] == 'open']
            for position_id in open_positions:
                self.close_position(position_id, "Bot shutdown")
            
            # Generate EOD report
            eod_report = self.telemetry.generate_eod_report()
            logger.info("EOD Report generated")
            
            # Disconnect broker
            self.broker.disconnect()
            
            logger.info("Shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='PUT-Lite Options Trading Bot')
    parser.add_argument('--config', default='config/strategy.yaml', help='Config file path')
    parser.add_argument('--dry-run', action='store_true', help='Run in simulation mode')
    parser.add_argument('--live', action='store_true', help='Run in live trading mode')
    
    args = parser.parse_args()
    
    # Safety check for live mode
    if args.live and not args.dry_run:
        mode = os.getenv('MODE', 'paper')
        if mode != 'live':
            logger.error("Live mode requires MODE=live environment variable")
            sys.exit(1)
        
        confirm = input("⚠️  LIVE TRADING MODE - Are you sure? Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            logger.info("Live trading cancelled")
            sys.exit(0)
    
    # Create and run bot
    bot = PutLiteBot(
        config_path=args.config,
        dry_run=args.dry_run or not args.live,
        live_mode=args.live and not args.dry_run
    )
    
    try:
        success = bot.run_trading_session()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

