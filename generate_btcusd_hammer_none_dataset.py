"""
Generate BTCUSD candlestick chart images for BOTH:
- bullish hammer patterns  (label: hammer)
- non-hammer / "none" patterns (label: none)

Output layout (relative to repo root):
- data/train/hammer/*.png
- data/train/none/*.png

Uses public historical data via ccxt (no API key needed) and
draws TradingView-style 40-candle windows, similar to the existing
`generate_hammer_btc_dataset.py` script.
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

import ccxt
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

# Target counts per class
TARGET_HAMMER_IMAGES = 40
TARGET_NONE_IMAGES = 40

# Candles per image (40 matches CV model and renderer)
CANDLES_PER_IMAGE = 40

# Symbol / timeframe (spot BTC vs USD stablecoins)
SYMBOLS = ["BTC/USDT", "BTC/USDC", "BTC/USD"]
TIMEFRAMES = ["5m"]  # focus on 5m for hammer training
EXCHANGES = ["binance", "coinbase", "kraken"]

# Output directories (train set)
BASE_DIR = Path("data/train")
HAMMER_DIR = BASE_DIR / "hammer"
NONE_DIR = BASE_DIR / "none"

# TradingView-like colors
COLOR_BULLISH = "#26a69a"  # Green
COLOR_BEARISH = "#d32f2f"  # Red
COLOR_GRID = "#e0e0e0"     # Light gray
COLOR_BG = "#ffffff"       # White


# -----------------------------------------------------------------------------
# DATA FETCHING
# -----------------------------------------------------------------------------

def fetch_candles(
    symbol: str,
    timeframe: str,
    limit: int,
    exchange_name: str = "binance",
) -> Optional[List[Dict]]:
    """
    Fetch candles from a crypto exchange using ccxt.
    Returns list of dicts with keys: timestamp, open, high, low, close, volume.
    """
    try:
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class({
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })

        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

        candles = []
        for c in ohlcv:
            candles.append(
                {
                    "timestamp": c[0],
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5]),
                }
            )

        print(f"✓ Fetched {len(candles)} candles for {symbol} {timeframe} from {exchange_name}")
        return candles

    except Exception as e:
        print(f"✗ Error fetching {symbol} {timeframe} from {exchange_name}: {e}")
        return None


# -----------------------------------------------------------------------------
# PATTERN DETECTION (same logic as generate_hammer_btc_dataset.py)
# -----------------------------------------------------------------------------

def is_bullish_hammer(open_: float, high: float, low: float, close: float) -> bool:
    """Return True if candle is a bullish hammer."""
    # Must be bullish
    if close <= open_:
        return False

    body = abs(close - open_)
    range_ = high - low

    # Avoid division by zero or tiny ranges
    if range_ < 0.0005 * open_ or body == 0:
        return False

    # Body should be small relative to range
    if body / range_ > 0.3:
        return False

    lower_shadow = min(open_, close) - low
    upper_shadow = high - max(open_, close)

    # Long lower shadow (>= 2x body)
    if lower_shadow / body < 2.0:
        return False

    # Small upper shadow (<= 0.3x body)
    if upper_shadow / body > 0.3:
        return False

    return True


def find_labelled_windows(
    candles: List[Dict],
) -> List[Tuple[int, bool]]:
    """
    Scan a candle series and return:
    - list of (start_index, is_hammer_window)

    A window is considered:
    - hammer window if the LAST candle in the 40-candle window is a bullish hammer
    - none window  if the LAST candle is NOT a hammer AND no other candles in
      that window are hammers (to keep it "clean none").
    """
    labelled: List[Tuple[int, bool]] = []

    if len(candles) < CANDLES_PER_IMAGE:
        return labelled

    for i in range(CANDLES_PER_IMAGE - 1, len(candles)):
        # Index of last candle in the window
        last_idx = i
        first_idx = i - (CANDLES_PER_IMAGE - 1)

        window = candles[first_idx : last_idx + 1]
        last = window[-1]

        last_is_hammer = is_bullish_hammer(
            last["open"], last["high"], last["low"], last["close"]
        )

        if last_is_hammer:
            labelled.append((first_idx, True))
        else:
            # Check if any candle in window is hammer; if so, skip as "none"
            any_hammer = False
            for c in window:
                if is_bullish_hammer(c["open"], c["high"], c["low"], c["close"]):
                    any_hammer = True
                    break
            if not any_hammer:
                labelled.append((first_idx, False))

    return labelled


# -----------------------------------------------------------------------------
# PLOTTING
# -----------------------------------------------------------------------------

def plot_window_to_png(
    candles_window: List[Dict],
    output_path: Path,
):
    """Plot a 40-candle window to a PNG file with TradingView-like styling."""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    # Convert timestamps to datetime
    dates = [datetime.fromtimestamp(c["timestamp"] / 1000) for c in candles_window]

    opens = [c["open"] for c in candles_window]
    highs = [c["high"] for c in candles_window]
    lows = [c["low"] for c in candles_window]
    closes = [c["close"] for c in candles_window]

    for i, (open_, high, low, close) in enumerate(
        zip(opens, highs, lows, closes)
    ):
        color = COLOR_BULLISH if close >= open_ else COLOR_BEARISH

        # Wick
        ax.plot([i, i], [low, high], color=color, linewidth=1.5, solid_capstyle="round")

        body_bottom = min(open_, close)
        body_top = max(open_, close)
        body_height = body_top - body_bottom

        # Min body height for visibility
        if body_height < (high - low) * 0.01:
            body_height = (high - low) * 0.01
            mid = (open_ + close) / 2
            body_bottom = mid - body_height / 2
            body_top = mid + body_height / 2

        rect = plt.Rectangle(
            (i - 0.3, body_bottom),
            0.6,
            body_height,
            facecolor=color,
            edgecolor=color,
            linewidth=0.5,
        )
        ax.add_patch(rect)

    # X axis
    ax.set_xlim(-0.5, CANDLES_PER_IMAGE - 0.5)
    step = max(1, CANDLES_PER_IMAGE // 8)
    ax.set_xticks(range(0, CANDLES_PER_IMAGE, step))
    ax.set_xticklabels(
        [
            dates[i].strftime("%H:%M") if i < len(dates) else ""
            for i in range(0, CANDLES_PER_IMAGE, step)
        ],
        rotation=45,
        ha="right",
    )
    ax.set_xlabel("Time", color="#666666", fontsize=10)

    # Y axis
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.set_ylabel("Price", color="#666666", fontsize=10, rotation=-90, labelpad=20)

    price_min = min(lows)
    price_max = max(highs)
    price_range = price_max - price_min
    margin = price_range * 0.05
    ax.set_ylim(price_min - margin, price_max + margin)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

    ax.grid(True, color=COLOR_GRID, linestyle="-", linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_color("#cccccc")
    ax.spines["bottom"].set_color("#cccccc")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=100, bbox_inches="tight", facecolor=COLOR_BG, edgecolor="none")
    plt.close()

    print(f"  → Saved: {output_path}")


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("BTCUSD Hammer / None Dataset Generator")
    print("=" * 70)
    print(f"Target hammer images: {TARGET_HAMMER_IMAGES}")
    print(f"Target none images  : {TARGET_NONE_IMAGES}")
    print()

    HAMMER_DIR.mkdir(parents=True, exist_ok=True)
    NONE_DIR.mkdir(parents=True, exist_ok=True)

    hammer_count = 0
    none_count = 0

    # To avoid duplicates: (symbol, timeframe, last_candle_ts)
    seen_keys = set()

    candles_per_fetch = 1500

    for exchange_name in EXCHANGES:
        for symbol in SYMBOLS:
            for timeframe in TIMEFRAMES:
                if hammer_count >= TARGET_HAMMER_IMAGES and none_count >= TARGET_NONE_IMAGES:
                    break

                candles = fetch_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=candles_per_fetch,
                    exchange_name=exchange_name,
                )
                if not candles or len(candles) < CANDLES_PER_IMAGE:
                    continue

                labelled = find_labelled_windows(candles)
                for start_idx, is_hammer in labelled:
                    if hammer_count >= TARGET_HAMMER_IMAGES and is_hammer:
                        continue
                    if none_count >= TARGET_NONE_IMAGES and not is_hammer:
                        continue

                    window = candles[start_idx : start_idx + CANDLES_PER_IMAGE]
                    last_ts = window[-1]["timestamp"]
                    key = (symbol, timeframe, last_ts, is_hammer)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    if is_hammer:
                        hammer_count += 1
                        fname = f"hammer_btc_{hammer_count:03d}.png"
                        out_path = HAMMER_DIR / fname
                    else:
                        none_count += 1
                        fname = f"none_btc_{none_count:03d}.png"
                        out_path = NONE_DIR / fname

                    plot_window_to_png(window, out_path)

                    if hammer_count >= TARGET_HAMMER_IMAGES and none_count >= TARGET_NONE_IMAGES:
                        break

            if hammer_count >= TARGET_HAMMER_IMAGES and none_count >= TARGET_NONE_IMAGES:
                break
        if hammer_count >= TARGET_HAMMER_IMAGES and none_count >= TARGET_NONE_IMAGES:
            break

    print()
    print("=" * 70)
    print("Generation complete.")
    print(f"Hammer images: {hammer_count} -> {HAMMER_DIR.resolve()}")
    print(f"None images  : {none_count} -> {NONE_DIR.resolve()}")
    print("=" * 70)


if __name__ == "__main__":
    main()


