import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals
import time

print('Loading data...')
df_raw = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv', sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)
df_daily_ri = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().reset_index()
df_15m = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

daily_swings = smc.swing_highs_lows(df_daily_ri, swing_length=5)
daily_ob = smc.ob(df_daily_ri, daily_swings)
ltf_swings = smc.swing_highs_lows(df_15m, swing_length=5)
reversals = detect_reversals(df_15m, ltf_swings)
midnight = smc.ny_midnight_open(df_15m)
fvg = smc.fvg(df_15m)

res = turtle_soup_signals(ohlc=df_15m, reversals=reversals, daily_ob=daily_ob, daily_ohlc=df_daily_ri, ny_midnight=midnight, fvg_df=fvg)

sigs = res[res['turtle_soup_bull'] | res['turtle_soup_bear']].copy()
sigs['entry'] = sigs['ts_entry_price']
sigs['stop'] = sigs['ts_ob_stop']
sigs['target'] = np.where(sigs['ts_target_fvg'].notna(), sigs['ts_target_fvg'], sigs['ts_target_near'])
sigs = sigs.dropna(subset=['entry', 'stop', 'target']).copy()
prime_setups = sigs[
    (sigs['power3_sponsored'] == True) &
    (sigs['down_candle_violated'] == True) &
    (sigs['is_lethargic'] == False)
]

print(f'\nAnalysing post-TP continuation for {len(prime_setups)} Prime Setups...')
print('='*65)

# POST_TP scan window: 80 bars = 20 hours
POST_TP_BARS = 80

results = []

for idx, row in prime_setups.iterrows():
    entry_idx = df_15m.index.get_loc(idx)
    entry_price = row['entry']
    stop_price  = row['stop']
    target_price = row['target']
    is_bull = row['turtle_soup_bull']

    risk_pips    = abs(entry_price - stop_price) * 10000
    tp_pips      = abs(target_price - entry_price) * 10000

    # ── Phase 1: scan until TP or SL ──────────────────────────────
    tp_hit_idx = None
    outcome = 'Pending'
    for i in range(entry_idx + 1, len(df_15m)):
        bar = df_15m.iloc[i]
        if is_bull:
            if bar['low'] <= stop_price:
                outcome = 'Loss'
                break
            if bar['high'] >= target_price:
                outcome = 'Win'
                tp_hit_idx = i
                break
        else:
            if bar['high'] >= stop_price:
                outcome = 'Loss'
                break
            if bar['low'] <= target_price:
                outcome = 'Win'
                tp_hit_idx = i
                break

    # ── For Losses: check if sweep-and-go eventually hits TP ──────
    if outcome == 'Loss':
        for j in range(i + 1, min(len(df_15m), i + 41)):
            bar = df_15m.iloc[j]
            if is_bull and bar['high'] >= target_price:
                tp_hit_idx = j
                break
            elif not is_bull and bar['low'] <= target_price:
                tp_hit_idx = j
                break

    # ── Phase 2: post-TP continuation ─────────────────────────────
    post_tp_extension = 0.0
    if tp_hit_idx is not None:
        best_price = target_price
        for k in range(tp_hit_idx + 1, min(len(df_15m), tp_hit_idx + POST_TP_BARS + 1)):
            bar = df_15m.iloc[k]
            if is_bull:
                if bar['high'] > best_price:
                    best_price = bar['high']
                else:
                    # stop tracking once price pulls back 50% of post-TP extension
                    pullback = (best_price - bar['low']) * 10000
                    extension = (best_price - target_price) * 10000
                    if pullback > extension * 0.5 and extension > 0:
                        break
            else:
                if bar['low'] < best_price:
                    best_price = bar['low']
                else:
                    pullback = (bar['high'] - best_price) * 10000
                    extension = (target_price - best_price) * 10000
                    if pullback > extension * 0.5 and extension > 0:
                        break

        post_tp_extension = abs(best_price - target_price) * 10000

    results.append({
        'date': idx.strftime('%Y-%m-%d %H:%M'),
        'direction': 'BULL' if is_bull else 'BEAR',
        'outcome': outcome,
        'tp_pips': round(tp_pips, 1),
        'tp_hit': tp_hit_idx is not None,
        'post_tp_ext': round(post_tp_extension, 1),
    })

df_r = pd.DataFrame(results)

# ── Summary ────────────────────────────────────────────────────────
wins   = df_r[df_r['outcome'] == 'Win']
losses = df_r[df_r['outcome'] == 'Loss']
losses_tp = losses[losses['tp_hit'] == True]
losses_no_tp = losses[losses['tp_hit'] == False]

print('\n--- WINNING TRADES (Hit TP without SL) ---')
for _, r in wins.iterrows():
    print(f"  {r['date']} | {r['direction']} | TP: {r['tp_pips']:.1f} pips | Post-TP Extension: +{r['post_tp_ext']:.1f} pips")
if len(wins) > 0:
    print(f"  >> Average post-TP extension (Wins): +{wins['post_tp_ext'].mean():.1f} pips")

print('\n--- LOSING TRADES (Stop Hit — but swept to TP) ---')
for _, r in losses_tp.iterrows():
    print(f"  {r['date']} | {r['direction']} | TP: {r['tp_pips']:.1f} pips | Post-TP Extension: +{r['post_tp_ext']:.1f} pips")
if len(losses_tp) > 0:
    print(f"  >> Average post-TP extension (Sweep & Go): +{losses_tp['post_tp_ext'].mean():.1f} pips")

if len(losses_no_tp) > 0:
    print(f'\n--- LOSSES that NEVER hit TP ({len(losses_no_tp)} trades) ---')
    for _, r in losses_no_tp.iterrows():
        print(f"  {r['date']} | {r['direction']} | Pure loss — price never reached TP within 10h")

print('\n--- OVERALL SUMMARY ---')
tp_hit_all = df_r[df_r['tp_hit'] == True]
print(f"Trades that eventually hit TP: {len(tp_hit_all)} of {len(df_r)}")
print(f"Average post-TP extension (ALL that hit TP): +{tp_hit_all['post_tp_ext'].mean():.1f} pips")
print(f"Max post-TP extension seen: +{tp_hit_all['post_tp_ext'].max():.1f} pips")
print(f"Min post-TP extension seen: +{tp_hit_all['post_tp_ext'].min():.1f} pips")
