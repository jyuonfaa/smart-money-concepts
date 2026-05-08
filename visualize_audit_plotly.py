"""
ICT Video 3 — THE FINAL SUCCESS STATE
Corrected Day Attribution | Pruned Daily Levels | 4H Signatures | Zero Double Tags
"""
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc
import uuid

def get_killzone(timestamp):
    hour = timestamp.hour + timestamp.minute / 60
    if 19 <= hour:          return "Asian"
    elif 2 <= hour < 5:     return "London Open"
    elif 7 <= hour < 9:     return "NY Open"
    elif 10 <= hour < 11:   return "London Close"
    else:                   return "Other"

def build_daily_tags(ohlc):
    """Zero-Tolerance Institutional Day Deduplication with Correct Day Naming"""
    records = []
    ohlc = ohlc.copy()
    # Shift time by 17h so 5pm becomes 0am for grouping
    ohlc['inst_ts'] = ohlc.index - pd.Timedelta(hours=17)
    ohlc['inst_date'] = ohlc['inst_ts'].dt.strftime('%Y-%m-%d')
    
    for inst_date, day_data in ohlc.groupby('inst_date'):
        if len(day_data) < 10: continue
        hi_idx, lo_idx = day_data['high'].idxmax(), day_data['low'].idxmin()
        # Use the name of the institutional day (e.g. Wed night)
        inst_day_name = day_data['inst_ts'].dt.day_name().iloc[0]
        
        records.append({
            'date': inst_date, 'day_name': inst_day_name, 'tag_type': 'HIGH', 
            'ts': hi_idx, 'p': float(day_data.loc[hi_idx, 'high']), 
            'kz': get_killzone(hi_idx)
        })
        records.append({
            'date': inst_date, 'day_name': inst_day_name, 'tag_type': 'LOW',  
            'ts': lo_idx, 'p': float(day_data.loc[lo_idx, 'low']),  
            'kz': get_killzone(lo_idx)
        })
    
    df = pd.DataFrame(records).drop_duplicates(subset=['date', 'tag_type'])
    return df.sort_values('ts')

