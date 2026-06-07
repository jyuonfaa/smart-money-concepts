import pandas as pd
import numpy as np
from smartmoneyconcepts import smc

df = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv',
    sep=';', names=['date','open','high','low','close','volume'])
df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M%S')
df = df.set_index('date')

df_4h = df.resample('4h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

swings_4h = smc.swing_highs_lows(df_4h, swing_length=10)
ob_4h     = smc.ob(df_4h, swings_4h)

ob_4h_times = df_4h.index.values

episode_dates = ['2016-04-14', '2016-06-21', '2016-10-19', '2016-11-08']

for ep_date_str in episode_dates:
    ep_ts     = pd.Timestamp(ep_date_str)
    # Search from the END of the episode day
    ep_ts_end = ep_ts + pd.Timedelta(days=1)
    ep_4h_idx = int(np.searchsorted(ob_4h_times, np.datetime64(ep_ts_end))) - 1
    
    print(f'\n=== {ep_date_str}  ep_4h_idx={ep_4h_idx}  4H bar at idx={df_4h.index[ep_4h_idx]} ===')
    found = 0
    for k in range(ep_4h_idx, -1, -1):
        if ob_4h['OB'].iloc[k] == -1.0:
            mit_idx = ob_4h['MitigatedIndex'].iloc[k]
            passes   = pd.isna(mit_idx) or (mit_idx == 0.0 and k > 0) or mit_idx >= ep_4h_idx
            print(f'    k={k}  date={df_4h.index[k]}  top={ob_4h["Top"].iloc[k]:.5f}  bot={ob_4h["Bottom"].iloc[k]:.5f}  mit_idx={mit_idx}  PASSES={passes}')
            found += 1
            if found >= 1:
                break
