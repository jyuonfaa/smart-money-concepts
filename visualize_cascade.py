import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import detect_reversals, institutional_cascade_signals
import warnings
warnings.filterwarnings('ignore')

def main():
    print("Loading data...")
    df_raw = pd.read_csv(
        'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv',
        sep=';', names=['date','open','high','low','close','volume'],
        index_col=False
    )
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
    df_raw.set_index('date', inplace=True)

    df_4h = df_raw.resample('4h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    df_daily = df_raw.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    df_weekly = df_raw.resample('1W').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    df_monthly = df_raw.resample('1ME').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

    print("Calculating cascade...")
    monthly_ob = smc.monthly_range_ob(df_monthly)
    weekly_swings = smc.swing_highs_lows(df_weekly, swing_length=5)
    weekly_ob = smc.ob(df_weekly, weekly_swings)
    daily_swings = smc.swing_highs_lows(df_daily, swing_length=5)
    daily_ob = smc.ob(df_daily, daily_swings)
    ltf_swings = smc.swing_highs_lows(df_4h, swing_length=5)
    ltf_reversals = detect_reversals(df_4h, ltf_swings)
    ltf_fvg = smc.fvg(df_4h)

    res = institutional_cascade_signals(
        ohlc_ltf=df_4h, reversals_ltf=ltf_reversals, daily_ob=daily_ob, daily_ohlc=df_daily,
        weekly_ob=weekly_ob, weekly_ohlc=df_weekly, monthly_ob_df=monthly_ob, fvg_df=ltf_fvg
    )

    sigs = res[res['turtle_soup_bull'] | res['turtle_soup_bear']].copy()
    
    last_m = monthly_ob.iloc[-1]
    m_high = float(last_m.get('monthly_down_ob_high', np.nan))
    m_low = float(last_m.get('monthly_down_ob_low', np.nan))
    m_up_high = float(last_m.get('monthly_up_ob_high', np.nan))
    m_up_low = float(last_m.get('monthly_up_ob_low', np.nan))

    print(f"Plotting {len(sigs)} cascade setups...")

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df_4h.index, open=df_4h['open'], high=df_4h['high'],
        low=df_4h['low'], close=df_4h['close'], name='4H Chart',
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    ))

    # Add Monthly Bounds
    if not pd.isna(m_high):
        fig.add_hline(y=m_high, line_dash="dash", line_color="blue", annotation_text="Monthly Bullish OB Top")
    if not pd.isna(m_low):
        fig.add_hline(y=m_low, line_dash="dash", line_color="blue", annotation_text="Monthly Bullish OB Floor")
    if not pd.isna(m_up_high):
        fig.add_hline(y=m_up_high, line_dash="dash", line_color="orange", annotation_text="Monthly Bearish OB Ceiling")
    if not pd.isna(m_up_low):
        fig.add_hline(y=m_up_low, line_dash="dash", line_color="orange", annotation_text="Monthly Bearish OB Bottom")

    # Plot Setup Markers and Targets
    for idx, row in sigs.iterrows():
        entry = row['ts_entry_price']
        target = row['ts_target_near']
        stop = row['ts_ob_stop']
        is_bull = row['turtle_soup_bull']
        
        marker_color = 'green' if is_bull else 'red'
        marker_symbol = 'triangle-up' if is_bull else 'triangle-down'
        
        # Entry Marker
        fig.add_trace(go.Scatter(
            x=[idx], y=[entry], mode='markers',
            marker=dict(color=marker_color, size=12, symbol=marker_symbol),
            name='Entry'
        ))
        
        # Draw line from Entry to Macro Target to show scale
        if not pd.isna(target):
            fig.add_trace(go.Scatter(
                x=[idx, idx + pd.Timedelta(days=15)], y=[entry, target],
                mode='lines', line=dict(color=marker_color, dash='dot', width=1),
                showlegend=False
            ))
            
        # Draw Stop
        if not pd.isna(stop):
            fig.add_trace(go.Scatter(
                x=[idx, idx + pd.Timedelta(days=2)], y=[stop, stop],
                mode='lines', line=dict(color='yellow', width=2),
                showlegend=False
            ))

    fig.update_layout(
        title="4-Tier Institutional Cascade & Macro Targets (AUDUSD 4H)",
        xaxis_rangeslider_visible=False,
        template='plotly_dark',
        height=800
    )

    out_file = "ICT_CASCADE_MACRO_TARGETS.html"
    fig.write_html(out_file)
    print(f"Saved visualization to {out_file}")

if __name__ == "__main__":
    main()
