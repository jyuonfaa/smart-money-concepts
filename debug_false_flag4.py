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
df_15m = df.resample('15min').agg({'open':'first','high':'max',
    'low':'min','close':'last','volume':'sum'}).dropna()

daily_swings = smc.swing_highs_lows(df_daily, swing_length=10)
daily_cons = smc.consolidation(df_daily)
daily_ob = smc.ob(df_daily, daily_swings)
daily_reversals = detect_reversals(df_daily, daily_swings)
daily_liq = smc.liquidity(df_daily, daily_swings)
daily_ts = turtle_soup_signals(df_daily, daily_reversals, daily_ob, df_daily,
    liq_df=daily_liq)
daily_rets = smc.retracements(df_daily, daily_swings)

# For April 14 episode: cons Top=0.76539 Bot=0.75004, ob_top=0.76432 ob_bot=0.75793
# Check: is April 14 in premium?
apr14_idx = daily_rets.index.get_loc(pd.Timestamp('2016-04-14')) if pd.Timestamp('2016-04-14') in daily_rets.index else None
if apr14_idx is None:
    # daily_rets may have a RangeIndex — align by position using df_daily
    pos = df_daily.index.get_loc(pd.Timestamp('2016-04-14'))
    apr14_ret = daily_rets.iloc[pos]
else:
    apr14_ret = daily_rets.iloc[apr14_idx]
print('Apr 14 retracement row:')
print('daily_rets index type:', type(daily_rets.index))
print('daily_rets columns:', daily_rets.columns.tolist())
print(apr14_ret)

# Check 15M candles after Apr 14 for first return to OB zone
# OB zone: 0.75793 to 0.76432, close < cons_top 0.76539
search_start = pd.Timestamp('2016-04-15')
df_15m_after = df_15m[df_15m.index >= search_start]
ob_bot = 0.75793
ob_top = 0.76432
cons_top = 0.76539

candidates = df_15m_after[
    (df_15m_after['high'] >= ob_bot) &
    (df_15m_after['high'] <= ob_top) &
    (df_15m_after['close'] < cons_top)
]
print()
print('First 5 qualifying 15M entry candles after Apr 14:')
print(candidates.head(5)[['open','high','low','close']])
