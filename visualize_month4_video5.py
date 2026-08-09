import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, r'd:\C.Slim\ict-intelligence')
from smartmoneyconcepts import smc

OUT_DIR = r"C:\Users\ESTHER\.gemini\antigravity\brain\6a816fef-ace0-45c8-a977-524bfb23b0c3"

CSV_PATH = r'd:\C.Slim\ict-intelligence\HISTDATA_COM_ASCII_AUDUSD_M12016\DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'])
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)
df_daily = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

swings = smc.swing_highs_lows(df_daily, swing_length=10)
bb_df = smc._breaker_blocks(df_daily, swings)

# 2. Confirm and state explicitly whether BB output already preserves DatetimeIndex
print("========================================")
print(f"Index dtype verification: {bb_df.index.dtype}")
print(f"Is DatetimeIndex? {isinstance(bb_df.index, pd.DatetimeIndex)}")
print("========================================")

blocks = bb_df[~bb_df['BB'].isna()]

def plot_zoomed(start_date, end_date, title, filename_base):
    fig = go.Figure(data=[go.Candlestick(
        x=df_daily.index,
        open=df_daily['open'],
        high=df_daily['high'],
        low=df_daily['low'],
        close=df_daily['close'],
        name='AUDUSD Daily'
    )])
    
    for date, row in blocks.iterrows():
        d_str = str(date.date())
        is_bearish = (row['BB'] == -1)
        is_live = pd.isna(row['Invalidated'])
        
        # 1. Anchor zones correctly to actual timestamps
        end_idx = df_daily.index[-1]
        if not is_live:
            end_idx = df_daily.index[int(row['Invalidated'])]
            
        sub = df_daily.loc[date:end_idx]
        if len(sub) > 0:
            raid_date = sub['high'].idxmax() if is_bearish else sub['low'].idxmin()
        else:
            raid_date = date
            
        # Color coding: Distinctly differentiate confirmed-live vs confirmed-invalidated
        if is_bearish:
            fill_color = "rgba(255, 0, 0, 0.3)" if is_live else "rgba(150, 0, 0, 0.1)"
            line_color = "red" if is_live else "darkred"
        else:
            fill_color = "rgba(0, 255, 0, 0.3)" if is_live else "rgba(0, 150, 0, 0.1)"
            line_color = "green" if is_live else "darkgreen"
            
        x0 = str(date)
        x1 = str(end_idx)
        
        # Rectangle spanning BBBodyTop to BBBodyBottom
        fig.add_shape(type="rect", x0=x0, y0=row['BBBodyBottom'], x1=x1, y1=row['BBBodyTop'],
            line=dict(color=line_color, width=1), fillcolor=fill_color, opacity=1)
            
        # Marker/Line at MidSwingLevel (Activation Threshold)
        fig.add_shape(type="line", x0=x0, y0=row['MidSwingLevel'], x1=x1, y1=row['MidSwingLevel'],
            line=dict(color="blue", width=2, dash="dash"))
        
        # Marker/Line at BBWickHigh/BBWickLow (Stop Level)
        stop_lvl = row['BBWickHigh'] if is_bearish else row['BBWickLow']
        if not pd.isna(stop_lvl):
            fig.add_shape(type="line", x0=x0, y0=stop_lvl, x1=x1, y1=stop_lvl,
                line=dict(color="purple", width=2, dash="dot"))
                
        # Marker at RaidLevel
        fig.add_trace(go.Scatter(x=[str(raid_date)], y=[row['RaidLevel']],
            mode="markers", marker=dict(color="black", symbol="x", size=10), name=f"Raid ({d_str})"))
            
        # Label each block with direction and its index/date
        label = f"{'BEAR' if is_bearish else 'BULL'} BB ({d_str})"
        status_label = "LIVE" if is_live else f"INVALIDATED ({str(end_idx.date())})"
        full_label = f"{label}<br>{status_label}"
        
        fig.add_annotation(x=x0, y=row['BBBodyTop'] if is_bearish else row['BBBodyBottom'],
            text=full_label, showarrow=True, arrowhead=1, ax=40, ay=-40 if is_bearish else 40)

    # Dynamic y-axis for clean viewing
    sub_df = df_daily.loc[start_date:end_date]
    y_min = sub_df['low'].min() - 0.005
    y_max = sub_df['high'].max() + 0.005
    
    fig.update_layout(
        title=title, xaxis_rangeslider_visible=False,
        xaxis_range=[start_date, end_date], yaxis_range=[y_min, y_max],
        width=1400, height=800
    )
    
    html_path = os.path.join(OUT_DIR, f"{filename_base}.html")
    fig.write_html(html_path)
    print(f"Saved HTML: {html_path}")
    
    png_path = os.path.join(OUT_DIR, f"{filename_base}.png")
    try:
        fig.write_image(png_path)
        print(f"Saved PNG: {png_path}")
    except Exception as e:
        print(f"Failed to save PNG (Kaleido missing?): {e}")

# 4. Zoom into and screenshot TWO specific daily blocks
plot_zoomed('2016-02-15', '2016-08-31', "M4V5 Breaker Block - BEARISH (2016-04-07)", "bb_bearish_0407")
plot_zoomed('2016-01-15', '2016-07-31', "M4V5 Breaker Block - BULLISH (2016-02-04)", "bb_bullish_0204")
