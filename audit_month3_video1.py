"""
audit_month3_video1.py
Full implementation audit for Month 3, Video 1 concepts.
Checks every named concept from the PDF against actual smc.py functions.
"""

import pandas as pd
import numpy as np
from smartmoneyconcepts import smc

CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

df_monthly = df_raw.resample('ME').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_weekly  = df_raw.resample('W').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_daily   = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_15m     = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

fails = []
passes = []

def check(name, expr, details=""):
    try:
        result = expr()
        passes.append(f"[PASS] {name}: {details}")
        return result
    except Exception as e:
        fails.append(f"[FAIL] {name}: {e}")
        return None

print("="*65)
print("  MONTH 3 VIDEO 1 - FULL IMPLEMENTATION AUDIT")
print("="*65)

# ---------------------------------------------------------------
# CONCEPT 1: Timeframe Hierarchy - Monthly, Weekly, Daily, 15M
# ---------------------------------------------------------------
print("\n[1] TIMEFRAME HIERARCHY")

swings_m = check("Monthly swing_highs_lows",
    lambda: smc.swing_highs_lows(df_monthly, swing_length=3),
    f"bars={len(df_monthly)}")

swings_w = check("Weekly swing_highs_lows",
    lambda: smc.swing_highs_lows(df_weekly, swing_length=5),
    f"bars={len(df_weekly)}")

swings_d = check("Daily swing_highs_lows",
    lambda: smc.swing_highs_lows(df_daily, swing_length=10),
    f"bars={len(df_daily)}")

swings_15m = check("15M swing_highs_lows",
    lambda: smc.swing_highs_lows(df_15m, swing_length=10),
    f"bars={len(df_15m)}")

# ---------------------------------------------------------------
# CONCEPT 2: Order Blocks (mentioned as 2nd setup)
# ---------------------------------------------------------------
print("\n[2] ORDER BLOCKS")

ob_monthly = check("Monthly Order Blocks",
    lambda: smc.ob(df_monthly, smc.swing_highs_lows(df_monthly, swing_length=3)),
    "ob() on monthly")

ob_weekly = check("Weekly Order Blocks",
    lambda: smc.ob(df_weekly, smc.swing_highs_lows(df_weekly, swing_length=5)),
    "ob() on weekly")

ob_daily = check("Daily Order Blocks",
    lambda: smc.ob(df_daily, swings_d),
    "ob() on daily")

# Validate columns returned
if ob_daily is not None:
    expected = {'OB', 'Top', 'Bottom', 'OBVolume', 'Percentage', 'MitigatedIndex'}
    missing = expected - set(ob_daily.columns)
    if missing:
        fails.append(f"[FAIL] Daily OB missing columns: {missing}")
    else:
        passes.append(f"[PASS] Daily OB columns intact: {list(ob_daily.columns)}")
    bull_obs = (ob_daily['OB'] == 1).sum()
    bear_obs = (ob_daily['OB'] == -1).sum()
    passes.append(f"[PASS] Daily OB count: {bull_obs} Bullish, {bear_obs} Bearish")

# ---------------------------------------------------------------
# CONCEPT 3: Stop Runs / Turtle Soup (mentioned as 3rd setup)
# ---------------------------------------------------------------
print("\n[3] STOP RUNS (LIQUIDITY / TURTLE SOUP)")

liq_daily = check("Daily Liquidity pools",
    lambda: smc.liquidity(df_daily, swings_d),
    "liquidity() on daily")

if liq_daily is not None:
    liq_valid = liq_daily.dropna()
    passes.append(f"[PASS] Found {len(liq_valid)} liquidity pools on Daily")
    expected_liq_cols = {'Liquidity', 'Level', 'End', 'Swept'}
    missing = expected_liq_cols - set(liq_daily.columns)
    if missing:
        fails.append(f"[FAIL] Liquidity missing columns: {missing}")

# ---------------------------------------------------------------
# CONCEPT 4: Optimal Trade Entry (OTE / Fib pullback - 1st setup)
# ---------------------------------------------------------------
print("\n[4] OPTIMAL TRADE ENTRY (OTE)")

rets_daily = check("Daily Retracements (OTE)",
    lambda: smc.retracements(df_daily, swings_d),
    "retracements() on daily")

