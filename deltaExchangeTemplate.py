"""
Bullish Hammer Pattern Trading Bot for Delta Exchange
=====================================================
WARNING: This bot executes REAL trades automatically!
- Test on TESTNET first
- Use small position sizes
- Monitor continuously
- Understand the risks

Strategy:
- Detects bullish hammer candlestick patterns on 5-minute timeframe
- Enters long position when hammer is detected
- Sets 2% stop loss and 3% take profit
- Manages one position at a time

Author: Delta Exchange API Assistant
Date: December 2025
"""

import hashlib
import hmac
import requests
import time
import logging
from datetime import datetime
from typing import Optional, Dict, List
import json

# ============================================================================
# CONFIGURATION
# ============================================================================

# API Configuration
API_KEY = 'rC9EH0b8wn3t4qQ3bSV92UFigGBLvj'
API_SECRET = 'uxFMd4UIwOy5ifxyYgWnZhZPfnbzfhSq1ZsMebXtfFycowWTDp1RyfhDcvcc'
BASE_URL = 'https://cdn-ind.testnet.deltaex.org'  # Testnet

# Trading Parameters
SYMBOL = 'BTCUSD'
PRODUCT_ID = 27  # BTCUSD product ID
TIMEFRAME = '5m'
POSITION_SIZE = 10  # WARNING: This is 10 contracts = 0.01 BTC
STOP_LOSS_PERCENT = 2.0  # 2% stop loss
TAKE_PROFIT_PERCENT = 3.0  # 3% take profit

# Bot Settings
CHECK_INTERVAL = 60  # Check every 60 seconds
MAX_CANDLES = 100  # Number of candles to fetch

# Hammer Pattern Criteria
HAMMER_BODY_RATIO = 0.3  # Body should be <= 30% of total range
HAMMER_LOWER_SHADOW_RATIO = 2.0  # Lower shadow >= 2x body size
HAMMER_UPPER_SHADOW_RATIO = 0.5  # Upper shadow <= 50% of body size

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DELTA EXCHANGE API CLIENT
# ============================================================================

