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
daily_ts = turtle_soup_signals(df_daily, daily_reversals, daily_ob, df_daily, liq_df=daily_liq)
daily_rets = smc.retracements(df_daily, daily_swings)
daily_cons = smc.consolidation(df_daily)

d_dir = daily_rets['Direction'].values
ret_pct = daily_rets['CurrentRetracement%'].values
is_bullish = d_dir == 1
is_bearish = d_dir == -1
daily_premium = (is_bullish & (ret_pct < 50)) | (is_bearish & (ret_pct > 50))

ts_bear_dates = [pd.Timestamp('2016-04-14'), pd.Timestamp('2016-06-21'),
                 pd.Timestamp('2016-10-19'), pd.Timestamp('2016-11-08'), pd.Timestamp('2016-11-10')]

print('Per-episode breakdown:')
for d in ts_bear_dates:
    pos = df_daily.index.get_loc(d)
    is_prem = daily_premium[pos]
    direction = d_dir[pos]
    ret = ret_pct[pos]
    
    # lookback for cons_top
    is_cons = daily_cons['Consolidation'].notna() & (daily_cons['Consolidation'] != 0)
    cons_top_vals = daily_cons['Top'].values
    ctop = np.nan
    for j in range(pos, max(0, pos-30)-1, -1):
        if is_cons.iloc[j] and not np.isnan(cons_top_vals[j]):
            ctop = cons_top_vals[j]
            break
    
    daily_high = df_daily['high'].iloc[pos]
    high_ok = daily_high >= ctop * 0.998 if not np.isnan(ctop) else False

    print(f'{d.date()} | pos={pos} | dir={direction} | ret%={ret} | premium={is_prem} | ctop={ctop:.5f} | daily_high={daily_high:.5f} | high_ok={high_ok}')
