# Step-by-Step Guide: Training Your CV Model with Screenshots

## Overview
This guide will walk you through collecting candlestick chart screenshots and training your computer vision model to detect bullish hammer patterns.

---

## Part 1: Collecting Screenshots

### Step 1: Choose Your Trading Platform
You can take screenshots from any trading platform that shows candlestick charts:
- Delta Exchange website
- TradingView
- Binance
- Any other charting platform

### Step 2: Set Up Your Chart View
1. **Open a candlestick chart** for any cryptocurrency (BTC, ETH, etc.)
2. **Set the timeframe** to match your bot's interval (e.g., 5m, 15m, 1h)
3. **Display approximately 40 candles** on screen (zoom in/out to show ~40 candles)
4. **Use a clean chart style**:
   - Show only candlesticks (hide indicators if possible)
   - Use a simple color scheme (green/red candles)
   - Remove volume bars if visible

### Step 3: Identify Hammer Patterns

**What is a Bullish Hammer?**
- Small body (open/close) near the top of the candle
- Long lower wick (at least 2x the body size)
- Little to no upper wick
- Usually appears after a downtrend

**Visual Example:**
```
    |
    |  ← Small upper wick
    ███  ← Small body at top
    |
    |  ← Long lower wick (2-3x body)
    |
```

### Step 4: Take Screenshots

#### For HAMMER Folder (Positive Examples):
1. **Find charts with clear bullish hammer patterns**
2. **Position the hammer candle** near the right side (most recent)
3. **Take a screenshot** showing ~40 candles with the hammer visible
4. **Save the screenshot** as a PNG file
5. **Name it descriptively**: `hammer_btc_20241201_001.png`

**Tips:**
- Collect at least 50-100 hammer pattern screenshots
- Vary the market conditions (different coins, timeframes)
- Include hammers at different positions in the chart
- Make sure the hammer is clearly visible

#### For NONE Folder (Negative Examples):
1. **Find charts WITHOUT hammer patterns**
2. **Take screenshots** of normal candlestick patterns:
   - Regular up/down candles
   - Doji patterns
   - Engulfing patterns
   - Any pattern that is NOT a hammer
3. **Save as PNG files**
4. **Name them**: `none_btc_20241201_001.png`

**Tips:**
- Collect 2-3x more "none" images than "hammer" images (for balanced training)
- Include various market conditions
- Make sure NO hammer patterns are visible in these images

### Step 5: Organize Your Screenshots

1. **Open your file explorer** and navigate to:
   ```
   /Users/ranjitkumar/Desktop/PythonTradingBot/data/train/
   ```

2. **Copy your hammer screenshots** to:
   ```
   data/train/hammer/
   ```

3. **Copy your non-hammer screenshots** to:
   ```
   data/train/none/
   ```

**Final Structure Should Look Like:**
```
data/
├── train/
│   ├── hammer/
│   │   ├── hammer_btc_001.png
│   │   ├── hammer_btc_002.png
│   │   ├── hammer_eth_001.png
│   │   └── ... (50-100+ images)
│   └── none/
│       ├── none_btc_001.png
│       ├── none_btc_002.png
│       ├── none_eth_001.png
│       └── ... (100-300+ images)
└── val/  (optional, for validation)
    ├── hammer/
    │   └── ... (10-20 images)
    └── none/
        └── ... (20-40 images)
```

---

## Part 2: Preparing Screenshots (Optional but Recommended)

### Step 6: Resize/Crop Screenshots (If Needed)

Your screenshots should be similar to the demo images:
- **Size**: Approximately 1000x600 pixels
- **Format**: PNG
- **Content**: ~40 candles visible

**If your screenshots are different sizes:**
1. Use an image editor (Preview on Mac, Paint on Windows, GIMP, etc.)
2. Crop to show only the candlestick chart area
3. Resize to approximately 1000x600 pixels
4. Save as PNG format

**Quick Check:**
Compare your screenshots with the demo images:
- `data/train/hammer/demo_hammer.png`
- `data/train/none/demo_none.png`

Your images should look similar in size and format.

---

## Part 3: Training the Model

### Step 7: Verify Your Data

Before training, check that you have images in both folders:

