# Quick Fix: Delta Exchange API Authentication Error

## The Problem
You're getting `401 Unauthorized - invalid_api_key` errors because the API keys are empty or incorrect.

## Immediate Solution

### Step 1: Check Your Current API Keys
```bash
python3 -c "import config; print('Key:', config.DELTA_API_KEY); print('Secret:', config.DELTA_API_SECRET[:20] + '...')"
```

If they're empty, continue to Step 2.

### Step 2: Set Your Demo Account API Keys

**Option A: Edit config.py (Easiest)**
1. Open `config.py`
2. Find these lines:
   ```python
   DELTA_API_KEY = os.getenv("DELTA_API_KEY", "3TzRAaf8DyKhWNsLKzK8S7Cmt0F3Ds")
   DELTA_API_SECRET = os.getenv("DELTA_API_SECRET", "54AxJa9oHnCLdufzjZO9bdFNjnp3e9kLMa3OKwojrmQcOlkNM7BMnGpi0zSL")
   ```
3. Replace with your actual demo account keys:
   ```python
   DELTA_API_KEY = os.getenv("DELTA_API_KEY", "YOUR_DEMO_API_KEY_HERE")
   DELTA_API_SECRET = os.getenv("DELTA_API_SECRET", "YOUR_DEMO_API_SECRET_HERE")
   ```

**Option B: Use Environment Variables**
```bash
export DELTA_API_KEY="YOUR_DEMO_API_KEY_HERE"
export DELTA_API_SECRET="YOUR_DEMO_API_SECRET_HERE"
```

### Step 3: Get Your Demo Account API Keys

1. Log into Delta Exchange demo account
2. Go to **API Management**
3. Create or view your API key
4. **Important**: Enable "Read" permission
5. Copy the API Key and API Secret

### Step 4: Test Your Keys
```bash
python3 test_delta_api.py
```

You should see:
```
✓ All tests passed! Your API keys are valid.
```

### Step 5: Run the Bot
```bash
python3 main.py
```

## Why This Happens

The error occurs because:
1. **Empty API keys**: Environment variables or config.py has empty strings
2. **Invalid keys**: API keys are incorrect or expired
3. **Missing permissions**: API key doesn't have "Read" permission
4. **Wrong account type**: Using production keys with demo account

## Still Having Issues?

1. **Verify keys are correct**: Double-check you copied the full key and secret
2. **Check permissions**: Ensure API key has "Read" permission in Delta Exchange
3. **Test connection**: Run `python3 test_delta_api.py` to verify
4. **Generate new keys**: If old keys don't work, create new ones in Delta Exchange

## Note About Demo Account Balance

Even with valid API keys, if your demo account has 0.00 USDT balance:
- ✅ Bot will detect patterns
- ✅ Bot will calculate signals
- ❌ Bot won't place trades (no funds)

This is **normal behavior** - the bot protects you from trading with zero balance.

