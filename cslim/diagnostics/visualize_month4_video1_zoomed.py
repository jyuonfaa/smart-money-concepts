import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts.smc import smc, triad_divergence

def build_visualization():
    # 1. Load Data
    dxy = pd.read_csv("tests/test_data/MACRO/DXY_Daily_2016.csv")
    dxy['date'] = pd.to_datetime(dxy['date'])
    dxy.set_index('date', inplace=True)

    zb = pd.read_csv("tests/test_data/MACRO/ZB_Daily_2016.csv")
    zb['date'] = pd.to_datetime(zb['date'])
    zb.set_index('date', inplace=True)

    zn = pd.read_csv("tests/test_data/MACRO/ZN_Daily_2016.csv")
    zn['date'] = pd.to_datetime(zn['date'])
    zn.set_index('date', inplace=True)

    zf = pd.read_csv("tests/test_data/MACRO/ZF_Daily_2016.csv")
    zf['date'] = pd.to_datetime(zf['date'])
    zf.set_index('date', inplace=True)

    dxy_swings = smc.swing_highs_lows_v4(dxy)

    triad = {
        '30Y Bond (ZB)': zb,
        '10Y Note (ZN)': zn,
        '5Y Note (ZF)': zf
    }

    # 2. Build USDX POIs
    dxy_swings_v1 = smc.swing_highs_lows(dxy, swing_length=5)
    
    dxy_ob = smc.ob(dxy, dxy_swings_v1)
    dxy_ob.index = dxy.index
    pois_ob = dxy_ob[dxy_ob['OB'].notna()][['Top', 'Bottom', 'MitigatedIndex']].rename(columns={'Top': 'top', 'Bottom': 'bottom', 'MitigatedIndex': 'end_idx'})
    
    dxy_fvg = smc.fvg(dxy)
    dxy_fvg.index = dxy.index
    pois_fvg = dxy_fvg[dxy_fvg['FVG'].notna()][['Top', 'Bottom', 'MitigatedIndex']].rename(columns={'Top': 'top', 'Bottom': 'bottom', 'MitigatedIndex': 'end_idx'})
    
    dxy_liq = smc.liquidity(dxy, dxy_swings_v1)
    dxy_liq.index = dxy.index
    pois_liq = dxy_liq[dxy_liq['Liquidity'].notna()][['Level', 'Swept']].rename(columns={'Level': 'top', 'Swept': 'end_idx'})
    pois_liq['bottom'] = pois_liq['top']
    pois_liq = pois_liq[['top', 'bottom', 'end_idx']]
    
    usdx_pois = pd.concat([pois_ob, pois_fvg, pois_liq]).dropna()

    # 3. Get Divergences (MODE 2 - POI Gated)
    div_poi = triad_divergence(dxy, triad, dxy_swings, lookaround_bars=5, usdx_pois=usdx_pois)
    bullish_poi = div_poi[div_poi['triad_bullish_div']]
    bearish_poi = div_poi[div_poi['triad_bearish_div']]

    # 4. Setup Plotly Figure
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03,
        row_heights=[0.55, 0.15, 0.15, 0.15],
        subplot_titles=("USDX (DXY) Daily 2016", "30Y Bond (ZB)", "10Y Note (ZN)", "5Y Note (ZF)")
    )

    # Plot DXY
    fig.add_trace(go.Candlestick(
        x=dxy.index, open=dxy['open'], high=dxy['high'], low=dxy['low'], close=dxy['close'],
        name="DXY"
    ), row=1, col=1)

    # Plot ZB
    fig.add_trace(go.Candlestick(
        x=zb.index, open=zb['open'], high=zb['high'], low=zb['low'], close=zb['close'],
        name="ZB"
    ), row=2, col=1)

    # Plot ZN
    fig.add_trace(go.Candlestick(
        x=zn.index, open=zn['open'], high=zn['high'], low=zn['low'], close=zn['close'],
        name="ZN"
    ), row=3, col=1)

    # Plot ZF
    fig.add_trace(go.Candlestick(
        x=zf.index, open=zf['open'], high=zf['high'], low=zf['low'], close=zf['close'],
        name="ZF"
    ), row=4, col=1)

    # Add POIs to Panel 1
    for date, row in usdx_pois.iterrows():
        end_idx = int(row['end_idx']) if pd.notna(row['end_idx']) else 0
        if end_idx > 0 and end_idx < len(dxy):
            x1_date = dxy.index[end_idx]
        else:
            x1_date = dxy.index[-1]

        fig.add_shape(
            type="rect",
            x0=date, x1=x1_date,
            y0=row['bottom'], y1=row['top'],
            fillcolor="LightSalmon", opacity=0.2, line_width=0,
            row=1, col=1
        )

    # Add Divergence Markers and Vertical Lines
    for date, row in bullish_poi.iterrows():
        fig.add_annotation(
            x=date, y=dxy.loc[date, 'low'],
            text=f"▲ {row['triad_diverging_assets']}",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="Lime",
            ax=0, ay=40, font=dict(color="Lime", size=10),
            row=1, col=1
        )
        fig.add_vline(x=date, line_dash="dash", line_color="gray", opacity=0.7)

    for date, row in bearish_poi.iterrows():
        fig.add_annotation(
            x=date, y=dxy.loc[date, 'high'],
            text=f"▼ {row['triad_diverging_assets']}",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="Red",
            ax=0, ay=-40, font=dict(color="Red", size=10),
            row=1, col=1
        )
        fig.add_vline(x=date, line_dash="dash", line_color="gray", opacity=0.7)

    fig.update_layout(
        title="ICT Month 4 Video 1 — Interest Rate Triad Divergence | USDX + Triad Legs | POI-Gated",
        height=1000,
        xaxis_rangeslider_visible=False,
        xaxis_range=['2016-04-10', '2016-05-13'],
        xaxis2_rangeslider_visible=False,
        xaxis3_rangeslider_visible=False,
        xaxis4_rangeslider_visible=False,
        template="plotly_dark"
    )

    out_file = "visualize_month4_video1_zoomed.html"
    fig.write_html(out_file)
    print(f"Chart saved to {out_file}")

if __name__ == "__main__":
    build_visualization()
