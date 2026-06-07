import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc

def resample_data(df, tf):
    """Resample OHLC data to higher timeframes."""
    resampled = df.resample(tf).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).dropna()
    return resampled

def draw_custom_ohlc(fig, df, row, col, name):
    """Draw candles using Scatter to avoid ghost range sliders."""
    fig.add_trace(go.Scatter(
        x=np.repeat(df.index, 3),
        y=np.column_stack((df['low'], df['high'], [None]*len(df))).flatten(),
        mode='lines', line=dict(color='gray', width=1), showlegend=False
    ), row=row, col=col)
    
    colors = ['lime' if c >= o else 'red' for o, c in zip(df['open'], df['close'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['close']-df['open'], base=df['open'],
        marker_color=colors, marker_line_width=0, name=name, showlegend=False
    ), row=row, col=col)

def run_video6_valuation():
    print("INITIALIZING VIDEO 6: DEFINITIVE INSTITUTIONAL VALUATION [EURUSD]")
    
    # 1. Load Data
    path = "tests/test_data/EURUSD/EURUSD_15M.csv"
    df_15m = pd.read_csv(path, parse_dates=['Date'], index_col=False)
    df_15m.columns = [c.lower() for c in df_15m.columns]
    df_15m.set_index('date', inplace=True)
    df_15m = df_15m.iloc[-1500:] 
    
    df_4h = resample_data(df_15m, '4h')
    df_daily = resample_data(df_15m, '1d')
    
    # 2. Institutional Scanners
    swings_4h = smc.swing_highs_lows_v4(df_4h)
    # voids_4h = smc.sequence_void(df_4h) # TODO: restore void rendering when smc.void_scanner confirmed
    obs_4h = smc.identify_order_block(df_4h, swings_4h)
    fvgs_4h = smc.fvg(df_4h)
    # bos_choch uses old 'HighLow' schema — derive MSB directly from swings_4h instead
    # A confirmed swing is itself a structural break (conf_ts marks the break candle)
    msb_4h_derived = swings_4h[['conf_ts', 'type']].copy()
    
    # 3. Setup Dashboard
    fig = make_subplots(rows=3, cols=1, shared_xaxes=False, 
                        vertical_spacing=0.08, 
                        subplot_titles=("Surgical Valuation (15M)", "Institutional Context (4H)", "Parent Range (Daily)"),
                        row_heights=[0.5, 0.25, 0.25])

    # PANE 1: 15M
    fig.add_trace(go.Candlestick(x=df_15m.index, open=df_15m['open'], high=df_15m['high'], low=df_15m['low'], close=df_15m['close'], name="15M"), row=1, col=1)
    
    parent_h, parent_l = df_daily['high'].max(), df_daily['low'].min()
    daily_range = parent_h - parent_l
    eq = (parent_h + parent_l) / 2
    prem_zone = parent_h - (daily_range / 3)
    
    # 4. Confluence Scorer with 24h Proximity Filter
    signals = []
    last_signal_ts = df_15m.index[0] - pd.Timedelta(days=1)
    
    for i in range(100, len(df_15m)):
        ts = df_15m.index[i]
        price = df_15m['close'].iloc[i]
        
        is_premium = price > prem_zone
        # v4h_active = voids_4h[voids_4h.index <= ts]
        # in_void = not v4h_active.empty and (v4h_active.iloc[-1]['bottom'] <= price <= v4h_active.iloc[-1]['top'])
        in_void = False
        fvg_4h_pos = df_4h.index.searchsorted(ts, side='right') - 1
        fvg_active = fvgs_4h.iloc[:fvg_4h_pos + 1].dropna(subset=['Top'])
        has_fvg_above = not fvg_active.empty and (fvg_active.iloc[-1]['Top'] > price)
        recent_msb = msb_4h_derived[(msb_4h_derived['conf_ts'] <= ts) & (msb_4h_derived['conf_ts'] > ts - pd.Timedelta(hours=168))]
        has_msb = not recent_msb.empty
        active_obs = obs_4h[obs_4h['ts'] <= ts]  # obs uses 'ts' column, not DatetimeIndex
        has_ob = not active_obs.empty and (abs(active_obs.iloc[-1]['low'] - price) < 0.0020)

        score = (1 if is_premium else 0) + (1 if in_void else 0) + (1 if has_fvg_above else 0) + (1 if has_msb else 0) + (1 if has_ob else 0)
        
        if score >= 4:
            if ts > last_signal_ts + pd.Timedelta(hours=24): # 24h Proximity Filter
                signals.append(dict(ts=ts, p=df_15m['high'].iloc[i], type="SELL", score=score))
                last_signal_ts = ts

    # Transpose 4H Voids
    # for start_ts, v in voids_4h.iterrows():
    #     fig.add_shape(type="rect", x0=start_ts, x1=v['end'], y0=v['bottom'], y1=v['top'],
    #                   fillcolor="orange", opacity=0.15, line_width=0, row=1, col=1)

    # For staggering annotations to avoid horizontal overlapping
    last_annot_ts = None
    ay_toggle = -50

    for s in signals[-3:]: # Rule of 3 (Distinct setups)
        score_val = s['score']
        label_text = f"SENIOR ({score_val}/5)"
        
        # Color mapping:
        # - SENIOR 5/5 = gold
        # - SENIOR 4/5 = muted style (dim gold or grey)
        if score_val == 5:
            bg_color = "gold"
            fg_color = "black"
        else:
            bg_color = "dimgray"
            fg_color = "white"
            
        # Stagger logic: if this signal is close to the previous one, change ay
        current_ay = -50
        if last_annot_ts is not None and (s['ts'] - last_annot_ts) < pd.Timedelta(hours=48):
            ay_toggle = -90 if ay_toggle == -50 else -50
            current_ay = ay_toggle
        last_annot_ts = s['ts']
            
        fig.add_annotation(x=s['ts'], y=s['p'], text=label_text, 
                           showarrow=True, arrowhead=2, bgcolor=bg_color, font=dict(color=fg_color),
                           ay=current_ay, row=1, col=1)

    # PANE 2: 4H (Hard Anchored Lines)
    draw_custom_ohlc(fig, df_4h, row=2, col=1, name="4H")
    x_end_4h = df_4h.index[-1]
    
    # for start_ts, v in voids_4h.iterrows():
    #     fig.add_shape(type="rect", x0=start_ts, x1=v['end'], y0=v['bottom'], y1=v['top'],
    #                   fillcolor="orange", opacity=0.25, line_width=0, row=2, col=1)
    #     ce = (v['bottom'] + v['top']) / 2
    #     fig.add_shape(type="line", x0=start_ts, x1=v['end'], y0=ce, y1=ce, 
    #                   line=dict(color="gold", width=1.5, dash="dot"), row=2, col=1)

    for _, o in obs_4h.dropna().iterrows():
        ob_fv = (o['high'] + o['low']) / 2
        start_ts = o['conf_ts']
        
        # Determine mitigation: find the first 4H candle after start_ts where price mitigates it (low < ob_fv)
        future_candles = df_4h[df_4h.index > start_ts]
        mitigating_candles = future_candles[future_candles['low'] < ob_fv]
        if not mitigating_candles.empty:
            end_ts = mitigating_candles.index[0]
        else:
            end_ts = x_end_4h
            
        fig.add_shape(type="line", x0=start_ts, x1=end_ts, y0=ob_fv, y1=ob_fv, 
                      line=dict(color="cyan", width=1.5, dash="dash"), row=2, col=1)

    # PANE 3: DAILY
    draw_custom_ohlc(fig, df_daily, row=3, col=1, name="Daily")
    fig.add_shape(type="line", x0=df_daily.index[0], x1=df_daily.index[-1], y0=eq, y1=eq, 
                  line=dict(color="white", width=2, dash="dash"), row=3, col=1)
    fig.add_shape(type="line", x0=df_daily.index[0], x1=df_daily.index[-1], y0=prem_zone, y1=prem_zone, 
                  line=dict(color="red", width=1, dash="dot"), row=3, col=1)
    disc_zone = parent_l + (daily_range / 3)
    fig.add_shape(type="line", x0=df_daily.index[0], x1=df_daily.index[-1], y0=disc_zone, y1=disc_zone, 
                  line=dict(color="lime", width=1, dash="dot"), row=3, col=1)

    fig.update_xaxes(rangeslider_visible=False)
    fig.update_layout(height=1200, template="plotly_dark", showlegend=False, 
                      title_text="ICT VIDEO 6: DEFINITIVE INSTITUTIONAL VALUATION [EURUSD]")
    
    fig.write_html("ICT_VIDEO_6_VALUATION_v2.html")
    print("DONE: ICT_VIDEO_6_VALUATION_v2.html generated.")

if __name__ == "__main__":
    run_video6_valuation()
