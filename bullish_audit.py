"""
ICT Video 3 — BULLISH VALIDATION AUDIT (Historical)
Targets July 2024 (Strong Bullish Week)
"""
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from smartmoneyconcepts import smc

def get_killzone(timestamp):
    hour = timestamp.hour + timestamp.minute / 60
    if 19 <= hour:          return "Asian"
    elif 2 <= hour < 5:     return "London Open"
    elif 7 <= hour < 9:     return "NY Open"
    elif 10 <= hour < 11:   return "London Close"
    else:                   return "Other"

def run_bullish_validation():
    symbol = "EURUSD=X"
    # July 2024 was a strong bullish rally for EURUSD
    start_date = "2024-07-08"
    end_date = "2024-07-15"
    
    print(f"Downloading Historical Bullish Data ({start_date} to {end_date})...")
    df = yf.download(symbol, start=start_date, end=end_date, interval="1h", progress=False)

    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    if df.index.tz is None: df.index = df.index.tz_localize("UTC").tz_convert("America/New_York")
    else: df.index = df.index.tz_convert("America/New_York")

    # Group by Institutional Day (17:00)
    df['inst_date'] = (df.index - pd.Timedelta(hours=17)).strftime('%Y-%m-%d')
    records = []
    for date_str, day_data in df.groupby('inst_date'):
        if len(day_data) < 5: continue
        hi_idx, lo_idx = day_data['high'].idxmax(), day_data['low'].idxmin()
        records.append({'type': 'HIGH', 'ts': hi_idx, 'p': float(day_data.loc[hi_idx, 'high']), 'kz': get_killzone(hi_idx)})
        records.append({'type': 'LOW',  'ts': lo_idx, 'p': float(day_data.loc[lo_idx, 'low']),  'kz': get_killzone(lo_idx)})
    
    daily_tags = pd.DataFrame(records)
    w_lo_ts = df['low'].idxmin()
    w_hi_ts = df['high'].idxmax()

    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="1H Bullish"))

    print("\n--- BULLISH VALIDATION AUDIT LOG ---")
    for _, row in daily_tags.iterrows():
        color = "#26a69a" if row['type']=="HIGH" else "#ef5350"
        ay = -40 if row['type']=="HIGH" else 40
        fig.add_annotation(x=row['ts'], y=row['p'], text=f"{row['type']} ({row['kz']})", showarrow=True, arrowhead=2, ay=ay, font=dict(color=color, size=9))
        if row['type'] == 'LOW':
            print(f"  LOW formed in {row['kz']} on {row['ts'].day_name()}")

    # Weekly Low (The Key Anchor)
    fig.add_annotation(x=w_lo_ts, y=df.loc[w_lo_ts, 'low'], text=f"WEEKLY LOW - {w_lo_ts.day_name()} {get_killzone(w_lo_ts)}", showarrow=True, arrowhead=3, ay=80, font=dict(color="Gold", size=12, family="Arial Black"))
    
    print(f"\nWEEKLY LOW: {w_lo_ts.day_name()} {get_killzone(w_lo_ts)}")

    fig.update_layout(height=800, template="plotly_dark", title=f"BULLISH VALIDATION AUDIT: EURUSD {start_date} (Weekly Low Focus)", showlegend=False)
    fig.write_html("bullish_validation_2024.html")
    print("\n[SUCCESS] Bullish Audit saved as bullish_validation_2024.html")

if __name__ == "__main__":
    run_bullish_validation()
