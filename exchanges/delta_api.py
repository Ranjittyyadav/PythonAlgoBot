"""
Delta Exchange API implementation.
"""
import logging
import time
import hmac
import hashlib
import base64
import requests
from typing import List, Dict, Optional, Any
from urllib.parse import urlencode

from exchanges.base import CryptoExchangeAPI
import config

logger = logging.getLogger(__name__)


class DeltaAPI(CryptoExchangeAPI):
    """Delta Exchange API implementation."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        api_secret: Optional[str] = None,
        testnet: bool = False
    ):
        """
        Initialize Delta Exchange API client.
        
        Args:
            api_key: Delta Exchange API key
            api_secret: Delta Exchange API secret
            testnet: Whether to use testnet (default: False, Delta uses production by default)
        """
        self.api_key = api_key if api_key else config.DELTA_API_KEY
        self.api_secret = api_secret if api_secret else config.DELTA_API_SECRET
        self.testnet = testnet if testnet is not None else config.DELTA_TESTNET
        
        # Validate API keys
        if not self.api_key or not self.api_secret:
            logger.warning("⚠️  Delta Exchange API keys are not set!")
            logger.warning("   Please set DELTA_API_KEY and DELTA_API_SECRET in config.py")
            logger.warning("   or as environment variables.")
            logger.warning("   The bot will not be able to fetch balances or place orders.")
        
        # Delta Exchange API base URL
        # For demo/testnet accounts, use testnet API endpoint
        if self.testnet:
            # Use testnet API endpoint for demo accounts
            self.base_url = "https://testnet-api.delta.exchange"
            self.demo_url = None
        else:
            self.base_url = "https://api.delta.exchange"
            self.demo_url = None
        
        logger.info(f"Initialized DeltaAPI (testnet={self.testnet}, base_url={self.base_url})")
    
    def _generate_signature(
        self, 
        timestamp: str, 
        method: str, 
        path: str, 
        body: str = ""
    ) -> str:
        """
        Generate HMAC SHA256 signature for authenticated requests.
        
        Delta Exchange signature format: METHOD + PATH + TIMESTAMP + BODY
        The API secret should be used directly (not base64 decoded).
        """
        import json
        if isinstance(body, dict):
            body = json.dumps(body, separators=(',', ':'))
        elif not isinstance(body, str):
            body = str(body) if body else ""
        
        # Construct message: METHOD + PATH + TIMESTAMP + BODY
        message = f"{method}{path}{timestamp}{body}"
        
        # Generate HMAC SHA256 signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Delta Exchange API.
        
        Args:
            method: HTTP method ('GET' or 'POST')
            endpoint: API endpoint
            params: Request parameters (for GET requests)
            signed: Whether to sign the request
            json_data: JSON body data (for POST requests)
            
        Returns:
            JSON response as dictionary
        """
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        body = ""
        if signed:
            # Delta Exchange uses Unix timestamp in seconds (as string)
            timestamp = str(int(time.time()))
            
            # Prepare body for signature
            if json_data:
                import json
                body = json.dumps(json_data, separators=(',', ':'))
            elif method == 'GET':
                # For GET requests, body is empty in signature (even if params exist)
                body = ""
            else:
                body = ""
            
            # Generate signature
            signature = self._generate_signature(timestamp, method, endpoint, body)
            
            # Set authentication headers
            headers.update({
                'api-key': self.api_key,
                'timestamp': timestamp,
                'signature': signature
            })
            
            # Debug logging (only if API key is set)
            if self.api_key:
                logger.debug(f"Auth headers set for {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=json_data, params=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            # Delta Exchange wraps responses in a 'result' field
            if isinstance(result, dict) and 'result' in result:
                return result['result']
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                error_text = e.response.text if hasattr(e.response, 'text') else ""
                logger.error(f"Delta Exchange API authentication failed (401 Unauthorized)")
                logger.error(f"Response: {error_text}")
                
                # Check if it's invalid_api_key
                try:
                    error_json = e.response.json()
                    if error_json.get('error', {}).get('code') == 'invalid_api_key':
                        logger.error("")
                        logger.error("⚠️  INVALID API KEY ERROR")
                        logger.error("=" * 60)
                        logger.error("Possible causes:")
                        logger.error("  1. API key or secret is incorrect")
                        logger.error("  2. API key doesn't have 'Read' permission")
                        logger.error("  3. API key has expired or been revoked")
                        logger.error("  4. Using wrong API keys (demo vs production)")
                        logger.error("")
                        logger.error("Solutions:")
                        logger.error("  1. Run: python3 test_delta_api.py")
                        logger.error("  2. Verify API keys in Delta Exchange → API Management")
                        logger.error("  3. Ensure API key has 'Read' permission enabled")
                        logger.error("  4. Generate new API keys if needed")
                        logger.error("=" * 60)
                except:
                    pass
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Delta Exchange API request failed: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def _get_product_id(self, symbol: str) -> Optional[int]:
        """
        Get product_id from symbol by querying products endpoint.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Product ID as integer, or None if not found
        """
        try:
            # Cache product IDs to avoid repeated API calls
            if not hasattr(self, '_product_cache'):
                self._product_cache = {}
            
            if symbol in self._product_cache:
                return self._product_cache[symbol]
            
            # Fetch all products
            data = self._make_request('GET', '/v2/products')
            
            # Search for matching symbol
            if isinstance(data, list):
                for product in data:
                    product_symbol = product.get('symbol', '')
                    if product_symbol == symbol or product_symbol == f"{symbol}PERP":
                        product_id = product.get('id')
                        if product_id:
                            self._product_cache[symbol] = product_id
                            logger.debug(f"Found product_id {product_id} for symbol {symbol}")
                            return product_id
            
            logger.warning(f"Product ID not found for symbol {symbol}")
            return None
        except Exception as e:
            logger.error(f"Error fetching product ID: {e}")
            return None
    
    def _convert_interval(self, interval: str) -> str:
        """Convert interval format to Delta Exchange format."""
        # Delta Exchange interval mapping
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '2h': '2h',
            '4h': '4h',
            '6h': '6h',
            '12h': '12h',
            '1d': '1d',
            '1w': '1w'
        }
        return interval_map.get(interval, '5m')
    
    def fetch_live_candles(
        self, 
        symbol: str, 
        interval: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch live candlestick data from Delta Exchange."""
        try:
            delta_interval = self._convert_interval(interval)
            
            # Delta Exchange candles endpoint: /v2/history/candles
            # Uses symbol (not product_id) and requires start/end timestamps
            endpoint = "/v2/history/candles"
            
            # Calculate start and end times
            # Get the most recent candles
            end_time = int(time.time())
            interval_seconds = self._get_interval_seconds(interval)
            start_time = end_time - (limit * interval_seconds)
            
            params = {
                'symbol': symbol,
                'resolution': delta_interval,
                'start': start_time,
                'end': end_time
            }
            
            data = self._make_request('GET', endpoint, params)
            
            candles = []
            # Delta Exchange returns candles in a list format
            # Response structure: [{"time": timestamp, "open": float, "high": float, "low": float, "close": float, "volume": float}, ...]
            if isinstance(data, list):
                for candle in data:
                    # Delta Exchange returns time in seconds (Unix timestamp)
                    candle_time = int(candle.get('time', candle.get('timestamp', 0)))
                    candles.append({
                        'open_time': candle_time * 1000,  # Convert to milliseconds
                        'open': float(candle.get('open', 0)),
                        'high': float(candle.get('high', 0)),
                        'low': float(candle.get('low', 0)),
                        'close': float(candle.get('close', 0)),
                        'volume': float(candle.get('volume', 0)),
                        'close_time': (candle_time + interval_seconds) * 1000  # Convert to milliseconds
                    })
            elif isinstance(data, dict):
                # Handle wrapped response format
                result = data.get('result', data.get('candles', []))
                if isinstance(result, list):
                    for candle in result:
                        candle_time = int(candle.get('time', candle.get('timestamp', 0)))
                        candles.append({
                            'open_time': candle_time * 1000,
                            'open': float(candle.get('open', 0)),
                            'high': float(candle.get('high', 0)),
                            'low': float(candle.get('low', 0)),
                            'close': float(candle.get('close', 0)),
                            'volume': float(candle.get('volume', 0)),
                            'close_time': (candle_time + interval_seconds) * 1000
                        })
            
            logger.debug(f"Fetched {len(candles)} candles for {symbol}")
            return candles
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            return []
    
    def _get_interval_seconds(self, interval: str) -> int:
        """Convert interval string to seconds."""
        interval_map = {
            '1m': 60, '5m': 300, '15m': 900, '30m': 1800,
            '1h': 3600, '2h': 7200, '4h': 14400, '6h': 21600,
            '12h': 43200, '1d': 86400, '1w': 604800
        }
        return interval_map.get(interval, 300)
    
    def get_account_balance(self, asset: str = "USDT") -> float:
        """Get account balance for a specific asset."""
        try:
            # Delta Exchange wallet balances endpoint: /v2/wallet/balances
            data = self._make_request('GET', '/v2/wallet/balances', signed=True)
            
            # Debug: log the response structure
            logger.debug(f"Balance response type: {type(data)}")
            if isinstance(data, (list, dict)):
                logger.debug(f"Balance response sample: {str(data)[:200]}")
            
            # Delta Exchange balance format - try multiple possible structures
            balances_list = []
            
            if isinstance(data, list):
                balances_list = data
            elif isinstance(data, dict):
                # Try different possible keys
                balances_list = data.get('balances', data.get('result', []))
                if not balances_list and isinstance(data.get('result'), list):
                    balances_list = data['result']
            
            # Search for the asset
            for balance in balances_list:
                # Try different ways to match the asset
                asset_symbol = None
                asset_id = None
                
                # Check if asset is a dict with symbol
                if isinstance(balance.get('asset'), dict):
                    asset_symbol = balance['asset'].get('symbol')
                    asset_id = balance['asset'].get('id')
                elif isinstance(balance.get('asset_id'), (int, str)):
                    asset_id = str(balance.get('asset_id'))
                
                # Also check direct fields
                if not asset_symbol:
                    asset_symbol = balance.get('symbol')
                if not asset_id:
                    asset_id = balance.get('asset_id')
                
                # Match by symbol or asset_id
                if (asset_symbol and asset_symbol.upper() == asset.upper()) or \
                   (asset_id and str(asset_id) == asset):
                    # Try different balance field names
                    available = balance.get('available', balance.get('available_balance', balance.get('balance', 0)))
                    if available:
                        result = float(available)
                        logger.debug(f"Found {asset} balance: {result}")
                        return result
            
            # If not found, log all available assets for debugging
            logger.warning(f"Asset {asset} not found in account")
            if balances_list:
                logger.debug(f"Available assets in response: {[b.get('asset', {}).get('symbol', 'unknown') if isinstance(b.get('asset'), dict) else b.get('symbol', 'unknown') for b in balances_list[:5]]}")
            
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            logger.exception("Full error details:")
            return 0.0
    
    def place_market_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float
    ) -> Optional[Dict[str, Any]]:
        """Place a market order on Delta Exchange."""
        try:
            # Get product_id from symbol
            product_id = self._get_product_id(symbol)
            if product_id is None:
                logger.error(f"Could not find product_id for symbol {symbol}")
                return None
            
            # Delta Exchange order placement
            json_data = {
                'product_id': product_id,
                'side': side.lower(),
                'order_type': 'market_order',
                'size': str(quantity)  # Delta may require string format
            }
            
            data = self._make_request('POST', '/v2/orders', json_data=json_data, signed=True)
            logger.info(f"Order placed: {side} {quantity} {symbol} - Order ID: {data.get('id')}")
            return data
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def get_ticker_price(self, symbol: str) -> float:
        """Get current ticker price for a symbol."""
        try:
            # Delta Exchange ticker endpoint: /v2/tickers/{symbol}
            # Can use symbol directly, not product_id
            data = self._make_request('GET', f'/v2/tickers/{symbol}')
            
            # Delta Exchange ticker format
            if isinstance(data, dict):
                return float(data.get('close', data.get('last_price', data.get('mark_price', 0))))
            elif isinstance(data, list) and len(data) > 0:
                return float(data[0].get('close', data[0].get('last_price', data[0].get('mark_price', 0))))
            
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching ticker price: {e}")
            return 0.0