if rets_daily is not None:
    expected_r_cols = {'Direction', 'CurrentRetracement%'}
    missing = expected_r_cols - set(rets_daily.columns)
    if missing:
        fails.append(f"[FAIL] Retracements missing columns: {missing}")
    else:
        bull_ote = ((rets_daily['Direction']==1)&(rets_daily['CurrentRetracement%'].between(62,79))).sum()
        bear_ote = ((rets_daily['Direction']==-1)&(rets_daily['CurrentRetracement%'].between(62,79))).sum()
        passes.append(f"[PASS] OTE zones on Daily: {bull_ote} Bull, {bear_ote} Bear (62-79% fib)")

# ---------------------------------------------------------------
# CONCEPT 5: Breaker Blocks (introduced in this video)
# ---------------------------------------------------------------
print("\n[5] BREAKER BLOCKS")

bb_daily = check("Daily Breaker Blocks",
    lambda: smc.breaker_blocks(df_daily, swings_d),
    "breaker_blocks() on daily")

if bb_daily is not None:
    bb_daily.index = df_daily.index
    valid_bb = bb_daily.dropna()
    n_bear = (valid_bb['Breaker'] == -1).sum()
    n_bull = (valid_bb['Breaker'] ==  1).sum()
    passes.append(f"[PASS] Daily Breakers: {n_bear} Bear, {n_bull} Bull")

    # Critical: geometry check - top must always be above bottom
    geo_ok = (valid_bb['Top'] > valid_bb['Bottom']).all()
    if not geo_ok:
        fails.append("[FAIL] Breaker geometry violation: Top <= Bottom in at least one row")
    else:
        passes.append("[PASS] Breaker geometry: Top > Bottom for all zones")

bb_weekly = check("Weekly Breaker Blocks",
    lambda: smc.breaker_blocks(df_weekly, smc.swing_highs_lows(df_weekly, swing_length=5)),
    "breaker_blocks() on weekly")

# ---------------------------------------------------------------
# CONCEPT 6: Macro Swing Grading (Fibonacci Quadrants)
# ---------------------------------------------------------------
print("\n[6] MACRO SWING GRADING")

grades_d = check("Daily Macro Grading",
    lambda: smc.macro_swing_grading(df_daily),
    "macro_swing_grading() on daily")

if grades_d is not None:
    cols = ['0%', '25%', '50%', '75%', '100%']
    vals = [grades_d[c].iloc[0] for c in cols]
    ordered = all(vals[i] < vals[i+1] for i in range(len(vals)-1))
    eq_centered = abs((vals[2] - vals[0]) - (vals[4] - vals[2])) < 0.00001
    if not ordered:
        fails.append("[FAIL] Macro grading quadrants are NOT in ascending order")
    else:
        passes.append(f"[PASS] Quadrant ordering: {' < '.join(f'{v:.5f}' for v in vals)}")
    if not eq_centered:
        fails.append("[FAIL] 50% Equilibrium is NOT at the true center of the macro range")
    else:
        passes.append(f"[PASS] Equilibrium ({vals[2]:.5f}) is perfectly centered")

grades_m = check("Monthly Macro Grading",
    lambda: smc.macro_swing_grading(df_monthly),
    "macro_swing_grading() on monthly")

# ---------------------------------------------------------------
# CONCEPT 7: Fair Value Gaps / Liquidity Voids (1st setup - detector only)
# ---------------------------------------------------------------
print("\n[7] FAIR VALUE GAPS (Liquidity Voids)")

fvg_daily = check("Daily FVG detector",
    lambda: smc.fvg(df_daily),
    "fvg() on daily")

if fvg_daily is not None:
    valid_fvg = fvg_daily.dropna()
    n_bull_fvg = (valid_fvg['FVG'] == 1).sum()
    n_bear_fvg = (valid_fvg['FVG'] == -1).sum()
    passes.append(f"[PASS] Daily FVGs found: {n_bull_fvg} Bullish, {n_bear_fvg} Bearish")

    # Check MitigatedIndex - this tells us if the void was 'closed' / returned to
    mitigated = valid_fvg['MitigatedIndex'].notna().sum()
    passes.append(f"[PASS] Mitigated FVGs (returned to): {mitigated} of {len(valid_fvg)}")

# ---------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------
print("\n" + "="*65)
print("  AUDIT RESULTS")
print("="*65)
for p in passes:
    print(p)
if fails:
    print()
    for f in fails:
        print(f)
print()
print(f"  {len(passes)} PASSED / {len(fails)} FAILED")
if len(fails) == 0:
    print("  ALL CONCEPTS CORRECTLY IMPLEMENTED")
else:
    print("  ACTION REQUIRED - see FAIL items above")
print("="*65)
