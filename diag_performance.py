import pandas as pd
import numpy as np
import yfinance as yf
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import turtle_soup_signals, false_flag_signals

# Load Data
df_1d = yf.download('AUDUSD=X', start='2016-09-01', end='2016-10-01', interval='1d', progress=False)
df_15m = yf.download('AUDUSD=X', start='2016-09-01', end='2016-10-01', interval='15m', progress=False)

def clean_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
    else:
        df.index = df.index.tz_convert('America/New_York')
    return df

df_1d = clean_df(df_1d)
df_15m = clean_df(df_15m)

# 1. Daily OB & Retracements
d_swings = smc.swing_highs_lows_v4(df_1d)
daily_ob = smc.identify_order_block(df_1d, d_swings)
daily_ret = smc.retracements(df_1d, d_swings)

# 2. LTF (15M) Setup
liq_15m = smc.liquidity(df_15m)
rev_15m = smc.detect_reversals(df_15m, smc.swing_highs_lows_v4(df_15m))

# 3. Signals
ts_15m = turtle_soup_signals(df_15m, rev_15m, daily_ob, df_1d, liq_df=liq_15m, use_daily_ob_stop=True)
cons_15m = smc.consolidation(df_15m)
ff_15m = false_flag_signals(df_15m, ts_15m, cons_15m, daily_ret, df_1d)

# Combine for analysis
analysis = pd.concat([df_15m[['open', 'high', 'low', 'close']], ff_15m, ts_15m[['ts_target_near', 'ts_target_far']]], axis=1)
signals = analysis[analysis['false_bull_flag'] == True].copy()

results = []
for idx, row in signals.iterrows():
    entry_time = idx
    entry_price = row['trap_entry']
    stop_loss = row['trap_stop_loss']
    target = row['ts_target_near']  # Using near target for conservative win rate
    
    # We are going SHORT
    risk = stop_loss - entry_price
    reward = entry_price - target
    rr = reward / risk if risk > 0 else 0
    
    # Look forward
    future_df = analysis.loc[entry_time:]
    
    outcome = 'OPEN'
    exit_time = None
    exit_price = None
    
    for f_idx, f_row in future_df.iloc[1:].iterrows():
        # Did it hit stop loss?
        if f_row['high'] >= stop_loss:
            outcome = 'LOSS'
            exit_time = f_idx
            exit_price = stop_loss
            break
        # Did it hit target?
        elif f_row['low'] <= target:
            outcome = 'WIN'
            exit_time = f_idx
            exit_price = target
            break
            
    if outcome != 'OPEN':
        duration = exit_time - entry_time
        results.append({
            'Entry Time': entry_time,
            'Outcome': outcome,
            'Risk (Pips)': risk * 10000,
            'Reward (Pips)': reward * 10000,
            'R:R': rr,
            'Duration': duration
        })

results_df = pd.DataFrame(results)
if not results_df.empty:
    wins = results_df[results_df['Outcome'] == 'WIN']
    losses = results_df[results_df['Outcome'] == 'LOSS']
    
    win_rate = len(wins) / len(results_df) * 100
    avg_rr = results_df['R:R'].mean()
    avg_duration = results_df['Duration'].mean()
    
    print('\n--- PERFORMANCE METRICS (Targeting Nearest Liquidity) ---')
    print(f'Total Trades Evaluated: {len(results_df)}')
    print(f'Wins: {len(wins)} | Losses: {len(losses)}')
    print(f'Win Rate: {win_rate:.1f}%')
    print(f'Average Risk: {results_df["Risk (Pips)"].mean():.1f} pips')
    print(f'Average Reward: {results_df["Reward (Pips)"].mean():.1f} pips')
    print(f'Average R:R: {avg_rr:.2f}')
    print(f'Average Trade Duration: {avg_duration}')
    
    print('\n--- TRADE LOG ---')
    print(results_df.to_string())
else:
    print('No resolved trades found.')
