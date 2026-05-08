import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc

def forensic_btc_audit():
    symbol = "BTC-USD"
    print(f"BTC FORENSIC AUDIT STARTING...")
    
    # 1. Fetch
    df_1d = yf.download(symbol, period="1y", interval="1d", progress=False)
    df_15m = yf.download(symbol, period="7d", interval="15m", progress=False)
    
    def clean_df(df):
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        if df.index.tz is None: df.index = df.index.tz_localize("UTC").tz_convert("America/New_York")
        else: df.index = df.index.tz_convert("America/New_York")
        return df

    df_1d, df_15m = clean_df(df_1d), clean_df(df_15m)

    # 2. Daily Anchors (OTE)
    d_swings = smc.swing_highs_lows_v4(df_1d)
    active_otes = []
    for i in range(1, len(d_swings)):
        p1, p5 = d_swings.iloc[i-1], d_swings.iloc[i]
        mode = 'BULLISH' if p1['type'] == 'LOW' else 'BEARISH'
        r = abs(p5['p'] - p1['p'])
        o62 = p5['p'] - 0.62*r if mode == 'BULLISH' else p5['p'] + 0.62*r
        o79 = p5['p'] - 0.79*r if mode == 'BULLISH' else p5['p'] + 0.79*r
        active_otes.append({'62': o62, '79': o79, 'mode': mode, 'conf_ts': p5['conf_ts'], 'label': f"D1 OTE [{p5['ts'].strftime('%b %d')}]"})

    display_otes = sorted(active_otes, key=lambda x: x['conf_ts'], reverse=True)[:3]

    # 3. 15M Surgical Signals (Senior Logic)
    m15_swings = smc.swing_highs_lows_v4(df_15m)
    candidates = []
    zone_cooldowns = {}
    
    for _, row in m15_swings.iterrows():
        for i, ote in enumerate(display_otes):
            if min(ote['62'], ote['79']) <= row['p'] <= max(ote['62'], ote['79']):
                cooldown_key = (i, row['type'])
                if cooldown_key in zone_cooldowns:
                    if row['ts'] - zone_cooldowns[cooldown_key] < pd.Timedelta(hours=2):
                        continue
                candidates.append((row['ts'], row['p'], row['type'], i))
                zone_cooldowns[cooldown_key] = row['ts']
                break

    candidates.sort(key=lambda x: x[0])
    last_type = None
    final_signals = []
    for c in candidates:
        if c[2] != last_type:
            final_signals.append(c)
            last_type = c[2]

    # 4. Output Log
    print("\n" + "="*50)
    print("BTC INSTITUTIONAL AUDIT LOG")
    print(f"{'TIMESTAMP':<20} | {'TYPE':<5} | {'PRICE':<8}")
    print("-" * 40)
    for ts, p, t, z in final_signals:
        print(f"{ts.strftime('%Y-%m-%d %H:%M'):<20} | {t:<5} | {p:<8.2f}")
    print("="*50 + "\n")

    # 5. Visual Proof
    fig = make_subplots(rows=2, cols=1, subplot_titles=("BTC Daily", "BTC 15M Surgical"))
    fig.add_trace(go.Candlestick(x=df_1d.index, open=df_1d['open'], high=df_1d['high'], low=df_1d['low'], close=df_1d['close']), row=1, col=1)
    fig.add_trace(go.Candlestick(x=df_15m.index, open=df_15m['open'], high=df_15m['high'], low=df_15m['low'], close=df_15m['close']), row=2, col=1)
    
    for ote in display_otes:
        color = "rgba(0, 255, 0, 0.1)" if ote['mode'] == 'BULLISH' else "rgba(255, 0, 0, 0.1)"
        start_ts = max(ote['conf_ts'], df_15m.index[0])
        fig.add_shape(type="rect", x0=start_ts, x1=df_15m.index[-1], y0=ote['79'], y1=ote['62'], fillcolor=color, row=2, col=1)

    for ts, p, t, z in final_signals:
        c = "Green" if t == "LOW" else "Red"
        fig.add_annotation(x=ts, y=p, text=t, showarrow=True, arrowhead=2, font=dict(color=c), row=2, col=1)

    fig.update_layout(height=1000, template="plotly_dark", title="BTC-USD FORENSIC STRESS TEST", showlegend=False)
    fig.write_html("BTC_FORENSIC_AUDIT.html")
    print(f"[SUCCESS] BTC Audit Complete: BTC_FORENSIC_AUDIT.html")

if __name__ == "__main__":
    forensic_btc_audit()
