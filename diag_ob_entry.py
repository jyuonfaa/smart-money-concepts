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
df_15m   = df.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

daily_swings   = smc.swing_highs_lows(df_daily, swing_length=10)
daily_ob       = smc.ob(df_daily, daily_swings)
daily_reversals= detect_reversals(df_daily, daily_swings)
daily_liq      = smc.liquidity(df_daily, daily_swings)
daily_ts       = turtle_soup_signals(df_daily, daily_reversals, daily_ob, df_daily, liq_df=daily_liq)

swings_4h = smc.swing_highs_lows(df_4h, swing_length=10)
ob_4h     = smc.ob(df_4h, swings_4h)
disp_4h   = smc.displacement(df_4h)

disp_4h_times = df_4h.index.values
ob_4h_times   = df_4h.index.values

# The four episodes from the trace
episodes = [
    ('2016-04-14', 'bear', 0.76539),
    ('2016-06-21', 'bear', 0.74680),
    ('2016-10-19', 'bear', 0.76970),
    ('2016-11-08', 'bear', 0.76800),
]

for ep_date_str, ep_type, ctop in episodes:
    ep_ts     = pd.Timestamp(ep_date_str)
    ep_4h_idx = int(np.searchsorted(ob_4h_times, np.datetime64(ep_ts)))
    print(f"\n=== Episode {ep_date_str} ({ep_type}) ctop={ctop:.5f} ep_4h_idx={ep_4h_idx} ===")

    # Find the 4H OB
    ob_top, ob_bot = np.nan, np.nan
    for k in range(ep_4h_idx, -1, -1):
        if ob_4h['OB'].iloc[k] == -1.0:
            mit_idx = ob_4h['MitigatedIndex'].iloc[k]
            passes  = pd.isna(mit_idx) or (mit_idx == 0.0 and k > 0) or mit_idx >= ep_4h_idx
            print(f"  4H OB at k={k} date={df_4h.index[k]}  top={ob_4h['Top'].iloc[k]:.5f}  "
                  f"bot={ob_4h['Bottom'].iloc[k]:.5f}  mit_idx={mit_idx}  passes={passes}")
            if passes:
                ob_top = ob_4h['Top'].iloc[k]
                ob_bot = ob_4h['Bottom'].iloc[k]
                break

    if np.isnan(ob_bot):
        print("  --> No qualifying 4H OB found. Episode skipped.")
        continue

    print(f"  --> OB zone: {ob_bot:.5f} – {ob_top:.5f}")

    # Scan 15M for entry
    search_start = ep_ts + pd.Timedelta(days=1)
    ltf_sub = df_15m[df_15m.index >= search_start].head(500)
    candidates = ltf_sub[
        (ltf_sub['high'] >= ob_bot) &
        (ltf_sub['high'] <= ob_top) &
        (ltf_sub['close'] < ctop)
    ]
    print(f"  15M qualifying entry candles: {len(candidates)}")
    if len(candidates) > 0:
        print(candidates.head(3)[['open','high','low','close']])
    else:
        print(f"  15M high range after episode: min={ltf_sub['high'].min():.5f}  max={ltf_sub['high'].max():.5f}")