def run_final_success():
    symbol = "EURUSD=X"
    uid = str(uuid.uuid4())[:8]
    output_name = f"ICT_VIDEO_3_FINAL_SUCCESS_{uid}.html"

    print("Downloading Final MTF Audit Data...")
    df_1d  = yf.download(symbol, period="1y", interval="1d", progress=False)
    df_4h  = yf.download(symbol, period="3mo", interval="1h", progress=False)
    df_1h  = yf.download(symbol, period="1mo", interval="1h", progress=False)
    df_15m = yf.download(symbol, period="7d", interval="15m", progress=False)

    def clean_df(df):
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        df = df[~df.index.duplicated(keep='first')]
        if df.index.tz is None: df.index = df.index.tz_localize("UTC").tz_convert("America/New_York")
        else: df.index = df.index.tz_convert("America/New_York")
        return df

    df_1d, df_4h, df_1h, df_15m = clean_df(df_1d), clean_df(df_4h), clean_df(df_1h), clean_df(df_15m)

    # --- LOGIC ---
    # Daily: Higher significance (length=60)
    daily_swings = smc.swing_highs_lows(df_1d, swing_length=60).dropna(subset=['HighLow'])
    
    # 4H Signatures
    df_4h_smc = smc.swing_highs_lows(df_4h, swing_length=15)
    liq_4h = smc.liquidity(df_4h, df_4h_smc, range_percent=0.01)
    disp_4h = smc.displacement(df_4h)
    
    # 15M Surgical
    df_15m_smc = smc.swing_highs_lows(df_15m, swing_length=10)
    liq_15m = smc.liquidity(df_15m, df_15m_smc, range_percent=0.015)
    disp_15m = smc.displacement(df_15m)
    daily_tags = build_daily_tags(df_15m)
    
    # Weekly Anchor (Institutional naming)
    hi_ts_w, lo_ts_w = df_15m['high'].idxmax(), df_15m['low'].idxmin()
    w_lo_inst_day = (lo_ts_w - pd.Timedelta(hours=17)).day_name()
    w_hi_inst_day = (hi_ts_w - pd.Timedelta(hours=17)).day_name()

    # --- DASHBOARD ---
    fig = make_subplots(rows=4, cols=1, vertical_spacing=0.03, row_heights=[0.12, 0.18, 0.20, 0.50],
                        subplot_titles=("DAILY (12mo) - Pruned HTF Levels", "4H (3mo) - Mid-Term Signatures", "1H (3wk)", "15M (Surgical)"))

    # PANE 1: DAILY
    fig.add_trace(go.Candlestick(x=df_1d.index, open=df_1d['open'], high=df_1d['high'], low=df_1d['low'], close=df_1d['close'], name="D"), row=1, col=1)
    for _, row in daily_swings.tail(6).iterrows(): # Only top 6 most recent significant
        fig.add_shape(type="line", x0=df_1d.index[0], x1=df_1d.index[-1], y0=row['Level'], y1=row['Level'], line=dict(color="White", width=1, dash="dot"), row=1, col=1)

    # PANE 2: 4H (Signatures Activated)
    fig.add_trace(go.Candlestick(x=df_4h.index, open=df_4h['open'], high=df_4h['high'], low=df_4h['low'], close=df_4h['close'], name="4H"), row=2, col=1)
    for _, row in liq_4h[liq_4h['IsTooClean']==1].iterrows():
        fig.add_shape(type="rect", x0=df_4h.index[0], x1=df_4h.index[-1], y0=row['Level'], y1=row['End'], fillcolor="rgba(130,130,130,0.15)", line_width=0, row=2, col=1)
    for idx in df_4h.index[disp_4h['Displacement']!=0]:
        r = df_4h.loc[idx]
        fig.add_shape(type="rect", x0=idx - pd.Timedelta(hours=1), x1=idx + pd.Timedelta(hours=1), y0=r['low'], y1=r['high'], line=dict(color="Yellow", width=1), row=2, col=1)

    # PANE 3: 1H
    fig.add_trace(go.Candlestick(x=df_1h.index, open=df_1h['open'], high=df_1h['high'], low=df_1h['low'], close=df_1h['close'], name="1H"), row=3, col=1)

    # PANE 4: 15M
    fig.add_trace(go.Candlestick(x=df_15m.index, open=df_15m['open'], high=df_15m['high'], low=df_15m['low'], close=df_15m['close'], name="15M"), row=4, col=1)
    
    # 15M Signatures
    for _, row in liq_15m[liq_15m['IsTooClean']==1].iterrows():
        fig.add_shape(type="rect", x0=df_15m.index[0], x1=df_15m.index[-1], y0=row['Level'], y1=row['End'], fillcolor="rgba(130,130,130,0.15)", line_width=0, layer="below", row=4, col=1)
        fig.add_annotation(x=df_15m.index[len(df_15m)//2], y=(row['Level']+row['End'])/2, text="Too Clean", showarrow=False, font=dict(color="rgba(255,255,255,0.6)", size=9), row=4, col=1)

    for idx in df_15m.index[disp_15m['Displacement']!=0]:
        r = df_15m.loc[idx]
        fig.add_shape(type="rect", x0=idx - pd.Timedelta(minutes=15), x1=idx + pd.Timedelta(minutes=15), y0=r['low'], y1=r['high'], line=dict(color="Yellow", width=1), row=4, col=1)

    # 15M DAILY TAGS (Zero-Tolerance)
    for _, row in daily_tags.iterrows():
        color = "#26a69a" if row['tag_type']=="HIGH" else "#ef5350"
        ay = -50 if row['tag_type']=="HIGH" else 50
        fig.add_annotation(x=row['ts'], y=row['p'], text=f"{row['tag_type']} ({row['kz']})", showarrow=True, arrowhead=2, ay=ay, font=dict(color=color, size=9), row=4, col=1)

    # WEEKLY TAGS (Institutional Day Attribution)
    fig.add_annotation(x=hi_ts_w, y=df_15m.loc[hi_ts_w, 'high'], text=f"WEEKLY HIGH - {w_hi_inst_day} {get_killzone(hi_ts_w)}", showarrow=True, arrowhead=3, ay=-100, font=dict(color="Gold", size=11, family="Arial Black"), row=4, col=1)
    fig.add_annotation(x=lo_ts_w, y=df_15m.loc[lo_ts_w, 'low'],  text=f"WEEKLY LOW - {w_lo_inst_day} {get_killzone(lo_ts_w)}",  showarrow=True, arrowhead=3, ay=100,  font=dict(color="Gold", size=11, family="Arial Black"), row=4, col=1)

    fig.update_layout(height=1600, template="plotly_dark", title=f"ICT VIDEO 3: FINAL SUCCESS STATE [{uid}]", showlegend=False, xaxis4_rangeslider_visible=False)
    fig.write_html(output_name)
    print(f"\n[DONE] FINAL SUCCESS: OPEN '{output_name}'")

if __name__ == "__main__":
    run_final_success()
