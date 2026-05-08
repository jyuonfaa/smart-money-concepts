"""
ICT Master Audit: VIDEOS 1-4 INTEGRATED
Asset: GOLD (GC=F)
Time (V1&2) | Footprints (V3) | OTE Gating (V4)
"""
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc
import uuid

def run_gold_master_audit():
    symbol = "GC=F"
    uid = str(uuid.uuid4())[:8]
    output_name = f"ICT_GOLD_MASTER_{uid}.html"

    print(f"Generating GOLD MASTER AUDIT (Videos 1-4) [{uid}]...")
    df_1d  = yf.download(symbol, period="1y", interval="1d", progress=False)
    df_15m = yf.download(symbol, period="7d", interval="15m", progress=False)

    def clean_df(df):
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        if df.index.tz is None: df.index = df.index.tz_localize("UTC").tz_convert("America/New_York")
        else: df.index = df.index.tz_convert("America/New_York")
        return df

    df_1d, df_15m = clean_df(df_1d), clean_df(df_15m)

    d_swings = smc.swing_highs_lows_v4(df_1d)
    daily_ote = None
    if len(d_swings) >= 2:
        p1, p5 = d_swings.iloc[-2], d_swings.iloc[-1]
        mode = 'BULLISH' if p1['type'] == 'LOW' else 'BEARISH'
        r = abs(float(p5['p']) - float(p1['p']))
        daily_ote = {
            'mode': mode, 'ts': p5['ts'],
            '62': float(p5['p'])-0.62*r if mode=='BULLISH' else float(p5['p'])+0.62*r,
            '705': float(p5['p'])-0.705*r if mode=='BULLISH' else float(p5['p'])+0.705*r,
            '79': float(p5['p'])-0.79*r if mode=='BULLISH' else float(p5['p'])+0.79*r
        }

    m15_swings = smc.swing_highs_lows_v4(df_15m)
    m15_obs = smc.identify_order_block(df_15m, m15_swings)
    
    fig = make_subplots(rows=2, cols=1, vertical_spacing=0.05, row_heights=[0.3, 0.7],
                        subplot_titles=("DAILY ANCHOR (Video 4)", "15M INTEGRATED AUDIT (Videos 1-4)"))

    fig.add_trace(go.Candlestick(x=df_1d.index, open=df_1d['open'], high=df_1d['high'], low=df_1d['low'], close=df_1d['close'], name="D"), row=1, col=1)
    fig.add_trace(go.Candlestick(x=df_15m.index, open=df_15m['open'], high=df_15m['high'], low=df_15m['low'], close=df_15m['close'], name="15M"), row=2, col=1)

    if daily_ote:
        color = "rgba(0, 255, 0, 0.15)" if daily_ote['mode'] == 'BULLISH' else "rgba(255, 0, 0, 0.15)"
        for r in [1, 2]:
            fig.add_shape(type="rect", x0=df_15m.index[0] if r==2 else daily_ote['ts'], x1=df_1d.index[-1] if r==1 else df_15m.index[-1],
                            y0=daily_ote['79'], y1=daily_ote['62'], fillcolor=color, line_width=1, line_dash="dash", row=r, col=1)
            fig.add_shape(type="line", x0=df_15m.index[0] if r==2 else daily_ote['ts'], x1=df_1d.index[-1] if r==1 else df_15m.index[-1],
                            y0=daily_ote['705'], y1=daily_ote['705'], line=dict(color="Gold", width=2, dash="dash"), row=r, col=1)

    unique_days = pd.Series(df_15m.index.date).unique()
    for d in unique_days:
        day_start = f"{d} 00:00"
        day_end = f"{d} 23:59"
        fig.add_vrect(x0=f"{d} 02:00", x1=f"{d} 05:00", fillcolor="rgba(0, 0, 255, 0.05)", line_width=0, layer="below", row=2, col=1)
        fig.add_vrect(x0=f"{d} 08:30", x1=f"{d} 11:00", fillcolor="rgba(255, 165, 0, 0.05)", line_width=0, layer="below", row=2, col=1)
        
        day_df = df_15m.loc[df_15m.index.date == d]
        if not day_df.empty:
            open_p = float(day_df['open'].iloc[0])
            fig.add_shape(type="line", x0=day_start, x1=day_end, y0=open_p, y1=open_p,
                            line=dict(color="rgba(255, 255, 255, 0.2)", width=1, dash="dot"), row=2, col=1)

    for _, row in m15_obs.tail(10).iterrows():
        fig.add_shape(type="rect", x0=row['ts'], x1=df_15m.index[-1], y0=row['low'], y1=row['high'], fillcolor="rgba(255, 0, 255, 0.1)", line_width=0, row=2, col=1)
    
    if daily_ote:
        uz, lz = max(daily_ote['62'], daily_ote['79']), min(daily_ote['62'], daily_ote['79'])
        for _, row in m15_swings.iterrows():
            if lz <= float(row['p']) <= uz:
                hr = row['ts'].hour
                in_kz = (2 <= hr <= 5) or (8 <= hr <= 11)
                label = f"<b>{row['label']}</b>" + ("<br>KILLZONE" if in_kz else "")
                color = "#26a69a" if row['type'] == "LOW" else "#ef5350"
                fig.add_annotation(x=row['ts'], y=row['p'], text=label, showarrow=True, arrowhead=2, ay=100 if row['type']=="LOW" else -100, font=dict(color=color, size=10), row=2, col=1)

    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"]), dict(bounds=[17, 17], pattern="hour")], row=1, col=1)
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"]), dict(bounds=[17, 17], pattern="hour")], row=2, col=1)
    fig.update_layout(height=1400, template="plotly_dark", title=f"GOLD MASTER AUDIT (VIDEOS 1-4) [{uid}]", showlegend=False, xaxis1_rangeslider_visible=False, xaxis2_rangeslider_visible=False)
    fig.write_html(output_name)
    print(f"\n[DONE] MASTER AUDIT SUCCESS: OPEN '{output_name}'")

if __name__ == "__main__":
    run_gold_master_audit()
