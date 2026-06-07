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

print('daily_ob index type:', type(daily_ob.index))
print('daily_ob columns:', daily_ob.columns.tolist())
print()
bear_obs = daily_ob[daily_ob['OB'] == -1.0]
print('All bearish OBs:')
print(bear_obs[['OB','Top','Bottom','MitigatedIndex']].to_string())
