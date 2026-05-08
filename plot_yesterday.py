import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, PriceDeliveryStateMachine

print("Downloading EUR/USD 15m data for early May 2026...")
timeframe = "15m"
# Fetch a window around May 6 to ensure indicators have context
ohlc = yf.download("EURUSD=X", start="2026-05-01", end="2026-05-08", interval=timeframe, progress=False)

if ohlc.empty:
    print("Error: No data downloaded. Check your internet connection or ticker.")
    exit()

if isinstance(ohlc.columns, pd.MultiIndex):
    ohlc.columns = ohlc.columns.get_level_values(0)
ohlc.columns = [c.lower() for c in ohlc.columns]
ohlc = ohlc[['open', 'high', 'low', 'close', 'volume']]
ohlc.index = pd.to_datetime(ohlc.index).tz_localize(None)

print(f"Downloaded {len(ohlc)} rows. Calculating ICT Indicators...")

# 1. Detection Layers
swing_hl = smc.swing_highs_lows(ohlc, swing_length=10)
swing_hl.index = ohlc.index

fvg = smc.fvg(ohlc, join_consecutive=False)
fvg.index = ohlc.index

cons = smc.consolidation(ohlc, prd=10, conslen=5)
cons.index = ohlc.index

exp = smc.expansion(ohlc, cons)
exp.index = ohlc.index

rev = detect_reversals(ohlc, swing_hl)
rev.index = ohlc.index

# 2. State Machine
pdsm = PriceDeliveryStateMachine()
state_results = pdsm.process(
    ohlc, cons, exp,
    fvg=fvg,
    reversals=rev,
)
state_results.index = ohlc.index

# Filter for May 6th specifically for the summary
may_6_data = state_results[state_results.index.date == pd.to_datetime("2026-05-06").date()]

print(f"\n--- Analysis for May 6, 2026 ---")
print(f"Total 15m candles: {len(may_6_data)}")
print(f"State Distribution:\n{may_6_data['State'].value_counts()}")
rev_count = rev[rev.index.date == pd.to_datetime("2026-05-06").date()]['Reversal'].notna().sum()
print(f"Reversal Signals (Stop Runs): {rev_count}")

# 3. Build Chart
fig = go.Figure()

# Candlesticks
fig.add_trace(go.Candlestick(
    x=ohlc.index,
    open=ohlc['open'], high=ohlc['high'],
    low=ohlc['low'], close=ohlc['close'],
    name='EUR/USD 15M'
))

# FVG Shapes
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

# Swing HL Markers
highs = swing_hl[swing_hl['HighLow'] == 1.0]
fig.add_trace(go.Scatter(x=highs.index, y=highs['Level'], mode='markers', marker=dict(symbol='triangle-down', size=10, color='red'), name='Swing High'))
lows = swing_hl[swing_hl['HighLow'] == -1.0]
fig.add_trace(go.Scatter(x=lows.index, y=lows['Level'], mode='markers', marker=dict(symbol='triangle-up', size=10, color='lime'), name='Swing Low'))

# State indicators at bottom
state_colors = {'consolidation': 'grey', 'expansion': 'blue', 'retracement': 'yellow', 'reversal': 'red', 'unknown': 'white'}
for state in state_results['State'].unique():
    mask = state_results[state_results['State'] == state]
    if not mask.empty:
        fig.add_trace(go.Scatter(x=mask.index, y=[ohlc['low'].min() * 0.999] * len(mask), mode='markers', marker=dict(symbol='square', size=5, color=state_colors.get(state, 'white')), name=f'State: {state}'))

# Layout
fig.update_layout(
    title=f'ICT Price Delivery - EUR/USD (15M) | May 6, 2026 Analysis',
    template='plotly_dark',
    xaxis_rangeslider_visible=False,
    height=800,
    shapes=fvg_shapes
)

# Limit view to May 6
fig.update_xaxes(range=["2026-05-06 00:00", "2026-05-07 00:00"])

output_file = "chart_may_6.html"
fig.write_html(output_file)
print(f"\nChart saved to {output_file}. Use a browser to view it.")
