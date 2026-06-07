"""
visualize_month2_video2.py — ICT Month 2, Video 2: Fractal Refinement Dashboard

Three-pane Plotly dashboard. Pure Projection — zero logic here.
Pane 1 (1H):
  - Candlestick chart
  - Turtle Soup entry arrows — Rule of 3 (max 3 labels), staggered offsets, 48h spacing
  - Entry zone shaded (wick-high to bar-open)
  - Stop level (midpoint stop) — anchored to conf_ts, +80 bars right
  - R1-R5 levels — anchored to conf_ts, +80 bars right
  - Horizontal Daily OB anchor level line (red dashed reference)

Pane 2 (15M):
  - Candlestick chart
  - Turtle Soup entry arrows — Rule of 3, 12h spacing
  - Entry zone shaded
  - Stop level (Daily OB Bottom stop) — anchored to conf_ts, +80 bars right
  - R1-R5 levels — anchored to conf_ts, +80 bars right
  - Horizontal Daily OB anchor level line (red dashed reference)

Pane 3 (5M):
  - Candlestick chart
  - Turtle Soup entry arrows — Rule of 3, 4h spacing
  - Entry zone shaded
  - Stop level (Daily OB Bottom stop) — anchored to conf_ts, +80 bars right
  - R1-R5 levels — anchored to conf_ts, +80 bars right
  - Horizontal Daily OB anchor level line (red dashed reference)

Stable Output: ICT_MONTH2_VIDEO2_TURTLE_SOUP.html
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals
from risk_engine import calc_r_multiples, calc_rr

# ─── 1. Load Data ────────────────────────────────────────────────────────────

CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'

df_raw = pd.read_csv(CSV_PATH, sep=';',
    names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

# Daily (RangeIndex for smc.ob() compatibility)
df_daily_dt = df_raw.resample('1D').agg({
    'open':'first','high':'max','low':'min','close':'last','volume':'sum'
}).dropna()

# We run detection on the full Aug-Sep period to ensure lookback history is fully populated!
DETECTION_START = '2016-08-01'
DETECTION_END   = '2016-10-01'

df_daily_ri_focus = df_daily_dt.loc[DETECTION_START:DETECTION_END].reset_index()

df_1h_full  = df_1h  = df_raw.resample('1h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().loc[DETECTION_START:DETECTION_END]
df_15m_full = df_15m = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().loc[DETECTION_START:DETECTION_END]
df_5m_full  = df_5m  = df_raw.resample('5min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().loc[DETECTION_START:DETECTION_END]

# ─── 2. Run Detectors & State Machines on Full Aug-Sep Period ───────────────

# Daily OB Reference (Anchor)
daily_swings = smc.swing_highs_lows(df_daily_ri_focus, swing_length=5)
daily_ob     = smc.ob(df_daily_ri_focus, daily_swings)

# 1H Signals (use_daily_ob_stop = False)
swings_1h    = smc.swing_highs_lows(df_1h_full, swing_length=10)
reversals_1h = detect_reversals(df_1h_full, swings_1h)
ts_1h_full   = turtle_soup_signals(
    ohlc=df_1h_full, reversals=reversals_1h, daily_ob=daily_ob, daily_ohlc=df_daily_ri_focus,
    use_daily_ob_stop=False, refinement_level='1H'
)

# 15M Signals (use_daily_ob_stop = True)
swings_15m    = smc.swing_highs_lows(df_15m_full, swing_length=10)
reversals_15m = detect_reversals(df_15m_full, swings_15m)
ts_15m_full   = turtle_soup_signals(
    ohlc=df_15m_full, reversals=reversals_15m, daily_ob=daily_ob, daily_ohlc=df_daily_ri_focus,
    use_daily_ob_stop=True, refinement_level='15M'
)

# 5M Signals (use_daily_ob_stop = True)
swings_5m    = smc.swing_highs_lows(df_5m_full, swing_length=10)
reversals_5m = detect_reversals(df_5m_full, swings_5m)
ts_5m_full   = turtle_soup_signals(
    ohlc=df_5m_full, reversals=reversals_5m, daily_ob=daily_ob, daily_ohlc=df_daily_ri_focus,
    use_daily_ob_stop=True, refinement_level='5M'
)

# ─── 3. Slice to Focus Window (Aug 3–12) for Plotting ───────────────────────

FOCUS_START = '2016-08-03'
FOCUS_END   = '2016-08-12'

df_1h_focus  = df_1h_full.loc[FOCUS_START:FOCUS_END].copy()
df_15m_focus = df_15m_full.loc[FOCUS_START:FOCUS_END].copy()
df_5m_focus  = df_5m_full.loc[FOCUS_START:FOCUS_END].copy()

ts_1h_focus  = ts_1h_full.loc[FOCUS_START:FOCUS_END].copy()
ts_15m_focus = ts_15m_full.loc[FOCUS_START:FOCUS_END].copy()
ts_5m_focus  = ts_5m_full.loc[FOCUS_START:FOCUS_END].copy()

# Diagnose missing rendering (Change 3 console prints)
print(f"=== SIGNAL DIAGNOSTIC (Focus window {FOCUS_START} to {FOCUS_END}) ===")
print(f"1H Bearish signals  : {ts_1h_focus['turtle_soup_bear'].sum()}")
print(f"15M Bearish signals : {ts_15m_focus['turtle_soup_bear'].sum()}")
print(f"5M Bearish signals  : {ts_5m_focus['turtle_soup_bear'].sum()}")

# ─── 4. Subplot Construction (3-Pane) ────────────────────────────────────────

fig = make_subplots(
    rows=3, cols=1,
    vertical_spacing=0.06,
    subplot_titles=(
        "Pane 1: AUDUSD 1H Chart — 1H Scale (Midpoint Stops)",
        "Pane 2: AUDUSD 15M Chart — Refinement Level 15M (Daily OB Bottom Stops)",
        "Pane 3: AUDUSD 5M Chart — Refinement Level 5M (Daily OB Bottom Stops)"
    )
)

# Shared Stylings
BG_COLOR         = "#0f172a"
GRID_COLOR       = "#1e293b"
FONT_FAMILY      = "Courier New, monospace"
ENTRY_BEAR_COLOR = "rgba(0, 229, 255, 0.08)"
OB_BEAR_LINE     = "rgba(0, 229, 255, 0.4)"
STOP_COLOR       = "#ef5350"
R_LEVEL_COLOR    = "#26a69a"
GOLD_ANCHOR      = "rgba(255, 235, 59, 0.7)"

ob_ceiling = 0.76779
ob_floor   = 0.76352

# Helper function to plot a single pane's data
def plot_pane(df_focus, ts_signals, row_num, label_min_hours, bar_delta, right_delta):
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df_focus.index,
        open=df_focus['open'],   high=df_focus['high'],
        low=df_focus['low'],     close=df_focus['close'],
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
        increasing_fillcolor='#26a69a', decreasing_fillcolor='#ef5350',
        name=f'OHLC {row_num}', showlegend=False
    ), row=row_num, col=1)

    # Shaded horizontal band for Daily OB Reference across the entire pane
    fig.add_shape(type="rect",
        x0=df_focus.index[0], x1=df_focus.index[-1],
        y0=ob_floor, y1=ob_ceiling,
        fillcolor="rgba(255, 235, 59, 0.03)",
        line=dict(color="rgba(255, 235, 59, 0.2)", width=1, dash="dot"),
        row=row_num, col=1
    )

    # Annotate Daily OB Reference Line
    fig.add_annotation(
        x=df_focus.index[10], y=ob_ceiling,
        text="Daily Bearish OB Ceiling (0.76779)",
        showarrow=False,
        font=dict(size=8, color=GOLD_ANCHOR, family=FONT_FAMILY),
        xanchor="left", yanchor="bottom",
        row=row_num, col=1
    )
    fig.add_annotation(
        x=df_focus.index[10], y=ob_floor,
        text="Daily Bearish OB Floor (0.76352)",
        showarrow=False,
        font=dict(size=8, color=GOLD_ANCHOR, family=FONT_FAMILY),
        xanchor="left", yanchor="top",
        row=row_num, col=1
    )

    # Extract signals
    bear_sigs = ts_signals[ts_signals['turtle_soup_bear']].copy()
    
    # Apply Rule of 3 + temporal spacing
    signals_to_label = []
    last_label_ts = None
    for ts_val, row_val in bear_sigs.sort_index().iterrows():
        gap_ok = (last_label_ts is None or
                  (ts_val - last_label_ts).total_seconds() / 3600 >= label_min_hours)
        if gap_ok:
            signals_to_label.append((ts_val, row_val))
            last_label_ts = ts_val
        if len(signals_to_label) >= 3:
            break

    # Plot shapes and annotations for each labeled signal
    for sig_idx, (ts, row) in enumerate(signals_to_label):
        entry    = float(row['ts_ob_top'])
        stop     = float(row['ts_ob_stop'])
        zone_lo  = float(row['ts_ob_bottom'])
        zone_hi  = float(row['ts_ob_top'])
        r_levels = calc_r_multiples(entry, stop, max_r=5, bullish=False)

        ts_right = ts + right_delta
        ts_right = min(ts_right, df_focus.index[-1])
        ts_left  = max(ts - bar_delta, df_focus.index[0])

        # Shaded signal block (transposed OB entry zone)
        fig.add_shape(type="rect",
            x0=ts_left, x1=ts_right,
            y0=zone_lo, y1=zone_hi,
            fillcolor=ENTRY_BEAR_COLOR,
            line=dict(color=OB_BEAR_LINE, width=1.2, dash="dot"),
            row=row_num, col=1
        )

        # Stop loss line
        fig.add_shape(type="line",
            x0=ts_left, x1=ts_right, y0=stop, y1=stop,
            line=dict(color=STOP_COLOR, width=1.5, dash="dash"),
            row=row_num, col=1
        )
        fig.add_annotation(
            x=ts_right, y=stop,
            text=f"Stop: {stop:.5f}",
            showarrow=False,
            font=dict(size=8, color=STOP_COLOR, family=FONT_FAMILY),
            xanchor="left", yanchor="middle",
            row=row_num, col=1
        )

        # R-levels (R1-R5) dropping down for SHORT
        for r_idx, r_val in enumerate(r_levels):
            fig.add_shape(type="line",
                x0=ts_left, x1=ts_right, y0=r_val, y1=r_val,
                line=dict(color=R_LEVEL_COLOR, width=1, dash="dot"),
                row=row_num, col=1
            )
            if r_idx in [0, 2, 4]:  # label R1, R3, R5 to keep chart clean
                fig.add_annotation(
                    x=ts_right, y=r_val,
                    text=f"R{r_idx+1}: {r_val:.5f}",
                    showarrow=False,
                    font=dict(size=8, color=R_LEVEL_COLOR, family=FONT_FAMILY),
                    xanchor="left", yanchor="middle",
                    row=row_num, col=1
                )

        # Signal Marker Arrow
        fig.add_annotation(
            x=ts, y=df_focus.loc[ts, 'high'],
            text="TS BEAR SHORT",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#00e5ff",
            ax=0, ay=-40 - (sig_idx * 15), # staggered vertical offsets
            font=dict(size=9, color="#00e5ff", family=FONT_FAMILY),
            bgcolor="rgba(15, 23, 42, 0.9)",
            bordercolor="#00e5ff",
            borderwidth=1,
            row=row_num, col=1
        )

# Plot Pane 1 (1H):
# 48h spacing, 6h left shift, 80h right projection
plot_pane(
    df_focus          = df_1h_focus,
    ts_signals        = ts_1h_focus,
    row_num           = 1,
    label_min_hours   = 48,
    bar_delta         = pd.Timedelta(hours=6),
    right_delta       = pd.Timedelta(hours=80)
)

# Plot Pane 2 (15M):
# 12h spacing, 2h left shift, 20h right projection (80 bars * 15m = 20h)
plot_pane(
    df_focus          = df_15m_focus,
    ts_signals        = ts_15m_focus,
    row_num           = 2,
    label_min_hours   = 12,
    bar_delta         = pd.Timedelta(hours=2),
    right_delta       = pd.Timedelta(hours=20)
)

# Plot Pane 3 (5M):
# 4h spacing, 1h left shift, 6.67h right projection (80 bars * 5m = 400m = 6.67h)
plot_pane(
    df_focus          = df_5m_focus,
    ts_signals        = ts_5m_focus,
    row_num           = 3,
    label_min_hours   = 4,
    bar_delta         = pd.Timedelta(hours=1),
    right_delta       = pd.Timedelta(minutes=400)
)

# Layout adjustments
fig.update_layout(
    title=dict(
        text="AUDUSD Month 2 Video 2 — Fractal Refinement (1H vs 15M vs 5M Stops)",
        font=dict(size=14, color="#f8fafc", family=FONT_FAMILY)
    ),
    template="plotly_dark",
    paper_bgcolor=BG_COLOR,
    plot_bgcolor=BG_COLOR,
    height=1200,
    margin=dict(l=50, r=100, t=100, b=50),
    xaxis=dict(gridcolor=GRID_COLOR, rangeslider=dict(visible=False)),
    yaxis=dict(gridcolor=GRID_COLOR),
    xaxis2=dict(gridcolor=GRID_COLOR, rangeslider=dict(visible=False)),
    yaxis2=dict(gridcolor=GRID_COLOR),
    xaxis3=dict(gridcolor=GRID_COLOR, rangeslider=dict(visible=False)),
    yaxis3=dict(gridcolor=GRID_COLOR),
)

# Write output file
OUTPUT_FILE = "ICT_MONTH2_VIDEO2_TURTLE_SOUP.html"
fig.write_html(OUTPUT_FILE)
print(f"\nLocked visual dashboard: {OUTPUT_FILE}")
