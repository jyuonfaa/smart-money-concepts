import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals

CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

df_daily_dt = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_daily_ri_focus = df_daily_dt.loc['2016-08-01':'2016-10-01'].reset_index()
df_15m = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().loc['2016-08-01':'2016-10-01']

# Daily Data Prep
daily_swings = smc.swing_highs_lows(df_daily_ri_focus, swing_length=5)
daily_ob     = smc.ob(df_daily_ri_focus, daily_swings)

# 15M Data Prep
ltf_swings = smc.swing_highs_lows(df_15m, swing_length=5)
ltf_raw_ob = smc.ob(df_15m, ltf_swings)
reversals_15m = detect_reversals(df_15m, ltf_swings)

# Session OBs
london = smc.sessions(df_15m, "London")
ny = smc.sessions(df_15m, "New York")
combined_mask = (london['Active'] == 1) | (ny['Active'] == 1)
ltf_session_obs = smc.session_order_blocks(df_15m, ltf_raw_ob, combined_mask)

print("=================================================================")
print("  DIAGNOSTICS: SESSION OB FILTER & LETHARGY WINDOW SWEEP")
print("=================================================================\n")

raw_ob_count = ltf_raw_ob['OB'].notna().sum()
session_ob_count = ltf_session_obs['OB'].notna().sum()
print(f"[DATA] Raw 15M Order Blocks:          {raw_ob_count}")
print(f"[DATA] Session-Linked Order Blocks:   {session_ob_count}")
print(f"[DATA] Filter Reduction:              {raw_ob_count - session_ob_count} removed ({(1-session_ob_count/raw_ob_count)*100:.0f}%)\n")

# --- SCENARIO A: No session OB filter (existing baseline) ---
res_base = turtle_soup_signals(
    ohlc=df_15m,
    reversals=reversals_15m,
    daily_ob=daily_ob,
    daily_ohlc=df_daily_ri_focus,
    lethargy_window=5,
    lethargy_threshold_pips=0.0010,
)

total_bull_base = res_base['turtle_soup_bull'].sum()
total_bear_base = res_base['turtle_soup_bear'].sum()
total_base = total_bull_base + total_bear_base

print(f"--- Scenario A: Daily OB anchor only (NO session filter) ---")
print(f"Total Signals: {total_base}  (Bull: {total_bull_base}, Bear: {total_bear_base})")
if total_base > 0:
    leth_mask = res_base['is_lethargic'] & (res_base['turtle_soup_bull'] | res_base['turtle_soup_bear'])
    print(f"Lethargic Signals: {leth_mask.sum()} ({leth_mask.sum()/total_base*100:.1f}%)")
print()

# --- SCENARIO B: Session OB filter enabled ---
res_session = turtle_soup_signals(
    ohlc=df_15m,
    reversals=reversals_15m,
    daily_ob=daily_ob,
    daily_ohlc=df_daily_ri_focus,
    lethargy_window=5,
    lethargy_threshold_pips=0.0010,
    ltf_session_obs=ltf_session_obs,
)

total_bull_s = res_session['turtle_soup_bull'].sum()
total_bear_s = res_session['turtle_soup_bear'].sum()
total_s = total_bull_s + total_bear_s

print(f"--- Scenario B: Daily OB + Session OB precision filter ---")
print(f"Total Signals: {total_s}  (Bull: {total_bull_s}, Bear: {total_bear_s})")
if total_s > 0:
    leth_mask_s = res_session['is_lethargic'] & (res_session['turtle_soup_bull'] | res_session['turtle_soup_bear'])
    print(f"Lethargic Signals: {leth_mask_s.sum()} ({leth_mask_s.sum()/total_s*100:.1f}%)")
else:
    print("No signals survived session OB precision filter in this window.")
print()

# --- SCENARIO C: Lethargy window sweep on baseline ---
print("--- Scenario C: Lethargy window sweep on baseline signals ---")
windows = [3, 5, 10, 20]
for w in windows:
    res = turtle_soup_signals(
        ohlc=df_15m, reversals=reversals_15m, daily_ob=daily_ob, daily_ohlc=df_daily_ri_focus,
        lethargy_window=w, lethargy_threshold_pips=0.0010
    )
    sig_mask = res['turtle_soup_bull'] | res['turtle_soup_bear']
    leth = (res['is_lethargic'] & sig_mask).sum()
    total = sig_mask.sum()
    pct = f"{leth/total*100:.1f}%" if total > 0 else "N/A"
    print(f"  Window {w:>2} candles ({w*15:>3}min): {leth}/{total} lethargic ({pct})")
