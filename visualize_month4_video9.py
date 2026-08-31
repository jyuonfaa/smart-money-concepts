import sys
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, r'd:\C.Slim\ict-intelligence')

CSV_PATH = r'd:\C.Slim\ict-intelligence\HISTDATA_COM_ASCII_AUDUSD_M12016\DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'])
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)
df_15m = df_raw.resample('15min').agg(
    {'open':'first','high':'max','low':'min','close':'last','volume':'sum'}
).dropna()

# Window: Sep 17 12:00 to Sep 19 06:00 — wide enough to show Friday close + weekend gap + Sunday reopen
df_win = df_15m.loc['2016-09-17 12:00':'2016-09-19 06:00'].copy()

# Known values
vb_ts      = pd.Timestamp('2016-09-18 17:00')
vb_high    = 0.74890
vb_low     = 0.74776
vb_mt      = (vb_high + vb_low) / 2.0
filled_ts  = pd.Timestamp('2016-09-18 18:45')
inval_ts   = pd.Timestamp('2016-09-18 19:00')

# Convert index to string for plotly category axis
xs = [str(t) for t in df_win.index]
vb_ts_s     = str(vb_ts)
filled_ts_s = str(filled_ts)
inval_ts_s  = str(inval_ts)
# Zone ends at invalidation bar
zone_end_s  = str(inval_ts)

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

# VB zone rectangle (formation to invalidation)
fig.add_shape(
    type='rect',
    x0=vb_ts_s, x1=zone_end_s,
    y0=vb_low,  y1=vb_high,
    xref='x', yref='y',
    fillcolor='rgba(255, 80, 80, 0.20)',
    line=dict(color='rgba(255, 80, 80, 0.80)', width=1.5),
)

# VBMeanThreshold dotted line within zone
fig.add_shape(
    type='line',
    x0=vb_ts_s, x1=zone_end_s,
    y0=vb_mt, y1=vb_mt,
    xref='x', yref='y',
    line=dict(color='rgba(255, 80, 80, 0.60)', width=1, dash='dot'),
)

# VB formation label
fig.add_annotation(
    x=vb_ts_s, y=vb_high,
    text='BEAR VB<br>formed',
    showarrow=True, arrowhead=2, arrowcolor='red',
    ax=0, ay=-40,
    font=dict(size=10, color='red'),
    xref='x', yref='y',
)

# VBFilled vertical line
fig.add_shape(
    type='line',
    x0=filled_ts_s, x1=filled_ts_s,
    y0=0, y1=1,
    xref='x', yref='paper',
    line=dict(color='orange', width=2, dash='dash'),
)
fig.add_annotation(
    x=filled_ts_s, y=0.97,
    text='FILLED',
    showarrow=False,
    font=dict(size=10, color='darkorange', family='monospace'),
    xref='x', yref='paper',
    bgcolor='rgba(255,255,255,0.7)',
)

# VBInvalidated vertical line
fig.add_shape(
    type='line',
    x0=inval_ts_s, x1=inval_ts_s,
    y0=0, y1=1,
    xref='x', yref='paper',
    line=dict(color='black', width=2, dash='dash'),
)
fig.add_annotation(
    x=inval_ts_s, y=0.90,
    text='INVAL',
    showarrow=False,
    font=dict(size=10, color='black', family='monospace'),
    xref='x', yref='paper',
    bgcolor='rgba(255,255,255,0.7)',
)

# Labels for VBHigh / VBLow on the right y-axis edge
fig.add_annotation(
    x=zone_end_s, y=vb_high,
    text=f'VBHigh {vb_high:.5f}',
    showarrow=False, xanchor='left',
    font=dict(size=9, color='red'),
    xref='x', yref='y', xshift=4,
)
fig.add_annotation(
    x=zone_end_s, y=vb_low,
    text=f'VBLow {vb_low:.5f}',
    showarrow=False, xanchor='left',
    font=dict(size=9, color='red'),
    xref='x', yref='y', xshift=4,
)

# Weekend gap shading: Friday close to Sunday open
# On a date axis this renders as physical whitespace automatically;
# add a light grey band to make it explicit.
fig.add_shape(
    type='rect',
    x0='2016-09-16 17:00', x1='2016-09-18 17:00',
    y0=0, y1=1,
    xref='x', yref='paper',
    fillcolor='rgba(200, 200, 200, 0.15)',
    line=dict(width=0),
    layer='below',
)
fig.add_annotation(
    x='2016-09-17 12:00', y=0.08,
    text='weekend (no data)',
    showarrow=False,
    font=dict(size=9, color='grey'),
    xref='x', yref='paper',
)

fig.update_layout(
    title='M4V9 Vacuum Block — AUDUSD 15M, Sep 17-19 2016 (Weekly Open Gap)',
    xaxis_title='Time (UTC)',
    yaxis_title='Price',
    xaxis=dict(
        type='date',
        range=['2016-09-17 12:00', '2016-09-19 06:00'],
        tickformat='%b %d\n%H:%M',
        dtick=3 * 3600 * 1000,  # 3-hour ticks in milliseconds
    ),
    xaxis_rangeslider_visible=False,
    plot_bgcolor='white',
    paper_bgcolor='white',
    height=600,
    width=1400,
    legend=dict(orientation='h', y=1.02, x=0),
)

out_html = r'd:\C.Slim\ict-intelligence\vb_sep18_weekly_open.html'
out_png  = r'd:\C.Slim\ict-intelligence\vb_sep18_weekly_open.png'

fig.write_html(out_html)
print(f'HTML saved: {out_html}')

try:
    fig.write_image(out_png, scale=2)
    print(f'PNG saved: {out_png}')
except Exception as e:
    print(f'PNG failed: {e}')
