import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from smartmoneyconcepts import smc

print("Downloading data for 15-minute USD/CHF chart...")
timeframe = "15m"
ohlc = yf.download("USDCHF=X", interval=timeframe, period="1mo", progress=False)

if isinstance(ohlc.columns, pd.MultiIndex):
    ohlc.columns = ohlc.columns.get_level_values(0)
ohlc.columns = [c.lower() for c in ohlc.columns]
ohlc = ohlc[['open', 'high', 'low', 'close', 'volume']]
ohlc.index = pd.to_datetime(ohlc.index).tz_localize(None)

print("Calculating indicators...")

# ─── Layer 2: Detection ─────────────────────────────────────────────────

# Swing structure
swing_hl = smc.swing_highs_lows(ohlc, swing_length=10)
swing_hl.index = ohlc.index

# Fair Value Gaps (coupled with Retracement)
fvg = smc.fvg(ohlc, join_consecutive=False)
fvg.index = ohlc.index

# Consolidation (ZigZag pivot approach)
cons = smc.consolidation(ohlc, prd=10, conslen=5)
cons.index = ohlc.index

# Expansion (displacement candle + OB)
exp = smc.expansion(ohlc, cons)
exp.index = ohlc.index

# Reversals (stop run: wick beyond swing level, body closes back inside)
from smartmoneyconcepts.state_machine import detect_reversals, PriceDeliveryStateMachine
rev = detect_reversals(ohlc, swing_hl)
rev.index = ohlc.index

# ─── Layer 5: State Machine ─────────────────────────────────────────────

pdsm = PriceDeliveryStateMachine()
state_results = pdsm.process(
    ohlc, cons, exp,
    fvg=fvg,
    reversals=rev,
)
state_results.index = ohlc.index

print("Building chart...")

fig = go.Figure()

# ─── Candlesticks ────────────────────────────────────────────────────────

fig.add_trace(go.Candlestick(
    x=ohlc.index,
    open=ohlc['open'], high=ohlc['high'],
    low=ohlc['low'], close=ohlc['close'],
    name='USDJPY'
))

# ─── Profit Objectives ──────────────────────────────────────────────────

tp1 = state_results[state_results['TP1'].notna()]
if not tp1.empty:
    fig.add_trace(go.Scatter(
        x=tp1.index, y=tp1['TP1'],
        mode='lines',
        line=dict(color='rgba(0, 255, 0, 0.4)', width=1, dash='dot'),
        name='TP1 (50% Extension)'
    ))

tp2 = state_results[state_results['TP2'].notna()]
if not tp2.empty:
    fig.add_trace(go.Scatter(
        x=tp2.index, y=tp2['TP2'],
        mode='lines',
        line=dict(color='rgba(0, 255, 0, 0.6)', width=1, dash='dash'),
        name='TP2 (100% Extension)'
    ))
    
# ─── Equilibrium ────────────────────────────────────────────────────────

eq_line = state_results[state_results['Equilibrium'].notna()]
if not eq_line.empty:
    fig.add_trace(go.Scatter(
        x=eq_line.index, y=eq_line['Equilibrium'],
        mode='lines',
        line=dict(color='rgba(255, 255, 255, 0.5)', width=1, dash='dashdot'),
        name='Equilibrium (50% Range)'
    ))

# ─── Breakout Markers ───────────────────────────────────────────────────

break_long = cons[cons['BreakLong'].notna()]
if not break_long.empty:
    fig.add_trace(go.Scatter(
        x=break_long.index,
        y=ohlc.loc[break_long.index, 'high'],
        mode='markers',
        marker=dict(symbol='triangle-up', size=14, color='cyan',
                    line=dict(color='white', width=1)),
        name='Breakout Long'
    ))

break_short = cons[cons['BreakShort'].notna()]
if not break_short.empty:
    fig.add_trace(go.Scatter(
        x=break_short.index,
        y=ohlc.loc[break_short.index, 'low'],
        mode='markers',
        marker=dict(symbol='triangle-down', size=14, color='orange',
                    line=dict(color='white', width=1)),
        name='Breakout Short'
    ))

# ─── FVG Boxes ──────────────────────────────────────────────────────────

fvg_shapes = []
for idx in fvg[fvg['FVG'].notna()].index:
    row = fvg.loc[idx]
    color = 'rgba(0, 200, 100, 0.12)' if row['FVG'] == 1.0 else 'rgba(200, 50, 50, 0.12)'
    border = 'rgba(0, 200, 100, 0.3)' if row['FVG'] == 1.0 else 'rgba(200, 50, 50, 0.3)'
    mit = int(row['MitigatedIndex'])
    if mit > 0 and mit < len(ohlc):
        end_idx = ohlc.index[mit]
    else:
        end_idx = ohlc.index[min(len(ohlc)-1, ohlc.index.get_loc(idx) + 20)]
    fvg_shapes.append(dict(
        type="rect", x0=idx, y0=row['Bottom'], x1=end_idx, y1=row['Top'],
        fillcolor=color, line=dict(color=border, width=0.5), layer="below"
    ))

# ─── Reversal Markers (magenta diamonds) + OB boxes (orange) ────────────

rev_active = rev[rev['Reversal'].notna()]
rev_ob_shapes = []

