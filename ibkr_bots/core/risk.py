"""
Risk management module for position sizing, loss limits, and kill switches.
Tracks PnL and enforces daily/per-trade risk limits.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass, field
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Current risk metrics and limits"""
    daily_pnl: float = 0.0
    daily_loss_limit: float = 150.0
    per_trade_loss_limit: float = 50.0
    max_positions: int = 3
    current_positions: int = 0
    vix_spike_threshold: float = 3.0
    is_halted: bool = False
    halt_reason: str = ""
    trades_today: int = 0


@dataclass
class TradeRisk:
    """Risk assessment for a specific trade"""
    symbol: str
    max_loss: float
    position_size: int
    risk_per_share: float
    stop_loss_level: Optional[float] = None
    time_stop: Optional[datetime] = None
    approved: bool = False
    rejection_reason: str = ""


class RiskManager:
    """Centralized risk management and position monitoring"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.risk_file = "data/risk_state.json"
        self.metrics = RiskMetrics()
        self._load_daily_state()
        
        # Update limits from config
        risk_config = config.get('risk', {})
        self.metrics.daily_loss_limit = risk_config.get('max_daily_loss', 150)
        self.metrics.per_trade_loss_limit = risk_config.get('max_loss_per_trade', 50)
        self.metrics.max_positions = risk_config.get('max_positions', 3)
        self.metrics.vix_spike_threshold = risk_config.get('vix_spike_pts', 3)
        
        logger.info(f"Risk limits: Daily ${self.metrics.daily_loss_limit}, "
                   f"Per-trade ${self.metrics.per_trade_loss_limit}, "
                   f"Max positions {self.metrics.max_positions}")
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
    
    def _load_daily_state(self):
        """Load today's risk state from file"""
        self._ensure_data_dir()
        
        try:
            if os.path.exists(self.risk_file):
                with open(self.risk_file, 'r') as f:
                    data = json.load(f)
                
                today_str = date.today().isoformat()
                today_data = data.get(today_str, {})
                
                if today_data:
                    self.metrics.daily_pnl = today_data.get('daily_pnl', 0.0)
                    self.metrics.current_positions = today_data.get('current_positions', 0)
                    self.metrics.is_halted = today_data.get('is_halted', False)
                    self.metrics.halt_reason = today_data.get('halt_reason', "")
                    self.metrics.trades_today = today_data.get('trades_today', 0)
                    
                    logger.info(f"Loaded daily state: PnL ${self.metrics.daily_pnl:.2f}, "
                               f"Positions {self.metrics.current_positions}, "
                               f"Trades {self.metrics.trades_today}")
                               
        except Exception as e:
            logger.warning(f"Could not load risk state: {e}")
    
    def _save_daily_state(self):
        """Save current risk state to file"""
        try:
            data = {}
            if os.path.exists(self.risk_file):
                with open(self.risk_file, 'r') as f:
                    data = json.load(f)
            
            today_str = date.today().isoformat()
            data[today_str] = {
                'daily_pnl': self.metrics.daily_pnl,
                'current_positions': self.metrics.current_positions,
                'is_halted': self.metrics.is_halted,
                'halt_reason': self.metrics.halt_reason,
                'trades_today': self.metrics.trades_today,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.risk_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save risk state: {e}")
    
    def assess_trade_risk(self, symbol: str, max_loss: float, 
                         position_size: int = 1) -> TradeRisk:
        """
        Assess risk for a proposed trade
        
        Args:
            symbol: Trading symbol
            max_loss: Maximum potential loss for the trade
            position_size: Number of contracts/shares
            
        Returns:
            TradeRisk object with approval/rejection decision
        """
        risk_per_share = max_loss / position_size if position_size > 0 else max_loss
        
        trade_risk = TradeRisk(
            symbol=symbol,
            max_loss=max_loss,
            position_size=position_size,
            risk_per_share=risk_per_share
        )
        
        # Check if trading is halted
        if self.metrics.is_halted:
            trade_risk.rejection_reason = f"Trading halted: {self.metrics.halt_reason}"
            return trade_risk
        
        # Check per-trade loss limit
        if max_loss > self.metrics.per_trade_loss_limit:
            trade_risk.rejection_reason = (f"Trade risk ${max_loss:.2f} exceeds "
                                         f"per-trade limit ${self.metrics.per_trade_loss_limit}")
            return trade_risk
        
        # Check if adding this loss would breach daily limit
        potential_daily_loss = min(0, self.metrics.daily_pnl) - max_loss
        if abs(potential_daily_loss) > self.metrics.daily_loss_limit:
            trade_risk.rejection_reason = (f"Potential daily loss ${abs(potential_daily_loss):.2f} "
                                         f"exceeds limit ${self.metrics.daily_loss_limit}")
            return trade_risk
        
        # Check position count limit
        if self.metrics.current_positions >= self.metrics.max_positions:
            trade_risk.rejection_reason = (f"Already at max positions "
                                         f"({self.metrics.current_positions}/{self.metrics.max_positions})")
            return trade_risk
        
        # Trade approved
        trade_risk.approved = True
        logger.info(f"Trade approved for {symbol}: max loss ${max_loss:.2f}")
        
        return trade_risk
    
    def record_trade_entry(self, symbol: str, max_loss: float):
        """Record a new trade entry"""
        self.metrics.current_positions += 1
        self.metrics.trades_today += 1
        
        logger.info(f"Trade entered: {symbol}, positions: {self.metrics.current_positions}, "
                   f"trades today: {self.metrics.trades_today}")
        
        self._save_daily_state()
    
    def record_trade_exit(self, symbol: str, realized_pnl: float):
        """Record a trade exit with realized P&L"""
        self.metrics.current_positions = max(0, self.metrics.current_positions - 1)
        self.metrics.daily_pnl += realized_pnl
        
        logger.info(f"Trade exited: {symbol}, PnL: ${realized_pnl:.2f}, "
                   f"Daily PnL: ${self.metrics.daily_pnl:.2f}")
        
        # Check if daily loss limit breached
        if self.metrics.daily_pnl < -self.metrics.daily_loss_limit:
            self.halt_trading(f"Daily loss limit breached: ${self.metrics.daily_pnl:.2f}")
        
        self._save_daily_state()
    
    def update_unrealized_pnl(self, positions_pnl: Dict[str, float]):
        """Update current unrealized P&L for open positions"""
        total_unrealized = sum(positions_pnl.values())
        total_pnl = self.metrics.daily_pnl + total_unrealized
        
        # Log significant unrealized losses
        if total_unrealized < -self.metrics.per_trade_loss_limit:
            logger.warning(f"Large unrealized loss: ${total_unrealized:.2f}")
        
        # Check if total P&L (realized + unrealized) breaches daily limit
        if total_pnl < -self.metrics.daily_loss_limit:
            self.halt_trading(f"Total P&L breached daily limit: ${total_pnl:.2f} "
                             f"(realized: ${self.metrics.daily_pnl:.2f}, "
                             f"unrealized: ${total_unrealized:.2f})")
    
    def halt_trading(self, reason: str):
        """Halt all trading with given reason"""
        self.metrics.is_halted = True
        self.metrics.halt_reason = reason
        
        logger.error(f"TRADING HALTED: {reason}")
        
        # Save halt state immediately
        self._save_daily_state()
        
        # Create emergency halt file that bots check
        try:
            with open("data/emergency_halt.flag", 'w') as f:
                f.write(f"{datetime.now().isoformat()}: {reason}\n")
        except Exception as e:
            logger.error(f"Could not create halt flag file: {e}")
    
    def resume_trading(self):
        """Resume trading (manual override)"""
        self.metrics.is_halted = False
        self.metrics.halt_reason = ""
        
        logger.info("Trading resumed")
        self._save_daily_state()
        
        # Remove halt flag file
        try:
            if os.path.exists("data/emergency_halt.flag"):
                os.remove("data/emergency_halt.flag")
        except Exception as e:
            logger.warning(f"Could not remove halt flag: {e}")
    
    def check_vix_spike(self, current_vix: float, previous_vix: float) -> bool:
        """
        Check for VIX spike that should halt trading
        
        Args:
            current_vix: Current VIX level
            previous_vix: Previous VIX level for comparison
            
        Returns:
            True if VIX spike detected
        """
        if current_vix > previous_vix + self.metrics.vix_spike_threshold:
            self.halt_trading(f"VIX spike detected: {previous_vix:.1f} -> {current_vix:.1f}")
            return True
        
        return False
    
    def check_emergency_halt(self) -> bool:
        """Check if emergency halt flag file exists"""
        return os.path.exists("data/emergency_halt.flag")
    
    def is_trading_allowed(self) -> Tuple[bool, str]:
        """
        Check if trading is currently allowed
        
        Returns:
            Tuple of (allowed, reason)
        """
        if self.check_emergency_halt():
            return False, "Emergency halt flag exists"
        
        if self.metrics.is_halted:
            return False, self.metrics.halt_reason
        
        if self.metrics.daily_pnl < -self.metrics.daily_loss_limit:
            return False, f"Daily loss limit exceeded: ${self.metrics.daily_pnl:.2f}"
        
        if self.metrics.current_positions >= self.metrics.max_positions:
            return False, f"At maximum positions ({self.metrics.max_positions})"
        
        return True, "Trading allowed"
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get current risk metrics summary"""
        allowed, reason = self.is_trading_allowed()
        
        return {
            'trading_allowed': allowed,
            'status_reason': reason,
            'daily_pnl': self.metrics.daily_pnl,
            'daily_limit': self.metrics.daily_loss_limit,
            'positions': f"{self.metrics.current_positions}/{self.metrics.max_positions}",
            'trades_today': self.metrics.trades_today,
            'is_halted': self.metrics.is_halted,
            'halt_reason': self.metrics.halt_reason
        }


# Global risk manager instance  
_risk_manager = None

def get_risk_manager(config: Dict[str, Any]) -> RiskManager:
    """Get the global risk manager instance"""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager(config)
    return _risk_manager