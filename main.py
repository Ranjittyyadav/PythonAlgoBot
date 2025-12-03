"""
Main entry point for the trading bot.
"""
import logging
import os
import sys
from pathlib import Path

from exchanges.delta_api import DeltaAPI
from signals.numeric_hammer import NumericHammerSignalEngine
from signals.cv_hammer import CVHammerSignalEngine
from bot import CryptoTradingBot
import config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def create_exchange_api():
    """Create and return the Delta Exchange API instance."""
    exchange_name = config.EXCHANGE_NAME.lower()
    
    if exchange_name == "delta":
        return DeltaAPI(testnet=config.DELTA_TESTNET)
    else:
        logger.warning(f"Unknown exchange '{exchange_name}', defaulting to Delta Exchange")
        return DeltaAPI(testnet=config.DELTA_TESTNET)


def create_signal_engine(engine_type: str = None):
    """
    Create and return the appropriate signal engine instance.
    
    Args:
        engine_type: 'numeric' or 'cv'. If None, auto-detect based on model availability.
        
    Returns:
        SignalEngine instance
    """
    if engine_type is None:
        engine_type = os.getenv("SIGNAL_ENGINE", "auto")
    
    engine_type = engine_type.lower()
    
    if engine_type == "numeric":
        logger.info("Using NumericHammerSignalEngine")
        return NumericHammerSignalEngine()
    
    elif engine_type == "cv":
        model_path = Path(config.CV_MODEL_WEIGHTS)
        if not model_path.exists():
            logger.warning(f"CV model weights not found at {model_path}, falling back to numeric engine")
            return NumericHammerSignalEngine()
        
        logger.info(f"Using CVHammerSignalEngine with model at {model_path}")
        return CVHammerSignalEngine(
            model_weights_path=str(model_path),
            threshold=config.CV_THRESHOLD,
            image_dir=config.CHART_IMAGE_DIR
        )
    
    elif engine_type == "auto":
        # Auto-detect: try CV first, fallback to numeric
        model_path = Path(config.CV_MODEL_WEIGHTS)
        if model_path.exists():
            logger.info(f"Auto-detected CV model at {model_path}, using CVHammerSignalEngine")
            return CVHammerSignalEngine(
                model_weights_path=str(model_path),
                threshold=config.CV_THRESHOLD,
                image_dir=config.CHART_IMAGE_DIR
            )
        else:
            logger.info("No CV model found, using NumericHammerSignalEngine")
            return NumericHammerSignalEngine()
    
    else:
        raise ValueError(f"Unsupported signal engine type: {engine_type}")


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("CryptoTradingBot Starting")
    logger.info("=" * 60)
    logger.info(f"Exchange: {config.EXCHANGE_NAME}")
    logger.info(f"Symbol: {config.SYMBOL}")
    logger.info(f"Interval: {config.INTERVAL}")
    logger.info(f"Risk Percent: {config.RISK_PERCENT}")
    logger.info(f"Stop Loss Percent: {config.STOP_LOSS_PERCENT}")
    
    try:
        # Create exchange API
        exchange_api = create_exchange_api()
        
        # Create signal engine
        engine_type = os.getenv("SIGNAL_ENGINE", "auto")
        signal_engine = create_signal_engine(engine_type)
        
        # Create and run bot
        bot = CryptoTradingBot(
            exchange_api=exchange_api,
            signal_engine=signal_engine
        )
        
        bot.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

