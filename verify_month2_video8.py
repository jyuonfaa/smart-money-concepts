import pandas as pd
import numpy as np
from smartmoneyconcepts import smc

def test_measured_moves():
    print("========================================")
    print("  VERIFYING MONTH 2 VIDEO 8: MEASURED MOVES")
    print("========================================\n")
    
    # Create synthetic daily OHLC data to test the geometric projector
    dates = pd.date_range('2016-01-01', periods=10, freq='D')
    
    # We will simulate a Bullish False Breakout setup
    # 1. Price creates a low (Low1)
    # 2. Price rallies to create a high (High1) -> This establishes the Amplitude
    # 3. Price drops to create a new low (Low2) below a consolidation -> This is the stop run
    # 4. Target should be Low2 + (High1 - Low1)
    
    df = pd.DataFrame({
        'open':  [1.0, 1.0, 1.5, 2.0, 2.0, 1.8, 1.5, 1.5, 2.0, 2.5],
        'high':  [1.5, 1.2, 2.0, 2.5, 2.2, 2.0, 1.6, 1.8, 2.5, 3.0],
        'low':   [0.8, 1.0, 1.2, 1.8, 1.5, 1.2, 0.9, 1.2, 1.5, 2.0],
        'close': [1.2, 1.1, 1.8, 2.2, 1.8, 1.5, 1.0, 1.6, 2.2, 2.8],
        'volume':[100]*10
    }, index=dates)
    
    # Manually define the swings instead of running the zigzag, for precise testing
    # Low1 at idx 1 (level 1.0)
    # High1 at idx 3 (level 2.5)
    # Low2 at idx 6 (level 0.9)  <- Stop Run
    
    shl_data = [np.nan]*10
    shl_lvl  = [np.nan]*10
    
    shl_data[1] = -1; shl_lvl[1] = 1.0  # Low1
    shl_data[3] = 1;  shl_lvl[3] = 2.5  # High1
    shl_data[6] = -1; shl_lvl[6] = 0.9  # Low2
    
    swings = pd.DataFrame({'HighLow': shl_data, 'Level': shl_lvl}, index=dates)
    
    print("1. Testing Geometric Projections...")
    measured = smc.measured_moves(df, swings)
    
    # At index 6, the Low2 is formed. 
    # Amplitude = High1 (2.5) - Low1 (1.0) = 1.5
    # TargetBull = Low2 (0.9) + 1.5 = 2.4
    
    target_bull_idx6 = measured['MeasuredTargetBull'].iloc[6]
    
    expected_target = 0.9 + (2.5 - 1.0)
    
    print(f"Low1: 1.0")
    print(f"High1: 2.5")
    print(f"Amplitude: 1.5")
    print(f"Low2 (Stop Run): 0.9")
    print(f"Expected Target (Low2 + Amplitude): {expected_target:.4f}")
    print(f"Algorithm Output Target: {target_bull_idx6:.4f}")
    
    if np.isclose(target_bull_idx6, expected_target):
        print(">> [PASS] Measured Target Bull is mathematically perfect.")
    else:
        print(">> [FAIL] Measured Target Bull is incorrect.")
        
    print("\n2. Testing integration with backtest_video7.py...")
    print("Run `python backtest_video7.py` to ensure it runs without errors.")
    
if __name__ == "__main__":
    test_measured_moves()
