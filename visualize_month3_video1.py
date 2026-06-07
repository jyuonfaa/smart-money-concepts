"""
visualize_month3_video1.py
Month 3, Video 1 Dashboard
Shows: Price, Swing Highs/Lows, Breaker Blocks, Macro Fib Quadrants
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc

CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

df_daily = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

swings_d = smc.swing_highs_lows(df_daily, swing_length=10)
grades   = smc.macro_swing_grading(df_daily)
bb       = smc.breaker_blocks(df_daily, swings_d)
bb.index = df_daily.index

fig = go.Figure()

# --- Candlestick ---
fig.add_trace(go.Candlestick(
    x=df_daily.index, open=df_daily['open'], high=df_daily['high'],
    low=df_daily['low'],   close=df_daily['close'],
    name='AUDUSD Daily',
    increasing_line_color='#00e676', increasing_fillcolor='#00e676',
    decreasing_line_color='#ef5350', decreasing_fillcolor='#ef5350',
))

# --- Swing Highs / Lows ---
swing_highs = swings_d[swings_d['HighLow'] ==  1]
swing_lows  = swings_d[swings_d['HighLow'] == -1]
fig.add_trace(go.Scatter(
    x=df_daily.index[swing_highs.index], y=swing_highs['Level'],
    mode='markers', name='Swing High',
    marker=dict(symbol='triangle-down', color='#ef5350', size=10)
))
fig.add_trace(go.Scatter(
    x=df_daily.index[swing_lows.index], y=swing_lows['Level'],
    mode='markers', name='Swing Low',
    marker=dict(symbol='triangle-up', color='#00e676', size=10)
))

# --- Macro Fib Quadrant Lines ---
q_colors   = ['#b2ebf2', '#80deea', '#e040fb', '#80deea', '#b2ebf2']
q_labels   = ['0% (Abs Low)', '25%', '50% Equilibrium', '75%', '100% (Abs High)']
q_columns  = ['0%', '25%', '50%', '75%', '100%']
q_dashes   = ['dot', 'dot', 'solid', 'dot', 'dot']
q_widths   = [1, 1, 2, 1, 1]
for col, label, color, dash, width in zip(q_columns, q_labels, q_colors, q_dashes, q_widths):
    level = grades[col].iloc[0]
    fig.add_hline(
        y=level, line_dash=dash, line_color=color, line_width=width,
        annotation_text=f'  {label}: {level:.5f}',
        annotation_position='top left',
        annotation_font_color=color, annotation_font_size=10,
    )

# --- Breaker Blocks ---
valid_bb = bb.dropna()
for dt, row in valid_bb.iterrows():
    is_bear = row['Breaker'] == -1
    color   = 'rgba(239,83,80,0.25)' if is_bear else 'rgba(0,230,118,0.25)'
    border  = '#ef5350' if is_bear else '#00e676'
    label   = 'BEAR Breaker' if is_bear else 'BULL Breaker'

    # Rectangle spanning from activation candle onwards
    broken_i = int(row['BrokenIndex'])
    if broken_i < len(df_daily):
        activation_date = df_daily.index[broken_i]
    else:
        activation_date = df_daily.index[-1]

    fig.add_shape(
        type='rect',
        x0=activation_date, x1=df_daily.index[-1],
        y0=row['Bottom'], y1=row['Top'],
        fillcolor=color, line=dict(color=border, width=1, dash='dot'),
        label=dict(text=f" {label} ({dt.strftime('%b %d')})", textposition='middle right',
                   font=dict(color=border, size=9)),
    )

# --- Layout ---
fig.update_layout(
    title='ICT Month 3 Video 1 — Breaker Blocks & Macro Fib Grading (AUDUSD 2016)',
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
    height=750,
)

out_path = 'ICT_MONTH3_VIDEO1_BREAKERS.html'
fig.write_html(out_path)
print(f'Dashboard written to: {out_path}')
