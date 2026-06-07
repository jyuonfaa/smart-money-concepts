"""
visualize_month2_video1.py — ICT Month 2, Video 1: Turtle Soup + Daily OB Dashboard

Two-pane Plotly dashboard. Pure Projection — zero logic here.

Pane 1 (Daily):
  - Candlestick
  - OB zone as shaded box (ENTRY ZONE only: open→high for bull, low→open for bear)
  - Equal-high buy stop clusters from smc.liquidity() IsTooClean flag (gold dotted)

Pane 2 (1H):
  - Candlestick
  - Turtle Soup entry arrows — Rule of 3: max 3 labels, staggered y-offsets
  - Daily OB entry zone shaded (transposed from daily — uses ts_ob_bottom/top)
  - Stop level line (OB body midpoint — red dashed) — anchored to conf_ts, +80 bars right
  - R1-R5 levels as green dotted lines — anchored to conf_ts, +80 bars right
  - 1H equal-high clusters from smc.liquidity() IsTooClean (gold dotted, buy stop targets)
  - "Daily Bullish Orderblock" label at OB zone

FIX LOG vs previous version:
  Gap 2:    entry price now uses ts_ob_bottom (= bar.open) for bull, ts_ob_top for bear
  Issue A:  label deduplication — Rule of 3, max 3 labels, staggered y-offsets
  Issue B:  R-level lines anchored to signal conf_ts + 80-bar right cutoff (not chart-wide)
  Gap 6:    1H buy stop targets now use actual smc.liquidity() IsTooClean clusters

Golden Master output: ICT_MONTH2_VIDEO1_TURTLE_SOUP.html
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals
from risk_engine import calc_ob_stop, calc_r_multiples, calc_rr, get_exit_schedule

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
df_daily_ri = df_daily_dt.reset_index()   # RangeIndex version

# 1H
df_1h = df_raw.resample('1h').agg({
    'open':'first','high':'max','low':'min','close':'last','volume':'sum'
}).dropna()

# Focus window: Aug–Sept 2016
FOCUS_START = '2016-08-01'
FOCUS_END   = '2016-10-01'
df_daily_focus    = df_daily_dt.loc[FOCUS_START:FOCUS_END].copy()
df_daily_ri_focus = df_daily_ri[
    (df_daily_ri['date'] >= FOCUS_START) & (df_daily_ri['date'] <= FOCUS_END)
].reset_index(drop=True)
df_1h_focus = df_1h.loc[FOCUS_START:FOCUS_END].copy()

print(f"Daily bars : {len(df_daily_focus)}")
print(f"1H bars    : {len(df_1h_focus)}")

# ─── 2. Detectors ────────────────────────────────────────────────────────────

# Daily OBs
daily_swings = smc.swing_highs_lows(df_daily_ri_focus, swing_length=5)
daily_ob     = smc.ob(df_daily_ri_focus, daily_swings)

# Daily equal highs / buy stop clusters
daily_liq    = smc.liquidity(df_daily_ri_focus, daily_swings)

# 1H swings + reversals
h1_swings    = smc.swing_highs_lows(df_1h_focus, swing_length=10)
reversals_1h = detect_reversals(df_1h_focus, h1_swings)

# 1H equal highs / buy stop clusters (structural levels, not R-projections)
h1_liq = smc.liquidity(df_1h_focus, h1_swings)

# Turtle Soup — pass h1_liq so ts_target_near/far are populated (ICT page 60)
ts_df = turtle_soup_signals(
    ohlc       = df_1h_focus,
    reversals  = reversals_1h,
    daily_ob   = daily_ob,
    daily_ohlc = df_daily_ri_focus,
    liq_df     = h1_liq,
)

# ─── 3. Data Audit Console Print (Gatekeeper Check 1) ────────────────────────

bull_signals = ts_df[ts_df['turtle_soup_bull']].copy()
bear_signals = ts_df[ts_df['turtle_soup_bear']].copy()
all_signals  = pd.concat([bull_signals, bear_signals]).sort_index()

schedule = get_exit_schedule()

print("\n=== TURTLE SOUP SIGNAL AUDIT (post Gap 1+2 fix) ===")
print(f"{'Timestamp':<22} {'Dir':>5} {'EntryZone_Lo':>13} {'EntryZone_Hi':>13} "
      f"{'Stop':>9} {'Entry':>9} {'R1':>9} {'R2':>9} {'R3':>9} {'R4':>9} {'R5':>9}")
for ts, row in all_signals.iterrows():
    is_bull   = row['turtle_soup_bull']
    direction = 'BULL' if is_bull else 'BEAR'
    entry        = float(row['ts_ob_bottom']) if is_bull else float(row['ts_ob_top'])
    stop         = float(row['ts_ob_stop'])
    zone_lo      = float(row['ts_ob_bottom'])
    zone_hi      = float(row['ts_ob_top'])
    tgt_near     = float(row['ts_target_near']) if not pd.isna(row['ts_target_near']) else float('nan')
    tgt_far      = float(row['ts_target_far'])  if not pd.isna(row['ts_target_far'])  else float('nan')
    # Fix: pass bullish explicitly — do not infer direction from stop position
    r_levels     = calc_r_multiples(entry, stop, max_r=5, bullish=is_bull)
    print(f"{str(ts)[:22]:<22} {direction:>5} {zone_lo:>13.5f} {zone_hi:>13.5f} "
          f"{stop:>9.5f} {entry:>9.5f} "
          + " ".join(f"{r:>9.5f}" for r in r_levels)
          + f"  TgtNear={tgt_near:.5f}" if not pd.isna(tgt_near) else
          f"{str(ts)[:22]:<22} {direction:>5} {zone_lo:>13.5f} {zone_hi:>13.5f} "
          f"{stop:>9.5f} {entry:>9.5f} "
          + " ".join(f"{r:>9.5f}" for r in r_levels)
          + "  TgtNear=n/a")

print(f"\nTotal: BULL={len(bull_signals)}, BEAR={len(bear_signals)}")
print(f"\nExit schedule:")
for r, v in schedule.items():
    print(f"  R{r}: {v['note']}")

# ─── 4. Build Two-Pane Dashboard ─────────────────────────────────────────────

DARK_BG     = "#0b0f19"
GRID_COLOR  = "#1c2333"
TEXT_COLOR  = "#ffffff"
SUB_COLOR   = "#b0bec5"
FONT_FAMILY = "Outfit, sans-serif"

OB_BULL_COLOR   = "rgba(38, 166, 154, 0.20)"
OB_BULL_LINE    = "#26a69a"
OB_BEAR_COLOR   = "rgba(239, 83, 80, 0.20)"
OB_BEAR_LINE    = "#ef5350"
STOP_COLOR      = "#ff5252"
R_COLORS_HEX    = ["#a5d6a7","#81c784","#66bb6a","#4caf50","#388e3c"]
BUY_STOP_COLOR  = "#ffca28"
ENTRY_BULL_COLOR = "rgba(41, 182, 246, 0.15)"
ENTRY_BEAR_COLOR = "rgba(239, 83, 80, 0.15)"

# 1H bar width in fractional days (for right-cutoff anchoring — Issue B fix)
H1_BAR_DAYS  = 1.0 / 24.0
RIGHT_BARS   = 80  # R-levels extend 80 bars (80 hours) to the right of signal

fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=False,
    subplot_titles=["AUDUSD Daily — Order Block Entry Zones + Buy Stop Clusters",
                    "AUDUSD 1H — Turtle Soup Entry + R1-R5 + Buy Stop Targets"],
    vertical_spacing=0.08,
    row_heights=[0.38, 0.62]
)

# ─── PANE 1: Daily ───────────────────────────────────────────────────────────

fig.add_trace(go.Candlestick(
    x=df_daily_focus.index,
    open=df_daily_focus['open'],   high=df_daily_focus['high'],
    low=df_daily_focus['low'],     close=df_daily_focus['close'],
    increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
    increasing_fillcolor='#26a69a', decreasing_fillcolor='#ef5350',
    name='AUDUSD Daily', showlegend=False,
), row=1, col=1)

# Draw daily OB ENTRY ZONES (Gap 2 fix: open→high for bull, low→open for bear)
for i in range(len(daily_ob)):
    ob_row  = daily_ob.iloc[i]
    bar_row = df_daily_ri_focus.iloc[i]
    if pd.isna(ob_row['OB']):
        continue
    date_val = bar_row['date']
    end_date = date_val + pd.Timedelta(days=12)
    is_bull  = (ob_row['OB'] == 1.0)

    if is_bull:
        # Entry zone: open of down candle → high (green zone)
        zone_lo = float(bar_row['open'])
        zone_hi = float(ob_row['Top'])
        fill    = OB_BULL_COLOR
        border  = OB_BULL_LINE
        label   = "Daily Bullish OB (Entry Zone)"
    else:
        # Entry zone: low → open of up candle (red zone)
        zone_lo = float(ob_row['Bottom'])
        zone_hi = float(bar_row['open'])
        fill    = OB_BEAR_COLOR
        border  = OB_BEAR_LINE
        label   = "Daily Bearish OB (Entry Zone)"

    fig.add_shape(type="rect",
        x0=date_val, x1=end_date, y0=zone_lo, y1=zone_hi,
        fillcolor=fill, line=dict(color=border, width=1.5, dash="dot"),
        row=1, col=1
    )
    fig.add_annotation(
        x=date_val, y=zone_hi,
        text=label, showarrow=False,
        font=dict(size=9, color=border, family=FONT_FAMILY),
        xanchor="left", yanchor="bottom",
        row=1, col=1
    )

# Daily equal-high buy stop clusters (IsTooClean == 1 bullish = equal highs)
for i in range(len(daily_liq)):
    liq_row = daily_liq.iloc[i]
    if pd.isna(liq_row['Liquidity']) or liq_row['IsTooClean'] != 1:
        continue
    if liq_row['Liquidity'] != 1.0:  # only bullish equal highs as buy stops
        continue
    level      = float(liq_row['Level'])
    date_start = df_daily_ri_focus.iloc[i]['date']
    end_idx    = min(i + 25, len(df_daily_ri_focus) - 1)
    date_end   = df_daily_ri_focus.iloc[end_idx]['date']

    fig.add_shape(type="line",
        x0=date_start, x1=date_end, y0=level, y1=level,
        line=dict(color=BUY_STOP_COLOR, width=1.5, dash="dot"),
        row=1, col=1
    )
    fig.add_annotation(
        x=date_end, y=level,
        text="Buy Stops", showarrow=False,
        font=dict(size=9, color=BUY_STOP_COLOR, family=FONT_FAMILY),
        xanchor="left",
        row=1, col=1
    )

# ─── PANE 2: 1H ──────────────────────────────────────────────────────────────

fig.add_trace(go.Candlestick(
    x=df_1h_focus.index,
    open=df_1h_focus['open'],   high=df_1h_focus['high'],
    low=df_1h_focus['low'],     close=df_1h_focus['close'],
    increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
    increasing_fillcolor='#26a69a', decreasing_fillcolor='#ef5350',
    name='AUDUSD 1H', showlegend=False,
), row=2, col=1)

# 1H buy stop clusters (Gap 6: actual structural equal highs, not R-projections)
h1_liq_plotted = 0
for i in range(len(h1_liq)):
    liq_row = h1_liq.iloc[i]
    if pd.isna(liq_row['Liquidity']) or liq_row['IsTooClean'] != 1:
        continue
    if liq_row['Liquidity'] != 1.0:  # bullish equal highs = buy stops
        continue
    level      = float(liq_row['Level'])
    ts_start   = df_1h_focus.index[i]
    end_idx    = min(i + 80, len(df_1h_focus) - 1)
    ts_end_liq = df_1h_focus.index[end_idx]

    fig.add_shape(type="line",
        x0=ts_start, x1=ts_end_liq, y0=level, y1=level,
        line=dict(color=BUY_STOP_COLOR, width=1.2, dash="dot"),
        row=2, col=1
    )
    h1_liq_plotted += 1

print(f"\n1H buy stop clusters plotted: {h1_liq_plotted}")

# Fix 2: enforce minimum 48h timestamp gap between labels (not just y-stagger)
# This prevents horizontal crowding of labels on the same OB cluster
MIN_LABEL_HOURS = 48
signals_to_label = []
last_label_ts    = None
for ts_val, row_val in all_signals.sort_index().iterrows():
    gap_ok = (last_label_ts is None or
              (ts_val - last_label_ts).total_seconds() / 3600 >= MIN_LABEL_HOURS)
    if gap_ok:
        signals_to_label.append((ts_val, row_val))
        last_label_ts = ts_val
    if len(signals_to_label) >= 3:   # Rule of 3
        break

print(f"\nLabels to display: {len(signals_to_label)} "
      f"({[str(t)[:16] for t, _ in signals_to_label]})")

label_ay_offsets = [-50, -80, -50]   # vertical stagger (still used for the remaining labels)

for sig_idx, (ts, row) in enumerate(signals_to_label):
    is_bull  = row['turtle_soup_bull']
    entry    = float(row['ts_ob_bottom']) if is_bull else float(row['ts_ob_top'])
    stop     = float(row['ts_ob_stop'])
    zone_lo  = float(row['ts_ob_bottom'])
    zone_hi  = float(row['ts_ob_top'])
    # Fix 1: pass bullish explicitly so SHORT R-levels go DOWN, not UP
    r_levels = calc_r_multiples(entry, stop, max_r=5, bullish=is_bull)

    # Issue B: anchor right cutoff to conf_ts + 80 bars (not chart-wide)
    ts_right = ts + pd.Timedelta(hours=RIGHT_BARS)
    # Clip to chart boundary
    ts_right = min(ts_right, df_1h_focus.index[-1])
    ts_left  = max(ts - pd.Timedelta(hours=6), df_1h_focus.index[0])

    is_color = "#ffeb3b" if is_bull else "#00e5ff"
    fill     = ENTRY_BULL_COLOR if is_bull else ENTRY_BEAR_COLOR
    border   = OB_BULL_LINE    if is_bull else OB_BEAR_LINE
    label    = "TURTLE SOUP LONG" if is_bull else "TURTLE SOUP SHORT"

    # OB entry zone on 1H (uses corrected zone_lo/hi = open-anchored)
    fig.add_shape(type="rect",
        x0=ts_left, x1=ts_right,
        y0=zone_lo, y1=zone_hi,
        fillcolor=fill,
        line=dict(color=border, width=1.5, dash="dot"),
        row=2, col=1
    )
    fig.add_annotation(
        x=ts_left, y=zone_lo,
        text="Daily Bullish Orderblock" if is_bull else "Daily Bearish Orderblock",
        showarrow=False,
        font=dict(size=9, color=border, family=FONT_FAMILY),
        xanchor="left", yanchor="top",
        row=2, col=1
    )

    # Stop line — anchored: ts_left to ts_right only (Issue B)
    fig.add_shape(type="line",
        x0=ts_left, x1=ts_right, y0=stop, y1=stop,
        line=dict(color=STOP_COLOR, width=1.5, dash="dash"),
        row=2, col=1
    )
    fig.add_annotation(
        x=ts_right, y=stop,
        text="Stop (OB Body Mid)", showarrow=False,
        font=dict(size=8, color=STOP_COLOR, family=FONT_FAMILY),
        xanchor="left",
        row=2, col=1
    )

    # R1–R5 lines — anchored: ts to ts_right (Issue B fix)
    r_names  = ["R1", "R2", "R3", "R4 (BE)", "R5 (Exit)"]
    for r_idx, (r_price, r_name, r_color) in enumerate(zip(r_levels, r_names, R_COLORS_HEX)):
        fig.add_shape(type="line",
            x0=ts, x1=ts_right, y0=r_price, y1=r_price,
            line=dict(color=r_color, width=1.2, dash="dot"),
            row=2, col=1
        )
        fig.add_annotation(
            x=ts_right, y=r_price,
            text=r_name, showarrow=False,
            font=dict(size=8, color=r_color, family=FONT_FAMILY),
            xanchor="left",
            row=2, col=1
        )

    # Entry arrow — Fix 2: staggered ay per label index (horizontal spacing enforced upstream)
    y_anchor = entry
    ay_val   = label_ay_offsets[sig_idx] if is_bull else -label_ay_offsets[sig_idx]

    fig.add_annotation(
        x=ts, y=y_anchor,
        text=label,
        ax=0, ay=ay_val,
        showarrow=True, arrowhead=3, arrowsize=1.2, arrowwidth=2,
        arrowcolor=is_color,
        bgcolor="rgba(11, 15, 25, 0.95)",
        bordercolor=is_color,
        borderwidth=1, borderpad=4,
        font=dict(color="white", size=10, family=FONT_FAMILY),
        row=2, col=1
    )

# ─── 5. Layout ───────────────────────────────────────────────────────────────

fig.update_layout(
    title=dict(
        text="ICT MONTH 2 VIDEO 1 — TURTLE SOUP + DAILY ORDER BLOCK [AUDUSD 2016]<br>"
             "<sup>Entry Zone: Open to High (ICT Green Zone) | Stop: OB Body Midpoint | R1-R5 Anchored</sup>",
        font=dict(size=16, color=TEXT_COLOR, family=FONT_FAMILY),
        x=0.04, y=0.98
    ),
    plot_bgcolor=DARK_BG,
    paper_bgcolor=DARK_BG,
    height=1100,
    margin=dict(l=60, r=130, t=90, b=60),
    showlegend=False,
)

for axis_key in ['xaxis', 'xaxis2']:
    fig.update_layout(**{axis_key: dict(
        tickfont=dict(color=SUB_COLOR),
        gridcolor=GRID_COLOR,
        rangeslider=dict(visible=False),
        type='date'
    )})

for axis_key in ['yaxis', 'yaxis2']:
    fig.update_layout(**{axis_key: dict(
        tickfont=dict(color=SUB_COLOR),
        gridcolor=GRID_COLOR,
        tickformat='.5f'
    )})

# Fix subplot title colors
for ann in fig.layout.annotations:
    if ann.text and ann.text.startswith("AUDUSD"):
        ann.font.color = SUB_COLOR

# ─── 6. Save ─────────────────────────────────────────────────────────────────

OUTPUT_HTML = "ICT_MONTH2_VIDEO1_TURTLE_SOUP.html"
fig.write_html(OUTPUT_HTML)
print(f"\nGolden Master saved: {OUTPUT_HTML}")
print(f"Absolute path: d:\\C.Slim\\ict-intelligence\\{OUTPUT_HTML}")
