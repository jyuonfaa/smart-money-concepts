import pandas as pd
import numpy as np
import plotly.graph_objects as go
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals, false_flag_signals
from risk_engine import calc_r_multiples

# ─── 1. Load Data ────────────────────────────────────────────────────────────
CSV_PATH = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

df_daily_dt = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_daily_ri_focus = df_daily_dt.loc['2016-10-01':'2016-11-15'].reset_index()

df_15m = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
df_4h = df_raw.resample('4h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

# ─── 2. Run Detectors ────────────────────────────────────────────────────────
daily_swings = smc.swing_highs_lows(df_daily_ri_focus, swing_length=5)
daily_ob     = smc.ob(df_daily_ri_focus, daily_swings)
daily_retracements = smc.retracements(df_daily_ri_focus, daily_swings)

daily_ohlc_time = df_daily_ri_focus.copy()
daily_ohlc_time.set_index('date', inplace=True)

swings_15m    = smc.swing_highs_lows(df_15m, swing_length=10)
reversals_15m = detect_reversals(df_15m, swings_15m)
consolidation_15m = smc.consolidation(df_15m, prd=10, conslen=5)
liq_15m = smc.liquidity(df_15m, swings_15m)
ts_15m = turtle_soup_signals(df_15m, reversals_15m, daily_ob, df_daily_ri_focus, liq_df=liq_15m, use_daily_ob_stop=False, refinement_level='15M')

df_daily = df_daily_dt

daily_swings = smc.swing_highs_lows(df_daily, swing_length=10)
daily_cons = smc.consolidation(df_daily)
daily_rets = smc.retracements(df_daily, daily_swings)
daily_ob_df = smc.ob(df_daily, daily_swings)
daily_reversals = detect_reversals(df_daily, daily_swings)
daily_liq = smc.liquidity(df_daily, daily_swings)
daily_ts = turtle_soup_signals(df_daily, daily_reversals,
    daily_ob_df, df_daily, liq_df=daily_liq)

swings_4h = smc.swing_highs_lows(df_4h, swing_length=10)
ob_4h = smc.ob(df_4h, swings_4h)
disp_4h = smc.displacement(df_4h)

ff_15m = false_flag_signals(
    ohlc_daily=df_daily,
    ohlc_ltf=df_15m,
    ohlc_4h=df_4h,
    daily_consolidation=daily_cons,
    daily_retracements=daily_rets,
    daily_turtle_soup=daily_ts,
    ob_4h=ob_4h,
    disp_4h=disp_4h
)

# ─── 3. Display & Signal Windows ─────────────────────────────────────────────
# Candles: Oct 15-30
FOCUS_START  = '2016-10-15'
FOCUS_END    = '2016-10-30'
# Signals: look back to Oct 15 so pre-window episodes project their lines forward
SIGNAL_START = '2016-10-15'

df_focus   = df_15m.loc[FOCUS_START:FOCUS_END].copy()
ff_signals = ff_15m.loc[SIGNAL_START:FOCUS_END].copy()   # wider slice for signals
ff_focus   = ff_15m.loc[FOCUS_START:FOCUS_END].copy()    # kept for reference
cons_focus = consolidation_15m.loc[FOCUS_START:FOCUS_END].copy()
ts_focus   = ts_15m.loc[FOCUS_START:FOCUS_END].copy()

# ─── 4. Subplot Construction ────────────────────────────────────────────────
fig = go.Figure()
BG_COLOR         = "#0f172a"
GRID_COLOR       = "#1e293b"
FONT_FAMILY      = "Courier New, monospace"

# Candlestick
fig.add_trace(go.Candlestick(
    x=df_focus.index,
    open=df_focus['open'], high=df_focus['high'],
    low=df_focus['low'], close=df_focus['close'],
    increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
    increasing_fillcolor='#26a69a', decreasing_fillcolor='#ef5350',
    name='15M OHLC', showlegend=False
))

# Shade Consolidation Zones (The Flags)
in_cons = False
cons_start = None
for ts, row in cons_focus.iterrows():
    is_active = not pd.isna(row['Consolidation']) and row['Consolidation'] > 0
    if is_active and not in_cons:
        in_cons = True
        cons_start = ts
    elif not is_active and in_cons:
        in_cons = False
        cons_end = ts
        top = cons_focus.loc[cons_start, 'Top']
        bot = cons_focus.loc[cons_start, 'Bottom']
        fig.add_shape(type="rect",
            x0=cons_start, x1=cons_end,
            y0=bot, y1=top,
            fillcolor="rgba(255, 235, 59, 0.1)",
            line=dict(color="rgba(255, 235, 59, 0.5)", width=1, dash="dot"),
        )

# ─── helpers ──────────────────────────────────────────────────────────────────
FOCUS_RIGHT = df_focus.index[-1]
FOCUS_LEFT  = df_focus.index[0]

def nearest_swing_low(daily_swings_raw, daily_idx, below_price, before_ts):
    daily_swings = daily_swings_raw.copy()
    daily_swings.index = daily_idx
    past = daily_swings[daily_swings.index <= before_ts]
    swing_lows = past[past['HighLow'] == -1]['Level']
    valid_lows = swing_lows[swing_lows < below_price]
    return valid_lows.max() if not valid_lows.empty else np.nan

def nearest_swing_high(daily_swings_raw, daily_idx, above_price, before_ts):
    daily_swings = daily_swings_raw.copy()
    daily_swings.index = daily_idx
    past = daily_swings[daily_swings.index <= before_ts]
    swing_highs = past[past['HighLow'] == 1]['Level']
    valid_highs = swing_highs[swing_highs > above_price]
    return valid_highs.min() if not valid_highs.empty else np.nan

def find_trade_end(df, start_ts, is_short, stop_price, tp1, tp2):
    future = df[df.index >= start_ts]
    for idx, row in future.iterrows():
        if is_short:
            if row['high'] >= stop_price or (pd.notna(tp1) and row['low'] <= tp1) or (pd.notna(tp2) and row['low'] <= tp2):
                return idx
        else:
            if row['low'] <= stop_price or (pd.notna(tp1) and row['high'] >= tp1) or (pd.notna(tp2) and row['high'] >= tp2):
                return idx
    return min(start_ts + pd.Timedelta(days=4), df.index[-1])

# ─── Plot FALSE BULL FLAG signals (Short Traps) ───────────────────────────────
# Use ff_signals so signals before Oct 24 still project their lines forward
bull_sigs = ff_signals[ff_signals['false_bull_flag']]
for sig_idx, (ts, row) in enumerate(bull_sigs.iterrows()):
    entry    = row['trap_entry']
    stop     = row['trap_stop_loss']
    cons_top = row.get('trap_cons_top', np.nan)
    cons_bot = row.get('trap_cons_bottom', np.nan)

    tp1 = cons_bot if pd.notna(cons_bot) else np.nan
    tp2 = nearest_swing_low(daily_swings, df_daily.index, below_price=tp1 if pd.notna(tp1) else entry, before_ts=ts)

    # Lines start at the later of signal time or FOCUS_LEFT
    ts_left  = max(ts, FOCUS_LEFT)
    
    # Lines end when target/stop hit, or cap at FOCUS_RIGHT
    trade_end_ts = find_trade_end(df_15m, ts, is_short=True, stop_price=stop, tp1=tp1, tp2=tp2)
    ts_right = min(trade_end_ts, FOCUS_RIGHT)

    # ── Risk Zone (entry → stop) shaded ──
    fig.add_shape(type="rect", x0=ts_left, x1=ts_right, y0=entry, y1=stop,
                  fillcolor="rgba(239,83,80,0.07)", line=dict(width=0))

    # ── Flag (consolidation) zone ──
    if pd.notna(cons_top) and pd.notna(cons_bot):
        flag_ts_left = ts - pd.Timedelta(minutes=30 * 15)
        fig.add_shape(type="rect", x0=flag_ts_left, x1=ts_left, y0=cons_bot, y1=cons_top,
                      fillcolor="rgba(255,215,0,0.12)",
                      line=dict(color="rgba(255,215,0,0.5)", width=1, dash="dot"))
        fig.add_annotation(x=flag_ts_left, y=cons_top, text="Flag Zone", showarrow=False,
                           font=dict(size=8, color="#ffd700", family=FONT_FAMILY),
                           xanchor="left", yanchor="bottom")

    # ── Entry ──
    fig.add_shape(type="line", x0=ts_left, x1=ts_right, y0=entry, y1=entry,
                  line=dict(color="#00e5ff", width=1.5, dash="dash"))
    fig.add_annotation(x=ts_right, y=entry, text=f"▶ ENTRY  {entry:.5f}",
                       showarrow=False, font=dict(size=9, color="#00e5ff", family=FONT_FAMILY),
                       xanchor="left", bgcolor="rgba(15,23,42,0.85)")

    # ── Stop Loss ──
    fig.add_shape(type="line", x0=ts_left, x1=ts_right, y0=stop, y1=stop,
                  line=dict(color="#ef5350", width=2, dash="dot"))
    fig.add_annotation(x=ts_right, y=stop, text=f"✕ STOP   {stop:.5f}",
                       showarrow=False, font=dict(size=9, color="#ef5350", family=FONT_FAMILY),
                       xanchor="left", bgcolor="rgba(15,23,42,0.85)")

    # ── TP1 ──
    if pd.notna(tp1):
        fig.add_shape(type="line", x0=ts_left, x1=ts_right, y0=tp1, y1=tp1,
                      line=dict(color="#a5d6a7", width=1.5, dash="dash"))
        fig.add_annotation(x=ts_right, y=tp1, text=f"TP1  {tp1:.5f}",
                           showarrow=False, font=dict(size=9, color="#a5d6a7", family=FONT_FAMILY),
                           xanchor="left", bgcolor="rgba(15,23,42,0.85)")

    # ── TP2 ──
    if pd.notna(tp2):
        fig.add_shape(type="line", x0=ts_left, x1=ts_right, y0=tp2, y1=tp2,
                      line=dict(color="#26a69a", width=2))
        fig.add_annotation(x=ts_right, y=tp2, text=f"TP2  {tp2:.5f}",
                           showarrow=False, font=dict(size=9, color="#26a69a", family=FONT_FAMILY),
                           xanchor="left", bgcolor="rgba(15,23,42,0.85)")

    # ── Signal Arrow ──
    arrow_y = df_focus.loc[ts, 'high'] if ts in df_focus.index else stop
    fig.add_annotation(
        x=ts, y=arrow_y, text="FALSE BULL FLAG (SHORT)",
        showarrow=True, arrowhead=2, arrowcolor="#ef5350",
        ax=0, ay=-50 - (sig_idx % 2 * 20),
        font=dict(size=10, color="#ef5350", family=FONT_FAMILY),
        bgcolor="rgba(15,23,42,0.9)", bordercolor="#ef5350", borderwidth=1
    )

# ─── Plot FALSE BEAR FLAG signals (Long Traps) ───────────────────────────────
bear_sigs = ff_signals[ff_signals['false_bear_flag']]
for sig_idx, (ts, row) in enumerate(bear_sigs.iterrows()):
    entry    = row['trap_entry']
    stop     = row['trap_stop_loss']
    cons_top = row.get('trap_cons_top', np.nan)
    cons_bot = row.get('trap_cons_bottom', np.nan)

    tp1 = cons_top if pd.notna(cons_top) else np.nan
    tp2 = nearest_swing_high(daily_swings, df_daily.index, above_price=tp1 if pd.notna(tp1) else entry, before_ts=ts)

    ts_left  = max(ts, FOCUS_LEFT)
    
    trade_end_ts = find_trade_end(df_15m, ts, is_short=False, stop_price=stop, tp1=tp1, tp2=tp2)
    ts_right = min(trade_end_ts, FOCUS_RIGHT)

    # ── Risk Zone ──
    fig.add_shape(type="rect", x0=ts_left, x1=ts_right, y0=stop, y1=entry,
                  fillcolor="rgba(239,83,80,0.07)", line=dict(width=0))

    # ── Flag Zone ──
    if pd.notna(cons_top) and pd.notna(cons_bot):
        flag_ts_left = ts - pd.Timedelta(minutes=30 * 15)
        fig.add_shape(type="rect", x0=flag_ts_left, x1=ts_left, y0=cons_bot, y1=cons_top,
                      fillcolor="rgba(0,229,255,0.10)",
                      line=dict(color="rgba(0,229,255,0.5)", width=1, dash="dot"))
        fig.add_annotation(x=flag_ts_left, y=cons_top, text="Flag Zone", showarrow=False,
                           font=dict(size=8, color="#00e5ff", family=FONT_FAMILY),
                           xanchor="left", yanchor="bottom")

    # ── Entry ──
    fig.add_shape(type="line", x0=ts_left, x1=ts_right, y0=entry, y1=entry,
                  line=dict(color="#00e5ff", width=1.5, dash="dash"))
    fig.add_annotation(x=ts_right, y=entry, text=f"▶ ENTRY  {entry:.5f}",
                       showarrow=False, font=dict(size=9, color="#00e5ff", family=FONT_FAMILY),
                       xanchor="left", bgcolor="rgba(15,23,42,0.85)")

    # ── Stop Loss ──
    fig.add_shape(type="line", x0=ts_left, x1=ts_right, y0=stop, y1=stop,
                  line=dict(color="#ef5350", width=2, dash="dot"))
    fig.add_annotation(x=ts_right, y=stop, text=f"✕ STOP   {stop:.5f}",
                       showarrow=False, font=dict(size=9, color="#ef5350", family=FONT_FAMILY),
                       xanchor="left", bgcolor="rgba(15,23,42,0.85)")

    # ── TP1 ──
    if pd.notna(tp1):
        fig.add_shape(type="line", x0=ts_left, x1=ts_right, y0=tp1, y1=tp1,
                      line=dict(color="#a5d6a7", width=1.5, dash="dash"))
        fig.add_annotation(x=ts_right, y=tp1, text=f"TP1  {tp1:.5f}",
                           showarrow=False, font=dict(size=9, color="#a5d6a7", family=FONT_FAMILY),
                           xanchor="left", bgcolor="rgba(15,23,42,0.85)")

    # ── TP2 ──
    if pd.notna(tp2):
        fig.add_shape(type="line", x0=ts_left, x1=ts_right, y0=tp2, y1=tp2,
                      line=dict(color="#26a69a", width=2))
        fig.add_annotation(x=ts_right, y=tp2, text=f"TP2  {tp2:.5f}",
                           showarrow=False, font=dict(size=9, color="#26a69a", family=FONT_FAMILY),
                           xanchor="left", bgcolor="rgba(15,23,42,0.85)")

    # ── Signal Arrow ──
    arrow_y = df_focus.loc[ts, 'low'] if ts in df_focus.index else stop
    fig.add_annotation(
        x=ts, y=arrow_y, text="FALSE BEAR FLAG (LONG)",
        showarrow=True, arrowhead=2, arrowcolor="#26a69a",
        ax=0, ay=50 + (sig_idx % 2 * 20),
        font=dict(size=10, color="#26a69a", family=FONT_FAMILY),
        bgcolor="rgba(15,23,42,0.9)", bordercolor="#26a69a", borderwidth=1
    )

fig.update_layout(
    title=dict(text="AUDUSD Month 2 Video 7 — Market Maker Trap (False Flags)", font=dict(size=14, color="#f8fafc", family=FONT_FAMILY)),
    template="plotly_dark", paper_bgcolor=BG_COLOR, plot_bgcolor=BG_COLOR, height=800,
    margin=dict(l=50, r=100, t=100, b=50),
    xaxis=dict(gridcolor=GRID_COLOR, rangeslider=dict(visible=False)),
    yaxis=dict(gridcolor=GRID_COLOR)
)

OUTPUT_FILE = "ICT_MONTH2_VIDEO7_FALSE_FLAG.html"
fig.write_html(OUTPUT_FILE)
print(f"Locked visual dashboard: {OUTPUT_FILE}")
