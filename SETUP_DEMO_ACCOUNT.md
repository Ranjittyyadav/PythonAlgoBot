# Setting Up Delta Exchange Demo Account API Keys

## Quick Setup Guide

### Step 1: Get Your Demo Account API Keys

1. **Log into Delta Exchange**
   - Go to https://www.delta.exchange
   - Log in with your demo/test account

2. **Navigate to API Management**
   - Click on your profile/account menu
   - Go to "API Management" or "API Keys"

3. **Create a New API Key** (if you don't have one)
   - Click "Create API Key" or "Generate New Key"
   - **Important**: Enable these permissions:
     - ✅ **Read** (required for fetching balances and market data)
     - ✅ **Trade** (required for placing orders - optional if you only want to monitor)
   - Save the API Key and API Secret immediately (you won't be able to see the secret again!)

### Step 2: Configure the Bot

You have **two options** to set your API keys:

#### Option A: Environment Variables (Recommended)
```bash
export DELTA_API_KEY="your_demo_api_key_here"
export DELTA_API_SECRET="your_demo_api_secret_here"
export DELTA_TESTNET="true"
```

Then run the bot:
```bash
python3 main.py
```

#### Option B: Edit config.py Directly
1. Open `config.py`
2. Find these lines:
   ```python
   DELTA_API_KEY = os.getenv("DELTA_API_KEY", "")
   DELTA_API_SECRET = os.getenv("DELTA_API_SECRET", "")
   ```
3. Replace the empty strings with your keys:
   ```python
   DELTA_API_KEY = os.getenv("DELTA_API_KEY", "your_demo_api_key_here")
   DELTA_API_SECRET = os.getenv("DELTA_API_SECRET", "your_demo_api_secret_here")
   ```

### Step 3: Test Your API Keys

Before running the bot, test your API keys:

```bash
python3 test_delta_api.py
```

You should see:
```
✓ All tests passed! Your API keys are valid.
```

If you see errors, check:
- API keys are correct (no typos)
- API key has "Read" permission enabled
- You're using demo account keys (not production)

### Step 4: Verify Demo Account Balance

For the bot to place trades, you need funds in your demo account:

1. **Check your balance**:
   ```bash
   python3 test_delta_api.py
   ```
   Look for: `✓ USDT Balance: X.XX USDT`

2. **If balance is 0.00 USDT**:
   - The bot will detect patterns but won't place trades
   - This is normal for demo accounts - you may need to add demo funds
   - Check Delta Exchange demo account settings for how to get demo funds

### Step 5: Run the Bot

Once API keys are set and tested:

```bash
python3 main.py
```

The bot will:
- ✅ Fetch market data
- ✅ Detect hammer patterns using CV model
- ✅ Calculate position sizes
- ✅ Place trades (if balance > 0)

## Troubleshooting

### Error: "invalid_api_key"
- **Solution**: Verify your API keys are correct
- Run `python3 test_delta_api.py` to test
- Make sure you copied the full key and secret (no extra spaces)

### Error: "Position size is zero"
- **Cause**: Account balance is 0.00 USDT
- **Solution**: Add funds to your demo account or check demo account settings

### Error: "401 Unauthorized"
- **Cause**: API key doesn't have required permissions
- **Solution**: Enable "Read" permission in API Management

## Security Notes

⚠️ **Never commit API keys to git!**
- Use environment variables instead of hardcoding in config.py
- Add `config.py` to `.gitignore` if you hardcode keys
- API keys in config.py are only for local development

## Next Steps

After setup:
1. ✅ Test API connection: `python3 test_delta_api.py`
2. ✅ Run the bot: `python3 main.py`
3. ✅ Monitor logs for pattern detection
4. ✅ Check Delta Exchange for executed trades

Good luck! 🚀

