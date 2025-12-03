"""
Debug script to test Delta Exchange API authentication in detail.
This will help identify authentication issues.
"""
import logging
import json
import requests
import time
import hmac
import hashlib
from exchanges.delta_api import DeltaAPI
import config

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_auth_manually():
    """Test authentication manually to see exact request/response."""
    print("=" * 70)
    print("Delta Exchange API Authentication Debug")
    print("=" * 70)
    print()
    
    api_key = config.DELTA_API_KEY
    api_secret = config.DELTA_API_SECRET
    testnet = config.DELTA_TESTNET
    
    base_url = "https://testnet-api.delta.exchange" if testnet else "https://api.delta.exchange"
    
    print(f"API Key: {api_key[:10]}...{api_key[-5:]}")
    print(f"Testnet: {testnet}")
    print(f"Base URL: {base_url}")
    print()
    
    # Test 1: Public endpoint (no auth)
    print("1. Testing public endpoint...")
    try:
        response = requests.get(f"{base_url}/v2/products", params={'limit': 1}, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ Public endpoint works")
        else:
            print(f"   ✗ Public endpoint failed: {response.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    print()
    
    # Test 2: Authenticated endpoint with manual signature
    print("2. Testing authenticated endpoint with manual signature...")
    endpoint = "/v2/wallet/balances"
    method = "GET"
    timestamp = str(int(time.time()))
    body = ""
    
    # Generate signature: METHOD + PATH + TIMESTAMP + BODY
    message = f"{method}{endpoint}{timestamp}{body}"
    signature = hmac.new(
        api_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        'api-key': api_key,
        'timestamp': timestamp,
        'signature': signature,
        'Content-Type': 'application/json'
    }
    
    print(f"   Method: {method}")
    print(f"   Path: {endpoint}")
    print(f"   Timestamp: {timestamp}")
    print(f"   Message: {message}")
    print(f"   Signature: {signature[:20]}...{signature[-10:]}")
    print()
    
    try:
        url = f"{base_url}{endpoint}"
        print(f"   Request URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        print(f"   Response Body: {response.text[:500]}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print("   ✓ Authentication successful!")
            print(f"   Response data type: {type(data)}")
            if isinstance(data, dict):
                print(f"   Response keys: {list(data.keys())}")
                if 'result' in data:
                    result = data['result']
                    print(f"   Result type: {type(result)}")
                    if isinstance(result, list) and len(result) > 0:
                        print(f"   First balance entry: {json.dumps(result[0], indent=2)}")
            elif isinstance(data, list) and len(data) > 0:
                print(f"   First balance entry: {json.dumps(data[0], indent=2)}")
        elif response.status_code == 401:
            print("   ✗ Authentication failed (401 Unauthorized)")
            try:
                error_data = response.json()
                print(f"   Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
        else:
            print(f"   ✗ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 70)
    print("Debug Complete")
    print("=" * 70)

if __name__ == "__main__":
    test_auth_manually()

