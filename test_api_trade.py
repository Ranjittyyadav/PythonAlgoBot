"""
Simple test program to verify API connection and execute one buy/sell trade.
This script will:
1. Test API connection
2. Check account balance
3. Get current price
4. Place a small BUY order
5. Place a SELL order to close the position
"""
import logging
import time
import sys
from exchanges.delta_api import DeltaAPI
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_api_trade():
    """Test API and execute one buy/sell trade."""
    print("=" * 70)
    print("API Trade Test - Buy and Sell One Trade")
    print("=" * 70)
    print()
    
    # Check API keys
    api_key = config.DELTA_API_KEY
    api_secret = config.DELTA_API_SECRET
    
    if not api_key or not api_secret:
        print("❌ ERROR: API keys not set!")
        print("   Please set DELTA_API_KEY and DELTA_API_SECRET in config.py")
        return False
    
    print(f"✓ API Key configured: {api_key[:10]}...{api_key[-5:]}")
    print(f"✓ Testnet mode: {config.DELTA_TESTNET}")
    print()
    
    # Initialize API
    try:
        logger.info("Initializing Delta Exchange API...")
        api = DeltaAPI(testnet=config.DELTA_TESTNET)
        print("✓ API initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize API: {e}")
        return False
    
    # Test 1: Get account balance
    print("\n" + "-" * 70)
    print("Step 1: Checking Account Balance")
    print("-" * 70)
    try:
        balance = api.get_account_balance("USDT")
        if balance is None or balance < 0:
            print("❌ Failed to get balance")
            return False
        
        print(f"✓ USDT Balance: {balance:.2f} USDT")
        
        if balance < 1.0:
            print("⚠️  WARNING: Balance is very low. You need at least 1 USDT to test trading.")
            print("   The test will continue but may fail if balance is insufficient.")
    except Exception as e:
        print(f"❌ Error getting balance: {e}")
        return False
    
    # Test 2: Get current price
    print("\n" + "-" * 70)
    print("Step 2: Getting Current Price")
    print("-" * 70)
    symbol = config.SYMBOL
    try:
        current_price = api.get_ticker_price(symbol)
        if current_price <= 0:
            print(f"❌ Failed to get price for {symbol}")
            return False
        
        print(f"✓ Current {symbol} price: ${current_price:.2f}")
    except Exception as e:
        print(f"❌ Error getting price: {e}")
        return False
    
    # Test 3: Calculate small position size
    print("\n" + "-" * 70)
    print("Step 3: Calculating Position Size")
    print("-" * 70)
    
    # Use a very small position for testing (0.001 of base currency or minimum)
    # For BTC, this would be 0.001 BTC
    test_quantity = 0.001  # Very small quantity for testing
    
    # Calculate cost
    estimated_cost = test_quantity * current_price
    print(f"✓ Test quantity: {test_quantity} {symbol.replace('USDT', '')}")
    print(f"✓ Estimated cost: ${estimated_cost:.2f} USDT")
    
    if estimated_cost > balance:
        print(f"⚠️  WARNING: Estimated cost (${estimated_cost:.2f}) exceeds balance (${balance:.2f})")
        print("   Trying with smaller quantity...")
        # Try with even smaller quantity
        test_quantity = (balance * 0.5) / current_price  # Use 50% of balance
        estimated_cost = test_quantity * current_price
        print(f"   Adjusted quantity: {test_quantity:.6f} {symbol.replace('USDT', '')}")
        print(f"   Adjusted cost: ${estimated_cost:.2f} USDT")
    
    if estimated_cost > balance:
        print(f"❌ Insufficient balance. Need ${estimated_cost:.2f}, have ${balance:.2f}")
        return False
    
    # Test 4: Place BUY order
    print("\n" + "-" * 70)
    print("Step 4: Placing BUY Order")
    print("-" * 70)
    buy_order = None
    try:
        print(f"Placing BUY order: {test_quantity:.6f} {symbol} at market price...")
        buy_order = api.place_market_order(symbol, "BUY", test_quantity)
        
        if buy_order:
            print("✓ BUY order placed successfully!")
            print(f"  Order ID: {buy_order.get('id', 'N/A')}")
            print(f"  Status: {buy_order.get('status', 'N/A')}")
            print(f"  Side: {buy_order.get('side', 'N/A')}")
            print(f"  Size: {buy_order.get('size', 'N/A')}")
        else:
            print("❌ Failed to place BUY order")
            return False
    except Exception as e:
        print(f"❌ Error placing BUY order: {e}")
        logger.exception("Full error details:")
        return False
    
    # Wait a moment for order to fill
    print("\n⏳ Waiting 3 seconds for order to fill...")
    time.sleep(3)
    
    # Test 5: Place SELL order
    print("\n" + "-" * 70)
    print("Step 5: Placing SELL Order")
    print("-" * 70)
    sell_order = None
    try:
        print(f"Placing SELL order: {test_quantity:.6f} {symbol} at market price...")
        sell_order = api.place_market_order(symbol, "SELL", test_quantity)
        
        if sell_order:
            print("✓ SELL order placed successfully!")
            print(f"  Order ID: {sell_order.get('id', 'N/A')}")
            print(f"  Status: {sell_order.get('status', 'N/A')}")
            print(f"  Side: {sell_order.get('side', 'N/A')}")
            print(f"  Size: {sell_order.get('size', 'N/A')}")
        else:
            print("❌ Failed to place SELL order")
            print("⚠️  WARNING: You may have an open position. Please check your account.")
            return False
    except Exception as e:
        print(f"❌ Error placing SELL order: {e}")
        logger.exception("Full error details:")
        print("⚠️  WARNING: You may have an open position. Please check your account.")
        return False
    
    # Final check: Get updated balance
    print("\n" + "-" * 70)
    print("Step 6: Checking Final Balance")
    print("-" * 70)
    try:
        final_balance = api.get_account_balance("USDT")
        print(f"✓ Final USDT Balance: {final_balance:.2f} USDT")
        
        if final_balance != balance:
            difference = final_balance - balance
            print(f"  Balance change: ${difference:+.2f} USDT")
    except Exception as e:
        print(f"⚠️  Could not get final balance: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print("✓ API connection: OK")
    print("✓ Account balance: Retrieved")
    print("✓ Current price: Retrieved")
    if buy_order:
        print("✓ BUY order: Placed successfully")
    if sell_order:
        print("✓ SELL order: Placed successfully")
    print("\n✅ All tests completed!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        success = test_api_trade()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        logger.exception("Full error details:")
        sys.exit(1)

