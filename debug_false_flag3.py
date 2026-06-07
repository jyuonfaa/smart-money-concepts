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
daily_ob = smc.ob(df_daily, daily_swings)
daily_reversals = detect_reversals(df_daily, daily_swings)
daily_liq = smc.liquidity(df_daily, daily_swings)
daily_ts = turtle_soup_signals(df_daily, daily_reversals, daily_ob, df_daily,
    liq_df=daily_liq)

# For each turtle_soup_bear date, print the daily close price
ts_bear_rows = daily_ts[daily_ts['turtle_soup_bear'] == True]
print('turtle_soup_bear signals with daily close price:')
for date, row in ts_bear_rows.iterrows():
    close = df_daily.loc[date, 'close']
    print(f'{date.date()} | close: {close:.5f} | ob_top: {row["ts_ob_top"]:.5f} | ob_bot: {row["ts_ob_bottom"]:.5f}')

# Print the daily close prices for the 5 days around each signal
print()
print('Daily closes around April 14 (Mar 28 to Apr 20):')
mask = (df_daily.index >= '2016-03-28') & (df_daily.index <= '2016-04-20')
print(df_daily[mask]['close'].to_string())
