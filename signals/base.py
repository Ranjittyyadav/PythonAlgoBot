"""
Base class for signal engines.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class SignalEngine(ABC):
    """Abstract base class for trading signal engines."""
    
    @abstractmethod
    def generate_signal(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a trading signal based on candle data.
        
        Args:
            candles: List of candle dictionaries with keys: open_time, open, high, low, close, volume, close_time
            
        Returns:
            Dictionary with keys:
                - is_buy: bool - Whether to place a buy order
                - pattern: str | None - Pattern name if detected (e.g., "bullish_hammer")
                - score: float - Confidence score (0.0 to 1.0)
        """
        pass

