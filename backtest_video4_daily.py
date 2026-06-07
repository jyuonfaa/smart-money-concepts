import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals
import time
import warnings
warnings.filterwarnings('ignore')

print('Loading data...')
t0 = time.time()
df_raw = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv', sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

# Timeframes
df_daily = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_weekly = df_raw.resample('1W').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_monthly = df_raw.resample('1ME').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

print(f'Data loaded in {time.time()-t0:.2f}s')

print('Calculating SMC indicators on Daily/Weekly/Monthly...')
# Calculate Swings and OBs for the higher timeframe (Weekly acting as "Daily")
weekly_swings = smc.swing_highs_lows(df_weekly, swing_length=5)
weekly_ob = smc.ob(df_weekly, weekly_swings)

# Calculate Daily elements (Acting as "LTF")
daily_swings = smc.swing_highs_lows(df_daily, swing_length=5)
daily_reversals = detect_reversals(df_daily, daily_swings)
daily_fvg = smc.fvg(df_daily)
monthly_ob = smc.monthly_range_ob(df_monthly)

def simulate_trades(sigs, df_ltf):
    # Prepare
    sigs['entry'] = sigs['ts_entry_price']
    sigs['stop'] = sigs['ts_ob_stop']
    sigs['target'] = np.where(sigs['ts_target_fvg'].notna(), sigs['ts_target_fvg'], sigs['ts_target_near'])
    sigs = sigs.dropna(subset=['entry', 'stop', 'target']).copy()
    
    # Best setups
    # Note: On the daily chart, power of 3 sponsor (ny_midnight) and lethargic check don't apply the same way,
    # so we will loosen the "prime setup" criteria for daily execution to just require the basic signal.
    prime_setups = sigs
    
    wins = 0
    losses = 0
    sweeps = 0
    total_sweep_depth = 0
    total_pips_won = 0
    total_pips_lost = 0

    for idx, row in prime_setups.iterrows():
        entry_idx = df_ltf.index.get_loc(idx)
        entry_price = row['entry']
        stop_price = row['stop']
        target_price = row['target']
        is_bull = row['turtle_soup_bull']
        
        risk_pips = abs(entry_price - stop_price) * 10000
        reward_pips_potential = abs(target_price - entry_price) * 10000
        
        outcome = "Pending"
        pips_realized = 0
        
        for i in range(entry_idx + 1, len(df_ltf)):
            future_bar = df_ltf.iloc[i]
            if is_bull:
                if future_bar['low'] <= stop_price:
                    outcome = "Loss"
                    pips_realized = -risk_pips
                    break
                elif future_bar['high'] >= target_price:
                    outcome = "Win"
                    pips_realized = reward_pips_potential
                    break
            else:
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
            max_adverse = stop_price
            # Scan next 20 days (approx 1 month) for target hit
            for j in range(i + 1, min(len(df_ltf), i + 21)):
                future_bar_sweep = df_ltf.iloc[j]
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
        elif outcome == "Loss":
            losses += 1
            total_pips_lost += abs(pips_realized)
            if sweep_and_go:
                sweeps += 1
                total_sweep_depth += sweep_depth_pips

    total_trades = wins + losses
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    net_pips = total_pips_won - total_pips_lost
    return total_trades, wins, losses, win_rate, net_pips, sweeps, total_sweep_depth

print('\nRunning engine Without Monthly OB Gate...')
res_unfiltered = turtle_soup_signals(
    ohlc=df_daily, reversals=daily_reversals, daily_ob=weekly_ob, daily_ohlc=df_weekly,
    ny_midnight=None, fvg_df=daily_fvg
)

print('Running engine With Monthly OB Gate...')
res_filtered = turtle_soup_signals(
    ohlc=df_daily, reversals=daily_reversals, daily_ob=weekly_ob, daily_ohlc=df_weekly,
    ny_midnight=None, fvg_df=daily_fvg, monthly_ob_df=monthly_ob
)

print('\n' + '='*80)
print(f'{"Month":<10} | {"Trades (No Gate)":<18} | {"Win% (No Gate)":<18} | {"Trades (Gated)":<16} | {"Win% (Gated)":<16}')
print('-'*80)

total_unfiltered_trades = 0
total_unfiltered_wins = 0
total_unfiltered_losses = 0
total_unfiltered_net = 0

total_filtered_trades = 0
total_filtered_wins = 0
total_filtered_losses = 0
total_filtered_net = 0
total_filtered_sweeps = 0
total_filtered_sweep_depth = 0

for month in range(1, 13):
    start_date = f'2016-{month:02d}-01'
    if month == 12:
        end_date = '2017-01-01'
    else:
        end_date = f'2016-{month+1:02d}-01'
        
    mask = (df_daily.index >= start_date) & (df_daily.index < end_date)
    
    sigs_unfilt = res_unfiltered[mask]
    sigs_unfilt = sigs_unfilt[sigs_unfilt['turtle_soup_bull'] | sigs_unfilt['turtle_soup_bear']]
    u_trades, u_wins, u_losses, u_wr, u_net, u_sweeps, u_sdepth = simulate_trades(sigs_unfilt, df_daily)
    
    sigs_filt = res_filtered[mask]
    sigs_filt = sigs_filt[(sigs_filt['turtle_soup_bull'] | sigs_filt['turtle_soup_bear']) & sigs_filt['monthly_ob_gated']]
    f_trades, f_wins, f_losses, f_wr, f_net, f_sweeps, f_sdepth = simulate_trades(sigs_filt, df_daily)

    total_unfiltered_trades += u_trades
    total_unfiltered_wins += u_wins
    total_unfiltered_losses += u_losses
    total_unfiltered_net += u_net
    
    total_filtered_trades += f_trades
    total_filtered_wins += f_wins
    total_filtered_losses += f_losses
    total_filtered_net += f_net
    total_filtered_sweeps += f_sweeps
    total_filtered_sweep_depth += f_sdepth
    
    print(f'{month:02d}/2016    | {u_trades:<18} | {u_wr:<17.1f}% | {f_trades:<16} | {f_wr:<15.1f}%')

print('-'*80)
unfilt_wr = (total_unfiltered_wins / total_unfiltered_trades * 100) if total_unfiltered_trades > 0 else 0
filt_wr = (total_filtered_wins / total_filtered_trades * 100) if total_filtered_trades > 0 else 0

print(f'TOTAL      | {total_unfiltered_trades:<18} | {unfilt_wr:<17.1f}% | {total_filtered_trades:<16} | {filt_wr:<15.1f}%')
print(f'NET PIPS   | {total_unfiltered_net:+.1f} pips{"":<10} |                  | {total_filtered_net:+.1f} pips')
print('='*80)

if total_filtered_losses > 0:
    sweep_rate = (total_filtered_sweeps / total_filtered_losses) * 100
    avg_sweep_depth = total_filtered_sweep_depth / total_filtered_sweeps if total_filtered_sweeps > 0 else 0
    print(f"\\n[SWEEP ANALYSIS ON GATED TRADES]")
    print(f"Of the {total_filtered_losses} losing trades, {total_filtered_sweeps} ({sweep_rate:.1f}%) eventually hit our original target.")
    print(f"Before reversing to target, price went against our stop by an average of: {avg_sweep_depth:.1f} pips.")
