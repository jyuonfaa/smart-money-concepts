import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc

def run_smt_2026_forex():
    print("Downloading 2026 YTD data for EUR/USD and USD/CHF...")
    
    # ICT explicitly states we can use inversely correlated pairs 
    # if the Dollar Index is unavailable. EURUSD vs USDCHF is the classic pairing.
    asset1_ticker = 'EURUSD=X'
    asset2_ticker = 'CHF=X' # USDCHF
    
    start_date = "2026-01-01"
    end_date = "2026-06-06"
    
    try:
        df1 = yf.download(asset1_ticker, start=start_date, end=end_date, progress=False)
        df2 = yf.download(asset2_ticker, start=start_date, end=end_date, progress=False)
    except Exception as e:
        print(f"Download failed: {e}")
        return

    if df1.empty or df2.empty:
        print("Failed to get data from Yahoo Finance.")
        return
        
    print(f"Loaded {len(df1)} EURUSD rows and {len(df2)} USDCHF rows.")
    
    # Flatten columns
    df1.columns = [c[0].lower() if isinstance(df1.columns, pd.MultiIndex) else c.lower() for c in df1.columns]
    df2.columns = [c[0].lower() if isinstance(df2.columns, pd.MultiIndex) else c.lower() for c in df2.columns]
        
    print("Calculating Swings and SMT Divergence...")
    # SMT Divergence engine accepts the primary asset and the inversely correlated benchmark
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

    fig.update_layout(title="2026 SMT Divergence: EUR/USD vs USD/CHF", template="plotly_dark", height=800, xaxis_rangeslider_visible=False, xaxis2_rangeslider_visible=False)
    
    out_file = "ICT_SMT_2026_REAL_DATA.html"
    fig.write_html(out_file)
    print(f"\n[SUCCESS] Generated SMT 2026 visualization: {out_file}")

if __name__ == "__main__":
    run_smt_2026_forex()
