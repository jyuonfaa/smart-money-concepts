import pandas as pd
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals, false_flag_signals

df = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv', sep=';', names=['date','open','high','low','close','volume'])
df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M%S')
df = df.set_index('date')
df_daily = df.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_15m = df.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_4h = df.resample('4h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

daily_swings = smc.swing_highs_lows(df_daily, swing_length=10)
daily_cons = smc.consolidation(df_daily)
daily_rets = smc.retracements(df_daily, daily_swings)
daily_ob_df = smc.ob(df_daily, daily_swings)
daily_reversals = detect_reversals(df_daily, daily_swings)
daily_liq = smc.liquidity(df_daily, daily_swings)
daily_ts = turtle_soup_signals(df_daily, daily_reversals, daily_ob_df, df_daily, liq_df=daily_liq)
swings_4h = smc.swing_highs_lows(df_4h, swing_length=10)
ob_4h = smc.ob(df_4h, swings_4h)
disp_4h = smc.displacement(df_4h)

ff_15m = false_flag_signals(df_daily, df_15m, df_4h, daily_cons, daily_rets, daily_ts, ob_4h, disp_4h)

print('--- Trades & Stop Losses ---')
for idx, row in ff_15m[ff_15m['false_bear_flag']].iterrows():
    print(idx, 'Bear Flag | Entry:', row['trap_entry'], 'SL:', row['trap_stop_loss'], 'low:', df_daily.loc[idx.strftime('%Y-%m-%d')]['low'])

for idx, row in ff_15m[ff_15m['false_bull_flag']].iterrows():
    print(idx, 'Bull Flag | Entry:', row['trap_entry'], 'SL:', row['trap_stop_loss'])
