import os

path = r'd:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py'

with open(path, 'r') as f:
    lines = f.readlines()

# Remove the previous Video 4 methods to rebuild WITHOUT the toggle
start_idx = -1
for i, line in enumerate(lines):
    if '@classmethod' in line and 'def swing_highs_lows_v4' in lines[i+1]:
        start_idx = i
        break
if start_idx != -1:
    lines = lines[:start_idx]

# THE ARCHITECTURALLY CORRECT VIDEO 4 LOGIC
# NO TOGGLE | NO ALTERNATION | STRICT 4-CANDLE i+2
final_logic = """
    @classmethod
    def swing_highs_lows_v4(cls, ohlc):
        \"\"\"
        ICT Video 4: Religious 4-Candle confirmation.
        NO Rigid Toggle. Returns ALL confirmed swings to be filtered by the OTE zone.
        \"\"\"
        import pandas as pd
        df = ohlc.copy()
        is_sunday = df.index.dayofweek == 6
        df_v = df[~is_sunday].copy()
        h, l, c = df_v['high'].values, df_v['low'].values, df_v['close'].values
        idx = df_v.index
        results = []
        
        # Religious sequence requires i+2 check
        for i in range(2, len(df_v) - 2):
            # --- HIGH DOWN MOVE CONFIRMED ---
            if h[i] > h[i-1] and h[i] > h[i+1]:
                if c[i+2] < c[i+1]: # 4th candle closed down
                    results.append({'ts': idx[i], 'type': 'HIGH', 'p': h[i], 'label': 'High Down Move Confirmed'})
            
            # --- LOW UP MOVE CONFIRMED ---
            if l[i] < l[i-1] and l[i] < l[i+1]:
                if c[i+2] > c[i+1]: # 4th candle closed up
                    results.append({'ts': idx[i], 'type': 'LOW', 'p': l[i], 'label': 'Low Up Move Confirmed'})
        
        return pd.DataFrame(results)

    @classmethod
    def identify_order_block(cls, ohlc, confirmed_swings):
        \"\"\"
        ICT Video 4: OB identification.
        \"\"\"
        import pandas as pd
        if confirmed_swings.empty: return pd.DataFrame()
        obs = []
        for i in range(1, len(confirmed_swings)):
            curr = confirmed_swings.iloc[i]
            prev = confirmed_swings.iloc[i-1]
            if curr['type'] == 'HIGH' and prev['type'] == 'LOW':
                sub = ohlc.loc[prev['ts']:curr['ts']]
                down_candles = sub[sub['close'] < sub['open']]
                if not down_candles.empty:
                    ob_row = down_candles.iloc[0]
                    obs.append({'ts': ob_row.name, 'type': 'BULLISH_OB', 'high': ob_row['high'], 'low': ob_row['low']})
        return pd.DataFrame(obs)
"""

with open(path, 'w') as f:
    f.writelines(lines)
    f.write(final_logic)

print("Successfully removed Rigid Toggle. System now supports raw 4-candle confirmation for zonal filtering.")
