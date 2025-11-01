"""
Oriphim Runner - Trading Engine

Coordinates job execution by integrating cloud jobs with local broker execution.
Handles strategy routing, pre-trade validation, execution, and result reporting.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger('oriphim_runner.engine')


class TradingEngine:
    """
    Core trading execution engine
    
    Responsibilities:
    - Receive jobs from cloud via WebSocket
    - Validate job parameters and market conditions
    - Route to appropriate strategy execution
    - Monitor trade execution and report results
    - Handle errors and edge cases
    """
    
    def __init__(self):
        # Strategy mapping
        self.strategy_handlers = {
            'bull_put_spread': self.execute_bull_put_spread,
            'iron_condor': self.execute_iron_condor,
            'covered_call': self.execute_covered_call,
            'custom_strategy': self.execute_custom_strategy
        }
        
        # Execution state
        self.current_job_id = None
        self.job_start_time = None
        self.execution_stats = {
            'jobs_executed': 0,
            'jobs_successful': 0,
            'jobs_failed': 0,
            'total_pnl': 0.0
        }
        
        logger.info("Trading engine initialized")
    
    async def execute_job(self, job: Dict[str, Any], ibkr_manager) -> Dict[str, Any]:
        """
        Execute trading job received from cloud
        
        Args:
            job: Job configuration from cloud
            ibkr_manager: IBKR broker manager instance
            
        Returns:
            Execution result dictionary
        """
        job_id = job.get('id', 'unknown')
        self.current_job_id = job_id
        self.job_start_time = datetime.now()
        
        logger.info(f"Starting job execution: {job_id}")
        
        try:
            # 1. Validate job structure
            validation_result = await self.validate_job(job)
            if not validation_result['valid']:
                return self.create_error_result(job_id, f"Invalid job: {validation_result['error']}")
            
            # 2. Check market conditions and trading hours
            market_check = await self.check_market_conditions(job)
            if not market_check['tradeable']:
                return self.create_info_result(job_id, f"Market conditions: {market_check['reason']}")
            
            # 3. Verify broker connection
            if not ibkr_manager.is_connected:
                return self.create_error_result(job_id, "Broker not connected")
            
            # 4. Execute strategy-specific logic
            strategy = job.get('strategy')
            if strategy not in self.strategy_handlers:
                return self.create_error_result(job_id, f"Unknown strategy: {strategy}")
            
            handler = self.strategy_handlers[strategy]
            result = await handler(job, ibkr_manager)
            
            # 5. Update statistics
            self.update_execution_stats(result)
            
            # 6. Log completion
            duration = (datetime.now() - self.job_start_time).total_seconds()
            logger.info(f"Job {job_id} completed in {duration:.2f}s: {result['status']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Job execution error: {e}")
            return self.create_error_result(job_id, str(e))
        
        finally:
            self.current_job_id = None
            self.job_start_time = None
    
    async def validate_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Validate job structure and parameters"""
        try:
            required_fields = ['id', 'strategy', 'symbol', 'config']
            
            for field in required_fields:
                if field not in job:
                    return {'valid': False, 'error': f'Missing required field: {field}'}
            
            # Validate symbol
            symbol = job['symbol']
            if not symbol or len(symbol) > 10:
                return {'valid': False, 'error': 'Invalid symbol'}
            
            # Validate strategy
            strategy = job['strategy']
            if strategy not in self.strategy_handlers:
                return {'valid': False, 'error': f'Unsupported strategy: {strategy}'}
            
            # Validate config structure
            config = job.get('config', {})
            if not isinstance(config, dict):
                return {'valid': False, 'error': 'Config must be a dictionary'}
            
            return {'valid': True, 'error': None}
            
        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {e}'}
    
    async def check_market_conditions(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Check if market conditions allow trading"""
        try:
            # Check trading hours (simplified - would use proper market calendar)
            now = datetime.now()
            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            
            if not (market_open <= now <= market_close):
                return {
                    'tradeable': False,
                    'reason': 'Outside market hours'
                }
            
            # Check if it's a weekday
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return {
                    'tradeable': False,
                    'reason': 'Market closed - weekend'
                }
            
            # Additional checks could include:
            # - Holiday calendar
            # - VIX spike detection
            # - News/earnings blackouts
            # - Volatility conditions
            
            return {
                'tradeable': True,
                'reason': 'Market conditions normal'
            }
            
        except Exception as e:
            logger.error(f"Error checking market conditions: {e}")
            return {
                'tradeable': False,
                'reason': f'Market check error: {e}'
            }
    
    async def execute_bull_put_spread(self, job: Dict[str, Any], ibkr_manager) -> Dict[str, Any]:
        """Execute bull put spread strategy"""
        try:
            symbol = job['symbol']
            config = job['config']
            
            logger.info(f"Executing bull put spread for {symbol}")
            
            # Prepare trade configuration
            trade_config = {
                'strategy': 'bull_put_spread',
                'symbol': symbol,
                'target_delta': config.get('target_delta', 0.10),
                'min_credit': config.get('min_credit', 0.15),
                'max_loss_per_trade': config.get('max_loss_per_trade', 50.0)
            }
            
            # Execute via IBKR manager
            execution_result = await ibkr_manager.execute_trade(trade_config)
            
            if execution_result['status'] == 'success':
                return self.create_success_result(job['id'], {
                    'strategy': 'bull_put_spread',
                    'symbol': symbol,
                    'execution_details': execution_result,
                    'expected_return': execution_result.get('credit', 0),
                    'max_risk': execution_result.get('max_loss', 0)
                })
            else:
                return self.create_error_result(job['id'], execution_result.get('message', 'Execution failed'))
            
        except Exception as e:
            logger.error(f"Bull put spread execution error: {e}")
            return self.create_error_result(job['id'], str(e))
    
    async def execute_iron_condor(self, job: Dict[str, Any], ibkr_manager) -> Dict[str, Any]:
        """Execute iron condor strategy"""
        try:
            symbol = job['symbol']
            config = job['config']
            
            logger.info(f"Executing iron condor for {symbol}")
            
            trade_config = {
                'strategy': 'iron_condor',
                'symbol': symbol,
                'wing_multiplier': config.get('wing_multiplier', 1.3),
                'min_credit': config.get('min_credit', 0.25)
            }
            
            execution_result = await ibkr_manager.execute_trade(trade_config)
            
            if execution_result['status'] == 'success':
                return self.create_success_result(job['id'], {
                    'strategy': 'iron_condor',
                    'symbol': symbol,
                    'execution_details': execution_result,
                    'prob_profit': execution_result.get('prob_profit', 0.5)
                })
            else:
                return self.create_error_result(job['id'], execution_result.get('message', 'Execution failed'))
            
        except Exception as e:
            logger.error(f"Iron condor execution error: {e}")
            return self.create_error_result(job['id'], str(e))
    
    async def execute_covered_call(self, job: Dict[str, Any], ibkr_manager) -> Dict[str, Any]:
        """Execute covered call strategy"""
        try:
            symbol = job['symbol']
            config = job['config']
            
            logger.info(f"Executing covered call for {symbol}")
            
            # Check if we have the underlying stock
            positions = await ibkr_manager.get_positions()
            stock_position = next((pos for pos in positions if pos['symbol'] == symbol), None)
            
            if not stock_position or stock_position['quantity'] < 100:
                return self.create_error_result(job['id'], f"Insufficient {symbol} shares for covered call")
            
            trade_config = {
                'strategy': 'covered_call',
                'symbol': symbol,
                'shares_owned': stock_position['quantity'],
                'target_delta': config.get('target_delta', 0.30)
            }
            
            execution_result = await ibkr_manager.execute_trade(trade_config)
            
            if execution_result['status'] == 'success':
                return self.create_success_result(job['id'], {
                    'strategy': 'covered_call',
                    'symbol': symbol,
                    'execution_details': execution_result,
                    'shares_covered': stock_position['quantity']
                })
            else:
                return self.create_error_result(job['id'], execution_result.get('message', 'Execution failed'))
            
        except Exception as e:
            logger.error(f"Covered call execution error: {e}")
            return self.create_error_result(job['id'], str(e))
    
    async def execute_custom_strategy(self, job: Dict[str, Any], ibkr_manager) -> Dict[str, Any]:
        """Execute custom strategy from cloud"""
        try:
            # This would handle custom strategies defined in the cloud dashboard
            custom_code = job['config'].get('custom_code')
            if not custom_code:
                return self.create_error_result(job['id'], "No custom code provided")
            
            # For security, we'd validate and sandbox the custom code
            # For now, return a placeholder
            return self.create_info_result(job['id'], "Custom strategy execution not yet implemented")
            
        except Exception as e:
            logger.error(f"Custom strategy execution error: {e}")
            return self.create_error_result(job['id'], str(e))
    
    def create_success_result(self, job_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create success result"""
        return {
            'job_id': job_id,
            'status': 'success',
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'execution_time_ms': self.get_execution_time_ms()
        }
    
    def create_error_result(self, job_id: str, error_message: str) -> Dict[str, Any]:
        """Create error result"""
        return {
            'job_id': job_id,
            'status': 'error',
            'error': error_message,
            'timestamp': datetime.now().isoformat(),
            'execution_time_ms': self.get_execution_time_ms()
        }
    
    def create_info_result(self, job_id: str, info_message: str) -> Dict[str, Any]:
        """Create info result (for skipped trades, etc.)"""
        return {
            'job_id': job_id,
            'status': 'info',
            'message': info_message,
            'timestamp': datetime.now().isoformat(),
            'execution_time_ms': self.get_execution_time_ms()
        }
    
    def get_execution_time_ms(self) -> int:
        """Get execution time in milliseconds"""
        if not self.job_start_time:
            return 0
        
        duration = datetime.now() - self.job_start_time
        return int(duration.total_seconds() * 1000)
    
    def update_execution_stats(self, result: Dict[str, Any]):
        """Update execution statistics"""
        self.execution_stats['jobs_executed'] += 1
        
        if result['status'] == 'success':
            self.execution_stats['jobs_successful'] += 1
            
            # Extract P&L if available
            data = result.get('data', {})
            execution_details = data.get('execution_details', {})
            pnl = execution_details.get('expected_return', 0)
            
            if isinstance(pnl, (int, float)):
                self.execution_stats['total_pnl'] += pnl
        else:
            self.execution_stats['jobs_failed'] += 1
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get current execution statistics"""
        stats = self.execution_stats.copy()
        
        if stats['jobs_executed'] > 0:
            stats['success_rate'] = stats['jobs_successful'] / stats['jobs_executed']
        else:
            stats['success_rate'] = 0.0
        
        return stats
    
    async def emergency_stop(self):
        """Emergency stop all trading activity"""
        logger.warning("EMERGENCY STOP ACTIVATED")
        
        # Cancel current job if running
        if self.current_job_id:
            logger.warning(f"Cancelling current job: {self.current_job_id}")
            self.current_job_id = None
        
        # Additional emergency procedures could include:
        # - Close all open positions
        # - Cancel pending orders
        # - Notify cloud of emergency stop
        # - Log emergency event
        
        logger.warning("Emergency stop complete")


# Mock Trading Engine for testing
class MockTradingEngine(TradingEngine):
    """Mock trading engine for testing without actual execution"""
    
    async def execute_job(self, job: Dict[str, Any], ibkr_manager) -> Dict[str, Any]:
        """Mock job execution with simulated delay"""
        job_id = job.get('id', 'mock_job')
        strategy = job.get('strategy', 'unknown')
        symbol = job.get('symbol', 'SPY')
        
        logger.info(f"Mock executing {strategy} for {symbol}")
        
        # Simulate execution time
        await asyncio.sleep(2)
        
        # Simulate success 90% of the time
        import random
        if random.random() < 0.9:
            return self.create_success_result(job_id, {
                'strategy': strategy,
                'symbol': symbol,
                'execution_details': {
                    'credit': 0.52,
                    'max_profit': 52.0,
                    'max_loss': 48.0,
                    'mode': 'mock'
                },
                'expected_return': 52.0
            })
        else:
            return self.create_error_result(job_id, "Mock execution failure")