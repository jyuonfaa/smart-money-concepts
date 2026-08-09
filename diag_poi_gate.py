"""
Diagnostic: print exact htf_poi_top, htf_poi_btm, htf_bias at each signal timestamp.
No modifications — read-only diagnostic.
"""
import pandas as pd
import numpy as np
from smartmoneyconcepts.smc import smc

df_15m = pd.read_csv('tests/test_data/EURUSD/EURUSD_15M.csv')
df_15m.rename(columns={'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Tickvol': 'volume'}, inplace=True)
df_15m['date'] = pd.to_datetime(df_15m['date'], format='%Y.%m.%d %H:%M:%S')
df_15m.set_index('date', inplace=True)
eurusd = df_15m.loc['2022-10-10':'2022-11-10'].copy()

eurusd_1h = eurusd.resample('1h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
eurusd_daily = eurusd.resample('D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

raw_swings_1h = smc.swing_highs_lows(eurusd_1h, swing_length=5)
valid = raw_swings_1h[raw_swings_1h['HighLow'].notna()].copy()
swings_1h = pd.DataFrame({'ts': valid.index, 'type': valid['HighLow'].map({1: 'HIGH', -1: 'LOW'}), 'p': valid['Level']}).reset_index(drop=True)
patterns = smc.false_hns_patterns(eurusd_1h, swings_1h)
print(f"Patterns detected: {len(patterns)}")
print("Pattern trap_types:", patterns['trap_type'].tolist())
print()

daily_swings = smc.swing_highs_lows(eurusd_daily, swing_length=3)
obs = smc.ob(eurusd_daily, daily_swings)

# Print the raw OB series — direction and values
ob_rows = obs[obs['OB'].notna()]
print("=== RAW DAILY OB SERIES (all directions) ===")
for i, row in ob_rows.iterrows():
    direction = "BULLISH (+1)" if row['OB'] == 1.0 else "BEARISH (-1)"
    d = eurusd_daily.index[i] if isinstance(i, int) else i
    print(f"  {pd.Timestamp(d).date()}  {direction}  Top={row['Top']:.5f}  Bottom={row['Bottom']:.5f}")
print()

htf_bias    = pd.Series(0.0,    index=eurusd_1h.index)
htf_poi_top = pd.Series(np.nan, index=eurusd_1h.index)
htf_poi_btm = pd.Series(np.nan, index=eurusd_1h.index)
daily_bias = pd.Series(0.0, index=eurusd_daily.index)
daily_top  = pd.Series(np.nan, index=eurusd_daily.index)
daily_btm  = pd.Series(np.nan, index=eurusd_daily.index)

current_bias   = 0.0
active_ob_top  = None
active_ob_btm  = None
active_ob_idx  = 0
pending_bias   = 0.0
pending_ob_top = None
pending_ob_btm = None
pending_ob_idx = 0

for i in range(len(eurusd_daily)):
    idx   = eurusd_daily.index[i]
    high  = eurusd_daily['high'].iloc[i]
    low   = eurusd_daily['low'].iloc[i]
    close = eurusd_daily['close'].iloc[i]

    daily_bias.loc[idx] = current_bias
    daily_top.loc[idx]  = active_ob_top
    daily_btm.loc[idx]  = active_ob_btm

    ob_val = obs['OB'].iloc[i]
    if pd.notna(ob_val) and ob_val != 0:
        open_price = eurusd_daily['open'].iloc[i]
        if ob_val == 1.0:
            ob_t = high
            ob_b = open_price
        else:
            ob_t = open_price
            ob_b = low
        pending_bias    = ob_val
        pending_ob_top  = ob_t
        pending_ob_btm  = ob_b
        pending_ob_idx  = i

    if pending_bias == 1:
        if close > pending_ob_top:
            current_bias  = 1
            active_ob_top = pending_ob_top
            active_ob_btm = pending_ob_btm
            active_ob_idx = pending_ob_idx
            pending_bias  = 0
        elif close < pending_ob_btm:
            pending_bias = 0
    elif pending_bias == -1:
        if close < pending_ob_btm:
            current_bias  = -1
            active_ob_top = pending_ob_top
            active_ob_btm = pending_ob_btm
            active_ob_idx = pending_ob_idx
            pending_bias  = 0
        elif close > pending_ob_top:
            pending_bias = 0

    if current_bias == 1 and active_ob_btm is not None:
        if close < active_ob_btm:
            prior_high = eurusd_daily['high'].iloc[max(0, active_ob_idx-10):active_ob_idx].max() if active_ob_idx > 0 else np.inf
            rally_high = eurusd_daily['high'].iloc[active_ob_idx:i+1].max()
            if rally_high > prior_high:
                current_bias = -1
            else:
                active_ob_top = None; active_ob_btm = None; current_bias = 0.0
    elif current_bias == -1 and active_ob_top is not None:
        if close > active_ob_top:
            prior_low = eurusd_daily['low'].iloc[max(0, active_ob_idx-10):active_ob_idx].min() if active_ob_idx > 0 else -np.inf
            drop_low  = eurusd_daily['low'].iloc[active_ob_idx:i+1].min()
            if drop_low < prior_low:
                current_bias = 1
            else:
                active_ob_top = None; active_ob_btm = None; current_bias = 0.0

for idx in eurusd_1h.index:
    d = pd.Timestamp(idx.date())
    if d in daily_bias.index:
        htf_bias.loc[idx]    = daily_bias.loc[d]
        htf_poi_top.loc[idx] = daily_top.loc[d]
        htf_poi_btm.loc[idx] = daily_btm.loc[d]

signals = smc.hns_signals(eurusd_1h, patterns, htf_bias, htf_poi_top, htf_poi_btm)
buys  = signals[signals['signal'] == 1]
sells = signals[signals['signal'] == -1]

print("=== BUY SIGNALS ===")
for ts, row in buys.iterrows():
    poi_t = htf_poi_top.loc[ts]
    poi_b = htf_poi_btm.loc[ts]
    bias  = htf_bias.loc[ts]
    print(f"  Timestamp : {ts}")
    print(f"  Bias      : {bias} (1=bullish daily OB active, -1=bearish)")
    print(f"  htf_poi_top: {poi_t:.5f}")
    print(f"  htf_poi_btm: {poi_b:.5f}")
    print(f"  Bar low   : {eurusd_1h.loc[ts, 'low']:.5f}")
    print(f"  Trigger   : low({eurusd_1h.loc[ts, 'low']:.5f}) <= equal_lows AND poi_b({poi_b:.5f}) <= low <= poi_t({poi_t:.5f})")
    print()

print("=== SELL SIGNALS ===")
for ts, row in sells.iterrows():
    poi_t = htf_poi_top.loc[ts]
    poi_b = htf_poi_btm.loc[ts]
    bias  = htf_bias.loc[ts]
    print(f"  Timestamp : {ts}")
    print(f"  Bias      : {bias} (1=bullish daily OB active, -1=bearish)")
    print(f"  htf_poi_top: {poi_t:.5f}")
    print(f"  htf_poi_btm: {poi_b:.5f}")
    print(f"  Bar high  : {eurusd_1h.loc[ts, 'high']:.5f}")
    print(f"  Trigger   : high({eurusd_1h.loc[ts, 'high']:.5f}) >= equal_highs AND poi_b({poi_b:.5f}) <= high <= poi_t({poi_t:.5f})")
    print()

# Show daily_bias timeline around signal dates
print("=== DAILY BIAS TIMELINE (all days with non-zero bias) ===")
nonzero_days = daily_bias[daily_bias != 0]
for d, b in nonzero_days.items():
    direction = "BULLISH OB" if b == 1 else "BEARISH OB"
    t = daily_top.loc[d]
    bt = daily_btm.loc[d]
    t_str = f"{t:.5f}" if pd.notna(t) else "nan"
    bt_str = f"{bt:.5f}" if pd.notna(bt) else "nan"
    print(f"  {d.date()}  bias={b:+.0f} ({direction})  poi_top={t_str}  poi_btm={bt_str}")
