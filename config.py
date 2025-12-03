"""
Configuration module for the trading bot.
All configuration values are centralized here.
"""
import os
from pathlib import Path

# Exchange configuration
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "delta")
# Default symbol aligned with Delta testnet template (BTCUSD perpetual)
SYMBOL = os.getenv("SYMBOL", "BTCUSD")
INTERVAL = os.getenv("INTERVAL", "5m")
CANDLE_COUNT = int(os.getenv("CANDLE_COUNT", "100"))

# Risk management
RISK_PERCENT = float(os.getenv("RISK_PERCENT", "0.02"))
STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", "0.02"))
MIN_TRADE_INTERVAL_SECONDS = int(os.getenv("MIN_TRADE_INTERVAL_SECONDS", "300"))

# Computer vision model configuration
CV_MODEL_WEIGHTS = os.getenv("CV_MODEL_WEIGHTS", "models/cv_hammer.pth")
CV_THRESHOLD = float(os.getenv("CV_THRESHOLD", "0.7"))
CHART_IMAGE_DIR = os.getenv("CHART_IMAGE_DIR", "chart_images")

# Delta Exchange configuration (default: demo/testnet mode)
# IMPORTANT: Update these with your actual Delta Exchange demo account API keys
# Get them from: Delta Exchange → API Management
DELTA_API_KEY = os.getenv("DELTA_API_KEY", "rC9EH0b8wn3t4qQ3bSV92UFigGBLvj")
DELTA_API_SECRET = os.getenv("DELTA_API_SECRET", "uxFMd4UIwOy5ifxyYgWnZhZPfnbzfhSq1ZsMebXtfFycowWTDp1RyfhDcvcc")
DELTA_TESTNET = os.getenv("DELTA_TESTNET", "true").lower() == "true"  # Default to demo/testnet

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Ensure directories exist
Path(CHART_IMAGE_DIR).mkdir(parents=True, exist_ok=True)
Path("models").mkdir(parents=True, exist_ok=True)

