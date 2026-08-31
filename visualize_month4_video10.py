import sys
import pandas as pd
import plotly.graph_objects as go

CSV_PATH = r'd:\C.Slim\ict-intelligence\HISTDATA_COM_ASCII_AUDUSD_M12016\DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'])
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 1: AUDUSD 15M (Sep 11 12:00 to Sep 13 14:00 UTC)
# ═══════════════════════════════════════════════════════════════════════════════
df_15m = df_raw.resample('15min').agg(
    {'open':'first','high':'max','low':'min','close':'last','volume':'sum'}
).dropna()

df_c1 = df_15m.loc['2016-09-11 12:00':'2016-09-13 14:00'].copy()

# Strings for category axis
xs_c1 = [str(t) for t in df_c1.index]

lv_start_s = '2016-09-11 19:30:00'
lv_end_s   = '2016-09-12 20:00:00'
lv_low     = 0.74938
lv_high    = 0.75678

filled_ts_s = '2016-09-13 10:45:00'
cg_ts_s     = '2016-09-13 11:00:00'

fig1 = go.Figure()

# Candlesticks
fig1.add_trace(go.Candlestick(
    x=xs_c1,
    open=df_c1['open'],
    high=df_c1['high'],
    low=df_c1['low'],
    close=df_c1['close'],
    name='AUDUSD 15M',
    increasing_line_color='#26a69a',
    decreasing_line_color='#ef5350',
    increasing_fillcolor='#26a69a',
    decreasing_fillcolor='#ef5350',
))

# Shaded Liquidity Void rectangle (formation range: LVStart to LVEnd)
fig1.add_shape(
    type='rect',
    x0=lv_start_s, x1=lv_end_s,
    y0=lv_low,     y1=lv_high,
    xref='x', yref='y',
    fillcolor='rgba(41, 98, 255, 0.18)',
    line=dict(color='rgba(41, 98, 255, 0.8)', width=1.5, dash='solid'),
)

# Reference dashed line from void floor (cap level) to the fill event
fig1.add_shape(
    type='line',
    x0=lv_end_s, x1=filled_ts_s,
    y0=lv_low,   y1=lv_low,
    xref='x', yref='y',
    line=dict(color='rgba(41, 98, 255, 0.6)', width=1.5, dash='dot'),
)

# Void Label
fig1.add_annotation(
    x=lv_start_s, y=lv_high,
    text=f"Sell-Side Void (Displacement Run)<br>LVHigh: {lv_high:.5f} | LVLow: {lv_low:.5f}",
    showarrow=True, arrowhead=1, ax=40, ay=-30,
    bgcolor='rgba(41, 98, 255, 0.15)', bordercolor='rgba(41, 98, 255, 0.8)',
    font=dict(size=10, color='#0d47a1')
)

# LVFilled Marker (2016-09-13 10:45)
fill_low = df_c1.loc[filled_ts_s, 'low'] if filled_ts_s in df_c1.index else lv_low
fig1.add_annotation(
    x=filled_ts_s, y=fill_low,
    text=f"LVFilled<br>(2016-09-13 10:45)",
    showarrow=True, arrowhead=2, arrowcolor='#2e7d32', arrowsize=1.5, arrowwidth=2,
    ax=0, ay=45,
    bgcolor='rgba(46, 125, 50, 0.2)', bordercolor='#2e7d32',
    font=dict(size=11, color='#1b5e20', family='Arial Black')
)

# LVCommonGapRef Marker (2016-09-13 11:00)
cg_high = df_c1.loc[cg_ts_s, 'high'] if cg_ts_s in df_c1.index else lv_low
fig1.add_annotation(
    x=cg_ts_s, y=cg_high,
    text=f"LVCommonGapRef<br>(2016-09-13 11:00 FVG)",
    showarrow=True, arrowhead=2, arrowcolor='#e65100', arrowsize=1.5, arrowwidth=2,
    ax=35, ay=-45,
    bgcolor='rgba(230, 81, 0, 0.2)', bordercolor='#e65100',
    font=dict(size=11, color='#bf360c', family='Arial Black')
)

