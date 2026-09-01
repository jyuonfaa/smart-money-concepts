import pandas as pd
import plotly.graph_objects as go

CSV_PATH = r'd:\C.Slim\ict-intelligence\HISTDATA_COM_ASCII_AUDUSD_M12016\DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'])
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

df_15m = df_raw.resample('15min').agg(
    {'open':'first','high':'max','low':'min','close':'last','volume':'sum'}
).dropna()

df_win = df_15m.loc['2016-09-14 20:00':'2016-09-15 14:00'].copy()

xs = [str(t) for t in df_win.index]

swing_level = 0.74956
raid_ts_s   = '2016-09-15 08:30:00'
revert_ts_s = '2016-09-15 08:45:00'
sweep_depth_pips = 10.9

fig = go.Figure()

# Candlesticks
fig.add_trace(go.Candlestick(
    x=xs,
    open=df_win['open'],
    high=df_win['high'],
    low=df_win['low'],
    close=df_win['close'],
    name='AUDUSD 15M',
    increasing_line_color='#26a69a',
    decreasing_line_color='#ef5350',
    increasing_fillcolor='#26a69a',
    decreasing_fillcolor='#ef5350',
))

# Horizontal reference line for swing high (0.74956)
fig.add_shape(
    type='line',
    x0=xs[0], x1=xs[-1],
    y0=swing_level, y1=swing_level,
    xref='x', yref='y',
    line=dict(color='#d32f2f', width=1.8, dash='dash'),
)

fig.add_annotation(
    x=xs[2], y=swing_level,
    text=f"Swing High Reference: {swing_level:.5f}<br>(Formed 2016-09-14 02:45)",
    showarrow=False,
    yshift=14,
    xanchor='left',
    bgcolor='rgba(255, 255, 255, 0.85)',
    bordercolor='#d32f2f',
    font=dict(size=10, color='#b71c1c')
)

# Raid bar marker (2016-09-15 08:30)
raid_high = df_win.loc[raid_ts_s, 'high']
fig.add_annotation(
    x=raid_ts_s, y=raid_high,
    text=f"Liquidity Raid Bar<br>High: {raid_high:.5f}<br>SweepDepthPips: {sweep_depth_pips:.1f} (expected)",
    showarrow=True, arrowhead=2, arrowcolor='#d32f2f', arrowsize=1.5, arrowwidth=2,
    ax=0, ay=-55,
    bgcolor='rgba(211, 47, 47, 0.15)', bordercolor='#d32f2f',
    font=dict(size=11, color='#b71c1c', family='Arial Black')
)

# Reversion bar marker (2016-09-15 08:45)
revert_close = df_win.loc[revert_ts_s, 'close']
revert_low   = df_win.loc[revert_ts_s, 'low']
fig.add_annotation(
    x=revert_ts_s, y=revert_low,
    text=f"RaidReverted=True<br>(Close: {revert_close:.5f} < {swing_level:.5f})",
    showarrow=True, arrowhead=2, arrowcolor='#2e7d32', arrowsize=1.5, arrowwidth=2,
    ax=45, ay=45,
    bgcolor='rgba(46, 125, 50, 0.15)', bordercolor='#2e7d32',
    font=dict(size=10, color='#1b5e20', family='Arial Black')
)

fig.update_layout(
    title='M4V11 Visual Audit: Liquidity Raid Mechanic — AUDUSD 15M (Sep 14 20:00 – Sep 15 14:00 UTC)',
    xaxis_title='Time (UTC)',
    yaxis_title='Price',
    xaxis=dict(
        type='category',
        categoryorder='array',
        categoryarray=xs,
        nticks=20,
        tickangle=-45,
    ),
    xaxis_rangeslider_visible=False,
    plot_bgcolor='white',
    paper_bgcolor='white',
    height=650,
    width=1400,
    margin=dict(l=60, r=40, t=60, b=80),
)

out_html = r'd:\C.Slim\ict-intelligence\m4v11_chart_liquidity_raid.html'
out_png  = r'd:\C.Slim\ict-intelligence\m4v11_chart_liquidity_raid.png'

fig.write_html(out_html)
fig.write_image(out_png, scale=2)
print(f"Chart saved: {out_png}")
