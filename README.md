# Python Trading Bot

A cryptocurrency trading bot with pluggable signal engines supporting both numeric pattern detection and computer vision-based candlestick classification.

## Features

- **Exchange Abstraction**: Support for multiple exchanges (Binance, Coinbase) with a unified API
- **Pluggable Signal Engines**: 
  - Numeric pattern detection (bullish hammer)
  - Computer vision-based pattern classification using PyTorch
- **Risk Management**: Configurable position sizing and stop-loss management
- **Chart Rendering**: Automatic candlestick chart generation for CV analysis
- **Robust Error Handling**: Graceful shutdown and comprehensive logging

## Architecture

```
PythonTradingBot/
├── config.py              # Centralized configuration
├── bot.py                 # Main trading bot class
├── main.py                # CLI entrypoint
├── train_cv_model.py      # CV model training script
├── exchanges/
│   ├── base.py           # Exchange API base class
│   └── delta_api.py      # Delta Exchange implementation
├── signals/
│   ├── base.py           # Signal engine base class
│   ├── numeric_hammer.py # Numeric pattern detector
│   └── cv_hammer.py      # Computer vision detector
├── models/
│   └── cv_model.py       # PyTorch model definition
└── charting/
    └── renderer.py       # Chart rendering utilities
```

## Installation

1. **Clone or navigate to the project directory**

2. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```
   
   **Note**: If you encounter issues installing `mplfinance`, it may require installing pre-release versions. In that case, run:
   ```bash
   pip3 install --pre mplfinance
   pip3 install -r requirements.txt
   ```
   
   **Note for macOS users**: Use `python3` and `pip3` instead of `python` and `pip`.

3. **Configure environment variables** (optional):
   Create a `.env` file or set environment variables:
   ```bash
   export EXCHANGE_NAME="delta"
   export SYMBOL="BTCUSDT"
   export INTERVAL="5m"
   export DELTA_API_KEY="your_api_key"
   export DELTA_API_SECRET="your_api_secret"
   export DELTA_TESTNET="true"  # Set to "true" for demo account, "false" for production
   export SIGNAL_ENGINE="numeric"  # or "cv" or "auto"
   ```

## Usage

### Running with Numeric Engine (No Training Required)

The numeric engine works out of the box and doesn't require any model training:

```bash
python3 main.py
```

Or explicitly specify the engine:
```bash
SIGNAL_ENGINE=numeric python3 main.py
```

### Training a Computer Vision Model

1. **Prepare training data**:
   Organize your candlestick chart images in the following structure:
   ```
   data/
   ├── train/
   │   ├── hammer/
   │   │   ├── chart1.png
   │   │   ├── chart2.png
   │   │   └── ...
   │   └── none/
   │       ├── chart1.png
   │       ├── chart2.png
   │       └── ...
   └── val/
       ├── hammer/
       │   └── ...
       └── none/
           └── ...
   ```
   
   **Image Format Specifications:**
   - **Format**: PNG (Portable Network Graphics)
   - **Size**: 10x6 inches (approximately 1000x600 pixels at 100 DPI)
   - **Style**: Candlestick chart using 'charles' style from mplfinance
   - **Content**: Last 40 candles displayed
   - **No volume bars**: Volume is hidden for cleaner pattern recognition
   
   **Generate Demo Images:**
   To see example images in the correct format, run:
   ```bash
   python3 generate_demo_chart.py
   ```
   This will create sample images in `data/train/hammer/` and `data/train/none/` folders.
   
   **Note**: The `chart_images/` folder is used by the bot at runtime to temporarily store rendered charts. For training, place your images in the `data/train/` directory structure above.

2. **Train the model**:
   ```bash
   python3 train_cv_model.py --data_dir data/train --val_dir data/val --epochs 10 --batch_size 32
   ```
   
   **📖 For detailed step-by-step instructions on collecting screenshots and training, see [TRAINING_GUIDE.md](TRAINING_GUIDE.md)**
   
   The trained model will be saved to `models/cv_hammer.pth` by default.

3. **Run with CV engine**:
   ```bash
   SIGNAL_ENGINE=cv python3 main.py
   ```

   Or use auto-detection (default):
   ```bash
   python3 main.py
   ```
   The bot will automatically use the CV engine if model weights are found, otherwise fallback to numeric.

## Configuration

All configuration is centralized in `config.py` and can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `EXCHANGE_NAME` | `delta` | Exchange to use (Delta Exchange) |
| `SYMBOL` | `BTCUSDT` | Trading pair symbol |
| `INTERVAL` | `5m` | Candle interval (`1m`, `5m`, `15m`, `1h`, etc.) |
| `CANDLE_COUNT` | `100` | Number of candles to fetch |
| `RISK_PERCENT` | `0.02` | Risk percentage per trade (2%) |
| `STOP_LOSS_PERCENT` | `0.02` | Stop loss percentage (2%) |
| `MIN_TRADE_INTERVAL_SECONDS` | `300` | Minimum seconds between trades |
| `CV_MODEL_WEIGHTS` | `models/cv_hammer.pth` | Path to CV model weights |
| `CV_THRESHOLD` | `0.7` | Confidence threshold for CV buy signal |
| `CHART_IMAGE_DIR` | `chart_images` | Directory for rendered charts |
| `DELTA_API_KEY` | `` | Delta Exchange API key |
| `DELTA_API_SECRET` | `` | Delta Exchange API secret |
| `DELTA_TESTNET` | `true` | Use Delta Exchange demo/testnet mode (default: true) |
| `SIGNAL_ENGINE` | `auto` | Signal engine type (`numeric`, `cv`, or `auto`) |

## Signal Engines

### NumericHammerSignalEngine

Detects bullish hammer patterns using numeric rules:
- Small body near the top of the candle
- Long lower wick (at least 2x body size)
- Little to no upper wick
- Occurs after a downtrend

### CVHammerSignalEngine

Uses a PyTorch ResNet18-based classifier to detect bullish hammer patterns from rendered candlestick charts. Requires a trained model.

## Exchange Support

### Delta Exchange (Default)

The bot is configured to use Delta Exchange by default with demo account support. Configure with:

**For Demo/Testnet Account:**
```bash
export EXCHANGE_NAME="delta"
export DELTA_API_KEY="your_demo_api_key"
export DELTA_API_SECRET="your_demo_api_secret"
export DELTA_TESTNET="true"  # Default is true for demo mode
```

**For Production Account:**
```bash
export EXCHANGE_NAME="delta"
export DELTA_API_KEY="your_production_api_key"
export DELTA_API_SECRET="your_production_api_secret"
export DELTA_TESTNET="false"
```

**Note**: 
- The bot defaults to demo/testnet mode for safety
- Delta Exchange uses product IDs instead of symbol strings - the bot automatically resolves symbols to product IDs
- Please refer to [Delta Exchange API documentation](https://docs.delta.exchange) for the latest endpoint specifications
- Demo accounts are typically managed through API key permissions on Delta Exchange

## Risk Management

The bot implements several risk management features:

- **Position Sizing**: Calculates position size based on account balance and risk percentage
- **Stop Loss**: Sets stop loss based on hammer pattern low or percentage below entry
- **Trade Cooldown**: Enforces minimum time between trades to prevent overtrading

## Logging

The bot uses Python's logging module with INFO level by default. Logs include:
- Signal generation results
- Order placement attempts
- Error messages
- Risk calculations

Set log level via:
```bash
export LOG_LEVEL="DEBUG"  # or INFO, WARNING, ERROR
```

## Graceful Shutdown

The bot handles SIGINT (Ctrl+C) and SIGTERM signals for graceful shutdown, ensuring orders are not interrupted mid-execution.

## Development

### Adding a New Signal Engine

1. Create a new class in `signals/` that inherits from `SignalEngine`
2. Implement the `generate_signal()` method
3. Update `main.py` to support the new engine type

### Adding a New Exchange

1. Create a new class in `exchanges/` that inherits from `CryptoExchangeAPI`
2. Implement all abstract methods
3. Update `main.py` to support the new exchange

## Notes

- The bot uses testnet/sandbox by default for safety
- Always test thoroughly before using with real funds
- The CV model requires training data - the numeric engine works without training
- Chart images are saved to `chart_images/` directory for debugging

## License

This project is provided as-is for educational purposes. Use at your own risk.

