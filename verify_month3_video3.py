import pandas as pd
import numpy as np
from smartmoneyconcepts import smc

def test_ny_midnight():
    print("=================================================================")
    print("  VERIFY NY MIDNIGHT POWER 3 DETECTOR")
    print("=================================================================\n")

    # Create synthetic 15M data over 2 days
    # Day 1: Starts at exactly 00:00 NY time (05:00 UTC)
    # Day 2: Simulating a weekend gap where 00:00 NY is missing, first candle is 17:00 NY (22:00 UTC)
    
    dates = pd.date_range('2023-01-02 05:00:00', periods=10, freq='15min', tz='UTC')
    # Day 2: First candle at 22:00 UTC (17:00 NY)
    dates = dates.append(pd.date_range('2023-01-08 22:00:00', periods=5, freq='15min', tz='UTC'))
    
    data = {
        'open': np.random.rand(15),
        'high': np.random.rand(15),
        'low': np.random.rand(15),
        'close': np.random.rand(15),
        'volume': np.random.randint(100, 1000, size=15)
    }
    
    # Manually set the opening prices we expect to capture
    # Day 1: 00:00 NY open
    data['open'][0] = 1.1000
    
    # Day 2: 17:00 NY open (Index 10)
    data['open'][10] = 1.2000
    
    df = pd.DataFrame(data, index=dates)
    
    midnight_series = smc.ny_midnight_open(df)
    
    # Validation for Day 1
    day1_val = midnight_series.iloc[5] # some candle inside Day 1
    print(f"Day 1 (Has 00:00 candle) Expected Open: 1.1000")
    print(f"Day 1 Calculated Open: {day1_val}")
    
    if np.isclose(day1_val, 1.1000):
        print("[PASS] Day 1 NY Midnight Open correctly extracted and forward filled.")
    else:
        print("[FAIL] Day 1 calculation incorrect.")
        
    # Validation for Day 2
    day2_val = midnight_series.iloc[12] # some candle inside Day 2
    print(f"\nDay 2 (Missing 00:00, Starts 17:00) Expected Open: 1.2000")
    print(f"Day 2 Calculated Open: {day2_val}")
    
    if np.isclose(day2_val, 1.2000):
        print("[PASS] Day 2 NY Midnight Open correctly fell back to true session open.")
    else:
        print("[FAIL] Day 2 fallback incorrect.")
        
    print("\n=================================================================")
    print("  VERIFICATION COMPLETE")
    print("=================================================================")

if __name__ == "__main__":
    test_ny_midnight()
