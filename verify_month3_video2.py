import pandas as pd
import numpy as np
from smartmoneyconcepts import smc

def test_body_based_sweep():
    print("=================================================================")
    print("  VERIFY MONTH 3 VIDEO 2: CANDLE BODY SWEEP CONFIRMATION")
    print("=================================================================\n")

    # Synthetic data for a bullish pool (resistance)
    # We need multiple swing highs around the same level.
    # swing_length=1 means 1 lower high before and after.
    # Index 1: swing high at 1.15
    # Index 3: swing high at 1.16
    # Index 5: wick goes to 1.25, close is 1.05 (no sweep yet)
    # Index 6: close is 1.20 (sweep)
    data = {
        'open':  [1.00, 1.05, 1.00, 1.05, 1.00, 1.00, 1.00],
        'high':  [1.05, 1.15, 1.05, 1.16, 1.05, 1.25, 1.25],
        'low':   [0.95, 1.00, 0.95, 1.00, 0.95, 0.95, 0.95],
        'close': [1.05, 1.10, 1.05, 1.10, 1.05, 1.05, 1.20],
        'volume':[100, 100, 100, 100, 100, 100, 100]
    }
    
    df = pd.DataFrame(data)
    df.index = pd.date_range('2023-01-01', periods=7, freq='D')
    
    # Run SMC functions
    shl = smc.swing_highs_lows(df, swing_length=1)
    # Use a large range_percent so 1.15 and 1.16 are grouped
    liq = smc.liquidity(df, shl, range_percent=0.10)
    
    bull_pools = liq[liq['Liquidity'] == 1]
    if not bull_pools.empty:
        idx = bull_pools.index[0]
        swept_idx = bull_pools.loc[idx, 'Swept']
        print(f"\nBullish pool found at {idx}. Swept at integer index: {swept_idx}")
        
        if swept_idx == 5:
            print("[FAIL] Pool was swept by a wick (candle 5). This violates ICT M3V2 rules.")
        elif swept_idx == 6:
            print("[PASS] Pool was swept by a close (candle 6).")
        elif swept_idx == 0:
            print("[FAIL] Pool was not swept.")
        else:
            print(f"[FAIL] Pool swept at unexpected index: {swept_idx}")
    else:
        print("[FAIL] No bullish pool found.")

    # Synthetic data for a bearish pool (support)
    # Index 1: swing low at 1.05
    # Index 3: swing low at 1.04
    # Index 5: wick goes to 0.95, close is 1.15 (no sweep yet)
    # Index 6: close is 1.00 (sweep)
    data2 = {
        'open':  [1.20, 1.15, 1.20, 1.15, 1.20, 1.20, 1.20],
        'high':  [1.25, 1.20, 1.25, 1.20, 1.25, 1.25, 1.25],
        'low':   [1.15, 1.05, 1.15, 1.04, 1.15, 0.95, 0.95],
        'close': [1.15, 1.10, 1.15, 1.10, 1.15, 1.15, 1.00],
        'volume':[100, 100, 100, 100, 100, 100, 100]
    }
    
    df2 = pd.DataFrame(data2)
    df2.index = pd.date_range('2023-01-01', periods=7, freq='D')
    
    shl2 = smc.swing_highs_lows(df2, swing_length=1)
    liq2 = smc.liquidity(df2, shl2, range_percent=0.10)
    
    bear_pools = liq2[liq2['Liquidity'] == -1]
    if not bear_pools.empty:
        idx = bear_pools.index[0]
        swept_idx = bear_pools.loc[idx, 'Swept']
        print(f"\nBearish pool found at {idx}. Swept at integer index: {swept_idx}")
        
        if swept_idx == 5:
            print("[FAIL] Pool was swept by a wick (candle 5). This violates ICT M3V2 rules.")
        elif swept_idx == 6:
            print("[PASS] Pool was swept by a close (candle 6).")
        elif swept_idx == 0:
            print("[FAIL] Pool was not swept.")
        else:
            print(f"[FAIL] Pool swept at unexpected index: {swept_idx}")
    else:
        print("[FAIL] No bearish pool found.")

if __name__ == "__main__":
    test_body_based_sweep()
