"""
Base class for cryptocurrency exchange APIs.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any


class CryptoExchangeAPI(ABC):
    """Abstract base class for cryptocurrency exchange APIs."""
    
    @abstractmethod
    def fetch_live_candles(
        self, 
        symbol: str, 
        interval: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch live candlestick data from the exchange.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Candle interval (e.g., '5m', '1h')
            limit: Number of candles to fetch
            
        Returns:
            List of candle dictionaries with keys: open_time, open, high, low, close, volume, close_time
        """
        pass
    
    @abstractmethod
    def get_account_balance(self, asset: str = "USDT") -> float:
        """
        Get account balance for a specific asset.
        
        Args:
            asset: Asset symbol (e.g., 'USDT', 'BTC')
            
        Returns:
            Available balance as float
        """
        pass
    
    @abstractmethod
    def place_market_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float
    ) -> Optional[Dict[str, Any]]:
        """
        Place a market order on the exchange.
        
        Args:
            symbol: Trading pair symbol
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            
        Returns:
            Order response dictionary or None if failed
        """
        pass
    
    @abstractmethod
    def get_ticker_price(self, symbol: str) -> float:
        """
        Get current ticker price for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Current price as float
        """
        pass

