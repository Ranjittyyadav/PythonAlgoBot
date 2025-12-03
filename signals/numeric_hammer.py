"""
Numeric pattern-based bullish hammer signal engine.
"""
import logging
from typing import List, Dict, Any

from signals.base import SignalEngine

logger = logging.getLogger(__name__)


class NumericHammerSignalEngine(SignalEngine):
    """Signal engine that detects bullish hammer patterns using numeric rules."""
    
    def generate_signal(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect bullish hammer pattern using numeric rules.
        
        A bullish hammer pattern is characterized by:
        - Small body (open/close) near the top of the candle
        - Long lower wick (at least 2x the body size)
        - Little to no upper wick
        - Occurs after a downtrend
        
        Args:
            candles: List of candle dictionaries
            
        Returns:
            Signal dictionary with is_buy, pattern, and score
        """
        if len(candles) < 2:
            return {"is_buy": False, "pattern": None, "score": 0.0}
        
        # Get the last candle
        last_candle = candles[-1]
        open_price = last_candle['open']
        high = last_candle['high']
        low = last_candle['low']
        close = last_candle['close']
        
        # Calculate body and wicks
        body_size = abs(close - open_price)
        upper_wick = high - max(open_price, close)
        lower_wick = min(open_price, close) - low
        total_range = high - low
        
        # Avoid division by zero
        if total_range == 0:
            return {"is_buy": False, "pattern": None, "score": 0.0}
        
        # Check for downtrend (previous candle closed lower)
        prev_candle = candles[-2]
        is_downtrend = prev_candle['close'] > close
        
        # Hammer criteria:
        # 1. Lower wick should be at least 2x the body size
        # 2. Body should be in upper half of the candle
        # 3. Upper wick should be small (less than body size)
        # 4. Should occur after a downtrend
        
        lower_wick_ratio = lower_wick / total_range if total_range > 0 else 0
        body_position = (min(open_price, close) - low) / total_range if total_range > 0 else 0
        
        is_hammer = (
            lower_wick >= 2 * body_size and
            body_position >= 0.6 and  # Body in upper 40% of candle
            upper_wick <= body_size and
            is_downtrend
        )
        
        if is_hammer:
            # Calculate confidence score based on how well it matches criteria
            score = min(1.0, (
                0.3 * (1.0 if lower_wick >= 2 * body_size else lower_wick / (2 * body_size)) +
                0.3 * body_position +
                0.2 * (1.0 if upper_wick <= body_size else max(0, 1 - (upper_wick / body_size))) +
                0.2 * (1.0 if is_downtrend else 0.5)
            ))
            
            logger.info(f"Bullish hammer detected! Score: {score:.2f}")
            return {
                "is_buy": True,
                "pattern": "bullish_hammer",
                "score": score
            }
        
        return {"is_buy": False, "pattern": None, "score": 0.0}

