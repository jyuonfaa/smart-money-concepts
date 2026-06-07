"""
verify_month3_video1.py
Month 3, Video 1 Verification Gate
Confirms:
  1. Monthly, Weekly, Daily pipeline is intact
  2. smc.breaker_blocks() finds structurally sound levels
  3. smc.macro_swing_grading() returns correct quadrant levels
"""

import pandas as pd
from smartmoneyconcepts import smc

CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

df_monthly = df_raw.resample('ME').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_weekly  = df_raw.resample('W').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_daily   = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

swings_d = smc.swing_highs_lows(df_daily, swing_length=10)

print("=" * 60)
print("  MONTH 3 VIDEO 1 - VERIFICATION GATE")
print("=" * 60)

# --- Task 3: Data Pipeline ---
print("\n[TASK 3] Data Pipeline:")
print(f"  Monthly bars : {len(df_monthly)}")
print(f"  Weekly  bars : {len(df_weekly)}")
print(f"  Daily   bars : {len(df_daily)}")
assert len(df_monthly) == 12, "Expected 12 monthly bars for 2016"
assert len(df_weekly)  >= 52, "Expected at least 52 weekly bars for 2016"
print("  [PASS] Monthly, Weekly, Daily resampling confirmed.")

# --- Task 2: Macro Swing Grading ---
print("\n[TASK 2] Macro Swing Grading (Daily AUDUSD 2016):")
grades = smc.macro_swing_grading(df_daily)
q0   = grades['0%'].iloc[0]
q25  = grades['25%'].iloc[0]
q50  = grades['50%'].iloc[0]
q75  = grades['75%'].iloc[0]
q100 = grades['100%'].iloc[0]
print(f"  0%  (Absolute Low)  = {q0:.5f}")
print(f"  25% (Q1)            = {q25:.5f}")
print(f"  50% (Equilibrium)   = {q50:.5f}")
print(f"  75% (Q3)            = {q75:.5f}")
print(f"  100% (Absolute High)= {q100:.5f}")
# Confirm ordering is mathematically sound
assert q0 < q25 < q50 < q75 < q100, "Quadrant ordering is wrong!"
assert abs((q50 - q0) - (q100 - q50)) < 0.00001, "Equilibrium is not centered!"
print("  [PASS] Quadrant levels are mathematically ordered and Equilibrium is centered.")

# --- Task 1: Breaker Blocks ---
print("\n[TASK 1] Breaker Blocks (Daily AUDUSD 2016):")
bb = smc.breaker_blocks(df_daily, swings_d)
bb.index = df_daily.index
valid_bb = bb.dropna()
print(f"  Total Breaker Blocks Found: {len(valid_bb)}")
bearish = valid_bb[valid_bb['Breaker'] == -1]
bullish = valid_bb[valid_bb['Breaker'] ==  1]
print(f"  Bearish Breakers (Resistance): {len(bearish)}")
print(f"  Bullish Breakers (Support):    {len(bullish)}")
for dt, row in valid_bb.iterrows():
    kind = "BEAR" if row['Breaker'] == -1 else "BULL"
    print(f"    [{kind}] {dt.date()}  Top={row['Top']:.5f}  Bot={row['Bottom']:.5f}")
assert len(valid_bb) > 0, "No Breaker Blocks found - logic error!"
for _, row in valid_bb.iterrows():
    assert row['Top'] > row['Bottom'], "Breaker top must be above bottom"
print("  [PASS] All breaker top/bottom geometries are valid.")

print("\n" + "=" * 60)
print("  ALL CHECKS PASSED - VIDEO 1 GATEKEEPER CLEARED")
print("=" * 60)
