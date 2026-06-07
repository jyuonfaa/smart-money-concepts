"""
visualize_month2_video3.py — ICT Month 2, Video 3: How Traders Make 10% Per Month

Three-pane Plotly dashboard.
Pane 1 (15M):
  - Candlestick chart
  - Turtle Soup entry arrows
  - Entry zone shaded
  - Stop level
  - Target ladder (ts_target_near, ts_target_far, ts_target_1h)

Pane 2 (5M):
  - Candlestick chart
  - Turtle Soup entry arrows
  - R1-R9 dotted lines
  - ts_target_near labeled as "9R Pool"

Pane 3 (1H):
  - Candlestick chart showing ts_target_1h

Stable Output: ICT_MONTH2_VIDEO3_TURTLE_SOUP.html
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals
from risk_engine import calc_r_multiples

# ─── 1. Load Data ────────────────────────────────────────────────────────────

CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'

df_raw = pd.read_csv(CSV_PATH, sep=';',
    names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

df_daily_dt = df_raw.resample('1D').agg({
    'open':'first','high':'max','low':'min','close':'last','volume':'sum'
}).dropna()

DETECTION_START = '2016-01-01'
DETECTION_END   = '2016-04-01'

df_daily_ri_focus = df_daily_dt.loc[DETECTION_START:DETECTION_END].reset_index()

df_1h_full  = df_raw.resample('1h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().loc[DETECTION_START:DETECTION_END]
df_15m_full = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().loc[DETECTION_START:DETECTION_END]
df_5m_full  = df_raw.resample('5min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().loc[DETECTION_START:DETECTION_END]

# ─── 2. Run Detectors & State Machines on Full Aug-Sep Period ───────────────

daily_swings = smc.swing_highs_lows(df_daily_ri_focus, swing_length=5)
daily_ob     = smc.ob(df_daily_ri_focus, daily_swings)

# We must generate swings BEFORE we can compute liquidity
swings_15m    = smc.swing_highs_lows(df_15m_full, swing_length=10)
swings_5m     = smc.swing_highs_lows(df_5m_full, swing_length=10)
swings_1h     = smc.swing_highs_lows(df_1h_full, swing_length=10)

# Compute liquidity for target generation
liq_15m = smc.liquidity(df_15m_full, swings_15m)
liq_15m.index = df_15m_full.index

liq_5m  = smc.liquidity(df_5m_full, swings_5m)
liq_5m.index = df_5m_full.index

liq_1h  = smc.liquidity(df_1h_full, swings_1h)
liq_1h.index = df_1h_full.index

# 15M Signals
reversals_15m = detect_reversals(df_15m_full, swings_15m)
ts_15m_full   = turtle_soup_signals(
    ohlc=df_15m_full, reversals=reversals_15m, daily_ob=daily_ob, daily_ohlc=df_daily_ri_focus,
    liq_df=liq_15m, use_daily_ob_stop=True, refinement_level='15M', liq_1h=liq_1h
)

# 5M Signals
reversals_5m = detect_reversals(df_5m_full, swings_5m)
ts_5m_full   = turtle_soup_signals(
    ohlc=df_5m_full, reversals=reversals_5m, daily_ob=daily_ob, daily_ohlc=df_daily_ri_focus,
    liq_df=liq_5m, use_daily_ob_stop=True, refinement_level='5M', liq_1h=liq_1h
)

# 1H Signals
reversals_1h = detect_reversals(df_1h_full, swings_1h)
ts_1h_full   = turtle_soup_signals(
    ohlc=df_1h_full, reversals=reversals_1h, daily_ob=daily_ob, daily_ohlc=df_daily_ri_focus,
    liq_df=liq_1h, use_daily_ob_stop=False, refinement_level='1H'
)

# ─── 3. Slice to Focus Window (Aug 3–12) for Plotting ───────────────────────

FOCUS_START = '2016-02-14'
FOCUS_END   = '2016-03-05'

df_1h_focus  = df_1h_full.loc[FOCUS_START:FOCUS_END].copy()
df_15m_focus = df_15m_full.loc[FOCUS_START:FOCUS_END].copy()
df_5m_focus  = df_5m_full.loc[FOCUS_START:FOCUS_END].copy()

ts_1h_focus  = ts_1h_full.loc[FOCUS_START:FOCUS_END].copy()
ts_15m_focus = ts_15m_full.loc[FOCUS_START:FOCUS_END].copy()
ts_5m_focus  = ts_5m_full.loc[FOCUS_START:FOCUS_END].copy()

# ─── 4. Subplot Construction (3-Pane) ────────────────────────────────────────

fig = make_subplots(
    rows=3, cols=1,
    vertical_spacing=0.06,
    subplot_titles=(
        "Pane 1: AUDUSD 15M Chart — Target Ladder (ts_target_near -> ts_target_far -> ts_target_1h)",
        "Pane 2: AUDUSD 5M Chart — R1 to R9 Ladder (50% scale at 3R)",
        "Pane 3: AUDUSD 1H Chart — 1H Pool Runner Objective"
    )
)

# Shared Stylings
BG_COLOR         = "#0f172a"
GRID_COLOR       = "#1e293b"
FONT_FAMILY      = "Courier New, monospace"
ENTRY_BULL_COLOR = "rgba(38, 166, 154, 0.08)"
OB_BULL_LINE     = "rgba(38, 166, 154, 0.4)"
STOP_COLOR       = "#ef5350"
R_LEVEL_COLOR    = "#26a69a"

LADDER_1 = "rgba(76, 175, 80, 0.4)"
LADDER_2 = "rgba(76, 175, 80, 0.7)"
LADDER_3 = "rgba(76, 175, 80, 1.0)"

def plot_pane(df_focus, ts_signals, row_num, label_min_hours, bar_delta, right_delta, draw_ladder=False, draw_r_levels=False):
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df_focus.index,
        open=df_focus['open'],   high=df_focus['high'],
        low=df_focus['low'],     close=df_focus['close'],
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
        increasing_fillcolor='#26a69a', decreasing_fillcolor='#ef5350',
        name=f'OHLC {row_num}', showlegend=False
    ), row=row_num, col=1)

    bull_sigs = ts_signals[ts_signals['turtle_soup_bull']].copy()
    
    signals_to_label = []
    last_label_ts = None
    for ts_val, row_val in bull_sigs.sort_index().iterrows():
        gap_ok = (last_label_ts is None or (ts_val - last_label_ts).total_seconds() / 3600 >= label_min_hours)
        if gap_ok:
            signals_to_label.append((ts_val, row_val))
            last_label_ts = ts_val
        if len(signals_to_label) >= 3:
            break

    for sig_idx, (ts, row) in enumerate(signals_to_label):
        entry    = float(row['ts_ob_bottom'])
        stop     = float(row['ts_ob_stop'])
        zone_lo  = float(row['ts_ob_bottom'])
        zone_hi  = float(row['ts_ob_top'])

        ts_right = ts + right_delta
        ts_right = min(ts_right, df_focus.index[-1])
        ts_left  = max(ts - bar_delta, df_focus.index[0])

        # Entry Zone
        fig.add_shape(type="rect",
            x0=ts_left, x1=ts_right, y0=zone_lo, y1=zone_hi,
            fillcolor=ENTRY_BULL_COLOR, line=dict(color=OB_BULL_LINE, width=1.2, dash="dot"),
            row=row_num, col=1
        )

        # Stop
        fig.add_shape(type="line",
            x0=ts_left, x1=ts_right, y0=stop, y1=stop,
            line=dict(color=STOP_COLOR, width=1.5, dash="dash"),
            row=row_num, col=1
        )

        if draw_r_levels:
            r_levels = calc_r_multiples(entry, stop, max_r=9, bullish=True)
            for r_idx, r_val in enumerate(r_levels):
                fig.add_shape(type="line",
                    x0=ts_left, x1=ts_right, y0=r_val, y1=r_val,
                    line=dict(color=R_LEVEL_COLOR, width=1, dash="dot"),
                    row=row_num, col=1
                )
                if (r_idx + 1 in [3, 9]) and (sig_idx == 0):
                    text = "3R — 3% Locked" if r_idx + 1 == 3 else "9R — Astonishing"
                    fig.add_annotation(
                        x=ts, y=r_val, text=text, showarrow=False,
                        font=dict(size=9, color=R_LEVEL_COLOR, family=FONT_FAMILY),
                        xanchor="left", yanchor="bottom", row=row_num, col=1
                    )

        if draw_ladder:
            t1 = float(row['ts_target_near'])
            t2 = float(row['ts_target_far'])
            t3 = float(row['ts_target_1h'])

            # Ladder lines
            for t_val, color, name in [(t1, LADDER_1, "Near Pool"), (t2, LADDER_2, "Far Pool"), (t3, LADDER_3, "1H Pool Runner")]:
                if not np.isnan(t_val):
                    fig.add_shape(type="line",
                        x0=ts_left, x1=ts_right, y0=t_val, y1=t_val,
                        line=dict(color=color, width=2, dash="dash"),
                        row=row_num, col=1
                    )
                    fig.add_annotation(
                        x=ts_right, y=t_val, text=name, showarrow=False,
                        font=dict(size=9, color=color, family=FONT_FAMILY),
                        xanchor="left", yanchor="middle", row=row_num, col=1
                    )
            
            # Capital Annotation Box
            fig.add_annotation(
                x=0.98, y=0.95, xref="x domain", yref="y domain",
                text="2% Risk → 3R = 3% banked → Runner to 1H Pool",
                showarrow=False, font=dict(size=12, color="#f8fafc", family=FONT_FAMILY),
                bgcolor="rgba(15, 23, 42, 0.9)", bordercolor=LADDER_3, borderwidth=1,
                row=row_num, col=1
            )

        # Arrow
        fig.add_annotation(
            x=ts, y=df_focus.loc[ts, 'low'], text="TS BULL", showarrow=True,
            arrowhead=2, arrowcolor="#00e5ff", ax=0, ay=40 + (sig_idx * 15),
            font=dict(size=9, color="#00e5ff", family=FONT_FAMILY),
            bgcolor="rgba(15, 23, 42, 0.9)", bordercolor="#00e5ff", borderwidth=1,
            row=row_num, col=1
        )

# Plot Pane 1 (15M) — Target Ladder
plot_pane(df_15m_focus, ts_15m_focus, 1, 12, pd.Timedelta(hours=2), pd.Timedelta(hours=48), draw_ladder=True)

# Plot Pane 2 (5M) — R levels up to 9R
plot_pane(df_5m_focus, ts_5m_focus, 2, 4, pd.Timedelta(hours=1), pd.Timedelta(hours=24), draw_r_levels=True)

# Plot Pane 3 (1H) — 1H targets
plot_pane(df_1h_focus, ts_1h_focus, 3, 48, pd.Timedelta(hours=6), pd.Timedelta(hours=96), draw_ladder=True)

fig.update_layout(
    title=dict(text="AUDUSD Month 2 Video 3 — How Traders Make 10% Per Month", font=dict(size=14, color="#f8fafc", family=FONT_FAMILY)),
    template="plotly_dark", paper_bgcolor=BG_COLOR, plot_bgcolor=BG_COLOR,
    height=1200, margin=dict(l=50, r=100, t=100, b=50),
    xaxis=dict(gridcolor=GRID_COLOR, rangeslider=dict(visible=False)),
    yaxis=dict(gridcolor=GRID_COLOR),
    xaxis2=dict(gridcolor=GRID_COLOR, rangeslider=dict(visible=False)),
    yaxis2=dict(gridcolor=GRID_COLOR),
    xaxis3=dict(gridcolor=GRID_COLOR, rangeslider=dict(visible=False)),
    yaxis3=dict(gridcolor=GRID_COLOR),
)

OUTPUT_FILE = "ICT_MONTH2_VIDEO3_TURTLE_SOUP.html"
fig.write_html(OUTPUT_FILE)
print(f"\\nLocked visual dashboard: {OUTPUT_FILE}")
