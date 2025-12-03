"""
Coinbase exchange API implementation.
"""
import logging
import time
import hmac
import hashlib
import base64
import requests
from typing import List, Dict, Optional, Any

from exchanges.base import CryptoExchangeAPI
import config

logger = logging.getLogger(__name__)


class CoinbaseAPI(CryptoExchangeAPI):
    """Coinbase exchange API implementation."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        api_secret: Optional[str] = None,
        passphrase: Optional[str] = None,
        sandbox: bool = True
    ):
        """
        Initialize Coinbase API client.
        
        Args:
            api_key: Coinbase API key
            api_secret: Coinbase API secret
            passphrase: Coinbase API passphrase
            sandbox: Whether to use sandbox (default: True)
        """
        self.api_key = api_key or config.COINBASE_API_KEY
        self.api_secret = api_secret or config.COINBASE_API_SECRET
        self.passphrase = passphrase or config.COINBASE_PASSPHRASE
        self.sandbox = sandbox
        
        if self.sandbox:
            self.base_url = "https://api-public.sandbox.exchange.coinbase.com"
        else:
            self.base_url = "https://api.exchange.coinbase.com"
        
        logger.info(f"Initialized CoinbaseAPI (sandbox={self.sandbox})")
    
    def _generate_signature(
        self, 
        timestamp: str, 
        method: str, 
        request_path: str, 
        body: str = ""
    ) -> str:
        """Generate HMAC SHA256 signature for authenticated requests."""
        message = f"{timestamp}{method}{request_path}{body}"
        hmac_key = base64.b64decode(self.api_secret)
        signature = hmac.new(hmac_key, message.encode('utf-8'), hashlib.sha256)
        return base64.b64encode(signature.digest()).decode('utf-8')
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Coinbase API.
        
        Args:
            method: HTTP method ('GET' or 'POST')
            endpoint: API endpoint
            params: Request parameters
            signed: Whether to sign the request
            
        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if signed:
            timestamp = str(time.time())
            body = ""
            if params and method == 'POST':
                import json
                body = json.dumps(params)
            
            signature = self._generate_signature(timestamp, method, endpoint, body)
            headers.update({
                'CB-ACCESS-KEY': self.api_key,
                'CB-ACCESS-SIGN': signature,
                'CB-ACCESS-TIMESTAMP': timestamp,
                'CB-ACCESS-PASSPHRASE': self.passphrase,
                'Content-Type': 'application/json'
            })
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Coinbase API request failed: {e}")
            raise
    
    def _convert_symbol(self, symbol: str) -> str:
        """Convert symbol format (e.g., BTCUSDT -> BTC-USDT)."""
        if 'USDT' in symbol:
            base = symbol.replace('USDT', '')
            return f"{base}-USDT"
        return symbol
    
    def fetch_live_candles(
        self, 
        symbol: str, 
        interval: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch live candlestick data from Coinbase."""
        try:
            # Convert interval format (5m -> 300, 1h -> 3600)
            interval_map = {
                '1m': 60, '5m': 300, '15m': 900,
                '1h': 3600, '4h': 14400, '1d': 86400
            }
            granularity = interval_map.get(interval, 300)
            
            coinbase_symbol = self._convert_symbol(symbol)
            params = {
                'start': int(time.time() - (limit * granularity)),
                'end': int(time.time()),
                'granularity': granularity
            }
            
            data = self._make_request('GET', f'/products/{coinbase_symbol}/candles', params)
            
            candles = []
            for candle in reversed(data):  # Coinbase returns newest first
                candles.append({
                    'open_time': int(candle[0]) * 1000,  # Convert to milliseconds
                    'open': float(candle[3]),
                    'high': float(candle[2]),
                    'low': float(candle[1]),
                    'close': float(candle[4]),
                    'volume': float(candle[5]),
                    'close_time': int(candle[0] + granularity) * 1000
                })
            
            logger.debug(f"Fetched {len(candles)} candles for {symbol}")
            return candles[-limit:]  # Return last N candles
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            return []
    
    def get_account_balance(self, asset: str = "USDT") -> float:
        """Get account balance for a specific asset."""
        try:
            data = self._make_request('GET', '/accounts', signed=True)
            
            for account in data:
                if account['currency'] == asset:
                    return float(account['available'])
            
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
        """Place a market order on Coinbase."""
        try:
            coinbase_symbol = self._convert_symbol(symbol)
            params = {
                'product_id': coinbase_symbol,
                'side': side.lower(),
                'type': 'market',
                'size': str(quantity)
            }
            
            data = self._make_request('POST', '/orders', params, signed=True)
            logger.info(f"Order placed: {side} {quantity} {symbol} - Order ID: {data.get('id')}")
            return data
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def get_ticker_price(self, symbol: str) -> float:
        """Get current ticker price for a symbol."""
        try:
            coinbase_symbol = self._convert_symbol(symbol)
            data = self._make_request('GET', f'/products/{coinbase_symbol}/ticker')
            return float(data['price'])
        except Exception as e:
            logger.error(f"Error fetching ticker price: {e}")
            return 0.0