if not rev_active.empty:
    # Diamonds at reversal candles
    bull_rev = rev_active[rev_active['Reversal'] == 1.0]
    if not bull_rev.empty:
        fig.add_trace(go.Scatter(
            x=bull_rev.index,
            y=ohlc.loc[bull_rev.index, 'low'],
            mode='markers',
            marker=dict(symbol='diamond', size=12, color='magenta',
                        line=dict(color='white', width=1)),
            name='Bullish Reversal (Stop Run)'
        ))
    
    bear_rev = rev_active[rev_active['Reversal'] == -1.0]
    if not bear_rev.empty:
        fig.add_trace(go.Scatter(
            x=bear_rev.index,
            y=ohlc.loc[bear_rev.index, 'high'],
            mode='markers',
            marker=dict(symbol='diamond', size=12, color='magenta',
                        line=dict(color='white', width=1)),
            name='Bearish Reversal (Stop Run)'
        ))
    
    # Orange OB boxes at each reversal
    for idx in rev_active.index:
        row = rev_active.loc[idx]
        if not pd.isna(row['OB_Top']) and not pd.isna(row['OB_Bottom']):
            # Box extends 10 bars forward from reversal
            end_pos = min(len(ohlc)-1, ohlc.index.get_loc(idx) + 10)
            end_dt = ohlc.index[end_pos]
            rev_ob_shapes.append(dict(
                type="rect", x0=idx, y0=row['OB_Bottom'], x1=end_dt, y1=row['OB_Top'],
                fillcolor="rgba(255, 165, 0, 0.2)",
                line=dict(color="rgba(255, 165, 0, 0.6)", width=1),
                layer="below"
            ))

# ─── State Bar ───────────────────────────────────────────────────────────

state_colors = {
    'consolidation': 'grey',
    'expansion': 'blue',
    'retracement': 'yellow',
    'reversal': 'red',
    'unknown': 'white',
}
for state in state_results['State'].unique():
    mask = state_results[state_results['State'] == state]
    if not mask.empty:
        fig.add_trace(go.Scatter(
            x=mask.index,
            y=[ohlc['low'].min() * 0.99] * len(mask),
            mode='markers',
            marker=dict(symbol='square', size=5,
                        color=state_colors.get(state, 'white')),
            name=f'State: {state}'
        ))

# ─── Swing Highs and Lows ───────────────────────────────────────────────

highs = swing_hl[swing_hl['HighLow'] == 1.0]
fig.add_trace(go.Scatter(
    x=highs.index, y=highs['Level'],
    mode='markers',
    marker=dict(symbol='triangle-down', size=12, color='red'),
    name='Swing High'
))

lows = swing_hl[swing_hl['HighLow'] == -1.0]
fig.add_trace(go.Scatter(
    x=lows.index, y=lows['Level'],
    mode='markers',
    marker=dict(symbol='triangle-up', size=12, color='lime'),
    name='Swing Low'
))

# ─── Consolidation Boxes ────────────────────────────────────────────────

cons_shapes = []

def draw_consolidation(s, e, top, bottom, eq, ote_h, ote_l):
    cons_shapes.append(dict(
        type="rect", x0=s, y0=bottom, x1=e, y1=top,
        fillcolor="rgba(128,128,128,0.1)",
        line=dict(color="rgba(128,128,128,0.3)", width=1), layer="below"
    ))
    cons_shapes.append(dict(
        type="rect", x0=s, y0=ote_l, x1=e, y1=ote_h,
        fillcolor="rgba(0,191,255,0.2)",
        line=dict(width=0), layer="below"
    ))
    cons_shapes.append(dict(
        type="line", x0=s, y0=eq, x1=e, y1=eq,
        line=dict(color="rgba(255,255,255,0.6)", width=1, dash="dot"),
        layer="below"
    ))

in_cons = False
s_time = locked_t = locked_b = locked_eq = locked_oh = locked_ol = None
prev_dt = ohlc.index[0]

for dt, row in cons.iterrows():
    is_c = not pd.isna(row['Consolidation'])
    if is_c and not in_cons:
        in_cons = True
        s_time = dt
        locked_t = row['Top']
        locked_b = row['Bottom']
        locked_eq = row['Equilibrium']
        locked_oh = row['OTE_High']
        locked_ol = row['OTE_Low']
    elif not is_c and in_cons:
        draw_consolidation(s_time, prev_dt, locked_t, locked_b, locked_eq, locked_oh, locked_ol)
        in_cons = False
    prev_dt = dt

if in_cons:
    draw_consolidation(s_time, prev_dt, locked_t, locked_b, locked_eq, locked_oh, locked_ol)

# ─── Layout ─────────────────────────────────────────────────────────────

all_shapes = cons_shapes + fvg_shapes + rev_ob_shapes

# Print reversal count for verification
rev_count = rev['Reversal'].notna().sum()
print(f"Reversal signals detected: {rev_count}")
print(f"State distribution:\n{state_results['State'].value_counts()}")

fig.update_layout(
    title=f'ICT Price Delivery - USD/JPY ({timeframe} Timeframe) | {rev_count} reversals detected',
    yaxis_title='Price',
    xaxis_title='Date',
    shapes=all_shapes,
    template='plotly_dark',
    xaxis_rangeslider_visible=False,
    height=800
)

print("Opening chart in your web browser...")
fig.write_html("chart.html", auto_open=True)
print("Done! You should see the chart in your browser.")
