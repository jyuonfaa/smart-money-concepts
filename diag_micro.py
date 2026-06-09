import pandas as pd
from smartmoneyconcepts.smc import smc

zn = pd.read_csv('tests/test_data/MACRO/ZN_Daily_2016.csv', parse_dates=['date'], index_col='date')
zb = pd.read_csv('tests/test_data/MACRO/ZB_Daily_2016.csv', parse_dates=['date'], index_col='date')
dxy = pd.read_csv('tests/test_data/MACRO/DXY_Daily_2016.csv', parse_dates=['date'], index_col='date')

df = smc.macro_bond_bias(zn, zb, dxy)

trigger_dates = [pd.Timestamp('2016-04-26'), pd.Timestamp('2016-05-19'), pd.Timestamp('2016-07-27')]
print("Regime on micro trigger dates:")
for d in trigger_dates:
    r = df.at[d, 'regime']
    print("  " + str(d.date()) + ": regime=" + str(r))

print()
zn_swings = smc.swing_highs_lows_v4(zn)
smt_micro = smc.smt_divergence(zn, zb, zn_swings, correlation='positive')

# Map every trigger column to its USD directional effect
raw = pd.Series(0, index=zn.index)
raw[smt_micro['smt_bearish_div'] == True] = 1
raw[smt_micro['smt_bearish_div_bm'] == True] = 1
raw[smt_micro['smt_bullish_div'] == True] = -1
raw[smt_micro['smt_bullish_div_bm'] == True] = -1

print("Raw micro USD-effect triggers after July 29 (Bullish Regime window):")
post = raw[raw.index >= '2016-07-29']
nonzero = post[post != 0]
if nonzero.empty:
    print("  NONE - no ZN/ZB SMT divergence detected on continuous data after regime started")
else:
    print(nonzero)

print()
# Check ALL smt_micro columns to see full detail
print("Full smt_micro event detail (all True rows after July 29):")
post_micro = smt_micro[smt_micro.index >= '2016-07-29']
event_cols = ['smt_bearish_div','smt_bearish_div_bm','smt_bullish_div','smt_bullish_div_bm']
for col in event_cols:
    fired = post_micro[post_micro[col] == True]
    if not fired.empty:
        print("  " + col + ": " + str(fired.index.tolist()))
    else:
        print("  " + col + ": none")