fig1.update_layout(
    title='M4V10 Chart 1: Complete Liquidity Void Lifecycle — AUDUSD 15M (Sep 11–13, 2016)',
    xaxis_title='Time (UTC)',
    yaxis_title='Price',
    xaxis=dict(
        type='category',
        categoryorder='array',
        categoryarray=xs_c1,
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

out_c1_html = r'd:\C.Slim\ict-intelligence\m4v10_chart1_15m_lifecycle.html'
out_c1_png  = r'd:\C.Slim\ict-intelligence\m4v10_chart1_15m_lifecycle.png'
fig1.write_html(out_c1_html)
fig1.write_image(out_c1_png, scale=2)
print(f"Chart 1 saved: {out_c1_png}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 2: AUDUSD Daily (Jan 01 2016 to Jun 01 2016)
# ═══════════════════════════════════════════════════════════════════════════════
df_daily = df_raw.resample('D').agg(
    {'open':'first','high':'max','low':'min','close':'last','volume':'sum'}
).dropna()

df_c2 = df_daily.loc['2016-01-01':'2016-06-01'].copy()
xs_c2 = [str(t.date()) for t in df_c2.index]

lv_start_c2 = '2016-01-14'
lv_end_c2   = '2016-05-24'
lv_low_c2   = 0.68269
lv_high_c2  = 0.78344

fig2 = go.Figure()

fig2.add_trace(go.Candlestick(
    x=xs_c2,
    open=df_c2['open'],
    high=df_c2['high'],
    low=df_c2['low'],
    close=df_c2['close'],
    name='AUDUSD Daily',
    increasing_line_color='#26a69a',
    decreasing_line_color='#ef5350',
    increasing_fillcolor='#26a69a',
    decreasing_fillcolor='#ef5350',
))

# Shaded zone strictly from LVStart (2016-01-14) to LVEnd (2016-05-24)
fig2.add_shape(
    type='rect',
    x0=lv_start_c2, x1=lv_end_c2,
    y0=lv_low_c2,   y1=lv_high_c2,
    xref='x', yref='y',
    fillcolor='rgba(156, 39, 176, 0.15)',
    line=dict(color='rgba(156, 39, 176, 0.8)', width=1.5, dash='solid'),
)

fig2.add_annotation(
    x=lv_start_c2, y=lv_high_c2,
    text=f"Buy-Side Void (4.5 Month Formation Span)<br>LVStart: 2016-01-14 -> LVEnd: 2016-05-24<br>LVHigh: {lv_high_c2:.5f} | LVLow: {lv_low_c2:.5f} (Unfilled)",
    showarrow=True, arrowhead=1, ax=80, ay=-35,
    bgcolor='rgba(156, 39, 176, 0.15)', bordercolor='rgba(156, 39, 176, 0.8)',
    font=dict(size=10, color='#4a148c')
)

fig2.update_layout(
    title='M4V10 Chart 2: Long-Duration Liquidity Void Anchoring — AUDUSD Daily (Jan–Jun 2016)',
    xaxis_title='Date',
    yaxis_title='Price',
    xaxis=dict(
        type='category',
        categoryorder='array',
        categoryarray=xs_c2,
        nticks=25,
        tickangle=-45,
    ),
    xaxis_rangeslider_visible=False,
    plot_bgcolor='white',
    paper_bgcolor='white',
    height=650,
    width=1400,
    margin=dict(l=60, r=40, t=60, b=80),
)

out_c2_html = r'd:\C.Slim\ict-intelligence\m4v10_chart2_daily_long_duration.html'
out_c2_png  = r'd:\C.Slim\ict-intelligence\m4v10_chart2_daily_long_duration.png'
fig2.write_html(out_c2_html)
fig2.write_image(out_c2_png, scale=2)
print(f"Chart 2 saved: {out_c2_png}")
