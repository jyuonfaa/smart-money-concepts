import pandas as pd
import plotly.graph_objects as go
from smartmoneyconcepts.smc import smc
import numpy as np

def run_multi_tf_verification():
    print("=== Multi-Timeframe Month 3 Video 8 Verification ===")
    
    # Load EURUSD 15M data
    print("Loading 15M data...")
    # Skip rows to make execution faster if needed, but let's just load it
    df_15m = pd.read_csv('tests/test_data/EURUSD/EURUSD_15M.csv')
    df_15m.rename(columns={'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Tickvol': 'volume'}, inplace=True)
    df_15m['date'] = pd.to_datetime(df_15m['date'], format='%Y.%m.%d %H:%M:%S')
    df_15m.set_index('date', inplace=True)
    
    # Let's take just a 1-month slice to keep it fast and visualizations clean
    eurusd = df_15m.loc['2022-10-10':'2022-11-10'].copy()
    
    # Resample to 1H - ICT uses 1H as the signal/pattern chart (page 256: "let's take a look at an hourly chart")
    eurusd_1h = eurusd.resample('1h').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

    # Calculate swings on 1H (ICT signal chart)
    # smc.swing_highs_lows returns HighLow/Level columns; _false_hns_patterns needs type/p/ts
    print("Calculating 1H swings...")
    raw_swings_1h = smc.swing_highs_lows(eurusd_1h, swing_length=5)

    # Adapt format: convert HighLow (+1/-1) → type ('HIGH'/'LOW'), Level → p, index → ts
    valid = raw_swings_1h[raw_swings_1h['HighLow'].notna()].copy()
    swings_1h = pd.DataFrame({
        'ts':   valid.index,
        'type': valid['HighLow'].map({1: 'HIGH', -1: 'LOW'}),
        'p':    valid['Level'],
    }).reset_index(drop=True)

    # Detect False H&S Patterns on 1H
    print("Detecting patterns on 1H (ICT signal chart)...")
    patterns = smc.false_hns_patterns(eurusd_1h, swings_1h)

    
    print(f"Detected {len(patterns)} total False H&S patterns")
    
    # Resample to Daily to get HTF Orderblocks
    print("Resampling to Daily for HTF bias...")
    eurusd_daily = eurusd.resample('D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    # Get HTF Swings with appropriate swing_length for the data window
    # swing_length=3 works for a ~30 day daily window; larger windows need bigger values
    daily_swings = smc.swing_highs_lows(eurusd_daily, swing_length=3)
    obs  = smc.ob(eurusd_daily, daily_swings)
    fvgs = smc.fvg(eurusd_daily)

    htf_bias    = pd.Series(0.0,    index=eurusd_1h.index)
    htf_poi_top = pd.Series(np.nan, index=eurusd_1h.index)
    htf_poi_btm = pd.Series(np.nan, index=eurusd_1h.index)
    
    daily_bias = pd.Series(0.0, index=eurusd_daily.index)
    daily_top = pd.Series(np.nan, index=eurusd_daily.index)
    daily_btm = pd.Series(np.nan, index=eurusd_daily.index)
    
    current_bias  = 0.0
    active_ob_top = None
    active_ob_btm = None
    active_ob_idx = 0
    
    pending_bias  = 0.0
    pending_ob_top = None
    pending_ob_btm = None
    pending_ob_idx = 0

    for i in range(len(eurusd_daily)):
        idx   = eurusd_daily.index[i]
        high  = eurusd_daily['high'].iloc[i]
        low   = eurusd_daily['low'].iloc[i]
        close = eurusd_daily['close'].iloc[i]

        # 1. Record the state for TODAY before evaluating today's price action (Zero Lookahead)
        daily_bias.loc[idx] = current_bias
        daily_top.loc[idx] = active_ob_top
        daily_btm.loc[idx] = active_ob_btm

        # 2. Check if an OB formed today (it is marked retroactively by the SMC indicator, so we put it in Pending state)
        ob_val = obs['OB'].iloc[i]
        if pd.notna(ob_val) and ob_val != 0:
            open_price = eurusd_daily['open'].iloc[i]
            if ob_val == 1.0:
                ob_t = high
                ob_b = open_price
            else:
                ob_t = open_price
                ob_b = low

            pending_bias = ob_val
            pending_ob_top = ob_t
            pending_ob_btm = ob_b
            pending_ob_idx = i
                
        # 3. Check if a Pending OB gets confirmed today by the close
        if pending_bias == 1:
            if close > pending_ob_top:
                current_bias = 1
                active_ob_top = pending_ob_top
                active_ob_btm = pending_ob_btm
                active_ob_idx = pending_ob_idx
                pending_bias = 0
            elif close < pending_ob_btm:
                pending_bias = 0
        elif pending_bias == -1:
            if close < pending_ob_btm:
                current_bias = -1
                active_ob_top = pending_ob_top
                active_ob_btm = pending_ob_btm
                active_ob_idx = pending_ob_idx
                pending_bias = 0
            elif close > pending_ob_top:
                pending_bias = 0

        # 4. Check for Breaker flip on ACTIVE OBs
        if current_bias == 1 and active_ob_btm is not None:
            if close < active_ob_btm:
                prior_high = eurusd_daily['high'].iloc[max(0, active_ob_idx-10):active_ob_idx].max() if active_ob_idx > 0 else np.inf
                rally_high = eurusd_daily['high'].iloc[active_ob_idx:i+1].max()
                
                if rally_high > prior_high:
                    current_bias = -1  # Valid Bearish Breaker
                else:
                    active_ob_top = None
                    active_ob_btm = None
                    current_bias = 0.0
        elif current_bias == -1 and active_ob_top is not None:
            if close > active_ob_top:
                prior_low = eurusd_daily['low'].iloc[max(0, active_ob_idx-10):active_ob_idx].min() if active_ob_idx > 0 else -np.inf
                drop_low = eurusd_daily['low'].iloc[active_ob_idx:i+1].min()
                
                if drop_low < prior_low:
                    current_bias = 1   # Valid Bullish Breaker
                else:
                    active_ob_top = None
                    active_ob_btm = None
                    current_bias = 0.0

    # Map the daily bias onto the 1H dataframe (Gap 1: 1H is the signal chart)
    for idx in eurusd_1h.index:
        d = pd.Timestamp(idx.date())
        if d in daily_bias.index:
            htf_bias.loc[idx] = daily_bias.loc[d]
            htf_poi_top.loc[idx] = daily_top.loc[d]
            htf_poi_btm.loc[idx] = daily_btm.loc[d]

    print("Executing bar-by-bar sweeps on 1H...")
    signals = smc.hns_signals(eurusd_1h, patterns, htf_bias, htf_poi_top, htf_poi_btm)
    
    buys = signals[signals['signal'] == 1]
    sells = signals[signals['signal'] == -1]

    print(f"Total executions fired: {len(buys) + len(sells)}")
    print(f"  - {len(buys)} Buys  (Equal-Lows Turtle Soup inside Bullish Daily POI)")
    print(f"  - {len(sells)} Sells (Equal-Highs Turtle Soup inside Bearish Daily POI)")

    # ── Visualization ────────────────────────────────────────────────────────
    print("Generating Visualization...")
    fig = go.Figure()

    # ── Helper: convert any timestamp to ISO string (required for add_shape with xref='x') ──
    def ts_str(t):
        return pd.Timestamp(t).isoformat()

    x_min = ts_str(eurusd_1h.index[0])
    x_max = ts_str(eurusd_1h.index[-1])

    fig.add_trace(go.Candlestick(
        x=eurusd_1h.index,
        open=eurusd_1h['open'], high=eurusd_1h['high'],
        low=eurusd_1h['low'],  close=eurusd_1h['close'],
        name='EURUSD 1H',
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    ))

    # 2. Gap 3: Daily POI zones as shaded rectangles
    # Collect contiguous POI windows
    poi_segments = []
    prev_t, prev_b, prev_bias, seg_start = None, None, None, None
    for idx in eurusd_1h.index:
        t  = htf_poi_top.loc[idx] if idx in htf_poi_top.index else np.nan
        b  = htf_poi_btm.loc[idx] if idx in htf_poi_btm.index else np.nan
        bias = htf_bias.loc[idx]  if idx in htf_bias.index  else 0
        if pd.notna(t) and pd.notna(b):
            if t != prev_t or b != prev_b:
                if seg_start is not None:
                    poi_segments.append((seg_start, idx, prev_t, prev_b, prev_bias))
                seg_start = idx
                prev_t, prev_b, prev_bias = t, b, bias
        else:
            if seg_start is not None:
                poi_segments.append((seg_start, idx, prev_t, prev_b, prev_bias))
                seg_start = None
                prev_t, prev_b, prev_bias = None, None, None
    if seg_start is not None:
        poi_segments.append((seg_start, eurusd_1h.index[-1], prev_t, prev_b, prev_bias))

    for (x0, x1, yt, yb, bias) in poi_segments:
        fill = 'rgba(0,210,110,0.18)' if bias == 1 else 'rgba(220,50,50,0.18)'
        edge = 'rgba(0,210,110,0.7)'  if bias == 1 else 'rgba(220,50,50,0.7)'
        # Use add_trace with fill='toself' for rectangles to avoid shape bugs on date axes
        fig.add_trace(go.Scatter(
            x=[x0, x1, x1, x0, x0],
            y=[yb, yb, yt, yt, yb],
            fill='toself',
            fillcolor=fill,
            line=dict(color=edge, width=1.5),
            mode='lines',
            showlegend=False,
            hoverinfo='skip'
        ))

    # 3. 1H Swing markers
    highs_1h = swings_1h[swings_1h['type'] == 'HIGH']
    lows_1h  = swings_1h[swings_1h['type'] == 'LOW']
    fig.add_trace(go.Scatter(
        x=highs_1h['ts'], y=highs_1h['p'], mode='markers',
        marker=dict(color='lime', symbol='triangle-down', size=8), name='1H Highs'
    ))
    fig.add_trace(go.Scatter(
        x=lows_1h['ts'], y=lows_1h['p'], mode='markers',
        marker=dict(color='tomato', symbol='triangle-up', size=8), name='1H Lows'
    ))

    # 4. Equal-Lows / Equal-Highs horizontal neckline (the liquidity level retail is watching)
    all_execs = pd.concat([buys, sells]) if (not buys.empty or not sells.empty) else pd.DataFrame()
    for exec_ts, row in all_execs.iterrows():
        t1_val = row.get('t1')
        p1_val = row.get('p1')
        p2_val = row.get('p2')
        if pd.isna(t1_val) or pd.isna(p1_val):
            continue
        level = min(float(p1_val), float(p2_val)) if row['signal'] == 1 else max(float(p1_val), float(p2_val))
        color = '#00e5ff' if row['signal'] == 1 else '#ff9800'
        fig.add_trace(go.Scatter(
            x=[t1_val, exec_ts], y=[level, level],
            mode='lines', line=dict(color=color, width=2, dash='dot'),
            showlegend=False, hoverinfo='skip'
        ))


    # ── 5. BUY executions ───────────────────────────────────────────────────
    if not buys.empty:
        fig.add_trace(go.Scatter(
            x=buys.index,
            y=eurusd_1h.loc[buys.index, 'low'] * 0.9998,
            mode='markers',
            marker=dict(color='cyan', symbol='triangle-up', size=16,
                        line=dict(width=2, color='white')),
            hovertext=buys['trigger_type'],
            name='BUY — Turtle Soup'
        ))
        for idx, row in buys.iterrows():
            t1_p, t2_p = row['target_1'], row['target_2']
            x_end = eurusd_1h.index[-1]
            if pd.notna(t1_p):
                fig.add_trace(go.Scatter(
                    x=[idx, x_end], y=[t1_p, t1_p],
                    mode='lines', line=dict(color='cyan', width=1, dash='dot'), showlegend=False
                ))
            if pd.notna(t2_p):
                fig.add_trace(go.Scatter(
                    x=[idx, x_end], y=[t2_p, t2_p],
                    mode='lines', line=dict(color='cyan', width=2, dash='dash'), showlegend=False
                ))

    # 6. SELL executions (Turtle Soup)
    if not sells.empty:
        fig.add_trace(go.Scatter(
            x=sells.index,
            y=eurusd_1h.loc[sells.index, 'high'] * 1.0002,
            mode='markers',
            marker=dict(color='magenta', symbol='triangle-down', size=16,
                        line=dict(width=2, color='white')),
            hovertext=sells['trigger_type'],
            name='SELL — Turtle Soup'
        ))
        for idx, row in sells.iterrows():
            t1_p, t2_p = row['target_1'], row['target_2']
            x_end = eurusd_1h.index[-1]
            if pd.notna(t1_p):
                fig.add_trace(go.Scatter(
                    x=[idx, x_end], y=[t1_p, t1_p],
                    mode='lines', line=dict(color='magenta', width=1, dash='dot'), showlegend=False
                ))
            if pd.notna(t2_p):
                fig.add_trace(go.Scatter(
                    x=[idx, x_end], y=[t2_p, t2_p],
                    mode='lines', line=dict(color='magenta', width=2, dash='dash'), showlegend=False
                ))

    fig.update_layout(
        title='ICT Month 3 Video 8 — Market Maker Trap | 1H Signal Chart | Daily POI Zones',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        template='plotly_dark',
        height=860,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis=dict(range=[eurusd_1h.index[0], eurusd_1h.index[-1]])
    )

    fig.write_html('visualize_video8.html')
    print("Saved visualization to visualize_video8.html")

if __name__ == '__main__':
    run_multi_tf_verification()

