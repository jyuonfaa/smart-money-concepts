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

def run_audusd_validation():
    print("INITIALIZING AUDUSD FORENSIC AUDIT: SEPT 2016 [VIDEO 6]")
    
    path = "HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv"
    df_raw = pd.read_csv(path, sep=';', names=['date', 'open', 'high', 'low', 'close', 'volume'], index_col=False)
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
    df_raw.set_index('date', inplace=True)
    
    mask = (df_raw.index >= '2016-09-02') & (df_raw.index <= '2016-09-24')
    df_sept = df_raw.loc[mask].copy()
    
    df_15m = resample_data(df_sept, '15min')
    df_4h = resample_data(df_sept, '4h')
    df_daily = resample_data(df_sept, '1d')
    
    swings_4h = smc.swing_highs_lows_v4(df_4h)
    voids_4h = smc.sequence_void(df_4h)
    obs_4h = smc.identify_order_block(df_4h, swings_4h)
    fvgs_4h = smc.fvg(df_4h)
    bos_choch_4h = smc.bos_choch(df_4h, swings_4h)
    
    fig = make_subplots(rows=3, cols=1, shared_xaxes=False, 
                        vertical_spacing=0.08, 
                        subplot_titles=("Surgical Valuation (15M)", "Institutional Context (4H)", "Parent Range (Daily)"),
                        row_heights=[0.5, 0.25, 0.25])

    fig.add_trace(go.Candlestick(x=df_15m.index, open=df_15m['open'], high=df_15m['high'], low=df_15m['low'], close=df_15m['close'], name="15M"), row=1, col=1)
    
    parent_h, parent_l = df_daily['high'].max(), df_daily['low'].min()
    daily_range = parent_h - parent_l
    eq = (parent_h + parent_l) / 2
    disc_zone = parent_l + (daily_range / 3)
    
    for start_ts, v in voids_4h.iterrows():
        fig.add_shape(type="rect", x0=start_ts, x1=v['end'], y0=v['bottom'], y1=v['top'],
                      fillcolor="orange", opacity=0.15, line_width=0, row=1, col=1)

    signals = []
    last_signal_ts = df_15m.index[0] - pd.Timedelta(days=1)
    
    for i in range(50, len(df_15m)):
        ts = df_15m.index[i]
        price = df_15m['close'].iloc[i]
        is_discount = price < disc_zone
        v4h_active = voids_4h[voids_4h.index <= ts]
        in_void = not v4h_active.empty and (v4h_active.iloc[-1]['bottom'] <= price <= v4h_active.iloc[-1]['top'])
        msb_4h = bos_choch_4h[(bos_choch_4h.index <= ts) & (bos_choch_4h.index > ts - pd.Timedelta(hours=120))]
        has_msb = not msb_4h.empty
        ob_score = 1 if not obs_4h[obs_4h.index <= ts].empty else 0
        
        score = (1 if is_discount else 0) + (1 if in_void else 0) + (1 if has_msb else 0) + ob_score + 1
        if score >= 4:
            if ts > last_signal_ts + pd.Timedelta(hours=24):
                signals.append(dict(ts=ts, p=df_15m['low'].iloc[i], type="BUY", score=score))
                last_signal_ts = ts

    for s in signals[-3:]:
        fig.add_annotation(x=s['ts'], y=s['p'], text=f"SENIOR ({s['score']}/5)", 
                           showarrow=True, arrowhead=2, bgcolor="lime", font=dict(color="black"),
                           ay=50, row=1, col=1)

    draw_custom_ohlc(fig, df_4h, row=2, col=1, name="4H")
    x_end_4h = df_4h.index[-1]
    
    for start_ts, v in voids_4h.iterrows():
        fig.add_shape(type="rect", x0=start_ts, x1=v['end'], y0=v['bottom'], y1=v['top'],
                      fillcolor="orange", opacity=0.25, line_width=0, row=2, col=1)
        ce = (v['bottom'] + v['top']) / 2
        fig.add_shape(type="line", x0=start_ts, x1=v['end'], y0=ce, y1=ce, 
                      line=dict(color="gold", width=1.5, dash="dot"), row=2, col=1)

    for _, o in obs_4h.iterrows():
        fig.add_shape(type="line", x0=o['conf_ts'], x1=x_end_4h, y0=o['fv'], y1=o['fv'], 
                      line=dict(color="cyan", width=1.5, dash="dash"), row=2, col=1)

    draw_custom_ohlc(fig, df_daily, row=3, col=1, name="Daily")
    fig.add_shape(type="line", x0=df_daily.index[0], x1=df_daily.index[-1], y0=eq, y1=eq, 
                  line=dict(color="white", width=2, dash="dash"), row=3, col=1)
    prem_zone = parent_h - (daily_range / 3)
    fig.add_shape(type="line", x0=df_daily.index[0], x1=df_daily.index[-1], y0=prem_zone, y1=prem_zone, 
                  line=dict(color="red", width=1, dash="dot"), row=3, col=1)
    fig.add_shape(type="line", x0=df_daily.index[0], x1=df_daily.index[-1], y0=disc_zone, y1=disc_zone, 
                  line=dict(color="lime", width=1, dash="dot"), row=3, col=1)

    fig.update_xaxes(rangeslider_visible=False)
    fig.update_layout(height=1200, template="plotly_dark", showlegend=False, 
                      title_text="AUDUSD SEPT 2016: DEFINITIVE INSTITUTIONAL VALUATION")
    
    fig.write_html("AUDUSD_SEPT_2016_VALUATION.html")
    print("DONE: AUDUSD_SEPT_2016_VALUATION.html generated.")

if __name__ == "__main__":
    run_audusd_validation()
