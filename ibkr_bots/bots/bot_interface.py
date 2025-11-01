"""
Oriphim Bot Interface - Common interface for all trading bots
Provides standardized callable interface for SaaS execution
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class LogLevel(Enum):
    """Log levels for bot messaging"""
    DEBUG = "debug"
    INFO = "info" 
    WARNING = "warning"
    ERROR = "error"


@dataclass
class BotMessage:
    """Structured message from bot execution"""
    timestamp: datetime
    level: LogLevel
    message: str
    context: Dict[str, Any]
    
    def to_json(self) -> str:
        """Convert to JSON string for transmission"""
        return json.dumps({
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'message': self.message,
            'context': self.context
        })


class OriphimBot(ABC):
    """Base class for all Oriphim trading bots"""
    
    def __init__(self, config: Dict[str, Any], mode: str = 'paper'):
        self.config = config
        self.mode = mode  # 'paper' or 'live'
        self.running = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    def get_bot_kind(self) -> str:
        """Return the bot type identifier"""
        pass
        
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate bot configuration"""
        pass
        
    @abstractmethod
    def run(self) -> Iterator[BotMessage]:
        """Main bot execution - yields messages for real-time streaming"""
        pass
    
    def stop(self):
        """Signal bot to stop execution"""
        self.running = False
        
    def log(self, level: LogLevel, message: str, **context) -> BotMessage:
        """Create and return a structured log message"""
        msg = BotMessage(
            timestamp=datetime.now(),
            level=level,
            message=message,
            context=context
        )
        
        # Also log to Python logger
        getattr(self.logger, level.value)(f"{message} {context}")
        
        return msg


# Factory function for creating bots
def create_bot(kind: str, config: Dict[str, Any], mode: str = 'paper') -> OriphimBot:
    """Create bot instance based on kind"""
    from .bot_A_putlite_refactored import PutLiteBot
    from .bot_B_buywrite_refactored import BuyWriteBot  
    from .bot_C_condor_refactored import CondorBot
    from .bot_D_gammaburst_refactored import GammaBurstBot
    
    bot_classes = {
        'putlite': PutLiteBot,
        'buywrite': BuyWriteBot,
        'condor': CondorBot,
        'gammaburst': GammaBurstBot
    }
    
    if kind not in bot_classes:
        raise ValueError(f"Unknown bot kind: {kind}")
        
    return bot_classes[kind](config, mode)


# Main runner function for SaaS execution
def run_bot(kind: str, config: Dict[str, Any], mode: str = 'paper') -> Iterator[str]:
    """
    Main entry point for bot execution from Runner
    Yields JSON log messages for real-time streaming
    """
    try:
        bot = create_bot(kind, config, mode)
        
        # Validate configuration
        if not bot.validate_config(config):
            yield BotMessage(
                timestamp=datetime.now(),
                level=LogLevel.ERROR,
                message=f"Invalid configuration for {kind} bot",
                context={'config': config}
            ).to_json()
            return
            
        # Start bot execution
        for message in bot.run():
            yield message.to_json()
            
    except Exception as e:
        yield BotMessage(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            message=f"Bot execution failed: {str(e)}",
            context={'error_type': type(e).__name__, 'kind': kind}
        ).to_json()