"""
Event calendar and blackout management.
Handles CPI, FOMC, NFP, and earnings blackouts.
"""

import logging
from typing import Dict, Any, List, Set
from datetime import datetime, date, timedelta
import json

logger = logging.getLogger(__name__)


class EventCalendar:
    """Manages trading blackouts for major economic events and earnings"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Get event configuration
        events_config = config.get('events', {})
        self.blackout_kinds = set(events_config.get('blackout_kinds', []))
        self.manual_blackout = events_config.get('manual_blackout', False)
        
        # Initialize event calendar with known dates for 2025
        self._init_2025_calendar()
        
        logger.info(f"Event blackouts enabled for: {self.blackout_kinds}")
        if self.manual_blackout:
            logger.warning("Manual blackout override is ACTIVE")
    
    def _init_2025_calendar(self):
        """Initialize calendar with known major economic events for 2025"""
        
        # Federal Reserve FOMC meetings 2025 (typically 8 per year)
        fomc_dates = [
            "2025-01-29",  # Jan meeting
            "2025-03-19",  # Mar meeting  
            "2025-05-07",  # May meeting
            "2025-06-18",  # Jun meeting
            "2025-07-30",  # Jul meeting
            "2025-09-17",  # Sep meeting
            "2025-11-05",  # Nov meeting
            "2025-12-17",  # Dec meeting
        ]
        
        # CPI release dates (monthly, typically mid-month)
        cpi_dates = [
            "2025-01-15", "2025-02-12", "2025-03-12", "2025-04-10",
            "2025-05-14", "2025-06-11", "2025-07-10", "2025-08-13", 
            "2025-09-10", "2025-10-14", "2025-11-13", "2025-12-10"
        ]
        
        # Non-Farm Payrolls (first Friday of each month)
        nfp_dates = [
            "2025-01-03", "2025-02-07", "2025-03-07", "2025-04-04",
            "2025-05-02", "2025-06-06", "2025-07-04", "2025-08-01",
            "2025-09-05", "2025-10-03", "2025-11-07", "2025-12-05"
        ]
        
        # Store events by date
        self.events_by_date = {}
        
        for date_str in fomc_dates:
            if date_str not in self.events_by_date:
                self.events_by_date[date_str] = []
            self.events_by_date[date_str].append("FOMC")
        
        for date_str in cpi_dates:
            if date_str not in self.events_by_date:
                self.events_by_date[date_str] = []
            self.events_by_date[date_str].append("CPI")
        
        for date_str in nfp_dates:
            if date_str not in self.events_by_date:
                self.events_by_date[date_str] = []
            self.events_by_date[date_str].append("NFP")
        
        logger.info(f"Loaded {len(self.events_by_date)} event dates for 2025")
    
    def is_blackout(self, symbol: str, check_date: datetime = None) -> bool:
        """
        Check if trading should be blacked out due to events
        
        Args:
            symbol: Trading symbol to check
            check_date: Date to check (default: today)
            
        Returns:
            True if trading should be blacked out
        """
        if check_date is None:
            check_date = datetime.now()
        
        # Manual blackout override
        if self.manual_blackout:
            logger.info("Manual blackout is active")
            return True
        
        check_date_str = check_date.strftime("%Y-%m-%d")
        
        # Check for economic events
        events_today = self.events_by_date.get(check_date_str, [])
        
        for event_type in events_today:
            if event_type in self.blackout_kinds:
                logger.info(f"Trading blackout due to {event_type} on {check_date_str}")
                return True
        
        # Check for earnings (symbol-specific)
        if "EARNINGS" in self.blackout_kinds:
            if self._is_earnings_day(symbol, check_date):
                logger.info(f"Earnings blackout for {symbol} on {check_date_str}")
                return True
        
        return False
    
    def _is_earnings_day(self, symbol: str, check_date: datetime) -> bool:
        """
        Check if it's earnings day for a specific symbol
        
        For MVP, we'll use a simplified approach with known major earnings seasons.
        In production, you'd integrate with earnings calendar APIs.
        
        Args:
            symbol: Stock symbol
            check_date: Date to check
            
        Returns:
            True if likely earnings day
        """
        
        # Major earnings seasons (rough approximation)
        month = check_date.month
        day = check_date.day
        
        # Q1 earnings: Late April / Early May
        # Q2 earnings: Mid-Late July  
        # Q3 earnings: Late October / Early November
        # Q4 earnings: Late January / February
        
        earnings_seasons = [
            (1, 15, 2, 15),   # Q4 earnings: Jan 15 - Feb 15
            (4, 20, 5, 10),   # Q1 earnings: Apr 20 - May 10  
            (7, 15, 8, 5),    # Q2 earnings: Jul 15 - Aug 5
            (10, 20, 11, 10)  # Q3 earnings: Oct 20 - Nov 10
        ]
        
        # Check if we're in an earnings season
        for start_month, start_day, end_month, end_day in earnings_seasons:
            start_date = date(check_date.year, start_month, start_day)
            end_date = date(check_date.year, end_month, end_day)
            
            if start_date <= check_date.date() <= end_date:
                # During earnings season, be more conservative
                # For mega-cap tech stocks, assume higher probability
                mega_cap_tech = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'META', 'GOOGL']
                
                if symbol in mega_cap_tech:
                    # Higher probability for mega caps during earnings season
                    return (day - start_day) % 7 < 2  # ~2 days per week during season
                else:
                    # Lower probability for other stocks
                    return (day - start_day) % 10 < 1  # ~1 day per 10 during season
        
        return False
    
    def get_next_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming events in the next N days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of event dictionaries
        """
        upcoming_events = []
        today = date.today()
        
        for i in range(days_ahead):
            check_date = today + timedelta(days=i)
            date_str = check_date.strftime("%Y-%m-%d")
            
            events = self.events_by_date.get(date_str, [])
            
            for event_type in events:
                if event_type in self.blackout_kinds:
                    upcoming_events.append({
                        'date': date_str,
                        'event_type': event_type,
                        'description': self._get_event_description(event_type)
                    })
        
        return upcoming_events
    
    def _get_event_description(self, event_type: str) -> str:
        """Get human-readable description for event type"""
        descriptions = {
            'FOMC': 'Federal Reserve FOMC Meeting',
            'CPI': 'Consumer Price Index Release',
            'NFP': 'Non-Farm Payrolls Report', 
            'EARNINGS': 'Earnings Season'
        }
        
        return descriptions.get(event_type, event_type)
    
    def add_custom_blackout(self, date_str: str, event_type: str):
        """
        Add a custom blackout date
        
        Args:
            date_str: Date in YYYY-MM-DD format
            event_type: Type of event (will be added to blackout list)
        """
        if date_str not in self.events_by_date:
            self.events_by_date[date_str] = []
        
        self.events_by_date[date_str].append(event_type)
        
        # Add to blackout kinds if not already there
        self.blackout_kinds.add(event_type)
        
        logger.info(f"Added custom blackout: {event_type} on {date_str}")
    
    def set_manual_blackout(self, enabled: bool):
        """Enable or disable manual blackout override"""
        self.manual_blackout = enabled
        
        if enabled:
            logger.warning("Manual blackout ENABLED - all trading will be blocked")
        else:
            logger.info("Manual blackout DISABLED")
    
    def get_blackout_status(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive blackout status for a symbol
        
        Args:
            symbol: Symbol to check
            
        Returns:
            Dict with blackout information
        """
        now = datetime.now()
        is_blocked = self.is_blackout(symbol, now)
        
        today_events = self.events_by_date.get(now.strftime("%Y-%m-%d"), [])
        blocked_events = [e for e in today_events if e in self.blackout_kinds]
        
        upcoming = self.get_next_events(3)  # Next 3 days
        
        return {
            'symbol': symbol,
            'is_blackout': is_blocked,
            'manual_override': self.manual_blackout,
            'todays_events': blocked_events,
            'upcoming_events': upcoming,
            'blackout_types': list(self.blackout_kinds),
            'check_time': now.isoformat()
        }


# Global event calendar instance
_event_calendar = None

def get_event_calendar(config: Dict[str, Any]) -> EventCalendar:
    """Get the global event calendar instance"""
    global _event_calendar
    if _event_calendar is None:
        _event_calendar = EventCalendar(config)
    return _event_calendar