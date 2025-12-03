"""
Chart rendering utilities for converting candle data to images.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import mplfinance as mpf
from datetime import datetime

logger = logging.getLogger(__name__)


def render_candles_to_image(
    candles: List[Dict[str, Any]], 
    out_path: str, 
    last_n: int = 40
) -> str:
    """
    Render candlestick chart to an image file.
    
    Args:
        candles: List of candle dictionaries with keys: open_time, open, high, low, close, volume
        out_path: Output file path for the image
        last_n: Number of most recent candles to render
        
    Returns:
        Path to the rendered image file
    """
    if len(candles) == 0:
        raise ValueError("Cannot render empty candle list")
    
    # Take last N candles
    recent_candles = candles[-last_n:] if len(candles) > last_n else candles
    
    # Convert to DataFrame
    data = []
    for candle in recent_candles:
        # Convert timestamp to datetime
        if isinstance(candle['open_time'], int):
            # Assume milliseconds if > 1e10, otherwise seconds
            if candle['open_time'] > 1e10:
                dt = datetime.fromtimestamp(candle['open_time'] / 1000)
            else:
                dt = datetime.fromtimestamp(candle['open_time'])
        else:
            dt = pd.to_datetime(candle['open_time'])
        
        data.append({
            'Date': dt,
            'Open': candle['open'],
            'High': candle['high'],
            'Low': candle['low'],
            'Close': candle['close'],
            'Volume': candle.get('volume', 0)
        })
    
    df = pd.DataFrame(data)
    df.set_index('Date', inplace=True)
    
    # Ensure output directory exists
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Render chart
    try:
        mpf.plot(
            df,
            type='candle',
            volume=False,
            style='charles',
            savefig=dict(fname=out_path, dpi=100, bbox_inches='tight'),
            figsize=(10, 6),
            show_nontrading=False
        )
        logger.debug(f"Chart rendered to {out_path}")
        return out_path
    except Exception as e:
        logger.error(f"Error rendering chart: {e}")
        raise

