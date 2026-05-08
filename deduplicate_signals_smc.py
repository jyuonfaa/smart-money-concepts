import os

path = r'd:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py'

with open(path, 'r') as f:
    lines = f.readlines()

# Remove the raw swing_highs_lows_v4 to re-add it with Cluster Deduplication
start_idx = -1
for i, line in enumerate(lines):
    if '@classmethod' in line and 'def swing_highs_lows_v4' in lines[i+1]:
        start_idx = i
        break
if start_idx != -1:
    lines = lines[:start_idx]

# THE REFINED VIDEO 4 LOGIC
# 4-CANDLE i+2 | SUNDAY SKIP | CLUSTER DEDUPLICATION (No Stacking)
refined_logic = """
    @classmethod
    def swing_highs_lows_v4(cls, ohlc):
        \"\"\"
        ICT Video 4: Religious 4-Candle confirmation.
        Includes Cluster Deduplication to prevent stacked labels.
        \"\"\"
        import pandas as pd
        df = ohlc.copy()
        is_sunday = df.index.dayofweek == 6
        df_v = df[~is_sunday].copy()
        h, l, c = df_v['high'].values, df_v['low'].values, df_v['close'].values
        idx = df_v.index
        raw = []
        
        for i in range(2, len(df_v) - 2):
            if h[i] > h[i-1] and h[i] > h[i+1]:
                if c[i+2] < c[i+1]: 
                    raw.append({'ts': idx[i], 'type': 'HIGH', 'p': h[i], 'label': 'High Down Move Confirmed'})
            if l[i] < l[i-1] and l[i] < l[i+1]:
                if c[i+2] > c[i+1]: 
                    raw.append({'ts': idx[i], 'type': 'LOW', 'p': l[i], 'label': 'Low Up Move Confirmed'})
        
        if not raw: return pd.DataFrame()
        
        # --- CLUSTER DEDUPLICATION ---
        # Ensures no two signals of the same type appear in sequence. 
        # Keeps only the absolute extreme of the cluster.
        final = []
        curr = raw[0]
        for nxt in raw[1:]:
            if nxt['type'] == curr['type']:
                # If next is more extreme, update current
                if (curr['type'] == 'HIGH' and nxt['p'] > curr['p']) or \
                   (curr['type'] == 'LOW' and nxt['p'] < curr['p']):
                    curr = nxt
            else:
                final.append(curr)
                curr = nxt
        final.append(curr)
        return pd.DataFrame(final)

    @classmethod
    def identify_order_block(cls, ohlc, confirmed_swings):
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
    f.write(refined_logic)

print("Successfully re-enabled Cluster Deduplication. Stacked labels will now be filtered to their absolute extremes.")
