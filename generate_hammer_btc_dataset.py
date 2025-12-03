"""
Generate 40 PNG images of real BTC candlestick charts with bullish hammer patterns.
Each image is 1000x600 pixels, styled like TradingView, and saved to a ZIP file.
"""
import ccxt
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import zipfile
import os
from pathlib import Path
import time
from typing import List, Dict, Tuple, Optional

# Configuration
OUTPUT_DIR = "hammer_btc_20251125_images"
ZIP_FILENAME = "hammer_btc_20251125_dataset.zip"
DATE_PREFIX = "20251125"
TARGET_IMAGES = 40
CANDLES_PER_IMAGE = 40

# TradingView-like colors
COLOR_BULLISH = "#26a69a"  # Green
COLOR_BEARISH = "#d32f2f"  # Red
COLOR_GRID = "#e0e0e0"     # Light gray
COLOR_BG = "#ffffff"       # White


def fetch_candles(symbol: str, timeframe: str, limit: int, exchange_name: str = "binance") -> Optional[List[Dict]]:
    """
    Fetch candles from a crypto exchange using ccxt.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe (e.g., '1m', '5m', '15m')
        limit: Number of candles to fetch
        exchange_name: Exchange name (default: 'binance')
        
    Returns:
        List of candle dictionaries or None if failed
    """
    try:
        # Initialize exchange
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        # Fetch OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        # Convert to list of dicts
        candles = []
        for candle in ohlcv:
            candles.append({
                'timestamp': candle[0],
                'open': candle[1],
                'high': candle[2],
                'low': candle[3],
                'close': candle[4],
                'volume': candle[5]
            })
        
        print(f"✓ Fetched {len(candles)} candles for {symbol} {timeframe} from {exchange_name}")
        return candles
        
    except Exception as e:
        print(f"✗ Error fetching {symbol} {timeframe} from {exchange_name}: {e}")
        return None


def is_bullish_hammer(open_: float, high: float, low: float, close: float) -> bool:
    """
    Detect if a candle is a bullish hammer pattern.
    
    Requirements:
    - Candle must be bullish: close > open
    - Small body (body/range <= 0.3)
    - Long lower shadow (lower_shadow/body >= 2.0)
    - Small upper shadow (upper_shadow/body <= 0.3)
    
    Args:
        open_: Open price
        high: High price
        low: Low price
        close: Close price
        
    Returns:
        True if candle is a bullish hammer
    """
    # Must be bullish
    if close <= open_:
        return False
    
    # Calculate body and range
    body = abs(close - open_)
    range_ = high - low
    
    # Avoid division by zero and too small ranges
    if range_ < 0.0005 * open_ or body == 0:
        return False
    
    # Body should be small relative to range
    if body / range_ > 0.3:
        return False
    
    # Calculate shadows
    lower_shadow = min(open_, close) - low
    upper_shadow = high - max(open_, close)
    
    # Long lower shadow (at least 2x body)
    if lower_shadow / body < 2.0:
        return False
    
    # Small upper shadow (at most 0.3x body)
    if upper_shadow / body > 0.3:
        return False
    
    return True


def find_hammer_windows(candles: List[Dict], symbol: str, timeframe: str) -> List[Tuple[int, str, str]]:
    """
    Find windows of 40 candles ending with a bullish hammer.
    
    Args:
        candles: List of candle dictionaries
        symbol: Trading pair symbol
        timeframe: Timeframe string
        
    Returns:
        List of tuples: (start_index, symbol, timeframe)
    """
    windows = []
    
    # Need at least 40 candles
    if len(candles) < CANDLES_PER_IMAGE:
        return windows
    
    # Scan for hammers
    for i in range(CANDLES_PER_IMAGE - 1, len(candles)):
        candle = candles[i]
        
        if is_bullish_hammer(
            candle['open'],
            candle['high'],
            candle['low'],
            candle['close']
        ):
            # Found a hammer at index i
            start_idx = i - (CANDLES_PER_IMAGE - 1)
            windows.append((start_idx, symbol, timeframe))
    
    return windows


