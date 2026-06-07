import urllib.request
import ssl
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc

def fetch_yahoo_chart_api(ticker, start_ts, end_ts):
    print(f"Fetching {ticker} directly from Yahoo v8 JSON API (Bypassing SSL & Crumb)...")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?period1={start_date}&period2={end_date}&interval=1d"
    
    context = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, context=context) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]
        
        df = pd.DataFrame({
            'date': pd.to_datetime(timestamps, unit='s'),
            'open': quote['open'],
            'high': quote['high'],
            'low': quote['low'],
            'close': quote['close']
        })
        df.set_index('date', inplace=True)
        return df.dropna()
    except Exception as e:
        print(f"Failed to fetch {ticker}: {e}")
        return pd.DataFrame()

# Using 2023 timestamps since 2026 data doesn't exist in real markets yet!
start_date = 1672531200 # Jan 1, 2023
end_date = 1704067200   # Dec 31, 2023

def run_smt_real_data():
    df1 = fetch_yahoo_chart_api('EURUSD=X', start_date, end_date)
    df2 = fetch_yahoo_chart_api('CHF=X', start_date, end_date) # USDCHF
    
    if df1.empty or df2.empty:
        print("Failed to get data.")
        return
        
    print(f"Loaded {len(df1)} EURUSD rows and {len(df2)} USDCHF rows for the year 2023.")
    
    print("Calculating Swings and SMT Divergence...")
    swings = smc.swing_highs_lows_v4(df1)
    smt_df = smc.smt_divergence(df1, df2, swings)
    
    bullish_divs = smt_df[smt_df['smt_bullish_div']]
    bearish_divs = smt_df[smt_df['smt_bearish_div']]
    
    print(f"Found {len(bullish_divs)} Bullish SMT Divergences")
    print(f"Found {len(bearish_divs)} Bearish SMT Divergences")
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=("USD/CHF (Inversely Correlated Benchmark)", "EUR/USD (Primary Asset)"))
                        
    fig.add_trace(go.Candlestick(x=df2.index, open=df2['open'], high=df2['high'], low=df2['low'], close=df2['close'], name='USDCHF'), row=1, col=1)
    fig.add_trace(go.Candlestick(x=df1.index, open=df1['open'], high=df1['high'], low=df1['low'], close=df1['close'], name='EURUSD'), row=2, col=1)
    
    # Plot Bearish SMT (EURUSD Higher High, USDCHF fails Lower Low)
    for ts, row in bearish_divs.iterrows():
        highs = swings[swings['type'] == 'HIGH']
        prev_highs = highs[highs['ts'] < ts]
        if len(prev_highs) > 0:
            prev_ts = prev_highs.iloc[-1]['ts']
            fig.add_shape(type="line", x0=prev_ts, y0=df1.loc[prev_ts]['high'], x1=ts, y1=df1.loc[ts]['high'], line=dict(color="Red", width=2), row=2, col=1)
            try:
                l0 = df2.loc[str(prev_ts.date())[:10]:str((prev_ts + pd.Timedelta(days=3)).date())[:10]]['low'].min()
                l1 = df2.loc[str(ts.date())[:10]:str((ts + pd.Timedelta(days=3)).date())[:10]]['low'].min()
                fig.add_shape(type="line", x0=prev_ts, y0=l0, x1=ts, y1=l1, line=dict(color="Red", width=2), row=1, col=1)
                fig.add_annotation(x=ts, y=df1.loc[ts]['high'], text="SMT Bearish", showarrow=True, arrowhead=1, ay=-40, row=2, col=1)
            except KeyError:
                pass

    # Plot Bullish SMT (EURUSD Lower Low, USDCHF fails Higher High)
    for ts, row in bullish_divs.iterrows():
        lows = swings[swings['type'] == 'LOW']
        prev_lows = lows[lows['ts'] < ts]
        if len(prev_lows) > 0:
            prev_ts = prev_lows.iloc[-1]['ts']
            fig.add_shape(type="line", x0=prev_ts, y0=df1.loc[prev_ts]['low'], x1=ts, y1=df1.loc[ts]['low'], line=dict(color="Green", width=2), row=2, col=1)
            try:
                h0 = df2.loc[str(prev_ts.date())[:10]:str((prev_ts + pd.Timedelta(days=3)).date())[:10]]['high'].max()
                h1 = df2.loc[str(ts.date())[:10]:str((ts + pd.Timedelta(days=3)).date())[:10]]['high'].max()
                fig.add_shape(type="line", x0=prev_ts, y0=h0, x1=ts, y1=h1, line=dict(color="Green", width=2), row=1, col=1)
                fig.add_annotation(x=ts, y=df1.loc[ts]['low'], text="SMT Bullish", showarrow=True, arrowhead=1, ay=40, row=2, col=1)
            except KeyError:
                pass

    fig.update_layout(title="Real Market SMT Divergence: EUR/USD vs USD/CHF", template="plotly_dark", height=800, xaxis_rangeslider_visible=False, xaxis2_rangeslider_visible=False)
    
    out_file = "ICT_SMT_REAL_DATA.html"
    fig.write_html(out_file)
    print(f"\n[SUCCESS] Generated SMT visualization: {out_file}")

if __name__ == "__main__":
    run_smt_real_data()
