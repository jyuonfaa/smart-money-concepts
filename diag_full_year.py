import pandas as pd
from smartmoneyconcepts.smc import smc

zn = pd.read_csv('tests/test_data/MACRO/ZN_Daily_2016.csv', parse_dates=['date'], index_col='date')
zb = pd.read_csv('tests/test_data/MACRO/ZB_Daily_2016.csv', parse_dates=['date'], index_col='date')
dxy = pd.read_csv('tests/test_data/MACRO/DXY_Daily_2016.csv', parse_dates=['date'], index_col='date')

df = smc.macro_bond_bias(zn, zb, dxy)

# Get ALL raw micro triggers across the entire year, with their regime on that date
zn_swings = smc.swing_highs_lows_v4(zn)
smt_micro = smc.smt_divergence(zn, zb, zn_swings, correlation='positive')

raw = pd.Series(0, index=zn.index)
raw[smt_micro['smt_bearish_div'] == True] = 1
raw[smt_micro['smt_bearish_div_bm'] == True] = 1
raw[smt_micro['smt_bullish_div'] == True] = -1
raw[smt_micro['smt_bullish_div_bm'] == True] = -1

nonzero = raw[raw != 0]

print("=== ALL RAW MICRO TRIGGERS — FULL 2016 YEAR ===")
print(f"{'Date':<15} | {'USD Effect':<12} | {'Regime':<10} | {'Aligned?':<10}")
print("-" * 55)
for dt, effect in nonzero.items():
    regime = df.at[dt, 'regime']
    aligned = "YES" if (regime != 0 and regime == effect) else "NO"
    effect_str = "BUY USD (+1)" if effect == 1 else "SELL USD (-1)"
    regime_str = "BULL (+1)" if regime == 1 else ("BEAR (-1)" if regime == -1 else "NONE (0)")
    print(f"{dt.date()!s:<15} | {effect_str:<12} | {regime_str:<10} | {aligned:<10}")

print()
print(f"Total raw triggers:      {len(nonzero)}")
print(f"Aligned signals (fired): {(df['signal'] != 0).sum()}")
print()

# Show regime windows
print("=== REGIME WINDOWS ===")
prev = 0
start = None
for dt, val in df['regime'].items():
    if val != prev:
        if prev != 0 and start:
            print(f"  Regime {prev:+d}: {start.date()} -> {dt.date()}")
        start = dt
        prev = val
if prev != 0:
    print(f"  Regime {prev:+d}: {start.date()} -> 2016-12-31 (year end)")
