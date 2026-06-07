import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals

df = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv',
    sep=';', names=['date','open','high','low','close','volume'])
df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M%S')
df = df.set_index('date')

df_daily = df.resample('D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_4h    = df.resample('4h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

daily_swings   = smc.swing_highs_lows(df_daily, swing_length=10)
daily_cons     = smc.consolidation(df_daily)
daily_rets     = smc.retracements(df_daily, daily_swings)
daily_ob       = smc.ob(df_daily, daily_swings)
daily_reversals= detect_reversals(df_daily, daily_swings)
daily_liq      = smc.liquidity(df_daily, daily_swings)
daily_ts       = turtle_soup_signals(df_daily, daily_reversals, daily_ob, df_daily, liq_df=daily_liq)

swings_4h = smc.swing_highs_lows(df_4h, swing_length=10)
disp_4h   = smc.displacement(df_4h)

d_dir  = daily_rets['Direction'].values
ret_pct= daily_rets['CurrentRetracement%'].values
is_bullish = d_dir == 1
is_bearish = d_dir == -1
daily_premium  = (is_bullish & (ret_pct < 50)) | (is_bearish & (ret_pct > 50))
daily_discount = (is_bullish & (ret_pct > 50)) | (is_bearish & (ret_pct < 50))

is_cons_s    = daily_cons['Consolidation'].notna() & (daily_cons['Consolidation'] != 0)
is_cons      = is_cons_s.values
cons_top_vals= daily_cons['Top'].values
cons_bot_vals= daily_cons['Bottom'].values
ts_bear      = daily_ts['turtle_soup_bear'].values
ts_bull      = daily_ts['turtle_soup_bull'].values

disp_4h_times = df_4h.index.values
disp_4h_vals  = disp_4h['Displacement'].values

CONS_LOOKBACK = 30
n_daily = len(df_daily)

print("=== Episode Trace ===")
for i in range(n_daily):
    if not (ts_bear[i] and daily_premium[i]) and not (ts_bull[i] and daily_discount[i]):
        continue

    # Consolidation check
    ctop, cbot = np.nan, np.nan
    window_start = max(0, i - CONS_LOOKBACK)
    for j in range(i, window_start - 1, -1):
        if is_cons[j] and not np.isnan(cons_top_vals[j]):
            ctop = cons_top_vals[j]
            cbot = cons_bot_vals[j]
            break
    if np.isnan(ctop):
        continue

    daily_high_i = df_daily['high'].values[i]
    if daily_high_i < ctop * 0.998:
        continue

    ep_type = 'bear' if (ts_bear[i] and daily_premium[i]) else 'bull'
    ep_ts   = df_daily.index[i]
    lb_ts   = df_daily.index[max(0, i - CONS_LOOKBACK)]

    disp_mask  = (disp_4h_times >= np.datetime64(lb_ts)) & (disp_4h_times <= np.datetime64(ep_ts))
    disp_in_window = disp_4h_vals[disp_mask]
    needed_disp = 1.0 if ep_type == 'bear' else -1.0
    has_flagpole = np.any(disp_in_window == needed_disp)

    print(f"  {ep_ts.date()}  type={ep_type}  ctop={ctop:.5f}  daily_high={daily_high_i:.5f}  "
          f"lb={lb_ts.date()}  disps_in_window={disp_in_window[disp_in_window != 0].tolist()}  "
          f"has_flagpole={has_flagpole}")
