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
df_4h = df.resample('4h').agg({'open':'first','high':'max',
    'low':'min','close':'last','volume':'sum'}).dropna()
df_15m = df.resample('15min').agg({'open':'first','high':'max',
    'low':'min','close':'last','volume':'sum'}).dropna()

daily_swings = smc.swing_highs_lows(df_daily, swing_length=10)
daily_cons = smc.consolidation(df_daily)
daily_rets = smc.retracements(df_daily, daily_swings)
daily_ob = smc.ob(df_daily, daily_swings)
daily_reversals = detect_reversals(df_daily, daily_swings)
daily_liq = smc.liquidity(df_daily, daily_swings)
daily_ts = turtle_soup_signals(df_daily, daily_reversals, daily_ob,
    df_daily, liq_df=daily_liq)

swings_4h = smc.swing_highs_lows(df_4h, swing_length=10)
ob_4h = smc.ob(df_4h, swings_4h)
disp_4h = smc.displacement(df_4h)

signals = false_flag_signals(
    df_daily, df_15m, df_4h,
    daily_cons, daily_rets, daily_ts,
    ob_4h, disp_4h
)

bull = signals[signals['false_bull_flag']]
bear = signals[signals['false_bear_flag']]
print(f'false_bull_flag signals: {len(bull)}')
print(f'false_bear_flag signals: {len(bear)}')
print(bull[['trap_entry','trap_stop_loss','trap_cons_top','trap_cons_bottom']].to_string())

bull_ok = (bull['trap_stop_loss'] > bull['trap_entry']).all() if len(bull) > 0 else True
bear_ok = (bear['trap_stop_loss'] < bear['trap_entry']).all() if len(bear) > 0 else True
print(f'Stop above entry for all bull flags: {bull_ok}')
print(f'Stop below entry for all bear flags: {bear_ok}')
