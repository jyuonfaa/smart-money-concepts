import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from smartmoneyconcepts import smc

def load_audusd():
    print("Loading local AUDUSD 2016 data...")
    df_raw = pd.read_csv(
        'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv',
        sep=';', names=['date','open','high','low','close','volume'],
        index_col=False
    )
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
    df_raw.set_index('date', inplace=True)
    
    daily = df_raw.resample('1D').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    
    monthly = df_raw.resample('1ME').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    
    return daily, monthly

def create_pair_figure(symbol, daily, monthly):
    # Run Detector on Monthly
    monthly_ob = smc.monthly_range_ob(monthly)
    last = monthly_ob.iloc[-1]
    
    m_high = float(last['monthly_down_ob_high'])
    m_low = float(last['monthly_down_ob_low'])
    m_up_high = float(last['monthly_up_ob_high'])
    m_up_low = float(last['monthly_up_ob_low'])
    bias = last['monthly_bias']

    n = len(monthly)
    down_idx = None
    for i in range(n - 1, -1, -1):
        if monthly.iloc[i]['close'] < monthly.iloc[i]['open']:
            down_idx = i
            break
            
    up_idx = None
    if down_idx is not None:
        for i in range(down_idx - 1, -1, -1):
            row = monthly.iloc[i]
            if row['close'] > row['open'] and row['low'] > m_high:
                up_idx = i
                break
        if up_idx is None:
            for i in range(down_idx - 1, -1, -1):
                row = monthly.iloc[i]
                if row['close'] > row['open']:
                    up_idx = i
                    break

    fig = make_subplots(
        rows=1, cols=2, 
        subplot_titles=(f"{symbol} Monthly Chart", f"{symbol} Daily Chart"),
        column_widths=[0.4, 0.6],
        horizontal_spacing=0.05
    )

    # 1. Monthly Chart
    fig.add_trace(go.Candlestick(
        x=monthly.index,
        open=monthly['open'], high=monthly['high'],
        low=monthly['low'], close=monthly['close'],
        name='Monthly',
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    ), row=1, col=1)

    if down_idx is not None:
        down_date = monthly.index[down_idx]
        fig.add_shape(
            type="rect",
            x0=down_date - pd.Timedelta(days=10), y0=m_low,
            x1=down_date + pd.Timedelta(days=10), y1=m_high,
            fillcolor="rgba(239, 83, 80, 0.3)", line_width=1, line_color="rgba(239, 83, 80, 0.8)",
            row=1, col=1
        )

    if up_idx is not None:
        up_date = monthly.index[up_idx]
        fig.add_shape(
            type="rect",
            x0=up_date - pd.Timedelta(days=10), y0=m_up_low,
            x1=up_date + pd.Timedelta(days=10), y1=m_up_high,
            fillcolor="rgba(38, 166, 154, 0.3)", line_width=1, line_color="rgba(38, 166, 154, 0.8)",
            row=1, col=1
        )

    for level, color, name in [
        (m_high, 'red', 'Down High'), (m_low, 'red', 'Down Low'),
        (m_up_high, 'green', 'Up High'), (m_up_low, 'green', 'Up Low')
    ]:
        if not pd.isna(level):
            fig.add_hline(y=level, line_dash="dot", line_color=color, annotation_text=name, row=1, col=1)

    # 2. Daily Chart
    fig.add_trace(go.Candlestick(
        x=daily.index,
        open=daily['open'], high=daily['high'],
        low=daily['low'], close=daily['close'],
        name='Daily',
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    ), row=1, col=2)

    if not pd.isna(m_high) and not pd.isna(m_low):
        fig.add_hrect(
            y0=m_low, y1=m_high, fillcolor="rgba(38, 166, 154, 0.1)",
            layer="below", line_width=0, annotation_text="Bullish OB Zone", annotation_position="top left",
            row=1, col=2
        )
    if not pd.isna(m_up_high) and not pd.isna(m_up_low):
        fig.add_hrect(
            y0=m_up_low, y1=m_up_high, fillcolor="rgba(239, 83, 80, 0.1)",
            layer="below", line_width=0, annotation_text="Bearish OB Zone", annotation_position="bottom left",
            row=1, col=2
        )

    bias_color = "green" if bias == "BULLISH" else "red" if bias == "BEARISH" else "gray"
    fig.add_annotation(
        xref="paper", yref="paper", x=1.0, y=1.05,
        text=f"<b>Bias: {bias}</b>", showarrow=False,
        font=dict(size=16, color=bias_color),
        align="right"
    )

    fig.update_layout(
        title=f"Month 3 Video 4: {symbol} Monthly Range Anticipation",
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        template='plotly_dark',
        height=700,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def main():
    daily, monthly = load_audusd()
    fig = create_pair_figure("AUDUSD", daily, monthly)
    
    out_file = "ICT_MONTH3_VIDEO4_MONTHLY_RANGE.html"
    fig.write_html(out_file)
    print(f"\\nDashboard generated: {out_file}")

if __name__ == "__main__":
    main()
