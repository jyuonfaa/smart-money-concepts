import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals, false_flag_signals

CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

df_daily_dt = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_daily_ri_focus = df_daily_dt.loc['2016-08-01':'2016-10-01'].reset_index()
df_15m = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().loc['2016-08-01':'2016-10-01']

daily_swings = smc.swing_highs_lows(df_daily_ri_focus, swing_length=5)
daily_ob     = smc.ob(df_daily_ri_focus, daily_swings)
daily_retracements = smc.retracements(df_daily_ri_focus, daily_swings)
daily_ohlc_time = df_daily_ri_focus.copy()
daily_ohlc_time.set_index('date', inplace=True)

swings_15m     = smc.swing_highs_lows(df_15m, swing_length=10)
reversals_15m  = detect_reversals(df_15m, swings_15m)
consolidation_15m = smc.consolidation(df_15m, prd=10, conslen=5)
liq_15m = smc.liquidity(df_15m, swings_15m)
ts_15m = turtle_soup_signals(df_15m, reversals_15m, daily_ob, df_daily_ri_focus, liq_df=liq_15m, use_daily_ob_stop=False, refinement_level='15M')
ff_15m = false_flag_signals(df_15m, ts_15m, consolidation_15m, daily_retracements, daily_ohlc_time, consolidation_lookback_bars=30)

COLS = ['turtle_soup_bear', 'ts_ob_top', 'ts_ob_bottom', 'ts_ob_stop', 'ts_target_near', 'ts_target_far']

pd.set_option('display.float_format', '{:.5f}'.format)
pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 200)

bull_ts = ff_15m[ff_15m['false_bull_flag']].index
print(f"Raw turtle_soup_signals output at {len(bull_ts)} false_bull_flag timestamps:\n")
print(ts_15m.loc[bull_ts, COLS].to_string())

print("\n--- liq_df sample (first 20 non-NaN rows) ---")
liq_non_null = liq_15m[liq_15m['Liquidity'].notna() & (liq_15m['Liquidity'] != 0)].head(20)
print(liq_non_null[['Liquidity', 'Level', 'IsTooClean']].to_string())
