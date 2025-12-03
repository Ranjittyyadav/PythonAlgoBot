"""
Test script to verify Delta Exchange API authentication.
Run this to check if your API keys are valid.
"""
import sys
import logging
from exchanges.delta_api import DeltaAPI
import config

# Enable debug logging to see API responses
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

def test_api_connection():
    """Test Delta Exchange API connection and authentication."""
    print("=" * 70)
    print("Delta Exchange API Connection Test")
    print("=" * 70)
    print()
    
    # Check if API keys are set
    api_key = config.DELTA_API_KEY
    api_secret = config.DELTA_API_SECRET
    
    if not api_key or api_key == "" or not api_secret or api_secret == "":
        print("❌ ERROR: API keys not set!")
        print("   Please set DELTA_API_KEY and DELTA_API_SECRET in config.py")
        print("   or as environment variables.")
        return False
    
    print(f"API Key: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else '***'}")
    print(f"API Secret: {'*' * 20}...{api_secret[-5:] if len(api_secret) > 25 else '***'}")
    print()
    
    # Initialize API
    try:
        print("1. Initializing Delta Exchange API...")
        api = DeltaAPI(testnet=config.DELTA_TESTNET)
        print(f"   ✓ API initialized (testnet={config.DELTA_TESTNET})")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        return False
    
    # Test 1: Fetch products (public endpoint, no auth needed)
    try:
        print("\n2. Testing public endpoint (fetching products)...")
        products = api._make_request('GET', '/v2/products', params={'limit': 5})
        if products:
            print(f"   ✓ Successfully fetched {len(products) if isinstance(products, list) else 'some'} products")
        else:
            print("   ⚠ No products returned")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 2: Fetch wallet balances (requires authentication)
    try:
        print("\n3. Testing authenticated endpoint (wallet balances)...")
        balance = api.get_account_balance("USDT")
        if balance > 0:
            print(f"   ✓ Authentication successful!")
            print(f"   ✓ USDT Balance: {balance:.2f} USDT")
            return True
        elif balance == 0:
            print(f"   ✓ Authentication successful!")
            print(f"   ⚠ USDT Balance: 0.00 USDT (account may be empty)")
            return True
        else:
            print(f"   ✗ Failed to get balance")
            return False
    except Exception as e:
        print(f"   ✗ Authentication failed: {e}")
        print()
        print("   Possible issues:")
        print("   - API key or secret is incorrect")
        print("   - API key doesn't have 'Read' permission")
        print("   - API key has expired or been revoked")
        print("   - Using wrong API keys (demo vs production)")
        print()
        print("   Solutions:")
        print("   1. Log into Delta Exchange → API Management")
        print("   2. Verify your API key is active")
        print("   3. Check that it has 'Read' permission enabled")
        print("   4. Generate new API keys if needed")
        print("   5. Update config.py with the new keys")
        return False

if __name__ == "__main__":
    success = test_api_connection()
    print()
    print("=" * 70)
    if success:
        print("✓ All tests passed! Your API keys are valid.")
        print("  You can now run the trading bot.")
    else:
        print("✗ API authentication failed.")
        print("  Please fix the issues above before running the trading bot.")
    print("=" * 70)
    sys.exit(0 if success else 1)