def plot_window_to_png(candles_window: List[Dict], output_path: str, index: int):
    """
    Plot a 40-candle window to a PNG file with TradingView-like styling.
    
    Args:
        candles_window: List of 40 candle dictionaries
        output_path: Path to save the PNG
        index: Image index for filename
    """
    # Create figure with exact size (1000x600 pixels at 100 DPI = 10x6 inches)
    fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)
    
    # Convert timestamps to datetime
    dates = [datetime.fromtimestamp(c['timestamp'] / 1000) for c in candles_window]
    
    # Prepare data
    opens = [c['open'] for c in candles_window]
    highs = [c['high'] for c in candles_window]
    lows = [c['low'] for c in candles_window]
    closes = [c['close'] for c in candles_window]
    
    # Plot candles
    for i, (date, open_, high, low, close) in enumerate(zip(dates, opens, highs, lows, closes)):
        # Determine color
        color = COLOR_BULLISH if close >= open_ else COLOR_BEARISH
        
        # Draw wick (vertical line from low to high)
        ax.plot([i, i], [low, high], color=color, linewidth=1.5, solid_capstyle='round')
        
        # Draw body (rectangle from open to close)
        body_bottom = min(open_, close)
        body_top = max(open_, close)
        body_height = body_top - body_bottom
        
        # Ensure minimum body height for visibility
        if body_height < (high - low) * 0.01:
            body_height = (high - low) * 0.01
            body_bottom = (open_ + close) / 2 - body_height / 2
            body_top = (open_ + close) / 2 + body_height / 2
        
        rect = plt.Rectangle(
            (i - 0.3, body_bottom),
            0.6,
            body_height,
            facecolor=color,
            edgecolor=color,
            linewidth=0.5
        )
        ax.add_patch(rect)
    
    # Set x-axis
    ax.set_xlim(-0.5, CANDLES_PER_IMAGE - 0.5)
    ax.set_xticks(range(0, CANDLES_PER_IMAGE, max(1, CANDLES_PER_IMAGE // 8)))
    ax.set_xticklabels([
        dates[i].strftime('%H:%M') if i < len(dates) else ''
        for i in range(0, CANDLES_PER_IMAGE, max(1, CANDLES_PER_IMAGE // 8))
    ], rotation=45, ha='right')
    ax.set_xlabel('Time', color='#666666', fontsize=10)
    
    # Set y-axis (right side, like TradingView)
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.set_ylabel('Price', color='#666666', fontsize=10, rotation=-90, labelpad=20)
    
    # Format y-axis
    price_min = min(lows)
    price_max = max(highs)
    price_range = price_max - price_min
    margin = price_range * 0.05  # 5% margin
    
    ax.set_ylim(price_min - margin, price_max + margin)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Grid
    ax.grid(True, color=COLOR_GRID, linestyle='-', linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)
    
    # Remove top and right spines (keep only left and bottom for grid)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    
    # Tight layout and save
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight', facecolor=COLOR_BG, edgecolor='none')
    plt.close()
    
    print(f"  → Saved: {output_path}")


def main():
    """Main function to generate the dataset."""
    print("=" * 70)
    print("BTC Bullish Hammer Dataset Generator")
    print("=" * 70)
    print(f"Target: {TARGET_IMAGES} images")
    print(f"Date prefix: {DATE_PREFIX}")
    print()
    
    # Create output directory
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    
    # Configuration for data fetching
    symbols = ['BTC/USDT', 'BTC/USDC', 'BTC/USD']
    timeframes = ['1m', '5m', '15m']
    exchanges = ['binance', 'coinbase', 'kraken']  # Try multiple exchanges for variety
    
    # Fetch parameters
    candles_per_fetch = 1000  # Fetch large blocks to find hammers
    
    # Storage
    all_windows = []  # List of (start_idx, candles, symbol, timeframe, timestamp)
    seen_windows = set()  # For de-duplication: (symbol, timeframe, last_candle_timestamp)
    
    print("Step 1: Fetching market data and finding hammer patterns...")
    print("-" * 70)
    
    # Fetch candles and find hammers
    for exchange_name in exchanges:
        for symbol in symbols:
            for timeframe in timeframes:
                if len(all_windows) >= TARGET_IMAGES:
                    break
                
                # Fetch candles
                candles = fetch_candles(symbol, timeframe, candles_per_fetch, exchange_name)
                if candles is None or len(candles) < CANDLES_PER_IMAGE:
                    continue
                
                # Find hammer windows
                windows = find_hammer_windows(candles, symbol, timeframe)
                
                for start_idx, sym, tf in windows:
                    if len(all_windows) >= TARGET_IMAGES:
                        break
                    
                    # Extract window
                    window_candles = candles[start_idx:start_idx + CANDLES_PER_IMAGE]
                    last_candle_timestamp = window_candles[-1]['timestamp']
                    
                    # De-duplicate
                    window_key = (sym, tf, last_candle_timestamp)
                    if window_key not in seen_windows:
                        seen_windows.add(window_key)
                        all_windows.append((start_idx, window_candles, sym, tf, last_candle_timestamp))
                        print(f"  ✓ Found hammer at {sym} {tf} (timestamp: {last_candle_timestamp})")
                
                # Small delay to avoid rate limits
                time.sleep(0.5)
        
        if len(all_windows) >= TARGET_IMAGES:
            break
    
    # Limit to target number
    all_windows = all_windows[:TARGET_IMAGES]
    
    if len(all_windows) < TARGET_IMAGES:
        print(f"\n⚠ Warning: Only found {len(all_windows)} hammer patterns (target: {TARGET_IMAGES})")
        print("  Continuing with available data...")
    
    print()
    print(f"Step 2: Generating {len(all_windows)} chart images...")
    print("-" * 70)
    
    # Generate images
    image_files = []
    for idx, (start_idx, window_candles, symbol, timeframe, timestamp) in enumerate(all_windows, 1):
        filename = f"hammer_btc_{DATE_PREFIX}_{idx:03d}.png"
        output_path = output_dir / filename
        
        plot_window_to_png(window_candles, str(output_path), idx)
        image_files.append(filename)
    
    print()
    print(f"Step 3: Creating ZIP archive...")
    print("-" * 70)
    
    # Create ZIP file
    zip_path = Path(ZIP_FILENAME)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename in image_files:
            file_path = output_dir / filename
            if file_path.exists():
                zipf.write(file_path, filename)
                print(f"  ✓ Added to ZIP: {filename}")
    
    print()
    print("=" * 70)
    print("Dataset Generation Complete!")
    print("=" * 70)
    print(f"Images created: {len(image_files)}")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"ZIP file: {zip_path.absolute()}")
    print(f"ZIP size: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
    print()
    print("Files in ZIP:")
    for i, filename in enumerate(image_files, 1):
        print(f"  {i:2d}. {filename}")
    print()
    print("✓ Done!")


if __name__ == "__main__":
    main()

