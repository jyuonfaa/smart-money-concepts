import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, turtle_soup_signals

print('Loading data...')
df_raw = pd.read_csv('HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv', sep=';', names=['date','open','high','low','close','volume'], index_col=False)
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)

# Focus on late June 2016 where we had a Prime Setup
start_date = '2016-06-24'
end_date = '2016-06-29'

df_daily_ri = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().loc['2016-06-01':'2016-07-10'].reset_index()
df_15m = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna().loc['2016-06-15':'2016-07-05']

print('Calculating SMC indicators...')
daily_swings = smc.swing_highs_lows(df_daily_ri, swing_length=5)
daily_ob = smc.ob(df_daily_ri, daily_swings)
ltf_swings = smc.swing_highs_lows(df_15m, swing_length=5)
reversals = detect_reversals(df_15m, ltf_swings)
midnight = smc.ny_midnight_open(df_15m)
fvg = smc.fvg(df_15m)

london = smc.sessions(df_15m, session='London').iloc[:, 0]
ny = smc.sessions(df_15m, session='New York').iloc[:, 0]
sessions = london | ny
ltf_obs = smc.ob(df_15m, ltf_swings)
session_obs = smc.session_order_blocks(df_15m, ltf_obs, sessions)

res = turtle_soup_signals(
    ohlc=df_15m, reversals=reversals, daily_ob=daily_ob, daily_ohlc=df_daily_ri,
    ny_midnight=midnight, fvg_df=fvg, ltf_session_obs=session_obs, max_session_ob_age_days=3
)

# Filter for plotting range
mask = (df_15m.index >= start_date) & (df_15m.index <= end_date)
df_plot = df_15m[mask]
res_plot = res[mask]
midnight_plot = midnight[mask]

fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03)

# Candlestick
fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['open'], high=df_plot['high'], low=df_plot['low'], close=df_plot['close'], name='15M Price'))

# Midnight Open
midnight_starts = midnight_plot.dropna()
for i in range(len(midnight_starts)):
    start_idx = midnight_starts.index[i]
    if i < len(midnight_starts) - 1:
        end_idx = midnight_starts.index[i+1]
    else:
        end_idx = df_plot.index[-1]
    val = midnight_starts.iloc[i]
    fig.add_trace(go.Scatter(x=[start_idx, end_idx], y=[val, val], mode='lines', line=dict(color='blue', width=2, dash='dot'), name='NY Midnight Open', showlegend=(i==0)))

# FVG Plotting
fvg['Datetime'] = df_15m.index[fvg.index]
fvg_plot = fvg[(fvg['Datetime'] >= pd.to_datetime(start_date)) & (fvg['Datetime'] <= pd.to_datetime(end_date))]
for i, row in fvg_plot.iterrows():
    if row['FVG'] == 1:
        color = 'rgba(0, 255, 0, 0.2)'
    elif row['FVG'] == -1:
        color = 'rgba(255, 0, 0, 0.2)'
    else:
        continue
    
    start_dt = row['Datetime']
    end_dt = df_plot.index[-1]
    if not np.isnan(row['MitigatedIndex']):
        mit_idx = int(row['MitigatedIndex'])
        if mit_idx < len(df_15m):
            end_dt = df_15m.index[mit_idx]
            
    if end_dt >= pd.to_datetime(start_date):
        fig.add_shape(type="rect", x0=start_dt, y0=row['Bottom'], x1=end_dt, y1=row['Top'], fillcolor=color, line=dict(width=0), layer="below")

# Signals
for dt, row in res_plot.iterrows():
    is_prime = row['power3_sponsored'] and row['down_candle_violated'] and not row['is_lethargic']
    
    if row['turtle_soup_bull']:
        color = 'gold' if is_prime else 'green'
        marker_symbol = 'star-triangle-up' if is_prime else 'triangle-up'
        size = 20 if is_prime else 12
        text = 'Prime Bullish' if is_prime else 'Bullish Signal'
        
        fig.add_trace(go.Scatter(x=[dt], y=[row['ts_entry_price']], mode='markers', marker=dict(symbol=marker_symbol, color=color, size=size, line=dict(width=2, color='black')), name=text, hovertemplate=f"Entry: {row['ts_entry_price']}<br>Stop: {row['ts_ob_stop']}<br>FVG Target: {row['ts_target_fvg']}"))
        
        # Plot entry and stop lines for prime setups
        if is_prime:
            fig.add_shape(type="line", x0=dt, y0=row['ts_entry_price'], x1=dt+pd.Timedelta(hours=10), y1=row['ts_entry_price'], line=dict(color="green", width=2, dash="dash"))
            fig.add_shape(type="line", x0=dt, y0=row['ts_ob_stop'], x1=dt+pd.Timedelta(hours=10), y1=row['ts_ob_stop'], line=dict(color="red", width=2, dash="dash"))
            if not np.isnan(row['ts_target_fvg']):
                fig.add_shape(type="line", x0=dt, y0=row['ts_target_fvg'], x1=dt+pd.Timedelta(hours=10), y1=row['ts_target_fvg'], line=dict(color="purple", width=2, dash="dash"))

    elif row['turtle_soup_bear']:
        color = 'gold' if is_prime else 'red'
        marker_symbol = 'star-triangle-down' if is_prime else 'triangle-down'
        size = 20 if is_prime else 12
        text = 'Prime Bearish' if is_prime else 'Bearish Signal'
        
        fig.add_trace(go.Scatter(x=[dt], y=[row['ts_entry_price']], mode='markers', marker=dict(symbol=marker_symbol, color=color, size=size, line=dict(width=2, color='black')), name=text, hovertemplate=f"Entry: {row['ts_entry_price']}<br>Stop: {row['ts_ob_stop']}<br>FVG Target: {row['ts_target_fvg']}"))
        
        if is_prime:
            fig.add_shape(type="line", x0=dt, y0=row['ts_entry_price'], x1=dt+pd.Timedelta(hours=10), y1=row['ts_entry_price'], line=dict(color="red", width=2, dash="dash"))
            fig.add_shape(type="line", x0=dt, y0=row['ts_ob_stop'], x1=dt+pd.Timedelta(hours=10), y1=row['ts_ob_stop'], line=dict(color="red", width=2, dash="dash"))
            if not np.isnan(row['ts_target_fvg']):
                fig.add_shape(type="line", x0=dt, y0=row['ts_target_fvg'], x1=dt+pd.Timedelta(hours=10), y1=row['ts_target_fvg'], line=dict(color="purple", width=2, dash="dash"))

fig.update_layout(title='Month 3 Video 3: Institutional Sponsorship (Prime Setups vs Raw)', template='plotly_dark', xaxis_rangeslider_visible=False, height=900, hovermode='x unified')
fig.write_html('visualize_month3_video3.html')
print("Successfully generated visualize_month3_video3.html")
