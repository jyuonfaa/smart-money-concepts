import os

path = r'd:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py'

# Read the file
with open(path, 'r') as f:
    lines = f.readlines()

# We need to find the methods we added and replace them with filtered versions.
# I will just rewrite the entire smc class methods at the end.

# First, remove the old ones
start_idx = -1
for i, line in enumerate(lines):
    if '@classmethod' in line and 'def swing_highs_lows_v4(cls, ohlc):' in lines[i+1]:
        start_idx = i
        break

if start_idx != -1:
    lines = lines[:start_idx]

# New, Filtered methods
new_methods = """
    @classmethod
    def swing_highs_lows_v4(cls, ohlc, filter_atr=True):
        \"\"\"
        ICT Video 4: Filtered Institutional Swing Engine.
        - 3-Candle Base (Wicks).
        - 4th Candle Close confirmation.
        - ATR-based Significance Filter to remove micro-noise.
        - Sunday Filter.
        \"\"\"
        import pandas as pd
        import numpy as np
        df = ohlc.copy()
        is_sunday = df.index.dayofweek == 6
        df_valid = df[~is_sunday].copy()
        
        # Calculate ATR for significance filtering
        high, low, close = df_valid['high'], df_valid['low'], df_valid['close']
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().fillna(method='bfill').values
        
        highs, lows, closes = high.values, low.values, close.values
        idx = df_valid.index
        
        raw_results = []
        for i in range(2, len(df_valid) - 1):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                if closes[i+1] < closes[i]:
                    raw_results.append({'ts': idx[i], 'type': 'HIGH', 'price': highs[i], 'atr': atr[i]})
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                if closes[i+1] > closes[i]:
                    raw_results.append({'ts': idx[i], 'type': 'LOW', 'price': lows[i], 'atr': atr[i]})
        
        if not raw_results: return pd.DataFrame()
        
        # --- CLUSTER FILTERING (Keep only the best extreme in a sequence) ---
        filtered = []
        if raw_results:
            current_group = [raw_results[0]]
            for r in raw_results[1:]:
                if r['type'] == current_group[-1]['type']:
                    current_group.append(r)
                else:
                    # Pick the best from the group
                    if current_group[0]['type'] == 'HIGH':
                        best = max(current_group, key=lambda x: x['price'])
                    else:
                        best = min(current_group, key=lambda x: x['price'])
                    filtered.append(best)
                    current_group = [r]
            # Handle last group
            if current_group[0]['type'] == 'HIGH':
                best = max(current_group, key=lambda x: x['price'])
            else:
                best = min(current_group, key=lambda x: x['price'])
            filtered.append(best)

        # --- SIGNIFICANCE FILTER (ATR Gate) ---
        final = []
        if len(filtered) > 1:
            for i in range(1, len(filtered)):
                move = abs(filtered[i]['price'] - filtered[i-1]['price'])
                # Only keep if the move between swings is > 1.5 * ATR
                if move > (1.5 * filtered[i]['atr']):
                    final.append(filtered[i])
        
        return pd.DataFrame(final if final else filtered)

    @classmethod
    def detect_liquidity_sweep(cls, ohlc, swing_v4):
        \"\"\"
        Filtered Liquidity Sweeps: Only checks against the last 10 significant swings.
        \"\"\"
        import pandas as pd
        if swing_v4.empty: return pd.DataFrame()
        sweeps = []
        for i, row in swing_v4.iterrows():
            # Check against only the last few significant highs/lows (Structure)
            prev_swings = swing_v4[(swing_v4['type'] == row['type']) & (swing_v4['ts'] < row['ts'])].tail(10)
            if not prev_swings.empty:
                prev_p = prev_swings.iloc[-1]['price']
                if row['type'] == 'HIGH' and row['price'] > prev_p:
                    sweeps.append({'ts': row['ts'], 'type': 'BUY_STOP_RUN', 'price': row['price']})
                elif row['type'] == 'LOW' and row['price'] < prev_p:
                    sweeps.append({'ts': row['ts'], 'type': 'SELL_STOP_RUN', 'price': row['price']})
        return pd.DataFrame(sweeps)
"""

with open(path, 'w') as f:
    f.writelines(lines)
    f.write(new_methods)

print("Successfully applied Significance Filters to smc class.")
