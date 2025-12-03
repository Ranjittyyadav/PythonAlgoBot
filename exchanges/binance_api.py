"""
Binance exchange API implementation.
"""
import logging
import time
import hmac
import hashlib
import requests
from typing import List, Dict, Optional, Any
from urllib.parse import urlencode

from exchanges.base import CryptoExchangeAPI
import config

logger = logging.getLogger(__name__)


class BinanceAPI(CryptoExchangeAPI):
    """Binance exchange API implementation."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        api_secret: Optional[str] = None,
        testnet: bool = True
    ):
        """
        Initialize Binance API client.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Whether to use testnet (default: True)
        """
        self.api_key = api_key or config.BINANCE_API_KEY
        self.api_secret = api_secret or config.BINANCE_API_SECRET
        self.testnet = testnet
        
        if self.testnet:
            self.base_url = "https://testnet.binance.vision/api"
        else:
            self.base_url = "https://api.binance.com/api"
        
        logger.info(f"Initialized BinanceAPI (testnet={self.testnet})")
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for authenticated requests."""
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Binance API.
        
        Args:
            method: HTTP method ('GET' or 'POST')
            endpoint: API endpoint
            params: Request parameters
            signed: Whether to sign the request
            
        Returns:
            JSON response as dictionary
        """
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
            headers['X-MBX-APIKEY'] = self.api_key
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, params=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Binance API request failed: {e}")
            raise
    
    def fetch_live_candles(
        self, 
        symbol: str, 
        interval: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch live candlestick data from Binance."""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            data = self._make_request('GET', '/v3/klines', params)
            
            candles = []
            for candle in data:
                candles.append({
                    'open_time': int(candle[0]),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5]),
                    'close_time': int(candle[6])
                })
            
            logger.debug(f"Fetched {len(candles)} candles for {symbol}")
            return candles
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            return []
    
    def get_account_balance(self, asset: str = "USDT") -> float:
        """Get account balance for a specific asset."""
        try:
            params = {}
            data = self._make_request('GET', '/v3/account', params, signed=True)
            
            for balance in data.get('balances', []):
                if balance['asset'] == asset:
                    return float(balance['free'])
            
            logger.warning(f"Asset {asset} not found in account")
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0.0
    
    def place_market_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float
    ) -> Optional[Dict[str, Any]]:
        """Place a market order on Binance."""
        try:
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': 'MARKET',
                'quantity': quantity
            }
            
            data = self._make_request('POST', '/v3/order', params, signed=True)
            logger.info(f"Order placed: {side} {quantity} {symbol} - Order ID: {data.get('orderId')}")
            return data
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def get_ticker_price(self, symbol: str) -> float:
        """Get current ticker price for a symbol."""
        try:
            params = {'symbol': symbol}
            data = self._make_request('GET', '/v3/ticker/price', params)
            return float(data['price'])
        except Exception as e:
            logger.error(f"Error fetching ticker price: {e}")
            return 0.0

