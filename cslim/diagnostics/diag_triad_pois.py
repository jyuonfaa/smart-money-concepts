"""
Diagnostic script for Triad POIs.
"""
import pandas as pd
import numpy as np
from smartmoneyconcepts.smc import smc

dxy = pd.read_csv("tests/test_data/MACRO/DXY_Daily_2016.csv")
dxy['date'] = pd.to_datetime(dxy['date'])
dxy.set_index('date', inplace=True)

# Build POIs exactly as in verify_month4_video1.py
dxy_swings_v1 = smc.swing_highs_lows(dxy, swing_length=5)
dxy_ob = smc.ob(dxy, dxy_swings_v1)
pois_ob = dxy_ob[dxy_ob['OB'].notna()][['Top', 'Bottom']].rename(
    columns={'Top': 'top', 'Bottom': 'bottom'}
)

dxy_fvg = smc.fvg(dxy)
pois_fvg = dxy_fvg[dxy_fvg['FVG'].notna()][['Top', 'Bottom']].rename(
    columns={'Top': 'top', 'Bottom': 'bottom'}
)

dxy_liq = smc.liquidity(dxy, dxy_swings_v1)
pois_liq = dxy_liq[dxy_liq['Liquidity'].notna()][['Level']].copy()
pois_liq['top'] = pois_liq['Level']
pois_liq['bottom'] = pois_liq['Level']
pois_liq = pois_liq[['top', 'bottom']]

usdx_pois = pd.concat([pois_ob, pois_fvg, pois_liq]).dropna()

# 1. print len and head(20)
print(f"Total POIs count: {len(usdx_pois)}")
print("=== First 20 POIs ===")
print(usdx_pois.head(20))
print()

# 2. Pick 2016-03-04
date_target = pd.Timestamp("2016-03-04")
dxy_close = dxy.loc[date_target, 'close']
print(f"DXY Close on {date_target.date()}: {dxy_close}")

# Let's get the swing price on that date from dxy_swings
dxy_swings = smc.swing_highs_lows_v4(dxy)
swing_row = dxy_swings[dxy_swings['ts'] == date_target]
if not swing_row.empty:
    swing_price = swing_row.iloc[0]['p']
    print(f"DXY Swing Price on {date_target.date()}: {swing_price}")
else:
    # Check nearest swing
    dxy_swings['time_diff'] = (dxy_swings['ts'] - date_target).abs()
    nearest_idx = dxy_swings['time_diff'].idxmin()
    nearest_row = dxy_swings.loc[nearest_idx]
    swing_price = nearest_row['p']
    print(f"Nearest DXY Swing Price around {date_target.date()}: {swing_price} at {nearest_row['ts'].date()}")

# Manually find which POI rows contain this price
print("Matching POIs containing this price:")
matched = []
for idx, poi in usdx_pois.iterrows():
    if poi['bottom'] <= swing_price <= poi['top']:
        matched.append((idx, poi['bottom'], poi['top']))
for m in matched:
    print(f"  Row Index: {m[0].date() if isinstance(m[0], pd.Timestamp) else m[0]} | Range: [{m[1]:.5f}, {m[2]:.5f}]")
print()

# 3. Test _is_at_poi with an extreme price
def _is_at_poi(swing_price):
    for _, poi in usdx_pois.iterrows():
        top = poi['top']
        bottom = poi['bottom']
        if bottom <= swing_price <= top:
            return True
    return False

extreme_high = 200.0
extreme_low = 10.0
inside_price = swing_price

print(f"Test _is_at_poi({extreme_high}): {_is_at_poi(extreme_high)}")
print(f"Test _is_at_poi({extreme_low}): {_is_at_poi(extreme_low)}")
print(f"Test _is_at_poi({inside_price}): {_is_at_poi(inside_price)}")
