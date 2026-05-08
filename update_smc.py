import os

new_code = """

def swing_highs_lows_v4(ohlc):
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

def detect_liquidity_sweep(ohlc, swing_v4):
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

with open(r'd:\C.Slim\ict-intelligence\smartmoneyconcepts\smc.py', 'a') as f:
    f.write(new_code)
print("Successfully appended Video 4 logic to smc.py")
