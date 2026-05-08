import os

path = r'd:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py'

with open(path, 'r') as f:
    lines = f.readlines()

# Remove the previous Video 4 methods
start_idx = -1
for i, line in enumerate(lines):
    if '@classmethod' in line and 'def swing_highs_lows_v4' in lines[i+1]:
        start_idx = i
        break
if start_idx != -1:
    lines = lines[:start_idx]

# 100% RELIGIOUS VIDEO 4 LOGIC
religious_logic = """
    @classmethod
    def swing_highs_lows_v4(cls, ohlc):
        \"\"\"
        ICT Video 4 RELIGIOUS VERSION:
        - 3-Candle Base (i-1, i, i+1).
        - 4th Candle Confirmation (i+2) must CLOSE in reversal direction.
        - Sunday Filter included.
        \"\"\"
        import pandas as pd
        df = ohlc.copy()
        is_sunday = df.index.dayofweek == 6
        df_v = df[~is_sunday].copy() # 'v' for valid/non-sunday
        
        h, l, c = df_v['high'].values, df_v['low'].values, df_v['close'].values
        idx = df_v.index
        raw = []
        
        # Religious sequence requires i+2 check, so range ends at len-2
        for i in range(2, len(df_v) - 2):
            # --- SWING HIGH (OH Potential) ---
            if h[i] > h[i-1] and h[i] > h[i+1]:
                # THE 4TH CANDLE (i+2) MUST CLOSE DOWN
                if c[i+2] < c[i+1]: # Confirmation
                    raw.append({'ts': idx[i], 'type': 'HIGH', 'p': h[i], 'origin_ts': idx[i-1]})
            
            # --- SWING LOW (OL Potential) ---
            if l[i] < l[i-1] and l[i] < l[i+1]:
                # THE 4TH CANDLE (i+2) MUST CLOSE UP
                if c[i+2] > c[i+1]: # Confirmation
                    raw.append({'ts': idx[i], 'type': 'LOW', 'p': l[i], 'origin_ts': idx[i-1]})
        
        if not raw: return pd.DataFrame()
        
        # Rigid Toggle (Picking absolute extremes for the wave)
        final = []
        curr = raw[0]
        for nxt in raw[1:]:
            if nxt['type'] == curr['type']:
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
        \"\"\"
        ICT Video 4: Identifying the 'Down candle before the up move'.
        \"\"\"
        import pandas as pd
        obs = []
        for i in range(1, len(confirmed_swings)):
            curr = confirmed_swings.iloc[i]
            prev = confirmed_swings.iloc[i-1]
            if curr['type'] == 'HIGH' and prev['type'] == 'LOW':
                # Bullish Impulse (Low to High). Look for the last down candle near the Low.
                sub = ohlc.loc[prev['ts']:curr['ts']]
                down_candles = sub[sub['close'] < sub['open']]
                if not down_candles.empty:
                    ob_row = down_candles.iloc[0] # The one that started the move
                    obs.append({'ts': ob_row.name, 'type': 'BULLISH_OB', 'high': ob_row['high'], 'low': ob_row['low']})
        return pd.DataFrame(obs)
"""

with open(path, 'w') as f:
    f.writelines(lines)
    f.write(religious_logic)

print("Successfully applied 100% RELIGIOUS Video 4 logic.")
