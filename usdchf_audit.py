"""
ICT Video 4: USDCHF FRACTAL AUDIT
Verification of OTE respect on USDCHF
"""
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc
import uuid

def run_usdchf_audit():
    symbol = "USDCHF=X" 
    uid = str(uuid.uuid4())[:8]
    output_name = f"ICT_USDCHF_AUDIT_{uid}.html"

    print(f"Generating USDCHF Institutional Audit [{uid}]...")
    df_1d  = yf.download(symbol, period="1y", interval="1d", progress=False)
    df_4h  = yf.download(symbol, period="3mo", interval="1h", progress=False)
    df_15m = yf.download(symbol, period="7d", interval="15m", progress=False)

    def clean_df(df, resample=None):
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        if resample:
            df = df.resample(resample).agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna()
        if df.index.tz is None: df.index = df.index.tz_localize("UTC").tz_convert("America/New_York")
        else: df.index = df.index.tz_convert("America/New_York")
        return df

    df_1d, df_4h, df_15m = clean_df(df_1d), clean_df(df_4h, "4h"), clean_df(df_15m)

    d_swings = smc.swing_highs_lows_v4(df_1d)
    daily_otes = []
    for i in range(1, len(d_swings)):
        p1, p5 = d_swings.iloc[i-1], d_swings.iloc[i]
        mode = 'BULLISH' if p1['type'] == 'LOW' else 'BEARISH'
        r = abs(float(p5['p']) - float(p1['p']))
        if mode == 'BULLISH':
            o62, o705, o79 = float(p5['p'])-0.62*r, float(p5['p'])-0.705*r, float(p5['p'])-0.79*r
        else:
            o62, o705, o79 = float(p5['p'])+0.62*r, float(p5['p'])+0.705*r, float(p5['p'])+0.79*r
        
        if i >= len(d_swings) - 4: 
            daily_otes.append({'mode': mode, '62': o62, '705': o705, '79': o79})

    fig = make_subplots(rows=3, cols=1, vertical_spacing=0.03, row_heights=[0.3, 0.3, 0.4],
                        subplot_titles=("USDCHF DAILY", "USDCHF 4H (Interbank)", "USDCHF 15M (Surgical)"))

    for i, df in enumerate([df_1d, df_4h, df_15m]):
        fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name=f"P{i+1}"), row=i+1, col=1)

    for ote in daily_otes:
        color = "rgba(0, 255, 0, 0.1)" if ote['mode'] == 'BULLISH' else "rgba(255, 0, 0, 0.1)"
        for r in [1, 2, 3]:
            fig.add_shape(type="rect", x0=df_1d.index[0], x1=df_1d.index[-1], y0=ote['79'], y1=ote['62'], fillcolor=color, line_width=1, line_dash="dash", row=r, col=1)
            fig.add_shape(type="line", x0=df_1d.index[0], x1=df_1d.index[-1], y0=ote['705'], y1=ote['705'], line=dict(color="Gold", width=2, dash="dash"), row=r, col=1)

    m15_swings = smc.swing_highs_lows_v4(df_15m)
    for _, row in m15_swings.iterrows():
        for ote in daily_otes:
            uz, lz = max(float(ote['62']), float(ote['79'])), min(float(ote['62']), float(ote['79']))
            if lz <= float(row['p']) <= uz:
                c = "#26a69a" if row['type'] == "LOW" else "#ef5350"
                fig.add_annotation(x=row['ts'], y=row['p'], text=f"<b>{row['label']}</b>", showarrow=True, arrowhead=2, ay=80 if row['type']=="LOW" else -80, font=dict(color=c, size=10), row=3, col=1)
                break

    for r in [1, 2, 3]:
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"]), dict(bounds=[17, 17], pattern="hour")], row=r, col=1)
    
    fig.update_layout(height=1600, template="plotly_dark", title="USDCHF INSTITUTIONAL FRACTAL AUDIT", showlegend=False, xaxis1_rangeslider_visible=False, xaxis2_rangeslider_visible=False, xaxis3_rangeslider_visible=False)
    fig.write_html(output_name)
    print(f"\n[DONE] USDCHF SUCCESS: OPEN '{output_name}'")

if __name__ == "__main__":
    run_usdchf_audit()
