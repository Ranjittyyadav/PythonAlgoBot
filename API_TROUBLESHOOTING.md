# Delta Exchange API Troubleshooting Guide

## Current Status
- ✅ API connection to testnet endpoint works (`https://testnet-api.delta.exchange`)
- ✅ Public endpoints work (fetching products)
- ❌ Authenticated endpoints fail with "invalid_api_key" error

## Authentication Error Details
- **Error Code**: `invalid_api_key`
- **Status**: 401 Unauthorized
- **Endpoint**: `/v2/wallet/balances`
- **Signature Format**: `METHOD + PATH + TIMESTAMP + BODY` (appears correct)

## Possible Causes & Solutions

### 1. IP Whitelisting (Most Common)
If your API key has IP whitelisting enabled, requests from your current IP will be blocked.

**Solution:**
1. Log into Delta Exchange → API Management
2. Find your API key
3. Check if IP whitelisting is enabled
4. Either:
   - Add your current IP address to the whitelist, OR
   - Disable IP whitelisting (for testing)

**To find your IP:**
```bash
curl ifconfig.me
```

### 2. API Keys Not for Testnet
Your API keys might be for production, not testnet.

**Solution:**
1. Log into your **demo/testnet account** (not production)
2. Go to API Management
3. Generate new API keys specifically for testnet
4. Update `config.py` with the new keys

### 3. API Key Permissions
Ensure your API key has both "Read" and "Trade" permissions enabled.

**Solution:**
1. Delta Exchange → API Management
2. Check your API key permissions
3. Enable both "Read" and "Trade" if not already enabled

### 4. API Key Expired or Revoked
The API key might have been revoked or expired.

**Solution:**
1. Generate a new API key
2. Update `config.py` with the new key and secret
3. Make sure to copy both the key AND secret correctly

### 5. Wrong API Secret
Double-check that the API secret in `config.py` matches exactly what's shown in Delta Exchange.

**Solution:**
1. In Delta Exchange → API Management
2. View your API key details
3. Copy the secret again (make sure there are no extra spaces)
4. Update `config.py`:
   ```python
   DELTA_API_KEY = "your_key_here"
   DELTA_API_SECRET = "your_secret_here"
   ```

## Testing Steps

### Step 1: Test Basic Connection
```bash
python3 test_delta_api.py
```

### Step 2: Test with Debug Output
```bash
python3 test_auth_debug.py
```

### Step 3: Test Trade Execution
```bash
python3 test_api_trade.py
```

## Current Configuration
- **Testnet URL**: `https://testnet-api.delta.exchange` ✅
- **API Key**: Configured in `config.py`
- **Testnet Mode**: `True` (from `DELTA_TESTNET`)

## Next Steps
1. Check IP whitelisting in Delta Exchange API Management
2. Verify you're using testnet API keys (not production)
3. Regenerate API keys if needed
4. Run `python3 test_auth_debug.py` again after making changes

## Contact Support
If none of the above solutions work, contact Delta Exchange support with:
- Your API key (first 10 and last 5 characters)
- The error message you're seeing
- Confirmation that you're using testnet API keys

