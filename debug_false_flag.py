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
daily_cons = smc.consolidation(df_daily)
daily_rets = smc.retracements(df_daily, daily_swings)
daily_ob = smc.ob(df_daily, daily_swings)
daily_reversals = detect_reversals(df_daily, daily_swings)
daily_liq = smc.liquidity(df_daily, daily_swings)
daily_ts = turtle_soup_signals(df_daily, daily_reversals, daily_ob, df_daily, liq_df=daily_liq)

# --- Layer 1: Daily Consolidation ---
is_cons = daily_cons['Consolidation'].notna() & (daily_cons['Consolidation'] != 0)
print('=== LAYER 1: Daily Consolidation ===')
print('Total days in consolidation:', is_cons.sum())
print(daily_cons[is_cons][['Consolidation','Top','Bottom']].head(5))

# --- Layer 2: Daily Turtle Soup signals ---
print()
print('=== LAYER 2: Daily Turtle Soup Signals ===')
bear_count = daily_ts['turtle_soup_bear'].sum()
bull_count = daily_ts['turtle_soup_bull'].sum()
print('turtle_soup_bear days:', bear_count)
print('turtle_soup_bull days:', bull_count)
print(daily_ts[daily_ts['turtle_soup_bear'] == True][['turtle_soup_bear','ts_ob_top','ts_ob_bottom']].head(5))
print(daily_ts[daily_ts['turtle_soup_bull'] == True][['turtle_soup_bull','ts_ob_top','ts_ob_bottom']].head(5))

# --- Layer 3: Daily Premium/Discount ---
d_dir = daily_rets['Direction'].values
ret_pct = daily_rets['CurrentRetracement%'].values
is_bullish = d_dir == 1
is_bearish = d_dir == -1
daily_premium = (is_bullish & (ret_pct < 50)) | (is_bearish & (ret_pct > 50))
daily_discount = (is_bullish & (ret_pct > 50)) | (is_bearish & (ret_pct < 50))
print()
print('=== LAYER 3: Daily Premium/Discount ===')
print('Days in premium:', daily_premium.sum())
print('Days in discount:', daily_discount.sum())
print('Days with NaN direction:', pd.isna(d_dir).sum())

# --- Layer 4: Coincidence check ---
ts_bear = daily_ts['turtle_soup_bear'].values
ts_bull = daily_ts['turtle_soup_bull'].values
cons_arr = is_cons.values
coincidence_bear = cons_arr & ts_bear & daily_premium
coincidence_bull = cons_arr & ts_bull & daily_discount
print()
print('=== LAYER 4: Coincidence (cons AND ts AND premium/discount) ===')
print('Bear episode candidates:', coincidence_bear.sum())
print('Bull episode candidates:', coincidence_bull.sum())

# --- Layer 5: What does ts_bear look like on cons days? ---
print()
print('=== LAYER 5: ts_bear values on consolidation days ===')
cons_days = daily_cons[is_cons].index
ts_on_cons = daily_ts.loc[daily_ts.index.isin(cons_days), ['turtle_soup_bear','turtle_soup_bull']]
print('Consolidation days with ts_bear=True:', (ts_on_cons['turtle_soup_bear'] == True).sum())
print('Consolidation days with ts_bull=True:', (ts_on_cons['turtle_soup_bull'] == True).sum())

# --- Layer 6: Sample of turtle soup bear dates vs consolidation dates ---
print()
print('=== LAYER 6: Sample turtle_soup_bear dates ===')
bear_dates = daily_ts[daily_ts['turtle_soup_bear'] == True].index
print(bear_dates[:10].tolist())
print('Sample consolidation dates:')
print(daily_cons[is_cons].index[:10].tolist())
