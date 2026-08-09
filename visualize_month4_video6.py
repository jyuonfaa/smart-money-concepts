"""
visualize_month4_video6.py
Month 4, Video 6 -- Rejection Blocks Visual Audit.
Generates zoomed charts for two specific Daily blocks:
  - 2016-02-04 BEAR
  - 2016-02-09 BULL
Standards: correctly anchored zones, DatetimeIndex preserved/confirmed, RBTop/RBBottom
rectangles, separate RBWickLevel (stop) and RBBodyLevel (trigger) markers,
color-coded live vs. invalidated.
"""
import sys
import pandas as pd
import numpy as np
sys.path.insert(0, r'd:\C.Slim\ict-intelligence')

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from smartmoneyconcepts.smc import smc
if not hasattr(smc, '_rejection_blocks'):
    _impl_path = r'C:\Users\ESTHER\.gemini\antigravity\brain\6a816fef-ace0-45c8-a977-524bfb23b0c3\scratch\rb_impl.py'
    with open(_impl_path, 'r', encoding='utf-8') as _f:
        exec(compile(_f.read(), _impl_path, 'exec'), globals())

# ── Load data ─────────────────────────────────────────────────────────────────
CSV_PATH = r'd:\C.Slim\ict-intelligence\HISTDATA_COM_ASCII_AUDUSD_M12016\DAT_ASCII_AUDUSD_M1_2016.csv'
print("Loading AUDUSD 2016 1M data...")
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'])
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

print("Resampling to Daily...")
daily = df_raw.resample('D').agg(
    {'open':'first','high':'max','low':'min','close':'last','volume':'sum'}
).dropna()

# ── Prove DatetimeIndex preserved ─────────────────────────────────────────────
print(f"\nDatetimeIndex dtype check: {daily.index.dtype}")
assert str(daily.index.dtype).startswith('datetime'), "FAIL: DatetimeIndex not preserved"
print("DatetimeIndex dtype: CONFIRMED datetime64[us]")

# ── Detect Rejection Blocks ───────────────────────────────────────────────────
swings = smc.swing_highs_lows(daily, swing_length=5)
rbs    = smc._rejection_blocks(daily, swings)

print(f"\nRB output index dtype: {rbs.index.dtype}")
assert str(rbs.index.dtype).startswith('datetime'), "FAIL: RB output lost DatetimeIndex"
print("RB output index: CONFIRMED datetime64 -- zone anchoring safe")

detected = rbs[rbs['RB'].notna()]
print(f"Total detected daily RBs: {len(detected)}")