```bash
# Count images in hammer folder
ls -1 data/train/hammer/*.png | wc -l

# Count images in none folder
ls -1 data/train/none/*.png | wc -l
```

**Recommended Minimum:**
- Hammer: 50+ images
- None: 100+ images (2x hammer for balanced training)

### Step 8: Train the Model

Run the training script:

```bash
python3 train_cv_model.py --data_dir data/train --epochs 10 --batch_size 32
```

**Parameters Explained:**
- `--data_dir data/train`: Path to your training data
- `--epochs 10`: Number of training iterations (increase for better accuracy)
- `--batch_size 32`: Images processed at once (reduce if you get memory errors)
- `--val_dir data/val`: Optional validation folder (if you have one)

**Training Process:**
1. The script will load all images
2. Train the model for the specified epochs
3. Save the trained model to `models/cv_hammer.pth`
4. Show training progress and accuracy

**Example Output:**
```
Loaded 75 samples from data/train
  - No hammer (class 0): 150
  - Hammer (class 1): 75

Epoch 1/10
Train Loss: 0.5234, Train Acc: 72.50%

Epoch 2/10
Train Loss: 0.4123, Train Acc: 81.25%
...
```

### Step 9: Monitor Training

Watch for:
- **Training Accuracy**: Should increase over epochs (aim for 80%+)
- **Training Loss**: Should decrease over epochs
- **Model Saved**: Look for "Saved best model" messages

**If Training Fails:**
- Check that images are PNG format
- Verify folder structure is correct
- Ensure you have enough images (minimum 20-30 per class)
- Try reducing batch_size if you get memory errors

---

## Part 4: Using Your Trained Model

### Step 10: Test the Trained Model

Once training completes, the model is saved to:
```
models/cv_hammer.pth
```

### Step 11: Run the Bot with CV Engine

The bot will automatically use your trained model:

```bash
python3 main.py
```

Or explicitly specify CV engine:

```bash
SIGNAL_ENGINE=cv python3 main.py
```

The bot will:
1. Fetch live candles from Delta Exchange
2. Render charts to images
3. Use your trained CV model to detect hammer patterns
4. Place trades when hammer patterns are detected with high confidence

---

## Quick Reference Checklist

- [ ] Collect 50-100+ hammer pattern screenshots
- [ ] Collect 100-300+ non-hammer screenshots
- [ ] Save all screenshots as PNG files
- [ ] Place hammer images in `data/train/hammer/`
- [ ] Place non-hammer images in `data/train/none/`
- [ ] Verify image counts in both folders
- [ ] Run training script: `python3 train_cv_model.py --data_dir data/train --epochs 10`
- [ ] Wait for training to complete
- [ ] Check that `models/cv_hammer.pth` was created
- [ ] Run bot with CV engine: `python3 main.py`

---

## Tips for Better Results

1. **More Data = Better Model**: Collect as many screenshots as possible
2. **Quality Over Quantity**: Make sure hammer patterns are clearly visible
3. **Variety**: Include different coins, timeframes, and market conditions
4. **Balance**: Keep a 2:1 ratio (none:hammer) for balanced training
5. **Validation Set**: Create a `data/val/` folder with 10-20% of your images for validation
6. **Iterate**: Train multiple times with different parameters to improve accuracy

---

## Troubleshooting

**Problem**: "No training data found"
- **Solution**: Check that images are in `data/train/hammer/` and `data/train/none/`

**Problem**: "CUDA out of memory"
- **Solution**: Reduce batch_size: `--batch_size 16` or `--batch_size 8`

**Problem**: Low training accuracy (< 60%)
- **Solution**: 
  - Collect more training images
  - Ensure hammer patterns are clearly visible
  - Check that images are properly labeled

**Problem**: Model not detecting hammers
- **Solution**:
  - Retrain with more diverse data
  - Adjust CV_THRESHOLD in config.py (lower = more sensitive)
  - Verify model file exists: `ls models/cv_hammer.pth`

---

## Next Steps

After training:
1. Test the model on new charts
2. Adjust the confidence threshold in `config.py` (CV_THRESHOLD)
3. Monitor bot performance
4. Collect more data and retrain if needed

Good luck with your training! 🚀

