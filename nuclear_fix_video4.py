import os

path = r'd:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py'

# Read the file
with open(path, 'r') as f:
    lines = f.readlines()

# Remove the old swing_highs_lows_v4 and detect_liquidity_sweep
start_idx = -1
for i, line in enumerate(lines):
    if '@classmethod' in line and 'def swing_highs_lows_v4(cls, ohlc, filter_atr=True):' in lines[i+1]:
        start_idx = i
        break

if start_idx != -1:
    lines = lines[:start_idx]

# New, Rigidly Deduplicated methods
new_methods = """
    @classmethod
    def swing_highs_lows_v4(cls, ohlc):
        \"\"\"
        ICT Video 4: RIGID Institutional Swing Engine.
        - Guarantees High -> Low -> High sequence.
        - Picks absolute extreme for each wave.
        \"\"\"
        import pandas as pd
        import numpy as np
        df = ohlc.copy()
        is_sunday = df.index.dayofweek == 6
        df_valid = df[~is_sunday].copy()
        highs, lows, closes = df_valid['high'].values, df_valid['low'].values, df_valid['close'].values
        idx = df_valid.index
        
        raw = []
        for i in range(2, len(df_valid) - 1):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1] and closes[i+1] < closes[i]:
                raw.append({'ts': idx[i], 'type': 'HIGH', 'p': highs[i]})
            if lows[i] < lows[i-1] and lows[i] < lows[i+1] and closes[i+1] > closes[i]:
                raw.append({'ts': idx[i], 'type': 'LOW', 'p': lows[i]})
        
        if not raw: return pd.DataFrame()
        
        # --- RIGID TOGGLE FILTER ---
        final = []
        current = raw[0]
        for next_p in raw[1:]:
            if next_p['type'] == current['type']:
                # Update current if next is more extreme
                if (current['type'] == 'HIGH' and next_p['p'] > current['p']) or \
                   (current['type'] == 'LOW' and next_p['p'] < current['p']):
                    current = next_p
            else:
                final.append(current)
                current = next_p
        final.append(current)
        
        return pd.DataFrame(final)

    @classmethod
    def detect_liquidity_sweep(cls, ohlc, swing_v4):
        \"\"\"
        Detects Stop Runs relative to the last significant structural high/low.
        \"\"\"
        import pandas as pd
        if len(swing_v4) < 2: return pd.DataFrame()
        sweeps = []
        for i in range(1, len(swing_v4)):
            row = swing_v4.iloc[i]
            # Check if this swing 'raided' any of the previous 3 swings of the same type
            prev_same = swing_v4[(swing_v4['type'] == row['type']) & (swing_v4['ts'] < row['ts'])].tail(3)
            for _, prev in prev_same.iterrows():
                if row['type'] == 'HIGH' and row['p'] > prev['p']:
                    sweeps.append({'ts': row['ts'], 'type': 'BUY_STOP_RUN', 'p': row['p']})
                    break
                elif row['type'] == 'LOW' and row['p'] < prev['p']:
                    sweeps.append({'ts': row['ts'], 'type': 'SELL_STOP_RUN', 'p': row['p']})
                    break
        return pd.DataFrame(sweeps)
"""

with open(path, 'w') as f:
    f.writelines(lines)
    f.write(new_methods)

print("Successfully applied Rigid Toggle Filters to smc class.")
