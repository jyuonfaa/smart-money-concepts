"""
visualize_month3_video2.py
Month 3, Video 2 Dashboard: Top-Down Liquidity Sweep Confirmation
Plots the Daily chart with Monthly and Weekly Liquidity pools overlaid, showing how Daily closes interact with HTF body levels.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from smartmoneyconcepts import smc

CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

df_monthly = df_raw.resample('ME').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_weekly  = df_raw.resample('W-SUN').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_daily   = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

# Compute Liquidity on HTFs
# Compute Singlular Swings on HTFs
swings_m = smc.swing_highs_lows(df_monthly, swing_length=1)
swings_w = smc.swing_highs_lows(df_weekly, swing_length=2)

fig = go.Figure()

# --- Candlestick ---
fig.add_trace(go.Candlestick(
    x=df_daily.index, open=df_daily['open'], high=df_daily['high'],
    low=df_daily['low'],   close=df_daily['close'],
    name='AUDUSD Daily',
    increasing_line_color='#00e676', increasing_fillcolor='#00e676',
    decreasing_line_color='#ef5350', decreasing_fillcolor='#ef5350',
))

# --- Add HTF Swing Levels ---
def add_swing_lines(swings_df, tf_df, name_prefix, color_bull, color_bear, dash_style, width):
    valid_swings = swings_df.dropna(subset=['HighLow'])
    for idx, row in valid_swings.iterrows():
        # idx is an integer from 0..len(tf_df)-1
        dt = tf_df.index[idx]
        
        # HighLow = 1 means Swing High (Buy Stops above)
        # HighLow = -1 means Swing Low (Sell Stops below)
        is_high = row['HighLow'] == 1
        color = color_bull if is_high else color_bear
        
        # We will use the true candle body limit for the line, as per Video 2!
        tf_candle = tf_df.iloc[idx]
        if is_high:
            level = max(tf_candle['open'], tf_candle['close'])
        else:
            level = min(tf_candle['open'], tf_candle['close'])
            
        start_date = str(dt.date())
        
        # Find where the daily chart closes through this body level (Video 2 sweep rule)
        end_date = str(df_daily.index[-1].date())
        # Only check future daily candles
        future_daily = df_daily[df_daily.index > dt]
        if not future_daily.empty:
            if is_high:
                # Sweep is when a daily close goes ABOVE the HTF body high
                sweeps = future_daily[future_daily['close'] > level]
                if not sweeps.empty:
                    end_date = str(sweeps.index[0].date())
            else:
                # Sweep is when a daily close goes BELOW the HTF body low
                sweeps = future_daily[future_daily['close'] < level]
                if not sweeps.empty:
                    end_date = str(sweeps.index[0].date())
            
        label = f"{name_prefix} {'Buy' if is_high else 'Sell'} Stops (Body)"
        
        fig.add_shape(
            type='line',
            x0=start_date, x1=end_date,
            y0=level, y1=level,
            line=dict(color=color, width=width, dash=dash_style),
        )
        fig.add_annotation(
            x=start_date, y=level,
            text=label,
            showarrow=False,
            yshift=10 if is_high else -10,
            font=dict(color=color, size=10)
        )

# Add Monthly Lines (Solid, very thick)
add_swing_lines(swings_m, df_monthly, "Monthly", '#00b0ff', '#ff1744', 'solid', 3)

# Add Weekly Lines (Dash, medium)
add_swing_lines(swings_w, df_weekly, "Weekly", '#80d8ff', '#ff8a80', 'dash', 2)

# --- Layout ---
fig.update_layout(
    title='ICT Month 3 Video 2 — Top-Down Institutional Order Flow & Body Sweeps (AUDUSD 2016)',
    title_font=dict(size=18, color='#e0e0e0'),
    paper_bgcolor='#0d1117',
    plot_bgcolor='#161b22',
    font=dict(color='#c9d1d9'),
    xaxis=dict(
        gridcolor='#21262d', showgrid=True, rangeslider=dict(visible=False),
        tickfont=dict(color='#8b949e'), title='Date'
    ),
    yaxis=dict(
        gridcolor='#21262d', showgrid=True,
        tickfont=dict(color='#8b949e'), title='Price'
    ),
    legend=dict(
        bgcolor='rgba(22,27,34,0.85)', bordercolor='#30363d',
        borderwidth=1, font=dict(color='#c9d1d9')
    ),
    height=800,
)

out_path = 'ICT_MONTH3_VIDEO2_TOPDOWN.html'
fig.write_html(out_path)
print(f'Dashboard written to: {out_path}')

img_path = r'C:\Users\ESTHER\.gemini\antigravity\brain\f64d08c6-7375-4d73-9b56-6d675b60f9e9\month3_video2_topdown.png'
try:
    fig.write_image(img_path)
    print(f'Image saved to: {img_path}')
except Exception as e:
    print(f'Could not save image: {e}')