def make_rb_chart(block_date, direction, context_days=30, label=""):
    """
    Render a zoomed candlestick chart for a single Rejection Block.
    context_days: how many calendar days before/after the swing to include.
    """
    block_ts = pd.Timestamp(block_date)
    row       = rbs.loc[block_ts]

    rb_top     = row['RBTop']
    rb_bottom  = row['RBBottom']
    wick_level = row['RBWickLevel']
    body_level = row['RBBodyLevel']
    inv_ts     = row['Invalidated']
    is_live    = pd.isna(inv_ts)

    # Derive cluster boundaries from swings for the anchor rectangle start
    hl_vals      = swings['HighLow'].values
    swing_idxs   = np.where(~np.isnan(hl_vals))[0]
    block_pos    = daily.index.get_loc(block_ts)
    # Find which swing_idx matches block_pos
    sw_i = np.where(swing_idxs == block_pos)[0]
    if len(sw_i) == 0:
        # fallback: use block_ts directly
        cluster_start = block_ts
        prev_swing_ts = block_ts
    else:
        i = sw_i[0]
        prev_pos      = swing_idxs[i - 1] if i > 0 else block_pos
        cluster_start = daily.index[prev_pos + 1]
        prev_swing_ts = daily.index[prev_pos]

    # Window: context_days before cluster_start to context_days after block_ts (or invalidation)
    window_start = cluster_start - pd.Timedelta(days=context_days)
    if is_live:
        window_end = block_ts + pd.Timedelta(days=context_days)
    else:
        inv_ts_parsed = pd.Timestamp(inv_ts)
        window_end = inv_ts_parsed + pd.Timedelta(days=10)

    chart_data = daily.loc[window_start:window_end].copy()

    # Zone rect x-span: cluster start -> invalidation or end of data
    zone_x_start = cluster_start
    zone_x_end   = inv_ts_parsed if not is_live else daily.index[-1]

    # Color scheme
    zone_color   = 'rgba(220,50,50,0.15)' if direction == 'BEAR' else 'rgba(50,180,80,0.15)'
    zone_border  = 'rgba(220,50,50,0.6)'  if direction == 'BEAR' else 'rgba(50,180,80,0.6)'
    wick_color   = 'rgba(255,80,0,0.85)'  # stop = orange regardless of direction
    body_color   = 'rgba(30,120,255,0.85)' # trigger = blue regardless of direction
    candle_up    = '#26a69a'
    candle_dn    = '#ef5350'
    title_status = 'LIVE' if is_live else f'Invalidated {pd.Timestamp(inv_ts).date()}'

    fig = go.Figure()

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=chart_data.index,
        open=chart_data['open'],
        high=chart_data['high'],
        low=chart_data['low'],
        close=chart_data['close'],
        increasing_line_color=candle_up,
        decreasing_line_color=candle_dn,
        name='AUDUSD Daily',
        showlegend=True,
    ))

    # RBTop/RBBottom zone rectangle (anchored correctly, NOT wall-to-wall)
    fig.add_shape(
        type='rect',
        x0=zone_x_start, x1=zone_x_end,
        y0=rb_bottom, y1=rb_top,
        fillcolor=zone_color,
        line=dict(color=zone_border, width=1.5),
        layer='below',
        name='RB Zone',
    )

    # RBWickLevel -- stop reference (horizontal line across window)
    fig.add_shape(
        type='line',
        x0=zone_x_start, x1=zone_x_end,
        y0=wick_level, y1=wick_level,
        line=dict(color=wick_color, width=1.5, dash='dot'),
    )
    fig.add_annotation(
        x=zone_x_end, y=wick_level,
        text=f"WickLevel (Stop) {wick_level:.5f}",
        showarrow=False, xanchor='left',
        font=dict(color=wick_color, size=11),
        bgcolor='rgba(255,255,255,0.7)',
    )

    # RBBodyLevel -- trigger (horizontal line)
    fig.add_shape(
        type='line',
        x0=zone_x_start, x1=zone_x_end,
        y0=body_level, y1=body_level,
        line=dict(color=body_color, width=1.5, dash='dash'),
    )
    fig.add_annotation(
        x=zone_x_end, y=body_level,
        text=f"BodyLevel (Trigger) {body_level:.5f}",
        showarrow=False, xanchor='left',
        font=dict(color=body_color, size=11),
        bgcolor='rgba(255,255,255,0.7)',
    )

    # Vertical line at block formation date
    fig.add_shape(
        type='line',
        x0=block_ts, x1=block_ts,
        y0=rb_bottom * 0.998, y1=rb_top * 1.002,
        line=dict(color='gray', width=1, dash='dot'),
    )
    fig.add_annotation(
        x=block_ts, y=rb_top * 1.001,
        text=f"RB Formed ({block_ts.date()})",
        showarrow=False, yanchor='bottom',
        font=dict(color='gray', size=10),
    )

    # Invalidation marker
    if not is_live:
        fig.add_shape(
            type='line',
            x0=inv_ts_parsed, x1=inv_ts_parsed,
            y0=0, y1=1,
            xref='x', yref='paper',
            line=dict(color='black', width=1.5, dash='solid'),
        )
        fig.add_annotation(
            x=inv_ts_parsed,
            y=1, yref='paper',
            text=f"Invalidated {pd.Timestamp(inv_ts).date()}",
            showarrow=False,
            xanchor='left', yanchor='top',
            font=dict(size=10, color='black'),
            bgcolor='rgba(255,255,255,0.7)',
        )

    # Legend proxies for zone/lines
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='lines',
        line=dict(color=zone_border, width=8),
        name=f"RB Zone ({rb_bottom:.5f} - {rb_top:.5f})",
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='lines',
        line=dict(color=wick_color, width=2, dash='dot'),
        name=f"WickLevel / Stop ({wick_level:.5f})",
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='lines',
        line=dict(color=body_color, width=2, dash='dash'),
        name=f"BodyLevel / Trigger ({body_level:.5f})",
    ))

    fig.update_layout(
        title=f"M4V6 Rejection Block -- {direction} | {block_ts.date()} | {title_status}",
        xaxis_title='Date',
        yaxis_title='Price (AUDUSD)',
        template='plotly_white',
        xaxis_rangeslider_visible=False,
        height=650,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
        margin=dict(l=60, r=160, t=80, b=60),
    )

    return fig


# ── Generate charts for the two target blocks ─────────────────────────────────
targets = [
    ('2016-02-04', 'BEAR', 'rb_bear_0204'),
    ('2016-02-09', 'BULL', 'rb_bull_0209'),
]

artifact_dir = r'C:\Users\ESTHER\.gemini\antigravity\brain\6a816fef-ace0-45c8-a977-524bfb23b0c3'

for block_date, direction, slug in targets:
    print(f"\nRendering {direction} block {block_date}...")
    fig = make_rb_chart(block_date, direction)

    html_path = rf'{artifact_dir}\{slug}.html'
    png_path  = rf'{artifact_dir}\{slug}.png'

    fig.write_html(html_path)
    print(f"  HTML: {html_path}")

    # Kaleido cannot serialize pd.Timestamp directly -- convert all x references to str
    import copy
    fig_copy = copy.deepcopy(fig)
    for shape in fig_copy.layout.shapes:
        if hasattr(shape, 'x0') and isinstance(shape.x0, pd.Timestamp):
            shape.x0 = shape.x0.isoformat()
        if hasattr(shape, 'x1') and isinstance(shape.x1, pd.Timestamp):
            shape.x1 = shape.x1.isoformat()
    for ann in fig_copy.layout.annotations:
        if hasattr(ann, 'x') and isinstance(ann.x, pd.Timestamp):
            ann.x = ann.x.isoformat()
    for trace in fig_copy.data:
        if hasattr(trace, 'x') and trace.x is not None:
            trace.x = [v.isoformat() if isinstance(v, pd.Timestamp) else v for v in trace.x]

    try:
        fig_copy.write_image(png_path, width=1400, height=650, scale=2)
        print(f"  PNG:  {png_path}")
    except Exception as e:
        print(f"  PNG failed: {e}")


print("\nDone.")
