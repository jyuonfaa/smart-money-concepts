import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals

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
daily_ts = turtle_soup_signals(df_daily, daily_reversals, daily_ob, df_daily,
    liq_df=daily_liq)

# Print ALL turtle_soup_bear dates with their price
ts_bear_rows = daily_ts[daily_ts['turtle_soup_bear'] == True]
print('ALL turtle_soup_bear signals on Daily:')
print(ts_bear_rows[['turtle_soup_bear','ts_ob_top','ts_ob_bottom']].to_string())

# Print ALL consolidation dates with Top/Bottom
is_cons = daily_cons['Consolidation'].notna() & (daily_cons['Consolidation'] != 0)
cons_rows = daily_cons[is_cons]
print()
print('ALL Daily consolidation dates:')
print(cons_rows[['Consolidation','Top','Bottom']].to_string())
