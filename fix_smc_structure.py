import os

path = r'd:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py'

# Read the file
with open(path, 'r') as f:
    lines = f.readlines()

# Remove the previous bad append (the last ~60 lines)
# We look for the start of our previous append
start_idx = -1
for i, line in enumerate(lines):
    if 'def swing_highs_lows_v4(ohlc):' in line:
        start_idx = i
        break

if start_idx != -1:
    lines = lines[:start_idx]

# Find the end of the 'smc' class (it's the whole file basically, so we look for where to insert)
# Actually, I'll just append them to the class by finding the end of the class definition.
# Since the class spans the whole file, I will just append them with proper indentation.

new_methods = """
    @classmethod
    def swing_highs_lows_v4(cls, ohlc):
        \"\"\"
        ICT Video 4: Confirmed Retracement Swing Engine.
        - 3-Candle Base: Center is extreme (including wicks).
        - 4th Candle Confirmation: Must CLOSE in the reversal direction.
        - Sunday Filter: Skips Sunday candles in the sequence.
        \"\"\"
        import pandas as pd
        df = ohlc.copy()
        # Identify Sundays (NY time)
        is_sunday = df.index.dayofweek == 6
        df_valid = df[~is_sunday].copy()
        
        highs = df_valid['high'].values
        lows  = df_valid['low'].values
        closes = df_valid['close'].values
        idx   = df_valid.index
        
        results = []
        for i in range(2, len(df_valid) - 1):
            # --- SWING HIGH (BULLISH RETRACEMENT) ---
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                if closes[i+1] < closes[i]: # 4th candle closed lower
                    results.append({'ts': idx[i], 'type': 'HIGH', 'price': highs[i], 'confirmed_at': idx[i+1]})
            
            # --- SWING LOW (BEARISH RETRACEMENT) ---
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                if closes[i+1] > closes[i]: # 4th candle closed higher
                    results.append({'ts': idx[i], 'type': 'LOW', 'price': lows[i], 'confirmed_at': idx[i+1]})
                    
        return pd.DataFrame(results)

    @classmethod
    def detect_liquidity_sweep(cls, ohlc, swing_v4):
        \"\"\"
        ICT Video 4: Identifying Stop Runs (Liquidity Sweeps).
        Checks if price breached an old swing high/low before a confirmed retracement.
        \"\"\"
        import pandas as pd
        sweeps = []
        for i, row in swing_v4.iterrows():
            prev_swings = swing_v4[(swing_v4['type'] == row['type']) & (swing_v4['ts'] < row['ts'])]
            if not prev_swings.empty:
                prev_p = prev_swings.iloc[-1]['price']
                if row['type'] == 'HIGH' and row['price'] > prev_p:
                    sweeps.append({'ts': row['ts'], 'type': 'BUY_STOP_RUN', 'price': row['price']})
                elif row['type'] == 'LOW' and row['price'] < prev_p:
                    sweeps.append({'ts': row['ts'], 'type': 'SELL_STOP_RUN', 'price': row['price']})
        return pd.DataFrame(sweeps)
"""

# Append the methods to the end of the file (which is inside the class scope)
with open(path, 'w') as f:
    f.writelines(lines)
    f.write(new_methods)

print("Successfully integrated Video 4 methods into smc class.")
