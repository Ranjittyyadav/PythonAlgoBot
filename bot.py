"""
Main trading bot class.
"""
import logging
import time
import signal
import sys
from typing import Optional
from datetime import datetime, timedelta

from exchanges.base import CryptoExchangeAPI
from signals.base import SignalEngine
import config

logger = logging.getLogger(__name__)


class CryptoTradingBot:
    """Main trading bot that orchestrates exchange API and signal engine."""
    
    def __init__(
        self,
        exchange_api: CryptoExchangeAPI,
        signal_engine: SignalEngine,
        symbol: str = None,
        interval: str = None,
        candle_count: int = None,
        risk_percent: float = None,
        stop_loss_percent: float = None,
        min_trade_interval_seconds: int = None
    ):
        """
        Initialize the trading bot.
        
        Args:
            exchange_api: Exchange API instance
            signal_engine: Signal engine instance
            symbol: Trading pair symbol
            interval: Candle interval
            candle_count: Number of candles to fetch
            risk_percent: Risk percentage per trade
            stop_loss_percent: Stop loss percentage below entry
            min_trade_interval_seconds: Minimum seconds between trades
        """
        self.exchange_api = exchange_api
        self.signal_engine = signal_engine
        self.symbol = symbol or config.SYMBOL
        self.interval = interval or config.INTERVAL
        self.candle_count = candle_count or config.CANDLE_COUNT
        self.risk_percent = risk_percent or config.RISK_PERCENT
        self.stop_loss_percent = stop_loss_percent or config.STOP_LOSS_PERCENT
        self.min_trade_interval_seconds = min_trade_interval_seconds or config.MIN_TRADE_INTERVAL_SECONDS
        
        self.last_trade_time: Optional[datetime] = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Initialized CryptoTradingBot: symbol={self.symbol}, interval={self.interval}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        sys.exit(0)
    
    def can_place_trade(self) -> bool:
        """Check if enough time has passed since last trade."""
        if self.last_trade_time is None:
            return True
        
        time_since_last_trade = (datetime.now() - self.last_trade_time).total_seconds()
        return time_since_last_trade >= self.min_trade_interval_seconds
    
    def calculate_position_size(self, entry_price: float) -> float:
        """
        Calculate position size based on risk management.
        
        Args:
            entry_price: Entry price for the trade
            
        Returns:
            Position size in base currency
        """
        balance = self.exchange_api.get_account_balance("USDT")
        risk_amount = balance * self.risk_percent
        
        # Calculate stop loss price
        stop_loss_price = entry_price * (1 - self.stop_loss_percent)
        price_diff = entry_price - stop_loss_price
        
        if price_diff == 0:
            logger.warning("Price difference is zero, cannot calculate position size")
            return 0.0
        
        position_size = risk_amount / price_diff
        
        logger.info(f"Balance: {balance:.2f} USDT, Risk: {risk_amount:.2f} USDT, Position size: {position_size:.6f}")
        return position_size
    
    def calculate_stop_loss_price(self, candles: list, entry_price: float) -> float:
        """
        Calculate stop loss price based on hammer pattern low.
        
        Args:
            candles: List of recent candles
            entry_price: Entry price
            
        Returns:
            Stop loss price
        """
        if len(candles) == 0:
            return entry_price * (1 - self.stop_loss_percent)
        
        # Use the low of the last candle (hammer) as reference
        last_candle_low = candles[-1]['low']
        
        # Set stop loss slightly below the hammer low
        stop_loss = last_candle_low * (1 - self.stop_loss_percent)
        
        # Ensure stop loss is not too far from entry
        max_stop_loss = entry_price * (1 - self.stop_loss_percent * 2)
        stop_loss = min(stop_loss, max_stop_loss)
        
        return stop_loss
    
    def run(self):
        """Main trading loop."""
        logger.info("Starting trading bot...")
        self.running = True
        
        while self.running:
            try:
                # Fetch latest candles
                candles = self.exchange_api.fetch_live_candles(
                    self.symbol,
                    self.interval,
                    self.candle_count
                )
                
                if len(candles) == 0:
                    logger.warning("No candles received, skipping iteration")
                    time.sleep(10)
                    continue
                
                # Generate signal
                signal_result = self.signal_engine.generate_signal(candles)
                
                logger.info(f"Signal: is_buy={signal_result['is_buy']}, pattern={signal_result['pattern']}, score={signal_result['score']:.3f}")
                
                # Check if we should place a trade
                if signal_result['is_buy']:
                    if not self.can_place_trade():
                        time_remaining = self.min_trade_interval_seconds - (datetime.now() - self.last_trade_time).total_seconds()
                        logger.info(f"Trade cooldown active, {time_remaining:.0f} seconds remaining")
                    else:
                        # Get current price
                        current_price = self.exchange_api.get_ticker_price(self.symbol)
                        
                        if current_price == 0:
                            logger.error("Failed to get current price")
                            time.sleep(10)
                            continue
                        
                        # Calculate position size
                        position_size = self.calculate_position_size(current_price)
                        
                        if position_size <= 0:
                            logger.warning("Position size is zero or negative, skipping trade")
                            time.sleep(10)
                            continue
                        
                        # Calculate stop loss
                        stop_loss_price = self.calculate_stop_loss_price(candles, current_price)
                        
                        logger.info(f"Placing BUY order: {position_size:.6f} {self.symbol} at {current_price:.2f}, stop loss: {stop_loss_price:.2f}")
                        
                        # Place order
                        order_result = self.exchange_api.place_market_order(
                            self.symbol,
                            "BUY",
                            position_size
                        )
                        
                        if order_result:
                            self.last_trade_time = datetime.now()
                            logger.info("Order placed successfully")
                        else:
                            logger.error("Failed to place order")
                
                # Wait before next iteration
                time.sleep(10)
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, shutting down...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(10)
        
        logger.info("Trading bot stopped")

