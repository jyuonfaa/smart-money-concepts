import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, institutional_cascade_signals
import time
import warnings
warnings.filterwarnings('ignore')

print('Loading data...')
t0 = time.time()
df_raw = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv', sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

# Timeframes
df_4h = df_raw.resample('4h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_daily = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_weekly = df_raw.resample('1W').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_monthly = df_raw.resample('1ME').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

print(f'Data loaded in {time.time()-t0:.2f}s')

print('Calculating SMC indicators on all 4 Tiers...')
monthly_ob = smc.monthly_range_ob(df_monthly)

weekly_swings = smc.swing_highs_lows(df_weekly, swing_length=5)
weekly_ob = smc.ob(df_weekly, weekly_swings)

daily_swings = smc.swing_highs_lows(df_daily, swing_length=5)
daily_ob = smc.ob(df_daily, daily_swings)

ltf_swings = smc.swing_highs_lows(df_4h, swing_length=5)
ltf_reversals = detect_reversals(df_4h, ltf_swings)
ltf_fvg = smc.fvg(df_4h)

print('Running 4-Tier Institutional Cascade Engine...')
res = institutional_cascade_signals(
    ohlc_ltf=df_4h,
    reversals_ltf=ltf_reversals,
    daily_ob=daily_ob,
    daily_ohlc=df_daily,
    weekly_ob=weekly_ob,
    weekly_ohlc=df_weekly,
    monthly_ob_df=monthly_ob,
    fvg_df=ltf_fvg
)

sigs = res[res['turtle_soup_bull'] | res['turtle_soup_bear']].copy()

print(f"\n[RESULTS] 4-Tier Cascade Setup Count (4H Execution): {len(sigs)}")

# Quick simulation to see performance
if len(sigs) > 0:
    wins = 0
    losses = 0
    sweeps = 0
    total_sweep_depth = 0
    
    sigs['entry'] = sigs['ts_entry_price']
    sigs['stop'] = sigs['ts_ob_stop']
    # Use Macro Target (ts_target_near), fallback to FVG if missing
    sigs['target'] = np.where(sigs['ts_target_near'].notna(), sigs['ts_target_near'], sigs['ts_target_fvg'])
    sigs = sigs.dropna(subset=['entry', 'stop', 'target']).copy()
    
    for idx, row in sigs.iterrows():
        entry_idx = df_4h.index.get_loc(idx)
        entry_price = row['entry']
        stop_price = row['stop']
        target_price = row['target']
        is_bull = row['turtle_soup_bull']
        
        outcome = "Pending"
        
        for i in range(entry_idx + 1, len(df_4h)):
            future_bar = df_4h.iloc[i]
            if is_bull:
                if future_bar['low'] <= stop_price:
                    outcome = "Loss"
                    break
                elif future_bar['high'] >= target_price:
                    outcome = "Win"
                    break
            else:
                if future_bar['high'] >= stop_price:
                    outcome = "Loss"
                    break
                elif future_bar['low'] <= target_price:
                    outcome = "Win"
                    break
                    
        sweep_and_go = False
        sweep_depth_pips = 0
        if outcome == "Loss":
            max_adverse = stop_price
            for j in range(i + 1, min(len(df_4h), i + 240)): # 40 days
                future_bar_sweep = df_4h.iloc[j]
                if is_bull:
                    max_adverse = min(max_adverse, future_bar_sweep['low'])
                    if future_bar_sweep['high'] >= target_price:
                        sweep_and_go = True
                        sweep_depth_pips = (stop_price - max_adverse) * 10000
                        break
                else:
                    max_adverse = max(max_adverse, future_bar_sweep['high'])
                    if future_bar_sweep['low'] <= target_price:
                        sweep_and_go = True
                        sweep_depth_pips = (max_adverse - stop_price) * 10000
                        break
                        
        if outcome == "Win": wins += 1
        elif outcome == "Loss":
            losses += 1
            if sweep_and_go:
                sweeps += 1
                total_sweep_depth += sweep_depth_pips
                
    total = wins + losses
    print(f"Total Completed Trades: {total}")
    if total > 0:
        print(f"Win Rate: {(wins/total)*100:.1f}%")
        if losses > 0:
            print(f"Sweep Rate (Losses that later hit target): {(sweeps/losses)*100:.1f}%")
            if sweeps > 0:
                print(f"Average Sweep Depth (Adverse Excursion): {total_sweep_depth/sweeps:.1f} pips")