class DeltaExchangeAPI:
    """Delta Exchange API client with authentication."""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        
    def generate_signature(self, message: str) -> str:
        """Generate HMAC SHA256 signature."""
        message_bytes = bytes(message, 'utf-8')
        secret_bytes = bytes(self.api_secret, 'utf-8')
        hash_obj = hmac.new(secret_bytes, message_bytes, hashlib.sha256)
        return hash_obj.hexdigest()
    
    def _make_request(self, method: str, path: str, params: Dict = None, 
                     payload: str = '') -> Dict:
        """Make authenticated API request."""
        timestamp = str(int(time.time()))
        query_string = ''
        
        if params:
            query_string = '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        signature_data = method + timestamp + path + query_string + payload
        signature = self.generate_signature(signature_data)
        
        headers = {
            'api-key': self.api_key,
            'timestamp': timestamp,
            'signature': signature,
            'User-Agent': 'python-trading-bot',
            'Content-Type': 'application/json'
        }
        
        url = f'{self.base_url}{path}'
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, data=payload, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_candles(self, symbol: str, resolution: str, start: int, end: int) -> List[Dict]:
        """Fetch historical candlestick data."""
        path = '/v2/history/candles'
        params = {
            'symbol': symbol,
            'resolution': resolution,
            'start': start,
            'end': end
        }
        
        # Public endpoint - no authentication needed
        url = f'{self.base_url}{path}'
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            return data.get('result', [])
        return []
    
    def get_wallet_balance(self, asset_symbol: str = 'USD') -> float:
        """Get wallet balance for specific asset."""
        path = '/v2/wallet/balances'
        response = self._make_request('GET', path)
        
        if response.get('success'):
            for wallet in response.get('result', []):
                if wallet.get('asset_symbol') == asset_symbol:
                    return float(wallet.get('available_balance', 0))
        return 0.0
    
    def get_position(self, product_id: int) -> Optional[Dict]:
        """Get current position for product."""
        path = '/v2/positions'
        params = {'product_id': product_id}
        response = self._make_request('GET', path, params=params)
        
        if response.get('success'):
            result = response.get('result', {})
            size = result.get('size', 0)
            if size != 0:
                return result
        return None
    
    def place_market_order(self, product_id: int, side: str, size: int) -> Dict:
        """Place market order."""
        path = '/v2/orders'
        
        order_data = {
            'product_id': product_id,
            'size': size,
            'side': side,
            'order_type': 'market_order'
        }
        
        payload = json.dumps(order_data)
        response = self._make_request('POST', path, payload=payload)
        
        return response.get('result', {})
    
    def place_limit_order(self, product_id: int, side: str, size: int, 
                         limit_price: str) -> Dict:
        """Place limit order."""
        path = '/v2/orders'
        
        order_data = {
            'product_id': product_id,
            'size': size,
            'side': side,
            'order_type': 'limit_order',
            'limit_price': limit_price
        }
        
        payload = json.dumps(order_data)
        response = self._make_request('POST', path, payload=payload)
        
        return response.get('result', {})
    
    def place_stop_loss_order(self, product_id: int, side: str, size: int, 
                             stop_price: str) -> Dict:
        """Place stop loss order."""
        path = '/v2/orders'
        
        order_data = {
            'product_id': product_id,
            'size': size,
            'side': side,
            'order_type': 'market_order',
            'stop_order_type': 'stop_loss_order',
            'stop_price': stop_price
        }
        
        payload = json.dumps(order_data)
        response = self._make_request('POST', path, payload=payload)
        
        return response.get('result', {})
    
    def place_take_profit_order(self, product_id: int, side: str, size: int, 
                               stop_price: str) -> Dict:
        """Place take profit order."""
        path = '/v2/orders'
        
        order_data = {
            'product_id': product_id,
            'size': size,
            'side': side,
            'order_type': 'market_order',
            'stop_order_type': 'take_profit_order',
            'stop_price': stop_price
        }
        
        payload = json.dumps(order_data)
        response = self._make_request('POST', path, payload=payload)
        
        return response.get('result', {})
    
    def get_ticker_price(self, symbol: str) -> float:
        """Get current ticker price."""
        path = f'/v2/tickers/{symbol}'
        
        # Public endpoint
        url = f'{self.base_url}{path}'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            result = data.get('result', {})
            return float(result.get('close', 0))
        return 0.0

# ============================================================================
# PATTERN DETECTION
# ============================================================================

class HammerDetector:
    """Bullish hammer candlestick pattern detector."""
    
    @staticmethod
    def is_bullish_hammer(candle: Dict) -> bool:
        """
        Detect bullish hammer pattern.
        
        Criteria:
        - Small body at the top of the range
        - Long lower shadow (at least 2x body size)
        - Little to no upper shadow
        - Appears after downtrend (simplified: close > open)
        """
        open_price = float(candle['open'])
        high_price = float(candle['high'])
        low_price = float(candle['low'])
        close_price = float(candle['close'])
        
        # Calculate components
        body_size = abs(close_price - open_price)
        total_range = high_price - low_price
        lower_shadow = min(open_price, close_price) - low_price
        upper_shadow = high_price - max(open_price, close_price)
        
        # Avoid division by zero
        if total_range == 0 or body_size == 0:
            return False
        
        # Check hammer criteria
        body_ratio = body_size / total_range
        lower_shadow_ratio = lower_shadow / body_size if body_size > 0 else 0
        upper_shadow_ratio = upper_shadow / body_size if body_size > 0 else 0
        
        is_hammer = (
            body_ratio <= HAMMER_BODY_RATIO and
            lower_shadow_ratio >= HAMMER_LOWER_SHADOW_RATIO and
            upper_shadow_ratio <= HAMMER_UPPER_SHADOW_RATIO and
            close_price > open_price  # Bullish candle
        )
        
        if is_hammer:
            logger.info(f"Bullish Hammer Detected!")
            logger.info(f"  Open: {open_price}, High: {high_price}, Low: {low_price}, Close: {close_price}")
            logger.info(f"  Body Ratio: {body_ratio:.2%}, Lower Shadow Ratio: {lower_shadow_ratio:.2f}x")
        
        return is_hammer

