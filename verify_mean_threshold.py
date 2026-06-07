import pandas as pd
import numpy as np
from smartmoneyconcepts import smc

def test_mean_threshold():
    print("=================================================================")
    print("  VERIFY OB MEAN THRESHOLD (50% BODY MIDPOINT)")
    print("=================================================================\n")

    # Synthetic data to form a Bullish OB
    # Candles 0-2 form a swing high
    # Candle 3 breaks it (BOS)
    data = {
        'open':  [1.00, 1.05, 1.02, 1.00, 1.15],
        'high':  [1.05, 1.10, 1.08, 1.05, 1.25],
        'low':   [0.95, 1.00, 0.98, 0.90, 1.05],
        'close': [1.02, 1.08, 1.00, 0.95, 1.20],
        'volume':[100, 100, 100, 100, 100]
    }
    # OB candidate is the down candle at index 3.
    # Open: 1.00, Close: 0.95. Body mid = (1.00+0.95)/2 = 0.975
    
    df = pd.DataFrame(data)
    df.index = pd.date_range('2023-01-01', periods=5, freq='D')
    
    shl = smc.swing_highs_lows(df, swing_length=1)
    ob = smc.ob(df, shl)
    
    print("SMC Output for OBs:")
    print(ob.dropna(subset=['OB']))
    
    bull_obs = ob[ob['OB'] == 1]
    if not bull_obs.empty:
        idx = bull_obs.index[0]
        mean_thresh = bull_obs.loc[idx, 'MeanThreshold']
        expected_mean = (1.00 + 0.95) / 2.0
        
        print(f"\nBullish OB found at {idx}.")
        print(f"Calculated Mean Threshold: {mean_thresh}")
        print(f"Expected Mean Threshold: {expected_mean}")
        
        if np.isclose(mean_thresh, expected_mean):
            print("[PASS] Mean Threshold correctly calculates the 50% midpoint of the OB candle body.")
        else:
            print("[FAIL] Mean Threshold calculation is incorrect.")
    else:
        print("[FAIL] No bullish OB found.")

if __name__ == "__main__":
    test_mean_threshold()
