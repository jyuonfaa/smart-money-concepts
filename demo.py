import yfinance as yf
import pandas as pd
from smartmoneyconcepts import smc

print("Downloading EURUSD data from Yahoo Finance...")
# Get 1-hour data for the last 60 days
ohlc = yf.download("EURUSD=X", interval="1h", period="60d", progress=False)

# In newer versions, yfinance returns multi-index columns. We flatten them here.
if isinstance(ohlc.columns, pd.MultiIndex):
    ohlc.columns = ohlc.columns.get_level_values(0)

# The SMC library explicitly requires lowercase column names
ohlc.columns = [c.lower() for c in ohlc.columns]

# Ensure we only keep the standard columns
ohlc = ohlc[['open', 'high', 'low', 'close', 'volume']]

print(f"\nDownloaded {len(ohlc)} rows of data.")
print("--- Raw OHLC Data (Last 3 rows) ---")
print(ohlc.tail(3))
print("-" * 50)

print("\nRunning SMC Detection Layer...")

# 1. Foundation: Swing Highs and Lows
# We need this first because other indicators depend on it.
print("\n--- 1. Swing Highs and Lows (Last 5 detected) ---")
swing_hl = smc.swing_highs_lows(ohlc, swing_length=15)
# Show only rows where a swing high (1) or swing low (-1) was found
print(swing_hl.dropna().tail(5))

# 2. Independent: Fair Value Gaps
print("\n--- 2. Fair Value Gaps (Last 5 detected) ---")
fvg = smc.fvg(ohlc, join_consecutive=False)
# Show only rows where an FVG was found
print(fvg.dropna(subset=['FVG']).tail(5))

# 3. Dependent: Break of Structure (BOS) / Change of Character (CHoCH)
print("\n--- 3. BOS & CHoCH (Last 5 detected) ---")
bos = smc.bos_choch(ohlc, swing_hl)
# Filter out empty rows
detected_bos = bos[(bos['BOS'] != 0) | (bos['CHOCH'] != 0)]
print(detected_bos.tail(5))

# 4. Dependent: Order Blocks
print("\n--- 4. Order Blocks (Last 5 detected) ---")
ob = smc.ob(ohlc, swing_hl)
print(ob.dropna(subset=['OB']).tail(5))

print("\nDone! This shows how the library highlights structural points in the data.")