# ============================================================================
# TRADING BOT
# ============================================================================

class TradingBot:
    """Automated trading bot for bullish hammer pattern."""
    
    def __init__(self, api: DeltaExchangeAPI):
        self.api = api
        self.in_position = False
        self.entry_price = 0.0
        self.stop_loss_price = 0.0
        self.take_profit_price = 0.0
        self.position_size = 0
        
    def check_existing_position(self) -> bool:
        """Check if there's an existing position."""
        try:
            position = self.api.get_position(PRODUCT_ID)
            if position:
                size = int(position.get('size', 0))
                if size != 0:
                    self.in_position = True
                    self.position_size = abs(size)
                    self.entry_price = float(position.get('entry_price', 0))
                    logger.info(f"Existing position found: {size} contracts at ${self.entry_price}")
                    return True
            self.in_position = False
            return False
        except Exception as e:
            logger.error(f"Error checking position: {e}")
            return False
    
    def get_latest_candles(self, count: int = 10) -> List[Dict]:
        """Fetch latest candlestick data."""
        try:
            end_time = int(time.time())
            start_time = end_time - (count * 5 * 60)  # 5 minutes per candle
            
            candles = self.api.get_candles(SYMBOL, TIMEFRAME, start_time, end_time)
            return candles[-count:] if candles else []
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            return []
    
    def enter_long_position(self, entry_price: float):
        """Enter long position with stop loss and take profit."""
        try:
            logger.info("=" * 70)
            logger.info("ENTERING LONG POSITION")
            logger.info("=" * 70)
            
            # Place market buy order
            logger.info(f"Placing BUY order: {POSITION_SIZE} contracts at market price")
            order = self.api.place_market_order(PRODUCT_ID, 'buy', POSITION_SIZE)
            
            if order:
                logger.info(f"✓ BUY order placed successfully!")
                logger.info(f"  Order ID: {order.get('id')}")
                logger.info(f"  Size: {order.get('size')} contracts")
                
                self.in_position = True
                self.entry_price = entry_price
                self.position_size = POSITION_SIZE
                
                # Calculate stop loss and take profit prices
                self.stop_loss_price = entry_price * (1 - STOP_LOSS_PERCENT / 100)
                self.take_profit_price = entry_price * (1 + TAKE_PROFIT_PERCENT / 100)
                
                logger.info(f"  Entry Price: ${entry_price:.2f}")
                logger.info(f"  Stop Loss: ${self.stop_loss_price:.2f} (-{STOP_LOSS_PERCENT}%)")
                logger.info(f"  Take Profit: ${self.take_profit_price:.2f} (+{TAKE_PROFIT_PERCENT}%)")
                
                # Wait a moment for order to fill
                time.sleep(2)
                
                # Place stop loss order
                logger.info(f"Placing STOP LOSS order at ${self.stop_loss_price:.2f}")
                sl_order = self.api.place_stop_loss_order(
                    PRODUCT_ID, 'sell', POSITION_SIZE, str(self.stop_loss_price)
                )
                if sl_order:
                    logger.info(f"✓ Stop Loss order placed: {sl_order.get('id')}")
                
                # Place take profit order
                logger.info(f"Placing TAKE PROFIT order at ${self.take_profit_price:.2f}")
                tp_order = self.api.place_take_profit_order(
                    PRODUCT_ID, 'sell', POSITION_SIZE, str(self.take_profit_price)
                )
                if tp_order:
                    logger.info(f"✓ Take Profit order placed: {tp_order.get('id')}")
                
                logger.info("=" * 70)
                return True
            else:
                logger.error("Failed to place BUY order")
                return False
                
        except Exception as e:
            logger.error(f"Error entering position: {e}")
            return False
    
    def monitor_position(self):
        """Monitor current position and check exit conditions."""
        try:
            current_price = self.api.get_ticker_price(SYMBOL)
            
            if current_price <= 0:
                return
            
            # Calculate current P&L
            pnl_percent = ((current_price - self.entry_price) / self.entry_price) * 100
            pnl_usd = (current_price - self.entry_price) * POSITION_SIZE * 0.001  # Contract value
            
            logger.info(f"Position Monitor - Price: ${current_price:.2f} | "
                       f"P&L: {pnl_percent:+.2f}% (${pnl_usd:+.2f})")
            
            # Check if position still exists
            position = self.api.get_position(PRODUCT_ID)
            if not position or position.get('size', 0) == 0:
                logger.info("Position closed (Stop Loss or Take Profit hit)")
                self.in_position = False
                self.entry_price = 0.0
                
        except Exception as e:
            logger.error(f"Error monitoring position: {e}")
    
    def run(self):
        """Main bot loop."""
        logger.info("=" * 70)
        logger.info("BULLISH HAMMER TRADING BOT STARTED")
        logger.info("=" * 70)
        logger.info(f"Symbol: {SYMBOL}")
        logger.info(f"Timeframe: {TIMEFRAME}")
        logger.info(f"Position Size: {POSITION_SIZE} contracts")
        logger.info(f"Stop Loss: {STOP_LOSS_PERCENT}%")
        logger.info(f"Take Profit: {TAKE_PROFIT_PERCENT}%")
        logger.info(f"Environment: {'TESTNET' if 'testnet' in BASE_URL else 'PRODUCTION'}")
        logger.info("=" * 70)
        
        # Check API connection
        try:
            balance = self.api.get_wallet_balance('USD')
            logger.info(f"✓ API Connected - USD Balance: ${balance:.2f}")
        except Exception as e:
            logger.error(f"✗ API Connection Failed: {e}")
            return
        
        # Check for existing position
        self.check_existing_position()
        
        detector = HammerDetector()
        
        while True:
            try:
                logger.info(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking market...")
                
                # Check existing position first
                if self.in_position:
                    self.monitor_position()
                    time.sleep(CHECK_INTERVAL)
                    continue
                
                # Fetch latest candles
                candles = self.get_latest_candles(count=5)
                
                if len(candles) < 2:
                    logger.warning("Not enough candle data")
                    time.sleep(CHECK_INTERVAL)
                    continue
                
                # Check the last completed candle (not the current forming one)
                last_candle = candles[-2]
                
                # Detect bullish hammer
                if detector.is_bullish_hammer(last_candle):
                    current_price = self.api.get_ticker_price(SYMBOL)
                    
                    if current_price > 0:
                        logger.info(f"Signal detected! Current price: ${current_price:.2f}")
                        self.enter_long_position(current_price)
                    else:
                        logger.error("Could not fetch current price")
                else:
                    logger.info("No hammer pattern detected")
                
                # Wait before next check
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("\n\nBot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(CHECK_INTERVAL)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point."""
    
    # Validate API keys
    if API_KEY == 'your_testnet_api_key_here' or API_SECRET == 'your_testnet_api_secret_here':
        print("=" * 70)
        print("ERROR: Please configure your API keys!")
        print("=" * 70)
        print("1. Go to https://testnet.delta.exchange")
        print("2. Create API keys with trading permissions")
        print("3. Update API_KEY and API_SECRET in this script")
        print("=" * 70)
        return
    
    # Warning message
    print("\n" + "=" * 70)
    print("⚠️  WARNING: AUTOMATED TRADING BOT")
    print("=" * 70)
    print("This bot will execute REAL trades automatically!")
    print(f"Position Size: {POSITION_SIZE} contracts (0.001 BTC each)")
    print(f"Stop Loss: {STOP_LOSS_PERCENT}%")
    print(f"Take Profit: {TAKE_PROFIT_PERCENT}%")
    print(f"Environment: {'TESTNET' if 'testnet' in BASE_URL else 'PRODUCTION'}")
    print("=" * 70)
    
    response = input("\nType 'START' to begin trading: ")
    if response.upper() != 'START':
        print("Bot cancelled.")
        return
    
    # Initialize API and bot
    api = DeltaExchangeAPI(API_KEY, API_SECRET, BASE_URL)
    bot = TradingBot(api)
    
    # Run bot
    bot.run()

if __name__ == "__main__":
    main()
