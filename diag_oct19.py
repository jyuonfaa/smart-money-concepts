import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import (
    detect_reversals, turtle_soup_signals, false_flag_signals
)

df = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv',
    sep=';', names=['date','open','high','low','close','volume'])
df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M%S')
df = df.set_index('date')

df_daily = df.resample('D').agg({'open':'first','high':'max',
    'low':'min','close':'last','volume':'sum'}).dropna()

daily_swings = smc.swing_highs_lows(df_daily, swing_length=10)
daily_cons = smc.consolidation(df_daily)
daily_rets = smc.retracements(df_daily, daily_swings)
daily_ob = smc.ob(df_daily, daily_swings)
daily_reversals = detect_reversals(df_daily, daily_swings)
daily_liq = smc.liquidity(df_daily, daily_swings)
daily_ts = turtle_soup_signals(df_daily, daily_reversals, daily_ob,
    df_daily, liq_df=daily_liq)

# Check Oct 19 specifically
oct19_idx = df_daily.index.get_loc('2016-10-19')
print(f'Oct 19 index position: {oct19_idx}')

# Premium check
d_dir = daily_rets['Direction'].values
ret_pct = daily_rets['CurrentRetracement%'].values
is_bullish = d_dir == 1
is_bearish = d_dir == -1
daily_premium = (is_bullish & (ret_pct < 50)) | (is_bearish & (ret_pct > 50))
print(f'Oct 19 premium: {daily_premium[oct19_idx]}')
print(f'Oct 19 direction: {d_dir[oct19_idx]}, ret%: {ret_pct[oct19_idx]}')

# Turtle soup check
print(f'Oct 19 turtle_soup_bear: {daily_ts["turtle_soup_bear"].iloc[oct19_idx]}')
print(f'Oct 19 daily high: {df_daily.iloc[oct19_idx]["high"]:.5f}')

# Consolidation lookback from Oct 19
is_cons = daily_cons['Consolidation'].notna() & (daily_cons['Consolidation'] != 0)
cons_top_vals = daily_cons['Top'].values
cons_bot_vals = daily_cons['Bottom'].values
is_cons_arr = is_cons.values

print()
print('Consolidation lookback from Oct 19 (30 bars back):')
window_start = max(0, oct19_idx - 30)
found = False
for j in range(oct19_idx, window_start - 1, -1):
    if is_cons_arr[j] and not np.isnan(cons_top_vals[j]):
        print(f'  Found at position {j}: date={df_daily.index[j].date()}, top={cons_top_vals[j]:.5f}, bot={cons_bot_vals[j]:.5f}')
        print(f'  Daily high on Oct 19: {df_daily.iloc[oct19_idx]["high"]:.5f}')
        print(f'  Sanity check (high >= cons_top * 0.998): {df_daily.iloc[oct19_idx]["high"] >= cons_top_vals[j] * 0.998}')
        found = True
        break
if not found:
    print('  No consolidation found in lookback window.')

# OB check
print()
print('Bearish OB lookup from Oct 19:')
for k in range(oct19_idx, -1, -1):
    if daily_ob['OB'].iloc[k] == -1.0:
        mit_idx = daily_ob['MitigatedIndex'].iloc[k]
        print(f'  OB at position {k}, date={df_daily.index[k].date()}, top={daily_ob["Top"].iloc[k]:.5f}, bot={daily_ob["Bottom"].iloc[k]:.5f}, mit_idx={mit_idx}')
        passes = pd.isna(mit_idx) or (mit_idx == 0.0 and k > 0) or mit_idx >= oct19_idx
        print(f'  Passes filter: {passes}')
        if passes:
            break
