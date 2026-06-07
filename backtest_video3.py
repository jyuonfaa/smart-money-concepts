import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals
import time

print('Loading data...')
t0 = time.time()
df_raw = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv', sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

# Resample to Daily and 15M
df_daily_ri = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().reset_index()
df_15m = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
print(f'Data loaded in {time.time()-t0:.2f}s')

print('Calculating SMC indicators...')
daily_swings = smc.swing_highs_lows(df_daily_ri, swing_length=5)
daily_ob = smc.ob(df_daily_ri, daily_swings)
ltf_swings = smc.swing_highs_lows(df_15m, swing_length=5)
reversals = detect_reversals(df_15m, ltf_swings)
midnight = smc.ny_midnight_open(df_15m)
fvg = smc.fvg(df_15m)
london = smc.sessions(df_15m, session='London').iloc[:, 0]
ny = smc.sessions(df_15m, session='New York').iloc[:, 0]
sessions = london | ny
ltf_obs = smc.ob(df_15m, ltf_swings)
session_obs = smc.session_order_blocks(df_15m, ltf_obs, sessions)

print('Running signal engine...')
t1 = time.time()
res = turtle_soup_signals(
    ohlc=df_15m, reversals=reversals, daily_ob=daily_ob, daily_ohlc=df_daily_ri,
    ny_midnight=midnight, fvg_df=fvg # removed ltf_session_obs and max_session_ob_age_days for diagnostic
)
print(f'Engine finished in {time.time()-t1:.2f}s')

sigs = res[res['turtle_soup_bull'] | res['turtle_soup_bear']].copy()

# Simple Simulation Metrics
sigs['entry'] = sigs['ts_entry_price']
sigs['stop'] = sigs['ts_ob_stop']
# Prefer FVG target, fallback to near liquidity target
sigs['target'] = np.where(sigs['ts_target_fvg'].notna(), sigs['ts_target_fvg'], sigs['ts_target_near'])

# Drop signals without a valid target or stop
sigs = sigs.dropna(subset=['entry', 'stop', 'target']).copy()

# Risk Reward
sigs['risk'] = abs(sigs['entry'] - sigs['stop'])
sigs['reward'] = abs(sigs['target'] - sigs['entry'])
sigs['RR'] = sigs['reward'] / sigs['risk']

# Filtering
all_count = len(sigs)
# Best setups: Power3 Sponsored + Down Candle Violated + Not Lethargic
prime_setups = sigs[
    (sigs['power3_sponsored'] == True) & 
    (sigs['down_candle_violated'] == True) & 
    (sigs['is_lethargic'] == False)
]

print('\n=== BACKTEST RESULTS (AUDUSD 2016) ===')
print(f"Total Raw Signals: {len(res[res['turtle_soup_bull'] | res['turtle_soup_bear']])}")
print(f"Signals w/ Targets & Stops: {all_count}")
print(f"Avg R:R (All): {sigs['RR'].mean():.2f}")

# True Trade Simulation for Prime Setups
wins = 0
losses = 0
sweeps = 0
total_sweep_depth = 0
total_duration_mins = 0
total_pips_won = 0
total_pips_lost = 0
total_rr_achieved = 0
total_mae_wins = 0

print('\n--- Prime Setups True Simulation ---')
for idx, row in prime_setups.iterrows():
    entry_idx = df_15m.index.get_loc(idx)
    entry_price = row['entry']
    stop_price = row['stop']
    target_price = row['target']
    is_bull = row['turtle_soup_bull']
    
    # Calculate Risk in pips
    risk_pips = abs(entry_price - stop_price) * 10000
    reward_pips_potential = abs(target_price - entry_price) * 10000
    
    trade_active = True
    outcome = "Pending"
    duration_bars = 0
    pips_realized = 0
    mae = entry_price # Track max adverse excursion
    
    # Forward scan from the entry bar onwards
    for i in range(entry_idx + 1, len(df_15m)):
        duration_bars += 1
        future_bar = df_15m.iloc[i]
        
        if is_bull:
            mae = min(mae, future_bar['low'])
            if future_bar['low'] <= stop_price:
                outcome = "Loss"
                pips_realized = -risk_pips
                break
            elif future_bar['high'] >= target_price:
                outcome = "Win"
                pips_realized = reward_pips_potential
                break
        else: # Bearish
            mae = max(mae, future_bar['high'])
            if future_bar['high'] >= stop_price:
                outcome = "Loss"
                pips_realized = -risk_pips
                break
            elif future_bar['low'] <= target_price:
                outcome = "Win"
                pips_realized = reward_pips_potential
                break
                
    sweep_and_go = False
    sweep_depth_pips = 0
    if outcome == "Loss":
        # Check the next 40 bars (10 hours) to see if it eventually hit the target
        max_adverse = stop_price
        for j in range(i + 1, min(len(df_15m), i + 41)):
            future_bar_sweep = df_15m.iloc[j]
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
                
    if outcome == "Win":
        wins += 1
        total_pips_won += pips_realized
        total_rr_achieved += (pips_realized / risk_pips)
        mae_pips = abs(mae - entry_price) * 10000
        total_mae_wins += mae_pips
    elif outcome == "Loss":
        losses += 1
        total_pips_lost += abs(pips_realized)
        total_rr_achieved -= 1
        if sweep_and_go:
            sweeps += 1
            total_sweep_depth += sweep_depth_pips
        
    total_duration_mins += (duration_bars * 15)

total_trades = wins + losses
if total_trades > 0:
    win_rate = (wins / total_trades) * 100
    loss_rate = (losses / total_trades) * 100
    avg_duration = total_duration_mins / total_trades
    avg_pips = (total_pips_won - total_pips_lost) / total_trades
    avg_rr = total_rr_achieved / total_trades
    
    avg_pips_won = total_pips_won / wins if wins > 0 else 0
    avg_pips_lost = total_pips_lost / losses if losses > 0 else 0
    avg_mae_wins = total_mae_wins / wins if wins > 0 else 0
    
    print(f"Total Completed Trades: {total_trades}")
    print(f"Wins: {wins} ({win_rate:.1f}%)")
    print(f"Losses: {losses} ({loss_rate:.1f}%)")
    print(f"Average Pips Gained (on Wins): +{avg_pips_won:.1f} pips")
    print(f"Average Pips Lost (on Losses): -{avg_pips_lost:.1f} pips")
    print(f"Average Drawdown on Winning Trades: {avg_mae_wins:.1f} pips")
    if sweeps > 0:
        avg_sweep_depth = total_sweep_depth / sweeps
        print(f"  -> Of the {losses} losses, {sweeps} were sweeps (hit stop then hit target within 10 hours)")
        print(f"  -> Average draw down beyond stop before reversal: {avg_sweep_depth:.1f} pips")
    print(f"Average Duration: {avg_duration / 60:.1f} hours ({avg_duration:.0f} mins)")
else:
    print("No trades completed.")
