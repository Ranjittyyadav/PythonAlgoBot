# Troubleshooting Guide: Delta Exchange API Authentication

## Error: 401 Unauthorized - invalid_api_key

If you see this error:
```
Delta Exchange API request failed: 401 Client Error: Unauthorized
Response: {"error":{"code":"invalid_api_key"},"success":false}
```

### Possible Causes and Solutions:

#### 1. **Invalid API Key or Secret**
- **Check**: Verify your API key and secret are correct in `config.py` or environment variables
- **Solution**: 
  - Go to Delta Exchange → API Management
  - Generate new API keys if needed
  - Update `DELTA_API_KEY` and `DELTA_API_SECRET` in `config.py` or set as environment variables

#### 2. **API Key Permissions**
- **Check**: Ensure your API key has the required permissions:
  - Read wallet balances
  - Place orders (if trading)
  - Read market data
- **Solution**: 
  - Log into Delta Exchange
  - Go to API Management
  - Edit your API key permissions
  - Enable: "Read", "Trade" (if needed)

#### 3. **Demo/Testnet vs Production**
- **Check**: Verify you're using the correct API keys for your environment
- **Solution**: 
  - Demo/testnet accounts may have different API keys
  - Ensure `DELTA_TESTNET` matches your account type
  - Use demo API keys for testing

#### 4. **API Key Expired or Revoked**
- **Check**: API keys can expire or be revoked
- **Solution**: Generate new API keys from Delta Exchange

#### 5. **Signature Generation Issue**
- **Check**: The signature format might be incorrect
- **Solution**: The code uses: `METHOD + PATH + TIMESTAMP + BODY`
  - Verify the API secret is correct (not base64 encoded)
  - Check that timestamp is in seconds (Unix timestamp)

### Quick Fix Steps:

1. **Verify API Keys**:
   ```bash
   # Check your config
   cat config.py | grep DELTA_API
   ```

2. **Test with Environment Variables**:
   ```bash
   export DELTA_API_KEY="byPiH7EYatOX9r67cBuDnATAhoXjy2"
   export DELTA_API_SECRET="Gi91lgZg9mTZrAwB21VEpbMnAItiZNz6wCIXxBlzOzhPjEeXOw4lMruDalbt"
   python3 main.py
   ```

3. **Check API Key Status**:
   - Log into Delta Exchange
   - Go to API Management
   - Verify key is active and has correct permissions

4. **Generate New Keys** (if needed):
   - Delete old API key
   - Create new API key
   - Update config.py with new credentials

### Note:
The CV model is working correctly (detected hammer with 100% confidence), but trades cannot be placed without valid API authentication.

