"""
Script to generate a demo candlestick chart image for training data.
This shows what format the images should be in for the CV model.
"""
import pandas as pd
import mplfinance as mpf
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path

def generate_demo_chart(output_path: str, chart_type: str = "hammer"):
    """
    Generate a demo candlestick chart image.
    
    Args:
        output_path: Path to save the image
        chart_type: 'hammer' or 'none' - determines the pattern shown
    """
    # Create sample data
    dates = pd.date_range(start=datetime.now() - timedelta(days=5), periods=40, freq='5min')
    
    # Generate base price data
    base_price = 50000
    prices = []
    current_price = base_price
    
    for i in range(40):
        # Add some volatility
        change = np.random.normal(0, 100)
        current_price += change
        prices.append(current_price)
    
    # Create OHLC data
    data = []
    for i, price in enumerate(prices):
        # Create realistic OHLC from price
        high = price + abs(np.random.normal(0, 50))
        low = price - abs(np.random.normal(0, 50))
        open_price = prices[i-1] if i > 0 else price
        close = price
        
        # For hammer pattern, modify the last candle
        if chart_type == "hammer" and i == 39:
            # Create a bullish hammer: small body at top, long lower wick
            body_size = abs(close - open_price) * 0.3  # Small body
            if close > open_price:
                open_price = close - body_size
            else:
                close = open_price + body_size
            
            # Long lower wick (2-3x body size)
            lower_wick = body_size * 2.5
            low = min(open_price, close) - lower_wick
            high = max(open_price, close) + body_size * 0.3  # Small upper wick
        
        data.append({
            'Date': dates[i],
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': np.random.uniform(100, 1000)
        })
    
    df = pd.DataFrame(data)
    df.set_index('Date', inplace=True)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Render chart
    mpf.plot(
        df,
        type='candle',
        volume=False,
        style='charles',
        savefig=dict(fname=output_path, dpi=100, bbox_inches='tight'),
        figsize=(10, 6),
        show_nontrading=False
    )
    
    print(f"Demo chart saved to: {output_path}")
    print(f"Chart type: {chart_type}")
    print(f"Image format: PNG")
    print(f"Size: 10x6 inches at 100 DPI")


if __name__ == "__main__":
    # Create demo directories
    Path("data/train/hammer").mkdir(parents=True, exist_ok=True)
    Path("data/train/none").mkdir(parents=True, exist_ok=True)
    
    # Generate demo images
    print("Generating demo candlestick chart images...")
    print("\n1. Generating HAMMER pattern example:")
    generate_demo_chart("data/train/hammer/demo_hammer.png", "hammer")
    
    print("\n2. Generating NONE (no hammer) pattern example:")
    generate_demo_chart("data/train/none/demo_none.png", "none")
    
    print("\n" + "="*60)
    print("Demo images generated successfully!")
    print("="*60)
    print("\nImage Specifications:")
    print("- Format: PNG")
    print("- Size: 10x6 inches (1000x600 pixels at 100 DPI)")
    print("- Style: Candlestick chart (charles style)")
    print("- Content: Last 40 candles")
    print("\nFor training your CV model:")
    print("1. Place hammer pattern images in: data/train/hammer/*.png")
    print("2. Place non-hammer images in: data/train/none/*.png")
    print("3. Run: python3 train_cv_model.py --data_dir data/train")

