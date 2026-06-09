import pandas as pd
import plotly.graph_objects as go
from smartmoneyconcepts.smc import smc
import numpy as np

# Load EURUSD Daily 2016 data
eurusd = pd.read_csv('tests/test_data/MACRO/EURUSD_Daily_2016.csv', parse_dates=['date'], index_col='date')

# Calculate Swings
swings = smc.swing_highs_lows_v4(eurusd)

# Calculate Trendline Phantoms
phantoms = smc.trendline_phantoms(eurusd, swings)

# Create Dashboard
fig = go.Figure()

# Plot Candlesticks
fig.add_trace(go.Candlestick(
    x=eurusd.index,
    open=eurusd['open'],
    high=eurusd['high'],
    low=eurusd['low'],
    close=eurusd['close'],
    name='EURUSD Daily'
))

# Plot Swings
highs = swings[swings['type'] == 'HIGH']
lows = swings[swings['type'] == 'LOW']

fig.add_trace(go.Scatter(
    x=highs['ts'], y=highs['p'],
    mode='markers', marker=dict(color='green', symbol='triangle-down', size=8),
    name='Swing High'
))
fig.add_trace(go.Scatter(
    x=lows['ts'], y=lows['p'],
    mode='markers', marker=dict(color='red', symbol='triangle-up', size=8),
    name='Swing Low'
))

# Plot Traps
active_bullish_interim = phantoms[phantoms['trap_type'] == 1]['trap_interim'].dropna()
active_bearish_interim = phantoms[phantoms['trap_type'] == -1]['trap_interim'].dropna()

active_bullish_point2 = phantoms[phantoms['trap_type'] == 1]['trap_point2'].dropna()
active_bearish_point2 = phantoms[phantoms['trap_type'] == -1]['trap_point2'].dropna()

if not active_bullish_interim.empty:
    fig.add_trace(go.Scatter(
        x=active_bullish_interim.index, y=active_bullish_interim.values,
        mode='lines', line=dict(color='blue', width=2, dash='dash'),
        name='Bullish Trap (Interim Low)'
    ))
    fig.add_trace(go.Scatter(
        x=active_bullish_point2.index, y=active_bullish_point2.values,
        mode='lines', line=dict(color='cyan', width=2, dash='dot'),
        name='Bullish Trap (Point 2 High)'
    ))

if not active_bearish_interim.empty:
    fig.add_trace(go.Scatter(
        x=active_bearish_interim.index, y=active_bearish_interim.values,
        mode='lines', line=dict(color='orange', width=2, dash='dash'),
        name='Bearish Trap (Interim High)'
    ))
    fig.add_trace(go.Scatter(
        x=active_bearish_point2.index, y=active_bearish_point2.values,
        mode='lines', line=dict(color='yellow', width=2, dash='dot'),
        name='Bearish Trap (Point 2 Low)'
    ))

# Check for signals
htf_bias = pd.Series(1, index=eurusd.index) # Assume Bullish HTF
ob_swings = smc.swing_highs_lows(eurusd, swing_length=3)
ob_df = smc.ob(eurusd, ob_swings)
signals = smc.phantom_signals(eurusd, phantoms, ob_df, htf_bias)

bullish_signals = signals[signals['signal'] == 1]
bearish_signals = signals[signals['signal'] == -1]

# Custom colors for different triggers
def get_color(trigger_type):
    if pd.isna(trigger_type): return 'white'
    if 'Turtle Soup' in str(trigger_type): return 'purple'
    if 'Limit' in str(trigger_type): return 'cyan'
    if 'Breaker' in str(trigger_type): return 'magenta'
    if 'OB Tap' in str(trigger_type): return 'pink'
    if 'Phase 3' in str(trigger_type): return 'yellow'
    return 'white'

if not bullish_signals.empty:
    for idx, row in bullish_signals.iterrows():
        c = get_color(row['trigger_type'])
        sym = 'triangle-up' if 'Phase 3' not in str(row['trigger_type']) else 'star'
        
        # Plot Entry
        fig.add_trace(go.Scatter(
            x=[idx], y=[eurusd.loc[idx]['low']],
            mode='markers+text', marker=dict(color=c, symbol=sym, size=14, line=dict(width=2, color='white')),
            text=[str(row['trigger_type']).replace('Phase 2 BUY -- ', '').replace('Phase 3 BUY -- ', 'P3: ')], textposition='bottom center',
            name='Bullish Exec', showlegend=False
        ))
        
        # Plot Target 1
        target = row['target_price']
        if not pd.isna(target):
            fig.add_shape(type="line", x0=idx, y0=eurusd.loc[idx]['low'], x1=idx, y1=target, line=dict(color=c, width=2, dash="dot"))
            
        # Plot Target 2 (FVG)
        target2 = row['secondary_target']
        if not pd.isna(target2):
            fig.add_shape(type="line", x0=idx, y0=eurusd.loc[idx]['low'], x1=idx, y1=target2, line=dict(color="orange", width=1, dash="dash"))

if not bearish_signals.empty:
    for idx, row in bearish_signals.iterrows():
        c = get_color(row['trigger_type'])
        sym = 'triangle-down' if 'Phase 3' not in str(row['trigger_type']) else 'star'
        
        # Plot Entry
        fig.add_trace(go.Scatter(
            x=[idx], y=[eurusd.loc[idx]['high']],
            mode='markers+text', marker=dict(color=c, symbol=sym, size=14, line=dict(width=2, color='white')),
            text=[str(row['trigger_type']).replace('Phase 2 SELL -- ', '').replace('Phase 3 SELL -- ', 'P3: ')], textposition='top center',
            name='Bearish Exec', showlegend=False
        ))
        
        # Plot Target 1
        target = row['target_price']
        if not pd.isna(target):
            fig.add_shape(type="line", x0=idx, y0=eurusd.loc[idx]['high'], x1=idx, y1=target, line=dict(color=c, width=2, dash="dot"))
            
        # Plot Target 2 (FVG)
        target2 = row['secondary_target']
        if not pd.isna(target2):
            fig.add_shape(type="line", x0=idx, y0=eurusd.loc[idx]['high'], x1=idx, y1=target2, line=dict(color="orange", width=1, dash="dash"))

fig.update_layout(
    title='ICT Month 3 Video 7: Trendline Phantoms (False Trendlines)',
    yaxis_title='EURUSD Price',
    xaxis_rangeslider_visible=False,
    template='plotly_dark',
    height=800
)

output_file = 'ICT_MONTH3_VIDEO7_PHANTOMS.html'
fig.write_html(output_file)
print(f"Generated dashboard: {output_file}")
print(f"Bullish Traps active on {len(active_bullish_interim)} days")
print(f"Bearish Traps active on {len(active_bearish_interim)} days")
print(f"Executions fired: {len(bullish_signals) + len(bearish_signals)}")
