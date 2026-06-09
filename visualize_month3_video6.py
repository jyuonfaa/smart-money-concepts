import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts.smc import smc

def run_dashboard():
    # 1. Load Data
    zn = pd.read_csv("tests/test_data/MACRO/ZN_Daily_2016.csv")
    zb = pd.read_csv("tests/test_data/MACRO/ZB_Daily_2016.csv")
    dxy = pd.read_csv("tests/test_data/MACRO/DXY_Daily_2016.csv")
    eurusd = pd.read_csv("tests/test_data/MACRO/EURUSD_Daily_2016.csv")

    for df in [zn, zb, dxy, eurusd]:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)

    common_dates = zn.index.intersection(zb.index).intersection(dxy.index).intersection(eurusd.index)
    zn = zn.loc[common_dates].copy()
    zb = zb.loc[common_dates].copy()
    dxy = dxy.loc[common_dates].copy()
    eurusd = eurusd.loc[common_dates].copy()

    # Full 2016 view — quarterly signals fire across the whole year
    start_dt, end_dt = "2016-01-01", "2016-12-31"
    zn = zn.loc[start_dt:end_dt]
    zb = zb.loc[start_dt:end_dt]
    dxy = dxy.loc[start_dt:end_dt]
    eurusd = eurusd.loc[start_dt:end_dt]

    # 2. Compute Quarterly Macro Bias    # Calculate Macro Regime and Execution Signals
    macro_df = smc.macro_bond_bias(zn, zb, dxy)
    
    # Calculate Inter-market Order Block Alignment (Prime Setups)
    ob_alignment = smc.macro_ob_alignment(zb, dxy)
    prime_dates = ob_alignment[ob_alignment == True].index

    # 4. Build 4-Pane Dashboard
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.3, 0.3, 0.2, 0.2],
        subplot_titles=(
            "US 10-Year T-Note (ZN) — THE BAROMETER",
            "US 30-Year T-Bond (ZB) — THE BAROMETER",
            "US Dollar Index (DXY) — MACRO TREND",
            "EURUSD — MICRO TECHNICAL EXECUTION"
        )
    )

    fig.add_trace(go.Candlestick(x=zn.index, open=zn['open'], high=zn['high'], low=zn['low'], close=zn['close'], name="ZN"), row=1, col=1)
    fig.add_trace(go.Candlestick(x=zb.index, open=zb['open'], high=zb['high'], low=zb['low'], close=zb['close'], name="ZB"), row=2, col=1)
    fig.add_trace(go.Candlestick(x=dxy.index, open=dxy['open'], high=dxy['high'], low=dxy['low'], close=dxy['close'], name="DXY"), row=3, col=1)
    fig.add_trace(go.Candlestick(x=eurusd.index, open=eurusd['open'], high=eurusd['high'], low=eurusd['low'], close=eurusd['close'], name="EURUSD"), row=4, col=1)

    # 5. Mark Quarterly Macro Regimes and Execution Signals
    # Shade DXY background for Macro Regime
    for dt, row in macro_df.iterrows():
        if pd.isna(row['regime']) or row['regime'] == 0:
            continue
        color = "rgba(0, 229, 255, 0.1)" if row['regime'] == 1 else "rgba(255, 23, 68, 0.1)"
        # Draw a shape on DXY pane (row 3)
        fig.add_vrect(
            x0=dt, x1=dt + pd.Timedelta(days=1),
            fillcolor=color, opacity=0.3, layer="below", line_width=0, row=3, col=1
        )
        
    # Mark Execution Signals
    signals = macro_df['signal'][macro_df['signal'] != 0]
    eurusd_bias = smc.macro_pair_bias(signals, 'EURUSD')
    
    for dt, bias in signals.items():
        if dt < pd.to_datetime(start_dt) or dt > pd.to_datetime(end_dt):
            continue
        color = "#00e5ff" if bias == 1 else "#ff1744"
        label = "BUY USD" if bias == 1 else "SELL USD"
        eurusd_action = "EURUSD SHORT" if eurusd_bias.loc[dt] == -1 else "EURUSD LONG"
        
        fig.add_vline(x=dt, line_width=2, line_dash="dash", line_color=color, opacity=0.9, row='all', col=1)
        
        # Annotate DXY Pane
        fig.add_annotation(
            x=dt, y=dxy['high'].max(),
            text=label, showarrow=False,
            font=dict(color=color, size=10, family="Outfit, sans-serif"),
            textangle=-90, yshift=40, row=3, col=1
        )
        
        # Annotate EURUSD Pane
        fig.add_annotation(
            x=dt, y=eurusd['high'].max(),
            text=eurusd_action, showarrow=False,
            font=dict(color=color, size=10, family="Outfit, sans-serif"),
            textangle=-90, yshift=40, row=4, col=1
        )

    # 6. Shade Prime Setup Confluence Zones (DXY Bullish OB + ZB Bearish OB overlap)
    if len(prime_dates) > 0:
        all_idx = dxy.index.tolist()
        prime_set = set(prime_dates)
        zone_start = None
        for i, date in enumerate(all_idx):
            is_prime = date in prime_set
            if is_prime and zone_start is None:
                zone_start = date
            elif not is_prime and zone_start is not None:
                fig.add_vrect(x0=zone_start, x1=all_idx[i-1], fillcolor="#ffd600", opacity=0.12, line_width=0, row=3, col=1)
                fig.add_vrect(x0=zone_start, x1=all_idx[i-1], fillcolor="#ffd600", opacity=0.12, line_width=0, row=4, col=1)
                zone_start = None
        if zone_start is not None:
            fig.add_vrect(x0=zone_start, x1=all_idx[-1], fillcolor="#ffd600", opacity=0.12, line_width=0, row=3, col=1)
            fig.add_vrect(x0=zone_start, x1=all_idx[-1], fillcolor="#ffd600", opacity=0.12, line_width=0, row=4, col=1)

    # 7. Masterpiece Styling
    fig.update_layout(
        title=dict(text="ICT MONTH 3 VIDEO 6: MACRO ECONOMIC TO MICRO TECHNICAL", font=dict(size=22, color="#ffffff", family="Outfit, sans-serif")),
        plot_bgcolor="#0b0f19",
        paper_bgcolor="#0b0f19",
        margin=dict(l=50, r=30, t=80, b=50),
        height=1300,
        showlegend=False,
    )
    for ax in ['xaxis', 'xaxis2', 'xaxis3', 'xaxis4']:
        fig.update_layout({ax: dict(rangeslider=dict(visible=False), type='date', gridcolor="#263238", tickfont=dict(color="#b0bec5"))})
    for i in range(1, 5):
        fig.update_yaxes(gridcolor="#263238", tickfont=dict(color="#b0bec5"), row=i, col=1)

    out_file = "ICT_MONTH3_VIDEO6_MACRO_FLOW.html"
    fig.write_html(out_file)
    print(f"Enhanced dashboard saved to {out_file}")
    print(f"Quarterly macro signals plotted: {len(signals)}")
    print(f"Prime Setup OB confluence zones detected: {len(prime_dates)} trading days")

if __name__ == "__main__":
    run_dashboard()
